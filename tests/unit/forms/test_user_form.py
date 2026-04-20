import pytest

MODULE = 'iot_app.forms.user'


@pytest.mark.unit
class TestUserCreateForm:
    """UserCreateForm のバリデーションテスト"""

    def test_valid_data_passes(self, app):
        """観点1: 正常なデータでバリデーションが通る"""
        with app.test_request_context():
            from iot_app.forms.user import UserCreateForm
            form = UserCreateForm(data={
                'user_name': 'テストユーザー',
                'email_address': 'test@example.com',
                'organization_id': 1,
                'user_type_id': 2,
                'region_id': 1,
                'address': '東京都港区',
                'language_code': 'ja',
            })
            assert form.validate()

    def test_user_name_required(self, app):
        """観点2: user_name が空の場合バリデーションエラー"""
        with app.test_request_context():
            from iot_app.forms.user import UserCreateForm
            form = UserCreateForm(data={
                'user_name': '',
                'email_address': 'test@example.com',
                'organization_id': 1,
                'user_type_id': 2,
                'region_id': 1,
                'address': '東京都港区',
                'language_code': 'ja',
            })
            assert not form.validate()
            assert 'user_name' in form.errors

    def test_user_name_max_20_chars(self, app):
        """観点3: user_name が 20 文字を超えるとバリデーションエラー"""
        with app.test_request_context():
            from iot_app.forms.user import UserCreateForm
            form = UserCreateForm(data={
                'user_name': 'あ' * 21,
                'email_address': 'test@example.com',
                'organization_id': 1,
                'user_type_id': 2,
                'region_id': 1,
                'address': '東京都',
                'language_code': 'ja',
            })
            assert not form.validate()
            assert 'user_name' in form.errors

    def test_user_name_exactly_20_chars_passes(self, app):
        """観点4: user_name が 20 文字はバリデーション通過"""
        with app.test_request_context():
            from iot_app.forms.user import UserCreateForm
            form = UserCreateForm(data={
                'user_name': 'あ' * 20,
                'email_address': 'test@example.com',
                'organization_id': 1,
                'user_type_id': 2,
                'region_id': 1,
                'address': '東京都',
                'language_code': 'ja',
            })
            assert form.validate()

    def test_email_required(self, app):
        """観点5: email_address が空の場合バリデーションエラー"""
        with app.test_request_context():
            from iot_app.forms.user import UserCreateForm
            form = UserCreateForm(data={
                'user_name': 'テスト',
                'email_address': '',
                'organization_id': 1,
                'user_type_id': 2,
                'region_id': 1,
                'address': '東京都',
                'language_code': 'ja',
            })
            assert not form.validate()
            assert 'email_address' in form.errors

    def test_email_invalid_format(self, app):
        """観点6: email_address のフォーマットが不正な場合バリデーションエラー"""
        with app.test_request_context():
            from iot_app.forms.user import UserCreateForm
            form = UserCreateForm(data={
                'user_name': 'テスト',
                'email_address': 'not-an-email',
                'organization_id': 1,
                'user_type_id': 2,
                'region_id': 1,
                'address': '東京都',
                'language_code': 'ja',
            })
            assert not form.validate()
            assert 'email_address' in form.errors

    def test_email_max_254_chars(self, app):
        """観点7: email_address が 254 文字を超えるとバリデーションエラー"""
        with app.test_request_context():
            from iot_app.forms.user import UserCreateForm
            long_local = 'a' * 244
            form = UserCreateForm(data={
                'user_name': 'テスト',
                'email_address': f'{long_local}@example.com',
                'organization_id': 1,
                'user_type_id': 2,
                'region_id': 1,
                'address': '東京都',
                'language_code': 'ja',
            })
            assert not form.validate()
            assert 'email_address' in form.errors

    def test_address_max_500_chars(self, app):
        """観点8: address が 500 文字を超えるとバリデーションエラー"""
        with app.test_request_context():
            from iot_app.forms.user import UserCreateForm
            form = UserCreateForm(data={
                'user_name': 'テスト',
                'email_address': 'test@example.com',
                'organization_id': 1,
                'user_type_id': 2,
                'region_id': 1,
                'address': 'あ' * 501,
                'language_code': 'ja',
            })
            assert not form.validate()
            assert 'address' in form.errors

    def test_address_exactly_500_chars_passes(self, app):
        """観点9: address が 500 文字はバリデーション通過"""
        with app.test_request_context():
            from iot_app.forms.user import UserCreateForm
            form = UserCreateForm(data={
                'user_name': 'テスト',
                'email_address': 'test@example.com',
                'organization_id': 1,
                'user_type_id': 2,
                'region_id': 1,
                'address': 'あ' * 500,
                'language_code': 'ja',
            })
            assert form.validate()

    def test_organization_id_required(self, app):
        """観点10: organization_id が未選択の場合バリデーションエラー"""
        with app.test_request_context():
            from iot_app.forms.user import UserCreateForm
            form = UserCreateForm(data={
                'user_name': 'テスト',
                'email_address': 'test@example.com',
                'organization_id': None,
                'user_type_id': 2,
                'region_id': 1,
                'address': '東京都',
                'language_code': 'ja',
            })
            assert not form.validate()
            assert 'organization_id' in form.errors

    def test_user_type_id_required(self, app):
        """観点11: user_type_id が未選択の場合バリデーションエラー"""
        with app.test_request_context():
            from iot_app.forms.user import UserCreateForm
            form = UserCreateForm(data={
                'user_name': 'テスト',
                'email_address': 'test@example.com',
                'organization_id': 1,
                'user_type_id': None,
                'region_id': 1,
                'address': '東京都',
                'language_code': 'ja',
            })
            assert not form.validate()
            assert 'user_type_id' in form.errors


