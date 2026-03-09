"""
シルバー層LDPパイプライン - バイナリ/JSON判定・変換処理 単体テスト

対象関数:
    - is_valid_json()
    - parse_binary_telemetry()
    - update_json_device_id()
    - convert_to_json_with_device_id()

参照仕様書: docs/03-features/ldp-pipeline/silver-layer/ldp-pipeline-specification.md
            「バイナリ/JSON判定・変換処理」セクション
"""
import json
import math
import struct
import pytest
from datetime import datetime, timezone


# ============================================================
# テスト対象関数（仕様書記載の実装を直接定義）
# ============================================================

def is_valid_json(data: str) -> bool:
    """文字列が有効なJSONかどうかを判定する"""
    if data is None:
        return False
    try:
        json.loads(data)
        return True
    except (json.JSONDecodeError, TypeError):
        return False


def parse_binary_telemetry(binary_data: bytes, override_device_id: str = None):
    """バイナリ形式のテレメトリデータをJSON文字列に変換する"""
    if binary_data is None or len(binary_data) != 188:
        return None

    try:
        unpacked = struct.unpack('<iq22d', binary_data)
        device_id = unpacked[0]
        event_timestamp_ms = unpacked[1]
        sensor_values = unpacked[2:]

        if override_device_id is not None:
            device_id = override_device_id
        else:
            device_id = str(device_id)

        event_timestamp = datetime.fromtimestamp(
            event_timestamp_ms / 1000.0,
            tz=timezone.utc
        ).strftime('%Y-%m-%dT%H:%M:%S.') + f'{event_timestamp_ms % 1000:03d}Z'

        sensor_fields = [
            "external_temp", "set_temp_freezer_1",
            "internal_sensor_temp_freezer_1", "internal_temp_freezer_1",
            "df_temp_freezer_1", "condensing_temp_freezer_1",
            "adjusted_internal_temp_freezer_1", "set_temp_freezer_2",
            "internal_sensor_temp_freezer_2", "internal_temp_freezer_2",
            "df_temp_freezer_2", "condensing_temp_freezer_2",
            "adjusted_internal_temp_freezer_2", "compressor_freezer_1",
            "compressor_freezer_2", "fan_motor_1", "fan_motor_2",
            "fan_motor_3", "fan_motor_4", "fan_motor_5",
            "defrost_heater_output_1", "defrost_heater_output_2"
        ]

        result = {"device_id": device_id, "event_timestamp": event_timestamp}
        for i, field_name in enumerate(sensor_fields):
            value = sensor_values[i]
            result[field_name] = None if value != value else value  # NaN → None

        return json.dumps(result)

    except (struct.error, ValueError, OverflowError):
        return None


def update_json_device_id(json_str: str, override_device_id: str):
    """JSON文字列内のdevice_idを上書きする"""
    if json_str is None:
        return None
    if override_device_id is None:
        return json_str
    try:
        data = json.loads(json_str)
        data["device_id"] = override_device_id
        return json.dumps(data)
    except (json.JSONDecodeError, TypeError):
        return json_str


def convert_to_json_with_device_id(raw_value: bytes, override_device_id: str):
    """テレメトリデータをJSON形式に変換し、デバイスIDを設定する"""
    if raw_value is None:
        return None
    try:
        decoded_str = raw_value.decode('utf-8')
        if is_valid_json(decoded_str):
            return update_json_device_id(decoded_str, override_device_id)
    except (UnicodeDecodeError, AttributeError):
        pass
    return parse_binary_telemetry(raw_value, override_device_id)


# ============================================================
# テストデータ生成ヘルパー
# ============================================================

def make_valid_binary(device_id: int = 12345,
                      timestamp_ms: int = 1737625800000,
                      sensor_values: list = None) -> bytes:
    """188バイトの正常バイナリデータを生成する"""
    if sensor_values is None:
        sensor_values = [25.5, -20.0, -19.8, -19.5, -15.2, 35.0, -19.7,
                         -25.0, -24.6, -24.3, -18.5, 38.0, -24.5,
                         2800.0, 3100.0, 1200.0, 1180.0, 1150.0,
                         1220.0, 1190.0, 0.0, 0.0]
    return struct.pack('<iq22d', device_id, timestamp_ms, *sensor_values)


