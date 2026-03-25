import logging as _logging
import os
import time as _time
import uuid as _uuid

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

    # db.create_all() が全テーブルを認識できるようモデルを明示インポート
    with app.app_context():
        from iot_app.models import customer_dashboard, organization, device, measurement  # noqa: F401

    # ────────────────────────────────────────────────
    # リクエストロギング
    # ────────────────────────────────────────────────
    from iot_app.common.logger import get_logger as _get_logger
    _app_logger = _get_logger('iot_app.request')

    @app.before_request
    def _log_request_start():
        from flask import g, request
        g.request_id = str(_uuid.uuid4())
        g._request_start_time = _time.time()
        _app_logger.info('リクエスト開始', extra={
            'requestId': g.request_id,
            'endpoint': request.endpoint or request.path,
            'method': request.method,
        })

    @app.after_request
    def _log_request_end(response):
        from flask import g, request
        elapsed_ms = int((_time.time() - getattr(g, '_request_start_time', _time.time())) * 1000)
        log_extra = {
            'httpStatus': response.status_code,
            'processingTime': elapsed_ms,
            'endpoint': request.endpoint or request.path,
            'method': request.method,
        }
        if response.status_code >= 500:
            _app_logger.error('リクエスト完了', extra=log_extra)
        elif response.status_code >= 400:
            _app_logger.warning('リクエスト完了', extra=log_extra)
        else:
            _app_logger.info('リクエスト完了', extra=log_extra)
        return response

    # ────────────────────────────────────────────────
    # SQLAlchemy SQL ロギング
    # ────────────────────────────────────────────────
    _sql_logger = _logging.getLogger('iot_app.sql')

    with app.app_context():
        from sqlalchemy import event as _sa_event

        @_sa_event.listens_for(db.engine, "before_cursor_execute")
        def _before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            conn.info.setdefault('query_start_time', []).append(_time.time())

        @_sa_event.listens_for(db.engine, "after_cursor_execute")
        def _after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            elapsed_ms = int((_time.time() - conn.info['query_start_time'].pop(-1)) * 1000)
            stmt_upper = statement.strip().upper()
            level = _logging.DEBUG if stmt_upper.startswith('SELECT') else _logging.INFO
            _sql_logger.log(level, 'SQL実行', extra={
                'query': statement[:200],
                'durationMs': elapsed_ms,
            })

    # ヘルスチェックルート（認証除外パス）
    @app.route('/health')
    def health():
        return jsonify(status='ok'), 200

    # Analysis Blueprint
    from iot_app.views.analysis.customer_dashboard import customer_dashboard_bp
    from iot_app.views.analysis.customer_dashboard import common   # noqa: F401
    from iot_app.views.analysis.customer_dashboard import timeline  # noqa: F401
    app.register_blueprint(customer_dashboard_bp)

    # 開発環境専用 Blueprint
    if config_name == "development":
        from iot_app.views.dev import dev_bp
        app.register_blueprint(dev_bp)

    return app
