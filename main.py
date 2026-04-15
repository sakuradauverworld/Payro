import sys
from pathlib import Path
import tkinter as tk
from tkinter import ttk

try:
    from tkinterdnd2 import TkinterDnD as _TkDnD
    _TkBase = _TkDnD.Tk
except Exception:
    _TkBase = tk.Tk

# data/ フォルダをEXEと同じ場所に配置
DATA_DIR = Path(sys.executable).parent / "data" if getattr(sys, "frozen", False) else Path(__file__).parent / "data"
DATA_DIR.mkdir(exist_ok=True)

CONFIG_PATH = DATA_DIR / "config.json"
EMPLOYEES_PATH = DATA_DIR / "employees.csv"

from config import Config
from employee_manager import EmployeeManager

from gui_send_tab import SendTab
from gui_employee_tab import EmployeeTab
from gui_settings_tab import SettingsTab


class App(_TkBase):
    def __init__(self):
        super().__init__()
        self.title("Payro - 給与明細一括送信")
        self.geometry("900x600")
        self.resizable(True, True)

        self.config_data = Config(CONFIG_PATH)
        self.employee_mgr = EmployeeManager(EMPLOYEES_PATH)

        notebook = ttk.Notebook(self)
        notebook.pack(fill="both", expand=True, padx=8, pady=8)

        self.send_tab = SendTab(notebook, app=self)
        self.employee_tab = EmployeeTab(notebook, app=self)
        self.settings_tab = SettingsTab(notebook, app=self)

        notebook.add(self.send_tab, text="  送信  ")
        notebook.add(self.employee_tab, text="  従業員管理  ")
        notebook.add(self.settings_tab, text="  設定  ")

        if not self.config_data.is_configured():
            notebook.select(self.settings_tab)

if __name__ == "__main__":
    app = App()
    app.mainloop()
