"""
顧客作成ダッシュボード フォーム定義

参照設計書:
  - docs/03-features/flask-app/customer-dashboard/timeline/ui-specification.md
  - docs/03-features/flask-app/customer-dashboard/timeline/workflow-specification.md
"""

from flask_wtf import FlaskForm
from wtforms import FloatField, IntegerField, RadioField, SelectField, StringField
from wtforms.validators import DataRequired, Length, NumberRange, Optional, ValidationError


class TimelineGadgetForm(FlaskForm):
    """時系列グラフガジェット登録フォーム

    仕様: ui-specification.md > バリデーション（ガジェット登録画面）
    """

    title = StringField(
        'タイトル',
        validators=[
            DataRequired(message='タイトルを入力してください'),
            Length(max=20, message='タイトルは20文字以内で入力してください'),
        ],
        default='時系列',
    )

    device_mode = RadioField(
        '表示デバイス選択',
        choices=[('fixed', 'デバイス固定'), ('variable', 'デバイス可変')],
        default='fixed',
        validators=[DataRequired(message='表示デバイス選択を選択してください')],
    )

    device_id = IntegerField(
        'デバイス選択',
        validators=[Optional()],
    )

    group_id = SelectField(
        'グループ選択',
        coerce=int,
        choices=[],
        validators=[DataRequired(message='グループを選択してください')],
    )

    left_item_id = IntegerField(
        '左表示項目',
        validators=[DataRequired(message='左表示項目を選択してください')],
    )

    right_item_id = IntegerField(
        '右表示項目',
        validators=[DataRequired(message='右表示項目を選択してください')],
    )

    left_min_value = FloatField(
        '左表示項目 最小値',
        validators=[Optional()],
    )

    left_max_value = FloatField(
        '左表示項目 最大値',
        validators=[Optional()],
    )

    right_min_value = FloatField(
        '右表示項目 最小値',
        validators=[Optional()],
    )

    right_max_value = FloatField(
        '右表示項目 最大値',
        validators=[Optional()],
    )

    gadget_size = SelectField(
        '部品サイズ',
        choices=[('2x2', '2x2'), ('2x4', '2x4')],
        validators=[DataRequired(message='部品サイズを選択してください')],
    )

    def validate_device_id(self, field):
        """デバイス固定モード時はデバイスIDが必須"""
        if self.device_mode.data == 'fixed' and not field.data:
            raise ValidationError('デバイスを選択してください')

    def validate_left_min_value(self, field):
        """左最小値 < 左最大値"""
        if field.data is not None and self.left_max_value.data is not None:
            if field.data >= self.left_max_value.data:
                raise ValidationError('左表示項目の最小値は最大値より小さい値を入力してください')

    def validate_left_max_value(self, field):
        """左最大値 > 左最小値"""
        if field.data is not None and self.left_min_value.data is not None:
            if field.data <= self.left_min_value.data:
                raise ValidationError('左表示項目の最大値は最小値より大きい値を入力してください')

    def validate_right_min_value(self, field):
        """右最小値 < 右最大値"""
        if field.data is not None and self.right_max_value.data is not None:
            if field.data >= self.right_max_value.data:
                raise ValidationError('右表示項目の最小値は最大値より小さい値を入力してください')

    def validate_right_max_value(self, field):
        """右最大値 > 右最小値"""
        if field.data is not None and self.right_min_value.data is not None:
            if field.data <= self.right_min_value.data:
                raise ValidationError('右表示項目の最大値は最小値より大きい値を入力してください')
