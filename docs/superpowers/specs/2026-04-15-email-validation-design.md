# メールアドレスバリデーション 設計

**Goal:** 従業員ダイアログでメールアドレスの形式をチェックし、`gmailcom` のようなタイポを登録前に弾く

**Architecture:** `_EmployeeDialog._ok()` に正規表現チェックを追加するのみ。データ層 (`employee_manager.py`) は変更しない（入力はすべてこのダイアログ経由のため）

**Tech Stack:** Python `re` モジュール（標準ライブラリ）

---

## バリデーション仕様

**パターン:** `^[^@\s]+@[^@\s]+\.[^@\s]+$`

| 入力 | 結果 |
|------|------|
| `name@example.com` | OK |
| `name@gmail.com` | OK |
| `name@gmailcom` | NG（ドットなし） |
| `namegmail.com` | NG（`@` なし） |
| `name @gmail.com` | NG（スペースあり） |

**エラーメッセージ:** 「メールアドレスの形式が正しくありません。（例: name@example.com）」

## 変更ファイル

- **修正:** `payro/gui_employee_tab.py` — `_EmployeeDialog._ok()` に形式チェック追加（約5行）
