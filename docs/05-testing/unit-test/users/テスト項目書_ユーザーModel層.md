# テスト項目書 - ユーザー管理機能 Model層

- **対象ファイル**: `src/iot_app/models/user.py`
- **テストコード**: `tests/unit/models/test_user.py`
- **観点表**: `docs/05-testing/unit-test/unit-test-perspectives.md`
- **ワークフロー仕様書**: `docs/03-features/flask-app/users/workflow-specification.md`

**テスト総数:** 15件

---

## 対応表

テストクラスと、ワークフロー仕様書の各ワークフロー・処理フロー項目の対応を示します。

| テストクラス | テスト項目No. | 対応ワークフロー | 処理フロー項目 | エンドポイント |
|------------|:---:|--------------|-------------|-------------|
| TestUserModel | 1〜11 | 全ワークフロー横断 | カラム定義・制約・デフォルト値検証（user_master テーブル） | 全エンドポイント |
| TestUserTypeModel | 12〜15 | 初期表示 / 検索・絞り込み / ユーザー登録（登録実行） / ユーザー更新（更新実行） | カラム定義・制約・デフォルト値検証（user_type_master テーブル） | `GET /admin/users` / `POST /admin/users/register` / `POST /admin/users/<id>/update` |

---

## ワークフロー別カバレッジ

ワークフロー仕様書の各ワークフローに対して、どのテストクラスが対応しているかを示します。

### 全ワークフロー横断（user_master テーブル定義）

| 処理フロー項目 | 対応テストクラス | テスト項目No. |
|-------------|--------------|:---:|
| テーブル名確認（user_master） | TestUserModel | 1 |
| 主キー確認（user_id） | TestUserModel | 2 |
| オートインクリメント確認（user_id） | TestUserModel | 3 |
| NOT NULL 確認（user_name） | TestUserModel | 4 |
| NOT NULL 確認（email_address） | TestUserModel | 5 |
| NOT NULL 確認（databricks_user_id） | TestUserModel | 6 |
| デフォルト値確認（language_code = 'ja'） | TestUserModel | 7 |
| デフォルト値確認（status = 1） | TestUserModel | 8 |
| デフォルト値確認（alert_notification_flag = True） | TestUserModel | 9 |
| デフォルト値確認（system_notification_flag = True） | TestUserModel | 10 |
| デフォルト値確認（delete_flag = False） | TestUserModel | 11 |

### 初期表示 / 検索・絞り込み / ユーザー登録（登録実行） / ユーザー更新（更新実行）

| 処理フロー項目 | 対応テストクラス | テスト項目No. |
|-------------|--------------|:---:|
| テーブル名確認（user_type_master） | TestUserTypeModel | 12 |
| 主キー確認（user_type_id） | TestUserTypeModel | 13 |
| NOT NULL 確認（user_type_name） | TestUserTypeModel | 14 |
| デフォルト値確認（delete_flag = False） | TestUserTypeModel | 15 |

---

## テストクラス一覧

テストクラスに対して、テスト観点、操作手順、予想結果を示します。

### TestUserModel

`User` モデルのカラム定義テスト（観点: 2.1 正常系処理（カラム定義・制約・デフォルト値が設計書通りであること））

| No | テスト観点 | 操作手順 | 予想結果 |
| -- | ---------- | -------- | -------- |
| 1 | 2.1.1 正常系：テーブル名 | app_context 内で `User.__tablename__` を参照する | `'user_master'` であること |
| 2 | 2.1.1 正常系：主キー | app_context 内で `User.__table__.c.user_id.primary_key` を参照する | `True` であること |
| 3 | 2.1.1 正常系：オートインクリメント | app_context 内で `User.__table__.c.user_id.autoincrement` を参照する | `True` であること |
| 4 | 2.1.1 正常系：NOT NULL（user_name） | app_context 内で `User.__table__.c.user_name.nullable` を参照する | `False` であること |
| 5 | 2.1.1 正常系：NOT NULL（email_address） | app_context 内で `User.__table__.c.email_address.nullable` を参照する | `False` であること |
| 6 | 2.1.1 正常系：NOT NULL（databricks_user_id） | app_context 内で `User.__table__.c.databricks_user_id.nullable` を参照する | `False` であること |
| 7 | 2.1.1 正常系：デフォルト値（language_code） | app_context 内で `User.__table__.c.language_code.default.arg` を参照する | `'ja'` であること |
| 8 | 2.1.1 正常系：デフォルト値（status） | app_context 内で `User.__table__.c.status.default.arg` を参照する | `1`（有効）であること |
| 9 | 2.1.1 正常系：デフォルト値（alert_notification_flag） | app_context 内で `User.__table__.c.alert_notification_flag.default.arg` を参照する | `True` であること |
| 10 | 2.1.1 正常系：デフォルト値（system_notification_flag） | app_context 内で `User.__table__.c.system_notification_flag.default.arg` を参照する | `True` であること |
| 11 | 2.1.1 正常系：デフォルト値（delete_flag） | app_context 内で `User.__table__.c.delete_flag.default.arg` を参照する | `False`（論理削除なし）であること |

---

### TestUserTypeModel

`UserType` モデルのカラム定義テスト（観点: 2.1 正常系処理（カラム定義・制約・デフォルト値が設計書通りであること））

| No | テスト観点 | 操作手順 | 予想結果 |
| -- | ---------- | -------- | -------- |
| 12 | 2.1.1 正常系：テーブル名 | app_context 内で `UserType.__tablename__` を参照する | `'user_type_master'` であること |
| 13 | 2.1.1 正常系：主キー | app_context 内で `UserType.__table__.c.user_type_id.primary_key` を参照する | `True` であること |
| 14 | 2.1.1 正常系：NOT NULL（user_type_name） | app_context 内で `UserType.__table__.c.user_type_name.nullable` を参照する | `False` であること |
| 15 | 2.1.1 正常系：デフォルト値（delete_flag） | app_context 内で `UserType.__table__.c.delete_flag.default.arg` を参照する | `False`（論理削除なし）であること |
