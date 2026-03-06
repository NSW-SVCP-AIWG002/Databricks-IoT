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

    # Blueprint 登録
    from iot_app.views.chat.views import chat_bp
    app.register_blueprint(chat_bp)

    # ヘルスチェックルート（認証除外パス）
    @app.route('/health')
    def health():
        return jsonify(status='ok'), 200

    return app
