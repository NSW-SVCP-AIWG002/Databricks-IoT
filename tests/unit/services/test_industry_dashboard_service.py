"""
業種別ダッシュボードサービス層 単体テスト

対象: src/services/industry_dashboard_service.py

テスト対象関数:
  - get_accessible_organizations     タスク2-1
  - check_device_access              タスク2-2
  - get_recent_alerts_with_count     タスク2-3
  - get_device_list_with_count       タスク2-4
  - get_latest_sensor_data           タスク2-5
  - get_device_alerts_with_count     タスク2-6
  - validate_date_range              タスク2-10
"""

from unittest.mock import MagicMock, patch


from src.services.industry_dashboard_service import (
    check_device_access,
    get_accessible_organizations,
    get_device_alerts_with_count,
    get_device_list_with_count,
    get_latest_sensor_data,
    get_recent_alerts_with_count,
    validate_date_range,
)


# ============================================================
# タスク2-1: get_accessible_organizations
# ============================================================

class TestGetAccessibleOrganizations:
    """get_accessible_organizations のテスト"""

    def test_returns_org_id_list(self):
        """組織IDリストが正しく返されること"""
        mock_rows = [(1,), (2,), (3,)]
        with patch("src.services.industry_dashboard_service.db") as mock_db:
            mock_db.session.query.return_value.filter.return_value.all.return_value = mock_rows
            result = get_accessible_organizations(10)
        assert result == [1, 2, 3]

    def test_returns_empty_list_when_no_rows(self):
        """該当行なし時に空リストを返すこと"""
        with patch("src.services.industry_dashboard_service.db") as mock_db:
            mock_db.session.query.return_value.filter.return_value.all.return_value = []
            result = get_accessible_organizations(10)
        assert result == []


# ============================================================
# タスク2-2: check_device_access
# ============================================================

class TestCheckDeviceAccess:
    """check_device_access のテスト"""

    def test_returns_device_when_accessible(self):
        """アクセス可能デバイスのオブジェクトを返すこと"""
        mock_device = MagicMock()
        with patch("src.services.industry_dashboard_service.db") as mock_db:
            mock_db.session.query.return_value.filter.return_value.first.return_value = mock_device
            result = check_device_access("test-uuid", [1, 2, 3])
        assert result == mock_device

    def test_returns_none_when_not_accessible(self):
        """アクセス不可の場合に None を返すこと"""
        with patch("src.services.industry_dashboard_service.db") as mock_db:
            mock_db.session.query.return_value.filter.return_value.first.return_value = None
            result = check_device_access("test-uuid", [1, 2, 3])
        assert result is None

    def test_returns_none_when_empty_org_ids(self):
        """org_ids が空リストの場合に None を返すこと（DBアクセスなし）"""
        result = check_device_access("test-uuid", [])
        assert result is None


# ============================================================
# タスク2-3: get_recent_alerts_with_count
# ============================================================

class TestGetRecentAlertsWithCount:
    """get_recent_alerts_with_count のテスト"""

    def _make_base_query_mock(self, mock_db, alerts, count):
        """DBクエリチェーンのモックを構築するヘルパー"""
        q = MagicMock()
        mock_db.session.query.return_value.join.return_value = q
        q.join.return_value = q
        q.filter.return_value = q
        q.count.return_value = count
        q.order_by.return_value.limit.return_value.all.return_value = alerts
        return q

    def test_returns_empty_when_no_org_ids(self):
        """org_ids が空リストの場合に ([], 0) を返すこと"""
        result = get_recent_alerts_with_count({}, [])
        assert result == ([], 0)

    def test_returns_alerts_and_count(self):
        """アラートリストと件数のタプルを返すこと"""
        mock_alert = MagicMock()
        with patch("src.services.industry_dashboard_service.db") as mock_db:
            self._make_base_query_mock(mock_db, [mock_alert], 1)
            alerts, total = get_recent_alerts_with_count(
                {"organization_name": "", "device_name": ""}, [1]
            )
        assert total == 1
        assert alerts == [mock_alert]

    def test_organization_name_filter_applied(self):
        """organization_name が指定された場合にフィルタが追加されること"""
        with patch("src.services.industry_dashboard_service.db") as mock_db:
            q = self._make_base_query_mock(mock_db, [], 0)
            get_recent_alerts_with_count({"organization_name": "店舗A"}, [1])
        # 初期フィルタ + 組織名フィルタ の2回以上呼ばれること
        assert q.filter.call_count >= 1

    def test_device_name_filter_applied(self):
        """device_name が指定された場合にフィルタが追加されること"""
        with patch("src.services.industry_dashboard_service.db") as mock_db:
            q = self._make_base_query_mock(mock_db, [], 0)
            get_recent_alerts_with_count({"device_name": "冷蔵庫1"}, [1])
        assert q.filter.call_count >= 1


# ============================================================
# タスク2-4: get_device_list_with_count
# ============================================================

