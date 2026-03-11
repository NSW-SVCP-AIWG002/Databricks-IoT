"""
顧客作成ダッシュボード共通機能 - 単体テスト
対象: src/iot_app/services/customer_dashboard_service.py
"""

import pytest
from unittest.mock import MagicMock, patch, call

MODULE = 'iot_app.services.customer_dashboard_service'


# ---------------------------------------------------------------------------
# get_accessible_organizations
# ---------------------------------------------------------------------------

@pytest.mark.unit
class TestGetAccessibleOrganizations:
    """観点: 3.1.1（フィルタ条件）, 3.1.4（件数）

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
        from iot_app.services.customer_dashboard_service import get_accessible_organizations

        # Act
        result = get_accessible_organizations(1)

        # Assert
        assert result == [10, 20, 30]

    @patch(f'{MODULE}.db')
    def test_returns_empty_list_when_no_children(self, mock_db):
        """3.1.4.2 データなし: 空リストを返す"""
        # Arrange
        mock_db.session.query.return_value.filter.return_value.all.return_value = []
        from iot_app.services.customer_dashboard_service import get_accessible_organizations

        # Act
        result = get_accessible_organizations(999)

        # Assert
        assert result == []

    @patch(f'{MODULE}.db')
    def test_filters_by_parent_organization_id(self, mock_db):
        """3.1.1.1 フィルタ条件: parent_organization_id で絞り込む"""
        # Arrange
        from iot_app.services.customer_dashboard_service import (
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


# ---------------------------------------------------------------------------
# get_dashboard_user_setting
# ---------------------------------------------------------------------------

@pytest.mark.unit
class TestGetDashboardUserSetting:
    """観点: 2.2.1（存在あり）, 2.2.2（存在なし）

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
        from iot_app.services.customer_dashboard_service import get_dashboard_user_setting

        # Act
        result = get_dashboard_user_setting('user-001')

        # Assert
        assert result is mock_setting

    @patch(f'{MODULE}.db')
    def test_returns_none_when_not_exists(self, mock_db):
        """2.2.2 ユーザー設定が存在しない場合: None を返す"""
        # Arrange
        mock_db.session.query.return_value.filter.return_value.first.return_value = None
        from iot_app.services.customer_dashboard_service import get_dashboard_user_setting

        # Act
        result = get_dashboard_user_setting('user-not-exist')

        # Assert
        assert result is None


# ---------------------------------------------------------------------------
# upsert_dashboard_user_setting
# ---------------------------------------------------------------------------

@pytest.mark.unit
class TestUpsertDashboardUserSetting:
    """観点: 3.2.1.1（新規登録）, 3.3.1.1（更新）

    ワークフロー仕様書 § ダッシュボード登録 ② ユーザー設定更新
    INSERT ON DUPLICATE KEY UPDATE パターン（UPSERT）
    """

    @patch(f'{MODULE}.db')
    def test_inserts_when_no_existing_setting(self, mock_db):
        """3.2.1.1 ユーザー設定が存在しない場合: INSERTする"""
        # Arrange
        mock_db.session.query.return_value.filter.return_value.first.return_value = None
        from iot_app.services.customer_dashboard_service import upsert_dashboard_user_setting

        # Act
        upsert_dashboard_user_setting('user-001', 1)

        # Assert
        mock_db.session.add.assert_called_once()
        added_obj = mock_db.session.add.call_args[0][0]
        assert added_obj.organization_id == 0
        assert added_obj.device_id == 0

    @patch(f'{MODULE}.db')
    def test_updates_when_existing_setting(self, mock_db):
        """3.3.1.1 ユーザー設定が存在する場合: dashboard_id を更新する"""
        # Arrange
        mock_setting = MagicMock()
        mock_setting.dashboard_id = 1
        mock_db.session.query.return_value.filter.return_value.first.return_value = mock_setting
        from iot_app.services.customer_dashboard_service import upsert_dashboard_user_setting

        # Act
        upsert_dashboard_user_setting('user-001', 99)

        # Assert
        assert mock_setting.dashboard_id == 99
        mock_db.session.add.assert_not_called()


# ---------------------------------------------------------------------------
# get_dashboards
# ---------------------------------------------------------------------------

@pytest.mark.unit
class TestGetDashboards:
    """観点: 3.1.1.1（フィルタ条件）, 3.1.4.1/3.1.4.2（件数）

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
        from iot_app.services.customer_dashboard_service import get_dashboards

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
        from iot_app.services.customer_dashboard_service import get_dashboards

        # Act
        result = get_dashboards([1])

        # Assert
        assert result == []

    @patch(f'{MODULE}.db')
    def test_returns_empty_when_accessible_org_ids_empty(self, mock_db):
        """3.1.1.1 accessible_org_ids が空: ダッシュボードなし"""
        # Arrange
        from iot_app.services.customer_dashboard_service import get_dashboards

        # Act
        result = get_dashboards([])

        # Assert
        assert result == []
        mock_db.session.query.assert_not_called()


# ---------------------------------------------------------------------------
# get_first_dashboard
# ---------------------------------------------------------------------------

@pytest.mark.unit
class TestGetFirstDashboard:
    """観点: 3.1.4.1/3.1.4.2（件数）

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
        from iot_app.services.customer_dashboard_service import get_first_dashboard

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
        from iot_app.services.customer_dashboard_service import get_first_dashboard

        # Act
        result = get_first_dashboard([1])

        # Assert
        assert result is None


