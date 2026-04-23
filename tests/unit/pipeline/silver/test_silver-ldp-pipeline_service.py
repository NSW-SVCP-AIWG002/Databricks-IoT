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
import builtins
from unittest.mock import MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# テスト用ヘルパー
# ---------------------------------------------------------------------------

def _make_binary_telemetry(
    device_id: str = "test_device-id",
    event_timestamp_ms: int = 1737624600000,
    sensor_values: list = None,
) -> bytes:
    """188バイトのバイナリテレメトリデータを生成する。

    バイナリフォーマット（リトルエンディアン、設計書 § バイナリフォーマット定義）:
        <128s = device_id        (STRING, 128バイト)
        <q  = event_timestamp  (INT64,  8バイト, ミリ秒)
        <22d= センサー値22個   (FLOAT64×22, 176バイト)
    合計: 128 + 8 + 176 = 312バイト
    """
    if sensor_values is None:
        sensor_values = [
            25.5, -20.0, -19.8, -19.5, -15.2, 35.0, -19.7,
            -25.0, -24.6, -24.3, -18.5, 38.0, -24.5,
            2800.0, 3100.0, 1200.0, 1180.0, 1150.0, 1220.0, 1190.0,
            0.0, 0.0,
        ]
    return struct.pack("<128sq22d", device_id.encode(), event_timestamp_ms, *sensor_values)

# ---------------------------------------------------------------------------
# テスト用ヘルパー — Spark Row の dict アクセスをエミュレート
# ---------------------------------------------------------------------------

class _MockRow:
    """Spark Row の row["field"] アクセスをエミュレートするモック行オブジェクト"""
    def __init__(self, **kw):
        self._d = kw

    def __getitem__(self, k):
        return self._d[k]

# ===========================================================================
# STEP 1.5: デバイスID抽出 — MQTT Topic
# 設計書: § データ変換仕様 > デバイスID抽出処理 > MQTT TopicからのデバイスID抽出
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

    def test_single_digit_id_extracted_correctly(self):
        """2.1.1: 1桁の数値IDが正常に抽出される

        実行内容: topic = "/1/data/refrigerator"
        想定結果: "1" が返される（最小桁数の数値ID）
        """
        from pipeline.silver.functions.device_id_extraction import extract_device_id_from_topic
        # Arrange
        topic = "/1/data/refrigerator"
        # Act
        result = extract_device_id_from_topic(topic)
        # Assert
        assert result == "1"

    def test_large_device_id_extracted_correctly(self):
        """2.1.1: 大きな数値IDが正常に抽出される

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
        
    def test_void_device_id_extracted_correctly(self):
        """2.1.1: 空文字列のデバイスIDが正常に抽出される

        実行内容: topic = "//data/refrigerator"
        想定結果: None が返される
        """
        from pipeline.silver.functions.device_id_extraction import extract_device_id_from_topic
        # Arrange
        topic = "//data/refrigerator"
        # Act
        result = extract_device_id_from_topic(topic)
        # Assert
        assert result is None

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

    def test_empty_string_topic_returns_none(self):
        """1.1.1 (1.1.1): 空文字が渡された場合、Noneが返される

        実行内容: topic = ""（空文字列）
        想定結果: None が返される（正規表現に不一致）
        """
        from pipeline.silver.functions.device_id_extraction import extract_device_id_from_topic
        # Arrange
        topic = ""
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
        
    def test_string_device_id_returns_correctly(self):
        """2.1.1: 文字列IDが正常に抽出される

        実行内容: topic = "/abc/data/refrigerator"（IDが文字列）
        想定結果: "abc" が返される
        """
        from pipeline.silver.functions.device_id_extraction import extract_device_id_from_topic
        # Arrange
        topic = "/abc/data/refrigerator"
        # Act
        result = extract_device_id_from_topic(topic)
        # Assert
        assert result == "abc"

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

        実行内容: topic = "/0100100101101011010/data/refrigerator"
        想定結果: "0100100101101011010" が返される
        """
        from pipeline.silver.functions.device_id_extraction import extract_device_id_from_topic
        # Arrange
        topic = "/0100100101101011010/data/refrigerator"
        # Act
        result = extract_device_id_from_topic(topic)
        # Assert
        assert result == "0100100101101011010"


# ===========================================================================
# STEP 1.5: デバイスID抽出 — EventHub key
# 設計書: § データ変換仕様 > デバイスID抽出処理 > EventHub keyからのデバイスID抽出
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

    def test_large_numeric_key_returns_correctly(self):
        """2.1.1: 大きな数値keyが正常に返される

        実行内容: message_key = "9999999"
        想定結果: "9999999" が返される（大きな数値デバイスID）
        """
        from pipeline.silver.functions.device_id_extraction import extract_device_id_from_key
        # Arrange
        message_key = "9999999"
        # Act
        result = extract_device_id_from_key(message_key)
        # Assert
        assert result == "9999999"


