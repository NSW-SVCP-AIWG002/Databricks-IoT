"""
TokenExchanger の単体テスト

観点: unit-test-perspectives.md
  - 2.1 正常系処理
  - 2.2 対象データ存在チェック
  - 1.3 エラーハンドリング
"""
import time
import pytest
from unittest.mock import MagicMock, patch
from flask import session

from iot_app.auth.token_exchange import TokenExchanger
from iot_app.auth.exceptions import TokenExchangeError, JWTRetrievalError


# ---------------------------------------------------------------------------
# フィクスチャ
# ---------------------------------------------------------------------------

@pytest.fixture
def exchanger(monkeypatch):
    """テスト用 TokenExchanger インスタンス（DATABRICKS_HOST をモック）"""
    monkeypatch.setenv("DATABRICKS_HOST", "test.azuredatabricks.net")
    return TokenExchanger()


# ---------------------------------------------------------------------------
# exchange_token()
# ---------------------------------------------------------------------------

@pytest.mark.unit
class TestTokenExchangerExchangeToken:
    """TokenExchanger.exchange_token() のテスト
    観点: 2.1 正常系処理, 1.3 エラーハンドリング
    """

    def test_exchange_success_returns_access_token_and_expires_in(self, exchanger):
        """2.1.1: 200 レスポンス時、access_token と expires_in を含む dict が返される"""
        # Arrange
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "access_token": "databricks-access-token",
            "token_type": "Bearer",
            "expires_in": 3600,
        }

        with patch("requests.post", return_value=mock_response):
            # Act
            result = exchanger.exchange_token("idp-jwt-token")

        # Assert
        assert result["access_token"] == "databricks-access-token"
        assert result["expires_in"] == 3600

    def test_exchange_posts_to_correct_endpoint_url(self, exchanger):
        """2.1.1: Token Exchange リクエストが正しいエンドポイント URL に送信される
        （設計書3.5.5: https://{DATABRICKS_HOST}/oidc/v1/token）"""
        # Arrange
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"access_token": "token", "expires_in": 3600}

        with patch("requests.post", return_value=mock_response) as mock_post:
            # Act
            exchanger.exchange_token("test-idp-jwt")

            # Assert
            called_url = mock_post.call_args.args[0]
            assert called_url == "https://test.azuredatabricks.net/oidc/v1/token"

    def test_exchange_uses_correct_request_parameters(self, exchanger):
        """2.1.1: Token Exchange リクエストに正しい grant_type とパラメータが設定される"""
        # Arrange
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"access_token": "token", "expires_in": 3600}

        with patch("requests.post", return_value=mock_response) as mock_post:
            # Act
            exchanger.exchange_token("test-idp-jwt")

            # Assert
            call_kwargs = mock_post.call_args.kwargs
            data = call_kwargs.get("data", {})
            assert data.get("grant_type") == "urn:ietf:params:oauth:grant-type:token-exchange"
            assert data.get("subject_token") == "test-idp-jwt"
            assert data.get("subject_token_type") == "urn:ietf:params:oauth:token-type:id_token"
            assert data.get("scope") == "all-apis"

    def test_exchange_non_200_raises_token_exchange_error(self, exchanger):
        """1.3.6: Databricks API が 200 以外を返した場合 TokenExchangeError が発生する"""
        # Arrange
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.text = "invalid_grant: token is expired"

        with patch("requests.post", return_value=mock_response):
            # Act & Assert
            with pytest.raises(TokenExchangeError):
                exchanger.exchange_token("invalid-jwt")



# ---------------------------------------------------------------------------
# cache_token()
# ---------------------------------------------------------------------------

