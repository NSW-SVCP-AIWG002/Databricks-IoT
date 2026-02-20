"""
業種別ダッシュボード機能 結合テスト

対象エンドポイント:
  GET  /industry-dashboard/store-monitoring
  POST /industry-dashboard/store-monitoring
  GET  /industry-dashboard/store-monitoring/<device_uuid>
  GET  /industry-dashboard/device-details/<device_uuid>
  POST /industry-dashboard/device-details/<device_uuid>
  GET  /industry-dashboard/device-details/<device_uuid>?export=csv
"""

from unittest.mock import MagicMock, patch

import pytest


STORE_MONITORING_URL = "/industry-dashboard/store-monitoring"
DEVICE_DETAILS_URL = "/industry-dashboard/device-details"
DEVICE_UUID = "test-device-uuid-1234"


def _make_mock_user(organization_id=1):
    user = MagicMock()
    user.organization_id = organization_id
    return user


def _make_mock_device(device_uuid=DEVICE_UUID, device_id=1):
    device = MagicMock()
    device.device_uuid = device_uuid
    device.device_id = device_id
    device.device_name = "冷蔵庫1"
    device.device_model = "MODEL-A100"
    return device


# ============================================================
# タスク4-1: GET /industry-dashboard/store-monitoring (初期表示)
# ============================================================

class TestStoreMonitoringGet:
    """店舗モニタリング初期表示のテスト"""

    @patch("src.views.industry_dashboard.views.get_device_list_with_count")
    @patch("src.views.industry_dashboard.views.get_recent_alerts_with_count")
    @patch("src.views.industry_dashboard.views.get_accessible_organizations")
    def test_initial_display_returns_200(
        self, mock_orgs, mock_alerts, mock_devices, client
    ):
        """初期表示が200を返すこと"""
        mock_orgs.return_value = [1, 2]
        mock_alerts.return_value = ([], 0)
        mock_devices.return_value = ([], 0)

        with patch("flask.g") as mock_g:
            mock_g.current_user = _make_mock_user()
            response = client.get(STORE_MONITORING_URL)

        assert response.status_code == 200

    @patch("src.views.industry_dashboard.views.get_device_list_with_count")
    @patch("src.views.industry_dashboard.views.get_recent_alerts_with_count")
    @patch("src.views.industry_dashboard.views.get_accessible_organizations")
    def test_paging_returns_200(
        self, mock_orgs, mock_alerts, mock_devices, client
    ):
        """ページングが200を返すこと"""
        mock_orgs.return_value = [1]
        mock_alerts.return_value = ([], 0)
        mock_devices.return_value = ([], 0)

        with patch("flask.g") as mock_g:
            mock_g.current_user = _make_mock_user()
            response = client.get(f"{STORE_MONITORING_URL}?page=2")

        assert response.status_code == 200

    @patch("src.views.industry_dashboard.views.get_accessible_organizations",
           side_effect=Exception("DB error"))
    def test_db_error_returns_500(self, mock_orgs, client):
        """DBエラー時に500を返すこと"""
        with patch("flask.g") as mock_g:
            mock_g.current_user = _make_mock_user()
            response = client.get(STORE_MONITORING_URL)

        assert response.status_code == 500


# ============================================================
# タスク4-2: POST /industry-dashboard/store-monitoring (検索)
# ============================================================

class TestStoreMonitoringPost:
    """店舗モニタリング検索のテスト"""

    @patch("src.views.industry_dashboard.views.get_device_list_with_count")
    @patch("src.views.industry_dashboard.views.get_recent_alerts_with_count")
    @patch("src.views.industry_dashboard.views.get_accessible_organizations")
    def test_search_returns_200(
        self, mock_orgs, mock_alerts, mock_devices, client
    ):
        """検索が200を返すこと"""
        mock_orgs.return_value = [1]
        mock_alerts.return_value = ([], 0)
        mock_devices.return_value = ([], 0)

        with patch("flask.g") as mock_g:
            mock_g.current_user = _make_mock_user()
            response = client.post(STORE_MONITORING_URL, data={
                "organization_name": "店舗A",
                "device_name": "",
            })

        assert response.status_code == 200