# ===========================================================================
# STEP 1.5: デバイスID抽出 — 統合処理
# 設計書: § データ変換仕様 > デバイスID抽出処理 > デバイスID抽出の統合処理
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
        リトルエンディアン '<128sq22d'
        device_id (STRING, 128B) + event_timestamp (INT64, 8B, ms) + センサー値22個 (FLOAT64×22, 176B)
        合計 312バイト
        NaN値は null として出力
    """

    def test_valid_312byte_binary_returns_json(self):
        """2.1.1: 312バイトの正常なバイナリデータの場合、JSON文字列が返される

        実行内容: 正常な312バイトのバイナリデータを入力
        想定結果: JSON文字列が返される（device_id/event_timestamp含む）
        """
        from pipeline.silver.functions.json_telemetry import parse_binary_telemetry
        # Arrange
        binary_data = _make_binary_telemetry(device_id="test_device-id", event_timestamp_ms=1737624600000)
        # Act
        result = parse_binary_telemetry(binary_data)
        # Assert
        assert result is not None
        parsed = json.loads(result)
        assert "device_id" in parsed
        assert parsed["device_id"] == "test_device-id"
        assert "event_timestamp" in parsed
        assert parsed["event_timestamp"] == "2025-01-23T09:30:00.000Z"

    def test_valid_binary_contains_all_22_sensor_fields(self):
        """2.1.2: 変換結果に22個のセンサーフィールドが含まれる

        実行内容: 正常な312バイトのバイナリデータを入力
        想定結果: 設計書定義の全22センサーフィールドがJSONに含まれる
        """
        from pipeline.silver.functions.json_telemetry import parse_binary_telemetry
        # Arrange
        binary_data = _make_binary_telemetry(device_id="test_device-id", event_timestamp_ms=1737624600000)
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
        """1.3.1: 312バイトでないバイナリの場合、Noneが返される

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

        実行内容: device_id="99999"のバイナリとoverride_device_id="11111"を入力
        想定結果: 返却JSONのdevice_idが"11111"で上書きされる（設計書 §デバイスIDの上書き）
        """
        from pipeline.silver.functions.json_telemetry import parse_binary_telemetry
        # Arrange
        binary_data = _make_binary_telemetry(device_id="99999")
        override_device_id = "11111"
        # Act
        result = parse_binary_telemetry(binary_data, override_device_id)
        # Assert
        assert result is not None
        parsed = json.loads(result)
        assert str(parsed["device_id"]) == "11111"

    def test_no_override_uses_binary_device_id_as_string(self):
        """2.1.1: override_device_idがNoneの場合、バイナリのdevice_idが文字列化して使用される

        実行内容: device_id="12345"のバイナリとoverride_device_id=Noneを入力
        想定結果: 返却JSONのdevice_idが"12345"（文字列）になる
        """
        from pipeline.silver.functions.json_telemetry import parse_binary_telemetry
        # Arrange
        binary_data = _make_binary_telemetry(device_id="12345")
        # Act
        result = parse_binary_telemetry(binary_data, None)
        # Assert
        assert result is not None
        parsed = json.loads(result)
        assert str(parsed["device_id"]) == "12345"

    def test_event_timestamp_is_iso8601_utc_format(self):
        """2.1.1: 変換結果のevent_timestampがISO 8601形式（UTC）になる

        実行内容: event_timestamp_ms = 1737624600000 (2025-01-23T09:30:00 UTC)
        想定結果: "2025-01-23T09:30:00.000Z" 形式のタイムスタンプが返される
        """
        from pipeline.silver.functions.json_telemetry import parse_binary_telemetry
        # Arrange
        binary_data = _make_binary_telemetry(event_timestamp_ms=1737624600000)
        # Act
        result = parse_binary_telemetry(binary_data)
        # Assert
        assert result is not None
        parsed = json.loads(result)
        assert parsed["event_timestamp"] == "2025-01-23T09:30:00.000Z"

    def test_nan_sensor_value_converted_to_none(self):
        """2.1.1: センサー値がNaNの場合、nullとして格納される

        実行内容: NaN値を含む312バイトのバイナリデータを入力
        想定結果: 該当フィールドの値がnullになる（設計書定義「NaN値はnullとして扱う」）
        """
        from pipeline.silver.functions.json_telemetry import parse_binary_telemetry
        
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

        実行内容: device_id="test-device_id%"のJSONとoverride_device_id="12345"を入力
        想定結果: JSONのdevice_idが"12345"（str）に更新される
        """
        from pipeline.silver.functions.json_telemetry import update_json_device_id
        # Arrange
        json_str = json.dumps({"device_id": "test-device_id%", "event_timestamp": "2026-01-23T10:30:00.000Z"})
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
        json_str = json.dumps({"device_id": "test-device_id%", "event_timestamp": "2026-01-23T10:30:00.000Z"})
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
        
    def test_invalid_json_str_returns_original_string_2(self):
        """1.3.1: json_strが無効なJSONの場合、元の文字列がそのまま返される（例外を伝播させない）

        実行内容: override_device_id=""を入力
        想定結果: 元の文字列がそのまま返される（ValueErrorをキャッチして継続）
        """
        from pipeline.silver.functions.json_telemetry import update_json_device_id
        # Arrange
        json_str = json.dumps({"device_id": "test-device_id%", "event_timestamp": "2026-01-23T10:30:00.000Z"})
        override_device_id = ""
        # Act
        result = update_json_device_id(json_str, override_device_id)
        # Assert
        assert result == json_str
        
    def test_invalid_json_str_returns_original_string_3(self):
        """1.3.1: json_strが無効なJSONの場合、元の文字列がそのまま返される（例外を伝播させない）

        実行内容: override_device_id=[]を入力
        想定結果: 元の文字列がそのまま返される（TypeErrorをキャッチして継続）
        """
        from pipeline.silver.functions.json_telemetry import update_json_device_id
        # Arrange
        json_str = json.dumps({"device_id": "99999", "event_timestamp": "2026-01-23T10:30:00.000Z"})
        override_device_id = []
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
            "device_id": "99999",
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
            "device_id": "99999",
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
        payload = {"device_id": "99999", "event_timestamp": "2026-01-23T10:30:00.000Z"}
        raw_value = json.dumps(payload).encode("utf-8")
        override_device_id = None
        # Act
        result = convert_to_json_with_device_id(raw_value, override_device_id)
        # Assert
        assert result is not None
        parsed = json.loads(result)
        assert parsed["device_id"] == "99999"
        
