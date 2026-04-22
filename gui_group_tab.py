import re
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from recipient_manager import Recipient


def is_valid_email(email: str) -> bool:
    return bool(re.match(r'^[^@\s]+@[^@\s]+\.[^@\s]+$', email))


class GroupTab(ttk.Frame):
    def __init__(self, parent, *, app):
        super().__init__(parent)
        self._app = app
        self._current_group_id: str | None = None
        self._build()
        self._refresh_groups()

    def _build(self):
        # 左ペイン: グループ一覧
        left = ttk.Frame(self, width=320)
        left.pack(side="left", fill="y", padx=(8, 4), pady=8)
        left.pack_propagate(False)

        ttk.Label(left, text="グループ一覧", font=("", 10, "bold")).pack(anchor="w")

        cols = ("name", "template")
        self._group_tree = ttk.Treeview(left, columns=cols, show="headings", height=14, selectmode="browse")
        self._group_tree.heading("name", text="グループ名")
        self._group_tree.heading("template", text="テンプレート")
        self._group_tree.column("name", width=155)
        self._group_tree.column("template", width=155)
        self._group_tree.pack(fill="both", expand=True, pady=(4, 0))
        self._group_tree.bind("<<TreeviewSelect>>", self._on_group_select)
        self._group_tree.bind("<Double-Button-1>", self._on_group_double_click)
        self._group_tree.bind("<Button-1>", self._on_group_click)

        btn_frame = ttk.Frame(left)
        btn_frame.pack(fill="x", pady=(6, 0))
        ttk.Button(btn_frame, text="追加", command=self._add_group).pack(side="left", expand=True, fill="x", padx=1)
        ttk.Button(btn_frame, text="複製", command=self._duplicate_group).pack(side="left", expand=True, fill="x", padx=1)
        ttk.Button(btn_frame, text="削除", command=self._delete_group).pack(side="left", expand=True, fill="x", padx=1)

        ttk.Separator(self, orient="vertical").pack(side="left", fill="y", padx=4, pady=8)

        # 右ペイン: 宛先一覧
        right = ttk.Frame(self)
        right.pack(side="left", fill="both", expand=True, padx=(4, 8), pady=8)

        ttk.Label(right, text="宛先一覧", font=("", 10, "bold")).pack(anchor="w")

        cols = ("excluded", "name", "email")
        self._recip_tree = ttk.Treeview(right, columns=cols, show="headings", height=14)
        self._recip_tree.heading("excluded", text="送信対象")
        self._recip_tree.heading("name", text="名前")
        self._recip_tree.heading("email", text="メールアドレス")
        self._recip_tree.column("excluded", width=80, anchor="center")
        self._recip_tree.column("name", width=200)
        self._recip_tree.column("email", width=300)
        self._recip_tree.tag_configure("excluded", foreground="gray")
        self._recip_tree.bind("<Button-1>", self._on_recip_click)
        self._recip_tree.pack(fill="both", expand=True, pady=(4, 0))

        recip_btn_frame = ttk.Frame(right)
        recip_btn_frame.pack(fill="x", pady=(4, 0))
        ttk.Button(recip_btn_frame, text="追加", command=self._add_recipient).pack(side="left", padx=2)
        ttk.Button(recip_btn_frame, text="編集", command=self._edit_recipient).pack(side="left", padx=2)
        ttk.Button(recip_btn_frame, text="削除", command=self._delete_recipient).pack(side="left", padx=2)
        ttk.Separator(recip_btn_frame, orient="vertical").pack(side="left", fill="y", padx=8)
        ttk.Button(recip_btn_frame, text="CSVテンプレート出力", command=self._export_csv_template).pack(side="left", padx=2)
        ttk.Button(recip_btn_frame, text="CSVインポート", command=self._import_csv).pack(side="left", padx=2)

    def _refresh_groups(self):
        self._group_tree.delete(*self._group_tree.get_children())
        for group in self._app.recipient_mgr.groups:
            tmpl = self._app.template_mgr.get_by_id(group.template_id)
            tmpl_name = tmpl.name if tmpl else "（未設定）"
            self._group_tree.insert("", "end", values=(group.name, tmpl_name))
        if self._app.recipient_mgr.groups:
            current_ids = [g.id for g in self._app.recipient_mgr.groups]
            if self._current_group_id not in current_ids:
                self._current_group_id = self._app.recipient_mgr.groups[0].id
                self._group_tree.selection_set(self._group_tree.get_children()[0])
            else:
                idx = next(i for i, g in enumerate(self._app.recipient_mgr.groups) if g.id == self._current_group_id)
                self._group_tree.selection_set(self._group_tree.get_children()[idx])
        else:
            self._current_group_id = None
        self._refresh_recipients()
        if hasattr(self._app, 'send_tab'):
            self._app.send_tab.refresh_groups()

    def _refresh_template_combo(self):
        # テンプレートタブから呼ばれる。グループ一覧を再描画して最新のテンプレート名を反映する。
        self._refresh_groups()

    def _refresh_recipients(self):
        self._recip_tree.delete(*self._recip_tree.get_children())
        if not self._current_group_id:
            return
        for r in self._app.recipient_mgr.get_recipients(self._current_group_id):
            checkbox = "☐" if r.excluded else "☑"
            tags = ("excluded",) if r.excluded else ()
            self._recip_tree.insert("", "end",
                                    values=(checkbox, r.name, r.email),
                                    tags=tags)

    def _on_group_select(self, event):
        sel = self._group_tree.selection()
        if not sel:
            return
        idx = self._group_tree.index(sel[0])
        groups = self._app.recipient_mgr.groups
        if idx < len(groups):
            self._current_group_id = groups[idx].id
            self._refresh_recipients()

    def _on_group_click(self, event):
        column = self._group_tree.identify_column(event.x)
        row_id = self._group_tree.identify_row(event.y)
        if row_id and column == "#2":
            self._group_tree.after(10, lambda: self._edit_template_inline(row_id))

    def _on_group_double_click(self, event):
        column = self._group_tree.identify_column(event.x)
        row_id = self._group_tree.identify_row(event.y)
        if not row_id or column != "#1":
            return
        idx = self._group_tree.index(row_id)
        groups = self._app.recipient_mgr.groups
        if idx >= len(groups):
            return
        group = groups[idx]
        bbox = self._group_tree.bbox(row_id, "#1")
        if not bbox:
            return
        x, y, w, h = bbox
        entry_var = tk.StringVar(value=group.name)
        entry = ttk.Entry(self._group_tree, textvariable=entry_var)
        entry.place(x=x, y=y, width=w, height=h)
        entry.focus()
        entry.select_range(0, "end")

        def confirm(event=None):
            new_name = entry_var.get().strip()
            entry.destroy()
            if new_name and new_name != group.name:
                self._app.recipient_mgr.update_group(group.id, name=new_name)
                self._refresh_groups()

        entry.bind("<Return>", confirm)
        entry.bind("<FocusOut>", confirm)
        entry.bind("<Escape>", lambda e: entry.destroy())

    def _edit_template_inline(self, row_id):
        bbox = self._group_tree.bbox(row_id, "#2")
        if not bbox:
            return
        x, y, w, h = bbox
        idx = self._group_tree.index(row_id)
        groups = self._app.recipient_mgr.groups
        if idx >= len(groups):
            return
        group = groups[idx]
        templates = self._app.template_mgr.templates
        if not templates:
            return
        tmpl_names = [t.name for t in templates]
        current_tmpl = self._app.template_mgr.get_by_id(group.template_id)
        current_name = current_tmpl.name if current_tmpl else ""

        combo_var = tk.StringVar(value=current_name)
        combo = ttk.Combobox(self._group_tree, textvariable=combo_var, values=tmpl_names, state="readonly")
        combo.place(x=x, y=y, width=w, height=h)
        combo.focus()

        def on_select(event=None):
            new_name = combo_var.get()
            tmpl = next((t for t in templates if t.name == new_name), None)
            combo.destroy()
            if tmpl and tmpl.id != group.template_id:
                self._app.recipient_mgr.update_group(group.id, template_id=tmpl.id)
                self._refresh_groups()

        combo.bind("<<ComboboxSelected>>", on_select)
        combo.bind("<Escape>", lambda e: combo.destroy())
        combo.bind("<FocusOut>", lambda e: combo.destroy())

    def _add_group(self):
        templates = self._app.template_mgr.templates
        if not templates:
            messagebox.showwarning("テンプレートなし", "先に「テンプレート管理」タブでテンプレートを作成してください。")
            return
        dialog = _GroupNameDialog(self)
        if dialog.result:
            self._app.recipient_mgr.add_group(dialog.result, templates[0].id)
            self._refresh_groups()

    def _duplicate_group(self):
        if not self._current_group_id:
            messagebox.showwarning("未選択", "複製するグループを選択してください。")
            return
        self._app.recipient_mgr.duplicate_group(self._current_group_id)
        self._refresh_groups()

    def _delete_group(self):
        if not self._current_group_id:
            messagebox.showwarning("未選択", "削除するグループを選択してください。")
            return
        group = next(g for g in self._app.recipient_mgr.groups if g.id == self._current_group_id)
        if messagebox.askyesno("確認", f"グループ「{group.name}」を削除しますか？\n宛先も全て削除されます。"):
            self._app.recipient_mgr.remove_group(self._current_group_id)
            self._current_group_id = None
            self._refresh_groups()

    def _add_recipient(self):
        if not self._current_group_id:
            messagebox.showwarning("グループ未選択", "宛先を追加するグループを選択してください。")
            return
        dialog = _RecipientDialog(self, title="宛先を追加")
        if dialog.result:
            self._app.recipient_mgr.add_recipient(self._current_group_id, Recipient(**dialog.result))
            self._refresh_recipients()

    def _edit_recipient(self):
        sel = self._recip_tree.selection()
        if not sel:
            messagebox.showwarning("未選択", "編集する宛先を選択してください。")
            return
        idx = self._recip_tree.index(sel[0])
        r = self._app.recipient_mgr.get_recipients(self._current_group_id)[idx]
        dialog = _RecipientDialog(self, title="宛先を編集",
                                  initial={"name": r.name, "email": r.email})
        if dialog.result:
            new_r = Recipient(**dialog.result)
            new_r.excluded = r.excluded
            self._app.recipient_mgr.update_recipient(self._current_group_id, idx, new_r)
            self._refresh_recipients()

    def _delete_recipient(self):
        sel = self._recip_tree.selection()
        if not sel:
            messagebox.showwarning("未選択", "削除する宛先を選択してください。")
            return
        idx = self._recip_tree.index(sel[0])
        name = self._app.recipient_mgr.get_recipients(self._current_group_id)[idx].name
        if messagebox.askyesno("確認", f"「{name}」を削除しますか？"):
            self._app.recipient_mgr.remove_recipient(self._current_group_id, idx)
            self._refresh_recipients()

    def _on_recip_click(self, event):
        column = self._recip_tree.identify_column(event.x)
        row_id = self._recip_tree.identify_row(event.y)
        if column == "#1" and row_id and self._current_group_id:
            idx = self._recip_tree.index(row_id)
            recipients = self._app.recipient_mgr.get_recipients(self._current_group_id)
            r = recipients[idx]
            r.excluded = not r.excluded
            self._app.recipient_mgr.save_recipients(self._current_group_id)
            self._refresh_recipients()

    def _export_csv_template(self):
        path = filedialog.asksaveasfilename(
            title="CSVテンプレートを保存",
            defaultextension=".csv",
            filetypes=[("CSVファイル", "*.csv")],
            initialfile="宛先テンプレート.csv",
        )
        if path:
            Path(path).write_text(
                self._app.recipient_mgr.csv_template_headers(),
                encoding="utf-8-sig",  # Excel 対応
            )
            messagebox.showinfo("完了", f"CSVテンプレートを保存しました。\n{path}")

    def _import_csv(self):
        if not self._current_group_id:
            messagebox.showwarning("グループ未選択", "インポート先のグループを選択してください。")
            return
        path = filedialog.askopenfilename(
            title="CSVファイルを選択",
            filetypes=[("CSVファイル", "*.csv"), ("すべてのファイル", "*.*")],
        )
        if path:
            try:
                self._app.recipient_mgr.import_recipients(self._current_group_id, Path(path))
                self._refresh_recipients()
                messagebox.showinfo("インポート完了", "宛先をインポートしました。")
            except Exception as e:
                messagebox.showerror("インポートエラー", f"CSVの読み込みに失敗しました。\n{e}")


