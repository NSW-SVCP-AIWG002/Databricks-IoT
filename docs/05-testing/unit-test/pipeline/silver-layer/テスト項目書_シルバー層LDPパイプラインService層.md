# テスト項目書 - silver-ldp-pipeline

- **対象ファイル**:
  - `src/pipeline/silver/functions/device_id_extraction.py`
  - `src/pipeline/silver/functions/json_telemetry.py`
  - `src/pipeline/silver/functions/alert_judgment.py`
  - `src/pipeline/silver/functions/mysql_connector.py`
- **テストコード**: `/workspaces/Databricks-IoT/tests/unit/pipeline/silver/test_silver-ldp-pipeline_service.py`
- **観点表**: `docs/05-testing/unit-test/unit-test-perspectives.md`
- **ワークフロー仕様書**: `/workspaces/Databricks-IoT/docs/03-features/ldp-pipeline/silver-layer/ldp-pipeline-specification.md`

---

## 対応表

テストクラスと、ワークフロー仕様書の各ワークフロー・処理フロー項目の対応を示します。

| テストクラス | テスト項目No. | 対応ワークフロー | 処理フロー項目 | エンドポイント |
|---|:---:|---|---|---|
| TestExtractDeviceIdFromTopic | 1〜11 | シルバー層LDPパイプライン | STEP 1.5: デバイスID抽出 > MQTT TopicからのデバイスID抽出 | `extract_device_id_from_topic()` |
| TestExtractDeviceIdFromKey | 12〜17 | シルバー層LDPパイプライン | STEP 1.5: デバイスID抽出 > EventHub keyからのデバイスID抽出 | `extract_device_id_from_key()` |
| TestExtractDeviceId | 18〜24 | シルバー層LDPパイプライン | STEP 1.5: デバイスID抽出 > デバイスID抽出の統合処理 | `extract_device_id()` |
| TestIsValidJson | 25〜30 | シルバー層LDPパイプライン | STEP 1.6: バイナリ/JSON判定・変換 > フォーマット判定ロジック | `is_valid_json()` |
| TestParseBinaryTelemetry | 31〜39 | シルバー層LDPパイプライン | STEP 1.6: バイナリ/JSON判定・変換 > バイナリ→JSON変換処理 | `parse_binary_telemetry()` |
| TestUpdateJsonDeviceId | 40〜46 | シルバー層LDPパイプライン | STEP 1.6: バイナリ/JSON判定・変換 > JSON形式へのデバイスID上書き処理 | `update_json_device_id()` |
| TestConvertToJsonWithDeviceId | 47〜51 | シルバー層LDPパイプライン | STEP 1.6: バイナリ/JSON判定・変換 > フォーマット判定・変換の統合処理 | `convert_to_json_with_device_id()` |
| TestGetAlertAbnormalState | 52〜53 | シルバー層LDPパイプライン | STEP 4: アラート判定 > 異常状態テーブル取得（マスタデータ取得） | `get_alert_abnormal_state()` |
| TestDetermineUpdatePattern | 54〜57 | シルバー層LDPパイプライン | STEP 4: アラート判定 > 異常状態テーブル更新処理（更新パターン判定） | `determine_update_pattern()` |
| TestShouldEnqueueEmail | 58〜63 | シルバー層LDPパイプライン | STEP 4: アラート判定 > メール送信キュー登録 > キュー登録の設計方針 | `should_enqueue_email()` |
| TestIsRetryableError | 64〜74 | シルバー層LDPパイプライン | 外部連携仕様 > OLTPリトライ戦略 | `is_retryable_error()` |
| TestGetMysqlConnection | 75〜79 | シルバー層LDPパイプライン | 外部連携仕様 > OLTPリトライ戦略 | `get_mysql_connection()` |
| TestUpdateAlertAbnormalState | 80〜83 | シルバー層LDPパイプライン | STEP 5b: 外部連携出力 > 異常状態テーブル更新処理 | `update_alert_abnormal_state()` |
| TestEnqueueEmailNotification | 84〜86 | シルバー層LDPパイプライン | STEP 5b: 外部連携出力 > メール送信キュー登録処理 | `enqueue_email_notification()` |
| TestUpdateDeviceStatus | 87〜90 | シルバー層LDPパイプライン | STEP 5b: 外部連携出力 > デバイスステータス更新 | `update_device_status()` |
| TestInsertAlertHistory | 91〜93 | シルバー層LDPパイプライン | STEP 5b: 外部連携出力 > アラート履歴登録処理（アラート発報時） | `insert_alert_history()` |
| TestUpdateAlertHistoryOnRecovery | 94〜96 | シルバー層LDPパイプライン | STEP 5b: 外部連携出力 > アラート履歴更新処理（復旧時） | `update_alert_history_on_recovery()` |

---

## ワークフロー別カバレッジ

ワークフロー仕様書の各ワークフローに対して、どのテストクラスが対応しているかを示します。

### シルバー層LDPパイプライン

#### STEP 1.5: デバイスID抽出