@pytest.mark.unit
class TestUserUpdateForm:
    """UserUpdateForm のバリデーションテスト"""

    def test_valid_data_passes(self, app):
        """観点1: 正常なデータでバリデーションが通る"""
        with app.test_request_context():
            from iot_app.forms.user import UserUpdateForm
            form = UserUpdateForm(data={
                'user_name': '更新ユーザー',
                'email_address': 'updated@example.com',
                'organization_id': 2,
                'user_type_id': 3,
                'region_id': 1,
                'address': '大阪府',
                'language_code': 'en',
            })
            assert form.validate()

    def test_user_name_required(self, app):
        """観点2: user_name が空の場合バリデーションエラー"""
        with app.test_request_context():
            from iot_app.forms.user import UserUpdateForm
            form = UserUpdateForm(data={
                'user_name': '',
                'email_address': 'updated@example.com',
                'organization_id': 2,
                'user_type_id': 3,
                'region_id': 1,
                'address': '大阪府',
                'language_code': 'en',
            })
            assert not form.validate()
            assert 'user_name' in form.errors

    def test_user_name_max_20_chars(self, app):
        """観点3: user_name が 20 文字を超えるとバリデーションエラー"""
        with app.test_request_context():
            from iot_app.forms.user import UserUpdateForm
            form = UserUpdateForm(data={
                'user_name': 'あ' * 21,
                'email_address': 'updated@example.com',
                'organization_id': 2,
                'user_type_id': 3,
                'region_id': 1,
                'address': '大阪府',
                'language_code': 'en',
            })
            assert not form.validate()
            assert 'user_name' in form.errors

    def test_email_invalid_format(self, app):
        """観点4: email_address のフォーマットが不正な場合バリデーションエラー"""
        with app.test_request_context():
            from iot_app.forms.user import UserUpdateForm
            form = UserUpdateForm(data={
                'user_name': '更新',
                'email_address': 'bad-email',
                'organization_id': 2,
                'user_type_id': 3,
                'region_id': 1,
                'address': '大阪府',
                'language_code': 'en',
            })
            assert not form.validate()
            assert 'email_address' in form.errors

    def test_address_max_500_chars(self, app):
        """観点5: address が 500 文字を超えるとバリデーションエラー"""
        with app.test_request_context():
            from iot_app.forms.user import UserUpdateForm
            form = UserUpdateForm(data={
                'user_name': '更新',
                'email_address': 'updated@example.com',
                'organization_id': 2,
                'user_type_id': 3,
                'region_id': 1,
                'address': 'あ' * 501,
                'language_code': 'en',
            })
            assert not form.validate()
            assert 'address' in form.errors
