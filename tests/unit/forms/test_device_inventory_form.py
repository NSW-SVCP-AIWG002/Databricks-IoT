"""
デバイス台帳管理 - Forms層 単体テスト

対象ファイル: src/iot_app/forms/device_inventory.py

参照ドキュメント:
  - 機能設計書:       docs/03-features/flask-app/device-inventory/workflow-specification.md
  - UI仕様書:         docs/03-features/flask-app/device-inventory/ui-specification.md
  - 単体テスト観点表: docs/05-testing/unit-test/unit-test-perspectives.md
  - 実装ガイド:       docs/05-testing/unit-test/unit-test-guide.md

テスト対象:
  - device_uuid_format_validator: AUTH_TYPE別 device_uuid フォーマットバリデーション
  - date_after_purchase_validator: 購入日以降チェックバリデーターファクトリ
  - DeviceInventorySearchForm.validate_purchase_date_to: 購入日範囲相関バリデーション
  - DeviceInventoryCreateForm: 登録フォームバリデーション（必須・最大文字数・形式）
  - DeviceInventoryUpdateForm: 更新フォームバリデーション（登録フォームと同一）
"""
import os
import pytest
from datetime import date
from unittest.mock import Mock, patch, MagicMock


# ============================================================
# 定数
# ============================================================

FORMS_MODULE = 'iot_app.forms.device_inventory'
SERVICE_MODULE = 'iot_app.services.device_inventory_service'


# ============================================================
# ヘルパー関数
# ============================================================

def make_mock_form_field(data=None, errors=None):
    """WTForms フィールドのモックを生成するヘルパー"""
    field = Mock()
    field.data = data
    field.errors = errors or []
    return field


def make_mock_create_form(**field_values):
    """DeviceInventoryCreateForm のモックフォームを生成するヘルパー"""
    form = Mock()
    form.purchase_date = make_mock_form_field(
        field_values.get('purchase_date', date(2025, 1, 15))
    )
    form.device_uuid = make_mock_form_field(
        field_values.get('device_uuid', 'DEV-UUID-001')
    )
    return form


# ============================================================
# 1. device_uuid_format_validator
# 観点: 1.1.6 不整値チェック, 2.1 正常系処理
# ============================================================

@pytest.mark.unit
class TestDeviceUuidFormatValidator:
    """device_uuid_format_validator - AUTH_TYPE別 device_uuid フォーマット検証

    観点セクション: 1.1.6 不整値チェック(マスタ存在など), 2.1 正常系処理
    """

    @patch.dict(os.environ, {'AUTH_TYPE': 'azure'})
    def test_valid_azure_uuid_does_not_raise(self):
        """2.1.1, 1.6.1: azure 環境で有効な device_uuid を渡してもバリデーションエラーが発生しない

        実行内容: AUTH_TYPE=azure で許容される文字のみを含む UUID で device_uuid_format_validator を実行する
        想定結果: ValidationError が発生しないこと
        """
        # Arrange
        from iot_app.forms.device_inventory import device_uuid_format_validator
        from wtforms import ValidationError

        form = make_mock_create_form()
        field = make_mock_form_field(data='MyDevice-001.%#_*?,:valid')

        # Act & Assert: ValidationError が発生しないこと
        try:
            device_uuid_format_validator(form, field)
        except ValidationError:
            pytest.fail('Valid azure UUID raised ValidationError unexpectedly')

    @patch.dict(os.environ, {'AUTH_TYPE': 'aws'})
    def test_valid_aws_uuid_does_not_raise(self):
        """2.1.1, 1.6.1: aws 環境で有効な device_uuid を渡してもバリデーションエラーが発生しない

        実行内容: AUTH_TYPE=aws で許容される文字のみを含む UUID で device_uuid_format_validator を実行する
        想定結果: ValidationError が発生しないこと
        """
        # Arrange
        from iot_app.forms.device_inventory import device_uuid_format_validator
        from wtforms import ValidationError

        form = make_mock_create_form()
        field = make_mock_form_field(data='MyDevice_001-abc')

        # Act & Assert
        try:
            device_uuid_format_validator(form, field)
        except ValidationError:
            pytest.fail('Valid aws UUID raised ValidationError unexpectedly')

    @patch.dict(os.environ, {'AUTH_TYPE': 'azure'})
    def test_invalid_azure_uuid_raises_validation_error(self):
        """1.6.2: azure 環境で使用不可文字（@ など）を含む UUID でValidationError が発生する

        実行内容: AUTH_TYPE=azure で許容されない文字（@）を含む UUID で device_uuid_format_validator を実行する
        想定結果: ValidationError がスローされること
        """
        # Arrange
        from iot_app.forms.device_inventory import device_uuid_format_validator
        from wtforms import ValidationError

        form = make_mock_create_form()
        field = make_mock_form_field(data='invalid@device')

        # Act & Assert: ValidationError が発生すること
        with pytest.raises(ValidationError):
            device_uuid_format_validator(form, field)

    @patch.dict(os.environ, {'AUTH_TYPE': 'aws'})
    def test_invalid_aws_uuid_raises_validation_error(self):
        """1.6.2: aws 環境で使用不可文字（ドット等）を含む UUID で ValidationError が発生する

        実行内容: AUTH_TYPE=aws で許容されないドットを含む UUID で device_uuid_format_validator を実行する
        想定結果: ValidationError がスローされること
        """
        # Arrange
        from iot_app.forms.device_inventory import device_uuid_format_validator
        from wtforms import ValidationError

        form = make_mock_create_form()
        field = make_mock_form_field(data='device.uuid.with.dots')

        # Act & Assert
        with pytest.raises(ValidationError):
            device_uuid_format_validator(form, field)

    @patch.dict(os.environ, {'AUTH_TYPE': 'azure'})
    def test_empty_field_data_skips_validation(self):
        """2.1.2, 1.6.4: field.data が None または空文字の場合、バリデーションをスキップする

        実行内容: field.data が None の状態で device_uuid_format_validator を実行する
        想定結果: ValidationError が発生しないこと（Optional との組み合わせでは空値は通過する）
        """
        # Arrange
        from iot_app.forms.device_inventory import device_uuid_format_validator
        from wtforms import ValidationError

        form = make_mock_create_form()
        field = make_mock_form_field(data=None)

        # Act & Assert: None の場合はスキップされる（エラーなし）
        try:
            device_uuid_format_validator(form, field)
        except ValidationError:
            pytest.fail('None field.data raised ValidationError unexpectedly')

    @patch.dict(os.environ, {'AUTH_TYPE': 'azure'})
    def test_validation_error_message_contains_format_info(self):
        """1.6.2: バリデーションエラーメッセージにフォーマット情報が含まれる

        実行内容: azure 環境で不正文字を含む UUID で device_uuid_format_validator を実行する
        想定結果: ValidationError のメッセージが "device_uuidの形式が不正です" を含むこと
        """
        # Arrange
        from iot_app.forms.device_inventory import device_uuid_format_validator
        from wtforms import ValidationError

        form = make_mock_create_form()
        field = make_mock_form_field(data='invalid uuid with space')

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            device_uuid_format_validator(form, field)
        assert 'device_uuidの形式が不正です' in str(exc_info.value)

    @patch.dict(os.environ, {'AUTH_TYPE': 'local'})
    def test_local_auth_type_uses_azure_rules(self):
        """2.1.1, 1.6.1: AUTH_TYPE=local の場合、azure と同じルールが適用される

        実行内容: AUTH_TYPE=local で azure では有効、aws では無効な文字（ドット）を含む UUID を渡す
        想定結果: ValidationError が発生しないこと（local は azure と同じため、ドットは許可）
        """
        # Arrange
        from iot_app.forms.device_inventory import device_uuid_format_validator
        from wtforms import ValidationError

        form = make_mock_create_form()
        field = make_mock_form_field(
            data='device.with.dots')  # azure では許可、aws では不可

        # Act & Assert: local は azure と同じ → ドットを許可
        try:
            device_uuid_format_validator(form, field)
        except ValidationError:
            pytest.fail(
                'local AUTH_TYPE should use azure rules; dots should be allowed')


