import streamlit as st
import requests
import uuid
import json
import ast
import re
import traceback
import base64
import pandas as pd
import plotly.graph_objects as go
import plotly.io as pio
from pathlib import Path
from logging import getLogger
from requests.exceptions import Timeout, ReadTimeout, ConnectTimeout
import time
from concurrent.futures import ThreadPoolExecutor

from conf.logging_config import log_message
from conf.streamlit_settings import AgentAPI, ServicePrincipalConfig


logger = getLogger(__name__)

# ===========================
#  Streamlit 初期化
# ===========================
if "messages" not in st.session_state:
    st.session_state["messages"] = []
if "thread_id" not in st.session_state:
    st.session_state["thread_id"] = str(uuid.uuid4())
if "resume_state" not in st.session_state:
    st.session_state["resume_state"] = None
if "conversation_info" not in st.session_state:
    st.session_state["conversation_info"] = None

# ===========================
#  Databricks OAuth トークン取得（サービスプリンシパル）
# ===========================
def get_service_principal_token():
    ws_url = ServicePrincipalConfig.WORKSPACE_URL
    client_id = ServicePrincipalConfig.DATABRICKS_CLIENT_ID
    client_secret = ServicePrincipalConfig.DATABRICKS_CLIENT_SECRET
    token_endpoint = f"{ws_url}/oidc/v1/token"
    token_resp = requests.post(
        token_endpoint,
        auth=(client_id, client_secret),
        data={"grant_type": "client_credentials", "scope": "all-apis"},
        timeout=10,
    )
    token_resp.raise_for_status()
    return token_resp.json()["access_token"]

# ===========================
#  Databricks Agent 呼び出し（バックグラウンド関数）
# ===========================
def _post_to_databricks_agent(access_token, prompt, resume_state, conversation_info, thread_id):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}",
    }
    payload = {
        "dataframe_records": [
            {
                "prompt": prompt,
                "access_token": access_token,  # バックエンドが必要としているため同梱
                "thread_id": thread_id,
            }
        ]
    }

    log_message(f"payload: {payload}")

    response = requests.post(AgentAPI.endpoint, headers=headers, json=payload, timeout=600)
    log_message(f"ステータスコード: {response.status_code}")

    if response.status_code != 200:
        log_message(f"APIエラー: {response.status_code} - {response.text}")
    response.raise_for_status()

    return response.json()

def _parse_predictions(data):
    predictions = data.get("predictions", {}) if isinstance(data, dict) else {}
    log_message(f"predictions: {predictions}")

    message = predictions.get("message", "")
    df = None
    fig = None
    sql_query = predictions.get("sql_query")

    # DataFrame
    df_raw = predictions.get("df")
    if df_raw:
        try:
            df_json = json.loads(df_raw)
            df = pd.DataFrame(df_json)
        except Exception as e:
            logger.exception(f"df のパースでエラー: {e}")

    # Figure
    fig_data = predictions.get("fig_data")
    if fig_data:
        try:
            fig = pio.from_json(fig_data)
        except Exception as e:
            logger.exception(f"fig_data のパースでエラー: {e}")

    resume_state = predictions.get("resume_state")
    conversation_info = predictions.get("conversation_info")

    return message, df, sql_query, fig, resume_state, conversation_info

# ===========================
#  Databricks Agent 呼び出し（進捗付き）
# ===========================
def call_databricks_agent(prompt):
    try:
        start = time.time()
        with st.status("処理を開始します…", expanded=True, state="running") as status:
            status.write("1/4 認証トークンを取得中")
            access_token = get_service_principal_token()

            status.write("2/4 APIへリクエスト送信中")
            prog = st.progress(0, text="Databricksからの応答を待機中…")
            pct = 0
            result = None
            error = None

            with ThreadPoolExecutor(max_workers=1) as ex:
                future = ex.submit(
                    _post_to_databricks_agent,
                    access_token,
                    prompt,
                    st.session_state["resume_state"],
                    st.session_state["conversation_info"],
                    st.session_state["thread_id"],
                )
                # 完了まで疑似プログレスを更新
                while not future.done():
                    pct = (pct + 3) % 100
                    prog.progress(pct, text="Databricksからの応答を待機中…")
                    time.sleep(0.1)

                try:
                    result = future.result()
                    prog.progress(100, text="レスポンスを受信しました")
                except Exception as e:
                    error = e

            if error:
                if isinstance(error, (Timeout, ReadTimeout, ConnectTimeout)):
                    status.update(label="タイムアウトしました", state="complete")
                    logger.warning(f"タイムアウト: {error}")
                    return "5分以内に回答が返ってきませんでした。再度お試しください。", None, None, None
                status.update(label="エラーが発生しました", state="error")
                st.error(f"APIエラー: {error}")
                logger.exception(error)
                return "エラーが発生しました。再度チャットを開始してください。", None, None, None

            status.write("3/4 レスポンス解析中")
            message, df, sql_query, fig, resume_state, conversation_info = _parse_predictions(result)

            # 状態更新
            st.session_state["resume_state"] = resume_state
            st.session_state["conversation_info"] = conversation_info

            elapsed = time.time() - start
            status.write(f"4/4 完了（{elapsed:.1f}秒）")
            status.update(label="完了しました", state="complete")

            return message, df, sql_query, fig

    except Exception as e:
        st.error(f"APIエラー: {e}")
        traceback.print_exc()
        return "エラーが発生しました。再度チャットを開始してください。", None, None, None

