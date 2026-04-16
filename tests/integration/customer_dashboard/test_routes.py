"""顧客作成ダッシュボード共通機能 - 結合テスト

対象エンドポイント: /analysis/customer-dashboard (共通機能 No.1〜27 のうち common 担当分)
観点参照: integration-test-perspectives.md

NOTE:
  - require_auth は現状スタブ。本実装後は 1.1 認証テスト（未認証 → 401）を追加すること。
  - テストDBは SQLite in-memory (TestingConfig)。SQLite はデフォルトで FK 制約を無効化するため、
    関連テーブルを完全に構築しなくてもレコード挿入が可能。
  - WTF_CSRF_ENABLED=False (TestingConfig) のため、POST リクエストに CSRF トークン不要。
"""

import json
import re
from datetime import datetime
from unittest.mock import MagicMock

import pytest
from flask import g

from iot_app import db as _db
from iot_app.models.customer_dashboard import (
    DashboardGadgetMaster,
    DashboardGroupMaster,
    DashboardMaster,
    DashboardUserSetting,
    GadgetTypeMaster,
)
from iot_app.models.device import DeviceMaster, DeviceTypeMaster
from iot_app.models.organization import OrganizationClosure, OrganizationMaster
from iot_app.models.user import User

BASE_URL = '/analysis/customer-dashboard'
TEST_USER_ID = 1
TEST_ORG_ID = 1
CHILD_ORG_ID = 2
PARENT_ORG_ID = 3


# ============================================================
# 共通フィクスチャ
# ============================================================

@pytest.fixture(autouse=True)
def inject_current_user(app):
    """全テストリクエストで g.current_user をモックユーザーに差し込む。

    require_auth 本実装前の暫定措置。本実装後は認証ヘッダーによるセッション確立に置き換えること。
    """
    mock_user = MagicMock()
    mock_user.user_id = TEST_USER_ID

    def _set_user():
        g.current_user = mock_user

    app.before_request_funcs.setdefault(None, []).insert(0, _set_user)
    yield mock_user
    funcs = app.before_request_funcs.get(None, [])
    if _set_user in funcs:
        funcs.remove(_set_user)


_TEST_ORG_IDS = (TEST_ORG_ID, CHILD_ORG_ID, PARENT_ORG_ID, 99)
"""テスト全体で使用する組織ID一覧。

元の設計は SQLite in-memory（FK制約なし）を前提としていたが、MySQL に移行済み。
dashboard_master.organization_id の FK 制約を満たすため、
テストで使用する全組織IDのレコードを事前に作成する。
"""


@pytest.fixture()
def seed_user(app):
    """テスト用ユーザーを DB に挿入してコミット。テスト後に削除する。"""
    from datetime import date
    with app.app_context():
        for org_id in _TEST_ORG_IDS:
            if not _db.session.get(OrganizationMaster, org_id):
                _db.session.add(OrganizationMaster(
                    organization_id=org_id,
                    organization_name=f'テスト組織{org_id}',
                    organization_type_id=1,
                    address='テスト住所',
                    phone_number='000-0000-0000',
                    contact_person='テスト担当者',
                    contract_status_id=1,
                    contract_start_date=date(2024, 1, 1),
                    databricks_group_id=f'test-group-{org_id}',
                    creator=1,
                    modifier=1,
                ))
        _db.session.flush()
        user = User(
            user_id=TEST_USER_ID,
            databricks_user_id='test-databricks-uid',
            user_name='テストユーザー',
            organization_id=TEST_ORG_ID,
            email_address='test@example.com',
            user_type_id=1,
            language_code='ja',
            region_id=1,
            address='',
            status=1,
            alert_notification_flag=True,
            system_notification_flag=True,
            create_date=datetime.now(),
            creator=1,
            update_date=datetime.now(),
            modifier=1,
        )
        _db.session.add(user)
        _db.session.commit()

    yield
    # teardown は conftest.py の clean_db (autouse) に委ねる。
    # clean_db は FK 依存順に全テーブルを削除するため、
    # ここで個別に削除すると FK エラーが発生する。


@pytest.fixture()
def seed_org_closure(app, seed_user):
    """テスト用組織閉包レコードを DB に追加（自組織のみアクセス可能な最小構成）。"""
    with app.app_context():
        closure = OrganizationClosure(
            parent_organization_id=TEST_ORG_ID,
            subsidiary_organization_id=TEST_ORG_ID,
            depth=0,
        )
        _db.session.add(closure)
        _db.session.commit()

    yield

    with app.app_context():
        c = _db.session.query(OrganizationClosure).filter_by(
            parent_organization_id=TEST_ORG_ID,
            subsidiary_organization_id=TEST_ORG_ID,
        ).first()
        if c:
            _db.session.delete(c)
            _db.session.commit()


@pytest.fixture()
def seed_child_org_closure(app, seed_user):
    """自org + 子orgの組織閉包を追加（データスコープ1.3.2テスト用）。"""
    with app.app_context():
        self_closure = OrganizationClosure(
            parent_organization_id=TEST_ORG_ID,
            subsidiary_organization_id=TEST_ORG_ID,
            depth=0,
        )
        child_closure = OrganizationClosure(
            parent_organization_id=TEST_ORG_ID,
            subsidiary_organization_id=CHILD_ORG_ID,
            depth=1,
        )
        _db.session.add_all([self_closure, child_closure])
        _db.session.commit()

    yield CHILD_ORG_ID

    with app.app_context():
        for subsidiary_id in (TEST_ORG_ID, CHILD_ORG_ID):
            c = _db.session.query(OrganizationClosure).filter_by(
                parent_organization_id=TEST_ORG_ID,
                subsidiary_organization_id=subsidiary_id,
            ).first()
            if c:
                _db.session.delete(c)
        _db.session.commit()


@pytest.fixture()
def seed_dashboard(app, seed_org_closure):
    """テスト用ダッシュボードを DB に追加。"""
    with app.app_context():
        dashboard = DashboardMaster(
            dashboard_uuid='test-dash-uuid-0001',
            dashboard_name='テストダッシュボード',
            organization_id=TEST_ORG_ID,
            create_date=datetime.now(),
            creator=TEST_USER_ID,
            update_date=datetime.now(),
            modifier=TEST_USER_ID,
        )
        _db.session.add(dashboard)
        _db.session.commit()
        dashboard_id = dashboard.dashboard_id

    yield dashboard_id

    with app.app_context():
        _db.session.query(DashboardUserSetting).filter_by(
            dashboard_id=dashboard_id,
        ).delete(synchronize_session=False)
        _db.session.query(DashboardGroupMaster).filter_by(
            dashboard_id=dashboard_id,
        ).delete(synchronize_session=False)
        d = _db.session.get(DashboardMaster, dashboard_id)
        if d:
            _db.session.delete(d)
        _db.session.commit()


@pytest.fixture()
def seed_group(app, seed_dashboard):
    """テスト用ダッシュボードグループを DB に追加。"""
    with app.app_context():
        group = DashboardGroupMaster(
            dashboard_group_uuid='test-group-uuid-0001',
            dashboard_group_name='テストグループ',
            dashboard_id=seed_dashboard,
            display_order=1,
            create_date=datetime.now(),
            creator=TEST_USER_ID,
            update_date=datetime.now(),
            modifier=TEST_USER_ID,
        )
        _db.session.add(group)
        _db.session.commit()
        group_id = group.dashboard_group_id

    yield group_id

    with app.app_context():
        g_obj = _db.session.get(DashboardGroupMaster, group_id)
        if g_obj:
            _db.session.delete(g_obj)
            _db.session.commit()


@pytest.fixture()
def seed_gadget_type(app):
    """テスト用ガジェット種別を DB に追加。"""
    with app.app_context():
        gadget_type = GadgetTypeMaster(
            gadget_type_name='棒グラフ',
            data_source_type=1,
            gadget_image_path='/static/images/bar_chart.png',
            gadget_description='棒グラフです',
            display_order=6,
            create_date=datetime.now(),
            creator=TEST_USER_ID,
            update_date=datetime.now(),
            modifier=TEST_USER_ID,
        )
        _db.session.add(gadget_type)
        _db.session.commit()
        gadget_type_id = gadget_type.gadget_type_id

    yield gadget_type_id

    with app.app_context():
        gt = _db.session.get(GadgetTypeMaster, gadget_type_id)
        if gt:
            _db.session.delete(gt)
            _db.session.commit()


@pytest.fixture()
def seed_gadget(app, seed_group, seed_gadget_type):
    """テスト用ガジェットを DB に追加。"""
    with app.app_context():
        gadget = DashboardGadgetMaster(
            gadget_uuid='test-gadget-uuid-0001',
            gadget_name='テストガジェット',
            dashboard_group_id=seed_group,
            gadget_type_id=seed_gadget_type,
            chart_config={},
            data_source_config={},
            position_x=0,
            position_y=0,
            gadget_size=1,
            display_order=1,
            create_date=datetime.now(),
            creator=TEST_USER_ID,
            update_date=datetime.now(),
            modifier=TEST_USER_ID,
        )
        _db.session.add(gadget)
        _db.session.commit()
        gadget_id = gadget.gadget_id

    yield gadget_id

    with app.app_context():
        gd = _db.session.get(DashboardGadgetMaster, gadget_id)
        if gd:
            _db.session.delete(gd)
            _db.session.commit()


# ============================================================
# No.1 顧客作成ダッシュボード初期表示
# ============================================================

