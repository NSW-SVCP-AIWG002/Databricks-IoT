"""
デバイス台帳管理 - Service層 単体テスト

対象ファイル: src/iot_app/services/device_stock_service.py

参照ドキュメント:
  - UI設計書:       docs/03-features/flask-app/device-inventory/ui-specification.md
  - 機能設計書:     docs/03-features/flask-app/device-inventory/workflow-specification.md
  - 単体テスト観点表: docs/05-testing/unit-test/unit-test-perspectives.md
  - 実装ガイド:     docs/05-testing/unit-test/unit-test-guide.md
"""
import pytest
from unittest.mock import MagicMock, Mock, patch, call
from datetime import date


# ============================================================
# フィクスチャ
# ============================================================

@pytest.fixture
def mock_session():
    """DBセッションのモック"""
    return MagicMock()


@pytest.fixture
def service(mock_session):
    """DeviceStockService のインスタンス（DBセッションをモック化）"""
    from iot_app.services.device_stock_service import DeviceStockService
    return DeviceStockService(db_session=mock_session)


def make_valid_form_data(**overrides):
    """
    登録・更新フォームの有効データを生成するヘルパー。
    必須項目をすべて含む最小有効データをベースに、引数で任意項目を上書きできる。
    """
    data = {
        # device_master 登録フィールド
        "device_uuid": "DEV-001",                          # 必須, 最大128文字
        "device_name": "センサーA",                        # 必須, 最大100文字
        "device_type_id": 1,                               # 必須
        "device_model": "MODEL-X100",                      # 必須, 最大100文字
        "sim_id": None,                                    # 任意, 最大20文字
        "mac_address": "AA:BB:CC:DD:EE:FF",                # 必須, XX:XX:XX:XX:XX:XX形式
        "organization_id": 1,                              # 必須
        "software_version": None,                          # 任意, 最大100文字
        "device_location": None,                           # 任意, 最大100文字
        "certificate_expiration_date": None,               # 任意
        # device_inventory_master 登録フィールド
        "inventory_status_id": 1,                          # 任意
        "purchase_date": date(2025, 1, 15),                # 必須
        "estimated_ship_date": None,                       # 任意, 購入日以降
        "ship_date": None,                                 # 任意, 購入日以降
        "manufacturer_warranty_end_date": date(2026, 1, 15),  # 必須, 購入日以降
        "inventory_location": "倉庫A",                     # 必須, 最大100文字
        # 作成者
        "user_id": 1,
    }
    data.update(overrides)
    return data


def make_inventory_mock(**kwargs):
    """CSVエクスポートテスト用の在庫データモックを生成"""
    m = Mock()
    m.device = Mock()
    m.device.device_name = kwargs.get("device_name", "センサーA")
    m.device.device_type = Mock()
    m.device.device_type.device_type_name = kwargs.get("device_type_name", "センサー")
    m.device.device_model = kwargs.get("device_model", "MODEL-X100")
    m.device.sim_id = kwargs.get("sim_id", "SIM001")
    m.device.mac_address = kwargs.get("mac_address", "AA:BB:CC:DD:EE:FF")
    m.inventory_status = Mock()
    m.inventory_status.inventory_status_name = kwargs.get("inventory_status_name", "在庫中")
    m.purchase_date = kwargs.get("purchase_date", date(2025, 1, 15))
    m.estimated_ship_date = kwargs.get("estimated_ship_date", None)
    m.ship_date = kwargs.get("ship_date", None)
    m.manufacturer_warranty_end_date = kwargs.get("manufacturer_warranty_end_date", date(2026, 1, 15))
    m.inventory_location = kwargs.get("inventory_location", "倉庫A")
    return m


# ============================================================
# 1. 入力バリデーション
# 観点: 1.1.1 必須チェック, 1.1.2 最大文字列長チェック
# ============================================================

