# メールアドレスバリデーション 実装計画

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 従業員ダイアログのOKボタン押下時にメールアドレスの形式をチェックし、`xxx@yyy.zzz` 形式でなければ警告を出して登録をブロックする

**Architecture:** `gui_employee_tab.py` にモジュールレベル関数 `is_valid_email()` を追加し、`_EmployeeDialog._ok()` から呼び出す。テストは `is_valid_email()` 単体をテストする。

**Tech Stack:** Python `re` モジュール（標準ライブラリ）、pytest

---

### Task 1: メールアドレスバリデーション

**Files:**
- Modify: `payro/gui_employee_tab.py`
- Test: `payro/tests/test_gui_employee_tab.py`（新規作成）

- [ ] **Step 1: テストファイルを作成して失敗させる**

`payro/tests/test_gui_employee_tab.py` を新規作成:

```python
from gui_employee_tab import is_valid_email


def test_valid_email():
    assert is_valid_email("name@example.com") is True

def test_valid_email_subdomain():
    assert is_valid_email("name@mail.example.co.jp") is True

def test_invalid_no_dot_in_domain():
    assert is_valid_email("name@gmailcom") is False

def test_invalid_no_at():
    assert is_valid_email("namegmail.com") is False

def test_invalid_space():
    assert is_valid_email("name @gmail.com") is False

def test_invalid_empty():
    assert is_valid_email("") is False
```

- [ ] **Step 2: テストを実行して失敗を確認**

```
cd payro
pytest tests/test_gui_employee_tab.py -v
```

Expected: `ImportError: cannot import name 'is_valid_email' from 'gui_employee_tab'`

- [ ] **Step 3: `is_valid_email()` を `gui_employee_tab.py` に追加する**

`gui_employee_tab.py` の先頭 `import tkinter as tk` の直前に追加:

```python
import re

def is_valid_email(email: str) -> bool:
    return bool(re.match(r'^[^@\s]+@[^@\s]+\.[^@\s]+$', email))
```

- [ ] **Step 4: テストを実行してパスを確認**

```
pytest tests/test_gui_employee_tab.py -v
```

Expected: 6 passed

- [ ] **Step 5: `_EmployeeDialog._ok()` でバリデーションを呼び出す**

`gui_employee_tab.py` の `_ok()` メソッドを以下に書き換える:

```python
def _ok(self):
    values = {k: v.get().strip() for k, v in self._vars.items()}
    if not values["name"] or not values["email"]:
        from tkinter import messagebox
        messagebox.showwarning("入力エラー", "名前とメールアドレスは必須です。")
        return
    if not is_valid_email(values["email"]):
        from tkinter import messagebox
        messagebox.showwarning("入力エラー", "メールアドレスの形式が正しくありません。\n（例: name@example.com）")
        return
    self.result = values
    self.destroy()
```

- [ ] **Step 6: 全テストを実行して既存テストが壊れていないことを確認**

```
pytest tests/ -v
```

Expected: 全テストが passed（既存21件 + 新規6件 = 27件）

- [ ] **Step 7: コミット**

```bash
git add payro/gui_employee_tab.py payro/tests/test_gui_employee_tab.py
git commit -m "feat: メールアドレス形式バリデーションを追加"
```
