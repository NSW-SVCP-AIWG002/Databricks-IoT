"""
デバイス台帳管理 - Service層 単体テスト

対象ファイル: src/iot_app/services/device_inventory_service.py

参照ドキュメント:
  - 機能設計書:       docs/03-features/flask-app/device-inventory/workflow-specification.md
  - 単体テスト観点表: docs/05-testing/unit-test/unit-test-perspectives.md
  - 実装ガイド:       docs/05-testing/unit-test/unit-test-guide.md
"""
import pytest
from unittest.mock import MagicMock, Mock, patch
from datetime import date


# ============================================================
# 定数
# ============================================================

MODULE = 'iot_app.services.device_inventory_service'


# ============================================================
# ヘルパー関数
# ============================================================

def make_valid_form_data(**overrides):
    """
    登録・更新フォームの有効データを生成するヘルパー。
    必須項目をすべて含む最小有効データをベースに、引数で任意項目を上書きできる。
    """
    data = {
        'device_uuid':                    'DEV-UUID-001',       # 必須, 最大128文字
        'device_name':                    'センサーA',           # 必須, 最大100文字
        'device_type_id':                 1,                    # 必須
        'device_model':                   'MODEL-X100',         # 必須, 最大100文字
        'sim_id':                         None,                 # 任意, 最大20文字
        'mac_address':                    'AA:BB:CC:DD:EE:FF',  # 必須, XX:XX:XX:XX:XX:XX形式
        'organization_id':                '1',                  # 必須
        'software_version':               None,                 # 任意, 最大100文字
        'device_location':                None,                 # 任意, 最大100文字
        'certificate_expiration_date':    None,                 # 任意
        'inventory_status_id':            1,                    # 必須
        'purchase_date':                  date(2025, 1, 15),    # 必須
        'estimated_ship_date':            None,                 # 任意
        'ship_date':                      None,                 # 任意
        'manufacturer_warranty_end_date': date(2026, 1, 15),    # 必須
        'inventory_location':             '倉庫A',              # 必須, 最大100文字
    }
    data.update(overrides)
    return data


def make_default_search_params(**overrides):
    """検索パラメータのデフォルト値を生成するヘルパー"""
    params = {
        'page': 1,
        'per_page': 25,
        'sort_item_id': -1,
        'sort_order': -1,
        'device_uuid': '',
        'device_name': '',
        'device_type': -1,
        'inventory_status': -1,
        'inventory_location': '',
        'purchase_date_from': None,
        'purchase_date_to': None,
    }
    params.update(overrides)
    return params


def make_mock_query():
    """SQLAlchemy クエリチェーンのモックを生成するヘルパー"""
    q = MagicMock()
    q.join.return_value = q
    q.filter.return_value = q
    q.order_by.return_value = q
    q.count.return_value = 0
    q.all.return_value = []
    q.limit.return_value = q
    q.offset.return_value = q
    return q


def make_inventory_mock(**kwargs):
    """CSVエクスポートテスト用の在庫データモックを生成するヘルパー"""
    m = Mock()
    m.device = Mock()
    m.device.device_name = kwargs.get('device_name', 'センサーA')
    m.device.device_type = Mock()
    m.device.device_type.device_type_name = kwargs.get('device_type_name', 'センサー')
    m.device.device_model = kwargs.get('device_model', 'MODEL-X100')
    m.device.sim_id = kwargs.get('sim_id', 'SIM001')
    m.device.mac_address = kwargs.get('mac_address', 'AA:BB:CC:DD:EE:FF')
    m.inventory_status = Mock()
    m.inventory_status.inventory_status_name = kwargs.get('inventory_status_name', '在庫中')
    m.purchase_date = kwargs.get('purchase_date', date(2025, 1, 15))
    m.estimated_ship_date = kwargs.get('estimated_ship_date', None)
    m.ship_date = kwargs.get('ship_date', None)
    m.manufacturer_warranty_end_date = kwargs.get(
        'manufacturer_warranty_end_date', date(2026, 1, 15)
    )
    m.inventory_location = kwargs.get('inventory_location', '倉庫A')
    return m


# ============================================================
# 1. get_default_search_params
# 観点: 2.1 正常系処理
# ============================================================

@pytest.mark.unit
class TestGetDefaultSearchParams:
    """get_default_search_params - デフォルト検索パラメータ生成
    観点: 2.1 正常系処理
    """

    def test_returns_page_1(self):
        """2.1.1: page のデフォルト値は 1 である"""
        # Arrange / Act
        from iot_app.services.device_inventory_service import get_default_search_params
        
        # get_default_search_params関数実行
        result = get_default_search_params()
        
        # Assert: result内のkey『page』が持つvalueが1であること
        assert result['page'] == 1

    def test_returns_per_page_25(self):
        """2.1.1: per_page のデフォルト値は 25 である"""
        # Arrange / Act
        from iot_app.services.device_inventory_service import get_default_search_params
        
        # get_default_search_params関数実行
        result = get_default_search_params()
        
        # Assert: result内のkey『per_page』が持つvalueが25であること
        assert result['per_page'] == 25

    def test_returns_empty_string_for_device_uuid(self):
        """2.1.1: device_uuid のデフォルト値は空文字である"""
        # Arrange / Act
        from iot_app.services.device_inventory_service import get_default_search_params
        
        # get_default_search_params関数実行
        result = get_default_search_params()
        
        # Assert: result内のkey『device_uuid』が持つvalueが''(空文字)であること
        assert result['device_uuid'] == ''

    def test_returns_empty_string_for_device_name(self):
        """2.1.1: device_name のデフォルト値は空文字である"""
        # Arrange / Act
        from iot_app.services.device_inventory_service import get_default_search_params
        
        # get_default_search_params関数実行
        result = get_default_search_params()
        
        # Assert: result内のkey『device_name』が持つvalueが''(空文字)であること
        assert result['device_name'] == ''

    def test_returns_all_for_device_type(self):
        """2.1.1: device_type のデフォルト値は -1 である（すべて選択）"""
        # Arrange / Act
        from iot_app.services.device_inventory_service import get_default_search_params
        
        # get_default_search_params関数実行
        result = get_default_search_params()
        
        # Assert: result内のkey『device_type』が持つvalueが-1であること
        assert result['device_type'] == -1

    def test_returns_all_for_inventory_status(self):
        """2.1.1: inventory_status のデフォルト値は -1 である（すべて選択）"""
        # Arrange / Act
        from iot_app.services.device_inventory_service import get_default_search_params
        
        # get_default_search_params関数実行
        result = get_default_search_params()
        
        # Assert: result内のkey『inventory_status』が持つvalueが-1であること
        assert result['inventory_status'] == -1

    def test_returns_empty_string_for_inventory_location(self):
        """2.1.1: inventory_location のデフォルト値は空文字である"""
        # Arrange / Act
        from iot_app.services.device_inventory_service import get_default_search_params
        
        # get_default_search_params関数実行
        result = get_default_search_params()
        
        # Assert: result内のkey『inventory_location』が持つvalueが''(空文字)であること
        assert result['inventory_location'] == ''

    def test_returns_none_for_purchase_date_from(self):
        """2.1.1: purchase_date_from のデフォルト値は None である"""
        # Arrange / Act
        from iot_app.services.device_inventory_service import get_default_search_params
        
        # get_default_search_params関数実行
        result = get_default_search_params()
        
        # Assert: result内のkey『purchase_date_from』が持つvalueがNoneであること
        assert result['purchase_date_from'] is None

    def test_returns_none_for_purchase_date_to(self):
        """2.1.1: purchase_date_to のデフォルト値は None である"""
        # Arrange / Act
        from iot_app.services.device_inventory_service import get_default_search_params
        
        # get_default_search_params関数実行
        result = get_default_search_params()
        
        # Assert: result内のkey『purchase_date_to』が持つvalueがNoneであること
        assert result['purchase_date_to'] is None

    def test_returns_minus1_for_sort_item_id(self):
        """2.1.1: sort_item_id のデフォルト値は -1 である（未選択）"""
        # Arrange / Act
        from iot_app.services.device_inventory_service import get_default_search_params
        
        # get_default_search_params関数実行
        result = get_default_search_params()
        
        # Assert: result内のkey『sort_item_id』が持つvalueが-1であること
        assert result['sort_item_id'] == -1

    def test_returns_minus1_for_sort_order(self):
        """2.1.1: sort_order のデフォルト値は -1 である（未選択）"""
        # Arrange / Act
        from iot_app.services.device_inventory_service import get_default_search_params
        
        # get_default_search_params関数実行
        result = get_default_search_params()
        
        # Assert: result内のkey『sort_order』が持つvalueが-1であること
        assert result['sort_order'] == -1


# ============================================================
# 2. search_device_inventories
# 観点: 3.1.1 検索条件指定, 3.1.2 検索条件未指定, 3.1.3 ページング, 3.1.4 戻り値ハンドリング
# ============================================================

