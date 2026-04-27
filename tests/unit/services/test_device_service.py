"""
デバイス管理 - Service層 単体テスト

対象ファイル: src/iot_app/services/device_service.py

参照ドキュメント:
  - UI仕様書:           docs/03-features/flask-app/devices/ui-specification.md
  - 機能設計書:         docs/03-features/flask-app/devices/workflow-specification.md
  - 単体テスト観点表:   docs/05-testing/unit-test/unit-test-perspectives.md
  - 実装ガイド:         docs/05-testing/unit-test/unit-test-guide.md
"""
import pytest
from unittest.mock import MagicMock, Mock, patch

# ============================================================
# 定数
# ============================================================

MODULE = 'iot_app.services.device_service'


# ============================================================
# ヘルパー関数
# ============================================================

def make_valid_device_data(**overrides):
    """
    登録・更新フォームの有効データを生成するヘルパー。
    必須項目をすべて含む最小有効データをベースに、引数で任意項目を上書きできる。
    """
    data = {
        'device_uuid':                 'DEV-001',           # 必須, 最大128文字, 英数字+ハイフンのみ
        'device_name':                 'センサー1号機',       # 必須, 最大100文字
        'device_type_id':              1,                   # 必須
        'device_model':                'MODEL-A100',        # 必須, 最大100文字
        'sim_id':                      None,                # 任意, 最大20文字
        'mac_address':                 'AA:BB:CC:DD:EE:FF', # 任意, XX:XX:XX:XX:XX:XX形式
        'device_location':             '本社1F',             # 任意, 最大100文字
        'organization_id':             1,                   # 必須
        'certificate_expiration_date': None,                # 任意
    }
    data.update(overrides)
    return data


def make_default_search_params(**overrides):
    """検索パラメータのデフォルト値を生成するヘルパー"""
    params = {
        'page':                        1,
        'per_page':                    25,
        'sort_by':                     '',
        'order':                       '',
        'device_id':                   '',
        'device_name':                 '',
        'device_type_id':              None,
        'location':                    '',
        'organization_id':             None,
        'certificate_expiration_date': '',
        'status':                      None,
    }
    params.update(overrides)
    return params


def make_mock_query():
    """SQLAlchemy クエリチェーンのモックを生成するヘルパー"""
    q = MagicMock()
    q.join.return_value = q
    q.outerjoin.return_value = q
    q.filter.return_value = q
    q.filter_by.return_value = q
    q.order_by.return_value = q
    q.count.return_value = 0
    q.all.return_value = []
    q.limit.return_value = q
    q.offset.return_value = q
    q.first.return_value = None
    return q


def make_device_mock(**kwargs):
    """デバイスデータモックを生成するヘルパー"""
    m = Mock()
    m.device_uuid = kwargs.get('device_uuid', 'DEV-001')
    m.device_name = kwargs.get('device_name', 'センサー1号機')
    m.device_type_id = kwargs.get('device_type_id', 1)
    m.device_type = Mock()
    m.device_type.device_type_name = kwargs.get('device_type_name', 'センサー')
    m.device_model = kwargs.get('device_model', 'MODEL-A100')
    m.sim_id = kwargs.get('sim_id', None)
    m.mac_address = kwargs.get('mac_address', 'AA:BB:CC:DD:EE:FF')
    m.organization_id = kwargs.get('organization_id', 1)
    m.software_version = kwargs.get('software_version', None)
    m.device_location = kwargs.get('device_location', '本社1F')
    m.certificate_expiration_date = kwargs.get('certificate_expiration_date', None)
    return m


def make_device_row(**kwargs):
    """generate_devices_csv 用の (device, org_name, type_name, last_received_time) タプルを生成するヘルパー"""
    device = make_device_mock(**{k: v for k, v in kwargs.items()
                                  if k not in ('organization_name', 'device_type_name', 'last_received_time')})
    org_name = kwargs.get('organization_name', '本社')
    type_name = kwargs.get('device_type_name', 'センサー')
    last_received_time = kwargs.get('last_received_time', None)
    return (device, org_name, type_name, last_received_time)


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
        from iot_app.services.device_service import get_default_search_params

        result = get_default_search_params()
        # Assert: result['page'] が 1 であること
        assert result['page'] == 1

    def test_returns_per_page_25(self):
        """2.1.1: per_page のデフォルト値は 25 である"""
        # Arrange / Act
        from iot_app.services.device_service import get_default_search_params

        result = get_default_search_params()
        # Assert: result['per_page'] が 25 であること
        assert result['per_page'] == 25

    def test_returns_empty_string_for_device_id(self):
        """2.1.1: device_id のデフォルト値は空文字である"""
        # Arrange / Act
        from iot_app.services.device_service import get_default_search_params

        result = get_default_search_params()
        # Assert: result['device_id'] が空文字であること
        assert result['device_id'] == ''

    def test_returns_empty_string_for_device_name(self):
        """2.1.1: device_name のデフォルト値は空文字である"""
        # Arrange / Act
        from iot_app.services.device_service import get_default_search_params

        result = get_default_search_params()
        # Assert: result['device_name'] が空文字であること
        assert result['device_name'] == ''

    def test_returns_none_for_device_type_id(self):
        """2.1.1: device_type_id のデフォルト値は None である（すべて選択）"""
        # Arrange / Act
        from iot_app.services.device_service import get_default_search_params

        result = get_default_search_params()
        # Assert: result['device_type_id'] が None であること
        assert result['device_type_id'] is None

    def test_returns_empty_string_for_location(self):
        """2.1.1: location のデフォルト値は空文字である"""
        # Arrange / Act
        from iot_app.services.device_service import get_default_search_params

        result = get_default_search_params()
        # Assert: result['location'] が空文字であること
        assert result['location'] == ''

    def test_returns_none_for_organization_id(self):
        """2.1.1: organization_id のデフォルト値は None である（すべて選択）"""
        # Arrange / Act
        from iot_app.services.device_service import get_default_search_params

        result = get_default_search_params()
        # Assert: result['organization_id'] が None であること
        assert result['organization_id'] is None

    def test_returns_empty_string_for_certificate_expiration_date(self):
        """2.1.1: certificate_expiration_date のデフォルト値は空文字である"""
        # Arrange / Act
        from iot_app.services.device_service import get_default_search_params

        result = get_default_search_params()
        # Assert: result['certificate_expiration_date'] が空文字であること
        assert result['certificate_expiration_date'] == ''

    def test_returns_none_for_status(self):
        """2.1.1: status のデフォルト値は None である（すべて選択）"""
        # Arrange / Act
        from iot_app.services.device_service import get_default_search_params

        result = get_default_search_params()
        # Assert: result['status'] が None であること
        assert result['status'] is None

    def test_returns_empty_string_for_sort_by(self):
        """2.1.1: sort_by のデフォルト値は空文字である（未選択）"""
        # Arrange / Act
        from iot_app.services.device_service import get_default_search_params

        result = get_default_search_params()
        # Assert: result['sort_by'] が空文字であること
        assert result['sort_by'] == ''

    def test_returns_empty_string_for_order(self):
        """2.1.1: order のデフォルト値は空文字である（未選択）"""
        # Arrange / Act
        from iot_app.services.device_service import get_default_search_params

        result = get_default_search_params()
        # Assert: result['order'] が空文字であること
        assert result['order'] == ''


# ============================================================
# 2. search_devices
# 観点: 3.1.1 検索条件指定, 3.1.2 検索条件未指定, 3.1.3 ページング, 3.1.4 戻り値ハンドリング
# ============================================================

