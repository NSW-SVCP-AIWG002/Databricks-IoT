# テスト項目書 - ゴールド層LDPパイプライン Model層

- **対象ファイル**: `src/pipeline/gold/gold_ldp_pipeline.py`
- **テストコード**: `/workspaces/Databricks-IoT/tests/unit/pipeline/gold/test_gold-ldp-pipeline_model.py`
- **観点表**: `docs/05-testing/unit-test/unit-test-perspectives.md`
- **ワークフロー仕様書**: `/workspaces/Databricks-IoT/docs/03-features/ldp-pipeline/gold_layer/ldp-pipeline-specification.md`

---

## 対応表

テストクラスと、ワークフロー仕様書の各ワークフロー・処理フロー項目の対応を示します。

| テストクラス            | テスト項目No. | 対応ワークフロー                           | 処理フロー項目                           | エンドポイント            |
| ----------------------- | :-----------: | ------------------------------------------ | ---------------------------------------- | ------------------------- |
| TestSensorColumns       |     1〜4      | 時次集計処理 / 日次集計処理 / 月次集計処理 | ②共通集計処理（センサーカラム定義）      | `SENSOR_COLUMNS`          |
| TestCreateUnpivotExpr   |     5〜7      | 時次集計処理 / 日次集計処理 / 月次集計処理 | ②共通集計処理（横持ち→縦持ち変換式生成） | `create_unpivot_expr()`   |
| TestAggregationConfig   |     8〜10     | 時次集計処理 / 日次集計処理 / 月次集計処理 | ②共通集計処理（集計設定クラス）          | `AGGREGATION_CONFIGS`     |
| TestAggregateSensorData |    11〜13     | 時次集計処理 / 日次集計処理 / 月次集計処理 | ②共通集計処理（aggregate_sensor_data）   | `aggregate_sensor_data()` |
| TestMergeToGold         |    14〜15     | 時次集計処理 / 日次集計処理 / 月次集計処理 | ③共通書込処理（merge_to_gold）           | `merge_to_gold()`         |

---

## ワークフロー別カバレッジ

ワークフロー仕様書の各ワークフローに対して、どのテストクラスが対応しているかを示します。

### 時次集計処理 / 日次集計処理 / 月次集計処理（共通）

Model層テストは、全3ワークフローが共通で使用するデータ変換定数・集計設定クラスを対象とするため、下表はワークフロー横断で共通です。

| 処理フロー項目                                                 | 対応テストクラス        | テスト項目No. |
| -------------------------------------------------------------- | ----------------------- | :-----------: |
| ②共通集計処理 - センサーカラム定義（SENSOR_COLUMNS）           | TestSensorColumns       |     1〜4      |
| ②共通集計処理 - 横持ち→縦持ち変換式生成（create_unpivot_expr） | TestCreateUnpivotExpr   |     5〜7      |
| ②共通集計処理 - 集計設定クラス（AGGREGATION_CONFIGS）          | TestAggregationConfig   |     8〜10     |
| ②共通集計処理（aggregate_sensor_data）                         | TestAggregateSensorData |    11〜13     |
| ③共通書込処理（merge_to_gold）                                 | TestMergeToGold         |    14〜15     |

---

## テストクラス一覧

テストクラスに対して、テスト観点、操作手順、予想結果を示します。

### TestSensorColumns

| No  | テスト観点             | 操作手順                                                                                            | 予想結果                                                                                                                                       |
| --- | ---------------------- | --------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------- |
| 1   | 1.1.3 数値範囲チェック | `len(SENSOR_COLUMNS)` を確認する。                                                                  | `len(SENSOR_COLUMNS) == 22` であること。                                                                                                       |
| 2   | 1.1.3 数値範囲チェック | `SENSOR_COLUMNS` の全 summary_item をリストに抽出し、`min()` と `max()` を確認する。                | `min(items) == 1` かつ `max(items) == 22` であること。                                                                                         |
| 3   | 1.1.1 必須チェック     | `SENSOR_COLUMNS` の全 summary_item をリストに抽出し、`len(items)` と `len(set(items))` を比較する。 | `len(items) == len(set(items))` であること（summary_item に重複がない）。                                                                      |
| 4   | 2.1.1 正常処理         | `dict(SENSOR_COLUMNS)` で辞書に変換し、item=1, 16, 22 の値を確認する。                              | `col_map[1] == "external_temp"` であること。`col_map[16] == "fan_motor_1"` であること。`col_map[22] == "defrost_heater_output_2"` であること。 |

---

### TestCreateUnpivotExpr

| No  | テスト観点     | 操作手順                                                                                                                      | 予想結果                                                                  |
| --- | -------------- | ----------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------- |
| 5   | 2.1.1 正常処理 | `create_unpivot_expr()` を呼び出す。                                                                                          | 戻り値の文字列に `"stack(22,"` または `"stack(22 "` が含まれること。      |
| 6   | 2.1.1 正常処理 | `create_unpivot_expr()` を呼び出す。`SENSOR_COLUMNS` に定義された全カラム名についてループしながら戻り値に含まれるか確認する。 | `SENSOR_COLUMNS` に定義された全22カラム名が戻り値の文字列に含まれること。 |
| 7   | 2.1.1 正常処理 | `create_unpivot_expr()` を呼び出す。                                                                                          | 戻り値の文字列に `"AS (summary_item, sensor_value)"` が含まれること。     |

---

### TestAggregationConfig

