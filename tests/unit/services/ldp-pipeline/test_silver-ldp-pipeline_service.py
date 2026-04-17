"""
シルバー層LDPパイプライン 単体テスト

設計書参照:
    - docs/03-features/ldp-pipeline/silver-layer/README.md
    - docs/03-features/ldp-pipeline/silver-layer/ldp-pipeline-specification.md

テスト観点参照:
    - docs/05-testing/unit-test/unit-test-perspectives.md

テスト対象（設計書コードサンプルに定義された純粋関数）:
    [1] extract_device_id_from_topic   デバイスID抽出 MQTT Topic
    [2] extract_device_id_from_key     デバイスID抽出 EventHub key
    [3] extract_device_id              デバイスID抽出 統合（優先順位）
    [4] is_valid_json                  JSON有効性判定
    [5] parse_binary_telemetry         バイナリ→JSON変換
    [6] update_json_device_id          JSON device_id 上書き
    [7] convert_to_json_with_device_id バイナリ/JSON統合変換
    [8] determine_update_pattern       異常状態更新パターン判定
    [9] should_enqueue_email           メール送信キュー登録判定
    [10] is_retryable_error            リトライ可能エラー判定
    [11] get_mysql_connection          MySQL接続コンテキストマネージャ（リトライ付き）

各テストメソッドには:
    - 対応する観点表の項目番号（docstring）
    - 設計書仕様の根拠（コメント）
    - AAAパターン（Arrange / Act / Assert）
    - @pytest.mark.unit マーカー
を記載する。
"""

import json
import socket
import struct
import sys
import os
import pytest
from unittest.mock import MagicMock, patch

# パス設定（silver パイプラインの関数モジュールを参照）
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../../../src/pipeline/silver"))

import pymysql
import pymysql.err

from functions.device_id_extraction import (
    extract_device_id_from_topic,
    extract_device_id_from_key,
    extract_device_id,
)
from functions.json_telemetry import (
    is_valid_json,
    parse_binary_telemetry,
    update_json_device_id,
    convert_to_json_with_device_id,
)
from functions.alert_judgment import (
    determine_update_pattern,
    should_enqueue_email,
)
from functions.mysql_connector import is_retryable_error, get_mysql_connection


# =============================================================================
# テストデータヘルパー
# =============================================================================

def _make_binary_telemetry(device_id: int, event_timestamp_ms: int, sensor_values: list) -> bytes:
    """
    設計書仕様のバイナリフォーマット（<iq22d, 188バイト）でテストデータを生成する。

    設計書「バイナリフォーマット定義」:
        device_id        : INT32  (4バイト)
        event_timestamp  : INT64  (8バイト, Unixミリ秒)
        センサー値 × 22  : FLOAT64 (176バイト)
        合計             : 188バイト（リトルエンディアン）
    """
    assert len(sensor_values) == 22
    return struct.pack("<iq22d", device_id, event_timestamp_ms, *sensor_values)


# 標準センサー値（設計書サンプルJSONから引用）
_SENSOR_VALUES = [
    25.5,    # external_temp
    -20.0,   # set_temp_freezer_1
    -19.8,   # internal_sensor_temp_freezer_1
    -19.5,   # internal_temp_freezer_1
    -15.2,   # df_temp_freezer_1
    35.0,    # condensing_temp_freezer_1
    -19.7,   # adjusted_internal_temp_freezer_1
    -25.0,   # set_temp_freezer_2
    -24.6,   # internal_sensor_temp_freezer_2
    -24.3,   # internal_temp_freezer_2
    -18.5,   # df_temp_freezer_2
    38.0,    # condensing_temp_freezer_2
    -24.5,   # adjusted_internal_temp_freezer_2
    2800.0,  # compressor_freezer_1
    3100.0,  # compressor_freezer_2
    1200.0,  # fan_motor_1
    1180.0,  # fan_motor_2
    1150.0,  # fan_motor_3
    1220.0,  # fan_motor_4
    1190.0,  # fan_motor_5
    0.0,     # defrost_heater_output_1
    0.0,     # defrost_heater_output_2
]


# =============================================================================
# [1] extract_device_id_from_topic
# 観点: 2.1 正常系処理 / 1.1.1 必須チェック
# 設計書「MQTT TopicからのデバイスID抽出」
#   - パターン: ^/(\d+)/data/refrigerator$
#   - None の場合は None を返す
#   - パターン不一致は None を返す
# =============================================================================

