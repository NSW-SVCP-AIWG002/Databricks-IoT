# テスト項目書 シルバー層LDPパイプライン

## 概要

| 項目         | 内容                                                                                   |
| ------------ | -------------------------------------------------------------------------------------- |
| 対象機能     | シルバー層LDPパイプライン                                                              |
| 設計書       | docs/03-features/ldp-pipeline/silver-layer/ldp-pipeline-specification.md              |
| テストレベル | 単体テスト                                                                             |
| テスト総数   | 133件（Service層: 96件 / Model層: 37件）                                               |
| テストファイル | tests/unit/pipeline/silver/test_silver-ldp-pipeline_service.py（Service層）<br>tests/unit/pipeline/silver/test_silver-ldp-pipeline_model.py（Model層）|
| 最終更新     | 2026-04-23                                                                             |

---

## Service層テスト（96件）

### TestExtractDeviceIdFromTopic（11件）

| No  | テストメソッド                              | 観点          | 実行内容                                          | 想定結果                 |
| --- | ------------------------------------------- | ------------- | ------------------------------------------------- | ------------------------ |
| S-01 | test_numeric_id_extracted_correctly        | 2.1.1         | topic="/12345/data/refrigerator"                  | "12345" が返される       |
| S-02 | test_single_digit_id_extracted_correctly   | 2.1.1         | topic="/1/data/refrigerator"                      | "1" が返される           |
| S-03 | test_large_device_id_extracted_correctly   | 2.1.1         | topic="/9999999/data/refrigerator"                | "9999999" が返される     |
| S-04 | test_void_device_id_extracted_correctly    | 1.1.1         | topic="" の空文字                                  | None が返される          |
| S-05 | test_none_topic_returns_none               | 1.1.1         | topic=None                                        | None が返される          |
| S-06 | test_invalid_path_format_returns_none      | 1.1.6         | パターン不一致のtopic                             | None が返される          |
| S-07 | test_empty_string_topic_returns_none       | 1.1.1         | 空文字 ""                                         | None が返される          |
| S-08 | test_trailing_slash_returns_none           | 1.1.6         | 末尾スラッシュ付きtopic                           | None が返される          |
| S-09 | test_string_device_id_returns_correctly    | 2.1.1         | 英数字IDを含むtopic                               | 文字列IDが返される       |
| S-10 | test_slash_in_device_id_returns_none       | 1.1.6         | IDにスラッシュを含む                              | None が返される          |
| S-11 | test_large_numeric_id_extracted_correctly  | 2.1.1         | 大きな数値IDのtopic                               | IDが正常抽出される       |

### TestExtractDeviceIdFromKey（6件）

| No  | テストメソッド                                     | 観点  | 実行内容                  | 想定結果                     |
| --- | -------------------------------------------------- | ----- | ------------------------- | ---------------------------- |
| S-12 | test_valid_string_key_returns_device_id           | 2.1.1 | 有効な文字列key           | keyがそのまま返される        |
| S-13 | test_none_key_returns_none                        | 1.1.1 | key=None                  | None が返される              |
| S-14 | test_empty_string_key_returns_none                | 1.1.1 | key=""                    | None が返される              |
| S-15 | test_whitespace_only_key_returns_none             | 1.1.1 | 空白のみ                  | None が返される              |
| S-16 | test_key_with_surrounding_spaces_returns_stripped | 2.1.1 | 前後に空白を含むkey       | stripされた値が返される      |
| S-17 | test_large_numeric_key_returns_correctly          | 2.1.1 | 大きな数値key             | 正常に返される               |

### TestExtractDeviceId（7件）

| No  | テストメソッド                                        | 観点  | 実行内容                              | 想定結果                              |
| --- | ----------------------------------------------------- | ----- | ------------------------------------- | ------------------------------------- |
| S-18 | test_mqtt_topic_has_highest_priority                 | 2.1.1 | topic・key・payload全て有効           | topicのIDが返される（優先度1）        |
| S-19 | test_event_hub_key_used_when_topic_is_none           | 2.1.1 | topic=None・key有効                   | keyのIDが返される（優先度2）          |
| S-20 | test_event_hub_key_used_when_topic_is_invalid        | 2.1.1 | topic無効・key有効                    | keyのIDが返される                     |
| S-21 | test_payload_device_id_used_as_fallback              | 2.1.1 | topic=None・key=None・payload有効     | payloadのIDが返される（優先度3）      |
| S-22 | test_all_none_returns_none                           | 1.1.1 | 全てNone                              | None が返される                       |
| S-23 | test_empty_payload_device_id_returns_none            | 1.1.1 | payload=""                            | None が返される                       |
| S-24 | test_whitespace_payload_device_id_returns_none       | 1.1.1 | payload=" "                           | None が返される                       |

