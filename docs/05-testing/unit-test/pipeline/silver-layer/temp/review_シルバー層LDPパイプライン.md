# テストコードレビュー結果 — シルバー層LDPパイプライン

| 項目         | 内容                                                                                   |
| ------------ | -------------------------------------------------------------------------------------- |
| レビュー日   | 2026-04-23                                                                             |
| 対象ファイル | tests/unit/pipeline/silver/test_silver-ldp-pipeline_service.py<br>tests/unit/pipeline/silver/test_silver-ldp-pipeline_model.py |
| テスト項目書 | docs/05-testing/unit-test/pipeline/silver-layer/テスト項目書_シルバー層LDPパイプライン.md |

---

## チェックリスト確認結果

| No     | チェック項目                                                                                         | 結果 |
| ------ | ---------------------------------------------------------------------------------------------------- | ---- |
| CL-1-1 | DB操作・モデル生成・APIリクエストで明示的に指定している全フィールドをアサートしているか              | **NG**（指摘No.1, 2）|
| CL-1-2 | 検索に使用される全フィルター条件が、テスト群全体を通じて少なくとも1件ずつ検証されているか            | OK |
| CL-2-1 | 外部API・サービス・リポジトリで例外が発生した場合に、例外が上位へ伝播するテストがあるか              | OK（TestGetMysqlConnection.test_raises_after_max_retries_exceeded） |
| CL-2-2 | 4xxエラー（クライアントエラー）と5xxエラー（サーバーエラー）のうち代表ケースが最低1件あるか          | OK（OperationalError で検証済み） |
| CL-3-1〜6 | バリデーション（フォーム層）                                                                     | N/A（フォーム層なし） |
| CL-4-1〜3 | CSVエクスポート                                                                                  | N/A（該当なし） |
| CL-5-1 | `unittest.mock.patch` のパスがテスト対象モジュール内のimport先を指しているか                        | OK（`functions.alert_judgment.*` でテスト対象モジュール内参照） |
| CL-5-2 | 各テストメソッドのdocstringに観点番号と概要が記載されているか                                        | OK（全メソッドに観点番号付き docstring あり） |
| CL-6-1 | テスト項目書の「テスト総数」とテストコードの実テストメソッド数が一致しているか                        | **NG**（指摘No.4: テスト項目書の TestIsRetryableError ヘッダーが「12件」だが実コードは11件） |
| CL-6-2 | テスト項目書のNo列に重複・欠番がないか                                                               | OK（S-01〜S-95, M-01〜M-37 連番） |
| CL-6-3 | テストコードに追加・変更があった場合、テスト項目書の内容・総数・連番も更新されているか                | OK（本レビューで対応済み） |

チェックリスト外追加確認:
- **正常系テストの欠落**: TestEnqueueEmailNotification に INSERT 実行パスのテストが未実装（指摘No.3）

---

## 指摘テーブル

| No | 対象ファイル | 対象テスト / 行 | 指摘内容 | 対応観点 | 修正案 |
|----|-------------|----------------|----------|----------|--------|
| 1  | test_silver-ldp-pipeline_service.py | TestInsertAlertHistory.test_fired_record_inserts_history_and_updates_state_with_lastrowid / L1874 | INSERT パラメータ4件（alert_id=5, abnormal_start_time, ALERT_STATUS_FIRING=1, current_sensor_value=-30.0）が明示的に指定されているが一切アサートされていない（UPDATEのlastrowid確認のみ） | CL-1-1 | `insert_params = mock_cursor.execute.call_args_list[0][0][1]` を取得し params[0]==5, params[1]=="2026-01-23T08:00:00", params[2]==1, params[3]==-30.0 を追加 |
| 2  | test_silver-ldp-pipeline_service.py | TestUpdateDeviceStatus.test_records_execute_upsert_sql / L1758 | INSERT パラメータ2件（device_id=1001, last_received_time="2026-01-23T09:00:00"）が明示的に指定されているが一切アサートされていない | CL-1-1 | `params = mock_cursor.execute.call_args_list[0][0][1]` を取得し params[0]==1001, params[1]=="2026-01-23T09:00:00" を追加 |
| 3  | test_silver-ldp-pipeline_service.py | TestEnqueueEmailNotification（クラス全体） | `email_notification_queue` への INSERT が成功するケース（queue_list が空でないパス）のテストが存在せず、全フィールドのアサートが未実施 | チェックリスト外（正常系テストの欠落） | INSERT 実行パスの正常系テスト1件（test_queue_records_inserted_with_all_fields）を追加 |
| 4  | テスト項目書_シルバー層LDPパイプライン.md | TestIsRetryableError ヘッダー | 「TestIsRetryableError（12件）」と記載されているが、実テストコードには11件しか存在しない | CL-6-1 | ヘッダーを「TestIsRetryableError（11件）」に修正 |

---

## 修正後の状態

| 項目         | 修正前   | 修正後   |
| ------------ | -------- | -------- |
| Service層テスト総数 | 95件 | 96件（+1: test_queue_records_inserted_with_all_fields） |
| Model層テスト総数 | 37件 | 37件（変更なし） |
| テスト総計   | 132件    | 133件    |
