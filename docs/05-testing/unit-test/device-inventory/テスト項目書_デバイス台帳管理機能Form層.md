# テスト項目書 - device-inventory

- **対象ファイル**: `src/iot_app/forms/device_inventory.py`
- **テストコード**: `/workspaces/Databricks-IoT/tests/unit/forms/test_device_inventory_form.py`
- **観点表**: `docs/05-testing/unit-test/unit-test-perspectives.md`
- **ワークフロー仕様書**: `/workspaces/Databricks-IoT/docs/03-features/flask-app/device-inventory/workflow-specification.md`

---

## 対応表

テストクラスと、ワークフロー仕様書の各ワークフロー・処理フロー項目の対応を示します。

| テストクラス | テスト項目No. | 対応ワークフロー | 処理フロー項目 | エンドポイント |
|---|:---:|---|---|---|
| TestDeviceInventorySearchFormFieldDefinitions | 1〜6 | 初期表示・検索・絞り込み・ソート・ページング | 検索フォームフィールド定義 | `GET /admin/device-inventory`, `POST /admin/device-inventory` |
| TestDeviceInventorySearchFormValidation | 7〜12 | 検索・絞り込み | 購入日範囲の相関バリデーション | `POST /admin/device-inventory` |
| TestDeviceUuidFormatValidator | 13〜19 | デバイス台帳登録・デバイス台帳更新 | device_uuid フォーマット検証 | `POST /admin/device-inventory/create`, `POST /admin/device-inventory/<uuid>/update` |
| TestDateAfterPurchaseValidator | 20〜26 | デバイス台帳登録・デバイス台帳更新 | 購入日以降チェックバリデーター | `POST /admin/device-inventory/create`, `POST /admin/device-inventory/<uuid>/update` |
| TestDeviceInventoryCreateFormRequiredFields | 27〜36 | デバイス台帳登録 | 登録フォーム必須フィールドバリデーション | `POST /admin/device-inventory/create` |
| TestDeviceInventoryCreateFormMaxLength | 37〜43 | デバイス台帳登録 | 登録フォーム最大文字数バリデーション | `POST /admin/device-inventory/create` |
| TestDeviceInventoryCreateFormMacAddress | 44〜47 | デバイス台帳登録 | 登録フォームMACアドレス形式バリデーション | `POST /admin/device-inventory/create` |
| TestDeviceInventoryCreateFormDateRelations | 48〜50 | デバイス台帳登録 | 登録フォーム日付相関バリデーター適用確認 | `POST /admin/device-inventory/create` |
| TestDeviceInventoryUpdateFormValidation | 51〜66 | デバイス台帳更新 | 更新フォームバリデーション | `POST /admin/device-inventory/<uuid>/update` |

---

## ワークフロー別カバレッジ

ワークフロー仕様書の各ワークフローに対して、どのテストクラスが対応しているかを示します。

### 初期表示

| 処理フロー項目 | 対応テストクラス | テスト項目No. |
|---|---|:---:|
| 検索フォームフィールド定義 | TestDeviceInventorySearchFormFieldDefinitions | 1〜6 |

### 検索・絞り込み

| 処理フロー項目 | 対応テストクラス | テスト項目No. |
|---|---|:---:|
| 検索フォームフィールド定義 | TestDeviceInventorySearchFormFieldDefinitions | 1〜6 |
| 購入日範囲の相関バリデーション | TestDeviceInventorySearchFormValidation | 7〜12 |

### ソート

| 処理フロー項目 | 対応テストクラス | テスト項目No. |
|---|---|:---:|
| 検索フォームフィールド定義（sort_order選択肢） | TestDeviceInventorySearchFormFieldDefinitions | 6 |

### ページング

| 処理フロー項目 | 対応テストクラス | テスト項目No. |
|---|---|:---:|
| 検索フォームフィールド定義 | TestDeviceInventorySearchFormFieldDefinitions | 1〜6 |

### デバイス台帳登録