@pytest.mark.unit
class TestTokenExchangerCacheToken:
    """TokenExchanger.cache_token() のテスト
    観点: 2.1 正常系処理
    """

    def test_cache_token_stores_access_token_in_session(self, exchanger, app):
        """2.1.1: cache_token() 後、セッションに databricks_token が保存される"""
        # Arrange & Act & Assert
        with app.test_request_context("/"):
            exchanger.cache_token("cached-token", 3600)
            assert session["databricks_token"] == "cached-token"

    def test_cache_token_sets_expiry_60_seconds_before_actual(self, exchanger, app):
        """2.1.1: トークンの有効期限は実際の expires_in より 60 秒早く設定される（早期再取得を防止）"""
        # Arrange & Act & Assert
        with app.test_request_context("/"):
            before = time.time()
            exchanger.cache_token("test-token", 3600)
            after = time.time()

            expires = session["databricks_token_expires"]
            # before + 3540 <= expires <= after + 3540
            assert before + 3540 <= expires <= after + 3540

    def test_cache_token_stores_expiry_timestamp_in_session(self, exchanger, app):
        """2.1.1: cache_token() 後、セッションに databricks_token_expires が保存される"""
        # Arrange & Act & Assert
        with app.test_request_context("/"):
            exchanger.cache_token("test-token", 3600)
            assert "databricks_token_expires" in session


# ---------------------------------------------------------------------------
# get_cached_token()
# ---------------------------------------------------------------------------

@pytest.mark.unit
class TestTokenExchangerGetCachedToken:
    """TokenExchanger.get_cached_token() のテスト
    観点: 2.1 正常系処理, 2.2 対象データ存在チェック
    """

    def test_returns_token_when_valid(self, exchanger, app):
        """2.2.1: 有効なキャッシュトークンが存在する場合、トークン文字列が返される"""
        # Arrange & Act & Assert
        with app.test_request_context("/"):
            session["databricks_token"] = "valid-token"
            session["databricks_token_expires"] = time.time() + 1800  # 30分後

            result = exchanger.get_cached_token()

            assert result == "valid-token"

    def test_returns_none_when_token_expired(self, exchanger, app):
        """2.2.3: トークンの有効期限が切れている場合、None が返される"""
        # Arrange & Act & Assert
        with app.test_request_context("/"):
            session["databricks_token"] = "expired-token"
            session["databricks_token_expires"] = time.time() - 60  # 1分前に切れた

            result = exchanger.get_cached_token()

            assert result is None

    def test_returns_none_when_no_token_in_session(self, exchanger, app):
        """2.2.2: セッションにトークンが存在しない場合、None が返される"""
        # Arrange & Act & Assert
        with app.test_request_context("/"):
            result = exchanger.get_cached_token()

            assert result is None


# ---------------------------------------------------------------------------
# ensure_valid_token()
# ---------------------------------------------------------------------------

@pytest.mark.unit
class TestTokenExchangerEnsureValidToken:
    """TokenExchanger.ensure_valid_token() のテスト
    観点: 2.1 正常系処理, 1.3 エラーハンドリング
    """

    def test_uses_cached_token_without_exchange(self, exchanger, app):
        """2.1.1: 有効なキャッシュトークンがある場合、Token Exchange は実行されない"""
        # Arrange
        mock_provider = MagicMock()

        with app.test_request_context("/"):
            session["databricks_token"] = "cached-token"
            session["databricks_token_expires"] = time.time() + 1800

            with patch.object(exchanger, "exchange_token") as mock_exchange:
                # Act
                result = exchanger.ensure_valid_token(mock_provider, MagicMock())

        # Assert
        assert result == "cached-token"
        mock_exchange.assert_not_called()

    def test_exchanges_token_when_cache_is_empty(self, exchanger, app):
        """2.1.1: キャッシュが空の場合、Token Exchange を実行して新しいトークンを返す"""
        # Arrange
        mock_provider = MagicMock()
        mock_provider.get_jwt_for_token_exchange.return_value = "idp-jwt"

        with app.test_request_context("/"):
            with patch.object(
                exchanger,
                "exchange_token",
                return_value={"access_token": "new-token", "expires_in": 3600},
            ) as mock_exchange:
                with patch.object(exchanger, "cache_token"):
                    # Act
                    result = exchanger.ensure_valid_token(mock_provider, MagicMock())

        # Assert
        assert result == "new-token"
        mock_exchange.assert_called_once_with("idp-jwt")

    def test_jwt_retrieval_error_raises_jwt_retrieval_error(self, exchanger, app):
        """1.3.6: JWT 取得に失敗した場合（認証基盤の異常）、JWTRetrievalError が発生する"""
        # Arrange
        from iot_app.auth.exceptions import UnauthorizedError

        mock_provider = MagicMock()
        mock_provider.get_jwt_for_token_exchange.side_effect = UnauthorizedError("JWT not found")

        # Act & Assert
        with app.test_request_context("/"):
            with pytest.raises(JWTRetrievalError):
                exchanger.ensure_valid_token(mock_provider, MagicMock())

    def test_token_exchange_error_propagates(self, exchanger, app):
        """1.3.1: Token Exchange 失敗時、TokenExchangeError が伝播する"""
        # Arrange
        mock_provider = MagicMock()
        mock_provider.get_jwt_for_token_exchange.return_value = "idp-jwt"

        # Act & Assert
        with app.test_request_context("/"):
            with patch.object(
                exchanger,
                "exchange_token",
                side_effect=TokenExchangeError("exchange failed"),
            ):
                with pytest.raises(TokenExchangeError):
                    exchanger.ensure_valid_token(mock_provider, MagicMock())

    def test_caches_token_after_successful_exchange(self, exchanger, app):
        """2.1.1: Token Exchange 成功後、取得したトークンがキャッシュされる"""
        # Arrange
        mock_provider = MagicMock()
        mock_provider.get_jwt_for_token_exchange.return_value = "idp-jwt"

        with app.test_request_context("/"):
            with patch.object(
                exchanger,
                "exchange_token",
                return_value={"access_token": "new-token", "expires_in": 3600},
            ):
                with patch.object(exchanger, "cache_token") as mock_cache:
                    # Act
                    exchanger.ensure_valid_token(mock_provider, MagicMock())

        # Assert
        mock_cache.assert_called_once_with("new-token", 3600)


