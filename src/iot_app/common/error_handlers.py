from urllib.parse import quote

from flask import g, jsonify, redirect, render_template, request, session, url_for

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


# (title, message, reason)
_4XX_CONTENT = {
    400: ('不正なリクエストです',   'リクエストの内容が正しくありません。',                                                              'Bad Request'),
    403: ('アクセスできません',     'このアプリケーションへのアクセス権限がありません。\nシステム管理者にお問い合わせください。',          'Forbidden'),
    404: ('ページが見つかりません', 'お探しのページは存在しないか、削除された可能性があります。',                                        'Not Found'),
    409: ('競合が発生しました',     '他の操作と競合が発生しました。再度お試しください。',                                               'Conflict'),
}


def handle_4xx(e):
    """400系例外ハンドラー（401以外）

    - AJAX（X-Requested-With: XMLHttpRequest）: JSON返却 → JSがトースト表示
    - アプリ内遷移（referrerあり）: referrerへリダイレクト + ?error= → トースト表示
    - URL直打ち（referrerなし）: 4xx.html エラーページ
    """
    logger.warning("Client Error", extra={"httpStatus": e.code})
    title, message, reason = _4XX_CONTENT.get(e.code, ('エラー', 'エラーが発生しました。', 'Error'))

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({'error': message}), e.code

    referrer = request.referrer
    if referrer:
        sep = '&' if '?' in referrer else '?'
        return redirect(f"{referrer}{sep}error={quote(message, safe='')}")

    return render_template('errors/4xx.html', code=e.code, title=title, message=message, reason=reason), e.code


def register_error_handlers(app):
    """エラーハンドラーをアプリに登録"""
    app.register_error_handler(Exception, handle_500)
    app.register_error_handler(401, handle_401)
    app.register_error_handler(400, handle_4xx)
    app.register_error_handler(403, handle_4xx)
    app.register_error_handler(404, handle_4xx)
    app.register_error_handler(409, handle_4xx)