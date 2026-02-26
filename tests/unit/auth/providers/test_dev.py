"""
auth/providers/dev.py の単体テスト

観点: unit-test-perspectives.md
  - 2.1 正常系処理
  - 1.3 エラーハンドリング

検証内容:
  - DEV_AUTH_EMAIL が設定されている場合、そのメールアドレスで UserInfo を返す
  - DEV_AUTH_EMAIL が未設定の場合、デフォルト値 dev@localhost を使用する
  - get_jwt_for_token_exchange() は NotImplementedError を送出する
  - logout_url() は "/" を返す
  - requires_additional_setup() は False を返す
"""
import pytest
from unittest.mock import MagicMock

from auth.providers.dev import DevAuthProvider
from auth.exceptions import UnauthorizedError


@pytest.mark.unit
class TestDevAuthProvider:
    """DevAuthProvider のテスト
    観点: 2.1 正常系処理, 1.3 エラーハンドリング
    """

    def test_get_user_info_returns_email_from_env(self, monkeypatch):
        """2.1.1: DEV_AUTH_EMAIL 環境変数が設定されている場合、その値で UserInfo を返す"""
        monkeypatch.setenv("DEV_AUTH_EMAIL", "tester@example.com")
        provider = DevAuthProvider()
        mock_request = MagicMock()

        result = provider.get_user_info(mock_request)

        assert result["email"] == "tester@example.com"

    def test_get_user_info_uses_default_when_env_not_set(self, monkeypatch):
        """2.1.2: DEV_AUTH_EMAIL 未設定時はデフォルト値 dev@localhost を使用する"""
        monkeypatch.delenv("DEV_AUTH_EMAIL", raising=False)
        provider = DevAuthProvider()
        mock_request = MagicMock()

        result = provider.get_user_info(mock_request)

        assert result["email"] == "dev@localhost"

    def test_get_jwt_for_token_exchange_raises_not_implemented(self):
        """1.3.1: get_jwt_for_token_exchange() は NotImplementedError を送出する
        （dev mode では Token Exchange を行わず DEV_DATABRICKS_TOKEN を使用するため）
        """
        provider = DevAuthProvider()
        mock_request = MagicMock()

        with pytest.raises(NotImplementedError):
            provider.get_jwt_for_token_exchange(mock_request)

    def test_logout_url_returns_root(self):
        """2.1.3: logout_url() はトップページ "/" を返す"""
        provider = DevAuthProvider()

        assert provider.logout_url() == "/"

    def test_requires_additional_setup_returns_false(self):
        """2.1.4: requires_additional_setup() は False を返す"""
        provider = DevAuthProvider()

        assert provider.requires_additional_setup() is False
