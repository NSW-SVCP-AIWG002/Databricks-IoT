"""
ゴールド層LDPパイプライン Service層 単体テスト

対象モジュール: pipeline.gold.gold_ldp_pipeline
対象クラス/関数: run_aggregation, TeamsNotifier, notify_error
"""
import logging
import pytest
import requests
from unittest.mock import MagicMock, patch

try:
    from pyspark.sql.utils import AnalysisException
except ImportError:
    from conftest import AnalysisException  # type: ignore[no-redef]

from pipeline.gold.gold_ldp_pipeline import (  # type: ignore[import]
    AggregationPeriod,
    TeamsNotifier,
    notify_error,
    run_aggregation,
)


# ---------------------------------------------------------------------------
# TestRunAggregation
# ---------------------------------------------------------------------------

@pytest.mark.unit
class TestRunAggregation:
    """run_aggregation 関数 - 集計実行処理

    観点: 2.1.1 正常系処理, 1.3.1 例外伝播, 1.4.1 ログレベル, 2.3.2 副作用チェック
    """

    # ------------------------------------------------------------------
    # 正常系: データあり → 時次集計の集計・書込関数が呼び出される
    # ------------------------------------------------------------------

    @patch("pipeline.gold.gold_ldp_pipeline.merge_to_gold")
    @patch("pipeline.gold.gold_ldp_pipeline.aggregate_sensor_data")
    @patch("pipeline.gold.gold_ldp_pipeline.notify_error")
    @patch("pipeline.gold.gold_ldp_pipeline.spark")
    def test_run_aggregation_hourly_success(
        self, mock_spark, mock_notify, mock_aggregate, mock_merge
    ):
        """2.1.1: 時次集計 データあり → merge_to_gold が呼ばれ正常終了する"""
        # Arrange
        mock_df = MagicMock()
        mock_df.isEmpty.return_value = False
        mock_spark.table.return_value.filter.return_value = mock_df
        mock_aggregate.return_value = MagicMock()

        # Act
        run_aggregation(AggregationPeriod.HOURLY, "event_datetime = '2026-01-28 0:00:00'")

        # Assert: 集計関数が呼び出されること
        mock_aggregate.assert_called_once()
        # Assert: 書込関数が呼び出されること
        mock_merge.assert_called_once()
        # Assert: 異常通知関数は呼び出されないこと
        mock_notify.assert_not_called()
        
    # ------------------------------------------------------------------------------------
    # 正常系: データあり → 日次集計の集計・書込関数が呼び出される（集計対象の違いに依存しないこと）
    # ------------------------------------------------------------------------------------
        
    @patch("pipeline.gold.gold_ldp_pipeline.merge_to_gold")
    @patch("pipeline.gold.gold_ldp_pipeline.aggregate_sensor_data")
    @patch("pipeline.gold.gold_ldp_pipeline.notify_error")
    @patch("pipeline.gold.gold_ldp_pipeline.spark")
    def test_run_aggregation_daily_success(
        self, mock_spark, mock_notify, mock_aggregate, mock_merge
    ):
        """2.1.1: 日次集計 データあり → merge_to_gold が呼ばれ正常終了する"""
        # Arrange
        mock_df = MagicMock()
        mock_df.isEmpty.return_value = False
        mock_spark.table.return_value.filter.return_value = mock_df
        mock_aggregate.return_value = MagicMock()

        # Act
        run_aggregation(AggregationPeriod.DAILY, "event_date = '2026-01-28'")

        # Assert: 集計関数が呼び出されること
        mock_aggregate.assert_called_once()
        # Assert: 書込関数が呼び出されること
        mock_merge.assert_called_once()
        # Assert: 異常通知関数は呼び出されないこと
        mock_notify.assert_not_called()
        
    # ------------------------------------------------------------------------------------
    # 正常系: データあり → 月次集計の集計・書込関数が呼び出される（集計対象の違いに依存しないこと）
    # ------------------------------------------------------------------------------------
        
    @patch("pipeline.gold.gold_ldp_pipeline.merge_to_gold")
    @patch("pipeline.gold.gold_ldp_pipeline.aggregate_sensor_data")
    @patch("pipeline.gold.gold_ldp_pipeline.notify_error")
    @patch("pipeline.gold.gold_ldp_pipeline.spark")
    def test_run_aggregation_monthly_success(
        self, mock_spark, mock_notify, mock_aggregate, mock_merge
    ):
        """2.1.1: 月次集計 データあり → merge_to_gold が呼ばれ正常終了する"""
        # Arrange
        mock_df = MagicMock()
        mock_df.isEmpty.return_value = False
        mock_spark.table.return_value.filter.return_value = mock_df
        mock_aggregate.return_value = MagicMock()

        # Act
        run_aggregation(
            AggregationPeriod.MONTHLY,
            "event_date BETWEEN '2026-01-01' AND '2026-01-31'"
        )

        # Assert: 集計関数が呼び出されること
        mock_aggregate.assert_called_once()
        # Assert: 書込関数が呼び出されること
        mock_merge.assert_called_once()
        # Assert: 異常通知関数は呼び出されないこと
        mock_notify.assert_not_called()
        
    # ------------------------------------------------------------------------------------
    # 正常系: データあり → 時次集計でINFOログが出力される
    # ------------------------------------------------------------------------------------
    
    @patch("pipeline.gold.gold_ldp_pipeline.merge_to_gold")
    @patch("pipeline.gold.gold_ldp_pipeline.aggregate_sensor_data")
    @patch("pipeline.gold.gold_ldp_pipeline.spark")
    def test_run_aggregation_hourly_success_log_check(
        self, mock_spark, mock_aggregate, mock_merge, caplog
    ):
        """2.1.1 / 1.4.1.3: 時次集計 データあり → 正常完了・INFOログが出力される"""
        # Arrange
        mock_df = MagicMock()
        mock_df.isEmpty.return_value = False
        mock_spark.table.return_value.filter.return_value = mock_df
        mock_aggregated = MagicMock()
        mock_aggregated.count.return_value = 100
        mock_aggregate.return_value = mock_aggregated
        mock_merge.return_value = None  # merge_to_gold は戻り値なし

        # Act
        with caplog.at_level(logging.INFO, logger="pipeline.gold.gold_ldp_pipeline"):
            run_aggregation(AggregationPeriod.HOURLY, "event_datetime = '2026-01-28 0:00:00'")

        # Assert: 集計完了のINFOログが出力されること
        assert any(
            "集計完了" in record.message
            for record in caplog.records
            if record.levelno == logging.INFO
        )

    # ------------------------------------------------------------------------------------
    # 正常系: データあり → 日次集計でINFOログが出力される（集計対象の違いに依存しないこと）
    # ------------------------------------------------------------------------------------

    @patch("pipeline.gold.gold_ldp_pipeline.merge_to_gold")
    @patch("pipeline.gold.gold_ldp_pipeline.aggregate_sensor_data")
    @patch("pipeline.gold.gold_ldp_pipeline.spark")
    def test_run_aggregation_daily_success_log_check(
        self, mock_spark, mock_aggregate, mock_merge, caplog
    ):
        """2.1.1 / 1.4.1.3: 日次集計 データあり → 正常完了・INFOログが出力される"""
        # Arrange
        mock_df = MagicMock()
        mock_df.isEmpty.return_value = False
        mock_spark.table.return_value.filter.return_value = mock_df
        mock_aggregated = MagicMock()
        mock_aggregated.count.return_value = 100
        mock_aggregate.return_value = mock_aggregated
        mock_merge.return_value = None
        
        # Act
        with caplog.at_level(logging.INFO, logger="pipeline.gold.gold_ldp_pipeline"):
            run_aggregation(AggregationPeriod.DAILY, "event_date = '2026-01-28'")

        # Assert: 集計完了のINFOログが出力されること
        assert any(
            "集計完了" in record.message
            for record in caplog.records
            if record.levelno == logging.INFO
        )
        
    # ------------------------------------------------------------------------------------
    # 正常系: データあり → 月次集計でINFOログが出力される（集計対象の違いに依存しないこと）
    # ------------------------------------------------------------------------------------
        
    @patch("pipeline.gold.gold_ldp_pipeline.merge_to_gold")
    @patch("pipeline.gold.gold_ldp_pipeline.aggregate_sensor_data")
    @patch("pipeline.gold.gold_ldp_pipeline.spark")
    def test_run_aggregation_monthly_success_log_check(
        self, mock_spark, mock_aggregate, mock_merge, caplog
    ):
        """2.1.1 / 1.4.1.3: 月次集計 データあり → 正常完了・INFOログが出力される"""
        # Arrange
        mock_df = MagicMock()
        mock_df.isEmpty.return_value = False
        mock_spark.table.return_value.filter.return_value = mock_df
        mock_aggregated = MagicMock()
        mock_aggregated.count.return_value = 100
        mock_aggregate.return_value = mock_aggregated
        mock_merge.return_value = None
        
        # Act
        with caplog.at_level(logging.INFO, logger="pipeline.gold.gold_ldp_pipeline"):
            run_aggregation(AggregationPeriod.MONTHLY, "event_date BETWEEN '2026-01-01' AND '2026-01-31'")

        # Assert: 集計完了のINFOログが出力されること
        assert any(
            "集計完了" in record.message
            for record in caplog.records
            if record.levelno == logging.INFO
        )

    # ------------------------------------------------------------------------------------
    # 正常系: データなし → WARNINGログを出力して正常終了する（異常通知なし）
    # ------------------------------------------------------------------------------------

    @patch("pipeline.gold.gold_ldp_pipeline.merge_to_gold")
    @patch("pipeline.gold.gold_ldp_pipeline.aggregate_sensor_data")
    @patch("pipeline.gold.gold_ldp_pipeline.notify_error")
    @patch("pipeline.gold.gold_ldp_pipeline.spark")
    def test_run_aggregation_no_data_warns(
        self, mock_spark, mock_notify, mock_aggregate, mock_merge, caplog
    ):
        """1.4.1.2: 対象データなし → GOLD_WARN_001 WARNINGログを出力して正常終了する（通知なし）"""
        # Arrange
        mock_df = MagicMock()
        mock_df.isEmpty.return_value = True
        mock_spark.table.return_value.filter.return_value = mock_df

        # Act
        with caplog.at_level(logging.WARNING, logger="pipeline.gold.gold_ldp_pipeline"):
            run_aggregation(AggregationPeriod.DAILY, "event_date = '2026-01-28'")

        # Assert: 書込関数は呼ばれないこと
        mock_merge.assert_not_called()
        # Assert: 集計関数は呼ばれないこと
        mock_aggregate.assert_not_called()
        # Assert: 異常通知関数は呼ばれないこと
        mock_notify.assert_not_called()
        # Assert: GOLD_WARN_001 の WARNING ログが出力されること
        assert any("GOLD_WARN_001: 対象期間のデータが存在しません" in record.message for record in caplog.records)

    # -----------------------------------------------------------------------------------
    # 異常系: データ読込フェーズでのエラーハンドリング（AnalysisException）（異常通知あり）
    # -----------------------------------------------------------------------------------

    @patch("pipeline.gold.gold_ldp_pipeline.merge_to_gold")
    @patch("pipeline.gold.gold_ldp_pipeline.aggregate_sensor_data")
    @patch("pipeline.gold.gold_ldp_pipeline.notify_error")
    @patch("pipeline.gold.gold_ldp_pipeline.spark")
    def test_run_aggregation_read_analysis_exception_no_retry(
        self, mock_spark, mock_notify, mock_aggregate, mock_merge
    ):
        """1.3.1 / 2.3.2: AnalysisException 発生 → リトライなし・notify_error(GOLD_ERR_001)・例外が伝播する"""
        # Arrange
        mock_spark.table.return_value.filter.side_effect = AnalysisException("Table not found")

        # Act & Assert: 上処理にて、AnalysisException が強制的に引き起こされることを検証
        with pytest.raises(AnalysisException):
            run_aggregation(AggregationPeriod.DAILY, "event_date = '2026-01-28'")

        # Assert: filter の呼び出しが 1 回のみであること（リトライなし）
        assert mock_spark.table.return_value.filter.call_count == 1
        # Assert: 異常通知関数が呼び出されること
        mock_notify.assert_called_once()
        # Assert: 異常通知関数の呼び出し引数"error_code"に GOLD_ERR_001 が設定されていること
        assert mock_notify.call_args.kwargs["error_code"] == "GOLD_ERR_001"
        # Assert: 集計関数は呼び出されないこと
        mock_aggregate.assert_not_called()
        # Assert: 書込関数は呼び出されないこと
        mock_merge.assert_not_called()
        
    # -----------------------------------------------------------------------------------
    # 異常系: データ読込フェーズでのエラーハンドリング（PermissionError）（異常通知あり）
    # -----------------------------------------------------------------------------------

    @patch("pipeline.gold.gold_ldp_pipeline.merge_to_gold")
    @patch("pipeline.gold.gold_ldp_pipeline.aggregate_sensor_data")
    @patch("pipeline.gold.gold_ldp_pipeline.notify_error")
    @patch("pipeline.gold.gold_ldp_pipeline.spark")
    def test_run_aggregation_read_permission_error_no_retry(
        self, mock_spark, mock_notify, mock_aggregate, mock_merge
    ):
        """1.3.1 / 2.3.2: PermissionError 発生 → リトライなし・notify_error(GOLD_ERR_001)・例外が伝播する"""
        # Arrange
        mock_spark.table.return_value.filter.side_effect = PermissionError("Access denied")

        # Act & Assert: 上処理にて、PermissionError が強制的に引き起こされることを検証
        with pytest.raises(PermissionError):
            run_aggregation(AggregationPeriod.DAILY, "event_date = '2026-01-28'")

        # Assert: filter の呼び出しが 1 回のみであること（リトライなし）
        assert mock_spark.table.return_value.filter.call_count == 1
        # Assert: 異常通知関数が呼び出されること
        mock_notify.assert_called_once()
        # Assert: 異常通知関数の呼び出し引数"error_code"に GOLD_ERR_001 が設定されていること
        assert mock_notify.call_args.kwargs["error_code"] == "GOLD_ERR_001"
        # Assert: 集計関数は呼び出されないこと
        mock_aggregate.assert_not_called()
        # Assert: 書込関数は呼び出されないこと
        mock_merge.assert_not_called()
        
    # -----------------------------------------------------------------------------------
    # 異常系: データ読込フェーズでのエラーハンドリング（一般例外）（異常通知あり）
    # -----------------------------------------------------------------------------------

    @patch("pipeline.gold.gold_ldp_pipeline.merge_to_gold")
    @patch("pipeline.gold.gold_ldp_pipeline.aggregate_sensor_data")
    @patch("pipeline.gold.gold_ldp_pipeline.notify_error")
    @patch("pipeline.gold.gold_ldp_pipeline.spark")
    def test_run_aggregation_read_retry_exhausted(
        self, mock_spark, mock_notify, mock_aggregate, mock_merge
    ):
        """1.3.1 / 2.3.2: 一般例外が 3 回連続 → MAX_READ_RETRY 後に notify_error(GOLD_ERR_001)・例外が伝播する"""
        # Arrange
        mock_spark.table.return_value.filter.side_effect = RuntimeError("Network error")

        # Act & Assert: 上処理にて、RuntimeError が強制的に引き起こされることを検証
        with pytest.raises(RuntimeError):
            run_aggregation(AggregationPeriod.DAILY, "event_date = '2026-01-28'")

        # Assert: filter の呼び出しが 3 回であること（リトライ回数の上限）
        assert mock_spark.table.return_value.filter.call_count == 3
        # Assert: 異常通知関数が呼び出されること
        mock_notify.assert_called_once()
        # Assert: 異常通知関数の呼び出し引数"error_code"に GOLD_ERR_001 が設定されていること
        assert mock_notify.call_args.kwargs["error_code"] == "GOLD_ERR_001"
        # Assert: 集計関数は呼び出されないこと
        mock_aggregate.assert_not_called()
        # Assert: 書込関数は呼び出されないこと
        mock_merge.assert_not_called()

    # -----------------------------------------------------------------------------------
    # 異常系: 集計フェーズでのエラーハンドリング（一般例外）（異常通知あり）
    # -----------------------------------------------------------------------------------

    @patch("pipeline.gold.gold_ldp_pipeline.merge_to_gold")
    @patch("pipeline.gold.gold_ldp_pipeline.aggregate_sensor_data")
    @patch("pipeline.gold.gold_ldp_pipeline.notify_error")
    @patch("pipeline.gold.gold_ldp_pipeline.spark")
    def test_run_aggregation_aggregate_error(
        self, mock_spark, mock_notify, mock_aggregate, mock_merge
    ):
        """1.3.1 / 2.3.2: 集計処理で例外 → notify_error(GOLD_ERR_002)・例外が伝播し merge は呼ばれない"""
        # Arrange
        mock_df = MagicMock()
        mock_df.isEmpty.return_value = False
        mock_spark.table.return_value.filter.return_value = mock_df
        # 集計処理で例外を発生させる
        mock_aggregate.side_effect = RuntimeError("Aggregation failed")

        # Act & Assert: 上処理にて、RuntimeError が強制的に引き起こされることを検証
        with pytest.raises(RuntimeError):
            run_aggregation(AggregationPeriod.DAILY, "event_date = '2026-01-28'")

        # Assert: 異常通知関数が呼び出されること
        mock_notify.assert_called_once()
        # Assert: 異常通知関数の呼び出し引数"error_code"に GOLD_ERR_002 が設定されていること
        assert mock_notify.call_args.kwargs["error_code"] == "GOLD_ERR_002"
        # Assert: 書込関数は呼び出されないこと
        mock_merge.assert_not_called()
        
    # -----------------------------------------------------------------------------------
    # 異常系: 書込フェーズでのエラーハンドリング（一般例外）（異常通知あり）
    # -----------------------------------------------------------------------------------

    @patch("pipeline.gold.gold_ldp_pipeline.merge_to_gold")
    @patch("pipeline.gold.gold_ldp_pipeline.aggregate_sensor_data")
    @patch("pipeline.gold.gold_ldp_pipeline.notify_error")
    @patch("pipeline.gold.gold_ldp_pipeline.spark")
    def test_run_aggregation_merge_error(
        self, mock_spark, mock_notify, mock_aggregate, mock_merge
    ):
        """1.3.1 / 2.3.2: MERGE 処理で例外 → notify_error(GOLD_ERR_003)・例外が伝播する"""
        # Arrange
        mock_df = MagicMock()
        mock_df.isEmpty.return_value = False
        mock_spark.table.return_value.filter.return_value = mock_df
        mock_aggregate.return_value = MagicMock()
        # 書込処理で例外を発生させる
        mock_merge.side_effect = RuntimeError("Merge failed")

        # Act & Assert: 上処理にて、RuntimeError が強制的に引き起こされることを検証
        with pytest.raises(RuntimeError):
            run_aggregation(AggregationPeriod.DAILY, "event_date = '2026-01-28'")

        # Assert: 異常通知関数が呼び出されること
        mock_notify.assert_called_once()
        # Assert: 異常通知関数の呼び出し引数"error_code"に GOLD_ERR_003 が設定されていること
        assert mock_notify.call_args.kwargs["error_code"] == "GOLD_ERR_003"

    # -----------------------------------------------------------------------------------
    # 異常系: データ読込フェーズ（AnalysisException）→ ERRORログ出力確認
    # -----------------------------------------------------------------------------------

    @patch("pipeline.gold.gold_ldp_pipeline.merge_to_gold")
    @patch("pipeline.gold.gold_ldp_pipeline.aggregate_sensor_data")
    @patch("pipeline.gold.gold_ldp_pipeline.notify_error")
    @patch("pipeline.gold.gold_ldp_pipeline.spark")
    def test_run_aggregation_read_analysis_exception_log_check(
        self, mock_spark, mock_notify, mock_aggregate, mock_merge, caplog
    ):
        """1.4.1.1: AnalysisException 発生 → GOLD_ERR_001 を含む ERROR レベルのログが出力される"""
        # Arrange
        mock_spark.table.return_value.filter.side_effect = AnalysisException("Table not found")

        # Act
        with caplog.at_level(logging.ERROR, logger="pipeline.gold.gold_ldp_pipeline"):
            with pytest.raises(AnalysisException):
                run_aggregation(AggregationPeriod.DAILY, "event_date = '2026-01-28'")

        # Assert: GOLD_ERR_001 を含む ERROR ログが出力されること
        assert any(
            "GOLD_ERR_001" in record.message
            for record in caplog.records
            if record.levelno == logging.ERROR
        )
        # Assert: 異常通知関数が呼び出されること
        mock_notify.assert_called_once()
        # Assert: 集計関数は呼び出されないこと
        mock_aggregate.assert_not_called()
        # Assert: 書込関数は呼び出されないこと
        mock_merge.assert_not_called()

    # -----------------------------------------------------------------------------------
    # 異常系: データ読込フェーズ（PermissionError）→ ERRORログ出力確認
    # -----------------------------------------------------------------------------------

    @patch("pipeline.gold.gold_ldp_pipeline.merge_to_gold")
    @patch("pipeline.gold.gold_ldp_pipeline.aggregate_sensor_data")
    @patch("pipeline.gold.gold_ldp_pipeline.notify_error")
    @patch("pipeline.gold.gold_ldp_pipeline.spark")
    def test_run_aggregation_read_permission_error_log_check(
        self, mock_spark, mock_notify, mock_aggregate, mock_merge, caplog
    ):
        """1.4.1.1: PermissionError 発生 → GOLD_ERR_001 を含む ERROR レベルのログが出力される"""
        # Arrange
        mock_spark.table.return_value.filter.side_effect = PermissionError("Access denied")

        # Act
        with caplog.at_level(logging.ERROR, logger="pipeline.gold.gold_ldp_pipeline"):
            with pytest.raises(PermissionError):
                run_aggregation(AggregationPeriod.DAILY, "event_date = '2026-01-28'")

        # Assert: GOLD_ERR_001 を含む ERROR ログが出力されること
        assert any(
            "GOLD_ERR_001" in record.message
            for record in caplog.records
            if record.levelno == logging.ERROR
        )
        # Assert: 異常通知関数が呼び出されること
        mock_notify.assert_called_once()
        # Assert: 集計関数は呼び出されないこと
        mock_aggregate.assert_not_called()
        # Assert: 書込関数は呼び出されないこと
        mock_merge.assert_not_called()

    # -----------------------------------------------------------------------------------
    # 異常系: データ読込フェーズ（一般例外リトライ上限）→ ERRORログ出力確認
    # -----------------------------------------------------------------------------------

    @patch("pipeline.gold.gold_ldp_pipeline.merge_to_gold")
    @patch("pipeline.gold.gold_ldp_pipeline.aggregate_sensor_data")
    @patch("pipeline.gold.gold_ldp_pipeline.notify_error")
    @patch("pipeline.gold.gold_ldp_pipeline.spark")
    def test_run_aggregation_read_retry_exhausted_log_check(
        self, mock_spark, mock_notify, mock_aggregate, mock_merge, caplog
    ):
        """1.4.1.1: 一般例外リトライ上限 → GOLD_ERR_001 を含む ERROR レベルのログが出力される"""
        # Arrange
        mock_spark.table.return_value.filter.side_effect = RuntimeError("Network error")

        # Act
        with caplog.at_level(logging.ERROR, logger="pipeline.gold.gold_ldp_pipeline"):
            with pytest.raises(RuntimeError):
                run_aggregation(AggregationPeriod.DAILY, "event_date = '2026-01-28'")

        # Assert: GOLD_ERR_001 を含む ERROR ログが出力されること
        assert any(
            "GOLD_ERR_001" in record.message
            for record in caplog.records
            if record.levelno == logging.ERROR
        )
        # Assert: 異常通知関数が呼び出されること
        mock_notify.assert_called_once()
        # Assert: 集計関数は呼び出されないこと
        mock_aggregate.assert_not_called()
        # Assert: 書込関数は呼び出されないこと
        mock_merge.assert_not_called()

    # -----------------------------------------------------------------------------------
    # 異常系: 集計フェーズ（RuntimeError）→ ERRORログ出力確認
    # -----------------------------------------------------------------------------------

    @patch("pipeline.gold.gold_ldp_pipeline.merge_to_gold")
    @patch("pipeline.gold.gold_ldp_pipeline.aggregate_sensor_data")
    @patch("pipeline.gold.gold_ldp_pipeline.notify_error")
    @patch("pipeline.gold.gold_ldp_pipeline.spark")
    def test_run_aggregation_aggregate_error_log_check(
        self, mock_spark, mock_notify, mock_aggregate, mock_merge, caplog
    ):
        """1.4.1.1: 集計処理で例外 → GOLD_ERR_002 を含む ERROR レベルのログが出力される"""
        # Arrange
        mock_df = MagicMock()
        mock_df.isEmpty.return_value = False
        mock_spark.table.return_value.filter.return_value = mock_df
        mock_aggregate.side_effect = RuntimeError("Aggregation failed")

        # Act
        with caplog.at_level(logging.ERROR, logger="pipeline.gold.gold_ldp_pipeline"):
            with pytest.raises(RuntimeError):
                run_aggregation(AggregationPeriod.DAILY, "event_date = '2026-01-28'")

        # Assert: GOLD_ERR_002 を含む ERROR ログが出力されること
        assert any(
            "GOLD_ERR_002" in record.message
            for record in caplog.records
            if record.levelno == logging.ERROR
        )
        # Assert: 異常通知関数が呼び出されること
        mock_notify.assert_called_once()
        # Assert: 書込関数は呼び出されないこと
        mock_merge.assert_not_called()

    # -----------------------------------------------------------------------------------
    # 異常系: 書込フェーズ（RuntimeError）→ ERRORログ出力確認
    # -----------------------------------------------------------------------------------

    @patch("pipeline.gold.gold_ldp_pipeline.merge_to_gold")
    @patch("pipeline.gold.gold_ldp_pipeline.aggregate_sensor_data")
    @patch("pipeline.gold.gold_ldp_pipeline.notify_error")
    @patch("pipeline.gold.gold_ldp_pipeline.spark")
    def test_run_aggregation_merge_error_log_check(
        self, mock_spark, mock_notify, mock_aggregate, mock_merge, caplog
    ):
        """1.4.1.1: MERGE 処理で例外 → GOLD_ERR_003 を含む ERROR レベルのログが出力される"""
        # Arrange
        mock_df = MagicMock()
        mock_df.isEmpty.return_value = False
        mock_spark.table.return_value.filter.return_value = mock_df
        mock_aggregate.return_value = MagicMock()
        mock_merge.side_effect = RuntimeError("Merge failed")

        # Act
        with caplog.at_level(logging.ERROR, logger="pipeline.gold.gold_ldp_pipeline"):
            with pytest.raises(RuntimeError):
                run_aggregation(AggregationPeriod.DAILY, "event_date = '2026-01-28'")

        # Assert: GOLD_ERR_003 を含む ERROR ログが出力されること
        assert any(
            "GOLD_ERR_003" in record.message
            for record in caplog.records
            if record.levelno == logging.ERROR
        )
        # Assert: 異常通知関数が呼び出されること
        mock_notify.assert_called_once()

