# テスト項目書 - ユーザー管理機能 Form層

**対象ファイル:** `tests/unit/forms/test_user_form.py`
**対象モジュール:** `iot_app.forms.user`
**テスト総数:** 32件

---

### TestUserCreateForm

`UserCreateForm` のバリデーションテスト（観点: 1.1.1 必須チェック, 1.1.2 最大文字列長チェック, 1.1.5 メールアドレス形式チェック, 2.1 正常系処理）

| No | テスト観点 | 操作手順 | 予想結果 |
| -- | ---------- | -------- | -------- |
| 1 | 2.1.1 正常系：有効な入力値 | app の test_request_context 内で有効なデータ全項目を渡して `UserCreateForm` を生成し、`form.validate()` を呼ぶ | バリデーションが通ること（`True` を返すこと） |
| 2 | 1.1.1 必須チェック（user_name 空文字） | `user_name=''` で `UserCreateForm` を生成し、`form.validate()` を呼ぶ | バリデーションが失敗し、`form.errors` に `'user_name'` が含まれること |
| 3 | 1.1.2 最大文字列長チェック（user_name 上限+1） | `user_name='あ'*21`（21文字）で `UserCreateForm` を生成し、`form.validate()` を呼ぶ | バリデーションが失敗し、`form.errors` に `'user_name'` が含まれること |
| 4 | 1.1.2 最大文字列長チェック（user_name 上限±0） | `user_name='あ'*20`（20文字）で `UserCreateForm` を生成し、`form.validate()` を呼ぶ | バリデーションが通ること |
| 5 | 1.1.2 最大文字列長チェック（user_name 上限-1） | `user_name='あ'*19`（19文字）で `UserCreateForm` を生成し、`form.validate()` を呼ぶ | バリデーションが通ること |
| 6 | 1.1.1 必須チェック（email_address 空文字） | `email_address=''` で `UserCreateForm` を生成し、`form.validate()` を呼ぶ | バリデーションが失敗し、`form.errors` に `'email_address'` が含まれること |
| 7 | 1.1.5 メールアドレス形式チェック（@なし） | `email_address='not-an-email'` で `UserCreateForm` を生成し、`form.validate()` を呼ぶ | バリデーションが失敗し、`form.errors` に `'email_address'` が含まれること |
| 8 | 1.1.2 最大文字列長チェック（email_address 上限+1） | 合計255文字のメールアドレスで `UserCreateForm` を生成し、`form.validate()` を呼ぶ | バリデーションが失敗し、`form.errors` に `'email_address'` が含まれること |
| 9 | 1.1.2 最大文字列長チェック（email_address 上限±0） | 合計254文字のメールアドレスで `UserCreateForm` を生成し、`form.validate()` を呼ぶ | バリデーションが通ること |
| 10 | 1.1.2 最大文字列長チェック（email_address 上限-1） | 合計253文字のメールアドレスで `UserCreateForm` を生成し、`form.validate()` を呼ぶ | バリデーションが通ること |
| 11 | 1.1.5 メールアドレス形式チェック（ドメインなし） | `email_address='user@'` で `UserCreateForm` を生成し、`form.validate()` を呼ぶ | バリデーションが失敗し、`form.errors` に `'email_address'` が含まれること |
| 12 | 1.1.5 メールアドレス形式チェック（ローカル部なし） | `email_address='@example.com'` で `UserCreateForm` を生成し、`form.validate()` を呼ぶ | バリデーションが失敗し、`form.errors` に `'email_address'` が含まれること |
| 13 | 1.1.2 最大文字列長チェック（address 上限＋1） | `address='あ'*501`（501文字）で `UserCreateForm` を生成し、`form.validate()` を呼ぶ | バリデーションが失敗し、`form.errors` に `'address'` が含まれること |
| 14 | 1.1.2 最大文字列長チェック（address 上限±0） | `address='あ'*500`（500文字）で `UserCreateForm` を生成し、`form.validate()` を呼ぶ | バリデーションが通ること |
| 15 | 1.1.2 最大文字列長チェック（address 上限-1） | `address='あ'*499`（499文字）で `UserCreateForm` を生成し、`form.validate()` を呼ぶ | バリデーションが通ること |
| 16 | 1.1.2 最大文字列長チェック（address 空文字・任意項目） | `address=''` で `UserCreateForm` を生成し、`form.validate()` を呼ぶ | バリデーションが通ること（address は任意項目） |
| 17 | 1.1.1 必須チェック（organization_id 未選択） | `organization_id=None` で `UserCreateForm` を生成し、`form.validate()` を呼ぶ | バリデーションが失敗し、`form.errors` に `'organization_id'` が含まれること |
| 18 | 1.1.1 必須チェック（user_type_id 未選択） | `user_type_id=None` で `UserCreateForm` を生成し、`form.validate()` を呼ぶ | バリデーションが失敗し、`form.errors` に `'user_type_id'` が含まれること |
| 19 | 1.1.1 必須チェック（region_id 未選択） | `region_id=None` で `UserCreateForm` を生成し、`form.validate()` を呼ぶ | バリデーションが失敗し、`form.errors` に `'region_id'` が含まれること |
| 20 | 1.1.1 必須チェック（status 未選択） | `status=None` で `UserCreateForm` を生成し、`form.validate()` を呼ぶ | バリデーションが失敗し、`form.errors` に `'status'` が含まれること |

