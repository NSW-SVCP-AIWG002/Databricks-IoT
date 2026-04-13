"""
顧客作成ダッシュボード 表ガジェット - 単体テスト

対象:
  - src/iot_app/forms/customer_dashboard/grid.py ※未実装
      GridGadgetForm
  - src/iot_app/services/customer_dashboard/grid.py ※未実装
      validate_chart_params(start_datetime_str, end_datetime_str)
      format_grid_data(rows, columns)
      calculate_page_offset(page, per_page=25)
      fetch_grid_data(device_id, start_datetime, end_datetime, limit=1000, offset=0)
      get_column_definition()
      register_grid_gadget(params, current_user_id)
      get_grid_create_context(dashboard_id)
      generate_grid_csv(grid_data, columns)

参照仕様書:
  - docs/03-features/flask-app/customer-dashboard/grid/ui-specification.md
  - docs/03-features/flask-app/customer-dashboard/grid/workflow-specification.md
"""

import pytest
from datetime import datetime
from unittest.mock import MagicMock, patch

_GRID_FORM_MODULE = 'iot_app.forms.customer_dashboard.grid'
_GRID_SERVICE_MODULE = 'iot_app.services.customer_dashboard.grid'


# ===========================================================================
# Section 1: フォームバリデーション - タイトル (GridGadgetForm.gadget_name)
# UI仕様書 § バリデーション（登録画面）
#   タイトル: 必須、最大20文字
# ===========================================================================

@pytest.mark.unit
class TestGridGadgetFormTitle:
    """表ガジェット登録フォーム - タイトルバリデーション

    観点: 1.1.1（必須チェック）, 1.1.2（最大文字列長チェック）
    UI仕様書 § バリデーション（ガジェット登録画面）
      - タイトル: 必須 → エラー「タイトルを入力してください」
      - タイトル: 最大20文字 → エラー「タイトルは20文字以内で入力してください」
    """

    def test_valid_when_title_provided(self, app):
        """1.1.1.3 入力あり: タイトルが入力されている場合はバリデーション通過"""
        # Arrange
        from iot_app.forms.customer_dashboard.grid import GridGadgetForm
        # Act
        with app.test_request_context():
            form = GridGadgetForm(data={'gadget_name': '表ガジェット', 'group_id': 1, 'gadget_size': '0'})
            result = form.validate()
        # Assert
        assert result is True

    def test_invalid_when_title_empty(self, app):
        """1.1.1.1 空文字: タイトルが空文字の場合はバリデーションエラー"""
        # Arrange
        from iot_app.forms.customer_dashboard.grid import GridGadgetForm
        # Act
        with app.test_request_context():
            form = GridGadgetForm(data={'gadget_name': ''})
            result = form.validate()
        # Assert
        assert result is False
        assert 'gadget_name' in form.errors

    def test_invalid_when_title_none(self, app):
        """1.1.1.2 None: タイトルが None の場合はバリデーションエラー"""
        # Arrange
        from iot_app.forms.customer_dashboard.grid import GridGadgetForm
        # Act
        with app.test_request_context():
            form = GridGadgetForm(data={'gadget_name': None})
            result = form.validate()
        # Assert
        assert result is False
        assert 'gadget_name' in form.errors

    def test_invalid_when_title_whitespace_only(self, app):
        """1.1.1.4 空白のみ: DataRequired が strip するためバリデーションエラー"""
        # Arrange
        from iot_app.forms.customer_dashboard.grid import GridGadgetForm
        # Act
        with app.test_request_context():
            form = GridGadgetForm(data={'gadget_name': '   '})
            result = form.validate()
        # Assert
        assert result is False
        assert 'gadget_name' in form.errors

    def test_valid_when_title_is_19_chars(self, app):
        """1.2.1 最大長-1（19文字）: バリデーション通過"""
        # Arrange
        from iot_app.forms.customer_dashboard.grid import GridGadgetForm
        # Act
        with app.test_request_context():
            form = GridGadgetForm(data={'gadget_name': 'a' * 19, 'group_id': 1, 'gadget_size': '0'})
            result = form.validate()
        # Assert
        assert result is True

    def test_valid_when_title_is_20_chars(self, app):
        """1.2.2 最大長（20文字）: バリデーション通過"""
        # Arrange
        from iot_app.forms.customer_dashboard.grid import GridGadgetForm
        # Act
        with app.test_request_context():
            form = GridGadgetForm(data={'gadget_name': 'a' * 20, 'group_id': 1, 'gadget_size': '0'})
            result = form.validate()
        # Assert
        assert result is True

    def test_invalid_when_title_is_21_chars(self, app):
        """1.2.3 最大長+1（21文字）: バリデーションエラー「タイトルは20文字以内で入力してください」"""
        # Arrange
        from iot_app.forms.customer_dashboard.grid import GridGadgetForm
        # Act
        with app.test_request_context():
            form = GridGadgetForm(data={'gadget_name': 'a' * 21})
            result = form.validate()
        # Assert
        assert result is False
        assert 'gadget_name' in form.errors
        assert 'タイトルは20文字以内で入力してください' in form.errors['gadget_name']

    def test_error_message_when_title_required(self, app):
        """1.1.1: 必須エラーメッセージ確認「タイトルを入力してください」"""
        # Arrange
        from iot_app.forms.customer_dashboard.grid import GridGadgetForm
        # Act
        with app.test_request_context():
            form = GridGadgetForm(data={'gadget_name': ''})
            form.validate()
        # Assert
        assert 'タイトルを入力してください' in form.errors.get('gadget_name', [])


# ===========================================================================
# Section 2: フォームバリデーション - グループ選択 (GridGadgetForm.group_id)
# UI仕様書 § バリデーション（登録画面）
#   グループ選択: 必須
# ===========================================================================

@pytest.mark.unit
class TestGridGadgetFormGroup:
    """表ガジェット登録フォーム - グループ選択バリデーション

    観点: 1.1.1（必須チェック）
    UI仕様書 § バリデーション（ガジェット登録画面）
      - グループ選択: 必須 → エラー「グループを選択してください」
    """

    def test_valid_when_group_id_provided(self, app):
        """1.1.1.3 入力あり: group_id が指定されている場合はバリデーション通過"""
        # Arrange
        from iot_app.forms.customer_dashboard.grid import GridGadgetForm
        # Act
        with app.test_request_context():
            form = GridGadgetForm(data={'gadget_name': 'テスト', 'group_id': 1, 'gadget_size': '0'})
            result = form.validate()
        # Assert
        assert result is True

    def test_invalid_when_group_id_empty(self, app):
        """1.1.1.1 空文字: group_id が未選択の場合はバリデーションエラー"""
        # Arrange
        from iot_app.forms.customer_dashboard.grid import GridGadgetForm
        # Act
        with app.test_request_context():
            form = GridGadgetForm(data={'gadget_name': 'テスト', 'group_id': ''})
            result = form.validate()
        # Assert
        assert result is False
        assert 'group_id' in form.errors

    def test_invalid_when_group_id_none(self, app):
        """1.1.1.2 None: group_id が None の場合はバリデーションエラー"""
        # Arrange
        from iot_app.forms.customer_dashboard.grid import GridGadgetForm
        # Act
        with app.test_request_context():
            form = GridGadgetForm(data={'gadget_name': 'テスト', 'group_id': None})
            result = form.validate()
        # Assert
        assert result is False
        assert 'group_id' in form.errors

    def test_error_message_when_group_required(self, app):
        """1.1.1: グループ必須エラーメッセージ確認「グループを選択してください」"""
        # Arrange
        from iot_app.forms.customer_dashboard.grid import GridGadgetForm
        # Act
        with app.test_request_context():
            form = GridGadgetForm(data={'gadget_name': 'テスト', 'group_id': None})
            form.validate()
        # Assert
        assert 'グループを選択してください' in form.errors.get('group_id', [])


