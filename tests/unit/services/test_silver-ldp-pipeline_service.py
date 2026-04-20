"""
シルバー層LDPパイプライン サービス層 - 単体テスト
対象モジュール: silver_ldp_pipeline.pipeline
設計書: docs/03-features/ldp-pipeline/silver-layer/ldp-pipeline-specification.md
"""

import json
import struct
import pytest

# NOTE: 実装前のテストファースト。実装後は以下のインポートが有効になる
# from silver_ldp_pipeline.pipeline import (
#     extract_device_id_from_topic,
#     extract_device_id_from_key,
#     extract_device_id,
#     is_valid_json,
#     parse_binary_telemetry,
#     update_json_device_id,
#     convert_to_json_with_device_id,
# )

# ---------------------------------------------------------------------------
# テスト用ヘルパー: 188バイトのバイナリテレメトリデータを生成
# ---------------------------------------------------------------------------

def _make_binary_telemetry(device_id=12345, event_timestamp_ms=1737624600000, sensor_values=None):
    """テスト用バイナリテレメトリデータ（188バイト）を生成する。

    バイナリフォーマット（リトルエンディアン）:
        i  = device_id (INT32, 4バイト)
        q  = event_timestamp (INT64, 8バイト, ミリ秒)
        22d = 22個のDOUBLE型センサー値 (8バイト × 22 = 176バイト)
    合計: 4 + 8 + 176 = 188バイト
    """
    if sensor_values is None:
        sensor_values = [25.5, -20.0, -19.8, -19.5, -15.2, 35.0, -19.7,
                         -25.0, -24.6, -24.3, -18.5, 38.0, -24.5,
                         2800.0, 3100.0, 1200.0, 1180.0, 1150.0, 1220.0, 1190.0,
                         0.0, 0.0]
    return struct.pack('<iq22d', device_id, event_timestamp_ms, *sensor_values)


# ===========================================================================
# STEP 1.5: デバイスID抽出処理
# 設計書: § デバイスID抽出処理
# ===========================================================================

@pytest.mark.unit
class TestExtractDeviceIdFromTopic:
    """MQTT TopicからデバイスIDを抽出する

    観点: データ変換仕様 > デバイスID抽出処理 > MQTT TopicからのデバイスID抽出
    対応観点表: 1.1.1（必須チェック）, 1.1.6（不整値チェック）
    """

    def test_valid_mqtt_topic_returns_device_id(self):
        """2.1.1: 正常なMQTT Topic形式の場合、デバイスIDが返される

        実行内容: /12345/data/refrigerator を入力
        想定結果: "12345" が返される
        """
        from silver_ldp_pipeline.pipeline import extract_device_id_from_topic
        # Arrange
        topic = "/12345/data/refrigerator"
        # Act
        result = extract_device_id_from_topic(topic)
        # Assert
        assert result == "12345"

    def test_none_topic_returns_none(self):
        """1.1.1 (1.1.2): Noneが渡された場合、Noneが返される

        実行内容: topic = None を入力
        想定結果: None が返される
        """
        from silver_ldp_pipeline.pipeline import extract_device_id_from_topic
        # Arrange
        topic = None
        # Act
        result = extract_device_id_from_topic(topic)
        # Assert
        assert result is None

    def test_invalid_format_returns_none(self):
        """1.1.6 (1.6.2): パターンに一致しないTopicの場合、Noneが返される

        実行内容: /invalid/path を入力（refrigerator パスなし）
        想定結果: None が返される
        """
        from silver_ldp_pipeline.pipeline import extract_device_id_from_topic
        # Arrange
        topic = "/invalid/path"
        # Act
        result = extract_device_id_from_topic(topic)
        # Assert
        assert result is None

    def test_non_numeric_device_id_returns_none(self):
        """1.1.6 (1.6.2): デバイスIDが数字以外の場合、Noneが返される

        実行内容: /abc/data/refrigerator を入力（アルファベットID）
        想定結果: None が返される（正規表現 r'^/(\d+)/data/refrigerator$' に不一致）
        """
        from silver_ldp_pipeline.pipeline import extract_device_id_from_topic
        # Arrange
        topic = "/abc/data/refrigerator"
        # Act
        result = extract_device_id_from_topic(topic)
        # Assert
        assert result is None

    def test_trailing_slash_returns_none(self):
        """1.1.6 (1.6.2): 末尾にスラッシュがある場合、Noneが返される

        実行内容: /12345/data/refrigerator/ を入力（末尾スラッシュ）
        想定結果: None が返される（正規表現 $ に不一致）
        """
        from silver_ldp_pipeline.pipeline import extract_device_id_from_topic
        # Arrange
        topic = "/12345/data/refrigerator/"
        # Act
        result = extract_device_id_from_topic(topic)
        # Assert
        assert result is None

    def test_large_device_id_returns_correctly(self):
        """2.1.1: 大きな数値IDも正常に抽出される

        実行内容: /9999999/data/refrigerator を入力
        想定結果: "9999999" が返される
        """
        from silver_ldp_pipeline.pipeline import extract_device_id_from_topic
        # Arrange
        topic = "/9999999/data/refrigerator"
        # Act
        result = extract_device_id_from_topic(topic)
        # Assert
        assert result == "9999999"


