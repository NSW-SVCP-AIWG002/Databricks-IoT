"""
顧客作成ダッシュボード共通機能 - 単体テスト
対象: src/iot_app/services/customer_dashboard/common.py
"""

import pytest
from unittest.mock import MagicMock, patch

MODULE = 'iot_app.services.customer_dashboard.common'


# ---------------------------------------------------------------------------
# get_organization_id_by_user
# ---------------------------------------------------------------------------

@pytest.mark.unit
class TestGetOrganizationIdByUser:
    """ユーザーIDから所属組織IDを取得する

    NOTE: get_accessible_organizations が不要になった際は呼び出し元ごと削除する。
    """

    @patch(f'{MODULE}.db')
    def test_returns_organization_id(self, mock_db):
        """ユーザーが存在する場合: organization_id を返す"""
        # Arrange
        mock_db.session.query.return_value.filter.return_value.scalar.return_value = 5
        from iot_app.services.customer_dashboard.common import get_organization_id_by_user

        # Act
        result = get_organization_id_by_user(1)

        # Assert
        assert result == 5

    @patch(f'{MODULE}.db')
    def test_returns_none_when_not_found(self, mock_db):
        """ユーザーが存在しない場合: None を返す"""
        # Arrange
        mock_db.session.query.return_value.filter.return_value.scalar.return_value = None
        from iot_app.services.customer_dashboard.common import get_organization_id_by_user

        # Act
        result = get_organization_id_by_user(999)

        # Assert
        assert result is None


# ---------------------------------------------------------------------------
# get_accessible_organizations
# ---------------------------------------------------------------------------

@pytest.mark.unit
class TestGetAccessibleOrganizations:
    """観点: 3.1.1（フィルタ条件）, 3.1.4（件数）

    使用ルート:
        GET  /analysis/customer-dashboard（初期表示）
        GET  /analysis/customer-dashboard/dashboards（管理モーダル）
        POST /analysis/customer-dashboard/dashboards/<uuid>/switch
        POST /analysis/customer-dashboard/dashboards/<uuid>/update
        POST /analysis/customer-dashboard/dashboards/<uuid>/delete
        POST /analysis/customer-dashboard/groups/register
        POST /analysis/customer-dashboard/groups/<uuid>/update
        POST /analysis/customer-dashboard/groups/<uuid>/delete
        POST /analysis/customer-dashboard/gadgets/<uuid>/update
        POST /analysis/customer-dashboard/gadgets/<uuid>/delete

    ワークフロー仕様書 § ダッシュボード初期表示 ② データスコープ制限の適用
    organization_closure テーブルから subsidiary_organization_id を取得する
    """

    @patch(f'{MODULE}.db')
    def test_returns_org_id_list(self, mock_db):
        """3.1.4.1 データあり: 下位組織IDリストを返す"""
        # Arrange
        mock_db.session.query.return_value.filter.return_value.all.return_value = [
            (10,), (20,), (30,)
        ]
        from iot_app.services.customer_dashboard.common import get_accessible_organizations

        # Act
        result = get_accessible_organizations(1)

        # Assert
        assert result == [10, 20, 30]

    @patch(f'{MODULE}.db')
    def test_returns_empty_list_when_no_children(self, mock_db):
        """3.1.4.2 データなし: 空リストを返す"""
        # Arrange
        mock_db.session.query.return_value.filter.return_value.all.return_value = []
        from iot_app.services.customer_dashboard.common import get_accessible_organizations

        # Act
        result = get_accessible_organizations(999)

        # Assert
        assert result == []

    @patch(f'{MODULE}.db')
    def test_filters_by_parent_organization_id(self, mock_db):
        """3.1.1.1 フィルタ条件: parent_organization_id で絞り込む"""
        # Arrange
        from iot_app.services.customer_dashboard.common import (
            get_accessible_organizations,
        )
        from iot_app.models.organization import OrganizationClosure

        mock_db.session.query.return_value.filter.return_value.all.return_value = [
            (5,)
        ]

        # Act
        get_accessible_organizations(3)

        # Assert
        mock_db.session.query.assert_called_once_with(OrganizationClosure.subsidiary_organization_id)
        filter_expr = mock_db.session.query.return_value.filter.call_args[0][0]
        assert filter_expr.left == OrganizationClosure.parent_organization_id
        assert filter_expr.right.value == 3


# ---------------------------------------------------------------------------
# get_dashboard_user_setting
# ---------------------------------------------------------------------------

@pytest.mark.unit
class TestGetDashboardUserSetting:
    """観点: 2.2.1（存在あり）, 2.2.2（存在なし）

    使用ルート:
        GET  /analysis/customer-dashboard（初期表示）

    ワークフロー仕様書 § ダッシュボード初期表示 ③ ダッシュボードユーザー設定取得
    user_id に一致する dashboard_user_setting レコードを返す
    """

    @patch(f'{MODULE}.db')
    def test_returns_setting_when_exists(self, mock_db):
        """2.2.1 ユーザー設定が存在する場合: レコードを返す"""
        # Arrange
        mock_setting = MagicMock()
        mock_setting.dashboard_id = 1
        mock_db.session.query.return_value.filter.return_value.first.return_value = mock_setting
        from iot_app.services.customer_dashboard.common import get_dashboard_user_setting

        # Act
        result = get_dashboard_user_setting(1)

        # Assert
        assert result is mock_setting

    @patch(f'{MODULE}.db')
    def test_returns_none_when_not_exists(self, mock_db):
        """2.2.2 ユーザー設定が存在しない場合: None を返す"""
        # Arrange
        mock_db.session.query.return_value.filter.return_value.first.return_value = None
        from iot_app.services.customer_dashboard.common import get_dashboard_user_setting

        # Act
        result = get_dashboard_user_setting(999)

        # Assert
        assert result is None


# ---------------------------------------------------------------------------
# get_dashboard_by_id
# ---------------------------------------------------------------------------

@pytest.mark.unit
class TestGetDashboardById:
    """観点: 2.2.1（存在あり）, 2.2.2（存在なし）

    使用ルート:
        GET  /analysis/customer-dashboard（初期表示）

    ワークフロー仕様書 § ダッシュボード初期表示 ④ ダッシュボード情報取得
    dashboard_id に一致する dashboard_master レコードを返す（PKルックアップ、スコープ制限なし）
    """

    @patch(f'{MODULE}.db')
    def test_returns_dashboard_when_found(self, mock_db):
        """2.2.1 dashboard_id に一致するレコードを返す"""
        # Arrange
        mock_dashboard = MagicMock()
        mock_dashboard.dashboard_id = 1
        mock_db.session.query.return_value.filter.return_value.first.return_value = mock_dashboard
        from iot_app.services.customer_dashboard.common import get_dashboard_by_id

        # Act
        result = get_dashboard_by_id(1)

        # Assert
        assert result is mock_dashboard

    @patch(f'{MODULE}.db')
    def test_returns_none_when_not_found(self, mock_db):
        """2.2.2 存在しない dashboard_id の場合: None を返す"""
        # Arrange
        mock_db.session.query.return_value.filter.return_value.first.return_value = None
        from iot_app.services.customer_dashboard.common import get_dashboard_by_id

        # Act
        result = get_dashboard_by_id(999)

        # Assert
        assert result is None


# ---------------------------------------------------------------------------
# upsert_dashboard_user_setting
# ---------------------------------------------------------------------------

@pytest.mark.unit
class TestUpsertDashboardUserSetting:
    """観点: 3.2.1.1（新規登録）, 3.3.1.1（更新）

    使用ルート:
        POST /analysis/customer-dashboard/dashboards/register（登録後のユーザー設定更新）
        POST /analysis/customer-dashboard/dashboards/<uuid>/switch（表示切替）
        POST /analysis/customer-dashboard/dashboards/<uuid>/delete（次ダッシュボードあり時）

    ワークフロー仕様書 § ダッシュボード登録 ② ユーザー設定更新
    INSERT ON DUPLICATE KEY UPDATE パターン（UPSERT）
    """

    @patch(f'{MODULE}.db')
    def test_inserts_when_no_existing_setting(self, mock_db):
        """3.2.1.1 ユーザー設定が存在しない場合: INSERTする"""
        # Arrange
        mock_db.session.query.return_value.filter.return_value.first.return_value = None
        from iot_app.services.customer_dashboard.common import upsert_dashboard_user_setting

        # Act
        upsert_dashboard_user_setting(1, 1)

        # Assert
        mock_db.session.add.assert_called_once()
        added_obj = mock_db.session.add.call_args[0][0]
        assert added_obj.dashboard_id == 1
        assert added_obj.organization_id is None
        assert added_obj.device_id is None
        assert added_obj.creator == 1
        assert added_obj.modifier == 1

    @patch(f'{MODULE}.db')
    def test_updates_when_existing_setting(self, mock_db):
        """3.3.1.1 ユーザー設定が存在する場合: dashboard_id を更新する"""
        # Arrange
        mock_setting = MagicMock()
        mock_setting.dashboard_id = 1
        mock_db.session.query.return_value.filter.return_value.first.return_value = mock_setting
        from iot_app.services.customer_dashboard.common import upsert_dashboard_user_setting

        # Act
        upsert_dashboard_user_setting(1, 99)

        # Assert
        assert mock_setting.dashboard_id == 99
        mock_db.session.add.assert_not_called()


# ---------------------------------------------------------------------------
# get_dashboards
# ---------------------------------------------------------------------------