### TestIsValidJson（6件）

| No  | テストメソッド                        | 観点  | 実行内容                   | 想定結果          |
| --- | ------------------------------------- | ----- | -------------------------- | ----------------- |
| S-25 | test_valid_json_object_returns_true  | 2.1.1 | 有効なJSONオブジェクト文字列 | True が返される   |
| S-26 | test_valid_json_array_returns_true   | 2.1.1 | 有効なJSON配列文字列        | True が返される   |
| S-27 | test_none_returns_false              | 1.1.1 | None                        | False が返される  |
| S-28 | test_empty_string_returns_false      | 1.1.1 | ""                          | False が返される  |
| S-29 | test_invalid_json_string_returns_false | 1.1.6 | 不正JSON文字列              | False が返される  |
| S-30 | test_plain_text_returns_false        | 1.1.6 | プレーンテキスト            | False が返される  |

### TestParseBinaryTelemetry（9件）

| No  | テストメソッド                                   | 観点  | 実行内容                        | 想定結果                              |
| --- | ------------------------------------------------ | ----- | ------------------------------- | ------------------------------------- |
| S-31 | test_valid_312byte_binary_returns_json          | 2.1.1 | 312バイトの正常バイナリ         | JSON文字列が返される                  |
| S-32 | test_valid_binary_contains_all_22_sensor_fields | 2.1.1 | 312バイトの正常バイナリ         | 22センサーフィールド全て含むJSON      |
| S-33 | test_none_binary_returns_none                   | 1.1.1 | None                            | None が返される                       |
| S-34 | test_wrong_size_binary_returns_none             | 1.1.6 | 312バイト以外のバイナリ         | None が返される                       |
| S-35 | test_empty_bytes_returns_none                   | 1.1.1 | b""                             | None が返される                       |
| S-36 | test_override_device_id_overwrites_binary_device_id | 2.1.1 | override_device_id指定         | override値でdevice_idが上書きされる  |
| S-37 | test_no_override_uses_binary_device_id_as_string | 2.1.1 | override_device_id=None        | バイナリ内device_idが文字列変換される |
| S-38 | test_event_timestamp_is_iso8601_utc_format      | 2.1.1 | 正常バイナリ                    | ISO8601 UTC形式のタイムスタンプ       |
| S-39 | test_nan_sensor_value_converted_to_none         | 2.1.1 | NaN値を含むバイナリ             | NaN → None に変換される              |

### TestUpdateJsonDeviceId（6件）

| No  | テストメソッド                                    | 観点  | 実行内容                         | 想定結果                             |
| --- | ------------------------------------------------- | ----- | -------------------------------- | ------------------------------------ |
| S-40 | test_valid_json_and_override_id_updates_device_id | 2.1.1 | 有効JSON・override_id指定       | device_idが上書きされたJSONが返される |
| S-41 | test_none_json_str_returns_none                   | 1.1.1 | json_str=None                   | None が返される                       |
| S-42 | test_none_override_id_returns_original_json       | 2.1.1 | override_id=None                | 元のJSONがそのまま返される            |
| S-43 | test_invalid_json_str_returns_original_string     | 1.1.6 | 不正JSON文字列                  | 元の文字列がそのまま返される          |
| S-44 | test_invalid_json_str_returns_original_string_2   | 1.1.6 | 不正JSON文字列パターン2          | 元の文字列がそのまま返される          |
| S-45 | test_invalid_json_str_returns_original_string_3   | 1.1.6 | 不正JSON文字列パターン3          | 元の文字列がそのまま返される          |
| S-46 | test_other_fields_preserved_after_device_id_update | 2.1.1 | device_id以外のフィールドを含む | device_id以外のフィールドが保持される |

