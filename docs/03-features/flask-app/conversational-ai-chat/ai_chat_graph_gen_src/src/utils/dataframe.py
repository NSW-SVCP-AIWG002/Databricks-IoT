import json
import io

import pandas as pd
import numpy as np
from typing import Any, Optional
from pandas.api.types import is_datetime64_any_dtype, is_object_dtype

def _auto_convert_numeric_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    DataFrameの各カラムをチェックし、数値に変換できそうな
    object型（文字列）のカラムを数値型に自動で変換する。

    Args:
        df (pd.DataFrame): 処理対象のDataFrame

    Returns:
        pd.DataFrame: 型変換後のDataFrame
    """
    df_converted = df.copy()
    
    print("--- 自動型変換を開始します ---")
    for col in df_converted.columns:
        # カラムのデータ型が 'object' (主に文字列) の場合のみ処理
        if df_converted[col].dtype == 'object':
            # まず、数値への変換を試みる
            # errors='coerce' で、変換できない値は NaN になる
            converted_series = pd.to_numeric(df_converted[col], errors='coerce')
            
            # 変換を試みた結果、少なくとも1つでも有効な数値があれば
            # (すべてがNaNになっていなければ)、そのカラムを置き換える
            if converted_series.notna().any():
                df_converted[col] = converted_series
                print(f"✅ カラム '{col}' を数値型に変換しました。")
            else:
                print(f"ℹ️ カラム '{col}' は数値として解釈できませんでした。元の型のままです。")

    print("--- 自動型変換が完了しました ---\n")
    return df_converted

def get_df_schema_info(df_json: str) -> str:
    """
    LLMに渡すためのスキーマ情報を生成する。
    全データは渡さず、カラム名、型、代表的な値（カテゴリカルな場合）のみを抽出する。
    このデータ構造を前提に、〇〇を知るためのPandasコードを書いて
    """
    # 引数で受け取ったJSON文字列をDataFrameに戻す
    if df_json:
        records = json.loads(df_json)
        df = pd.DataFrame(records)
    else:
        return "分析対象のデータがありません。"
    
    buffer = io.StringIO()
    df.info(buf=buffer)
    info_str = buffer.getvalue()
    
    # カラムごとのユニークな値を抽出（カテゴリカル列のヒントになる）
    unique_vals = []
    for col in df.columns:
        if df[col].dtype == 'object' or df[col].dtype.name == 'category':
            # ユニーク数が少なければ全リスト、多ければトップ10を表示
            uniqs = df[col].unique()
            if len(uniqs) < 20:
                unique_vals.append(f"- {col}: {list(uniqs)}")
            else:
                unique_vals.append(f"- {col}: {list(uniqs[:10])} ... (total {len(uniqs)})")
    
    unique_str = "\n".join(unique_vals)

    return f"""
    ### DataFrame Schema
    {info_str}

    ### Categorical Columns (Sample Values)
    {unique_str}
    
    ### First 3 Rows (Sample)
    {df.head(3).to_string()}
    """

def to_records_json_or_none(x: Any) -> Optional[str]:
    """
    値 `x` をレコード指向（orient="records"）のJSON文字列へ変換するユーティリティ。

    次を満たす場合のみJSON文字列を返す:
    - `x` が `str` のときはそのまま返す（すでにJSONである想定を含む）。
    - `x` が `pd.DataFrame` かつ空でないときは、日付/日時列を 'YYYY-MM-DD' に正規化した上で
      `DataFrame.to_json(orient="records", force_ascii=False)` でエンコードする。
    それ以外（`None`、空の `DataFrame`、その他の型）の場合は `None` を返す。

    Args:
        x (Any): 変換対象。許容される主な値は `None`、`str`、`pandas.DataFrame`。

    Returns:
        Optional[str]: レコード指向（orient="records"）のJSON文字列。
        変換不能時（`None`、空の `DataFrame`、未対応の型）は `None`。
    """
    if x is None:
        return None
    if isinstance(x, str):
        return x
    if isinstance(x, pd.DataFrame):
        if x.empty:
            return None
        return x.to_json(orient="records", force_ascii=False)
    return None

def get_df_summary(json_str: str) -> str:
    """
    Pandas DataFrameの要約情報（info, head, describe）を
    LLMが読みやすい形式の文字列として生成する。

    Args:
        json_str (str): 対象のjson_str

    Returns:
        str: フォーマットされたDataFrameの要約情報
    """
    # 1. JSON文字列をPythonのリスト/辞書にパース
    data = json.loads(json_str)
    
    # 2. DataFrameに変換
    df = pd.DataFrame(data)
    df = _auto_convert_numeric_columns(df)
    print(df)
    # df.info() の出力を文字列としてキャプチャ
    buffer = io.StringIO()
    df.info(buf=buffer)
    info_str = buffer.getvalue()

    # df.head() の出力を文字列としてキャプチャ
    head_str = df.head().to_string()

    # Markdown形式で整形
    summary = f"""
        ### DataFrame Information

        #### df.info()
        {info_str}

        #### df.head()
        {head_str}
    """
    # 数値データを持つカラムのみを対象にする
    numeric_df = df.select_dtypes(include='number')
    if not numeric_df.empty:
        describe_str = numeric_df.describe().to_string()
        summary += f"""
            #### df.describe()
            {describe_str}
        """
    return summary