@pytest.mark.unit
class TestGetDashboards:
    """観点: 3.1.1.1（フィルタ条件）, 3.1.4.1/3.1.4.2（件数）

    使用ルート:
        GET  /analysis/customer-dashboard（初期表示）
        GET  /analysis/customer-dashboard/dashboards（管理モーダル）

    ワークフロー仕様書 § ダッシュボード管理モーダル表示 ① ダッシュボード一覧取得
    accessible_org_ids でスコープ制限し dashboard_id 昇順に返す
    """

    @patch(f'{MODULE}.db')
    def test_returns_dashboards_in_accessible_scope(self, mock_db):
        """3.1.4.1 アクセス可能組織内のダッシュボードを返す"""
        # Arrange
        mock_dash1 = MagicMock()
        mock_dash2 = MagicMock()
        (
            mock_db.session.query.return_value
            .filter.return_value
            .order_by.return_value
            .all.return_value
        ) = [mock_dash1, mock_dash2]
        from iot_app.services.customer_dashboard.common import get_dashboards

        # Act
        result = get_dashboards([1, 2, 3])

        # Assert
        assert result == [mock_dash1, mock_dash2]

    @patch(f'{MODULE}.db')
    def test_returns_empty_when_no_dashboards(self, mock_db):
        """3.1.4.2 ダッシュボードなし: 空リストを返す"""
        # Arrange
        (
            mock_db.session.query.return_value
            .filter.return_value
            .order_by.return_value
            .all.return_value
        ) = []
        from iot_app.services.customer_dashboard.common import get_dashboards

        # Act
        result = get_dashboards([1])

        # Assert
        assert result == []

    @patch(f'{MODULE}.db')
    def test_returns_empty_when_accessible_org_ids_empty(self, mock_db):
        """3.1.1.1 accessible_org_ids が空: ダッシュボードなし"""
        # Arrange
        from iot_app.services.customer_dashboard.common import get_dashboards

        # Act
        result = get_dashboards([])

        # Assert
        assert result == []
        mock_db.session.query.assert_not_called()

    @patch(f'{MODULE}.db')
    def test_filters_by_accessible_org_ids(self, mock_db):
        """3.1.1.1 accessible_org_ids で organization_id を絞り込む"""
        # Arrange
        (
            mock_db.session.query.return_value
            .filter.return_value
            .order_by.return_value
            .all.return_value
        ) = []
        from iot_app.services.customer_dashboard.common import get_dashboards
        from iot_app.models.customer_dashboard import DashboardMaster

        # Act
        get_dashboards([1, 2])

        # Assert
        filter_args = mock_db.session.query.return_value.filter.call_args[0]
        in_expr = next(f for f in filter_args if hasattr(f, 'right') and getattr(f.right, 'expanding', False))
        assert in_expr.left == DashboardMaster.organization_id
        assert in_expr.right.value == [1, 2]


# ---------------------------------------------------------------------------
# get_first_dashboard
# ---------------------------------------------------------------------------

@pytest.mark.unit
class TestGetFirstDashboard:
    """観点: 3.1.4.1/3.1.4.2（件数）

    使用ルート:
        GET  /analysis/customer-dashboard（初期表示・ユーザー設定なし時）
        POST /analysis/customer-dashboard/dashboards/<uuid>/delete（削除後の次ダッシュボード取得）

    ワークフロー仕様書 § ダッシュボード初期表示 ④
    ユーザー設定なし時に dashboard_id 昇順の先頭ダッシュボードを返す
    """

    @patch(f'{MODULE}.db')
    def test_returns_first_dashboard_by_id_asc(self, mock_db):
        """3.1.4.1 データあり: 最初のダッシュボードを返す"""
        # Arrange
        mock_dash = MagicMock()
        (
            mock_db.session.query.return_value
            .filter.return_value
            .order_by.return_value
            .first.return_value
        ) = mock_dash
        from iot_app.services.customer_dashboard.common import get_first_dashboard

        # Act
        result = get_first_dashboard([1, 2])

        # Assert
        assert result is mock_dash

    @patch(f'{MODULE}.db')
    def test_returns_none_when_no_dashboard(self, mock_db):
        """3.1.4.2 データなし: None を返す"""
        # Arrange
        (
            mock_db.session.query.return_value
            .filter.return_value
            .order_by.return_value
            .first.return_value
        ) = None
        from iot_app.services.customer_dashboard.common import get_first_dashboard

        # Act
        result = get_first_dashboard([1])

        # Assert
        assert result is None

    @patch(f'{MODULE}.db')
    def test_excludes_specified_dashboard_id(self, mock_db):
        """3.1.1.1 exclude_id 指定時: 該当ダッシュボードを除外して取得する"""
        # Arrange
        mock_dash = MagicMock()
        (
            mock_db.session.query.return_value
            .filter.return_value
            .filter.return_value
            .order_by.return_value
            .first.return_value
        ) = mock_dash
        from iot_app.services.customer_dashboard.common import get_first_dashboard

        # Act
        result = get_first_dashboard([1, 2], exclude_id=3)

        # Assert
        assert result is mock_dash
        assert mock_db.session.query.return_value.filter.return_value.filter.called

    @patch(f'{MODULE}.db')
    def test_filters_by_accessible_org_ids(self, mock_db):
        """3.1.1.1 accessible_org_ids で organization_id を絞り込む"""
        # Arrange
        (
            mock_db.session.query.return_value
            .filter.return_value
            .order_by.return_value
            .first.return_value
        ) = None
        from iot_app.services.customer_dashboard.common import get_first_dashboard
        from iot_app.models.customer_dashboard import DashboardMaster

        # Act
        get_first_dashboard([1, 2])

        # Assert
        filter_args = mock_db.session.query.return_value.filter.call_args[0]
        in_expr = next(f for f in filter_args if hasattr(f, 'right') and getattr(f.right, 'expanding', False))
        assert in_expr.left == DashboardMaster.organization_id
        assert in_expr.right.value == [1, 2]


# ---------------------------------------------------------------------------
# get_active_dashboard
# ---------------------------------------------------------------------------

@pytest.mark.unit
class TestGetActiveDashboard:
    """観点: 2.2.1/2.2.2/2.2.3（ユーザー設定の有無・ダッシュボードの有無）

    使用ルート:
        GET  /analysis/customer-dashboard（初期表示）

    ワークフロー仕様書 § ダッシュボード初期表示 アクティブダッシュボード決定
    ユーザー設定あり→設定値を返す、なし→先頭ダッシュボードを返す、どちらもなし→None
    """

    @patch(f'{MODULE}.get_first_dashboard')
    def test_returns_dashboard_id_from_user_setting_when_exists(self, mock_get_first):
        """2.2.1 ユーザー設定にdashboard_idがある場合: 設定値を返す"""
        # Arrange
        mock_setting = MagicMock()
        mock_setting.dashboard_id = 5
        from iot_app.services.customer_dashboard.common import get_active_dashboard

        # Act
        result = get_active_dashboard(mock_setting, accessible_org_ids=[1, 2])

        # Assert
        assert result == 5
        mock_get_first.assert_not_called()

    @patch(f'{MODULE}.get_first_dashboard')
    def test_returns_first_dashboard_when_no_user_setting(self, mock_get_first):
        """2.2.2 ユーザー設定なし: 先頭ダッシュボードのIDを返す"""
        # Arrange
        mock_first = MagicMock()
        mock_first.dashboard_id = 3
        mock_get_first.return_value = mock_first
        from iot_app.services.customer_dashboard.common import get_active_dashboard

        # Act
        result = get_active_dashboard(None, accessible_org_ids=[1, 2])

        # Assert
        assert result == 3
        mock_get_first.assert_called_once_with([1, 2])

    @patch(f'{MODULE}.get_first_dashboard')
    def test_returns_none_when_no_dashboards_exist(self, mock_get_first):
        """2.2.3 ユーザー設定なし・ダッシュボードなし: None を返す"""
        # Arrange
        mock_get_first.return_value = None
        from iot_app.services.customer_dashboard.common import get_active_dashboard

        # Act
        result = get_active_dashboard(None, accessible_org_ids=[1, 2])

        # Assert
        assert result is None


# ---------------------------------------------------------------------------
# check_dashboard_access
# ---------------------------------------------------------------------------

@pytest.mark.unit
class TestCheckDashboardAccess:
    """観点: 2.2.1/2.2.2/2.2.3（存在チェック）, 1.2.1/1.2.2（スコープ制限）

    使用ルート:
        POST /analysis/customer-dashboard/dashboards/<uuid>/switch（スコープチェック）
        POST /analysis/customer-dashboard/dashboards/<uuid>/update（スコープチェック）
        POST /analysis/customer-dashboard/dashboards/<uuid>/delete（スコープチェック）
        POST /analysis/customer-dashboard/groups/register（スコープチェック）

    ワークフロー仕様書 § ダッシュボード表示切替 データスコープ制限チェック
    dashboard_uuid と accessible_org_ids が一致するレコードを返す
    """

    @patch(f'{MODULE}.db')
    def test_returns_dashboard_when_accessible(self, mock_db):
        """2.2.1 / 1.2.1 スコープ内ダッシュボード: レコードを返す"""
        # Arrange
        mock_dash = MagicMock()
        mock_db.session.query.return_value.filter.return_value.first.return_value = mock_dash
        from iot_app.services.customer_dashboard.common import check_dashboard_access

        # Act
        result = check_dashboard_access('dash-uuid-001', [1, 2])

        # Assert
        assert result is mock_dash

    @patch(f'{MODULE}.db')
    def test_returns_none_when_not_found(self, mock_db):
        """2.2.2 ダッシュボードが存在しない場合: None を返す"""
        # Arrange
        mock_db.session.query.return_value.filter.return_value.first.return_value = None
        from iot_app.services.customer_dashboard.common import check_dashboard_access

        # Act
        result = check_dashboard_access('no-such-uuid', [1, 2])

        # Assert
        assert result is None

    @patch(f'{MODULE}.db')
    def test_returns_none_when_out_of_scope(self, mock_db):
        """1.2.2 アクセス可能スコープ外（organization_id 不一致）: None を返す"""
        # Arrange
        mock_db.session.query.return_value.filter.return_value.first.return_value = None
        from iot_app.services.customer_dashboard.common import check_dashboard_access

        # Act
        result = check_dashboard_access('dash-uuid-001', [99])

        # Assert
        assert result is None

    @patch(f'{MODULE}.db')
    def test_returns_none_when_logically_deleted(self, mock_db):
        """2.2.3 論理削除済み（delete_flag=True）: None を返す"""
        # Arrange
        # delete_flag=False フィルタにより論理削除済みレコードはヒットしない
        mock_db.session.query.return_value.filter.return_value.first.return_value = None
        from iot_app.services.customer_dashboard.common import check_dashboard_access

        # Act
        result = check_dashboard_access('deleted-dash-uuid', [1])

        # Assert
        assert result is None

    @patch(f'{MODULE}.db')
    def test_filters_by_accessible_org_ids(self, mock_db):
        """3.1.1.1 accessible_org_ids で organization_id を絞り込む"""
        # Arrange
        mock_db.session.query.return_value.filter.return_value.first.return_value = None
        from iot_app.services.customer_dashboard.common import check_dashboard_access
        from iot_app.models.customer_dashboard import DashboardMaster

        # Act
        check_dashboard_access('dash-uuid-001', [1, 2])

        # Assert
        filter_args = mock_db.session.query.return_value.filter.call_args[0]
        in_expr = next(f for f in filter_args if hasattr(f, 'right') and getattr(f.right, 'expanding', False))
        assert in_expr.left == DashboardMaster.organization_id
        assert in_expr.right.value == [1, 2]


