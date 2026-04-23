# テスト項目書：シルバー層LDPパイプライン Service層

対象テストコード: `tests/unit/pipeline/silver/test_silver-ldp-pipeline_service.py`
参照観点表: `docs/05-testing/unit-test/unit-test-perspectives.md`
作成日: 2026-04-22

---

## TestExtractDeviceIdFromTopic

対象関数: `extract_device_id_from_topic(topic)` — MQTTトピックパス `^/([^/]+)/data/refrigerator$` からデバイスIDを抽出する

| No | テスト観点 | 操作手順 | 予想結果 | 実施結果 | 実施日時 | 実施者 | 備考 |
|----|-----------|---------|---------|---------|---------|-------|------|
| 1 | 2.1.1 正常系処理：有効な入力データ | `topic = "/12345/data/refrigerator"` を設定し、`extract_device_id_from_topic(topic)` を呼び出す | 戻り値が `"12345"` と等しい | | | | |
| 2 | 2.1.1 正常系処理：有効な入力データ | `topic = "/1/data/refrigerator"` を設定し、`extract_device_id_from_topic(topic)` を呼び出す | 戻り値が `"1"` と等しい（1桁の最小数値ID） | | | | |
| 3 | 2.1.1 正常系処理：有効な入力データ | `topic = "/9999999/data/refrigerator"` を設定し、`extract_device_id_from_topic(topic)` を呼び出す | 戻り値が `"9999999"` と等しい（大きな数値ID） | | | | |
| 4 | 1.1.1 必須チェック：None入力 | `topic = None` を設定し、`extract_device_id_from_topic(topic)` を呼び出す | 戻り値が `None` | | | | |
| 5 | 1.1.6 不整値チェック：未定義値 | `topic = "/invalid/path"` を設定し、`extract_device_id_from_topic(topic)` を呼び出す | 戻り値が `None`（`refrigerator` サフィックスなしのためパターン不一致） | | | | |
| 6 | 1.1.6 不整値チェック：未定義値 | `topic = "/12345/data/refrigerator/"` （末尾スラッシュ付き）を設定し、`extract_device_id_from_topic(topic)` を呼び出す | 戻り値が `None`（正規表現の終端アンカー `$` に不一致） | | | | |
| 7 | 1.1.6 不整値チェック：未定義値 | `topic = "/abc/def/data/refrigerator"` （デバイスIDにスラッシュ混入）を設定し、`extract_device_id_from_topic(topic)` を呼び出す | 戻り値が `None`（スラッシュを含まないパターン `[^/]+` に不一致） | | | | |
| 8 | 2.1.1 正常系処理：有効な入力データ | `topic = "/0100100101101011010/data/refrigerator"` を設定し、`extract_device_id_from_topic(topic)` を呼び出す | 戻り値が `"0100100101101011010"` と等しい | | | | |

---

## TestExtractDeviceIdFromKey

対象関数: `extract_device_id_from_key(message_key)` — EventHubメッセージキーからデバイスIDを抽出する

| No | テスト観点 | 操作手順 | 予想結果 | 実施結果 | 実施日時 | 実施者 | 備考 |
|----|-----------|---------|---------|---------|---------|-------|------|
| 9 | 2.1.1 正常系処理：有効な入力データ | `message_key = "12345"` を設定し、`extract_device_id_from_key(message_key)` を呼び出す | 戻り値が `"12345"` と等しい | | | | |
| 10 | 1.1.1 必須チェック：None入力 | `message_key = None` を設定し、`extract_device_id_from_key(message_key)` を呼び出す | 戻り値が `None` | | | | |
| 11 | 1.1.1 必須チェック：空文字入力 | `message_key = ""` を設定し、`extract_device_id_from_key(message_key)` を呼び出す | 戻り値が `None` | | | | |
| 12 | 1.1.1 必須チェック：空白のみ入力 | `message_key = "   "` を設定し、`extract_device_id_from_key(message_key)` を呼び出す | 戻り値が `None`（strip()後に空文字となるため） | | | | |
| 13 | 2.1.1 正常系処理：有効な入力データ | `message_key = "  12345  "` （前後に空白）を設定し、`extract_device_id_from_key(message_key)` を呼び出す | 戻り値が `"12345"` と等しい（strip()処理により前後空白が除去される） | | | | |
| 14 | 2.1.1 正常系処理：有効な入力データ | `message_key = "9999999"` を設定し、`extract_device_id_from_key(message_key)` を呼び出す | 戻り値が `"9999999"` と等しい（大きな数値デバイスID） | | | | |

