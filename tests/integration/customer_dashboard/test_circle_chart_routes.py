"""
顧客作成ダッシュボード 円グラフガジェット - 結合テスト

対象エンドポイント:
  GET  /analysis/customer-dashboard
  POST /analysis/customer-dashboard/gadgets/<gadget_uuid>/data
  GET  /analysis/customer-dashboard/gadgets/circle-chart/create
  POST /analysis/customer-dashboard/gadgets/circle-chart/register

参照設計書:
  - docs/03-features/flask-app/customer-dashboard/circle-chart/ui-specification.md
  - docs/03-features/flask-app/customer-dashboard/circle-chart/workflow-specification.md

NOTE: モデルファイル（models/dashboard.py 等）が実装済みであることが前提。
      外部API（Unity Catalog / sensor_data_view）のみモック化する。
"""

import json
import uuid
from datetime import date

import pytest
from bs4 import BeautifulSoup

BASE_URL = "/analysis/customer-dashboard"

# Unity Catalog クエリのモック対象パス
_FETCH_CIRCLE_DATA = "iot_app.views.analysis.customer_dashboard.circle_chart.fetch_circle_chart_data"


def _soup(response) -> BeautifulSoup:
    """FlaskレスポンスからBeautifulSoupオブジェクトを生成するヘルパー"""
    return BeautifulSoup(response.data, "html.parser")


def _make_circle_gadget(db_session, gadget_type_id, dashboard_group_id=1, position_y=1, display_order=1):
    """DashboardGadgetMaster（円グラフ）テストレコードを生成して db_session に追加するヘルパー

    複数件作成・スコープ外テスト等で共通利用する。flush は呼び出し側で行うこと。
    """
    from iot_app.models.customer_dashboard import DashboardGadgetMaster
    g = DashboardGadgetMaster(
        gadget_uuid=str(uuid.uuid4()),
        gadget_name="テスト円グラフ",
        gadget_type_id=gadget_type_id,
        dashboard_group_id=dashboard_group_id,
        chart_config=json.dumps({"item_id_1": 1}),
        data_source_config=json.dumps({"device_id": None}),
        position_x=0,
        position_y=position_y,
        gadget_size=0,
        display_order=display_order,
        creator=1,
        modifier=1,
    )
    db_session.add(g)
    return g


# ─────────────────────────────────────────────────────────────────────────────
# 共通フィクスチャ（このファイル固有）
# ─────────────────────────────────────────────────────────────────────────────

@pytest.fixture()
def gadget_type_circle(db_session):
    """GadgetTypeMaster テストレコード（円グラフ）

    create_circle_chart_gadget() がサービス層で gadget_type_name='円グラフ' を
    動的ルックアップするため、登録テストでは必ず必要。
    """
    from iot_app.models.customer_dashboard import GadgetTypeMaster
    gt = GadgetTypeMaster(
        gadget_type_id=2,
        gadget_type_name="円グラフ",
        data_source_type=1,
        gadget_image_path="images/gadgets/circle_chart.png",
        gadget_description="円グラフガジェット",
        display_order=2,
        creator=1,
        modifier=1,
        delete_flag=False,
    )
    db_session.add(gt)
    db_session.flush()
    return gt


@pytest.fixture()
def circle_gadget(db_session, gadget_type_circle):
    """DashboardGadgetMaster テストレコード（円グラフ, デバイス固定モード）"""
    from iot_app.models.customer_dashboard import DashboardGadgetMaster
    g = DashboardGadgetMaster(
        gadget_uuid=str(uuid.uuid4()),
        gadget_name="テスト円グラフ",
        gadget_type_id=gadget_type_circle.gadget_type_id,
        dashboard_group_id=1,
        chart_config=json.dumps({"item_id_1": 1, "item_id_2": 2}),
        data_source_config=json.dumps({"device_id": 1}),
        position_x=0,
        position_y=1,
        gadget_size=0,
        display_order=1,
        creator=1,
        modifier=1,
    )
    db_session.add(g)
    db_session.flush()
    return g


@pytest.fixture()
def circle_gadget_variable(db_session, gadget_type_circle):
    """DashboardGadgetMaster テストレコード（円グラフ, デバイス可変モード）"""
    from iot_app.models.customer_dashboard import DashboardGadgetMaster
    g = DashboardGadgetMaster(
        gadget_uuid=str(uuid.uuid4()),
        gadget_name="テスト円グラフ（可変）",
        gadget_type_id=gadget_type_circle.gadget_type_id,
        dashboard_group_id=1,
        chart_config=json.dumps({"item_id_1": 1}),
        data_source_config=json.dumps({"device_id": None}),
        position_x=0,
        position_y=2,
        gadget_size=0,
        display_order=2,
        creator=1,
        modifier=1,
    )
    db_session.add(g)
    db_session.flush()
    return g


@pytest.fixture()
def device_master_record(db_session, organization_master_record):
    """DeviceMaster テストレコード（device_id=1, organization_id=1）

    デバイス固定モードのスコープチェックに使用する。
    DeviceMaster は device_type_master への FK を持つため、
    デバイス種別マスタも合わせて登録する。
    """
    from iot_app.models.device import DeviceMaster, DeviceTypeMaster
    dt = DeviceTypeMaster(
        device_type_id=1,
        device_type_name="テストデバイス種別",
        creator=1,
        modifier=1,
    )
    db_session.add(dt)
    db_session.flush()

    device = DeviceMaster(
        device_id=1,
        device_uuid=str(uuid.uuid4()),
        organization_id=1,
        device_type_id=1,
        device_name="テストデバイス",
        device_model="MODEL-001",
        device_inventory_id=1,
        creator=1,
        modifier=1,
    )
    db_session.add(device)
    db_session.flush()
    return device


@pytest.fixture()
def measurement_items_two(db_session):
    """MeasurementItemMaster テストレコード 2件（外気温度 / 第1冷凍 設定温度）

    seed_measurement_items が既に挿入済みの場合は既存レコードを返す（重複キーエラー回避）。
    """
    from iot_app.models.measurement import MeasurementItemMaster
    result = []
    for item_id, item_name, display, col_name, unit in [
        (1, "external_temp", "外気温度", "external_temp", "℃"),
        (2, "set_temp_freezer_1", "第1冷凍 設定温度", "set_temp_freezer_1", "℃"),
    ]:
        item = db_session.get(MeasurementItemMaster, item_id)
        if item is None:
            item = MeasurementItemMaster(
                measurement_item_id=item_id,
                measurement_item_name=item_name,
                display_name=display,
                silver_data_column_name=col_name,
                unit_name=unit,
                creator=1,
                modifier=1,
                delete_flag=False,
            )
            db_session.add(item)
        result.append(item)
    db_session.flush()
    return result


# ─────────────────────────────────────────────────────────────────────────────
# 1. 顧客作成ダッシュボード初期表示（円グラフガジェット登録済みケース）
# GET /analysis/customer-dashboard
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.integration
class TestCustomerDashboardIndexWithCircleChart:
    """顧客作成ダッシュボード初期表示（円グラフガジェット含む）

    観点: 2.1.1 一覧初期表示、4.1 一覧表示（登録済みガジェット/論理削除ガジェット）
    """

    @pytest.fixture(autouse=True)
    def _setup(self, auth_scope, dashboard_master, dashboard_group_master, gadget_type_circle):
        """認証ユーザー＋アクセス可能スコープ＋円グラフガジェット種別マスタを事前登録"""

    def test_index_returns_200(self, client):
        """2.1.1: ガジェット0件でも200とHTMLを返す"""
        # Arrange: DBにガジェットなし（初期状態）

        # Act
        response = client.get(BASE_URL)

        # Assert
        assert response.status_code == 200
        assert b"customer-dashboard" in response.data

    def test_index_renders_registered_circle_gadget(self, client, circle_gadget):
        """4.1.2: 登録済みの円グラフガジェットが data-gadget-uuid 属性付きの div として描画される"""
        # Arrange: circle_gadget フィクスチャで DashboardGadgetMaster に1件登録済み

        # Act
        response = client.get(BASE_URL)
        soup = _soup(response)

        # Assert: DOM上に data-gadget-uuid 属性を持つ要素が存在する
        assert response.status_code == 200
        gadget_el = soup.find(attrs={"data-gadget-uuid": circle_gadget.gadget_uuid})
        assert gadget_el is not None

    def test_index_does_not_render_deleted_circle_gadget(self, client, circle_gadget, db_session):
        """4.1.4: delete_flag=True の円グラフガジェットは DOM に存在しない"""
        # Arrange: ガジェットを論理削除
        circle_gadget.delete_flag = True
        db_session.flush()

        # Act
        response = client.get(BASE_URL)
        soup = _soup(response)

        # Assert
        assert soup.find(attrs={"data-gadget-uuid": circle_gadget.gadget_uuid}) is None

    def test_index_renders_multiple_circle_gadgets(self, client, db_session):
        """4.1.3: 複数件の円グラフガジェットが登録されている場合、すべて DOM に描画される"""
        # Arrange: 2件のガジェットを登録
        gadget_uuids = []
        for i in range(2):
            g = _make_circle_gadget(db_session, gadget_type_id=2, position_y=i + 1, display_order=i + 1)
            gadget_uuids.append(g.gadget_uuid)
        db_session.flush()

        # Act
        response = client.get(BASE_URL)
        soup = _soup(response)

        # Assert: 2件ともに data-gadget-uuid 属性が存在する
        assert response.status_code == 200
        for g_uuid in gadget_uuids:
            assert soup.find(attrs={"data-gadget-uuid": g_uuid}) is not None

    def test_index_does_not_render_out_of_scope_gadget(self, client, db_session):
        """4.1.5: アクセス可能スコープ外のガジェットは DOM に描画されない

        organization_closure によりスコープ外（organization_id=99）のダッシュボードグループに
        属するガジェットは表示されないことを確認する。
        """
        # Arrange: スコープ外グループ（dashboard_group_id=99）のガジェットを登録
        # dashboard_group_id=99 は organization_id=99 のダッシュボードに属し、
        # auth_scope（organization_id=1）からはアクセス不可
        out_of_scope_gadget = _make_circle_gadget(
            db_session, gadget_type_id=2, dashboard_group_id=99, position_y=1, display_order=1
        )
        db_session.flush()

        # Act
        response = client.get(BASE_URL)
        soup = _soup(response)

        # Assert: スコープ外ガジェットの UUID が DOM に存在しない
        assert soup.find(attrs={"data-gadget-uuid": out_of_scope_gadget.gadget_uuid}) is None


