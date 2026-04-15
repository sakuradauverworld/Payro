# Payro 実装計画

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 毎月の給与明細PDFをGmailで従業員全員に一括送信するGUIデスクトップアプリ（EXE配布）を実装する

**Architecture:** Python + tkinter の3タブGUIアプリ。コアロジック（設定・従業員管理・テンプレート・メール送信）をそれぞれ独立したモジュールに分離し、GUIから呼び出す構成。データはJSON（設定）とCSV（従業員リスト）でローカル保存。

**Tech Stack:** Python 3.11+, tkinter, tkinterdnd2, smtplib, PyInstaller, pytest

---

## ファイル構成

```
payro/
├── main.py                  # GUIエントリーポイント・メインウィンドウ（タブ管理）
├── config.py                # 設定のJSON読み書き
├── employee_manager.py      # 従業員リストのCSV読み書き
├── template_engine.py       # メールテンプレート変数差し込み
├── mail_sender.py           # Gmail SMTP送信ロジック
├── requirements.txt         # 依存ライブラリ
├── data/                    # 実行時データ（EXEと同フォルダに生成）
│   ├── employees.csv
│   └── config.json
└── tests/
    ├── test_config.py
    ├── test_employee_manager.py
    ├── test_template_engine.py
    └── test_mail_sender.py
```

---

## Task 1: プロジェクトセットアップ

**Files:**
- Create: `payro/requirements.txt`
- Create: `payro/data/config.json`（デフォルト設定）
- Create: `payro/data/employees.csv`（ヘッダーのみ）

- [ ] **Step 1: requirements.txtを作成する**

```
tkinterdnd2==0.3.0
pytest==8.3.5
pyinstaller==6.11.1
```

- [ ] **Step 2: デフォルトconfig.jsonを作成する**

`payro/data/config.json`:
```json
{
  "gmail_address": "",
  "gmail_app_password": "",
  "subject_template": "{year}年{month}月分 給与明細",
  "body_template": "{name}様\n\n{month}月分の給与明細を添付いたします。\n\nご確認よろしくお願いいたします。",
  "filename_pattern_type": "contains"
}
```

- [ ] **Step 3: デフォルトemployees.csvを作成する**

`payro/data/employees.csv`:
```csv
name,email,filename_pattern
```

- [ ] **Step 4: 依存ライブラリをインストールする**

```bash
cd payro
pip install -r requirements.txt
```

期待出力: `Successfully installed tkinterdnd2-0.3.0`

- [ ] **Step 5: コミット**

```bash
git init
git add requirements.txt data/
git commit -m "chore: プロジェクト初期セットアップ"
```

---

## Task 2: config.py — 設定の読み書き

**Files:**
- Create: `payro/config.py`
- Create: `payro/tests/test_config.py`

- [ ] **Step 1: テストを書く**

`payro/tests/test_config.py`:
```python
import json
import pytest
from pathlib import Path
from config import Config

@pytest.fixture
def tmp_config(tmp_path):
    config_path = tmp_path / "config.json"
    config_path.write_text(json.dumps({
        "gmail_address": "test@gmail.com",
        "gmail_app_password": "abcd efgh ijkl mnop",
        "subject_template": "{year}年{month}月分 給与明細",
        "body_template": "{name}様\n\n添付をご確認ください。",
        "filename_pattern_type": "contains"
    }), encoding="utf-8")
    return config_path

def test_load(tmp_config):
    cfg = Config(tmp_config)
    assert cfg.gmail_address == "test@gmail.com"
    assert cfg.gmail_app_password == "abcd efgh ijkl mnop"
    assert cfg.subject_template == "{year}年{month}月分 給与明細"
    assert cfg.filename_pattern_type == "contains"

def test_save(tmp_config):
    cfg = Config(tmp_config)
    cfg.gmail_address = "new@gmail.com"
    cfg.save()
    cfg2 = Config(tmp_config)
    assert cfg2.gmail_address == "new@gmail.com"

def test_is_configured_false(tmp_config):
    cfg = Config(tmp_config)
    cfg.gmail_address = ""
    assert cfg.is_configured() is False

def test_is_configured_true(tmp_config):
    cfg = Config(tmp_config)
    assert cfg.is_configured() is True

def test_missing_file_creates_defaults(tmp_path):
    config_path = tmp_path / "config.json"
    cfg = Config(config_path)
    assert cfg.gmail_address == ""
    assert cfg.subject_template == "{year}年{month}月分 給与明細"
```

