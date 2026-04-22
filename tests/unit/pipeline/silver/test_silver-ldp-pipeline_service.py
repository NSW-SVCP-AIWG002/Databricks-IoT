"""
シルバー層LDPパイプライン サービス層 - 単体テスト

対象モジュール:
    pipeline.silver.functions.device_id_extraction
    pipeline.silver.functions.json_telemetry
    pipeline.silver.functions.alert_judgment  (純粋関数のみ)
    pipeline.silver.functions.mysql_connector (is_retryable_error)

設計書: docs/03-features/ldp-pipeline/silver-layer/ldp-pipeline-specification.md
観点表: docs/05-testing/unit-test/unit-test-perspectives.md
"""

import json
import socket
import struct
from unittest.mock import MagicMock

import pytest


# ---------------------------------------------------------------------------
# テスト用ヘルパー
# ---------------------------------------------------------------------------

def _make_binary_telemetry(
    device_id: int = 12345,
    event_timestamp_ms: int = 1737624600000,
    sensor_values: list = None,
) -> bytes:
    """188バイトのバイナリテレメトリデータを生成する。

    バイナリフォーマット（リトルエンディアン、設計書 § バイナリフォーマット定義）:
        <i  = device_id        (INT32,  4バイト)
        <q  = event_timestamp  (INT64,  8バイト, ミリ秒)
        <22d= センサー値22個   (FLOAT64×22, 176バイト)
    合計: 4 + 8 + 176 = 188バイト
    """
    if sensor_values is None:
        sensor_values = [
            25.5, -20.0, -19.8, -19.5, -15.2, 35.0, -19.7,
            -25.0, -24.6, -24.3, -18.5, 38.0, -24.5,
            2800.0, 3100.0, 1200.0, 1180.0, 1150.0, 1220.0, 1190.0,
            0.0, 0.0,
        ]
    return struct.pack("<iq22d", device_id, event_timestamp_ms, *sensor_values)


# ===========================================================================
# STEP 1.5: デバイスID抽出 — MQTT Topic
# 設計書: § デバイスID抽出処理 > MQTT TopicからのデバイスID抽出
# ===========================================================================

@pytest.mark.unit
class TestExtractDeviceIdFromTopic:
    """MQTT Topicパスから機器IDを抽出する

    観点: データ変換仕様 > デバイスID抽出処理 > MQTT TopicからのデバイスID抽出
    対応観点表: 2.1 正常系処理, 1.1.1 必須チェック, 1.1.6 不整値チェック

    設計書定義:
        パターン: ^/([^/]+)/data/refrigerator$
        機器IDは文字列（数値に限らない）。スラッシュを含まない任意の文字列を許容する。
    """

    def test_numeric_id_extracted_correctly(self):
        """2.1.1: 数値IDを含む正常なMQTT Topicの場合、デバイスIDが返される

        実行内容: topic = "/12345/data/refrigerator"
        想定結果: "12345" が返される
        """
        from pipeline.silver.functions.device_id_extraction import extract_device_id_from_topic
        # Arrange
        topic = "/12345/data/refrigerator"
        # Act
        result = extract_device_id_from_topic(topic)
        # Assert
        assert result == "12345"

    def test_alphanumeric_id_with_hyphen_extracted_correctly(self):
        """2.1.1: ハイフンを含む文字列IDの場合、正常に抽出される

        実行内容: topic = "/dev-001/data/refrigerator"
        想定結果: "dev-001" が返される（機器IDは文字列。数値に限らない）
        """
        from pipeline.silver.functions.device_id_extraction import extract_device_id_from_topic
        # Arrange
        topic = "/dev-001/data/refrigerator"
        # Act
        result = extract_device_id_from_topic(topic)
        # Assert
        assert result == "dev-001"

    def test_alphabetic_id_extracted_correctly(self):
        """2.1.1: アルファベットのみのIDも正常に抽出される

        実行内容: topic = "/abc/data/refrigerator"
        想定結果: "abc" が返される
        """
        from pipeline.silver.functions.device_id_extraction import extract_device_id_from_topic
        # Arrange
        topic = "/abc/data/refrigerator"
        # Act
        result = extract_device_id_from_topic(topic)
        # Assert
        assert result == "abc"

    def test_none_topic_returns_none(self):
        """1.1.1 (1.1.2): Noneが渡された場合、Noneが返される

        実行内容: topic = None
        想定結果: None が返される
        """
        from pipeline.silver.functions.device_id_extraction import extract_device_id_from_topic
        # Arrange
        topic = None
        # Act
        result = extract_device_id_from_topic(topic)
        # Assert
        assert result is None

    def test_invalid_path_format_returns_none(self):
        """1.1.6 (1.6.2): パターン不一致のTopicの場合、Noneが返される

        実行内容: topic = "/invalid/path"（refrigeratorサフィックスなし）
        想定結果: None が返される
        """
        from pipeline.silver.functions.device_id_extraction import extract_device_id_from_topic
        # Arrange
        topic = "/invalid/path"
        # Act
        result = extract_device_id_from_topic(topic)
        # Assert
        assert result is None

    def test_trailing_slash_returns_none(self):
        """1.1.6 (1.6.2): 末尾にスラッシュが付く場合、Noneが返される

        実行内容: topic = "/12345/data/refrigerator/"（末尾スラッシュ）
        想定結果: None が返される（正規表現 $ に不一致）
        """
        from pipeline.silver.functions.device_id_extraction import extract_device_id_from_topic
        # Arrange
        topic = "/12345/data/refrigerator/"
        # Act
        result = extract_device_id_from_topic(topic)
        # Assert
        assert result is None

    def test_slash_in_device_id_returns_none(self):
        """1.1.6 (1.6.2): 機器IDにスラッシュを含む場合、Noneが返される

        実行内容: topic = "/abc/def/data/refrigerator"（IDにスラッシュ混入）
        想定結果: None が返される（スラッシュを含まない任意の文字列のみ許容）
        """
        from pipeline.silver.functions.device_id_extraction import extract_device_id_from_topic
        # Arrange
        topic = "/abc/def/data/refrigerator"
        # Act
        result = extract_device_id_from_topic(topic)
        # Assert
        assert result is None

    def test_large_numeric_id_extracted_correctly(self):
        """2.1.1: 大きな数値IDも正常に抽出される

        実行内容: topic = "/9999999/data/refrigerator"
        想定結果: "9999999" が返される
        """
        from pipeline.silver.functions.device_id_extraction import extract_device_id_from_topic
        # Arrange
        topic = "/9999999/data/refrigerator"
        # Act
        result = extract_device_id_from_topic(topic)
        # Assert
        assert result == "9999999"


