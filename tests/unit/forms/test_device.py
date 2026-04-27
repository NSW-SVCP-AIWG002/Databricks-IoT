"""
デバイス管理 - Form層 単体テスト

対象ファイル: src/iot_app/forms/device.py

参照ドキュメント:
  - UI仕様書:           docs/03-features/flask-app/devices/ui-specification.md
  - 単体テスト観点表:   docs/05-testing/unit-test/unit-test-perspectives.md
  - 実装ガイド:         docs/05-testing/unit-test/unit-test-guide.md
"""
import pytest


# ============================================================
# 1. DeviceCreateForm
# 観点: 1.1.1 必須チェック, 1.1.2 最大文字列長チェック, 1.1.6 不整値チェック
# ============================================================

@pytest.mark.unit
class TestDeviceCreateFormRequired:
    """DeviceCreateForm - 必須チェック
    観点: 1.1.1 必須チェック
    """

    def test_valid_when_all_required_fields_provided(self, app):
        """1.1.1.3 必須項目すべて入力あり: バリデーション通過"""
        from iot_app.forms.device import DeviceCreateForm
        with app.test_request_context():
            form = DeviceCreateForm(data={
                'device_uuid': 'DEV-001',
                'device_name': 'センサー1号機',
                'device_type_id': '1',
                'device_model': 'MODEL-A',
                'organization_id': '1',
            })
            form.device_type_id.choices = [('1', 'センサー')]
            form.organization_id.choices = [('1', 'A株式会社')]
            assert form.validate()

    def test_invalid_when_device_uuid_empty(self, app):
        """1.1.1.1 device_uuid 空文字: バリデーションエラー"""
        from iot_app.forms.device import DeviceCreateForm
        with app.test_request_context():
            form = DeviceCreateForm(data={
                'device_uuid': '',
                'device_name': 'センサー1号機',
                'device_type_id': '1',
                'device_model': 'MODEL-A',
                'organization_id': '1',
            })
            form.device_type_id.choices = [('1', 'センサー')]
            form.organization_id.choices = [('1', 'A株式会社')]
            assert not form.validate()
            assert 'device_uuid' in form.errors

    def test_invalid_when_device_name_empty(self, app):
        """1.1.1.1 device_name 空文字: バリデーションエラー"""
        from iot_app.forms.device import DeviceCreateForm
        with app.test_request_context():
            form = DeviceCreateForm(data={
                'device_uuid': 'DEV-001',
                'device_name': '',
                'device_type_id': '1',
                'device_model': 'MODEL-A',
                'organization_id': '1',
            })
            form.device_type_id.choices = [('1', 'センサー')]
            form.organization_id.choices = [('1', 'A株式会社')]
            assert not form.validate()
            assert 'device_name' in form.errors

    def test_invalid_when_device_type_id_missing(self, app):
        """1.1.1.2 device_type_id 未選択: バリデーションエラー"""
        from iot_app.forms.device import DeviceCreateForm
        with app.test_request_context():
            form = DeviceCreateForm(data={
                'device_uuid': 'DEV-001',
                'device_name': 'センサー1号機',
                'device_type_id': '',
                'device_model': 'MODEL-A',
                'organization_id': '1',
            })
            form.device_type_id.choices = [('', ''), ('1', 'センサー')]
            form.organization_id.choices = [('1', 'A株式会社')]
            assert not form.validate()
            assert 'device_type_id' in form.errors

    def test_invalid_when_organization_id_missing(self, app):
        """1.1.1.2 organization_id 未選択: バリデーションエラー"""
        from iot_app.forms.device import DeviceCreateForm
        with app.test_request_context():
            form = DeviceCreateForm(data={
                'device_uuid': 'DEV-001',
                'device_name': 'センサー1号機',
                'device_type_id': '1',
                'device_model': 'MODEL-A',
                'organization_id': '',
            })
            form.device_type_id.choices = [('1', 'センサー')]
            form.organization_id.choices = [('', ''), ('1', 'A株式会社')]
            assert not form.validate()
            assert 'organization_id' in form.errors

    def test_invalid_when_device_name_whitespace_only(self, app):
        """1.1.1.4 device_name 空白のみ: DataRequired が strip するためバリデーションエラー"""
        from iot_app.forms.device import DeviceCreateForm
        with app.test_request_context():
            form = DeviceCreateForm(data={
                'device_uuid': 'DEV-001',
                'device_name': '   ',
                'device_type_id': '1',
                'device_model': 'MODEL-A',
                'organization_id': '1',
            })
            form.device_type_id.choices = [('1', 'センサー')]
            form.organization_id.choices = [('1', 'A株式会社')]
            assert not form.validate()
            assert 'device_name' in form.errors