# ---------------------------------------------------------------------------
# create_dashboard
# ---------------------------------------------------------------------------

@pytest.mark.unit
class TestCreateDashboard:
    """観点: 3.2.1.1（登録）, 3.2.2.1（uuid・監査項目の自動設定）

    使用ルート:
        POST /analysis/customer-dashboard/dashboards/register

    ワークフロー仕様書 § ダッシュボード登録 ① ダッシュボード登録
    dashboard_uuid, creator, modifier を自動付与して INSERT する
    """

    @patch(f'{MODULE}.db')
    def test_adds_dashboard_to_session(self, mock_db):
        """3.2.1.1 ダッシュボードを db.session.add する"""
        # Arrange
        from iot_app.services.customer_dashboard.common import create_dashboard

        # Act
        create_dashboard('テストダッシュボード', organization_id=1, user_id=1)

        # Assert
        mock_db.session.add.assert_called_once()

    @patch(f'{MODULE}.db')
    def test_sets_uuid_automatically(self, mock_db):
        """3.2.2.1 dashboard_uuid が自動生成される（UUID形式・36文字）"""
        # Arrange
        from iot_app.services.customer_dashboard.common import create_dashboard

        # Act
        create_dashboard('テストダッシュボード', organization_id=1, user_id=1)
        added_obj = mock_db.session.add.call_args[0][0]

        # Assert
        assert added_obj.dashboard_uuid is not None
        assert len(str(added_obj.dashboard_uuid)) == 36

    @patch(f'{MODULE}.db')
    def test_sets_creator_and_modifier(self, mock_db):
        """3.2.2.1 creator / modifier にログインユーザーIDが設定される"""
        # Arrange
        from iot_app.services.customer_dashboard.common import create_dashboard

        # Act
        create_dashboard('テストダッシュボード', organization_id=1, user_id=1)
        added_obj = mock_db.session.add.call_args[0][0]

        # Assert
        assert added_obj.creator == 1
        assert added_obj.modifier == 1


# ---------------------------------------------------------------------------
# update_dashboard_title
# ---------------------------------------------------------------------------

@pytest.mark.unit
class TestUpdateDashboardTitle:
    """観点: 3.3.1.1（更新）, 3.3.2.1（監査項目更新）

    使用ルート:
        POST /analysis/customer-dashboard/dashboards/<uuid>/update

    ワークフロー仕様書 § ダッシュボードタイトル更新
    ダッシュボード名と modifier を更新する（楽観ロック検証はView層で実施）
    """

    def test_updates_dashboard_name(self):
        """3.3.1.1 dashboard_name を指定した名前に更新する"""
        # Arrange
        mock_dashboard = MagicMock()
        from iot_app.services.customer_dashboard.common import update_dashboard_title

        # Act
        update_dashboard_title(mock_dashboard, name='新しいタイトル', modifier=1)

        # Assert
        assert mock_dashboard.dashboard_name == '新しいタイトル'

    def test_sets_modifier(self):
        """3.3.2.1 modifier にユーザーIDを設定する"""
        # Arrange
        mock_dashboard = MagicMock()
        from iot_app.services.customer_dashboard.common import update_dashboard_title

        # Act
        update_dashboard_title(mock_dashboard, name='タイトル', modifier=1)

        # Assert
        assert mock_dashboard.modifier == 1


# ---------------------------------------------------------------------------
# delete_dashboard_user_setting
# ---------------------------------------------------------------------------

@pytest.mark.unit
class TestDeleteDashboardUserSetting:
    """観点: 3.4.1.1（論理削除）, 3.4.2.1（監査項目更新）

    使用ルート:
        POST /analysis/customer-dashboard/dashboards/<uuid>/delete（次ダッシュボードなし時）

    ワークフロー仕様書 § ダッシュボード削除 ユーザー設定削除
    dashboard_user_setting を論理削除する（delete_flag = True）
    """

    @patch(f'{MODULE}.db')
    def test_sets_delete_flag(self, mock_db):
        """3.4.1.1 delete_flag を True に設定する"""
        # Arrange
        mock_setting = MagicMock()
        mock_db.session.query.return_value.filter.return_value.first.return_value = mock_setting
        from iot_app.services.customer_dashboard.common import delete_dashboard_user_setting

        # Act
        delete_dashboard_user_setting(user_id=1, modifier=1)

        # Assert
        assert mock_setting.delete_flag is True

    @patch(f'{MODULE}.db')
    def test_sets_modifier(self, mock_db):
        """3.4.2.1 modifier を更新する"""
        # Arrange
        mock_setting = MagicMock()
        mock_db.session.query.return_value.filter.return_value.first.return_value = mock_setting
        from iot_app.services.customer_dashboard.common import delete_dashboard_user_setting

        # Act
        delete_dashboard_user_setting(user_id=1, modifier=1)

        # Assert
        assert mock_setting.modifier == 1


# ---------------------------------------------------------------------------
# delete_dashboard_with_cascade
# ---------------------------------------------------------------------------

@pytest.mark.unit
class TestDeleteDashboardWithCascade:
    """観点: 3.4.1.1（論理削除）, 3.4.4（次ダッシュボードへの切替）

    使用ルート:
        POST /analysis/customer-dashboard/dashboards/<uuid>/delete

    ワークフロー仕様書 § ダッシュボード削除
    配下のガジェット・グループを論理削除後、ダッシュボードを論理削除する。
    次のダッシュボードがある場合はユーザー設定を更新し、ない場合は論理削除する。
    """

    @patch(f'{MODULE}.delete_gadgets_by_dashboard')
    @patch(f'{MODULE}.delete_groups_by_dashboard')
    @patch(f'{MODULE}.get_first_dashboard')
    @patch(f'{MODULE}.upsert_dashboard_user_setting')
    @patch(f'{MODULE}.delete_dashboard_user_setting')
    def test_cascade_deletes_gadgets_and_groups(
        self, _mock_del_setting, _mock_upsert, mock_get_first, mock_del_groups, mock_del_gadgets
    ):
        """3.4.1.1 配下のガジェット・グループを論理削除する"""
        # Arrange
        mock_dashboard = MagicMock()
        mock_dashboard.dashboard_id = 1
        mock_get_first.return_value = MagicMock(dashboard_id=2)
        from iot_app.services.customer_dashboard.common import delete_dashboard_with_cascade

        # Act
        delete_dashboard_with_cascade(mock_dashboard, accessible_org_ids=[1], user_id=1)

        # Assert
        mock_del_gadgets.assert_called_once_with(dashboard_id=1, modifier=1)
        mock_del_groups.assert_called_once_with(dashboard_id=1, modifier=1)
        mock_get_first.assert_called_once_with([1], exclude_id=1)

    @patch(f'{MODULE}.delete_gadgets_by_dashboard')
    @patch(f'{MODULE}.delete_groups_by_dashboard')
    @patch(f'{MODULE}.get_first_dashboard')
    @patch(f'{MODULE}.upsert_dashboard_user_setting')
    @patch(f'{MODULE}.delete_dashboard_user_setting')
    def test_sets_delete_flag_on_dashboard(
        self, _mock_del_setting, _mock_upsert, mock_get_first, _mock_del_groups, _mock_del_gadgets
    ):
        """3.4.1.1 ダッシュボードの delete_flag を True に設定する"""
        # Arrange
        mock_dashboard = MagicMock()
        mock_dashboard.dashboard_id = 1
        mock_get_first.return_value = None
        from iot_app.services.customer_dashboard.common import delete_dashboard_with_cascade

        # Act
        delete_dashboard_with_cascade(mock_dashboard, accessible_org_ids=[1], user_id=1)

        # Assert
        assert mock_dashboard.delete_flag is True
        assert mock_dashboard.modifier == 1
        mock_get_first.assert_called_once_with([1], exclude_id=1)

    @patch(f'{MODULE}.delete_gadgets_by_dashboard')
    @patch(f'{MODULE}.delete_groups_by_dashboard')
    @patch(f'{MODULE}.get_first_dashboard')
    @patch(f'{MODULE}.upsert_dashboard_user_setting')
    @patch(f'{MODULE}.delete_dashboard_user_setting')
    def test_switches_to_next_dashboard_when_exists(
        self, mock_del_setting, mock_upsert, mock_get_first, _mock_del_groups, _mock_del_gadgets
    ):
        """3.4.4 次のダッシュボードがある場合: ユーザー設定を更新する"""
        # Arrange
        mock_dashboard = MagicMock()
        mock_dashboard.dashboard_id = 1
        mock_next = MagicMock()
        mock_next.dashboard_id = 2
        mock_get_first.return_value = mock_next
        from iot_app.services.customer_dashboard.common import delete_dashboard_with_cascade

        # Act
        delete_dashboard_with_cascade(mock_dashboard, accessible_org_ids=[1], user_id=1)

        # Assert
        mock_get_first.assert_called_once_with([1], exclude_id=1)
        mock_upsert.assert_called_once_with(1, 2)
        mock_del_setting.assert_not_called()

    @patch(f'{MODULE}.delete_gadgets_by_dashboard')
    @patch(f'{MODULE}.delete_groups_by_dashboard')
    @patch(f'{MODULE}.get_first_dashboard')
    @patch(f'{MODULE}.upsert_dashboard_user_setting')
    @patch(f'{MODULE}.delete_dashboard_user_setting')
    def test_deletes_user_setting_when_no_next_dashboard(
        self, mock_del_setting, mock_upsert, mock_get_first, _mock_del_groups, _mock_del_gadgets
    ):
        """3.4.4 次のダッシュボードがない場合: ユーザー設定を論理削除する"""
        # Arrange
        mock_dashboard = MagicMock()
        mock_dashboard.dashboard_id = 1
        mock_get_first.return_value = None
        from iot_app.services.customer_dashboard.common import delete_dashboard_with_cascade

        # Act
        delete_dashboard_with_cascade(mock_dashboard, accessible_org_ids=[1], user_id=1)

        # Assert
        mock_get_first.assert_called_once_with([1], exclude_id=1)
        mock_del_setting.assert_called_once_with(user_id=1, modifier=1)
        mock_upsert.assert_not_called()