# ===========================================================================
# アラート異常状態テーブル読み込み
# 設計書: § アラート処理仕様 > 異常状態テーブル取得処理
# ===========================================================================

@pytest.mark.unit
class TestGetAlertAbnormalState:
    """異常状態テーブルの読み込みとフォールバックを検証する

    観点: アラート処理仕様 > 異常状態テーブル取得処理
    対応観点表: 1.3 エラーハンドリング, 2.1 正常系処理

    設計書定義（alert_judgment.py L36-67）:
        - JDBC で alert_abnormal_state を読み込む
        - 派生カラム is_abnormal（abnormal_start_time IS NOT NULL）を付与
        - 派生カラム alert_fired（alert_fired_time IS NOT NULL）を付与
        - 例外発生時は空DataFrameを返す（フォールバック）
    """

    @patch.object(builtins, "spark")
    def test_exception_returns_empty_dataframe(self, mock_spark):
        """1.3.1: JDBC 読み込み失敗時は空DataFrameが返される

        実行内容: spark.read.format("jdbc").options().load() が例外を送出
        想定結果: spark.createDataFrame([], schema=...) が呼ばれ、空DFが返される
        """
        from pipeline.silver.functions.alert_judgment import get_alert_abnormal_state
        # Arrange
        mock_spark.read.format.return_value.options.return_value.load.side_effect = Exception("DB error")
        # Act
        get_alert_abnormal_state()
        # Assert
        mock_spark.createDataFrame.assert_called_once()
        call_args = mock_spark.createDataFrame.call_args[0]
        assert call_args[0] == []

    @patch.object(builtins, "spark")
    def test_success_adds_is_abnormal_and_alert_fired_columns(self, mock_spark):
        """2.1.1: 読み込み成功時に派生カラム is_abnormal と alert_fired が付与される

        実行内容: spark.read.format("jdbc").options().load() が mock_df を返す
        想定結果: df.withColumn("is_abnormal", ...) と df.withColumn("alert_fired", ...) が呼ばれる
        """
        from pipeline.silver.functions.alert_judgment import get_alert_abnormal_state
        # Arrange
        mock_df = MagicMock()
        mock_spark.read.format.return_value.options.return_value.load.return_value = mock_df
        # Act
        get_alert_abnormal_state()
        # Assert: 1回目の withColumn が "is_abnormal" で呼ばれた
        first_col = mock_df.withColumn.call_args_list[0][0][0]
        assert first_col == "is_abnormal", (
            f"1回目の withColumn が 'is_abnormal' でない: '{first_col}'"
        )
        # Assert: 2回目の withColumn が "alert_fired" で呼ばれた（withColumn.return_value 上）
        second_col = mock_df.withColumn.return_value.withColumn.call_args_list[0][0][0]
        assert second_col == "alert_fired", (
            f"2回目の withColumn が 'alert_fired' でない: '{second_col}'"
        )


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
        
# ===========================================================================
# STEP 5b: 異常状態テーブル更新
# 設計書: § アラート処理仕様 > 異常状態テーブル更新処理
# ===========================================================================

