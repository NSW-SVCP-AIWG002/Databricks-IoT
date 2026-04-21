from flask_wtf import FlaskForm
from wtforms import FloatField, SelectField, StringField
from wtforms.validators import DataRequired, Length, Optional

from iot_app.common.messages import (
    ERR_MAX_VALUE_GREATER_THAN_MIN,
    ERR_MIN_VALUE_LESS_THAN_MAX,
    err_max_length,
    err_required,
    err_select_required,
)


class BarChartGadgetForm(FlaskForm):
    """棒グラフガジェット登録フォーム"""

    title = StringField(
        'タイトル',
        validators=[
            DataRequired(message=err_required('タイトル')),
            Length(max=20, message=err_max_length('タイトル', 20)),
        ]
    )
    device_mode = SelectField(
        '表示デバイス',
        choices=[('fixed', 'デバイス固定'), ('variable', 'デバイス可変')],
        validators=[DataRequired(message=err_select_required('表示デバイス'))],
    )
    device_id = SelectField('デバイス', coerce=int, validators=[Optional()])
    group_id = SelectField('グループ', coerce=int, validators=[DataRequired(message=err_select_required('グループ'))])
    summary_method_id = SelectField('集約方法', coerce=int, validators=[DataRequired(message=err_select_required('集約方法'))])
    measurement_item_id = SelectField('表示項目', coerce=int, validators=[DataRequired(message=err_select_required('表示項目'))])
    min_value = FloatField('最小値', validators=[Optional()])
    max_value = FloatField('最大値', validators=[Optional()])

    def validate(self, extra_validators=None):
        result = super().validate(extra_validators)
        if self.device_mode.data == 'fixed' and (self.device_id.data is None or self.device_id.data == 0):
            self.device_id.errors.append(err_select_required('デバイス'))
            result = False
        return result

    def validate_min_value(self, field):
        from wtforms import ValidationError as WTFormsValidationError
        if field.data is not None and self.max_value.data is not None:
            if field.data >= self.max_value.data:
                raise WTFormsValidationError(ERR_MIN_VALUE_LESS_THAN_MAX)

    def validate_max_value(self, field):
        from wtforms import ValidationError as WTFormsValidationError
        if field.data is not None and self.min_value.data is not None:
            if field.data <= self.min_value.data:
                raise WTFormsValidationError(ERR_MAX_VALUE_GREATER_THAN_MIN)

    gadget_size = SelectField(
        '部品サイズ',
        choices=[('2x2', '2x2'), ('2x4', '2x4')],
        validators=[DataRequired(message=err_select_required('部品サイズ'))],
    )