# ===========================================================================
# Section 3: フォームバリデーション - 部品サイズ (GridGadgetForm.gadget_size)
# UI仕様書 § バリデーション（登録画面）
#   部品サイズ: 必須（0=2x2, 1=2x4）
# ===========================================================================

@pytest.mark.unit
class TestGridGadgetFormGadgetSize:
    """表ガジェット登録フォーム - 部品サイズバリデーション

    観点: 1.1.1（必須チェック）, 1.1.6（不整値チェック）
    UI仕様書 § バリデーション（ガジェット登録画面）
      - 部品サイズ: 必須 → エラー「部品サイズを選択してください」
      - 部品サイズ: 0（2x2）または 1（2x4）のみ有効
    """

    def test_valid_when_gadget_size_2x2(self, app):
        """1.6.1 許容値（0 = 2x2）: バリデーション通過"""
        # Arrange
        from iot_app.forms.customer_dashboard.grid import GridGadgetForm
        # Act
        with app.test_request_context():
            form = GridGadgetForm(data={'gadget_name': 'テスト', 'group_id': 1, 'gadget_size': '0'})
            result = form.validate()
        # Assert
        assert result is True

    def test_valid_when_gadget_size_2x4(self, app):
        """1.6.1 許容値（1 = 2x4）: バリデーション通過"""
        # Arrange
        from iot_app.forms.customer_dashboard.grid import GridGadgetForm
        # Act
        with app.test_request_context():
            form = GridGadgetForm(data={'gadget_name': 'テスト', 'group_id': 1, 'gadget_size': '1'})
            result = form.validate()
        # Assert
        assert result is True

    def test_invalid_when_gadget_size_empty(self, app):
        """1.1.1.1 空文字: gadget_size が未選択の場合はバリデーションエラー"""
        # Arrange
        from iot_app.forms.customer_dashboard.grid import GridGadgetForm
        # Act
        with app.test_request_context():
            form = GridGadgetForm(data={'gadget_name': 'テスト', 'group_id': 1, 'gadget_size': ''})
            result = form.validate()
        # Assert
        assert result is False
        assert 'gadget_size' in form.errors

    def test_invalid_when_gadget_size_undefined_value(self, app):
        """1.6.2 未定義値: 0/1 以外の値はバリデーションエラー"""
        # Arrange
        from iot_app.forms.customer_dashboard.grid import GridGadgetForm
        # Act
        with app.test_request_context():
            form = GridGadgetForm(data={'gadget_name': 'テスト', 'group_id': 1, 'gadget_size': '99'})
            result = form.validate()
        # Assert
        assert result is False
        assert 'gadget_size' in form.errors

    def test_error_message_when_gadget_size_required(self, app):
        """1.1.1: 部品サイズ必須エラーメッセージ確認「部品サイズを選択してください」"""
        # Arrange
        from iot_app.forms.customer_dashboard.grid import GridGadgetForm
        # Act
        with app.test_request_context():
            form = GridGadgetForm(data={'gadget_name': 'テスト', 'group_id': 1, 'gadget_size': ''})
            form.validate()
        # Assert
        assert '部品サイズを選択してください' in form.errors.get('gadget_size', [])


# ===========================================================================
# Section 4: サービス - チャートパラメータバリデーション
# ワークフロー仕様書 § ガジェットデータ取得 > バリデーション
#   開始日時: 日付形式（YYYY/MM/DD HH:mm:ss）
#   終了日時: 日付形式（YYYY/MM/DD HH:mm:ss）
#   開始日時 < 終了日時
# ===========================================================================

@pytest.mark.unit
class TestValidateChartParams:
    """表ガジェット - チャートパラメータバリデーション

    観点: 1.1.4（日付形式チェック）, 1.1.1（必須チェック）
    ワークフロー仕様書 § ガジェットデータ取得 > バリデーション
      - 開始日時: 日付形式チェック（YYYY/MM/DD HH:mm:ss）
      - 終了日時: 日付形式チェック（YYYY/MM/DD HH:mm:ss）
      - 開始日時 < 終了日時: 終了日時は開始日時以降の日時を入力してください
    """

    def test_valid_when_both_datetimes_correct_format(self):
        """1.4.1 正常な形式: 開始・終了日時が正しい形式の場合 True"""
        # Arrange
        from iot_app.services.customer_dashboard.grid import validate_chart_params
        start = '2026/01/01 00:00:00'
        end   = '2026/01/01 23:59:59'
        # Act
        result = validate_chart_params(start, end)
        # Assert
        assert result is True

    def test_invalid_when_start_datetime_empty(self):
        """1.1.1.1 空文字: 開始日時が空文字の場合 False"""
        # Arrange
        from iot_app.services.customer_dashboard.grid import validate_chart_params
        # Act
        result = validate_chart_params('', '2026/01/01 23:59:59')
        # Assert
        assert result is False

    def test_invalid_when_start_datetime_none(self):
        """1.1.1.2 None: 開始日時が None の場合 False"""
        # Arrange
        from iot_app.services.customer_dashboard.grid import validate_chart_params
        # Act
        result = validate_chart_params(None, '2026/01/01 23:59:59')
        # Assert
        assert result is False

    def test_invalid_when_end_datetime_empty(self):
        """1.1.1.1 空文字: 終了日時が空文字の場合 False"""
        # Arrange
        from iot_app.services.customer_dashboard.grid import validate_chart_params
        # Act
        result = validate_chart_params('2026/01/01 00:00:00', '')
        # Assert
        assert result is False

    def test_invalid_when_end_datetime_none(self):
        """1.1.1.2 None: 終了日時が None の場合 False"""
        # Arrange
        from iot_app.services.customer_dashboard.grid import validate_chart_params
        # Act
        result = validate_chart_params('2026/01/01 00:00:00', None)
        # Assert
        assert result is False

    def test_invalid_when_start_datetime_wrong_format(self):
        """1.4.3 異なる区切り文字: YYYY-MM-DD HH:mm:ss 形式は不正"""
        # Arrange
        from iot_app.services.customer_dashboard.grid import validate_chart_params
        # Act
        result = validate_chart_params('2026-01-01 00:00:00', '2026/01/01 23:59:59')
        # Assert
        assert result is False

    def test_invalid_when_end_datetime_wrong_format(self):
        """1.4.3 異なる区切り文字: 終了日時が不正形式の場合 False"""
        # Arrange
        from iot_app.services.customer_dashboard.grid import validate_chart_params
        # Act
        result = validate_chart_params('2026/01/01 00:00:00', '2026-01-01 23:59:59')
        # Assert
        assert result is False

    def test_invalid_when_end_before_start(self):
        """終了日時が開始日時より前の場合 False（終了日時は開始日時以降の日時を入力してください）"""
        # Arrange
        from iot_app.services.customer_dashboard.grid import validate_chart_params
        # Act
        result = validate_chart_params('2026/01/02 00:00:00', '2026/01/01 23:59:59')
        # Assert
        assert result is False

    def test_valid_when_start_equals_end(self):
        """終了日時が開始日時と同じ場合 True（「以降」は ≥ のため同一日時は有効）"""
        # Arrange
        from iot_app.services.customer_dashboard.grid import validate_chart_params
        # Act
        result = validate_chart_params('2026/01/01 00:00:00', '2026/01/01 00:00:00')
        # Assert
        assert result is True

    def test_invalid_when_start_datetime_date_only(self):
        """1.4.4 月が1桁: 時刻なし形式は不正"""
        # Arrange
        from iot_app.services.customer_dashboard.grid import validate_chart_params
        # Act
        result = validate_chart_params('2026/01/01', '2026/01/02 00:00:00')
        # Assert
        assert result is False

    def test_invalid_when_nonexistent_date(self):
        """1.4.5 存在しない日付: 2/30 は不正"""
        # Arrange
        from iot_app.services.customer_dashboard.grid import validate_chart_params
        # Act
        result = validate_chart_params('2026/02/30 00:00:00', '2026/03/01 00:00:00')
        # Assert
        assert result is False

    def test_valid_leap_year_date(self):
        """1.4.6 閏年: 2024/02/29 は有効"""
        # Arrange
        from iot_app.services.customer_dashboard.grid import validate_chart_params
        # Act
        result = validate_chart_params('2024/02/29 00:00:00', '2024/03/01 00:00:00')
        # Assert
        assert result is True

    def test_invalid_non_leap_year_date(self):
        """1.4.7 非閏年: 2023/02/29 は不正"""
        # Arrange
        from iot_app.services.customer_dashboard.grid import validate_chart_params
        # Act
        result = validate_chart_params('2023/02/29 00:00:00', '2023/03/01 00:00:00')
        # Assert
        assert result is False

    #  日時範囲の上限制約（例: 終了日時 - 開始日時 ≤ 24時間）の有無

    def test_valid_when_range_is_exactly_24_hours(self):
        """24時間ちょうどの範囲は有効（境界値）"""
        # Arrange
        from iot_app.services.customer_dashboard.grid import validate_chart_params
        # Act
        result = validate_chart_params('2026/01/01 00:00:00', '2026/01/02 00:00:00')
        # Assert
        assert result is True

    def test_invalid_when_range_exceeds_24_hours(self):
        """24時間超の範囲は不正"""
        # Arrange
        from iot_app.services.customer_dashboard.grid import validate_chart_params
        # Act
        result = validate_chart_params('2026/01/01 00:00:00', '2026/01/02 00:00:01')
        # Assert
        assert result is False


