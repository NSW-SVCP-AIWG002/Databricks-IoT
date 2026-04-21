import pytest
from unittest.mock import patch, MagicMock

MODULE = 'iot_app.databricks.scim_client'


@pytest.mark.unit
class TestScimClientCreateUser:
    """ScimClient.create_user のテスト
    観点: 3.2.1 登録処理呼び出し, 3.2.2 登録結果, 1.3 エラーハンドリング
    """

    @patch(f'{MODULE}.requests')
    def test_create_user_returns_databricks_user_id(self, mock_requests, app):
        """3.2.2.1: create_user がレスポンスの id（databricks_user_id 文字列）を返す"""
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.return_value = {'id': 'new-scim-uid', 'userName': 'test@example.com'}
        mock_requests.post.return_value = mock_response
        app.config['DATABRICKS_HOST'] = 'https://test.azuredatabricks.net'
        app.config['DATABRICKS_SERVICE_PRINCIPAL_TOKEN'] = 'test-token'
        with app.app_context():
            from iot_app.databricks.scim_client import ScimClient
            client = ScimClient()
            result = client.create_user('test@example.com', display_name='テストユーザー')
        assert result == 'new-scim-uid'

    @patch(f'{MODULE}.requests')
    def test_create_user_sends_post_to_scim_users_endpoint(self, mock_requests, app):
        """3.2.1.1: SCIM /Users エンドポイントに POST リクエストを送信する"""
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.return_value = {'id': 'uid', 'userName': 'u@u.com'}
        mock_requests.post.return_value = mock_response
        app.config['DATABRICKS_HOST'] = 'https://test.azuredatabricks.net'
        app.config['DATABRICKS_SERVICE_PRINCIPAL_TOKEN'] = 'test-token'
        with app.app_context():
            from iot_app.databricks.scim_client import ScimClient
            client = ScimClient()
            client.create_user('u@u.com', display_name='ユーザー')
        assert mock_requests.post.called
        call_url = mock_requests.post.call_args[0][0]
        assert 'Users' in call_url or 'users' in call_url.lower()

    @patch(f'{MODULE}.requests')
    def test_create_user_request_contains_email_and_display_name(self, mock_requests, app):
        """3.2.1.1: リクエストボディに userName（email）と displayName が含まれる"""
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.return_value = {'id': 'uid', 'userName': 't@e.com'}
        mock_requests.post.return_value = mock_response
        app.config['DATABRICKS_HOST'] = 'https://test.azuredatabricks.net'
        app.config['DATABRICKS_SERVICE_PRINCIPAL_TOKEN'] = 'test-token'
        with app.app_context():
            from iot_app.databricks.scim_client import ScimClient
            client = ScimClient()
            client.create_user('t@e.com', display_name='テスト名')
        call_kwargs = mock_requests.post.call_args[1]
        body = call_kwargs.get('json', {})
        body_str = str(body)
        assert 't@e.com' in body_str
        assert 'テスト名' in body_str

    @patch(f'{MODULE}.requests')
    def test_create_user_raises_on_api_error(self, mock_requests, app):
        """1.3.1: API エラー（4xx）時に例外が伝播する"""
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.raise_for_status.side_effect = Exception('Bad Request')
        mock_requests.post.return_value = mock_response
        app.config['DATABRICKS_HOST'] = 'https://test.azuredatabricks.net'
        app.config['DATABRICKS_SERVICE_PRINCIPAL_TOKEN'] = 'test-token'
        with app.app_context():
            from iot_app.databricks.scim_client import ScimClient
            client = ScimClient()
            with pytest.raises(Exception):
                client.create_user('bad@bad.com', display_name='エラー')


