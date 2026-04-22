# テスト項目書 - ユーザー管理機能 Model層

**対象ファイル:** `tests/unit/models/test_user.py`
**対象モジュール:** `iot_app.models.user`
**テスト総数:** 15件

---

## TestUserModel

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

## TestUserTypeModel

`UserType` モデルのカラム定義テスト（観点: 2.1 正常系処理（カラム定義・制約・デフォルト値が設計書通りであること））

| No | テスト観点 | 操作手順 | 予想結果 |
| -- | ---------- | -------- | -------- |
| 12 | 2.1.1 正常系：テーブル名 | app_context 内で `UserType.__tablename__` を参照する | `'user_type_master'` であること |
| 13 | 2.1.1 正常系：主キー | app_context 内で `UserType.__table__.c.user_type_id.primary_key` を参照する | `True` であること |
| 14 | 2.1.1 正常系：NOT NULL（user_type_name） | app_context 内で `UserType.__table__.c.user_type_name.nullable` を参照する | `False` であること |
| 15 | 2.1.1 正常系：デフォルト値（delete_flag） | app_context 内で `UserType.__table__.c.delete_flag.default.arg` を参照する | `False`（論理削除なし）であること |