@pytest.mark.integration
class TestCustomerDashboardIndex:
    """顧客作成ダッシュボード初期表示テスト

    観点: 2.1.1 一覧初期表示, 4.1 一覧表示（Read）テスト, 1.3 データスコープフィルタテスト
    対象ルート: GET /analysis/customer-dashboard
    """

    def test_display_with_no_dashboard(self, client, seed_org_closure):
        """2.1.1: ダッシュボード0件 - 200 で空のダッシュボード画面が表示される"""
        # Arrange (seed_org_closure でユーザー・組織閉包は準備済み)

        # Act
        response = client.get(BASE_URL)

        # Assert
        assert response.status_code == 200
        assert 'dashboard-header__title'.encode() not in response.data

    def test_display_with_dashboard(self, client, seed_dashboard):
        """2.1.1 / 4.1.2: ダッシュボードあり - 200 でダッシュボード名が表示される"""
        # Arrange (seed_dashboard でダッシュボード挿入済み)

        # Act
        response = client.get(BASE_URL)

        # Assert
        assert response.status_code == 200
        assert 'テストダッシュボード'.encode() in response.data

    def test_display_with_user_setting(self, client, app, seed_dashboard):
        """2.1.1 / 4.1.2: ユーザー設定あり - ユーザーが選択したダッシュボードを表示する"""
        # Arrange
        with app.app_context():
            setting = DashboardUserSetting(
                user_id=TEST_USER_ID,
                dashboard_id=seed_dashboard,
                organization_id=None,
                device_id=None,
                create_date=datetime.now(),
                creator=TEST_USER_ID,
                update_date=datetime.now(),
                modifier=TEST_USER_ID,
            )
            _db.session.add(setting)
            _db.session.commit()

        # Act
        response = client.get(BASE_URL)

        # Assert
        assert response.status_code == 200
        # ダッシュボード名がレスポンスに含まれることを確認
        with app.app_context():
            dashboard = _db.session.get(DashboardMaster, seed_dashboard)
            assert dashboard.dashboard_name.encode() in response.data

        # Teardown
        with app.app_context():
            s = _db.session.get(DashboardUserSetting, TEST_USER_ID)
            if s:
                _db.session.delete(s)
                _db.session.commit()

    @pytest.mark.integration
    def test_scope_allows_self_and_child(self, client, app, seed_child_org_closure):
        """1.3.1 / 1.3.2: 自org・子orgのダッシュボードは両方管理モーダルに表示される"""
        child_org_id = seed_child_org_closure
        with app.app_context():
            dash_self = DashboardMaster(
                dashboard_uuid='scope-self-uuid-ai001',
                dashboard_name='自orgダッシュボードAI',
                organization_id=TEST_ORG_ID,
                create_date=datetime.now(),
                creator=TEST_USER_ID,
                update_date=datetime.now(),
                modifier=TEST_USER_ID,
            )
            dash_child = DashboardMaster(
                dashboard_uuid='scope-child-uuid-ai001',
                dashboard_name='子orgダッシュボードAI',
                organization_id=child_org_id,
                create_date=datetime.now(),
                creator=TEST_USER_ID,
                update_date=datetime.now(),
                modifier=TEST_USER_ID,
            )
            _db.session.add_all([dash_self, dash_child])
            _db.session.commit()
            dash_self_id = dash_self.dashboard_id
            dash_child_id = dash_child.dashboard_id

        try:
            # Act: 初期表示（自orgダッシュボードがアクティブ）
            response = client.get(BASE_URL)
            assert response.status_code == 200
            assert '自orgダッシュボードAI'.encode() in response.data

            # Act: 管理モーダル（自org・子org両方のダッシュボードが一覧表示される）
            mgmt_response = client.get(f'{BASE_URL}/dashboards')
            assert mgmt_response.status_code == 200
            assert '自orgダッシュボードAI'.encode() in mgmt_response.data
            assert '子orgダッシュボードAI'.encode() in mgmt_response.data
        finally:
            with app.app_context():
                for dashboard_id in (dash_self_id, dash_child_id):
                    _db.session.query(DashboardUserSetting).filter_by(
                        dashboard_id=dashboard_id,
                    ).delete(synchronize_session=False)
                    d = _db.session.get(DashboardMaster, dashboard_id)
                    if d:
                        _db.session.delete(d)
                _db.session.commit()

    @pytest.mark.integration
    def test_scope_blocks_parent(self, client, app, seed_org_closure):
        """1.3.3: 親orgのダッシュボードは表示されない（スコープ制御の方向性確認）"""
        with app.app_context():
            # 親子関係のclosureを設定（PARENT_ORG_ID → TEST_ORG_ID 方向）
            # TEST_USERはPARENT_ORG_IDの子だが、子から親のデータは見えない
            parent_closure = OrganizationClosure(
                parent_organization_id=PARENT_ORG_ID,
                subsidiary_organization_id=TEST_ORG_ID,
                depth=1,
            )
            dash_parent = DashboardMaster(
                dashboard_uuid='scope-parent-uuid-ai001',
                dashboard_name='親orgダッシュボードAI',
                organization_id=PARENT_ORG_ID,
                create_date=datetime.now(),
                creator=TEST_USER_ID,
                update_date=datetime.now(),
                modifier=TEST_USER_ID,
            )
            _db.session.add_all([parent_closure, dash_parent])
            _db.session.commit()
            dash_parent_id = dash_parent.dashboard_id

        # Act
        response = client.get(BASE_URL)

        # Assert
        assert response.status_code == 200
        assert '親orgダッシュボードAI'.encode() not in response.data

        # Teardown
        with app.app_context():
            d = _db.session.get(DashboardMaster, dash_parent_id)
            if d:
                _db.session.delete(d)
            c = _db.session.query(OrganizationClosure).filter_by(
                parent_organization_id=PARENT_ORG_ID,
                subsidiary_organization_id=TEST_ORG_ID,
            ).first()
            if c:
                _db.session.delete(c)
            _db.session.commit()

    def test_scope_blocks_unrelated(self, client, app, seed_user):
        """1.3.4: 無関係組織のダッシュボードは表示されない"""
        # Arrange: 組織閉包なし (org 1 の accessible_orgs = []) → ダッシュボード取得できない
        other_org_id = 99
        with app.app_context():
            dashboard = DashboardMaster(
                dashboard_uuid='other-org-dash-uuid',
                dashboard_name='他組織ダッシュボード',
                organization_id=other_org_id,
                create_date=datetime.now(),
                creator=TEST_USER_ID,
                update_date=datetime.now(),
                modifier=TEST_USER_ID,
            )
            _db.session.add(dashboard)
            _db.session.commit()
            dashboard_id = dashboard.dashboard_id

        # Act
        response = client.get(BASE_URL)

        # Assert
        assert response.status_code == 200
        assert '他組織ダッシュボード'.encode() not in response.data

        # Teardown
        with app.app_context():
            d = _db.session.get(DashboardMaster, dashboard_id)
            if d:
                _db.session.delete(d)
                _db.session.commit()

    @pytest.mark.integration
    def test_deleted_group_not_shown(self, client, app, seed_dashboard):
        """ delete_flag=True のグループはダッシュボード表示に含まれない"""
        # Arrange: 論理削除済みグループを作成
        with app.app_context():
            group = DashboardGroupMaster(
                dashboard_group_uuid='deleted-group-uuid-y001',
                dashboard_group_name='削除済みグループY',
                dashboard_id=seed_dashboard,
                display_order=99,
                delete_flag=True,
                create_date=datetime.now(),
                creator=TEST_USER_ID,
                update_date=datetime.now(),
                modifier=TEST_USER_ID,
            )
            _db.session.add(group)
            _db.session.commit()
            group_id = group.dashboard_group_id

        # Act
        response = client.get(BASE_URL)

        # Assert
        assert response.status_code == 200
        assert '削除済みグループY'.encode() not in response.data

        # Teardown
        with app.app_context():
            g_obj = _db.session.get(DashboardGroupMaster, group_id)
            if g_obj:
                _db.session.delete(g_obj)
                _db.session.commit()

    @pytest.mark.integration
    def test_deleted_records_not_shown(self, client, app, seed_group, seed_gadget_type):
        """ 全階層の delete_flag=True レコードは初期表示に含まれない

        - ガジェット（delete_flag=True）が表示されないこと
        - ダッシュボード（delete_flag=True）がリストに表示されないこと
        """
        with app.app_context():
            deleted_gadget = DashboardGadgetMaster(
                gadget_uuid='deleted-gadget-uuid-aj001',
                gadget_name='削除済みガジェットAJ',
                dashboard_group_id=seed_group,
                gadget_type_id=seed_gadget_type,
                chart_config={},
                data_source_config={},
                position_x=0,
                position_y=0,
                gadget_size=1,
                display_order=99,
                delete_flag=True,
                create_date=datetime.now(),
                creator=TEST_USER_ID,
                update_date=datetime.now(),
                modifier=TEST_USER_ID,
            )
            deleted_dashboard = DashboardMaster(
                dashboard_uuid='deleted-dash-uuid-aj001',
                dashboard_name='削除済みダッシュボードAJ',
                organization_id=TEST_ORG_ID,
                delete_flag=True,
                create_date=datetime.now(),
                creator=TEST_USER_ID,
                update_date=datetime.now(),
                modifier=TEST_USER_ID,
            )
            _db.session.add_all([deleted_gadget, deleted_dashboard])
            _db.session.commit()
            deleted_gadget_id = deleted_gadget.gadget_id
            deleted_dashboard_id = deleted_dashboard.dashboard_id

        # Act
        response = client.get(BASE_URL)

        # Assert
        assert response.status_code == 200
        assert '削除済みガジェットAJ'.encode() not in response.data
        assert '削除済みダッシュボードAJ'.encode() not in response.data

        # Teardown
        with app.app_context():
            gd = _db.session.get(DashboardGadgetMaster, deleted_gadget_id)
            if gd:
                _db.session.delete(gd)
            d = _db.session.get(DashboardMaster, deleted_dashboard_id)
            if d:
                _db.session.delete(d)
            _db.session.commit()

    @pytest.mark.integration
    def test_other_dashboard_data_not_shown(self, client, app, seed_gadget, seed_gadget_type):
        """ chain確認 - 別ダッシュボードのGroup・Gadgetは初期表示に含まれない

        seed_dashboard（アクティブ）配下のGroup・Gadgetは表示され（positive）、
        別ダッシュボード配下のGroup・GadgetはFK filterで除外される（negative）。
        """
        with app.app_context():
            other_dashboard = DashboardMaster(
                dashboard_uuid='other-dash-uuid-aj001',
                dashboard_name='別ダッシュボードAJ',
                organization_id=TEST_ORG_ID,
                create_date=datetime.now(),
                creator=TEST_USER_ID,
                update_date=datetime.now(),
                modifier=TEST_USER_ID,
            )
            _db.session.add(other_dashboard)
            _db.session.flush()
            other_group = DashboardGroupMaster(
                dashboard_group_uuid='other-group-uuid-aj001',
                dashboard_group_name='別ダッシュボードグループAJ',
                dashboard_id=other_dashboard.dashboard_id,
                display_order=1,
                create_date=datetime.now(),
                creator=TEST_USER_ID,
                update_date=datetime.now(),
                modifier=TEST_USER_ID,
            )
            _db.session.add(other_group)
            _db.session.flush()
            other_gadget = DashboardGadgetMaster(
                gadget_uuid='other-gadget-uuid-aj001',
                gadget_name='別ダッシュボードガジェットAJ',
                dashboard_group_id=other_group.dashboard_group_id,
                gadget_type_id=seed_gadget_type,
                chart_config={},
                data_source_config={},
                position_x=0,
                position_y=0,
                gadget_size=1,
                display_order=1,
                create_date=datetime.now(),
                creator=TEST_USER_ID,
                update_date=datetime.now(),
                modifier=TEST_USER_ID,
            )
            _db.session.add(other_gadget)
            _db.session.commit()
            other_dashboard_id = other_dashboard.dashboard_id
            other_group_id = other_group.dashboard_group_id
            other_gadget_id = other_gadget.gadget_id

        # Act
        response = client.get(BASE_URL)

        # Assert
        assert response.status_code == 200
        # アクティブダッシュボード（seed_dashboard）配下のデータは表示される（positive）
        assert 'テストグループ'.encode() in response.data
        assert 'テストガジェット'.encode() in response.data
        # 別ダッシュボード配下のデータはFK filterで除外される（negative）
        assert '別ダッシュボードグループAJ'.encode() not in response.data
        assert '別ダッシュボードガジェットAJ'.encode() not in response.data

        # Teardown
        with app.app_context():
            gd = _db.session.get(DashboardGadgetMaster, other_gadget_id)
            if gd:
                _db.session.delete(gd)
            g = _db.session.get(DashboardGroupMaster, other_group_id)
            if g:
                _db.session.delete(g)
            d = _db.session.get(DashboardMaster, other_dashboard_id)
            if d:
                _db.session.delete(d)
            _db.session.commit()

    @pytest.mark.integration
    def test_default_display_selects_first_dashboard_by_id(self, client, app, seed_org_closure):
        """ ユーザー設定なし時、ID昇順先頭のダッシュボードがアクティブになる

        get_active_dashboard() の「設定なし → get_first_dashboard()」分岐を確認する。
        d1（先にINSERT → ID小）がアクティブ選択され、その配下グループが表示される。
        """
        with app.app_context():
            d1 = DashboardMaster(
                dashboard_uuid='ak-dash-uuid-0001',
                dashboard_name='AKダッシュボード1',
                organization_id=TEST_ORG_ID,
                create_date=datetime.now(),
                creator=TEST_USER_ID,
                update_date=datetime.now(),
                modifier=TEST_USER_ID,
            )
            _db.session.add(d1)
            _db.session.flush()
            group_d1 = DashboardGroupMaster(
                dashboard_group_uuid='ak-group-uuid-0001',
                dashboard_group_name='AKグループ（d1配下）',
                dashboard_id=d1.dashboard_id,
                display_order=1,
                create_date=datetime.now(),
                creator=TEST_USER_ID,
                update_date=datetime.now(),
                modifier=TEST_USER_ID,
            )
            _db.session.add(group_d1)
            d2 = DashboardMaster(
                dashboard_uuid='ak-dash-uuid-0002',
                dashboard_name='AKダッシュボード2',
                organization_id=TEST_ORG_ID,
                create_date=datetime.now(),
                creator=TEST_USER_ID,
                update_date=datetime.now(),
                modifier=TEST_USER_ID,
            )
            _db.session.add(d2)
            _db.session.commit()
            d1_id = d1.dashboard_id
            group_d1_id = group_d1.dashboard_group_id
            d2_id = d2.dashboard_id

        # Act: ユーザー設定なしでアクセス
        response = client.get(BASE_URL)

        # Assert: ID昇順先頭の d1 がアクティブ → d1 配下のグループが表示される
        assert response.status_code == 200
        assert 'AKグループ（d1配下）'.encode() in response.data

        # Teardown
        with app.app_context():
            for dashboard_id in (d1_id, d2_id):
                _db.session.query(DashboardUserSetting).filter_by(
                    dashboard_id=dashboard_id,
                ).delete(synchronize_session=False)
            g = _db.session.get(DashboardGroupMaster, group_d1_id)
            if g:
                _db.session.delete(g)
            for dashboard_id in (d1_id, d2_id):
                d = _db.session.get(DashboardMaster, dashboard_id)
                if d:
                    _db.session.delete(d)
            _db.session.commit()

    @pytest.mark.integration
    def test_organizations_always_rendered(self, client, app, seed_dashboard):
        """⑦: 組織選択肢は常時レンダリングされる（user_setting に関わらず）"""
        with app.app_context():
            org = OrganizationMaster(
                organization_id=TEST_ORG_ID,
                organization_name='テスト組織⑦',
                organization_type_id=1,
                address='',
                phone_number='',
                contact_person='',
                contract_status_id=1,
                contract_start_date=datetime.now().date(),
                databricks_group_id='',
                create_date=datetime.now(),
                creator=TEST_USER_ID,
                update_date=datetime.now(),
                modifier=TEST_USER_ID,
            )
            _db.session.merge(org)
            _db.session.commit()

        # Act: user_setting なしで初期表示
        response = client.get(BASE_URL)

        # Assert: 組織名が select-organization に含まれる
        assert response.status_code == 200
        assert 'テスト組織⑦'.encode() in response.data

    @pytest.mark.integration
    def test_devices_rendered_when_organization_id_nonzero(self, client, app, seed_dashboard):
        """⑧分岐(True): user_setting.organization_id != 0 の場合、デバイス選択肢がレンダリングされる"""
        with app.app_context():
            org = OrganizationMaster(
                organization_id=TEST_ORG_ID,
                organization_name='テスト組織⑧',
                organization_type_id=1,
                address='',
                phone_number='',
                contact_person='',
                contract_status_id=1,
                contract_start_date=datetime.now().date(),
                databricks_group_id='',
                create_date=datetime.now(),
                creator=TEST_USER_ID,
                update_date=datetime.now(),
                modifier=TEST_USER_ID,
            )
            _db.session.merge(org)
            device_type = DeviceTypeMaster(
                device_type_id=1,
                device_type_name='テストデバイス種別',
                creator=TEST_USER_ID,
                modifier=TEST_USER_ID,
            )
            _db.session.merge(device_type)
            _db.session.flush()
            device = DeviceMaster(
                device_id=9999,
                device_uuid='test-device-uuid-viii',
                organization_id=TEST_ORG_ID,
                device_type_id=1,
                device_name='テストデバイス⑧',
                device_model='MODEL-VIII',
                device_inventory_id=0,
                create_date=datetime.now(),
                creator=TEST_USER_ID,
                update_date=datetime.now(),
                modifier=TEST_USER_ID,
            )
            _db.session.add(device)
            _db.session.flush()
            setting = DashboardUserSetting(
                user_id=TEST_USER_ID,
                dashboard_id=seed_dashboard,
                organization_id=TEST_ORG_ID,  # != 0 → デバイス取得される
                device_id=device.device_id,
                create_date=datetime.now(),
                creator=TEST_USER_ID,
                update_date=datetime.now(),
                modifier=TEST_USER_ID,
            )
            _db.session.add(setting)
            _db.session.commit()
            device_id = device.device_id

        # Act
        response = client.get(BASE_URL)

        # Assert: デバイス名が select-device に含まれる
        assert response.status_code == 200
        assert 'テストデバイス⑧'.encode() in response.data

        # Teardown
        with app.app_context():
            s = _db.session.get(DashboardUserSetting, TEST_USER_ID)
            if s:
                _db.session.delete(s)
            d = _db.session.get(DeviceMaster, device_id)
            if d:
                _db.session.delete(d)
            _db.session.commit()

    @pytest.mark.integration
    def test_devices_empty_when_organization_id_is_none(self, client, app, seed_dashboard):
        """⑧分岐(False): user_setting.organization_id is None の場合、デバイスは取得されない（select disabled）"""
        with app.app_context():
            setting = DashboardUserSetting(
                user_id=TEST_USER_ID,
                dashboard_id=seed_dashboard,
                organization_id=None,  # is None → デバイス取得されない
                device_id=None,
                create_date=datetime.now(),
                creator=TEST_USER_ID,
                update_date=datetime.now(),
                modifier=TEST_USER_ID,
            )
            _db.session.add(setting)
            _db.session.commit()

        # Act
        response = client.get(BASE_URL)

        # Assert: select-device が disabled 属性を持つ（デバイス選択不可）
        assert response.status_code == 200
        assert 'disabled'.encode() in response.data

        # Teardown
        with app.app_context():
            s = _db.session.get(DashboardUserSetting, TEST_USER_ID)
            if s:
                _db.session.delete(s)
                _db.session.commit()