# ===========================================================================
# STEP 1.5: デバイスID抽出 — EventHub key
# 設計書: § デバイスID抽出処理 > EventHub keyからのデバイスID抽出
# ===========================================================================

@pytest.mark.unit
class TestExtractDeviceIdFromKey:
    """EventHubメッセージのkeyからデバイスIDを抽出する

    観点: データ変換仕様 > デバイスID抽出処理 > EventHub keyからのデバイスID抽出
    対応観点表: 2.1 正常系処理, 1.1.1 必須チェック

    設計書定義:
        - message_key が None または空文字・空白のみ → None を返す
        - それ以外 → message_key.strip() を返す
    """

    def test_valid_string_key_returns_device_id(self):
        """2.1.1: 有効な文字列keyが渡された場合、デバイスIDが返される

        実行内容: message_key = "12345"
        想定結果: "12345" が返される
        """
        from pipeline.silver.functions.device_id_extraction import extract_device_id_from_key
        # Arrange
        message_key = "12345"
        # Act
        result = extract_device_id_from_key(message_key)
        # Assert
        assert result == "12345"

    def test_none_key_returns_none(self):
        """1.1.1 (1.1.2): Noneが渡された場合、Noneが返される

        実行内容: message_key = None
        想定結果: None が返される
        """
        from pipeline.silver.functions.device_id_extraction import extract_device_id_from_key
        # Arrange
        message_key = None
        # Act
        result = extract_device_id_from_key(message_key)
        # Assert
        assert result is None

    def test_empty_string_key_returns_none(self):
        """1.1.1 (1.1.1): 空文字が渡された場合、Noneが返される

        実行内容: message_key = ""
        想定結果: None が返される
        """
        from pipeline.silver.functions.device_id_extraction import extract_device_id_from_key
        # Arrange
        message_key = ""
        # Act
        result = extract_device_id_from_key(message_key)
        # Assert
        assert result is None

    def test_whitespace_only_key_returns_none(self):
        """1.1.1 (1.1.4): 空白のみの場合、Noneが返される

        実行内容: message_key = "   "
        想定結果: None が返される
        """
        from pipeline.silver.functions.device_id_extraction import extract_device_id_from_key
        # Arrange
        message_key = "   "
        # Act
        result = extract_device_id_from_key(message_key)
        # Assert
        assert result is None

    def test_key_with_surrounding_spaces_returns_stripped_value(self):
        """2.1.1: 前後に空白がある文字列の場合、strip()した値が返される

        実行内容: message_key = "  12345  "
        想定結果: "12345" が返される
        """
        from pipeline.silver.functions.device_id_extraction import extract_device_id_from_key
        # Arrange
        message_key = "  12345  "
        # Act
        result = extract_device_id_from_key(message_key)
        # Assert
        assert result == "12345"

    def test_alphanumeric_key_with_hyphen_returns_correctly(self):
        """2.1.1: ハイフンを含む文字列keyが正常に返される

        実行内容: message_key = "dev-001"
        想定結果: "dev-001" が返される（keyは文字列、数値に限らない）
        """
        from pipeline.silver.functions.device_id_extraction import extract_device_id_from_key
        # Arrange
        message_key = "dev-001"
        # Act
        result = extract_device_id_from_key(message_key)
        # Assert
        assert result == "dev-001"


# ===========================================================================
# STEP 1.5: デバイスID抽出 — 統合処理
# 設計書: § デバイスID抽出処理 > デバイスID抽出の統合処理
# ===========================================================================

