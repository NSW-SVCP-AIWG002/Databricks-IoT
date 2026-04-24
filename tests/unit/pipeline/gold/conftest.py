"""
ゴールド層パイプライン単体テスト共通設定

PySpark / Delta Lake がテスト環境にインストールされていない場合に
sys.modules へモックを注入し、テストの収集・実行を可能にする。
"""
import sys
from unittest.mock import MagicMock


class AnalysisException(Exception):
    """pyspark.sql.utils.AnalysisException のスタブ（パッケージ未インストール環境用）"""
    pass


# pyspark.sql.utils は AnalysisException を正しいクラスとして提供する必要があるため個別に構築
_pyspark_sql_utils = MagicMock()
_pyspark_sql_utils.AnalysisException = AnalysisException

if "pyspark" not in sys.modules:
    sys.modules["pyspark"] = MagicMock()
    sys.modules["pyspark.sql"] = MagicMock()
    sys.modules["pyspark.sql.functions"] = MagicMock()
    sys.modules["pyspark.sql.utils"] = _pyspark_sql_utils

if "delta" not in sys.modules:
    sys.modules["delta"] = MagicMock()
    sys.modules["delta.tables"] = MagicMock()