| 処理フロー項目 | 対応テストクラス | テスト項目No. |
|---|---|:---:|
| device_uuid フォーマット検証 | TestDeviceUuidFormatValidator | 13〜19 |
| 購入日以降チェックバリデーター | TestDateAfterPurchaseValidator | 20〜26 |
| 登録フォーム必須フィールドバリデーション | TestDeviceInventoryCreateFormRequiredFields | 27〜36 |
| 登録フォーム最大文字数バリデーション | TestDeviceInventoryCreateFormMaxLength | 37〜43 |
| 登録フォームMACアドレス形式バリデーション | TestDeviceInventoryCreateFormMacAddress | 44〜47 |
| 登録フォーム日付相関バリデーター適用確認 | TestDeviceInventoryCreateFormDateRelations | 48〜50 |

### デバイス台帳更新

| 処理フロー項目 | 対応テストクラス | テスト項目No. |
|---|---|:---:|
| device_uuid フォーマット検証 | TestDeviceUuidFormatValidator | 13〜19 |
| 購入日以降チェックバリデーター | TestDateAfterPurchaseValidator | 20〜26 |
| 更新フォームバリデーション | TestDeviceInventoryUpdateFormValidation | 51〜66 |

---

## テストクラス一覧

テストクラスに対して、テスト観点、操作手順、予想結果を示します。

---

### TestDeviceInventorySearchFormFieldDefinitions

| No | テスト観点 | 操作手順 | 予想結果 |
|---|---|---|---|
| 1 | 2.1.2 正常系処理：最小構成の入力で正常終了 / 1.2.2 最大文字列長チェック：上限値で正常終了 / 1.2.3 最大文字列長チェック：上限値超過でエラー | `DeviceInventorySearchForm.device_uuid` フィールドの `validators` を取得し、`Optional` と `Length` バリデーターを確認する | `Optional` バリデーターが含まれること、`Length` バリデーターが含まれ `max=128` であること、バリデーターが2つのみであること |
| 2 | 2.1.2 正常系処理：最小構成の入力で正常終了 / 1.2.2 最大文字列長チェック：上限値で正常終了 / 1.2.3 最大文字列長チェック：上限値超過でエラー | `DeviceInventorySearchForm.device_name` フィールドの `validators` を取得し、`Optional` と `Length` バリデーターを確認する | `Optional` バリデーターが含まれること、`Length` バリデーターが含まれ `max=100` であること、バリデーターが2つのみであること |
| 3 | 2.1.2 正常系処理：最小構成の入力で正常終了 / 1.2.2 最大文字列長チェック：上限値で正常終了 / 1.2.3 最大文字列長チェック：上限値超過でエラー | `DeviceInventorySearchForm.inventory_location` フィールドの `validators` を取得し、`Optional` と `Length` バリデーターを確認する | `Optional` バリデーターが含まれること、`Length` バリデーターが含まれ `max=100` であること、バリデーターが2つのみであること |
| 4 | 2.1.2 正常系処理：最小構成の入力で正常終了 | `DeviceInventorySearchForm.purchase_date_from` フィールドの `validators` を取得し、`Optional` バリデーターを確認する | `Optional` バリデーターが含まれること、バリデーターが1つのみであること |
| 5 | 2.1.2 正常系処理：最小構成の入力で正常終了 | `DeviceInventorySearchForm.purchase_date_to` フィールドの `validators` を取得し、`Optional` バリデーターを確認する | `Optional` バリデーターが含まれること、バリデーターが1つのみであること |
| 6 | 1.6.1 不整値チェック：許容値で正常終了 / 1.6.2 不整値チェック：非許容値でエラー | `DeviceInventorySearchForm.sort_order` フィールドの `choices` を取得し、各選択肢の値を確認する | `choices` の値に `-1`（未選択）、`1`（昇順）、`2`（降順）がすべて含まれること |

---

### TestDeviceInventorySearchFormValidation

