"""
シルバー層LDPパイプライン

Kafkaからテレメトリデータを取得し、シルバー層Delta Lakeに書き込む。
アラート判定・OLTP DB更新・メール送信キュー登録を foreachBatch で実行する。

実行環境: Databricks（spark / dbutils は Databricks ランタイムが提供）
"""

import builtins
builtins.dbutils = dbutils  # noqa: F821
builtins.spark = spark      # noqa: F821

from pyspark.sql import functions as F
from pyspark.sql.types import (
    DoubleType, IntegerType, StringType, StructField, StructType,
)

from functions.alert_judgment import (
    check_alerts_with_duration,
    enqueue_email_notification,
    evaluate_threshold,
    get_alert_abnormal_state,
    insert_alert_history,
    update_alert_abnormal_state,
    update_alert_history_on_recovery,
    update_device_status,
)
from functions.constants import PIPELINE_TRIGGER_INTERVAL, TOPIC_NAME
from functions.device_id_extraction import (
    extract_device_id_udf,
)
from functions.json_telemetry import convert_to_json_with_device_id_udf

# =============================================================================
# 接続設定（Databricks Secrets から取得）
# =============================================================================

EVENTHUBS_NAMESPACE = dbutils.secrets.get("iot-secrets", "eventhubs-namespace")
EVENTHUBS_CONNECTION_STRING = dbutils.secrets.get("iot-secrets", "eventhubs-connection-string")

HOST = dbutils.secrets.get("my_sql_secrets", "host")
DATABASE = "iot_app_db"
PORT = 3306
OLTP_JDBC_URL = f"jdbc:mysql://{HOST}:{PORT}/{DATABASE}?useSSL=true&requireSSL=true&verifyServerCertificate=true"

CHECKPOINT_LOCATION = (
    "abfss://checkpoints@{storage_account}.dfs.core.windows.net/silver_pipeline/"
)

SILVER_TABLE = "iot_catalog.silver.silver_sensor_data"

# =============================================================================
# Kafkaオプション
# =============================================================================

kafka_options = {
    "kafka.bootstrap.servers": f"{EVENTHUBS_NAMESPACE}.servicebus.windows.net:9093",
    "subscribe": TOPIC_NAME,
    "kafka.sasl.mechanism": "PLAIN",
    "kafka.security.protocol": "SASL_SSL",
    "kafka.sasl.jaas.config": (
        "kafkashaded.org.apache.kafka.common.security.plain.PlainLoginModule required "
        f'username="$ConnectionString" '
        f'password="{EVENTHUBS_CONNECTION_STRING}";'
    ),
    "startingOffsets": "latest",
    "failOnDataLoss": "false",
}

# =============================================================================
# センサーデータスキーマ
# =============================================================================

