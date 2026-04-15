"""
検索条件Cookie管理共通関数

一覧画面における検索条件の格納・取得・削除を統一的に処理する。
Cookie名規則: search_conditions_{画面名}
"""
import json

from flask import current_app, request


def set_search_conditions_cookie(response, screen_name, conditions):
    """検索条件をCookieに保存する

    Args:
        response: Flaskのレスポンスオブジェクト
        screen_name: 画面名（例: "users", "devices"）
        conditions: 保存する検索条件（辞書型）

    Returns:
        更新されたレスポンスオブジェクト
    """
    cookie_name = f"search_conditions_{screen_name}"
    cookie_value = json.dumps(conditions, ensure_ascii=False)

    # AUTH_TYPE='dev'（ローカル開発環境）では HTTP 通信のため secure=False にする。
    # secure=True のままだと HTTPS 以外でブラウザがCookieを送信せず、検索条件が保持されない。
    # 本番（AUTH_TYPE='azure' 等）は HTTPS 通信なので secure=True を維持する。
    is_secure = current_app.config.get('AUTH_TYPE') != 'dev'

    response.set_cookie(
        cookie_name,
        value=cookie_value,
        max_age=86400,
        httponly=True,
        secure=is_secure,
        samesite='Lax',
    )

    return response


def get_search_conditions_cookie(screen_name):
    """Cookieから検索条件を取得する

    Args:
        screen_name: 画面名（例: "users", "devices"）

    Returns:
        検索条件の辞書（Cookieが存在しない場合は空の辞書）
    """
    cookie_name = f"search_conditions_{screen_name}"
    cookie_value = request.cookies.get(cookie_name)

    if cookie_value:
        try:
            return json.loads(cookie_value)
        except json.JSONDecodeError:
            return {}

    return {}


def clear_search_conditions_cookie(response, screen_name):
    """検索条件のCookieを削除する

    Args:
        response: Flaskのレスポンスオブジェクト
        screen_name: 画面名（例: "users", "devices"）

    Returns:
        更新されたレスポンスオブジェクト
    """
    cookie_name = f"search_conditions_{screen_name}"
    response.delete_cookie(cookie_name)

    return response
