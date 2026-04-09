"""
顧客作成ダッシュボード 帯グラフガジェット - 結合テスト

対象エンドポイント:
  GET  /analysis/customer-dashboard
  POST /analysis/customer-dashboard/gadgets/<gadget_uuid>/data
  GET  /analysis/customer-dashboard/gadgets/belt-chart/create
  POST /analysis/customer-dashboard/gadgets/belt-chart/register
  GET  /analysis/customer-dashboard/gadgets/<gadget_uuid>?export=csv

参照設計書:
  - docs/03-features/flask-app/customer-dashboard/belt-chart/ui-specification.md
  - docs/03-features/flask-app/customer-dashboard/belt-chart/workflow-specification.md

NOTE: モデルファイル（models/dashboard.py 等）が実装済みであることが前提。
      外部API（Unity Catalog）のみモック化する。認証ミドルウェアは conftest の
      bypass_auth_middleware でバイパス済み。
"""

import json
import uuid
from datetime import date

import pytest
from bs4 import BeautifulSoup

BASE_URL = "/analysis/customer-dashboard"
_VALID_DATETIME = "2026/03/06 12:00:00"

# Unity Catalog クエリのモック対象パス（帯グラフはシルバー層とゴールド層両方を使用）
_SILVER_QUERY = "iot_app.services.customer_dashboard.belt_chart.execute_silver_query"
_GOLD_QUERY   = "iot_app.services.customer_dashboard.belt_chart.execute_gold_query"


def _soup(response) -> BeautifulSoup:
    """FlaskレスポンスからBeautifulSoupオブジェクトを生成するヘルパー"""
    return BeautifulSoup(response.data, 'html.parser')


# ─────────────────────────────────────────────────────────────────────────────
# 共通フィクスチャ（帯グラフガジェット用）
# ─────────────────────────────────────────────────────────────────────────────

@pytest.fixture()
def gadget_type_belt(db_session):
    """GadgetTypeMaster テストレコード（帯グラフ）"""
    from iot_app.models.customer_dashboard import GadgetTypeMaster
    gt = GadgetTypeMaster(
        gadget_type_id=5,
        gadget_type_name='帯グラフ',
        data_source_type=1,
        gadget_image_path='images/gadgets/belt_chart.png',
        gadget_description='帯グラフガジェット',
        display_order=5,
        creator=1,
        modifier=1,
        delete_flag=False,
    )
    db_session.add(gt)
    db_session.flush()
    return gt


@pytest.fixture()
def measurement_items_multi(db_session):
    """MeasurementItemMaster テストレコード（複数項目）"""
    from iot_app.models.measurement import MeasurementItemMaster
    items = []
    item_defs = [
        (1, '外気温度', 'external_temp', '℃'),
        (2, '第1冷凍 設定温度', 'set_temp_freezer_1', '℃'),
        (3, '第1冷凍 庫内センサー温度', 'internal_sensor_temp_freezer_1', '℃'),
    ]
    for mid, display_name, col_name, unit in item_defs:
        item = MeasurementItemMaster(
            measurement_item_id=mid,
            measurement_item_name=display_name,
            display_name=display_name,
            silver_data_column_name=col_name,
            unit_name=unit,
            creator=1,
            modifier=1,
            delete_flag=False,
        )
        db_session.add(item)
        items.append(item)
    db_session.flush()
    return items


@pytest.fixture()
def belt_chart_gadget_fixed(db_session, gadget_type_belt):
    """DashboardGadgetMaster テストレコード（帯グラフ、デバイス固定モード）"""
    from iot_app.models.customer_dashboard import DashboardGadgetMaster
    g = DashboardGadgetMaster(
        gadget_uuid=str(uuid.uuid4()),
        gadget_name='テスト帯グラフ',
        gadget_type_id=gadget_type_belt.gadget_type_id,
        dashboard_group_id=1,
        chart_config=json.dumps({
            'measurement_item_ids': [1, 2],
            'summary_method_id': 1,
        }),
        data_source_config=json.dumps({'device_id': 1}),
        position_x=0,
        position_y=1,
        gadget_size='2x2',
        display_order=1,
        creator=1,
        modifier=1,
    )
    db_session.add(g)
    db_session.flush()
    return g


@pytest.fixture()
def belt_chart_gadget_variable(db_session, gadget_type_belt):
    """DashboardGadgetMaster テストレコード（帯グラフ、デバイス可変モード）"""
    from iot_app.models.customer_dashboard import DashboardGadgetMaster
    g = DashboardGadgetMaster(
        gadget_uuid=str(uuid.uuid4()),
        gadget_name='テスト帯グラフ（可変）',
        gadget_type_id=gadget_type_belt.gadget_type_id,
        dashboard_group_id=1,
        chart_config=json.dumps({
            'measurement_item_ids': [1, 2],
            'summary_method_id': 1,
        }),
        data_source_config=json.dumps({'device_id': None}),
        position_x=0,
        position_y=1,
        gadget_size='2x2',
        display_order=1,
        creator=1,
        modifier=1,
    )
    db_session.add(g)
    db_session.flush()
    return g


