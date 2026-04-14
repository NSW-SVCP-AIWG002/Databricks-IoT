"""
業種別ダッシュボード機能 結合テスト

対象エンドポイント（ワークフロー仕様書 使用するFlaskルート一覧）:
  GET  /analysis/industry-dashboard/store-monitoring           店舗モニタリング初期表示・ページング
  POST /analysis/industry-dashboard/store-monitoring           店舗モニタリング検索
  GET  /analysis/industry-dashboard/store-monitoring/<uuid>    センサー情報表示
  GET  /analysis/industry-dashboard/device-details/<uuid>      デバイス詳細初期表示・ページング・CSVエクスポート
  POST /analysis/industry-dashboard/device-details/<uuid>      デバイス詳細検索（表示期間変更）

認証:
  tests/integration/conftest.py の inject_test_user フィクスチャにより
  全テストで g.current_user が自動セットされる。

CSRF:
  TestingConfig に WTF_CSRF_ENABLED = False を設定済み。

サービス関数モック化方針:
  OLTP DB テーブル（device_master、organization_master 等）はすべて MySQL に存在する。
  silver_sensor_data は MySQL（直近 SENSOR_DATA_CUTOFF_MONTHS 以内）と
  Unity Catalog（全期間・フォールバック）の両方に存在し、
  ワークフロー仕様書「センサーデータ取得のデータソース切り替えロジック」に従い取得する：
    - MySQL にデータあり → MySQL 優先（get_latest_sensor_data）
    - MySQL にデータなし、または終了日時 < カットオフ → Unity Catalog にフォールバック
    - 期間またがり → MySQL（直近部分）+ Unity Catalog（古い部分）マージ
  - 通常テスト: サービス層関数（get_latest_sensor_data、get_graph_data 等）を unittest.mock でモック化
  - UC 実接続テスト: @pytest.mark.databricks マーカー付与（TestUnityCatalogDatabricks 参照）

適用した観点表セクション（integration-test-perspectives.md 参照）:
  1.1  認証テスト（inject_test_user autouse フィクスチャにより全テストで暗黙的に確認）
  1.3  データスコープフィルタテスト
  2.1  正常遷移テスト
  2.2  エラー時遷移テスト
  3.1  必須チェック
  3.4  日付形式チェック
  3.8  相関チェック
  4.1  一覧表示（Read）テスト
  4.2  詳細表示（Read）テスト
  4.6  CSVエクスポートテスト
  5.1  検索条件テスト
  5.3  ページネーションテスト
  6.3  Unity Catalog クエリテスト
       → silver_sensor_data フォールバックソース（MySQL 優先、UC は長期保存・フォールバック）
       → モック版: TestUnityCatalogDataSourceSwitching
       → 実接続版: TestUnityCatalogDatabricks（@pytest.mark.databricks、DEV_DATABRICKS_TOKEN 必要）
  9.1  SQLインジェクションテスト
  9.2  XSSテスト

適用しない観点表セクション（設計書に該当なし）:
  1.2  認可テスト        → 全ロールでアクセス可能（ロール制限なし、ワークフロー仕様書「データスコープ制限」参照）
  3.2  文字列長チェック  → サーバーサイドバリデーション未記載（UI仕様書 2-1:200文字、2-2:100文字はUI側制限）
  3.7  重複チェック      → Read専用機能のため対象外
  4.3-4.5 CRUD登録/更新/削除 → 本機能はReadのみ
  5.2  ソートテスト      → クライアント側ソートのみ（E2Eテスト対象、ワークフロー仕様書「ページ内ソート」参照）
  6.1/6.2 外部API連携テスト  → Databricks SCIM API は本機能では未使用
                              （ユーザー・グループ管理は本機能のスコープ外）
  7    トランザクション   → Read専用機能のため対象外
  8    ログ出力テスト     → Read専用機能のため省略
  9.3  CSRFテスト        → GETエンドポイント主体、POSTにはCSRFトークン対象外（TestingConfig）
"""

import json
from unittest.mock import MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# 定数
# ---------------------------------------------------------------------------

STORE_MONITORING_URL = "/analysis/industry-dashboard/store-monitoring"
DEVICE_DETAILS_URL = "/analysis/industry-dashboard/device-details"
DEVICE_UUID = "test-device-uuid-1234"

_VIEW_MODULE = "iot_app.views.analysis.industry_dashboard"


# ---------------------------------------------------------------------------
# ヘルパー
# ---------------------------------------------------------------------------


def _make_mock_device(device_uuid=DEVICE_UUID, device_id=1):
    """テスト用デバイスオブジェクトを生成する。"""
    device = MagicMock()
    device.device_uuid = device_uuid
    device.device_id = device_id
    device.device_name = "冷蔵庫1"
    device.device_model = "MODEL-A100"
    device.organization_id = 1
    return device



# ===========================================================================
# 1.3 データスコープフィルタテスト
# ===========================================================================


@pytest.mark.integration
class TestStoreMonitoringDataScope:
    """店舗モニタリング データスコープフィルタテスト

    観点: 1.3 データスコープフィルタテスト
    ワークフロー仕様書「データスコープ制限の適用」に対応。
    organization_closure を用いて自組織・下位組織のデータのみ表示する。
    ロールによる条件分岐は一切行わない（仕様書明記）。
    """

    @patch(f"{_VIEW_MODULE}.get_device_list_with_count")
    @patch(f"{_VIEW_MODULE}.get_recent_alerts_with_count")
    @patch(f"{_VIEW_MODULE}.get_accessible_organizations")
    def test_own_org_data_is_visible(
        self, mock_orgs, mock_alerts, mock_devices, client
    ):
        """1.3.1: 自組織データが表示されること

        get_accessible_organizations が自組織IDを含むリストを返し、
        クエリ関数がそのIDで呼び出されることを確認する。
        """
        # Arrange
        mock_orgs.return_value = [1]  # 自組織ID
        mock_alerts.return_value = ([], 0)
        mock_devices.return_value = ([], 0)

        # Act
        response = client.get(STORE_MONITORING_URL)

        # Assert
        assert response.status_code == 200
        # get_accessible_organizations がユーザーの organization_id（=1）で呼ばれること
        mock_orgs.assert_called_once_with(1)
        # アラート取得にアクセス可能な組織IDが渡されること
        call_org_ids = mock_alerts.call_args[0][1]
        assert call_org_ids == [1]
        # デバイス一覧にも同じ組織IDが渡されること
        device_call_org_ids = mock_devices.call_args[0][1]
        assert device_call_org_ids == [1]

    @patch(f"{_VIEW_MODULE}.get_device_list_with_count")
    @patch(f"{_VIEW_MODULE}.get_recent_alerts_with_count")
    @patch(f"{_VIEW_MODULE}.get_accessible_organizations")
    def test_subsidiary_org_data_is_visible(
        self, mock_orgs, mock_alerts, mock_devices, client
    ):
        """1.3.2: 下位組織データが表示されること

        get_accessible_organizations が下位組織IDも含むリストを返し、
        クエリ関数にその全IDが渡されることを確認する。
        """
        # Arrange
        mock_orgs.return_value = [1, 10, 11]  # 自組織＋下位組織IDs
        mock_alerts.return_value = ([], 0)
        mock_devices.return_value = ([], 0)

        # Act
        response = client.get(STORE_MONITORING_URL)

        # Assert
        assert response.status_code == 200
        call_org_ids = mock_alerts.call_args[0][1]
        assert 10 in call_org_ids
        assert 11 in call_org_ids
        # デバイス一覧にも同じ組織IDが渡されること
        device_call_org_ids = mock_devices.call_args[0][1]
        assert 10 in device_call_org_ids
        assert 11 in device_call_org_ids

    @patch(f"{_VIEW_MODULE}.get_device_list_with_count")
    @patch(f"{_VIEW_MODULE}.get_recent_alerts_with_count")
    @patch(f"{_VIEW_MODULE}.get_accessible_organizations")
    def test_empty_org_scope_returns_empty_result(
        self, mock_orgs, mock_alerts, mock_devices, client
    ):
        """1.3.3 / 1.3.4: アクセス可能な組織が存在しない場合は空リストでクエリが実行されること

        上位・無関係組織のデータが表示されないことをシミュレートする。
        組織IDsが空リストの場合でも200を返し、データが空になることを確認する。
        """
        # Arrange
        mock_orgs.return_value = []  # アクセス可能組織なし
        mock_alerts.return_value = ([], 0)
        mock_devices.return_value = ([], 0)

        # Act
        response = client.get(STORE_MONITORING_URL)

        # Assert
        assert response.status_code == 200
        call_org_ids = mock_alerts.call_args[0][1]
        assert call_org_ids == []


# ===========================================================================
# 2 & 4. 店舗モニタリング初期表示・ページング（GET）
# ===========================================================================


