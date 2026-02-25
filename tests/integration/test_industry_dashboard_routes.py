"""
業種別ダッシュボード機能 結合テスト

対象エンドポイント（ワークフロー仕様書 使用するFlaskルート一覧）:
  GET  /industry-dashboard/store-monitoring           店舗モニタリング初期表示・ページング
  POST /industry-dashboard/store-monitoring           店舗モニタリング検索
  GET  /industry-dashboard/store-monitoring/<uuid>    センサー情報表示
  GET  /industry-dashboard/device-details/<uuid>      デバイス詳細初期表示・ページング・CSVエクスポート
  POST /industry-dashboard/device-details/<uuid>      デバイス詳細検索（表示期間変更）

認証:
  tests/integration/conftest.py の inject_test_user フィクスチャにより
  全テストで g.current_user が自動セットされる。

CSRF:
  TestingConfig に WTF_CSRF_ENABLED = False を設定済み。
"""

from unittest.mock import MagicMock, patch

import pytest


STORE_MONITORING_URL = "/industry-dashboard/store-monitoring"
DEVICE_DETAILS_URL = "/industry-dashboard/device-details"
DEVICE_UUID = "test-device-uuid-1234"


def _make_mock_device(device_uuid=DEVICE_UUID, device_id=1):
    device = MagicMock()
    device.device_uuid = device_uuid
    device.device_id = device_id
    device.device_name = "冷蔵庫1"
    device.device_model = "MODEL-A100"
    return device


# ============================================================
# タスク4-1: GET /industry-dashboard/store-monitoring
# 店舗モニタリング初期表示・ページング
# ============================================================

class TestStoreMonitoringGet:
    """店舗モニタリング初期表示・ページングのテスト

    ワークフロー仕様書「店舗モニタリング初期表示」に対応。
    """

    @patch("src.views.industry_dashboard.views.get_device_list_with_count")
    @patch("src.views.industry_dashboard.views.get_recent_alerts_with_count")
    @patch("src.views.industry_dashboard.views.get_accessible_organizations")
    def test_initial_display_returns_200(
        self, mock_orgs, mock_alerts, mock_devices, client
    ):
        """初期表示（pageパラメータなし）が200を返すこと"""
        mock_orgs.return_value = [1, 2]
        mock_alerts.return_value = ([], 0)
        mock_devices.return_value = ([], 0)

        response = client.get(STORE_MONITORING_URL)

        assert response.status_code == 200

    @patch("src.views.industry_dashboard.views.get_device_list_with_count")
    @patch("src.views.industry_dashboard.views.get_recent_alerts_with_count")
    @patch("src.views.industry_dashboard.views.get_accessible_organizations")
    def test_paging_returns_200(
        self, mock_orgs, mock_alerts, mock_devices, client
    ):
        """ページング（pageパラメータあり）が200を返すこと"""
        mock_orgs.return_value = [1]
        mock_alerts.return_value = ([], 0)
        mock_devices.return_value = ([], 0)

        response = client.get(f"{STORE_MONITORING_URL}?page=2")

        assert response.status_code == 200

    @patch("src.views.industry_dashboard.views.get_device_list_with_count")
    @patch("src.views.industry_dashboard.views.get_recent_alerts_with_count")
    @patch("src.views.industry_dashboard.views.get_accessible_organizations")
    def test_empty_org_ids_returns_200(
        self, mock_orgs, mock_alerts, mock_devices, client
    ):
        """アクセス可能組織なし（空リスト）でも200を返すこと"""
        mock_orgs.return_value = []
        mock_alerts.return_value = ([], 0)
        mock_devices.return_value = ([], 0)

        response = client.get(STORE_MONITORING_URL)

        assert response.status_code == 200

    @patch("src.views.industry_dashboard.views.get_accessible_organizations",
           side_effect=Exception("DB接続エラー"))
    def test_db_error_returns_500(self, mock_orgs, client):
        """DBエラー時に500を返すこと（ワークフロー仕様書「エラーハンドリング」）"""
        response = client.get(STORE_MONITORING_URL)

        assert response.status_code == 500

    @patch("src.views.industry_dashboard.views.get_device_list_with_count")
    @patch("src.views.industry_dashboard.views.get_recent_alerts_with_count")
    @patch("src.views.industry_dashboard.views.get_accessible_organizations")
    def test_initial_display_sets_cookie(
        self, mock_orgs, mock_alerts, mock_devices, client
    ):
        """初期表示時に検索条件がCookieにセットされること"""
        mock_orgs.return_value = [1]
        mock_alerts.return_value = ([], 0)
        mock_devices.return_value = ([], 0)

        response = client.get(STORE_MONITORING_URL)

        assert response.status_code == 200
        assert "store_monitoring_search_params" in response.headers.get("Set-Cookie", "")

    @patch("src.views.industry_dashboard.views.get_device_list_with_count")
    @patch("src.views.industry_dashboard.views.get_recent_alerts_with_count")
    @patch("src.views.industry_dashboard.views.get_accessible_organizations")
    def test_paging_uses_cookie_search_params(
        self, mock_orgs, mock_alerts, mock_devices, client
    ):
        """ページング時にCookieの検索条件（組織名）が使用されること"""
        import json

        mock_orgs.return_value = [1]
        mock_alerts.return_value = ([], 0)
        mock_devices.return_value = ([], 0)

        cookie_params = {"organization_name": "店舗A", "device_name": "", "page": 1}
        client.set_cookie(
            "store_monitoring_search_params", json.dumps(cookie_params)
        )

        response = client.get(f"{STORE_MONITORING_URL}?page=2")

        assert response.status_code == 200
        call_args = mock_alerts.call_args[0][0]
        assert call_args.get("organization_name") == "店舗A"


