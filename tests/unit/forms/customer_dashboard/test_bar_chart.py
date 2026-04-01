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
        'gadget_size': '2x2',
    }
    data.update(overrides)
    form = BarChartGadgetForm(data=data)
    device_id_val = data['device_id'] if data['device_id'] is not None else 0
    form.device_id.choices = [(0, '選択してください'), (device_id_val, '')]
    form.group_id.choices = [(1, 'グループ1')]
    form.summary_method_id.choices = [(1, 'AVG')]
    form.measurement_item_id.choices = [(1, '外気温度')]
    return form


# ---------------------------------------------------------------------------
# デバイス選択必須チェック（固定モード時）
# ---------------------------------------------------------------------------

@pytest.mark.unit
class TestBarChartGadgetFormDeviceIdValidation:
    """観点: 3.1.2 デバイス選択必須チェック（デバイス固定モード時）

    UI仕様書 § バリデーション: デバイス選択 | 必須（デバイス固定モード時）| 「デバイスを選択してください」

    NOTE: device_id は Optional() バリデーターを持つため、ブラウザから未送信の場合に
    WTForms が StopValidation を発行し validate_xxx メソッドが実行されない。
    そのため validate() オーバーライドで cross-field チェックを実装している。
    """

    def test_fixed_mode_device_id_zero_is_invalid(self, app):
        """3.1.2.1 固定モード + device_id=0（未選択）: バリデーションエラー"""
        with app.test_request_context():
            form = _make_form(app, device_mode='fixed', device_id=0)
            assert not form.validate()
            assert 'device_id' in form.errors
            assert 'デバイスを選択してください' in form.device_id.errors

    def test_fixed_mode_device_id_none_is_invalid(self, app):
        """3.1.2.2 固定モード + device_id 未指定（None）: バリデーションエラー"""
        with app.test_request_context():
            form = _make_form(app, device_mode='fixed', device_id=None)
            assert not form.validate()
            assert 'device_id' in form.errors
            assert 'デバイスを選択してください' in form.device_id.errors

    def test_fixed_mode_device_id_valid_no_error(self, app):
        """3.1.2.3 固定モード + device_id=5（有効値）: device_id にエラーなし"""
        with app.test_request_context():
            form = _make_form(app, device_mode='fixed', device_id=5)
            form.validate()
            assert 'device_id' not in form.errors

    def test_variable_mode_device_id_zero_no_error(self, app):
        """3.1.2.4 可変モード + device_id=0: デバイス選択不要のためエラーなし"""
        with app.test_request_context():
            form = _make_form(app, device_mode='variable', device_id=0)
            form.validate()
            assert 'device_id' not in form.errors
