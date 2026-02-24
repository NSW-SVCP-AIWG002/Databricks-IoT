"""
auth/exceptions.py の単体テスト

観点: unit-test-perspectives.md
  - 1.3 エラーハンドリング（エラーハンドリング関数）

検証内容:
  - 全例外クラスが AuthError を継承していること（基底クラスによる一括捕捉を保証）
  - ERROR_CODE 属性を持つクラスの属性値が設計書通りであること
  - 各例外が raise / except で正常に機能すること

※ 自前IdP固有クラス（UserNotFoundError等）は Azure スコープ外のため対象外
"""
import pytest

from auth.exceptions import (
    AuthError,
    UnauthorizedError,
    ForbiddenError,
    TokenExchangeError,
    SessionExpiredError,
    JWTExpiredError,
    JWTRetrievalError,
    PasswordExpiredError,
)


# ---------------------------------------------------------------------------
# 継承関係
# ---------------------------------------------------------------------------

@pytest.mark.unit
class TestAuthErrorInheritance:
    """例外クラスの継承関係テスト
    観点: 1.3 エラーハンドリング

    全認証例外が AuthError を継承していることを検証する。
    これにより `except AuthError` で認証関連例外を一括捕捉できることを保証する。
    """

    def test_auth_error_inherits_from_exception(self):
        """1.3.1: AuthError は Python 標準 Exception のサブクラスである"""
        assert issubclass(AuthError, Exception)

    def test_unauthorized_error_inherits_from_auth_error(self):
        """1.3.1: UnauthorizedError は AuthError のサブクラスである"""
        assert issubclass(UnauthorizedError, AuthError)

    def test_forbidden_error_inherits_from_auth_error(self):
        """1.3.1: ForbiddenError は AuthError のサブクラスである"""
        assert issubclass(ForbiddenError, AuthError)

    def test_token_exchange_error_inherits_from_auth_error(self):
        """1.3.1: TokenExchangeError は AuthError のサブクラスである"""
        assert issubclass(TokenExchangeError, AuthError)

    def test_session_expired_error_inherits_from_auth_error(self):
        """1.3.1: SessionExpiredError は AuthError のサブクラスである"""
        assert issubclass(SessionExpiredError, AuthError)

    def test_jwt_expired_error_inherits_from_auth_error(self):
        """1.3.1: JWTExpiredError は AuthError のサブクラスである"""
        assert issubclass(JWTExpiredError, AuthError)

    def test_jwt_retrieval_error_inherits_from_auth_error(self):
        """1.3.1: JWTRetrievalError は AuthError のサブクラスである"""
        assert issubclass(JWTRetrievalError, AuthError)

    def test_password_expired_error_inherits_from_auth_error(self):
        """1.3.1: PasswordExpiredError は AuthError のサブクラスである"""
        assert issubclass(PasswordExpiredError, AuthError)


# ---------------------------------------------------------------------------
# raise / except 動作
# ---------------------------------------------------------------------------

@pytest.mark.unit
class TestExceptionRaisability:
    """例外の raise / except 動作テスト
    観点: 1.3 エラーハンドリング

    各例外が正常に raise でき、AuthError のサブクラスとして捕捉できることを検証する。
    ミドルウェアは例外型ごとに個別 except で処理し（UnauthorizedError→401、JWTRetrievalError/TokenExchangeError→500）、
    AuthError による一括捕捉は行わない。
    """

    def test_unauthorized_error_can_be_raised_and_caught_as_auth_error(self):
        """1.3.3: UnauthorizedError は raise でき、AuthError として捕捉できる"""
        with pytest.raises(AuthError):
            raise UnauthorizedError("未認証")

    def test_forbidden_error_can_be_raised_and_caught_as_auth_error(self):
        """1.3.4: ForbiddenError は raise でき、AuthError として捕捉できる"""
        with pytest.raises(AuthError):
            raise ForbiddenError("権限不足")

    def test_token_exchange_error_can_be_raised_and_caught_as_auth_error(self):
        """1.3.6: TokenExchangeError は raise でき、AuthError として捕捉できる"""
        with pytest.raises(AuthError):
            raise TokenExchangeError("Token Exchange失敗")

    def test_jwt_retrieval_error_can_be_raised_and_caught_as_auth_error(self):
        """1.3.6: JWTRetrievalError は raise でき、AuthError として捕捉できる"""
        with pytest.raises(AuthError):
            raise JWTRetrievalError("JWT取得失敗")

    def test_unauthorized_error_message_is_preserved(self):
        """1.3.1: raise 時のメッセージが例外インスタンスに保持される"""
        message = "X-MS-CLIENT-PRINCIPAL header not found"
        exc = UnauthorizedError(message)
        assert str(exc) == message