@pytest.mark.unit
class TestUpdateAlertAbnormalState:
    """異常状態テーブルの更新パターン別 SQL 実行を検証する（foreachBatch）

    観点: アラート処理仕様 > 異常状態テーブル更新処理
    対応観点表: 2.1 正常系処理, 2.3 副作用チェック

    設計書定義（更新パターン）:
        "recovery"       - threshold_exceeded=False → abnormal_start_time=NULL
        "alert_fired"    - threshold_exceeded=True, alert_triggered=True → alert_fired_time=NOW()
        "abnormal_start" - threshold_exceeded=True, alert_triggered=False → COALESCE(abnormal_start_time,...)
    """

    def _make_mock_conn(self):
        """MySQL接続・カーソルモックを生成するヘルパー"""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_conn.cursor.return_value.__exit__.return_value = False
        return mock_conn, mock_cursor

    def _make_mock_batch_df(self, records):
        """指定レコードを collect() で返す batch_df モックを生成するヘルパー"""
        mock_batch_df = MagicMock()
        mock_batch_df.alias.return_value.join.return_value.select.return_value.distinct.return_value.collect.return_value = records
        return mock_batch_df

    @patch("functions.alert_judgment.get_mysql_connection")
    def test_empty_collect_returns_without_db_call(self, mock_get_conn):
        """2.1.1: collect() が空の場合、DB接続なしで終了する

        実行内容: バッチの collect() が [] を返す
        想定結果: get_mysql_connection が呼ばれない（早期リターン）
        """
        from pipeline.silver.functions.alert_judgment import update_alert_abnormal_state
        # Arrange
        mock_batch_df = self._make_mock_batch_df([])
        # Act
        update_alert_abnormal_state(mock_batch_df, 0)
        # Assert
        mock_get_conn.assert_not_called()

    @patch("functions.alert_judgment.get_mysql_connection")
    def test_recovery_pattern_sql_executed(self, mock_get_conn):
        """2.1.1: threshold_exceeded=False の場合、復旧パターンの SQL が実行される

        実行内容: threshold_exceeded=False, alert_triggered=False のレコード
        想定結果: abnormal_start_time=NULL を含むSQL が実行され、conn.commit() が呼ばれる
        """
        from pipeline.silver.functions.alert_judgment import update_alert_abnormal_state
        # Arrange
        records = [_MockRow(
            device_id=1001, alert_id=5,
            threshold_exceeded=False, alert_triggered=False,
            current_sensor_value=25.0, event_timestamp="2026-01-23T09:00:00",
            abnormal_start_time=None,
        )]
        mock_batch_df = self._make_mock_batch_df(records)
        mock_conn, mock_cursor = self._make_mock_conn()
        mock_get_conn.return_value.__enter__.return_value = mock_conn
        mock_get_conn.return_value.__exit__.return_value = False
        # Act
        update_alert_abnormal_state(mock_batch_df, 0)
        # Assert
        sql_executed = mock_cursor.execute.call_args_list[0][0][0]
        assert "abnormal_start_time = NULL" in sql_executed, (
            f"recovery パターンの SQL に 'abnormal_start_time = NULL' が含まれていない"
        )
        mock_conn.commit.assert_called_once()

    @patch("functions.alert_judgment.get_mysql_connection")
    def test_alert_fired_pattern_sql_executed(self, mock_get_conn):
        """2.1.1: threshold_exceeded=True, alert_triggered=True の場合、発報パターンの SQL が実行される

        実行内容: threshold_exceeded=True, alert_triggered=True のレコード
        想定結果: alert_fired_time=NOW() を含むSQL が実行され、conn.commit() が呼ばれる
        """
        from pipeline.silver.functions.alert_judgment import update_alert_abnormal_state
        # Arrange
        records = [_MockRow(
            device_id=1001, alert_id=5,
            threshold_exceeded=True, alert_triggered=True,
            current_sensor_value=-30.0, event_timestamp="2026-01-23T09:00:00",
            abnormal_start_time="2026-01-23T08:00:00",
        )]
        mock_batch_df = self._make_mock_batch_df(records)
        mock_conn, mock_cursor = self._make_mock_conn()
        mock_get_conn.return_value.__enter__.return_value = mock_conn
        mock_get_conn.return_value.__exit__.return_value = False
        # Act
        update_alert_abnormal_state(mock_batch_df, 0)
        # Assert
        sql_executed = mock_cursor.execute.call_args_list[0][0][0]
        assert "alert_fired_time = NOW()" in sql_executed, (
            f"alert_fired パターンの SQL に 'alert_fired_time = NOW()' が含まれていない"
        )
        mock_conn.commit.assert_called_once()

    @patch("functions.alert_judgment.get_mysql_connection")
    def test_abnormal_start_pattern_sql_executed(self, mock_get_conn):
        """2.1.1: threshold_exceeded=True, alert_triggered=False の場合、異常開始パターンの SQL が実行される

        実行内容: threshold_exceeded=True, alert_triggered=False のレコード
        想定結果: COALESCE(abnormal_start_time,...) を含むSQL が実行され、conn.commit() が呼ばれる
        """
        from pipeline.silver.functions.alert_judgment import update_alert_abnormal_state
        # Arrange
        records = [_MockRow(
            device_id=1001, alert_id=5,
            threshold_exceeded=True, alert_triggered=False,
            current_sensor_value=-30.0, event_timestamp="2026-01-23T09:00:00",
            abnormal_start_time=None,
        )]
        mock_batch_df = self._make_mock_batch_df(records)
        mock_conn, mock_cursor = self._make_mock_conn()
        mock_get_conn.return_value.__enter__.return_value = mock_conn
        mock_get_conn.return_value.__exit__.return_value = False
        # Act
        update_alert_abnormal_state(mock_batch_df, 0)
        # Assert
        sql_executed = mock_cursor.execute.call_args_list[0][0][0]
        assert "COALESCE(abnormal_start_time," in sql_executed, (
            f"abnormal_start パターンの SQL に 'COALESCE(abnormal_start_time,' が含まれていない"
        )
        mock_conn.commit.assert_called_once()

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
        想定結果: False が返される（None は True ではないため False）
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
        想定結果: False が返される（None は True ではないため False）
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

# ===========================================================================
# OLTP接続 — get_mysql_connection コンテキストマネージャ
# 設計書: § 外部連携仕様 > OLTPリトライ戦略
# ===========================================================================

