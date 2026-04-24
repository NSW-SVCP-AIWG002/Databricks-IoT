"""
ゴールド層LDPパイプライン Model層 単体テスト

対象モジュール: pipeline.gold.gold_ldp_pipeline
対象クラス/関数:
    SENSOR_COLUMNS, create_unpivot_expr,
    AggregationPeriod, AggregationConfig, AGGREGATION_CONFIGS,
    aggregate_sensor_data, merge_to_gold
"""
import pytest
from unittest.mock import MagicMock, patch, call

from pipeline.gold.gold_ldp_pipeline import (  # type: ignore[import]
    SENSOR_COLUMNS,
    create_unpivot_expr,
    AggregationPeriod,
    AGGREGATION_CONFIGS,
    aggregate_sensor_data,
    merge_to_gold,
)


# ---------------------------------------------------------------------------
# TestSensorColumns
# ---------------------------------------------------------------------------

@pytest.mark.unit
class TestSensorColumns:
    """SENSOR_COLUMNS - センサーカラム定義（summary_item と カラム名のマッピング）

    観点: 1.1.3 数値範囲チェック（summary_item が 1〜22 の範囲）, 1.1.1 必須チェック（重複なし）
    """

    # -----------------------------------------------------------------------------------
    # 数値範囲チェック: 定数定義されたセンサーカラムの総数の確認
    # -----------------------------------------------------------------------------------
    
    def test_sensor_columns_count(self):
        """1.1.3: SENSOR_COLUMNS が設計書通り 22 件定義されている"""
        
        # Assert: SENSOR_COLUMNS の件数が 22 件であること
        assert len(SENSOR_COLUMNS) == 22

    # -----------------------------------------------------------------------------------
    # 数値範囲チェック: 定数定義されたセンサーカラムの範囲の確認
    # -----------------------------------------------------------------------------------

    def test_sensor_columns_item_range(self):
        """1.1.3: summary_item が 1〜22 の範囲内にある（最小値=1, 最大値=22）"""
        items = [item for item, _ in SENSOR_COLUMNS]
        
        # Assert: summary_item の最小値が 1 であること
        assert min(items) == 1
        #Assert: summary_item の最大値が 22 であること
        assert max(items) == 22
    
    # -----------------------------------------------------------------------------------
    # 必須（重複）チェック: 定数定義されたセンサーカラムの重複有無の確認
    # -----------------------------------------------------------------------------------

    def test_sensor_columns_unique_items(self):
        """1.1.1: summary_item に重複がない（22 件すべて一意）"""
        items = [item for item, _ in SENSOR_COLUMNS]
        
        # Assert: summary_item に重複がないこと（リストの件数とセットの件数が同じであること）
        assert len(items) == len(set(items))
        
    # -----------------------------------------------------------------------------------
    # 代表項目チェック: 定数定義されたセンサーカラムの代表項目の確認
    # -----------------------------------------------------------------------------------

    def test_sensor_columns_known_items(self):
        """2.1.1: 代表項目の定義が設計書と一致する（item=1: external_temp, item=16: fan_motor_1, item=22: defrost_heater_output_2）"""
        col_map = dict(SENSOR_COLUMNS)
        
        # Assert: item=1 が external_temp であること
        assert col_map[1] == "external_temp"
        # Assert: item=16 が fan_motor_1 であること
        assert col_map[16] == "fan_motor_1"
        # Asssert: item=22 が defrost_heater_output_2 であること
        assert col_map[22] == "defrost_heater_output_2"

# ---------------------------------------------------------------------------
# TestCreateUnpivotExpr
# ---------------------------------------------------------------------------