| 処理フロー項目 | 対応テストクラス | テスト項目No. |
|---|---|:---:|
| MQTT TopicからのデバイスID抽出 | TestExtractDeviceIdFromTopic | 1〜11 |
| EventHub keyからのデバイスID抽出 | TestExtractDeviceIdFromKey | 12〜17 |
| デバイスID抽出の統合処理 | TestExtractDeviceId | 18〜24 |

#### STEP 1.6: バイナリ/JSON判定・変換

| 処理フロー項目 | 対応テストクラス | テスト項目No. |
|---|---|:---:|
| フォーマット判定ロジック | TestIsValidJson | 25〜30 |
| バイナリ→JSON変換処理 | TestParseBinaryTelemetry | 31〜39 |
| JSON形式へのデバイスID上書き処理 | TestUpdateJsonDeviceId | 40〜46 |
| フォーマット判定・変換の統合処理 | TestConvertToJsonWithDeviceId | 47〜51 |

#### STEP 4: アラート判定

| 処理フロー項目 | 対応テストクラス | テスト項目No. |
|---|---|:---:|
| 異常状態テーブル取得（マスタデータ取得） | TestGetAlertAbnormalState | 52〜53 |
| 異常状態テーブル更新パターン判定 | TestDetermineUpdatePattern | 54〜57 |
| メール送信キュー登録条件判定 | TestShouldEnqueueEmail | 58〜63 |

#### 外部連携仕様 > OLTPリトライ戦略

| 処理フロー項目 | 対応テストクラス | テスト項目No. |
|---|---|:---:|
| リトライ対象エラー判定 | TestIsRetryableError | 64〜74 |
| MySQL接続コンテキストマネージャ（リトライ） | TestGetMysqlConnection | 75〜79 |

#### STEP 5b: 外部連携出力処理

| 処理フロー項目 | 対応テストクラス | テスト項目No. |
|---|---|:---:|
| 異常状態テーブル更新 | TestUpdateAlertAbnormalState | 80〜83 |
| メール送信キュー登録 | TestEnqueueEmailNotification | 84〜86 |
| デバイスステータス更新 | TestUpdateDeviceStatus | 87〜90 |
| アラート履歴登録（発報時） | TestInsertAlertHistory | 91〜93 |
| アラート履歴更新（復旧時） | TestUpdateAlertHistoryOnRecovery | 94〜96 |

---

## テストクラス一覧

テストクラスに対して、テスト観点、操作手順、予想結果を示します。

---

### TestExtractDeviceIdFromTopic

**観点**: データ変換仕様 > デバイスID抽出処理 > MQTT TopicからのデバイスID抽出

| No | テスト観点 | 操作手順 | 予想結果 |
|---|---|---|---|
| 1 | 2.1.1 正常系処理：有効な入力データ | `topic = "/12345/data/refrigerator"` を設定し、`extract_device_id_from_topic(topic)` を呼び出す | `"12345"` が返される |
| 2 | 2.1.1 正常系処理：有効な入力データ | `topic = "/1/data/refrigerator"` を設定し、`extract_device_id_from_topic(topic)` を呼び出す | `"1"` が返される（1桁の最小桁数ID） |
| 3 | 2.1.1 正常系処理：有効な入力データ | `topic = "/9999999/data/refrigerator"` を設定し、`extract_device_id_from_topic(topic)` を呼び出す | `"9999999"` が返される |
| 4 | 2.1.1 正常系処理：有効な入力データ | `topic = "//data/refrigerator"` を設定し、`extract_device_id_from_topic(topic)` を呼び出す | `None` が返される（空文字IDは正規表現 `[^/]+` に不一致） |
| 5 | 1.1.1 必須チェック：None入力 | `topic = None` を設定し、`extract_device_id_from_topic(topic)` を呼び出す | `None` が返される |
| 6 | 1.1.6 不整値チェック：許容されていないコード値 | `topic = "/invalid/path"` を設定し（`/data/refrigerator` サフィックスなし）、`extract_device_id_from_topic(topic)` を呼び出す | `None` が返される（パターン不一致） |
| 7 | 1.1.1 必須チェック：空文字入力 | `topic = ""` を設定し、`extract_device_id_from_topic(topic)` を呼び出す | `None` が返される（正規表現に不一致） |
| 8 | 1.1.6 不整値チェック：許容されていないコード値 | `topic = "/12345/data/refrigerator/"` を設定し（末尾スラッシュあり）、`extract_device_id_from_topic(topic)` を呼び出す | `None` が返される（正規表現 `$` に不一致） |
| 9 | 2.1.1 正常系処理：有効な入力データ | `topic = "/abc/data/refrigerator"` を設定し（文字列ID）、`extract_device_id_from_topic(topic)` を呼び出す | `"abc"` が返される |
| 10 | 1.1.6 不整値チェック：許容されていないコード値 | `topic = "/abc/def/data/refrigerator"` を設定し（IDにスラッシュ含む）、`extract_device_id_from_topic(topic)` を呼び出す | `None` が返される（スラッシュを含まない文字列のみ許容） |
| 11 | 2.1.1 正常系処理：有効な入力データ | `topic = "/0100100101101011010/data/refrigerator"` を設定し、`extract_device_id_from_topic(topic)` を呼び出す | `"0100100101101011010"` が返される |

