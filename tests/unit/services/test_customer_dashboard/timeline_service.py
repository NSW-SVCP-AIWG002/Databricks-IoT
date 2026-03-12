"""
時系列グラフガジェット サービス層 単体テスト

対象モジュール: iot_app.services.customer_dashboard.timeline_service
参照設計書:
  - docs/03-features/flask-app/customer-dashboard/timeline/ui-specification.md
  - docs/03-features/flask-app/customer-dashboard/timeline/workflow-specification.md
  - docs/03-features/common/logging-specification.md
参照観点表: docs/06-testing/unit-test/unit-test-perspectives.md
"""

import csv
import io
import logging
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from iot_app.services.customer_dashboard.timeline_service import (
    format_timeline_data,
    generate_timeline_csv,
    validate_chart_params,
    validate_gadget_registration,
)


# ============================================================
# TestValidateChartParams
# 観点: 1.1.1 必須チェック、1.1.4 日付形式チェック
# ============================================================

@pytest.mark.unit
class TestValidateChartParams:
    """ガジェットデータ取得パラメータのバリデーション
    観点: 1.1.1 必須チェック、1.1.4 日付形式チェック
    仕様: workflow-specification.md > ガジェットデータ取得 > バリデーション
    """

    # ---- 正常系 ----

    def test_valid_params_returns_true(self):
        """2.1.1: 正常な開始日時・終了日時で True が返る"""
        # Arrange
        start = '2026/02/17 00:00:00'
        end   = '2026/02/17 10:00:00'

        # Act
        result = validate_chart_params(start, end)

        # Assert
        assert result is True

    # ---- 必須チェック (1.1.1) ----

    def test_start_datetime_none_returns_false(self):
        """1.1.2: 開始日時が None の場合 False が返る"""
        # Arrange / Act / Assert
        assert validate_chart_params(None, '2026/02/17 10:00:00') is False

    def test_end_datetime_none_returns_false(self):
        """1.1.1: 終了日時が None の場合 False が返る"""
        # Arrange / Act / Assert
        assert validate_chart_params('2026/02/17 00:00:00', None) is False

    def test_start_datetime_empty_returns_false(self):
        """1.1.1: 開始日時が空文字の場合 False が返る"""
        # Arrange / Act / Assert
        assert validate_chart_params('', '2026/02/17 10:00:00') is False

    def test_end_datetime_empty_returns_false(self):
        """1.1.1: 終了日時が空文字の場合 False が返る"""
        # Arrange / Act / Assert
        assert validate_chart_params('2026/02/17 00:00:00', '') is False

    # ---- 日付形式チェック (1.1.4) ----

    def test_start_datetime_invalid_format_returns_false(self):
        """1.4.3: 開始日時がスラッシュ区切り以外（ハイフン区切り）の場合 False が返る"""
        # Arrange / Act / Assert
        assert validate_chart_params('2026-02-17 00:00:00', '2026/02/17 10:00:00') is False

    def test_end_datetime_invalid_format_returns_false(self):
        """1.4.3: 終了日時がスラッシュ区切り以外（ハイフン区切り）の場合 False が返る"""
        # Arrange / Act / Assert
        assert validate_chart_params('2026/02/17 00:00:00', '2026-02-17 10:00:00') is False

    def test_start_datetime_date_only_returns_false(self):
        """1.4.4: 開始日時に時刻部分がない場合 False が返る（YYYY/MM/DD のみ）"""
        # Arrange / Act / Assert
        assert validate_chart_params('2026/02/17', '2026/02/17 10:00:00') is False

    def test_start_datetime_single_digit_month_returns_false(self):
        """1.4.4: 開始日時の月が1桁（ゼロ埋めなし）の場合 False が返る
        仕様: %Y/%m/%d %H:%M:%S 形式では月はゼロ埋め必須"""
        # Arrange / Act / Assert
        assert validate_chart_params('2026/2/17 00:00:00', '2026/02/17 10:00:00') is False

    def test_start_datetime_invalid_date_returns_false(self):
        """1.4.5: 存在しない日付（2月30日）の場合 False が返る"""
        # Arrange / Act / Assert
        assert validate_chart_params('2026/02/30 00:00:00', '2026/02/17 10:00:00') is False

    def test_leap_year_date_returns_true(self):
        """1.4.6: 閏年の 2/29 は有効な日付として True が返る"""
        # Arrange / Act / Assert
        assert validate_chart_params('2024/02/29 00:00:00', '2024/02/29 10:00:00') is True

    def test_non_leap_year_feb29_returns_false(self):
        """1.4.7: 非閏年の 2/29 は False が返る"""
        # Arrange / Act / Assert
        assert validate_chart_params('2023/02/29 00:00:00', '2023/02/29 10:00:00') is False

    # ---- 開始 < 終了チェック ----

    def test_start_equal_to_end_returns_false(self):
        """開始日時と終了日時が同一の場合 False が返る
        仕様: 開始日時 < 終了日時 であること"""
        # Arrange
        dt = '2026/02/17 00:00:00'

        # Act / Assert
        assert validate_chart_params(dt, dt) is False

    def test_start_after_end_returns_false(self):
        """開始日時が終了日時より後の場合 False が返る
        仕様: 終了日時は開始日時以降の日時を入力してください"""
        # Arrange
        start = '2026/02/17 10:00:00'
        end   = '2026/02/17 00:00:00'

        # Act / Assert
        assert validate_chart_params(start, end) is False

    def test_datetime_range_exceeds_24hours_returns_false(self):
        """終了日時 - 開始日時 > 24時間の場合 False が返る
        仕様: ui-specification.md > 日時範囲の制約 終了日時 - 開始日時 ≤ 24時間
        # TODO: サーバーサイドバリデーションへの適用はワークフロー仕様書に明記なし。要確認"""
        # Arrange
        start = '2026/02/17 00:00:00'
        end   = '2026/02/18 00:00:01'  # 24時間 + 1秒

        # Act / Assert
        assert validate_chart_params(start, end) is False

    def test_datetime_range_exactly_24hours_returns_true(self):
        """終了日時 - 開始日時 = 24時間の場合 True が返る（境界値）
        仕様: ui-specification.md > 日時範囲の制約 終了日時 - 開始日時 ≤ 24時間"""
        # Arrange
        start = '2026/02/17 00:00:00'
        end   = '2026/02/18 00:00:00'  # ちょうど24時間

        # Act / Assert
        assert validate_chart_params(start, end) is True


