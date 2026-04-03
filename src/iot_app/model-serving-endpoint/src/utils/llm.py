import json
import os
import re

from typing import Any, List, Dict, Sequence, Union

from databricks.sdk import WorkspaceClient
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from databricks_langchain import ChatDatabricks
from conf.logging_config import log_message

def _clean_json_string(text_json: str | None) -> str | None:
    if not text_json:
        return None
    match = re.search(r'(\{.*\}|\[.*\])', text_json, re.DOTALL)
    if match:
        return match.group(0)
    return None

def _normalize_messages_for_llm(
    messages: Sequence[Union[BaseMessage, Dict[str, Any], str]] | None
) -> List[BaseMessage]:
    """
    既存の messages（BaseMessage / dict / str 混在可）を
    ChatDatabricks 用の BaseMessage リストに正規化する。
    """
    norm: List[BaseMessage] = []
    if not messages:
        return norm

    for m in messages:
        if isinstance(m, BaseMessage):
            norm.append(m)
        elif isinstance(m, dict):
            role = m.get("role", "user")
            content = str(m.get("content", ""))
            if role == "system":
                norm.append(SystemMessage(content=content))
            elif role == "assistant":
                norm.append(AIMessage(content=content))
            else:
                norm.append(HumanMessage(content=content))
        else:
            # 単なる文字列は user 発話として扱う（後方互換）
            norm.append(HumanMessage(content=str(m)))
    return norm

def post_chat(
    endpoint: str,   # 互換性のために受け取るが、ChatDatabricks 版では使わない
    system_prompt: str,
    prompt: str,
    messages: Sequence[Union[BaseMessage, Dict[str, Any], str]] | None = None,
    temperature: float = 0.1,
) -> Dict[str, Any]:
    """
    ChatDatabricks を使って LLM を呼び出し、レスポンスから JSON を抜き出して dict で返す。

    - endpoint: 互換性のために残しているが、本実装では無視。
    - system_prompt: SystemMessage として先頭に付与。
    - prompt: 今回のユーザ入力。
    - messages: 会話履歴（BaseMessage / dict / str いずれも受け入れる）。
    - temperature: llm.bind(temperature=...) で上書き。

    戻り値:
      - 応答テキスト中から JSON オブジェクト/配列を抽出できれば、その dict
      - JSON がなければ {"message": <生テキスト>} を返す
    """
    _ws = WorkspaceClient(
        host=os.environ.get("DATABRICKS_HOST"),
        client_id=os.environ.get("DATABRICKS_CLIENT_ID"),
        client_secret=os.environ.get("DATABRICKS_CLIENT_SECRET"),
    )
    llm = ChatDatabricks(
        workspace_client=_ws,
        endpoint=endpoint,
        temperature=0.1,
    )
    # print(f"post_chat called: system_prompt len={len(system_prompt)}, prompt={prompt[:50]}...")
    
    # 1) 履歴を BaseMessage リストに正規化
    norm_messages = _normalize_messages_for_llm(messages)

    # 2) System + 履歴 + 今回の Human でメッセージを構築
    llm_messages: List[BaseMessage] = [
        SystemMessage(content=system_prompt),
        *norm_messages,
        HumanMessage(content=prompt),
    ]
    # print(f"post_chat: llm_messages={llm_messages}")
    # 3) 温度を上書きして ChatDatabricks を呼ぶ
    llm_with_temp = llm.bind(temperature=temperature)
    try:
        resp = llm_with_temp.invoke(llm_messages)
    except Exception as e:
        log_message(f"Error in ChatDatabricks.invoke: {e}", level="ERROR")
        # 既存 post_chat が {} を返していた動きに合わせる
        return {}

    # ChatDatabricks の resp は ChatMessage（content は str か list）
    text = resp.content if isinstance(resp.content, str) else str(resp.content)
    log_message(f"LLM raw response (first 200 chars): {text[:200]}")

    # 4) JSON 抜き出し
    json_str = _clean_json_string(text)
    if json_str:
        try:
            parsed = json.loads(json_str)
            return parsed
        except Exception as e:
            log_message("Response is not JSON format, returning as text message", level="WARNING")

    # JSON でなければそのまま message として返す
    return {"message": text}