class _RecipientDialog(tk.Toplevel):
    def __init__(self, parent, *, title: str, initial: dict | None = None):
        super().__init__(parent)
        self.title(title)
        self.resizable(False, False)
        self.grab_set()
        self.result = None
        initial = initial or {"name": "", "email": ""}

        fields = [("名前:", "name"), ("メールアドレス:", "email")]
        self._vars = {}
        for i, (label, key) in enumerate(fields):
            ttk.Label(self, text=label).grid(row=i, column=0, padx=8, pady=4, sticky="e")
            var = tk.StringVar(value=initial[key])
            ttk.Entry(self, textvariable=var, width=36).grid(row=i, column=1, padx=8, pady=4)
            self._vars[key] = var

        btn_frame = ttk.Frame(self)
        btn_frame.grid(row=len(fields), column=0, columnspan=2, pady=8)
        ttk.Button(btn_frame, text="OK", command=self._ok).pack(side="left", padx=4)
        ttk.Button(btn_frame, text="キャンセル", command=self.destroy).pack(side="left", padx=4)
        self.wait_window()

    def _ok(self):
        values = {k: v.get().strip() for k, v in self._vars.items()}
        if not values["name"] or not values["email"]:
            messagebox.showwarning("入力エラー", "名前とメールアドレスは必須です。")
            return
        if not is_valid_email(values["email"]):
            messagebox.showwarning("入力エラー", "メールアドレスの形式が正しくありません。\n（例: name@example.com）")
            return
        self.result = values
        self.destroy()