@pytest.mark.unit
class TestExtractDeviceId:
    """優先順位に従ってデバイスIDを抽出する統合処理

    観点: データ変換仕様 > デバイスID抽出処理 > デバイスID抽出の統合処理
    対応観点表: 2.1 正常系処理, 1.1.1 必須チェック

    設計書定義（優先順位）:
        1. MQTT Topic (/<機器ID>/data/refrigerator形式)
        2. EventHub key
        3. ペイロード内のdevice_id（フォールバック）
    """

    def test_mqtt_topic_has_highest_priority(self):
        """2.1.1: MQTT TopicからのIDが最優先（優先度1 > 2 > 3）

        実行内容: 有効なtopic・key・payload全て指定
        想定結果: topicから抽出したIDが返される
        """
        from pipeline.silver.functions.device_id_extraction import extract_device_id
        # Arrange
        topic = "/11111/data/refrigerator"
        message_key = "22222"
        payload_device_id = "33333"
        # Act
        result = extract_device_id(topic, message_key, payload_device_id)
        # Assert
        assert result == "11111"

    def test_event_hub_key_used_when_topic_is_none(self):
        """2.1.1: MQTT TopicがNoneの場合、EventHub keyを使用（優先度2）

        実行内容: topic=None、有効なkey・payload指定
        想定結果: keyから抽出したIDが返される
        """
        from pipeline.silver.functions.device_id_extraction import extract_device_id
        # Arrange
        topic = None
        message_key = "22222"
        payload_device_id = "33333"
        # Act
        result = extract_device_id(topic, message_key, payload_device_id)
        # Assert
        assert result == "22222"

    def test_event_hub_key_used_when_topic_is_invalid(self):
        """2.1.1: MQTT Topicが不正形式の場合もEventHub keyを使用（優先度2）

        実行内容: topicが不正形式、有効なkey指定
        想定結果: keyから抽出したIDが返される
        """
        from pipeline.silver.functions.device_id_extraction import extract_device_id
        # Arrange
        topic = "/not/valid/format"
        message_key = "22222"
        payload_device_id = "33333"
        # Act
        result = extract_device_id(topic, message_key, payload_device_id)
        # Assert
        assert result == "22222"

    def test_payload_device_id_used_as_fallback(self):
        """2.1.1: Topic/key両方無効な場合、ペイロードのdevice_idを使用（優先度3）

        実行内容: topic=None, key=None, 有効なpayload_device_id
        想定結果: payload_device_idが返される
        """
        from pipeline.silver.functions.device_id_extraction import extract_device_id
        # Arrange
        topic = None
        message_key = None
        payload_device_id = "33333"
        # Act
        result = extract_device_id(topic, message_key, payload_device_id)
        # Assert
        assert result == "33333"

    def test_all_none_returns_none(self):
        """1.1.1 (1.1.2): すべての入力がNoneの場合、Noneが返される

        実行内容: topic=None, key=None, payload_device_id=None
        想定結果: None が返される
        """
        from pipeline.silver.functions.device_id_extraction import extract_device_id
        # Arrange
        topic = None
        message_key = None
        payload_device_id = None
        # Act
        result = extract_device_id(topic, message_key, payload_device_id)
        # Assert
        assert result is None

    def test_empty_payload_device_id_returns_none(self):
        """1.1.1 (1.1.1): topic/key無効かつpayload_device_idが空文字の場合、Noneが返される

        実行内容: topic=None, key=None, payload_device_id=""
        想定結果: None が返される（空文字はフォールバックに使用しない）
        """
        from pipeline.silver.functions.device_id_extraction import extract_device_id
        # Arrange
        topic = None
        message_key = None
        payload_device_id = ""
        # Act
        result = extract_device_id(topic, message_key, payload_device_id)
        # Assert
        assert result is None

    def test_whitespace_payload_device_id_returns_none(self):
        """1.1.1 (1.1.4): topic/key無効かつpayload_device_idが空白のみの場合、Noneが返される

        実行内容: topic=None, key=None, payload_device_id="   "
        想定結果: None が返される
        """
        from pipeline.silver.functions.device_id_extraction import extract_device_id
        # Arrange
        topic = None
        message_key = None
        payload_device_id = "   "
        # Act
        result = extract_device_id(topic, message_key, payload_device_id)
        # Assert
        assert result is None


# ===========================================================================
# STEP 1.6: フォーマット判定 — JSON判定
# 設計書: § バイナリ/JSON判定・変換処理 > フォーマット判定ロジック
# ===========================================================================

@pytest.mark.unit
class TestIsValidJson:
    """文字列が有効なJSONかどうかを判定する

    観点: データ変換仕様 > バイナリ/JSON判定・変換処理 > フォーマット判定ロジック
    対応観点表: 2.1 正常系処理, 1.1.1 必須チェック, 1.1.6 不整値チェック

    設計書定義:
        - None → False
        - json.loads が成功 → True
        - JSONDecodeError / TypeError → False
    """

    def test_valid_json_object_returns_true(self):
        """2.1.1: 有効なJSONオブジェクト文字列の場合、Trueが返される

        実行内容: テレメトリデータJSON文字列を入力
        想定結果: True が返される
        """
        from pipeline.silver.functions.json_telemetry import is_valid_json
        # Arrange
        data = '{"device_id": 12345, "event_timestamp": "2026-01-23T10:30:00.000Z", "external_temp": 25.5}'
        # Act
        result = is_valid_json(data)
        # Assert
        assert result is True

    def test_valid_json_array_returns_true(self):
        """2.1.1: 有効なJSON配列文字列の場合、Trueが返される

        実行内容: data = '[1, 2, 3]'
        想定結果: True が返される
        """
        from pipeline.silver.functions.json_telemetry import is_valid_json
        # Arrange
        data = "[1, 2, 3]"
        # Act
        result = is_valid_json(data)
        # Assert
        assert result is True

    def test_none_returns_false(self):
        """1.1.1 (1.1.2): Noneが渡された場合、Falseが返される

        実行内容: data = None
        想定結果: False が返される
        """
        from pipeline.silver.functions.json_telemetry import is_valid_json
        # Arrange
        data = None
        # Act
        result = is_valid_json(data)
        # Assert
        assert result is False

    def test_empty_string_returns_false(self):
        """1.1.1 (1.1.1): 空文字が渡された場合、Falseが返される

        実行内容: data = ""
        想定結果: False が返される
        """
        from pipeline.silver.functions.json_telemetry import is_valid_json
        # Arrange
        data = ""
        # Act
        result = is_valid_json(data)
        # Assert
        assert result is False

    def test_invalid_json_string_returns_false(self):
        """1.1.6 (1.6.2): 無効なJSON文字列の場合、Falseが返される

        実行内容: data = "{invalid json}"（JSONDecodeError発生）
        想定結果: False が返される
        """
        from pipeline.silver.functions.json_telemetry import is_valid_json
        # Arrange
        data = "{invalid json}"
        # Act
        result = is_valid_json(data)
        # Assert
        assert result is False

    def test_plain_text_returns_false(self):
        """1.1.6 (1.6.2): JSON形式でない平文の場合、Falseが返される

        実行内容: data = "hello world"
        想定結果: False が返される
        """
        from pipeline.silver.functions.json_telemetry import is_valid_json
        # Arrange
        data = "hello world"
        # Act
        result = is_valid_json(data)
        # Assert
        assert result is False


# ===========================================================================
# STEP 1.6: フォーマット変換 — バイナリ→JSON変換
# 設計書: § バイナリ/JSON判定・変換処理 > バイナリ→JSON変換処理
# ===========================================================================

