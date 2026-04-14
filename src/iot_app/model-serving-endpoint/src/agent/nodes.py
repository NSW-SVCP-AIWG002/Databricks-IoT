import json
import traceback
import time
import pandas as pd

from databricks import sql
from langgraph.errors import GraphInterrupt
from langgraph.types import interrupt
from langchain_core.messages import BaseMessage, AIMessage, HumanMessage

from conf.settings import endpoint, TokenContext, GenieConfig, SQLConfig

from conf.prompt import planner_prompt, decide_get_new_data_prompt
from conf.logging_config import log_message
from db.connection import get_db_connection
from src.agent.state import AgentState
from src.utils.llm import post_chat
from src.utils.dataframe import get_df_summary, to_records_json_or_none
from src.utils.common import unique_by_api
from src.apis.request_genie_api import genie_conversation
from src.apis.request_graph_api import create_plot
from src.apis.request_llm_api import generate_llm_response


# ----------------------------
# Planner
# ----------------------------
def planner_node(state: AgentState) -> AgentState:
    try:
        print("--------planning---------")
        prompt = state.get("prompt", "")
        messages = state.get("messages", [])
        conversation_info = state.get("genie_conversation_info", None)
        start_plan = time.time()

        result = post_chat(
            endpoint=endpoint,
            system_prompt=planner_prompt,
            prompt=prompt,
            messages=messages,
            temperature=0.1,
        )
        selected = result.get("selected_apis", [])
        selected_apis = unique_by_api(selected)
        print(f"1つ目のselected_apis:{selected_apis}")

        # まず selected_apis から API名配列を作成
        api_names = [api.get("api") for api in selected_apis if isinstance(api, dict)]

        # space名を決める関数（selected_apis優先 → state/genie_conversation_info → 既定）
        def resolve_space_name() -> str:
            # 1) LLM選択の GenieAPI から space を拾う
            for it in selected_apis:
                if it.get("api") == "GenieAPI" and it.get("space"):
                    return it["space"]
            # 2) 直前の状態から推定（id→nameの逆引き）
            prev_space_id = None
            conv = state.get("genie_conversation_info")
            if isinstance(conv, dict):
                prev_space_id = conv.get("space_id")
            prev_space_id = prev_space_id or state.get("space")
            if prev_space_id:
                for name, cfg in GenieConfig.DATABRICKS_GENIE_SPACES.items():
                    if cfg.get("id") == prev_space_id:
                        return name
            
            return None

        # GraphAPIのみが選ばれている場合は GenieAPI を自動挿入し、space を必ず付ける
        if "GraphAPI" in api_names and "GenieAPI" not in api_names:
            print("GraphAPI detected without GenieAPI. Auto-injecting GenieAPI.")
            space_name = resolve_space_name()

            genie_prompt = None
            if isinstance(conversation_info, dict):
                genie_prompt = conversation_info.get("content")

            if not genie_prompt:
                # データ未取得（または会話情報未保持）。ユーザー向けに専用メッセージへ変換するための明示的エラーを投げる
                raise RuntimeError("NO_DATA_FOR_GRAPH")
            
            genie_task = {
                "api": "GenieAPI",
                "prompt": genie_prompt,
                "space": space_name,
                "reuse": True,
            }
            selected_apis.insert(0, genie_task)

        # LLMが返した GenieAPI に space がない場合も補完する
        space_name_for_fill = resolve_space_name()
        for it in selected_apis:
            if it.get("api") == "GenieAPI" and not it.get("space"):
                it["space"] = space_name_for_fill

        if not selected_apis:
            selected_apis.append({
                "api": "LLM",
                "prompt": prompt
            })

        # space_id を確定（selected_apis 内の GenieAPI の space を優先）
        space_id = None
        genie_items = [it for it in selected_apis if it.get("api") == "GenieAPI"]
        if genie_items:
            space_name = genie_items[0].get("space", "") or space_name_for_fill
            if space_name:
                space_id = GenieConfig.DATABRICKS_GENIE_SPACES[space_name]["id"]

        print(f"プランニング時間: {time.time() - start_plan}秒")
        print(f"2つ目のselected_apis:{selected_apis}")

        # space_id があれば一緒に返す
        if space_id is not None:
            return {"selected_apis": selected_apis, "space": space_id}
        else:
            return {"selected_apis": selected_apis}

    except Exception as e:
        traceback.print_exc()
         # データ未取得の専用メッセージに切り替え
        if isinstance(e, RuntimeError) and str(e) == "NO_DATA_FOR_GRAPH":
            message = "データがみつかりませんでした。お手数ですが、入力内容や条件をご確認いただき、再度データ取得をお試しください。"
        else:
            message = "Agentでエラーが発生しました。お手数ですが、入力内容や条件をご確認いただき、新しいスレッドで再度お試しください"
        return {
            "messages": list(state.get("messages", [])) + [HumanMessage(content=prompt)] + [AIMessage(content=f"{message}:{e}")],
            "Error": True,
        }