@pytest.mark.unit
class TestExtractDeviceIdFromTopic:
    """
    [1] MQTT Topic からのデバイスID抽出
    観点: 2.1 正常系処理 / 1.1.1 必須チェック
    設計書セクション: 「データ変換仕様 > MQTT TopicからのデバイスID抽出」
    """

    def test_normal_topic_returns_device_id(self):
        """2.1.1: 正常な MQTT Topic 形式の場合、デバイスIDが返却される
        設計書例: /12345/data/refrigerator → "12345"
        """
        # Arrange
        topic = "/12345/data/refrigerator"
        # Act
        result = extract_device_id_from_topic(topic)
        # Assert
        assert result == "12345"

    def test_multi_digit_device_id_extracted(self):
        """2.1.1: 複数桁のデバイスIDも正しく抽出される
        設計書: <機器ID> は \\d+ （1桁以上の数値）
        """
        # Arrange
        topic = "/987654321/data/refrigerator"
        # Act
        result = extract_device_id_from_topic(topic)
        # Assert
        assert result == "987654321"

    def test_single_digit_device_id_extracted(self):
        """2.1.1: 1桁のデバイスIDも正しく抽出される"""
        # Arrange
        topic = "/1/data/refrigerator"
        # Act
        result = extract_device_id_from_topic(topic)
        # Assert
        assert result == "1"

    def test_none_topic_returns_none(self):
        """1.1.1: topic が None の場合、None が返却される
        設計書: if topic is None: return None
        """
        # Arrange / Act
        result = extract_device_id_from_topic(None)
        # Assert
        assert result is None

    def test_empty_string_returns_none(self):
        """1.1.1: 空文字の場合、None が返却される（パターン不一致）"""
        # Arrange / Act
        result = extract_device_id_from_topic("")
        # Assert
        assert result is None

    def test_non_numeric_device_id_returns_none(self):
        """2.1.1: デバイスIDが数値でない場合、None が返却される
        設計書: パターン \\d+ に非マッチ → None
        """
        # Arrange / Act
        result = extract_device_id_from_topic("/abc/data/refrigerator")
        # Assert
        assert result is None

    def test_wrong_path_suffix_returns_none(self):
        """2.1.1: パス末尾が /data/refrigerator でない場合、None が返却される
        設計書: 正規表現末尾 $ により完全一致を要求
        """
        # Arrange / Act
        result = extract_device_id_from_topic("/12345/data/other")
        # Assert
        assert result is None

    def test_missing_leading_slash_returns_none(self):
        """2.1.1: 先頭スラッシュがない場合、None が返却される
        設計書: パターンが ^ から始まるため先頭 / が必須
        """
        # Arrange / Act
        result = extract_device_id_from_topic("12345/data/refrigerator")
        # Assert
        assert result is None

    def test_trailing_extra_segment_returns_none(self):
        """2.1.1: パスの後ろに余分なセグメントがある場合、None が返却される
        設計書: パターン末尾 $ により完全一致を要求
        """
        # Arrange / Act
        result = extract_device_id_from_topic("/12345/data/refrigerator/extra")
        # Assert
        assert result is None


# =============================================================================
# [2] extract_device_id_from_key
# 観点: 2.1 正常系処理 / 1.1.1 必須チェック
# 設計書「EventHub keyからのデバイスID抽出」
#   - key は数値文字列であることを検証し、strip 後に返す
#   - None / 空文字 / 数値以外は None を返す
# =============================================================================

@pytest.mark.unit
class TestExtractDeviceIdFromKey:
    """
    [2] EventHub key からのデバイスID抽出
    観点: 2.1 正常系処理 / 1.1.1 必須チェック
    設計書セクション: 「データ変換仕様 > EventHub keyからのデバイスID抽出」
    """

    def test_valid_numeric_key_returned(self):
        """2.1.1: 数値文字列のkeyの場合、デバイスIDが返却される"""
        # Arrange
        message_key = "12345"
        # Act
        result = extract_device_id_from_key(message_key)
        # Assert
        assert result == "12345"

    def test_key_with_spaces_trimmed(self):
        """2.1.1: 前後スペースを持つkeyは trim 後の値が返却される
        設計書: message_key.strip() を使用
        """
        # Arrange
        message_key = "  99999  "
        # Act
        result = extract_device_id_from_key(message_key)
        # Assert
        assert result == "99999"

    def test_none_key_returns_none(self):
        """1.1.1: key が None の場合、None が返却される
        設計書: if message_key is None ... return None
        """
        # Arrange / Act
        result = extract_device_id_from_key(None)
        # Assert
        assert result is None

    def test_empty_key_returns_none(self):
        """1.1.1: 空文字のkeyの場合、None が返却される
        設計書: if ... message_key.strip() == "" ... return None
        """
        # Arrange / Act
        result = extract_device_id_from_key("")
        # Assert
        assert result is None

    def test_whitespace_only_key_returns_none(self):
        """1.1.1: スペースのみのkeyの場合、None が返却される"""
        # Arrange / Act
        result = extract_device_id_from_key("   ")
        # Assert
        assert result is None

    def test_non_numeric_key_returns_none(self):
        """2.1.1: 数値以外の文字列keyの場合、None が返却される
        設計書: int(message_key.strip()) が ValueError → None
        """
        # Arrange / Act
        result = extract_device_id_from_key("device-001")
        # Assert
        assert result is None

    def test_alphanumeric_key_returns_none(self):
        """2.1.1: 英数字混在のkeyの場合、None が返却される"""
        # Arrange / Act
        result = extract_device_id_from_key("123abc")
        # Assert
        assert result is None


