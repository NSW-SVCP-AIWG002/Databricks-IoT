"""
棒グラフガジェット登録フォーム - 単体テスト
対象: src/iot_app/forms/customer_dashboard/bar_chart.py
"""

import pytest
from iot_app.forms.customer_dashboard.bar_chart import BarChartGadgetForm


def _make_form(app, **overrides):
    """バリデーション通過用の最小データ（可変モード）でフォームを生成する

    動的 SelectField（device_id / group_id / summary_method_id / measurement_item_id）は
    ビュー層でリクエスト時に choices を設定するため、ここではダミー choices を注入する。
    """
    data = {
        'title': 'テストガジェット',
        'device_mode': 'variable',
        'device_id': 0,
        'group_id': 1,
        'summary_method_id': 1,
        'measurement_item_id': 1,
        'min_value': 10,
        'max_value': 20,
        'gadget_size': 0,
    }
    data.update(overrides)
    form = BarChartGadgetForm(data=data)
    device_id_val = data['device_id'] if data['device_id'] is not None else 0
    form.device_id.choices = [(device_id_val, '')]
    form.group_id.choices = [(1, 'グループ1')]
    form.summary_method_id.choices = [(1, 'AVG')]
    form.measurement_item_id.choices = [(1, '外気温度')]
    return form

# ---------------------------------------------------------------------------
# タイトルチェック
# ---------------------------------------------------------------------------

@pytest.mark.unit
class TestBarChartGadgetFormTitleValidation:
    """観点: 1.1.1（必須チェック）, 1.1.2（最大文字列長チェック）

    UI仕様書 § バリデーション（ガジェット登録画面）
    title: 必須・最大20文字
    """

    def test_invalid_when_empty(self, app):
        """1.1.1.1 空文字: バリデーションエラー"""
        with app.test_request_context():
            form = _make_form(app, title='')
            assert not form.validate()
            assert 'title' in form.errors
            assert 'タイトルを入力してください' in form.title.errors

    def test_invalid_when_none(self, app):
        """1.1.1.2 None: バリデーションエラー"""
        with app.test_request_context():
            form = _make_form(app, title=None)
            assert not form.validate()
            assert 'title' in form.errors
            assert 'タイトルを入力してください' in form.title.errors

    def test_valid_when_provided(self, app):
        """1.1.1.3 入力あり: バリデーション通過"""
        with app.test_request_context():
            form = _make_form(app, title='棒グラフ')
            assert form.validate()
    
    def test_invalid_when_whitespace_only(self, app):
        """1.1.1.4 空白のみ: DataRequired が strip するためバリデーションエラー"""
        with app.test_request_context():
            form = _make_form(app, title='   ')
            assert not form.validate()
            assert 'title' in form.errors
            assert 'タイトルを入力してください' in form.title.errors
    
    def test_valid_when_19_chars(self, app):
        """1.1.2.1 最大長-1（19文字）: バリデーション通過"""
        with app.test_request_context():
            form = _make_form(app, title='a' * 19)
            assert form.validate()

    def test_valid_when_20_chars(self, app):
        """1.1.2.2 最大長ちょうど（20文字）: バリデーション通過"""
        with app.test_request_context():
            form = _make_form(app, title='a' * 20)
            assert form.validate()

    def test_invalid_when_exceeds_20_chars(self, app):
        """1.1.2.3 最大長+1（21文字）: バリデーションエラー"""
        with app.test_request_context():
            form = _make_form(app, title='a' * 21)
            assert not form.validate()
            assert 'title' in form.errors
            assert 'タイトルは20文字以内で入力してください' in form.title.errors

# ---------------------------------------------------------------------------
# 表示デバイスチェック
# ---------------------------------------------------------------------------