@pytest.mark.unit
class TestSearchDevices:
    """search_devices - デバイス一覧検索
    観点: 3.1.1 検索条件指定, 3.1.2 検索条件未指定, 3.1.3 ページング・件数制御,
          3.1.4 検索結果戻り値ハンドリング
    """

    @patch(f'{MODULE}.DeviceTypeMaster')
    @patch(f'{MODULE}.DeviceMasterByUser')
    def test_search_with_device_uuid_applies_like_filter(
        self, mock_dbmu, mock_dtm
    ):
        """3.1.1.1: device_id を指定した場合、LIKE フィルタが適用される（部分一致）"""
        # Arrange
        from iot_app.services.device_service import search_devices

        q = make_mock_query()
        mock_dbmu.query = q
        params = make_default_search_params(device_id='DEV-001')

        # Act: 検索実行
        search_devices(params, user_id=1)

        # Assert: filter が1回以上呼ばれ、device_id を含むフィルタが適用されること
        assert q.filter.call_count > 0
        mock_dbmu.device_uuid.like.assert_called_with('%DEV-001%')

    @patch(f'{MODULE}.DeviceTypeMaster')
    @patch(f'{MODULE}.DeviceMasterByUser')
    def test_search_with_device_name_applies_like_filter(
        self, mock_dbmu, mock_dtm
    ):
        """3.1.1.2: device_name を指定した場合、LIKE フィルタが適用される（部分一致）"""
        # Arrange
        from iot_app.services.device_service import search_devices

        q = make_mock_query()
        mock_dbmu.query = q
        params = make_default_search_params(device_name='センサー')

        # Act: 検索実行
        search_devices(params, user_id=1)

        # Assert: filter が1回以上呼ばれ、device_name を含むフィルタが適用されること
        assert q.filter.call_count > 0
        mock_dbmu.device_name.like.assert_called_with('%センサー%')

    @patch(f'{MODULE}.DeviceTypeMaster')
    @patch(f'{MODULE}.DeviceMasterByUser')
    def test_search_with_device_type_id_applies_filter(
        self, mock_dbmu, mock_dtm
    ):
        """3.1.1.1: device_type_id が None 以外の場合、device_type_id フィルタが適用される"""
        # Arrange
        from iot_app.services.device_service import search_devices

        q = make_mock_query()
        mock_dbmu.query = q
        params = make_default_search_params(device_type_id=1)

        # Act: 検索実行
        search_devices(params, user_id=1)

        # Assert: filter が呼ばれること
        assert q.filter.call_count > 0

    @patch(f'{MODULE}.DeviceTypeMaster')
    @patch(f'{MODULE}.DeviceMasterByUser')
    def test_search_with_device_location_applies_like_filter(
        self, mock_dbmu, mock_dtm
    ):
        """3.1.1.1: device_location を指定した場合、LIKE フィルタが適用される（部分一致）"""
        # Arrange
        from iot_app.services.device_service import search_devices

        q = make_mock_query()
        mock_dbmu.query = q
        params = make_default_search_params(location='本社')

        # Act: 検索実行
        search_devices(params, user_id=1)
        filter_args_str = str(q.filter.call_args_list)

        # Assert: location を含むフィルタが適用されること
        assert q.filter.call_count > 0
        mock_dbmu.device_location.like.assert_called_with('%本社%')

    @patch(f'{MODULE}.DeviceTypeMaster')
    @patch(f'{MODULE}.DeviceMasterByUser')
    def test_search_with_organization_id_applies_filter(
        self, mock_dbmu, mock_dtm
    ):
        """3.1.1.1: organization_id が None 以外の場合、organization_id フィルタが適用される"""
        # Arrange
        from iot_app.services.device_service import search_devices

        q = make_mock_query()
        mock_dbmu.query = q
        params = make_default_search_params(organization_id=10)

        # Act: 検索実行
        search_devices(params, user_id=1)

        # Assert: filter が呼ばれること
        assert q.filter.call_count > 0

    @patch(f'{MODULE}.DeviceTypeMaster')
    @patch(f'{MODULE}.DeviceMasterByUser')
    def test_search_with_no_conditions_calls_no_text_filter(
        self, mock_dbmu, mock_dtm
    ):
        """3.1.2.1: 検索条件未指定の場合、テキスト系フィルタが適用されない"""
        # Arrange
        from iot_app.services.device_service import search_devices

        q = make_mock_query()
        mock_dbmu.query = q
        params = make_default_search_params()   # 全デフォルト（空文字/None）

        # Act: 検索実行（条件なし）
        search_devices(params, user_id=1)
        filter_args_str = str(q.filter.call_args_list)

        # Assert: テキスト検索文字列が含まれないこと
        assert 'DEV' not in filter_args_str
        assert 'センサー' not in filter_args_str

    @patch(f'{MODULE}.DeviceTypeMaster')
    @patch(f'{MODULE}.DeviceMasterByUser')
    def test_search_pagination_applies_limit_and_offset(
        self, mock_dbmu, mock_dtm
    ):
        """3.1.3.1: ページネーション設定値（page/per_page）が LIMIT/OFFSET として渡される"""
        # Arrange
        from iot_app.services.device_service import search_devices

        q = make_mock_query()
        mock_dbmu.query = q
        params = make_default_search_params(page=2, per_page=25)

        # Act: 2ページ目を取得
        search_devices(params, user_id=1)

        # Assert: limit / offset が呼ばれること
        assert q.limit.call_count > 0
        assert q.offset.call_count > 0

    @patch(f'{MODULE}.DeviceTypeMaster')
    @patch(f'{MODULE}.DeviceMasterByUser')
    def test_search_returns_list_and_total(
        self, mock_dbmu, mock_dtm
    ):
        """3.1.4.1: Repository がリストを返した場合、リストと件数がそのまま返される"""
        # Arrange
        from iot_app.services.device_service import search_devices

        q = make_mock_query()
        device1 = make_device_mock(device_uuid='DEV-001')
        device2 = make_device_mock(device_uuid='DEV-002')
        q.all.return_value = [device1, device2]
        q.count.return_value = 2
        mock_dbmu.query = q
        params = make_default_search_params()

        # Act: 検索実行
        devices, total = search_devices(params, user_id=1)

        # Assert: 結果リストと件数が返却されること
        assert len(devices) == 2
        assert total == 2

    @patch(f'{MODULE}.DeviceTypeMaster')
    @patch(f'{MODULE}.DeviceMasterByUser')
    def test_search_returns_empty_list_when_no_results(
        self, mock_dbmu, mock_dtm
    ):
        """3.1.4.2: Repository が空リストを返した場合、空リストと件数0が返される"""
        # Arrange
        from iot_app.services.device_service import search_devices

        q = make_mock_query()
        q.all.return_value = []
        q.count.return_value = 0
        mock_dbmu.query = q
        params = make_default_search_params()

        # Act: 検索実行（ヒットなし）
        devices, total = search_devices(params, user_id=1)

        # Assert: 空リストと件数0が返却されること
        assert devices == []
        assert total == 0

    @patch(f'{MODULE}.DeviceTypeMaster')
    @patch(f'{MODULE}.DeviceMasterByUser')
    def test_search_with_all_conditions_applied(
        self, mock_dbmu, mock_dtm
    ):
        """3.1.1.2: 複数条件を指定した場合、全条件が欠落なく渡される"""
        # Arrange
        from iot_app.services.device_service import search_devices

        q = make_mock_query()
        mock_dbmu.query = q
        params = make_default_search_params(
            device_id='DEV-001',
            device_name='センサー',
            device_type_id=1,
            location='本社',
            organization_id=10,
            status='connected',
        )

        # Act: 全条件指定で検索実行
        search_devices(params, user_id=1)

        # Assert: 各検索条件が全てフィルタとして適用されること
        mock_dbmu.device_uuid.like.assert_called_with('%DEV-001%')
        mock_dbmu.device_name.like.assert_called_with('%センサー%')
        mock_dbmu.device_location.like.assert_called_with('%本社%')

    @patch(f'{MODULE}.DeviceTypeMaster')
    @patch(f'{MODULE}.DeviceMasterByUser')
    def test_search_partial_conditions_does_not_apply_empty_conditions(
        self, mock_dbmu, mock_dtm
    ):
        """3.1.1.3: 一部条件のみ指定した場合、未指定条件はフィルタとして適用されない"""
        # Arrange
        from iot_app.services.device_service import search_devices

        q = make_mock_query()
        mock_dbmu.query = q
        # device_id のみ指定、他はデフォルト（空文字/None）
        params = make_default_search_params(device_id='DEV-001')

        # Act: 一部条件のみで検索実行
        search_devices(params, user_id=1)

        # Assert: 指定した条件（device_id）は適用され、未指定条件はフィルタとして渡されないこと
        mock_dbmu.device_uuid.like.assert_called_with('%DEV-001%')
        mock_dbmu.device_name.like.assert_not_called()
        mock_dbmu.device_location.like.assert_not_called()

    @patch(f'{MODULE}.DeviceTypeMaster')
    @patch(f'{MODULE}.DeviceMasterByUser')
    def test_search_multiple_conditions_combined_with_and(
        self, mock_dbmu, mock_dtm
    ):
        """3.1.1.4: 複数条件を指定した場合、すべての条件が AND 条件として組み立てられる
        （filter() が条件ごとに呼び出され、チェーンされることで AND 結合となる）
        """
        # Arrange
        from iot_app.services.device_service import search_devices

        q = make_mock_query()
        mock_dbmu.query = q
        params = make_default_search_params(
            device_id='DEV-001',
            device_name='センサー',
            location='本社',
        )

        # Act: 複数条件で検索実行
        search_devices(params, user_id=1)

        # Assert: filter() が複数回呼ばれること（条件ごとに filter チェーンされ AND 結合となる）
        assert q.filter.call_count >= 2

    @patch(f'{MODULE}.DeviceTypeMaster')
    @patch(f'{MODULE}.DeviceMasterByUser')
    def test_search_no_or_condition_in_filter_calls(
        self, mock_dbmu, mock_dtm
    ):
        """3.1.1.5: 複数条件を指定した場合、OR 条件（or_()）が含まれない"""
        # Arrange
        from iot_app.services.device_service import search_devices

        q = make_mock_query()
        mock_dbmu.query = q
        params = make_default_search_params(
            device_id='DEV-001',
            device_name='センサー',
        )

        # Act: 複数条件で検索実行
        search_devices(params, user_id=1)
        filter_args_str = str(q.filter.call_args_list)

        # Assert: OR 条件を示す文字列（or_）がフィルタ引数に含まれないこと
        assert 'or_' not in filter_args_str

    @patch(f'{MODULE}.DeviceTypeMaster')
    @patch(f'{MODULE}.DeviceMasterByUser')
    def test_search_raises_on_db_error(self, mock_dbmu, mock_dtm):
        """1.3.1: DBクエリ実行中に例外が発生した場合、例外が伝播し 500 エラーとなる"""
        # Arrange
        from iot_app.services.device_service import search_devices

        # DBクエリで例外を発生させる
        mock_dbmu.query.filter.side_effect = Exception('DB接続エラー')
        mock_dbmu.query.filter_by.side_effect = Exception('DB接続エラー')
        mock_dbmu.query.join.side_effect = Exception('DB接続エラー')
        params = make_default_search_params()

        # Act & Assert: 例外が呼び出し元へ伝播すること
        with pytest.raises(Exception, match='DB接続エラー'):
            search_devices(params, user_id=1)

    @patch(f'{MODULE}.DeviceTypeMaster')
    @patch(f'{MODULE}.DeviceMasterByUser')
    def test_search_with_status_condition(self, mock_dbmu, mock_dtm):
        """3.1.1.1: status='connected' を指定した場合、filter() が適用される"""
        # Arrange
        from iot_app.services.device_service import search_devices

        q = make_mock_query()
        mock_dbmu.query = q
        params = make_default_search_params(status='connected')

        # Act
        search_devices(params, user_id=1)

        # Assert: status 条件が filter() として適用されること
        assert q.filter.call_count > 0

    @patch(f'{MODULE}.DeviceTypeMaster')
    @patch(f'{MODULE}.DeviceMasterByUser')
    def test_search_with_status_disconnected_condition(self, mock_dbmu, mock_dtm):
        """3.1.1.1: status='disconnected' を指定した場合、filter() が適用される"""
        # Arrange
        from iot_app.services.device_service import search_devices

        q = make_mock_query()
        mock_dbmu.query = q
        params = make_default_search_params(status='disconnected')

        # Act
        search_devices(params, user_id=1)

        # Assert: status='disconnected' 条件が filter() として適用されること
        assert q.filter.call_count > 0

    @patch(f'{MODULE}.DeviceTypeMaster')
    @patch(f'{MODULE}.DeviceMasterByUser')
    def test_search_with_certificate_expiration_date_condition(self, mock_dbmu, mock_dtm):
        """3.1.1.1: certificate_expiration_date を指定した場合、filter() が適用される"""
        # Arrange
        from iot_app.services.device_service import search_devices
        from datetime import date

        q = make_mock_query()
        mock_dbmu.query = q
        params = make_default_search_params(certificate_expiration_date=date(2025, 12, 31))

        # MagicMock.__le__ はデフォルト NotImplemented を返すため date との <= 比較で TypeError になる。
        # patch.object でテスト実行中のみ __le__ を上書きして比較を通過させる。
        cert_attr = mock_dbmu.certificate_expiration_date
        with patch(f'{MODULE}.DeviceMasterByUser', mock_dbmu):
            with patch.object(type(cert_attr), '__le__', new=lambda self, other: MagicMock()):
                # Act
                search_devices(params, user_id=1)

        # Assert: certificate_expiration_date 条件が filter() として適用されること
        assert q.filter.call_count > 0


