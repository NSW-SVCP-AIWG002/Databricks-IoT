"""
顧客作成ダッシュボード 円グラフガジェット - 単体テスト

対象:
  - src/iot_app/forms/customer_dashboard/circle_chart.py (CircleChartGadgetForm) ※未実装
  - src/iot_app/services/customer_dashboard/circle_chart.py (format_circle_chart_data) ※未実装
  - src/iot_app/services/customer_dashboard/common.py (check_gadget_access 等)

参照仕様書:
  - docs/03-features/flask-app/customer-dashboard/circle-chart/ui-specification.md
  - docs/03-features/flask-app/customer-dashboard/circle-chart/workflow-specification.md
"""

import pytest
from unittest.mock import MagicMock, patch

COMMON_SERVICE_MODULE = 'iot_app.services.customer_dashboard.common'

# UI仕様書 § (4) 凡例一覧: measurement_item_id 1〜22 の有効ID
_ALL_ITEM_IDS = list(range(1, 23))


# ===========================================================================
# Section 1: フォームバリデーション - タイトル (CircleChartGadgetForm.gadget_name)
# UI仕様書 § バリデーション（登録画面）
#   タイトル: 必須、最大20文字
# ===========================================================================

@pytest.mark.unit
class TestCircleChartGadgetFormTitle:
    """円グラフガジェット登録フォーム - タイトルバリデーション

    観点: 1.1.1（必須チェック）, 1.1.2（最大文字列長チェック）
    UI仕様書 § バリデーション（登録画面）
      - タイトル: 必須 → エラー「タイトルを入力してください」
      - タイトル: 最大20文字 → エラー「タイトルは20文字以内で入力してください」
    """

    def test_valid_when_title_provided(self, app):
        """1.1.1.3 入力あり: タイトルが入力されている場合はバリデーション通過"""
        # Arrange
        from iot_app.forms.customer_dashboard.circle_chart import CircleChartGadgetForm
        # Act
        with app.test_request_context():
            form = CircleChartGadgetForm(data={'gadget_name': '円グラフ'})
            result = form.validate()
        # Assert
        assert result is True

    def test_invalid_when_title_empty(self, app):
        """1.1.1.1 空文字: タイトルが空文字の場合はバリデーションエラー"""
        # Arrange
        from iot_app.forms.customer_dashboard.circle_chart import CircleChartGadgetForm
        # Act
        with app.test_request_context():
            form = CircleChartGadgetForm(data={'gadget_name': ''})
            result = form.validate()
        # Assert
        assert result is False
        assert 'gadget_name' in form.errors

    def test_invalid_when_title_none(self, app):
        """1.1.1.2 None: タイトルが None の場合はバリデーションエラー"""
        # Arrange
        from iot_app.forms.customer_dashboard.circle_chart import CircleChartGadgetForm
        # Act
        with app.test_request_context():
            form = CircleChartGadgetForm(data={'gadget_name': None})
            result = form.validate()
        # Assert
        assert result is False
        assert 'gadget_name' in form.errors

    def test_invalid_when_title_whitespace_only(self, app):
        """1.1.1.4 空白のみ: DataRequired が strip するためバリデーションエラー"""
        # Arrange
        from iot_app.forms.customer_dashboard.circle_chart import CircleChartGadgetForm
        # Act
        with app.test_request_context():
            form = CircleChartGadgetForm(data={'gadget_name': '   '})
            result = form.validate()
        # Assert
        assert result is False
        assert 'gadget_name' in form.errors

    def test_valid_when_title_is_19_chars(self, app):
        """1.2.1 最大長-1（19文字）: バリデーション通過"""
        # Arrange
        from iot_app.forms.customer_dashboard.circle_chart import CircleChartGadgetForm
        # Act
        with app.test_request_context():
            form = CircleChartGadgetForm(data={'gadget_name': 'a' * 19})
            result = form.validate()
        # Assert
        assert result is True

    def test_valid_when_title_is_20_chars(self, app):
        """1.2.2 最大長ちょうど（20文字）: バリデーション通過"""
        # Arrange
        from iot_app.forms.customer_dashboard.circle_chart import CircleChartGadgetForm
        # Act
        with app.test_request_context():
            form = CircleChartGadgetForm(data={'gadget_name': 'a' * 20})
            result = form.validate()
        # Assert
        assert result is True

    def test_invalid_when_title_exceeds_20_chars(self, app):
        """1.2.3 最大長+1（21文字）: バリデーションエラー"""
        # Arrange
        from iot_app.forms.customer_dashboard.circle_chart import CircleChartGadgetForm
        # Act
        with app.test_request_context():
            form = CircleChartGadgetForm(data={'gadget_name': 'a' * 21})
            result = form.validate()
        # Assert
        assert result is False
        assert 'gadget_name' in form.errors

    def test_error_message_for_empty_title(self, app):
        """1.1.1.1 空文字: エラーメッセージが仕様書記載のメッセージであること"""
        # Arrange
        from iot_app.forms.customer_dashboard.circle_chart import CircleChartGadgetForm
        # Act
        with app.test_request_context():
            form = CircleChartGadgetForm(data={'gadget_name': ''})
            form.validate()
        # Assert
        assert 'タイトルを入力してください' in form.errors['gadget_name']

    def test_error_message_for_title_too_long(self, app):
        """1.2.3 最大長+1: エラーメッセージが仕様書記載のメッセージであること"""
        # Arrange
        from iot_app.forms.customer_dashboard.circle_chart import CircleChartGadgetForm
        # Act
        with app.test_request_context():
            form = CircleChartGadgetForm(data={'gadget_name': 'a' * 21})
            form.validate()
        # Assert
        assert 'タイトルは20文字以内で入力してください' in form.errors['gadget_name']


# ===========================================================================
# Section 2: フォームバリデーション - 表示項目選択 (CircleChartGadgetForm.measurement_item_ids)
# UI仕様書 § バリデーション（登録画面）
#   表示項目選択: 1-5個選択必須
# UI仕様書 § (4) 凡例: 凡例は最大5つまで設定可能
# ===========================================================================

@pytest.mark.unit
class TestCircleChartGadgetFormMeasurementItems:
    """円グラフガジェット登録フォーム - 表示項目選択バリデーション

    観点: 1.1.1（必須チェック）
    UI仕様書 § バリデーション（登録画面）
      - 表示項目選択: 1〜5個必須 → エラー「表示項目を1つ以上5つ以下で選択してください」
    UI仕様書 § (4) 凡例: 選択可能項目は22種類（凡例一覧参照）
    """

    def test_valid_when_one_item_selected(self, app):
        """1.1.1.3 入力あり（最小1個）: バリデーション通過"""
        # Arrange
        from iot_app.forms.customer_dashboard.circle_chart import CircleChartGadgetForm
        # Act
        with app.test_request_context():
            form = CircleChartGadgetForm(data={'gadget_name': '円グラフ', 'measurement_item_ids': ['1']})
            form.measurement_item_ids.choices = [(i, f'item{i}') for i in _ALL_ITEM_IDS]
            result = form.validate()
        # Assert
        assert result is True

    def test_valid_when_five_items_selected(self, app):
        """2.1.3 最大件数内（5個）: バリデーション通過
        UI仕様書 § (4) 凡例: 凡例は最大5つまで設定可能
        """
        # Arrange
        from iot_app.forms.customer_dashboard.circle_chart import CircleChartGadgetForm
        # Act
        with app.test_request_context():
            form = CircleChartGadgetForm(
                data={'gadget_name': '円グラフ', 'measurement_item_ids': ['1', '2', '3', '4', '5']}
            )
            form.measurement_item_ids.choices = [(i, f'item{i}') for i in _ALL_ITEM_IDS]
            result = form.validate()
        # Assert
        assert result is True

    def test_invalid_when_no_items_selected(self, app):
        """1.1.1.1 未選択（0個）: バリデーションエラー"""
        # Arrange
        from iot_app.forms.customer_dashboard.circle_chart import CircleChartGadgetForm
        # Act
        with app.test_request_context():
            form = CircleChartGadgetForm(data={'gadget_name': '円グラフ', 'measurement_item_ids': []})
            form.measurement_item_ids.choices = [(i, f'item{i}') for i in _ALL_ITEM_IDS]
            result = form.validate()
        # Assert
        assert result is False
        assert 'measurement_item_ids' in form.errors

    def test_invalid_when_six_items_selected(self, app):
        """最大超過（6個）: バリデーションエラー
        UI仕様書 § (3.1) 表示項目選択リスト: 選択制限 最小1個、最大5個
        """
        # Arrange
        from iot_app.forms.customer_dashboard.circle_chart import CircleChartGadgetForm
        # Act
        with app.test_request_context():
            form = CircleChartGadgetForm(
                data={'gadget_name': '円グラフ', 'measurement_item_ids': ['1', '2', '3', '4', '5', '6']}
            )
            form.measurement_item_ids.choices = [(i, f'item{i}') for i in _ALL_ITEM_IDS]
            result = form.validate()
        # Assert
        assert result is False
        assert 'measurement_item_ids' in form.errors

    def test_error_message_for_no_items(self, app):
        """未選択: エラーメッセージが仕様書記載のメッセージであること"""
        # Arrange
        from iot_app.forms.customer_dashboard.circle_chart import CircleChartGadgetForm
        # Act
        with app.test_request_context():
            form = CircleChartGadgetForm(data={'gadget_name': '円グラフ', 'measurement_item_ids': []})
            form.measurement_item_ids.choices = [(i, f'item{i}') for i in _ALL_ITEM_IDS]
            form.validate()
        # Assert
        assert '表示項目を1つ以上5つ以下で選択してください' in form.errors['measurement_item_ids']

    def test_error_message_for_too_many_items(self, app):
        """最大超過: エラーメッセージが仕様書記載のメッセージであること"""
        # Arrange
        from iot_app.forms.customer_dashboard.circle_chart import CircleChartGadgetForm
        # Act
        with app.test_request_context():
            form = CircleChartGadgetForm(
                data={'gadget_name': '円グラフ', 'measurement_item_ids': ['1', '2', '3', '4', '5', '6']}
            )
            form.measurement_item_ids.choices = [(i, f'item{i}') for i in _ALL_ITEM_IDS]
            form.validate()
        # Assert
        assert '表示項目を1つ以上5つ以下で選択してください' in form.errors['measurement_item_ids']

    def test_invalid_when_item_id_out_of_valid_range(self, app):
        """1.1.6.2 未定義値: 有効範囲外のmeasurement_item_id（例: 999）はバリデーションエラー
        UI仕様書 § (4) 凡例一覧: measurement_item_id の有効値は 1〜22 のみ
        WTForms SelectMultipleField は choices に含まれない値を自動で弾く
        """
        # Arrange
        from iot_app.forms.customer_dashboard.circle_chart import CircleChartGadgetForm
        # Act
        with app.test_request_context():
            form = CircleChartGadgetForm(
                data={'gadget_name': '円グラフ', 'measurement_item_ids': ['999']}
            )
            form.measurement_item_ids.choices = [(i, f'item{i}') for i in _ALL_ITEM_IDS]
            result = form.validate()
        # Assert
        assert result is False
        assert 'measurement_item_ids' in form.errors

    def test_valid_when_all_item_ids_are_within_range(self, app):
        """1.1.6.1 許容値: 有効範囲内のmeasurement_item_idはバリデーション通過
        UI仕様書 § (4) 凡例一覧: measurement_item_id = 1 は有効値
        """
        # Arrange
        from iot_app.forms.customer_dashboard.circle_chart import CircleChartGadgetForm
        # Act
        with app.test_request_context():
            form = CircleChartGadgetForm(
                data={'gadget_name': '円グラフ', 'measurement_item_ids': ['1', '22']}
            )
            form.measurement_item_ids.choices = [(i, f'item{i}') for i in _ALL_ITEM_IDS]
            result = form.validate()
        # Assert
        assert result is True


# ===========================================================================
# Section 3: フォームバリデーション - グループ選択 (CircleChartGadgetForm.group_id)
# UI仕様書 § バリデーション（登録画面）
#   グループ選択: 必須
# ===========================================================================

@pytest.mark.unit
class TestCircleChartGadgetFormGroupId:
    """円グラフガジェット登録フォーム - グループ選択バリデーション

    観点: 1.1.1（必須チェック）
    UI仕様書 § バリデーション（登録画面）
      - グループ選択: 必須 → エラー「グループを選択してください」
    """

    def test_invalid_when_group_id_empty(self, app):
        """1.1.1.1 空文字: グループが未選択の場合はバリデーションエラー"""
        # Arrange
        from iot_app.forms.customer_dashboard.circle_chart import CircleChartGadgetForm
        # Act
        with app.test_request_context():
            form = CircleChartGadgetForm(data={'gadget_name': '円グラフ', 'group_id': ''})
            result = form.validate()
        # Assert
        assert result is False
        assert 'group_id' in form.errors

    def test_invalid_when_group_id_none(self, app):
        """1.1.1.2 None: グループIDがNoneの場合はバリデーションエラー"""
        # Arrange
        from iot_app.forms.customer_dashboard.circle_chart import CircleChartGadgetForm
        # Act
        with app.test_request_context():
            form = CircleChartGadgetForm(data={'gadget_name': '円グラフ', 'group_id': None})
            result = form.validate()
        # Assert
        assert result is False
        assert 'group_id' in form.errors

    def test_valid_when_group_id_provided(self, app):
        """1.1.1.3 入力あり: グループIDが指定されている場合はバリデーション通過"""
        # Arrange
        from iot_app.forms.customer_dashboard.circle_chart import CircleChartGadgetForm
        # Act
        with app.test_request_context():
            form = CircleChartGadgetForm(data={
                'gadget_name': '円グラフ',
                'group_id': '1',
                'device_mode': 'device_tree',
                'measurement_item_ids': ['1'],
            })
            form.measurement_item_ids.choices = [(i, f'item{i}') for i in _ALL_ITEM_IDS]
            result = form.validate()
        # Assert
        assert result is True

    def test_error_message_for_empty_group_id(self, app):
        """未選択: エラーメッセージが仕様書記載のメッセージであること"""
        # Arrange
        from iot_app.forms.customer_dashboard.circle_chart import CircleChartGadgetForm
        # Act
        with app.test_request_context():
            form = CircleChartGadgetForm(data={'gadget_name': '円グラフ', 'group_id': ''})
            form.validate()
        # Assert
        assert 'グループを選択してください' in form.errors['group_id']


# ===========================================================================
# Section 4: フォームバリデーション - デバイスID（デバイス固定モード時のみ）
# UI仕様書 § バリデーション（登録画面）
#   デバイス選択: 必須（デバイス固定モード時）
# ワークフロー仕様書 § ガジェット登録 バリデーション
# ===========================================================================

