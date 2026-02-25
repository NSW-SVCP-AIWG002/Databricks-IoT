"""
結合テスト共通フィクスチャ

全結合テストで使用する共通フィクスチャを定義する。
主な役割: before_request フックで flask.g に認証済みユーザーをセットする。
"""

from types import SimpleNamespace

import pytest


@pytest.fixture(autouse=True)
def inject_test_user(app):
    """各テストリクエストで g.current_user をセットする before_request フックを登録する。

    flask.g は LocalProxy であり、パッチでは差し替えできない。
    before_request フックで直接 g に属性をセットすることで、
    ビュー層が参照する g.current_user を正しく設定する。
    """
    from flask import g

    def _set_current_user():
        g.current_user = SimpleNamespace(
            user_id=1,
            user_type_id=1,
            organization_id=1,
            email_address="test@example.com",
        )
        g.current_user_id = 1
        g.databricks_token = ""

    # before_request_funcs の先頭に挿入（ミドルウェアより先に実行）
    app.before_request_funcs.setdefault(None, []).insert(0, _set_current_user)

    yield

    # テスト後にフックを削除してテスト間の干渉を防ぐ
    funcs = app.before_request_funcs.get(None, [])
    if _set_current_user in funcs:
        funcs.remove(_set_current_user)