@pytest.mark.unit
class TestCreateUnpivotExpr:
    """create_unpivot_expr - stack 関数式生成（横持ち→縦持ち変換）

    観点: 2.1.1 正常系処理
    """
    # -----------------------------------------------------------------------------------
    # stack 関数の引数数チェック: stack(22, ...) が生成される
    # -----------------------------------------------------------------------------------
    
    def test_create_unpivot_expr_stack_count(self):
        """2.1.1: stack(22, ...) が生成される（センサー項目数 = 22）"""
        
        # Act: create_unpivot_expr を呼び出して式を取得
        expr = create_unpivot_expr()
        
        # Assert: stack(22, ...) が式に含まれること（スペースの有無を考慮して両方チェック）
        assert "stack(22," in expr or "stack(22 " in expr
        
    # -----------------------------------------------------------------------------------
    # stack 関数の引数内容チェック: 定数定義された全 22 カラム名が stack 式に含まれる
    # -----------------------------------------------------------------------------------

    def test_create_unpivot_expr_contains_all_columns(self):
        """2.1.1: 全 22 カラム名が stack 式に含まれる"""
        
        # Act: create_unpivot_expr を呼び出して式を取得
        expr = create_unpivot_expr()
        
        # Assert: SENSOR_COLUMNS に定義された全 22 カラム名が式に含まれること
        for _, col_name in SENSOR_COLUMNS:
            assert col_name in expr, f"カラム名 '{col_name}' が式に含まれていない"
            
    # -----------------------------------------------------------------------------------
    # AS エイリアスチェック: AS (summary_item, sensor_value) のエイリアスが含まれる
    # -----------------------------------------------------------------------------------

    def test_create_unpivot_expr_alias(self):
        """2.1.1: AS (summary_item, sensor_value) のエイリアスが含まれる"""
        
        # Act: create_unpivot_expr を呼び出して式を取得
        expr = create_unpivot_expr()
        
        # Assert: AS (summary_item, sensor_value) のエイリアスが式に含まれること
        assert "AS (summary_item, sensor_value)" in expr

# ---------------------------------------------------------------------------
# TestAggregationConfig
# ---------------------------------------------------------------------------

@pytest.mark.unit
class TestAggregationConfig:
    """AggregationConfig / AGGREGATION_CONFIGS - 集計設定クラス

    観点: 2.1.1 正常系処理（CL-1-1: 全フィールドをアサート）
    """
    
    # -----------------------------------------------------------------------------------
    # HOURLY 設定 - 全フィールドが設計書と一致する
    # -----------------------------------------------------------------------------------

    def test_aggregation_config_hourly(self):
        """2.1.1 / CL-1-1: HOURLY 設定 - 全フィールドが設計書と一致する"""
        
        # Act: AGGREGATION_CONFIGS から HOURLY の設定を取得
        config = AGGREGATION_CONFIGS[AggregationPeriod.HOURLY]

        # Asser: period が AggregationPeriod.HOURLY であること
        assert config.period == AggregationPeriod.HOURLY
        # Assert: output_table が "iot_catalog.gold.gold_sensor_data_hourly_summary" であること
        assert config.output_table == "iot_catalog.gold.gold_sensor_data_hourly_summary"
        # Assert: time_column が "collection_datetime" であること
        assert config.time_column == "collection_datetime"
        # Assert: time_expr が "event_timestamp" であること
        assert config.time_expr == "event_timestamp"

    def test_aggregation_config_daily(self):
        """2.1.1 / CL-1-1: DAILY 設定 - 全フィールドが設計書と一致する"""
        
        # Act: AGGREGATION_CONFIGS から DAILY の設定を取得
        config = AGGREGATION_CONFIGS[AggregationPeriod.DAILY]

        # Assert: period が AggregationPeriod.DAILY であること
        assert config.period == AggregationPeriod.DAILY
        # Assert: output_table が "iot_catalog.gold.gold_sensor_data_daily_summary" であること
        assert config.output_table == "iot_catalog.gold.gold_sensor_data_daily_summary"
        # Assert: time_column が "collection_date" であること
        assert config.time_column == "collection_date"
        # Assert: time_expr が "event_date" であること
        assert config.time_expr == "event_date"

    def test_aggregation_config_monthly(self):
        """2.1.1 / CL-1-1: MONTHLY 設定 - 全フィールドが設計書と一致する"""
        
        # Act: AGGREGATION_CONFIGS から MONTHLY の設定を取得
        config = AGGREGATION_CONFIGS[AggregationPeriod.MONTHLY]

        # Assert: period が AggregationPeriod.MONTHLY であること
        assert config.period == AggregationPeriod.MONTHLY
        # Assert: output_table が "iot_catalog.gold.gold_sensor_data_monthly_summary" であること
        assert config.output_table == "iot_catalog.gold.gold_sensor_data_monthly_summary"
        # Assert: time_column が "collection_year_month" であること
        assert config.time_column == "collection_year_month"
        # Assert: time_expr が "DATE_FORMAT(event_timestamp, 'yyyy/MM')" であること
        assert config.time_expr == "DATE_FORMAT(event_date, 'yyyy/MM')"