# ---------------------------------------------------------------------------
# get_dashboard_groups
# ---------------------------------------------------------------------------

@pytest.mark.unit
class TestGetDashboardGroups:
    """観点: 3.1.1.1（フィルタ条件）, 3.1.4.1/3.1.4.2（件数）

    使用ルート:
        GET  /analysis/customer-dashboard（初期表示）

    ワークフロー仕様書 § ダッシュボード初期表示 ⑤ ダッシュボードグループ一覧取得
    dashboard_id に紐づくグループを display_order 昇順で返す
    """

    @patch(f'{MODULE}.db')
    def test_filters_by_dashboard_id(self, mock_db):
        """3.1.1.1 フィルタ条件: dashboard_id で絞り込む"""
        # Arrange
        from iot_app.services.customer_dashboard.common import get_dashboard_groups
        from iot_app.models.customer_dashboard import DashboardGroupMaster
        (
            mock_db.session.query.return_value
            .filter.return_value
            .order_by.return_value
            .all.return_value
        ) = []

        # Act
        get_dashboard_groups(dashboard_id=1)

        # Assert
        mock_db.session.query.assert_called_once_with(DashboardGroupMaster)
        mock_db.session.query.return_value.filter.assert_called_once()

    @patch(f'{MODULE}.db')
    def test_returns_groups_ordered_by_display_order(self, mock_db):
        """3.1.4.1 グループあり: display_order 昇順のリストを返す"""
        # Arrange
        mock_group1 = MagicMock()
        mock_group2 = MagicMock()
        (
            mock_db.session.query.return_value
            .filter.return_value
            .order_by.return_value
            .all.return_value
        ) = [mock_group1, mock_group2]
        from iot_app.services.customer_dashboard.common import get_dashboard_groups

        # Act
        result = get_dashboard_groups(dashboard_id=1)

        # Assert
        assert result == [mock_group1, mock_group2]

    @patch(f'{MODULE}.db')
    def test_returns_empty_when_no_groups(self, mock_db):
        """3.1.4.2 グループなし: 空リストを返す"""
        # Arrange
        (
            mock_db.session.query.return_value
            .filter.return_value
            .order_by.return_value
            .all.return_value
        ) = []
        from iot_app.services.customer_dashboard.common import get_dashboard_groups

        # Act
        result = get_dashboard_groups(dashboard_id=1)

        # Assert
        assert result == []


# ---------------------------------------------------------------------------
# create_dashboard_group
# ---------------------------------------------------------------------------

@pytest.mark.unit
class TestCreateDashboardGroup:
    """観点: 3.2.1.1（登録）, 3.2.2.1（uuid・監査項目の自動設定）

    使用ルート:
        POST /analysis/customer-dashboard/groups/register

    ワークフロー仕様書 § ダッシュボードグループ登録 ① ダッシュボードグループ登録
    """

    @patch(f'{MODULE}.db')
    def test_adds_group_to_session(self, mock_db):
        """3.2.1.1 ダッシュボードグループを db.session.add する"""
        # Arrange
        from iot_app.services.customer_dashboard.common import create_dashboard_group

        # Act
        create_dashboard_group(
            group_name='グループA',
            dashboard_id=1,
            user_id=1,
        )

        # Assert
        mock_db.session.add.assert_called_once()

    @patch(f'{MODULE}.db')
    def test_sets_creator_and_modifier(self, mock_db):
        """3.2.2.1 creator / modifier にログインユーザーIDが設定される"""
        # Arrange
        from iot_app.services.customer_dashboard.common import create_dashboard_group

        # Act
        create_dashboard_group('グループA', dashboard_id=1, user_id=1)
        added_obj = mock_db.session.add.call_args[0][0]

        # Assert
        assert added_obj.creator == 1
        assert added_obj.modifier == 1

    @patch(f'{MODULE}.db')
    def test_sets_uuid_automatically(self, mock_db):
        """3.2.2.1 dashboard_group_uuid が自動生成される（UUID形式・36文字）"""
        # Arrange
        from iot_app.services.customer_dashboard.common import create_dashboard_group

        # Act
        create_dashboard_group('グループA', dashboard_id=1, user_id=1)
        added_obj = mock_db.session.add.call_args[0][0]

        # Assert
        assert added_obj.dashboard_group_uuid is not None
        assert len(str(added_obj.dashboard_group_uuid)) == 36

    @patch(f'{MODULE}.db')
    def test_sets_display_order_as_max_plus_one(self, mock_db):
        """3.2.2.1 display_order に既存最大値+1を設定する"""
        # Arrange
        mock_db.session.query.return_value.filter.return_value.scalar.return_value = 2
        from iot_app.services.customer_dashboard.common import create_dashboard_group

        # Act
        create_dashboard_group('グループA', dashboard_id=1, user_id=1)
        added_obj = mock_db.session.add.call_args[0][0]

        # Assert
        assert added_obj.display_order == 3

    @patch(f'{MODULE}.db')
    def test_sets_display_order_to_one_when_no_groups_exist(self, mock_db):
        """3.2.2.1 グループが存在しない場合: display_order を 1 に設定する"""
        # Arrange
        mock_db.session.query.return_value.filter.return_value.scalar.return_value = None
        from iot_app.services.customer_dashboard.common import create_dashboard_group

        # Act
        create_dashboard_group('グループA', dashboard_id=1, user_id=1)
        added_obj = mock_db.session.add.call_args[0][0]

        # Assert
        assert added_obj.display_order == 1


# ---------------------------------------------------------------------------
# check_group_access
# ---------------------------------------------------------------------------

@pytest.mark.unit
class TestCheckGroupAccess:
    """観点: 2.2.1/2.2.2/2.2.3（存在チェック）, 1.2.1/1.2.2（スコープ制限）

    使用ルート:
        POST /analysis/customer-dashboard/groups/<uuid>/update（スコープチェック）
        POST /analysis/customer-dashboard/groups/<uuid>/delete（スコープチェック）

    ワークフロー仕様書 § ダッシュボードグループタイトル更新 ③ データスコープ制限チェック
    dashboard_group_uuid と accessible_org_ids が一致するレコードを返す
    """

    @patch(f'{MODULE}.db')
    def test_returns_group_when_accessible(self, mock_db):
        """2.2.1 / 1.2.1 スコープ内グループ: レコードを返す"""
        # Arrange
        mock_group = MagicMock()
        mock_db.session.query.return_value.join.return_value.filter.return_value.first.return_value = mock_group
        from iot_app.services.customer_dashboard.common import check_group_access

        # Act
        result = check_group_access('group-uuid-001', [1, 2])

        # Assert
        assert result is mock_group

    @patch(f'{MODULE}.db')
    def test_returns_none_when_not_found(self, mock_db):
        """2.2.2 グループが存在しない場合: None を返す"""
        # Arrange
        mock_db.session.query.return_value.join.return_value.filter.return_value.first.return_value = None
        from iot_app.services.customer_dashboard.common import check_group_access

        # Act
        result = check_group_access('no-such-uuid', [1, 2])

        # Assert
        assert result is None

    @patch(f'{MODULE}.db')
    def test_returns_none_when_out_of_scope(self, mock_db):
        """1.2.2 アクセス可能スコープ外（organization_id 不一致）: None を返す"""
        # Arrange
        mock_db.session.query.return_value.join.return_value.filter.return_value.first.return_value = None
        from iot_app.services.customer_dashboard.common import check_group_access

        # Act
        result = check_group_access('group-uuid-001', [99])

        # Assert
        assert result is None

    @patch(f'{MODULE}.db')
    def test_returns_none_when_logically_deleted(self, mock_db):
        """2.2.3 論理削除済み（delete_flag=True）: None を返す"""
        # Arrange
        mock_db.session.query.return_value.join.return_value.filter.return_value.first.return_value = None
        from iot_app.services.customer_dashboard.common import check_group_access

        # Act
        result = check_group_access('deleted-group-uuid', [1])

        # Assert
        assert result is None

    @patch(f'{MODULE}.db')
    def test_filters_by_accessible_org_ids(self, mock_db):
        """3.1.1.1 accessible_org_ids で organization_id を絞り込む（JOIN経由）"""
        # Arrange
        mock_db.session.query.return_value.join.return_value.filter.return_value.first.return_value = None
        from iot_app.services.customer_dashboard.common import check_group_access
        from iot_app.models.customer_dashboard import DashboardMaster

        # Act
        check_group_access('group-uuid-001', [1, 2])

        # Assert
        filter_args = mock_db.session.query.return_value.join.return_value.filter.call_args[0]
        in_expr = next(f for f in filter_args if hasattr(f, 'right') and getattr(f.right, 'expanding', False))
        assert in_expr.left == DashboardMaster.organization_id
        assert in_expr.right.value == [1, 2]