# ============================================================
# 3. create_device
# 観点: 3.2.1 登録処理呼び出し, 3.2.2 登録結果, 2.3 副作用チェック
# ============================================================

@pytest.mark.unit
class TestCreateDevice:
    """create_device - デバイス登録
    観点: 3.2.1 登録処理呼び出し, 3.2.2 登録結果, 2.3 副作用チェック
    """

    @patch(f'{MODULE}.db')
    @patch(f'{MODULE}.DeviceMaster')
    def test_create_raises_if_device_uuid_duplicate(
        self, mock_dm, mock_db
    ):
        """3.2.1.3: device_uuid が既に存在する場合、DuplicateDeviceIdError がスローされ DB に登録されない"""
        # Arrange
        from iot_app.services.device_service import create_device
        from iot_app.services.device_service import DuplicateDeviceIdError

        # 重複デバイスを返すようにモック設定
        mock_dm.query.filter_by.return_value.first.return_value = Mock()
        data = make_valid_device_data()

        # Act & Assert: DuplicateDeviceIdError が発生すること
        with pytest.raises(DuplicateDeviceIdError):
            create_device(data, user_id=1)

        # Assert: DB への session.add が呼ばれないこと（重複チェックで処理中断）
        mock_db.session.add.assert_not_called()

    @patch(f'{MODULE}.db')
    @patch(f'{MODULE}.DeviceMaster')
    def test_create_raises_if_mac_address_duplicate(
        self, mock_dm, mock_db
    ):
        """3.2.1.3: mac_address が既に存在する場合、DuplicateMacAddressError がスローされ DB に登録されない"""
        # Arrange
        from iot_app.services.device_service import create_device
        from iot_app.services.device_service import DuplicateMacAddressError

        # device_uuid は重複なし、mac_address は重複あり
        call_count = {'count': 0}

        def side_effect(**kwargs):
            m = MagicMock()
            call_count['count'] += 1
            if call_count['count'] == 1:
                # device_uuid チェック: 重複なし
                m.first.return_value = None
            else:
                # mac_address チェック: 重複あり
                m.first.return_value = Mock()
            return m

        mock_dm.query.filter_by.side_effect = side_effect
        data = make_valid_device_data()

        # Act & Assert: DuplicateMacAddressError が発生すること
        with pytest.raises(DuplicateMacAddressError):
            create_device(data, user_id=1)

        # Assert: DB への session.add が呼ばれないこと
        mock_db.session.add.assert_not_called()

    @patch(f'{MODULE}.db')
    @patch(f'{MODULE}.DeviceMaster')
    @patch(f'{MODULE}.UnityCatalogConnector')
    def test_create_success_calls_db_session_add_and_commit(
        self, mock_uc, mock_dm, mock_db
    ):
        """3.2.1.1 / 3.2.2.1: 有効なデータで登録内容が DB に渡され、session.commit が呼ばれる"""
        # Arrange
        from iot_app.services.device_service import create_device

        # device_uuid, mac_address ともに重複なし
        mock_dm.query.filter_by.return_value.first.return_value = None
        data = make_valid_device_data()

        # Act: デバイス登録実行
        create_device(data, user_id=1)

        # Assert: DB に session.add と session.commit が呼ばれること
        mock_db.session.add.assert_called_once()
        mock_db.session.commit.assert_called_once()

    @patch(f'{MODULE}.db')
    @patch(f'{MODULE}.DeviceMaster')
    def test_create_rollback_on_db_error(
        self, mock_dm, mock_db
    ):
        """2.3.2: DB エラー発生時に rollback が呼ばれ、データが更新されない"""
        # Arrange
        from iot_app.services.device_service import create_device

        mock_dm.query.filter_by.return_value.first.return_value = None
        # session.commit 時に例外発生
        mock_db.session.commit.side_effect = Exception('DB error')
        data = make_valid_device_data()

        # Act & Assert: 例外が上位へ伝播すること
        with pytest.raises(Exception):
            create_device(data, user_id=1)

        # Assert: rollback が呼ばれること
        mock_db.session.rollback.assert_called_once()

    @patch(f'{MODULE}.db')
    @patch(f'{MODULE}.DeviceMaster')
    @patch(f'{MODULE}.UnityCatalogConnector')
    def test_create_with_optional_fields_none_passes(
        self, mock_uc, mock_dm, mock_db
    ):
        """3.2.1.2: 任意項目に None を含む場合、None のまま DB に渡される"""
        # Arrange
        from iot_app.services.device_service import create_device

        mock_dm.query.filter_by.return_value.first.return_value = None
        # sim_id, mac_address, device_location, certificate_expiration_date を None に
        data = make_valid_device_data(
            sim_id=None,
            mac_address=None,
            device_location=None,
            certificate_expiration_date=None,
        )

        # Act: 任意項目 None で登録実行
        create_device(data, user_id=1)

        # Assert: session.add と session.commit が呼ばれること（None でも正常登録）
        mock_db.session.add.assert_called_once()
        mock_db.session.commit.assert_called_once()

    @patch(f'{MODULE}.db')
    @patch(f'{MODULE}.DeviceMaster')
    @patch(f'{MODULE}.UnityCatalogConnector')
    def test_create_returns_created_device_id(
        self, mock_uc, mock_dm, mock_db
    ):
        """3.2.2.1: 登録成功時、Repository（session.add）に渡されたデバイスオブジェクトが返却される"""
        # Arrange
        from iot_app.services.device_service import create_device

        mock_dm.query.filter_by.return_value.first.return_value = None
        # DeviceMaster() コンストラクタが返すインスタンスに device_uuid を設定
        created_instance = Mock()
        created_instance.device_uuid = 'DEV-001'
        mock_dm.return_value = created_instance
        data = make_valid_device_data(device_uuid='DEV-001')

        # Act: デバイス登録実行
        result = create_device(data, user_id=1)

        # Assert: 戻り値に登録されたデバイスの識別子（device_uuid）が含まれること
        assert result is not None
        assert result.device_uuid == 'DEV-001'

    @patch(f'{MODULE}.db')
    @patch(f'{MODULE}.DeviceMaster')
    def test_create_raises_on_device_uuid_db_query_error(
        self, mock_dm, mock_db
    ):
        """1.3.1: device_uuid 重複チェック中に DB エラーが発生した場合、例外が伝播し 500 エラーとなる"""
        # Arrange
        from iot_app.services.device_service import create_device

        # device_uuid の重複チェッククエリで例外を発生させる
        mock_dm.query.filter_by.side_effect = Exception('DB接続エラー')
        data = make_valid_device_data()

        # Act & Assert: 例外が呼び出し元へ伝播すること
        with pytest.raises(Exception, match='DB接続エラー'):
            create_device(data, user_id=1)

        # Assert: session.add は呼ばれないこと
        mock_db.session.add.assert_not_called()

    @patch(f'{MODULE}.db')
    @patch(f'{MODULE}.DeviceMaster')
    def test_create_raises_on_mac_address_db_query_error(
        self, mock_dm, mock_db
    ):
        """1.3.1: mac_address 重複チェック中に DB エラーが発生した場合、例外が伝播し 500 エラーとなる"""
        # Arrange
        from iot_app.services.device_service import create_device

        # device_uuid チェックは重複なし、mac_address チェックで DB エラー
        call_count = {'count': 0}

        def side_effect(**kwargs):
            m = MagicMock()
            call_count['count'] += 1
            if call_count['count'] == 1:
                m.first.return_value = None   # device_uuid: 重複なし
            else:
                raise Exception('mac_address DB クエリエラー')
            return m

        mock_dm.query.filter_by.side_effect = side_effect
        data = make_valid_device_data()

        # Act & Assert: 例外が呼び出し元へ伝播すること
        with pytest.raises(Exception, match='mac_address DB クエリエラー'):
            create_device(data, user_id=1)

        # Assert: session.add は呼ばれないこと
        mock_db.session.add.assert_not_called()

    @patch(f'{MODULE}.db')
    @patch(f'{MODULE}.DeviceMaster')
    @patch(f'{MODULE}.UnityCatalogConnector')
    def test_create_db_insert_called_before_unity_catalog_insert(
        self, mock_uc, mock_dm, mock_db
    ):
        """3.2.1.1: DB 登録（session.add）が UnityCatalog 登録より先に呼ばれること（フローの順序保証）"""
        # Arrange
        from iot_app.services.device_service import create_device

        mock_dm.query.filter_by.return_value.first.return_value = None
        call_order = []

        def db_add(*args, **kwargs):
            call_order.append('db')

        def uc_insert(*args, **kwargs):
            call_order.append('unity_catalog')

        mock_db.session.add.side_effect = db_add
        mock_uc.return_value.execute_dml.side_effect = uc_insert
        data = make_valid_device_data()

        # Act
        create_device(data, user_id=1)

        # Assert: DB 登録 → UnityCatalog 登録 の順であること
        assert call_order.index('db') < call_order.index('unity_catalog')

    @patch(f'{MODULE}.db')
    @patch(f'{MODULE}.DeviceMaster')
    @patch(f'{MODULE}.UnityCatalogConnector')
    def test_create_rollback_on_unity_catalog_error(
        self, mock_uc, mock_dm, mock_db
    ):
        """2.3.2: OLTP DB commit 後に UnityCatalog 登録が失敗した場合、db.session.rollback が呼ばれ例外が伝播する"""
        # Arrange
        from iot_app.services.device_service import create_device

        mock_dm.query.filter_by.return_value.first.return_value = None
        # DB add/flush/commit は成功、UC INSERT で例外発生
        mock_uc.return_value.execute_dml.side_effect = Exception('UnityCatalog登録エラー')
        data = make_valid_device_data()

        # Act & Assert: 例外が伝播すること
        with pytest.raises(Exception, match='UnityCatalog登録エラー'):
            create_device(data, user_id=1)

        # Assert: DB への session.add は呼ばれていること（DB は先に処理）
        mock_db.session.add.assert_called_once()
        # Assert: DB delete が呼ばれること（補償トランザクション - UC失敗時にDBから削除）
        mock_db.session.delete.assert_called()
        # Assert: commit が2回呼ばれること（1回目: 通常登録、2回目: delete後のコミット）
        assert mock_db.session.commit.call_count == 2

    @patch(f'{MODULE}.db')
    @patch(f'{MODULE}.DeviceMaster')
    @patch(f'{MODULE}.UnityCatalogConnector')
    def test_create_rollback_on_db_commit_error_no_uc_called(
        self, mock_uc, mock_dm, mock_db
    ):
        """2.3.2: DB commit が失敗した場合、UnityCatalog 登録は呼ばれず DB rollback のみが実行される"""
        # Arrange
        from iot_app.services.device_service import create_device

        mock_dm.query.filter_by.return_value.first.return_value = None
        # DB commit で例外発生（UC はまだ呼ばれていない）
        mock_db.session.commit.side_effect = Exception('DB登録エラー')
        data = make_valid_device_data()

        # Act & Assert: 例外が伝播すること
        with pytest.raises(Exception, match='DB登録エラー'):
            create_device(data, user_id=1)

        # Assert: DB rollback が呼ばれること
        mock_db.session.rollback.assert_called_once()
        # Assert: UnityCatalog への登録は呼ばれないこと（DB commit 失敗のため）
        mock_uc.return_value.execute_dml.assert_not_called()


