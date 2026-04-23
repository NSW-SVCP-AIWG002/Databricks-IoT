"""
アラート設定管理 - Model層 単体テスト

対象ファイル: src/iot_app/models/alert.py

参照ドキュメント:
  - UI設計書:         docs/03-features/flask-app/alert-settings/ui-specification.md
  - 機能設計書:       docs/03-features/flask-app/alert-settings/workflow-specification.md
  - 単体テスト観点表: docs/05-testing/unit-test/unit-test-perspectives.md
  - 実装ガイド:       docs/05-testing/unit-test/unit-test-guide.md
"""
# 観点: unit-test-perspectives.md > 1.1.2 最大文字列長チェック
import pytest
from unittest.mock import MagicMock, patch


# ============================================================
# 1. AlertSettingMaster モデル定義テスト
# 観点: モデルのプロパティ・カラム定義（DB非依存）
# ============================================================

@pytest.mark.unit
class TestAlertSettingMaster:
    """AlertSettingMaster モデルのカラム定義テスト
    観点: モデルのプロパティ・制約定義（DB非依存）、1.1.2 最大文字列長チェック

    出典: src/iot_app/models/alert.py, workflow-specification.md > 入力検証
    """

    def test_tablename_is_alert_setting_master(self):
        """モデルのテーブル名が 'alert_setting_master' である"""
        # Arrange & Act
        from iot_app.models.alert import AlertSettingMaster
        # Assert
        assert AlertSettingMaster.__tablename__ == "alert_setting_master"

    def test_alert_id_is_primary_key(self):
        """alert_id が主キー (PK) として定義されている"""
        # Arrange
        from iot_app.models.alert import AlertSettingMaster
        col = AlertSettingMaster.__table__.columns["alert_id"]
        # Assert
        assert col.primary_key is True

    def test_alert_id_is_autoincrement(self):
        """alert_id が AUTO_INCREMENT（autoincrement）として定義されている"""
        # Arrange
        from iot_app.models.alert import AlertSettingMaster
        col = AlertSettingMaster.__table__.columns["alert_id"]
        # Assert
        assert col.autoincrement is True or col.autoincrement == "auto"

    def test_alert_uuid_column_exists(self):
        """alert_uuid カラムが存在する"""
        # Arrange
        from iot_app.models.alert import AlertSettingMaster
        # Assert
        assert hasattr(AlertSettingMaster, "alert_uuid")

    def test_alert_uuid_is_not_nullable(self):
        """alert_uuid は NOT NULL 制約を持つ"""
        # Arrange
        from iot_app.models.alert import AlertSettingMaster
        col = AlertSettingMaster.__table__.columns["alert_uuid"]
        # Assert
        assert col.nullable is False

    def test_alert_name_max_length_is_100(self):
        """1.1.2: alert_name の最大文字列長が 100 である（UI仕様書 (4.2) と一致）"""
        # Arrange
        from iot_app.models.alert import AlertSettingMaster
        col = AlertSettingMaster.__table__.columns["alert_name"]
        # Assert
        assert col.type.length == 100

    def test_alert_name_is_not_nullable(self):
        """alert_name は NOT NULL 制約を持つ"""
        # Arrange
        from iot_app.models.alert import AlertSettingMaster
        col = AlertSettingMaster.__table__.columns["alert_name"]
        # Assert
        assert col.nullable is False

    def test_device_id_is_not_nullable(self):
        """device_id は NOT NULL 制約を持つ"""
        # Arrange
        from iot_app.models.alert import AlertSettingMaster
        col = AlertSettingMaster.__table__.columns["device_id"]
        # Assert
        assert col.nullable is False

    def test_device_id_has_foreign_key(self):
        """device_id は device_master.device_id への外部キーを持つ"""
        # Arrange
        from iot_app.models.alert import AlertSettingMaster
        col = AlertSettingMaster.__table__.columns["device_id"]
        fk_targets = {fk.target_fullname for fk in col.foreign_keys}
        # Assert
        assert "device_master.device_id" in fk_targets

    def test_alert_conditions_measurement_item_id_is_not_nullable(self):
        """alert_conditions_measurement_item_id は NOT NULL 制約を持つ"""
        # Arrange
        from iot_app.models.alert import AlertSettingMaster
        col = AlertSettingMaster.__table__.columns["alert_conditions_measurement_item_id"]
        # Assert
        assert col.nullable is False

    def test_alert_conditions_operator_is_not_nullable(self):
        """alert_conditions_operator は NOT NULL 制約を持つ"""
        # Arrange
        from iot_app.models.alert import AlertSettingMaster
        col = AlertSettingMaster.__table__.columns["alert_conditions_operator"]
        # Assert
        assert col.nullable is False

    def test_alert_conditions_threshold_is_not_nullable(self):
        """alert_conditions_threshold は NOT NULL 制約を持つ"""
        # Arrange
        from iot_app.models.alert import AlertSettingMaster
        col = AlertSettingMaster.__table__.columns["alert_conditions_threshold"]
        # Assert
        assert col.nullable is False

    def test_alert_recovery_conditions_measurement_item_id_is_not_nullable(self):
        """alert_recovery_conditions_measurement_item_id は NOT NULL 制約を持つ"""
        # Arrange
        from iot_app.models.alert import AlertSettingMaster
        col = AlertSettingMaster.__table__.columns["alert_recovery_conditions_measurement_item_id"]
        # Assert
        assert col.nullable is False

    def test_alert_recovery_conditions_operator_is_not_nullable(self):
        """alert_recovery_conditions_operator は NOT NULL 制約を持つ"""
        # Arrange
        from iot_app.models.alert import AlertSettingMaster
        col = AlertSettingMaster.__table__.columns["alert_recovery_conditions_operator"]
        # Assert
        assert col.nullable is False

    def test_alert_recovery_conditions_threshold_is_not_nullable(self):
        """alert_recovery_conditions_threshold は NOT NULL 制約を持つ"""
        # Arrange
        from iot_app.models.alert import AlertSettingMaster
        col = AlertSettingMaster.__table__.columns["alert_recovery_conditions_threshold"]
        # Assert
        assert col.nullable is False

    def test_judgment_time_default_is_5(self):
        """judgment_time のデフォルト値が 5 である"""
        # Arrange
        from iot_app.models.alert import AlertSettingMaster
        col = AlertSettingMaster.__table__.columns["judgment_time"]
        # Assert
        assert col.default.arg == 5

    def test_judgment_time_is_not_nullable(self):
        """judgment_time は NOT NULL 制約を持つ"""
        # Arrange
        from iot_app.models.alert import AlertSettingMaster
        col = AlertSettingMaster.__table__.columns["judgment_time"]
        # Assert
        assert col.nullable is False

    def test_alert_level_id_has_foreign_key(self):
        """alert_level_id は alert_level_master.alert_level_id への外部キーを持つ"""
        # Arrange
        from iot_app.models.alert import AlertSettingMaster
        col = AlertSettingMaster.__table__.columns["alert_level_id"]
        fk_targets = {fk.target_fullname for fk in col.foreign_keys}
        # Assert
        assert "alert_level_master.alert_level_id" in fk_targets

    def test_alert_notification_flag_default_is_true(self):
        """alert_notification_flag のデフォルト値が True である（UI仕様書 (4.8) デフォルト: checked）"""
        # Arrange
        from iot_app.models.alert import AlertSettingMaster
        col = AlertSettingMaster.__table__.columns["alert_notification_flag"]
        # Assert
        assert col.default.arg is True

    def test_alert_email_flag_default_is_true(self):
        """alert_email_flag のデフォルト値が True である（UI仕様書 (4.9) デフォルト: checked）"""
        # Arrange
        from iot_app.models.alert import AlertSettingMaster
        col = AlertSettingMaster.__table__.columns["alert_email_flag"]
        # Assert
        assert col.default.arg is True

    def test_delete_flag_default_is_false(self):
        """delete_flag のデフォルト値が False である（論理削除初期値）"""
        # Arrange
        from iot_app.models.alert import AlertSettingMaster
        col = AlertSettingMaster.__table__.columns["delete_flag"]
        # Assert
        assert col.default.arg is False

    def test_delete_flag_is_not_nullable(self):
        """delete_flag は NOT NULL 制約を持つ"""
        # Arrange
        from iot_app.models.alert import AlertSettingMaster
        col = AlertSettingMaster.__table__.columns["delete_flag"]
        # Assert
        assert col.nullable is False

    def test_create_date_is_not_nullable(self):
        """create_date は NOT NULL 制約を持つ（監査証跡）"""
        # Arrange
        from iot_app.models.alert import AlertSettingMaster
        col = AlertSettingMaster.__table__.columns["create_date"]
        # Assert
        assert col.nullable is False

    def test_creator_is_not_nullable(self):
        """creator は NOT NULL 制約を持つ（監査証跡）"""
        # Arrange
        from iot_app.models.alert import AlertSettingMaster
        col = AlertSettingMaster.__table__.columns["creator"]
        # Assert
        assert col.nullable is False

    def test_update_date_is_not_nullable(self):
        """update_date は NOT NULL 制約を持つ（監査証跡）"""
        # Arrange
        from iot_app.models.alert import AlertSettingMaster
        col = AlertSettingMaster.__table__.columns["update_date"]
        # Assert
        assert col.nullable is False

    def test_modifier_is_not_nullable(self):
        """modifier は NOT NULL 制約を持つ（監査証跡）"""
        # Arrange
        from iot_app.models.alert import AlertSettingMaster
        col = AlertSettingMaster.__table__.columns["modifier"]
        # Assert
        assert col.nullable is False


