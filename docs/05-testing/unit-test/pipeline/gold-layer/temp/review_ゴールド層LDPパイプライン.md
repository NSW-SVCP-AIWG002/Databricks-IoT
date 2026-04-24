# テストコードレビュー結果 — ゴールド層LDPパイプライン

| 項目         | 内容 |
| ------------ | ---- |
| レビュー日   | 2026-04-24 |
| 対象ファイル | tests/unit/pipeline/gold/test_gold-ldp-pipeline_service.py |
| テスト項目書 | docs/05-testing/unit-test/pipeline/gold-layer/テスト項目書_ゴールド層LDPパイプライン_Service層.md |

---

## チェックリスト確認結果

| No | チェック項目 | 結果 |
| --- | --- | --- |
| CL-1-1 | DB操作・モデル生成・APIリクエストで明示的に指定している全フィールドをアサートしているか | **NG**（指摘No.1） |
| CL-1-2 | 検索に使用される全フィルター条件が、テスト群全体を通じて少なくとも1件ずつ検証されているか | OK（`sensor_value IS NOT NULL` / `delete_flag = FALSE` をそれぞれ No.19・No.20 で検証済み） |
| CL-2-1 | 外部API・サービス・リポジトリで例外が発生した場合に、例外が上位へ伝播するテストがあるか | OK（No.8〜12 で AnalysisException / PermissionError / RuntimeError の伝播を検証） |
| CL-2-2 | 4xxエラーと5xxエラーのうち代表ケースが最低1件あるか | OK（No.25 で HTTP 500 を検証） |
| CL-3-1〜6 | バリデーション（フォーム層） | N/A（フォーム層なし） |
| CL-4-1〜3 | CSVエクスポート | N/A（該当なし） |
| CL-5-1 | `unittest.mock.patch` のパスがテスト対象モジュール内のimport先を指しているか | **NG**（指摘No.2・No.3） |
| CL-5-2 | 各テストメソッドのdocstringに観点番号と概要が記載されているか | OK（全34メソッドに観点番号付き docstring あり） |
| CL-6-1 | テスト項目書の「テスト総数」とテストコードの実テストメソッド数が一致しているか | OK（テスト項目書 34件・テストコード 34件 が一致） |
| CL-6-2 | テスト項目書のNo列に重複・欠番がないか | OK（No.1〜34 連番、重複なし） |
| CL-6-3 | テストコードに追加・変更があった場合、テスト項目書の内容・総数・連番も更新されているか | OK（本セッションで同時更新済み） |

チェックリスト外の追加確認:

- **コード品質（未参照モック）**: No.13〜17 の ERRORログ確認テストで、`@patch` で宣言したモックパラメータが一部テスト本体で未参照（指摘No.4）
- **テストの配置**: `TestAggregateSensorData`・`TestMergeToGold` がService層ファイルに配置されているが、テスト対象関数（`aggregate_sensor_data` / `merge_to_gold`）はModel層に属する（指摘No.5）

---

## 指摘テーブル