- [ ] **Step 2: テストが失敗することを確認する**

```bash
cd payro
python -m pytest tests/test_config.py -v
```

期待出力: `ModuleNotFoundError: No module named 'config'`

- [ ] **Step 3: config.pyを実装する**

`payro/config.py`:
```python
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
```

- [ ] **Step 4: テストが通ることを確認する**

```bash
python -m pytest tests/test_config.py -v
```

期待出力: `5 passed`

- [ ] **Step 5: コミット**

```bash
git add config.py tests/test_config.py
git commit -m "feat: 設定の読み書き(config.py)を実装"
```

---

## Task 3: employee_manager.py — 従業員リスト管理

**Files:**
- Create: `payro/employee_manager.py`
- Create: `payro/tests/test_employee_manager.py`

- [ ] **Step 1: テストを書く**

`payro/tests/test_employee_manager.py`:
```python
import pytest
from pathlib import Path
from employee_manager import EmployeeManager, Employee

@pytest.fixture
def tmp_csv(tmp_path):
    csv_path = tmp_path / "employees.csv"
    csv_path.write_text(
        "name,email,filename_pattern\n山田太郎,yamada@example.com,山田太郎\n佐藤花子,sato@example.com,佐藤花子\n",
        encoding="utf-8"
    )
    return csv_path

def test_load(tmp_csv):
    mgr = EmployeeManager(tmp_csv)
    assert len(mgr.employees) == 2
    assert mgr.employees[0].name == "山田太郎"
    assert mgr.employees[0].email == "yamada@example.com"
    assert mgr.employees[0].filename_pattern == "山田太郎"

def test_add_and_save(tmp_csv):
    mgr = EmployeeManager(tmp_csv)
    mgr.add(Employee(name="田中次郎", email="tanaka@example.com", filename_pattern="田中次郎"))
    mgr.save()
    mgr2 = EmployeeManager(tmp_csv)
    assert len(mgr2.employees) == 3
    assert mgr2.employees[2].name == "田中次郎"

def test_remove(tmp_csv):
    mgr = EmployeeManager(tmp_csv)
    mgr.remove(0)
    assert len(mgr.employees) == 1
    assert mgr.employees[0].name == "佐藤花子"

def test_update(tmp_csv):
    mgr = EmployeeManager(tmp_csv)
    mgr.update(0, Employee(name="山田太郎", email="new@example.com", filename_pattern="山田太郎"))
    assert mgr.employees[0].email == "new@example.com"

def test_find_by_filename(tmp_csv):
    mgr = EmployeeManager(tmp_csv)
    emp = mgr.find_by_filename("給与明細_山田太郎_202604.pdf")
    assert emp is not None
    assert emp.name == "山田太郎"

def test_find_by_filename_no_match(tmp_csv):
    mgr = EmployeeManager(tmp_csv)
    emp = mgr.find_by_filename("給与明細_鈴木一郎_202604.pdf")
    assert emp is None

def test_missing_file_creates_empty(tmp_path):
    mgr = EmployeeManager(tmp_path / "employees.csv")
    assert mgr.employees == []
```

- [ ] **Step 2: テストが失敗することを確認する**

```bash
python -m pytest tests/test_employee_manager.py -v
```

期待出力: `ModuleNotFoundError: No module named 'employee_manager'`

- [ ] **Step 3: employee_manager.pyを実装する**

`payro/employee_manager.py`:
```python
import csv
from dataclasses import dataclass
from pathlib import Path

@dataclass
class Employee:
    name: str
    email: str
    filename_pattern: str

class EmployeeManager:
    def __init__(self, path: Path):
        self._path = Path(path)
        self.employees: list[Employee] = []
        if self._path.exists():
            self._load()

    def _load(self):
        with self._path.open(encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            self.employees = [
                Employee(
                    name=row["name"],
                    email=row["email"],
                    filename_pattern=row["filename_pattern"],
                )
                for row in reader
            ]

    def save(self):
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with self._path.open("w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["name", "email", "filename_pattern"])
            writer.writeheader()
            for emp in self.employees:
                writer.writerow({"name": emp.name, "email": emp.email, "filename_pattern": emp.filename_pattern})

    def add(self, employee: Employee):
        self.employees.append(employee)

    def remove(self, index: int):
        self.employees.pop(index)

    def update(self, index: int, employee: Employee):
        self.employees[index] = employee

    def find_by_filename(self, filename: str) -> Employee | None:
        for emp in self.employees:
            if emp.filename_pattern in filename:
                return emp
        return None
```

