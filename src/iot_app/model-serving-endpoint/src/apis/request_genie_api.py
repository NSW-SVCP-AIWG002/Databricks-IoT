import base64
import requests
import traceback
import pandas as pd
import os
import time
import pytz
import io
import logging
from typing import Optional, Tuple, Dict, Any
from contextlib import contextmanager
from datetime import datetime

from databricks import sql
from databricks.sdk import WorkspaceClient

from conf.settings import FileStoreConfig, GenieConfig, TokenContext
from conf.logging_config import log_message
from db.connection import get_db_connection

# 定数の定義
JST_TIMEZONE = pytz.timezone('Asia/Tokyo')
DEFAULT_POLL_INTERVAL = 5
DEFAULT_POLL_TIMEOUT = 600
DEFAULT_MAX_RETRIES = 3

def create_workspace_client() -> WorkspaceClient:
    """
    新しいWorkspaceClientインスタンスを作成
    
    Returns:
        WorkspaceClient: 新しい接続インスタンス
    """
    auth_token = TokenContext.get("auth_token")
    return WorkspaceClient(
        host=FileStoreConfig.DATABRICKS_HOST,
        token=auth_token
    )

def upload_large_csv_with_sdk(
    df: pd.DataFrame, 
    sled_info: Dict[str, Any], 
    timestamp_jst: str,
) -> Optional[str]:
    """
    Databricks SDKを使用してCSVをアップロード（インメモリ処理）
    
    Args:
        df: アップロードするDataFrame
        sled_info: メッセージ情報を含む辞書
        timestamp_jst: JSTタイムスタンプ
    
    Returns:
        アップロードされたファイル名、失敗時はNone
    """
    # 入力検証
    if df is None or df.empty:
        log_message("DataFrameが空またはNoneです", level="WARNING")
        return None
    
    message_id = sled_info.get("message_id")
    if not message_id:
        log_message("message_idが指定されていません", level="WARNING")
        return None
    
    w = None
    try:
        # 新しいWorkspaceClientを作成（各リクエストごと）
        w = create_workspace_client()
        log_message("Databricks接続完了")
        
        # ファイル名とパスの生成
        save_csv_name = FileStoreConfig.CSV_FILE_NAME.format(
            message_id=message_id,
            timestamp=timestamp_jst
        )
        dbfs_path = f"/FileStore/{save_csv_name}"
        
        # CSVデータをメモリ上で処理（一時ファイルを使わない）
        csv_string = df.to_csv(index=False)
        csv_buffer = io.BytesIO(csv_string.encode('utf-8-sig'))
        
        # ファイルをアップロード
        w.dbfs.upload(dbfs_path, csv_buffer, overwrite=True)
        
        log_message(f"✓ アップロード完了: {dbfs_path}")
        return save_csv_name
        
    except Exception as e:
        log_message(f"アップロード失敗: {str(e)}", level="ERROR")
        return None
    finally:
        # 明示的なクリーンアップ（ガベージコレクションを待たない）
        if w is not None:
            try:
                # WorkspaceClientのクリーンアップ（必要に応じて）
                pass
            except:
                pass

def execution_sql(sql_query: str) -> pd.DataFrame:
    """
    SQLクエリを実行してDataFrameを返す
    
    Args:
        sql_query: 実行するSQLクエリ
    
    Returns:
        クエリ結果のDataFrame
    
    Raises:
        Exception: SQL実行エラー
    """
    connection = None
    cursor = None
    
    try:
        auth_token = TokenContext.get("auth_token")

        conn = get_db_connection(auth_token)
        cursor = conn.cursor()
        try:
            cursor.execute(sql_query)
            rows = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]
            return pd.DataFrame(rows, columns=columns)
        finally:
            cursor.close()
    except Exception as e:
        log_message(f"SQL実行エラー: {str(e)}",level="ERROR")
        raise

def get_api_headers() -> Dict[str, str]:
    """
    API用のヘッダーを取得
    
    Returns:
        Dict[str, str]: APIヘッダー
    """
    auth_token = TokenContext.get("auth_token")
    return {
        "Authorization": f"Bearer {auth_token}",
        "Content-Type": "application/json"
    }