# ---------------------------------------------------------------------------
# update_group_title
# ---------------------------------------------------------------------------

@pytest.mark.unit
class TestUpdateGroupTitle:
    """観点: 3.3.1.1（更新）, 3.3.2.1（監査項目更新）

    使用ルート:
        POST /analysis/customer-dashboard/groups/<uuid>/update

    ワークフロー仕様書 § グループタイトル更新
    グループ名と modifier を更新する（楽観ロック検証はView層で実施）
    """

    def test_updates_group_name(self):
        """3.3.1.1 dashboard_group_name を指定した名前に更新する"""
        # Arrange
        mock_group = MagicMock()
        from iot_app.services.customer_dashboard.common import update_group_title

        # Act
        update_group_title(mock_group, name='新グループ名', modifier=1)

        # Assert
        assert mock_group.dashboard_group_name == '新グループ名'

    def test_sets_modifier(self):
        """3.3.2.1 modifier にユーザーIDを設定する"""
        # Arrange
        mock_group = MagicMock()
        from iot_app.services.customer_dashboard.common import update_group_title

        # Act
        update_group_title(mock_group, name='グループ名', modifier=1)

        # Assert
        assert mock_group.modifier == 1


# ---------------------------------------------------------------------------
# get_gadgets_by_groups
# ---------------------------------------------------------------------------

@pytest.mark.unit
class TestGetGadgetsByGroups:
    """観点: 3.1.4.1（件数）, 3.1.2.1（空入力時の早期リターン）

    使用ルート:
        GET  /analysis/customer-dashboard（初期表示）

    ワークフロー仕様書 § ダッシュボード初期表示 ⑥ ガジェット一覧取得
    group_ids が空のとき DB アクセスを行わず空リストを返す
    """

    @patch(f'{MODULE}.db')
    def test_returns_gadgets_for_given_groups(self, mock_db):
        """3.1.4.1 グループIDあり: 該当ガジェット一覧を返す"""
        # Arrange
        mock_gadget1 = MagicMock()
        (
            mock_db.session.query.return_value
            .filter.return_value
            .order_by.return_value
            .all.return_value
        ) = [mock_gadget1]
        from iot_app.services.customer_dashboard.common import get_gadgets_by_groups

        # Act
        result = get_gadgets_by_groups([10, 20])

        # Assert
        assert result == [mock_gadget1]

    @patch(f'{MODULE}.db')
    def test_returns_empty_without_db_access_when_group_ids_empty(self, mock_db):
        """3.1.2.1 group_ids が空: DBアクセスせず空リストを返す"""
        # Arrange
        from iot_app.services.customer_dashboard.common import get_gadgets_by_groups

        # Act
        result = get_gadgets_by_groups([])

        # Assert
        assert result == []
        mock_db.session.query.assert_not_called()


# ---------------------------------------------------------------------------
# get_gadget_types
# ---------------------------------------------------------------------------

@pytest.mark.unit
class TestGetGadgetTypes:
    """観点: 3.1.4.1/3.1.4.2（件数）, 3.1.1.1（ソート）

    使用ルート:
        GET  /analysis/customer-dashboard/gadgets/add（ガジェット追加モーダル）

    ワークフロー仕様書 § ガジェット追加モーダル表示
    gadget_type_master から全ガジェット種別を取得する
    """

    @patch(f'{MODULE}.db')
    def test_returns_all_gadget_types(self, mock_db):
        """3.1.4.1 ガジェット種別あり: 種別リストを返す"""
        # Arrange
        mock_types = [MagicMock() for _ in range(22)]  # 仕様上22種
        (
            mock_db.session.query.return_value
            .filter.return_value
            .order_by.return_value
            .all.return_value
        ) = mock_types
        from iot_app.services.customer_dashboard.common import get_gadget_types

        # Act
        result = get_gadget_types()

        # Assert
        assert len(result) == 22

    @patch(f'{MODULE}.db')
    def test_returns_empty_when_no_gadget_types(self, mock_db):
        """3.1.4.2 ガジェット種別なし: 空リストを返す"""
        # Arrange
        (
            mock_db.session.query.return_value
            .filter.return_value
            .order_by.return_value
            .all.return_value
        ) = []
        from iot_app.services.customer_dashboard.common import get_gadget_types

        # Act
        result = get_gadget_types()

        # Assert
        assert result == []


# ---------------------------------------------------------------------------
# check_gadget_access
# ---------------------------------------------------------------------------

@pytest.mark.unit
class TestCheckGadgetAccess:
    """観点: 2.2.1/2.2.2/2.2.3（存在チェック）, 1.2.1/1.2.2（スコープ制限）

    使用ルート:
        POST /analysis/customer-dashboard/gadgets/<uuid>/update（スコープチェック）
        POST /analysis/customer-dashboard/gadgets/<uuid>/delete（スコープチェック）

    ワークフロー仕様書 § ガジェット削除 / ガジェットタイトル更新 スコープチェック
    gadget_uuid → group → dashboard → organization の間接参照でスコープを確認する

    TODO: check_gadget_access() の JOIN クエリ実装方針（Q4）は設計書に未記載。
          ガジェット→グループ→ダッシュボード→組織の間接参照方式について要確認。
    """

    @patch(f'{MODULE}.db')
    def test_returns_gadget_when_accessible(self, mock_db):
        """2.2.1 / 1.2.1 スコープ内ガジェット: レコードを返す"""
        # Arrange
        mock_gadget = MagicMock()
        mock_db.session.query.return_value.join.return_value.join.return_value.filter.return_value.first.return_value = mock_gadget
        from iot_app.services.customer_dashboard.common import check_gadget_access

        # Act
        result = check_gadget_access('gadget-uuid-001', [1, 2])

        # Assert
        assert result is mock_gadget

    @patch(f'{MODULE}.db')
    def test_returns_none_when_not_found(self, mock_db):
        """2.2.2 ガジェットが存在しない場合: None を返す"""
        # Arrange
        mock_db.session.query.return_value.join.return_value.join.return_value.filter.return_value.first.return_value = None
        from iot_app.services.customer_dashboard.common import check_gadget_access

        # Act
        result = check_gadget_access('no-such-uuid', [1, 2])

        # Assert
        assert result is None

    @patch(f'{MODULE}.db')
    def test_returns_none_when_out_of_scope(self, mock_db):
        """1.2.2 アクセス可能スコープ外（organization_id 不一致）: None を返す"""
        # Arrange
        mock_db.session.query.return_value.join.return_value.join.return_value.filter.return_value.first.return_value = None
        from iot_app.services.customer_dashboard.common import check_gadget_access

        # Act
        result = check_gadget_access('gadget-uuid-001', [99])

        # Assert
        assert result is None

    @patch(f'{MODULE}.db')
    def test_returns_none_when_logically_deleted(self, mock_db):
        """2.2.3 論理削除済み（delete_flag=True）: None を返す"""
        # Arrange
        # delete_flag=False フィルタにより論理削除済みレコードはヒットしない
        mock_db.session.query.return_value.join.return_value.join.return_value.filter.return_value.first.return_value = None
        from iot_app.services.customer_dashboard.common import check_gadget_access

        # Act
        result = check_gadget_access('deleted-gadget-uuid', [1])

        # Assert
        assert result is None

    @patch(f'{MODULE}.db')
    def test_filters_by_accessible_org_ids(self, mock_db):
        """3.1.1.1 accessible_org_ids で organization_id を絞り込む（JOIN経由）"""
        # Arrange
        (
            mock_db.session.query.return_value
            .join.return_value
            .join.return_value
            .filter.return_value
            .first.return_value
        ) = None
        from iot_app.services.customer_dashboard.common import check_gadget_access
        from iot_app.models.customer_dashboard import DashboardMaster

        # Act
        check_gadget_access('gadget-uuid-001', [1, 2])

        # Assert
        filter_args = (
            mock_db.session.query.return_value
            .join.return_value
            .join.return_value
            .filter.call_args[0]
        )
        in_expr = next(f for f in filter_args if hasattr(f, 'right') and getattr(f.right, 'expanding', False))
        assert in_expr.left == DashboardMaster.organization_id
        assert in_expr.right.value == [1, 2]


# ---------------------------------------------------------------------------
# update_gadget_title
# ---------------------------------------------------------------------------

@pytest.mark.unit
class TestUpdateGadgetTitle:
    """観点: 3.3.1.1（更新）, 3.3.2.1（監査項目更新）

    使用ルート:
        POST /analysis/customer-dashboard/gadgets/<uuid>/update

    ワークフロー仕様書 § ガジェットタイトル更新
    ガジェット名と modifier を更新する（楽観ロック検証はView層で実施）
    """

    def test_updates_gadget_name(self):
        """3.3.1.1 gadget_name を指定した名前に更新する"""
        # Arrange
        mock_gadget = MagicMock()
        from iot_app.services.customer_dashboard.common import update_gadget_title

        # Act
        update_gadget_title(mock_gadget, name='新ガジェット名', modifier=1)

        # Assert
        assert mock_gadget.gadget_name == '新ガジェット名'

    def test_sets_modifier(self):
        """3.3.2.1 modifier にユーザーIDを設定する"""
        # Arrange
        mock_gadget = MagicMock()
        from iot_app.services.customer_dashboard.common import update_gadget_title

        # Act
        update_gadget_title(mock_gadget, name='ガジェット名', modifier=1)

        # Assert
        assert mock_gadget.modifier == 1