# ============================================================
# is_valid_json のテスト
# ============================================================

@pytest.mark.unit
class TestIsValidJson:
    """JSON形式判定処理
    観点: 2.1 正常系処理, 1.1.1 必須チェック, 1.3 エラーハンドリング
    """

    def test_valid_json_object(self):
        """2.1.1: 有効なJSONオブジェクト文字列はTrueを返す"""
        # Arrange
        data = '{"device_id": "12345", "event_timestamp": "2026-01-23T10:30:00.000Z"}'

        # Act
        result = is_valid_json(data)

        # Assert
        assert result is True

    def test_valid_json_array(self):
        """2.1.2: 有効なJSON配列文字列はTrueを返す"""
        # Arrange
        data = '[1, 2, 3]'

        # Act
        result = is_valid_json(data)

        # Assert
        assert result is True

    def test_none_returns_false(self):
        """1.1.2: NoneはFalseを返す"""
        # Arrange
        data = None

        # Act
        result = is_valid_json(data)

        # Assert
        assert result is False

    def test_empty_string_returns_false(self):
        """1.1.1: 空文字はFalseを返す"""
        # Arrange
        data = ""

        # Act
        result = is_valid_json(data)

        # Assert
        assert result is False

    def test_invalid_json_syntax(self):
        """1.3: JSON構文エラーの文字列はFalseを返す"""
        # Arrange
        data = '{device_id: 12345}'  # クォートなし

        # Act
        result = is_valid_json(data)

        # Assert
        assert result is False

    def test_plain_string_returns_false(self):
        """1.3: JSONでない平文字列はFalseを返す"""
        # Arrange
        data = "hello world"

        # Act
        result = is_valid_json(data)

        # Assert
        assert result is False

    def test_truncated_json_returns_false(self):
        """1.3: 不完全なJSON文字列はFalseを返す"""
        # Arrange
        data = '{"device_id": 12345'  # 閉じ括弧なし

        # Act
        result = is_valid_json(data)

        # Assert
        assert result is False


# ============================================================
# parse_binary_telemetry のテスト
# ============================================================