# =============================================================================
# [3] extract_device_id（統合処理）
# 観点: 2.1 正常系処理 / 1.1.1 必須チェック
# 設計書「デバイスID取得元の優先順位」:
#   優先度1: MQTT Topic（/<機器ID>/data/refrigerator形式）
#   優先度2: EventHub key
#   優先度3: ペイロード内 device_id
# =============================================================================

@pytest.mark.unit
class TestExtractDeviceId:
    """
    [3] デバイスID抽出 統合処理（優先順位）
    観点: 2.1 正常系処理 / 1.1.1 必須チェック
    設計書セクション: 「デバイスID取得元の優先順位」
    """

    def test_priority1_topic_takes_precedence_over_key_and_payload(self):
        """2.1.1: 優先度1 - MQTT Topic が有効な場合、Topic のデバイスIDが返却される
        設計書: 優先順位 1 = MQTT Topic（最優先）
        """
        # Arrange
        topic = "/12345/data/refrigerator"
        message_key = "99999"
        payload_device_id = "11111"
        # Act
        result = extract_device_id(topic, message_key, payload_device_id)
        # Assert
        assert result == "12345"

    def test_priority2_key_used_when_topic_is_none(self):
        """2.1.1: 優先度2 - Topic が None でkeyが有効な場合、key のデバイスIDが返却される"""
        # Arrange
        topic = None
        message_key = "99999"
        payload_device_id = "11111"
        # Act
        result = extract_device_id(topic, message_key, payload_device_id)
        # Assert
        assert result == "99999"

    def test_priority2_key_used_when_topic_is_invalid(self):
        """2.1.1: 優先度2 - Topic が無効なパターンでkeyが有効な場合、key のデバイスIDが返却される"""
        # Arrange
        topic = "/invalid/path"
        message_key = "99999"
        payload_device_id = "11111"
        # Act
        result = extract_device_id(topic, message_key, payload_device_id)
        # Assert
        assert result == "99999"

    def test_priority3_payload_used_when_topic_and_key_are_none(self):
        """2.1.1: 優先度3 - Topic も key も None の場合、ペイロードのデバイスIDが返却される
        設計書: 優先順位 3 = ペイロード内 device_id（フォールバック）
        """
        # Arrange
        topic = None
        message_key = None
        payload_device_id = "11111"
        # Act
        result = extract_device_id(topic, message_key, payload_device_id)
        # Assert
        assert result == "11111"

    def test_priority3_payload_used_when_topic_invalid_and_key_non_numeric(self):
        """2.1.1: 優先度3 - Topic が無効かつkey が数値でない場合、ペイロードが使用される"""
        # Arrange
        topic = None
        message_key = "not-a-number"
        payload_device_id = "55555"
        # Act
        result = extract_device_id(topic, message_key, payload_device_id)
        # Assert
        assert result == "55555"

    def test_payload_device_id_stripped(self):
        """2.1.1: ペイロードのデバイスIDは前後スペースを trim して返却される
        設計書: str(payload_device_id).strip() != "" の場合、strip 後の値を返す
        """
        # Arrange
        topic = None
        message_key = None
        payload_device_id = "  22222  "
        # Act
        result = extract_device_id(topic, message_key, payload_device_id)
        # Assert
        assert result == "22222"

    def test_all_none_returns_none(self):
        """1.1.1: すべてのソースが None の場合、None が返却される
        設計書: すべて失敗時は None を返す
        """
        # Arrange / Act
        result = extract_device_id(None, None, None)
        # Assert
        assert result is None

    def test_payload_empty_string_returns_none(self):
        """1.1.1: Topic・key が None でペイロードが空文字の場合、None が返却される"""
        # Arrange / Act
        result = extract_device_id(None, None, "  ")
        # Assert
        assert result is None


# =============================================================================
# [4] is_valid_json
# 観点: 2.1 正常系処理 / 1.1.1 必須チェック
# 設計書「フォーマット判定ロジック」:
#   - json.loads() 成功 → True
#   - None / 不正 JSON / 空文字 → False
# =============================================================================

@pytest.mark.unit
class TestIsValidJson:
    """
    [4] JSON有効性判定
    観点: 2.1 正常系処理 / 1.1.1 必須チェック
    設計書セクション: 「バイナリ/JSON判定・変換処理 > フォーマット判定ロジック」
    """

    def test_valid_json_object_returns_true(self):
        """2.1.1: 有効なJSONオブジェクト文字列の場合、True が返却される
        設計書: json.loads() が成功した場合 True
        """
        # Arrange
        data = '{"device_id": "12345", "event_timestamp": "2026-01-23T10:30:00.000Z"}'
        # Act / Assert
        assert is_valid_json(data) is True

    def test_valid_json_array_returns_true(self):
        """2.1.1: 有効なJSON配列文字列の場合、True が返却される"""
        # Arrange / Act / Assert
        assert is_valid_json('[1, 2, 3]') is True

    def test_none_returns_false(self):
        """1.1.1: data が None の場合、False が返却される
        設計書: if data is None: return False
        """
        # Arrange / Act / Assert
        assert is_valid_json(None) is False

    def test_empty_string_returns_false(self):
        """1.1.1: 空文字の場合、False が返却される
        設計書: json.JSONDecodeError → False
        """
        # Arrange / Act / Assert
        assert is_valid_json("") is False

    def test_invalid_json_returns_false(self):
        """2.1.1: 不正なJSON文字列の場合、False が返却される
        設計書: json.JSONDecodeError 発生時は False
        """
        # Arrange
        data = '{"key": missing_value}'
        # Act / Assert
        assert is_valid_json(data) is False

    def test_plain_text_returns_false(self):
        """2.1.1: JSONでないプレーンテキストの場合、False が返却される"""
        # Arrange / Act / Assert
        assert is_valid_json("hello world") is False