# ---------------------------------------------------------------------------
# delete_gadget
# ---------------------------------------------------------------------------

@pytest.mark.unit
class TestDeleteGadget:
    """観点: 3.4.1.1（論理削除）, 3.4.2.1（監査項目更新）

    使用ルート:
        POST /analysis/customer-dashboard/gadgets/<uuid>/delete

    ワークフロー仕様書 § ガジェット削除
    ガジェットを論理削除する（delete_flag = True）
    """

    def test_sets_delete_flag(self):
        """3.4.1.1 delete_flag を True に設定する"""
        # Arrange
        mock_gadget = MagicMock()
        from iot_app.services.customer_dashboard.common import delete_gadget

        # Act
        delete_gadget(mock_gadget, modifier=1)

        # Assert
        assert mock_gadget.delete_flag is True

    def test_sets_modifier(self):
        """3.4.2.1 modifier にユーザーIDを設定する"""
        # Arrange
        mock_gadget = MagicMock()
        from iot_app.services.customer_dashboard.common import delete_gadget

        # Act
        delete_gadget(mock_gadget, modifier=1)

        # Assert
        assert mock_gadget.modifier == 1


# ---------------------------------------------------------------------------
# save_layout
# ---------------------------------------------------------------------------

@pytest.mark.unit
class TestSaveLayout:
    """観点: 2.2.2（対象なし時スキップ）, 3.3.1.1（更新）, 2.3.2（エラー時ロールバック）

    使用ルート:
        POST /analysis/customer-dashboard/layout/save

    ワークフロー仕様書 § レイアウト保存
    各ガジェットの position_x/y, display_order を更新する。
    gadget_size は変更しない（登録時固定）。
    ガジェットが存在しない場合はスキップする。
    エラー時は db.session.rollback() を呼ぶ。
    """

    @patch(f'{MODULE}.db')
    def test_updates_position_for_each_gadget(self, mock_db):
        """3.3.1.1 ガジェットごとに position_x/y / display_order を更新する"""
        # Arrange
        mock_gadget = MagicMock()
        mock_db.session.query.return_value.filter.return_value.first.return_value = mock_gadget
        layout_data = [
            {'gadget_uuid': 'g-001', 'position_x': 0, 'position_y': 1, 'display_order': 0}
        ]
        from iot_app.services.customer_dashboard.common import save_layout

        # Act
        save_layout(layout_data, modifier=1)

        # Assert
        assert mock_gadget.position_x == 0
        assert mock_gadget.position_y == 1
        assert mock_gadget.display_order == 0
        assert mock_gadget.modifier == 1
        # TODO: freezegun導入後に update_date を検証する

    @patch(f'{MODULE}.db')
    def test_does_not_change_gadget_size(self, mock_db):
        """3.3.1.1 gadget_size は変更しない（登録時固定）"""
        # Arrange
        mock_gadget = MagicMock()
        mock_gadget.gadget_size = 0
        mock_db.session.query.return_value.filter.return_value.first.return_value = mock_gadget
        layout_data = [
            {'gadget_uuid': 'g-001', 'position_x': 1, 'position_y': 2, 'display_order': 1}
        ]
        from iot_app.services.customer_dashboard.common import save_layout

        # Act
        save_layout(layout_data, modifier=1)

        # Assert
        assert mock_gadget.gadget_size == 0

    @patch(f'{MODULE}.db')
    def test_skips_when_gadget_not_found(self, mock_db):
        """2.2.2 gadget_uuid に一致するガジェットが存在しない場合: 更新をスキップする"""
        # Arrange
        mock_db.session.query.return_value.filter.return_value.first.return_value = None
        layout_data = [
            {'gadget_uuid': 'no-such-uuid', 'position_x': 0, 'position_y': 0, 'display_order': 0}
        ]
        from iot_app.services.customer_dashboard.common import save_layout

        # Act / Assert（例外が発生しないこと）
        save_layout(layout_data, modifier=1)

    @patch(f'{MODULE}.db')
    def test_rollbacks_on_exception(self, mock_db):
        """2.3.2 DB エラー時に db.session.rollback() を呼ぶ"""
        # Arrange
        mock_db.session.query.side_effect = Exception('DB error')
        layout_data = [
            {'gadget_uuid': 'g-001', 'position_x': 0, 'position_y': 0, 'display_order': 0}
        ]
        from iot_app.services.customer_dashboard.common import save_layout

        # Act
        with pytest.raises(Exception):
            save_layout(layout_data, modifier=1)

        # Assert
        mock_db.session.rollback.assert_called_once()


# ---------------------------------------------------------------------------
# delete_gadgets_by_dashboard
# ---------------------------------------------------------------------------

@pytest.mark.unit
class TestDeleteGadgetsByDashboard:
    """観点: 3.4.1.1（論理削除）, 3.4.2.1（監査項目更新）

    使用ルート:
        POST /analysis/customer-dashboard/dashboards/<uuid>/delete（カスケード削除）

    ワークフロー仕様書 § ダッシュボード削除 カスケード削除
    dashboard_id に紐づく全ガジェットを論理削除する
    """

    @patch(f'{MODULE}.db')
    def test_sets_delete_flag_on_gadgets(self, mock_db):
        """3.4.1.1 ガジェットの delete_flag を True に設定する"""
        # Arrange
        mock_gadget1 = MagicMock()
        mock_gadget2 = MagicMock()
        (
            mock_db.session.query.return_value
            .join.return_value
            .filter.return_value
            .all.return_value
        ) = [mock_gadget1, mock_gadget2]
        from iot_app.services.customer_dashboard.common import delete_gadgets_by_dashboard

        # Act
        delete_gadgets_by_dashboard(dashboard_id=1, modifier=1)

        # Assert
        assert mock_gadget1.delete_flag is True
        assert mock_gadget2.delete_flag is True

    @patch(f'{MODULE}.db')
    def test_sets_modifier_on_gadgets(self, mock_db):
        """3.4.2.1 ガジェットの modifier を更新する"""
        # Arrange
        mock_gadget = MagicMock()
        (
            mock_db.session.query.return_value
            .join.return_value
            .filter.return_value
            .all.return_value
        ) = [mock_gadget]
        from iot_app.services.customer_dashboard.common import delete_gadgets_by_dashboard

        # Act
        delete_gadgets_by_dashboard(dashboard_id=1, modifier=1)

        # Assert
        assert mock_gadget.modifier == 1
        mock_db.session.commit.assert_called_once()

    @patch(f'{MODULE}.db')
    def test_does_nothing_when_no_gadgets(self, mock_db):
        """3.1.4.2 ガジェットなし: commitのみ呼ばれる"""
        # Arrange
        (
            mock_db.session.query.return_value
            .join.return_value
            .filter.return_value
            .all.return_value
        ) = []
        from iot_app.services.customer_dashboard.common import delete_gadgets_by_dashboard

        # Act
        delete_gadgets_by_dashboard(dashboard_id=1, modifier=1)

        # Assert
        mock_db.session.commit.assert_called_once()


# ---------------------------------------------------------------------------
# delete_groups_by_dashboard
# ---------------------------------------------------------------------------

@pytest.mark.unit
class TestDeleteGroupsByDashboard:
    """観点: 3.4.1.1（論理削除）, 3.4.2.1（監査項目更新）

    使用ルート:
        POST /analysis/customer-dashboard/dashboards/<uuid>/delete（カスケード削除）

    ワークフロー仕様書 § ダッシュボード削除 カスケード削除
    dashboard_id に紐づく全グループを論理削除する
    """

    @patch(f'{MODULE}.db')
    def test_sets_delete_flag_on_groups(self, mock_db):
        """3.4.1.1 グループの delete_flag を True に設定する"""
        # Arrange
        mock_group1 = MagicMock()
        mock_group2 = MagicMock()
        (
            mock_db.session.query.return_value
            .filter.return_value
            .all.return_value
        ) = [mock_group1, mock_group2]
        from iot_app.services.customer_dashboard.common import delete_groups_by_dashboard

        # Act
        delete_groups_by_dashboard(dashboard_id=1, modifier=1)

        # Assert
        assert mock_group1.delete_flag is True
        assert mock_group2.delete_flag is True

    @patch(f'{MODULE}.db')
    def test_sets_modifier_on_groups(self, mock_db):
        """3.4.2.1 グループの modifier を更新する"""
        # Arrange
        mock_group = MagicMock()
        (
            mock_db.session.query.return_value
            .filter.return_value
            .all.return_value
        ) = [mock_group]
        from iot_app.services.customer_dashboard.common import delete_groups_by_dashboard

        # Act
        delete_groups_by_dashboard(dashboard_id=1, modifier=1)

        # Assert
        assert mock_group.modifier == 1
        mock_db.session.commit.assert_called_once()

    @patch(f'{MODULE}.db')
    def test_does_nothing_when_no_groups(self, mock_db):
        """3.1.4.2 グループなし: commitのみ呼ばれる"""
        # Arrange
        (
            mock_db.session.query.return_value
            .filter.return_value
            .all.return_value
        ) = []
        from iot_app.services.customer_dashboard.common import delete_groups_by_dashboard

        # Act
        delete_groups_by_dashboard(dashboard_id=1, modifier=1)

        # Assert
        mock_db.session.commit.assert_called_once()


# ---------------------------------------------------------------------------
# delete_gadgets_by_group
# ---------------------------------------------------------------------------