# ============================================================
# タスク4-3: GET /industry-dashboard/store-monitoring/<uuid> (センサー情報)
# ============================================================

class TestShowSensorInfo:
    """センサー情報表示のテスト"""

    @patch("src.views.industry_dashboard.views.get_latest_sensor_data")
    @patch("src.views.industry_dashboard.views.get_device_list_with_count")
    @patch("src.views.industry_dashboard.views.get_recent_alerts_with_count")
    @patch("src.views.industry_dashboard.views.check_device_access")
    @patch("src.views.industry_dashboard.views.get_accessible_organizations")
    def test_returns_200_with_sensor_data(
        self, mock_orgs, mock_check, mock_alerts, mock_devices, mock_sensor, client
    ):
        """センサーデータあり時に200を返すこと"""
        mock_orgs.return_value = [1]
        mock_check.return_value = _make_mock_device()
        mock_alerts.return_value = ([], 0)
        mock_devices.return_value = ([], 0)
        mock_sensor.return_value = MagicMock()

        with patch("flask.g") as mock_g:
            mock_g.current_user = _make_mock_user()
            response = client.get(f"{STORE_MONITORING_URL}/{DEVICE_UUID}")

        assert response.status_code == 200

    @patch("src.views.industry_dashboard.views.check_device_access")
    @patch("src.views.industry_dashboard.views.get_accessible_organizations")
    def test_returns_404_when_device_not_found(
        self, mock_orgs, mock_check, client
    ):
        """デバイス未検出時に404を返すこと"""
        mock_orgs.return_value = [1]
        mock_check.return_value = None

        with patch("flask.g") as mock_g:
            mock_g.current_user = _make_mock_user()
            response = client.get(f"{STORE_MONITORING_URL}/{DEVICE_UUID}")

        assert response.status_code == 404


# ============================================================
# タスク4-4: GET /industry-dashboard/device-details/<uuid> (詳細初期表示)
# ============================================================

class TestDeviceDetailsGet:
    """デバイス詳細初期表示のテスト"""

    @patch("src.views.industry_dashboard.views.get_graph_data")
    @patch("src.views.industry_dashboard.views.get_device_alerts_with_count")
    @patch("src.views.industry_dashboard.views.check_device_access")
    @patch("src.views.industry_dashboard.views.get_accessible_organizations")
    def test_initial_display_returns_200(
        self, mock_orgs, mock_check, mock_alerts, mock_graph, client
    ):
        """初期表示が200を返すこと"""
        mock_orgs.return_value = [1]
        mock_check.return_value = _make_mock_device()
        mock_alerts.return_value = ([], 0)
        mock_graph.return_value = []

        with patch("flask.g") as mock_g:
            mock_g.current_user = _make_mock_user()
            response = client.get(f"{DEVICE_DETAILS_URL}/{DEVICE_UUID}")

        assert response.status_code == 200

    @patch("src.views.industry_dashboard.views.check_device_access")
    @patch("src.views.industry_dashboard.views.get_accessible_organizations")
    def test_returns_404_when_device_not_found(
        self, mock_orgs, mock_check, client
    ):
        """デバイス未検出時に404を返すこと"""
        mock_orgs.return_value = [1]
        mock_check.return_value = None

        with patch("flask.g") as mock_g:
            mock_g.current_user = _make_mock_user()
            response = client.get(f"{DEVICE_DETAILS_URL}/{DEVICE_UUID}")

        assert response.status_code == 404


# ============================================================
# タスク4-5: POST /industry-dashboard/device-details/<uuid> (期間変更)
# ============================================================

