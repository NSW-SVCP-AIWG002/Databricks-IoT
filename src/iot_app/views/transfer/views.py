from flask import g, render_template, request
from sqlalchemy.exc import IntegrityError

from iot_app import db
from iot_app.common.logger import get_logger
from iot_app.decorators.auth import require_role
from iot_app.forms.transfer import CSVImportForm
from iot_app.services.csv_service import (
    detect_encoding,
    read_csv,
    validate_csv_format,
)
from iot_app.views.transfer import transfer_bp

logger = get_logger(__name__)

# ユーザー種別ごとのアクセス可能なマスタ種別
# key: user_type_id, value: list of (master_type_id, master_name)
_MASTER_CHOICES_BY_USER_TYPE: dict[int, list[tuple[str, str]]] = {
    1: [('1', 'デバイス'), ('2', 'ユーザー'), ('3', '組織'), ('4', 'アラート設定'), ('5', 'デバイス在庫情報')],  # system_admin
    2: [('1', 'デバイス'), ('2', 'ユーザー'), ('3', '組織'), ('4', 'アラート設定')],   # management_admin
    3: [('1', 'デバイス'), ('2', 'ユーザー'), ('3', '組織'), ('4', 'アラート設定')],   # sales_company_user
}


def _get_master_choices() -> list[tuple[str, str]]:
    """現在のユーザーのロールに応じたマスタ種別選択肢を返す。"""
    user_type_id = getattr(g.current_user, 'user_type_id', None)
    return _MASTER_CHOICES_BY_USER_TYPE.get(user_type_id, [])


@transfer_bp.route('/csv-import', methods=['GET'])
@require_role('system_admin', 'management_admin', 'sales_company_user')
def csv_import_get():
    form = CSVImportForm()
    form.master_type_id.choices = _get_master_choices()
    logger.info('CSVインポート画面表示')
    return render_template('transfer/csv-import.html', form=form)


@transfer_bp.route('/csv-import', methods=['POST'])
@require_role('system_admin', 'management_admin', 'sales_company_user')
def csv_import_post():
    form = CSVImportForm()
    form.master_type_id.choices = _get_master_choices()

    if not form.validate_on_submit():
        logger.info('CSVインポート: フォームバリデーションエラー')
        return render_template('transfer/csv-import.html', form=form), 422

    master_type_id = int(form.master_type_id.data)
    csv_file = form.csv_file.data

    # ① エンコーディング検出・CSV読み込み
    try:
        file_content = csv_file.read()
        csv_file.seek(0)
        encoding = detect_encoding(file_content)
        df = read_csv(file_content, encoding)
        logger.info('CSV読み込み成功', extra={'rows': len(df)})
    except Exception as e:
        logger.error('CSV読み込みエラー', extra={'error': str(e)})
        return render_template(
            'transfer/csv-import-error.html',
            import_errors=[{'row': 0, 'column': '-', 'message': 'CSVファイルの読み込みに失敗しました'}],
        ), 400

    # ② フォーマットバリデーション
    try:
        errors = validate_csv_format(df, master_type_id, g.current_user)
    except Exception as e:
        logger.error('CSVバリデーションエラー', extra={'error': str(e)})
        return render_template(
            'transfer/csv-import-error.html',
            import_errors=[{'row': 0, 'column': '-', 'message': 'CSVデータの検証中にエラーが発生しました'}],
        ), 400

    if errors:
        logger.info('CSVインポート: バリデーションエラー', extra={'errorCount': len(errors)})
        return render_template('transfer/csv-import-error.html', import_errors=errors), 400

    # ③ トランザクション処理
    try:
        db.session.commit()
        logger.info('CSVインポート成功', extra={'masterTypeId': master_type_id, 'rows': len(df)})
        return render_template('transfer/csv-import-success.html', imported_count=len(df))
    except IntegrityError as e:
        db.session.rollback()
        logger.error('CSVインポート失敗（整合性エラー）', extra={'error': str(e)})
        return render_template(
            'transfer/csv-import-error.html',
            import_errors=[{'row': 0, 'column': '-', 'message': 'CSVファイルのインポートが失敗しました'}],
        ), 400
    except Exception as e:
        db.session.rollback()
        logger.error('CSVインポート失敗', extra={'error': str(e)})
        return render_template(
            'transfer/csv-import-error.html',
            import_errors=[{'row': 0, 'column': '-', 'message': 'CSVファイルのインポートが失敗しました'}],
        ), 400
