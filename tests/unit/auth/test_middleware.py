"""
認証ミドルウェアの単体テスト

観点: unit-test-perspectives.md
  - 2.1 正常系処理
  - 1.3 エラーハンドリング
"""
import pytest
from unittest.mock import MagicMock, patch
from flask import session
from werkzeug.exceptions import InternalServerError, Unauthorized

from iot_app.auth.middleware import is_excluded_path, _sync_session, authenticate_request
from iot_app.auth.exceptions import UnauthorizedError, JWTRetrievalError, TokenExchangeError, JWTExpiredError


# ---------------------------------------------------------------------------
# is_excluded_path()
# ---------------------------------------------------------------------------

@pytest.mark.unit
class TestIsExcludedPath:
    """is_excluded_path() のテスト
    観点: 2.1 正常系処理
    """

    def test_static_file_path_is_excluded(self):
        """2.1.1: /static/* は認証チェックをスキップする"""
        assert is_excluded_path("/static/css/main.css") is True

    def test_static_root_is_excluded(self):
        """2.1.1: /static 直下も認証チェックをスキップする"""
        assert is_excluded_path("/static") is True

    def test_auth_login_is_excluded(self):
        """2.1.1: /auth/login は認証チェックをスキップする（オンプレミス環境のログイン画面）"""
        assert is_excluded_path("/auth/login") is True

    def test_auth_password_reset_is_excluded(self):
        """2.1.1: /auth/password-reset/* は認証チェックをスキップする"""
        assert is_excluded_path("/auth/password-reset/confirm") is True

    def test_well_known_is_excluded(self):
        """2.1.1: /.well-known/* は認証チェックをスキップする（OIDC設定エンドポイント）"""
        assert is_excluded_path("/.well-known/openid-configuration") is True

    def test_health_is_excluded(self):
        """2.1.1: /health は認証チェックをスキップする（ヘルスチェック）"""
        assert is_excluded_path("/health") is True

    def test_dashboard_is_not_excluded(self):
        """2.1.1: /dashboard は認証対象パスである"""
        assert is_excluded_path("/dashboard") is False

    def test_root_path_is_not_excluded(self):
        """2.1.1: / は認証対象パスである"""
        assert is_excluded_path("/") is False

    def test_admin_path_is_not_excluded(self):
        """2.1.1: /admin/* は認証対象パスである（ADM-001〜016）"""
        assert is_excluded_path("/admin/devices") is False

    def test_alert_path_is_not_excluded(self):
        """2.1.1: /alert/* は認証対象パスである（ALT-001〜006）"""
        assert is_excluded_path("/alert/alert-settings") is False

    def test_notice_path_is_not_excluded(self):
        """2.1.1: /notice/* は認証対象パスである（NTC-001〜006）"""
        assert is_excluded_path("/notice/mail-settings") is False

    def test_account_path_is_not_excluded(self):
        """2.1.1: /account/* は認証対象パスである（ACC-001〜002）"""
        assert is_excluded_path("/account/language") is False

    def test_transfer_path_is_not_excluded(self):
        """2.1.1: /transfer/* は認証対象パスである（TRF-001）"""
        assert is_excluded_path("/transfer/csv-import") is False


# ---------------------------------------------------------------------------
# _sync_session()
# ---------------------------------------------------------------------------

@pytest.mark.unit
class TestSyncSession:
    """_sync_session() のテスト
    観点: 2.1 正常系処理
    """

    def _default_idp_user_info(self):
        return {"email": "yamada@example.com"}

    def _default_app_user(self):
        return {"user_id": 42, "user_type_id": 2}

    def test_sync_session_sets_email(self, app):
        """2.1.1: IdP から受け取った email が Flask セッションに保存される"""
        with app.test_request_context("/"):
            _sync_session(self._default_idp_user_info(), self._default_app_user())
            assert session["email"] == "yamada@example.com"

    def test_sync_session_sets_user_id_from_app_user(self, app):
        """2.1.1: find_user_by_email() で取得した app_user の user_id が Flask セッションに保存される
        （IdP の識別子ではなく、MySQL の user_master.user_id）
        """
        with app.test_request_context("/"):
            _sync_session(self._default_idp_user_info(), self._default_app_user())
            assert session["user_id"] == 42

    def test_sync_session_sets_user_type_id_from_app_user(self, app):
        """2.1.1: find_user_by_email() で取得した app_user の user_type_id が Flask セッションに保存される"""
        with app.test_request_context("/"):
            _sync_session(self._default_idp_user_info(), self._default_app_user())
            assert session["user_type_id"] == 2

    def test_sync_session_sets_permanent_true(self, app):
        """2.1.1: セッションは永続化（PERMANENT_SESSION_LIFETIME 適用）される"""
        with app.test_request_context("/"):
            _sync_session(self._default_idp_user_info(), self._default_app_user())
            assert session.permanent is True


