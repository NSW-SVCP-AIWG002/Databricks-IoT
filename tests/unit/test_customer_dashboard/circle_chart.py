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
            form = CircleChartGadgetForm(data={'gadget_name': '円グラフ', 'group_id': '1'})
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
            })
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
            })
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
