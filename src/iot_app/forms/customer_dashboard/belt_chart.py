"""
顧客作成ダッシュボード 帯グラフガジェット登録フォーム

参照設計書:
  - docs/03-features/flask-app/customer-dashboard/belt-chart/ui-specification.md
  - docs/03-features/flask-app/customer-dashboard/belt-chart/workflow-specification.md
"""

from flask_wtf import FlaskForm
from wtforms import IntegerField, RadioField, SelectField, SelectMultipleField, StringField
from wtforms.validators import DataRequired, Length, Optional, ValidationError

from iot_app.common.messages import ERR_GADGET_ITEM_COUNT, err_max_length, err_required, err_select_required


class BeltChartGadgetForm(FlaskForm):
    """帯グラフガジェット登録フォーム

    仕様: ui-specification.md > バリデーション（ガジェット登録画面）
    """

    gadget_name = StringField(
        'タイトル',
        validators=[
            DataRequired(message=err_required('タイトル')),
            Length(max=20, message=err_max_length('タイトル', 20)),
        ],
    )

    device_mode = RadioField(
        '表示デバイス選択',
        choices=[('fixed', 'デバイス固定'), ('variable', 'デバイス可変')],
        default='variable',
        validators=[DataRequired(message=err_select_required('表示デバイス'))],
    )

    device_id = IntegerField(
        'デバイス選択',
        validators=[Optional()],
    )

    group_id = IntegerField(
        'グループ選択',
        default=1,
        validators=[DataRequired(message=err_select_required('グループ'))],
    )

    summary_method_id = IntegerField(
        '集約方法',
        default=1,
        validators=[DataRequired(message=err_select_required('集約方法'))],
    )

    measurement_item_ids = SelectMultipleField(
        '表示項目選択',
        coerce=int,
        choices=[],
    )

    gadget_size = SelectField(
        '部品サイズ',
        choices=[('0', '2x2'), ('1', '2x4')],
        default='0',
        validators=[DataRequired(message=err_select_required('部品サイズ'))],
    )

    def validate_measurement_item_ids(self, field):
        """表示項目選択: 1〜5個必須（choices が設定済みの場合のみ検証）

        choices が空（ビュー未設定）の場合は検証をスキップする。
        """
        if not field.choices:
            return
        if not field.data or len(field.data) < 1 or len(field.data) > 5:
            raise ValidationError(ERR_GADGET_ITEM_COUNT)

    def validate(self, extra_validators=None):
        result = super().validate(extra_validators)
        if self.device_mode.data == 'fixed' and not self.device_id.data:
            self.device_id.errors.append(err_select_required('デバイス'))
            result = False
        return result
