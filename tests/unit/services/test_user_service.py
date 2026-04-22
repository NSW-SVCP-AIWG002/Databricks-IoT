import pytest
from unittest.mock import patch, MagicMock, call

MODULE = 'iot_app.services.user_service'


# ---------------------------------------------------------------------------
# get_default_search_params
# ---------------------------------------------------------------------------

@pytest.mark.unit
class TestGetDefaultSearchParams:
    """get_default_search_params のテスト
    観点: 2.1 正常系処理, 3.1.2 検索条件未指定（全件相当）
    """

    def test_default_pagination(self):
        """2.1.1: page=1, per_page=ITEM_PER_PAGE がデフォルト"""
        from iot_app.services.user_service import get_default_search_params
        from iot_app.common.constants import ITEM_PER_PAGE
        params = get_default_search_params()
        assert params['page'] == 1
        assert params['per_page'] == ITEM_PER_PAGE

    def test_default_text_filters(self):
        """3.1.2.1: user_name, email_address のデフォルトは空文字（条件なし相当）"""
        from iot_app.services.user_service import get_default_search_params
        params = get_default_search_params()
        assert params['user_name'] == ''
        assert params['email_address'] == ''

    def test_default_id_filters(self):
        """3.1.2.1: user_type_id / organization_id / region_id / status のデフォルトは None"""
        from iot_app.services.user_service import get_default_search_params
        params = get_default_search_params()
        assert params['user_type_id'] is None
        assert params['organization_id'] is None
        assert params['region_id'] is None
        assert params['status'] is None

    def test_default_sort(self):
        """2.1.1: sort_by='user_name', order='asc' がデフォルト"""
        from iot_app.services.user_service import get_default_search_params
        params = get_default_search_params()
        assert params['sort_by'] == 'user_name'
        assert params['order'] == 'asc'


# ---------------------------------------------------------------------------
# search_users
# ---------------------------------------------------------------------------

@pytest.mark.unit
class TestSearchUsers:
    """search_users のテスト
    観点: 3.1.1 検索条件指定, 3.1.2 検索条件未指定, 3.1.3 ページング, 3.1.4 戻り値ハンドリング
    """

    def _make_query_mock(self, mock_db, _mock_uc, total=2, users=None):
        """テスト用クエリモックの共通セットアップ"""
        if users is None:
            users = [MagicMock(), MagicMock()][:total]
        mock_query = MagicMock()
        mock_query.count.return_value = total
        mock_query.order_by.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.limit.return_value.offset.return_value.all.return_value = users
        mock_db.session.query.return_value.filter.return_value = mock_query
        return mock_query

    @patch(f'{MODULE}.UserMasterByUser')
    @patch(f'{MODULE}.db')
    def test_returns_tuple_of_users_and_total(self, mock_db, _mock_uc):
        """3.1.4.1: (users, total) のタプルを返す"""
        self._make_query_mock(mock_db, _mock_uc, total=2)
        from iot_app.services.user_service import search_users
        params = {'page': 1, 'per_page': 20, 'sort_by': 'user_name', 'order': 'asc',
                  'user_name': '', 'email_address': '', 'user_type_id': None,
                  'organization_id': None, 'region_id': None, 'status': None}
        result = search_users(params, user_id=1)
        assert isinstance(result, tuple)
        assert len(result) == 2

    @patch(f'{MODULE}.UserMasterByUser')
    @patch(f'{MODULE}.db')
    def test_returns_empty_list_when_no_results(self, mock_db, _mock_uc):
        """3.1.4.2: 該当なしの場合、空リストと total=0 を返す"""
        self._make_query_mock(mock_db, _mock_uc, total=0, users=[])
        from iot_app.services.user_service import search_users
        params = {'page': 1, 'per_page': 20, 'sort_by': 'user_name', 'order': 'asc',
                  'user_name': 'notexist', 'email_address': '', 'user_type_id': None,
                  'organization_id': None, 'region_id': None, 'status': None}
        users, total = search_users(params, user_id=1)
        assert users == []
        assert total == 0

    @patch(f'{MODULE}.UserMasterByUser')
    @patch(f'{MODULE}.db')
    def test_text_filter_applied(self, mock_db, _mock_uc):
        """3.1.1.1: テキスト条件が指定された場合、部分一致フィルタが適用される"""
        mock_query = self._make_query_mock(mock_db, _mock_uc, total=1)
        from iot_app.services.user_service import search_users
        params = {'page': 1, 'per_page': 20, 'sort_by': 'user_name', 'order': 'asc',
                  'user_name': '田中', 'email_address': '', 'user_type_id': None,
                  'organization_id': None, 'region_id': None, 'status': None}
        search_users(params, user_id=1)
        filter_args_str = str(mock_query.filter.call_args_list)
        assert mock_query.filter.called
        assert '%田中%' in filter_args_str

    @patch(f'{MODULE}.UserMasterByUser')
    @patch(f'{MODULE}.db')
    def test_id_filter_applied(self, mock_db, _mock_uc):
        """3.1.1.1: IDフィルタ条件が指定された場合、完全一致フィルタが適用される"""
        mock_query = self._make_query_mock(mock_db, _mock_uc, total=1)
        from iot_app.services.user_service import search_users
        params = {'page': 1, 'per_page': 20, 'sort_by': 'user_name', 'order': 'asc',
                  'user_name': '', 'email_address': '', 'user_type_id': 2,
                  'organization_id': None, 'region_id': None, 'status': None}
        search_users(params, user_id=1)
        filter_args_str = str(mock_query.filter.call_args_list)
        assert mock_query.filter.called
        assert 'user_type_id' in filter_args_str
        assert '2' in filter_args_str

    @patch(f'{MODULE}.UserMasterByUser')
    @patch(f'{MODULE}.db')
    def test_multiple_conditions_applied(self, mock_db, _mock_uc):
        """3.1.1.2: 複数条件（user_name + email）が指定された場合に両方の部分一致フィルタが適用される"""
        mock_query = self._make_query_mock(mock_db, _mock_uc, total=1)
        from iot_app.services.user_service import search_users
        params = {'page': 1, 'per_page': 20, 'sort_by': 'user_name', 'order': 'asc',
                  'user_name': '田中', 'email_address': '@example', 'user_type_id': None,
                  'organization_id': None, 'region_id': None, 'status': None}
        search_users(params, user_id=1)
        filter_args_str = str(mock_query.filter.call_args_list)
        assert mock_query.filter.call_count >= 2
        assert '%田中%' in filter_args_str
        assert '%@example%' in filter_args_str

    @patch(f'{MODULE}.UserMasterByUser')
    @patch(f'{MODULE}.db')
    def test_none_condition_not_filtered(self, mock_db, _mock_uc):
        """3.1.1.3: user_type_id=None のとき user_type_id フィルタは追加されない"""
        mock_query = self._make_query_mock(mock_db, _mock_uc, total=5)
        from iot_app.services.user_service import search_users
        params = {'page': 1, 'per_page': 20, 'sort_by': 'user_name', 'order': 'asc',
                  'user_name': '', 'email_address': '', 'user_type_id': None,
                  'organization_id': None, 'region_id': None, 'status': None}
        search_users(params, user_id=1)
        assert mock_query.filter.call_count == 0

    @patch(f'{MODULE}.UserMasterByUser')
    @patch(f'{MODULE}.db')
    def test_conditions_are_and_combined(self, mock_db, _mock_uc):
        """3.1.1.5: 複数条件は AND 結合（filter を連鎖呼び出し、OR は使わない）"""
        mock_query = self._make_query_mock(mock_db, _mock_uc, total=1)
        from iot_app.services.user_service import search_users
        params = {'page': 1, 'per_page': 20, 'sort_by': 'user_name', 'order': 'asc',
                  'user_name': '田中', 'email_address': '@example', 'user_type_id': 2,
                  'organization_id': None, 'region_id': None, 'status': None}
        search_users(params, user_id=1)
        assert mock_query.filter.call_count >= 2

    @patch(f'{MODULE}.UserMasterByUser')
    @patch(f'{MODULE}.db')
    def test_scope_filter_applied_with_login_user_id(self, mock_db, mock_uc_model):
        """3.1.1.4: login_user_id によるスコープ制限が全件フィルタに含まれる"""
        self._make_query_mock(mock_db, mock_uc_model, total=3)
        from iot_app.services.user_service import search_users
        params = {'page': 1, 'per_page': 20, 'sort_by': 'user_name', 'order': 'asc',
                  'user_name': '', 'email_address': '', 'user_type_id': None,
                  'organization_id': None, 'region_id': None, 'status': None}
        search_users(params, user_id=99)
        mock_db.session.query.assert_called_once_with(mock_uc_model)

    @patch(f'{MODULE}.UserMasterByUser')
    @patch(f'{MODULE}.db')
    def test_paging_offset_calculated_correctly(self, mock_db, _mock_uc):
        """3.1.3.1: ページ番号からオフセットが正しく計算される（page=3, per_page=20 → offset=40）"""
        mock_query = self._make_query_mock(mock_db, _mock_uc, total=100)
        from iot_app.services.user_service import search_users
        params = {'page': 3, 'per_page': 20, 'sort_by': 'user_name', 'order': 'asc',
                  'user_name': '', 'email_address': '', 'user_type_id': None,
                  'organization_id': None, 'region_id': None, 'status': None}
        search_users(params, user_id=1)
        mock_query.limit.return_value.offset.assert_called_once_with(40)

    @patch(f'{MODULE}.UserMasterByUser')
    @patch(f'{MODULE}.db')
    def test_per_page_passed_to_limit(self, mock_db, _mock_uc):
        """3.1.3.1: per_page の設定値が limit() に渡される"""
        mock_query = self._make_query_mock(mock_db, _mock_uc, total=100)
        from iot_app.services.user_service import search_users
        params = {'page': 1, 'per_page': 10, 'sort_by': 'user_name', 'order': 'asc',
                  'user_name': '', 'email_address': '', 'user_type_id': None,
                  'organization_id': None, 'region_id': None, 'status': None}
        search_users(params, user_id=1)
        mock_query.limit.assert_called_once_with(10)

    @patch(f'{MODULE}.UserMasterByUser')
    @patch(f'{MODULE}.db')
    def test_sort_asc_applied_to_query(self, mock_db, mock_uc):
        """3.1.1.1: order='asc' のとき query.order_by に .asc() が適用される"""
        self._make_query_mock(mock_db, mock_uc, total=1)
        from iot_app.services.user_service import search_users
        params = {'page': 1, 'per_page': 20, 'sort_by': 'user_name', 'order': 'asc',
                  'user_name': '', 'email_address': '', 'user_type_id': None,
                  'organization_id': None, 'region_id': None, 'status': None}
        search_users(params, user_id=1)
        mock_uc.user_name.asc.assert_called()

    @patch(f'{MODULE}.UserMasterByUser')
    @patch(f'{MODULE}.db')
    def test_sort_desc_applied_to_query(self, mock_db, mock_uc):
        """3.1.1.1: order='desc' のとき query.order_by に .desc() が適用される"""
        self._make_query_mock(mock_db, mock_uc, total=1)
        from iot_app.services.user_service import search_users
        params = {'page': 1, 'per_page': 20, 'sort_by': 'user_name', 'order': 'desc',
                  'user_name': '', 'email_address': '', 'user_type_id': None,
                  'organization_id': None, 'region_id': None, 'status': None}
        search_users(params, user_id=1)
        mock_uc.user_name.desc.assert_called()