# ----------------------------
# Router
# ----------------------------
def routing_node(state: AgentState) -> AgentState:
    try:
        print("------------routing------------------")
        prompt = state.get("prompt", "")
        selected = state.get("selected_apis", [])
        print(f"ルーティング時selected_apis：{selected}")
        api_index = state.get("next_api_index", 0)
        # print(f"state：{state}")

        api_list = [api.get("api") for api in selected if isinstance(api, dict)]

        need_LLM = False
        if "LLM" in api_list:
            api_list = [a for a in api_list if a != "LLM"]
            need_LLM = True

        if api_index >= len(selected):
            return {"next": "final_response", "need_LLM": need_LLM}

        api_item = selected[api_index]
        api_name = api_item.get("api", "")
        api_index += 1
        print(f"APIne-mu：{api_name}")
        # GraphAPIはGenie経由の条件遷移で呼ぶためrouterではスキップ
        if api_name in ("GraphAPI"):
            return {"next": "router", "next_api_index": api_index, "need_LLM": need_LLM}
        return {"next": api_name, "next_api_index": api_index, "need_LLM": need_LLM}
    except Exception:
        traceback.print_exc()
        message = "Routing nodeでエラーが発生しました。お手数ですが、入力内容や条件をご確認いただき、再度お試しください"
        return {
            "messages": list(state.get("messages", [])) + [HumanMessage(content=prompt)] + [AIMessage(content=message)],
            "Error": True,
            "next": "final_response",
        }