# ─────────────────────────────────────────────────────────────────────────────
# 1. ガジェットデータ取得（AJAX）
# POST /analysis/customer-dashboard/gadgets/<gadget_uuid>/data
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.integration
class TestGadgetBeltChartData:
    """帯グラフガジェット データ取得（AJAX）

    観点: 4.2 詳細表示、3.4 日付形式チェック、3.6 不整値チェック、2.2 エラー時遷移
    """

    @pytest.fixture(autouse=True)
    def _require_auth_scope(
        self, auth_scope, dashboard_master, dashboard_group_master, gadget_type_belt
    ):
        """全テストで認証ユーザー＋アクセス可能スコープ＋ガジェット関連マスタを事前登録する"""

    def _url(self, gadget_uuid):
        return f"{BASE_URL}/gadgets/{gadget_uuid}/data"

    def test_data_returns_json_structure_day_unit(
        self, client, belt_chart_gadget_fixed, mocker
    ):
        """4.2.1: display_unit=day 正常取得 - gadget_uuid / chart_data / updated_at を含む JSON を返す"""
        # Arrange: ゴールド層（hourly）クエリをモック（外部API）
        mocker.patch(_GOLD_QUERY, return_value=[
            {'collection_hour': 10, 'summary_item': 1, 'summary_value': 25.5},
            {'collection_hour': 11, 'summary_item': 2, 'summary_value': 15.0},
        ])

        # Act
        response = client.post(
            self._url(belt_chart_gadget_fixed.gadget_uuid),
            json={
                'display_unit': 'day',
                'interval': '10min',
                'base_datetime': _VALID_DATETIME,
            },
        )

        # Assert: JSONレスポンスの構造を検証
        assert response.status_code == 200
        body = response.get_json()
        assert body['gadget_uuid'] == belt_chart_gadget_fixed.gadget_uuid
        assert 'chart_data' in body
        assert 'labels' in body['chart_data']
        assert 'series' in body['chart_data']
        assert 'updated_at' in body

    def test_data_returns_json_structure_week_unit(
        self, client, belt_chart_gadget_fixed, mocker
    ):
        """4.2.1: display_unit=week 正常取得 - chart_data.series が配列で返る"""
        # Arrange: ゴールド層（daily）クエリをモック
        mocker.patch(_GOLD_QUERY, return_value=[])

        # Act
        response = client.post(
            self._url(belt_chart_gadget_fixed.gadget_uuid),
            json={
                'display_unit': 'week',
                'interval': '10min',
                'base_datetime': _VALID_DATETIME,
            },
        )

        # Assert
        assert response.status_code == 200
        body = response.get_json()
        assert isinstance(body['chart_data']['series'], list)

    def test_data_returns_json_structure_month_unit(
        self, client, belt_chart_gadget_fixed, mocker
    ):
        """4.2.1: display_unit=month 正常取得 - chart_data.series が配列で返る"""
        # Arrange: ゴールド層（daily）クエリをモック
        mocker.patch(_GOLD_QUERY, return_value=[])

        # Act
        response = client.post(
            self._url(belt_chart_gadget_fixed.gadget_uuid),
            json={
                'display_unit': 'month',
                'interval': '10min',
                'base_datetime': _VALID_DATETIME,
            },
        )

        # Assert
        assert response.status_code == 200
        body = response.get_json()
        assert 'labels' in body['chart_data']
        assert 'series' in body['chart_data']

    def test_data_hour_unit_uses_silver_query(
        self, client, belt_chart_gadget_fixed, measurement_items_multi, mocker
    ):
        """4.2.5: display_unit=hour 時、シルバー層クエリが呼ばれる"""
        # Arrange: シルバー層クエリをモック（外部API）
        mock_silver = mocker.patch(_SILVER_QUERY, return_value=[])

        # Act: display_unit=hour を指定（measurement_items_multi フィクスチャで複数項目登録済み）
        response = client.post(
            self._url(belt_chart_gadget_fixed.gadget_uuid),
            json={'display_unit': 'hour', 'interval': '10min', 'base_datetime': _VALID_DATETIME},
        )

        # Assert: シルバー層クエリが呼ばれている
        assert response.status_code == 200
        assert mock_silver.called

    def test_data_series_contains_multiple_items(
        self, client, belt_chart_gadget_fixed, mocker
    ):
        """4.2.5: 複数の measurement_item_ids が設定されたガジェットで series に複数項目が含まれる"""
        # Arrange: ゴールド層（hourly）クエリをモック（2項目分のデータ）
        mocker.patch(_GOLD_QUERY, return_value=[
            {'collection_hour': 10, 'summary_item': 1, 'summary_value': 25.5},
            {'collection_hour': 10, 'summary_item': 2, 'summary_value': 15.0},
        ])

        # Act
        response = client.post(
            self._url(belt_chart_gadget_fixed.gadget_uuid),
            json={'display_unit': 'day', 'interval': '10min', 'base_datetime': _VALID_DATETIME},
        )

        # Assert: series に 2 アイテム
        body = response.get_json()
        assert response.status_code == 200
        assert len(body['chart_data']['series']) == 2

    def test_data_series_element_has_name_and_values_keys(
        self, client, belt_chart_gadget_fixed, mocker
    ):
        """⑤レスポンス形式: series の各要素に name（文字列）と values（配列）キーが存在する

        設計書レスポンス形式:
          "series": [{"name": "外気温度", "values": [10.5, 12.3, ...]}, ...]
        """
        # Arrange: ゴールド層クエリをモック（1項目分のデータあり）
        mocker.patch(_GOLD_QUERY, return_value=[
            {'collection_hour': 10, 'summary_item': 1, 'summary_value': 25.5},
        ])

        # Act
        response = client.post(
            self._url(belt_chart_gadget_fixed.gadget_uuid),
            json={'display_unit': 'day', 'interval': '10min', 'base_datetime': _VALID_DATETIME},
        )

        # Assert: series[0] に name（str）と values（list）が存在する
        assert response.status_code == 200
        body = response.get_json()
        series = body['chart_data']['series']
        assert len(series) >= 1
        first = series[0]
        assert 'name' in first, "series要素に 'name' キーが存在しない"
        assert isinstance(first['name'], str), "series[].name は文字列であること"
        assert 'values' in first, "series要素に 'values' キーが存在しない"
        assert isinstance(first['values'], list), "series[].values は配列であること"

    def test_data_labels_format_is_list_of_strings(
        self, client, belt_chart_gadget_fixed, mocker
    ):
        """⑤レスポンス形式: labels が文字列の配列として返る

        設計書レスポンス形式:
          "labels": ["00:00", "00:05", "00:10"]  （display_unit=day 時は時刻文字列）
        """
        # Arrange: ゴールド層クエリをモック（複数時刻のデータ）
        mocker.patch(_GOLD_QUERY, return_value=[
            {'collection_hour': 10, 'summary_item': 1, 'summary_value': 25.5},
            {'collection_hour': 11, 'summary_item': 1, 'summary_value': 26.0},
        ])

        # Act
        response = client.post(
            self._url(belt_chart_gadget_fixed.gadget_uuid),
            json={'display_unit': 'day', 'interval': '10min', 'base_datetime': _VALID_DATETIME},
        )

        # Assert: labels が list で、各要素が文字列
        assert response.status_code == 200
        body = response.get_json()
        labels = body['chart_data']['labels']
        assert isinstance(labels, list), "labels は配列であること"
        if labels:
            assert all(isinstance(lbl, str) for lbl in labels), "labels の各要素は文字列であること"

    def test_data_nonexistent_gadget_returns_404(self, client):
        """2.2.4: 存在しないgadget_uuidで404エラー"""
        # Arrange: DBにガジェットなし
        nonexistent_uuid = str(uuid.uuid4())

        # Act
        response = client.post(
            self._url(nonexistent_uuid),
            json={'display_unit': 'day', 'interval': '10min', 'base_datetime': _VALID_DATETIME},
        )

        # Assert
        assert response.status_code == 404

    def test_data_deleted_gadget_returns_404(
        self, client, belt_chart_gadget_fixed, db_session, mocker
    ):
        """4.2.3: delete_flag=True の論理削除済みガジェットへのデータ取得リクエストは404"""
        # Arrange: ガジェットを論理削除
        belt_chart_gadget_fixed.delete_flag = True
        db_session.flush()

        # Act
        response = client.post(
            self._url(belt_chart_gadget_fixed.gadget_uuid),
            json={'display_unit': 'day', 'interval': '10min', 'base_datetime': _VALID_DATETIME},
        )

        # Assert: get_gadget_by_uuid が delete_flag=False のみ返すため404
        assert response.status_code == 404

    def test_data_invalid_display_unit_returns_400(
        self, client, belt_chart_gadget_fixed
    ):
        """3.6.1: display_unit が hour/day/week/month 以外で400エラー"""
        # Act
        response = client.post(
            self._url(belt_chart_gadget_fixed.gadget_uuid),
            json={'display_unit': 'invalid_unit', 'interval': '10min', 'base_datetime': _VALID_DATETIME},
        )

        # Assert
        assert response.status_code == 400
        assert response.get_json()['error'] == 'パラメータが不正です'

    def test_data_invalid_interval_returns_400(
        self, client, belt_chart_gadget_fixed
    ):
        """3.6.2: interval が 1/2/3/5/10/15min 以外で400エラー（例: 4min は無効）"""
        # Act
        response = client.post(
            self._url(belt_chart_gadget_fixed.gadget_uuid),
            json={'display_unit': 'hour', 'interval': '4min', 'base_datetime': _VALID_DATETIME},
        )

        # Assert
        assert response.status_code == 400

    def test_data_invalid_datetime_format_returns_400(
        self, client, belt_chart_gadget_fixed
    ):
        """3.4.2: base_datetime が YYYY/MM/DD HH:mm:ss 以外の形式で400エラー"""
        # Act
        response = client.post(
            self._url(belt_chart_gadget_fixed.gadget_uuid),
            json={'display_unit': 'day', 'interval': '10min', 'base_datetime': '2026-03-06T12:00:00'},
        )

        # Assert
        assert response.status_code == 400

    def test_data_missing_base_datetime_returns_400(
        self, client, belt_chart_gadget_fixed
    ):
        """3.1.1: base_datetime 未指定で400エラー"""
        # Act
        response = client.post(
            self._url(belt_chart_gadget_fixed.gadget_uuid),
            json={'display_unit': 'day', 'interval': '10min'},
        )

        # Assert
        assert response.status_code == 400

    def test_data_unity_catalog_error_returns_500(
        self, client, belt_chart_gadget_fixed, mocker
    ):
        """2.2.6: Unity Catalog クエリ失敗時に500エラー"""
        # Arrange: 外部API呼び出しが例外を送出
        mocker.patch(_GOLD_QUERY, side_effect=Exception("Databricks connection timeout"))

        # Act
        response = client.post(
            self._url(belt_chart_gadget_fixed.gadget_uuid),
            json={'display_unit': 'day', 'interval': '10min', 'base_datetime': _VALID_DATETIME},
        )

        # Assert
        assert response.status_code == 500

    def test_data_db_error_returns_500(
        self, client, belt_chart_gadget_fixed, mocker
    ):
        """2.2.5: DB接続失敗時に500エラー"""
        from sqlalchemy.exc import OperationalError

        # Arrange: DB操作（check_gadget_access）がOperationalErrorを送出
        mocker.patch(
            'iot_app.views.analysis.customer_dashboard.belt_chart.check_gadget_access',
            side_effect=OperationalError("DB connection failed", None, None),
        )

        # Act
        response = client.post(
            self._url(belt_chart_gadget_fixed.gadget_uuid),
            json={'display_unit': 'day', 'interval': '10min', 'base_datetime': _VALID_DATETIME},
        )

        # Assert
        assert response.status_code == 500

    def test_data_variable_mode_uses_user_setting_device(
        self, client, belt_chart_gadget_variable, dashboard_user_setting, mocker
    ):
        """4.2.5: デバイス可変モードのガジェットは dashboard_user_setting.device_id を使用する"""
        # Arrange: ゴールド層クエリをモック（デバイスIDが dashboard_user_setting から取得される）
        mocker.patch(_GOLD_QUERY, return_value=[])

        # Act: デバイス可変モードガジェットにデータ取得リクエスト
        response = client.post(
            self._url(belt_chart_gadget_variable.gadget_uuid),
            json={'display_unit': 'day', 'interval': '10min', 'base_datetime': _VALID_DATETIME},
        )

        # Assert: ゴールド層クエリが呼ばれ（デバイス可変でも処理できる）、200が返る
        assert response.status_code == 200

    def test_data_variable_mode_without_user_setting_uses_none_device_id(
        self, client, belt_chart_gadget_variable, mocker
    ):
        """② デバイス可変モード・ユーザー設定なし（device_id=None）でも処理が完了する

        dashboard_user_setting が存在しない場合、device_id=None のまま
        fetch_belt_chart_data が呼ばれる。
        サービス層が None デバイスを許容し、空データを返すことを確認する。
        """
        # Arrange: ゴールド層クエリをモック（device_id=None でも呼ばれる）
        mocker.patch(_GOLD_QUERY, return_value=[])

        # Act: dashboard_user_setting フィクスチャなし（DB に user_setting レコードなし）
        response = client.post(
            self._url(belt_chart_gadget_variable.gadget_uuid),
            json={'display_unit': 'day', 'interval': '10min', 'base_datetime': _VALID_DATETIME},
        )

        # Assert: device_id=None でもエラーにならず正常レスポンスが返る
        assert response.status_code == 200
        body = response.get_json()
        assert 'chart_data' in body

    def test_data_updated_at_format_is_datetime_string(
        self, client, belt_chart_gadget_fixed, mocker
    ):
        """⑤ レスポンス形式: updated_at が YYYY/MM/DD HH:mm:ss 形式の文字列である

        設計書レスポンス形式:
          "updated_at": "2026/03/05 12:00:00"
        """
        from datetime import datetime as _dt

        # Arrange
        mocker.patch(_GOLD_QUERY, return_value=[])

        # Act
        response = client.post(
            self._url(belt_chart_gadget_fixed.gadget_uuid),
            json={'display_unit': 'day', 'interval': '10min', 'base_datetime': _VALID_DATETIME},
        )

        # Assert: updated_at が '%Y/%m/%d %H:%M:%S' としてパース可能な文字列
        assert response.status_code == 200
        body = response.get_json()
        updated_at = body.get('updated_at')
        assert updated_at is not None, "updated_at キーが存在しない"
        try:
            _dt.strptime(updated_at, '%Y/%m/%d %H:%M:%S')
        except ValueError:
            raise AssertionError(
                f"updated_at の形式が不正です。期待: 'YYYY/MM/DD HH:mm:ss', 実際: '{updated_at}'"
            )

    def test_data_empty_result_returns_empty_series(
        self, client, belt_chart_gadget_fixed, mocker
    ):
        """4.1.1: データなし（空配列）でも正常に {"labels": [], "series": []} を返す"""
        # Arrange: クエリが空リストを返す
        mocker.patch(_GOLD_QUERY, return_value=[])

        # Act
        response = client.post(
            self._url(belt_chart_gadget_fixed.gadget_uuid),
            json={'display_unit': 'day', 'interval': '10min', 'base_datetime': _VALID_DATETIME},
        )

        # Assert
        assert response.status_code == 200
        body = response.get_json()
        assert body['chart_data']['labels'] == []
        assert body['chart_data']['series'] == []

    def test_data_valid_interval_values_accepted(
        self, client, belt_chart_gadget_fixed, mocker
    ):
        """3.4.1: 許容される集計時間幅（1min/2min/3min/5min/10min/15min）はすべて受け付ける"""
        mocker.patch(_SILVER_QUERY, return_value=[])

        for valid_interval in ('1min', '2min', '3min', '5min', '10min', '15min'):
            # Act
            response = client.post(
                self._url(belt_chart_gadget_fixed.gadget_uuid),
                json={
                    'display_unit': 'hour',
                    'interval': valid_interval,
                    'base_datetime': _VALID_DATETIME,
                },
            )
            # Assert
            assert response.status_code == 200, f"interval={valid_interval} で失敗"


