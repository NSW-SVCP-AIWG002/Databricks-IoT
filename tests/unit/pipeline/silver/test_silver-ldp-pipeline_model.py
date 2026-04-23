"""
シルバー層LDPパイプライン モデル層 - 単体テスト

対象モジュール:
    pipeline.silver.functions.alert_judgment  (MEASUREMENT_COLUMN_MAP, ALERT_STATUS_*)
    pipeline.silver.functions.constants       (BINARY_DATA_SIZE, BINARY_STRUCT_FORMAT,
                                               SENSOR_FIELDS, OLTP_MAX_RETRIES,
                                               sensor_schema)

設計書: docs/03-features/ldp-pipeline/silver-layer/ldp-pipeline-specification.md
観点表: docs/05-testing/unit-test/unit-test-perspectives.md
"""

import struct

import pytest

# ===========================================================================
# パイプライン設定定数
# 設計書: § ストリーミング処理仕様
# ===========================================================================

@pytest.mark.unit
class TestPipelineConstants:
    """パイプライン設定定数を検証する

    観点: ストリーミング処理仕様 > パイプライン設定
    対応観点表: 2.1 正常系処理

    設計書定義:
        PIPELINE_TRIGGER_INTERVAL = "10 seconds"  （10秒間隔のマイクロバッチ処理）
        TOPIC_NAME = "eh-telemetry"               （Azure Event Hubs トピック名）
    """

    def test_pipeline_trigger_interval_is_10_seconds(self):
        """2.1.1: PIPELINE_TRIGGER_INTERVAL が設計書定義の "10 seconds" である

        実行内容: PIPELINE_TRIGGER_INTERVAL の値を検証
        想定結果: "10 seconds" である（設計書 §ストリーミング処理仕様「トリガー間隔: 10秒」）
        """
        from pipeline.silver.functions.constants import PIPELINE_TRIGGER_INTERVAL
        # Assert
        assert PIPELINE_TRIGGER_INTERVAL == "10 seconds"

    def test_topic_name_is_eh_telemetry(self):
        """2.1.1: TOPIC_NAME が設計書定義の "eh-telemetry" である

        実行内容: TOPIC_NAME の値を検証
        想定結果: "eh-telemetry" である（設計書 §Kafka接続設定「トピック名」）
        """
        from pipeline.silver.functions.constants import TOPIC_NAME
        # Assert
        assert TOPIC_NAME == "eh-telemetry"


# ===========================================================================
# 測定項目IDとセンサーカラムの対応マップ
# 設計書: § アラート処理仕様 > 測定項目IDとセンサーカラムの対応
# ===========================================================================

