import pytest

MODULE = 'iot_app.forms.user'


@pytest.mark.unit
class TestUserCreateForm:
    """UserCreateForm のバリデーションテスト
    観点: 1.1.1 必須チェック, 1.1.2 最大文字列長チェック, 1.1.5 メールアドレス形式チェック, 2.1 正常系処理
    """

    def _valid_data(self, **overrides):
        data = {
            'user_name': 'テストユーザー',
            'email_address': 'test@example.com',
            'organization_id': 1,
            'user_type_id': 2,
            'region_id': 1,
            'address': '東京都港区',
            'status': 1,
        }
        data.update(overrides)
        return data

    def test_valid_data_passes(self, app):
        """2.1.1: 正常なデータでバリデーションが通る"""
        with app.test_request_context():
            from iot_app.forms.user import UserCreateForm
            form = UserCreateForm(data=self._valid_data())
            assert form.validate()

    # --- user_name ---

    def test_user_name_required_empty(self, app):
        """1.1.1: user_name が空文字の場合バリデーションエラー"""
        with app.test_request_context():
            from iot_app.forms.user import UserCreateForm
            form = UserCreateForm(data=self._valid_data(user_name=''))
            assert not form.validate()
            assert 'user_name' in form.errors

    def test_user_name_max_length_exceeded(self, app):
        """1.2.3: user_name が 21 文字（最大長+1）の場合バリデーションエラー"""
        with app.test_request_context():
            from iot_app.forms.user import UserCreateForm
            form = UserCreateForm(data=self._valid_data(user_name='あ' * 21))
            assert not form.validate()
            assert 'user_name' in form.errors

    def test_user_name_max_length_passes(self, app):
        """1.2.2: user_name が 20 文字（最大長ちょうど）はバリデーション通過"""
        with app.test_request_context():
            from iot_app.forms.user import UserCreateForm
            form = UserCreateForm(data=self._valid_data(user_name='あ' * 20))
            assert form.validate()

    # --- email_address ---

    def test_email_required_empty(self, app):
        """1.1.1: email_address が空文字の場合バリデーションエラー"""
        with app.test_request_context():
            from iot_app.forms.user import UserCreateForm
            form = UserCreateForm(data=self._valid_data(email_address=''))
            assert not form.validate()
            assert 'email_address' in form.errors

    def test_email_invalid_format(self, app):
        """1.5.2: email_address にフォーマット不正（@ なし）でバリデーションエラー"""
        with app.test_request_context():
            from iot_app.forms.user import UserCreateForm
            form = UserCreateForm(data=self._valid_data(email_address='not-an-email'))
            assert not form.validate()
            assert 'email_address' in form.errors

    def test_email_max_length_exceeded(self, app):
        """1.2.3: email_address が 255 文字（最大長+1）の場合バリデーションエラー"""
        with app.test_request_context():
            from iot_app.forms.user import UserCreateForm
            long_local = 'a' * 244
            form = UserCreateForm(data=self._valid_data(
                email_address=f'{long_local}@example.com'  # 244+1+11=256文字
            ))
            assert not form.validate()
            assert 'email_address' in form.errors

    def test_email_max_length_passes(self, app):
        """1.2.2: email_address が 254 文字（最大長ちょうど）はバリデーション通過"""
        with app.test_request_context():
            from iot_app.forms.user import UserCreateForm
            local = 'a' * 243
            form = UserCreateForm(data=self._valid_data(
                email_address=f'{local}@example.com'  # 243+1+10=254文字
            ))
            assert form.validate()

    # --- address ---

    def test_address_max_length_exceeded(self, app):
        """1.2.3: address が 501 文字（最大長+1）の場合バリデーションエラー"""
        with app.test_request_context():
            from iot_app.forms.user import UserCreateForm
            form = UserCreateForm(data=self._valid_data(address='あ' * 501))
            assert not form.validate()
            assert 'address' in form.errors

    def test_address_max_length_passes(self, app):
        """1.2.2: address が 500 文字（最大長ちょうど）はバリデーション通過"""
        with app.test_request_context():
            from iot_app.forms.user import UserCreateForm
            form = UserCreateForm(data=self._valid_data(address='あ' * 500))
            assert form.validate()

    def test_address_empty_passes(self, app):
        """1.2.4: address が空文字（任意項目）はバリデーション通過"""
        with app.test_request_context():
            from iot_app.forms.user import UserCreateForm
            form = UserCreateForm(data=self._valid_data(address=''))
            assert form.validate()

    # --- 必須選択項目 ---

    def test_organization_id_required(self, app):
        """1.1.2: organization_id が未選択（None）の場合バリデーションエラー"""
        with app.test_request_context():
            from iot_app.forms.user import UserCreateForm
            form = UserCreateForm(data=self._valid_data(organization_id=None))
            assert not form.validate()
            assert 'organization_id' in form.errors

    def test_user_type_id_required(self, app):
        """1.1.2: user_type_id が未選択（None）の場合バリデーションエラー"""
        with app.test_request_context():
            from iot_app.forms.user import UserCreateForm
            form = UserCreateForm(data=self._valid_data(user_type_id=None))
            assert not form.validate()
            assert 'user_type_id' in form.errors

    def test_region_id_required(self, app):
        """1.1.2: region_id が未選択（None）の場合バリデーションエラー"""
        with app.test_request_context():
            from iot_app.forms.user import UserCreateForm
            form = UserCreateForm(data=self._valid_data(region_id=None))
            assert not form.validate()
            assert 'region_id' in form.errors

    def test_status_required(self, app):
        """1.1.2: status が未選択（None）の場合バリデーションエラー"""
        with app.test_request_context():
            from iot_app.forms.user import UserCreateForm
            form = UserCreateForm(data=self._valid_data(status=None))
            assert not form.validate()
            assert 'status' in form.errors