# ============================================================
# 4. get_device_by_uuid
# 観点: 2.2 対象データ存在チェック（スコープ制限適用）
# ============================================================

@pytest.mark.unit
class TestGetDeviceByUuid:
    """get_device_by_uuid - デバイス参照（スコープ制限適用）
    観点: 2.2 対象データ存在チェック
    スコープ制限は v_device_master_by_user VIEW 経由で user_id を渡すことで自動適用される。
    デバイスが存在しない（またはスコープ外）の場合は None を返す。呼び出し元（View）が abort(404) を担う。
    """

    @patch(f'{MODULE}.db')
    @patch(f'{MODULE}.DeviceMasterByUser')
    def test_get_device_by_uuid_success(self, mock_dbmu, mock_db):
        """2.2.1: 存在するデバイスの場合、DeviceMasterByUser オブジェクトが返される"""
        # Arrange
        from iot_app.services.device_service import get_device_by_uuid

        device = make_device_mock(device_uuid='DEV-001')
        q = make_mock_query()
        q.first.return_value = device
        mock_db.session.query.return_value = q

        # Act: 存在するデバイスを取得
        result = get_device_by_uuid('DEV-001', user_id=1)

        # Assert: デバイスオブジェクトが返されること
        assert result == device

    @patch(f'{MODULE}.db')
    @patch(f'{MODULE}.DeviceMasterByUser')
    def test_get_device_by_uuid_not_found_returns_none(self, mock_dbmu, mock_db):
        """2.2.2: 存在しない device_uuid の場合、None が返される"""
        # Arrange
        from iot_app.services.device_service import get_device_by_uuid

        q = make_mock_query()
        q.first.return_value = None
        mock_db.session.query.return_value = q

        # Act
        result = get_device_by_uuid('NONEXISTENT-001', user_id=1)

        # Assert: None が返されること（呼び出し元が abort(404) を担う）
        assert result is None

    @patch(f'{MODULE}.db')
    @patch(f'{MODULE}.DeviceMasterByUser')
    def test_get_device_by_uuid_deleted_returns_none(self, mock_dbmu, mock_db):
        """2.2.3: 論理削除済みのデバイスは VIEW フィルタで除外され None が返される"""
        # Arrange
        from iot_app.services.device_service import get_device_by_uuid

        q = make_mock_query()
        q.first.return_value = None
        mock_db.session.query.return_value = q

        # Act
        result = get_device_by_uuid('DELETED-001', user_id=1)

        # Assert: None が返されること（論理削除済みは VIEW で除外）
        assert result is None

    @patch(f'{MODULE}.db')
    @patch(f'{MODULE}.DeviceMasterByUser')
    def test_get_device_by_uuid_db_error_raises(self, mock_dbmu, mock_db):
        """1.3.1: DB クエリで例外が発生した場合、例外が伝播し 500 エラーとなる"""
        # Arrange
        from iot_app.services.device_service import get_device_by_uuid

        mock_db.session.query.side_effect = Exception('DB接続エラー')

        # Act & Assert: 例外が呼び出し元へ伝播すること
        with pytest.raises(Exception, match='DB接続エラー'):
            get_device_by_uuid('DEV-001', user_id=1)

    @patch(f'{MODULE}.db')
    @patch(f'{MODULE}.DeviceMasterByUser')
    def test_get_device_by_uuid_scope_out_returns_none(self, mock_dbmu, mock_db):
        """データスコープ: アクセス権限外のデバイスは VIEW 経由で除外され None が返される"""
        # Arrange
        from iot_app.services.device_service import get_device_by_uuid

        q = make_mock_query()
        q.first.return_value = None
        mock_db.session.query.return_value = q

        # Act
        result = get_device_by_uuid('DEV-OTHER-ORG-001', user_id=99)

        # Assert: None が返されること（スコープ外は VIEW で除外）
        assert result is None

    @patch(f'{MODULE}.db')
    @patch(f'{MODULE}.DeviceMasterByUser')
    def test_get_device_by_uuid_returns_all_fields_for_edit(self, mock_dbmu, mock_db):
        """3.3.2.2相当: 取得したデバイスの全フィールド（更新モーダル初期値用）が返り値に含まれる"""
        # Arrange
        from iot_app.services.device_service import get_device_by_uuid

        device = make_device_mock(
            device_uuid='DEV-001',
            device_name='センサー1号機',
            device_type_id=1,
            device_model='MODEL-A100',
            sim_id='SIM-001',
            mac_address='AA:BB:CC:DD:EE:FF',
            device_location='本社1F',
            organization_id=1,
        )
        q = make_mock_query()
        q.first.return_value = device
        mock_db.session.query.return_value = q

        # Act
        result = get_device_by_uuid('DEV-001', user_id=1)

        # Assert: 更新モーダルの初期表示に必要な全フィールドが含まれること
        assert result.device_uuid == 'DEV-001'
        assert result.device_name == 'センサー1号機'
        assert result.device_type_id == 1
        assert result.device_model == 'MODEL-A100'
        assert result.sim_id == 'SIM-001'
        assert result.mac_address == 'AA:BB:CC:DD:EE:FF'
        assert result.device_location == '本社1F'
        assert result.organization_id == 1


