import pytest

MODULE = 'iot_app.models.user'


@pytest.mark.unit
class TestUserModel:
    """User モデルのテスト
    観点: 2.1 正常系処理（カラム定義・制約・デフォルト値が設計書通りであること）
    """

    def test_tablename(self, app):
        """2.1.1: __tablename__ が 'user_master'"""
        with app.app_context():
            from iot_app.models.user import User
            assert User.__tablename__ == 'user_master'

    def test_primary_key_is_user_id(self, app):
        """2.1.1: user_id が主キー"""
        with app.app_context():
            from iot_app.models.user import User
            col = User.__table__.c.user_id
            assert col.primary_key is True

    def test_user_id_is_autoincrement(self, app):
        """2.1.1: user_id が autoincrement"""
        with app.app_context():
            from iot_app.models.user import User
            col = User.__table__.c.user_id
            assert col.autoincrement is True

    def test_user_name_not_nullable(self, app):
        """2.1.1: user_name は NOT NULL"""
        with app.app_context():
            from iot_app.models.user import User
            col = User.__table__.c.user_name
            assert col.nullable is False

    def test_email_address_not_nullable(self, app):
        """2.1.1: email_address は NOT NULL"""
        with app.app_context():
            from iot_app.models.user import User
            col = User.__table__.c.email_address
            assert col.nullable is False

    def test_databricks_user_id_not_nullable(self, app):
        """2.1.1: databricks_user_id は NOT NULL"""
        with app.app_context():
            from iot_app.models.user import User
            col = User.__table__.c.databricks_user_id
            assert col.nullable is False

    def test_default_language_code(self, app):
        """2.1.1: language_code のデフォルト値は 'ja'"""
        with app.app_context():
            from iot_app.models.user import User
            col = User.__table__.c.language_code
            assert col.default.arg == 'ja'

    def test_default_status(self, app):
        """2.1.1: status のデフォルト値は 1（有効）"""
        with app.app_context():
            from iot_app.models.user import User
            col = User.__table__.c.status
            assert col.default.arg == 1

    def test_default_alert_notification_flag(self, app):
        """2.1.1: alert_notification_flag のデフォルト値は True"""
        with app.app_context():
            from iot_app.models.user import User
            col = User.__table__.c.alert_notification_flag
            assert col.default.arg is True

    def test_default_system_notification_flag(self, app):
        """2.1.1: system_notification_flag のデフォルト値は True"""
        with app.app_context():
            from iot_app.models.user import User
            col = User.__table__.c.system_notification_flag
            assert col.default.arg is True

    def test_default_delete_flag(self, app):
        """2.1.1: delete_flag のデフォルト値は False（論理削除なし）"""
        with app.app_context():
            from iot_app.models.user import User
            col = User.__table__.c.delete_flag
            assert col.default.arg is False


@pytest.mark.unit
class TestUserTypeModel:
    """UserType モデルのテスト
    観点: 2.1 正常系処理（カラム定義・制約・デフォルト値が設計書通りであること）
    """

    def test_tablename(self, app):
        """2.1.1: __tablename__ が 'user_type_master'"""
        with app.app_context():
            from iot_app.models.user import UserType
            assert UserType.__tablename__ == 'user_type_master'

    def test_primary_key_is_user_type_id(self, app):
        """2.1.1: user_type_id が主キー"""
        with app.app_context():
            from iot_app.models.user import UserType
            col = UserType.__table__.c.user_type_id
            assert col.primary_key is True

    def test_user_type_name_not_nullable(self, app):
        """2.1.1: user_type_name は NOT NULL"""
        with app.app_context():
            from iot_app.models.user import UserType
            col = UserType.__table__.c.user_type_name
            assert col.nullable is False

    def test_default_delete_flag(self, app):
        """2.1.1: delete_flag のデフォルト値は False（論理削除なし）"""
        with app.app_context():
            from iot_app.models.user import UserType
            col = UserType.__table__.c.delete_flag
            assert col.default.arg is False