@pytest.mark.unit
class TestDeviceCreateFormMaxLength:
    """DeviceCreateForm - 最大文字列長チェック
    観点: 1.1.2 最大文字列長チェック
    """

    def _base_data(self, **overrides):
        data = {
            'device_uuid': 'DEV-001',
            'device_name': 'センサー',
            'device_type_id': '1',
            'device_model': 'MODEL-A',
            'organization_id': '1',
        }
        data.update(overrides)
        return data

    def _make_form(self, app, data):
        from iot_app.forms.device import DeviceCreateForm
        with app.test_request_context():
            form = DeviceCreateForm(data=data)
            form.device_type_id.choices = [('1', 'センサー')]
            form.organization_id.choices = [('1', 'A株式会社')]
            return form.validate(), form.errors

    # --- device_uuid (最大128文字) ---

    def test_device_uuid_127_chars_passes(self, app):
        """1.2.1 device_uuid 127文字（最大-1）: バリデーション通過"""
        from iot_app.forms.device import DeviceCreateForm
        with app.test_request_context():
            form = DeviceCreateForm(data=self._base_data(device_uuid='A' * 127))
            form.device_type_id.choices = [('1', 'センサー')]
            form.organization_id.choices = [('1', 'A株式会社')]
            assert form.validate()

    def test_device_uuid_128_chars_passes(self, app):
        """1.2.2 device_uuid 128文字（最大）: バリデーション通過"""
        from iot_app.forms.device import DeviceCreateForm
        with app.test_request_context():
            form = DeviceCreateForm(data=self._base_data(device_uuid='A' * 128))
            form.device_type_id.choices = [('1', 'センサー')]
            form.organization_id.choices = [('1', 'A株式会社')]
            assert form.validate()

    def test_device_uuid_129_chars_fails(self, app):
        """1.2.3 device_uuid 129文字（最大+1）: バリデーションエラー"""
        from iot_app.forms.device import DeviceCreateForm
        with app.test_request_context():
            form = DeviceCreateForm(data=self._base_data(device_uuid='A' * 129))
            form.device_type_id.choices = [('1', 'センサー')]
            form.organization_id.choices = [('1', 'A株式会社')]
            assert not form.validate()
            assert 'device_uuid' in form.errors

    # --- device_name (最大100文字) ---

    def test_device_name_99_chars_passes(self, app):
        """1.2.1 device_name 99文字（最大-1）: バリデーション通過"""
        from iot_app.forms.device import DeviceCreateForm
        with app.test_request_context():
            form = DeviceCreateForm(data=self._base_data(device_name='あ' * 99))
            form.device_type_id.choices = [('1', 'センサー')]
            form.organization_id.choices = [('1', 'A株式会社')]
            assert form.validate()

    def test_device_name_100_chars_passes(self, app):
        """1.2.2 device_name 100文字（最大）: バリデーション通過"""
        from iot_app.forms.device import DeviceCreateForm
        with app.test_request_context():
            form = DeviceCreateForm(data=self._base_data(device_name='あ' * 100))
            form.device_type_id.choices = [('1', 'センサー')]
            form.organization_id.choices = [('1', 'A株式会社')]
            assert form.validate()

    def test_device_name_101_chars_fails(self, app):
        """1.2.3 device_name 101文字（最大+1）: バリデーションエラー"""
        from iot_app.forms.device import DeviceCreateForm
        with app.test_request_context():
            form = DeviceCreateForm(data=self._base_data(device_name='あ' * 101))
            form.device_type_id.choices = [('1', 'センサー')]
            form.organization_id.choices = [('1', 'A株式会社')]
            assert not form.validate()
            assert 'device_name' in form.errors

    # --- device_model (最大100文字) ---

    def test_device_model_100_chars_passes(self, app):
        """1.2.2 device_model 100文字（最大）: バリデーション通過"""
        from iot_app.forms.device import DeviceCreateForm
        with app.test_request_context():
            form = DeviceCreateForm(data=self._base_data(device_model='M' * 100))
            form.device_type_id.choices = [('1', 'センサー')]
            form.organization_id.choices = [('1', 'A株式会社')]
            assert form.validate()

    def test_device_model_101_chars_fails(self, app):
        """1.2.3 device_model 101文字（最大+1）: バリデーションエラー"""
        from iot_app.forms.device import DeviceCreateForm
        with app.test_request_context():
            form = DeviceCreateForm(data=self._base_data(device_model='M' * 101))
            form.device_type_id.choices = [('1', 'センサー')]
            form.organization_id.choices = [('1', 'A株式会社')]
            assert not form.validate()
            assert 'device_model' in form.errors

    def test_device_model_empty_fails(self, app):
        """1.2.4 device_model 空文字（必須項目）: バリデーションエラー"""
        from iot_app.forms.device import DeviceCreateForm
        with app.test_request_context():
            form = DeviceCreateForm(data=self._base_data(device_model=''))
            form.device_type_id.choices = [('1', 'センサー')]
            form.organization_id.choices = [('1', 'A株式会社')]
            assert not form.validate()
            assert 'device_model' in form.errors

    # --- sim_id (最大20文字) ---

    def test_sim_id_20_chars_passes(self, app):
        """1.2.2 sim_id 20文字（最大）: バリデーション通過"""
        from iot_app.forms.device import DeviceCreateForm
        with app.test_request_context():
            form = DeviceCreateForm(data=self._base_data(sim_id='1' * 20))
            form.device_type_id.choices = [('1', 'センサー')]
            form.organization_id.choices = [('1', 'A株式会社')]
            assert form.validate()

    def test_sim_id_21_chars_fails(self, app):
        """1.2.3 sim_id 21文字（最大+1）: バリデーションエラー"""
        from iot_app.forms.device import DeviceCreateForm
        from werkzeug.datastructures import ImmutableMultiDict
        with app.test_request_context():
            formdata = ImmutableMultiDict([
                ('device_uuid', 'DEV-001'),
                ('device_name', 'センサー'),
                ('device_type_id', '1'),
                ('device_model', 'MODEL-A'),
                ('organization_id', '1'),
                ('sim_id', '1' * 21),
            ])
            form = DeviceCreateForm(formdata=formdata)
            form.device_type_id.choices = [('1', 'センサー')]
            form.organization_id.choices = [('1', 'A株式会社')]
            assert not form.validate()
            assert 'sim_id' in form.errors

    def test_sim_id_empty_passes(self, app):
        """1.2.4 sim_id 空文字（任意項目）: バリデーション通過"""
        from iot_app.forms.device import DeviceCreateForm
        with app.test_request_context():
            form = DeviceCreateForm(data=self._base_data(sim_id=''))
            form.device_type_id.choices = [('1', 'センサー')]
            form.organization_id.choices = [('1', 'A株式会社')]
            assert form.validate()

    # --- device_location (最大100文字) ---

    def test_device_location_100_chars_passes(self, app):
        """1.2.2 device_location 100文字（最大）: バリデーション通過"""
        from iot_app.forms.device import DeviceCreateForm
        with app.test_request_context():
            form = DeviceCreateForm(data=self._base_data(device_location='あ' * 100))
            form.device_type_id.choices = [('1', 'センサー')]
            form.organization_id.choices = [('1', 'A株式会社')]
            assert form.validate()

    def test_device_location_101_chars_fails(self, app):
        """1.2.3 device_location 101文字（最大+1）: バリデーションエラー"""
        from iot_app.forms.device import DeviceCreateForm
        from werkzeug.datastructures import ImmutableMultiDict
        with app.test_request_context():
            formdata = ImmutableMultiDict([
                ('device_uuid', 'DEV-001'),
                ('device_name', 'センサー'),
                ('device_type_id', '1'),
                ('device_model', 'MODEL-A'),
                ('organization_id', '1'),
                ('device_location', 'あ' * 101),
            ])
            form = DeviceCreateForm(formdata=formdata)
            form.device_type_id.choices = [('1', 'センサー')]
            form.organization_id.choices = [('1', 'A株式会社')]
            assert not form.validate()
            assert 'device_location' in form.errors

    def test_device_location_empty_passes(self, app):
        """1.2.4 device_location 空文字（任意項目）: バリデーション通過"""
        from iot_app.forms.device import DeviceCreateForm
        with app.test_request_context():
            form = DeviceCreateForm(data=self._base_data(device_location=''))
            form.device_type_id.choices = [('1', 'センサー')]
            form.organization_id.choices = [('1', 'A株式会社')]
            assert form.validate()