---

### TestExtractDeviceIdFromKey

**観点**: データ変換仕様 > デバイスID抽出処理 > EventHub keyからのデバイスID抽出

| No | テスト観点 | 操作手順 | 予想結果 |
|---|---|---|---|
| 12 | 2.1.1 正常系処理：有効な入力データ | `message_key = "12345"` を設定し、`extract_device_id_from_key(message_key)` を呼び出す | `"12345"` が返される |
| 13 | 1.1.1 必須チェック：None入力 | `message_key = None` を設定し、`extract_device_id_from_key(message_key)` を呼び出す | `None` が返される |
| 14 | 1.1.1 必須チェック：空文字入力 | `message_key = ""` を設定し、`extract_device_id_from_key(message_key)` を呼び出す | `None` が返される |
| 15 | 1.1.1 必須チェック：空白のみ入力 | `message_key = "   "` を設定し、`extract_device_id_from_key(message_key)` を呼び出す | `None` が返される（`strip()` 後が空文字のためNone） |
| 16 | 2.1.1 正常系処理：有効な入力データ | `message_key = "  12345  "` を設定し（前後に空白あり）、`extract_device_id_from_key(message_key)` を呼び出す | `"12345"` が返される（`strip()` 処理済み） |
| 17 | 2.1.1 正常系処理：有効な入力データ | `message_key = "9999999"` を設定し、`extract_device_id_from_key(message_key)` を呼び出す | `"9999999"` が返される |

---

### TestExtractDeviceId

**観点**: データ変換仕様 > デバイスID抽出処理 > デバイスID抽出の統合処理

| No | テスト観点 | 操作手順 | 予想結果 |
|---|---|---|---|
| 18 | 2.1.1 正常系処理：有効な入力データ | `topic = "/11111/data/refrigerator"`, `message_key = "22222"`, `payload_device_id = "33333"` を設定し、`extract_device_id(topic, message_key, payload_device_id)` を呼び出す | `"11111"` が返される（MQTT Topic が最優先） |
| 19 | 2.1.1 正常系処理：有効な入力データ | `topic = None`, `message_key = "22222"`, `payload_device_id = "33333"` を設定し、`extract_device_id()` を呼び出す | `"22222"` が返される（Topic 無効時は EventHub key を使用） |
| 20 | 2.1.1 正常系処理：有効な入力データ | `topic = "/not/valid/format"`, `message_key = "22222"`, `payload_device_id = "33333"` を設定し、`extract_device_id()` を呼び出す | `"22222"` が返される（不正形式 Topic はスキップし EventHub key を使用） |
| 21 | 2.1.1 正常系処理：有効な入力データ | `topic = None`, `message_key = None`, `payload_device_id = "33333"` を設定し、`extract_device_id()` を呼び出す | `"33333"` が返される（Topic/key 両方無効時はペイロード内 device_id をフォールバックとして使用） |
| 22 | 1.1.1 必須チェック：None入力 | `topic = None`, `message_key = None`, `payload_device_id = None` を設定し、`extract_device_id()` を呼び出す | `None` が返される |
| 23 | 1.1.1 必須チェック：空文字入力 | `topic = None`, `message_key = None`, `payload_device_id = ""` を設定し、`extract_device_id()` を呼び出す | `None` が返される（空文字はフォールバックとして使用しない） |
| 24 | 1.1.1 必須チェック：空白のみ入力 | `topic = None`, `message_key = None`, `payload_device_id = "   "` を設定し、`extract_device_id()` を呼び出す | `None` が返される（`strip()` 後が空文字のためフォールバック不使用） |

---

### TestIsValidJson

**観点**: データ変換仕様 > バイナリ/JSON判定・変換処理 > フォーマット判定ロジック

| No | テスト観点 | 操作手順 | 予想結果 |
|---|---|---|---|
| 25 | 2.1.1 正常系処理：有効な入力データ | `data = '{"device_id": 12345, "event_timestamp": "2026-01-23T10:30:00.000Z", "external_temp": 25.5}'` を設定し、`is_valid_json(data)` を呼び出す | `True` が返される |
| 26 | 2.1.1 正常系処理：有効な入力データ | `data = "[1, 2, 3]"` を設定し、`is_valid_json(data)` を呼び出す | `True` が返される（JSON配列） |
| 27 | 1.1.1 必須チェック：None入力 | `data = None` を設定し、`is_valid_json(data)` を呼び出す | `False` が返される |
| 28 | 1.1.1 必須チェック：空文字入力 | `data = ""` を設定し、`is_valid_json(data)` を呼び出す | `False` が返される |
| 29 | 1.1.6 不整値チェック：許容されていないコード値 | `data = "{invalid json}"` を設定し（JSON構文エラー）、`is_valid_json(data)` を呼び出す | `False` が返される（`json.JSONDecodeError` を内部でキャッチ） |
| 30 | 1.1.6 不整値チェック：許容されていないコード値 | `data = "hello world"` を設定し、`is_valid_json(data)` を呼び出す | `False` が返される（JSON形式でない平文） |