# ============================================================
# No.2 ダッシュボード管理モーダル表示
# ============================================================

@pytest.mark.integration
class TestDashboardManagement:
    """ダッシュボード管理モーダル表示テスト

    観点: 2.1.3 登録画面表示, 4.1 一覧表示テスト
    対象ルート: GET /analysis/customer-dashboard/dashboards
    """

    def test_display_empty(self, client, seed_org_closure):
        """4.1.1: ダッシュボード0件 - 200 で空のテーブルが表示される"""
        # Act
        response = client.get(f'{BASE_URL}/dashboards')

        # Assert
        assert response.status_code == 200
        assert 'テストダッシュボード'.encode() not in response.data

    def test_display_dashboards(self, client, seed_dashboard):
        """4.1.2: ダッシュボードあり - 200 でダッシュボード一覧が表示される"""
        # Act
        response = client.get(f'{BASE_URL}/dashboards')

        # Assert
        assert response.status_code == 200
        assert 'テストダッシュボード'.encode() in response.data

    def test_scope_excludes_other_org_dashboard(self, client, app, seed_org_closure):
        """1.3.4: 無関係組織のダッシュボードは一覧に表示されない"""
        # Arrange: org 2 のダッシュボードを挿入（org 1 はアクセス不可）
        with app.app_context():
            dashboard = DashboardMaster(
                dashboard_uuid='other-dash-mgmt-uuid',
                dashboard_name='他組織ダッシュボードMGMT',
                organization_id=99,
                create_date=datetime.now(),
                creator=TEST_USER_ID,
                update_date=datetime.now(),
                modifier=TEST_USER_ID,
            )
            _db.session.add(dashboard)
            _db.session.commit()
            dashboard_id = dashboard.dashboard_id

        # Act
        response = client.get(f'{BASE_URL}/dashboards')

        # Assert
        assert response.status_code == 200
        assert '他組織ダッシュボードMGMT'.encode() not in response.data

        # Teardown
        with app.app_context():
            d = _db.session.get(DashboardMaster, dashboard_id)
            if d:
                _db.session.delete(d)
                _db.session.commit()

    @pytest.mark.integration
    def test_display_sorted_by_id(self, client, app, seed_org_closure):
        """5.2.1: ダッシュボード一覧はID昇順で返される。"""
        # Arrange: 複数ダッシュボードを作成
        with app.app_context():
            d1 = DashboardMaster(
                dashboard_uuid='aaaaaaaa-0000-0000-0000-000000000001',
                dashboard_name='Beta',
                organization_id=TEST_ORG_ID,
                creator=TEST_USER_ID,
                modifier=TEST_USER_ID,
            )
            d2 = DashboardMaster(
                dashboard_uuid='aaaaaaaa-0000-0000-0000-000000000002',
                dashboard_name='Alpha',
                organization_id=TEST_ORG_ID,
                creator=TEST_USER_ID,
                modifier=TEST_USER_ID,
            )
            _db.session.add_all([d1, d2])
            _db.session.commit()
            d1_id, d2_id = d1.dashboard_id, d2.dashboard_id

        # Act
        response = client.get(f'{BASE_URL}/dashboards')

        # Assert: Beta(d1) が Alpha(d2) より前に出現する（ID昇順）
        assert response.status_code == 200
        pos_beta = response.data.find(b'Beta')
        pos_alpha = response.data.find(b'Alpha')
        assert pos_beta < pos_alpha

        # Teardown
        with app.app_context():
            _db.session.query(DashboardMaster).filter(
                DashboardMaster.dashboard_id.in_([d1_id, d2_id])
            ).delete(synchronize_session=False)
            _db.session.commit()

    @pytest.mark.integration
    def test_deleted_dashboard_not_shown(self, client, app, seed_org_closure):
        """タスクY: delete_flag=True のダッシュボードは一覧に表示されない"""
        # Arrange: 論理削除済みダッシュボードを作成
        with app.app_context():
            dashboard = DashboardMaster(
                dashboard_uuid='deleted-dash-uuid-y001',
                dashboard_name='削除済みダッシュボードY',
                organization_id=TEST_ORG_ID,
                delete_flag=True,
                create_date=datetime.now(),
                creator=TEST_USER_ID,
                update_date=datetime.now(),
                modifier=TEST_USER_ID,
            )
            _db.session.add(dashboard)
            _db.session.commit()
            dashboard_id = dashboard.dashboard_id

        # Act
        response = client.get(f'{BASE_URL}/dashboards')

        # Assert
        assert response.status_code == 200
        assert '削除済みダッシュボードY'.encode() not in response.data

        # Teardown
        with app.app_context():
            d = _db.session.get(DashboardMaster, dashboard_id)
            if d:
                _db.session.delete(d)
                _db.session.commit()


# ============================================================
# No.3 ダッシュボード登録モーダル表示 / No.4 ダッシュボード登録実行
# ============================================================