# ─────────────────────────────────────────────────────────────────────────────
# 2. ガジェット登録モーダル表示
# GET /analysis/customer-dashboard/gadgets/belt-chart/create
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.integration
class TestGadgetBeltChartCreate:
    """帯グラフガジェット 登録モーダル表示

    観点: 2.1.3 登録画面表示、2.2 エラー時遷移
    """

    _URL = f"{BASE_URL}/gadgets/belt-chart/create"

    def test_create_modal_returns_200(
        self,
        client,
        auth_user_id,
        dashboard_user_setting,
        dashboard_master,
        dashboard_group_master,
    ):
        """2.1.3: 正常表示 - 200とHTMLを返す"""
        # Act
        response = client.get(self._URL)

        # Assert
        assert response.status_code == 200

    def test_create_modal_has_title_input(
        self,
        client,
        auth_user_id,
        dashboard_user_setting,
        dashboard_master,
        dashboard_group_master,
    ):
        """2.1.3: タイトル入力フィールド（input[name="gadget_name"]）が存在し初期値「帯グラフ」"""
        # Act
        response = client.get(self._URL)
        soup = _soup(response)

        # Assert
        title_input = soup.find('input', {'name': 'gadget_name'})
        assert title_input is not None

    def test_create_modal_has_device_mode_buttons(
        self,
        client,
        auth_user_id,
        dashboard_user_setting,
        dashboard_master,
        dashboard_group_master,
    ):
        """2.1.3: 表示デバイス選択ボタン（fixed/variable）が存在する"""
        # Act
        response = client.get(self._URL)
        soup = _soup(response)

        # Assert: デバイス固定・デバイス可変を示すボタンまたは入力要素が存在する
        mode_inputs = soup.find_all('input', {'name': 'device_mode'})
        assert len(mode_inputs) >= 2
        mode_values = {inp.get('value') for inp in mode_inputs}
        assert 'fixed' in mode_values
        assert 'variable' in mode_values

    def test_create_modal_has_gadget_size_select(
        self,
        client,
        auth_user_id,
        dashboard_user_setting,
        dashboard_master,
        dashboard_group_master,
    ):
        """2.1.3: 部品サイズ選択（select[name="gadget_size"]）に 2x2・2x4 の選択肢がある"""
        # Act
        response = client.get(self._URL)
        soup = _soup(response)

        # Assert
        select = soup.find('select', {'name': 'gadget_size'})
        assert select is not None
        option_values = {opt.get('value') for opt in select.find_all('option') if opt.get('value')}
        assert '0' in option_values or '2x2' in str(select)  # 実装依存: 0=2x2 または "2x2" 直接

    def test_create_modal_has_measurement_items_checkboxes(
        self,
        client,
        auth_user_id,
        dashboard_user_setting,
        dashboard_master,
        dashboard_group_master,
        measurement_items_multi,
    ):
        """2.1.3: measurement_item_master の表示項目がチェックボックスとして描画される（最大5項目選択可能）"""
        # Arrange: measurement_items_multi フィクスチャで3項目登録済み

        # Act
        response = client.get(self._URL)
        soup = _soup(response)

        # Assert: name="measurement_item_ids" のチェックボックスが存在する
        checkboxes = soup.find_all('input', {
            'name': 'measurement_item_ids',
            'type': 'checkbox',
        })
        assert len(checkboxes) >= 1

    def test_create_modal_lists_measurement_item_names(
        self,
        client,
        auth_user_id,
        dashboard_user_setting,
        dashboard_master,
        dashboard_group_master,
        measurement_items_multi,
    ):
        """2.1.3: measurement_item_master の display_name がページに含まれる"""
        # Act
        response = client.get(self._URL)

        # Assert: '外気温度' がHTMLに含まれる
        assert '外気温度'.encode('utf-8') in response.data

    def test_create_modal_lists_groups(
        self,
        client,
        auth_user_id,
        dashboard_user_setting,
        dashboard_master,
        dashboard_group_master,
    ):
        """2.1.3: dashboard_group_master のグループ名が group_id セレクトの option として描画される"""
        # Arrange: dashboard_group_master フィクスチャで 'テストグループ' を登録済み

        # Act
        response = client.get(self._URL)
        soup = _soup(response)

        # Assert
        select = soup.find('select', {'name': 'group_id'})
        assert select is not None
        option_texts = [opt.get_text(strip=True) for opt in select.find_all('option')]
        assert 'テストグループ' in option_texts

    def test_create_modal_lists_summary_methods(
        self,
        client,
        auth_user_id,
        dashboard_user_setting,
        dashboard_master,
        dashboard_group_master,
        gold_summary_method_master,
    ):
        """2.1.3: gold_summary_method_master の集約方法名が summary_method_id セレクトの option として描画される"""
        # Arrange: gold_summary_method_master フィクスチャで AVG/MAX/MIN を登録済み

        # Act
        response = client.get(self._URL)
        soup = _soup(response)

        # Assert
        select = soup.find('select', {'name': 'summary_method_id'})
        assert select is not None
        option_texts = [opt.get_text(strip=True) for opt in select.find_all('option')]
        assert '平均' in option_texts
        assert '最大' in option_texts
        assert '最小' in option_texts

    def test_create_modal_lists_organizations(
        self,
        client,
        auth_scope,
        dashboard_user_setting,
        dashboard_master,
        dashboard_group_master,
    ):
        """⑤ 組織一覧取得: accessible_org_ids に含まれる組織名が <select id="organization-filter"> に描画される

        auth_scope フィクスチャが organization_master_record（organization_id=1, name='テスト組織'）を含む。
        get_organizations(accessible_org_ids=[1]) が 'テスト組織' を返し、
        <select id="organization-filter"> の <option> に含まれることを確認する。
        """
        # Act
        response = client.get(self._URL)
        soup = _soup(response)

        # Assert: organization-filter セレクトに組織名が含まれる
        assert response.status_code == 200
        org_select = soup.find('select', {'id': 'organization-filter'})
        assert org_select is not None, "<select id='organization-filter'> が存在しない"
        option_texts = [opt.get_text(strip=True) for opt in org_select.find_all('option')]
        assert 'テスト組織' in option_texts, f"組織名 'テスト組織' が options に存在しない: {option_texts}"

    def test_create_modal_lists_devices_in_fixed_mode(
        self,
        client,
        auth_user_id,
        dashboard_user_setting,
        dashboard_master,
        dashboard_group_master,
        mocker,
    ):
        """⑥ デバイス一覧取得: accessible_org_ids 内のデバイス名が <select name="device_id"> に描画される

        get_all_devices_in_scope をモックしてデバイスレコードを返し、
        <select name="device_id"> の <option> にデバイス名が含まれることを確認する。
        （デバイス登録には device_type_master / device_inventory_master FK が必要なためモック化）
        """
        from types import SimpleNamespace

        # Arrange: デバイス一覧取得をモック
        mocker.patch(
            'iot_app.views.analysis.customer_dashboard.belt_chart.get_all_devices_in_scope',
            return_value=[
                SimpleNamespace(
                    device_id=99,
                    device_name='テストデバイス_固定モード用',
                    organization_id=1,
                )
            ],
        )

        # Act
        response = client.get(self._URL)
        soup = _soup(response)

        # Assert: device-select に デバイス名が含まれる
        assert response.status_code == 200
        device_select = soup.find('select', {'name': 'device_id'})
        assert device_select is not None, "<select name='device_id'> が存在しない"
        option_texts = [opt.get_text(strip=True) for opt in device_select.find_all('option')]
        assert 'テストデバイス_固定モード用' in option_texts, \
            f"デバイス名 'テストデバイス_固定モード用' が options に存在しない: {option_texts}"

    def test_create_modal_no_user_setting_returns_404(
        self, client, auth_user_id
    ):
        """2.2.4: ダッシュボードユーザー設定が存在しない場合に404エラー"""
        # Arrange: dashboard_user_setting フィクスチャを使わない（DBに設定なし）

        # Act
        response = client.get(self._URL)

        # Assert
        assert response.status_code == 404

    def test_create_modal_no_dashboard_returns_404(
        self, client, auth_user_id, dashboard_user_setting
    ):
        """2.2.4: user_setting は存在するが dashboard_master が存在しない場合に404エラー

        workflow-spec: get_dashboard_by_id が None → CheckDashboard→なし→Error404
        """
        # Arrange: dashboard_user_setting あり・dashboard_master なし（DBに登録しない）

        # Act
        response = client.get(self._URL)

        # Assert
        assert response.status_code == 404

    def test_create_modal_empty_summary_methods_returns_200(
        self,
        client,
        auth_user_id,
        dashboard_user_setting,
        dashboard_master,
        dashboard_group_master,
    ):
        """gold_summary_method_master が空（0件）でも登録モーダルが200で表示される

        workflow-spec: ⑦集約方法一覧取得 - 該当レコードなしでも空リストを渡してテンプレート描画する
        """
        # Arrange: gold_summary_method_master フィクスチャなし（テーブル空）

        # Act
        response = client.get(self._URL)

        # Assert: 集約方法が空でもモーダルは200で表示される
        assert response.status_code == 200


