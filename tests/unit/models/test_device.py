"""
デバイス管理 - Model層 単体テスト

対象ファイル: src/iot_app/models/device.py

参照ドキュメント:
  - UI仕様書:           docs/03-features/flask-app/devices/ui-specification.md
  - 機能設計書:         docs/03-features/flask-app/devices/workflow-specification.md
  - 単体テスト観点表:   docs/05-testing/unit-test/unit-test-perspectives.md
  - 実装ガイド:         docs/05-testing/unit-test/unit-test-guide.md

テスト対象:
  - DeviceMaster:     DB非依存のプロパティ・デフォルト値・コンストラクタ挙動
  - DeviceTypeMaster: DB非依存のプロパティ・デフォルト値
"""
import pytest
from datetime import datetime


# ============================================================
# ヘルパー関数
# ============================================================

def make_valid_device_master_kwargs(**overrides):
    """DeviceMaster コンストラクタの最小有効引数セットを返す"""
    kwargs = {
        'device_uuid':                 'DEV-001',
        'organization_id':             1,
        'device_type_id':              1,
        'device_name':                 'センサー1号機',
        'device_model':                'MODEL-A100',
        'creator':                     1,
        'modifier':                    1,
    }
    kwargs.update(overrides)
    return kwargs


def make_valid_device_type_master_kwargs(**overrides):
    """DeviceTypeMaster コンストラクタの最小有効引数セットを返す"""
    kwargs = {
        'device_type_name': 'センサー',
        'creator':          1,
        'modifier':         1,
    }
    kwargs.update(overrides)
    return kwargs


# ============================================================
# 1. DeviceMaster
# 観点: 2.1 正常系処理（有効な入力データ）
# ============================================================