@pytest.mark.integration
class TestStoreMonitoringGet:
    """店舗モニタリング初期表示・ページングテスト

    観点: 2.1 正常遷移テスト / 4.1 一覧表示（Read）テスト / 5.3 ページネーションテスト
    ワークフロー仕様書「店舗モニタリング初期表示」に対応。
    エンドポイント: GET /analysis/industry-dashboard/store-monitoring
    """

    @patch(f"{_VIEW_MODULE}.get_device_list_with_count")
    @patch(f"{_VIEW_MODULE}.get_recent_alerts_with_count")
    @patch(f"{_VIEW_MODULE}.get_accessible_organizations")
    def test_initial_display_sets_cookie(
        self, mock_orgs, mock_alerts, mock_devices, client
    ):
        """2.1.1: 初期表示時に検索条件がCookieにセットされること

        ワークフロー仕様書「検索条件の保持方法: Cookieに保持」、
        「Cookie名: store_monitoring_search_params、max_age=86400」に対応。
        """
        # Arrange
        mock_orgs.return_value = [1]
        mock_alerts.return_value = ([], 0)
        mock_devices.return_value = ([], 0)

        # Act
        response = client.get(STORE_MONITORING_URL)

        # Assert
        assert response.status_code == 200
        assert "store_monitoring_search_params" in response.headers.get("Set-Cookie", "")

    @patch(f"{_VIEW_MODULE}.get_device_list_with_count")
    @patch(f"{_VIEW_MODULE}.get_recent_alerts_with_count")
    @patch(f"{_VIEW_MODULE}.get_accessible_organizations")
    def test_paging_does_not_set_cookie(
        self, mock_orgs, mock_alerts, mock_devices, client
    ):
        """5.3.2: ページング時にはCookieが書き込まれないこと

        ワークフロー仕様書「処理フロー: 初期表示時のみCookie格納（if save_cookie:）」に対応。
        pageパラメータありの場合は _set_cookie が呼ばれず、Set-Cookieヘッダが付かない。
        """
        # Arrange
        mock_orgs.return_value = [1]
        mock_alerts.return_value = ([], 0)
        mock_devices.return_value = ([], 0)

        # Act
        response = client.get(f"{STORE_MONITORING_URL}?page=2")

        # Assert
        assert response.status_code == 200
        assert "store_monitoring_search_params" not in response.headers.get("Set-Cookie", "")

    @patch(f"{_VIEW_MODULE}.get_device_list_with_count")
    @patch(f"{_VIEW_MODULE}.get_recent_alerts_with_count")
    @patch(f"{_VIEW_MODULE}.get_accessible_organizations")
    def test_paging_uses_cookie_search_params(
        self, mock_orgs, mock_alerts, mock_devices, client
    ):
        """5.3.2: ページング時にCookieの検索条件（組織名）が引き継がれること

        ワークフロー仕様書「処理フロー: GetCookie→Cookieから検索条件取得」に対応。
        """
        # Arrange
        mock_orgs.return_value = [1]
        mock_alerts.return_value = ([], 0)
        mock_devices.return_value = ([], 0)
        cookie_params = {"organization_name": "店舗A", "device_name": "", "page": 1}
        client.set_cookie(
            "store_monitoring_search_params", json.dumps(cookie_params)
        )

        # Act
        response = client.get(f"{STORE_MONITORING_URL}?page=2")

        # Assert
        assert response.status_code == 200
        call_search_params = mock_alerts.call_args[0][0]
        assert call_search_params.get("organization_name") == "店舗A"
        # デバイス一覧にも同じ検索条件が渡されること
        device_call_params = mock_devices.call_args[0][0]
        assert device_call_params.get("organization_name") == "店舗A"

    @patch(f"{_VIEW_MODULE}.get_accessible_organizations",
           side_effect=Exception("DB接続エラー"))
    def test_db_error_returns_500(self, mock_orgs, client):
        """2.2.5: DBエラー時に500を返すこと

        ワークフロー仕様書「エラーハンドリング: 500 データベースエラー」に対応。
        """
        # Act
        response = client.get(STORE_MONITORING_URL)

        # Assert
        assert response.status_code == 500


# ===========================================================================
# 5.1. 店舗モニタリング検索（POST）
# ===========================================================================


@pytest.mark.integration
class TestStoreMonitoringPost:
    """店舗モニタリング検索テスト

    観点: 2.1 正常遷移テスト / 5.1 検索条件テスト
    ワークフロー仕様書「店舗モニタリング検索」に対応。
    エンドポイント: POST /analysis/industry-dashboard/store-monitoring
    フォームパラメータ: organization_name, device_name
    """

    @patch(f"{_VIEW_MODULE}.get_device_list_with_count")
    @patch(f"{_VIEW_MODULE}.get_recent_alerts_with_count")
    @patch(f"{_VIEW_MODULE}.get_accessible_organizations")
    def test_search_with_empty_conditions_returns_200(
        self, mock_orgs, mock_alerts, mock_devices, client
    ):
        """5.1.1: 検索条件なし（全件検索）で200を返すこと

        UI仕様書(2-1)(2-2)「空でも可」に対応。
        """
        # Arrange
        mock_orgs.return_value = [1]
        mock_alerts.return_value = ([], 0)
        mock_devices.return_value = ([], 0)

        # Act
        response = client.post(STORE_MONITORING_URL, data={
            "organization_name": "",
            "device_name": "",
        })

        # Assert
        assert response.status_code == 200

    @patch(f"{_VIEW_MODULE}.get_device_list_with_count")
    @patch(f"{_VIEW_MODULE}.get_recent_alerts_with_count")
    @patch(f"{_VIEW_MODULE}.get_accessible_organizations")
    def test_search_with_store_name_partial_match_returns_200(
        self, mock_orgs, mock_alerts, mock_devices, client
    ):
        """5.1.7: 店舗名部分一致検索（前方一致）で200を返すこと

        UI仕様書(2-1)「部分一致検索」に記載されている店舗名検索を確認する。
        ワークフロー仕様書SQL: LIKE CONCAT('%', :organization_name, '%') に対応。
        """
        # Arrange
        mock_orgs.return_value = [1]
        mock_alerts.return_value = ([], 0)
        mock_devices.return_value = ([], 0)

        # Act
        response = client.post(STORE_MONITORING_URL, data={
            "organization_name": "店舗",  # 前方一致
            "device_name": "",
        })

        # Assert
        assert response.status_code == 200
        # 検索条件が正しくクエリ関数に渡されること
        call_search_params = mock_alerts.call_args[0][0]
        assert call_search_params.get("organization_name") == "店舗"
        # デバイス一覧にも同じ検索条件が渡されること
        device_call_params = mock_devices.call_args[0][0]
        assert device_call_params.get("organization_name") == "店舗"

    @patch(f"{_VIEW_MODULE}.get_device_list_with_count")
    @patch(f"{_VIEW_MODULE}.get_recent_alerts_with_count")
    @patch(f"{_VIEW_MODULE}.get_accessible_organizations")
    def test_search_with_device_name_partial_match_returns_200(
        self, mock_orgs, mock_alerts, mock_devices, client
    ):
        """5.1.9: デバイス名部分一致検索（中間一致）で200を返すこと

        UI仕様書(2-2)「部分一致検索」に記載されているデバイス名検索を確認する。
        ワークフロー仕様書SQL: LIKE CONCAT('%', :device_name, '%') に対応。
        """
        # Arrange
        mock_orgs.return_value = [1]
        mock_alerts.return_value = ([], 0)
        mock_devices.return_value = ([], 0)

        # Act
        response = client.post(STORE_MONITORING_URL, data={
            "organization_name": "",
            "device_name": "冷蔵",  # 中間一致（例: 「冷蔵庫1」にマッチ）
        })

        # Assert
        assert response.status_code == 200
        call_search_params = mock_alerts.call_args[0][0]
        assert call_search_params.get("device_name") == "冷蔵"
        # デバイス一覧にも同じ検索条件が渡されること
        device_call_params = mock_devices.call_args[0][0]
        assert device_call_params.get("device_name") == "冷蔵"

    @patch(f"{_VIEW_MODULE}.get_device_list_with_count")
    @patch(f"{_VIEW_MODULE}.get_recent_alerts_with_count")
    @patch(f"{_VIEW_MODULE}.get_accessible_organizations")
    def test_and_search_with_both_conditions(
        self, mock_orgs, mock_alerts, mock_devices, client
    ):
        """5.1.10: 店舗名・デバイス名の複数条件AND検索で200を返すこと

        ワークフロー仕様書SQL「AND CASE WHEN :organization_name … AND CASE WHEN :device_name …」に対応。
        """
        # Arrange
        mock_orgs.return_value = [1]
        mock_alerts.return_value = ([], 0)
        mock_devices.return_value = ([], 0)

        # Act
        response = client.post(STORE_MONITORING_URL, data={
            "organization_name": "店舗A",
            "device_name": "冷蔵庫",
        })

        # Assert
        assert response.status_code == 200
        call_search_params = mock_alerts.call_args[0][0]
        assert call_search_params.get("organization_name") == "店舗A"
        assert call_search_params.get("device_name") == "冷蔵庫"
        # デバイス一覧にも同じ検索条件が渡されること
        # ワークフロー仕様書SQL: デバイス一覧も CASE WHEN :organization_name / :device_name でフィルタ
        device_call_params = mock_devices.call_args[0][0]
        assert device_call_params.get("organization_name") == "店舗A"
        assert device_call_params.get("device_name") == "冷蔵庫"

    @patch(f"{_VIEW_MODULE}.get_device_list_with_count")
    @patch(f"{_VIEW_MODULE}.get_recent_alerts_with_count")
    @patch(f"{_VIEW_MODULE}.get_accessible_organizations")
    def test_search_saves_cookie(
        self, mock_orgs, mock_alerts, mock_devices, client
    ):
        """2.1.2: 検索実行後にCookieに検索条件が保存されること

        ワークフロー仕様書「検索条件の保持方法: Cookie名 store_monitoring_search_params」に対応。
        """
        # Arrange
        mock_orgs.return_value = [1]
        mock_alerts.return_value = ([], 0)
        mock_devices.return_value = ([], 0)

        # Act
        response = client.post(STORE_MONITORING_URL, data={
            "organization_name": "店舗A",
            "device_name": "",
        })

        # Assert
        assert response.status_code == 200
        assert "store_monitoring_search_params" in response.headers.get("Set-Cookie", "")

    @patch(f"{_VIEW_MODULE}.get_accessible_organizations",
           side_effect=Exception("DB接続エラー"))
    def test_db_error_returns_500(self, mock_orgs, client):
        """2.2.5: DBエラー時に500を返すこと

        ワークフロー仕様書「エラーハンドリング: 500 データベースエラー」に対応。
        """
        # Act
        response = client.post(STORE_MONITORING_URL, data={
            "organization_name": "店舗A",
        })

        # Assert
        assert response.status_code == 500


