from abc import ABC, abstractmethod
from typing import TypedDict


class UserInfo(TypedDict):
    email: str


class AuthProvider(ABC):
    """認証プロバイダー抽象基底クラス"""

    @abstractmethod
    def get_user_info(self, request) -> UserInfo:
        """リクエストからユーザー情報を取得"""
        pass

    @abstractmethod
    def get_jwt_for_token_exchange(self, request) -> str:
        """Token Exchange用のJWTを取得"""
        pass

    @abstractmethod
    def logout_url(self) -> str:
        """ログアウトURLを返却"""
        pass

    @abstractmethod
    def requires_additional_setup(self) -> bool:
        """追加設定（ログイン画面等）が必要か"""
        pass
