"""
デバイス台帳管理 - Model層 単体テスト

対象ファイル: src/iot_app/models/device_stock.py

参照ドキュメント:
  - 機能設計書:       docs/03-features/flask-app/device-inventory/workflow-specification.md
  - UI仕様書:         docs/03-features/flask-app/device-inventory/ui-specification.md
  - 単体テスト観点表: docs/05-testing/unit-test/unit-test-perspectives.md
  - 実装ガイド:       docs/05-testing/unit-test/unit-test-guide.md

テスト対象:
  - DeviceInventoryMaster: DB非依存のプロパティ・デフォルト値・コンストラクタ挙動
  - InventoryStatusMaster: DB非依存のプロパティ・デフォルト値
"""
import pytest
from datetime import date, datetime
from unittest.mock import MagicMock, patch


# ============================================================
# 定数
# ============================================================

MODEL_MODULE = 'iot_app.models.device_inventory'


# ============================================================
# ヘルパー関数
# ============================================================

def make_valid_inventory_kwargs(**overrides):
    """DeviceInventoryMaster コンストラクタの最小有効引数セットを返す"""
    kwargs = {
        'device_inventory_uuid':           'INV-UUID-001',
        'inventory_status_id':             1,
        'device_model':                    'MODEL-X100',
        'mac_address':                     'AA:BB:CC:DD:EE:FF',
        'purchase_date':                   date(2025, 1, 15),
        'manufacturer_warranty_end_date':  date(2026, 1, 15),
        'inventory_location':              '倉庫A',
        'creator':                         1,
        'modifier':                        1,
    }
    kwargs.update(overrides)
    return kwargs


# ============================================================
# 1. DeviceInventoryMaster
# 観点: 2.1 正常系処理（有効な入力データ）
# ============================================================

@pytest.mark.unit
class TestDeviceInventoryMasterDefaults:
    """DeviceInventoryMaster - デフォルト値のテスト
    観点: 2.1.1 正常系処理（有効な入力データ）
    """

    def test_delete_flag_defaults_to_false(self):
        """2.1.1: delete_flag を指定しない場合、デフォルト値 False が設定される"""
        # Arrange / Act
        from iot_app.models.device_inventory import DeviceInventoryMaster

        kwargs = make_valid_inventory_kwargs()
        # delete_flag を明示的に指定しない
        kwargs.pop('delete_flag', None)

        instance = DeviceInventoryMaster(**kwargs)

        # Assert: delete_flag のデフォルト値が False であること
        assert instance.delete_flag is False

    def test_delete_flag_can_be_set_to_true(self):
        """2.1.1: delete_flag=True を指定した場合、True が設定される"""
        # Arrange / Act
        from iot_app.models.device_inventory import DeviceInventoryMaster

        instance = DeviceInventoryMaster(
            **make_valid_inventory_kwargs(delete_flag=True)
        )

        # Assert: delete_flag が True であること
        assert instance.delete_flag is True

    def test_delete_flag_explicit_false_stays_false(self):
        """2.1.1: delete_flag=False を明示的に指定した場合、False が維持される"""
        # Arrange / Act
        from iot_app.models.device_inventory import DeviceInventoryMaster

        instance = DeviceInventoryMaster(
            **make_valid_inventory_kwargs(delete_flag=False)
        )

        # Assert: delete_flag が False であること
        assert instance.delete_flag is False

    def test_estimated_ship_date_defaults_to_none(self):
        """2.1.1: estimated_ship_date を指定しない場合、None が設定される（任意項目）"""
        # Arrange / Act
        from iot_app.models.device_inventory import DeviceInventoryMaster

        instance = DeviceInventoryMaster(**make_valid_inventory_kwargs())

        # Assert: estimated_ship_date のデフォルト値が None であること
        assert instance.estimated_ship_date is None

    def test_ship_date_defaults_to_none(self):
        """2.1.1: ship_date を指定しない場合、None が設定される（任意項目）"""
        # Arrange / Act
        from iot_app.models.device_inventory import DeviceInventoryMaster

        instance = DeviceInventoryMaster(**make_valid_inventory_kwargs())

        # Assert: ship_date のデフォルト値が None であること
        assert instance.ship_date is None