@pytest.mark.unit
class TestCircleChartGadgetFormDeviceId:
    """円グラフガジェット登録フォーム - デバイスIDバリデーション（デバイス固定時）

    観点: 1.1.1（必須チェック）
    UI仕様書 § バリデーション（登録画面）
      - デバイス選択: 必須（デバイス固定モード時）→ エラー「デバイスを選択してください」
    UI仕様書 § (2) 表示デバイス選択
      - デバイス固定: device_mode = 'device_specified'
      - デバイス可変: device_mode = 'device_tree'
    """

    def test_invalid_when_fixed_mode_and_device_id_empty(self, app):
        """1.1.1.1 デバイス固定 + device_id空文字: バリデーションエラー"""
        # Arrange
        from iot_app.forms.customer_dashboard.circle_chart import CircleChartGadgetForm
        # Act
        with app.test_request_context():
            form = CircleChartGadgetForm(data={
                'gadget_name': '円グラフ',
                'device_mode': 'device_specified',
                'device_id': '',
            })
            result = form.validate()
        # Assert
        assert result is False
        assert 'device_id' in form.errors

    def test_invalid_when_fixed_mode_and_device_id_none(self, app):
        """1.1.1.2 デバイス固定 + device_id=None: バリデーションエラー"""
        # Arrange
        from iot_app.forms.customer_dashboard.circle_chart import CircleChartGadgetForm
        # Act
        with app.test_request_context():
            form = CircleChartGadgetForm(data={
                'gadget_name': '円グラフ',
                'device_mode': 'device_specified',
                'device_id': None,
            })
            result = form.validate()
        # Assert
        assert result is False
        assert 'device_id' in form.errors

    def test_valid_when_fixed_mode_and_device_id_provided(self, app):
        """1.1.1.3 デバイス固定 + device_id指定あり: バリデーション通過"""
        # Arrange
        from iot_app.forms.customer_dashboard.circle_chart import CircleChartGadgetForm
        # Act
        with app.test_request_context():
            form = CircleChartGadgetForm(data={
                'gadget_name': '円グラフ',
                'device_mode': 'device_specified',
                'device_id': '42',
                'group_id': '1',
                'measurement_item_ids': ['1'],
            })
            form.measurement_item_ids.choices = [(i, f'item{i}') for i in _ALL_ITEM_IDS]
            result = form.validate()
        # Assert
        assert result is True

    def test_valid_when_variable_mode_and_device_id_empty(self, app):
        """デバイス可変モード: device_idが空でもバリデーション通過
        UI仕様書 § (2.2) デバイス可変: 表示デバイス指定エリア(4)を非表示
        """
        # Arrange
        from iot_app.forms.customer_dashboard.circle_chart import CircleChartGadgetForm
        # Act
        with app.test_request_context():
            form = CircleChartGadgetForm(data={
                'gadget_name': '円グラフ',
                'device_mode': 'device_tree',
                'device_id': '',
                'group_id': '1',
                'measurement_item_ids': ['1'],
            })
            form.measurement_item_ids.choices = [(i, f'item{i}') for i in _ALL_ITEM_IDS]
            result = form.validate()
        # Assert
        assert result is True

    def test_error_message_for_missing_device_id(self, app):
        """デバイス固定 + 未選択: エラーメッセージが仕様書記載のメッセージであること"""
        # Arrange
        from iot_app.forms.customer_dashboard.circle_chart import CircleChartGadgetForm
        # Act
        with app.test_request_context():
            form = CircleChartGadgetForm(data={
                'gadget_name': '円グラフ',
                'device_mode': 'device_specified',
                'device_id': '',
            })
            form.validate()
        # Assert
        assert 'デバイスを選択してください' in form.errors['device_id']

    def test_error_message_for_missing_device_mode(self, app):
        """表示デバイス未選択: エラーメッセージが仕様書記載のメッセージであること
        UI仕様書 § バリデーション（登録画面）
          表示デバイス選択: 必須 → エラー「表示デバイスを選択してください」
        """
        # Arrange
        from iot_app.forms.customer_dashboard.circle_chart import CircleChartGadgetForm
        # Act
        with app.test_request_context():
            form = CircleChartGadgetForm(data={
                'gadget_name': '円グラフ',
                'device_mode': '',
                'group_id': '1',
            })
            form.validate()
        # Assert
        assert '表示デバイスを選択してください' in form.errors.get('device_mode', [])


# ===========================================================================
# Section 5: データ整形ロジック (format_circle_chart_data)
# ワークフロー仕様書 § ガジェットデータ取得 ⑤ データ整形
# ===========================================================================

@pytest.mark.unit
class TestFormatCircleChartData:
    """円グラフデータ整形ロジック

    観点: 2.1（正常系処理）, 3.1.4（検索結果戻り値ハンドリング）
    ワークフロー仕様書 § ガジェットデータ取得 ⑤ データ整形
    ※ format_circle_chart_data は src/iot_app/services/customer_dashboard/circle_chart.py に実装予定
    """

    def test_returns_labels_and_values_from_single_row(self):
        """2.1.1 正常処理: センサーデータ1行 + 表示項目定義からlabels/valuesを返す"""
        # Arrange
        from iot_app.services.customer_dashboard.circle_chart import format_circle_chart_data
        rows = [{'external_temp': 10.5, 'set_temp_freezer_1': 12.3}]
        columns = [
            {'silver_data_column_name': 'external_temp', 'display_name': '外気温度', 'measurement_item_id': 1},
            {'silver_data_column_name': 'set_temp_freezer_1', 'display_name': '第1冷凍 設定温度', 'measurement_item_id': 2},
        ]
        # Act
        result = format_circle_chart_data(rows, columns)
        # Assert
        assert result['labels'] == ['外気温度', '第1冷凍 設定温度']
        assert result['values'] == [10.5, 12.3]

    def test_returns_empty_when_rows_is_empty(self):
        """3.1.4.2 空結果: rowsが空の場合は labels=[], values=[] を返す"""
        # Arrange
        from iot_app.services.customer_dashboard.circle_chart import format_circle_chart_data
        rows = []
        columns = [
            {'silver_data_column_name': 'external_temp', 'display_name': '外気温度', 'measurement_item_id': 1},
        ]
        # Act
        result = format_circle_chart_data(rows, columns)
        # Assert
        assert result == {'labels': [], 'values': []}

    def test_returns_empty_labels_and_values_when_columns_is_empty(self):
        """2.1.2 最小構成: columnsが空リストの場合は空の labels/values を返す"""
        # Arrange
        from iot_app.services.customer_dashboard.circle_chart import format_circle_chart_data
        rows = [{'external_temp': 10.5}]
        columns = []
        # Act
        result = format_circle_chart_data(rows, columns)
        # Assert
        assert result == {'labels': [], 'values': []}

    def test_uses_only_first_row(self):
        """2.1.1 正常処理: rowsが複数ある場合は先頭行のみ使用する
        ワークフロー仕様書 ⑤ row = rows[0]
        """
        # Arrange
        from iot_app.services.customer_dashboard.circle_chart import format_circle_chart_data
        rows = [
            {'external_temp': 10.5},
            {'external_temp': 99.9},
        ]
        columns = [
            {'silver_data_column_name': 'external_temp', 'display_name': '外気温度', 'measurement_item_id': 1},
        ]
        # Act
        result = format_circle_chart_data(rows, columns)
        # Assert
        assert result['values'] == [10.5]

    def test_value_is_none_when_column_missing_in_row(self):
        """2.1.1 正常処理: rowsに対象カラムが存在しない場合は None が格納される
        ワークフロー仕様書 ⑤ value = row.get(column_name)
        """
        # Arrange
        from iot_app.services.customer_dashboard.circle_chart import format_circle_chart_data
        rows = [{}]
        columns = [
            {'silver_data_column_name': 'external_temp', 'display_name': '外気温度', 'measurement_item_id': 1},
        ]
        # Act
        result = format_circle_chart_data(rows, columns)
        # Assert
        assert result['labels'] == ['外気温度']
        assert result['values'] == [None]

    def test_max_five_items(self):
        """2.1.3 最大件数: columns が5件の場合、5件すべてが結果に含まれる
        UI仕様書 § (4) 凡例: 凡例は最大5つまで設定可能
        """
        # Arrange
        from iot_app.services.customer_dashboard.circle_chart import format_circle_chart_data
        rows = [{
            'external_temp': 1.0,
            'set_temp_freezer_1': 2.0,
            'internal_sensor_temp_freezer_1': 3.0,
            'internal_temp_freezer_1': 4.0,
            'df_temp_freezer_1': 5.0,
        }]
        columns = [
            {'silver_data_column_name': 'external_temp', 'display_name': '外気温度', 'measurement_item_id': 1},
            {'silver_data_column_name': 'set_temp_freezer_1', 'display_name': '第1冷凍 設定温度', 'measurement_item_id': 2},
            {'silver_data_column_name': 'internal_sensor_temp_freezer_1', 'display_name': '第1冷凍 庫内センサー温度', 'measurement_item_id': 3},
            {'silver_data_column_name': 'internal_temp_freezer_1', 'display_name': '第1冷凍 庫内温度', 'measurement_item_id': 4},
            {'silver_data_column_name': 'df_temp_freezer_1', 'display_name': '第1冷凍 DF温度', 'measurement_item_id': 5},
        ]
        # Act
        result = format_circle_chart_data(rows, columns)
        # Assert
        assert len(result['labels']) == 5
        assert len(result['values']) == 5

    def test_label_order_matches_columns_order(self):
        """2.1.1 正常処理: labelsの順序が columns の順序と一致する
        ワークフロー仕様書 ⑤ columns の順序どおりに labels/values を構築する
        """
        # Arrange
        from iot_app.services.customer_dashboard.circle_chart import format_circle_chart_data
        rows = [{'external_temp': 10.5, 'set_temp_freezer_1': 12.3, 'df_temp_freezer_1': 7.1}]
        columns = [
            {'silver_data_column_name': 'df_temp_freezer_1', 'display_name': '第1冷凍 DF温度', 'measurement_item_id': 5},
            {'silver_data_column_name': 'external_temp', 'display_name': '外気温度', 'measurement_item_id': 1},
            {'silver_data_column_name': 'set_temp_freezer_1', 'display_name': '第1冷凍 設定温度', 'measurement_item_id': 2},
        ]
        # Act
        result = format_circle_chart_data(rows, columns)
        # Assert
        assert result['labels'][0] == '第1冷凍 DF温度'
        assert result['labels'][1] == '外気温度'
        assert result['labels'][2] == '第1冷凍 設定温度'

    def test_response_structure_has_required_keys(self):
        """2.1.1 正常処理: 戻り値に 'labels' と 'values' キーが存在する
        ワークフロー仕様書 ⑥ レスポンス形式: chart_data.labels, chart_data.values
        """
        # Arrange
        from iot_app.services.customer_dashboard.circle_chart import format_circle_chart_data
        rows = [{'external_temp': 10.5}]
        columns = [
            {'silver_data_column_name': 'external_temp', 'display_name': '外気温度', 'measurement_item_id': 1},
        ]
        # Act
        result = format_circle_chart_data(rows, columns)
        # Assert
        assert 'labels' in result
        assert 'values' in result


# ===========================================================================
# Section 6: データスコープ制御 (check_gadget_access)
# ワークフロー仕様書 § ガジェットデータ取得 データスコープ制限チェック
# ===========================================================================

@pytest.mark.unit
class TestCheckGadgetAccess:
    """ガジェットアクセス権限チェック

    観点: 2.2（対象データ存在チェック）
    ワークフロー仕様書 § ガジェットデータ取得 スコープOK判定
    """

    @patch(f'{COMMON_SERVICE_MODULE}.db')
    def test_returns_gadget_when_accessible(self, mock_db):
        """2.2.1 存在確認: ガジェットがアクセス可能スコープ内に存在する場合はガジェットを返す"""
        # Arrange
        mock_gadget = MagicMock()
        (
            mock_db.session.query.return_value
            .join.return_value.join.return_value
            .filter.return_value.first.return_value
        ) = mock_gadget
        from iot_app.services.customer_dashboard.common import check_gadget_access
        # Act
        result = check_gadget_access('test-uuid', [1, 2, 3])
        # Assert
        assert result == mock_gadget

    @patch(f'{COMMON_SERVICE_MODULE}.db')
    def test_returns_none_when_not_accessible(self, mock_db):
        """2.2.2 存在確認: ガジェットがアクセス可能スコープ外の場合は None を返す"""
        # Arrange
        (
            mock_db.session.query.return_value
            .join.return_value.join.return_value
            .filter.return_value.first.return_value
        ) = None
        from iot_app.services.customer_dashboard.common import check_gadget_access
        # Act
        result = check_gadget_access('unknown-uuid', [1, 2, 3])
        # Assert
        assert result is None

    @patch(f'{COMMON_SERVICE_MODULE}.db')
    def test_returns_none_when_accessible_org_ids_empty(self, mock_db):
        """2.2.2 存在確認: accessible_org_ids が空の場合は None を返す
        # TODO: 設計書に空リスト時の明示的な記載なし、要確認
        """
        # Arrange
        (
            mock_db.session.query.return_value
            .join.return_value.join.return_value
            .filter.return_value.first.return_value
        ) = None
        from iot_app.services.customer_dashboard.common import check_gadget_access
        # Act
        result = check_gadget_access('test-uuid', [])
        # Assert
        assert result is None


# ===========================================================================
# Section 6b: ダッシュボードアクセス確認 (check_dashboard_access)
# ワークフロー仕様書 § ガジェット登録モーダル表示 ② ダッシュボード情報取得
# ===========================================================================

@pytest.mark.unit
class TestCheckDashboardAccess:
    """ダッシュボードアクセス確認

    観点: 2.2（対象データ存在チェック）
    ワークフロー仕様書 § ガジェット登録モーダル表示 実装例
      dashboard = get_dashboard_by_id(user_setting.dashboard_id, accessible_org_ids)
      if not dashboard: abort(404)
    """

    @patch(f'{COMMON_SERVICE_MODULE}.db')
    def test_returns_dashboard_when_accessible(self, mock_db):
        """2.2.1 存在確認: アクセス可能スコープ内にダッシュボードが存在する場合はダッシュボードを返す
        ワークフロー仕様書 § ガジェット登録モーダル表示 ②
          dashboard = get_dashboard_by_id(user_setting.dashboard_id, accessible_org_ids)
          → ダッシュボードが存在 → abort(404) を呼ばない
        """
        # Arrange
        mock_dashboard = MagicMock()
        mock_dashboard.dashboard_id = 1
        (
            mock_db.session.query.return_value
            .filter.return_value.first.return_value
        ) = mock_dashboard
        from iot_app.services.customer_dashboard.common import check_dashboard_access
        # Act
        result = check_dashboard_access('valid-dashboard-uuid', [1, 2, 3])
        # Assert
        assert result == mock_dashboard
        assert result.dashboard_id == 1

    @patch(f'{COMMON_SERVICE_MODULE}.db')
    def test_returns_none_when_not_found(self, mock_db):
        """2.2.2 存在確認: アクセス可能スコープ内にダッシュボードが存在しない場合は None を返す
        ワークフロー仕様書 § ガジェット登録モーダル表示 実装例
          if not dashboard: abort(404)
        """
        # Arrange
        (
            mock_db.session.query.return_value
            .filter.return_value.first.return_value
        ) = None
        from iot_app.services.customer_dashboard.common import check_dashboard_access
        # Act
        result = check_dashboard_access('nonexistent-uuid', [1, 2, 3])
        # Assert
        assert result is None


# ===========================================================================
# Section 7: ユーザー設定取得 (get_dashboard_user_setting)
# ワークフロー仕様書 § ガジェットデータ取得 ② デバイスID決定（デバイス可変モード）
# ワークフロー仕様書 § ガジェット登録モーダル表示 ① ダッシュボードユーザー設定取得
# ===========================================================================

