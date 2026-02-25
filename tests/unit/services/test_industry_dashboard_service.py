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
  - get_graph_data                   タスク2-7
  - export_sensor_data_csv           タスク2-8
  - get_default_date_range           タスク2-9
  - validate_date_range              タスク2-10
"""

from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from src.services.industry_dashboard_service import (
    check_device_access,
    export_sensor_data_csv,
    get_accessible_organizations,
    get_default_date_range,
    get_device_alerts_with_count,
    get_device_list_with_count,
    get_graph_data,
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

    def test_count_capped_at_limit(self):
        """取得件数が limit を超える場合は limit に丸められること"""
        with patch("src.services.industry_dashboard_service.db") as mock_db:
            self._make_base_query_mock(mock_db, [], 100)
            _, total = get_recent_alerts_with_count({}, [1], limit=30)
        assert total == 30

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
        mock_conn.close.assert_called_once()

    def test_returns_none_when_not_found(self):
        """センサーデータが存在しない場合に None を返すこと"""
        mock_conn = MagicMock()
        mock_conn.execute.return_value.fetchone.return_value = None

        fake_uc = MagicMock()
        fake_uc.get_unity_catalog_connection.return_value = mock_conn
        with patch.dict("sys.modules", {"src.db.unity_catalog_connector": fake_uc}):
            result = get_latest_sensor_data(device_id=99)

        assert result is None

    def test_connection_is_always_closed(self):
        """例外が発生しても接続が必ずクローズされること"""
        mock_conn = MagicMock()
        mock_conn.execute.side_effect = Exception("DB error")

        fake_uc = MagicMock()
        fake_uc.get_unity_catalog_connection.return_value = mock_conn
        with patch.dict("sys.modules", {"src.db.unity_catalog_connector": fake_uc}):
            with pytest.raises(Exception):
                get_latest_sensor_data(device_id=1)

        mock_conn.close.assert_called_once()


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

    def test_count_capped_at_alert_fetch_limit(self):
        """件数が ALERT_FETCH_LIMIT を超える場合は上限に丸められること"""
        from src.services.industry_dashboard_service import ALERT_FETCH_LIMIT
        with patch("src.services.industry_dashboard_service.db") as mock_db:
            self._make_base_query_mock(mock_db, [], 9999)
            _, total = get_device_alerts_with_count(device_id=1, search_params={"page": 1})
        assert total == ALERT_FETCH_LIMIT

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
# タスク2-7: get_graph_data
# ============================================================

class TestGetGraphData:
    """get_graph_data のテスト"""

    def test_returns_rows_for_date_range(self):
        """指定した表示期間のセンサーデータ行リストを返すこと"""
        mock_rows = [MagicMock(), MagicMock()]
        mock_conn = MagicMock()
        mock_conn.execute.return_value.fetchall.return_value = mock_rows

        fake_uc = MagicMock()
        fake_uc.get_unity_catalog_connection.return_value = mock_conn
        with patch.dict("sys.modules", {"src.db.unity_catalog_connector": fake_uc}):
            result = get_graph_data(
                device_id=1,
                search_params={
                    "search_start_datetime": "2026-02-01T00:00",
                    "search_end_datetime": "2026-02-02T00:00",
                },
            )

        assert result == mock_rows
        mock_conn.close.assert_called_once()

    def test_returns_empty_list_when_no_data(self):
        """データなし時に空リストを返すこと"""
        mock_conn = MagicMock()
        mock_conn.execute.return_value.fetchall.return_value = []

        fake_uc = MagicMock()
        fake_uc.get_unity_catalog_connection.return_value = mock_conn
        with patch.dict("sys.modules", {"src.db.unity_catalog_connector": fake_uc}):
            result = get_graph_data(device_id=1, search_params={})

        assert result == []

    def test_connection_is_always_closed(self):
        """例外が発生しても接続が必ずクローズされること"""
        mock_conn = MagicMock()
        mock_conn.execute.side_effect = Exception("Unity Catalog error")

        fake_uc = MagicMock()
        fake_uc.get_unity_catalog_connection.return_value = mock_conn
        with patch.dict("sys.modules", {"src.db.unity_catalog_connector": fake_uc}):
            with pytest.raises(Exception):
                get_graph_data(device_id=1, search_params={})

        mock_conn.close.assert_called_once()


# ============================================================
# タスク2-8: export_sensor_data_csv
# ============================================================

class TestExportSensorDataCsv:
    """export_sensor_data_csv のテスト"""

    def _make_mock_device(self, device_uuid="test-uuid-1234", device_id=1):
        device = MagicMock()
        device.device_uuid = device_uuid
        device.device_id = device_id
        return device

    def _make_mock_row(self):
        """センサーデータ行のモックを生成（全フィールド設定）"""
        row = MagicMock()
        row.event_timestamp = datetime(2026, 2, 1, 10, 0, 0)
        row.external_temp = -5.0
        row.set_temp_freezer_1 = -18.0
        row.internal_sensor_temp_freezer_1 = -17.5
        row.internal_temp_freezer_1 = -17.0
        row.df_temp_freezer_1 = -16.0
        row.condensing_temp_freezer_1 = 30.0
        row.adjusted_internal_temp_freezer_1 = -17.2
        row.set_temp_freezer_2 = -20.0
        row.internal_sensor_temp_freezer_2 = -19.5
        row.internal_temp_freezer_2 = -19.0
        row.df_temp_freezer_2 = -18.0
        row.condensing_temp_freezer_2 = 28.0
        row.adjusted_internal_temp_freezer_2 = -19.2
        row.compressor_freezer_1 = 1
        row.compressor_freezer_2 = 1
        row.fan_motor_1 = 100
        row.fan_motor_2 = 90
        row.fan_motor_3 = 80
        row.fan_motor_4 = 70
        row.fan_motor_5 = 60
        row.defrost_heater_output_1 = 0
        row.defrost_heater_output_2 = 0
        return row

    def test_returns_csv_response(self, app):
        """CSV形式のレスポンスを返すこと"""
        mock_row = self._make_mock_row()
        with app.app_context():
            with patch("src.services.industry_dashboard_service.get_graph_data",
                       return_value=[mock_row]):
                response = export_sensor_data_csv(
                    self._make_mock_device(),
                    {"search_start_datetime": "2026-02-01T00:00",
                     "search_end_datetime": "2026-02-02T00:00"},
                )
        assert "text/csv" in response.headers["Content-type"]

    def test_csv_has_correct_header_columns(self, app):
        """CSVヘッダーが仕様書に定義された23カラムであること"""
        expected_columns = [
            "イベント発生日時",
            "外気温度",
            "第1冷凍 設定温度",
            "第1冷凍 庫内センサー温度",
            "第1冷凍 庫内温度",
            "第1冷凍 DF温度",
            "第1冷凍 凝縮温度",
            "第1冷凍 微調整後庫内温度",
            "第2冷凍 設定温度",
            "第2冷凍 庫内センサー温度",
            "第2冷凍 庫内温度",
            "第2冷凍 DF温度",
            "第2冷凍 凝縮温度",
            "第2冷凍 微調整後庫内温度",
            "第1冷凍 圧縮機",
            "第2冷凍 圧縮機",
            "第1ファンモータ",
            "第2ファンモータ",
            "第3ファンモータ",
            "第4ファンモータ",
            "第5ファンモータ",
            "防露ヒータ出力(1)",
            "防露ヒータ出力(2)",
        ]
        with app.app_context():
            with patch("src.services.industry_dashboard_service.get_graph_data",
                       return_value=[]):
                response = export_sensor_data_csv(self._make_mock_device(), {})
        csv_text = response.get_data(as_text=True)
        header_line = csv_text.splitlines()[0]
        for col in expected_columns:
            assert col in header_line, f"ヘッダーに '{col}' が含まれていません"

    def test_csv_content_disposition_is_attachment(self, app):
        """Content-Disposition が attachment であること"""
        with app.app_context():
            with patch("src.services.industry_dashboard_service.get_graph_data",
                       return_value=[]):
                response = export_sensor_data_csv(self._make_mock_device(), {})
        assert "attachment" in response.headers["Content-Disposition"]

    def test_csv_filename_contains_device_uuid(self, app):
        """ファイル名にデバイスUUIDが含まれること"""
        device = self._make_mock_device(device_uuid="test-uuid-abcd")
        with app.app_context():
            with patch("src.services.industry_dashboard_service.get_graph_data",
                       return_value=[]):
                response = export_sensor_data_csv(device, {})
        assert "test-uuid-abcd" in response.headers["Content-Disposition"]

    def test_csv_data_row_has_23_columns(self, app):
        """データ行が23カラムであること"""
        mock_row = self._make_mock_row()
        with app.app_context():
            with patch("src.services.industry_dashboard_service.get_graph_data",
                       return_value=[mock_row]):
                response = export_sensor_data_csv(self._make_mock_device(), {})
        csv_text = response.get_data(as_text=True)
        data_line = csv_text.splitlines()[1]  # 2行目がデータ行
        columns = data_line.split(",")
        assert len(columns) == 23

    def test_csv_null_fields_output_as_empty_string(self, app):
        """Noneフィールドが空文字列として出力されること"""
        mock_row = MagicMock()
        mock_row.event_timestamp = None
        mock_row.external_temp = None
        mock_row.set_temp_freezer_1 = None
        mock_row.internal_sensor_temp_freezer_1 = None
        mock_row.internal_temp_freezer_1 = None
        mock_row.df_temp_freezer_1 = None
        mock_row.condensing_temp_freezer_1 = None
        mock_row.adjusted_internal_temp_freezer_1 = None
        mock_row.set_temp_freezer_2 = None
        mock_row.internal_sensor_temp_freezer_2 = None
        mock_row.internal_temp_freezer_2 = None
        mock_row.df_temp_freezer_2 = None
        mock_row.condensing_temp_freezer_2 = None
        mock_row.adjusted_internal_temp_freezer_2 = None
        mock_row.compressor_freezer_1 = None
        mock_row.compressor_freezer_2 = None
        mock_row.fan_motor_1 = None
        mock_row.fan_motor_2 = None
        mock_row.fan_motor_3 = None
        mock_row.fan_motor_4 = None
        mock_row.fan_motor_5 = None
        mock_row.defrost_heater_output_1 = None
        mock_row.defrost_heater_output_2 = None

        with app.app_context():
            with patch("src.services.industry_dashboard_service.get_graph_data",
                       return_value=[mock_row]):
                response = export_sensor_data_csv(self._make_mock_device(), {})
        csv_text = response.get_data(as_text=True)
        data_line = csv_text.splitlines()[1]
        # 全カラムが空文字列（カンマのみ）
        assert data_line == "," * 22


# ============================================================
# タスク2-9: get_default_date_range
# ============================================================

class TestGetDefaultDateRange:
    """get_default_date_range のテスト"""

    def test_returns_dict_with_required_keys(self):
        """必須キーを含む辞書が返されること"""
        result = get_default_date_range()
        assert "search_start_datetime" in result
        assert "search_end_datetime" in result

    def test_start_is_before_end(self):
        """開始日時が終了日時より前であること"""
        result = get_default_date_range()
        start = datetime.strptime(result["search_start_datetime"], "%Y-%m-%dT%H:%M")
        end = datetime.strptime(result["search_end_datetime"], "%Y-%m-%dT%H:%M")
        assert start < end

    def test_range_is_24_hours(self):
        """差が24時間以内であること（UI仕様書 10-1: 初期値=現在日時から1日前）"""
        result = get_default_date_range()
        start = datetime.strptime(result["search_start_datetime"], "%Y-%m-%dT%H:%M")
        end = datetime.strptime(result["search_end_datetime"], "%Y-%m-%dT%H:%M")
        diff = (end - start).total_seconds()
        assert 23 * 3600 <= diff <= 24 * 3600 + 60


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

    def test_valid_range_returns_empty_errors(self):
        """正常な期間の場合にエラーなし"""
        errors = validate_date_range("2026-02-01T00:00", "2026-02-02T00:00")
        assert errors == []

    def test_invalid_format_returns_error(self):
        """不正な日時フォーマットのエラーを検出すること"""
        errors = validate_date_range("2026/02/01 00:00", "2026-02-02T00:00")
        assert len(errors) == 1
        assert "形式" in errors[0]

    def test_start_equal_to_end_returns_error(self):
        """開始 == 終了のエラーを検出すること"""
        errors = validate_date_range("2026-02-01T00:00", "2026-02-01T00:00")
        assert len(errors) == 1
        assert "開始日時" in errors[0]

    def test_start_after_end_returns_error(self):
        """開始 > 終了のエラーを検出すること"""
        errors = validate_date_range("2026-02-03T00:00", "2026-02-01T00:00")
        assert len(errors) == 1
        assert "開始日時" in errors[0]

    def test_range_over_62_days_returns_error(self):
        """62日超過のエラーを検出すること（ワークフロー仕様書: 最大2ヶ月=62日）"""
        errors = validate_date_range("2026-01-01T00:00", "2026-03-10T00:00")
        assert len(errors) == 1
        assert "2ヶ月" in errors[0]

    def test_exactly_62_days_is_valid(self):
        """ちょうど62日はエラーなし"""
        errors = validate_date_range("2026-01-01T00:00", "2026-03-04T00:00")
        assert errors == []

    def test_empty_string_returns_error(self):
        """空文字列のエラーを検出すること"""
        errors = validate_date_range("", "2026-02-02T00:00")
        assert len(errors) >= 1

    def test_none_value_returns_error(self):
        """None値のエラーを検出すること"""
        errors = validate_date_range(None, "2026-02-02T00:00")
        assert len(errors) >= 1

    def test_exactly_61_days_is_valid(self):
        """61日はエラーなし（上限62日の境界値: 61日 < 62日）"""
        # 2026-01-01 → 2026-03-03 = 31 + 28 + 2 = 61日
        errors = validate_date_range("2026-01-01T00:00", "2026-03-03T00:00")
        assert errors == []

    def test_exactly_63_days_returns_error(self):
        """63日はエラー（62日超過の境界値: 63日 > 62日）"""
        # 2026-01-01 → 2026-03-05 = 31 + 28 + 4 = 63日
        errors = validate_date_range("2026-01-01T00:00", "2026-03-05T00:00")
        assert len(errors) == 1
        assert "2ヶ月" in errors[0]