---

### TestUserUpdateForm

`UserUpdateForm` のバリデーションテスト（観点: 1.1.1 必須チェック, 1.1.2 最大文字列長チェック, 2.1 正常系処理）

| No | テスト観点 | 操作手順 | 予想結果 |
| -- | ---------- | -------- | -------- |
| 21 | 2.1.1 正常系：有効な入力値 | app の test_request_context 内で有効なデータ全項目を渡して `UserUpdateForm` を生成し、`form.validate()` を呼ぶ | バリデーションが通ること（`True` を返すこと） |
| 22 | 1.1.1 必須チェック（user_name 空文字） | `user_name=''` で `UserUpdateForm` を生成し、`form.validate()` を呼ぶ | バリデーションが失敗し、`form.errors` に `'user_name'` が含まれること |
| 23 | 1.1.2 最大文字列長チェック（user_name 上限+1） | `user_name='あ'*21`（21文字）で `UserUpdateForm` を生成し、`form.validate()` を呼ぶ | バリデーションが失敗し、`form.errors` に `'user_name'` が含まれること |
| 24 | 1.1.2 最大文字列長チェック（user_name 上限ちょうど） | `user_name='あ'*20`（20文字）で `UserUpdateForm` を生成し、`form.validate()` を呼ぶ | バリデーションが通ること |
| 25 | 1.1.2 最大文字列長チェック（user_name 上限-1） | `user_name='あ'*19`（19文字）で `UserUpdateForm` を生成し、`form.validate()` を呼ぶ | バリデーションが通ること |
| 26 | 1.1.2 最大文字列長チェック（address 上限+1） | `address='あ'*501`（501文字）で `UserUpdateForm` を生成し、`form.validate()` を呼ぶ | バリデーションが失敗し、`form.errors` に `'address'` が含まれること |
| 27 | 1.1.2 最大文字列長チェック（address 上限ちょうど） | `address='あ'*500`（500文字）で `UserUpdateForm` を生成し、`form.validate()` を呼ぶ | バリデーションが通ること |
| 28 | 1.1.2 最大文字列長チェック（address 上限-1） | `address='あ'*499`（499文字）で `UserUpdateForm` を生成し、`form.validate()` を呼ぶ | バリデーションが通ること |
| 29 | 1.1.2 最大文字列長チェック（address 空文字・任意項目） | `address=''` で `UserUpdateForm` を生成し、`form.validate()` を呼ぶ | バリデーションが通ること（address は任意項目） |
| 30 | 1.1.1 必須チェック（region_id 未選択） | `region_id=None` で `UserUpdateForm` を生成し、`form.validate()` を呼ぶ | バリデーションが失敗し、`form.errors` に `'region_id'` が含まれること |
| 31 | 1.1.1 必須チェック（status 未選択） | `status=None` で `UserUpdateForm` を生成し、`form.validate()` を呼ぶ | バリデーションが失敗し、`form.errors` に `'status'` が含まれること |
| 32 | 2.1.1 正常系：email_address フィールド非存在 | `UserUpdateForm` を生成し、`form._fields` を参照する | `email_address、organization_id、user_type_id` が `form._fields` に含まれないこと（更新不可項目） |
