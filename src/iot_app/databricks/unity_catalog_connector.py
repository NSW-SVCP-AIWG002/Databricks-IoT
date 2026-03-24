import os
import re

from databricks import sql
from flask import g


class UnityCatalogConnector:
    """Unity Catalog 接続クラス（databricks-sql-connector 使用）"""

    def __init__(self):
        host = os.environ.get('DATABRICKS_HOST', '')
        # server_hostname は scheme なしのホスト名のみ
        self._server_hostname = re.sub(r'^https?://', '', host).rstrip('/')
        self._http_path = os.environ.get('DATABRICKS_HTTP_PATH', '')

    def execute(self, sql_text, params) -> list[dict]:
        """SQL を実行して結果を list[dict] で返す

        Args:
            sql_text (str): 実行する SQL（named parameter :param_name 形式）
            params (dict): パラメータ辞書

        Returns:
            list[dict]: クエリ結果行のリスト
        """
        token = getattr(g, 'databricks_token', None)

        # :param_name → %(param_name)s に変換（databricks-sql-connector の形式）
        converted_sql = re.sub(r':(\w+)', r'%(\1)s', sql_text)

        with sql.connect(
            server_hostname=self._server_hostname,
            http_path=self._http_path,
            access_token=token,
        ) as connection:
            with connection.cursor() as cursor:
                cursor.execute(converted_sql, params)
                columns = [desc[0] for desc in cursor.description]
                return [dict(zip(columns, row)) for row in cursor.fetchall()]

    def execute_one(self, sql_text, params) -> dict | None:
        """SQL を実行して先頭1件を dict で返す（fetchone 使用）

        Args:
            sql_text (str): 実行する SQL（named parameter :param_name 形式）
            params (dict): パラメータ辞書

        Returns:
            dict | None: 先頭1行。結果が0件の場合は None
        """
        token = getattr(g, 'databricks_token', None)
        converted_sql = re.sub(r':(\w+)', r'%(\1)s', sql_text)

        with sql.connect(
            server_hostname=self._server_hostname,
            http_path=self._http_path,
            access_token=token,
        ) as connection:
            with connection.cursor() as cursor:
                cursor.execute(converted_sql, params)
                row = cursor.fetchone()
                if row is None:
                    return None
                columns = [desc[0] for desc in cursor.description]
                return dict(zip(columns, row))
