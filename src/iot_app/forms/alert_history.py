from flask_wtf import FlaskForm
from wtforms import StringField, SelectField
from wtforms.validators import Optional, Length


def _coerce_optional_int(value):
    """空文字列または None を None に変換する（SelectField 用 coerce）"""
    if value is None or value == '' or value == 'None':
        return None
    return int(value)


class AlertHistorySearchForm(FlaskForm):
    """アラート履歴検索フォーム"""
    start_datetime = StringField(validators=[Optional()])
    end_datetime = StringField(validators=[Optional()])
    device_name = StringField(validators=[Optional(), Length(max=100)])
    device_location = StringField(validators=[Optional(), Length(max=100)])
    alert_name = StringField(validators=[Optional(), Length(max=100)])
    alert_level_id = SelectField(
        coerce=_coerce_optional_int,
        validators=[Optional()],
        choices=[],
    )
    alert_status_id = SelectField(
        coerce=_coerce_optional_int,
        validators=[Optional()],
        choices=[],
    )
    sort_by = SelectField(validators=[Optional()], choices=[])
    order = SelectField(choices=[('desc', '降順'), ('asc', '昇順')])
