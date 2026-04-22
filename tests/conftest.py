import os
import pytest

os.environ["FLASK_ENV"] = "testing"

from iot_app import create_app, db as _db


@pytest.fixture()
def app():
    """テスト用Flaskアプリケーションを生成（TestingConfig使用）

    テーブルは Docker 初期化（10_test_database.sql）で作成済みのため
    create_all() は不要。
    """
    app = create_app()

    with app.app_context():
        yield app


@pytest.fixture()
def client(app):
    """テスト用HTTPクライアント"""
    return app.test_client()


@pytest.fixture()
def db_session(app):
    """テスト用DBセッション

    app が function スコープのため、各テストは独立した DB を持つ。
    セッションをそのまま yield し、テスト終了後は app の drop_all に委ねる。
    """
    with app.app_context():
        yield _db.session
