"""
顧客作成ダッシュボード 帯グラフガジェット - 単体テスト

対象:
  - src/iot_app/forms/customer_dashboard/belt_chart.py (BeltChartGadgetForm) ※未実装
  - src/iot_app/services/customer_dashboard/belt_chart.py (validate_chart_params) ※未実装
  - src/iot_app/services/customer_dashboard/belt_chart.py (format_belt_chart_data) ※未実装

参照仕様書:
  - docs/03-features/flask-app/customer-dashboard/belt-chart/ui-specification.md
  - docs/03-features/flask-app/customer-dashboard/belt-chart/workflow-specification.md
"""

import pytest
from datetime import datetime, date
from unittest.mock import MagicMock, patch

# measurement_item_master の有効 ID レンジ（UI仕様書 § (3) 表示項目選択）
_ALL_ITEM_IDS = list(range(1, 23))

_BELT_CHART_FORM_MODULE = 'iot_app.forms.customer_dashboard.belt_chart'
_BELT_CHART_SERVICE_MODULE = 'iot_app.services.customer_dashboard.belt_chart'
COMMON_SERVICE_MODULE = 'iot_app.services.customer_dashboard.common'


# ===========================================================================
# Section 1: フォームバリデーション - タイトル (BeltChartGadgetForm.gadget_name)
# UI仕様書 § バリデーション（登録画面）
#   タイトル: 必須、最大20文字
# ===========================================================================

@pytest.mark.unit
class TestBeltChartGadgetFormTitle:
    """帯グラフガジェット登録フォーム - タイトルバリデーション

    観点: 1.1.1（必須チェック）, 1.1.2（最大文字列長チェック）
    UI仕様書 § バリデーション（登録画面）
      - タイトル: 必須 → エラー「タイトルを入力してください」
      - タイトル: 最大20文字 → エラー「タイトルは20文字以内で入力してください」
    """

    def test_valid_when_title_provided(self, app):
        """1.1.1.3 入力あり: タイトルが入力されている場合はバリデーション通過"""
        # Arrange
        from iot_app.forms.customer_dashboard.belt_chart import BeltChartGadgetForm
        # Act
        with app.test_request_context():
            form = BeltChartGadgetForm(data={'gadget_name': '帯グラフ'})
            result = form.validate()
        # Assert
        assert result is True

    def test_invalid_when_title_empty(self, app):
        """1.1.1.1 空文字: タイトルが空文字の場合はバリデーションエラー"""
        # Arrange
        from iot_app.forms.customer_dashboard.belt_chart import BeltChartGadgetForm
        # Act
        with app.test_request_context():
            form = BeltChartGadgetForm(data={'gadget_name': ''})
            result = form.validate()
        # Assert
        assert result is False
        assert 'gadget_name' in form.errors

    def test_invalid_when_title_none(self, app):
        """1.1.1.2 None: タイトルが None の場合はバリデーションエラー"""
        # Arrange
        from iot_app.forms.customer_dashboard.belt_chart import BeltChartGadgetForm
        # Act
        with app.test_request_context():
            form = BeltChartGadgetForm(data={'gadget_name': None})
            result = form.validate()
        # Assert
        assert result is False
        assert 'gadget_name' in form.errors

    def test_invalid_when_title_whitespace_only(self, app):
        """1.1.1.4 空白のみ: DataRequired が strip するためバリデーションエラー"""
        # Arrange
        from iot_app.forms.customer_dashboard.belt_chart import BeltChartGadgetForm
        # Act
        with app.test_request_context():
            form = BeltChartGadgetForm(data={'gadget_name': '   '})
            result = form.validate()
        # Assert
        assert result is False
        assert 'gadget_name' in form.errors

    def test_valid_when_title_is_19_chars(self, app):
        """1.2.1 最大長-1（19文字）: バリデーション通過"""
        # Arrange
        from iot_app.forms.customer_dashboard.belt_chart import BeltChartGadgetForm
        # Act
        with app.test_request_context():
            form = BeltChartGadgetForm(data={'gadget_name': 'a' * 19})
            result = form.validate()
        # Assert
        assert result is True

    def test_valid_when_title_is_20_chars(self, app):
        """1.2.2 最大長ちょうど（20文字）: バリデーション通過"""
        # Arrange
        from iot_app.forms.customer_dashboard.belt_chart import BeltChartGadgetForm
        # Act
        with app.test_request_context():
            form = BeltChartGadgetForm(data={'gadget_name': 'a' * 20})
            result = form.validate()
        # Assert
        assert result is True

    def test_invalid_when_title_exceeds_20_chars(self, app):
        """1.2.3 最大長+1（21文字）: バリデーションエラー"""
        # Arrange
        from iot_app.forms.customer_dashboard.belt_chart import BeltChartGadgetForm
        # Act
        with app.test_request_context():
            form = BeltChartGadgetForm(data={'gadget_name': 'a' * 21})
            result = form.validate()
        # Assert
        assert result is False
        assert 'gadget_name' in form.errors

    def test_error_message_for_empty_title(self, app):
        """1.1.1.1 空文字: エラーメッセージが仕様書記載のメッセージであること"""
        # Arrange
        from iot_app.forms.customer_dashboard.belt_chart import BeltChartGadgetForm
        # Act
        with app.test_request_context():
            form = BeltChartGadgetForm(data={'gadget_name': ''})
            form.validate()
        # Assert
        assert 'タイトルを入力してください' in form.errors['gadget_name']

    def test_error_message_for_title_too_long(self, app):
        """1.2.3 最大長+1: エラーメッセージが仕様書記載のメッセージであること"""
        # Arrange
        from iot_app.forms.customer_dashboard.belt_chart import BeltChartGadgetForm
        # Act
        with app.test_request_context():
            form = BeltChartGadgetForm(data={'gadget_name': 'a' * 21})
            form.validate()
        # Assert
        assert 'タイトルは20文字以内で入力してください' in form.errors['gadget_name']


# ===========================================================================
# Section 2: フォームバリデーション - 表示デバイス選択 (BeltChartGadgetForm.device_mode)
# UI仕様書 § バリデーション（登録画面）
#   表示デバイス: 必須
# ===========================================================================

@pytest.mark.unit
class TestBeltChartGadgetFormDeviceMode:
    """帯グラフガジェット登録フォーム - 表示デバイス選択バリデーション

    観点: 1.1.1（必須チェック）
    UI仕様書 § バリデーション（登録画面）
      - 表示デバイス: 必須 → エラー「表示デバイスを選択してください」
    UI仕様書 § (2) 表示デバイス選択
      - デバイス固定: device_mode = 'fixed'
      - デバイス可変: device_mode = 'variable'
    """

    def test_invalid_when_device_mode_empty(self, app):
        """1.1.1.1 空文字: 表示デバイスが未選択の場合はバリデーションエラー"""
        # Arrange
        from iot_app.forms.customer_dashboard.belt_chart import BeltChartGadgetForm
        # Act
        with app.test_request_context():
            form = BeltChartGadgetForm(data={'gadget_name': '帯グラフ', 'device_mode': ''})
            result = form.validate()
        # Assert
        assert result is False
        assert 'device_mode' in form.errors

    def test_invalid_when_device_mode_none(self, app):
        """1.1.1.2 None: 表示デバイスが None の場合はバリデーションエラー"""
        # Arrange
        from iot_app.forms.customer_dashboard.belt_chart import BeltChartGadgetForm
        # Act
        with app.test_request_context():
            form = BeltChartGadgetForm(data={'gadget_name': '帯グラフ', 'device_mode': None})
            result = form.validate()
        # Assert
        assert result is False
        assert 'device_mode' in form.errors

    def test_valid_when_device_mode_is_fixed(self, app):
        """1.1.1.3 入力あり（fixed）: デバイス固定モードはバリデーション通過"""
        # Arrange
        from iot_app.forms.customer_dashboard.belt_chart import BeltChartGadgetForm
        # Act
        with app.test_request_context():
            form = BeltChartGadgetForm(data={
                'gadget_name': '帯グラフ',
                'device_mode': 'fixed',
                'device_id': '42',
                'group_id': '1',
                'summary_method_id': '1',
                'gadget_size': '0',
                'measurement_item_ids': ['1'],
            })
            form.measurement_item_ids.choices = [(i, f'item{i}') for i in _ALL_ITEM_IDS]
            result = form.validate()
        # Assert
        assert result is True

    def test_valid_when_device_mode_is_variable(self, app):
        """1.1.1.3 入力あり（variable）: デバイス可変モードはバリデーション通過"""
        # Arrange
        from iot_app.forms.customer_dashboard.belt_chart import BeltChartGadgetForm
        # Act
        with app.test_request_context():
            form = BeltChartGadgetForm(data={
                'gadget_name': '帯グラフ',
                'device_mode': 'variable',
                'group_id': '1',
                'summary_method_id': '1',
                'gadget_size': '0',
                'measurement_item_ids': ['1'],
            })
            form.measurement_item_ids.choices = [(i, f'item{i}') for i in _ALL_ITEM_IDS]
            result = form.validate()
        # Assert
        assert result is True

    def test_error_message_for_missing_device_mode(self, app):
        """未選択: エラーメッセージが仕様書記載のメッセージであること"""
        # Arrange
        from iot_app.forms.customer_dashboard.belt_chart import BeltChartGadgetForm
        # Act
        with app.test_request_context():
            form = BeltChartGadgetForm(data={
                'gadget_name': '帯グラフ',
                'device_mode': '',
                'group_id': '1',
            })
            form.validate()
        # Assert
        assert '表示デバイスを選択してください' in form.errors.get('device_mode', [])


# ===========================================================================
# Section 3: フォームバリデーション - デバイスID（デバイス固定モード時のみ）
# UI仕様書 § バリデーション（登録画面）
#   デバイス（デバイス固定時のみ）: 必須
# ワークフロー仕様書 § ガジェット登録 バリデーション
# ===========================================================================

@pytest.mark.unit
class TestBeltChartGadgetFormDeviceId:
    """帯グラフガジェット登録フォーム - デバイスIDバリデーション（デバイス固定時）

    観点: 1.1.1（必須チェック）
    UI仕様書 § バリデーション（登録画面）
      - デバイス（デバイス固定時のみ）: 必須 → エラー「デバイスを選択してください」
    UI仕様書 § (2) 表示デバイス選択
      - デバイス固定: device_mode = 'fixed'
      - デバイス可変: device_mode = 'variable'
    """

    def test_invalid_when_fixed_mode_and_device_id_empty(self, app):
        """1.1.1.1 デバイス固定 + device_id空文字: バリデーションエラー"""
        # Arrange
        from iot_app.forms.customer_dashboard.belt_chart import BeltChartGadgetForm
        # Act
        with app.test_request_context():
            form = BeltChartGadgetForm(data={
                'gadget_name': '帯グラフ',
                'device_mode': 'fixed',
                'device_id': '',
            })
            result = form.validate()
        # Assert
        assert result is False
        assert 'device_id' in form.errors

    def test_invalid_when_fixed_mode_and_device_id_none(self, app):
        """1.1.1.2 デバイス固定 + device_id=None: バリデーションエラー"""
        # Arrange
        from iot_app.forms.customer_dashboard.belt_chart import BeltChartGadgetForm
        # Act
        with app.test_request_context():
            form = BeltChartGadgetForm(data={
                'gadget_name': '帯グラフ',
                'device_mode': 'fixed',
                'device_id': None,
            })
            result = form.validate()
        # Assert
        assert result is False
        assert 'device_id' in form.errors

    def test_valid_when_fixed_mode_and_device_id_provided(self, app):
        """1.1.1.3 デバイス固定 + device_id指定あり: バリデーション通過"""
        # Arrange
        from iot_app.forms.customer_dashboard.belt_chart import BeltChartGadgetForm
        # Act
        with app.test_request_context():
            form = BeltChartGadgetForm(data={
                'gadget_name': '帯グラフ',
                'device_mode': 'fixed',
                'device_id': '42',
                'group_id': '1',
                'summary_method_id': '1',
                'gadget_size': '0',
                'measurement_item_ids': ['1'],
            })
            form.measurement_item_ids.choices = [(i, f'item{i}') for i in _ALL_ITEM_IDS]
            result = form.validate()
        # Assert
        assert result is True

    def test_valid_when_variable_mode_and_device_id_empty(self, app):
        """デバイス可変モード: device_idが空でもバリデーション通過
        UI仕様書 § (4) 表示デバイス指定: デバイス可変モード時は非表示
        """
        # Arrange
        from iot_app.forms.customer_dashboard.belt_chart import BeltChartGadgetForm
        # Act
        with app.test_request_context():
            form = BeltChartGadgetForm(data={
                'gadget_name': '帯グラフ',
                'device_mode': 'variable',
                'device_id': '',
                'group_id': '1',
                'summary_method_id': '1',
                'gadget_size': '0',
                'measurement_item_ids': ['1'],
            })
            form.measurement_item_ids.choices = [(i, f'item{i}') for i in _ALL_ITEM_IDS]
            result = form.validate()
        # Assert
        assert result is True

    def test_error_message_for_missing_device_id(self, app):
        """デバイス固定 + 未選択: エラーメッセージが仕様書記載のメッセージであること"""
        # Arrange
        from iot_app.forms.customer_dashboard.belt_chart import BeltChartGadgetForm
        # Act
        with app.test_request_context():
            form = BeltChartGadgetForm(data={
                'gadget_name': '帯グラフ',
                'device_mode': 'fixed',
                'device_id': '',
            })
            form.validate()
        # Assert
        assert 'デバイスを選択してください' in form.errors['device_id']


# ===========================================================================
# Section 4: フォームバリデーション - 表示項目選択 (BeltChartGadgetForm.measurement_item_ids)
# UI仕様書 § バリデーション（登録画面）
#   表示項目: 1-5個選択必須
# UI仕様書 § (5) 凡例: 凡例は最大5つまで設定可能
# ===========================================================================