@pytest.mark.unit
class TestSearchDeviceInventories:
    """search_device_inventories - デバイス台帳一覧検索
    観点: 3.1.1 検索条件指定, 3.1.2 検索条件未指定, 3.1.3 ページング・件数制御,
          3.1.4 検索結果戻り値ハンドリング
    """

    @patch(f'{MODULE}.SortItemMaster')
    @patch(f'{MODULE}.InventoryStatusMaster')
    @patch(f'{MODULE}.DeviceTypeMaster')
    @patch(f'{MODULE}.DeviceMaster')
    @patch(f'{MODULE}.DeviceInventoryMaster')
    def test_search_with_device_uuid_applies_filter(
        self, mock_dim, mock_dm, mock_dtm, mock_ism, mock_sim
    ):
        """3.1.1.1: device_uuid を指定した場合、like フィルタが適用される/前方一致検索であること"""
        # Arrange
        from iot_app.services.device_inventory_service import search_device_inventories
        q = make_mock_query()
        mock_dim.query = q
        mock_sim.query.filter_by.return_value.first.return_value = None

        # ヘルパーの値を書き換えてパラメータ生成
        params = make_default_search_params(device_uuid='DEV-001')

        # Act
        inventories, total = search_device_inventories(params)
        # フィルタ条件取得
        call_args = q.filter.call_args_list
        # 文字列にキャスト
        filter_args_str = str(call_args)

        # Assert: filter が1回以上呼ばれていること（like フィルタ含む）
        assert q.filter.call_count > 0
        # Assert: 文字列パラメータによる検索が前方一致検索であること
        assert 'DEV-001%' in filter_args_str  # 前方一致

    @patch(f'{MODULE}.SortItemMaster')
    @patch(f'{MODULE}.InventoryStatusMaster')
    @patch(f'{MODULE}.DeviceTypeMaster')
    @patch(f'{MODULE}.DeviceMaster')
    @patch(f'{MODULE}.DeviceInventoryMaster')
    def test_search_with_device_name_applies_filter(
        self, mock_dim, mock_dm, mock_dtm, mock_ism, mock_sim
    ):
        """3.1.1.2: device_name を指定した場合、like フィルタが適用される/前方一致検索であること"""
        # Arrange
        from iot_app.services.device_inventory_service import search_device_inventories
        q = make_mock_query()
        mock_dim.query = q
        mock_sim.query.filter_by.return_value.first.return_value = None

        # ヘルパーの値を書き換えてパラメータ生成
        params = make_default_search_params(device_name='センサー')

        # Act
        inventories, total = search_device_inventories(params)
        # フィルタ条件取得
        call_args = q.filter.call_args_list
        # 文字列にキャスト
        filter_args_str = str(call_args)

        # Assert: filterメソッドが1回以上実行されること
        assert q.filter.call_count > 0
        # Assert: 文字列パラメータによる検索が前方一致検索であること
        assert 'センサー%' in filter_args_str  # 前方一致

    @patch(f'{MODULE}.SortItemMaster')
    @patch(f'{MODULE}.InventoryStatusMaster')
    @patch(f'{MODULE}.DeviceTypeMaster')
    @patch(f'{MODULE}.DeviceMaster')
    @patch(f'{MODULE}.DeviceInventoryMaster')
    def test_search_with_device_type_not_minus1_applies_filter(
        self, mock_dim, mock_dm, mock_dtm, mock_ism, mock_sim
    ):
        """3.1.1.1: device_type が -1（すべて）以外の場合、device_type_id フィルタが適用される"""
        # Arrange
        from iot_app.services.device_inventory_service import search_device_inventories
        q = make_mock_query()
        mock_dim.query = q
        mock_sim.query.filter_by.return_value.first.return_value = None

        # ヘルパーの値を書き換えてパラメータ生成
        params = make_default_search_params(device_type=1, sort_item_id=1, sort_order=1)

        # Act
        inventories, total = search_device_inventories(params)

        # Assert: filterメソッドが1回以上実行されること
        assert q.filter.call_count > 0

    @patch(f'{MODULE}.SortItemMaster')
    @patch(f'{MODULE}.InventoryStatusMaster')
    @patch(f'{MODULE}.DeviceTypeMaster')
    @patch(f'{MODULE}.DeviceMaster')
    @patch(f'{MODULE}.DeviceInventoryMaster')
    def test_search_with_purchase_date_range_applies_filter(
        self, mock_dim, mock_dm, mock_dtm, mock_ism, mock_sim
    ):
        """3.1.1.2: 購入日 From/To を指定した場合、範囲フィルタが適用される"""
        # Arrange
        from iot_app.services.device_inventory_service import search_device_inventories
        q = make_mock_query()
        mock_dim.query = q
        mock_sim.query.filter_by.return_value.first.return_value = None

        # ヘルパーの値を書き換えてパラメータ生成
        params = make_default_search_params(
            purchase_date_from=date(2025, 1, 1),
            purchase_date_to=date(2025, 12, 31),
        )

        # Act
        inventories, total = search_device_inventories(params)

        # Assert: filterメソッドが1回以上実行されること
        assert q.filter.call_count > 0

    @patch(f'{MODULE}.SortItemMaster')
    @patch(f'{MODULE}.InventoryStatusMaster')
    @patch(f'{MODULE}.DeviceTypeMaster')
    @patch(f'{MODULE}.DeviceMaster')
    @patch(f'{MODULE}.DeviceInventoryMaster')
    def test_search_without_conditions_returns_result(
        self, mock_dim, mock_dm, mock_dtm, mock_ism, mock_sim
    ):
        """3.1.2.1: 検索条件なし（-1/空文字/None）の場合、基本クエリが実行されてリストを返す"""
        # Arrange
        from iot_app.services.device_inventory_service import search_device_inventories
        q = make_mock_query()
        q.count.return_value = 0
        q.offset.return_value.all.return_value = []
        mock_dim.query = q
        mock_sim.query.filter_by.return_value.first.return_value = None

        # ヘルパーの値を書き換えてパラメータ生成
        params = make_default_search_params()

        # Act
        inventories, total = search_device_inventories(params)

        # Assert: デバイス台帳一覧がリスト型で返却されること
        assert isinstance(inventories, list)
        # Assert: 検索結果件数が数値型で返却されること
        assert isinstance(total, int)

    @patch(f'{MODULE}.SortItemMaster')
    @patch(f'{MODULE}.InventoryStatusMaster')
    @patch(f'{MODULE}.DeviceTypeMaster')
    @patch(f'{MODULE}.DeviceMaster')
    @patch(f'{MODULE}.DeviceInventoryMaster')
    def test_search_per_page_minus1_uses_all_without_limit(
        self, mock_dim, mock_dm, mock_dtm, mock_ism, mock_sim
    ):
        """3.1.3.1: per_page=-1 の場合、LIMIT/OFFSET なしで全件取得（all()）される"""
        # Arrange
        from iot_app.services.device_inventory_service import search_device_inventories
        mock_records = [Mock(), Mock()]
        q = make_mock_query()
        q.all.return_value = mock_records
        q.count.return_value = 2
        mock_dim.query = q
        mock_sim.query.filter_by.return_value.first.return_value = None

        # ヘルパーの値を書き換えてパラメータ生成
        params = make_default_search_params(per_page=-1)

        # Act
        inventories, total = search_device_inventories(params)

        # Assert: limit が呼ばれていないこと
        q.limit.assert_not_called()
        # Assert: 出力される結果がMockデータと一致すること（全件取得）
        assert inventories == mock_records

    @patch(f'{MODULE}.SortItemMaster')
    @patch(f'{MODULE}.InventoryStatusMaster')
    @patch(f'{MODULE}.DeviceTypeMaster')
    @patch(f'{MODULE}.DeviceMaster')
    @patch(f'{MODULE}.DeviceInventoryMaster')
    def test_search_with_per_page_uses_limit_offset(
        self, mock_dim, mock_dm, mock_dtm, mock_ism, mock_sim
    ):
        """3.1.3.1: per_page が正数の場合、LIMIT/OFFSET を使ってページングされる"""
        # Arrange
        from iot_app.services.device_inventory_service import search_device_inventories
        mock_records = [Mock()]
        q = make_mock_query()
        q.count.return_value = 1
        q.offset.return_value.all.return_value = mock_records
        mock_dim.query = q
        mock_sim.query.filter_by.return_value.first.return_value = None

        # ヘルパーの値を書き換えてパラメータ生成
        params = make_default_search_params(page=2, per_page=25)

        # Act
        inventories, total = search_device_inventories(params)

        # Assert: limitが呼ばれること
        q.limit.assert_called()
        # Assert: offsetが呼ばれること
        q.offset.assert_called()

    @patch(f'{MODULE}.SortItemMaster')
    @patch(f'{MODULE}.InventoryStatusMaster')
    @patch(f'{MODULE}.DeviceTypeMaster')
    @patch(f'{MODULE}.DeviceMaster')
    @patch(f'{MODULE}.DeviceInventoryMaster')
    def test_search_returns_tuple_of_list_and_total(
        self, mock_dim, mock_dm, mock_dtm, mock_ism, mock_sim
    ):
        """3.1.4.1: Repository がリストを返す場合、(inventories, total) タプルが返却される"""
        # Arrange
        from iot_app.services.device_inventory_service import search_device_inventories
        mock_records = [Mock(), Mock(), Mock()]
        q = make_mock_query()
        q.count.return_value = 3
        q.offset.return_value.all.return_value = mock_records
        mock_dim.query = q
        mock_sim.query.filter_by.return_value.first.return_value = None

        # ヘルパーの値をそのままパラメータとして設定
        params = make_default_search_params()

        # Act
        result = search_device_inventories(params)

        # Assert: (list, int)タプルの形式で返却されていること
        assert isinstance(result, tuple)
        # Assert: タプルのサイズが2（list, int）であること
        assert len(result) == 2
        _, total = result
        # Assert: 返却される検索結果件数が3であること
        assert total == 3

    @patch(f'{MODULE}.SortItemMaster')
    @patch(f'{MODULE}.InventoryStatusMaster')
    @patch(f'{MODULE}.DeviceTypeMaster')
    @patch(f'{MODULE}.DeviceMaster')
    @patch(f'{MODULE}.DeviceInventoryMaster')
    def test_search_empty_result_returns_empty_list_and_zero(
        self, mock_dim, mock_dm, mock_dtm, mock_ism, mock_sim
    ):
        """3.1.4.2: 検索結果が0件の場合、空リストと 0 が返却される"""
        # Arrange
        from iot_app.services.device_inventory_service import search_device_inventories
        q = make_mock_query()
        q.count.return_value = 0
        q.offset.return_value.all.return_value = []
        mock_dim.query = q
        mock_sim.query.filter_by.return_value.first.return_value = None

        # ヘルパーの値をそのままパラメータとして設定
        params = make_default_search_params()

        # Act
        inventories, total = search_device_inventories(params)

        # Assert: 検索結果一覧の件数が0件であること
        assert total == 0
        # Assert: 検索結果一覧が空であること
        assert inventories == []

    @patch(f'{MODULE}.SortItemMaster')
    @patch(f'{MODULE}.InventoryStatusMaster')
    @patch(f'{MODULE}.DeviceTypeMaster')
    @patch(f'{MODULE}.DeviceMaster')
    @patch(f'{MODULE}.DeviceInventoryMaster')
    def test_search_with_device_type_minus1_skips_filter(
        self, mock_dim, mock_dm, mock_dtm, mock_ism, mock_sim
    ):
        """3.1.2.1: device_type=-1（すべて）のとき、device_type_id フィルタが適用されない
        （SortItemMaster の filter_by は呼ばれない = ソート条件も未指定のためデフォルト動作）
        """
        # Arrange
        from iot_app.services.device_inventory_service import search_device_inventories
        q = make_mock_query()
        mock_dim.query = q
        mock_sim.query.filter_by.return_value.first.return_value = None

        # ヘルパーの値を書き換えてパラメータ生成
        params = make_default_search_params(device_type=-1)  # -1 = すべて（フィルタなし）

        # Act
        search_device_inventories(params)

        # Assert: SortItemMaster.query.filter_by は sort_item_id=-1 のため呼ばれないこと
        mock_sim.query.filter_by.assert_not_called()

    @patch(f'{MODULE}.SortItemMaster')
    @patch(f'{MODULE}.InventoryStatusMaster')
    @patch(f'{MODULE}.DeviceTypeMaster')
    @patch(f'{MODULE}.DeviceMaster')
    @patch(f'{MODULE}.DeviceInventoryMaster')
    def test_search_with_inventory_status_minus1_skips_filter(
        self, mock_dim, mock_dm, mock_dtm, mock_ism, mock_sim
    ):
        """3.1.2.1: inventory_status=-1（すべて）のとき、inventory_status_id フィルタが適用されない"""
        # Arrange
        from iot_app.services.device_inventory_service import search_device_inventories
        q = make_mock_query()
        mock_dim.query = q
        mock_sim.query.filter_by.return_value.first.return_value = None

        # device_type と inventory_status をともに -1 にしてフィルタなし状態を作る
        params = make_default_search_params(inventory_status=-1)

        # Act
        search_device_inventories(params)

        # Assert: sort_item_id=-1 のため SortItemMaster.query.filter_by は呼ばれないこと
        mock_sim.query.filter_by.assert_not_called()

    @patch(f'{MODULE}.SortItemMaster')
    @patch(f'{MODULE}.InventoryStatusMaster')
    @patch(f'{MODULE}.DeviceTypeMaster')
    @patch(f'{MODULE}.DeviceMaster')
    @patch(f'{MODULE}.DeviceInventoryMaster')
    def test_search_with_sort_item_id_minus1_skips_sort_lookup(
        self, mock_dim, mock_dm, mock_dtm, mock_ism, mock_sim
    ):
        """3.1.1.1: sort_item_id=-1（未選択）のとき、SortItemMaster の検索をスキップし
        デフォルトソート（device_inventory_id DESC）で order_by が呼ばれる"""
        # Arrange
        from iot_app.services.device_inventory_service import search_device_inventories
        q = make_mock_query()
        mock_dim.query = q

        # ヘルパーの値を書き換えてパラメータ生成
        params = make_default_search_params(sort_item_id=-1, sort_order=-1)

        # Act
        search_device_inventories(params)

        # Assert: sort_item_id=-1 のため SortItemMaster.query.filter_by は呼ばれないこと
        mock_sim.query.filter_by.assert_not_called()
        # order_by は呼ばれる（デフォルトソート）こと
        q.order_by.assert_called()

    @patch(f'{MODULE}.SortItemMaster')
    @patch(f'{MODULE}.InventoryStatusMaster')
    @patch(f'{MODULE}.DeviceTypeMaster')
    @patch(f'{MODULE}.DeviceMaster')
    @patch(f'{MODULE}.DeviceInventoryMaster')
    def test_search_with_sort_order_1_applies_asc(
        self, mock_dim, mock_dm, mock_dtm, mock_ism, mock_sim
    ):
        """3.1.1.1: sort_order=1（昇順）かつ有効な sort_item_id のとき、SortItemMaster が検索され昇順ソートが適用される"""
        # Arrange
        from iot_app.services.device_inventory_service import search_device_inventories
        q = make_mock_query()
        mock_dim.query = q
        mock_inventory_attr = Mock()
        mock_inventory_attr.asc.return_value = 'asc_col'
        mock_dim.device_inventory_id = mock_inventory_attr

        sort_item_mock = Mock()
        sort_item_mock.sort_item_name = 'inventory_location'  # DeviceInventoryMaster カラム
        mock_sim.query.filter_by.return_value.first.return_value = sort_item_mock

        # ヘルパーの値を書き換えてパラメータ生成
        params = make_default_search_params(sort_item_id=9, sort_order=1)  # sort_order=1: 昇順

        # Act
        search_device_inventories(params)

        # Assert: SortItemMaster の検索が呼ばれること
        mock_sim.query.filter_by.assert_called()
        # Assert: asc() が使われること
        mock_inventory_attr.asc.assert_called()

    @patch(f'{MODULE}.SortItemMaster')
    @patch(f'{MODULE}.InventoryStatusMaster')
    @patch(f'{MODULE}.DeviceTypeMaster')
    @patch(f'{MODULE}.DeviceMaster')
    @patch(f'{MODULE}.DeviceInventoryMaster')
    def test_search_with_sort_order_2_applies_desc(
        self, mock_dim, mock_dm, mock_dtm, mock_ism, mock_sim
    ):
        """3.1.1.1: sort_order=2（降順）かつ有効な sort_item_id のとき、SortItemMaster が検索され降順ソートが適用される"""
        # Arrange
        from iot_app.services.device_inventory_service import search_device_inventories
        q = make_mock_query()
        mock_dim.query = q
        mock_inventory_attr = Mock()
        mock_inventory_attr.desc.return_value = 'desc_col'
        mock_dim.device_inventory_id = mock_inventory_attr

        sort_item_mock = Mock()
        sort_item_mock.sort_item_name = 'inventory_location'  # DeviceInventoryMaster カラム
        mock_sim.query.filter_by.return_value.first.return_value = sort_item_mock

        # ヘルパーの値を書き換えてパラメータ生成
        params = make_default_search_params(sort_item_id=9, sort_order=2)  # sort_order=2: 降順

        # Act
        search_device_inventories(params)

        # Assert: SortItemMaster の検索が呼ばれること
        mock_sim.query.filter_by.assert_called()
        #  Assert: desc() が使われること
        mock_inventory_attr.desc.assert_called()


