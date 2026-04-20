# テスト項目書 - デバイス管理台帳 Form層

- **対象テストコード**: `tests/unit/forms/test_device_inventory_form.py`
- **対象モジュール**: `iot_app.forms.device_inventory(DeviceInventoryCreateForm, )`
- **作成日**: 2026-04-20

---

## TestDeviceUuidFormatValidator

| No  | テスト観点                                                                           | 操作手順                                                                                                                                        | 予想結果                                                                   | 実施結果 | 確認日 | 確認者 | 備考 |
| --- | ------------------------------------------------------------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------- | -------- | ------ | ------ | ---- |
| 1   | 2.1.1: azure 環境で有効な device_uuid を渡してもバリデーションエラーが発生しない     | `make_mock_create_form()`でMockフォームを生成し、`device_uuid_format_validator()`に生成したMockフォームと、azure 環境で有効なデバイスUUIDを渡す | azure 環境で有効な`device_uuid`を渡しても`ValidationError`が発生しないこと |          |        |        |      |
| 2   | 2.1.1: aws 環境で有効な device_uuid を渡してもバリデーションエラーが発生しない       | 上項目と同様の試験を、aws 環境で有効な`device_uuid`を用いて行う                                                                                 | aws 環境で有効な`device_uuid`を渡しても`ValidationError`が発生しないこと   |          |        |        |      |
| 3   | 1.1.6.2: azure 環境で使用不可文字（@ など）を含む UUID でValidationError が発生する  | 上項目と同様の試験を、azure 環境で無効な`device_uuid`を用いて行う                                                                               | `ValidationError`がスローされること                                        |          |        |        |      |
| 4   | 1.1.6.2: aws 環境で使用不可文字（ドット等）を含む UUID で ValidationError が発生する | 上項目と同様の試験を、azure 環境で無効な`device_uuid`を用いて行う                                                                               | `ValidationError`がスローされること                                        |          |        |        |      |