@pytest.mark.unit
class TestParseBinaryTelemetry:
    """バイナリ形式のテレメトリデータをJSON文字列に変換する

    観点: データ変換仕様 > バイナリ/JSON判定・変換処理 > バイナリ→JSON変換処理
    対応観点表: 2.1 正常系処理, 1.1.1 必須チェック, 1.3 エラーハンドリング

    設計書定義（バイナリフォーマット）:
        リトルエンディアン '<iq22d'
        device_id (INT32, 4B) + event_timestamp (INT64, 8B, ms) + センサー値22個 (FLOAT64×22, 176B)
        合計 188バイト
        NaN値は null として出力
    """

    def test_valid_188byte_binary_returns_json(self):
        """2.1.1: 188バイトの正常なバイナリデータの場合、JSON文字列が返される

        実行内容: 正常な188バイトのバイナリデータを入力
        想定結果: JSON文字列が返される（device_id/event_timestamp含む）
        """
        from pipeline.silver.functions.json_telemetry import parse_binary_telemetry
        # Arrange
        binary_data = _make_binary_telemetry(device_id=12345)
        # Act
        result = parse_binary_telemetry(binary_data)
        # Assert
        assert result is not None
        parsed = json.loads(result)
        assert "device_id" in parsed
        assert "event_timestamp" in parsed

    def test_valid_binary_contains_all_22_sensor_fields(self):
        """2.1.2: 変換結果に22個のセンサーフィールドが含まれる

        実行内容: 正常な188バイトのバイナリデータを入力
        想定結果: 設計書定義の全22センサーフィールドがJSONに含まれる
        """
        from pipeline.silver.functions.json_telemetry import parse_binary_telemetry
        # Arrange
        binary_data = _make_binary_telemetry()
        expected_fields = [
            "external_temp", "set_temp_freezer_1", "internal_sensor_temp_freezer_1",
            "internal_temp_freezer_1", "df_temp_freezer_1", "condensing_temp_freezer_1",
            "adjusted_internal_temp_freezer_1", "set_temp_freezer_2",
            "internal_sensor_temp_freezer_2", "internal_temp_freezer_2",
            "df_temp_freezer_2", "condensing_temp_freezer_2",
            "adjusted_internal_temp_freezer_2", "compressor_freezer_1",
            "compressor_freezer_2", "fan_motor_1", "fan_motor_2", "fan_motor_3",
            "fan_motor_4", "fan_motor_5", "defrost_heater_output_1",
            "defrost_heater_output_2",
        ]
        # Act
        result = parse_binary_telemetry(binary_data)
        # Assert
        parsed = json.loads(result)
        for field in expected_fields:
            assert field in parsed, f"センサーフィールド '{field}' がJSONに含まれていない"

    def test_none_binary_returns_none(self):
        """1.1.1 (1.1.2): Noneが渡された場合、Noneが返される

        実行内容: binary_data = None
        想定結果: None が返される
        """
        from pipeline.silver.functions.json_telemetry import parse_binary_telemetry
        # Arrange
        binary_data = None
        # Act
        result = parse_binary_telemetry(binary_data)
        # Assert
        assert result is None

    def test_wrong_size_binary_returns_none(self):
        """1.3.1: 188バイトでないバイナリの場合、Noneが返される

        実行内容: 100バイトのバイナリデータを入力（バイナリフォーマット不整合）
        想定結果: None が返される（サイズ検証失敗）
        """
        from pipeline.silver.functions.json_telemetry import parse_binary_telemetry
        # Arrange
        binary_data = b"\x00" * 100
        # Act
        result = parse_binary_telemetry(binary_data)
        # Assert
        assert result is None

    def test_empty_bytes_returns_none(self):
        """1.3.1: 空バイト列が渡された場合、Noneが返される

        実行内容: binary_data = b"" （0バイト）
        想定結果: None が返される
        """
        from pipeline.silver.functions.json_telemetry import parse_binary_telemetry
        # Arrange
        binary_data = b""
        # Act
        result = parse_binary_telemetry(binary_data)
        # Assert
        assert result is None

    def test_override_device_id_overwrites_binary_device_id(self):
        """2.1.1: override_device_idが指定された場合、バイナリ内のdevice_idが上書きされる

        実行内容: device_id=99999のバイナリとoverride_device_id="11111"を入力
        想定結果: 返却JSONのdevice_idが"11111"で上書きされる（設計書 §デバイスIDの上書き）
        """
        from pipeline.silver.functions.json_telemetry import parse_binary_telemetry
        # Arrange
        binary_data = _make_binary_telemetry(device_id=99999)
        override_device_id = "11111"
        # Act
        result = parse_binary_telemetry(binary_data, override_device_id)
        # Assert
        assert result is not None
        parsed = json.loads(result)
        assert str(parsed["device_id"]) == "11111"

    def test_no_override_uses_binary_device_id_as_string(self):
        """2.1.1: override_device_idがNoneの場合、バイナリのdevice_idが文字列化して使用される

        実行内容: device_id=12345のバイナリとoverride_device_id=Noneを入力
        想定結果: 返却JSONのdevice_idが"12345"（文字列）になる
        """
        from pipeline.silver.functions.json_telemetry import parse_binary_telemetry
        # Arrange
        binary_data = _make_binary_telemetry(device_id=12345)
        # Act
        result = parse_binary_telemetry(binary_data, None)
        # Assert
        assert result is not None
        parsed = json.loads(result)
        assert str(parsed["device_id"]) == "12345"

    def test_event_timestamp_is_iso8601_utc_format(self):
        """2.1.1: 変換結果のevent_timestampがISO 8601形式（UTC）になる

        実行内容: event_timestamp_ms = 1737624600000 (2026-01-23T10:30:00 UTC)
        想定結果: "2026-01-23T10:30:00.000Z" 形式のタイムスタンプが返される
        """
        from pipeline.silver.functions.json_telemetry import parse_binary_telemetry
        # Arrange
        binary_data = _make_binary_telemetry(event_timestamp_ms=1737624600000)
        # Act
        result = parse_binary_telemetry(binary_data)
        # Assert
        assert result is not None
        parsed = json.loads(result)
        assert parsed["event_timestamp"] == "2026-01-23T10:30:00.000Z"

    def test_nan_sensor_value_converted_to_none(self):
        """2.1.1: センサー値がNaNの場合、nullとして格納される

        実行内容: NaN値を含む188バイトのバイナリデータを入力
        想定結果: 該当フィールドの値がnullになる（設計書定義「NaN値はnullとして扱う」）
        """
        from pipeline.silver.functions.json_telemetry import parse_binary_telemetry
        import math
        # Arrange
        sensor_values = [float("nan")] + [25.5] * 21
        binary_data = _make_binary_telemetry(sensor_values=sensor_values)
        # Act
        result = parse_binary_telemetry(binary_data)
        # Assert
        assert result is not None
        parsed = json.loads(result)
        assert parsed["external_temp"] is None