# ============================================================
# 2. AlertLevelMaster モデル定義テスト
# 観点: モデルのプロパティ・カラム定義（DB非依存）
# ============================================================

@pytest.mark.unit
class TestAlertLevelMaster:
    """AlertLevelMaster モデルのカラム定義テスト
    観点: モデルのプロパティ・制約定義（DB非依存）、1.1.2 最大文字列長チェック
    """

    def test_tablename_is_alert_level_master(self):
        """モデルのテーブル名が 'alert_level_master' である"""
        # Arrange & Act
        from iot_app.models.alert import AlertLevelMaster
        # Assert
        assert AlertLevelMaster.__tablename__ == "alert_level_master"

    def test_alert_level_id_is_primary_key(self):
        """alert_level_id が主キー (PK) として定義されている"""
        # Arrange
        from iot_app.models.alert import AlertLevelMaster
        col = AlertLevelMaster.__table__.columns["alert_level_id"]
        # Assert
        assert col.primary_key is True

    def test_alert_level_name_max_length_is_100(self):
        """1.1.2: alert_level_name の最大文字列長が 100 である"""
        # Arrange
        from iot_app.models.alert import AlertLevelMaster
        col = AlertLevelMaster.__table__.columns["alert_level_name"]
        # Assert
        assert col.type.length == 100

    def test_alert_level_name_is_not_nullable(self):
        """alert_level_name は NOT NULL 制約を持つ"""
        # Arrange
        from iot_app.models.alert import AlertLevelMaster
        col = AlertLevelMaster.__table__.columns["alert_level_name"]
        # Assert
        assert col.nullable is False

    def test_delete_flag_default_is_false(self):
        """delete_flag のデフォルト値が False である（論理削除初期値）"""
        # Arrange
        from iot_app.models.alert import AlertLevelMaster
        col = AlertLevelMaster.__table__.columns["delete_flag"]
        # Assert
        assert col.default.arg is False