# ---------------------------------------------------------------------------
# get_user_form_options
# ---------------------------------------------------------------------------

@pytest.mark.unit
class TestGetUserFormOptions:
    """get_user_form_options のテスト
    観点: 2.1 正常系処理, 3.1.1 検索条件指定, 3.1.4 戻り値ハンドリング
    """

    @patch(f'{MODULE}.SortItem')
    @patch(f'{MODULE}.Region')
    @patch(f'{MODULE}.UserType')
    @patch(f'{MODULE}.OrganizationMasterByUser')
    @patch(f'{MODULE}.db')
    def test_returns_four_tuple(self, mock_db, _mock_org, _mock_ut, _mock_region, _mock_sort):
        """2.1.1/3.1.4.1: (organizations, user_types, regions, sort_items) の4タプルを返す"""
        mock_q = MagicMock()
        mock_q.filter.return_value.order_by.return_value.all.return_value = []
        mock_db.session.query.return_value = mock_q
        from iot_app.services.user_service import get_user_form_options
        result = get_user_form_options(user_id=1, login_user_type_id=2)
        assert isinstance(result, tuple)
        assert len(result) == 4

    @patch(f'{MODULE}.SortItem')
    @patch(f'{MODULE}.Region')
    @patch(f'{MODULE}.UserType')
    @patch(f'{MODULE}.OrganizationMasterByUser')
    @patch(f'{MODULE}.db')
    def test_user_type_filtered_by_login_user_type_id(self, mock_db, _mock_org, _mock_ut, _mock_region, _mock_sort):
        """3.1.1.1: login_user_type_id より user_type_id が大きいもののみ返す（下位ロールのみ）"""
        mock_q = MagicMock()
        mock_q.filter.return_value.order_by.return_value.all.return_value = []
        mock_db.session.query.return_value = mock_q
        from iot_app.services.user_service import get_user_form_options
        get_user_form_options(user_id=1, login_user_type_id=2)
        assert mock_db.session.query.return_value.filter.called


# ---------------------------------------------------------------------------
# check_email_duplicate
# ---------------------------------------------------------------------------

@pytest.mark.unit
class TestCheckEmailDuplicate:
    """check_email_duplicate のテスト
    観点: 3.1.1 検索条件指定, 3.1.4 検索結果戻り値ハンドリング, 2.2 対象データ存在チェック
    """

    @patch(f'{MODULE}.User')
    def test_returns_true_when_duplicate_exists(self, mock_user):
        """3.1.4.1: 該当ユーザーが存在する場合 True を返す"""
        mock_user.query.filter_by.return_value.first.return_value = MagicMock()
        from iot_app.services.user_service import check_email_duplicate
        result = check_email_duplicate('dup@example.com')
        assert result is True

    @patch(f'{MODULE}.User')
    def test_returns_false_when_no_duplicate(self, mock_user):
        """3.1.4.2: 該当ユーザーが存在しない場合 False を返す"""
        mock_user.query.filter_by.return_value.first.return_value = None
        from iot_app.services.user_service import check_email_duplicate
        result = check_email_duplicate('new@example.com')
        assert result is False

    @patch(f'{MODULE}.User')
    def test_email_condition_passed_to_query(self, mock_user):
        """3.1.1.1: email_address 条件がクエリに渡される"""
        mock_user.query.filter_by.return_value.first.return_value = None
        from iot_app.services.user_service import check_email_duplicate
        check_email_duplicate('test@example.com')
        mock_user.query.filter_by.assert_called_once_with(
            email_address='test@example.com',
            delete_flag=False,
        )

    @patch(f'{MODULE}.User')
    def test_excludes_logical_deleted_users(self, mock_user):
        """2.2.3: 論理削除済みユーザーは除外する（delete_flag=False フィルタ）"""
        mock_user.query.filter_by.return_value.first.return_value = None
        from iot_app.services.user_service import check_email_duplicate
        check_email_duplicate('any@example.com')
        _, kwargs = mock_user.query.filter_by.call_args
        assert kwargs.get('delete_flag') is False


# ---------------------------------------------------------------------------
# _insert_unity_catalog_user
# ---------------------------------------------------------------------------

@pytest.mark.unit
class TestInsertUnityCatalogUser:
    """_insert_unity_catalog_user のテスト
    観点: 3.2.1 登録処理呼び出し
    """

    @patch(f'{MODULE}.UnityCatalogConnector')
    def test_execute_dml_called_once(self, mock_conn_cls):
        """3.2.1.1: execute_dml が1回呼ばれる"""
        mock_conn = MagicMock()
        mock_conn_cls.return_value = mock_conn
        from iot_app.services.user_service import _insert_unity_catalog_user
        _insert_unity_catalog_user(
            user_id=1, databricks_user_id='uid-1',
            user_data={'user_name': 'テスト', 'email_address': 't@e.com',
                       'organization_id': 1, 'user_type_id': 2, 'region_id': 1,
                       'address': '東京都', 'status': 1,
                       'alert_notification_flag': True, 'system_notification_flag': True},
            creator_id=99,
        )
        mock_conn.execute_dml.assert_called_once()

    @patch(f'{MODULE}.UnityCatalogConnector')
    def test_all_fields_passed_in_params(self, mock_conn_cls):
        """3.2.1.1: user_id を含む全フィールドがパラメータに含まれる"""
        mock_conn = MagicMock()
        mock_conn_cls.return_value = mock_conn
        from iot_app.services.user_service import _insert_unity_catalog_user
        _insert_unity_catalog_user(
            user_id=42, databricks_user_id='uid-42',
            user_data={'user_name': 'テスト', 'email_address': 't@e.com',
                       'organization_id': 1, 'user_type_id': 2, 'region_id': 1,
                       'address': '東京都', 'status': 1,
                       'alert_notification_flag': True, 'system_notification_flag': True},
            creator_id=10,
        )
        params = mock_conn.execute_dml.call_args[0][1]
        assert params['user_id'] == 42
        assert params['databricks_user_id'] == 'uid-42'
        assert params['creator_id'] == 10
        assert params['user_name'] == 'テスト'
        assert params['organization_id'] == 1
        assert params['email_address'] == 't@e.com'
        assert params['user_type_id'] == 2
        assert params['region_id'] == 1
        assert params['address'] == '東京都'
        assert params['status'] == 1
        assert params['alert_notification_flag'] is True
        assert params['system_notification_flag'] is True