# ============================================================
# タスク4-2: POST /industry-dashboard/store-monitoring
# 店舗モニタリング検索
# ============================================================

class TestStoreMonitoringPost:
    """店舗モニタリング検索のテスト

    ワークフロー仕様書「店舗モニタリング検索」に対応。
    """

    @patch("src.views.industry_dashboard.views.get_device_list_with_count")
    @patch("src.views.industry_dashboard.views.get_recent_alerts_with_count")
    @patch("src.views.industry_dashboard.views.get_accessible_organizations")
    def test_search_with_store_name_returns_200(
        self, mock_orgs, mock_alerts, mock_devices, client
    ):
        """店舗名検索が200を返すこと"""
        mock_orgs.return_value = [1]
        mock_alerts.return_value = ([], 0)
        mock_devices.return_value = ([], 0)

        response = client.post(STORE_MONITORING_URL, data={
            "organization_name": "店舗A",
            "device_name": "",
        })

        assert response.status_code == 200

    @patch("src.views.industry_dashboard.views.get_device_list_with_count")
    @patch("src.views.industry_dashboard.views.get_recent_alerts_with_count")
    @patch("src.views.industry_dashboard.views.get_accessible_organizations")
    def test_search_with_device_name_returns_200(
        self, mock_orgs, mock_alerts, mock_devices, client
    ):
        """デバイス名検索が200を返すこと"""
        mock_orgs.return_value = [1]
        mock_alerts.return_value = ([], 0)
        mock_devices.return_value = ([], 0)

        response = client.post(STORE_MONITORING_URL, data={
            "organization_name": "",
            "device_name": "冷蔵庫",
        })

        assert response.status_code == 200

    @patch("src.views.industry_dashboard.views.get_device_list_with_count")
    @patch("src.views.industry_dashboard.views.get_recent_alerts_with_count")
    @patch("src.views.industry_dashboard.views.get_accessible_organizations")
    def test_search_with_empty_conditions_returns_200(
        self, mock_orgs, mock_alerts, mock_devices, client
    ):
        """検索条件が空でも200を返すこと"""
        mock_orgs.return_value = [1]
        mock_alerts.return_value = ([], 0)
        mock_devices.return_value = ([], 0)

        response = client.post(STORE_MONITORING_URL, data={
            "organization_name": "",
            "device_name": "",
        })

        assert response.status_code == 200

    @patch("src.views.industry_dashboard.views.get_accessible_organizations",
           side_effect=Exception("DB接続エラー"))
    def test_db_error_returns_500(self, mock_orgs, client):
        """DBエラー時に500を返すこと"""
        response = client.post(STORE_MONITORING_URL, data={
            "organization_name": "店舗A",
        })

        assert response.status_code == 500

    @patch("src.views.industry_dashboard.views.get_device_list_with_count")
    @patch("src.views.industry_dashboard.views.get_recent_alerts_with_count")
    @patch("src.views.industry_dashboard.views.get_accessible_organizations")
    def test_search_saves_cookie(
        self, mock_orgs, mock_alerts, mock_devices, client
    ):
        """検索後に検索条件がCookieにセットされること"""
        mock_orgs.return_value = [1]
        mock_alerts.return_value = ([], 0)
        mock_devices.return_value = ([], 0)

        response = client.post(STORE_MONITORING_URL, data={
            "organization_name": "店舗A",
            "device_name": "",
        })

        assert response.status_code == 200
        assert "store_monitoring_search_params" in response.headers.get("Set-Cookie", "")