# ----------------------------
# GenieAPI
# ----------------------------
def genieapi_node(state: AgentState) -> AgentState:
    """
    Genie連携の実行ノード。選択API群と会話状態に基づきGenieとの対話を進め、応答メッセージ・SQL・データを状態差分として返す。

    動作概要:
        - state から `selected_apis`・`genie_conversation_info`・`prompt`・`messages` を取得する。
        - "GenieAPI" の項目から実行用 `prompt` を抽出し、`genie_conversation(prompt, conversation_info, data_exists)` を呼び出す。
        - 返却された `(message, sql_query, df, conversation_info)` を用いて状態差分を構築する。
        - `df` が空の DataFrame の場合は、取得失敗メッセージを上書きする。
        - 正常時は、前段の `messages` に `message` を1件追加し、`sql_query`、更新済み `genie_conversation_info`、
          および `df` をレコード配列のJSON文字列へ変換した値（なければ None）を返す。
        - 例外時はエラーメッセージと `Error=True` を付与して返す。

    Args:
        state (AgentState): LangGraph互換の状態辞書。
            - "selected_apis": Annotated[List[List[Dict[str, Any]]], ...] を想定。最後のグループを対象にする。
            - "genie_conversation_info": Annotated[List[Any], ...]。Genie側の会話コンテキストを保持し、往復ごとに更新する。
            - "prompt": Annotated[List[str], ...]。最新のユーザー入力。
            - "messages": List[Dict[str, Any]]。LLMゲート時の履歴参照などに用いる。

    Returns:
        AgentState: 反映すべき状態差分。
            - 正常時:
                {
                    "messages": 既存messages + [message:str],
                    "sql_query": [Optional[str]],
                    "genie_conversation_info": [Any],
                    "dataframe": [Optional[str]],  # orient="records" のJSON文字列（なければ None）
                }
            - "GenieAPI" 設定が見つからない場合:
                {"messages": ["GenieAPIの設定が見つかりません"], "Error": [True]}
            - 例外時:
                {"messages": ["GenieAPIのデータ取得で問題が発生しました。..."], "Error": [True]}
    """
    try:
        print("---Genie API ---")
        start_time_genie = time.time()
        prompt = state.get("prompt", "")
        messages = state.get("messages", [])
        selected = state.get("selected_apis", [[]])
        conversation_info = state.get("genie_conversation_info", None)
        need_new_genie_data = state.get("need_new_genie_data", False)
        space_id = state.get("space", None)

        # 実行API一覧
        api_list = [api.get("api") for api in selected if isinstance(api, dict)]
        
        # GenieAPIの選択元に応じてデータ取得方針を決定
        # - reuse=True: GraphAPIのみ選択時にPlannerが自動挿入したケース → 既存データ再利用（新規取得不要）
        # - reuse なし: Plannerが明示的にGenieAPIを選択したケース → 新規データ取得
        genie_items = [it for it in selected if it.get("api") == "GenieAPI"]
        reuse = genie_items[0].get("reuse", False) if genie_items else False
        if reuse:
            need_new_genie_data = False
        else:
            need_new_genie_data = True

        if "LLM" in api_list or "GraphAPI" in api_list:
            genie_items = [it for it in selected if it.get("api") == "GenieAPI"]
            if not genie_items:
                message = "GenieAPIの設定が見つかりません"
                return {
                    "messages": list(state.get("messages", [])) + [HumanMessage(content=prompt)] + [AIMessage(content=message)],
                    "Error": True
                }
            prompt = genie_items[0].get("prompt", "")

        if conversation_info: 
            if conversation_info["space_id"] != space_id:
                conversation_info = None

        # ここにspace_idを引数に追加
        message, sql_query, df, conversation_info, download_url = genie_conversation(prompt, conversation_info, need_new_genie_data, space_id=space_id)

        message += "\n\nGenieAPIから取得したデータを下記に表示しています"
        print(f"GenieAPI実行時間: {time.time() - start_time_genie}秒")

        if isinstance(df, pd.DataFrame) and df.empty:
            message = "GenieAPIのデータが取得できていません。\n\nお手数ですが、入力内容や条件をご確認いただき、再度お試しください。"

        # HITL: GraphAPIが選択されており、データ取得が成功している場合にユーザー確認
        if "GraphAPI" in api_list and isinstance(df, pd.DataFrame) and not df.empty:
            user_response = interrupt({
                "message": "以下のデータを取得しました。グラフを作成しますか？",
                "preview": df.head(10).to_dict(orient="records"),
                "sql_query": sql_query,
                "genie_download_url": download_url,
            })
            if user_response == "いいえ":
                # GraphAPIをselected_apisから除外してRouterへ戻す
                updated_apis = [api for api in selected if api.get("api") != "GraphAPI"]
                df_json = to_records_json_or_none(df)
                df_summary = get_df_summary(df_json)
                return {
                    "messages": list(state.get("messages", [])) + [HumanMessage(content=prompt)] + [AIMessage(content=df_summary)] + [AIMessage(content=message)],
                    "sql_query": sql_query,
                    "genie_conversation_info": conversation_info,
                    "genie_download_url": download_url,
                    "dataframe": df_json,
                    "selected_apis": updated_apis,
                }
            # "はい" の場合はそのまま通常処理へ（check_genie_response が GraphAPI へルーティング）

        df = to_records_json_or_none(df)
        df_summary = get_df_summary(df)

        return {
            "messages": list(state.get("messages", [])) + [HumanMessage(content=prompt)] + [AIMessage(content=df_summary)] + [AIMessage(content=message)],
            "sql_query": sql_query,
            "genie_conversation_info": conversation_info,
            "genie_download_url": download_url,
            "dataframe": df,
        }
    except GraphInterrupt:
        raise
    except Exception:
        traceback.print_exc()
        message = "GenieAPIのデータ取得で問題が発生しました。\n\nお手数ですが、入力内容や条件をご確認いただき、再度お試しください。"
        return {
            "messages": list(state.get("messages", [])) + [HumanMessage(content=prompt)] + [AIMessage(content=message)],
            "Error": True
        }