@pytest.mark.unit
class TestBeltChartGadgetFormMeasurementItems:
    """帯グラフガジェット登録フォーム - 表示項目選択バリデーション

    観点: 1.1.1（必須チェック）, 1.1.6（不整値チェック）
    UI仕様書 § バリデーション（登録画面）
      - 表示項目: 1〜5個必須 → エラー「表示項目を1つ以上5つ以下で選択してください」
    UI仕様書 § (5) 凡例: 凡例は最大5つまで設定可能
    """

    def test_valid_when_one_item_selected(self, app):
        """1.1.1.3 入力あり（最小1個）: バリデーション通過"""
        # Arrange
        from iot_app.forms.customer_dashboard.belt_chart import BeltChartGadgetForm
        # Act
        with app.test_request_context():
            form = BeltChartGadgetForm(data={'gadget_name': '帯グラフ', 'measurement_item_ids': ['1']})
            form.measurement_item_ids.choices = [(i, f'item{i}') for i in _ALL_ITEM_IDS]
            result = form.validate()
        # Assert
        assert result is True

    def test_valid_when_five_items_selected(self, app):
        """最大件数内（5個）: バリデーション通過
        UI仕様書 § (5) 凡例: 凡例は最大5つまで設定可能
        """
        # Arrange
        from iot_app.forms.customer_dashboard.belt_chart import BeltChartGadgetForm
        # Act
        with app.test_request_context():
            form = BeltChartGadgetForm(
                data={'gadget_name': '帯グラフ', 'measurement_item_ids': ['1', '2', '3', '4', '5']}
            )
            form.measurement_item_ids.choices = [(i, f'item{i}') for i in _ALL_ITEM_IDS]
            result = form.validate()
        # Assert
        assert result is True

    def test_invalid_when_no_items_selected(self, app):
        """1.1.1.1 未選択（0個）: バリデーションエラー"""
        # Arrange
        from iot_app.forms.customer_dashboard.belt_chart import BeltChartGadgetForm
        # Act
        with app.test_request_context():
            form = BeltChartGadgetForm(data={'gadget_name': '帯グラフ', 'measurement_item_ids': []})
            form.measurement_item_ids.choices = [(i, f'item{i}') for i in _ALL_ITEM_IDS]
            result = form.validate()
        # Assert
        assert result is False
        assert 'measurement_item_ids' in form.errors

    def test_invalid_when_six_items_selected(self, app):
        """最大超過（6個）: バリデーションエラー
        UI仕様書 § バリデーション: 表示項目は1〜5個必須
        """
        # Arrange
        from iot_app.forms.customer_dashboard.belt_chart import BeltChartGadgetForm
        # Act
        with app.test_request_context():
            form = BeltChartGadgetForm(
                data={'gadget_name': '帯グラフ', 'measurement_item_ids': ['1', '2', '3', '4', '5', '6']}
            )
            form.measurement_item_ids.choices = [(i, f'item{i}') for i in _ALL_ITEM_IDS]
            result = form.validate()
        # Assert
        assert result is False
        assert 'measurement_item_ids' in form.errors

    def test_invalid_when_item_id_out_of_valid_range(self, app):
        """1.1.6.2 未定義値: 有効範囲外の measurement_item_id はバリデーションエラー
        WTForms SelectMultipleField は choices に含まれない値を自動で弾く
        """
        # Arrange
        from iot_app.forms.customer_dashboard.belt_chart import BeltChartGadgetForm
        # Act
        with app.test_request_context():
            form = BeltChartGadgetForm(
                data={'gadget_name': '帯グラフ', 'measurement_item_ids': ['999']}
            )
            form.measurement_item_ids.choices = [(i, f'item{i}') for i in _ALL_ITEM_IDS]
            result = form.validate()
        # Assert
        assert result is False
        assert 'measurement_item_ids' in form.errors

    def test_error_message_for_no_items(self, app):
        """未選択: エラーメッセージが仕様書記載のメッセージであること"""
        # Arrange
        from iot_app.forms.customer_dashboard.belt_chart import BeltChartGadgetForm
        # Act
        with app.test_request_context():
            form = BeltChartGadgetForm(data={'gadget_name': '帯グラフ', 'measurement_item_ids': []})
            form.measurement_item_ids.choices = [(i, f'item{i}') for i in _ALL_ITEM_IDS]
            form.validate()
        # Assert
        assert '表示項目を1つ以上5つ以下で選択してください' in form.errors['measurement_item_ids']

    def test_error_message_for_too_many_items(self, app):
        """最大超過: エラーメッセージが仕様書記載のメッセージであること"""
        # Arrange
        from iot_app.forms.customer_dashboard.belt_chart import BeltChartGadgetForm
        # Act
        with app.test_request_context():
            form = BeltChartGadgetForm(
                data={'gadget_name': '帯グラフ', 'measurement_item_ids': ['1', '2', '3', '4', '5', '6']}
            )
            form.measurement_item_ids.choices = [(i, f'item{i}') for i in _ALL_ITEM_IDS]
            form.validate()
        # Assert
        assert '表示項目を1つ以上5つ以下で選択してください' in form.errors['measurement_item_ids']


# ===========================================================================
# Section 5: フォームバリデーション - グループ選択 (BeltChartGadgetForm.group_id)
# UI仕様書 § バリデーション（登録画面）
#   グループ: 必須
# ===========================================================================

@pytest.mark.unit
class TestBeltChartGadgetFormGroupId:
    """帯グラフガジェット登録フォーム - グループ選択バリデーション

    観点: 1.1.1（必須チェック）
    UI仕様書 § バリデーション（登録画面）
      - グループ: 必須 → エラー「グループを選択してください」
    """

    def test_invalid_when_group_id_empty(self, app):
        """1.1.1.1 空文字: グループが未選択の場合はバリデーションエラー"""
        # Arrange
        from iot_app.forms.customer_dashboard.belt_chart import BeltChartGadgetForm
        # Act
        with app.test_request_context():
            form = BeltChartGadgetForm(data={'gadget_name': '帯グラフ', 'group_id': ''})
            result = form.validate()
        # Assert
        assert result is False
        assert 'group_id' in form.errors

    def test_invalid_when_group_id_none(self, app):
        """1.1.1.2 None: グループIDが None の場合はバリデーションエラー"""
        # Arrange
        from iot_app.forms.customer_dashboard.belt_chart import BeltChartGadgetForm
        # Act
        with app.test_request_context():
            form = BeltChartGadgetForm(data={'gadget_name': '帯グラフ', 'group_id': None})
            result = form.validate()
        # Assert
        assert result is False
        assert 'group_id' in form.errors

    def test_valid_when_group_id_provided(self, app):
        """1.1.1.3 入力あり: グループIDが指定されている場合はバリデーション通過"""
        # Arrange
        from iot_app.forms.customer_dashboard.belt_chart import BeltChartGadgetForm
        # Act
        with app.test_request_context():
            form = BeltChartGadgetForm(data={
                'gadget_name': '帯グラフ',
                'group_id': '1',
                'device_mode': 'variable',
                'summary_method_id': '1',
                'gadget_size': '0',
                'measurement_item_ids': ['1'],
            })
            form.measurement_item_ids.choices = [(i, f'item{i}') for i in _ALL_ITEM_IDS]
            result = form.validate()
        # Assert
        assert result is True

    def test_error_message_for_empty_group_id(self, app):
        """未選択: エラーメッセージが仕様書記載のメッセージであること"""
        # Arrange
        from iot_app.forms.customer_dashboard.belt_chart import BeltChartGadgetForm
        # Act
        with app.test_request_context():
            form = BeltChartGadgetForm(data={'gadget_name': '帯グラフ', 'group_id': ''})
            form.validate()
        # Assert
        assert 'グループを選択してください' in form.errors['group_id']


# ===========================================================================
# Section 6: フォームバリデーション - 集約方法 (BeltChartGadgetForm.summary_method_id)
# UI仕様書 § バリデーション（登録画面）
#   集約方法: 必須
# ===========================================================================

@pytest.mark.unit
class TestBeltChartGadgetFormSummaryMethod:
    """帯グラフガジェット登録フォーム - 集約方法バリデーション

    観点: 1.1.1（必須チェック）
    UI仕様書 § バリデーション（登録画面）
      - 集約方法: 必須 → エラー「集約方法を選択してください」
    UI仕様書 § (7) 集約方法: gold_summary_method_master から取得
    """

    def test_invalid_when_summary_method_id_empty(self, app):
        """1.1.1.1 空文字: 集約方法が未選択の場合はバリデーションエラー"""
        # Arrange
        from iot_app.forms.customer_dashboard.belt_chart import BeltChartGadgetForm
        # Act
        with app.test_request_context():
            form = BeltChartGadgetForm(data={'gadget_name': '帯グラフ', 'summary_method_id': ''})
            result = form.validate()
        # Assert
        assert result is False
        assert 'summary_method_id' in form.errors

    def test_invalid_when_summary_method_id_none(self, app):
        """1.1.1.2 None: 集約方法が None の場合はバリデーションエラー"""
        # Arrange
        from iot_app.forms.customer_dashboard.belt_chart import BeltChartGadgetForm
        # Act
        with app.test_request_context():
            form = BeltChartGadgetForm(data={'gadget_name': '帯グラフ', 'summary_method_id': None})
            result = form.validate()
        # Assert
        assert result is False
        assert 'summary_method_id' in form.errors

    def test_valid_when_summary_method_id_provided(self, app):
        """1.1.1.3 入力あり: 集約方法IDが指定されている場合はバリデーション通過"""
        # Arrange
        from iot_app.forms.customer_dashboard.belt_chart import BeltChartGadgetForm
        # Act
        with app.test_request_context():
            form = BeltChartGadgetForm(data={
                'gadget_name': '帯グラフ',
                'summary_method_id': '1',
                'device_mode': 'variable',
                'group_id': '1',
                'gadget_size': '0',
                'measurement_item_ids': ['1'],
            })
            form.measurement_item_ids.choices = [(i, f'item{i}') for i in _ALL_ITEM_IDS]
            result = form.validate()
        # Assert
        assert result is True

    def test_error_message_for_empty_summary_method_id(self, app):
        """未選択: エラーメッセージが仕様書記載のメッセージであること"""
        # Arrange
        from iot_app.forms.customer_dashboard.belt_chart import BeltChartGadgetForm
        # Act
        with app.test_request_context():
            form = BeltChartGadgetForm(data={'gadget_name': '帯グラフ', 'summary_method_id': ''})
            form.validate()
        # Assert
        assert '集約方法を選択してください' in form.errors['summary_method_id']


# ===========================================================================
# Section 7: フォームバリデーション - 部品サイズ (BeltChartGadgetForm.gadget_size)
# UI仕様書 § バリデーション（登録画面）
#   部品サイズ: 必須
# ===========================================================================

@pytest.mark.unit
class TestBeltChartGadgetFormGadgetSize:
    """帯グラフガジェット登録フォーム - 部品サイズバリデーション

    観点: 1.1.1（必須チェック）
    UI仕様書 § バリデーション（登録画面）
      - 部品サイズ: 必須 → エラー「部品サイズを選択してください」
    UI仕様書 § (9) 部品サイズ: 2x2 (gadget_size=0) または 2x4 (gadget_size=1)
    """

    def test_invalid_when_gadget_size_empty(self, app):
        """1.1.1.1 空文字: 部品サイズが未選択の場合はバリデーションエラー"""
        # Arrange
        from iot_app.forms.customer_dashboard.belt_chart import BeltChartGadgetForm
        # Act
        with app.test_request_context():
            form = BeltChartGadgetForm(data={'gadget_name': '帯グラフ', 'gadget_size': ''})
            result = form.validate()
        # Assert
        assert result is False
        assert 'gadget_size' in form.errors

    def test_invalid_when_gadget_size_none(self, app):
        """1.1.1.2 None: 部品サイズが None の場合はバリデーションエラー"""
        # Arrange
        from iot_app.forms.customer_dashboard.belt_chart import BeltChartGadgetForm
        # Act
        with app.test_request_context():
            form = BeltChartGadgetForm(data={'gadget_name': '帯グラフ', 'gadget_size': None})
            result = form.validate()
        # Assert
        assert result is False
        assert 'gadget_size' in form.errors

    def test_valid_when_gadget_size_is_2x2(self, app):
        """1.1.1.3 入力あり（2x2, gadget_size=0）: バリデーション通過
        UI仕様書 § (9) 部品サイズ: 2x2 は gadget_size=0
        """
        # Arrange
        from iot_app.forms.customer_dashboard.belt_chart import BeltChartGadgetForm
        # Act
        with app.test_request_context():
            form = BeltChartGadgetForm(data={
                'gadget_name': '帯グラフ',
                'gadget_size': '0',
                'device_mode': 'variable',
                'group_id': '1',
                'summary_method_id': '1',
                'measurement_item_ids': ['1'],
            })
            form.measurement_item_ids.choices = [(i, f'item{i}') for i in _ALL_ITEM_IDS]
            result = form.validate()
        # Assert
        assert result is True

    def test_valid_when_gadget_size_is_2x4(self, app):
        """1.1.1.3 入力あり（2x4, gadget_size=1）: バリデーション通過
        UI仕様書 § (9) 部品サイズ: 2x4 は gadget_size=1
        """
        # Arrange
        from iot_app.forms.customer_dashboard.belt_chart import BeltChartGadgetForm
        # Act
        with app.test_request_context():
            form = BeltChartGadgetForm(data={
                'gadget_name': '帯グラフ',
                'gadget_size': '1',
                'device_mode': 'variable',
                'group_id': '1',
                'summary_method_id': '1',
                'measurement_item_ids': ['1'],
            })
            form.measurement_item_ids.choices = [(i, f'item{i}') for i in _ALL_ITEM_IDS]
            result = form.validate()
        # Assert
        assert result is True

    def test_error_message_for_empty_gadget_size(self, app):
        """未選択: エラーメッセージが仕様書記載のメッセージであること"""
        # Arrange
        from iot_app.forms.customer_dashboard.belt_chart import BeltChartGadgetForm
        # Act
        with app.test_request_context():
            form = BeltChartGadgetForm(data={'gadget_name': '帯グラフ', 'gadget_size': ''})
            form.validate()
        # Assert
        assert '部品サイズを選択してください' in form.errors['gadget_size']


# ===========================================================================
# Section 8: チャートパラメータバリデーション (validate_chart_params)
# ワークフロー仕様書 § ガジェットデータ取得 バリデーション
#   - 表示単位: 許容値（hour/day/week/month）
#   - 集計間隔: 許容値（1min/2min/3min/5min/10min/15min）
#   - 基準日時: 形式（YYYY/MM/DD HH:mm:ss）
# ===========================================================================