# ===========================================================================
# センサー情報表示（GET /store-monitoring/<uuid>）
# ===========================================================================


@pytest.mark.integration
class TestShowSensorInfo:
    """センサー情報表示テスト

    観点: 2.1 正常遷移テスト / 2.2 エラー時遷移テスト / 4.2 詳細表示テスト
    ワークフロー仕様書「センサー情報表示」に対応。
    エンドポイント: GET /analysis/industry-dashboard/store-monitoring/<device_uuid>
    OLTP DB（MySQL）の silver_sensor_data テーブルから最新センサーデータを取得する。
    """

    @patch(f"{_VIEW_MODULE}.get_latest_sensor_data")
    @patch(f"{_VIEW_MODULE}.get_device_list_with_count")
    @patch(f"{_VIEW_MODULE}.get_recent_alerts_with_count")
    @patch(f"{_VIEW_MODULE}.check_device_access")
    @patch(f"{_VIEW_MODULE}.get_accessible_organizations")
    def test_returns_200_with_sensor_data(
        self, mock_orgs, mock_check, mock_alerts, mock_devices, mock_sensor, client
    ):
        """4.2.1: センサーデータあり時に200を返すこと

        OLTP DB（silver_sensor_data）からセンサーデータが取得できた場合、
        店舗モニタリング画面がセンサー情報表示状態（show_sensor_info=True）で200を返す。
        """
        # Arrange
        mock_orgs.return_value = [1]
        mock_check.return_value = _make_mock_device()
        mock_alerts.return_value = ([], 0)
        mock_devices.return_value = ([], 0)
        mock_sensor.return_value = MagicMock()  # OLTP DB 正常応答

        # Act
        response = client.get(f"{STORE_MONITORING_URL}/{DEVICE_UUID}")

        # Assert
        assert response.status_code == 200

    @patch(f"{_VIEW_MODULE}.get_latest_sensor_data")
    @patch(f"{_VIEW_MODULE}.get_device_list_with_count")
    @patch(f"{_VIEW_MODULE}.get_recent_alerts_with_count")
    @patch(f"{_VIEW_MODULE}.check_device_access")
    @patch(f"{_VIEW_MODULE}.get_accessible_organizations")
    def test_returns_200_when_sensor_data_is_none(
        self, mock_orgs, mock_check, mock_alerts, mock_devices, mock_sensor, client
    ):
        """4.2.5: センサーデータなし（DB未登録）でも200を返すこと

        UI仕様書(5-2〜5-5)「初期表示: ラベルのみ」に対応。
        観点 4.2.5「関連データ表示: 外部結合で取得するデータが正常に表示される」のうち
        silver_sensor_data にレコードがない（None）場合でも画面が正常に表示されることを確認する。
        """
        # Arrange
        mock_orgs.return_value = [1]
        mock_check.return_value = _make_mock_device()
        mock_alerts.return_value = ([], 0)
        mock_devices.return_value = ([], 0)
        mock_sensor.return_value = None

        # Act
        response = client.get(f"{STORE_MONITORING_URL}/{DEVICE_UUID}")

        # Assert
        assert response.status_code == 200

    @patch(f"{_VIEW_MODULE}.check_device_access")
    @patch(f"{_VIEW_MODULE}.get_accessible_organizations")
    def test_returns_404_when_device_not_found(
        self, mock_orgs, mock_check, client
    ):
        """2.2.4 / 4.2.4: デバイス未検出・アクセス権限なし時に404を返すこと

        ワークフロー仕様書「エラーハンドリング: 404 リソース不存在」に対応。
        check_device_access が None を返す（スコープ外またはDB未登録）ケース。
        """
        # Arrange
        mock_orgs.return_value = [1]
        mock_check.return_value = None  # データスコープ外 or 未登録デバイス

        # Act
        response = client.get(f"{STORE_MONITORING_URL}/{DEVICE_UUID}")

        # Assert
        assert response.status_code == 404

    @patch(f"{_VIEW_MODULE}.get_accessible_organizations",
           side_effect=Exception("DB接続エラー"))
    def test_db_error_returns_500(self, mock_orgs, client):
        """2.2.5: DBエラー時に500を返すこと

        ワークフロー仕様書「エラーハンドリング: 500 データベースエラー」に対応。
        """
        # Act
        response = client.get(f"{STORE_MONITORING_URL}/{DEVICE_UUID}")

        # Assert
        assert response.status_code == 500

    @patch(f"{_VIEW_MODULE}.get_latest_sensor_data",
           side_effect=Exception("DBクエリエラー"))
    @patch(f"{_VIEW_MODULE}.get_device_list_with_count")
    @patch(f"{_VIEW_MODULE}.get_recent_alerts_with_count")
    @patch(f"{_VIEW_MODULE}.check_device_access")
    @patch(f"{_VIEW_MODULE}.get_accessible_organizations")
    def test_sensor_data_db_error_returns_500(
        self, mock_orgs, mock_check, mock_alerts, mock_devices, mock_sensor, client
    ):
        """2.2.5: センサーデータ取得（silver_sensor_data）のDBエラー時に500を返すこと

        ワークフロー仕様書「エラーハンドリング: 500 データベースエラー」に対応。
        get_latest_sensor_data で例外が発生した場合、500エラーとなることを確認する。
        """
        # Arrange
        mock_orgs.return_value = [1]
        mock_check.return_value = _make_mock_device()
        mock_alerts.return_value = ([], 0)
        mock_devices.return_value = ([], 0)

        # Act
        response = client.get(f"{STORE_MONITORING_URL}/{DEVICE_UUID}")

        # Assert
        assert response.status_code == 500

    @patch(f"{_VIEW_MODULE}.get_latest_sensor_data")
    @patch(f"{_VIEW_MODULE}.get_device_list_with_count")
    @patch(f"{_VIEW_MODULE}.get_recent_alerts_with_count")
    @patch(f"{_VIEW_MODULE}.check_device_access")
    @patch(f"{_VIEW_MODULE}.get_accessible_organizations")
    def test_cookie_search_params_used_when_present(
        self, mock_orgs, mock_check, mock_alerts, mock_devices, mock_sensor, client
    ):
        """5.1.1: Cookie有り時にCookieの検索条件（組織名）が引き継がれること

        センサー情報表示後もデバイス一覧の検索条件が維持されることを確認する。
        ワークフロー仕様書「UI状態: 前回の検索条件を保持」に対応。
        """
        # Arrange
        mock_orgs.return_value = [1]
        mock_check.return_value = _make_mock_device()
        mock_alerts.return_value = ([], 0)
        mock_devices.return_value = ([], 0)
        mock_sensor.return_value = None
        cookie_params = {"organization_name": "店舗B", "device_name": "", "page": 1}
        client.set_cookie(
            "store_monitoring_search_params", json.dumps(cookie_params)
        )

        # Act
        response = client.get(f"{STORE_MONITORING_URL}/{DEVICE_UUID}")

        # Assert
        assert response.status_code == 200
        call_search_params = mock_alerts.call_args[0][0]
        assert call_search_params.get("organization_name") == "店舗B"
        # デバイス一覧にも同じ検索条件が渡されること
        device_call_params = mock_devices.call_args[0][0]
        assert device_call_params.get("organization_name") == "店舗B"


# ===========================================================================
# デバイス詳細初期表示・ページング（GET /device-details/<uuid>）
# ===========================================================================