- [ ] **Step 4: テストが通ることを確認する**

```bash
python -m pytest tests/test_employee_manager.py -v
```

期待出力: `8 passed`

- [ ] **Step 5: コミット**

```bash
git add employee_manager.py tests/test_employee_manager.py
git commit -m "feat: 従業員リスト管理(employee_manager.py)を実装"
```

---

## Task 4: template_engine.py — メールテンプレート差し込み

**Files:**
- Create: `payro/template_engine.py`
- Create: `payro/tests/test_template_engine.py`

- [ ] **Step 1: テストを書く**

`payro/tests/test_template_engine.py`:
```python
from template_engine import render

def test_render_name_and_month():
    result = render("{name}様、{month}月分の給与明細を送付します。", name="山田太郎", month="4", year="2026")
    assert result == "山田太郎様、4月分の給与明細を送付します。"

def test_render_year():
    result = render("{year}年{month}月分 給与明細", name="佐藤花子", month="12", year="2026")
    assert result == "2026年12月分 給与明細"

def test_render_unknown_placeholder_remains():
    result = render("{name}様、{unknown}はそのまま", name="山田太郎", month="4", year="2026")
    assert result == "山田太郎様、{unknown}はそのまま"
```

- [ ] **Step 2: テストが失敗することを確認する**

```bash
python -m pytest tests/test_template_engine.py -v
```

期待出力: `ModuleNotFoundError: No module named 'template_engine'`

- [ ] **Step 3: template_engine.pyを実装する**

`payro/template_engine.py`:
```python
def render(template: str, *, name: str, month: str, year: str) -> str:
    return template.format_map(_SafeDict(name=name, month=month, year=year))

class _SafeDict(dict):
    def __missing__(self, key: str) -> str:
        return "{" + key + "}"
```

- [ ] **Step 4: テストが通ることを確認する**

```bash
python -m pytest tests/test_template_engine.py -v
```

期待出力: `3 passed`

- [ ] **Step 5: コミット**

```bash
git add template_engine.py tests/test_template_engine.py
git commit -m "feat: メールテンプレート差し込み(template_engine.py)を実装"
```

---

## Task 5: mail_sender.py — Gmail SMTP送信

**Files:**
- Create: `payro/mail_sender.py`
- Create: `payro/tests/test_mail_sender.py`

- [ ] **Step 1: テストを書く**

`payro/tests/test_mail_sender.py`:
```python
import smtplib
from unittest.mock import MagicMock, patch
from pathlib import Path
from mail_sender import MailSender, SendResult

@patch("mail_sender.smtplib.SMTP_SSL")
def test_send_success(mock_smtp_class, tmp_path):
    pdf = tmp_path / "山田太郎_202604.pdf"
    pdf.write_bytes(b"%PDF-1.4 fake")

    mock_server = MagicMock()
    mock_smtp_class.return_value.__enter__ = MagicMock(return_value=mock_server)
    mock_smtp_class.return_value.__exit__ = MagicMock(return_value=False)

    sender = MailSender(gmail_address="test@gmail.com", gmail_app_password="xxxx")
    result = sender.send(
        to_email="yamada@example.com",
        subject="2026年4月分 給与明細",
        body="山田太郎様\n\n添付をご確認ください。",
        pdf_path=pdf,
    )
    assert result == SendResult.SUCCESS
    assert mock_server.sendmail.called

@patch("mail_sender.smtplib.SMTP_SSL")
def test_send_auth_failure(mock_smtp_class, tmp_path):
    pdf = tmp_path / "dummy.pdf"
    pdf.write_bytes(b"%PDF-1.4 fake")

    mock_smtp_class.return_value.__enter__.side_effect = smtplib.SMTPAuthenticationError(535, b"Bad credentials")

    sender = MailSender(gmail_address="bad@gmail.com", gmail_app_password="wrong")
    result = sender.send(
        to_email="yamada@example.com",
        subject="件名",
        body="本文",
        pdf_path=pdf,
    )
    assert result == SendResult.AUTH_ERROR

@patch("mail_sender.smtplib.SMTP_SSL")
def test_send_network_failure(mock_smtp_class, tmp_path):
    pdf = tmp_path / "dummy.pdf"
    pdf.write_bytes(b"%PDF-1.4 fake")

    mock_smtp_class.return_value.__enter__.side_effect = OSError("Connection refused")

    sender = MailSender(gmail_address="test@gmail.com", gmail_app_password="xxxx")
    result = sender.send(
        to_email="yamada@example.com",
        subject="件名",
        body="本文",
        pdf_path=pdf,
    )
    assert result == SendResult.NETWORK_ERROR
```

