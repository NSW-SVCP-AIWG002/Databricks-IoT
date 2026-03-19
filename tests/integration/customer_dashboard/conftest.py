"""
顧客作成ダッシュボード 結合テスト共通フィクスチャ

NOTE: このテストはモデルファイル（models/dashboard.py, models/measurement.py 等）が
      実装済みであることを前提とする。ブランチ統合後に実行可能。
"""

import json
import uuid

import pytest


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
        from iot_app.models.dashboard import (
            DashboardGadgetMaster, DashboardGroupMaster, DashboardMaster,
            DashboardUserSetting, GadgetTypeMaster,
        )
        from iot_app.models.device import DeviceMaster
        from iot_app.models.measurement import MeasurementItemMaster
        from iot_app.models.organization import OrganizationClosure, OrganizationMaster
        _db.session.query(DashboardGadgetMaster).delete()
        _db.session.query(DashboardUserSetting).delete()
        _db.session.query(DashboardGroupMaster).delete()
        _db.session.query(DashboardMaster).delete()
        _db.session.query(DeviceMaster).delete()
        _db.session.query(OrganizationClosure).delete()
        _db.session.query(GadgetTypeMaster).delete()
        _db.session.query(MeasurementItemMaster).delete()
        _db.session.query(OrganizationMaster).delete()
        _db.session.commit()


@pytest.fixture()
def auth_user_id(app):
    """テスト用: g.current_user_id を 1 に設定する before_request ハンドラを登録"""
    def _inject():
        from flask import g
        g.current_user_id = 1

    app.before_request_funcs.setdefault(None, []).append(_inject)
    yield 1
    app.before_request_funcs[None].remove(_inject)


@pytest.fixture()
def gadget_variable(db_session, gadget_type):
    """DashboardGadgetMaster テストレコード（デバイス可変モード: device_id=None）"""
    import json as _json
    import uuid as _uuid
    from iot_app.models.dashboard import DashboardGadgetMaster
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
    """DashboardMaster テストレコード（仮実装）"""
    from iot_app.models.dashboard import DashboardMaster
    d = DashboardMaster(
        dashboard_id=1,
        dashboard_name='テストダッシュボード',
        delete_flag=False,
    )
    db_session.add(d)
    db_session.flush()
    return d


@pytest.fixture()
def dashboard_user_setting(db_session, dashboard_master):
    """DashboardUserSetting テストレコード（user_id=1, device_id=1）"""
    from iot_app.models.dashboard import DashboardUserSetting
    s = DashboardUserSetting(
        user_id=1,
        dashboard_id=dashboard_master.dashboard_id,
        device_id=1,
    )
    db_session.add(s)
    db_session.flush()
    return s


@pytest.fixture()
def dashboard_group_master(db_session, dashboard_master):
    """DashboardGroupMaster テストレコード（仮実装）"""
    from iot_app.models.dashboard import DashboardGroupMaster
    gr = DashboardGroupMaster(
        group_id=1,
        dashboard_id=dashboard_master.dashboard_id,
        group_name='テストグループ',
        display_order=1,
        delete_flag=False,
    )
    db_session.add(gr)
    db_session.flush()
    return gr


@pytest.fixture()
def gadget_type(db_session):
    """GadgetTypeMaster テストレコード（FKのために必要）"""
    from iot_app.models.dashboard import GadgetTypeMaster
    gt = GadgetTypeMaster(
        gadget_type_id=1,
        gadget_type_name='棒グラフ',
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
        display_name='外気温度',
        silver_data_column_name='external_temp',
        delete_flag=False,
    )
    db_session.add(item)
    db_session.flush()
    return item


@pytest.fixture()
def gadget(db_session, gadget_type):
    """DashboardGadgetMaster テストレコード（デバイス固定モード, 2x2）"""
    from iot_app.models.dashboard import DashboardGadgetMaster
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
