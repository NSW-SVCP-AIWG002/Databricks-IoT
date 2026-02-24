"""
AzureEasyAuthProvider の単体テスト

観点: unit-test-perspectives.md
  - 2.1 正常系処理
  - 1.3 エラーハンドリング
"""
import base64
import json
import pytest
from unittest.mock import MagicMock

from auth.providers.azure_easy_auth import AzureEasyAuthProvider
from auth.exceptions import UnauthorizedError


# ---------------------------------------------------------------------------
# ヘルパー
# ---------------------------------------------------------------------------

def _make_client_principal(claims: list) -> str:
    """X-MS-CLIENT-PRINCIPAL ヘッダー値（Base64）を生成するヘルパー"""
    data = {
        "auth_typ": "aad",
        "claims": claims,
        "name_typ": "name",
        "role_typ": "roles",
    }
    return base64.b64encode(json.dumps(data).encode()).decode()


# ---------------------------------------------------------------------------
# get_user_info()
# ---------------------------------------------------------------------------

@pytest.mark.unit
class TestAzureEasyAuthProviderGetUserInfo:
    """AzureEasyAuthProvider.get_user_info() のテスト
    観点: 2.1 正常系処理, 1.3 エラーハンドリング
    """

    def setup_method(self):
        self.provider = AzureEasyAuthProvider()

    def test_get_user_info_success(self):
        """2.1.1: 有効な X-MS-CLIENT-PRINCIPAL ヘッダーから email を返す"""
        # Arrange
        claims = [
            {"typ": "preferred_username", "val": "yamada@example.com"},
        ]
        mock_request = MagicMock()
        mock_request.headers.get.return_value = _make_client_principal(claims)

        # Act
        result = self.provider.get_user_info(mock_request)

        # Assert
        assert result["email"] == "yamada@example.com"

    def test_get_user_info_missing_header_raises_unauthorized(self):
        """1.3.3: X-MS-CLIENT-PRINCIPAL ヘッダーが存在しない場合 UnauthorizedError が発生する"""
        # Arrange
        mock_request = MagicMock()
        mock_request.headers.get.return_value = None

        # Act & Assert
        with pytest.raises(UnauthorizedError):
            self.provider.get_user_info(mock_request)


# ---------------------------------------------------------------------------
# get_jwt_for_token_exchange()
# ---------------------------------------------------------------------------

@pytest.mark.unit
class TestAzureEasyAuthProviderGetJwt:
    """AzureEasyAuthProvider.get_jwt_for_token_exchange() のテスト
    観点: 2.1 正常系処理, 1.3 エラーハンドリング
    """

    def setup_method(self):
        self.provider = AzureEasyAuthProvider()

    def test_get_jwt_success(self):
        """2.1.1: X-MS-TOKEN-AAD-ACCESS-TOKEN ヘッダーからトークン文字列を返す"""
        # Arrange
        mock_request = MagicMock()
        mock_request.headers.get.return_value = "eyJ.test.token"

        # Act
        result = self.provider.get_jwt_for_token_exchange(mock_request)

        # Assert
        assert result == "eyJ.test.token"

    def test_get_jwt_returns_exact_header_value(self):
        """2.1.1: ヘッダーの値をそのまま返す（変換・デコードは行わない）"""
        # Arrange
        expected_token = "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.payload.signature"
        mock_request = MagicMock()
        mock_request.headers.get.return_value = expected_token

        # Act
        result = self.provider.get_jwt_for_token_exchange(mock_request)

        # Assert
        assert result == expected_token

    def test_get_jwt_missing_header_raises_unauthorized(self):
        """1.3.3: X-MS-TOKEN-AAD-ACCESS-TOKEN ヘッダーが存在しない場合 UnauthorizedError が発生する"""
        # Arrange
        mock_request = MagicMock()
        mock_request.headers.get.return_value = None

        # Act & Assert
        with pytest.raises(UnauthorizedError):
            self.provider.get_jwt_for_token_exchange(mock_request)


# ---------------------------------------------------------------------------
# logout_url()
# ---------------------------------------------------------------------------

@pytest.mark.unit
class TestAzureEasyAuthProviderLogoutUrl:
    """AzureEasyAuthProvider.logout_url() のテスト
    観点: 2.1 正常系処理
    """

    def setup_method(self):
        self.provider = AzureEasyAuthProvider()

    def test_logout_url_returns_azure_easy_auth_endpoint(self):
        """2.1.1: Azure Easy Auth のログアウトエンドポイント '/.auth/logout' を返す"""
        # Arrange & Act
        result = self.provider.logout_url()

        # Assert
        assert result == "/.auth/logout"


# ---------------------------------------------------------------------------
# requires_additional_setup()
# ---------------------------------------------------------------------------

@pytest.mark.unit
class TestAzureEasyAuthProviderRequiresSetup:
    """AzureEasyAuthProvider.requires_additional_setup() のテスト
    観点: 2.1 正常系処理
    """

    def setup_method(self):
        self.provider = AzureEasyAuthProvider()

    def test_requires_additional_setup_returns_false(self):
        """2.1.1: Azure 環境では Easy Auth が認証を処理するため False を返す"""
        # Arrange & Act
        result = self.provider.requires_additional_setup()

        # Assert
        assert result is False