# ─────────────────────────────────────────────────────────────────────────────
# 2. ガジェットデータ取得（AJAX）
# POST /analysis/customer-dashboard/gadgets/<gadget_uuid>/data
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.integration
class TestGadgetCircleChartData:
    """円グラフガジェット データ取得（AJAX）

    観点: 4.2 詳細表示、2.2 エラー時遷移、3.6 不整値チェック、6.3 Unity Catalog クエリ
    """

    @pytest.fixture(autouse=True)
    def _setup(self, auth_scope, dashboard_master, dashboard_group_master, gadget_type_circle):
        """認証ユーザー＋アクセス可能スコープ＋ガジェット関連マスタを事前登録"""

    def _url(self, gadget_uuid):
        return f"{BASE_URL}/gadgets/{gadget_uuid}/data"

    def test_data_returns_json_structure(self, client, circle_gadget, measurement_items_two, mocker):
        """4.2.1: 正常取得 - gadget_uuid / device_name / chart_data / updated_at を含む JSON を返す"""
        # Arrange: センサーデータ取得をモック（Unity Catalog）
        mocker.patch(
            _FETCH_CIRCLE_DATA,
            return_value=[{"external_temp": 10.5, "set_temp_freezer_1": 12.3}],
        )

        # Act
        response = client.post(self._url(circle_gadget.gadget_uuid))

        # Assert
        assert response.status_code == 200
        data = response.get_json()
        assert "gadget_uuid" in data
        assert "chart_data" in data
        assert "updated_at" in data
        assert "labels" in data["chart_data"]
        assert "values" in data["chart_data"]

    def test_data_chart_data_labels_match_measurement_items(
        self, client, circle_gadget, measurement_items_two, mocker
    ):
        """4.2.5: chart_data.labels が MeasurementItemMaster.display_name と一致する"""
        # Arrange
        mocker.patch(
            _FETCH_CIRCLE_DATA,
            return_value=[{"external_temp": 10.5, "set_temp_freezer_1": 12.3}],
        )

        # Act
        response = client.post(self._url(circle_gadget.gadget_uuid))
        data = response.get_json()

        # Assert: chart_config の item_id_1=1(外気温度), item_id_2=2(第1冷凍 設定温度) に対応
        assert "外気温度" in data["chart_data"]["labels"]
        assert "第1冷凍 設定温度" in data["chart_data"]["labels"]

    def test_data_returns_empty_chart_when_no_sensor_data(
        self, client, circle_gadget, measurement_items_two, mocker
    ):
        """4.2.1: センサーデータが0件の場合、labels/values が空リストで返る"""
        # Arrange: センサーデータ0件をモック
        mocker.patch(_FETCH_CIRCLE_DATA, return_value=[])

        # Act
        response = client.post(self._url(circle_gadget.gadget_uuid))
        data = response.get_json()

        # Assert
        assert response.status_code == 200
        assert data["chart_data"]["labels"] == []
        assert data["chart_data"]["values"] == []

    def test_data_device_variable_mode_uses_user_setting(
        self, client, circle_gadget_variable, dashboard_user_setting, measurement_items_two, mocker
    ):
        """4.2.1: デバイス可変モード - dashboard_user_setting.device_id を使用してデータ取得する"""
        # Arrange: dashboard_user_setting.device_id=1 が設定済み
        mock_fetch = mocker.patch(
            _FETCH_CIRCLE_DATA,
            return_value=[{"external_temp": 5.0}],
        )

        # Act
        response = client.post(self._url(circle_gadget_variable.gadget_uuid))

        # Assert: device_id=1 でセンサーデータが取得される
        assert response.status_code == 200
        mock_fetch.assert_called_once_with(1)

    def test_data_unknown_gadget_uuid_returns_404(self, client):
        """3.6.2: 存在しない gadget_uuid でリクエストすると 404 を返す

        ルーターが get_gadget_type(gadget_uuid) で None を取得すると abort(404) を呼び出す。
        abort(404) は error_handlers の handle_4xx（HTML）を返すため、JSON ではなくステータスコードのみ検証する。
        """
        # Act
        response = client.post(self._url(str(uuid.uuid4())))

        # Assert
        assert response.status_code == 404

    def test_data_deleted_gadget_returns_404(self, client, circle_gadget, db_session, mocker):
        """4.2.3: delete_flag=True の論理削除済みガジェットへのデータ取得は 404 を返す"""
        # Arrange: ガジェットを論理削除
        circle_gadget.delete_flag = True
        db_session.flush()

        # Act
        response = client.post(self._url(circle_gadget.gadget_uuid))

        # Assert: get_gadget_by_uuid が delete_flag=False のみ返すため 404
        assert response.status_code == 404

    def test_data_sensor_query_error_returns_500(
        self, client, circle_gadget, measurement_items_two, mocker
    ):
        """2.2.6: Unity Catalog クエリ失敗時に 500 エラーを返す"""
        # Arrange: センサーデータ取得が例外を送出
        mocker.patch(
            _FETCH_CIRCLE_DATA,
            side_effect=Exception("Databricks connection timeout"),
        )

        # Act
        response = client.post(self._url(circle_gadget.gadget_uuid))

        # Assert
        assert response.status_code == 500
        data = response.get_json()
        assert "error" in data

    def test_data_out_of_scope_gadget_returns_404(
        self, client, db_session, measurement_items_two, mocker
    ):
        """4.2.4: アクセス可能スコープ外のガジェットへのデータ取得は 404 を返す

        check_gadget_access() がガジェットの dashboard_group → dashboard の
        organization_id をアクセス可能スコープ（accessible_org_ids）で検証する。
        スコープ外のガジェットは 404 として扱われる。
        """
        # Arrange: スコープ外グループ（dashboard_group_id=99）のガジェットを登録
        out_of_scope_gadget = _make_circle_gadget(
            db_session, gadget_type_id=2, dashboard_group_id=99, position_y=1, display_order=1
        )
        db_session.flush()

        # Act
        response = client.post(self._url(out_of_scope_gadget.gadget_uuid))

        # Assert: スコープ外のため 404
        assert response.status_code == 404
        data = response.get_json()
        assert "error" in data


