import base64
import json

from auth.providers.base import AuthProvider, UserInfo
from auth.exceptions import UnauthorizedError


class AzureEasyAuthProvider(AuthProvider):
    """Azure Easy Auth 認証プロバイダー（X-MS-* ヘッダーからユーザー情報・JWT取得）"""

    def get_user_info(self, request) -> UserInfo:
        """X-MS-CLIENT-PRINCIPAL ヘッダーから email を取得する"""
        header_value = request.headers.get("X-MS-CLIENT-PRINCIPAL")
        if not header_value:
            raise UnauthorizedError("X-MS-CLIENT-PRINCIPAL header not found")

        decoded = json.loads(base64.b64decode(header_value).decode())
        claims = decoded.get("claims", [])
        email = next(
            (c["val"] for c in claims if c.get("typ") == "preferred_username"),
            None,
        )
        if not email:
            raise UnauthorizedError("preferred_username claim not found")

        return UserInfo(email=email)

    def get_jwt_for_token_exchange(self, request) -> str:
        """X-MS-TOKEN-AAD-ACCESS-TOKEN ヘッダーから JWT を取得する"""
        token = request.headers.get("X-MS-TOKEN-AAD-ACCESS-TOKEN")
        if not token:
            raise UnauthorizedError("X-MS-TOKEN-AAD-ACCESS-TOKEN header not found")
        return token

    def logout_url(self) -> str:
        return "/.auth/logout"

    def requires_additional_setup(self) -> bool:
        return False