---

### TestParseBinaryTelemetry

**観点**: データ変換仕様 > バイナリ/JSON判定・変換処理 > バイナリ→JSON変換処理

| No | テスト観点 | 操作手順 | 予想結果 |
|---|---|---|---|
| 31 | 2.1.1 正常系処理：有効な入力データ | `_make_binary_telemetry(device_id="test_device-id", event_timestamp_ms=1737624600000)` で312バイトバイナリを生成し、`parse_binary_telemetry(binary_data)` を呼び出す | JSON文字列が返される。`device_id = "test_device-id"`, `event_timestamp = "2025-01-23T09:30:00.000Z"` が含まれる |
| 32 | 2.1.2 正常系処理：最小構成の入力 | 正常な312バイトバイナリを生成し、`parse_binary_telemetry(binary_data)` を呼び出す | `external_temp`, `set_temp_freezer_1` 〜 `defrost_heater_output_2` の全22センサーフィールドがJSONに含まれる |
| 33 | 1.1.1 必須チェック：None入力 | `binary_data = None` を設定し、`parse_binary_telemetry(binary_data)` を呼び出す | `None` が返される |
| 34 | 1.3.1 エラーハンドリング：例外伝播 | `binary_data = b"\x00" * 100`（100バイト）を設定し、`parse_binary_telemetry(binary_data)` を呼び出す | `None` が返される（312バイト以外はサイズ検証失敗） |
| 35 | 1.3.1 エラーハンドリング：例外伝播 | `binary_data = b""`（空バイト列）を設定し、`parse_binary_telemetry(binary_data)` を呼び出す | `None` が返される |
| 36 | 2.1.1 正常系処理：有効な入力データ | `_make_binary_telemetry(device_id="99999")` で生成したバイナリと `override_device_id="11111"` を設定し、`parse_binary_telemetry(binary_data, override_device_id)` を呼び出す | 返却JSONの `device_id` が `"11111"` に上書きされる |
| 37 | 2.1.1 正常系処理：有効な入力データ | `_make_binary_telemetry(device_id="12345")` で生成したバイナリと `override_device_id=None` を設定し、`parse_binary_telemetry(binary_data, None)` を呼び出す | 返却JSONの `device_id` が `"12345"`（文字列）になる |
| 38 | 2.1.1 正常系処理：有効な入力データ | `_make_binary_telemetry(event_timestamp_ms=1737624600000)` で生成したバイナリを `parse_binary_telemetry(binary_data)` に渡す | `event_timestamp` が `"2025-01-23T09:30:00.000Z"` 形式（ISO 8601 UTC）になる |
| 39 | 2.1.1 正常系処理：有効な入力データ | `sensor_values=[float("nan")] + [25.5]*21` で生成した312バイトバイナリを `parse_binary_telemetry(binary_data)` に渡す | `external_temp` フィールドの値が `null`（None）になる（NaN値はnullとして扱う） |

---

### TestUpdateJsonDeviceId

**観点**: データ変換仕様 > バイナリ/JSON判定・変換処理 > JSON形式へのデバイスID上書き処理

| No | テスト観点 | 操作手順 | 予想結果 |
|---|---|---|---|
| 40 | 2.1.1 正常系処理 / 3.3.2.1 更新結果：例外なく処理が完了 | `json_str={"device_id": "test-device_id%", "event_timestamp": "..."}` のJSON文字列と `override_device_id="12345"` を設定し、`update_json_device_id(json_str, override_device_id)` を呼び出す | JSONの `device_id` が `"12345"`（str型）に更新されたJSON文字列が返される |
| 41 | 1.1.1 必須チェック：None入力 | `json_str=None`, `override_device_id="12345"` を設定し、`update_json_device_id()` を呼び出す | `None` が返される |
| 42 | 2.1.1 正常系処理：有効な入力データ | `json_str={"device_id": "test-device_id%", "event_timestamp": "..."}` のJSON文字列と `override_device_id=None` を設定し、`update_json_device_id()` を呼び出す | 元の `json_str` がそのまま返される（上書きなし） |
| 43 | 1.3.1 エラーハンドリング：例外伝播 | `json_str="{invalid json}"`, `override_device_id="12345"` を設定し（`JSONDecodeError` 発生）、`update_json_device_id()` を呼び出す | 元の文字列 `"{invalid json}"` がそのまま返される（例外を内部でキャッチして継続） |
| 44 | 1.3.1 エラーハンドリング：例外伝播 | 有効な `json_str` と `override_device_id=""` を設定し（`ValueError` 発生）、`update_json_device_id()` を呼び出す | 元の `json_str` がそのまま返される |
| 45 | 1.3.1 エラーハンドリング：例外伝播 | 有効な `json_str` と `override_device_id=[]` を設定し（`TypeError` 発生）、`update_json_device_id()` を呼び出す | 元の `json_str` がそのまま返される |
| 46 | 2.3.1 副作用チェック：処理失敗時データが更新されない | `device_id="99999"`, `event_timestamp`, `external_temp=25.5`, `internal_temp_freezer_1=-19.5` を含む `json_str` と `override_device_id="12345"` を設定し、`update_json_device_id()` を呼び出す | `device_id` が `"12345"` に更新される。`event_timestamp`, `external_temp`, `internal_temp_freezer_1` は元の値のまま変更されない |

