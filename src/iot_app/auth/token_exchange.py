import os
import time

import requests
from flask import session

from iot_app.auth.exceptions import TokenExchangeError, JWTExpiredError, JWTRetrievalError, UnauthorizedError
from iot_app.common.logger import get_logger

logger = get_logger(__name__)


class TokenExchanger:
    """Token Exchange処理クラス"""

    def __init__(self):
        self.databricks_host = os.getenv('DATABRICKS_HOST')
        self.token_endpoint = f"https://{self.databricks_host}/oidc/v1/token"

    def exchange_token(self, idp_jwt: str) -> dict:
        """IdP JWTをDatabricksトークンに交換

        Returns:
            dict: {'access_token': str, 'expires_in': int}

        Raises:
            TokenExchangeError: Databricks API が 200 以外を返した場合
        """
        logger.info("外部API呼び出し開始", extra={
            "service": "databricks_token_exchange",
            "operation": "Token Exchange",
        })
        start = time.time()

        payload = {
            'grant_type': 'urn:ietf:params:oauth:grant-type:token-exchange',
            'subject_token': idp_jwt,
            'subject_token_type': 'urn:ietf:params:oauth:token-type:id_token',
            'scope': 'all-apis',
        }

        response = requests.post(self.token_endpoint, data=payload)
        duration_ms = int((time.time() - start) * 1000)

        if response.status_code != 200:
            logger.error("外部API失敗", exc_info=False, extra={
                "service": "databricks_token_exchange",
                "operation": "Token Exchange",
                "status": response.status_code,
                "duration_ms": duration_ms,
                "failure_reason": response.text[:200],
            })
            if 'TOKEN_EXPIRED' in response.text:
                raise JWTExpiredError(f"Token Exchange failed: {response.text}")
            raise TokenExchangeError(f"Token Exchange failed: {response.text}")

        logger.info("外部API完了", extra={
            "service": "databricks_token_exchange",
            "operation": "Token Exchange",
            "duration_ms": duration_ms,
        })

        result = response.json()
        return {
            'access_token': result['access_token'],
            'expires_in': result['expires_in'],
        }

    def cache_token(self, access_token: str, expires_in: int):
        """トークンをセッションにキャッシュ"""
        session['databricks_token'] = access_token
        session['databricks_token_expires'] = time.time() + expires_in - 60

    def get_cached_token(self):
        """キャッシュされたトークンを取得"""
        token = session.get('databricks_token')
        expires = session.get('databricks_token_expires', 0)

        if token and time.time() < expires:
            return token
        return None

    def ensure_valid_token(self, auth_provider, request) -> str:
        """有効なDatabricksトークンを確保（期限切れなら再取得）

        Args:
            auth_provider: AuthProviderインスタンス
            request: Flaskリクエストオブジェクト

        Returns:
            str: 有効なDatabricksアクセストークン

        Raises:
            JWTRetrievalError: JWT取得に失敗した場合（認証基盤の異常）
            TokenExchangeError: Token Exchange自体に失敗した場合
        """
        token = self.get_cached_token()
        if token:
            return token

        try:
            jwt_token = auth_provider.get_jwt_for_token_exchange(request)
        except UnauthorizedError as e:
            raise JWTRetrievalError(str(e)) from e

        result = self.exchange_token(jwt_token)
        self.cache_token(result['access_token'], result['expires_in'])
        return result['access_token']