@pytest.mark.unit
class TestDeviceCreateFormFormat:
    """DeviceCreateForm - 形式チェック
    観点: 1.1.6 不整値チェック
    """

    def _base_data(self, **overrides):
        data = {
            'device_uuid': 'DEV-001',
            'device_name': 'センサー',
            'device_type_id': '1',
            'device_model': 'MODEL-A',
            'organization_id': '1',
        }
        data.update(overrides)
        return data

    # --- device_uuid: 英数字とハイフンのみ ---

    def test_device_uuid_alphanumeric_hyphen_passes(self, app):
        """1.6.1 device_uuid 英数字+ハイフン: バリデーション通過"""
        from iot_app.forms.device import DeviceCreateForm
        with app.test_request_context():
            form = DeviceCreateForm(data=self._base_data(device_uuid='ABC-123-def'))
            form.device_type_id.choices = [('1', 'センサー')]
            form.organization_id.choices = [('1', 'A株式会社')]
            assert form.validate()

    def test_device_uuid_with_underscore_fails(self, app):
        """1.6.2 device_uuid アンダースコア含む: バリデーションエラー"""
        from iot_app.forms.device import DeviceCreateForm
        with app.test_request_context():
            form = DeviceCreateForm(data=self._base_data(device_uuid='DEV_001'))
            form.device_type_id.choices = [('1', 'センサー')]
            form.organization_id.choices = [('1', 'A株式会社')]
            assert not form.validate()
            assert 'device_uuid' in form.errors

    def test_device_uuid_with_dot_fails(self, app):
        """1.6.2 device_uuid ドット含む: バリデーションエラー"""
        from iot_app.forms.device import DeviceCreateForm
        with app.test_request_context():
            form = DeviceCreateForm(data=self._base_data(device_uuid='DEV.001'))
            form.device_type_id.choices = [('1', 'センサー')]
            form.organization_id.choices = [('1', 'A株式会社')]
            assert not form.validate()
            assert 'device_uuid' in form.errors

    def test_device_uuid_with_space_fails(self, app):
        """1.6.2 device_uuid スペース含む: バリデーションエラー"""
        from iot_app.forms.device import DeviceCreateForm
        with app.test_request_context():
            form = DeviceCreateForm(data=self._base_data(device_uuid='DEV 001'))
            form.device_type_id.choices = [('1', 'センサー')]
            form.organization_id.choices = [('1', 'A株式会社')]
            assert not form.validate()
            assert 'device_uuid' in form.errors

    # --- mac_address: XX:XX:XX:XX:XX:XX 形式 ---

    def test_mac_address_valid_uppercase_passes(self, app):
        """1.6.1 mac_address 大文字 XX:XX:XX:XX:XX:XX: バリデーション通過"""
        from iot_app.forms.device import DeviceCreateForm
        with app.test_request_context():
            form = DeviceCreateForm(data=self._base_data(mac_address='AA:BB:CC:DD:EE:FF'))
            form.device_type_id.choices = [('1', 'センサー')]
            form.organization_id.choices = [('1', 'A株式会社')]
            assert form.validate()

    def test_mac_address_valid_lowercase_passes(self, app):
        """1.6.1 mac_address 小文字 xx:xx:xx:xx:xx:xx: バリデーション通過"""
        from iot_app.forms.device import DeviceCreateForm
        with app.test_request_context():
            form = DeviceCreateForm(data=self._base_data(mac_address='aa:bb:cc:dd:ee:ff'))
            form.device_type_id.choices = [('1', 'センサー')]
            form.organization_id.choices = [('1', 'A株式会社')]
            assert form.validate()

    def test_mac_address_hyphen_separator_fails(self, app):
        """1.6.2 mac_address ハイフン区切り: バリデーションエラー"""
        from iot_app.forms.device import DeviceCreateForm
        from werkzeug.datastructures import ImmutableMultiDict
        with app.test_request_context():
            formdata = ImmutableMultiDict([
                ('device_uuid', 'DEV-001'),
                ('device_name', 'センサー'),
                ('device_type_id', '1'),
                ('device_model', 'MODEL-A'),
                ('organization_id', '1'),
                ('mac_address', 'AA-BB-CC-DD-EE-FF'),
            ])
            form = DeviceCreateForm(formdata=formdata)
            form.device_type_id.choices = [('1', 'センサー')]
            form.organization_id.choices = [('1', 'A株式会社')]
            assert not form.validate()
            assert 'mac_address' in form.errors

    def test_mac_address_invalid_hex_fails(self, app):
        """1.6.2 mac_address 16進数以外の文字: バリデーションエラー"""
        from iot_app.forms.device import DeviceCreateForm
        from werkzeug.datastructures import ImmutableMultiDict
        with app.test_request_context():
            formdata = ImmutableMultiDict([
                ('device_uuid', 'DEV-001'),
                ('device_name', 'センサー'),
                ('device_type_id', '1'),
                ('device_model', 'MODEL-A'),
                ('organization_id', '1'),
                ('mac_address', 'GG:HH:II:JJ:KK:LL'),
            ])
            form = DeviceCreateForm(formdata=formdata)
            form.device_type_id.choices = [('1', 'センサー')]
            form.organization_id.choices = [('1', 'A株式会社')]
            assert not form.validate()
            assert 'mac_address' in form.errors

    def test_mac_address_too_short_fails(self, app):
        """1.6.2 mac_address セグメント5つ（不足）: バリデーションエラー"""
        from iot_app.forms.device import DeviceCreateForm
        from werkzeug.datastructures import ImmutableMultiDict
        with app.test_request_context():
            formdata = ImmutableMultiDict([
                ('device_uuid', 'DEV-001'),
                ('device_name', 'センサー'),
                ('device_type_id', '1'),
                ('device_model', 'MODEL-A'),
                ('organization_id', '1'),
                ('mac_address', 'AA:BB:CC:DD:EE'),
            ])
            form = DeviceCreateForm(formdata=formdata)
            form.device_type_id.choices = [('1', 'センサー')]
            form.organization_id.choices = [('1', 'A株式会社')]
            assert not form.validate()
            assert 'mac_address' in form.errors

    def test_mac_address_empty_passes(self, app):
        """1.1.4 mac_address 空文字（任意項目・Regexp は空文字をスキップ）: バリデーション通過"""
        from iot_app.forms.device import DeviceCreateForm
        with app.test_request_context():
            form = DeviceCreateForm(data=self._base_data(mac_address=''))
            form.device_type_id.choices = [('1', 'センサー')]
            form.organization_id.choices = [('1', 'A株式会社')]
            assert form.validate()

    def test_mac_address_none_passes(self, app):
        """1.1.4 mac_address None（任意項目）: バリデーション通過"""
        from iot_app.forms.device import DeviceCreateForm
        with app.test_request_context():
            form = DeviceCreateForm(data=self._base_data(mac_address=None))
            form.device_type_id.choices = [('1', 'センサー')]
            form.organization_id.choices = [('1', 'A株式会社')]
            assert form.validate()


