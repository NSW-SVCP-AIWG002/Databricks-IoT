"""
顧客作成ダッシュボード - モデル単体テスト（DB非依存）
対象: src/iot_app/models/customer_dashboard.py（予定）

テスト観点: モデルのプロパティ・デフォルト値・インスタンス生成（DB操作は対象外）
"""

import pytest
from unittest.mock import MagicMock


# ---------------------------------------------------------------------------
# DashboardMaster
# ---------------------------------------------------------------------------

@pytest.mark.unit
class TestDashboardMaster:
    """観点: モデル定義（カラム・デフォルト値・インスタンス生成）

    README データモデル § dashboard_master
    """

    def test_instantiate_with_required_fields(self):
        """必須フィールドを指定してインスタンスを生成できる"""
        # Arrange / Act
        from iot_app.models.customer_dashboard import DashboardMaster

        dashboard = DashboardMaster(
            dashboard_uuid='test-uuid-001',
            dashboard_name='テストダッシュボード',
            organization_id=1,
            creator=1,
            modifier=1,
        )

        # Assert
        assert dashboard.dashboard_uuid == 'test-uuid-001'
        assert dashboard.dashboard_name == 'テストダッシュボード'
        assert dashboard.organization_id == 1

    def test_delete_flag_default_is_false(self):
        """delete_flag のデフォルト値は False"""
        # Arrange / Act
        from iot_app.models.customer_dashboard import DashboardMaster

        dashboard = DashboardMaster(
            dashboard_uuid='test-uuid-001',
            dashboard_name='テストダッシュボード',
            organization_id=1,
            creator=1,
            modifier=1,
        )

        # Assert
        assert dashboard.delete_flag is False

    def test_dashboard_name_max_length(self):
        """dashboard_name は最大50文字を受け付ける"""
        # Arrange
        from iot_app.models.customer_dashboard import DashboardMaster

        name_50 = 'あ' * 50

        # Act
        dashboard = DashboardMaster(
            dashboard_uuid='test-uuid-001',
            dashboard_name=name_50,
            organization_id=1,
            creator=1,
            modifier=1,
        )

        # Assert
        assert len(dashboard.dashboard_name) == 50


# ---------------------------------------------------------------------------
# DashboardGroupMaster
# ---------------------------------------------------------------------------

@pytest.mark.unit
class TestDashboardGroupMaster:
    """観点: モデル定義（カラム・デフォルト値・インスタンス生成）

    README データモデル § dashboard_group_master
    """

    def test_instantiate_with_required_fields(self):
        """必須フィールドを指定してインスタンスを生成できる"""
        # Arrange / Act
        from iot_app.models.customer_dashboard import DashboardGroupMaster

        group = DashboardGroupMaster(
            dashboard_group_uuid='group-uuid-001',
            dashboard_group_name='グループA',
            dashboard_id=1,
            display_order=0,
            creator=1,
            modifier=1,
        )

        # Assert
        assert group.dashboard_group_uuid == 'group-uuid-001'
        assert group.dashboard_group_name == 'グループA'
        assert group.dashboard_id == 1
        assert group.display_order == 0

    def test_delete_flag_default_is_false(self):
        """delete_flag のデフォルト値は False"""
        # Arrange / Act
        from iot_app.models.customer_dashboard import DashboardGroupMaster

        group = DashboardGroupMaster(
            dashboard_group_uuid='group-uuid-001',
            dashboard_group_name='グループA',
            dashboard_id=1,
            display_order=0,
            creator=1,
            modifier=1,
        )

        # Assert
        assert group.delete_flag is False

    def test_group_name_max_length(self):
        """dashboard_group_name は最大50文字を受け付ける"""
        # Arrange
        from iot_app.models.customer_dashboard import DashboardGroupMaster

        name_50 = 'あ' * 50

        # Act
        group = DashboardGroupMaster(
            dashboard_group_uuid='group-uuid-001',
            dashboard_group_name=name_50,
            dashboard_id=1,
            display_order=0,
            creator=1,
            modifier=1,
        )

        # Assert
        assert len(group.dashboard_group_name) == 50


# ---------------------------------------------------------------------------
# DashboardGadgetMaster
# ---------------------------------------------------------------------------