# ---------------------------------------------------------------------------
# check_dashboard_access
# ---------------------------------------------------------------------------

@pytest.mark.unit
class TestCheckDashboardAccess:
    """観点: 2.2.1/2.2.2/2.2.3（存在チェック）, 1.2.1/1.2.2（スコープ制限）

    ワークフロー仕様書 § ダッシュボード表示切替 データスコープ制限チェック
    dashboard_uuid と accessible_org_ids が一致するレコードを返す
    """

    @patch(f'{MODULE}.db')
    def test_returns_dashboard_when_accessible(self, mock_db):
        """2.2.1 / 1.2.1 スコープ内ダッシュボード: レコードを返す"""
        # Arrange
        mock_dash = MagicMock()
        mock_db.session.query.return_value.filter.return_value.first.return_value = mock_dash
        from iot_app.services.customer_dashboard_service import check_dashboard_access

        # Act
        result = check_dashboard_access('dash-uuid-001', [1, 2])

        # Assert
        assert result is mock_dash

    @patch(f'{MODULE}.db')
    def test_returns_none_when_not_found(self, mock_db):
        """2.2.2 ダッシュボードが存在しない場合: None を返す"""
        # Arrange
        mock_db.session.query.return_value.filter.return_value.first.return_value = None
        from iot_app.services.customer_dashboard_service import check_dashboard_access

        # Act
        result = check_dashboard_access('no-such-uuid', [1, 2])

        # Assert
        assert result is None

    @patch(f'{MODULE}.db')
    def test_returns_none_when_out_of_scope(self, mock_db):
        """1.2.2 / 2.2.3 アクセス可能スコープ外: None を返す"""
        # Arrange
        mock_db.session.query.return_value.filter.return_value.first.return_value = None
        from iot_app.services.customer_dashboard_service import check_dashboard_access

        # Act
        result = check_dashboard_access('dash-uuid-001', [99])

        # Assert
        assert result is None


# ---------------------------------------------------------------------------
# create_dashboard
# ---------------------------------------------------------------------------

@pytest.mark.unit
class TestCreateDashboard:
    """観点: 3.2.1.1（登録）, 3.2.2.1（uuid・監査項目の自動設定）

    ワークフロー仕様書 § ダッシュボード登録 ① ダッシュボード登録
    dashboard_uuid, creator, modifier を自動付与して INSERT する
    """

    @patch(f'{MODULE}.db')
    def test_adds_dashboard_to_session(self, mock_db):
        """3.2.1.1 ダッシュボードを db.session.add する"""
        # Arrange
        from iot_app.services.customer_dashboard_service import create_dashboard

        # Act
        create_dashboard('テストダッシュボード', organization_id=1, user_id='user-001')

        # Assert
        mock_db.session.add.assert_called_once()

    @patch(f'{MODULE}.db')
    def test_sets_uuid_automatically(self, mock_db):
        """3.2.2.1 dashboard_uuid が自動生成される（UUID形式・36文字）"""
        # Arrange
        from iot_app.services.customer_dashboard_service import create_dashboard

        # Act
        create_dashboard('テストダッシュボード', organization_id=1, user_id='user-001')
        added_obj = mock_db.session.add.call_args[0][0]

        # Assert
        assert added_obj.dashboard_uuid is not None
        assert len(str(added_obj.dashboard_uuid)) == 36

    @patch(f'{MODULE}.db')
    def test_sets_creator_and_modifier(self, mock_db):
        """3.2.2.1 creator / modifier にログインユーザーIDが設定される"""
        # Arrange
        from iot_app.services.customer_dashboard_service import create_dashboard

        # Act
        create_dashboard('テストダッシュボード', organization_id=1, user_id='user-001')
        added_obj = mock_db.session.add.call_args[0][0]

        # Assert
        assert added_obj.creator == 'user-001'
        assert added_obj.modifier == 'user-001'


# ---------------------------------------------------------------------------
# get_dashboard_groups
# ---------------------------------------------------------------------------