# ===========================================================================
# Section 5: サービス - データ整形
# ワークフロー仕様書 § ガジェットデータ取得 > 処理詳細 > ④ データ整形
#   format_grid_data(rows, columns) → grid_data リストに変換
# ===========================================================================

@pytest.mark.unit
class TestFormatGridData:
    """表ガジェット - データ整形

    観点: 3.1.4（検索結果戻り値ハンドリング）
    ワークフロー仕様書 § ④ データ整形
      - event_timestamp を YYYY/MM/DD HH:MM:SS 形式に変換
      - device_name を含める
      - measurement_item_master の silver_data_column_name に対応する値を含める
    """

    def _make_column(self, column_name, display_name=''):
        """テスト用カラム定義オブジェクトを生成"""
        col = MagicMock()
        col.silver_data_column_name = column_name
        col.display_name = display_name
        return col

    def test_format_returns_list(self):
        """3.1.4.1 正常系: rows が存在する場合、grid_data リストが返却される"""
        # Arrange
        from iot_app.services.customer_dashboard.grid import format_grid_data
        rows = [
            {
                'event_timestamp': datetime(2026, 1, 1, 12, 0, 0),
                'device_name': 'Device-001',
                'external_temp': 25.5,
            }
        ]
        columns = [self._make_column('external_temp', '外気温度')]
        # Act
        result = format_grid_data(rows, columns)
        # Assert
        assert isinstance(result, list)
        assert len(result) == 1

    def test_format_event_timestamp_as_string(self):
        """event_timestamp が YYYY/MM/DD HH:MM:SS 形式の文字列に変換される"""
        # Arrange
        from iot_app.services.customer_dashboard.grid import format_grid_data
        rows = [
            {
                'event_timestamp': datetime(2026, 3, 5, 12, 0, 0),
                'device_name': 'Device-001',
            }
        ]
        columns = []
        # Act
        result = format_grid_data(rows, columns)
        # Assert
        assert result[0]['event_timestamp'] == '2026/03/05 12:00:00'

    def test_format_device_name_included(self):
        """device_name が各行データに含まれる"""
        # Arrange
        from iot_app.services.customer_dashboard.grid import format_grid_data
        rows = [
            {
                'event_timestamp': datetime(2026, 1, 1, 0, 0, 0),
                'device_name': 'テストデバイス',
            }
        ]
        columns = []
        # Act
        result = format_grid_data(rows, columns)
        # Assert
        assert result[0]['device_name'] == 'テストデバイス'

    def test_format_sensor_columns_included(self):
        """measurement_item_master の各カラム値が行データに含まれる"""
        # Arrange
        from iot_app.services.customer_dashboard.grid import format_grid_data
        rows = [
            {
                'event_timestamp': datetime(2026, 1, 1, 0, 0, 0),
                'device_name': 'Device-001',
                'external_temp': 20.0,
                'set_temp_freezer_1': -18.0,
            }
        ]
        columns = [
            self._make_column('external_temp', '外気温度'),
            self._make_column('set_temp_freezer_1', '第1冷凍 設定温度'),
        ]
        # Act
        result = format_grid_data(rows, columns)
        # Assert
        assert result[0]['external_temp'] == 20.0
        assert result[0]['set_temp_freezer_1'] == -18.0

    def test_format_returns_empty_list_when_no_rows(self):
        """3.1.4.2 空結果: rows が空の場合、空リストが返却される"""
        # Arrange
        from iot_app.services.customer_dashboard.grid import format_grid_data
        rows = []
        columns = [self._make_column('external_temp')]
        # Act
        result = format_grid_data(rows, columns)
        # Assert
        assert result == []

    def test_format_multiple_rows(self):
        """複数行が正しく変換される"""
        # Arrange
        from iot_app.services.customer_dashboard.grid import format_grid_data
        rows = [
            {
                'event_timestamp': datetime(2026, 1, 1, 0, 0, 0),
                'device_name': 'Device-001',
                'external_temp': 10.0,
            },
            {
                'event_timestamp': datetime(2026, 1, 1, 0, 1, 0),
                'device_name': 'Device-001',
                'external_temp': 11.0,
            },
        ]
        columns = [self._make_column('external_temp')]
        # Act
        result = format_grid_data(rows, columns)
        # Assert
        assert len(result) == 2
        assert result[0]['external_temp'] == 10.0
        assert result[1]['external_temp'] == 11.0

    def test_format_missing_column_value_returns_none(self):
        """センサー値が存在しない場合は None が設定される"""
        # Arrange
        from iot_app.services.customer_dashboard.grid import format_grid_data
        rows = [
            {
                'event_timestamp': datetime(2026, 1, 1, 0, 0, 0),
                'device_name': 'Device-001',
                # external_temp は row に存在しない
            }
        ]
        columns = [self._make_column('external_temp')]
        # Act
        result = format_grid_data(rows, columns)
        # Assert
        assert result[0].get('external_temp') is None

    def test_format_device_name_missing_returns_empty_string(self):
        """device_name が row に存在しない場合は空文字が設定される"""
        # Arrange
        from iot_app.services.customer_dashboard.grid import format_grid_data
        rows = [
            {
                'event_timestamp': datetime(2026, 1, 1, 0, 0, 0),
                # device_name は row に存在しない
            }
        ]
        columns = []
        # Act
        result = format_grid_data(rows, columns)
        # Assert
        assert result[0]['device_name'] == ''


# ===========================================================================
# Section 6: サービス - ページング計算
# ワークフロー仕様書 § ページング > 処理詳細
#   calculate_page_offset(page, per_page=25) → offset を返す
#   PER_PAGE = 25（固定）
#   offset = (page - 1) × per_page
# ===========================================================================