---

### TestConvertToJsonWithDeviceId

**観点**: データ変換仕様 > バイナリ/JSON判定・変換処理 > フォーマット判定・変換の統合処理

| No | テスト観点 | 操作手順 | 予想結果 |
|---|---|---|---|
| 47 | 1.1.1 必須チェック：None入力 | `raw_value=None`, `override_device_id="12345"` を設定し、`convert_to_json_with_device_id(raw_value, override_device_id)` を呼び出す | `None` が返される |
| 48 | 2.1.1 正常系処理：有効な入力データ | `payload={"device_id": "99999", "event_timestamp": "...", "external_temp": 25.5}` をJSONエンコードしたUTF-8バイト列と `override_device_id="12345"` を設定し、`convert_to_json_with_device_id()` を呼び出す（処理フロー step2: JSON形式判定後） | `device_id` が `"12345"` に上書きされたJSON文字列が返される |
| 49 | 2.1.1 正常系処理：有効な入力データ | `_make_binary_telemetry(device_id=12345)` で生成した312バイトバイナリと `override_device_id="12345"` を設定し、`convert_to_json_with_device_id()` を呼び出す（処理フロー step3: バイナリ変換） | `device_id`, `event_timestamp` を含むJSON文字列が返される |
| 50 | 1.3.1 エラーハンドリング：例外伝播 | `raw_value=b"\xFF\xFE\xFD"`（3バイト不正データ）と `override_device_id="12345"` を設定し（UTF-8デコード失敗かつバイナリパース失敗）、`convert_to_json_with_device_id()` を呼び出す | `None` が返される（変換エラー時はレコード破棄） |
| 51 | 2.1.1 正常系処理：有効な入力データ | `payload={"device_id": "99999", "event_timestamp": "..."}` のUTF-8バイト列と `override_device_id=None` を設定し、`convert_to_json_with_device_id()` を呼び出す | 元の `device_id="99999"` が保持されたJSON文字列が返される |

---

### TestGetAlertAbnormalState

**観点**: アラート処理仕様 > マスタデータ取得 > 異常状態テーブル取得

| No | テスト観点 | 操作手順 | 予想結果 |
|---|---|---|---|
| 52 | 1.3.1 エラーハンドリング：例外伝播 | `spark` をモックし、`spark.read.format("jdbc").options().load()` が `Exception("DB error")` を送出するよう設定し、`get_alert_abnormal_state()` を呼び出す | `spark.createDataFrame` が1回呼ばれ、引数が `([], schema=_ALERT_ABNORMAL_STATE_SCHEMA)` となる（空DataFrameで代替。例外を握りつぶし継続） |
| 53 | 2.1.1 正常系処理：有効な入力データ | `spark` をモックし、`spark.read.format("jdbc").options().load()` が `mock_df` を返すよう設定し、`get_alert_abnormal_state()` を呼び出す | `mock_df.withColumn` の1回目の呼び出しが `"is_abnormal"` を引数として呼ばれる。2回目の呼び出しが `"alert_fired"` を引数として呼ばれる（派生カラム付与） |

---

### TestDetermineUpdatePattern

**観点**: アラート処理仕様 > 異常状態テーブル更新処理（更新パターン判定）

| No | テスト観点 | 操作手順 | 予想結果 |
|---|---|---|---|
| 54 | 2.1.1 正常系処理：有効な入力データ | `threshold_exceeded=False`, `alert_triggered=False` を設定し、`determine_update_pattern(threshold_exceeded, alert_triggered)` を呼び出す | `"recovery"` が返される（正常状態への復旧処理） |
| 55 | 2.1.1 正常系処理：有効な入力データ | `threshold_exceeded=False`, `alert_triggered=True` を設定し、`determine_update_pattern()` を呼び出す | `"recovery"` が返される（閾値超過なしが最優先条件、`alert_triggered` の値に関わらずrecovery） |
| 56 | 2.1.1 正常系処理：有効な入力データ | `threshold_exceeded=True`, `alert_triggered=True` を設定し、`determine_update_pattern()` を呼び出す | `"alert_fired"` が返される（`alert_fired_time=NOW()` 更新処理） |
| 57 | 2.1.1 正常系処理：有効な入力データ | `threshold_exceeded=True`, `alert_triggered=False` を設定し、`determine_update_pattern()` を呼び出す | `"abnormal_start"` が返される（新規異常開始または異常継続処理） |