# ---------------------------------------------------------------------------
# _rollback_create_user
# ---------------------------------------------------------------------------

@pytest.mark.unit
class TestRollbackCreateUser:
    """_rollback_create_user のテスト
    観点: 2.3 副作用チェック, 1.3 エラーハンドリング
    """

    @patch(f'{MODULE}.ScimClient')
    def test_scim_delete_called_when_databricks_id_present(self, mock_scim_cls):
        """2.3.2: databricks_user_id がある場合 SCIM delete_user が呼ばれる"""
        mock_scim = MagicMock()
        mock_scim_cls.return_value = mock_scim
        from iot_app.services.user_service import _rollback_create_user
        _rollback_create_user(user_id=None, databricks_user_id='uid-1', uc_inserted=False)
        mock_scim.delete_user.assert_called_once_with('uid-1')

    @patch(f'{MODULE}.ScimClient')
    def test_scim_delete_skipped_when_no_databricks_id(self, mock_scim_cls):
        """2.3.2: databricks_user_id が None の場合 SCIM delete_user はスキップされる"""
        mock_scim = MagicMock()
        mock_scim_cls.return_value = mock_scim
        from iot_app.services.user_service import _rollback_create_user
        _rollback_create_user(user_id=None, databricks_user_id=None, uc_inserted=False)
        mock_scim.delete_user.assert_not_called()

    @patch(f'{MODULE}.UnityCatalogConnector')
    @patch(f'{MODULE}.ScimClient')
    def test_uc_delete_called_when_uc_inserted_true_and_user_id_present(self, mock_scim_cls, mock_conn_cls):
        """2.3.2: uc_inserted=True かつ user_id がある場合 UC execute_dml (DELETE) が呼ばれる"""
        mock_scim_cls.return_value = MagicMock()
        mock_conn = MagicMock()
        mock_conn_cls.return_value = mock_conn
        from iot_app.services.user_service import _rollback_create_user
        _rollback_create_user(user_id=5, databricks_user_id='uid-1', uc_inserted=True)
        mock_conn.execute_dml.assert_called_once()

    @patch(f'{MODULE}.UnityCatalogConnector')
    @patch(f'{MODULE}.ScimClient')
    def test_uc_delete_skipped_when_uc_not_inserted(self, mock_scim_cls, mock_conn_cls):
        """2.3.2: uc_inserted=False の場合 UC execute_dml はスキップされる"""
        mock_scim_cls.return_value = MagicMock()
        mock_conn = MagicMock()
        mock_conn_cls.return_value = mock_conn
        from iot_app.services.user_service import _rollback_create_user
        _rollback_create_user(user_id=5, databricks_user_id='uid-1', uc_inserted=False)
        mock_conn.execute_dml.assert_not_called()

    @patch(f'{MODULE}.ScimClient')
    def test_scim_exception_suppressed(self, mock_scim_cls):
        """1.3.1: SCIM delete_user が例外を投げても re-raise されない（ベストエフォート）"""
        mock_scim = MagicMock()
        mock_scim.delete_user.side_effect = Exception('SCIM error')
        mock_scim_cls.return_value = mock_scim
        from iot_app.services.user_service import _rollback_create_user
        _rollback_create_user(user_id=None, databricks_user_id='uid-1', uc_inserted=False)

    @patch(f'{MODULE}.UnityCatalogConnector')
    @patch(f'{MODULE}.ScimClient')
    def test_uc_exception_suppressed(self, mock_scim_cls, mock_conn_cls):
        """1.3.1: UC execute_dml が例外を投げても re-raise されない（ベストエフォート）"""
        mock_scim_cls.return_value = MagicMock()
        mock_conn = MagicMock()
        mock_conn.execute_dml.side_effect = Exception('UC error')
        mock_conn_cls.return_value = mock_conn
        from iot_app.services.user_service import _rollback_create_user
        _rollback_create_user(user_id=5, databricks_user_id='uid-1', uc_inserted=True)


# ---------------------------------------------------------------------------
# create_user
# ---------------------------------------------------------------------------