@pytest.mark.unit
class TestCalculatePageOffset:
    """表ガジェット - ページング計算

    観点: 3.1.3（ページング・件数制御）, 1.3.x（数値範囲チェック）
    ワークフロー仕様書 § ページング > 処理詳細
      - PER_PAGE = 25（固定）
      - offset = (page - 1) × PER_PAGE
      - page は 1 以上の整数
    """

    def test_first_page_offset_is_zero(self):
        """3.1.3.1 1ページ目: offset=0"""
        # Arrange
        from iot_app.services.customer_dashboard.grid import calculate_page_offset
        # Act
        result = calculate_page_offset(page=1)
        # Assert
        assert result == 0

    def test_second_page_offset_is_25(self):
        """3.1.3.1 2ページ目: offset=25（PER_PAGE=25）"""
        # Arrange
        from iot_app.services.customer_dashboard.grid import calculate_page_offset
        # Act
        result = calculate_page_offset(page=2)
        # Assert
        assert result == 25

    def test_tenth_page_offset_is_225(self):
        """3.1.3.1 10ページ目: offset=225"""
        # Arrange
        from iot_app.services.customer_dashboard.grid import calculate_page_offset
        # Act
        result = calculate_page_offset(page=10)
        # Assert
        assert result == 225

    def test_per_page_default_is_25(self):
        """3.1.3.1 PER_PAGE固定値: デフォルト per_page=25 が適用される"""
        # Arrange
        from iot_app.services.customer_dashboard.grid import calculate_page_offset
        # Act
        offset_p1 = calculate_page_offset(page=1)
        offset_p2 = calculate_page_offset(page=2)
        # Assert
        assert offset_p2 - offset_p1 == 25

    def test_invalid_when_page_is_zero(self):
        """1.3.1 最小値-1（page=0）: 不正値のため ValueError がスローされる"""
        # Arrange
        from iot_app.services.customer_dashboard.grid import calculate_page_offset
        # Act & Assert
        with pytest.raises((ValueError, AssertionError)):
            calculate_page_offset(page=0)

    def test_invalid_when_page_is_negative(self):
        """1.3.1 負の値（page=-1）: 不正値のため ValueError がスローされる"""
        # Arrange
        from iot_app.services.customer_dashboard.grid import calculate_page_offset
        # Act & Assert
        with pytest.raises((ValueError, AssertionError)):
            calculate_page_offset(page=-1)


# ===========================================================================
# Section 7: サービス - ガジェット登録処理
# ワークフロー仕様書 § ガジェット登録 > 処理詳細
#   register_grid_gadget(params, current_user_id) → DashboardGadgetMaster を登録
#   params: title, group_id, gadget_size
# ===========================================================================

_SERVICE_MODULE = 'iot_app.services.customer_dashboard.grid'