# ============================================================
# TestFormatTimelineData
# 観点: 2.1 正常系処理
# ============================================================

@pytest.mark.unit
class TestFormatTimelineData:
    """時系列データ整形処理
    観点: 2.1 正常系処理
    仕様: workflow-specification.md > ガジェットデータ取得 > 処理詳細④
    """

    def test_format_returns_labels_and_left_right_values(self):
        """2.1.1: 正常なデータ行リストから labels / left_values / right_values が生成される"""
        # Arrange
        rows = [
            {
                'event_timestamp': datetime(2026, 2, 17, 0, 0, 0),
                'external_temp': 25.5,
                'compressor_freezer_1': 2500.0,
            },
            {
                'event_timestamp': datetime(2026, 2, 17, 0, 1, 0),
                'external_temp': 26.0,
                'compressor_freezer_1': 2480.0,
            },
        ]

        # Act
        result = format_timeline_data(rows, 'external_temp', 'compressor_freezer_1')

        # Assert
        assert result['labels']       == ['2026/02/17 00:00:00', '2026/02/17 00:01:00']
        assert result['left_values']  == [25.5, 26.0]
        assert result['right_values'] == [2500.0, 2480.0]

    def test_format_returns_empty_lists_when_no_rows(self):
        """3.1.4.2: データが 0 件の場合、labels / left_values / right_values がすべて空リストになる"""
        # Arrange
        rows = []

        # Act
        result = format_timeline_data(rows, 'external_temp', 'compressor_freezer_1')

        # Assert
        assert result == {'labels': [], 'left_values': [], 'right_values': []}

    def test_format_timestamp_format(self):
        """2.1.1: event_timestamp が YYYY/MM/DD HH:mm:ss 形式で labels に格納される
        仕様: ui-specification.md > ツールチップ表示形式"""
        # Arrange
        rows = [
            {
                'event_timestamp': datetime(2026, 2, 17, 8, 30, 0),
                'external_temp': 10.0,
                'fan_motor_1': 1200.0,
            }
        ]

        # Act
        result = format_timeline_data(rows, 'external_temp', 'fan_motor_1')

        # Assert
        assert result['labels'][0] == '2026/02/17 08:30:00'

    def test_format_none_sensor_value_preserved(self):
        """2.1.2: センサー値が None の場合もそのまま values に格納される"""
        # Arrange
        rows = [
            {
                'event_timestamp': datetime(2026, 2, 17, 0, 0, 0),
                'external_temp': None,
                'compressor_freezer_1': None,
            }
        ]

        # Act
        result = format_timeline_data(rows, 'external_temp', 'compressor_freezer_1')

        # Assert
        assert result['left_values']  == [None]
        assert result['right_values'] == [None]


# ============================================================
# TestValidateGadgetRegistration
# 観点: 1.1.1 必須チェック、1.1.2 最大文字列長チェック、
#       1.1.3 数値範囲チェック、1.1.6 不整値チェック
# ============================================================