# ---------------------------------------------------------------------------
# ロギング
# ---------------------------------------------------------------------------

@pytest.mark.unit
class TestTokenExchangerLogging:
    """TokenExchanger のロギングテスト
    観点: 1.4 ログ出力機能

    実装時に以下のログ出力を行うこと（設計書セクション 6.5 Token Exchangeパターン）:
      - INFO : Token Exchange 成功時（外部API呼び出し開始・完了）
      - ERROR: Token Exchange API が非200を返した場合（外部API失敗）
    必須フィールド: service="databricks_token_exchange", operation="Token Exchange",
                    duration_ms（INFO完了・ERROR共通）, status・failure_reason（ERRORのみ）
    """

    def test_exchange_success_logs_info_with_required_fields(self, exchanger, caplog):
        """1.4.1.2: Token Exchange 成功時に INFO レベルで service / operation / duration_ms フィールド付きログが出力される"""
        import logging

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"access_token": "token", "expires_in": 3600}

        with patch("requests.post", return_value=mock_response):
            with caplog.at_level(logging.INFO):
                exchanger.exchange_token("valid-jwt")

        info_records = [r for r in caplog.records if r.levelno == logging.INFO]
        assert info_records, "INFO レベルのログが出力されていない"
        completion_record = next(
            (r for r in info_records if getattr(r, "duration_ms", None) is not None), None
        )
        assert completion_record is not None, "duration_ms フィールドを含む INFO ログがない"
        assert getattr(completion_record, "service", None) == "databricks_token_exchange"
        assert getattr(completion_record, "operation", None) == "Token Exchange"

    def test_exchange_failure_logs_error_with_required_fields(self, exchanger, caplog):
        """1.4.1.1: Token Exchange API が非200を返した場合に ERROR レベルで必須フィールド付きログが出力される
        （service, operation, status, duration_ms, failure_reason）
        """
        import logging

        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.text = "invalid_grant: token is expired"

        with patch("requests.post", return_value=mock_response):
            with caplog.at_level(logging.ERROR):
                try:
                    exchanger.exchange_token("invalid-jwt")
                except TokenExchangeError:
                    pass

        error_records = [r for r in caplog.records if r.levelno == logging.ERROR]
        assert error_records, "ERROR レベルのログが出力されていない"
        rec = error_records[0]
        assert getattr(rec, "service", None) == "databricks_token_exchange"
        assert getattr(rec, "operation", None) == "Token Exchange"
        assert getattr(rec, "status", None) == 400
        assert getattr(rec, "duration_ms", None) is not None
        assert getattr(rec, "failure_reason", None) is not None