@pytest.mark.unit
class TestRegisterGridGadget:
    """表ガジェット登録処理 - 登録処理呼び出しと登録結果

    観点: 3.2.1 登録処理呼び出し, 3.2.2 登録結果
    ワークフロー仕様書 § ガジェット登録 > 処理詳細
    """

    def _valid_params(self):
        """有効な登録パラメータを返すヘルパー"""
        return {
            'title':       'テスト表ガジェット',
            'group_id':    1,
            'gadget_size': '0',
        }

    @patch(f'{_SERVICE_MODULE}.db')
    def test_register_calls_db_session_add(self, mock_db):
        """3.2.1.1: 正常な入力値で db.session.add が呼び出される"""
        from unittest.mock import Mock
        from iot_app.services.customer_dashboard.grid import register_grid_gadget
        # Arrange
        mock_db.session.add = Mock()
        mock_db.session.commit = Mock()
        mock_db.session.query = Mock()
        mock_db.session.query.return_value.filter.return_value.scalar.return_value = 0
        # Act
        register_grid_gadget(self._valid_params(), current_user_id=1)
        # Assert
        mock_db.session.add.assert_called_once()

    @patch(f'{_SERVICE_MODULE}.db')
    def test_register_calls_db_session_commit(self, mock_db):
        """3.2.1.1: 正常な入力値で db.session.commit が呼び出される"""
        from unittest.mock import Mock
        from iot_app.services.customer_dashboard.grid import register_grid_gadget
        # Arrange
        mock_db.session.add = Mock()
        mock_db.session.commit = Mock()
        mock_db.session.query = Mock()
        mock_db.session.query.return_value.filter.return_value.scalar.return_value = 0
        # Act
        register_grid_gadget(self._valid_params(), current_user_id=1)
        # Assert
        mock_db.session.commit.assert_called_once()

    @patch(f'{_SERVICE_MODULE}.db')
    def test_register_gadget_name_matches_title(self, mock_db):
        """3.2.1.1: 登録されるガジェット名がフォームの title と一致する"""
        from unittest.mock import Mock
        from iot_app.services.customer_dashboard.grid import register_grid_gadget
        # Arrange
        captured = {}
        mock_db.session.add = Mock(side_effect=lambda g: captured.update({'gadget': g}))
        mock_db.session.commit = Mock()
        mock_db.session.query = Mock()
        mock_db.session.query.return_value.filter.return_value.scalar.return_value = 0
        # Act
        register_grid_gadget(self._valid_params(), current_user_id=1)
        # Assert
        assert captured['gadget'].gadget_name == 'テスト表ガジェット'

    @patch(f'{_SERVICE_MODULE}.db')
    def test_register_chart_config_is_empty_json(self, mock_db):
        """3.2.1.1: chart_config は空の JSON オブジェクト {} として登録される"""
        import json
        from unittest.mock import Mock
        from iot_app.services.customer_dashboard.grid import register_grid_gadget
        # Arrange
        captured = {}
        mock_db.session.add = Mock(side_effect=lambda g: captured.update({'gadget': g}))
        mock_db.session.commit = Mock()
        mock_db.session.query = Mock()
        mock_db.session.query.return_value.filter.return_value.scalar.return_value = 0
        # Act
        register_grid_gadget(self._valid_params(), current_user_id=1)
        # Assert
        assert json.loads(captured['gadget'].chart_config) == {}

    @patch(f'{_SERVICE_MODULE}.db')
    def test_register_data_source_config_has_empty_device_id(self, mock_db):
        """3.2.1.1: data_source_config の device_id は None で登録される（可変デバイスモード）"""
        import json
        from unittest.mock import Mock
        from iot_app.services.customer_dashboard.grid import register_grid_gadget
        # Arrange
        captured = {}
        mock_db.session.add = Mock(side_effect=lambda g: captured.update({'gadget': g}))
        mock_db.session.commit = Mock()
        mock_db.session.query = Mock()
        mock_db.session.query.return_value.filter.return_value.scalar.return_value = 0
        # Act
        register_grid_gadget(self._valid_params(), current_user_id=1)
        # Assert
        data_source_config = json.loads(captured['gadget'].data_source_config)
        assert 'device_id' in data_source_config
        assert data_source_config['device_id'] is None

    @patch(f'{_SERVICE_MODULE}.db')
    def test_register_position_y_increments_from_existing_max(self, mock_db):
        """3.2.1.1: position_y は既存の最大値 + 1 で登録される"""
        from unittest.mock import Mock
        from iot_app.services.customer_dashboard.grid import register_grid_gadget
        # Arrange
        captured = {}
        mock_db.session.add = Mock(side_effect=lambda g: captured.update({'gadget': g}))
        mock_db.session.commit = Mock()
        mock_db.session.query = Mock()
        mock_db.session.query.return_value.filter.return_value.scalar.return_value = 3
        # Act
        register_grid_gadget(self._valid_params(), current_user_id=1)
        # Assert
        assert captured['gadget'].position_y == 4

    @patch(f'{_SERVICE_MODULE}.db')
    def test_register_gadget_uuid_is_valid_uuid(self, mock_db):
        """3.2.1.1: gadget_uuid が有効な UUID 形式で登録される"""
        import uuid as uuid_module
        from unittest.mock import Mock
        from iot_app.services.customer_dashboard.grid import register_grid_gadget
        # Arrange
        captured = {}
        mock_db.session.add = Mock(side_effect=lambda g: captured.update({'gadget': g}))
        mock_db.session.commit = Mock()
        mock_db.session.query = Mock()
        mock_db.session.query.return_value.filter.return_value.scalar.return_value = 0
        # Act
        register_grid_gadget(self._valid_params(), current_user_id=1)
        # Assert: UUID形式として解析できることを確認（不正な場合は ValueError）
        uuid_module.UUID(captured['gadget'].gadget_uuid)

    @patch(f'{_SERVICE_MODULE}.db')
    def test_register_dashboard_group_id_matches_param(self, mock_db):
        """3.2.1.1: dashboard_group_id がフォームの group_id と一致する"""
        from unittest.mock import Mock
        from iot_app.services.customer_dashboard.grid import register_grid_gadget
        # Arrange
        captured = {}
        mock_db.session.add = Mock(side_effect=lambda g: captured.update({'gadget': g}))
        mock_db.session.commit = Mock()
        mock_db.session.query = Mock()
        mock_db.session.query.return_value.filter.return_value.scalar.return_value = 0
        params = self._valid_params()
        params['group_id'] = 42
        # Act
        register_grid_gadget(params, current_user_id=1)
        # Assert
        assert captured['gadget'].dashboard_group_id == 42

    @patch(f'{_SERVICE_MODULE}.db')
    def test_register_gadget_type_is_grid_type(self, mock_db):
        """3.2.1.1: gadget_type_id が '表' ガジェットのタイプIDで登録される"""
        from unittest.mock import Mock
        from iot_app.services.customer_dashboard.grid import register_grid_gadget
        # Arrange
        captured = {}
        mock_gadget_type = Mock()
        mock_gadget_type.gadget_type_id = 7
        mock_db.session.add = Mock(side_effect=lambda g: captured.update({'gadget': g}))
        mock_db.session.commit = Mock()
        mock_db.session.query = Mock()
        mock_db.session.query.return_value.filter.return_value.scalar.return_value = 0
        mock_db.session.query.return_value.filter_by.return_value.first.return_value = mock_gadget_type
        # Act
        register_grid_gadget(self._valid_params(), current_user_id=1)
        # Assert
        assert captured['gadget'].gadget_type_id == 7

    @patch(f'{_SERVICE_MODULE}.db')
    def test_register_position_x_is_zero(self, mock_db):
        """3.2.1.1: position_x は 0（固定値）で登録される"""
        from unittest.mock import Mock
        from iot_app.services.customer_dashboard.grid import register_grid_gadget
        # Arrange
        captured = {}
        mock_db.session.add = Mock(side_effect=lambda g: captured.update({'gadget': g}))
        mock_db.session.commit = Mock()
        mock_db.session.query = Mock()
        mock_db.session.query.return_value.filter.return_value.scalar.return_value = 0
        # Act
        register_grid_gadget(self._valid_params(), current_user_id=1)
        # Assert
        assert captured['gadget'].position_x == 0

    @patch(f'{_SERVICE_MODULE}.db')
    def test_register_gadget_size_matches_param(self, mock_db):
        """3.2.1.1: gadget_size がフォームの gadget_size と一致する"""
        from unittest.mock import Mock
        from iot_app.services.customer_dashboard.grid import register_grid_gadget
        # Arrange
        captured = {}
        mock_db.session.add = Mock(side_effect=lambda g: captured.update({'gadget': g}))
        mock_db.session.commit = Mock()
        mock_db.session.query = Mock()
        mock_db.session.query.return_value.filter.return_value.scalar.return_value = 0
        params = self._valid_params()
        params['gadget_size'] = '1'  # 2x4
        # Act
        register_grid_gadget(params, current_user_id=1)
        # Assert
        assert str(captured['gadget'].gadget_size) == '1'

    @patch(f'{_SERVICE_MODULE}.db')
    def test_register_display_order_increments_from_existing_max(self, mock_db):
        """3.2.1.1: display_order は既存の最大値 + 1 で登録される"""
        from unittest.mock import Mock
        from iot_app.services.customer_dashboard.grid import register_grid_gadget
        # Arrange
        captured = {}
        mock_db.session.add = Mock(side_effect=lambda g: captured.update({'gadget': g}))
        mock_db.session.commit = Mock()
        mock_db.session.query = Mock()
        mock_db.session.query.return_value.filter.return_value.scalar.return_value = 2
        # Act
        register_grid_gadget(self._valid_params(), current_user_id=1)
        # Assert
        assert captured['gadget'].display_order == 3

    @patch(f'{_SERVICE_MODULE}.db')
    def test_register_creator_is_current_user_id(self, mock_db):
        """3.2.1.1: creator が current_user_id で登録される"""
        from unittest.mock import Mock
        from iot_app.services.customer_dashboard.grid import register_grid_gadget
        # Arrange
        captured = {}
        mock_db.session.add = Mock(side_effect=lambda g: captured.update({'gadget': g}))
        mock_db.session.commit = Mock()
        mock_db.session.query = Mock()
        mock_db.session.query.return_value.filter.return_value.scalar.return_value = 0
        # Act
        register_grid_gadget(self._valid_params(), current_user_id=99)
        # Assert
        assert captured['gadget'].creator == 99

    @patch(f'{_SERVICE_MODULE}.db')
    def test_register_modifier_is_current_user_id(self, mock_db):
        """3.2.1.1: modifier が current_user_id で登録される"""
        from unittest.mock import Mock
        from iot_app.services.customer_dashboard.grid import register_grid_gadget
        # Arrange
        captured = {}
        mock_db.session.add = Mock(side_effect=lambda g: captured.update({'gadget': g}))
        mock_db.session.commit = Mock()
        mock_db.session.query = Mock()
        mock_db.session.query.return_value.filter.return_value.scalar.return_value = 0
        # Act
        register_grid_gadget(self._valid_params(), current_user_id=99)
        # Assert
        assert captured['gadget'].modifier == 99

    @patch(f'{_SERVICE_MODULE}.db')
    def test_register_delete_flag_is_false(self, mock_db):
        """3.2.1.1: delete_flag が False で登録される"""
        from unittest.mock import Mock
        from iot_app.services.customer_dashboard.grid import register_grid_gadget
        # Arrange
        captured = {}
        mock_db.session.add = Mock(side_effect=lambda g: captured.update({'gadget': g}))
        mock_db.session.commit = Mock()
        mock_db.session.query = Mock()
        mock_db.session.query.return_value.filter.return_value.scalar.return_value = 0
        # Act
        register_grid_gadget(self._valid_params(), current_user_id=1)
        # Assert
        assert captured['gadget'].delete_flag is False

    @patch(f'{_SERVICE_MODULE}.db')
    def test_register_validation_error_does_not_call_db_add(self, mock_db):
        """3.2.1.3: バリデーションエラー発生時は db.session.add が呼ばれない"""
        from unittest.mock import Mock
        from iot_app.services.customer_dashboard.grid import register_grid_gadget
        # Arrange
        mock_db.session.add = Mock()
        params = self._valid_params()
        params['title'] = ''  # 必須項目を空にしてバリデーションエラーを発生させる
        # Act & Assert
        with pytest.raises(Exception):
            register_grid_gadget(params, current_user_id=1)
        mock_db.session.add.assert_not_called()

    @patch(f'{_SERVICE_MODULE}.db')
    def test_register_returns_gadget(self, mock_db):
        """3.2.2.1: 登録成功時に登録されたガジェットオブジェクトが返る"""
        from unittest.mock import Mock
        from iot_app.services.customer_dashboard.grid import register_grid_gadget
        # Arrange
        captured = {}

        def set_gadget(g):
            g.gadget_id = 99
            captured['gadget'] = g

        mock_db.session.add = Mock(side_effect=set_gadget)
        mock_db.session.commit = Mock()
        mock_db.session.query = Mock()
        mock_db.session.query.return_value.filter.return_value.scalar.return_value = 0
        # Act
        result = register_grid_gadget(self._valid_params(), current_user_id=1)
        # Assert
        assert result is not None
        assert result.gadget_id == 99


