# テスト項目書 - CSV インポート Form層

対象テストコード: `tests/unit/forms/test_transfer.py`
テスト総数: **9件**

---

## TestCSVImportFormMasterType

| No | テスト観点 | 操作手順 | 予想結果 |
|----|-----------|---------|---------|
| 1 | 1.1.1.1 必須チェック：未入力（空文字） | `app.test_request_context()` 内で `CSVImportForm` を生成する。`_make_form_with_choices(CSVImportForm, '')` で `master_type_id.choices=[('1','デバイスマスタ'),('2','ユーザーマスタ')]`・`master_type_id.data=''` を設定する。`csv_file.data` に有効なCSVファイル（`filename='test.csv'`）の `FileStorage` をセットし、`form.validate()` を呼び出す | バリデーションが失敗し（戻り値 `False`）、`form.errors` に `'master_type_id'` キーが含まれること |
| 2 | 1.1.1.2 必須チェック：None | `app.test_request_context()` 内で `CSVImportForm` を生成する。`_make_form_with_choices(CSVImportForm, None)` で `master_type_id.choices` を設定し `master_type_id.data=None` とする。`csv_file.data` に有効なCSVファイルの `FileStorage` をセットし、`form.validate()` を呼び出す | バリデーションが失敗し、`form.errors` に `'master_type_id'` キーが含まれること |
| 3 | 1.1.1.3 必須チェック：入力あり（許容値） | `app.test_request_context()` 内で `CSVImportForm` を生成する。`_make_form_with_choices(CSVImportForm, '1')` で `master_type_id.choices=[('1','デバイスマスタ'),('2','ユーザーマスタ')]`・`master_type_id.data='1'`（choices内の値）を設定する。`csv_file.data` に有効なCSVファイルの `FileStorage` をセットし、`form.validate()` を呼び出す | バリデーションが通過すること（戻り値 `True`） |
| 4 | 1.1.6.2 不整値チェック：未定義値 | `app.test_request_context()` 内で `CSVImportForm` を生成する。`_make_form_with_choices(CSVImportForm, '999')` で `master_type_id.choices=[('1','デバイスマスタ'),('2','ユーザーマスタ')]`・`master_type_id.data='999'`（choicesに存在しない値）を設定する。`csv_file.data` に有効なCSVファイルの `FileStorage` をセットし、`form.validate()` を呼び出す | バリデーションが失敗し、`form.errors` に `'master_type_id'` キーが含まれること |

---

## TestCSVImportFormCsvFile

| No | テスト観点 | 操作手順 | 予想結果 |
|----|-----------|---------|---------|
| 5 | 1.1.1.2 必須チェック：None | `app.test_request_context()` 内で `CSVImportForm` を生成する。`_make_form_with_choices(CSVImportForm, '1')` で `master_type_id` を設定する。`csv_file.data=None` にセットし、`form.validate()` を呼び出す | バリデーションが失敗し、`form.errors` に `'csv_file'` キーが含まれること |
| 6 | 1.1.1.3 必須チェック：入力あり（有効な .csv ファイル） | `app.test_request_context()` 内で `CSVImportForm` を生成する。`_make_form_with_choices(CSVImportForm, '1')` で `master_type_id` を設定する。`csv_file.data` に `FileStorage(stream=BytesIO(b'col\nval'), filename='devices.csv', content_type='text/csv')` をセットし、`form.validate()` を呼び出す | バリデーションが通過すること（戻り値 `True`） |
| 7 | 1.1.6.2 不整値チェック：未定義値（拡張子 .xlsx） | `app.test_request_context()` 内で `CSVImportForm` を生成する。`_make_form_with_choices(CSVImportForm, '1')` で `master_type_id` を設定する。`csv_file.data` に `FileStorage(stream=BytesIO(b'data'), filename='test.xlsx', content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')` をセットし、`form.validate()` を呼び出す | バリデーションが失敗し、`form.errors` に `'csv_file'` キーが含まれること |
| 8 | 1.1.6.2 不整値チェック：未定義値（ファイルサイズ > 10MB） | `app.test_request_context()` 内で `CSVImportForm` を生成する。`_make_form_with_choices(CSVImportForm, '1')` で `master_type_id` を設定する。`csv_file.data` に `FileStorage(stream=BytesIO(b'x' * (10 * 1024 * 1024 + 1)), filename='test.csv', content_type='text/csv')` をセットし（10MB+1byte）、`form.validate()` を呼び出す | バリデーションが失敗し、`form.errors` に `'csv_file'` キーが含まれること |
| 9 | 1.1.6.2 不整値チェック：未定義値（拡張子 .txt） | `app.test_request_context()` 内で `CSVImportForm` を生成する。`_make_form_with_choices(CSVImportForm, '1')` で `master_type_id` を設定する。`csv_file.data` に `FileStorage(stream=BytesIO(b'data'), filename='test.txt', content_type='text/plain')` をセットし、`form.validate()` を呼び出す | バリデーションが失敗し、`form.errors` に `'csv_file'` キーが含まれること |