@pytest.mark.unit
class TestGetMysqlConnection:
    """リトライ付きMySQL接続コンテキストマネージャを検証する

    観点: 外部連携仕様 > OLTPリトライ戦略
    対応観点表: 2.1 正常系処理, 1.3 エラーハンドリング

    設計書定義（mysql_connector.py L49-85）:
        - range(OLTP_MAX_RETRIES + 1) = range(4) で最大4ループ
        - attempt < OLTP_MAX_RETRIES - 1 (= < 2) の場合のみ sleep してリトライ
        - attempt=2 で raise last_error（実質的な試行回数は 3 回）
    """

    @patch("functions.mysql_connector.time.sleep")
    @patch("functions.mysql_connector.get_mysql_config", return_value={})
    @patch("functions.mysql_connector.pymysql.connect")
    def test_success_on_first_attempt_yields_connection(self, mock_connect, mock_get_config, mock_sleep):
        """2.1.1: 1回目の接続成功で conn が yield される

        実行内容: pymysql.connect が mock_conn を返す
        想定結果: with ブロック内で conn = mock_conn が利用可能
        """
        from pipeline.silver.functions.mysql_connector import get_mysql_connection
        # Act & Assert
        with get_mysql_connection() as conn:
            assert conn is mock_connect.return_value

    @patch("functions.mysql_connector.time.sleep")
    @patch("functions.mysql_connector.get_mysql_config", return_value={})
    @patch("functions.mysql_connector.pymysql.connect")
    def test_connection_closed_after_successful_use(self, mock_connect, mock_get_config, mock_sleep):
        """2.1.1: 正常終了後 finally ブロックで conn.close() が1回呼ばれる

        実行内容: pymysql.connect が mock_conn を返し、with ブロックを正常終了
        想定結果: mock_conn.close() が1回呼ばれる（設計書 §接続クローズ保証）
        """
        from pipeline.silver.functions.mysql_connector import get_mysql_connection
        # Act
        with get_mysql_connection() as conn:
            pass
        # Assert
        mock_connect.return_value.close.assert_called_once()

    @patch("functions.mysql_connector.OLTP_RETRY_INTERVALS", [0.001, 0.001, 0.001])
    @patch("functions.mysql_connector.time.sleep")
    @patch("functions.mysql_connector.get_mysql_config", return_value={})
    @patch("functions.mysql_connector.pymysql.connect")
    def test_retries_on_retryable_error_then_succeeds(self, mock_connect, mock_get_config, mock_sleep):
        """1.3.1: 1回目失敗（接続エラー）後にリトライして2回目成功する

        実行内容: connect: side_effect=[OperationalError(2006), mock_conn]
        想定結果: time.sleep が1回呼ばれ、最終的に conn が返される
        """
        import pymysql
        from pipeline.silver.functions.mysql_connector import get_mysql_connection
        # Arrange
        mock_conn = MagicMock()
        mock_connect.side_effect = [
            pymysql.err.OperationalError(2006, "MySQL server has gone away"),
            mock_conn,
        ]
        # Act
        with get_mysql_connection() as conn:
            assert conn is mock_conn
        # Assert
        assert mock_sleep.call_count == 1

    @patch("functions.mysql_connector.OLTP_RETRY_INTERVALS", [0.001, 0.001, 0.001])
    @patch("functions.mysql_connector.time.sleep")
    @patch("functions.mysql_connector.get_mysql_config", return_value={})
    @patch("functions.mysql_connector.pymysql.connect")
    def test_raises_after_max_retries_exceeded(self, mock_connect, mock_get_config, mock_sleep):
        """1.3.1: 全試行失敗時は最後の例外が送出される

        実行内容: pymysql.connect が常に OperationalError(2006) を送出
        想定結果: pymysql.err.OperationalError が送出される（設計書 §最大リトライ超過）
        """
        import pymysql
        from pipeline.silver.functions.mysql_connector import get_mysql_connection
        # Arrange
        mock_connect.side_effect = pymysql.err.OperationalError(2006, "MySQL server has gone away")
        # Act & Assert
        with pytest.raises(pymysql.err.OperationalError):
            with get_mysql_connection() as conn:
                pass

    @patch("functions.mysql_connector.OLTP_RETRY_INTERVALS", [0.001, 0.001, 0.001])
    @patch("functions.mysql_connector.time.sleep")
    @patch("functions.mysql_connector.get_mysql_config", return_value={})
    @patch("functions.mysql_connector.pymysql.connect")
    def test_sleep_called_exactly_twice_on_three_failures(self, mock_connect, mock_get_config, mock_sleep):
        """1.3.1: 全試行失敗時 sleep は2回だけ呼ばれる

        実行内容: 全3試行（attempt 0, 1, 2）が全て失敗する
        想定結果: time.sleep が2回呼ばれる
            （attempt < OLTP_MAX_RETRIES - 1 = < 2 の場合のみ sleep: attempt 0, 1 のみ）
            （attempt 2 は即 raise last_error → sleep なし）
        """
        import pymysql
        from pipeline.silver.functions.mysql_connector import get_mysql_connection
        # Arrange
        mock_connect.side_effect = pymysql.err.OperationalError(2006, "MySQL server has gone away")
        # Act
        with pytest.raises(pymysql.err.OperationalError):
            with get_mysql_connection() as conn:
                pass
        # Assert
        assert mock_sleep.call_count == 2

# ===========================================================================
# STEP 5b: メール送信キュー登録
# 設計書: § 外部連携仕様 > メール送信キュー登録処理
# ===========================================================================

@pytest.mark.unit
class TestEnqueueEmailNotification:
    """メール送信キュー登録の早期リターン条件を検証する（foreachBatch）

    観点: 外部連携仕様 > メール送信キュー登録処理
    対応観点表: 2.1 正常系処理, 1.1.1 必須チェック

    設計書定義（alert_judgment.py L335-458）:
        - alert_triggered=True AND alert_email_flag=True のレコードのみ登録
        - 対象レコードがない場合は早期リターン
    """

    @patch("functions.alert_judgment.get_mysql_connection")
    def test_no_alert_records_returns_early(self, mock_get_conn):
        """2.1.1: フィルタ後の alert_records が0件の場合、早期リターンする

        実行内容: alert_records.isEmpty() = True
        想定結果: get_mysql_connection が呼ばれない（Spark JDBC 読み込みも発生しない）
        """
        from pipeline.silver.functions.alert_judgment import enqueue_email_notification
        # Arrange
        mock_batch_df = MagicMock()
        mock_batch_df.filter.return_value.isEmpty.return_value = True
        # Act
        enqueue_email_notification(mock_batch_df, 0, MagicMock())
        # Assert
        mock_get_conn.assert_not_called()

    @patch("functions.alert_judgment.get_mysql_connection")
    def test_empty_queue_after_join_returns_early(self, mock_get_conn):
        """2.1.1: Spark結合後のキューレコードが0件の場合、DB接続なしで終了する

        実行内容: alert_records.isEmpty()=False、queue_records.collect()=[]
        想定結果: get_mysql_connection が呼ばれない
        """
        from pipeline.silver.functions.alert_judgment import enqueue_email_notification
        # Arrange
        mock_batch_df = MagicMock()
        mock_batch_df.filter.return_value.isEmpty.return_value = False
        # Spark JDBC + 結合チェーン末尾の collect() を空リストに設定
        (
            mock_batch_df.filter.return_value
            .join.return_value
            .join.return_value
            .join.return_value
            .select.return_value
            .collect.return_value
        ) = []
        # Act
        enqueue_email_notification(mock_batch_df, 0, MagicMock())
        # Assert
        mock_get_conn.assert_not_called()
        
