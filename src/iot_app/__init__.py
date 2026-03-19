import logging as _logging
import os
import time
import uuid

from flask import Flask, g, jsonify, request
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

_logger = None
_sql_logger = None


def create_app():
    """Flaskアプリケーションファクトリ"""
    global _logger, _sql_logger

    app = Flask(__name__)

    config_name = os.getenv("FLASK_ENV", "development")

    from iot_app.config import config
    app.config.from_object(config.get(config_name, config["default"]))

    db.init_app(app)

    from iot_app.common.logger import get_logger
    _logger = get_logger(__name__)
    _sql_logger = get_logger("iot_app.sql")

    # ── リクエスト前後ログ（6.2）──────────────────────────────────────────

    @app.before_request
    def _before_request():
        g.request_id = str(uuid.uuid4())
        g.request_start_time = time.monotonic()
        _logger.info("リクエスト開始")

    @app.after_request
    def _after_request(response):
        duration_ms = int((time.monotonic() - getattr(g, "request_start_time", time.monotonic())) * 1000)
        _logger.info(
            "リクエスト完了",
            extra={"httpStatus": response.status_code, "processingTime": duration_ms},
        )
        if response.status_code >= 500:
            error_type = getattr(g, "last_exception_type", "Unknown")
            _logger.error("Internal Server Error", extra={"error_type": error_type})
        elif response.status_code >= 400:
            _logger.warning("Client Error", extra={"httpStatus": response.status_code})
        return response

    # ── SQLAlchemy イベントリスナー（6.5）────────────────────────────────

    with app.app_context():
        from sqlalchemy import event as _sa_event

        @_sa_event.listens_for(db.engine, "before_cursor_execute")
        def _before_sql(conn, cursor, statement, parameters, context, executemany):
            conn.info.setdefault("query_start_time", []).append(time.monotonic())

        @_sa_event.listens_for(db.engine, "after_cursor_execute")
        def _after_sql(conn, cursor, statement, parameters, context, executemany):
            duration_ms = int((time.monotonic() - conn.info["query_start_time"].pop(-1)) * 1000)
            stmt = statement.strip()
            level = _logging.DEBUG if stmt.upper().startswith("SELECT") else _logging.INFO
            _sql_logger.log(level, "SQL実行", extra={"query": stmt, "duration_ms": duration_ms})

    # ヘルスチェックルート（認証除外パス）
    @app.route('/health')
    def health():
        return jsonify(status='ok'), 200

    # 分析機能 Blueprint
    from iot_app.views.analysis import customer_dashboard_bp
    app.register_blueprint(customer_dashboard_bp)

    # 開発環境専用 Blueprint
    if config_name == "development":
        from iot_app.views.dev import dev_bp
        app.register_blueprint(dev_bp)

    return app