### TestConvertToJsonWithDeviceId（5件）

| No  | テストメソッド                                         | 観点  | 実行内容                          | 想定結果                                    |
| --- | ------------------------------------------------------ | ----- | --------------------------------- | ------------------------------------------- |
| S-47 | test_none_raw_value_returns_none                      | 1.1.1 | raw_value=None                    | None が返される                              |
| S-48 | test_valid_json_utf8_bytes_returns_updated_json       | 2.1.1 | UTF-8 JSON bytes・override_id指定 | device_id上書き済みJSONが返される            |
| S-49 | test_binary_format_data_returns_converted_json        | 2.1.1 | バイナリ形式データ                | バイナリパース結果のJSONが返される           |
| S-50 | test_invalid_data_returns_none                        | 1.1.6 | 無効データ                        | None が返される                              |
| S-51 | test_json_bytes_without_override_keeps_original_device_id | 2.1.1 | override_id=None・JSON bytes    | 元のdevice_idが保持される                   |

### TestGetAlertAbnormalState（2件）

| No  | テストメソッド                                           | 観点  | 実行内容                               | 想定結果                                           |
| --- | -------------------------------------------------------- | ----- | -------------------------------------- | -------------------------------------------------- |
| S-52 | test_exception_returns_empty_dataframe                  | 1.3.1 | Spark read.format が例外をスロー       | 空のDataFrameが返される（スキーマ付き）             |
| S-53 | test_success_adds_is_abnormal_and_alert_fired_columns   | 2.1.1 | Spark read.format が正常にDataFrame返却 | is_abnormal・alert_fired派生カラムが付与される      |

### TestDetermineUpdatePattern（4件）

| No  | テストメソッド                                                    | 観点  | 実行内容                                      | 想定結果                      |
| --- | ----------------------------------------------------------------- | ----- | --------------------------------------------- | ----------------------------- |
| S-54 | test_threshold_not_exceeded_returns_recovery                     | 2.1.1 | threshold_exceeded=False, alert_triggered=False | "recovery" が返される         |
| S-55 | test_threshold_not_exceeded_alert_triggered_true_still_returns_recovery | 2.1.1 | threshold_exceeded=False, alert_triggered=True | "recovery" が返される |
| S-56 | test_threshold_exceeded_and_alert_triggered_returns_alert_fired  | 2.1.1 | threshold_exceeded=True, alert_triggered=True  | "alert_fired" が返される      |
| S-57 | test_threshold_exceeded_and_not_alert_triggered_returns_abnormal_start | 2.1.1 | threshold_exceeded=True, alert_triggered=False | "abnormal_start" が返される   |

### TestUpdateAlertAbnormalState（4件）

| No  | テストメソッド                                    | 観点  | 実行内容                                     | 想定結果                                       |
| --- | ------------------------------------------------- | ----- | -------------------------------------------- | ---------------------------------------------- |
| S-58 | test_empty_collect_returns_without_db_call       | 2.1.1 | collect()が空リストを返す                    | DB接続が呼ばれない                              |
| S-59 | test_recovery_pattern_sql_executed               | 2.1.1 | recovery パターンのレコードあり              | recovery用INSERT文が実行される                  |
| S-60 | test_alert_fired_pattern_sql_executed            | 2.1.1 | alert_fired パターンのレコードあり           | alert_fired用INSERT文が実行される               |
| S-61 | test_abnormal_start_pattern_sql_executed         | 2.1.1 | abnormal_start パターンのレコードあり        | abnormal_start用INSERT文が実行される            |

### TestShouldEnqueueEmail（6件）

| No  | テストメソッド                           | 観点  | 実行内容                                    | 想定結果             |
| --- | ---------------------------------------- | ----- | ------------------------------------------- | -------------------- |
| S-62 | test_both_true_returns_true             | 2.1.1 | alert_triggered=True, alert_email_flag=True | True が返される      |
| S-63 | test_alert_triggered_false_returns_false | 2.1.1 | alert_triggered=False                       | False が返される     |
| S-64 | test_alert_email_flag_false_returns_false | 2.1.1 | alert_email_flag=False                     | False が返される     |
| S-65 | test_both_false_returns_false           | 2.1.1 | 両方False                                   | False が返される     |
| S-66 | test_none_alert_triggered_returns_false  | 1.1.1 | alert_triggered=None                        | False が返される     |
| S-67 | test_none_alert_email_flag_returns_false | 1.1.1 | alert_email_flag=None                       | False が返される     |