@pytest.mark.unit
class TestDeviceMasterDefaults:
    """DeviceMaster - デフォルト値のテスト
    観点: 2.1.1 正常系処理（有効な入力データ）
    """

    def test_delete_flag_defaults_to_false(self):
        """2.1.1: delete_flag を指定しない場合、デフォルト値 False が設定される"""
        # Arrange / Act
        from iot_app.models.device import DeviceMaster

        kwargs = make_valid_device_master_kwargs()
        kwargs.pop('delete_flag', None)   # 明示的に指定しない

        instance = DeviceMaster(**kwargs)

        # Assert: delete_flag のデフォルト値が False であること
        assert instance.delete_flag is False

    def test_delete_flag_can_be_set_to_true(self):
        """2.1.1: delete_flag=True を明示的に指定した場合、True が設定される"""
        # Arrange / Act
        from iot_app.models.device import DeviceMaster

        instance = DeviceMaster(**make_valid_device_master_kwargs(delete_flag=True))

        # Assert: delete_flag が True であること
        assert instance.delete_flag is True

    def test_device_uuid_is_set_correctly(self):
        """2.1.1: 指定した device_uuid がインスタンスに設定される"""
        # Arrange / Act
        from iot_app.models.device import DeviceMaster

        instance = DeviceMaster(**make_valid_device_master_kwargs(device_uuid='DEV-TEST-001'))

        # Assert: device_uuid に指定した値が設定されること
        assert instance.device_uuid == 'DEV-TEST-001'

    def test_device_name_is_set_correctly(self):
        """2.1.1: 指定した device_name がインスタンスに設定される"""
        # Arrange / Act
        from iot_app.models.device import DeviceMaster

        instance = DeviceMaster(**make_valid_device_master_kwargs(device_name='温度センサー'))

        # Assert: device_name に指定した値が設定されること
        assert instance.device_name == '温度センサー'

    def test_sim_id_none_by_default(self):
        """2.1.2: sim_id を指定しない場合、None が設定される（nullable列）"""
        # Arrange / Act
        from iot_app.models.device import DeviceMaster

        kwargs = make_valid_device_master_kwargs()
        kwargs.pop('sim_id', None)   # 指定しない

        instance = DeviceMaster(**kwargs)

        # Assert: sim_id が None であること（任意項目）
        assert instance.sim_id is None

    def test_mac_address_none_by_default(self):
        """2.1.2: mac_address を指定しない場合、None が設定される（nullable列）"""
        # Arrange / Act
        from iot_app.models.device import DeviceMaster

        kwargs = make_valid_device_master_kwargs()
        kwargs.pop('mac_address', None)   # 指定しない

        instance = DeviceMaster(**kwargs)

        # Assert: mac_address が None であること（任意項目）
        assert instance.mac_address is None

    def test_mac_address_set_correctly(self):
        """2.1.1: 指定した mac_address がインスタンスに設定される"""
        # Arrange / Act
        from iot_app.models.device import DeviceMaster

        instance = DeviceMaster(
            **make_valid_device_master_kwargs(mac_address='AA:BB:CC:DD:EE:FF')
        )

        # Assert: mac_address に指定した値が設定されること
        assert instance.mac_address == 'AA:BB:CC:DD:EE:FF'

    def test_software_version_none_by_default(self):
        """2.1.2: software_version を指定しない場合、None が設定される（nullable列）"""
        # Arrange / Act
        from iot_app.models.device import DeviceMaster

        kwargs = make_valid_device_master_kwargs()
        kwargs.pop('software_version', None)   # 指定しない

        instance = DeviceMaster(**kwargs)

        # Assert: software_version が None であること（任意項目）
        assert instance.software_version is None

    def test_device_location_none_by_default(self):
        """2.1.2: device_location を指定しない場合、None が設定される（nullable列）"""
        # Arrange / Act
        from iot_app.models.device import DeviceMaster

        kwargs = make_valid_device_master_kwargs()
        kwargs.pop('device_location', None)   # 指定しない

        instance = DeviceMaster(**kwargs)

        # Assert: device_location が None であること（任意項目）
        assert instance.device_location is None

    def test_certificate_expiration_date_none_by_default(self):
        """2.1.2: certificate_expiration_date を指定しない場合、None が設定される（nullable列）"""
        # Arrange / Act
        from iot_app.models.device import DeviceMaster

        kwargs = make_valid_device_master_kwargs()
        kwargs.pop('certificate_expiration_date', None)   # 指定しない

        instance = DeviceMaster(**kwargs)

        # Assert: certificate_expiration_date が None であること（任意項目）
        assert instance.certificate_expiration_date is None

    def test_certificate_expiration_date_set_correctly(self):
        """2.1.1: 指定した certificate_expiration_date がインスタンスに設定される"""
        # Arrange
        from iot_app.models.device import DeviceMaster

        expiry = datetime(2025, 12, 31, 0, 0, 0)
        instance = DeviceMaster(
            **make_valid_device_master_kwargs(certificate_expiration_date=expiry)
        )

        # Assert: certificate_expiration_date に指定した値が設定されること
        assert instance.certificate_expiration_date == expiry

    def test_device_type_id_set_correctly(self):
        """2.1.1: 指定した device_type_id がインスタンスに設定される"""
        # Arrange / Act
        from iot_app.models.device import DeviceMaster

        instance = DeviceMaster(**make_valid_device_master_kwargs(device_type_id=2))

        # Assert: device_type_id に指定した値が設定されること
        assert instance.device_type_id == 2

    def test_tablename_is_device_master(self):
        """2.1.1: テーブル名が 'device_master' であること"""
        # Arrange / Act
        from iot_app.models.device import DeviceMaster

        # Assert: __tablename__ が 'device_master' であること
        assert DeviceMaster.__tablename__ == 'device_master'

    def test_device_model_set_correctly(self):
        """2.1.1: 指定した device_model がインスタンスに設定される（nullable=False フィールド）"""
        # Arrange / Act
        from iot_app.models.device import DeviceMaster

        instance = DeviceMaster(**make_valid_device_master_kwargs(device_model='MODEL-B200'))

        # Assert: device_model に指定した値が設定されること
        assert instance.device_model == 'MODEL-B200'

    def test_device_inventory_id_set_correctly(self):
        """2.1.1: 指定した device_inventory_id がインスタンスに設定される（nullable列）"""
        # Arrange / Act
        from iot_app.models.device import DeviceMaster

        instance = DeviceMaster(**make_valid_device_master_kwargs(device_inventory_id=42))

        # Assert: device_inventory_id に指定した値が設定されること
        assert instance.device_inventory_id == 42

    def test_device_inventory_id_none_by_default(self):
        """2.1.2: device_inventory_id を指定しない場合、None が設定される（nullable列）"""
        # Arrange / Act
        from iot_app.models.device import DeviceMaster

        kwargs = make_valid_device_master_kwargs()
        kwargs.pop('device_inventory_id', None)   # 指定しない

        instance = DeviceMaster(**kwargs)

        # Assert: device_inventory_id が None であること（任意項目）
        assert instance.device_inventory_id is None

    def test_creator_and_modifier_set_correctly(self):
        """2.1.1: 指定した creator と modifier がインスタンスに設定される（監査証跡フィールド）"""
        # Arrange / Act
        from iot_app.models.device import DeviceMaster

        instance = DeviceMaster(**make_valid_device_master_kwargs(creator=10, modifier=20))

        # Assert: creator/modifier に指定した値が設定されること
        assert instance.creator == 10
        assert instance.modifier == 20

    def test_software_version_set_correctly(self):
        """2.1.1: 指定した software_version がインスタンスに設定される"""
        # Arrange / Act
        from iot_app.models.device import DeviceMaster

        instance = DeviceMaster(**make_valid_device_master_kwargs(software_version='v1.2.3'))

        # Assert: software_version に指定した値が設定されること
        assert instance.software_version == 'v1.2.3'


