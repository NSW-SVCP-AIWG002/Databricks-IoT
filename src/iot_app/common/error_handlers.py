from flask import g, session, redirect, url_for, render_template

from iot_app.common.logger import get_logger

logger = get_logger(__name__)


def handle_500(e):
    """500系例外ハンドラー"""
    logger.error("Internal Server Error", exc_info=True, extra={"error_type": type(e).__name__})
    return render_template("errors/500.html"), 500


def handle_401(e):
    """401ハンドラー: セッションクリア → ログインへリダイレクト"""
    raw_email = getattr(g, "failed_email", None)
    if raw_email:
        logger.warning("認証失敗", extra={"raw_email": raw_email})
    else:
        logger.warning("認証失敗")
    session.clear()
    return redirect(url_for("auth.login"))


def handle_4xx(e):
    """400系例外ハンドラー（401以外）"""
    logger.warning("Client Error", extra={"httpStatus": e.code})
    return '', e.code


def register_error_handlers(app):
    """エラーハンドラーをアプリに登録"""
    app.register_error_handler(Exception, handle_500)
    app.register_error_handler(401, handle_401)
    app.register_error_handler(400, handle_4xx)
    app.register_error_handler(403, handle_4xx)
    app.register_error_handler(404, handle_4xx)
