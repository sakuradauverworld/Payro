import re
import threading
import tkinter as tk
from datetime import datetime
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from send_coordinator import SendCoordinator
from template_engine import render


class SendTab(ttk.Frame):
    def __init__(self, parent, *, app):
        super().__init__(parent)
        self._app = app
        self._pdf_paths: list[Path] = []
        self._match_results: list = []
        self._coord: SendCoordinator | None = None
        self._current_group_id: str | None = None
        self._build()
        self._try_init_dnd()

    def _try_init_dnd(self):
        try:
            from tkinterdnd2 import DND_FILES
            self._drop_area.drop_target_register(DND_FILES)
            self._drop_area.dnd_bind("<<Drop>>", self._on_drop)
        except Exception:
            pass  # tkinterdnd2 未対応環境では D&D 無効

    def _build(self):
        top = ttk.Frame(self)
        top.pack(fill="x", padx=8, pady=8)

        # グループ選択
        ttk.Label(top, text="グループ:").pack(side="left")
        self._group_var = tk.StringVar()
        self._group_combo = ttk.Combobox(top, textvariable=self._group_var, state="readonly", width=20)
        self._group_combo.pack(side="left", padx=(4, 12))
        self._group_combo.bind("<<ComboboxSelected>>", self._on_group_change)

        # 年月入力
        ttk.Label(top, text="対象年月:").pack(side="left")
        self._year_var = tk.StringVar(value=str(datetime.now().year))
        ttk.Entry(top, textvariable=self._year_var, width=6).pack(side="left", padx=(4, 0))
        ttk.Label(top, text="年").pack(side="left")
        self._month_var = tk.StringVar(value=str(datetime.now().month))
        ttk.Entry(top, textvariable=self._month_var, width=4).pack(side="left", padx=(4, 0))
        ttk.Label(top, text="月").pack(side="left", padx=(0, 12))

        ttk.Button(top, text="フォルダを選択", command=self._select_folder).pack(side="left", padx=4)
        ttk.Button(top, text="ファイルを選択", command=self._select_files).pack(side="left", padx=4)
        ttk.Button(top, text="クリア", command=self._clear).pack(side="left")

        # ドロップエリア
        self._drop_area = tk.Label(
            self,
            text="ここにPDFファイルをドラッグ&ドロップ\nまたは上の「フォルダを選択」を使用",
            relief="groove", bg="#f0f0f0", height=4
        )
        self._drop_area.pack(fill="x", padx=8, pady=4)

        # コンテンツフレーム（マッチング一覧と誘導メッセージを切り替え）
        self._content_frame = ttk.Frame(self)
        self._content_frame.pack(fill="both", expand=True, padx=8, pady=4)

        # マッチング一覧
        cols = ("status", "name", "email", "filename")
        self._tree = ttk.Treeview(self._content_frame, columns=cols, show="headings", height=14)
        self._tree.heading("status", text="状態")
        self._tree.heading("name", text="名前")
        self._tree.heading("email", text="メールアドレス")
        self._tree.heading("filename", text="PDFファイル名")
        self._tree.column("status", width=80, anchor="center")
        self._tree.column("name", width=140)
        self._tree.column("email", width=220)
        self._tree.column("filename", width=300)
        self._tree.tag_configure("ok", background="#d4edda")
        self._tree.tag_configure("warn", background="#f8d7da")
        self._tree.tag_configure("skip", background="#e9ecef", foreground="gray")
        self._tree.pack(fill="both", expand=True)

        # 誘導ラベル（初期は非表示）
        self._guide_label = ttk.Label(
            self._content_frame,
            text="",
            foreground="#888888",
            justify="center",
            font=("", 11),
            anchor="center",
        )

        # 送信ボタン（初期は disabled、全員 PDF マッチ時のみ有効化）
        self._send_btn = ttk.Button(self, text="全員に送信", command=self._send, state="disabled")
        self._send_btn.pack(pady=8)

    def refresh_groups(self):
        """グループ一覧を再読み込みする（main.py 起動時・グループ管理から戻ったとき）"""
        groups = self._app.recipient_mgr.groups
        self._group_combo["values"] = [g.name for g in groups]
        if groups:
            current_ids = [g.id for g in groups]
            if self._current_group_id not in current_ids:
                self._current_group_id = groups[0].id
                self._group_var.set(groups[0].name)
            else:
                group = next(g for g in groups if g.id == self._current_group_id)
                self._group_var.set(group.name)
        else:
            self._current_group_id = None
            self._group_var.set("")
        self._update_tree()

    def _on_group_change(self, event):
        sel_name = self._group_var.get()
        group = next((g for g in self._app.recipient_mgr.groups if g.name == sel_name), None)
        if group:
            self._current_group_id = group.id
            self._pdf_paths = []
            self._update_tree()

    def _select_folder(self):
        folder = filedialog.askdirectory(title="PDFフォルダを選択")
        if folder:
            self._pdf_paths = list(Path(folder).glob("*.pdf"))
            self._update_tree()

    def _select_files(self):
        files = filedialog.askopenfilenames(
            title="PDFファイルを選択",
            filetypes=[("PDFファイル", "*.pdf"), ("すべてのファイル", "*.*")]
        )
        if files:
            self._pdf_paths = [Path(f) for f in files]
            self._update_tree()

    def _on_drop(self, event):
        raw = event.data
        paths = re.findall(r'\{([^}]+)\}|(\S+)', raw)
        self._pdf_paths = [Path(p[0] or p[1]) for p in paths if (p[0] or p[1]).lower().endswith(".pdf")]
        self._update_tree()

    def _clear(self):
        self._pdf_paths = []
        self._tree.delete(*self._tree.get_children())
        self._send_btn.config(state="disabled")

    def _show_guide(self, message: str):
        self._tree.pack_forget()
        self._guide_label.config(text=message)
        self._guide_label.pack(fill="both", expand=True)

    def _hide_guide(self):
        self._guide_label.pack_forget()
        self._tree.pack(fill="both", expand=True)

    def _update_tree(self):
        self._tree.delete(*self._tree.get_children())
        if not self._current_group_id:
            self._show_guide(
                "まず「グループ管理」タブを開いて\n"
                "グループを作成し、宛先を登録してください。"
            )
            self._send_btn.config(state="disabled")
            return
        recipients = self._app.recipient_mgr.get_recipients(self._current_group_id)
        if not recipients:
            self._show_guide(
                "このグループには宛先が登録されていません。\n"
                "「グループ管理」タブで宛先を追加してください。"
            )
            self._send_btn.config(state="disabled")
            return
        if not self._pdf_paths:
            self._hide_guide()
            self._match_results = []
            self._coord = None
            self._send_btn.config(state="disabled")
            return

        self._hide_guide()

        coord = SendCoordinator(recipients=recipients, pdf_paths=self._pdf_paths)
        self._match_results = coord.match()
        self._coord = coord

        all_ready = True
        for mr in self._match_results:
            if mr.recipient.excluded:
                tag, status, filename = "skip", "除外中", "—"
            elif mr.pdf_path:
                tag, status, filename = "ok", "送信予定", mr.pdf_path.name
            else:
                tag, status, filename = "warn", "PDFなし", "（PDFなし）"
                all_ready = False
            self._tree.insert("", "end",
                               values=(status, mr.recipient.name, mr.recipient.email, filename),
                               tags=(tag,))

        # 非除外の宛先が全員 PDF マッチしている場合のみ送信ボタンを有効化
        non_excluded = [mr for mr in self._match_results if not mr.recipient.excluded]
        self._send_btn.config(state="normal" if (non_excluded and all_ready) else "disabled")

    def _send(self):
        if not self._year_var.get().isdigit() or not self._month_var.get().isdigit():
            messagebox.showerror("入力エラー", "年月は数値で入力してください。")
            return
        year_int = int(self._year_var.get())
        month_int = int(self._month_var.get())
        if not (1900 <= year_int <= 2100) or not (1 <= month_int <= 12):
            messagebox.showerror("入力エラー", "年は1900〜2100、月は1〜12で入力してください。")
            return
        cfg = self._app.config_data
        if not cfg.is_configured():
            messagebox.showerror("設定未完了", "「設定」タブでGmailアドレスとアプリパスワードを設定してください。")
            return
        if self._coord is None:
            return

        year = self._year_var.get()
        month = self._month_var.get()

        # 選択グループのテンプレートを取得（確認ダイアログ前）
        group = next(g for g in self._app.recipient_mgr.groups if g.id == self._current_group_id)
        template = self._app.template_mgr.get_by_id(group.template_id)
        if template is None:
            messagebox.showerror("テンプレートエラー", "グループに紐づけられたテンプレートが見つかりません。")
            return

        # プレビュー用レンダリング（最初の非除外宛先の名前を使用）
        recipients_for_preview = self._app.recipient_mgr.get_recipients(self._current_group_id)
        non_excluded = [r for r in recipients_for_preview if not r.excluded]
        preview_name = non_excluded[0].name if non_excluded else "（氏名）"
        subject_preview = render(template.subject, name=preview_name, year=year, month=month)
        body_preview = render(template.body, name=preview_name, year=year, month=month)

        # 詳細確認ダイアログ
        if not self._show_send_confirm_dialog(
            group_name=group.name,
            recipient_count=len(non_excluded),
            year=year,
            month=month,
            subject=subject_preview,
            body_preview=body_preview,
        ):
            return

        # 送信直前に最新の宛先リストで再マッチング（宛先変更に対応）
        recipients = self._app.recipient_mgr.get_recipients(self._current_group_id)
        self._coord = SendCoordinator(recipients=recipients, pdf_paths=self._pdf_paths)
        self._match_results = self._coord.match()

        subject = render(template.subject, name="", year=year, month=month)

        self._send_btn.config(state="disabled", text="送信中...")

        def _run():
            report = self._coord.execute(
                match_results=self._match_results,
                gmail_address=cfg.gmail_address,
                gmail_app_password=cfg.gmail_app_password,
                subject=subject,
                body_template=template.body,
                year=year,
                month=month,
            )
            self.after(0, lambda: self._on_done(report, year, month))

        threading.Thread(target=_run, daemon=True).start()

    def _show_send_confirm_dialog(self, *, group_name: str, recipient_count: int,
                                   year: str, month: str, subject: str, body_preview: str) -> bool:
        result = tk.BooleanVar(value=False)

        win = tk.Toplevel(self)
        win.title("送信確認")
        win.geometry("520x440")
        win.resizable(False, False)
        win.grab_set()

        info = (
            f"グループ　：{group_name}\n"
            f"宛先数　　：{recipient_count}名\n"
            f"対象年月　：{year}年{month}月\n"
            f"\n"
            f"【件名】\n{subject}\n"
            f"\n"
            f"【本文プレビュー（1通目）】\n{body_preview}"
        )

        text = tk.Text(win, wrap="word", height=18)
        text.insert("1.0", info)
        text.config(state="disabled")
        text.pack(fill="both", expand=True, padx=12, pady=(12, 4))

        btn_frame = ttk.Frame(win)
        btn_frame.pack(pady=8)

        def _ok():
            result.set(True)
            win.destroy()

        def _cancel():
            win.destroy()

        ttk.Button(btn_frame, text="送信する", command=_ok).pack(side="left", padx=8)
        ttk.Button(btn_frame, text="キャンセル", command=_cancel).pack(side="left", padx=8)

        win.protocol("WM_DELETE_WINDOW", _cancel)
        win.wait_window()

        return result.get()

    def _on_done(self, report, year, month):
        self._send_btn.config(state="normal", text="全員に送信")
        report_text = report.to_text(year=year, month=month)

        win = tk.Toplevel(self)
        win.title("送信完了レポート")
        win.geometry("560x400")
        text = tk.Text(win, wrap="word")
        text.insert("1.0", report_text)
        text.config(state="disabled")
        text.pack(fill="both", expand=True, padx=8, pady=8)

        def _save():
            path = filedialog.asksaveasfilename(
                defaultextension=".txt",
                filetypes=[("テキストファイル", "*.txt")],
                initialfile=f"送信レポート_{year}{month.zfill(2)}.txt"
            )
            if path:
                Path(path).write_text(report_text, encoding="utf-8")

        ttk.Button(win, text="レポートを保存", command=_save).pack(pady=4)

        # 送信後クリア
        self._clear()
