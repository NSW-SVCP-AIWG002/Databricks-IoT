"""
シルバー層LDPパイプライン モデル層 - 単体テスト
対象モジュール: silver_ldp_pipeline.pipeline
設計書: docs/03-features/ldp-pipeline/silver-layer/ldp-pipeline-specification.md
"""

import pytest

# NOTE: 実装前のテストファースト。実装後は以下のインポートが有効になる
# from silver_ldp_pipeline.pipeline import MEASUREMENT_COLUMN_MAP

# ===========================================================================
# 測定項目IDとセンサーカラムの対応マップ
# 設計書: § 測定項目IDとセンサーカラムの対応
# ===========================================================================

@pytest.mark.unit
class TestMeasurementColumnMap:
    """測定項目IDとセンサーカラム名の対応マップを検証する

    観点: アラート処理仕様 > 測定項目IDとセンサーカラムの対応
    対応観点表: 2.1（正常系処理）, 1.1.6（不整値チェック）
    設計書定義: measurement_item_id 1〜22 の22エントリ
    """

    def test_map_contains_all_22_entries(self):
        """2.1.1: マップに22エントリが存在する

        実行内容: MEASUREMENT_COLUMN_MAP のエントリ数を検証
        想定結果: エントリ数が22である
        """
        from silver_ldp_pipeline.pipeline import MEASUREMENT_COLUMN_MAP
        # Assert
        assert len(MEASUREMENT_COLUMN_MAP) == 22

    def test_map_keys_are_sequential_1_to_22(self):
        """2.1.1: マップのキーが1〜22の連続した整数である

        実行内容: MEASUREMENT_COLUMN_MAP のキー集合を検証
        想定結果: {1, 2, ..., 22} と一致する
        """
        from silver_ldp_pipeline.pipeline import MEASUREMENT_COLUMN_MAP
        # Assert
        assert set(MEASUREMENT_COLUMN_MAP.keys()) == set(range(1, 23))

    def test_map_values_match_specification(self):
        """2.1.1: マップの各値が設計書定義のカラム名と一致する

        実行内容: MEASUREMENT_COLUMN_MAP の全エントリを設計書の定義と比較
        想定結果: 全エントリが設計書の定義と一致する

        設計書 § 測定項目IDとセンサーカラムの対応 より:
            1: external_temp（共通外気温度）
            2: set_temp_freezer_1（第1冷凍設定温度）
            3: internal_sensor_temp_freezer_1（第1冷凍庫内センサー温度）
            4: internal_temp_freezer_1（第1冷凍表示温度）
            5: df_temp_freezer_1（第1冷凍DF温度）
            6: condensing_temp_freezer_1（第1冷凍凝縮温度）
            7: adjusted_internal_temp_freezer_1（第1冷凍微調整後庫内温度）
            8: set_temp_freezer_2（第2冷凍設定温度）
            9: internal_sensor_temp_freezer_2（第2冷凍庫内センサー温度）
            10: internal_temp_freezer_2（第2冷凍表示温度）
            11: df_temp_freezer_2（第2冷凍DF温度）
            12: condensing_temp_freezer_2（第2冷凍凝縮温度）
            13: adjusted_internal_temp_freezer_2（第2冷凍微調整後庫内温度）
            14: compressor_freezer_1（第1冷凍圧縮機回転数）
            15: compressor_freezer_2（第2冷凍圧縮機回転数）
            16: fan_motor_1（第1ファンモータ回転数）
            17: fan_motor_2（第2ファンモータ回転数）
            18: fan_motor_3（第3ファンモータ回転数）
            19: fan_motor_4（第4ファンモータ回転数）
            20: fan_motor_5（第5ファンモータ回転数）
            21: defrost_heater_output_1（防露ヒータ出力(1)）
            22: defrost_heater_output_2（防露ヒータ出力(2)）
        """
        from silver_ldp_pipeline.pipeline import MEASUREMENT_COLUMN_MAP
        # Arrange
        expected = {
            1:  "external_temp",
            2:  "set_temp_freezer_1",
            3:  "internal_sensor_temp_freezer_1",
            4:  "internal_temp_freezer_1",
            5:  "df_temp_freezer_1",
            6:  "condensing_temp_freezer_1",
            7:  "adjusted_internal_temp_freezer_1",
            8:  "set_temp_freezer_2",
            9:  "internal_sensor_temp_freezer_2",
            10: "internal_temp_freezer_2",
            11: "df_temp_freezer_2",
            12: "condensing_temp_freezer_2",
            13: "adjusted_internal_temp_freezer_2",
            14: "compressor_freezer_1",
            15: "compressor_freezer_2",
            16: "fan_motor_1",
            17: "fan_motor_2",
            18: "fan_motor_3",
            19: "fan_motor_4",
            20: "fan_motor_5",
            21: "defrost_heater_output_1",
            22: "defrost_heater_output_2",
        }
        # Assert
        assert MEASUREMENT_COLUMN_MAP == expected

    def test_map_values_are_all_strings(self):
        """2.1.1: マップの全値が文字列型である

        実行内容: MEASUREMENT_COLUMN_MAP の全値の型を検証
        想定結果: 全値が str 型である
        """
        from silver_ldp_pipeline.pipeline import MEASUREMENT_COLUMN_MAP
        # Assert
        for item_id, column_name in MEASUREMENT_COLUMN_MAP.items():
            assert isinstance(column_name, str), (
                f"measurement_item_id={item_id} のカラム名が文字列でない: {type(column_name)}"
            )