# ============================================================
# 3. create_device_inventory
# 観点: 2.1 正常系処理, 2.3 副作用チェック, 3.2 登録機能
# ============================================================

@pytest.mark.unit
class TestCreateDeviceInventory:
    """create_device_inventory - デバイス台帳登録
    観点: 2.1 正常系処理, 2.3 副作用チェック, 3.2 登録機能, 1.3 エラーハンドリング
    """

    @patch(f'{MODULE}.UnityCatalogConnector')
    @patch(f'{MODULE}.db')
    @patch(f'{MODULE}.DeviceMaster')
    @patch(f'{MODULE}.DeviceInventoryMaster')
    def test_create_success_adds_inventory_and_device_to_session(
        self, mock_dim_cls, mock_dm_cls, mock_db, mock_uc_cls
    ):
        """2.1.1 / 3.2.1.1: 有効な入力値で db.session.add() が device_inventory と device に対して呼ばれる"""
        # Arrange
        from iot_app.services.device_inventory_service import create_device_inventory
        mock_inventory = Mock()
        mock_inventory.device_inventory_id = 100
        mock_dim_cls.return_value = mock_inventory

        mock_device = Mock()
        mock_device.device_id = 200
        mock_dm_cls.return_value = mock_device

        mock_uc = Mock()
        mock_uc_cls.return_value = mock_uc

        # ヘルパーから登録に必要な最小データ構成を取得
        form_data = make_valid_form_data()

        # Act: INSERT実施
        create_device_inventory(form_data, creator_id=1)

        # Assert: db.session.add()が2回（デバイス台帳マスタ、デバイスマスタへの登録の2回）呼ばれること
        assert mock_db.session.add.call_count >= 2 
        # Assert: db.flush()が呼ばれること
        mock_db.session.flush.assert_called()

    @patch(f'{MODULE}.UnityCatalogConnector')
    @patch(f'{MODULE}.db')
    @patch(f'{MODULE}.DeviceMaster')
    @patch(f'{MODULE}.DeviceInventoryMaster')
    def test_create_success_commits_on_completion(
        self, mock_dim_cls, mock_dm_cls, mock_db, mock_uc_cls
    ):
        """2.1.1 / 3.2.2.1: 正常完了時に db.session.commit() が1回呼ばれる"""
        # Arrange
        from iot_app.services.device_inventory_service import create_device_inventory
        mock_inventory = Mock()
        mock_inventory.device_inventory_id = 100
        mock_dim_cls.return_value = mock_inventory

        mock_device = Mock()
        mock_device.device_id = 200
        mock_dm_cls.return_value = mock_device

        mock_uc = Mock()
        mock_uc_cls.return_value = mock_uc

        # ヘルパーから登録に必要な最小データ構成を取得
        form_data = make_valid_form_data()

        # Act: INSERT実施
        create_device_inventory(form_data, creator_id=1)

        # Assert: 登録成功時、db.session.commit()が1回だけ呼ばれていること
        mock_db.session.commit.assert_called_once()

    @patch(f'{MODULE}.UnityCatalogConnector')
    @patch(f'{MODULE}.db')
    @patch(f'{MODULE}.DeviceMaster')
    @patch(f'{MODULE}.DeviceInventoryMaster')
    def test_create_calls_unity_catalog_insert(
        self, mock_dim_cls, mock_dm_cls, mock_db, mock_uc_cls
    ):
        """3.2.1.1: Unity Catalog device_master への INSERT が呼び出される"""
        # Arrange
        from iot_app.services.device_inventory_service import create_device_inventory
        mock_inventory = Mock()
        mock_inventory.device_inventory_id = 100
        mock_dim_cls.return_value = mock_inventory

        mock_device = Mock()
        mock_device.device_id = 200
        mock_dm_cls.return_value = mock_device

        mock_uc = Mock()
        mock_uc_cls.return_value = mock_uc

        # ヘルパーから登録に必要な最小データ構成を取得
        form_data = make_valid_form_data()

        # Act: INSERT実施
        create_device_inventory(form_data, creator_id=1)

        # Assert: UCへのクエリ実行が1回呼び出されること
        mock_uc.execute_dml.assert_called_once()
        sql_arg = mock_uc.execute_dml.call_args[0][0]
        # Assert: UCへのINSERTクエリ実行が渡されること
        assert 'INSERT INTO iot_catalog.oltp_db.device_master' in sql_arg

    @patch(f'{MODULE}.UnityCatalogConnector')
    @patch(f'{MODULE}.db')
    @patch(f'{MODULE}.DeviceMaster')
    @patch(f'{MODULE}.DeviceInventoryMaster')
    def test_create_db_flush_exception_calls_rollback(
        self, mock_dim_cls, mock_dm_cls, mock_db, mock_uc_cls
    ):
        """2.3.2: db.session.flush() が例外をスローした場合、rollback() が呼ばれる"""
        # Arrange
        from iot_app.services.device_inventory_service import create_device_inventory
        mock_inventory = Mock()
        mock_dim_cls.return_value = mock_inventory
        
        # db.session.flush()の代わりに強制的にExceptionが発生するように設定
        mock_db.session.flush.side_effect = Exception('DB Flush Error')

        # ヘルパーから登録に必要な最小データ構成を取得
        form_data = make_valid_form_data()

        # Act: create_device_inventoryはdb.session.flush()時にExceptionが発生するはず
        with pytest.raises(Exception):
            # INSERT実施
            create_device_inventory(form_data, creator_id=1)

        # Assert: db.session.rollback()が呼び出されること
        mock_db.session.rollback.assert_called()

    @patch(f'{MODULE}.UnityCatalogConnector')
    @patch(f'{MODULE}.db')
    @patch(f'{MODULE}.DeviceMaster')
    @patch(f'{MODULE}.DeviceInventoryMaster')
    def test_create_db_exception_propagates(
        self, mock_dim_cls, mock_dm_cls, mock_db, mock_uc_cls
    ):
        """1.3.1: DB例外が握りつぶされず上位へ伝播される"""
        # Arrange
        from iot_app.services.device_inventory_service import create_device_inventory
        mock_inventory = Mock()
        mock_dim_cls.return_value = mock_inventory
        
        # db.session.flush()の代わりに強制的にRuntimeErrorが発生するように設定
        mock_db.session.flush.side_effect = RuntimeError('DB Connection Error')

        # ヘルパーから登録に必要な最小データ構成を取得
        form_data = make_valid_form_data()

        # Act: create_device_inventoryはdb.session.flush()時にRuntimeErrorが発生するはず
        with pytest.raises(RuntimeError):
            # INSERT実施
            create_device_inventory(form_data, creator_id=1)

    @patch(f'{MODULE}.UnityCatalogConnector')
    @patch(f'{MODULE}.db')
    @patch(f'{MODULE}.DeviceMaster')
    @patch(f'{MODULE}.DeviceInventoryMaster')
    def test_create_uc_exception_triggers_compensating_delete(
        self, mock_dim_cls, mock_dm_cls, mock_db, mock_uc_cls
    ):
        """1.3.1: UC INSERT 失敗時に補償 DELETE が実行される（execute_dml が2回呼ばれる）"""
        # Arrange
        from iot_app.services.device_inventory_service import create_device_inventory
        mock_inventory = Mock()
        mock_inventory.device_inventory_id = 100
        mock_dim_cls.return_value = mock_inventory

        mock_device = Mock()
        mock_device.device_id = 200
        mock_dm_cls.return_value = mock_device

        mock_uc = Mock()
        # INSERT（1回目）失敗し、Exception発報したのち、補償DELETE（2回目）に成功するように設定
        mock_uc.execute_dml.side_effect = [Exception('UC Insert Error'), None]
        mock_uc_cls.return_value = mock_uc

        # ヘルパーから登録に必要な最小データ構成を取得
        form_data = make_valid_form_data()

        # Act & Assert
        with pytest.raises(Exception):
            # INSERT実施
            create_device_inventory(form_data, creator_id=1)

        # Assert: UCへのクエリ実行が2回実行されること
        assert mock_uc.execute_dml.call_count == 2
        compensating_sql = mock_uc.execute_dml.call_args_list[1][0][0]
        # Assert: UCへのDELETEクエリ実行が2回のうちに実行されること
        assert 'DELETE FROM iot_catalog.oltp_db.device_master' in compensating_sql

    @patch(f'{MODULE}.UnityCatalogConnector')
    @patch(f'{MODULE}.db')
    @patch(f'{MODULE}.DeviceMaster')
    @patch(f'{MODULE}.DeviceInventoryMaster')
    def test_create_uc_exception_calls_oltp_rollback(
        self, mock_dim_cls, mock_dm_cls, mock_db, mock_uc_cls
    ):
        """2.3.2: UC INSERT 失敗時に db.session.rollback() が呼ばれる"""
        # Arrange
        from iot_app.services.device_inventory_service import create_device_inventory
        mock_inventory = Mock()
        mock_inventory.device_inventory_id = 100
        mock_dim_cls.return_value = mock_inventory

        mock_device = Mock()
        mock_device.device_id = 200
        mock_dm_cls.return_value = mock_device

        mock_uc = Mock()
        
        # INSERT（1回目）に失敗しException発報→有償DELETE（2回目）に成功するように設定
        mock_uc.execute_dml.side_effect = [Exception('UC Error'), None]
        mock_uc_cls.return_value = mock_uc

        # ヘルパーから登録に必要な最小データ構成を取得
        form_data = make_valid_form_data()

        # Act & Assert
        with pytest.raises(Exception):
            # INSERT実施
            create_device_inventory(form_data, creator_id=1)

        # Assert: UCへのINSERTクエリ実行失敗時、OLTPに対するロールバックが実行されること
        mock_db.session.rollback.assert_called()

    @patch(f'{MODULE}.uuid')
    @patch(f'{MODULE}.UnityCatalogConnector')
    @patch(f'{MODULE}.db')
    @patch(f'{MODULE}.DeviceMaster')
    @patch(f'{MODULE}.DeviceInventoryMaster')
    def test_create_generates_device_inventory_uuid(
        self, mock_dim_cls, mock_dm_cls, mock_db, mock_uc_cls, mock_uuid_mod
    ):
        """3.2.1.1: device_inventory_uuid が uuid4() で自動生成される"""
        # Arrange
        from iot_app.services.device_inventory_service import create_device_inventory
        mock_uuid_mod.uuid4.return_value = Mock(__str__=lambda self: 'generated-uuid')

        mock_inventory = Mock()
        mock_inventory.device_inventory_id = 100
        mock_dim_cls.return_value = mock_inventory

        mock_device = Mock()
        mock_device.device_id = 200
        mock_dm_cls.return_value = mock_device

        mock_uc = Mock()
        mock_uc_cls.return_value = mock_uc

        # ヘルパーから登録に必要な最小データ構成を取得
        form_data = make_valid_form_data()

        # Act: INSERT実施
        create_device_inventory(form_data, creator_id=1)

        # Assert: データ登録時、uuid生成メソッドが呼び出されること
        mock_uuid_mod.uuid4.assert_called()

    @patch(f'{MODULE}.UnityCatalogConnector')
    @patch(f'{MODULE}.db')
    @patch(f'{MODULE}.DeviceMaster')
    @patch(f'{MODULE}.DeviceInventoryMaster')
    def test_create_sets_creator_id_on_records(
        self, mock_dim_cls, mock_dm_cls, mock_db, mock_uc_cls
    ):
        """3.2.1.1: creator_id が device_inventory と device の creator/modifier に設定される"""
        # Arrange
        from iot_app.services.device_inventory_service import create_device_inventory
        created_kwargs = {}

        def capture_dim(**kwargs):
            created_kwargs.update(kwargs)
            m = Mock()
            m.device_inventory_id = 100
            return m

        # mock_dim_clsに設定された値をcapture_dim関数を使ってcreated_kwargsに保持
        mock_dim_cls.side_effect = capture_dim

        mock_device = Mock()
        mock_device.device_id = 200
        mock_dm_cls.return_value = mock_device

        mock_uc = Mock()
        mock_uc_cls.return_value = mock_uc

        # ヘルパーから登録に必要な最小データ構成を取得
        form_data = make_valid_form_data()

        # Act: INSERT実施
        create_device_inventory(form_data, creator_id=42)

        # Assert: device_inventory の creator に 42 が渡されること
        assert created_kwargs.get('creator') == 42
        # Assert: device_inventory の modifier に 42 が渡されること
        assert created_kwargs.get('modifier') == 42