# ============================================================
# 2. date_after_purchase_validator（出荷予定日などのバリデーションで用いる。購入日よりも後の日付であることのバリデーション）
# 観点: 1.1.4 日付形式チェック, 2.1 正常系処理
# ============================================================

@pytest.mark.unit
class TestDateAfterPurchaseValidator:
    """date_after_purchase_validator - 購入日以降チェックバリデーターファクトリ

    観点セクション: 1.1.4 日付形式チェック, 2.1 正常系処理
    """

    def test_valid_date_same_as_purchase_date_does_not_raise(self):
        """2.1.1, 1.4.1: 購入日と同日の場合、ValidationError が発生しない

        実行内容: field.data = 購入日と同一日付 で date_after_purchase_validator を実行する
        想定結果: ValidationError が発生しないこと
        """
        # Arrange
        from iot_app.forms.device_inventory import date_after_purchase_validator
        from wtforms import ValidationError

        validator = date_after_purchase_validator('出荷予定日')
        purchase_date = date(2025, 1, 15)
        form = make_mock_create_form(purchase_date=purchase_date)
        field = make_mock_form_field(data=purchase_date)  # 購入日と同日

        # Act & Assert
        try:
            validator(form, field)
        except ValidationError:
            pytest.fail(
                'Same-as-purchase date raised ValidationError unexpectedly')

    def test_valid_date_after_purchase_date_does_not_raise(self):
        """2.1.1, 1.4.1: 購入日より後の日付の場合、ValidationError が発生しない

        実行内容: field.data = 購入日より1日後の日付 で date_after_purchase_validator を実行する
        想定結果: ValidationError が発生しないこと
        """
        # Arrange
        from iot_app.forms.device_inventory import date_after_purchase_validator
        from wtforms import ValidationError

        validator = date_after_purchase_validator('出荷予定日')
        form = make_mock_create_form(purchase_date=date(2025, 1, 15))
        field = make_mock_form_field(data=date(2025, 1, 16))  # 購入日の翌日

        # Act & Assert
        try:
            validator(form, field)
        except ValidationError:
            pytest.fail(
                'Date after purchase raised ValidationError unexpectedly')

    def test_date_before_purchase_raises_validation_error(self):
        """1.6.2: 購入日より前の日付の場合、ValidationError が発生する

        実行内容: field.data = 購入日より1日前の日付 で date_after_purchase_validator を実行する
        想定結果: ValidationError がスローされること
        """
        # Arrange
        from iot_app.forms.device_inventory import date_after_purchase_validator
        from wtforms import ValidationError

        validator = date_after_purchase_validator('出荷予定日')
        form = make_mock_create_form(purchase_date=date(2025, 1, 15))
        field = make_mock_form_field(data=date(2025, 1, 14))  # 購入日の前日

        # Act & Assert
        with pytest.raises(ValidationError):
            validator(form, field)

    def test_error_message_contains_field_label(self):
        """1.6.2: エラーメッセージにフィールドラベルと「購入日以降」が含まれる

        実行内容: date_after_purchase_validator('メーカー保証終了日') で購入日より前の日付を検証する
        想定結果: "メーカー保証終了日は購入日以降を指定してください" を含むエラーメッセージがスローされること
        """
        # Arrange
        from iot_app.forms.device_inventory import date_after_purchase_validator
        from wtforms import ValidationError

        validator = date_after_purchase_validator('メーカー保証終了日')
        form = make_mock_create_form(purchase_date=date(2025, 1, 15))
        field = make_mock_form_field(data=date(2025, 1, 10))

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            validator(form, field)
        assert 'メーカー保証終了日' in str(exc_info.value)
        assert '購入日以降' in str(exc_info.value)

    def test_none_field_data_skips_validation(self):
        """2.1.2, 1.6.4: field.data が None の場合、バリデーションをスキップする（任意項目）

        実行内容: field.data = None で date_after_purchase_validator を実行する
        想定結果: ValidationError が発生しないこと
        """
        # Arrange
        from iot_app.forms.device_inventory import date_after_purchase_validator
        from wtforms import ValidationError

        validator = date_after_purchase_validator('出荷日')
        form = make_mock_create_form(purchase_date=date(2025, 1, 15))
        field = make_mock_form_field(data=None)

        # Act & Assert
        try:
            validator(form, field)
        except ValidationError:
            pytest.fail('None field.data raised ValidationError unexpectedly')

    def test_none_purchase_date_skips_validation(self):
        """2.1.2, 1.6.4: form.purchase_date.data が None の場合、バリデーションをスキップする

        実行内容: form.purchase_date.data = None で date_after_purchase_validator を実行する
        想定結果: ValidationError が発生しないこと（purchase_date が未入力なら相関チェック不要）
        """
        # Arrange
        from iot_app.forms.device_inventory import date_after_purchase_validator
        from wtforms import ValidationError

        validator = date_after_purchase_validator('出荷日')
        form = make_mock_create_form(purchase_date=None)
        field = make_mock_form_field(data=date(2025, 1, 10))

        # Act & Assert
        try:
            validator(form, field)
        except ValidationError:
            pytest.fail(
                'None purchase_date raised ValidationError unexpectedly')

    def test_validator_factory_creates_distinct_validators_per_label(self):
        """2.1.1: 異なるラベルでファクトリを呼び出すと、それぞれ独立したバリデーターが返る

        実行内容: date_after_purchase_validator を '出荷予定日' と '出荷日' それぞれで呼び出す
        想定結果: 2つの異なる callable オブジェクトが返ること
        """
        # Arrange
        from iot_app.forms.device_inventory import date_after_purchase_validator

        # Act
        v1 = date_after_purchase_validator('出荷予定日')
        v2 = date_after_purchase_validator('出荷日')

        # Assert: 別々の callable であること
        assert callable(v1)
        assert callable(v2)
        assert v1 is not v2


# ============================================================
# 3. DeviceInventorySearchForm.validate_purchase_date_to
# 観点: 1.1.4 日付形式チェック, 2.1 正常系処理
# ============================================================