# =========================================================
# Custom CSS（ChatGPT風デザイン）
# =========================================================
def load_css():
    st.markdown("""
        <style>
        /* 基本レイアウト */
        .main {
            padding: 0rem 3rem;
        }
        /* チャットメッセージ共通 */
        .chat-bubble {
            padding: 1rem 1.4rem;
            margin: 1rem 0;
            border-radius: 18px;
            width: fit-content;
            max-width: 85%;
            line-height: 1.6;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }
        /* ユーザーの吹き出し */
        .user-bubble {
            margin-left: auto;
            background: linear-gradient(135deg, #4A90E2, #357ABD);
            color: white;
        }
        /* アシスタントの吹き出し */
        .assistant-bubble {
            background: #ffffff;
            border: 1px solid #E5E7EB;
        }
        /* サイドバーの新規チャットボタン */
        .sidebar-button > button {
            width: 100%;
            border-radius: 12px !important;
            padding: 0.7rem !important;
            background: #10A37F !important;
            color: white !important;
            font-weight: bold !important;
            border: none !important;
        }
        /* 過去チャットのリスト */
        .history-item {
            padding: 0.7rem 1rem;
            border-radius: 12px;
            background: #F3F4F6;
            margin-bottom: 0.5rem;
            cursor: pointer;
        }
        .history-item:hover {
            background: #E5E7EB;
        }
        /* ローディングアニメーション */
        .dots {
            display: inline-block;
            font-size: 18px;
        }
        .dots::after {
            content: " ...";
            animation: dots 1.2s steps(4, end) infinite;
        }
        @keyframes dots {
            0%, 20% { content: "   "; }
            40% { content: ".  "; }
            60% { content: ".. "; }
            80%, 100% { content: "..."; }
        }
        /* 固定ヘッダー */
        .fixed-header {
            position: fixed;
            top: 0; left: 0; right: 0;
            z-index: 999;
            background: #ffffff;
            border-bottom: 1px solid #E5E7EB;
            padding: 12px 24px;
        }
        .fixed-header .title {
            font-size: 1.25rem;
            font-weight: 700;
            display: inline-block;
        }
        .fixed-header .actions {
            float: right;
        }
        .fixed-header .btn {
            display: inline-block;
            padding: 8px 12px;
            border-radius: 8px;
            background: #10A37F;
            color: #fff;
            text-decoration: none;
            font-weight: 600;
        }
        
        /* 画面中央のヒーロー文言 */
        .hero {
            min-height: 50vh;            
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.6rem;
            color: #6b7280;
            text-align: center;
        }
        </style>
    """, unsafe_allow_html=True)

# ===========================
#  Streamlit UI
# ===========================
# Wideモードをデフォルトに
st.set_page_config(layout="wide")

# ===== ヘッダー =====
# col1, _ = st.columns([6, 2])

@st.cache_data(show_spinner=False)
def img_to_base64(path_str: str) -> str:
    with open(path_str, "rb") as f:
        return base64.b64encode(f.read()).decode()

# streamlit_app.py と同じ階層にある image/logo.png を指す
BASE_DIR = Path(__file__).parent if "__file__" in globals() else Path.cwd()
LOGO_FILE = "<your image path>.png"
LOGO_PATH = BASE_DIR / "image" / LOGO_FILE

logo_b64 = img_to_base64(str(LOGO_PATH))

# ✅ col1 の中で横並びレイアウトを作る
# title_col, button_col = col1.columns([5, 0.5], vertical_alignment="center")
title_col, spacer_col, button_col = st.columns([9, 1, 2], vertical_alignment="center")

# ---- タイトル側 ----
title_col.markdown(f"""
<div style="display:flex; align-items:center; gap:10px;">
    <img src="data:image/png;base64,{logo_b64}" style="height:28px;" />
    <span style="font-size:1.5rem; font-weight:700;">Genie Agent</span>
</div>
""", unsafe_allow_html=True)

# ---- ボタン側 ----
with button_col:
    # st.markdown('<div class="header-btn">', unsafe_allow_html=True)
    if st.button("🆕 新規チャット", key="header_new_chat", type="primary", use_container_width=False):
        st.session_state["messages"] = []
        st.session_state["thread_id"] = str(uuid.uuid4())
        st.session_state["resume_state"] = None
        st.session_state["conversation_info"] = None
        st.rerun()