# ============================================================
# 5. update_device
# 観点: 3.3.1 更新処理呼び出し, 3.3.2 更新結果, 2.3 副作用チェック
# ============================================================

@pytest.mark.unit
class TestUpdateDevice:
    """update_device - デバイス更新
    観点: 3.3.1 更新処理呼び出し, 3.3.2 更新結果, 2.3 副作用チェック
    """

    @patch(f'{MODULE}.db')
    @patch(f'{MODULE}.DeviceMaster')
    @patch(f'{MODULE}.UnityCatalogConnector')
    def test_update_success(self, mock_uc, mock_dm, mock_db):
        """3.3.2.1: 正常な更新データで処理が完了し、session.commit が呼ばれる"""
        # Arrange
        from iot_app.services.device_service import update_device

        existing_device = make_device_mock(device_uuid='DEV-001')
        # get_device: 対象デバイスが存在する
        mock_dm.query.filter_by.return_value.first.return_value = existing_device
        data = make_valid_device_data(mac_address='BB:CC:DD:EE:FF:AA')

        # Act: 更新実行
        update_device('DEV-001', data, user_id=1)

        # Assert: session.commit が呼ばれること
        mock_db.session.commit.assert_called_once()

    @patch(f'{MODULE}.db')
    @patch(f'{MODULE}.DeviceMaster')
    def test_update_raises_if_mac_address_duplicate_other_device(
        self, mock_dm, mock_db
    ):
        """3.3.1.3: 他デバイスの mac_address と重複する場合、DuplicateMacAddressError がスローされる"""
        # Arrange
        from iot_app.services.device_service import update_device, DuplicateMacAddressError

        existing_device = make_device_mock(device_uuid='DEV-001')
        duplicate_device = make_device_mock(device_uuid='DEV-002')

        call_count = {'count': 0}

        def filter_by_side_effect(**kwargs):
            m = MagicMock()
            call_count['count'] += 1
            if call_count['count'] == 1:
                # get_device: 対象デバイスが存在する
                m.first.return_value = existing_device
            else:
                # mac_address 重複チェック: 他デバイスで使用中
                m.first.return_value = duplicate_device
            return m

        mock_dm.query.filter_by.side_effect = filter_by_side_effect
        data = make_valid_device_data(mac_address='BB:CC:DD:EE:FF:AA')

        # Act & Assert: DuplicateMacAddressError が発生すること
        with pytest.raises(DuplicateMacAddressError):
            update_device('DEV-001', data, user_id=1)

        # Assert: DB への session.commit が呼ばれないこと
        mock_db.session.commit.assert_not_called()

    @patch(f'{MODULE}.db')
    @patch(f'{MODULE}.DeviceMaster')
    def test_update_raises_if_device_not_found(self, mock_dm, mock_db):
        """2.2.2: 更新対象の device_uuid が存在しない場合、NotFoundError がスローされる"""
        # Arrange
        from iot_app.services.device_service import update_device
        from iot_app.common.exceptions import NotFoundError

        mock_dm.query.filter_by.return_value.first.return_value = None
        data = make_valid_device_data()

        # Act & Assert: NotFoundError が発生すること
        with pytest.raises(NotFoundError):
            update_device('NONEXISTENT-001', data, user_id=1)

    @patch(f'{MODULE}.db')
    @patch(f'{MODULE}.DeviceMaster')
    @patch(f'{MODULE}.UnityCatalogConnector')
    def test_update_with_minimal_required_data_passes(self, mock_uc, mock_dm, mock_db):
        """2.1.2: 任意項目をすべて None にした最小構成の入力でも更新が正常終了する"""
        # Arrange
        from iot_app.services.device_service import update_device

        existing_device = make_device_mock(device_uuid='DEV-001')
        mock_dm.query.filter_by.return_value.first.return_value = existing_device
        # 任意項目（device_model/sim_id/mac_address/device_location/certificate_expiration_date）をすべて None
        data = make_valid_device_data(
            device_model=None,
            sim_id=None,
            mac_address=None,
            device_location=None,
            certificate_expiration_date=None,
        )

        # Act: 最小構成で更新実行
        update_device('DEV-001', data, user_id=1)

        # Assert: session.commit が呼ばれること（最小構成でも正常終了）
        mock_db.session.commit.assert_called_once()

    @patch(f'{MODULE}.db')
    @patch(f'{MODULE}.DeviceMaster')
    def test_update_raises_if_device_logically_deleted(self, mock_dm, mock_db):
        """2.2.3: 論理削除済みのデバイスを更新しようとした場合、NotFoundError がスローされる"""
        # Arrange
        from iot_app.services.device_service import update_device
        from iot_app.common.exceptions import NotFoundError

        # delete_flag=True のデバイスはサービス内フィルタ（delete_flag=False）で除外されるため None が返る
        mock_dm.query.filter_by.return_value.first.return_value = None
        data = make_valid_device_data()

        # Act & Assert: NotFoundError が発生すること（論理削除済みは更新不可）
        with pytest.raises(NotFoundError):
            update_device('DELETED-001', data, user_id=1)

    @patch(f'{MODULE}.db')
    @patch(f'{MODULE}.DeviceMaster')
    def test_update_rollback_on_db_error(self, mock_dm, mock_db):
        """2.3.2: DB エラー発生時に rollback が呼ばれる"""
        # Arrange
        from iot_app.services.device_service import update_device

        existing_device = make_device_mock(device_uuid='DEV-001')
        mock_dm.query.filter_by.return_value.first.return_value = existing_device
        mock_db.session.commit.side_effect = Exception('DB error')
        data = make_valid_device_data()

        # Act & Assert: 例外が上位へ伝播すること
        with pytest.raises(Exception):
            update_device('DEV-001', data, user_id=1)

        # Assert: rollback が呼ばれること
        mock_db.session.rollback.assert_called_once()

    @patch(f'{MODULE}.db')
    @patch(f'{MODULE}.DeviceMaster')
    @patch(f'{MODULE}.UnityCatalogConnector')
    def test_update_repository_called_with_target_device_uuid(
        self, mock_uc, mock_dm, mock_db
    ):
        """3.3.2.2: update_device に渡した device_uuid で DB クエリが呼ばれ、指定 ID のデバイスが更新対象となる"""
        # Arrange
        from iot_app.services.device_service import update_device

        existing_device = make_device_mock(device_uuid='DEV-TARGET-001')
        mock_dm.query.filter_by.return_value.first.return_value = existing_device
        data = make_valid_device_data()

        # Act
        update_device('DEV-TARGET-001', data, user_id=1)

        # Assert: filter_by に device_uuid='DEV-TARGET-001' が渡されること
        call_kwargs_list = [
            call[1] for call in mock_dm.query.filter_by.call_args_list
        ]
        assert any(
            kw.get('device_uuid') == 'DEV-TARGET-001'
            for kw in call_kwargs_list
        ), "filter_by(device_uuid='DEV-TARGET-001') が呼ばれていない"

    @patch(f'{MODULE}.db')
    @patch(f'{MODULE}.DeviceMaster')
    def test_update_not_found_does_not_call_repository(
        self, mock_dm, mock_db
    ):
        """2.2.2: 更新対象の device_uuid が存在しない場合、NotFoundError がスローされ session.commit は呼ばれない"""
        # Arrange
        from iot_app.services.device_service import update_device
        from iot_app.common.exceptions import NotFoundError

        # 対象デバイスが見つからない
        mock_dm.query.filter_by.return_value.first.return_value = None
        data = make_valid_device_data()

        # Act & Assert: NotFoundError が発生すること
        with pytest.raises(NotFoundError):
            update_device('NONEXISTENT-001', data, user_id=1)

        # Assert: session.commit が呼ばれないこと（Repository 未呼出）
        mock_db.session.commit.assert_not_called()


# ============================================================
# 6. delete_device
# 観点: 3.4.1 削除処理呼び出し, 3.4.2 削除結果, 2.2 対象データ存在チェック, 2.3 副作用チェック
# ============================================================