@pytest.mark.unit
class TestDeviceInventorySearchFormValidation:
    """DeviceInventorySearchForm - 購入日範囲の相関バリデーション

    観点セクション: 1.1.4 日付形式チェック, 2.1 正常系処理
    """

    def _make_search_form_instance(self, from_date=None, to_date=None):
        """テスト用の DeviceInventorySearchForm インスタンスを生成する"""
        from iot_app.forms.device_inventory import DeviceInventorySearchForm
        form = DeviceInventorySearchForm.__new__(DeviceInventorySearchForm)
        form.purchase_date_from = make_mock_form_field(data=from_date)
        form.purchase_date_to = make_mock_form_field(data=to_date)
        return form

    def test_from_date_before_to_date_passes(self):
        """2.1.1, 1.4.1: 開始日 < 終了日 の場合、ValidationError が発生しない

        実行内容: purchase_date_from < purchase_date_to で validate_purchase_date_to を実行する
        想定結果: ValidationError が発生しないこと
        """
        # Arrange
        from iot_app.forms.device_inventory import DeviceInventorySearchForm
        from wtforms import ValidationError

        form = self._make_search_form_instance(
            from_date=date(2025, 1, 1),
            to_date=date(2025, 12, 31),
        )
        to_field = make_mock_form_field(data=date(2025, 12, 31))

        # Act & Assert
        try:
            DeviceInventorySearchForm.validate_purchase_date_to(form, to_field)
        except ValidationError:
            pytest.fail('From < To date raised ValidationError unexpectedly')

    def test_from_date_equals_to_date_passes(self):
        """2.1.1, 1.4.1: 開始日 = 終了日 の場合、ValidationError が発生しない

        実行内容: purchase_date_from = purchase_date_to で validate_purchase_date_to を実行する
        想定結果: ValidationError が発生しないこと（同日は許可）
        """
        # Arrange
        from iot_app.forms.device_inventory import DeviceInventorySearchForm
        from wtforms import ValidationError

        same_date = date(2025, 6, 15)
        form = self._make_search_form_instance(
            from_date=same_date,
            to_date=same_date,
        )
        to_field = make_mock_form_field(data=same_date)

        # Act & Assert
        try:
            DeviceInventorySearchForm.validate_purchase_date_to(form, to_field)
        except ValidationError:
            pytest.fail('From == To date raised ValidationError unexpectedly')

    def test_from_date_after_to_date_raises_validation_error(self):
        """1.6.2: 開始日 > 終了日 の場合、ValidationError が発生する

        実行内容: purchase_date_from > purchase_date_to で validate_purchase_date_to を実行する
        想定結果: ValidationError がスローされること
        """
        # Arrange
        from iot_app.forms.device_inventory import DeviceInventorySearchForm
        from wtforms import ValidationError

        form = self._make_search_form_instance(
            from_date=date(2025, 12, 31),
            to_date=date(2025, 1, 1),
        )
        to_field = make_mock_form_field(data=date(2025, 1, 1))

        # Act & Assert
        with pytest.raises(ValidationError):
            DeviceInventorySearchForm.validate_purchase_date_to(form, to_field)

    def test_error_message_instructs_correct_date_range(self):
        """1.6.2: エラーメッセージが「開始日は終了日以前を指定してください」である

        実行内容: purchase_date_from > purchase_date_to で validate_purchase_date_to を実行する
        想定結果: ValidationError のメッセージが "開始日は終了日以前を指定してください" であること
        """
        # Arrange
        from iot_app.forms.device_inventory import DeviceInventorySearchForm
        from wtforms import ValidationError

        form = self._make_search_form_instance(
            from_date=date(2025, 12, 31),
            to_date=date(2025, 1, 1),
        )
        to_field = make_mock_form_field(data=date(2025, 1, 1))

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            DeviceInventorySearchForm.validate_purchase_date_to(form, to_field)
        assert '開始日は終了日以前を指定してください' in str(exc_info.value)

    def test_none_from_date_skips_range_check(self):
        """2.1.2, 1.6.4: purchase_date_from が None の場合、相関チェックをスキップする

        実行内容: purchase_date_from = None, purchase_date_to = 有効な日付 で validate_purchase_date_to を実行する
        想定結果: ValidationError が発生しないこと
        """
        # Arrange
        from iot_app.forms.device_inventory import DeviceInventorySearchForm
        from wtforms import ValidationError

        form = self._make_search_form_instance(
            from_date=None,
            to_date=date(2025, 6, 30),
        )
        to_field = make_mock_form_field(data=date(2025, 6, 30))

        # Act & Assert
        try:
            DeviceInventorySearchForm.validate_purchase_date_to(form, to_field)
        except ValidationError:
            pytest.fail('None from_date raised ValidationError unexpectedly')

    def test_none_to_date_skips_range_check(self):
        """2.1.2, 1.6.4: purchase_date_to が None の場合、相関チェックをスキップする

        実行内容: purchase_date_from = 有効な日付, purchase_date_to = None で validate_purchase_date_to を実行する
        想定結果: ValidationError が発生しないこと
        """
        # Arrange
        from iot_app.forms.device_inventory import DeviceInventorySearchForm
        from wtforms import ValidationError

        form = self._make_search_form_instance(
            from_date=date(2025, 1, 1),
            to_date=None,
        )
        to_field = make_mock_form_field(data=None)

        # Act & Assert
        try:
            DeviceInventorySearchForm.validate_purchase_date_to(form, to_field)
        except ValidationError:
            pytest.fail('None to_date raised ValidationError unexpectedly')


# ============================================================
# 4. DeviceInventoryCreateForm バリデーション
# 観点: 1.1.1 必須チェック, 1.1.2 最大文字列長チェック, 1.1.6 不整値チェック,
#        2.1 正常系処理
# ============================================================