def make_databricks_request(
    method: str, 
    endpoint: str, 
    json_data: Optional[Dict] = None,
    timeout: int = 30
) -> Dict[str, Any]:
    """
    Databricks APIにリクエストを送信する汎用関数
    
    Args:
        method: HTTPメソッド（"get" or "post"）
        endpoint: APIエンドポイント
        json_data: POSTリクエスト用のJSONデータ
        timeout: リクエストタイムアウト（秒）
    
    Returns:
        APIレスポンスのJSON
    
    Raises:
        ValueError: サポートされていないHTTPメソッドの場合
        requests.HTTPError: APIリクエストが失敗した場合
    """
    url = f"{GenieConfig.DATABRICKS_HOST}{endpoint}"
    headers = get_api_headers()
    
    method_lower = method.lower()
    
    try:
        if method_lower == "post":
            log_message("POSTリクエスト送信")
            response = requests.post(
                url, 
                headers=headers, 
                json=json_data,
                timeout=timeout
            )
        elif method_lower == "get":
            response = requests.get(
                url, 
                headers=headers,
                timeout=timeout
            )
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")
        
        response.raise_for_status()
        return response.json()
        
    except requests.Timeout:
        log_message(f"リクエストタイムアウト: {endpoint}", level="ERROR")
        raise
    except requests.RequestException as e:
        log_message(f"APIリクエストエラー: {str(e)}", level="ERROR")
        raise

def process_query_response(
    status_obj: Dict[str, Any],
    sql_query: str,
    sled_info: Dict[str, Any],
    timestamp_jst: str
) -> Tuple[str, str, pd.DataFrame, Dict[str, Any], Optional[str]]:
    """
    クエリレスポンスを処理して結果を返す
    
    Args:
        status_obj: ステータスオブジェクト
        sql_query: 実行されたSQLクエリ
        sled_info: メッセージ情報
        timestamp_jst: JSTタイムスタンプ
    
    Returns:
        (content, sql_query, df, sled_info, download_url)のタプル
    """
    atts = status_obj.get("attachments", [])
    if not atts or "query" not in atts[0]:
        return "No query attachment.", None, None, sled_info, None
    
    q = atts[0]["query"]
    content = q.get("description")
    statement_id = q.get("statement_id")
    
    try:
        # ステートメント結果を取得
        st = make_databricks_request(
            "get", 
            GenieConfig.STATEMENT_API.format(statement_id=statement_id)
        )
        
        manifest = st.get("manifest", {})
        result = st.get("result", {})
        rows = result.get("data_array", [])
        row_count = result.get("row_count", 0)
        
        # カラム情報の取得
        schema_columns = manifest.get("schema", {}).get("columns", [])
        cols = [c["name"] for c in schema_columns]
        df = pd.DataFrame(rows, columns=cols)
        
        # 大きなデータセットの場合はCSVファイルを生成
        download_url = None
        if row_count > 0:
            try:
                df_for_csv = execution_sql(sql_query)
                save_csv_name = upload_large_csv_with_sdk(
                    df_for_csv, 
                    sled_info, 
                    timestamp_jst
                )
                
                if save_csv_name:
                    download_url = f"{FileStoreConfig.DATABRICKS_HOST}/files/{save_csv_name}"
                    log_message(f"download_url: {download_url}")
            except Exception as e:
                log_message(f"CSV生成エラー: {str(e)}", level="ERROR")
                # CSVエラーがあってもデータは返す
        
        return content, sql_query, df, sled_info, download_url
        
    except Exception as e:
        log_message(f"クエリレスポンス処理エラー: {str(e)}", level="ERROR")
        return f"Error processing query: {str(e)}", sql_query, None, sled_info, None