# ============================================================
# 2. DeviceTypeMaster
# 観点: 2.1 正常系処理（有効な入力データ）
# ============================================================

@pytest.mark.unit
class TestDeviceTypeMasterDefaults:
    """DeviceTypeMaster - デフォルト値のテスト
    観点: 2.1.1 正常系処理（有効な入力データ）
    """

    def test_delete_flag_defaults_to_false(self):
        """2.1.1: delete_flag を指定しない場合、デフォルト値 False が設定される"""
        # Arrange / Act
        from iot_app.models.device import DeviceTypeMaster

        kwargs = make_valid_device_type_master_kwargs()
        kwargs.pop('delete_flag', None)   # 明示的に指定しない

        instance = DeviceTypeMaster(**kwargs)

        # Assert: delete_flag のデフォルト値が False であること
        assert instance.delete_flag is False

    def test_delete_flag_can_be_set_to_true(self):
        """2.1.1: delete_flag=True を明示的に指定した場合、True が設定される"""
        # Arrange / Act
        from iot_app.models.device import DeviceTypeMaster

        instance = DeviceTypeMaster(
            **make_valid_device_type_master_kwargs(delete_flag=True)
        )

        # Assert: delete_flag が True であること
        assert instance.delete_flag is True

    def test_device_type_name_set_correctly(self):
        """2.1.1: 指定した device_type_name がインスタンスに設定される"""
        # Arrange / Act
        from iot_app.models.device import DeviceTypeMaster

        instance = DeviceTypeMaster(
            **make_valid_device_type_master_kwargs(device_type_name='ゲートウェイ')
        )

        # Assert: device_type_name に指定した値が設定されること
        assert instance.device_type_name == 'ゲートウェイ'

    def test_tablename_is_device_type_master(self):
        """2.1.1: テーブル名が 'device_type_master' であること"""
        # Arrange / Act
        from iot_app.models.device import DeviceTypeMaster

        # Assert: __tablename__ が 'device_type_master' であること
        assert DeviceTypeMaster.__tablename__ == 'device_type_master'

    def test_creator_and_modifier_set_correctly(self):
        """2.1.1: 指定した creator と modifier がインスタンスに設定される（監査証跡フィールド）"""
        # Arrange / Act
        from iot_app.models.device import DeviceTypeMaster

        instance = DeviceTypeMaster(
            **make_valid_device_type_master_kwargs(creator=5, modifier=7)
        )

        # Assert: creator/modifier に指定した値が設定されること
        assert instance.creator == 5
        assert instance.modifier == 7


# ============================================================
# 3. DeviceMasterByUser
# 観点: 2.1 正常系処理（有効な入力データ）
# ============================================================

def make_valid_device_master_by_user_kwargs(**overrides):
    """DeviceMasterByUser コンストラクタの最小有効引数セットを返す"""
    kwargs = {
        'user_id':              1,
        'user_name':            'テストユーザー',
        'user_organization_id': 1,
        'device_id':            1,
        'device_type_id':       1,
        'device_name':          'センサー1号機',
        'device_model':         'MODEL-A100',
        'device_stock_id':      1,
        'creator':              1,
        'modifier':             1,
        'depth':                0,
    }
    kwargs.update(overrides)
    return kwargs