| No | テスト観点 | 操作手順 | 予想結果 |
|---|---|---|---|
| 7 | 2.1.1 正常系処理：有効な入力データで正常終了 / 1.4.1 日付形式チェック：有効な日付で正常終了 | `purchase_date_from=date(2025,1,1)`、`purchase_date_to=date(2025,12,31)` でフォームインスタンスを生成し、`to_field.data=date(2025,12,31)` で `DeviceInventorySearchForm.validate_purchase_date_to(form, to_field)` を呼び出す | `ValidationError` が発生しないこと |
| 8 | 2.1.1 正常系処理：有効な入力データで正常終了 / 1.4.1 日付形式チェック：有効な日付で正常終了 | `purchase_date_from=date(2025,6,15)`、`purchase_date_to=date(2025,6,15)` の同日でフォームインスタンスを生成し、`to_field.data=date(2025,6,15)` で `validate_purchase_date_to(form, to_field)` を呼び出す | `ValidationError` が発生しないこと（同日は許可） |
| 9 | 1.6.2 不整値チェック：非許容値でエラー | `purchase_date_from=date(2025,12,31)`、`purchase_date_to=date(2025,1,1)` でフォームインスタンスを生成し、`to_field.data=date(2025,1,1)` で `validate_purchase_date_to(form, to_field)` を呼び出す | `ValidationError` がスローされること |
| 10 | 1.6.2 不整値チェック：非許容値でエラー | `purchase_date_from=date(2025,12,31)`、`purchase_date_to=date(2025,1,1)` でフォームインスタンスを生成し、`to_field.data=date(2025,1,1)` で `validate_purchase_date_to(form, to_field)` を呼び出す | `ValidationError` がスローされ、メッセージに `'開始日は終了日以前を指定してください'` が含まれること |
| 11 | 2.1.2 正常系処理：最小構成の入力で正常終了 / 1.6.4 不整値チェック：空値で正常終了 | `purchase_date_from=None`、`purchase_date_to=date(2025,6,30)` でフォームインスタンスを生成し、`to_field.data=date(2025,6,30)` で `validate_purchase_date_to(form, to_field)` を呼び出す | `ValidationError` が発生しないこと |
| 12 | 2.1.2 正常系処理：最小構成の入力で正常終了 / 1.6.4 不整値チェック：空値で正常終了 | `purchase_date_from=date(2025,1,1)`、`purchase_date_to=None` でフォームインスタンスを生成し、`to_field.data=None` で `validate_purchase_date_to(form, to_field)` を呼び出す | `ValidationError` が発生しないこと |

---

### TestDeviceUuidFormatValidator

| No | テスト観点 | 操作手順 | 予想結果 |
|---|---|---|---|
| 13 | 2.1.1 正常系処理：有効な入力データで正常終了 / 1.6.1 不整値チェック：許容値で正常終了 | `AUTH_TYPE=azure` を環境変数に設定し、`field.data='MyDevice-001.%#_*?,:valid'`（azure許容文字のみ）で `device_uuid_format_validator(form, field)` を呼び出す | `ValidationError` が発生しないこと |
| 14 | 2.1.1 正常系処理：有効な入力データで正常終了 / 1.6.1 不整値チェック：許容値で正常終了 | `AUTH_TYPE=aws` を環境変数に設定し、`field.data='MyDevice_001-abc'`（aws許容文字のみ）で `device_uuid_format_validator(form, field)` を呼び出す | `ValidationError` が発生しないこと |
| 15 | 1.6.2 不整値チェック：非許容値でエラー | `AUTH_TYPE=azure` を環境変数に設定し、`field.data='invalid@device'`（`@` は azure 非許容文字）で `device_uuid_format_validator(form, field)` を呼び出す | `ValidationError` がスローされること |
| 16 | 1.6.2 不整値チェック：非許容値でエラー | `AUTH_TYPE=aws` を環境変数に設定し、`field.data='device.uuid.with.dots'`（ドットは aws 非許容文字）で `device_uuid_format_validator(form, field)` を呼び出す | `ValidationError` がスローされること |
| 17 | 2.1.2 正常系処理：最小構成の入力で正常終了 / 1.6.4 不整値チェック：空値で正常終了 | `AUTH_TYPE=azure` を環境変数に設定し、`field.data=None` で `device_uuid_format_validator(form, field)` を呼び出す | `ValidationError` が発生しないこと（None はスキップ） |
| 18 | 1.6.2 不整値チェック：非許容値でエラー | `AUTH_TYPE=azure` を環境変数に設定し、`field.data='invalid uuid with space'`（スペースを含む）で `device_uuid_format_validator(form, field)` を呼び出す | `ValidationError` がスローされ、メッセージに `'device_uuidの形式が不正です'` が含まれること |
| 19 | 2.1.1 正常系処理：有効な入力データで正常終了 / 1.6.1 不整値チェック：許容値で正常終了 | `AUTH_TYPE=local` を環境変数に設定し、`field.data='device.with.dots'`（ドットを含む。azure許容・aws不可）で `device_uuid_format_validator(form, field)` を呼び出す | `ValidationError` が発生しないこと（local は azure と同じルールが適用される） |

