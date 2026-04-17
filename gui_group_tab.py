import re
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, simpledialog, ttk

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
        left = ttk.Frame(self, width=220)
        left.pack(side="left", fill="y", padx=(8, 4), pady=8)
        left.pack_propagate(False)

        ttk.Label(left, text="グループ一覧", font=("", 10, "bold")).pack(anchor="w")

        self._group_listbox = tk.Listbox(left, selectmode="single", height=14)
        self._group_listbox.pack(fill="both", expand=True, pady=(4, 0))
        self._group_listbox.bind("<<ListboxSelect>>", self._on_group_select)
        self._group_listbox.bind("<Double-Button-1>", self._on_group_double_click)

        tmpl_frame = ttk.Frame(left)
        tmpl_frame.pack(fill="x", pady=(6, 0))
        ttk.Label(tmpl_frame, text="テンプレート:").pack(anchor="w")
        self._tmpl_var = tk.StringVar()
        self._tmpl_combo = ttk.Combobox(tmpl_frame, textvariable=self._tmpl_var, state="readonly", width=24)
        self._tmpl_combo.pack(fill="x")
        self._tmpl_combo.bind("<<ComboboxSelected>>", self._on_template_change)

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

        cols = ("excluded", "name", "email", "filename_pattern")
        self._recip_tree = ttk.Treeview(right, columns=cols, show="headings", height=14)
        self._recip_tree.heading("excluded", text="送信対象")
        self._recip_tree.heading("name", text="名前")
        self._recip_tree.heading("email", text="メールアドレス")
        self._recip_tree.heading("filename_pattern", text="ファイル名キーワード")
        self._recip_tree.column("excluded", width=80, anchor="center")
        self._recip_tree.column("name", width=160)
        self._recip_tree.column("email", width=240)
        self._recip_tree.column("filename_pattern", width=200)
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
        self._group_listbox.delete(0, "end")
        for group in self._app.recipient_mgr.groups:
            self._group_listbox.insert("end", group.name)
        self._refresh_template_combo()
        if self._app.recipient_mgr.groups:
            current_ids = [g.id for g in self._app.recipient_mgr.groups]
            if self._current_group_id not in current_ids:
                self._current_group_id = self._app.recipient_mgr.groups[0].id
                self._group_listbox.selection_set(0)
            else:
                idx = next(i for i, g in enumerate(self._app.recipient_mgr.groups) if g.id == self._current_group_id)
                self._group_listbox.selection_set(idx)
            self._refresh_template_for_current_group()
        else:
            self._current_group_id = None
        self._refresh_recipients()

    def _refresh_template_combo(self):
        self._tmpl_combo["values"] = [t.name for t in self._app.template_mgr.templates]

    def _refresh_template_for_current_group(self):
        if not self._current_group_id:
            self._tmpl_var.set("")
            return
        group = next((g for g in self._app.recipient_mgr.groups if g.id == self._current_group_id), None)
        if group:
            tmpl = self._app.template_mgr.get_by_id(group.template_id)
            self._tmpl_var.set(tmpl.name if tmpl else "")

    def _refresh_recipients(self):
        self._recip_tree.delete(*self._recip_tree.get_children())
        if not self._current_group_id:
            return
        for r in self._app.recipient_mgr.get_recipients(self._current_group_id):
            checkbox = "☐" if r.excluded else "☑"
            tags = ("excluded",) if r.excluded else ()
            self._recip_tree.insert("", "end",
                                    values=(checkbox, r.name, r.email, r.filename_pattern),
                                    tags=tags)

    def _on_group_select(self, event):
        sel = self._group_listbox.curselection()
        if not sel:
            return
        self._current_group_id = self._app.recipient_mgr.groups[sel[0]].id
        self._refresh_template_for_current_group()
        self._refresh_recipients()

    def _on_group_double_click(self, event):
        sel = self._group_listbox.curselection()
        if not sel:
            return
        idx = sel[0]
        group = self._app.recipient_mgr.groups[idx]
        bbox = self._group_listbox.bbox(idx)
        if not bbox:
            return
        x, y, w, h = bbox
        entry_var = tk.StringVar(value=group.name)
        entry = ttk.Entry(self._group_listbox, textvariable=entry_var)
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

    def _on_template_change(self, event):
        if not self._current_group_id:
            return
        selected_name = self._tmpl_var.get()
        tmpl = next((t for t in self._app.template_mgr.templates if t.name == selected_name), None)
        if tmpl:
            self._app.recipient_mgr.update_group(self._current_group_id, template_id=tmpl.id)

    def _add_group(self):
        templates = self._app.template_mgr.templates
        if not templates:
            messagebox.showwarning("テンプレートなし", "先に「テンプレート管理」タブでテンプレートを作成してください。")
            return
        name = simpledialog.askstring("グループ追加", "グループ名:", parent=self)
        if name and name.strip():
            self._app.recipient_mgr.add_group(name.strip(), templates[0].id)
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
                                  initial={"name": r.name, "email": r.email, "filename_pattern": r.filename_pattern})
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
        initial = initial or {"name": "", "email": "", "filename_pattern": ""}

        fields = [("名前:", "name"), ("メールアドレス:", "email"), ("ファイル名キーワード:", "filename_pattern")]
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