# ===========================================================================
# STEP 1.6: フォーマット変換 — JSON device_id上書き
# 設計書: § バイナリ/JSON判定・変換処理 > JSON形式へのデバイスID上書き処理
# ===========================================================================

@pytest.mark.unit
class TestUpdateJsonDeviceId:
    """JSON文字列内のdevice_idを上書きする

    観点: データ変換仕様 > バイナリ/JSON判定・変換処理 > JSON形式へのデバイスID上書き処理
    対応観点表: 2.1 正常系処理, 1.1.1 必須チェック, 1.3 エラーハンドリング, 2.3 副作用チェック

    設計書定義:
        - json_str=None → None
        - override_device_id=None → json_strをそのまま返す
        - 正常 → data["device_id"] = str(override_device_id) で上書き
        - JSONDecodeError/TypeError/ValueError → json_strをそのまま返す
    """

    def test_valid_json_and_override_id_updates_device_id(self):
        """2.1.1 / 3.3.2.1: 有効なJSONとoverride_device_idの場合、device_idが更新される

        実行内容: device_id=99999のJSONとoverride_device_id="12345"を入力
        想定結果: JSONのdevice_idが"12345"（str）に更新される
        """
        from pipeline.silver.functions.json_telemetry import update_json_device_id
        # Arrange
        json_str = json.dumps({"device_id": 99999, "event_timestamp": "2026-01-23T10:30:00.000Z"})
        override_device_id = "12345"
        # Act
        result = update_json_device_id(json_str, override_device_id)
        # Assert
        assert result is not None
        parsed = json.loads(result)
        assert str(parsed["device_id"]) == "12345"

    def test_none_json_str_returns_none(self):
        """1.1.1 (1.1.2): json_strがNoneの場合、Noneが返される

        実行内容: json_str=None, override_device_id="12345"
        想定結果: None が返される
        """
        from pipeline.silver.functions.json_telemetry import update_json_device_id
        # Arrange
        json_str = None
        override_device_id = "12345"
        # Act
        result = update_json_device_id(json_str, override_device_id)
        # Assert
        assert result is None

    def test_none_override_id_returns_original_json(self):
        """2.1.1: override_device_idがNoneの場合、元のJSON文字列がそのまま返される

        実行内容: 有効なjson_strとoverride_device_id=None
        想定結果: 元のjson_strがそのまま返される
        """
        from pipeline.silver.functions.json_telemetry import update_json_device_id
        # Arrange
        json_str = json.dumps({"device_id": 99999, "event_timestamp": "2026-01-23T10:30:00.000Z"})
        override_device_id = None
        # Act
        result = update_json_device_id(json_str, override_device_id)
        # Assert
        assert result == json_str

    def test_invalid_json_str_returns_original_string(self):
        """1.3.1: json_strが無効なJSONの場合、元の文字列がそのまま返される（例外を伝播させない）

        実行内容: 無効なjson_strとoverride_device_id="12345"を入力
        想定結果: 元の文字列がそのまま返される（JSONDecodeErrorをキャッチして継続）
        """
        from pipeline.silver.functions.json_telemetry import update_json_device_id
        # Arrange
        json_str = "{invalid json}"
        override_device_id = "12345"
        # Act
        result = update_json_device_id(json_str, override_device_id)
        # Assert
        assert result == json_str

    def test_other_fields_preserved_after_device_id_update(self):
        """2.3.1: device_id更新後、その他のフィールドが保持される

        実行内容: 複数フィールドを持つJSONとoverride_device_idを入力
        想定結果: device_id以外のフィールドが変更されずに保持される（副作用なし）
        """
        from pipeline.silver.functions.json_telemetry import update_json_device_id
        # Arrange
        original = {
            "device_id": 99999,
            "event_timestamp": "2026-01-23T10:30:00.000Z",
            "external_temp": 25.5,
            "internal_temp_freezer_1": -19.5,
        }
        json_str = json.dumps(original)
        override_device_id = "12345"
        # Act
        result = update_json_device_id(json_str, override_device_id)
        # Assert
        parsed = json.loads(result)
        assert str(parsed["device_id"]) == "12345"
        assert parsed["event_timestamp"] == "2026-01-23T10:30:00.000Z"
        assert parsed["external_temp"] == 25.5
        assert parsed["internal_temp_freezer_1"] == -19.5


# ===========================================================================
# STEP 1.6: フォーマット変換 — 統合処理
# 設計書: § バイナリ/JSON判定・変換処理 > フォーマット判定・変換の統合処理
# ===========================================================================