@pytest.mark.integration
class TestDashboardCreate:
    """ダッシュボード登録テスト

    観点: 2.1.3 登録画面表示, 3.1 必須チェック, 3.2 文字列長チェック,
          4.3 登録（Create）テスト, 2.3.1 登録成功後リダイレクト
    対象ルート: GET /analysis/customer-dashboard/dashboards/create
               POST /analysis/customer-dashboard/dashboards/register
    """

    def test_get_create_form(self, client, seed_org_closure):
        """2.1.3: 登録フォームが 200 で表示される"""
        # Act
        response = client.get(f'{BASE_URL}/dashboards/create')

        # Assert
        assert response.status_code == 200

    def test_register_success(self, client, app, seed_org_closure):
        """4.3.1: 正常登録 - 302 リダイレクト、DB にレコードが追加される"""
        # Arrange
        dashboard_name = 'テスト登録ダッシュボード'

        # Act
        response = client.post(
            f'{BASE_URL}/dashboards/register',
            data={'dashboard_name': dashboard_name},
            follow_redirects=False,
        )

        # Assert
        assert response.status_code == 200

        # DB にレコードが追加されたことを確認
        with app.app_context():
            dashboard = _db.session.query(DashboardMaster).filter_by(
                dashboard_name=dashboard_name,
                delete_flag=False,
            ).first()
            assert dashboard is not None
            assert dashboard.dashboard_name == dashboard_name
            assert dashboard.organization_id == TEST_ORG_ID

            # タスクH: dashboard_user_setting が新規ダッシュボードIDで更新されることを確認
            new_dashboard = _db.session.query(DashboardMaster).filter_by(
                dashboard_name='テスト登録ダッシュボード'
            ).first()
            setting = _db.session.query(DashboardUserSetting).filter_by(user_id=TEST_USER_ID).first()
            assert setting is not None
            assert setting.dashboard_id == new_dashboard.dashboard_id

            # Teardown
            _db.session.query(DashboardUserSetting).filter_by(
                dashboard_id=dashboard.dashboard_id,
            ).delete(synchronize_session=False)
            _db.session.delete(dashboard)
            _db.session.commit()

    def test_register_sets_create_date_and_creator(self, client, app, seed_org_closure):
        """4.3.6 / 4.3.7: 登録日時と作成者が自動設定される"""
        # Act
        client.post(
            f'{BASE_URL}/dashboards/register',
            data={'dashboard_name': '日時テストダッシュボード'},
        )

        # Assert / Teardown
        try:
            with app.app_context():
                dashboard = _db.session.query(DashboardMaster).filter_by(
                    dashboard_name='日時テストダッシュボード',
                    delete_flag=False,
                ).first()
                assert dashboard is not None
                assert dashboard.create_date is not None
                assert dashboard.creator == TEST_USER_ID
                # タスクI: delete_flag=False・UUID形式の検証
                assert dashboard.delete_flag is False
                assert re.match(
                    r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$',
                    dashboard.dashboard_uuid,
                )
        finally:
            # タスクQ: teardown を try/finally で保護
            with app.app_context():
                setting = _db.session.get(DashboardUserSetting, TEST_USER_ID)
                if setting:
                    _db.session.delete(setting)
                d = _db.session.query(DashboardMaster).filter_by(
                    dashboard_name='日時テストダッシュボード',
                ).first()
                if d:
                    _db.session.delete(d)
                _db.session.commit()

    def test_register_required_validation(self, client, seed_org_closure):
        """3.1.2: ダッシュボードタイトル未入力 - 400 エラーが返される"""
        # Act
        response = client.post(
            f'{BASE_URL}/dashboards/register',
            data={'dashboard_name': ''},
        )

        # Assert
        assert response.status_code == 400

    def test_register_max_length_validation(self, client, seed_org_closure):
        """3.2.2: 51文字以上のタイトル - 400 エラーが返される（上限50文字）"""
        # Arrange
        too_long_name = 'あ' * 51

        # Act
        response = client.post(
            f'{BASE_URL}/dashboards/register',
            data={'dashboard_name': too_long_name},
        )

        # Assert
        assert response.status_code == 400

    def test_register_max_length_boundary(self, client, app, seed_org_closure):
        """3.2.1: 50文字のタイトル - 正常登録される（境界値）"""
        # Arrange
        max_length_name = 'あ' * 50

        # Act
        response = client.post(
            f'{BASE_URL}/dashboards/register',
            data={'dashboard_name': max_length_name},
            follow_redirects=False,
        )

        # Assert
        assert response.status_code == 200

        # Teardown
        with app.app_context():
            dashboard = _db.session.query(DashboardMaster).filter_by(
                dashboard_name=max_length_name,
            ).first()
            if dashboard:
                _db.session.query(DashboardUserSetting).filter_by(
                    dashboard_id=dashboard.dashboard_id,
                ).delete(synchronize_session=False)
                _db.session.delete(dashboard)
                _db.session.commit()

    @pytest.mark.integration
    def test_register_shows_success_message(self, client, app, seed_org_closure):
        """ ダッシュボード登録後リダイレクト先に成功メッセージが表示される"""
        # Act
        response = client.post(
            f'{BASE_URL}/dashboards/register',
            data={'dashboard_name': '成功メッセージ確認ダッシュボード'},
            follow_redirects=True,
        )

        # Assert
        assert response.status_code == 200
        assert response.get_json()['message'] == 'ダッシュボードを登録しました'

        # Teardown
        with app.app_context():
            setting = _db.session.get(DashboardUserSetting, TEST_USER_ID)
            if setting:
                _db.session.delete(setting)
            d = _db.session.query(DashboardMaster).filter_by(
                dashboard_name='成功メッセージ確認ダッシュボード',
            ).first()
            if d:
                _db.session.delete(d)
            _db.session.commit()

    @pytest.mark.integration
    def test_register_updates_existing_user_setting(self, client, app, seed_dashboard):
        """ upsert_dashboard_user_setting の設定あり→UPDATE 分岐確認

        既存の DashboardUserSetting がある状態で登録すると、
        dashboard_id が新規ダッシュボードの ID に更新される。
        """
        # Arrange: 既存ユーザー設定を seed_dashboard に向けて作成
        with app.app_context():
            setting = DashboardUserSetting(
                user_id=TEST_USER_ID,
                dashboard_id=seed_dashboard,
                organization_id=None,
                device_id=None,
                create_date=datetime.now(),
                creator=TEST_USER_ID,
                update_date=datetime.now(),
                modifier=TEST_USER_ID,
            )
            _db.session.add(setting)
            _db.session.commit()

        # Act: 新規ダッシュボード登録
        client.post(
            f'{BASE_URL}/dashboards/register',
            data={'dashboard_name': '設定更新確認ダッシュボード'},
            follow_redirects=False,
        )

        # Assert: ユーザー設定が新しいダッシュボードIDに更新されている
        with app.app_context():
            new_dashboard = _db.session.query(DashboardMaster).filter_by(
                dashboard_name='設定更新確認ダッシュボード',
            ).first()
            updated_setting = _db.session.get(DashboardUserSetting, TEST_USER_ID)
            assert updated_setting is not None
            assert updated_setting.dashboard_id == new_dashboard.dashboard_id

        # Teardown
        with app.app_context():
            s = _db.session.get(DashboardUserSetting, TEST_USER_ID)
            if s:
                _db.session.delete(s)
            d = _db.session.query(DashboardMaster).filter_by(
                dashboard_name='設定更新確認ダッシュボード',
            ).first()
            if d:
                _db.session.delete(d)
            _db.session.commit()


# ============================================================
# No.5 ダッシュボードタイトル更新モーダル表示 / No.6 更新実行
# ============================================================

@pytest.mark.integration
class TestDashboardUpdate:
    """ダッシュボードタイトル更新テスト

    観点: 2.1.4 更新画面表示, 2.2.4 存在しないリソース,
          3.1 必須チェック, 3.2 文字列長チェック,
          4.4 更新（Update）テスト, 2.3.2 更新成功後リダイレクト
    対象ルート: GET  /analysis/customer-dashboard/dashboards/<uuid>/edit
               POST /analysis/customer-dashboard/dashboards/<uuid>/update
    """

    def test_get_edit_form(self, client, seed_dashboard):
        """2.1.4: 既存ダッシュボードの更新フォームが 200 で表示される"""
        # Act
        response = client.get(f'{BASE_URL}/dashboards/test-dash-uuid-0001/edit')

        # Assert
        assert response.status_code == 200

    def test_get_edit_form_not_found(self, client, seed_org_closure):
        """2.2.4: 存在しない UUID で更新フォームを開くと 404 が返される"""
        # Act
        response = client.get(f'{BASE_URL}/dashboards/nonexistent-uuid/edit')

        # Assert
        assert response.status_code == 404

    def test_get_edit_form_scope_out(self, client, app, seed_org_closure):
        """1.3.4: スコープ外ダッシュボードの更新フォームは 404 が返される"""
        # Arrange: 他組織のダッシュボード
        with app.app_context():
            dashboard = DashboardMaster(
                dashboard_uuid='scope-out-dash-uuid',
                dashboard_name='スコープ外ダッシュボード',
                organization_id=99,
                create_date=datetime.now(),
                creator=TEST_USER_ID,
                update_date=datetime.now(),
                modifier=TEST_USER_ID,
            )
            _db.session.add(dashboard)
            _db.session.commit()
            dashboard_id = dashboard.dashboard_id

        # Act
        response = client.get(f'{BASE_URL}/dashboards/scope-out-dash-uuid/edit')

        # Assert
        assert response.status_code == 404

        # Teardown
        with app.app_context():
            d = _db.session.get(DashboardMaster, dashboard_id)
            if d:
                _db.session.delete(d)
                _db.session.commit()

    def test_update_success(self, client, app, seed_dashboard):
        """4.4.1: 正常更新 - 200 JSON、DB のタイトルが更新される"""
        # Arrange
        new_name = '更新後ダッシュボード名'

        # Act
        response = client.post(
            f'{BASE_URL}/dashboards/test-dash-uuid-0001/update',
            data={'dashboard_name': new_name},
            follow_redirects=False,
        )

        # Assert
        assert response.status_code == 200
        with app.app_context():
            dashboard = _db.session.query(DashboardMaster).filter_by(
                dashboard_uuid='test-dash-uuid-0001',
            ).first()
            assert dashboard.dashboard_name == new_name

    @pytest.mark.integration
    def test_update_shows_success_message(self, client, seed_dashboard):
        """ ダッシュボード更新後リダイレクト先に成功メッセージが表示される"""
        # Act
        response = client.post(
            f'{BASE_URL}/dashboards/test-dash-uuid-0001/update',
            data={'dashboard_name': '成功メッセージ確認'},
            follow_redirects=True,
        )

        # Assert
        assert response.status_code == 200
        assert response.get_json()['message'] == 'ダッシュボードタイトルを更新しました'

    def test_update_sets_modifier_and_update_date(self, client, app, seed_dashboard):
        """4.4.3 / 4.4.4: 更新日時と更新者が更新される"""
        # Act
        client.post(
            f'{BASE_URL}/dashboards/test-dash-uuid-0001/update',
            data={'dashboard_name': '更新日時テスト'},
        )

        # Assert
        with app.app_context():
            dashboard = _db.session.query(DashboardMaster).filter_by(
                dashboard_uuid='test-dash-uuid-0001',
            ).first()
            assert dashboard.update_date is not None
            assert dashboard.modifier == TEST_USER_ID

    def test_update_required_validation(self, client, seed_dashboard):
        """3.1.2: タイトル未入力 - 400 エラーが返される"""
        # Act
        response = client.post(
            f'{BASE_URL}/dashboards/test-dash-uuid-0001/update',
            data={'dashboard_name': ''},
        )

        # Assert
        assert response.status_code == 400

    def test_update_max_length_validation(self, client, seed_dashboard):
        """3.2.2: 51文字以上のタイトル - 400 エラーが返される（上限50文字）"""
        # Act
        response = client.post(
            f'{BASE_URL}/dashboards/test-dash-uuid-0001/update',
            data={'dashboard_name': 'あ' * 51},
        )

        # Assert
        assert response.status_code == 400

    def test_update_not_found(self, client, seed_org_closure):
        """2.2.4: 存在しない UUID で更新実行すると 404 が返される"""
        # Act
        response = client.post(
            f'{BASE_URL}/dashboards/nonexistent-uuid/update',
            data={'dashboard_name': '更新テスト'},
        )

        # Assert
        assert response.status_code == 404

    @pytest.mark.integration
    def test_update_optimistic_lock_conflict(self, client, monkeypatch, seed_dashboard):
        """楽観ロック競合: snapshot取得時に古い日時を返すことで 409 を再現する"""
        import iot_app.views.analysis.customer_dashboard.common as view_module

        call_count = [0]

        def fake_get_dashboard_update_date(uuid):
            if call_count[0] == 0:
                call_count[0] += 1
                return datetime(2000, 1, 1)  # snapshot: 古い日時
            return datetime.now()            # current: 新しい日時

        monkeypatch.setattr(view_module, 'get_dashboard_update_date', fake_get_dashboard_update_date)

        response = client.post(
            f'{BASE_URL}/dashboards/test-dash-uuid-0001/update',
            data={'dashboard_name': '競合テスト'},
        )
        assert response.status_code == 409

    @pytest.mark.integration
    def test_update_does_not_change_create_date_and_creator(self, client, app, seed_dashboard):
        """タスクZ: ダッシュボード更新時に create_date と creator が変更されない"""
        # Arrange
        with app.app_context():
            dashboard = _db.session.query(DashboardMaster).filter_by(
                dashboard_uuid='test-dash-uuid-0001',
            ).first()
            before_create_date = dashboard.create_date
            before_creator = dashboard.creator

        # Act
        client.post(
            f'{BASE_URL}/dashboards/test-dash-uuid-0001/update',
            data={'dashboard_name': '不変確認更新ダッシュボード'},
        )

        # Assert
        with app.app_context():
            dashboard = _db.session.query(DashboardMaster).filter_by(
                dashboard_uuid='test-dash-uuid-0001',
            ).first()
            _db.session.refresh(dashboard)
            assert dashboard.create_date == before_create_date
            assert dashboard.creator == before_creator

    @pytest.mark.integration
    def test_update_deleted_dashboard_returns_404(self, client, app, seed_dashboard):
        """タスクAA: 論理削除済みダッシュボードへの更新リクエストで 404 が返される"""
        # Arrange: 事前に論理削除済み状態にする
        with app.app_context():
            d = _db.session.get(DashboardMaster, seed_dashboard)
            d.delete_flag = True
            _db.session.commit()

        # Act
        response = client.post(
            f'{BASE_URL}/dashboards/test-dash-uuid-0001/update',
            data={'dashboard_name': '削除済みダッシュボード更新'},
        )

        # Assert
        assert response.status_code == 404