| No  | テスト観点                                   | 操作手順                                                      | 予想結果                                                                                                                                                                                                                                                                                   |
| --- | -------------------------------------------- | ------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| 8   | 2.1.1 正常処理 / CL-1-1 全フィールドアサート | `AGGREGATION_CONFIGS[AggregationPeriod.HOURLY]` を取得する。  | `config.period == AggregationPeriod.HOURLY` であること。`config.output_table == "iot_catalog.gold.gold_sensor_data_hourly_summary"` であること。`config.time_column == "collection_datetime"` であること。`config.time_expr == "event_timestamp"` であること。                             |
| 9   | 2.1.1 正常処理 / CL-1-1 全フィールドアサート | `AGGREGATION_CONFIGS[AggregationPeriod.DAILY]` を取得する。   | `config.period == AggregationPeriod.DAILY` であること。`config.output_table == "iot_catalog.gold.gold_sensor_data_daily_summary"` であること。`config.time_column == "collection_date"` であること。`config.time_expr == "event_date"` であること。                                        |
| 10  | 2.1.1 正常処理 / CL-1-1 全フィールドアサート | `AGGREGATION_CONFIGS[AggregationPeriod.MONTHLY]` を取得する。 | `config.period == AggregationPeriod.MONTHLY` であること。`config.output_table == "iot_catalog.gold.gold_sensor_data_monthly_summary"` であること。`config.time_column == "collection_year_month"` であること。`config.time_expr` に `"DATE_FORMAT"` が含まれ、`"yyyy/MM"` が含まれること。 |

---

### TestAggregateSensorData

| No  | テスト観点                             | 操作手順                                                                                                                                                                                                                                                                                                                                                   | 予想結果                                                                                                                                                                                              |
| --- | -------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 11  | 2.1.1 正常処理                         | `AGGREGATION_CONFIGS[AggregationPeriod.DAILY]` を config として取得する。`pipeline.gold.gold_ldp_pipeline.spark` と `pipeline.gold.gold_ldp_pipeline.F` をモック化する。`spark.table().filter()` が MagicMock（`mock_method_master`）を返すように設定する。silver_df を MagicMock で用意する。`aggregate_sensor_data(mock_silver_df, config)` を呼び出す。 | 戻り値が `None` でない。`silver_df.selectExpr` が1回呼ばれる。`F` は呼ばれない（`mock_F.assert_not_called()`）。                                                                                      |
| 12  | 1.1.1 必須チェック                     | `pipeline.gold.gold_ldp_pipeline.spark` と `pipeline.gold.gold_ldp_pipeline.F` をモック化する（`_ = mock_spark, mock_F` で参照抑制）。silver_df を MagicMock で用意する。`aggregate_sensor_data(mock_silver_df, config)` を `try/except` で呼び出す（後続処理の失敗を許容）。                                                                              | `silver_df.selectExpr().filter` が引数 `"sensor_value IS NOT NULL"` で呼ばれる。                                                                                                                      |
| 13  | 1.1.6 不整値チェック（マスタ存在など） | `pipeline.gold.gold_ldp_pipeline.spark` と `pipeline.gold.gold_ldp_pipeline.F` をモック化する。silver_df を MagicMock で用意する。`aggregate_sensor_data(mock_silver_df, config)` を `try/except` で呼び出す（後続処理の失敗を許容）。                                                                                                                     | `spark.table` が引数 `"iot_catalog.gold.gold_summary_method_master"` で呼ばれる。`spark.table().filter` が引数 `"delete_flag = FALSE"` で呼ばれる。`F` は呼ばれない（`mock_F.assert_not_called()`）。 |

---

### TestMergeToGold

| No  | テスト観点                                   | 操作手順                                                                                                                                                                                                                                                                                                                                                                                                                                                  | 予想結果                                                                                                                                                                                                                                                                                                             |
| --- | -------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 14  | 2.1.1 正常処理                               | `AGGREGATION_CONFIGS[AggregationPeriod.DAILY]` を config として取得する。`delta.tables.DeltaTable` と `pipeline.gold.gold_ldp_pipeline.spark` をモック化する。`DeltaTable.forName()` が `mock_gold_table` を返すように設定する。`mock_gold_table.alias().merge().whenMatchedUpdate().whenNotMatchedInsertAll().execute` を `execute_mock` として取得する。aggregated_df を MagicMock で用意する。`merge_to_gold(mock_aggregated_df, config)` を呼び出す。 | `execute_mock` が1回呼ばれる。`DeltaTable.forName` が `(mock_spark, config.output_table)` の引数で1回呼ばれる。                                                                                                                                                                                                      |
| 15  | 2.1.1 正常処理 / CL-1-1 全フィールドアサート | `delta.tables.DeltaTable` と `pipeline.gold.gold_ldp_pipeline.spark` をモック化する。`DeltaTable.forName()` が `mock_gold_table` を返すように設定する。`merge_to_gold(mock_aggregated_df, config)` を呼び出す。`mock_gold_table.alias().merge` の呼び出し引数（位置引数の2番目: `merge_call.call_args.args[1]`）を `merge_condition` として取得する。                                                                                                     | `merge` が呼ばれる。`merge_condition` に `"device_id"` が含まれる。`merge_condition` に `"organization_id"` が含まれる。`merge_condition` に `config.time_column`（DAILY: `"collection_date"`）が含まれる。`merge_condition` に `"summary_item"` が含まれる。`merge_condition` に `"summary_method_id"` が含まれる。 |

---

## 変更履歴

| 日付       | 版数 | 変更内容 | 担当者       |
| ---------- | ---- | -------- | ------------ |
| 2026-04-24 | 1.0  | 初版作成 | Kei Sugiyama |