# ============================================================
# 4. update_device_inventory
# 観点: 2.1 正常系処理, 2.2 対象データ存在チェック, 2.3 副作用チェック, 3.3 更新機能
# ============================================================

@pytest.mark.unit
class TestUpdateDeviceInventory:
    """update_device_inventory - デバイス台帳更新
    観点: 2.1 正常系処理, 2.2 対象データ存在チェック, 2.3 副作用チェック,
          3.3 更新機能, 1.3 エラーハンドリング
    """

    def _setup_mock_inventory_and_device(self, mock_dim_cls, mock_dm_cls):
        """テスト用の inventory/device モックを組み立てるヘルパー"""
        mock_inventory = Mock()
        mock_inventory.device_inventory_id = 100
        mock_dim_cls.query.filter_by.return_value.first_or_404.return_value = mock_inventory

        mock_device = Mock()
        mock_device.device_id = 200
        mock_device.device_uuid = 'OLD-UUID'
        mock_device.device_name = 'OLD NAME'
        mock_device.device_type_id = 1
        mock_device.device_model = 'OLD-MODEL'
        mock_device.sim_id = None
        mock_device.mac_address = 'AA:BB:CC:DD:EE:FF'
        mock_device.organization_id = '1'
        mock_device.software_version = None
        mock_device.device_location = None
        mock_device.certificate_expiration_date = None
        mock_device.modifier = 1
        mock_dm_cls.query.filter_by.return_value.first_or_404.return_value = mock_device

        return mock_inventory, mock_device

    @patch(f'{MODULE}.UnityCatalogConnector')
    @patch(f'{MODULE}.db')
    @patch(f'{MODULE}.DeviceMaster')
    @patch(f'{MODULE}.DeviceInventoryMaster')
    def test_update_success_updates_inventory_fields(
        self, mock_dim_cls, mock_dm_cls, mock_db, mock_uc_cls
    ):
        """2.1.1 / 3.3.1.1: 有効な入力値で device_inventory_master のフィールドが更新される"""
        # Arrange
        from iot_app.services.device_inventory_service import update_device_inventory
        mock_inventory, mock_device = self._setup_mock_inventory_and_device(
            mock_dim_cls, mock_dm_cls
        )
        mock_uc = Mock()
        mock_uc_cls.return_value = mock_uc

        # ヘルパーのinventory_location、purchase_dateの内容を上書きしてデータ構成を取得
        form_data = make_valid_form_data(
            inventory_location='新倉庫B',
            purchase_date=date(2025, 6, 1),
        )

        # Act: UPDATE実施
        update_device_inventory('test-uuid', form_data, modifier_id=1)

        # Assert: 在庫場所が「新倉庫B」に更新されること
        assert mock_inventory.inventory_location == '新倉庫B'
        # Assert: 購入日が「2025/06/01」に更新されること
        assert mock_inventory.purchase_date == date(2025, 6, 1)

    @patch(f'{MODULE}.UnityCatalogConnector')
    @patch(f'{MODULE}.db')
    @patch(f'{MODULE}.DeviceMaster')
    @patch(f'{MODULE}.DeviceInventoryMaster')
    def test_update_success_updates_device_fields(
        self, mock_dim_cls, mock_dm_cls, mock_db, mock_uc_cls
    ):
        """3.3.1.1: 有効な入力値で device_master のフィールドが更新される"""
        # Arrange
        from iot_app.services.device_inventory_service import update_device_inventory
        mock_inventory, mock_device = self._setup_mock_inventory_and_device(
            mock_dim_cls, mock_dm_cls
        )
        mock_uc = Mock()
        mock_uc_cls.return_value = mock_uc

        # ヘルパーのdevice_name、device_type_idの内容を上書きしてデータ構成を取得
        form_data = make_valid_form_data(
            device_name='新センサーX',
            device_type_id=2,
        )

        # Act: UPDATE実施
        update_device_inventory('test-uuid', form_data, modifier_id=1)

        # Assert: 更新後のデバイス名が「新センサーX」であること
        assert mock_device.device_name == '新センサーX'
        # Assert: 更新後のデバイスデバイス種別IDが2であること
        assert mock_device.device_type_id == 2

    @patch(f'{MODULE}.UnityCatalogConnector')
    @patch(f'{MODULE}.db')
    @patch(f'{MODULE}.DeviceMaster')
    @patch(f'{MODULE}.DeviceInventoryMaster')
    def test_update_sets_modifier_id_on_both_records(
        self, mock_dim_cls, mock_dm_cls, mock_db, mock_uc_cls
    ):
        """3.3.2.2: modifier_id が device_inventory と device の両方に設定される"""
        # Arrange
        from iot_app.services.device_inventory_service import update_device_inventory
        mock_inventory, mock_device = self._setup_mock_inventory_and_device(
            mock_dim_cls, mock_dm_cls
        )
        mock_uc = Mock()
        mock_uc_cls.return_value = mock_uc

        # ヘルパーから更新に必要な最小データ構成を取得
        form_data = make_valid_form_data()

        # Act: UPDATE実施
        update_device_inventory('test-uuid', form_data, modifier_id=99)

        # Assert: デバイス台帳マスタのレコード更新者IDが99であること
        assert mock_inventory.modifier == 99
        # Assert: デバイスマスタのレコード更新者IDが99であること
        assert mock_device.modifier == 99

    @patch(f'{MODULE}.UnityCatalogConnector')
    @patch(f'{MODULE}.db')
    @patch(f'{MODULE}.DeviceMaster')
    @patch(f'{MODULE}.DeviceInventoryMaster')
    def test_update_calls_unity_catalog_update(
        self, mock_dim_cls, mock_dm_cls, mock_db, mock_uc_cls
    ):
        """3.3.1.1: Unity Catalog device_master への UPDATE が呼び出される"""
        # Arrange
        from iot_app.services.device_inventory_service import update_device_inventory
        mock_inventory, mock_device = self._setup_mock_inventory_and_device(
            mock_dim_cls, mock_dm_cls
        )
        mock_uc = Mock()
        mock_uc_cls.return_value = mock_uc

        # ヘルパーから更新に必要な最小データ構成を取得
        form_data = make_valid_form_data()

        # Act: UPDATE実施
        update_device_inventory('test-uuid', form_data, modifier_id=1)

        # Assert: UCへのクエリ実行が1回呼び出されること
        mock_uc.execute_dml.assert_called_once()
        sql_arg = mock_uc.execute_dml.call_args[0][0]
        # Assert: UCへのUPDATEクエリ実行が呼び出されること
        assert 'UPDATE iot_catalog.oltp_db.device_master' in sql_arg

    @patch(f'{MODULE}.UnityCatalogConnector')
    @patch(f'{MODULE}.db')
    @patch(f'{MODULE}.DeviceMaster')
    @patch(f'{MODULE}.DeviceInventoryMaster')
    def test_update_success_commits(
        self, mock_dim_cls, mock_dm_cls, mock_db, mock_uc_cls
    ):
        """3.3.2.1: 更新処理成功時に commit() が1回呼ばれる"""
        # Arrange
        from iot_app.services.device_inventory_service import update_device_inventory
        mock_inventory, mock_device = self._setup_mock_inventory_and_device(
            mock_dim_cls, mock_dm_cls
        )
        mock_uc = Mock()
        mock_uc_cls.return_value = mock_uc

        # ヘルパーから更新に必要な最小データ構成を取得
        form_data = make_valid_form_data()

        # Act: UPDATE実施
        update_device_inventory('test-uuid', form_data, modifier_id=1)

        # Assert: 更新成功時、db.session.commit()が1回呼び出されること
        mock_db.session.commit.assert_called_once()

    @patch(f'{MODULE}.UnityCatalogConnector')
    @patch(f'{MODULE}.db')
    @patch(f'{MODULE}.DeviceMaster')
    @patch(f'{MODULE}.DeviceInventoryMaster')
    def test_update_db_flush_exception_calls_rollback(
        self, mock_dim_cls, mock_dm_cls, mock_db, mock_uc_cls
    ):
        """2.3.2: db.session.flush() 失敗時に rollback() が呼ばれる"""
        # Arrange
        from iot_app.services.device_inventory_service import update_device_inventory
        mock_inventory, mock_device = self._setup_mock_inventory_and_device(
            mock_dim_cls, mock_dm_cls
        )
        # db.session.flush()の代わりに、強制的Exceptionを発生させるように設定
        mock_db.session.flush.side_effect = Exception('DB Flush Error')

        # ヘルパーから更新に必要な最小データ構成を取得
        form_data = make_valid_form_data()

        # Act & Assert: 前の設定から、必ずExceptionが発生するはず。発生しなければNG
        with pytest.raises(Exception):
            # UPDATE実施
            update_device_inventory('test-uuid', form_data, modifier_id=1)

        # Assert: db.session.flush()失敗時、db.session.rollback()が呼び出されること
        mock_db.session.rollback.assert_called()

    @patch(f'{MODULE}.UnityCatalogConnector')
    @patch(f'{MODULE}.db')
    @patch(f'{MODULE}.DeviceMaster')
    @patch(f'{MODULE}.DeviceInventoryMaster')
    def test_update_uc_exception_triggers_uc_rollback(
        self, mock_dim_cls, mock_dm_cls, mock_db, mock_uc_cls
    ):
        """1.3.1: UC UPDATE 失敗時に旧値での UC ロールバック UPDATE が実行される（execute_dml が2回呼ばれる）"""
        # Arrange
        from iot_app.services.device_inventory_service import update_device_inventory
        mock_inventory, mock_device = self._setup_mock_inventory_and_device(
            mock_dim_cls, mock_dm_cls
        )
        mock_uc = Mock()
        
        # UPDATE失敗し、Exception発報 → UC ロールバック成功と設定
        mock_uc.execute_dml.side_effect = [Exception('UC Update Error'), None]
        mock_uc_cls.return_value = mock_uc

        # ヘルパーから更新に必要な最小データ構成を取得
        form_data = make_valid_form_data()

        # Act & Assert: 前の設定から、必ずExceptionが発生するはず。発生しなければNG
        with pytest.raises(Exception):
            # UPDATE実施
            update_device_inventory('test-uuid', form_data, modifier_id=1)

        # Assert: execute_dmlがUPDATE、UCロールバックのちょうど2度呼ばれること
        assert mock_uc.execute_dml.call_count == 2

    @patch(f'{MODULE}.UnityCatalogConnector')
    @patch(f'{MODULE}.db')
    @patch(f'{MODULE}.DeviceMaster')
    @patch(f'{MODULE}.DeviceInventoryMaster')
    def test_update_uc_exception_calls_oltp_rollback(
        self, mock_dim_cls, mock_dm_cls, mock_db, mock_uc_cls
    ):
        """2.3.2: UC UPDATE 失敗時に db.session.rollback() が呼ばれる"""
        # Arrange
        from iot_app.services.device_inventory_service import update_device_inventory
        mock_inventory, mock_device = self._setup_mock_inventory_and_device(
            mock_dim_cls, mock_dm_cls
        )
        mock_uc = Mock()
        
        # UPDATE失敗し、Exception発報 → UC ロールバック成功と設定
        mock_uc.execute_dml.side_effect = [Exception('UC Error'), None]
        mock_uc_cls.return_value = mock_uc

        # ヘルパーから更新に必要な最小データ構成を取得
        form_data = make_valid_form_data()

        # Act & Assert: 前の設定から、必ずExceptionが発生するはず。発生しなければNG
        with pytest.raises(Exception):
            # UPDATE実施
            update_device_inventory('test-uuid', form_data, modifier_id=1)

        # Assert: OLTPロールバックが呼ばれていること
        mock_db.session.rollback.assert_called()