@pytest.mark.unit
class TestDeviceInventoryMasterInit:
    """DeviceInventoryMaster - コンストラクタ・フィールド設定のテスト
    観点: 2.1.1 正常系処理（有効な入力データ）, 2.1.2 正常系処理（最小構成の入力）
    """

    def test_device_inventory_uuid_is_set_correctly(self):
        """2.1.1: device_inventory_uuid が正しく設定される"""
        # Arrange
        expected_uuid = 'INV-UUID-TEST-001'

        # Act
        from iot_app.models.device_inventory import DeviceInventoryMaster

        instance = DeviceInventoryMaster(
            **make_valid_inventory_kwargs(device_inventory_uuid=expected_uuid)
        )

        # Assert: device_inventory_uuid が期待値と一致すること
        assert instance.device_inventory_uuid == expected_uuid

    def test_inventory_status_id_is_set_correctly(self):
        """2.1.1: inventory_status_id が正しく設定される（必須項目）"""
        # Arrange
        expected_status_id = 3

        # Act
        from iot_app.models.device_inventory import DeviceInventoryMaster

        instance = DeviceInventoryMaster(
            **make_valid_inventory_kwargs(inventory_status_id=expected_status_id)
        )

        # Assert: inventory_status_id が期待値と一致すること
        assert instance.inventory_status_id == expected_status_id

    def test_device_model_is_set_correctly(self):
        """2.1.1: device_model が正しく設定される（必須、最大100文字）"""
        # Arrange
        expected_model = 'MODEL-Z500'

        # Act
        from iot_app.models.device_inventory import DeviceInventoryMaster

        instance = DeviceInventoryMaster(
            **make_valid_inventory_kwargs(device_model=expected_model)
        )

        # Assert: device_model が期待値と一致すること
        assert instance.device_model == expected_model

    def test_mac_address_is_set_correctly(self):
        """2.1.1: mac_address が XX:XX:XX:XX:XX:XX 形式で正しく設定される（必須）"""
        # Arrange
        expected_mac = 'BB:CC:DD:EE:FF:00'

        # Act
        from iot_app.models.device_inventory import DeviceInventoryMaster

        instance = DeviceInventoryMaster(
            **make_valid_inventory_kwargs(mac_address=expected_mac)
        )

        # Assert: mac_address が期待値と一致すること
        assert instance.mac_address == expected_mac

    def test_purchase_date_is_set_correctly(self):
        """2.1.1: purchase_date が正しく設定される（必須、日付型）"""
        # Arrange
        expected_date = date(2025, 6, 15)

        # Act
        from iot_app.models.device_inventory import DeviceInventoryMaster

        instance = DeviceInventoryMaster(
            **make_valid_inventory_kwargs(purchase_date=expected_date)
        )

        # Assert: purchase_date が期待値と一致すること
        assert instance.purchase_date == expected_date

    def test_manufacturer_warranty_end_date_is_set_correctly(self):
        """2.1.1: manufacturer_warranty_end_date が正しく設定される（必須）"""
        # Arrange
        expected_date = date(2027, 12, 31)

        # Act
        from iot_app.models.device_inventory import DeviceInventoryMaster

        instance = DeviceInventoryMaster(
            **make_valid_inventory_kwargs(manufacturer_warranty_end_date=expected_date)
        )

        # Assert: manufacturer_warranty_end_date が期待値と一致すること
        assert instance.manufacturer_warranty_end_date == expected_date

    def test_inventory_location_is_set_correctly(self):
        """2.1.1: inventory_location が正しく設定される（必須、最大100文字）"""
        # Arrange
        expected_location = '新倉庫B-棚3'

        # Act
        from iot_app.models.device_inventory import DeviceInventoryMaster

        instance = DeviceInventoryMaster(
            **make_valid_inventory_kwargs(inventory_location=expected_location)
        )

        # Assert: inventory_location が期待値と一致すること
        assert instance.inventory_location == expected_location

    def test_estimated_ship_date_is_set_when_provided(self):
        """2.1.1: estimated_ship_date を指定した場合、正しく設定される（任意）"""
        # Arrange
        expected_date = date(2025, 3, 1)

        # Act
        from iot_app.models.device_inventory import DeviceInventoryMaster

        instance = DeviceInventoryMaster(
            **make_valid_inventory_kwargs(estimated_ship_date=expected_date)
        )

        # Assert: estimated_ship_date が期待値と一致すること
        assert instance.estimated_ship_date == expected_date

    def test_ship_date_is_set_when_provided(self):
        """2.1.1: ship_date を指定した場合、正しく設定される（任意）"""
        # Arrange
        expected_date = date(2025, 4, 10)

        # Act
        from iot_app.models.device_inventory import DeviceInventoryMaster

        instance = DeviceInventoryMaster(
            **make_valid_inventory_kwargs(ship_date=expected_date)
        )

        # Assert: ship_date が期待値と一致すること
        assert instance.ship_date == expected_date

    def test_creator_and_modifier_are_set_correctly(self):
        """2.1.1: creator と modifier が正しく設定される（必須、ユーザーID）"""
        # Arrange
        expected_creator_id = 42

        # Act
        from iot_app.models.device_inventory import DeviceInventoryMaster

        instance = DeviceInventoryMaster(
            **make_valid_inventory_kwargs(creator=expected_creator_id, modifier=expected_creator_id)
        )

        # Assert: creator が期待値と一致すること
        assert instance.creator == expected_creator_id
        # Assert: modifier が期待値と一致すること
        assert instance.modifier == expected_creator_id

    def test_minimum_required_fields_create_valid_instance(self):
        """2.1.2: 最小構成（必須項目のみ）でインスタンスが生成される"""
        # Arrange / Act
        from iot_app.models.device_inventory import DeviceInventoryMaster

        instance = DeviceInventoryMaster(**make_valid_inventory_kwargs())

        # Assert: インスタンスが生成されること
        assert instance is not None
        # Assert: delete_flag のデフォルト値が False であること
        assert instance.delete_flag is False


