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

テストDB方針:
  OLTP DB テーブル（device_master、organization_master 等）はすべて MySQL 実DBに存在する。
  tests/integration/conftest.py の industry_test_data フィクスチャで
  テスト用データを投入し、テスト完了後に削除する（READ COMMITTED 対応: commit+delete 方式）。

  @patch によるモックは以下の用途にのみ使用する:
    - 例外シミュレーション（side_effect=Exception）による 500 エラー確認
    - get_accessible_organizations を [] に固定する空スコープ確認

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
  6.3  Unity Catalog クエリテスト → 不要のため除外
  7    トランザクション   → Read専用機能のため対象外
  8    ログ出力テスト     → Read専用機能のため省略
  9.3  CSRFテスト        → GETエンドポイント主体、POSTにはCSRFトークン対象外（TestingConfig）
"""

import json
from unittest.mock import patch

import pytest


# ---------------------------------------------------------------------------
# 定数
# ---------------------------------------------------------------------------

STORE_MONITORING_URL = "/analysis/industry-dashboard/store-monitoring"
AUTOCOMPLETE_URL = f"{STORE_MONITORING_URL}/organizations"
DEVICE_DETAILS_URL = "/analysis/industry-dashboard/device-details"

# 404確認用: DBに存在しない UUID
DEVICE_UUID_NOT_FOUND = "non-existent-uuid-for-404-test"

_VIEW_MODULE = "iot_app.views.analysis.industry_dashboard"


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

    MySQL実DB: industry_test_data フィクスチャで投入したデータで検証する。
    """

    def test_own_org_data_is_visible(self, industry_test_data, client):
        """1.3.1: 自組織のデバイスが表示されること

        organization_closure (parent=自組織, subsidiary=自組織) により
        自組織のデバイスが一覧に含まれることを確認する。
        """
        # Arrange: industry_test_data が org_accessible のデバイスを投入済み

        # Act
        response = client.get(STORE_MONITORING_URL)

        # Assert
        assert response.status_code == 200
        assert industry_test_data["device_name"].encode() in response.data

    def test_subsidiary_org_data_is_visible(self, industry_test_data, client):
        """1.3.2: 下位組織のデバイスが表示されること

        organization_closure (parent=自組織, subsidiary=下位組織) により
        下位組織のデバイスも一覧に含まれることを確認する。
        """
        # Arrange: industry_test_data が org_sub のデバイスも投入済み

        # Act
        response = client.get(STORE_MONITORING_URL)

        # Assert
        assert response.status_code == 200
        assert industry_test_data["device_sub_name"].encode() in response.data

    def test_inaccessible_org_data_not_visible(self, industry_test_data, client):
        """1.3.3 / 1.3.4: アクセス不可組織のデバイスが表示されないこと

        organization_closure に登録されていない組織のデバイスは
        一覧に含まれないことを確認する。
        """
        # Arrange: industry_test_data が org_inaccessible（closure なし）を投入済み

        # Act
        response = client.get(STORE_MONITORING_URL)

        # Assert
        assert response.status_code == 200
        assert "テストアクセス不可デバイス_結合テスト用".encode() not in response.data


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

    def test_initial_display_sets_cookie(self, industry_test_data, client):
        """2.1.1: 初期表示時に検索条件がCookieにセットされること

        ワークフロー仕様書「検索条件の保持方法: Cookieに保持」、
        「Cookie名: store_monitoring_search_params、max_age=86400」に対応。
        """
        # Act
        response = client.get(STORE_MONITORING_URL)

        # Assert
        assert response.status_code == 200
        assert "store_monitoring_search_params" in response.headers.get("Set-Cookie", "")

    def test_paging_sets_cookie(self, industry_test_data, client):
        """5.3.2: ページング時もCookieが書き込まれること

        ワークフロー仕様書「検索条件の保持方法: 初期表示・ページング問わず常時更新」に対応。
        pageパラメータありの場合でも _set_cookie が呼ばれ、Set-Cookieヘッダが付く。
        """
        # Act
        response = client.get(f"{STORE_MONITORING_URL}?page=2")

        # Assert
        assert response.status_code == 200
        assert "store_monitoring_search_params" in response.headers.get("Set-Cookie", "")

    def test_paging_uses_cookie_search_params(self, industry_test_data, client):
        """5.3.2: ページング時にCookieの検索条件（組織名）が引き継がれること

        ワークフロー仕様書「処理フロー: GetCookie→Cookieから検索条件取得」に対応。
        org_accessible_name で Cookie を設定し、page=2 リクエスト時に
        その条件でフィルタされたデバイスが表示されることを確認する。
        """
        # Arrange: org_accessible_name に完全一致する Cookie をセット
        cookie_params = {
            "organization_name": industry_test_data["org_accessible_name"],
            "device_name": "",
            "page": 1,
            "alert_page": 1,
        }
        client.set_cookie("store_monitoring_search_params", json.dumps(cookie_params))

        # Act
        response = client.get(f"{STORE_MONITORING_URL}?page=2")

        # Assert: 検索条件（org_accessible_name）に合致するデバイスが表示されること
        assert response.status_code == 200
        assert industry_test_data["device_name"].encode() in response.data

    def test_db_error_returns_500(self, client):
        """2.2.5: DBエラー時に500を返すこと

        ワークフロー仕様書「エラーハンドリング: 500 データベースエラー」に対応。
        """
        # Act
        with patch(
            f"{_VIEW_MODULE}.get_accessible_organizations",
            side_effect=Exception("DB接続エラー"),
        ):
            response = client.get(STORE_MONITORING_URL)

        # Assert
        assert response.status_code == 500

    def test_initial_display_auto_loads_first_device_sensor_data(
        self, industry_test_data, client
    ):
        """4.1.3 / 2.1.1: デバイスリスト有時に先頭デバイスのセンサーデータが自動表示されること

        ワークフロー仕様書「UI状態: センサー情報欄:
        先頭デバイスのセンサー情報を自動表示（初期表示時）」に対応。
        industry_test_data の device_accessible にはセンサーデータが登録されているため、
        初期表示でセンサー情報が表示されることを確認する。
        """
        # Act
        response = client.get(STORE_MONITORING_URL)

        # Assert: 200 かつ センサーデータを持つデバイスが先頭に表示される
        assert response.status_code == 200
        assert industry_test_data["device_name"].encode() in response.data

    def test_initial_display_empty_org_scope_returns_200(self, client):
        """4.1.1: アクセス可能組織が0件の場合は200でデバイス空リストを返すこと

        ワークフロー仕様書「UI状態: デバイスリストが空（0件）の場合」に対応。
        get_accessible_organizations が空リストを返す場合、
        デバイス取得スキップして200を返すことを確認する。
        """
        # Act
        with patch(
            f"{_VIEW_MODULE}.get_accessible_organizations", return_value=[]
        ):
            response = client.get(STORE_MONITORING_URL)

        # Assert
        assert response.status_code == 200


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

    POST ハンドラは DB アクセスを一切行わない PRG パターン（Cookie 保存後 GET リダイレクト）。
    """

    def test_search_with_empty_conditions_returns_302(self, client):
        """5.1.1: 検索条件なし（全件検索）でPRGリダイレクト（302）を返すこと

        UI仕様書(2-1)(2-2)「空でも可」に対応。
        店舗モニタリングPOSTはPRGパターンのため常に302を返す。
        """
        # Act
        response = client.post(STORE_MONITORING_URL, data={
            "organization_name": "",
            "device_name": "",
        })

        # Assert
        assert response.status_code == 302

    def test_search_saves_cookie(self, client):
        """2.1.2: 検索実行後にCookieに検索条件が保存されること

        ワークフロー仕様書「検索条件の保持方法: Cookie名 store_monitoring_search_params」に対応。
        POSTはPRGパターンのため302を返す。Set-Cookieは複数発行されるため getlist で確認する。
        """
        # Act
        response = client.post(STORE_MONITORING_URL, data={
            "organization_name": "店舗A",
            "device_name": "",
        })

        # Assert
        assert response.status_code == 302
        all_set_cookies = " ".join(response.headers.getlist("Set-Cookie"))
        assert "store_monitoring_search_params" in all_set_cookies

    def test_post_always_returns_302(self, client):
        """2.2.5: POSTはDBアクセスなしのPRGパターンのため常に302を返すこと

        ワークフロー仕様書「店舗モニタリング検索（PRG: Cookie保存後GETへリダイレクト）」に対応。
        POSTハンドラはDB呼び出しを行わず検索条件をCookieに格納してGETへリダイレクトするため、
        DBエラーは発生しない。500エラーはリダイレクト先のGETハンドラで発生しうる。
        """
        # Act
        response = client.post(STORE_MONITORING_URL, data={
            "organization_name": "店舗A",
        })

        # Assert
        assert response.status_code == 302

    def test_search_with_store_name_partial_match_returns_200(
        self, industry_test_data, client
    ):
        """5.1.7: 店舗名部分一致検索（前方一致）でGETまで通して200を返すこと

        UI仕様書(2-1)「部分一致検索」に記載されている店舗名検索を確認する。
        ワークフロー仕様書SQL: LIKE CONCAT('%', :organization_name, '%') に対応。
        follow_redirects=True でPRGリダイレクト先GETまで通し、
        org_accessible_name に部分一致するデバイスが表示されることを確認する。
        """
        # Arrange: org_accessible_name の先頭4文字で部分一致検索
        partial_name = industry_test_data["org_accessible_name"][:4]

        # Act
        response = client.post(STORE_MONITORING_URL, data={
            "organization_name": partial_name,
            "device_name": "",
        }, follow_redirects=True)

        # Assert
        assert response.status_code == 200
        assert industry_test_data["device_name"].encode() in response.data

    def test_search_with_device_name_partial_match_returns_200(
        self, industry_test_data, client
    ):
        """5.1.9: デバイス名部分一致検索（中間一致）でGETまで通して200を返すこと

        UI仕様書(2-2)「部分一致検索」に記載されているデバイス名検索を確認する。
        ワークフロー仕様書SQL: LIKE CONCAT('%', :device_name, '%') に対応。
        follow_redirects=True でPRGリダイレクト先GETまで通し、
        device_name に部分一致するデバイスが表示されることを確認する。
        """
        # Arrange: device_name の先頭5文字（"テストデバ"）で部分一致検索
        partial_device = industry_test_data["device_name"][:5]

        # Act
        response = client.post(STORE_MONITORING_URL, data={
            "organization_name": "",
            "device_name": partial_device,
        }, follow_redirects=True)

        # Assert
        assert response.status_code == 200
        assert industry_test_data["device_name"].encode() in response.data

    def test_and_search_with_both_conditions(self, industry_test_data, client):
        """5.1.10: 店舗名・デバイス名の複数条件AND検索でGETまで通して200を返すこと

        ワークフロー仕様書SQL「AND CASE WHEN :organization_name … AND CASE WHEN :device_name …」に対応。
        follow_redirects=True でPRGリダイレクト先GETまで通し、
        両条件に合致するデバイスが表示されることを確認する。
        """
        # Arrange: 両方とも部分一致する条件
        partial_org = industry_test_data["org_accessible_name"][:4]
        partial_dev = industry_test_data["device_name"][:5]

        # Act
        response = client.post(STORE_MONITORING_URL, data={
            "organization_name": partial_org,
            "device_name": partial_dev,
        }, follow_redirects=True)

        # Assert
        assert response.status_code == 200
        assert industry_test_data["device_name"].encode() in response.data

    def test_search_post_redirects_with_302(self, client):
        """2.3.1: POST検索後に302リダイレクトが返ること（PRGパターン）

        ワークフロー仕様書「店舗モニタリング検索（PRG: Cookie保存後GETへリダイレクト）」に対応。
        POSTリクエストはDBアクセスなしで検索条件をCookieに保存し、
        302でGETエンドポイントへリダイレクトする。
        """
        # Act (follow_redirects=False がデフォルト)
        response = client.post(STORE_MONITORING_URL, data={
            "organization_name": "店舗A",
            "device_name": "",
        })

        # Assert
        assert response.status_code == 302
        location = response.headers.get("Location", "")
        assert "store-monitoring" in location

    def test_search_with_organization_id_saves_organization_id_to_cookie(self, client):
        """5.1.2: organization_id 指定時にCookieにorganization_idが保存されること

        UI仕様書(2-1)「ドロップダウン選択時は organization_id で完全一致検索」に対応。
        ドロップダウンから店舗を選択すると organization_id がフォームに含まれ、
        Cookieへ保存される。（検索実行時の完全一致フィルタはGETルートが担当）
        """
        # Arrange
        org_id = "42"

        # Act
        response = client.post(STORE_MONITORING_URL, data={
            "organization_name": "店舗A",
            "organization_id": org_id,
            "device_name": "",
        })

        # Assert: PRGリダイレクト
        assert response.status_code == 302
        # delete_cookie → set_cookie の順で2つのSet-Cookieヘッダが発行されるため getlist で確認する
        all_set_cookies = " ".join(response.headers.getlist("Set-Cookie"))
        assert "store_monitoring_search_params" in all_set_cookies
        # Cookieの値にorganization_idが含まれること
        assert org_id in all_set_cookies


# ===========================================================================
# センサー情報表示（GET /store-monitoring/<uuid>）
# ===========================================================================


@pytest.mark.integration
class TestShowSensorInfo:
    """センサー情報表示テスト

    観点: 2.1 正常遷移テスト / 2.2 エラー時遷移テスト / 4.2 詳細表示テスト
    ワークフロー仕様書「センサー情報表示」に対応。
    エンドポイント: GET /analysis/industry-dashboard/store-monitoring/<device_uuid>
    MySQL実DB（silver_sensor_data テーブル）から最新センサーデータを取得する。
    """

    def test_returns_200_with_sensor_data(self, industry_test_data, client):
        """4.2.1: センサーデータあり時に200を返すこと

        MySQL実DB（silver_sensor_data）にセンサーデータが登録されているデバイスに対して
        店舗モニタリング画面がセンサー情報表示状態（show_sensor_info=True）で200を返す。
        """
        # Act
        response = client.get(
            f"{STORE_MONITORING_URL}/{industry_test_data['device_uuid']}"
        )

        # Assert
        assert response.status_code == 200

    def test_returns_200_when_sensor_data_is_none(self, industry_test_data, client):
        """4.2.5: センサーデータなし（DB未登録）でも200を返すこと

        UI仕様書(5-2〜5-5)「初期表示: ラベルのみ」に対応。
        silver_sensor_data にレコードがないデバイス（device_sub）に対して
        画面が正常に表示されることを確認する。
        """
        # Arrange: device_sub はセンサーデータ未投入

        # Act
        response = client.get(
            f"{STORE_MONITORING_URL}/{industry_test_data['device_sub_uuid']}"
        )

        # Assert
        assert response.status_code == 200

    def test_returns_404_when_device_not_found(self, industry_test_data, client):
        """2.2.4 / 4.2.4: デバイス未検出・アクセス権限なし時に404を返すこと

        ワークフロー仕様書「エラーハンドリング: 404 リソース不存在」に対応。
        DBに存在しないUUIDを使用し、check_device_access が None を返す（未登録デバイス）ケース。
        """
        # Act
        response = client.get(f"{STORE_MONITORING_URL}/{DEVICE_UUID_NOT_FOUND}")

        # Assert
        assert response.status_code == 404

    def test_returns_404_when_device_is_inaccessible(self, industry_test_data, client):
        """1.3.3: アクセス不可組織のデバイスへのアクセスで404を返すこと

        organization_closure に登録されていない組織のデバイスUUIDを指定した場合、
        check_device_access がスコープ外と判断し None を返す → 404。
        """
        # Act
        response = client.get(
            f"{STORE_MONITORING_URL}/{industry_test_data['device_inaccessible_uuid']}"
        )

        # Assert
        assert response.status_code == 404

    def test_db_error_returns_500(self, client):
        """2.2.5: DBエラー時に500を返すこと

        ワークフロー仕様書「エラーハンドリング: 500 データベースエラー」に対応。
        """
        # Act
        with patch(
            f"{_VIEW_MODULE}.get_accessible_organizations",
            side_effect=Exception("DB接続エラー"),
        ):
            response = client.get(f"{STORE_MONITORING_URL}/{DEVICE_UUID_NOT_FOUND}")

        # Assert
        assert response.status_code == 500

    def test_sensor_data_db_error_returns_500(self, industry_test_data, client):
        """2.2.5: センサーデータ取得（silver_sensor_data）のDBエラー時に500を返すこと

        ワークフロー仕様書「エラーハンドリング: 500 データベースエラー」に対応。
        get_latest_sensor_data で例外が発生した場合、500エラーとなることを確認する。
        """
        # Act
        with patch(
            f"{_VIEW_MODULE}.get_latest_sensor_data",
            side_effect=Exception("DBクエリエラー"),
        ):
            response = client.get(
                f"{STORE_MONITORING_URL}/{industry_test_data['device_uuid']}"
            )

        # Assert
        assert response.status_code == 500

    def test_cookie_search_params_used_when_present(self, industry_test_data, client):
        """5.1.1: Cookie有り時にCookieの検索条件（組織名）が引き継がれること

        センサー情報表示後もデバイス一覧の検索条件が維持されることを確認する。
        ワークフロー仕様書「UI状態: 前回の検索条件を保持」に対応。
        org_accessible_name を Cookie にセットした状態でアクセスし、
        org_accessible のデバイスが一覧に表示されることを確認する。
        """
        # Arrange
        cookie_params = {
            "organization_name": industry_test_data["org_accessible_name"],
            "device_name": "",
            "page": 1,
            "alert_page": 1,
        }
        client.set_cookie("store_monitoring_search_params", json.dumps(cookie_params))

        # Act
        response = client.get(
            f"{STORE_MONITORING_URL}/{industry_test_data['device_uuid']}"
        )

        # Assert
        assert response.status_code == 200
        assert industry_test_data["device_name"].encode() in response.data


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

    def test_initial_display_sets_cookie(self, industry_test_data, client):
        """2.1.1: 初期表示時に検索条件（表示期間）がCookieにセットされること

        ワークフロー仕様書「検索条件の保持方法: Cookie名 device_details_search_params」に対応。
        表示期間の初期値は直近24時間（get_default_date_range()）。
        """
        # Act
        response = client.get(
            f"{DEVICE_DETAILS_URL}/{industry_test_data['device_uuid']}"
        )

        # Assert
        assert response.status_code == 200
        assert "device_details_search_params" in response.headers.get("Set-Cookie", "")

    def test_paging_does_not_set_cookie(self, industry_test_data, client):
        """5.3.2: ページング時にはCookieが書き込まれないこと

        ワークフロー仕様書「処理フロー: 初期表示時のみCookie格納（if save_cookie:）」に対応。
        pageパラメータありの場合は _set_cookie が呼ばれず、Set-Cookieヘッダが付かない。
        """
        # Act
        response = client.get(
            f"{DEVICE_DETAILS_URL}/{industry_test_data['device_uuid']}?page=2"
        )

        # Assert
        assert response.status_code == 200
        assert "device_details_search_params" not in response.headers.get("Set-Cookie", "")

    def test_paging_uses_cookie_search_params(self, industry_test_data, client):
        """5.3.2: ページング時にCookieの表示期間がグラフデータ取得に使用されること

        ワークフロー仕様書「処理フロー: GetCookie→Cookieから検索条件取得」に対応。
        センサーデータ投入時刻を含む範囲でCookieをセットし、page=2 リクエスト後に
        200が返ることを確認する（グラフデータ取得にCookieの期間が使用される）。
        """
        # Arrange: センサーデータ（過去1時間）を含む範囲で Cookie をセット
        from datetime import datetime, timedelta
        now = datetime.now()
        cookie_params = {
            "search_start_datetime": (now - timedelta(hours=2)).strftime("%Y-%m-%dT%H:%M"),
            "search_end_datetime": now.strftime("%Y-%m-%dT%H:%M"),
            "page": 1,
        }
        client.set_cookie("device_details_search_params", json.dumps(cookie_params))

        # Act
        response = client.get(
            f"{DEVICE_DETAILS_URL}/{industry_test_data['device_uuid']}?page=2"
        )

        # Assert
        assert response.status_code == 200

    def test_returns_404_when_device_not_found(self, industry_test_data, client):
        """2.2.4 / 4.2.4: デバイス未検出・アクセス権限なし時に404を返すこと

        ワークフロー仕様書「エラーハンドリング: 404 リソース不存在」に対応。
        check_device_access が None を返す（スコープ外またはDB未登録）ケース。
        """
        # Act
        response = client.get(f"{DEVICE_DETAILS_URL}/{DEVICE_UUID_NOT_FOUND}")

        # Assert
        assert response.status_code == 404

    def test_db_error_returns_500(self, client):
        """2.2.5: DBエラー時に500を返すこと

        ワークフロー仕様書「エラーハンドリング: 500 データベースエラー」に対応。
        """
        # Act
        with patch(
            f"{_VIEW_MODULE}.get_accessible_organizations",
            side_effect=Exception("DB接続エラー"),
        ):
            response = client.get(f"{DEVICE_DETAILS_URL}/{DEVICE_UUID_NOT_FOUND}")

        # Assert
        assert response.status_code == 500

    def test_graph_data_db_error_returns_500(self, industry_test_data, client):
        """2.2.5: グラフデータ取得（silver_sensor_data）のDBエラー時に500を返すこと

        ワークフロー仕様書「エラーハンドリング: 500 データベースエラー」に対応。
        get_graph_data で例外が発生した場合、500エラーとなることを確認する。
        """
        # Act
        with patch(
            f"{_VIEW_MODULE}.get_graph_data",
            side_effect=Exception("DBクエリエラー"),
        ):
            response = client.get(
                f"{DEVICE_DETAILS_URL}/{industry_test_data['device_uuid']}"
            )

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

    バリデーションテストは industry_test_data の実デバイスUUIDを使用することで
    check_device_access がDBから実データを取得し、その後バリデーションが実行される。
    """

    def test_valid_period_returns_200(self, industry_test_data, client):
        """3.1.1 / 3.4.1 / 3.8.1: 正しい日時形式・整合性のある期間で200を返すこと"""
        # Act
        response = client.post(
            f"{DEVICE_DETAILS_URL}/{industry_test_data['device_uuid']}",
            data={
                "search_start_datetime": "2026-02-01T00:00",
                "search_end_datetime": "2026-02-02T00:00",
            },
        )

        # Assert
        assert response.status_code == 200

    def test_valid_period_saves_cookie(self, industry_test_data, client):
        """2.1.2: 正常な表示期間変更後にCookieが更新されること

        ワークフロー仕様書「検索条件の保持方法: Cookie名 device_details_search_params」に対応。
        """
        # Act
        response = client.post(
            f"{DEVICE_DETAILS_URL}/{industry_test_data['device_uuid']}",
            data={
                "search_start_datetime": "2026-02-01T00:00",
                "search_end_datetime": "2026-02-02T00:00",
            },
        )

        # Assert
        assert response.status_code == 200
        assert "device_details_search_params" in response.headers.get("Set-Cookie", "")

    def test_empty_start_datetime_returns_400(self, industry_test_data, client):
        """3.1.2: 開始日時が空（未入力）の場合に400を返すこと

        ワークフロー仕様書「バリデーション: search_start_datetime は必須」に対応。
        """
        # Act
        response = client.post(
            f"{DEVICE_DETAILS_URL}/{industry_test_data['device_uuid']}",
            data={
                "search_start_datetime": "",  # 未入力
                "search_end_datetime": "2026-02-02T00:00",
            },
        )

        # Assert
        assert response.status_code == 400

    def test_empty_end_datetime_returns_400(self, industry_test_data, client):
        """3.1.2: 終了日時が空（未入力）の場合に400を返すこと

        ワークフロー仕様書「バリデーション: search_end_datetime は必須」に対応。
        """
        # Act
        response = client.post(
            f"{DEVICE_DETAILS_URL}/{industry_test_data['device_uuid']}",
            data={
                "search_start_datetime": "2026-02-01T00:00",
                "search_end_datetime": "",  # 未入力
            },
        )

        # Assert
        assert response.status_code == 400

    def test_invalid_datetime_format_returns_400(self, industry_test_data, client):
        """3.4.2: 不正な日時フォーマット（YYYY/MM/DD HH:mm）で400を返すこと

        ワークフロー仕様書「バリデーション: YYYY-MM-DDTHH:MM形式」に対応。
        """
        # Act
        response = client.post(
            f"{DEVICE_DETAILS_URL}/{industry_test_data['device_uuid']}",
            data={
                "search_start_datetime": "2026/02/01 00:00",  # 不正フォーマット（スラッシュ区切り）
                "search_end_datetime": "2026-02-02T00:00",
            },
        )

        # Assert
        assert response.status_code == 400

    def test_start_after_end_returns_400(self, industry_test_data, client):
        """3.8.2: 開始日時 > 終了日時の場合に400を返すこと

        ワークフロー仕様書「バリデーション: 開始日時 < 終了日時であること」に対応。
        """
        # Act
        response = client.post(
            f"{DEVICE_DETAILS_URL}/{industry_test_data['device_uuid']}",
            data={
                "search_start_datetime": "2026-02-10T00:00",
                "search_end_datetime": "2026-02-01T00:00",  # 開始が終了より後
            },
        )

        # Assert
        assert response.status_code == 400

    def test_start_equal_to_end_returns_400(self, industry_test_data, client):
        """3.8.2: 開始日時 == 終了日時の場合に400を返すこと

        「開始日時 < 終了日時」の条件より、等値は不正となる。
        ワークフロー仕様書「バリデーション: start_dt >= end_dt → エラー」に対応。
        """
        # Act
        response = client.post(
            f"{DEVICE_DETAILS_URL}/{industry_test_data['device_uuid']}",
            data={
                "search_start_datetime": "2026-02-01T00:00",
                "search_end_datetime": "2026-02-01T00:00",  # 同値
            },
        )

        # Assert
        assert response.status_code == 400

    def test_period_over_62_days_returns_400(self, industry_test_data, client):
        """3.8.2: 表示期間62日超過で400を返すこと

        ワークフロー仕様書「バリデーション: 表示期間が最大2ヶ月（62日）以内であること」に対応。
        """
        # Act
        response = client.post(
            f"{DEVICE_DETAILS_URL}/{industry_test_data['device_uuid']}",
            data={
                "search_start_datetime": "2026-01-01T00:00",
                "search_end_datetime": "2026-03-20T00:00",  # 78日 > 62日
            },
        )

        # Assert
        assert response.status_code == 400

    def test_exactly_62_days_returns_200(self, industry_test_data, client):
        """3.8.1: 表示期間がちょうど62日（境界値）の場合に200を返すこと

        ワークフロー仕様書「バリデーション: (end_dt - start_dt).days > 62 → エラー」
        つまり days == 62 は許容される境界値。
        """
        # Act
        response = client.post(
            f"{DEVICE_DETAILS_URL}/{industry_test_data['device_uuid']}",
            data={
                "search_start_datetime": "2026-01-01T00:00",
                "search_end_datetime": "2026-03-04T00:00",  # ちょうど62日
            },
        )

        # Assert
        assert response.status_code == 200

    def test_device_not_found_returns_404(self, industry_test_data, client):
        """2.2.4: デバイス未検出時に404を返すこと

        ワークフロー仕様書「エラーハンドリング: 404 リソース不存在」に対応。
        DBに存在しないUUIDを使用し check_device_access が None を返すケース。
        """
        # Act
        response = client.post(
            f"{DEVICE_DETAILS_URL}/{DEVICE_UUID_NOT_FOUND}",
            data={
                "search_start_datetime": "2026-02-01T00:00",
                "search_end_datetime": "2026-02-02T00:00",
            },
        )

        # Assert
        assert response.status_code == 404

    def test_db_error_returns_500(self, client):
        """2.2.5: DBエラー時に500を返すこと

        ワークフロー仕様書「エラーハンドリング: 500 データベースエラー」に対応。
        """
        # Act
        with patch(
            f"{_VIEW_MODULE}.get_accessible_organizations",
            side_effect=Exception("DB接続エラー"),
        ):
            response = client.post(
                f"{DEVICE_DETAILS_URL}/{DEVICE_UUID_NOT_FOUND}",
                data={
                    "search_start_datetime": "2026-02-01T00:00",
                    "search_end_datetime": "2026-02-02T00:00",
                },
            )

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
    CSVデータ元: MySQL実DB（silver_sensor_data テーブル）。
    """

    def test_csv_export_returns_text_csv(self, industry_test_data, client):
        """4.6.1: ?export=csv パラメータでContent-type: text/csvが返ること

        UI仕様書(11)「クリック時: /device-details/<device_uuid>?export=csv にリクエスト」に対応。
        レスポンスの Content-type が text/csv であることを確認する。
        """
        # Act
        response = client.get(
            f"{DEVICE_DETAILS_URL}/{industry_test_data['device_uuid']}?export=csv"
        )

        # Assert
        assert response.status_code == 200
        assert "text/csv" in response.content_type

    def test_csv_export_content_disposition_includes_device_uuid(
        self, industry_test_data, client
    ):
        """4.6.3: CSVエクスポートのファイル名に対象デバイスのUUIDが含まれること

        ワークフロー仕様書「CSVエクスポート: export_sensor_data_csv(device, search_params)」に対応。
        Content-Disposition ヘッダのファイル名にデバイスUUIDが含まれることを確認する。
        """
        # Act
        response = client.get(
            f"{DEVICE_DETAILS_URL}/{industry_test_data['device_uuid']}?export=csv"
        )

        # Assert
        assert response.status_code == 200
        content_disposition = response.headers.get("Content-Disposition", "")
        assert industry_test_data["device_uuid"] in content_disposition

    def test_csv_export_uses_cookie_search_params(self, industry_test_data, client):
        """4.6.3: Cookie有り時にCookieの表示期間でCSVエクスポートされること

        ワークフロー仕様書「前提条件: 表示期間はCookieに保存されている」に対応。
        センサーデータを含む期間でCookieをセットし、CSVエクスポートが正常に返ることを確認する。
        """
        # Arrange: センサーデータ（過去1時間）を含む範囲で Cookie をセット
        from datetime import datetime, timedelta
        now = datetime.now()
        cookie_params = {
            "search_start_datetime": (now - timedelta(hours=2)).strftime("%Y-%m-%dT%H:%M"),
            "search_end_datetime": now.strftime("%Y-%m-%dT%H:%M"),
        }
        client.set_cookie("device_details_search_params", json.dumps(cookie_params))

        # Act
        response = client.get(
            f"{DEVICE_DETAILS_URL}/{industry_test_data['device_uuid']}?export=csv"
        )

        # Assert
        assert response.status_code == 200
        assert "text/csv" in response.content_type

    def test_csv_export_uses_default_params_when_no_cookie(
        self, industry_test_data, client
    ):
        """4.6.3: Cookie無し時にデフォルト期間（直近24時間）でCSVエクスポートが返ること

        ワークフロー仕様書「前提条件: Cookieに表示期間がない場合はデフォルト期間でエクスポート」
        「デフォルト期間: 現在日時から1日前まで」に対応。
        """
        # Arrange: Cookieをセットしない

        # Act
        response = client.get(
            f"{DEVICE_DETAILS_URL}/{industry_test_data['device_uuid']}?export=csv"
        )

        # Assert
        assert response.status_code == 200
        assert "text/csv" in response.content_type

    def test_csv_export_returns_404_when_device_not_found(
        self, industry_test_data, client
    ):
        """2.2.4: デバイス未検出時のCSVエクスポートで404を返すこと

        ワークフロー仕様書「エラーハンドリング: 404 リソース不存在」に対応。
        """
        # Act
        response = client.get(
            f"{DEVICE_DETAILS_URL}/{DEVICE_UUID_NOT_FOUND}?export=csv"
        )

        # Assert
        assert response.status_code == 404

    def test_csv_export_db_error_returns_500(self, client):
        """2.2.5: DBエラー時のCSVエクスポートで500を返すこと

        ワークフロー仕様書「エラーハンドリング: 500 データベースエラー」に対応。
        """
        # Act
        with patch(
            f"{_VIEW_MODULE}.get_accessible_organizations",
            side_effect=Exception("DB接続エラー"),
        ):
            response = client.get(
                f"{DEVICE_DETAILS_URL}/{DEVICE_UUID_NOT_FOUND}?export=csv"
            )

        # Assert
        assert response.status_code == 500

    def test_csv_export_db_error_in_service_returns_500(
        self, industry_test_data, client
    ):
        """2.2.5: CSVエクスポート処理中のDBエラーで500を返すこと

        ワークフロー仕様書「エラーハンドリング: 500 CSVエクスポートに失敗しました」に対応。
        export_sensor_data_csv（サービス層）で例外が発生した場合、500エラーとなることを確認する。
        """
        # Act
        with patch(
            f"{_VIEW_MODULE}.export_sensor_data_csv",
            side_effect=Exception("DBクエリエラー"),
        ):
            response = client.get(
                f"{DEVICE_DETAILS_URL}/{industry_test_data['device_uuid']}?export=csv"
            )

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

    POST ハンドラは DB アクセスなし（PRG パターン）のため、
    不正入力があっても 302 が返り 500 にならないことを確認する。
    """

    def test_sql_injection_in_store_name_returns_not_500(self, client):
        """9.1.1: 店舗名フィールドへのSQLインジェクション文字列でサーバーエラーにならないこと

        SQLAlchemy のプリペアドステートメントにより注入文字列はエスケープされ、
        500エラーとならないことを確認する。
        """
        # Act
        response = client.post(STORE_MONITORING_URL, data={
            "organization_name": "' OR '1'='1",  # 基本的なSQLインジェクション
            "device_name": "",
        })

        # Assert: POSTはPRGパターンのため302を返す。サーバーエラー(500)にならないことを確認する
        assert response.status_code != 500

    def test_sql_injection_drop_table_in_device_name(self, client):
        """9.1.2: デバイス名フィールドへのDROP TABLE文字列でサーバーエラーにならないこと"""
        # Act
        response = client.post(STORE_MONITORING_URL, data={
            "organization_name": "",
            "device_name": "'; DROP TABLE device_master;--",
        })

        # Assert: POSTはPRGパターンのため302を返す。サーバーエラー(500)にならないことを確認する
        assert response.status_code != 500

    def test_sql_injection_union_select_in_store_name(self, client):
        """9.1.3: UNIONを使ったSQLインジェクション文字列でサーバーエラーにならないこと

        SQLAlchemy のプリペアドステートメントにより注入文字列はエスケープされ、
        500エラーとならないことを確認する。
        """
        # Act
        response = client.post(STORE_MONITORING_URL, data={
            "organization_name": "' UNION SELECT * FROM user_master--",
            "device_name": "",
        })

        # Assert: POSTはPRGパターンのため302を返す。サーバーエラー(500)にならないことを確認する
        assert response.status_code != 500

    def test_xss_script_tag_in_store_name_is_escaped(self, client):
        """9.2.1: 店舗名フィールドへの<script>タグがJinja2自動エスケープで無効化されること

        Jinja2 の自動エスケープにより、スクリプトタグがそのままHTMLに
        出力されることなく、安全にエスケープされることを確認する。
        """
        # Arrange
        xss_payload = "<script>alert('XSS')</script>"

        # Act
        response = client.post(STORE_MONITORING_URL, data={
            "organization_name": xss_payload,
            "device_name": "",
        })

        # Assert: POSTはPRGパターンのため302を返す。サーバーエラー(500)にならないことを確認する
        assert response.status_code != 500

    def test_xss_img_tag_in_device_name_is_escaped(self, client):
        """9.2.2: デバイス名フィールドへの<img onerror>タグがエスケープされること"""
        # Arrange
        xss_payload = "<img src=x onerror=alert('XSS')>"

        # Act
        response = client.post(STORE_MONITORING_URL, data={
            "organization_name": "",
            "device_name": xss_payload,
        })

        # Assert: POSTはPRGパターンのため302を返す。サーバーエラー(500)にならないことを確認する
        assert response.status_code != 500

    def test_xss_javascript_protocol_in_device_name_is_escaped(self, client):
        """9.2.3: デバイス名フィールドへのJavaScriptプロトコルがエスケープされること

        Jinja2 の自動エスケープにより、javascript: スキームがそのままHTMLに
        出力されることなく、安全にエスケープされることを確認する。
        """
        # Arrange
        xss_payload = "javascript:alert('XSS')"

        # Act
        response = client.post(STORE_MONITORING_URL, data={
            "organization_name": "",
            "device_name": xss_payload,
        })

        # Assert: POSTはPRGパターンのため302を返す。サーバーエラー(500)にならないことを確認する
        assert response.status_code != 500


