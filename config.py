import json
from pathlib import Path

DEFAULTS = {
    "gmail_address": "",
    "gmail_app_password": "",
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
        self.gmail_app_password: str = merged["gmail_app_password"]
        self.subject_template: str = merged["subject_template"]
        self.body_template: str = merged["body_template"]
        self.filename_pattern_type: str = merged["filename_pattern_type"]

    def save(self):
        self._path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "gmail_address": self.gmail_address,
            "gmail_app_password": self.gmail_app_password,
            "subject_template": self.subject_template,
            "body_template": self.body_template,
            "filename_pattern_type": self.filename_pattern_type,
        }
        self._path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    def is_configured(self) -> bool:
        return bool(self.gmail_address and self.gmail_app_password)