@pytest.mark.unit
class TestDeviceStockServiceValidation:
    """デバイス台帳登録・更新フォームバリデーション
    観点: 1.1.1 必須チェック, 1.1.2 最大文字列長チェック, 1.1.4 日付形式チェック
    """

    # ----------------------------------------------------------------
    # 1.1.1 必須チェック - device_uuid
    # ----------------------------------------------------------------

    def test_required_device_uuid_empty_raises(self, service):
        """1.1.1: device_uuid が空文字の場合 ValidationError がスローされる"""
        # Arrange
        data = make_valid_form_data(device_uuid="")
        # Act & Assert
        with pytest.raises(Exception):
            service.create(data)

    def test_required_device_uuid_none_raises(self, service):
        """1.1.2: device_uuid が None の場合 ValidationError がスローされる"""
        # Arrange
        data = make_valid_form_data(device_uuid=None)
        # Act & Assert
        with pytest.raises(Exception):
            service.create(data)

    # ----------------------------------------------------------------
    # 1.1.1 必須チェック - device_name
    # ----------------------------------------------------------------

    def test_required_device_name_empty_raises(self, service):
        """1.1.1: device_name が空文字の場合 ValidationError がスローされる"""
        # Arrange
        data = make_valid_form_data(device_name="")
        # Act & Assert
        with pytest.raises(Exception):
            service.create(data)

    def test_required_device_name_none_raises(self, service):
        """1.1.2: device_name が None の場合 ValidationError がスローされる"""
        # Arrange
        data = make_valid_form_data(device_name=None)
        # Act & Assert
        with pytest.raises(Exception):
            service.create(data)

    # ----------------------------------------------------------------
    # 1.1.1 必須チェック - その他必須項目
    # ----------------------------------------------------------------

    def test_required_device_type_id_none_raises(self, service):
        """1.1.2: device_type_id が None の場合 ValidationError がスローされる"""
        # Arrange
        data = make_valid_form_data(device_type_id=None)
        # Act & Assert
        with pytest.raises(Exception):
            service.create(data)

    def test_required_device_model_empty_raises(self, service):
        """1.1.1: device_model が空文字の場合 ValidationError がスローされる"""
        # Arrange
        data = make_valid_form_data(device_model="")
        # Act & Assert
        with pytest.raises(Exception):
            service.create(data)

    def test_required_mac_address_empty_raises(self, service):
        """1.1.1: mac_address が空文字の場合 ValidationError がスローされる"""
        # Arrange
        data = make_valid_form_data(mac_address="")
        # Act & Assert
        with pytest.raises(Exception):
            service.create(data)

    def test_required_organization_id_none_raises(self, service):
        """1.1.2: organization_id が None の場合 ValidationError がスローされる"""
        # Arrange
        data = make_valid_form_data(organization_id=None)
        # Act & Assert
        with pytest.raises(Exception):
            service.create(data)

    def test_required_purchase_date_none_raises(self, service):
        """1.1.2: purchase_date が None の場合 ValidationError がスローされる"""
        # Arrange
        data = make_valid_form_data(purchase_date=None)
        # Act & Assert
        with pytest.raises(Exception):
            service.create(data)

    def test_required_manufacturer_warranty_end_date_none_raises(self, service):
        """1.1.2: manufacturer_warranty_end_date が None の場合 ValidationError がスローされる"""
        # Arrange
        data = make_valid_form_data(manufacturer_warranty_end_date=None)
        # Act & Assert
        with pytest.raises(Exception):
            service.create(data)

    def test_required_inventory_location_empty_raises(self, service):
        """1.1.1: inventory_location が空文字の場合 ValidationError がスローされる"""
        # Arrange
        data = make_valid_form_data(inventory_location="")
        # Act & Assert
        with pytest.raises(Exception):
            service.create(data)

    # ----------------------------------------------------------------
    # 1.1.2 最大文字列長チェック - device_uuid (最大128文字)
    # ----------------------------------------------------------------

    def test_max_length_device_uuid_128_ok(self, service):
        """1.2.2: device_uuid が 128文字ちょうどはバリデーション通過"""
        # Arrange
        data = make_valid_form_data(device_uuid="a" * 128)
        # Act & Assert
        # ValidationError が起きないことを確認（DB操作はモックのため例外なし）
        # TODO: 実装完了後に検証

    def test_max_length_device_uuid_129_raises(self, service):
        """1.2.3: device_uuid が 129文字の場合 ValidationError がスローされる"""
        # Arrange
        data = make_valid_form_data(device_uuid="a" * 129)
        # Act & Assert
        with pytest.raises(Exception):
            service.create(data)

    # ----------------------------------------------------------------
    # 1.1.2 最大文字列長チェック - device_name (最大100文字)
    # ----------------------------------------------------------------

    def test_max_length_device_name_100_ok(self, service):
        """1.2.2: device_name が 100文字ちょうどはバリデーション通過"""
        # TODO: 実装完了後に検証

    def test_max_length_device_name_101_raises(self, service):
        """1.2.3: device_name が 101文字の場合 ValidationError がスローされる"""
        # Arrange
        data = make_valid_form_data(device_name="あ" * 101)
        # Act & Assert
        with pytest.raises(Exception):
            service.create(data)

    # ----------------------------------------------------------------
    # 1.1.2 最大文字列長チェック - device_model (最大100文字)
    # ----------------------------------------------------------------

    def test_max_length_device_model_101_raises(self, service):
        """1.2.3: device_model が 101文字の場合 ValidationError がスローされる"""
        # Arrange
        data = make_valid_form_data(device_model="a" * 101)
        # Act & Assert
        with pytest.raises(Exception):
            service.create(data)

    # ----------------------------------------------------------------
    # 1.1.2 最大文字列長チェック - sim_id (任意, 最大20文字)
    # ----------------------------------------------------------------

    def test_max_length_sim_id_20_ok(self, service):
        """1.2.2: sim_id が 20文字ちょうどはバリデーション通過（任意項目）"""
        # TODO: 実装完了後に検証

    def test_max_length_sim_id_21_raises(self, service):
        """1.2.3: sim_id が 21文字の場合 ValidationError がスローされる"""
        # Arrange
        data = make_valid_form_data(sim_id="a" * 21)
        # Act & Assert
        with pytest.raises(Exception):
            service.create(data)

    # ----------------------------------------------------------------
    # 1.1.2 最大文字列長チェック - software_version (任意, 最大100文字)
    # ----------------------------------------------------------------

    def test_max_length_software_version_101_raises(self, service):
        """1.2.3: software_version が 101文字の場合 ValidationError がスローされる"""
        # Arrange
        data = make_valid_form_data(software_version="a" * 101)
        # Act & Assert
        with pytest.raises(Exception):
            service.create(data)

    # ----------------------------------------------------------------
    # 1.1.2 最大文字列長チェック - device_location (任意, 最大100文字)
    # ----------------------------------------------------------------

    def test_max_length_device_location_101_raises(self, service):
        """1.2.3: device_location が 101文字の場合 ValidationError がスローされる"""
        # Arrange
        data = make_valid_form_data(device_location="a" * 101)
        # Act & Assert
        with pytest.raises(Exception):
            service.create(data)

    # ----------------------------------------------------------------
    # 1.1.2 最大文字列長チェック - inventory_location (必須, 最大100文字)
    # ----------------------------------------------------------------

    def test_max_length_inventory_location_101_raises(self, service):
        """1.2.3: inventory_location が 101文字の場合 ValidationError がスローされる"""
        # Arrange
        data = make_valid_form_data(inventory_location="a" * 101)
        # Act & Assert
        with pytest.raises(Exception):
            service.create(data)

    # ----------------------------------------------------------------
    # MACアドレス形式チェック (XX:XX:XX:XX:XX:XX)
    # ----------------------------------------------------------------

    def test_mac_address_invalid_no_colon_raises(self, service):
        """MACアドレス: コロンなし形式（AABBCCDDEEFF）の場合 ValidationError がスローされる"""
        # Arrange
        data = make_valid_form_data(mac_address="AABBCCDDEEFF")
        # Act & Assert
        with pytest.raises(Exception):
            service.create(data)

    def test_mac_address_invalid_short_raises(self, service):
        """MACアドレス: 17文字未満の場合 ValidationError がスローされる"""
        # Arrange
        data = make_valid_form_data(mac_address="AA:BB:CC:DD:EE")
        # Act & Assert
        with pytest.raises(Exception):
            service.create(data)

    def test_mac_address_invalid_long_raises(self, service):
        """MACアドレス: 17文字超過の場合 ValidationError がスローされる"""
        # Arrange
        data = make_valid_form_data(mac_address="XX:XX:XX:XX:XX:XX:XX")
        # Act & Assert
        with pytest.raises(Exception):
            service.create(data)

    def test_mac_address_invalid_slash_separator_raises(self, service):
        """MACアドレス: スラッシュ区切り形式の場合 ValidationError がスローされる"""
        # Arrange
        data = make_valid_form_data(mac_address="AA/BB/CC/DD/EE/FF")
        # Act & Assert
        with pytest.raises(Exception):
            service.create(data)

    # ----------------------------------------------------------------
    # 日付範囲チェック (出荷予定日/出荷日/保証終了日 >= 購入日)
    # ----------------------------------------------------------------

    def test_estimated_ship_date_before_purchase_date_raises(self, service):
        """1.1.4: 出荷予定日 < 購入日の場合 ValidationError がスローされる"""
        # Arrange
        data = make_valid_form_data(
            purchase_date=date(2025, 3, 1),
            estimated_ship_date=date(2025, 2, 28),
        )
        # Act & Assert
        with pytest.raises(Exception):
            service.create(data)

    def test_estimated_ship_date_equal_purchase_date_ok(self, service):
        """1.1.4: 出荷予定日 == 購入日は許容される"""
        # TODO: 実装完了後に検証（同日が許容されることを確認）

    def test_ship_date_before_purchase_date_raises(self, service):
        """1.1.4: 出荷日 < 購入日の場合 ValidationError がスローされる"""
        # Arrange
        data = make_valid_form_data(
            purchase_date=date(2025, 3, 1),
            ship_date=date(2025, 2, 28),
        )
        # Act & Assert
        with pytest.raises(Exception):
            service.create(data)

    def test_manufacturer_warranty_end_date_before_purchase_date_raises(self, service):
        """1.1.4: メーカー保証終了日 < 購入日の場合 ValidationError がスローされる"""
        # Arrange
        data = make_valid_form_data(
            purchase_date=date(2025, 3, 1),
            manufacturer_warranty_end_date=date(2025, 2, 28),
        )
        # Act & Assert
        with pytest.raises(Exception):
            service.create(data)

    def test_manufacturer_warranty_end_date_equal_purchase_date_ok(self, service):
        """1.1.4: メーカー保証終了日 == 購入日は許容される"""
        # TODO: 実装完了後に検証（同日が許容されることを確認）

    def test_estimated_ship_date_equal_purchase_date_ok(self, service):
        """1.4.3: スラッシュ区切り"""
        # Arrange
        data = make_valid_form_data(
            purchase_date=date(2025, 3, 1),
            manufacturer_warranty_end_date="2024/01/01",
        )
        # Act & Assert
        with pytest.raises(Exception):
            service.create(data)

    def test_estimated_ship_date_equal_purchase_date_ok(self, service):
        """1.4.5: 存在しない日付"""
        # Arrange
        data = make_valid_form_data(
            purchase_date=date(2025, 3, 1),
            manufacturer_warranty_end_date="2024-02-30",
        )
        # Act & Assert
        with pytest.raises(Exception):
            service.create(data)


    def test_estimated_ship_date_equal_purchase_date_ok(self, service):
        """1.4.6: うるう年"""
        # Arrange
        data = make_valid_form_data(
            purchase_date=date(2024, 2, 29),
            manufacturer_warranty_end_date=date(2024, 2, 29),
        )
        # Act & Assert
        with pytest.raises(Exception):
            service.create(data)
        # TODO: 実装完了後に検証（同日が許容されることを確認）

    def test_estimated_ship_date_equal_purchase_date_ok(self, service):
        """1.4.7: うるう年"""
        # Arrange
        data = make_valid_form_data(
            purchase_date=date(2023, 2, 29),
            manufacturer_warranty_end_date=date(2023, 2, 29),
        )
        # Act & Assert
        with pytest.raises(Exception):
            service.create(data)