@pytest.mark.unit
class TestValidateGadgetRegistration:
    """ガジェット登録パラメータのバリデーション
    観点: 1.1.1, 1.1.2, 1.1.3, 1.1.6
    仕様: ui-specification.md > バリデーション（ガジェット登録画面）
    """

    def _valid_params(self, **overrides):
        """有効なデフォルトパラメータを返すヘルパー"""
        params = {
            'title':         '時系列テストガジェット',
            'device_mode':   'variable',
            'device_id':     None,
            'group_id':      1,
            'left_item_id':  1,
            'right_item_id': 2,
            'left_min_value':  None,
            'left_max_value':  None,
            'right_min_value': None,
            'right_max_value': None,
            'gadget_size':   '2x2',
        }
        params.update(overrides)
        return params

    # ---- タイトル 必須チェック (1.1.1) ----

    def test_title_none_raises_validation_error(self):
        """1.1.1: タイトルが None の場合 ValidationError が発生する
        エラーメッセージ: タイトルを入力してください"""
        from iot_app.common.exceptions import ValidationError
        params = self._valid_params(title=None)

        with pytest.raises(ValidationError, match='タイトルを入力してください'):
            validate_gadget_registration(params)

    def test_title_empty_raises_validation_error(self):
        """1.1.1: タイトルが空文字の場合 ValidationError が発生する
        エラーメッセージ: タイトルを入力してください"""
        from iot_app.common.exceptions import ValidationError
        params = self._valid_params(title='')

        with pytest.raises(ValidationError, match='タイトルを入力してください'):
            validate_gadget_registration(params)

    def test_title_whitespace_passes(self):
        """1.1.1: タイトルが空白文字のみの場合、ValidationError は発生しない"""
        params = self._valid_params(title='   ')
        validate_gadget_registration(params)

    # ---- タイトル 最大文字列長チェック (1.1.2) ----

    def test_title_19_chars_passes(self):
        """1.2.1: タイトルが 19 文字（最大長-1）の場合は正常終了する"""
        params = self._valid_params(title='あ' * 19)
        # ValidationError が発生しないことを確認
        validate_gadget_registration(params)

    def test_title_20_chars_passes(self):
        """1.2.2: タイトルが 20 文字（最大長ちょうど）の場合は正常終了する
        仕様: タイトルは20文字以内"""
        params = self._valid_params(title='あ' * 20)
        validate_gadget_registration(params)

    def test_title_21_chars_raises_validation_error(self):
        """1.2.3: タイトルが 21 文字（最大長+1）の場合 ValidationError が発生する
        エラーメッセージ: タイトルは20文字以内で入力してください"""
        from iot_app.common.exceptions import ValidationError
        params = self._valid_params(title='あ' * 21)

        with pytest.raises(ValidationError, match='タイトルは20文字以内で入力してください'):
            validate_gadget_registration(params)

    # ---- デバイス選択 必須チェック (デバイス固定モード) (1.1.1) ----

    def test_device_id_none_in_fixed_mode_raises_validation_error(self):
        """1.1.2: デバイス固定モードでデバイスIDが None の場合 ValidationError が発生する
        エラーメッセージ: デバイスを選択してください"""
        from iot_app.common.exceptions import ValidationError
        params = self._valid_params(device_mode='fixed', device_id=None)

        with pytest.raises(ValidationError, match='デバイスを選択してください'):
            validate_gadget_registration(params)

    def test_device_id_none_in_variable_mode_passes(self):
        """デバイス可変モードでは device_id が None でも正常終了する"""
        params = self._valid_params(device_mode='variable', device_id=None)
        validate_gadget_registration(params)

    # ---- グループ選択 必須チェック (1.1.1) ----

    def test_group_id_none_raises_validation_error(self):
        """1.1.2: グループIDが None の場合 ValidationError が発生する
        エラーメッセージ: グループを選択してください"""
        from iot_app.common.exceptions import ValidationError
        params = self._valid_params(group_id=None)

        with pytest.raises(ValidationError, match='グループを選択してください'):
            validate_gadget_registration(params)

    # ---- 左右表示項目 必須チェック (1.1.1) ----

    def test_left_item_id_none_raises_validation_error(self):
        """1.1.2: 左表示項目IDが None の場合 ValidationError が発生する
        エラーメッセージ: 左表示項目を選択してください"""
        from iot_app.common.exceptions import ValidationError
        params = self._valid_params(left_item_id=None)

        with pytest.raises(ValidationError, match='左表示項目を選択してください'):
            validate_gadget_registration(params)

    def test_right_item_id_none_raises_validation_error(self):
        """1.1.2: 右表示項目IDが None の場合 ValidationError が発生する
        エラーメッセージ: 右表示項目を選択してください"""
        from iot_app.common.exceptions import ValidationError
        params = self._valid_params(right_item_id=None)

        with pytest.raises(ValidationError, match='右表示項目を選択してください'):
            validate_gadget_registration(params)

    # ---- 最小値/最大値 数値形式チェック (1.1.3) ----

    def test_left_min_value_non_numeric_raises_validation_error(self):
        """1.3.7: 左表示項目の最小値に数値以外を入力した場合 ValidationError が発生する
        エラーメッセージ: 左表示項目の最小値は数値で入力してください"""
        from iot_app.common.exceptions import ValidationError
        params = self._valid_params(left_min_value='abc')

        with pytest.raises(ValidationError, match='左表示項目の最小値は数値で入力してください'):
            validate_gadget_registration(params)

    def test_left_max_value_non_numeric_raises_validation_error(self):
        """1.3.7: 左表示項目の最大値に数値以外を入力した場合 ValidationError が発生する
        エラーメッセージ: 左表示項目の最大値は数値で入力してください"""
        from iot_app.common.exceptions import ValidationError
        params = self._valid_params(left_max_value='abc')

        with pytest.raises(ValidationError, match='左表示項目の最大値は数値で入力してください'):
            validate_gadget_registration(params)

    def test_right_min_value_non_numeric_raises_validation_error(self):
        """1.3.7: 右表示項目の最小値に数値以外を入力した場合 ValidationError が発生する
        エラーメッセージ: 右表示項目の最小値は数値で入力してください"""
        from iot_app.common.exceptions import ValidationError
        params = self._valid_params(right_min_value='abc')

        with pytest.raises(ValidationError, match='右表示項目の最小値は数値で入力してください'):
            validate_gadget_registration(params)

    def test_right_max_value_non_numeric_raises_validation_error(self):
        """1.3.7: 右表示項目の最大値に数値以外を入力した場合 ValidationError が発生する
        エラーメッセージ: 右表示項目の最大値は数値で入力してください"""
        from iot_app.common.exceptions import ValidationError
        params = self._valid_params(right_max_value='abc')

        with pytest.raises(ValidationError, match='右表示項目の最大値は数値で入力してください'):
            validate_gadget_registration(params)

    # ---- 最小値 < 最大値 チェック (1.1.3) ----

    def test_left_min_equal_to_max_raises_validation_error(self):
        """1.3.5 / 1.3.6: 左の最小値 = 最大値の場合 ValidationError が発生する
        エラーメッセージ: 左表示項目の最小値は最大値より小さい値を入力してください"""
        from iot_app.common.exceptions import ValidationError
        params = self._valid_params(left_min_value='10', left_max_value='10')

        with pytest.raises(ValidationError, match='左表示項目の最小値は最大値より小さい値を入力してください'):
            validate_gadget_registration(params)

    def test_left_min_greater_than_max_raises_validation_error(self):
        """1.3.6: 左の最小値 > 最大値の場合 ValidationError が発生する"""
        from iot_app.common.exceptions import ValidationError
        params = self._valid_params(left_min_value='20', left_max_value='10')

        with pytest.raises(ValidationError, match='左表示項目の最小値は最大値より小さい値を入力してください'):
            validate_gadget_registration(params)

    def test_right_min_equal_to_max_raises_validation_error(self):
        """1.3.5: 右の最小値 = 最大値の場合 ValidationError が発生する
        エラーメッセージ: 右表示項目の最小値は最大値より小さい値を入力してください"""
        from iot_app.common.exceptions import ValidationError
        params = self._valid_params(right_min_value='10', right_max_value='10')

        with pytest.raises(ValidationError, match='右表示項目の最小値は最大値より小さい値を入力してください'):
            validate_gadget_registration(params)

    def test_right_min_greater_than_max_raises_validation_error(self):
        """1.3.6: 右の最小値 > 最大値の場合 ValidationError が発生する
        エラーメッセージ: 右表示項目の最小値は最大値より小さい値を入力してください"""
        from iot_app.common.exceptions import ValidationError
        params = self._valid_params(right_min_value='20', right_max_value='10')

        with pytest.raises(ValidationError, match='右表示項目の最小値は最大値より小さい値を入力してください'):
            validate_gadget_registration(params)

    def test_left_min_less_than_max_passes(self):
        """1.3.4: 左の最小値 < 最大値の場合は正常終了する"""
        params = self._valid_params(left_min_value='0', left_max_value='100')
        validate_gadget_registration(params)

    def test_min_max_none_passes(self):
        """2.1.2: 最小値・最大値がどちらも None の場合は正常終了する（任意項目）"""
        params = self._valid_params(
            left_min_value=None, left_max_value=None,
            right_min_value=None, right_max_value=None,
        )
        validate_gadget_registration(params)

    # ---- 部品サイズ 不整値チェック (1.1.6) ----

    def test_gadget_size_2x2_passes(self):
        """1.6.1: gadget_size が '2x2' の場合は正常終了する"""
        params = self._valid_params(gadget_size='2x2')
        validate_gadget_registration(params)

    def test_gadget_size_2x4_passes(self):
        """1.6.1: gadget_size が '2x4' の場合は正常終了する"""
        params = self._valid_params(gadget_size='2x4')
        validate_gadget_registration(params)

    def test_gadget_size_invalid_raises_validation_error(self):
        """1.6.2: gadget_size が許容値以外の場合 ValidationError が発生する
        エラーメッセージ: 部品サイズが不正です"""
        from iot_app.common.exceptions import ValidationError
        params = self._valid_params(gadget_size='3x3')

        with pytest.raises(ValidationError, match='部品サイズが不正です'):
            validate_gadget_registration(params)

    def test_gadget_size_none_raises_validation_error(self):
        """1.1.2: gadget_size が None の場合 ValidationError が発生する
        エラーメッセージ: 部品サイズを選択してください"""
        from iot_app.common.exceptions import ValidationError
        params = self._valid_params(gadget_size=None)

        with pytest.raises(ValidationError, match='部品サイズを選択してください'):
            validate_gadget_registration(params)

    # ---- 複合正常系 ----

    def test_all_valid_params_passes(self):
        """2.1.1: 全項目が正常値の場合、ValidationError が発生しない（複合正常系）
        仕様: ui-specification.md > バリデーション（ガジェット登録画面）"""
        params = {
            'title':           '時系列テストガジェット',
            'device_mode':     'fixed',
            'device_id':       12345,
            'group_id':        1,
            'left_item_id':    1,
            'right_item_id':   2,
            'left_min_value':  '0',
            'left_max_value':  '100',
            'right_min_value': '10',
            'right_max_value': '200',
            'gadget_size':     '2x2',
        }
        # ValidationError が発生しないことを確認
        validate_gadget_registration(params)