---

### TestShouldEnqueueEmail

**観点**: 外部連携仕様 > メール送信キュー登録処理 > キュー登録の設計方針

| No | テスト観点 | 操作手順 | 予想結果 |
|---|---|---|---|
| 58 | 2.1.1 正常系処理：有効な入力データ | `alert_triggered=True`, `alert_email_flag=True` を設定し、`should_enqueue_email(alert_triggered, alert_email_flag)` を呼び出す | `True` が返される（メール送信キューへ登録する） |
| 59 | 2.1.1 正常系処理：有効な入力データ | `alert_triggered=False`, `alert_email_flag=True` を設定し、`should_enqueue_email()` を呼び出す | `False` が返される（アラート未発報のためキュー登録しない） |
| 60 | 2.1.1 正常系処理：有効な入力データ | `alert_triggered=True`, `alert_email_flag=False` を設定し、`should_enqueue_email()` を呼び出す | `False` が返される（メール通知設定がOFFのためキュー登録しない） |
| 61 | 2.1.1 正常系処理：有効な入力データ | `alert_triggered=False`, `alert_email_flag=False` を設定し、`should_enqueue_email()` を呼び出す | `False` が返される |
| 62 | 1.1.1 必須チェック：None入力 | `alert_triggered=None`, `alert_email_flag=True` を設定し、`should_enqueue_email()` を呼び出す | `False` が返される（NoneはTrueではないためFalse） |
| 63 | 1.1.1 必須チェック：None入力 | `alert_triggered=True`, `alert_email_flag=None` を設定し、`should_enqueue_email()` を呼び出す | `False` が返される（NoneはTrueではないためFalse） |

---

### TestIsRetryableError

**観点**: 外部連携仕様 > OLTPリトライ戦略（リトライ対象エラー判定）

| No | テスト観点 | 操作手順 | 予想結果 |
|---|---|---|---|
| 64 | 1.3.1 エラーハンドリング：例外伝播 | `error = socket.timeout("Connection timed out")` を設定し、`is_retryable_error(error)` を呼び出す | `True` が返される（接続タイムアウトはリトライ対象） |
| 65 | 1.3.1 エラーハンドリング：例外伝播 | `error = ConnectionResetError("Connection reset by peer")` を設定し、`is_retryable_error(error)` を呼び出す | `True` が返される（一時的なネットワークエラーはリトライ対象） |
| 66 | 1.3.1 エラーハンドリング：例外伝播 | `error = BrokenPipeError("Broken pipe")` を設定し、`is_retryable_error(error)` を呼び出す | `True` が返される（一時的なネットワークエラーはリトライ対象） |
| 67 | 1.3.1 エラーハンドリング：例外伝播 | `error = OSError("Network unreachable")` を設定し、`is_retryable_error(error)` を呼び出す | `True` が返される（一時的なネットワークエラーはリトライ対象） |
| 68 | 1.3.1 エラーハンドリング：例外伝播 | `error = pymysql.err.OperationalError(2003, "Can't connect to MySQL server")` を設定し、`is_retryable_error(error)` を呼び出す | `True` が返される（errno=2003 接続不可はリトライ対象） |
| 69 | 1.3.1 エラーハンドリング：例外伝播 | `error = pymysql.err.OperationalError(2006, "MySQL server has gone away")` を設定し、`is_retryable_error(error)` を呼び出す | `True` が返される（errno=2006 サーバー切断はリトライ対象） |
| 70 | 1.3.1 エラーハンドリング：例外伝播 | `error = pymysql.err.OperationalError(2013, "Lost connection to MySQL server during query")` を設定し、`is_retryable_error(error)` を呼び出す | `True` が返される（errno=2013 クエリ中切断はリトライ対象） |
| 71 | 1.3.4 エラーハンドリング：ForbiddenError | `error = pymysql.err.OperationalError(1045, "Access denied for user")` を設定し、`is_retryable_error(error)` を呼び出す | `False` が返される（errno=1045 認証エラーはリトライ不可） |
| 72 | 1.3.6 エラーハンドリング：AppError | `error = pymysql.err.ProgrammingError(1064, "SQL syntax error")` を設定し、`is_retryable_error(error)` を呼び出す | `False` が返される（SQL構文エラーはリトライ不可） |
| 73 | 1.3.6 エラーハンドリング：AppError | `error = pymysql.err.IntegrityError(1062, "Duplicate entry")` を設定し、`is_retryable_error(error)` を呼び出す | `False` が返される（制約違反はリトライ不可） |
| 74 | 1.3.6 エラーハンドリング：AppError | `error = ValueError("Invalid value")` を設定し、`is_retryable_error(error)` を呼び出す | `False` が返される（一般的なPython例外はリトライ不可） |

---

### TestGetMysqlConnection

**観点**: 外部連携仕様 > OLTPリトライ戦略（MySQL接続コンテキストマネージャ）