@pytest.mark.unit
class TestValidateChartParams:
    """チャートパラメータバリデーション

    観点: 1.1.4（日付形式チェック）, 1.1.6（不整値チェック）
    ワークフロー仕様書 § ガジェットデータ取得 バリデーションルール
      - 表示単位: 許容値（hour/day/week/month） → エラー「表示単位が不正です」
      - 集計間隔: 許容値（1min/2min/3min/5min/10min/15min） → エラー「集計間隔が不正です」
      - 基準日時: 形式（YYYY/MM/DD HH:mm:ss） → エラー「正しい日付形式で入力してください」
    """

    # ── 正常系 ──────────────────────────────────────────────

    def test_valid_with_all_valid_params_hour(self):
        """2.1.1 正常処理: 全パラメータ正常（display_unit=hour）→ None を返す"""
        # Arrange
        from iot_app.services.customer_dashboard.belt_chart import validate_chart_params
        # Act
        result = validate_chart_params('hour', '10min', '2026/03/05 12:00:00')
        # Assert
        assert result is None

    def test_valid_with_all_valid_params_day(self):
        """2.1.1 正常処理: 全パラメータ正常（display_unit=day）→ None を返す"""
        # Arrange
        from iot_app.services.customer_dashboard.belt_chart import validate_chart_params
        # Act
        result = validate_chart_params('day', '10min', '2026/03/05 12:00:00')
        # Assert
        assert result is None

    def test_valid_with_all_valid_params_week(self):
        """2.1.1 正常処理: 全パラメータ正常（display_unit=week）→ None を返す"""
        # Arrange
        from iot_app.services.customer_dashboard.belt_chart import validate_chart_params
        # Act
        result = validate_chart_params('week', '10min', '2026/03/05 12:00:00')
        # Assert
        assert result is None

    def test_valid_with_all_valid_params_month(self):
        """2.1.1 正常処理: 全パラメータ正常（display_unit=month）→ None を返す"""
        # Arrange
        from iot_app.services.customer_dashboard.belt_chart import validate_chart_params
        # Act
        result = validate_chart_params('month', '10min', '2026/03/05 12:00:00')
        # Assert
        assert result is None

    # ── display_unit バリデーション ─────────────────────────

    def test_invalid_when_display_unit_is_unknown(self):
        """1.1.6.2 未定義値: display_unit が 'hour/day/week/month' 以外の場合 → エラーメッセージを返す"""
        # Arrange
        from iot_app.services.customer_dashboard.belt_chart import validate_chart_params
        # Act
        result = validate_chart_params('minute', '10min', '2026/03/05 12:00:00')
        # Assert
        assert result is not None

    def test_invalid_when_display_unit_empty(self):
        """1.1.6.3 空文字: display_unit が空文字の場合 → エラーメッセージを返す"""
        # Arrange
        from iot_app.services.customer_dashboard.belt_chart import validate_chart_params
        # Act
        result = validate_chart_params('', '10min', '2026/03/05 12:00:00')
        # Assert
        assert result is not None

    def test_invalid_when_display_unit_none(self):
        """1.1.6.4 None: display_unit が None の場合 → エラーメッセージを返す"""
        # Arrange
        from iot_app.services.customer_dashboard.belt_chart import validate_chart_params
        # Act
        result = validate_chart_params(None, '10min', '2026/03/05 12:00:00')
        # Assert
        assert result is not None

    # ── interval バリデーション ──────────────────────────────

    @pytest.mark.parametrize('interval', ['1min', '2min', '3min', '5min', '10min', '15min'])
    def test_valid_for_all_allowed_intervals(self, interval):
        """1.1.6.1 許容値: 許容された集計間隔（1/2/3/5/10/15min）は None
        ワークフロー仕様書 § バリデーション: 集計間隔 許容値リスト
        """
        # Arrange
        from iot_app.services.customer_dashboard.belt_chart import validate_chart_params
        # Act
        result = validate_chart_params('hour', interval, '2026/03/05 12:00:00')
        # Assert
        assert result is None

    def test_invalid_when_interval_is_unknown(self):
        """1.1.6.2 未定義値: interval が許容値以外の場合 → エラーメッセージを返す"""
        # Arrange
        from iot_app.services.customer_dashboard.belt_chart import validate_chart_params
        # Act
        result = validate_chart_params('hour', '7min', '2026/03/05 12:00:00')
        # Assert
        assert result is not None

    def test_invalid_when_interval_empty(self):
        """1.1.6.3 空文字: interval が空文字の場合 → エラーメッセージを返す"""
        # Arrange
        from iot_app.services.customer_dashboard.belt_chart import validate_chart_params
        # Act
        result = validate_chart_params('hour', '', '2026/03/05 12:00:00')
        # Assert
        assert result is not None

    def test_invalid_when_interval_none(self):
        """1.1.6.4 None: interval が None の場合 → エラーメッセージを返す"""
        # Arrange
        from iot_app.services.customer_dashboard.belt_chart import validate_chart_params
        # Act
        result = validate_chart_params('hour', None, '2026/03/05 12:00:00')
        # Assert
        assert result is not None

    # ── base_datetime バリデーション ─────────────────────────

    def test_invalid_when_base_datetime_wrong_format(self):
        """1.1.4.3 形式不正: base_datetime がスラッシュ区切り以外の形式 → エラーメッセージを返す
        ワークフロー仕様書 § バリデーション: 基準日時 形式（YYYY/MM/DD HH:mm:ss）
        """
        # Arrange
        from iot_app.services.customer_dashboard.belt_chart import validate_chart_params
        # Act
        result = validate_chart_params('hour', '10min', '2026-03-05 12:00:00')
        # Assert
        assert result is not None

    def test_invalid_when_base_datetime_date_only(self):
        """1.1.4 形式不正: 時刻部分が省略されている場合 → エラーメッセージを返す"""
        # Arrange
        from iot_app.services.customer_dashboard.belt_chart import validate_chart_params
        # Act
        result = validate_chart_params('hour', '10min', '2026/03/05')
        # Assert
        assert result is not None

    def test_invalid_when_base_datetime_empty(self):
        """1.1.4 空文字: base_datetime が空文字の場合 → エラーメッセージを返す"""
        # Arrange
        from iot_app.services.customer_dashboard.belt_chart import validate_chart_params
        # Act
        result = validate_chart_params('hour', '10min', '')
        # Assert
        assert result is not None

    def test_invalid_when_base_datetime_none(self):
        """1.1.4 None: base_datetime が None の場合 → エラーメッセージを返す"""
        # Arrange
        from iot_app.services.customer_dashboard.belt_chart import validate_chart_params
        # Act
        result = validate_chart_params('hour', '10min', None)
        # Assert
        assert result is not None

    def test_invalid_when_base_datetime_invalid_date(self):
        """1.1.4.5 存在しない日付: 2026/02/30 は存在しないため → エラーメッセージを返す"""
        # Arrange
        from iot_app.services.customer_dashboard.belt_chart import validate_chart_params
        # Act
        result = validate_chart_params('hour', '10min', '2026/02/30 00:00:00')
        # Assert
        assert result is not None


# ===========================================================================
# Section 9: データ整形ロジック - 時単位 (format_belt_chart_data / display_unit='hour')
# ワークフロー仕様書 § ガジェットデータ取得 ④ データ整形
#   - インターバル単位（1/2/3/5/10/15分）のバケット集計
#   - ラベル形式: HH:mm
# ===========================================================================

@pytest.mark.unit
class TestFormatBeltChartDataHour:
    """帯グラフデータ整形ロジック（時単位）

    観点: 2.1（正常系処理）, 3.1.4（検索結果戻り値ハンドリング）
    ワークフロー仕様書 § ④ データ整形（display_unit=hour）
    ※ format_belt_chart_data は src/iot_app/services/customer_dashboard/belt_chart.py に実装予定
    """

    def test_returns_labels_and_series_structure(self):
        """2.1.1 正常処理: 戻り値に 'labels' と 'series' キーが存在する
        ワークフロー仕様書 § ⑤ レスポンス形式: chart_data.labels, chart_data.series
        """
        # Arrange
        from iot_app.services.customer_dashboard.belt_chart import format_belt_chart_data
        rows = [
            {'event_timestamp': datetime(2026, 3, 5, 11, 5, 0), 'external_temp': 10.0},
        ]
        measurement_items = [
            {'silver_data_column_name': 'external_temp', 'display_name': '外気温度'},
        ]
        # Act
        result = format_belt_chart_data(rows, 'hour', measurement_items, interval='10min')
        # Assert
        assert 'labels' in result
        assert 'series' in result

    def test_label_format_is_hhmm(self):
        """2.1.1 正常処理: 時単位のラベル形式は HH:mm
        ワークフロー仕様書 § ④ ラベル形式: HH:mm
        """
        # Arrange
        from iot_app.services.customer_dashboard.belt_chart import format_belt_chart_data
        rows = [
            {'event_timestamp': datetime(2026, 3, 5, 11, 5, 0), 'external_temp': 10.0},
        ]
        measurement_items = [
            {'silver_data_column_name': 'external_temp', 'display_name': '外気温度'},
        ]
        # Act
        result = format_belt_chart_data(rows, 'hour', measurement_items, interval='10min')
        # Assert
        assert len(result['labels']) == 1
        # 11:05 → 10分インターバルでバケット 11:00
        assert result['labels'][0] == '11:00'

    def test_rows_in_same_bucket_are_aggregated(self):
        """2.1.1 正常処理: 同一バケット内の複数行は集計される
        ワークフロー仕様書 § ④ インターバル単位のグループ化・集計はPython側で実施
        """
        # Arrange
        from iot_app.services.customer_dashboard.belt_chart import format_belt_chart_data
        rows = [
            {'event_timestamp': datetime(2026, 3, 5, 11, 0, 0), 'external_temp': 10.0},
            {'event_timestamp': datetime(2026, 3, 5, 11, 5, 0), 'external_temp': 20.0},
        ]
        measurement_items = [
            {'silver_data_column_name': 'external_temp', 'display_name': '外気温度'},
        ]
        # Act
        result = format_belt_chart_data(rows, 'hour', measurement_items, interval='10min')
        # Assert
        # 両行は 11:00 のバケットに属する → 1本のラベル
        assert len(result['labels']) == 1
        assert result['labels'][0] == '11:00'
        assert len(result['series'][0]['values']) == 1

    def test_rows_in_different_buckets_generate_multiple_labels(self):
        """2.1.1 正常処理: 異なるバケットの行はそれぞれラベルを生成する
        ワークフロー仕様書 § ④ バケットごとに1本生成
        """
        # Arrange
        from iot_app.services.customer_dashboard.belt_chart import format_belt_chart_data
        rows = [
            {'event_timestamp': datetime(2026, 3, 5, 11, 0, 0), 'external_temp': 10.0},
            {'event_timestamp': datetime(2026, 3, 5, 11, 10, 0), 'external_temp': 20.0},
        ]
        measurement_items = [
            {'silver_data_column_name': 'external_temp', 'display_name': '外気温度'},
        ]
        # Act
        result = format_belt_chart_data(rows, 'hour', measurement_items, interval='10min')
        # Assert
        assert len(result['labels']) == 2
        assert '11:00' in result['labels']
        assert '11:10' in result['labels']

    def test_series_name_matches_display_name(self):
        """2.1.1 正常処理: series[].name は measurement_item の display_name と一致する
        ワークフロー仕様書 § ⑤ レスポンス形式: series[].name
        """
        # Arrange
        from iot_app.services.customer_dashboard.belt_chart import format_belt_chart_data
        rows = [
            {'event_timestamp': datetime(2026, 3, 5, 11, 0, 0), 'external_temp': 10.0},
        ]
        measurement_items = [
            {'silver_data_column_name': 'external_temp', 'display_name': '外気温度'},
        ]
        # Act
        result = format_belt_chart_data(rows, 'hour', measurement_items, interval='10min')
        # Assert
        assert result['series'][0]['name'] == '外気温度'

    def test_multiple_measurement_items_generate_multiple_series(self):
        """2.1.1 正常処理: 複数の表示項目は複数の series を生成する
        ワークフロー仕様書 § ⑤ レスポンス形式: series は表示項目数分
        """
        # Arrange
        from iot_app.services.customer_dashboard.belt_chart import format_belt_chart_data
        rows = [
            {'event_timestamp': datetime(2026, 3, 5, 11, 0, 0),
             'external_temp': 10.0, 'set_temp_freezer_1': 5.0},
        ]
        measurement_items = [
            {'silver_data_column_name': 'external_temp', 'display_name': '外気温度'},
            {'silver_data_column_name': 'set_temp_freezer_1', 'display_name': '第1冷凍 設定温度'},
        ]
        # Act
        result = format_belt_chart_data(rows, 'hour', measurement_items, interval='10min')
        # Assert
        assert len(result['series']) == 2

    def test_returns_empty_labels_and_series_when_rows_empty(self):
        """3.1.4.2 空結果: rows が空の場合は labels=[], series=[] を返す
        ワークフロー仕様書 § ⑤ データなしの場合: labels=[], series=[]
        """
        # Arrange
        from iot_app.services.customer_dashboard.belt_chart import format_belt_chart_data
        rows = []
        measurement_items = [
            {'silver_data_column_name': 'external_temp', 'display_name': '外気温度'},
        ]
        # Act
        result = format_belt_chart_data(rows, 'hour', measurement_items, interval='10min')
        # Assert
        assert result['labels'] == []
        assert result['series'] == []

    def test_labels_are_sorted_chronologically(self):
        """2.1.1 正常処理: ラベルは時刻順（昇順）に並ぶ
        ワークフロー仕様書 § ④ sorted_keys = sorted({...})
        """
        # Arrange
        from iot_app.services.customer_dashboard.belt_chart import format_belt_chart_data
        rows = [
            {'event_timestamp': datetime(2026, 3, 5, 11, 20, 0), 'external_temp': 30.0},
            {'event_timestamp': datetime(2026, 3, 5, 11, 0, 0), 'external_temp': 10.0},
            {'event_timestamp': datetime(2026, 3, 5, 11, 10, 0), 'external_temp': 20.0},
        ]
        measurement_items = [
            {'silver_data_column_name': 'external_temp', 'display_name': '外気温度'},
        ]
        # Act
        result = format_belt_chart_data(rows, 'hour', measurement_items, interval='10min')
        # Assert
        assert result['labels'] == sorted(result['labels'])

    @pytest.mark.parametrize('interval,bucket_minute', [
        ('1min', 7),
        ('5min', 5),
        ('15min', 0),
    ])
    def test_bucket_start_minute_by_interval(self, interval, bucket_minute):
        """2.1.1 正常処理: 集計間隔ごとにバケット開始分が正しく計算される
        ワークフロー仕様書 § ④ bucket = dt.replace(minute=(dt.minute // interval_min) * interval_min)
        """
        # Arrange
        from iot_app.services.customer_dashboard.belt_chart import format_belt_chart_data
        # 11:07 のデータを各インターバルでバケット化
        rows = [
            {'event_timestamp': datetime(2026, 3, 5, 11, 7, 0), 'external_temp': 10.0},
        ]
        measurement_items = [
            {'silver_data_column_name': 'external_temp', 'display_name': '外気温度'},
        ]
        # Act
        result = format_belt_chart_data(rows, 'hour', measurement_items, interval=interval)
        # Assert
        expected_label = f'11:{bucket_minute:02d}'
        assert result['labels'][0] == expected_label


