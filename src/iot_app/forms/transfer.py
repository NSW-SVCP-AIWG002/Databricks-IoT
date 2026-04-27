from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, FileField, FileSize
from wtforms import SelectField
from wtforms.validators import DataRequired


class CSVImportForm(FlaskForm):
    master_type_id = SelectField(
        'マスタ種別',
        validators=[DataRequired()],
        choices=[],
    )
    csv_file = FileField(
        'CSVファイル',
        validators=[
            DataRequired(),
            FileAllowed(['csv'], 'CSVファイルを選択してください'),
            FileSize(max_size=10 * 1024 * 1024, message='ファイルサイズは10MB以下にしてください'),
        ],
    )