# ============================================================
# 2. CRUD共通テスト
# 観点: 2.1 正常系処理, 2.2 対象データ存在チェック, 2.3 副作用チェック
# ============================================================

@pytest.mark.unit
class TestDeviceStockServiceCrud:
    """デバイス台帳 CRUD共通
    観点: 2.1 正常系処理, 2.2 対象データ存在チェック, 2.3 副作用チェック
    """

    # ----------------------------------------------------------------
    # 2.2 対象データ存在チェック
    # ----------------------------------------------------------------

    def test_get_nonexistent_uuid_raises(self, service):
        """2.2.2: 存在しない UUID で get() を呼ぶと NotFoundError がスローされる"""
        # Arrange
        with patch.object(service, '_get_inventory_by_uuid', return_value=None):
            # Act & Assert
            with pytest.raises(Exception):
                service.get("nonexistent-uuid")

    def test_get_logically_deleted_raises(self, service):
        """2.2.3: 論理削除済みデータは NotFoundError がスローされる"""
        # Arrange
        deleted_mock = Mock()
        deleted_mock.delete_flag = True
        with patch.object(service, '_get_inventory_by_uuid', return_value=deleted_mock):
            # Act & Assert
            with pytest.raises(Exception):
                service.get("deleted-uuid")

    def test_get_existing_returns_data(self, service):
        """2.2.1: 存在する UUID で get() は正常に処理される"""
        # Arrange
        inventory_mock = Mock()
        inventory_mock.delete_flag = False
        with patch.object(service, '_get_inventory_by_uuid', return_value=inventory_mock):
            # Act
            result = service.get("existing-uuid")
            # Assert
            assert result is not None

    # ----------------------------------------------------------------
    # 2.3 副作用チェック - rollback
    # ----------------------------------------------------------------

    def test_rollback_called_on_create_exception(self, mock_session, service):
        """2.3.2: 登録処理で例外発生時に rollback() が呼び出される"""
        # Arrange
        mock_session.add.side_effect = Exception("DB connection error")
        data = make_valid_form_data()
        # Act
        with pytest.raises(Exception):
            service.create(data)
        # Assert
        mock_session.rollback.assert_called()

    def test_rollback_called_on_update_exception(self, mock_session, service):
        """2.3.2: 更新処理で例外発生時に rollback() が呼び出される"""
        # Arrange
        inventory_mock = Mock()
        inventory_mock.delete_flag = False
        inventory_mock.device_inventory_id = 1
        device_mock = Mock()
        device_mock.delete_flag = False
        mock_session.commit.side_effect = Exception("DB error")

        with patch.object(service, '_get_inventory_by_uuid', return_value=inventory_mock), \
             patch.object(service, '_get_device_by_inventory_id', return_value=device_mock):
            # Act
            with pytest.raises(Exception):
                service.update("test-uuid", make_valid_form_data())
            # Assert
            mock_session.rollback.assert_called()

    def test_rollback_called_on_delete_exception(self, mock_session, service):
        """2.3.2: 削除処理で例外発生時に rollback() が呼び出される"""
        # Arrange
        inventory_mock = Mock()
        inventory_mock.delete_flag = False
        inventory_mock.device_inventory_id = 1
        mock_session.commit.side_effect = Exception("DB error")

        with patch.object(service, '_get_inventories_by_uuids', return_value=[inventory_mock]):
            # Act
            with pytest.raises(Exception):
                service.delete(["test-uuid"])
            # Assert
            mock_session.rollback.assert_called()

    def test_no_data_change_when_validation_fails(self, mock_session, service):
        """2.3.1: バリデーションエラー時はデータが更新されない（DB操作が呼ばれない）"""
        # Arrange
        data = make_valid_form_data(device_uuid="")  # 必須項目が空
        # Act
        with pytest.raises(Exception):
            service.create(data)
        # Assert: add/commit が呼ばれていない
        mock_session.add.assert_not_called()
        mock_session.commit.assert_not_called()