# ----------------------------
# GraphAPI
# ----------------------------
def graphapi_node(state: AgentState) -> AgentState:
    """
    グラフ生成をしてfigをplotlyオブジェクトとして返すノード。

    動作概要:
        - 先行ノードのエラーがあれば中断する（state["Error"] の末尾が真なら例外）。 
        - `sql_query` を取得し、空であればエラー応答を返す。 
        - Databricks SQL に接続し、`sql_query` を実行して行データとカラムから `pd.DataFrame` を構築する。 
        - `create_plot(prompt, sql_query, df)` で可視化を生成し、図オブジェクトを `to_json()` 可能であればJSON化する。 
        - `dataframe` は `to_records_json_or_none(df)` により orient="records" のJSON文字列へ変換する（空なら None）。 
        - `messages` に描画ロジックからの説明メッセージを追加し、図データや会話状態とともに返す。 

    Args:
        state (AgentState): LangGraph互換の状態辞書。 
            - "Error": Annotated[List[bool], ...]。直前のノードで発生したエラー有無。 
            - "sql_query": Annotated[List[Optional[str]], ...]。実行対象のSQL（末尾が最新）。 
            - "genie_conversation_info": Annotated[List[Any], ...]。Genie側の会話コンテキスト。 
            - "prompt": Annotated[List[str], ...]。可視化の文脈に利用（create_plotへ渡す）。 

    Returns:
        AgentState: 反映すべき状態差分。 
            - 正常時:
                {
                    "fig_data": [Optional[str]],          # plotlyオブジェクトのjsonテキスト（なければ None）
                    "messages": existing + [str],         # 可視化に関する説明メッセージ
                    "dataframe": [Optional[str]],         # orient="records" のJSON（空なら None）
                    "sql_query": [str],                   # 実行に用いたクエリ
                    "genie_conversation_info": [Any],     # 会話状態（透過的に持ち回り）
                } 
            - エラー時:
                {
                    "messages": ["...エラーメッセージ..."],
                    "Error": [True],
                } 
    """
    try:
        print("---Graph API ---")
        prompt = state.get("prompt", "")
        sql_query = state.get("sql_query", "")
        conversation_info = state.get("genie_conversation_info", None)
        download_url = state.get("genie_download_url", None)
        dataframe = state.get("dataframe", None)
        auth_token = TokenContext.get("auth_token")

        if state.get("Error", False):
            raise Exception("Genie APIのデータ取得でエラーが発生しました")

        if not isinstance(sql_query, str) or not sql_query.strip():
            return {
                "messages": ["Genieからデータが取得できていないようです。\n\nお手数ですが、入力内容や条件をご確認いただき、再度お試しください"], 
                "Error": True
                }

        with sql.connect(
            server_hostname=SQLConfig.SQL_SERVER_HOST_NAME,
            http_path=SQLConfig.SQL_HTTP_PATH,
            access_token=auth_token,
        ) as connection:
            with connection.cursor() as cursor:
                cursor.execute(sql_query)
                rows = cursor.fetchall()
                columns = [desc[0] for desc in cursor.description]
                df = pd.DataFrame(rows, columns=columns)

        fig, message = create_plot(prompt, sql_query, df.copy())
        if df.empty:
            message += "\n\n※Genieからデータが取得できていません。入力内容をご確認いただき再度お試しください"

        try:
            fig_json = fig.to_json() if hasattr(fig, "to_json") else None
        except Exception:
            fig_json = None

        return {
            "fig_data": fig_json,
            "messages": list(state.get("messages", [])) + [HumanMessage(content=prompt)] + [AIMessage(content=message)],
            # "dataframe": to_records_json_or_none(df),
            "sql_query": sql_query,
            "genie_conversation_info": conversation_info,
            "genie_download_url": download_url,
        }
    except GraphInterrupt:
        raise
    except Exception:
        traceback.print_exc()
        message = "Genie,GraphAPIでエラーが発生しました。\n\nお手数ですが、入力内容や条件をご確認いただき、再度お試しください"
        return {
            "messages": list(state.get("messages", [])) + [HumanMessage(content=prompt)] + [AIMessage(content=message)],
            "Error": True,
        }