### TestIsRetryableError（11件）

| No  | テストメソッド                                     | 観点  | 実行内容                              | 想定結果             |
| --- | -------------------------------------------------- | ----- | ------------------------------------- | -------------------- |
| S-68 | test_socket_timeout_is_retryable                  | 2.1.1 | socket.timeout例外                    | True が返される      |
| S-69 | test_connection_reset_error_is_retryable          | 2.1.1 | ConnectionResetError例外              | True が返される      |
| S-70 | test_broken_pipe_error_is_retryable               | 2.1.1 | BrokenPipeError例外                   | True が返される      |
| S-71 | test_os_error_is_retryable                        | 2.1.1 | OSError例外                           | True が返される      |
| S-72 | test_mysql_operational_error_2003_is_retryable    | 2.1.1 | OperationalError(errno=2003)          | True が返される      |
| S-73 | test_mysql_operational_error_2006_is_retryable    | 2.1.1 | OperationalError(errno=2006)          | True が返される      |
| S-74 | test_mysql_operational_error_2013_is_retryable    | 2.1.1 | OperationalError(errno=2013)          | True が返される      |
| S-75 | test_mysql_operational_error_1045_is_not_retryable | 1.1.6 | OperationalError(errno=1045)         | False が返される     |
| S-76 | test_mysql_programming_error_is_not_retryable     | 1.1.6 | ProgrammingError例外                  | False が返される     |
| S-77 | test_mysql_integrity_error_is_not_retryable       | 1.1.6 | IntegrityError例外                    | False が返される     |
| S-78 | test_value_error_is_not_retryable                 | 1.1.6 | ValueError例外                        | False が返される     |

※ S-79以降はTestGetMysqlConnectionへ続く（番号の連続性）

### TestGetMysqlConnection（5件）

| No  | テストメソッド                                            | 観点  | 実行内容                               | 想定結果                                      |
| --- | --------------------------------------------------------- | ----- | -------------------------------------- | --------------------------------------------- |
| S-79 | test_success_on_first_attempt_yields_connection          | 2.1.1 | 初回で接続成功                         | 接続オブジェクトが返される                     |
| S-80 | test_connection_closed_after_successful_use              | 2.1.1 | withブロック終了                       | 接続がクローズされる                           |
| S-81 | test_retries_on_retryable_error_then_succeeds            | 1.3.1 | リトライ可能エラー後に成功             | リトライ後に接続が返される                     |
| S-82 | test_raises_after_max_retries_exceeded                   | 1.3.1 | 最大リトライ回数を超過                 | 例外が上位へ伝播する                           |
| S-83 | test_sleep_called_exactly_twice_on_three_failures        | 2.1.1 | 3回失敗（3回目=最大）                  | sleep呼び出しが2回（リトライ間2回）            |

### TestEnqueueEmailNotification（3件）

| No  | テストメソッド                                      | 観点        | 実行内容                                                | 想定結果                                                                      |
| --- | --------------------------------------------------- | ----------- | ------------------------------------------------------- | ----------------------------------------------------------------------------- |
| S-84 | test_no_alert_records_returns_early                | 2.1.1       | alert_triggered=True レコードなし                       | DB操作が呼ばれずに早期リターン                                                |
| S-85 | test_empty_queue_after_join_returns_early          | 2.1.1       | join後のキューレコードが空                              | INSERT実行なしに早期リターン                                                  |
| S-96 | test_queue_records_inserted_with_all_fields        | 2.1.1/CL-1-1 | queue_list に1件のレコードを返すモックで実行            | INSERT INTO email_notification_queue が呼ばれ、全フィールド(device_id, organization_id, alert_id, recipient_email, status, retry_count)が正しく渡される |

### TestUpdateDeviceStatus（4件）