---

## TestExtractDeviceId

対象関数: `extract_device_id(topic, message_key, payload_device_id)` — 優先度1=Topic、2=key、3=payloadの順でデバイスIDを抽出する統合処理

| No | テスト観点 | 操作手順 | 予想結果 | 実施結果 | 実施日時 | 実施者 | 備考 |
|----|-----------|---------|---------|---------|---------|-------|------|
| 15 | 2.1.1 正常系処理：有効な入力データ | `topic = "/11111/data/refrigerator"`, `message_key = "22222"`, `payload_device_id = "33333"` を設定し、`extract_device_id(topic, message_key, payload_device_id)` を呼び出す | 戻り値が `"11111"` と等しい（MQTTトピックからのIDが最優先） | | | | |
| 16 | 2.1.1 正常系処理：有効な入力データ | `topic = None`, `message_key = "22222"`, `payload_device_id = "33333"` を設定し、`extract_device_id(topic, message_key, payload_device_id)` を呼び出す | 戻り値が `"22222"` と等しい（TopicがNoneのためkeyを使用） | | | | |
| 17 | 2.1.1 正常系処理：有効な入力データ | `topic = "/not/valid/format"`, `message_key = "22222"`, `payload_device_id = "33333"` を設定し、`extract_device_id(topic, message_key, payload_device_id)` を呼び出す | 戻り値が `"22222"` と等しい（topicがパターン不一致のためkeyを使用） | | | | |
| 18 | 2.1.1 正常系処理：有効な入力データ | `topic = None`, `message_key = None`, `payload_device_id = "33333"` を設定し、`extract_device_id(topic, message_key, payload_device_id)` を呼び出す | 戻り値が `"33333"` と等しい（topic/key両方無効のためpayload_device_idをフォールバックとして使用） | | | | |
| 19 | 1.1.1 必須チェック：None入力 | `topic = None`, `message_key = None`, `payload_device_id = None` を設定し、`extract_device_id(topic, message_key, payload_device_id)` を呼び出す | 戻り値が `None`（すべての取得元が無効） | | | | |
| 20 | 1.1.1 必須チェック：空文字入力 | `topic = None`, `message_key = None`, `payload_device_id = ""` を設定し、`extract_device_id(topic, message_key, payload_device_id)` を呼び出す | 戻り値が `None`（空文字はフォールバックに使用しない） | | | | |
| 21 | 1.1.1 必須チェック：空白のみ入力 | `topic = None`, `message_key = None`, `payload_device_id = "   "` を設定し、`extract_device_id(topic, message_key, payload_device_id)` を呼び出す | 戻り値が `None`（空白のみはフォールバックに使用しない） | | | | |

---

## TestIsValidJson

対象関数: `is_valid_json(data)` — 入力がJSONとして解析可能かどうかを判定する

| No | テスト観点 | 操作手順 | 予想結果 | 実施結果 | 実施日時 | 実施者 | 備考 |
|----|-----------|---------|---------|---------|---------|-------|------|
| 22 | 2.1.1 正常系処理：有効な入力データ | `data = '{"device_id": 12345, "event_timestamp": "2026-01-23T10:30:00.000Z", "external_temp": 25.5}'` を設定し、`is_valid_json(data)` を呼び出す | 戻り値が `True` | | | | |
| 23 | 2.1.1 正常系処理：有効な入力データ | `data = "[1, 2, 3]"` を設定し、`is_valid_json(data)` を呼び出す | 戻り値が `True`（JSON配列も有効） | | | | |
| 24 | 1.1.1 必須チェック：None入力 | `data = None` を設定し、`is_valid_json(data)` を呼び出す | 戻り値が `False` | | | | |
| 25 | 1.1.1 必須チェック：空文字入力 | `data = ""` を設定し、`is_valid_json(data)` を呼び出す | 戻り値が `False` | | | | |
| 26 | 1.1.6 不整値チェック：未定義値 | `data = "{invalid json}"` を設定し、`is_valid_json(data)` を呼び出す | 戻り値が `False`（JSONDecodeError発生） | | | | |
| 27 | 1.1.6 不整値チェック：未定義値 | `data = "hello world"` を設定し、`is_valid_json(data)` を呼び出す | 戻り値が `False`（JSON形式でない平文） | | | | |