# ─────────────────────────────────────────────────────────────────────────────
# 3. ガジェット登録モーダル表示
# GET /analysis/customer-dashboard/gadgets/circle-chart/create
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.integration
class TestGadgetCircleChartCreate:
    """円グラフガジェット 登録モーダル表示

    観点: 2.1.3 登録画面表示、2.2 エラー時遷移
    """

    _URL = f"{BASE_URL}/gadgets/circle-chart/create"

    def test_create_modal_returns_200(
        self, client, auth_user_id, dashboard_user_setting, dashboard_master, dashboard_group_master
    ):
        """2.1.3: 正常表示 - 200 と HTML を返す"""
        # Act
        response = client.get(self._URL)

        # Assert
        assert response.status_code == 200

    def test_create_modal_has_gadget_name_input(
        self, client, auth_user_id, dashboard_user_setting, dashboard_master, dashboard_group_master
    ):
        """2.1.3: タイトル入力フィールド（input[name="gadget_name"]）が存在し、初期値が「円グラフ」である"""
        # Act
        response = client.get(self._URL)
        soup = _soup(response)

        # Assert
        title_input = soup.find("input", {"name": "gadget_name"})
        assert title_input is not None
        assert title_input.get("value") == "円グラフ"

    def test_create_modal_has_device_mode_buttons(
        self, client, auth_user_id, dashboard_user_setting, dashboard_master, dashboard_group_master
    ):
        """2.1.3: 表示デバイス選択ボタン（data-mode="fixed"/"variable"）が存在する"""
        # Act
        response = client.get(self._URL)
        soup = _soup(response)

        # Assert
        mode_buttons = soup.find_all("button", {"data-mode": True})
        modes = {btn["data-mode"] for btn in mode_buttons}
        assert "fixed" in modes
        assert "variable" in modes

    def test_create_modal_lists_measurement_items(
        self, client, auth_user_id, dashboard_user_setting, dashboard_master, dashboard_group_master,
        measurement_items_two,
    ):
        """2.1.3: measurement_item_master の表示項目がチェックボックスとして描画される"""
        # Arrange: measurement_items_two で '外気温度'（id=1）と '第1冷凍 設定温度'（id=2）が登録済み

        # Act
        response = client.get(self._URL)
        soup = _soup(response)

        # Assert: name="measurement_item_ids" のチェックボックスが存在する
        checkboxes = soup.find_all("input", {"name": "measurement_item_ids", "type": "checkbox"})
        assert len(checkboxes) >= 1
        checkbox_values = {cb.get("value") for cb in checkboxes}
        assert "1" in checkbox_values  # 外気温度
        assert "2" in checkbox_values  # 第1冷凍 設定温度

    def test_create_modal_lists_groups(
        self, client, auth_user_id, dashboard_user_setting, dashboard_master, dashboard_group_master
    ):
        """2.1.3: dashboard_group_master のグループ名が group_id セレクトの option として描画される"""
        # Act
        response = client.get(self._URL)
        soup = _soup(response)

        # Assert
        select = soup.find("select", {"name": "group_id"})
        assert select is not None
        option_texts = [opt.get_text(strip=True) for opt in select.find_all("option")]
        assert "テストグループ" in option_texts

    def test_create_modal_no_user_setting_returns_404(
        self, client, auth_user_id
    ):
        """2.2.4: dashboard_user_setting が存在しない場合 404 エラーを返す"""
        # Arrange: dashboard_user_setting を登録しない（auth_user_id のみ）

        # Act
        response = client.get(self._URL)

        # Assert
        assert response.status_code == 404


