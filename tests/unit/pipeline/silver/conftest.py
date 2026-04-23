"""
シルバー層パイプライン 単体テスト共通設定

Databricks環境外（ローカル/CI）でテストを実行するために必要な
PySpark・Databricksランタイムグローバル変数のモック設定を行う。

設計書: docs/03-features/ldp-pipeline/silver-layer/ldp-pipeline-specification.md
"""
import builtins
import os
import sys
from unittest.mock import MagicMock

# ---------------------------------------------------------------------------
# sys.path 設定
# src/pipeline/silver を追加することで、パイプライン内部の
# "from functions.xxx import ..." スタイルの絶対インポートを解決する
# ---------------------------------------------------------------------------
_silver_src = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "../../../../src/pipeline/silver")
)
if _silver_src not in sys.path:
    sys.path.insert(0, _silver_src)

# ---------------------------------------------------------------------------
# PySpark モック
# pyspark は Databricks ランタイム上でのみ利用可能。
# モジュールロード時のインポートエラーを防ぐため sys.modules に登録する。
# ---------------------------------------------------------------------------
for _pyspark_mod in [
    "pyspark",
    "pyspark.sql",
    "pyspark.sql.functions",
    "delta",
    "delta.tables",
]:
    if _pyspark_mod not in sys.modules:
        sys.modules[_pyspark_mod] = MagicMock()

# ---------------------------------------------------------------------------
# Databricks ランタイムグローバル変数モック
# dbutils / spark は Databricks ノートブック環境が提供するグローバル変数。
# pipeline モジュールは builtins 経由で参照するため、ここで差し込む。
# ---------------------------------------------------------------------------
_dbutils_mock = MagicMock()
_dbutils_mock.secrets.get.return_value = "mock_secret_value"
builtins.dbutils = _dbutils_mock
builtins.spark = MagicMock()
