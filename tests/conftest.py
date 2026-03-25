import os
import pytest

os.environ["FLASK_ENV"] = "testing"

from src import create_app, db as _db


@pytest.fixture()
def app():
    """テスト用Flaskアプリケーションを生成（TestingConfig使用）

    function スコープ: テストごとに新しいインメモリ SQLite DB を作成し、
    テスト終了後に drop_all でクリアする。
    これにより db.session.commit() を呼ぶエンドポイントのテストでも
    テスト間のデータ汚染が発生しない。
    """
    app = create_app()

    with app.app_context():
        _db.create_all()
        yield app
        _db.drop_all()


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
