import re

from pyspark.sql import functions as F
from pyspark.sql.types import StringType 


def extract_device_id_from_topic(topic: str) -> str:
    """
    MQTT Topicから機器IDを抽出する

    Args:
        topic: MQTT Topic文字列（例: "/12345/data/refrigerator"）

    Returns:
        str: 機器ID。抽出失敗時はNone
    """
    if topic is None:
        return None

    pattern = r'^/(\d+)/data/refrigerator$'
    match = re.match(pattern, topic)

    if match:
        return match.group(1)
    return None


def extract_device_id_from_key(message_key: str) -> str:
    """
    EventHubメッセージのkeyからデバイスIDを抽出する

    Args:
        message_key: Kafkaメッセージのkey（文字列）

    Returns:
        str: デバイスID。抽出失敗時はNone
    """
    if message_key is None or message_key.strip() == "":
        return None

    try:
        int(message_key.strip())
        return message_key.strip()
    except ValueError:
        return None


def extract_device_id(topic: str, message_key: str, payload_device_id: str) -> str:
    """
    優先順位に従ってデバイスIDを抽出する

    優先順位:
    1. MQTT Topic（/<機器ID>/data/refrigerator形式）
    2. EventHub key
    3. ペイロード内のdevice_id

    Args:
        topic: MQTT Topic文字列
        message_key: Kafkaメッセージのkey
        payload_device_id: ペイロード内のdevice_id

    Returns:
        str: デバイスID。すべて失敗時はNone
    """
    device_id = extract_device_id_from_topic(topic)
    if device_id is not None:
        return device_id

    device_id = extract_device_id_from_key(message_key)
    if device_id is not None:
        return device_id

    if payload_device_id is not None and str(payload_device_id).strip() != "":
        return str(payload_device_id).strip()

    return None


# UDF登録
extract_device_id_from_topic_udf = F.udf(extract_device_id_from_topic, StringType())
extract_device_id_from_key_udf = F.udf(extract_device_id_from_key, StringType())
extract_device_id_udf = F.udf(extract_device_id, StringType())