# ============================================================
# 3.1 検索機能（Read）
# 観点: 3.1.1 検索条件指定, 3.1.2 条件未指定, 3.1.3 ページング, 3.1.4 戻り値
# ============================================================

@pytest.mark.unit
class TestDeviceStockServiceSearch:
    """デバイス台帳検索機能
    観点: 3.1.1 検索条件指定, 3.1.2 条件未指定, 3.1.3 ページング・件数制御, 3.1.4 戻り値
    """

    def _setup_mock_query(self, mock_query, total=0, items=None):
        """検索クエリモックのセットアップ共通処理"""
        if items is None:
            items = []
        mock_query.return_value.count.return_value = total
        mock_query.return_value.order_by.return_value.limit.return_value.offset.return_value.all.return_value = items
        return mock_query

    # ----------------------------------------------------------------
    # 3.1.1 検索条件指定
    # ----------------------------------------------------------------

    def test_search_with_device_uuid_calls_query(self, service):
        """3.1.1.1: device_uuid 指定時に検索条件が Repository に渡される"""
        # Arrange & Act
        with patch.object(service, '_build_query') as mock_build:
            self._setup_mock_query(mock_build)
            service.search(device_uuid="DEV-001")
            # Assert
            mock_build.assert_called_once()
            _, kwargs = mock_build.call_args
            assert kwargs.get("device_uuid") == "DEV-001"

    def test_search_with_device_name_calls_query(self, service):
        """3.1.1.1: device_name 指定時に検索条件が Repository に渡される"""
        # Arrange & Act
        with patch.object(service, '_build_query') as mock_build:
            self._setup_mock_query(mock_build)
            service.search(device_name="センサー")
            # Assert
            _, kwargs = mock_build.call_args
            assert kwargs.get("device_name") == "センサー"

    def test_search_with_multiple_conditions(self, service):
        """3.1.1.2: 複数条件指定時に全条件が欠落なく渡される"""
        # Arrange & Act
        with patch.object(service, '_build_query') as mock_build:
            self._setup_mock_query(mock_build)
            service.search(
                device_uuid="DEV-001",
                device_name="センサー",
                device_type_id=1,
                inventory_status_id=1,
                inventory_location="倉庫A",
                purchase_date_from=date(2025, 1, 1),
                purchase_date_to=date(2025, 12, 31),
            )
            # Assert
            _, kwargs = mock_build.call_args
            assert kwargs.get("device_uuid") == "DEV-001"
            assert kwargs.get("device_name") == "センサー"
            assert kwargs.get("device_type_id") == 1

    def test_search_partial_conditions_none_excluded(self, service):
        """3.1.1.3: 一部条件のみ指定した場合、未指定条件は None または除外される"""
        # Arrange & Act
        with patch.object(service, '_build_query') as mock_build:
            self._setup_mock_query(mock_build)
            service.search(device_name="センサー")
            # Assert
            _, kwargs = mock_build.call_args
            # 未指定の device_uuid は None または含まれない
            assert kwargs.get("device_uuid") is None or "device_uuid" not in kwargs

    # ----------------------------------------------------------------
    # 3.1.2 検索条件未指定（全件相当）
    # ----------------------------------------------------------------

    def test_search_no_conditions_returns_all(self, service):
        """3.1.2.1: 検索条件なしの場合、条件なし（全件相当）で Repository が呼ばれる"""
        # Arrange
        with patch.object(service, '_build_query') as mock_build:
            mock_items = [Mock() for _ in range(5)]
            self._setup_mock_query(mock_build, total=5, items=mock_items)
            # Act
            result = service.search()
            # Assert: _build_query が呼ばれている
            mock_build.assert_called_once()

    # ----------------------------------------------------------------
    # 3.1.3 ページング・件数制御
    # ----------------------------------------------------------------

    def test_search_pagination_offset_calculated_correctly(self, service):
        """3.1.3.1: page=2, per_page=25 の場合 offset=25 でクエリが発行される"""
        # Arrange
        with patch.object(service, '_build_query') as mock_build:
            self._setup_mock_query(mock_build, total=100, items=[Mock()] * 25)
            # Act
            service.search(page=2, per_page=25)
            # Assert
            query_chain = mock_build.return_value.order_by.return_value
            query_chain.limit.assert_called_with(25)
            query_chain.limit.return_value.offset.assert_called_with(25)  # (2-1)*25

    def test_search_page1_offset_is_zero(self, service):
        """3.1.3.1: page=1 の場合 offset=0 でクエリが発行される"""
        # Arrange
        with patch.object(service, '_build_query') as mock_build:
            self._setup_mock_query(mock_build, total=10, items=[Mock()] * 10)
            # Act
            service.search(page=1, per_page=25)
            # Assert
            query_chain = mock_build.return_value.order_by.return_value
            query_chain.limit.return_value.offset.assert_called_with(0)

    # ----------------------------------------------------------------
    # 3.1.4 検索結果戻り値ハンドリング
    # ----------------------------------------------------------------

    def test_search_returns_list_from_repository(self, service):
        """3.1.4.1: Repository がリストを返却した場合、そのまま返却される"""
        # Arrange
        mock_items = [Mock(), Mock(), Mock()]
        with patch.object(service, '_build_query') as mock_build:
            self._setup_mock_query(mock_build, total=3, items=mock_items)
            # Act
            items, total = service.search()
            # Assert
            assert items == mock_items
            assert total == 3

    def test_search_returns_empty_list_when_no_results(self, service):
        """3.1.4.2: Repository が空リストを返却した場合、空リストが返却される"""
        # Arrange
        with patch.object(service, '_build_query') as mock_build:
            self._setup_mock_query(mock_build, total=0, items=[])
            # Act
            items, total = service.search()
            # Assert
            assert items == []
            assert total == 0