# ============================================================
# 3. AlertStatusMaster モデル定義テスト
# 観点: モデルのプロパティ・カラム定義（DB非依存）
# ============================================================

@pytest.mark.unit
class TestAlertStatusMaster:
    """AlertStatusMaster モデルのカラム定義テスト
    観点: モデルのプロパティ・制約定義（DB非依存）
    """

    def test_tablename_is_alert_status_master(self):
        """モデルのテーブル名が 'alert_status_master' である"""
        # Arrange & Act
        from iot_app.models.alert import AlertStatusMaster
        # Assert
        assert AlertStatusMaster.__tablename__ == "alert_status_master"

    def test_alert_status_id_is_primary_key(self):
        """alert_status_id が主キー (PK) として定義されている"""
        # Arrange
        from iot_app.models.alert import AlertStatusMaster
        col = AlertStatusMaster.__table__.columns["alert_status_id"]
        # Assert
        assert col.primary_key is True

    def test_alert_status_name_is_not_nullable(self):
        """alert_status_name は NOT NULL 制約を持つ"""
        # Arrange
        from iot_app.models.alert import AlertStatusMaster
        col = AlertStatusMaster.__table__.columns["alert_status_name"]
        # Assert
        assert col.nullable is False

    def test_delete_flag_default_is_false(self):
        """delete_flag のデフォルト値が False である（論理削除初期値）"""
        # Arrange
        from iot_app.models.alert import AlertStatusMaster
        col = AlertStatusMaster.__table__.columns["delete_flag"]
        # Assert
        assert col.default.arg is False