# ============================================================
# タスク4-3: GET /industry-dashboard/store-monitoring/<uuid>
# センサー情報表示
# ============================================================

class TestShowSensorInfo:
    """センサー情報表示のテスト

    ワークフロー仕様書「センサー情報表示」に対応。
    """

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

        response = client.get(f"{STORE_MONITORING_URL}/{DEVICE_UUID}")

        assert response.status_code == 200

    @patch("src.views.industry_dashboard.views.get_latest_sensor_data")
    @patch("src.views.industry_dashboard.views.get_device_list_with_count")
    @patch("src.views.industry_dashboard.views.get_recent_alerts_with_count")
    @patch("src.views.industry_dashboard.views.check_device_access")
    @patch("src.views.industry_dashboard.views.get_accessible_organizations")
    def test_returns_200_when_sensor_data_is_none(
        self, mock_orgs, mock_check, mock_alerts, mock_devices, mock_sensor, client
    ):
        """センサーデータなし（Unity Catalog 未登録）でも200を返すこと"""
        mock_orgs.return_value = [1]
        mock_check.return_value = _make_mock_device()
        mock_alerts.return_value = ([], 0)
        mock_devices.return_value = ([], 0)
        mock_sensor.return_value = None

        response = client.get(f"{STORE_MONITORING_URL}/{DEVICE_UUID}")

        assert response.status_code == 200

    @patch("src.views.industry_dashboard.views.check_device_access")
    @patch("src.views.industry_dashboard.views.get_accessible_organizations")
    def test_returns_404_when_device_not_found(
        self, mock_orgs, mock_check, client
    ):
        """デバイス未検出・アクセス権限なし時に404を返すこと"""
        mock_orgs.return_value = [1]
        mock_check.return_value = None

        response = client.get(f"{STORE_MONITORING_URL}/{DEVICE_UUID}")

        assert response.status_code == 404

    @patch("src.views.industry_dashboard.views.get_accessible_organizations",
           side_effect=Exception("DB接続エラー"))
    def test_db_error_returns_500(self, mock_orgs, client):
        """DBエラー時に500を返すこと"""
        response = client.get(f"{STORE_MONITORING_URL}/{DEVICE_UUID}")

        assert response.status_code == 500

    @patch("src.views.industry_dashboard.views.get_latest_sensor_data")
    @patch("src.views.industry_dashboard.views.get_device_list_with_count")
    @patch("src.views.industry_dashboard.views.get_recent_alerts_with_count")
    @patch("src.views.industry_dashboard.views.check_device_access")
    @patch("src.views.industry_dashboard.views.get_accessible_organizations")
    def test_cookie_search_params_used_when_present(
        self, mock_orgs, mock_check, mock_alerts, mock_devices, mock_sensor, client
    ):
        """Cookie有り時にCookieの検索条件（組織名）が使用されること"""
        import json

        mock_orgs.return_value = [1]
        mock_check.return_value = _make_mock_device()
        mock_alerts.return_value = ([], 0)
        mock_devices.return_value = ([], 0)
        mock_sensor.return_value = None

        cookie_params = {"organization_name": "店舗B", "device_name": "", "page": 1}
        client.set_cookie(
            "store_monitoring_search_params", json.dumps(cookie_params)
        )

        response = client.get(f"{STORE_MONITORING_URL}/{DEVICE_UUID}")

        assert response.status_code == 200
        call_args = mock_alerts.call_args[0][0]
        assert call_args.get("organization_name") == "店舗B"


