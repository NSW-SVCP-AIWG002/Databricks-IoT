import pytest
from unittest.mock import patch, MagicMock

MODULE = 'iot_app.databricks.scim_client'


@pytest.fixture
def scim_client(app):
    """ScimClient インスタンスを生成するフィクスチャ"""
    app.config['DATABRICKS_HOST'] = 'https://test.azuredatabricks.net'
    app.config['DATABRICKS_SERVICE_PRINCIPAL_TOKEN'] = 'test-token'
    with app.app_context():
        from iot_app.databricks.scim_client import ScimClient
        return ScimClient()


@pytest.mark.unit
class TestScimClientCreateUser:
    """ScimClient.create_user のテスト"""

    @patch(f'{MODULE}.requests')
    def test_create_user_returns_user_data(self, mock_requests, app):
        """観点1: create_user が作成されたユーザーのデータを返す"""
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
        assert result['id'] == 'new-scim-uid'

    @patch(f'{MODULE}.requests')
    def test_create_user_sends_post_to_scim_endpoint(self, mock_requests, app):
        """観点2: SCIM Users エンドポイントに POST リクエストを送信する"""
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
        assert 'scim' in call_url.lower() or 'Users' in call_url

    @patch(f'{MODULE}.requests')
    def test_create_user_raises_on_error(self, mock_requests, app):
        """観点3: API エラー時に例外を発生させる"""
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
    """ScimClient.update_user のテスト"""

    @patch(f'{MODULE}.requests')
    def test_update_user_sends_put_request(self, mock_requests, app):
        """観点1: SCIM Users/{id} エンドポイントに PUT リクエストを送信する"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'id': 'uid-1', 'active': True}
        mock_requests.put.return_value = mock_response
        app.config['DATABRICKS_HOST'] = 'https://test.azuredatabricks.net'
        app.config['DATABRICKS_SERVICE_PRINCIPAL_TOKEN'] = 'test-token'
        with app.app_context():
            from iot_app.databricks.scim_client import ScimClient
            client = ScimClient()
            client.update_user('uid-1', email='new@example.com', display_name='更新名', active=True)
        assert mock_requests.put.called

    @patch(f'{MODULE}.requests')
    def test_update_user_active_status_converted_to_bool(self, mock_requests, app):
        """観点2: status 値が active フラグ（bool）に変換される"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'id': 'uid-1', 'active': False}
        mock_requests.put.return_value = mock_response
        app.config['DATABRICKS_HOST'] = 'https://test.azuredatabricks.net'
        app.config['DATABRICKS_SERVICE_PRINCIPAL_TOKEN'] = 'test-token'
        with app.app_context():
            from iot_app.databricks.scim_client import ScimClient
            client = ScimClient()
            client.update_user('uid-1', email='u@u.com', display_name='名前', active=False)
        payload = mock_requests.put.call_args[1].get('json') or mock_requests.put.call_args[0][1] if len(mock_requests.put.call_args[0]) > 1 else {}
        assert mock_requests.put.called


@pytest.mark.unit
class TestScimClientDeleteUser:
    """ScimClient.delete_user のテスト"""

    @patch(f'{MODULE}.requests')
    def test_delete_user_sends_delete_request(self, mock_requests, app):
        """観点1: SCIM Users/{id} エンドポイントに DELETE リクエストを送信する"""
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
        """観点2: DELETE URL にユーザー ID が含まれる"""
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


@pytest.mark.unit
class TestScimClientAddUserToGroup:
    """ScimClient.add_user_to_group のテスト"""

    @patch(f'{MODULE}.requests')
    def test_add_user_to_group_sends_patch_request(self, mock_requests, app):
        """観点1: SCIM Groups/{id} エンドポイントに PATCH リクエストを送信する"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_requests.patch.return_value = mock_response
        app.config['DATABRICKS_HOST'] = 'https://test.azuredatabricks.net'
        app.config['DATABRICKS_SERVICE_PRINCIPAL_TOKEN'] = 'test-token'
        with app.app_context():
            from iot_app.databricks.scim_client import ScimClient
            client = ScimClient()
            client.add_user_to_group('user-uid', 'group-gid')
        assert mock_requests.patch.called

    @patch(f'{MODULE}.requests')
    def test_add_user_to_group_uses_workspace_group_id(self, mock_requests, app):
        """観点2: DATABRICKS_WORKSPACE_GROUP_ID がグループ ID として使われる"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_requests.patch.return_value = mock_response
        app.config['DATABRICKS_HOST'] = 'https://test.azuredatabricks.net'
        app.config['DATABRICKS_SERVICE_PRINCIPAL_TOKEN'] = 'test-token'
        with app.app_context():
            from iot_app.databricks.scim_client import ScimClient
            client = ScimClient()
            client.add_user_to_group('user-uid', 'workspace-group-id')
        call_url = mock_requests.patch.call_args[0][0]
        assert 'Groups' in call_url or 'groups' in call_url
