import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask, render_template, flash, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from config import Config

app = Flask(__name__)
app.config.from_object(Config)

db = SQLAlchemy(app)


class Device(db.Model):
    """Device model."""
    __tablename__ = "devices"

    id = db.Column(db.Integer, primary_key=True)
    device_name = db.Column(db.String(255), nullable=False)
    device_type = db.Column(db.String(100))
    status = db.Column(db.String(50), default="active")
    created_at = db.Column(db.DateTime, server_default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, server_default=db.func.current_timestamp(),
                           onupdate=db.func.current_timestamp())


# エラーハンドラー
@app.errorhandler(404)
def not_found_error(error):
    """404エラーハンドラー"""
    return render_template('errors/404.html'), 404


@app.route("/")
def index():
    """ホーム画面"""
    return render_template('index.html', message="Hello, Databricks-IoT!")


@app.route("/health")
def health():
    """ヘルスチェック画面"""
    return render_template('health.html', status="healthy")


@app.route("/devices")
def devices_list():
    """デバイス一覧画面"""
    try:
        devices = Device.query.all()
        return render_template('devices/list.html', devices=devices)
    except Exception as e:
        flash('データの取得に失敗しました', 'error')
        return render_template('devices/list.html', devices=[]), 500


@app.route("/devices/<int:device_id>")
def device_detail(device_id):
    """デバイス詳細画面"""
    device = Device.query.get(device_id)
    if not device:
        flash('指定されたデバイスが見つかりません', 'error')
        return render_template('errors/404.html'), 404
    return render_template('devices/detail.html', device=device)


if __name__ == "__main__":
    app.run(host=Config.FLASK_HOST, port=Config.FLASK_PORT, debug=True)
