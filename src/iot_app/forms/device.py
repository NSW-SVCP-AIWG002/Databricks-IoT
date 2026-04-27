from flask_wtf import FlaskForm
from wtforms import DateField, HiddenField, IntegerField, SelectField, StringField
from wtforms.validators import DataRequired, Length, Optional, Regexp


class DeviceSearchForm(FlaskForm):
    device_id = StringField('デバイスID', validators=[Optional(), Length(max=128)])
    device_name = StringField('デバイス名', validators=[Optional(), Length(max=100)])
    device_type_id = SelectField(
        'デバイス種別',
        coerce=lambda x: int(x) if x else None,
        choices=[],
        validators=[Optional()],
    )
    location = StringField('設置場所', validators=[Optional(), Length(max=100)])
    organization_id = SelectField(
        '所属組織',
        coerce=lambda x: int(x) if x else None,
        choices=[],
        validators=[Optional()],
    )
    certificate_expiration_date = DateField(
        '証明書期限', validators=[Optional()], format='%Y-%m-%d'
    )
    status = SelectField(
        'ステータス',
        choices=[
            ('', 'すべて'),
            ('connected', '接続済み'),
            ('disconnected', '未接続'),
        ],
        validators=[Optional()],
    )
    sort_by = SelectField('ソート項目', choices=[], validators=[Optional()])
    order = SelectField(
        'ソート順',
        choices=[('', '指定なし'), ('asc', '昇順'), ('desc', '降順')],
        validators=[Optional()],
    )


class DeviceCreateForm(FlaskForm):
    device_uuid = StringField(
        'デバイスID',
        validators=[
            DataRequired(message='デバイスIDは必須です'),
            Length(max=128, message='デバイスIDは128文字以内で入力してください'),
            Regexp(
                r'^[a-zA-Z0-9\-]+$',
                message='デバイスIDは英数字とハイフンのみ使用できます',
            ),
        ],
    )
    device_name = StringField(
        'デバイス名',
        validators=[
            DataRequired(message='デバイス名は必須です'),
            Length(max=100, message='デバイス名は100文字以内で入力してください'),
        ],
    )
    device_type_id = SelectField(
        'デバイス種別',
        coerce=lambda x: int(x) if x else None,
        choices=[],
        validators=[DataRequired(message='デバイス種別は必須です')],
    )
    device_model = StringField(
        'モデル情報',
        validators=[
            DataRequired(message='モデル情報は必須です'),
            Length(max=100, message='モデル情報は100文字以内で入力してください'),
        ],
    )
    sim_id = StringField(
        'SIMID',
        validators=[
            Optional(),
            Length(max=20, message='SIMIDは20文字以内で入力してください'),
        ],
    )
    mac_address = StringField(
        'MACアドレス',
        validators=[
            Optional(),
            Regexp(
                r'^([0-9a-fA-F]{2}:){5}[0-9a-fA-F]{2}$',
                message='MACアドレスはXX:XX:XX:XX:XX:XX形式で入力してください',
            ),
        ],
    )
    device_location = StringField(
        '設置場所',
        validators=[
            Optional(),
            Length(max=100, message='設置場所は100文字以内で入力してください'),
        ],
    )
    organization_id = SelectField(
        '所属組織',
        coerce=lambda x: int(x) if x else None,
        choices=[],
        validators=[DataRequired(message='所属組織は必須です')],
    )
    certificate_expiration_date = DateField(
        '証明書期限', validators=[Optional()], format='%Y-%m-%d'
    )


class DeviceUpdateForm(FlaskForm):
    device_name = StringField(
        'デバイス名',
        validators=[
            DataRequired(message='デバイス名は必須です'),
            Length(max=100, message='デバイス名は100文字以内で入力してください'),
        ],
    )
    device_type_id = SelectField(
        'デバイス種別',
        coerce=lambda x: int(x) if x else None,
        choices=[],
        validators=[DataRequired(message='デバイス種別は必須です')],
    )
    device_model = StringField(
        'モデル情報',
        validators=[
            Optional(),
            Length(max=100, message='モデル情報は100文字以内で入力してください'),
        ],
    )
    sim_id = StringField(
        'SIMID',
        validators=[
            Optional(),
            Length(max=20, message='SIMIDは20文字以内で入力してください'),
        ],
    )
    mac_address = StringField(
        'MACアドレス',
        validators=[
            Optional(),
            Regexp(
                r'^([0-9a-fA-F]{2}:){5}[0-9a-fA-F]{2}$',
                message='MACアドレスはXX:XX:XX:XX:XX:XX形式で入力してください',
            ),
        ],
    )
    device_location = StringField(
        '設置場所',
        validators=[
            Optional(),
            Length(max=100, message='設置場所は100文字以内で入力してください'),
        ],
    )
    organization_id = SelectField(
        '所属組織',
        coerce=lambda x: int(x) if x else None,
        choices=[],
        validators=[DataRequired(message='所属組織は必須です')],
    )
    certificate_expiration_date = DateField(
        '証明書期限', validators=[Optional()], format='%Y-%m-%d'
    )


class DeviceDeleteForm(FlaskForm):
    device_uuids = HiddenField('削除対象デバイスUUID', validators=[DataRequired()])