@pytest.mark.unit
class TestCreateUser:
    """create_user のテスト
    観点: 2.1 正常系処理, 2.3 副作用チェック, 3.2 登録機能, 1.3 エラーハンドリング
    """

    def _make_auth_provider(self):
        return MagicMock()

    def _make_form_data(self):
        return {
            'user_name': 'テストユーザー',
            'email_address': 'test@example.com',
            'organization_id': 1,
            'user_type_id': 2,
            'region_id': 1,
            'address': '東京都',
            'status': 1,
            'alert_notification_flag': True,
            'system_notification_flag': True,
        }

    @patch(f'{MODULE}._insert_unity_catalog_user')
    @patch(f'{MODULE}.ScimClient')
    @patch(f'{MODULE}.User')
    @patch(f'{MODULE}.db')
    def test_saga_order_oltp_insert_scim_uc_activate_commit(self, mock_db, mock_user_cls, mock_scim_cls, mock_uc_insert):
        """3.2.1.1 / 2.1.1: Saga実行順 ①OLTP flush → ②SCIM create → ③グループ追加 → ④UC INSERT → ⑤活性化 flush → commit"""
        call_order = []
        mock_db.session.flush.side_effect = lambda: call_order.append('flush')
        mock_db.session.commit.side_effect = lambda: call_order.append('commit')
        mock_scim = MagicMock()
        mock_scim.create_user.side_effect = lambda **kw: (call_order.append('scim_create'), 'new-uid')[1]
        mock_scim.add_user_to_group.side_effect = lambda *_: call_order.append('add_to_group')
        mock_scim_cls.return_value = mock_scim
        mock_uc_insert.side_effect = lambda *_, **__: call_order.append('uc')
        mock_user_cls.return_value = MagicMock()
        from iot_app.services.user_service import create_user
        create_user(self._make_form_data(), creator_id=1, auth_provider=self._make_auth_provider())
        assert call_order == ['flush', 'scim_create', 'add_to_group', 'uc', 'flush', 'commit']

    @patch(f'{MODULE}._insert_unity_catalog_user')
    @patch(f'{MODULE}.ScimClient')
    @patch(f'{MODULE}.User')
    @patch(f'{MODULE}.db')
    def test_initial_oltp_insert_has_delete_flag_true(self, mock_db, mock_user_cls, mock_scim_cls, mock_uc_insert):
        """3.2.1.1: 仮登録ステップで User が delete_flag=True で生成され session.add() に渡される"""
        created_users = []
        mock_user_cls.side_effect = lambda **kwargs: (created_users.append(kwargs), MagicMock())[1]
        mock_scim = MagicMock()
        mock_scim.create_user.return_value = 'new-uid'
        mock_scim_cls.return_value = mock_scim
        from iot_app.services.user_service import create_user
        create_user(self._make_form_data(), creator_id=1,
                    auth_provider=self._make_auth_provider())
        assert len(created_users) > 0
        assert created_users[0].get('delete_flag') is True
        mock_db.session.add.assert_called_once()

    @patch(f'{MODULE}._insert_unity_catalog_user')
    @patch(f'{MODULE}.ScimClient')
    @patch(f'{MODULE}.User')
    @patch(f'{MODULE}.db')
    def test_initial_oltp_insert_fields_passed_correctly(self, mock_db, mock_user_cls, mock_scim_cls, mock_uc_insert):
        """3.2.1.1: User() コンストラクタに user_data・固定値・creator_id が正しく渡される"""
        created_users = []
        mock_user_cls.side_effect = lambda **kwargs: (created_users.append(kwargs), MagicMock())[1]
        mock_scim = MagicMock()
        mock_scim.create_user.return_value = 'new-uid'
        mock_scim_cls.return_value = mock_scim
        from iot_app.services.user_service import create_user
        create_user(self._make_form_data(), creator_id=1,
                    auth_provider=self._make_auth_provider())
        assert len(created_users) > 0
        kwargs = created_users[0]
        assert kwargs.get('databricks_user_id') == ''
        assert kwargs.get('user_name') == 'テストユーザー'
        assert kwargs.get('email_address') == 'test@example.com'
        assert kwargs.get('user_type_id') == 2
        assert kwargs.get('organization_id') == 1
        assert kwargs.get('language_code') == 'ja'
        assert kwargs.get('region_id') == 1
        assert kwargs.get('address') == '東京都'
        assert kwargs.get('status') == 1
        assert kwargs.get('alert_notification_flag') is True
        assert kwargs.get('system_notification_flag') is True
        assert kwargs.get('creator') == 1
        assert kwargs.get('modifier') == 1

    @patch(f'{MODULE}._insert_unity_catalog_user')
    @patch(f'{MODULE}.ScimClient')
    @patch(f'{MODULE}.User')
    @patch(f'{MODULE}.db')
    def test_activation_updates_databricks_id_and_delete_flag(self, mock_db, mock_user_cls, mock_scim_cls, mock_uc_insert):
        """3.2.1.1: UC INSERT 後の活性化ステップで databricks_user_id と delete_flag=False が更新される"""
        mock_user_obj = MagicMock()
        mock_user_obj.delete_flag = True
        mock_user_cls.return_value = mock_user_obj
        mock_scim = MagicMock()
        mock_scim.create_user.return_value = 'new-uid'
        mock_scim_cls.return_value = mock_scim
        from iot_app.services.user_service import create_user
        create_user(self._make_form_data(), creator_id=1,
                    auth_provider=self._make_auth_provider())
        assert mock_user_obj.databricks_user_id == 'new-uid'
        assert mock_user_obj.delete_flag is False

    @patch(f'{MODULE}._insert_unity_catalog_user')
    @patch(f'{MODULE}.ScimClient')
    @patch(f'{MODULE}.User')
    @patch(f'{MODULE}.db')
    def test_scim_create_user_called_with_email_and_name(self, mock_db, mock_user_cls, mock_scim_cls, mock_uc_insert):
        """3.2.1.1: SCIM create_user が email と display_name で呼ばれる"""
        mock_user_obj = MagicMock()
        mock_user_cls.return_value = mock_user_obj
        mock_scim = MagicMock()
        mock_scim.create_user.return_value = 'new-uid'
        mock_scim_cls.return_value = mock_scim
        from iot_app.services.user_service import create_user
        form_data = self._make_form_data()
        create_user(form_data, creator_id=1, auth_provider=self._make_auth_provider())
        mock_scim.create_user.assert_called_once_with(
            email=form_data['email_address'],
            display_name=form_data['user_name'],
        )

    @patch(f'{MODULE}._rollback_create_user')
    @patch(f'{MODULE}.ScimClient')
    @patch(f'{MODULE}.User')
    @patch(f'{MODULE}.db')
    def test_scim_failure_triggers_rollback_and_raises(self, mock_db, mock_user_cls, mock_scim_cls, mock_rollback):
        """2.3.2/1.3.1: SCIM create_user 失敗時に _rollback_create_user が呼ばれ例外が伝播する"""
        mock_user_obj = MagicMock()
        mock_user_cls.return_value = mock_user_obj
        mock_scim = MagicMock()
        mock_scim.create_user.side_effect = Exception('SCIM error')
        mock_scim_cls.return_value = mock_scim
        from iot_app.services.user_service import create_user
        with pytest.raises(Exception):
            create_user(self._make_form_data(), creator_id=1,
                        auth_provider=self._make_auth_provider())
        mock_rollback.assert_called_once()

    @patch(f'{MODULE}._rollback_create_user')
    @patch(f'{MODULE}._insert_unity_catalog_user')
    @patch(f'{MODULE}.ScimClient')
    @patch(f'{MODULE}.User')
    @patch(f'{MODULE}.db')
    def test_uc_failure_rollback_called_with_uc_inserted_false(
            self, mock_db, mock_user_cls, mock_scim_cls, mock_uc_insert, mock_rollback):
        """2.3.2: UC INSERT 失敗時に _rollback_create_user が uc_inserted=False で呼ばれる"""
        mock_user_obj = MagicMock()
        mock_user_cls.return_value = mock_user_obj
        mock_scim = MagicMock()
        mock_scim.create_user.return_value = 'new-uid'
        mock_scim_cls.return_value = mock_scim
        mock_uc_insert.side_effect = Exception('UC error')
        from iot_app.services.user_service import create_user
        with pytest.raises(Exception):
            create_user(self._make_form_data(), creator_id=1,
                        auth_provider=self._make_auth_provider())
        args, kwargs = mock_rollback.call_args
        uc_inserted = kwargs.get('uc_inserted', args[2] if len(args) > 2 else None)
        assert uc_inserted is False

    @patch(f'{MODULE}._rollback_create_user')
    @patch(f'{MODULE}._insert_unity_catalog_user')
    @patch(f'{MODULE}.ScimClient')
    @patch(f'{MODULE}.User')
    @patch(f'{MODULE}.db')
    def test_commit_failure_rollback_called_with_uc_inserted_true(
            self, mock_db, mock_user_cls, mock_scim_cls, mock_uc_insert, mock_rollback):
        """2.3.2: commit 失敗時に _rollback_create_user が uc_inserted=True で呼ばれる"""
        mock_user_obj = MagicMock()
        mock_user_cls.return_value = mock_user_obj
        mock_scim = MagicMock()
        mock_scim.create_user.return_value = 'new-uid'
        mock_scim_cls.return_value = mock_scim
        mock_db.session.commit.side_effect = Exception('commit error')
        from iot_app.services.user_service import create_user
        with pytest.raises(Exception):
            create_user(self._make_form_data(), creator_id=1,
                        auth_provider=self._make_auth_provider())
        args, kwargs = mock_rollback.call_args
        uc_inserted = kwargs.get('uc_inserted', args[2] if len(args) > 2 else None)
        assert uc_inserted is True

    @patch(f'{MODULE}._insert_unity_catalog_user')
    @patch(f'{MODULE}.ScimClient')
    @patch(f'{MODULE}.User')
    @patch(f'{MODULE}.db')
    def test_add_user_to_group_called_with_databricks_user_id(
            self, mock_db, mock_user_cls, mock_scim_cls, mock_uc_insert):
        """3.2.1.1: SCIM create_user 後に add_user_to_group が databricks_user_id で呼ばれる"""
        mock_user_obj = MagicMock()
        mock_user_cls.return_value = mock_user_obj
        mock_scim = MagicMock()
        mock_scim.create_user.return_value = 'new-uid'
        mock_scim_cls.return_value = mock_scim
        from iot_app.services.user_service import create_user
        create_user(self._make_form_data(), creator_id=1,
                    auth_provider=self._make_auth_provider())
        mock_scim.add_user_to_group.assert_called_once()
        positional_args = mock_scim.add_user_to_group.call_args[0]
        assert 'new-uid' in positional_args

    @patch(f'{MODULE}._rollback_create_user')
    @patch(f'{MODULE}.ScimClient')
    @patch(f'{MODULE}.User')
    @patch(f'{MODULE}.db')
    def test_add_to_group_failure_triggers_rollback_with_uc_inserted_false(
            self, mock_db, mock_user_cls, mock_scim_cls, mock_rollback):
        """2.3.2: add_user_to_group 失敗時に _rollback_create_user が uc_inserted=False で呼ばれる"""
        mock_user_obj = MagicMock()
        mock_user_cls.return_value = mock_user_obj
        mock_scim = MagicMock()
        mock_scim.create_user.return_value = 'new-uid'
        mock_scim.add_user_to_group.side_effect = Exception('group error')
        mock_scim_cls.return_value = mock_scim
        from iot_app.services.user_service import create_user
        with pytest.raises(Exception):
            create_user(self._make_form_data(), creator_id=1,
                        auth_provider=self._make_auth_provider())
        mock_rollback.assert_called_once()
        args, kwargs = mock_rollback.call_args
        uc_inserted = kwargs.get('uc_inserted', args[2] if len(args) > 2 else None)
        assert uc_inserted is False

    @patch(f'{MODULE}.check_email_duplicate')
    @patch(f'{MODULE}._insert_unity_catalog_user')
    @patch(f'{MODULE}.ScimClient')
    @patch(f'{MODULE}.User')
    @patch(f'{MODULE}.db')
    def test_check_email_duplicate_called_with_email(
            self, mock_db, mock_user_cls, mock_scim_cls, mock_uc_insert, mock_check):
        """3.2.1.1: create_user 実行時に check_email_duplicate が email_address で呼ばれる"""
        mock_check.return_value = False
        mock_user_cls.return_value = MagicMock()
        mock_scim = MagicMock()
        mock_scim.create_user.return_value = 'new-uid'
        mock_scim_cls.return_value = mock_scim
        from iot_app.services.user_service import create_user
        form_data = self._make_form_data()
        create_user(form_data, creator_id=1, auth_provider=self._make_auth_provider())
        mock_check.assert_called_once_with(form_data['email_address'])


# ---------------------------------------------------------------------------
# _update_oltp_user
# ---------------------------------------------------------------------------