| No | テスト観点 | 操作手順 | 予想結果 |
|---|---|---|---|
| 75 | 2.1.1 正常系処理：有効な入力データ | `pymysql.connect` が `mock_conn` を返すようモックし、`get_mysql_connection()` の with ブロックを実行する | with ブロック内で `conn is mock_connect.return_value` が成立する（1回目の接続成功で conn が yield） |
| 76 | 2.1.1 正常系処理：有効な入力データ | `pymysql.connect` が `mock_conn` を返すようモックし、`get_mysql_connection()` の with ブロックを正常終了させる | `mock_conn.close()` が1回呼ばれる（finally ブロックでの接続クローズ保証） |
| 77 | 1.3.1 エラーハンドリング：例外伝播 | `pymysql.connect` の `side_effect` を `[OperationalError(2006), mock_conn]` に設定し（1回目失敗・2回目成功）、`get_mysql_connection()` の with ブロックを実行する | `time.sleep` が1回呼ばれる。`conn is mock_conn` が成立する（リトライ成功） |
| 78 | 1.3.1 エラーハンドリング：例外伝播 | `pymysql.connect` が常に `OperationalError(2006)` を送出するようモックし、`get_mysql_connection()` の with ブロックを実行する | `pymysql.err.OperationalError` が送出される（最大リトライ超過後に最後の例外を再送出） |
| 79 | 1.3.1 エラーハンドリング：例外伝播 | `pymysql.connect` が常に `OperationalError(2006)` を送出するようモックし（3試行すべて失敗）、`get_mysql_connection()` を実行する | `time.sleep` が2回だけ呼ばれる（attempt 0, 1 でのみ sleep し、attempt 2 は即 raise のため sleep なし） |

---

### TestUpdateAlertAbnormalState

**観点**: アラート処理仕様 > 異常状態テーブル更新処理 / 外部連携仕様 > STEP 5b

| No | テスト観点 | 操作手順 | 予想結果 |
|---|---|---|---|
| 80 | 2.1.1 正常系処理：有効な入力データ | `batch_df` の `collect()` が空リスト `[]` を返すようモックし、`update_alert_abnormal_state(mock_batch_df, 0)` を呼び出す | `get_mysql_connection` が呼ばれない（対象レコードなしで早期リターン） |
| 81 | 2.1.1 正常系処理：有効な入力データ | `threshold_exceeded=False`, `alert_triggered=False` のレコード1件を `collect()` が返すようモックし、`get_mysql_connection` をモックし、`update_alert_abnormal_state()` を呼び出す | `cursor.execute` の1回目呼び出しのSQL文字列に `"abnormal_start_time = NULL"` が含まれる。`conn.commit()` が1回呼ばれる |
| 82 | 2.1.1 正常系処理：有効な入力データ | `threshold_exceeded=True`, `alert_triggered=True` のレコード1件を `collect()` が返すようモックし、`get_mysql_connection` をモックし、`update_alert_abnormal_state()` を呼び出す | `cursor.execute` の1回目呼び出しのSQL文字列に `"alert_fired_time = NOW()"` が含まれる。`conn.commit()` が1回呼ばれる |
| 83 | 2.1.1 正常系処理：有効な入力データ | `threshold_exceeded=True`, `alert_triggered=False` のレコード1件を `collect()` が返すようモックし、`get_mysql_connection` をモックし、`update_alert_abnormal_state()` を呼び出す | `cursor.execute` の1回目呼び出しのSQL文字列に `"COALESCE(abnormal_start_time,"` が含まれる。`conn.commit()` が1回呼ばれる |

---

### TestEnqueueEmailNotification

**観点**: 外部連携仕様 > メール送信キュー登録処理

| No | テスト観点 | 操作手順 | 予想結果 |
|---|---|---|---|
| 84 | 2.1.1 正常系処理：有効な入力データ | `batch_df.filter().isEmpty()` が `True` を返すようモックし、`enqueue_email_notification(mock_batch_df, 0, MagicMock())` を呼び出す | `get_mysql_connection` が呼ばれない（フィルタ後0件のため早期リターン） |
| 85 | 2.1.1 正常系処理：有効な入力データ | `alert_records.isEmpty()=False` かつ Spark結合後の `queue_records.collect()=[]` を返すようモックし、`enqueue_email_notification()` を呼び出す | `get_mysql_connection` が呼ばれない（キューレコード0件のため早期リターン） |
| 86 | 2.1.1 正常系処理：有効な入力データ | `device_id=1001`, `organization_id=10`, `alert_id=5`, `recipient_email="test@example.com"`, `status="PENDING"`, `retry_count=0` 等を含むキューレコード1件を `collect()` が返すようモックし、`get_mysql_connection` をモックし、`enqueue_email_notification()` を呼び出す | `cursor.execute` が1回呼ばれ、SQL文字列に `"INSERT INTO email_notification_queue"` が含まれる。パラメータに `device_id=1001`, `organization_id=10`, `alert_id=5`, `recipient_email="test@example.com"`, `status="PENDING"`, `retry_count=0` が含まれる。`conn.commit()` が1回呼ばれる |

