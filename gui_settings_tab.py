import tkinter as tk
import webbrowser
from tkinter import ttk, messagebox


class SettingsTab(ttk.Frame):
    def __init__(self, parent, *, app):
        super().__init__(parent)
        self._app = app
        self._build()
        self._load()

    def _build(self):
        pad = {"padx": 12, "pady": 6}

        ttk.Label(self, text="Gmail設定", font=("", 11, "bold")).grid(row=0, column=0, columnspan=2, sticky="w", **pad)

        ttk.Label(self, text="Gmailアドレス:").grid(row=1, column=0, sticky="e", **pad)
        self._gmail_var = tk.StringVar()
        ttk.Entry(self, textvariable=self._gmail_var, width=40).grid(row=1, column=1, sticky="w", **pad)

        ttk.Label(self, text="アプリパスワード:").grid(row=2, column=0, sticky="e", **pad)
        self._password_var = tk.StringVar()
        ttk.Entry(self, textvariable=self._password_var, show="*", width=40).grid(row=2, column=1, sticky="w", **pad)

        ttk.Label(self, text="※ Googleアカウント → セキュリティ → アプリパスワード で発行してください",
                  foreground="gray").grid(row=3, column=0, columnspan=2, sticky="w", padx=12)

        link = tk.Label(self, text="https://myaccount.google.com/apppasswords",
                        foreground="blue", cursor="hand2")
        link.grid(row=4, column=0, columnspan=2, sticky="w", padx=12)
        link.bind("<Button-1>", lambda _: webbrowser.open("https://myaccount.google.com/apppasswords"))

        ttk.Separator(self, orient="horizontal").grid(row=5, column=0, columnspan=2, sticky="ew", pady=12)
        ttk.Label(self, text="メールテンプレート", font=("", 11, "bold")).grid(row=6, column=0, columnspan=2, sticky="w", **pad)

        ttk.Label(self, text="件名:").grid(row=7, column=0, sticky="e", **pad)
        self._subject_var = tk.StringVar()
        ttk.Entry(self, textvariable=self._subject_var, width=60).grid(row=7, column=1, sticky="w", **pad)

        ttk.Label(self, text="本文:").grid(row=8, column=0, sticky="ne", **pad)
        self._body_text = tk.Text(self, width=60, height=6)
        self._body_text.grid(row=8, column=1, sticky="w", **pad)

        ttk.Label(self, text="使用可能変数: {name} {year} {month}", foreground="gray").grid(
            row=9, column=1, sticky="w", padx=12)

        ttk.Button(self, text="保存", command=self._save).grid(row=10, column=1, sticky="e", **pad)

    def _load(self):
        cfg = self._app.config_data
        self._gmail_var.set(cfg.gmail_address)
        self._password_var.set(cfg.gmail_app_password)
        self._subject_var.set(cfg.subject_template)
        self._body_text.delete("1.0", "end")
        self._body_text.insert("1.0", cfg.body_template)

    def _save(self):
        cfg = self._app.config_data
        cfg.gmail_address = self._gmail_var.get().strip()
        cfg.gmail_app_password = self._password_var.get().strip()
        cfg.subject_template = self._subject_var.get().strip()
        cfg.body_template = self._body_text.get("1.0", "end-1c")
        cfg.save()
        messagebox.showinfo("保存完了", "設定を保存しました。")
