"""
シルバー層LDPパイプライン - デバイスID抽出処理 単体テスト

対象関数:
    - extract_device_id_from_topic()
    - extract_device_id_from_key()
    - extract_device_id()

参照仕様書: docs/03-features/ldp-pipeline/silver-layer/ldp-pipeline-specification.md
            「デバイスID抽出処理」セクション
"""
import pytest
import re


# ============================================================
# テスト対象関数（仕様書記載の実装を直接定義）
# ============================================================

def extract_device_id_from_topic(topic: str):
    """MQTT Topicから機器IDを抽出する"""
    if topic is None:
        return None
    pattern = r'^/(\d+)/data/refrigerator$'
    match = re.match(pattern, topic)
    if match:
        return match.group(1)
    return None


def extract_device_id_from_key(message_key: str):
    """EventHubメッセージのkeyからデバイスIDを抽出する"""
    if message_key is None or message_key.strip() == "":
        return None
    try:
        int(message_key.strip())
        return message_key.strip()
    except ValueError:
        return None


def extract_device_id(topic: str, message_key: str, payload_device_id: str):
    """優先順位に従ってデバイスIDを抽出する"""
    device_id = extract_device_id_from_topic(topic)
    if device_id is not None:
        return device_id

    device_id = extract_device_id_from_key(message_key)
    if device_id is not None:
        return device_id

    if payload_device_id is not None and str(payload_device_id).strip() != "":
        return str(payload_device_id).strip()

    return None


# ============================================================
# extract_device_id_from_topic のテスト
# ============================================================

@pytest.mark.unit
class TestExtractDeviceIdFromTopic:
    """MQTT TopicからのデバイスID抽出処理
    観点: 2.1 正常系処理, 1.1.1 必須チェック, 1.3 エラーハンドリング
    """

    def test_valid_topic_extracts_device_id(self):
        """2.1.1: 正常なMQTT Topic形式からデバイスIDが抽出される"""
        # Arrange
        topic = "/12345/data/refrigerator"

        # Act
        result = extract_device_id_from_topic(topic)

        # Assert
        assert result == "12345"

    def test_valid_topic_single_digit_id(self):
        """2.1.2: 1桁のデバイスIDでも正常に抽出される"""
        # Arrange
        topic = "/1/data/refrigerator"

        # Act
        result = extract_device_id_from_topic(topic)

        # Assert
        assert result == "1"

    def test_valid_topic_large_id(self):
        """2.1.3: 大きな数値のデバイスIDが正常に抽出される"""
        # Arrange
        topic = "/9999999/data/refrigerator"

        # Act
        result = extract_device_id_from_topic(topic)

        # Assert
        assert result == "9999999"

    def test_none_topic_returns_none(self):
        """1.1.2: TopicがNoneの場合はNoneを返す"""
        # Arrange
        topic = None

        # Act
        result = extract_device_id_from_topic(topic)

        # Assert
        assert result is None

    def test_invalid_topic_format_no_leading_slash(self):
        """1.3: 先頭スラッシュがない不正なTopic形式はNoneを返す"""
        # Arrange
        topic = "12345/data/refrigerator"

        # Act
        result = extract_device_id_from_topic(topic)

        # Assert
        assert result is None

    def test_invalid_topic_wrong_path(self):
        """1.3: パス末尾が /data/refrigerator でない場合はNoneを返す"""
        # Arrange
        topic = "/12345/data/freezer"

        # Act
        result = extract_device_id_from_topic(topic)

        # Assert
        assert result is None

    def test_invalid_topic_alphabetic_id(self):
        """1.3: デバイスIDが数字以外の場合はNoneを返す"""
        # Arrange
        topic = "/abc/data/refrigerator"

        # Act
        result = extract_device_id_from_topic(topic)

        # Assert
        assert result is None

    def test_invalid_topic_extra_path_segment(self):
        """1.3: パスに余分なセグメントがある場合はNoneを返す"""
        # Arrange
        topic = "/12345/extra/data/refrigerator"

        # Act
        result = extract_device_id_from_topic(topic)

        # Assert
        assert result is None

    def test_empty_topic_returns_none(self):
        """1.1.1: 空文字のTopicはNoneを返す"""
        # Arrange
        topic = ""

        # Act
        result = extract_device_id_from_topic(topic)

        # Assert
        assert result is None


# ============================================================
# extract_device_id_from_key のテスト
# ============================================================