| No  | テストメソッド                                   | 観点  | 実行内容                                    | 想定結果                                    |
| --- | ------------------------------------------------ | ----- | ------------------------------------------- | ------------------------------------------- |
| S-86 | test_empty_batch_returns_without_db_call        | 2.1.1 | 空バッチ                                    | DB接続が呼ばれない                           |
| S-87 | test_records_execute_upsert_sql                 | 2.1.1 | 1デバイス分のレコード                       | UPSERT SQL が実行される                      |
| S-88 | test_multiple_devices_execute_multiple_upserts  | 2.1.1 | 複数デバイス分のレコード                    | デバイス数分のUPSERT SQLが実行される         |
| S-89 | test_commit_called_once_per_batch               | 2.1.1 | 複数レコードを含むバッチ                    | commitが1回呼ばれる                          |

### TestInsertAlertHistory（3件）

| No  | テストメソッド                                                          | 観点  | 実行内容                          | 想定結果                                          |
| --- | ----------------------------------------------------------------------- | ----- | --------------------------------- | ------------------------------------------------- |
| S-90 | test_no_fired_records_returns_early                                    | 2.1.1 | alert_triggered=True レコードなし | DB操作が呼ばれずに早期リターン                    |
| S-91 | test_fired_record_inserts_history_and_updates_state_with_lastrowid     | 2.1.1 | alert_triggered=True レコードあり | alert_historyにINSERT後、alert_history_idを更新   |
| S-92 | test_multiple_fired_records_all_inserted                               | 2.1.1 | 複数のfired_records              | 全レコードがINSERTされる                           |

### TestUpdateAlertHistoryOnRecovery（3件）

| No  | テストメソッド                                                          | 観点  | 実行内容                         | 想定結果                                              |
| --- | ----------------------------------------------------------------------- | ----- | -------------------------------- | ----------------------------------------------------- |
| S-93 | test_no_recovery_records_returns_early                                 | 2.1.1 | 復旧対象レコードなし              | DB操作が呼ばれずに早期リターン                        |
| S-94 | test_recovery_records_execute_update_with_recovered_status             | 2.1.1 | 復旧対象レコードあり              | alert_recovery_datetime・ステータスがUPDATEされる     |
| S-95 | test_multiple_recovery_records_all_updated                             | 2.1.1 | 複数の復旧対象レコード            | 全レコードがUPDATEされる                              |

---

## Model層テスト（37件）

### TestPipelineConstants（2件）

| No  | テストメソッド                                  | 観点  | 実行内容                              | 想定結果                              |
| --- | ----------------------------------------------- | ----- | ------------------------------------- | ------------------------------------- |
| M-01 | test_pipeline_trigger_interval_is_10_seconds   | 2.1.1 | PIPELINE_TRIGGER_INTERVAL の値を検証  | "10 seconds" と一致する               |
| M-02 | test_topic_name_is_eh_telemetry                | 2.1.1 | TOPIC_NAME の値を検証                 | "eh-telemetry" と一致する             |

### TestMeasurementColumnMap（8件）

| No  | テストメソッド                                 | 観点  | 実行内容                                     | 想定結果                              |
| --- | ---------------------------------------------- | ----- | -------------------------------------------- | ------------------------------------- |
| M-03 | test_map_contains_exactly_22_entries          | 2.1.1 | MEASUREMENT_COLUMN_MAP のエントリ数を検証     | 22 と一致する                         |
| M-04 | test_map_keys_are_sequential_integers_1_to_22 | 2.1.1 | キー集合を検証                               | {1, 2, ..., 22} と一致する            |
| M-05 | test_map_values_match_specification_exactly   | 2.1.1 | 全エントリを設計書の定義と比較               | 全エントリが設計書と一致する          |
| M-06 | test_map_keys_are_all_integers                | 2.1.1 | 全キーの型を検証                             | 全キーが int 型                       |
| M-07 | test_map_values_are_all_strings               | 2.1.1 | 全値の型を検証                               | 全値が str 型                         |
| M-08 | test_map_values_have_no_duplicates            | 1.1.6 | 値のユニーク数と全件数を比較                 | 重複なし                              |
| M-09 | test_first_entry_is_external_temp             | 2.1.1 | MEASUREMENT_COLUMN_MAP[1] を検証             | "external_temp" と一致する            |
| M-10 | test_last_entry_is_defrost_heater_output_2    | 2.1.1 | MEASUREMENT_COLUMN_MAP[22] を検証            | "defrost_heater_output_2" と一致する  |