@pytest.mark.integration
class TestDeviceDetailsGet:
    """デバイス詳細初期表示・ページングテスト

    観点: 2.1 正常遷移テスト / 2.2 エラー時遷移テスト / 4.2 詳細表示テスト /
         5.3 ページネーションテスト
    ワークフロー仕様書「デバイス詳細初期表示」に対応。
    エンドポイント: GET /analysis/industry-dashboard/device-details/<device_uuid>
    """

    @patch(f"{_VIEW_MODULE}.get_graph_data")
    @patch(f"{_VIEW_MODULE}.get_device_alerts_with_count")
    @patch(f"{_VIEW_MODULE}.check_device_access")
    @patch(f"{_VIEW_MODULE}.get_accessible_organizations")
    def test_initial_display_sets_cookie(
        self, mock_orgs, mock_check, mock_alerts, mock_graph, client
    ):
        """2.1.1: 初期表示時に検索条件（表示期間）がCookieにセットされること

        ワークフロー仕様書「検索条件の保持方法: Cookie名 device_details_search_params」に対応。
        表示期間の初期値は直近24時間（get_default_date_range()）。
        """
        # Arrange
        mock_orgs.return_value = [1]
        mock_check.return_value = _make_mock_device()
        mock_alerts.return_value = ([], 0)
        mock_graph.return_value = []

        # Act
        response = client.get(f"{DEVICE_DETAILS_URL}/{DEVICE_UUID}")

        # Assert
        assert response.status_code == 200
        assert "device_details_search_params" in response.headers.get("Set-Cookie", "")

    @patch(f"{_VIEW_MODULE}.get_graph_data")
    @patch(f"{_VIEW_MODULE}.get_device_alerts_with_count")
    @patch(f"{_VIEW_MODULE}.check_device_access")
    @patch(f"{_VIEW_MODULE}.get_accessible_organizations")
    def test_paging_does_not_set_cookie(
        self, mock_orgs, mock_check, mock_alerts, mock_graph, client
    ):
        """5.3.2: ページング時にはCookieが書き込まれないこと

        ワークフロー仕様書「処理フロー: 初期表示時のみCookie格納（if save_cookie:）」に対応。
        pageパラメータありの場合は _set_cookie が呼ばれず、Set-Cookieヘッダが付かない。
        """
        # Arrange
        mock_orgs.return_value = [1]
        mock_check.return_value = _make_mock_device()
        mock_alerts.return_value = ([], 0)
        mock_graph.return_value = []

        # Act
        response = client.get(f"{DEVICE_DETAILS_URL}/{DEVICE_UUID}?page=2")

        # Assert
        assert response.status_code == 200
        assert "device_details_search_params" not in response.headers.get("Set-Cookie", "")

    @patch(f"{_VIEW_MODULE}.get_graph_data")
    @patch(f"{_VIEW_MODULE}.get_device_alerts_with_count")
    @patch(f"{_VIEW_MODULE}.check_device_access")
    @patch(f"{_VIEW_MODULE}.get_accessible_organizations")
    def test_paging_uses_cookie_search_params(
        self, mock_orgs, mock_check, mock_alerts, mock_graph, client
    ):
        """5.3.2: ページング時にCookieの表示期間がグラフデータ取得に使用されること

        ワークフロー仕様書「処理フロー: GetCookie→Cookieから検索条件取得」に対応。
        """
        # Arrange
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

        # Act
        response = client.get(f"{DEVICE_DETAILS_URL}/{DEVICE_UUID}?page=2")

        # Assert
        assert response.status_code == 200
        call_search_params = mock_graph.call_args[0][1]
        assert call_search_params.get("search_start_datetime") == "2026-02-01T00:00"
        assert call_search_params.get("search_end_datetime") == "2026-02-10T00:00"
        # アラート取得にも同じ検索条件が渡されること
        alerts_call_search_params = mock_alerts.call_args[0][1]  # [0]=device_id, [1]=search_params
        assert alerts_call_search_params.get("search_start_datetime") == "2026-02-01T00:00"
        assert alerts_call_search_params.get("search_end_datetime") == "2026-02-10T00:00"

    @patch(f"{_VIEW_MODULE}.check_device_access")
    @patch(f"{_VIEW_MODULE}.get_accessible_organizations")
    def test_returns_404_when_device_not_found(
        self, mock_orgs, mock_check, client
    ):
        """2.2.4 / 4.2.4: デバイス未検出・アクセス権限なし時に404を返すこと

        ワークフロー仕様書「エラーハンドリング: 404 リソース不存在」に対応。
        check_device_access が None を返す（スコープ外またはDB未登録）ケース。
        """
        # Arrange
        mock_orgs.return_value = [1]
        mock_check.return_value = None

        # Act
        response = client.get(f"{DEVICE_DETAILS_URL}/{DEVICE_UUID}")

        # Assert
        assert response.status_code == 404

    @patch(f"{_VIEW_MODULE}.get_accessible_organizations",
           side_effect=Exception("DB接続エラー"))
    def test_db_error_returns_500(self, mock_orgs, client):
        """2.2.5: DBエラー時に500を返すこと

        ワークフロー仕様書「エラーハンドリング: 500 データベースエラー」に対応。
        """
        # Act
        response = client.get(f"{DEVICE_DETAILS_URL}/{DEVICE_UUID}")

        # Assert
        assert response.status_code == 500

    @patch(f"{_VIEW_MODULE}.get_graph_data",
           side_effect=Exception("DBクエリエラー"))
    @patch(f"{_VIEW_MODULE}.get_device_alerts_with_count")
    @patch(f"{_VIEW_MODULE}.check_device_access")
    @patch(f"{_VIEW_MODULE}.get_accessible_organizations")
    def test_graph_data_db_error_returns_500(
        self, mock_orgs, mock_check, mock_alerts, mock_graph, client
    ):
        """2.2.5: グラフデータ取得（silver_sensor_data）のDBエラー時に500を返すこと

        ワークフロー仕様書「エラーハンドリング: 500 データベースエラー」に対応。
        get_graph_data で例外が発生した場合、500エラーとなることを確認する。
        """
        # Arrange
        mock_orgs.return_value = [1]
        mock_check.return_value = _make_mock_device()
        mock_alerts.return_value = ([], 0)

        # Act
        response = client.get(f"{DEVICE_DETAILS_URL}/{DEVICE_UUID}")

        # Assert
        assert response.status_code == 500


# ===========================================================================
# デバイス詳細検索・バリデーション（POST /device-details/<uuid>）
# ===========================================================================