- [ ] **Step 2: テストが失敗することを確認する**

```bash
python -m pytest tests/test_mail_sender.py -v
```

期待出力: `ModuleNotFoundError: No module named 'mail_sender'`

- [ ] **Step 3: mail_sender.pyを実装する**

`payro/mail_sender.py`:
```python
import smtplib
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from enum import Enum
from pathlib import Path

class SendResult(Enum):
    SUCCESS = "success"
    AUTH_ERROR = "auth_error"
    NETWORK_ERROR = "network_error"

class MailSender:
    SMTP_HOST = "smtp.gmail.com"
    SMTP_PORT = 465

    def __init__(self, gmail_address: str, gmail_app_password: str):
        self._address = gmail_address
        self._password = gmail_app_password

    def send(self, *, to_email: str, subject: str, body: str, pdf_path: Path) -> SendResult:
        msg = MIMEMultipart()
        msg["From"] = self._address
        msg["To"] = to_email
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain", "utf-8"))

        with Path(pdf_path).open("rb") as f:
            part = MIMEApplication(f.read(), _subtype="pdf")
            part.add_header("Content-Disposition", "attachment", filename=Path(pdf_path).name)
            msg.attach(part)

        try:
            with smtplib.SMTP_SSL(self.SMTP_HOST, self.SMTP_PORT) as server:
                server.login(self._address, self._password)
                server.sendmail(self._address, to_email, msg.as_string())
            return SendResult.SUCCESS
        except smtplib.SMTPAuthenticationError:
            return SendResult.AUTH_ERROR
        except OSError:
            return SendResult.NETWORK_ERROR
```

- [ ] **Step 4: テストが通ることを確認する**

```bash
python -m pytest tests/test_mail_sender.py -v
```

期待出力: `3 passed`

- [ ] **Step 5: コミット**

```bash
git add mail_sender.py tests/test_mail_sender.py
git commit -m "feat: Gmail SMTP送信(mail_sender.py)を実装"
```

---

## Task 6: 送信コーディネーター — PDFマッチングと送信実行

**Files:**
- Create: `payro/send_coordinator.py`
- Create: `payro/tests/test_send_coordinator.py`

このモジュールはGUIから呼ばれるコアロジックをまとめる。PDFリストと従業員リストを照合し、送信を実行してレポートを返す。

- [ ] **Step 1: テストを書く**