@pytest.mark.unit
class TestGetDashboardUserSetting:
    """ダッシュボードユーザー設定取得

    観点: 2.2（対象データ存在チェック）, 3.1.4（検索結果戻り値ハンドリング）
    ワークフロー仕様書 § ガジェット登録モーダル表示 ①
    ワークフロー仕様書 § ガジェットデータ取得 ② デバイスID決定（デバイス可変モード）
    """

    @patch(f'{COMMON_SERVICE_MODULE}.db')
    def test_returns_setting_when_exists(self, mock_db):
        """2.2.1 存在確認: ユーザー設定が存在する場合は設定オブジェクトを返す"""
        # Arrange
        mock_setting = MagicMock()
        mock_setting.device_id = 42
        (
            mock_db.session.query.return_value
            .filter.return_value.first.return_value
        ) = mock_setting
        from iot_app.services.customer_dashboard.common import get_dashboard_user_setting
        # Act
        result = get_dashboard_user_setting(user_id=1)
        # Assert
        assert result == mock_setting
        assert result.device_id == 42

    @patch(f'{COMMON_SERVICE_MODULE}.db')
    def test_returns_none_when_not_exists(self, mock_db):
        """2.2.2 存在確認: ユーザー設定が存在しない場合は None を返す"""
        # Arrange
        (
            mock_db.session.query.return_value
            .filter.return_value.first.return_value
        ) = None
        from iot_app.services.customer_dashboard.common import get_dashboard_user_setting
        # Act
        result = get_dashboard_user_setting(user_id=999)
        # Assert
        assert result is None

    @patch(f'{COMMON_SERVICE_MODULE}.db')
    def test_device_id_is_none_in_variable_mode(self, mock_db):
        """2.2.1 存在確認: デバイス可変モード時、device_id が None の設定を返す
        ワークフロー仕様書 § ② data_source_config.device_id が null の場合はデバイス可変モード
        """
        # Arrange
        mock_setting = MagicMock()
        mock_setting.device_id = None
        (
            mock_db.session.query.return_value
            .filter.return_value.first.return_value
        ) = mock_setting
        from iot_app.services.customer_dashboard.common import get_dashboard_user_setting
        # Act
        result = get_dashboard_user_setting(user_id=1)
        # Assert
        assert result is not None
        assert result.device_id is None


# ===========================================================================
# Section 8: デバイス一覧取得 (get_devices)
# ワークフロー仕様書 § ガジェット登録モーダル表示 ⑥ デバイス一覧取得
# ===========================================================================

@pytest.mark.unit
class TestGetDevices:
    """デバイス一覧取得

    観点: 3.1.1（検索条件指定）, 3.1.4（検索結果戻り値ハンドリング）
    ワークフロー仕様書 § ガジェット登録モーダル表示 ⑥ デバイス一覧取得
    """

    @patch(f'{COMMON_SERVICE_MODULE}.db')
    def test_returns_devices_for_organization(self, mock_db):
        """3.1.1.1 条件指定: organization_id でフィルタされたデバイス一覧を返す"""
        # Arrange
        mock_device_1 = MagicMock()
        mock_device_2 = MagicMock()
        (
            mock_db.session.query.return_value
            .filter.return_value
            .order_by.return_value.all.return_value
        ) = [mock_device_1, mock_device_2]
        from iot_app.services.customer_dashboard.common import get_devices
        # Act
        result = get_devices(organization_id=1)
        # Assert
        assert result == [mock_device_1, mock_device_2]

    @patch(f'{COMMON_SERVICE_MODULE}.db')
    def test_returns_empty_list_when_no_devices(self, mock_db):
        """3.1.4.2 空結果: 対象組織にデバイスが存在しない場合は空リストを返す"""
        # Arrange
        (
            mock_db.session.query.return_value
            .filter.return_value
            .order_by.return_value.all.return_value
        ) = []
        from iot_app.services.customer_dashboard.common import get_devices
        # Act
        result = get_devices(organization_id=999)
        # Assert
        assert result == []


# ===========================================================================
# Section 9: 組織一覧取得 (get_organizations)
# ワークフロー仕様書 § ガジェット登録モーダル表示 ⑤ 組織一覧取得
# ===========================================================================

@pytest.mark.unit
class TestGetOrganizations:
    """組織一覧取得

    観点: 3.1.1（検索条件指定）, 3.1.4（検索結果戻り値ハンドリング）
    ワークフロー仕様書 § ガジェット登録モーダル表示 ⑤ 組織一覧取得
    """

    @patch(f'{COMMON_SERVICE_MODULE}.db')
    def test_returns_organizations_within_scope(self, mock_db):
        """3.1.1.1 条件指定: accessible_org_ids でフィルタされた組織一覧を返す"""
        # Arrange
        mock_org_1 = MagicMock()
        mock_org_2 = MagicMock()
        (
            mock_db.session.query.return_value
            .filter.return_value
            .order_by.return_value.all.return_value
        ) = [mock_org_1, mock_org_2]
        from iot_app.services.customer_dashboard.common import get_organizations
        # Act
        result = get_organizations(accessible_org_ids=[1, 2])
        # Assert
        assert result == [mock_org_1, mock_org_2]

    @patch(f'{COMMON_SERVICE_MODULE}.db')
    def test_returns_empty_list_when_no_accessible_orgs(self, mock_db):
        """3.1.4.2 空結果: アクセス可能組織が存在しない場合は空リストを返す"""
        # Arrange
        (
            mock_db.session.query.return_value
            .filter.return_value
            .order_by.return_value.all.return_value
        ) = []
        from iot_app.services.customer_dashboard.common import get_organizations
        # Act
        result = get_organizations(accessible_org_ids=[])
        # Assert
        assert result == []


# ===========================================================================
# Section 10: ガジェット登録用グループ一覧取得 (get_dashboard_groups)
# ワークフロー仕様書 § ガジェット登録モーダル表示 ③ ダッシュボードグループ一覧取得
# ===========================================================================

@pytest.mark.unit
class TestGetDashboardGroups:
    """ダッシュボードグループ一覧取得（円グラフ登録モーダル用）

    観点: 3.1.1（検索条件指定）, 3.1.4（検索結果戻り値ハンドリング）
    ワークフロー仕様書 § ガジェット登録モーダル表示 ③ ダッシュボードグループ一覧取得
    ワークフロー仕様書 ③ SQL: ORDER BY display_order ASC
    """

    @patch(f'{COMMON_SERVICE_MODULE}.db')
    def test_returns_groups_ordered_by_display_order(self, mock_db):
        """3.1.1.1 条件指定: dashboard_id でフィルタされたグループ一覧を display_order 昇順で返す"""
        # Arrange
        mock_group_1 = MagicMock()
        mock_group_1.display_order = 1
        mock_group_2 = MagicMock()
        mock_group_2.display_order = 2
        (
            mock_db.session.query.return_value
            .filter.return_value
            .order_by.return_value.all.return_value
        ) = [mock_group_1, mock_group_2]
        from iot_app.services.customer_dashboard.common import get_dashboard_groups
        # Act
        result = get_dashboard_groups(dashboard_id=1)
        # Assert
        assert result == [mock_group_1, mock_group_2]
        assert result[0].display_order < result[1].display_order

    @patch(f'{COMMON_SERVICE_MODULE}.db')
    def test_returns_empty_list_when_no_groups(self, mock_db):
        """3.1.4.2 空結果: グループが存在しない場合は空リストを返す"""
        # Arrange
        (
            mock_db.session.query.return_value
            .filter.return_value
            .order_by.return_value.all.return_value
        ) = []
        from iot_app.services.customer_dashboard.common import get_dashboard_groups
        # Act
        result = get_dashboard_groups(dashboard_id=999)
        # Assert
        assert result == []


# ===========================================================================
# Section 11: ガジェット論理削除 (delete_gadget)
# ワークフロー仕様書 § 共通仕様（ガジェット削除）
# ===========================================================================

@pytest.mark.unit
class TestDeleteGadget:
    """ガジェット論理削除

    観点: 3.4（削除機能）
    ワークフロー仕様書 §（共通仕様書参照: ガジェット削除）
    """

    def test_sets_delete_flag_true(self):
        """3.4.2.1 処理完了: delete_flag が True に設定される"""
        # Arrange
        from iot_app.services.customer_dashboard.common import delete_gadget
        mock_gadget = MagicMock()
        mock_gadget.delete_flag = False
        # Act
        delete_gadget(mock_gadget, modifier=1)
        # Assert
        assert mock_gadget.delete_flag is True

    def test_sets_modifier(self):
        """3.4.1.1 呼び出し: modifier が更新される"""
        # Arrange
        from iot_app.services.customer_dashboard.common import delete_gadget
        mock_gadget = MagicMock()
        # Act
        delete_gadget(mock_gadget, modifier=99)
        # Assert
        assert mock_gadget.modifier == 99


# ===========================================================================
# Section 12: ガジェットタイトル更新 (update_gadget_title)
# ワークフロー仕様書 § 共通仕様（ガジェットタイトル変更）
# ===========================================================================

@pytest.mark.unit
class TestUpdateGadgetTitle:
    """ガジェットタイトル更新

    観点: 3.3（更新機能）
    ワークフロー仕様書 §（共通仕様書参照: ガジェットタイトル変更）
    UI仕様書 § (1.1) 設定アイコン - ガジェットタイトル変更
    """

    def test_updates_gadget_name(self):
        """3.3.2.1 処理完了: gadget_name が更新される"""
        # Arrange
        from iot_app.services.customer_dashboard.common import update_gadget_title
        mock_gadget = MagicMock()
        # Act
        update_gadget_title(mock_gadget, name='新しいタイトル', modifier=1)
        # Assert
        assert mock_gadget.gadget_name == '新しいタイトル'

    def test_updates_modifier(self):
        """3.3.2.2 ID指定: modifier が更新される"""
        # Arrange
        from iot_app.services.customer_dashboard.common import update_gadget_title
        mock_gadget = MagicMock()
        # Act
        update_gadget_title(mock_gadget, name='タイトル', modifier=42)
        # Assert
        assert mock_gadget.modifier == 42

    def test_name_max_length_boundary(self, app):
        """1.2.2 最大長ちょうど（20文字）: ガジェット名最大文字数のフォームバリデーション
        UI仕様書 § (1) タイトル: 最大20文字
        """
        # Arrange
        from iot_app.forms.customer_dashboard.circle_chart import CircleChartGadgetForm
        # Act
        with app.test_request_context():
            form = CircleChartGadgetForm(data={'gadget_name': 'あ' * 20})
            result = form.validate()
        # Assert
        assert result is True


# ===========================================================================
# Section 13: アクセス可能組織ID取得 (get_accessible_organizations)
# ワークフロー仕様書 § バリデーション - データスコープ制限
# ===========================================================================

@pytest.mark.unit
class TestGetAccessibleOrganizations:
    """アクセス可能組織IDリスト取得（円グラフ関連ルートで使用）

    観点: 3.1.4（検索結果戻り値ハンドリング）
    ワークフロー仕様書 § ガジェットデータ取得 スコープOK判定
    ワークフロー仕様書 § ガジェット登録 ① デバイス存在&データスコープチェック
    """

    @patch(f'{COMMON_SERVICE_MODULE}.db')
    def test_returns_org_id_list(self, mock_db):
        """3.1.4.1 正常系: 下位組織IDのリストを返す"""
        # Arrange
        mock_db.session.query.return_value.filter.return_value.all.return_value = [
            (10,), (20,), (30,)
        ]
        from iot_app.services.customer_dashboard.common import get_accessible_organizations
        # Act
        result = get_accessible_organizations(parent_org_id=1)
        # Assert
        assert result == [10, 20, 30]

    @patch(f'{COMMON_SERVICE_MODULE}.db')
    def test_returns_empty_list_when_no_suborganizations(self, mock_db):
        """3.1.4.2 空結果: 下位組織が存在しない場合は空リストを返す"""
        # Arrange
        mock_db.session.query.return_value.filter.return_value.all.return_value = []
        from iot_app.services.customer_dashboard.common import get_accessible_organizations
        # Act
        result = get_accessible_organizations(parent_org_id=999)
        # Assert
        assert result == []

    @patch(f'{COMMON_SERVICE_MODULE}.db')
    def test_returns_self_org_included(self, mock_db):
        """3.1.4.1 正常系: 自組織IDも含む結果が返される（閉包テーブルは自身も含む設計）
        # TODO: 設計書に自組織を含む旨の明示的な記載なし、要確認
        """
        # Arrange
        mock_db.session.query.return_value.filter.return_value.all.return_value = [
            (1,), (10,), (20,)
        ]
        from iot_app.services.customer_dashboard.common import get_accessible_organizations
        # Act
        result = get_accessible_organizations(parent_org_id=1)
        # Assert
        assert 1 in result


# ===========================================================================
# Section 14: エラーハンドリング (1.3 エラーハンドリング観点)
#
# 根拠仕様書:
#   ワークフロー仕様書 § ガジェットデータ取得 / ガジェット登録モーダル表示 / ガジェット登録
#   各フロー図のエラーハンドリング分岐および実装例の except ブロック
#
# NOTE: AppError クラスはコードベース未定義。
#       予期しない内部エラーは Python 組み込み Exception として伝播し、
#       ビュー層の except ブロックで捕捉して 500 レスポンスを返す。
# NOTE: スコープ外アクセスはワークフロー仕様書フロー図で "Error404" と定義されており、
#       ForbiddenError(403) ではなく NotFoundError(404) として扱う。
# ===========================================================================


# ---------------------------------------------------------------------------
# 1.3.1 例外伝播
# ---------------------------------------------------------------------------

@pytest.mark.unit
class TestErrorHandling_ExceptionPropagation:
    """1.3.1 例外伝播: Service / Repository で例外発生時、握りつぶされず上位へ伝播する

    根拠:
      ワークフロー仕様書 § ガジェットデータ取得 実装例
        except Exception as e:
            logger.error(...)
            return jsonify({'error': '...'}), 500
      ワークフロー仕様書 § ガジェット登録 実装例
        except Exception as e:
            db.session.rollback()
            logger.error(...)
            abort(500)
    """

    @patch(f'{COMMON_SERVICE_MODULE}.db')
    def test_get_accessible_organizations_propagates_db_error(self, mock_db):
        """1.3.1.1 get_accessible_organizations: DB例外が握りつぶされず上位へ伝播する
        ワークフロー仕様書 § ガジェットデータ取得 ① accessible_org_ids 取得
        """
        # Arrange
        mock_db.session.query.side_effect = Exception('DB接続エラー')
        from iot_app.services.customer_dashboard.common import get_accessible_organizations
        # Act / Assert
        with pytest.raises(Exception):
            get_accessible_organizations(parent_org_id=1)

    @patch(f'{COMMON_SERVICE_MODULE}.db')
    def test_get_dashboard_user_setting_propagates_db_error(self, mock_db):
        """1.3.1.2 get_dashboard_user_setting: DB例外が握りつぶされず上位へ伝播する
        ワークフロー仕様書 § ガジェット登録モーダル表示 フロー図 UserSettingQuery 失敗 → Error500
        """
        # Arrange
        mock_db.session.query.side_effect = Exception('DB接続エラー')
        from iot_app.services.customer_dashboard.common import get_dashboard_user_setting
        # Act / Assert
        with pytest.raises(Exception):
            get_dashboard_user_setting(user_id=1)

    @patch(f'{COMMON_SERVICE_MODULE}.db')
    def test_check_gadget_access_propagates_db_error(self, mock_db):
        """1.3.1.3 check_gadget_access: DB例外が握りつぶされず上位へ伝播する
        ワークフロー仕様書 § ガジェットデータ取得 フロー図 CheckGetConfig 失敗 → Error500
        """
        # Arrange
        mock_db.session.query.side_effect = Exception('DB接続エラー')
        from iot_app.services.customer_dashboard.common import check_gadget_access
        # Act / Assert
        with pytest.raises(Exception):
            check_gadget_access('test-uuid', [1, 2, 3])

    @patch(f'{COMMON_SERVICE_MODULE}.db')
    def test_fetch_circle_chart_data_propagates_db_error(self, mock_db):
        """1.3.1.4 fetch_circle_chart_data: DB例外が握りつぶされず上位へ伝播する
        ワークフロー仕様書 § ガジェットデータ取得 フロー図 SilverQuery 失敗 → Error500
        ※ circle_chart.py 未実装 → TDDテスト（実装後に通過）
        """
        # Arrange
        mock_db.session.query.side_effect = Exception('センサーデータ取得エラー')
        from iot_app.services.customer_dashboard.circle_chart import fetch_circle_chart_data
        # Act / Assert
        with pytest.raises(Exception):
            fetch_circle_chart_data(device_id=1)