# ---------------------------------------------------------------------------
# authenticate_request()
# ---------------------------------------------------------------------------

@pytest.mark.unit
class TestAuthenticateRequest:
    """authenticate_request() のテスト
    観点: 2.1 正常系処理, 1.3 エラーハンドリング
    """

    def _make_mock_provider(self, user_info=None, requires_setup=False):
        """テスト用 AuthProvider モックを生成するヘルパー"""
        mock_provider = MagicMock()
        if user_info:
            mock_provider.get_user_info.return_value = user_info
        mock_provider.requires_additional_setup.return_value = requires_setup
        mock_provider.logout_url.return_value = "/.auth/logout"
        return mock_provider

    def _default_user_info(self):
        return {"email": "yamada@example.com"}

    def _default_app_user(self):
        return {"user_id": 42, "user_type_id": 2}

    def test_excluded_path_skips_auth_and_returns_none(self, app):
        """2.1.1: 認証除外パスへのリクエストは認証チェックをスキップして None を返す"""
        mock_provider = self._make_mock_provider()

        with app.test_request_context("/static/css/main.css"):
            with patch("iot_app.auth.middleware.auth_provider", mock_provider):
                result = authenticate_request()

        assert result is None
        mock_provider.get_user_info.assert_not_called()

    def test_idp_auth_failure_clears_session_and_raises_401(self, app):
        """1.3.3: IdP 認証失敗時、Flask セッションをクリアして 401 を発生させる"""
        mock_provider = self._make_mock_provider()
        mock_provider.get_user_info.side_effect = UnauthorizedError("not authenticated")

        with app.test_request_context("/dashboard"):
            with patch("iot_app.auth.middleware.auth_provider", mock_provider):
                session["email"] = "existing@example.com"

                with pytest.raises(Unauthorized):
                    authenticate_request()

                assert session.get("email") is None

    def test_user_not_registered_aborts_403(self, app):
        """1.3.3: IdP 認証済みだがアプリ未登録ユーザーの場合、abort(403) を発生させる
        （セッションはクリアしない）
        """
        from werkzeug.exceptions import Forbidden

        mock_provider = self._make_mock_provider(user_info=self._default_user_info())

        with app.test_request_context("/dashboard"):
            with patch("iot_app.auth.middleware.auth_provider", mock_provider):
                with patch("iot_app.auth.middleware.find_user_by_email",
                           side_effect=UnauthorizedError("user not found")):
                    session["email"] = "existing@example.com"

                    with pytest.raises(Forbidden):
                        authenticate_request()

                    # IdP認証は成功しているためセッションはクリアしない
                    assert session.get("email") == "existing@example.com"

    def test_idp_auth_success_syncs_session_and_returns_none(self, app):
        """2.1.1: IdP 認証成功時、セッションが同期されて None を返す"""
        mock_provider = self._make_mock_provider(
            user_info=self._default_user_info(),
            requires_setup=False,
        )
        mock_exchanger = MagicMock()
        mock_exchanger.ensure_valid_token.return_value = "valid-databricks-token"

        with app.test_request_context("/dashboard"):
            with patch("iot_app.auth.middleware.auth_provider", mock_provider):
                with patch("iot_app.auth.middleware.find_user_by_email",
                           return_value=self._default_app_user()):
                    with patch("iot_app.auth.token_exchange.TokenExchanger",
                               return_value=mock_exchanger):
                        result = authenticate_request()

                        assert session["email"] == "yamada@example.com"

        assert result is None

    def test_databricks_token_set_to_g_on_success(self, app):
        """2.1.1: Token Exchange 成功後、g.current_user.databricks_token に有効なトークンが設定される"""
        from flask import g

        mock_provider = self._make_mock_provider(
            user_info=self._default_user_info(),
            requires_setup=False,
        )
        mock_exchanger = MagicMock()
        mock_exchanger.ensure_valid_token.return_value = "valid-databricks-token"

        with app.test_request_context("/dashboard"):
            with patch("iot_app.auth.middleware.auth_provider", mock_provider):
                with patch("iot_app.auth.middleware.find_user_by_email",
                           return_value=self._default_app_user()):
                    with patch("iot_app.auth.token_exchange.TokenExchanger",
                               return_value=mock_exchanger):
                        authenticate_request()
                        assert g.current_user.databricks_token == "valid-databricks-token"

    def test_user_context_set_to_g_from_session(self, app):
        """2.1.1: IdP 認証成功後、g.current_user.user_id / g.current_user.user_type_id が
        _sync_session によりセッション経由で設定される（設計書3.1 ステップ5）"""
        from flask import g

        mock_provider = self._make_mock_provider(
            user_info=self._default_user_info(),
            requires_setup=False,
        )
        mock_exchanger = MagicMock()
        mock_exchanger.ensure_valid_token.return_value = "valid-token"

        with app.test_request_context("/dashboard"):
            with patch("iot_app.auth.middleware.auth_provider", mock_provider):
                with patch("iot_app.auth.middleware.find_user_by_email",
                           return_value=self._default_app_user()):
                    with patch("iot_app.auth.token_exchange.TokenExchanger",
                               return_value=mock_exchanger):
                        authenticate_request()

                        assert g.current_user.user_id == 42
                        assert g.current_user.user_type_id == 2

    def test_dev_mode_uses_dev_databricks_token(self, app, monkeypatch):
        """2.1.7: AUTH_TYPE=dev のとき Token Exchange をスキップし
        DEV_DATABRICKS_TOKEN 環境変数の値が g.current_user.databricks_token に設定される
        """
        from flask import g

        monkeypatch.setenv("DEV_DATABRICKS_TOKEN", "dev-token-xyz")
        mock_provider = self._make_mock_provider(
            user_info=self._default_user_info(),
            requires_setup=False,
        )

        with app.test_request_context("/dashboard"):
            app.config['AUTH_TYPE'] = 'dev'
            with patch("iot_app.auth.middleware.auth_provider", mock_provider):
                with patch("iot_app.auth.middleware.find_user_by_email",
                           return_value=self._default_app_user()):
                    authenticate_request()
                    assert g.current_user.databricks_token == "dev-token-xyz"

    def test_dev_mode_aborts_500_when_dev_token_not_set(self, app, monkeypatch):
        """1.3.7: AUTH_TYPE=dev かつ DEV_DATABRICKS_TOKEN 未設定時は 500 エラーになる"""
        monkeypatch.delenv("DEV_DATABRICKS_TOKEN", raising=False)
        mock_provider = self._make_mock_provider(
            user_info=self._default_user_info(),
            requires_setup=False,
        )

        with app.test_request_context("/dashboard"):
            app.config['AUTH_TYPE'] = 'dev'
            with patch("iot_app.auth.middleware.auth_provider", mock_provider):
                with patch("iot_app.auth.middleware.find_user_by_email",
                           return_value=self._default_app_user()):
                    with pytest.raises(InternalServerError):
                        authenticate_request()

    def test_jwt_retrieval_failure_aborts_with_500(self, app):
        """1.3.6: JWT 取得失敗時（認証基盤の異常）、500 エラーが発生する"""
        mock_provider = self._make_mock_provider(
            user_info=self._default_user_info(),
            requires_setup=False,
        )
        mock_exchanger = MagicMock()
        mock_exchanger.ensure_valid_token.side_effect = JWTRetrievalError("JWT not found")

        with app.test_request_context("/dashboard"):
            with patch("iot_app.auth.middleware.auth_provider", mock_provider):
                with patch("iot_app.auth.middleware.find_user_by_email",
                           return_value=self._default_app_user()):
                    with patch("iot_app.auth.token_exchange.TokenExchanger",
                               return_value=mock_exchanger):
                        with pytest.raises(InternalServerError):
                            authenticate_request()

    def test_token_exchange_failure_aborts_with_500(self, app):
        """1.3.6: Token Exchange 失敗時（Databricks側エラー）、500 エラーが発生する"""
        mock_provider = self._make_mock_provider(
            user_info=self._default_user_info(),
            requires_setup=False,
        )
        mock_exchanger = MagicMock()
        mock_exchanger.ensure_valid_token.side_effect = TokenExchangeError("exchange failed")

        with app.test_request_context("/dashboard"):
            with patch("iot_app.auth.middleware.auth_provider", mock_provider):
                with patch("iot_app.auth.middleware.find_user_by_email",
                           return_value=self._default_app_user()):
                    with patch("iot_app.auth.token_exchange.TokenExchanger",
                               return_value=mock_exchanger):
                        with pytest.raises(InternalServerError):
                            authenticate_request()