# ============================================================
# タスク4-4: GET /industry-dashboard/device-details/<uuid>
# デバイス詳細初期表示・ページング
# ============================================================

class TestDeviceDetailsGet:
    """デバイス詳細初期表示・ページングのテスト

    ワークフロー仕様書「デバイス詳細初期表示」に対応。
    """

    @patch("src.views.industry_dashboard.views.get_graph_data")
    @patch("src.views.industry_dashboard.views.get_device_alerts_with_count")
    @patch("src.views.industry_dashboard.views.check_device_access")
    @patch("src.views.industry_dashboard.views.get_accessible_organizations")
    def test_initial_display_returns_200(
        self, mock_orgs, mock_check, mock_alerts, mock_graph, client
    ):
        """初期表示（pageパラメータなし）が200を返すこと"""
        mock_orgs.return_value = [1]
        mock_check.return_value = _make_mock_device()
        mock_alerts.return_value = ([], 0)
        mock_graph.return_value = []

        response = client.get(f"{DEVICE_DETAILS_URL}/{DEVICE_UUID}")

        assert response.status_code == 200

    @patch("src.views.industry_dashboard.views.get_graph_data")
    @patch("src.views.industry_dashboard.views.get_device_alerts_with_count")
    @patch("src.views.industry_dashboard.views.check_device_access")
    @patch("src.views.industry_dashboard.views.get_accessible_organizations")
    def test_paging_returns_200(
        self, mock_orgs, mock_check, mock_alerts, mock_graph, client
    ):
        """ページング（pageパラメータあり）が200を返すこと"""
        mock_orgs.return_value = [1]
        mock_check.return_value = _make_mock_device()
        mock_alerts.return_value = ([], 0)
        mock_graph.return_value = []

        response = client.get(f"{DEVICE_DETAILS_URL}/{DEVICE_UUID}?page=2")

        assert response.status_code == 200

    @patch("src.views.industry_dashboard.views.check_device_access")
    @patch("src.views.industry_dashboard.views.get_accessible_organizations")
    def test_returns_404_when_device_not_found(
        self, mock_orgs, mock_check, client
    ):
        """デバイス未検出・アクセス権限なし時に404を返すこと"""
        mock_orgs.return_value = [1]
        mock_check.return_value = None

        response = client.get(f"{DEVICE_DETAILS_URL}/{DEVICE_UUID}")

        assert response.status_code == 404

    @patch("src.views.industry_dashboard.views.get_accessible_organizations",
           side_effect=Exception("DB接続エラー"))
    def test_db_error_returns_500(self, mock_orgs, client):
        """DBエラー時に500を返すこと"""
        response = client.get(f"{DEVICE_DETAILS_URL}/{DEVICE_UUID}")

        assert response.status_code == 500

    @patch("src.views.industry_dashboard.views.get_graph_data")
    @patch("src.views.industry_dashboard.views.get_device_alerts_with_count")
    @patch("src.views.industry_dashboard.views.check_device_access")
    @patch("src.views.industry_dashboard.views.get_accessible_organizations")
    def test_initial_display_sets_cookie(
        self, mock_orgs, mock_check, mock_alerts, mock_graph, client
    ):
        """初期表示時に検索条件（表示期間）がCookieにセットされること"""
        mock_orgs.return_value = [1]
        mock_check.return_value = _make_mock_device()
        mock_alerts.return_value = ([], 0)
        mock_graph.return_value = []

        response = client.get(f"{DEVICE_DETAILS_URL}/{DEVICE_UUID}")

        assert response.status_code == 200
        assert "device_details_search_params" in response.headers.get("Set-Cookie", "")

    @patch("src.views.industry_dashboard.views.get_graph_data")
    @patch("src.views.industry_dashboard.views.get_device_alerts_with_count")
    @patch("src.views.industry_dashboard.views.check_device_access")
    @patch("src.views.industry_dashboard.views.get_accessible_organizations")
    def test_paging_uses_cookie_search_params(
        self, mock_orgs, mock_check, mock_alerts, mock_graph, client
    ):
        """ページング時にCookieの表示期間がグラフデータ取得に使用されること"""
        import json

        mock_orgs.return_value = [1]
        mock_check.return_value = _make_mock_device()
        mock_alerts.return_value = ([], 0)
        mock_graph.return_value = []

        cookie_params = {
            "search_start_datetime": "2026-02-01T00:00",
            "search_end_datetime": "2026-02-10T00:00",
            "page": 1,
        }
        client.set_cookie(
            "device_details_search_params", json.dumps(cookie_params)
        )

        response = client.get(f"{DEVICE_DETAILS_URL}/{DEVICE_UUID}?page=2")

        assert response.status_code == 200
        # get_graph_data の search_params 引数（第2引数）を確認
        call_search_params = mock_graph.call_args[0][1]
        assert call_search_params.get("search_start_datetime") == "2026-02-01T00:00"
        assert call_search_params.get("search_end_datetime") == "2026-02-10T00:00"


