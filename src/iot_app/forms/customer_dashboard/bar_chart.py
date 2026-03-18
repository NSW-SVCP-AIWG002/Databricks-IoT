from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, FloatField
from wtforms.validators import DataRequired, Length, Optional


class BarChartGadgetForm(FlaskForm):
    """棒グラフガジェット登録フォーム"""

    title = StringField(
        'タイトル',
        validators=[
            DataRequired(message='タイトルを入力してください'),
            Length(max=20, message='タイトルは20文字以内で入力してください'),
        ]
    )
    device_mode = SelectField(
        '表示デバイス',
        choices=[('fixed', 'デバイス固定'), ('variable', 'デバイス可変')],
        validators=[DataRequired(message='表示デバイスを選択してください')],
    )
    device_id = SelectField('デバイス', coerce=int, validators=[Optional()])
    group_id = SelectField('グループ', coerce=int, validators=[DataRequired(message='グループを選択してください')])
    summary_method_id = SelectField('集約方法', coerce=int, validators=[DataRequired(message='集約方法を選択してください')])
    measurement_item_id = SelectField('表示項目', coerce=int, validators=[DataRequired(message='表示項目を選択してください')])
    min_value = FloatField('最小値', validators=[Optional()])
    max_value = FloatField('最大値', validators=[Optional()])
    gadget_size = SelectField(
        '部品サイズ',
        choices=[('2x2', '2x2'), ('2x4', '2x4')],
        validators=[DataRequired(message='部品サイズを選択してください')],
    )