# ============================================================
# 3.2 登録機能
# 観点: 3.2.1 登録処理呼び出し, 3.2.2 登録結果
# ============================================================

@pytest.mark.unit
class TestDeviceStockServiceCreate:
    """デバイス台帳登録機能
    観点: 3.2.1 登録処理呼び出し, 3.2.2 登録結果, 2.1 正常系処理
    """

    # ----------------------------------------------------------------
    # 3.2.1 登録処理呼び出し
    # ----------------------------------------------------------------

    def test_create_calls_db_add_twice(self, mock_session, service):
        """3.2.1.1: 正常な入力値で device_inventory_master と device_master の両方に add が呼ばれる"""
        # Arrange
        data = make_valid_form_data()
        mock_session.flush.return_value = None
        mock_session.commit.return_value = None
        # Act
        service.create(data)
        # Assert: 2テーブル分のINSERT
        assert mock_session.add.call_count == 2

    def test_create_with_none_optional_fields(self, mock_session, service):
        """3.2.1.2: None を含む入力値でも Repository に渡される（任意項目が None）"""
        # Arrange
        data = make_valid_form_data(sim_id=None, software_version=None, device_location=None)
        mock_session.flush.return_value = None
        mock_session.commit.return_value = None
        # Act
        service.create(data)  # 例外が発生しないことを確認
        # Assert
        assert mock_session.add.call_count == 2

    def test_create_validation_error_does_not_call_add(self, mock_session, service):
        """3.2.1.3: バリデーションエラー発生時は Repository（add）は呼び出されない"""
        # Arrange
        data = make_valid_form_data(device_uuid="")  # 必須項目が空
        # Act
        with pytest.raises(Exception):
            service.create(data)
        # Assert
        mock_session.add.assert_not_called()

    # ----------------------------------------------------------------
    # 3.2.2 登録結果
    # ----------------------------------------------------------------

    def test_create_calls_commit_on_success(self, mock_session, service):
        """3.2.2.1: 登録処理成功時に commit が呼ばれる"""
        # Arrange
        data = make_valid_form_data()
        mock_session.flush.return_value = None
        mock_session.commit.return_value = None
        # Act
        service.create(data)
        # Assert
        mock_session.commit.assert_called_once()

    def test_create_calls_flush_before_commit(self, mock_session, service):
        """登録時に flush → commit の順序で呼ばれる（device_inventory_id を device_master に渡すため）"""
        # Arrange
        data = make_valid_form_data()
        call_order = []
        mock_session.flush.side_effect = lambda: call_order.append("flush")
        mock_session.commit.side_effect = lambda: call_order.append("commit")
        # Act
        service.create(data)
        # Assert
        assert call_order.index("flush") < call_order.index("commit")

    def test_create_mac_address_stored_without_conversion(self, mock_session, service):
        """登録時 mac_address は XX:XX:XX:XX:XX:XX 形式のまま格納される（変換しない）"""
        # Arrange
        data = make_valid_form_data(mac_address="AA:BB:CC:DD:EE:FF")
        mock_session.flush.return_value = None
        mock_session.commit.return_value = None
        # Act
        service.create(data)
        # Assert: add に渡されたオブジェクトの mac_address が変換されていない
        added_objects = [c[0][0] for c in mock_session.add.call_args_list]
        mac_values = [
            getattr(obj, "mac_address", None)
            for obj in added_objects
            if hasattr(obj, "mac_address")
        ]
        assert all(mac == "AA:BB:CC:DD:EE:FF" for mac in mac_values)


