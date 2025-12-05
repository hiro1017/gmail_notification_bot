import os
import json
import base64
import time
from datetime import datetime
from email.mime.text import MIMEText
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import requests
from dotenv import load_dotenv

# 環境変数を読み込み
load_dotenv()

class GmailDiscordBot:
    def __init__(self):
        # Gmail API のスコープ
        self.SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']
        
        # 環境変数から設定を読み込み
        self.DISCORD_WEBHOOK_URL = os.getenv('DISCORD_WEBHOOK_URL')
        self.GMAIL_CREDENTIALS_PATH = os.getenv('GMAIL_CREDENTIALS_PATH', 'credentials.json')
        self.GMAIL_TOKEN_PATH = os.getenv('GMAIL_TOKEN_PATH', 'token.json')
        self.CHECK_INTERVAL = int(os.getenv('CHECK_INTERVAL', '300'))  # 5分間隔
        
        # 処理済みメールIDを記録するファイル
        self.PROCESSED_EMAILS_FILE = 'processed_emails.txt'
        
        # Gmail履歴IDを保存するファイル
        self.HISTORY_ID_FILE = 'last_history_id.txt'
        
        # Gmail API サービス
        self.service = None
        self.processed_emails = self.load_processed_emails()
        self.last_history_id = self.load_last_history_id()
    
    def load_processed_emails(self):
        """処理済みメールIDを読み込み"""
        if os.path.exists(self.PROCESSED_EMAILS_FILE):
            with open(self.PROCESSED_EMAILS_FILE, 'r') as f:
                return set(line.strip() for line in f)
        return set()
    
    def load_last_history_id(self):
        """最後に処理した履歴IDを読み込み"""
        if os.path.exists(self.HISTORY_ID_FILE):
            with open(self.HISTORY_ID_FILE, 'r') as f:
                return f.read().strip()
        return None
    
    def save_last_history_id(self, history_id):
        """最後に処理した履歴IDを保存"""
        with open(self.HISTORY_ID_FILE, 'w') as f:
            f.write(str(history_id))
        self.last_history_id = history_id
    
    def authenticate_gmail(self):
        """Gmail APIの認証"""
        creds = None
        
        # credentials.jsonの存在確認
        if not os.path.exists(self.GMAIL_CREDENTIALS_PATH):
            print(f"エラー: {self.GMAIL_CREDENTIALS_PATH} が見つかりません")
            return
        
        # token.jsonファイルがあれば認証情報を読み込み
        if os.path.exists(self.GMAIL_TOKEN_PATH):
            creds = Credentials.from_authorized_user_file(self.GMAIL_TOKEN_PATH, self.SCOPES)
        
        # 有効な認証情報がない場合は再認証
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                except Exception as e:
                    print(f"トークン更新エラー: {e}")
                    creds = None
            
            if not creds:
                try:
                    flow = InstalledAppFlow.from_client_secrets_file(
                        self.GMAIL_CREDENTIALS_PATH, self.SCOPES)
                    
                    # 手動認証用の設定
                    flow.redirect_uri = 'urn:ietf:wg:oauth:2.0:oob'
                    
                    # 認証URLを生成・表示
                    auth_url, _ = flow.authorization_url(prompt='consent')
                    print("=== Gmail認証が必要です ===")
                    print("1. 以下のURLをブラウザで開いてください：")
                    print(auth_url)
                    print("2. Googleアカウントでログインし、アプリを承認してください")
                    print("3. 表示された認証コードをコピーしてください")
                    
                    # ユーザーに認証コードの入力を求める
                    auth_code = input("認証コードを入力してください: ")
                    
                    # 認証コードを使用してトークンを取得
                    flow.fetch_token(code=auth_code)
                    creds = flow.credentials
                    
                except Exception as e:
                    print(f"認証エラー: {e}")
                    print("credentials.jsonの設定を確認してください")
                    return
            
            # 認証情報を保存
            with open(self.GMAIL_TOKEN_PATH, 'w') as token:
                token.write(creds.to_json())
        
        self.service = build('gmail', 'v1', credentials=creds)
        print("Gmail API認証が完了しました")
    
    def save_processed_email(self, email_id):
        """処理済みメールIDを保存"""
        self.processed_emails.add(email_id)
        with open(self.PROCESSED_EMAILS_FILE, 'a') as f:
            f.write(f"{email_id}\n")
    
    def get_new_unread_messages(self):
        """新しい未読メッセージのみを取得"""
        try:
            if not self.last_history_id:
                # 初回実行時：現在の未読メールを取得して通知
                print("初回実行：現在の未読メールをチェックします")
                return self.get_current_unread_emails()
            
            # 前回から現在までの履歴を取得
            history = self.service.users().history().list(
                userId='me',
                startHistoryId=self.last_history_id,
                historyTypes=['messageAdded']  # 新規メッセージの追加のみ
            ).execute()
            
            # 現在の履歴IDを更新
            profile = self.service.users().getProfile(userId='me').execute()
            current_history_id = profile['historyId']
            self.save_last_history_id(current_history_id)
            
            new_unread_messages = []
            changes = history.get('history', [])
            
            for change in changes:
                if 'messagesAdded' in change:
                    for message_added in change['messagesAdded']:
                        message = message_added['message']
                        # INBOXラベルとUNREADラベルがあるメッセージのみ（未読の受信メール）
                        labels = message.get('labelIds', [])
                        if 'INBOX' in labels and 'UNREAD' in labels:
                            new_unread_messages.append(message)
            
            return new_unread_messages
            
        except Exception as e:
            print(f"履歴取得エラー: {e}")
            # エラーの場合は従来の未読メール取得にフォールバック
            return self.get_current_unread_emails()
    
    def get_current_unread_emails(self):
        """現在の未読メールを取得"""
        try:
            query = 'is:unread in:inbox'  # 受信トレイの未読メールのみ
            results = self.service.users().messages().list(userId='me', q=query).execute()
            messages = results.get('messages', [])
            
            # 初回実行時は履歴IDも記録
            if not self.last_history_id:
                profile = self.service.users().getProfile(userId='me').execute()
                current_history_id = profile['historyId']
                self.save_last_history_id(current_history_id)
                print(f"履歴ID {current_history_id} を記録しました")
            
            return messages
        except Exception as e:
            print(f"未読メール取得エラー: {e}")
            return []
    
    def get_email_details(self, message_id):
        """メールの詳細情報を取得"""
        try:
            message = self.service.users().messages().get(userId='me', id=message_id).execute()
            
            # ヘッダー情報を取得
            headers = message['payload'].get('headers', [])
            subject = next((h['value'] for h in headers if h['name'] == 'Subject'), '件名なし')
            sender = next((h['value'] for h in headers if h['name'] == 'From'), '送信者不明')
            date = next((h['value'] for h in headers if h['name'] == 'Date'), '')
            
            # メール本文を取得
            body = self.extract_message_body(message['payload'])
            
            # 全ての添付ファイルを取得
            attachments = self.get_attachments(message_id, message['payload'])
            
            return {
                'id': message_id,
                'subject': subject,
                'sender': sender,
                'date': date,
                'body': body[:1000] + ('...' if len(body) > 1000 else ''),
                'attachments': attachments
            }
        except Exception as e:
            print(f"メール詳細取得エラー: {e}")
            return None
    
    def extract_message_body(self, payload):
        """メール本文を抽出"""
        body = ""
        
        if 'parts' in payload:
            for part in payload['parts']:
                mime_type = part.get('mimeType', '')
                
                # text/plainの本文を優先的に取得
                if mime_type == 'text/plain' and part.get('body', {}).get('data'):
                    data = part['body']['data']
                    body = base64.urlsafe_b64decode(data).decode('utf-8')
                    break
                
                # multipart配下を再帰的に探索
                elif mime_type.startswith('multipart/'):
                    body = self.extract_message_body(part)
                    if body:
                        break
                
                # text/htmlも取得対象に（text/plainがない場合のフォールバック）
                elif mime_type == 'text/html' and not body and part.get('body', {}).get('data'):
                    data = part['body']['data']
                    html_body = base64.urlsafe_b64decode(data).decode('utf-8')
                    # 簡易的なHTML除去（より高度な処理が必要な場合はBeautifulSoupなどを使用）
                    import re
                    body = re.sub('<[^<]+?>', '', html_body)
        else:
            # partsがない場合は直接本文を取得
            if payload.get('body', {}).get('data'):
                data = payload['body']['data']
                body = base64.urlsafe_b64decode(data).decode('utf-8')
        
        return body
    
    def get_attachments(self, message_id, payload, attachments=None):
        """全ての添付ファイルを取得"""
        if attachments is None:
            attachments = []
        
        if 'parts' in payload:
            for part in payload['parts']:
                # 添付ファイルかチェック
                mime_type = part.get('mimeType', '')
                filename = part.get('filename', '')
                
                # ファイル名があり、attachmentIdがある場合は添付ファイル
                if filename and part.get('body', {}).get('attachmentId'):
                    try:
                        attachment_id = part['body']['attachmentId']
                        attachment = self.service.users().messages().attachments().get(
                            userId='me',
                            messageId=message_id,
                            id=attachment_id
                        ).execute()
                        
                        # ファイルデータをbase64デコード
                        file_data = base64.urlsafe_b64decode(attachment['data'])
                        
                        attachments.append({
                            'data': file_data,
                            'mime_type': mime_type,
                            'filename': filename
                        })
                    except Exception as e:
                        print(f"添付ファイル取得エラー: {e}")
                
                # 再帰的に検索
                if 'parts' in part:
                    self.get_attachments(message_id, part, attachments)
        
        return attachments
    
    def send_to_discord(self, email_data):
        """DiscordにメールデータをWebhookで送信"""
        try:
            # メイン情報のembed
            main_embed = {
                "title": f"📧 新着メール: {email_data['subject']}",
                "color": 0x00ff00,
                "fields": [
                    {
                        "name": "送信者",
                        "value": email_data['sender'],
                        "inline": True
                    },
                    {
                        "name": "受信日時",
                        "value": email_data['date'],
                        "inline": True
                    },
                    {
                        "name": "本文プレビュー",
                        "value": email_data['body'] if email_data['body'] else "本文が空です",
                        "inline": False
                    }
                ],
                "timestamp": datetime.now().isoformat(),
                "footer": {
                    "text": "📨 新着メール通知"
                }
            }
            
            # 添付ファイル情報を本文の後に追加
            if email_data.get('attachments'):
                attachment_list = []
                for att in email_data['attachments']:
                    size_kb = len(att['data']) / 1024
                    attachment_list.append(f"📎 {att['filename']} ({size_kb:.1f} KB)")
                
                if attachment_list:
                    main_embed['fields'].append({
                        "name": "添付ファイル",
                        "value": "\n".join(attachment_list[:10]),  # 最大10件まで表示
                        "inline": False
                    })
            
            embeds = [main_embed]
            
            # 画像用のembedを追加(添付ファイルリストの後に表示される)
            image_attachments = [att for att in email_data.get('attachments', []) 
                            if att['mime_type'].startswith('image/')]
            
            for idx, img in enumerate(image_attachments[:10]):  # 最大10枚まで
                image_embed = {
                    "image": {"url": f"attachment://{img['filename']}"},
                    "color": 0x00ff00
                }
                embeds.append(image_embed)
            
            payload = {
                "embeds": embeds
            }
            
            # 添付ファイルがある場合
            if email_data.get('attachments'):
                files = {}
                for idx, att in enumerate(email_data['attachments'][:10]):  # Discordの制限: 最大10ファイル
                    files[f'file{idx}'] = (att['filename'], att['data'], att['mime_type'])
                
                # multipart/form-dataで送信
                response = requests.post(
                    self.DISCORD_WEBHOOK_URL,
                    data={'payload_json': json.dumps(payload)},
                    files=files
                )
            else:
                # 通常のJSON送信
                response = requests.post(self.DISCORD_WEBHOOK_URL, json=payload)
            
            if response.status_code == 204 or response.status_code == 200:
                print(f"Discordに送信成功: {email_data['subject']}")
                return True
            else:
                print(f"Discord送信エラー: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"Discord送信エラー: {e}")
            return False
    
    def mark_as_read(self, message_id):
        """メールを既読にマーク"""
        try:
            self.service.users().messages().modify(
                userId='me',
                id=message_id,
                body={'removeLabelIds': ['UNREAD']}
            ).execute()
            print(f"メールを既読にマーク: {message_id}")
        except Exception as e:
            print(f"既読マークエラー: {e}")
    
    def run_once(self):
        """一度だけメールチェックを実行"""
        print(f"新着メールチェック開始: {datetime.now()}")
        
        # 新しく受信したメールを取得
        new_messages = self.get_new_unread_messages()  # ← この行を修正
        
        if not new_messages:
            print("新着メールはありません")
            return
        
        print(f"{len(new_messages)}件の新着メールを発見")
        
        for message in new_messages:
            message_id = message['id']
            
            # 既に処理済みの場合はスキップ
            if message_id in self.processed_emails:
                print(f"スキップ（処理済み）: {message_id}")
                continue
            
            # メール詳細を取得
            email_data = self.get_email_details(message_id)
            
            if email_data:
                print(f"新着メール処理中: {email_data['subject']}")
                # Discordに送信
                if self.send_to_discord(email_data):
                    # 送信成功したら処理済みとしてマーク
                    self.save_processed_email(message_id)
                
                # API制限を避けるため少し待機
                time.sleep(1)
    
    def run_forever(self):
        """継続的にメールをチェック"""
        print(f"Gmail to Discord Bot を開始します（新着メール受信時通知モード）")
        print(f"チェック間隔: {self.CHECK_INTERVAL}秒")
        
        while True:
            try:
                self.run_once()
            except Exception as e:
                print(f"エラーが発生しました: {e}")
            
            print(f"次のチェックまで{self.CHECK_INTERVAL}秒待機...")
            time.sleep(self.CHECK_INTERVAL)

def main():
    # 環境変数の確認
    required_env_vars = ['DISCORD_WEBHOOK_URL']
    missing_vars = [var for var in required_env_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"以下の環境変数が設定されていません: {', '.join(missing_vars)}")
        return
    
    # Botインスタンスを作成
    bot = GmailDiscordBot()
    
    # Gmail認証
    bot.authenticate_gmail()
    
    # メールチェックを開始
    try:
        bot.run_forever()
    except KeyboardInterrupt:
        print("\nBotを停止します")

if __name__ == "__main__":
    main()