# ===========================================================================
# Section 8: サービス - ガジェット登録ロールバック
# ワークフロー仕様書 § ガジェット登録 > エラーハンドリング
# ===========================================================================

@pytest.mark.unit
class TestRegisterGridGadgetRollback:
    """表ガジェット登録処理 - 副作用チェック

    観点: 2.3 副作用チェック
    ワークフロー仕様書 § ガジェット登録 > エラーハンドリング
      - DB例外発生時は rollback が呼ばれる
      - 処理失敗時はデータが永続化されない
    """

    def _valid_params(self):
        return {
            'title':       'テスト表ガジェット',
            'group_id':    1,
            'gadget_size': '0',
        }

    @patch(f'{_SERVICE_MODULE}.db')
    def test_rollback_called_on_db_exception(self, mock_db):
        """2.3.2: DB 例外発生時に db.session.rollback が呼び出される"""
        from unittest.mock import Mock
        from iot_app.services.customer_dashboard.grid import register_grid_gadget
        # Arrange
        mock_db.session.add = Mock()
        mock_db.session.commit.side_effect = Exception('DB接続エラー')
        mock_db.session.rollback = Mock()
        mock_db.session.query = Mock()
        mock_db.session.query.return_value.filter.return_value.scalar.return_value = 0
        # Act & Assert
        with pytest.raises(Exception):
            register_grid_gadget(self._valid_params(), current_user_id=1)
        mock_db.session.rollback.assert_called_once()

    @patch(f'{_SERVICE_MODULE}.db')
    def test_data_not_persisted_on_exception(self, mock_db):
        """2.3.1: 処理失敗時（例外発生時）はデータが永続化されない（commit 完了前に rollback）"""
        from unittest.mock import Mock
        from iot_app.services.customer_dashboard.grid import register_grid_gadget
        # Arrange
        mock_db.session.add = Mock()
        mock_db.session.commit.side_effect = Exception('DB接続エラー')
        mock_db.session.rollback = Mock()
        mock_db.session.query = Mock()
        mock_db.session.query.return_value.filter.return_value.scalar.return_value = 0
        # Act & Assert
        with pytest.raises(Exception):
            register_grid_gadget(self._valid_params(), current_user_id=1)
        # Assert: commit が失敗し rollback が呼ばれたことを確認
        mock_db.session.rollback.assert_called_once()


# ===========================================================================
# Section 9: サービス - センサーデータ取得
# ワークフロー仕様書 § ガジェットデータ取得 > 処理詳細 > ② センサーデータ取得
#   fetch_grid_data(device_id, start_datetime, end_datetime, limit=25, offset=0)
#   → sensor_data_view を照会し、行リストを返す
# ===========================================================================

@pytest.mark.unit
class TestFetchGridData:
    """表ガジェット - センサーデータ取得

    観点: 2.1 正常系処理, 3.1.3 ページング・件数制御, 3.1.4 検索結果戻り値ハンドリング
    ワークフロー仕様書 § ② センサーデータ取得
      - execute_silver_query が呼ばれる
      - limit / offset が Silver層クエリに渡される
      - 戻り値がリストとして返却される
      - データなしの場合は空リストが返却される
    """

    def _base_args(self):
        return dict(
            device_id=1,
            start_datetime=datetime(2026, 1, 1, 0, 0, 0),
            end_datetime=datetime(2026, 1, 1, 23, 59, 59),
        )

    @patch(f'{_SERVICE_MODULE}.execute_silver_query')
    def test_calls_execute_silver_query(self, mock_silver):
        """2.1.1: fetch_grid_data は execute_silver_query を呼び出す"""
        from iot_app.services.customer_dashboard.grid import fetch_grid_data
        # Arrange
        mock_silver.return_value = []
        # Act
        fetch_grid_data(**self._base_args())
        # Assert
        mock_silver.assert_called_once()

    @patch(f'{_SERVICE_MODULE}.execute_silver_query')
    def test_limit_is_passed_to_query(self, mock_silver):
        """3.1.3.1: limit の設定値が Silver層クエリに渡される"""
        from iot_app.services.customer_dashboard.grid import fetch_grid_data
        # Arrange
        mock_silver.return_value = []
        # Act
        fetch_grid_data(**self._base_args(), limit=25, offset=0)
        # Assert: 呼び出し時の引数に limit=25 が含まれる
        call_kwargs = mock_silver.call_args
        args_str = str(call_kwargs)
        assert '25' in args_str

    @patch(f'{_SERVICE_MODULE}.execute_silver_query')
    def test_offset_is_passed_to_query(self, mock_silver):
        """3.1.3.1: offset の設定値が Silver層クエリに渡される（2ページ目: offset=25）"""
        from iot_app.services.customer_dashboard.grid import fetch_grid_data
        # Arrange
        mock_silver.return_value = []
        # Act
        fetch_grid_data(**self._base_args(), limit=25, offset=25)
        # Assert: 呼び出し時の引数に offset=25 が含まれる
        call_kwargs = mock_silver.call_args
        args_str = str(call_kwargs)
        assert '25' in args_str

    @patch(f'{_SERVICE_MODULE}.execute_silver_query')
    def test_returns_list_from_silver_query(self, mock_silver):
        """3.1.4.1: Silver層がリストを返した場合、そのまま返却される"""
        from iot_app.services.customer_dashboard.grid import fetch_grid_data
        # Arrange
        expected = [
            {'event_timestamp': datetime(2026, 1, 1, 0, 0, 0), 'external_temp': 25.0},
            {'event_timestamp': datetime(2026, 1, 1, 0, 1, 0), 'external_temp': 26.0},
        ]
        mock_silver.return_value = expected
        # Act
        result = fetch_grid_data(**self._base_args())
        # Assert
        assert result == expected

    @patch(f'{_SERVICE_MODULE}.execute_silver_query')
    def test_returns_empty_list_when_no_data(self, mock_silver):
        """3.1.4.2: Silver層が空リストを返した場合、空リストが返却される"""
        from iot_app.services.customer_dashboard.grid import fetch_grid_data
        # Arrange
        mock_silver.return_value = []
        # Act
        result = fetch_grid_data(**self._base_args())
        # Assert
        assert result == []

    @patch(f'{_SERVICE_MODULE}.execute_silver_query')
    def test_returns_list_type(self, mock_silver):
        """2.1.2: 戻り値がリスト型である"""
        from iot_app.services.customer_dashboard.grid import fetch_grid_data
        # Arrange
        mock_silver.return_value = [{'event_timestamp': datetime(2026, 1, 1, 0, 0, 0)}]
        # Act
        result = fetch_grid_data(**self._base_args())
        # Assert
        assert isinstance(result, list)

    @patch(f'{_SERVICE_MODULE}.execute_silver_query')
    def test_default_limit_is_1000(self, mock_silver):
        """3.1.3.1: limit を省略した場合、デフォルト値 1000 が Silver層クエリに渡される
        ワークフロー仕様書 § ② センサーデータ取得: 最大取得件数 1,000件
        """
        from iot_app.services.customer_dashboard.grid import fetch_grid_data
        # Arrange
        mock_silver.return_value = []
        # Act
        fetch_grid_data(**self._base_args())
        # Assert: 呼び出し引数に 1000 が含まれる
        args_str = str(mock_silver.call_args)
        assert '1000' in args_str

    @patch(f'{_SERVICE_MODULE}.execute_silver_query')
    def test_csv_limit_is_100000(self, mock_silver):
        """3.1.3.1: CSV エクスポート時は limit=100,000 が Silver層クエリに渡される
        ワークフロー仕様書 § CSVエクスポート ② センサーデータ取得: 最大取得件数 100,000件
        """
        from iot_app.services.customer_dashboard.grid import fetch_grid_data
        # Arrange
        mock_silver.return_value = []
        # Act
        fetch_grid_data(**self._base_args(), limit=100000)
        # Assert: 呼び出し引数に 100000 が含まれる
        args_str = str(mock_silver.call_args)
        assert '100000' in args_str