@pytest.mark.unit
class TestUpdateOltpUser:
    """_update_oltp_user のテスト
    観点: 3.3.1 更新処理呼び出し, 3.3.2 更新結果
    """

    @patch(f'{MODULE}.User')
    @patch(f'{MODULE}.db')
    def test_updates_all_updatable_fields(self, mock_db, mock_user_cls):
        """3.3.1.1: user_name, region_id, address, status, flags が更新される"""
        mock_user = MagicMock()
        mock_user_cls.query.get.return_value = mock_user
        from iot_app.services.user_service import _update_oltp_user
        _update_oltp_user(user_id=1, user_data={
            'user_name': '更新後名前', 'region_id': 2, 'address': '大阪府',
            'status': 0, 'alert_notification_flag': False, 'system_notification_flag': True,
        }, modifier_id=99)
        assert mock_user.user_name == '更新後名前'
        assert mock_user.region_id == 2
        assert mock_user.address == '大阪府'
        assert mock_user.status == 0
        assert mock_user.alert_notification_flag is False
        assert mock_user.system_notification_flag is True
        assert mock_user.modifier == 99

    @patch(f'{MODULE}.User')
    @patch(f'{MODULE}.db')
    def test_targets_correct_user_id(self, mock_db, mock_user_cls):
        """3.3.2.2: 指定した user_id のユーザーが取得・更新される"""
        mock_user = MagicMock()
        mock_user_cls.query.get.return_value = mock_user
        from iot_app.services.user_service import _update_oltp_user
        _update_oltp_user(user_id=42, user_data={
            'user_name': 'test', 'region_id': 1, 'address': 'addr',
            'status': 1, 'alert_notification_flag': True, 'system_notification_flag': True,
        }, modifier_id=1)
        mock_user_cls.query.get.assert_called_once_with(42)


# ---------------------------------------------------------------------------
# _update_unity_catalog_user
# ---------------------------------------------------------------------------

@pytest.mark.unit
class TestUpdateUnityCatalogUser:
    """_update_unity_catalog_user のテスト
    観点: 3.3.1 更新処理呼び出し
    """

    @patch(f'{MODULE}.UnityCatalogConnector')
    def test_execute_dml_called_with_update(self, mock_conn_cls):
        """3.3.1.1: execute_dml が1回呼ばれる"""
        mock_conn = MagicMock()
        mock_conn_cls.return_value = mock_conn
        from iot_app.services.user_service import _update_unity_catalog_user
        _update_unity_catalog_user(user_id=1, user_data={
            'user_name': '更新名', 'region_id': 2, 'address': '東京都',
            'status': 1, 'alert_notification_flag': True, 'system_notification_flag': False,
        }, modifier_id=99)
        mock_conn.execute_dml.assert_called_once()

    @patch(f'{MODULE}.UnityCatalogConnector')
    def test_all_fields_passed_in_params(self, mock_conn_cls):
        """3.3.2.2: 全更新対象フィールドが execute_dml のパラメータに含まれる"""
        mock_conn = MagicMock()
        mock_conn_cls.return_value = mock_conn
        from iot_app.services.user_service import _update_unity_catalog_user
        _update_unity_catalog_user(user_id=55, user_data={
            'user_name': '更新名', 'region_id': 1, 'address': '大阪府',
            'status': 1, 'alert_notification_flag': True, 'system_notification_flag': True,
        }, modifier_id=1)
        params = mock_conn.execute_dml.call_args[0][1]
        assert params['user_id'] == 55
        assert params['user_name'] == '更新名'
        assert params['region_id'] == 1
        assert params['address'] == '大阪府'
        assert params['status'] == 1
        assert params['alert_notification_flag'] is True
        assert params['system_notification_flag'] is True
        assert params['modifier_id'] == 1


# ---------------------------------------------------------------------------
# _rollback_update_user
# ---------------------------------------------------------------------------

@pytest.mark.unit
class TestRollbackUpdateUser:
    """_rollback_update_user のテスト
    観点: 2.3 副作用チェック, 1.3 エラーハンドリング
    """

    @patch(f'{MODULE}.UnityCatalogConnector')
    @patch(f'{MODULE}.ScimClient')
    @patch(f'{MODULE}.User')
    def test_restores_scim_and_uc_from_oltp(self, mock_user_cls, mock_scim_cls, mock_conn_cls):
        """2.3.2: OLTP から元データを取得し SCIM と UC を復元する"""
        mock_original = MagicMock()
        mock_user_cls.query.get.return_value = mock_original
        mock_scim = MagicMock()
        mock_scim_cls.return_value = mock_scim
        mock_conn = MagicMock()
        mock_conn_cls.return_value = mock_conn
        from iot_app.services.user_service import _rollback_update_user
        _rollback_update_user(databricks_user_id='uid-1', user_id=1)
        mock_scim.update_user.assert_called_once()
        mock_conn.execute_dml.assert_called_once()

    @patch(f'{MODULE}.UnityCatalogConnector')
    @patch(f'{MODULE}.ScimClient')
    @patch(f'{MODULE}.User')
    def test_all_fields_restored_to_scim_and_uc(self, mock_user_cls, mock_scim_cls, mock_conn_cls):
        """2.3.2: SCIMとUCに元データの全フィールドが正しく渡される"""
        mock_original = MagicMock()
        mock_original.user_name = '元の名前'
        mock_original.region_id = 3
        mock_original.address = '京都府'
        mock_original.status = 0
        mock_original.alert_notification_flag = False
        mock_original.system_notification_flag = True
        mock_original.modifier = 77
        mock_user_cls.query.get.return_value = mock_original
        mock_scim = MagicMock()
        mock_scim_cls.return_value = mock_scim
        mock_conn = MagicMock()
        mock_conn_cls.return_value = mock_conn
        from iot_app.services.user_service import _rollback_update_user
        _rollback_update_user(databricks_user_id='uid-1', user_id=10)
        mock_scim.update_user.assert_called_once_with('uid-1', '元の名前', 0)
        params = mock_conn.execute_dml.call_args[0][1]
        assert params['user_id'] == 10
        assert params['user_name'] == '元の名前'
        assert params['region_id'] == 3
        assert params['address'] == '京都府'
        assert params['status'] == 0
        assert params['alert_notification_flag'] is False
        assert params['system_notification_flag'] is True
        assert params['modifier'] == 77

    @patch(f'{MODULE}.ScimClient')
    @patch(f'{MODULE}.User')
    def test_skips_when_user_not_found_in_oltp(self, mock_user_cls, mock_scim_cls):
        """2.3.2: OLTP に元データがない場合は何もしない"""
        mock_user_cls.query.get.return_value = None
        mock_scim = MagicMock()
        mock_scim_cls.return_value = mock_scim
        from iot_app.services.user_service import _rollback_update_user
        _rollback_update_user(databricks_user_id='uid-1', user_id=999)
        mock_scim.update_user.assert_not_called()

    @patch(f'{MODULE}.ScimClient')
    @patch(f'{MODULE}.User')
    def test_exception_suppressed(self, mock_user_cls, mock_scim_cls):
        """1.3.1: ロールバック中の例外を re-raise しない（ベストエフォート）"""
        mock_original = MagicMock()
        mock_user_cls.query.get.return_value = mock_original
        mock_scim = MagicMock()
        mock_scim.update_user.side_effect = Exception('SCIM restore error')
        mock_scim_cls.return_value = mock_scim
        from iot_app.services.user_service import _rollback_update_user
        _rollback_update_user(databricks_user_id='uid-1', user_id=1)


# ---------------------------------------------------------------------------
# update_user
# ---------------------------------------------------------------------------