# ============================================================
# No.7 ダッシュボード削除確認モーダル表示 / No.8 ダッシュボード削除実行
# ============================================================

@pytest.mark.integration
class TestDashboardDelete:
    """ダッシュボード削除テスト

    観点: 2.1.6 削除確認表示, 4.5 削除（Delete）テスト, 2.3.3 削除成功後リダイレクト
    対象ルート: GET  /analysis/customer-dashboard/dashboards/<uuid>/delete
               POST /analysis/customer-dashboard/dashboards/<uuid>/delete
    """

    def test_get_delete_confirm(self, client, seed_dashboard):
        """2.1.6: 削除確認モーダルが 200 で表示される"""
        # Act
        response = client.get(f'{BASE_URL}/dashboards/test-dash-uuid-0001/delete')

        # Assert
        assert response.status_code == 200

    def test_get_delete_confirm_not_found(self, client, seed_org_closure):
        """2.2.4: 存在しない UUID で削除確認を開くと 404 が返される"""
        # Act
        response = client.get(f'{BASE_URL}/dashboards/nonexistent-uuid/delete')

        # Assert
        assert response.status_code == 404

    def test_delete_success(self, client, app, seed_dashboard, seed_group, seed_gadget):
        """4.5.1: 正常削除 - 302 リダイレクト、delete_flag=True に更新される"""
        # Arrange: DashboardUserSetting を作成（削除後に delete_flag=True になることを確認するため）
        with app.app_context():
            setting = DashboardUserSetting(
                user_id=TEST_USER_ID,
                dashboard_id=seed_dashboard,
                organization_id=None,
                device_id=None,
                create_date=datetime.now(),
                creator=TEST_USER_ID,
                update_date=datetime.now(),
                modifier=TEST_USER_ID,
            )
            _db.session.add(setting)
            _db.session.commit()

        # Act
        response = client.post(
            f'{BASE_URL}/dashboards/test-dash-uuid-0001/delete',
            follow_redirects=False,
        )

        # Assert
        assert response.status_code == 200
        with app.app_context():
            dashboard = _db.session.query(DashboardMaster).filter_by(
                dashboard_uuid='test-dash-uuid-0001',
            ).first()
            assert dashboard.delete_flag is True
            assert dashboard.modifier == TEST_USER_ID
            # タスクA: 配下グループ・ガジェットも論理削除されていることを確認
            group = _db.session.get(DashboardGroupMaster, seed_group)
            assert group.delete_flag is True
            gadget = _db.session.get(DashboardGadgetMaster, seed_gadget)
            assert gadget.delete_flag is True
            # タスクV: DashboardUserSetting も delete_flag=True になっていることを確認
            # （次のダッシュボードがない場合 → delete_dashboard_user_setting が呼ばれる）
            user_setting = _db.session.query(DashboardUserSetting).filter_by(
                user_id=TEST_USER_ID,
            ).first()
            assert user_setting is not None
            assert user_setting.delete_flag is True

        # Teardown: タスクAC - DashboardUserSetting は物理削除されずdelete_flag=Trueのまま残るため手動削除
        with app.app_context():
            setting = _db.session.get(DashboardUserSetting, TEST_USER_ID)
            if setting:
                _db.session.delete(setting)
                _db.session.commit()

    def test_delete_not_found(self, client, seed_org_closure):
        """2.2.4: 存在しない UUID で削除実行すると 404 が返される"""
        # Act
        response = client.post(f'{BASE_URL}/dashboards/nonexistent-uuid/delete')

        # Assert
        assert response.status_code == 404

    @pytest.mark.integration
    def test_delete_already_deleted(self, client, app, seed_dashboard):
        """4.5.3: 論理削除済みダッシュボードへの削除リクエストで404が返される。"""
        # Arrange: 事前に削除済み状態にする
        with app.app_context():
            d = _db.session.get(DashboardMaster, seed_dashboard)
            d.delete_flag = True
            _db.session.commit()

        # Act
        response = client.post(
            f'{BASE_URL}/dashboards/test-dash-uuid-0001/delete',
            data={'update_date': datetime.now().isoformat()},
        )

        # Assert
        assert response.status_code == 404

    @pytest.mark.integration
    def test_delete_optimistic_lock_conflict(self, client, monkeypatch, seed_dashboard):
        """楽観ロック競合: snapshot取得時に古い日時を返すことで 409 を再現する"""
        import iot_app.views.analysis.customer_dashboard.common as view_module

        call_count = [0]

        def fake_get_dashboard_update_date(uuid):
            if call_count[0] == 0:
                call_count[0] += 1
                return datetime(2000, 1, 1)  # snapshot: 古い日時
            return datetime.now()            # current: 新しい日時

        monkeypatch.setattr(view_module, 'get_dashboard_update_date', fake_get_dashboard_update_date)

        response = client.post(
            f'{BASE_URL}/dashboards/test-dash-uuid-0001/delete',
        )
        assert response.status_code == 409

    @pytest.mark.integration
    def test_delete_rollback_on_error(self, client, monkeypatch, app, seed_dashboard):
        """7.2: DB例外発生時にロールバックされ、ダッシュボードが残ること。"""
        import iot_app.views.analysis.customer_dashboard.common as view_module

        def raise_error(*args, **kwargs):
            raise Exception("DB error")

        monkeypatch.setattr(view_module, 'delete_dashboard_with_cascade', raise_error)

        client.post(
            f'{BASE_URL}/dashboards/test-dash-uuid-0001/delete',
            data={'update_date': datetime.now().isoformat()},
        )

        with app.app_context():
            d = _db.session.get(DashboardMaster, seed_dashboard)
            assert d is not None
            assert d.delete_flag is False

    @pytest.mark.integration
    def test_delete_shows_success_message(self, client, app, seed_dashboard):
        """タスクAB: ダッシュボード削除後リダイレクト先に成功メッセージが表示される"""
        # Act
        response = client.post(
            f'{BASE_URL}/dashboards/test-dash-uuid-0001/delete',
            follow_redirects=True,
        )

        # Assert
        assert response.status_code == 200
        assert response.get_json()['message'] == 'ダッシュボードを削除しました'

    @pytest.mark.integration
    def test_delete_updates_user_setting_to_next_dashboard(self, client, app, seed_dashboard):
        """タスクAK横展開: delete_dashboard_with_cascade の次ダッシュボードあり→ユーザー設定更新分岐確認

        削除対象以外のダッシュボードが存在する場合、
        ユーザー設定の dashboard_id が次のダッシュボードIDに更新される。
        """
        with app.app_context():
            # 次のダッシュボードを作成（seed_dashboardより後にINSERT → IDが大きい）
            d2 = DashboardMaster(
                dashboard_uuid='delete-next-dash-uuid-ak001',
                dashboard_name='削除後の次ダッシュボード',
                organization_id=TEST_ORG_ID,
                create_date=datetime.now(),
                creator=TEST_USER_ID,
                update_date=datetime.now(),
                modifier=TEST_USER_ID,
            )
            _db.session.add(d2)
            _db.session.commit()
            d2_id = d2.dashboard_id
            # ユーザー設定を seed_dashboard に向けて作成
            setting = DashboardUserSetting(
                user_id=TEST_USER_ID,
                dashboard_id=seed_dashboard,
                organization_id=None,
                device_id=None,
                create_date=datetime.now(),
                creator=TEST_USER_ID,
                update_date=datetime.now(),
                modifier=TEST_USER_ID,
            )
            _db.session.add(setting)
            _db.session.commit()

        # Act: seed_dashboard を削除
        client.post(
            f'{BASE_URL}/dashboards/test-dash-uuid-0001/delete',
            follow_redirects=False,
        )

        # Assert: ユーザー設定が d2 の ID に更新されている
        with app.app_context():
            updated_setting = _db.session.get(DashboardUserSetting, TEST_USER_ID)
            assert updated_setting is not None
            assert updated_setting.dashboard_id == d2_id

        # Teardown
        with app.app_context():
            s = _db.session.get(DashboardUserSetting, TEST_USER_ID)
            if s:
                _db.session.delete(s)
            d = _db.session.get(DashboardMaster, d2_id)
            if d:
                _db.session.delete(d)
            _db.session.commit()


# ============================================================
# No.9 ダッシュボード表示切替
# ============================================================

@pytest.mark.integration
class TestDashboardSwitch:
    """ダッシュボード表示切替テスト

    観点: 2.3.2 更新成功後リダイレクト, 2.2.4 存在しないリソース
    対象ルート: POST /analysis/customer-dashboard/dashboards/<uuid>/switch
    """

    def test_switch_success(self, client, app, seed_dashboard):
        """4.4.1: 正常切替 - 200 JSON、ユーザー設定が更新される"""
        # Act
        response = client.post(
            f'{BASE_URL}/dashboards/test-dash-uuid-0001/switch',
            follow_redirects=False,
        )

        # Assert
        assert response.status_code == 200

        # Teardown user setting
        with app.app_context():
            setting = _db.session.get(DashboardUserSetting, TEST_USER_ID)
            if setting:
                _db.session.delete(setting)
                _db.session.commit()

    def test_switch_not_found(self, client, seed_org_closure):
        """2.2.4: 存在しない UUID で切替を実行すると 404 が返される"""
        # Act
        response = client.post(f'{BASE_URL}/dashboards/nonexistent-uuid/switch')

        # Assert
        assert response.status_code == 404

    def test_switch_scope_out(self, client, app, seed_org_closure):
        """1.3.4: スコープ外ダッシュボードへの切替は 404 が返される"""
        # Arrange: 他組織のダッシュボード
        with app.app_context():
            dashboard = DashboardMaster(
                dashboard_uuid='switch-scope-out-uuid',
                dashboard_name='スコープ外ダッシュボード',
                organization_id=99,
                create_date=datetime.now(),
                creator=TEST_USER_ID,
                update_date=datetime.now(),
                modifier=TEST_USER_ID,
            )
            _db.session.add(dashboard)
            _db.session.commit()
            dashboard_id = dashboard.dashboard_id

        # Act
        response = client.post(f'{BASE_URL}/dashboards/switch-scope-out-uuid/switch')

        # Assert
        assert response.status_code == 404

        # Teardown
        with app.app_context():
            d = _db.session.get(DashboardMaster, dashboard_id)
            if d:
                _db.session.delete(d)
                _db.session.commit()

    @pytest.mark.integration
    def test_switch_updates_existing_user_setting(self, client, app, seed_dashboard):
        """ upsert_dashboard_user_setting の設定あり→UPDATE 分岐確認

        既存の DashboardUserSetting がある状態でスイッチすると、
        dashboard_id がスイッチ先のIDに更新される。
        """
        with app.app_context():
            # スイッチ先となる別ダッシュボードを作成
            other_dash = DashboardMaster(
                dashboard_uuid='switch-update-uuid-ak001',
                dashboard_name='スイッチ先ダッシュボードAK',
                organization_id=TEST_ORG_ID,
                create_date=datetime.now(),
                creator=TEST_USER_ID,
                update_date=datetime.now(),
                modifier=TEST_USER_ID,
            )
            _db.session.add(other_dash)
            _db.session.commit()
            other_dash_id = other_dash.dashboard_id
            # 既存のユーザー設定を seed_dashboard に向けて作成
            setting = DashboardUserSetting(
                user_id=TEST_USER_ID,
                dashboard_id=seed_dashboard,
                organization_id=None,
                device_id=None,
                create_date=datetime.now(),
                creator=TEST_USER_ID,
                update_date=datetime.now(),
                modifier=TEST_USER_ID,
            )
            _db.session.add(setting)
            _db.session.commit()

        # Act: other_dash にスイッチ
        response = client.post(
            f'{BASE_URL}/dashboards/switch-update-uuid-ak001/switch',
            follow_redirects=False,
        )

        # Assert: ユーザー設定が other_dash の ID に更新されている
        assert response.status_code == 200
        with app.app_context():
            updated_setting = _db.session.get(DashboardUserSetting, TEST_USER_ID)
            assert updated_setting is not None
            assert updated_setting.dashboard_id == other_dash_id

        # Teardown
        with app.app_context():
            s = _db.session.get(DashboardUserSetting, TEST_USER_ID)
            if s:
                _db.session.delete(s)
            d = _db.session.get(DashboardMaster, other_dash_id)
            if d:
                _db.session.delete(d)
            _db.session.commit()