# ============================================================
# 3.3 更新機能（Update）
# 観点: 3.3.1 更新処理呼び出し, 3.3.2 更新結果
# ============================================================

@pytest.mark.unit
class TestDeviceStockServiceUpdate:
    """デバイス台帳更新機能
    観点: 3.3.1 更新処理呼び出し, 3.3.2 更新結果
    """

    def _setup_update_mocks(self, service):
        """更新テスト用モックセットアップ"""
        inventory_mock = Mock()
        inventory_mock.delete_flag = False
        inventory_mock.device_inventory_id = 1
        device_mock = Mock()
        device_mock.delete_flag = False
        return inventory_mock, device_mock

    # ----------------------------------------------------------------
    # 3.3.1 更新処理呼び出し
    # ----------------------------------------------------------------

    def test_update_passes_id_and_data_to_repository(self, mock_session, service):
        """3.3.1.1: 正常な入力値で更新対象IDと更新内容が Repository に渡される"""
        # Arrange
        inventory_mock, device_mock = self._setup_update_mocks(service)
        data = make_valid_form_data(device_name="更新後デバイス名", inventory_location="倉庫B")
        mock_session.commit.return_value = None

        with patch.object(service, '_get_inventory_by_uuid', return_value=inventory_mock), \
             patch.object(service, '_get_device_by_inventory_id', return_value=device_mock):
            # Act
            service.update("test-uuid", data)
            # Assert: モックオブジェクトのフィールドが更新されている
            assert device_mock.device_name == "更新後デバイス名"
            assert inventory_mock.inventory_location == "倉庫B"

    def test_update_with_none_optional_fields(self, mock_session, service):
        """3.3.1.2: None を含む入力値でも Repository に渡される"""
        # Arrange
        inventory_mock, device_mock = self._setup_update_mocks(service)
        data = make_valid_form_data(sim_id=None, estimated_ship_date=None)
        mock_session.commit.return_value = None

        with patch.object(service, '_get_inventory_by_uuid', return_value=inventory_mock), \
             patch.object(service, '_get_device_by_inventory_id', return_value=device_mock):
            # Act
            service.update("test-uuid", data)  # 例外なし
            # Assert
            mock_session.commit.assert_called_once()

    def test_update_validation_error_does_not_call_commit(self, mock_session, service):
        """3.3.1.3: バリデーションエラー発生時は Repository（commit）は呼び出されない"""
        # Arrange
        data = make_valid_form_data(device_uuid="")
        # Act
        with pytest.raises(Exception):
            service.update("test-uuid", data)
        # Assert
        mock_session.commit.assert_not_called()

    def test_update_not_found_raises(self, service):
        """2.2.2: 存在しない UUID で更新しようとした場合 NotFoundError がスローされる"""
        # Arrange
        with patch.object(service, '_get_inventory_by_uuid', return_value=None):
            # Act & Assert
            with pytest.raises(Exception):
                service.update("nonexistent-uuid", make_valid_form_data())

    def test_get_logically_deleted_raises(self, service):
        """2.2.3: 論理削除済みデータは NotFoundError がスローされる"""
        # Arrange
        with patch.object(service, '_get_inventory_by_uuid', return_value="nonexistent-uuid"):
            # Act & Assert
            with pytest.raises(Exception):
                service.update("nonexistent-uuid", make_valid_form_data())

    # ----------------------------------------------------------------
    # 3.3.2 更新結果
    # ----------------------------------------------------------------

    def test_update_success_calls_commit(self, mock_session, service):
        """3.3.2.1: 更新処理成功時に例外なく処理が完了し commit が呼ばれる"""
        # Arrange
        inventory_mock, device_mock = self._setup_update_mocks(service)
        mock_session.commit.return_value = None

        with patch.object(service, '_get_inventory_by_uuid', return_value=inventory_mock), \
             patch.object(service, '_get_device_by_inventory_id', return_value=device_mock):
            # Act
            service.update("test-uuid", make_valid_form_data())
            # Assert
            mock_session.commit.assert_called_once()

    def test_update_updates_both_tables(self, mock_session, service):
        """3.3.1.1: device_inventory_master と device_master の両テーブルが更新される"""
        # Arrange
        inventory_mock, device_mock = self._setup_update_mocks(service)
        data = make_valid_form_data(
            device_name="新デバイス名",
            inventory_location="新倉庫",
            mac_address="FF:EE:DD:CC:BB:AA",
        )
        mock_session.commit.return_value = None

        with patch.object(service, '_get_inventory_by_uuid', return_value=inventory_mock), \
             patch.object(service, '_get_device_by_inventory_id', return_value=device_mock):
            # Act
            service.update("test-uuid", data)
            # Assert: 両テーブルのフィールドが更新されている
            assert device_mock.device_name == "新デバイス名"
            assert inventory_mock.inventory_location == "新倉庫"


# ============================================================
# 3.4 削除機能（論理削除）
# 観点: 3.4.1 削除処理呼び出し, 3.4.2 削除結果
# ============================================================

