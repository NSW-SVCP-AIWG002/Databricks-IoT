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

    # 認証プロバイダーの初期化
    auth_type = app.config.get('AUTH_TYPE')
    if auth_type:
        with app.app_context():
            from iot_app.auth.factory import get_auth_provider
            import iot_app.auth.middleware as mw
            mw.auth_provider = get_auth_provider()

    # before_request フック（認証）の登録
    from iot_app.auth.middleware import authenticate_request
    app.before_request(authenticate_request)

    # エラーハンドラーの登録
    from iot_app.common.error_handlers import register_error_handlers
    register_error_handlers(app)

    # Blueprint の登録
    from iot_app.auth.routes import auth_bp
    app.register_blueprint(auth_bp)

    # ヘルスチェックルート（認証除外パス）
    @app.route('/health')
    def health():
        return jsonify(status='ok'), 200

    @app.route('/ping')
    def ping():
        return 'pong', 200

    return app