# ============================================================
# TestRegisterGadget
# 観点: 3.2.1 登録処理呼び出し、3.2.2 登録結果
# ============================================================

@pytest.mark.unit
class TestRegisterGadget:
    """ガジェット登録処理のRepository呼び出し・結果
    観点: 3.2.1 登録処理呼び出し、3.2.2 登録結果
    仕様: workflow-specification.md > ガジェット登録 > 処理詳細③
    """

    def _valid_params(self, **overrides):
        """有効なデフォルトパラメータを返すヘルパー
        注: TestValidateGadgetRegistration._valid_params とデフォルトが異なる点
            - device_mode: 'fixed'（こちら）vs 'variable'（TestValidateGadgetRegistration）
            - min/max: 値あり（こちら）vs None（TestValidateGadgetRegistration）
        """
        params = {
            'title':           '時系列テストガジェット',
            'device_mode':     'fixed',
            'device_id':       12345,
            'group_id':        1,
            'left_item_id':    1,
            'right_item_id':   2,
            'left_min_value':  '0',
            'left_max_value':  '100',
            'right_min_value': '10',
            'right_max_value': '200',
            'gadget_size':     '2x2',
        }
        params.update(overrides)
        return params

    # ---- 3.2.1.1: 正常値がRepositoryに渡される ----

    def test_valid_params_passed_to_repository(self):
        """3.2.1.1: 正常な入力値で呼び出した場合、登録内容がRepositoryに渡される
        仕様: workflow-specification.md > ガジェット登録③ db.session.add(gadget)"""
        from iot_app.services.customer_dashboard.timeline_service import register_gadget

        with patch('iot_app.services.customer_dashboard.timeline_service.db') as mock_db:
            mock_gadget = MagicMock()
            mock_gadget.gadget_id = 1
            mock_db.session.add = MagicMock()
            mock_db.session.commit = MagicMock()

            with patch(
                'iot_app.services.customer_dashboard.timeline_service.DashboardGadgetMaster',
                return_value=mock_gadget,
            ):
                register_gadget(self._valid_params())

            # db.session.add が呼ばれたことを確認
            mock_db.session.add.assert_called_once_with(mock_gadget)
            mock_db.session.commit.assert_called_once()

    # ---- 3.2.1.2: None を含む値がそのままRepositoryに渡される ----

    def test_none_values_passed_to_repository_as_is(self):
        """3.2.1.2: 入力値に None を含む場合、None を含んだままRepositoryに渡される
        仕様: data_source_config の device_id は可変モード時 null"""
        from iot_app.services.customer_dashboard.timeline_service import register_gadget

        params = self._valid_params(
            device_mode='variable',
            device_id=None,
            left_min_value=None,
            left_max_value=None,
            right_min_value=None,
            right_max_value=None,
        )

        with patch('iot_app.services.customer_dashboard.timeline_service.db') as mock_db:
            mock_gadget = MagicMock()
            mock_gadget.gadget_id = 2
            mock_db.session.add = MagicMock()
            mock_db.session.commit = MagicMock()

            with patch(
                'iot_app.services.customer_dashboard.timeline_service.DashboardGadgetMaster',
                return_value=mock_gadget,
            ):
                register_gadget(params)

            # None を含んだままセッションに追加されていることを確認
            mock_db.session.add.assert_called_once_with(mock_gadget)

    # ---- 3.2.1.3: バリデーションエラー時はRepositoryを呼び出さない ----

    def test_repository_not_called_on_validation_error(self):
        """3.2.1.3: バリデーションエラーが発生した場合、Repositoryは呼び出されない
        仕様: workflow-specification.md > ガジェット登録② バリデーションエラー時は登録しない"""
        from iot_app.common.exceptions import ValidationError
        from iot_app.services.customer_dashboard.timeline_service import register_gadget

        params = self._valid_params(title=None)  # タイトルNoneでバリデーションエラー

        with patch('iot_app.services.customer_dashboard.timeline_service.db') as mock_db:
            with pytest.raises(ValidationError):
                register_gadget(params)

            # db.session.add が呼ばれていないことを確認
            mock_db.session.add.assert_not_called()
            mock_db.session.commit.assert_not_called()

    # ---- 3.2.2.1: 登録成功時にIDが返却される ----

    def test_register_gadget_returns_gadget_id(self):
        """3.2.2.1: 登録処理成功時、RepositoryからガジェットIDが返却される
        仕様: workflow-specification.md > ガジェット登録③ gadget_id を返却"""
        from iot_app.services.customer_dashboard.timeline_service import register_gadget

        with patch('iot_app.services.customer_dashboard.timeline_service.db') as mock_db:
            mock_gadget = MagicMock()
            mock_gadget.gadget_id = 42
            mock_db.session.add = MagicMock()
            mock_db.session.commit = MagicMock()

            with patch(
                'iot_app.services.customer_dashboard.timeline_service.DashboardGadgetMaster',
                return_value=mock_gadget,
            ):
                result = register_gadget(self._valid_params())

            # 登録されたガジェットのIDが返却されることを確認
            assert result == 42

    # ---- 2.3 副作用チェック ----

    def test_rollback_called_on_exception(self):
        """2.3.1 / 2.3.2: commit()で IntegrityError が発生した場合、rollback()が呼び出され
        例外が上位に伝播する
        仕様: workflow-specification.md > ガジェット登録③ except IntegrityError: rollback()"""
        from sqlalchemy.exc import IntegrityError
        from iot_app.services.customer_dashboard.timeline_service import register_gadget

        with patch('iot_app.services.customer_dashboard.timeline_service.db') as mock_db:
            mock_gadget = MagicMock()
            mock_db.session.add = MagicMock()
            mock_db.session.commit.side_effect = IntegrityError(
                statement=None, params=None, orig=Exception('duplicate entry')
            )
            mock_db.session.rollback = MagicMock()

            with patch(
                'iot_app.services.customer_dashboard.timeline_service.DashboardGadgetMaster',
                return_value=mock_gadget,
            ):
                # IntegrityError が上位に伝播することを確認
                with pytest.raises(IntegrityError):
                    register_gadget(self._valid_params())

            # rollback() が呼び出されたことを確認（2.3.2）
            mock_db.session.rollback.assert_called_once()


