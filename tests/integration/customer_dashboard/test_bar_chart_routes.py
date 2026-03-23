"""
顧客作成ダッシュボード 棒グラフガジェット - 結合テスト

対象エンドポイント:
  GET  /analysis/customer-dashboard
  POST /analysis/customer-dashboard/gadgets/<gadget_uuid>/data
  GET  /analysis/customer-dashboard/gadgets/bar-chart/create
  POST /analysis/customer-dashboard/gadgets/bar-chart/register
  GET  /analysis/customer-dashboard/gadgets/<gadget_uuid>?export=csv

参照設計書:
  - docs/03-features/flask-app/customer-dashboard/bar-chart/ui-specification.md
  - docs/03-features/flask-app/customer-dashboard/bar-chart/workflow-specification.md

NOTE: モデルファイル（models/dashboard.py 等）が実装済みであることが前提。
      外部API（Unity Catalog）のみモック化する。認証ミドルウェアはこのブランチでは未実装のため対象外。
"""

import json
import uuid

import pytest
from bs4 import BeautifulSoup

BASE_URL = "/analysis/customer-dashboard"
_VALID_DATETIME = "2026/03/06 12:00:00"

# Unity Catalog クエリのモック対象パス
_SILVER_QUERY = "iot_app.services.customer_dashboard.bar_chart.execute_silver_query"
_GOLD_QUERY   = "iot_app.services.customer_dashboard.bar_chart.execute_gold_query"


def _soup(response) -> BeautifulSoup:
    """FlaskレスポンスからBeautifulSoupオブジェクトを生成するヘルパー"""
    return BeautifulSoup(response.data, 'html.parser')


# ─────────────────────────────────────────────────────────────────────────────
# 1. 顧客作成ダッシュボード初期表示
# GET /analysis/customer-dashboard
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.integration
class TestCustomerDashboardIndex:
    """顧客作成ダッシュボード初期表示

    観点: 2.1.1 一覧初期表示、4.1 一覧表示
    """

    def test_index_returns_200(self, client):
        """2.1.1: ガジェット0件でも200とHTMLを返す"""
        # Arrange: DBにガジェットなし（初期状態）

        # Act
        response = client.get(BASE_URL)

        # Assert
        assert response.status_code == 200
        assert b"customer-dashboard" in response.data

    def test_index_renders_registered_gadget(self, client, gadget):
        """4.1.2: 登録済みガジェットが data-gadget-uuid 属性付きの div として描画される"""
        # Arrange: gadget フィクスチャで DashboardGadgetMaster に1件登録済み

        # Act
        response = client.get(BASE_URL)
        soup = _soup(response)

        # Assert: DOM上に data-gadget-uuid 属性を持つ要素が存在する
        assert response.status_code == 200
        gadget_el = soup.find(attrs={'data-gadget-uuid': gadget.gadget_uuid})
        assert gadget_el is not None

    def test_index_renders_gadget_title(self, client, gadget):
        """4.1.3: ガジェットタイトルが gadget__title クラス要素に描画される"""
        # Act
        response = client.get(BASE_URL)
        soup = _soup(response)

        # Assert
        title_el = soup.find(class_='gadget__title')
        assert title_el is not None
        assert gadget.gadget_name in title_el.get_text()

    def test_index_renders_csv_export_button(self, client, gadget):
        """4.1.4: CSVエクスポートボタンが data-gadget-uuid 付きで描画される"""
        # Act
        response = client.get(BASE_URL)
        soup = _soup(response)

        # Assert
        csv_btn = soup.find('button', {'data-gadget-uuid': gadget.gadget_uuid})
        assert csv_btn is not None

    def test_index_does_not_render_deleted_gadget(self, client, gadget, db_session):
        """4.1.5: delete_flag=True のガジェットは DOM に存在しない"""
        # Arrange: ガジェットを論理削除
        gadget.delete_flag = True
        db_session.flush()

        # Act
        response = client.get(BASE_URL)
        soup = _soup(response)

        # Assert
        assert soup.find(attrs={'data-gadget-uuid': gadget.gadget_uuid}) is None


# ─────────────────────────────────────────────────────────────────────────────
# 2. ガジェットデータ取得（AJAX）
# POST /analysis/customer-dashboard/gadgets/<gadget_uuid>/data
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.integration
class TestGadgetBarChartData:
    """棒グラフガジェット データ取得（AJAX）

    観点: 4.2 詳細表示、3.4 日付形式チェック、3.6 不整値チェック、2.2 エラー時遷移
    """

    def _url(self, gadget_uuid):
        return f"{BASE_URL}/gadgets/{gadget_uuid}/data"

    def test_data_returns_json_structure(self, client, gadget, mocker):
        """4.2.1: 正常取得 - gadget_uuid / chart_data / updated_at を含む JSON を返す"""
        # Arrange: ゴールド層クエリをモック（外部API）
        mocker.patch(_GOLD_QUERY, return_value=[
            {'collection_hour': 10, 'summary_value': 25.5},
            {'collection_hour': 11, 'summary_value': 26.0},
        ])

        # Act
        response = client.post(
            self._url(gadget.gadget_uuid),
            json={
                'display_unit': 'day',
                'interval': '10min',
                'base_datetime': _VALID_DATETIME,
            },
        )

        # Assert: JSONレスポンスの構造を検証
        assert response.status_code == 200
        body = response.get_json()
        assert body['gadget_uuid'] == gadget.gadget_uuid
        assert 'chart_data' in body
        assert 'labels' in body['chart_data']
        assert 'values' in body['chart_data']
        assert 'updated_at' in body

    def test_data_chart_values_match_mocked_rows(self, client, gadget, mocker):
        """4.2.2: ゴールド層の行データが chart_data.labels / values に正しく変換される"""
        # Arrange
        mocker.patch(_GOLD_QUERY, return_value=[
            {'collection_hour': 8,  'summary_value': 20.0},
            {'collection_hour': 9,  'summary_value': 21.5},
        ])

        # Act
        response = client.post(
            self._url(gadget.gadget_uuid),
            json={'display_unit': 'day', 'interval': '10min', 'base_datetime': _VALID_DATETIME},
        )

        # Assert: ラベルと値が正しく変換されているか
        body = response.get_json()
        assert body['chart_data']['labels'] == ['08:00', '09:00']
        assert body['chart_data']['values'] == [20.0, 21.5]

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

    def test_data_invalid_display_unit_returns_400(self, client, gadget):
        """3.6.1: display_unit が hour/day/week/month 以外で400エラー"""
        # Act
        response = client.post(
            self._url(gadget.gadget_uuid),
            json={'display_unit': 'hourly', 'interval': '10min', 'base_datetime': _VALID_DATETIME},
        )

        # Assert
        assert response.status_code == 400
        assert response.get_json()['error'] == 'パラメータが不正です'

    def test_data_invalid_interval_returns_400(self, client, gadget):
        """3.6.2: interval が 1/2/3/5/10/15min 以外で400エラー"""
        # Act
        response = client.post(
            self._url(gadget.gadget_uuid),
            json={'display_unit': 'day', 'interval': '4min', 'base_datetime': _VALID_DATETIME},
        )

        # Assert
        assert response.status_code == 400

    def test_data_invalid_datetime_format_returns_400(self, client, gadget):
        """3.4.1: base_datetime が YYYY/MM/DD HH:mm:ss 以外の形式で400エラー"""
        # Act
        response = client.post(
            self._url(gadget.gadget_uuid),
            json={'display_unit': 'day', 'interval': '10min', 'base_datetime': '2026-03-06T12:00:00'},
        )

        # Assert
        assert response.status_code == 400

    def test_data_missing_base_datetime_returns_400(self, client, gadget):
        """3.1.1: base_datetime 未指定で400エラー"""
        # Act
        response = client.post(
            self._url(gadget.gadget_uuid),
            json={'display_unit': 'day', 'interval': '10min'},
        )

        # Assert
        assert response.status_code == 400

    def test_data_unity_catalog_error_returns_500(self, client, gadget, mocker):
        """2.2.6: Unity Catalog クエリ失敗時に500エラー"""
        # Arrange: 外部API呼び出しが例外を送出
        mocker.patch(_GOLD_QUERY, side_effect=Exception("Databricks connection timeout"))

        # Act
        response = client.post(
            self._url(gadget.gadget_uuid),
            json={'display_unit': 'day', 'interval': '10min', 'base_datetime': _VALID_DATETIME},
        )

        # Assert
        assert response.status_code == 500

    def test_data_deleted_gadget_returns_404(self, client, gadget, db_session, mocker):
        """4.2.3: delete_flag=True の論理削除済みガジェットへのデータ取得リクエストは404"""
        # Arrange: ガジェットを論理削除
        gadget.delete_flag = True
        db_session.flush()

        # Act
        response = client.post(
            self._url(gadget.gadget_uuid),
            json={'display_unit': 'day', 'interval': '10min', 'base_datetime': _VALID_DATETIME},
        )

        # Assert: get_gadget_by_uuid が delete_flag=False のみ返すため404
        assert response.status_code == 404

    def test_data_hour_unit_uses_silver_query_with_column_name(self, client, gadget, measurement_item, mocker):
        """4.2.5: display_unit=hour 時、MeasurementItemMaster から取得した column_name でシルバー層クエリが呼ばれる"""
        # Arrange: シルバー層クエリをモック（外部API）
        mock_silver = mocker.patch(_SILVER_QUERY, return_value=[])

        # Act: display_unit=hour を指定（measurement_item フィクスチャで id=1, column_name='external_temp' 登録済み）
        response = client.post(
            self._url(gadget.gadget_uuid),
            json={'display_unit': 'hour', 'interval': '10min', 'base_datetime': _VALID_DATETIME},
        )

        # Assert: シルバー層クエリが呼ばれている（column_name は format_bar_chart_data 内で使用）
        assert response.status_code == 200
        assert mock_silver.called