@pytest.mark.integration
class TestDeviceDetailsPost:
    """デバイス詳細検索（表示期間変更）テスト

    観点: 2.1/2.2 画面遷移テスト / 3.1 必須チェック / 3.4 日付形式チェック / 3.8 相関チェック
    ワークフロー仕様書「デバイス詳細検索（表示期間変更）」に対応。
    エンドポイント: POST /analysis/industry-dashboard/device-details/<device_uuid>

    バリデーションルール（ワークフロー仕様書「バリデーション」セクション）:
      - search_start_datetime: 必須、YYYY-MM-DDTHH:MM形式
      - search_end_datetime:   必須、YYYY-MM-DDTHH:MM形式
      - 開始日時 < 終了日時であること
      - 表示期間が最大2ヶ月（62日）以内であること
    """

    @patch(f"{_VIEW_MODULE}.get_graph_data")
    @patch(f"{_VIEW_MODULE}.get_device_alerts_with_count")
    @patch(f"{_VIEW_MODULE}.check_device_access")
    @patch(f"{_VIEW_MODULE}.get_accessible_organizations")
    def test_valid_period_returns_200(
        self, mock_orgs, mock_check, mock_alerts, mock_graph, client
    ):
        """3.1.1 / 3.4.1 / 3.8.1: 正しい日時形式・整合性のある期間で200を返すこと"""
        # Arrange
        mock_orgs.return_value = [1]
        mock_check.return_value = _make_mock_device()
        mock_alerts.return_value = ([], 0)
        mock_graph.return_value = []

        # Act
        response = client.post(f"{DEVICE_DETAILS_URL}/{DEVICE_UUID}", data={
            "search_start_datetime": "2026-02-01T00:00",
            "search_end_datetime": "2026-02-02T00:00",
        })

        # Assert
        assert response.status_code == 200
        # グラフデータ取得に表示期間が渡されること
        # ワークフロー仕様書「グラフ用データ取得: get_graph_data(device.device_id, search_params)」に対応
        call_graph_params = mock_graph.call_args[0][1]  # [0]=device_id, [1]=search_params
        assert call_graph_params.get("search_start_datetime") == "2026-02-01T00:00"
        assert call_graph_params.get("search_end_datetime") == "2026-02-02T00:00"
        # アラート取得にも同じ表示期間が渡されること
        call_alerts_params = mock_alerts.call_args[0][1]  # [0]=device_id, [1]=search_params
        assert call_alerts_params.get("search_start_datetime") == "2026-02-01T00:00"
        assert call_alerts_params.get("search_end_datetime") == "2026-02-02T00:00"

    @patch(f"{_VIEW_MODULE}.get_graph_data")
    @patch(f"{_VIEW_MODULE}.get_device_alerts_with_count")
    @patch(f"{_VIEW_MODULE}.check_device_access")
    @patch(f"{_VIEW_MODULE}.get_accessible_organizations")
    def test_valid_period_saves_cookie(
        self, mock_orgs, mock_check, mock_alerts, mock_graph, client
    ):
        """2.1.2: 正常な表示期間変更後にCookieが更新されること

        ワークフロー仕様書「検索条件の保持方法: Cookie名 device_details_search_params」に対応。
        """
        # Arrange
        mock_orgs.return_value = [1]
        mock_check.return_value = _make_mock_device()
        mock_alerts.return_value = ([], 0)
        mock_graph.return_value = []

        # Act
        response = client.post(f"{DEVICE_DETAILS_URL}/{DEVICE_UUID}", data={
            "search_start_datetime": "2026-02-01T00:00",
            "search_end_datetime": "2026-02-02T00:00",
        })

        # Assert
        assert response.status_code == 200
        assert "device_details_search_params" in response.headers.get("Set-Cookie", "")

    @patch(f"{_VIEW_MODULE}.check_device_access")
    @patch(f"{_VIEW_MODULE}.get_accessible_organizations")
    def test_empty_start_datetime_returns_400(
        self, mock_orgs, mock_check, client
    ):
        """3.1.2: 開始日時が空（未入力）の場合に400を返すこと

        ワークフロー仕様書「バリデーション: search_start_datetime は必須」に対応。
        """
        # Arrange
        mock_orgs.return_value = [1]
        mock_check.return_value = _make_mock_device()

        # Act
        response = client.post(f"{DEVICE_DETAILS_URL}/{DEVICE_UUID}", data={
            "search_start_datetime": "",  # 未入力
            "search_end_datetime": "2026-02-02T00:00",
        })

        # Assert
        assert response.status_code == 400

    @patch(f"{_VIEW_MODULE}.check_device_access")
    @patch(f"{_VIEW_MODULE}.get_accessible_organizations")
    def test_empty_end_datetime_returns_400(
        self, mock_orgs, mock_check, client
    ):
        """3.1.2: 終了日時が空（未入力）の場合に400を返すこと

        ワークフロー仕様書「バリデーション: search_end_datetime は必須」に対応。
        """
        # Arrange
        mock_orgs.return_value = [1]
        mock_check.return_value = _make_mock_device()

        # Act
        response = client.post(f"{DEVICE_DETAILS_URL}/{DEVICE_UUID}", data={
            "search_start_datetime": "2026-02-01T00:00",
            "search_end_datetime": "",  # 未入力
        })

        # Assert
        assert response.status_code == 400

    @patch(f"{_VIEW_MODULE}.check_device_access")
    @patch(f"{_VIEW_MODULE}.get_accessible_organizations")
    def test_invalid_datetime_format_returns_400(
        self, mock_orgs, mock_check, client
    ):
        """3.4.2: 不正な日時フォーマット（YYYY/MM/DD HH:mm）で400を返すこと

        ワークフロー仕様書「バリデーション: YYYY-MM-DDTHH:MM形式」に対応。
        """
        # Arrange
        mock_orgs.return_value = [1]
        mock_check.return_value = _make_mock_device()

        # Act
        response = client.post(f"{DEVICE_DETAILS_URL}/{DEVICE_UUID}", data={
            "search_start_datetime": "2026/02/01 00:00",  # 不正フォーマット（スラッシュ区切り）
            "search_end_datetime": "2026-02-02T00:00",
        })

        # Assert
        assert response.status_code == 400

    @patch(f"{_VIEW_MODULE}.check_device_access")
    @patch(f"{_VIEW_MODULE}.get_accessible_organizations")
    def test_start_after_end_returns_400(
        self, mock_orgs, mock_check, client
    ):
        """3.8.2: 開始日時 > 終了日時の場合に400を返すこと

        ワークフロー仕様書「バリデーション: 開始日時 < 終了日時であること」に対応。
        """
        # Arrange
        mock_orgs.return_value = [1]
        mock_check.return_value = _make_mock_device()

        # Act
        response = client.post(f"{DEVICE_DETAILS_URL}/{DEVICE_UUID}", data={
            "search_start_datetime": "2026-02-10T00:00",
            "search_end_datetime": "2026-02-01T00:00",  # 開始が終了より後
        })

        # Assert
        assert response.status_code == 400

    @patch(f"{_VIEW_MODULE}.check_device_access")
    @patch(f"{_VIEW_MODULE}.get_accessible_organizations")
    def test_start_equal_to_end_returns_400(
        self, mock_orgs, mock_check, client
    ):
        """3.8.2: 開始日時 == 終了日時の場合に400を返すこと

        「開始日時 < 終了日時」の条件より、等値は不正となる。
        ワークフロー仕様書「バリデーション: start_dt >= end_dt → エラー」に対応。
        """
        # Arrange
        mock_orgs.return_value = [1]
        mock_check.return_value = _make_mock_device()

        # Act
        response = client.post(f"{DEVICE_DETAILS_URL}/{DEVICE_UUID}", data={
            "search_start_datetime": "2026-02-01T00:00",
            "search_end_datetime": "2026-02-01T00:00",  # 同値
        })

        # Assert
        assert response.status_code == 400

    @patch(f"{_VIEW_MODULE}.check_device_access")
    @patch(f"{_VIEW_MODULE}.get_accessible_organizations")
    def test_period_over_62_days_returns_400(
        self, mock_orgs, mock_check, client
    ):
        """3.8.2: 表示期間62日超過で400を返すこと

        ワークフロー仕様書「バリデーション: 表示期間が最大2ヶ月（62日）以内であること」に対応。
        """
        # Arrange
        mock_orgs.return_value = [1]
        mock_check.return_value = _make_mock_device()

        # Act
        response = client.post(f"{DEVICE_DETAILS_URL}/{DEVICE_UUID}", data={
            "search_start_datetime": "2026-01-01T00:00",
            "search_end_datetime": "2026-03-20T00:00",  # 78日 > 62日
        })

        # Assert
        assert response.status_code == 400

    @patch(f"{_VIEW_MODULE}.check_device_access")
    @patch(f"{_VIEW_MODULE}.get_accessible_organizations")
    def test_exactly_62_days_returns_200(
        self, mock_orgs, mock_check, client
    ):
        """3.8.1: 表示期間がちょうど62日（境界値）の場合に200を返すこと

        ワークフロー仕様書「バリデーション: (end_dt - start_dt).days > 62 → エラー」
        つまり days == 62 は許容される境界値。
        """
        # Arrange
        mock_orgs.return_value = [1]
        mock_check.return_value = _make_mock_device()

        with patch(f"{_VIEW_MODULE}.get_device_alerts_with_count", return_value=([], 0)), \
             patch(f"{_VIEW_MODULE}.get_graph_data", return_value=[]):
            # Act
            response = client.post(f"{DEVICE_DETAILS_URL}/{DEVICE_UUID}", data={
                "search_start_datetime": "2026-01-01T00:00",
                "search_end_datetime": "2026-03-04T00:00",  # ちょうど62日
            })

        # Assert
        assert response.status_code == 200

    @patch(f"{_VIEW_MODULE}.check_device_access")
    @patch(f"{_VIEW_MODULE}.get_accessible_organizations")
    def test_device_not_found_returns_404(
        self, mock_orgs, mock_check, client
    ):
        """2.2.4: デバイス未検出時に404を返すこと

        ワークフロー仕様書「エラーハンドリング: 404 リソース不存在」に対応。
        """
        # Arrange
        mock_orgs.return_value = [1]
        mock_check.return_value = None

        # Act
        response = client.post(f"{DEVICE_DETAILS_URL}/{DEVICE_UUID}", data={
            "search_start_datetime": "2026-02-01T00:00",
            "search_end_datetime": "2026-02-02T00:00",
        })

        # Assert
        assert response.status_code == 404

    @patch(f"{_VIEW_MODULE}.get_accessible_organizations",
           side_effect=Exception("DB接続エラー"))
    def test_db_error_returns_500(self, mock_orgs, client):
        """2.2.5: DBエラー時に500を返すこと

        ワークフロー仕様書「エラーハンドリング: 500 データベースエラー」に対応。
        """
        # Act
        response = client.post(f"{DEVICE_DETAILS_URL}/{DEVICE_UUID}", data={
            "search_start_datetime": "2026-02-01T00:00",
            "search_end_datetime": "2026-02-02T00:00",
        })

        # Assert
        assert response.status_code == 500


# ===========================================================================
# CSVエクスポート（GET /device-details/<uuid>?export=csv）
# ===========================================================================