# ===========================================================================
# STEP 5b: デバイスステータス更新
# 設計書: § 外部連携仕様 > デバイスステータス更新処理
# ===========================================================================

@pytest.mark.unit
class TestUpdateDeviceStatus:
    """デバイスステータスの UPSERT 処理を検証する（foreachBatch）

    観点: 外部連携仕様 > デバイスステータス更新処理
    対応観点表: 2.1 正常系処理, 3.3 更新機能, 2.3 副作用チェック

    設計書定義（alert_judgment.py L608-638）:
        - バッチ内の全レコードを対象に device_id ごとの最新 event_timestamp を取得
        - device_status_data を UPSERT（ON DUPLICATE KEY UPDATE）
    """

    def _make_mock_conn(self):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_conn.cursor.return_value.__exit__.return_value = False
        return mock_conn, mock_cursor

    @patch("functions.alert_judgment.get_mysql_connection")
    def test_empty_batch_returns_without_db_call(self, mock_get_conn):
        """2.1.1: バッチが空の場合、DB接続なしで終了する

        実行内容: batch_df.groupBy().agg().collect() が [] を返す
        想定結果: get_mysql_connection が呼ばれない（早期リターン）
        """
        from pipeline.silver.functions.alert_judgment import update_device_status
        # Arrange
        mock_batch_df = MagicMock()
        mock_batch_df.groupBy.return_value.agg.return_value.collect.return_value = []
        # Act
        update_device_status(mock_batch_df, 0)
        # Assert
        mock_get_conn.assert_not_called()

    @patch("functions.alert_judgment.get_mysql_connection")
    def test_records_execute_upsert_sql(self, mock_get_conn):
        """2.1.1: レコードが存在する場合、device_status_data に UPSERT SQL が実行される

        実行内容: 1件のデバイスレコード（device_id=1001, last_received_time=...）
        想定結果: INSERT INTO device_status_data ... ON DUPLICATE KEY UPDATE が呼ばれる
        """
        from pipeline.silver.functions.alert_judgment import update_device_status
        # Arrange
        records = [_MockRow(device_id=1001, last_received_time="2026-01-23T09:00:00")]
        mock_batch_df = MagicMock()
        mock_batch_df.groupBy.return_value.agg.return_value.collect.return_value = records
        mock_conn, mock_cursor = self._make_mock_conn()
        mock_get_conn.return_value.__enter__.return_value = mock_conn
        mock_get_conn.return_value.__exit__.return_value = False
        # Act
        update_device_status(mock_batch_df, 0)
        # Assert
        sql_executed = mock_cursor.execute.call_args_list[0][0][0]
        assert "INSERT INTO device_status_data" in sql_executed
        assert "ON DUPLICATE KEY UPDATE" in sql_executed
        mock_conn.commit.assert_called_once()

    @patch("functions.alert_judgment.get_mysql_connection")
    def test_multiple_devices_execute_multiple_upserts(self, mock_get_conn):
        """2.1.1: 複数デバイスのレコードが全て UPSERT される

        実行内容: 3件のデバイスレコード
        想定結果: cursor.execute が3回呼ばれる
        """
        from pipeline.silver.functions.alert_judgment import update_device_status
        # Arrange
        records = [
            _MockRow(device_id=1001, last_received_time="2026-01-23T09:00:00"),
            _MockRow(device_id=1002, last_received_time="2026-01-23T09:01:00"),
            _MockRow(device_id=1003, last_received_time="2026-01-23T09:02:00"),
        ]
        mock_batch_df = MagicMock()
        mock_batch_df.groupBy.return_value.agg.return_value.collect.return_value = records
        mock_conn, mock_cursor = self._make_mock_conn()
        mock_get_conn.return_value.__enter__.return_value = mock_conn
        mock_get_conn.return_value.__exit__.return_value = False
        # Act
        update_device_status(mock_batch_df, 0)
        # Assert
        assert mock_cursor.execute.call_count == 3, (
            f"execute が3回呼ばれるべきところ {mock_cursor.execute.call_count} 回"
        )

    @patch("functions.alert_judgment.get_mysql_connection")
    def test_commit_called_once_per_batch(self, mock_get_conn):
        """2.3.1: 複数レコードを処理しても conn.commit() は1回だけ呼ばれる

        実行内容: 3件のデバイスレコード
        想定結果: conn.commit() が1回だけ呼ばれる（全レコード一括コミット）
        """
        from pipeline.silver.functions.alert_judgment import update_device_status
        # Arrange
        records = [
            _MockRow(device_id=1001, last_received_time="2026-01-23T09:00:00"),
            _MockRow(device_id=1002, last_received_time="2026-01-23T09:01:00"),
            _MockRow(device_id=1003, last_received_time="2026-01-23T09:02:00"),
        ]
        mock_batch_df = MagicMock()
        mock_batch_df.groupBy.return_value.agg.return_value.collect.return_value = records
        mock_conn, mock_cursor = self._make_mock_conn()
        mock_get_conn.return_value.__enter__.return_value = mock_conn
        mock_get_conn.return_value.__exit__.return_value = False
        # Act
        update_device_status(mock_batch_df, 0)
        # Assert
        mock_conn.commit.assert_called_once()
        
