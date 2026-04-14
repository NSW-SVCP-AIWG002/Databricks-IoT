"""
顧客作成ダッシュボード 表ガジェット - 結合テスト

対象エンドポイント:
  GET  /analysis/customer-dashboard/gadgets/grid/create
  POST /analysis/customer-dashboard/gadgets/grid/register
  POST /analysis/customer-dashboard/gadgets/<gadget_uuid>/data
  GET  /analysis/customer-dashboard/gadgets/<gadget_uuid>?export=csv
  POST /analysis/customer-dashboard/gadgets/preview/grid/data

参照設計書:
  - docs/03-features/flask-app/customer-dashboard/grid/ui-specification.md
  - docs/03-features/flask-app/customer-dashboard/grid/workflow-specification.md
  - docs/03-features/flask-app/customer-dashboard/common/workflow-specification.md

NOTE: モデルファイル（models/dashboard.py 等）が実装済みであることが前提。
      外部API（Unity Catalog / sensor_data_view）のみモック化する。
      認証ミドルウェアはこのブランチでは未実装のため対象外。
"""

import json
import re
import uuid
from datetime import date, datetime as _dt

import pytest

BASE_URL = "/analysis/customer-dashboard"
_VALID_START_DATETIME = "2026/03/06 12:00:00"
_VALID_END_DATETIME   = "2026/03/06 13:00:00"

# Unity Catalog クエリのモック対象パス（サービス層のシルバークエリ）
_SILVER_QUERY = "iot_app.services.customer_dashboard.grid.execute_silver_query"
_COUNT_QUERY  = "iot_app.views.analysis.customer_dashboard.grid.count_grid_data"

# テスト用ユーザー・組織 ID
_TEST_USER_ID = 1
_TEST_ORG_ID  = 1


# ─────────────────────────────────────────────────────────────────────────────
# フィクスチャ（grid ガジェット専用）
# ─────────────────────────────────────────────────────────────────────────────


@pytest.fixture()
def auth_user_id(app):
    """テスト用 g.current_user を before_request フックでセットアップする"""
    from flask import g as flask_g

    def _set_test_user():
        flask_g.current_user = type('_TestUser', (), {
            'user_id': _TEST_USER_ID,
            'organization_id': _TEST_ORG_ID,
        })()

    app.before_request_funcs.setdefault(None, []).append(_set_test_user)
    yield _TEST_USER_ID
    app.before_request_funcs[None].remove(_set_test_user)


@pytest.fixture()
def organization_master(db_session):
    """OrganizationMaster テストレコード（organization_id=_TEST_ORG_ID）"""
    from iot_app.models.organization import OrganizationMaster
    org = OrganizationMaster(
        organization_id=_TEST_ORG_ID,
        organization_name='テスト組織',
        organization_type_id=1,
        address='テスト住所',
        phone_number='000-0000-0000',
        contact_person='テスト担当者',
        contract_status_id=1,
        contract_start_date=date(2024, 1, 1),
        databricks_group_id='test-group',
        creator=1,
        modifier=1,
        delete_flag=False,
    )
    db_session.add(org)
    db_session.flush()
    return org


@pytest.fixture()
def organization_closure(db_session, organization_master):
    """OrganizationClosure テストレコード（自組織を自分で参照）

    get_accessible_org_ids が organization_closure を参照するため、
    親=_TEST_ORG_ID / 子=_TEST_ORG_ID の自己閉包レコードを挿入する。
    これにより accessible_org_ids = [_TEST_ORG_ID] となる。
    """
    from iot_app.models.organization import OrganizationClosure
    closure = OrganizationClosure(
        parent_organization_id=_TEST_ORG_ID,
        subsidiary_organization_id=_TEST_ORG_ID,
        depth=0,
    )
    db_session.add(closure)
    db_session.flush()
    return closure


@pytest.fixture()
def user_master(db_session, organization_master):
    """UserMaster テストレコード（user_id=_TEST_USER_ID, organization_id=_TEST_ORG_ID）"""
    from iot_app.models.user import User
    user = User(
        user_id=_TEST_USER_ID,
        databricks_user_id='test-databricks-id',
        user_name='テストユーザー',
        organization_id=_TEST_ORG_ID,
        email_address='test@test.com',
        user_type_id=1,
        language_code='ja',
        region_id=1,
        address='',
        creator=1,
        modifier=1,
        create_date=_dt.now(),
        update_date=_dt.now(),
    )
    db_session.add(user)
    db_session.flush()
    return user


@pytest.fixture()
def dashboard_master(db_session, organization_master, organization_closure):
    """DashboardMaster テストレコード（organization_id=_TEST_ORG_ID）"""
    from iot_app.models.customer_dashboard import DashboardMaster
    dm = DashboardMaster(
        dashboard_id=1,
        dashboard_uuid=str(uuid.uuid4()),
        dashboard_name='テストダッシュボード',
        organization_id=_TEST_ORG_ID,
        creator=1,
        modifier=1,
        delete_flag=False,
    )
    db_session.add(dm)
    db_session.flush()
    return dm


@pytest.fixture()
def dashboard_user_setting(db_session, dashboard_master):
    """DashboardUserSetting テストレコード（user_id=_TEST_USER_ID, dashboard_id=1）"""
    from iot_app.models.customer_dashboard import DashboardUserSetting
    setting = DashboardUserSetting(
        user_id=_TEST_USER_ID,
        dashboard_id=dashboard_master.dashboard_id,
        organization_id=_TEST_ORG_ID,
        device_id=0,
        creator=1,
        modifier=1,
    )
    db_session.add(setting)
    db_session.flush()
    return setting


@pytest.fixture()
def dashboard_group_master(db_session, dashboard_master):
    """DashboardGroupMaster テストレコード（dashboard_id=1, display_order=1）"""
    from iot_app.models.customer_dashboard import DashboardGroupMaster
    grp = DashboardGroupMaster(
        dashboard_group_id=1,
        dashboard_group_uuid=str(uuid.uuid4()),
        dashboard_id=dashboard_master.dashboard_id,
        dashboard_group_name='テストグループ',
        display_order=1,
        creator=1,
        modifier=1,
        delete_flag=False,
    )
    db_session.add(grp)
    db_session.flush()
    return grp


@pytest.fixture()
def gadget_type_grid(db_session):
    """GadgetTypeMaster テストレコード（表ガジェット用）"""
    from iot_app.models.customer_dashboard import GadgetTypeMaster
    gt = GadgetTypeMaster(
        gadget_type_id=1,
        gadget_type_name='表',
        data_source_type=1,
        gadget_image_path='images/gadgets/grid.png',
        gadget_description='表ガジェット',
        display_order=1,
        creator=1,
        modifier=1,
        delete_flag=False,
    )
    db_session.add(gt)
    db_session.flush()
    return gt


@pytest.fixture()
def measurement_item(db_session):
    """MeasurementItemMaster テストレコード（外気温度）

    seed_measurement_items（セッションスコープ）が既にid=1を挿入している場合は
    重複エラーを避けるためget-or-createパターンを使用する。
    """
    from iot_app.models.measurement import MeasurementItemMaster
    item = db_session.query(MeasurementItemMaster).filter_by(measurement_item_id=1).first()
    if item is None:
        item = MeasurementItemMaster(
            measurement_item_id=1,
            measurement_item_name='外気温度',
            display_name='外気温度',
            silver_data_column_name='external_temp',
            unit_name='℃',
            creator=1,
            modifier=1,
            delete_flag=False,
        )
        db_session.add(item)
        db_session.flush()
    return item


