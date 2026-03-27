class NotFoundError(Exception):
    """リソースが見つからない場合の例外"""


class ValidationError(Exception):
    """入力値バリデーションエラーの例外"""


class AuthError(Exception):
    """認証エラー"""