@pytest.mark.unit
class TestDeleteGadgetsByGroup:
    """観点: 3.4.1.1（論理削除）, 3.4.2.1（監査項目更新）

    使用ルート:
        POST /analysis/customer-dashboard/groups/<uuid>/delete（カスケード削除）

    ワークフロー仕様書 § ダッシュボードグループ削除 カスケード削除
    group_id に紐づく全ガジェットを論理削除する
    """

    @patch(f'{MODULE}.db')
    def test_sets_delete_flag_on_gadgets(self, mock_db):
        """3.4.1.1 ガジェットの delete_flag を True に設定する"""
        # Arrange
        mock_gadget1 = MagicMock()
        mock_gadget2 = MagicMock()
        (
            mock_db.session.query.return_value
            .filter.return_value
            .all.return_value
        ) = [mock_gadget1, mock_gadget2]
        from iot_app.services.customer_dashboard.common import delete_gadgets_by_group

        # Act
        delete_gadgets_by_group(group_id=10, modifier=1)

        # Assert
        assert mock_gadget1.delete_flag is True
        assert mock_gadget2.delete_flag is True

    @patch(f'{MODULE}.db')
    def test_sets_modifier_on_gadgets(self, mock_db):
        """3.4.2.1 ガジェットの modifier を更新する"""
        # Arrange
        mock_gadget = MagicMock()
        (
            mock_db.session.query.return_value
            .filter.return_value
            .all.return_value
        ) = [mock_gadget]
        from iot_app.services.customer_dashboard.common import delete_gadgets_by_group

        # Act
        delete_gadgets_by_group(group_id=10, modifier=1)

        # Assert
        assert mock_gadget.modifier == 1
        mock_db.session.commit.assert_called_once()

    @patch(f'{MODULE}.db')
    def test_does_nothing_when_no_gadgets(self, mock_db):
        """3.1.4.2 ガジェットなし: commitのみ呼ばれる"""
        # Arrange
        (
            mock_db.session.query.return_value
            .filter.return_value
            .all.return_value
        ) = []
        from iot_app.services.customer_dashboard.common import delete_gadgets_by_group

        # Act
        delete_gadgets_by_group(group_id=10, modifier=1)

        # Assert
        mock_db.session.commit.assert_called_once()


# ---------------------------------------------------------------------------
# delete_group_with_cascade
# ---------------------------------------------------------------------------

@pytest.mark.unit
class TestDeleteGroupWithCascade:
    """観点: 3.4.1.1（論理削除）

    使用ルート:
        POST /analysis/customer-dashboard/groups/<uuid>/delete

    ワークフロー仕様書 § ダッシュボードグループ削除
    配下のガジェットを論理削除後、グループを論理削除する。
    """

    @patch(f'{MODULE}.delete_gadgets_by_group')
    def test_deletes_gadgets_in_group(self, mock_del_gadgets):
        """3.4.1.1 配下のガジェットを論理削除する"""
        # Arrange
        mock_group = MagicMock()
        mock_group.dashboard_group_id = 10
        from iot_app.services.customer_dashboard.common import delete_group_with_cascade

        # Act
        delete_group_with_cascade(mock_group, user_id=1)

        # Assert
        mock_del_gadgets.assert_called_once_with(group_id=10, modifier=1)

    @patch(f'{MODULE}.delete_gadgets_by_group')
    def test_sets_delete_flag_on_group(self, _):
        """3.4.1.1 グループの delete_flag を True に設定する"""
        # Arrange
        mock_group = MagicMock()
        mock_group.dashboard_group_id = 10
        from iot_app.services.customer_dashboard.common import delete_group_with_cascade

        # Act
        delete_group_with_cascade(mock_group, user_id=1)

        # Assert
        assert mock_group.delete_flag is True

    @patch(f'{MODULE}.delete_gadgets_by_group')
    def test_sets_modifier_on_group(self, _):
        """3.4.2.1 グループの modifier を更新する"""
        # Arrange
        mock_group = MagicMock()
        mock_group.dashboard_group_id = 10
        from iot_app.services.customer_dashboard.common import delete_group_with_cascade

        # Act
        delete_group_with_cascade(mock_group, user_id=1)

        # Assert
        assert mock_group.modifier == 1


# ---------------------------------------------------------------------------
# get_devices_by_organization
# ---------------------------------------------------------------------------

@pytest.mark.unit
class TestGetDevicesByOrganization:
    """観点: 3.1.4.1/3.1.4.2（件数）, 3.1.1.1（フィルタ条件）

    使用ルート:
        GET  /analysis/customer-dashboard/organizations/<org_id>/devices（AJAX）

    ワークフロー仕様書 § データソース選択 No.26
    organization_id に紐づくデバイス一覧を device_id 昇順で返す。
    delete_flag = FALSE のみ対象。
    """

    @patch(f'{MODULE}.db')
    def test_returns_devices_for_organization(self, mock_db):
        """3.1.4.1 デバイスあり: デバイス一覧を返す"""
        # Arrange
        mock_device1 = MagicMock()
        mock_device2 = MagicMock()
        (
            mock_db.session.query.return_value
            .filter.return_value
            .order_by.return_value
            .all.return_value
        ) = [mock_device1, mock_device2]
        from iot_app.services.customer_dashboard.common import get_devices_by_organization

        # Act
        result = get_devices_by_organization(org_id=1)

        # Assert
        assert result == [mock_device1, mock_device2]

    @patch(f'{MODULE}.db')
    def test_returns_empty_when_no_devices(self, mock_db):
        """3.1.4.2 デバイスなし: 空リストを返す"""
        # Arrange
        (
            mock_db.session.query.return_value
            .filter.return_value
            .order_by.return_value
            .all.return_value
        ) = []
        from iot_app.services.customer_dashboard.common import get_devices_by_organization

        # Act
        result = get_devices_by_organization(org_id=999)

        # Assert
        assert result == []


# ---------------------------------------------------------------------------
# update_datasource_setting
# ---------------------------------------------------------------------------

@pytest.mark.unit
class TestUpdateDatasourceSetting:
    """観点: 3.3.1.1（更新）, 3.3.2.1（監査項目更新）, 3.1.2（デフォルト値正規化）

    使用ルート:
        POST /analysis/customer-dashboard/datasource/save（AJAX）

    ワークフロー仕様書 § データソース選択 No.27
    dashboard_user_setting の organization_id / device_id を更新する。
    None の場合は 0 に正規化する（DB設計: 未選択=0）。
    """

    @patch(f'{MODULE}.db')
    def test_updates_organization_id_and_device_id(self, mock_db):
        """3.3.1.1 organization_id と device_id を更新する"""
        # Arrange
        mock_setting = MagicMock()
        mock_db.session.query.return_value.filter.return_value.first.return_value = mock_setting
        from iot_app.services.customer_dashboard.common import update_datasource_setting

        # Act
        update_datasource_setting(user_id=1, organization_id=5, device_id=10, modifier=1)

        # Assert
        assert mock_setting.organization_id == 5
        assert mock_setting.device_id == 10

    @patch(f'{MODULE}.db')
    def test_passes_none_organization_id_as_none(self, mock_db):
        """3.1.2 organization_id が None の場合は None のまま設定する（未選択はNULLで保持）"""
        # Arrange
        mock_setting = MagicMock()
        mock_db.session.query.return_value.filter.return_value.first.return_value = mock_setting
        from iot_app.services.customer_dashboard.common import update_datasource_setting

        # Act
        update_datasource_setting(user_id=1, organization_id=None, device_id=10, modifier=1)

        # Assert
        assert mock_setting.organization_id is None

    @patch(f'{MODULE}.db')
    def test_passes_none_device_id_as_none(self, mock_db):
        """3.1.2 device_id が None の場合は None のまま設定する（未選択はNULLで保持）"""
        # Arrange
        mock_setting = MagicMock()
        mock_db.session.query.return_value.filter.return_value.first.return_value = mock_setting
        from iot_app.services.customer_dashboard.common import update_datasource_setting

        # Act
        update_datasource_setting(user_id=1, organization_id=5, device_id=None, modifier=1)

        # Assert
        assert mock_setting.device_id is None

    @patch(f'{MODULE}.db')
    def test_sets_modifier(self, mock_db):
        """3.3.2.1 modifier にユーザーIDを設定する"""
        # Arrange
        mock_setting = MagicMock()
        mock_db.session.query.return_value.filter.return_value.first.return_value = mock_setting
        from iot_app.services.customer_dashboard.common import update_datasource_setting

        # Act
        update_datasource_setting(user_id=1, organization_id=5, device_id=10, modifier=1)

        # Assert
        assert mock_setting.modifier == 1


# ---------------------------------------------------------------------------
# get_organizations
# ---------------------------------------------------------------------------