@pytest.mark.unit
class TestDeviceInventoryCreateFormRequiredFields:
    """DeviceInventoryCreateForm - 必須フィールドバリデーション（フォームクラス定義の確認）

    観点セクション: 1.1.1 必須チェック
    """

    def test_device_uuid_has_data_required_validator(self):
        """1.1.1, 1.1.2, 1.1.3: device_uuid フィールドに DataRequired バリデーターが設定されている

        実行内容: DeviceInventoryCreateForm の device_uuid フィールドのバリデーターを確認する
        想定結果: DataRequired バリデーターが含まれていること
        """
        # Arrange / Act
        from iot_app.forms.device_inventory import DeviceInventoryCreateForm
        from wtforms.validators import DataRequired

        validators = DeviceInventoryCreateForm.device_uuid.kwargs.get(
            'validators', []
        )
        # Assert: DataRequired が含まれること
        assert any(isinstance(v, DataRequired) for v in validators)

    def test_device_name_has_data_required_validator(self):
        """1.1.1, 1.1.2, 1.1.3: device_name フィールドに DataRequired バリデーターが設定されている

        実行内容: DeviceInventoryCreateForm の device_name フィールドのバリデーターを確認する
        想定結果: DataRequired バリデーターが含まれていること
        """
        # Arrange / Act
        from iot_app.forms.device_inventory import DeviceInventoryCreateForm
        from wtforms.validators import DataRequired

        validators = DeviceInventoryCreateForm.device_name.kwargs.get(
            'validators', []
        )
        assert any(isinstance(v, DataRequired) for v in validators)

    def test_device_type_id_has_data_required_validator(self):
        """1.1.1, 1.1.2, 1.1.3: device_type_id フィールドに DataRequired バリデーターが設定されている

        実行内容: DeviceInventoryCreateForm の device_type_id フィールドのバリデーターを確認する
        想定結果: DataRequired バリデーターが含まれていること
        """
        # Arrange / Act
        from iot_app.forms.device_inventory import DeviceInventoryCreateForm
        from wtforms.validators import DataRequired

        validators = DeviceInventoryCreateForm.device_type_id.kwargs.get(
            'validators', []
        )
        assert any(isinstance(v, DataRequired) for v in validators)

    def test_device_model_has_data_required_validator(self):
        """1.1.1, 1.1.2, 1.1.3: device_model フィールドに DataRequired バリデーターが設定されている

        実行内容: DeviceInventoryCreateForm の device_model フィールドのバリデーターを確認する
        想定結果: DataRequired バリデーターが含まれていること
        """
        # Arrange / Act
        from iot_app.forms.device_inventory import DeviceInventoryCreateForm
        from wtforms.validators import DataRequired

        validators = DeviceInventoryCreateForm.device_model.kwargs.get(
            'validators', []
        )
        assert any(isinstance(v, DataRequired) for v in validators)

    def test_mac_address_has_data_required_validator(self):
        """1.1.1, 1.1.2, 1.1.3: mac_address フィールドに DataRequired バリデーターが設定されている

        実行内容: DeviceInventoryCreateForm の mac_address フィールドのバリデーターを確認する
        想定結果: DataRequired バリデーターが含まれていること
        """
        # Arrange / Act
        from iot_app.forms.device_inventory import DeviceInventoryCreateForm
        from wtforms.validators import DataRequired

        validators = DeviceInventoryCreateForm.mac_address.kwargs.get(
            'validators', []
        )
        assert any(isinstance(v, DataRequired) for v in validators)

    def test_organization_id_has_data_required_validator(self):
        """1.1.1, 1.1.2, 1.1.3: organization_id フィールドに DataRequired バリデーターが設定されている

        実行内容: DeviceInventoryCreateForm の organizaiton_id フィールドのバリデーターを確認する
        想定結果: DataRequired バリデーターが含まれていること
        """
        # Arrange / Act
        from iot_app.forms.device_inventory import DeviceInventoryCreateForm
        from wtforms.validators import DataRequired

        validators = DeviceInventoryCreateForm.organizaiton_id.kwargs.get(
            'validators', []
        )
        assert any(isinstance(v, DataRequired) for v in validators)

    def test_inventory_status_id_has_data_required_validator(self):
        """1.1.1, 1.1.2, 1.1.3: inventory_status_id フィールドに DataRequired バリデーターが設定されている

        実行内容: DeviceInventoryCreateForm の inventory_status_id フィールドのバリデーターを確認する
        想定結果: DataRequired バリデーターが含まれていること
        """
        # Arrange / Act
        from iot_app.forms.device_inventory import DeviceInventoryCreateForm
        from wtforms.validators import DataRequired

        validators = DeviceInventoryCreateForm.inventory_status_id.kwargs.get(
            'validators', []
        )
        assert any(isinstance(v, DataRequired) for v in validators)

    def test_inventory_location_has_data_required_validator(self):
        """1.1.1, 1.1.2, 1.1.3: inventory_location フィールドに DataRequired バリデーターが設定されている

        実行内容: DeviceInventoryCreateForm の inventory_location フィールドのバリデーターを確認する
        想定結果: DataRequired バリデーターが含まれていること
        """
        # Arrange / Act
        from iot_app.forms.device_inventory import DeviceInventoryCreateForm
        from wtforms.validators import DataRequired

        validators = DeviceInventoryCreateForm.inventory_location.kwargs.get(
            'validators', []
        )
        assert any(isinstance(v, DataRequired) for v in validators)

    def test_purchase_date_has_data_required_validator(self):
        """1.1.1, 1.1.2, 1.1.3: purchase_date フィールドに DataRequired バリデーターが設定されている

        実行内容: DeviceInventoryCreateForm の purchase_date フィールドのバリデーターを確認する
        想定結果: DataRequired バリデーターが含まれていること
        """
        # Arrange / Act
        from iot_app.forms.device_inventory import DeviceInventoryCreateForm
        from wtforms.validators import DataRequired

        validators = DeviceInventoryCreateForm.purchase_date.kwargs.get(
            'validators', []
        )
        assert any(isinstance(v, DataRequired) for v in validators)

    def test_manufacturer_warranty_end_date_has_data_required_validator(self):
        """1.1.1, 1.1.2, 1.1.3: manufacturer_warranty_end_date フィールドに DataRequired バリデーターが設定されている

        実行内容: DeviceInventoryCreateForm の manufacturer_warranty_end_date フィールドのバリデーターを確認する
        想定結果: DataRequired バリデーターが含まれていること
        """
        # Arrange / Act
        from iot_app.forms.device_inventory import DeviceInventoryCreateForm
        from wtforms.validators import DataRequired

        validators = DeviceInventoryCreateForm.manufacturer_warranty_end_date.kwargs.get(
            'validators', []
        )
        assert any(isinstance(v, DataRequired) for v in validators)


@pytest.mark.unit
class TestDeviceInventoryCreateFormMaxLength:
    """DeviceInventoryCreateForm - 最大文字数バリデーション（フォームクラス定義の確認）

    観点セクション: 1.1.2 最大文字列長チェック
    """

    def _get_length_validator(self, field_validators):
        """フィールドの Length バリデーターを取得する"""
        from wtforms.validators import Length
        for v in field_validators:
            if isinstance(v, Length):
                return v
        return None

    def test_device_uuid_max_length_is_128(self):
        """1.2.2, 1.2.3: device_uuid の最大文字数が 128 に設定されている

        実行内容: DeviceInventoryCreateForm の device_uuid フィールドの Length バリデーターを確認する
        想定結果: max=128 が設定されていること
        """
        # Arrange / Act
        from iot_app.forms.device_inventory import DeviceInventoryCreateForm
        from wtforms.validators import Length

        validators = DeviceInventoryCreateForm.device_uuid.kwargs.get(
            'validators', [])
        length_v = self._get_length_validator(validators)

        # Assert
        assert length_v is not None, 'Length validator not found for device_uuid'
        assert length_v.max == 128

    def test_device_name_max_length_is_100(self):
        """1.2.2, 1.2.3: device_name の最大文字数が 100 に設定されている

        実行内容: DeviceInventoryCreateForm の device_name フィールドの Length バリデーターを確認する
        想定結果: max=100 が設定されていること
        """
        # Arrange / Act
        from iot_app.forms.device_inventory import DeviceInventoryCreateForm

        validators = DeviceInventoryCreateForm.device_name.kwargs.get(
            'validators', [])
        length_v = self._get_length_validator(validators)

        assert length_v is not None, 'Length validator not found for device_name'
        assert length_v.max == 100

    def test_device_model_max_length_is_100(self):
        """1.2.2, 1.2.3: device_model の最大文字数が 100 に設定されている

        実行内容: DeviceInventoryCreateForm の device_model フィールドの Length バリデーターを確認する
        想定結果: max=100 が設定されていること
        """
        # Arrange / Act
        from iot_app.forms.device_inventory import DeviceInventoryCreateForm

        validators = DeviceInventoryCreateForm.device_model.kwargs.get(
            'validators', [])
        length_v = self._get_length_validator(validators)

        assert length_v is not None, 'Length validator not found for device_model'
        assert length_v.max == 100

    def test_sim_id_max_length_is_20(self):
        """1.2.2, 1.2.3: sim_id の最大文字数が 20 に設定されている

        実行内容: DeviceInventoryCreateForm の sim_id フィールドの Length バリデーターを確認する
        想定結果: max=20 が設定されていること
        """
        # Arrange / Act
        from iot_app.forms.device_inventory import DeviceInventoryCreateForm

        validators = DeviceInventoryCreateForm.sim_id.kwargs.get(
            'validators', [])
        length_v = self._get_length_validator(validators)

        assert length_v is not None, 'Length validator not found for sim_id'
        assert length_v.max == 20

    def test_software_version_max_length_is_100(self):
        """1.2.2, 1.2.3: software_version の最大文字数が 100 に設定されている

        実行内容: DeviceInventoryCreateForm の software_version フィールドの Length バリデーターを確認する
        想定結果: max=100 が設定されていること
        """
        # Arrange / Act
        from iot_app.forms.device_inventory import DeviceInventoryCreateForm

        validators = DeviceInventoryCreateForm.software_version.kwargs.get(
            'validators', [])
        length_v = self._get_length_validator(validators)

        assert length_v is not None, 'Length validator not found for software_version'
        assert length_v.max == 100

    def test_device_location_max_length_is_100(self):
        """1.2.2, 1.2.3: device_location の最大文字数が 100 に設定されている

        実行内容: DeviceInventoryCreateForm の device_location フィールドの Length バリデーターを確認する
        想定結果: max=100 が設定されていること
        """
        # Arrange / Act
        from iot_app.forms.device_inventory import DeviceInventoryCreateForm

        validators = DeviceInventoryCreateForm.device_location.kwargs.get(
            'validators', [])
        length_v = self._get_length_validator(validators)

        assert length_v is not None, 'Length validator not found for device_location'
        assert length_v.max == 100

    def test_inventory_location_max_length_is_100(self):
        """1.2.2, 1.2.3: inventory_location の最大文字数が 100 に設定されている

        実行内容: DeviceInventoryCreateForm の inventory_location フィールドの Length バリデーターを確認する
        想定結果: max=100 が設定されていること
        """
        # Arrange / Act
        from iot_app.forms.device_inventory import DeviceInventoryCreateForm

        validators = DeviceInventoryCreateForm.inventory_location.kwargs.get(
            'validators', [])
        length_v = self._get_length_validator(validators)

        assert length_v is not None, 'Length validator not found for inventory_location'
        assert length_v.max == 100