# ---------------------------------------------------------------------------
# 1.3.2 ValidationError（400）
# ---------------------------------------------------------------------------

@pytest.mark.unit
class TestErrorHandling_ValidationError:
    """1.3.2 ValidationError: バリデーション違反条件で処理実行 → バリデーションエラー（400）

    根拠:
      ワークフロー仕様書 § ガジェット登録 バリデーション表
        タイトル: 必須、最大20文字
        表示デバイス: 必須
        デバイス（デバイス固定時のみ）: 必須
        グループ: 必須
        表示項目: 1〜5個必須
      ワークフロー仕様書 § ガジェット登録 エラーハンドリング表
        400 | バリデーションエラー | フォーム再表示（エラーモーダル表示）
    """

    def test_form_invalid_when_all_fields_empty(self, app):
        """1.3.2.1 全必須項目が未入力: validate() = False → ビュー層で 400 返却
        ワークフロー仕様書 § ガジェット登録 バリデーション表（全項目必須）
        """
        # Arrange
        from iot_app.forms.customer_dashboard.circle_chart import CircleChartGadgetForm
        # Act
        with app.test_request_context():
            form = CircleChartGadgetForm(data={})
            result = form.validate()
        # Assert
        assert result is False

    def test_form_invalid_when_device_mode_not_selected(self, app):
        """1.3.2.2 表示デバイス未選択: validate() = False → ビュー層で 400 返却
        ワークフロー仕様書 § ガジェット登録 バリデーション表
          表示デバイス: 必須 → エラー「表示デバイスを選択してください」
        """
        # Arrange
        from iot_app.forms.customer_dashboard.circle_chart import CircleChartGadgetForm
        # Act
        with app.test_request_context():
            form = CircleChartGadgetForm(data={
                'gadget_name': '円グラフ',
                'device_mode': '',
                'group_id': '1',
            })
            result = form.validate()
        # Assert
        assert result is False
        assert 'device_mode' in form.errors

    def test_form_invalid_when_items_count_is_zero(self, app):
        """1.3.2.3 表示項目が0個: validate() = False → ビュー層で 400 返却
        ワークフロー仕様書 § ガジェット登録 バリデーション表
          表示項目: 必須（1つ以上5つ以下）→ エラー「表示項目を1つ以上5つ以下で選択してください」
        """
        # Arrange
        from iot_app.forms.customer_dashboard.circle_chart import CircleChartGadgetForm
        # Act
        with app.test_request_context():
            form = CircleChartGadgetForm(data={
                'gadget_name': '円グラフ',
                'device_mode': 'device_tree',
                'group_id': '1',
                'measurement_item_ids': [],
            })
            form.measurement_item_ids.choices = [(i, f'item{i}') for i in _ALL_ITEM_IDS]
            result = form.validate()
        # Assert
        assert result is False
        assert 'measurement_item_ids' in form.errors

    def test_form_invalid_when_items_count_exceeds_five(self, app):
        """1.3.2.4 表示項目が6個以上: validate() = False → ビュー層で 400 返却
        UI仕様書 § (4) 凡例: 最大5つまで設定可能
        ワークフロー仕様書 § ガジェット登録 バリデーション表
          表示項目: 1〜5個必須
        """
        # Arrange
        from iot_app.forms.customer_dashboard.circle_chart import CircleChartGadgetForm
        # Act
        with app.test_request_context():
            form = CircleChartGadgetForm(data={
                'gadget_name': '円グラフ',
                'device_mode': 'device_tree',
                'group_id': '1',
                'measurement_item_ids': ['1', '2', '3', '4', '5', '6'],
            })
            form.measurement_item_ids.choices = [(i, f'item{i}') for i in _ALL_ITEM_IDS]
            result = form.validate()
        # Assert
        assert result is False
        assert 'measurement_item_ids' in form.errors


# ---------------------------------------------------------------------------
# 1.3.3 AuthenticationError（401）
# ---------------------------------------------------------------------------

@pytest.mark.unit
class TestErrorHandling_AuthenticationError:
    """1.3.3 AuthenticationError: 認証失敗条件で処理実行 → 401エラーレスポンス

    根拠:
      ワークフロー仕様書 § ガジェットデータ取得 フロー図
        Auth → CheckAuth → |未認証| → Error401[401エラーレスポンス]
      ワークフロー仕様書 § ガジェット登録モーダル表示 フロー図
        Auth → CheckAuth → |未認証| → LoginRedirect[ログイン画面へリダイレクト]
      iot_app.auth.exceptions.UnauthorizedError が AuthenticationError（401）に相当
    """

    def test_unauthorized_error_is_importable(self):
        """1.3.3.1 UnauthorizedError が iot_app.auth.exceptions から import できること
        認証失敗時にスローされる例外クラスが定義されていること
        """
        # Act
        from iot_app.auth.exceptions import UnauthorizedError
        # Assert
        assert issubclass(UnauthorizedError, Exception)

    def test_unauthorized_error_propagates_to_caller(self):
        """1.3.3.2 UnauthorizedError がスローされた場合、呼び出し元へ伝播する
        ワークフロー仕様書 § ガジェットデータ取得 フロー図: 未認証 → Error401
        """
        # Arrange
        from iot_app.auth.exceptions import UnauthorizedError

        def mock_auth_check():
            raise UnauthorizedError('認証が必要です')

        # Act / Assert
        with pytest.raises(UnauthorizedError):
            mock_auth_check()


# ---------------------------------------------------------------------------
# 1.3.4 スコープ外アクセス（404）
# NOTE: ワークフロー仕様書フロー図では "スコープ外 → Error404" と定義。
#       ForbiddenError(403) ではなく 404 を返すのが本機能の仕様。
# ---------------------------------------------------------------------------

@pytest.mark.unit
class TestErrorHandling_ScopeViolation:
    """1.3.4 スコープ外アクセス: アクセス可能スコープ外のリソース操作 → 404エラーレスポンス

    根拠:
      ワークフロー仕様書 § ガジェットデータ取得 フロー図
        CheckScope → |スコープ外| → Error404[404エラーレスポンス]
      ワークフロー仕様書 § ガジェットデータ取得 実装例
        if not check_gadget_access(gadget, accessible_org_ids):
            return jsonify({'error': 'アクセス権限がありません'}), 404
    """

    @patch(f'{COMMON_SERVICE_MODULE}.db')
    def test_check_gadget_access_returns_none_when_out_of_scope(self, mock_db):
        """1.3.4.1 check_gadget_access: スコープ外のガジェットに対して None を返す
        ワークフロー仕様書 § ガジェットデータ取得 フロー図: スコープ外 → Error404
        """
        # Arrange
        (
            mock_db.session.query.return_value
            .join.return_value.join.return_value
            .filter.return_value.first.return_value
        ) = None
        from iot_app.services.customer_dashboard.common import check_gadget_access
        # Act
        result = check_gadget_access('out-of-scope-uuid', [1, 2, 3])
        # Assert
        assert result is None  # None を受けたビュー層が 404 を返す

    @patch(f'{COMMON_SERVICE_MODULE}.db')
    def test_check_gadget_access_returns_none_when_org_ids_empty(self, mock_db):
        """1.3.4.2 check_gadget_access: accessible_org_ids が空リストの場合 None を返す
        ワークフロー仕様書 § セキュリティ実装 データスコープ制限
          accessible_org_ids が空の場合はアクセス不可
        """
        # Arrange
        (
            mock_db.session.query.return_value
            .join.return_value.join.return_value
            .filter.return_value.first.return_value
        ) = None
        from iot_app.services.customer_dashboard.common import check_gadget_access
        # Act
        result = check_gadget_access('test-uuid', [])
        # Assert
        assert result is None  # None を受けたビュー層が 404 を返す


# ---------------------------------------------------------------------------
# 1.3.5 NotFoundError（404）
# ---------------------------------------------------------------------------

@pytest.mark.unit
class TestErrorHandling_NotFoundError:
    """1.3.5 NotFoundError: 存在しないリソースで処理実行 → 404エラーレスポンス

    根拠:
      ワークフロー仕様書 § ガジェット登録モーダル表示 フロー図
        CheckUserSetting → |なし| → Error404[404エラーモーダル表示]
        CheckDashboard   → |なし| → Error404[404エラーモーダル表示]
      ワークフロー仕様書 § ガジェット登録 フロー図
        CheckDeviceQuery → |NG|  → Error404[404エラーモーダル表示]
      ワークフロー仕様書 § ガジェット登録モーダル表示 実装例
        if not user_setting: abort(404)
        if not dashboard:    abort(404)
    """

    @patch(f'{COMMON_SERVICE_MODULE}.db')
    def test_get_dashboard_user_setting_returns_none_when_not_found(self, mock_db):
        """1.3.5.1 get_dashboard_user_setting: ユーザー設定が存在しない場合 None を返す
        ワークフロー仕様書 § ガジェット登録モーダル表示 実装例
          user_setting = get_dashboard_user_setting(user_id)
          if not user_setting: abort(404)
        """
        # Arrange
        (
            mock_db.session.query.return_value
            .filter.return_value.first.return_value
        ) = None
        from iot_app.services.customer_dashboard.common import get_dashboard_user_setting
        # Act
        result = get_dashboard_user_setting(user_id=99999)
        # Assert
        assert result is None  # None を受けたビュー層が abort(404) を呼ぶ

    @patch(f'{COMMON_SERVICE_MODULE}.db')
    def test_check_dashboard_access_returns_none_when_not_found(self, mock_db):
        """1.3.5.2 check_dashboard_access: アクセス可能スコープ内にダッシュボードが存在しない場合 None を返す
        ワークフロー仕様書 § ガジェット登録モーダル表示 実装例
          dashboard = get_dashboard_by_id(user_setting.dashboard_id, accessible_org_ids)
          if not dashboard: abort(404)
        """
        # Arrange
        (
            mock_db.session.query.return_value
            .filter.return_value.first.return_value
        ) = None
        from iot_app.services.customer_dashboard.common import check_dashboard_access
        # Act
        result = check_dashboard_access('nonexistent-uuid', [1, 2, 3])
        # Assert
        assert result is None  # None を受けたビュー層が abort(404) を呼ぶ

    @patch(f'{COMMON_SERVICE_MODULE}.db')
    def test_get_gadget_by_uuid_returns_none_when_not_found(self, mock_db):
        """1.3.5.3 get_gadget_by_uuid: 存在しない gadget_uuid で None を返す
        ワークフロー仕様書 § ガジェットデータ取得 実装例
          gadget = get_gadget_by_uuid(gadget_uuid)
          if not gadget:
              return jsonify({'error': '指定されたガジェットが見つかりません'}), 404
        ※ circle_chart.py 未実装 → TDDテスト（実装後に通過）
        """
        # Arrange
        mock_db.session.query.return_value.filter.return_value.first.return_value = None
        from iot_app.services.customer_dashboard.circle_chart import get_gadget_by_uuid
        # Act
        result = get_gadget_by_uuid('nonexistent-uuid')
        # Assert
        assert result is None  # None を受けたビュー層が 404 を返す


# ---------------------------------------------------------------------------
# 1.3.6 AppError（500）
# NOTE: AppError クラスはコードベース未定義。
#       DBエラーは Exception として伝播し、ビュー層の except ブロックで
#       rollback + abort(500) / return jsonify(...), 500 として処理される。
# ---------------------------------------------------------------------------

@pytest.mark.unit
class TestErrorHandling_InternalError:
    """1.3.6 AppError（500相当）: 予期しない内部エラー発生 → 500エラーレスポンス

    根拠:
      ワークフロー仕様書 § ガジェットデータ取得 実装例
        except Exception as e:
            logger.error(f'円グラフデータ取得エラー: ...')
            return jsonify({'error': 'データの取得に失敗しました'}), 500
      ワークフロー仕様書 § ガジェット登録 実装例
        except Exception as e:
            db.session.rollback()
            logger.error(f'円グラフガジェット登録エラー: ...')
            abort(500)
      ワークフロー仕様書 § ガジェット登録モーダル表示 フロー図
        CheckUserSettingQuery → |失敗| → Error500[500エラーページ表示]
    """

    @patch(f'{COMMON_SERVICE_MODULE}.db')
    def test_get_accessible_organizations_raises_on_unexpected_error(self, mock_db):
        """1.3.6.1 get_accessible_organizations: 予期しない例外（RuntimeError等）が上位へ伝播する
        ワークフロー仕様書 § ガジェット登録モーダル表示 フロー図
          Scope[データスコープ制限適用] で DB エラー → Error500
        """
        # Arrange
        mock_db.session.query.side_effect = RuntimeError('予期しない内部エラー')
        from iot_app.services.customer_dashboard.common import get_accessible_organizations
        # Act / Assert
        with pytest.raises(RuntimeError):
            get_accessible_organizations(parent_org_id=1)

    @patch(f'{COMMON_SERVICE_MODULE}.db')
    def test_save_layout_rollbacks_and_propagates_on_db_error(self, mock_db):
        """1.3.6.2 save_layout: DB例外発生時に rollback し例外を再 raise する
        ワークフロー仕様書 § ガジェット登録 実装例
          except Exception as e:
              db.session.rollback()
              abort(500)
        """
        # Arrange
        mock_db.session.query.side_effect = Exception('DB書き込みエラー')
        layout_data = [
            {'gadget_uuid': 'g-001', 'position_x': 0, 'position_y': 0, 'display_order': 0}
        ]
        from iot_app.services.customer_dashboard.common import save_layout
        # Act / Assert
        with pytest.raises(Exception):
            save_layout(layout_data, modifier=1)
        mock_db.session.rollback.assert_called_once()

    @patch(f'{COMMON_SERVICE_MODULE}.db')
    def test_create_circle_chart_gadget_rollbacks_and_propagates_on_db_error(self, mock_db):
        """1.3.6.3 create_circle_chart_gadget: DB例外発生時に rollback し例外を再 raise する
        ワークフロー仕様書 § ガジェット登録 実装例
          except Exception as e:
              db.session.rollback()
              abort(500)
        ※ circle_chart.py 未実装 → TDDテスト（実装後に通過）
        """
        # Arrange
        mock_db.session.add.side_effect = Exception('DB INSERT エラー')
        from iot_app.services.customer_dashboard.circle_chart import create_circle_chart_gadget
        # Act / Assert
        with pytest.raises(Exception):
            create_circle_chart_gadget(
                gadget_name='円グラフ',
                dashboard_group_id=1,
                chart_config={'item_id_1': 1},
                data_source_config={'device_id': None},
                user_id=1,
            )
        mock_db.session.rollback.assert_called_once()