# ─────────────────────────────────────────────────────────────────────────────
# 3. ガジェット登録モーダル表示
# GET /analysis/customer-dashboard/gadgets/bar-chart/create
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.integration
class TestGadgetBarChartCreate:
    """棒グラフガジェット 登録モーダル表示

    観点: 2.1.3 登録画面表示、2.2 エラー時遷移
    """

    _URL = f"{BASE_URL}/gadgets/bar-chart/create"

    def test_create_modal_returns_200(
        self, client, auth_user_id, dashboard_user_setting, dashboard_master, dashboard_group_master
    ):
        """2.1.3: 正常表示 - 200とHTMLを返す"""
        # Act
        response = client.get(self._URL)

        # Assert
        assert response.status_code == 200

    def test_create_modal_has_title_input(
        self, client, auth_user_id, dashboard_user_setting, dashboard_master, dashboard_group_master
    ):
        """2.1.3: タイトル入力フィールド（input[name="title"]）が存在する"""
        # Act
        response = client.get(self._URL)
        soup = _soup(response)

        # Assert
        assert soup.find('input', {'name': 'title'}) is not None

    def test_create_modal_has_device_mode_radio(
        self, client, auth_user_id, dashboard_user_setting, dashboard_master, dashboard_group_master
    ):
        """2.1.3: 表示デバイス選択ボタン（data-mode="fixed/variable"）が存在する"""
        # Act
        response = client.get(self._URL)
        soup = _soup(response)

        # Assert: 実装はボタン＋hidden input方式（data-mode属性で fixed/variable を切り替え）
        mode_buttons = soup.find_all('button', {'data-mode': True})
        modes = {btn['data-mode'] for btn in mode_buttons}
        assert 'fixed' in modes
        assert 'variable' in modes

    def test_create_modal_has_gadget_size_select(
        self, client, auth_user_id, dashboard_user_setting, dashboard_master, dashboard_group_master
    ):
        """2.1.3: 部品サイズ選択（select[name="gadget_size"]）に 2x2・2x4 の選択肢がある"""
        # Act
        response = client.get(self._URL)
        soup = _soup(response)

        # Assert
        select = soup.find('select', {'name': 'gadget_size'})
        assert select is not None
        option_values = {opt['value'] for opt in select.find_all('option') if opt.get('value')}
        assert '2x2' in option_values
        assert '2x4' in option_values

    def test_create_modal_lists_measurement_items(
        self, client, auth_user_id, dashboard_user_setting, dashboard_master, dashboard_group_master,
        measurement_item,
    ):
        """2.1.3: measurement_item_master の表示項目がラジオボタンとして描画される"""
        # Arrange: measurement_item フィクスチャで '外気温度'（id=1）を登録済み

        # Act
        response = client.get(self._URL)
        soup = _soup(response)

        # Assert: 実装はラジオボタンのテーブル方式
        # name="measurement_item_id" の radio input が存在し、対応するラベルに '外気温度' が含まれる
        radio = soup.find('input', {
            'name': 'measurement_item_id',
            'type': 'radio',
            'value': str(measurement_item.measurement_item_id),
        })
        assert radio is not None
        label = soup.find('label', {'for': radio['id']})
        assert label is not None
        assert '外気温度' in label.get_text()