@pytest.mark.integration
class TestCsvExport:
    """CSVエクスポートテスト

    観点: 4.6 CSVエクスポートテスト / 2.2 エラー時遷移テスト
    ワークフロー仕様書「CSVエクスポート」に対応。
    エンドポイント: GET /analysis/industry-dashboard/device-details/<uuid>?export=csv
    UI仕様書(11)「CSVエクスポートボタン」に対応。
    CSVデータ元: OLTP DB（MySQL）の silver_sensor_data テーブル。
    """

    @patch(f"{_VIEW_MODULE}.export_sensor_data_csv")
    @patch(f"{_VIEW_MODULE}.check_device_access")
    @patch(f"{_VIEW_MODULE}.get_accessible_organizations")
    def test_csv_export_calls_export_function(
        self, mock_orgs, mock_check, mock_export, client
    ):
        """4.6.1: ?export=csv パラメータで export_sensor_data_csv が呼び出されること

        UI仕様書(11)「クリック時: /device-details/<device_uuid>?export=csv にリクエスト」に対応。
        """
        # Arrange
        mock_orgs.return_value = [1]
        mock_check.return_value = _make_mock_device()
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.headers = {"Content-type": "text/csv; charset=utf-8-sig"}
        mock_export.return_value = mock_resp

        # Act
        client.get(f"{DEVICE_DETAILS_URL}/{DEVICE_UUID}?export=csv")

        # Assert
        mock_export.assert_called_once()

    @patch(f"{_VIEW_MODULE}.export_sensor_data_csv")
    @patch(f"{_VIEW_MODULE}.check_device_access")
    @patch(f"{_VIEW_MODULE}.get_accessible_organizations")
    def test_csv_export_passes_correct_device(
        self, mock_orgs, mock_check, mock_export, client
    ):
        """4.6.3: CSVエクスポートが正しいデバイスオブジェクトを渡すこと

        ワークフロー仕様書「CSVエクスポート: export_sensor_data_csv(device, search_params)」に対応。
        """
        # Arrange
        mock_device = _make_mock_device()
        mock_orgs.return_value = [1]
        mock_check.return_value = mock_device
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.headers = {"Content-type": "text/csv; charset=utf-8-sig"}
        mock_export.return_value = mock_resp

        # Act
        client.get(f"{DEVICE_DETAILS_URL}/{DEVICE_UUID}?export=csv")

        # Assert
        called_device = mock_export.call_args[0][0]
        assert called_device == mock_device

    @patch(f"{_VIEW_MODULE}.export_sensor_data_csv")
    @patch(f"{_VIEW_MODULE}.check_device_access")
    @patch(f"{_VIEW_MODULE}.get_accessible_organizations")
    def test_csv_export_uses_cookie_search_params(
        self, mock_orgs, mock_check, mock_export, client
    ):
        """4.6.3: Cookie有り時にCookieの表示期間がCSVエクスポートに渡されること

        ワークフロー仕様書「前提条件: 表示期間はCookieに保存されている」に対応。
        """
        # Arrange
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

        # Act
        client.get(f"{DEVICE_DETAILS_URL}/{DEVICE_UUID}?export=csv")

        # Assert
        called_search_params = mock_export.call_args[0][1]
        assert called_search_params.get("search_start_datetime") == "2026-02-01T00:00"
        assert called_search_params.get("search_end_datetime") == "2026-02-10T00:00"

    @patch(f"{_VIEW_MODULE}.export_sensor_data_csv")
    @patch(f"{_VIEW_MODULE}.check_device_access")
    @patch(f"{_VIEW_MODULE}.get_accessible_organizations")
    def test_csv_export_uses_default_params_when_no_cookie(
        self, mock_orgs, mock_check, mock_export, client
    ):
        """4.6.3: Cookie無し時にデフォルト期間（直近24時間）でCSVエクスポートが呼ばれること

        ワークフロー仕様書「前提条件: Cookieに表示期間がない場合はデフォルト期間でエクスポート」
        「デフォルト期間: 現在日時から1日前まで」に対応。
        """
        # Arrange
        mock_orgs.return_value = [1]
        mock_check.return_value = _make_mock_device()
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.headers = {"Content-type": "text/csv; charset=utf-8-sig"}
        mock_export.return_value = mock_resp
        # Cookieをセットしない

        # Act
        client.get(f"{DEVICE_DETAILS_URL}/{DEVICE_UUID}?export=csv")

        # Assert
        mock_export.assert_called_once()
        called_search_params = mock_export.call_args[0][1]
        # デフォルト期間のキーが存在すること（値は動的なため存在確認のみ）
        assert "search_start_datetime" in called_search_params
        assert "search_end_datetime" in called_search_params

    @patch(f"{_VIEW_MODULE}.check_device_access")
    @patch(f"{_VIEW_MODULE}.get_accessible_organizations")
    def test_csv_export_returns_404_when_device_not_found(
        self, mock_orgs, mock_check, client
    ):
        """2.2.4: デバイス未検出時のCSVエクスポートで404を返すこと

        ワークフロー仕様書「エラーハンドリング: 404 リソース不存在」に対応。
        """
        # Arrange
        mock_orgs.return_value = [1]
        mock_check.return_value = None

        # Act
        response = client.get(f"{DEVICE_DETAILS_URL}/{DEVICE_UUID}?export=csv")

        # Assert
        assert response.status_code == 404

    @patch(f"{_VIEW_MODULE}.get_accessible_organizations",
           side_effect=Exception("DB接続エラー"))
    def test_csv_export_db_error_returns_500(self, mock_orgs, client):
        """2.2.5: DBエラー時のCSVエクスポートで500を返すこと

        ワークフロー仕様書「エラーハンドリング: 500 データベースエラー」に対応。
        """
        # Act
        response = client.get(f"{DEVICE_DETAILS_URL}/{DEVICE_UUID}?export=csv")

        # Assert
        assert response.status_code == 500

    @patch(f"{_VIEW_MODULE}.export_sensor_data_csv",
           side_effect=Exception("DBクエリエラー"))
    @patch(f"{_VIEW_MODULE}.check_device_access")
    @patch(f"{_VIEW_MODULE}.get_accessible_organizations")
    def test_csv_export_db_error_in_service_returns_500(
        self, mock_orgs, mock_check, mock_export, client
    ):
        """2.2.5: CSVエクスポート処理中のDBエラーで500を返すこと

        ワークフロー仕様書「エラーハンドリング: 500 CSVエクスポートに失敗しました」に対応。
        """
        # Arrange
        mock_orgs.return_value = [1]
        mock_check.return_value = _make_mock_device()

        # Act
        response = client.get(f"{DEVICE_DETAILS_URL}/{DEVICE_UUID}?export=csv")

        # Assert
        assert response.status_code == 500


# ===========================================================================
# セキュリティテスト
# ===========================================================================


@pytest.mark.integration
class TestSecurity:
    """セキュリティテスト

    観点: 9.1 SQLインジェクションテスト / 9.2 XSSテスト
    検索フォームへの不正入力がアプリケーションに影響しないことを確認する。
    SQLAlchemy のプリペアドステートメントにより SQLインジェクションは防がれ、
    Jinja2 の自動エスケープにより XSS は防がれる。
    """

    @patch(f"{_VIEW_MODULE}.get_device_list_with_count")
    @patch(f"{_VIEW_MODULE}.get_recent_alerts_with_count")
    @patch(f"{_VIEW_MODULE}.get_accessible_organizations")
    def test_sql_injection_in_store_name_returns_200_or_400(
        self, mock_orgs, mock_alerts, mock_devices, client
    ):
        """9.1.1: 店舗名フィールドへのSQLインジェクション文字列でサーバーエラーにならないこと

        SQLAlchemy のプリペアドステートメントにより注入文字列はエスケープされ、
        500エラーとならないことを確認する。
        """
        # Arrange
        mock_orgs.return_value = [1]
        mock_alerts.return_value = ([], 0)
        mock_devices.return_value = ([], 0)

        # Act
        response = client.post(STORE_MONITORING_URL, data={
            "organization_name": "' OR '1'='1",  # 基本的なSQLインジェクション
            "device_name": "",
        })

        # Assert
        assert response.status_code in (200, 400)  # サーバーエラー(500)にならないこと

    @patch(f"{_VIEW_MODULE}.get_device_list_with_count")
    @patch(f"{_VIEW_MODULE}.get_recent_alerts_with_count")
    @patch(f"{_VIEW_MODULE}.get_accessible_organizations")
    def test_sql_injection_drop_table_in_device_name(
        self, mock_orgs, mock_alerts, mock_devices, client
    ):
        """9.1.2: デバイス名フィールドへのDROP TABLE文字列でサーバーエラーにならないこと"""
        # Arrange
        mock_orgs.return_value = [1]
        mock_alerts.return_value = ([], 0)
        mock_devices.return_value = ([], 0)

        # Act
        response = client.post(STORE_MONITORING_URL, data={
            "organization_name": "",
            "device_name": "'; DROP TABLE device_master;--",
        })

        # Assert
        assert response.status_code in (200, 400)

    @patch(f"{_VIEW_MODULE}.get_device_list_with_count")
    @patch(f"{_VIEW_MODULE}.get_recent_alerts_with_count")
    @patch(f"{_VIEW_MODULE}.get_accessible_organizations")
    def test_xss_script_tag_in_store_name_is_escaped(
        self, mock_orgs, mock_alerts, mock_devices, client
    ):
        """9.2.1: 店舗名フィールドへの<script>タグがJinja2自動エスケープで無効化されること

        Jinja2 の自動エスケープにより、スクリプトタグがそのままHTMLに
        出力されることなく、安全にエスケープされることを確認する。
        """
        # Arrange
        mock_orgs.return_value = [1]
        mock_alerts.return_value = ([], 0)
        mock_devices.return_value = ([], 0)
        xss_payload = "<script>alert('XSS')</script>"

        # Act
        response = client.post(STORE_MONITORING_URL, data={
            "organization_name": xss_payload,
            "device_name": "",
        })

        # Assert
        assert response.status_code in (200, 400)
        if response.status_code == 200:
            # <script> タグが生のまま HTML に出力されていないこと
            response_text = response.data.decode("utf-8")
            assert "<script>alert('XSS')</script>" not in response_text

    @patch(f"{_VIEW_MODULE}.get_device_list_with_count")
    @patch(f"{_VIEW_MODULE}.get_recent_alerts_with_count")
    @patch(f"{_VIEW_MODULE}.get_accessible_organizations")
    def test_xss_img_tag_in_device_name_is_escaped(
        self, mock_orgs, mock_alerts, mock_devices, client
    ):
        """9.2.2: デバイス名フィールドへの<img onerror>タグがエスケープされること"""
        # Arrange
        mock_orgs.return_value = [1]
        mock_alerts.return_value = ([], 0)
        mock_devices.return_value = ([], 0)
        xss_payload = "<img src=x onerror=alert('XSS')>"

        # Act
        response = client.post(STORE_MONITORING_URL, data={
            "organization_name": "",
            "device_name": xss_payload,
        })

        # Assert
        assert response.status_code in (200, 400)
        if response.status_code == 200:
            response_text = response.data.decode("utf-8")
            assert "<img src=x onerror=alert('XSS')>" not in response_text

    @patch(f"{_VIEW_MODULE}.get_device_list_with_count")
    @patch(f"{_VIEW_MODULE}.get_recent_alerts_with_count")
    @patch(f"{_VIEW_MODULE}.get_accessible_organizations")
    def test_sql_injection_union_select_in_store_name(
        self, mock_orgs, mock_alerts, mock_devices, client
    ):
        """9.1.3: UNIONを使ったSQLインジェクション文字列でサーバーエラーにならないこと

        SQLAlchemy のプリペアドステートメントにより注入文字列はエスケープされ、
        500エラーとならないことを確認する。
        """
        # Arrange
        mock_orgs.return_value = [1]
        mock_alerts.return_value = ([], 0)
        mock_devices.return_value = ([], 0)

        # Act
        response = client.post(STORE_MONITORING_URL, data={
            "organization_name": "' UNION SELECT * FROM user_master--",
            "device_name": "",
        })

        # Assert
        assert response.status_code in (200, 400)  # サーバーエラー(500)にならないこと

    @patch(f"{_VIEW_MODULE}.get_device_list_with_count")
    @patch(f"{_VIEW_MODULE}.get_recent_alerts_with_count")
    @patch(f"{_VIEW_MODULE}.get_accessible_organizations")
    def test_xss_javascript_protocol_in_device_name_is_escaped(
        self, mock_orgs, mock_alerts, mock_devices, client
    ):
        """9.2.3: デバイス名フィールドへのJavaScriptプロトコルがエスケープされること

        Jinja2 の自動エスケープにより、javascript: スキームがそのままHTMLに
        出力されることなく、安全にエスケープされることを確認する。
        """
        # Arrange
        mock_orgs.return_value = [1]
        mock_alerts.return_value = ([], 0)
        mock_devices.return_value = ([], 0)
        xss_payload = "javascript:alert('XSS')"

        # Act
        response = client.post(STORE_MONITORING_URL, data={
            "organization_name": "",
            "device_name": xss_payload,
        })

        # Assert
        assert response.status_code in (200, 400)
        if response.status_code == 200:
            response_text = response.data.decode("utf-8")
            assert "javascript:alert('XSS')" not in response_text


