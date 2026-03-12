"""
共通例外クラス定義
"""


class ValidationError(Exception):
    """バリデーションエラー"""
    pass


class NotFoundError(Exception):
    """リソース未検出エラー"""
    pass


class AuthError(Exception):
    """認証エラー"""
    pass
