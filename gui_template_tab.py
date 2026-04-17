import tkinter as tk
from tkinter import messagebox, ttk


class TemplateTab(ttk.Frame):
    def __init__(self, parent, *, app):
        super().__init__(parent)
        self._app = app
        self._current_template_id: str | None = None
        self._build()
        self._refresh_list()

    def _build(self):
        # 左ペイン: テンプレート一覧
        left = ttk.Frame(self, width=200)
        left.pack(side="left", fill="y", padx=(8, 4), pady=8)
        left.pack_propagate(False)

        ttk.Label(left, text="テンプレート一覧", font=("", 10, "bold")).pack(anchor="w")

        self._listbox = tk.Listbox(left, selectmode="single", height=14)
        self._listbox.pack(fill="both", expand=True, pady=(4, 0))
        self._listbox.bind("<<ListboxSelect>>", self._on_select)

        btn_frame = ttk.Frame(left)
        btn_frame.pack(fill="x", pady=(6, 0))
        ttk.Button(btn_frame, text="追加", command=self._add).pack(side="left", expand=True, fill="x", padx=1)
        ttk.Button(btn_frame, text="削除", command=self._delete).pack(side="left", expand=True, fill="x", padx=1)

        ttk.Separator(self, orient="vertical").pack(side="left", fill="y", padx=4, pady=8)

        # 右ペイン: エディタ
        right = ttk.Frame(self)
        right.pack(side="left", fill="both", expand=True, padx=(4, 8), pady=8)

        pad = {"padx": 8, "pady": 4}

        ttk.Label(right, text="テンプレート編集", font=("", 10, "bold")).grid(row=0, column=0, columnspan=2, sticky="w", **pad)

        ttk.Label(right, text="名前:").grid(row=1, column=0, sticky="e", **pad)
        self._name_var = tk.StringVar()
        ttk.Entry(right, textvariable=self._name_var, width=40).grid(row=1, column=1, sticky="w", **pad)

        ttk.Label(right, text="件名:").grid(row=2, column=0, sticky="e", **pad)
        self._subject_var = tk.StringVar()
        ttk.Entry(right, textvariable=self._subject_var, width=60).grid(row=2, column=1, sticky="w", **pad)

        ttk.Label(right, text="本文:").grid(row=3, column=0, sticky="ne", **pad)
        self._body_text = tk.Text(right, width=60, height=8)
        self._body_text.grid(row=3, column=1, sticky="w", **pad)

        ttk.Label(right, text="使用可能変数: {name} {year} {month}", foreground="gray").grid(
            row=4, column=1, sticky="w", padx=8)

        ttk.Button(right, text="保存", command=self._save_template).grid(row=5, column=1, sticky="e", **pad)

    def _refresh_list(self):
        self._listbox.delete(0, "end")
        for tmpl in self._app.template_mgr.templates:
            self._listbox.insert("end", tmpl.name)
        if self._app.template_mgr.templates:
            current_ids = [t.id for t in self._app.template_mgr.templates]
            if self._current_template_id not in current_ids:
                self._current_template_id = self._app.template_mgr.templates[0].id
                self._listbox.selection_set(0)
            else:
                idx = next(i for i, t in enumerate(self._app.template_mgr.templates)
                           if t.id == self._current_template_id)
                self._listbox.selection_set(idx)
            self._load_editor()
        else:
            self._current_template_id = None
            self._clear_editor()

    def _on_select(self, event):
        sel = self._listbox.curselection()
        if not sel:
            return
        self._current_template_id = self._app.template_mgr.templates[sel[0]].id
        self._load_editor()

    def _load_editor(self):
        if not self._current_template_id:
            return
        tmpl = self._app.template_mgr.get_by_id(self._current_template_id)
        if tmpl:
            self._name_var.set(tmpl.name)
            self._subject_var.set(tmpl.subject)
            self._body_text.delete("1.0", "end")
            self._body_text.insert("1.0", tmpl.body)

    def _clear_editor(self):
        self._name_var.set("")
        self._subject_var.set("")
        self._body_text.delete("1.0", "end")

    def _add(self):
        tmpl = self._app.template_mgr.add(
            name="新しいテンプレート",
            subject="{year}年{month}月",
            body="{name}様\n\n",
        )
        self._current_template_id = tmpl.id
        self._refresh_list()

    def _delete(self):
        if not self._current_template_id:
            messagebox.showwarning("未選択", "削除するテンプレートを選択してください。")
            return
        tmpl = self._app.template_mgr.get_by_id(self._current_template_id)
        if messagebox.askyesno("確認", f"テンプレート「{tmpl.name}」を削除しますか？"):
            self._app.template_mgr.remove(self._current_template_id)
            self._current_template_id = None
            self._refresh_list()

    def _save_template(self):
        if not self._current_template_id:
            return
        name = self._name_var.get().strip()
        subject = self._subject_var.get().strip()
        body = self._body_text.get("1.0", "end-1c")
        if not name:
            messagebox.showwarning("入力エラー", "テンプレート名は必須です。")
            return
        self._app.template_mgr.update(self._current_template_id, name=name, subject=subject, body=body)
        self._refresh_list()
        messagebox.showinfo("保存完了", "テンプレートを保存しました。")
