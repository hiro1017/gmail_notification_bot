# gmail_notification_bot

# Gmail to Discord Bot (複数アカウント対応版)

複数のGmailアカウントの新着メールをDiscordに自動通知するBotです。各アカウントを色分けし、指定したロールにメンションすることができます。

## 📋 機能

- ✅ **複数Gmailアカウント対応** (最大4アカウント)
- ✅ **新着メールのみ通知** (Gmail History APIを使用)
- ✅ **アカウント別の色分け表示**
- ✅ **Discordロールメンション機能**
- ✅ **添付ファイルの自動転送** (画像、PDF等)
- ✅ **メール本文プレビュー表示**
- ✅ **重複通知防止機能**

---

## 🚀 セットアップ手順

### 1. 必要なパッケージのインストール

```bash
pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client requests python-dotenv
```

### 2. Google Cloud Consoleでの設定

#### 2-1. プロジェクトの作成
1. [Google Cloud Console](https://console.cloud.google.com/) にアクセス
2. 新しいプロジェクトを作成 (例: "Gmail Discord Bot")

#### 2-2. Gmail APIの有効化
1. 「APIとサービス」→「ライブラリ」を開く
2. "Gmail API" を検索して有効化

#### 2-3. OAuth 2.0 認証情報の作成
1. 「APIとサービス」→「認証情報」を開く
2. 「認証情報を作成」→「OAuthクライアントID」を選択
3. アプリケーションの種類: **デスクトップアプリ**
4. 名前を入力 (例: "Gmail Bot Client")
5. 「作成」をクリック
6. **JSONをダウンロード**

#### 2-4. 認証情報ファイルの配置
ダウンロードしたJSONファイルを以下のように配置:

```
プロジェクトフォルダ/
├── bot.py
├── .env
├── credentials_account1.json  ← アカウント1用
├── credentials_account2.json  ← アカウント2用
├── credentials_account3.json  ← アカウント3用 (オプション)
└── credentials_account4.json  ← アカウント4用 (オプション)
```

### 3. Discord Webhookの設定

#### 3-1. Webhookの作成
1. Discordサーバーで通知を受け取りたいチャンネルを開く
2. チャンネル設定 → 連携サービス → ウェブフック
3. 「新しいウェブフック」をクリック
4. Webhook URLをコピー

#### 3-2. ロールIDの取得 (メンション機能を使う場合)
1. Discordの「ユーザー設定」→「詳細設定」→「開発者モード」をON
2. サーバー設定 → ロール → メンションしたいロールを右クリック
3. 「IDをコピー」を選択

### 4. .envファイルの作成

プロジェクトフォルダに `.env` ファイルを作成:

```bash
# Discord Webhook URL (必須)
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/YOUR_WEBHOOK_URL

# メールチェック間隔(秒) デフォルト: 300秒 = 5分
CHECK_INTERVAL=300

# ========== アカウント1の設定 ==========
GMAIL_CREDENTIALS_PATH_1=credentials_account1.json
GMAIL_TOKEN_PATH_1=token_account1.json
ACCOUNT_NAME_1=メインアカウント
DISCORD_ROLE_ID_1=1234567890123456789

# ========== アカウント2の設定 ==========
GMAIL_CREDENTIALS_PATH_2=credentials_account2.json
GMAIL_TOKEN_PATH_2=token_account2.json
ACCOUNT_NAME_2=仕事用アカウント
DISCORD_ROLE_ID_2=9876543210987654321

# ========== アカウント3の設定 (オプション) ==========
# GMAIL_CREDENTIALS_PATH_3=credentials_account3.json
# GMAIL_TOKEN_PATH_3=token_account3.json
# ACCOUNT_NAME_3=サブアカウント
# DISCORD_ROLE_ID_3=1111111111111111111

# ========== アカウント4の設定 (オプション) ==========
# GMAIL_CREDENTIALS_PATH_4=credentials_account4.json
# GMAIL_TOKEN_PATH_4=token_account4.json
# ACCOUNT_NAME_4=プライベート
# DISCORD_ROLE_ID_4=2222222222222222222
```

### 5. 初回認証

各アカウントごとに初回認証が必要です:

```bash
python bot.py
```

実行すると、各アカウントごとに以下のように表示されます:

```
=== [メインアカウント] Gmail認証が必要です ===
1. 以下のURLをブラウザで開いてください:
https://accounts.google.com/o/oauth2/auth?...
2. Googleアカウントでログインし、アプリを承認してください
3. 表示された認証コードをコピーしてください
[メインアカウント] 認証コードを入力してください: 
```

**手順:**
1. 表示されたURLをブラウザで開く
2. 該当するGmailアカウントでログイン
3. 「このアプリは確認されていません」と表示される場合:
   - 「詳細」→「(安全ではないページ)に移動」をクリック
4. アクセス許可を承認
5. 表示された認証コードをコピー
6. ターミナルに貼り付けてEnter

認証が成功すると `token_account1.json` が自動生成されます。

---

## 🖥️ Ubuntuサーバーでの実行方法

### screenコマンドで常時実行

```bash
# 新しいscreenセッションを作成
screen -S gmail_bot

# Botを起動
python bot.py

# デタッチ (Ctrl+A → D)
# セッションはバックグラウンドで継続実行されます
```

### screenセッションの操作

```bash
# セッション一覧を表示
screen -ls

# セッションに再接続
screen -r gmail_bot

# セッションを終了 (セッション内で)
exit
# または Ctrl+D
```

### サーバー再起動時の自動起動設定

`/etc/systemd/system/gmail-bot.service` を作成:

```ini
[Unit]
Description=Gmail to Discord Bot
After=network.target

[Service]
Type=simple
User=YOUR_USERNAME
WorkingDirectory=/path/to/bot
ExecStart=/usr/bin/python3 /path/to/bot/bot.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

有効化と起動:

```bash
sudo systemctl daemon-reload
sudo systemctl enable gmail-bot.service
sudo systemctl start gmail-bot.service

# 状態確認
sudo systemctl status gmail-bot.service

# ログ確認
sudo journalctl -u gmail-bot.service -f
```

---

## 📊 ファイル構成

```
プロジェクトフォルダ/
├── bot.py                          # メインプログラム
├── .env                            # 環境変数設定
├── credentials_account1.json       # アカウント1のGmail認証情報
├── credentials_account2.json       # アカウント2のGmail認証情報
├── token_account1.json            # アカウント1のトークン (自動生成)
├── token_account2.json            # アカウント2のトークン (自動生成)
├── processed_emails_account1.txt  # アカウント1の処理済みメールID (自動生成)
├── processed_emails_account2.txt  # アカウント2の処理済みメールID (自動生成)
├── last_history_id_account1.txt   # アカウント1の履歴ID (自動生成)
└── last_history_id_account2.txt   # アカウント2の履歴ID (自動生成)
```

---

## 🎨 アカウント別の色分け

各アカウントは以下の色で表示されます:

| アカウント | 色 | 16進数カラーコード |
|-----------|---|------------------|
| account1 | 🟢 緑 | #00ff00 |
| account2 | 🔵 青 | #0099ff |
| account3 | 🟠 オレンジ | #ff9900 |
| account4 | 🟣 ピンク | #ff0099 |

---

## 🔧 カスタマイズ

### チェック間隔の変更

`.env` ファイルで変更:

```bash
CHECK_INTERVAL=180  # 3分ごと
CHECK_INTERVAL=600  # 10分ごと
```

### メンション機能のON/OFF

メンションが不要な場合は、`.env` から `DISCORD_ROLE_ID_X` の行を削除またはコメントアウト:

```bash
# DISCORD_ROLE_ID_1=1234567890123456789  # コメントアウトでメンション無効
```

### アカウントの色を変更

`bot.py` の `get_account_color` メソッドを編集:

```python
def get_account_color(self):
    colors = {
        'account1': 0xff0000,  # 赤に変更
        'account2': 0x00ff00,  # 緑に変更
        'account3': 0x0000ff,  # 青に変更
        'account4': 0xffff00,  # 黄色に変更
    }
    return colors.get(self.account_id, 0x808080)
```

---

## 📝 通知メッセージの例

Discordには以下のような形式で通知されます:

```
@管理者ロール

📧 新着メール [メインアカウント]
件名: 重要なお知らせ

送信者: example@gmail.com
受信日時: Mon, 6 Dec 2024 10:30:00 +0900

本文プレビュー:
お世話になっております。
本日の会議についてのご連絡です...

添付ファイル:
📎 資料.pdf (245.3 KB)
📎 画像.png (128.7 KB)

📨 メインアカウント
```

---

## ⚠️ トラブルシューティング

### 1. 認証エラーが発生する

**症状:** `認証エラー: invalid_grant`

**解決方法:**
1. `token_accountX.json` を削除
2. Botを再起動して再認証

### 2. メールが通知されない

**確認項目:**
- `.env` の `DISCORD_WEBHOOK_URL` が正しいか
- `credentials_accountX.json` が正しい場所にあるか
- Gmailの受信トレイに未読メールがあるか
- ログに `[アカウント名] 新着メールチェック開始` が表示されているか

### 3. "このアプリは確認されていません" と表示される

**解決方法:**
1. 「詳細」をクリック
2. 「(安全ではないページ)に移動」をクリック
3. これは自分で作成したアプリなので問題ありません

### 4. 添付ファイルが送信されない

**原因:** Discordの制限 (1ファイル25MB、合計10ファイルまで)

**対処法:**
- 大きなファイルは自動的にスキップされます
- ファイル名と容量は表示されます

### 5. 重複して通知される

**確認項目:**
- `processed_emails_accountX.txt` が正常に書き込まれているか
- ファイルの権限を確認: `chmod 644 processed_emails_*.txt`

---

## 🔐 セキュリティ注意事項

1. **credentials.jsonとtoken.jsonは絶対に公開しない**
   - `.gitignore` に追加推奨
   
2. **Discord Webhook URLは秘密情報**
   - URLが漏れると誰でも通知を送信できます
   
3. **サーバーのアクセス権限を適切に設定**
   ```bash
   chmod 600 .env
   chmod 600 credentials_*.json
   chmod 600 token_*.json
   ```

---

## 📚 参考リンク

- [Gmail API Documentation](https://developers.google.com/gmail/api)
- [Discord Webhooks Guide](https://discord.com/developers/docs/resources/webhook)
- [Google Cloud Console](https://console.cloud.google.com/)

---

## 📄 ライセンス

このプロジェクトはMITライセンスの下で公開されています。

---

## 🤝 サポート

問題が発生した場合は、以下を確認してください:

1. ログ出力の最後のエラーメッセージ
2. `.env` ファイルの設定
3. 各 `credentials_accountX.json` の存在確認

---

**作成日:** 2025年12月6日  
**バージョン:** 2.0 (複数アカウント対応版)
