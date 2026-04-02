from databricks import sql
from conf.settings import SQLConfig

_connections = {}

def get_db_connection(access_token: str, use_cache: bool = True):
    """DB接続を取得"""
    if use_cache and access_token in _connections:
        conn = _connections[access_token]
        # 接続が生きているか確認
        try:
            conn.cursor().execute("SELECT 1")
            return conn
        except:
            pass  # 接続切れなら再作成
    
    conn = sql.connect(
        server_hostname=SQLConfig.SQL_SERVER_HOST_NAME,
        http_path=SQLConfig.SQL_HTTP_PATH,
        access_token=access_token,
    )
    
    if use_cache:
        _connections[access_token] = conn
    
    return conn