# ===========================================================================
# Section 10: サービス - カラム定義取得
# ワークフロー仕様書 § ③ テーブルカラム名取得 / ④ CSVカラム定義
#   get_column_definition() → measurement_item_master を measurement_item_id 昇順で取得
# ===========================================================================

@pytest.mark.unit
class TestGetColumnDefinition:
    """表ガジェット - カラム定義取得

    観点: 3.1.1 検索条件指定, 3.1.4 検索結果戻り値ハンドリング
    ワークフロー仕様書 § ③ テーブルカラム名取得 / ④ CSVカラム定義
      - delete_flag=False のレコードのみ取得
      - measurement_item_id 昇順で取得される
      - 戻り値がリストとして返却される
    """

    @patch(f'{_SERVICE_MODULE}.db')
    def test_column_definition_ordered_by_measurement_item_id(self, mock_db):
        """3.1.1.1: get_column_definition は measurement_item_id 昇順でクエリする"""
        from iot_app.services.customer_dashboard.grid import get_column_definition
        # Arrange
        mock_db.session.query.return_value.filter.return_value.order_by.return_value.all.return_value = []
        # Act
        get_column_definition()
        # Assert: order_by が呼ばれている
        assert mock_db.session.query.return_value.filter.return_value.order_by.called

    @patch(f'{_SERVICE_MODULE}.db')
    def test_column_definition_excludes_deleted(self, mock_db):
        """3.1.1.1: delete_flag=True のカラムは除外される（filter 条件の確認）"""
        from iot_app.models.measurement import MeasurementItemMaster
        from iot_app.services.customer_dashboard.grid import get_column_definition
        # Arrange
        mock_db.session.query.return_value.filter.return_value.order_by.return_value.all.return_value = []
        # Act
        get_column_definition()
        # Assert: MeasurementItemMaster に対するクエリが呼ばれている
        calls = [str(c) for c in mock_db.session.query.call_args_list]
        assert any('MeasurementItemMaster' in c for c in calls)

    @patch(f'{_SERVICE_MODULE}.db')
    def test_column_definition_returns_list(self, mock_db):
        """3.1.4.1: 戻り値がリストとして返却される"""
        from iot_app.services.customer_dashboard.grid import get_column_definition
        # Arrange
        mock_col = MagicMock()
        mock_col.silver_data_column_name = 'external_temp'
        mock_col.display_name = '外気温度'
        mock_db.session.query.return_value.filter.return_value.order_by.return_value.all.return_value = [mock_col]
        # Act
        result = get_column_definition()
        # Assert
        assert isinstance(result, list)
        assert len(result) == 1

    @patch(f'{_SERVICE_MODULE}.db')
    def test_column_definition_returns_empty_list_when_no_items(self, mock_db):
        """3.1.4.2: measurement_item_master が空の場合、空リストが返却される"""
        from iot_app.services.customer_dashboard.grid import get_column_definition
        # Arrange
        mock_db.session.query.return_value.filter.return_value.order_by.return_value.all.return_value = []
        # Act
        result = get_column_definition()
        # Assert
        assert result == []


# ===========================================================================
# Section 11: サービス - 登録モーダル表示コンテキスト
# ワークフロー仕様書 § ガジェット登録モーダル表示 > 処理詳細
#   get_grid_create_context(dashboard_id) → {'groups': [...]}
# ===========================================================================

@pytest.mark.unit
class TestGetGridCreateContext:
    """表ガジェット登録モーダル用コンテキスト取得

    使用ルート:
        GET /analysis/customer-dashboard/gadgets/grid/create

    ワークフロー仕様書 § ガジェット登録モーダル表示 > 処理詳細
    """

    @patch(f'{_SERVICE_MODULE}.db')
    def test_returns_groups_key(self, mock_db):
        """返却値に groups キーが含まれる"""
        from iot_app.services.customer_dashboard.grid import get_grid_create_context
        # Arrange
        mock_db.session.query.return_value.filter.return_value.order_by.return_value.all.return_value = []
        # Act
        result = get_grid_create_context(dashboard_id=1)
        # Assert
        assert 'groups' in result

    @patch(f'{_SERVICE_MODULE}.db')
    def test_groups_excludes_deleted(self, mock_db):
        """delete_flag=True のグループは除外される（filter 条件の確認）"""
        from iot_app.models.customer_dashboard import DashboardGroupMaster
        from iot_app.services.customer_dashboard.grid import get_grid_create_context
        # Arrange
        mock_db.session.query.return_value.filter.return_value.order_by.return_value.all.return_value = []
        # Act
        get_grid_create_context(dashboard_id=1)
        # Assert: DashboardGroupMaster に対するクエリが呼ばれている
        calls = [str(c) for c in mock_db.session.query.call_args_list]
        assert any('DashboardGroupMaster' in c for c in calls)

    @patch(f'{_SERVICE_MODULE}.db')
    def test_groups_returns_list(self, mock_db):
        """ダッシュボードグループが存在する場合、リストとして返却される"""
        from iot_app.services.customer_dashboard.grid import get_grid_create_context
        # Arrange
        mock_group = MagicMock()
        mock_group.dashboard_group_id = 1
        mock_group.dashboard_group_name = 'グループA'
        mock_db.session.query.return_value.filter.return_value.order_by.return_value.all.return_value = [mock_group]
        # Act
        result = get_grid_create_context(dashboard_id=1)
        # Assert
        assert len(result['groups']) == 1

    @patch(f'{_SERVICE_MODULE}.db')
    def test_groups_empty_when_no_groups(self, mock_db):
        """ダッシュボードグループが存在しない場合、空リストが返却される"""
        from iot_app.services.customer_dashboard.grid import get_grid_create_context
        # Arrange
        mock_db.session.query.return_value.filter.return_value.order_by.return_value.all.return_value = []
        # Act
        result = get_grid_create_context(dashboard_id=1)
        # Assert
        assert result['groups'] == []


# ===========================================================================
# Section 12: サービス - CSV生成ロジック
# ワークフロー仕様書 § CSVエクスポート > 処理詳細
#   generate_grid_csv(grid_data, columns) → CSV文字列（UTF-8 BOM付き）
#   ヘッダー: 受信日時, デバイス名称, + measurement_item display_name
# ===========================================================================