# =============================================================================
# [5] parse_binary_telemetry
# 観点: 2.1 正常系処理 / 1.1.1 必須チェック
# 設計書「バイナリ→JSON変換処理」:
#   - 188バイトの <iq22d フォーマット → JSON文字列
#   - override_device_id 指定時は device_id を上書き
#   - NaN → null（None）
#   - None / 188バイト以外 → None
# =============================================================================

@pytest.mark.unit
class TestParseBinaryTelemetry:
    """
    [5] バイナリ→JSON変換
    観点: 2.1 正常系処理 / 1.1.1 必須チェック
    設計書セクション: 「バイナリ/JSON判定・変換処理 > バイナリ→JSON変換処理」
    """

    def test_valid_188_bytes_returns_json_string(self):
        """2.1.1: 正常な188バイトのバイナリデータの場合、JSON文字列が返却される
        設計書: struct.unpack('<iq22d', binary_data) でアンパック → json.dumps() で返却
        """
        # Arrange
        binary_data = _make_binary_telemetry(12345, 1706001000000, _SENSOR_VALUES)
        # Act
        result = parse_binary_telemetry(binary_data)
        # Assert
        assert result is not None
        parsed = json.loads(result)
        assert "device_id" in parsed
        assert "event_timestamp" in parsed
        assert "external_temp" in parsed

    def test_override_none_uses_binary_device_id_as_string(self):
        """2.1.1: override_device_id が None の場合、バイナリの device_id を str 変換して使用
        設計書: else: device_id = str(device_id)
        """
        # Arrange
        binary_data = _make_binary_telemetry(12345, 1706001000000, _SENSOR_VALUES)
        # Act
        result = parse_binary_telemetry(binary_data, override_device_id=None)
        # Assert
        parsed = json.loads(result)
        assert parsed["device_id"] == "12345"

    def test_override_device_id_replaces_binary_device_id(self):
        """2.1.1: override_device_id が指定された場合、バイナリの device_id が上書きされる
        設計書: if override_device_id is not None: device_id = override_device_id
        """
        # Arrange
        binary_data = _make_binary_telemetry(12345, 1706001000000, _SENSOR_VALUES)
        # Act
        result = parse_binary_telemetry(binary_data, override_device_id="99999")
        # Assert
        parsed = json.loads(result)
        assert parsed["device_id"] == "99999"

    def test_event_timestamp_is_iso8601_utc_format(self):
        """2.1.1: event_timestamp は ISO 8601 UTC 形式（末尾 Z）で返却される
        設計書: strftime('%Y-%m-%dT%H:%M:%S.') + f'{ms % 1000:03d}Z'
        """
        # Arrange
        binary_data = _make_binary_telemetry(12345, 1706001000000, _SENSOR_VALUES)
        # Act
        result = parse_binary_telemetry(binary_data)
        # Assert
        parsed = json.loads(result)
        ts = parsed["event_timestamp"]
        assert ts.endswith("Z")
        assert "T" in ts

    def test_nan_sensor_value_becomes_null(self):
        """2.1.1: センサー値が NaN の場合、JSON では null（None）に変換される
        設計書: if value != value: result[field_name] = None  # NaNチェック
        """
        # Arrange
        nan_values = [float("nan")] + _SENSOR_VALUES[1:]
        binary_data = _make_binary_telemetry(12345, 1706001000000, nan_values)
        # Act
        result = parse_binary_telemetry(binary_data)
        # Assert
        parsed = json.loads(result)
        assert parsed["external_temp"] is None

    def test_none_binary_returns_none(self):
        """1.1.1: binary_data が None の場合、None が返却される
        設計書: if binary_data is None or len(binary_data) != 188: return None
        """
        # Arrange / Act / Assert
        assert parse_binary_telemetry(None) is None

    def test_undersized_binary_returns_none(self):
        """2.1.1: 188バイト未満のデータの場合、None が返却される
        設計書変換エラー表: 「バイナリデータが188バイトでない → レコード破棄」
        """
        # Arrange / Act / Assert
        assert parse_binary_telemetry(b'\x00' * 187) is None

    def test_oversized_binary_returns_none(self):
        """2.1.1: 188バイト超のデータの場合、None が返却される"""
        # Arrange / Act / Assert
        assert parse_binary_telemetry(b'\x00' * 189) is None

    def test_all_22_sensor_fields_present_in_result(self):
        """2.1.1: 変換結果のJSONに22個のセンサーフィールドがすべて含まれる
        設計書「バイナリフォーマット定義」: 22個の FLOAT64 フィールドが定義されている
        """
        # Arrange
        binary_data = _make_binary_telemetry(12345, 1706001000000, _SENSOR_VALUES)
        expected_fields = [
            "external_temp", "set_temp_freezer_1", "internal_sensor_temp_freezer_1",
            "internal_temp_freezer_1", "df_temp_freezer_1", "condensing_temp_freezer_1",
            "adjusted_internal_temp_freezer_1", "set_temp_freezer_2",
            "internal_sensor_temp_freezer_2", "internal_temp_freezer_2",
            "df_temp_freezer_2", "condensing_temp_freezer_2",
            "adjusted_internal_temp_freezer_2", "compressor_freezer_1",
            "compressor_freezer_2", "fan_motor_1", "fan_motor_2", "fan_motor_3",
            "fan_motor_4", "fan_motor_5", "defrost_heater_output_1", "defrost_heater_output_2",
        ]
        # Act
        result = parse_binary_telemetry(binary_data)
        parsed = json.loads(result)
        # Assert
        for field in expected_fields:
            assert field in parsed, f"センサーフィールド '{field}' が欠落している"