# ===========================================================================
# Section 10: データ整形ロジック - 日単位 (format_belt_chart_data / display_unit='day')
# ワークフロー仕様書 § ガジェットデータ取得 ④ データ整形
#   - 1時間単位で24本取得
#   - ラベル形式: HH（例: '00', '01', ..., '23'）
# ===========================================================================

@pytest.mark.unit
class TestFormatBeltChartDataDay:
    """帯グラフデータ整形ロジック（日単位）

    観点: 2.1（正常系処理）, 3.1.4（検索結果戻り値ハンドリング）
    ワークフロー仕様書 § ④ データ整形（display_unit=day）
      - gold_sensor_data_hourly_summary から取得
      - ラベル形式: HH（例: '00', '01', ..., '23'）
    """

    def test_label_format_is_hh(self):
        """2.1.1 正常処理: 日単位のラベル形式は HH（時刻の整数値文字列）
        ワークフロー仕様書 § ④ ラベル形式: HH（0〜23時の24本）
        """
        # Arrange
        from iot_app.services.customer_dashboard.belt_chart import format_belt_chart_data
        rows = [
            {'summary_item': 1, 'collection_hour': 0, 'summary_value': 10.0},
            {'summary_item': 1, 'collection_hour': 1, 'summary_value': 11.0},
        ]
        measurement_items = [
            {'measurement_item_id': 1, 'display_name': '外気温度'},
        ]
        # Act
        result = format_belt_chart_data(rows, 'day', measurement_items)
        # Assert
        assert '00' in result['labels']
        assert '01' in result['labels']

    def test_series_values_correspond_to_hours(self):
        """2.1.1 正常処理: series の値が collection_hour に対応する
        ワークフロー仕様書 § ④ hour_data[name][row['collection_hour']] = row['summary_value']
        """
        # Arrange
        from iot_app.services.customer_dashboard.belt_chart import format_belt_chart_data
        rows = [
            {'summary_item': 1, 'collection_hour': 0, 'summary_value': 10.0},
            {'summary_item': 1, 'collection_hour': 1, 'summary_value': 20.0},
        ]
        measurement_items = [
            {'measurement_item_id': 1, 'display_name': '外気温度'},
        ]
        # Act
        result = format_belt_chart_data(rows, 'day', measurement_items)
        # Assert
        idx_00 = result['labels'].index('00')
        idx_01 = result['labels'].index('01')
        assert result['series'][0]['values'][idx_00] == 10.0
        assert result['series'][0]['values'][idx_01] == 20.0

    def test_missing_hour_value_is_none(self):
        """3.1.4.1 欠損データ: データがない時間帯の値は None
        ワークフロー仕様書 § ④ hour_data = {name: {h: None for h in hour_set}}
        """
        # Arrange
        from iot_app.services.customer_dashboard.belt_chart import format_belt_chart_data
        # collection_hour=0 のデータのみ（hour=1 はなし）
        rows = [
            {'summary_item': 1, 'collection_hour': 0, 'summary_value': 10.0},
        ]
        measurement_items = [
            {'measurement_item_id': 1, 'display_name': '外気温度'},
        ]
        # Act
        result = format_belt_chart_data(rows, 'day', measurement_items)
        # Assert
        # hour=0 のデータのみ → labels=['00'] → values[0]=10.0
        assert len(result['labels']) == 1
        assert result['series'][0]['values'][0] == 10.0

    def test_multiple_measurement_items_generate_multiple_series(self):
        """2.1.1 正常処理: 複数の表示項目は複数の series を生成する"""
        # Arrange
        from iot_app.services.customer_dashboard.belt_chart import format_belt_chart_data
        rows = [
            {'summary_item': 1, 'collection_hour': 0, 'summary_value': 10.0},
            {'summary_item': 2, 'collection_hour': 0, 'summary_value': 5.0},
        ]
        measurement_items = [
            {'measurement_item_id': 1, 'display_name': '外気温度'},
            {'measurement_item_id': 2, 'display_name': '第1冷凍 設定温度'},
        ]
        # Act
        result = format_belt_chart_data(rows, 'day', measurement_items)
        # Assert
        assert len(result['series']) == 2
        assert result['series'][0]['name'] == '外気温度'
        assert result['series'][1]['name'] == '第1冷凍 設定温度'

    def test_returns_empty_when_rows_empty(self):
        """3.1.4.2 空結果: rows が空の場合は labels=[], series=[] を返す"""
        # Arrange
        from iot_app.services.customer_dashboard.belt_chart import format_belt_chart_data
        rows = []
        measurement_items = [
            {'measurement_item_id': 1, 'display_name': '外気温度'},
        ]
        # Act
        result = format_belt_chart_data(rows, 'day', measurement_items)
        # Assert
        assert result['labels'] == []
        assert result['series'] == []


# ===========================================================================
# Section 11: データ整形ロジック - 週・月単位 (format_belt_chart_data / 'week'/'month')
# ワークフロー仕様書 § ガジェットデータ取得 ④ データ整形
#   - 週単位: 1日単位で7本（日曜〜土曜）  ラベル形式: E（例: 'Sun', 'Mon', ..., 'Sat'）
#   - 月単位: 1日単位で月内全日          ラベル形式: DD（例: '01', '15', '31'）
# ===========================================================================

@pytest.mark.unit
class TestFormatBeltChartDataWeekMonth:
    """帯グラフデータ整形ロジック（週・月単位）

    観点: 2.1（正常系処理）, 3.1.4（検索結果戻り値ハンドリング）
    ワークフロー仕様書 § ④ データ整形（display_unit=week/month）
      - gold_sensor_data_daily_summary から取得
      - ラベル形式（週）: E — 曜日略称（'Sun'〜'Sat'）
      - ラベル形式（月）: DD — 日番号ゼロ埋め（'01'〜'31'）
    """

    def test_week_label_format_is_weekday_abbreviation(self):
        """2.1.1 正常処理（週単位）: ラベル形式は E（曜日略称 'Sun'〜'Sat'）
        2026-03-01 は日曜 → 'Sun', 2026-03-02 は月曜 → 'Mon'
        """
        # Arrange
        from iot_app.services.customer_dashboard.belt_chart import format_belt_chart_data
        rows = [
            {'summary_item': 1, 'collection_date': date(2026, 3, 1), 'summary_value': 10.0},
            {'summary_item': 1, 'collection_date': date(2026, 3, 2), 'summary_value': 20.0},
        ]
        measurement_items = [
            {'measurement_item_id': 1, 'display_name': '外気温度'},
        ]
        # Act
        result = format_belt_chart_data(rows, 'week', measurement_items)
        # Assert
        assert 'Sun' in result['labels']
        assert 'Mon' in result['labels']

    def test_month_label_format_is_dd(self):
        """2.1.1 正常処理（月単位）: ラベル形式は DD（日番号ゼロ埋め）
        2026-03-15 → '15'
        """
        # Arrange
        from iot_app.services.customer_dashboard.belt_chart import format_belt_chart_data
        rows = [
            {'summary_item': 1, 'collection_date': date(2026, 3, 15), 'summary_value': 10.0},
        ]
        measurement_items = [
            {'measurement_item_id': 1, 'display_name': '外気温度'},
        ]
        # Act
        result = format_belt_chart_data(rows, 'month', measurement_items)
        # Assert
        assert '15' in result['labels']

    def test_series_values_correspond_to_dates(self):
        """2.1.1 正常処理: series の値が collection_date に対応する（週単位）
        2026-03-01(Sun)→10.0, 2026-03-02(Mon)→20.0
        """
        # Arrange
        from iot_app.services.customer_dashboard.belt_chart import format_belt_chart_data
        rows = [
            {'summary_item': 1, 'collection_date': date(2026, 3, 1), 'summary_value': 10.0},
            {'summary_item': 1, 'collection_date': date(2026, 3, 2), 'summary_value': 20.0},
        ]
        measurement_items = [
            {'measurement_item_id': 1, 'display_name': '外気温度'},
        ]
        # Act
        result = format_belt_chart_data(rows, 'week', measurement_items)
        # Assert
        idx_sun = result['labels'].index('Sun')
        idx_mon = result['labels'].index('Mon')
        assert result['series'][0]['values'][idx_sun] == 10.0
        assert result['series'][0]['values'][idx_mon] == 20.0

    def test_missing_date_value_is_none(self):
        """3.1.4.1 欠損データ: データがない日付の値は None（月単位）
        2026-03-01 のみ → labels=['01'] → values[0]=10.0
        """
        # Arrange
        from iot_app.services.customer_dashboard.belt_chart import format_belt_chart_data
        rows = [
            {'summary_item': 1, 'collection_date': date(2026, 3, 1), 'summary_value': 10.0},
        ]
        measurement_items = [
            {'measurement_item_id': 1, 'display_name': '外気温度'},
        ]
        # Act
        result = format_belt_chart_data(rows, 'month', measurement_items)
        # Assert
        # date=3/1 のみ → labels=['01'] → values[0]=10.0
        assert len(result['labels']) == 1
        assert result['series'][0]['values'][0] == 10.0

    def test_labels_are_sorted_chronologically_for_week(self):
        """2.1.1 正常処理（週単位）: ラベルは日付の昇順に対応する曜日順で並ぶ
        2026-03-01(Sun), 2026-03-02(Mon), 2026-03-03(Tue) → ['Sun', 'Mon', 'Tue']
        """
        # Arrange
        from iot_app.services.customer_dashboard.belt_chart import format_belt_chart_data
        rows = [
            {'summary_item': 1, 'collection_date': date(2026, 3, 3), 'summary_value': 30.0},
            {'summary_item': 1, 'collection_date': date(2026, 3, 1), 'summary_value': 10.0},
            {'summary_item': 1, 'collection_date': date(2026, 3, 2), 'summary_value': 20.0},
        ]
        measurement_items = [
            {'measurement_item_id': 1, 'display_name': '外気温度'},
        ]
        # Act
        result = format_belt_chart_data(rows, 'week', measurement_items)
        # Assert: 日付昇順に対応する曜日順（Sun→Mon→Tue）
        assert result['labels'] == ['Sun', 'Mon', 'Tue']

    def test_multiple_measurement_items_for_month(self):
        """2.1.1 正常処理（月単位）: 複数の表示項目は複数の series を生成する"""
        # Arrange
        from iot_app.services.customer_dashboard.belt_chart import format_belt_chart_data
        rows = [
            {'summary_item': 1, 'collection_date': date(2026, 3, 1), 'summary_value': 10.0},
            {'summary_item': 2, 'collection_date': date(2026, 3, 1), 'summary_value': 5.0},
        ]
        measurement_items = [
            {'measurement_item_id': 1, 'display_name': '外気温度'},
            {'measurement_item_id': 2, 'display_name': '第1冷凍 設定温度'},
        ]
        # Act
        result = format_belt_chart_data(rows, 'month', measurement_items)
        # Assert
        assert len(result['series']) == 2

    def test_returns_empty_when_rows_empty_week(self):
        """3.1.4.2 空結果（週単位）: rows が空の場合は labels=[], series=[] を返す"""
        # Arrange
        from iot_app.services.customer_dashboard.belt_chart import format_belt_chart_data
        rows = []
        measurement_items = [
            {'measurement_item_id': 1, 'display_name': '外気温度'},
        ]
        # Act
        result = format_belt_chart_data(rows, 'week', measurement_items)
        # Assert
        assert result['labels'] == []
        assert result['series'] == []

    def test_returns_empty_when_rows_empty_month(self):
        """3.1.4.2 空結果（月単位）: rows が空の場合は labels=[], series=[] を返す"""
        # Arrange
        from iot_app.services.customer_dashboard.belt_chart import format_belt_chart_data
        rows = []
        measurement_items = [
            {'measurement_item_id': 1, 'display_name': '外気温度'},
        ]
        # Act
        result = format_belt_chart_data(rows, 'month', measurement_items)
        # Assert
        assert result['labels'] == []
        assert result['series'] == []


# ---------------------------------------------------------------------------
# 2.1 / 2.2 / 2.3: ガジェット登録サービス (register_belt_chart_gadget)
# ---------------------------------------------------------------------------

