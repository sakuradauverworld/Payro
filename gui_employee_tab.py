import tkinter as tk
from tkinter import ttk

class EmployeeTab(ttk.Frame):
    def __init__(self, parent, *, app):
        super().__init__(parent)
        ttk.Label(self, text="従業員管理タブ（実装予定）").pack(pady=20)
