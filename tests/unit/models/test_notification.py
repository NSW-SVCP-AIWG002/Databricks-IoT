"""
メール通知 - Model層 単体テスト

対象ファイル: src/iot_app/models/notification.py

参照ドキュメント:
  - 機能設計書: docs/03-features/flask-app/mail-history/README.md
  - 実装ガイド: docs/05-testing/unit-test/unit-test-guide.md
"""

import pytest
from datetime import datetime
from unittest.mock import MagicMock, patch


MODULE = 'iot_app.models.notification'


# ============================================================
# MailTypeMaster
# ============================================================

@pytest.mark.unit
class TestMailTypeMaster:
    """MailTypeMaster モデルのフィールド定義を検証するテスト群"""

    def test_tablename(self):
        """テーブル名が mail_type_master であること"""
        from iot_app.models.notification import MailTypeMaster
        assert MailTypeMaster.__tablename__ == 'mail_type_master'

    def test_has_required_columns(self):
        """必須カラムが定義されていること"""
        from iot_app.models.notification import MailTypeMaster
        mapper = MailTypeMaster.__mapper__
        column_names = {c.key for c in mapper.columns}
        assert 'mail_type_id' in column_names
        assert 'mail_type_name' in column_names
        assert 'delete_flag' in column_names
        assert 'create_date' in column_names
        assert 'update_date' in column_names

    def test_primary_key_is_mail_type_id(self):
        """主キーが mail_type_id であること"""
        from iot_app.models.notification import MailTypeMaster
        pk_columns = [c.key for c in MailTypeMaster.__mapper__.columns if c.primary_key]
        assert pk_columns == ['mail_type_id']


# ============================================================
# MailHistory
# ============================================================

@pytest.mark.unit
class TestMailHistory:
    """MailHistory モデルのフィールド定義を検証するテスト群"""

    def test_tablename(self):
        """テーブル名が mail_history であること"""
        from iot_app.models.notification import MailHistory
        assert MailHistory.__tablename__ == 'mail_history'

    def test_has_required_columns(self):
        """必須カラムが定義されていること"""
        from iot_app.models.notification import MailHistory
        mapper = MailHistory.__mapper__
        column_names = {c.key for c in mapper.columns}
        required = {
            'mail_history_id',
            'mail_history_uuid',
            'mail_type',
            'sender_email',
            'subject',
            'body',
            'sent_at',
            'organization_id',
            'create_date',
            'creator',
            'update_date',
            'modifier',
        }
        assert required <= column_names

    def test_does_not_have_removed_columns(self):
        """旧設計カラム (recipients, user_id) が存在しないこと"""
        from iot_app.models.notification import MailHistory
        column_names = {c.key for c in MailHistory.__mapper__.columns}
        assert 'recipients' not in column_names
        assert 'user_id' not in column_names

    def test_primary_key_is_mail_history_id(self):
        """主キーが mail_history_id であること"""
        from iot_app.models.notification import MailHistory
        pk_columns = [c.key for c in MailHistory.__mapper__.columns if c.primary_key]
        assert pk_columns == ['mail_history_id']

    def test_mail_history_uuid_is_unique(self):
        """mail_history_uuid に UNIQUE 制約が設定されていること"""
        from iot_app.models.notification import MailHistory
        col = MailHistory.__mapper__.columns['mail_history_uuid']
        assert col.unique is True

    def test_mail_type_has_fk_to_mail_type_master(self):
        """mail_type に mail_type_master への外部キーが設定されていること"""
        from iot_app.models.notification import MailHistory
        col = MailHistory.__mapper__.columns['mail_type']
        fk_targets = {fk.target_fullname for fk in col.foreign_keys}
        assert 'mail_type_master.mail_type_id' in fk_targets


# ============================================================
# MailRecipient
# ============================================================

@pytest.mark.unit
class TestMailRecipient:
    """MailRecipient モデルのフィールド定義を検証するテスト群"""

    def test_tablename(self):
        """テーブル名が mail_recipient であること"""
        from iot_app.models.notification import MailRecipient
        assert MailRecipient.__tablename__ == 'mail_recipient'

    def test_has_required_columns(self):
        """必須カラムが定義されていること"""
        from iot_app.models.notification import MailRecipient
        mapper = MailRecipient.__mapper__
        column_names = {c.key for c in mapper.columns}
        required = {
            'mail_history_id',
            'user_id',
            'recipient_email',
            'create_date',
            'creator',
        }
        assert required <= column_names

    def test_composite_primary_key(self):
        """複合主キーが (mail_history_id, user_id) であること"""
        from iot_app.models.notification import MailRecipient
        pk_columns = {c.key for c in MailRecipient.__mapper__.columns if c.primary_key}
        assert pk_columns == {'mail_history_id', 'user_id'}

    def test_mail_history_id_has_fk_to_mail_history(self):
        """mail_history_id に mail_history への外部キーが設定されていること"""
        from iot_app.models.notification import MailRecipient
        col = MailRecipient.__mapper__.columns['mail_history_id']
        fk_targets = {fk.target_fullname for fk in col.foreign_keys}
        assert 'mail_history.mail_history_id' in fk_targets