# =============================================================================
# [6] update_json_device_id
# 観点: 2.1 正常系処理 / 1.1.1 必須チェック / 2.3 副作用チェック
# 設計書「JSON形式へのデバイスID上書き処理」:
#   - override_device_id を int に変換して device_id を上書き
#   - override_device_id=None → json_str をそのまま返す
#   - json_str=None → None
#   - 不正JSON / 変換失敗 → json_str をそのまま返す
# =============================================================================

@pytest.mark.unit
class TestUpdateJsonDeviceId:
    """
    [6] JSON device_id 上書き処理
    観点: 2.1 正常系処理 / 1.1.1 必須チェック / 2.3 副作用チェック
    設計書セクション: 「バイナリ/JSON判定・変換処理 > JSON形式へのデバイスID上書き処理」
    """

    def test_device_id_overwritten_as_integer(self):
        """2.1.1: 有効なJSONと override_device_id が指定された場合、device_id が整数型で上書きされる
        設計書: data["device_id"] = int(override_device_id)
        """
        # Arrange
        json_str = '{"device_id": "12345", "event_timestamp": "2026-01-23T10:30:00.000Z"}'
        # Act
        result = update_json_device_id(json_str, "99999")
        # Assert
        parsed = json.loads(result)
        assert parsed["device_id"] == 99999
        assert isinstance(parsed["device_id"], int)

    def test_override_none_returns_original_string(self):
        """2.1.1: override_device_id が None の場合、元の JSON 文字列がそのまま返却される
        設計書: if override_device_id is None: return json_str
        """
        # Arrange
        json_str = '{"device_id": "12345"}'
        # Act
        result = update_json_device_id(json_str, None)
        # Assert
        assert result == json_str

    def test_none_json_str_returns_none(self):
        """1.1.1: json_str が None の場合、None が返却される
        設計書: if json_str is None: return None
        """
        # Arrange / Act / Assert
        assert update_json_device_id(None, "99999") is None

    def test_invalid_json_returns_original_string(self):
        """1.3.1: 不正なJSON文字列の場合、元の文字列がそのまま返却される（例外を発生させない）
        設計書: except (json.JSONDecodeError, TypeError, ValueError): return json_str
        """
        # Arrange
        json_str = "not-a-json"
        # Act
        result = update_json_device_id(json_str, "99999")
        # Assert
        assert result == json_str

    def test_non_numeric_override_returns_original_string(self):
        """1.3.1: override_device_id が数値変換不可の場合、元の文字列が返却される
        設計書: ValueError → return json_str
        """
        # Arrange
        json_str = '{"device_id": "12345"}'
        # Act
        result = update_json_device_id(json_str, "not-a-number")
        # Assert
        assert result == json_str

    def test_other_fields_not_affected(self):
        """2.3.1: device_id 以外のフィールドは変更されない
        設計書: device_id のみを上書きし、他のフィールドはそのまま保持する
        """
        # Arrange
        json_str = '{"device_id": "12345", "external_temp": 25.5, "event_timestamp": "2026-01-23T10:30:00.000Z"}'
        # Act
        result = update_json_device_id(json_str, "99999")
        # Assert
        parsed = json.loads(result)
        assert parsed["external_temp"] == 25.5
        assert parsed["event_timestamp"] == "2026-01-23T10:30:00.000Z"


# =============================================================================
# [7] convert_to_json_with_device_id
# 観点: 2.1 正常系処理 / 1.1.1 必須チェック
# 設計書「フォーマット判定・変換の統合処理」:
#   Step1: UTF-8 デコード試行
#   Step2: is_valid_json() → update_json_device_id() で返却
#   Step3: parse_binary_telemetry() にフォールバック
# =============================================================================