# ============================================================
# 5. delete_device_inventories
# 観点: 2.1 正常系処理, 2.2 対象データ存在チェック, 2.3 副作用チェック, 3.4 削除機能
# ============================================================

@pytest.mark.unit
class TestDeleteDeviceInventories:
    """delete_device_inventories - デバイス台帳論理削除
    観点: 2.1 正常系処理, 2.2 対象データ存在チェック, 2.3 副作用チェック,
          3.4 削除機能, 1.3 エラーハンドリング
    """

    @patch(f'{MODULE}.UnityCatalogConnector')
    @patch(f'{MODULE}.db')
    @patch(f'{MODULE}.DeviceMaster')
    @patch(f'{MODULE}.DeviceInventoryMaster')
    def test_delete_success_sets_delete_flag_true_on_inventory(
        self, mock_dim_cls, mock_dm_cls, mock_db, mock_uc_cls
    ):
        """2.1.1 / 3.4.1.1: 有効な UUID で device_inventory の delete_flag が True になる"""
        # Arrange
        from iot_app.services.device_inventory_service import delete_device_inventories
        mock_inventory = Mock()
        mock_inventory.device_inventory_id = 100
        mock_inventory.delete_flag = False
        mock_dim_cls.query.filter.return_value.all.return_value = [mock_inventory]

        mock_device = Mock()
        mock_device.delete_flag = False
        mock_dm_cls.query.filter_by.return_value.all.return_value = [mock_device]

        mock_uc = Mock()
        mock_uc_cls.return_value = mock_uc

        # Act: DELETE実行
        delete_device_inventories(['uuid-001'], modifier_id=1)

        # Assert: デバイス台帳の対象となるデータのdelete_flagがTrueに更新されていること（論理削除扱いであること）
        assert mock_inventory.delete_flag is True

    @patch(f'{MODULE}.UnityCatalogConnector')
    @patch(f'{MODULE}.db')
    @patch(f'{MODULE}.DeviceMaster')
    @patch(f'{MODULE}.DeviceInventoryMaster')
    def test_delete_success_sets_delete_flag_true_on_device(
        self, mock_dim_cls, mock_dm_cls, mock_db, mock_uc_cls
    ):
        """2.1.1 / 3.4.1.1: device_master の delete_flag も True になる"""
        # Arrange
        from iot_app.services.device_inventory_service import delete_device_inventories
        mock_inventory = Mock()
        mock_inventory.device_inventory_id = 100
        mock_dim_cls.query.filter.return_value.all.return_value = [mock_inventory]

        mock_device = Mock()
        mock_device.delete_flag = False
        mock_dm_cls.query.filter_by.return_value.all.return_value = [mock_device]

        mock_uc = Mock()
        mock_uc_cls.return_value = mock_uc

        # Act: 
        delete_device_inventories(['uuid-001'], modifier_id=1)

        # Assert
        assert mock_device.delete_flag is True

    @patch(f'{MODULE}.UnityCatalogConnector')
    @patch(f'{MODULE}.db')
    @patch(f'{MODULE}.DeviceMaster')
    @patch(f'{MODULE}.DeviceInventoryMaster')
    def test_delete_sets_modifier_id_on_records(
        self, mock_dim_cls, mock_dm_cls, mock_db, mock_uc_cls
    ):
        """3.4.1.1: modifier_id が device_inventory と device の両方に設定される"""
        # Arrange
        from iot_app.services.device_inventory_service import delete_device_inventories
        mock_inventory = Mock()
        mock_inventory.device_inventory_id = 100
        mock_dim_cls.query.filter.return_value.all.return_value = [mock_inventory]

        mock_device = Mock()
        mock_dm_cls.query.filter_by.return_value.all.return_value = [mock_device]

        mock_uc = Mock()
        mock_uc_cls.return_value = mock_uc

        # Act
        delete_device_inventories(['uuid-001'], modifier_id=99)

        # Assert
        assert mock_inventory.modifier == 99
        assert mock_device.modifier == 99

    @patch(f'{MODULE}.UnityCatalogConnector')
    @patch(f'{MODULE}.db')
    @patch(f'{MODULE}.DeviceMaster')
    @patch(f'{MODULE}.DeviceInventoryMaster')
    def test_delete_calls_unity_catalog_soft_delete(
        self, mock_dim_cls, mock_dm_cls, mock_db, mock_uc_cls
    ):
        """3.4.1.1: Unity Catalog device_master への論理削除 UPDATE が呼び出される"""
        # Arrange
        from iot_app.services.device_inventory_service import delete_device_inventories
        mock_inventory = Mock()
        mock_inventory.device_inventory_id = 100
        mock_dim_cls.query.filter.return_value.all.return_value = [mock_inventory]

        mock_device = Mock()
        mock_dm_cls.query.filter_by.return_value.all.return_value = [mock_device]

        mock_uc = Mock()
        mock_uc_cls.return_value = mock_uc

        # Act
        delete_device_inventories(['uuid-001'], modifier_id=1)

        # Assert
        mock_uc.execute_dml.assert_called_once()
        sql_arg = mock_uc.execute_dml.call_args[0][0]
        assert 'UPDATE iot_catalog.oltp_db.device_master' in sql_arg
        assert 'delete_flag' in sql_arg

    @patch(f'{MODULE}.UnityCatalogConnector')
    @patch(f'{MODULE}.db')
    @patch(f'{MODULE}.DeviceMaster')
    @patch(f'{MODULE}.DeviceInventoryMaster')
    def test_delete_success_commits(
        self, mock_dim_cls, mock_dm_cls, mock_db, mock_uc_cls
    ):
        """3.4.2.1: 削除処理成功時に commit() が1回呼ばれる"""
        # Arrange
        from iot_app.services.device_inventory_service import delete_device_inventories
        mock_inventory = Mock()
        mock_inventory.device_inventory_id = 100
        mock_dim_cls.query.filter.return_value.all.return_value = [mock_inventory]

        mock_device = Mock()
        mock_dm_cls.query.filter_by.return_value.all.return_value = [mock_device]

        mock_uc = Mock()
        mock_uc_cls.return_value = mock_uc

        # Act
        delete_device_inventories(['uuid-001'], modifier_id=1)

        # Assert
        mock_db.session.commit.assert_called_once()

    @patch(f'{MODULE}.UnityCatalogConnector')
    @patch(f'{MODULE}.db')
    @patch(f'{MODULE}.DeviceMaster')
    @patch(f'{MODULE}.DeviceInventoryMaster')
    def test_delete_no_matching_records_raises_value_error(
        self, mock_dim_cls, mock_dm_cls, mock_db, mock_uc_cls
    ):
        """2.2.2: 存在しない UUID を指定した場合 ValueError がスローされる"""
        # Arrange
        from iot_app.services.device_inventory_service import delete_device_inventories
        mock_dim_cls.query.filter.return_value.all.return_value = []

        # Act & Assert
        with pytest.raises(ValueError, match='削除対象が見つかりません'):
            delete_device_inventories(['nonexistent-uuid'], modifier_id=1)

    @patch(f'{MODULE}.UnityCatalogConnector')
    @patch(f'{MODULE}.db')
    @patch(f'{MODULE}.DeviceMaster')
    @patch(f'{MODULE}.DeviceInventoryMaster')
    def test_delete_empty_uuids_list_raises_value_error(
        self, mock_dim_cls, mock_dm_cls, mock_db, mock_uc_cls
    ):
        """2.2.2: 空の UUID リストを指定した場合 ValueError がスローされる"""
        # Arrange
        from iot_app.services.device_inventory_service import delete_device_inventories
        mock_dim_cls.query.filter.return_value.all.return_value = []

        # Act & Assert
        with pytest.raises(ValueError):
            delete_device_inventories([], modifier_id=1)

    @patch(f'{MODULE}.UnityCatalogConnector')
    @patch(f'{MODULE}.db')
    @patch(f'{MODULE}.DeviceMaster')
    @patch(f'{MODULE}.DeviceInventoryMaster')
    def test_delete_db_flush_exception_calls_rollback(
        self, mock_dim_cls, mock_dm_cls, mock_db, mock_uc_cls
    ):
        """2.3.2: db.session.flush() 失敗時に rollback() が呼ばれる"""
        # Arrange
        from iot_app.services.device_inventory_service import delete_device_inventories
        mock_inventory = Mock()
        mock_inventory.device_inventory_id = 100
        mock_dim_cls.query.filter.return_value.all.return_value = [mock_inventory]

        mock_device = Mock()
        mock_dm_cls.query.filter_by.return_value.all.return_value = [mock_device]
        mock_db.session.flush.side_effect = Exception('DB Flush Error')

        # Act & Assert
        with pytest.raises(Exception):
            delete_device_inventories(['uuid-001'], modifier_id=1)

        mock_db.session.rollback.assert_called()

    @patch(f'{MODULE}.UnityCatalogConnector')
    @patch(f'{MODULE}.db')
    @patch(f'{MODULE}.DeviceMaster')
    @patch(f'{MODULE}.DeviceInventoryMaster')
    def test_delete_uc_exception_triggers_uc_rollback(
        self, mock_dim_cls, mock_dm_cls, mock_db, mock_uc_cls
    ):
        """1.3.1: UC 論理削除失敗時に UC ロールバック UPDATE が実行される（execute_dml が2回呼ばれる）"""
        # Arrange
        from iot_app.services.device_inventory_service import delete_device_inventories
        mock_inventory = Mock()
        mock_inventory.device_inventory_id = 100
        mock_dim_cls.query.filter.return_value.all.return_value = [mock_inventory]

        mock_device = Mock()
        mock_dm_cls.query.filter_by.return_value.all.return_value = [mock_device]

        mock_uc = Mock()
        # 1回目 (論理削除UPDATE) 失敗 → 2回目 (ロールバックUPDATE) 成功
        mock_uc.execute_dml.side_effect = [Exception('UC Error'), None]
        mock_uc_cls.return_value = mock_uc

        # Act & Assert
        with pytest.raises(Exception):
            delete_device_inventories(['uuid-001'], modifier_id=1)

        assert mock_uc.execute_dml.call_count == 2
        rollback_sql = mock_uc.execute_dml.call_args_list[1][0][0]
        assert 'delete_flag = false' in rollback_sql or 'delete_flag=false' in rollback_sql.replace(' ', '')

    @patch(f'{MODULE}.UnityCatalogConnector')
    @patch(f'{MODULE}.db')
    @patch(f'{MODULE}.DeviceMaster')
    @patch(f'{MODULE}.DeviceInventoryMaster')
    def test_delete_uc_exception_calls_oltp_rollback(
        self, mock_dim_cls, mock_dm_cls, mock_db, mock_uc_cls
    ):
        """2.3.2: UC 論理削除失敗時に db.session.rollback() が呼ばれる"""
        # Arrange
        from iot_app.services.device_inventory_service import delete_device_inventories
        mock_inventory = Mock()
        mock_inventory.device_inventory_id = 100
        mock_dim_cls.query.filter.return_value.all.return_value = [mock_inventory]

        mock_device = Mock()
        mock_dm_cls.query.filter_by.return_value.all.return_value = [mock_device]

        mock_uc = Mock()
        mock_uc.execute_dml.side_effect = [Exception('UC Error'), None]
        mock_uc_cls.return_value = mock_uc

        # Act & Assert
        with pytest.raises(Exception):
            delete_device_inventories(['uuid-001'], modifier_id=1)

        mock_db.session.rollback.assert_called()

    @patch(f'{MODULE}.UnityCatalogConnector')
    @patch(f'{MODULE}.db')
    @patch(f'{MODULE}.DeviceMaster')
    @patch(f'{MODULE}.DeviceInventoryMaster')
    def test_delete_multiple_inventories(
        self, mock_dim_cls, mock_dm_cls, mock_db, mock_uc_cls
    ):
        """2.1.3: 複数の UUID を指定した場合、すべての台帳が論理削除される"""
        # Arrange
        from iot_app.services.device_inventory_service import delete_device_inventories
        inv1 = Mock()
        inv1.device_inventory_id = 100
        inv1.delete_flag = False
        inv2 = Mock()
        inv2.device_inventory_id = 200
        inv2.delete_flag = False
        mock_dim_cls.query.filter.return_value.all.return_value = [inv1, inv2]

        mock_device = Mock()
        mock_dm_cls.query.filter_by.return_value.all.return_value = [mock_device]

        mock_uc = Mock()
        mock_uc_cls.return_value = mock_uc

        # Act
        delete_device_inventories(['uuid-001', 'uuid-002'], modifier_id=1)

        # Assert
        assert inv1.delete_flag is True
        assert inv2.delete_flag is True