# ============================================================
# 2. DeviceUpdateForm
# 観点: 1.1.1 必須チェック, 1.1.2 最大文字列長チェック, 1.1.6 不整値チェック
# ============================================================

@pytest.mark.unit
class TestDeviceUpdateFormRequired:
    """DeviceUpdateForm - 必須チェック
    観点: 1.1.1 必須チェック
    補足: device_uuid フィールドは更新フォームに存在しない（読み取り専用）
    """

    def test_valid_when_required_fields_provided(self, app):
        """1.1.1.3 必須項目すべて入力あり: バリデーション通過"""
        from iot_app.forms.device import DeviceUpdateForm
        with app.test_request_context():
            form = DeviceUpdateForm(data={
                'device_name': 'センサー1号機',
                'device_type_id': '1',
                'organization_id': '1',
            })
            form.device_type_id.choices = [('1', 'センサー')]
            form.organization_id.choices = [('1', 'A株式会社')]
            assert form.validate()

    def test_invalid_when_device_name_empty(self, app):
        """1.1.1.1 device_name 空文字: バリデーションエラー"""
        from iot_app.forms.device import DeviceUpdateForm
        with app.test_request_context():
            form = DeviceUpdateForm(data={
                'device_name': '',
                'device_type_id': '1',
                'organization_id': '1',
            })
            form.device_type_id.choices = [('1', 'センサー')]
            form.organization_id.choices = [('1', 'A株式会社')]
            assert not form.validate()
            assert 'device_name' in form.errors

    def test_invalid_when_device_type_id_missing(self, app):
        """1.1.1.2 device_type_id 未選択: バリデーションエラー"""
        from iot_app.forms.device import DeviceUpdateForm
        with app.test_request_context():
            form = DeviceUpdateForm(data={
                'device_name': 'センサー1号機',
                'device_type_id': '',
                'organization_id': '1',
            })
            form.device_type_id.choices = [('', ''), ('1', 'センサー')]
            form.organization_id.choices = [('1', 'A株式会社')]
            assert not form.validate()
            assert 'device_type_id' in form.errors

    def test_invalid_when_organization_id_missing(self, app):
        """1.1.1.2 organization_id 未選択: バリデーションエラー"""
        from iot_app.forms.device import DeviceUpdateForm
        with app.test_request_context():
            form = DeviceUpdateForm(data={
                'device_name': 'センサー1号機',
                'device_type_id': '1',
                'organization_id': '',
            })
            form.device_type_id.choices = [('1', 'センサー')]
            form.organization_id.choices = [('', ''), ('1', 'A株式会社')]
            assert not form.validate()
            assert 'organization_id' in form.errors

    def test_invalid_when_device_name_whitespace_only(self, app):
        """1.1.1.4 device_name 空白のみ: DataRequired が strip するためバリデーションエラー"""
        from iot_app.forms.device import DeviceUpdateForm
        with app.test_request_context():
            form = DeviceUpdateForm(data={
                'device_name': '   ',
                'device_type_id': '1',
                'organization_id': '1',
            })
            form.device_type_id.choices = [('1', 'センサー')]
            form.organization_id.choices = [('1', 'A株式会社')]
            assert not form.validate()
            assert 'device_name' in form.errors

    def test_no_device_uuid_field(self, app):
        """DeviceUpdateForm に device_uuid フィールドが存在しないこと"""
        from iot_app.forms.device import DeviceUpdateForm
        with app.test_request_context():
            form = DeviceUpdateForm(data={})
            assert not hasattr(form, 'device_uuid')


