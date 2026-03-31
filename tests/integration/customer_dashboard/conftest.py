"""
顧客作成ダッシュボード 結合テスト共通フィクスチャ

NOTE: このテストはモデルファイル（models/dashboard.py, models/measurement.py 等）が
      実装済みであることを前提とする。ブランチ統合後に実行可能。
"""

import json
import os
import uuid
from datetime import date, datetime
from unittest.mock import patch

import pytest


@pytest.fixture(autouse=True)
def bypass_auth_middleware():
    """認証ミドルウェアをテスト用にバイパスする

    DevAuthProvider が "dev@localhost" のユーザーを DB から検索するが、
    テスト DB には存在しないため 403 になる。
    find_user_by_email をパッチして middleware が正常通過するようにする。
    """
    with patch(
        'iot_app.auth.middleware.find_user_by_email',
        return_value={'user_id': 1, 'user_type_id': 1},
    ):
        with patch.dict(os.environ, {'DEV_DATABRICKS_TOKEN': 'test-token'}):
            yield


@pytest.fixture()
def db_session(app):
    """テスト用DBセッション（customer_dashboardテスト向けオーバーライド）

    ルートconftestのdb_sessionはbegin_nested()でSAVEPOINTを使うが、
    テスト内で db.session.commit() が呼ばれるとSAVEPOINTが解放され
    rollback()がエラーになる。clean_dbフィクスチャでテスト間分離を
    担保するため、ここではSAVEPOINTを使わないシンプルな実装にする。
    """
    with app.app_context():
        from iot_app import db as _db
        yield _db.session
        _db.session.rollback()


@pytest.fixture(autouse=True)
def disable_csrf(app):
    """CSRFを無効化（結合テスト用）"""
    app.config['WTF_CSRF_ENABLED'] = False
    yield
    app.config['WTF_CSRF_ENABLED'] = True


@pytest.fixture(autouse=True)
def clean_db(app):
    """各テスト後に全テーブルをクリア（テスト間分離）

    サービス層の db.session.commit() により db_session.rollback() では
    元に戻せないデータが残るため、テスト後に明示的に全レコードを削除する。
    FK制約に従い依存先テーブルから順に削除する。
    """
    yield
    from iot_app import db as _db
    with app.app_context():
        _db.session.remove()
        from iot_app.models.customer_dashboard import (
            DashboardGadgetMaster, DashboardGroupMaster, DashboardMaster,
            DashboardUserSetting, GadgetTypeMaster, GoldSummaryMethodMaster,
        )
        from iot_app.models.device import DeviceMaster
        from iot_app.models.measurement import MeasurementItemMaster
        from iot_app.models.organization import OrganizationClosure, OrganizationMaster
        from iot_app.models.user import User
        _db.session.query(DashboardGadgetMaster).delete()
        _db.session.query(DashboardUserSetting).delete()
        _db.session.query(DashboardGroupMaster).delete()
        _db.session.query(DashboardMaster).delete()
        _db.session.query(DeviceMaster).delete()
        _db.session.query(OrganizationClosure).delete()
        _db.session.query(GadgetTypeMaster).delete()
        _db.session.query(GoldSummaryMethodMaster).delete()
        _db.session.query(MeasurementItemMaster).delete()
        _db.session.query(User).delete()
        _db.session.query(OrganizationMaster).delete()
        _db.session.commit()


@pytest.fixture(autouse=True)
def inject_current_user(app):
    """テスト用: g.current_user（user_id=None）を全テストで注入

    認証未実装ブランチのため user_id=None を設定する。
    auth_user_id フィクスチャと併用する場合は auth_user_id 側で上書きされる。
    """
    from types import SimpleNamespace

    def _inject():
        from flask import g
        if not hasattr(g, 'current_user'):
            g.current_user = SimpleNamespace(user_id=None)

    app.before_request_funcs.setdefault(None, []).append(_inject)
    yield
    app.before_request_funcs[None].remove(_inject)


@pytest.fixture()
def auth_user_id(app):
    """テスト用: g.current_user_id=1 および g.current_user.user_id=1 を設定"""
    from types import SimpleNamespace

    def _inject():
        from flask import g
        g.current_user = SimpleNamespace(user_id=1)

    app.before_request_funcs.setdefault(None, []).append(_inject)
    yield 1
    app.before_request_funcs[None].remove(_inject)