# ---------------------------------------------------------------------------
# TestTeamsNotifier
# ---------------------------------------------------------------------------

@pytest.mark.unit
class TestTeamsNotifier:
    """TeamsNotifier - Teams 通知クラス

    観点: 2.1.1 正常系処理, 1.3.1 例外伝播
    """

    def setup_method(self):
        self.webhook_url = "https://teams.webhook.example.com/test"
        self.base_args = {
            "error_code": "GOLD_ERR_001",
            "error_message": "シルバー層からのデータ読込に失敗しました",
            "pipeline_name": "gold_sensor_data_daily_summary",
            "target_date": "2026-01-28",
        }
        
    # -----------------------------------------------------------------------------------
    # 正常系: Postリクエスト成功 → Trueを返却する
    # -----------------------------------------------------------------------------------

    @patch("pipeline.gold.gold_ldp_pipeline.requests.post")
    def test_send_error_notification_success(self, mock_post):
        """2.1.1: HTTP 200 → True を返却する"""
        # Arrange
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response
        notifier = TeamsNotifier(webhook_url=self.webhook_url, timeout=30, retry_count=3)

        # Act: TeamsNotifier.send_error_notification を呼び出す
        result = notifier.send_error_notification(**self.base_args)

        # Assert: True を返すこと
        assert result is True
        # Assert: requests.post が1回呼び出されること
        mock_post.assert_called_once()
        # Assert: requests.post の呼び出し引数に webhook_url が含まれること
        call_args = mock_post.call_args
        assert call_args.args[0] == self.webhook_url
        
    # -----------------------------------------------------------------------------------
    # 正常系: Postリクエスト成功 → INFOログを出力する
    # -----------------------------------------------------------------------------------

    @patch("pipeline.gold.gold_ldp_pipeline.requests.post")
    def test_send_error_notification_success_log_check(self, mock_post, caplog):
        """2.1.1: HTTP 200 → INFOログを出力する"""
        # Arrange
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response
        notifier = TeamsNotifier(webhook_url=self.webhook_url, timeout=30, retry_count=3)

        # Act: TeamsNotifier.send_error_notification を呼び出す
        with caplog.at_level(logging.INFO, logger="pipeline.gold.gold_ldp_pipeline"):
            result = notifier.send_error_notification(**self.base_args)

        # Assert: Teams通知送信成功のINFOログが出力されること
        assert any(
            "Teams通知送信成功" in record.message
            for record in caplog.records
            if record.levelno == logging.INFO
        )
        
    # -----------------------------------------------------------------------------------
    # 異常系: Postリクエスト失敗 → リトライする（本テストケースでは2回を想定）
    # -----------------------------------------------------------------------------------

    @patch("time.sleep")
    @patch("pipeline.gold.gold_ldp_pipeline.requests.post")
    def test_send_error_notification_http_error_retry(self, mock_post, mock_sleep):
        """2.1.1: HTTP 500 → retry_count 回だけリトライして False を返し、指数バックオフの sleep が呼ばれる"""
        # Arrange
        mock_response = MagicMock()
        # Arrange: HTTP 500 を返すように設定
        mock_response.status_code = 500
        mock_post.return_value = mock_response
        # Arrange: retry_count=2 の TeamsNotifier を作成
        notifier = TeamsNotifier(webhook_url=self.webhook_url, timeout=30, retry_count=2)

        # Act: TeamsNotifier.send_error_notification を呼び出す
        result = notifier.send_error_notification(**self.base_args)

        # Assert: False を返すこと
        assert result is False
        # Assert: requests.post が retry_count 回呼び出されること（初回 + リトライ回数）
        assert mock_post.call_count == 2
        # retry_count=2 の場合: attempt 0 → sleep(1)、attempt 1 は最後なので sleep なし
        mock_sleep.assert_called_once_with(1)
        
    # -----------------------------------------------------------------------------------
    # 異常系: Postリクエスト失敗 → リトライ中にWARNログを出力する
    # -----------------------------------------------------------------------------------

    @patch("time.sleep")
    @patch("pipeline.gold.gold_ldp_pipeline.requests.post")
    def test_send_error_notification_http_error_retry_log_check(self, mock_post, mock_sleep, caplog):
        """2.1.1: HTTP 500 → retry_count 回だけリトライして False を返し、指数バックオフの sleep が呼ばれる"""
        # Arrange
        mock_response = MagicMock()
        # Arrange: HTTP 500 を返すように設定
        mock_response.status_code = 500
        mock_post.return_value = mock_response
        # Arrange: retry_count=2 の TeamsNotifier を作成
        notifier = TeamsNotifier(webhook_url=self.webhook_url, timeout=30, retry_count=2)

        # Act: TeamsNotifier.send_error_notification を呼び出す
        with caplog.at_level(logging.WARN, logger="pipeline.gold.gold_ldp_pipeline"):
            result = notifier.send_error_notification(**self.base_args)

        # Assert: Teams通知送信失敗のWARNログが出力されること
        assert any(
            "Teams通知送信失敗" in record.message
            for record in caplog.records
            if record.levelno == logging.WARN
        )
        
    # --------------------------------------------------------------------------------------------
    # 異常系: Postリクエスト時、RequestException 発生 → リトライする（本テストケースでは2回を想定）
    # --------------------------------------------------------------------------------------------

    @patch("time.sleep")
    @patch("pipeline.gold.gold_ldp_pipeline.requests.post")
    def test_send_error_notification_request_exception_retry(self, mock_post, mock_sleep):
        """1.3.1: RequestException 発生 → retry_count 回だけリトライして False を返し、指数バックオフの sleep が呼ばれる"""
        # Arrange: requests.post が RequestException を発生させるように設定
        mock_post.side_effect = requests.exceptions.RequestException("Connection error")
        # Arrange: retry_count=2 の TeamsNotifier を作成
        notifier = TeamsNotifier(webhook_url=self.webhook_url, timeout=30, retry_count=2)

        # Act: TeamsNotifier.send_error_notification を呼び出す
        result = notifier.send_error_notification(**self.base_args)

        # Assert: False を返すこと
        assert result is False
        # Assert: requests.post が retry_count 回呼び出されること（初回 + リトライ回数）
        assert mock_post.call_count == 2
        # retry_count=2 の場合: attempt 0 → sleep(1)、attempt 1 は最後なので sleep なし
        mock_sleep.assert_called_once_with(1)
        
    # --------------------------------------------------------------------------------------------
    # 異常系: Postリクエスト時、RequestException 発生 → WARNログを出力する
    # --------------------------------------------------------------------------------------------

    @patch("time.sleep")
    @patch("pipeline.gold.gold_ldp_pipeline.requests.post")
    def test_send_error_notification_request_exception_retry_log_check(self, mock_post, mock_sleep, caplog):
        """1.3.1: RequestException 発生 → retry_count 回だけリトライして False を返し、指数バックオフの sleep が呼ばれる"""
        # Arrange: requests.post が RequestException を発生させるように設定
        mock_post.side_effect = requests.exceptions.RequestException("Connection error")
        # Arrange: retry_count=2 の TeamsNotifier を作成
        notifier = TeamsNotifier(webhook_url=self.webhook_url, timeout=30, retry_count=2)

        # Act: TeamsNotifier.send_error_notification を呼び出す
        with caplog.at_level(logging.WARN, logger="pipeline.gold.gold_ldp_pipeline"):
            result = notifier.send_error_notification(**self.base_args)

        # Assert: Teams通知送信エラーのWARNログが出力されること
        assert any(
            "Teams通知送信エラー" in record.message
            for record in caplog.records
            if record.levelno == logging.WARN
        )
        
    # --------------------------------------------------------------------------------------------
    # 異常系: リトライ上限到達 → ERRORログを出力し、False を返す（本テストケースでは3回リトライして失敗する想定）
    # --------------------------------------------------------------------------------------------

    @patch("time.sleep")
    @patch("pipeline.gold.gold_ldp_pipeline.requests.post")
    def test_send_error_notification_retry_exhausted(self, mock_post, mock_sleep, caplog):
        """2.3.2 / 1.4.1.1: リトライ上限到達 → False を返却・ERROR ログを出力し指数バックオフの sleep が 2 回呼ばれる"""
        # Arrange
        mock_post.side_effect = requests.exceptions.RequestException("Connection error")
        notifier = TeamsNotifier(webhook_url=self.webhook_url, timeout=30, retry_count=3)

        # Act
        with caplog.at_level(logging.ERROR, logger="pipeline.gold.gold_ldp_pipeline"):
            result = notifier.send_error_notification(**self.base_args)

        # Assert
        assert result is False
        assert any(
            "Teams通知送信失敗（リトライ上限）" in record.message
            for record in caplog.records
            if record.levelno == logging.ERROR
        )
        # retry_count=3 の場合: attempt 0 → sleep(1)、attempt 1 → sleep(2)、attempt 2 は最後なので sleep なし
        assert mock_sleep.call_count == 2