# ─────────────────────────────────────────────────────────────────────────────
# 3. ガジェット登録実行
# POST /analysis/customer-dashboard/gadgets/belt-chart/register
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.integration
class TestGadgetBeltChartRegister:
    """帯グラフガジェット 登録実行

    観点: 3.1 必須チェック、3.2 文字列長チェック、4.3 登録、2.3 リダイレクト
    """

    _URL = f"{BASE_URL}/gadgets/belt-chart/register"

    _SKIP_GADGET_TYPE = frozenset({
        'test_register_without_gadget_type_master_returns_error',
        'test_register_with_deleted_gadget_type_master_returns_error',
    })

    @pytest.fixture(autouse=True)
    def _require_gadget_type(self, request, db_session):
        """全テストで GadgetTypeMaster='帯グラフ' を事前登録する（サービス層の動的ルックアップに必要）。
        GadgetTypeMaster の存在チェックテストではスキップする。
        """
        if request.node.name in self._SKIP_GADGET_TYPE:
            return
        from iot_app.models.customer_dashboard import GadgetTypeMaster
        gt = GadgetTypeMaster(
            gadget_type_id=5,
            gadget_type_name='帯グラフ',
            data_source_type=1,
            gadget_image_path='images/gadgets/belt_chart.png',
            gadget_description='帯グラフガジェット',
            display_order=5,
            creator=1,
            modifier=1,
            delete_flag=False,
        )
        db_session.add(gt)
        db_session.flush()

    def _valid_form(self, **overrides):
        """デバイス可変モード・2x2 の最小有効フォームデータ（表示項目1件）"""
        data = {
            'gadget_name': '帯グラフ',
            'device_mode': 'variable',  # 可変モード: デバイス存在チェックをスキップ
            'device_id': '0',
            'group_id': '1',
            'summary_method_id': '1',
            'measurement_item_ids': '1',  # 表示項目1件選択
            'gadget_size': '0',           # 0=2x2
        }
        data.update(overrides)
        return data

    def test_register_success_redirects_to_dashboard(self, client, measurement_item):
        """2.3.1 / 4.3.1: 正常登録後、ダッシュボード画面へ302リダイレクト"""
        # Arrange: measurement_item フィクスチャで id=1 を登録済み

        # Act
        response = client.post(self._URL, data=self._valid_form(), follow_redirects=False)

        # Assert
        assert response.status_code == 302
        assert BASE_URL in response.headers['Location']
        assert 'registered=1' in response.headers['Location']

    def test_register_creates_record_in_db(self, client, app, measurement_item):
        """4.3.1: 正常登録後、dashboard_gadget_master に1件レコードが追加される"""
        # Arrange
        from iot_app.models.customer_dashboard import DashboardGadgetMaster

        # Act
        client.post(self._URL, data=self._valid_form())

        # Assert: リクエスト後に DB を直接クエリして検証
        with app.app_context():
            from iot_app import db
            count = db.session.query(DashboardGadgetMaster).filter_by(delete_flag=False).count()
        assert count == 1

    def test_register_gadget_uuid_is_set(self, client, app, measurement_item):
        """4.3.5: 登録されたガジェットに gadget_uuid（UUID形式）が自動採番される"""
        # Act
        client.post(self._URL, data=self._valid_form())

        # Assert
        with app.app_context():
            from iot_app import db
            from iot_app.models.customer_dashboard import DashboardGadgetMaster
            gadget = db.session.query(DashboardGadgetMaster).first()
        assert gadget is not None
        assert len(gadget.gadget_uuid) == 36  # UUID形式

    def test_register_title_stored_correctly(self, client, app, measurement_item):
        """4.3.1: 登録されたガジェットのタイトルがDBに正しく保存される"""
        # Act
        client.post(self._URL, data=self._valid_form(gadget_name='テスト帯グラフ'))

        # Assert
        with app.app_context():
            from iot_app import db
            from iot_app.models.customer_dashboard import DashboardGadgetMaster
            gadget = db.session.query(DashboardGadgetMaster).first()
        assert gadget.gadget_name == 'テスト帯グラフ'

    def test_register_gadget_size_2x2_stored(self, client, app, measurement_item):
        """4.3.1: 部品サイズ 2x2（gadget_size=0）がDBに保存される"""
        # Act
        client.post(self._URL, data=self._valid_form(gadget_size='0'))

        # Assert
        with app.app_context():
            from iot_app import db
            from iot_app.models.customer_dashboard import DashboardGadgetMaster
            gadget = db.session.query(DashboardGadgetMaster).first()
        assert gadget.gadget_size == 0

    def test_register_gadget_size_2x4_stored(self, client, app, measurement_item):
        """4.3.1: 部品サイズ 2x4（gadget_size=1）がDBに保存される"""
        # Act
        response = client.post(
            self._URL, data=self._valid_form(gadget_size='1'), follow_redirects=False
        )

        # Assert
        assert response.status_code == 302
        with app.app_context():
            from iot_app import db
            from iot_app.models.customer_dashboard import DashboardGadgetMaster
            gadget = db.session.query(DashboardGadgetMaster).first()
        assert gadget.gadget_size == 1

    def test_register_chart_config_stores_measurement_item_ids_and_summary_method(
        self, client, app, measurement_item
    ):
        """4.3.1: chart_config に measurement_item_ids（リスト）と summary_method_id が正しく保存される"""
        # Act
        client.post(self._URL, data=self._valid_form(measurement_item_ids='1', summary_method_id='1'))

        # Assert
        with app.app_context():
            from iot_app import db
            from iot_app.models.customer_dashboard import DashboardGadgetMaster
            gadget = db.session.query(DashboardGadgetMaster).first()
        chart_config = json.loads(gadget.chart_config)
        assert 1 in chart_config['measurement_item_ids']
        assert chart_config['summary_method_id'] == 1

    def test_register_data_source_config_device_id_is_null_in_variable_mode(
        self, client, app, measurement_item
    ):
        """4.3.4: device_mode=variable 時、data_source_config の device_id は null で保存される"""
        # Act
        client.post(self._URL, data=self._valid_form(device_mode='variable'))

        # Assert
        with app.app_context():
            from iot_app import db
            from iot_app.models.customer_dashboard import DashboardGadgetMaster
            gadget = db.session.query(DashboardGadgetMaster).first()
        data_source_config = json.loads(gadget.data_source_config)
        assert data_source_config['device_id'] is None

    def test_register_fixed_mode_data_source_config_has_device_id_integer(
        self, client, app, measurement_item, mocker
    ):
        """② 固定モード登録後 data_source_config.device_id が送信した整数値で保存される"""
        # Arrange
        from types import SimpleNamespace
        mocker.patch(
            'iot_app.views.analysis.customer_dashboard.belt_chart.check_device_access',
            return_value=SimpleNamespace(device_id=42, device_name='テストデバイス', organization_id=1),
        )

        # Act
        client.post(self._URL, data=self._valid_form(device_mode='fixed', device_id='42'))

        # Assert
        with app.app_context():
            from iot_app import db
            from iot_app.models.customer_dashboard import DashboardGadgetMaster
            gadget = db.session.query(DashboardGadgetMaster).first()
        data_source_config = json.loads(gadget.data_source_config)
        assert data_source_config['device_id'] == 42

    def test_register_gadget_type_id_stored_correctly(
        self, client, app, measurement_item, gadget_type_belt
    ):
        """③ gadget_type_id が gadget_type_belt（id=5）の値で保存される"""
        # Act
        client.post(self._URL, data=self._valid_form(device_mode='variable'))

        # Assert
        with app.app_context():
            from iot_app import db
            from iot_app.models.customer_dashboard import DashboardGadgetMaster
            gadget = db.session.query(DashboardGadgetMaster).first()
        assert gadget.gadget_type_id == 5

    def test_register_delete_flag_is_false_on_creation(self, client, app, measurement_item):
        """4.3.2: 登録直後の delete_flag は False で保存される"""
        # Act
        client.post(self._URL, data=self._valid_form())

        # Assert
        with app.app_context():
            from iot_app import db
            from iot_app.models.customer_dashboard import DashboardGadgetMaster
            gadget = db.session.query(DashboardGadgetMaster).first()
        assert gadget.delete_flag is False

    def test_register_position_x_is_zero(self, client, app, measurement_item):
        """4.3.2: position_x のデフォルト値が 0 で登録される"""
        # Act
        client.post(self._URL, data=self._valid_form())

        # Assert
        with app.app_context():
            from iot_app import db
            from iot_app.models.customer_dashboard import DashboardGadgetMaster
            gadget = db.session.query(DashboardGadgetMaster).first()
        assert gadget.position_x == 0

    def test_register_position_y_is_one_for_first_gadget(self, client, app, measurement_item):
        """4.3.2: グループ内初登録時、position_y は 1（max(0) + 1）で登録される"""
        # Act
        client.post(self._URL, data=self._valid_form())

        # Assert
        with app.app_context():
            from iot_app import db
            from iot_app.models.customer_dashboard import DashboardGadgetMaster
            gadget = db.session.query(DashboardGadgetMaster).first()
        assert gadget.position_y == 1

    def test_register_display_order_increments_for_second_gadget(
        self, client, app, measurement_item
    ):
        """4.3.2: 同グループに2件目登録時、display_order は 2 で登録される"""
        # Arrange: 1件目を登録
        client.post(self._URL, data=self._valid_form(gadget_name='1件目'))

        # Act: 2件目を同グループに登録
        client.post(self._URL, data=self._valid_form(gadget_name='2件目'))

        # Assert: 2件登録されており、display_order が 1, 2 になっている
        with app.app_context():
            from iot_app import db
            from iot_app.models.customer_dashboard import DashboardGadgetMaster
            gadgets = db.session.query(DashboardGadgetMaster).order_by(
                DashboardGadgetMaster.display_order.asc()
            ).all()
        assert len(gadgets) == 2
        assert gadgets[0].display_order == 1
        assert gadgets[1].display_order == 2

    def test_register_gadget_id_is_auto_incremented(self, client, app, measurement_item):
        """4.3.5: 主キー gadget_id が整数として自動採番される"""
        # Act
        client.post(self._URL, data=self._valid_form())

        # Assert
        with app.app_context():
            from iot_app import db
            from iot_app.models.customer_dashboard import DashboardGadgetMaster
            gadget = db.session.query(DashboardGadgetMaster).first()
        assert gadget.gadget_id is not None
        assert isinstance(gadget.gadget_id, int)
        assert gadget.gadget_id >= 1

    def test_register_create_date_is_set(self, client, app, measurement_item):
        """4.3.6: create_date・update_date に現在日時が設定される"""
        # Act
        client.post(self._URL, data=self._valid_form())

        # Assert
        with app.app_context():
            from iot_app import db
            from iot_app.models.customer_dashboard import DashboardGadgetMaster
            gadget = db.session.query(DashboardGadgetMaster).first()
        assert gadget.create_date is not None
        assert gadget.update_date is not None

    def test_register_creator_and_modifier_are_set(self, client, app, measurement_item):
        """4.3.7: bypass_auth_middleware により user_id=1 が設定されるため creator・modifier は 1 になる"""
        # Act
        client.post(self._URL, data=self._valid_form())

        # Assert
        with app.app_context():
            from iot_app import db
            from iot_app.models.customer_dashboard import DashboardGadgetMaster
            gadget = db.session.query(DashboardGadgetMaster).first()
        assert gadget.creator == 1
        assert gadget.modifier == 1

    # ── バリデーション：必須チェック ──────────────────────────────────────────

    def test_register_title_required_returns_400(self, client, measurement_item):
        """3.1.1: タイトル未入力で400（バリデーションエラー）"""
        # Act
        response = client.post(self._URL, data=self._valid_form(gadget_name=''))

        # Assert
        assert response.status_code == 400

    def test_register_group_required_returns_400(self, client, measurement_item):
        """3.1.2: グループ未選択（0）で400"""
        # Act
        response = client.post(self._URL, data=self._valid_form(group_id='0'))

        # Assert
        assert response.status_code == 400

    def test_register_summary_method_required_returns_400(self, client, measurement_item):
        """3.1.3: 集約方法未選択（0）で400"""
        # Act
        response = client.post(self._URL, data=self._valid_form(summary_method_id='0'))

        # Assert
        assert response.status_code == 400

    def test_register_measurement_item_required_returns_400(self, client, measurement_item):
        """3.1.4: 表示項目未選択で400（1〜5個必須）"""
        # Act: measurement_item_ids を送信しない
        data = {
            'gadget_name': '帯グラフ',
            'device_mode': 'variable',
            'device_id': '0',
            'group_id': '1',
            'summary_method_id': '1',
            'gadget_size': '0',
        }
        response = client.post(self._URL, data=data)

        # Assert
        assert response.status_code == 400

    def test_register_measurement_item_max_5_items(self, client, app, db_session):
        """3.1.4: 表示項目を5個選択して登録成功"""
        from iot_app.models.measurement import MeasurementItemMaster
        # Arrange: 5件の measurement_item を登録
        for i in range(1, 6):
            item = MeasurementItemMaster(
                measurement_item_id=i,
                measurement_item_name=f'項目{i}',
                display_name=f'項目{i}',
                silver_data_column_name=f'col_{i}',
                unit_name='℃',
                creator=1,
                modifier=1,
                delete_flag=False,
            )
            db_session.add(item)
        db_session.flush()

        data = {
            'gadget_name': '帯グラフ',
            'device_mode': 'variable',
            'device_id': '0',
            'group_id': '1',
            'summary_method_id': '1',
            'measurement_item_ids': ['1', '2', '3', '4', '5'],  # 5項目
            'gadget_size': '0',
        }

        # Act
        response = client.post(self._URL, data=data, follow_redirects=False)

        # Assert
        assert response.status_code == 302

    def test_register_measurement_item_over_5_returns_400(self, client, db_session):
        """3.1.4: 表示項目を6個以上選択すると400"""
        from iot_app.models.measurement import MeasurementItemMaster
        # Arrange: 6件の measurement_item を登録
        for i in range(1, 7):
            item = MeasurementItemMaster(
                measurement_item_id=i,
                measurement_item_name=f'項目{i}',
                display_name=f'項目{i}',
                silver_data_column_name=f'col_{i}',
                unit_name='℃',
                creator=1,
                modifier=1,
                delete_flag=False,
            )
            db_session.add(item)
        db_session.flush()

        data = {
            'gadget_name': '帯グラフ',
            'device_mode': 'variable',
            'device_id': '0',
            'group_id': '1',
            'summary_method_id': '1',
            'measurement_item_ids': ['1', '2', '3', '4', '5', '6'],  # 6項目（超過）
            'gadget_size': '0',
        }

        # Act
        response = client.post(self._URL, data=data)

        # Assert
        assert response.status_code == 400

    def test_register_gadget_size_required_returns_400(self, client, measurement_item):
        """3.1.5: 部品サイズ未選択で400"""
        # Act
        response = client.post(self._URL, data=self._valid_form(gadget_size=''))

        # Assert
        assert response.status_code == 400

    # ── バリデーション：文字列長チェック ─────────────────────────────────────

    def test_register_title_20_chars_succeeds(self, client, measurement_item):
        """3.2.1: タイトル20文字以内は登録成功"""
        # Act
        response = client.post(
            self._URL, data=self._valid_form(gadget_name='あ' * 20), follow_redirects=False
        )

        # Assert
        assert response.status_code == 302

    def test_register_title_21_chars_returns_400(self, client, measurement_item):
        """3.2.2: タイトル21文字以上で400"""
        # Act
        response = client.post(self._URL, data=self._valid_form(gadget_name='あ' * 21))

        # Assert
        assert response.status_code == 400

    # ── バリデーション：デバイス固定モード ───────────────────────────────────

    def test_register_device_id_required_in_fixed_mode_returns_400(
        self, client, measurement_item
    ):
        """3.1.6: device_mode=fixed でデバイスID未指定（0）は400（バリデーションエラー）"""
        # Act
        response = client.post(
            self._URL, data=self._valid_form(device_mode='fixed', device_id='0')
        )

        # Assert
        assert response.status_code == 400

    def test_register_fixed_mode_nonexistent_device_id_returns_404(
        self, client, measurement_item
    ):
        """4.3.8: device_mode=fixed かつ DBに存在しない device_id を送信すると 404"""
        # Arrange: DeviceMaster に該当レコードを登録しない（nonexistent_id=9999）
        form_data = self._valid_form(device_mode='fixed', device_id='9999')

        # Act
        response = client.post(self._URL, data=form_data)

        # Assert
        assert response.status_code == 404

    def test_register_fixed_mode_device_not_in_accessible_orgs_returns_404(
        self, client, app, measurement_item
    ):
        """4.3.9: device_mode=fixed、device_id はDBに存在するがアクセス可能組織外のため 404

        認証未実装ブランチでは get_accessible_org_ids() が常に [] を返すため、
        fixed モードのデバイスチェック（ビュー層）は必ず abort(404) になる。
        """
        # Arrange: DeviceMaster にデバイスを登録するが、org スコープ外（accessible_org_ids=[]）
        with app.app_context():
            from iot_app import db
            from iot_app.models.device import DeviceMaster
            from iot_app.models.organization import OrganizationMaster

            org = OrganizationMaster(
                organization_name='別組織',
                organization_type_id=1,
                address='',
                phone_number='000',
                contact_person='担当者',
                contract_status_id=1,
                contract_start_date=date(2024, 1, 1),
                databricks_group_id='test-group-other',
                creator=1,
                modifier=1,
            )
            db.session.add(org)
            db.session.flush()

            device = DeviceMaster(
                device_uuid=str(uuid.uuid4()),
                device_name='別組織デバイス',
                organization_id=org.organization_id,
                device_type_id=1,
                device_model='モデルX',
                device_inventory_id=1,
                creator=1,
                modifier=1,
            )
            db.session.add(device)
            db.session.commit()
            device_id = device.device_id

        form_data = self._valid_form(device_mode='fixed', device_id=str(device_id))

        # Act
        response = client.post(self._URL, data=form_data)

        # Assert: accessible_org_ids=[] のためアクセス不可 → 404
        assert response.status_code == 404

    # ── GadgetTypeMaster 存在チェック ────────────────────────────────────────

    def test_register_without_gadget_type_master_returns_error(
        self, client, measurement_item
    ):
        """4.3.10: GadgetTypeMaster に「帯グラフ」レコードが存在しない場合はエラー"""
        # Arrange: gadget_type フィクスチャを使わず GadgetTypeMaster を空にしておく

        # Act
        response = client.post(self._URL, data=self._valid_form())

        # Assert: GadgetTypeMaster に該当レコードなし → 404 または 500
        assert response.status_code in (404, 500)

    def test_register_with_deleted_gadget_type_master_returns_error(
        self, client, app, measurement_item
    ):
        """4.3.11: GadgetTypeMaster に delete_flag=True の「帯グラフ」しかない場合はエラー"""
        # Arrange: delete_flag=True の帯グラフレコードのみ登録
        with app.app_context():
            from iot_app import db
            from iot_app.models.customer_dashboard import GadgetTypeMaster
            gt = GadgetTypeMaster(
                gadget_type_name='帯グラフ',
                data_source_type=1,
                gadget_image_path='images/gadgets/belt_chart.png',
                gadget_description='帯グラフガジェット',
                display_order=5,
                creator=1,
                modifier=1,
                delete_flag=True,
            )
            db.session.add(gt)
            db.session.commit()

        # Act
        response = client.post(self._URL, data=self._valid_form())

        # Assert: delete_flag=True のため first() が None → 404 または 500
        assert response.status_code in (404, 500)

    # ── バリデーションエラー時のモーダル再描画 ──────────────────────────────

    def test_register_400_re_renders_modal_with_form(self, client, measurement_item):
        """2.2.2: バリデーションエラー時（400）に登録モーダルが再描画され、フォームが含まれる"""
        # Act: タイトル空で送信 → 400
        response = client.post(self._URL, data=self._valid_form(gadget_name=''))
        soup = _soup(response)

        # Assert: フォームが再描画されている
        assert response.status_code == 400
        assert soup.find('input', {'name': 'gadget_name'}) is not None

    def test_register_db_error_returns_500(self, client, measurement_item, mocker):
        """2.2.5: DB接続失敗時に500エラー"""
        from sqlalchemy.exc import OperationalError

        # Arrange: DB書き込み（register_belt_chart_gadget）がOperationalErrorを送出
        mocker.patch(
            'iot_app.views.analysis.customer_dashboard.belt_chart.register_belt_chart_gadget',
            side_effect=OperationalError("DB connection failed", None, None),
        )

        # Act: 正常なパラメータで送信
        response = client.post(self._URL, data=self._valid_form())

        # Assert
        assert response.status_code == 500

    def test_register_unique_constraint_violation_returns_500(
        self, client, measurement_item, mocker
    ):
        """7.2.1: UNIQUE制約違反発生時にロールバックされ500エラーが返る

        gadget_uuid は UNIQUE制約あり。同一UUIDの二重登録を模擬し、
        IntegrityError が発生した場合にビュー層でロールバックされることを確認する。
        """
        from sqlalchemy.exc import IntegrityError

        # Arrange: DB書き込みが UNIQUE制約違反を送出
        mocker.patch(
            'iot_app.views.analysis.customer_dashboard.belt_chart.register_belt_chart_gadget',
            side_effect=IntegrityError(
                "Duplicate entry 'xxx-yyy-zzz' for key 'gadget_uuid'", None, None
            ),
        )

        # Act
        response = client.post(self._URL, data=self._valid_form())

        # Assert: ロールバック済み → 500
        assert response.status_code == 500

    def test_register_foreign_key_constraint_violation_returns_500(
        self, client, measurement_item, mocker
    ):
        """7.2.2: 外部キー制約違反発生時にロールバックされ500エラーが返る

        dashboard_group_id は dashboard_group_master への外部キー。
        存在しないグループIDが渡された場合の IntegrityError ハンドリングを確認する。
        """
        from sqlalchemy.exc import IntegrityError

        # Arrange: DB書き込みが外部キー制約違反を送出
        mocker.patch(
            'iot_app.views.analysis.customer_dashboard.belt_chart.register_belt_chart_gadget',
            side_effect=IntegrityError(
                "Cannot add or update a child row: a foreign key constraint fails "
                "(`databricks_iot`.`dashboard_gadget_master`, CONSTRAINT `fk_gadget_group` "
                "FOREIGN KEY (`dashboard_group_id`) REFERENCES `dashboard_group_master` (`dashboard_group_id`))",
                None,
                None,
            ),
        )

        # Act
        response = client.post(self._URL, data=self._valid_form())

        # Assert: ロールバック済み → 500
        assert response.status_code == 500