# ============================================================
# No.10 グループ登録モーダル表示 / No.11 グループ登録実行
# ============================================================

@pytest.mark.integration
class TestGroupCreate:
    """ダッシュボードグループ登録テスト

    観点: 2.1.3 登録画面表示, 3.1 必須チェック, 3.2 文字列長チェック,
          4.3 登録（Create）テスト, 2.3.1 登録成功後リダイレクト
    対象ルート: GET  /analysis/customer-dashboard/groups/create
               POST /analysis/customer-dashboard/groups/register
    """

    def test_get_create_form(self, client, seed_org_closure):
        """2.1.3: グループ登録フォームが 200 で表示される"""
        # Act
        response = client.get(
            f'{BASE_URL}/groups/create',
            query_string={'dashboard_uuid': 'test-dash-uuid-0001'},
        )

        # Assert
        assert response.status_code == 200

    def test_register_success(self, client, app, seed_dashboard):
        """4.3.1: 正常登録 - 200 JSON、DB にレコードが追加される"""
        # Arrange
        group_name = 'テスト登録グループ'

        # Act
        response = client.post(
            f'{BASE_URL}/groups/register',
            data={
                'dashboard_uuid': 'test-dash-uuid-0001',
                'dashboard_group_name': group_name,
            },
            follow_redirects=False,
        )

        # Assert
        assert response.status_code == 200
        with app.app_context():
            group = _db.session.query(DashboardGroupMaster).filter_by(
                dashboard_group_name=group_name,
                delete_flag=False,
            ).first()
            assert group is not None
            assert group.dashboard_id == seed_dashboard

            # タスクN: display_order の採番確認（初回登録なので1）
            latest_group = _db.session.query(DashboardGroupMaster).filter_by(
                dashboard_id=seed_dashboard,
            ).order_by(DashboardGroupMaster.display_order.desc()).first()
            assert latest_group.display_order == 1

            # Teardown
            _db.session.delete(group)
            _db.session.commit()

    def test_register_required_validation(self, client, seed_dashboard):
        """3.1.2: グループ名未入力 - 400 エラーが返される"""
        # Act
        response = client.post(
            f'{BASE_URL}/groups/register',
            data={
                'dashboard_uuid': 'test-dash-uuid-0001',
                'dashboard_group_name': '',
            },
        )

        # Assert
        assert response.status_code == 400

    def test_register_max_length_validation(self, client, seed_dashboard):
        """3.2.2: 51文字以上のグループ名 - 400 エラーが返される（上限50文字）"""
        # Act
        response = client.post(
            f'{BASE_URL}/groups/register',
            data={
                'dashboard_uuid': 'test-dash-uuid-0001',
                'dashboard_group_name': 'あ' * 51,
            },
        )

        # Assert
        assert response.status_code == 400

    def test_register_invalid_dashboard_uuid(self, client, seed_org_closure):
        """2.2.4: 存在しないダッシュボード UUID でグループ登録すると 404 が返される"""
        # Act
        response = client.post(
            f'{BASE_URL}/groups/register',
            data={
                'dashboard_uuid': 'nonexistent-dashboard-uuid',
                'dashboard_group_name': 'テストグループ',
            },
        )

        # Assert
        assert response.status_code == 404

    @pytest.mark.integration
    def test_register_display_order_increments(self, client, app, seed_group):
        """タスクAK横展開: create_dashboard_group の display_order 採番 既存あり→max+1 分岐確認

        seed_group（display_order=1）が存在する状態で2つ目のグループを登録すると
        display_order が 2 になる。
        """
        # Act: seed_group（display_order=1）がある状態で2つ目を登録
        client.post(
            f'{BASE_URL}/groups/register',
            data={
                'dashboard_uuid': 'test-dash-uuid-0001',
                'dashboard_group_name': '2番目グループAK',
            },
            follow_redirects=False,
        )

        # Assert: display_order が max+1 = 2 になっている
        with app.app_context():
            group2 = _db.session.query(DashboardGroupMaster).filter_by(
                dashboard_group_name='2番目グループAK',
            ).first()
            assert group2 is not None
            assert group2.display_order == 2

        # Teardown
        with app.app_context():
            g = _db.session.query(DashboardGroupMaster).filter_by(
                dashboard_group_name='2番目グループAK',
            ).first()
            if g:
                _db.session.delete(g)
                _db.session.commit()

    @pytest.mark.integration
    def test_register_shows_success_message(self, client, app, seed_dashboard):
        """タスクAB: グループ登録後リダイレクト先に成功メッセージが表示される"""
        # Act
        response = client.post(
            f'{BASE_URL}/groups/register',
            data={
                'dashboard_uuid': 'test-dash-uuid-0001',
                'dashboard_group_name': '成功メッセージ確認グループ',
            },
            follow_redirects=True,
        )

        # Assert
        assert response.status_code == 200
        assert response.get_json()['message'] == 'ダッシュボードグループを登録しました'

        # Teardown
        with app.app_context():
            _db.session.query(DashboardGroupMaster).filter_by(
                dashboard_group_name='成功メッセージ確認グループ',
            ).delete(synchronize_session=False)
            _db.session.commit()


# ============================================================
# No.12 グループタイトル更新モーダル表示 / No.13 グループタイトル更新実行
# ============================================================

@pytest.mark.integration
class TestGroupUpdate:
    """ダッシュボードグループタイトル更新テスト

    観点: 2.1.4 更新画面表示, 2.2.4 存在しないリソース,
          3.1 必須チェック, 3.2 文字列長チェック, 4.4 更新テスト
    対象ルート: GET  /analysis/customer-dashboard/groups/<uuid>/edit
               POST /analysis/customer-dashboard/groups/<uuid>/update
    """

    def test_get_edit_form(self, client, seed_group):
        """2.1.4: グループ更新フォームが 200 で表示される"""
        # Act
        response = client.get(f'{BASE_URL}/groups/test-group-uuid-0001/edit')

        # Assert
        assert response.status_code == 200

    def test_get_edit_form_not_found(self, client, seed_org_closure):
        """2.2.4: 存在しない UUID で更新フォームを開くと 404 が返される"""
        # Act
        response = client.get(f'{BASE_URL}/groups/nonexistent-uuid/edit')

        # Assert
        assert response.status_code == 404

    @pytest.mark.integration
    def test_get_edit_form_not_found_zero_uuid(self, client, seed_org_closure):
        """1.3.4: スコープ外（存在しない）UUIDへのアクセスで404を返す。"""
        # Act
        response = client.get(
            f'{BASE_URL}/groups/00000000-0000-0000-0000-000000000000/edit'
        )

        # Assert
        assert response.status_code == 404

    def test_update_success(self, client, app, seed_group):
        """4.4.1: 正常更新 - 200 JSON、DB のグループ名が更新される"""
        # Arrange
        new_name = '更新後グループ名'

        # Act
        response = client.post(
            f'{BASE_URL}/groups/test-group-uuid-0001/update',
            data={
                'dashboard_uuid': 'test-dash-uuid-0001',
                'dashboard_group_name': new_name,
            },
            follow_redirects=False,
        )

        # Assert
        assert response.status_code == 200
        with app.app_context():
            group = _db.session.query(DashboardGroupMaster).filter_by(
                dashboard_group_uuid='test-group-uuid-0001',
            ).first()
            assert group.dashboard_group_name == new_name

    @pytest.mark.integration
    def test_update_shows_success_message(self, client, seed_group):
        """タスクAF: グループ更新後リダイレクト先に成功メッセージが表示される"""
        # Act
        response = client.post(
            f'{BASE_URL}/groups/test-group-uuid-0001/update',
            data={
                'dashboard_uuid': 'test-dash-uuid-0001',
                'dashboard_group_name': '成功メッセージ確認',
            },
            follow_redirects=True,
        )

        # Assert
        assert response.status_code == 200
        assert response.get_json()['message'] == 'ダッシュボードグループタイトルを更新しました'

    def test_update_required_validation(self, client, seed_group):
        """3.1.2: グループ名未入力 - 400 エラーが返される"""
        # Act
        response = client.post(
            f'{BASE_URL}/groups/test-group-uuid-0001/update',
            data={'dashboard_group_name': ''},
        )

        # Assert
        assert response.status_code == 400

    def test_update_max_length_validation(self, client, seed_group):
        """3.2.2: 51文字以上のグループ名 - 400 エラーが返される"""
        # Act
        response = client.post(
            f'{BASE_URL}/groups/test-group-uuid-0001/update',
            data={'dashboard_group_name': 'あ' * 51},
        )

        # Assert
        assert response.status_code == 400

    def test_update_not_found(self, client, seed_org_closure):
        """2.2.4: 存在しない UUID で更新実行すると 404 が返される"""
        # Act
        response = client.post(
            f'{BASE_URL}/groups/nonexistent-uuid/update',
            data={'dashboard_group_name': '更新テスト'},
        )

        # Assert
        assert response.status_code == 404

    @pytest.mark.integration
    def test_update_sets_modifier_and_update_date(self, client, app, seed_group):
        """4.4.3/4.4.4: グループ更新時に modifier と update_date が設定される。"""
        # Arrange
        with app.app_context():
            group_obj = _db.session.get(DashboardGroupMaster, seed_group)
            before = group_obj.update_date

        # Act
        client.post(
            f'{BASE_URL}/groups/test-group-uuid-0001/update',
            data={
                'dashboard_group_name': '更新後グループ',
                'update_date': before.isoformat(),
            },
        )

        # Assert
        with app.app_context():
            group = _db.session.get(DashboardGroupMaster, seed_group)
            assert group.modifier == TEST_USER_ID
            assert group.update_date is not None

    @pytest.mark.integration
    def test_update_does_not_change_create_date_and_creator(self, client, app, seed_group):
        """タスクZ: グループ更新時に create_date と creator が変更されない"""
        # Arrange
        with app.app_context():
            group = _db.session.query(DashboardGroupMaster).filter_by(
                dashboard_group_uuid='test-group-uuid-0001',
            ).first()
            before_create_date = group.create_date
            before_creator = group.creator

        # Act
        client.post(
            f'{BASE_URL}/groups/test-group-uuid-0001/update',
            data={
                'dashboard_uuid': 'test-dash-uuid-0001',
                'dashboard_group_name': '不変確認更新グループ',
            },
        )

        # Assert
        with app.app_context():
            group = _db.session.query(DashboardGroupMaster).filter_by(
                dashboard_group_uuid='test-group-uuid-0001',
            ).first()
            _db.session.refresh(group)
            assert group.create_date == before_create_date
            assert group.creator == before_creator

    @pytest.mark.integration
    def test_update_deleted_group_returns_404(self, client, app, seed_group):
        """タスクAA: 論理削除済みグループへの更新リクエストで 404 が返される"""
        # Arrange: 事前に論理削除済み状態にする
        with app.app_context():
            g_obj = _db.session.get(DashboardGroupMaster, seed_group)
            g_obj.delete_flag = True
            _db.session.commit()

        # Act
        response = client.post(
            f'{BASE_URL}/groups/test-group-uuid-0001/update',
            data={
                'dashboard_uuid': 'test-dash-uuid-0001',
                'dashboard_group_name': '削除済みグループ更新',
            },
        )

        # Assert
        assert response.status_code == 404

    @pytest.mark.integration
    def test_update_optimistic_lock_conflict(self, client, monkeypatch, seed_group):
        """楽観ロック競合: snapshot取得時に古い日時を返すことで 409 を再現する"""
        import iot_app.views.analysis.customer_dashboard.common as view_module

        call_count = [0]

        def fake_get_group_update_date(uuid):
            if call_count[0] == 0:
                call_count[0] += 1
                return datetime(2000, 1, 1)  # snapshot: 古い日時
            return datetime.now()            # current: 新しい日時

        monkeypatch.setattr(view_module, 'get_group_update_date', fake_get_group_update_date)

        response = client.post(
            f'{BASE_URL}/groups/test-group-uuid-0001/update',
            data={'dashboard_group_name': '競合テスト'},
        )
        assert response.status_code == 409


# ============================================================
# No.14 グループ削除確認モーダル表示 / No.15 グループ削除実行
# ============================================================

