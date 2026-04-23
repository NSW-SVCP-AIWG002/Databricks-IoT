import builtins as _builtins
import random
import certifi as _certifi

from pyspark.sql.types import (
    DoubleType, IntegerType, StringType, StructField, StructType,
)

# =============================================================================
# パイプライン設定
# =============================================================================

PIPELINE_TRIGGER_INTERVAL = "10 seconds"
TOPIC_NAME = "eh-telemetry"

# =============================================================================
# バイナリフォーマット定義
# =============================================================================

BINARY_STRUCT_FORMAT = "<128sq22d"  # Little-endian: STRING(128) + INT64(8) + FLOAT64*22(176)
BINARY_DATA_SIZE = 312  # バイト数: STRING(128) + INT64(8) + FLOAT64*22(176) = 312

# センサーフィールド名（バイナリアンパック順序と対応）
SENSOR_FIELDS = [
    "external_temp",
    "set_temp_freezer_1",
    "internal_sensor_temp_freezer_1",
    "internal_temp_freezer_1",
    "df_temp_freezer_1",
    "condensing_temp_freezer_1",
    "adjusted_internal_temp_freezer_1",
    "set_temp_freezer_2",
    "internal_sensor_temp_freezer_2",
    "internal_temp_freezer_2",
    "df_temp_freezer_2",
    "condensing_temp_freezer_2",
    "adjusted_internal_temp_freezer_2",
    "compressor_freezer_1",
    "compressor_freezer_2",
    "fan_motor_1",
    "fan_motor_2",
    "fan_motor_3",
    "fan_motor_4",
    "fan_motor_5",
    "defrost_heater_output_1",
    "defrost_heater_output_2",
]

# =============================================================================
# センサーデータスキーマ（JSONパース用）
# 設計書: § JSONパース処理 > センサーデータスキーマ
# =============================================================================

SENSOR_SCHEMA = StructType([
    StructField("device_id", IntegerType(), False),
    StructField("event_timestamp", StringType(), False),
    StructField("external_temp", DoubleType(), True),
    StructField("set_temp_freezer_1", DoubleType(), True),
    StructField("internal_sensor_temp_freezer_1", DoubleType(), True),
    StructField("internal_temp_freezer_1", DoubleType(), True),
    StructField("df_temp_freezer_1", DoubleType(), True),
    StructField("condensing_temp_freezer_1", DoubleType(), True),
    StructField("adjusted_internal_temp_freezer_1", DoubleType(), True),
    StructField("set_temp_freezer_2", DoubleType(), True),
    StructField("internal_sensor_temp_freezer_2", DoubleType(), True),
    StructField("internal_temp_freezer_2", DoubleType(), True),
    StructField("df_temp_freezer_2", DoubleType(), True),
    StructField("condensing_temp_freezer_2", DoubleType(), True),
    StructField("adjusted_internal_temp_freezer_2", DoubleType(), True),
    StructField("compressor_freezer_1", DoubleType(), True),
    StructField("compressor_freezer_2", DoubleType(), True),
    StructField("fan_motor_1", DoubleType(), True),
    StructField("fan_motor_2", DoubleType(), True),
    StructField("fan_motor_3", DoubleType(), True),
    StructField("fan_motor_4", DoubleType(), True),
    StructField("fan_motor_5", DoubleType(), True),
    StructField("defrost_heater_output_1", DoubleType(), True),
    StructField("defrost_heater_output_2", DoubleType(), True),
])

# =============================================================================
# 測定項目IDとセンサーカラムのマッピング
# =============================================================================

MEASUREMENT_COLUMN_MAP = {
    1:  "external_temp",
    2:  "set_temp_freezer_1",
    3:  "internal_sensor_temp_freezer_1",
    4:  "internal_temp_freezer_1",
    5:  "df_temp_freezer_1",
    6:  "condensing_temp_freezer_1",
    7:  "adjusted_internal_temp_freezer_1",
    8:  "set_temp_freezer_2",
    9:  "internal_sensor_temp_freezer_2",
    10: "internal_temp_freezer_2",
    11: "df_temp_freezer_2",
    12: "condensing_temp_freezer_2",
    13: "adjusted_internal_temp_freezer_2",
    14: "compressor_freezer_1",
    15: "compressor_freezer_2",
    16: "fan_motor_1",
    17: "fan_motor_2",
    18: "fan_motor_3",
    19: "fan_motor_4",
    20: "fan_motor_5",
    21: "defrost_heater_output_1",
    22: "defrost_heater_output_2",
}

# =============================================================================
# MySQL接続設定（Databricks Secrets経由で注入される想定）
# =============================================================================

def get_mysql_config():
    """
    MySQL接続設定を返す（遅延解決）

    Spark Connect ワーカーではモジュールインポート時に dbutils が利用不可なため、
    実行時に builtins.dbutils 経由で解決する。
    """
    _dbutils = _builtins.dbutils
    return {
        "host": _dbutils.secrets.get("my_sql_secrets", "host"),
        "port": 3306,
        "user": _dbutils.secrets.get("my_sql_secrets", "username"),
        "password": _dbutils.secrets.get("my_sql_secrets", "password"),
        "database": "iot_app_db",
        "charset": "utf8mb4",
        "connect_timeout": 10,
        "read_timeout": 30,
        "write_timeout": 30,
        "ssl_ca": _certifi.where(),    # certifi CA証明書でSSL有効化（Azure MySQL対応）
        "ssl_verify_cert": True,
        "ssl_verify_identity": False,  # ホスト名検証はスキップ
    }

# ドライバーではインポート時に初期化、ワーカーではスキップ
try:
    MYSQL_CONFIG = get_mysql_config()
except (NameError, AttributeError):
    MYSQL_CONFIG = None

# =============================================================================
# OLTPリトライ設定
# =============================================================================

OLTP_MAX_RETRIES = 3

# ジッター付き指数バックオフ（秒）: 1-2秒, 2-4秒, 4-8秒
OLTP_RETRY_INTERVALS = [
    random.uniform(1, 2),
    random.uniform(2, 4),
    random.uniform(4, 8),
]

# リトライ対象MySQLエラーコード
RETRYABLE_MYSQL_ERRNOS = {
    2003,  # Can't connect to MySQL server
    2006,  # MySQL server has gone away
    2013,  # Lost connection to MySQL server during query
}
