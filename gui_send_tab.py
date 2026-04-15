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
        self._build()
        self._try_init_dnd()

    def _try_init_dnd(self):
        try:
            from tkinterdnd2 import DND_FILES
            self._drop_area.drop_target_register(DND_FILES)
            self._drop_area.dnd_bind("<<Drop>>", self._on_drop)
        except Exception:
            pass  # tkinterdnd2 未対応環境ではD&D無効

    def _build(self):
        top = ttk.Frame(self)
        top.pack(fill="x", padx=8, pady=8)

        # 年月入力
        ttk.Label(top, text="対象年月:").pack(side="left")
        self._year_var = tk.StringVar(value=str(datetime.now().year))
        ttk.Entry(top, textvariable=self._year_var, width=6).pack(side="left", padx=(4, 0))
        ttk.Label(top, text="年").pack(side="left")
        self._month_var = tk.StringVar(value=str(datetime.now().month))
        ttk.Entry(top, textvariable=self._month_var, width=4).pack(side="left", padx=(4, 0))
        ttk.Label(top, text="月").pack(side="left", padx=(0, 12))

        ttk.Button(top, text="フォルダを選択", command=self._select_folder).pack(side="left", padx=4)
        ttk.Button(top, text="クリア", command=self._clear).pack(side="left")

        # ドロップエリア
        self._drop_area = tk.Label(
            self,
            text="ここにPDFファイルをドラッグ&ドロップ\nまたは上の「フォルダを選択」を使用",
            relief="groove", bg="#f0f0f0", height=4
        )
        self._drop_area.pack(fill="x", padx=8, pady=4)

        # マッチング一覧
        cols = ("status", "name", "email", "filename")
        self._tree = ttk.Treeview(self, columns=cols, show="headings", height=14)
        self._tree.heading("status", text="状態")
        self._tree.heading("name", text="名前")
        self._tree.heading("email", text="メールアドレス")
        self._tree.heading("filename", text="PDFファイル名")
        self._tree.column("status", width=60, anchor="center")
        self._tree.column("name", width=140)
        self._tree.column("email", width=220)
        self._tree.column("filename", width=300)
        self._tree.tag_configure("ok", background="#d4edda")
        self._tree.tag_configure("ng", background="#f8d7da")
        self._tree.pack(fill="both", expand=True, padx=8, pady=4)

        # 送信ボタン
        self._send_btn = ttk.Button(self, text="全員に送信", command=self._send, state="disabled")
        self._send_btn.pack(pady=8)

    def _select_folder(self):
        folder = filedialog.askdirectory(title="PDFフォルダを選択")
        if folder:
            self._pdf_paths = list(Path(folder).glob("*.pdf"))
            self._update_tree()

    def _on_drop(self, event):
        raw = event.data
        # tkinterdnd2はスペース区切りで複数ファイルを返す（パスにスペースがある場合は{}で囲まれる）
        paths = re.findall(r'\{([^}]+)\}|(\S+)', raw)
        self._pdf_paths = [Path(p[0] or p[1]) for p in paths if (p[0] or p[1]).lower().endswith(".pdf")]
        self._update_tree()

    def _clear(self):
        self._pdf_paths = []
        self._tree.delete(*self._tree.get_children())
        self._send_btn.config(state="disabled")

    def _update_tree(self):
        self._tree.delete(*self._tree.get_children())
        employees = self._app.employee_mgr.employees
        if not employees:
            messagebox.showwarning("従業員未登録", "先に「従業員管理」タブで従業員を登録してください。")
            return

        coord = SendCoordinator(employees=employees, pdf_paths=self._pdf_paths)
        self._match_results = coord.match()
        self._coord = coord

        for mr in self._match_results:
            if mr.pdf_path:
                tag = "ok"
                status = "✓"
                filename = mr.pdf_path.name
            else:
                tag = "ng"
                status = "✗"
                filename = "（PDFなし）"
            self._tree.insert("", "end",
                               values=(status, mr.employee.name, mr.employee.email, filename),
                               tags=(tag,))

        self._send_btn.config(state="normal")

    def _send(self):
        if not self._year_var.get().isdigit() or not self._month_var.get().isdigit():
            messagebox.showerror("入力エラー", "年月は数値で入力してください。")
            return
        cfg = self._app.config_data
        if not cfg.is_configured():
            messagebox.showerror("設定未完了", "「設定」タブでGmailアドレスとアプリパスワードを設定してください。")
            return

        if self._coord is None:
            return

        skipped = [mr for mr in self._match_results if mr.pdf_path is None]
        if skipped:
            names = "\n".join(f"  ・{mr.employee.name}" for mr in skipped)
            ok = messagebox.askyesno(
                "確認",
                f"以下の{len(skipped)}名はPDFがありません。スキップして残りに送信しますか？\n\n{names}"
            )
            if not ok:
                return

        self._send_btn.config(state="disabled", text="送信中...")
        year = self._year_var.get()
        month = self._month_var.get()
        subject = render(cfg.subject_template, name="", year=year, month=month)

        def _run():
            report = self._coord.execute(
                match_results=self._match_results,
                gmail_address=cfg.gmail_address,
                gmail_app_password=cfg.gmail_app_password,
                subject=subject,
                body_template=cfg.body_template,
                year=year,
                month=month,
            )
            self.after(0, lambda: self._on_done(report, year, month))

        threading.Thread(target=_run, daemon=True).start()

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