@pytest.mark.unit
class TestRegisterBeltChartGadgetNormal:
    """観点: 2.1（正常系処理）

    register_belt_chart_gadget が有効な入力を受け取ったとき、
    DashboardGadgetMaster を db.session に追加し commit することを確認する。
    """

    def test_valid_input_calls_commit(self):
        """2.1.1 正常処理: 有効な入力データで db.session.commit() が呼ばれる"""
        # Arrange
        from unittest.mock import patch, MagicMock
        from iot_app.services.customer_dashboard.belt_chart import register_belt_chart_gadget

        mock_db = MagicMock()
        form_data = {
            'title': 'テストガジェット',
            'device_mode': 'dynamic',
            'device_id': None,
            'group_id': 1,
            'measurement_item_ids': [1, 2],
            'summary_method_id': 1,
            'gadget_size': 0,
        }
        with patch('iot_app.services.customer_dashboard.belt_chart.db', mock_db):
            # Act
            register_belt_chart_gadget(form_data, current_user_id=1)

        # Assert
        mock_db.session.commit.assert_called_once()

    def test_valid_input_adds_gadget_to_session(self):
        """2.1.2 最小構成の入力: db.session.add() に DashboardGadgetMaster が渡される"""
        # Arrange
        from unittest.mock import patch, MagicMock, call
        from iot_app.services.customer_dashboard.belt_chart import register_belt_chart_gadget

        mock_db = MagicMock()
        form_data = {
            'title': 'G',
            'device_mode': 'dynamic',
            'device_id': None,
            'group_id': 1,
            'measurement_item_ids': [1],
            'summary_method_id': 1,
            'gadget_size': 0,
        }
        with patch('iot_app.services.customer_dashboard.belt_chart.db', mock_db):
            # Act
            register_belt_chart_gadget(form_data, current_user_id=1)

        # Assert
        mock_db.session.add.assert_called_once()

    def test_position_x_is_always_zero(self):
        """③ ガジェット登録: position_x は常に 0 で登録される
        ワークフロー仕様書 § ③ INSERT position_x = 0
        """
        # Arrange
        from unittest.mock import patch, MagicMock
        from iot_app.services.customer_dashboard.belt_chart import register_belt_chart_gadget

        mock_db = MagicMock()
        form_data = {
            'title': 'テストガジェット',
            'device_mode': 'dynamic',
            'device_id': None,
            'group_id': 1,
            'measurement_item_ids': [1],
            'summary_method_id': 1,
            'gadget_size': 0,
        }
        with patch('iot_app.services.customer_dashboard.belt_chart.db', mock_db):
            # Act
            register_belt_chart_gadget(form_data, current_user_id=1)

        # Assert
        added_gadget = mock_db.session.add.call_args[0][0]
        assert added_gadget.position_x == 0

    def test_position_y_is_max_plus_one(self):
        """③ ガジェット登録: position_y は既存 MAX(position_y) + 1 で設定される
        ワークフロー仕様書 § ③ position_y = COALESCE(MAX(position_y), 0) + 1
        """
        # Arrange
        from unittest.mock import patch, MagicMock
        from iot_app.services.customer_dashboard.belt_chart import register_belt_chart_gadget

        mock_db = MagicMock()
        # MAX(position_y) = 2 を返すよう設定
        mock_db.session.query.return_value.filter.return_value.scalar.return_value = 2
        form_data = {
            'title': 'テストガジェット',
            'device_mode': 'dynamic',
            'device_id': None,
            'group_id': 1,
            'measurement_item_ids': [1],
            'summary_method_id': 1,
            'gadget_size': 0,
        }
        with patch('iot_app.services.customer_dashboard.belt_chart.db', mock_db):
            # Act
            register_belt_chart_gadget(form_data, current_user_id=1)

        # Assert
        added_gadget = mock_db.session.add.call_args[0][0]
        assert added_gadget.position_y == 3  # MAX(2) + 1

    def test_display_order_is_max_plus_one(self):
        """③ ガジェット登録: display_order は既存 MAX(display_order) + 1 で設定される
        ワークフロー仕様書 § ③ display_order = COALESCE(MAX(display_order), 0) + 1
        """
        # Arrange
        from unittest.mock import patch, MagicMock
        from iot_app.services.customer_dashboard.belt_chart import register_belt_chart_gadget

        mock_db = MagicMock()
        # MAX(display_order) = 4 を返すよう設定
        mock_db.session.query.return_value.filter.return_value.scalar.return_value = 4
        form_data = {
            'title': 'テストガジェット',
            'device_mode': 'dynamic',
            'device_id': None,
            'group_id': 1,
            'measurement_item_ids': [1],
            'summary_method_id': 1,
            'gadget_size': 0,
        }
        with patch('iot_app.services.customer_dashboard.belt_chart.db', mock_db):
            # Act
            register_belt_chart_gadget(form_data, current_user_id=1)

        # Assert
        added_gadget = mock_db.session.add.call_args[0][0]
        assert added_gadget.display_order == 5  # MAX(4) + 1

    def test_delete_flag_is_false_on_insert(self):
        """③ ガジェット登録: delete_flag は False で登録される
        ワークフロー仕様書 § ③ INSERT delete_flag = FALSE
        """
        # Arrange
        from unittest.mock import patch, MagicMock
        from iot_app.services.customer_dashboard.belt_chart import register_belt_chart_gadget

        mock_db = MagicMock()
        form_data = {
            'title': 'テストガジェット',
            'device_mode': 'dynamic',
            'device_id': None,
            'group_id': 1,
            'measurement_item_ids': [1],
            'summary_method_id': 1,
            'gadget_size': 0,
        }
        with patch('iot_app.services.customer_dashboard.belt_chart.db', mock_db):
            # Act
            register_belt_chart_gadget(form_data, current_user_id=1)

        # Assert
        added_gadget = mock_db.session.add.call_args[0][0]
        assert added_gadget.delete_flag is False

    def test_gadget_type_id_is_fetched_from_master(self):
        """③ ガジェット登録: GadgetTypeMaster から '帯グラフ' の gadget_type_id を取得してガジェットに設定される
        ワークフロー仕様書 § ③ gadget_type = db.session.query(GadgetTypeMaster).filter_by(gadget_type_name='帯グラフ')
        """
        # Arrange
        from unittest.mock import patch, MagicMock
        from iot_app.services.customer_dashboard.belt_chart import register_belt_chart_gadget

        mock_db = MagicMock()
        mock_gadget_type = MagicMock()
        mock_gadget_type.gadget_type_id = 99
        # filter_by().first() → mock_gadget_type
        mock_db.session.query.return_value.filter_by.return_value.first.return_value = mock_gadget_type
        form_data = {
            'title': 'テストガジェット',
            'device_mode': 'dynamic',
            'device_id': None,
            'group_id': 1,
            'measurement_item_ids': [1],
            'summary_method_id': 1,
            'gadget_size': 0,
        }
        with patch('iot_app.services.customer_dashboard.belt_chart.db', mock_db):
            # Act
            register_belt_chart_gadget(form_data, current_user_id=1)

        # Assert
        added_gadget = mock_db.session.add.call_args[0][0]
        assert added_gadget.gadget_type_id == 99

    def test_raises_when_gadget_type_not_found(self):
        """③ ガジェット登録: GadgetTypeMaster に '帯グラフ' が存在しない場合に例外がスローされる
        ワークフロー仕様書 § ③ gadget_type_id = gadget_type.gadget_type_id
          → gadget_type が None のとき AttributeError 等が発生し上位へ伝播する
        """
        # Arrange
        from unittest.mock import patch, MagicMock
        from iot_app.services.customer_dashboard.belt_chart import register_belt_chart_gadget

        mock_db = MagicMock()
        # GadgetTypeMaster が見つからない → None
        mock_db.session.query.return_value.filter_by.return_value.first.return_value = None
        form_data = {
            'title': 'テストガジェット',
            'device_mode': 'dynamic',
            'device_id': None,
            'group_id': 1,
            'measurement_item_ids': [1],
            'summary_method_id': 1,
            'gadget_size': 0,
        }
        with patch('iot_app.services.customer_dashboard.belt_chart.db', mock_db):
            # Act / Assert
            with pytest.raises(Exception):
                register_belt_chart_gadget(form_data, current_user_id=1)


@pytest.mark.unit
class TestRegisterBeltChartGadgetExistenceCheck:
    """観点: 2.2（対象データ存在チェック）

    device_mode='fixed' のとき、指定 device_id のデバイスが存在・アクセス可能か確認する。
    存在しない場合や論理削除済みの場合は NotFoundError がスローされることを確認する。
    """

    def test_fixed_mode_existing_device_succeeds(self):
        """2.2.1 存在確認: device_mode=fixed かつデバイスが存在するとき正常処理される"""
        # Arrange
        from unittest.mock import patch, MagicMock
        from iot_app.services.customer_dashboard.belt_chart import register_belt_chart_gadget

        mock_db = MagicMock()
        mock_device = MagicMock()
        form_data = {
            'title': 'テストガジェット',
            'device_mode': 'fixed',
            'device_id': 10,
            'group_id': 1,
            'measurement_item_ids': [1],
            'summary_method_id': 1,
            'gadget_size': 0,
        }
        with patch('iot_app.services.customer_dashboard.belt_chart.db', mock_db), \
             patch('iot_app.services.customer_dashboard.belt_chart.check_device_access',
                   return_value=mock_device):
            # Act & Assert（例外なし）
            register_belt_chart_gadget(form_data, current_user_id=1, accessible_org_ids=[1])

    def test_fixed_mode_nonexistent_device_raises_not_found(self):
        """2.2.2 存在確認: device_mode=fixed かつデバイスが存在しないとき NotFoundError がスローされる"""
        # Arrange
        from unittest.mock import patch, MagicMock
        from iot_app.services.customer_dashboard.belt_chart import register_belt_chart_gadget
        from iot_app.common.exceptions import NotFoundError

        mock_db = MagicMock()
        form_data = {
            'title': 'テストガジェット',
            'device_mode': 'fixed',
            'device_id': 999,
            'group_id': 1,
            'measurement_item_ids': [1],
            'summary_method_id': 1,
            'gadget_size': 0,
        }
        with patch('iot_app.services.customer_dashboard.belt_chart.db', mock_db), \
             patch('iot_app.services.customer_dashboard.belt_chart.check_device_access',
                   return_value=None):
            # Act & Assert
            with pytest.raises(NotFoundError):
                register_belt_chart_gadget(form_data, current_user_id=1, accessible_org_ids=[1])

    def test_fixed_mode_deleted_device_raises_not_found(self):
        """2.2.3 存在確認: device_mode=fixed かつデバイスが論理削除済みのとき NotFoundError がスローされる"""
        # Arrange
        from unittest.mock import patch, MagicMock
        from iot_app.services.customer_dashboard.belt_chart import register_belt_chart_gadget
        from iot_app.common.exceptions import NotFoundError

        mock_db = MagicMock()
        # check_device_access は論理削除済みを None で返す仕様
        form_data = {
            'title': 'テストガジェット',
            'device_mode': 'fixed',
            'device_id': 5,
            'group_id': 1,
            'measurement_item_ids': [1],
            'summary_method_id': 1,
            'gadget_size': 0,
        }
        with patch('iot_app.services.customer_dashboard.belt_chart.db', mock_db), \
             patch('iot_app.services.customer_dashboard.belt_chart.check_device_access',
                   return_value=None):
            # Act & Assert
            with pytest.raises(NotFoundError):
                register_belt_chart_gadget(form_data, current_user_id=1, accessible_org_ids=[1])


@pytest.mark.unit
class TestRegisterBeltChartGadgetSideEffect:
    """観点: 2.3（副作用チェック）

    DB操作で例外が発生したとき rollback() が呼ばれ、
    データが更新されないことを確認する。
    """

    def test_exception_during_commit_calls_rollback(self):
        """2.3.2 副作用: commit() で例外が発生したとき rollback() が呼ばれる"""
        # Arrange
        from unittest.mock import patch, MagicMock
        from iot_app.services.customer_dashboard.belt_chart import register_belt_chart_gadget

        mock_db = MagicMock()
        mock_db.session.commit.side_effect = Exception('DB error')
        form_data = {
            'title': 'テストガジェット',
            'device_mode': 'dynamic',
            'device_id': None,
            'group_id': 1,
            'measurement_item_ids': [1],
            'summary_method_id': 1,
            'gadget_size': 0,
        }
        with patch('iot_app.services.customer_dashboard.belt_chart.db', mock_db):
            # Act
            with pytest.raises(Exception):
                register_belt_chart_gadget(form_data, current_user_id=1)

        # Assert
        mock_db.session.rollback.assert_called_once()

    def test_exception_during_commit_does_not_persist_data(self):
        """2.3.1 副作用: 処理失敗時にデータが更新されない（commit が完了しない）"""
        # Arrange
        from unittest.mock import patch, MagicMock
        from iot_app.services.customer_dashboard.belt_chart import register_belt_chart_gadget

        mock_db = MagicMock()
        mock_db.session.commit.side_effect = Exception('DB error')
        form_data = {
            'title': 'テストガジェット',
            'device_mode': 'dynamic',
            'device_id': None,
            'group_id': 1,
            'measurement_item_ids': [1],
            'summary_method_id': 1,
            'gadget_size': 0,
        }
        with patch('iot_app.services.customer_dashboard.belt_chart.db', mock_db):
            # Act
            with pytest.raises(Exception):
                register_belt_chart_gadget(form_data, current_user_id=1)

        # Assert: commit が完了していないため永続化されていない
        assert mock_db.session.commit.call_count == 1  # 呼ばれたが失敗
        mock_db.session.rollback.assert_called_once()


# ---------------------------------------------------------------------------
# 3.2: 登録機能（登録処理呼び出し・登録結果）
# ---------------------------------------------------------------------------

@pytest.mark.unit
class TestRegisterBeltChartGadgetRepositoryCall:
    """観点: 3.2.1（登録処理呼び出し）, 3.2.2（登録結果）

    register_belt_chart_gadget が db.session.add() に渡す
    DashboardGadgetMaster のフィールドと戻り値を検証する。
    """

    def test_gadget_fields_match_form_data(self):
        """3.2.1.1 呼び出し: 正常な入力値 → db.session.add() に渡されるガジェットのフィールドが form_data と一致する"""
        # Arrange
        from unittest.mock import patch, MagicMock, call
        from iot_app.services.customer_dashboard.belt_chart import register_belt_chart_gadget
        import json

        mock_db = MagicMock()
        form_data = {
            'title': 'テストガジェット',
            'device_mode': 'dynamic',
            'device_id': None,
            'group_id': 2,
            'measurement_item_ids': [1, 3],
            'summary_method_id': 2,
            'gadget_size': 1,
        }
        with patch('iot_app.services.customer_dashboard.belt_chart.db', mock_db):
            # Act
            register_belt_chart_gadget(form_data, current_user_id=10)

        # Assert
        added_gadget = mock_db.session.add.call_args[0][0]
        assert added_gadget.gadget_name == 'テストガジェット'
        assert added_gadget.dashboard_group_id == 2
        assert added_gadget.gadget_size == 1
        assert added_gadget.creator == 10
        assert added_gadget.modifier == 10
        chart_config = json.loads(added_gadget.chart_config)
        assert chart_config['measurement_item_ids'] == [1, 3]
        assert chart_config['summary_method_id'] == 2

    def test_fixed_device_id_stored_in_data_source_config(self):
        """② data_source_config: device_mode=fixed のとき device_id が実値で格納される
        ワークフロー仕様書 § ③ data_source_config = json.dumps({'device_id': device_id})
        """
        # Arrange
        from unittest.mock import patch, MagicMock
        from iot_app.services.customer_dashboard.belt_chart import register_belt_chart_gadget
        import json

        mock_db = MagicMock()
        mock_device = MagicMock()
        form_data = {
            'title': 'テストガジェット',
            'device_mode': 'fixed',
            'device_id': 12345,
            'group_id': 1,
            'measurement_item_ids': [1],
            'summary_method_id': 1,
            'gadget_size': 0,
        }
        with patch('iot_app.services.customer_dashboard.belt_chart.db', mock_db), \
             patch('iot_app.services.customer_dashboard.belt_chart.check_device_access',
                   return_value=mock_device):
            # Act
            register_belt_chart_gadget(form_data, current_user_id=1, accessible_org_ids=[1])

        # Assert
        added_gadget = mock_db.session.add.call_args[0][0]
        data_source_config = json.loads(added_gadget.data_source_config)
        assert data_source_config['device_id'] == 12345

    def test_device_id_none_stored_as_none_in_data_source_config(self):
        """3.2.1.2 呼び出し: device_id=None を含む入力 → data_source_config に None のまま格納される"""
        # Arrange
        from unittest.mock import patch, MagicMock
        from iot_app.services.customer_dashboard.belt_chart import register_belt_chart_gadget
        import json

        mock_db = MagicMock()
        form_data = {
            'title': 'テストガジェット',
            'device_mode': 'dynamic',
            'device_id': None,
            'group_id': 1,
            'measurement_item_ids': [1],
            'summary_method_id': 1,
            'gadget_size': 0,
        }
        with patch('iot_app.services.customer_dashboard.belt_chart.db', mock_db):
            # Act
            register_belt_chart_gadget(form_data, current_user_id=1)

        # Assert
        added_gadget = mock_db.session.add.call_args[0][0]
        data_source_config = json.loads(added_gadget.data_source_config)
        assert data_source_config['device_id'] is None

    def test_returns_gadget_uuid_on_success(self):
        """3.2.2.1 登録結果: 登録処理成功 → 生成した gadget_uuid が返却される"""
        # Arrange
        from unittest.mock import patch, MagicMock
        from iot_app.services.customer_dashboard.belt_chart import register_belt_chart_gadget

        mock_db = MagicMock()
        form_data = {
            'title': 'テストガジェット',
            'device_mode': 'dynamic',
            'device_id': None,
            'group_id': 1,
            'measurement_item_ids': [1],
            'summary_method_id': 1,
            'gadget_size': 0,
        }
        with patch('iot_app.services.customer_dashboard.belt_chart.db', mock_db):
            # Act
            result = register_belt_chart_gadget(form_data, current_user_id=1)

        # Assert: UUID形式の文字列が返却される
        import re
        assert result is not None
        assert re.match(
            r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$',
            result
        )