| No | 対象ファイル | 対象テスト / 行 | 指摘内容 | 対応観点 | 修正案 |
|----|-------------|----------------|----------|----------|--------|
| 1 | test_gold-ldp-pipeline_service.py | TestMergeToGold.test_merge_to_gold_executes_successfully / L641〜693 | `whenMatchedUpdate(set=...)` の引数（更新フィールド一覧）が一切アサートされていない。現在は `whenMatchedUpdate.return_value` のチェーンのみで呼び出し引数を検証していないため、更新対象カラムが誤っていてもテストが通過する | CL-1-1 | 実装コードの `whenMatchedUpdate(set={...})` 引数を確認した上で、`mock_gold_table.alias.return_value.merge.return_value.whenMatchedUpdate.assert_called_with(set={...})` を追加する |
| 2 | test_gold-ldp-pipeline_service.py | TestMergeToGold.test_merge_to_gold_executes_successfully / L641<br>TestMergeToGold.test_merge_to_gold_uses_correct_merge_key / L668 | `@patch("delta.tables.DeltaTable")` がモジュール直接参照になっている。実装が `from delta.tables import DeltaTable` を使用している場合、`gold_ldp_pipeline.py` 内のローカル参照はパッチされず、テストが実際のクラスを呼び出す | CL-5-1 | `@patch("pipeline.gold.gold_ldp_pipeline.DeltaTable")` に変更する |
| 3 | test_gold-ldp-pipeline_service.py | TestTeamsNotifier.test_send_error_notification_http_error_retry / L767<br>同 test_send_error_notification_http_error_retry_log_check / L793<br>同 test_send_error_notification_request_exception_retry / L820<br>同 test_send_error_notification_request_exception_retry_log_check / L843<br>同 test_send_error_notification_retry_exhausted / L867 | `@patch("time.sleep")` がモジュール直接参照になっている。実装が `from time import sleep` を使用している場合、`gold_ldp_pipeline.py` 内のローカル参照はパッチされず、実際の `sleep` が呼ばれてテストが遅延または誤動作する | CL-5-1 | 実装の import 方式を確認した上で、`from time import sleep` の場合は `@patch("pipeline.gold.gold_ldp_pipeline.sleep")` に、`import time` の場合は `@patch("pipeline.gold.gold_ldp_pipeline.time.sleep")` に変更する |
| 4 | test_gold-ldp-pipeline_service.py | TestRunAggregation.test_run_aggregation_read_analysis_exception_log_check / L408（`mock_notify`, `mock_aggregate`, `mock_merge` 未参照）<br>同 test_run_aggregation_read_permission_error_log_check / L435（同上）<br>同 test_run_aggregation_read_retry_exhausted_log_check / L462（同上）<br>同 test_run_aggregation_aggregate_error_log_check / L489（`mock_notify`, `mock_merge` 未参照）<br>同 test_run_aggregation_merge_error_log_check / L519（`mock_notify` 未参照） | ERRORログ出力確認テスト（No.13〜17）において、副作用抑制目的で `@patch` 宣言したモックパラメータがテスト本体で一切参照されていない。IDEヒントの発生原因となるほか、副作用が起きていないことを明示的に保証できない | CL-5（コード品質） | 未参照パラメータに対して `mock_notify.assert_not_called()` 等を追加し、副作用の不発生を明示的にアサートする |
| 5 | test_gold-ldp-pipeline_service.py | TestAggregateSensorData（L547〜621）<br>TestMergeToGold（L626〜693） | `aggregate_sensor_data` および `merge_to_gold` はModel層の関数だが、Service層テストファイルに配置されている。Model層テストファイル（`test_gold-ldp-pipeline_model.py`）への配置が望ましい | チェックリスト外（テスト配置） | `test_gold-ldp-pipeline_model.py` にクラスを移動し、Service層ファイルから削除する。なお、現在 Model層ファイルには同名クラスが既に存在するため、重複を解消すること |

---

## 修正後の想定状態

| 項目 | 現状 | 修正後（想定） |
| --- | --- | --- |
| 指摘No.1 | `whenMatchedUpdate` 引数未検証 | 更新フィールドのアサートを追加 |
| 指摘No.2 | `@patch("delta.tables.DeltaTable")` | `@patch("pipeline.gold.gold_ldp_pipeline.DeltaTable")` |
| 指摘No.3 | `@patch("time.sleep")` | `@patch("pipeline.gold.gold_ldp_pipeline.time.sleep")` 等（実装確認後） |
| 指摘No.4 | 未参照モック 5テスト | `assert_not_called()` 等を追加 |
| 指摘No.5 | Service層ファイルに Model層テストが混在 | Model層ファイルへ移動・重複解消 |

> **注:** 指摘No.1 の修正には実装コード（`src/pipeline/gold/gold_ldp_pipeline.py`）の `whenMatchedUpdate(set=...)` 引数の確認が必要。指摘No.3 の修正は実装の `import` 方式の確認が前提となる。
