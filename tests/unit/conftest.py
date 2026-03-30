"""
単体テスト共通フィクスチャ
"""
import pytest
from flask import Flask


@pytest.fixture
def app():
    """テスト用 Flask アプリケーション（セッション・コンテキスト操作が必要なテストで使用）"""
    app = Flask(__name__)
    app.config["TESTING"] = True
    app.config["SECRET_KEY"] = "test-secret-key"
    return app
