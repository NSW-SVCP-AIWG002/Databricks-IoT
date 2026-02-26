"""
common/error_handlers.py の単体テスト

観点: unit-test-perspectives.md
  - 1.3 エラーハンドリング
  - 1.4 ログ出力機能

検証内容:
  - 500系例外発生時にERRORレベルでログが出力される（exc_info=True）
  - 401例外発生時にWARNレベルでログが出力される（raw_emailあり/なし）
  - 401ハンドラーはセッションをクリアしてログインへリダイレクトする
  - 400系例外発生時にWARNレベルでログが出力される
"""
import pytest
from unittest.mock import patch

from werkzeug.exceptions import Unauthorized, NotFound

from iot_app.common.error_handlers import handle_500, handle_401, handle_4xx


# ---------------------------------------------------------------------------
# handle_500()
# ---------------------------------------------------------------------------

@pytest.mark.unit
class TestHandle500:
    """handle_500() のテスト
    観点: 1.4.1 ログレベル
    """

    def test_500_handler_logs_error_with_exc_info(self, app):
        """1.4.1.1: 500系例外発生時にERRORレベルでログが出力され、スタックトレース（exc_info）が含まれる"""
        error = Exception("some internal error")

        with app.test_request_context("/"):
            with patch("iot_app.common.error_handlers.logger") as mock_logger:
                with patch("iot_app.common.error_handlers.render_template", return_value=""):
                    handle_500(error)

                    mock_logger.error.assert_called_once()
                    _, kwargs = mock_logger.error.call_args
                    assert kwargs.get("exc_info") is True


# ---------------------------------------------------------------------------
# handle_401()
# ---------------------------------------------------------------------------

@pytest.mark.unit
class TestHandle401:
    """handle_401() のテスト
    観点: 1.3 エラーハンドリング, 1.4.1 ログレベル
    """

    def test_401_handler_logs_warning_with_raw_email(self, app):
        """1.4.1.2: g.failed_email が設定されている場合、raw_email 付きで WARN ログが出力される"""
        from flask import g
        error = Unauthorized()

        with app.test_request_context("/"):
            g.failed_email = "unknown@external.com"
            with patch("iot_app.common.error_handlers.logger") as mock_logger:
                with patch("iot_app.common.error_handlers.redirect", return_value=""):
                    with patch("iot_app.common.error_handlers.url_for", return_value="/auth/login"):
                        handle_401(error)

                        mock_logger.warning.assert_called_once()
                        _, kwargs = mock_logger.warning.call_args
                        assert kwargs.get("extra", {}).get("raw_email") == "unknown@external.com"

    def test_401_handler_logs_warning_without_email(self, app):
        """1.4.1.2: g.failed_email が未設定の場合でも WARN ログが出力される"""
        error = Unauthorized()

        with app.test_request_context("/"):
            with patch("iot_app.common.error_handlers.logger") as mock_logger:
                with patch("iot_app.common.error_handlers.redirect", return_value=""):
                    with patch("iot_app.common.error_handlers.url_for", return_value="/auth/login"):
                        handle_401(error)

                        mock_logger.warning.assert_called_once()

    def test_401_handler_clears_session_and_redirects(self, app):
        """1.3.3: 401 ハンドラーはセッションをクリアしてログインへリダイレクトする"""
        from flask import session as flask_session
        error = Unauthorized()

        with app.test_request_context("/"):
            with patch("iot_app.common.error_handlers.logger"):
                with patch("iot_app.common.error_handlers.redirect") as mock_redirect:
                    with patch("iot_app.common.error_handlers.url_for", return_value="/auth/login"):
                        flask_session["email"] = "existing@example.com"
                        handle_401(error)

                        assert flask_session.get("email") is None
                        mock_redirect.assert_called_once_with("/auth/login")


# ---------------------------------------------------------------------------
# handle_4xx()
# ---------------------------------------------------------------------------

@pytest.mark.unit
class TestHandle4xx:
    """handle_4xx() のテスト
    観点: 1.4.1 ログレベル
    """

    def test_4xx_handler_logs_warning(self, app):
        """1.4.1.2: 400系例外発生時に WARN レベルでログが出力される"""
        error = NotFound()

        with app.test_request_context("/"):
            with patch("iot_app.common.error_handlers.logger") as mock_logger:
                handle_4xx(error)

                mock_logger.warning.assert_called_once()
                _, kwargs = mock_logger.warning.call_args
                assert kwargs.get("extra", {}).get("httpStatus") == 404