@pytest.mark.unit
class TestDeviceMasterByUser:
    """DeviceMasterByUser - デフォルト値・フィールド値のテスト
    観点: 2.1.1 正常系処理（有効な入力データ）
    対象: v_device_master_by_user VIEW（ログインユーザーが参照可能なデバイス一覧）
    """

    def test_tablename_is_v_device_master_by_user(self):
        """2.1.1: テーブル名（ビュー名）が 'v_device_master_by_user' であること"""
        # Arrange / Act
        from iot_app.models.device import DeviceMasterByUser

        # Assert
        assert DeviceMasterByUser.__tablename__ == 'v_device_master_by_user'

    def test_delete_flag_defaults_to_false(self):
        """2.1.1: delete_flag を指定しない場合、デフォルト値 False が設定される"""
        # Arrange / Act
        from iot_app.models.device import DeviceMasterByUser

        kwargs = make_valid_device_master_by_user_kwargs()
        kwargs.pop('delete_flag', None)

        instance = DeviceMasterByUser(**kwargs)

        # Assert
        assert instance.delete_flag is False

    def test_user_id_set_correctly(self):
        """2.1.1: 指定した user_id がインスタンスに設定される"""
        # Arrange / Act
        from iot_app.models.device import DeviceMasterByUser

        instance = DeviceMasterByUser(**make_valid_device_master_by_user_kwargs(user_id=99))

        # Assert
        assert instance.user_id == 99

    def test_device_id_set_correctly(self):
        """2.1.1: 指定した device_id がインスタンスに設定される"""
        # Arrange / Act
        from iot_app.models.device import DeviceMasterByUser

        instance = DeviceMasterByUser(**make_valid_device_master_by_user_kwargs(device_id=42))

        # Assert
        assert instance.device_id == 42

    def test_device_name_set_correctly(self):
        """2.1.1: 指定した device_name がインスタンスに設定される"""
        # Arrange / Act
        from iot_app.models.device import DeviceMasterByUser

        instance = DeviceMasterByUser(
            **make_valid_device_master_by_user_kwargs(device_name='温度センサー')
        )

        # Assert
        assert instance.device_name == '温度センサー'

    def test_device_model_set_correctly(self):
        """2.1.1: 指定した device_model がインスタンスに設定される"""
        # Arrange / Act
        from iot_app.models.device import DeviceMasterByUser

        instance = DeviceMasterByUser(
            **make_valid_device_master_by_user_kwargs(device_model='MODEL-X500')
        )

        # Assert
        assert instance.device_model == 'MODEL-X500'

    def test_depth_set_correctly(self):
        """2.1.1: 指定した depth（組織階層深さ）がインスタンスに設定される"""
        # Arrange / Act
        from iot_app.models.device import DeviceMasterByUser

        instance = DeviceMasterByUser(**make_valid_device_master_by_user_kwargs(depth=3))

        # Assert
        assert instance.depth == 3

    def test_sim_id_none_by_default(self):
        """2.1.2: sim_id を指定しない場合、None が設定される（nullable列）"""
        # Arrange / Act
        from iot_app.models.device import DeviceMasterByUser

        kwargs = make_valid_device_master_by_user_kwargs()
        kwargs.pop('sim_id', None)

        instance = DeviceMasterByUser(**kwargs)

        # Assert
        assert instance.sim_id is None

    def test_mac_address_none_by_default(self):
        """2.1.2: mac_address を指定しない場合、None が設定される（nullable列）"""
        # Arrange / Act
        from iot_app.models.device import DeviceMasterByUser

        kwargs = make_valid_device_master_by_user_kwargs()
        kwargs.pop('mac_address', None)

        instance = DeviceMasterByUser(**kwargs)

        # Assert
        assert instance.mac_address is None

    def test_device_location_none_by_default(self):
        """2.1.2: device_location を指定しない場合、None が設定される（nullable列）"""
        # Arrange / Act
        from iot_app.models.device import DeviceMasterByUser

        kwargs = make_valid_device_master_by_user_kwargs()
        kwargs.pop('device_location', None)

        instance = DeviceMasterByUser(**kwargs)

        # Assert
        assert instance.device_location is None

    def test_certificate_expiration_date_none_by_default(self):
        """2.1.2: certificate_expiration_date を指定しない場合、None が設定される（nullable列）"""
        # Arrange / Act
        from iot_app.models.device import DeviceMasterByUser

        kwargs = make_valid_device_master_by_user_kwargs()
        kwargs.pop('certificate_expiration_date', None)

        instance = DeviceMasterByUser(**kwargs)

        # Assert
        assert instance.certificate_expiration_date is None

    def test_software_version_none_by_default(self):
        """2.1.2: software_version を指定しない場合、None が設定される（nullable列）"""
        # Arrange / Act
        from iot_app.models.device import DeviceMasterByUser

        kwargs = make_valid_device_master_by_user_kwargs()
        kwargs.pop('software_version', None)

        instance = DeviceMasterByUser(**kwargs)

        # Assert
        assert instance.software_version is None
