import os

from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


def create_app():
    """Flaskアプリケーションファクトリ"""
    app = Flask(__name__)

    config_name = os.getenv("FLASK_ENV", "development")

    from iot_app.config import config
    app.config.from_object(config.get(config_name, config["default"]))

    db.init_app(app)

    # before_request: 認証ミドルウェア
    from iot_app.auth.middleware import set_mock_current_user
    app.before_request(set_mock_current_user)

    # ヘルスチェックルート（認証除外パス）
    @app.route('/health')
    def health():
        return jsonify(status='ok'), 200

    # 業種別ダッシュボード Blueprint
    from views.industry_dashboard.views import dashboard_bp
    app.register_blueprint(dashboard_bp)

    # 開発環境専用 Blueprint
    if config_name == "development":
        from iot_app.views.dev import dev_bp
        app.register_blueprint(dev_bp)

    return app