@pytest.mark.unit
class TestScimClientUpdateUser:
    """ScimClient.update_user のテスト
    観点: 3.3.1 更新処理呼び出し, 3.3.2 更新結果, 1.3 エラーハンドリング
    ※ update_user(databricks_user_id, display_name, status) でDatabricks側のdisplayNameとactiveを更新する
    """

    @patch(f'{MODULE}.requests')
    def test_update_user_sends_patch_to_scim_users_endpoint(self, mock_requests, app):
        """3.3.1.1: SCIM /Users/{id} エンドポイントに PATCH リクエストを送信する"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_requests.patch.return_value = mock_response
        app.config['DATABRICKS_HOST'] = 'https://test.azuredatabricks.net'
        app.config['DATABRICKS_SERVICE_PRINCIPAL_TOKEN'] = 'test-token'
        with app.app_context():
            from iot_app.databricks.scim_client import ScimClient
            client = ScimClient()
            client.update_user('uid-1', display_name='更新名', status=1)
        assert mock_requests.patch.called
        call_url = mock_requests.patch.call_args[0][0]
        assert 'uid-1' in call_url

    @patch(f'{MODULE}.requests')
    def test_update_user_payload_contains_active_false_when_inactive(self, mock_requests, app):
        """3.3.1.1: status=0 のとき Operations 内の active が False になる"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_requests.patch.return_value = mock_response
        app.config['DATABRICKS_HOST'] = 'https://test.azuredatabricks.net'
        app.config['DATABRICKS_SERVICE_PRINCIPAL_TOKEN'] = 'test-token'
        with app.app_context():
            from iot_app.databricks.scim_client import ScimClient
            client = ScimClient()
            client.update_user('uid-1', display_name='名前', status=0)
        call_kwargs = mock_requests.patch.call_args[1]
        body = call_kwargs.get('json', {})
        operations = body.get('Operations', [])
        active_op = next((op for op in operations if op.get('path') == 'active'), None)
        assert active_op is not None
        assert active_op['value'] is False

    @patch(f'{MODULE}.requests')
    def test_update_user_raises_on_api_error(self, mock_requests, app):
        """1.3.1: API エラー（4xx）時に例外が伝播する"""
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.raise_for_status.side_effect = Exception('Not Found')
        mock_requests.patch.return_value = mock_response
        app.config['DATABRICKS_HOST'] = 'https://test.azuredatabricks.net'
        app.config['DATABRICKS_SERVICE_PRINCIPAL_TOKEN'] = 'test-token'
        with app.app_context():
            from iot_app.databricks.scim_client import ScimClient
            client = ScimClient()
            with pytest.raises(Exception):
                client.update_user('bad-uid', display_name='名前', status=1)


@pytest.mark.unit
class TestScimClientDeleteUser:
    """ScimClient.delete_user のテスト
    観点: 3.4.1 削除処理呼び出し, 3.4.2 削除結果, 1.3 エラーハンドリング
    """

    @patch(f'{MODULE}.requests')
    def test_delete_user_sends_delete_to_scim_users_endpoint(self, mock_requests, app):
        """3.4.1.1: SCIM /Users/{id} エンドポイントに DELETE リクエストを送信する"""
        mock_response = MagicMock()
        mock_response.status_code = 204
        mock_requests.delete.return_value = mock_response
        app.config['DATABRICKS_HOST'] = 'https://test.azuredatabricks.net'
        app.config['DATABRICKS_SERVICE_PRINCIPAL_TOKEN'] = 'test-token'
        with app.app_context():
            from iot_app.databricks.scim_client import ScimClient
            client = ScimClient()
            client.delete_user('uid-to-delete')
        assert mock_requests.delete.called

    @patch(f'{MODULE}.requests')
    def test_delete_user_url_contains_user_id(self, mock_requests, app):
        """3.4.2.2: DELETE URL に指定した user_id が含まれる"""
        mock_response = MagicMock()
        mock_response.status_code = 204
        mock_requests.delete.return_value = mock_response
        app.config['DATABRICKS_HOST'] = 'https://test.azuredatabricks.net'
        app.config['DATABRICKS_SERVICE_PRINCIPAL_TOKEN'] = 'test-token'
        with app.app_context():
            from iot_app.databricks.scim_client import ScimClient
            client = ScimClient()
            client.delete_user('target-uid-999')
        call_url = mock_requests.delete.call_args[0][0]
        assert 'target-uid-999' in call_url

    @patch(f'{MODULE}.requests')
    def test_delete_user_raises_on_api_error(self, mock_requests, app):
        """1.3.1: API エラー（4xx）時に例外が伝播する"""
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.raise_for_status.side_effect = Exception('Not Found')
        mock_requests.delete.return_value = mock_response
        app.config['DATABRICKS_HOST'] = 'https://test.azuredatabricks.net'
        app.config['DATABRICKS_SERVICE_PRINCIPAL_TOKEN'] = 'test-token'
        with app.app_context():
            from iot_app.databricks.scim_client import ScimClient
            client = ScimClient()
            with pytest.raises(Exception):
                client.delete_user('nonexistent-uid')


