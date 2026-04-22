import tkinter as tk
from tkinter import ttk


class UsageTab(ttk.Frame):
    def __init__(self, parent, *, app):
        super().__init__(parent)
        self._build()

    def _build(self):
        outer = ttk.Frame(self)
        outer.pack(fill="both", expand=True, padx=16, pady=16)

        ttk.Label(outer, text="使い方", font=("", 13, "bold")).pack(anchor="w", pady=(0, 12))

        text = tk.Text(outer, wrap="word", state="normal", relief="flat",
                       background=self.winfo_toplevel().cget("background"),
                       font=("", 10), cursor="arrow")
        text.pack(fill="both", expand=True)

        content = """\
【基本的な流れ】

1. ユーザー設定タブ
   Gmailアドレスと「アプリパスワード」を入力して「保存」してください。
   アプリパスワードは通常のGmailパスワードとは別物です。以下の手順で発行します。

   ▼ アプリパスワードの発行手順

   ① 2段階認証を有効にする（必須）
      Googleアカウントの設定（myaccount.google.com）→「セキュリティ」
      →「2段階認証プロセス」をオンにする
      ※ここが済んでいないとアプリパスワードの項目が表示されません

   ② アプリパスワードを発行する
      「セキュリティ」→「2段階認証プロセス」→ページ下部「アプリパスワード」
      アプリ名に「IkkiniOkuru」などと入力して「作成」を押す
      → 16桁の英字が表示される（例: abcd efgh ijkl mnop）

   ③ パスワードをコピーして設定画面に貼り付ける
      スペースは自動的に除去されるため、そのままペーストしてください

   ⚠️ よくある躓きポイント
   ・「セキュリティ」に「アプリパスワード」が見当たらない
     → 2段階認証が有効になっていない可能性があります
   ・通常のGmailパスワードを入力してしまっている
     → アプリパスワード（16桁）を使う必要があります
   ・Googleアカウントの管理者によりアプリパスワードが無効化されている
     → 職場・学校アカウントの場合、管理者に確認が必要です

2. グループ管理タブ
   送信先グループを作成し、宛先（氏名・メールアドレス）を登録します。
   CSVインポートを使うと一括で宛先を追加できます。

3. テンプレート管理タブ
   メール件名と本文を登録します。
   使用できる変数: {name}（氏名）、{year}（年）、{month}（月）

4. 送信タブ
   ① グループを選択する
   ② 年月を入力する
   ③ PDFファイルをドラッグ&ドロップまたはフォルダ選択で追加する
   ④ 宛先とPDFが正しくマッチしていることを確認する
   ⑤ 「送信」ボタンを押して確認ダイアログでOKを押す


【CSVインポートの手順】

1. グループ管理タブで対象グループを選択する
2. 「CSVテンプレート出力」でヘッダー行のみのCSVをダウンロードする
3. ExcelやスプレッドシートでCSVに宛先を記入する
   　列: name（氏名）、email（メールアドレス）
4. 「CSVインポート」で記入済みCSVを読み込む


【PDFのマッチングについて】

宛先の名前がPDFファイル名に含まれていると自動的にマッチします。
例: 名前「山田太郎」→「山田太郎_202504.pdf」にマッチ


【送信ボタンが押せない場合】

非除外の宛先全員にPDFが1対1でマッチしている場合のみ送信できます。
一覧で「PDFなし」になっている宛先がないか確認してください。
"""
        text.insert("1.0", content)
        text.config(state="disabled")