@pytest.mark.unit
class TestGetDashboardGroups:
    """観点: 3.1.4.1/3.1.4.2（件数）

    ワークフロー仕様書 § ダッシュボード初期表示 ⑤ ダッシュボードグループ一覧取得
    dashboard_id に紐づくグループを display_order 昇順で返す
    """

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
        from iot_app.services.customer_dashboard_service import get_dashboard_groups

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
        from iot_app.services.customer_dashboard_service import get_dashboard_groups

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

    ワークフロー仕様書 § ダッシュボードグループ登録 ① ダッシュボードグループ登録
    """

    @patch(f'{MODULE}.db')
    def test_adds_group_to_session(self, mock_db):
        """3.2.1.1 ダッシュボードグループを db.session.add する"""
        # Arrange
        from iot_app.services.customer_dashboard_service import create_dashboard_group

        # Act
        create_dashboard_group(
            group_name='グループA',
            dashboard_id=1,
            user_id='user-001',
        )

        # Assert
        mock_db.session.add.assert_called_once()

    @patch(f'{MODULE}.db')
    def test_sets_creator_and_modifier(self, mock_db):
        """3.2.2.1 creator / modifier にログインユーザーIDが設定される"""
        # Arrange
        from iot_app.services.customer_dashboard_service import create_dashboard_group

        # Act
        create_dashboard_group('グループA', dashboard_id=1, user_id='user-001')
        added_obj = mock_db.session.add.call_args[0][0]

        # Assert
        assert added_obj.creator == 'user-001'
        assert added_obj.modifier == 'user-001'

    @patch(f'{MODULE}.db')
    def test_sets_uuid_automatically(self, mock_db):
        """3.2.2.1 dashboard_group_uuid が自動生成される（UUID形式・36文字）"""
        # Arrange
        from iot_app.services.customer_dashboard_service import create_dashboard_group

        # Act
        create_dashboard_group('グループA', dashboard_id=1, user_id='user-001')
        added_obj = mock_db.session.add.call_args[0][0]

        # Assert
        assert added_obj.dashboard_group_uuid is not None
        assert len(str(added_obj.dashboard_group_uuid)) == 36


# ---------------------------------------------------------------------------
# get_gadgets_by_groups
# ---------------------------------------------------------------------------

@pytest.mark.unit
class TestGetGadgetsByGroups:
    """観点: 3.1.4.1（件数）, 3.1.2.1（空入力時の早期リターン）

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
        from iot_app.services.customer_dashboard_service import get_gadgets_by_groups

        # Act
        result = get_gadgets_by_groups([10, 20])

        # Assert
        assert result == [mock_gadget1]

    @patch(f'{MODULE}.db')
    def test_returns_empty_without_db_access_when_group_ids_empty(self, mock_db):
        """3.1.2.1 group_ids が空: DBアクセスせず空リストを返す"""
        # Arrange
        from iot_app.services.customer_dashboard_service import get_gadgets_by_groups

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
        from iot_app.services.customer_dashboard_service import get_gadget_types

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
        from iot_app.services.customer_dashboard_service import get_gadget_types

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
        mock_db.session.query.return_value.filter.return_value.first.return_value = mock_gadget
        from iot_app.services.customer_dashboard_service import check_gadget_access

        # Act
        result = check_gadget_access('gadget-uuid-001', [1, 2])

        # Assert
        assert result is mock_gadget

    @patch(f'{MODULE}.db')
    def test_returns_none_when_not_found(self, mock_db):
        """2.2.2 ガジェットが存在しない場合: None を返す"""
        # Arrange
        mock_db.session.query.return_value.filter.return_value.first.return_value = None
        from iot_app.services.customer_dashboard_service import check_gadget_access

        # Act
        result = check_gadget_access('no-such-uuid', [1, 2])

        # Assert
        assert result is None

    @patch(f'{MODULE}.db')
    def test_returns_none_when_out_of_scope(self, mock_db):
        """1.2.2 / 2.2.3 アクセス可能スコープ外: None を返す"""
        # Arrange
        mock_db.session.query.return_value.filter.return_value.first.return_value = None
        from iot_app.services.customer_dashboard_service import check_gadget_access

        # Act
        result = check_gadget_access('gadget-uuid-001', [99])

        # Assert
        assert result is None


# ---------------------------------------------------------------------------
# save_layout
# ---------------------------------------------------------------------------

@pytest.mark.unit
class TestSaveLayout:
    """観点: 3.3.1.1（更新）, 2.3.2（エラー時ロールバック）

    ワークフロー仕様書 § レイアウト保存
    各ガジェットの position_x/y, display_order を更新する。
    gadget_size は変更しない（登録時固定）。
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
        from iot_app.services.customer_dashboard_service import save_layout

        # Act
        save_layout(layout_data, modifier='user-001')

        # Assert
        assert mock_gadget.position_x == 0
        assert mock_gadget.position_y == 1
        assert mock_gadget.display_order == 0
        assert mock_gadget.modifier == 'user-001'
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
        from iot_app.services.customer_dashboard_service import save_layout

        # Act
        save_layout(layout_data, modifier='user-001')

        # Assert
        assert mock_gadget.gadget_size == 0

    @patch(f'{MODULE}.db')
    def test_rollbacks_on_exception(self, mock_db):
        """2.3.2 DB エラー時に db.session.rollback() を呼ぶ"""
        # Arrange
        mock_db.session.query.side_effect = Exception('DB error')
        layout_data = [
            {'gadget_uuid': 'g-001', 'position_x': 0, 'position_y': 0, 'display_order': 0}
        ]
        from iot_app.services.customer_dashboard_service import save_layout

        # Act
        with pytest.raises(Exception):
            save_layout(layout_data, modifier='user-001')

        # Assert
        mock_db.session.rollback.assert_called_once()
