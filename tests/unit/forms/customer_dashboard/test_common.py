"""
顧客作成ダッシュボード共通フォーム - 単体テスト
対象: src/iot_app/forms/customer_dashboard/common.py
"""

import pytest
from iot_app.forms.customer_dashboard.common import (
    DashboardForm,
    DashboardGroupForm,
    GadgetForm,
)


# ---------------------------------------------------------------------------
# DashboardForm
# ---------------------------------------------------------------------------

@pytest.mark.unit
class TestDashboardForm:
    """観点: 1.1.1（必須チェック）, 1.1.2（最大文字列長チェック）

    UI仕様書 § (11) 登録/更新モーダル バリデーション
    dashboard_name: 必須・最大50文字
    """

    def test_valid_when_name_provided(self, app):
        """1.1.1.3 入力あり: バリデーション通過"""
        with app.test_request_context():
            form = DashboardForm(data={'dashboard_name': 'テストダッシュボード'})
            assert form.validate()

    def test_invalid_when_name_empty(self, app):
        """1.1.1.1 空文字: バリデーションエラー"""
        with app.test_request_context():
            form = DashboardForm(data={'dashboard_name': ''})
            assert not form.validate()
            assert 'dashboard_name' in form.errors

    def test_invalid_when_name_none(self, app):
        """1.1.1.2 None: バリデーションエラー"""
        with app.test_request_context():
            form = DashboardForm(data={'dashboard_name': None})
            assert not form.validate()
            assert 'dashboard_name' in form.errors

    def test_invalid_when_name_whitespace_only(self, app):
        """1.1.1.4 空白のみ: DataRequired が strip するためバリデーションエラー"""
        with app.test_request_context():
            form = DashboardForm(data={'dashboard_name': '   '})
            assert not form.validate()
            assert 'dashboard_name' in form.errors

    def test_valid_when_name_is_49_chars(self, app):
        """1.2.1 最大長-1（49文字）: バリデーション通過"""
        with app.test_request_context():
            form = DashboardForm(data={'dashboard_name': 'a' * 49})
            assert form.validate()

    def test_valid_when_name_is_50_chars(self, app):
        """1.2.2 最大長ちょうど（50文字）: バリデーション通過"""
        with app.test_request_context():
            form = DashboardForm(data={'dashboard_name': 'a' * 50})
            assert form.validate()

    def test_invalid_when_name_exceeds_50_chars(self, app):
        """1.2.3 最大長+1（51文字）: バリデーションエラー"""
        with app.test_request_context():
            form = DashboardForm(data={'dashboard_name': 'a' * 51})
            assert not form.validate()
            assert 'dashboard_name' in form.errors


# ---------------------------------------------------------------------------
# DashboardGroupForm
# ---------------------------------------------------------------------------

@pytest.mark.unit
class TestDashboardGroupForm:
    """観点: 1.1.1（必須チェック）, 1.1.2（最大文字列長チェック）

    UI仕様書 § (11) 登録/更新モーダル バリデーション
    dashboard_group_name: 必須・最大50文字
    """

    def test_valid_when_name_provided(self, app):
        """1.1.1.3 入力あり: バリデーション通過"""
        with app.test_request_context():
            form = DashboardGroupForm(data={'dashboard_group_name': 'テストグループ'})
            assert form.validate()

    def test_invalid_when_name_empty(self, app):
        """1.1.1.1 空文字: バリデーションエラー"""
        with app.test_request_context():
            form = DashboardGroupForm(data={'dashboard_group_name': ''})
            assert not form.validate()
            assert 'dashboard_group_name' in form.errors

    def test_invalid_when_name_none(self, app):
        """1.1.1.2 None: バリデーションエラー"""
        with app.test_request_context():
            form = DashboardGroupForm(data={'dashboard_group_name': None})
            assert not form.validate()
            assert 'dashboard_group_name' in form.errors

    def test_invalid_when_name_whitespace_only(self, app):
        """1.1.1.4 空白のみ: DataRequired が strip するためバリデーションエラー"""
        with app.test_request_context():
            form = DashboardGroupForm(data={'dashboard_group_name': '   '})
            assert not form.validate()
            assert 'dashboard_group_name' in form.errors

    def test_valid_when_name_is_49_chars(self, app):
        """1.2.1 最大長-1（49文字）: バリデーション通過"""
        with app.test_request_context():
            form = DashboardGroupForm(data={'dashboard_group_name': 'a' * 49})
            assert form.validate()

    def test_valid_when_name_is_50_chars(self, app):
        """1.2.2 最大長ちょうど（50文字）: バリデーション通過"""
        with app.test_request_context():
            form = DashboardGroupForm(data={'dashboard_group_name': 'a' * 50})
            assert form.validate()

    def test_invalid_when_name_exceeds_50_chars(self, app):
        """1.2.3 最大長+1（51文字）: バリデーションエラー"""
        with app.test_request_context():
            form = DashboardGroupForm(data={'dashboard_group_name': 'a' * 51})
            assert not form.validate()
            assert 'dashboard_group_name' in form.errors


# ---------------------------------------------------------------------------
# GadgetForm
# ---------------------------------------------------------------------------

@pytest.mark.unit
class TestGadgetForm:
    """観点: 1.1.1（必須チェック）, 1.1.2（最大文字列長チェック）

    UI仕様書 § (11) 登録/更新モーダル バリデーション
    gadget_name: 必須・最大20文字
    """

    def test_valid_when_name_provided(self, app):
        """1.1.1.3 入力あり: バリデーション通過"""
        with app.test_request_context():
            form = GadgetForm(data={'gadget_name': 'テストガジェット'})
            assert form.validate()

    def test_invalid_when_name_empty(self, app):
        """1.1.1.1 空文字: バリデーションエラー"""
        with app.test_request_context():
            form = GadgetForm(data={'gadget_name': ''})
            assert not form.validate()
            assert 'gadget_name' in form.errors

    def test_invalid_when_name_none(self, app):
        """1.1.1.2 None: バリデーションエラー"""
        with app.test_request_context():
            form = GadgetForm(data={'gadget_name': None})
            assert not form.validate()
            assert 'gadget_name' in form.errors

    def test_invalid_when_name_whitespace_only(self, app):
        """1.1.1.4 空白のみ: DataRequired が strip するためバリデーションエラー"""
        with app.test_request_context():
            form = GadgetForm(data={'gadget_name': '   '})
            assert not form.validate()
            assert 'gadget_name' in form.errors

    def test_valid_when_name_is_19_chars(self, app):
        """1.2.1 最大長-1（19文字）: バリデーション通過"""
        with app.test_request_context():
            form = GadgetForm(data={'gadget_name': 'a' * 19})
            assert form.validate()

    def test_valid_when_name_is_20_chars(self, app):
        """1.2.2 最大長ちょうど（20文字）: バリデーション通過"""
        with app.test_request_context():
            form = GadgetForm(data={'gadget_name': 'a' * 20})
            assert form.validate()

    def test_invalid_when_name_exceeds_20_chars(self, app):
        """1.2.3 最大長+1（21文字）: バリデーションエラー"""
        with app.test_request_context():
            form = GadgetForm(data={'gadget_name': 'a' * 21})
            assert not form.validate()
            assert 'gadget_name' in form.errors