# ---------------------------------------------------------------------------
# TestAggregateSensorData
# ---------------------------------------------------------------------------

@pytest.mark.unit
class TestAggregateSensorData:
    """aggregate_sensor_data - 共通集計処理（横持ち→縦持ち変換・統計値計算・マスタ結合）

    観点: 2.1.1 正常系処理, 1.1.1 必須チェック（NULL 除外フィルタ）, 1.1.6 不整値チェック（論理削除マスタ除外）
    """
    # 代表例として日次集計処理を選択し、テスト前に共通の集計設定をセットアップする
    def setup_method(self):
        self.config = AGGREGATION_CONFIGS[AggregationPeriod.DAILY]

    # -----------------------------------------------------------------------------------
    # 正常系: 集計処理正常終了 → 集計結果のDataFrameが返される
    # -----------------------------------------------------------------------------------

    @patch("pipeline.gold.gold_ldp_pipeline.F")
    @patch("pipeline.gold.gold_ldp_pipeline.spark")
    def test_aggregate_sensor_data_returns_result(self, mock_spark, mock_F):
        """2.1.1: 集計処理が正常に完了し DataFrame を返す"""
        # Arrange
        mock_silver_df = MagicMock()
        mock_spark.table.return_value.filter.return_value = MagicMock()

        # Act（Spark 処理は MagicMock チェーンで代替）
        result = aggregate_sensor_data(mock_silver_df, self.config)

        # Assert: 集計結果の DataFrame が返されること（None でないことを確認）
        assert result is not None
        # Assert: silver_df.selectExpr が呼ばれること（横持ち→縦持ち変換の開始を確認）
        mock_silver_df.selectExpr.assert_called_once()
        # Assert: F モジュールは直接呼び出されないこと
        mock_F.assert_not_called()

    # -----------------------------------------------------------------------------------
    # 正常系: シルバー層データ集計時、sensor_value=NULL のレコードが除外される
    # -----------------------------------------------------------------------------------

    @patch("pipeline.gold.gold_ldp_pipeline.F")
    @patch("pipeline.gold.gold_ldp_pipeline.spark")
    def test_aggregate_sensor_data_null_sensor_value_excluded(self, mock_spark, mock_F):
        """1.1.1: sensor_value=NULL のレコードが filter("sensor_value IS NOT NULL") で除外される"""
        # Arrange
        mock_silver_df = MagicMock()
        _ = mock_spark, mock_F  # 副作用抑制のみ・本テストでの検証対象外

        # Act（後続処理が失敗しても NULL フィルタ呼び出しを確認できれば良い）
        try:
            aggregate_sensor_data(mock_silver_df, self.config)
        except Exception:
            pass

        # Assert: selectExpr の戻り値に対して IS NOT NULL フィルタが呼ばれること
        mock_silver_df.selectExpr.return_value.filter.assert_called_with(
            "sensor_value IS NOT NULL"
        )

    # -----------------------------------------------------------------------------------
    # 正常系: サマリ計算手法マスタの取得時、delete_flag=FALSE のレコードのみが対象となる
    # -----------------------------------------------------------------------------------

    @patch("pipeline.gold.gold_ldp_pipeline.F")
    @patch("pipeline.gold.gold_ldp_pipeline.spark")
    def test_aggregate_sensor_data_master_join_excludes_deleted(self, mock_spark, mock_F):
        """1.1.6: delete_flag=TRUE のマスタレコードが結合から除外される（delete_flag = FALSE フィルタ確認）"""
        # Arrange
        mock_silver_df = MagicMock()

        # Act
        try:
            aggregate_sensor_data(mock_silver_df, self.config)
        except Exception:
            pass

        # Assert: gold_summary_method_master に対するクエリが発行されること
        mock_spark.table.assert_called_with("iot_catalog.gold.gold_summary_method_master")
        # Assert: delete_flag = FALSE フィルタが適用されること
        mock_spark.table.return_value.filter.assert_called_with("delete_flag = FALSE")
        # Assert: F モジュールは直接呼び出されないこと
        mock_F.assert_not_called()

