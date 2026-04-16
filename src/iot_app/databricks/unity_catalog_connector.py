import os
import re
import time

from databricks import sql
from flask import g

from iot_app.common.logger import get_logger

logger = get_logger(__name__)


class UnityCatalogConnector:
    """Unity Catalog 接続クラス（databricks-sql-connector 使用）"""

    def __init__(self):
        host = os.environ.get('DATABRICKS_HOST', '')
        # server_hostname は scheme なしのホスト名のみ
        self._server_hostname = re.sub(r'^https?://', '', host).rstrip('/')
        self._http_path = os.environ.get('DATABRICKS_HTTP_PATH', '')

    def _request(self, sql_text, params, operation, fetch_one=False, dml=False):
        """SQL 実行の内部メソッド（ログ出力・タイミング計測を一元管理）

        Args:
            sql_text (str): 実行する SQL（named parameter :param_name 形式）
            params (dict): パラメータ辞書
            operation (str): ログ出力用の操作名
            fetch_one (bool): True の場合は先頭1件のみ取得（dml=False 時のみ有効）
            dml (bool): True の場合は DML 専用パス（cursor.description / fetchall を呼ばない）

        Returns:
            list[dict] | dict | None: dml=True なら None、fetch_one=False なら list[dict]、True なら dict または None
        """
        logger.info("外部API呼び出し開始", extra={
            "service": "unity_catalog",
            "operation": operation,
        })
        start = time.time()
        token = getattr(getattr(g, 'current_user', None), 'databricks_token', None)
        converted_sql = re.sub(r':(\w+)', r'%(\1)s', sql_text)

        try:
            with sql.connect(
                server_hostname=self._server_hostname,
                http_path=self._http_path,
                access_token=token,
            ) as connection:
                with connection.cursor() as cursor:
                    cursor.execute(converted_sql, params)
                    if dml:
                        # DML 後は cursor.description が None になるため参照しない
                        result = None
                    else:
                        columns = [desc[0] for desc in cursor.description]
                        if fetch_one:
                            row = cursor.fetchone()
                            result = dict(zip(columns, row)) if row is not None else None
                        else:
                            result = [dict(zip(columns, row)) for row in cursor.fetchall()]

            duration_ms = int((time.time() - start) * 1000)
            logger.info("外部API完了", extra={
                "service": "unity_catalog",
                "operation": operation,
                "duration_ms": duration_ms,
            })
            return result

        except Exception as e:
            duration_ms = int((time.time() - start) * 1000)
            logger.error("外部API例外", exc_info=True, extra={
                "service": "unity_catalog",
                "operation": operation,
                "duration_ms": duration_ms,
                "failure_reason": str(e)[:200],
            })
            raise

    def execute(self, sql_text, params, operation="SQL実行") -> list[dict]:
        """SQL を実行して結果を list[dict] で返す

        Args:
            sql_text (str): 実行する SQL（named parameter :param_name 形式）
            params (dict): パラメータ辞書
            operation (str): ログ出力用の操作名

        Returns:
            list[dict]: クエリ結果行のリスト
        """
        return self._request(sql_text, params, operation)

    def execute_dml(self, sql_text, params, operation="DML実行") -> None:
        """INSERT / UPDATE / DELETE を実行する（DML専用パス）

        cursor.description が None になる DML に対応するため、
        cursor.description / fetchall / fetchone を呼ばない専用パスを使用する。

        Args:
            sql_text (str): 実行する SQL（named parameter :param_name 形式）
            params (dict): パラメータ辞書
            operation (str): ログ出力用の操作名
        """
        self._request(sql_text, params, operation, dml=True)

    def execute_one(self, sql_text, params, operation="SQL実行") -> dict | None:
        """SQL を実行して先頭1件を dict で返す（fetchone 使用）

        Args:
            sql_text (str): 実行する SQL（named parameter :param_name 形式）
            params (dict): パラメータ辞書
            operation (str): ログ出力用の操作名

        Returns:
            dict | None: 先頭1行。結果が0件の場合は None
        """
        return self._request(sql_text, params, operation, fetch_one=True)