@pytest.mark.unit
class TestConvertToJsonWithDeviceId:
    """テレメトリデータをJSON形式に変換し、デバイスIDを設定する統合処理

    観点: データ変換仕様 > バイナリ/JSON判定・変換処理 > フォーマット判定・変換の統合処理
    対応観点表: 2.1 正常系処理, 1.1.1 必須チェック, 1.3 エラーハンドリング

    設計書定義（処理フロー）:
        1. raw_value を UTF-8デコード試行
        2. JSON形式ならdevice_idを上書きして返却
        3. JSON形式でなければバイナリとしてパースしてJSON変換
        4. 変換失敗時は None を返す
    """

    def test_none_raw_value_returns_none(self):
        """1.1.1 (1.1.2): raw_valueがNoneの場合、Noneが返される

        実行内容: raw_value=None, override_device_id="12345"
        想定結果: None が返される
        """
        from pipeline.silver.functions.json_telemetry import convert_to_json_with_device_id
        # Arrange
        raw_value = None
        override_device_id = "12345"
        # Act
        result = convert_to_json_with_device_id(raw_value, override_device_id)
        # Assert
        assert result is None

    def test_valid_json_utf8_bytes_returns_updated_json(self):
        """2.1.1: UTF-8エンコードされた有効なJSONバイト列の場合、device_idが更新されたJSONが返される

        実行内容: テレメトリデータJSONのバイト列とoverride_device_id="12345"を入力
        想定結果: device_idが上書きされたJSON文字列が返される（処理フロー step2）
        """
        from pipeline.silver.functions.json_telemetry import convert_to_json_with_device_id
        # Arrange
        payload = {
            "device_id": 99999,
            "event_timestamp": "2026-01-23T10:30:00.000Z",
            "external_temp": 25.5,
        }
        raw_value = json.dumps(payload).encode("utf-8")
        override_device_id = "12345"
        # Act
        result = convert_to_json_with_device_id(raw_value, override_device_id)
        # Assert
        assert result is not None
        parsed = json.loads(result)
        assert str(parsed["device_id"]) == "12345"

    def test_binary_format_data_returns_converted_json(self):
        """2.1.1: 188バイトのバイナリ形式データの場合、JSON変換されたデータが返される

        実行内容: 188バイトのバイナリテレメトリデータを入力（処理フロー step3）
        想定結果: JSON文字列が返される（device_id/event_timestamp含む）
        """
        from pipeline.silver.functions.json_telemetry import convert_to_json_with_device_id
        # Arrange
        raw_value = _make_binary_telemetry(device_id=12345)
        override_device_id = "12345"
        # Act
        result = convert_to_json_with_device_id(raw_value, override_device_id)
        # Assert
        assert result is not None
        parsed = json.loads(result)
        assert "device_id" in parsed
        assert "event_timestamp" in parsed

    def test_invalid_data_returns_none(self):
        """1.3.1: UTF-8デコード失敗かつバイナリパース失敗の場合、Noneが返される

        実行内容: 3バイトの不正バイナリデータを入力（188バイト未満）
        想定結果: None が返される（変換エラー時はレコード破棄）
        """
        from pipeline.silver.functions.json_telemetry import convert_to_json_with_device_id
        # Arrange
        raw_value = b"\xFF\xFE\xFD"
        override_device_id = "12345"
        # Act
        result = convert_to_json_with_device_id(raw_value, override_device_id)
        # Assert
        assert result is None

    def test_json_bytes_without_override_keeps_original_device_id(self):
        """2.1.1: override_device_idがNoneの場合、元のJSONのdevice_idが保持される

        実行内容: 有効なJSONバイト列とoverride_device_id=Noneを入力
        想定結果: 元のdevice_idが保持されたJSON文字列が返される
        """
        from pipeline.silver.functions.json_telemetry import convert_to_json_with_device_id
        # Arrange
        payload = {"device_id": 99999, "event_timestamp": "2026-01-23T10:30:00.000Z"}
        raw_value = json.dumps(payload).encode("utf-8")
        override_device_id = None
        # Act
        result = convert_to_json_with_device_id(raw_value, override_device_id)
        # Assert
        assert result is not None
        parsed = json.loads(result)
        assert parsed["device_id"] == 99999


# ===========================================================================
# STEP 4: アラート判定 — 更新パターン判定
# 設計書: § アラート処理仕様 > 異常状態テーブル更新処理
# ===========================================================================

@pytest.mark.unit
class TestDetermineUpdatePattern:
    """閾値超過フラグとアラート発報フラグから異常状態テーブルの更新パターンを判定する

    観点: アラート処理仕様 > 異常状態テーブル更新処理
    対応観点表: 2.1 正常系処理, 1.1.6 不整値チェック

    設計書定義（更新パターン）:
        "recovery"       - threshold_exceeded=False（復旧: 状態リセット）
        "alert_fired"    - threshold_exceeded=True AND alert_triggered=True（アラート発報）
        "abnormal_start" - threshold_exceeded=True AND alert_triggered=False（新規異常開始/継続）
    """

    def test_threshold_not_exceeded_returns_recovery(self):
        """2.1.1: 閾値超過なし（正常値）の場合、"recovery"が返される

        実行内容: threshold_exceeded=False, alert_triggered=False
        想定結果: "recovery" が返される（正常状態への復旧処理）
        """
        from pipeline.silver.functions.alert_judgment import determine_update_pattern
        # Arrange
        threshold_exceeded = False
        alert_triggered = False
        # Act
        result = determine_update_pattern(threshold_exceeded, alert_triggered)
        # Assert
        assert result == "recovery"

    def test_threshold_not_exceeded_alert_triggered_true_still_returns_recovery(self):
        """2.1.1: 閾値超過なしの場合、alert_triggeredの値に関わらず"recovery"が返される

        実行内容: threshold_exceeded=False, alert_triggered=True
        想定結果: "recovery" が返される（閾値超過なしが最優先条件）
        """
        from pipeline.silver.functions.alert_judgment import determine_update_pattern
        # Arrange
        threshold_exceeded = False
        alert_triggered = True
        # Act
        result = determine_update_pattern(threshold_exceeded, alert_triggered)
        # Assert
        assert result == "recovery"

    def test_threshold_exceeded_and_alert_triggered_returns_alert_fired(self):
        """2.1.1: 閾値超過かつアラート発報条件成立の場合、"alert_fired"が返される

        実行内容: threshold_exceeded=True, alert_triggered=True
        想定結果: "alert_fired" が返される（alert_fired_time=NOW()更新処理）
        """
        from pipeline.silver.functions.alert_judgment import determine_update_pattern
        # Arrange
        threshold_exceeded = True
        alert_triggered = True
        # Act
        result = determine_update_pattern(threshold_exceeded, alert_triggered)
        # Assert
        assert result == "alert_fired"

    def test_threshold_exceeded_and_not_alert_triggered_returns_abnormal_start(self):
        """2.1.1: 閾値超過かつアラート未発報の場合、"abnormal_start"が返される

        実行内容: threshold_exceeded=True, alert_triggered=False
        想定結果: "abnormal_start" が返される（新規異常開始または異常継続処理）
        """
        from pipeline.silver.functions.alert_judgment import determine_update_pattern
        # Arrange
        threshold_exceeded = True
        alert_triggered = False
        # Act
        result = determine_update_pattern(threshold_exceeded, alert_triggered)
        # Assert
        assert result == "abnormal_start"

    def test_all_combinations_return_valid_pattern(self):
        """1.1.6 (1.6.1): 全4通りの入力組み合わせで戻り値が定義済みパターンのいずれかになる

        実行内容: (False,False), (False,True), (True,False), (True,True) の4通りを検証
        想定結果: 全パターンが "recovery"/"alert_fired"/"abnormal_start" のいずれか
        """
        from pipeline.silver.functions.alert_judgment import determine_update_pattern
        # Arrange
        valid_patterns = {"recovery", "alert_fired", "abnormal_start"}
        test_cases = [(False, False), (False, True), (True, False), (True, True)]
        # Act & Assert
        for threshold_exceeded, alert_triggered in test_cases:
            result = determine_update_pattern(threshold_exceeded, alert_triggered)
            assert result in valid_patterns, (
                f"threshold_exceeded={threshold_exceeded}, alert_triggered={alert_triggered} で "
                f"未定義パターン '{result}' が返された"
            )