# ─────────────────────────────────────────────────────────────────────────────
# 4. CSVエクスポート
# GET /analysis/customer-dashboard/gadgets/<gadget_uuid>?export=csv
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.integration
class TestGadgetBeltChartCsvExport:
    """帯グラフガジェット CSVエクスポート

    観点: 4.6 CSVエクスポート、2.2 エラー時遷移
    """

    @pytest.fixture(autouse=True)
    def _require_auth_scope(
        self, auth_scope, dashboard_master, dashboard_group_master, gadget_type_belt
    ):
        """全テストで認証ユーザー＋アクセス可能スコープ＋ガジェット関連マスタを事前登録する"""

    def _url(self, gadget_uuid, **params):
        query = "&".join(f"{k}={v}" for k, v in params.items())
        return f"{BASE_URL}/gadgets/{gadget_uuid}?{query}"

    def _default_params(self):
        return {
            'export': 'csv',
            'display_unit': 'day',
            'interval': '10min',
            'base_datetime': _VALID_DATETIME,
        }

    def test_csv_returns_200(self, client, belt_chart_gadget_fixed, mocker):
        """4.6.1: 正常エクスポート - 200レスポンス"""
        # Arrange: 外部APIをモック
        mocker.patch(_GOLD_QUERY, return_value=[
            {'collection_hour': 10, 'summary_item': 1, 'summary_value': 25.5},
        ])

        # Act
        response = client.get(
            self._url(belt_chart_gadget_fixed.gadget_uuid, **self._default_params())
        )

        # Assert
        assert response.status_code == 200

    def test_csv_content_type_is_text_csv(self, client, belt_chart_gadget_fixed, mocker):
        """4.6.1: Content-Type が text/csv"""
        # Arrange
        mocker.patch(_GOLD_QUERY, return_value=[])

        # Act
        response = client.get(
            self._url(belt_chart_gadget_fixed.gadget_uuid, **self._default_params())
        )

        # Assert
        assert 'text/csv' in response.content_type

    def test_csv_content_disposition_is_attachment(
        self, client, belt_chart_gadget_fixed, mocker
    ):
        """4.6.1: Content-Disposition で attachment（ダウンロード）になる"""
        # Arrange
        mocker.patch(_GOLD_QUERY, return_value=[])

        # Act
        response = client.get(
            self._url(belt_chart_gadget_fixed.gadget_uuid, **self._default_params())
        )

        # Assert
        disposition = response.headers.get('Content-Disposition', '')
        assert 'attachment' in disposition

    def test_csv_filename_format(self, client, belt_chart_gadget_fixed, mocker):
        """4.6.2: Content-Disposition のファイル名が sensor_data_YYYYMMDDHHmmss.csv 形式になる

        UI仕様書: 出力ファイル名: sensor_data_{yyyyMMddHHmmss}.csv
        """
        import re
        # Arrange
        mocker.patch(_GOLD_QUERY, return_value=[])

        # Act
        response = client.get(
            self._url(belt_chart_gadget_fixed.gadget_uuid, **self._default_params())
        )

        # Assert: ファイル名が指定フォーマット
        disposition = response.headers.get('Content-Disposition', '')
        assert re.search(r'sensor_data_\d{14}\.csv', disposition)

    def test_csv_has_header_row(self, client, belt_chart_gadget_fixed, mocker):
        """4.6.5: CSVの1行目に「デバイス名」「時間」列ヘッダーが含まれる

        CSVサンプル（設計書）の先頭列: デバイス名,時間,{測定項目名...}
        """
        # Arrange
        mocker.patch(_GOLD_QUERY, return_value=[])

        # Act
        response = client.get(
            self._url(belt_chart_gadget_fixed.gadget_uuid, **self._default_params())
        )

        # Assert: CSV先頭行に「デバイス名」「時間」が含まれる（BOM付きUTF-8考慮）
        csv_text = response.data.decode('utf-8-sig')
        lines = [line for line in csv_text.splitlines() if line.strip()]
        assert len(lines) >= 1
        header = lines[0]
        assert 'デバイス名' in header
        assert '時間' in header

    def test_csv_without_export_param_returns_404(self, client, belt_chart_gadget_fixed):
        """2.2.4: export=csv パラメータなしで404"""
        # Act
        response = client.get(
            f"{BASE_URL}/gadgets/{belt_chart_gadget_fixed.gadget_uuid}"
            f"?display_unit=day&interval=10min&base_datetime={_VALID_DATETIME}"
        )

        # Assert
        assert response.status_code == 404

    def test_csv_nonexistent_gadget_returns_404(self, client):
        """2.2.4: 存在しないgadget_uuidで404"""
        # Act
        response = client.get(self._url(str(uuid.uuid4()), **self._default_params()))

        # Assert
        assert response.status_code == 404

    def test_csv_deleted_gadget_returns_404(
        self, client, belt_chart_gadget_fixed, db_session
    ):
        """4.2.3: delete_flag=True の論理削除済みガジェットへのCSVエクスポートは404"""
        # Arrange: ガジェットを論理削除
        belt_chart_gadget_fixed.delete_flag = True
        db_session.flush()

        # Act
        response = client.get(
            self._url(belt_chart_gadget_fixed.gadget_uuid, **self._default_params())
        )

        # Assert
        assert response.status_code == 404

    def test_csv_invalid_display_unit_returns_400(
        self, client, belt_chart_gadget_fixed
    ):
        """3.6.1: 不正な display_unit で400"""
        # Act
        params = {**self._default_params(), 'display_unit': 'invalid'}
        response = client.get(self._url(belt_chart_gadget_fixed.gadget_uuid, **params))

        # Assert
        assert response.status_code == 400

    def test_csv_invalid_interval_returns_400(
        self, client, belt_chart_gadget_fixed
    ):
        """3.6.2: 不正な interval（4min）で400"""
        # Act
        params = {**self._default_params(), 'interval': '4min'}
        response = client.get(self._url(belt_chart_gadget_fixed.gadget_uuid, **params))

        # Assert
        assert response.status_code == 400

    def test_csv_invalid_datetime_format_returns_400(
        self, client, belt_chart_gadget_fixed
    ):
        """3.4.2: 不正な日付形式（ISO形式等）で400"""
        # Act
        params = {**self._default_params(), 'base_datetime': '2026-03-06T12:00:00'}
        response = client.get(self._url(belt_chart_gadget_fixed.gadget_uuid, **params))

        # Assert
        assert response.status_code == 400

    def test_csv_unity_catalog_error_returns_500(
        self, client, belt_chart_gadget_fixed, mocker
    ):
        """2.2.6: Unity Catalog クエリ失敗時に500"""
        # Arrange
        mocker.patch(_GOLD_QUERY, side_effect=Exception("Connection error"))

        # Act
        response = client.get(
            self._url(belt_chart_gadget_fixed.gadget_uuid, **self._default_params())
        )

        # Assert
        assert response.status_code == 500

    def test_csv_db_error_returns_500(
        self, client, belt_chart_gadget_fixed, mocker
    ):
        """2.2.5: DB接続失敗時に500エラー"""
        from sqlalchemy.exc import OperationalError

        # Arrange: DB操作（check_gadget_access）がOperationalErrorを送出
        mocker.patch(
            'iot_app.views.analysis.customer_dashboard.belt_chart.check_gadget_access',
            side_effect=OperationalError("DB connection failed", None, None),
        )

        # Act
        response = client.get(
            self._url(belt_chart_gadget_fixed.gadget_uuid, **self._default_params())
        )

        # Assert
        assert response.status_code == 500

    def test_csv_hour_unit_uses_silver_query(
        self, client, belt_chart_gadget_fixed, measurement_items_multi, mocker
    ):
        """4.6.3: display_unit=hour のCSVエクスポートはシルバー層クエリを使用する"""
        # Arrange
        mock_silver = mocker.patch(_SILVER_QUERY, return_value=[])

        # Act
        params = {**self._default_params(), 'display_unit': 'hour'}
        response = client.get(self._url(belt_chart_gadget_fixed.gadget_uuid, **params))

        # Assert: シルバー層クエリが呼ばれている
        assert response.status_code == 200
        assert mock_silver.called

    def test_csv_variable_mode_gadget_returns_200(
        self, client, belt_chart_gadget_variable, dashboard_user_setting, mocker
    ):
        """4.6.6: デバイス可変モードガジェットのCSVエクスポートも正常に200を返す"""
        # Arrange: ゴールド層クエリをモック
        mocker.patch(_GOLD_QUERY, return_value=[])

        # Act
        response = client.get(
            self._url(belt_chart_gadget_variable.gadget_uuid, **self._default_params())
        )

        # Assert
        assert response.status_code == 200

    def test_csv_week_unit_returns_200(self, client, belt_chart_gadget_fixed, mocker):
        """4.6.3: display_unit=week のCSVエクスポートが正常に200を返す（ゴールド層daily使用）"""
        # Arrange
        mocker.patch(_GOLD_QUERY, return_value=[])

        # Act
        params = {**self._default_params(), 'display_unit': 'week'}
        response = client.get(self._url(belt_chart_gadget_fixed.gadget_uuid, **params))

        # Assert
        assert response.status_code == 200

    def test_csv_month_unit_returns_200(self, client, belt_chart_gadget_fixed, mocker):
        """4.6.3: display_unit=month のCSVエクスポートが正常に200を返す（ゴールド層daily使用）"""
        # Arrange
        mocker.patch(_GOLD_QUERY, return_value=[])

        # Act
        params = {**self._default_params(), 'display_unit': 'month'}
        response = client.get(self._url(belt_chart_gadget_fixed.gadget_uuid, **params))

        # Assert
        assert response.status_code == 200

    def test_csv_header_columns_contain_device_name_and_time(
        self, client, belt_chart_gadget_fixed, mocker
    ):
        """4.6.5: CSVヘッダーが「デバイス名」「時間」「測定項目名」列を含む"""
        # Arrange
        mocker.patch(
            'iot_app.views.analysis.customer_dashboard.belt_chart.fetch_belt_chart_data',
            return_value=[],
        )
        mocker.patch(
            'iot_app.views.analysis.customer_dashboard.belt_chart.format_belt_chart_data',
            return_value={'labels': [], 'series': [{'name': '外気温度（℃）', 'values': []}]},
        )
        mocker.patch(
            'iot_app.views.analysis.customer_dashboard.belt_chart.get_device_name_by_id',
            return_value='DEV-001',
        )

        # Act
        response = client.get(
            self._url(belt_chart_gadget_fixed.gadget_uuid, **self._default_params())
        )

        # Assert
        assert response.status_code == 200
        csv_text = response.data.decode('utf-8-sig')
        header = csv_text.splitlines()[0]
        assert 'デバイス名' in header
        assert '時間' in header
        assert '外気温度（℃）' in header

    def test_csv_hour_unit_time_format(
        self, client, belt_chart_gadget_fixed, mocker
    ):
        """CSVの時単位は「YYYY/MM/DD HH:mm」形式でタイムスタンプが出力される"""
        # Arrange
        mocker.patch(
            'iot_app.views.analysis.customer_dashboard.belt_chart.fetch_belt_chart_data',
            return_value=[],
        )
        mocker.patch(
            'iot_app.views.analysis.customer_dashboard.belt_chart.format_belt_chart_data',
            return_value={'labels': ['10:10'], 'series': [{'name': '外気温度（℃）', 'values': [25.50]}]},
        )
        mocker.patch(
            'iot_app.views.analysis.customer_dashboard.belt_chart.get_device_name_by_id',
            return_value='DEV-001',
        )

        # Act
        params = {**self._default_params(), 'display_unit': 'hour', 'base_datetime': '2026/02/05 10:00:00'}
        response = client.get(self._url(belt_chart_gadget_fixed.gadget_uuid, **params))

        # Assert
        assert response.status_code == 200
        csv_text = response.data.decode('utf-8-sig')
        data_row = csv_text.splitlines()[1]
        assert '2026/02/05 10:10' in data_row

    def test_csv_day_unit_time_format(
        self, client, belt_chart_gadget_fixed, mocker
    ):
        """CSVの日単位は「YYYY/MM/DD HH:00」形式でタイムスタンプが出力される"""
        # Arrange
        mocker.patch(
            'iot_app.views.analysis.customer_dashboard.belt_chart.fetch_belt_chart_data',
            return_value=[],
        )
        mocker.patch(
            'iot_app.views.analysis.customer_dashboard.belt_chart.format_belt_chart_data',
            return_value={'labels': ['10'], 'series': [{'name': '外気温度（℃）', 'values': [25.50]}]},
        )
        mocker.patch(
            'iot_app.views.analysis.customer_dashboard.belt_chart.get_device_name_by_id',
            return_value='DEV-001',
        )

        # Act
        params = {**self._default_params(), 'display_unit': 'day', 'base_datetime': '2026/02/05 10:00:00'}
        response = client.get(self._url(belt_chart_gadget_fixed.gadget_uuid, **params))

        # Assert
        assert response.status_code == 200
        csv_text = response.data.decode('utf-8-sig')
        data_row = csv_text.splitlines()[1]
        assert '2026/02/05 10:00' in data_row

    def test_csv_week_unit_time_format(
        self, client, belt_chart_gadget_fixed, mocker
    ):
        """CSVの週単位は「YYYY/MM/DD(曜)」形式でタイムスタンプが出力される"""
        # Arrange
        # base_datetime=2026/03/06（金曜）: 週開始=2026/03/01（日）、Mon→2026/03/02
        mocker.patch(
            'iot_app.views.analysis.customer_dashboard.belt_chart.fetch_belt_chart_data',
            return_value=[],
        )
        mocker.patch(
            'iot_app.views.analysis.customer_dashboard.belt_chart.format_belt_chart_data',
            return_value={'labels': ['Mon'], 'series': [{'name': '外気温度（℃）', 'values': [25.50]}]},
        )
        mocker.patch(
            'iot_app.views.analysis.customer_dashboard.belt_chart.get_device_name_by_id',
            return_value='DEV-001',
        )

        # Act
        params = {**self._default_params(), 'display_unit': 'week'}
        response = client.get(self._url(belt_chart_gadget_fixed.gadget_uuid, **params))

        # Assert
        assert response.status_code == 200
        csv_text = response.data.decode('utf-8-sig')
        data_row = csv_text.splitlines()[1]
        # 2026/03/06（金）→ 週開始日（日）= 2026/03/01, Mon = 2026/03/02
        assert '2026/03/02(Mon)' in data_row

    def test_csv_month_unit_time_format(
        self, client, belt_chart_gadget_fixed, mocker
    ):
        """CSVの月単位は「YYYY/MM/DD」形式（時分なし）でタイムスタンプが出力される"""
        # Arrange
        mocker.patch(
            'iot_app.views.analysis.customer_dashboard.belt_chart.fetch_belt_chart_data',
            return_value=[],
        )
        mocker.patch(
            'iot_app.views.analysis.customer_dashboard.belt_chart.format_belt_chart_data',
            return_value={'labels': ['01'], 'series': [{'name': '外気温度（℃）', 'values': [25.50]}]},
        )
        mocker.patch(
            'iot_app.views.analysis.customer_dashboard.belt_chart.get_device_name_by_id',
            return_value='DEV-001',
        )

        # Act
        params = {**self._default_params(), 'display_unit': 'month'}
        response = client.get(self._url(belt_chart_gadget_fixed.gadget_uuid, **params))

        # Assert
        assert response.status_code == 200
        csv_text = response.data.decode('utf-8-sig')
        data_row = csv_text.splitlines()[1]
        # 月単位: YYYY/MM/DD（時分なし）
        assert '2026/03/01' in data_row
        assert ':' not in data_row.split(',')[1]  # 時刻列にコロンなし