# ===========================================================================
# STEP 5b: アラート履歴登録（発報時）
# 設計書: § 外部連携仕様 > アラート履歴登録処理
# ===========================================================================

@pytest.mark.unit
class TestInsertAlertHistory:
    """アラート履歴の INSERT と alert_abnormal_state の UPDATE を検証する（foreachBatch）

    観点: 外部連携仕様 > アラート履歴登録処理
    対応観点表: 2.1 正常系処理, 3.2 登録機能, 2.3 副作用チェック

    設計書定義（alert_judgment.py L469-518）:
        - alert_triggered=True のレコードを alert_history に INSERT
        - cursor.lastrowid で取得した alert_history_id を alert_abnormal_state に UPDATE
        - conn.commit() で一括コミット
    """

    def _make_mock_conn(self, lastrowid=9999):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.lastrowid = lastrowid
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_conn.cursor.return_value.__exit__.return_value = False
        return mock_conn, mock_cursor

    @patch("functions.alert_judgment.get_mysql_connection")
    def test_no_fired_records_returns_early(self, mock_get_conn):
        """2.1.1: alert_triggered=True のレコードが0件の場合、DB接続なしで終了する

        実行内容: batch_df.filter().collect() が [] を返す
        想定結果: get_mysql_connection が呼ばれない（早期リターン）
        """
        from pipeline.silver.functions.alert_judgment import insert_alert_history
        # Arrange
        mock_batch_df = MagicMock()
        mock_batch_df.filter.return_value.collect.return_value = []
        # Act
        insert_alert_history(mock_batch_df, 0)
        # Assert
        mock_get_conn.assert_not_called()

    @patch("functions.alert_judgment.get_mysql_connection")
    def test_fired_record_inserts_history_and_updates_state_with_lastrowid(self, mock_get_conn):
        """3.2.1 / 3.3.1: 発報レコードに対して alert_history INSERT 後、lastrowid で alert_abnormal_state を UPDATE する

        実行内容: 1件の alert_triggered=True レコード
        想定結果:
            - cursor.execute が INSERT into alert_history を呼ぶ
            - cursor.lastrowid = 9999 → UPDATE alert_abnormal_state で 9999 が使われる
            - conn.commit() が呼ばれる
        """
        from pipeline.silver.functions.alert_judgment import insert_alert_history
        # Arrange
        records = [_MockRow(
            alert_id=5, device_id=1001,
            abnormal_start_time="2026-01-23T08:00:00",
            current_sensor_value=-30.0,
        )]
        mock_batch_df = MagicMock()
        mock_batch_df.filter.return_value.collect.return_value = records
        mock_conn, mock_cursor = self._make_mock_conn(lastrowid=9999)
        mock_get_conn.return_value.__enter__.return_value = mock_conn
        mock_get_conn.return_value.__exit__.return_value = False
        # Act
        insert_alert_history(mock_batch_df, 0)
        # Assert: INSERT 呼ばれた
        assert mock_cursor.execute.call_count == 2, (
            f"execute が2回（INSERT + UPDATE）呼ばれるべきところ {mock_cursor.execute.call_count} 回"
        )
        insert_sql = mock_cursor.execute.call_args_list[0][0][0]
        assert "INSERT INTO alert_history" in insert_sql
        # Assert: UPDATE に lastrowid=9999 が含まれる
        update_params = mock_cursor.execute.call_args_list[1][0][1]
        assert update_params[0] == 9999, (
            f"UPDATE の最初のパラメータ（alert_history_id）が 9999 でない: {update_params[0]}"
        )
        mock_conn.commit.assert_called_once()

    @patch("functions.alert_judgment.get_mysql_connection")
    def test_multiple_fired_records_all_inserted(self, mock_get_conn):
        """3.2.1: 複数の発報レコードが全て INSERT される

        実行内容: 3件の alert_triggered=True レコード
        想定結果: cursor.execute が INSERT 3回 + UPDATE 3回 = 6回呼ばれる
        """
        from pipeline.silver.functions.alert_judgment import insert_alert_history
        # Arrange
        records = [
            _MockRow(alert_id=1, device_id=1001, abnormal_start_time="2026-01-23T08:00:00", current_sensor_value=-30.0),
            _MockRow(alert_id=2, device_id=1002, abnormal_start_time="2026-01-23T08:05:00", current_sensor_value=-28.0),
            _MockRow(alert_id=3, device_id=1003, abnormal_start_time="2026-01-23T08:10:00", current_sensor_value=-32.0),
        ]
        mock_batch_df = MagicMock()
        mock_batch_df.filter.return_value.collect.return_value = records
        mock_conn, mock_cursor = self._make_mock_conn()
        mock_get_conn.return_value.__enter__.return_value = mock_conn
        mock_get_conn.return_value.__exit__.return_value = False
        # Act
        insert_alert_history(mock_batch_df, 0)
        # Assert: INSERT 3回 + UPDATE 3回 = 6回
        assert mock_cursor.execute.call_count == 6, (
            f"execute が6回（INSERT×3 + UPDATE×3）呼ばれるべきところ {mock_cursor.execute.call_count} 回"
        )