# ─────────────────────────────────────────────────────────────────────────────
# 4. ガジェット登録実行
# POST /analysis/customer-dashboard/gadgets/bar-chart/register
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.integration
class TestGadgetBarChartRegister:
    """棒グラフガジェット 登録実行

    観点: 3.1 必須チェック、3.2 文字列長チェック、3.8 相関チェック、4.3 登録、2.3 リダイレクト
    """

    _URL = f"{BASE_URL}/gadgets/bar-chart/register"

    _SKIP_GADGET_TYPE = frozenset({
        'test_register_without_gadget_type_master_returns_error',
        'test_register_with_deleted_gadget_type_master_returns_error',
        'test_register_gadget_type_id_matches_gadget_type_master',  # 独自の gadget_type fixture を使用
    })

    @pytest.fixture(autouse=True)
    def _require_gadget_type(self, request, db_session):
        """全テストで GadgetTypeMaster='棒グラフ' を事前登録する（サービス層の動的ルックアップに必要）。
        GadgetTypeMaster の存在チェックテストではスキップする。
        """
        if request.node.name in self._SKIP_GADGET_TYPE:
            return
        from iot_app.models.dashboard import GadgetTypeMaster
        gt = GadgetTypeMaster(gadget_type_id=1, gadget_type_name='棒グラフ', delete_flag=False)
        db_session.add(gt)
        db_session.flush()

    def _valid_form(self, **overrides):
        """デバイス可変モード・2x2 の最小有効フォームデータ"""
        data = {
            'title': 'テストガジェット',
            'device_mode': 'variable',   # 可変モード: デバイス存在チェックをスキップ
            'device_id': '0',
            'group_id': '1',
            'summary_method_id': '1',
            'measurement_item_id': '1',
            'gadget_size': '2x2',
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
        """4.3.2: 正常登録後、dashboard_gadget_master に1件レコードが追加される"""
        # Arrange
        from iot_app.models.dashboard import DashboardGadgetMaster

        # Act
        client.post(self._URL, data=self._valid_form())

        # Assert: リクエスト後に DB を直接クエリして検証
        with app.app_context():
            from iot_app import db
            count = db.session.query(DashboardGadgetMaster).filter_by(delete_flag=False).count()
        assert count == 1

    def test_register_gadget_uuid_is_set(self, client, app, measurement_item):
        """4.3.3: 登録されたガジェットに gadget_uuid が自動採番される"""
        # Act
        client.post(self._URL, data=self._valid_form())

        # Assert
        with app.app_context():
            from iot_app import db
            from iot_app.models.dashboard import DashboardGadgetMaster
            gadget = db.session.query(DashboardGadgetMaster).first()
        assert gadget is not None
        assert len(gadget.gadget_uuid) == 36  # UUID形式

    def test_register_title_stored_correctly(self, client, app, measurement_item):
        """4.3.4: 登録されたガジェットのタイトルがDBに正しく保存される"""
        # Act
        client.post(self._URL, data=self._valid_form(title='棒グラフテスト'))

        # Assert
        with app.app_context():
            from iot_app import db
            from iot_app.models.dashboard import DashboardGadgetMaster
            gadget = db.session.query(DashboardGadgetMaster).first()
        assert gadget.gadget_name == '棒グラフテスト'

    def test_register_gadget_size_stored_correctly(self, client, app, measurement_item):
        """4.3.5: 部品サイズ 2x4 がDBに保存される"""
        # Act
        client.post(self._URL, data=self._valid_form(gadget_size='2x4'))

        # Assert
        with app.app_context():
            from iot_app import db
            from iot_app.models.dashboard import DashboardGadgetMaster
            gadget = db.session.query(DashboardGadgetMaster).first()
        assert gadget.gadget_size == '2x4'

    def test_register_title_required_returns_422(self, client, measurement_item):
        """3.1.1: タイトル未入力で400（バリデーションエラー）"""
        # Act
        response = client.post(self._URL, data=self._valid_form(title=''))

        # Assert
        assert response.status_code == 400

    def test_register_title_20_chars_succeeds(self, client, measurement_item):
        """3.2.1: タイトル20文字は登録成功"""
        # Act
        response = client.post(self._URL, data=self._valid_form(title='あ' * 20), follow_redirects=False)

        # Assert
        assert response.status_code == 302

    def test_register_title_21_chars_returns_422(self, client, measurement_item):
        """3.2.2: タイトル21文字以上で400"""
        # Act
        response = client.post(self._URL, data=self._valid_form(title='あ' * 21))

        # Assert
        assert response.status_code == 400

    def test_register_device_id_required_in_fixed_mode(self, client, measurement_item):
        """3.1.2: device_mode=fixed でデバイスID未指定（0）は404（ビュー層でデバイス不在チェック）"""
        # Act
        response = client.post(self._URL, data=self._valid_form(device_mode='fixed', device_id='0'))

        # Assert
        assert response.status_code == 404

    def test_register_group_required_returns_422(self, client, measurement_item):
        """3.1.3: グループ未選択（0）で400"""
        # Act
        response = client.post(self._URL, data=self._valid_form(group_id='0'))

        # Assert
        assert response.status_code == 400

    def test_register_summary_method_required_returns_422(self, client, measurement_item):
        """3.1.4: 集約方法未選択（0）で400"""
        # Act
        response = client.post(self._URL, data=self._valid_form(summary_method_id='0'))

        # Assert
        assert response.status_code == 400

    def test_register_measurement_item_required_returns_422(self, client, measurement_item):
        """3.1.5: 表示項目未選択（0）で400"""
        # Act
        response = client.post(self._URL, data=self._valid_form(measurement_item_id='0'))

        # Assert
        assert response.status_code == 400

    def test_register_gadget_size_required_returns_422(self, client, measurement_item):
        """3.1.6: 部品サイズ未選択で400"""
        # Act
        response = client.post(self._URL, data=self._valid_form(gadget_size=''))

        # Assert
        assert response.status_code == 400

    def test_register_min_greater_than_max_returns_422(self, client, measurement_item):
        """3.8.1: 最小値 > 最大値で400"""
        # Act
        response = client.post(self._URL, data=self._valid_form(min_value='10.0', max_value='5.0'))

        # Assert
        assert response.status_code == 400

    def test_register_min_equals_max_returns_422(self, client, measurement_item):
        """3.8.2: 最小値 = 最大値で400"""
        # Act
        response = client.post(self._URL, data=self._valid_form(min_value='5.0', max_value='5.0'))

        # Assert
        assert response.status_code == 400

    def test_register_valid_min_max_succeeds(self, client, measurement_item):
        """3.8.3: 最小値 < 最大値で登録成功"""
        # Act
        response = client.post(
            self._URL,
            data=self._valid_form(min_value='-10.0', max_value='30.0'),
            follow_redirects=False,
        )

        # Assert
        assert response.status_code == 302

    def test_register_omit_min_max_succeeds(self, client, measurement_item):
        """3.8.4: 最小値・最大値ともに省略可（任意項目）"""
        # Act
        response = client.post(self._URL, data=self._valid_form(), follow_redirects=False)

        # Assert
        assert response.status_code == 302

    def test_register_success_redirects_to_dashboard_page(self, client, app, measurement_item):
        """4.3.1: 登録成功後にダッシュボード画面（/analysis/customer-dashboard）へリダイレクトされる"""
        # Act: リダイレクトを追跡してダッシュボード画面を取得
        response = client.post(self._URL, data=self._valid_form(), follow_redirects=True)

        # Assert: 最終的にダッシュボード画面（200）が表示される
        assert response.status_code == 200
        assert b"customer-dashboard" in response.data
        # TODO: 設計書に成功メッセージモーダルの記載なし、要確認

    def test_register_default_position_x_is_zero(self, client, app, measurement_item):
        """4.3.2: position_x のデフォルト値が 0 で登録される"""
        # Act
        client.post(self._URL, data=self._valid_form())

        # Assert
        with app.app_context():
            from iot_app import db
            from iot_app.models.dashboard import DashboardGadgetMaster
            gadget = db.session.query(DashboardGadgetMaster).first()
        assert gadget.position_x == 0

    def test_register_default_display_order_is_one(self, client, app, measurement_item):
        """4.3.2: display_order のデフォルト値が 1（グループ内初登録時）で登録される"""
        # Act
        client.post(self._URL, data=self._valid_form())

        # Assert
        with app.app_context():
            from iot_app import db
            from iot_app.models.dashboard import DashboardGadgetMaster
            gadget = db.session.query(DashboardGadgetMaster).first()
        assert gadget.display_order == 1

    def test_register_position_y_is_one_for_first_gadget(self, client, app, measurement_item):
        """4.3.2: グループ内初登録時、position_y は 1（max(0) + 1）で登録される"""
        # Act
        client.post(self._URL, data=self._valid_form())

        # Assert
        with app.app_context():
            from iot_app import db
            from iot_app.models.dashboard import DashboardGadgetMaster
            gadget = db.session.query(DashboardGadgetMaster).first()
        assert gadget.position_y == 1

    def test_register_position_y_increments_for_second_gadget(self, client, app, measurement_item):
        """4.3.2: 同グループに2件目登録時、position_y は既存最大値 + 1（= 2）で登録される"""
        # Arrange: 1件目を登録（group_id=1, position_y=1 になる）
        client.post(self._URL, data=self._valid_form(title='1件目'))

        # Act: 2件目を同グループに登録
        client.post(self._URL, data=self._valid_form(title='2件目'))

        # Assert: 2件目の position_y == 2
        with app.app_context():
            from iot_app import db
            from iot_app.models.dashboard import DashboardGadgetMaster
            gadgets = db.session.query(DashboardGadgetMaster).order_by(
                DashboardGadgetMaster.position_y.asc()
            ).all()
        assert len(gadgets) == 2
        assert gadgets[0].position_y == 1
        assert gadgets[1].position_y == 2

    def test_register_null_min_max_stored_in_chart_config(self, client, app, measurement_item):
        """4.3.4: min_value・max_value 省略時、chart_config JSON 内で null が設定される"""
        # Act: min/max を省略して登録
        client.post(self._URL, data=self._valid_form())

        # Assert
        with app.app_context():
            from iot_app import db
            from iot_app.models.dashboard import DashboardGadgetMaster
            gadget = db.session.query(DashboardGadgetMaster).first()
        chart_config = json.loads(gadget.chart_config)
        assert chart_config['min_value'] is None
        assert chart_config['max_value'] is None

    def test_register_dashboard_group_id_stored_correctly(self, client, app, measurement_item):
        """4.3.4: フォームの group_id が dashboard_group_id としてDBに保存される"""
        # Act
        client.post(self._URL, data=self._valid_form(group_id='5'))

        # Assert
        with app.app_context():
            from iot_app import db
            from iot_app.models.dashboard import DashboardGadgetMaster
            gadget = db.session.query(DashboardGadgetMaster).first()
        assert gadget.dashboard_group_id == 5

    def test_register_gadget_type_id_is_one(self, client, app, measurement_item):
        """4.3.2: gadget_type_id は棒グラフ固定値（= 1）でDBに保存される"""
        # Act
        client.post(self._URL, data=self._valid_form())

        # Assert
        with app.app_context():
            from iot_app import db
            from iot_app.models.dashboard import DashboardGadgetMaster
            gadget = db.session.query(DashboardGadgetMaster).first()
        assert gadget.gadget_type_id == 1

    def test_register_chart_config_stores_measurement_and_summary(self, client, app, measurement_item):
        """4.3.4: chart_config に measurement_item_id と summary_method_id が正しく保存される"""
        # Act
        client.post(self._URL, data=self._valid_form(measurement_item_id='1', summary_method_id='2'))

        # Assert
        with app.app_context():
            from iot_app import db
            from iot_app.models.dashboard import DashboardGadgetMaster
            gadget = db.session.query(DashboardGadgetMaster).first()
        chart_config = json.loads(gadget.chart_config)
        assert chart_config['measurement_item_id'] == 1
        assert chart_config['summary_method_id'] == 2

    def test_register_data_source_config_device_id_is_null_in_variable_mode(self, client, app, measurement_item):
        """4.3.4: device_mode=variable 時、data_source_config の device_id は null で保存される"""
        # Act
        client.post(self._URL, data=self._valid_form(device_mode='variable'))

        # Assert
        with app.app_context():
            from iot_app import db
            from iot_app.models.dashboard import DashboardGadgetMaster
            gadget = db.session.query(DashboardGadgetMaster).first()
        data_source_config = json.loads(gadget.data_source_config)
        assert data_source_config['device_id'] is None

    def test_register_delete_flag_is_false_on_creation(self, client, app, measurement_item):
        """4.3.2: 登録直後の delete_flag は False で保存される"""
        # Act
        client.post(self._URL, data=self._valid_form())

        # Assert
        with app.app_context():
            from iot_app import db
            from iot_app.models.dashboard import DashboardGadgetMaster
            gadget = db.session.query(DashboardGadgetMaster).first()
        assert gadget.delete_flag is False

    def test_register_gadget_id_is_auto_incremented(self, client, app, measurement_item):
        """4.3.5: 主キー gadget_id が整数として自動採番される"""
        # Act
        client.post(self._URL, data=self._valid_form())

        # Assert
        with app.app_context():
            from iot_app import db
            from iot_app.models.dashboard import DashboardGadgetMaster
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
            from iot_app.models.dashboard import DashboardGadgetMaster
            gadget = db.session.query(DashboardGadgetMaster).first()
        assert gadget.create_date is not None
        assert gadget.update_date is not None

    def test_register_creator_is_none_without_auth(self, client, app, measurement_item):
        """4.3.7: 認証未実装ブランチでは creator・modifier に None が設定される"""
        # NOTE: 認証実装後は current_user_id が設定されること（ログインユーザーのIDになる）を確認すること
        # Act
        client.post(self._URL, data=self._valid_form())

        # Assert
        with app.app_context():
            from iot_app import db
            from iot_app.models.dashboard import DashboardGadgetMaster
            gadget = db.session.query(DashboardGadgetMaster).first()
        assert gadget.creator is None
        assert gadget.modifier is None

    def test_register_fixed_mode_nonexistent_device_id_returns_404(
        self, client, app, measurement_item
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
        """4.3.9: device_mode=fixed、device_id はDBに存在するが accessible_org_ids=[] のためアクセス不可 → 404

        認証未実装ブランチでは get_accessible_org_ids() が常に [] を返すため、
        fixed モードのデバイスチェック（ビュー層）は必ず abort(404) になる。
        """
        # Arrange: DeviceMaster にデバイスを登録するが、org スコープ外（accessible_org_ids=[]）
        with app.app_context():
            from iot_app import db
            from iot_app.models.organization import OrganizationMaster
            from iot_app.models.device import DeviceMaster

            org = OrganizationMaster(organization_name='テスト組織')
            db.session.add(org)
            db.session.flush()

            device = DeviceMaster(
                device_name='テストデバイス',
                organization_id=org.organization_id,
            )
            db.session.add(device)
            db.session.commit()
            device_id = device.device_id

        form_data = self._valid_form(device_mode='fixed', device_id=str(device_id))

        # Act
        response = client.post(self._URL, data=form_data)

        # Assert: accessible_org_ids=[] のためアクセス不可 → 404
        assert response.status_code == 404

    # TODO: 認証実装後に追加 - device_mode=fixed 成功ケース
    # 認証実装後は accessible_org_ids に device の organization_id が含まれる状態を作り、
    # ビュー層のデバイスチェックを通過して正常登録（302リダイレクト）を確認すること。

    def test_register_without_gadget_type_master_returns_error(self, client, measurement_item):
        """4.3.10: GadgetTypeMaster に「棒グラフ」レコードが存在しない場合はエラー

        NOTE: サービスコードが gadget_type_id=1 ハードコードのままの場合、このテストは失敗する。
        GadgetTypeMaster からの動的取得に変更することでパスする。
        """
        # Arrange: gadget_type フィクスチャを使わずに GadgetTypeMaster を空にしておく
        # measurement_item のみ登録済み（gadget_type レコードなし）

        # Act
        response = client.post(self._URL, data=self._valid_form())

        # Assert: GadgetTypeMaster に該当レコードなし → 404 または 500
        assert response.status_code in (404, 500)

    def test_register_with_deleted_gadget_type_master_returns_error(self, client, app, measurement_item):
        """4.3.11: GadgetTypeMaster に delete_flag=True の「棒グラフ」しかない場合はエラー

        NOTE: サービスコードが gadget_type_id=1 ハードコードのままの場合、このテストは失敗する。
        GadgetTypeMaster からの動的取得（delete_flag=False フィルタ付き）に変更することでパスする。
        """
        # Arrange: delete_flag=True の棒グラフレコードのみ登録
        with app.app_context():
            from iot_app import db
            from iot_app.models.dashboard import GadgetTypeMaster
            gt = GadgetTypeMaster(
                gadget_type_name='棒グラフ',
                delete_flag=True,
            )
            db.session.add(gt)
            db.session.commit()

        # Act
        response = client.post(self._URL, data=self._valid_form())

        # Assert: delete_flag=True のため first() が None → 404 または 500
        assert response.status_code in (404, 500)

    def test_register_gadget_type_id_matches_gadget_type_master(self, client, app, gadget_type, measurement_item):
        """4.3.12: 保存された gadget_type_id が GadgetTypeMaster から動的取得した値と一致する

        NOTE: サービスコードが gadget_type_id=1 ハードコードのままで、かつ GadgetTypeMaster の
        gadget_type_id が 1 の場合は偶然パスする。gadget_type_id が 1 以外の値になる環境では
        ハードコードの問題が顕在化する。
        """
        # Arrange: gadget_type フィクスチャで GadgetTypeMaster に「棒グラフ」登録済み
        expected_gadget_type_id = gadget_type.gadget_type_id

        # Act
        client.post(self._URL, data=self._valid_form())

        # Assert: DBに保存された gadget_type_id が GadgetTypeMaster の値と一致
        with app.app_context():
            from iot_app import db
            from iot_app.models.dashboard import DashboardGadgetMaster
            gadget = db.session.query(DashboardGadgetMaster).first()
        assert gadget.gadget_type_id == expected_gadget_type_id


# ─────────────────────────────────────────────────────────────────────────────
# 5. CSVエクスポート
# GET /analysis/customer-dashboard/gadgets/<gadget_uuid>?export=csv
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.integration
class TestGadgetCsvExport:
    """棒グラフガジェット CSVエクスポート

    観点: 4.6 CSVエクスポート、2.2 エラー時遷移
    """

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

    def test_csv_returns_200(self, client, gadget, mocker):
        """4.6.1: 正常エクスポート - 200レスポンス"""
        # Arrange: 外部APIをモック
        mocker.patch(_GOLD_QUERY, return_value=[
            {'collection_hour': 10, 'summary_value': 25.5},
        ])

        # Act
        response = client.get(self._url(gadget.gadget_uuid, **self._default_params()))

        # Assert
        assert response.status_code == 200

    def test_csv_content_type_is_text_csv(self, client, gadget, mocker):
        """4.6.2: Content-Type が text/csv"""
        # Arrange
        mocker.patch(_GOLD_QUERY, return_value=[])

        # Act
        response = client.get(self._url(gadget.gadget_uuid, **self._default_params()))

        # Assert
        assert 'text/csv' in response.content_type

    def test_csv_content_disposition_is_attachment(self, client, gadget, mocker):
        """4.6.3: Content-Disposition で attachment（ダウンロード）になる"""
        # Arrange
        mocker.patch(_GOLD_QUERY, return_value=[])

        # Act
        response = client.get(self._url(gadget.gadget_uuid, **self._default_params()))

        # Assert
        disposition = response.headers.get('Content-Disposition', '')
        assert 'attachment' in disposition
        assert 'sensor_data_' in disposition

    def test_csv_has_utf8_bom(self, client, gadget, mocker):
        """4.6.4: CSVがUTF-8 BOM付き（Excelで文字化けしない）"""
        # Arrange
        mocker.patch(_GOLD_QUERY, return_value=[])

        # Act
        response = client.get(self._url(gadget.gadget_uuid, **self._default_params()))

        # Assert
        assert response.data[:3] == b'\xef\xbb\xbf'

    def test_csv_has_header_row(self, client, gadget, mocker):
        """4.6.5: CSVの1行目にヘッダー（timestamp, value）が含まれる"""
        # Arrange
        mocker.patch(_GOLD_QUERY, return_value=[])

        # Act
        response = client.get(self._url(gadget.gadget_uuid, **self._default_params()))

        # Assert
        csv_text = response.data.decode('utf-8-sig')
        header = csv_text.splitlines()[0]
        assert 'timestamp' in header
        assert 'value' in header

    def test_csv_data_rows_match_mocked_rows(self, client, gadget, mocker):
        """4.6.6: ゴールド層の行データがCSVのデータ行に正しく出力される"""
        # Arrange
        mocker.patch(_GOLD_QUERY, return_value=[
            {'collection_hour': 8,  'summary_value': 20.0},
            {'collection_hour': 9,  'summary_value': 21.5},
        ])

        # Act
        response = client.get(self._url(gadget.gadget_uuid, **self._default_params()))

        # Assert
        csv_text = response.data.decode('utf-8-sig')
        lines = csv_text.splitlines()
        assert len(lines) == 3  # ヘッダー + 2行
        assert '08:00' in lines[1]
        assert '20.0' in lines[1]

    def test_csv_without_export_param_returns_404(self, client, gadget):
        """2.2.4: export=csv パラメータなしで404"""
        # Act
        response = client.get(
            f"{BASE_URL}/gadgets/{gadget.gadget_uuid}?display_unit=day&interval=10min&base_datetime={_VALID_DATETIME}"
        )

        # Assert
        assert response.status_code == 404

    def test_csv_nonexistent_gadget_returns_404(self, client):
        """2.2.4: 存在しないgadget_uuidで404"""
        # Act
        response = client.get(self._url(str(uuid.uuid4()), **self._default_params()))

        # Assert
        assert response.status_code == 404

    def test_csv_invalid_display_unit_returns_400(self, client, gadget):
        """3.6.1: 不正なdisplay_unitで400"""
        # Act
        params = {**self._default_params(), 'display_unit': 'invalid'}
        response = client.get(self._url(gadget.gadget_uuid, **params))

        # Assert
        assert response.status_code == 400

    def test_csv_unity_catalog_error_returns_500(self, client, gadget, mocker):
        """2.2.6: Unity Catalog クエリ失敗時に500"""
        # Arrange
        mocker.patch(_GOLD_QUERY, side_effect=Exception("Connection error"))

        # Act
        response = client.get(self._url(gadget.gadget_uuid, **self._default_params()))

        # Assert
        assert response.status_code == 500

    def test_csv_filename_format(self, client, gadget, mocker):
        """4.6.2: Content-Disposition のファイル名が sensor_data_YYYYMMDDHHmmss.csv 形式になる"""
        import re
        # Arrange
        mocker.patch(_GOLD_QUERY, return_value=[])

        # Act
        response = client.get(self._url(gadget.gadget_uuid, **self._default_params()))

        # Assert
        disposition = response.headers.get('Content-Disposition', '')
        assert re.search(r'sensor_data_\d{14}\.csv', disposition), \
            f"ファイル名形式が不正: {disposition}"

    def test_csv_search_params_passed_to_gold_query(self, client, gadget, mocker):
        """4.6.3: display_unit=day・base_datetime の検索条件がゴールド層クエリに正しく渡る"""
        from datetime import date
        # Arrange
        mock_query = mocker.patch(_GOLD_QUERY, return_value=[])
        params = {**self._default_params(), 'display_unit': 'day', 'base_datetime': '2026/03/06 12:00:00'}

        # Act
        client.get(self._url(gadget.gadget_uuid, **params))

        # Assert: execute_gold_query が target_date=date(2026,3,6) で呼ばれている
        assert mock_query.called
        call_kwargs = mock_query.call_args.kwargs
        assert call_kwargs.get('target_date') == date(2026, 3, 6)
        assert call_kwargs.get('display_unit') == 'day'

    def test_csv_data_output_in_query_order(self, client, gadget, mocker):
        """4.6.4: DBクエリが返したデータの順序がCSV出力にそのまま反映される"""
        # Arrange: 時刻昇順（08:00 → 09:00 → 10:00）でモック返却
        mocker.patch(_GOLD_QUERY, return_value=[
            {'collection_hour': 8,  'summary_value': 20.0},
            {'collection_hour': 9,  'summary_value': 22.0},
            {'collection_hour': 10, 'summary_value': 18.0},
        ])

        # Act
        response = client.get(self._url(gadget.gadget_uuid, **self._default_params()))

        # Assert: CSV の行順序がクエリ返却順と一致する
        csv_text = response.data.decode('utf-8-sig')
        lines = csv_text.splitlines()
        assert len(lines) == 4      # ヘッダー + 3行
        assert '08:00' in lines[1]
        assert '09:00' in lines[2]
        assert '10:00' in lines[3]

    def test_csv_empty_data_outputs_header_only(self, client, gadget, mocker):
        """4.6.5: クエリ結果0件の場合、ヘッダー行のみのCSVが出力される"""
        # Arrange
        mocker.patch(_GOLD_QUERY, return_value=[])

        # Act
        response = client.get(self._url(gadget.gadget_uuid, **self._default_params()))

        # Assert: データ行なし、ヘッダー1行のみ
        csv_text = response.data.decode('utf-8-sig')
        lines = [line for line in csv_text.splitlines() if line.strip()]
        assert len(lines) == 1
        assert 'timestamp' in lines[0]
        assert 'value' in lines[0]


# ─────────────────────────────────────────────────────────────────────────────
# 6. HTMLレンダリング（BeautifulSoup DOM検証）
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.integration
class TestHtmlRendering:
    """HTMLレンダリング検証（DOM構造）

    観点: HTMLレンダリング（BEM構造・フォーム要素・ガジェット構造）
    """

    def test_dashboard_toolbar_structure(self, client):
        """ダッシュボードツールバーに編集モード・レイアウト保存・管理ボタンが存在する"""
        # Act
        response = client.get(BASE_URL)
        soup = _soup(response)

        # Assert: ツールバー要素の存在
        assert soup.find(id='edit-mode-btn') is not None
        assert soup.find(id='save-layout-btn') is not None
        assert soup.find(id='dashboard-manage-btn') is not None

    def test_dashboard_datasource_selects(self, client):
        """データソース選択フォームに組織・デバイスの select が存在する"""
        # Act
        response = client.get(BASE_URL)
        soup = _soup(response)

        # Assert
        assert soup.find(id='select-organization') is not None
        assert soup.find(id='select-device') is not None

    def test_gadget_has_barchart_canvas(self, client, gadget):
        """ガジェット内に棒グラフキャンバス（id='chart-<uuid>'）が存在する"""
        # Act
        response = client.get(BASE_URL)
        soup = _soup(response)

        # Assert
        canvas = soup.find(id=f'chart-{gadget.gadget_uuid}')
        assert canvas is not None

    def test_gadget_has_unit_buttons(self, client, gadget):
        """棒グラフガジェットに時/日/週/月の表示単位ボタンが存在する"""
        # Act
        response = client.get(BASE_URL)
        soup = _soup(response)

        # Assert
        unit_btns = soup.find_all('button', class_='bar-chart__unit-btn')
        unit_values = {btn['data-unit'] for btn in unit_btns if btn.get('data-unit')}
        assert unit_values == {'hour', 'day', 'week', 'month'}

    def test_gadget_has_interval_select(self, client, gadget):
        """棒グラフガジェットに集計時間幅 select（1/2/3/5/10/15分）が存在する"""
        # Act
        response = client.get(BASE_URL)
        soup = _soup(response)

        # Assert
        interval_select = soup.find('select', class_='bar-chart__interval-select')
        assert interval_select is not None
        option_values = {opt['value'] for opt in interval_select.find_all('option') if opt.get('value')}
        assert option_values == {'1min', '2min', '3min', '5min', '10min', '15min'}

    def test_gadget_has_datetime_input(self, client, gadget):
        """棒グラフガジェットに日時入力フィールド（bar-chart__datetime-input）が存在する"""
        # Act
        response = client.get(BASE_URL)
        soup = _soup(response)

        # Assert
        dt_input = soup.find('input', class_='bar-chart__datetime-input')
        assert dt_input is not None

    def test_empty_state_message_shown_when_no_gadgets(self, client):
        """ガジェット未登録時に空状態メッセージ要素（customer-dashboard__empty）が表示される"""
        # Arrange: DBにガジェットなし

        # Act
        response = client.get(BASE_URL)
        soup = _soup(response)

        # Assert
        assert soup.find(class_='customer-dashboard__empty') is not None

    def test_empty_state_hidden_when_gadgets_exist(self, client, gadget):
        """ガジェット登録済み時に空状態メッセージが表示されない"""
        # Act
        response = client.get(BASE_URL)
        soup = _soup(response)

        # Assert
        assert soup.find(class_='customer-dashboard__empty') is None

    def test_register_422_re_renders_modal_with_form(self, client, measurement_item):
        """バリデーションエラー時（400）に登録モーダルが再描画され、フォームが含まれる"""
        # Act: タイトル空で送信 → 400
        response = client.post(
            f"{BASE_URL}/gadgets/bar-chart/register",
            data={
                'title': '',
                'device_mode': 'variable',
                'device_id': '0',
                'group_id': '1',
                'summary_method_id': '1',
                'measurement_item_id': '1',
                'gadget_size': '2x2',
            },
        )
        soup = _soup(response)

        # Assert: フォームが再描画されている
        assert response.status_code == 400
        assert soup.find('input', {'name': 'title'}) is not None


# ─────────────────────────────────────────────────────────────────────────────
# 7. セキュリティテスト
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.integration
class TestSecurity:
    """セキュリティテスト

    観点: 9.1 SQLインジェクション、9.2 XSS、9.3 CSRF対策
    """

    _REGISTER_URL = f"{BASE_URL}/gadgets/bar-chart/register"

    def _valid_form(self, **overrides):
        data = {
            'title': 'テストガジェット',
            'device_mode': 'variable',
            'device_id': '0',
            'group_id': '1',
            'summary_method_id': '1',
            'measurement_item_id': '1',
            'gadget_size': '2x2',
        }
        data.update(overrides)
        return data

    def _insert_gadget_with_name(self, db_session, gadget_name, gadget_type):
        """XSSテスト用ガジェットをDB直接登録するヘルパー（20文字制限を回避）"""
        import json as _json
        from iot_app.models.dashboard import DashboardGadgetMaster
        gadget = DashboardGadgetMaster(
            gadget_uuid=str(uuid.uuid4()),
            gadget_name=gadget_name,
            gadget_type_id=1,
            dashboard_group_id=1,
            chart_config=_json.dumps({
                'measurement_item_id': 1,
                'summary_method_id': 1,
                'min_value': None,
                'max_value': None,
            }),
            data_source_config=_json.dumps({'device_id': None}),
            position_x=0,
            position_y=1,
            gadget_size='2x2',
            display_order=1,
            creator=1,
            modifier=1,
        )
        db_session.add(gadget)
        db_session.flush()
        return gadget

    # ── 9.1 SQLインジェクション ──────────────────────────────────────────

    def test_sql_injection_basic_in_title(self, client):
        """9.1.1: タイトルに基本的なSQLインジェクション（' OR '1'='1）を入力してもサーバーがクラッシュしない"""
        # Act: SQLAlchemy ORM がパラメータをエスケープするため 302 または 422 を返す
        response = client.post(
            self._REGISTER_URL,
            data=self._valid_form(title="' OR '1'='1"),
        )

        # Assert: 500（サーバーエラー）にならない
        assert response.status_code != 500

    def test_sql_injection_comment_in_title(self, client):
        """9.1.2: コメントを使ったSQLインジェクション（'; DROP TABLE--）でサーバーがクラッシュしない"""
        # Act
        response = client.post(
            self._REGISTER_URL,
            data=self._valid_form(title="'; DROP TABLE--"),
        )

        # Assert
        assert response.status_code != 500

    def test_sql_injection_union_in_title(self, client):
        """9.1.3: UNIONを使ったSQLインジェクション（' UNION SELECT--）でサーバーがクラッシュしない"""
        # Act
        response = client.post(
            self._REGISTER_URL,
            data=self._valid_form(title="' UNION SELECT--"),
        )

        # Assert
        assert response.status_code != 500

    def test_sql_injection_in_gadget_uuid_url(self, client):
        """9.1.1: URLの gadget_uuid にSQLインジェクション文字列を指定しても404を返す（500にならない）"""
        # Act: SQLAlchemy フィルタに渡るが ORM がエスケープするため404
        response = client.post(
            f"{BASE_URL}/gadgets/' OR '1'='1/data",
            json={'display_unit': 'day', 'interval': '10min', 'base_datetime': _VALID_DATETIME},
        )

        # Assert
        assert response.status_code == 404

    # ── 9.2 XSS ─────────────────────────────────────────────────────────

    def test_xss_script_tag_in_gadget_title_is_escaped(self, client, db_session, gadget_type):
        """9.2.1: <script> タグを含むガジェット名がダッシュボードHTMLでエスケープされて表示される"""
        # Arrange: DB直接登録（20文字制限を回避、SQLite は VARCHAR 長を強制しない）
        xss_payload = "<script>alert('XSS')</script>"
        self._insert_gadget_with_name(db_session, xss_payload, gadget_type)

        # Act
        response = client.get(BASE_URL)

        # Assert: <script> タグがそのまま出力されていない（Jinja2 の自動エスケープ）
        assert b"<script>alert('XSS')</script>" not in response.data
        assert b"&lt;script&gt;" in response.data

    def test_xss_img_onerror_in_gadget_title_is_escaped(self, client, db_session, gadget_type):
        """9.2.2: imgタグXSS（onerror）を含むガジェット名がエスケープされて表示される"""
        # Arrange
        xss_payload = "<img src=x onerror=alert('XSS')>"
        self._insert_gadget_with_name(db_session, xss_payload, gadget_type)

        # Act
        response = client.get(BASE_URL)

        # Assert: <img タグがそのまま出力されていない（Jinja2 の自動エスケープ）
        assert b"<img" not in response.data

    def test_xss_javascript_protocol_in_gadget_title_is_escaped(self, client, db_session, gadget_type):
        """9.2.3: JavaScriptプロトコル（javascript:alert）を含むガジェット名がエスケープされて表示される"""
        # Arrange
        xss_payload = "javascript:alert('XSS')"
        self._insert_gadget_with_name(db_session, xss_payload, gadget_type)

        # Act
        response = client.get(BASE_URL)

        # Assert: javascript: の引数がエスケープされており、そのまま実行可能な形で出力されていない
        assert b"javascript:alert('XSS')" not in response.data

    # ── 9.3 CSRF対策 ─────────────────────────────────────────────────────

    def test_csrf_post_without_token_returns_400(self, client, app):
        """9.3.1: CSRF有効時、トークンなしPOSTで400エラー"""
        # Arrange: disable_csrf autouse フィクスチャ後に CSRF を一時的に有効化
        app.config['WTF_CSRF_ENABLED'] = True
        try:
            # Act: CSRF トークンなしで POST
            response = client.post(
                self._REGISTER_URL,
                data=self._valid_form(),
            )

            # Assert
            assert response.status_code == 400
        finally:
            app.config['WTF_CSRF_ENABLED'] = False

    def test_csrf_post_with_invalid_token_returns_400(self, client, app):
        """9.3.2: CSRF有効時、無効なトークンのPOSTで400エラー"""
        # Arrange
        app.config['WTF_CSRF_ENABLED'] = True
        try:
            # Act
            response = client.post(
                self._REGISTER_URL,
                data={**self._valid_form(), 'csrf_token': 'invalid-token-xyz'},
            )

            # Assert
            assert response.status_code == 400
        finally:
            app.config['WTF_CSRF_ENABLED'] = False

    def test_csrf_is_disabled_for_other_tests(self, app):
        """9.3.3: disable_csrf autouse フィクスチャにより CSRF が無効化されている"""
        # Assert: 他テストに影響しないことを確認
        assert app.config['WTF_CSRF_ENABLED'] is False


# ─────────────────────────────────────────────────────────────────────────────
# 8. トランザクション・ロールバックテスト
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.integration
class TestTransaction:
    """トランザクション・ロールバックテスト

    観点: 7.2.1 UNIQUE制約違反、7.2.3/7.2.4 コミット失敗→ロールバック
    """

    _REGISTER_URL = f"{BASE_URL}/gadgets/bar-chart/register"

    def _valid_form(self, **overrides):
        data = {
            'title': 'トランザクションテスト',
            'device_mode': 'variable',
            'device_id': '0',
            'group_id': '1',
            'summary_method_id': '1',
            'measurement_item_id': '1',
            'gadget_size': '2x2',
        }
        data.update(overrides)
        return data

    def test_unique_uuid_constraint_violation_returns_500(
        self, client, db_session, gadget_type, measurement_item, mocker
    ):
        """7.2.1: gadget_uuid UNIQUE制約違反時にロールバックされ500エラー"""
        import json as _json
        from iot_app.models.dashboard import DashboardGadgetMaster

        fixed_uuid_str = 'aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee'

        # Arrange: 固定UUIDで直接DB挿入（既存レコードを作成）
        existing = DashboardGadgetMaster(
            gadget_uuid=fixed_uuid_str,
            gadget_name='既存ガジェット',
            gadget_type_id=1,
            dashboard_group_id=1,
            chart_config=_json.dumps({
                'measurement_item_id': 1, 'summary_method_id': 1,
                'min_value': None, 'max_value': None,
            }),
            data_source_config=_json.dumps({'device_id': None}),
            position_x=0, position_y=1, gadget_size='2x2',
            display_order=1, creator=1, modifier=1,
        )
        db_session.add(existing)
        db_session.flush()

        # uuid.uuid4 を固定値に差し替え → 同じ UUID で登録を試みる
        mocker.patch(
            'iot_app.services.customer_dashboard.bar_chart.uuid.uuid4',
            return_value=uuid.UUID(fixed_uuid_str),
        )

        # Act: UNIQUE制約違反が発生する登録リクエスト
        response = client.post(self._REGISTER_URL, data=self._valid_form())

        # Assert: サービス層でロールバック済み → 500
        assert response.status_code == 500

    # NOTE: 7.2.3/7.2.4（コミット失敗→ロールバック）は db.session.commit をモックするため
    # 「DBはモック化しない」ガイドラインに違反する。
    # 実際のDB制約違反でロールバックを検証する test_unique_uuid_constraint_violation_returns_500 で代替する。


# ─────────────────────────────────────────────────────────────────────────────
# 9. ログ出力テスト（ログ設計書準拠）
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.integration
class TestLogging:
    """ログ出力テスト

    観点: 6.2 リクエスト前後、4章 自動付与フィールド、5.1 マスキング、
          6.5 SQLAlchemy イベント、6.6 エラーハンドリング、8.2.1 エラーログ

    NOTE: 未実装の機能に対応するテストは現状 FAIL する。
          各機能を実装した後にパスすることを確認すること。
    """

    # ── 6.2 リクエスト前後ログ ────────────────────────────────────────────

    def test_request_start_is_logged_as_info(self, client, caplog):
        """6.2: リクエスト受信時に INFO 'リクエスト開始' が出力される"""
        import logging
        with caplog.at_level(logging.INFO):
            client.get(BASE_URL)

        assert any("リクエスト開始" in r.message for r in caplog.records)

    def test_request_end_is_logged_with_status_and_duration(self, client, caplog):
        """6.2: リクエスト完了時に INFO 'リクエスト完了' + httpStatus + processingTime が出力される"""
        import logging
        with caplog.at_level(logging.INFO):
            client.get(BASE_URL)

        end_records = [r for r in caplog.records if "リクエスト完了" in r.message]
        assert len(end_records) >= 1
        record = end_records[0]
        assert hasattr(record, "httpStatus")
        assert hasattr(record, "processingTime")
        assert isinstance(record.processingTime, int)

    # ── 4章 AppLoggerAdapter 自動付与フィールド ───────────────────────────

    def test_logger_attaches_endpoint_and_method_in_request_context(self, client, gadget, mocker, caplog):
        """4章: リクエストコンテキスト内の ERROR ログに endpoint・method が自動付与される"""
        import logging
        # Unity Catalog を例外に差し替えて logger.error を発火させる
        mocker.patch(_GOLD_QUERY, side_effect=Exception("trigger log"))

        with caplog.at_level(logging.ERROR, logger="iot_app.services.customer_dashboard.bar_chart"):
            client.post(
                f"{BASE_URL}/gadgets/{gadget.gadget_uuid}/data",
                json={"display_unit": "day", "interval": "10min", "base_datetime": _VALID_DATETIME},
            )

        error_records = [r for r in caplog.records if r.levelno == logging.ERROR]
        assert len(error_records) >= 1
        record = error_records[0]
        assert hasattr(record, "endpoint")
        assert hasattr(record, "method")
        assert record.endpoint == f"/analysis/customer-dashboard/gadgets/{gadget.gadget_uuid}/data"
        assert record.method == "POST"

    def test_logger_attaches_request_id(self, client, gadget, mocker, caplog):
        """4章: ログに requestId（UUID v4）が自動付与される"""
        import logging
        mocker.patch(_GOLD_QUERY, side_effect=Exception("trigger log"))

        with caplog.at_level(logging.ERROR, logger="iot_app.services.customer_dashboard.bar_chart"):
            client.post(
                f"{BASE_URL}/gadgets/{gadget.gadget_uuid}/data",
                json={"display_unit": "day", "interval": "10min", "base_datetime": _VALID_DATETIME},
            )

        error_records = [r for r in caplog.records if r.levelno == logging.ERROR]
        assert len(error_records) >= 1
        record = error_records[0]
        assert hasattr(record, "requestId")
        assert record.requestId != "-"

    # ── 5.1 マスキング ────────────────────────────────────────────────────

    def test_email_is_masked_in_log_output(self, app):
        """5.1: email キーを使ってログを出力すると先頭2文字以外がマスクされる（ya****@example.com）"""
        from iot_app.common.logger import get_logger
        test_logger = get_logger("test.masking")

        with app.app_context():
            with app.test_request_context("/"):
                _, kwargs = test_logger.process("テスト", {"extra": {"email": "yamada@example.com"}})

        assert kwargs["extra"]["email"] == "ya****@example.com"

    def test_phone_is_masked_in_log_output(self, app):
        """5.1: phone キーを使ってログを出力すると中間4桁がマスクされる（090-****-5678）"""
        from iot_app.common.logger import get_logger
        test_logger = get_logger("test.masking")

        with app.app_context():
            with app.test_request_context("/"):
                _, kwargs = test_logger.process("テスト", {"extra": {"phone": "090-1234-5678"}})

        assert kwargs["extra"]["phone"] == "090-****-5678"

    def test_non_sensitive_key_is_not_masked(self, app):
        """5.1: マスキング対象外のキー（device_id 等）はそのまま出力される"""
        from iot_app.common.logger import get_logger
        test_logger = get_logger("test.masking")

        with app.app_context():
            with app.test_request_context("/"):
                _, kwargs = test_logger.process("テスト", {"extra": {"device_id": 123}})

        assert kwargs["extra"]["device_id"] == 123

    # ── 6.5 SQLAlchemy イベントリスナー ──────────────────────────────────

    def test_insert_is_logged_as_info_with_query_and_duration(self, client, measurement_item, gadget_type, caplog):
        """6.5: INSERT 実行時に INFO 'SQL実行' + query + duration_ms が出力される"""
        import logging
        with caplog.at_level(logging.INFO):
            client.post(
                f"{BASE_URL}/gadgets/bar-chart/register",
                data={
                    "title": "SQLログテスト",
                    "device_mode": "variable",
                    "device_id": "0",
                    "group_id": "1",
                    "summary_method_id": "1",
                    "measurement_item_id": "1",
                    "gadget_size": "2x2",
                },
            )

        sql_records = [r for r in caplog.records if "SQL実行" in r.message]
        insert_records = [r for r in sql_records if hasattr(r, "query") and "INSERT" in r.query.upper()]
        assert len(insert_records) >= 1
        record = insert_records[0]
        assert hasattr(record, "duration_ms")
        assert record.levelno == logging.INFO

    def test_select_is_logged_as_debug(self, client, caplog):
        """6.5: SELECT 実行時に DEBUG 'SQL実行' が出力される"""
        import logging
        with caplog.at_level(logging.DEBUG):
            client.get(BASE_URL)

        sql_records = [r for r in caplog.records if "SQL実行" in r.message]
        select_records = [
            r for r in sql_records
            if hasattr(r, "query") and r.query.strip().upper().startswith("SELECT")
        ]
        assert len(select_records) >= 1
        assert all(r.levelno == logging.DEBUG for r in select_records)

    # ── 6.6 エラーハンドリングログ ────────────────────────────────────────

    def test_500_error_is_logged_as_error_with_error_type(self, client, gadget, mocker, caplog):
        """6.6: 500エラー時に ERROR 'Internal Server Error' + error_type が出力される"""
        import logging
        mocker.patch(_GOLD_QUERY, side_effect=Exception("DB down"))

        with caplog.at_level(logging.ERROR):
            client.post(
                f"{BASE_URL}/gadgets/{gadget.gadget_uuid}/data",
                json={"display_unit": "day", "interval": "10min", "base_datetime": _VALID_DATETIME},
            )

        error_records = [r for r in caplog.records if "Internal Server Error" in r.message]
        assert len(error_records) >= 1
        record = error_records[0]
        assert hasattr(record, "error_type")
        assert record.error_type == "Exception"

    def test_404_error_is_logged_as_warning_with_http_status(self, client, caplog):
        """6.6: 404エラー時に WARNING 'Client Error' + httpStatus=404 が出力される"""
        import logging
        nonexistent = str(uuid.uuid4())
        with caplog.at_level(logging.WARNING):
            client.get(
                f"{BASE_URL}/gadgets/{nonexistent}"
                f"?export=csv&display_unit=day&interval=10min&base_datetime={_VALID_DATETIME}"
            )

        warn_records = [r for r in caplog.records if "Client Error" in r.message]
        assert len(warn_records) >= 1
        record = warn_records[0]
        assert hasattr(record, "httpStatus")
        assert record.httpStatus == 404

    # ── 8.2.1 サービス層エラーログ ───────────────────────────────────────

    def test_data_fetch_error_logged_as_error(self, client, gadget, mocker, caplog):
        """8.2.1: Unity Catalog クエリ失敗時に ERROR '棒グラフデータ取得エラー' が出力される"""
        import logging
        mocker.patch(_GOLD_QUERY, side_effect=Exception("Connection timeout"))

        with caplog.at_level(logging.ERROR, logger="iot_app.services.customer_dashboard.bar_chart"):
            client.post(
                f"{BASE_URL}/gadgets/{gadget.gadget_uuid}/data",
                json={"display_unit": "day", "interval": "10min", "base_datetime": _VALID_DATETIME},
            )

        assert any("棒グラフデータ取得エラー" in r.message for r in caplog.records)

    def test_csv_export_error_logged_as_error(self, client, gadget, mocker, caplog):
        """8.2.1: CSV エクスポートのクエリ失敗時に ERROR '棒グラフCSVエクスポートエラー' が出力される"""
        import logging
        mocker.patch(_GOLD_QUERY, side_effect=Exception("Connection error"))

        with caplog.at_level(logging.ERROR, logger="iot_app.services.customer_dashboard.bar_chart"):
            client.get(
                f"{BASE_URL}/gadgets/{gadget.gadget_uuid}"
                f"?export=csv&display_unit=day&interval=10min&base_datetime={_VALID_DATETIME}"
            )

        assert any("棒グラフCSVエクスポートエラー" in r.message for r in caplog.records)

    def test_register_error_logged_as_error_with_exc_info(self, client, measurement_item, gadget_type, mocker, caplog):
        """8.2.1: ガジェット登録失敗時に ERROR '棒グラフガジェット登録エラー' が exc_info=True で出力される"""
        import logging
        mocker.patch(
            "iot_app.services.customer_dashboard.bar_chart.db.session.commit",
            side_effect=Exception("DB commit error"),
        )

        with caplog.at_level(logging.ERROR, logger="iot_app.services.customer_dashboard.bar_chart"):
            client.post(
                f"{BASE_URL}/gadgets/bar-chart/register",
                data={
                    "title": "ログテスト",
                    "device_mode": "variable",
                    "device_id": "0",
                    "group_id": "1",
                    "summary_method_id": "1",
                    "measurement_item_id": "1",
                    "gadget_size": "2x2",
                },
            )

        error_records = [r for r in caplog.records if "棒グラフガジェット登録エラー" in r.message]
        assert len(error_records) >= 1
        # exc_info=True 指定時、LogRecord に exc_info が記録される
        assert error_records[0].exc_info is not None


# ─────────────────────────────────────────────────────────────────────────────
# 新テスト: Route 2 - デバイス可変モードのデバイスID決定ロジック
# POST /analysis/customer-dashboard/gadgets/<gadget_uuid>/data
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.integration
class TestGadgetBarChartDataVariableMode:
    """棒グラフガジェット データ取得（可変モード device_id 決定ロジック）

    観点: device_id=null の場合に dashboard_user_setting から device_id を取得する
    """

    def _url(self, gadget_uuid):
        return f"{BASE_URL}/gadgets/{gadget_uuid}/data"

    def _json_params(self):
        return {'display_unit': 'day', 'interval': '10min', 'base_datetime': _VALID_DATETIME}

    def test_variable_mode_with_user_setting_uses_device_id(
        self, client, gadget_variable, auth_user_id, dashboard_user_setting, mocker
    ):
        """可変モードガジェット＋user_setting有り → setting.device_id がクエリに渡る"""
        # Arrange
        mock_query = mocker.patch(_GOLD_QUERY, return_value=[])

        # Act
        response = client.post(self._url(gadget_variable.gadget_uuid), json=self._json_params())

        # Assert: 200 かつ execute_gold_query が setting.device_id=1 で呼ばれている
        assert response.status_code == 200
        assert mock_query.called
        assert mock_query.call_args.kwargs['device_id'] == dashboard_user_setting.device_id

    def test_variable_mode_without_user_setting_device_id_is_none(
        self, client, gadget_variable, auth_user_id, mocker
    ):
        """可変モードガジェット＋user_setting無し → device_id=None でクエリが呼ばれる"""
        # Arrange: dashboard_user_setting フィクスチャなし（設定レコードなし）
        mock_query = mocker.patch(_GOLD_QUERY, return_value=[])

        # Act
        response = client.post(self._url(gadget_variable.gadget_uuid), json=self._json_params())

        # Assert: 200 かつ device_id=None で呼ばれる
        assert response.status_code == 200
        assert mock_query.called
        assert mock_query.call_args.kwargs['device_id'] is None

    def test_fixed_mode_not_affected_by_user_setting(
        self, client, gadget, auth_user_id, dashboard_user_setting, mocker
    ):
        """固定モードガジェットは device_id をガジェット設定から取得し user_setting を使わない"""
        # Arrange: gadget は device_id=1（固定モード）、dashboard_user_setting も device_id=1
        mock_query = mocker.patch(_GOLD_QUERY, return_value=[])

        # Act
        response = client.post(self._url(gadget.gadget_uuid), json=self._json_params())

        # Assert: 200 かつ gadget の data_source_config から device_id=1 が渡る
        assert response.status_code == 200
        assert mock_query.called
        assert mock_query.call_args.kwargs['device_id'] == 1


# ─────────────────────────────────────────────────────────────────────────────
# 新テスト: Route 3 - dashboard_user_setting → dashboard_master フロー
# GET /analysis/customer-dashboard/gadgets/bar-chart/create
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.integration
class TestGadgetBarChartCreateNewFlow:
    """棒グラフガジェット 登録モーダル表示 - 新フロー検証

    観点: current_user_id=None→404、user_setting無し→404、dashboard無し→404、正常表示→200
    """

    _URL = f"{BASE_URL}/gadgets/bar-chart/create"

    def test_create_no_user_setting_returns_404(self, client, auth_user_id, dashboard_master):
        """user_setting が存在しない場合 404"""
        # Arrange: auth_user_id あり、dashboard_master あり、しかし user_setting なし

        # Act
        response = client.get(self._URL)

        # Assert
        assert response.status_code == 404

    def test_create_user_setting_dashboard_not_found_returns_404(
        self, client, auth_user_id, db_session
    ):
        """user_setting が存在するが dashboard が存在しない場合 404"""
        # Arrange: 存在しない dashboard_id=9999 を指す user_setting を直接作成
        from iot_app.models.dashboard import DashboardMaster, DashboardUserSetting
        dummy_dashboard = DashboardMaster(dashboard_id=9999, dashboard_name='存在しない', delete_flag=False)
        db_session.add(dummy_dashboard)
        db_session.flush()
        setting = DashboardUserSetting(user_id=1, dashboard_id=9999, device_id=None)
        db_session.add(setting)
        db_session.flush()
        # dashboard_master のレコードを論理削除して「アクセス不可」にする
        dummy_dashboard.delete_flag = True
        db_session.flush()

        # Act
        response = client.get(self._URL)

        # Assert
        assert response.status_code == 404

    def test_create_with_full_setup_returns_200(
        self, client, auth_user_id, dashboard_user_setting, dashboard_master, dashboard_group_master
    ):
        """user_setting・dashboard・group が揃っている場合 200"""
        # Act
        response = client.get(self._URL)

        # Assert
        assert response.status_code == 200


# ─────────────────────────────────────────────────────────────────────────────
# 新テスト: Route 4 - リダイレクト先に ?registered=1 付与
# POST /analysis/customer-dashboard/gadgets/bar-chart/register
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.integration
class TestGadgetBarChartRegisterRedirect:
    """棒グラフガジェット 登録後リダイレクト URL 検証"""

    _URL = f"{BASE_URL}/gadgets/bar-chart/register"

    def _valid_form(self, **overrides):
        data = {
            'title': 'テストガジェット',
            'device_mode': 'variable',
            'device_id': '0',
            'group_id': '1',
            'summary_method_id': '1',
            'measurement_item_id': '1',
            'gadget_size': '2x2',
        }
        data.update(overrides)
        return data

    @pytest.fixture(autouse=True)
    def _require_gadget_type(self, db_session):
        from iot_app.models.dashboard import GadgetTypeMaster
        gt = GadgetTypeMaster(gadget_type_id=1, gadget_type_name='棒グラフ', delete_flag=False)
        db_session.add(gt)
        db_session.flush()

    def test_register_redirect_url_contains_registered_param(self, client, measurement_item):
        """4: 登録成功後のリダイレクト先 URL に ?registered=1 が含まれる"""
        # Act
        response = client.post(self._URL, data=self._valid_form(), follow_redirects=False)

        # Assert
        assert response.status_code == 302
        assert 'registered=1' in response.headers['Location']


# ─────────────────────────────────────────────────────────────────────────────
# 新テスト: Route 5 - 可変モードの CSV エクスポート
# GET /analysis/customer-dashboard/gadgets/<gadget_uuid>?export=csv
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.integration
class TestGadgetCsvExportVariableMode:
    """棒グラフガジェット CSVエクスポート - 可変モード device_id 決定ロジック"""

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

    def test_csv_variable_mode_with_user_setting_uses_device_id(
        self, client, gadget_variable, auth_user_id, dashboard_user_setting, mocker
    ):
        """可変モード＋user_setting有り → setting.device_id でクエリ実行され CSV が返る"""
        # Arrange
        mock_query = mocker.patch(_GOLD_QUERY, return_value=[])

        # Act
        response = client.get(self._url(gadget_variable.gadget_uuid, **self._default_params()))

        # Assert: 200 かつ device_id=setting.device_id でクエリが呼ばれる
        assert response.status_code == 200
        assert mock_query.called
        assert mock_query.call_args.kwargs['device_id'] == dashboard_user_setting.device_id

    def test_csv_variable_mode_without_user_setting_device_id_is_none(
        self, client, gadget_variable, auth_user_id, mocker
    ):
        """可変モード＋user_setting無し → device_id=None のまま CSV が返る"""
        # Arrange: dashboard_user_setting なし
        mock_query = mocker.patch(_GOLD_QUERY, return_value=[])

        # Act
        response = client.get(self._url(gadget_variable.gadget_uuid, **self._default_params()))

        # Assert: 200 かつ device_id=None でクエリが呼ばれる
        assert response.status_code == 200
        assert mock_query.called
        assert mock_query.call_args.kwargs['device_id'] is None
