import json
import struct
from datetime import datetime, timezone

from pyspark.sql import functions as F
from pyspark.sql.types import StringType

from iot_app.ldp_pipeline.constants import BINARY_DATA_SIZE, BINARY_STRUCT_FORMAT, SENSOR_FIELDS


def is_valid_json(data: str) -> bool:
    """
    文字列が有効なJSONかどうかを判定する

    Args:
        data: 判定対象の文字列

    Returns:
        bool: 有効なJSONならTrue、それ以外はFalse
    """
    if data is None:
        return False
    try:
        json.loads(data)
        return True
    except (json.JSONDecodeError, TypeError):
        return False


def parse_binary_telemetry(binary_data: bytes, override_device_id: str = None) -> str:
    """
    バイナリ形式のテレメトリデータをJSON文字列に変換する

    Args:
        binary_data: バイナリ形式のテレメトリデータ（188バイト）
        override_device_id: 上書き用デバイスID（MQTT Topic/EventHub keyから抽出したID）

    Returns:
        str: JSON形式の文字列。パース失敗時はNone
    """
    if binary_data is None or len(binary_data) != BINARY_DATA_SIZE:
        return None

    try:
        unpacked = struct.unpack(BINARY_STRUCT_FORMAT, binary_data)

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

        result = {"device_id": device_id, "event_timestamp": event_timestamp}

        for i, field_name in enumerate(SENSOR_FIELDS):
            value = sensor_values[i]
            result[field_name] = None if value != value else value  # NaN → None

        return json.dumps(result)

    except (struct.error, ValueError, OverflowError):
        return None


def update_json_device_id(json_str: str, override_device_id: str) -> str:
    """
    JSON文字列内のdevice_idを上書きする

    Args:
        json_str: JSON形式のテレメトリデータ
        override_device_id: 上書き用デバイスID

    Returns:
        str: device_idを更新したJSON文字列
    """
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


def convert_to_json_with_device_id(raw_value: bytes, override_device_id: str) -> str:
    """
    テレメトリデータをJSON形式に変換し、デバイスIDを設定する

    処理フロー:
    1. バイナリデータを文字列にデコード試行
    2. 文字列がJSON形式ならデバイスIDを上書きして返却
    3. JSON形式でなければバイナリとしてパースしてJSONに変換（デバイスID上書き）

    Args:
        raw_value: Kafkaメッセージのvalue（バイナリ）
        override_device_id: 上書き用デバイスID

    Returns:
        str: JSON形式の文字列。変換失敗時はNone
    """
    if raw_value is None:
        return None

    try:
        decoded_str = raw_value.decode('utf-8')
        if is_valid_json(decoded_str):
            return update_json_device_id(decoded_str, override_device_id)
    except (UnicodeDecodeError, AttributeError):
        pass

    return parse_binary_telemetry(raw_value, override_device_id)


# UDF登録
is_valid_json_udf = F.udf(is_valid_json, "boolean")
parse_binary_telemetry_udf = F.udf(parse_binary_telemetry, StringType())
update_json_device_id_udf = F.udf(update_json_device_id, StringType())
convert_to_json_with_device_id_udf = F.udf(convert_to_json_with_device_id, StringType())
