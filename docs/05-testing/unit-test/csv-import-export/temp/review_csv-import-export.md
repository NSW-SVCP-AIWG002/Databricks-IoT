# レビュー結果: csv-import-export 単体テスト

対象ファイル:
- `tests/unit/services/test_csv_service.py`
- `tests/unit/forms/test_transfer.py`

---

## チェックリスト確認結果

| No     | チェック項目                                                                                         | 結果 | 備考 |
| ------ | ---------------------------------------------------------------------------------------------------- | ---- | ---- |
| CL-1-1 | DB操作で明示的に指定している全フィールドをアサートしているか                                          | OK   | apply_data_scope_filter は filter 呼び出し確認。generate_csv で全10列を検証（CL-4-1/4-2） |
| CL-1-2 | 検索に使用される全フィルター条件が少なくとも1件ずつ検証されているか                                  | OK   | organization_closure によるスコープフィルターを2ケース（有/無）検証 |
| CL-2-1 | 外部API・サービスで例外が発生した場合に例外が上位へ伝播するテストがあるか                            | OK   | test_raises_on_read_error / test_db_exception_propagates |
| CL-2-2 | 4xx/5xxエラーの代表ケースが最低1件あるか                                                             | OK   | Service層のためHTTPエラーは対象外 |
| CL-3-1 | 必須チェック: 1.1.1節の全ケースが揃っているか                                                        | OK   | 空文字・None・有効値のケースあり |
| CL-3-2 | 最大文字列長チェック: 1.1.2節の全ケースが揃っているか                                                | OK   | 対象フィールドに最大文字列長制約なし（N/A） |
| CL-3-3 | 数値範囲チェック: 1.1.3節の全ケースが揃っているか                                                    | OK   | 対象フィールドに数値範囲制約なし（N/A） |
| CL-3-4 | 日付形式チェック: 1.1.4節の全ケースが揃っているか                                                    | OK   | 対象フィールドに日付制約なし（N/A） |
| CL-3-5 | メールアドレス形式チェック: 1.1.5節の全ケースが揃っているか                                          | OK   | 対象フィールドにメール制約なし（N/A） |
| CL-3-6 | 不整値チェック: 1.1.6節の全ケースが揃っているか                                                      | OK   | 許容値・未定義値・空文字・None のケースあり |
| CL-4-1 | ヘッダー行の全列名を検証しているか                                                                    | OK   | test_header_contains_all_columns で10列全て検証 |
| CL-4-2 | データ行の全列の値と列順を検証しているか                                                              | OK   | test_data_row_contains_all_field_values + test_column_order_matches_dict_insertion_order |
| CL-4-3 | None値が空文字で出力されるテストがあるか                                                              | OK   | test_none_value_outputs_empty_string |
| CL-5-1 | patch のパスがテスト対象モジュール内のimport先を指しているか                                          | OK   | MODULE = 'iot_app.services.csv_service' を使用 |
| CL-5-2 | 各テストメソッドのdocstringに観点番号と概要が記載されているか                                        | OK   | 全メソッドに観点番号付きdocstringあり |
| CL-6-1 | テスト項目書の「テスト総数」とテストコードの実テストメソッド数が一致しているか                        | OK   | Service層28件・Form層9件 一致 |
| CL-6-2 | テスト項目書のNo列に重複・欠番がないか                                                                | OK   | Service層1〜28連番・Form層1〜9連番、重複・欠番なし |
| CL-6-3 | テストコードに追加・変更があった場合、テスト項目書の内容・総数・連番も更新されているか                | OK   | 項目書を新規作成（初版） |

---

## 指摘一覧

| No | 対象ファイル | 対象テスト / 行 | 指摘内容 | 対応観点 | 修正案 |
|----|-------------|----------------|----------|----------|--------|
| 1  | test_csv_service.py | test_none_value_outputs_empty_string / L493 | `assert ',,', decoded` は `assert (str, obj)` 形式でありタプルが truthy のため常に True となる | CL-4-3 | `assert ',,' in decoded` に修正 |

## 修正対応

| No | 対応状況 | 修正内容 |
|----|----------|----------|
| 1  | 修正済み | `assert ',,', decoded` → `assert ',,' in decoded` |

---

## テスト件数

| ファイル | テスト件数 |
|---------|-----------|
| test_csv_service.py | 28件 |
| test_transfer.py | 9件 |
| **合計** | **37件** |