# ---------------------------------------------------------------------------
# JWTExpiredError ハンドリング
# ---------------------------------------------------------------------------

@pytest.mark.unit
class TestJWTExpiredHandling:
    """JWTExpiredError 発生時のレスポンス分岐テスト
    観点: 1.3 エラーハンドリング

    JWTExpiredError（Databricks Token Exchange の JWT 期限切れ）発生時の挙動:
      - 非AJAXリクエスト: token_refresh.html を返す（通常ページとしてリフレッシュ処理）
      - AJAXリクエスト: 401 + {"error": "token_expired"} JSON を返す
        （フロントのグローバル fetch インターセプターが window.location.reload() を実行）
    """

    def _make_mock_provider(self):
        mock_provider = MagicMock()
        mock_provider.get_user_info.return_value = {"email": "yamada@example.com"}
        mock_provider.requires_additional_setup.return_value = False
        return mock_provider

    def _default_app_user(self):
        return {"user_id": 42, "user_type_id": 2, "organization_id": 10}

    def _make_expired_exchanger(self):
        mock_exchanger = MagicMock()
        mock_exchanger.ensure_valid_token.side_effect = JWTExpiredError("token expired")
        return mock_exchanger

    def test_non_ajax_jwt_expired_returns_token_refresh_template(self, app):
        """1.3.5: 通常リクエスト（非AJAX）でJWT期限切れの場合、token_refresh.html を返す"""
        with app.test_request_context("/dashboard"):
            with patch("iot_app.auth.middleware.auth_provider", self._make_mock_provider()):
                with patch("iot_app.auth.middleware.find_user_by_email",
                           return_value=self._default_app_user()):
                    with patch("iot_app.auth.token_exchange.TokenExchanger",
                               return_value=self._make_expired_exchanger()):
                        with patch("iot_app.auth.middleware.render_template",
                                   return_value="<html>token_refresh</html>") as mock_render:
                            result = authenticate_request()

        mock_render.assert_called_once()
        assert mock_render.call_args[0][0] == "auth/token_refresh.html"
        assert result == "<html>token_refresh</html>"

    def test_xhr_header_jwt_expired_returns_401_json(self, app):
        """1.3.5: X-Requested-With: XMLHttpRequest の場合、JWT期限切れは 401 + JSON を返す"""
        with app.test_request_context(
            "/dashboard",
            headers={"X-Requested-With": "XMLHttpRequest"},
        ):
            with patch("iot_app.auth.middleware.auth_provider", self._make_mock_provider()):
                with patch("iot_app.auth.middleware.find_user_by_email",
                           return_value=self._default_app_user()):
                    with patch("iot_app.auth.token_exchange.TokenExchanger",
                               return_value=self._make_expired_exchanger()):
                        result = authenticate_request()

        response, status_code = result
        assert status_code == 401
        assert response.get_json() == {"error": "token_expired"}

    def test_json_content_type_jwt_expired_returns_401_json(self, app):
        """1.3.5: Content-Type: application/json（request.is_json）の場合、JWT期限切れは 401 + JSON を返す"""
        with app.test_request_context(
            "/dashboard",
            content_type="application/json",
        ):
            with patch("iot_app.auth.middleware.auth_provider", self._make_mock_provider()):
                with patch("iot_app.auth.middleware.find_user_by_email",
                           return_value=self._default_app_user()):
                    with patch("iot_app.auth.token_exchange.TokenExchanger",
                               return_value=self._make_expired_exchanger()):
                        result = authenticate_request()

        response, status_code = result
        assert status_code == 401
        assert response.get_json() == {"error": "token_expired"}

    def test_accept_json_header_jwt_expired_returns_401_json(self, app):
        """1.3.5: Accept: application/json ヘッダーの場合、JWT期限切れは 401 + JSON を返す"""
        with app.test_request_context(
            "/dashboard",
            headers={"Accept": "application/json"},
        ):
            with patch("iot_app.auth.middleware.auth_provider", self._make_mock_provider()):
                with patch("iot_app.auth.middleware.find_user_by_email",
                           return_value=self._default_app_user()):
                    with patch("iot_app.auth.token_exchange.TokenExchanger",
                               return_value=self._make_expired_exchanger()):
                        result = authenticate_request()

        response, status_code = result
        assert status_code == 401
        assert response.get_json() == {"error": "token_expired"}


