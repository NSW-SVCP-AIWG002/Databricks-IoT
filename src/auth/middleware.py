import os
import logging
from types import SimpleNamespace

from flask import g, request

logger = logging.getLogger(__name__)

EXCLUDED_PATHS = [
    '/static',
    '/auth/login',
    '/auth/password-reset',
    '/.well-known',
    '/health',
]


def is_excluded_path(path: str) -> bool:
    return any(path.startswith(excluded) for excluded in EXCLUDED_PATHS)


def authenticate_request():
    """リクエスト認証処理（before_request）"""

    if is_excluded_path(request.path):
        return None

    # 即席: 開発環境バイパス（Azure Easy Auth なし）
    if os.getenv('FLASK_ENV') == 'development':
        logger.debug('開発環境バイパス: モックユーザーをセット')
        g.current_user = SimpleNamespace(
            user_id=1,
            user_type_id=1,
            organization_id=1,
            email_address='dev@example.com',
        )
        g.current_user_id = 1
        g.current_user_type_id = 1
        g.databricks_token = ''
        return None

    # 本番: 未実装（Azure Easy Auth 実装時に追加）
    return None