# ---------------------------------------------------------------------------
# TestBuildAdaptiveCard
# ---------------------------------------------------------------------------

@pytest.mark.unit
class TestBuildAdaptiveCard:
    """TeamsNotifier._build_adaptive_card - Adaptive Card 構築

    観点: 2.1.1 正常系処理（CL-1-1: 全必須フィールドのアサート）
    """

    def setup_method(self):
        self.notifier = TeamsNotifier(webhook_url="https://teams.webhook.example.com/test")
        
    # ------------------------------------------------------------------------------------------------------------
    # 正常系: エラーコードが『GOLD_ERR_XXX』として渡されたとき、タイトルに「[高]」が含まれ、color が attention になること
    # ------------------------------------------------------------------------------------------------------------

    def test_build_adaptive_card_err_priority_high(self):
        """2.1.1: GOLD_ERR_XXX → タイトルに「[高]」・color が attention"""
        
        # Arrange / Act: Adaptive Card を構築するための引数を指定して _build_adaptive_card を呼び出す
        card = self.notifier._build_adaptive_card(
            error_code="GOLD_ERR_001",
            error_message="テストエラー",
            pipeline_name="gold_sensor_data_daily_summary",
            target_date="2026-01-28",
        )

        # Assert
        body = card["attachments"][0]["content"]["body"]
        title_block = next(b for b in body if b.get("type") == "TextBlock")
        
        # Assert: タイトルに「[高]」が含まれること
        assert "[高]" in title_block["text"]
        # Assert: color が attention であること
        assert title_block["color"] == "attention"
        
    # ------------------------------------------------------------------------------------------------------------
    # 正常系: エラーコードが『GOLD_WARN_XXX』として渡されたとき、タイトルに「[中]」が含まれ、color が warning になること
    # ------------------------------------------------------------------------------------------------------------

    def test_build_adaptive_card_warn_priority_medium(self):
        """2.1.1: GOLD_WARN_XXX → タイトルに「[中]」・color が warning"""
        
        # Arrange / Act: Adaptive Card を構築するための引数を指定して _build_adaptive_card を呼び出す
        card = self.notifier._build_adaptive_card(
            error_code="GOLD_WARN_002",
            error_message="スキップ警告",
            pipeline_name="gold_sensor_data_daily_summary",
            target_date="2026-01-28",
        )

        # Assert
        body = card["attachments"][0]["content"]["body"]
        title_block = next(b for b in body if b.get("type") == "TextBlock")
        
        # Assert: タイトルに「[中]」が含まれること
        assert "[中]" in title_block["text"]
        # Assert: color が warning であること
        assert title_block["color"] == "warning"
        
    # ------------------------------------------------------------------------------------------------------------
    # 正常系: 全必須項目が Adaptive Card の FactSet に含まれること（CL-1-1）
    # ------------------------------------------------------------------------------------------------------------

    def test_build_adaptive_card_required_fields(self):
        """2.1.1 / CL-1-1: 全必須フィールド（エラーコード・エラー内容・発生日時・パイプライン・処理対象日）が FactSet に含まれる"""
        # Arrange
        error_code = "GOLD_ERR_001"
        error_message = "シルバー層からのデータ読込に失敗しました"
        pipeline_name = "gold_sensor_data_daily_summary"
        target_date = "2026-01-28"

        # Act: Adaptive Card を構築するための引数を指定して _build_adaptive_card を呼び出す
        card = self.notifier._build_adaptive_card(
            error_code=error_code,
            error_message=error_message,
            pipeline_name=pipeline_name,
            target_date=target_date,
        )

        body = card["attachments"][0]["content"]["body"]
        fact_set = next(b for b in body if b.get("type") == "FactSet")
        facts = {f["title"]: f["value"] for f in fact_set["facts"]}
        
        # Assert: エラーコードが FactSet に含まれること
        assert facts["エラーコード"] == error_code
        # Assert: エラー内容が FactSet に含まれること
        assert facts["エラー内容"] == error_message
        # Assert: パイプライン名が FactSet に含まれること
        assert facts["パイプライン"] == pipeline_name
        # Assert: 処理対象日が FactSet に含まれること
        assert facts["処理対象日"] == target_date
        # Assert: 発生日時が FactSet に含まれること
        assert "発生日時" in facts
        
    # ------------------------------------------------------------------------------------------------------------
    # 正常系: Stack Trace が 500 文字を超える場合 → カードには先頭 500 文字のみが含まれること
    # ------------------------------------------------------------------------------------------------------------

    def test_build_adaptive_card_with_stack_trace(self):
        """2.1.1: stack_trace 指定時 → 先頭 500 文字がカードに含まれ、501 文字目以降は含まれない"""
        # Arrange
        long_trace = "Traceback...\n" + "x" * 600

        # Act: Adaptive Card を構築するための引数を指定して _build_adaptive_card を呼び出す
        card = self.notifier._build_adaptive_card(
            error_code="GOLD_ERR_001",
            error_message="エラー",
            pipeline_name="gold_sensor_data_daily_summary",
            target_date="2026-01-28",
            stack_trace=long_trace,
        )

        # bodyパート内のTextBlock属性を持つ者のうち、「詳細情報」を含むテキストを持つものを抽出
        body = card["attachments"][0]["content"]["body"]
        detail_block = next(
            (b for b in body if b.get("type") == "TextBlock" and "詳細情報" in b.get("text", "")),
            None,
        )
        
        # Assert: 詳細情報ブロックが存在すること
        assert detail_block is not None
        # Assert: 詳細情報ブロックのテキストに、stack_trace の先頭 500 文字が含まれること
        assert long_trace[:500] in detail_block["text"]
        # Assert: 詳細情報ブロックのテキストに、stack_trace の 501 文字目以降が含まれないこと
        assert long_trace[500:] not in detail_block["text"]


