"""
顧客作成ダッシュボード フォーム定義

参照設計書:
  - docs/03-features/flask-app/customer-dashboard/timeline/ui-specification.md
  - docs/03-features/flask-app/customer-dashboard/timeline/workflow-specification.md
"""

from flask_wtf import FlaskForm
from wtforms import FloatField, IntegerField, RadioField, SelectField, StringField
from wtforms.validators import DataRequired, Length, NumberRange, Optional, ValidationError

from iot_app.common.messages import (
    err_max_greater_than_min,
    err_max_length,
    err_min_less_than_max,
    err_numeric,
    err_required,
    err_select_required,
)


class _JaFloatField(FloatField):
    """日本語エラーメッセージ付き FloatField"""

    def __init__(self, label, message, **kwargs):
        super().__init__(label, **kwargs)
        self._number_message = message

    def process_formdata(self, valuelist):
        if valuelist:
            try:
                self.data = float(valuelist[0])
            except (ValueError, TypeError):
                self.data = None
                raise ValueError(self._number_message)


class TimelineGadgetForm(FlaskForm):
    """時系列グラフガジェット登録フォーム

    仕様: ui-specification.md > バリデーション（ガジェット登録画面）
    """

    title = StringField(
        'タイトル',
        validators=[
            DataRequired(message=err_required('タイトル')),
            Length(max=20, message=err_max_length('タイトル', 20)),
        ],
        default='時系列',
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

    group_id = SelectField(
        'グループ選択',
        coerce=int,
        choices=[],
        validators=[DataRequired(message=err_select_required('グループ'))],
    )

    left_item_id = IntegerField(
        '左表示項目',
        validators=[DataRequired(message=err_select_required('左表示項目'))],
    )

    right_item_id = IntegerField(
        '右表示項目',
        validators=[DataRequired(message=err_select_required('右表示項目'))],
    )

    left_min_value = _JaFloatField(
        '左表示項目 最小値',
        message=err_numeric('左表示項目の最小値'),
        validators=[Optional()],
    )

    left_max_value = _JaFloatField(
        '左表示項目 最大値',
        message=err_numeric('左表示項目の最大値'),
        validators=[Optional()],
    )

    right_min_value = _JaFloatField(
        '右表示項目 最小値',
        message=err_numeric('右表示項目の最小値'),
        validators=[Optional()],
    )

    right_max_value = _JaFloatField(
        '右表示項目 最大値',
        message=err_numeric('右表示項目の最大値'),
        validators=[Optional()],
    )

    gadget_size = SelectField(
        '部品サイズ',
        choices=[('2x2', '2x2'), ('2x4', '2x4')],
        validators=[DataRequired(message=err_select_required('部品サイズ'))],
    )

    def validate(self, extra_validators=None):
        result = super().validate(extra_validators)
        if self.device_mode.data == 'fixed' and not self.device_id.data:
            self.device_id.errors.append(err_select_required('デバイス'))
            result = False
        return result

    def validate_left_min_value(self, field):
        """左最小値 < 左最大値"""
        if field.data is not None and self.left_max_value.data is not None:
            if field.data >= self.left_max_value.data:
                raise ValidationError(err_min_less_than_max('左表示項目'))

    def validate_left_max_value(self, field):
        """左最大値 > 左最小値"""
        if field.data is not None and self.left_min_value.data is not None:
            if field.data <= self.left_min_value.data:
                raise ValidationError(err_max_greater_than_min('左表示項目'))

    def validate_right_min_value(self, field):
        """右最小値 < 右最大値"""
        if field.data is not None and self.right_max_value.data is not None:
            if field.data >= self.right_max_value.data:
                raise ValidationError(err_min_less_than_max('右表示項目'))

    def validate_right_max_value(self, field):
        """右最大値 > 右最小値"""
        if field.data is not None and self.right_min_value.data is not None:
            if field.data <= self.right_min_value.data:
                raise ValidationError(err_max_greater_than_min('右表示項目'))