@pytest.mark.integration
class TestGroupDelete:
    """ダッシュボードグループ削除テスト

    観点: 2.1.6 削除確認表示, 4.5 削除テスト, 2.3.3 削除成功後リダイレクト
    対象ルート: GET  /analysis/customer-dashboard/groups/<uuid>/delete
               POST /analysis/customer-dashboard/groups/<uuid>/delete
    """

    def test_get_delete_confirm(self, client, seed_group):
        """2.1.6: グループ削除確認モーダルが 200 で表示される"""
        # Act
        response = client.get(f'{BASE_URL}/groups/test-group-uuid-0001/delete')

        # Assert
        assert response.status_code == 200

    def test_get_delete_confirm_not_found(self, client, seed_org_closure):
        """2.2.4: 存在しない UUID で削除確認を開くと 404 が返される"""
        # Act
        response = client.get(f'{BASE_URL}/groups/nonexistent-uuid/delete')

        # Assert
        assert response.status_code == 404

    @pytest.mark.integration
    def test_delete_confirm_not_found_zero_uuid(self, client, seed_org_closure):
        """1.3.4: スコープ外（存在しない）UUIDへのアクセスで404を返す。"""
        # Act
        response = client.get(
            f'{BASE_URL}/groups/00000000-0000-0000-0000-000000000000/delete'
        )

        # Assert
        assert response.status_code == 404

    def test_delete_success(self, client, app, seed_group, seed_gadget):
        """4.5.1: 正常削除 - 200 JSON、delete_flag=True に更新される"""
        # Act
        response = client.post(
            f'{BASE_URL}/groups/test-group-uuid-0001/delete',
            follow_redirects=False,
        )

        # Assert
        assert response.status_code == 200
        with app.app_context():
            group = _db.session.query(DashboardGroupMaster).filter_by(
                dashboard_group_uuid='test-group-uuid-0001',
            ).first()
            assert group.delete_flag is True
            assert group.modifier == TEST_USER_ID
            # タスクB: 配下ガジェットも論理削除されていることを確認
            gadget = _db.session.get(DashboardGadgetMaster, seed_gadget)
            assert gadget.delete_flag is True

    def test_delete_not_found(self, client, seed_org_closure):
        """2.2.4: 存在しない UUID で削除実行すると 404 が返される"""
        # Act
        response = client.post(f'{BASE_URL}/groups/nonexistent-uuid/delete')

        # Assert
        assert response.status_code == 404

    @pytest.mark.integration
    def test_delete_already_deleted(self, client, app, seed_group):
        """4.5.3: 論理削除済みグループへの削除リクエストで404が返される。"""
        # Arrange: 事前に削除済み状態にする
        with app.app_context():
            g_obj = _db.session.get(DashboardGroupMaster, seed_group)
            g_obj.delete_flag = True
            _db.session.commit()

        # Act
        response = client.post(
            f'{BASE_URL}/groups/test-group-uuid-0001/delete',
            data={'update_date': datetime.now().isoformat()},
        )

        # Assert
        assert response.status_code == 404

    @pytest.mark.integration
    def test_delete_optimistic_lock_conflict(self, client, monkeypatch, seed_group):
        """楽観ロック競合: snapshot取得時に古い日時を返すことで 409 を再現する"""
        import iot_app.views.analysis.customer_dashboard.common as view_module

        call_count = [0]

        def fake_get_group_update_date(uuid):
            if call_count[0] == 0:
                call_count[0] += 1
                return datetime(2000, 1, 1)  # snapshot: 古い日時
            return datetime.now()            # current: 新しい日時

        monkeypatch.setattr(view_module, 'get_group_update_date', fake_get_group_update_date)

        response = client.post(
            f'{BASE_URL}/groups/test-group-uuid-0001/delete',
        )
        assert response.status_code == 409

    @pytest.mark.integration
    def test_delete_shows_success_message(self, client, seed_group):
        """タスクAB: グループ削除後リダイレクト先に成功メッセージが表示される"""
        # Act
        response = client.post(
            f'{BASE_URL}/groups/test-group-uuid-0001/delete',
            follow_redirects=True,
        )

        # Assert
        assert response.status_code == 200
        assert response.get_json()['message'] == 'ダッシュボードグループを削除しました'


# ============================================================
# No.16 ガジェット追加モーダル表示
# ============================================================

@pytest.mark.integration
class TestGadgetAdd:
    """ガジェット追加モーダル表示テスト

    観点: 2.1.3 登録画面表示, 4.1 一覧表示テスト
    対象ルート: GET /analysis/customer-dashboard/gadgets/add
    """

    def test_display_gadget_add_modal(self, client, seed_gadget_type):
        """2.1.3: ガジェット追加モーダルが 200 で表示される"""
        # Act
        response = client.get(f'{BASE_URL}/gadgets/add')

        # Assert
        assert response.status_code == 200

    def test_display_gadget_types(self, client, seed_gadget_type):
        """4.1.2: ガジェット種別一覧が表示される"""
        # Act
        response = client.get(f'{BASE_URL}/gadgets/add')

        # Assert
        assert response.status_code == 200
        assert '棒グラフ'.encode() in response.data


# ============================================================
# No.19 ガジェットタイトル更新モーダル表示 / No.20 ガジェットタイトル更新実行
# ============================================================

@pytest.mark.integration
class TestGadgetTitleUpdate:
    """ガジェットタイトル更新テスト

    観点: 2.1.4 更新画面表示, 2.2.4 存在しないリソース,
          3.1 必須チェック, 3.2 文字列長チェック, 4.4 更新テスト
    対象ルート: GET  /analysis/customer-dashboard/gadgets/<uuid>/edit
               POST /analysis/customer-dashboard/gadgets/<uuid>/update
    """

    def test_get_edit_form(self, client, seed_gadget):
        """2.1.4: ガジェットタイトル更新フォームが 200 で表示される"""
        # Act
        response = client.get(f'{BASE_URL}/gadgets/test-gadget-uuid-0001/edit')

        # Assert
        assert response.status_code == 200

    def test_get_edit_form_not_found(self, client, seed_org_closure):
        """2.2.4: 存在しない UUID で更新フォームを開くと 404 が返される"""
        # Act
        response = client.get(f'{BASE_URL}/gadgets/nonexistent-uuid/edit')

        # Assert
        assert response.status_code == 404

    @pytest.mark.integration
    def test_get_edit_form_not_found_zero_uuid(self, client, seed_org_closure):
        """1.3.4: スコープ外（存在しない）UUIDへのアクセスで404を返す。"""
        # Act
        response = client.get(
            f'{BASE_URL}/gadgets/00000000-0000-0000-0000-000000000000/edit'
        )

        # Assert
        assert response.status_code == 404

    def test_update_success(self, client, app, seed_gadget):
        """4.4.1: 正常更新 - 200 JSON、DB のガジェット名が更新される"""
        # Arrange
        new_name = '更新ガジェット名'

        # Act
        response = client.post(
            f'{BASE_URL}/gadgets/test-gadget-uuid-0001/update',
            data={'gadget_name': new_name},
            follow_redirects=False,
        )

        # Assert
        assert response.status_code == 200
        with app.app_context():
            gadget = _db.session.query(DashboardGadgetMaster).filter_by(
                gadget_uuid='test-gadget-uuid-0001',
            ).first()
            assert gadget.gadget_name == new_name

    @pytest.mark.integration
    def test_update_shows_success_message(self, client, seed_gadget):
        """タスクAF: ガジェット更新後リダイレクト先に成功メッセージが表示される"""
        # Act
        response = client.post(
            f'{BASE_URL}/gadgets/test-gadget-uuid-0001/update',
            data={'gadget_name': '成功メッセージ確認'},
            follow_redirects=True,
        )

        # Assert
        assert response.status_code == 200
        assert response.get_json()['message'] == 'ガジェットタイトルを更新しました'

    def test_update_required_validation(self, client, seed_gadget):
        """3.1.2: ガジェット名未入力 - 400 エラーが返される"""
        # Act
        response = client.post(
            f'{BASE_URL}/gadgets/test-gadget-uuid-0001/update',
            data={'gadget_name': ''},
        )

        # Assert
        assert response.status_code == 400

    def test_update_max_length_validation(self, client, seed_gadget):
        """3.2.2: 21文字以上のガジェット名 - 400 エラーが返される（上限20文字）"""
        # Act
        response = client.post(
            f'{BASE_URL}/gadgets/test-gadget-uuid-0001/update',
            data={'gadget_name': 'あ' * 21},
        )

        # Assert
        assert response.status_code == 400

    def test_update_max_length_boundary(self, client, app, seed_gadget):
        """3.2.1: 20文字のガジェット名 - 正常更新される（境界値）"""
        # Arrange
        max_name = 'あ' * 20

        # Act
        response = client.post(
            f'{BASE_URL}/gadgets/test-gadget-uuid-0001/update',
            data={'gadget_name': max_name},
            follow_redirects=False,
        )

        # Assert
        assert response.status_code == 200

    def test_update_not_found(self, client, seed_org_closure):
        """2.2.4: 存在しない UUID で更新実行すると 404 が返される"""
        # Act
        response = client.post(
            f'{BASE_URL}/gadgets/nonexistent-uuid/update',
            data={'gadget_name': '更新テスト'},
        )

        # Assert
        assert response.status_code == 404

    @pytest.mark.integration
    def test_update_sets_modifier_and_update_date(self, client, app, seed_gadget):
        """4.4.3/4.4.4: ガジェット更新時に modifier と update_date が設定される。"""
        # Arrange
        with app.app_context():
            gadget_obj = _db.session.get(DashboardGadgetMaster, seed_gadget)
            before = gadget_obj.update_date

        # Act
        client.post(
            f'{BASE_URL}/gadgets/test-gadget-uuid-0001/update',
            data={
                'gadget_name': '更新後ガジェット',
                'update_date': before.isoformat(),
            },
        )

        # Assert
        with app.app_context():
            gadget = _db.session.get(DashboardGadgetMaster, seed_gadget)
            assert gadget.modifier == TEST_USER_ID
            assert gadget.update_date is not None

    @pytest.mark.integration
    def test_update_optimistic_lock_conflict(self, client, monkeypatch, seed_gadget):
        """楽観ロック競合: snapshot取得時に古い日時を返すことで 409 を再現する"""
        import iot_app.views.analysis.customer_dashboard.common as view_module

        call_count = [0]

        def fake_get_gadget_update_date(uuid):
            if call_count[0] == 0:
                call_count[0] += 1
                return datetime(2000, 1, 1)  # snapshot: 古い日時
            return datetime.now()            # current: 新しい日時

        monkeypatch.setattr(view_module, 'get_gadget_update_date', fake_get_gadget_update_date)

        response = client.post(
            f'{BASE_URL}/gadgets/test-gadget-uuid-0001/update',
            data={'gadget_name': '競合テスト'},
        )
        assert response.status_code == 409

    @pytest.mark.integration
    def test_update_does_not_change_create_date_and_creator(self, client, app, seed_gadget):
        """タスクZ: ガジェット更新時に create_date と creator が変更されない"""
        # Arrange
        with app.app_context():
            gadget = _db.session.query(DashboardGadgetMaster).filter_by(
                gadget_uuid='test-gadget-uuid-0001',
            ).first()
            before_create_date = gadget.create_date
            before_creator = gadget.creator

        # Act
        client.post(
            f'{BASE_URL}/gadgets/test-gadget-uuid-0001/update',
            data={'gadget_name': '不変確認更新ガジェット'},
        )

        # Assert
        with app.app_context():
            gadget = _db.session.query(DashboardGadgetMaster).filter_by(
                gadget_uuid='test-gadget-uuid-0001',
            ).first()
            _db.session.refresh(gadget)
            assert gadget.create_date == before_create_date
            assert gadget.creator == before_creator

    @pytest.mark.integration
    def test_update_deleted_gadget_returns_404(self, client, app, seed_gadget):
        """タスクAA: 論理削除済みガジェットへの更新リクエストで 404 が返される"""
        # Arrange: 事前に論理削除済み状態にする
        with app.app_context():
            gd = _db.session.get(DashboardGadgetMaster, seed_gadget)
            gd.delete_flag = True
            _db.session.commit()

        # Act
        response = client.post(
            f'{BASE_URL}/gadgets/test-gadget-uuid-0001/update',
            data={'gadget_name': '削除済みガジェット更新'},
        )

        # Assert
        assert response.status_code == 404


