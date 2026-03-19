import os
import pytest

os.environ["FLASK_ENV"] = "testing"

from src import create_app, db as _db


@pytest.fixture(scope="session")
def app():
    """テスト用Flaskアプリケーションを生成（TestingConfig使用）"""
    app = create_app()

    with app.app_context():
        # 遅延インポートのモデルを create_all() 前に明示的にインポート
        import iot_app.models.dashboard  # noqa: F401
        import iot_app.models.measurement  # noqa: F401
        import iot_app.models.organization  # noqa: F401
        import iot_app.models.device  # noqa: F401
        _db.create_all()
        yield app
        _db.drop_all()


@pytest.fixture()
def client(app):
    """テスト用HTTPクライアント"""
    return app.test_client()


@pytest.fixture()
def db_session(app):
    """テスト用DBセッション（各テスト後にロールバック）"""
    with app.app_context():
        _db.session.begin_nested()
        yield _db.session
        _db.session.rollback()