@pytest.mark.unit
class TestUserUpdateForm:
    """UserUpdateForm のバリデーションテスト
    観点: 1.1.1 必須チェック, 1.1.2 最大文字列長チェック, 2.1 正常系処理
    ※ UserUpdateForm は user_name / region_id / address / status / flags のみ編集可能
       email_address, organization_id, user_type_id は不変項目のためフォームフィールドなし
    """

    def _valid_data(self, **overrides):
        data = {
            'user_name': '更新ユーザー',
            'region_id': 1,
            'address': '大阪府',
            'status': 1,
        }
        data.update(overrides)
        return data

    def test_valid_data_passes(self, app):
        """2.1.1: 正常なデータでバリデーションが通る"""
        with app.test_request_context():
            from iot_app.forms.user import UserUpdateForm
            form = UserUpdateForm(data=self._valid_data())
            assert form.validate()

    # --- user_name ---

    def test_user_name_required_empty(self, app):
        """1.1.1: user_name が空文字の場合バリデーションエラー"""
        with app.test_request_context():
            from iot_app.forms.user import UserUpdateForm
            form = UserUpdateForm(data=self._valid_data(user_name=''))
            assert not form.validate()
            assert 'user_name' in form.errors

    def test_user_name_max_length_exceeded(self, app):
        """1.2.3: user_name が 21 文字（最大長+1）の場合バリデーションエラー"""
        with app.test_request_context():
            from iot_app.forms.user import UserUpdateForm
            form = UserUpdateForm(data=self._valid_data(user_name='あ' * 21))
            assert not form.validate()
            assert 'user_name' in form.errors

    def test_user_name_max_length_passes(self, app):
        """1.2.2: user_name が 20 文字（最大長ちょうど）はバリデーション通過"""
        with app.test_request_context():
            from iot_app.forms.user import UserUpdateForm
            form = UserUpdateForm(data=self._valid_data(user_name='あ' * 20))
            assert form.validate()

    # --- address ---

    def test_address_max_length_exceeded(self, app):
        """1.2.3: address が 501 文字（最大長+1）の場合バリデーションエラー"""
        with app.test_request_context():
            from iot_app.forms.user import UserUpdateForm
            form = UserUpdateForm(data=self._valid_data(address='あ' * 501))
            assert not form.validate()
            assert 'address' in form.errors

    def test_address_max_length_passes(self, app):
        """1.2.2: address が 500 文字（最大長ちょうど）はバリデーション通過"""
        with app.test_request_context():
            from iot_app.forms.user import UserUpdateForm
            form = UserUpdateForm(data=self._valid_data(address='あ' * 500))
            assert form.validate()

    def test_address_empty_passes(self, app):
        """1.2.4: address が空文字（任意項目）はバリデーション通過"""
        with app.test_request_context():
            from iot_app.forms.user import UserUpdateForm
            form = UserUpdateForm(data=self._valid_data(address=''))
            assert form.validate()

    # --- 必須選択項目 ---

    def test_region_id_required(self, app):
        """1.1.2: region_id が未選択（None）の場合バリデーションエラー"""
        with app.test_request_context():
            from iot_app.forms.user import UserUpdateForm
            form = UserUpdateForm(data=self._valid_data(region_id=None))
            assert not form.validate()
            assert 'region_id' in form.errors

    def test_status_required(self, app):
        """1.1.2: status が未選択（None）の場合バリデーションエラー"""
        with app.test_request_context():
            from iot_app.forms.user import UserUpdateForm
            form = UserUpdateForm(data=self._valid_data(status=None))
            assert not form.validate()
            assert 'status' in form.errors
