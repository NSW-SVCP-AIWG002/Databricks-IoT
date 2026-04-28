# テスト項目書 - ユーザー管理機能 Form層

- **対象ファイル**: `src/iot_app/forms/user.py`
- **テストコード**: `tests/unit/forms/test_user_form.py`
- **観点表**: `docs/05-testing/unit-test/unit-test-perspectives.md`
- **ワークフロー仕様書**: `docs/03-features/flask-app/users/workflow-specification.md`

**テスト総数:** 32件

---

## 対応表

テストクラスと、ワークフロー仕様書の各ワークフロー・処理フロー項目の対応を示します。

| テストクラス | テスト項目No. | 対応ワークフロー | 処理フロー項目 | エンドポイント |
|------------|:---:|--------------|-------------|-------------|
| TestUserCreateForm | 1〜20 | ユーザー登録（登録実行） | フォーム入力バリデーション（正常系・必須・最大長・形式） | `POST /admin/users/register` |
| TestUserUpdateForm | 21〜32 | ユーザー更新（更新実行） | フォーム入力バリデーション（正常系・必須・最大長・更新不可項目確認） | `POST /admin/users/<id>/update` |

---

## ワークフロー別カバレッジ

ワークフロー仕様書の各ワークフローに対して、どのテストクラスが対応しているかを示します。

### ユーザー登録（登録実行）

| 処理フロー項目 | 対応テストクラス | テスト項目No. |
|-------------|--------------|:---:|
| フォーム入力バリデーション（全必須項目が有効） | TestUserCreateForm | 1 |
| 必須チェック（user_name 空文字） | TestUserCreateForm | 2 |
| 最大文字列長チェック（user_name 上限+1） | TestUserCreateForm | 3 |
| 最大文字列長チェック（user_name 上限±0） | TestUserCreateForm | 4 |
| 最大文字列長チェック（user_name 上限-1） | TestUserCreateForm | 5 |
| 必須チェック（email_address 空文字） | TestUserCreateForm | 6 |
| メールアドレス形式チェック（@なし） | TestUserCreateForm | 7 |
| 最大文字列長チェック（email_address 上限+1） | TestUserCreateForm | 8 |
| 最大文字列長チェック（email_address 上限±0） | TestUserCreateForm | 9 |
| 最大文字列長チェック（email_address 上限-1） | TestUserCreateForm | 10 |
| メールアドレス形式チェック（ドメインなし） | TestUserCreateForm | 11 |
| メールアドレス形式チェック（ローカル部なし） | TestUserCreateForm | 12 |
| 最大文字列長チェック（address 上限+1） | TestUserCreateForm | 13 |
| 最大文字列長チェック（address 上限±0） | TestUserCreateForm | 14 |
| 最大文字列長チェック（address 上限-1） | TestUserCreateForm | 15 |
| 任意項目（address 空文字） | TestUserCreateForm | 16 |
| 必須チェック（organization_id 未選択） | TestUserCreateForm | 17 |
| 必須チェック（user_type_id 未選択） | TestUserCreateForm | 18 |
| 必須チェック（region_id 未選択） | TestUserCreateForm | 19 |
| 必須チェック（status 未選択） | TestUserCreateForm | 20 |

### ユーザー更新（更新実行）

| 処理フロー項目 | 対応テストクラス | テスト項目No. |
|-------------|--------------|:---:|
| フォーム入力バリデーション（全必須項目が有効） | TestUserUpdateForm | 21 |
| 更新不可項目（email_address・organization_id・user_type_id）非存在確認 | TestUserUpdateForm | 32 |
| 必須チェック（user_name 空文字） | TestUserUpdateForm | 22 |
| 最大文字列長チェック（user_name 上限+1） | TestUserUpdateForm | 23 |
| 最大文字列長チェック（user_name 上限ちょうど） | TestUserUpdateForm | 24 |
| 最大文字列長チェック（user_name 上限-1） | TestUserUpdateForm | 25 |
| 最大文字列長チェック（address 上限+1） | TestUserUpdateForm | 26 |
| 最大文字列長チェック（address 上限ちょうど） | TestUserUpdateForm | 27 |
| 最大文字列長チェック（address 上限-1） | TestUserUpdateForm | 28 |
| 任意項目（address 空文字） | TestUserUpdateForm | 29 |
| 必須チェック（region_id 未選択） | TestUserUpdateForm | 30 |
| 必須チェック（status 未選択） | TestUserUpdateForm | 31 |

---

## テストクラス一覧

テストクラスに対して、テスト観点、操作手順、予想結果を示します。

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