def poll_for_completion(
    endpoint_url: str,
    sled_info: Dict[str, Any],
    timestamp_jst: str,
    poll_interval: int = DEFAULT_POLL_INTERVAL,
    poll_timeout: int = DEFAULT_POLL_TIMEOUT
) -> Tuple[Any, ...]:
    """
    完了までポーリングして結果を返す
    
    Args:
        endpoint_url: ポーリング用エンドポイントURL
        sled_info: メッセージ情報
        timestamp_jst: JSTタイムスタンプ
        poll_interval: ポーリング間隔（秒）
        poll_timeout: タイムアウト時間（秒）
    
    Returns:
        処理結果のタプル
    """
    start_time = time.time()
    
    while True:
        # タイムアウトチェック
        elapsed_time = time.time() - start_time
        if elapsed_time > poll_timeout:
            log_message(f"ポーリングタイムアウト: {elapsed_time}秒", level="WARNING")
            return "Polling timeout.", None, None, sled_info, None
        
        try:
            status_obj = make_databricks_request("get", endpoint_url)
            status = status_obj.get("status")
            
            if status == "COMPLETED":
                atts = status_obj.get("attachments", [])
                
                # クエリ結果の処理
                if atts and "query" in atts[0]:
                    q = atts[0]["query"]
                    sql_query = q.get("query")
                    return process_query_response(
                        status_obj, sql_query, sled_info, timestamp_jst
                    )
                
                # テキスト応答の処理
                if atts and "text" in atts[0]:
                    return atts[0]["text"]["content"], None, None, sled_info, None
                
                return "No attachment.", None, None, sled_info, None
            
            if status in ("FAILED", "CANCELED"):
                err = status_obj.get("error", status)
                log_message(f"Genie error: {err}", level="ERROR")
                return f"Genie error: {err}", None, None, sled_info, None
            
        except Exception as e:
            log_message(f"ポーリング中のエラー: {str(e)}", level="ERROR")
            # エラーが発生してもリトライ
            
        time.sleep(poll_interval)

def genie_conversation(
    prompt: str,
    sled_info: Optional[Dict[str, Any]] = None,
    search: bool = False,
    max_retries: int = DEFAULT_MAX_RETRIES,
    poll_interval: int = DEFAULT_POLL_INTERVAL,
    poll_timeout: int = DEFAULT_POLL_TIMEOUT,
    space_id: Optional[str] = None,  # 引数にスペースIDを追加
) -> Tuple[Any, ...]:
    """
    Genie APIとの対話を行う
    
    Args:
        prompt: 送信するプロンプト
        sled_info: 既存の会話情報（継続の場合）
        search: 新たなデータを取得するかのフラグ
        max_retries: 最大リトライ回数（現在未使用）
        poll_interval: ポーリング間隔（秒）
        poll_timeout: ポーリングタイムアウト（秒）

        space_id: 利用するGenieスペースID
                  Noneの場合はsled_infoから復元、さらに無ければ売上スペースをデフォルトとする
    
    Returns:
        (content, sql_query, df, sled_info, download_url)のタプル
    """
    # 日本時間を取得
    timestamp_jst = datetime.now(JST_TIMEZONE).strftime("%Y%m%d_%H%M%S")
    
    statement_data = {
        "content": prompt,
        "disposition": "EXTERNAL_LINKS"
    }
    
    try:
        # 分析モードの処理
        if not search and sled_info:
            endpoint_url = GenieConfig.GENIE_GET_MESSAGE_API.format(
                # ここにスペースIDを追加
                space_id=space_id,
                conversation_id=sled_info["conversation_id"],
                message_id=sled_info["message_id"],
            )
            return poll_for_completion(
                endpoint_url, sled_info, timestamp_jst, poll_interval, poll_timeout
            )
        
        # 新規または継続の会話を開始
        if not sled_info:
            # 初回投稿
            resp = make_databricks_request(
                "post",
                GenieConfig.GENIE_START_CONVERSATION_API.format(
                    space_id=space_id

                ),
                json_data=statement_data,
            )
            msg = resp["message"]
            conversation_id = msg["conversation_id"]
            message_id = msg["id"]
            sled_info = msg
        else:
            # 継続投稿
            conversation_id = sled_info["conversation_id"]
            resp = make_databricks_request(
                "post",
                GenieConfig.GENIE_POST_MESSAGE_API.format(
                    space_id=space_id,

                    conversation_id=conversation_id,
                ),
                json_data=statement_data,
            )
            msg = resp.get("message", resp)
            message_id = msg["id"]
            sled_info = msg
        
        # ポーリング処理
        endpoint_url = GenieConfig.GENIE_GET_MESSAGE_API.format(
            space_id=space_id,

            conversation_id=conversation_id,
            message_id=message_id,
        )
        
        return poll_for_completion(
            endpoint_url, sled_info, timestamp_jst, poll_interval, poll_timeout
        )
        
    except Exception as e:
        log_message(f"Genie conversation error: {str(e)}", level="ERROR")
        return f"Error: {str(e)}", None, None, sled_info, None