# ---------------------------------------------------------------------------
# ロギング
# ---------------------------------------------------------------------------

@pytest.mark.unit
class TestAuthenticateRequestLogging:
    """authenticate_request() のロギングテスト
    観点: 1.4 ログ出力機能

    実装時に以下のログ出力を行うこと:
      - INFO : 認証成功時
      ※ WARN（400系）および ERROR（500系）は error_handlers.py が自動ログ出力するため、test_error_handlers.py で検証
    """

    def _make_mock_provider(self, user_info=None, requires_setup=False):
        mock_provider = MagicMock()
        if user_info:
            mock_provider.get_user_info.return_value = user_info
        mock_provider.requires_additional_setup.return_value = requires_setup
        mock_provider.logout_url.return_value = "/.auth/logout"
        return mock_provider

    def _default_user_info(self):
        return {"email": "yamada@example.com"}

    def _default_app_user(self):
        return {"user_id": 42, "user_type_id": 2}

    def test_user_not_registered_logs_warning(self, app, caplog):
        """1.4.1.3: アプリ未登録ユーザーのアクセス時に WARN レベルで email フィールド付きログが出力される"""
        import logging
        from werkzeug.exceptions import Forbidden

        mock_provider = self._make_mock_provider(user_info=self._default_user_info())

        with app.test_request_context("/dashboard"):
            with patch("iot_app.auth.middleware.auth_provider", mock_provider):
                with patch("iot_app.auth.middleware.find_user_by_email",
                           side_effect=UnauthorizedError("user not found")):
                    with caplog.at_level(logging.WARNING):
                        with pytest.raises(Forbidden):
                            authenticate_request()

        warn_records = [r for r in caplog.records if r.levelno == logging.WARNING]
        assert warn_records, "WARNING レベルのログが出力されていない"
        assert any(getattr(r, "email", None) is not None for r in warn_records), \
            "WARNING ログに email フィールドが含まれていない"

    def test_auth_success_logs_info(self, app, caplog):
        """1.4.1.3: 認証成功時に INFO レベルで email フィールド付きログが出力される
        （設計書セクション7: extra={"email": ...} が必須フィールド）
        """
        import logging

        mock_provider = self._make_mock_provider(
            user_info=self._default_user_info(),
            requires_setup=False,
        )
        mock_exchanger = MagicMock()
        mock_exchanger.ensure_valid_token.return_value = "valid-token"

        with app.test_request_context("/dashboard"):
            with patch("iot_app.auth.middleware.auth_provider", mock_provider):
                with patch("iot_app.auth.middleware.find_user_by_email",
                           return_value=self._default_app_user()):
                    with patch("iot_app.auth.token_exchange.TokenExchanger",
                               return_value=mock_exchanger):
                        with caplog.at_level(logging.INFO):
                            authenticate_request()

        info_records = [r for r in caplog.records if r.levelno == logging.INFO]
        assert info_records, "INFO レベルのログが出力されていない"
        assert any(getattr(r, "email", None) is not None for r in info_records), \
            "INFO ログに email フィールドが含まれていない"