# ============================================================
# TestFetchTimelineDataExistenceCheck
# 観点: 2.2 対象データ存在チェック
# ============================================================

@pytest.mark.unit
class TestFetchTimelineDataExistenceCheck:
    """ガジェットデータ取得時の対象データ存在チェック
    観点: 2.2 対象データ存在チェック
    仕様: workflow-specification.md > ガジェットデータ取得 > 処理詳細②
    """

    # ---- 2.2.1: 対象IDが存在する場合は正常処理 ----

    def test_existing_gadget_uuid_processes_normally(self):
        """2.2.1: 対象ガジェットUUIDが存在する場合、正常にデータ取得処理が実行される"""
        from iot_app.services.customer_dashboard.timeline_service import fetch_timeline_data

        mock_gadget = MagicMock()
        mock_gadget.delete_flag = False
        mock_gadget.gadget_id = 1
        mock_gadget.data_source_config = '{"device_id": 1}'

        with patch(
            'iot_app.services.customer_dashboard.timeline_service.DashboardGadgetMaster'
        ) as mock_model:
            mock_model.query.filter_by.return_value.first.return_value = mock_gadget
            with patch(
                'iot_app.services.customer_dashboard.timeline_service.execute_silver_query',
                return_value=[],
            ):
                # NotFoundError が発生しないことを確認
                fetch_timeline_data(
                    gadget_uuid='aaaaaaaa-0000-0000-0000-000000000001',
                    start_datetime=datetime(2026, 2, 17, 0, 0, 0),
                    end_datetime=datetime(2026, 2, 17, 1, 0, 0),
                )

    # ---- 2.2.2: 対象IDが存在しない場合は NotFoundError ----

    def test_nonexistent_gadget_uuid_raises_not_found_error(self):
        """2.2.2: 対象ガジェットUUIDが存在しない場合、NotFoundError がスローされる"""
        from iot_app.common.exceptions import NotFoundError
        from iot_app.services.customer_dashboard.timeline_service import fetch_timeline_data

        with patch(
            'iot_app.services.customer_dashboard.timeline_service.DashboardGadgetMaster'
        ) as mock_model:
            mock_model.query.filter_by.return_value.first.return_value = None

            with pytest.raises(NotFoundError):
                fetch_timeline_data(
                    gadget_uuid='ffffffff-0000-0000-0000-000000000000',
                    start_datetime=datetime(2026, 2, 17, 0, 0, 0),
                    end_datetime=datetime(2026, 2, 17, 1, 0, 0),
                )

    # ---- 2.2.3: 論理削除済みデータは NotFoundError ----

    def test_logically_deleted_gadget_raises_not_found_error(self):
        """2.2.3: delete_flag=True の論理削除済みガジェットは NotFoundError がスローされる
        仕様: dashboard_gadget_master.delete_flag = TRUE のレコードは存在しないとみなす"""
        from iot_app.common.exceptions import NotFoundError
        from iot_app.services.customer_dashboard.timeline_service import fetch_timeline_data

        mock_gadget = MagicMock()
        mock_gadget.delete_flag = True

        with patch(
            'iot_app.services.customer_dashboard.timeline_service.DashboardGadgetMaster'
        ) as mock_model:
            mock_model.query.filter_by.return_value.first.return_value = mock_gadget

            with pytest.raises(NotFoundError):
                fetch_timeline_data(
                    gadget_uuid='aaaaaaaa-0000-0000-0000-000000000001',
                    start_datetime=datetime(2026, 2, 17, 0, 0, 0),
                    end_datetime=datetime(2026, 2, 17, 1, 0, 0),
                )

    # ---- 2.2.4: デバイス可変モード時のフォールバック ----

    def test_variable_mode_falls_back_to_user_setting_device_id(self):
        """2.2.4: デバイス可変モード（device_id=null）時、dashboard_user_setting.device_id を使用する
        仕様: workflow-specification.md > ガジェットデータ取得② デバイスID決定
              data_source_config.device_id が null → ユーザー設定から device_id を取得"""
        from iot_app.services.customer_dashboard.timeline_service import fetch_timeline_data

        mock_gadget = MagicMock()
        mock_gadget.delete_flag = False
        mock_gadget.data_source_config = '{"device_id": null}'

        mock_user_setting = MagicMock()
        mock_user_setting.device_id = 99999

        with patch(
            'iot_app.services.customer_dashboard.timeline_service.DashboardGadgetMaster'
        ) as mock_model:
            mock_model.query.filter_by.return_value.first.return_value = mock_gadget

            with patch(
                'iot_app.services.customer_dashboard.timeline_service.get_dashboard_user_setting',
                return_value=mock_user_setting,
            ):
                with patch(
                    'iot_app.services.customer_dashboard.timeline_service.execute_silver_query',
                    return_value=[],
                ) as mock_query:
                    fetch_timeline_data(
                        gadget_uuid='aaaaaaaa-0000-0000-0000-000000000001',
                        start_datetime=datetime(2026, 2, 17, 0, 0, 0),
                        end_datetime=datetime(2026, 2, 17, 1, 0, 0),
                    )

                # ユーザー設定のdevice_id（99999）でSilverクエリが呼ばれることを確認
                assert mock_query.call_args is not None
                call_args_flat = (
                    list(mock_query.call_args.args)
                    + list(mock_query.call_args.kwargs.values())
                )
                assert 99999 in call_args_flat, (
                    f'device_id=99999 がクエリ引数に含まれていない: {mock_query.call_args}'
                )