# ============================================================
# 4. AlertHistory モデル定義テスト
# 観点: モデルのプロパティ・カラム定義（DB非依存）
# ============================================================

@pytest.mark.unit
class TestAlertHistory:
    """AlertHistory モデルのカラム定義テスト
    観点: モデルのプロパティ・制約定義（DB非依存）
    """

    def test_tablename_is_alert_history(self):
        """モデルのテーブル名が 'alert_history' である"""
        # Arrange & Act
        from iot_app.models.alert import AlertHistory
        # Assert
        assert AlertHistory.__tablename__ == "alert_history"

    def test_alert_history_id_is_primary_key(self):
        """alert_history_id が主キー (PK) として定義されている"""
        # Arrange
        from iot_app.models.alert import AlertHistory
        col = AlertHistory.__table__.columns["alert_history_id"]
        # Assert
        assert col.primary_key is True

    def test_alert_id_has_foreign_key_to_alert_setting_master(self):
        """alert_id は alert_setting_master.alert_id への外部キーを持つ"""
        # Arrange
        from iot_app.models.alert import AlertHistory
        col = AlertHistory.__table__.columns["alert_id"]
        fk_targets = {fk.target_fullname for fk in col.foreign_keys}
        # Assert
        assert "alert_setting_master.alert_id" in fk_targets

    def test_alert_recovery_datetime_is_nullable(self):
        """alert_recovery_datetime は NULL 許容（復旧前は NULL）"""
        # Arrange
        from iot_app.models.alert import AlertHistory
        col = AlertHistory.__table__.columns["alert_recovery_datetime"]
        # Assert
        assert col.nullable is True

    def test_alert_value_is_nullable(self):
        """alert_value は NULL 許容"""
        # Arrange
        from iot_app.models.alert import AlertHistory
        col = AlertHistory.__table__.columns["alert_value"]
        # Assert
        assert col.nullable is True

    def test_alert_occurrence_datetime_is_not_nullable(self):
        """alert_occurrence_datetime は NOT NULL 制約を持つ"""
        # Arrange
        from iot_app.models.alert import AlertHistory
        col = AlertHistory.__table__.columns["alert_occurrence_datetime"]
        # Assert
        assert col.nullable is False

    def test_delete_flag_default_is_false(self):
        """delete_flag のデフォルト値が False である（論理削除初期値）"""
        # Arrange
        from iot_app.models.alert import AlertHistory
        col = AlertHistory.__table__.columns["delete_flag"]
        # Assert
        assert col.default.arg is False
