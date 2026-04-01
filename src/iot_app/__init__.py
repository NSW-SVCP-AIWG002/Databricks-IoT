import logging as _logging
import os
import sys
import logging
import time
import uuid

from flask import Flask, g, jsonify, request, session
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

_logger = None
_sql_logger = None


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
    global _logger, _sql_logger

    app = Flask(__name__)

    config_name = os.getenv("FLASK_ENV", "development")

    from iot_app.config import config
    app.config.from_object(config.get(config_name, config["default"]))

    db.init_app(app)

    # db.create_all() が全テーブルを認識できるようモデルを明示インポート
    with app.app_context():
        from iot_app.models import customer_dashboard, organization, device, measurement  # noqa: F401

    # ログハンドラー設定
    configure_logging(app, config_name)

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

    # ルートリダイレクト
    @app.route('/')
    def index():
        from flask import redirect
        return redirect('/analysis/industry-dashboard/store-monitoring')

    # 分析機能 Blueprint
    from iot_app.views.analysis import customer_dashboard_bp
    app.register_blueprint(customer_dashboard_bp)

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
