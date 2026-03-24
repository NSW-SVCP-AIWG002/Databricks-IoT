import os
import sys
import logging

from flask import Flask, jsonify, g, session
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


def configure_logging(app, env):
    """ログハンドラーを設定する（ログ設計書 3章）

    全環境: stdout に JSON 出力
    development のみ: logs/app.log にテキスト出力を追加
    """
    from pythonjsonlogger.json import JsonFormatter

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)

    # 全環境: stdout に JSON 出力
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(JsonFormatter())
    root_logger.addHandler(stream_handler)

    # development のみ: logs/app.log にテキスト出力
    if env == "development":
        os.makedirs("logs", exist_ok=True)
        file_handler = logging.FileHandler("logs/app.log")
        file_handler.setFormatter(
            logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
        )
        root_logger.addHandler(file_handler)


def create_app():
    """Flaskアプリケーションファクトリ"""
    app = Flask(__name__)

    config_name = os.getenv("FLASK_ENV", "development")

    from iot_app.config import config
    app.config.from_object(config.get(config_name, config["default"]))

    db.init_app(app)

    # ログハンドラー設定
    configure_logging(app, config_name)

    # auth_provider を初期化（get_auth_provider は current_app を参照するため app context 内で実行）
    import iot_app.auth.middleware as mw
    from iot_app.auth.factory import get_auth_provider
    with app.app_context():
        mw.auth_provider = get_auth_provider()

    # 認証ミドルウェアを before_request に登録
    from iot_app.auth.middleware import authenticate_request
    app.before_request(authenticate_request)

    # auth Blueprint 登録（/auth/login, /auth/logout）
    from iot_app.auth.routes import auth_bp
    app.register_blueprint(auth_bp)

    # エラーハンドラー登録
    from iot_app.common.error_handlers import register_error_handlers
    register_error_handlers(app)

    # ヘルスチェックルート（認証除外パス）
    @app.route('/health')
    def health():
        return jsonify(status='ok'), 200
    
    # 開発環境専用 Blueprint
    if config_name == "development":
        from iot_app.views.dev import dev_bp
        app.register_blueprint(dev_bp)

    # 認証動作確認用エンドポイント（開発用）
    @app.route('/ping')
    def ping():
        user = getattr(g, "current_user", None)

        return jsonify(
            status='ok',
            auth=dict(
                email=session.get('email'),
                user_id=getattr(user, "user_id", None),
                user_type_id=getattr(user, "user_type_id", None),
            ),
            databricks_token='present' if getattr(user, 'databricks_token', None) else 'missing',
        ), 200

    return app