@pytest.mark.unit
class TestGridCsvGeneration:
    """表ガジェット CSVエクスポート - CSV生成ロジック

    観点: 3.5.1 CSV生成ロジック, 3.5.2 エスケープ処理, 3.5.3 エンコーディング処理
    ワークフロー仕様書 § CSVエクスポート > 処理詳細 ④ CSVカラム定義
    """

    def _make_column(self, silver_data_column_name, display_name):
        col = MagicMock()
        col.silver_data_column_name = silver_data_column_name
        col.display_name = display_name
        return col

    def _read_csv(self, csv_bytes_or_str):
        import io
        import csv
        if isinstance(csv_bytes_or_str, bytes):
            text = csv_bytes_or_str.decode('utf-8-sig')
        else:
            text = csv_bytes_or_str.lstrip('\ufeff')
        return list(csv.reader(io.StringIO(text)))

    def _call(self, grid_data, columns):
        from iot_app.services.customer_dashboard.grid import generate_grid_csv
        return generate_grid_csv(grid_data, columns)

    # ----------------------------------------------------------
    # 3.5.1 CSV生成ロジック - ヘッダー
    # ----------------------------------------------------------

    def test_csv_header_starts_with_timestamp_and_device(self):
        """3.5.1.1: ヘッダー先頭は「受信日時」「デバイス名称」"""
        # Arrange
        columns = [self._make_column('external_temp', '外気温度')]
        # Act
        rows = self._read_csv(self._call([], columns))
        # Assert
        assert rows[0][0] == '受信日時'
        assert rows[0][1] == 'デバイス名称'

    def test_csv_header_includes_measurement_item_display_names(self):
        """3.5.1.1: ヘッダーに measurement_item の display_name が含まれる"""
        # Arrange
        columns = [
            self._make_column('external_temp', '外気温度'),
            self._make_column('set_temp_freezer_1', '第1冷凍 設定温度'),
        ]
        # Act
        rows = self._read_csv(self._call([], columns))
        # Assert
        assert '外気温度' in rows[0]
        assert '第1冷凍 設定温度' in rows[0]

    def test_csv_header_column_order(self):
        """3.5.1.4: カラム順序は 受信日時 → デバイス名称 → measurement_item 順"""
        # Arrange
        columns = [
            self._make_column('external_temp', '外気温度'),
            self._make_column('set_temp_freezer_1', '第1冷凍 設定温度'),
        ]
        # Act
        rows = self._read_csv(self._call([], columns))
        # Assert
        assert rows[0] == ['受信日時', 'デバイス名称', '外気温度', '第1冷凍 設定温度']

    # ----------------------------------------------------------
    # 3.5.1 CSV生成ロジック - データ行
    # ----------------------------------------------------------

    def test_csv_data_row_count_matches_grid_data(self):
        """3.5.1.2: データ行数が grid_data の件数と一致する"""
        # Arrange
        columns = [self._make_column('external_temp', '外気温度')]
        grid_data = [
            {'event_timestamp': '2026/01/01 00:00:00', 'device_name': 'DEV-001', 'external_temp': 10.0},
            {'event_timestamp': '2026/01/01 00:01:00', 'device_name': 'DEV-001', 'external_temp': 11.0},
        ]
        # Act
        rows = self._read_csv(self._call(grid_data, columns))
        # Assert: ヘッダー1行 + データ2行
        assert len(rows) == 3

    def test_csv_empty_when_no_data(self):
        """3.5.1.3: データなしの場合はヘッダー行のみ出力される"""
        # Arrange
        columns = [self._make_column('external_temp', '外気温度')]
        # Act
        rows = self._read_csv(self._call([], columns))
        # Assert
        assert len(rows) == 1

    def test_csv_event_timestamp_in_column_0(self):
        """3.5.1.2: データ行の列0に受信日時が出力される"""
        # Arrange
        columns = []
        grid_data = [{'event_timestamp': '2026/03/05 12:00:00', 'device_name': 'DEV-001'}]
        # Act
        rows = self._read_csv(self._call(grid_data, columns))
        # Assert
        assert rows[1][0] == '2026/03/05 12:00:00'

    def test_csv_device_name_in_column_1(self):
        """3.5.1.2: データ行の列1にデバイス名称が出力される"""
        # Arrange
        columns = []
        grid_data = [{'event_timestamp': '2026/03/05 12:00:00', 'device_name': 'TEST-DEVICE'}]
        # Act
        rows = self._read_csv(self._call(grid_data, columns))
        # Assert
        assert rows[1][1] == 'TEST-DEVICE'

    def test_csv_sensor_value_in_data_columns(self):
        """3.5.1.2: センサー値が measurement_item 列に出力される"""
        # Arrange
        columns = [self._make_column('external_temp', '外気温度')]
        grid_data = [{'event_timestamp': '2026/01/01 00:00:00', 'device_name': 'DEV-001', 'external_temp': 25.5}]
        # Act
        rows = self._read_csv(self._call(grid_data, columns))
        # Assert
        assert rows[1][2] == '25.5'

    # ----------------------------------------------------------
    # 3.5.2 エスケープ処理
    # ----------------------------------------------------------

    def test_csv_device_name_with_comma_is_quoted(self):
        """3.5.2.1: デバイス名称にカンマを含む場合はダブルクォートで囲まれる"""
        # Arrange
        columns = []
        grid_data = [{'event_timestamp': '2026/01/01 00:00:00', 'device_name': 'DEV,001'}]
        # Act
        csv_text = self._call(grid_data, columns)
        # Assert
        assert '"DEV,001"' in csv_text

    def test_csv_device_name_with_double_quote_is_escaped(self):
        """3.5.2.3: デバイス名称にダブルクォートを含む場合は \"\" でエスケープされる"""
        # Arrange
        columns = []
        grid_data = [{'event_timestamp': '2026/01/01 00:00:00', 'device_name': 'DEV"001'}]
        # Act
        rows = self._read_csv(self._call(grid_data, columns))
        # Assert
        assert rows[1][1] == 'DEV"001'

    # ----------------------------------------------------------
    # 3.5.3 エンコーディング処理
    # ----------------------------------------------------------

    def test_csv_device_name_with_newline_is_quoted(self):
        """3.5.2.2: デバイス名称に改行を含む場合はダブルクォートで囲まれる"""
        # Arrange
        columns = []
        grid_data = [{'event_timestamp': '2026/01/01 00:00:00', 'device_name': 'DEV\n001'}]
        # Act
        rows = self._read_csv(self._call(grid_data, columns))
        # Assert
        assert rows[1][1] == 'DEV\n001'

    def test_csv_no_escape_for_plain_data(self):
        """3.5.2.4: 特殊文字を含まないデータはそのまま出力される"""
        # Arrange
        columns = []
        grid_data = [{'event_timestamp': '2026/01/01 00:00:00', 'device_name': 'DEVICE001'}]
        # Act
        rows = self._read_csv(self._call(grid_data, columns))
        # Assert
        assert rows[1][1] == 'DEVICE001'

    def test_csv_has_utf8_bom(self):
        """3.5.3.1: CSV出力の先頭に UTF-8 BOM（0xEF 0xBB 0xBF）が付与される"""
        # Arrange
        columns = []
        # Act
        result = self._call([], columns)
        # Assert
        if isinstance(result, bytes):
            assert result[:3] == b'\xef\xbb\xbf'
        else:
            assert result.startswith('\ufeff')

    def test_csv_japanese_characters_not_garbled(self):
        """3.5.3.2: 日本語データを含む場合に文字化けなく出力される"""
        # Arrange
        columns = [self._make_column('external_temp', '外気温度')]
        grid_data = [{'event_timestamp': '2026/01/01 00:00:00', 'device_name': 'テストデバイス', 'external_temp': 25.0}]
        # Act
        rows = self._read_csv(self._call(grid_data, columns))
        # Assert
        assert rows[0][2] == '外気温度'
        assert rows[1][1] == 'テストデバイス'

    def test_csv_emoji_characters_not_garbled(self):
        """3.5.3.3: 絵文字等の特殊文字を含む場合に文字化けなく出力される"""
        # Arrange
        columns = []
        grid_data = [{'event_timestamp': '2026/01/01 00:00:00', 'device_name': 'DEV😊001'}]
        # Act
        rows = self._read_csv(self._call(grid_data, columns))
        # Assert
        assert rows[1][1] == 'DEV😊001'