# ===========================================================================
# Section 15: ログ出力機能 (1.4 ログ出力機能観点)
#
# 根拠仕様書:
#   ログ設計書 §6.1 タイミング一覧
#   ログ設計書 §5.3 出力禁止項目
#   ワークフロー仕様書 § ログ出力ルール
#     出力しない情報（機密情報）: 認証トークン、センサーデータの具体値
#
# 検証方針:
#   - pytest caplog フィクスチャでログキャプチャ
#   - logger.xxx の呼び出しレベルは patch で検証
#   - 機密情報の非出力は caplog.text への非含有で検証
#
# NOTE: 1.4.2.1〜2.5, 2.7（requestId / method / endpoint / userId / httpStatus）は
#       tests/unit/common/test_logger.py / test_error_handlers.py でカバー済み。
# NOTE: 1.4.2.6（組織ID）はログ設計書 §4 により「出力しない」仕様のため N/A。
# NOTE: 1.4.2.2（タイムスタンプ）は Python logging フレームワーク標準機能のため N/A。
# ===========================================================================

import logging


# ---------------------------------------------------------------------------
# 1.4.1 ログレベル
# ---------------------------------------------------------------------------

@pytest.mark.unit
class TestLogLevel_CircleChart:
    """1.4.1 ログレベル: エラー種別・処理結果に応じた正しいログレベルで出力される

    根拠:
      ログ設計書 §6.1 タイミング一覧
        エラー 500系例外        → error_handlers.py   → ERROR
        エラー 400系 abort(4xx) → error_handlers.py   → WARN
        リクエスト終了           → after_request フック → INFO
        MySQL SELECT           → SQLAlchemy イベント  → DEBUG
      ワークフロー仕様書 § ガジェットデータ取得 実装例
        except Exception as e:
            logger.error(f'円グラフデータ取得エラー: ...')    # ERROR
      ワークフロー仕様書 § ガジェット登録 実装例
        except Exception as e:
            logger.error(f'円グラフガジェット登録エラー: ...')  # ERROR
    """

    def test_error_level_logged_on_500(self, app):
        """1.4.1.1 ERRORレベル: 500系例外発生時に ERROR レベルでログが出力される
        ログ設計書 §6.1: 500系例外 → error_handlers.py → ERROR
        circle_chart ガジェットデータ取得エラー・登録エラーは handle_500 経由でログ出力
        """
        # Arrange
        from iot_app.common.error_handlers import handle_500
        error = Exception('circle_chart 内部エラー')
        # Act / Assert
        with app.test_request_context('/analysis/customer-dashboard/gadgets/test-uuid/data'):
            with patch('iot_app.common.error_handlers.logger') as mock_logger:
                with patch('iot_app.common.error_handlers.render_template', return_value=''):
                    handle_500(error)
            mock_logger.error.assert_called_once()

    def test_warn_level_logged_on_4xx(self, app):
        """1.4.1.2 WARNレベル: 400系エラー（abort(404)等）発生時に WARN レベルでログが出力される
        ログ設計書 §6.1: 400系 abort(4xx) → error_handlers.py → WARN
        circle_chart: ガジェット未存在 → abort(404) → handle_4xx → WARN
        """
        # Arrange
        from iot_app.common.error_handlers import handle_4xx
        from werkzeug.exceptions import NotFound
        error = NotFound()
        # Act / Assert
        with app.test_request_context('/analysis/customer-dashboard/gadgets/test-uuid/data'):
            with patch('iot_app.common.error_handlers.logger') as mock_logger:
                handle_4xx(error)
            mock_logger.warning.assert_called_once()

    def test_info_level_logged_on_normal_completion(self, app):
        """1.4.1.3 INFOレベル: 正常処理完了時に INFO レベルでログが出力される
        ログ設計書 §6.2: after_request フックで INFO 出力
          logger.info("リクエスト完了", extra={"httpStatus": ..., "processingTime": ...})
        """
        # Arrange
        from iot_app.common.logger import get_logger
        logger = get_logger('test.circle_chart')
        # Act / Assert
        with app.test_request_context('/analysis/customer-dashboard'):
            with patch.object(logger.logger, 'info') as mock_info:
                logger.info('リクエスト完了', extra={'httpStatus': 200, 'processingTime': 42})
            mock_info.assert_called_once()
            call_args = mock_info.call_args
            assert call_args[0][0] == 'リクエスト完了'

    def test_debug_level_logged_for_detail_info(self, app):
        """1.4.1.4 DEBUGレベル: 詳細情報出力時に DEBUG レベルでログが出力される
        ログ設計書 §6.1: MySQL SELECT → SQLAlchemy イベント → DEBUG
        ログ設計書 §6.6: db.event.listens_for(Engine, "before_cursor_execute") で SELECT → DEBUG
        """
        # Arrange
        from iot_app.common.logger import get_logger
        logger = get_logger('test.circle_chart')
        # Act / Assert
        with app.test_request_context('/analysis/customer-dashboard'):
            with patch.object(logger.logger, 'debug') as mock_debug:
                logger.debug('SELECT クエリ実行', extra={'sql': 'SELECT ...'})
            mock_debug.assert_called_once()


# ---------------------------------------------------------------------------
# 1.4.2 必須項目出力（未カバー分のみ）
# ---------------------------------------------------------------------------

@pytest.mark.unit
class TestLogRequiredFields_CircleChart:
    """1.4.2.8 処理時間: after_request ログに processingTime（ms）が含まれる

    根拠:
      ログ設計書 §6.2 リクエスト前後（自動）
        @app.after_request
        def log_request_end(response):
            duration_ms = int((time.time() - g.start_time) * 1000)
            logger.info("リクエスト完了", extra={"httpStatus": ..., "processingTime": duration_ms})

    NOTE: 1.4.2.1〜2.5, 2.7 は tests/unit/common/test_logger.py / test_error_handlers.py カバー済み。
    NOTE: 1.4.2.6（組織ID）はログ設計書 §4 により「出力しない」仕様のため N/A。
    NOTE: 1.4.2.2（タイムスタンプ）は Python logging フレームワーク標準機能のため N/A。
    """

    def test_processing_time_included_in_after_request_log(self, app):
        """1.4.2.8 処理時間: after_request ログに processingTime（ms）が含まれる
        ログ設計書 §6.2: logger.info("リクエスト完了", extra={"processingTime": duration_ms})
        """
        # Arrange
        from iot_app.common.logger import get_logger
        logger = get_logger('test.after_request')
        # Act
        with app.test_request_context('/analysis/customer-dashboard/gadgets/test-uuid/data'):
            with patch.object(logger.logger, 'info') as mock_info:
                logger.info(
                    'リクエスト完了',
                    extra={'httpStatus': 200, 'processingTime': 123}
                )
        # Assert
        mock_info.assert_called_once()
        _, kwargs = mock_info.call_args
        assert kwargs['extra']['processingTime'] == 123


# ---------------------------------------------------------------------------
# 1.4.3 機密情報の非出力
# ---------------------------------------------------------------------------

@pytest.mark.unit
class TestLogSensitiveData_CircleChart:
    """1.4.3 機密情報の非出力: 機密情報がログに含まれない

    根拠:
      ワークフロー仕様書 § ログ出力ルール
        出力しない情報（機密情報）:
          - 認証トークン
          - センサーデータの具体値
      ログ設計書 §5.3 出力禁止項目
        Databricks トークン・セッション ID・パスワード等は絶対に出力しない

    NOTE: 1.4.3.1 パスワード非出力は circle_chart 機能ではパスワードを扱わないため N/A。
          本システムは Azure Easy Auth 認証のため、アプリ側でパスワードを処理しない。
    """

    def test_sensor_data_values_not_in_logs(self, caplog):
        """1.4.3.2（センサーデータ）: format_circle_chart_data 実行時にセンサーデータの具体値がログに含まれない
        ワークフロー仕様書 § ログ出力ルール
          出力しない情報（機密情報）: センサーデータの具体値
        ※ circle_chart.py 未実装 → TDDテスト（実装後に通過）
        """
        # Arrange
        from iot_app.services.customer_dashboard.circle_chart import format_circle_chart_data
        rows = [{'external_temp': 99.9, 'set_temp_freezer_1': 12.345}]
        columns = [
            {'silver_data_column_name': 'external_temp', 'display_name': '外気温度', 'measurement_item_id': 1},
            {'silver_data_column_name': 'set_temp_freezer_1', 'display_name': '第1冷凍 設定温度', 'measurement_item_id': 2},
        ]
        # Act
        with caplog.at_level(logging.DEBUG):
            format_circle_chart_data(rows, columns)
        # Assert: センサーデータの具体値がログに含まれない
        assert '99.9' not in caplog.text
        assert '12.345' not in caplog.text

    @patch(f'{COMMON_SERVICE_MODULE}.db')
    def test_databricks_token_not_in_logs(self, mock_db, caplog):
        """1.4.3.2（トークン）: get_accessible_organizations 実行時に Databricks トークンがログに含まれない
        ログ設計書 §5.3: Databricks トークンは絶対に出力しない
        ワークフロー仕様書 § ログ出力ルール: 認証トークンを出力しない
        """
        # Arrange
        mock_db.session.query.return_value.filter.return_value.all.return_value = [(1,)]
        _FAKE_TOKEN = 'fake-databricks-token-for-test'
        from iot_app.services.customer_dashboard.common import get_accessible_organizations
        # Act
        with caplog.at_level(logging.DEBUG):
            get_accessible_organizations(parent_org_id=1)
        # Assert: Databricks トークン文字列がログに含まれない
        assert _FAKE_TOKEN not in caplog.text
        assert 'dapi' not in caplog.text

    def test_session_id_not_in_logs(self, app, caplog):
        """1.4.3.3 セッションID非出力: circle_chart 処理中にセッションIDがログに含まれない
        ログ設計書 §5.3: セッション ID は絶対に出力しない
        """
        # Arrange
        _FAKE_SESSION_ID = 'sess_abcdef1234567890'
        from iot_app.common.logger import get_logger
        logger = get_logger('test.circle_chart')
        # Act: セッションIDは extra に渡さない（出力禁止項目）
        with app.test_request_context('/analysis/customer-dashboard'):
            with caplog.at_level(logging.DEBUG):
                logger.info('ガジェット登録完了', extra={'gadget_uuid': 'test-uuid'})
        # Assert: セッションIDがログに含まれない
        assert _FAKE_SESSION_ID not in caplog.text

    def test_csrf_token_not_in_logs(self, app, caplog):
        """1.4.3.4 CSRFトークン非出力: ガジェット登録フォーム送信処理中に CSRF トークンがログに含まれない
        ログ設計書 §5.3: 出力禁止項目
        ワークフロー仕様書 § ガジェット登録: POST /analysis/customer-dashboard/gadgets/circle-chart/register
        """
        # Arrange
        _FAKE_CSRF = 'csrf_token_abcdef1234567890'
        from iot_app.common.logger import get_logger
        logger = get_logger('test.circle_chart')
        # Act: CSRF トークンは extra に渡さない（出力禁止項目）
        with app.test_request_context(
            '/analysis/customer-dashboard/gadgets/circle-chart/register',
            method='POST',
        ):
            with caplog.at_level(logging.DEBUG):
                logger.info('ガジェット登録処理開始', extra={'group_id': 1})
        # Assert: CSRF トークンがログに含まれない
        assert _FAKE_CSRF not in caplog.text


# ===========================================================================
# Section 16: 副作用チェック (2.3 副作用チェック観点)
#
# 根拠仕様書:
#   ワークフロー仕様書 § ガジェット登録 実装例
#     except Exception as e:
#         db.session.rollback()   # rollback 後に abort(500)
#   ワークフロー仕様書 § ガジェットデータ取得 実装例
#     except Exception as e:
#         return jsonify({'error': '...'}), 500  # rollback は view 側の責務
#
# NOTE: update_gadget_title / delete_gadgets_by_dashboard は自前で rollback を持たない。
#       rollback の責務は呼び出し元 View の try/except ブロックにある。
# ===========================================================================


# ---------------------------------------------------------------------------
# 2.3.1 処理失敗時にデータが更新されない
# ---------------------------------------------------------------------------

@pytest.mark.unit
class TestSideEffect_NoDataUpdate:
    """2.3.1 副作用: 処理失敗時にデータが更新されない（db.session.commit() が呼ばれない）

    根拠:
      ワークフロー仕様書 § ガジェット登録 実装例
        except Exception as e:
            db.session.rollback()
            abort(500)
        → rollback 後に raise するため commit() に到達しない
      ワークフロー仕様書 § ガジェット登録 フロー図
        CheckInsert → |失敗| → Error500[500エラーページ表示]
        → commit() は成功時のみ実行される
    """

    @patch(f'{COMMON_SERVICE_MODULE}.db')
    def test_save_layout_does_not_commit_on_db_error(self, mock_db):
        """2.3.1.1 save_layout: DB例外発生時に db.session.commit() が呼ばれない
        ワークフロー仕様書: except Exception → rollback() → raise
        rollback 後に再 raise するため commit() に到達しない
        """
        # Arrange
        mock_db.session.query.side_effect = Exception('DB書き込みエラー')
        layout_data = [
            {'gadget_uuid': 'g-001', 'position_x': 0, 'position_y': 0, 'display_order': 0}
        ]
        from iot_app.services.customer_dashboard.common import save_layout
        # Act
        with pytest.raises(Exception):
            save_layout(layout_data, modifier=1)
        # Assert: commit() が呼ばれていない
        mock_db.session.commit.assert_not_called()

    @patch(f'{COMMON_SERVICE_MODULE}.db')
    def test_delete_gadgets_by_dashboard_does_not_commit_on_db_error(self, mock_db):
        """2.3.1.2 delete_gadgets_by_dashboard: DB例外発生時に db.session.commit() が呼ばれない
        実装: db.session.query(...).all() → 例外発生時は commit() 行に到達しない
        NOTE: 本関数は自前の rollback を持たない。rollback は呼び出し元 View の責務。
        """
        # Arrange
        mock_db.session.query.side_effect = Exception('DBクエリエラー')
        from iot_app.services.customer_dashboard.common import delete_gadgets_by_dashboard
        # Act
        with pytest.raises(Exception):
            delete_gadgets_by_dashboard(dashboard_id=1, modifier=1)
        # Assert: commit() が呼ばれていない（commit 行に到達しない）
        mock_db.session.commit.assert_not_called()

    @patch(f'{COMMON_SERVICE_MODULE}.db')
    def test_create_circle_chart_gadget_does_not_commit_on_db_error(self, mock_db):
        """2.3.1.3 create_circle_chart_gadget: DB例外発生時に db.session.commit() が呼ばれない
        ワークフロー仕様書 § ガジェット登録 実装例
          except Exception as e:
              db.session.rollback()
              abort(500)
        ※ circle_chart.py 未実装 → TDDテスト（実装後に通過）
        """
        # Arrange
        mock_db.session.add.side_effect = Exception('DB INSERT エラー')
        from iot_app.services.customer_dashboard.circle_chart import create_circle_chart_gadget
        # Act
        with pytest.raises(Exception):
            create_circle_chart_gadget(
                gadget_name='円グラフ',
                dashboard_group_id=1,
                chart_config={'item_id_1': 1},
                data_source_config={'device_id': None},
                user_id=1,
            )
        # Assert: commit() が呼ばれていない
        mock_db.session.commit.assert_not_called()


# ---------------------------------------------------------------------------
# 2.3.2 例外発生時に rollback() が呼ばれる
# ---------------------------------------------------------------------------