@pytest.mark.unit
class TestExtractDeviceIdFromKey:
    """EventHubメッセージのkeyからデバイスIDを抽出する

    観点: データ変換仕様 > デバイスID抽出処理 > EventHub keyからのデバイスID抽出
    対応観点表: 1.1.1（必須チェック）, 1.1.6（不整値チェック）
    """

    def test_valid_numeric_key_returns_device_id(self):
        """2.1.1: 数値文字列のkeyが渡された場合、デバイスIDが返される

        実行内容: message_key = "12345" を入力
        想定結果: "12345" が返される
        """
        from silver_ldp_pipeline.pipeline import extract_device_id_from_key
        # Arrange
        message_key = "12345"
        # Act
        result = extract_device_id_from_key(message_key)
        # Assert
        assert result == "12345"

    def test_none_key_returns_none(self):
        """1.1.1 (1.1.2): Noneが渡された場合、Noneが返される

        実行内容: message_key = None を入力
        想定結果: None が返される
        """
        from silver_ldp_pipeline.pipeline import extract_device_id_from_key
        # Arrange
        message_key = None
        # Act
        result = extract_device_id_from_key(message_key)
        # Assert
        assert result is None

    def test_empty_string_key_returns_none(self):
        """1.1.1 (1.1.1): 空文字が渡された場合、Noneが返される

        実行内容: message_key = "" を入力
        想定結果: None が返される
        """
        from silver_ldp_pipeline.pipeline import extract_device_id_from_key
        # Arrange
        message_key = ""
        # Act
        result = extract_device_id_from_key(message_key)
        # Assert
        assert result is None

    def test_whitespace_only_key_returns_none(self):
        """1.1.1 (1.1.4): 空白のみの場合、Noneが返される

        実行内容: message_key = "   " を入力
        想定結果: None が返される
        """
        from silver_ldp_pipeline.pipeline import extract_device_id_from_key
        # Arrange
        message_key = "   "
        # Act
        result = extract_device_id_from_key(message_key)
        # Assert
        assert result is None

    def test_non_numeric_key_returns_none(self):
        """1.1.6 (1.6.2): 数値以外の文字列が渡された場合、Noneが返される

        実行内容: message_key = "device-abc" を入力
        想定結果: None が返される（int() 変換失敗）
        """
        from silver_ldp_pipeline.pipeline import extract_device_id_from_key
        # Arrange
        message_key = "device-abc"
        # Act
        result = extract_device_id_from_key(message_key)
        # Assert
        assert result is None