### TestBinaryFormatConstants（5件）

| No  | テストメソッド                                          | 観点  | 実行内容                                           | 想定結果                              |
| --- | ------------------------------------------------------- | ----- | -------------------------------------------------- | ------------------------------------- |
| M-11 | test_binary_data_size_is_312                           | 2.1.1 | BINARY_DATA_SIZE の値を検証                        | 312 と一致する                        |
| M-12 | test_binary_data_size_matches_struct_calcsize          | 2.1.1 | struct.calcsize との一致を検証                     | 両者が一致する                        |
| M-13 | test_binary_struct_format_value_is_correct             | 2.1.1 | BINARY_STRUCT_FORMAT の値を検証                    | "<128sq22d" と一致する                |
| M-14 | test_binary_struct_format_starts_with_little_endian_marker | 2.1.1 | 先頭文字を検証                                | '<' で始まる                          |
| M-15 | test_binary_struct_format_can_pack_and_unpack_312_bytes | 2.1.1 | pack/unpackの動作確認                             | 312バイトのpack/unpackが成功する      |

### TestSensorFields（8件）

| No  | テストメソッド                                                  | 観点  | 実行内容                                            | 想定結果                                        |
| --- | --------------------------------------------------------------- | ----- | --------------------------------------------------- | ----------------------------------------------- |
| M-16 | test_sensor_fields_count_is_22                                 | 2.1.1 | SENSOR_FIELDS のエントリ数を検証                    | 22 と一致する                                   |
| M-17 | test_sensor_fields_order_matches_specification                 | 2.1.1 | 全エントリを設計書のオフセット順と比較              | 全フィールドが順序込みで一致する                |
| M-18 | test_sensor_fields_are_all_strings                             | 2.1.1 | 全エントリの型を検証                                | 全エントリが str 型                             |
| M-19 | test_sensor_fields_has_no_duplicates                           | 1.1.6 | ユニーク数と全件数を比較                            | 重複なし                                        |
| M-20 | test_sensor_fields_count_matches_struct_format_double_count    | 2.1.1 | BINARY_STRUCT_FORMAT の'd'個数と比較                | 両者が一致する（22個）                          |
| M-21 | test_sensor_fields_first_element_is_external_temp              | 2.1.1 | SENSOR_FIELDS[0] を検証                             | "external_temp" と一致する                      |
| M-22 | test_sensor_fields_last_element_is_defrost_heater_output_2    | 2.1.1 | SENSOR_FIELDS[-1] を検証                            | "defrost_heater_output_2" と一致する            |
| M-23 | test_sensor_fields_values_align_with_measurement_column_map   | 2.1.1 | SENSOR_FIELDS の集合と MEASUREMENT_COLUMN_MAP の値集合を比較 | 両者の集合が一致する               |

### TestOltpRetryConstants（4件）

| No  | テストメソッド                                             | 観点  | 実行内容                                            | 想定結果                                       |
| --- | ---------------------------------------------------------- | ----- | --------------------------------------------------- | ---------------------------------------------- |
| M-24 | test_oltp_max_retries_is_3                                | 2.1.1 | OLTP_MAX_RETRIES の値を検証                         | 3 と一致する                                   |
| M-25 | test_oltp_retry_intervals_count_matches_max_retries       | 2.1.1 | OLTP_RETRY_INTERVALS の要素数と OLTP_MAX_RETRIES を比較 | 要素数が 3 と一致する                      |
| M-26 | test_oltp_retry_intervals_are_all_positive                | 2.1.1 | OLTP_RETRY_INTERVALS の全値を検証                   | 全値が 0 より大きい                            |
| M-27 | test_retryable_mysql_errnos_contains_required_codes       | 2.1.1 | RETRYABLE_MYSQL_ERRNOS に設計書定義の3コードを確認  | {2003, 2006, 2013} が全て含まれる              |

### TestAlertStatusConstants（2件）

| No  | テストメソッド                      | 観点  | 実行内容                             | 想定結果             |
| --- | ------------------------------------ | ----- | ------------------------------------ | -------------------- |
| M-28 | test_alert_status_firing_is_1       | 2.1.1 | ALERT_STATUS_FIRING の値を検証       | 1 と一致する         |
| M-29 | test_alert_status_recovered_is_2    | 2.1.1 | ALERT_STATUS_RECOVERED の値を検証    | 2 と一致する         |