@pytest.mark.unit
class TestConvertToJsonWithDeviceId:
    """
    [7] バイナリ/JSON統合変換処理
    観点: 2.1 正常系処理 / 1.1.1 必須チェック
    設計書セクション: 「バイナリ/JSON判定・変換処理 > フォーマット判定・変換の統合処理」
    """

    def test_utf8_json_bytes_returns_json_with_overridden_device_id(self):
        """2.1.1: UTF-8エンコードされたJSON文字列の場合、device_id 上書き後のJSONが返却される
        設計書: Step1→Step2 のフロー（JSON→update_json_device_id）
        """
        # Arrange
        raw_value = json.dumps({"device_id": "12345", "event_timestamp": "2026-01-23T10:30:00.000Z"}).encode("utf-8")
        # Act
        result = convert_to_json_with_device_id(raw_value, "99999")
        # Assert
        assert result is not None
        assert json.loads(result)["device_id"] == 99999

    def test_binary_188_bytes_returns_json(self):
        """2.1.1: 188バイトのバイナリデータの場合、バイナリ変換によるJSONが返却される
        設計書: Step3 のフロー（バイナリ→parse_binary_telemetry）
        """
        # Arrange
        raw_value = _make_binary_telemetry(12345, 1706001000000, _SENSOR_VALUES)
        # Act
        result = convert_to_json_with_device_id(raw_value, "99999")
        # Assert
        assert result is not None
        parsed = json.loads(result)
        assert "device_id" in parsed

    def test_none_returns_none(self):
        """1.1.1: raw_value が None の場合、None が返却される
        設計書: if raw_value is None: return None
        """
        # Arrange / Act / Assert
        assert convert_to_json_with_device_id(None, "99999") is None

    def test_invalid_utf8_and_wrong_size_returns_none(self):
        """2.1.1: UTF-8デコード失敗かつ188バイト以外のデータの場合、None が返却される
        設計書変換エラー表: 「UTF-8デコード失敗かつバイナリパース失敗 → レコード破棄」
        """
        # Arrange
        raw_value = b'\xff\xfe' + b'\x00' * 10  # 不正 UTF-8 かつ 188 バイト未満
        # Act / Assert
        assert convert_to_json_with_device_id(raw_value, "99999") is None

    def test_override_none_preserves_original_device_id(self):
        """2.1.1: override_device_id が None の場合、元のJSONの device_id が保持される"""
        # Arrange
        raw_value = json.dumps({"device_id": "12345"}).encode("utf-8")
        # Act
        result = convert_to_json_with_device_id(raw_value, None)
        # Assert
        assert json.loads(result)["device_id"] == "12345"


# =============================================================================
# [8] determine_update_pattern
# 観点: 2.1 正常系処理 / 機能別テスト
# 設計書「異常状態テーブル更新処理」:
#   threshold_exceeded=False             → "recovery"
#   threshold_exceeded=True, triggered=True  → "alert_fired"
#   threshold_exceeded=True, triggered=False → "abnormal_start"
# =============================================================================

@pytest.mark.unit
class TestDetermineUpdatePattern:
    """
    [8] 異常状態テーブル更新パターン判定
    観点: 2.1 正常系処理 / 機能別テスト
    設計書セクション: 「アラート処理仕様 > 異常状態テーブル更新処理」
    """

    def test_recovery_when_threshold_not_exceeded(self):
        """2.1.1: threshold_exceeded=False の場合、"recovery" が返却される
        設計書更新パターン4: 復旧 → abnormal_start_time=NULL, alert_fired_time=NULL
        """
        # Arrange / Act
        result = determine_update_pattern(False, False)
        # Assert
        assert result == "recovery"

    def test_recovery_regardless_of_alert_triggered_when_not_exceeded(self):
        """2.1.1: threshold_exceeded=False の場合、alert_triggered に関わらず "recovery"
        設計書: threshold_exceeded=False が最優先判定条件
        """
        # Arrange / Act
        result = determine_update_pattern(False, True)
        # Assert
        assert result == "recovery"

    def test_alert_fired_when_threshold_exceeded_and_triggered(self):
        """2.1.1: threshold_exceeded=True かつ alert_triggered=True の場合、"alert_fired" が返却される
        設計書更新パターン3: アラート発報 → alert_fired_time=current_timestamp
        """
        # Arrange / Act
        result = determine_update_pattern(True, True)
        # Assert
        assert result == "alert_fired"

    def test_abnormal_start_when_threshold_exceeded_and_not_triggered(self):
        """2.1.1: threshold_exceeded=True かつ alert_triggered=False の場合、"abnormal_start" が返却される
        設計書更新パターン1・2: 新規異常開始 または 異常継続
        """
        # Arrange / Act
        result = determine_update_pattern(True, False)
        # Assert
        assert result == "abnormal_start"

    def test_return_value_is_str(self):
        """2.1.1: 返却値はすべて文字列型である"""
        for thresh, triggered in [(False, False), (False, True), (True, True), (True, False)]:
            assert isinstance(determine_update_pattern(thresh, triggered), str)

    def test_all_return_values_within_defined_patterns(self):
        """2.1.1: 返却値は設計書で定義された3値のみである"""
        valid = {"recovery", "alert_fired", "abnormal_start"}
        for thresh, triggered in [(False, False), (False, True), (True, True), (True, False)]:
            assert determine_update_pattern(thresh, triggered) in valid