sensor_schema = StructType([
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
# マスタデータ取得（Spark JDBC）
# =============================================================================

def _jdbc_options(table: str) -> dict:
    """JDBC共通オプションを返す"""
    return {
        "url": OLTP_JDBC_URL,
        # "driver": "com.mysql.cj.jdbc.Driver",
        "dbtable": table,
        "user": dbutils.secrets.get("my_sql_secrets", "username"),
        "password": dbutils.secrets.get("my_sql_secrets", "password"),
    }


def get_device_master():
    """デバイスマスタを取得"""
    return spark.read.format("jdbc").options(**_jdbc_options("device_master")).load()


def get_alert_settings():
    """アラート設定マスタを取得"""
    return (
        spark.read.format("jdbc").options(**_jdbc_options("alert_setting_master")).load()
        .filter("delete_flag = FALSE")
    )


# =============================================================================
# foreachBatchコールバック
# =============================================================================

def process_sensor_batch(batch_df, batch_id):
    """
    マイクロバッチ処理メイン（foreachBatch コールバック）

    処理フロー:
    1. 空バッチスキップ
    2. マスタデータ取得
    3. 閾値判定・継続時間判定
    4. Delta Lake書込み
    5. OLTP更新（異常状態/アラート履歴/メール送信キュー/デバイスステータス）
    """
    if batch_df.isEmpty():
        return

    # マスタデータ取得（バッチごとに最新を参照）
    alert_settings_df = get_alert_settings()
    alert_state_df = get_alert_abnormal_state()

    # STEP 4: アラート判定（閾値 + 継続時間）
    threshold_df = evaluate_threshold(batch_df, alert_settings_df)
    alert_df = check_alerts_with_duration(threshold_df, alert_state_df)

    # STEP 5a: Delta Lake書込み（センサーデータ）
    output_df = alert_df.select(
        F.col("device_id"),
        F.col("organization_id"),
        F.col("event_timestamp"),
        F.to_date(F.col("event_timestamp")).alias("event_date"),
        *[F.col(f) for f in [
            "external_temp", "set_temp_freezer_1",
            "internal_sensor_temp_freezer_1", "internal_temp_freezer_1",
            "df_temp_freezer_1", "condensing_temp_freezer_1",
            "adjusted_internal_temp_freezer_1", "set_temp_freezer_2",
            "internal_sensor_temp_freezer_2", "internal_temp_freezer_2",
            "df_temp_freezer_2", "condensing_temp_freezer_2",
            "adjusted_internal_temp_freezer_2", "compressor_freezer_1",
            "compressor_freezer_2", "fan_motor_1", "fan_motor_2",
            "fan_motor_3", "fan_motor_4", "fan_motor_5",
            "defrost_heater_output_1", "defrost_heater_output_2",
        ]],
        F.col("raw_json").alias("sensor_data_json"),
        F.current_timestamp().alias("create_time"),
    )

    output_df.write.format("delta").mode("append").saveAsTable(SILVER_TABLE)

    # STEP 5a-2: MySQL書込み（センサーデータ）
    try:
        (
            output_df.write
            .format("jdbc")
            .options(**_jdbc_options("silver_sensor_data"))
            .mode("append")
            .save()
        )
    except Exception as e:
        print(f"[SILVER_ERR_007] MySQLへのセンサーデータ書込みに失敗しました: {e}")

    # STEP 5b: OLTP更新
    try:
        update_alert_abnormal_state(alert_df, batch_id)
    except Exception as e:
        print(f"[SILVER_ERR_006] アラート異常状態への書込みに失敗しました: {e}")

    try:
        insert_alert_history(alert_df, batch_id)
    except Exception as e:
        print(f"[SILVER_ERR_004] アラート履歴の登録に失敗しました: {e}")

    try:
        update_alert_history_on_recovery(alert_df, batch_id)
    except Exception as e:
        print(f"[SILVER_ERR_004] アラート履歴の復旧更新に失敗しました: {e}")

    try:
        enqueue_email_notification(alert_df, batch_id, spark)
    except Exception as e:
        print(f"[SILVER_ERR_003] メール送信キューへの書込みに失敗しました: {e}")

    try:
        update_device_status(alert_df, batch_id)
    except Exception as e:
        print(f"[SILVER_ERR_005] デバイスステータスの更新に失敗しました: {e}")


# =============================================================================
# パイプライン起動
# =============================================================================

def build_kafka_stream():
    """
    Kafkaストリームを構築し、デバイスID抽出・フォーマット変換・JSONパースを適用する

    Returns:
        DataFrame: センサーデータ（パース済み）
    """
    return (
        spark.readStream
        .format("kafka")
        .options(**kafka_options)
        .load()

        # STEP 1: Kafkaカラム選択
        .select(
            F.col("value"),
            F.col("topic"),
            F.col("key").cast("string").alias("message_key"),
            F.col("timestamp").alias("kafka_timestamp"),
        )

        # STEP 1.5: デバイスID抽出
        .withColumn(
            "extracted_device_id",
            extract_device_id_udf(
                F.col("topic"),
                F.col("message_key"),
                F.get_json_object(F.col("value").cast("string"), "$.device_id"),
            )
        )
        .filter(F.col("extracted_device_id").isNotNull())

        # STEP 1.6: バイナリ/JSON変換
        .withColumn(
            "raw_json",
            convert_to_json_with_device_id_udf(
                F.col("value"),
                F.col("extracted_device_id"),
            )
        )
        .filter(F.col("raw_json").isNotNull())

        # STEP 2: JSONパース
        .withColumn("parsed", F.from_json(F.col("raw_json"), sensor_schema))
        .filter(F.col("parsed").isNotNull())
        .filter(F.col("parsed.device_id").isNotNull())
        .filter(F.col("parsed.event_timestamp").isNotNull())
        .select(
            F.col("parsed.device_id").alias("device_id"),
            F.to_timestamp(F.col("parsed.event_timestamp")).alias("event_timestamp"),
            F.col("parsed.external_temp").alias("external_temp"),
            F.col("parsed.set_temp_freezer_1").alias("set_temp_freezer_1"),
            F.col("parsed.internal_sensor_temp_freezer_1").alias("internal_sensor_temp_freezer_1"),
            F.col("parsed.internal_temp_freezer_1").alias("internal_temp_freezer_1"),
            F.col("parsed.df_temp_freezer_1").alias("df_temp_freezer_1"),
            F.col("parsed.condensing_temp_freezer_1").alias("condensing_temp_freezer_1"),
            F.col("parsed.adjusted_internal_temp_freezer_1").alias("adjusted_internal_temp_freezer_1"),
            F.col("parsed.set_temp_freezer_2").alias("set_temp_freezer_2"),
            F.col("parsed.internal_sensor_temp_freezer_2").alias("internal_sensor_temp_freezer_2"),
            F.col("parsed.internal_temp_freezer_2").alias("internal_temp_freezer_2"),
            F.col("parsed.df_temp_freezer_2").alias("df_temp_freezer_2"),
            F.col("parsed.condensing_temp_freezer_2").alias("condensing_temp_freezer_2"),
            F.col("parsed.adjusted_internal_temp_freezer_2").alias("adjusted_internal_temp_freezer_2"),
            F.col("parsed.compressor_freezer_1").alias("compressor_freezer_1"),
            F.col("parsed.compressor_freezer_2").alias("compressor_freezer_2"),
            F.col("parsed.fan_motor_1").alias("fan_motor_1"),
            F.col("parsed.fan_motor_2").alias("fan_motor_2"),
            F.col("parsed.fan_motor_3").alias("fan_motor_3"),
            F.col("parsed.fan_motor_4").alias("fan_motor_4"),
            F.col("parsed.fan_motor_5").alias("fan_motor_5"),
            F.col("parsed.defrost_heater_output_1").alias("defrost_heater_output_1"),
            F.col("parsed.defrost_heater_output_2").alias("defrost_heater_output_2"),
            F.col("raw_json"),
        )

        # STEP 3: デバイスマスタ結合（organization_id付与）
        .join(F.broadcast(get_device_master()), "device_id", "left")
    )


def start_pipeline():
    """パイプライン起動"""
    kafka_stream = build_kafka_stream()

    query = (
        kafka_stream
        .writeStream
        .foreachBatch(process_sensor_batch)
        .option("checkpointLocation", CHECKPOINT_LOCATION)
        .trigger(processingTime=PIPELINE_TRIGGER_INTERVAL)
        .start()
    )

    query.awaitTermination()


# =============================================================================
# エントリーポイント（Databricks ノートブック実行時）
# =============================================================================

if __name__ == "__main__":
    start_pipeline()
