from flask import g, request, session, abort

from auth.services import find_user_by_email
from auth.exceptions import UnauthorizedError, JWTRetrievalError, TokenExchangeError
from common.logger import get_logger

logger = get_logger(__name__)

# テスト時はモックで上書き、本番時は create_app() 内で get_auth_provider() により初期化する
auth_provider = None

EXCLUDED_PATHS = [
    '/static',
    '/auth/login',
    '/auth/password-reset',
    '/.well-known',
    '/health',
]


def is_excluded_path(path: str) -> bool:
    """認証除外パスかどうかを判定"""
    return any(path.startswith(excluded) for excluded in EXCLUDED_PATHS)


def _sync_session(idp_user_info: dict, app_user: dict):
    """IdP認証情報・アプリユーザー情報をFlaskセッションに同期"""
    session['email'] = idp_user_info['email']
    session['user_id'] = app_user['user_id']
    session['user_type_id'] = app_user['user_type_id']
    session.permanent = True


def authenticate_request():
    """リクエスト認証処理（before_request）"""

    if is_excluded_path(request.path):
        return None

    try:
        idp_user_info = auth_provider.get_user_info(request)
    except UnauthorizedError:
        session.clear()
        abort(401)

    try:
        app_user = find_user_by_email(idp_user_info['email'])
    except UnauthorizedError:
        session.clear()
        abort(401)

    _sync_session(idp_user_info, app_user)

    g.current_user_id = session.get('user_id')
    g.current_user_type_id = session.get('user_type_id')

    if auth_provider.requires_additional_setup():
        allowed_paths = ['/account/password/change', '/auth/logout']
        if request.path not in allowed_paths and session.get('password_expired'):
            from flask import redirect, url_for
            return redirect(url_for('account.password_change'))

    try:
        from auth.token_exchange import TokenExchanger
        token_exchanger = TokenExchanger()
        databricks_token = token_exchanger.ensure_valid_token(auth_provider, request)
        g.databricks_token = databricks_token
    except JWTRetrievalError:
        abort(500)
    except TokenExchangeError:
        abort(500)

    logger.info("認証成功", extra={"email": idp_user_info.get("email")})

    return None