# ============================================================
# タスク4-5: POST /industry-dashboard/device-details/<uuid>
# デバイス詳細検索（表示期間変更）
# ============================================================

class TestDeviceDetailsPost:
    """デバイス詳細検索（表示期間変更）のテスト

    ワークフロー仕様書「デバイス詳細検索（表示期間変更）」に対応。
    バリデーションルール: 開始<終了、最大62日、YYYY-MM-DDTHH:MM形式。
    """

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

        response = client.post(f"{DEVICE_DETAILS_URL}/{DEVICE_UUID}", data={
            "search_start_datetime": "2026-02-01T00:00",
            "search_end_datetime": "2026-02-02T00:00",
        })

        assert response.status_code == 200

    @patch("src.views.industry_dashboard.views.check_device_access")
    @patch("src.views.industry_dashboard.views.get_accessible_organizations")
    def test_start_after_end_returns_400(
        self, mock_orgs, mock_check, client
    ):
        """開始日時 > 終了日時の場合に400を返すこと（バリデーション: 開始<終了）"""
        mock_orgs.return_value = [1]
        mock_check.return_value = _make_mock_device()

        response = client.post(f"{DEVICE_DETAILS_URL}/{DEVICE_UUID}", data={
            "search_start_datetime": "2026-02-10T00:00",
            "search_end_datetime": "2026-02-01T00:00",
        })

        assert response.status_code == 400

    @patch("src.views.industry_dashboard.views.check_device_access")
    @patch("src.views.industry_dashboard.views.get_accessible_organizations")
    def test_start_equal_to_end_returns_400(
        self, mock_orgs, mock_check, client
    ):
        """開始日時 == 終了日時の場合に400を返すこと"""
        mock_orgs.return_value = [1]
        mock_check.return_value = _make_mock_device()

        response = client.post(f"{DEVICE_DETAILS_URL}/{DEVICE_UUID}", data={
            "search_start_datetime": "2026-02-01T00:00",
            "search_end_datetime": "2026-02-01T00:00",
        })

        assert response.status_code == 400

    @patch("src.views.industry_dashboard.views.check_device_access")
    @patch("src.views.industry_dashboard.views.get_accessible_organizations")
    def test_over_62_days_returns_400(
        self, mock_orgs, mock_check, client
    ):
        """62日超過の表示期間で400を返すこと（バリデーション: 最大2ヶ月=62日）"""
        mock_orgs.return_value = [1]
        mock_check.return_value = _make_mock_device()

        response = client.post(f"{DEVICE_DETAILS_URL}/{DEVICE_UUID}", data={
            "search_start_datetime": "2026-01-01T00:00",
            "search_end_datetime": "2026-03-20T00:00",
        })

        assert response.status_code == 400

    @patch("src.views.industry_dashboard.views.check_device_access")
    @patch("src.views.industry_dashboard.views.get_accessible_organizations")
    def test_invalid_datetime_format_returns_400(
        self, mock_orgs, mock_check, client
    ):
        """不正な日時フォーマットで400を返すこと"""
        mock_orgs.return_value = [1]
        mock_check.return_value = _make_mock_device()

        response = client.post(f"{DEVICE_DETAILS_URL}/{DEVICE_UUID}", data={
            "search_start_datetime": "2026/02/01 00:00",  # 不正フォーマット
            "search_end_datetime": "2026-02-02T00:00",
        })

        assert response.status_code == 400

    @patch("src.views.industry_dashboard.views.check_device_access")
    @patch("src.views.industry_dashboard.views.get_accessible_organizations")
    def test_device_not_found_returns_404(
        self, mock_orgs, mock_check, client
    ):
        """デバイス未検出時に404を返すこと"""
        mock_orgs.return_value = [1]
        mock_check.return_value = None

        response = client.post(f"{DEVICE_DETAILS_URL}/{DEVICE_UUID}", data={
            "search_start_datetime": "2026-02-01T00:00",
            "search_end_datetime": "2026-02-02T00:00",
        })

        assert response.status_code == 404

    @patch("src.views.industry_dashboard.views.get_accessible_organizations",
           side_effect=Exception("DB接続エラー"))
    def test_db_error_returns_500(self, mock_orgs, client):
        """DBエラー時に500を返すこと"""
        response = client.post(f"{DEVICE_DETAILS_URL}/{DEVICE_UUID}", data={
            "search_start_datetime": "2026-02-01T00:00",
            "search_end_datetime": "2026-02-02T00:00",
        })

        assert response.status_code == 500

    @patch("src.views.industry_dashboard.views.get_graph_data")
    @patch("src.views.industry_dashboard.views.get_device_alerts_with_count")
    @patch("src.views.industry_dashboard.views.check_device_access")
    @patch("src.views.industry_dashboard.views.get_accessible_organizations")
    def test_valid_period_saves_cookie(
        self, mock_orgs, mock_check, mock_alerts, mock_graph, client
    ):
        """正常な表示期間変更後にCookieが更新されること"""
        mock_orgs.return_value = [1]
        mock_check.return_value = _make_mock_device()
        mock_alerts.return_value = ([], 0)
        mock_graph.return_value = []

        response = client.post(f"{DEVICE_DETAILS_URL}/{DEVICE_UUID}", data={
            "search_start_datetime": "2026-02-01T00:00",
            "search_end_datetime": "2026-02-02T00:00",
        })

        assert response.status_code == 200
        assert "device_details_search_params" in response.headers.get("Set-Cookie", "")