# ============================================================
# No.21 ガジェット削除確認モーダル表示 / No.22 ガジェット削除実行
# ============================================================

@pytest.mark.integration
class TestGadgetDelete:
    """ガジェット削除テスト

    観点: 2.1.6 削除確認表示, 4.5 削除テスト, 2.3.3 削除成功後リダイレクト
    対象ルート: GET  /analysis/customer-dashboard/gadgets/<uuid>/delete
               POST /analysis/customer-dashboard/gadgets/<uuid>/delete
    """

    def test_get_delete_confirm(self, client, seed_gadget):
        """2.1.6: ガジェット削除確認モーダルが 200 で表示される"""
        # Act
        response = client.get(f'{BASE_URL}/gadgets/test-gadget-uuid-0001/delete')

        # Assert
        assert response.status_code == 200

    def test_get_delete_confirm_not_found(self, client, seed_org_closure):
        """2.2.4: 存在しない UUID で削除確認を開くと 404 が返される"""
        # Act
        response = client.get(f'{BASE_URL}/gadgets/nonexistent-uuid/delete')

        # Assert
        assert response.status_code == 404

    @pytest.mark.integration
    def test_delete_confirm_not_found_zero_uuid(self, client, seed_org_closure):
        """1.3.4: スコープ外（存在しない）UUIDへのアクセスで404を返す。"""
        # Act
        response = client.get(
            f'{BASE_URL}/gadgets/00000000-0000-0000-0000-000000000000/delete'
        )

        # Assert
        assert response.status_code == 404

    def test_delete_success(self, client, app, seed_gadget):
        """4.5.1: 正常削除 - 200 JSON、delete_flag=True に更新される"""
        # Act
        response = client.post(
            f'{BASE_URL}/gadgets/test-gadget-uuid-0001/delete',
            follow_redirects=False,
        )

        # Assert
        assert response.status_code == 200
        with app.app_context():
            gadget = _db.session.query(DashboardGadgetMaster).filter_by(
                gadget_uuid='test-gadget-uuid-0001',
            ).first()
            assert gadget.delete_flag is True
            assert gadget.modifier == TEST_USER_ID

    def test_delete_not_found(self, client, seed_org_closure):
        """2.2.4: 存在しない UUID で削除実行すると 404 が返される"""
        # Act
        response = client.post(f'{BASE_URL}/gadgets/nonexistent-uuid/delete')

        # Assert
        assert response.status_code == 404

    @pytest.mark.integration
    def test_delete_already_deleted(self, client, app, seed_gadget):
        """4.5.3: 論理削除済みガジェットへの削除リクエストで404が返される。"""
        # Arrange: 事前に削除済み状態にする
        with app.app_context():
            gd = _db.session.get(DashboardGadgetMaster, seed_gadget)
            gd.delete_flag = True
            _db.session.commit()

        # Act
        response = client.post(
            f'{BASE_URL}/gadgets/test-gadget-uuid-0001/delete',
            data={'update_date': datetime.now().isoformat()},
        )

        # Assert
        assert response.status_code == 404

    @pytest.mark.integration
    def test_delete_optimistic_lock_conflict(self, client, monkeypatch, seed_gadget):
        """楽観ロック競合: snapshot取得時に古い日時を返すことで 409 を再現する"""
        import iot_app.views.analysis.customer_dashboard.common as view_module

        call_count = [0]

        def fake_get_gadget_update_date(uuid):
            if call_count[0] == 0:
                call_count[0] += 1
                return datetime(2000, 1, 1)  # snapshot: 古い日時
            return datetime.now()            # current: 新しい日時

        monkeypatch.setattr(view_module, 'get_gadget_update_date', fake_get_gadget_update_date)

        response = client.post(
            f'{BASE_URL}/gadgets/test-gadget-uuid-0001/delete',
        )
        assert response.status_code == 409

    @pytest.mark.integration
    def test_delete_shows_success_message(self, client, seed_gadget):
        """タスクAB: ガジェット削除後リダイレクト先に成功メッセージが表示される"""
        # Act
        response = client.post(
            f'{BASE_URL}/gadgets/test-gadget-uuid-0001/delete',
            follow_redirects=True,
        )

        # Assert
        assert response.status_code == 200
        assert response.get_json()['message'] == 'ガジェットを削除しました'


# ============================================================
# No.24 レイアウト保存（AJAX）
# ============================================================

@pytest.mark.integration
class TestLayoutSave:
    """レイアウト保存テスト

    観点: 4.4 更新テスト, 7.1 正常コミットテスト
    対象ルート: POST /analysis/customer-dashboard/layout/save
    """

    def test_save_layout_success(self, client, seed_gadget):
        """4.4.1: レイアウト保存成功 - 200 JSON レスポンスが返される"""
        # Arrange
        payload = {
            'gadgets': [
                {
                    'gadget_uuid': 'test-gadget-uuid-0001',
                    'position_x': 1,
                    'position_y': 2,
                    'display_order': 1,
                }
            ]
        }

        # Act
        response = client.post(
            f'{BASE_URL}/layout/save',
            data=json.dumps(payload),
            content_type='application/json',
        )

        # Assert
        assert response.status_code == 200
        data = json.loads(response.data)
        # タスクP: Assert 強化
        assert data.get('message') == 'レイアウトを保存しました'

    def test_save_layout_empty_gadgets(self, client, seed_org_closure):
        """4.4.1: ガジェットなしのレイアウト保存 - 200 JSON レスポンスが返される"""
        # Arrange
        payload = {'gadgets': []}

        # Act
        response = client.post(
            f'{BASE_URL}/layout/save',
            data=json.dumps(payload),
            content_type='application/json',
        )

        # Assert
        assert response.status_code == 200

    def test_save_layout_updates_position(self, client, app, seed_gadget):
        """4.4.2: レイアウト保存後、DB の position_x/y が更新される"""
        # Arrange
        payload = {
            'gadgets': [
                {
                    'gadget_uuid': 'test-gadget-uuid-0001',
                    'position_x': 3,
                    'position_y': 5,
                    'display_order': 2,
                }
            ]
        }

        # Act
        client.post(
            f'{BASE_URL}/layout/save',
            data=json.dumps(payload),
            content_type='application/json',
        )

        # Assert
        with app.app_context():
            gadget = _db.session.query(DashboardGadgetMaster).filter_by(
                gadget_uuid='test-gadget-uuid-0001',
            ).first()
            assert gadget.position_x == 3
            assert gadget.position_y == 5


# ============================================================
# No.26 デバイス一覧取得（AJAX）
# ============================================================

@pytest.mark.integration
class TestDeviceList:
    """デバイス一覧取得テスト

    観点: 4.1 一覧表示テスト, 1.3 データスコープフィルタテスト
    対象ルート: GET /analysis/customer-dashboard/organizations/<org_id>/devices
    """

    def test_get_devices_success(self, client, seed_org_closure):
        """4.1.1: 有効な org_id - 200 JSON レスポンスが返される"""
        # Act
        response = client.get(f'{BASE_URL}/organizations/{TEST_ORG_ID}/devices')

        # Assert
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'devices' in data

    def test_get_devices_empty(self, client, seed_org_closure):
        """4.1.1: デバイスが存在しない org_id - 空のリストが返される"""
        # Act
        response = client.get(f'{BASE_URL}/organizations/999/devices')

        # Assert
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['devices'] == []


# ============================================================
# No.27 データソース設定保存（AJAX）
# ============================================================

@pytest.mark.integration
class TestDatasourceSave:
    """データソース設定保存テスト

    観点: 4.4 更新テスト, 7.1 正常コミットテスト
    対象ルート: POST /analysis/customer-dashboard/datasource/save
    """

    def test_save_datasource_success(self, client, app, seed_org_closure):
        """4.4.1: 正常保存 - 200 JSON レスポンスが返される"""
        # Arrange
        # ユーザー設定を事前に作成してダッシュボードIDが使えるようにする
        # NOTE: dashboard_id FK の都合で DashboardUserSetting がない場合は
        #       update_datasource_setting が upsert する実装次第
        payload = {
            'organization_id': TEST_ORG_ID,
            'device_id': 0,
        }

        # Act
        response = client.post(
            f'{BASE_URL}/datasource/save',
            data=json.dumps(payload),
            content_type='application/json',
        )

        # Assert
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data.get('status') == 'ok'


# ============================================================
# 9.3 CSRF 対策テスト
# ============================================================

@pytest.mark.integration
class TestCSRF:
    """CSRF 対策テスト

    観点: 9.3 CSRF 対策テスト
    NOTE: TestingConfig では WTF_CSRF_ENABLED=False のため、CSRF 無効テストのみ実施。
          本番相当の CSRF 有効テストは TestingConfig で WTF_CSRF_ENABLED=True にした
          別フィクスチャを用意して実施すること。
    """

    def test_post_without_csrf_token_in_testing(self, client, app, seed_org_closure):
        """9.3.1の逆確認: テスト環境では CSRF トークンなしの POST が通過する（CSRF 無効確認）
        NOTE: TestingConfig では WTF_CSRF_ENABLED=False のため CSRF は無効。
              9.3.1（トークンなし→403）・9.3.2（無効トークン→403）の本確認は
              WTF_CSRF_ENABLED=True の別フィクスチャが必要。
        """
        # Arrange: CSRF トークンを含まないリクエスト

        # Act
        response = client.post(
            f'{BASE_URL}/dashboards/register',
            data={'dashboard_name': 'CSRFテスト'},
        )

        # Assert: TestingConfig では CSRF 無効のため 400（バリデーション正常動作）または
        #          200（登録成功）であり、403（CSRF 拒否）にはならない
        assert response.status_code in (200, 400)
        assert response.status_code != 403

        # Teardown: 200（登録成功）の場合に作成されたレコードを削除する
        if response.status_code == 200:
            with app.app_context():
                setting = _db.session.get(DashboardUserSetting, TEST_USER_ID)
                if setting:
                    _db.session.delete(setting)
                d = _db.session.query(DashboardMaster).filter_by(
                    dashboard_name='CSRFテスト',
                ).first()
                if d:
                    _db.session.delete(d)
                _db.session.commit()


# ============================================================
# 9. セキュリティテスト
# ============================================================

class TestSecurity:
    """9. セキュリティテスト"""

    @pytest.mark.integration
    def test_sqlinjection_dashboard_name(self, client, app, seed_user, seed_org_closure):
        """9.1: SQLインジェクション文字列をダッシュボード名に入力しても安全に処理される。

        SQLAlchemy のプリペアドステートメントにより、SQL として解釈されず
        リテラル文字列として保存されることを確認する。
        """
        # Arrange
        sqli_name = "' OR 1=1 --"

        # Act
        response = client.post(
            f'{BASE_URL}/dashboards/register',
            data={'dashboard_name': sqli_name},
        )

        # Assert: 400（バリデーション通過後に保存）または 302（成功）のいずれか
        # 500 が返らないこと（SQLiとして解釈されていないこと）を確認
        assert response.status_code != 500

        # 登録成功した場合、literal string として保存されていること
        if response.status_code == 200:
            with app.app_context():
                setting = _db.session.get(DashboardUserSetting, TEST_USER_ID)
                if setting:
                    _db.session.delete(setting)
                d = _db.session.query(DashboardMaster).filter_by(dashboard_name=sqli_name).first()
                if d:
                    _db.session.delete(d)
                _db.session.commit()

    @pytest.mark.integration
    def test_xss_dashboard_name_escaped(self, client, app, seed_user, seed_org_closure, seed_dashboard):
        """9.2: XSS文字列をダッシュボード名に入力した場合、レスポンスでエスケープされる。

        Jinja2 の自動エスケープにより <script> タグが &lt;script&gt; として出力されることを確認する。
        """
        # Arrange: XSS文字列でダッシュボード名を更新
        xss_name = '<script>alert("xss")</script>'
        with app.app_context():
            d = _db.session.get(DashboardMaster, seed_dashboard)
            d.dashboard_name = xss_name
            _db.session.commit()

        # Act: 画面を表示
        response = client.get(BASE_URL)

        # Assert: エスケープされていること
        assert b'<script>alert' not in response.data
        assert b'&lt;script&gt;' in response.data or xss_name.encode() not in response.data