@pytest.mark.unit
class TestDeviceUpdateFormMaxLength:
    """DeviceUpdateForm - 最大文字列長チェック
    観点: 1.1.2 最大文字列長チェック
    """

    def _base_data(self, **overrides):
        data = {
            'device_name': 'センサー',
            'device_type_id': '1',
            'organization_id': '1',
        }
        data.update(overrides)
        return data

    # --- device_name (最大100文字) ---

    def test_device_name_100_chars_passes(self, app):
        """1.2.2 device_name 100文字（最大）: バリデーション通過"""
        from iot_app.forms.device import DeviceUpdateForm
        with app.test_request_context():
            form = DeviceUpdateForm(data=self._base_data(device_name='あ' * 100))
            form.device_type_id.choices = [('1', 'センサー')]
            form.organization_id.choices = [('1', 'A株式会社')]
            assert form.validate()

    def test_device_name_101_chars_fails(self, app):
        """1.2.3 device_name 101文字（最大+1）: バリデーションエラー"""
        from iot_app.forms.device import DeviceUpdateForm
        with app.test_request_context():
            form = DeviceUpdateForm(data=self._base_data(device_name='あ' * 101))
            form.device_type_id.choices = [('1', 'センサー')]
            form.organization_id.choices = [('1', 'A株式会社')]
            assert not form.validate()
            assert 'device_name' in form.errors

    # --- sim_id (最大20文字) ---

    def test_sim_id_20_chars_passes(self, app):
        """1.2.2 sim_id 20文字（最大）: バリデーション通過"""
        from iot_app.forms.device import DeviceUpdateForm
        with app.test_request_context():
            form = DeviceUpdateForm(data=self._base_data(sim_id='1' * 20))
            form.device_type_id.choices = [('1', 'センサー')]
            form.organization_id.choices = [('1', 'A株式会社')]
            assert form.validate()

    def test_sim_id_21_chars_fails(self, app):
        """1.2.3 sim_id 21文字（最大+1）: バリデーションエラー"""
        from iot_app.forms.device import DeviceUpdateForm
        from werkzeug.datastructures import ImmutableMultiDict
        with app.test_request_context():
            formdata = ImmutableMultiDict([
                ('device_name', 'センサー'),
                ('device_type_id', '1'),
                ('organization_id', '1'),
                ('sim_id', '1' * 21),
            ])
            form = DeviceUpdateForm(formdata=formdata)
            form.device_type_id.choices = [('1', 'センサー')]
            form.organization_id.choices = [('1', 'A株式会社')]
            assert not form.validate()
            assert 'sim_id' in form.errors

    # --- device_location (最大100文字) ---

    def test_device_location_100_chars_passes(self, app):
        """1.2.2 device_location 100文字（最大）: バリデーション通過"""
        from iot_app.forms.device import DeviceUpdateForm
        with app.test_request_context():
            form = DeviceUpdateForm(data=self._base_data(device_location='あ' * 100))
            form.device_type_id.choices = [('1', 'センサー')]
            form.organization_id.choices = [('1', 'A株式会社')]
            assert form.validate()

    def test_device_location_101_chars_fails(self, app):
        """1.2.3 device_location 101文字（最大+1）: バリデーションエラー"""
        from iot_app.forms.device import DeviceUpdateForm
        from werkzeug.datastructures import ImmutableMultiDict
        with app.test_request_context():
            formdata = ImmutableMultiDict([
                ('device_name', 'センサー'),
                ('device_type_id', '1'),
                ('organization_id', '1'),
                ('device_location', 'あ' * 101),
            ])
            form = DeviceUpdateForm(formdata=formdata)
            form.device_type_id.choices = [('1', 'センサー')]
            form.organization_id.choices = [('1', 'A株式会社')]
            assert not form.validate()
            assert 'device_location' in form.errors


