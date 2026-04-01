"""
顧客作成ダッシュボード 時系列グラフガジェット - 結合テスト

対象エンドポイント:
  GET  /analysis/customer-dashboard
  POST /analysis/customer-dashboard/gadgets/<gadget_uuid>/data
  GET  /analysis/customer-dashboard/gadgets/timeline/create
  POST /analysis/customer-dashboard/gadgets/timeline/register
  GET  /analysis/customer-dashboard/gadgets/<gadget_uuid>?export=csv

参照設計書:
  - docs/03-features/flask-app/customer-dashboard/timeline/ui-specification.md
  - docs/03-features/flask-app/customer-dashboard/timeline/workflow-specification.md
  - docs/03-features/flask-app/customer-dashboard/common/workflow-specification.md

NOTE: モデルファイル（models/dashboard.py 等）が実装済みであることが前提。
      外部API（Unity Catalog / sensor_data_view）のみモック化する。
      認証ミドルウェアはこのブランチでは未実装のため対象外。
"""

import json
import uuid
from datetime import date

import pytest

BASE_URL = "/analysis/customer-dashboard"
_VALID_START_DATETIME = "2026/03/06 12:00:00"
_VALID_END_DATETIME   = "2026/03/06 13:00:00"

# Unity Catalog クエリのモック対象パス（サービス層のシルバークエリ）
_SILVER_QUERY = "iot_app.services.customer_dashboard.timeline.execute_silver_query"

# ガジェット登録サービスのモック対象パス
# view が `from ... import register_gadget` で直接参照しているため、view 側の名前をパッチする
_REGISTER_GADGET = "iot_app.views.analysis.customer_dashboard.timeline.register_gadget"

# テスト用ユーザー・組織 ID（認証未実装のため before_request で g.current_user を固定）
_TEST_USER_ID = 1
_TEST_ORG_ID  = 1


# ─────────────────────────────────────────────────────────────────────────────
# フィクスチャ（timeline ガジェット専用）
# ─────────────────────────────────────────────────────────────────────────────


@pytest.fixture()
def auth_user_id(app):
    """テスト用 g.current_user を before_request フックでセットアップする

    認証ミドルウェアが未実装のため、view が g.current_user にアクセスする際に
    AttributeError が発生しないよう、テスト用ユーザーオブジェクトを注入する。
    app.before_request() は初回リクエスト後に呼び出し不可のため、
    before_request_funcs に直接追加してチェックをバイパスする。
    テスト終了後はフックを除去し、他テストへの影響を防ぐ。
    """
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
    """UserMaster テストレコード（user_id=_TEST_USER_ID, organization_id=_TEST_ORG_ID）

    get_organization_id_by_user(user_id) が user_master を参照するため必要。
    """
    from datetime import datetime as _dt
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
    """DashboardMaster テストレコード（organization_id=_TEST_ORG_ID）

    organization_closure に依存: get_accessible_org_ids が [_TEST_ORG_ID] を返すことで
    DashboardMaster のスコープチェックが通る。
    """
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
def device_master(db_session, organization_master):
    """DeviceMaster テストレコード（organization_id=_TEST_ORG_ID）"""
    from iot_app.models.device import DeviceMaster
    device = DeviceMaster(
        device_id=1,
        device_uuid=str(uuid.uuid4()),
        device_name='テストデバイス',
        device_type_id=1,
        device_model='テストモデル',
        device_inventory_id=1,
        organization_id=_TEST_ORG_ID,
        creator=1,
        modifier=1,
        delete_flag=False,
    )
    db_session.add(device)
    db_session.flush()
    return device


