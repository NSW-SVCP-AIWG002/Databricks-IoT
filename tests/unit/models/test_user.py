import pytest

MODULE = 'iot_app.models.user'


@pytest.mark.unit
class TestUserModel:
    """User モデルのテスト"""

    def test_tablename(self, app):
        """観点1: __tablename__ が 'user_master'"""
        with app.app_context():
            from iot_app.models.user import User
            assert User.__tablename__ == 'user_master'

    def test_default_language_code(self, app):
        """観点2: language_code のデフォルト値は 'ja'"""
        with app.app_context():
            from iot_app.models.user import User
            col = User.__table__.c.language_code
            assert col.default.arg == 'ja'

    def test_default_status(self, app):
        """観点3: status のデフォルト値は 1（有効）"""
        with app.app_context():
            from iot_app.models.user import User
            col = User.__table__.c.status
            assert col.default.arg == 1

    def test_default_alert_notification_flag(self, app):
        """観点4: alert_notification_flag のデフォルト値は True"""
        with app.app_context():
            from iot_app.models.user import User
            col = User.__table__.c.alert_notification_flag
            assert col.default.arg is True

    def test_default_system_notification_flag(self, app):
        """観点5: system_notification_flag のデフォルト値は True"""
        with app.app_context():
            from iot_app.models.user import User
            col = User.__table__.c.system_notification_flag
            assert col.default.arg is True

    def test_default_delete_flag(self, app):
        """観点6: delete_flag のデフォルト値は False（論理削除なし）"""
        with app.app_context():
            from iot_app.models.user import User
            col = User.__table__.c.delete_flag
            assert col.default.arg is False

    def test_primary_key_is_user_id(self, app):
        """観点7: user_id が主キー"""
        with app.app_context():
            from iot_app.models.user import User
            col = User.__table__.c.user_id
            assert col.primary_key is True

    def test_email_address_not_nullable(self, app):
        """観点8: email_address は NOT NULL"""
        with app.app_context():
            from iot_app.models.user import User
            col = User.__table__.c.email_address
            assert col.nullable is False

    def test_databricks_user_id_not_nullable(self, app):
        """観点9: databricks_user_id は NOT NULL"""
        with app.app_context():
            from iot_app.models.user import User
            col = User.__table__.c.databricks_user_id
            assert col.nullable is False


@pytest.mark.unit
class TestUserTypeModel:
    """UserType モデルのテスト"""

    def test_tablename(self, app):
        """観点1: __tablename__ が 'user_type_master'"""
        with app.app_context():
            from iot_app.models.user import UserType
            assert UserType.__tablename__ == 'user_type_master'

    def test_primary_key_is_user_type_id(self, app):
        """観点2: user_type_id が主キー"""
        with app.app_context():
            from iot_app.models.user import UserType
            col = UserType.__table__.c.user_type_id
            assert col.primary_key is True