@pytest.mark.unit
class TestMeasurementColumnMap:
    """測定項目IDとセンサーカラム名の対応マップを検証する

    観点: アラート処理仕様 > 測定項目IDとセンサーカラムの対応
    対応観点表: 2.1 正常系処理, 1.1.6 不整値チェック

    設計書定義: measurement_item_id 1〜22 の22エントリ
        1:  external_temp                   （共通外気温度）
        2:  set_temp_freezer_1              （第1冷凍設定温度）
        3:  internal_sensor_temp_freezer_1  （第1冷凍庫内センサー温度）
        4:  internal_temp_freezer_1         （第1冷凍表示温度）
        5:  df_temp_freezer_1               （第1冷凍DF温度）
        6:  condensing_temp_freezer_1       （第1冷凍凝縮温度）
        7:  adjusted_internal_temp_freezer_1（第1冷凍微調整後庫内温度）
        8:  set_temp_freezer_2              （第2冷凍設定温度）
        9:  internal_sensor_temp_freezer_2  （第2冷凍庫内センサー温度）
        10: internal_temp_freezer_2         （第2冷凍表示温度）
        11: df_temp_freezer_2               （第2冷凍DF温度）
        12: condensing_temp_freezer_2       （第2冷凍凝縮温度）
        13: adjusted_internal_temp_freezer_2（第2冷凍微調整後庫内温度）
        14: compressor_freezer_1            （第1冷凍圧縮機回転数）
        15: compressor_freezer_2            （第2冷凍圧縮機回転数）
        16: fan_motor_1                     （第1ファンモーター回転数）
        17: fan_motor_2                     （第2ファンモーター回転数）
        18: fan_motor_3                     （第3ファンモーター回転数）
        19: fan_motor_4                     （第4ファンモーター回転数）
        20: fan_motor_5                     （第5ファンモーター回転数）
        21: defrost_heater_output_1         （防露ヒータ出力(1)）
        22: defrost_heater_output_2         （防露ヒータ出力(2)）
    """

    def test_map_contains_exactly_22_entries(self):
        """2.1.1: マップに設計書定義通り22エントリが存在する

        実行内容: MEASUREMENT_COLUMN_MAP のエントリ数を検証
        想定結果: エントリ数が22である（設計書 §測定項目IDとセンサーカラムの対応）
        """
        from pipeline.silver.functions.alert_judgment import MEASUREMENT_COLUMN_MAP
        # Assert
        assert len(MEASUREMENT_COLUMN_MAP) == 22

    def test_map_keys_are_sequential_integers_1_to_22(self):
        """2.1.1: マップのキーが1〜22の連続した整数である

        実行内容: MEASUREMENT_COLUMN_MAP のキー集合を検証
        想定結果: set(keys) == {1, 2, ..., 22}
        """
        from pipeline.silver.functions.alert_judgment import MEASUREMENT_COLUMN_MAP
        # Assert
        assert set(MEASUREMENT_COLUMN_MAP.keys()) == set(range(1, 23))

    def test_map_values_match_specification_exactly(self):
        """2.1.1: マップの各値が設計書定義のセンサーカラム名と完全一致する

        実行内容: MEASUREMENT_COLUMN_MAP の全エントリを設計書の定義と比較
        想定結果: 全エントリが設計書の定義と一致する
        """
        from pipeline.silver.functions.alert_judgment import MEASUREMENT_COLUMN_MAP
        # Arrange
        expected = {
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
        # Assert
        assert MEASUREMENT_COLUMN_MAP == expected

    def test_map_keys_are_all_integers(self):
        """2.1.1: マップの全キーが int 型である

        実行内容: MEASUREMENT_COLUMN_MAP の全キーの型を検証
        想定結果: 全キーが int 型である
        """
        from pipeline.silver.functions.alert_judgment import MEASUREMENT_COLUMN_MAP
        # Assert
        for item_id in MEASUREMENT_COLUMN_MAP.keys():
            assert isinstance(item_id, int), (
                f"キー '{item_id}' が整数でない: {type(item_id)}"
            )

    def test_map_values_are_all_strings(self):
        """2.1.1: マップの全値が str 型である

        実行内容: MEASUREMENT_COLUMN_MAP の全値の型を検証
        想定結果: 全値が str 型である
        """
        from pipeline.silver.functions.alert_judgment import MEASUREMENT_COLUMN_MAP
        # Assert
        for item_id, column_name in MEASUREMENT_COLUMN_MAP.items():
            assert isinstance(column_name, str), (
                f"measurement_item_id={item_id} のカラム名が文字列でない: {type(column_name)}"
            )

    def test_map_values_have_no_duplicates(self):
        """1.1.6 (1.6.2): マップの値（カラム名）に重複が存在しない

        実行内容: MEASUREMENT_COLUMN_MAP の値のユニーク数と全件数を比較
        想定結果: 重複なし（各測定項目IDに対してユニークなカラム名が割り当てられている）
        """
        from pipeline.silver.functions.alert_judgment import MEASUREMENT_COLUMN_MAP
        # Assert
        values = list(MEASUREMENT_COLUMN_MAP.values())
        assert len(values) == len(set(values))

    def test_first_entry_is_external_temp(self):
        """2.1.1: 測定項目ID=1 は "external_temp"（共通外気温度）である

        実行内容: MEASUREMENT_COLUMN_MAP[1] を検証
        想定結果: "external_temp" が返される
        """
        from pipeline.silver.functions.alert_judgment import MEASUREMENT_COLUMN_MAP
        # Assert
        assert MEASUREMENT_COLUMN_MAP[1] == "external_temp"

    def test_last_entry_is_defrost_heater_output_2(self):
        """2.1.1: 測定項目ID=22 は "defrost_heater_output_2"（防露ヒータ出力(2)）である

        実行内容: MEASUREMENT_COLUMN_MAP[22] を検証
        想定結果: "defrost_heater_output_2" が返される
        """
        from pipeline.silver.functions.alert_judgment import MEASUREMENT_COLUMN_MAP
        # Assert
        assert MEASUREMENT_COLUMN_MAP[22] == "defrost_heater_output_2"


# ===========================================================================
# バイナリフォーマット定数
# 設計書: § バイナリ/JSON判定・変換処理 > バイナリフォーマット定義
# ===========================================================================

@pytest.mark.unit
class TestBinaryFormatConstants:
    """バイナリテレメトリデータのフォーマット定数を検証する

    観点: データ変換仕様 > バイナリ/JSON判定・変換処理 > バイナリフォーマット定義
    対応観点表: 2.1 正常系処理, 1.1.6 不整値チェック

    設計書定義:
        BINARY_DATA_SIZE = 312 （STRING(128) + INT64(8) + FLOAT64×22(176) = 312バイト）
        BINARY_STRUCT_FORMAT = "<128sq22d" （リトルエンディアン）
    """

    def test_binary_data_size_is_312(self):
        """2.1.1: BINARY_DATA_SIZE が設計書定義の312バイトである

        実行内容: BINARY_DATA_SIZE の値を検証
        想定結果: 312 である
        """
        from pipeline.silver.functions.constants import BINARY_DATA_SIZE
        # Assert
        assert BINARY_DATA_SIZE == 312

    def test_binary_data_size_matches_struct_calcsize(self):
        """2.1.1: BINARY_DATA_SIZE が BINARY_STRUCT_FORMAT のパックサイズと一致する

        実行内容: struct.calcsize(BINARY_STRUCT_FORMAT) と BINARY_DATA_SIZE を比較
        想定結果: 両者が一致する（STRING(128) + INT64(8) + FLOAT64×22(176) = 312）
        """
        from pipeline.silver.functions.constants import BINARY_DATA_SIZE, BINARY_STRUCT_FORMAT
        # Assert
        assert struct.calcsize(BINARY_STRUCT_FORMAT) == BINARY_DATA_SIZE

    def test_binary_struct_format_value_is_correct(self):
        """2.1.1: BINARY_STRUCT_FORMAT が設計書定義の "<128sq22d" である

        実行内容: BINARY_STRUCT_FORMAT の値を検証
        想定結果: "<128sq22d" と一致する

        設計書定義:
            '<' = リトルエンディアン
            '128s' = device_id (STRING, 128バイト)
            'q' = event_timestamp (INT64, 8バイト, ミリ秒)
            '22d' = 22センサー値 (FLOAT64×22, 176バイト)
        """
        from pipeline.silver.functions.constants import BINARY_STRUCT_FORMAT
        # Assert
        assert BINARY_STRUCT_FORMAT == "<128sq22d"

    def test_binary_struct_format_starts_with_little_endian_marker(self):
        """2.1.1: BINARY_STRUCT_FORMAT がリトルエンディアン('<')で始まる

        実行内容: BINARY_STRUCT_FORMAT の先頭文字を検証
        想定結果: '<' で始まる（設計書定義「リトルエンディアン」）
        """
        from pipeline.silver.functions.constants import BINARY_STRUCT_FORMAT
        # Assert
        assert BINARY_STRUCT_FORMAT.startswith("<")

    def test_binary_struct_format_can_pack_and_unpack_312_bytes(self):
        """2.1.1: BINARY_STRUCT_FORMAT で312バイトのパック・アンパックが正常に行える

        実行内容: struct.pack で312バイトのデータを生成し、struct.unpack で元の値を取り出す
        想定結果: パック結果が312バイトで、アンパックが成功する
        """
        from pipeline.silver.functions.constants import BINARY_STRUCT_FORMAT
        # Arrange
        test_values = [b"test-device_id", 1737624600000] + [25.5] * 22
        # Act
        packed = struct.pack(BINARY_STRUCT_FORMAT, *test_values)
        unpacked = struct.unpack(BINARY_STRUCT_FORMAT, packed)
        # Assert
        assert len(packed) == 312
        assert unpacked[0] == b"test-device_id"


# ===========================================================================
# センサーフィールド定義（SENSOR_FIELDS）
# 設計書: § バイナリ/JSON判定・変換処理 > バイナリフォーマット定義
# ===========================================================================

@pytest.mark.unit
class TestSensorFields:
    """バイナリアンパック順序に対応するセンサーフィールド名リストを検証する

    観点: データ変換仕様 > バイナリ/JSON判定・変換処理 > バイナリフォーマット定義
    対応観点表: 2.1 正常系処理, 1.1.6 不整値チェック

    設計書定義: 22センサーフィールド（バイナリオフセット137〜312の順）
        external_temp, set_temp_freezer_1, internal_sensor_temp_freezer_1,
        internal_temp_freezer_1, df_temp_freezer_1, condensing_temp_freezer_1,
        adjusted_internal_temp_freezer_1, set_temp_freezer_2,
        internal_sensor_temp_freezer_2, internal_temp_freezer_2,
        df_temp_freezer_2, condensing_temp_freezer_2,
        adjusted_internal_temp_freezer_2, compressor_freezer_1,
        compressor_freezer_2, fan_motor_1〜5, defrost_heater_output_1〜2
    """

    def test_sensor_fields_count_is_22(self):
        """2.1.1: SENSOR_FIELDS に22個のフィールドが定義されている

        実行内容: SENSOR_FIELDS のエントリ数を検証
        想定結果: 22 である（BINARY_STRUCT_FORMAT の '22d' に対応）
        """
        from pipeline.silver.functions.constants import SENSOR_FIELDS
        # Assert
        assert len(SENSOR_FIELDS) == 22

    def test_sensor_fields_order_matches_specification(self):
        """2.1.1: SENSOR_FIELDS の順序が設計書のバイナリオフセット順と完全一致する

        実行内容: SENSOR_FIELDS の全エントリを設計書のオフセット順と比較
        想定結果: 全フィールドが設計書定義の順序と一致する
        """
        from pipeline.silver.functions.constants import SENSOR_FIELDS
        # Arrange
        expected = [
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
        # Assert
        assert SENSOR_FIELDS == expected

    def test_sensor_fields_are_all_strings(self):
        """2.1.1: SENSOR_FIELDS の全エントリが str 型である

        実行内容: SENSOR_FIELDS の全エントリの型を検証
        想定結果: 全エントリが str 型である
        """
        from pipeline.silver.functions.constants import SENSOR_FIELDS
        # Assert
        for i, field in enumerate(SENSOR_FIELDS):
            assert isinstance(field, str), (
                f"インデックス {i} のフィールド名が文字列でない: {type(field)}"
            )

    def test_sensor_fields_has_no_duplicates(self):
        """1.1.6 (1.6.2): SENSOR_FIELDS に重複したフィールド名が存在しない

        実行内容: SENSOR_FIELDS のユニーク数と全件数を比較
        想定結果: 重複なし（全フィールドが一意）
        """
        from pipeline.silver.functions.constants import SENSOR_FIELDS
        # Assert
        assert len(SENSOR_FIELDS) == len(set(SENSOR_FIELDS))

    def test_sensor_fields_count_matches_struct_format_double_count(self):
        """2.1.1: SENSOR_FIELDS の件数が BINARY_STRUCT_FORMAT の double 数と一致する

        実行内容: SENSOR_FIELDS の件数と BINARY_STRUCT_FORMAT の 'd' 個数を比較
        想定結果: 両者が一致する（22個）
        """
        import re
        from pipeline.silver.functions.constants import SENSOR_FIELDS, BINARY_STRUCT_FORMAT
        # Arrange - フォーマット文字列から double（d）の個数を抽出
        double_count = sum(
            int(m.group(1)) if m.group(1) else 1
            for m in re.finditer(r"(\d*)d", BINARY_STRUCT_FORMAT)
        )
        # Assert
        assert len(SENSOR_FIELDS) == double_count

    def test_sensor_fields_first_element_is_external_temp(self):
        """2.1.1: SENSOR_FIELDS[0]（バイナリオフセット137）は "external_temp" である

        実行内容: SENSOR_FIELDS[0] の値を検証
        想定結果: "external_temp" が返される（設計書定義のオフセット137の先頭フィールド）
        """
        from pipeline.silver.functions.constants import SENSOR_FIELDS
        # Assert
        assert SENSOR_FIELDS[0] == "external_temp"

    def test_sensor_fields_last_element_is_defrost_heater_output_2(self):
        """2.1.1: SENSOR_FIELDS[-1]（バイナリオフセット最終）は "defrost_heater_output_2" である

        実行内容: SENSOR_FIELDS[-1] の値を検証
        想定結果: "defrost_heater_output_2" が返される
        """
        from pipeline.silver.functions.constants import SENSOR_FIELDS
        # Assert
        assert SENSOR_FIELDS[-1] == "defrost_heater_output_2"

    def test_sensor_fields_values_align_with_measurement_column_map(self):
        """2.1.1: SENSOR_FIELDS の集合と MEASUREMENT_COLUMN_MAP の値集合が一致する

        実行内容: SENSOR_FIELDS の集合と MEASUREMENT_COLUMN_MAP の値集合を比較
        想定結果: 両者が一致する（同じセンサーフィールドを参照）
        """
        from pipeline.silver.functions.constants import SENSOR_FIELDS
        from pipeline.silver.functions.alert_judgment import MEASUREMENT_COLUMN_MAP
        # Assert
        assert set(SENSOR_FIELDS) == set(MEASUREMENT_COLUMN_MAP.values())


# ===========================================================================
# OLTPリトライ設定定数
# 設計書: § 外部連携仕様 > OLTPリトライ戦略
# ===========================================================================

@pytest.mark.unit
class TestOltpRetryConstants:
    """OLTPリトライ設定定数を検証する

    観点: 外部連携仕様 > OLTPリトライ戦略
    対応観点表: 2.1 正常系処理

    設計書定義:
        OLTP_MAX_RETRIES = 3（3回失敗で例外送出）
        OLTP_RETRY_INTERVALS: ジッター付き指数バックオフ（1〜2秒, 2〜4秒, 4〜8秒）
        リトライ対象MySQLエラーコード: {2003, 2006, 2013}
    """

    def test_oltp_max_retries_is_3(self):
        """2.1.1: OLTP_MAX_RETRIES が設計書定義の3回である

        実行内容: OLTP_MAX_RETRIES の値を検証
        想定結果: 3 である（設計書 §OLTPリトライ戦略「最大リトライ回数: 3回」）
        """
        from pipeline.silver.functions.constants import OLTP_MAX_RETRIES
        # Assert
        assert OLTP_MAX_RETRIES == 3

    def test_oltp_retry_intervals_count_matches_max_retries(self):
        """2.1.1: OLTP_RETRY_INTERVALS の要素数が OLTP_MAX_RETRIES と一致する

        実行内容: OLTP_RETRY_INTERVALS の要素数と OLTP_MAX_RETRIES を比較
        想定結果: 要素数が 3 である（各リトライ試行に対応するインターバルが設定されている）
        """
        from pipeline.silver.functions.constants import OLTP_MAX_RETRIES, OLTP_RETRY_INTERVALS
        # Assert
        assert len(OLTP_RETRY_INTERVALS) == OLTP_MAX_RETRIES

    def test_oltp_retry_intervals_are_all_positive(self):
        """2.1.1: OLTP_RETRY_INTERVALS の全値が正数である

        実行内容: OLTP_RETRY_INTERVALS の全要素が正の値であることを検証
        想定結果: 全値が 0 より大きい
        """
        from pipeline.silver.functions.constants import OLTP_RETRY_INTERVALS
        # Assert
        for i, interval in enumerate(OLTP_RETRY_INTERVALS):
            assert interval > 0, f"OLTP_RETRY_INTERVALS[{i}] = {interval} が正数でない"

    def test_retryable_mysql_errnos_contains_required_codes(self):
        """2.1.1: RETRYABLE_MYSQL_ERRNOS に設計書定義の3つのエラーコードが含まれる

        実行内容: RETRYABLE_MYSQL_ERRNOS の値を検証
        想定結果: {2003, 2006, 2013} が含まれる（接続系エラーコード）

        設計書定義:
            2003: Can't connect to MySQL server
            2006: MySQL server has gone away
            2013: Lost connection to MySQL server during query
        """
        from pipeline.silver.functions.constants import RETRYABLE_MYSQL_ERRNOS
        # Assert
        assert 2003 in RETRYABLE_MYSQL_ERRNOS, "errno 2003 (Can't connect) が RETRYABLE_MYSQL_ERRNOS に含まれていない"
        assert 2006 in RETRYABLE_MYSQL_ERRNOS, "errno 2006 (Server gone away) が RETRYABLE_MYSQL_ERRNOS に含まれていない"
        assert 2013 in RETRYABLE_MYSQL_ERRNOS, "errno 2013 (Lost connection) が RETRYABLE_MYSQL_ERRNOS に含まれていない"


# ===========================================================================
# アラートステータス定数
# 設計書: § 外部連携仕様 > アラート履歴登録処理
# ===========================================================================

@pytest.mark.unit
class TestAlertStatusConstants:
    """アラートステータスID定数を検証する

    観点: 外部連携仕様 > アラート履歴登録処理 > アラート履歴処理の設計方針
    対応観点表: 2.1 正常系処理

    設計書定義:
        ALERT_STATUS_FIRING    = 1  （発生中）
        ALERT_STATUS_RECOVERED = 2  （復旧済み）
    """

    def test_alert_status_firing_is_1(self):
        """2.1.1: ALERT_STATUS_FIRING が 1 (発生中) である

        実行内容: ALERT_STATUS_FIRING の値を検証
        想定結果: 1 である（設計書定義「初期ステータス: 発生中 (alert_status_id=1)」）
        """
        from pipeline.silver.functions.alert_judgment import ALERT_STATUS_FIRING
        # Assert
        assert ALERT_STATUS_FIRING == 1

    def test_alert_status_recovered_is_2(self):
        """2.1.1: ALERT_STATUS_RECOVERED が 2 (復旧済み) である

        実行内容: ALERT_STATUS_RECOVERED の値を検証
        想定結果: 2 である（設計書定義「復旧ステータス: 復旧済み (alert_status_id=2)」）
        """
        from pipeline.silver.functions.alert_judgment import ALERT_STATUS_RECOVERED
        # Assert
        assert ALERT_STATUS_RECOVERED == 2


# ===========================================================================
# センサーデータスキーマ（SENSOR_SCHEMA）
# 設計書: § JSONパース処理 > センサーデータスキーマ
# ===========================================================================

@pytest.mark.unit
class TestSensorSchema:
    """JSONパース用センサーデータスキーマの定義を検証する

    観点: JSONパース処理 > センサーデータスキーマ
    対応観点表: 2.1 正常系処理, 1.1.6 不整値チェック

    設計書定義:
        合計24フィールド（必須2 + センサー22）
        device_id:       IntegerType, nullable=False（必須）
        event_timestamp: StringType,  nullable=False（必須）
        センサー22項目:   DoubleType,  nullable=True
    """

    def test_sensor_schema_has_24_fields(self):
        """2.1.1: SENSOR_SCHEMA に設計書定義通り24フィールドが存在する

        実行内容: SENSOR_SCHEMA.fields のフィールド数を検証
        想定結果: 24 である（device_id + event_timestamp + センサー22項目）
        """
        from pipeline.silver.functions.constants import SENSOR_SCHEMA
        # Assert
        assert len(SENSOR_SCHEMA.fields) == 24

    def test_device_id_field_is_integer_and_required(self):
        """2.1.1: SENSOR_SCHEMA[0] が IntegerType かつ nullable=False である

        実行内容: 先頭フィールドの名前・型・nullable を検証
        想定結果: name="device_id", type=IntegerType, nullable=False
        """
        from pyspark.sql.types import IntegerType
        from pipeline.silver.functions.constants import SENSOR_SCHEMA
        # Arrange
        field = SENSOR_SCHEMA.fields[0]
        # Assert
        assert field.name == "device_id"
        assert isinstance(field.dataType, IntegerType)
        assert field.nullable is False

    def test_event_timestamp_field_is_string_and_required(self):
        """2.1.1: SENSOR_SCHEMA[1] が StringType かつ nullable=False である

        実行内容: 2番目フィールドの名前・型・nullable を検証
        想定結果: name="event_timestamp", type=StringType, nullable=False
        """
        from pyspark.sql.types import StringType
        from pipeline.silver.functions.constants import SENSOR_SCHEMA
        # Arrange
        field = SENSOR_SCHEMA.fields[1]
        # Assert
        assert field.name == "event_timestamp"
        assert isinstance(field.dataType, StringType)
        assert field.nullable is False

    def test_all_22_sensor_fields_are_double_and_nullable(self):
        """2.1.1: センサー22項目（インデックス2〜23）が DoubleType かつ nullable=True である

        実行内容: インデックス2〜23の全フィールドの型・nullable を検証
        想定結果: 全フィールドが DoubleType かつ nullable=True
        """
        from pyspark.sql.types import DoubleType
        from pipeline.silver.functions.constants import SENSOR_SCHEMA
        # Arrange
        sensor_fields = SENSOR_SCHEMA.fields[2:]
        # Assert
        assert len(sensor_fields) == 22
        for field in sensor_fields:
            assert isinstance(field.dataType, DoubleType), (
                f"フィールド '{field.name}' の型が DoubleType でない: {type(field.dataType)}"
            )
            assert field.nullable is True, (
                f"フィールド '{field.name}' が nullable=True でない"
            )

    def test_sensor_field_names_match_specification_in_order(self):
        """2.1.1: センサー22項目のフィールド名が設計書定義の順序と完全一致する

        実行内容: インデックス2〜23のフィールド名を設計書の定義と比較
        想定結果: 全フィールド名・順序が一致する
        """
        from pipeline.silver.functions.constants import SENSOR_SCHEMA
        # Arrange
        expected_sensor_names = [
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
        # Act
        actual_names = [f.name for f in SENSOR_SCHEMA.fields[2:]]
        # Assert
        assert actual_names == expected_sensor_names

    def test_only_device_id_and_event_timestamp_are_required(self):
        """1.1.1: nullable=False のフィールドが device_id と event_timestamp のみである

        実行内容: nullable=False のフィールド名集合を検証
        想定結果: {"device_id", "event_timestamp"} のみ（センサー項目はすべて nullable）
        """
        from pipeline.silver.functions.constants import SENSOR_SCHEMA
        # Arrange
        required_fields = {f.name for f in SENSOR_SCHEMA.fields if not f.nullable}
        # Assert
        assert required_fields == {"device_id", "event_timestamp"}

    def test_no_duplicate_field_names(self):
        """1.1.6 (1.6.2): SENSOR_SCHEMA に重複したフィールド名が存在しない

        実行内容: 全フィールド名のユニーク数と全件数を比較
        想定結果: 重複なし（全フィールドが一意）
        """
        from pipeline.silver.functions.constants import SENSOR_SCHEMA
        # Arrange
        names = [f.name for f in SENSOR_SCHEMA.fields]
        # Assert
        assert len(names) == len(set(names))

    def test_sensor_schema_field_names_align_with_sensor_fields_constant(self):
        """2.1.1: SENSOR_SCHEMA のセンサーフィールド名集合が SENSOR_FIELDS と一致する

        実行内容: SENSOR_SCHEMA インデックス2〜23 の名前集合と SENSOR_FIELDS の集合を比較
        想定結果: 両者が一致する（バイナリ変換と JSON パースで同一フィールドを参照）
        """
        from pipeline.silver.functions.constants import SENSOR_SCHEMA, SENSOR_FIELDS
        # Arrange
        schema_sensor_names = {f.name for f in SENSOR_SCHEMA.fields[2:]}
        # Assert
        assert schema_sensor_names == set(SENSOR_FIELDS)