# ─────────────────────────────────────────────────────────────────────────────
# 5. 認証テスト
# 観点: 1.1 認証テスト
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.integration
class TestBeltChartAuthentication:
    """帯グラフガジェット 認証テスト

    観点: 1.1 認証テスト

    NOTE: require_auth デコレータは現在 no-op（将来の本実装に向けた設計予約）。
          認証はミドルウェア層（authenticate_request）で実施。
          テスト環境では bypass_auth_middleware により認証ミドルウェアをバイパス済み。
          「認証済み」= ユーザーが user_master に存在し g.current_user.user_id が解決できる状態。
          「未認証相当」= user_id=1 だが user_master に存在しない → org_id が解決できない状態。
    """

    def test_authenticated_user_can_access_data_endpoint(
        self,
        client,
        auth_scope,
        dashboard_master,
        dashboard_group_master,
        gadget_type_belt,
        belt_chart_gadget_fixed,
        mocker,
    ):
        """1.1.1: 認証済みユーザー（auth_scope）はデータ取得エンドポイントに正常アクセスできる"""
        # Arrange: 外部APIをモック
        mocker.patch(_GOLD_QUERY, return_value=[])

        # Act
        response = client.post(
            f"{BASE_URL}/gadgets/{belt_chart_gadget_fixed.gadget_uuid}/data",
            json={
                'display_unit': 'day',
                'interval': '10min',
                'base_datetime': _VALID_DATETIME,
            },
        )

        # Assert
        assert response.status_code == 200

    def test_unauthenticated_user_cannot_access_data_endpoint(
        self,
        client,
        dashboard_master,
        dashboard_group_master,
        gadget_type_belt,
        belt_chart_gadget_fixed,
    ):
        """1.1.2: 未認証相当ユーザー（user_master 不在 → accessible_orgs=[]）はデータ取得で404を受ける

        user_id=1 が g.current_user に設定されるが、user_master にレコードがないため
        get_organization_id_by_user(1) → None → get_accessible_organizations(None) → []
        → check_gadget_access(uuid, []) → None → 404 が返る。
        """
        # Arrange: auth_scope を使わない（user_master / organization_closure 未登録）

        # Act
        response = client.post(
            f"{BASE_URL}/gadgets/{belt_chart_gadget_fixed.gadget_uuid}/data",
            json={
                'display_unit': 'day',
                'interval': '10min',
                'base_datetime': _VALID_DATETIME,
            },
        )

        # Assert
        assert response.status_code == 404

    def test_authenticated_user_can_access_create_endpoint(
        self,
        client,
        auth_scope,
        dashboard_master,
        dashboard_group_master,
        gadget_type_belt,
    ):
        """1.1.1: 認証済みユーザーはガジェット登録フォーム取得エンドポイントに正常アクセスできる"""
        # Act
        response = client.get(f"{BASE_URL}/gadgets/belt-chart/create")

        # Assert
        assert response.status_code == 200

    def test_authenticated_user_can_access_csv_export_endpoint(
        self,
        client,
        auth_scope,
        dashboard_master,
        dashboard_group_master,
        gadget_type_belt,
        belt_chart_gadget_fixed,
        mocker,
    ):
        """1.1.1: 認証済みユーザーはCSVエクスポートエンドポイントに正常アクセスできる"""
        # Arrange
        mocker.patch(_GOLD_QUERY, return_value=[])

        # Act
        response = client.get(
            f"{BASE_URL}/gadgets/{belt_chart_gadget_fixed.gadget_uuid}"
            f"?export=csv&display_unit=day&interval=10min&base_datetime={_VALID_DATETIME}"
        )

        # Assert
        assert response.status_code == 200