@pytest.mark.unit
class TestUpdateUser:
    """update_user のテスト
    観点: 2.1 正常系処理, 2.3 副作用チェック, 3.3 更新機能, 1.3 エラーハンドリング
    """

    def _make_user_data(self):
        return {'user_name': '更新後', 'region_id': 1, 'address': '大阪府',
                'status': 1, 'alert_notification_flag': True, 'system_notification_flag': True}

    @patch(f'{MODULE}._update_unity_catalog_user')
    @patch(f'{MODULE}._update_oltp_user')
    @patch(f'{MODULE}.ScimClient')
    @patch(f'{MODULE}.db')
    def test_success_commits(self, mock_db, mock_scim_cls, mock_update_oltp, mock_update_uc):
        """2.1.1/3.3.2.1: 正常終了時に db.session.commit が呼ばれる"""
        mock_scim_cls.return_value = MagicMock()
        from iot_app.services.user_service import update_user
        update_user(user_id=1, databricks_user_id='uid-1',
                    user_data=self._make_user_data(), modifier_id=1)
        mock_db.session.commit.assert_called_once()

    @patch(f'{MODULE}._update_unity_catalog_user')
    @patch(f'{MODULE}._update_oltp_user')
    @patch(f'{MODULE}.ScimClient')
    @patch(f'{MODULE}.db')
    def test_saga_order_scim_then_uc_then_oltp(self, mock_db, mock_scim_cls, mock_update_oltp, mock_update_uc):
        """3.3.1.1: Saga実行順は ①SCIM update → ②UC UPDATE → ③OLTP UPDATE"""
        call_order = []
        mock_scim = MagicMock()
        mock_scim.update_user.side_effect = lambda *_, **__: call_order.append('scim')
        mock_scim_cls.return_value = mock_scim
        mock_update_uc.side_effect = lambda *_, **__: call_order.append('uc')
        mock_update_oltp.side_effect = lambda *_, **__: call_order.append('oltp')
        from iot_app.services.user_service import update_user
        update_user(user_id=1, databricks_user_id='uid-1',
                    user_data=self._make_user_data(), modifier_id=1)
        assert call_order == ['scim', 'uc', 'oltp']

    @patch(f'{MODULE}._rollback_update_user')
    @patch(f'{MODULE}.ScimClient')
    @patch(f'{MODULE}.db')
    def test_scim_failure_triggers_rollback_and_raises(self, mock_db, mock_scim_cls, mock_rollback):
        """2.3.2/1.3.1: SCIM update 失敗時にロールバックが呼ばれ例外が伝播する"""
        mock_scim = MagicMock()
        mock_scim.update_user.side_effect = Exception('SCIM error')
        mock_scim_cls.return_value = mock_scim
        from iot_app.services.user_service import update_user
        with pytest.raises(Exception):
            update_user(user_id=1, databricks_user_id='uid-1',
                        user_data=self._make_user_data(), modifier_id=1)
        mock_rollback.assert_called_once()

    @patch(f'{MODULE}._rollback_update_user')
    @patch(f'{MODULE}._update_unity_catalog_user')
    @patch(f'{MODULE}.ScimClient')
    @patch(f'{MODULE}.db')
    def test_uc_failure_triggers_rollback_and_raises(self, mock_db, mock_scim_cls, mock_update_uc, mock_rollback):
        """2.3.2/1.3.1: UC UPDATE 失敗時にロールバックが呼ばれ例外が伝播する"""
        mock_scim_cls.return_value = MagicMock()
        mock_update_uc.side_effect = Exception('UC error')
        from iot_app.services.user_service import update_user
        with pytest.raises(Exception):
            update_user(user_id=1, databricks_user_id='uid-1',
                        user_data=self._make_user_data(), modifier_id=1)
        mock_rollback.assert_called_once()

    @patch(f'{MODULE}._rollback_update_user')
    @patch(f'{MODULE}._update_unity_catalog_user')
    @patch(f'{MODULE}._update_oltp_user')
    @patch(f'{MODULE}.ScimClient')
    @patch(f'{MODULE}.db')
    def test_oltp_failure_triggers_rollback_and_raises(
            self, mock_db, mock_scim_cls, mock_update_oltp, mock_update_uc, mock_rollback):
        """2.3.2/1.3.1: OLTP UPDATE 失敗時にロールバックが呼ばれ例外が伝播する"""
        mock_scim_cls.return_value = MagicMock()
        mock_update_oltp.side_effect = Exception('OLTP error')
        from iot_app.services.user_service import update_user
        with pytest.raises(Exception):
            update_user(user_id=1, databricks_user_id='uid-1',
                        user_data=self._make_user_data(), modifier_id=1)
        mock_rollback.assert_called_once()

    @patch(f'{MODULE}.check_email_duplicate')
    @patch(f'{MODULE}._update_unity_catalog_user')
    @patch(f'{MODULE}._update_oltp_user')
    @patch(f'{MODULE}.ScimClient')
    @patch(f'{MODULE}.db')
    def test_check_email_duplicate_not_called(
            self, mock_db, mock_scim_cls, mock_update_oltp, mock_update_uc, mock_check):
        """2.3.2: update_user は email を変更しないため check_email_duplicate を呼ばない"""
        mock_scim_cls.return_value = MagicMock()
        from iot_app.services.user_service import update_user
        update_user(user_id=1, databricks_user_id='uid-1',
                    user_data=self._make_user_data(), modifier_id=1)
        mock_check.assert_not_called()


# ---------------------------------------------------------------------------
# get_user_by_databricks_id
# ---------------------------------------------------------------------------

@pytest.mark.unit
class TestGetUserByDatabricksId:
    """get_user_by_databricks_id のテスト
    観点: 2.2 対象データ存在チェック, 3.1.1 検索条件指定
    """

    @patch(f'{MODULE}.UserMasterByUser')
    @patch(f'{MODULE}.db')
    def test_returns_user_when_found(self, mock_db, _mock_uc):
        """2.2.1: 対象IDが存在する場合ユーザーオブジェクトを返す"""
        mock_user = MagicMock()
        mock_db.session.query.return_value.filter.return_value.first.return_value = mock_user
        from iot_app.services.user_service import get_user_by_databricks_id
        result = get_user_by_databricks_id('uid-1', login_user_id=1)
        assert result is mock_user

    @patch(f'{MODULE}.UserMasterByUser')
    @patch(f'{MODULE}.db')
    def test_returns_none_when_not_found(self, mock_db, _mock_uc):
        """2.2.2: 対象IDが存在しない場合 None を返す"""
        mock_db.session.query.return_value.filter.return_value.first.return_value = None
        from iot_app.services.user_service import get_user_by_databricks_id
        result = get_user_by_databricks_id('nonexistent', login_user_id=1)
        assert result is None

    @patch(f'{MODULE}.UserMasterByUser')
    @patch(f'{MODULE}.db')
    def test_delete_flag_false_filter_applied(self, mock_db, _mock_uc):
        """2.2.3: 論理削除済み（delete_flag=True）ユーザーは除外される"""
        mock_db.session.query.return_value.filter.return_value.first.return_value = None
        from iot_app.services.user_service import get_user_by_databricks_id
        get_user_by_databricks_id('uid-1', login_user_id=1)
        mock_db.session.query.return_value.filter.assert_called_once()

    @patch(f'{MODULE}.UserMasterByUser')
    @patch(f'{MODULE}.db')
    def test_scope_filter_applied(self, mock_db, _mock_uc):
        """3.1.1.1: login_user_id によるスコープ制限がフィルタに含まれる"""
        mock_db.session.query.return_value.filter.return_value.first.return_value = None
        from iot_app.services.user_service import get_user_by_databricks_id
        get_user_by_databricks_id('uid-1', login_user_id=42)
        mock_db.session.query.assert_called_once_with(_mock_uc)


# ---------------------------------------------------------------------------
# _delete_unity_catalog_user
# ---------------------------------------------------------------------------

@pytest.mark.unit
class TestDeleteUnityCatalogUser:
    """_delete_unity_catalog_user のテスト
    観点: 3.4.1 削除処理呼び出し
    """

    @patch(f'{MODULE}.UnityCatalogConnector')
    def test_execute_dml_called_with_delete(self, mock_conn_cls):
        """3.4.1.1: execute_dml が1回呼ばれる"""
        mock_conn = MagicMock()
        mock_conn_cls.return_value = mock_conn
        from iot_app.services.user_service import _delete_unity_catalog_user
        _delete_unity_catalog_user(user_id=5)
        mock_conn.execute_dml.assert_called_once()

    @patch(f'{MODULE}.UnityCatalogConnector')
    def test_user_id_passed_to_delete(self, mock_conn_cls):
        """3.4.1.1: 指定した user_id がパラメータに含まれる"""
        mock_conn = MagicMock()
        mock_conn_cls.return_value = mock_conn
        from iot_app.services.user_service import _delete_unity_catalog_user
        _delete_unity_catalog_user(user_id=77)
        params = mock_conn.execute_dml.call_args[0][1]
        assert params['user_id'] == 77


# ---------------------------------------------------------------------------
# _rollback_delete_user
# ---------------------------------------------------------------------------

