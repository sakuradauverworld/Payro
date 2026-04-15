import re
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog


def is_valid_email(email: str) -> bool:
    return bool(re.match(r'^[^@\s]+@[^@\s]+\.[^@\s]+$', email))


class EmployeeTab(ttk.Frame):
    def __init__(self, parent, *, app):
        super().__init__(parent)
        self._app = app
        self._build()
        self._refresh()

    def _build(self):
        cols = ("name", "email", "filename_pattern")
        self._tree = ttk.Treeview(self, columns=cols, show="headings", height=18)
        self._tree.heading("name", text="名前")
        self._tree.heading("email", text="メールアドレス")
        self._tree.heading("filename_pattern", text="ファイル名キーワード")
        self._tree.column("name", width=160)
        self._tree.column("email", width=240)
        self._tree.column("filename_pattern", width=200)
        self._tree.pack(side="left", fill="both", expand=True, padx=(8, 0), pady=8)

        scrollbar = ttk.Scrollbar(self, orient="vertical", command=self._tree.yview)
        scrollbar.pack(side="left", fill="y", pady=8)
        self._tree.configure(yscrollcommand=scrollbar.set)

        btn_frame = ttk.Frame(self)
        btn_frame.pack(side="left", fill="y", padx=8, pady=8)
        ttk.Button(btn_frame, text="追加", command=self._add).pack(fill="x", pady=2)
        ttk.Button(btn_frame, text="編集", command=self._edit).pack(fill="x", pady=2)
        ttk.Button(btn_frame, text="削除", command=self._delete).pack(fill="x", pady=2)

    def _refresh(self):
        self._tree.delete(*self._tree.get_children())
        for emp in self._app.employee_mgr.employees:
            self._tree.insert("", "end", values=(emp.name, emp.email, emp.filename_pattern))

    def _add(self):
        dialog = _EmployeeDialog(self, title="従業員を追加")
        if dialog.result:
            from employee_manager import Employee
            self._app.employee_mgr.add(Employee(**dialog.result))
            self._app.employee_mgr.save()
            self._refresh()

    def _edit(self):
        selected = self._tree.selection()
        if not selected:
            messagebox.showwarning("未選択", "編集する従業員を選択してください。")
            return
        idx = self._tree.index(selected[0])
        emp = self._app.employee_mgr.employees[idx]
        dialog = _EmployeeDialog(self, title="従業員を編集",
                                  initial={"name": emp.name, "email": emp.email, "filename_pattern": emp.filename_pattern})
        if dialog.result:
            from employee_manager import Employee
            self._app.employee_mgr.update(idx, Employee(**dialog.result))
            self._app.employee_mgr.save()
            self._refresh()

    def _delete(self):
        selected = self._tree.selection()
        if not selected:
            messagebox.showwarning("未選択", "削除する従業員を選択してください。")
            return
        idx = self._tree.index(selected[0])
        name = self._app.employee_mgr.employees[idx].name
        if messagebox.askyesno("確認", f"「{name}」を削除しますか？"):
            self._app.employee_mgr.remove(idx)
            self._app.employee_mgr.save()
            self._refresh()


class _EmployeeDialog(tk.Toplevel):
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