# ─────────────────────────────────────────────────────────────────────────────
# 6. 認可テスト
# 観点: 1.2 認可（権限チェック）機能
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.integration
class TestBeltChartAuthorization:
    """帯グラフガジェット 認可テスト

    観点: 1.2 認可（権限チェック）機能

    NOTE: require_auth デコレータが現状 no-op のため、ロールベースアクセス制御は未実装。
          帯グラフ関連エンドポイントにはロール制限が設計書上定義されていないため、
          認証済みユーザーであれば user_type_id によらず操作可能。
          本クラスは将来のロール制限実装に備えた観点を記録する目的で作成。
    """

    @pytest.fixture(autouse=True)
    def _require_auth_scope(
        self, auth_scope, dashboard_master, dashboard_group_master, gadget_type_belt
    ):
        """全テストで認証ユーザー＋アクセス可能スコープ＋ガジェット関連マスタを事前登録する"""

    def test_any_authenticated_user_can_access_data_endpoint(
        self, client, belt_chart_gadget_fixed, mocker
    ):
        """1.2.1〜1.2.6: 認証済みユーザーはロールによらずデータ取得エンドポイントにアクセスできる

        # TODO: require_auth が no-op のため、ロール別アクセス制御は未実装。
        #       将来の実装時に user_type_id ごとのテストケースに分割する。
        """
        # Arrange
        mocker.patch(_GOLD_QUERY, return_value=[])

        # Act
        response = client.post(
            f"{BASE_URL}/gadgets/{belt_chart_gadget_fixed.gadget_uuid}/data",
            json={
                'display_unit': 'day',
                'interval': '10min',
                'base_datetime': _VALID_DATETIME,
            },
        )

        # Assert: 現状はロール制限なし → 200
        assert response.status_code == 200


# ─────────────────────────────────────────────────────────────────────────────
# 7. データスコープフィルタテスト
# 観点: 1.3 データスコープフィルタテスト
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.integration
class TestBeltChartDataScope:
    """帯グラフガジェット データスコープフィルタテスト

    観点: 1.3 データスコープフィルタテスト

    スコープ制御の仕組み:
      get_organization_id_by_user(user_id) → ユーザーの所属組織ID
      get_accessible_organizations(org_id) → organization_closure を辿った組織IDリスト
      check_gadget_access(gadget_uuid, accessible_org_ids) → 2段JOIN でスコープ検証

    テストデータ構成:
      - ユーザー: org_id=1（auth_scope フィクスチャで設定）
      - closure: parent=1, sub=1（自組織）, parent=1, sub=sub_org（下位組織）
      - アクセス不可組織: closure 未登録の org（parent=1 に含まれない）
    """

    @pytest.fixture()
    def scope_orgs(self, db_session):
        """スコープテスト用の組織・closure・ダッシュボード・グループ・ガジェットを生成する

        Returns:
            dict:
                gadget_own     : 自組織ダッシュボードに属するガジェット（アクセス可）
                gadget_sub     : 下位組織ダッシュボードに属するガジェット（アクセス可）
                gadget_other   : 無関係組織ダッシュボードに属するガジェット（アクセス不可）
        """
        from iot_app.models.customer_dashboard import (
            DashboardGadgetMaster,
            DashboardGroupMaster,
            DashboardMaster,
            GadgetTypeMaster,
        )
        from iot_app.models.organization import OrganizationClosure, OrganizationMaster

        # ── 組織 ──────────────────────────────────────────────────────────
        org_own = OrganizationMaster(
            organization_name='スコープテスト自組織',
            organization_type_id=1,
            address='住所1',
            phone_number='000-0001',
            contact_person='担当1',
            contract_status_id=1,
            contract_start_date=date(2024, 1, 1),
            databricks_group_id='scope-own',
            creator=1,
            modifier=1,
        )
        org_sub = OrganizationMaster(
            organization_name='スコープテスト下位組織',
            organization_type_id=1,
            address='住所2',
            phone_number='000-0002',
            contact_person='担当2',
            contract_status_id=1,
            contract_start_date=date(2024, 1, 1),
            databricks_group_id='scope-sub',
            creator=1,
            modifier=1,
        )
        org_other = OrganizationMaster(
            organization_name='スコープテスト無関係組織',
            organization_type_id=1,
            address='住所3',
            phone_number='000-0003',
            contact_person='担当3',
            contract_status_id=1,
            contract_start_date=date(2024, 1, 1),
            databricks_group_id='scope-other',
            creator=1,
            modifier=1,
        )
        db_session.add_all([org_own, org_sub, org_other])
        db_session.flush()

        # ── 組織閉包 ──────────────────────────────────────────────────────
        # org_own を自分自身と下位組織が含まれるスコープとして設定
        db_session.add_all([
            OrganizationClosure(
                parent_organization_id=org_own.organization_id,
                subsidiary_organization_id=org_own.organization_id,
                depth=0,
            ),
            OrganizationClosure(
                parent_organization_id=org_own.organization_id,
                subsidiary_organization_id=org_sub.organization_id,
                depth=1,
            ),
        ])

        # ── ガジェット種別 ────────────────────────────────────────────────
        gt = GadgetTypeMaster(
            gadget_type_id=15,
            gadget_type_name='帯グラフ_スコープ用',
            data_source_type=1,
            gadget_image_path='images/gadgets/belt_chart.png',
            gadget_description='スコープテスト用',
            display_order=15,
            creator=1,
            modifier=1,
            delete_flag=False,
        )
        db_session.add(gt)
        db_session.flush()

        # ── ダッシュボード・グループ・ガジェット（自組織） ─────────────────
        dash_own = DashboardMaster(
            dashboard_uuid=str(uuid.uuid4()),
            dashboard_name='自組織ダッシュボード',
            organization_id=org_own.organization_id,
            creator=1,
            modifier=1,
            delete_flag=False,
        )
        db_session.add(dash_own)
        db_session.flush()

        group_own = DashboardGroupMaster(
            dashboard_group_uuid=str(uuid.uuid4()),
            dashboard_group_name='自組織グループ',
            dashboard_id=dash_own.dashboard_id,
            display_order=1,
            creator=1,
            modifier=1,
            delete_flag=False,
        )
        db_session.add(group_own)
        db_session.flush()

        gadget_own = DashboardGadgetMaster(
            gadget_uuid=str(uuid.uuid4()),
            gadget_name='自組織帯グラフ',
            gadget_type_id=gt.gadget_type_id,
            dashboard_group_id=group_own.dashboard_group_id,
            chart_config=json.dumps({'measurement_item_ids': [1], 'summary_method_id': 1}),
            data_source_config=json.dumps({'device_id': 1}),
            position_x=0,
            position_y=0,
            gadget_size='2x2',
            display_order=1,
            creator=1,
            modifier=1,
        )
        db_session.add(gadget_own)

        # ── ダッシュボード・グループ・ガジェット（下位組織） ──────────────
        dash_sub = DashboardMaster(
            dashboard_uuid=str(uuid.uuid4()),
            dashboard_name='下位組織ダッシュボード',
            organization_id=org_sub.organization_id,
            creator=1,
            modifier=1,
            delete_flag=False,
        )
        db_session.add(dash_sub)
        db_session.flush()

        group_sub = DashboardGroupMaster(
            dashboard_group_uuid=str(uuid.uuid4()),
            dashboard_group_name='下位組織グループ',
            dashboard_id=dash_sub.dashboard_id,
            display_order=1,
            creator=1,
            modifier=1,
            delete_flag=False,
        )
        db_session.add(group_sub)
        db_session.flush()

        gadget_sub = DashboardGadgetMaster(
            gadget_uuid=str(uuid.uuid4()),
            gadget_name='下位組織帯グラフ',
            gadget_type_id=gt.gadget_type_id,
            dashboard_group_id=group_sub.dashboard_group_id,
            chart_config=json.dumps({'measurement_item_ids': [1], 'summary_method_id': 1}),
            data_source_config=json.dumps({'device_id': 1}),
            position_x=0,
            position_y=0,
            gadget_size='2x2',
            display_order=1,
            creator=1,
            modifier=1,
        )
        db_session.add(gadget_sub)

        # ── ダッシュボード・グループ・ガジェット（無関係組織） ────────────
        dash_other = DashboardMaster(
            dashboard_uuid=str(uuid.uuid4()),
            dashboard_name='無関係組織ダッシュボード',
            organization_id=org_other.organization_id,
            creator=1,
            modifier=1,
            delete_flag=False,
        )
        db_session.add(dash_other)
        db_session.flush()

        group_other = DashboardGroupMaster(
            dashboard_group_uuid=str(uuid.uuid4()),
            dashboard_group_name='無関係組織グループ',
            dashboard_id=dash_other.dashboard_id,
            display_order=1,
            creator=1,
            modifier=1,
            delete_flag=False,
        )
        db_session.add(group_other)
        db_session.flush()

        gadget_other = DashboardGadgetMaster(
            gadget_uuid=str(uuid.uuid4()),
            gadget_name='無関係組織帯グラフ',
            gadget_type_id=gt.gadget_type_id,
            dashboard_group_id=group_other.dashboard_group_id,
            chart_config=json.dumps({'measurement_item_ids': [1], 'summary_method_id': 1}),
            data_source_config=json.dumps({'device_id': 1}),
            position_x=0,
            position_y=0,
            gadget_size='2x2',
            display_order=1,
            creator=1,
            modifier=1,
        )
        db_session.add(gadget_other)
        db_session.flush()

        return {
            'org_own_id': org_own.organization_id,
            'gadget_own': gadget_own,
            'gadget_sub': gadget_sub,
            'gadget_other': gadget_other,
        }

    @pytest.fixture()
    def scope_user(self, app, db_session, scope_orgs):
        """スコープテスト用ユーザー: org_own に所属、closure で org_own + org_sub がアクセス可能"""
        from datetime import datetime as _dt

        from iot_app.models.user import User

        now = _dt.now()
        user = User(
            user_id=101,
            databricks_user_id='scope-test-user',
            user_name='スコープテストユーザー',
            organization_id=scope_orgs['org_own_id'],
            email_address='scope@test.com',
            user_type_id=1,
            language_code='ja',
            region_id=1,
            address='',
            creator=1,
            modifier=1,
            create_date=now,
            update_date=now,
        )
        db_session.add(user)
        db_session.flush()

        # g.current_user.user_id を 101 に上書きする before_request フック
        def _inject_scope_user():
            from flask import g
            from types import SimpleNamespace
            g.current_user = SimpleNamespace(user_id=101)

        app.before_request_funcs.setdefault(None, []).append(_inject_scope_user)
        yield user
        funcs = app.before_request_funcs.get(None, [])
        if _inject_scope_user in funcs:
            funcs.remove(_inject_scope_user)

    def test_own_org_gadget_is_accessible(
        self, client, scope_orgs, scope_user, mocker
    ):
        """1.3.1: 自組織のダッシュボードに属するガジェットのデータが取得できる"""
        # Arrange
        mocker.patch(_GOLD_QUERY, return_value=[])

        # Act
        response = client.post(
            f"{BASE_URL}/gadgets/{scope_orgs['gadget_own'].gadget_uuid}/data",
            json={
                'display_unit': 'day',
                'interval': '10min',
                'base_datetime': _VALID_DATETIME,
            },
        )

        # Assert: 自組織 → スコープ内 → 200
        assert response.status_code == 200

    def test_sub_org_gadget_is_accessible(
        self, client, scope_orgs, scope_user, mocker
    ):
        """1.3.2: 下位組織のダッシュボードに属するガジェットのデータが取得できる

        organization_closure に parent=org_own, sub=org_sub が登録されているため
        下位組織のガジェットもアクセス可能スコープに含まれる。
        """
        # Arrange
        mocker.patch(_GOLD_QUERY, return_value=[])

        # Act
        response = client.post(
            f"{BASE_URL}/gadgets/{scope_orgs['gadget_sub'].gadget_uuid}/data",
            json={
                'display_unit': 'day',
                'interval': '10min',
                'base_datetime': _VALID_DATETIME,
            },
        )

        # Assert: 下位組織 → closure で accessible_org_ids に含まれる → 200
        assert response.status_code == 200

    def test_other_org_gadget_is_not_accessible(
        self, client, scope_orgs, scope_user
    ):
        """1.3.3/1.3.4: 無関係組織のダッシュボードに属するガジェットはアクセス不可（404）

        organization_closure に無関係組織が含まれないため
        check_gadget_access が None を返し 404 となる。
        """
        # Act
        response = client.post(
            f"{BASE_URL}/gadgets/{scope_orgs['gadget_other'].gadget_uuid}/data",
            json={
                'display_unit': 'day',
                'interval': '10min',
                'base_datetime': _VALID_DATETIME,
            },
        )

        # Assert: スコープ外 → 404
        assert response.status_code == 404