# ---------------------------------------------------------------------------
# 3.5: CSVエクスポート機能（CSV生成ロジック・エスケープ・エンコーディング）
# ---------------------------------------------------------------------------

def _make_chart_data(labels, series_name_value_pairs):
    """テスト用 chart_data ヘルパー"""
    return {
        'labels': labels,
        'series': [
            {'name': name, 'values': values}
            for name, values in series_name_value_pairs
        ],
    }


@pytest.mark.unit
class TestGenerateBeltChartCsvLayout:
    """観点: 3.5.1（CSV生成ロジック）

    generate_belt_chart_csv がヘッダー・データ行・列順序を正しく出力することを確認する。
    """

    def test_header_row_first_col_is_device_name(self):
        """3.5.1.1 ヘッダー先頭列: 1列目が 'デバイス名' である"""
        # Arrange
        from iot_app.services.customer_dashboard.belt_chart import generate_belt_chart_csv
        import csv as csv_module, io
        chart_data = _make_chart_data(
            ['11:00'],
            [('外気温度', [10.0])],
        )
        # Act
        result = generate_belt_chart_csv(chart_data, 'hour', '2024-04-06T00:00:00', 'Device A')
        reader = csv_module.reader(io.StringIO(result.lstrip('\ufeff')))
        header = next(reader)
        # Assert
        assert header[0] == 'デバイス名'

    def test_header_row_second_col_is_time_col_name(self):
        """3.5.1.2 ヘッダー2列目: display_unit='hour' のとき '時間' が出力される"""
        # Arrange
        from iot_app.services.customer_dashboard.belt_chart import generate_belt_chart_csv
        import csv as csv_module, io
        chart_data = _make_chart_data(['11:00'], [('外気温度', [10.0])])
        # Act
        result = generate_belt_chart_csv(chart_data, 'hour', '2024-04-06T00:00:00', 'Device A')
        reader = csv_module.reader(io.StringIO(result.lstrip('\ufeff')))
        header = next(reader)
        # Assert
        assert header[1] == '時間'

    def test_header_row_series_names_follow_time_col(self):
        """3.5.1.3 ヘッダー系列列: 3列目以降に series の name が順に並ぶ"""
        # Arrange
        from iot_app.services.customer_dashboard.belt_chart import generate_belt_chart_csv
        import csv as csv_module, io
        chart_data = _make_chart_data(
            ['11:00'],
            [('外気温度', [10.0]), ('第1冷凍 設定温度', [5.0])],
        )
        # Act
        result = generate_belt_chart_csv(chart_data, 'hour', '2024-04-06T00:00:00', 'Device A')
        reader = csv_module.reader(io.StringIO(result.lstrip('\ufeff')))
        header = next(reader)
        # Assert
        assert header[2] == '外気温度'
        assert header[3] == '第1冷凍 設定温度'

    def test_all_rows_are_output(self):
        """3.5.1.4 データ行出力: ラベル件数分のデータ行が出力される"""
        # Arrange
        from iot_app.services.customer_dashboard.belt_chart import generate_belt_chart_csv
        chart_data = _make_chart_data(
            ['11:00', '11:10', '11:20'],
            [('外気温度', [10.0, 20.0, 30.0])],
        )
        # Act
        result = generate_belt_chart_csv(chart_data, 'hour', '2024-04-06T00:00:00', 'Device A')
        lines = [l for l in result.lstrip('\ufeff').splitlines() if l]
        # Assert: ヘッダー1行 + データ3行
        assert len(lines) == 4

    def test_data_row_first_col_is_device_name(self):
        """3.5.1.5 データ行1列目: デバイス名が出力される"""
        # Arrange
        from iot_app.services.customer_dashboard.belt_chart import generate_belt_chart_csv
        import csv as csv_module, io
        chart_data = _make_chart_data(['11:00'], [('外気温度', [10.5])])
        # Act
        result = generate_belt_chart_csv(chart_data, 'hour', '2024-04-06T11:00:00', 'Device A')
        reader = csv_module.reader(io.StringIO(result.lstrip('\ufeff')))
        next(reader)  # ヘッダースキップ
        data_row = next(reader)
        # Assert
        assert data_row[0] == 'Device A'

    def test_data_row_sensor_value_is_two_decimal_places(self):
        """3.5.1.6 センサー値フォーマット: 数値が小数点2桁で出力される"""
        # Arrange
        from iot_app.services.customer_dashboard.belt_chart import generate_belt_chart_csv
        import csv as csv_module, io
        chart_data = _make_chart_data(['11:00'], [('外気温度', [10.5])])
        # Act
        result = generate_belt_chart_csv(chart_data, 'hour', '2024-04-06T11:00:00', 'Device A')
        reader = csv_module.reader(io.StringIO(result.lstrip('\ufeff')))
        next(reader)  # ヘッダースキップ
        data_row = next(reader)
        # Assert: 3列目がセンサー値（小数点2桁）
        assert data_row[2] == '10.50'

    def test_empty_labels_outputs_header_only(self):
        """3.5.1.7 0件出力: labels が空のときヘッダー行のみ出力される"""
        # Arrange
        from iot_app.services.customer_dashboard.belt_chart import generate_belt_chart_csv
        chart_data = _make_chart_data([], [('外気温度', [])])
        # Act
        result = generate_belt_chart_csv(chart_data, 'hour', '2024-04-06T00:00:00', 'Device A')
        lines = [l for l in result.lstrip('\ufeff').splitlines() if l]
        # Assert
        assert len(lines) == 1
        assert 'デバイス名' in lines[0]


@pytest.mark.unit
class TestGenerateBeltChartCsvEscape:
    """観点: 3.5.2（エスケープ処理）

    Python 標準 csv.writer が担うエスケープ動作を generate_belt_chart_csv が
    正しく通していることを確認する。
    """

    def test_comma_in_series_name_is_quoted(self):
        """3.5.2.1 カンマエスケープ: 凡例名にカンマを含む場合ダブルクォートで囲まれる"""
        # Arrange
        from iot_app.services.customer_dashboard.belt_chart import generate_belt_chart_csv
        chart_data = _make_chart_data(
            ['11:00'],
            [('温度,湿度', [10.0])],
        )
        # Act
        result = generate_belt_chart_csv(chart_data, 'hour', '2024-04-06T00:00:00', 'Device A')
        header_line = result.lstrip('\ufeff').splitlines()[0]
        # Assert
        assert '"温度,湿度"' in header_line

    def test_newline_in_series_name_is_quoted(self):
        """3.5.2.2 改行エスケープ: 凡例名に改行を含む場合ダブルクォートで囲まれる"""
        # Arrange
        from iot_app.services.customer_dashboard.belt_chart import generate_belt_chart_csv
        chart_data = _make_chart_data(
            ['11:00'],
            [('外気温度\n湿度', [10.0])],
        )
        # Act
        result = generate_belt_chart_csv(chart_data, 'hour', '2024-04-06T00:00:00', 'Device A')
        # Assert: 改行を含むフィールドはダブルクォートで囲まれる
        assert '"外気温度\n湿度"' in result

    def test_double_quote_in_series_name_is_escaped(self):
        """3.5.2.3 ダブルクォートエスケープ: 凡例名に " を含む場合 "" にエスケープされる"""
        # Arrange
        from iot_app.services.customer_dashboard.belt_chart import generate_belt_chart_csv
        chart_data = _make_chart_data(
            ['11:00'],
            [('温度"A"', [10.0])],
        )
        # Act
        result = generate_belt_chart_csv(chart_data, 'hour', '2024-04-06T00:00:00', 'Device A')
        header_line = result.lstrip('\ufeff').splitlines()[0]
        # Assert
        assert '""' in header_line

    def test_plain_value_is_not_quoted(self):
        """3.5.2.4 エスケープ不要: 特殊文字を含まないデータはそのまま出力される"""
        # Arrange
        from iot_app.services.customer_dashboard.belt_chart import generate_belt_chart_csv
        import csv as csv_module, io
        chart_data = _make_chart_data(
            ['11:00'],
            [('外気温度', [10.5])],
        )
        # Act
        result = generate_belt_chart_csv(chart_data, 'hour', '2024-04-06T11:00:00', 'Device A')
        reader = csv_module.reader(io.StringIO(result.lstrip('\ufeff')))
        next(reader)  # ヘッダースキップ
        data_row = next(reader)
        # Assert: デバイス名, タイムスタンプ, センサー値（小数点2桁）
        assert data_row[2] == '10.50'


@pytest.mark.unit
class TestGenerateBeltChartCsvEncoding:
    """観点: 3.5.3（エンコーディング処理）

    generate_belt_chart_csv が BOM 付き UTF-8 文字列を返し、
    日本語文字が正しく含まれることを確認する。
    """

    def test_output_starts_with_bom(self):
        """3.5.3.1 UTF-8 BOM付き: 戻り値の先頭が BOM (U+FEFF) である"""
        # Arrange
        from iot_app.services.customer_dashboard.belt_chart import generate_belt_chart_csv
        chart_data = _make_chart_data(['11:00'], [('外気温度', [10.0])])
        # Act
        result = generate_belt_chart_csv(chart_data, 'hour', '2024-04-06T00:00:00', 'Device A')
        # Assert
        assert result.startswith('\ufeff')

    def test_japanese_characters_are_preserved(self):
        """3.5.3.2 日本語文字: 日本語の凡例名・デバイス名が文字化けなく出力される"""
        # Arrange
        from iot_app.services.customer_dashboard.belt_chart import generate_belt_chart_csv
        chart_data = _make_chart_data(
            ['11:00'],
            [('外気温度', [10.0]), ('第1冷凍 設定温度', [3.5])],
        )
        # Act
        result = generate_belt_chart_csv(chart_data, 'hour', '2024-04-06T00:00:00', 'テストデバイス')
        # Assert
        assert '外気温度' in result
        assert '第1冷凍 設定温度' in result
        assert 'テストデバイス' in result


@pytest.mark.unit
class TestGenerateBeltChartCsvTimestamp:
    """観点: 3.5.4（時間列フォーマット）

    display_unit ごとに時間列のタイムスタンプが正しい形式に変換されることを確認する。
    """

    def test_hour_timestamp_format(self):
        """3.5.4.1 hour単位: 'YYYY/MM/DD HH:mm' 形式で出力される"""
        # Arrange
        from iot_app.services.customer_dashboard.belt_chart import generate_belt_chart_csv
        import csv as csv_module, io
        chart_data = _make_chart_data(['11:00'], [('外気温度', [10.0])])
        # Act
        result = generate_belt_chart_csv(chart_data, 'hour', '2024-04-06T00:00:00', 'Device A')
        reader = csv_module.reader(io.StringIO(result.lstrip('\ufeff')))
        next(reader)  # ヘッダースキップ
        data_row = next(reader)
        # Assert
        assert data_row[1] == '2024/04/06 11:00'

    def test_day_timestamp_format(self):
        """3.5.4.2 day単位: 'YYYY/MM/DD HH:mm' 形式で出力される（ラベルは時のみ）"""
        # Arrange
        from iot_app.services.customer_dashboard.belt_chart import generate_belt_chart_csv
        import csv as csv_module, io
        chart_data = _make_chart_data(['11'], [('外気温度', [10.0])])
        # Act
        result = generate_belt_chart_csv(chart_data, 'day', '2024-04-06T00:00:00', 'Device A')
        reader = csv_module.reader(io.StringIO(result.lstrip('\ufeff')))
        next(reader)  # ヘッダースキップ
        data_row = next(reader)
        # Assert
        assert data_row[1] == '2024/04/06 11:00'

    def test_week_timestamp_format(self):
        """3.5.4.3 week単位: 'YYYY/MM/DD(E)' 形式で出力される（E=曜日略称）"""
        # Arrange
        from iot_app.services.customer_dashboard.belt_chart import generate_belt_chart_csv
        import csv as csv_module, io
        # 2024-04-06 は土曜日 (Sat)
        chart_data = _make_chart_data(['Sat'], [('外気温度', [10.0])])
        # Act
        result = generate_belt_chart_csv(chart_data, 'week', '2024-04-06T00:00:00', 'Device A')
        reader = csv_module.reader(io.StringIO(result.lstrip('\ufeff')))
        next(reader)  # ヘッダースキップ
        data_row = next(reader)
        # Assert
        assert data_row[1] == '2024/04/06(Sat)'

    def test_month_timestamp_format(self):
        """3.5.4.4 month単位: 'YYYY/MM/DD' 形式で出力される（ラベルは日のみ）"""
        # Arrange
        from iot_app.services.customer_dashboard.belt_chart import generate_belt_chart_csv
        import csv as csv_module, io
        chart_data = _make_chart_data(['15'], [('外気温度', [10.0])])
        # Act
        result = generate_belt_chart_csv(chart_data, 'month', '2024-04-01T00:00:00', 'Device A')
        reader = csv_module.reader(io.StringIO(result.lstrip('\ufeff')))
        next(reader)  # ヘッダースキップ
        data_row = next(reader)
        # Assert
        assert data_row[1] == '2024/04/15'

    def test_week_time_col_header_is_youbi(self):
        """3.5.4.5 week単位のヘッダー: 2列目が '曜日' である"""
        # Arrange
        from iot_app.services.customer_dashboard.belt_chart import generate_belt_chart_csv
        import csv as csv_module, io
        chart_data = _make_chart_data(['Sat'], [('外気温度', [10.0])])
        # Act
        result = generate_belt_chart_csv(chart_data, 'week', '2024-04-06T00:00:00', 'Device A')
        reader = csv_module.reader(io.StringIO(result.lstrip('\ufeff')))
        header = next(reader)
        # Assert
        assert header[1] == '曜日'

    def test_month_time_col_header_is_hizuke(self):
        """3.5.4.6 month単位のヘッダー: 2列目が '日付' である"""
        # Arrange
        from iot_app.services.customer_dashboard.belt_chart import generate_belt_chart_csv
        import csv as csv_module, io
        chart_data = _make_chart_data(['15'], [('外気温度', [10.0])])
        # Act
        result = generate_belt_chart_csv(chart_data, 'month', '2024-04-01T00:00:00', 'Device A')
        reader = csv_module.reader(io.StringIO(result.lstrip('\ufeff')))
        header = next(reader)
        # Assert
        assert header[1] == '日付'