`payro/tests/test_send_coordinator.py`:
```python
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch
from employee_manager import Employee
from mail_sender import SendResult
from send_coordinator import SendCoordinator, MatchResult, SendReport

@pytest.fixture
def employees():
    return [
        Employee(name="山田太郎", email="yamada@example.com", filename_pattern="山田太郎"),
        Employee(name="佐藤花子", email="sato@example.com", filename_pattern="佐藤花子"),
        Employee(name="田中次郎", email="tanaka@example.com", filename_pattern="田中次郎"),
    ]

@pytest.fixture
def pdf_paths(tmp_path):
    p1 = tmp_path / "給与明細_山田太郎_202604.pdf"
    p2 = tmp_path / "給与明細_佐藤花子_202604.pdf"
    p1.write_bytes(b"%PDF fake")
    p2.write_bytes(b"%PDF fake")
    return [p1, p2]

def test_match(employees, pdf_paths):
    coord = SendCoordinator(employees=employees, pdf_paths=pdf_paths)
    results = coord.match()
    matched = [r for r in results if r.pdf_path is not None]
    unmatched = [r for r in results if r.pdf_path is None]
    assert len(matched) == 2
    assert len(unmatched) == 1
    assert unmatched[0].employee.name == "田中次郎"

@patch("send_coordinator.MailSender")
def test_execute_skips_unmatched(mock_sender_class, employees, pdf_paths):
    mock_sender = MagicMock()
    mock_sender.send.return_value = SendResult.SUCCESS
    mock_sender_class.return_value = mock_sender

    coord = SendCoordinator(employees=employees, pdf_paths=pdf_paths)
    match_results = coord.match()
    report = coord.execute(
        match_results=match_results,
        gmail_address="test@gmail.com",
        gmail_app_password="xxxx",
        subject="給与明細",
        body_template="{name}様",
        year="2026",
        month="4",
    )
    assert report.success_count == 2
    assert report.skip_count == 1
    assert report.failure_count == 0

@patch("send_coordinator.MailSender")
def test_execute_records_failure(mock_sender_class, employees, pdf_paths):
    mock_sender = MagicMock()
    mock_sender.send.return_value = SendResult.NETWORK_ERROR
    mock_sender_class.return_value = mock_sender

    coord = SendCoordinator(employees=employees, pdf_paths=pdf_paths)
    match_results = coord.match()
    report = coord.execute(
        match_results=match_results,
        gmail_address="test@gmail.com",
        gmail_app_password="xxxx",
        subject="給与明細",
        body_template="{name}様",
        year="2026",
        month="4",
    )
    assert report.failure_count == 2
    assert report.success_count == 0
```

- [ ] **Step 2: テストが失敗することを確認する**

```bash
python -m pytest tests/test_send_coordinator.py -v
```

期待出力: `ModuleNotFoundError: No module named 'send_coordinator'`

- [ ] **Step 3: send_coordinator.pyを実装する**

`payro/send_coordinator.py`:
```python
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from employee_manager import Employee
from mail_sender import MailSender, SendResult
from template_engine import render


@dataclass
class MatchResult:
    employee: Employee
    pdf_path: Path | None


@dataclass
class SendReport:
    sent_at: datetime = field(default_factory=datetime.now)
    success: list[str] = field(default_factory=list)
    failures: list[str] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)

    @property
    def success_count(self) -> int:
        return len(self.success)

    @property
    def failure_count(self) -> int:
        return len(self.failures)

    @property
    def skip_count(self) -> int:
        return len(self.skipped)

    def to_text(self, year: str, month: str) -> str:
        lines = [
            f"送信日時: {self.sent_at.strftime('%Y-%m-%d %H:%M:%S')}",
            f"対象月: {year}年{month}月",
            "",
            f"成功 ({self.success_count}名):",
        ]
        for s in self.success:
            lines.append(f"  - {s}")
        lines += ["", f"失敗 ({self.failure_count}名):"]
        for f_ in self.failures:
            lines.append(f"  - {f_}")
        lines += ["", f"スキップ ({self.skip_count}名):"]
        for s in self.skipped:
            lines.append(f"  - {s} - PDFなし")
        return "\n".join(lines)


class SendCoordinator:
    def __init__(self, *, employees: list[Employee], pdf_paths: list[Path]):
        self._employees = employees
        self._pdf_paths = pdf_paths

    def match(self) -> list[MatchResult]:
        results = []
        for emp in self._employees:
            matched_pdf = next(
                (p for p in self._pdf_paths if emp.filename_pattern in p.name),
                None,
            )
            results.append(MatchResult(employee=emp, pdf_path=matched_pdf))
        return results

    def execute(
        self,
        *,
        match_results: list[MatchResult],
        gmail_address: str,
        gmail_app_password: str,
        subject: str,
        body_template: str,
        year: str,
        month: str,
    ) -> SendReport:
        sender = MailSender(gmail_address=gmail_address, gmail_app_password=gmail_app_password)
        report = SendReport()

        for mr in match_results:
            emp = mr.employee
            if mr.pdf_path is None:
                report.skipped.append(emp.name)
                continue

            body = render(body_template, name=emp.name, month=month, year=year)
            result = sender.send(
                to_email=emp.email,
                subject=subject,
                body=body,
                pdf_path=mr.pdf_path,
            )
            if result == SendResult.SUCCESS:
                report.success.append(f"{emp.name} <{emp.email}>")
            else:
                report.failures.append(f"{emp.name} <{emp.email}> - {result.value}")

        return report
```

- [ ] **Step 4: テストが通ることを確認する**

