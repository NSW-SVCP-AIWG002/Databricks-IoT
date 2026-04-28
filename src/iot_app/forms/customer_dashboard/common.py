from flask_wtf import FlaskForm
from wtforms import HiddenField, StringField
from wtforms.validators import DataRequired, Length

from iot_app.common.messages import err_max_length, err_required


class DashboardForm(FlaskForm):
    dashboard_name = StringField(
        'ダッシュボード名',
        validators=[
            DataRequired(message=err_required('ダッシュボードタイトル')),
            Length(max=50, message=err_max_length('ダッシュボードタイトル', 50)),
        ]
    )


class DashboardGroupForm(FlaskForm):
    dashboard_uuid = HiddenField('dashboard_uuid')
    dashboard_group_name = StringField(
        'ダッシュボードグループ名',
        validators=[
            DataRequired(message=err_required('ダッシュボードグループタイトル')),
            Length(max=50, message=err_max_length('ダッシュボードグループタイトル', 50)),
        ]
    )


class GadgetForm(FlaskForm):
    gadget_name = StringField(
        'ガジェット名',
        validators=[
            DataRequired(message=err_required('ガジェットタイトル')),
            Length(max=20, message=err_max_length('ガジェットタイトル', 20)),
        ]
    )