# ===========================================================================
# STEP 4: アラート判定 — メール送信条件判定
# 設計書: § 外部連携仕様 > メール送信キュー登録処理 > キュー登録の設計方針
# ===========================================================================

@pytest.mark.unit
class TestShouldEnqueueEmail:
    """メール送信キュー登録の対象かどうかを判定する

    観点: 外部連携仕様 > メール送信キュー登録処理
    対応観点表: 2.1 正常系処理, 1.1.1 必須チェック

    設計書定義（登録条件）:
        alert_email_flag=TRUE かつ alert_triggered=TRUE の場合のみ登録
    """

    def test_both_true_returns_true(self):
        """2.1.1: alert_triggeredとalert_email_flagがともにTrueの場合、Trueが返される

        実行内容: alert_triggered=True, alert_email_flag=True
        想定結果: True が返される（メール送信キューへ登録する）
        """
        from pipeline.silver.functions.alert_judgment import should_enqueue_email
        # Arrange
        alert_triggered = True
        alert_email_flag = True
        # Act
        result = should_enqueue_email(alert_triggered, alert_email_flag)
        # Assert
        assert result is True

    def test_alert_triggered_false_returns_false(self):
        """2.1.1: alert_triggered=Falseの場合、Falseが返される

        実行内容: alert_triggered=False, alert_email_flag=True
        想定結果: False が返される（アラート未発報のためキュー登録しない）
        """
        from pipeline.silver.functions.alert_judgment import should_enqueue_email
        # Arrange
        alert_triggered = False
        alert_email_flag = True
        # Act
        result = should_enqueue_email(alert_triggered, alert_email_flag)
        # Assert
        assert result is False

    def test_alert_email_flag_false_returns_false(self):
        """2.1.1: alert_email_flag=Falseの場合、Falseが返される

        実行内容: alert_triggered=True, alert_email_flag=False
        想定結果: False が返される（メール通知設定がOFFのためキュー登録しない）
        """
        from pipeline.silver.functions.alert_judgment import should_enqueue_email
        # Arrange
        alert_triggered = True
        alert_email_flag = False
        # Act
        result = should_enqueue_email(alert_triggered, alert_email_flag)
        # Assert
        assert result is False

    def test_both_false_returns_false(self):
        """2.1.1: 両方Falseの場合、Falseが返される

        実行内容: alert_triggered=False, alert_email_flag=False
        想定結果: False が返される
        """
        from pipeline.silver.functions.alert_judgment import should_enqueue_email
        # Arrange
        alert_triggered = False
        alert_email_flag = False
        # Act
        result = should_enqueue_email(alert_triggered, alert_email_flag)
        # Assert
        assert result is False

    def test_none_alert_triggered_returns_false(self):
        """1.1.1 (1.1.2): alert_triggered=Noneの場合、Falseが返される

        実行内容: alert_triggered=None, alert_email_flag=True
        想定結果: False が返される（None is True → False）
        """
        from pipeline.silver.functions.alert_judgment import should_enqueue_email
        # Arrange
        alert_triggered = None
        alert_email_flag = True
        # Act
        result = should_enqueue_email(alert_triggered, alert_email_flag)
        # Assert
        assert result is False

    def test_none_alert_email_flag_returns_false(self):
        """1.1.1 (1.1.2): alert_email_flag=Noneの場合、Falseが返される

        実行内容: alert_triggered=True, alert_email_flag=None
        想定結果: False が返される（None is True → False）
        """
        from pipeline.silver.functions.alert_judgment import should_enqueue_email
        # Arrange
        alert_triggered = True
        alert_email_flag = None
        # Act
        result = should_enqueue_email(alert_triggered, alert_email_flag)
        # Assert
        assert result is False


# ===========================================================================
# OLTP接続 — リトライ判定
# 設計書: § 外部連携仕様 > OLTPリトライ戦略
# ===========================================================================