---

### TestDateAfterPurchaseValidator

| No | テスト観点 | 操作手順 | 予想結果 |
|---|---|---|---|
| 20 | 2.1.1 正常系処理：有効な入力データで正常終了 / 1.4.1 日付形式チェック：有効な日付で正常終了 | `date_after_purchase_validator('出荷予定日')` でバリデーターを生成し、`form.purchase_date.data=date(2025,1,15)`、`field.data=date(2025,1,15)`（同日）で呼び出す | `ValidationError` が発生しないこと |
| 21 | 2.1.1 正常系処理：有効な入力データで正常終了 / 1.4.1 日付形式チェック：有効な日付で正常終了 | `date_after_purchase_validator('出荷予定日')` でバリデーターを生成し、`form.purchase_date.data=date(2025,1,15)`、`field.data=date(2025,1,16)`（購入日の翌日）で呼び出す | `ValidationError` が発生しないこと |
| 22 | 1.6.2 不整値チェック：非許容値でエラー | `date_after_purchase_validator('出荷予定日')` でバリデーターを生成し、`form.purchase_date.data=date(2025,1,15)`、`field.data=date(2025,1,14)`（購入日の前日）で呼び出す | `ValidationError` がスローされること |
| 23 | 1.6.2 不整値チェック：非許容値でエラー | `date_after_purchase_validator('メーカー保証終了日')` でバリデーターを生成し、`form.purchase_date.data=date(2025,1,15)`、`field.data=date(2025,1,10)`（購入日より前）で呼び出す | `ValidationError` がスローされ、メッセージに `'メーカー保証終了日'` と `'購入日以降'` が含まれること |
| 24 | 2.1.2 正常系処理：最小構成の入力で正常終了 / 1.6.4 不整値チェック：空値で正常終了 | `date_after_purchase_validator('出荷日')` でバリデーターを生成し、`form.purchase_date.data=date(2025,1,15)`、`field.data=None` で呼び出す | `ValidationError` が発生しないこと（field.data が None の場合はスキップ） |
| 25 | 2.1.2 正常系処理：最小構成の入力で正常終了 / 1.6.4 不整値チェック：空値で正常終了 | `date_after_purchase_validator('出荷日')` でバリデーターを生成し、`form.purchase_date.data=None`、`field.data=date(2025,1,10)` で呼び出す | `ValidationError` が発生しないこと（purchase_date が None の場合は相関チェック不要） |
| 26 | 2.1.1 正常系処理：有効な入力データで正常終了 | `date_after_purchase_validator('出荷予定日')` と `date_after_purchase_validator('出荷日')` をそれぞれ呼び出す | 戻り値がいずれも `callable` であること、かつ2つのオブジェクトが異なること（`v1 is not v2`） |

---

### TestDeviceInventoryCreateFormRequiredFields

