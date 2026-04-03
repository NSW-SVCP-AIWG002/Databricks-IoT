import os
from types import SimpleNamespace

from flask import g, request, session, abort, render_template, current_app

from iot_app.auth.services import find_user_by_email
from iot_app.auth.exceptions import UnauthorizedError, JWTRetrievalError, TokenExchangeError
from iot_app.common.logger import get_logger

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
    session['organization_id'] = app_user['organization_id']
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
        # IdP認証済みだがアプリ未登録 → 403エラーページを直接返却
        # ※ abort(403) は使用しない。他の403（ロール不足）はモーダル表示だが、
        #   このケースはページ表示前に発生するため middleware 内で直接レンダリングする。
        logger.warning("アクセス拒否：アプリ未登録ユーザー", extra={"email": idp_user_info.get("email")})
        return render_template("errors/403.html"), 403

    _sync_session(idp_user_info, app_user)

    g.current_user = SimpleNamespace()
    g.current_user.user_id = session.get('user_id')
    g.current_user.user_type_id = session.get('user_type_id')
    g.current_user.organization_id = session.get('organization_id')

    if auth_provider.requires_additional_setup():
        allowed_paths = ['/account/password/change', '/auth/logout']
        if request.path not in allowed_paths and session.get('password_expired'):
            from flask import redirect, url_for
            return redirect(url_for('account.password_change'))

    if current_app.config.get('AUTH_TYPE') == 'dev':
        # ローカル開発用: Token Exchange をスキップし DEV_DATABRICKS_TOKEN を直接使用
        dev_token = os.getenv('DEV_DATABRICKS_TOKEN')
        if not dev_token:
            logger.error("DEV_DATABRICKS_TOKEN が設定されていません")
            abort(500)
        g.current_user.databricks_token = dev_token
    else:
        try:
            from iot_app.auth.token_exchange import TokenExchanger
            token_exchanger = TokenExchanger()
            g.current_user.databricks_token = token_exchanger.ensure_valid_token(auth_provider, request)
        except JWTRetrievalError:
            abort(500)
        except TokenExchangeError:
            abort(500)

    logger.info("認証成功", extra={"email": idp_user_info.get("email")})

    return None