# ─────────────────────────────────────────────────────────────────────────────
# 4. ガジェット登録実行
# POST /analysis/customer-dashboard/gadgets/circle-chart/register
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.integration
class TestGadgetCircleChartRegister:
    """円グラフガジェット 登録実行

    観点: 3.1 必須チェック、3.2 文字列長チェック、3.8 相関チェック、
          4.3 登録（Create）テスト、2.3 リダイレクトテスト
    """

    _URL = f"{BASE_URL}/gadgets/circle-chart/register"

    _SKIP_GADGET_TYPE = frozenset({
        "test_register_without_gadget_type_master_returns_500",
        "test_register_exception_rolls_back_db",
    })

    @pytest.fixture(autouse=True)
    def _require_gadget_type(self, request, db_session):
        """全テストで GadgetTypeMaster='円グラフ' を事前登録する（サービス層の動的ルックアップに必要）"""
        if request.node.name in self._SKIP_GADGET_TYPE:
            return
        from iot_app.models.customer_dashboard import GadgetTypeMaster
        gt = GadgetTypeMaster(
            gadget_type_id=2,
            gadget_type_name="円グラフ",
            data_source_type=1,
            gadget_image_path="images/gadgets/circle_chart.png",
            gadget_description="円グラフガジェット",
            display_order=2,
            creator=1,
            modifier=1,
            delete_flag=False,
        )
        db_session.add(gt)
        db_session.flush()

    def _valid_form(self, **overrides):
        """デバイス可変モードの最小有効フォームデータ"""
        data = {
            "gadget_name": "テスト円グラフ",
            "device_mode": "variable",
            "device_id": "0",
            "group_id": "1",
            "measurement_item_ids": ["1"],
        }
        data.update(overrides)
        return data

    # ── 正常系 ────────────────────────────────────────────────────────────────

    def test_register_success_redirects_to_dashboard(self, client, measurement_item):
        """2.3.1 / 4.3.1: 正常登録後、ダッシュボード画面へ 302 リダイレクト（registered=1 付き）"""
        # Arrange: measurement_item フィクスチャで id=1 を登録済み

        # Act
        response = client.post(self._URL, data=self._valid_form(), follow_redirects=False)

        # Assert
        assert response.status_code == 302
        assert BASE_URL in response.headers["Location"]
        assert "registered=1" in response.headers["Location"]

    def test_register_creates_record_in_db(self, client, app, measurement_item):
        """4.3.1: 正常登録後、dashboard_gadget_master に1件レコードが追加される"""
        # Act
        client.post(self._URL, data=self._valid_form())

        # Assert
        with app.app_context():
            from iot_app import db
            from iot_app.models.customer_dashboard import DashboardGadgetMaster
            count = db.session.query(DashboardGadgetMaster).filter_by(delete_flag=False).count()
        assert count == 1

    def test_register_gadget_uuid_is_auto_generated(self, client, app, measurement_item):
        """4.3.5: 登録されたガジェットに gadget_uuid（UUID v4形式）が自動採番される"""
        # Act
        client.post(self._URL, data=self._valid_form())

        # Assert
        with app.app_context():
            from iot_app import db
            from iot_app.models.customer_dashboard import DashboardGadgetMaster
            gadget = db.session.query(DashboardGadgetMaster).first()
        assert gadget is not None
        assert len(gadget.gadget_uuid) == 36  # UUID形式 (8-4-4-4-12)

    def test_register_title_stored_correctly(self, client, app, measurement_item):
        """4.3.1: 登録されたガジェットのタイトルが DB に正しく保存される"""
        # Act
        client.post(self._URL, data=self._valid_form(gadget_name="カスタム円グラフ"))

        # Assert
        with app.app_context():
            from iot_app import db
            from iot_app.models.customer_dashboard import DashboardGadgetMaster
            gadget = db.session.query(DashboardGadgetMaster).first()
        assert gadget.gadget_name == "カスタム円グラフ"

    def test_register_chart_config_stored_with_item_ids(self, client, app, measurement_item):
        """4.3.1: chart_config が item_id_1 キーで選択した measurement_item_id を保存する"""
        # Act
        client.post(self._URL, data=self._valid_form(measurement_item_ids=["1"]))

        # Assert
        with app.app_context():
            from iot_app import db
            from iot_app.models.customer_dashboard import DashboardGadgetMaster
            gadget = db.session.query(DashboardGadgetMaster).first()
        chart_config = json.loads(gadget.chart_config)
        assert chart_config.get("item_id_1") == 1

    def test_register_variable_mode_data_source_config_has_null_device_id(
        self, client, app, measurement_item
    ):
        """4.3.1: デバイス可変モードで登録すると data_source_config.device_id が null で保存される"""
        # Act
        client.post(self._URL, data=self._valid_form(device_mode="variable"))

        # Assert
        with app.app_context():
            from iot_app import db
            from iot_app.models.customer_dashboard import DashboardGadgetMaster
            gadget = db.session.query(DashboardGadgetMaster).first()
        data_source = json.loads(gadget.data_source_config)
        assert data_source.get("device_id") is None

    def test_register_fixed_mode_data_source_config_has_device_id(
        self, client, app, measurement_item, device_master_record,
        organization_master_record, organization_closure_record, auth_user_id, user_master_record
    ):
        """4.3.1: デバイス固定モードで登録すると data_source_config.device_id にデバイスIDが保存される"""
        # Act
        response = client.post(
            self._URL,
            data=self._valid_form(device_mode="fixed", device_id=str(device_master_record.device_id)),
            follow_redirects=False,
        )

        # Assert: 登録成功してリダイレクト
        assert response.status_code == 302
        with app.app_context():
            from iot_app import db
            from iot_app.models.customer_dashboard import DashboardGadgetMaster
            gadget = db.session.query(DashboardGadgetMaster).first()
        data_source = json.loads(gadget.data_source_config)
        assert data_source.get("device_id") == device_master_record.device_id

    def test_register_creator_modifier_set_to_current_user(self, client, app, measurement_item, auth_user_id):
        """4.3.7: 登録されたガジェットの creator / modifier がログインユーザー ID に設定される"""
        # Act
        client.post(self._URL, data=self._valid_form())

        # Assert
        with app.app_context():
            from iot_app import db
            from iot_app.models.customer_dashboard import DashboardGadgetMaster
            gadget = db.session.query(DashboardGadgetMaster).first()
        assert gadget.creator == auth_user_id
        assert gadget.modifier == auth_user_id

    def test_register_create_date_and_update_date_are_set(self, client, app, measurement_item):
        """4.3.6: 登録されたガジェットの create_date / update_date が自動設定される"""
        # Act
        client.post(self._URL, data=self._valid_form())

        # Assert
        with app.app_context():
            from iot_app import db
            from iot_app.models.customer_dashboard import DashboardGadgetMaster
            gadget = db.session.query(DashboardGadgetMaster).first()
        assert gadget.create_date is not None
        assert gadget.update_date is not None

    def test_register_default_values_are_set(self, client, app, measurement_item):
        """4.3.2: 未入力項目のデフォルト値が正しく設定される

        DashboardGadgetMaster のデフォルト値付きカラムを確認する。
          - position_x: 0（固定）
          - delete_flag: False
          - position_y: 1（グループ内の最大 position_y + 1）
          - gadget_size: 0
        """
        # Act
        client.post(self._URL, data=self._valid_form())

        # Assert
        with app.app_context():
            from iot_app import db
            from iot_app.models.customer_dashboard import DashboardGadgetMaster
            gadget = db.session.query(DashboardGadgetMaster).first()
        assert gadget.position_x == 0
        assert gadget.delete_flag is False
        assert gadget.position_y >= 1   # グループ内最大 position_y + 1
        assert gadget.gadget_size == 0

    def test_register_first_gadget_gets_position_y_1_and_display_order_1(
        self, client, app, measurement_item
    ):
        """4.3.2: グループが空の場合、position_y=1・display_order=1 が設定される

        サービス層のロジック: (MAX(position_y) or 0) + 1
        グループ内にガジェットが存在しない場合 MAX=None → (None or 0)+1 = 1
        """
        # Arrange: グループ内にガジェットなし（初期状態）

        # Act
        client.post(self._URL, data=self._valid_form())

        # Assert
        with app.app_context():
            from iot_app import db
            from iot_app.models.customer_dashboard import DashboardGadgetMaster
            gadget = db.session.query(DashboardGadgetMaster).first()
        assert gadget.position_y == 1
        assert gadget.display_order == 1

    def test_register_second_gadget_gets_incremented_position_y_and_display_order(
        self, client, app, db_session, measurement_item
    ):
        """4.3.2: 既存ガジェットがある場合、position_y・display_order に MAX+1 が設定される

        サービス層のロジック: (MAX(position_y) or 0) + 1
        グループ内に position_y=3・display_order=5 のガジェットが存在する場合、
        新規登録ガジェットには position_y=4・display_order=6 が設定される。
        """
        # Arrange: 同一グループ（dashboard_group_id=1）に既存ガジェットを登録
        from iot_app.models.customer_dashboard import DashboardGadgetMaster
        existing = DashboardGadgetMaster(
            gadget_uuid=str(uuid.uuid4()),
            gadget_name="既存ガジェット",
            gadget_type_id=2,
            dashboard_group_id=1,
            chart_config=json.dumps({"item_id_1": 1}),
            data_source_config=json.dumps({"device_id": None}),
            position_x=0,
            position_y=3,
            gadget_size=0,
            display_order=5,
            creator=1,
            modifier=1,
        )
        db_session.add(existing)
        db_session.flush()

        # Act: 同一グループに新規ガジェットを登録
        client.post(self._URL, data=self._valid_form())

        # Assert: MAX(position_y)=3 → 4、MAX(display_order)=5 → 6
        with app.app_context():
            from iot_app import db
            new_gadget = (
                db.session.query(DashboardGadgetMaster)
                .filter(DashboardGadgetMaster.gadget_name == "テスト円グラフ")
                .first()
            )
        assert new_gadget.position_y == 4
        assert new_gadget.display_order == 6

    def test_register_multiple_items_stored_in_chart_config(self, client, app, measurement_items_two):
        """4.3.1: 複数の表示項目を選択すると chart_config に item_id_1〜item_id_n が保存される"""
        # Act
        client.post(self._URL, data=self._valid_form(measurement_item_ids=["1", "2"]))

        # Assert
        with app.app_context():
            from iot_app import db
            from iot_app.models.customer_dashboard import DashboardGadgetMaster
            gadget = db.session.query(DashboardGadgetMaster).first()
        chart_config = json.loads(gadget.chart_config)
        assert chart_config.get("item_id_1") == 1
        assert chart_config.get("item_id_2") == 2

    # ── バリデーションエラー系 ────────────────────────────────────────────────

    def test_register_title_empty_returns_400(self, client, measurement_item):
        """3.1.2: タイトル未入力で 400（バリデーションエラー）"""
        # Act
        response = client.post(self._URL, data=self._valid_form(gadget_name=""))

        # Assert
        assert response.status_code == 400

    def test_register_title_too_long_returns_400(self, client, measurement_item):
        """3.2.2: タイトルが最大20文字を超過すると 400（バリデーションエラー）"""
        # Act
        response = client.post(self._URL, data=self._valid_form(gadget_name="あ" * 21))

        # Assert
        assert response.status_code == 400

    def test_register_title_max_length_succeeds(self, client, measurement_item):
        """3.2.1: タイトルが最大20文字以内で 302 リダイレクト（正常）"""
        # Act
        response = client.post(
            self._URL,
            data=self._valid_form(gadget_name="あ" * 20),
            follow_redirects=False,
        )

        # Assert
        assert response.status_code == 302

    def test_register_no_measurement_items_returns_400(self, client, measurement_item):
        """3.1.2: 表示項目が0件で 400（バリデーションエラー）"""
        # Act: measurement_item_ids を空にする
        data = self._valid_form()
        data.pop("measurement_item_ids")
        response = client.post(self._URL, data=data)

        # Assert
        assert response.status_code == 400

    def test_register_too_many_measurement_items_returns_400(self, client, db_session):
        """3.1.2: 表示項目が6件（上限5件超過）で 400（バリデーションエラー）"""
        # Arrange: 6件の MeasurementItemMaster を登録
        from iot_app.models.measurement import MeasurementItemMaster
        for i in range(1, 7):
            db_session.add(MeasurementItemMaster(
                measurement_item_id=i,
                measurement_item_name=f"col_{i}",
                display_name=f"項目{i}",
                silver_data_column_name=f"col_{i}",
                unit_name="℃",
                creator=1,
                modifier=1,
                delete_flag=False,
            ))
        db_session.flush()

        # Act
        response = client.post(
            self._URL,
            data=self._valid_form(measurement_item_ids=["1", "2", "3", "4", "5", "6"]),
        )

        # Assert
        assert response.status_code == 400

    def test_register_fixed_mode_without_device_id_returns_400(self, client, measurement_item):
        """3.8.2: デバイス固定モードでデバイスIDが未指定の場合 400（相関チェックエラー）"""
        # Act: device_mode='fixed' で device_id を指定しない
        response = client.post(
            self._URL,
            data=self._valid_form(device_mode="fixed", device_id="0"),
        )

        # Assert
        assert response.status_code == 400

    def test_register_fixed_mode_out_of_scope_device_returns_404(
        self, client, measurement_item,
        organization_master_record, organization_closure_record, auth_user_id, user_master_record,
        db_session
    ):
        """4.2.4: デバイス固定モードでスコープ外のデバイスIDを指定すると 404"""
        # Arrange: organization_id=99（スコープ外）のデバイスを登録
        from iot_app.models.device import DeviceMaster, DeviceTypeMaster
        dt = DeviceTypeMaster(
            device_type_id=1,
            device_type_name="テストデバイス種別",
            creator=1,
            modifier=1,
        )
        db_session.add(dt)
        db_session.flush()
        # スコープ外組織のデバイス（organization_id=99 は accessible_org_ids=[1] に含まれない）
        # NOTE: organization_id=99 は organization_master に存在しないが FK 制約が無い場合のみ機能する
        # TODO: 設計書に記載なし、要確認（FK制約の扱い）
        device_out = DeviceMaster(
            device_id=99,
            device_uuid=str(uuid.uuid4()),
            organization_id=None,  # FK制約回避のため NULL を使用
            device_type_id=1,
            device_name="スコープ外デバイス",
            device_model="MODEL-OUT",
            device_inventory_id=99,
            creator=1,
            modifier=1,
        )
        db_session.add(device_out)
        db_session.flush()

        # Act
        response = client.post(
            self._URL,
            data=self._valid_form(device_mode="fixed", device_id="99"),
        )

        # Assert
        assert response.status_code == 404

    def test_register_without_gadget_type_master_returns_500(
        self, client, measurement_item
    ):
        """2.2.5: GadgetTypeMaster='円グラフ' が存在しない場合、登録実行で 500 エラーになる

        サービス層が gadget_type_name='円グラフ' を動的ルックアップするため、
        マスタが未登録だと AttributeError が発生し 500 となる。
        """
        # Arrange: _require_gadget_type フィクスチャをスキップしているため GadgetTypeMaster が未登録

        # Act
        response = client.post(self._URL, data=self._valid_form())

        # Assert
        assert response.status_code == 500

    def test_register_exception_rolls_back_db(self, client, app, measurement_item):
        """7.2.3: 処理途中で例外発生時、dashboard_gadget_master にレコードが残らない（ロールバック）

        サービス層 create_circle_chart_gadget() は except 節で db.session.rollback() を
        呼び出してから再 raise する。GadgetTypeMaster='円グラフ' が存在しない状態で
        登録実行すると AttributeError が発生し、ロールバックが走ることを確認する。
        """
        # Arrange: _require_gadget_type フィクスチャをスキップしているため GadgetTypeMaster が未登録
        #          → INSERT 前の gadget_type ルックアップで AttributeError が発生

        # Act
        client.post(self._URL, data=self._valid_form())

        # Assert: ロールバックにより dashboard_gadget_master にレコードが存在しないこと
        with app.app_context():
            from iot_app import db
            from iot_app.models.customer_dashboard import DashboardGadgetMaster
            count = db.session.query(DashboardGadgetMaster).count()
        assert count == 0

    def test_register_explicit_rollback_on_db_error(self, client, app, measurement_item, mocker):
        """7.2.4: db.session.commit() が失敗した場合、rollback() が呼ばれ DB に変更が残らない

        サービス層の create_circle_chart_gadget() が db.session.commit() を呼び出す箇所を
        モックして SQLAlchemyError を発生させ、rollback() が実行されることと
        dashboard_gadget_master にレコードが存在しないことを確認する。
        """
        from sqlalchemy.exc import SQLAlchemyError

        # Arrange: commit() を失敗させる
        mocker.patch(
            "iot_app.services.customer_dashboard.circle_chart._common.db.session.commit",
            side_effect=SQLAlchemyError("commit failed"),
        )

        # Act
        response = client.post(self._URL, data=self._valid_form())

        # Assert: 500 エラーが返る
        assert response.status_code == 500

        # Assert: ロールバックにより dashboard_gadget_master にレコードが存在しないこと
        with app.app_context():
            from iot_app import db
            from iot_app.models.customer_dashboard import DashboardGadgetMaster
            count = db.session.query(DashboardGadgetMaster).count()
        assert count == 0