@pytest.mark.unit
class TestBarChartGadgetFormDeviceModeValidation:
    """観点: 1.1.1（必須チェック）

    UI仕様書 § バリデーション（ガジェット登録画面）
    device_mode: 必須（variable or fixed）
    """

    def test_invalid_when_empty(self, app):
        """1.1.1.1 空文字: バリデーションエラー"""
        with app.test_request_context():
            form = _make_form(app, device_mode='')
            assert not form.validate()
            assert 'device_mode' in form.errors
            assert '表示デバイスを選択してください' in form.device_mode.errors

    def test_invalid_when_none(self, app):
        """1.1.1.2 None: バリデーションエラー"""
        with app.test_request_context():
            form = _make_form(app, device_mode=None)
            assert not form.validate()
            assert 'device_mode' in form.errors
            assert '表示デバイスを選択してください' in form.device_mode.errors

    def test_valid_when_provided_fixed(self, app):
        """1.1.1.3 入力あり: バリデーション通過"""
        with app.test_request_context():
            form = _make_form(app, device_mode='fixed', device_id=5)
            assert form.validate()

    def test_valid_when_provided_variable(self, app):
        """1.1.1.3 入力あり: バリデーション通過"""
        with app.test_request_context():
            form = _make_form(app, device_mode='variable')
            assert form.validate()
    
    def test_invalid_when_whitespace_only(self, app):
        """1.1.1.4 空白のみ: DataRequired が strip するためバリデーションエラー"""
        with app.test_request_context():
            form = _make_form(app, device_mode='   ')
            assert not form.validate()
            assert 'device_mode' in form.errors
            assert '表示デバイスを選択してください' in form.device_mode.errors

# ---------------------------------------------------------------------------
# デバイス選択チェック（固定モード時）
# ---------------------------------------------------------------------------

@pytest.mark.unit
class TestBarChartGadgetFormDeviceIdValidation:
    """観点: 1.1.1（必須チェック）

    UI仕様書 § バリデーション（ガジェット登録画面）
    device_id: 必須（デバイス固定モード時のみ）

    NOTE: device_id は Optional() バリデーターを持つため、ブラウザから未送信の場合に
    WTForms が StopValidation を発行し test_xxx メソッドが実行されない。
    そのため validate() オーバーライドで cross-field チェックを実装している。
    """

    def test_invalid_fixed_mode_when_none(self, app):
        """1.1.1.2 None（固定モード）: バリデーションエラー"""
        with app.test_request_context():
            form = _make_form(app, device_mode='fixed', device_id=None)
            assert not form.validate()
            assert 'device_id' in form.errors
            assert 'デバイスを選択してください' in form.device_id.errors

    def test_valid_invalid_fixed_when_provided(self, app):
        """1.1.1.3 入力あり（固定モード）: バリデーション通過"""
        with app.test_request_context():
            form = _make_form(app, device_mode='fixed', device_id=5)
            assert form.validate()
    
    def test_invalid_fixed_mode_when_zero_no_error(self, app):
        """1.1.1.3 None（可変モード）: バリデーション通過"""
        with app.test_request_context():
            form = _make_form(app, device_mode='variable', device_id=None)
            assert form.validate()

# ---------------------------------------------------------------------------
# グループ選択チェック
# ---------------------------------------------------------------------------

@pytest.mark.unit
class TestBarChartGadgetFormGroupIdValidation:
    """観点: 1.1.1（必須チェック）

    UI仕様書 § バリデーション（ガジェット登録画面）
    group_id: 必須
    """

    def test_invalid_when_none(self, app):
        """1.1.1.2 None: バリデーションエラー"""
        with app.test_request_context():
            form = _make_form(app, group_id=None)
            assert not form.validate()
            assert 'group_id' in form.errors
            assert 'グループを選択してください' in form.group_id.errors

    def test_valid_when_provided(self, app):
        """1.1.1.3 入力あり: バリデーション通過"""
        with app.test_request_context():
            form = _make_form(app, group_id=1)
            assert form.validate()

# ---------------------------------------------------------------------------
# 集約方法チェック
# ---------------------------------------------------------------------------