---

## TestParseBinaryTelemetry

対象関数: `parse_binary_telemetry(binary_data, override_device_id=None)` — 188バイトのバイナリテレメトリ（`<iq22d`）をJSON文字列に変換する

| No | テスト観点 | 操作手順 | 予想結果 | 実施結果 | 実施日時 | 実施者 | 備考 |
|----|-----------|---------|---------|---------|---------|-------|------|
| 28 | 2.1.1 正常系処理：有効な入力データ | `_make_binary_telemetry(device_id=12345)` で188バイトのバイナリデータを生成し、`parse_binary_telemetry(binary_data)` を呼び出す | 戻り値が `None` でなく、`json.loads()` でパース可能。パース結果に `"device_id"` と `"event_timestamp"` キーが含まれる | | | | |
| 29 | 2.1.2 正常系処理：最小構成の入力 | `_make_binary_telemetry()` でデフォルト値の188バイトバイナリデータを生成し、`parse_binary_telemetry(binary_data)` を呼び出す | `json.loads()` したパース結果に設計書定義の全22センサーフィールド（`external_temp` ～ `defrost_heater_output_2`）が含まれる | | | | |
| 30 | 1.1.1 必須チェック：None入力 | `binary_data = None` を設定し、`parse_binary_telemetry(binary_data)` を呼び出す | 戻り値が `None` | | | | |
| 31 | 1.3.1 エラーハンドリング：例外伝播 | `binary_data = b"\x00" * 100` （100バイト）を設定し、`parse_binary_telemetry(binary_data)` を呼び出す | 戻り値が `None`（188バイト未満のためサイズ検証失敗） | | | | |
| 32 | 1.1.1 必須チェック：空文字入力 | `binary_data = b""` （0バイト）を設定し、`parse_binary_telemetry(binary_data)` を呼び出す | 戻り値が `None` | | | | |
| 33 | 2.1.1 正常系処理：有効な入力データ | `_make_binary_telemetry(device_id=99999)` でバイナリデータを生成し、`parse_binary_telemetry(binary_data, "11111")` を呼び出す（override_device_id="11111"） | 戻り値が `None` でなく、パース結果の `str(device_id)` が `"11111"` と等しい（バイナリ内のdevice_idが上書きされる） | | | | |
| 34 | 2.1.1 正常系処理：有効な入力データ | `_make_binary_telemetry(device_id=12345)` でバイナリデータを生成し、`parse_binary_telemetry(binary_data, None)` を呼び出す（override_device_id=None） | 戻り値が `None` でなく、パース結果の `str(device_id)` が `"12345"` と等しい（バイナリ内のdevice_idがそのまま使用される） | | | | |
| 35 | 2.1.1 正常系処理：有効な入力データ | `_make_binary_telemetry(event_timestamp_ms=1737624600000)` でバイナリデータを生成し、`parse_binary_telemetry(binary_data)` を呼び出す | 戻り値が `None` でなく、パース結果の `"event_timestamp"` が `"2025-01-23T09:30:00.000Z"` と等しい | | | | |
| 36 | 2.1.1 正常系処理：有効な入力データ | `sensor_values = [float("nan")] + [25.5] * 21` でNaN混入データを作成し、`_make_binary_telemetry(sensor_values=sensor_values)` でバイナリデータを生成。`parse_binary_telemetry(binary_data)` を呼び出す | 戻り値が `None` でなく、パース結果の `"external_temp"` が `None`（NaN値はnullに変換される） | | | | |

---

## TestUpdateJsonDeviceId

対象関数: `update_json_device_id(json_str, override_device_id)` — JSON文字列内の `device_id` を `str(override_device_id)` で上書きする

