from flask_wtf import FlaskForm
from wtforms import IntegerField, SelectField, StringField
from wtforms.validators import DataRequired, Length


class GridGadgetForm(FlaskForm):
    """表ガジェット登録フォーム"""

    gadget_name = StringField(
        'タイトル',
        validators=[
            DataRequired(message='タイトルを入力してください'),
            Length(max=20, message='タイトルは20文字以内で入力してください'),
        ]
    )

    group_id = IntegerField(
        'グループ',
        validators=[DataRequired(message='グループを選択してください')]
    )

    gadget_size = SelectField(
        '部品サイズ',
        choices=[('0', '2x2'), ('1', '2x4')],
        validators=[DataRequired(message='部品サイズを選択してください')],
    )