@pytest.mark.unit
class TestDeleteDevice:
    """delete_device - デバイス削除（論理削除）
    観点: 3.4.1 削除処理呼び出し, 3.4.2 削除結果, 2.3 副作用チェック
    注: デバイスの存在チェックは呼び出し元（View）が get_device_by_uuid() で実施済み。
        delete_device() には DeviceMasterByUser オブジェクトを渡す。
    """

    @patch(f'{MODULE}.UnityCatalogConnector')
    @patch(f'{MODULE}.db')
    def test_delete_success_calls_commit(self, mock_db, mock_uc):
        """3.4.1.1 / 3.4.2.1: DeviceMasterByUser オブジェクトを渡した場合、論理削除が完了し session.commit が呼ばれる"""
        # Arrange
        from iot_app.services.device_service import delete_device

        device = make_device_mock(device_uuid='DEV-001')
        device.delete_flag = False

        # Act: 論理削除実行（デバイスオブジェクトを直接渡す）
        delete_device(device, deleter_id=1)

        # Assert: session.commit が呼ばれること（論理削除フラグ更新）
        mock_db.session.commit.assert_called_once()

    @patch(f'{MODULE}.UnityCatalogConnector')
    @patch(f'{MODULE}.db')
    def test_delete_rollback_on_db_error(self, mock_db, mock_uc):
        """2.3.2: DB エラー発生時に rollback が呼ばれ、データが更新されない"""
        # Arrange
        from iot_app.services.device_service import delete_device

        device = make_device_mock(device_uuid='DEV-001')
        device.delete_flag = False
        mock_db.session.commit.side_effect = Exception('DB error')

        # Act & Assert: 例外が上位へ伝播すること
        with pytest.raises(Exception):
            delete_device(device, deleter_id=1)

        # Assert: rollback が呼ばれること
        mock_db.session.rollback.assert_called()

    @patch(f'{MODULE}.UnityCatalogConnector')
    @patch(f'{MODULE}.db')
    def test_delete_sets_delete_flag_to_true(self, mock_db, mock_uc):
        """3.4.1.1: 論理削除実行後、デバイスの delete_flag が True に設定される"""
        # Arrange
        from iot_app.services.device_service import delete_device

        device = make_device_mock(device_uuid='DEV-001')
        device.delete_flag = False

        # Act: 論理削除実行
        delete_device(device, deleter_id=1)

        # Assert: delete_flag が True に更新されること（論理削除の実装確認）
        assert device.delete_flag is True

    @patch(f'{MODULE}.UnityCatalogConnector')
    @patch(f'{MODULE}.db')
    def test_delete_unity_catalog_called_before_db_commit(
        self, mock_db, mock_uc
    ):
        """3.4.2.1: UnityCatalog 論理削除が OLTP DB commit より先に呼ばれること（フローの順序保証）"""
        # Arrange
        from iot_app.services.device_service import delete_device

        device = make_device_mock(device_uuid='DEV-001')
        device.delete_flag = False

        call_order = []

        def db_commit(*args, **kwargs):
            call_order.append('db_commit')

        def uc_delete(*args, **kwargs):
            call_order.append('unity_catalog')

        mock_db.session.commit.side_effect = db_commit
        mock_uc.return_value.execute_dml.side_effect = uc_delete

        # Act
        delete_device(device, deleter_id=1)

        # Assert: UnityCatalog 論理削除 → DB commit の順であること
        assert 'unity_catalog' in call_order
        assert 'db_commit' in call_order
        assert call_order.index('unity_catalog') < call_order.index('db_commit')

    @patch(f'{MODULE}.UnityCatalogConnector')
    @patch(f'{MODULE}.db')
    def test_delete_raises_on_unity_catalog_error(
        self, mock_db, mock_uc
    ):
        """2.3.2: UnityCatalog 論理削除が失敗した場合、DB は変更されず例外が伝播する"""
        # Arrange
        from iot_app.services.device_service import delete_device

        device = make_device_mock(device_uuid='DEV-001')
        device.delete_flag = False
        # UC 論理削除で例外発生（DB commit より先）
        mock_uc.return_value.execute_dml.side_effect = Exception('UnityCatalog削除エラー')

        # Act & Assert: 例外が伝播すること
        with pytest.raises(Exception, match='UnityCatalog削除エラー'):
            delete_device(device, deleter_id=1)

        # Assert: DB は変更されていないこと（commit 未実施）
        mock_db.session.commit.assert_not_called()


# ============================================================
# 7. generate_devices_csv
# 観点: 3.5.1 CSV生成ロジック, 3.5.2 エスケープ処理, 3.5.3 エンコーディング処理
# ============================================================

@pytest.mark.unit
class TestGenerateDevicesCsv:
    """generate_devices_csv - CSVエクスポート
    観点: 3.5.1 CSV生成ロジック, 3.5.2 エスケープ処理, 3.5.3 エンコーディング処理
    入力: (device, org_name, type_name, last_received_time) タプルのリスト
    """

    def test_csv_starts_with_bom(self):
        """3.5.3.1: 生成された CSV の先頭に UTF-8 BOM（EF BB BF）が付与される"""
        # Arrange
        from iot_app.services.device_service import generate_devices_csv

        devices = [make_device_row()]

        # Act: CSV 生成実行
        csv_bytes = generate_devices_csv(devices)

        # Assert: BOM が先頭に存在すること
        assert csv_bytes[:3] == b'\xef\xbb\xbf'

    def test_csv_contains_header_row(self):
        """3.5.1.1: 生成された CSV にヘッダー行が出力される"""
        # Arrange
        from iot_app.services.device_service import generate_devices_csv

        devices = [make_device_row()]

        # Act: CSV 生成実行
        csv_bytes = generate_devices_csv(devices)
        csv_text = csv_bytes.decode('utf-8-sig')

        # Assert: ヘッダー行に必須カラム名が含まれること
        assert 'デバイスID' in csv_text
        assert 'デバイス名' in csv_text
        assert 'ステータス' in csv_text

    def test_csv_column_order_follows_spec(self):
        """3.5.1.4: CSV の先頭カラムが仕様通りである（デバイスID が最初）"""
        # Arrange
        from iot_app.services.device_service import generate_devices_csv

        devices = [make_device_row()]

        # Act: CSV 生成実行
        csv_bytes = generate_devices_csv(devices)
        csv_text = csv_bytes.decode('utf-8-sig')
        header_line = csv_text.splitlines()[0]

        # Assert: 先頭カラムが デバイスID であること
        first_column = header_line.split(',')[0]
        assert first_column == 'デバイスID'

    def test_csv_data_rows_output_all_devices(self):
        """3.5.1.2: 複数件のデータリストを渡した場合、全件が CSV 行として出力される"""
        # Arrange
        from iot_app.services.device_service import generate_devices_csv

        row1 = make_device_row(device_uuid='DEV-001', device_name='センサー1')
        row2 = make_device_row(device_uuid='DEV-002', device_name='センサー2')
        devices = [row1, row2]

        # Act: CSV 生成実行（2件）
        csv_bytes = generate_devices_csv(devices)
        csv_text = csv_bytes.decode('utf-8-sig')
        lines = [l for l in csv_text.splitlines() if l]   # 空行除外

        # Assert: ヘッダー1行 + データ2行 = 合計3行であること
        assert len(lines) == 3

    def test_csv_empty_list_outputs_header_only(self):
        """3.5.1.3: 空リストを渡した場合、ヘッダー行のみ出力される"""
        # Arrange
        from iot_app.services.device_service import generate_devices_csv

        devices = []

        # Act: CSV 生成実行（0件）
        csv_bytes = generate_devices_csv(devices)
        csv_text = csv_bytes.decode('utf-8-sig')
        lines = [l for l in csv_text.splitlines() if l]   # 空行除外

        # Assert: ヘッダー行のみ（1行）であること
        assert len(lines) == 1
        assert 'デバイスID' in lines[0]

    def test_csv_comma_in_data_is_escaped(self):
        """3.5.2.1: データにカンマが含まれる場合、ダブルクォートで囲まれる"""
        # Arrange
        from iot_app.services.device_service import generate_devices_csv

        row = make_device_row(device_name='センサー,1号機')
        devices = [row]

        # Act: CSV 生成実行
        csv_bytes = generate_devices_csv(devices)
        csv_text = csv_bytes.decode('utf-8-sig')

        # Assert: カンマを含むフィールドがダブルクォートで囲まれること
        assert '"センサー,1号機"' in csv_text

    def test_csv_newline_in_data_is_escaped(self):
        """3.5.2.2: データに改行が含まれる場合、ダブルクォートで囲まれる"""
        # Arrange
        from iot_app.services.device_service import generate_devices_csv

        row = make_device_row(device_name='センサー\n1号機')
        devices = [row]

        # Act: CSV 生成実行
        csv_bytes = generate_devices_csv(devices)
        csv_text = csv_bytes.decode('utf-8-sig')

        # Assert: 改行を含むフィールドがダブルクォートで囲まれること
        assert '"センサー\n1号機"' in csv_text

    def test_csv_double_quote_in_data_is_escaped(self):
        """3.5.2.3: データにダブルクォートが含まれる場合、\"\"\"\"でエスケープされる"""
        # Arrange
        from iot_app.services.device_service import generate_devices_csv

        row = make_device_row(device_name='センサー"A"')
        devices = [row]

        # Act: CSV 生成実行
        csv_bytes = generate_devices_csv(devices)
        csv_text = csv_bytes.decode('utf-8-sig')

        # Assert: ダブルクォートが "" にエスケープされること
        assert '""' in csv_text

    def test_csv_normal_data_no_extra_escaping(self):
        """3.5.2.4: 特殊文字を含まないデータはそのまま出力される"""
        # Arrange
        from iot_app.services.device_service import generate_devices_csv

        row = make_device_row(device_uuid='DEV-001', device_name='センサー1')
        devices = [row]

        # Act: CSV 生成実行
        csv_bytes = generate_devices_csv(devices)
        csv_text = csv_bytes.decode('utf-8-sig')

        # Assert: エスケープなしでそのまま出力されること
        assert 'DEV-001' in csv_text
        assert 'センサー1' in csv_text

    def test_csv_japanese_characters_encoded_correctly(self):
        """3.5.3.2: 日本語データが文字化けなく正しく出力される"""
        # Arrange
        from iot_app.services.device_service import generate_devices_csv

        row = make_device_row(device_name='温度センサー1号機', device_location='本社ビル1階')
        devices = [row]

        # Act: CSV 生成実行
        csv_bytes = generate_devices_csv(devices)

        # Assert: UTF-8 BOM 付きでデコードした場合に日本語が正しく読める
        csv_text = csv_bytes.decode('utf-8-sig')
        assert '温度センサー1号機' in csv_text

    def test_csv_emoji_characters_encoded_correctly(self):
        """3.5.3.3: 絵文字等の特殊文字を含むデータが文字化けなく正しく出力される"""
        # Arrange
        from iot_app.services.device_service import generate_devices_csv

        row = make_device_row(device_name='🌡️温度センサー', device_location='🏢本社ビル')
        devices = [row]

        # Act: CSV 生成実行
        csv_bytes = generate_devices_csv(devices)

        # Assert: UTF-8 BOM 付きでデコードした場合に絵文字が文字化けなく読める
        csv_text = csv_bytes.decode('utf-8-sig')
        assert '🌡️温度センサー' in csv_text
        assert '🏢本社ビル' in csv_text

    def test_csv_header_contains_all_columns(self):
        """3.5.1.1: ヘッダー行に仕様で定義された全7列のカラム名が出力される"""
        # Arrange
        from iot_app.services.device_service import generate_devices_csv

        devices = [make_device_row()]

        # Act: CSV 生成実行
        csv_bytes = generate_devices_csv(devices)
        csv_text = csv_bytes.decode('utf-8-sig')
        header_line = csv_text.splitlines()[0]

        # Assert: 全7列のカラム名がヘッダーに含まれること
        expected_columns = [
            'デバイスID',
            'デバイス名',
            'デバイス種別',
            '設置場所',
            '所属組織',
            '証明書期限',
            'ステータス',
        ]
        for col in expected_columns:
            assert col in header_line, f"ヘッダーに '{col}' が含まれていない"

    def test_csv_column_order_all_columns(self):
        """3.5.1.4: CSV のカラム順序が仕様通りであること（全7列の順序を検証）"""
        # Arrange
        from iot_app.services.device_service import generate_devices_csv

        devices = [make_device_row()]

        # Act: CSV 生成実行
        csv_bytes = generate_devices_csv(devices)
        csv_text = csv_bytes.decode('utf-8-sig')
        header_columns = csv_text.splitlines()[0].split(',')

        # Assert: 全7列が仕様通りの順序で並ぶこと
        expected_order = [
            'デバイスID',
            'デバイス名',
            'デバイス種別',
            '設置場所',
            '所属組織',
            '証明書期限',
            'ステータス',
        ]
        assert header_columns == expected_order

    def test_csv_none_optional_fields_output_as_empty_string(self):
        """3.5.1.2: 任意項目（device_location/certificate_expiration_date）が None の場合、空文字として出力される"""
        # Arrange
        from iot_app.services.device_service import generate_devices_csv

        row = make_device_row(
            device_uuid='DEV-001',
            device_name='センサー1',
            device_location=None,
            certificate_expiration_date=None,
            organization_name=None,
            device_type_name=None,
        )
        devices = [row]

        # Act: CSV 生成実行
        csv_bytes = generate_devices_csv(devices)
        csv_text = csv_bytes.decode('utf-8-sig')
        data_line = csv_text.splitlines()[1]   # ヘッダーの次の行

        # Assert: None フィールドが空文字（連続カンマ）として出力されること
        assert 'None' not in data_line, "None がそのまま文字列として出力されている"



