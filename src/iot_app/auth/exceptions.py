class AuthError(Exception):
    """認証エラー基底クラス"""
    pass


class UnauthorizedError(AuthError):
    """未認証エラー（401）"""
    pass


class ForbiddenError(AuthError):
    """権限不足エラー（403）"""
    pass


class TokenExchangeError(AuthError):
    """Token Exchangeエラー"""
    ERROR_CODE = 'token_exchange_failed'


class SessionExpiredError(AuthError):
    """セッション期限切れエラー"""
    pass


class JWTExpiredError(AuthError):
    """JWT期限切れエラー（再発行トリガー）"""
    pass


class JWTRetrievalError(AuthError):
    """JWT取得失敗エラー（認証基盤の異常）

    Azure/AWSでリクエストヘッダーにJWTがない場合に発生（Easy Auth設定ミス等）。
    呼び出し元でFlaskセッションをクリアし、500エラーページへ遷移する。
    """
    pass


class PasswordExpiredError(AuthError):
    """パスワード期限切れエラー（パスワード変更画面へリダイレクト）"""
    pass