```bash
python -m pytest tests/test_send_coordinator.py -v
```

期待出力: `4 passed`

- [ ] **Step 5: コアロジック全体のテストを通す**

```bash
python -m pytest tests/ -v
```

期待出力: `全テスト passed`

- [ ] **Step 6: コミット**

```bash
git add send_coordinator.py tests/test_send_coordinator.py
git commit -m "feat: 送信コーディネーター(send_coordinator.py)を実装"
```

---

## Task 7: main.py — GUIメインウィンドウ（タブ骨格）

**Files:**
- Create: `payro/main.py`

ここからはGUIのため手動確認がメイン。まずタブ骨格だけ作る。

- [ ] **Step 1: main.pyのタブ骨格を実装する**

`payro/main.py`:
```python
import sys
from pathlib import Path
import tkinter as tk
from tkinter import ttk

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


class App(tk.Tk):
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
```

- [ ] **Step 2: 空のGUIモジュールを仮作成する（後のタスクで実装）**

`payro/gui_send_tab.py`:
```python
import tkinter as tk
from tkinter import ttk

class SendTab(ttk.Frame):
    def __init__(self, parent, *, app):
        super().__init__(parent)
        ttk.Label(self, text="送信タブ（実装予定）").pack(pady=20)
```

`payro/gui_employee_tab.py`:
```python
import tkinter as tk
from tkinter import ttk

class EmployeeTab(ttk.Frame):
    def __init__(self, parent, *, app):
        super().__init__(parent)
        ttk.Label(self, text="従業員管理タブ（実装予定）").pack(pady=20)
```

`payro/gui_settings_tab.py`:
```python
import tkinter as tk
from tkinter import ttk

class SettingsTab(ttk.Frame):
    def __init__(self, parent, *, app):
        super().__init__(parent)
        ttk.Label(self, text="設定タブ（実装予定）").pack(pady=20)
```

- [ ] **Step 3: 手動確認 — アプリが起動してタブが表示されることを確認する**

```bash
python main.py
```

確認項目:
- ウィンドウが開く
- 「送信」「従業員管理」「設定」の3タブが表示される
- Gmailが未設定なら設定タブが初期選択される

- [ ] **Step 4: コミット**

```bash
git add main.py gui_send_tab.py gui_employee_tab.py gui_settings_tab.py
git commit -m "feat: GUIメインウィンドウとタブ骨格を実装"
```

---

## Task 8: gui_settings_tab.py — 設定タブ

**Files:**
- Modify: `payro/gui_settings_tab.py`

- [ ] **Step 1: 設定タブを実装する**

`payro/gui_settings_tab.py`:
```python
import tkinter as tk
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

        ttk.Separator(self, orient="horizontal").grid(row=4, column=0, columnspan=2, sticky="ew", pady=12)
        ttk.Label(self, text="メールテンプレート", font=("", 11, "bold")).grid(row=5, column=0, columnspan=2, sticky="w", **pad)

        ttk.Label(self, text="件名:").grid(row=6, column=0, sticky="e", **pad)
        self._subject_var = tk.StringVar()
        ttk.Entry(self, textvariable=self._subject_var, width=60).grid(row=6, column=1, sticky="w", **pad)

        ttk.Label(self, text="本文:").grid(row=7, column=0, sticky="ne", **pad)
        self._body_text = tk.Text(self, width=60, height=6)
        self._body_text.grid(row=7, column=1, sticky="w", **pad)

        ttk.Label(self, text="使用可能変数: {name} {year} {month}", foreground="gray").grid(
            row=8, column=1, sticky="w", padx=12)

        ttk.Button(self, text="保存", command=self._save).grid(row=9, column=1, sticky="e", **pad)

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
```

- [ ] **Step 2: 手動確認**

```bash
python main.py
```

確認項目:
- 設定タブにGmailアドレス・パスワード・件名・本文の入力欄がある
- 「保存」ボタンで `data/config.json` に書き込まれる
- 再起動後も入力内容が残っている

- [ ] **Step 3: コミット**

```bash
git add gui_settings_tab.py
git commit -m "feat: 設定タブGUIを実装"
```

---

## Task 9: gui_employee_tab.py — 従業員管理タブ

**Files:**
- Modify: `payro/gui_employee_tab.py`

- [ ] **Step 1: 従業員管理タブを実装する**