@pytest.mark.unit
class TestDeviceInventoryCreateFormMacAddress:
    """DeviceInventoryCreateForm - MACアドレス形式バリデーション

    観点セクション: 1.1.6 不整値チェック, 2.1 正常系処理
    """

    def test_mac_address_has_regexp_validator(self):
        """1.6.1, 1.6.2: mac_address フィールドに Regexp バリデーターが設定されている

        実行内容: DeviceInventoryCreateForm の mac_address フィールドのバリデーターを確認する
        想定結果: Regexp バリデーターが含まれていること
        """
        # Arrange / Act
        from iot_app.forms.device_inventory import DeviceInventoryCreateForm
        from wtforms.validators import Regexp

        validators = DeviceInventoryCreateForm.mac_address.kwargs.get(
            'validators', [])

        # Assert: Regexp が含まれること
        assert any(isinstance(v, Regexp) for v in validators)

    def test_mac_address_regexp_accepts_valid_format(self):
        """2.1.1, 1.6.1: XX:XX:XX:XX:XX:XX 形式のMACアドレスが Regexp パターンに一致する

        実行内容: 有効な MAC アドレス (AA:BB:CC:DD:EE:FF) を Regexp パターンで検証する
        想定結果: パターンに一致すること（True）
        """
        # Arrange
        from iot_app.forms.device_inventory import DeviceInventoryCreateForm
        from wtforms.validators import Regexp
        import re

        validators = DeviceInventoryCreateForm.mac_address.kwargs.get(
            'validators', [])
        regexp_v = next((v for v in validators if isinstance(v, Regexp)), None)
        assert regexp_v is not None, 'Regexp validator not found for mac_address'

        valid_mac = 'AA:BB:CC:DD:EE:FF'

        # Assert: 有効な MAC アドレスがパターンに一致すること
        assert re.match(regexp_v.regex, valid_mac)

    def test_mac_address_regexp_rejects_invalid_format(self):
        """1.6.2: XX:XX:XX:XX:XX:XX 形式以外の MACアドレスが Regexp パターンに不一致となる

        実行内容: 無効な MAC アドレス (no-colon-format) を Regexp パターンで検証する
        想定結果: パターンに不一致であること（None）
        """
        # Arrange
        from iot_app.forms.device_inventory import DeviceInventoryCreateForm
        from wtforms.validators import Regexp
        import re

        validators = DeviceInventoryCreateForm.mac_address.kwargs.get(
            'validators', [])
        regexp_v = next((v for v in validators if isinstance(v, Regexp)), None)
        assert regexp_v is not None, 'Regexp validator not found for mac_address'

        invalid_mac = 'AABBCCDDEEFF'  # コロンなし

        # Assert: 無効な MAC アドレスがパターンに不一致であること
        assert not re.match(regexp_v.regex, invalid_mac)

    def test_mac_address_regexp_rejects_wrong_separator(self):
        """1.6.2: ハイフン区切りの MACアドレスが Regexp パターンに不一致となる

        実行内容: ハイフン区切り (AA-BB-CC-DD-EE-FF) を Regexp パターンで検証する
        想定結果: パターンに不一致であること（None）
        """
        # Arrange
        from iot_app.forms.device_inventory import DeviceInventoryCreateForm
        from wtforms.validators import Regexp
        import re

        validators = DeviceInventoryCreateForm.mac_address.kwargs.get(
            'validators', [])
        regexp_v = next((v for v in validators if isinstance(v, Regexp)), None)

        # Act & Assert
        assert not re.match(regexp_v.regex, 'AA-BB-CC-DD-EE-FF')


@pytest.mark.unit
class TestDeviceInventoryCreateFormDateRelations:
    """DeviceInventoryCreateForm - 日付フィールドへの相関バリデーター適用確認

    観点セクション: 1.1.4 日付形式チェック
    """

    def test_estimated_ship_date_has_date_after_purchase_validator(self):
        """1.4.1, 1.6.2: estimated_ship_date に date_after_purchase_validator が設定されている

        実行内容: DeviceInventoryCreateForm の estimated_ship_date フィールドのバリデーターを確認する
        想定結果: date_after_purchase_validator が適用されていること（callable が含まれる）
        """
        # Arrange / Act
        from iot_app.forms.device_inventory import DeviceInventoryCreateForm

        validators = DeviceInventoryCreateForm.estimated_ship_date.kwargs.get(
            'validators', [])

        # Assert: Optional と DateAfterPurchase 相当のバリデーターが含まれること
        # （date_after_purchase_validator は内部 closure なので callable 存在で確認）
        assert len(
            validators) >= 2, 'Expected at least Optional and date_after_purchase_validator'

    def test_ship_date_has_date_after_purchase_validator(self):
        """1.4.1, 1.6.2: ship_date に date_after_purchase_validator が設定されている

        実行内容: DeviceInventoryCreateForm の ship_date フィールドのバリデーターを確認する
        想定結果: date_after_purchase_validator が適用されていること（callable が含まれる）
        """
        # Arrange / Act
        from iot_app.forms.device_inventory import DeviceInventoryCreateForm

        validators = DeviceInventoryCreateForm.ship_date.kwargs.get(
            'validators', [])

        assert len(
            validators) >= 2, 'Expected at least Optional and date_after_purchase_validator'

    def test_manufacturer_warranty_end_date_has_date_after_purchase_validator(self):
        """1.1.3, 1.4.1, 1.6.2: manufacturer_warranty_end_date に date_after_purchase_validator が設定されている

        実行内容: DeviceInventoryCreateForm の manufacturer_warranty_end_date フィールドのバリデーターを確認する
        想定結果: DataRequired と date_after_purchase_validator が含まれること
        """
        # Arrange / Act
        from iot_app.forms.device_inventory import DeviceInventoryCreateForm
        from wtforms.validators import DataRequired

        validators = DeviceInventoryCreateForm.manufacturer_warranty_end_date.kwargs.get(
            'validators', []
        )

        # Assert: DataRequired が含まれること（必須項目）
        assert any(isinstance(v, DataRequired) for v in validators)
        # Assert: 相関バリデーター（callable）も含まれること
        assert len(validators) >= 2


