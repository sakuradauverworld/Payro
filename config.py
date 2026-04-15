import json
import keyring
from pathlib import Path

_KEYRING_SERVICE = "payro"
_KEYRING_KEY = "gmail_app_password"

DEFAULTS = {
    "gmail_address": "",
    "subject_template": "{year}年{month}月分 給与明細",
    "body_template": "{name}様\n\n{month}月分の給与明細を添付いたします。\n\nご確認よろしくお願いいたします。",
    "filename_pattern_type": "contains",
}

class Config:
    def __init__(self, path: Path):
        self._path = Path(path)
        data = {}
        if self._path.exists():
            data = json.loads(self._path.read_text(encoding="utf-8"))
        merged = {**DEFAULTS, **data}
        self.gmail_address: str = merged["gmail_address"]
        self.subject_template: str = merged["subject_template"]
        self.body_template: str = merged["body_template"]
        self.filename_pattern_type: str = merged["filename_pattern_type"]

        # 旧バージョンからの移行: config.jsonにパスワードが残っていればkeyringに移す
        if "gmail_app_password" in data and data["gmail_app_password"]:
            keyring.set_password(_KEYRING_SERVICE, _KEYRING_KEY, data["gmail_app_password"])
            self._migrate_password_from_json()

        self.gmail_app_password: str = keyring.get_password(_KEYRING_SERVICE, _KEYRING_KEY) or ""

    def _migrate_password_from_json(self):
        """config.jsonからgmail_app_passwordを削除する（keyringに移行済みのため）"""
        if not self._path.exists():
            return
        data = json.loads(self._path.read_text(encoding="utf-8"))
        data.pop("gmail_app_password", None)
        self._path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    def save(self):
        self._path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "gmail_address": self.gmail_address,
            "subject_template": self.subject_template,
            "body_template": self.body_template,
            "filename_pattern_type": self.filename_pattern_type,
        }
        self._path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        keyring.set_password(_KEYRING_SERVICE, _KEYRING_KEY, self.gmail_app_password)

    def is_configured(self) -> bool:
        return bool(self.gmail_address and self.gmail_app_password)
