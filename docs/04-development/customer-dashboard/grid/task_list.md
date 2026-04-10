# customer-dashboard/grid 実装タスクリスト

## タスク一覧

| #   | タスク名                         | 対象ファイル                                                                              | 対応テスト                                                        | 実装フロー状態 | 備考 |
| --- | -------------------------------- | ----------------------------------------------------------------------------------------- | ----------------------------------------------------------------- | -------------- | ---- |
| 1   | フォーム定義                     | `src/iot_app/forms/customer_dashboard/grid.py`                                            | Section 1（gadget_name）, Section 2（group_id）, Section 3（gadget_size） | 完了         |      |
| 2   | サービス層実装（バリデーション・整形・ページング） | `src/iot_app/services/customer_dashboard/grid.py`                         | Section 4（validate_chart_params）, Section 5（format_grid_data）, Section 6（calculate_page_offset） | 完了         |      |
| 3   | サービス層実装（データ取得・カラム定義・CSV）    | `src/iot_app/services/customer_dashboard/grid.py`                         | Section 9（fetch_grid_data）, Section 10（get_column_definition）, Section 11（generate_grid_csv） | 完了         |      |
| 4   | サービス層実装（ガジェット登録・コンテキスト）   | `src/iot_app/services/customer_dashboard/grid.py`                         | Section 7（register_grid_gadget）, Section 8（rollback）, Section 12（get_grid_create_context） | 完了         |      |
| 5   | Viewルーティング実装             | `src/iot_app/views/analysis/customer_dashboard/grid.py`                                   | 統合テスト対象（handle_gadget_data / handle_gadget_create / handle_gadget_register / handle_gadget_csv_export） | 完了         |      |
| 6   | レジストリ・モジュール登録       | `src/iot_app/views/analysis/customer_dashboard/common.py` / `__init__.py`                | -                                                                 | 完了         |      |
| 7   | ガジェットUIテンプレート         | `src/iot_app/templates/analysis/customer_dashboard/gadgets/grid.html`                    | -                                                                 | 完了         |      |
| 8   | 登録モーダルテンプレート         | `src/iot_app/templates/analysis/customer_dashboard/gadgets/modals/grid.html`             | -                                                                 | 完了         |      |
| 9   | JavaScript                       | `src/iot_app/static/js/components/customer_dashboard/grid.js`                            | -                                                                 | 完了         |      |
| 10  | CSS                              | `src/iot_app/static/css/components/customer_dashboard/grid.css`                          | -                                                                 | 完了         |      |

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
| 機能: 設計書との差分         | 完了   | 全サービス関数・View・テンプレートとも設計書仕様に準拠。count_grid_data をworkflow仕様書に基づき追加 |
| 機能: テスト仕様カバレッジ   | 完了   | Section 1-12 の全対象関数を実装済み |
| 機能: インターフェース整合性 | 完了   | view→service→model の引数・戻り値・例外が設計書と一致 |
| 非機能: セキュリティ         | 完了   | check_gadget_access によるデータスコープ制限、プリペアドステートメント使用 |
| 非機能: ログ準拠             | 完了   | エラー時 logger.error + exc_info=True、gadget_uuid をログに含む |
| 非機能: エラーハンドリング   | 完了   | 404/400/500 を適切に処理、DB例外時 rollback 実施 |