class _GroupNameDialog(tk.Toplevel):
    _PLACEHOLDER = "La pilates ○○店"

    def __init__(self, parent):
        super().__init__(parent)
        self.title("グループ追加")
        self.resizable(False, False)
        self.grab_set()
        self.result = None

        ttk.Label(self, text="グループ名:").grid(row=0, column=0, padx=(12, 4), pady=12, sticky="e")
        self._entry = tk.Entry(self, width=30, foreground="gray")
        self._entry.insert(0, self._PLACEHOLDER)
        self._entry.grid(row=0, column=1, padx=(4, 12), pady=12)
        self._entry.bind("<FocusIn>", self._on_focus_in)
        self._entry.bind("<FocusOut>", self._on_focus_out)
        self._is_placeholder = True

        btn_frame = ttk.Frame(self)
        btn_frame.grid(row=1, column=0, columnspan=2, pady=(0, 12))
        ttk.Button(btn_frame, text="OK", command=self._ok).pack(side="left", padx=4)
        ttk.Button(btn_frame, text="キャンセル", command=self.destroy).pack(side="left", padx=4)
        self.wait_window()

    def _on_focus_in(self, event):
        if self._is_placeholder:
            self._entry.delete(0, "end")
            self._entry.config(foreground="black")
            self._is_placeholder = False

    def _on_focus_out(self, event):
        if not self._entry.get():
            self._entry.insert(0, self._PLACEHOLDER)
            self._entry.config(foreground="gray")
            self._is_placeholder = True

    def _ok(self):
        value = "" if self._is_placeholder else self._entry.get().strip()
        if not value:
            messagebox.showwarning("入力エラー", "グループ名を入力してください。")
            return
        self.result = value
        self.destroy()