class TestDeviceDetailsPost:
    """デバイス詳細検索（表示期間変更）のテスト"""

    @patch("src.views.industry_dashboard.views.get_graph_data")
    @patch("src.views.industry_dashboard.views.get_device_alerts_with_count")
    @patch("src.views.industry_dashboard.views.check_device_access")
    @patch("src.views.industry_dashboard.views.get_accessible_organizations")
    def test_valid_period_returns_200(
        self, mock_orgs, mock_check, mock_alerts, mock_graph, client
    ):
        """正常な表示期間で200を返すこと"""
        mock_orgs.return_value = [1]
        mock_check.return_value = _make_mock_device()
        mock_alerts.return_value = ([], 0)
        mock_graph.return_value = []

        with patch("flask.g") as mock_g:
            mock_g.current_user = _make_mock_user()
            response = client.post(f"{DEVICE_DETAILS_URL}/{DEVICE_UUID}", data={
                "search_start_datetime": "2026-02-01T00:00",
                "search_end_datetime": "2026-02-02T00:00",
            })

        assert response.status_code == 200

    @patch("src.views.industry_dashboard.views.check_device_access")
    @patch("src.views.industry_dashboard.views.get_accessible_organizations")
    def test_invalid_period_returns_400(
        self, mock_orgs, mock_check, client
    ):
        """不正な表示期間で400を返すこと"""
        mock_orgs.return_value = [1]
        mock_check.return_value = _make_mock_device()

        with patch("flask.g") as mock_g:
            mock_g.current_user = _make_mock_user()
            response = client.post(f"{DEVICE_DETAILS_URL}/{DEVICE_UUID}", data={
                "search_start_datetime": "2026-02-10T00:00",
                "search_end_datetime": "2026-02-01T00:00",
            })

        assert response.status_code == 400

    @patch("src.views.industry_dashboard.views.check_device_access")
    @patch("src.views.industry_dashboard.views.get_accessible_organizations")
    def test_over_62_days_returns_400(
        self, mock_orgs, mock_check, client
    ):
        """62日超過の表示期間で400を返すこと"""
        mock_orgs.return_value = [1]
        mock_check.return_value = _make_mock_device()

        with patch("flask.g") as mock_g:
            mock_g.current_user = _make_mock_user()
            response = client.post(f"{DEVICE_DETAILS_URL}/{DEVICE_UUID}", data={
                "search_start_datetime": "2026-01-01T00:00",
                "search_end_datetime": "2026-03-20T00:00",
            })

        assert response.status_code == 400


# ============================================================
# タスク4-6: GET .../device-details/<uuid>?export=csv (CSVエクスポート)
# ============================================================

class TestCsvExport:
    """CSVエクスポートのテスト"""

    @patch("src.views.industry_dashboard.views.export_sensor_data_csv")
    @patch("src.views.industry_dashboard.views.check_device_access")
    @patch("src.views.industry_dashboard.views.get_accessible_organizations")
    def test_csv_export_returns_csv_response(
        self, mock_orgs, mock_check, mock_export, client
    ):
        """CSVエクスポートがCSVレスポンスを返すこと"""
        mock_orgs.return_value = [1]
        mock_check.return_value = _make_mock_device()

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.headers = {"Content-type": "text/csv; charset=utf-8-sig"}
        mock_export.return_value = mock_resp

        with patch("flask.g") as mock_g:
            mock_g.current_user = _make_mock_user()
            response = client.get(
                f"{DEVICE_DETAILS_URL}/{DEVICE_UUID}?export=csv"
            )

        mock_export.assert_called_once()

    @patch("src.views.industry_dashboard.views.check_device_access")
    @patch("src.views.industry_dashboard.views.get_accessible_organizations")
    def test_csv_export_returns_404_when_device_not_found(
        self, mock_orgs, mock_check, client
    ):
        """デバイス未検出時CSVエクスポートで404を返すこと"""
        mock_orgs.return_value = [1]
        mock_check.return_value = None

        with patch("flask.g") as mock_g:
            mock_g.current_user = _make_mock_user()
            response = client.get(
                f"{DEVICE_DETAILS_URL}/{DEVICE_UUID}?export=csv"
            )

        assert response.status_code == 404
