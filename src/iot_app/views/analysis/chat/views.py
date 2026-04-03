import re
import time
import uuid

import requests
from flask import Blueprint, g, jsonify, render_template, request, session
from markupsafe import escape

# from iot_app.common.logger import get_logger
from iot_app.config import config as app_config

chat_bp = Blueprint('chat', __name__)

_config = app_config.get('default')
# logger = get_logger(__name__)


def _get_config():
    """現在のFlaskアプリ設定を返す（テスト時に差し替え可能）"""
    import os
    env = os.getenv("FLASK_ENV", "development")
    return app_config.get(env, app_config["default"])


def sanitize_question(question: str) -> str:
    """質問テキストをサニタイズする。

    処理内容:
        1. HTML エスケープ（markupsafe.escape）
        2. 制御文字除去（\\x00-\\x1f, \\x7f-\\x9f）
        3. 前後の空白を strip()
    """
    question = str(escape(question))
    question = re.sub(r"[\x00-\x1f\x7f-\x9f]", "", question)
    return question.strip()


def call_orchestrator_endpoint(
    question: str,
    thread_id: str,
    user_token: str
) -> dict:
    """AIオーケストレータAPIを呼び出す（ユーザートークンで実行）。

    Args:
        question: ユーザーの質問テキスト
        thread_id: 会話スレッドID（LangGraph Checkpointerのキー）
        user_token: ユーザーのDatabricksトークン

    Returns:
        status, message, df, fig_data, sql_query を含む辞書
    """
    cfg = _get_config()
    endpoint_url = (
        f"https://{cfg.DATABRICKS_HOST}"
        f"/serving-endpoints/{cfg.DATABRICKS_SERVING_ENDPOINT_NAME}/invocations"
    )

    # logger.info("外部API呼び出し開始", extra={
    #     "service": "ai_orchestrator",
    #     "operation": "AIチャット質問送信",
    # })
    _start = time.time()

    response = requests.post(
        endpoint_url,
        headers={
            "Authorization": f"Bearer {user_token}",
            "Content-Type": "application/json",
        },
        json={
            "dataframe_records": [{
                "prompt": question,
                "access_token": user_token,
                "thread_id": thread_id,
            }]
        },
        timeout=60,
    )
    response.raise_for_status()
    result = response.json()

    # logger.info("外部API完了", extra={
    #     "service": "ai_orchestrator",
    #     "operation": "AIチャット質問送信",
    #     "duration_ms": int((time.time() - _start) * 1000),
    # })

    prediction = result.get("predictions", result)

    return {
        "status": prediction.get("status"),
        "message": prediction.get("message"),
        "df": prediction.get("df"),
        "fig_data": prediction.get("fig_data"),
        "sql_query": prediction.get("sql_query"),
    }


@chat_bp.route('/analysis/chat', methods=['GET'])
def show_chat():
    """チャット画面を表示（CHT-001）。

    認証チェック・トークン取得は AuthMiddleware（before_request）で実行済み。
    会話履歴の復元はフロントエンド（SessionStorage）で行う。
    """
    return render_template('chat/index.html',
                           user_email=session.get('email', ''))


@chat_bp.route('/api/analysis/chat', methods=['POST'])
def send_question():
    """質問を送信してAIオーケストレータから回答を取得。

    認証チェック・トークン取得は AuthMiddleware（before_request）で実行済み。
    g.databricks_token が利用可能。
    """
    data = request.get_json(silent=True) or {}

    raw_question = data.get('question', '')
    thread_id = data.get('thread_id', '').strip()

    question = sanitize_question(raw_question)

    # バリデーション: 質問テキスト
    if not question:
        return jsonify({
            "success": False,
            "error_code": "VALIDATION_ERROR",
            "error_message": "質問を入力してください",
        }), 400

    if len(question) > 1000:
        return jsonify({
            "success": False,
            "error_code": "VALIDATION_ERROR",
            "error_message": "質問は1000文字以内で入力してください",
        }), 400

    # バリデーション: thread_id
    if not thread_id:
        return jsonify({
            "success": False,
            "error_code": "VALIDATION_ERROR",
            "error_message": "thread_idが指定されていません",
        }), 400

    try:
        uuid.UUID(thread_id)
    except ValueError:
        return jsonify({
            "success": False,
            "error_code": "VALIDATION_ERROR",
            "error_message": "無効なthread_idが指定されました",
        }), 400

    user_token = getattr(g, 'databricks_token', None)

    try:
        result = call_orchestrator_endpoint(
            question=question,
            thread_id=thread_id,
            user_token=user_token,
        )
        return jsonify({
            "success": True,
            "thread_id": thread_id,
            **result,
        })

    except requests.exceptions.Timeout:
        # logger.error("外部APIタイムアウト", exc_info=True, extra={
        #     "service": "ai_orchestrator",
        #     "error_type": "Timeout",
        # })
        return jsonify({
            "success": False,
            "error_code": "GENIE_TIMEOUT",
            "error_message": "回答の取得がタイムアウトしました。しばらく経ってから再度お試しください。",
        }), 500

    except requests.exceptions.ConnectionError:
        # logger.error("外部API接続エラー", exc_info=True, extra={
        #     "service": "ai_orchestrator",
        #     "error_type": "ConnectionError",
        # })
        return jsonify({
            "success": False,
            "error_code": "NETWORK_ERROR",
            "error_message": "接続エラーが発生しました。しばらく経ってから再度お試しください。",
        }), 500

    except Exception as e:
        import traceback
        traceback.print_exc()
        # logger.error("外部API例外", exc_info=True, extra={
        #     "service": "ai_orchestrator",
        #     "error_type": type(e).__name__,
        # })
        return jsonify({
            "success": False,
            "error_code": "ORCHESTRATOR_ERROR",
            "error_message": "回答の生成に失敗しました。しばらく経ってから再度お試しください。",
        }), 500