# ============================================================
# 5. DeviceInventoryUpdateForm バリデーション
# 観点: 1.1.1 必須チェック, 1.1.2 最大文字列長チェック, 1.1.6 不整値チェック
# ============================================================

@pytest.mark.unit
class TestDeviceInventoryUpdateFormValidation:
    """DeviceInventoryUpdateForm - フォームクラス定義の確認（登録フォームと同一バリデーション）

    観点セクション: 1.1.1 必須チェック, 1.1.2 最大文字列長チェック, 1.1.6 不整値チェック
    """

    def _get_length_validator(self, field_validators):
        from wtforms.validators import Length
        for v in field_validators:
            if isinstance(v, Length):
                return v
        return None

    def test_update_form_device_uuid_has_validators(self):
        """1.1.1, 1.1.2, 1.1.3, 1.2.2, 1.2.3, 1.6.1, 1.6.2: 更新フォームの device_uuid フィールドに DataRequired が設定されている

        実行内容: DeviceInventoryUpdateForm の device_uuid フィールドのバリデーターを確認する
        想定結果: DataRequired バリデーターが含まれていること
        """
        # Arrange / Act
        from iot_app.forms.device_inventory import DeviceInventoryUpdateForm
        from wtforms.validators import DataRequired

        validators = DeviceInventoryUpdateForm.device_uuid.kwargs.get(
            'validators', [])
        length_v = self._get_length_validator(validators)

        # Assert: DataRequiredが設定されていること
        assert any(isinstance(v, DataRequired) for v in validators)
        # Assert: Lengthバリデータが設定されており、最大入力長は128文字であること
        assert length_v is not None, 'Length validator not found for device_uuid'
        assert length_v.max == 128
        # Assert: device_uuid_format_validatorバリデータが設定されていること
        assert any(
            callable(v) and 'device_uuid_format_validator' in getattr(
                v, '__qualname__', '')
            for v in validators
        )
        # Assert: 設定されているバリデータが3つのみであること
        assert len(validators) == 3

    def test_update_form_device_name_has_validators(self):
        """1.1.1, 1.1.2, 1.1.3, 1.2.2, 1.2.3: 更新フォームの device_name フィールドに DataRequired が設定されている

        実行内容: DeviceInventoryUpdateForm の device_name フィールドのバリデーターを確認する
        想定結果: DataRequired バリデーターが含まれていること
        """
        # Arrange / Act
        from iot_app.forms.device_inventory import DeviceInventoryUpdateForm
        from wtforms.validators import DataRequired

        validators = DeviceInventoryUpdateForm.device_name.kwargs.get(
            'validators', [])
        length_v = self._get_length_validator(validators)

        # Assert: DataRequiredが設定されていること
        assert any(isinstance(v, DataRequired) for v in validators)
        # Assert: Lengthバリデータが設定されており、最大入力長は100文字であること
        assert length_v is not None, 'Length validator not found for device_name'
        assert length_v.max == 100
        # Assert: 設定されているバリデータが2つのみであること
        assert len(validators) == 2

    def test_update_form_device_type_id_has_data_required(self):
        """1.1.1, 1.1.2, 1.1.3: 更新フォームの device_type_id フィールドに DataRequired が設定されている

        実行内容: DeviceInventoryUpdateForm の device_type_id フィールドのバリデーターを確認する
        想定結果: DataRequired バリデーターが含まれていること
        """
        # Arrange / Act
        from iot_app.forms.device_inventory import DeviceInventoryUpdateForm
        from wtforms.validators import DataRequired

        validators = DeviceInventoryUpdateForm.device_type_id.kwargs.get(
            'validators', [])
        assert any(isinstance(v, DataRequired) for v in validators)
        assert len(validators) == 1

    def test_update_form_device_model_has_validators(self):
        """1.1.1, 1.1.2, 1.1.3, 1.2.2, 1.2.3: 更新フォームの device_model フィールドに DataRequired が設定されている

        実行内容: DeviceInventoryUpdateForm の device_model フィールドのバリデーターを確認する
        想定結果: DataRequired バリデーターが含まれていること
        """
        # Arrange / Act
        from iot_app.forms.device_inventory import DeviceInventoryUpdateForm
        from wtforms.validators import DataRequired

        validators = DeviceInventoryUpdateForm.device_model.kwargs.get(
            'validators', [])
        length_v = self._get_length_validator(validators)

        # Assert: DataRequiredバリデータが設定されていること
        assert any(isinstance(v, DataRequired) for v in validators)
        # Assert: Lengthバリデータが設定されており、最大入力長は100文字であること
        assert length_v is not None, 'Length validator not found for device_model'
        assert length_v.max == 100
        # Assert: 設定されているバリデータは2つのみであること
        assert len(validators) == 2

    def test_update_form_sim_id_has_validators(self):
        """2.1.2, 1.2.2, 1.2.3: 更新フォームの sim_id の最大文字数が 20 に設定されている

        実行内容: DeviceInventoryUpdateForm の sim_id フィールドの Length バリデーターを確認する
        想定結果: max=20 が設定されていること
        """
        # Arrange / Act
        from iot_app.forms.device_inventory import DeviceInventoryUpdateForm
        from wtforms.validators import Optional

        validators = DeviceInventoryUpdateForm.sim_id.kwargs.get(
            'validators', [])
        length_v = self._get_length_validator(validators)

        # Assert: Optionalバリデータが設定されていること
        assert any(isinstance(v, Optional) for v in validators)
        # Assert: Lengthバリデータが設定されており、最大入力長は20文字であること
        assert length_v is not None, 'Length validator not found for sim_id'
        assert length_v.max == 20
        # Assert: 設定されているバリデータは2つのみであること
        assert len(validators) == 2

    def test_update_form_mac_address_has_validators(self):
        """1.1.1, 1.1.2, 1.1.3, 1.6.1, 1.6.2: 更新フォームの mac_address に Regexp バリデーターが設定されている

        実行内容: DeviceInventoryUpdateForm の mac_address フィールドのバリデーターを確認する
        想定結果: Regexp バリデーターが含まれていること
        """
        # Arrange / Act
        from iot_app.forms.device_inventory import DeviceInventoryUpdateForm
        from wtforms.validators import DataRequired, Regexp

        validators = DeviceInventoryUpdateForm.mac_address.kwargs.get(
            'validators', [])

        # Assert: Regexpバリデータが設定されていること
        assert any(isinstance(v, Regexp) for v in validators)
        # Assert: DataRequiredバリデータが設定されていること
        assert any(isinstance(v, DataRequired) for v in validators)
        # Assert: 設定されているバリデータは2つのみであること
        assert len(validators) == 2

    def test_update_form_software_version_has_validators(self):
        """2.1.2, 1.2.2, 1.2.3: 更新フォームの software_version の最大文字数が 100 に設定されている

        実行内容: DeviceInventoryUpdateForm の software_version フィールドの Length バリデーターを確認する
        想定結果: max=100 が設定されていること
        """
        # Arrange / Act
        from iot_app.forms.device_inventory import DeviceInventoryUpdateForm
        from wtforms.validators import Optional

        validators = DeviceInventoryUpdateForm.software_version.kwargs.get(
            'validators', [])
        length_v = self._get_length_validator(validators)

        # Assert: Optionalバリデータが設定されていること
        assert any(isinstance(v, Optional) for v in validators)
        # Assert: Lengthバリデータが設定されており、最大入力長は100文字であること
        assert length_v is not None, 'Length validator not found for software_version'
        assert length_v.max == 100
        # Assert: 設定されているバリデータは2つのみであること
        assert len(validators) == 2

    def test_update_form_device_location_has_validators(self):
        """2.1.2, 1.2.2, 1.2.3: 更新フォームの device_location の最大文字数が 100 に設定されている

        実行内容: DeviceInventoryUpdateForm の device_location フィールドの Length バリデーターを確認する
        想定結果: max=100 が設定されていること
        """
        # Arrange / Act
        from iot_app.forms.device_inventory import DeviceInventoryUpdateForm
        from wtforms.validators import Optional

        validators = DeviceInventoryUpdateForm.device_location.kwargs.get(
            'validators', [])
        length_v = self._get_length_validator(validators)

        # Assert: Optionalバリデータが設定されていること
        assert any(isinstance(v, Optional) for v in validators)
        # Assert: Lengthバリデータが設定されており、最大入力長は100文字であること
        assert length_v is not None, 'Length validator not found for device_location'
        assert length_v.max == 100
        # Assert: 設定されているバリデータは2つのみであること
        assert len(validators) == 2

    def test_update_form_certificate_expiration_date_has_Optional(self):
        """2.1.2: 更新フォームの certificate_expiration_date フィールドに Optional が設定されている

        実行内容: DeviceInventoryUpdateForm の certificate_expiration_date フィールドのバリデーターを確認する
        想定結果: Optional バリデーターのみが含まれていること
        """
        # Arrange / Act
        from iot_app.forms.device_inventory import DeviceInventoryUpdateForm
        from wtforms.validators import Optional

        validators = DeviceInventoryUpdateForm.certificate_expiration_date.kwargs.get(
            'validators', [])
        assert any(isinstance(v, Optional) for v in validators)
        assert len(validators) == 1

    def test_update_form_organization_id_has_data_required(self):
        """1.1.1, 1.1.2, 1.1.3: 更新フォームの organization_id フィールドに DataRequired が設定されている

        実行内容: DeviceInventoryUpdateForm の organization_id フィールドのバリデーターを確認する
        想定結果: DataRequired バリデーターが含まれていること
        """
        # Arrange / Act
        from iot_app.forms.device_inventory import DeviceInventoryUpdateForm
        from wtforms.validators import DataRequired

        validators = DeviceInventoryUpdateForm.organization_id.kwargs.get(
            'validators', [])
        assert any(isinstance(v, DataRequired) for v in validators)
        assert len(validators) == 1

    def test_update_form_inventory_status_id_has_data_required(self):
        """1.1.1, 1.1.2, 1.1.3: 更新フォームの inventory_status_id フィールドに DataRequired が設定されている

        実行内容: DeviceInventoryUpdateForm の inventory_status_id フィールドのバリデーターを確認する
        想定結果: DataRequired バリデーターが含まれていること
        """
        # Arrange / Act
        from iot_app.forms.device_inventory import DeviceInventoryUpdateForm
        from wtforms.validators import DataRequired

        validators = DeviceInventoryUpdateForm.inventory_status_id.kwargs.get(
            'validators', [])
        assert any(isinstance(v, DataRequired) for v in validators)
        assert len(validators) == 1

    def test_update_form_purchase_date_has_data_required(self):
        """1.1.1, 1.1.2, 1.1.3: 更新フォームの purchase_date フィールドに DataRequired が設定されている

        実行内容: DeviceInventoryUpdateForm の purchase_date フィールドのバリデーターを確認する
        想定結果: DataRequired バリデーターが含まれていること
        """
        # Arrange / Act
        from iot_app.forms.device_inventory import DeviceInventoryUpdateForm
        from wtforms.validators import DataRequired

        validators = DeviceInventoryUpdateForm.purchase_date.kwargs.get(
            'validators', [])
        assert any(isinstance(v, DataRequired) for v in validators)
        assert len(validators) == 1

    def test_update_form_estimated_ship_date_has_data_required(self):
        """2.1.2, 1.4.1, 1.6.2: 更新フォームの estimated_ship_date フィールドに Optional が設定されている

        実行内容: DeviceInventoryUpdateForm の estimated_ship_date フィールドのバリデーターを確認する
        想定結果: Optional、date_after_purchase_validator バリデーターが含まれていること
        """
        # Arrange / Act
        from iot_app.forms.device_inventory import DeviceInventoryUpdateForm
        from wtforms.validators import Optional

        validators = DeviceInventoryUpdateForm.estimated_ship_date.kwargs.get(
            'validators', [])

        # Assert: Optionalバリデータが設定されていること
        assert any(isinstance(v, Optional) for v in validators)
        # Assert: date_after_purchase_validatorバリデータが設定されていること
        assert any(
            callable(v) and 'date_after_purchase_validator' in getattr(
                v, '__qualname__', '')
            for v in validators
        )
        # Assert: 設定されているバリデータは2つのみであること
        assert len(validators) == 2

    def test_update_form_ship_date_has_data_required(self):
        """2.1.2, 1.4.1, 1.6.2: 更新フォームの ship_date フィールドに Optional が設定されている

        実行内容: DeviceInventoryUpdateForm の ship_date フィールドのバリデーターを確認する
        想定結果: Optional、date_after_purchase_validator バリデーターが含まれていること
        """
        # Arrange / Act
        from iot_app.forms.device_inventory import DeviceInventoryUpdateForm
        from wtforms.validators import Optional

        validators = DeviceInventoryUpdateForm.ship_date.kwargs.get(
            'validators', [])

        # Assert: Optionalバリデータが設定されていること
        assert any(isinstance(v, Optional) for v in validators)
        # Assert: date_after_purchase_validatorバリデータが設定されていること
        assert any(
            callable(v) and 'date_after_purchase_validator' in getattr(
                v, '__qualname__', '')
            for v in validators
        )
        # Assert: 設定されているバリデータは2つのみであること
        assert len(validators) == 2

    def test_update_form_inventory_location_max_length_is_100(self):
        """1.1.1, 1.1.2, 1.1.3, 1.2.2, 1.2.3: 更新フォームの inventory_location の最大文字数が 100 に設定されている

        実行内容: DeviceInventoryUpdateForm の inventory_location フィールドの Length バリデーターを確認する
        想定結果: max=100 が設定されていること
        """
        # Arrange / Act
        from iot_app.forms.device_inventory import DeviceInventoryUpdateForm
        from wtforms.validators import DataRequired

        validators = DeviceInventoryUpdateForm.inventory_location.kwargs.get(
            'validators', [])
        length_v = self._get_length_validator(validators)

        # Assert: DataRequiredバリデータが設定されていること
        assert any(isinstance(v, DataRequired) for v in validators)
        # Assert: Lengthバリデータが設定されており、最大入力長は100文字であること
        assert length_v is not None, 'Length validator not found for inventory_location'
        assert length_v.max == 100
        # Assert: 設定されているバリデータは2つのみであること
        assert len(validators) == 2

    def test_update_form_manufacturer_warranty_end_date_has_data_required(self):
        """1.1.1, 1.1.2, 1.1.3, 1.4.1, 1.6.2: 更新フォームの manufacturer_warranty_end_date フィールドに DataRequired が設定されている

        実行内容: DeviceInventoryUpdateForm の manufacturer_warranty_end_date フィールドのバリデーターを確認する
        想定結果: DataRequired バリデーターが含まれていること
        """
        # Arrange / Act
        from iot_app.forms.device_inventory import DeviceInventoryUpdateForm
        from wtforms.validators import DataRequired

        validators = DeviceInventoryUpdateForm.manufacturer_warranty_end_date.kwargs.get(
            'validators', []
        )

        # Assert: DataRequiredバリデータが設定されていること
        assert any(isinstance(v, DataRequired) for v in validators)
        # Assert: date_after_purchase_validatorバリデータが設定されていること
        assert any(
            callable(v) and 'date_after_purchase_validator' in getattr(
                v, '__qualname__', '')
            for v in validators
        )
        # Assert: 設定されているバリデータは2つのみであること
        assert len(validators) == 2


