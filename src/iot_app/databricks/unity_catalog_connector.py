from contextlib import contextmanager


@contextmanager
def get_databricks_connection():
    """Databricks Unity Catalog への接続を提供するコンテキストマネージャ。

    with get_databricks_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(sql, params)
        result = cursor.fetchone()
    """
    from flask import g
    import os

    server_hostname = os.getenv("DATABRICKS_SERVER_HOSTNAME", "")
    http_path = os.getenv("DATABRICKS_HTTP_PATH", "")
    access_token = getattr(g, "databricks_token", "")

    from databricks import sql as databricks_sql

    conn = databricks_sql.connect(
        server_hostname=server_hostname,
        http_path=http_path,
        access_token=access_token,
    )
    try:
        yield conn
    finally:
        conn.close()