---

### TestUpdateDeviceStatus

**観点**: 外部連携仕様 > デバイスステータス更新

| No | テスト観点 | 操作手順 | 予想結果 |
|---|---|---|---|
| 87 | 2.1.1 正常系処理：有効な入力データ | `batch_df.groupBy().agg().collect()` が空リスト `[]` を返すようモックし、`update_device_status(mock_batch_df, 0)` を呼び出す | `get_mysql_connection` が呼ばれない（対象レコードなしで早期リターン） |
| 88 | 2.1.1 正常系処理：有効な入力データ | `device_id=1001`, `last_received_time="2026-01-23T09:00:00"` の1件レコードを `collect()` が返すようモックし、`get_mysql_connection` をモックし、`update_device_status()` を呼び出す | `cursor.execute` の1回目呼び出しのSQL文字列に `"INSERT INTO device_status_data"` と `"ON DUPLICATE KEY UPDATE"` が含まれる。パラメータの `params[0]=1001`, `params[1]="2026-01-23T09:00:00"` が設定される。`conn.commit()` が1回呼ばれる |
| 89 | 2.1.1 正常系処理：有効な入力データ | `device_id=1001,1002,1003` の3件レコードを `collect()` が返すようモックし、`get_mysql_connection` をモックし、`update_device_status()` を呼び出す | `cursor.execute` が3回呼ばれる（デバイス数分のUPSERT実行） |
| 90 | 2.3.1 副作用チェック：処理失敗時データが更新されない | `device_id=1001,1002,1003` の3件レコードを `collect()` が返すようモックし、`get_mysql_connection` をモックし、`update_device_status()` を呼び出す | `conn.commit()` が1回だけ呼ばれる（複数レコード処理後も一括コミット） |

---

### TestInsertAlertHistory

**観点**: 外部連携仕様 > アラート履歴登録処理（アラート発報時）

| No | テスト観点 | 操作手順 | 予想結果 |
|---|---|---|---|
| 91 | 2.1.1 正常系処理：有効な入力データ | `batch_df.filter().collect()` が空リスト `[]` を返すようモックし、`insert_alert_history(mock_batch_df, 0)` を呼び出す | `get_mysql_connection` が呼ばれない（発報レコード0件のため早期リターン） |
| 92 | 3.2.1 登録機能：登録処理呼び出し / 3.3.1 更新機能：更新処理呼び出し | `alert_id=5`, `device_id=1001`, `abnormal_start_time="2026-01-23T08:00:00"`, `current_sensor_value=-30.0` の1件レコードを `collect()` が返すようモックし、`cursor.lastrowid=9999` を設定し、`get_mysql_connection` をモックし、`insert_alert_history()` を呼び出す | `cursor.execute` が2回呼ばれる（1回目: `"INSERT INTO alert_history"` を含むSQL, パラメータ `(5, "2026-01-23T08:00:00", 1, -30.0)`。2回目: UPDATE SQL, パラメータ先頭が `alert_history_id=9999`）。`conn.commit()` が1回呼ばれる |
| 93 | 3.2.1 登録機能：登録処理呼び出し | `alert_id=1,2,3` の3件の発報レコードを `collect()` が返すようモックし、`get_mysql_connection` をモックし、`insert_alert_history()` を呼び出す | `cursor.execute` が6回呼ばれる（INSERT 3回 + UPDATE 3回） |

---

### TestUpdateAlertHistoryOnRecovery

**観点**: 外部連携仕様 > アラート履歴更新処理（復旧時）

| No | テスト観点 | 操作手順 | 予想結果 |
|---|---|---|---|
| 94 | 2.1.1 正常系処理：有効な入力データ | `recovery_candidates.join().collect()` が空リスト `[]` を返すようモックし、`update_alert_history_on_recovery(mock_batch_df, 0)` を呼び出す | `get_mysql_connection` が呼ばれない（復旧対象レコード0件のため早期リターン） |
| 95 | 3.3.1 更新機能：更新処理呼び出し | `event_timestamp="2026-01-23T10:00:00"`, `alert_history_id=999`, `device_id=1001`, `alert_id=5` の1件レコードを `collect()` が返すようモックし、`get_mysql_connection` をモックし、`update_alert_history_on_recovery()` を呼び出す | `cursor.execute` の1回目呼び出しのSQL文字列に `"UPDATE alert_history"` が含まれる。パラメータの `params[1]=2`（ALERT_STATUS_RECOVERED）, `params[2]=999`（alert_history_id）が設定される。`conn.commit()` が1回呼ばれる |
| 96 | 3.3.1 更新機能：更新処理呼び出し | `alert_history_id=101,102,103` の3件の復旧レコードを `collect()` が返すようモックし、`get_mysql_connection` をモックし、`update_alert_history_on_recovery()` を呼び出す | `cursor.execute` が3回呼ばれる（復旧レコード数分のUPDATE実行） |