# ============================================================
# タスク4-6: GET /industry-dashboard/device-details/<uuid>?export=csv
# CSVエクスポート
# ============================================================

class TestCsvExport:
    """CSVエクスポートのテスト

    ワークフロー仕様書「CSVエクスポート」に対応。
    """

    @patch("src.views.industry_dashboard.views.export_sensor_data_csv")
    @patch("src.views.industry_dashboard.views.check_device_access")
    @patch("src.views.industry_dashboard.views.get_accessible_organizations")
    def test_csv_export_calls_export_function(
        self, mock_orgs, mock_check, mock_export, client
    ):
        """CSVエクスポートが export_sensor_data_csv を呼び出すこと"""
        mock_orgs.return_value = [1]
        mock_check.return_value = _make_mock_device()

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.headers = {"Content-type": "text/csv; charset=utf-8-sig"}
        mock_export.return_value = mock_resp

        client.get(f"{DEVICE_DETAILS_URL}/{DEVICE_UUID}?export=csv")

        mock_export.assert_called_once()

    @patch("src.views.industry_dashboard.views.export_sensor_data_csv")
    @patch("src.views.industry_dashboard.views.check_device_access")
    @patch("src.views.industry_dashboard.views.get_accessible_organizations")
    def test_csv_export_passes_device_to_export_function(
        self, mock_orgs, mock_check, mock_export, client
    ):
        """CSVエクスポートが正しいデバイスオブジェクトを渡すこと"""
        mock_device = _make_mock_device()
        mock_orgs.return_value = [1]
        mock_check.return_value = mock_device

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.headers = {"Content-type": "text/csv; charset=utf-8-sig"}
        mock_export.return_value = mock_resp

        client.get(f"{DEVICE_DETAILS_URL}/{DEVICE_UUID}?export=csv")

        call_args = mock_export.call_args
        assert call_args[0][0] == mock_device

    @patch("src.views.industry_dashboard.views.check_device_access")
    @patch("src.views.industry_dashboard.views.get_accessible_organizations")
    def test_csv_export_returns_404_when_device_not_found(
        self, mock_orgs, mock_check, client
    ):
        """デバイス未検出時CSVエクスポートで404を返すこと"""
        mock_orgs.return_value = [1]
        mock_check.return_value = None

        response = client.get(
            f"{DEVICE_DETAILS_URL}/{DEVICE_UUID}?export=csv"
        )

        assert response.status_code == 404

    @patch("src.views.industry_dashboard.views.get_accessible_organizations",
           side_effect=Exception("DB接続エラー"))
    def test_csv_export_db_error_returns_500(self, mock_orgs, client):
        """DBエラー時CSVエクスポートで500を返すこと"""
        response = client.get(
            f"{DEVICE_DETAILS_URL}/{DEVICE_UUID}?export=csv"
        )

        assert response.status_code == 500

    @patch("src.views.industry_dashboard.views.export_sensor_data_csv")
    @patch("src.views.industry_dashboard.views.check_device_access")
    @patch("src.views.industry_dashboard.views.get_accessible_organizations")
    def test_csv_export_uses_cookie_search_params(
        self, mock_orgs, mock_check, mock_export, client
    ):
        """Cookie有り時にCookieの表示期間がCSVエクスポートに渡されること"""
        import json

        mock_orgs.return_value = [1]
        mock_check.return_value = _make_mock_device()

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.headers = {"Content-type": "text/csv; charset=utf-8-sig"}
        mock_export.return_value = mock_resp

        cookie_params = {
            "search_start_datetime": "2026-02-01T00:00",
            "search_end_datetime": "2026-02-10T00:00",
        }
        client.set_cookie(
            "device_details_search_params", json.dumps(cookie_params)
        )

        client.get(f"{DEVICE_DETAILS_URL}/{DEVICE_UUID}?export=csv")

        # export_sensor_data_csv の search_params 引数（第2引数）を確認
        call_search_params = mock_export.call_args[0][1]
        assert call_search_params.get("search_start_datetime") == "2026-02-01T00:00"
        assert call_search_params.get("search_end_datetime") == "2026-02-10T00:00"