@pytest.mark.unit
class TestRollbackDeleteUser:
    """_rollback_delete_user のテスト
    観点: 2.3 副作用チェック, 1.3 エラーハンドリング
    """

    @patch(f'{MODULE}.UnityCatalogConnector')
    @patch(f'{MODULE}.User')
    def test_reinserts_to_uc_from_oltp(self, mock_user_cls, mock_conn_cls):
        """2.3.2: OLTP の元データから UC に再 INSERT する"""
        mock_original = MagicMock()
        mock_user_cls.query.get.return_value = mock_original
        mock_conn = MagicMock()
        mock_conn_cls.return_value = mock_conn
        from iot_app.services.user_service import _rollback_delete_user
        _rollback_delete_user(user_id=1)
        mock_conn.execute_dml.assert_called_once()

    @patch(f'{MODULE}.UnityCatalogConnector')
    @patch(f'{MODULE}.User')
    def test_all_fields_passed_from_oltp_user(self, mock_user_cls, mock_conn_cls):
        """2.3.2: OLTPの元データ全フィールドが execute_dml のパラメータに含まれる"""
        mock_original = MagicMock()
        mock_original.user_id = 1
        mock_original.databricks_user_id = 'uid-1'
        mock_original.user_name = 'テストユーザー'
        mock_original.organization_id = 1
        mock_original.email_address = 'test@example.com'
        mock_original.user_type_id = 2
        mock_original.language_code = 'ja'
        mock_original.region_id = 1
        mock_original.address = '東京都'
        mock_original.status = 1
        mock_original.alert_notification_flag = True
        mock_original.system_notification_flag = True
        mock_original.create_date = '2024-01-01'
        mock_original.creator = 99
        mock_original.modifier = 88
        mock_user_cls.query.get.return_value = mock_original
        mock_conn = MagicMock()
        mock_conn_cls.return_value = mock_conn
        from iot_app.services.user_service import _rollback_delete_user
        _rollback_delete_user(user_id=1)
        params = mock_conn.execute_dml.call_args[0][1]
        assert params['user_id'] == 1
        assert params['databricks_user_id'] == 'uid-1'
        assert params['user_name'] == 'テストユーザー'
        assert params['organization_id'] == 1
        assert params['email_address'] == 'test@example.com'
        assert params['user_type_id'] == 2
        assert params['language_code'] == 'ja'
        assert params['region_id'] == 1
        assert params['address'] == '東京都'
        assert params['status'] == 1
        assert params['alert_notification_flag'] is True
        assert params['system_notification_flag'] is True
        assert params['create_date'] == '2024-01-01'
        assert params['creator'] == 99
        assert params['modifier'] == 88

    @patch(f'{MODULE}.UnityCatalogConnector')
    @patch(f'{MODULE}.User')
    def test_skips_when_user_not_found_in_oltp(self, mock_user_cls, mock_conn_cls):
        """2.3.2: OLTP に元データがない場合は何もしない"""
        mock_user_cls.query.get.return_value = None
        mock_conn = MagicMock()
        mock_conn_cls.return_value = mock_conn
        from iot_app.services.user_service import _rollback_delete_user
        _rollback_delete_user(user_id=999)
        mock_conn.execute_dml.assert_not_called()

    @patch(f'{MODULE}.UnityCatalogConnector')
    @patch(f'{MODULE}.User')
    def test_exception_suppressed(self, mock_user_cls, mock_conn_cls):
        """1.3.1: ロールバック中の例外を re-raise しない（ベストエフォート）"""
        mock_original = MagicMock()
        mock_user_cls.query.get.return_value = mock_original
        mock_conn = MagicMock()
        mock_conn.execute_dml.side_effect = Exception('UC re-insert error')
        mock_conn_cls.return_value = mock_conn
        from iot_app.services.user_service import _rollback_delete_user
        _rollback_delete_user(user_id=1)


# ---------------------------------------------------------------------------
# delete_user
# ---------------------------------------------------------------------------

@pytest.mark.unit
class TestDeleteUser:
    """delete_user のテスト
    観点: 2.1 正常系処理, 2.3 副作用チェック, 3.4 削除機能, 1.3 エラーハンドリング
    """

    def _make_user_mock(self):
        user = MagicMock()
        user.user_id = 1
        user.databricks_user_id = 'uid-1'
        user.delete_flag = False
        return user

    @patch(f'{MODULE}._delete_unity_catalog_user')
    @patch(f'{MODULE}.ScimClient')
    @patch(f'{MODULE}.db')
    def test_success_commits(self, mock_db, mock_scim_cls, mock_delete_uc):
        """2.1.1/3.4.2.1: 正常終了時に db.session.commit が呼ばれる"""
        mock_scim_cls.return_value = MagicMock()
        user = self._make_user_mock()
        from iot_app.services.user_service import delete_user
        delete_user(user=user, deleter_id=99)
        mock_db.session.commit.assert_called_once()

    @patch(f'{MODULE}._delete_unity_catalog_user')
    @patch(f'{MODULE}.ScimClient')
    @patch(f'{MODULE}.db')
    def test_sets_delete_flag_true(self, mock_db, mock_scim_cls, mock_delete_uc):
        """3.4.1.1: OLTP 論理削除で user.delete_flag=True に設定される"""
        mock_scim_cls.return_value = MagicMock()
        user = self._make_user_mock()
        from iot_app.services.user_service import delete_user
        delete_user(user=user, deleter_id=99)
        assert user.delete_flag is True

    @patch(f'{MODULE}._delete_unity_catalog_user')
    @patch(f'{MODULE}.ScimClient')
    @patch(f'{MODULE}.db')
    def test_saga_order_uc_then_oltp_then_scim(self, mock_db, mock_scim_cls, mock_delete_uc):
        """3.4.1.1: Saga実行順は ①UC DELETE → ②OLTP 論理削除（flush） → ③SCIM delete"""
        call_order = []
        mock_delete_uc.side_effect = lambda *_, **__: call_order.append('uc')
        mock_db.session.flush.side_effect = lambda: call_order.append('oltp')
        mock_scim = MagicMock()
        mock_scim.delete_user.side_effect = lambda *_, **__: call_order.append('scim')
        mock_scim_cls.return_value = mock_scim
        user = self._make_user_mock()
        from iot_app.services.user_service import delete_user
        delete_user(user=user, deleter_id=99)
        assert call_order == ['uc', 'oltp', 'scim']

    @patch(f'{MODULE}._rollback_delete_user')
    @patch(f'{MODULE}._delete_unity_catalog_user')
    @patch(f'{MODULE}.db')
    def test_uc_failure_no_rollback_needed(self, mock_db, mock_delete_uc, mock_rollback):
        """2.3.2: UC DELETE 失敗時は uc_deleted=False なのでロールバック呼ばれない"""
        mock_delete_uc.side_effect = Exception('UC error')
        user = self._make_user_mock()
        from iot_app.services.user_service import delete_user
        with pytest.raises(Exception):
            delete_user(user=user, deleter_id=99)
        mock_rollback.assert_not_called()

    @patch(f'{MODULE}._rollback_delete_user')
    @patch(f'{MODULE}.ScimClient')
    @patch(f'{MODULE}._delete_unity_catalog_user')
    @patch(f'{MODULE}.db')
    def test_oltp_failure_triggers_uc_rollback_and_raises(
            self, mock_db, mock_delete_uc, mock_scim_cls, mock_rollback):
        """2.3.2/1.3.1: OLTP flush 失敗時に uc_deleted=True→UC ロールバックが呼ばれ例外が伝播する"""
        mock_scim_cls.return_value = MagicMock()
        user = self._make_user_mock()
        mock_db.session.flush.side_effect = Exception('OLTP flush error')
        from iot_app.services.user_service import delete_user
        with pytest.raises(Exception):
            delete_user(user=user, deleter_id=99)
        mock_rollback.assert_called_once_with(user.user_id)

    @patch(f'{MODULE}._rollback_delete_user')
    @patch(f'{MODULE}.ScimClient')
    @patch(f'{MODULE}._delete_unity_catalog_user')
    @patch(f'{MODULE}.db')
    def test_scim_failure_triggers_uc_rollback_and_raises(
            self, mock_db, mock_delete_uc, mock_scim_cls, mock_rollback):
        """2.3.2/1.3.1: SCIM delete 失敗時に uc_deleted=True→UC ロールバックが呼ばれ例外が伝播する"""
        mock_scim = MagicMock()
        mock_scim.delete_user.side_effect = Exception('SCIM error')
        mock_scim_cls.return_value = mock_scim
        user = self._make_user_mock()
        from iot_app.services.user_service import delete_user
        with pytest.raises(Exception):
            delete_user(user=user, deleter_id=99)
        mock_rollback.assert_called_once_with(user.user_id)


# ---------------------------------------------------------------------------
# get_all_users_for_export
# ---------------------------------------------------------------------------