# ----------------------------
# LLM
# ----------------------------
def llm_node(state: AgentState) -> AgentState:
    """
    最終応答生成ノード。収集済みデータ（表データ、PubMed/医中誌結果、SQL、会話状態）とLLM設定を用いて回答を生成・返却する。

    動作概要:
        - `state` から各種アーティファクトを取得する:
          - "selected_apis": LLMノードのプロンプト設定（"LLM" の辞書要素）を探索。
          - "dataframe": 分析用データのJSON文字列（orient="records"、存在しない場合は None）。
          - "sql_query": 直近の生成SQL。
          - "messages": これまでのメッセージ（前段の説明や警告等を含む）。
          - "genie_conversation_info": Genie側の会話状態。
          - "resume": 再実行・追記の判定フラグ。
        - "LLM" の設定が見つからない場合はメッセージに "LLM設定なし" を追加して返す。
        - LLMリクエストの実行条件:
          - `dataframe` が存在しない、または `resume` が True の場合に限り、LLMへ問い合わせを行う。
          - ベースプロンプトは、単純な質問提示または検索結果プレビュー（PubMed/医中誌のJSON）と
            ユーザークエリ、補足メッセージを含むテキストを構築して使用する。
        - LLM応答のテキストを抽出し、`messages` に1件追加して返す。

    Args:
        state (AgentState): LangGraph互換の状態辞書。
            - "selected_apis": Annotated[List[List[Dict[str, Any]]], ...]。最後のグループから "LLM" の設定を探索し、"prompt" を取得。
            - "dataframe": Annotated[List[Optional[str]], ...]。orient="records" のJSON。なければ None。
            - "sql_query": Annotated[List[Optional[str]], ...]。直近のSQL。
            - "messages": Annotated[List[List[str]], ...] や類似の履歴構造を想定。末尾を利用。
            - "genie_conversation_info": Annotated[List[Any], ...]。Genie会話コンテキスト。
            - "resume": Annotated[List[bool], ...]。LLMへの再実行フラグ。

    Returns:
        AgentState: 反映すべき状態差分。
            - 正常時:
                {
                    "messages": existing + [message:str],
                    "dataframe": [Optional[str]],
                    "sql_query": [str],
                    "genie_conversation_info": [Any],
                }
            - "LLM" 設定なし:
                {"messages": existing + ["LLM設定なし"]}
            - 例外時:
                {"messages": ["LLMAPIでエラーが発生しました。..."], "Error": [True]}
    """
    try:
        print("---LLM API ---")
        selected = state.get("selected_apis", [])
        df = state.get("dataframe")
        fig_data = state.get("fig_data")
        sql_query = state.get("sql_query", "")
        message = state.get("messages", [])
        conversation_info = state.get("genie_conversation_info", [])
        download_url = state.get("genie_download_url")
        llm_items = [it for it in selected if it.get("api") == "LLM"]
        prompt = llm_items[0].get("prompt", "")
        if not selected or not selected[-1]:
            error_msg = "LLMAPIでエラーが発生しています。適切なAPIが選択されていません。"
            return {
                "messages": [error_msg],
                "Error": True
            }
        
        api_list = [api.get("api") for api in selected if isinstance(api, dict)]
        
        start_time = time.time()
        message = generate_llm_response(prompt, message, api_list, df, selected)
        end_time = time.time()

        print(f"LLM実行時間{end_time - start_time}")

        return {
            "messages": list(state.get("messages", [])) + [HumanMessage(content=prompt)] + [AIMessage(content=message)],
            "dataframe": to_records_json_or_none(df),
            "sql_query": sql_query,
            "fig_data": fig_data,
            "genie_conversation_info": conversation_info,
            "genie_download_url": download_url,
        }
    except Exception as e:
        traceback.print_exc()
        message = "LLMAPIでエラーが発生しました。\n\nお手数ですが、入力内容や条件をご確認いただき、再度お試しください"
        return {
            "messages": list(state.get("messages", [])) + [HumanMessage(content=prompt)] + [AIMessage(content=f"{message}:{e}")],
            "Error": True,
        }


# ----------------------------
# 分岐関数
# ----------------------------
def check_genie_response(state: AgentState) -> str:
    """
    詳細説明

    Args:
        引数(arg1)の名前 (引数(arg1)の型): 引数(arg1)の説明
        引数(arg2)の名前 (:obj:`引数(arg2)の型`, optional): 引数(arg2)の説明

    Returns:
        戻り値の型: 戻り値の説明
    """
    print("---------------check_genie-----")
    selected = state.get("selected_apis", [[]])

    has_graph = any(item.get("api") == "GraphAPI" for item in selected)
    if has_graph:
        return "GraphAPI"
    return "router"


def final_response(state: AgentState) -> AgentState:
    print("---------------final_response-----")
    return state

# need_LLMを無理やりTrueにすれば強制的にLLMの結果が返される
def decide_llm_or_end(state: AgentState) -> str:
    need = state.get("need_LLM", False)
    return "LLM" if need else "END"