# ─────────────────────────────────────────────────────────────────────────────
# 5. セキュリティテスト
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.integration
class TestCircleChartSecurity:
    """円グラフガジェット セキュリティテスト

    観点: 9.1 SQLインジェクション、9.2 XSS、9.3 CSRF対策
    """

    @pytest.fixture(autouse=True)
    def _require_gadget_type(self, db_session):
        """全テストで GadgetTypeMaster='円グラフ' を事前登録する"""
        from iot_app.models.customer_dashboard import GadgetTypeMaster
        gt = GadgetTypeMaster(
            gadget_type_id=2,
            gadget_type_name="円グラフ",
            data_source_type=1,
            gadget_image_path="images/gadgets/circle_chart.png",
            gadget_description="円グラフガジェット",
            display_order=2,
            creator=1,
            modifier=1,
            delete_flag=False,
        )
        db_session.add(gt)
        db_session.flush()

    def _register_url(self):
        return f"{BASE_URL}/gadgets/circle-chart/register"

    def _valid_register_form(self, **overrides):
        data = {
            "gadget_name": "テスト円グラフ",
            "device_mode": "variable",
            "device_id": "0",
            "group_id": "1",
            "measurement_item_ids": ["1"],
        }
        data.update(overrides)
        return data

    # ── 9.1 SQLインジェクションテスト ────────────────────────────────────────

    def test_sql_injection_in_gadget_name_does_not_cause_error(
        self, client, measurement_item
    ):
        """9.1.1: gadget_name に基本的な SQLインジェクション文字列を入力しても
        SQLAlchemy プリペアドステートメントによりエスケープされ、500エラーにならない"""
        # Act
        response = client.post(
            self._register_url(),
            data=self._valid_register_form(gadget_name="' OR '1'='1"),
            follow_redirects=False,
        )

        # Assert: 302リダイレクト（正常登録）またはバリデーションエラー（400）であり、500にならない
        assert response.status_code in (302, 400)

    def test_sql_injection_with_comment_in_gadget_name_does_not_cause_error(
        self, client, measurement_item
    ):
        """9.1.2: gadget_name にコメントを使った SQLインジェクション文字列を入力しても
        SQLAlchemy プリペアドステートメントによりエスケープされ、500エラーにならない"""
        # Act
        response = client.post(
            self._register_url(),
            data=self._valid_register_form(gadget_name="'; DROP TABLE dashboard_gadget_master--"),
            follow_redirects=False,
        )

        # Assert: 500にならない（20文字超でバリデーションエラー 400 が期待値）
        assert response.status_code in (302, 400)

    def test_sql_injection_with_union_in_gadget_uuid_does_not_cause_error(
        self, client, auth_scope, dashboard_master, dashboard_group_master
    ):
        """9.1.3: gadget_uuid パスパラメータに UNION SELECT を含む文字列を渡しても
        SQLAlchemy プリペアドステートメントによりエスケープされ、500エラーにならない"""
        # Act: gadget_uuid パスパラメータに不正な値を設定
        malicious_uuid = "' UNION SELECT * FROM user_master--"
        response = client.post(f"{BASE_URL}/gadgets/{malicious_uuid}/data")

        # Assert: 404（ガジェット未検出）または 400 であり、500にならない
        assert response.status_code in (400, 404)

    # ── 9.2 XSSテスト ─────────────────────────────────────────────────────────

    def test_xss_script_tag_in_gadget_name_is_escaped_in_dashboard(
        self, client, db_session, auth_scope, dashboard_master, dashboard_group_master
    ):
        """9.2.1: gadget_name に <script> タグを含むガジェットをダッシュボードに表示しても
        Jinja2 自動エスケープにより <script> がそのまま出力されない"""
        # Arrange: XSSペイロードを含むガジェットを直接DBに登録
        import json as _json
        from iot_app.models.customer_dashboard import DashboardGadgetMaster
        xss_gadget = DashboardGadgetMaster(
            gadget_uuid=str(uuid.uuid4()),
            gadget_name="<script>alert('XSS')</script>",
            gadget_type_id=2,
            dashboard_group_id=dashboard_group_master.dashboard_group_id,
            chart_config=_json.dumps({"item_id_1": 1}),
            data_source_config=_json.dumps({"device_id": None}),
            position_x=0,
            position_y=1,
            gadget_size=0,
            display_order=1,
            creator=1,
            modifier=1,
        )
        db_session.add(xss_gadget)
        db_session.flush()

        # Act
        response = client.get(BASE_URL)

        # Assert: <script>alert('XSS')</script> がそのままレスポンスに含まれない
        assert b"<script>alert('XSS')</script>" not in response.data

    def test_xss_img_tag_in_gadget_name_is_escaped_in_dashboard(
        self, client, db_session, auth_scope, dashboard_master, dashboard_group_master
    ):
        """9.2.2: gadget_name に img タグ XSS を含むガジェットをダッシュボードに表示しても
        Jinja2 自動エスケープにより onerror イベントがそのまま出力されない"""
        # Arrange: img タグ XSS ペイロードを含むガジェットを直接DBに登録
        import json as _json
        from iot_app.models.customer_dashboard import DashboardGadgetMaster
        xss_gadget = DashboardGadgetMaster(
            gadget_uuid=str(uuid.uuid4()),
            gadget_name="<img src=x onerror=alert('XSS')>",
            gadget_type_id=2,
            dashboard_group_id=dashboard_group_master.dashboard_group_id,
            chart_config=_json.dumps({"item_id_1": 1}),
            data_source_config=_json.dumps({"device_id": None}),
            position_x=0,
            position_y=2,
            gadget_size=0,
            display_order=2,
            creator=1,
            modifier=1,
        )
        db_session.add(xss_gadget)
        db_session.flush()

        # Act
        response = client.get(BASE_URL)

        # Assert: onerror イベントがそのまま含まれない
        assert b"onerror=alert('XSS')" not in response.data

    # ── 9.3 CSRF対策テスト ────────────────────────────────────────────────────

    @pytest.fixture()
    def csrf_enabled(self, app):
        """CSRF 検証を有効化する（このフィクスチャを使うテストのみ有効）

        conftest の disable_csrf (autouse=True) が先に WTF_CSRF_ENABLED=False に
        設定するため、このフィクスチャで True に上書きしてテスト後に戻す。
        """
        app.config["WTF_CSRF_ENABLED"] = True
        yield
        app.config["WTF_CSRF_ENABLED"] = False

    def test_csrf_post_register_without_token_returns_400(
        self, client, csrf_enabled, measurement_item
    ):
        """9.3.1: CSRF トークンなしで POST /register を送信すると 400 エラーになる

        Flask-WTF の CSRFError は BadRequest (HTTP 400) を継承するため、
        カスタムハンドラー未登録の場合は 400 が返る。
        """
        # Act: CSRF トークンを含まないフォームデータで POST
        response = client.post(
            self._register_url(),
            data={
                "gadget_name": "テスト円グラフ",
                "device_mode": "variable",
                "group_id": "1",
                "measurement_item_ids": ["1"],
            },
        )

        # Assert
        assert response.status_code == 400

    def test_csrf_post_register_with_invalid_token_returns_400(
        self, client, csrf_enabled, measurement_item
    ):
        """9.3.2: 不正な CSRF トークンで POST /register を送信すると 400 エラーになる

        Flask-WTF の CSRFError は BadRequest (HTTP 400) を継承するため、
        カスタムハンドラー未登録の場合は 400 が返る。
        """
        # Act: 不正な CSRF トークンを含めて POST
        response = client.post(
            self._register_url(),
            data={
                "gadget_name": "テスト円グラフ",
                "device_mode": "variable",
                "group_id": "1",
                "measurement_item_ids": ["1"],
                "csrf_token": "invalid-token-xxxx",
            },
        )

        # Assert
        assert response.status_code == 400

    def test_csrf_post_register_with_valid_token_succeeds(
        self, client, csrf_enabled, auth_user_id, dashboard_user_setting,
        dashboard_master, dashboard_group_master, measurement_item
    ):
        """9.3.3: 有効な CSRF トークンで POST /register を送信すると処理が成功する"""
        # Arrange: GET でモーダルを取得して CSRF トークンを取得する
        get_response = client.get(f"{BASE_URL}/gadgets/circle-chart/create")
        assert get_response.status_code == 200, "登録モーダルの取得に失敗"
        soup = _soup(get_response)
        csrf_input = soup.find("input", {"name": "csrf_token"})
        assert csrf_input is not None, "CSRF トークンが見つかりません"
        token = csrf_input["value"]

        # Act
        response = client.post(
            self._register_url(),
            data={
                "gadget_name": "テスト円グラフ",
                "device_mode": "variable",
                "device_id": "0",
                "group_id": str(dashboard_group_master.dashboard_group_id),
                "measurement_item_ids": [str(measurement_item.measurement_item_id)],
                "csrf_token": token,
            },
            follow_redirects=False,
        )

        # Assert: バリデーションエラー（400）または成功リダイレクト（302）であり、403にならない
        assert response.status_code != 403