# =============================================================================
# [9] should_enqueue_email
# 観点: 2.1 正常系処理 / 機能別テスト
# 設計書「キュー登録の設計方針」:
#   登録条件: alert_triggered=True AND alert_email_flag=True のみ True
# =============================================================================

@pytest.mark.unit
class TestShouldEnqueueEmail:
    """
    [9] メール送信キュー登録判定
    観点: 2.1 正常系処理 / 機能別テスト
    設計書セクション: 「外部連携仕様 > キュー登録の設計方針」
    """

    def test_true_when_both_flags_true(self):
        """2.1.1: alert_triggered=True かつ alert_email_flag=True の場合、True が返却される
        設計書: 登録条件 = alert_email_flag=TRUE（かつアラート発報済み）
        """
        # Arrange / Act / Assert
        assert should_enqueue_email(True, True) is True

    def test_false_when_not_triggered(self):
        """2.1.1: alert_triggered=False の場合、alert_email_flag に関わらず False が返却される"""
        # Arrange / Act / Assert
        assert should_enqueue_email(False, True) is False

    def test_false_when_email_flag_false(self):
        """2.1.1: alert_email_flag=False の場合、alert_triggered に関わらず False が返却される
        設計書: alert_email_flag=FALSE の場合はメール送信キューに登録しない
        """
        # Arrange / Act / Assert
        assert should_enqueue_email(True, False) is False

    def test_false_when_both_false(self):
        """2.1.1: 両フラグが False の場合、False が返却される"""
        # Arrange / Act / Assert
        assert should_enqueue_email(False, False) is False

    def test_return_value_is_bool(self):
        """2.1.1: 返却値は bool 型である"""
        # Arrange / Act / Assert
        assert isinstance(should_enqueue_email(True, True), bool)


# =============================================================================
# [10] is_retryable_error
# 観点: 1.3 エラーハンドリング
# 設計書「OLTPリトライ戦略 > リトライ対象エラー表」:
#   ○ socket.timeout / ConnectionResetError / BrokenPipeError / OSError
#   ○ pymysql.err.OperationalError errno=2003, 2006, 2013
#   × pymysql.err.OperationalError errno=1045（認証エラー）
#   × pymysql.err.ProgrammingError / IntegrityError（SQLエラー）
# =============================================================================

@pytest.mark.unit
class TestIsRetryableError:
    """
    [10] リトライ可能エラー判定
    観点: 1.3 エラーハンドリング
    設計書セクション: 「外部連携仕様 > OLTPリトライ戦略 > リトライ対象エラー」
    """

    # ---- リトライ対象（ネットワーク系） ----

    def test_socket_timeout_is_retryable(self):
        """1.3.1: socket.timeout はリトライ対象（○）
        設計書リトライ対象エラー表: タイムアウト → ○
        """
        assert is_retryable_error(socket.timeout("timed out")) is True

    def test_connection_reset_error_is_retryable(self):
        """1.3.1: ConnectionResetError はリトライ対象（○）
        設計書: 一時的なネットワークエラー → ○
        """
        assert is_retryable_error(ConnectionResetError()) is True

    def test_broken_pipe_error_is_retryable(self):
        """1.3.1: BrokenPipeError はリトライ対象（○）"""
        assert is_retryable_error(BrokenPipeError()) is True

    def test_os_error_is_retryable(self):
        """1.3.1: OSError はリトライ対象（○）"""
        assert is_retryable_error(OSError("unreachable")) is True

    # ---- リトライ対象（MySQL接続系） ----

    def test_mysql_errno_2003_is_retryable(self):
        """1.3.1: OperationalError errno=2003 はリトライ対象（○）
        設計書: 接続エラー Can't connect to MySQL server → ○
        """
        err = pymysql.err.OperationalError(2003, "Can't connect")
        assert is_retryable_error(err) is True

    def test_mysql_errno_2006_is_retryable(self):
        """1.3.1: OperationalError errno=2006 はリトライ対象（○）
        設計書: MySQL server has gone away → ○
        """
        err = pymysql.err.OperationalError(2006, "gone away")
        assert is_retryable_error(err) is True

    def test_mysql_errno_2013_is_retryable(self):
        """1.3.1: OperationalError errno=2013 はリトライ対象（○）
        設計書: Lost connection to MySQL server during query → ○
        """
        err = pymysql.err.OperationalError(2013, "lost connection")
        assert is_retryable_error(err) is True

    # ---- リトライ対象外 ----

    def test_mysql_errno_1045_is_not_retryable(self):
        """1.3.1: OperationalError errno=1045 はリトライ対象外（×）
        設計書: 認証エラー Access denied → ×
        """
        err = pymysql.err.OperationalError(1045, "Access denied")
        assert is_retryable_error(err) is False

    def test_programming_error_is_not_retryable(self):
        """1.3.1: ProgrammingError はリトライ対象外（×）
        設計書: SQLエラー Syntax error → ×
        """
        err = pymysql.err.ProgrammingError(1064, "SQL syntax error")
        assert is_retryable_error(err) is False

    def test_integrity_error_is_not_retryable(self):
        """1.3.1: IntegrityError はリトライ対象外（×）
        設計書: 制約違反 Constraint violation → ×
        """
        err = pymysql.err.IntegrityError(1062, "Duplicate entry")
        assert is_retryable_error(err) is False

    def test_value_error_is_not_retryable(self):
        """1.3.1: ValueError はリトライ対象外（接続系エラーではない）"""
        assert is_retryable_error(ValueError("bad value")) is False


