import os

from flask import Flask
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


def create_app():
    """Flaskアプリケーションファクトリ"""
    app = Flask(__name__)

    config_name = os.getenv("FLASK_ENV", "development")

    from src.config import config
    app.config.from_object(config.get(config_name, config["default"]))

    db.init_app(app)

    # Blueprint登録
    from src.views.industry_dashboard import industry_dashboard_bp
    app.register_blueprint(industry_dashboard_bp)

    return app