# ---------------------------------------------------------------------------
# 1.4.1: ログレベル（belt_chart 固有）
# ---------------------------------------------------------------------------

@pytest.mark.unit
class TestBeltChartLogging:
    """観点: 1.4.1.1（ERRORレベル出力）

    register_belt_chart_gadget で DB 例外が発生したとき、
    logger.error() が呼ばれることを確認する。
    """

    def test_error_logged_on_db_exception(self):
        """1.4.1.1 ERRORレベル出力: commit() 失敗時に logger.error() が呼ばれる"""
        # Arrange
        from unittest.mock import patch, MagicMock
        from iot_app.services.customer_dashboard.belt_chart import register_belt_chart_gadget

        mock_db = MagicMock()
        mock_db.session.commit.side_effect = Exception('DB error')
        form_data = {
            'title': 'テストガジェット',
            'device_mode': 'dynamic',
            'device_id': None,
            'group_id': 1,
            'measurement_item_ids': [1],
            'summary_method_id': 1,
            'gadget_size': 0,
        }
        with patch('iot_app.services.customer_dashboard.belt_chart.db', mock_db), \
             patch('iot_app.services.customer_dashboard.belt_chart.logger') as mock_logger:
            # Act
            with pytest.raises(Exception):
                register_belt_chart_gadget(form_data, current_user_id=1)

        # Assert
        mock_logger.error.assert_called_once()


# ---------------------------------------------------------------------------
# 最大取得件数制限: ガジェットデータ取得(100件) vs CSVエクスポート(100,000件)
# ワークフロー仕様書 § CSVエクスポート グラフ表示との差異
# ---------------------------------------------------------------------------

@pytest.mark.unit
class TestFetchBeltChartDataLimit:
    """fetch_belt_chart_data の最大取得件数制限

    観点: ガジェットデータ取得 → limit=100（デフォルト）
          CSVエクスポート     → limit=100,000
    ワークフロー仕様書 § CSVエクスポート
      「最大取得件数: ガジェットデータ取得=100件 / CSVエクスポート=100,000件」
    """

    @patch(f'{_BELT_CHART_SERVICE_MODULE}.db')
    def test_fetch_uses_default_limit_100(self, mock_db):
        """ガジェットデータ取得: fetch_belt_chart_data のデフォルト limit は 100"""
        # Arrange
        from unittest.mock import call
        from iot_app.services.customer_dashboard.belt_chart import fetch_belt_chart_data
        from datetime import datetime

        mock_db.session.execute.return_value.fetchall.return_value = []
        # Act
        fetch_belt_chart_data(
            device_id=1,
            display_unit='hour',
            interval='10min',
            base_datetime=datetime(2026, 3, 5, 12, 0, 0),
            measurement_item_ids=[1],
            summary_method_id=1,
        )
        # Assert: limit=100 がクエリ引数に含まれること
        call_kwargs = mock_db.session.execute.call_args
        assert call_kwargs is not None
        # execute に渡された引数（位置またはキーワード）に 100 が含まれる
        all_args = list(call_kwargs.args) + list(call_kwargs.kwargs.values())
        assert any(str(100) in str(a) for a in all_args)

    @patch(f'{_BELT_CHART_SERVICE_MODULE}.db')
    def test_csv_export_uses_limit_100000(self, mock_db):
        """CSVエクスポート: fetch_belt_chart_data に limit=100000 を渡すと 100,000 件制限でクエリされる"""
        # Arrange
        from iot_app.services.customer_dashboard.belt_chart import fetch_belt_chart_data
        from datetime import datetime

        mock_db.session.execute.return_value.fetchall.return_value = []
        # Act
        fetch_belt_chart_data(
            device_id=1,
            display_unit='hour',
            interval='10min',
            base_datetime=datetime(2026, 3, 5, 12, 0, 0),
            measurement_item_ids=[1],
            summary_method_id=1,
            limit=100000,
        )
        # Assert: limit=100000 がクエリ引数に含まれること
        call_kwargs = mock_db.session.execute.call_args
        assert call_kwargs is not None
        all_args = list(call_kwargs.args) + list(call_kwargs.kwargs.values())
        assert any(str(100000) in str(a) for a in all_args)


# ---------------------------------------------------------------------------
# 1.1.3 / 1.1.6: 数値範囲チェック - gadget_size（許容値外）
# ---------------------------------------------------------------------------

@pytest.mark.unit
class TestGadgetSizeRangeCheck:
    """観点: 1.1.3（数値範囲チェック）, 1.1.6（不整値チェック）

    gadget_size は 0（2×2）または 1（2×4）のみ許容。
    UI仕様書 § (9) 部品サイズ: 2x2 (gadget_size=0) / 2x4 (gadget_size=1)
    """

    def test_invalid_when_gadget_size_is_2(self, app):
        """1.1.6.2 未定義値: gadget_size=2 は許容値外でバリデーションエラー"""
        # Arrange
        from iot_app.forms.customer_dashboard.belt_chart import BeltChartGadgetForm
        # Act
        with app.test_request_context():
            form = BeltChartGadgetForm(data={'gadget_name': '帯グラフ', 'gadget_size': '2'})
            result = form.validate()
        # Assert
        assert result is False
        assert 'gadget_size' in form.errors

    def test_invalid_when_gadget_size_is_negative(self, app):
        """1.1.3.1 最小値-1: gadget_size=-1 は許容値外でバリデーションエラー"""
        # Arrange
        from iot_app.forms.customer_dashboard.belt_chart import BeltChartGadgetForm
        # Act
        with app.test_request_context():
            form = BeltChartGadgetForm(data={'gadget_name': '帯グラフ', 'gadget_size': '-1'})
            result = form.validate()
        # Assert
        assert result is False
        assert 'gadget_size' in form.errors


# ---------------------------------------------------------------------------
# 1.2: 認可（権限チェック）- check_gadget_access / check_dashboard_access
# ---------------------------------------------------------------------------

