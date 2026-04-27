"""
tests/unit/batch/scheduled-email-job/conftest.py

メール通知送信バッチジョブの単体テスト用設定。

NOTE: テスト対象モジュール (email_notification_sender.py) の末尾には
      テスト収集時の自動実行を防ぐため以下のガード節が必要です:

          if __name__ == '__main__':
              process_email_queue()
"""
import os

# SendGrid API 設定（email_notification_sender モジュールインポート時に参照される）
os.environ.setdefault("SENDGRID_API_KEY", "test-sendgrid-api-key")

# MySQL 接続設定（process_email_queue 内で参照される）
os.environ.setdefault("MYSQL_HOST", "localhost")
os.environ.setdefault("MYSQL_PORT", "3306")
os.environ.setdefault("MYSQL_USER", "test_user")
os.environ.setdefault("MYSQL_PASSWORD", "test_password")
os.environ.setdefault("MYSQL_DATABASE", "test_db")