# ============================================================
# 2. InventoryStatusMaster
# 観点: 2.1 正常系処理（有効な入力データ）
# ============================================================

@pytest.mark.unit
class TestInventoryStatusMasterDefaults:
    """InventoryStatusMaster - デフォルト値・コンストラクタのテスト
    観点: 2.1.1 正常系処理（有効な入力データ）
    """

    def test_delete_flag_defaults_to_false(self):
        """2.1.1: delete_flag を指定しない場合、デフォルト値 False が設定される"""
        # Arrange / Act
        from iot_app.models.device_inventory import InventoryStatusMaster

        instance = InventoryStatusMaster(
            inventory_status_name='在庫中',
            creator=1,
            modifier=1,
        )

        # Assert: delete_flag のデフォルト値が False であること
        assert instance.delete_flag is False

    def test_inventory_status_name_is_set_correctly(self):
        """2.1.1: inventory_status_name が正しく設定される"""
        # Arrange
        expected_name = '出荷済み'

        # Act
        from iot_app.models.device_inventory import InventoryStatusMaster

        instance = InventoryStatusMaster(
            inventory_status_name=expected_name,
            creator=1,
            modifier=1,
        )

        # Assert: inventory_status_name が期待値と一致すること
        assert instance.inventory_status_name == expected_name

    def test_delete_flag_can_be_set_to_true(self):
        """2.1.1: delete_flag=True を指定した場合、True が設定される"""
        # Arrange / Act
        from iot_app.models.device_inventory import InventoryStatusMaster

        instance = InventoryStatusMaster(
            inventory_status_name='廃棄済み',
            creator=1,
            modifier=1,
            delete_flag=True,
        )

        # Assert: delete_flag が True であること
        assert instance.delete_flag is True


# ============================================================
# 3. DeviceMaster
# 観点: 2.1 正常系処理（有効な入力データ）
# ============================================================

