# csv-import-export 実装タスクリスト

## タスク一覧

| #   | タスク名              | 対象ファイル                                                        | 対応テスト                                       | 実装フロー状態 | 備考 |
| --- | --------------------- | ------------------------------------------------------------------- | ------------------------------------------------ | -------------- | ---- |
| 1   | requirements追加      | `requirements.txt`                                                  | -                                                | 完了           | chardet 追加 |
| 2   | Service層実装         | `src/iot_app/services/csv_service.py`                               | `tests/unit/services/test_csv_service.py`（28件） | 完了           | detect_encoding / read_csv / validate_csv_format / apply_data_scope_filter / generate_csv |
| 3   | Form層実装            | `src/iot_app/forms/transfer.py`                                     | `tests/unit/forms/test_transfer.py`（9件）        | 完了           | CSVImportForm（SelectField + FileField + FileSize） |
| 4   | Blueprint定義         | `src/iot_app/views/transfer/__init__.py`                            | -                                                | 完了           | transfer_bp 定義 |
| 5   | View層実装            | `src/iot_app/views/transfer/views.py`                               | -                                                | 完了           | GET: csv-import画面 / POST: インポート実行 |
| 6   | Template作成          | `src/iot_app/templates/transfer/`（5ファイル）                       | -                                                | 完了           | csv-import / confirm / loading / success / error |
| 7   | Blueprint登録         | `src/iot_app/__init__.py`                                           | -                                                | 完了           | transfer_bp を create_app() に追加 |

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
| 機能: 設計書との差分         | 未実施 |          |
| 機能: テスト仕様カバレッジ   | 未実施 |          |
| 機能: インターフェース整合性 | 未実施 |          |
| 非機能: セキュリティ         | 未実施 |          |
| 非機能: ログ準拠             | 未実施 |          |
| 非機能: エラーハンドリング   | 未実施 |          |
