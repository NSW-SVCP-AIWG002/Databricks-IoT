import os

from auth.providers.base import AuthProvider, UserInfo
from auth.exceptions import UnauthorizedError


class DevAuthProvider(AuthProvider):
    """ローカル開発用認証プロバイダー

    Azure Easy Auth が使用できないローカル開発環境向け。
    AUTH_TYPE=dev のときのみ factory.py から生成される。

    - 認証: DEV_AUTH_EMAIL 環境変数のユーザーとして即時認証成功
    - Token Exchange: 使用しない（DEV_DATABRICKS_TOKEN を middleware が直接使用）
    - ログアウト: トップページへリダイレクト
    """

    def get_user_info(self, request) -> UserInfo:
        """DEV_AUTH_EMAIL 環境変数からユーザー情報を返す"""
        email = os.getenv("DEV_AUTH_EMAIL", "dev@localhost")
        if not email:
            raise UnauthorizedError("DEV_AUTH_EMAIL is not set")
        return UserInfo(email=email)

    def get_jwt_for_token_exchange(self, request) -> str:
        """dev mode では Token Exchange を行わないため呼ばれない"""
        raise NotImplementedError(
            "DevAuthProvider does not support JWT retrieval. "
            "Use DEV_DATABRICKS_TOKEN instead."
        )

    def logout_url(self) -> str:
        """ログアウト先: トップページ"""
        return "/"

    def requires_additional_setup(self) -> bool:
        return False