@pytest.mark.unit
class TestDeviceStockServiceDelete:
    """デバイス台帳削除機能（論理削除）
    観点: 3.4.1 削除処理呼び出し, 3.4.2 削除結果
    """

    # ----------------------------------------------------------------
    # 3.4.1 削除処理呼び出し
    # ----------------------------------------------------------------

    def test_delete_passes_uuid_to_repository(self, mock_session, service):
        """3.4.1.1: 指定した UUID が Repository に渡される"""
        # Arrange
        inventory_mock = Mock()
        inventory_mock.delete_flag = False
        inventory_mock.device_inventory_id = 1
        device_mock = Mock()
        device_mock.delete_flag = False
        mock_session.commit.return_value = None

        with patch.object(service, '_get_inventories_by_uuids', return_value=[inventory_mock]) as mock_get, \
             patch.object(service, '_get_devices_by_inventory_ids', return_value=[device_mock]):
            # Act
            service.delete(["target-uuid"])
            # Assert
            mock_get.assert_called_once_with(["target-uuid"])

    def test_delete_empty_uuids_raises(self, service):
        """3.4.1.2: 空リストで削除しようとした場合 ValidationError がスローされる"""
        # Arrange & Act & Assert
        with pytest.raises(Exception):
            service.delete([])

    # ----------------------------------------------------------------
    # 3.4.2 削除結果
    # ----------------------------------------------------------------

    def test_delete_sets_delete_flag_true_on_inventory(self, mock_session, service):
        """3.4.2.1: device_inventory_master の delete_flag が TRUE に設定される"""
        # Arrange
        inventory_mock = Mock()
        inventory_mock.delete_flag = False
        inventory_mock.device_inventory_id = 1
        device_mock = Mock()
        device_mock.delete_flag = False
        mock_session.commit.return_value = None

        with patch.object(service, '_get_inventories_by_uuids', return_value=[inventory_mock]), \
             patch.object(service, '_get_devices_by_inventory_ids', return_value=[device_mock]):
            # Act
            service.delete(["test-uuid"])
            # Assert
            assert inventory_mock.delete_flag is True

    def test_delete_sets_delete_flag_true_on_device(self, mock_session, service):
        """3.4.2.1: device_master の delete_flag も TRUE に設定される"""
        # Arrange
        inventory_mock = Mock()
        inventory_mock.delete_flag = False
        inventory_mock.device_inventory_id = 1
        device_mock = Mock()
        device_mock.delete_flag = False
        mock_session.commit.return_value = None

        with patch.object(service, '_get_inventories_by_uuids', return_value=[inventory_mock]), \
             patch.object(service, '_get_devices_by_inventory_ids', return_value=[device_mock]):
            # Act
            service.delete(["test-uuid"])
            # Assert
            assert device_mock.delete_flag is True

    def test_delete_not_found_raises(self, service):
        """2.2.2: 存在しない UUID を削除しようとした場合 NotFoundError がスローされる"""
        # Arrange
        with patch.object(service, '_get_inventories_by_uuids', return_value=[]):
            # Act & Assert
            with pytest.raises(Exception):
                service.delete(["nonexistent-uuid"])

    def test_delete_not_found_raises(self, service):
        """2.2.2: 存在しない UUID を削除しようとした場合 NotFoundError がスローされる"""
        """       3件中1件不一致"""
        # TODO
        # Arrange
        inventories = [Mock(delete_flag=False, device_inventory_id=i) for i in range(3)]
        devices = [Mock(delete_flag=False) for _ in range(3)]
        mock_session.commit.return_value = None

        with patch.object(service, '_get_inventories_by_uuids', return_value=inventories), \
             patch.object(service, '_get_devices_by_inventory_ids', return_value=devices):
            # Act
            service.delete(["uuid-1", "none", "uuid-3"])
            # Assert
            with pytest.raises(Exception):
                service.delete(["nonexistent-uuid"])

    def test_delete_multiple_uuids_all_logically_deleted(self, mock_session, service):
        """3.4.2.2: 複数 UUID 指定時に全件の delete_flag が TRUE になる"""
        # Arrange
        inventories = [Mock(delete_flag=False, device_inventory_id=i) for i in range(3)]
        devices = [Mock(delete_flag=False) for _ in range(3)]
        mock_session.commit.return_value = None

        with patch.object(service, '_get_inventories_by_uuids', return_value=inventories), \
             patch.object(service, '_get_devices_by_inventory_ids', return_value=devices):
            # Act
            service.delete(["uuid-1", "uuid-2", "uuid-3"])
            # Assert
            assert all(inv.delete_flag is True for inv in inventories)
            assert all(dev.delete_flag is True for dev in devices)

    def test_delete_calls_commit_on_success(self, mock_session, service):
        """3.4.2.1: 削除処理成功時に commit が呼ばれる"""
        # Arrange
        inventory_mock = Mock()
        inventory_mock.delete_flag = False
        inventory_mock.device_inventory_id = 1
        device_mock = Mock()
        device_mock.delete_flag = False
        mock_session.commit.return_value = None

        with patch.object(service, '_get_inventories_by_uuids', return_value=[inventory_mock]), \
             patch.object(service, '_get_devices_by_inventory_ids', return_value=[device_mock]):
            # Act
            service.delete(["test-uuid"])
            # Assert
            mock_session.commit.assert_called_once()


# ============================================================
# 3.5 CSVエクスポート機能
# 観点: 3.5.1 CSV生成ロジック, 3.5.2 エスケープ処理, 3.5.3 エンコーディング処理
# ============================================================