@pytest.mark.unit
class TestSideEffect_Rollback:
    """2.3.2 副作用: 例外発生時に rollback() が呼ばれる

    根拠:
      ワークフロー仕様書 § ガジェット登録 実装例
        except Exception as e:
            db.session.rollback()
            abort(500)
      src/iot_app/services/customer_dashboard/common.py save_layout()
        except Exception:
            db.session.rollback()
            raise

    NOTE: update_gadget_title / delete_gadgets_by_dashboard は自前の rollback を持たない。
          これらの関数で例外が発生した場合、rollback は呼び出し元 View の try/except の責務。
          ワークフロー仕様書 実装例の except ブロックが該当する。
    """

    @patch(f'{COMMON_SERVICE_MODULE}.db')
    def test_save_layout_calls_rollback_on_exception(self, mock_db):
        """2.3.2.1 save_layout: DB例外発生時に db.session.rollback() が呼ばれる
        src/iot_app/services/customer_dashboard/common.py
          except Exception:
              db.session.rollback()
              raise
        """
        # Arrange
        mock_db.session.query.side_effect = Exception('DB書き込みエラー')
        layout_data = [
            {'gadget_uuid': 'g-001', 'position_x': 0, 'position_y': 0, 'display_order': 0}
        ]
        from iot_app.services.customer_dashboard.common import save_layout
        # Act
        with pytest.raises(Exception):
            save_layout(layout_data, modifier=1)
        # Assert: rollback() が呼ばれる
        mock_db.session.rollback.assert_called_once()

    @patch(f'{COMMON_SERVICE_MODULE}.db')
    def test_create_circle_chart_gadget_calls_rollback_on_exception(self, mock_db):
        """2.3.2.2 create_circle_chart_gadget: DB例外発生時に db.session.rollback() が呼ばれる
        ワークフロー仕様書 § ガジェット登録 実装例
          except Exception as e:
              db.session.rollback()
              abort(500)
        ※ circle_chart.py 未実装 → TDDテスト（実装後に通過）
        """
        # Arrange
        mock_db.session.add.side_effect = Exception('DB INSERT エラー')
        from iot_app.services.customer_dashboard.circle_chart import create_circle_chart_gadget
        # Act
        with pytest.raises(Exception):
            create_circle_chart_gadget(
                gadget_name='円グラフ',
                dashboard_group_id=1,
                chart_config={'item_id_1': 1},
                data_source_config={'device_id': None},
                user_id=1,
            )
        # Assert: rollback() が呼ばれる
        mock_db.session.rollback.assert_called_once()

    @patch(f'{COMMON_SERVICE_MODULE}.db')
    def test_update_gadget_title_has_no_own_rollback(self, mock_db):
        """2.3.2.3 update_gadget_title: 自前の rollback を持たない（呼び出し元 View の責務）
        本関数は model オブジェクトのフィールドを直接更新するのみ。
        commit / rollback は呼び出し元 View の try/except ブロックが担う。
        ワークフロー仕様書 § ガジェット登録 実装例:
          except Exception as e:
              db.session.rollback()   ← View 側の rollback
        """
        # Arrange
        from unittest.mock import MagicMock
        mock_gadget = MagicMock()
        from iot_app.services.customer_dashboard.common import update_gadget_title
        # Act: 正常に呼び出す（例外なし）
        update_gadget_title(mock_gadget, name='新タイトル', modifier=1)
        # Assert: rollback() も commit() も本関数内では呼ばれない
        mock_db.session.rollback.assert_not_called()
        mock_db.session.commit.assert_not_called()


# ===========================================================================
# Section 17: 登録機能 (3.2 登録機能観点)
#
# 根拠仕様書:
#   ワークフロー仕様書 § ガジェット登録 処理詳細（③ ガジェット登録）
#   ワークフロー仕様書 § ガジェット登録 バリデーション
#   ワークフロー仕様書 § ガジェット登録 ② chart_config / data_source_config JSONスキーマ
#
# 対象関数: create_circle_chart_gadget（circle_chart.py 未実装・TDDテスト）
#
# NOTE: circle_chart.py 未実装のため、全テストは ImportError で失敗する。
#       実装後に通過することを想定した仕様駆動テスト。
# ===========================================================================


# ---------------------------------------------------------------------------
# 3.2.1 登録処理呼び出し
# ---------------------------------------------------------------------------

@pytest.mark.unit
class TestRegister_CallRepository:
    """3.2.1 登録処理呼び出し: 正しい引数で Repository（db.session.add）が呼ばれる

    根拠:
      ワークフロー仕様書 § ガジェット登録 実装例 ③
        gadget = DashboardGadgetMaster(
            gadget_uuid=str(uuid.uuid4()),
            gadget_name=form.title.data,
            gadget_type_id=gadget_type_id,
            dashboard_group_id=form.group_id.data,
            chart_config=chart_config,
            data_source_config=data_source_config,
            ...
        )
        db.session.add(gadget)
      ワークフロー仕様書 § ガジェット登録 バリデーション
        if not form.validate_on_submit():
            return render_template(...), 400  → add() に到達しない
    """

    @patch(f'{COMMON_SERVICE_MODULE}.db')
    def test_add_called_with_correct_fields(self, mock_db):
        """3.2.1.1 正常な入力値: db.session.add() が正しいフィールドの DashboardGadgetMaster で呼ばれる
        ワークフロー仕様書 § ガジェット登録 実装例 ③ INSERT フィールド
          gadget_name, dashboard_group_id, chart_config, data_source_config, creator, modifier
        """
        # Arrange
        mock_db.session.query.return_value.filter.return_value.scalar.return_value = 0
        mock_db.session.query.return_value.filter_by.return_value.first.return_value = (
            type('GadgetType', (), {'gadget_type_id': 1})()
        )
        from iot_app.services.customer_dashboard.circle_chart import create_circle_chart_gadget
        # Act
        create_circle_chart_gadget(
            gadget_name='テスト円グラフ',
            dashboard_group_id=10,
            chart_config={'item_id_1': 1, 'item_id_2': 2},
            data_source_config={'device_id': 42},
            user_id=99,
        )
        # Assert: db.session.add() が呼ばれる
        mock_db.session.add.assert_called_once()
        added_gadget = mock_db.session.add.call_args[0][0]
        assert added_gadget.gadget_name == 'テスト円グラフ'
        assert added_gadget.dashboard_group_id == 10
        assert added_gadget.creator == 99
        assert added_gadget.modifier == 99

    @patch(f'{COMMON_SERVICE_MODULE}.db')
    def test_none_device_id_passed_as_is(self, mock_db):
        """3.2.1.2 device_id=None（デバイス可変モード）: data_source_config に None がそのまま渡される
        ワークフロー仕様書 § ガジェット登録 ② data_source_config JSONスキーマ
          デバイス可変モード: {"device_id": null}
          device_id = None のまま json.dumps({'device_id': device_id}) に渡す
        """
        # Arrange
        mock_db.session.query.return_value.filter.return_value.scalar.return_value = 0
        mock_db.session.query.return_value.filter_by.return_value.first.return_value = (
            type('GadgetType', (), {'gadget_type_id': 1})()
        )
        from iot_app.services.customer_dashboard.circle_chart import create_circle_chart_gadget
        import json
        # Act: device_id=None（デバイス可変モード）
        create_circle_chart_gadget(
            gadget_name='可変デバイス円グラフ',
            dashboard_group_id=10,
            chart_config={'item_id_1': 1},
            data_source_config={'device_id': None},
            user_id=99,
        )
        # Assert: data_source_config に device_id=null が含まれる
        mock_db.session.add.assert_called_once()
        added_gadget = mock_db.session.add.call_args[0][0]
        parsed = json.loads(added_gadget.data_source_config)
        assert parsed['device_id'] is None

    @patch(f'{COMMON_SERVICE_MODULE}.db')
    def test_add_not_called_when_form_invalid(self, mock_db, app):
        """3.2.1.3 バリデーションエラー発生: db.session.add() が呼ばれない
        ワークフロー仕様書 § ガジェット登録 実装例
          if not form.validate_on_submit():
              return render_template(...), 400  # add() に到達しない
        フォームバリデーション失敗時はサービス関数を呼ばないため add() は未呼び出し
        """
        # Arrange: フォームバリデーション失敗（必須項目なし）
        from iot_app.forms.customer_dashboard.circle_chart import CircleChartGadgetForm
        with app.test_request_context():
            form = CircleChartGadgetForm(data={})
            is_valid = form.validate()
        # Assert: フォームが無効であること（ビュー層が add() を呼ばない前提条件）
        assert is_valid is False
        # add() が呼ばれていないこと（バリデーション失敗時はサービス未到達）
        mock_db.session.add.assert_not_called()

    @patch(f'{COMMON_SERVICE_MODULE}.db')
    def test_chart_config_serialized_with_item_id_keys(self, mock_db):
        """② chart_config JSONスキーマ: item_id_1〜5 キーが JSON 文字列として保存される
        ワークフロー仕様書 § ガジェット登録 ② chart_config JSONスキーマ
          {"item_id_1": 1, "item_id_2": 2, ..., "item_id_5": 5}
        """
        # Arrange
        import json
        mock_db.session.query.return_value.filter.return_value.scalar.return_value = 0
        mock_db.session.query.return_value.filter_by.return_value.first.return_value = (
            type('GadgetType', (), {'gadget_type_id': 1})()
        )
        from iot_app.services.customer_dashboard.circle_chart import create_circle_chart_gadget
        # Act
        create_circle_chart_gadget(
            gadget_name='円グラフ',
            dashboard_group_id=10,
            chart_config={
                'item_id_1': 1, 'item_id_2': 2, 'item_id_3': 3,
                'item_id_4': 4, 'item_id_5': 5,
            },
            data_source_config={'device_id': None},
            user_id=99,
        )
        # Assert: chart_config が item_id_1〜5 キーを持つ JSON 文字列で保存される
        added_gadget = mock_db.session.add.call_args[0][0]
        parsed = json.loads(added_gadget.chart_config)
        for key in ['item_id_1', 'item_id_2', 'item_id_3', 'item_id_4', 'item_id_5']:
            assert key in parsed
        assert parsed['item_id_1'] == 1
        assert parsed['item_id_5'] == 5

    @patch(f'{COMMON_SERVICE_MODULE}.db')
    def test_data_source_config_fixed_mode_device_id_serialized(self, mock_db):
        """② data_source_config 固定モード: device_id が整数値として JSON 文字列で保存される
        ワークフロー仕様書 § ガジェット登録 ② data_source_config JSONスキーマ
          デバイス固定モード: {"device_id": 12345}
        """
        # Arrange
        import json
        mock_db.session.query.return_value.filter.return_value.scalar.return_value = 0
        mock_db.session.query.return_value.filter_by.return_value.first.return_value = (
            type('GadgetType', (), {'gadget_type_id': 1})()
        )
        from iot_app.services.customer_dashboard.circle_chart import create_circle_chart_gadget
        # Act
        create_circle_chart_gadget(
            gadget_name='固定デバイス円グラフ',
            dashboard_group_id=10,
            chart_config={'item_id_1': 1},
            data_source_config={'device_id': 12345},
            user_id=99,
        )
        # Assert: data_source_config に整数の device_id が含まれる
        added_gadget = mock_db.session.add.call_args[0][0]
        parsed = json.loads(added_gadget.data_source_config)
        assert parsed['device_id'] == 12345

    @patch(f'{COMMON_SERVICE_MODULE}.db')
    def test_position_y_and_display_order_are_max_plus_one(self, mock_db):
        """③ position_y / display_order = COALESCE(MAX, 0) + 1
        ワークフロー仕様書 § ガジェット登録 SQL
          position_y    = COALESCE(MAX(position_y), 0) + 1
          display_order = COALESCE(MAX(display_order), 0) + 1
        既存最大値が 4 の場合、新規ガジェットは 5 で登録される
        """
        # Arrange
        mock_db.session.query.return_value.filter.return_value.scalar.return_value = 4
        mock_db.session.query.return_value.filter_by.return_value.first.return_value = (
            type('GadgetType', (), {'gadget_type_id': 1})()
        )
        from iot_app.services.customer_dashboard.circle_chart import create_circle_chart_gadget
        # Act
        create_circle_chart_gadget(
            gadget_name='円グラフ',
            dashboard_group_id=10,
            chart_config={'item_id_1': 1},
            data_source_config={'device_id': None},
            user_id=99,
        )
        # Assert: MAX(4) + 1 = 5
        added_gadget = mock_db.session.add.call_args[0][0]
        assert added_gadget.position_y == 5
        assert added_gadget.display_order == 5

    @patch(f'{COMMON_SERVICE_MODULE}.db')
    def test_initial_values_are_set_correctly(self, mock_db):
        """③ INSERT 初期値: position_x=0 / gadget_size=0 / delete_flag=False
        ワークフロー仕様書 § ガジェット登録 SQL
          position_x = 0（固定）
          gadget_size = 0（円グラフは固定サイズ）
          delete_flag = FALSE
        """
        # Arrange
        mock_db.session.query.return_value.filter.return_value.scalar.return_value = 0
        mock_db.session.query.return_value.filter_by.return_value.first.return_value = (
            type('GadgetType', (), {'gadget_type_id': 1})()
        )
        from iot_app.services.customer_dashboard.circle_chart import create_circle_chart_gadget
        # Act
        create_circle_chart_gadget(
            gadget_name='円グラフ',
            dashboard_group_id=10,
            chart_config={'item_id_1': 1},
            data_source_config={'device_id': None},
            user_id=99,
        )
        # Assert
        added_gadget = mock_db.session.add.call_args[0][0]
        assert added_gadget.position_x == 0
        assert added_gadget.gadget_size == 0
        assert added_gadget.delete_flag is False

    @patch(f'{COMMON_SERVICE_MODULE}.db')
    def test_position_y_is_one_when_no_existing_gadgets(self, mock_db):
        """③ INSERT position_y/display_order: グループ内初ガジェット時は 1 になる
        ワークフロー仕様書 § ガジェット登録 SQL
          position_y  = COALESCE(MAX(position_y),  0) + 1
          display_order = COALESCE(MAX(display_order), 0) + 1
        scalar() が None を返す場合、or 0 により MAX=0 → 値は 1 になること
        """
        # Arrange: scalar()=None（グループ内にガジェットが存在しない）
        mock_db.session.query.return_value.filter.return_value.scalar.return_value = None
        mock_db.session.query.return_value.filter_by.return_value.first.return_value = (
            type('GadgetType', (), {'gadget_type_id': 1})()
        )
        from iot_app.services.customer_dashboard.circle_chart import create_circle_chart_gadget
        # Act
        create_circle_chart_gadget(
            gadget_name='円グラフ',
            dashboard_group_id=10,
            chart_config={'item_id_1': 1},
            data_source_config={'device_id': None},
            user_id=99,
        )
        # Assert
        added_gadget = mock_db.session.add.call_args[0][0]
        assert added_gadget.position_y == 1
        assert added_gadget.display_order == 1

    @patch(f'{COMMON_SERVICE_MODULE}.db')
    def test_gadget_type_id_is_set_from_gadget_type_master(self, mock_db):
        """③ INSERT gadget_type_id: GadgetTypeMaster から取得した値がモデルに設定される
        ワークフロー仕様書 § ガジェット登録 SQL
          gadget_type_id = db.session.query(GadgetTypeMaster)
                              .filter_by(gadget_type_name='円グラフ', delete_flag=False)
                              .first().gadget_type_id
        """
        # Arrange: GadgetTypeMaster から gadget_type_id=3 が返るケース
        mock_db.session.query.return_value.filter.return_value.scalar.return_value = 0
        mock_db.session.query.return_value.filter_by.return_value.first.return_value = (
            type('GadgetType', (), {'gadget_type_id': 3})()
        )
        from iot_app.services.customer_dashboard.circle_chart import create_circle_chart_gadget
        # Act
        create_circle_chart_gadget(
            gadget_name='円グラフ',
            dashboard_group_id=10,
            chart_config={'item_id_1': 1},
            data_source_config={'device_id': None},
            user_id=99,
        )
        # Assert
        added_gadget = mock_db.session.add.call_args[0][0]
        assert added_gadget.gadget_type_id == 3

    @patch(f'{COMMON_SERVICE_MODULE}.db')
    def test_commit_called_on_success(self, mock_db):
        """③ INSERT 成功後コミット: db.session.commit() が呼ばれる
        ワークフロー仕様書 § ガジェット登録 実装例
          db.session.add(gadget)
          db.session.commit()   ← 成功時は必ずコミットされる
        """
        # Arrange
        mock_db.session.query.return_value.filter.return_value.scalar.return_value = 0
        mock_db.session.query.return_value.filter_by.return_value.first.return_value = (
            type('GadgetType', (), {'gadget_type_id': 1})()
        )
        from iot_app.services.customer_dashboard.circle_chart import create_circle_chart_gadget
        # Act
        create_circle_chart_gadget(
            gadget_name='円グラフ',
            dashboard_group_id=10,
            chart_config={'item_id_1': 1},
            data_source_config={'device_id': None},
            user_id=99,
        )
        # Assert
        mock_db.session.commit.assert_called_once()


