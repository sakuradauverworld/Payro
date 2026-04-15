import tkinter as tk
from tkinter import ttk

class SettingsTab(ttk.Frame):
    def __init__(self, parent, *, app):
        super().__init__(parent)
        ttk.Label(self, text="設定タブ（実装予定）").pack(pady=20)