| No | テスト観点 | 操作手順 | 予想結果 | 実施結果 | 実施日時 | 実施者 | 備考 |
|----|-----------|---------|---------|---------|---------|-------|------|
| 37 | 2.1.1 正常系処理：有効な入力データ | `json_str = json.dumps({"device_id": 99999, "event_timestamp": "2026-01-23T10:30:00.000Z"})`, `override_device_id = "12345"` を設定し、`update_json_device_id(json_str, override_device_id)` を呼び出す | 戻り値が `None` でなく、パース結果の `str(device_id)` が `"12345"` と等しい | | | | |
| 38 | 1.1.1 必須チェック：None入力 | `json_str = None`, `override_device_id = "12345"` を設定し、`update_json_device_id(json_str, override_device_id)` を呼び出す | 戻り値が `None` | | | | |
| 39 | 2.1.1 正常系処理：有効な入力データ | `json_str = json.dumps({"device_id": 99999, "event_timestamp": "2026-01-23T10:30:00.000Z"})`, `override_device_id = None` を設定し、`update_json_device_id(json_str, override_device_id)` を呼び出す | 戻り値が元の `json_str` と等しい（override_device_idがNoneのため変更なし） | | | | |
| 40 | 1.3.1 エラーハンドリング：例外伝播 | `json_str = "{invalid json}"`, `override_device_id = "12345"` を設定し、`update_json_device_id(json_str, override_device_id)` を呼び出す | 戻り値が元の `json_str` と等しい（JSONDecodeErrorをキャッチして元の文字列を返す） | | | | |
| 41 | 2.3.1 副作用チェック：処理後データ保持 | `original = {"device_id": 99999, "event_timestamp": "2026-01-23T10:30:00.000Z", "external_temp": 25.5, "internal_temp_freezer_1": -19.5}` をJSON化し `override_device_id = "12345"` を設定。`update_json_device_id(json_str, override_device_id)` を呼び出す | パース結果の `str(device_id)` が `"12345"` に更新され、`event_timestamp` が `"2026-01-23T10:30:00.000Z"`、`external_temp` が `25.5`、`internal_temp_freezer_1` が `-19.5` と等しい（device_id以外のフィールドが保持される） | | | | |

---

## TestConvertToJsonWithDeviceId

対象関数: `convert_to_json_with_device_id(raw_value, override_device_id)` — UTF-8+JSON変換を試み、失敗時はバイナリ解析にフォールバックする統合処理

| No | テスト観点 | 操作手順 | 予想結果 | 実施結果 | 実施日時 | 実施者 | 備考 |
|----|-----------|---------|---------|---------|---------|-------|------|
| 42 | 1.1.1 必須チェック：None入力 | `raw_value = None`, `override_device_id = "12345"` を設定し、`convert_to_json_with_device_id(raw_value, override_device_id)` を呼び出す | 戻り値が `None` | | | | |
| 43 | 2.1.1 正常系処理：有効な入力データ | `payload = {"device_id": 99999, "event_timestamp": "2026-01-23T10:30:00.000Z", "external_temp": 25.5}` をUTF-8エンコードしたバイト列と `override_device_id = "12345"` を設定し、`convert_to_json_with_device_id(raw_value, override_device_id)` を呼び出す | 戻り値が `None` でなく、パース結果の `str(device_id)` が `"12345"` と等しい（UTF-8+JSON処理フロー step2） | | | | |
| 44 | 2.1.1 正常系処理：有効な入力データ | `_make_binary_telemetry(device_id=12345)` で188バイトのバイナリデータと `override_device_id = "12345"` を設定し、`convert_to_json_with_device_id(raw_value, override_device_id)` を呼び出す | 戻り値が `None` でなく、パース結果に `"device_id"` と `"event_timestamp"` キーが含まれる（バイナリ解析フォールバック step3） | | | | |
| 45 | 1.3.1 エラーハンドリング：例外伝播 | `raw_value = b"\xFF\xFE\xFD"` （3バイトの不正バイナリ）と `override_device_id = "12345"` を設定し、`convert_to_json_with_device_id(raw_value, override_device_id)` を呼び出す | 戻り値が `None`（UTF-8デコード失敗かつバイナリパース失敗のためレコード破棄） | | | | |
| 46 | 2.1.1 正常系処理：有効な入力データ | `payload = {"device_id": 99999, "event_timestamp": "2026-01-23T10:30:00.000Z"}` をUTF-8エンコードと `override_device_id = None` を設定し、`convert_to_json_with_device_id(raw_value, override_device_id)` を呼び出す | 戻り値が `None` でなく、パース結果の `device_id` が `99999` と等しい（override_device_idがNoneのため元のdevice_idが保持される） | | | | |

