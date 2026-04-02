"""
get_auth_provider() の単体テスト

観点: unit-test-perspectives.md
  - 2.1 正常系処理
  - 1.3 エラーハンドリング

設計: AUTH_TYPE は config.py で管理し、current_app.config 経由で参照する
      （認証設計書セクション2.3）
"""
import pytest

from iot_app.auth.factory import get_auth_provider
from iot_app.auth.providers.azure_easy_auth import AzureEasyAuthProvider
from iot_app.auth.providers.dev import DevAuthProvider


@pytest.mark.unit
class TestGetAuthProvider:
    """get_auth_provider() のテスト
    観点: 2.1 正常系処理, 1.3 エラーハンドリング
    """

    def test_returns_azure_provider_when_auth_type_is_azure(self, app):
        """2.1.1: AUTH_TYPE=azure のとき AzureEasyAuthProvider インスタンスが返される"""
        # Arrange
        with app.test_request_context("/"):
            app.config['AUTH_TYPE'] = 'azure'

            # Act
            result = get_auth_provider()

        # Assert
        assert isinstance(result, AzureEasyAuthProvider)

    def test_returns_dev_provider_when_auth_type_is_dev(self, app):
        """2.1.2: AUTH_TYPE=dev のとき DevAuthProvider インスタンスが返される"""
        with app.test_request_context("/"):
            app.config['AUTH_TYPE'] = 'dev'

            result = get_auth_provider()

        assert isinstance(result, DevAuthProvider)

    def test_raises_value_error_for_unknown_auth_type(self, app):
        """1.3.6: 未知の AUTH_TYPE が指定された場合、ValueError が発生する"""
        # Arrange
        with app.test_request_context("/"):
            app.config['AUTH_TYPE'] = 'unknown_provider'

            # Act & Assert
            with pytest.raises(ValueError):
                get_auth_provider()
