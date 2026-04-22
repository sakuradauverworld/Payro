import sys
from pathlib import Path
import tkinter as tk
from tkinter import ttk

try:
    from tkinterdnd2 import TkinterDnD as _TkDnD
    _TkBase = _TkDnD.Tk
except Exception:
    _TkBase = tk.Tk

if getattr(sys, "frozen", False):
    if sys.platform == "darwin":
        DATA_DIR = Path.home() / "Library" / "Application Support" / "IkkiniOkuru" / "data"
    else:
        DATA_DIR = Path(sys.executable).parent / "data"
else:
    DATA_DIR = Path(__file__).parent / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

CONFIG_PATH = DATA_DIR / "config.json"

from migration import migrate
migrate(DATA_DIR, CONFIG_PATH)

from config import Config
from recipient_manager import RecipientManager
from template_manager import TemplateManager

from gui_send_tab import SendTab
from gui_group_tab import GroupTab
from gui_template_tab import TemplateTab
from gui_settings_tab import SettingsTab
from gui_usage_tab import UsageTab


class App(_TkBase):
    def __init__(self):
        super().__init__()
        self.title("一気に送る君")
        self.geometry("900x600")
        self.resizable(True, True)

        self.config_data = Config(CONFIG_PATH)
        self.recipient_mgr = RecipientManager(DATA_DIR)
        self.template_mgr = TemplateManager(DATA_DIR / "templates.json")

        self._notebook = ttk.Notebook(self)
        self._notebook.pack(fill="both", expand=True, padx=8, pady=8)

        self.send_tab = SendTab(self._notebook, app=self)
        self.group_tab = GroupTab(self._notebook, app=self)
        self.settings_tab = SettingsTab(self._notebook, app=self)
        self.template_tab = TemplateTab(self._notebook, app=self)
        self.usage_tab = UsageTab(self._notebook, app=self)

        self._notebook.add(self.send_tab, text="  送信  ")
        self._notebook.add(self.group_tab, text="  グループ管理  ")
        self._notebook.add(self.settings_tab, text="  ユーザー設定  ")
        self._notebook.add(self.template_tab, text="  テンプレート管理  ")
        self._notebook.add(self.usage_tab, text="  使い方  ")

        self._prev_tab = None
        self._notebook.bind("<<NotebookTabChanged>>", self._on_tab_changed)

        self.send_tab.refresh_groups()

        if not self.config_data.is_configured():
            self._notebook.select(self.settings_tab)

    def _on_tab_changed(self, event):
        current = self._notebook.nametowidget(self._notebook.select())
        if self._prev_tab is self.send_tab and current is not self.send_tab:
            self.send_tab._clear()
        self._prev_tab = current


if __name__ == "__main__":
    app = App()
    app.mainloop()