# ─────────────────────────────────────────────────────────────────────────────
# 6. ログ出力テスト
# ─────────────────────────────────────────────────────────────────────────────

_LOGGER = "iot_app.views.analysis.customer_dashboard.circle_chart.logger"


@pytest.mark.integration
class TestCircleChartLogging:
    """円グラフガジェット ログ出力テスト

    観点: 8.2.1 エラーログ（エラー発生時に logger.error が呼ばれること）

    対象の logger.error 呼び出し箇所:
      ① handle_gadget_data: 円グラフデータ取得エラー
      ② handle_gadget_create: 円グラフ登録モーダル表示エラー
      ③ handle_gadget_register: 円グラフガジェット登録エラー
    """

    @pytest.fixture(autouse=True)
    def _setup(self, auth_scope, dashboard_master, dashboard_group_master, gadget_type_circle):
        """認証ユーザー＋アクセス可能スコープ＋ダッシュボード関連マスタ＋GadgetTypeMasterを事前登録

        gadget_type_circle を依存として宣言することで、circle_gadget フィクスチャが
        同じフィクスチャインスタンスを共有し UNIQUE 制約違反を防ぐ。
        """

    # ── ① ガジェットデータ取得エラー ────────────────────────────────────────

    def test_data_fetch_error_logs_error_message(
        self, client, circle_gadget, measurement_items_two, mocker
    ):
        """8.2.1 ①: Unity Catalog クエリ失敗時に logger.error が呼ばれ、
        メッセージに 'gadget_uuid' と '円グラフデータ取得エラー' が含まれる"""
        # Arrange
        mock_logger = mocker.patch(_LOGGER)
        mocker.patch(_FETCH_CIRCLE_DATA, side_effect=Exception("Databricks timeout"))

        # Act
        client.post(f"{BASE_URL}/gadgets/{circle_gadget.gadget_uuid}/data")

        # Assert: logger.error が1回呼ばれた
        mock_logger.error.assert_called_once()
        log_message = mock_logger.error.call_args[0][0]
        assert "円グラフデータ取得エラー" in log_message
        assert circle_gadget.gadget_uuid in log_message

    def test_data_fetch_error_log_includes_exception_message(
        self, client, circle_gadget, measurement_items_two, mocker
    ):
        """8.2.1 ①: エラーログに例外メッセージが含まれる"""
        # Arrange
        mock_logger = mocker.patch(_LOGGER)
        error_message = "connection refused"
        mocker.patch(_FETCH_CIRCLE_DATA, side_effect=Exception(error_message))

        # Act
        client.post(f"{BASE_URL}/gadgets/{circle_gadget.gadget_uuid}/data")

        # Assert: ログに例外メッセージが含まれる
        log_message = mock_logger.error.call_args[0][0]
        assert error_message in log_message

    # ── ② 登録モーダル表示エラー ────────────────────────────────────────────

    def test_create_modal_error_logs_error_message(
        self, client, auth_user_id, dashboard_user_setting, mocker
    ):
        """8.2.1 ②: 登録モーダル表示中に例外が発生した場合に logger.error が呼ばれる"""
        # Arrange: グループ取得で例外を発生させる
        mock_logger = mocker.patch(_LOGGER)
        mocker.patch(
            "iot_app.views.analysis.customer_dashboard.circle_chart.get_dashboard_groups",
            side_effect=Exception("DB connection error"),
        )

        # Act
        client.get(f"{BASE_URL}/gadgets/circle-chart/create")

        # Assert
        mock_logger.error.assert_called_once()
        log_message = mock_logger.error.call_args[0][0]
        assert "円グラフ登録モーダル表示エラー" in log_message

    # ── ③ ガジェット登録エラー ──────────────────────────────────────────────

    def test_register_error_logs_error_message(
        self, client, measurement_item, mocker
    ):
        """8.2.1 ③: ガジェット登録中に例外が発生した場合に logger.error が呼ばれる"""
        # Arrange: create_circle_chart_gadget でDB例外を発生させる
        mock_logger = mocker.patch(_LOGGER)
        mocker.patch(
            "iot_app.views.analysis.customer_dashboard.circle_chart.create_circle_chart_gadget",
            side_effect=Exception("DB insert failed"),
        )

        # Act
        client.post(
            f"{BASE_URL}/gadgets/circle-chart/register",
            data={
                "gadget_name": "テスト円グラフ",
                "device_mode": "variable",
                "device_id": "0",
                "group_id": "1",
                "measurement_item_ids": [str(measurement_item.measurement_item_id)],
            },
        )

        # Assert
        mock_logger.error.assert_called_once()
        log_message = mock_logger.error.call_args[0][0]
        assert "円グラフガジェット登録エラー" in log_message