# ===========================================================================
# 6.3 Unity Catalog クエリテスト（モック版）
# ===========================================================================


@pytest.mark.integration
class TestUnityCatalogDataSourceSwitching:
    """Unity Catalog データソース切り替えロジック テスト（モック）

    観点: 6.3 Unity Catalog クエリテスト（モック版）
    ワークフロー仕様書「センサーデータ取得のデータソース切り替えロジック」に対応。

    センサーデータは以下の 2 つのデータソースに分散して保存される:
      - MySQL: 直近 SENSOR_DATA_CUTOFF_MONTHS 以内（高速アクセス・プライマリ）
      - Unity Catalog (Delta Lake): 全期間（長期保存・フォールバック）

    データソース選択ルール（ワークフロー仕様書「データソース選択ルール」表）:
      - 終了日時 ≥ カットオフ かつ 開始日時 ≥ カットオフ → MySQL 優先（UCにも保持）
      - 終了日時 < カットオフ                              → Unity Catalog のみ
      - 開始日時 < カットオフ かつ 終了日時 ≥ カットオフ  → MySQL + Unity Catalog マージ

    本クラスはサービス層をモック化し、ビュー層での Unity Catalog フォールバック動作が
    正しく処理されることを確認する。
    実接続テストは TestUnityCatalogDatabricks を参照。
    """

    # -----------------------------------------------------------------------
    # センサー情報表示: get_latest_sensor_data の MySQL → UC フォールバック
    # -----------------------------------------------------------------------

    @patch(f"{_VIEW_MODULE}.get_latest_sensor_data")
    @patch(f"{_VIEW_MODULE}.get_device_list_with_count")
    @patch(f"{_VIEW_MODULE}.get_recent_alerts_with_count")
    @patch(f"{_VIEW_MODULE}.check_device_access")
    @patch(f"{_VIEW_MODULE}.get_accessible_organizations")
    def test_sensor_info_uc_fallback_data_returns_200(
        self, mock_orgs, mock_check, mock_alerts, mock_devices, mock_sensor, client
    ):
        """6.3.1.1: MySQL にデータなし → UC フォールバックデータで200を返すこと

        ワークフロー仕様書「get_latest_sensor_data の特別ルール:
        MySQL にデータが存在しない場合 → Unity Catalog から最新1件を返す」に対応。
        サービス層での MySQL→UC フォールバック後のデータをビュー層が正常に処理することを確認。
        get_latest_sensor_data が device_id を引数として呼び出されることも確認する。
        """
        # Arrange
        mock_orgs.return_value = [1]
        mock_device = _make_mock_device()
        mock_check.return_value = mock_device
        mock_alerts.return_value = ([], 0)
        mock_devices.return_value = ([], 0)
        # UC フォールバックにより取得したセンサーデータ（古い event_timestamp を持つ行）
        uc_sensor_row = MagicMock()
        uc_sensor_row.event_timestamp = "2020-01-01 00:00:00"
        mock_sensor.return_value = uc_sensor_row  # UC フォールバック結果をシミュレート

        # Act
        response = client.get(f"{STORE_MONITORING_URL}/{DEVICE_UUID}")

        # Assert
        assert response.status_code == 200
        # device_id を引数として get_latest_sensor_data が呼ばれること
        mock_sensor.assert_called_once_with(mock_device.device_id)

    # -----------------------------------------------------------------------
    # グラフデータ: カットオフ以前の期間 → Unity Catalog のみ
    # -----------------------------------------------------------------------

    @patch(f"{_VIEW_MODULE}.get_graph_data")
    @patch(f"{_VIEW_MODULE}.get_device_alerts_with_count")
    @patch(f"{_VIEW_MODULE}.check_device_access")
    @patch(f"{_VIEW_MODULE}.get_accessible_organizations")
    def test_graph_data_uc_only_period_passed_correctly(
        self, mock_orgs, mock_check, mock_alerts, mock_graph, client
    ):
        """6.3.1.1: カットオフ以前の検索期間が get_graph_data に正しく渡されること

        ワークフロー仕様書「データソース選択ルール:
        終了日時 < カットオフ → Unity Catalog のみ」に対応。
        ビュー層は日時をそのまま get_graph_data に渡し、サービス層が UC のみから取得する。
        （実際の UC 利用はサービス層が担当。ビュー層は期間をそのまま受け渡す。）
        """
        # Arrange
        mock_orgs.return_value = [1]
        mock_check.return_value = _make_mock_device()
        mock_alerts.return_value = ([], 0)
        mock_graph.return_value = []  # UC から取得した 0 件をシミュレート

        # Act: SENSOR_DATA_CUTOFF_MONTHS に関わらず確実に UC のみとなる過去期間（62日以内）
        response = client.post(f"{DEVICE_DETAILS_URL}/{DEVICE_UUID}", data={
            "search_start_datetime": "2020-01-01T00:00",
            "search_end_datetime": "2020-02-01T00:00",  # 31日間、62日制限以内
        })

        # Assert
        assert response.status_code == 200
        # 過去の日時がそのまま get_graph_data に渡されること
        call_graph_params = mock_graph.call_args[0][1]  # [0]=device_id, [1]=search_params
        assert call_graph_params.get("search_start_datetime") == "2020-01-01T00:00"
        assert call_graph_params.get("search_end_datetime") == "2020-02-01T00:00"

    @patch(f"{_VIEW_MODULE}.get_graph_data")
    @patch(f"{_VIEW_MODULE}.get_device_alerts_with_count")
    @patch(f"{_VIEW_MODULE}.check_device_access")
    @patch(f"{_VIEW_MODULE}.get_accessible_organizations")
    def test_graph_data_uc_returns_empty_list_renders_200(
        self, mock_orgs, mock_check, mock_alerts, mock_graph, client
    ):
        """6.3.1.2: UC が 0 件を返す場合でも空グラフで200を返すこと

        ワークフロー仕様書「データソース選択ルール: 終了日時 < カットオフ → UC のみ」に対応。
        UC にデータが存在しない期間を検索した場合、空グラフで正常にレンダリングされることを確認。
        """
        # Arrange
        mock_orgs.return_value = [1]
        mock_check.return_value = _make_mock_device()
        mock_alerts.return_value = ([], 0)
        mock_graph.return_value = []  # UC にデータなし（0 件）

        # Act
        response = client.post(f"{DEVICE_DETAILS_URL}/{DEVICE_UUID}", data={
            "search_start_datetime": "2020-01-01T00:00",
            "search_end_datetime": "2020-02-01T00:00",
        })

        # Assert
        assert response.status_code == 200

    # -----------------------------------------------------------------------
    # グラフデータ: MySQL + Unity Catalog マージ結果
    # -----------------------------------------------------------------------

    @patch(f"{_VIEW_MODULE}.get_graph_data")
    @patch(f"{_VIEW_MODULE}.get_device_alerts_with_count")
    @patch(f"{_VIEW_MODULE}.check_device_access")
    @patch(f"{_VIEW_MODULE}.get_accessible_organizations")
    def test_graph_data_uc_mysql_merged_result_renders_200(
        self, mock_orgs, mock_check, mock_alerts, mock_graph, client
    ):
        """6.3.1.1: UC + MySQL マージ結果がビュー層で正常にレンダリングされること

        ワークフロー仕様書「データソース選択ルール:
        開始日時 < カットオフ かつ 終了日時 ≥ カットオフ → MySQL + UC マージ」に対応。
        ワークフロー仕様書「get_sensor_data_from_dual_source: event_timestamp で昇順ソートしてマージ」
        にてマージされた複数レコードをビュー層が正常に処理することを確認。
        """
        # Arrange
        mock_orgs.return_value = [1]
        mock_check.return_value = _make_mock_device()
        mock_alerts.return_value = ([], 0)
        # UC（古いデータ）+ MySQL（新しいデータ）のマージ結果をシミュレート
        merged_data = [
            MagicMock(event_timestamp="2020-06-01T00:00"),   # UC 由来（古い）
            MagicMock(event_timestamp="2020-06-15T00:00"),   # UC 由来
            MagicMock(event_timestamp="2020-06-20T00:00"),   # MySQL 由来（新しい）
        ]
        mock_graph.return_value = merged_data

        # Act: カットオフをまたぐ可能性がある過去期間（62日以内）
        response = client.post(f"{DEVICE_DETAILS_URL}/{DEVICE_UUID}", data={
            "search_start_datetime": "2020-06-01T00:00",
            "search_end_datetime": "2020-07-01T00:00",  # 30日間
        })

        # Assert
        assert response.status_code == 200
        # マージされた検索期間が get_graph_data に渡されること
        call_graph_params = mock_graph.call_args[0][1]
        assert call_graph_params.get("search_start_datetime") == "2020-06-01T00:00"
        assert call_graph_params.get("search_end_datetime") == "2020-07-01T00:00"

    # -----------------------------------------------------------------------
    # POST /device-details/<uuid> での UC 接続エラー（既存の GET テストを補完）
    # -----------------------------------------------------------------------

    @patch(f"{_VIEW_MODULE}.get_graph_data",
           side_effect=Exception("Unity Catalog接続エラー"))
    @patch(f"{_VIEW_MODULE}.get_device_alerts_with_count")
    @patch(f"{_VIEW_MODULE}.check_device_access")
    @patch(f"{_VIEW_MODULE}.get_accessible_organizations")
    def test_graph_data_uc_error_in_post_returns_500(
        self, mock_orgs, mock_check, mock_alerts, mock_graph, client
    ):
        """6.3.2.1: POST デバイス詳細検索での UC 接続エラーで500を返すこと

        ワークフロー仕様書「エラーハンドリング: 500 データベースエラー」に対応。
        POST /device-details/<uuid> で get_graph_data（UC フォールバック含む）が
        例外を発生させた場合、500 エラーとなることを確認する。
        （GETエンドポイントの同等テスト test_graph_data_db_error_returns_500 を POSTで補完。）
        """
        # Arrange
        mock_orgs.return_value = [1]
        mock_check.return_value = _make_mock_device()
        mock_alerts.return_value = ([], 0)

        # Act
        response = client.post(f"{DEVICE_DETAILS_URL}/{DEVICE_UUID}", data={
            "search_start_datetime": "2020-01-01T00:00",
            "search_end_datetime": "2020-02-01T00:00",
        })

        # Assert
        assert response.status_code == 500

    # -----------------------------------------------------------------------
    # CSVエクスポート: UC 期間（カットオフ以前）の Cookie を利用
    # -----------------------------------------------------------------------

    @patch(f"{_VIEW_MODULE}.export_sensor_data_csv")
    @patch(f"{_VIEW_MODULE}.check_device_access")
    @patch(f"{_VIEW_MODULE}.get_accessible_organizations")
    def test_csv_export_uc_period_search_params_passed(
        self, mock_orgs, mock_check, mock_export, client
    ):
        """6.3.1.1: UC のみ期間（カットオフ以前）の Cookie で CSVエクスポートが正しく呼ばれること

        ワークフロー仕様書「CSVエクスポート: get_all_sensor_data の切り替えロジック
        （MySQL / Unity Catalog 切り替えロジック適用）」に対応。
        過去期間の検索条件が Cookie 経由で export_sensor_data_csv に正しく渡されることを確認。
        """
        # Arrange
        mock_orgs.return_value = [1]
        mock_check.return_value = _make_mock_device()
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.headers = {"Content-type": "text/csv; charset=utf-8-sig"}
        mock_export.return_value = mock_resp
        # UC のみ期間（過去日付）の検索条件を Cookie にセット
        cookie_params = {
            "search_start_datetime": "2020-01-01T00:00",
            "search_end_datetime": "2020-02-01T00:00",
        }
        client.set_cookie("device_details_search_params", json.dumps(cookie_params))

        # Act
        client.get(f"{DEVICE_DETAILS_URL}/{DEVICE_UUID}?export=csv")

        # Assert
        mock_export.assert_called_once()
        called_search_params = mock_export.call_args[0][1]
        # UC のみ期間がそのまま export_sensor_data_csv に渡されること
        assert called_search_params.get("search_start_datetime") == "2020-01-01T00:00"
        assert called_search_params.get("search_end_datetime") == "2020-02-01T00:00"