| No | テスト観点 | 操作手順 | 予想結果 |
|---|---|---|---|
| 27 | 1.1.1 必須チェック：未入力でエラー / 1.1.2 最大文字列長チェック：上限値で正常終了 / 1.1.3 必須チェック：入力済みで正常終了 | `DeviceInventoryCreateForm.device_uuid` フィールドの `validators` を取得する | `DataRequired` バリデーターが含まれていること |
| 28 | 1.1.1 必須チェック：未入力でエラー / 1.1.2 最大文字列長チェック：上限値で正常終了 / 1.1.3 必須チェック：入力済みで正常終了 | `DeviceInventoryCreateForm.device_name` フィールドの `validators` を取得する | `DataRequired` バリデーターが含まれていること |
| 29 | 1.1.1 必須チェック：未入力でエラー / 1.1.2 最大文字列長チェック：上限値で正常終了 / 1.1.3 必須チェック：入力済みで正常終了 | `DeviceInventoryCreateForm.device_type_id` フィールドの `validators` を取得する | `DataRequired` バリデーターが含まれていること |
| 30 | 1.1.1 必須チェック：未入力でエラー / 1.1.2 最大文字列長チェック：上限値で正常終了 / 1.1.3 必須チェック：入力済みで正常終了 | `DeviceInventoryCreateForm.device_model` フィールドの `validators` を取得する | `DataRequired` バリデーターが含まれていること |
| 31 | 1.1.1 必須チェック：未入力でエラー / 1.1.2 最大文字列長チェック：上限値で正常終了 / 1.1.3 必須チェック：入力済みで正常終了 | `DeviceInventoryCreateForm.mac_address` フィールドの `validators` を取得する | `DataRequired` バリデーターが含まれていること |
| 32 | 1.1.1 必須チェック：未入力でエラー / 1.1.2 最大文字列長チェック：上限値で正常終了 / 1.1.3 必須チェック：入力済みで正常終了 | `DeviceInventoryCreateForm.organizaiton_id` フィールドの `validators` を取得する | `DataRequired` バリデーターが含まれていること |
| 33 | 1.1.1 必須チェック：未入力でエラー / 1.1.2 最大文字列長チェック：上限値で正常終了 / 1.1.3 必須チェック：入力済みで正常終了 | `DeviceInventoryCreateForm.inventory_status_id` フィールドの `validators` を取得する | `DataRequired` バリデーターが含まれていること |
| 34 | 1.1.1 必須チェック：未入力でエラー / 1.1.2 最大文字列長チェック：上限値で正常終了 / 1.1.3 必須チェック：入力済みで正常終了 | `DeviceInventoryCreateForm.inventory_location` フィールドの `validators` を取得する | `DataRequired` バリデーターが含まれていること |
| 35 | 1.1.1 必須チェック：未入力でエラー / 1.1.2 最大文字列長チェック：上限値で正常終了 / 1.1.3 必須チェック：入力済みで正常終了 | `DeviceInventoryCreateForm.purchase_date` フィールドの `validators` を取得する | `DataRequired` バリデーターが含まれていること |
| 36 | 1.1.1 必須チェック：未入力でエラー / 1.1.2 最大文字列長チェック：上限値で正常終了 / 1.1.3 必須チェック：入力済みで正常終了 | `DeviceInventoryCreateForm.manufacturer_warranty_end_date` フィールドの `validators` を取得する | `DataRequired` バリデーターが含まれていること |

---

### TestDeviceInventoryCreateFormMaxLength

| No | テスト観点 | 操作手順 | 予想結果 |
|---|---|---|---|
| 37 | 1.2.2 最大文字列長チェック：上限値で正常終了 / 1.2.3 最大文字列長チェック：上限値超過でエラー | `DeviceInventoryCreateForm.device_uuid` フィールドの `validators` から `Length` バリデーターを取得する | `Length` バリデーターが存在し、`max=128` であること |
| 38 | 1.2.2 最大文字列長チェック：上限値で正常終了 / 1.2.3 最大文字列長チェック：上限値超過でエラー | `DeviceInventoryCreateForm.device_name` フィールドの `validators` から `Length` バリデーターを取得する | `Length` バリデーターが存在し、`max=100` であること |
| 39 | 1.2.2 最大文字列長チェック：上限値で正常終了 / 1.2.3 最大文字列長チェック：上限値超過でエラー | `DeviceInventoryCreateForm.device_model` フィールドの `validators` から `Length` バリデーターを取得する | `Length` バリデーターが存在し、`max=100` であること |
| 40 | 1.2.2 最大文字列長チェック：上限値で正常終了 / 1.2.3 最大文字列長チェック：上限値超過でエラー | `DeviceInventoryCreateForm.sim_id` フィールドの `validators` から `Length` バリデーターを取得する | `Length` バリデーターが存在し、`max=20` であること |
| 41 | 1.2.2 最大文字列長チェック：上限値で正常終了 / 1.2.3 最大文字列長チェック：上限値超過でエラー | `DeviceInventoryCreateForm.software_version` フィールドの `validators` から `Length` バリデーターを取得する | `Length` バリデーターが存在し、`max=100` であること |
| 42 | 1.2.2 最大文字列長チェック：上限値で正常終了 / 1.2.3 最大文字列長チェック：上限値超過でエラー | `DeviceInventoryCreateForm.device_location` フィールドの `validators` から `Length` バリデーターを取得する | `Length` バリデーターが存在し、`max=100` であること |
| 43 | 1.2.2 最大文字列長チェック：上限値で正常終了 / 1.2.3 最大文字列長チェック：上限値超過でエラー | `DeviceInventoryCreateForm.inventory_location` フィールドの `validators` から `Length` バリデーターを取得する | `Length` バリデーターが存在し、`max=100` であること |