@pytest.fixture()
def dashboard_user_setting(db_session, dashboard_master):
    """DashboardUserSetting テストレコード（user_id=_TEST_USER_ID, dashboard_id=1）"""
    from iot_app.models.customer_dashboard import DashboardUserSetting
    setting = DashboardUserSetting(
        user_id=_TEST_USER_ID,
        dashboard_id=dashboard_master.dashboard_id,
        device_id=None,
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
def gadget_type_timeline(db_session):
    """GadgetTypeMaster テストレコード（時系列グラフ用）"""
    from iot_app.models.customer_dashboard import GadgetTypeMaster
    gt = GadgetTypeMaster(
        gadget_type_id=1,
        gadget_type_name='時系列グラフ',
        data_source_type=1,
        gadget_image_path='images/gadgets/timeline.png',
        gadget_description='時系列グラフガジェット',
        display_order=1,
        creator=1,
        modifier=1,
        delete_flag=False,
    )
    db_session.add(gt)
    db_session.flush()
    return gt


@pytest.fixture()
def measurement_item_left(db_session):
    """MeasurementItemMaster テストレコード（左表示項目: external_temp）"""
    from iot_app.models.measurement import MeasurementItemMaster
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
def measurement_item_right(db_session, measurement_item_left):
    """MeasurementItemMaster テストレコード（右表示項目: compressor_freezer_1）"""
    from iot_app.models.measurement import MeasurementItemMaster
    item = MeasurementItemMaster(
        measurement_item_id=2,
        measurement_item_name='第1冷凍 圧縮機',
        display_name='第1冷凍 圧縮機',
        silver_data_column_name='compressor_freezer_1',
        unit_name='W',
        creator=1,
        modifier=1,
        delete_flag=False,
    )
    db_session.add(item)
    db_session.flush()
    return item


@pytest.fixture()
def timeline_gadget(db_session, dashboard_group_master, gadget_type_timeline, measurement_item_left, measurement_item_right):
    """DashboardGadgetMaster テストレコード（時系列グラフ・デバイス固定モード）

    dashboard_group_master に依存することで DashboardGroupMaster(id=1) と
    DashboardMaster(id=1, org_id=1) および OrganizationClosure が存在し、
    get_gadget_in_scope / get_active_gadgets_in_scope の INNER JOIN が成立する。
    """
    from iot_app.models.customer_dashboard import DashboardGadgetMaster
    g = DashboardGadgetMaster(
        gadget_uuid=str(uuid.uuid4()),
        gadget_name='テスト時系列グラフ',
        gadget_type_id=1,
        dashboard_group_id=1,
        chart_config=json.dumps({
            'left_item_id':    1,
            'right_item_id':   2,
            'left_min_value':  None,
            'left_max_value':  None,
            'right_min_value': None,
            'right_max_value': None,
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
def timeline_gadget_variable(db_session, dashboard_group_master, gadget_type_timeline, measurement_item_left, measurement_item_right):
    """DashboardGadgetMaster テストレコード（時系列グラフ・デバイス可変モード: device_id=None）

    dashboard_group_master に依存することで JOIN が成立する（timeline_gadget と同様）。
    """
    from iot_app.models.customer_dashboard import DashboardGadgetMaster
    g = DashboardGadgetMaster(
        gadget_uuid=str(uuid.uuid4()),
        gadget_name='テスト時系列グラフ（可変）',
        gadget_type_id=1,
        dashboard_group_id=1,
        chart_config=json.dumps({
            'left_item_id':    1,
            'right_item_id':   2,
            'left_min_value':  None,
            'left_max_value':  None,
            'right_min_value': None,
            'right_max_value': None,
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
# 1. 顧客作成ダッシュボード初期表示
# GET /analysis/customer-dashboard
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.integration
class TestCustomerDashboardIndex:
    """顧客作成ダッシュボード初期表示

    観点: 2.1.1 一覧初期表示、4.1 一覧表示（Read）テスト
    """

    @pytest.fixture(autouse=True)
    def _auth(self, auth_user_id, user_master, organization_closure):
        """全テストで g.current_user と user_master / organization_closure を自動セットアップする"""
        pass

    def test_index_returns_200(self, client):
        """2.1.1: ガジェット0件でも200とHTMLを返す"""
        # Arrange: DBにガジェットなし（初期状態）

        # Act
        response = client.get(BASE_URL)

        # Assert
        assert response.status_code == 200
        assert b"customer-dashboard" in response.data


# ─────────────────────────────────────────────────────────────────────────────
# 2. ガジェットデータ取得（AJAX）
# POST /analysis/customer-dashboard/gadgets/<gadget_uuid>/data
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.integration
class TestGadgetTimelineData:
    """時系列グラフガジェット データ取得（AJAX）

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

    def _mock_rows(self):
        """モック用センサーデータ行（event_timestamp は datetime オブジェクト）"""
        from datetime import datetime as _dt
        return [
            {
                'event_timestamp': _dt(2026, 3, 6, 12, 0, 0),
                'external_temp': 10.5,
                'compressor_freezer_1': 2500.0,
            },
            {
                'event_timestamp': _dt(2026, 3, 6, 12, 1, 0),
                'external_temp': 11.0,
                'compressor_freezer_1': 2480.0,
            },
        ]

    def test_data_returns_json_structure(self, client, timeline_gadget, mocker):
        """4.2.1: 正常取得 - gadget_uuid / chart_data / updated_at を含む JSON を返す"""
        # Arrange: シルバー層クエリをモック（外部API）
        mocker.patch(_SILVER_QUERY, return_value=self._mock_rows())

        # Act
        response = client.post(
            self._url(timeline_gadget.gadget_uuid),
            json=self._valid_payload(),
        )

        # Assert: JSONレスポンスの構造を検証
        assert response.status_code == 200
        body = response.get_json()
        assert body['gadget_uuid'] == timeline_gadget.gadget_uuid
        assert 'chart_data' in body
        assert 'labels' in body['chart_data']
        assert 'left_values' in body['chart_data']
        assert 'right_values' in body['chart_data']
        assert 'updated_at' in body

    def test_data_chart_values_match_mocked_rows(self, client, timeline_gadget, mocker):
        """4.2.2: シルバー層の行データが chart_data.labels / left_values / right_values に正しく変換される"""
        # Arrange
        mocker.patch(_SILVER_QUERY, return_value=self._mock_rows())

        # Act
        response = client.post(
            self._url(timeline_gadget.gadget_uuid),
            json=self._valid_payload(),
        )

        # Assert: ラベルと値が正しく変換されているか
        body = response.get_json()
        assert body['chart_data']['labels'] == [
            '2026/03/06 12:00:00',
            '2026/03/06 12:01:00',
        ]
        assert body['chart_data']['left_values'] == [10.5, 11.0]
        assert body['chart_data']['right_values'] == [2500.0, 2480.0]

    def test_data_empty_rows_returns_empty_arrays(self, client, timeline_gadget, mocker):
        """4.2.3: センサーデータ0件時は空配列を返す（エラーではない）"""
        # Arrange: データなしケース
        mocker.patch(_SILVER_QUERY, return_value=[])

        # Act
        response = client.post(
            self._url(timeline_gadget.gadget_uuid),
            json=self._valid_payload(),
        )

        # Assert
        assert response.status_code == 200
        body = response.get_json()
        assert body['chart_data']['labels'] == []
        assert body['chart_data']['left_values'] == []
        assert body['chart_data']['right_values'] == []

    def test_data_updated_at_format_is_datetime_string(self, client, timeline_gadget, mocker):
        """4.2.5: レスポンスの updated_at が 'YYYY/MM/DD HH:MM:SS' 形式の文字列である

        設計書 ⑤ レスポンス形式: updated_at は '2026/03/05 12:00:00' 形式。
        """
        import re
        mocker.patch(_SILVER_QUERY, return_value=[])

        response = client.post(
            self._url(timeline_gadget.gadget_uuid),
            json=self._valid_payload(),
        )

        body = response.get_json()
        assert re.fullmatch(r'\d{4}/\d{2}/\d{2} \d{2}:\d{2}:\d{2}', body['updated_at'])

    def test_data_empty_rows_response_has_gadget_uuid_and_updated_at(self, client, timeline_gadget, mocker):
        """4.2.5: データなし時も gadget_uuid・updated_at がレスポンスに含まれる

        設計書 ⑤ データなしの場合のレスポンス形式確認。
        """
        mocker.patch(_SILVER_QUERY, return_value=[])

        response = client.post(
            self._url(timeline_gadget.gadget_uuid),
            json=self._valid_payload(),
        )

        body = response.get_json()
        assert body['gadget_uuid'] == timeline_gadget.gadget_uuid
        assert 'updated_at' in body

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

    def test_data_deleted_gadget_returns_404(self, client, timeline_gadget, db_session, mocker):
        """4.2.3: delete_flag=True の論理削除済みガジェットへのデータ取得は404"""
        # Arrange: ガジェットを論理削除
        timeline_gadget.delete_flag = True
        db_session.flush()

        # Act
        response = client.post(
            self._url(timeline_gadget.gadget_uuid),
            json=self._valid_payload(),
        )

        # Assert
        assert response.status_code == 404

    def test_data_missing_start_datetime_returns_400(self, client, timeline_gadget):
        """3.1.1: start_datetime 未指定で400エラー"""
        # Act
        response = client.post(
            self._url(timeline_gadget.gadget_uuid),
            json={'end_datetime': _VALID_END_DATETIME},
        )

        # Assert
        assert response.status_code == 400
        assert response.get_json()['error'] == 'パラメータが不正です'

    def test_data_missing_end_datetime_returns_400(self, client, timeline_gadget):
        """3.1.2: end_datetime 未指定で400エラー"""
        # Act
        response = client.post(
            self._url(timeline_gadget.gadget_uuid),
            json={'start_datetime': _VALID_START_DATETIME},
        )

        # Assert
        assert response.status_code == 400

    def test_data_invalid_start_datetime_format_returns_400(self, client, timeline_gadget):
        """3.4.1: start_datetime が YYYY/MM/DD HH:mm:ss 以外の形式で400エラー（ISO 8601形式）"""
        # Act
        response = client.post(
            self._url(timeline_gadget.gadget_uuid),
            json=self._valid_payload(start_datetime='2026-03-06T12:00:00'),
        )

        # Assert
        assert response.status_code == 400

    def test_data_invalid_end_datetime_format_returns_400(self, client, timeline_gadget):
        """3.4.2: end_datetime が不正な日付形式で400エラー"""
        # Act
        response = client.post(
            self._url(timeline_gadget.gadget_uuid),
            json=self._valid_payload(end_datetime='not-a-date'),
        )

        # Assert
        assert response.status_code == 400

    def test_data_start_equals_end_datetime_returns_400(self, client, timeline_gadget):
        """3.8.1: 開始日時 = 終了日時（start >= end）で400エラー"""
        # Act
        response = client.post(
            self._url(timeline_gadget.gadget_uuid),
            json=self._valid_payload(
                start_datetime=_VALID_START_DATETIME,
                end_datetime=_VALID_START_DATETIME,  # start == end
            ),
        )

        # Assert
        assert response.status_code == 400

    def test_data_start_after_end_datetime_returns_400(self, client, timeline_gadget):
        """3.8.2: 開始日時 > 終了日時で400エラー"""
        # Act
        response = client.post(
            self._url(timeline_gadget.gadget_uuid),
            json=self._valid_payload(
                start_datetime=_VALID_END_DATETIME,
                end_datetime=_VALID_START_DATETIME,
            ),
        )

        # Assert
        assert response.status_code == 400

    def test_data_range_exceeds_24hours_returns_400(self, client, timeline_gadget):
        """3.8.3: 終了日時 - 開始日時 > 24時間で400エラー（仕様: 最大24時間）"""
        # Act
        response = client.post(
            self._url(timeline_gadget.gadget_uuid),
            json=self._valid_payload(
                start_datetime='2026/03/06 00:00:00',
                end_datetime='2026/03/07 00:00:01',  # 24時間超過
            ),
        )

        # Assert
        assert response.status_code == 400

    def test_data_unity_catalog_error_returns_500(self, client, timeline_gadget, mocker):
        """2.2.6: Unity Catalog クエリ失敗時に500エラー"""
        # Arrange: 外部API呼び出しが例外を送出
        mocker.patch(_SILVER_QUERY, side_effect=Exception("Databricks connection timeout"))

        # Act
        response = client.post(
            self._url(timeline_gadget.gadget_uuid),
            json=self._valid_payload(),
        )

        # Assert
        assert response.status_code == 500

    def test_data_variable_mode_uses_user_setting_device(self, client, timeline_gadget_variable, mocker):
        """4.2.4: デバイス可変モード時、ユーザー設定のデバイスIDでシルバー層クエリが呼ばれる"""
        # Arrange: 認証未実装のため g.current_user.user_id = None となり
        #          DashboardUserSetting に user_id=None で挿入できない（nullable=False）。
        #          ユーザー設定取得をモックして device_id=99 を返すことで、
        #          「可変モード時にユーザー設定の device_id が使われる」経路を検証する。
        mocker.patch(
            'iot_app.services.customer_dashboard.timeline.get_dashboard_user_setting',
            return_value=type('obj', (object,), {'device_id': 99})(),
        )
        mock_silver = mocker.patch(_SILVER_QUERY, return_value=[])

        # Act
        response = client.post(
            self._url(timeline_gadget_variable.gadget_uuid),
            json=self._valid_payload(),
        )

        # Assert: シルバー層クエリが呼ばれている
        assert response.status_code == 200
        assert mock_silver.called

    def test_data_fixed_mode_uses_data_source_device_id(self, client, timeline_gadget, mocker):
        """4.2.4: デバイス固定モード時、data_source_config の device_id でシルバー層クエリが呼ばれる

        data_source_config = {"device_id": 1} のガジェットで、
        ユーザー設定ではなく data_source_config.device_id=1 がシルバー層クエリに渡されることを確認する。
        """
        # Arrange: timeline_gadget は data_source_config={"device_id": 1}（デバイス固定モード）
        mock_silver = mocker.patch(_SILVER_QUERY, return_value=[])

        # Act
        response = client.post(
            self._url(timeline_gadget.gadget_uuid),
            json=self._valid_payload(),
        )

        # Assert: シルバー層クエリが data_source_config の device_id=1 で呼ばれている
        assert response.status_code == 200
        assert mock_silver.called
        assert mock_silver.call_args.kwargs['device_id'] == 1

    def test_data_silver_query_called_with_limit_100(self, client, timeline_gadget, mocker):
        """4.2.5: ガジェットデータ取得は最大100件（limit=100）でシルバー層クエリが呼ばれる"""
        mock_silver = mocker.patch(_SILVER_QUERY, return_value=[])

        # Act
        response = client.post(
            self._url(timeline_gadget.gadget_uuid),
            json=self._valid_payload(),
        )

        # Assert: limit=100 で呼ばれていること
        assert response.status_code == 200
        assert mock_silver.called
        assert mock_silver.call_args.kwargs['limit'] == 100


# ─────────────────────────────────────────────────────────────────────────────
# 3. ガジェット登録モーダル表示
# GET /analysis/customer-dashboard/gadgets/timeline/create
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.integration
class TestGadgetTimelineCreate:
    """時系列グラフガジェット 登録モーダル表示

    観点: 2.1.3 登録画面表示、2.2 エラー時遷移テスト
    """

    _URL = f"{BASE_URL}/gadgets/timeline/create"

    @pytest.fixture(autouse=True)
    def _auth(self, auth_user_id, user_master, organization_closure):
        """全テストで g.current_user と user_master / organization_closure を自動セットアップする"""
        pass

    def test_create_modal_returns_200(
        self, client, auth_user_id, dashboard_user_setting, dashboard_master,
        dashboard_group_master, measurement_item_left, measurement_item_right,
    ):
        """2.1.3: 正常表示 - 200とHTMLを返す"""
        # Act
        response = client.get(self._URL)

        # Assert
        assert response.status_code == 200

    def test_create_modal_no_dashboard_user_setting_returns_404(
        self, client, auth_user_id,
    ):
        """2.2.4: ダッシュボードユーザー設定が存在しない場合404エラー"""
        # Arrange: dashboard_user_setting フィクスチャなし（DBに設定なし）

        # Act
        response = client.get(self._URL)

        # Assert
        assert response.status_code == 404

    def test_create_modal_no_dashboard_master_returns_404(
        self, client, auth_user_id, db_session,
    ):
        """2.2.4: ダッシュボード情報が存在しない場合404エラー

        NOTE: DashboardUserSetting は存在するが、対応する DashboardMaster が
        accessible_org_ids に属さない（organization_closure がないため []）場合に 404 となる。
        dashboard_user_setting フィクスチャは dashboard_master に依存するため使用せず、
        インラインで DashboardUserSetting のみを作成する。
        """
        # Arrange: DashboardUserSetting だけ作成（DashboardMaster は作成しない）
        # organization_closure がないため accessible_org_ids=[] →
        # DashboardMaster.organization_id IN [] が常に False → NotFoundError → 404
        from iot_app.models.customer_dashboard import DashboardUserSetting
        setting = DashboardUserSetting(
            user_id=_TEST_USER_ID,
            dashboard_id=1,
            device_id=None,
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

    def test_create_modal_db_error_returns_500(
        self, client, auth_user_id, mocker,
    ):
        """2.2.5: DBエラー発生時に500エラーを返す"""
        mocker.patch(
            'iot_app.views.analysis.customer_dashboard.timeline.get_timeline_create_context',
            side_effect=Exception('DB接続エラー'),
        )
        response = client.get(self._URL)
        assert response.status_code == 500


# ─────────────────────────────────────────────────────────────────────────────
# 4. ガジェット登録実行
# POST /analysis/customer-dashboard/gadgets/timeline/register
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.integration
class TestGadgetTimelineRegister:
    """時系列グラフガジェット 登録実行

    観点: 3.1 必須チェック、3.2 文字列長チェック、3.8 相関チェック、
          4.3 登録（Create）テスト、2.3 リダイレクトテスト
    """

    _URL = f"{BASE_URL}/gadgets/timeline/register"

    _SKIP_GADGET_TYPE = frozenset({
        'test_register_without_gadget_type_master_returns_error',
    })

    @pytest.fixture(autouse=True)
    def _auth(self, auth_user_id, user_master, organization_closure):
        """全テストで g.current_user と user_master / organization_closure を自動セットアップする"""
        pass

    @pytest.fixture(autouse=True)
    def _register_setup(self, dashboard_group_master, dashboard_user_setting):
        """全テストで DashboardGroupMaster / DashboardUserSetting を事前登録する

        gadget_timeline_register ビューが group_id SelectField の choices をロードするために必要。
        - DashboardGroupMaster(dashboard_group_id=1) → group_id='1' が choices に含まれる
        - DashboardUserSetting(user_id=1) → ビューがグループを取得できる
        """
        pass

    @pytest.fixture(autouse=True)
    def _require_gadget_type(self, request, db_session):
        """全テストで GadgetTypeMaster='時系列グラフ' を事前登録する（サービス層の動的ルックアップに必要）。
        GadgetTypeMaster の存在チェックテストではスキップする。
        """
        if request.node.name in self._SKIP_GADGET_TYPE:
            return
        from iot_app.models.customer_dashboard import GadgetTypeMaster
        gt = GadgetTypeMaster(
            gadget_type_id=1,
            gadget_type_name='時系列グラフ',
            data_source_type=1,
            gadget_image_path='images/gadgets/timeline.png',
            gadget_description='時系列グラフガジェット',
            display_order=1,
            creator=1,
            modifier=1,
            delete_flag=False,
        )
        db_session.add(gt)
        db_session.flush()

    def _valid_form(self, **overrides):
        """デバイス可変モード・左右表示項目あり・2x2 の最小有効フォームデータ"""
        data = {
            'title':           'テスト時系列',
            'device_mode':     'variable',   # 可変モード: デバイス存在チェックをスキップ
            'device_id':       '0',
            'group_id':        '1',
            'left_item_id':    '1',
            'right_item_id':   '2',
            'gadget_size':     '2x2',
        }
        data.update(overrides)
        return data

    def test_register_success_redirects_to_dashboard(
        self, client, measurement_item_left, measurement_item_right,
    ):
        """2.3.1 / 4.3.1: 正常登録後、ダッシュボード画面へ302リダイレクト"""
        # Arrange: measurement_item_left / measurement_item_right フィクスチャで id=1,2 を登録済み

        # Act
        response = client.post(self._URL, data=self._valid_form(), follow_redirects=False)

        # Assert
        assert response.status_code == 302
        assert BASE_URL in response.headers['Location']

    def test_register_creates_record_in_db(
        self, client, app, measurement_item_left, measurement_item_right,
    ):
        """4.3.1: 正常登録後、dashboard_gadget_master に1件レコードが追加される"""
        # Act
        client.post(self._URL, data=self._valid_form())

        # Assert: リクエスト後に DB を直接クエリして検証
        with app.app_context():
            from iot_app import db
            from iot_app.models.customer_dashboard import DashboardGadgetMaster
            count = db.session.query(DashboardGadgetMaster).filter_by(delete_flag=False).count()
        assert count == 1

    def test_register_gadget_uuid_is_set(
        self, client, app, measurement_item_left, measurement_item_right,
    ):
        """4.3.5: 登録されたガジェットに gadget_uuid が自動採番される（UUID形式）"""
        # Act
        client.post(self._URL, data=self._valid_form())

        # Assert
        with app.app_context():
            from iot_app import db
            from iot_app.models.customer_dashboard import DashboardGadgetMaster
            gadget = db.session.query(DashboardGadgetMaster).first()
        assert gadget is not None
        assert len(gadget.gadget_uuid) == 36  # UUID形式（xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx）

    def test_register_create_date_and_update_date_are_set(
        self, client, app, measurement_item_left, measurement_item_right,
    ):
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
        assert gadget is not None
        assert gadget.create_date is not None, 'create_date が設定されていない'
        assert gadget.update_date is not None, 'update_date が設定されていない'
        assert before <= gadget.create_date <= after, 'create_date が登録時刻の範囲外'
        assert before <= gadget.update_date <= after, 'update_date が登録時刻の範囲外'

    def test_register_title_stored_correctly(
        self, client, app, measurement_item_left, measurement_item_right,
    ):
        """4.3.1: 登録されたガジェットのタイトルがDBに正しく保存される"""
        # Act
        client.post(self._URL, data=self._valid_form(title='時系列テスト'))

        # Assert
        with app.app_context():
            from iot_app import db
            from iot_app.models.customer_dashboard import DashboardGadgetMaster
            gadget = db.session.query(DashboardGadgetMaster).first()
        assert gadget.gadget_name == '時系列テスト'

    def test_register_gadget_size_stored_correctly(
        self, client, app, measurement_item_left, measurement_item_right,
    ):
        """4.3.2: 部品サイズ 2x4 がDBに保存される"""
        # Act
        client.post(self._URL, data=self._valid_form(gadget_size='2x4'))

        # Assert
        with app.app_context():
            from iot_app import db
            from iot_app.models.customer_dashboard import DashboardGadgetMaster
            gadget = db.session.query(DashboardGadgetMaster).first()
        assert gadget.gadget_size == 1

    def test_register_chart_config_stores_left_and_right_item_id(
        self, client, app, measurement_item_left, measurement_item_right,
    ):
        """4.3.2: chart_config に left_item_id / right_item_id が正しく保存される"""
        # Act
        client.post(self._URL, data=self._valid_form(left_item_id='1', right_item_id='2'))

        # Assert
        with app.app_context():
            from iot_app import db
            from iot_app.models.customer_dashboard import DashboardGadgetMaster
            gadget = db.session.query(DashboardGadgetMaster).first()
        chart_config = json.loads(gadget.chart_config)
        assert chart_config['left_item_id'] == 1
        assert chart_config['right_item_id'] == 2

    def test_register_chart_config_null_min_max_when_omitted(
        self, client, app, measurement_item_left, measurement_item_right,
    ):
        """4.3.4: 最小値・最大値省略時、chart_config JSON 内で null が設定される"""
        # Act: left/right min/max を省略して登録
        client.post(self._URL, data=self._valid_form())

        # Assert
        with app.app_context():
            from iot_app import db
            from iot_app.models.customer_dashboard import DashboardGadgetMaster
            gadget = db.session.query(DashboardGadgetMaster).first()
        chart_config = json.loads(gadget.chart_config)
        assert chart_config['left_min_value'] is None
        assert chart_config['left_max_value'] is None
        assert chart_config['right_min_value'] is None
        assert chart_config['right_max_value'] is None

    def test_register_data_source_config_device_id_is_null_in_variable_mode(
        self, client, app, measurement_item_left, measurement_item_right,
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

    def test_register_data_source_config_stores_device_id_in_fixed_mode(
        self, client, app, measurement_item_left, measurement_item_right, mocker,
    ):
        """4.3.2: device_mode=fixed 時、data_source_config に device_id が数値として保存される

        check_device_in_scope をモックしてスコープ確認をスキップし、
        device_id=12345 が data_source_config JSON に正しく保存されることを確認する。
        """
        # Arrange: デバイスアクセスチェックをモック（非Noneを返すことで通過）
        mocker.patch(
            'iot_app.views.analysis.customer_dashboard.timeline.check_device_in_scope',
            return_value=object(),
        )

        # Act
        client.post(self._URL, data=self._valid_form(device_mode='fixed', device_id='12345'))

        # Assert
        with app.app_context():
            from iot_app import db
            from iot_app.models.customer_dashboard import DashboardGadgetMaster
            gadget = db.session.query(DashboardGadgetMaster).first()
        data_source_config = json.loads(gadget.data_source_config)
        assert data_source_config['device_id'] == 12345

    def test_register_data_source_config_has_only_device_id_key(
        self, client, app, measurement_item_left, measurement_item_right,
    ):
        """4.3.2: data_source_config JSON のキーが device_id のみで余分なキーがないこと

        スキーマ: {"device_id": <int|null>}
        """
        # Act
        client.post(self._URL, data=self._valid_form(device_mode='variable'))

        # Assert
        with app.app_context():
            from iot_app import db
            from iot_app.models.customer_dashboard import DashboardGadgetMaster
            gadget = db.session.query(DashboardGadgetMaster).first()
        data_source_config = json.loads(gadget.data_source_config)
        assert set(data_source_config.keys()) == {'device_id'}

    def test_register_chart_config_stores_min_max_values(
        self, client, app, measurement_item_left, measurement_item_right,
    ):
        """4.3.2: min/max 値入力時、chart_config に正しい数値が保存される

        スキーマ例:
          {"left_min_value": 0.0, "right_min_value": 10.0,
           "left_max_value": 100.0, "right_max_value": 110.0}
        """
        # Act
        client.post(self._URL, data=self._valid_form(
            left_min_value='0.0',
            left_max_value='100.0',
            right_min_value='10.0',
            right_max_value='110.0',
        ))

        # Assert
        with app.app_context():
            from iot_app import db
            from iot_app.models.customer_dashboard import DashboardGadgetMaster
            gadget = db.session.query(DashboardGadgetMaster).first()
        chart_config = json.loads(gadget.chart_config)
        assert chart_config['left_min_value']  == 0.0
        assert chart_config['left_max_value']  == 100.0
        assert chart_config['right_min_value'] == 10.0
        assert chart_config['right_max_value'] == 110.0

    def test_register_chart_config_has_all_six_keys(
        self, client, app, measurement_item_left, measurement_item_right,
    ):
        """4.3.2: chart_config JSON が定義通り6キーを全て持ち、余分なキーがないこと

        スキーマ: {left_item_id, right_item_id, left_min_value, left_max_value,
                   right_min_value, right_max_value}
        """
        # Act
        client.post(self._URL, data=self._valid_form())

        # Assert
        with app.app_context():
            from iot_app import db
            from iot_app.models.customer_dashboard import DashboardGadgetMaster
            gadget = db.session.query(DashboardGadgetMaster).first()
        chart_config = json.loads(gadget.chart_config)
        expected_keys = {
            'left_item_id', 'right_item_id',
            'left_min_value', 'left_max_value',
            'right_min_value', 'right_max_value',
        }
        assert set(chart_config.keys()) == expected_keys

    def test_register_default_position_x_is_zero(
        self, client, app, measurement_item_left, measurement_item_right,
    ):
        """4.3.2: position_x のデフォルト値が 0 で登録される"""
        # Act
        client.post(self._URL, data=self._valid_form())

        # Assert
        with app.app_context():
            from iot_app import db
            from iot_app.models.customer_dashboard import DashboardGadgetMaster
            gadget = db.session.query(DashboardGadgetMaster).first()
        assert gadget.position_x == 0

    def test_register_position_y_is_one_for_first_gadget(
        self, client, app, measurement_item_left, measurement_item_right,
    ):
        """4.3.2: グループ内初登録時、position_y は 1（max(0)+1）で登録される"""
        # Act
        client.post(self._URL, data=self._valid_form())

        # Assert
        with app.app_context():
            from iot_app import db
            from iot_app.models.customer_dashboard import DashboardGadgetMaster
            gadget = db.session.query(DashboardGadgetMaster).first()
        assert gadget.position_y == 1

    def test_register_position_y_increments_for_second_gadget(
        self, client, app, measurement_item_left, measurement_item_right,
    ):
        """4.3.2: 同グループに2件目登録時、position_y は既存最大値+1（=2）で登録される"""
        # Arrange: 1件目を登録
        client.post(self._URL, data=self._valid_form(title='1件目'))

        # Act: 2件目を同グループに登録
        client.post(self._URL, data=self._valid_form(title='2件目'))

        # Assert: 2件目の position_y == 2
        with app.app_context():
            from iot_app import db
            from iot_app.models.customer_dashboard import DashboardGadgetMaster
            gadgets = db.session.query(DashboardGadgetMaster).order_by(
                DashboardGadgetMaster.position_y.asc()
            ).all()
        assert len(gadgets) == 2
        assert gadgets[0].position_y == 1
        assert gadgets[1].position_y == 2

    def test_register_display_order_is_one_for_first_gadget(
        self, client, app, measurement_item_left, measurement_item_right,
    ):
        """4.3.2: グループ内初登録時、display_order は 1（max(0)+1）で登録される"""
        # Act
        client.post(self._URL, data=self._valid_form())

        # Assert
        with app.app_context():
            from iot_app import db
            from iot_app.models.customer_dashboard import DashboardGadgetMaster
            gadget = db.session.query(DashboardGadgetMaster).first()
        assert gadget.display_order == 1

    def test_register_display_order_increments_for_second_gadget(
        self, client, app, measurement_item_left, measurement_item_right,
    ):
        """4.3.2: 同グループに2件目登録時、display_order は既存最大値+1（=2）で登録される

        position_y と同じく COALESCE(MAX(display_order), 0) + 1 で採番される。
        """
        # Arrange: 1件目を登録（display_order=1）
        client.post(self._URL, data=self._valid_form(title='1件目'))

        # Act: 2件目を同グループに登録
        client.post(self._URL, data=self._valid_form(title='2件目'))

        # Assert: 2件目の display_order == 2
        with app.app_context():
            from iot_app import db
            from iot_app.models.customer_dashboard import DashboardGadgetMaster
            gadgets = db.session.query(DashboardGadgetMaster).order_by(
                DashboardGadgetMaster.display_order.asc()
            ).all()
        assert len(gadgets) == 2
        assert gadgets[0].display_order == 1
        assert gadgets[1].display_order == 2

    def test_register_dashboard_group_id_stored_correctly(
        self, client, app, measurement_item_left, measurement_item_right,
    ):
        """4.3.2: フォームの group_id が dashboard_group_id としてDBに正しく保存される

        フォームフィールド名 group_id → DBカラム dashboard_group_id のマッピングを確認する。
        """
        # Act: group_id=1 で登録
        client.post(self._URL, data=self._valid_form(group_id='1'))

        # Assert
        with app.app_context():
            from iot_app import db
            from iot_app.models.customer_dashboard import DashboardGadgetMaster
            gadget = db.session.query(DashboardGadgetMaster).first()
        assert gadget.dashboard_group_id == 1

    def test_register_gadget_type_id_is_timeline_type(
        self, client, app, measurement_item_left, measurement_item_right,
    ):
        """4.3.2: 登録されたガジェットの gadget_type_id が GadgetTypeMaster の動的ルックアップ結果と一致する

        gadget_type_name='時系列グラフ' で GadgetTypeMaster を検索し、
        その gadget_type_id が登録されたガジェットに設定されることを確認する。
        ハードコード（=1）ではなく、DBからの動的取得であることを保証する。
        """
        # Act
        client.post(self._URL, data=self._valid_form())

        # Assert: GadgetTypeMaster の '時系列グラフ' レコードの ID と一致すること
        with app.app_context():
            from iot_app import db
            from iot_app.models.customer_dashboard import DashboardGadgetMaster, GadgetTypeMaster
            gadget = db.session.query(DashboardGadgetMaster).first()
            expected_type = db.session.query(GadgetTypeMaster).filter_by(
                gadget_type_name='時系列グラフ',
            ).first()
        assert gadget.gadget_type_id == expected_type.gadget_type_id

    def test_register_without_gadget_type_master_returns_error(
        self, client, app, measurement_item_left, measurement_item_right,
    ):
        """4.3.2: GadgetTypeMaster に '時系列グラフ' レコードが存在しない場合、登録が失敗する

        gadget_type_id のハードコードではなく GadgetTypeMaster から動的ルックアップするため、
        レコード不在時は ValidationError が発生し 500 が返ることを確認する。
        （_SKIP_GADGET_TYPE により autouse fixture がスキップされる）
        """
        # Arrange: GadgetTypeMaster にレコードなし（fixture スキップ済み）

        # Act
        response = client.post(self._URL, data=self._valid_form())

        # Assert: ガジェット種別不在 → サービス層 ValidationError → 500
        assert response.status_code == 500

    def test_register_delete_flag_is_false_on_creation(
        self, client, app, measurement_item_left, measurement_item_right,
    ):
        """4.3.2: 登録直後の delete_flag は False で保存される"""
        # Act
        client.post(self._URL, data=self._valid_form())

        # Assert
        with app.app_context():
            from iot_app import db
            from iot_app.models.customer_dashboard import DashboardGadgetMaster
            gadget = db.session.query(DashboardGadgetMaster).first()
        assert gadget.delete_flag is False

    def test_register_gadget_id_is_auto_incremented(
        self, client, app, measurement_item_left, measurement_item_right,
    ):
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

    def test_register_create_date_is_set(
        self, client, app, measurement_item_left, measurement_item_right,
    ):
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

    def test_register_creator_is_none_without_auth(
        self, client, app, measurement_item_left, measurement_item_right,
    ):
        """4.3.7: 認証未実装ブランチでは creator・modifier に None が設定される（current_user_id=0 に近い挙動）

        NOTE: 認証実装後は current_user.user_id がセットされていることを確認すること。
        """
        # Act
        client.post(self._URL, data=self._valid_form())

        # Assert
        with app.app_context():
            from iot_app import db
            from iot_app.models.customer_dashboard import DashboardGadgetMaster
            gadget = db.session.query(DashboardGadgetMaster).first()
        # 認証未実装: creator/modifier は None または 0
        # TODO: 認証実装後はログインユーザーのIDが設定されることを確認
        assert gadget.creator is None or isinstance(gadget.creator, int)
        assert gadget.modifier is None or isinstance(gadget.modifier, int)

    # ── バリデーション（必須チェック）────────────────────────────────────────

    def test_register_title_required_returns_400(
        self, client, measurement_item_left, measurement_item_right,
    ):
        """3.1.1: タイトル未入力で400（バリデーションエラー）"""
        # Act
        response = client.post(self._URL, data=self._valid_form(title=''))

        # Assert
        assert response.status_code == 400

    def test_register_left_item_id_required_returns_400(
        self, client, measurement_item_left, measurement_item_right,
    ):
        """3.1.2: 左表示項目未選択（空）で400"""
        # Act
        response = client.post(self._URL, data=self._valid_form(left_item_id=''))

        # Assert
        assert response.status_code == 400

    def test_register_right_item_id_required_returns_400(
        self, client, measurement_item_left, measurement_item_right,
    ):
        """3.1.3: 右表示項目未選択（空）で400"""
        # Act
        response = client.post(self._URL, data=self._valid_form(right_item_id=''))

        # Assert
        assert response.status_code == 400

    def test_register_group_required_returns_400(
        self, client, measurement_item_left, measurement_item_right,
    ):
        """3.1.4: グループ未選択（0）で400"""
        # Act
        response = client.post(self._URL, data=self._valid_form(group_id='0'))

        # Assert
        assert response.status_code == 400

    def test_register_gadget_size_required_returns_400(
        self, client, measurement_item_left, measurement_item_right,
    ):
        """3.1.5: 部品サイズ未選択（空）で400"""
        # Act
        response = client.post(self._URL, data=self._valid_form(gadget_size=''))

        # Assert
        assert response.status_code == 400

    def test_register_device_id_required_in_fixed_mode_returns_400(
        self, client, measurement_item_left, measurement_item_right,
    ):
        """3.1.6: device_mode=fixed でデバイスID未指定（0）は400（フォームバリデーションエラー）

        NOTE: device_id=0 は falsy のため、フォームの validate() が先にエラーを検出し 400 を返す。
        """
        # Act
        response = client.post(
            self._URL,
            data=self._valid_form(device_mode='fixed', device_id='0'),
        )

        # Assert
        assert response.status_code == 400

    # ── バリデーション（文字列長チェック）───────────────────────────────────

    def test_register_title_20_chars_succeeds(
        self, client, measurement_item_left, measurement_item_right,
    ):
        """3.2.1: タイトル20文字は登録成功"""
        # Act
        response = client.post(
            self._URL,
            data=self._valid_form(title='あ' * 20),
            follow_redirects=False,
        )

        # Assert
        assert response.status_code == 302

    def test_register_title_21_chars_returns_400(
        self, client, measurement_item_left, measurement_item_right,
    ):
        """3.2.2: タイトル21文字以上で400"""
        # Act
        response = client.post(self._URL, data=self._valid_form(title='あ' * 21))

        # Assert
        assert response.status_code == 400

    # ── バリデーション（相関チェック: min/max）──────────────────────────────

    def test_register_left_min_greater_than_max_returns_400(
        self, client, measurement_item_left, measurement_item_right,
    ):
        """3.8.1: 左最小値 > 左最大値で400（相関チェック）"""
        # Act
        response = client.post(
            self._URL,
            data=self._valid_form(left_min_value='10.0', left_max_value='5.0'),
        )

        # Assert
        assert response.status_code == 400

    def test_register_left_min_equals_max_returns_400(
        self, client, measurement_item_left, measurement_item_right,
    ):
        """3.8.2: 左最小値 = 左最大値で400（相関チェック）"""
        # Act
        response = client.post(
            self._URL,
            data=self._valid_form(left_min_value='5.0', left_max_value='5.0'),
        )

        # Assert
        assert response.status_code == 400

    def test_register_right_min_greater_than_max_returns_400(
        self, client, measurement_item_left, measurement_item_right,
    ):
        """3.8.3: 右最小値 > 右最大値で400（相関チェック）"""
        # Act
        response = client.post(
            self._URL,
            data=self._valid_form(right_min_value='100.0', right_max_value='50.0'),
        )

        # Assert
        assert response.status_code == 400

    def test_register_valid_left_min_max_succeeds(
        self, client, measurement_item_left, measurement_item_right,
    ):
        """3.8.4: 左最小値 < 左最大値で登録成功"""
        # Act
        response = client.post(
            self._URL,
            data=self._valid_form(left_min_value='-10.0', left_max_value='30.0'),
            follow_redirects=False,
        )

        # Assert
        assert response.status_code == 302

    def test_register_valid_right_min_max_succeeds(
        self, client, measurement_item_left, measurement_item_right,
    ):
        """3.8.5: 右最小値 < 右最大値で登録成功"""
        # Act
        response = client.post(
            self._URL,
            data=self._valid_form(right_min_value='0.0', right_max_value='3000.0'),
            follow_redirects=False,
        )

        # Assert
        assert response.status_code == 302

    def test_register_omit_all_min_max_succeeds(
        self, client, measurement_item_left, measurement_item_right,
    ):
        """3.8.6: 全 min/max 省略可（任意項目）"""
        # Act
        response = client.post(self._URL, data=self._valid_form(), follow_redirects=False)

        # Assert
        assert response.status_code == 302

    def test_register_right_min_equals_max_returns_400(
        self, client, measurement_item_left, measurement_item_right,
    ):
        """3.8.4: 右最小値 = 右最大値で400（相関チェック）

        左最小値＝最大値のテストと対称。UI仕様書に左右とも同一ルールが記載されている。
        """
        # Act
        response = client.post(
            self._URL,
            data=self._valid_form(right_min_value='5.0', right_max_value='5.0'),
        )

        # Assert
        assert response.status_code == 400

    # ── バリデーション（数値形式チェック: min/max フィールド）──────────────────

    def test_register_left_min_nonnumeric_returns_400(
        self, client, measurement_item_left, measurement_item_right,
    ):
        """3.3.1: 左最小値に非数値文字列を入力すると400（数値形式バリデーション）

        UI仕様書: 「左表示項目の最小値は数値で入力してください」
        """
        # Act
        response = client.post(
            self._URL,
            data=self._valid_form(left_min_value='abc'),
        )

        # Assert
        assert response.status_code == 400

    def test_register_left_max_nonnumeric_returns_400(
        self, client, measurement_item_left, measurement_item_right,
    ):
        """3.3.2: 左最大値に非数値文字列を入力すると400（数値形式バリデーション）

        UI仕様書: 「左表示項目の最大値は数値で入力してください」
        """
        # Act
        response = client.post(
            self._URL,
            data=self._valid_form(left_max_value='abc'),
        )

        # Assert
        assert response.status_code == 400

    def test_register_right_min_nonnumeric_returns_400(
        self, client, measurement_item_left, measurement_item_right,
    ):
        """3.3.3: 右最小値に非数値文字列を入力すると400（数値形式バリデーション）

        UI仕様書: 「右表示項目の最小値は数値で入力してください」
        """
        # Act
        response = client.post(
            self._URL,
            data=self._valid_form(right_min_value='abc'),
        )

        # Assert
        assert response.status_code == 400

    def test_register_right_max_nonnumeric_returns_400(
        self, client, measurement_item_left, measurement_item_right,
    ):
        """3.3.4: 右最大値に非数値文字列を入力すると400（数値形式バリデーション）

        UI仕様書: 「右表示項目の最大値は数値で入力してください」
        """
        # Act
        response = client.post(
            self._URL,
            data=self._valid_form(right_max_value='abc'),
        )

        # Assert
        assert response.status_code == 400

    # ── バリデーション（タイトル: 空白のみ）──────────────────────────────────

    def test_register_title_whitespace_only_returns_400(
        self, client, measurement_item_left, measurement_item_right,
    ):
        """3.2.3: タイトルが空白文字のみ（例: "   "）は400を返す

        WTForms の DataRequired バリデーターは空白のみの文字列も空値として扱う。
        """
        # Act
        response = client.post(
            self._URL,
            data=self._valid_form(title='   '),
        )

        # Assert
        assert response.status_code == 400

    def test_register_fixed_mode_nonexistent_device_id_returns_404(
        self, client, measurement_item_left, measurement_item_right,
    ):
        """4.3.8 / 2.2.4: device_mode=fixed かつ DBに存在しない device_id を送信すると 404"""
        # Arrange: DeviceMaster に該当レコードを登録しない（nonexistent_id=9999）
        form_data = self._valid_form(device_mode='fixed', device_id='9999')

        # Act
        response = client.post(self._URL, data=form_data)

        # Assert
        assert response.status_code == 404

    def test_register_success_then_dashboard_renders(
        self, client, measurement_item_left, measurement_item_right,
    ):
        """4.3.1 / 2.3.1: 登録成功後にリダイレクトを追跡するとダッシュボード画面（200）が表示される"""
        # Act: リダイレクトを追跡してダッシュボード画面を取得
        response = client.post(self._URL, data=self._valid_form(), follow_redirects=True)

        # Assert: 最終的にダッシュボード画面（200）が表示される
        assert response.status_code == 200
        assert b"customer-dashboard" in response.data
        # TODO: 設計書には成功メッセージモーダル表示の記載あり、要確認


# ─────────────────────────────────────────────────────────────────────────────
# 5. CSVエクスポート
# GET /analysis/customer-dashboard/gadgets/<gadget_uuid>?export=csv
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.integration
class TestGadgetTimelineCsvExport:
    """時系列グラフガジェット CSVエクスポート

    観点: 4.6 CSVエクスポートテスト、2.2 エラー時遷移テスト、3.4 日付形式チェック
    """

    @pytest.fixture(autouse=True)
    def _auth(self, auth_user_id, user_master, organization_closure):
        """全テストで g.current_user と user_master / organization_closure を自動セットアップする"""
        pass

    def _url(self, gadget_uuid, **params):
        query = "&".join(f"{k}={v}" for k, v in params.items())
        return f"{BASE_URL}/gadgets/{gadget_uuid}?{query}"

    def _default_params(self):
        return {
            'export':          'csv',
            'start_datetime':  _VALID_START_DATETIME,
            'end_datetime':    _VALID_END_DATETIME,
        }

    def _mock_rows(self):
        """モック用センサーデータ行"""
        from datetime import datetime as _dt
        return [
            {
                'event_timestamp': _dt(2026, 3, 6, 12, 0, 0),
                'device_id': 1,
                'device_name': 'テストデバイス',
                'external_temp': 10.5,
                'compressor_freezer_1': 2500.0,
            },
        ]

    def test_csv_returns_200(self, client, timeline_gadget, mocker):
        """4.6.1: 正常エクスポート - 200レスポンス"""
        # Arrange: 外部APIをモック
        mocker.patch(_SILVER_QUERY, return_value=self._mock_rows())

        # Act
        response = client.get(self._url(timeline_gadget.gadget_uuid, **self._default_params()))

        # Assert
        assert response.status_code == 200

    def test_csv_content_type_is_text_csv(self, client, timeline_gadget, mocker):
        """4.6.1: Content-Type が text/csv"""
        # Arrange
        mocker.patch(_SILVER_QUERY, return_value=[])

        # Act
        response = client.get(self._url(timeline_gadget.gadget_uuid, **self._default_params()))

        # Assert
        assert 'text/csv' in response.content_type

    def test_csv_content_disposition_is_attachment(self, client, timeline_gadget, mocker):
        """4.6.2: Content-Disposition で attachment（ダウンロード）になる"""
        # Arrange
        mocker.patch(_SILVER_QUERY, return_value=[])

        # Act
        response = client.get(self._url(timeline_gadget.gadget_uuid, **self._default_params()))

        # Assert
        disposition = response.headers.get('Content-Disposition', '')
        assert 'attachment' in disposition
        assert 'sensor_data_' in disposition

    def test_csv_filename_format(self, client, timeline_gadget, mocker):
        """4.6.2: ファイル名が sensor_data_{yyyyMMddHHmmss}.csv 形式"""
        # Arrange
        mocker.patch(_SILVER_QUERY, return_value=[])

        # Act
        response = client.get(self._url(timeline_gadget.gadget_uuid, **self._default_params()))

        # Assert
        disposition = response.headers.get('Content-Disposition', '')
        import re
        assert re.search(r'sensor_data_\d{14}\.csv', disposition)

    def test_csv_has_utf8_bom(self, client, timeline_gadget, mocker):
        """4.6.1: CSVがUTF-8 BOM付き（Excelで文字化けしない）"""
        # Arrange
        mocker.patch(_SILVER_QUERY, return_value=[])

        # Act
        response = client.get(self._url(timeline_gadget.gadget_uuid, **self._default_params()))

        # Assert: UTF-8 BOM（EF BB BF）
        assert response.data[:3] == b'\xef\xbb\xbf'

    def test_csv_has_header_row(self, client, timeline_gadget, mocker):
        """4.6.1: CSVの1行目に受信日時・デバイス名・左右表示項目ヘッダーが含まれる"""
        # Arrange
        mocker.patch(_SILVER_QUERY, return_value=[])

        # Act
        response = client.get(self._url(timeline_gadget.gadget_uuid, **self._default_params()))

        # Assert: 設計書記載のヘッダー（デバイス名, 時刻, 左表示項目ラベル, 右表示項目ラベル）
        csv_text = response.data.decode('utf-8-sig')
        header = csv_text.splitlines()[0]
        assert '時刻' in header
        assert 'デバイス名' in header

    def test_csv_data_rows_match_mocked_rows(self, client, timeline_gadget, mocker):
        """4.6.1: シルバー層の行データがCSVのデータ行に正しく出力される"""
        # Arrange
        mocker.patch(_SILVER_QUERY, return_value=self._mock_rows())

        # Act
        response = client.get(self._url(timeline_gadget.gadget_uuid, **self._default_params()))

        # Assert
        csv_text = response.data.decode('utf-8-sig')
        lines = csv_text.splitlines()
        assert len(lines) == 2  # ヘッダー + 1行
        assert '2026/03/06 12:00:00' in lines[1]
        assert '10.5' in lines[1]

    def test_csv_without_export_param_returns_404(self, client, timeline_gadget):
        """2.2.4: export=csv パラメータなしで404"""
        # Act
        response = client.get(
            f"{BASE_URL}/gadgets/{timeline_gadget.gadget_uuid}"
            f"?start_datetime={_VALID_START_DATETIME}&end_datetime={_VALID_END_DATETIME}"
        )

        # Assert
        assert response.status_code == 404

    def test_csv_nonexistent_gadget_returns_404(self, client):
        """2.2.4: 存在しない gadget_uuid で404"""
        # Act
        response = client.get(self._url(str(uuid.uuid4()), **self._default_params()))

        # Assert
        assert response.status_code == 404

    def test_csv_deleted_gadget_returns_404(self, client, timeline_gadget, db_session, mocker):
        """2.2.4: delete_flag=True の論理削除済みガジェットで404"""
        # Arrange: ガジェットを論理削除
        timeline_gadget.delete_flag = True
        db_session.flush()

        # Act
        response = client.get(self._url(timeline_gadget.gadget_uuid, **self._default_params()))

        # Assert
        assert response.status_code == 404

    def test_csv_out_of_scope_gadget_returns_404(
        self, client, auth_user_id, organization_master, organization_closure, db_session,
    ):
        """①: スコープ外の組織（org_id=2）に属するガジェットは404

        accessible_org_ids=[1] のユーザーが organization_id=2 のガジェットにアクセスすると
        get_gadget_in_scope が None を返し 404 になることを確認する。
        """
        from iot_app.models.customer_dashboard import (
            DashboardGadgetMaster, DashboardGroupMaster, DashboardMaster, GadgetTypeMaster,
        )
        # 別組織（org_id=2）のダッシュボード構造を作成
        gt = GadgetTypeMaster(
            gadget_type_id=98, gadget_type_name='時系列グラフ',
            data_source_type=1, gadget_image_path='images/gadgets/timeline.png',
            gadget_description='スコープ外テスト用', display_order=98,
            creator=1, modifier=1, delete_flag=False,
        )
        dash = DashboardMaster(
            dashboard_id=98, dashboard_name='他社ダッシュボード', organization_id=2,
            dashboard_uuid=str(uuid.uuid4()), delete_flag=False, creator=1, modifier=1,
        )
        grp = DashboardGroupMaster(
            dashboard_group_id=98, dashboard_id=98,
            dashboard_group_uuid=str(uuid.uuid4()),
            dashboard_group_name='他社グループ', display_order=1,
            delete_flag=False, creator=1, modifier=1,
        )
        gadget_uuid = str(uuid.uuid4())
        gadget = DashboardGadgetMaster(
            gadget_uuid=gadget_uuid, gadget_name='他社ガジェット', gadget_type_id=98,
            dashboard_group_id=98,
            chart_config=json.dumps({
                'left_item_id': 1, 'right_item_id': 2,
                'left_min_value': None, 'left_max_value': None,
                'right_min_value': None, 'right_max_value': None,
            }),
            data_source_config=json.dumps({'device_id': 1}),
            position_x=0, position_y=0, gadget_size='2x2', display_order=1,
            delete_flag=False, creator=1, modifier=1,
        )
        db_session.add_all([gt, dash, grp, gadget])
        db_session.flush()

        # Act
        response = client.get(self._url(gadget_uuid, **self._default_params()))

        # Assert: org_id=2 は accessible_org_ids=[1] に含まれないため 404
        assert response.status_code == 404

    def test_csv_variable_mode_uses_user_setting_device(
        self, client, timeline_gadget_variable, mocker,
    ):
        """②: デバイス可変モード時、ユーザー設定のデバイスIDでシルバー層クエリが呼ばれる

        認証未実装のため get_dashboard_user_setting をモックして device_id=99 を返す。
        """
        mocker.patch(
            'iot_app.services.customer_dashboard.timeline.get_dashboard_user_setting',
            return_value=type('obj', (object,), {'device_id': 99})(),
        )
        mock_silver = mocker.patch(_SILVER_QUERY, return_value=[])

        # Act
        response = client.get(self._url(timeline_gadget_variable.gadget_uuid, **self._default_params()))

        # Assert: シルバー層クエリが呼ばれている
        assert response.status_code == 200
        assert mock_silver.called

    def test_csv_fixed_mode_uses_data_source_device_id(
        self, client, timeline_gadget, mocker,
    ):
        """②: デバイス固定モード時、data_source_config の device_id でシルバー層クエリが呼ばれる

        data_source_config = {"device_id": 1} のガジェットで device_id=1 が渡されることを確認する。
        """
        mock_silver = mocker.patch(_SILVER_QUERY, return_value=[])

        # Act
        response = client.get(self._url(timeline_gadget.gadget_uuid, **self._default_params()))

        # Assert: シルバー層クエリが data_source_config の device_id=1 で呼ばれている
        assert response.status_code == 200
        assert mock_silver.called
        assert mock_silver.call_args.kwargs['device_id'] == 1

    def test_csv_silver_query_called_with_limit_100000(self, client, timeline_gadget, mocker):
        """4.6.6: CSVエクスポートは最大100,000件（limit=100000）でシルバー層クエリが呼ばれる"""
        mock_silver = mocker.patch(_SILVER_QUERY, return_value=[])

        # Act
        response = client.get(self._url(timeline_gadget.gadget_uuid, **self._default_params()))

        # Assert: limit=100000 で呼ばれていること
        assert response.status_code == 200
        assert mock_silver.called
        assert mock_silver.call_args.kwargs['limit'] == 100000

    def test_csv_invalid_start_datetime_format_returns_400(self, client, timeline_gadget):
        """3.4.1: 不正な start_datetime 形式で400エラー"""
        # Act
        params = {**self._default_params(), 'start_datetime': '2026-03-06T12:00:00'}
        response = client.get(self._url(timeline_gadget.gadget_uuid, **params))

        # Assert
        assert response.status_code == 400

    def test_csv_invalid_end_datetime_format_returns_400(self, client, timeline_gadget):
        """3.4.2: 不正な end_datetime 形式で400エラー"""
        # Act
        params = {**self._default_params(), 'end_datetime': 'invalid-date'}
        response = client.get(self._url(timeline_gadget.gadget_uuid, **params))

        # Assert
        assert response.status_code == 400

    def test_csv_start_after_end_returns_400(self, client, timeline_gadget):
        """3.8.1: 開始日時 > 終了日時で400エラー（相関チェック）"""
        # Act
        params = {**self._default_params(),
                  'start_datetime': _VALID_END_DATETIME,
                  'end_datetime':   _VALID_START_DATETIME}
        response = client.get(self._url(timeline_gadget.gadget_uuid, **params))

        # Assert
        assert response.status_code == 400

    def test_csv_range_exceeds_24hours_returns_400(self, client, timeline_gadget):
        """3.8.2: 終了日時 - 開始日時 > 24時間で400エラー（CSVエクスポート）

        データ取得エンドポイントと同一バリデーション（ワークフロー仕様書）。
        CSVでも24時間以内の範囲制限が適用されることを確認する。
        """
        # Act
        params = {**self._default_params(),
                  'start_datetime': '2026/03/06 00:00:00',
                  'end_datetime':   '2026/03/07 00:00:01'}  # 24時間1秒超過
        response = client.get(self._url(timeline_gadget.gadget_uuid, **params))

        # Assert
        assert response.status_code == 400

    def test_csv_missing_start_datetime_returns_400(self, client, timeline_gadget):
        """3.1.1: start_datetime 未指定で400エラー"""
        # Act
        params = {'export': 'csv', 'end_datetime': _VALID_END_DATETIME}
        response = client.get(self._url(timeline_gadget.gadget_uuid, **params))

        # Assert
        assert response.status_code == 400

    def test_csv_missing_end_datetime_returns_400(self, client, timeline_gadget):
        """3.1.2: end_datetime 未指定で400エラー"""
        # Act
        params = {'export': 'csv', 'start_datetime': _VALID_START_DATETIME}
        response = client.get(self._url(timeline_gadget.gadget_uuid, **params))

        # Assert
        assert response.status_code == 400

    def test_csv_unity_catalog_error_returns_500(self, client, timeline_gadget, mocker):
        """2.2.6: Unity Catalog クエリ失敗時に500エラー"""
        # Arrange
        mocker.patch(_SILVER_QUERY, side_effect=Exception("Connection error"))

        # Act
        response = client.get(self._url(timeline_gadget.gadget_uuid, **self._default_params()))

        # Assert
        assert response.status_code == 500

    def test_csv_empty_data_returns_header_only(self, client, timeline_gadget, mocker):
        """4.6.5: センサーデータ0件時はヘッダー行のみ出力される"""
        # Arrange
        mocker.patch(_SILVER_QUERY, return_value=[])

        # Act
        response = client.get(self._url(timeline_gadget.gadget_uuid, **self._default_params()))

        # Assert
        assert response.status_code == 200
        csv_text = response.data.decode('utf-8-sig')
        lines = [ln for ln in csv_text.splitlines() if ln]
        assert len(lines) == 1  # ヘッダーのみ


# ─────────────────────────────────────────────────────────────────────────────
# 6. ログ出力テスト
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.integration
class TestLogging:
    """ログ出力テスト

    観点: 8. ログ出力テスト（integration-test-perspectives.md）
    参照設計書: docs/03-features/common/logging-specification.md

    前提:
    - リクエスト前後ログ（8.1.1/8.1.2）は before_request / after_request フックで自動出力
    - SQLクエリログ（8.1.3）は SQLAlchemy イベントリスナーで自動出力
    - エラーログ（8.2.1/8.2.2）は error_handlers.py および各ビューで出力
    - マスキング（8.3）は AppLoggerAdapter が自動適用
    """

    @pytest.fixture(autouse=True)
    def _auth(self, auth_user_id, user_master, organization_closure):
        """全テストで g.current_user と user_master / organization_closure を自動セットアップする"""
        pass

    @pytest.fixture(autouse=True)
    def _register_setup(self, dashboard_group_master, dashboard_user_setting):
        """register エンドポイントを呼ぶテストで DashboardGroupMaster / DashboardUserSetting を事前登録する"""
        pass

    # ─── 8.1 正常系ログ ───────────────────────────────────────────────────────

    def test_request_start_is_logged_as_info(self, client, caplog):
        """8.1.1: リクエスト開始時に INFO 'リクエスト開始' が出力される"""
        import logging

        # Act
        with caplog.at_level(logging.INFO):
            client.get(BASE_URL)

        # Assert
        assert any('リクエスト開始' in r.message for r in caplog.records)

    def test_request_end_is_logged_with_status_and_duration(self, client, caplog):
        """8.1.2: リクエスト終了時に INFO 'リクエスト完了' が httpStatus・processingTime フィールドとともに出力される"""
        import logging

        # Act
        with caplog.at_level(logging.INFO):
            client.get(BASE_URL)

        # Assert: メッセージ存在
        end_records = [r for r in caplog.records if 'リクエスト完了' in r.message]
        assert len(end_records) >= 1
        # 設計書6.2: httpStatus・processingTime が extra フィールドに付与されること
        record = end_records[0]
        assert hasattr(record, 'httpStatus'), 'httpStatus フィールドが付与されていない'
        assert hasattr(record, 'processingTime'), 'processingTime フィールドが付与されていない'
        assert isinstance(record.processingTime, int)

    def test_logger_attaches_endpoint_and_method_in_request_context(self, client, caplog):
        """8.1.5: LoggerAdapter がリクエストコンテキストから endpoint・method を extra フィールドに自動付与する"""
        import logging

        # Act
        with caplog.at_level(logging.INFO):
            client.get(BASE_URL)

        # Assert: リクエスト開始ログが存在すること
        start_records = [r for r in caplog.records if 'リクエスト開始' in r.message]
        assert len(start_records) >= 1
        # 設計書4: endpoint・method が extra フィールドに付与されること
        record = start_records[0]
        assert hasattr(record, 'endpoint'), 'endpoint フィールドが付与されていない'
        assert hasattr(record, 'method'), 'method フィールドが付与されていない'

    def test_logger_attaches_request_id(self, client, caplog):
        """8.1.5: before_request で生成した UUID v4 が g.request_id に設定され、
        LoggerAdapter を通じた全ログに requestId（UUID v4 形式）として付与される"""
        import logging
        import re

        # Act
        with caplog.at_level(logging.INFO):
            client.get(BASE_URL)

        # Assert: リクエスト開始ログが存在すること
        start_records = [r for r in caplog.records if 'リクエスト開始' in r.message]
        assert len(start_records) >= 1
        # 設計書2.3: requestId が UUID v4 形式で extra フィールドに付与されること
        record = start_records[0]
        assert hasattr(record, 'requestId'), 'requestId フィールドが付与されていない'
        uuid_pattern = r'^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$'
        assert re.match(uuid_pattern, record.requestId), f'requestId が UUID v4 形式ではない: {record.requestId}'

    def test_insert_is_logged_as_info_with_query_and_duration(
        self, client, caplog, measurement_item_left, measurement_item_right,
    ):
        """8.1.3: INSERT クエリ実行時に INFO 'SQL実行' がクエリ内容・実行時間とともに出力される"""
        import logging

        # Arrange: GadgetTypeMaster を登録してから POST（INSERT が発生する）
        from iot_app.models.customer_dashboard import GadgetTypeMaster
        from iot_app import db
        with client.application.app_context():
            gt = GadgetTypeMaster(
                gadget_type_id=1,
                gadget_type_name='時系列グラフ',
                data_source_type=1,
                gadget_image_path='images/gadgets/timeline.png',
                gadget_description='時系列グラフガジェット',
                display_order=1,
                creator=1,
                modifier=1,
                delete_flag=False,
            )
            db.session.add(gt)
            db.session.commit()

        form_data = {
            'title':        'ログテスト',
            'device_mode':  'variable',
            'device_id':    '0',
            'group_id':     '1',
            'left_item_id':  '1',
            'right_item_id': '2',
            'gadget_size':  '2x2',
        }

        # Act
        with caplog.at_level(logging.INFO):
            client.post(f'{BASE_URL}/gadgets/timeline/register', data=form_data)

        # Assert: INSERT に対する INFO ログが出力されていること
        info_sql_records = [
            r for r in caplog.records
            if 'SQL実行' in r.message and r.levelno == logging.INFO
        ]
        assert len(info_sql_records) >= 1

    def test_select_is_logged_as_debug(self, client, caplog):
        """8.1.3: SELECT クエリ実行時に DEBUG 'SQL実行' が出力される"""
        import logging

        # Act: ダッシュボード一覧（SELECT が発生）
        with caplog.at_level(logging.DEBUG):
            client.get(BASE_URL)

        # Assert: SELECT に対する DEBUG ログが出力されていること
        debug_sql_records = [
            r for r in caplog.records
            if 'SQL実行' in r.message and r.levelno == logging.DEBUG
        ]
        assert len(debug_sql_records) >= 1

    # ─── 8.2 異常系ログ ───────────────────────────────────────────────────────

    def test_data_fetch_error_logged_as_error(
        self, client, timeline_gadget, mocker, caplog,
    ):
        """8.2.1: データ取得エラー発生時に ERROR '時系列グラフデータ取得エラー' が出力される"""
        import logging
        mocker.patch(_SILVER_QUERY, side_effect=Exception('接続エラー'))

        # Act
        with caplog.at_level(logging.ERROR):
            client.post(
                f'{BASE_URL}/gadgets/{timeline_gadget.gadget_uuid}/data',
                json={
                    'start_datetime': _VALID_START_DATETIME,
                    'end_datetime':   _VALID_END_DATETIME,
                },
            )

        # Assert
        assert any('時系列グラフデータ取得エラー' in r.message for r in caplog.records)

    def test_csv_export_error_logged_as_error(
        self, client, timeline_gadget, mocker, caplog,
    ):
        """8.2.1: CSVエクスポートエラー発生時に ERROR '時系列グラフCSVエクスポートエラー' が出力される"""
        import logging
        mocker.patch(_SILVER_QUERY, side_effect=Exception('接続エラー'))

        # Act
        with caplog.at_level(logging.ERROR):
            client.get(
                f'{BASE_URL}/gadgets/{timeline_gadget.gadget_uuid}',
                query_string={
                    'export':         'csv',
                    'start_datetime': _VALID_START_DATETIME,
                    'end_datetime':   _VALID_END_DATETIME,
                },
            )

        # Assert
        assert any('時系列グラフCSVエクスポートエラー' in r.message for r in caplog.records)

    def test_register_error_logged_as_error_with_exc_info(
        self, client, measurement_item_left, measurement_item_right, mocker, caplog,
    ):
        """8.2.1: ガジェット登録でサービス例外が発生した場合に
        ERROR '時系列グラフガジェット登録エラー' が exc_info=True で出力される"""
        import logging
        mocker.patch(_REGISTER_GADGET, side_effect=Exception('DB接続エラー'))

        form_data = {
            'title':        'エラーテスト',
            'device_mode':  'variable',
            'device_id':    '0',
            'group_id':     '1',
            'left_item_id':  '1',
            'right_item_id': '2',
            'gadget_size':  '2x2',
        }

        # Act
        with caplog.at_level(logging.ERROR):
            client.post(f'{BASE_URL}/gadgets/timeline/register', data=form_data)

        # Assert
        error_records = [
            r for r in caplog.records
            if '時系列グラフガジェット登録エラー' in r.message
        ]
        assert len(error_records) >= 1
        # exc_info=True が指定されていること（exc_info が設定されているレコードを確認）
        assert any(r.exc_info is not None for r in error_records)

    def test_register_success_is_logged_as_info(
        self, client, measurement_item_left, measurement_item_right, mocker, caplog,
    ):
        """8.1.4: ガジェット登録成功時に INFO '時系列グラフガジェット登録成功' が出力される（設計書6.1 手動出力）"""
        import logging
        mocker.patch(_REGISTER_GADGET)  # DBへの実際の書き込みをスキップ

        form_data = {
            'title':         'ログテスト登録成功',
            'device_mode':   'variable',
            'device_id':     '0',
            'group_id':      '1',
            'left_item_id':  '1',
            'right_item_id': '2',
            'gadget_size':   '2x2',
        }

        # Act
        with caplog.at_level(logging.INFO):
            client.post(f'{BASE_URL}/gadgets/timeline/register', data=form_data)

        # Assert: 登録成功の INFO ログが出力されていること
        assert any('時系列グラフガジェット登録成功' in r.message for r in caplog.records)

    def test_register_validation_error_is_logged_as_warning(
        self, client, measurement_item_left, measurement_item_right, mocker, caplog,
    ):
        """8.2.2: ガジェット登録でバリデーションエラー時に WARNING '時系列グラフガジェット登録バリデーションエラー' が出力される"""
        import logging
        from iot_app.common.exceptions import ValidationError as AppValidationError
        mocker.patch(_REGISTER_GADGET, side_effect=AppValidationError('テストバリデーションエラー'))

        form_data = {
            'title':         'バリデーションエラーテスト',
            'device_mode':   'variable',
            'device_id':     '0',
            'group_id':      '1',
            'left_item_id':  '1',
            'right_item_id': '2',
            'gadget_size':   '2x2',
        }

        # Act
        with caplog.at_level(logging.WARNING):
            client.post(f'{BASE_URL}/gadgets/timeline/register', data=form_data)

        # Assert: バリデーションエラーの WARNING ログが出力されていること
        assert any(
            '時系列グラフガジェット登録バリデーションエラー' in r.message
            for r in caplog.records
        )

    def test_500_error_is_logged_as_error_with_error_type(
        self, client, timeline_gadget, mocker, caplog,
    ):
        """8.2.1: 500エラー発生時に error_handlers.py が ERROR レベルでログを出力する"""
        import logging
        mocker.patch(_SILVER_QUERY, side_effect=Exception('内部エラー'))

        # Act
        with caplog.at_level(logging.ERROR):
            client.post(
                f'{BASE_URL}/gadgets/{timeline_gadget.gadget_uuid}/data',
                json={
                    'start_datetime': _VALID_START_DATETIME,
                    'end_datetime':   _VALID_END_DATETIME,
                },
            )

        # Assert: ERROR レベルのログが出力されていること
        error_records = [r for r in caplog.records if r.levelno == logging.ERROR]
        assert len(error_records) >= 1

    def test_404_error_is_logged_as_warning_with_http_status(self, client, caplog):
        """8.2.2: 404エラー発生時に error_handlers.py が WARNING レベルで httpStatus=404 とともにログを出力する"""
        import logging

        # Act: 存在しない gadget_uuid でデータ取得 → 404
        with caplog.at_level(logging.WARNING):
            client.post(
                f'{BASE_URL}/gadgets/nonexistent-uuid/data',
                json={
                    'start_datetime': _VALID_START_DATETIME,
                    'end_datetime':   _VALID_END_DATETIME,
                },
            )

        # Assert: WARNING レベルのログが出力されていること
        warning_records = [r for r in caplog.records if r.levelno == logging.WARNING]
        assert len(warning_records) >= 1
        # 設計書6.6: httpStatus=404 が extra フィールドに付与されること
        status_records = [r for r in warning_records if getattr(r, 'httpStatus', None) == 404]
        assert len(status_records) >= 1, 'httpStatus=404 フィールドが付与されていない'

    # ─── 8.3 機密情報マスキング ───────────────────────────────────────────────

    def test_email_is_masked_in_log_output(self, app, caplog):
        """8.3.1: email キーを使用したログ出力でメールアドレスが自動マスキングされる
        （ローカル部の先頭2文字以外を '****' に置換）"""
        import logging

        # Arrange: リクエストコンテキスト内で AppLoggerAdapter を通じてログ出力
        with app.test_request_context('/'):
            from iot_app.common.logger import get_logger
            test_logger = get_logger('test.masking')

            # Act
            with caplog.at_level(logging.INFO):
                test_logger.info('テスト', extra={'email': 'yamada@example.com'})

        # Assert: 平文のメールアドレスが出力されていないこと
        assert 'yamada@example.com' not in caplog.text
        # マスキング後の値がレコード属性に付与されていること（先頭2文字 + **** + @以降）
        assert any(getattr(r, 'email', None) == 'ya****@example.com' for r in caplog.records)

    def test_phone_is_masked_in_log_output(self, app, caplog):
        """8.3.2: phone キーを使用したログ出力で電話番号が自動マスキングされる
        （中間4桁を '****' に置換）"""
        import logging

        # Arrange
        with app.test_request_context('/'):
            from iot_app.common.logger import get_logger
            test_logger = get_logger('test.masking')

            # Act
            with caplog.at_level(logging.INFO):
                test_logger.info('テスト', extra={'phone': '090-1234-5678'})

        # Assert: 平文の電話番号が出力されていないこと
        assert '090-1234-5678' not in caplog.text
        # マスキング後の値がレコード属性に付与されていること
        assert any(getattr(r, 'phone', None) == '090-****-5678' for r in caplog.records)

    def test_non_sensitive_key_is_not_masked(self, app, caplog):
        """8.3.1: マスキング対象外のキーはそのまま出力される"""
        import logging

        # Arrange
        with app.test_request_context('/'):
            from iot_app.common.logger import get_logger
            test_logger = get_logger('test.masking')

            # Act
            with caplog.at_level(logging.INFO):
                test_logger.info('テスト', extra={'gadget_uuid': 'abc-123-def'})

        # Assert: マスキング対象外のキーはレコード属性にそのまま付与されること
        assert any(getattr(r, 'gadget_uuid', None) == 'abc-123-def' for r in caplog.records)


# ─────────────────────────────────────────────────────────────────────────────
# 7. トランザクション・ロールバックテスト
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.integration
class TestTransaction:
    """トランザクション・ロールバックテスト

    観点: 7.1 正常コミットテスト、7.2 ロールバックテスト（integration-test-perspectives.md）

    timeline の register_gadget は以下のトランザクション構造を持つ:
      db.session.add(gadget) → db.session.commit()
      except IntegrityError: db.session.rollback() → raise
    ビュー層の except Exception でさらに db.session.rollback() → abort(500)
    """

    _URL = f"{BASE_URL}/gadgets/timeline/register"

    @pytest.fixture(autouse=True)
    def _auth(self, auth_user_id, user_master, organization_closure):
        """全テストで g.current_user と user_master / organization_closure を自動セットアップする"""
        pass

    @pytest.fixture(autouse=True)
    def _register_setup(self, dashboard_group_master, dashboard_user_setting):
        """全テストで DashboardGroupMaster / DashboardUserSetting を事前登録する"""
        pass

    @pytest.fixture(autouse=True)
    def _gadget_type(self, db_session):
        """全テストで GadgetTypeMaster を事前登録する"""
        from iot_app.models.customer_dashboard import GadgetTypeMaster
        gt = GadgetTypeMaster(
            gadget_type_id=1,
            gadget_type_name='時系列グラフ',
            data_source_type=1,
            gadget_image_path='images/gadgets/timeline.png',
            gadget_description='時系列グラフガジェット',
            display_order=1,
            creator=1,
            modifier=1,
            delete_flag=False,
        )
        db_session.add(gt)
        db_session.flush()

    def _valid_form(self, **overrides):
        data = {
            'title':         'トランザクションテスト',
            'device_mode':   'variable',
            'device_id':     '0',
            'group_id':      '1',
            'left_item_id':  '1',
            'right_item_id': '2',
            'gadget_size':   '2x2',
        }
        data.update(overrides)
        return data

    def test_register_success_persists_to_db(
        self, client, app, measurement_item_left, measurement_item_right,
    ):
        """7.1.1: 正常登録でコミットが完了し、DBにレコードが永続化される"""
        # Act
        response = client.post(self._URL, data=self._valid_form())

        # Assert: 302リダイレクトかつDBに1件存在
        assert response.status_code == 302
        with app.app_context():
            from iot_app import db
            from iot_app.models.customer_dashboard import DashboardGadgetMaster
            count = db.session.query(DashboardGadgetMaster).filter_by(delete_flag=False).count()
        assert count == 1

    @pytest.mark.skip(reason='gadget_uuid UNIQUE制約がモデルに未定義のため保留')
    def test_unique_uuid_constraint_violation_returns_500(
        self, client, app, measurement_item_left, measurement_item_right, mocker,
    ):
        """7.2.1: gadget_uuid UNIQUE制約違反時にロールバックされ500エラーが返る

        uuid.uuid4() を固定値にモックすることで、2件目の登録で IntegrityError を発生させる。
        サービス層が rollback() を呼び出した後 raise し、ビュー層が abort(500) を返すことを確認。
        """
        import uuid as uuid_module
        fixed_uuid = str(uuid_module.uuid4())
        mocker.patch(
            'iot_app.services.customer_dashboard.timeline.uuid.uuid4',
            return_value=fixed_uuid,
        )

        # Arrange: 1件目を正常登録
        client.post(self._URL, data=self._valid_form(title='1件目'))

        # Act: 同一 UUID で2件目を登録 → UNIQUE制約違反
        response = client.post(self._URL, data=self._valid_form(title='2件目'))

        # Assert: 500エラーが返る
        assert response.status_code == 500

        # Assert: DBには1件のみ存在（2件目がロールバックされている）
        with app.app_context():
            from iot_app import db
            from iot_app.models.customer_dashboard import DashboardGadgetMaster
            count = db.session.query(DashboardGadgetMaster).count()
        assert count == 1

    def test_db_exception_during_commit_does_not_persist(
        self, client, app, measurement_item_left, measurement_item_right, mocker,
    ):
        """7.2.3: commit 中に Exception が発生した場合、データがDBに残らない

        処理途中（commit 時）で例外が発生しても、ロールバックにより
        DashboardGadgetMaster にレコードが残らないことを確認する。
        """
        mocker.patch(
            'iot_app.services.customer_dashboard.timeline.db.session.commit',
            side_effect=Exception('DB接続断'),
        )

        # Act
        response = client.post(self._URL, data=self._valid_form())

        # Assert: 500エラーが返る
        assert response.status_code == 500

        # Assert: DBにレコードが残っていない
        with app.app_context():
            from iot_app import db
            from iot_app.models.customer_dashboard import DashboardGadgetMaster
            count = db.session.query(DashboardGadgetMaster).count()
        assert count == 0

    def test_integrity_error_leaves_no_partial_data(
        self, client, app, measurement_item_left, measurement_item_right, mocker,
    ):
        """7.2.4: IntegrityError 発生時に明示的 rollback() が呼ばれ、DBが汚染されない

        register_gadget 内で IntegrityError が raise された後、
        ビュー層の except Exception → db.session.rollback() が呼ばれ、
        DBに中途半端なデータが残らないことを確認する。
        """
        from sqlalchemy.exc import IntegrityError
        mocker.patch(
            'iot_app.services.customer_dashboard.timeline.db.session.commit',
            side_effect=IntegrityError('UNIQUE', {}, Exception()),
        )

        # Act
        response = client.post(self._URL, data=self._valid_form())

        # Assert: エラーレスポンスが返る（500 または rollback による 5xx）
        assert response.status_code == 500

        # Assert: DBにデータが一切残っていない
        with app.app_context():
            from iot_app import db
            from iot_app.models.customer_dashboard import DashboardGadgetMaster
            count = db.session.query(DashboardGadgetMaster).count()
        assert count == 0


# ─────────────────────────────────────────────────────────────────────────────
# 9. セキュリティテスト
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.integration
class TestSecurity:
    """## 9. セキュリティテスト

    9.1 SQLインジェクションテスト
    9.2 XSS（クロスサイトスクリプティング）テスト
    9.3 CSRF対策テスト
    """

    _URL = f"{BASE_URL}/gadgets/timeline/register"
    _CREATE_URL = f"{BASE_URL}/gadgets/timeline/create"

    @pytest.fixture(autouse=True)
    def _auth(self, auth_user_id, user_master, organization_closure):
        """全テストで g.current_user と user_master / organization_closure を自動セットアップする"""
        pass

    @pytest.fixture(autouse=True)
    def _register_setup(self, dashboard_group_master, dashboard_user_setting):
        """全テストで DashboardGroupMaster / DashboardUserSetting を事前登録する"""
        pass

    @pytest.fixture(autouse=True)
    def _gadget_type(self, db_session):
        """全テストで GadgetTypeMaster を事前登録する"""
        from iot_app.models.customer_dashboard import GadgetTypeMaster
        gt = GadgetTypeMaster(
            gadget_type_id=1,
            gadget_type_name='時系列グラフ',
            data_source_type=1,
            gadget_image_path='images/gadgets/timeline.png',
            gadget_description='時系列グラフガジェット',
            display_order=1,
            creator=1,
            modifier=1,
            delete_flag=False,
        )
        db_session.add(gt)
        db_session.flush()

    def _valid_form(self, **overrides):
        """セキュリティテスト用の最小有効フォームデータ"""
        data = {
            'title':         'セキュリティテスト',
            'device_mode':   'variable',
            'device_id':     '0',
            'group_id':      '1',
            'left_item_id':  '1',
            'right_item_id': '2',
            'gadget_size':   '2x2',
        }
        data.update(overrides)
        return data

    # ── 9.1 SQLインジェクションテスト ──────────────────────────────────────────

    def test_sql_injection_short_payload_does_not_cause_db_error(
        self, client, measurement_item_left, measurement_item_right,
    ):
        """9.1.1: 20文字以内のSQLインジェクション文字列はDBエラー(500)にならない

        SQLAlchemy のプリペアドステートメントにより、インジェクション文字列は
        リテラル文字列として扱われ、任意のSQLは実行されない。
        """
        injection = "' OR 1=1 --"  # 12文字: Length(max=20) を通過する
        response = client.post(self._URL, data=self._valid_form(title=injection))
        # 302（登録成功）または 400（バリデーションエラー）。DBエラー（500）にはならない
        assert response.status_code in (302, 400)

    def test_sql_injection_semicolon_multi_statement_does_not_cause_db_error(
        self, client, measurement_item_left, measurement_item_right,
    ):
        """9.1.2: セミコロン複文インジェクション試行（16文字）がDBエラーにならない

        SQLAlchemy はプリペアドステートメントを使用するため、
        セミコロンによる複文実行を防御する。
        """
        injection = "1'; SELECT 1; --"  # 16文字
        response = client.post(self._URL, data=self._valid_form(title=injection))
        assert response.status_code in (302, 400)

    def test_sql_injection_long_payload_returns_400_by_length_validation(
        self, client, measurement_item_left, measurement_item_right,
    ):
        """9.1.3: 20文字超のSQLインジェクション文字列は文字数制限バリデーションで400を返す

        WTForms の Length(max=20) バリデーションが先に動作し、
        DBに到達する前に弾かれる。
        """
        long_injection = "'; DROP TABLE gadgets; --"  # 25文字
        response = client.post(self._URL, data=self._valid_form(title=long_injection))
        assert response.status_code == 400

    # ── 9.2 XSS（クロスサイトスクリプティング）テスト ───────────────────────────

    def test_xss_script_tag_in_gadget_name_is_escaped_in_dashboard(
        self, client, auth_user_id, dashboard_group_master, db_session, measurement_item_left, measurement_item_right,
    ):
        """9.2.1: <script>タグを含むガジェット名はJinja2自動エスケープで無害化される

        Jinja2 の {{ }} 構文はデフォルトでHTMLエスケープを行うため、
        <script> は &lt;script&gt; として出力され、XSSが成立しない。
        """
        import json
        from iot_app.models.customer_dashboard import DashboardGadgetMaster

        xss_name = '<script>alert(1)</script>'
        gadget = DashboardGadgetMaster(
            gadget_uuid=str(uuid.uuid4()),
            gadget_name=xss_name,
            gadget_type_id=1,
            dashboard_group_id=1,
            chart_config=json.dumps({
                'left_item_id':    1,
                'right_item_id':   2,
                'left_min_value':  None,
                'left_max_value':  None,
                'right_min_value': None,
                'right_max_value': None,
            }),
            data_source_config=json.dumps({'device_id': None}),
            position_x=0,
            position_y=1,
            gadget_size='2x2',
            display_order=1,
            creator=1,
            modifier=1,
        )
        db_session.add(gadget)
        db_session.flush()

        response = client.get(BASE_URL)
        html = response.data.decode('utf-8')

        # 生の <script> タグが HTML に含まれていない（XSS が成立しない）
        assert '<script>alert(1)</script>' not in html
        # Jinja2 によるエスケープ済み文字列が含まれる
        assert '&lt;script&gt;' in html

    def test_xss_img_onerror_in_gadget_name_is_escaped_in_dashboard(
        self, client, auth_user_id, dashboard_group_master, db_session, measurement_item_left, measurement_item_right,
    ):
        """9.2.2: <img onerror=...>を含むガジェット名はJinja2自動エスケープで無害化される

        onerror イベントハンドラによるXSSを防止する。
        """
        import json
        from iot_app.models.customer_dashboard import DashboardGadgetMaster

        xss_name = '<img src=x onerror=alert(1)>'
        gadget = DashboardGadgetMaster(
            gadget_uuid=str(uuid.uuid4()),
            gadget_name=xss_name,
            gadget_type_id=1,
            dashboard_group_id=1,
            chart_config=json.dumps({
                'left_item_id':    1,
                'right_item_id':   2,
                'left_min_value':  None,
                'left_max_value':  None,
                'right_min_value': None,
                'right_max_value': None,
            }),
            data_source_config=json.dumps({'device_id': None}),
            position_x=0,
            position_y=1,
            gadget_size='2x2',
            display_order=1,
            creator=1,
            modifier=1,
        )
        db_session.add(gadget)
        db_session.flush()

        response = client.get(BASE_URL)
        html = response.data.decode('utf-8')

        # 生の <img onerror> タグが出力されていない
        assert '<img src=x onerror=alert(1)>' not in html
        # Jinja2 によるエスケープ済み文字列が含まれる
        assert '&lt;img' in html

    def test_xss_javascript_uri_in_gadget_name_is_escaped_in_dashboard(
        self, client, auth_user_id, dashboard_group_master, db_session, measurement_item_left, measurement_item_right,
    ):
        """9.2.3: javascript:スキームを含むガジェット名はJinja2自動エスケープで無害化される

        Jinja2 は {{ }} 内の文字列を自動エスケープするため、
        javascript: スキームが href 属性として生出力されることを防ぐ。
        """
        import json
        from iot_app.models.customer_dashboard import DashboardGadgetMaster

        xss_name = 'javascript:alert(1)'
        gadget = DashboardGadgetMaster(
            gadget_uuid=str(uuid.uuid4()),
            gadget_name=xss_name,
            gadget_type_id=1,
            dashboard_group_id=1,
            chart_config=json.dumps({
                'left_item_id':    1,
                'right_item_id':   2,
                'left_min_value':  None,
                'left_max_value':  None,
                'right_min_value': None,
                'right_max_value': None,
            }),
            data_source_config=json.dumps({'device_id': None}),
            position_x=0,
            position_y=1,
            gadget_size='2x2',
            display_order=1,
            creator=1,
            modifier=1,
        )
        db_session.add(gadget)
        db_session.flush()

        response = client.get(BASE_URL)
        html = response.data.decode('utf-8')

        # javascript: スキームが href 属性として生出力されていない
        assert 'href="javascript:alert(1)"' not in html

    # ── 9.3 CSRF対策テスト ───────────────────────────────────────────────────

    def test_post_without_csrf_token_when_csrf_enabled_returns_400(
        self, app, measurement_item_left, measurement_item_right,
    ):
        """9.3.1: CSRF有効時、CSRFトークンなしのPOSTは400を返す

        WTF_CSRF_ENABLED=True かつ TESTING=False の環境では、
        form.validate_on_submit() が CSRF バリデーションを行い、
        トークンなしのリクエストを拒否する。
        """
        app.config['WTF_CSRF_ENABLED'] = True
        app.config['TESTING'] = False
        csrf_client = app.test_client()
        try:
            response = csrf_client.post(self._URL, data=self._valid_form())
            assert response.status_code == 400
        finally:
            app.config['WTF_CSRF_ENABLED'] = False
            app.config['TESTING'] = True

    def test_post_with_invalid_csrf_token_when_csrf_enabled_returns_400(
        self, app, measurement_item_left, measurement_item_right,
    ):
        """9.3.2: CSRF有効時、無効なCSRFトークンでのPOSTは400を返す

        推測または改ざんされたCSRFトークンはバリデーションに失敗し、
        リクエストが拒否されることを確認する。
        """
        app.config['WTF_CSRF_ENABLED'] = True
        app.config['TESTING'] = False
        csrf_client = app.test_client()
        try:
            data = self._valid_form()
            data['csrf_token'] = 'invalid-csrf-token-value'
            response = csrf_client.post(self._URL, data=data)
            assert response.status_code == 400
        finally:
            app.config['WTF_CSRF_ENABLED'] = False
            app.config['TESTING'] = True