---

## TestDetermineUpdatePattern

対象関数: `determine_update_pattern(threshold_exceeded, alert_triggered)` — 閾値超過フラグとアラート発報フラグから異常状態テーブルの更新パターンを判定する

| No | テスト観点 | 操作手順 | 予想結果 | 実施結果 | 実施日時 | 実施者 | 備考 |
|----|-----------|---------|---------|---------|---------|-------|------|
| 47 | 2.1.1 正常系処理：有効な入力データ | `threshold_exceeded = False`, `alert_triggered = False` を設定し、`determine_update_pattern(threshold_exceeded, alert_triggered)` を呼び出す | 戻り値が `"recovery"` と等しい（正常状態への復旧処理） | | | | |
| 48 | 2.1.1 正常系処理：有効な入力データ | `threshold_exceeded = False`, `alert_triggered = True` を設定し、`determine_update_pattern(threshold_exceeded, alert_triggered)` を呼び出す | 戻り値が `"recovery"` と等しい（閾値超過なしが最優先条件のため `alert_triggered` の値に関わらず復旧扱い） | | | | |
| 49 | 2.1.1 正常系処理：有効な入力データ | `threshold_exceeded = True`, `alert_triggered = True` を設定し、`determine_update_pattern(threshold_exceeded, alert_triggered)` を呼び出す | 戻り値が `"alert_fired"` と等しい（閾値超過かつアラート発報条件成立） | | | | |
| 50 | 2.1.1 正常系処理：有効な入力データ | `threshold_exceeded = True`, `alert_triggered = False` を設定し、`determine_update_pattern(threshold_exceeded, alert_triggered)` を呼び出す | 戻り値が `"abnormal_start"` と等しい（閾値超過かつアラート未発報） | | | | |
| 51 | 1.1.6 不整値チェック：許容値 | `(False, False)`, `(False, True)`, `(True, False)`, `(True, True)` の4通りの組み合わせで `determine_update_pattern(threshold_exceeded, alert_triggered)` を呼び出す | 全パターンの戻り値が `{"recovery", "alert_fired", "abnormal_start"}` のいずれかに含まれる | | | | |

---

## TestShouldEnqueueEmail

対象関数: `should_enqueue_email(alert_triggered, alert_email_flag)` — メール送信キュー登録対象かどうかを判定する（両方が `True` の場合のみ `True` を返す）

| No | テスト観点 | 操作手順 | 予想結果 | 実施結果 | 実施日時 | 実施者 | 備考 |
|----|-----------|---------|---------|---------|---------|-------|------|
| 52 | 2.1.1 正常系処理：有効な入力データ | `alert_triggered = True`, `alert_email_flag = True` を設定し、`should_enqueue_email(alert_triggered, alert_email_flag)` を呼び出す | 戻り値が `True`（メール送信キューへ登録する） | | | | |
| 53 | 2.1.1 正常系処理：有効な入力データ | `alert_triggered = False`, `alert_email_flag = True` を設定し、`should_enqueue_email(alert_triggered, alert_email_flag)` を呼び出す | 戻り値が `False`（アラート未発報のためキュー登録しない） | | | | |
| 54 | 2.1.1 正常系処理：有効な入力データ | `alert_triggered = True`, `alert_email_flag = False` を設定し、`should_enqueue_email(alert_triggered, alert_email_flag)` を呼び出す | 戻り値が `False`（メール通知設定がOFFのためキュー登録しない） | | | | |
| 55 | 2.1.1 正常系処理：有効な入力データ | `alert_triggered = False`, `alert_email_flag = False` を設定し、`should_enqueue_email(alert_triggered, alert_email_flag)` を呼び出す | 戻り値が `False` | | | | |
| 56 | 1.1.1 必須チェック：None入力 | `alert_triggered = None`, `alert_email_flag = True` を設定し、`should_enqueue_email(alert_triggered, alert_email_flag)` を呼び出す | 戻り値が `False`（`None is True` → `False`。厳密な `is True` 評価による） | | | | |
| 57 | 1.1.1 必須チェック：None入力 | `alert_triggered = True`, `alert_email_flag = None` を設定し、`should_enqueue_email(alert_triggered, alert_email_flag)` を呼び出す | 戻り値が `False`（`None is True` → `False`。厳密な `is True` 評価による） | | | | |