# ============================================================
# TestGenerateTimelineCsv
# 観点: 3.5.1 CSV生成ロジック、3.5.2 エスケープ処理
# ============================================================

@pytest.mark.unit
class TestGenerateTimelineCsv:
    """時系列データ CSV 生成処理
    観点: 3.5.1 CSV生成ロジック、3.5.2 エスケープ処理
    仕様: ui-specification.md > CSVファイル仕様・CSV列構成
    """

    def _parse_csv(self, csv_string):
        """CSV文字列をリストに変換するヘルパー（先頭BOMを除去）"""
        return list(csv.reader(io.StringIO(csv_string.lstrip('\ufeff'))))

    # ---- ヘッダー行 (3.5.1.1) ----

    def test_header_row_contains_defined_columns(self):
        """3.5.1.1: CSV の 1 行目が定義されたヘッダー行で出力される
        仕様: 受信日時, デバイス名, {左表示項目ラベル}, {右表示項目ラベル}"""
        # Arrange
        rows = []

        # Act
        result = generate_timeline_csv(
            rows,
            left_column_name='external_temp',
            right_column_name='compressor_freezer_1',
            left_label='外気温度',
            right_label='第1冷凍 圧縮機',
        )
        parsed = self._parse_csv(result)

        # Assert
        assert parsed[0] == ['受信日時', 'デバイス名', '外気温度', '第1冷凍 圧縮機']

    # ---- データ行出力 (3.5.1.2) ----

    def test_data_rows_all_output(self):
        """3.5.1.2: 複数件のデータがすべて CSV 行として出力される"""
        # Arrange
        rows = [
            {
                'event_timestamp':      datetime(2026, 2, 17, 0, 0, 0),
                'device_name':          'デバイスA',
                'external_temp':        25.5,
                'compressor_freezer_1': 2500.0,
            },
            {
                'event_timestamp':      datetime(2026, 2, 17, 0, 1, 0),
                'device_name':          'デバイスA',
                'external_temp':        26.0,
                'compressor_freezer_1': 2480.0,
            },
        ]

        # Act
        result = generate_timeline_csv(
            rows,
            left_column_name='external_temp',
            right_column_name='compressor_freezer_1',
            left_label='外気温度',
            right_label='第1冷凍 圧縮機',
        )
        parsed = self._parse_csv(result)

        # Assert（ヘッダー行 + 2データ行）
        assert len(parsed) == 3
        assert parsed[1] == ['2026/02/17 00:00:00', 'デバイスA', '25.5', '2500.0']
        assert parsed[2] == ['2026/02/17 00:01:00', 'デバイスA', '26.0', '2480.0']

    # ---- 0件出力 (3.5.1.3) ----

    def test_empty_rows_outputs_header_only(self):
        """3.5.1.3: データが 0 件の場合、ヘッダー行のみ出力される"""
        # Arrange
        rows = []

        # Act
        result = generate_timeline_csv(
            rows,
            left_column_name='external_temp',
            right_column_name='compressor_freezer_1',
            left_label='外気温度',
            right_label='第1冷凍 圧縮機',
        )
        parsed = self._parse_csv(result)

        # Assert
        assert len(parsed) == 1
        assert parsed[0][0] == '受信日時'

    # ---- 列順序 (3.5.1.4) ----

    def test_column_order(self):
        """3.5.1.4: 列が 受信日時 → デバイス名 → 左表示項目 → 右表示項目 の順で出力される"""
        # Arrange
        rows = [
            {
                'event_timestamp':      datetime(2026, 2, 17, 0, 0, 0),
                'device_name':          'デバイスA',
                'external_temp':        10.0,
                'fan_motor_1':          1200.0,
            }
        ]

        # Act
        result = generate_timeline_csv(
            rows,
            left_column_name='external_temp',
            right_column_name='fan_motor_1',
            left_label='外気温度',
            right_label='第1ファンモータ回転数',
        )
        parsed = self._parse_csv(result)

        # Assert（ヘッダー列順序確認）
        header = parsed[0]
        assert header.index('受信日時')             < header.index('デバイス名')
        assert header.index('デバイス名')           < header.index('外気温度')
        assert header.index('外気温度')             < header.index('第1ファンモータ回転数')

    # ---- エスケープ処理 (3.5.2) ----

    def test_comma_in_device_name_is_quoted(self):
        """3.5.2.1: デバイス名にカンマを含む場合、ダブルクォートで囲まれる"""
        # Arrange
        rows = [
            {
                'event_timestamp':      datetime(2026, 2, 17, 0, 0, 0),
                'device_name':          'デバイス,A',
                'external_temp':        25.5,
                'compressor_freezer_1': 2500.0,
            }
        ]

        # Act
        result = generate_timeline_csv(
            rows,
            left_column_name='external_temp',
            right_column_name='compressor_freezer_1',
            left_label='外気温度',
            right_label='第1冷凍 圧縮機',
        )
        parsed = self._parse_csv(result)

        # Assert（csv.reader でカンマが正しく解釈されている）
        assert parsed[1][1] == 'デバイス,A'

    def test_newline_in_device_name_is_quoted(self):
        """3.5.2.2: デバイス名に改行を含む場合、ダブルクォートで囲まれる"""
        # Arrange
        rows = [
            {
                'event_timestamp':      datetime(2026, 2, 17, 0, 0, 0),
                'device_name':          'デバイス\nA',
                'external_temp':        25.5,
                'compressor_freezer_1': 2500.0,
            }
        ]

        # Act
        result = generate_timeline_csv(
            rows,
            left_column_name='external_temp',
            right_column_name='compressor_freezer_1',
            left_label='外気温度',
            right_label='第1冷凍 圧縮機',
        )
        parsed = self._parse_csv(result)

        # Assert（csv.reader で改行が正しく解釈されている）
        assert 'デバイス\nA' in parsed[1][1]

    def test_double_quote_in_device_name_is_escaped(self):
        """3.5.2.3: デバイス名にダブルクォートを含む場合、\"\" でエスケープされる"""
        # Arrange
        rows = [
            {
                'event_timestamp':      datetime(2026, 2, 17, 0, 0, 0),
                'device_name':          'デバイス"A"',
                'external_temp':        25.5,
                'compressor_freezer_1': 2500.0,
            }
        ]

        # Act
        result = generate_timeline_csv(
            rows,
            left_column_name='external_temp',
            right_column_name='compressor_freezer_1',
            left_label='外気温度',
            right_label='第1冷凍 圧縮機',
        )
        parsed = self._parse_csv(result)

        # Assert（csv.reader でダブルクォートが正しく解釈されている）
        assert parsed[1][1] == 'デバイス"A"'

    def test_normal_data_output_as_is(self):
        """3.5.2.4: 特殊文字を含まない通常データはそのまま出力される"""
        # Arrange
        rows = [
            {
                'event_timestamp':      datetime(2026, 2, 17, 0, 0, 0),
                'device_name':          'デバイスA',
                'external_temp':        25.5,
                'compressor_freezer_1': 2500.0,
            }
        ]

        # Act
        result = generate_timeline_csv(
            rows,
            left_column_name='external_temp',
            right_column_name='compressor_freezer_1',
            left_label='外気温度',
            right_label='第1冷凍 圧縮機',
        )
        parsed = self._parse_csv(result)

        # Assert
        assert parsed[1][1] == 'デバイスA'

    # ---- タイムスタンプ形式 (3.5.1.5) ----

    def test_csv_timestamp_format_is_slash_separated(self):
        """3.5.1.5: CSV の受信日時カラムが YYYY/MM/DD HH:mm:ss 形式で出力される
        仕様: workflow-specification.md > CSVエクスポート④ event_timestamp.strftime('%Y/%m/%d %H:%M:%S')"""
        # Arrange
        rows = [
            {
                'event_timestamp':      datetime(2026, 2, 17, 8, 5, 3),
                'device_name':          'デバイスA',
                'external_temp':        25.5,
                'compressor_freezer_1': 2500.0,
            }
        ]

        # Act
        result = generate_timeline_csv(
            rows,
            left_column_name='external_temp',
            right_column_name='compressor_freezer_1',
            left_label='外気温度',
            right_label='第1冷凍 圧縮機',
        )
        parsed = self._parse_csv(result.lstrip('\ufeff'))

        # Assert: スラッシュ区切り・ゼロ埋めの形式であることを確認
        assert parsed[1][0] == '2026/02/17 08:05:03'

    # ---- BOM・文字コード (3.5.3) ----

    def test_csv_has_utf8_bom(self):
        """3.5.3.1: CSV生成結果の先頭に UTF-8 BOM（0xEF 0xBB 0xBF）が付与される"""
        # Arrange
        rows = []

        # Act
        result = generate_timeline_csv(
            rows,
            left_column_name='external_temp',
            right_column_name='compressor_freezer_1',
            left_label='外気温度',
            right_label='第1冷凍 圧縮機',
        )

        # Assert
        assert result.startswith('\ufeff')

    def test_csv_japanese_characters_output_correctly(self):
        """3.5.3.2: 日本語データを含む CSV が文字化けなく正しく出力される"""
        # Arrange
        rows = [
            {
                'event_timestamp':      datetime(2026, 2, 17, 0, 0, 0),
                'device_name':          '冷凍倉庫センサー１号機',
                'external_temp':        25.5,
                'compressor_freezer_1': 2500.0,
            }
        ]

        # Act
        result = generate_timeline_csv(
            rows,
            left_column_name='external_temp',
            right_column_name='compressor_freezer_1',
            left_label='外気温度',
            right_label='第1冷凍 圧縮機',
        )
        parsed = self._parse_csv(result.lstrip('\ufeff'))

        # Assert
        assert parsed[0] == ['受信日時', 'デバイス名', '外気温度', '第1冷凍 圧縮機']
        assert parsed[1][1] == '冷凍倉庫センサー１号機'