`payro/gui_employee_tab.py`:
```python
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog


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
        self.result = {k: v.get().strip() for k, v in self._vars.items()}
        self.destroy()
```

- [ ] **Step 2: 手動確認**

```bash
python main.py
```

確認項目:
- 「従業員管理」タブで一覧が表示される
- 「追加」ボタンでダイアログが開き、名前・メール・キーワードを入力して保存できる
- 「編集」「削除」が正常に動作する
- `data/employees.csv` に反映されている

- [ ] **Step 3: コミット**

```bash
git add gui_employee_tab.py
git commit -m "feat: 従業員管理タブGUIを実装"
```

---

## Task 10: gui_send_tab.py — 送信タブ

**Files:**
- Modify: `payro/gui_send_tab.py`

- [ ] **Step 1: 送信タブを実装する**

`payro/gui_send_tab.py`:
```python
import threading
import tkinter as tk
from datetime import datetime
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from send_coordinator import SendCoordinator
from template_engine import render


class SendTab(ttk.Frame):
    def __init__(self, parent, *, app):
        super().__init__(parent)
        self._app = app
        self._pdf_paths: list[Path] = []
        self._build()
        self._try_init_dnd()

    def _try_init_dnd(self):
        try:
            from tkinterdnd2 import DND_FILES
            self._drop_area.drop_target_register(DND_FILES)
            self._drop_area.dnd_bind("<<Drop>>", self._on_drop)
        except Exception:
            pass  # tkinterdnd2 未対応環境ではD&D無効

    def _build(self):
        top = ttk.Frame(self)
        top.pack(fill="x", padx=8, pady=8)

        # 年月入力
        ttk.Label(top, text="対象年月:").pack(side="left")
        self._year_var = tk.StringVar(value=str(datetime.now().year))
        ttk.Entry(top, textvariable=self._year_var, width=6).pack(side="left", padx=(4, 0))
        ttk.Label(top, text="年").pack(side="left")
        self._month_var = tk.StringVar(value=str(datetime.now().month))
        ttk.Entry(top, textvariable=self._month_var, width=4).pack(side="left", padx=(4, 0))
        ttk.Label(top, text="月").pack(side="left", padx=(0, 12))

        ttk.Button(top, text="フォルダを選択", command=self._select_folder).pack(side="left", padx=4)
        ttk.Button(top, text="クリア", command=self._clear).pack(side="left")

        # ドロップエリア
        self._drop_area = tk.Label(
            self,
            text="ここにPDFファイルをドラッグ&ドロップ\nまたは上の「フォルダを選択」を使用",
            relief="groove", bg="#f0f0f0", height=4
        )
        self._drop_area.pack(fill="x", padx=8, pady=4)

        # マッチング一覧
        cols = ("status", "name", "email", "filename")
        self._tree = ttk.Treeview(self, columns=cols, show="headings", height=14)
        self._tree.heading("status", text="状態")
        self._tree.heading("name", text="名前")
        self._tree.heading("email", text="メールアドレス")
        self._tree.heading("filename", text="PDFファイル名")
        self._tree.column("status", width=60, anchor="center")
        self._tree.column("name", width=140)
        self._tree.column("email", width=220)
        self._tree.column("filename", width=300)
        self._tree.tag_configure("ok", background="#d4edda")
        self._tree.tag_configure("ng", background="#f8d7da")
        self._tree.pack(fill="both", expand=True, padx=8, pady=4)

        # 送信ボタン
        self._send_btn = ttk.Button(self, text="全員に送信", command=self._send, state="disabled")
        self._send_btn.pack(pady=8)

    def _select_folder(self):
        folder = filedialog.askdirectory(title="PDFフォルダを選択")
        if folder:
            self._pdf_paths = list(Path(folder).glob("*.pdf"))
            self._update_tree()

    def _on_drop(self, event):
        raw = event.data
        # tkinterdnd2はスペース区切りで複数ファイルを返す（パスにスペースがある場合は{}で囲まれる）
        import re
        paths = re.findall(r'\{([^}]+)\}|(\S+)', raw)
        self._pdf_paths = [Path(p[0] or p[1]) for p in paths if (p[0] or p[1]).lower().endswith(".pdf")]
        self._update_tree()

    def _clear(self):
        self._pdf_paths = []
        self._tree.delete(*self._tree.get_children())
        self._send_btn.config(state="disabled")

    def _update_tree(self):
        self._tree.delete(*self._tree.get_children())
        employees = self._app.employee_mgr.employees
        if not employees:
            messagebox.showwarning("従業員未登録", "先に「従業員管理」タブで従業員を登録してください。")
            return

        coord = SendCoordinator(employees=employees, pdf_paths=self._pdf_paths)
        self._match_results = coord.match()
        self._coord = coord

        for mr in self._match_results:
            if mr.pdf_path:
                tag = "ok"
                status = "✓"
                filename = mr.pdf_path.name
            else:
                tag = "ng"
                status = "✗"
                filename = "（PDFなし）"
            self._tree.insert("", "end",
                               values=(status, mr.employee.name, mr.employee.email, filename),
                               tags=(tag,))

        self._send_btn.config(state="normal")

    def _send(self):
        cfg = self._app.config_data
        if not cfg.is_configured():
            messagebox.showerror("設定未完了", "「設定」タブでGmailアドレスとアプリパスワードを設定してください。")
            return

        skipped = [mr for mr in self._match_results if mr.pdf_path is None]
        if skipped:
            names = "\n".join(f"  ・{mr.employee.name}" for mr in skipped)
            ok = messagebox.askyesno(
                "確認",
                f"以下の{len(skipped)}名はPDFがありません。スキップして残りに送信しますか？\n\n{names}"
            )
            if not ok:
                return

        self._send_btn.config(state="disabled", text="送信中...")
        year = self._year_var.get()
        month = self._month_var.get()
        subject = render(cfg.subject_template, name="", year=year, month=month)

        def _run():
            report = self._coord.execute(
                match_results=self._match_results,
                gmail_address=cfg.gmail_address,
                gmail_app_password=cfg.gmail_app_password,
                subject=subject,
                body_template=cfg.body_template,
                year=year,
                month=month,
            )
            self.after(0, lambda: self._on_done(report, year, month))

        threading.Thread(target=_run, daemon=True).start()

    def _on_done(self, report, year, month):
        self._send_btn.config(state="normal", text="全員に送信")
        report_text = report.to_text(year=year, month=month)

        win = tk.Toplevel(self)
        win.title("送信完了レポート")
        win.geometry("560x400")
        text = tk.Text(win, wrap="word")
        text.insert("1.0", report_text)
        text.config(state="disabled")
        text.pack(fill="both", expand=True, padx=8, pady=8)

        def _save():
            path = filedialog.asksaveasfilename(
                defaultextension=".txt",
                filetypes=[("テキストファイル", "*.txt")],
                initialfile=f"送信レポート_{year}{month.zfill(2)}.txt"
            )
            if path:
                Path(path).write_text(report_text, encoding="utf-8")

        ttk.Button(win, text="レポートを保存", command=_save).pack(pady=4)
```

