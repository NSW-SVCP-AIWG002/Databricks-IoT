"""
単体テスト: iot_app.common.cookie
"""
import json

import pytest
from flask import Flask


@pytest.fixture
def app():
    app = Flask(__name__)
    app.config["TESTING"] = True
    app.config["SECRET_KEY"] = "test-secret-key"
    return app


class TestSetSearchConditionsCookie:
    def test_sets_cookie_with_correct_name(self, app):
        """指定画面名のCookie名で保存される"""
        from iot_app.common.cookie import set_search_conditions_cookie

        with app.test_request_context('/'):
            response = app.response_class()
            conditions = {'page': 1, 'keyword': 'test'}
            set_search_conditions_cookie(response, 'users', conditions)
            assert 'search_conditions_users' in response.headers.get('Set-Cookie', '')

    def test_cookie_value_roundtrip(self, app):
        """保存した検索条件をget_search_conditions_cookieで正しく取得できる"""
        from iot_app.common.cookie import get_search_conditions_cookie, set_search_conditions_cookie

        conditions = {'page': 2, 'keyword': 'テスト'}
        with app.test_client() as client:
            with client.application.test_request_context('/'):
                response = app.response_class()
                set_search_conditions_cookie(response, 'devices', conditions)
                # Set-Cookieヘッダーからcookie文字列を取り出してリクエストに再設定
                set_cookie_header = response.headers.get('Set-Cookie', '')
                cookie_str = set_cookie_header.split(';')[0]  # name=value部分のみ

            with client.application.test_request_context('/', headers={'Cookie': cookie_str}):
                result = get_search_conditions_cookie('devices')
                assert result == conditions

    def test_returns_response(self, app):
        """レスポンスオブジェクトを返す"""
        from iot_app.common.cookie import set_search_conditions_cookie

        with app.test_request_context('/'):
            response = app.response_class()
            result = set_search_conditions_cookie(response, 'users', {})
            assert result is response


class TestGetSearchConditionsCookie:
    def test_returns_conditions_from_cookie(self, app):
        """Cookieに保存された検索条件を正しく返す"""
        from iot_app.common.cookie import get_search_conditions_cookie

        conditions = {'page': 3, 'keyword': 'abc'}
        cookie_value = json.dumps(conditions)
        with app.test_request_context('/', headers={'Cookie': f'search_conditions_users={cookie_value}'}):
            result = get_search_conditions_cookie('users')
            assert result == conditions

    def test_returns_empty_dict_when_no_cookie(self, app):
        """Cookieが存在しない場合は空の辞書を返す"""
        from iot_app.common.cookie import get_search_conditions_cookie

        with app.test_request_context('/'):
            result = get_search_conditions_cookie('users')
            assert result == {}

    def test_returns_empty_dict_on_invalid_json(self, app):
        """不正なJSONが格納されている場合は空の辞書を返す"""
        from iot_app.common.cookie import get_search_conditions_cookie

        with app.test_request_context('/', headers={'Cookie': 'search_conditions_users=not_json'}):
            result = get_search_conditions_cookie('users')
            assert result == {}

    def test_different_screen_names_are_independent(self, app):
        """異なる画面名のCookieは独立して管理される"""
        from iot_app.common.cookie import get_search_conditions_cookie

        users_conditions = json.dumps({'page': 1})
        devices_conditions = json.dumps({'page': 5})
        headers = {'Cookie': f'search_conditions_users={users_conditions}; search_conditions_devices={devices_conditions}'}
        with app.test_request_context('/', headers=headers):
            assert get_search_conditions_cookie('users') == {'page': 1}
            assert get_search_conditions_cookie('devices') == {'page': 5}


class TestClearSearchConditionsCookie:
    def test_deletes_cookie(self, app):
        """指定画面名のCookieが削除される"""
        from iot_app.common.cookie import clear_search_conditions_cookie

        with app.test_request_context('/'):
            response = app.response_class()
            clear_search_conditions_cookie(response, 'users')
            assert 'search_conditions_users' in response.headers.get('Set-Cookie', '')

    def test_returns_response(self, app):
        """レスポンスオブジェクトを返す"""
        from iot_app.common.cookie import clear_search_conditions_cookie

        with app.test_request_context('/'):
            response = app.response_class()
            result = clear_search_conditions_cookie(response, 'users')
            assert result is response
