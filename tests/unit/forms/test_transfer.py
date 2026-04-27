"""
CSV インポート - Form層 単体テスト

対象ファイル: src/iot_app/forms/transfer.py

参照ドキュメント:
  - 機能設計書:       docs/03-features/flask-app/csv-import-export/workflow-specification.md
  - UI設計書:         docs/03-features/flask-app/csv-import-export/ui-specification.md
  - 単体テスト観点表: docs/05-testing/unit-test/unit-test-perspectives.md
"""
import pytest
from io import BytesIO
from werkzeug.datastructures import FileStorage


# ============================================================
# ヘルパー関数
# ============================================================

def _make_valid_csv_file(filename='test.csv', content=b'col\nval'):
    """有効な CSV FileStorage を生成するヘルパー"""
    return FileStorage(stream=BytesIO(content), filename=filename, content_type='text/csv')


def _make_form_with_choices(form_class, master_type_id_value):
    """master_type_id に choices をセットした CSVImportForm を生成するヘルパー

    SelectField は choices が空だと全値を受け付けてしまうため、
    テスト時は実運用相当の choices を明示的に設定する。
    """
    form = form_class()
    form.master_type_id.choices = [('1', 'デバイスマスタ'), ('2', 'ユーザーマスタ')]
    form.master_type_id.data = master_type_id_value
    return form


# ============================================================
# 1. master_type_id フィールド
# 観点: 1.1.1（必須チェック）, 1.1.6（不整値チェック）
# ============================================================

@pytest.mark.unit
class TestCSVImportFormMasterType:
    """master_type_id フィールド バリデーション

    UI仕様書 § (2) マスタ種別選択エリア
    master_type_id: 必須・DBに存在するマスタ種別のみ許容
    """

    def test_invalid_when_master_type_id_empty(self, app):
        """1.1.1.1 空文字: DataRequired によりバリデーションエラー"""
        from iot_app.forms.transfer import CSVImportForm
        with app.test_request_context():
            form = _make_form_with_choices(CSVImportForm, '')
            form.csv_file.data = _make_valid_csv_file()
            assert not form.validate()
            assert 'master_type_id' in form.errors

    def test_invalid_when_master_type_id_none(self, app):
        """1.1.1.2 None: DataRequired によりバリデーションエラー"""
        from iot_app.forms.transfer import CSVImportForm
        with app.test_request_context():
            form = _make_form_with_choices(CSVImportForm, None)
            form.csv_file.data = _make_valid_csv_file()
            assert not form.validate()
            assert 'master_type_id' in form.errors

    def test_valid_when_master_type_id_valid(self, app):
        """1.1.1.3 入力あり（choices 内の値）: バリデーション通過"""
        from iot_app.forms.transfer import CSVImportForm
        with app.test_request_context():
            form = _make_form_with_choices(CSVImportForm, '1')
            form.csv_file.data = _make_valid_csv_file()
            assert form.validate()

    def test_invalid_when_master_type_id_undefined(self, app):
        """1.1.6.2 未定義値（choices 外の値 '999'）: バリデーションエラー"""
        from iot_app.forms.transfer import CSVImportForm
        with app.test_request_context():
            form = _make_form_with_choices(CSVImportForm, '999')
            form.csv_file.data = _make_valid_csv_file()
            assert not form.validate()
            assert 'master_type_id' in form.errors


# ============================================================
# 2. csv_file フィールド
# 観点: 1.1.1（必須チェック）, 1.1.6（不整値チェック）
# ============================================================

@pytest.mark.unit
class TestCSVImportFormCsvFile:
    """csv_file フィールド バリデーション

    UI仕様書 § (3) ファイルアップロードエリア
    csv_file: 必須・拡張子 .csv のみ許容・最大サイズ 10MB
    """

    def test_invalid_when_csv_file_none(self, app):
        """1.1.1.2 None: DataRequired によりバリデーションエラー"""
        from iot_app.forms.transfer import CSVImportForm
        with app.test_request_context():
            form = _make_form_with_choices(CSVImportForm, '1')
            form.csv_file.data = None
            assert not form.validate()
            assert 'csv_file' in form.errors

    def test_valid_when_csv_file_valid(self, app):
        """1.1.1.3 入力あり（有効な .csv ファイル）: バリデーション通過"""
        from iot_app.forms.transfer import CSVImportForm
        with app.test_request_context():
            form = _make_form_with_choices(CSVImportForm, '1')
            form.csv_file.data = _make_valid_csv_file('devices.csv')
            assert form.validate()

    def test_invalid_when_csv_file_wrong_extension_xlsx(self, app):
        """1.1.6.2 拡張子 .xlsx: FileAllowed によりバリデーションエラー"""
        from iot_app.forms.transfer import CSVImportForm
        with app.test_request_context():
            form = _make_form_with_choices(CSVImportForm, '1')
            form.csv_file.data = FileStorage(
                stream=BytesIO(b'data'),
                filename='test.xlsx',
                content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            )
            assert not form.validate()
            assert 'csv_file' in form.errors

    def test_invalid_when_csv_file_exceeds_10mb(self, app):
        """1.1.6.2 ファイルサイズ > 10MB: バリデーションエラー"""
        from iot_app.forms.transfer import CSVImportForm
        with app.test_request_context():
            form = _make_form_with_choices(CSVImportForm, '1')
            large_data = b'x' * (10 * 1024 * 1024 + 1)  # 10MB + 1byte
            form.csv_file.data = FileStorage(
                stream=BytesIO(large_data),
                filename='test.csv',
                content_type='text/csv',
            )
            assert not form.validate()
            assert 'csv_file' in form.errors

    def test_invalid_when_csv_file_wrong_extension_txt(self, app):
        """1.1.6.2 拡張子 .txt: FileAllowed によりバリデーションエラー"""
        from iot_app.forms.transfer import CSVImportForm
        with app.test_request_context():
            form = _make_form_with_choices(CSVImportForm, '1')
            form.csv_file.data = FileStorage(
                stream=BytesIO(b'data'),
                filename='test.txt',
                content_type='text/plain',
            )
            assert not form.validate()
            assert 'csv_file' in form.errors
