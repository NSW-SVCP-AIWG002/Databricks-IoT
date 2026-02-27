import json
import numpy as np
import pandas as pd
import io
from io import StringIO
import re
import sys
import traceback

from conf.settings import endpoint
from conf.prompt import GENERAL_LLM_PROMPT, LLMAPI_prompt, ADVANCE_DATA_ANALYSIS_PROMPT
from conf.logging_config import log_message
from src.utils.llm import post_chat
from src.utils.dataframe import get_df_schema_info

def clean_code(code: str) -> str:
    """
    LLMが生成したテキストから実行可能なPythonコードのみを抽出・整形する。
    """
    # 1. Markdownコードブロック (```python ... ```) の抽出
    # re.DOTALL で改行も含めてマッチさせる
    match = re.search(r"```(?:python)?(.*?)```", code, re.DOTALL)
    if match:
        code = match.group(1)
    
    # 2. 前後の空白削除
    code = code.strip()

    return code

def advance_data_analysis(user_question, schema_info, df_json, messages):
    """
    Args:
        user_question (str): ユーザーの質問
        schema_info (str): データのスキーマ情報
        df_json (str): 実際のデータ（JSON文字列）
        messages (list): 会話履歴
    """

    # 1. プロンプトの構築
    formatted_prompt = f"""
        以下のスキーマ情報を持つDataFrame `df` に対して、ユーザーの質問に答えるコードを書いてください。

        ### スキーマ情報
        {schema_info}

        ### ユーザーの質問
        {user_question}
    """
    
    execution_result = ""  # 結果を格納する変数を初期化
    
    for i in range(5):
        try:
            # 2. LLMへのリクエスト
            result = post_chat(
                endpoint=endpoint,
                system_prompt=ADVANCE_DATA_ANALYSIS_PROMPT,
                prompt=formatted_prompt,
                messages=messages,
                temperature=0.1,
            )
            log_message(f"Advance_LLMからの応答:{result}")

            # 3. データの復元
            if df_json:
                records = json.loads(df_json)
                df = pd.DataFrame(records)
            else:
                return "分析対象のデータがありません。"

            # 4. コードの実行と出力のキャプチャ
            generated_code = result.get("message", "") 

            # local_vars = {"df": df, "pd": pd, "np": np, "json": json}
            exec_namespace = globals().copy()
            exec_namespace["df"] = df
            # stdoutをキャプチャするためのStringIOオブジェクト
            captured_output = StringIO()
            
            # 元のstdoutを保存
            original_stdout = sys.stdout
            
            try:
                # stdoutをStringIOにリダイレクト
                sys.stdout = captured_output
                
                
                # コード実行
                # exec(clean_code(generated_code), {}, local_vars)
                exec(clean_code(generated_code), exec_namespace)

                
            finally:
                # 必ず元のstdoutに戻す
                sys.stdout = original_stdout
            
            # キャプチャした出力を取得
            execution_result = captured_output.getvalue()
            
            # 成功したらループを抜ける
            break
            
        except Exception as e:
            print(f"リトライ: {i+1}, エラー: {str(e)}")
            continue

    # 5. 結果を返す
    if not execution_result.strip():
        return "コードは実行されましたが、結果が出力されませんでした（print関数が使われていない可能性があります）。"
        
    return execution_result

def generate_llm_response(prompt, messages, api_list, df_json, selected):
    if df_json:
        schema_info = get_df_schema_info(df_json)
        df_analysis_result = advance_data_analysis(prompt, schema_info, df_json, messages)
        log_message(f"df_analysis_result:{df_analysis_result}")
    else:
        df_analysis_result = None

    if api_list == ['LLM']:
        sys_prompt = GENERAL_LLM_PROMPT
    else:
        items = [it for it in selected if it.get("api") == "LLM"]

        if items:
            user_prompt = items[0].get("prompt", "")
        else:
            error_msg = "LLMAPIの設定が適切ではありません。"
            logger.error(error_msg)
            return {
                "messages": [error_msg],
                "Error": True,
            }

        prompt = f"""
            質問: {user_prompt}

            以下の検索結果を参考にして、上記の質問に回答してください。
            ユーザークエリ：{prompt}
                apiからのresponse:
                {df_analysis_result}
        """.strip()
        sys_prompt = LLMAPI_prompt

    result = post_chat(
        endpoint=endpoint,
        system_prompt=sys_prompt,
        prompt=prompt,
        messages=messages,
        temperature=0.1,
    )
    
    message = result["message"]  
    return message