@pytest.mark.unit
class TestParseBinaryTelemetry:
    """バイナリ→JSON変換処理
    観点: 2.1 正常系処理, 1.1 入力チェック, 1.3 エラーハンドリング
    """

    def test_valid_binary_returns_json_string(self):
        """2.1.1: 正常な188バイトのバイナリデータがJSON文字列に変換される"""
        # Arrange
        binary_data = make_valid_binary(device_id=12345, timestamp_ms=1737625800000)

        # Act
        result = parse_binary_telemetry(binary_data)

        # Assert
        assert result is not None
        parsed = json.loads(result)
        assert parsed["device_id"] == "12345"
        assert "event_timestamp" in parsed
        assert parsed["external_temp"] == 25.5

    def test_override_device_id_used_when_provided(self):
        """2.1.2: override_device_idが指定された場合はバイナリ内のdevice_idを上書きする"""
        # Arrange
        binary_data = make_valid_binary(device_id=12345)
        override_device_id = "99999"

        # Act
        result = parse_binary_telemetry(binary_data, override_device_id)

        # Assert
        parsed = json.loads(result)
        assert parsed["device_id"] == "99999"

    def test_timestamp_converted_to_iso8601(self):
        """2.1.3: event_timestampがISO 8601形式（UTC）に変換される"""
        # Arrange
        # 2025-01-23T09:50:00.000Z = 1737625800000ms
        timestamp_ms = 1737625800000
        binary_data = make_valid_binary(timestamp_ms=timestamp_ms)

        # Act
        result = parse_binary_telemetry(binary_data)

        # Assert
        parsed = json.loads(result)
        assert parsed["event_timestamp"] == "2025-01-23T09:50:00.000Z"

    def test_timestamp_milliseconds_preserved(self):
        """2.1.3: タイムスタンプのミリ秒部分が正しく変換される"""
        # Arrange
        # ミリ秒を含むタイムスタンプ: 123ms
        timestamp_ms = 1737625800123
        binary_data = make_valid_binary(timestamp_ms=timestamp_ms)

        # Act
        result = parse_binary_telemetry(binary_data)

        # Assert
        parsed = json.loads(result)
        assert parsed["event_timestamp"].endswith(".123Z")

    def test_nan_sensor_value_converted_to_none(self):
        """2.1.2: NaN値のセンサーカラムはnullとして変換される"""
        # Arrange
        sensor_values = [float('nan')] + [-20.0] * 21
        binary_data = make_valid_binary(sensor_values=sensor_values)

        # Act
        result = parse_binary_telemetry(binary_data)

        # Assert
        parsed = json.loads(result)
        assert parsed["external_temp"] is None

    def test_none_binary_returns_none(self):
        """1.1.2: binary_dataがNoneの場合はNoneを返す"""
        # Arrange
        binary_data = None

        # Act
        result = parse_binary_telemetry(binary_data)

        # Assert
        assert result is None

    def test_binary_less_than_188_bytes_returns_none(self):
        """1.3: 188バイト未満のバイナリはNoneを返す（不正なデータサイズ）"""
        # Arrange
        binary_data = b'\x00' * 187

        # Act
        result = parse_binary_telemetry(binary_data)

        # Assert
        assert result is None

    def test_binary_more_than_188_bytes_returns_none(self):
        """1.3: 188バイト超過のバイナリはNoneを返す（不正なデータサイズ）"""
        # Arrange
        binary_data = b'\x00' * 189

        # Act
        result = parse_binary_telemetry(binary_data)

        # Assert
        assert result is None

    def test_all_22_sensor_fields_present(self):
        """2.1.1: JSON変換後に22個のセンサーフィールドがすべて含まれる"""
        # Arrange
        binary_data = make_valid_binary()

        # Act
        result = parse_binary_telemetry(binary_data)

        # Assert
        parsed = json.loads(result)
        expected_fields = [
            "external_temp", "set_temp_freezer_1",
            "internal_sensor_temp_freezer_1", "internal_temp_freezer_1",
            "df_temp_freezer_1", "condensing_temp_freezer_1",
            "adjusted_internal_temp_freezer_1", "set_temp_freezer_2",
            "internal_sensor_temp_freezer_2", "internal_temp_freezer_2",
            "df_temp_freezer_2", "condensing_temp_freezer_2",
            "adjusted_internal_temp_freezer_2", "compressor_freezer_1",
            "compressor_freezer_2", "fan_motor_1", "fan_motor_2",
            "fan_motor_3", "fan_motor_4", "fan_motor_5",
            "defrost_heater_output_1", "defrost_heater_output_2"
        ]
        for field in expected_fields:
            assert field in parsed, f"フィールド '{field}' がJSON出力に含まれていない"

    def test_empty_bytes_returns_none(self):
        """1.1.1: 空バイト列はNoneを返す"""
        # Arrange
        binary_data = b''

        # Act
        result = parse_binary_telemetry(binary_data)

        # Assert
        assert result is None


# ============================================================
# update_json_device_id のテスト
# ============================================================