@pytest.mark.unit
class TestGetOrganizations:
    """観点: 3.1.4（件数）, 2.2.2（存在なし）

    使用ルート:
        GET  /analysis/customer-dashboard（初期表示）

    ワークフロー仕様書 § ダッシュボード初期表示 ⑦ 組織選択肢取得
    accessible_org_ids に含まれる organization_master レコードを返す（プルダウン用）
    """

    @patch(f'{MODULE}.db')
    def test_returns_organizations_in_scope(self, mock_db):
        """3.1.4.1 accessible_org_ids に一致する組織リストを返す"""
        # Arrange
        mock_org1 = MagicMock()
        mock_org2 = MagicMock()
        mock_db.session.query.return_value.filter.return_value.order_by.return_value.all.return_value = [
            mock_org1, mock_org2
        ]
        from iot_app.services.customer_dashboard.common import get_organizations

        # Act
        result = get_organizations([1, 2])

        # Assert
        assert result == [mock_org1, mock_org2]

    @patch(f'{MODULE}.db')
    def test_returns_empty_list_when_no_orgs(self, mock_db):
        """2.2.2 accessible_org_ids に一致する組織が存在しない場合: 空リストを返す"""
        # Arrange
        mock_db.session.query.return_value.filter.return_value.order_by.return_value.all.return_value = []
        from iot_app.services.customer_dashboard.common import get_organizations

        # Act
        result = get_organizations([])

        # Assert
        assert result == []

    @patch(f'{MODULE}.db')
    def test_filters_by_accessible_org_ids(self, mock_db):
        """3.1.1.1 accessible_org_ids で organization_id を絞り込む"""
        # Arrange
        mock_db.session.query.return_value.filter.return_value.order_by.return_value.all.return_value = []
        from iot_app.services.customer_dashboard.common import get_organizations
        from iot_app.models.organization import OrganizationMaster

        # Act
        get_organizations([1, 2])

        # Assert
        filter_args = mock_db.session.query.return_value.filter.call_args[0]
        in_expr = next(f for f in filter_args if hasattr(f, 'right') and getattr(f.right, 'expanding', False))
        assert in_expr.left == OrganizationMaster.organization_id
        assert in_expr.right.value == [1, 2]


# ---------------------------------------------------------------------------
# get_devices
# ---------------------------------------------------------------------------

@pytest.mark.unit
class TestGetDevices:
    """観点: 3.1.4（件数）, 2.2.2（存在なし）

    使用ルート:
        GET  /analysis/customer-dashboard（初期表示）

    ワークフロー仕様書 § ダッシュボード初期表示 ⑧ デバイス選択肢取得
    organization_id に紐づく device_master レコードを返す（プルダウン用）
    ユーザー設定の organization_id が 0 以外の場合のみ呼ばれる
    """

    @patch(f'{MODULE}.db')
    def test_returns_devices_for_organization(self, mock_db):
        """3.1.4.1 organization_id に一致するデバイスリストを返す"""
        # Arrange
        mock_device1 = MagicMock()
        mock_device2 = MagicMock()
        mock_db.session.query.return_value.filter.return_value.order_by.return_value.all.return_value = [
            mock_device1, mock_device2
        ]
        from iot_app.services.customer_dashboard.common import get_devices

        # Act
        result = get_devices(1)

        # Assert
        assert result == [mock_device1, mock_device2]

    @patch(f'{MODULE}.db')
    def test_returns_empty_list_when_no_devices(self, mock_db):
        """2.2.2 organization_id に一致するデバイスが存在しない場合: 空リストを返す"""
        # Arrange
        mock_db.session.query.return_value.filter.return_value.order_by.return_value.all.return_value = []
        from iot_app.services.customer_dashboard.common import get_devices

        # Act
        result = get_devices(999)

        # Assert
        assert result == []


# ---------------------------------------------------------------------------
# get_dashboard_update_date / get_group_update_date / get_gadget_update_date
# ---------------------------------------------------------------------------

@pytest.mark.unit
class TestGetDashboardUpdateDate:
    """楽観ロック用: ダッシュボードの update_date を返す"""

    @patch(f'{MODULE}.db')
    def test_returns_update_date(self, mock_db):
        """update_date が返る"""
        from datetime import datetime
        expected = datetime(2024, 1, 1, 12, 0, 0)
        mock_db.session.query.return_value.filter.return_value.scalar.return_value = expected
        from iot_app.services.customer_dashboard.common import get_dashboard_update_date

        result = get_dashboard_update_date('test-uuid')

        assert result == expected

    @patch(f'{MODULE}.db')
    def test_returns_none_when_not_found(self, mock_db):
        """存在しない UUID の場合: None を返す"""
        mock_db.session.query.return_value.filter.return_value.scalar.return_value = None
        from iot_app.services.customer_dashboard.common import get_dashboard_update_date

        result = get_dashboard_update_date('nonexistent-uuid')

        assert result is None


@pytest.mark.unit
class TestGetGroupUpdateDate:
    """楽観ロック用: グループの update_date を返す"""

    @patch(f'{MODULE}.db')
    def test_returns_update_date(self, mock_db):
        """update_date が返る"""
        from datetime import datetime
        expected = datetime(2024, 6, 1, 0, 0, 0)
        mock_db.session.query.return_value.filter.return_value.scalar.return_value = expected
        from iot_app.services.customer_dashboard.common import get_group_update_date

        result = get_group_update_date('test-group-uuid')

        assert result == expected

    @patch(f'{MODULE}.db')
    def test_returns_none_when_not_found(self, mock_db):
        """存在しない UUID の場合: None を返す"""
        mock_db.session.query.return_value.filter.return_value.scalar.return_value = None
        from iot_app.services.customer_dashboard.common import get_group_update_date

        result = get_group_update_date('nonexistent-uuid')

        assert result is None


@pytest.mark.unit
class TestGetGadgetUpdateDate:
    """楽観ロック用: ガジェットの update_date を返す"""

    @patch(f'{MODULE}.db')
    def test_returns_update_date(self, mock_db):
        """update_date が返る"""
        from datetime import datetime
        expected = datetime(2024, 12, 31, 23, 59, 59)
        mock_db.session.query.return_value.filter.return_value.scalar.return_value = expected
        from iot_app.services.customer_dashboard.common import get_gadget_update_date

        result = get_gadget_update_date('test-gadget-uuid')

        assert result == expected

    @patch(f'{MODULE}.db')
    def test_returns_none_when_not_found(self, mock_db):
        """存在しない UUID の場合: None を返す"""
        mock_db.session.query.return_value.filter.return_value.scalar.return_value = None
        from iot_app.services.customer_dashboard.common import get_gadget_update_date

        result = get_gadget_update_date('nonexistent-uuid')

        assert result is None


# ---------------------------------------------------------------------------
# get_gadget_type_id_by_name
# ---------------------------------------------------------------------------

@pytest.mark.unit
class TestGetGadgetTypeIdByName:
    """観点: 2.2.1（存在あり）, 2.2.2（存在なし）, 2.2.3（論理削除済み）

    使用ルート:
        GET  /analysis/customer-dashboard（初期表示: gadget_type_ids 構築）

    ガジェット種別名から gadget_type_id を返す。
    delete_flag=False のレコードのみ対象とする。
    """

    @patch(f'{MODULE}.db')
    def test_returns_gadget_type_id_when_found(self, mock_db):
        """2.2.1 ガジェット種別名が存在する場合: gadget_type_id を返す"""
        # Arrange
        mock_result = MagicMock()
        mock_result.gadget_type_id = 6
        mock_db.session.query.return_value.filter_by.return_value.first.return_value = mock_result
        from iot_app.services.customer_dashboard.common import get_gadget_type_id_by_name

        # Act
        result = get_gadget_type_id_by_name('棒グラフ')

        # Assert
        assert result == 6

    @patch(f'{MODULE}.db')
    def test_returns_none_when_not_found(self, mock_db):
        """2.2.2 ガジェット種別名が存在しない場合: None を返す"""
        # Arrange
        mock_db.session.query.return_value.filter_by.return_value.first.return_value = None
        from iot_app.services.customer_dashboard.common import get_gadget_type_id_by_name

        # Act
        result = get_gadget_type_id_by_name('存在しない種別')

        # Assert
        assert result is None

    @patch(f'{MODULE}.db')
    def test_returns_none_when_logically_deleted(self, mock_db):
        """2.2.3 delete_flag=True のレコードのみ存在する場合: None を返す"""
        # Arrange
        # delete_flag=False フィルタにより論理削除済みレコードはヒットしない
        mock_db.session.query.return_value.filter_by.return_value.first.return_value = None
        from iot_app.services.customer_dashboard.common import get_gadget_type_id_by_name

        # Act
        result = get_gadget_type_id_by_name('棒グラフ')

        # Assert
        assert result is None


# ---------------------------------------------------------------------------
# get_gadget_type
# ---------------------------------------------------------------------------

@pytest.mark.unit
class TestGetGadgetType:
    """gadget_uuid から gadget_type_name を返す

    使用ルート:
        POST /analysis/customer-dashboard/gadgets/<gadget_uuid>/data
        GET  /analysis/customer-dashboard/gadgets/<gadget_uuid>?export=csv
    """

    @patch(f'{MODULE}.db')
    def test_returns_gadget_type_name(self, mock_db):
        """2.3.1 gadget_uuid が存在する場合: gadget_type_name を返す"""
        # Arrange
        mock_row = MagicMock()
        mock_row.gadget_type_name = 'timeline'
        (
            mock_db.session.query.return_value
            .join.return_value
            .filter.return_value
            .first.return_value
        ) = mock_row
        from iot_app.services.customer_dashboard.common import get_gadget_type

        # Act
        result = get_gadget_type('test-uuid-1234')

        # Assert
        assert result == 'timeline'

    @patch(f'{MODULE}.db')
    def test_returns_none_when_not_found(self, mock_db):
        """2.3.2 gadget_uuid が存在しない場合: None を返す"""
        # Arrange
        (
            mock_db.session.query.return_value
            .join.return_value
            .filter.return_value
            .first.return_value
        ) = None
        from iot_app.services.customer_dashboard.common import get_gadget_type

        # Act
        result = get_gadget_type('non-existent-uuid')

        # Assert
        assert result is None

    @patch(f'{MODULE}.db')
    def test_returns_none_when_logically_deleted(self, mock_db):
        """2.3.3 delete_flag=True のガジェットのみ存在する場合: None を返す"""
        # Arrange
        # delete_flag=False フィルタにより論理削除済みレコードはヒットしない
        (
            mock_db.session.query.return_value
            .join.return_value
            .filter.return_value
            .first.return_value
        ) = None
        from iot_app.services.customer_dashboard.common import get_gadget_type

        # Act
        result = get_gadget_type('deleted-uuid-5678')

        # Assert
        assert result is None
