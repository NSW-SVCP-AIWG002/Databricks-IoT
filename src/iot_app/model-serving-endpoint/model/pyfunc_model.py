import pandas as pd
import requests
import time

from mlflow.pyfunc import PythonModel
from langgraph.types import Command

from conf.settings import TokenContext, SQLConfig
from conf.logging_config import log_message



def validate_databricks_token(host: str, token: str):
    """Databricksトークンの有効性を検証"""
    base_url = host if host.startswith("https://") else f"https://{host}"
    url = f"{base_url}/api/2.0/preview/scim/v2/Me"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    try:
        response = requests.get(url, headers=headers, timeout=5)
        
        if response.status_code == 401:
            raise ValueError("アクセストークンが無効です (401 Unauthorized)")
        elif response.status_code == 403:
            raise ValueError("アクセストークンに権限がありません (403 Forbidden)")
        elif response.status_code != 200:
            raise ValueError(f"トークン検証に失敗しました: Status {response.status_code}")
            
    except requests.exceptions.Timeout:
        raise TimeoutError("トークン検証中にタイムアウトしました")
    except requests.exceptions.RequestException as e:
        raise ConnectionError(f"トークン検証リクエストに失敗しました: {e}")


class LangGraphServingModel(PythonModel):
    """LangGraphエージェントのMLflow Servingラッパー"""

    def load_context(self, context):
        from src.agent.builder import build_agent
        self._build_agent = build_agent
        self._agent = None

    def _ensure_agent(self):
        if self._agent is None:
            self._agent = self._build_agent()

    def predict(self, context, model_input):
        payload = self._normalize_input(model_input)
        self._ensure_agent()

        prompt = payload.get("prompt")
        token = payload.get("access_token")
        thread_id = payload.get("thread_id")

        # log_message(f"payload: {payload}")
        # log_message(f"thread_id: {thread_id}")

        # トークン検証
        start_validate_token = time.time()
        if not self._validate_token(token):
            return self._error_response("有効なアクセストークンが設定されていません")
        end_validate_token = time.time()
        # log_message(f"Token validation took {end_validate_token - start_validate_token} seconds")

        config = {
            "configurable": {
                "thread_id": thread_id,
                "access_token": token
            }
        }

        # 状態に応じてstateを構築
        start_build_state = time.time()
        state = self._build_state(config, prompt)
        end_build_state = time.time()
        # log_message(f"State build took {end_build_state - start_build_state} seconds")

        # エージェント実行
        start_time = time.time()
        last_chunk, interrupted_payload = self._run_agent(state, config)
        end_time = time.time()
        # log_message(f"Agent execution took {end_time - start_time} seconds")
        
        # 結果を処理して返却
        return self._build_response(
            last_chunk=last_chunk,
            interrupted_payload=interrupted_payload,
            prompt=prompt,
            thread_id=thread_id,
            token=token
        )

    def _normalize_input(self, model_input) -> dict:
        """入力を辞書形式に正規化"""
        if isinstance(model_input, pd.DataFrame):
            return model_input.to_dict(orient="records")[0]
        if isinstance(model_input, dict):
            return model_input
        raise ValueError("Unsupported input type")

    def _validate_token(self, token: str) -> bool:
        """トークンを検証してコンテキストに設定"""
        try:
            if not token:
                raise ValueError("Token not found")
            validate_databricks_token(SQLConfig.SQL_SERVER_HOST_NAME, token)
            TokenContext.set("auth_token", token)
            log_message("Token successfully validated")
            return True
        except Exception as e:
            log_message(f"Token validation error: {e}", level="ERROR")
            return False

    def _build_state(self, config: dict, prompt: str) -> dict | Command:
        """現在の状態に応じてstateを構築"""
        snapshot = self._agent.get_state(config)
        # log_message(f"snapshot: {snapshot}")
        # log_message(f"snapshot.next: {snapshot.next}")

        if snapshot.next:
            # HITL（再開）モード
            # log_message(f"Resuming interrupted thread at {snapshot.next}")
            return Command(resume=prompt, update={"prompt": prompt})
        else:
            # 通常（新規/継続）モード
            # log_message("Starting new turn")
            return self._create_initial_state(prompt)

    def _create_initial_state(self, prompt: str) -> dict:
        """初期状態を作成"""
        return {
            "prompt": prompt,
            "messages": [],
            "sql_query": "",
            "genie_download_url": None,
            "dataframe": None,
            "fig_data": None,
            "next_api_index": 0,
            "need_LLM": False,
            "Error": False,
        }

    def _run_agent(self, state, config: dict) -> tuple[dict | None, dict | None]:
        """エージェントを実行し、最終チャンクと中断ペイロードを返す"""
        last_chunk = None
        interrupted_payload = None

        for chunk in self._agent.stream(state, config=config, stream_mode="updates"):
            last_chunk = chunk
            interrupted_payload = self._extract_interrupt(chunk)
            if interrupted_payload:
                break

        # log_message(f"last_chunk: {last_chunk}")
        return last_chunk, interrupted_payload

    def _extract_interrupt(self, chunk: dict) -> dict | None:
        """チャンクから中断ペイロードを抽出"""
        log_message(f"[DEBUG] _extract_interrupt chunk keys: {list(chunk.keys())}")

        # トップレベルの __interrupt__
        if "__interrupt__" in chunk and chunk["__interrupt__"]:
            log_message("[DEBUG] Found __interrupt__ at top level")
            return chunk["__interrupt__"][-1].value

        # ネストされた __interrupt__
        for k, v in chunk.items():
            if isinstance(v, dict) and "__interrupt__" in v and v["__interrupt__"]:
                log_message(f"[DEBUG] Found __interrupt__ nested under key: {k}")
                return v["__interrupt__"][-1].value

        return None

    def _build_response(
        self,
        last_chunk: dict | None,
        interrupted_payload: dict | None,
        prompt: str,
        thread_id: str,
        token: str
    ) -> dict:
        """レスポンスを構築"""

        if interrupted_payload:
            return self._build_interrupted_response(
                prompt, interrupted_payload, thread_id
            )
        # end_build_time = time.time()
        # log_message(f"build_response took {end_build_time - start_build_time} seconds")
        return self._build_completed_response(
            last_chunk, prompt, thread_id
        )

    def _build_interrupted_response(
        self,
        user_prompt: str,
        payload: dict,
        thread_id: str
    ) -> dict:
        """中断時のレスポンスを構築"""
        response = {
            "status": "interrupted",
            "message": payload.get("message"),
            "df": payload.get("preview"),
            "fig_data": None,
            "sql_query": payload.get("sql_query"),
            "download_url": payload.get("genie_download_url"),
        }

        return response

    def _build_completed_response(
        self,
        last_chunk: dict | None,
        prompt: str,
        thread_id: str
    ) -> dict:
        """完了時のレスポンスを構築"""
        state_like = self._extract_state_from_chunk(last_chunk)
        # print(f"state_like: {state_like}")

        if not state_like:
            return self._error_response("応答の取得に失敗しました")

        # メッセージを取得
        messages = state_like.get("messages", [])
        last_message = messages[-1] if messages else None
        message_content = last_message.content if last_message else ""

        # log_message(f"messages: {messages}")

        response = {
            "status": "ok",
            "message": message_content,
            "df": state_like.get("dataframe"),
            "fig_data": state_like.get("fig_data"),
            "sql_query": state_like.get("sql_query"),
            # "download_url": state_like.get("genie_download_url"),
        }

        # 会話履歴を保存
        start_save_db = time.time()
        end_save_db = time.time()
        # log_message(f"save_message took {end_save_db - start_save_db} seconds")
        # エラーチェック
        if state_like.get("Error"):
            return self._error_response(message_content)

        return response

    def _extract_state_from_chunk(self, chunk: dict | None) -> dict | None:
        """チャンクからstate情報を抽出"""
        if not chunk or not isinstance(chunk, dict):
            return None

        state_keys = ("messages", "dataframe", "fig_data")

        # ノード名: { state diff } パターン
        for v in chunk.values():
            if isinstance(v, dict) and any(k in v for k in state_keys):
                return v

        # トップレベルに直接keysがあるパターン
        if any(k in chunk for k in state_keys):
            return chunk

        return None

    def _error_response(self, message: str) -> dict:
        """エラーレスポンスを生成"""
        return {
            "status": "error",
            "message": message
        }