@pytest.mark.unit
class TestScimClientAddUserToGroup:
    """ScimClient.add_user_to_group のテスト
    観点: 3.2.1 登録処理呼び出し, 1.3 エラーハンドリング
    ※ add_user_to_group(group_id, databricks_user_id) でワークスペースグループへ追加する
    """

    @patch(f'{MODULE}.requests')
    def test_add_user_to_group_sends_patch_to_scim_groups_endpoint(self, mock_requests, app):
        """3.2.1.1: SCIM /Groups/{group_id} エンドポイントに PATCH リクエストを送信する"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_requests.patch.return_value = mock_response
        app.config['DATABRICKS_HOST'] = 'https://test.azuredatabricks.net'
        app.config['DATABRICKS_SERVICE_PRINCIPAL_TOKEN'] = 'test-token'
        with app.app_context():
            from iot_app.databricks.scim_client import ScimClient
            client = ScimClient()
            client.add_user_to_group('group-gid', 'user-uid')
        assert mock_requests.patch.called
        call_url = mock_requests.patch.call_args[0][0]
        assert 'Groups' in call_url or 'groups' in call_url.lower()

    @patch(f'{MODULE}.requests')
    def test_add_user_to_group_url_contains_group_id(self, mock_requests, app):
        """3.2.1.1: PATCH URL に group_id が含まれる"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_requests.patch.return_value = mock_response
        app.config['DATABRICKS_HOST'] = 'https://test.azuredatabricks.net'
        app.config['DATABRICKS_SERVICE_PRINCIPAL_TOKEN'] = 'test-token'
        with app.app_context():
            from iot_app.databricks.scim_client import ScimClient
            client = ScimClient()
            client.add_user_to_group('workspace-group-id', 'user-uid')
        call_url = mock_requests.patch.call_args[0][0]
        assert 'workspace-group-id' in call_url

    @patch(f'{MODULE}.requests')
    def test_add_user_to_group_request_body_contains_user_id(self, mock_requests, app):
        """3.2.1.1: リクエストボディに追加するユーザーの ID が含まれる"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_requests.patch.return_value = mock_response
        app.config['DATABRICKS_HOST'] = 'https://test.azuredatabricks.net'
        app.config['DATABRICKS_SERVICE_PRINCIPAL_TOKEN'] = 'test-token'
        with app.app_context():
            from iot_app.databricks.scim_client import ScimClient
            client = ScimClient()
            client.add_user_to_group('group-gid', 'user-uid-123')
        call_kwargs = mock_requests.patch.call_args[1]
        body_str = str(call_kwargs.get('json', {}))
        assert 'user-uid-123' in body_str

    @patch(f'{MODULE}.requests')
    def test_add_user_to_group_raises_on_api_error(self, mock_requests, app):
        """1.3.1: API エラー（4xx）時に例外が伝播する"""
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.raise_for_status.side_effect = Exception('Bad Request')
        mock_requests.patch.return_value = mock_response
        app.config['DATABRICKS_HOST'] = 'https://test.azuredatabricks.net'
        app.config['DATABRICKS_SERVICE_PRINCIPAL_TOKEN'] = 'test-token'
        with app.app_context():
            from iot_app.databricks.scim_client import ScimClient
            client = ScimClient()
            with pytest.raises(Exception):
                client.add_user_to_group('group-gid', 'user-uid')