- [ ] **Step 2: 手動確認**

```bash
python main.py
```

確認項目:
- 「送信」タブでフォルダを選択するとPDFが読み込まれる
- 従業員リストと照合して緑/赤で一覧表示される
- PDFなし従業員がいる場合に確認ダイアログが出る
- 送信後にレポートウィンドウが表示される
- レポートを保存できる

- [ ] **Step 3: コミット**

```bash
git add gui_send_tab.py
git commit -m "feat: 送信タブGUIを実装"
```

---

## Task 11: EXEビルド

**Files:**
- Create: `payro/payro.spec`（PyInstaller設定）

- [ ] **Step 1: PyInstallerでビルドする**

```bash
cd payro
pyinstaller --onefile --windowed --name Payro main.py
```

- [ ] **Step 2: ビルド成果物を確認する**

```
dist/Payro.exe  ← このファイルが生成される
```

- [ ] **Step 3: EXEを手動実行して動作確認する**

`dist/Payro.exe` をダブルクリックして起動確認。
確認項目:
- アプリが正常に起動する
- `dist/data/` フォルダが自動生成される
- 設定・従業員登録・送信の一連の操作が正常に動作する

- [ ] **Step 4: コミット**

```bash
git add payro.spec
git commit -m "chore: PyInstallerビルド設定を追加"
```

---

## 全テスト実行確認

```bash
cd payro
python -m pytest tests/ -v
```

期待出力: `全テスト passed（GUIテストを除く）`