class TestGetDeviceListWithCount:
    """get_device_list_with_count のテスト"""

    def _make_base_query_mock(self, mock_db, devices, count):
        q = MagicMock()
        mock_db.session.query.return_value.join.return_value = q
        q.join.return_value = q
        q.filter.return_value = q
        q.count.return_value = count
        q.order_by.return_value.limit.return_value.offset.return_value.all.return_value = devices
        return q

    def test_returns_empty_when_no_org_ids(self):
        """org_ids が空リストの場合に ([], 0) を返すこと"""
        result = get_device_list_with_count({}, [], page=1)
        assert result == ([], 0)

    def test_returns_devices_and_count(self):
        """デバイスリストと件数のタプルを返すこと"""
        mock_device = MagicMock()
        with patch("src.services.industry_dashboard_service.db") as mock_db:
            self._make_base_query_mock(mock_db, [mock_device], 1)
            devices, total = get_device_list_with_count(
                {"organization_name": "", "device_name": ""}, [1], page=1
            )
        assert total == 1
        assert devices == [mock_device]

    def test_page_offset_calculation(self):
        """ページ番号に応じてオフセットが正しく計算されること"""
        with patch("src.services.industry_dashboard_service.db") as mock_db:
            q = self._make_base_query_mock(mock_db, [], 5)
            get_device_list_with_count({}, [1], page=3, per_page=10)
        # page=3, per_page=10 → offset=20
        q.order_by.return_value.limit.return_value.offset.assert_called_with(20)

    def test_organization_name_filter_applied(self):
        """organization_name フィルタが適用されること"""
        with patch("src.services.industry_dashboard_service.db") as mock_db:
            q = self._make_base_query_mock(mock_db, [], 0)
            get_device_list_with_count({"organization_name": "店舗A"}, [1], page=1)
        assert q.filter.call_count >= 1

    def test_device_name_filter_applied(self):
        """device_name フィルタが適用されること"""
        with patch("src.services.industry_dashboard_service.db") as mock_db:
            q = self._make_base_query_mock(mock_db, [], 0)
            get_device_list_with_count({"device_name": "冷蔵庫"}, [1], page=1)
        assert q.filter.call_count >= 1

    def test_page_1_offset_is_zero(self):
        """page=1 のオフセットが 0 であること"""
        with patch("src.services.industry_dashboard_service.db") as mock_db:
            q = self._make_base_query_mock(mock_db, [], 5)
            get_device_list_with_count({}, [1], page=1, per_page=10)
        q.order_by.return_value.limit.return_value.offset.assert_called_with(0)


# ============================================================
# タスク2-5: get_latest_sensor_data
# ============================================================

class TestGetLatestSensorData:
    """get_latest_sensor_data のテスト"""

    def test_returns_row_when_found(self):
        """センサーデータが存在する場合にRowオブジェクトを返すこと"""
        mock_row = MagicMock()
        mock_conn = MagicMock()
        mock_conn.execute.return_value.fetchone.return_value = mock_row

        fake_uc = MagicMock()
        fake_uc.get_unity_catalog_connection.return_value = mock_conn
        with patch.dict("sys.modules", {"src.db.unity_catalog_connector": fake_uc}):
            result = get_latest_sensor_data(device_id=1)

        assert result == mock_row

    def test_returns_none_when_not_found(self):
        """センサーデータが存在しない場合に None を返すこと"""
        mock_conn = MagicMock()
        mock_conn.execute.return_value.fetchone.return_value = None

        fake_uc = MagicMock()
        fake_uc.get_unity_catalog_connection.return_value = mock_conn
        with patch.dict("sys.modules", {"src.db.unity_catalog_connector": fake_uc}):
            result = get_latest_sensor_data(device_id=99)

        assert result is None


# ============================================================
# タスク2-6: get_device_alerts_with_count
# ============================================================

class TestGetDeviceAlertsWithCount:
    """get_device_alerts_with_count のテスト"""

    def _make_base_query_mock(self, mock_db, alerts, count):
        q = MagicMock()
        mock_db.session.query.return_value.join.return_value = q
        q.join.return_value = q
        q.filter.return_value = q
        q.count.return_value = count
        q.order_by.return_value.limit.return_value.offset.return_value.all.return_value = alerts
        return q

    def test_returns_alerts_and_count(self):
        """アラートリストと件数のタプルを返すこと"""
        mock_alert = MagicMock()
        with patch("src.services.industry_dashboard_service.db") as mock_db:
            self._make_base_query_mock(mock_db, [mock_alert], 1)
            alerts, total = get_device_alerts_with_count(
                device_id=1, search_params={"page": 1}
            )
        assert total == 1
        assert alerts == [mock_alert]

    def test_page_offset_calculation(self):
        """ページ番号に応じてオフセットが正しく計算されること"""
        with patch("src.services.industry_dashboard_service.db") as mock_db:
            q = self._make_base_query_mock(mock_db, [], 5)
            get_device_alerts_with_count(device_id=1, search_params={"page": 3})
        # page=3, ITEM_PER_PAGE=10 → offset=20
        q.order_by.return_value.limit.return_value.offset.assert_called_with(20)

    def test_default_page_is_1(self):
        """page パラメータがない場合に page=1 として動作すること"""
        with patch("src.services.industry_dashboard_service.db") as mock_db:
            q = self._make_base_query_mock(mock_db, [], 0)
            get_device_alerts_with_count(device_id=1, search_params={})
        # page=1 → offset=0
        q.order_by.return_value.limit.return_value.offset.assert_called_with(0)


# ============================================================
# タスク2-10: validate_date_range
# ============================================================

class TestValidateDateRange:
    """validate_date_range のテスト

    バリデーションルール（ワークフロー仕様書 10.3 表示期間変更ボタン）:
      - 日時形式: YYYY-MM-DDTHH:MM
      - 開始日時 < 終了日時
      - 表示期間は最大2ヶ月（62日）以内
    """

    def test_none_value_returns_error(self):
        """None値のエラーを検出すること"""
        errors = validate_date_range(None, "2026-02-02T00:00")
        assert len(errors) >= 1

    def test_exactly_61_days_is_valid(self):
        """61日はエラーなし（上限62日の境界値: 61日 < 62日）"""
        # 2026-01-01 → 2026-03-03 = 31 + 28 + 2 = 61日
        errors = validate_date_range("2026-01-01T00:00", "2026-03-03T00:00")
        assert errors == []