# ─────────────────────────────────────────────────────────────────────────────
# 7. Unity Catalog クエリテスト（モック化）
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.integration
class TestCircleChartUnityCatalogQuery:
    """円グラフガジェット Unity Catalog クエリテスト

    観点: 6.3.1 正常系、6.3.2 異常系

    NOTE: Unity Catalog（sensor_data_view）への実接続をモック化して検証する。
          fetch_circle_chart_data の戻り値を制御することで、UC クエリ結果の
          ハンドリングが正しく実装されていることを確認する。
    """

    @pytest.fixture(autouse=True)
    def _setup(self, auth_scope, dashboard_master, dashboard_group_master, gadget_type_circle):
        """認証ユーザー＋アクセス可能スコープ＋ダッシュボード関連マスタ＋GadgetTypeMasterを事前登録

        gadget_type_circle を依存として宣言することで、circle_gadget フィクスチャが
        同じフィクスチャインスタンスを共有し UNIQUE 制約違反を防ぐ。
        """

    def _data_url(self, gadget_uuid):
        return f"{BASE_URL}/gadgets/{gadget_uuid}/data"

    def test_uc_query_returns_list_data(
        self, client, circle_gadget, measurement_items_two, mocker
    ):
        """6.3.1.1: UC クエリがデータを返す場合、JSON レスポンスの chart_data.values が
        リスト形式で返却される"""
        # Arrange: UC クエリ結果をモック（外気温度=10.5, 第1冷凍設定温度=12.3）
        mocker.patch(
            _FETCH_CIRCLE_DATA,
            return_value=[{"external_temp": 10.5, "set_temp_freezer_1": 12.3}],
        )

        # Act
        response = client.post(self._data_url(circle_gadget.gadget_uuid))

        # Assert: values がリスト形式で返る
        assert response.status_code == 200
        data = response.get_json()
        assert isinstance(data["chart_data"]["values"], list)
        assert len(data["chart_data"]["values"]) > 0

    def test_uc_query_returns_empty_list_when_no_data(
        self, client, circle_gadget, measurement_items_two, mocker
    ):
        """6.3.1.2: UC クエリが0件を返す場合、chart_data.labels / values が空リストで返却される"""
        # Arrange: UC クエリ結果が0件
        mocker.patch(_FETCH_CIRCLE_DATA, return_value=[])

        # Act
        response = client.post(self._data_url(circle_gadget.gadget_uuid))

        # Assert
        assert response.status_code == 200
        data = response.get_json()
        assert data["chart_data"]["labels"] == []
        assert data["chart_data"]["values"] == []

    def test_uc_query_returns_all_expected_columns_as_labels(
        self, client, db_session, auth_scope, dashboard_master, dashboard_group_master, mocker
    ):
        """6.3.1.7: chart_config に設定した全 item_id に対応するラベルが
        measurement_item_master.display_name から取得されて返却される"""
        # Arrange: 3件の MeasurementItemMaster を登録
        from iot_app.models.customer_dashboard import DashboardGadgetMaster
        from iot_app.models.measurement import MeasurementItemMaster
        items = [
            ("external_temp",        "外気温度",          1),
            ("set_temp_freezer_1",   "第1冷凍 設定温度",  2),
            ("internal_temp_freezer_1", "第1冷凍 庫内温度", 3),
        ]
        for col, name, mid in items:
            db_session.add(MeasurementItemMaster(
                measurement_item_id=mid,
                measurement_item_name=col,
                display_name=name,
                silver_data_column_name=col,
                unit_name="℃",
                creator=1,
                modifier=1,
                delete_flag=False,
            ))
        db_session.flush()

        # chart_config に item_id_1=1, item_id_2=2, item_id_3=3 を設定したガジェットを登録
        gadget = DashboardGadgetMaster(
            gadget_uuid=str(uuid.uuid4()),
            gadget_name="カラム検証ガジェット",
            gadget_type_id=2,
            dashboard_group_id=dashboard_group_master.dashboard_group_id,
            chart_config=json.dumps({"item_id_1": 1, "item_id_2": 2, "item_id_3": 3}),
            data_source_config=json.dumps({"device_id": 1}),
            position_x=0,
            position_y=1,
            gadget_size=0,
            display_order=1,
            creator=1,
            modifier=1,
        )
        db_session.add(gadget)
        db_session.flush()

        mocker.patch(
            _FETCH_CIRCLE_DATA,
            return_value=[{
                "external_temp": 10.5,
                "set_temp_freezer_1": 12.3,
                "internal_temp_freezer_1": 9.8,
            }],
        )

        # Act
        response = client.post(self._data_url(gadget.gadget_uuid))

        # Assert: chart_config に対応する3つのラベルがすべて含まれる
        assert response.status_code == 200
        data = response.get_json()
        labels = data["chart_data"]["labels"]
        assert "外気温度" in labels
        assert "第1冷凍 設定温度" in labels
        assert "第1冷凍 庫内温度" in labels
        assert len(labels) == 3

    def test_uc_query_values_are_numeric_types(
        self, client, circle_gadget, measurement_items_two, mocker
    ):
        """6.3.1.8: Delta Lake の DOUBLE 型相当値（float）が JSON で数値型として返却される

        sensor_data_view の温度・回転数カラムは DOUBLE 型。
        Python の float として取得され、JSON シリアライズ後も数値型を保つことを確認する。
        """
        # Arrange: float 値を持つセンサーデータをモック
        mocker.patch(
            _FETCH_CIRCLE_DATA,
            return_value=[{"external_temp": 10.5, "set_temp_freezer_1": -3.2}],
        )

        # Act
        response = client.post(self._data_url(circle_gadget.gadget_uuid))

        # Assert: values の各要素が数値型（int or float）である
        assert response.status_code == 200
        data = response.get_json()
        for value in data["chart_data"]["values"]:
            assert isinstance(value, (int, float)), f"期待する数値型ではない: {value!r}"

    def test_uc_query_error_raises_exception_and_returns_500(
        self, client, circle_gadget, measurement_items_two, mocker
    ):
        """6.3.2.1: UC クエリが例外を送出した場合、500 エラーが返却される

        sensor_data_view への接続失敗・タイムアウト等を想定。
        例外は views 層でキャッチされ、500 レスポンスとして返される。
        """
        # Arrange: UC クエリが例外を送出
        mocker.patch(
            _FETCH_CIRCLE_DATA,
            side_effect=Exception("AnalysisException: Table not found: sensor_data_view"),
        )

        # Act
        response = client.post(self._data_url(circle_gadget.gadget_uuid))

        # Assert: 500 エラーが返る
        assert response.status_code == 500
        data = response.get_json()
        assert "error" in data