---

### TestDeviceInventoryCreateFormMacAddress

| No | テスト観点 | 操作手順 | 予想結果 |
|---|---|---|---|
| 44 | 1.6.1 不整値チェック：許容値で正常終了 / 1.6.2 不整値チェック：非許容値でエラー | `DeviceInventoryCreateForm.mac_address` フィールドの `validators` を取得する | `Regexp` バリデーターが含まれていること |
| 45 | 2.1.1 正常系処理：有効な入力データで正常終了 / 1.6.1 不整値チェック：許容値で正常終了 | `DeviceInventoryCreateForm.mac_address` フィールドの `Regexp` バリデーターを取得し、`re.match(regexp_v.regex, 'AA:BB:CC:DD:EE:FF')` を実行する | 正規表現パターンに一致すること（`True`） |
| 46 | 1.6.2 不整値チェック：非許容値でエラー | `DeviceInventoryCreateForm.mac_address` フィールドの `Regexp` バリデーターを取得し、`re.match(regexp_v.regex, 'AABBCCDDEEFF')`（コロンなし）を実行する | 正規表現パターンに不一致であること（`None`） |
| 47 | 1.6.2 不整値チェック：非許容値でエラー | `DeviceInventoryCreateForm.mac_address` フィールドの `Regexp` バリデーターを取得し、`re.match(regexp_v.regex, 'AA-BB-CC-DD-EE-FF')`（ハイフン区切り）を実行する | 正規表現パターンに不一致であること（`None`） |

---

### TestDeviceInventoryCreateFormDateRelations

| No | テスト観点 | 操作手順 | 予想結果 |
|---|---|---|---|
| 48 | 1.4.1 日付形式チェック：有効な日付で正常終了 / 1.6.1 不整値チェック：許容値で正常終了 / 1.6.2 不整値チェック：非許容値でエラー | `DeviceInventoryCreateForm.estimated_ship_date` フィールドの `validators` を取得する | `Optional` バリデーターが含まれること、`__qualname__` に `'date_after_purchase_validator'` を含む callable が含まれること、バリデーターが2つのみであること |
| 49 | 1.4.1 日付形式チェック：有効な日付で正常終了 / 1.6.1 不整値チェック：許容値で正常終了 / 1.6.2 不整値チェック：非許容値でエラー | `DeviceInventoryCreateForm.ship_date` フィールドの `validators` を取得する | `Optional` バリデーターが含まれること、`__qualname__` に `'date_after_purchase_validator'` を含む callable が含まれること、バリデーターが2つのみであること |
| 50 | 1.1.3 必須チェック：入力済みで正常終了 / 1.4.1 日付形式チェック：有効な日付で正常終了 / 1.6.1 不整値チェック：許容値で正常終了 / 1.6.2 不整値チェック：非許容値でエラー | `DeviceInventoryCreateForm.manufacturer_warranty_end_date` フィールドの `validators` を取得する | `DataRequired` バリデーターが含まれること、`__qualname__` に `'date_after_purchase_validator'` を含む callable が含まれること、バリデーターが2つのみであること |

---

### TestDeviceInventoryUpdateFormValidation

