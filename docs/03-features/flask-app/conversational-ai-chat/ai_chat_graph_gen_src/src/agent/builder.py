from langgraph.graph import END, StateGraph

from db.checkpointer import DatabricksUnityCatalogCheckpointer
from src.agent.nodes import *

# ----------------------------
# agent builder
# ----------------------------
def build_agent():
    """
    エージェントの実行グラフ（StateGraph）を構築・コンパイルして返す。

    構成:
        - ノード登録:
          "planner", "router",
          "GenieAPI", "GraphAPI",  
          "final_response", "LLM" を追加する。
        - 条件付き遷移:
          - "router" → state["next"] の値に応じて各ノード/ENDへ分岐（"LLM" を含む）。
          - "GenieAPI" → check_genie_response の結果で "GenieConfirm"/"GraphAPI"/"router" へ。
          - "final_response" → decide_llm_or_end の結果で "LLM"/END へ。
        - エントリ/固定遷移:
          - エントリポイントは "planner"。
          - "planner" → "router"
          - 各APIノード（"GraphAPI"）→ "router"
          - "LLM" → END

    Returns:
        Any: builder.compile() の戻り値（LangGraphの実行可能グラフオブジェクト）。
    """
    memory_saver = DatabricksUnityCatalogCheckpointer()
    builder = StateGraph(AgentState)

    # ノード
    builder.add_node("planner", planner_node)
    builder.add_node("router", routing_node)
    builder.add_node("GenieAPI", genieapi_node)
    builder.add_node("GraphAPI", graphapi_node)
    builder.add_node("final_response", final_response)
    builder.add_node("LLM", llm_node)

    # 条件付き遷移
    builder.add_conditional_edges(
        "router",
        lambda s: s["next"],
        {
            "router": "router",
            "GenieAPI": "GenieAPI",
            "GraphAPI": "GraphAPI",
            "final_response": "final_response",
            "LLM": "LLM",
            "END": END,
        },
    )
    builder.add_conditional_edges(
        "GenieAPI", check_genie_response, {"GraphAPI": "GraphAPI", "router": "router"}
    )
 
    builder.add_conditional_edges("final_response", decide_llm_or_end, {"LLM": "LLM", "END": END})

    # エントリとエッジ
    builder.set_entry_point("planner")
    builder.add_edge("planner", "router")
    builder.add_edge("GraphAPI", "router")
    builder.add_edge("LLM", END)

    return builder.compile(checkpointer=memory_saver)