# ============================================================
# TestTimelineServiceLogging
# 観点: 1.4.1 ログレベル、1.4.3 機密情報の非出力、1.3.1 例外伝播
# ============================================================

@pytest.mark.unit
class TestTimelineServiceLogging:
    """時系列サービスのログ出力・例外伝播
    観点: 1.4.1 ログレベル、1.4.3 機密情報の非出力、1.3.1 例外伝播
    仕様: logging-specification.md > 6.6 エラーハンドリング
    """

    def _mock_gadget_lookup(self):
        """ガジェット取得のモックを返すヘルパー"""
        mock_gadget = MagicMock()
        mock_gadget.delete_flag = False
        mock_gadget.data_source_config = '{"device_id": 1}'
        return mock_gadget

    def test_fetch_timeline_data_raises_on_query_failure(self):
        """1.3.1: Unity Catalog クエリが失敗した場合、例外が上位に伝播する"""
        from iot_app.services.customer_dashboard.timeline_service import fetch_timeline_data

        with patch(
            'iot_app.services.customer_dashboard.timeline_service.DashboardGadgetMaster'
        ) as mock_model:
            mock_model.query.filter_by.return_value.first.return_value = self._mock_gadget_lookup()
            with patch(
                'iot_app.services.customer_dashboard.timeline_service.execute_silver_query',
                side_effect=Exception('Databricks接続エラー'),
            ):
                with pytest.raises(Exception, match='Databricks接続エラー'):
                    fetch_timeline_data(
                        gadget_uuid='aaaaaaaa-0000-0000-0000-000000000001',
                        start_datetime=datetime(2026, 2, 17, 0, 0, 0),
                        end_datetime=datetime(2026, 2, 17, 1, 0, 0),
                    )

    def test_fetch_timeline_data_logs_error_on_failure(self, caplog):
        """1.4.1.1: Unity Catalog クエリ失敗時に ERROR レベルのログが出力される
        仕様: logging-specification.md > 6.1 タイミング一覧（500系→ERROR）"""
        from iot_app.services.customer_dashboard.timeline_service import fetch_timeline_data

        with patch(
            'iot_app.services.customer_dashboard.timeline_service.DashboardGadgetMaster'
        ) as mock_model:
            mock_model.query.filter_by.return_value.first.return_value = self._mock_gadget_lookup()
            with patch(
                'iot_app.services.customer_dashboard.timeline_service.execute_silver_query',
                side_effect=Exception('Databricks接続エラー'),
            ):
                with caplog.at_level(logging.ERROR):
                    with pytest.raises(Exception):
                        fetch_timeline_data(
                            gadget_uuid='aaaaaaaa-0000-0000-0000-000000000001',
                            start_datetime=datetime(2026, 2, 17, 0, 0, 0),
                            end_datetime=datetime(2026, 2, 17, 1, 0, 0),
                        )

        assert any(r.levelno == logging.ERROR for r in caplog.records)

    def test_fetch_timeline_data_log_does_not_contain_sensor_values(self, caplog):
        """1.4.3: エラーログにセンサーデータの具体値が含まれない
        仕様: logging-specification.md > 5.3 出力禁止項目
              workflow-specification.md > ログ出力ルール（センサーデータの具体値は出力しない）"""
        from iot_app.services.customer_dashboard.timeline_service import fetch_timeline_data

        secret_value = 'SECRET_SENSOR_VALUE_9999'
        with patch(
            'iot_app.services.customer_dashboard.timeline_service.DashboardGadgetMaster'
        ) as mock_model:
            mock_model.query.filter_by.return_value.first.return_value = self._mock_gadget_lookup()
            with patch(
                'iot_app.services.customer_dashboard.timeline_service.execute_silver_query',
                side_effect=Exception(f'error: {secret_value}'),
            ):
                with caplog.at_level(logging.ERROR):
                    with pytest.raises(Exception):
                        fetch_timeline_data(
                            gadget_uuid='aaaaaaaa-0000-0000-0000-000000000001',
                            start_datetime=datetime(2026, 2, 17, 0, 0, 0),
                            end_datetime=datetime(2026, 2, 17, 1, 0, 0),
                        )

        log_text = ' '.join(r.getMessage() for r in caplog.records)
        # ログメッセージ本文にセンサーの具体値が埋め込まれていないことを確認
        # TODO: 設計書に「エラーメッセージにセンサー値を含めない」の明示はないため要確認
        assert secret_value not in log_text
