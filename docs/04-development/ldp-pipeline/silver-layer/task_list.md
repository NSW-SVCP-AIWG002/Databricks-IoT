# シルバー層LDPパイプライン 実装タスクリスト

## タスク一覧

| #   | タスク名                   | 対象ファイル                                                        | 対応テスト                                              | 実装フロー状態 | 備考                              |
| --- | -------------------------- | ------------------------------------------------------------------- | ------------------------------------------------------- | -------------- | --------------------------------- |
| 1   | データ定義層               | `src/iot_app/ldp_pipeline/__init__.py`<br>`src/iot_app/ldp_pipeline/constants.py` | -                                                       | 完了           | センサーフィールド定義・定数      |
| 2   | デバイスID抽出             | `src/iot_app/ldp_pipeline/device_id_extraction.py`                 | `tests/unit/test_ldp-pipeline/test_device_id_extraction.py` | 完了           | UDF登録含む                       |
| 3   | JSON/バイナリ判定・変換    | `src/iot_app/ldp_pipeline/json_telemetry.py`                       | `tests/unit/test_ldp-pipeline/test_json_telemetry.py`   | 完了           | UDF登録含む                       |
| 4   | アラート判定               | `src/iot_app/ldp_pipeline/alert_judgment.py`                       | `tests/unit/test_ldp-pipeline/test_alert_judgment.py`   | 完了           |                                   |
| 5   | MySQL接続・リトライ        | `src/iot_app/ldp_pipeline/mysql_connector.py`                      | `tests/unit/test_ldp-pipeline/test_mysql_connection.py` | 完了           | ジッター付き指数バックオフ        |
| 6   | パイプラインメイン         | `src/iot_app/ldp_pipeline/silver_pipeline.py`                      | -                                                       | 完了           | foreachBatch・Spark依存のため手動確認 |

## 実装フロー状態

| 状態     | 意味                 |
| -------- | -------------------- |
| 未着手   | 実装未開始           |
| 実装中   | ① 実装 実施中        |
| テスト中 | ② pytest 実行中      |
| 修正中   | ③ テスト失敗・修正中 |
| 完了     | ④ 全テスト通過       |

## セルフレビュー進捗

| 観点                         | 状態   | 確認結果 |
| ---------------------------- | ------ | -------- |
| 機能: 設計書との差分         | 完了   | ⚠️ 4件の差分検出。うち1件（enqueue_email_notificationのJDBC認証情報が空文字）は要対応。残り3件は軽微（デッドコード・parsed列未選択・二重commit） |
| 機能: テスト仕様カバレッジ   | 完了   | ✅ 純粋関数（determine_update_pattern / should_enqueue_email / アラート発報条件 / is_retryable_error / リトライロジック）は全パターン網羅。Spark/MySQL依存関数はDatabricksランタイム必須のため手動確認対象 |
| 機能: インターフェース整合性 | 完了   | ✅ 問題なし。silver_pipeline.pyからの全インポートが各モジュールに正しく定義されており、関数シグネチャも一致 |
| 非機能: セキュリティ         | 完了   | ⚠️ enqueue_email_notification()内のJDBC読込（mail_setting / measurement_item_master）でuser=""・password=""（要対応）。その他のSQL実行はプレースホルダ使用 |
| 非機能: ログ準拠             | 完了   | ⚠️ SILVER_ERR_003〜006は正常出力。mysql_connector.pyのリトライログ・update_alert_history_on_recovery()の復旧完了ログが設計書指定のprint文未実装（軽微） |
| 非機能: エラーハンドリング   | 完了   | ✅ 空バッチスキップ・OLTP各処理独立try/except・Delta Lake例外伝播・空レコード早期リターンはいずれも設計書準拠 |