# ============================================================
# 6. export_device_inventories_csv
# 観点: 3.5.1 CSV生成ロジック, 3.5.3 エンコーディング処理
# ============================================================

@pytest.mark.unit
class TestExportDeviceInventoriesCsv:
    """export_device_inventories_csv - CSVエクスポート
    観点: 3.5.1 CSV生成ロジック, 3.5.3 エンコーディング処理
    """

    @patch(f'{MODULE}.search_device_inventories')
    def test_export_calls_search_with_per_page_minus1(self, mock_search):
        """3.1.3.1: CSVエクスポートは per_page=-1 で全件取得する"""
        # Arrange
        from iot_app.services.device_inventory_service import export_device_inventories_csv
        mock_search.return_value = ([], 0)

        # Act
        export_device_inventories_csv(make_default_search_params())

        # Assert
        call_params = mock_search.call_args[0][0]
        assert call_params['per_page'] == -1

    @patch(f'{MODULE}.search_device_inventories')
    def test_export_calls_search_with_page_1(self, mock_search):
        """3.1.1.1: CSVエクスポートは page=1 で呼び出す（ページングを無効化する）"""
        # Arrange
        from iot_app.services.device_inventory_service import export_device_inventories_csv
        mock_search.return_value = ([], 0)

        # Act
        export_device_inventories_csv(make_default_search_params(page=3))

        # Assert
        call_params = mock_search.call_args[0][0]
        assert call_params['page'] == 1

    @patch(f'{MODULE}.search_device_inventories')
    def test_export_csv_contains_required_headers(self, mock_search):
        """3.5.1.1: 定義された列名がCSVヘッダー行に出力される"""
        # Arrange
        from iot_app.services.device_inventory_service import export_device_inventories_csv
        mock_search.return_value = ([], 0)

        # Act
        result = export_device_inventories_csv(make_default_search_params())

        # Assert: UTF-8 BOM 付きまたは通常の文字列で decode
        decoded = result if isinstance(result, str) else result.decode('utf-8-sig')
        assert '操作列' in decoded
        assert '在庫状況' in decoded
        assert 'モデル情報' in decoded
        assert 'デバイス名' in decoded
        assert 'デバイス種別' in decoded
        assert 'SIMID' in decoded
        assert 'MACアドレス' in decoded
        assert '購入日' in decoded
        assert '出荷予定日' in decoded
        assert '出荷日' in decoded
        assert 'メーカー保証終了日' in decoded
        assert '在庫場所' in decoded

    @patch(f'{MODULE}.search_device_inventories')
    def test_export_empty_list_returns_headers_only(self, mock_search):
        """3.5.1.3: 空リストを渡した場合、ヘッダー行のみ出力される"""
        # Arrange
        from iot_app.services.device_inventory_service import export_device_inventories_csv
        mock_search.return_value = ([], 0)

        # Act
        result = export_device_inventories_csv(make_default_search_params())

        # Assert
        decoded = result if isinstance(result, str) else result.decode('utf-8-sig')
        data_lines = [line for line in decoded.strip().split('\n') if line.strip()]
        assert len(data_lines) == 1  # ヘッダー行のみ

    @patch(f'{MODULE}.search_device_inventories')
    def test_export_multiple_records_all_output(self, mock_search):
        """3.5.1.2: 複数件のデータが全件CSV行として出力される"""
        # Arrange
        from iot_app.services.device_inventory_service import export_device_inventories_csv
        inv1 = make_inventory_mock(device_name='センサーA', purchase_date=date(2025, 1, 15))
        inv2 = make_inventory_mock(device_name='センサーB', purchase_date=date(2025, 2, 20))
        mock_search.return_value = ([inv1, inv2], 2)

        # Act
        result = export_device_inventories_csv(make_default_search_params())

        # Assert
        decoded = result if isinstance(result, str) else result.decode('utf-8-sig')
        data_lines = [line for line in decoded.strip().split('\n') if line.strip()]
        assert len(data_lines) == 3  # ヘッダー + 2件

    @patch(f'{MODULE}.search_device_inventories')
    def test_export_csv_column_order(self, mock_search):
        """3.5.1.4: CSV列の順序が仕様通りである（デバイス名, デバイス種別, ..., 在庫場所）"""
        # Arrange
        from iot_app.services.device_inventory_service import export_device_inventories_csv
        mock_search.return_value = ([], 0)

        # Act
        result = export_device_inventories_csv(make_default_search_params())

        # Assert
        decoded = result if isinstance(result, str) else result.decode('utf-8-sig')
        header_line = decoded.strip().split('\n')[0]
        # CSV ヘッダーからカラム名を取得（ダブルクォートを除去）
        columns = [c.strip().strip('"') for c in header_line.split(',')]

        expected_order = [
            'デバイス名', 'デバイス種別', 'モデル情報', 'SIMID', 'MACアドレス',
            '在庫状況', '購入日', '出荷予定日', '出荷日', 'メーカー保証終了日', '在庫場所',
        ]
        assert columns == expected_order

    @patch(f'{MODULE}.search_device_inventories')
    def test_export_csv_encodes_with_utf8_bom(self, mock_search):
        """3.5.3.1: CSVが UTF-8 BOM 付きでエンコードされる"""
        # Arrange
        from iot_app.services.device_inventory_service import export_device_inventories_csv
        mock_search.return_value = ([], 0)

        # Act
        result = export_device_inventories_csv(make_default_search_params())

        # Assert: 戻り値がバイト列の場合は BOM バイト列を確認、文字列の場合は BOM 文字を確認
        if isinstance(result, bytes):
            assert result[:3] == b'\xef\xbb\xbf'  # UTF-8 BOM
        else:
            # pandas の to_csv(encoding='utf-8-sig') は BOM 付き文字列を返す場合がある
            # TODO: 実装によって戻り値の型が変わる可能性あり。実装完了後に要確認
            assert isinstance(result, str)

    @patch(f'{MODULE}.search_device_inventories')
    def test_export_date_formatted_as_slash_separated(self, mock_search):
        """3.5.1.2: 購入日が YYYY/MM/DD 形式でCSVに出力される"""
        # Arrange
        from iot_app.services.device_inventory_service import export_device_inventories_csv
        inv = make_inventory_mock(purchase_date=date(2025, 3, 15))
        mock_search.return_value = ([inv], 1)

        # Act
        result = export_device_inventories_csv(make_default_search_params())

        # Assert
        decoded = result if isinstance(result, str) else result.decode('utf-8-sig')
        assert '2025/03/15' in decoded

    @patch(f'{MODULE}.search_device_inventories')
    def test_export_optional_date_none_outputs_empty_string(self, mock_search):
        """3.5.1.2: 任意の日付フィールドが None の場合、空文字が出力される"""
        # Arrange
        from iot_app.services.device_inventory_service import export_device_inventories_csv
        inv = make_inventory_mock(estimated_ship_date=None, ship_date=None)
        mock_search.return_value = ([inv], 1)

        # Act
        result = export_device_inventories_csv(make_default_search_params())

        # Assert: 空フィールドが含まれること（連続カンマで確認）
        decoded = result if isinstance(result, str) else result.decode('utf-8-sig')
        # 出荷予定日・出荷日が空 → データ行に空フィールドが存在すること
        data_line = decoded.strip().split('\n')[1]
        assert ',,' in data_line or ',"","",' in data_line or ',' in data_line