# =============================================================================
# [11] get_mysql_connection
# 観点: 1.3 エラーハンドリング / 2.1 正常系処理
# 設計書「OLTPリトライ戦略」:
#   最大リトライ回数: 3回
#   リトライ動作シーケンス:
#     試行1（attempt=0）: 実行 → 失敗 → 1〜2秒待機
#     試行2（attempt=1）: 実行 → 失敗 → 2〜4秒待機
#     試行3（attempt=2）: 実行 → 失敗 → 例外送出（リトライ上限）
# =============================================================================

@pytest.mark.unit
class TestGetMysqlConnection:
    """
    [11] MySQL接続コンテキストマネージャ（リトライ付き）
    観点: 1.3 エラーハンドリング / 2.1 正常系処理
    設計書セクション: 「外部連携仕様 > OLTPリトライ戦略」
    """

    def test_successful_connection_yields_conn_object(self):
        """2.1.1: 接続成功時、接続オブジェクトが yield される
        設計書: 正常接続時は conn を yield して return
        """
        # Arrange
        mock_conn = MagicMock()
        with patch("functions.mysql_connector.get_mysql_config", return_value={}), \
             patch("functions.mysql_connector.pymysql.connect", return_value=mock_conn):
            # Act
            with get_mysql_connection() as conn:
                # Assert
                assert conn is mock_conn

    def test_connection_closed_after_context_exit(self):
        """2.1.1: コンテキスト終了後、conn.close() が呼ばれる
        設計書: finally ブロックで conn.close()
        """
        # Arrange
        mock_conn = MagicMock()
        with patch("functions.mysql_connector.get_mysql_config", return_value={}), \
             patch("functions.mysql_connector.pymysql.connect", return_value=mock_conn):
            with get_mysql_connection() as conn:
                pass
        # Assert
        mock_conn.close.assert_called()

    def test_raises_after_3_failures(self):
        """1.3.1: 3回連続失敗した場合、例外が送出される
        設計書リトライシーケンス: 試行3（attempt=2）→ 例外送出（リトライ上限）
        """
        # Arrange
        err = pymysql.err.OperationalError(2003, "Can't connect")
        with patch("functions.mysql_connector.get_mysql_config", return_value={}), \
             patch("functions.mysql_connector.pymysql.connect", side_effect=err), \
             patch("functions.mysql_connector.time.sleep"):
            # Act & Assert
            with pytest.raises(pymysql.err.OperationalError):
                with get_mysql_connection() as conn:
                    pass

    def test_connect_called_3_times_on_all_failures(self):
        """1.3.1: 全失敗時、pymysql.connect は3回呼ばれる
        設計書リトライシーケンス: attempt=0,1,2 の3回試行後に例外送出
        """
        # Arrange
        err = pymysql.err.OperationalError(2003, "Can't connect")
        with patch("functions.mysql_connector.get_mysql_config", return_value={}), \
             patch("functions.mysql_connector.pymysql.connect", side_effect=err) as mock_connect, \
             patch("functions.mysql_connector.time.sleep"):
            with pytest.raises(pymysql.err.OperationalError):
                with get_mysql_connection() as conn:
                    pass
        # Assert
        assert mock_connect.call_count == 3

    def test_sleep_called_twice_for_retry_waits(self):
        """1.3.1: リトライ待機に time.sleep が2回呼ばれる
        設計書リトライシーケンス:
          attempt=0: sleep（1〜2秒）
          attempt=1: sleep（2〜4秒）
          attempt=2: 例外送出（sleepなし）
        """
        # Arrange
        err = pymysql.err.OperationalError(2003, "Can't connect")
        with patch("functions.mysql_connector.get_mysql_config", return_value={}), \
             patch("functions.mysql_connector.pymysql.connect", side_effect=err), \
             patch("functions.mysql_connector.time.sleep") as mock_sleep:
            with pytest.raises(pymysql.err.OperationalError):
                with get_mysql_connection() as conn:
                    pass
        # Assert
        assert mock_sleep.call_count == 2

    def test_succeeds_on_second_attempt_after_first_failure(self):
        """2.1.1: 1回目失敗・2回目成功の場合、接続オブジェクトが正常に取得できる
        設計書: リトライで接続成功した場合は conn を yield する
        """
        # Arrange
        err = pymysql.err.OperationalError(2003, "Can't connect")
        mock_conn = MagicMock()
        with patch("functions.mysql_connector.get_mysql_config", return_value={}), \
             patch("functions.mysql_connector.pymysql.connect", side_effect=[err, mock_conn]), \
             patch("functions.mysql_connector.time.sleep"):
            # Act
            with get_mysql_connection() as conn:
                # Assert
                assert conn is mock_conn