@pytest.mark.unit
class TestDeviceUpdateFormFormat:
    """DeviceUpdateForm - 形式チェック
    観点: 1.1.6 不整値チェック（mac_address）
    """

    def _base_data(self, **overrides):
        data = {
            'device_name': 'センサー',
            'device_type_id': '1',
            'organization_id': '1',
        }
        data.update(overrides)
        return data

    def test_mac_address_valid_passes(self, app):
        """1.6.1 mac_address XX:XX:XX:XX:XX:XX: バリデーション通過"""
        from iot_app.forms.device import DeviceUpdateForm
        with app.test_request_context():
            form = DeviceUpdateForm(data=self._base_data(mac_address='AA:BB:CC:DD:EE:FF'))
            form.device_type_id.choices = [('1', 'センサー')]
            form.organization_id.choices = [('1', 'A株式会社')]
            assert form.validate()

    def test_mac_address_hyphen_separator_fails(self, app):
        """1.6.2 mac_address ハイフン区切り: バリデーションエラー"""
        from iot_app.forms.device import DeviceUpdateForm
        from werkzeug.datastructures import ImmutableMultiDict
        with app.test_request_context():
            formdata = ImmutableMultiDict([
                ('device_name', 'センサー'),
                ('device_type_id', '1'),
                ('organization_id', '1'),
                ('mac_address', 'AA-BB-CC-DD-EE-FF'),
            ])
            form = DeviceUpdateForm(formdata=formdata)
            form.device_type_id.choices = [('1', 'センサー')]
            form.organization_id.choices = [('1', 'A株式会社')]
            assert not form.validate()
            assert 'mac_address' in form.errors

    def test_mac_address_empty_passes(self, app):
        """1.1.4 mac_address 空文字（任意項目）: バリデーション通過"""
        from iot_app.forms.device import DeviceUpdateForm
        with app.test_request_context():
            form = DeviceUpdateForm(data=self._base_data(mac_address=''))
            form.device_type_id.choices = [('1', 'センサー')]
            form.organization_id.choices = [('1', 'A株式会社')]
            assert form.validate()