# ---------------------------------------------------------------------------
# TestMergeToGold
# ---------------------------------------------------------------------------

@pytest.mark.unit
class TestMergeToGold:
    """merge_to_gold - ゴールド層への MERGE 処理（冪等性確保）

    観点: 2.1.1 正常系処理, CL-1-1: MERGE キー全カラムのアサート
    """

    def setup_method(self):
        self.config = AGGREGATION_CONFIGS[AggregationPeriod.DAILY]
        self.mock_aggregated_df = MagicMock()

    # -----------------------------------------------------------------------------------
    # 正常系: 書込処理正常終了 → execute() が 1 回呼ばれる
    # -----------------------------------------------------------------------------------

    @patch("pipeline.gold.gold_ldp_pipeline.DeltaTable")
    @patch("pipeline.gold.gold_ldp_pipeline.spark")
    def test_merge_to_gold_executes_successfully(self, mock_spark, mock_delta_table):
        """2.1.1: MERGE が例外なく実行され execute() が 1 回呼ばれる"""
        # Arrange
        mock_gold_table = MagicMock()
        mock_delta_table.forName.return_value = mock_gold_table
        execute_mock = (
            mock_gold_table.alias.return_value
            .merge.return_value
            .whenMatchedUpdate.return_value
            .whenNotMatchedInsertAll.return_value
            .execute
        )

        # Act
        merge_to_gold(self.mock_aggregated_df, self.config)

        # Assert: execute() が 1 回呼ばれること
        execute_mock.assert_called_once()
        # Assert: DeltaTable.forName が正しいテーブル名で呼ばれること
        mock_delta_table.forName.assert_called_once_with(mock_spark, self.config.output_table)

    # --------------------------------------------------------------------------------------------------------------
    # 正常系: MERGE キーに device_id / organization_id / time_column / summary_item / summary_method_id が使用されている
    # --------------------------------------------------------------------------------------------------------------

    @patch("pipeline.gold.gold_ldp_pipeline.DeltaTable")
    @patch("pipeline.gold.gold_ldp_pipeline.spark")
    def test_merge_to_gold_uses_correct_merge_key(self, mock_spark, mock_delta_table):
        """2.1.1 / CL-1-1: MERGE キーに設計書記載の全カラム（device_id / organization_id / time_column / summary_item / summary_method_id）が含まれる"""
        # Arrange
        mock_gold_table = MagicMock()
        mock_delta_table.forName.return_value = mock_gold_table
        _ = mock_spark  # 副作用抑制のみ・本テストでの検証対象外

        # Act: 書込処理を実行する（実際の MERGE 処理はモックで代替される）
        merge_to_gold(self.mock_aggregated_df, self.config)

        merge_call = mock_gold_table.alias.return_value.merge

        # Assert: merge 関数が呼び出されること
        assert merge_call.called
        _, merge_condition = merge_call.call_args.args
        # Assert: MERGE キーに device_id が含まれること
        assert "device_id" in merge_condition
        # Assert: MERGE キーに organization_id が含まれること
        assert "organization_id" in merge_condition
        # Assert: MERGE キーに time_column が含まれること
        assert self.config.time_column in merge_condition  # DAILY: "collection_date"
        # Assert: MERGE キーに summary_item が含まれること
        assert "summary_item" in merge_condition
        # Assert: MERGE キーに summary_method_id が含まれること
        assert "summary_method_id" in merge_condition