# ============================================================
# 8. get_device_form_options
# 観点: 2.1 正常系処理, 1.3.1 例外伝播, 3.1.4.2 空結果
# ============================================================

@pytest.mark.unit
class TestGetDeviceFormOptions:
    """get_device_form_options - 登録モーダル表示用フォームオプション取得テスト
    観点: 2.1 正常系処理（有効な入力データ）, 1.3.1 例外伝播, 3.1.4.2 空結果
    """

    def test_get_form_options_returns_device_types_orgs_and_sort_items(self):
        """2.1.1: 正常ケース - デバイス種別・組織・ソート項目の3要素タプルが返される"""
        # Arrange
        from iot_app.services.device_service import get_device_form_options

        mock_org1 = MagicMock()
        mock_org1.organization_id = 1
        mock_org1.organization_name = '本社'

        mock_dt1 = MagicMock()
        mock_dt1.device_type_id = 1
        mock_dt1.device_type_name = 'センサー'

        mock_sort1 = MagicMock()
        mock_sort1.sort_item_id = 1
        mock_sort1.sort_item_name = 'デバイス名'

        with patch(f'{MODULE}.OrganizationMasterByUser') as mock_org_model, \
             patch(f'{MODULE}.DeviceTypeMaster') as mock_dt_model, \
             patch(f'{MODULE}.SortItem') as mock_sort_model, \
             patch(f'{MODULE}.db') as mock_db:
            q_dt = make_mock_query()
            q_dt.all.return_value = [mock_dt1]
            q_org = make_mock_query()
            q_org.all.return_value = [mock_org1]
            q_sort = make_mock_query()
            q_sort.all.return_value = [mock_sort1]
            mock_db.session.query.side_effect = [q_dt, q_org, q_sort]

            # Act
            device_types, orgs, sort_items = get_device_form_options(user_id=1)

        # Assert: デバイス種別・組織・ソート項目リストが返される
        assert device_types == [mock_dt1]
        assert orgs == [mock_org1]
        assert sort_items == [mock_sort1]

    def test_get_form_options_loads_scoped_organizations_via_view(self):
        """3.1.1.1: OrganizationMasterByUser VIEW を使用し、user_id でスコープされた組織が取得される"""
        # Arrange
        from iot_app.services.device_service import get_device_form_options

        mock_scoped_org = MagicMock()
        mock_scoped_org.organization_id = 5

        with patch(f'{MODULE}.OrganizationMasterByUser') as mock_org_model, \
             patch(f'{MODULE}.DeviceTypeMaster') as mock_dt_model, \
             patch(f'{MODULE}.SortItem') as mock_sort_model, \
             patch(f'{MODULE}.db') as mock_db:
            q_dt = make_mock_query()
            q_org = make_mock_query()
            q_org.all.return_value = [mock_scoped_org]
            q_sort = make_mock_query()
            mock_db.session.query.side_effect = [q_dt, q_org, q_sort]

            # Act
            _, orgs, _ = get_device_form_options(user_id=5)

        # Assert: VIEW 経由で取得したスコープ済み組織リストが返される
        assert orgs == [mock_scoped_org]

    def test_get_form_options_loads_sort_items(self):
        """2.1.1: SortItem が取得され、ソート項目リストとして返される"""
        # Arrange
        from iot_app.services.device_service import get_device_form_options

        mock_sort1 = MagicMock()
        mock_sort1.sort_item_id = 1
        mock_sort2 = MagicMock()
        mock_sort2.sort_item_id = 2

        with patch(f'{MODULE}.OrganizationMasterByUser') as mock_org_model, \
             patch(f'{MODULE}.DeviceTypeMaster') as mock_dt_model, \
             patch(f'{MODULE}.SortItem') as mock_sort_model, \
             patch(f'{MODULE}.db') as mock_db:
            q_dt = make_mock_query()
            q_org = make_mock_query()
            q_sort = make_mock_query()
            q_sort.all.return_value = [mock_sort1, mock_sort2]
            mock_db.session.query.side_effect = [q_dt, q_org, q_sort]

            # Act
            _, _, sort_items = get_device_form_options(user_id=1)

        # Assert: ソート項目リストが返される
        assert sort_items == [mock_sort1, mock_sort2]

    def test_get_form_options_organization_db_error_raises(self):
        """1.3.1: 組織マスタのDB取得中に例外が発生した場合、例外がそのまま伝播する"""
        # Arrange
        from iot_app.services.device_service import get_device_form_options

        with patch(f'{MODULE}.OrganizationMasterByUser') as mock_org_model, \
             patch(f'{MODULE}.DeviceTypeMaster') as mock_dt_model, \
             patch(f'{MODULE}.SortItem') as mock_sort_model, \
             patch(f'{MODULE}.db') as mock_db:
            mock_db.session.query.side_effect = Exception('DB接続エラー')

            # Act / Assert: 例外が呼び出し元に伝播すること
            with pytest.raises(Exception, match='DB接続エラー'):
                get_device_form_options(user_id=1)

    def test_get_form_options_device_type_db_error_raises(self):
        """1.3.1: デバイス種別マスタのDB取得中に例外が発生した場合、例外がそのまま伝播する"""
        # Arrange
        from iot_app.services.device_service import get_device_form_options

        with patch(f'{MODULE}.OrganizationMasterByUser') as mock_org_model, \
             patch(f'{MODULE}.DeviceTypeMaster') as mock_dt_model, \
             patch(f'{MODULE}.SortItem') as mock_sort_model, \
             patch(f'{MODULE}.db') as mock_db:
            q_dt = make_mock_query()
            mock_db.session.query.side_effect = [q_dt, Exception('デバイス種別DB取得エラー')]

            # Act / Assert: 例外が呼び出し元に伝播すること
            with pytest.raises(Exception, match='デバイス種別DB取得エラー'):
                get_device_form_options(user_id=1)

    def test_get_form_options_returns_empty_lists_when_no_data(self):
        """3.1.4.2: 組織・デバイス種別・ソート項目が0件の場合、空リストが返される"""
        # Arrange
        from iot_app.services.device_service import get_device_form_options

        with patch(f'{MODULE}.OrganizationMasterByUser') as mock_org_model, \
             patch(f'{MODULE}.DeviceTypeMaster') as mock_dt_model, \
             patch(f'{MODULE}.SortItem') as mock_sort_model, \
             patch(f'{MODULE}.db') as mock_db:
            q_dt = make_mock_query()
            q_dt.all.return_value = []
            q_org = make_mock_query()
            q_org.all.return_value = []
            q_sort = make_mock_query()
            q_sort.all.return_value = []
            mock_db.session.query.side_effect = [q_dt, q_org, q_sort]

            # Act
            device_types, orgs, sort_items = get_device_form_options(user_id=1)

        # Assert: 空リストが返されること
        assert device_types == []
        assert orgs == []
        assert sort_items == []


