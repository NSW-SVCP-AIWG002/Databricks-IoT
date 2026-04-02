from flask import Blueprint, redirect, session, current_app

import iot_app.auth.middleware as mw

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')


@auth_bp.route('/logout')
def logout():
    """ログアウト処理: セッションクリア → IdP のログアウトURLへリダイレクト"""
    session.clear()
    return redirect(mw.auth_provider.logout_url())


@auth_bp.route('/login')
def login():
    """ログインリダイレクト（handle_401 から参照される）"""
    auth_type = current_app.config.get('AUTH_TYPE', 'azure')
    if auth_type == 'azure':
        return redirect('/.auth/login/aad?post_login_redirect_uri=/')
    return redirect('/')