@pytest.mark.unit
class TestExtractDeviceId:
    """優先順位に従ってデバイスIDを抽出する統合処理

    観点: データ変換仕様 > デバイスID抽出処理 > デバイスID抽出の統合処理
    対応観点表: 2.1（正常系処理）, 1.1.1（必須チェック）
    優先順位: 1. MQTT Topic, 2. EventHub key, 3. ペイロード内device_id
    """

    def test_mqtt_topic_takes_priority_over_key(self):
        """2.1.1: MQTT Topicからの抽出が最優先（優先度1）

        実行内容: 有効なtopicと有効なkeyを同時に渡す
        想定結果: topicから抽出したデバイスIDが返される
        """
        from silver_ldp_pipeline.pipeline import extract_device_id
        # Arrange
        topic = "/11111/data/refrigerator"
        message_key = "22222"
        payload_device_id = "33333"
        # Act
        result = extract_device_id(topic, message_key, payload_device_id)
        # Assert
        assert result == "11111"

    def test_event_hub_key_used_when_topic_is_none(self):
        """2.1.1: MQTT Topic無効時にEventHub keyを使用（優先度2）

        実行内容: topicがNone、有効なkeyとpayload_device_idを渡す
        想定結果: keyから抽出したデバイスIDが返される
        """
        from silver_ldp_pipeline.pipeline import extract_device_id
        # Arrange
        topic = None
        message_key = "22222"
        payload_device_id = "33333"
        # Act
        result = extract_device_id(topic, message_key, payload_device_id)
        # Assert
        assert result == "22222"

    def test_payload_device_id_used_as_fallback(self):
        """2.1.1: Topic/key無効時にペイロードのdevice_idを使用（優先度3）

        実行内容: topicがNone、keyがNone、有効なpayload_device_idを渡す
        想定結果: payload_device_idが返される
        """
        from silver_ldp_pipeline.pipeline import extract_device_id
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

        実行内容: topic/message_key/payload_device_id すべてNone
        想定結果: None が返される
        """
        from silver_ldp_pipeline.pipeline import extract_device_id
        # Arrange
        topic = None
        message_key = None
        payload_device_id = None
        # Act
        result = extract_device_id(topic, message_key, payload_device_id)
        # Assert
        assert result is None


# ===========================================================================
# STEP 1.6: バイナリ/JSON判定・変換処理
# 設計書: § バイナリ/JSON判定・変換処理
# ===========================================================================

@pytest.mark.unit
class TestIsValidJson:
    """文字列が有効なJSONかどうかを判定する

    観点: データ変換仕様 > バイナリ/JSON判定・変換処理 > フォーマット判定ロジック
    対応観点表: 1.1.1（必須チェック）, 1.1.6（不整値チェック）
    """

    def test_valid_json_object_returns_true(self):
        """2.1.1: 有効なJSONオブジェクト文字列の場合、Trueが返される

        実行内容: '{"key": "value"}' を入力
        想定結果: True が返される
        """
        from silver_ldp_pipeline.pipeline import is_valid_json
        # Arrange
        data = '{"device_id": 12345, "event_timestamp": "2026-01-23T10:30:00.000Z"}'
        # Act
        result = is_valid_json(data)
        # Assert
        assert result is True

    def test_none_returns_false(self):
        """1.1.1 (1.1.2): Noneが渡された場合、Falseが返される

        実行内容: data = None を入力
        想定結果: False が返される
        """
        from silver_ldp_pipeline.pipeline import is_valid_json
        # Arrange
        data = None
        # Act
        result = is_valid_json(data)
        # Assert
        assert result is False

    def test_invalid_json_string_returns_false(self):
        """1.1.6 (1.6.2): 無効なJSON文字列の場合、Falseが返される

        実行内容: '{invalid json}' を入力
        想定結果: False が返される
        """
        from silver_ldp_pipeline.pipeline import is_valid_json
        # Arrange
        data = '{invalid json}'
        # Act
        result = is_valid_json(data)
        # Assert
        assert result is False

    def test_empty_string_returns_false(self):
        """1.1.1 (1.1.1): 空文字が渡された場合、Falseが返される

        実行内容: data = "" を入力
        想定結果: False が返される
        """
        from silver_ldp_pipeline.pipeline import is_valid_json
        # Arrange
        data = ""
        # Act
        result = is_valid_json(data)
        # Assert
        assert result is False

    def test_valid_json_array_returns_true(self):
        """2.1.1: 有効なJSON配列文字列の場合、Trueが返される

        実行内容: '[1, 2, 3]' を入力
        想定結果: True が返される
        """
        from silver_ldp_pipeline.pipeline import is_valid_json
        # Arrange
        data = '[1, 2, 3]'
        # Act
        result = is_valid_json(data)
        # Assert
        assert result is True


@pytest.mark.unit
class TestParseBinaryTelemetry:
    """バイナリ形式のテレメトリデータをJSON文字列に変換する

    観点: データ変換仕様 > バイナリ/JSON判定・変換処理 > バイナリ→JSON変換処理
    対応観点表: 2.1（正常系処理）, 1.1.1（必須チェック）, 1.3（エラーハンドリング）
    バイナリフォーマット: リトルエンディアン '<iq22d' (188バイト)
    """

    def test_valid_binary_returns_json_string(self):
        """2.1.1: 188バイトの正常なバイナリデータの場合、JSON文字列が返される

        実行内容: 正常な188バイトのバイナリデータを入力
        想定結果: JSON文字列が返される（device_id/event_timestamp/センサー値を含む）
        """
        from silver_ldp_pipeline.pipeline import parse_binary_telemetry
        # Arrange
        binary_data = _make_binary_telemetry(device_id=12345)
        # Act
        result = parse_binary_telemetry(binary_data)
        # Assert
        assert result is not None
        parsed = json.loads(result)
        assert "device_id" in parsed
        assert "event_timestamp" in parsed

    def test_none_binary_returns_none(self):
        """1.1.1 (1.1.2): Noneが渡された場合、Noneが返される

        実行内容: binary_data = None を入力
        想定結果: None が返される
        """
        from silver_ldp_pipeline.pipeline import parse_binary_telemetry
        # Arrange
        binary_data = None
        # Act
        result = parse_binary_telemetry(binary_data)
        # Assert
        assert result is None

    def test_wrong_size_binary_returns_none(self):
        """1.3.1: 188バイトでないバイナリデータの場合、Noneが返される

        実行内容: 100バイトのバイナリデータを入力
        想定結果: None が返される（サイズ検証失敗）
        """
        from silver_ldp_pipeline.pipeline import parse_binary_telemetry
        # Arrange
        binary_data = b'\x00' * 100
        # Act
        result = parse_binary_telemetry(binary_data)
        # Assert
        assert result is None

    def test_override_device_id_is_applied(self):
        """2.1.1: override_device_idが指定された場合、バイナリ内のdevice_idが上書きされる

        実行内容: device_id=99999のバイナリデータとoverride_device_id="11111"を入力
        想定結果: 返却JSONのdevice_idが"11111"で上書きされる
        """
        from silver_ldp_pipeline.pipeline import parse_binary_telemetry
        # Arrange
        binary_data = _make_binary_telemetry(device_id=99999)
        override_device_id = "11111"
        # Act
        result = parse_binary_telemetry(binary_data, override_device_id)
        # Assert
        assert result is not None
        parsed = json.loads(result)
        assert str(parsed["device_id"]) == "11111"

    def test_no_override_uses_binary_device_id(self):
        """2.1.1: override_device_idが省略された場合、バイナリ内のdevice_idが使用される

        実行内容: device_id=12345のバイナリデータとoverride_device_id=Noneを入力
        想定結果: 返却JSONのdevice_idが12345になる
        """
        from silver_ldp_pipeline.pipeline import parse_binary_telemetry
        # Arrange
        binary_data = _make_binary_telemetry(device_id=12345)
        # Act
        result = parse_binary_telemetry(binary_data, None)
        # Assert
        assert result is not None
        parsed = json.loads(result)
        assert parsed["device_id"] == "12345"


@pytest.mark.unit
class TestUpdateJsonDeviceId:
    """JSON文字列内のdevice_idを上書きする

    観点: データ変換仕様 > バイナリ/JSON判定・変換処理 > JSON形式へのデバイスID上書き処理
    対応観点表: 2.1（正常系処理）, 1.1.1（必須チェック）, 1.3（エラーハンドリング）
    """

    def test_valid_json_and_override_id_updates_device_id(self):
        """2.1.1 / 3.3.2.1: 有効なJSONとoverride_device_idの場合、device_idが整数型で更新される

        実行内容: device_id=99999のJSONと override_device_id="12345"を入力
        想定結果: JSONのdevice_idが12345（int）に更新される
        """
        from silver_ldp_pipeline.pipeline import update_json_device_id
        # Arrange
        json_str = json.dumps({"device_id": 99999, "event_timestamp": "2026-01-23T10:30:00.000Z"})
        override_device_id = "12345"
        # Act
        result = update_json_device_id(json_str, override_device_id)
        # Assert
        assert result is not None
        parsed = json.loads(result)
        assert parsed["device_id"] == 12345

    def test_none_json_str_returns_none(self):
        """1.1.1 (1.1.2): json_strがNoneの場合、Noneが返される

        実行内容: json_str = None を入力
        想定結果: None が返される
        """
        from silver_ldp_pipeline.pipeline import update_json_device_id
        # Arrange
        json_str = None
        override_device_id = "12345"
        # Act
        result = update_json_device_id(json_str, override_device_id)
        # Assert
        assert result is None

    def test_none_override_returns_original_json(self):
        """2.1.1: override_device_idがNoneの場合、元のJSON文字列がそのまま返される

        実行内容: 有効なjson_strとoverride_device_id=Noneを入力
        想定結果: 元のjson_strがそのまま返される
        """
        from silver_ldp_pipeline.pipeline import update_json_device_id
        # Arrange
        json_str = json.dumps({"device_id": 99999, "event_timestamp": "2026-01-23T10:30:00.000Z"})
        override_device_id = None
        # Act
        result = update_json_device_id(json_str, override_device_id)
        # Assert
        assert result == json_str

    def test_invalid_json_returns_original_string(self):
        """1.3.1: json_strが無効なJSONの場合、元の文字列がそのまま返される

        実行内容: 無効なjson_strを入力
        想定結果: 元の文字列がそのまま返される（JSONDecodeErrorをキャッチ）
        """
        from silver_ldp_pipeline.pipeline import update_json_device_id
        # Arrange
        json_str = "{invalid json}"
        override_device_id = "12345"
        # Act
        result = update_json_device_id(json_str, override_device_id)
        # Assert
        assert result == json_str


@pytest.mark.unit
class TestConvertToJsonWithDeviceId:
    """テレメトリデータをJSON形式に変換し、デバイスIDを設定する統合処理

    観点: データ変換仕様 > バイナリ/JSON判定・変換処理 > フォーマット判定・変換の統合処理
    対応観点表: 2.1（正常系処理）, 1.1.1（必須チェック）, 1.3（エラーハンドリング）
    処理フロー:
        1. バイナリをUTF-8文字列にデコード試行
        2. JSON形式ならdevice_idを上書きして返却
        3. JSON形式でなければバイナリとしてパースしてJSONに変換
    """

    def test_none_raw_value_returns_none(self):
        """1.1.1 (1.1.2): raw_valueがNoneの場合、Noneが返される

        実行内容: raw_value = None を入力
        想定結果: None が返される
        """
        from silver_ldp_pipeline.pipeline import convert_to_json_with_device_id
        # Arrange
        raw_value = None
        override_device_id = "12345"
        # Act
        result = convert_to_json_with_device_id(raw_value, override_device_id)
        # Assert
        assert result is None

    def test_valid_json_bytes_returns_updated_json(self):
        """2.1.1: UTF-8エンコードされた有効なJSONバイトの場合、device_idが更新されたJSONが返される

        実行内容: 有効なJSONのバイト列とoverride_device_idを入力
        想定結果: device_idが上書きされたJSON文字列が返される
        """
        from silver_ldp_pipeline.pipeline import convert_to_json_with_device_id
        # Arrange
        payload = {"device_id": 99999, "event_timestamp": "2026-01-23T10:30:00.000Z", "external_temp": 25.5}
        raw_value = json.dumps(payload).encode('utf-8')
        override_device_id = "12345"
        # Act
        result = convert_to_json_with_device_id(raw_value, override_device_id)
        # Assert
        assert result is not None
        parsed = json.loads(result)
        assert parsed["device_id"] == 12345

    def test_binary_format_returns_converted_json(self):
        """2.1.1: バイナリ形式のデータの場合、JSON変換されたデータが返される

        実行内容: 188バイトのバイナリテレメトリデータを入力
        想定結果: JSON文字列が返される
        """
        from silver_ldp_pipeline.pipeline import convert_to_json_with_device_id
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

    def test_invalid_binary_and_non_json_returns_none(self):
        """1.3.1: UTF-8デコード失敗かつバイナリパース失敗の場合、Noneが返される

        実行内容: 変換不能なバイナリデータ（188バイト以外）を入力
        想定結果: None が返される
        """
        from silver_ldp_pipeline.pipeline import convert_to_json_with_device_id
        # Arrange
        raw_value = b'\xFF\xFE\xFD'  # 不正なバイナリデータ（3バイト、188バイト未満）
        override_device_id = "12345"
        # Act
        result = convert_to_json_with_device_id(raw_value, override_device_id)
        # Assert
        assert result is None

    def test_json_bytes_without_override_id_keeps_original(self):
        """2.1.1: override_device_idがNoneの場合、元のJSONのdevice_idが保持される

        実行内容: 有効なJSONのバイト列とoverride_device_id=Noneを入力
        想定結果: 元のdevice_idが保持されたJSON文字列が返される
        """
        from silver_ldp_pipeline.pipeline import convert_to_json_with_device_id
        # Arrange
        payload = {"device_id": 99999, "event_timestamp": "2026-01-23T10:30:00.000Z"}
        raw_value = json.dumps(payload).encode('utf-8')
        override_device_id = None
        # Act
        result = convert_to_json_with_device_id(raw_value, override_device_id)
        # Assert
        assert result is not None
        parsed = json.loads(result)
        assert parsed["device_id"] == 99999