| No | テスト観点 | 操作手順 | 予想結果 |
|---|---|---|---|
| 51 | 1.1.1 必須チェック：未入力でエラー / 1.1.2 最大文字列長チェック：上限値で正常終了 / 1.1.3 必須チェック：入力済みで正常終了 / 1.2.2 最大文字列長チェック：上限値で正常終了 / 1.2.3 最大文字列長チェック：上限値超過でエラー / 1.6.1 不整値チェック：許容値で正常終了 / 1.6.2 不整値チェック：非許容値でエラー | `DeviceInventoryUpdateForm.device_uuid` フィールドの `validators` を取得し、`DataRequired`・`Length`・`device_uuid_format_validator` の有無を確認する | `DataRequired` バリデーターが含まれること、`Length` バリデーターが存在し `max=128` であること、`__qualname__` に `'device_uuid_format_validator'` を含む callable が含まれること、バリデーターが3つのみであること |
| 52 | 1.1.1 必須チェック：未入力でエラー / 1.1.2 最大文字列長チェック：上限値で正常終了 / 1.1.3 必須チェック：入力済みで正常終了 / 1.2.2 最大文字列長チェック：上限値で正常終了 / 1.2.3 最大文字列長チェック：上限値超過でエラー | `DeviceInventoryUpdateForm.device_name` フィールドの `validators` を取得し、`DataRequired` と `Length` の有無を確認する | `DataRequired` バリデーターが含まれること、`Length` バリデーターが存在し `max=100` であること、バリデーターが2つのみであること |
| 53 | 1.1.1 必須チェック：未入力でエラー / 1.1.2 最大文字列長チェック：上限値で正常終了 / 1.1.3 必須チェック：入力済みで正常終了 | `DeviceInventoryUpdateForm.device_type_id` フィールドの `validators` を取得し、`DataRequired` の有無を確認する | `DataRequired` バリデーターが含まれること、バリデーターが1つのみであること |
| 54 | 1.1.1 必須チェック：未入力でエラー / 1.1.2 最大文字列長チェック：上限値で正常終了 / 1.1.3 必須チェック：入力済みで正常終了 / 1.2.2 最大文字列長チェック：上限値で正常終了 / 1.2.3 最大文字列長チェック：上限値超過でエラー | `DeviceInventoryUpdateForm.device_model` フィールドの `validators` を取得し、`DataRequired` と `Length` の有無を確認する | `DataRequired` バリデーターが含まれること、`Length` バリデーターが存在し `max=100` であること、バリデーターが2つのみであること |
| 55 | 2.1.2 正常系処理：最小構成の入力で正常終了 / 1.2.2 最大文字列長チェック：上限値で正常終了 / 1.2.3 最大文字列長チェック：上限値超過でエラー | `DeviceInventoryUpdateForm.sim_id` フィールドの `validators` を取得し、`Optional` と `Length` の有無を確認する | `Optional` バリデーターが含まれること、`Length` バリデーターが存在し `max=20` であること、バリデーターが2つのみであること |
| 56 | 1.1.1 必須チェック：未入力でエラー / 1.1.2 最大文字列長チェック：上限値で正常終了 / 1.1.3 必須チェック：入力済みで正常終了 / 1.6.1 不整値チェック：許容値で正常終了 / 1.6.2 不整値チェック：非許容値でエラー | `DeviceInventoryUpdateForm.mac_address` フィールドの `validators` を取得し、`Regexp` と `DataRequired` の有無を確認する | `Regexp` バリデーターが含まれること、`DataRequired` バリデーターが含まれること、バリデーターが2つのみであること |
| 57 | 2.1.2 正常系処理：最小構成の入力で正常終了 / 1.2.2 最大文字列長チェック：上限値で正常終了 / 1.2.3 最大文字列長チェック：上限値超過でエラー | `DeviceInventoryUpdateForm.software_version` フィールドの `validators` を取得し、`Optional` と `Length` の有無を確認する | `Optional` バリデーターが含まれること、`Length` バリデーターが存在し `max=100` であること、バリデーターが2つのみであること |
| 58 | 2.1.2 正常系処理：最小構成の入力で正常終了 / 1.2.2 最大文字列長チェック：上限値で正常終了 / 1.2.3 最大文字列長チェック：上限値超過でエラー | `DeviceInventoryUpdateForm.device_location` フィールドの `validators` を取得し、`Optional` と `Length` の有無を確認する | `Optional` バリデーターが含まれること、`Length` バリデーターが存在し `max=100` であること、バリデーターが2つのみであること |
| 59 | 2.1.2 正常系処理：最小構成の入力で正常終了 | `DeviceInventoryUpdateForm.certificate_expiration_date` フィールドの `validators` を取得し、`Optional` の有無を確認する | `Optional` バリデーターが含まれること、バリデーターが1つのみであること |
| 60 | 1.1.1 必須チェック：未入力でエラー / 1.1.2 最大文字列長チェック：上限値で正常終了 / 1.1.3 必須チェック：入力済みで正常終了 | `DeviceInventoryUpdateForm.organization_id` フィールドの `validators` を取得し、`DataRequired` の有無を確認する | `DataRequired` バリデーターが含まれること、バリデーターが1つのみであること |
| 61 | 1.1.1 必須チェック：未入力でエラー / 1.1.2 最大文字列長チェック：上限値で正常終了 / 1.1.3 必須チェック：入力済みで正常終了 | `DeviceInventoryUpdateForm.inventory_status_id` フィールドの `validators` を取得し、`DataRequired` の有無を確認する | `DataRequired` バリデーターが含まれること、バリデーターが1つのみであること |
| 62 | 1.1.1 必須チェック：未入力でエラー / 1.1.2 最大文字列長チェック：上限値で正常終了 / 1.1.3 必須チェック：入力済みで正常終了 | `DeviceInventoryUpdateForm.purchase_date` フィールドの `validators` を取得し、`DataRequired` の有無を確認する | `DataRequired` バリデーターが含まれること、バリデーターが1つのみであること |
| 63 | 2.1.2 正常系処理：最小構成の入力で正常終了 / 1.4.1 日付形式チェック：有効な日付で正常終了 / 1.6.2 不整値チェック：非許容値でエラー | `DeviceInventoryUpdateForm.estimated_ship_date` フィールドの `validators` を取得し、`Optional` と `date_after_purchase_validator` の有無を確認する | `Optional` バリデーターが含まれること、`__qualname__` に `'date_after_purchase_validator'` を含む callable が含まれること、バリデーターが2つのみであること |
| 64 | 2.1.2 正常系処理：最小構成の入力で正常終了 / 1.4.1 日付形式チェック：有効な日付で正常終了 / 1.6.2 不整値チェック：非許容値でエラー | `DeviceInventoryUpdateForm.ship_date` フィールドの `validators` を取得し、`Optional` と `date_after_purchase_validator` の有無を確認する | `Optional` バリデーターが含まれること、`__qualname__` に `'date_after_purchase_validator'` を含む callable が含まれること、バリデーターが2つのみであること |
| 65 | 1.1.1 必須チェック：未入力でエラー / 1.1.2 最大文字列長チェック：上限値で正常終了 / 1.1.3 必須チェック：入力済みで正常終了 / 1.2.2 最大文字列長チェック：上限値で正常終了 / 1.2.3 最大文字列長チェック：上限値超過でエラー | `DeviceInventoryUpdateForm.inventory_location` フィールドの `validators` を取得し、`DataRequired` と `Length` の有無を確認する | `DataRequired` バリデーターが含まれること、`Length` バリデーターが存在し `max=100` であること、バリデーターが2つのみであること |
| 66 | 1.1.1 必須チェック：未入力でエラー / 1.1.2 最大文字列長チェック：上限値で正常終了 / 1.1.3 必須チェック：入力済みで正常終了 / 1.4.1 日付形式チェック：有効な日付で正常終了 / 1.6.2 不整値チェック：非許容値でエラー | `DeviceInventoryUpdateForm.manufacturer_warranty_end_date` フィールドの `validators` を取得し、`DataRequired` と `date_after_purchase_validator` の有無を確認する | `DataRequired` バリデーターが含まれること、`__qualname__` に `'date_after_purchase_validator'` を含む callable が含まれること、バリデーターが2つのみであること |