# ---------------------------------------------------------------------------
# TestNotifyError
# ---------------------------------------------------------------------------

@pytest.mark.unit
class TestNotifyError:
    """notify_error 関数 - Teams エラー通知ヘルパー（dbutils.secrets + TeamsNotifier のラッパー）

    観点: 2.1.1 正常系処理
    """
    
    # ------------------------------------------------------------------------------------------------------------
    # 正常系: TeamsのWebhook URL を dbutils.secrets から取得し、TeamsNotifier.send_error_notification を正しい引数で呼び出す
    # ------------------------------------------------------------------------------------------------------------

    @patch("pipeline.gold.gold_ldp_pipeline.TeamsNotifier")
    @patch("pipeline.gold.gold_ldp_pipeline.dbutils")
    def test_notify_error_calls_teams_notifier(self, mock_dbutils, mock_notifier_class):
        """2.1.1: dbutils.secrets から webhook URL を取得し TeamsNotifier.send_error_notification を正しい引数で呼び出す"""
        # Arrange
        mock_dbutils.secrets.get.return_value = "https://teams.webhook.example.com/test"
        mock_notifier_instance = MagicMock()
        mock_notifier_class.return_value = mock_notifier_instance

        # Act
        notify_error(
            error_code="GOLD_ERR_001",
            error_message="テストエラー",
            pipeline_name="gold_sensor_data_daily_summary",
            target_date="2026-01-28",
        )

        # Assert: dbutils.secrets.get が正しいスコープ・キーで呼ばれること
        mock_dbutils.secrets.get.assert_called_once_with(
            scope="iot-pipeline-secrets",
            key="teams-webhook-url"
        )
        # Assert: TeamsNotifier が取得した webhook_url で生成されること
        mock_notifier_class.assert_called_once_with("https://teams.webhook.example.com/test")
        # Assert: send_error_notification が全引数を正しく渡して呼ばれること
        mock_notifier_instance.send_error_notification.assert_called_once_with(
            error_code="GOLD_ERR_001",
            error_message="テストエラー",
            pipeline_name="gold_sensor_data_daily_summary",
            target_date="2026-01-28",
        )