st.markdown("""
<style>
/* 既存の固定ヘッダー設定はそのまま */
div[data-testid="stHorizontalBlock"]:first-of-type {
    position: fixed !important;
    top: 0 !important;
    left: 0 !important;
    right: 0 !important;
    z-index: 9999 !important;
    background: #ffffff !important;
    border-bottom: 1px solid #E5E7EB !important;
    box-shadow: 0 2px 8px rgba(0,0,0,0.1) !important;
    padding: 12px 24px !important;
}
/* 公式ヘッダー非表示 + コンテンツ余白 */
[data-testid="stHeader"] { display: none !important; }
.block-container { padding-top: 80px !important; } /* ヘッダーの高さに合わせて調整 */

 /* タイトルは縮ませない・折り返さない */
.header-title {
  display: flex;
  align-items: center;
  gap: 10px;
  white-space: nowrap;
  flex: 0 0 auto;            /* shrinkしない */
  min-width: max-content;    /* 内容幅を維持 */
}
.header-logo {
  height: 28px;
  flex-shrink: 0;
}
.header-text {
  font-size: 1.5rem;
  font-weight: 700;
  white-space: nowrap;
  flex-shrink: 0;
}

/* ボタンコンテナは右端に寄せる */
.header-btn {
  display: flex;
  justify-content: flex-end;
}

/* ボタンは折り返し禁止 + 最小幅を維持（レスポンシブに可変） */
.header-btn .stButton > button {
  white-space: nowrap;
  width: auto;
  min-width: clamp(120px, 12vw, 170px);
  padding: 0.45rem 0.9rem;
}

/* どうしても狭い場合は横スクロール許可（任意） */
.stApp {
  overflow-x: auto;
}

/* ヘッダー行の「最後のカラムにあるボタンラッパー」を右寄せ */
div[data-testid="stHorizontalBlock"]:first-of-type [data-testid="column"]:last-child div.stButton {
  display: flex;
  justify-content: flex-end;  /* 右端へ */
  width: 100%;
}

/* 最後のカラムの右パディングをゼロにして、より端まで寄せる（端ぴったりにしたい場合） */
div[data-testid="stHorizontalBlock"]:first-of-type [data-testid="column"]:last-child {
  padding-right: 0 !important;
  margin-right: 0 !important;
}

/* ボタンの折り返し防止＆最小幅維持（.header-btnに入らない場合でも適用されるように） */
div[data-testid="stHorizontalBlock"]:first-of-type [data-testid="column"]:last-child .stButton > button {
  white-space: nowrap;
  width: auto;
  min-width: clamp(120px, 12vw, 170px);
  padding: 0.45rem 0.9rem;
}

/* （任意）ヘッダー内のカラム間ギャップをゼロにする */
div[data-testid="stHorizontalBlock"]:first-of-type .stColumns {
  gap: 0 !important;
}
</style>
""", unsafe_allow_html=True)

load_css()

# 画面中央のヒーロー文言（履歴が空のときだけ表示）
hero_ph = st.empty()
if len(st.session_state["messages"]) == 0:
    hero_ph.markdown('<div class="hero">何を知りたいですか？</div>', unsafe_allow_html=True)

# アシスタントの応答（本文、SQL、データフレーム、グラフ）を「どの場面でも同じ見た目」で描画する共通関数
def render_assistant_reply(message, df=None, sql_query=None, fig=None):
    # 本文の吹き出し
    if message:
        st.markdown(
            f'<div class="chat-bubble assistant-bubble">{message}</div>',
            unsafe_allow_html=True
        )
    # データフレーム出力（見出し → SQL expander → df の順）
    if df is not None:
        st.subheader("📋 データフレーム出力")
        if sql_query and sql_query.strip():
            with st.expander("💻 SQL出力"):
                st.code(sql_query, language="sql")
        st.dataframe(df, use_container_width=True)
    else:
        if sql_query and sql_query.strip():
            with st.expander("💻 SQL出力"):
                st.code(sql_query, language="sql")
    # グラフ出力
    if fig is not None:
        st.subheader("📈 グラフ出力")
        st.plotly_chart(fig, use_container_width=True)

# チャット履歴表示（ユーザーとアシスタントで統一レイアウト）
for i, msg in enumerate(st.session_state["messages"]):
    if msg["role"] == "user":
        st.markdown(
            f'<div class="chat-bubble user-bubble">{msg["content"]}</div>',
            unsafe_allow_html=True
        )
    else:
        render_assistant_reply(
            message=msg.get("content"),
            df=msg.get("dataframe"),
            sql_query=msg.get("sql_query"),
            fig=msg.get("fig"),
        )

# ユーザー入力に対する反応
if prompt := st.chat_input("メッセージを入力してください…"):
    # ヒーロー文言を消す
    hero_ph.empty()

    # 1) 画面にユーザー投稿を表示＆履歴に追加
    st.session_state["messages"].append({"role": "user", "content": prompt})
    st.markdown(
        f'<div class="chat-bubble user-bubble">{prompt}</div>',
        unsafe_allow_html=True
    )

    # 2) アシスタント応答取得（進捗バー付き）
    message, df, sql_query, fig = call_databricks_agent(prompt)

    # 3) 取得した応答を表示（履歴と同じレイアウトで）
    render_assistant_reply(
        message=message,
        df=df,
        sql_query=sql_query,
        fig=fig,
    )

    # 4) 履歴に保存
    st.session_state["messages"].append(
        {
            "role": "assistant",
            "content": message,
            "dataframe": df,
            "sql_query": sql_query,
            "fig": fig,
        }
    )