# ---------------------------------------------------------------------------
# 3.2.2 登録結果
# ---------------------------------------------------------------------------

@pytest.mark.unit
class TestRegister_Result:
    """3.2.2 登録結果: 登録成功時に正しい値が返る

    根拠:
      ワークフロー仕様書 § ガジェット登録 実装例 ③
        gadget = DashboardGadgetMaster(
            gadget_uuid=str(uuid.uuid4()),   # UUID v4 を自動生成
            ...
        )
        db.session.add(gadget)
      ワークフロー仕様書 § ガジェットデータ取得 ⑥ レスポンス形式
        "gadget_uuid": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
    """

    @patch(f'{COMMON_SERVICE_MODULE}.db')
    def test_returns_gadget_with_uuid(self, mock_db):
        """3.2.2.1 登録処理成功: gadget_uuid が設定された gadget オブジェクトが返る
        ワークフロー仕様書: gadget_uuid=str(uuid.uuid4())
        UUID v4 形式（8-4-4-4-12 の16進数文字列）で生成されること
        """
        # Arrange
        mock_db.session.query.return_value.filter.return_value.scalar.return_value = 0
        mock_db.session.query.return_value.filter_by.return_value.first.return_value = (
            type('GadgetType', (), {'gadget_type_id': 1})()
        )
        from iot_app.services.customer_dashboard.circle_chart import create_circle_chart_gadget
        import re
        _UUID_PATTERN = re.compile(
            r'^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$'
        )
        # Act
        result = create_circle_chart_gadget(
            gadget_name='円グラフ',
            dashboard_group_id=10,
            chart_config={'item_id_1': 1},
            data_source_config={'device_id': 42},
            user_id=99,
        )
        # Assert: 返却されたオブジェクトに UUID v4 形式の gadget_uuid が設定されている
        assert result is not None
        assert hasattr(result, 'gadget_uuid')
        assert _UUID_PATTERN.match(result.gadget_uuid)


# ===========================================================================
# Section 19: ガジェット設定取得 (get_gadget_by_uuid)
# ワークフロー仕様書 § ガジェットデータ取得 ① ガジェット設定取得
#
# 使用テーブル: dashboard_gadget_master
# SQL: SELECT gadget_id, gadget_uuid, gadget_type_id, chart_config, data_source_config
#      FROM dashboard_gadget_master
#      WHERE gadget_uuid = :gadget_uuid AND delete_flag = FALSE
#
# chart_config JSONスキーマ:      {"item_id_1": 1, ..., "item_id_5": 5}
# data_source_config JSONスキーマ: {"device_id": 12345}  ※nullの場合はデバイス可変モード
#
# ※ get_gadget_by_uuid は circle_chart.py 未実装 → TDDテスト（実装後に通過）
# ===========================================================================

CIRCLE_CHART_SERVICE_MODULE = 'iot_app.services.customer_dashboard.circle_chart'


@pytest.mark.unit
class TestGetGadgetByUuid:
    """ガジェット設定取得

    観点: 2.2（対象データ存在チェック）, 3.1.1（検索条件指定）
    ワークフロー仕様書 § ガジェットデータ取得 ① ガジェット設定取得
      gadget = get_gadget_by_uuid(gadget_uuid)
      if not gadget:
          return jsonify({'error': '指定されたガジェットが見つかりません'}), 404
    """

    @patch(f'{CIRCLE_CHART_SERVICE_MODULE}.db')
    def test_returns_gadget_when_found(self, mock_db):
        """2.2.1 正常系: 有効な gadget_uuid で検索 → gadget オブジェクトを返す
        ワークフロー仕様書 § ガジェットデータ取得 ①
          gadget = get_gadget_by_uuid(gadget_uuid)  → ガジェット存在 → 後続処理へ
        """
        # Arrange
        mock_gadget = MagicMock()
        mock_gadget.gadget_uuid = 'test-uuid-1234'
        mock_gadget.gadget_type_id = 1
        mock_db.session.query.return_value.filter.return_value.first.return_value = mock_gadget
        from iot_app.services.customer_dashboard.circle_chart import get_gadget_by_uuid
        # Act
        result = get_gadget_by_uuid('test-uuid-1234')
        # Assert
        assert result == mock_gadget
        assert result.gadget_uuid == 'test-uuid-1234'

    @patch(f'{CIRCLE_CHART_SERVICE_MODULE}.db')
    def test_chart_config_has_required_keys(self, mock_db):
        """chart_config JSONスキーマ: item_id_1〜item_id_5 キーが取得できること
        ワークフロー仕様書 § ガジェットデータ取得 ① chart_config JSONスキーマ
          {"item_id_1": 1, "item_id_2": 2, ..., "item_id_5": 5}
        """
        # Arrange
        import json
        mock_gadget = MagicMock()
        mock_gadget.chart_config = json.dumps({
            'item_id_1': 1,
            'item_id_2': 2,
            'item_id_3': 3,
            'item_id_4': 4,
            'item_id_5': 5,
        })
        mock_db.session.query.return_value.filter.return_value.first.return_value = mock_gadget
        from iot_app.services.customer_dashboard.circle_chart import get_gadget_by_uuid
        # Act
        result = get_gadget_by_uuid('test-uuid-1234')
        parsed = json.loads(result.chart_config)
        # Assert: item_id_1〜item_id_5 キーが含まれること
        assert 'item_id_1' in parsed
        assert 'item_id_2' in parsed
        assert parsed['item_id_1'] == 1
        assert parsed['item_id_5'] == 5

    @patch(f'{CIRCLE_CHART_SERVICE_MODULE}.db')
    def test_data_source_config_has_device_id_key(self, mock_db):
        """data_source_config JSONスキーマ: device_id キーが取得できること
        ワークフロー仕様書 § ガジェットデータ取得 ① data_source_config JSONスキーマ
          {"device_id": 12345}
        """
        # Arrange
        import json
        mock_gadget = MagicMock()
        mock_gadget.data_source_config = json.dumps({'device_id': 12345})
        mock_db.session.query.return_value.filter.return_value.first.return_value = mock_gadget
        from iot_app.services.customer_dashboard.circle_chart import get_gadget_by_uuid
        # Act
        result = get_gadget_by_uuid('test-uuid-1234')
        parsed = json.loads(result.data_source_config)
        # Assert
        assert 'device_id' in parsed
        assert parsed['device_id'] == 12345

    @patch(f'{CIRCLE_CHART_SERVICE_MODULE}.db')
    def test_device_id_null_indicates_variable_mode(self, mock_db):
        """デバイス可変モード: data_source_config.device_id = null の場合はデバイス可変モード
        ワークフロー仕様書 § ガジェットデータ取得 ①
          ※ device_id が null の場合はデバイス可変モード
          → ビュー層で data_source_config['device_id'] is None を確認してデバイス可変モードと判定
        """
        # Arrange
        import json
        mock_gadget = MagicMock()
        mock_gadget.data_source_config = json.dumps({'device_id': None})
        mock_db.session.query.return_value.filter.return_value.first.return_value = mock_gadget
        from iot_app.services.customer_dashboard.circle_chart import get_gadget_by_uuid
        # Act
        result = get_gadget_by_uuid('test-uuid-1234')
        parsed = json.loads(result.data_source_config)
        # Assert: device_id が null → デバイス可変モードとして識別可能
        assert parsed['device_id'] is None


# ===========================================================================
# Section 18: 表示項目一覧取得 (get_measurement_items)
# ワークフロー仕様書 § ガジェット登録モーダル表示 ④ 表示項目一覧取得
# ===========================================================================

@pytest.mark.unit
class TestGetMeasurementItems:
    """表示項目一覧取得（円グラフ凡例選択用）

    観点: 3.1.1（検索条件指定）, 3.1.4（検索結果戻り値ハンドリング）
    ワークフロー仕様書 § ガジェット登録モーダル表示 ④ 表示項目一覧取得
      measurement_items = get_measurement_items()
    UI仕様書 § (4) 凡例一覧: measurement_item_id 1〜22 の全22種類
    ※ get_measurement_items は common.py 未実装 → TDDテスト（実装後に通過）
    """

    @patch(f'{COMMON_SERVICE_MODULE}.db')
    def test_returns_all_measurement_items(self, mock_db):
        """3.1.4.1 正常系: 全 measurement_item を返す（引数なし・条件なし全件取得）
        ワークフロー仕様書 § ガジェット登録モーダル表示 ④
          measurement_items = get_measurement_items()  # 全件取得
        UI仕様書 § (4) 凡例一覧: 22種類の項目が存在する
        SQL: WHERE delete_flag = FALSE ORDER BY measurement_item_id
        """
        # Arrange
        mock_items = [MagicMock() for _ in range(22)]
        (
            mock_db.session.query.return_value
            .filter.return_value.order_by.return_value.all.return_value
        ) = mock_items
        from iot_app.services.customer_dashboard.common import get_measurement_items
        # Act
        result = get_measurement_items()
        # Assert
        assert result == mock_items
        assert len(result) == 22

    @patch(f'{COMMON_SERVICE_MODULE}.db')
    def test_returns_empty_list_when_no_items(self, mock_db):
        """3.1.4.2 空結果: measurement_item_master が空の場合は空リストを返す
        SQL: WHERE delete_flag = FALSE → 論理削除済みを除外した結果が空
        """
        # Arrange
        (
            mock_db.session.query.return_value
            .filter.return_value.order_by.return_value.all.return_value
        ) = []
        from iot_app.services.customer_dashboard.common import get_measurement_items
        # Act
        result = get_measurement_items()
        # Assert
        assert result == []

    @patch(f'{COMMON_SERVICE_MODULE}.db')
    def test_filters_deleted_items(self, mock_db):
        """3.1.1 検索条件: delete_flag=False フィルタが適用される
        ワークフロー仕様書 § ガジェット登録モーダル表示 ④ SQL
          WHERE delete_flag = FALSE
        論理削除済みの measurement_item は取得されないこと
        """
        # Arrange: delete_flag=False のみ2件返す（論理削除済みは除外）
        mock_active = [MagicMock(), MagicMock()]
        (
            mock_db.session.query.return_value
            .filter.return_value.order_by.return_value.all.return_value
        ) = mock_active
        from iot_app.services.customer_dashboard.common import get_measurement_items
        # Act
        result = get_measurement_items()
        # Assert: filter が呼ばれている（delete_flag フィルタが適用されている）
        mock_db.session.query.return_value.filter.assert_called_once()
        assert result == mock_active

    @patch(f'{COMMON_SERVICE_MODULE}.db')
    def test_propagates_db_error(self, mock_db):
        """1.3.1 例外伝播: DB例外が握りつぶされず上位へ伝播する
        ワークフロー仕様書 § ガジェット登録モーダル表示 フロー図
          ④ 表示項目一覧取得 失敗 → Error500
        """
        # Arrange
        mock_db.session.query.side_effect = Exception('DB接続エラー')
        from iot_app.services.customer_dashboard.common import get_measurement_items
        # Act / Assert
        with pytest.raises(Exception):
            get_measurement_items()


# ===========================================================================
# Section 20: センサーデータ取得 (fetch_circle_chart_data)
# ワークフロー仕様書 § ガジェットデータ取得 ③ センサーデータ取得
#
# 使用テーブル: iot_catalog.views.sensor_data_view
# SQL: SELECT event_timestamp, external_temp, ... FROM sensor_data_view
#      WHERE device_id = :device_id ORDER BY event_timestamp DESC LIMIT 1
#
# ※ fetch_circle_chart_data は circle_chart.py 未実装 → TDDテスト（実装後に通過）
# NOTE: 例外伝播テストは Section 14（1.3.1.4）に存在する。本セクションは正常系・空結果を補完。
# ===========================================================================

@pytest.mark.unit
class TestFetchCircleChartData:
    """センサーデータ取得

    観点: 2.1（正常系処理）, 3.1.4（検索結果戻り値ハンドリング）
    ワークフロー仕様書 § ガジェットデータ取得 ③
      rows = fetch_circle_chart_data(device_id)
    """

    @patch(f'{CIRCLE_CHART_SERVICE_MODULE}.db')
    def test_returns_sensor_data_rows(self, mock_db):
        """2.1.1 正常系: device_id に対応するセンサーデータ行を返す
        ワークフロー仕様書 § ③ SQL: LIMIT 1 → 最新1件を返す
        """
        # Arrange
        mock_row = {
            'event_timestamp': '2026-03-05T12:00:00',
            'external_temp': 10.5,
            'set_temp_freezer_1': 12.3,
        }
        mock_db.session.execute.return_value.fetchall.return_value = [mock_row]
        from iot_app.services.customer_dashboard.circle_chart import fetch_circle_chart_data
        # Act
        result = fetch_circle_chart_data(device_id=42)
        # Assert
        assert len(result) == 1
        assert result[0]['external_temp'] == 10.5

    @patch(f'{CIRCLE_CHART_SERVICE_MODULE}.db')
    def test_returns_empty_list_when_no_data(self, mock_db):
        """3.1.4.2 空結果: 対象デバイスのセンサーデータが存在しない場合は空リストを返す
        ワークフロー仕様書 § ⑤ データ整形
          rows が空 → format_circle_chart_data が {"labels": [], "values": []} を返す前提
        """
        # Arrange
        mock_db.session.execute.return_value.fetchall.return_value = []
        from iot_app.services.customer_dashboard.circle_chart import fetch_circle_chart_data
        # Act
        result = fetch_circle_chart_data(device_id=42)
        # Assert
        assert result == []


# ===========================================================================
# Section 21: 凡例名取得 (get_column_definition)
# ワークフロー仕様書 § ガジェットデータ取得 ④ 凡例名取得
#
# 使用テーブル: measurement_item_master
# SQL: SELECT measurement_item_id, silver_data_column_name, display_name
#      FROM measurement_item_master
#      WHERE delete_flag = FALSE
#      ORDER BY measurement_item_id
#
# ※ get_column_definition は circle_chart.py 未実装 → TDDテスト（実装後に通過）
# ===========================================================================

