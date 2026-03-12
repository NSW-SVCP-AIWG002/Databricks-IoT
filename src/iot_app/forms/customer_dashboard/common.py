from flask_wtf import FlaskForm
from wtforms import StringField
from wtforms.validators import DataRequired, Length


class DashboardForm(FlaskForm):
    dashboard_name = StringField(
        'ダッシュボード名',
        validators=[
            DataRequired(message='ダッシュボードタイトルを入力してください'),
            Length(max=50, message='ダッシュボードタイトルは50文字以内で入力してください'),
        ]
    )


class DashboardGroupForm(FlaskForm):
    dashboard_group_name = StringField(
        'ダッシュボードグループ名',
        validators=[
            DataRequired(message='ダッシュボードグループタイトルを入力してください'),
            Length(max=50, message='ダッシュボードグループタイトルは50文字以内で入力してください'),
        ]
    )


class GadgetForm(FlaskForm):
    gadget_name = StringField(
        'ガジェット名',
        validators=[
            DataRequired(message='ガジェットタイトルを入力してください'),
            Length(max=20, message='ガジェットタイトルは20文字以内で入力してください'),
        ]
    )