@pytest.mark.unit
class TestBarChartGadgetFormSummaryMethodIdValidation:
    """観点: 1.1.1（必須チェック）

    UI仕様書 § バリデーション（ガジェット登録画面）
    summary_method_id: 必須
    """

    def test_invalid_when_none(self, app):
        """1.1.1.2 None: バリデーションエラー"""
        with app.test_request_context():
            form = _make_form(app, summary_method_id=None)
            assert not form.validate()
            assert 'summary_method_id' in form.errors
            assert '集約方法を選択してください' in form.summary_method_id.errors

    def test_valid_when_provided(self, app):
        """1.1.1.3 入力あり: バリデーション通過"""
        with app.test_request_context():
            form = _make_form(app, summary_method_id=1)
            assert form.validate()

# ---------------------------------------------------------------------------
# 表示項目選択チェック
# ---------------------------------------------------------------------------

@pytest.mark.unit
class TestBarChartGadgetFormMeasurementItemIdValidation:
    """観点: 1.1.1（必須チェック）

    UI仕様書 § バリデーション（ガジェット登録画面）
    measurement_item_id: 必須
    """

    def test_invalid_when_none(self, app):
        """1.1.1.2 None: バリデーションエラー"""
        with app.test_request_context():
            form = _make_form(app, measurement_item_id=None)
            assert not form.validate()
            assert 'measurement_item_id' in form.errors
            assert '表示項目を選択してください' in form.measurement_item_id.errors

    def test_valid_when_provided(self, app):
        """1.1.1.3 入力あり: バリデーション通過"""
        with app.test_request_context():
            form = _make_form(app, measurement_item_id=1)
            assert form.validate()

# ---------------------------------------------------------------------------
# 最小値チェック
# ---------------------------------------------------------------------------

@pytest.mark.unit
class TestBarChartGadgetFormMinAndMaxValueValidation:
    """観点: 1.1.3（数値範囲チェック）

    UI仕様書 § バリデーション（ガジェット登録画面）
    min_value, max_value: 数値範囲チェック
    """

    def test_invalid_when_min_minus_one(self, app):
        """1.1.3.1 最小値より1小さい: バリデーションエラー"""
        with app.test_request_context():
            form = _make_form(app, min_value=10, max_value=9)
            assert not form.validate()
    
    def test_invalid_when_min_equal(self, app):
        """1.1.3.2 最小値ちょうど: バリデーションエラー"""
        with app.test_request_context():
            form = _make_form(app, min_value=10, max_value=10)
            assert not form.validate()

    def test_valid_when_min_plus_one(self, app):
        """1.1.3.3 最小値より1大きい: バリデーション通過"""
        with app.test_request_context():
            form = _make_form(app, min_value=10, max_value=11)
            assert form.validate()

# ---------------------------------------------------------------------------
# 部品サイズチェック
# ---------------------------------------------------------------------------

@pytest.mark.unit
class TestBarChartGadgetFormGadgetSizeValidation:
    """観点: 1.1.6（不整値チェック）

    UI仕様書 § バリデーション（ガジェット登録画面）
    gadget_size: 不整値チェック
    """

    def test_valid_when_zero(self, app):
        """1.1.6.1 許容されたコード値: バリデーション通過"""
        with app.test_request_context():
            form = _make_form(app, gadget_size=0)
            assert form.validate()
    
    def test_valid_when_one(self, app):
        """1.1.6.1 許容されたコード値: バリデーション通過"""
        with app.test_request_context():
            form = _make_form(app, gadget_size=1)
            assert form.validate()

    def test_valid_when_two(self, app):
        """1.1.6.2 許容されていないコード値: バリデーションエラー"""
        with app.test_request_context():
            form = _make_form(app, gadget_size=2)
            assert not form.validate()
            assert 'gadget_size' in form.errors
            assert '部品サイズを選択してください' in form.gadget_size.errors
    
    def test_invalid_when_none(self, app):
        """1.1.6.4 None: バリデーションエラー"""
        with app.test_request_context():
            form = _make_form(app, gadget_size=None)
            assert not form.validate()
            assert 'gadget_size' in form.errors
            assert '部品サイズを選択してください' in form.gadget_size.errors