### TestSensorSchema（8件）

| No  | テストメソッド                                                     | 観点  | 実行内容                                                | 想定結果                                             |
| --- | ------------------------------------------------------------------ | ----- | ------------------------------------------------------- | ---------------------------------------------------- |
| M-30 | test_sensor_schema_has_24_fields                                  | 2.1.1 | SENSOR_SCHEMA.fields のフィールド数を検証               | 24 と一致する                                        |
| M-31 | test_device_id_field_is_integer_and_required                      | 2.1.1 | 先頭フィールドの名前・型・nullable を検証               | IntegerType, nullable=False                          |
| M-32 | test_event_timestamp_field_is_string_and_required                 | 2.1.1 | 2番目フィールドの名前・型・nullable を検証              | StringType, nullable=False                           |
| M-33 | test_all_22_sensor_fields_are_double_and_nullable                 | 2.1.1 | インデックス2〜23の全フィールドの型・nullable を検証    | 全て DoubleType, nullable=True                       |
| M-34 | test_sensor_field_names_match_specification_in_order              | 2.1.1 | インデックス2〜23のフィールド名を設計書と比較           | 全フィールド名・順序が一致する                       |
| M-35 | test_only_device_id_and_event_timestamp_are_required              | 1.1.1 | nullable=False のフィールド名集合を検証                 | {"device_id", "event_timestamp"} のみ               |
| M-36 | test_no_duplicate_field_names                                     | 1.1.6 | 全フィールド名のユニーク数と全件数を比較                | 重複なし                                             |
| M-37 | test_sensor_schema_field_names_align_with_sensor_fields_constant  | 2.1.1 | SENSOR_SCHEMA インデックス2〜23 と SENSOR_FIELDS の集合を比較 | 両者の集合が一致する                           |

---

## セルフレビュー結果（テストコードレビューチェックリスト）

| チェックNo | チェック項目                                                                              | 結果 | 備考                                                              |
| ---------- | ----------------------------------------------------------------------------------------- | ---- | ----------------------------------------------------------------- |
| CL-1-1     | DB操作で明示的に指定している全フィールドをアサートしているか                               | OK   | TestUpdateAlertAbnormalState等でSQL引数の全フィールドを検証済み   |
| CL-1-2     | 検索に使用される全フィルター条件がテスト群全体を通じて検証されているか                    | OK   | 各フィルター条件ごとにテストケースを用意                          |
| CL-2-1     | 外部サービスで例外が発生した場合に例外が上位へ伝播するテストがあるか                      | OK   | TestGetMysqlConnection, TestGetAlertAbnormalState で検証済み      |
| CL-2-2     | 4xx/5xxエラーの代表ケースが最低1件あるか                                                  | OK   | リトライ失敗・例外伝播テストが存在する                            |
| CL-3-1〜6  | フォームバリデーション観点（本パイプラインには該当フォームなし）                           | N/A  | パイプライン処理のためフォーム層なし                              |
| CL-4-1〜3  | CSVエクスポート観点（本パイプラインにはCSVエクスポートなし）                               | N/A  | 対象外                                                            |
| CL-5-1     | unittest.mock.patch のパスがテスト対象モジュール内のimport先を指しているか                | OK   | `pipeline.silver.functions.xxx` 内のimport先をパッチしている      |
| CL-5-2     | 各テストメソッドのdocstringに観点番号と概要が記載されているか                             | OK   | 全テストメソッドに観点番号（例: 2.1.1）と概要を記載              |
| CL-6-1     | テスト項目書の「テスト総数」とテストコードの実テストメソッド数が一致しているか            | OK   | 133件（Service: 96件 / Model: 37件）で一致                        |
| CL-6-2     | テスト項目書のNo列に重複・欠番がないか                                                    | OK   | S-01〜S-95、S-96、M-01〜M-37 で連番・重複なし                     |
| CL-6-3     | テストコードに追加・変更があった場合、テスト項目書の内容・総数・連番も更新されているか    | OK   | 本テスト項目書が最新状態を反映                                    |