@pytest.mark.unit
class TestDashboardGadgetMaster:
    """観点: モデル定義（カラム・デフォルト値・gadget_size 値域）

    README データモデル § dashboard_gadget_master
    gadget_size: 0=2×2（480×480px）、1=2×4（960×480px）の2択
    """

    def test_instantiate_with_required_fields(self):
        """必須フィールドを指定してインスタンスを生成できる"""
        # Arrange / Act
        from iot_app.models.customer_dashboard import DashboardGadgetMaster

        gadget = DashboardGadgetMaster(
            gadget_uuid='gadget-uuid-001',
            gadget_name='テストガジェット',
            dashboard_group_id=1,
            gadget_type_id=1,
            chart_config={},
            data_source_config={},
            position_x=0,
            position_y=0,
            gadget_size=0,
            display_order=0,
            creator=1,
            modifier=1,
        )

        # Assert
        assert gadget.gadget_uuid == 'gadget-uuid-001'
        assert gadget.gadget_name == 'テストガジェット'

    def test_delete_flag_default_is_false(self):
        """delete_flag のデフォルト値は False"""
        # Arrange / Act
        from iot_app.models.customer_dashboard import DashboardGadgetMaster

        gadget = DashboardGadgetMaster(
            gadget_uuid='gadget-uuid-001',
            gadget_name='テストガジェット',
            dashboard_group_id=1,
            gadget_type_id=1,
            chart_config={},
            data_source_config={},
            position_x=0,
            position_y=0,
            gadget_size=0,
            display_order=0,
            creator=1,
            modifier=1,
        )

        # Assert
        assert gadget.delete_flag is False

    def test_gadget_name_max_length(self):
        """gadget_name は最大20文字を受け付ける"""
        # Arrange
        from iot_app.models.customer_dashboard import DashboardGadgetMaster

        name_20 = 'あ' * 20

        # Act
        gadget = DashboardGadgetMaster(
            gadget_uuid='gadget-uuid-001',
            gadget_name=name_20,
            dashboard_group_id=1,
            gadget_type_id=1,
            chart_config={},
            data_source_config={},
            position_x=0,
            position_y=0,
            gadget_size=0,
            display_order=0,
            creator=1,
            modifier=1,
        )

        # Assert
        assert len(gadget.gadget_name) == 20


# ---------------------------------------------------------------------------
# GadgetTypeMaster
# ---------------------------------------------------------------------------

@pytest.mark.unit
class TestGadgetTypeMaster:
    """観点: モデル定義（カラム・data_source_type 値域）

    README データモデル § gadget_type_master
    data_source_type: 0=組織、1=デバイス
    """

    def test_instantiate_with_required_fields(self):
        """必須フィールドを指定してインスタンスを生成できる"""
        # Arrange / Act
        from iot_app.models.customer_dashboard import GadgetTypeMaster

        gadget_type = GadgetTypeMaster(
            gadget_type_name='棒グラフ',
            data_source_type=0,
            gadget_image_path='static/images/bar_chart.png',
            gadget_description='棒グラフガジェット',
            display_order=1,
            creator=1,
            modifier=1,
        )

        # Assert
        assert gadget_type.gadget_type_name == '棒グラフ'
        assert gadget_type.data_source_type == 0
        assert gadget_type.display_order == 1

    def test_delete_flag_default_is_false(self):
        """delete_flag のデフォルト値は False"""
        # Arrange / Act
        from iot_app.models.customer_dashboard import GadgetTypeMaster

        gadget_type = GadgetTypeMaster(
            gadget_type_name='棒グラフ',
            data_source_type=0,
            gadget_image_path='static/images/bar_chart.png',
            gadget_description='棒グラフガジェット',
            display_order=1,
            creator=1,
            modifier=1,
        )

        # Assert
        assert gadget_type.delete_flag is False


# ---------------------------------------------------------------------------
# DashboardUserSetting
# ---------------------------------------------------------------------------

@pytest.mark.unit
class TestDashboardUserSetting:
    """観点: モデル定義（カラム・organization_id/device_id の未選択デフォルト値）

    README データモデル § dashboard_user_setting
    organization_id / device_id: 未選択の場合は 0 を登録
    """

    def test_instantiate_with_required_fields(self):
        """必須フィールドを指定してインスタンスを生成できる"""
        # Arrange / Act
        from iot_app.models.customer_dashboard import DashboardUserSetting

        setting = DashboardUserSetting(
            user_id=1,
            dashboard_id=1,
            organization_id=None,
            device_id=None,
            creator=1,
            modifier=1,
        )

        # Assert
        assert setting.user_id == 1
        assert setting.dashboard_id == 1

    def test_delete_flag_default_is_false(self):
        """delete_flag のデフォルト値は False"""
        # Arrange / Act
        from iot_app.models.customer_dashboard import DashboardUserSetting

        setting = DashboardUserSetting(
            user_id=1,
            dashboard_id=1,
            organization_id=None,
            device_id=None,
            creator=1,
            modifier=1,
        )

        # Assert
        assert setting.delete_flag is False