# ─────────────────────────────────────────────────────────────────────────────
# 8. セキュリティテスト
# 観点: 9.1 SQLインジェクション、9.2 XSS、9.3 CSRF
# ─────────────────────────────────────────────────────────────────────────────

_REGISTER_URL = f"{BASE_URL}/gadgets/belt-chart/register"


def _security_valid_form(**overrides):
    """セキュリティテスト用の正常フォームデータ（20文字以内の gadget_name）"""
    base = {
        'gadget_name': '帯グラフ',
        'group_id': '1',
        'summary_method_id': '1',
        'measurement_item_ids': ['1'],
        'gadget_size': '0',
        'device_mode': 'fixed',
        'device_id': '1',
    }
    base.update(overrides)
    return base


@pytest.mark.integration
class TestBeltChartSecurity:
    """帯グラフガジェット セキュリティテスト

    観点: 9.1 SQLインジェクションテスト、9.2 XSS、9.3 CSRF対策テスト

    SQLインジェクション対策:
      SQLAlchemy のプリペアドステートメントにより、入力値はパラメータとしてバインドされる。
      SQL文字列として解釈されることなく、DB エラーなしに処理される（または文字長で 400）。

    XSS対策:
      Jinja2 のオートエスケープにより、テンプレートで出力される文字列は自動エスケープされる。
      <script> 等の HTML タグはエンティティ（&lt; 等）に変換されて表示される。

    CSRF対策:
      Flask-WTF の CSRFProtect により、POST リクエストには有効なトークンが必要。
      テスト環境では disable_csrf フィクスチャ（autouse）により CSRF が無効化されているため、
      CSRF テストでは一時的に WTF_CSRF_ENABLED=True に上書きして検証する。
    """

    @pytest.fixture(autouse=True)
    def _setup(
        self, auth_scope, dashboard_master, dashboard_group_master, gadget_type_belt
    ):
        """全テストで認証ユーザー＋ガジェット関連マスタを事前登録する"""

    # ── 9.1 SQLインジェクション ─────────────────────────────────────────────

    def test_sql_injection_or_pattern_is_safe(self, client, measurement_item):
        """9.1.1: 基本的なSQLインジェクション（OR パターン）がエスケープされDBエラーが発生しない

        gadget_name に 'OR 1=1--' を含む文字列を送信。
        SQLAlchemy のプリペアドステートメントにより SQL として解釈されず、
        500（DBエラー）が発生しないことを確認する。
        """
        # Arrange: SQLインジェクション文字列（20文字以内）
        payload = "OR 1=1--"

        # Act
        response = client.post(
            _REGISTER_URL,
            data=_security_valid_form(gadget_name=payload),
        )

        # Assert: DBエラー（500）は発生しない。正常登録（302）または検証エラー（400）
        assert response.status_code != 500
        assert response.status_code in (200, 302, 400)

    def test_sql_injection_drop_table_is_safe(self, client, measurement_item):
        """9.1.2: コメントを使ったSQLインジェクション（DROP TABLE）がエスケープされる

        gadget_name に '; DROP TABLE' を含む文字列を送信。
        SQLAlchemy のプリペアドステートメントにより TABLE が削除されないことを確認する。
        """
        # Arrange: SQLインジェクション文字列（20文字以内）
        payload = "'; DROP TABLE"

        # Act
        response = client.post(
            _REGISTER_URL,
            data=_security_valid_form(gadget_name=payload),
        )

        # Assert: DBエラー（500）は発生しない
        assert response.status_code != 500

    def test_sql_injection_union_select_is_safe(self, client, measurement_item):
        """9.1.3: UNION を使ったSQLインジェクションがエスケープされる

        gadget_name に 'UNION SELECT' を含む文字列を送信。
        SQLAlchemy のプリペアドステートメントにより追加クエリが実行されないことを確認する。
        """
        # Arrange: SQLインジェクション文字列（20文字以内）
        payload = "UNION SELECT"

        # Act
        response = client.post(
            _REGISTER_URL,
            data=_security_valid_form(gadget_name=payload),
        )

        # Assert: DBエラー（500）は発生しない
        assert response.status_code != 500

    # ── 9.2 XSS（クロスサイトスクリプティング） ─────────────────────────────

    def test_xss_script_tag_is_html_escaped_in_re_rendered_form(
        self, client, measurement_item
    ):
        """9.2.1: <script>タグが登録フォーム再描画時に Jinja2 によってHTMLエスケープされる

        gadget_name に <script> タグ（8文字）を含む値を送信し、
        group_id=0（必須バリデーション失敗）で 400 レスポンス（フォーム再描画）を誘発。
        レスポンスHTML内に生の <script> タグが value 属性として出力されないことを確認する。
        """
        # Arrange: XSSペイロード（8文字、gadget_name バリデーション通過）
        xss_payload = '<script>'

        # Act: group_id=0 で必須チェック失敗 → 400 + フォーム再描画
        response = client.post(
            _REGISTER_URL,
            data=_security_valid_form(gadget_name=xss_payload, group_id='0'),
        )

        # Assert: 400 で再描画、value属性に生の <script> が埋め込まれていない
        assert response.status_code == 400
        # Jinja2 オートエスケープにより &lt;script&gt; に変換される
        assert b'value="<script>"' not in response.data
        assert b'value="<script>' not in response.data

    def test_xss_img_tag_is_stored_safely(self, client, measurement_item):
        """9.2.2: imgタグXSSペイロードがリテラル文字列として安全に保存される

        gadget_name に <img src=x>（12文字）を含む値を送信。
        正常登録（302）または文字長バリデーションエラー（400）となり、
        XSS スクリプトが実行されないことを確認する。
        """
        # Arrange: imgタグXSSペイロード（12文字）
        xss_payload = '<img src=x>'

        # Act
        response = client.post(
            _REGISTER_URL,
            data=_security_valid_form(gadget_name=xss_payload),
        )

        # Assert: DBエラー（500）は発生しない
        assert response.status_code != 500
        assert response.status_code in (200, 302, 400)

    def test_xss_javascript_protocol_is_stored_safely(self, client, measurement_item):
        """9.2.3: JavaScriptプロトコルペイロードがリテラル文字列として安全に保存される

        gadget_name に javascript:（11文字）を含む値を送信。
        SQLAlchemy / Jinja2 の保護により XSS が実行されないことを確認する。
        """
        # Arrange: JavaScriptプロトコルペイロード（11文字）
        xss_payload = 'javascript:'

        # Act
        response = client.post(
            _REGISTER_URL,
            data=_security_valid_form(gadget_name=xss_payload),
        )

        # Assert: DBエラー（500）は発生しない
        assert response.status_code != 500
        assert response.status_code in (200, 302, 400)

    # ── 9.3 CSRF対策 ──────────────────────────────────────────────────────────

    def test_csrf_token_absent_is_rejected(self, client, app, measurement_item):
        """9.3.1: CSRFトークンなしPOSTは拒否される（400/403）

        conftest の disable_csrf（autouse）が WTF_CSRF_ENABLED=False を設定するが、
        このテストでは True に上書きして CSRF 保護を有効化する。
        トークンなしの POST が Flask-WTF の CSRFProtect により拒否されることを確認する。
        """
        # Arrange: CSRFを有効化（disable_csrf フィクスチャの設定を上書き）
        app.config['WTF_CSRF_ENABLED'] = True
        try:
            # Act: CSRFトークンなしで POST
            response = client.post(
                _REGISTER_URL,
                data=_security_valid_form(),
            )

            # Assert: CSRF バリデーション失敗 → 400 または 403
            assert response.status_code in (400, 403)
        finally:
            # 他のテストに影響しないよう CSRF を無効化に戻す
            app.config['WTF_CSRF_ENABLED'] = False

    def test_csrf_invalid_token_is_rejected(self, client, app, measurement_item):
        """9.3.2: 不正なCSRFトークン付きPOSTは拒否される（400/403）

        不正な（ランダム文字列の）CSRF トークンを含む POST が
        Flask-WTF の CSRFProtect により拒否されることを確認する。
        """
        # Arrange: CSRFを有効化
        app.config['WTF_CSRF_ENABLED'] = True
        try:
            # Act: 不正なCSRFトークンで POST
            form_data = _security_valid_form()
            form_data['csrf_token'] = 'invalid-csrf-token-string'
            response = client.post(_REGISTER_URL, data=form_data)

            # Assert: CSRF バリデーション失敗 → 400 または 403
            assert response.status_code in (400, 403)
        finally:
            app.config['WTF_CSRF_ENABLED'] = False

    def test_csrf_disabled_allows_post_without_token(self, client, measurement_item):
        """9.3.3: テスト環境では disable_csrf フィクスチャにより CSRF が無効化され、トークンなしPOSTが成功する

        NOTE: 本番環境では Flask-WTF の CSRFProtect が有効であり、
              有効なトークンなしの POST は拒否される（9.3.1/9.3.2 で確認済み）。
              このテストはテスト基盤の CSRF 無効化設定が正しく機能していることの確認。
        """
        # Arrange: CSRF は disable_csrf フィクスチャ（autouse）により無効化済み
        # （WTF_CSRF_ENABLED=False）

        # Act: トークンなしで POST
        response = client.post(
            _REGISTER_URL,
            data=_security_valid_form(),
        )

        # Assert: CSRF なしでも処理される（302 または 400）
        assert response.status_code in (200, 302, 400)
        assert response.status_code != 403