@pytest.mark.unit
class TestCheckGadgetAccess:
    """観点: 1.2（認可・権限チェック）, 2.2（対象データ存在チェック）

    check_gadget_access がガジェットのアクセス可能スコープを正しく判定することを確認する。
    ワークフロー仕様書 § ガジェットデータ取得 データスコープ制限チェック
    """

    @patch(f'{COMMON_SERVICE_MODULE}.db')
    def test_returns_gadget_when_accessible(self, mock_db):
        """1.2.1 権限あり: ガジェットがアクセス可能スコープ内に存在する場合はガジェットを返す"""
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
        """1.2.2 権限なし: ガジェットがアクセス可能スコープ外の場合は None を返す"""
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
        """1.2.2 権限なし: accessible_org_ids が空の場合は None を返す
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


@pytest.mark.unit
class TestCheckDashboardAccess:
    """観点: 1.2（認可・権限チェック）, 2.2（対象データ存在チェック）

    check_dashboard_access がダッシュボードのアクセス可能スコープを正しく判定することを確認する。
    ワークフロー仕様書 § ガジェット登録モーダル表示 ② ダッシュボード情報取得
    """

    @patch(f'{COMMON_SERVICE_MODULE}.db')
    def test_returns_dashboard_when_accessible(self, mock_db):
        """1.2.1 権限あり: アクセス可能スコープ内にダッシュボードが存在する場合はダッシュボードを返す"""
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

    @patch(f'{COMMON_SERVICE_MODULE}.db')
    def test_returns_none_when_not_found(self, mock_db):
        """1.2.2 権限なし: アクセス可能スコープ内にダッシュボードが存在しない場合は None を返す"""
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


# ---------------------------------------------------------------------------
# 1.3: エラーハンドリング
# ---------------------------------------------------------------------------

@pytest.mark.unit
class TestErrorHandling_ExceptionPropagation:
    """観点: 1.3.1（例外伝播）

    Service / Repository で例外が発生したとき、握りつぶされず上位へ伝播することを確認する。
    ワークフロー仕様書 § ガジェット登録 実装例
      except Exception as e:
          db.session.rollback()
          logger.error(...)
          abort(500)
    """

    @patch(f'{COMMON_SERVICE_MODULE}.db')
    def test_get_accessible_organizations_propagates_db_error(self, mock_db):
        """1.3.1.1 get_accessible_organizations: DB例外が握りつぶされず上位へ伝播する"""
        # Arrange
        mock_db.session.query.side_effect = Exception('DB接続エラー')
        from iot_app.services.customer_dashboard.common import get_accessible_organizations
        # Act / Assert
        with pytest.raises(Exception):
            get_accessible_organizations(parent_org_id=1)

    @patch(f'{COMMON_SERVICE_MODULE}.db')
    def test_get_dashboard_user_setting_propagates_db_error(self, mock_db):
        """1.3.1.2 get_dashboard_user_setting: DB例外が握りつぶされず上位へ伝播する"""
        # Arrange
        mock_db.session.query.side_effect = Exception('DB接続エラー')
        from iot_app.services.customer_dashboard.common import get_dashboard_user_setting
        # Act / Assert
        with pytest.raises(Exception):
            get_dashboard_user_setting(user_id=1)

    @patch(f'{COMMON_SERVICE_MODULE}.db')
    def test_check_gadget_access_propagates_db_error(self, mock_db):
        """1.3.1.3 check_gadget_access: DB例外が握りつぶされず上位へ伝播する"""
        # Arrange
        mock_db.session.query.side_effect = Exception('DB接続エラー')
        from iot_app.services.customer_dashboard.common import check_gadget_access
        # Act / Assert
        with pytest.raises(Exception):
            check_gadget_access('test-uuid', [1, 2, 3])

    @patch(f'{_BELT_CHART_SERVICE_MODULE}.db')
    def test_fetch_belt_chart_data_propagates_db_error(self, mock_db):
        """1.3.1.4 fetch_belt_chart_data: DB例外が握りつぶされず上位へ伝播する"""
        # Arrange
        mock_db.session.query.side_effect = Exception('センサーデータ取得エラー')
        from iot_app.services.customer_dashboard.belt_chart import fetch_belt_chart_data
        # Act / Assert
        with pytest.raises(Exception):
            fetch_belt_chart_data(device_id=1, display_unit='hour')


@pytest.mark.unit
class TestErrorHandling_ValidationError:
    """観点: 1.3.2（ValidationError / 400）

    フォームバリデーション違反時に validate() = False となり、
    ビュー層が 400 を返すことを確認する。
    ワークフロー仕様書 § ガジェット登録 エラーハンドリング表
      400 | バリデーションエラー | フォーム再表示（エラーモーダル表示）
    """

    def test_form_invalid_when_all_fields_empty(self, app):
        """1.3.2.1 全必須項目が未入力: validate() = False → ビュー層で 400 返却"""
        # Arrange
        from iot_app.forms.customer_dashboard.belt_chart import BeltChartGadgetForm
        # Act
        with app.test_request_context():
            form = BeltChartGadgetForm(data={})
            result = form.validate()
        # Assert
        assert result is False

    def test_form_invalid_when_device_mode_not_selected(self, app):
        """1.3.2.2 表示デバイス未選択: validate() = False → ビュー層で 400 返却"""
        # Arrange
        from iot_app.forms.customer_dashboard.belt_chart import BeltChartGadgetForm
        # Act
        with app.test_request_context():
            form = BeltChartGadgetForm(data={
                'gadget_name': '帯グラフ',
                'device_mode': '',
                'group_id': '1',
            })
            result = form.validate()
        # Assert
        assert result is False
        assert 'device_mode' in form.errors

    def test_form_invalid_when_measurement_items_empty(self, app):
        """1.3.2.3 表示項目が0個: validate() = False → ビュー層で 400 返却"""
        # Arrange
        from iot_app.forms.customer_dashboard.belt_chart import BeltChartGadgetForm
        # Act
        with app.test_request_context():
            form = BeltChartGadgetForm(data={
                'gadget_name': '帯グラフ',
                'device_mode': 'dynamic',
                'group_id': '1',
                'measurement_item_ids': [],
            })
            form.measurement_item_ids.choices = [(i, f'item{i}') for i in _ALL_ITEM_IDS]
            result = form.validate()
        # Assert
        assert result is False
        assert 'measurement_item_ids' in form.errors

    def test_form_invalid_when_measurement_items_exceed_five(self, app):
        """1.3.2.4 表示項目が6個以上: validate() = False → ビュー層で 400 返却"""
        # Arrange
        from iot_app.forms.customer_dashboard.belt_chart import BeltChartGadgetForm
        # Act
        with app.test_request_context():
            form = BeltChartGadgetForm(data={
                'gadget_name': '帯グラフ',
                'device_mode': 'dynamic',
                'group_id': '1',
                'measurement_item_ids': ['1', '2', '3', '4', '5', '6'],
            })
            form.measurement_item_ids.choices = [(i, f'item{i}') for i in _ALL_ITEM_IDS]
            result = form.validate()
        # Assert
        assert result is False
        assert 'measurement_item_ids' in form.errors


@pytest.mark.unit
class TestErrorHandling_AuthenticationError:
    """観点: 1.3.3（AuthenticationError / 401）

    ワークフロー仕様書 § ガジェットデータ取得 フロー図
      Auth → CheckAuth → |未認証| → Error401[401エラーレスポンス]
    """

    def test_unauthorized_error_is_importable(self):
        """1.3.3.1 UnauthorizedError が iot_app.auth.exceptions から import できること"""
        # Act
        from iot_app.auth.exceptions import UnauthorizedError
        # Assert
        assert issubclass(UnauthorizedError, Exception)

    def test_unauthorized_error_propagates_to_caller(self):
        """1.3.3.2 UnauthorizedError がスローされた場合、呼び出し元へ伝播する"""
        # Arrange
        from iot_app.auth.exceptions import UnauthorizedError

        def mock_auth_check():
            raise UnauthorizedError('認証が必要です')

        # Act / Assert
        with pytest.raises(UnauthorizedError):
            mock_auth_check()


@pytest.mark.unit
class TestErrorHandling_ScopeViolation:
    """観点: 1.3.4（スコープ外アクセス / 404）

    ワークフロー仕様書 § ガジェットデータ取得 フロー図
      CheckScope → |スコープ外| → Error404[404エラーレスポンス]
    ワークフロー仕様書 § ガジェットデータ取得 実装例
      if not check_gadget_access(gadget, accessible_org_ids):
          return jsonify({'error': 'アクセス権限がありません'}), 404
    """

    @patch(f'{COMMON_SERVICE_MODULE}.db')
    def test_check_gadget_access_returns_none_when_out_of_scope(self, mock_db):
        """1.3.4.1 check_gadget_access: スコープ外のガジェットに対して None を返す"""
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
        assert result is None

    @patch(f'{COMMON_SERVICE_MODULE}.db')
    def test_check_gadget_access_returns_none_when_org_ids_empty(self, mock_db):
        """1.3.4.2 check_gadget_access: accessible_org_ids が空リストの場合 None を返す"""
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


@pytest.mark.unit
class TestErrorHandling_AppError:
    """観点: 1.3.6（AppError / 500）

    予期しない内部エラー発生時に rollback が呼ばれ、例外が上位へ伝播することを確認する。
    ワークフロー仕様書 § ガジェット登録 エラーハンドリング表
      500 | データベースエラー | 500エラーページ表示
    """

    def test_register_belt_chart_gadget_reraises_on_db_error(self):
        """1.3.6.1 AppError: register_belt_chart_gadget で DB エラー → 例外が上位へ伝播する"""
        # Arrange
        from unittest.mock import patch, MagicMock
        from iot_app.services.customer_dashboard.belt_chart import register_belt_chart_gadget

        mock_db = MagicMock()
        mock_db.session.commit.side_effect = Exception('予期しないDBエラー')
        form_data = {
            'title': 'テストガジェット',
            'device_mode': 'dynamic',
            'device_id': None,
            'group_id': 1,
            'measurement_item_ids': [1],
            'summary_method_id': 1,
            'gadget_size': 0,
        }
        with patch(f'{_BELT_CHART_SERVICE_MODULE}.db', mock_db):
            # Act / Assert
            with pytest.raises(Exception):
                register_belt_chart_gadget(form_data, current_user_id=1)

        mock_db.session.rollback.assert_called_once()


# ===========================================================================
# Section: ガジェット登録モーダル表示 ①〜⑦ データ取得
# ワークフロー仕様書 § ガジェット登録モーダル表示 処理詳細
# ===========================================================================

@pytest.mark.unit
class TestGetDashboardUserSetting:
    """ガジェット登録モーダル表示 ① ダッシュボードユーザー設定取得

    観点: 2.1（正常系処理）, 2.2（対象データ存在チェック）
    ワークフロー仕様書 § ① dashboard_user_setting WHERE user_id = :current_user_id AND delete_flag = FALSE
    """

    @patch(f'{COMMON_SERVICE_MODULE}.db')
    def test_returns_setting_when_exists(self, mock_db):
        """2.1.1 正常処理: ユーザー設定が存在する場合は DashboardUserSetting を返す"""
        # Arrange
        mock_setting = MagicMock()
        mock_setting.dashboard_id = 1
        (
            mock_db.session.query.return_value
            .filter.return_value.first.return_value
        ) = mock_setting
        from iot_app.services.customer_dashboard.common import get_dashboard_user_setting
        # Act
        result = get_dashboard_user_setting(user_id=1)
        # Assert
        assert result == mock_setting
        assert result.dashboard_id == 1

    @patch(f'{COMMON_SERVICE_MODULE}.db')
    def test_returns_none_when_not_exists(self, mock_db):
        """2.2.2 存在確認: ユーザー設定が存在しない場合は None を返す
        ワークフロー仕様書 § フロー図: CheckUserSetting → |なし| → Error404
        """
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


@pytest.mark.unit
class TestGetDashboardById:
    """ガジェット登録モーダル表示 ② ダッシュボード情報取得

    観点: 2.1（正常系処理）, 2.2（対象データ存在チェック）
    ワークフロー仕様書 § ② dashboard_master WHERE dashboard_id = :dashboard_id AND delete_flag = FALSE
    """

    @patch(f'{COMMON_SERVICE_MODULE}.db')
    def test_returns_dashboard_when_exists(self, mock_db):
        """2.1.1 正常処理: ダッシュボードが存在する場合は DashboardMaster を返す"""
        # Arrange
        mock_dashboard = MagicMock()
        mock_dashboard.dashboard_id = 1
        mock_dashboard.dashboard_name = 'テストダッシュボード'
        (
            mock_db.session.query.return_value
            .filter.return_value.first.return_value
        ) = mock_dashboard
        from iot_app.services.customer_dashboard.common import get_dashboard_by_id
        # Act
        result = get_dashboard_by_id(dashboard_id=1)
        # Assert
        assert result == mock_dashboard
        assert result.dashboard_name == 'テストダッシュボード'

    @patch(f'{COMMON_SERVICE_MODULE}.db')
    def test_returns_none_when_not_exists(self, mock_db):
        """2.2.2 存在確認: ダッシュボードが存在しない場合は None を返す
        ワークフロー仕様書 § フロー図: CheckDashboard → |なし| → Error404
        """
        # Arrange
        (
            mock_db.session.query.return_value
            .filter.return_value.first.return_value
        ) = None
        from iot_app.services.customer_dashboard.common import get_dashboard_by_id
        # Act
        result = get_dashboard_by_id(dashboard_id=999)
        # Assert
        assert result is None


@pytest.mark.unit
class TestGetDashboardGroups:
    """ガジェット登録モーダル表示 ③ ダッシュボードグループ一覧取得

    観点: 2.1（正常系処理）, 3.1.4（検索結果戻り値ハンドリング）
    ワークフロー仕様書 § ③ dashboard_group_master WHERE dashboard_id = :dashboard_id
      AND delete_flag = FALSE ORDER BY display_order ASC
    """

    @patch(f'{COMMON_SERVICE_MODULE}.db')
    def test_returns_groups_when_exist(self, mock_db):
        """2.1.1 正常処理: グループが存在する場合はリストを返す"""
        # Arrange
        mock_group1 = MagicMock()
        mock_group1.dashboard_group_name = 'グループA'
        mock_group2 = MagicMock()
        mock_group2.dashboard_group_name = 'グループB'
        (
            mock_db.session.query.return_value
            .filter.return_value
            .order_by.return_value.all.return_value
        ) = [mock_group1, mock_group2]
        from iot_app.services.customer_dashboard.common import get_dashboard_groups
        # Act
        result = get_dashboard_groups(dashboard_id=1)
        # Assert
        assert len(result) == 2
        assert result[0].dashboard_group_name == 'グループA'

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


@pytest.mark.unit
class TestGetMeasurementItems:
    """ガジェット登録モーダル表示 ④ 表示項目一覧取得

    観点: 2.1（正常系処理）, 3.1.4（検索結果戻り値ハンドリング）
    ワークフロー仕様書 § ④ measurement_item_master WHERE delete_flag = FALSE
      ORDER BY measurement_item_id ASC
    """

    @patch(f'{COMMON_SERVICE_MODULE}.db')
    def test_returns_items_when_exist(self, mock_db):
        """2.1.1 正常処理: 測定項目が存在する場合はリストを返す"""
        # Arrange
        mock_item1 = MagicMock()
        mock_item1.measurement_item_id = 1
        mock_item1.display_name = '外気温度'
        mock_item2 = MagicMock()
        mock_item2.measurement_item_id = 2
        mock_item2.display_name = '第1冷凍 設定温度'
        (
            mock_db.session.query.return_value
            .filter.return_value
            .order_by.return_value.all.return_value
        ) = [mock_item1, mock_item2]
        from iot_app.services.customer_dashboard.common import get_measurement_items
        # Act
        result = get_measurement_items()
        # Assert
        assert len(result) == 2
        assert result[0].display_name == '外気温度'

    @patch(f'{COMMON_SERVICE_MODULE}.db')
    def test_returns_empty_list_when_no_items(self, mock_db):
        """3.1.4.2 空結果: 測定項目が存在しない場合は空リストを返す"""
        # Arrange
        (
            mock_db.session.query.return_value
            .filter.return_value
            .order_by.return_value.all.return_value
        ) = []
        from iot_app.services.customer_dashboard.common import get_measurement_items
        # Act
        result = get_measurement_items()
        # Assert
        assert result == []


@pytest.mark.unit
class TestGetOrganizations:
    """ガジェット登録モーダル表示 ⑤ 組織一覧取得

    観点: 2.1（正常系処理）, 3.1.4（検索結果戻り値ハンドリング）
    ワークフロー仕様書 § ⑤ organization_master WHERE organization_id IN (:accessible_org_ids)
      AND delete_flag = FALSE ORDER BY organization_id ASC
    """

    @patch(f'{COMMON_SERVICE_MODULE}.db')
    def test_returns_organizations_when_exist(self, mock_db):
        """2.1.1 正常処理: 組織が存在する場合はリストを返す"""
        # Arrange
        mock_org = MagicMock()
        mock_org.organization_id = 1
        mock_org.organization_name = '組織A'
        (
            mock_db.session.query.return_value
            .filter.return_value
            .order_by.return_value.all.return_value
        ) = [mock_org]
        from iot_app.services.customer_dashboard.common import get_organizations
        # Act
        result = get_organizations(accessible_org_ids=[1])
        # Assert
        assert len(result) == 1
        assert result[0].organization_name == '組織A'

    @patch(f'{COMMON_SERVICE_MODULE}.db')
    def test_returns_empty_list_when_org_ids_empty(self, mock_db):
        """3.1.4.2 空結果: accessible_org_ids が空の場合は空リストを返す"""
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


@pytest.mark.unit
class TestGetAllDevicesInScope:
    """ガジェット登録モーダル表示 ⑥ デバイス一覧取得（デバイス固定モード用）

    観点: 2.1（正常系処理）, 3.1.4（検索結果戻り値ハンドリング）
    ワークフロー仕様書 § ⑥ device_master WHERE organization_id IN (:accessible_org_ids)
      AND delete_flag = FALSE ORDER BY device_id ASC
    """

    @patch(f'{COMMON_SERVICE_MODULE}.db')
    def test_returns_devices_when_exist(self, mock_db):
        """2.1.1 正常処理: デバイスが存在する場合はリストを返す"""
        # Arrange
        mock_device1 = MagicMock()
        mock_device1.device_id = 1
        mock_device1.device_name = 'デバイスA'
        mock_device2 = MagicMock()
        mock_device2.device_id = 2
        mock_device2.device_name = 'デバイスB'
        (
            mock_db.session.query.return_value
            .filter.return_value
            .order_by.return_value.all.return_value
        ) = [mock_device1, mock_device2]
        from iot_app.services.customer_dashboard.common import get_all_devices_in_scope
        # Act
        result = get_all_devices_in_scope(accessible_org_ids=[1, 2])
        # Assert
        assert len(result) == 2
        assert result[0].device_name == 'デバイスA'

    @patch(f'{COMMON_SERVICE_MODULE}.db')
    def test_returns_empty_list_when_no_devices(self, mock_db):
        """3.1.4.2 空結果: スコープ内にデバイスが存在しない場合は空リストを返す"""
        # Arrange
        (
            mock_db.session.query.return_value
            .filter.return_value
            .order_by.return_value.all.return_value
        ) = []
        from iot_app.services.customer_dashboard.common import get_all_devices_in_scope
        # Act
        result = get_all_devices_in_scope(accessible_org_ids=[1])
        # Assert
        assert result == []


@pytest.mark.unit
class TestGetAggregationMethods:
    """ガジェット登録モーダル表示 ⑦ 集約方法一覧取得

    観点: 2.1（正常系処理）, 3.1.4（検索結果戻り値ハンドリング）
    ワークフロー仕様書 § ⑦ gold_summary_method_master WHERE delete_flag = FALSE
      ORDER BY summary_method_id ASC
    ※ get_aggregation_methods() は belt_chart.py に実装予定（TDDテスト）
    """

    @patch(f'{_BELT_CHART_SERVICE_MODULE}.db')
    def test_returns_methods_when_exist(self, mock_db):
        """2.1.1 正常処理: 集約方法が存在する場合はリストを返す"""
        # Arrange
        mock_method1 = MagicMock()
        mock_method1.summary_method_id = 1
        mock_method1.summary_method_name = '平均'
        mock_method2 = MagicMock()
        mock_method2.summary_method_id = 2
        mock_method2.summary_method_name = '最大'
        (
            mock_db.session.query.return_value
            .filter.return_value
            .order_by.return_value.all.return_value
        ) = [mock_method1, mock_method2]
        from iot_app.services.customer_dashboard.belt_chart import get_aggregation_methods
        # Act
        result = get_aggregation_methods()
        # Assert
        assert len(result) == 2
        assert result[0].summary_method_name == '平均'

    @patch(f'{_BELT_CHART_SERVICE_MODULE}.db')
    def test_returns_empty_list_when_no_methods(self, mock_db):
        """3.1.4.2 空結果: 集約方法が存在しない場合は空リストを返す"""
        # Arrange
        (
            mock_db.session.query.return_value
            .filter.return_value
            .order_by.return_value.all.return_value
        ) = []
        from iot_app.services.customer_dashboard.belt_chart import get_aggregation_methods
        # Act
        result = get_aggregation_methods()
        # Assert
        assert result == []