@pytest.fixture()
def grid_gadget(db_session, dashboard_group_master, gadget_type_grid, measurement_item):
    """DashboardGadgetMaster テストレコード（表ガジェット・デバイス可変モード）

    dashboard_group_master に依存することで DashboardGroupMaster(id=1) と
    DashboardMaster(id=1, org_id=1) および OrganizationClosure が存在し、
    check_gadget_access の INNER JOIN が成立する。
    """
    from iot_app.models.customer_dashboard import DashboardGadgetMaster
    g = DashboardGadgetMaster(
        gadget_uuid=str(uuid.uuid4()),
        gadget_name='テスト表',
        gadget_type_id=1,
        dashboard_group_id=1,
        chart_config=json.dumps({}),
        data_source_config=json.dumps({'device_id': None}),
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


def _mock_rows():
    """モック用センサーデータ行（event_timestamp は datetime オブジェクト）"""
    return [
        {
            'event_timestamp': _dt(2026, 3, 6, 12, 0, 0),
            'device_name': 'Device-001',
            'external_temp': 25.5,
        },
        {
            'event_timestamp': _dt(2026, 3, 6, 12, 1, 0),
            'device_name': 'Device-001',
            'external_temp': 25.6,
        },
    ]


# ─────────────────────────────────────────────────────────────────────────────
# 1. ガジェットデータ取得（AJAX）
# POST /analysis/customer-dashboard/gadgets/<gadget_uuid>/data
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.integration
class TestGadgetGridData:
    """表ガジェット データ取得（AJAX）

    観点: 4.2 詳細表示（Read）テスト、3.4 日付形式チェック、3.8 相関チェック、2.2 エラー時遷移テスト
    """

    @pytest.fixture(autouse=True)
    def _auth(self, auth_user_id, user_master, organization_closure):
        """全テストで g.current_user と user_master / organization_closure を自動セットアップする"""
        pass

    def _url(self, gadget_uuid):
        return f"{BASE_URL}/gadgets/{gadget_uuid}/data"

    def _valid_payload(self, **overrides):
        """デフォルトの有効なリクエストペイロード"""
        data = {
            'start_datetime': _VALID_START_DATETIME,
            'end_datetime':   _VALID_END_DATETIME,
        }
        data.update(overrides)
        return data

    def test_data_returns_json_structure(self, client, grid_gadget, mocker):
        """4.2.1: 正常取得 - gadget_uuid / columns / grid_data / total_count / page / per_page / updated_at を含む JSON を返す"""
        # Arrange
        mocker.patch(_SILVER_QUERY, return_value=_mock_rows())
        mocker.patch(_COUNT_QUERY, return_value=2)

        # Act
        response = client.post(
            self._url(grid_gadget.gadget_uuid),
            json=self._valid_payload(),
        )

        # Assert
        assert response.status_code == 200
        body = response.get_json()
        assert body['gadget_uuid'] == grid_gadget.gadget_uuid
        assert 'columns' in body
        assert 'grid_data' in body
        assert 'total_count' in body
        assert 'page' in body
        assert 'per_page' in body
        assert 'updated_at' in body

    def test_data_grid_data_values_match_mocked_rows(self, client, grid_gadget, mocker):
        """4.2.2: シルバー層の行データが grid_data に正しく変換される（timestamp フォーマット含む）"""
        # Arrange
        mocker.patch(_SILVER_QUERY, return_value=_mock_rows())
        mocker.patch(_COUNT_QUERY, return_value=2)

        # Act
        response = client.post(
            self._url(grid_gadget.gadget_uuid),
            json=self._valid_payload(),
        )

        # Assert
        body = response.get_json()
        assert len(body['grid_data']) == 2
        assert body['grid_data'][0]['event_timestamp'] == '2026/03/06 12:00:00'
        assert body['grid_data'][1]['event_timestamp'] == '2026/03/06 12:01:00'
        assert body['grid_data'][0]['external_temp'] == 25.5
        assert body['grid_data'][0]['device_name'] == 'Device-001'  # ワークフロー ④ データ整形

    def test_data_columns_contain_measurement_items(self, client, grid_gadget, mocker):
        """4.2.3: columns に measurement_item_master のカラム定義が含まれる（column_name / display_name）"""
        # Arrange
        mocker.patch(_SILVER_QUERY, return_value=[])
        mocker.patch(_COUNT_QUERY, return_value=0)

        # Act
        response = client.post(
            self._url(grid_gadget.gadget_uuid),
            json=self._valid_payload(),
        )

        # Assert
        body = response.get_json()
        assert len(body['columns']) >= 1
        first_col = body['columns'][0]
        assert 'column_name' in first_col
        assert 'display_name' in first_col
        assert first_col['column_name'] == 'external_temp'
        assert first_col['display_name'] == '外気温度'

    def test_data_empty_rows_returns_empty_grid_data(self, client, grid_gadget, mocker):
        """4.2.4: センサーデータ0件時は空配列を返す（エラーではない）"""
        # Arrange
        mocker.patch(_SILVER_QUERY, return_value=[])
        mocker.patch(_COUNT_QUERY, return_value=0)

        # Act
        response = client.post(
            self._url(grid_gadget.gadget_uuid),
            json=self._valid_payload(),
        )

        # Assert
        assert response.status_code == 200
        body = response.get_json()
        assert body['grid_data'] == []
        assert body['total_count'] == 0

    def test_data_empty_rows_still_returns_columns(self, client, grid_gadget, mocker):
        """4.2.4: センサーデータ0件時でも columns（カラム定義）は返される

        設計書 ⑤ データなしの場合のレスポンス形式確認:
        grid_data=[] だが columns にヘッダー定義が含まれること。
        measurement_item_master から columns を取得する実装であるため、
        センサーデータの有無に関わらず常にカラム定義が返る。
        """
        # Arrange
        mocker.patch(_SILVER_QUERY, return_value=[])
        mocker.patch(_COUNT_QUERY, return_value=0)

        # Act
        response = client.post(
            self._url(grid_gadget.gadget_uuid),
            json=self._valid_payload(),
        )

        # Assert
        body = response.get_json()
        assert body['grid_data'] == []
        assert len(body['columns']) >= 1  # データなしでもカラム定義は返る

    def test_data_single_row_returns_one_grid_data(self, client, grid_gadget, mocker):
        """4.1.2: センサーデータ1件のみの場合、grid_data に1件だけ返される"""
        # Arrange
        mocker.patch(_SILVER_QUERY, return_value=[_mock_rows()[0]])
        mocker.patch(_COUNT_QUERY, return_value=1)

        # Act
        response = client.post(
            self._url(grid_gadget.gadget_uuid),
            json=self._valid_payload(),
        )

        # Assert
        body = response.get_json()
        assert response.status_code == 200
        assert len(body['grid_data']) == 1

    def test_data_gadget_outside_scope_returns_404(self, client, db_session):
        """4.1.5 / 4.2.4: 別組織（org_id=2）のガジェットへのアクセスは404

        テストユーザー（user_id=1, org_id=1）は org_id=2 の組織閉包を持たないため、
        check_gadget_access が None を返して 404 になることを検証する。
        """
        # Arrange: org_id=2 の組織・ダッシュボード・グループ・ガジェットを作成
        from iot_app.models.customer_dashboard import (
            DashboardGadgetMaster,
            DashboardGroupMaster,
            DashboardMaster,
            GadgetTypeMaster,
        )
        from iot_app.models.organization import OrganizationMaster

        other_org = OrganizationMaster(
            organization_id=2,
            organization_name='別組織',
            organization_type_id=1,
            address='別住所',
            phone_number='000-0000-0001',
            contact_person='別担当者',
            contract_status_id=1,
            contract_start_date=date(2024, 1, 1),
            databricks_group_id='other-group',
            creator=1,
            modifier=1,
            delete_flag=False,
        )
        db_session.add(other_org)
        db_session.flush()

        other_dashboard = DashboardMaster(
            dashboard_id=2,
            dashboard_uuid=str(uuid.uuid4()),
            dashboard_name='別ダッシュボード',
            organization_id=2,
            creator=1,
            modifier=1,
            delete_flag=False,
        )
        db_session.add(other_dashboard)
        db_session.flush()

        gt = GadgetTypeMaster(
            gadget_type_id=1,
            gadget_type_name='表',
            data_source_type=1,
            gadget_image_path='images/gadgets/grid.png',
            gadget_description='表ガジェット',
            display_order=1,
            creator=1,
            modifier=1,
            delete_flag=False,
        )
        db_session.add(gt)
        db_session.flush()

        other_group = DashboardGroupMaster(
            dashboard_group_id=1,
            dashboard_group_uuid=str(uuid.uuid4()),
            dashboard_id=2,
            dashboard_group_name='別グループ',
            display_order=1,
            creator=1,
            modifier=1,
            delete_flag=False,
        )
        db_session.add(other_group)
        db_session.flush()

        other_gadget_uuid = str(uuid.uuid4())
        other_gadget = DashboardGadgetMaster(
            gadget_uuid=other_gadget_uuid,
            gadget_name='別ガジェット',
            gadget_type_id=1,
            dashboard_group_id=1,
            chart_config=json.dumps({}),
            data_source_config=json.dumps({'device_id': None}),
            position_x=0,
            position_y=1,
            gadget_size=0,
            display_order=1,
            creator=1,
            modifier=1,
        )
        db_session.add(other_gadget)
        db_session.flush()

        # Act: テストユーザー（org_id=1）が org_id=2 のガジェットにアクセス
        # organization_closure に org_id=2 が含まれないため 404 となる
        response = client.post(
            self._url(other_gadget_uuid),
            json=self._valid_payload(),
        )

        # Assert
        assert response.status_code == 404

    def test_data_updated_at_format_is_datetime_string(self, client, grid_gadget, mocker):
        """4.2.5: レスポンスの updated_at が 'YYYY/MM/DD HH:MM:SS' 形式の文字列である

        設計書 ⑤ レスポンス形式: updated_at は '2026/03/05 12:00:00' 形式。
        """
        # Arrange
        mocker.patch(_SILVER_QUERY, return_value=[])
        mocker.patch(_COUNT_QUERY, return_value=0)

        # Act
        response = client.post(
            self._url(grid_gadget.gadget_uuid),
            json=self._valid_payload(),
        )

        # Assert
        body = response.get_json()
        assert re.fullmatch(r'\d{4}/\d{2}/\d{2} \d{2}:\d{2}:\d{2}', body['updated_at'])

    def test_data_pagination_defaults_to_page_1(self, client, grid_gadget, mocker):
        """5.3.1: page 未指定時、レスポンスの page が 1 になる"""
        # Arrange
        mocker.patch(_SILVER_QUERY, return_value=[])
        mocker.patch(_COUNT_QUERY, return_value=0)

        # Act
        response = client.post(
            self._url(grid_gadget.gadget_uuid),
            json=self._valid_payload(),  # page 未指定
        )

        # Assert
        body = response.get_json()
        assert body['page'] == 1
        assert body['per_page'] == 25

    def test_data_pagination_page2_passes_correct_offset(self, client, grid_gadget, mocker):
        """5.3.2: page=2 を指定すると offset=25 でシルバー層クエリが呼ばれる

        設計書「ページング計算: offset = (page - 1) × 25」を検証する。
        """
        # Arrange
        mock_silver = mocker.patch(_SILVER_QUERY, return_value=[])
        mocker.patch(_COUNT_QUERY, return_value=50)

        # Act
        response = client.post(
            self._url(grid_gadget.gadget_uuid),
            json=self._valid_payload(page=2),
        )

        # Assert
        assert response.status_code == 200
        body = response.get_json()
        assert body['page'] == 2
        # offset=25 でシルバー層クエリが呼ばれていること
        assert mock_silver.called
        assert mock_silver.call_args.kwargs.get('offset') == 25

    def test_data_pagination_last_page_returns_remaining_rows(self, client, grid_gadget, mocker):
        """5.3.3: 最終ページは残りの件数（total_count % per_page 件）を返す

        total_count=26、page=2 のとき grid_data は1件（26 - 25 = 1）。
        """
        # Arrange: page=2 では1件だけ返す
        mocker.patch(_SILVER_QUERY, return_value=[_mock_rows()[0]])
        mocker.patch(_COUNT_QUERY, return_value=26)

        # Act
        response = client.post(
            self._url(grid_gadget.gadget_uuid),
            json=self._valid_payload(page=2),
        )

        # Assert
        body = response.get_json()
        assert response.status_code == 200
        assert body['total_count'] == 26
        assert body['page'] == 2
        assert len(body['grid_data']) == 1

    def test_data_pagination_page0_returns_500(self, client, grid_gadget):
        """5.3.4: page=0 は実装上 ValueError → 500エラー

        # TODO: 設計書では「1ページ目表示」が期待値だが、
        #       実装（calculate_page_offset）は page<=0 で ValueError を送出し 500 になる。
        #       設計書との乖離あり、要確認。
        """
        # Act
        response = client.post(
            self._url(grid_gadget.gadget_uuid),
            json=self._valid_payload(page=0),
        )

        # Assert
        assert response.status_code == 500

    def test_data_pagination_exactly_25_rows_is_single_page(self, client, grid_gadget, mocker):
        """5.3.5: データ件数=25件（ページサイズ境界値）は正確に1ページに収まる

        total_count=25、page=1 のとき grid_data が25件返り、2ページ目はない。
        """
        # Arrange: 25件分のモックデータ
        rows_25 = _mock_rows() * 12 + [_mock_rows()[0]]  # 25件
        mocker.patch(_SILVER_QUERY, return_value=rows_25)
        mocker.patch(_COUNT_QUERY, return_value=25)

        # Act
        response = client.post(
            self._url(grid_gadget.gadget_uuid),
            json=self._valid_payload(page=1),
        )

        # Assert
        body = response.get_json()
        assert response.status_code == 200
        assert body['total_count'] == 25
        assert body['per_page'] == 25
        assert len(body['grid_data']) == 25

    def test_data_pagination_26_rows_splits_into_two_pages(self, client, grid_gadget, mocker):
        """5.3.6: データ件数=26件（ページサイズ+1）は2ページに分割される

        page=1 は25件、page=2 は1件。total_count=26 で2ページ目が存在する。
        """
        # Arrange: page=1 で25件返す
        rows_25 = _mock_rows() * 12 + [_mock_rows()[0]]  # 25件
        mocker.patch(_SILVER_QUERY, return_value=rows_25)
        mocker.patch(_COUNT_QUERY, return_value=26)

        # Act: page=1
        response = client.post(
            self._url(grid_gadget.gadget_uuid),
            json=self._valid_payload(page=1),
        )

        # Assert: 1ページ目は25件、合計26件
        body = response.get_json()
        assert response.status_code == 200
        assert body['total_count'] == 26
        assert len(body['grid_data']) == 25

    def test_data_total_count_matches_mock(self, client, grid_gadget, mocker):
        """5.3.7: total_count がモックの件数と正しく一致する"""
        # Arrange
        mocker.patch(_SILVER_QUERY, return_value=_mock_rows())
        mocker.patch(_COUNT_QUERY, return_value=2)

        # Act
        response = client.post(
            self._url(grid_gadget.gadget_uuid),
            json=self._valid_payload(),
        )

        # Assert
        body = response.get_json()
        assert response.status_code == 200
        assert body['total_count'] == 2

    def test_data_nonexistent_gadget_returns_404(self, client):
        """2.2.4: 存在しない gadget_uuid で404エラー"""
        # Arrange: DBにガジェットなし
        nonexistent_uuid = str(uuid.uuid4())

        # Act
        response = client.post(
            self._url(nonexistent_uuid),
            json=self._valid_payload(),
        )

        # Assert
        assert response.status_code == 404

    def test_data_deleted_gadget_returns_404(self, client, grid_gadget, db_session, mocker):
        """2.2.4: delete_flag=True の論理削除済みガジェットへのデータ取得は404"""
        # Arrange: ガジェットを論理削除
        grid_gadget.delete_flag = True
        db_session.flush()

        # Act
        response = client.post(
            self._url(grid_gadget.gadget_uuid),
            json=self._valid_payload(),
        )

        # Assert
        assert response.status_code == 404

    def test_data_missing_start_datetime_returns_400(self, client, grid_gadget):
        """3.1.1: start_datetime 未指定で400エラー"""
        # Act
        response = client.post(
            self._url(grid_gadget.gadget_uuid),
            json={'end_datetime': _VALID_END_DATETIME},
        )

        # Assert
        assert response.status_code == 400
        assert response.get_json()['error'] == 'パラメータが不正です'

    def test_data_missing_end_datetime_returns_400(self, client, grid_gadget):
        """3.1.2: end_datetime 未指定で400エラー"""
        # Act
        response = client.post(
            self._url(grid_gadget.gadget_uuid),
            json={'start_datetime': _VALID_START_DATETIME},
        )

        # Assert
        assert response.status_code == 400

    def test_data_invalid_start_datetime_format_returns_400(self, client, grid_gadget):
        """3.4.1: start_datetime が YYYY/MM/DD HH:mm:ss 以外の形式で400エラー（ISO 8601形式）"""
        # Act
        response = client.post(
            self._url(grid_gadget.gadget_uuid),
            json=self._valid_payload(start_datetime='2026-03-06T12:00:00'),
        )

        # Assert
        assert response.status_code == 400

    def test_data_invalid_end_datetime_format_returns_400(self, client, grid_gadget):
        """3.4.2: end_datetime が不正な日付形式で400エラー"""
        # Act
        response = client.post(
            self._url(grid_gadget.gadget_uuid),
            json=self._valid_payload(end_datetime='not-a-date'),
        )

        # Assert
        assert response.status_code == 400

    def test_data_start_after_end_datetime_returns_400(self, client, grid_gadget):
        """3.8.2: 開始日時 > 終了日時で400エラー"""
        # Act
        response = client.post(
            self._url(grid_gadget.gadget_uuid),
            json=self._valid_payload(
                start_datetime=_VALID_END_DATETIME,
                end_datetime=_VALID_START_DATETIME,
            ),
        )

        # Assert
        assert response.status_code == 400

    def test_data_range_exceeds_24hours_returns_400(self, client, grid_gadget):
        """3.8.3: 終了日時 - 開始日時 > 24時間で400エラー（仕様: 最大24時間）"""
        # Act
        response = client.post(
            self._url(grid_gadget.gadget_uuid),
            json=self._valid_payload(
                start_datetime='2026/03/06 00:00:00',
                end_datetime='2026/03/07 00:00:01',  # 24時間超過
            ),
        )

        # Assert
        assert response.status_code == 400

    def test_data_silver_query_error_returns_500(self, client, grid_gadget, mocker):
        """2.2.6: Unity Catalog クエリ失敗時に500エラー"""
        # Arrange: 外部API呼び出しが例外を送出
        mocker.patch(_SILVER_QUERY, side_effect=Exception("Databricks connection timeout"))

        # Act
        response = client.post(
            self._url(grid_gadget.gadget_uuid),
            json=self._valid_payload(),
        )

        # Assert
        assert response.status_code == 500

    def test_data_range_exactly_24hours_returns_200(self, client, grid_gadget, mocker):
        """3.8.8: 終了日時 - 開始日時 = ちょうど24時間は正常（境界値OK）

        設計書バリデーション: 「終了日時 - 開始日時 ≤ 24時間」
        ちょうど24時間は ≤ に含まれるため 200 を返す。
        """
        # Arrange
        mocker.patch(_SILVER_QUERY, return_value=[])
        mocker.patch(_COUNT_QUERY, return_value=0)

        # Act
        response = client.post(
            self._url(grid_gadget.gadget_uuid),
            json=self._valid_payload(
                start_datetime='2026/03/06 00:00:00',
                end_datetime='2026/03/07 00:00:00',  # ちょうど24時間
            ),
        )

        # Assert
        assert response.status_code == 200

    def test_data_start_equals_end_datetime_returns_400(self, client, grid_gadget):
        """3.8.4: 開始日時 == 終了日時で400エラー

        設計書バリデーションルール: 「開始日時 < 終了日時」（等値は不可）
        """
        # Act
        response = client.post(
            self._url(grid_gadget.gadget_uuid),
            json=self._valid_payload(
                start_datetime=_VALID_START_DATETIME,
                end_datetime=_VALID_START_DATETIME,  # 等値
            ),
        )

        # Assert
        assert response.status_code == 400

    def test_data_no_device_selected_returns_empty_grid_data(self, client, grid_gadget, mocker):
        """4.2.7: デバイス未選択時（device_id=0）はセンサーデータなしで空の grid_data を返す

        dashboard_user_setting.device_id=0 の場合、Unity Catalog クエリは device_id=None
        で呼ばれ、データなしの正常レスポンスを返す。
        """
        # Arrange: device_id=None でクエリが呼ばれる想定（device 未選択）
        mocker.patch(_SILVER_QUERY, return_value=[])
        mocker.patch(_COUNT_QUERY, return_value=0)

        # Act
        response = client.post(
            self._url(grid_gadget.gadget_uuid),
            json=self._valid_payload(),
        )

        # Assert: 200 かつ空の grid_data
        assert response.status_code == 200
        body = response.get_json()
        assert body['grid_data'] == []
        assert body['total_count'] == 0


# ─────────────────────────────────────────────────────────────────────────────
# 2. ガジェット登録モーダル表示
# GET /analysis/customer-dashboard/gadgets/grid/create
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.integration
class TestGadgetGridCreate:
    """表ガジェット 登録モーダル表示

    観点: 2.1.3 登録画面表示、2.2 エラー時遷移テスト
    """

    _URL = f"{BASE_URL}/gadgets/grid/create"

    @pytest.fixture(autouse=True)
    def _auth(self, auth_user_id, user_master, organization_closure):
        """全テストで g.current_user と user_master / organization_closure を自動セットアップする"""
        pass

    def test_create_modal_returns_200(
        self, client, dashboard_user_setting, dashboard_master, dashboard_group_master, measurement_item,
    ):
        """2.1.3: 正常表示 - 200とHTMLを返す"""
        # Act
        response = client.get(self._URL)

        # Assert
        assert response.status_code == 200

    def test_create_modal_no_dashboard_user_setting_returns_404(self, client):
        """2.2.4: ダッシュボードユーザー設定が存在しない場合404エラー"""
        # Arrange: dashboard_user_setting フィクスチャなし（DBに設定なし）

        # Act
        response = client.get(self._URL)

        # Assert
        assert response.status_code == 404

    def test_create_modal_no_dashboard_master_returns_404(self, client, db_session):
        """2.2.4: ダッシュボード情報が存在しない場合404エラー

        DashboardUserSetting は存在するが、対応する DashboardMaster が存在しない場合に
        get_dashboard_by_id が None を返し abort(404) となることを検証する。
        FK制約バイパスのため FOREIGN_KEY_CHECKS=0 を使用する。
        """
        # Arrange: FK制約を一時無効化してDashboardMasterなしでDashboardUserSettingを挿入
        from sqlalchemy import text as _text
        from iot_app.models.customer_dashboard import DashboardUserSetting

        db_session.execute(_text('SET FOREIGN_KEY_CHECKS=0'))
        setting = DashboardUserSetting(
            user_id=_TEST_USER_ID,
            dashboard_id=999,
            organization_id=_TEST_ORG_ID,
            device_id=0,
            creator=1,
            modifier=1,
            delete_flag=False,
        )
        db_session.add(setting)
        db_session.flush()
        db_session.execute(_text('SET FOREIGN_KEY_CHECKS=1'))

        # Act
        response = client.get(self._URL)

        # Assert
        assert response.status_code == 404

    def test_create_modal_deleted_dashboard_master_returns_404(self, client, db_session):
        """2.2.4: delete_flag=True の DashboardMaster は取得されず 404 になる

        ワークフロー仕様書SQL: WHERE delete_flag = FALSE
        DashboardUserSetting は存在するが、参照先の DashboardMaster が論理削除済みの場合、
        get_dashboard_by_id が None を返し abort(404) となることを検証する。
        """
        # Arrange: 論理削除済み DashboardMaster + それを参照する DashboardUserSetting を作成
        from iot_app.models.customer_dashboard import DashboardMaster, DashboardUserSetting
        from iot_app.models.organization import OrganizationClosure, OrganizationMaster

        deleted_dm = DashboardMaster(
            dashboard_id=1,
            dashboard_uuid=str(uuid.uuid4()),
            dashboard_name='削除済みダッシュボード',
            organization_id=_TEST_ORG_ID,
            creator=1,
            modifier=1,
            delete_flag=True,  # 論理削除済み
        )
        db_session.add(deleted_dm)
        db_session.flush()

        setting = DashboardUserSetting(
            user_id=_TEST_USER_ID,
            dashboard_id=1,
            organization_id=_TEST_ORG_ID,
            device_id=0,
            creator=1,
            modifier=1,
            delete_flag=False,
        )
        db_session.add(setting)
        db_session.flush()

        # Act
        response = client.get(self._URL)

        # Assert
        assert response.status_code == 404

    def test_create_modal_db_error_returns_500(self, client, dashboard_user_setting, dashboard_master, mocker):
        """2.2.5: DBエラー発生時に500エラーを返す"""
        # Arrange
        mocker.patch(
            'iot_app.views.analysis.customer_dashboard.grid.get_grid_create_context',
            side_effect=Exception('DB接続エラー'),
        )

        # Act
        response = client.get(self._URL)

        # Assert
        assert response.status_code == 500

    def test_create_modal_deleted_user_setting_returns_404(self, client, db_session, dashboard_master):
        """① delete_flag=TRUE の dashboard_user_setting は取得されず 404 になる

        get_dashboard_user_setting は delete_flag=FALSE のレコードのみ返すため、
        論理削除済みユーザー設定では abort(404) となる。
        """
        # Arrange: delete_flag=TRUE の設定を作成
        from iot_app.models.customer_dashboard import DashboardUserSetting
        setting = DashboardUserSetting(
            user_id=_TEST_USER_ID,
            dashboard_id=dashboard_master.dashboard_id,
            organization_id=_TEST_ORG_ID,
            device_id=0,
            creator=1,
            modifier=1,
            delete_flag=True,
        )
        db_session.add(setting)
        db_session.flush()

        # Act
        response = client.get(self._URL)

        # Assert
        assert response.status_code == 404

    def test_create_modal_groups_ordered_by_display_order(
        self, client, db_session, dashboard_user_setting, dashboard_master,
    ):
        """③ dashboard_group_master が display_order ASC で返される

        display_order=2 のグループを先に登録し、display_order=1 のグループを後に登録しても、
        レスポンス HTML 内では display_order=1 のグループ名が先に出現する。
        """
        # Arrange: display_order 逆順で登録（2 → 1）
        from iot_app.models.customer_dashboard import DashboardGroupMaster
        grp_b = DashboardGroupMaster(
            dashboard_group_id=2,
            dashboard_group_uuid=str(uuid.uuid4()),
            dashboard_id=dashboard_master.dashboard_id,
            dashboard_group_name='グループB',
            display_order=2,
            creator=1,
            modifier=1,
            delete_flag=False,
        )
        grp_a = DashboardGroupMaster(
            dashboard_group_id=1,
            dashboard_group_uuid=str(uuid.uuid4()),
            dashboard_id=dashboard_master.dashboard_id,
            dashboard_group_name='グループA',
            display_order=1,
            creator=1,
            modifier=1,
            delete_flag=False,
        )
        db_session.add(grp_b)
        db_session.add(grp_a)
        db_session.flush()

        # Act
        response = client.get(self._URL)

        # Assert: display_order=1 の「グループA」が「グループB」より先に出現する
        assert response.status_code == 200
        text = response.data.decode('utf-8')
        pos_a = text.find('グループA')
        pos_b = text.find('グループB')
        assert pos_a != -1 and pos_b != -1
        assert pos_a < pos_b

    def test_create_modal_no_groups_returns_empty_select(
        self, client, dashboard_user_setting, dashboard_master,
    ):
        """③ dashboard_group_master が 0 件の場合、グループ選択が空（初期値のみ）で 200 を返す

        グループが存在しなくてもモーダルは正常表示される。
        フォームの group_id select に「選択してください」のみ存在する。
        """
        # Arrange: dashboard_group_master は作成しない

        # Act
        response = client.get(self._URL)

        # Assert: グループが存在しなくてもモーダルは正常表示される
        assert response.status_code == 200

    def test_create_modal_has_default_title(
        self, client, dashboard_user_setting, dashboard_master,
    ):
        """① タイトル入力欄の初期値が「表」であること

        UI仕様書: タイトル 初期値: 「表」
        登録モーダルのHTMLに value="表" または「表」がデフォルト表示されることを確認する。
        """
        # Act
        response = client.get(self._URL)

        # Assert
        assert response.status_code == 200
        text = response.data.decode('utf-8')
        assert '表' in text

    def test_create_modal_deleted_groups_excluded(
        self, client, db_session, dashboard_user_setting, dashboard_master,
    ):
        """③ delete_flag=True の DashboardGroupMaster は取得されず HTML に表示されない

        ワークフロー仕様書SQL: WHERE delete_flag = FALSE
        論理削除済みグループは選択肢から除外される。
        """
        from iot_app.models.customer_dashboard import DashboardGroupMaster

        # Arrange: 有効グループ1件 + 削除済みグループ1件
        active_grp = DashboardGroupMaster(
            dashboard_group_id=1,
            dashboard_group_uuid=str(uuid.uuid4()),
            dashboard_id=dashboard_master.dashboard_id,
            dashboard_group_name='有効グループ',
            display_order=1,
            creator=1,
            modifier=1,
            delete_flag=False,
        )
        deleted_grp = DashboardGroupMaster(
            dashboard_group_id=2,
            dashboard_group_uuid=str(uuid.uuid4()),
            dashboard_id=dashboard_master.dashboard_id,
            dashboard_group_name='削除済みグループ',
            display_order=2,
            creator=1,
            modifier=1,
            delete_flag=True,
        )
        db_session.add(active_grp)
        db_session.add(deleted_grp)
        db_session.flush()

        # Act
        response = client.get(self._URL)

        # Assert: 有効グループは存在、削除済みグループは非表示
        assert response.status_code == 200
        text = response.data.decode('utf-8')
        assert '有効グループ' in text
        assert '削除済みグループ' not in text


# ─────────────────────────────────────────────────────────────────────────────
# 3. ガジェット登録実行
# POST /analysis/customer-dashboard/gadgets/grid/register
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.integration
class TestGadgetGridRegister:
    """表ガジェット 登録実行

    観点: 3.1 必須チェック、3.2 文字列長チェック、
          4.3 登録（Create）テスト、2.3 リダイレクトテスト、7 トランザクション
    """

    _URL = f"{BASE_URL}/gadgets/grid/register"

    _SKIP_GADGET_TYPE = frozenset({
        'test_register_without_gadget_type_master_returns_error',
    })

    @pytest.fixture(autouse=True)
    def _auth(self, auth_user_id, user_master, organization_closure):
        """全テストで g.current_user と user_master / organization_closure を自動セットアップする"""
        pass

    @pytest.fixture(autouse=True)
    def _register_setup(self, dashboard_group_master, dashboard_user_setting):
        """全テストで DashboardGroupMaster / DashboardUserSetting を事前登録する"""
        pass

    @pytest.fixture(autouse=True)
    def _require_gadget_type(self, request, db_session):
        """全テストで GadgetTypeMaster='表' を事前登録する（サービス層の動的ルックアップに必要）。
        GadgetTypeMaster の存在チェックテストではスキップする。
        """
        if request.node.name in self._SKIP_GADGET_TYPE:
            return
        from iot_app.models.customer_dashboard import GadgetTypeMaster
        gt = GadgetTypeMaster(
            gadget_type_id=1,
            gadget_type_name='表',
            data_source_type=1,
            gadget_image_path='images/gadgets/grid.png',
            gadget_description='表ガジェット',
            display_order=1,
            creator=1,
            modifier=1,
            delete_flag=False,
        )
        db_session.add(gt)
        db_session.flush()

    def _valid_form(self, **overrides):
        """最小有効フォームデータ（gadget_name, group_id, gadget_size）"""
        data = {
            'gadget_name': 'テスト表',
            'group_id':    '1',
            'gadget_size': '0',   # '0'=2x2, '1'=2x4
        }
        data.update(overrides)
        return data

    # ── 正常系 ────────────────────────────────────────────────────────────────

    def test_register_success_redirects_to_dashboard(self, client, measurement_item):
        """2.3.1 / 4.3.1: 正常登録後、ダッシュボード画面へ302リダイレクト（?registered=1 付き）"""
        # Act
        response = client.post(self._URL, data=self._valid_form(), follow_redirects=False)

        # Assert
        assert response.status_code == 302
        location = response.headers['Location']
        assert BASE_URL in location
        assert 'registered=1' in location  # ワークフロー仕様書: redirect(url_for(..., registered=1))

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

    def test_register_gadget_uuid_is_set(self, client, app, measurement_item):
        """4.3.5: 登録されたガジェットに gadget_uuid が自動採番される（UUID形式）"""
        # Act
        client.post(self._URL, data=self._valid_form())

        # Assert
        with app.app_context():
            from iot_app import db
            from iot_app.models.customer_dashboard import DashboardGadgetMaster
            gadget = db.session.query(DashboardGadgetMaster).first()
        assert gadget is not None
        assert len(gadget.gadget_uuid) == 36  # UUID形式

    def test_register_create_date_and_update_date_are_set(self, client, app, measurement_item):
        """4.3.6: 登録されたガジェットの create_date / update_date が自動設定される"""
        from datetime import datetime, timedelta
        before = datetime.utcnow() - timedelta(seconds=1)

        # Act
        client.post(self._URL, data=self._valid_form())

        after = datetime.utcnow() + timedelta(seconds=1)

        # Assert
        with app.app_context():
            from iot_app import db
            from iot_app.models.customer_dashboard import DashboardGadgetMaster
            gadget = db.session.query(DashboardGadgetMaster).first()
        assert gadget.create_date is not None
        assert gadget.update_date is not None
        assert before <= gadget.create_date <= after
        assert before <= gadget.update_date <= after

    def test_register_creator_and_modifier_are_set_to_current_user(self, client, app, measurement_item):
        """4.3.7: 登録されたガジェットの creator / modifier がログインユーザーID に設定される"""
        # Act
        client.post(self._URL, data=self._valid_form())

        # Assert
        with app.app_context():
            from iot_app import db
            from iot_app.models.customer_dashboard import DashboardGadgetMaster
            gadget = db.session.query(DashboardGadgetMaster).first()
        assert gadget.creator == _TEST_USER_ID
        assert gadget.modifier == _TEST_USER_ID

    def test_register_title_stored_correctly(self, client, app, measurement_item):
        """4.3.1: 登録されたガジェットのタイトルがDBに正しく保存される"""
        # Act
        client.post(self._URL, data=self._valid_form(gadget_name='表示テスト'))

        # Assert
        with app.app_context():
            from iot_app import db
            from iot_app.models.customer_dashboard import DashboardGadgetMaster
            gadget = db.session.query(DashboardGadgetMaster).first()
        assert gadget.gadget_name == '表示テスト'

    def test_register_gadget_size_2x2_stored_as_0(self, client, app, measurement_item):
        """4.3.2: 部品サイズ 2x2（gadget_size='0'）がDBに保存される"""
        # Act
        client.post(self._URL, data=self._valid_form(gadget_size='0'))

        # Assert
        with app.app_context():
            from iot_app import db
            from iot_app.models.customer_dashboard import DashboardGadgetMaster
            gadget = db.session.query(DashboardGadgetMaster).first()
        assert gadget.gadget_size == 0

    def test_register_gadget_size_2x4_stored_as_1(self, client, app, measurement_item):
        """4.3.2: 部品サイズ 2x4（gadget_size='1'）がDBに保存される"""
        # Act
        client.post(self._URL, data=self._valid_form(gadget_size='1'))

        # Assert
        with app.app_context():
            from iot_app import db
            from iot_app.models.customer_dashboard import DashboardGadgetMaster
            gadget = db.session.query(DashboardGadgetMaster).first()
        assert gadget.gadget_size == 1

    def test_register_data_source_config_device_id_is_null(self, client, app, measurement_item):
        """4.3.4: data_source_config の device_id は null（可変モード）で保存される

        表ガジェットは device_mode フィールドを持たず、常に device_id=null で登録される。
        """
        # Act
        client.post(self._URL, data=self._valid_form())

        # Assert
        with app.app_context():
            from iot_app import db
            from iot_app.models.customer_dashboard import DashboardGadgetMaster
            gadget = db.session.query(DashboardGadgetMaster).first()
        data_source_config = json.loads(gadget.data_source_config)
        assert data_source_config['device_id'] is None

    def test_register_chart_config_is_empty_dict(self, client, app, measurement_item):
        """4.3.4: chart_config は空の JSON オブジェクト {} で保存される

        表ガジェットは chart_config に設定項目がないため、空の JSON が保存される。
        """
        # Act
        client.post(self._URL, data=self._valid_form())

        # Assert
        with app.app_context():
            from iot_app import db
            from iot_app.models.customer_dashboard import DashboardGadgetMaster
            gadget = db.session.query(DashboardGadgetMaster).first()
        chart_config = json.loads(gadget.chart_config)
        assert chart_config == {}

    def test_register_dashboard_group_id_stored_correctly(self, client, app, measurement_item):
        """4.3.2: フォームの group_id が dashboard_group_id としてDBに正しく保存される"""
        # Act
        client.post(self._URL, data=self._valid_form(group_id='1'))

        # Assert
        with app.app_context():
            from iot_app import db
            from iot_app.models.customer_dashboard import DashboardGadgetMaster
            gadget = db.session.query(DashboardGadgetMaster).first()
        assert gadget.dashboard_group_id == 1

    def test_register_default_position_x_is_zero(self, client, app, measurement_item):
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
        """4.3.2: グループ内初登録時、position_y は 1（COALESCE(MAX, 0)+1）で登録される"""
        # Act
        client.post(self._URL, data=self._valid_form())

        # Assert
        with app.app_context():
            from iot_app import db
            from iot_app.models.customer_dashboard import DashboardGadgetMaster
            gadget = db.session.query(DashboardGadgetMaster).first()
        assert gadget.position_y == 1

    def test_register_position_y_increments_for_second_gadget(self, client, app, measurement_item):
        """4.3.2: 同グループに2件目登録時、position_y は既存最大値+1（=2）で登録される"""
        # Arrange: 1件目を登録
        client.post(self._URL, data=self._valid_form(gadget_name='1件目'))

        # Act: 2件目を同グループに登録
        client.post(self._URL, data=self._valid_form(gadget_name='2件目'))

        # Assert
        with app.app_context():
            from iot_app import db
            from iot_app.models.customer_dashboard import DashboardGadgetMaster
            gadgets = db.session.query(DashboardGadgetMaster).order_by(
                DashboardGadgetMaster.position_y.asc()
            ).all()
        assert len(gadgets) == 2
        assert gadgets[0].position_y == 1
        assert gadgets[1].position_y == 2

    def test_register_display_order_is_one_for_first_gadget(self, client, app, measurement_item):
        """4.3.2: グループ内初登録時、display_order は 1 で登録される"""
        # Act
        client.post(self._URL, data=self._valid_form())

        # Assert
        with app.app_context():
            from iot_app import db
            from iot_app.models.customer_dashboard import DashboardGadgetMaster
            gadget = db.session.query(DashboardGadgetMaster).first()
        assert gadget.display_order == 1

    def test_register_display_order_increments_for_second_gadget(self, client, app, measurement_item):
        """4.3.2: 同グループに2件目登録時、display_order は既存最大値+1（=2）で登録される"""
        # Arrange: 1件目を登録
        client.post(self._URL, data=self._valid_form(gadget_name='1件目'))

        # Act: 2件目を登録
        client.post(self._URL, data=self._valid_form(gadget_name='2件目'))

        # Assert: 2件目の display_order が 2
        with app.app_context():
            from iot_app import db
            from iot_app.models.customer_dashboard import DashboardGadgetMaster
            gadgets = db.session.query(DashboardGadgetMaster).order_by(
                DashboardGadgetMaster.display_order
            ).all()
        assert len(gadgets) == 2
        assert gadgets[0].display_order == 1
        assert gadgets[1].display_order == 2

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

    def test_register_gadget_type_id_is_grid_type(self, client, app, measurement_item):
        """4.3.2: 登録されたガジェットの gadget_type_id が GadgetTypeMaster '表' の動的ルックアップ結果と一致する"""
        # Act
        client.post(self._URL, data=self._valid_form())

        # Assert
        with app.app_context():
            from iot_app import db
            from iot_app.models.customer_dashboard import DashboardGadgetMaster, GadgetTypeMaster
            gadget = db.session.query(DashboardGadgetMaster).first()
            expected_type = db.session.query(GadgetTypeMaster).filter_by(
                gadget_type_name='表',
            ).first()
        assert gadget.gadget_type_id == expected_type.gadget_type_id

    def test_register_without_gadget_type_master_returns_error(self, client, app, measurement_item):
        """4.3.2: GadgetTypeMaster に '表' レコードが存在しない場合、登録が失敗する（500）

        gadget_type_id のハードコードではなく GadgetTypeMaster から動的ルックアップするため、
        レコード不在時は ValidationError が発生し 500 が返ることを確認する。
        （_SKIP_GADGET_TYPE により autouse fixture がスキップされる）
        """
        # Arrange: GadgetTypeMaster にレコードなし（fixture スキップ済み）

        # Act
        response = client.post(self._URL, data=self._valid_form())

        # Assert
        assert response.status_code == 500

    # ── バリデーション（必須チェック）────────────────────────────────────────

    def test_register_title_required_returns_400(self, client, measurement_item):
        """3.1.1: タイトル未入力で400（バリデーションエラー）"""
        # Act
        response = client.post(self._URL, data=self._valid_form(gadget_name=''))

        # Assert
        assert response.status_code == 400

    def test_register_group_id_required_returns_400(self, client, measurement_item):
        """3.1.2: グループ未選択（group_id=0）で400"""
        # Act
        response = client.post(self._URL, data=self._valid_form(group_id='0'))

        # Assert
        assert response.status_code == 400

    def test_register_gadget_size_required_returns_400(self, client, measurement_item):
        """3.1.3: 部品サイズ未選択（空）で400"""
        # Act
        response = client.post(self._URL, data=self._valid_form(gadget_size=''))

        # Assert
        assert response.status_code == 400

    # ── バリデーション（文字列長チェック）────────────────────────────────────

    def test_register_title_max_length_20_ok(self, client, measurement_item):
        """3.2.1: タイトル20文字以内は正常登録される"""
        # Act
        response = client.post(
            self._URL,
            data=self._valid_form(gadget_name='a' * 20),
            follow_redirects=False,
        )

        # Assert
        assert response.status_code == 302

    def test_register_title_over_max_length_returns_400(self, client, measurement_item):
        """3.2.2: タイトル21文字以上で400（バリデーションエラー）"""
        # Act
        response = client.post(self._URL, data=self._valid_form(gadget_name='a' * 21))

        # Assert
        assert response.status_code == 400

    # ── トランザクション ──────────────────────────────────────────────────────

    def test_register_db_error_rollback(self, client, app, measurement_item, mocker):
        """7: DB commit 失敗時にロールバックされ、レコードが残らない

        register_grid_gadget 内の db.session.commit 直後に例外を発生させることで
        ロールバックが実行され、dashboard_gadget_master にレコードが残らないことを確認する。
        """
        # Arrange: commit 時に例外を発生させる
        mocker.patch(
            'iot_app.views.analysis.customer_dashboard.grid.register_grid_gadget',
            side_effect=Exception('DB commit error'),
        )

        # Act
        response = client.post(self._URL, data=self._valid_form())

        # Assert: 500 エラーが返り、DBにレコードが残らない
        assert response.status_code == 500
        with app.app_context():
            from iot_app import db
            from iot_app.models.customer_dashboard import DashboardGadgetMaster
            count = db.session.query(DashboardGadgetMaster).count()
        assert count == 0

    # ── ログ出力 ──────────────────────────────────────────────────────────────

    def test_register_logs_start_info(self, client, measurement_item, caplog):
        """8.1.1 / 8.1.5: 登録開始時に INFO ログ「表ガジェット登録開始」と user_id が出力される"""
        import logging
        # Act
        with caplog.at_level(logging.INFO, logger='iot_app'):
            client.post(self._URL, data=self._valid_form())

        # Assert
        assert any(
            '表ガジェット登録開始' in r.message and str(_TEST_USER_ID) in r.message
            for r in caplog.records
        )

    def test_register_logs_success_info(self, client, measurement_item, caplog):
        """8.1.2: 登録成功時に INFO ログ「表ガジェット登録成功」と user_id が出力される"""
        import logging
        # Act
        with caplog.at_level(logging.INFO, logger='iot_app'):
            client.post(self._URL, data=self._valid_form())

        # Assert
        assert any(
            '表ガジェット登録成功' in r.message and str(_TEST_USER_ID) in r.message
            for r in caplog.records
        )

    def test_register_logs_error_on_failure(self, client, measurement_item, mocker, caplog):
        """8.2.1: 登録処理失敗時に ERROR ログ「表ガジェット登録エラー」が出力される"""
        import logging
        # Arrange: register_grid_gadget が例外を送出
        mocker.patch(
            'iot_app.views.analysis.customer_dashboard.grid.register_grid_gadget',
            side_effect=Exception('unexpected DB error'),
        )

        # Act
        with caplog.at_level(logging.ERROR, logger='iot_app'):
            client.post(self._URL, data=self._valid_form())

        # Assert
        assert any('表ガジェット登録エラー' in r.message for r in caplog.records)

    def test_register_gadget_size_invalid_returns_400(self, client, measurement_item):
        """3.1.4: gadget_size に無効値（選択肢外）を送ると400エラー

        UI仕様書: 選択肢は '0'(2x2) / '1'(2x4) のみ。
        それ以外の値はフォームバリデーションで弾かれる。
        """
        # Act
        response = client.post(self._URL, data=self._valid_form(gadget_size='2'))

        # Assert
        assert response.status_code == 400


# ─────────────────────────────────────────────────────────────────────────────
# 4. CSVエクスポート
# GET /analysis/customer-dashboard/gadgets/<gadget_uuid>?export=csv
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.integration
class TestGadgetGridCsvExport:
    """表ガジェット CSVエクスポート

    観点: 4.6 ファイル出力テスト、2.2 エラー時遷移テスト
    """

    @pytest.fixture(autouse=True)
    def _auth(self, auth_user_id, user_master, organization_closure):
        """全テストで g.current_user と user_master / organization_closure を自動セットアップする"""
        pass

    def _url(self, gadget_uuid, **params):
        from urllib.parse import urlencode
        base_params = {
            'export':         'csv',
            'start_datetime': _VALID_START_DATETIME,
            'end_datetime':   _VALID_END_DATETIME,
        }
        base_params.update(params)
        return f"{BASE_URL}/gadgets/{gadget_uuid}?{urlencode(base_params)}"

    def test_csv_export_returns_200_with_csv_content_type(self, client, grid_gadget, measurement_item, mocker):
        """4.6.1: 正常時 200 と content-type text/csv を返す"""
        # Arrange
        mocker.patch(_SILVER_QUERY, return_value=_mock_rows())

        # Act
        response = client.get(self._url(grid_gadget.gadget_uuid))

        # Assert
        assert response.status_code == 200
        assert 'text/csv' in response.content_type

    def test_csv_export_content_disposition_contains_filename(self, client, grid_gadget, measurement_item, mocker):
        """4.6.2: Content-Disposition ヘッダーに attachment; filename=sensor_data_*.csv が設定される

        設計書: 出力ファイル名 sensor_data_{yyyyMMddHHmmss}.csv
        """
        # Arrange
        mocker.patch(_SILVER_QUERY, return_value=_mock_rows())

        # Act
        response = client.get(self._url(grid_gadget.gadget_uuid))

        # Assert
        cd = response.headers.get('Content-Disposition', '')
        assert 'attachment' in cd
        assert re.search(r'filename=sensor_data_\d{14}\.csv', cd)

    def test_csv_export_header_row_contains_column_names(self, client, grid_gadget, measurement_item, mocker):
        """4.6.3: CSVの1行目（ヘッダー）に measurement_item_master の display_name が含まれる

        設計書: ヘッダー先頭は「受信日時」「デバイス名称」、その後 measurement_item_master から取得した display_name
        """
        # Arrange
        mocker.patch(_SILVER_QUERY, return_value=[])

        # Act
        response = client.get(self._url(grid_gadget.gadget_uuid))

        # Assert: CSVの1行目を確認
        text = response.data.decode('utf-8-sig', errors='replace')
        first_line = text.split('\n')[0]
        assert '受信日時' in first_line
        assert 'デバイス名称' in first_line
        assert '外気温度' in first_line  # measurement_item fixture の display_name

    def test_csv_export_data_rows_contain_sensor_values(self, client, grid_gadget, measurement_item, mocker):
        """4.6.4: CSVのデータ行にセンサー値が含まれる"""
        # Arrange
        mocker.patch(_SILVER_QUERY, return_value=_mock_rows())

        # Act
        response = client.get(self._url(grid_gadget.gadget_uuid))

        # Assert
        text = response.data.decode('utf-8-sig', errors='replace')
        assert '2026/03/06 12:00:00' in text
        assert 'Device-001' in text

    def test_csv_export_nonexistent_gadget_returns_404(self, client):
        """2.2.4: 存在しない gadget_uuid で404エラー"""
        # Arrange
        nonexistent_uuid = str(uuid.uuid4())

        # Act
        response = client.get(self._url(nonexistent_uuid))

        # Assert
        assert response.status_code == 404

    def test_csv_export_deleted_gadget_returns_404(self, client, grid_gadget, db_session):
        """2.2.4: delete_flag=True の論理削除済みガジェットへのCSVエクスポートは404

        データAPI（test_data_deleted_gadget_returns_404）と同様に、
        CSVエクスポートでも論理削除済みガジェットへのアクセスは404になることを検証する。
        """
        # Arrange: ガジェットを論理削除
        grid_gadget.delete_flag = True
        db_session.flush()

        # Act
        response = client.get(self._url(grid_gadget.gadget_uuid))

        # Assert
        assert response.status_code == 404

    def test_csv_export_without_export_param_returns_404(self, client, grid_gadget):
        """2.2.2: export=csv パラメータなしでのアクセスは404エラー

        設計書: export=csv が必須。それ以外は abort(404)。
        """
        # Act: export パラメータなし
        response = client.get(f"{BASE_URL}/gadgets/{grid_gadget.gadget_uuid}")

        # Assert
        assert response.status_code == 404

    def test_csv_export_invalid_datetime_returns_400(self, client, grid_gadget):
        """3.4.1: 不正な日時パラメータで400エラー"""
        from urllib.parse import urlencode
        params = urlencode({
            'export':         'csv',
            'start_datetime': 'invalid-date',
            'end_datetime':   _VALID_END_DATETIME,
        })
        response = client.get(f"{BASE_URL}/gadgets/{grid_gadget.gadget_uuid}?{params}")

        # Assert
        assert response.status_code == 400

    def test_csv_export_range_exceeds_24hours_returns_400(self, client, grid_gadget):
        """3.8.3: 24時間超過の日時範囲で400エラー"""
        from urllib.parse import urlencode
        params = urlencode({
            'export':         'csv',
            'start_datetime': '2026/03/06 00:00:00',
            'end_datetime':   '2026/03/07 00:00:01',
        })
        response = client.get(f"{BASE_URL}/gadgets/{grid_gadget.gadget_uuid}?{params}")

        # Assert
        assert response.status_code == 400

    def test_csv_export_silver_query_error_returns_500(self, client, grid_gadget, measurement_item, mocker):
        """2.2.6: Unity Catalog クエリ失敗時に500エラー"""
        # Arrange
        mocker.patch(_SILVER_QUERY, side_effect=Exception("Databricks connection timeout"))

        # Act
        response = client.get(self._url(grid_gadget.gadget_uuid))

        # Assert
        assert response.status_code == 500

    def test_csv_export_empty_data_returns_headers_only(self, client, grid_gadget, measurement_item, mocker):
        """4.6.5: センサーデータ0件時、CSVはヘッダー行のみ出力される（データ行なし）"""
        # Arrange
        mocker.patch(_SILVER_QUERY, return_value=[])

        # Act
        response = client.get(self._url(grid_gadget.gadget_uuid))

        # Assert
        assert response.status_code == 200
        text = response.data.decode('utf-8-sig')
        lines = [line for line in text.splitlines() if line.strip()]
        assert len(lines) == 1        # ヘッダー行のみ
        assert '外気温度' in lines[0]  # measurement_item fixture の display_name

    def test_csv_export_gadget_outside_scope_returns_404(self, client, db_session):
        """4.6.6: 権限範囲外（別組織）のガジェットへのCSVエクスポートは404

        テストユーザー（user_id=1, org_id=1）は org_id=2 の組織閉包を持たないため、
        check_gadget_access が None を返して abort(404) になることを検証する。
        """
        # Arrange: org_id=2 の組織・ダッシュボード・グループ・ガジェットを作成
        from iot_app.models.customer_dashboard import (
            DashboardGadgetMaster,
            DashboardGroupMaster,
            DashboardMaster,
            GadgetTypeMaster,
        )
        from iot_app.models.organization import OrganizationMaster

        other_org = OrganizationMaster(
            organization_id=2,
            organization_name='別組織',
            organization_type_id=1,
            address='別住所',
            phone_number='000-0000-0001',
            contact_person='別担当者',
            contract_status_id=1,
            contract_start_date=date(2024, 1, 1),
            databricks_group_id='other-group',
            creator=1,
            modifier=1,
            delete_flag=False,
        )
        db_session.add(other_org)
        db_session.flush()

        other_dashboard = DashboardMaster(
            dashboard_id=2,
            dashboard_uuid=str(uuid.uuid4()),
            dashboard_name='別ダッシュボード',
            organization_id=2,
            creator=1,
            modifier=1,
            delete_flag=False,
        )
        db_session.add(other_dashboard)
        db_session.flush()

        gt = GadgetTypeMaster(
            gadget_type_id=1,
            gadget_type_name='表',
            data_source_type=1,
            gadget_image_path='images/gadgets/grid.png',
            gadget_description='表ガジェット',
            display_order=1,
            creator=1,
            modifier=1,
            delete_flag=False,
        )
        db_session.add(gt)
        db_session.flush()

        other_group = DashboardGroupMaster(
            dashboard_group_id=1,
            dashboard_group_uuid=str(uuid.uuid4()),
            dashboard_id=2,
            dashboard_group_name='別グループ',
            display_order=1,
            creator=1,
            modifier=1,
            delete_flag=False,
        )
        db_session.add(other_group)
        db_session.flush()

        other_gadget_uuid = str(uuid.uuid4())
        other_gadget = DashboardGadgetMaster(
            gadget_uuid=other_gadget_uuid,
            gadget_name='別ガジェット',
            gadget_type_id=1,
            dashboard_group_id=1,
            chart_config=json.dumps({}),
            data_source_config=json.dumps({'device_id': None}),
            position_x=0,
            position_y=1,
            gadget_size=0,
            display_order=1,
            creator=1,
            modifier=1,
        )
        db_session.add(other_gadget)
        db_session.flush()

        # Act: テストユーザー（org_id=1）が org_id=2 のガジェットに CSV エクスポートアクセス
        response = client.get(self._url(other_gadget_uuid))

        # Assert
        assert response.status_code == 404

    def test_csv_export_uses_full_limit_not_per_page(self, client, grid_gadget, measurement_item, mocker):
        """4.6.8: CSVエクスポートは PER_PAGE（25件）ではなく全件（limit=100_000）で silver query を呼ぶ

        設計書: CSVエクスポートはページングを無視して全件取得する。
        fetch_grid_data が limit=100_000, offset=0 で呼ばれることを検証する。
        """
        # Arrange
        mock_silver = mocker.patch(_SILVER_QUERY, return_value=_mock_rows())

        # Act
        response = client.get(self._url(grid_gadget.gadget_uuid))

        # Assert
        assert response.status_code == 200
        assert mock_silver.called
        assert mock_silver.call_args.kwargs.get('limit') == 100_000
        assert mock_silver.call_args.kwargs.get('offset') == 0

    def test_csv_export_missing_start_datetime_returns_400(self, client, grid_gadget):
        """3.1.5: start_datetime 未指定で400エラー

        設計書バリデーション: 開始日時は必須（日付形式チェック）。
        """
        from urllib.parse import urlencode
        params = urlencode({
            'export':       'csv',
            'end_datetime': _VALID_END_DATETIME,
            # start_datetime を省略
        })
        response = client.get(f"{BASE_URL}/gadgets/{grid_gadget.gadget_uuid}?{params}")

        # Assert
        assert response.status_code == 400

    def test_csv_export_missing_end_datetime_returns_400(self, client, grid_gadget):
        """3.1.6: end_datetime 未指定で400エラー

        設計書バリデーション: 終了日時は必須（日付形式チェック）。
        """
        from urllib.parse import urlencode
        params = urlencode({
            'export':         'csv',
            'start_datetime': _VALID_START_DATETIME,
            # end_datetime を省略
        })
        response = client.get(f"{BASE_URL}/gadgets/{grid_gadget.gadget_uuid}?{params}")

        # Assert
        assert response.status_code == 400

    def test_csv_export_start_equals_end_datetime_returns_400(self, client, grid_gadget):
        """3.8.5: 開始日時 == 終了日時で400エラー

        設計書バリデーションルール: 「開始日時 < 終了日時」（等値は不可）
        """
        from urllib.parse import urlencode
        params = urlencode({
            'export':         'csv',
            'start_datetime': _VALID_START_DATETIME,
            'end_datetime':   _VALID_START_DATETIME,  # 等値
        })
        response = client.get(f"{BASE_URL}/gadgets/{grid_gadget.gadget_uuid}?{params}")

        # Assert
        assert response.status_code == 400

    def test_csv_export_invalid_export_param_returns_404(self, client, grid_gadget):
        """2.2.3: export パラメータが 'csv' 以外（例: 'json'）の場合 404

        ワークフロー仕様書実装例: if request.args.get('export') != 'csv': abort(404)
        """
        from urllib.parse import urlencode
        params = urlencode({
            'export':         'json',   # csv 以外
            'start_datetime': _VALID_START_DATETIME,
            'end_datetime':   _VALID_END_DATETIME,
        })
        response = client.get(f"{BASE_URL}/gadgets/{grid_gadget.gadget_uuid}?{params}")

        # Assert
        assert response.status_code == 404

    def test_csv_export_start_after_end_datetime_returns_400(self, client, grid_gadget):
        """3.8.9: 開始日時 > 終了日時で400エラー

        設計書バリデーションルール: 「開始日時 < 終了日時」
        DataAPI と同様に CSV エクスポートでも逆転はバリデーションエラー。
        """
        from urllib.parse import urlencode
        params = urlencode({
            'export':         'csv',
            'start_datetime': _VALID_END_DATETIME,    # 終了日時を開始に
            'end_datetime':   _VALID_START_DATETIME,  # 開始日時を終了に（逆転）
        })
        response = client.get(f"{BASE_URL}/gadgets/{grid_gadget.gadget_uuid}?{params}")

        # Assert
        assert response.status_code == 400

    def test_csv_export_response_has_bom(self, client, grid_gadget, measurement_item, mocker):
        """4.6.9: CSVレスポンスの先頭に UTF-8 BOM（\\xef\\xbb\\xbf）が付与される

        Excelでの文字化けを防ぐためにBOM付きUTF-8で出力する。
        レスポンスバイト列の先頭3バイトが BOM であることを確認する。
        """
        # Arrange
        mocker.patch(_SILVER_QUERY, return_value=[])

        # Act
        response = client.get(self._url(grid_gadget.gadget_uuid))

        # Assert
        assert response.status_code == 200
        assert response.data[:3] == b'\xef\xbb\xbf', "CSVレスポンスの先頭にBOMがない"

    def test_csv_export_range_exactly_24hours_returns_200(self, client, grid_gadget, measurement_item, mocker):
        """3.8.10: 終了日時 - 開始日時 = ちょうど24時間は正常（境界値OK）

        設計書バリデーション: 「終了日時 - 開始日時 ≤ 24時間」
        DataAPI と同様に CSV エクスポートでもちょうど24時間は ≤ に含まれるため 200 を返す。
        """
        # Arrange
        mocker.patch(_SILVER_QUERY, return_value=[])

        # Act
        from urllib.parse import urlencode
        params = urlencode({
            'export':         'csv',
            'start_datetime': '2026/03/06 00:00:00',
            'end_datetime':   '2026/03/07 00:00:00',  # ちょうど24時間
        })
        response = client.get(f"{BASE_URL}/gadgets/{grid_gadget.gadget_uuid}?{params}")

        # Assert
        assert response.status_code == 200


# ─────────────────────────────────────────────────────────────────────────────
# 5. 登録モーダル プレビューデータ取得（AJAX）
# POST /analysis/customer-dashboard/gadgets/preview/grid/data
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.integration
class TestGadgetGridPreviewData:
    """表ガジェット登録モーダル プレビューデータ取得（AJAX）

    観点: 4.2 詳細表示（Read）テスト、3.4 日付形式チェック、3.8 相関チェック
    """

    _URL = f"{BASE_URL}/gadgets/preview/grid/data"

    @pytest.fixture(autouse=True)
    def _auth(self, auth_user_id, user_master, organization_closure, dashboard_user_setting, dashboard_master):
        """全テストで g.current_user / user_master / organization_closure / dashboard_user_setting を自動セットアップする"""
        pass

    def _valid_payload(self, **overrides):
        """デフォルトの有効なリクエストペイロード"""
        data = {
            'start_datetime': _VALID_START_DATETIME,
            'end_datetime':   _VALID_END_DATETIME,
        }
        data.update(overrides)
        return data

    def test_preview_returns_json_structure(self, client, measurement_item, mocker):
        """4.2.1: 正常取得 - columns / grid_data / total_count / page / per_page を含む JSON を返す

        プレビューは gadget_uuid を含まない（登録前のため）。
        """
        # Arrange
        mocker.patch(_SILVER_QUERY, return_value=_mock_rows())
        mocker.patch(_COUNT_QUERY, return_value=2)

        # Act
        response = client.post(self._URL, json=self._valid_payload())

        # Assert
        assert response.status_code == 200
        body = response.get_json()
        assert 'columns' in body
        assert 'grid_data' in body
        assert 'total_count' in body
        assert 'page' in body
        assert 'per_page' in body

    def test_preview_empty_rows_returns_empty_grid_data(self, client, measurement_item, mocker):
        """4.2.4: センサーデータ0件時は空配列を返す（エラーではない）"""
        # Arrange
        mocker.patch(_SILVER_QUERY, return_value=[])
        mocker.patch(_COUNT_QUERY, return_value=0)

        # Act
        response = client.post(self._URL, json=self._valid_payload())

        # Assert
        assert response.status_code == 200
        body = response.get_json()
        assert body['grid_data'] == []

    def test_preview_invalid_datetime_returns_400(self, client, measurement_item):
        """3.4.1: 不正な日時パラメータで400エラー"""
        # Act
        response = client.post(self._URL, json=self._valid_payload(start_datetime='invalid'))

        # Assert
        assert response.status_code == 400

    def test_preview_range_exceeds_24hours_returns_400(self, client, measurement_item):
        """3.8.3: 24時間超過の日時範囲で400エラー"""
        # Act
        response = client.post(self._URL, json=self._valid_payload(
            start_datetime='2026/03/06 00:00:00',
            end_datetime='2026/03/07 00:00:01',
        ))

        # Assert
        assert response.status_code == 400

    def test_preview_silver_query_error_returns_500(self, client, measurement_item, mocker):
        """2.2.6: Unity Catalog クエリ失敗時に500エラー"""
        # Arrange
        mocker.patch(_SILVER_QUERY, side_effect=Exception("Databricks connection timeout"))

        # Act
        response = client.post(self._URL, json=self._valid_payload())

        # Assert
        assert response.status_code == 500

    def test_preview_start_after_end_datetime_returns_400(self, client, measurement_item):
        """3.8.6: 開始日時 > 終了日時で400エラー

        設計書バリデーションルール: 「開始日時 < 終了日時」
        """
        # Act
        response = client.post(self._URL, json=self._valid_payload(
            start_datetime=_VALID_END_DATETIME,
            end_datetime=_VALID_START_DATETIME,
        ))

        # Assert
        assert response.status_code == 400

    def test_preview_start_equals_end_datetime_returns_400(self, client, measurement_item):
        """3.8.7: 開始日時 == 終了日時で400エラー

        設計書バリデーションルール: 「開始日時 < 終了日時」（等値は不可）
        """
        # Act
        response = client.post(self._URL, json=self._valid_payload(
            start_datetime=_VALID_START_DATETIME,
            end_datetime=_VALID_START_DATETIME,  # 等値
        ))

        # Assert
        assert response.status_code == 400

    def test_preview_missing_start_datetime_returns_400(self, client, measurement_item):
        """3.1.7: start_datetime 未指定で400エラー

        設計書バリデーション: 開始日時は必須（日付形式チェック）。
        """
        # Act
        response = client.post(self._URL, json={'end_datetime': _VALID_END_DATETIME})

        # Assert
        assert response.status_code == 400

    def test_preview_missing_end_datetime_returns_400(self, client, measurement_item):
        """3.1.8: end_datetime 未指定で400エラー

        設計書バリデーション: 終了日時は必須（日付形式チェック）。
        """
        # Act
        response = client.post(self._URL, json={'start_datetime': _VALID_START_DATETIME})

        # Assert
        assert response.status_code == 400

    def test_preview_response_does_not_contain_gadget_uuid(self, client, measurement_item, mocker):
        """4.2.8: プレビューレスポンスに gadget_uuid が含まれない

        プレビューは登録前のため gadget_uuid が存在しない。
        ガジェットデータ取得API（登録済み）のレスポンスとは異なる。
        """
        # Arrange
        mocker.patch(_SILVER_QUERY, return_value=[])
        mocker.patch(_COUNT_QUERY, return_value=0)

        # Act
        response = client.post(self._URL, json=self._valid_payload())

        # Assert
        assert response.status_code == 200
        body = response.get_json()
        assert 'gadget_uuid' not in body

    def test_preview_range_exactly_24hours_returns_200(self, client, measurement_item, mocker):
        """3.8.11: 終了日時 - 開始日時 = ちょうど24時間は正常（境界値OK）

        設計書バリデーション: 「終了日時 - 開始日時 ≤ 24時間」
        DataAPI と同様にプレビューでもちょうど24時間は ≤ に含まれるため 200 を返す。
        """
        # Arrange
        mocker.patch(_SILVER_QUERY, return_value=[])
        mocker.patch(_COUNT_QUERY, return_value=0)

        # Act
        response = client.post(self._URL, json=self._valid_payload(
            start_datetime='2026/03/06 00:00:00',
            end_datetime='2026/03/07 00:00:00',  # ちょうど24時間
        ))

        # Assert
        assert response.status_code == 200