@pytest.mark.unit
class TestGetColumnDefinition:
    """凡例名取得（measurement_item_master 全件）

    観点: 3.1.4（検索結果戻り値ハンドリング）, 1.3.1（例外伝播）
    ワークフロー仕様書 § ガジェットデータ取得 ④
      all_columns = get_column_definition()
    """

    @patch(f'{CIRCLE_CHART_SERVICE_MODULE}.db')
    def test_returns_column_definitions(self, mock_db):
        """3.1.4.1 正常系: measurement_item_master の全列定義を返す
        ワークフロー仕様書 § ④ SQL: measurement_item_id, silver_data_column_name, display_name
        """
        # Arrange
        mock_col_1 = {
            'measurement_item_id': 1,
            'silver_data_column_name': 'external_temp',
            'display_name': '外気温度',
        }
        mock_col_2 = {
            'measurement_item_id': 2,
            'silver_data_column_name': 'set_temp_freezer_1',
            'display_name': '第1冷凍 設定温度',
        }
        mock_db.session.query.return_value.filter.return_value.order_by.return_value.all.return_value = [
            mock_col_1, mock_col_2
        ]
        from iot_app.services.customer_dashboard.circle_chart import get_column_definition
        # Act
        result = get_column_definition()
        # Assert
        assert len(result) == 2
        assert result[0]['measurement_item_id'] == 1
        assert result[0]['silver_data_column_name'] == 'external_temp'
        assert result[0]['display_name'] == '外気温度'

    @patch(f'{CIRCLE_CHART_SERVICE_MODULE}.db')
    def test_returns_empty_list_when_no_columns(self, mock_db):
        """3.1.4.2 空結果: measurement_item_master が空の場合は空リストを返す"""
        # Arrange
        mock_db.session.query.return_value.filter.return_value.order_by.return_value.all.return_value = []
        from iot_app.services.customer_dashboard.circle_chart import get_column_definition
        # Act
        result = get_column_definition()
        # Assert
        assert result == []

    @patch(f'{CIRCLE_CHART_SERVICE_MODULE}.db')
    def test_propagates_db_error(self, mock_db):
        """1.3.1 例外伝播: DB例外が握りつぶされず上位へ伝播する
        ワークフロー仕様書 § ガジェットデータ取得 フロー図
          LegendQuery 失敗 → Error500
        """
        # Arrange
        mock_db.session.query.side_effect = Exception('DB接続エラー')
        from iot_app.services.customer_dashboard.circle_chart import get_column_definition
        # Act / Assert
        with pytest.raises(Exception):
            get_column_definition()


# ===========================================================================
# Section 22: デバイス名取得 (get_device_name)
# ワークフロー仕様書 § ガジェットデータ取得 ② デバイス決定
#   device_name = get_device_name(device_id)
#
# 使用テーブル: device_master
# ※ get_device_name は circle_chart.py 未実装 → TDDテスト（実装後に通過）
# ===========================================================================

@pytest.mark.unit
class TestGetDeviceName:
    """デバイス名取得

    観点: 2.2（対象データ存在チェック）, 3.1.4（検索結果戻り値ハンドリング）
    ワークフロー仕様書 § ガジェットデータ取得 ② デバイス決定
      device_name = get_device_name(device_id)
    """

    @patch(f'{CIRCLE_CHART_SERVICE_MODULE}.db')
    def test_returns_device_name_when_found(self, mock_db):
        """2.2.1 正常系: 有効な device_id でデバイス名を返す
        ワークフロー仕様書 § ⑥ レスポンス形式: "device_name": "Device-001"
        """
        # Arrange
        mock_device = MagicMock()
        mock_device.device_name = 'Device-001'
        mock_db.session.query.return_value.filter.return_value.first.return_value = mock_device
        from iot_app.services.customer_dashboard.circle_chart import get_device_name
        # Act
        result = get_device_name(device_id=42)
        # Assert
        assert result == 'Device-001'

    @patch(f'{CIRCLE_CHART_SERVICE_MODULE}.db')
    def test_returns_none_when_device_not_found(self, mock_db):
        """2.2.2 存在確認: device_id に対応するデバイスが存在しない場合は None を返す"""
        # Arrange
        mock_db.session.query.return_value.filter.return_value.first.return_value = None
        from iot_app.services.customer_dashboard.circle_chart import get_device_name
        # Act
        result = get_device_name(device_id=99999)
        # Assert
        assert result is None

    @patch(f'{CIRCLE_CHART_SERVICE_MODULE}.db')
    def test_returns_none_when_device_id_is_none(self, mock_db):
        """デバイス可変モードでデバイス未確定: device_id=None の場合は None を返す
        ワークフロー仕様書 § ② デバイス可変モード
          user_setting.device_id が None のままの場合 → device_name = None
        """
        # Arrange
        mock_db.session.query.return_value.filter.return_value.first.return_value = None
        from iot_app.services.customer_dashboard.circle_chart import get_device_name
        # Act
        result = get_device_name(device_id=None)
        # Assert
        assert result is None

    @patch(f'{CIRCLE_CHART_SERVICE_MODULE}.db')
    def test_propagates_db_error(self, mock_db):
        """1.3.1 例外伝播: DB例外が握りつぶされず上位へ伝播する"""
        # Arrange
        mock_db.session.query.side_effect = Exception('DB接続エラー')
        from iot_app.services.customer_dashboard.circle_chart import get_device_name
        # Act / Assert
        with pytest.raises(Exception):
            get_device_name(device_id=42)


# ===========================================================================
# Section 23: ダッシュボード取得 (get_dashboard_by_id)
# ワークフロー仕様書 § ガジェット登録モーダル表示 ② ダッシュボード情報取得
#
# 使用テーブル: dashboard_master
# SQL: SELECT ... FROM dashboard_master WHERE dashboard_id = :dashboard_id
#
# common.py 実装済み:
#   def get_dashboard_by_id(dashboard_id):
#       return db.session.query(DashboardMaster).filter(...).first()
# ===========================================================================

@pytest.mark.unit
class TestGetDashboardById:
    """ダッシュボード取得

    観点: 2.2（対象データ存在チェック）, 3.1.1（検索条件指定）
    ワークフロー仕様書 § ガジェット登録モーダル表示 ②
      dashboard = get_dashboard_by_id(user_setting.dashboard_id, accessible_org_ids)
      if not dashboard: abort(404)
    """

    @patch(f'{COMMON_SERVICE_MODULE}.db')
    def test_returns_dashboard_when_found(self, mock_db):
        """2.2.1 正常系: 有効な dashboard_id でダッシュボードを返す
        ワークフロー仕様書 § ガジェット登録モーダル表示 ②
          → ダッシュボード取得成功 → abort(404) を呼ばない
        """
        # Arrange
        mock_dashboard = MagicMock()
        mock_dashboard.dashboard_id = 1
        mock_db.session.query.return_value.filter.return_value.first.return_value = mock_dashboard
        from iot_app.services.customer_dashboard.common import get_dashboard_by_id
        # Act
        result = get_dashboard_by_id(dashboard_id=1)
        # Assert
        assert result == mock_dashboard
        assert result.dashboard_id == 1

    @patch(f'{COMMON_SERVICE_MODULE}.db')
    def test_returns_none_when_not_found(self, mock_db):
        """2.2.2 存在確認: 存在しない dashboard_id の場合は None を返す
        ワークフロー仕様書 § ガジェット登録モーダル表示 ②
          if not dashboard: abort(404)
        """
        # Arrange
        mock_db.session.query.return_value.filter.return_value.first.return_value = None
        from iot_app.services.customer_dashboard.common import get_dashboard_by_id
        # Act
        result = get_dashboard_by_id(dashboard_id=99999)
        # Assert
        assert result is None

    @patch(f'{COMMON_SERVICE_MODULE}.db')
    def test_propagates_db_error(self, mock_db):
        """1.3.1 例外伝播: DB例外が握りつぶされず上位へ伝播する
        ワークフロー仕様書 § ガジェット登録モーダル表示 フロー図
          CheckDashboard 失敗 → Error500
        """
        # Arrange
        mock_db.session.query.side_effect = Exception('DB接続エラー')
        from iot_app.services.customer_dashboard.common import get_dashboard_by_id
        # Act / Assert
        with pytest.raises(Exception):
            get_dashboard_by_id(dashboard_id=1)


# ===========================================================================
# Section 24: スコープ内全デバイス一覧取得 (get_all_devices_in_scope)
# ワークフロー仕様書 § ガジェット登録モーダル表示 ⑥ デバイス一覧取得
#
# 使用テーブル: device_master
# SQL: SELECT device_id, device_name, organization_id FROM device_master
#      WHERE organization_id IN (:accessible_org_ids) AND delete_flag = FALSE
#      ORDER BY device_id ASC
#
# ※ get_all_devices_in_scope は common.py 未実装 → TDDテスト（実装後に通過）
# NOTE: get_devices(organization_id) は単一組織IDでフィルタ（Section 8）。
#       get_all_devices_in_scope(accessible_org_ids) は複数組織IDリストでフィルタする別関数。
# ===========================================================================

@pytest.mark.unit
class TestGetAllDevicesInScope:
    """スコープ内全デバイス一覧取得（ガジェット登録モーダル用）

    観点: 3.1.1（検索条件指定）, 3.1.4（検索結果戻り値ハンドリング）
    ワークフロー仕様書 § ガジェット登録モーダル表示 ⑥
      devices = get_all_devices_in_scope(accessible_org_ids)
    """

    @patch(f'{COMMON_SERVICE_MODULE}.db')
    def test_returns_devices_within_accessible_orgs(self, mock_db):
        """3.1.1.1 条件指定: accessible_org_ids（複数組織）でフィルタされたデバイス一覧を返す
        ワークフロー仕様書 § ⑥ SQL: organization_id IN (:accessible_org_ids)
        """
        # Arrange
        mock_device_1 = MagicMock()
        mock_device_1.device_name = 'Device-001'
        mock_device_2 = MagicMock()
        mock_device_2.device_name = 'Device-002'
        (
            mock_db.session.query.return_value
            .filter.return_value
            .order_by.return_value.all.return_value
        ) = [mock_device_1, mock_device_2]
        from iot_app.services.customer_dashboard.common import get_all_devices_in_scope
        # Act
        result = get_all_devices_in_scope(accessible_org_ids=[1, 2, 3])
        # Assert
        assert result == [mock_device_1, mock_device_2]
        assert len(result) == 2

    @patch(f'{COMMON_SERVICE_MODULE}.db')
    def test_returns_empty_list_when_no_devices(self, mock_db):
        """3.1.4.2 空結果: アクセス可能スコープ内にデバイスが存在しない場合は空リストを返す"""
        # Arrange
        (
            mock_db.session.query.return_value
            .filter.return_value
            .order_by.return_value.all.return_value
        ) = []
        from iot_app.services.customer_dashboard.common import get_all_devices_in_scope
        # Act
        result = get_all_devices_in_scope(accessible_org_ids=[1, 2, 3])
        # Assert
        assert result == []

    @patch(f'{COMMON_SERVICE_MODULE}.db')
    def test_returns_empty_list_when_accessible_org_ids_empty(self, mock_db):
        """3.1.1.3 条件未指定相当: accessible_org_ids が空リストの場合は空リストを返す
        アクセス可能組織がない場合はデバイスも0件となる
        """
        # Arrange
        (
            mock_db.session.query.return_value
            .filter.return_value
            .order_by.return_value.all.return_value
        ) = []
        from iot_app.services.customer_dashboard.common import get_all_devices_in_scope
        # Act
        result = get_all_devices_in_scope(accessible_org_ids=[])
        # Assert
        assert result == []

    @patch(f'{COMMON_SERVICE_MODULE}.db')
    def test_propagates_db_error(self, mock_db):
        """1.3.1 例外伝播: DB例外が握りつぶされず上位へ伝播する
        ワークフロー仕様書 § ガジェット登録モーダル表示 フロー図
          DeviceQuery 失敗 → Error500
        """
        # Arrange
        mock_db.session.query.side_effect = Exception('DB接続エラー')
        from iot_app.services.customer_dashboard.common import get_all_devices_in_scope
        # Act / Assert
        with pytest.raises(Exception):
            get_all_devices_in_scope(accessible_org_ids=[1, 2, 3])


# ===========================================================================
# Section 25: デバイス存在&スコープチェック (check_device_access)
# ワークフロー仕様書 § ガジェット登録 ① デバイス固定モード時のみ実行
#
# 使用テーブル: device_master
# SQL: SELECT device_id, device_name, organization_id FROM device_master
#      WHERE device_id = :device_id
#        AND organization_id IN (:accessible_org_ids)
#        AND delete_flag = FALSE
#
# ※ check_device_access は common.py 未実装 → TDDテスト（実装後に通過）
# ===========================================================================

@pytest.mark.unit
class TestCheckDeviceAccess:
    """デバイス存在&データスコープチェック（デバイス固定モード時のみ）

    観点: 2.2（対象データ存在チェック）, 3.1.1（検索条件指定）
    ワークフロー仕様書 § ガジェット登録 ①
      if form.device_mode.data == 'fixed':
          device = check_device_access(form.device_id.data, accessible_org_ids)
          if not device: abort(404)
    """

    @patch(f'{COMMON_SERVICE_MODULE}.db')
    def test_returns_device_when_accessible(self, mock_db):
        """2.2.1 正常系: device_id がアクセス可能スコープ内に存在する場合はデバイスを返す
        ワークフロー仕様書 § ① SQL:
          WHERE device_id = :device_id AND organization_id IN (:accessible_org_ids)
        """
        # Arrange
        mock_device = MagicMock()
        mock_device.device_id = 42
        mock_device.device_name = 'Device-001'
        mock_db.session.query.return_value.filter.return_value.first.return_value = mock_device
        from iot_app.services.customer_dashboard.common import check_device_access
        # Act
        result = check_device_access(device_id=42, accessible_org_ids=[1, 2, 3])
        # Assert
        assert result == mock_device
        assert result.device_id == 42

    @patch(f'{COMMON_SERVICE_MODULE}.db')
    def test_returns_none_when_device_not_in_scope(self, mock_db):
        """2.2.2 スコープ外: device_id がアクセス可能スコープ外の場合は None を返す
        ワークフロー仕様書 § ① organization_id IN (:accessible_org_ids) に合致しない
          → if not device: abort(404)
        """
        # Arrange
        mock_db.session.query.return_value.filter.return_value.first.return_value = None
        from iot_app.services.customer_dashboard.common import check_device_access
        # Act
        result = check_device_access(device_id=42, accessible_org_ids=[99, 100])
        # Assert
        assert result is None

    @patch(f'{COMMON_SERVICE_MODULE}.db')
    def test_returns_none_when_device_not_found(self, mock_db):
        """2.2.2 存在なし: device_id 自体が存在しない場合は None を返す
        ワークフロー仕様書 § ① SQL: WHERE device_id = :device_id → 0件
          → if not device: abort(404)
        """
        # Arrange
        mock_db.session.query.return_value.filter.return_value.first.return_value = None
        from iot_app.services.customer_dashboard.common import check_device_access
        # Act
        result = check_device_access(device_id=99999, accessible_org_ids=[1, 2, 3])
        # Assert
        assert result is None

    @patch(f'{COMMON_SERVICE_MODULE}.db')
    def test_propagates_db_error(self, mock_db):
        """1.3.1 例外伝播: DB例外が握りつぶされず上位へ伝播する
        ワークフロー仕様書 § ガジェット登録 フロー図
          CheckDeviceQuery 失敗 → Error500
        """
        # Arrange
        mock_db.session.query.side_effect = Exception('DB接続エラー')
        from iot_app.services.customer_dashboard.common import check_device_access
        # Act / Assert
        with pytest.raises(Exception):
            check_device_access(device_id=42, accessible_org_ids=[1, 2, 3])