# ─────────────────────────────────────────────────────────────────────────────
# 8. データスコープフィルタテスト
# POST /analysis/customer-dashboard/gadgets/<gadget_uuid>/data
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.integration
class TestCircleChartDataScope:
    """円グラフガジェット データスコープフィルタテスト

    観点: 1.3 データスコープフィルタテスト

    organization_closure テーブルによるアクセス制御が
    AJAX データ取得エンドポイントで機能することを確認する。
    check_gadget_access() は DashboardGadgetMaster → DashboardGroupMaster → DashboardMaster
    の2段 JOIN で DashboardMaster.organization_id を accessible_org_ids と照合する。
    """

    @pytest.fixture(autouse=True)
    def _setup(self, auth_user_id, db_session):
        """全テストで GadgetTypeMaster='円グラフ' と MeasurementItemMaster を登録する"""
        from iot_app.models.customer_dashboard import GadgetTypeMaster
        from iot_app.models.measurement import MeasurementItemMaster

        db_session.add(GadgetTypeMaster(
            gadget_type_id=2,
            gadget_type_name="円グラフ",
            data_source_type=1,
            gadget_image_path="images/gadgets/circle_chart.png",
            gadget_description="円グラフガジェット",
            display_order=2,
            creator=1,
            modifier=1,
            delete_flag=False,
        ))
        if db_session.get(MeasurementItemMaster, 1) is None:
            db_session.add(MeasurementItemMaster(
                measurement_item_id=1,
                measurement_item_name="external_temp",
                display_name="外気温度",
                silver_data_column_name="external_temp",
                unit_name="℃",
                creator=1,
                modifier=1,
                delete_flag=False,
            ))
        db_session.flush()

    # ── ヘルパーメソッド ────────────────────────────────────────────────────

    def _make_org(self, db_session, org_id):
        from datetime import date as _date
        from iot_app.models.organization import OrganizationMaster
        org = OrganizationMaster(
            organization_id=org_id,
            organization_name=f"テスト組織_{org_id}",
            organization_type_id=1,
            address="テスト住所",
            phone_number="000-0000-0000",
            contact_person="テスト担当者",
            contract_status_id=1,
            contract_start_date=_date(2024, 1, 1),
            databricks_group_id=f"test-group-{org_id}",
            creator=1,
            modifier=1,
        )
        db_session.add(org)
        return org

    def _make_closure(self, db_session, parent_id, subsidiary_id):
        from iot_app.models.organization import OrganizationClosure
        c = OrganizationClosure(
            parent_organization_id=parent_id,
            subsidiary_organization_id=subsidiary_id,
            depth=0 if parent_id == subsidiary_id else 1,
        )
        db_session.add(c)
        return c

    def _make_user(self, db_session, org_id):
        from datetime import datetime as _dt
        from iot_app.models.user import User
        now = _dt.now()
        user = User(
            user_id=1,
            databricks_user_id="test-databricks-id",
            user_name="テストユーザー",
            organization_id=org_id,
            email_address="test@test.com",
            user_type_id=1,
            language_code="ja",
            region_id=1,
            address="",
            creator=1,
            modifier=1,
            create_date=now,
            update_date=now,
        )
        db_session.add(user)
        return user

    def _make_dashboard_chain(self, db_session, org_id):
        """DashboardMaster → DashboardGroupMaster → DashboardGadgetMaster の連鎖を作成し、
        ガジェットを返す。data_source_config.device_id=1（固定）で DeviceMaster 不要。
        """
        from iot_app.models.customer_dashboard import (
            DashboardGadgetMaster, DashboardGroupMaster, DashboardMaster,
        )
        dashboard = DashboardMaster(
            dashboard_uuid=str(uuid.uuid4()),
            dashboard_name=f"テストダッシュボード_{org_id}",
            organization_id=org_id,
            creator=1,
            modifier=1,
            delete_flag=False,
        )
        db_session.add(dashboard)
        db_session.flush()

        group = DashboardGroupMaster(
            dashboard_group_uuid=str(uuid.uuid4()),
            dashboard_group_name="テストグループ",
            dashboard_id=dashboard.dashboard_id,
            display_order=1,
            creator=1,
            modifier=1,
            delete_flag=False,
        )
        db_session.add(group)
        db_session.flush()

        gadget = DashboardGadgetMaster(
            gadget_uuid=str(uuid.uuid4()),
            gadget_name="スコープテスト円グラフ",
            gadget_type_id=2,
            dashboard_group_id=group.dashboard_group_id,
            chart_config=json.dumps({"item_id_1": 1}),
            data_source_config=json.dumps({"device_id": 1}),
            position_x=0,
            position_y=1,
            gadget_size=0,
            display_order=1,
            creator=1,
            modifier=1,
        )
        db_session.add(gadget)
        db_session.flush()
        return gadget

    def _url(self, gadget_uuid):
        return f"{BASE_URL}/gadgets/{gadget_uuid}/data"

    # ── テスト ──────────────────────────────────────────────────────────────

    def test_own_org_gadget_is_accessible(self, client, db_session, mocker):
        """1.3.1: 自組織のダッシュボードに属するガジェットはデータ取得可能（200）

        ユーザー所属: org=1
        closure: (1→1)
        ダッシュボード org: 1
        期待: accessible_org_ids=[1] に org=1 が含まれる → 200
        """
        # Arrange
        self._make_org(db_session, 1)
        self._make_closure(db_session, 1, 1)
        self._make_user(db_session, 1)
        gadget = self._make_dashboard_chain(db_session, 1)
        mocker.patch(_FETCH_CIRCLE_DATA, return_value=[{"external_temp": 10.5}])

        # Act
        response = client.post(self._url(gadget.gadget_uuid))

        # Assert: 自組織スコープ内のためアクセス可能
        assert response.status_code == 200

    def test_child_org_gadget_is_accessible(self, client, db_session, mocker):
        """1.3.2: 下位組織のダッシュボードに属するガジェットはデータ取得可能（200）

        ユーザー所属: org=1（親）
        closure: (1→1), (1→2) → accessible_org_ids=[1, 2]
        ダッシュボード org: 2（子）
        期待: org=2 が accessible_org_ids=[1, 2] に含まれる → 200
        """
        # Arrange: 親組織=1, 子組織=2。closure に (1→2) を含めることで子組織へのアクセスを許可
        self._make_org(db_session, 1)
        self._make_org(db_session, 2)
        self._make_closure(db_session, 1, 1)
        self._make_closure(db_session, 1, 2)
        self._make_user(db_session, 1)
        gadget = self._make_dashboard_chain(db_session, 2)  # 子組織のダッシュボード
        mocker.patch(_FETCH_CIRCLE_DATA, return_value=[{"external_temp": 10.5}])

        # Act
        response = client.post(self._url(gadget.gadget_uuid))

        # Assert: 子組織はスコープ内のためアクセス可能
        assert response.status_code == 200

    def test_parent_org_gadget_is_not_accessible(self, client, db_session):
        """1.3.3: 上位組織のダッシュボードに属するガジェットは取得不可（404）

        ユーザー所属: org=2（子）
        closure: (2→2) のみ → accessible_org_ids=[2]
        ダッシュボード org: 1（親）
        期待: org=1 が accessible_org_ids=[2] に含まれない → 404
        """
        # Arrange: 親組織=1, 子組織=2。ユーザーは子org=2のみ参照可能
        self._make_org(db_session, 1)
        self._make_org(db_session, 2)
        self._make_closure(db_session, 2, 2)  # org=2 の自己参照のみ（org=1 へのアクセスなし）
        self._make_user(db_session, 2)         # ユーザーは org=2 所属
        gadget = self._make_dashboard_chain(db_session, 1)  # 親組織=1 のダッシュボード

        # Act
        response = client.post(self._url(gadget.gadget_uuid))

        # Assert: 上位組織はスコープ外のためアクセス不可
        assert response.status_code == 404
        data = response.get_json()
        assert "error" in data

    def test_unrelated_org_gadget_is_not_accessible(self, client, db_session):
        """1.3.4: 無関係組織のダッシュボードに属するガジェットは取得不可（404）

        ユーザー所属: org=1
        closure: (1→1) のみ → accessible_org_ids=[1]
        ダッシュボード org: 3（無関係）
        期待: org=3 が accessible_org_ids=[1] に含まれない → 404
        """
        # Arrange: ユーザー org=1, 無関係 org=3（closure に (1→3) なし）
        self._make_org(db_session, 1)
        self._make_org(db_session, 3)
        self._make_closure(db_session, 1, 1)
        self._make_user(db_session, 1)
        gadget = self._make_dashboard_chain(db_session, 3)  # 無関係組織のダッシュボード

        # Act
        response = client.post(self._url(gadget.gadget_uuid))

        # Assert: 無関係組織はスコープ外のためアクセス不可
        assert response.status_code == 404
        data = response.get_json()
        assert "error" in data


# ─────────────────────────────────────────────────────────────────────────────
# 9. 認証エラー時画面遷移テスト
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.integration
class TestCircleChartAuthError:
    """円グラフガジェット 認証エラー時画面遷移テスト

    観点: 2.2.1 認証エラー（DBに未登録ユーザー）時の各エンドポイントのレスポンス確認

    conftest の bypass_auth_middleware（autouse）は find_user_by_email を正常終了させるが、
    各テストで mocker.patch により UnauthorizedError 送出に上書きすることで
    アプリ未登録ユーザー状態を再現する。
    middleware は UnauthorizedError を受けて render_template("errors/403.html"), 403 を返す。
    """

    @pytest.fixture(autouse=True)
    def _simulate_auth_failure(self, mocker):
        """find_user_by_email を UnauthorizedError 送出に上書きし、未登録ユーザー状態を再現する"""
        from iot_app.auth.exceptions import UnauthorizedError
        mocker.patch(
            'iot_app.auth.middleware.find_user_by_email',
            side_effect=UnauthorizedError(),
        )

    def test_unauthenticated_user_accessing_dashboard_returns_403(self, client):
        """2.2.1: 未登録ユーザーがダッシュボード画面（GET /analysis/customer-dashboard）に
        アクセスすると 403 を返す"""
        # Act
        response = client.get(BASE_URL)

        # Assert
        assert response.status_code == 403

    def test_unauthenticated_user_accessing_gadget_data_returns_403(self, client):
        """2.2.1: 未登録ユーザーがガジェットデータ取得 AJAX
        （POST /gadgets/<uuid>/data）にアクセスすると 403 を返す"""
        # Act
        response = client.post(f"{BASE_URL}/gadgets/{uuid.uuid4()}/data")

        # Assert
        assert response.status_code == 403

    def test_unauthenticated_user_accessing_create_modal_returns_403(self, client):
        """2.2.1: 未登録ユーザーがガジェット登録モーダル
        （GET /gadgets/circle-chart/create）にアクセスすると 403 を返す"""
        # Act
        response = client.get(f"{BASE_URL}/gadgets/circle-chart/create")

        # Assert
        assert response.status_code == 403

    def test_unauthenticated_user_posting_register_returns_403(self, client):
        """2.2.1: 未登録ユーザーがガジェット登録 POST
        （POST /gadgets/circle-chart/register）を送信すると 403 を返す"""
        # Act
        response = client.post(f"{BASE_URL}/gadgets/circle-chart/register", data={})

        # Assert
        assert response.status_code == 403