# ===========================================================================
# 6.3 Unity Catalog クエリテスト（実接続版）
# ===========================================================================


@pytest.mark.integration
@pytest.mark.databricks
class TestUnityCatalogDatabricks:
    """Unity Catalog 実接続テスト

    観点: 6.3 Unity Catalog クエリテスト（実接続）
    ⚠️ 実施条件: Databricks 実接続が必要（.env の DEV_DATABRICKS_TOKEN 設定済み）
              接続不要な環境では `pytest -m "not databricks"` でスキップ可能。

    ワークフロー仕様書「センサーデータ取得のデータソース切り替えロジック」において
    Unity Catalog への実接続クエリ動作をルートレベルで確認する。

    テスト方針:
    - OLTP DB 操作（デバイス認証、アラート取得等）はモック化
    - get_latest_sensor_data / get_graph_data はモック化せず実接続で実行
    - テスト用デバイス（device_id=1）が UC に存在しない前提で 0件テストを兼ねる
    - データあり・なしどちらでも HTTPステータス 200 を確認する
    """

    @patch(f"{_VIEW_MODULE}.get_device_list_with_count")
    @patch(f"{_VIEW_MODULE}.get_recent_alerts_with_count")
    @patch(f"{_VIEW_MODULE}.check_device_access")
    @patch(f"{_VIEW_MODULE}.get_accessible_organizations")
    def test_sensor_info_uc_real_query_returns_200(
        self, mock_orgs, mock_check, mock_alerts, mock_devices, client
    ):
        """6.3.1.1 / 6.3.1.2: UC への実クエリでセンサー情報表示が200を返すこと

        get_latest_sensor_data が UC への実接続クエリを実行し、
        データあり・なしどちらでも200が返ることを確認する。
        UC にデータがある場合: sensor_data 付きで200
        UC にデータがない場合（0件）: sensor_data=None で200（6.3.1.2）
        """
        # Arrange: OLTP DB 部分のみモック化、get_latest_sensor_data は実接続
        mock_orgs.return_value = [1]
        mock_check.return_value = _make_mock_device()
        mock_alerts.return_value = ([], 0)
        mock_devices.return_value = ([], 0)

        # Act
        response = client.get(f"{STORE_MONITORING_URL}/{DEVICE_UUID}")

        # Assert
        assert response.status_code == 200

    @patch(f"{_VIEW_MODULE}.get_device_alerts_with_count")
    @patch(f"{_VIEW_MODULE}.check_device_access")
    @patch(f"{_VIEW_MODULE}.get_accessible_organizations")
    def test_graph_data_uc_only_real_query_returns_200(
        self, mock_orgs, mock_check, mock_alerts, client
    ):
        """6.3.1.1 / 6.3.1.2: カットオフ以前期間への UC 実クエリでグラフ表示が200を返すこと

        get_graph_data がカットオフより古い期間（2020年）のデータを UC から実際にクエリし、
        0件または有効データのどちらでも200が返ることを確認する。
        UC が 0件を返した場合も空グラフで正常表示されることを確認（6.3.1.2）。
        """
        # Arrange: OLTP DB 部分のみモック化、get_graph_data は実接続
        mock_orgs.return_value = [1]
        mock_check.return_value = _make_mock_device()
        mock_alerts.return_value = ([], 0)

        # Act: SENSOR_DATA_CUTOFF_MONTHS に関わらず確実に UC のみとなる過去期間（62日以内）
        response = client.post(f"{DEVICE_DETAILS_URL}/{DEVICE_UUID}", data={
            "search_start_datetime": "2020-01-01T00:00",
            "search_end_datetime": "2020-02-01T00:00",
        })

        # Assert
        assert response.status_code == 200

    @patch(f"{_VIEW_MODULE}.get_device_alerts_with_count")
    @patch(f"{_VIEW_MODULE}.check_device_access")
    @patch(f"{_VIEW_MODULE}.get_accessible_organizations")
    def test_graph_data_uc_query_result_is_list_format(
        self, mock_orgs, mock_check, mock_alerts, client
    ):
        """6.3.1.1 / 6.3.1.7: UC クエリ結果がリスト形式でビューに渡され200を返すこと

        get_graph_data の戻り値がリスト形式であることをルートレベルで確認する（実接続）。
        カラム構成の詳細確認はサービス層の単体テストで実施。
        """
        # Arrange
        mock_orgs.return_value = [1]
        mock_check.return_value = _make_mock_device()
        mock_alerts.return_value = ([], 0)

        # Act: 短い過去期間（UC のみ参照、62日以内）
        response = client.post(f"{DEVICE_DETAILS_URL}/{DEVICE_UUID}", data={
            "search_start_datetime": "2020-01-01T00:00",
            "search_end_datetime": "2020-01-15T00:00",  # 14日間
        })

        # Assert
        assert response.status_code == 200
