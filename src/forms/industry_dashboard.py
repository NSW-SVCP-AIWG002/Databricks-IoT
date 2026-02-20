"""
業種別ダッシュボード機能（冷蔵冷凍庫） フォーム定義

参照:
- workflow-specification.md「バリデーション」
- ui-specification.md「(10)表示期間変更」
"""

from flask_wtf import FlaskForm
from wtforms import StringField
from wtforms.validators import DataRequired, Length, Optional


class StoreMonitoringSearchForm(FlaskForm):
    """店舗モニタリング検索フォーム

    ui-specification.md「(2)検索フォーム」に対応する。
    """

    organization_name = StringField(
        "店舗名",
        validators=[Optional(), Length(max=200)],
        render_kw={"placeholder": "店舗を検索..."},
    )

    device_name = StringField(
        "デバイス名",
        validators=[Optional(), Length(max=100)],
    )


class DeviceDetailSearchForm(FlaskForm):
    """デバイス詳細検索フォーム（表示期間変更）

    ui-specification.md「(10)表示期間変更」に対応する。
    バリデーションルール:
    - search_start_datetime: 必須、日時形式（YYYY-MM-DDTHH:MM）
    - search_end_datetime: 必須、日時形式（YYYY-MM-DDTHH:MM）
    - 開始日時 < 終了日時であること（サービス層でチェック）
    - 表示期間が最大2ヶ月（62日）以内であること（サービス層でチェック）
    """

    search_start_datetime = StringField(
        "表示期間開始",
        validators=[DataRequired(message="開始日時を入力してください")],
    )

    search_end_datetime = StringField(
        "表示期間終了",
        validators=[DataRequired(message="終了日時を入力してください")],
    )