---

## TestIsRetryableError

対象関数: `is_retryable_error(error)` — リトライ可能なエラーかどうかを判定する（RETRYABLE_EXCEPTIONSまたはRETRYABLE_MYSQL_ERRNOS={2003,2006,2013}の場合True）

| No | テスト観点 | 操作手順 | 予想結果 | 実施結果 | 実施日時 | 実施者 | 備考 |
|----|-----------|---------|---------|---------|---------|-------|------|
| 58 | 1.3.1 エラーハンドリング：例外伝播 | `error = socket.timeout("Connection timed out")` を設定し、`is_retryable_error(error)` を呼び出す | 戻り値が `True`（socket.timeoutはリトライ対象） | | | | |
| 59 | 1.3.1 エラーハンドリング：例外伝播 | `error = ConnectionResetError("Connection reset by peer")` を設定し、`is_retryable_error(error)` を呼び出す | 戻り値が `True`（一時的なネットワークエラーのためリトライ対象） | | | | |
| 60 | 1.3.1 エラーハンドリング：例外伝播 | `error = BrokenPipeError("Broken pipe")` を設定し、`is_retryable_error(error)` を呼び出す | 戻り値が `True`（一時的なネットワークエラーのためリトライ対象） | | | | |
| 61 | 1.3.1 エラーハンドリング：例外伝播 | `error = OSError("Network unreachable")` を設定し、`is_retryable_error(error)` を呼び出す | 戻り値が `True`（一時的なネットワークエラーのためリトライ対象） | | | | |
| 62 | 1.3.1 エラーハンドリング：例外伝播 | `error = pymysql.err.OperationalError(2003, "Can't connect to MySQL server")` を設定し、`is_retryable_error(error)` を呼び出す | 戻り値が `True`（errno=2003「接続不可」はリトライ対象） | | | | |
| 63 | 1.3.1 エラーハンドリング：例外伝播 | `error = pymysql.err.OperationalError(2006, "MySQL server has gone away")` を設定し、`is_retryable_error(error)` を呼び出す | 戻り値が `True`（errno=2006「サーバー切断」はリトライ対象） | | | | |
| 64 | 1.3.1 エラーハンドリング：例外伝播 | `error = pymysql.err.OperationalError(2013, "Lost connection to MySQL server during query")` を設定し、`is_retryable_error(error)` を呼び出す | 戻り値が `True`（errno=2013「クエリ中切断」はリトライ対象） | | | | |
| 65 | 1.3.6 エラーハンドリング：AppError | `error = pymysql.err.OperationalError(1045, "Access denied for user")` を設定し、`is_retryable_error(error)` を呼び出す | 戻り値が `False`（errno=1045「認証エラー」はリトライ対象外） | | | | |
| 66 | 1.3.6 エラーハンドリング：AppError | `error = pymysql.err.ProgrammingError(1064, "SQL syntax error")` を設定し、`is_retryable_error(error)` を呼び出す | 戻り値が `False`（SQL構文エラーはリトライ対象外） | | | | |
| 67 | 1.3.6 エラーハンドリング：AppError | `error = pymysql.err.IntegrityError(1062, "Duplicate entry")` を設定し、`is_retryable_error(error)` を呼び出す | 戻り値が `False`（制約違反はリトライ対象外） | | | | |
| 68 | 1.3.6 エラーハンドリング：AppError | `error = ValueError("Invalid value")` を設定し、`is_retryable_error(error)` を呼び出す | 戻り値が `False`（一般的なPython例外はリトライ対象外） | | | | |