@pytest.fixture()
def gadget_variable(db_session, gadget_type):
    """DashboardGadgetMaster テストレコード（デバイス可変モード: device_id=None）"""
    import json as _json
    import uuid as _uuid
    from iot_app.models.customer_dashboard import DashboardGadgetMaster
    g = DashboardGadgetMaster(
        gadget_uuid=str(_uuid.uuid4()),
        gadget_name='テスト棒グラフ（可変）',
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
    db_session.add(g)
    db_session.flush()
    return g


@pytest.fixture()
def dashboard_master(db_session):
    """DashboardMaster テストレコード"""
    from iot_app.models.customer_dashboard import DashboardMaster
    d = DashboardMaster(
        dashboard_uuid=str(uuid.uuid4()),
        dashboard_name='テストダッシュボード',
        organization_id=1,
        creator=1,
        modifier=1,
        delete_flag=False,
    )
    db_session.add(d)
    db_session.flush()
    return d


@pytest.fixture()
def dashboard_user_setting(db_session, dashboard_master):
    """DashboardUserSetting テストレコード（user_id=1, device_id=1）"""
    from iot_app.models.customer_dashboard import DashboardUserSetting
    s = DashboardUserSetting(
        user_id=1,
        dashboard_id=dashboard_master.dashboard_id,
        device_id=1,
        creator=1,
        modifier=1,
    )
    db_session.add(s)
    db_session.flush()
    return s


@pytest.fixture()
def dashboard_group_master(db_session, dashboard_master):
    """DashboardGroupMaster テストレコード"""
    from iot_app.models.customer_dashboard import DashboardGroupMaster
    gr = DashboardGroupMaster(
        dashboard_group_uuid=str(uuid.uuid4()),
        dashboard_group_name='テストグループ',
        dashboard_id=dashboard_master.dashboard_id,
        display_order=1,
        creator=1,
        modifier=1,
        delete_flag=False,
    )
    db_session.add(gr)
    db_session.flush()
    return gr


@pytest.fixture()
def gold_summary_method_master(db_session):
    """GoldSummaryMethodMaster テストレコード"""
    from iot_app.models.customer_dashboard import GoldSummaryMethodMaster
    records = []
    for sm_id, code, name in [
        (1, 'AVG', '平均'),
        (2, 'MAX', '最大'),
        (3, 'MIN', '最小'),
    ]:
        sm = GoldSummaryMethodMaster(
            summary_method_id=sm_id,
            summary_method_code=code,
            summary_method_name=name,
            creator=1,
            modifier=1,
        )
        db_session.add(sm)
        records.append(sm)
    db_session.flush()
    return records


@pytest.fixture()
def gadget_type(db_session):
    """GadgetTypeMaster テストレコード（FKのために必要）"""
    from iot_app.models.customer_dashboard import GadgetTypeMaster
    gt = GadgetTypeMaster(
        gadget_type_id=1,
        gadget_type_name='棒グラフ',
        data_source_type=1,
        gadget_image_path='images/gadgets/bar_chart.png',
        gadget_description='棒グラフガジェット',
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
    """MeasurementItemMaster テストレコード"""
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
def gadget(db_session, gadget_type):
    """DashboardGadgetMaster テストレコード（デバイス固定モード, 2x2）"""
    from iot_app.models.customer_dashboard import DashboardGadgetMaster
    g = DashboardGadgetMaster(
        gadget_uuid=str(uuid.uuid4()),
        gadget_name='テスト棒グラフ',
        gadget_type_id=1,
        dashboard_group_id=1,
        chart_config=json.dumps({
            'measurement_item_id': 1,
            'summary_method_id': 1,
            'min_value': None,
            'max_value': None,
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
def organization_master_record(db_session):
    """OrganizationMaster テストレコード（organization_id=1）"""
    from iot_app.models.organization import OrganizationMaster
    org = OrganizationMaster(
        organization_id=1,
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
    )
    db_session.add(org)
    db_session.flush()
    return org


@pytest.fixture()
def organization_closure_record(db_session, organization_master_record):
    """OrganizationClosure テストレコード（org_id=1 の自己参照）"""
    from iot_app.models.organization import OrganizationClosure
    closure = OrganizationClosure(
        parent_organization_id=1,
        subsidiary_organization_id=1,
        depth=0,
    )
    db_session.add(closure)
    db_session.flush()
    return closure


@pytest.fixture()
def user_master_record(db_session, organization_master_record):
    """UserMaster テストレコード（user_id=1, organization_id=1）"""
    from iot_app.models.user import User
    now = datetime.now()
    user = User(
        user_id=1,
        databricks_user_id='test-databricks-id',
        user_name='テストユーザー',
        organization_id=1,
        email_address='test@test.com',
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
    return user


@pytest.fixture()
def auth_scope(auth_user_id, user_master_record, organization_closure_record):
    """認証ユーザー（user_id=1）のアクセス可能組織スコープをセットアップする結合テスト用フィクスチャ

    - user_master: user_id=1, organization_id=1
    - organization_closure: parent=1, subsidiary=1
    これにより get_organization_id_by_user(1) → 1,
    get_accessible_org_ids(1) → [1] となりスコープチェックを通過できる。
    dashboard_master.organization_id=1 であることが前提。
    """
    return auth_user_id
