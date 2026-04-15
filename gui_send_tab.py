import tkinter as tk
from tkinter import ttk

class SendTab(ttk.Frame):
    def __init__(self, parent, *, app):
        super().__init__(parent)
        ttk.Label(self, text="送信タブ（実装予定）").pack(pady=20)
