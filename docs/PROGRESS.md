# 進捗メモ

**最終更新:** 2026-04-15

## 完了済み
- Task 1: config.py — 設定管理
- Task 2: employee_manager.py — 従業員データ管理
- Task 3: template_engine.py — テンプレートエンジン
- Task 4: （前セッション完了済み）
- Task 5: mail_sender.py — Gmail SMTP送信（MailSender, SendResult 実装、テスト3件通過）
- Task 6: send_coordinator.py — 送信コーディネーター（SendCoordinator, MatchResult, SendReport 実装、テスト3件通過）

## 進行中 / 次にやること
- Task 7 以降（未着手）

## 決定事項・メモ
- Gmail SMTP送信は SMTP_SSL (port 465) を使用
- 送信結果は SendResult Enum で表現（SUCCESS / AUTH_ERROR / NETWORK_ERROR）
- テストはモックを使用し実際のGmail接続は行わない