@pytest.mark.unit
class TestIsRetryableError:
    """リトライ可能なエラーかどうかを判定する

    観点: 外部連携仕様 > OLTPリトライ戦略
    対応観点表: 1.3 エラーハンドリング, 2.1 正常系処理

    設計書定義（リトライ対象）:
        ○ socket.timeout, ConnectionResetError, BrokenPipeError, OSError
        ○ pymysql.err.OperationalError (errno: 2003, 2006, 2013)
        × pymysql.err.OperationalError (errno: 1045 認証エラー)
        × pymysql.err.ProgrammingError (SQLエラー)
        × pymysql.err.IntegrityError  (制約違反)
        × その他の例外 (ValueError, RuntimeError 等)
    """

    def test_socket_timeout_is_retryable(self):
        """1.3.1: socket.timeoutはリトライ対象である

        実行内容: socket.timeout 例外を入力
        想定結果: True が返される（接続タイムアウト → リトライ）
        """
        from pipeline.silver.functions.mysql_connector import is_retryable_error
        # Arrange
        error = socket.timeout("Connection timed out")
        # Act
        result = is_retryable_error(error)
        # Assert
        assert result is True

    def test_connection_reset_error_is_retryable(self):
        """1.3.1: ConnectionResetErrorはリトライ対象である

        実行内容: ConnectionResetError 例外を入力
        想定結果: True が返される（一時的なネットワークエラー → リトライ）
        """
        from pipeline.silver.functions.mysql_connector import is_retryable_error
        # Arrange
        error = ConnectionResetError("Connection reset by peer")
        # Act
        result = is_retryable_error(error)
        # Assert
        assert result is True

    def test_broken_pipe_error_is_retryable(self):
        """1.3.1: BrokenPipeErrorはリトライ対象である

        実行内容: BrokenPipeError 例外を入力
        想定結果: True が返される（一時的なネットワークエラー → リトライ）
        """
        from pipeline.silver.functions.mysql_connector import is_retryable_error
        # Arrange
        error = BrokenPipeError("Broken pipe")
        # Act
        result = is_retryable_error(error)
        # Assert
        assert result is True

    def test_os_error_is_retryable(self):
        """1.3.1: OSErrorはリトライ対象である

        実行内容: OSError 例外を入力
        想定結果: True が返される（一時的なネットワークエラー → リトライ）
        """
        from pipeline.silver.functions.mysql_connector import is_retryable_error
        # Arrange
        error = OSError("Network unreachable")
        # Act
        result = is_retryable_error(error)
        # Assert
        assert result is True

    def test_mysql_operational_error_2003_is_retryable(self):
        """1.3.1: MySQLエラーコード2003(接続不可)はリトライ対象である

        実行内容: pymysql.err.OperationalError(2003) を入力
        想定結果: True が返される（errno=2003: Can't connect to MySQL server）
        """
        import pymysql
        from pipeline.silver.functions.mysql_connector import is_retryable_error
        # Arrange
        error = pymysql.err.OperationalError(2003, "Can't connect to MySQL server")
        # Act
        result = is_retryable_error(error)
        # Assert
        assert result is True

    def test_mysql_operational_error_2006_is_retryable(self):
        """1.3.1: MySQLエラーコード2006(サーバー切断)はリトライ対象である

        実行内容: pymysql.err.OperationalError(2006) を入力
        想定結果: True が返される（errno=2006: MySQL server has gone away）
        """
        import pymysql
        from pipeline.silver.functions.mysql_connector import is_retryable_error
        # Arrange
        error = pymysql.err.OperationalError(2006, "MySQL server has gone away")
        # Act
        result = is_retryable_error(error)
        # Assert
        assert result is True

    def test_mysql_operational_error_2013_is_retryable(self):
        """1.3.1: MySQLエラーコード2013(クエリ中切断)はリトライ対象である

        実行内容: pymysql.err.OperationalError(2013) を入力
        想定結果: True が返される（errno=2013: Lost connection to MySQL server during query）
        """
        import pymysql
        from pipeline.silver.functions.mysql_connector import is_retryable_error
        # Arrange
        error = pymysql.err.OperationalError(2013, "Lost connection to MySQL server during query")
        # Act
        result = is_retryable_error(error)
        # Assert
        assert result is True

    def test_mysql_operational_error_1045_is_not_retryable(self):
        """1.3.4: MySQLエラーコード1045(認証エラー)はリトライ対象外である

        実行内容: pymysql.err.OperationalError(1045) を入力
        想定結果: False が返される（errno=1045: Access denied → リトライ不可）
        """
        import pymysql
        from pipeline.silver.functions.mysql_connector import is_retryable_error
        # Arrange
        error = pymysql.err.OperationalError(1045, "Access denied for user")
        # Act
        result = is_retryable_error(error)
        # Assert
        assert result is False

    def test_mysql_programming_error_is_not_retryable(self):
        """1.3.6: ProgrammingError(SQLエラー)はリトライ対象外である

        実行内容: pymysql.err.ProgrammingError を入力
        想定結果: False が返される（SQL構文エラー → リトライ不可）
        """
        import pymysql
        from pipeline.silver.functions.mysql_connector import is_retryable_error
        # Arrange
        error = pymysql.err.ProgrammingError(1064, "SQL syntax error")
        # Act
        result = is_retryable_error(error)
        # Assert
        assert result is False

    def test_mysql_integrity_error_is_not_retryable(self):
        """1.3.6: IntegrityError(制約違反)はリトライ対象外である

        実行内容: pymysql.err.IntegrityError を入力
        想定結果: False が返される（制約違反 → リトライ不可）
        """
        import pymysql
        from pipeline.silver.functions.mysql_connector import is_retryable_error
        # Arrange
        error = pymysql.err.IntegrityError(1062, "Duplicate entry")
        # Act
        result = is_retryable_error(error)
        # Assert
        assert result is False

    def test_value_error_is_not_retryable(self):
        """1.3.6: ValueError はリトライ対象外である

        実行内容: ValueError 例外を入力
        想定結果: False が返される（一般的なPython例外 → リトライ不可）
        """
        from pipeline.silver.functions.mysql_connector import is_retryable_error
        # Arrange
        error = ValueError("Invalid value")
        # Act
        result = is_retryable_error(error)
        # Assert
        assert result is False