@pytest.mark.unit
class TestUpdateJsonDeviceId:
    """JSONデバイスID上書き処理
    観点: 2.1 正常系処理, 1.1.1 必須チェック, 1.3 エラーハンドリング
    """

    def test_device_id_overwritten_in_json(self):
        """2.1.1: JSONのdevice_idが指定した値で上書きされる"""
        # Arrange
        json_str = '{"device_id": "12345", "event_timestamp": "2026-01-23T10:30:00.000Z"}'
        override_device_id = "99999"

        # Act
        result = update_json_device_id(json_str, override_device_id)

        # Assert
        parsed = json.loads(result)
        assert parsed["device_id"] == "99999"

    def test_other_fields_preserved_after_override(self):
        """2.1.2: device_id上書き後も他のフィールドは変更されない"""
        # Arrange
        json_str = '{"device_id": "12345", "external_temp": 25.5}'
        override_device_id = "99999"

        # Act
        result = update_json_device_id(json_str, override_device_id)

        # Assert
        parsed = json.loads(result)
        assert parsed["external_temp"] == 25.5

    def test_none_json_str_returns_none(self):
        """1.1.2: json_strがNoneの場合はNoneを返す"""
        # Arrange
        json_str = None
        override_device_id = "99999"

        # Act
        result = update_json_device_id(json_str, override_device_id)

        # Assert
        assert result is None

    def test_none_override_id_returns_original(self):
        """2.1.2: override_device_idがNoneの場合は元のJSONをそのまま返す"""
        # Arrange
        json_str = '{"device_id": "12345"}'
        override_device_id = None

        # Act
        result = update_json_device_id(json_str, override_device_id)

        # Assert
        assert result == json_str

    def test_invalid_json_returns_original_string(self):
        """1.3: 不正なJSON文字列の場合は元の文字列をそのまま返す"""
        # Arrange
        json_str = '{invalid json}'
        override_device_id = "99999"

        # Act
        result = update_json_device_id(json_str, override_device_id)

        # Assert
        assert result == json_str


# ============================================================
# convert_to_json_with_device_id のテスト
# ============================================================

@pytest.mark.unit
class TestConvertToJsonWithDeviceId:
    """フォーマット判定・変換統合処理
    観点: 2.1 正常系処理, 1.3 エラーハンドリング, 2.3 副作用チェック
    """

    def test_json_bytes_returns_json_with_overridden_device_id(self):
        """2.1.1: JSON形式のバイトデータはdevice_idを上書きしてJSONを返す"""
        # Arrange
        original_json = {"device_id": "12345", "external_temp": 25.5}
        raw_value = json.dumps(original_json).encode('utf-8')
        override_device_id = "99999"

        # Act
        result = convert_to_json_with_device_id(raw_value, override_device_id)

        # Assert
        parsed = json.loads(result)
        assert parsed["device_id"] == "99999"
        assert parsed["external_temp"] == 25.5

    def test_binary_data_converted_to_json(self):
        """2.1.2: バイナリ形式のデータはJSON形式に変換される"""
        # Arrange
        raw_value = make_valid_binary(device_id=12345)
        override_device_id = "99999"

        # Act
        result = convert_to_json_with_device_id(raw_value, override_device_id)

        # Assert
        assert result is not None
        parsed = json.loads(result)
        assert parsed["device_id"] == "99999"

    def test_none_raw_value_returns_none(self):
        """1.1.2: raw_valueがNoneの場合はNoneを返す"""
        # Arrange
        raw_value = None
        override_device_id = "12345"

        # Act
        result = convert_to_json_with_device_id(raw_value, override_device_id)

        # Assert
        assert result is None

    def test_invalid_binary_not_188_bytes_returns_none(self):
        """1.3: 188バイトでないバイナリ（UTF-8デコード失敗かつバイナリパース失敗）はNoneを返す"""
        # Arrange
        raw_value = b'\xff\xfe' + b'\x00' * 50  # 不正なUTF-8 + 不正サイズ

        # Act
        result = convert_to_json_with_device_id(raw_value, "12345")

        # Assert
        assert result is None

    def test_json_format_detected_correctly(self):
        """2.1.1: UTF-8デコード可能かつJSON形式のデータはJSON処理パスで処理される"""
        # Arrange
        json_data = '{"device_id": "111", "event_timestamp": "2026-01-23T10:30:00.000Z"}'
        raw_value = json_data.encode('utf-8')

        # Act
        result = convert_to_json_with_device_id(raw_value, None)

        # Assert
        parsed = json.loads(result)
        assert parsed["device_id"] == "111"  # override_device_idがNoneなので元のdevice_id

    def test_json_without_override_preserves_device_id(self):
        """2.1.2: override_device_idがNoneの場合、JSONのdevice_idはそのまま保持される"""
        # Arrange
        json_data = '{"device_id": "12345", "external_temp": 30.0}'
        raw_value = json_data.encode('utf-8')

        # Act
        result = convert_to_json_with_device_id(raw_value, None)

        # Assert
        parsed = json.loads(result)
        assert parsed["device_id"] == "12345"
