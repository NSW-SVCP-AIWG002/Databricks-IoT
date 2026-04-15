"""
単体テスト: iot_app.decorators.auth.require_role
"""
import pytest
from types import SimpleNamespace

from flask import g

from iot_app.decorators.auth import require_role


def _make_view(*roles):
    """require_role でラップしたダミービュー関数を返す"""
    @require_role(*roles)
    def view():
        return "ok"
    return view


class TestRequireRole:
    """require_role デコレータのテスト"""

    def test_allowed_role_passes(self, app):
        """許可ロールのユーザーはビュー関数を通過できる"""
        view = _make_view('system_admin', 'management_admin')
        with app.test_request_context('/'):
            g.current_user = SimpleNamespace(user_type_id=1)  # system_admin
            assert view() == "ok"

    def test_another_allowed_role_passes(self, app):
        """複数許可ロールのうち別のロールでも通過できる"""
        view = _make_view('system_admin', 'management_admin')
        with app.test_request_context('/'):
            g.current_user = SimpleNamespace(user_type_id=2)  # management_admin
            assert view() == "ok"

    def test_disallowed_role_is_forbidden(self, app):
        """許可外ロールのユーザーは 403 になる"""
        from werkzeug.exceptions import Forbidden
        view = _make_view('system_admin')
        with app.test_request_context('/'):
            g.current_user = SimpleNamespace(user_type_id=4)  # service_company_user
            with pytest.raises(Forbidden):
                view()

    def test_unknown_user_type_id_is_forbidden(self, app):
        """マッピングにない user_type_id は 403 になる"""
        from werkzeug.exceptions import Forbidden
        view = _make_view('system_admin')
        with app.test_request_context('/'):
            g.current_user = SimpleNamespace(user_type_id=99)
            with pytest.raises(Forbidden):
                view()

    def test_no_current_user_is_forbidden(self, app):
        """g.current_user が未設定の場合は 403 になる"""
        from werkzeug.exceptions import Forbidden
        view = _make_view('system_admin')
        with app.test_request_context('/'):
            with pytest.raises(Forbidden):
                view()

    def test_all_roles_allowed(self, app):
        """全ロールを許可している場合は全 user_type_id が通過できる"""
        view = _make_view(
            'system_admin', 'management_admin',
            'sales_company_user', 'service_company_user'
        )
        for user_type_id in (1, 2, 3, 4):
            with app.test_request_context('/'):
                g.current_user = SimpleNamespace(user_type_id=user_type_id)
                assert view() == "ok"