# ===========================================================================
# STEP 5b: アラート履歴更新（復旧時）
# 設計書: § 外部連携仕様 > アラート履歴登録処理 > 復旧時の更新処理
# ===========================================================================

@pytest.mark.unit
class TestUpdateAlertHistoryOnRecovery:
    """復旧時のアラート履歴更新処理を検証する（foreachBatch）

    観点: 外部連携仕様 > アラート履歴登録処理 > 復旧時の更新処理
    対応観点表: 2.1 正常系処理, 3.3 更新機能

    設計書定義（alert_judgment.py L521-565）:
        - threshold_exceeded=False かつ alert_fired 済み かつ alert_history_id 存在 のレコードを更新
        - alert_recovery_datetime = event_timestamp, alert_status_id = ALERT_STATUS_RECOVERED (=2)
    """

    def _make_mock_conn(self):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_conn.cursor.return_value.__exit__.return_value = False
        return mock_conn, mock_cursor

    @patch("functions.alert_judgment.get_mysql_connection")
    @patch("functions.alert_judgment.get_alert_abnormal_state")
    def test_no_recovery_records_returns_early(self, mock_get_abnormal_state, mock_get_conn):
        """2.1.1: 復旧対象レコードが0件の場合、DB接続なしで終了する

        実行内容: recovery_candidates.join().collect() が [] を返す
        想定結果: get_mysql_connection が呼ばれない（早期リターン）
        """
        from pipeline.silver.functions.alert_judgment import update_alert_history_on_recovery
        # Arrange
        mock_batch_df = MagicMock()
        mock_recovery_candidates = (
            mock_batch_df.filter.return_value.select.return_value.distinct.return_value
        )
        mock_recovery_candidates.join.return_value.collect.return_value = []
        # Act
        update_alert_history_on_recovery(mock_batch_df, 0)
        # Assert
        mock_get_conn.assert_not_called()

    @patch("functions.alert_judgment.get_mysql_connection")
    @patch("functions.alert_judgment.get_alert_abnormal_state")
    def test_recovery_records_execute_update_with_recovered_status(self, mock_get_abnormal_state, mock_get_conn):
        """3.3.1: 復旧レコードに対して ALERT_STATUS_RECOVERED=2 で alert_history が UPDATE される

        実行内容: 1件の復旧レコード（alert_history_id=999, event_timestamp=...）
        想定結果:
            - UPDATE alert_history SET alert_recovery_datetime=... が呼ばれる
            - ALERT_STATUS_RECOVERED (=2) がパラメータに渡される
            - conn.commit() が呼ばれる
        """
        from pipeline.silver.functions.alert_judgment import update_alert_history_on_recovery
        # Arrange
        records = [_MockRow(
            event_timestamp="2026-01-23T10:00:00",
            alert_history_id=999,
            device_id=1001,
            alert_id=5,
        )]
        mock_batch_df = MagicMock()
        mock_recovery_candidates = (
            mock_batch_df.filter.return_value.select.return_value.distinct.return_value
        )
        mock_recovery_candidates.join.return_value.collect.return_value = records
        mock_conn, mock_cursor = self._make_mock_conn()
        mock_get_conn.return_value.__enter__.return_value = mock_conn
        mock_get_conn.return_value.__exit__.return_value = False
        # Act
        update_alert_history_on_recovery(mock_batch_df, 0)
        # Assert
        sql_executed = mock_cursor.execute.call_args_list[0][0][0]
        assert "UPDATE alert_history" in sql_executed
        params = mock_cursor.execute.call_args_list[0][0][1]
        # パラメータ: (event_timestamp, ALERT_STATUS_RECOVERED, alert_history_id)
        assert params[1] == 2, (
            f"ALERT_STATUS_RECOVERED=2 がパラメータに渡されていない: {params[1]}"
        )
        assert params[2] == 999, (
            f"alert_history_id=999 がパラメータに渡されていない: {params[2]}"
        )
        mock_conn.commit.assert_called_once()

    @patch("functions.alert_judgment.get_mysql_connection")
    @patch("functions.alert_judgment.get_alert_abnormal_state")
    def test_multiple_recovery_records_all_updated(self, mock_get_abnormal_state, mock_get_conn):
        """3.3.1: 複数の復旧レコードが全て UPDATE される

        実行内容: 3件の復旧レコード
        想定結果: cursor.execute が3回呼ばれる
        """
        from pipeline.silver.functions.alert_judgment import update_alert_history_on_recovery
        # Arrange
        records = [
            _MockRow(event_timestamp="2026-01-23T10:00:00", alert_history_id=101, device_id=1001, alert_id=1),
            _MockRow(event_timestamp="2026-01-23T10:00:00", alert_history_id=102, device_id=1002, alert_id=2),
            _MockRow(event_timestamp="2026-01-23T10:00:00", alert_history_id=103, device_id=1003, alert_id=3),
        ]
        mock_batch_df = MagicMock()
        mock_recovery_candidates = (
            mock_batch_df.filter.return_value.select.return_value.distinct.return_value
        )
        mock_recovery_candidates.join.return_value.collect.return_value = records
        mock_conn, mock_cursor = self._make_mock_conn()
        mock_get_conn.return_value.__enter__.return_value = mock_conn
        mock_get_conn.return_value.__exit__.return_value = False
        # Act
        update_alert_history_on_recovery(mock_batch_df, 0)
        # Assert
        assert mock_cursor.execute.call_count == 3, (
            f"execute が3回呼ばれるべきところ {mock_cursor.execute.call_count} 回"
        )