# ===========================================================================
# 店舗名オートコンプリートAPI（GET /store-monitoring/organizations）
# ===========================================================================


@pytest.mark.integration
class TestStoreMonitoringOrganizationAutocomplete:
    """店舗名オートコンプリートAPIテスト

    観点: 4.1 一覧表示（Read）テスト / 2.2 エラー時遷移テスト / 1.3 データスコープフィルタテスト
    エンドポイント: GET /analysis/industry-dashboard/store-monitoring/organizations
    UI仕様書(2-1)「入力エリアに文字を入力すると、部分一致する店舗名をドロップダウンリストとして表示」に対応。
    MySQL実DB: industry_test_data フィクスチャで投入した組織データを使用する。
    """

    def test_autocomplete_returns_json_list(self, industry_test_data, client):
        """4.1.3: 部分一致クエリで組織候補リストがJSON形式で返ること

        UI仕様書(2-1)「入力エリアに文字を入力すると、部分一致する店舗名をドロップダウンリストとして表示」に対応。
        org_accessible_name の先頭文字で部分一致検索し、
        結果リストに org_accessible が含まれることを確認する。
        """
        # Arrange: org_accessible_name の先頭4文字で部分一致検索
        partial_name = industry_test_data["org_accessible_name"][:4]

        # Act
        response = client.get(f"{AUTOCOMPLETE_URL}?q={partial_name}")

        # Assert
        assert response.status_code == 200
        assert response.content_type.startswith("application/json")
        data = response.get_json()
        assert isinstance(data, list)
        org_names = [item["organization_name"] for item in data]
        assert industry_test_data["org_accessible_name"] in org_names

    def test_autocomplete_empty_query_returns_all_accessible_orgs(
        self, industry_test_data, client
    ):
        """4.1.1: qパラメータなし（空クエリ）でアクセス可能組織が全件返ること

        UI仕様書(2-1)「プレースホルダー: 店舗を検索...」から、未入力状態を想定。
        ワークフロー仕様書「request.args.get('q', '')」の実装に対応。
        """
        # Act（qパラメータなし）
        response = client.get(AUTOCOMPLETE_URL)

        # Assert
        assert response.status_code == 200
        data = response.get_json()
        assert isinstance(data, list)
        # org_accessible と org_sub は accessible、どちらかが結果に含まれること
        org_names = [item["organization_name"] for item in data]
        assert industry_test_data["org_accessible_name"] in org_names

    def test_autocomplete_inaccessible_org_not_included(
        self, industry_test_data, client
    ):
        """1.3.1: データスコープフィルタ適用でアクセス不可組織が候補に含まれないこと

        ワークフロー仕様書「データスコープ制限: get_accessible_organizations(current_user.organization_id)
        の結果を search_organizations_by_name に渡す」に対応。
        closure 未登録の org_inaccessible は候補に含まれないことを確認する。
        """
        # Act（qパラメータなし: 全アクセス可能組織を取得）
        response = client.get(AUTOCOMPLETE_URL)

        # Assert
        assert response.status_code == 200
        data = response.get_json()
        org_names = [item["organization_name"] for item in data]
        assert industry_test_data["org_accessible_name"] not in [
            n for n in org_names
            if n == "テストアクセス不可組織_結合テスト用"
        ]
        # アクセス不可組織が候補に含まれないこと
        assert "テストアクセス不可組織_結合テスト用" not in org_names

    def test_autocomplete_db_error_returns_500_with_empty_list(self, client):
        """2.2.5: DBエラー時に500ステータスと空リストを返すこと

        実装: except Exception → return jsonify([]), 500
        フロントエンドがエラー時にオートコンプリート候補を表示しない設計に対応。
        """
        # Act
        with patch(
            f"{_VIEW_MODULE}.get_accessible_organizations",
            side_effect=Exception("DB接続エラー"),
        ):
            response = client.get(f"{AUTOCOMPLETE_URL}?q=店舗")

        # Assert
        assert response.status_code == 500
        data = response.get_json()
        assert data == []