@pytest.mark.unit
class TestDeviceStockServiceCsvExport:
    """デバイス台帳 CSVエクスポート機能
    観点: 3.5.1 CSV生成ロジック, 3.5.2 エスケープ処理, 3.5.3 エンコーディング処理

    CSVカラム定義（workflow-specification.md より）:
    デバイス名, デバイス種別, モデル情報, SIMID, MACアドレス, 在庫状況,
    購入日, 出荷予定日, 出荷日, メーカー保証終了日, 在庫場所
    """

    # ----------------------------------------------------------------
    # 3.5.1 CSV生成ロジック
    # ----------------------------------------------------------------

    def test_csv_header_contains_all_columns(self, service):
        """3.5.1.1: 定義された列名がすべてヘッダー行に出力される"""
        # Arrange
        data = [make_inventory_mock()]
        # Act
        csv_output = service.export_csv(data)
        # Assert: 設計書で定義された全列名が含まれる
        assert "デバイス名" in csv_output
        assert "デバイス種別" in csv_output
        assert "モデル情報" in csv_output
        assert "SIMID" in csv_output
        assert "MACアドレス" in csv_output
        assert "在庫状況" in csv_output
        assert "購入日" in csv_output
        assert "出荷予定日" in csv_output
        assert "出荷日" in csv_output
        assert "メーカー保証終了日" in csv_output
        assert "在庫場所" in csv_output

    def test_csv_data_rows_all_items_output(self, service):
        """3.5.1.2: 複数件のデータリストを渡した場合、全件がCSV行として出力される"""
        # Arrange
        data = [make_inventory_mock(device_name=f"デバイス{i}") for i in range(3)]
        # Act
        csv_output = service.export_csv(data)
        # Assert
        for i in range(3):
            assert f"デバイス{i}" in csv_output

    def test_csv_empty_data_outputs_header_only(self, service):
        """3.5.1.3: 空リストを渡した場合、ヘッダー行のみ出力される"""
        # Arrange & Act
        csv_output = service.export_csv([])
        # Assert
        lines = [l for l in csv_output.strip().split("\n") if l.strip()]
        assert len(lines) == 1  # ヘッダー行のみ

    def test_csv_column_order_matches_specification(self, service):
        """3.5.1.4: 列の出力順が設計書の定義と一致する"""
        # Arrange
        data = [make_inventory_mock()]
        # Act
        csv_output = service.export_csv(data)
        header_line = csv_output.split("\n")[0]
        # Assert: ヘッダーの順序確認
        columns = ["デバイス名", "デバイス種別", "モデル情報", "SIMID", "MACアドレス",
                   "在庫状況", "購入日", "出荷予定日", "出荷日", "メーカー保証終了日", "在庫場所"]
        positions = [header_line.index(col) for col in columns if col in header_line]
        assert positions == sorted(positions)

    # ----------------------------------------------------------------
    # 3.5.2 エスケープ処理
    # ----------------------------------------------------------------

    def test_csv_escape_comma_in_data(self, service):
        """3.5.2.1: データにカンマを含む場合、ダブルクォートで囲まれる"""
        # Arrange
        data = [make_inventory_mock(device_name="センサー,A")]
        # Act
        csv_output = service.export_csv(data)
        # Assert
        assert '"センサー,A"' in csv_output

    def test_csv_escape_newline_in_data(self, service):
        """3.5.2.2: データに改行を含む場合、ダブルクォートで囲まれる"""
        # Arrange
        data = [make_inventory_mock(device_name="センサー\nA")]
        # Act
        csv_output = service.export_csv(data)
        # Assert
        assert '"センサー\nA"' in csv_output or '"センサーA"' in csv_output

    def test_csv_escape_double_quote_in_data(self, service):
        """3.5.2.3: データにダブルクォートを含む場合、\"\"でエスケープされる"""
        # Arrange
        data = [make_inventory_mock(device_name='センサー"A')]
        # Act
        csv_output = service.export_csv(data)
        # Assert
        assert '""' in csv_output

    def test_csv_no_escape_for_plain_data(self, service):
        """3.5.2.4: 特殊文字を含まないデータはそのまま出力される"""
        # Arrange
        data = [make_inventory_mock(device_name="センサーA")]
        # Act
        csv_output = service.export_csv(data)
        # Assert
        assert "センサーA" in csv_output

    # ----------------------------------------------------------------
    # 3.5.3 エンコーディング処理
    # ----------------------------------------------------------------

    def test_csv_bytes_has_utf8_bom(self, service):
        """3.5.3.1: CSV先頭に UTF-8 BOM（0xEF 0xBB 0xBF）が付与される"""
        # Arrange
        data = [make_inventory_mock()]
        # Act
        csv_bytes = service.export_csv_bytes(data)
        # Assert
        assert csv_bytes.startswith(b'\xef\xbb\xbf')

    def test_csv_japanese_data_no_garbling(self, service):
        """3.5.3.2: 日本語データを含む場合、文字化けなく正しく出力される"""
        # Arrange
        data = [make_inventory_mock(device_name="センサー日本語テスト", inventory_location="東京倉庫")]
        # Act
        csv_bytes = service.export_csv_bytes(data)
        csv_str = csv_bytes.decode("utf-8-sig")
        # Assert
        assert "センサー日本語テスト" in csv_str
        assert "東京倉庫" in csv_str

    def test_csv_date_format_is_yyyy_mm_dd(self, service):
        """購入日が YYYY/MM/DD 形式で出力される（設計書準拠）"""
        # Arrange
        data = [make_inventory_mock(purchase_date=date(2025, 1, 15))]
        # Act
        csv_output = service.export_csv(data)
        # Assert
        assert "2025/01/15" in csv_output

    def test_csv_none_date_output_as_empty(self, service):
        """日付が None の場合、空文字として出力される"""
        # Arrange
        data = [make_inventory_mock(estimated_ship_date=None, ship_date=None)]
        # Act
        csv_output = service.export_csv(data)
        # Assert: 空文字部分が存在する（エラーが起きない）
        assert csv_output is not None
        # TODO: 設計書に空文字の明示記載なし、要確認（空文字 or '-'）