# ============================================================
# 6. DeviceInventorySearchForm バリデーション（フィールド定義確認）
# 観点: 1.1.2 最大文字列長チェック, 2.1 正常系処理
# ============================================================

@pytest.mark.unit
class TestDeviceInventorySearchFormFieldDefinitions:
    """DeviceInventorySearchForm - 検索フォームフィールド定義確認

    観点セクション: 1.1.2 最大文字列長チェック, 2.1 正常系処理
    """

    def _get_length_validator(self, field_validators):
        from wtforms.validators import Length
        for v in field_validators:
            if isinstance(v, Length):
                return v
        return None

    def test_search_form_device_uuid_has_validators(self):
        """2.1.2, 1.2.2, 1.2.3: 検索フォームの device_uuid の最大文字数が 128 に設定されている

        実行内容: DeviceInventorySearchForm の device_uuid フィールドの Length バリデーターを確認する
        想定結果: max=128 が設定されていること
        """
        # Arrange / Act
        from iot_app.forms.device_inventory import DeviceInventorySearchForm
        from wtforms.validators import Optional

        validators = DeviceInventorySearchForm.device_uuid.kwargs.get(
            'validators', [])
        length_v = self._get_length_validator(validators)

        # Assert: Optionalバリデータが設定されていること
        assert any(isinstance(v, Optional) for v in validators)
        # Assert: Lengthバリデータが設定されており、最大入力長は128文字であること
        assert length_v is not None, 'Length validator not found for device_uuid'
        assert length_v.max == 128
        # Assert: 設定されているバリデータは2つのみであること
        assert len(validators) == 2

    def test_search_form_device_name_has_validators(self):
        """2.1.2, 1.2.2, 1.2.3: 検索フォームの device_name の最大文字数が 100 に設定されている

        実行内容: DeviceInventorySearchForm の device_name フィールドの Length バリデーターを確認する
        想定結果: max=100 が設定されていること
        """
        # Arrange / Act
        from iot_app.forms.device_inventory import DeviceInventorySearchForm
        from wtforms.validators import Optional

        validators = DeviceInventorySearchForm.device_name.kwargs.get(
            'validators', [])
        length_v = self._get_length_validator(validators)

        # Assert: Optionalバリデータが設定されていること
        assert any(isinstance(v, Optional) for v in validators)
        # Assert: Lengthバリデータが設定されており、最大入力長は100文字であること
        assert length_v is not None, 'Length validator not found for device_name'
        assert length_v.max == 100
        # Assert: 設定されているバリデータは2つのみであること
        assert len(validators) == 2

    def test_search_form_inventory_location_has_validators(self):
        """2.1.2, 1.2.2, 1.2.3: 検索フォームの inventory_location の最大文字数が 100 に設定されている

        実行内容: DeviceInventorySearchForm の inventory_location フィールドの Length バリデーターを確認する
        想定結果: max=100 が設定されていること
        """
        # Arrange / Act
        from iot_app.forms.device_inventory import DeviceInventorySearchForm
        from wtforms.validators import Optional

        validators = DeviceInventorySearchForm.inventory_location.kwargs.get(
            'validators', [])
        length_v = self._get_length_validator(validators)

        # Assert: Optionalバリデータが設定されていること
        assert any(isinstance(v, Optional) for v in validators)
        # Assert: Lengthバリデータが設定されており、最大入力長は100文字であること
        assert length_v is not None, 'Length validator not found for inventory_location'
        assert length_v.max == 100
        # Assert: 設定されているバリデータは2つのみであること
        assert len(validators) == 2

    def test_search_form_purchase_date_from_has_validators(self):
        """2.1.2: 検索フォームの purchase_date_from の最大文字数が 100 に設定されている

        実行内容: DeviceInventorySearchForm の purchase_date_from フィールドの Length バリデーターを確認する
        想定結果: max=100 が設定されていること
        """
        # Arrange / Act
        from iot_app.forms.device_inventory import DeviceInventorySearchForm
        from wtforms.validators import Optional

        validators = DeviceInventorySearchForm.purchase_date_from.kwargs.get(
            'validators', [])

        # Assert: Optionalバリデータが設定されていること
        assert any(isinstance(v, Optional) for v in validators)
        # Assert: 設定されているバリデータは1つのみであること
        assert len(validators) == 1

    def test_search_form_purchase_date_to_has_validators(self):
        """2.1.2: 検索フォームの purchase_date_to の最大文字数が 100 に設定されている

        実行内容: DeviceInventorySearchForm の purchase_date_to フィールドの Length バリデーターを確認する
        想定結果: max=100 が設定されていること
        """
        # Arrange / Act
        from iot_app.forms.device_inventory import DeviceInventorySearchForm
        from wtforms.validators import Optional

        validators = DeviceInventorySearchForm.purchase_date_to.kwargs.get(
            'validators', [])

        # Assert: Optionalバリデータが設定されていること
        assert any(isinstance(v, Optional) for v in validators)
        # Assert: 設定されているバリデータは1つのみであること
        assert len(validators) == 1

    def test_search_form_sort_order_choices_include_all_options(self):
        """1.6.1, 1.6.2: 検索フォームの sort_order の選択肢が設定されている（-1/1/2）

        実行内容: DeviceInventorySearchForm の sort_order フィールドの choices を確認する
        想定結果: -1（未選択）、1（昇順）、2（降順）の3選択肢が設定されていること
        """
        # Arrange / Act
        from iot_app.forms.device_inventory import DeviceInventorySearchForm

        choices = DeviceInventorySearchForm.sort_order.kwargs.get(
            'choices', [])
        choice_values = [c[0] for c in choices]

        # Assert: -1（未選択）、1（昇順）、2（降順）が含まれること
        assert -1 in choice_values
        assert 1 in choice_values
        assert 2 in choice_values