@pytest.mark.unit
class TestExtractDeviceIdFromKey:
    """EventHub keyからのデバイスID抽出処理
    観点: 2.1 正常系処理, 1.1.1 必須チェック, 1.3 エラーハンドリング
    """

    def test_valid_numeric_key_extracts_device_id(self):
        """2.1.1: 数値文字列のkeyからデバイスIDが抽出される"""
        # Arrange
        message_key = "12345"

        # Act
        result = extract_device_id_from_key(message_key)

        # Assert
        assert result == "12345"

    def test_key_with_whitespace_stripped(self):
        """2.1.2: 前後に空白があるkeyでもトリムして抽出される"""
        # Arrange
        message_key = "  12345  "

        # Act
        result = extract_device_id_from_key(message_key)

        # Assert
        assert result == "12345"

    def test_none_key_returns_none(self):
        """1.1.2: keyがNoneの場合はNoneを返す"""
        # Arrange
        message_key = None

        # Act
        result = extract_device_id_from_key(message_key)

        # Assert
        assert result is None

    def test_empty_key_returns_none(self):
        """1.1.1: 空文字のkeyはNoneを返す"""
        # Arrange
        message_key = ""

        # Act
        result = extract_device_id_from_key(message_key)

        # Assert
        assert result is None

    def test_whitespace_only_key_returns_none(self):
        """1.1.4: 空白のみのkeyはNoneを返す"""
        # Arrange
        message_key = "   "

        # Act
        result = extract_device_id_from_key(message_key)

        # Assert
        assert result is None

    def test_alphabetic_key_returns_none(self):
        """1.3: 英字を含むkeyはNoneを返す（数値以外は無効）"""
        # Arrange
        message_key = "abc123"

        # Act
        result = extract_device_id_from_key(message_key)

        # Assert
        assert result is None

    def test_alphanumeric_key_returns_none(self):
        """1.3: 英数字混在のkeyはNoneを返す"""
        # Arrange
        message_key = "device-12345"

        # Act
        result = extract_device_id_from_key(message_key)

        # Assert
        assert result is None

    def test_float_key_returns_none(self):
        """1.3: 小数点を含むkeyはNoneを返す"""
        # Arrange
        message_key = "123.45"

        # Act
        result = extract_device_id_from_key(message_key)

        # Assert
        assert result is None


# ============================================================
# extract_device_id のテスト（統合処理・優先順位）
# ============================================================

@pytest.mark.unit
class TestExtractDeviceId:
    """デバイスID抽出統合処理（優先順位判定）
    観点: 2.1 正常系処理, 1.3 エラーハンドリング
    """

    def test_priority1_topic_takes_precedence_over_key(self):
        """2.1.1: 優先度1 - MQTT TopicからデバイスIDが取得できる場合はTopicを優先する"""
        # Arrange
        topic = "/12345/data/refrigerator"
        message_key = "99999"
        payload_device_id = "77777"

        # Act
        result = extract_device_id(topic, message_key, payload_device_id)

        # Assert
        assert result == "12345"

    def test_priority2_key_used_when_topic_invalid(self):
        """2.1.2: 優先度2 - TopicからデバイスIDが取得できない場合はkeyを使用する"""
        # Arrange
        topic = "/invalid/topic"
        message_key = "99999"
        payload_device_id = "77777"

        # Act
        result = extract_device_id(topic, message_key, payload_device_id)

        # Assert
        assert result == "99999"

    def test_priority3_payload_used_as_fallback(self):
        """2.1.3: 優先度3 - Topic/keyともに無効な場合はペイロード内のdevice_idを使用する"""
        # Arrange
        topic = None
        message_key = None
        payload_device_id = "77777"

        # Act
        result = extract_device_id(topic, message_key, payload_device_id)

        # Assert
        assert result == "77777"

    def test_all_none_returns_none(self):
        """1.3: すべてのソースがNoneの場合はNoneを返す"""
        # Arrange
        topic = None
        message_key = None
        payload_device_id = None

        # Act
        result = extract_device_id(topic, message_key, payload_device_id)

        # Assert
        assert result is None

    def test_all_invalid_returns_none(self):
        """1.3: すべてのソースが不正な値の場合はNoneを返す"""
        # Arrange
        topic = "/invalid/topic"
        message_key = "not-a-number"
        payload_device_id = ""

        # Act
        result = extract_device_id(topic, message_key, payload_device_id)

        # Assert
        assert result is None

    def test_payload_device_id_stripped(self):
        """2.1.2: ペイロードdevice_idは前後空白をトリムして返す"""
        # Arrange
        topic = None
        message_key = None
        payload_device_id = "  12345  "

        # Act
        result = extract_device_id(topic, message_key, payload_device_id)

        # Assert
        assert result == "12345"

    def test_payload_whitespace_only_returns_none(self):
        """1.1.4: ペイロードdevice_idが空白のみの場合はNoneを返す"""
        # Arrange
        topic = None
        message_key = None
        payload_device_id = "   "

        # Act
        result = extract_device_id(topic, message_key, payload_device_id)

        # Assert
        assert result is None

    def test_topic_none_key_valid(self):
        """2.1.2: TopicがNoneでkeyが有効な場合はkeyからデバイスIDを取得する"""
        # Arrange
        topic = None
        message_key = "54321"
        payload_device_id = None

        # Act
        result = extract_device_id(topic, message_key, payload_device_id)

        # Assert
        assert result == "54321"