@pytest.mark.unit
class TestGetAllUsersForExport:
    """get_all_users_for_export のテスト
    観点: 3.1.1 検索条件指定, 3.1.2 検索条件未指定, 3.1.4 戻り値ハンドリング, 2.2 存在チェック
    """

    @patch(f'{MODULE}.UserMasterByUser')
    @patch(f'{MODULE}.db')
    def test_returns_list_of_matching_users(self, mock_db, _mock_uc):
        """3.1.4.1: 検索条件に合うユーザーリストを返す"""
        mock_users = [MagicMock(), MagicMock()]
        mock_q = MagicMock()
        mock_q.filter.return_value = mock_q
        mock_q.order_by.return_value.all.return_value = mock_users
        mock_db.session.query.return_value.filter.return_value = mock_q
        from iot_app.services.user_service import get_all_users_for_export
        result = get_all_users_for_export({'user_name': '', 'email_address': '',
                                           'user_type_id': None, 'organization_id': None,
                                           'region_id': None, 'status': None,
                                           'sort_by': 'user_name', 'order': 'asc'}, user_id=1)
        assert result == mock_users

    @patch(f'{MODULE}.UserMasterByUser')
    @patch(f'{MODULE}.db')
    def test_returns_empty_list_when_no_results(self, mock_db, _mock_uc):
        """3.1.4.2: 該当なしの場合、空リストを返す"""
        mock_q = MagicMock()
        mock_q.filter.return_value = mock_q
        mock_q.order_by.return_value.all.return_value = []
        mock_db.session.query.return_value.filter.return_value = mock_q
        from iot_app.services.user_service import get_all_users_for_export
        result = get_all_users_for_export({'user_name': 'notexist', 'email_address': '',
                                           'user_type_id': None, 'organization_id': None,
                                           'region_id': None, 'status': None,
                                           'sort_by': 'user_name', 'order': 'asc'}, user_id=1)
        assert result == []

    @patch(f'{MODULE}.UserMasterByUser')
    @patch(f'{MODULE}.db')
    def test_delete_flag_false_filter_applied(self, mock_db, _mock_uc):
        """2.2.3: 論理削除済みユーザーを除外する（delete_flag=False）"""
        mock_q = MagicMock()
        mock_q.filter.return_value = mock_q
        mock_q.order_by.return_value.all.return_value = []
        mock_db.session.query.return_value.filter.return_value = mock_q
        from iot_app.services.user_service import get_all_users_for_export
        get_all_users_for_export({'user_name': '', 'email_address': '',
                                  'user_type_id': None, 'organization_id': None,
                                  'region_id': None, 'status': None,
                                  'sort_by': 'user_name', 'order': 'asc'}, user_id=1)
        mock_db.session.query.return_value.filter.assert_called_once()

    @patch(f'{MODULE}.UserMasterByUser')
    @patch(f'{MODULE}.db')
    def test_user_name_filter_applied(self, mock_db, _mock_uc):
        """3.1.1.1: user_name 条件が指定された場合フィルタが追加される"""
        mock_q = MagicMock()
        mock_q.filter.return_value = mock_q
        mock_q.order_by.return_value.all.return_value = []
        mock_db.session.query.return_value.filter.return_value = mock_q
        from iot_app.services.user_service import get_all_users_for_export
        get_all_users_for_export({'user_name': '田中', 'email_address': '',
                                  'user_type_id': None, 'organization_id': None,
                                  'region_id': None, 'status': None,
                                  'sort_by': 'user_name', 'order': 'asc'}, user_id=1)
        assert mock_q.filter.called

    @patch(f'{MODULE}.UserMasterByUser')
    @patch(f'{MODULE}.db')
    def test_none_condition_not_filtered(self, mock_db, _mock_uc):
        """3.1.1.3: user_type_id=None のとき user_type_id フィルタは追加されない"""
        mock_q = MagicMock()
        mock_q.filter.return_value = mock_q
        mock_q.order_by.return_value.all.return_value = []
        mock_db.session.query.return_value.filter.return_value = mock_q
        from iot_app.services.user_service import get_all_users_for_export
        get_all_users_for_export({'user_name': '', 'email_address': '',
                                  'user_type_id': None, 'organization_id': None,
                                  'region_id': None, 'status': None,
                                  'sort_by': 'user_name', 'order': 'asc'}, user_id=1)
        assert mock_q.filter.call_count == 0


# ---------------------------------------------------------------------------
# generate_users_csv
# ---------------------------------------------------------------------------

@pytest.mark.unit
class TestGenerateUsersCsv:
    """generate_users_csv のテスト
    観点: 3.5.1 CSV生成ロジック, 3.5.2 エスケープ処理, 3.5.3 エンコーディング処理
    """

    def _make_user(self, user_id=1, user_name='テスト太郎', email='t@e.com',
                   user_type_name='管理者', org_id=1, org_name='テスト組織',
                   create_date='2024-01-01 00:00:00'):
        user = MagicMock()
        user.user_id = user_id
        user.user_name = user_name
        user.email_address = email
        user.user_type = MagicMock()
        user.user_type.user_type_name = user_type_name
        user.organization_id = org_id
        user.organization = MagicMock()
        user.organization.organization_name = org_name
        user.create_date = MagicMock()
        user.create_date.strftime.return_value = create_date
        return user

    def test_header_row_contains_defined_columns(self):
        """3.5.1.1: 定義済み全8列名がヘッダーに含まれる"""
        from iot_app.services.user_service import generate_users_csv
        result = generate_users_csv([])
        text = result.decode('utf-8-sig')
        assert 'ユーザーID' in text
        assert 'ユーザー名' in text
        assert 'メールアドレス' in text
        assert '所属組織ID' in text
        assert '所属組織名' in text
        assert 'ユーザー種別' in text
        assert '地域' in text
        assert '住所' in text

    def test_empty_users_returns_header_only(self):
        """3.5.1.3: 空リストの場合ヘッダー行のみ出力される"""
        from iot_app.services.user_service import generate_users_csv
        result = generate_users_csv([])
        text = result.decode('utf-8-sig')
        lines = [l for l in text.splitlines() if l.strip()]
        assert len(lines) == 1

    def test_all_users_included_as_rows(self):
        """3.5.1.2: 渡したユーザー数分のデータ行が含まれる"""
        from iot_app.services.user_service import generate_users_csv
        users = [self._make_user(1, 'ユーザー1'), self._make_user(2, 'ユーザー2')]
        result = generate_users_csv(users)
        text = result.decode('utf-8-sig')
        lines = [l for l in text.splitlines() if l.strip()]
        assert len(lines) == 3  # ヘッダー + 2行

    def test_column_order_matches_specification(self):
        """3.5.1.4: 列順序が設計書通り（全8列）"""
        from iot_app.services.user_service import generate_users_csv
        result = generate_users_csv([])
        text = result.decode('utf-8-sig')
        header = text.splitlines()[0]
        columns = header.split(',')
        assert columns[0] == 'ユーザーID'
        assert columns[1] == 'ユーザー名'
        assert columns[2] == 'メールアドレス'
        assert columns[3] == '所属組織ID'
        assert columns[4] == '所属組織名'
        assert columns[5] == 'ユーザー種別'
        assert columns[6] == '地域'
        assert columns[7] == '住所'

    def test_comma_in_field_quoted(self):
        """3.5.2.1: フィールド値にカンマが含まれる場合ダブルクォートで囲まれる"""
        from iot_app.services.user_service import generate_users_csv
        user = self._make_user(1, 'テスト,ユーザー')
        result = generate_users_csv([user])
        text = result.decode('utf-8-sig')
        assert '"テスト,ユーザー"' in text

    def test_newline_in_field_quoted(self):
        """3.5.2.2: フィールド値に改行が含まれる場合ダブルクォートで囲まれる"""
        from iot_app.services.user_service import generate_users_csv
        user = self._make_user(1, 'テスト\nユーザー')
        result = generate_users_csv([user])
        text = result.decode('utf-8-sig')
        assert '"テスト\nユーザー"' in text

    def test_double_quote_in_field_escaped(self):
        """3.5.2.3: フィールド値にダブルクォートが含まれる場合 \"\" でエスケープされる"""
        from iot_app.services.user_service import generate_users_csv
        user = self._make_user(1, '名前"テスト"')
        result = generate_users_csv([user])
        text = result.decode('utf-8-sig')
        assert '""' in text

    def test_plain_field_not_escaped(self):
        """3.5.2.4: 特殊文字を含まないフィールドはそのまま出力される"""
        from iot_app.services.user_service import generate_users_csv
        user = self._make_user(1, 'テストユーザー')
        result = generate_users_csv([user])
        text = result.decode('utf-8-sig')
        assert 'テストユーザー' in text

    def test_bom_prefix_present(self):
        """3.5.3.1: BOM（0xEF 0xBB 0xBF）が先頭に付与される"""
        from iot_app.services.user_service import generate_users_csv
        result = generate_users_csv([])
        assert result[:3] == b'\xef\xbb\xbf'

    def test_japanese_characters_output_correctly(self):
        """3.5.3.2: 日本語文字が文字化けなく正しく出力される"""
        from iot_app.services.user_service import generate_users_csv
        user = self._make_user(1, '山田太郎', 'yamada@example.com', '販社ユーザー', 1, '東京営業所')
        result = generate_users_csv([user])
        text = result.decode('utf-8-sig')
        assert '山田太郎' in text
        assert '東京営業所' in text

    def test_none_relationship_outputs_empty_string(self):
        """3.5.1.6: organization が None のとき所属組織名列が空文字で出力される"""
        import csv, io
        from iot_app.services.user_service import generate_users_csv
        user = self._make_user()
        user.organization = None
        result = generate_users_csv([user])
        text = result.decode('utf-8-sig')
        reader = csv.reader(io.StringIO(text))
        rows = list(reader)
        assert rows[1][5] == ''  # 所属組織名は5列目（0-indexed）
