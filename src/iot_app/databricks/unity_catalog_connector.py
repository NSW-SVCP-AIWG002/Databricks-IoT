from iot_app.common.logger import get_logger

logger = get_logger(__name__)


class UnityCatalogConnector:
    """Unity Catalog 接続クライアント（Databricks SQL Connector）"""

    def execute(self, sql, params=None):
        """SQL を実行してリスト形式で結果を返す

        Args:
            sql (str): 実行するSQL文
            params (dict): バインドパラメータ

        Returns:
            list[dict]: クエリ結果行のリスト
        """
        return []