# ============================================================
# TestGetAllDevicesForExport
# ============================================================

@pytest.mark.unit
class TestGetAllDevicesForExport:
    """get_all_devices_for_export のテスト"""

    def test_get_all_returns_all_when_no_filter(self):
        """3.1.6.1: フィルタなし・全件返却"""
        # Arrange
        from iot_app.services.device_service import get_all_devices_for_export

        expected = [make_device_row()]

        with patch(f'{MODULE}.db') as mock_db:
            q = make_mock_query()
            q.all.return_value = expected
            mock_db.session.query.return_value = q

            # Act
            result = get_all_devices_for_export(make_default_search_params(), user_id=1)

        # Assert
        assert result == expected

    def test_get_all_filters_by_device_id(self):
        """3.1.6.1: device_id 指定時に LIKE フィルタが適用される"""
        # Arrange
        from iot_app.services.device_service import get_all_devices_for_export

        with patch(f'{MODULE}.db') as mock_db:
            q = make_mock_query()
            mock_db.session.query.return_value = q

            # Act
            get_all_devices_for_export(
                make_default_search_params(device_id='DEV-001'), user_id=1
            )

        # Assert: filter が呼ばれること
        q.filter.assert_called()

    def test_get_all_filters_by_device_name(self):
        """3.1.6.1: device_name 指定時に LIKE フィルタが適用される"""
        # Arrange
        from iot_app.services.device_service import get_all_devices_for_export

        with patch(f'{MODULE}.db') as mock_db:
            q = make_mock_query()
            mock_db.session.query.return_value = q

            # Act
            get_all_devices_for_export(
                make_default_search_params(device_name='センサー'), user_id=1
            )

        # Assert
        q.filter.assert_called()

    def test_get_all_filters_by_device_type_id(self):
        """3.1.6.1: device_type_id 指定時にフィルタが適用される"""
        # Arrange
        from iot_app.services.device_service import get_all_devices_for_export

        with patch(f'{MODULE}.db') as mock_db:
            q = make_mock_query()
            mock_db.session.query.return_value = q

            # Act
            get_all_devices_for_export(
                make_default_search_params(device_type_id=2), user_id=1
            )

        # Assert
        q.filter.assert_called()

    def test_get_all_filters_by_location(self):
        """3.1.6.1: location 指定時に LIKE フィルタが適用される"""
        # Arrange
        from iot_app.services.device_service import get_all_devices_for_export

        with patch(f'{MODULE}.db') as mock_db:
            q = make_mock_query()
            mock_db.session.query.return_value = q

            # Act
            get_all_devices_for_export(
                make_default_search_params(location='東京'), user_id=1
            )

        # Assert
        q.filter.assert_called()

    def test_get_all_filters_by_organization_id(self):
        """3.1.6.1: organization_id 指定時にフィルタが適用される"""
        # Arrange
        from iot_app.services.device_service import get_all_devices_for_export

        with patch(f'{MODULE}.db') as mock_db:
            q = make_mock_query()
            mock_db.session.query.return_value = q

            # Act
            get_all_devices_for_export(
                make_default_search_params(organization_id=3), user_id=1
            )

        # Assert
        q.filter.assert_called()

    def test_get_all_filters_by_certificate_expiration_date(self):
        """3.1.6.1: certificate_expiration_date 指定時にフィルタが適用される"""
        # Arrange
        from iot_app.services.device_service import get_all_devices_for_export

        with patch(f'{MODULE}.db') as mock_db:
            q = make_mock_query()
            mock_db.session.query.return_value = q

            # Act
            get_all_devices_for_export(
                make_default_search_params(certificate_expiration_date='2025-12-31'), user_id=1
            )

        # Assert
        q.filter.assert_called()

    def test_get_all_filters_by_status_connected(self, app):
        """3.1.6.1: status='connected' 指定時に接続済み閾値フィルタが適用される"""
        from iot_app.services.device_service import get_all_devices_for_export

        app.config['DEVICE_DATA_INTERVAL_SECONDS'] = 300
        with app.app_context():
            with patch(f'{MODULE}.db') as mock_db:
                q = make_mock_query()
                mock_db.session.query.return_value = q

                get_all_devices_for_export(
                    make_default_search_params(status='connected'), user_id=1
                )

        q.filter.assert_called()

    def test_get_all_filters_by_status_disconnected(self, app):
        """3.1.6.1: status='disconnected' 指定時に未接続閾値フィルタが適用される"""
        from iot_app.services.device_service import get_all_devices_for_export

        app.config['DEVICE_DATA_INTERVAL_SECONDS'] = 300
        with app.app_context():
            with patch(f'{MODULE}.db') as mock_db:
                q = make_mock_query()
                mock_db.session.query.return_value = q

                get_all_devices_for_export(
                    make_default_search_params(status='disconnected'), user_id=1
                )

        q.filter.assert_called()

    def test_get_all_returns_empty_when_no_match(self):
        """3.1.4.2: 条件に合致するデバイスがない場合は空リストが返される"""
        # Arrange
        from iot_app.services.device_service import get_all_devices_for_export

        with patch(f'{MODULE}.db') as mock_db:
            q = make_mock_query()
            q.all.return_value = []
            mock_db.session.query.return_value = q

            # Act
            result = get_all_devices_for_export(make_default_search_params(), user_id=1)

        # Assert
        assert result == []

    def test_get_all_db_error_propagates(self):
        """1.3.1: DB エラーが呼び出し元に伝播する"""
        # Arrange
        from iot_app.services.device_service import get_all_devices_for_export

        with patch(f'{MODULE}.db') as mock_db:
            mock_db.session.query.side_effect = Exception('DB接続エラー')

            # Act / Assert
            with pytest.raises(Exception, match='DB接続エラー'):
                get_all_devices_for_export(make_default_search_params(), user_id=1)


# ============================================================
# TestGetDeviceStatusLabel
# ============================================================

@pytest.mark.unit
class TestGetDeviceStatusLabel:
    """_get_device_status_label のテスト"""

    def test_returns_disconnected_when_none(self):
        """3.1.7.1: last_received_time が None の場合は '未接続' を返す"""
        from iot_app.services.device_service import _get_device_status_label

        result = _get_device_status_label(None)

        assert result == '未接続'

    def test_returns_connected_when_within_threshold(self, app):
        """3.1.7.1: elapsed <= threshold * 2 の場合は '接続済み' を返す"""
        from iot_app.services.device_service import _get_device_status_label
        from datetime import datetime, timezone, timedelta

        threshold = 300
        now = datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        last_received_time = now - timedelta(seconds=300)  # elapsed=300 <= 600

        app.config['DEVICE_DATA_INTERVAL_SECONDS'] = threshold
        with app.app_context():
            with patch(f'{MODULE}.datetime') as mock_dt:
                mock_dt.now.return_value = now
                result = _get_device_status_label(last_received_time)

        assert result == '接続済み'

    def test_returns_disconnected_when_exceeds_threshold(self, app):
        """3.1.7.2: elapsed > threshold * 2 の場合は '未接続' を返す"""
        from iot_app.services.device_service import _get_device_status_label
        from datetime import datetime, timezone, timedelta

        threshold = 300
        now = datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        last_received_time = now - timedelta(seconds=700)  # elapsed=700 > 600

        app.config['DEVICE_DATA_INTERVAL_SECONDS'] = threshold
        with app.app_context():
            with patch(f'{MODULE}.datetime') as mock_dt:
                mock_dt.now.return_value = now
                result = _get_device_status_label(last_received_time)

        assert result == '未接続'

    def test_returns_connected_at_exact_threshold(self, app):
        """3.1.7.3: elapsed = threshold * 2 の場合は '接続済み' を返す（境界値）"""
        from iot_app.services.device_service import _get_device_status_label
        from datetime import datetime, timezone, timedelta

        threshold = 300
        now = datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        last_received_time = now - timedelta(seconds=600)  # elapsed=600 == 600

        app.config['DEVICE_DATA_INTERVAL_SECONDS'] = threshold
        with app.app_context():
            with patch(f'{MODULE}.datetime') as mock_dt:
                mock_dt.now.return_value = now
                result = _get_device_status_label(last_received_time)

        assert result == '接続済み'

    def test_returns_disconnected_just_over_threshold(self, app):
        """3.1.7.4: elapsed = threshold * 2 + 1 の場合は '未接続' を返す（境界値）"""
        from iot_app.services.device_service import _get_device_status_label
        from datetime import datetime, timezone, timedelta

        threshold = 300
        now = datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        last_received_time = now - timedelta(seconds=601)  # elapsed=601 > 600

        app.config['DEVICE_DATA_INTERVAL_SECONDS'] = threshold
        with app.app_context():
            with patch(f'{MODULE}.datetime') as mock_dt:
                mock_dt.now.return_value = now
                result = _get_device_status_label(last_received_time)

        assert result == '未接続'
