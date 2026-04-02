import base64
import json
import re
import time
import traceback
from typing import TypedDict

from langchain_core.messages import HumanMessage
from langgraph.graph import StateGraph
import numpy as np
import pandas as pd
import requests
import plotly.express as px
import plotly.graph_objects as go
import plotly.io as pio

from conf.settings import endpoint
from conf.logging_config import log_message
from conf.prompt import graph_prompt
from src.utils.llm import post_chat
from src.utils.sandbox import validate_generated_code, execute_with_timeout, CodeExecutionTimeoutError

# エージェントがグラフ描画するコードを生成する関数
def plot_code_node(prompt, sql_query, df):
    user_msg = f"データ:\n{df}\n\n指示:\n{prompt}\n\nSQLクエリ:\n{sql_query}"
    try:
        start_llm = time.time()
        json_res = post_chat(
            endpoint=endpoint,
            system_prompt=graph_prompt,
            prompt=user_msg,
            messages=[],
            temperature=0.1,
        )
        end_llm = time.time()
        log_message(f"LLM時間: {end_llm - start_llm}秒")

        # json_res = json.loads(result[-1]['text'])
        python_code = json_res["python_code"]
        explain = json_res["explain"]
        return {"plot_code": python_code, "explain" : explain}
    except Exception as e:
        traceback.print_exc()
        return {"plot_code": f"コード生成エラー: {e}"}


def clean_code(code):
    # 全角記号を半角に
    code = code.replace('、', ',').replace('。', '.').replace('：', ':').replace('（', '(').replace('）', ')')
    code = code.replace('\u3000', ' ')
    return code
    

# グラフ化コードを実行する関数
def create_plot(prompt, sql_query, df):
    for i in range(5):
        try:
            start_plotcode = time.time()
            result = plot_code_node(prompt, sql_query, df)
            end_plotcode = time.time()
            log_message(f"PlotCode時間: {end_plotcode - start_plotcode}秒")
            plot_code = result["plot_code"]
            message = result["explain"]
            if "fig" in plot_code:
                plot_code_clean = clean_code(plot_code)
                # L1: コード静的解析
                is_safe, violation = validate_generated_code(plot_code_clean)
                if not is_safe:
                    raise ValueError(f"安全でないコードが検出されました: {violation}")
                # L2: 制限付き実行名前空間
                exec_namespace = {
                    "df": df, "go": go, "px": px,
                    "pd": pd, "np": np, "print": print,
                    "__builtins__": {}
                }
                start_exec = time.time()
                # L3: タイムアウト付き実行
                execute_with_timeout(plot_code_clean, exec_namespace, 30)
                end_exec = time.time()
                log_message(f"生成コード実行時間: {end_exec - start_exec}秒")
                fig = exec_namespace.get("fig")
                return fig, message
            else:
                print("グラフ生成コードにfig変数が含まれていません。")
                return None, message
        except Exception as e:
            log_message("グラフ生成コード実行エラー", level="ERROR")
            log_message(f"リトライ{i}回目")
            traceback.print_exc()
            prompt += f"\n\n次のエラー出ないようにしてください:{e}"
            continue
    return None, message