@pytest.mark.unit
class TestDeviceMasterDefaults:
    """DeviceMaster - デフォルト値・コンストラクタのテスト
    観点: 2.1.1 正常系処理（有効な入力データ）

    NOTE: DeviceMaster は src/iot_app/models/device.py に定義されている
    """

    def test_delete_flag_defaults_to_false(self):
        """2.1.1: delete_flag を指定しない場合、デフォルト値 False が設定される"""
        # Arrange / Act
        from iot_app.models.device import DeviceMaster

        instance = DeviceMaster(
            device_uuid='DEV-UUID-001',
            organization_id=1,
            device_type_id=1,
            device_name='センサーA',
            device_model='MODEL-X100',
            device_inventory_id=100,
            creator=1,
            modifier=1
        )

        # Assert: delete_flag のデフォルト値が False であること
        assert instance.delete_flag is False

    def test_delete_flag_can_be_set_to_true(self):
        """2.1.1: delete_flag=True を指定した場合、True が設定される"""
        # Arrange / Act
        from iot_app.models.device import DeviceMaster

        instance = DeviceMaster(
            device_uuid='DEV-UUID-002',
            organization_id=1,
            device_type_id=1,
            device_name='センサーB',
            device_model='MODEL-X200',
            device_inventory_id=200,
            creator=1,
            modifier=1,
            delete_flag=True
        )

        # Assert: delete_flag が True であること
        assert instance.delete_flag is True

    def test_optional_fields_default_to_none(self):
        """2.1.2: 任意フィールド（sim_id, mac_address, software_version, device_location, certificate_expiration_date）
        を指定しない場合、None が設定される"""
        # Arrange / Act
        from iot_app.models.device import DeviceMaster

        instance = DeviceMaster(
            device_uuid='DEV-UUID-003',
            organization_id=1,
            device_type_id=1,
            device_name='センサーC',
            device_model='MODEL-X300',
            device_inventory_id=300,
            creator=1,
            modifier=1
        )

        # Assert: sim_id のデフォルト値が None であること
        assert instance.sim_id is None
        # Assert: mac_addressのデフォルト値が None であること
        assert instance.mac_address is None
        # Assert: software_version のデフォルト値が None であること
        assert instance.software_version is None
        # Assert: device_location のデフォルト値が None であること
        assert instance.device_location is None
        # Assert: certificate_expiration_date のデフォルト値が None であること
        assert instance.certificate_expiration_date is None

    def test_device_uuid_is_set_correctly(self):
        """2.1.1: device_uuid が正しく設定される（必須、最大128文字）"""
        # Arrange
        expected_uuid = 'MyDevice-UUID-12345'

        # Act
        from iot_app.models.device import DeviceMaster

        instance = DeviceMaster(
            device_uuid=expected_uuid,
            organization_id=1,
            device_type_id=1,
            device_name='テストデバイス',
            device_model='MODEL-TEST',
            device_inventory_id=1,
            creator=1,
            modifier=1,
        )

        # Assert: device_uuid が期待値と一致すること
        assert instance.device_uuid == expected_uuid

    def test_all_required_fields_set_on_init(self):
        """2.1.1: 必須フィールドがすべてコンストラクタで設定される"""
        # Arrange
        from iot_app.models.device import DeviceMaster

        device_uuid = 'FULL-UUID-001'
        device_type_id = 2
        device_name = 'フルデバイス'
        device_model = 'MODEL-FULL'
        device_inventory_id = 500
        organization_id = 10
        creator = 99
        modifier = 99

        # Act
        instance = DeviceMaster(
            device_uuid=device_uuid,
            organization_id=organization_id,
            device_type_id=device_type_id,
            device_name=device_name,
            device_model=device_model,
            device_inventory_id=device_inventory_id,
            creator=creator,
            modifier=modifier
        )

        # Assert: 各フィールドが期待値と一致すること
        assert instance.device_uuid == device_uuid
        assert instance.organization_id == organization_id
        assert instance.device_type_id == device_type_id
        assert instance.device_name == device_name
        assert instance.device_model == device_model
        assert instance.device_inventory_id == device_inventory_id
        assert instance.creator == creator
        assert instance.modifier == modifier
        assert instance.delete_flag is False


# ============================================================
# 4. DeviceTypeMaster
# 観点: 2.1 正常系処理（有効な入力データ）
# ============================================================

@pytest.mark.unit
class TestDeviceTypeMasterDefaults:
    """DeviceTypeMaster - デフォルト値・コンストラクタのテスト
    観点: 2.1.1 正常系処理（有効な入力データ）

    NOTE: DeviceTypeMaster は src/iot_app/models/device.py に定義されている
    """

    def test_delete_flag_defaults_to_false(self):
        """2.1.1: delete_flag を指定しない場合、デフォルト値 False が設定される"""
        # Arrange / Act
        from iot_app.models.device import DeviceTypeMaster

        instance = DeviceTypeMaster(
            device_type_name='センサー',
            creator=1,
            modifier=1,
        )

        # Assert: delete_flag のデフォルト値が False であること
        assert instance.delete_flag is False

    def test_device_type_name_is_set_correctly(self):
        """2.1.1: device_type_name が正しく設定される（必須、最大100文字）"""
        # Arrange
        expected_name = 'ゲートウェイ'

        # Act
        from iot_app.models.device import DeviceTypeMaster

        instance = DeviceTypeMaster(
            device_type_name=expected_name,
            creator=1,
            modifier=1,
        )

        # Assert: device_type_name が期待値と一致すること
        assert instance.device_type_name == expected_name

    def test_delete_flag_can_be_set_explicitly(self):
        """2.1.1: delete_flag=True を指定した場合、True が設定される"""
        # Arrange / Act
        from iot_app.models.device import DeviceTypeMaster

        instance = DeviceTypeMaster(
            device_type_name='廃止デバイス種別',
            creator=1,
            modifier=1,
            delete_flag=True,
        )

        # Assert: delete_flag が True であること
        assert instance.delete_flag is True
