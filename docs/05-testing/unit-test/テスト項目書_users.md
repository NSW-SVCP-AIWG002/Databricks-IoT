# テスト項目書 - ユーザー管理機能

対象テストファイル:
- `tests/unit/services/test_user_service.py`
- `tests/unit/forms/test_user_form.py`
- `tests/unit/databricks/test_scim_client.py`
- `tests/unit/models/test_user.py`

---

## test_user_service.py

### TestCheckEmailDuplicate

`check_email_duplicate` のテスト（観点: 3.1.1 検索条件指定, 3.1.4 検索結果戻り値ハンドリング, 2.2 対象データ存在チェック）

| No | テスト観点 | 操作手順 | 予想結果 |
| -- | ---------- | -------- | -------- |
| 1 | 3.1.4.1 検索結果戻り値（存在あり） | `User.query.filter_by().first()` が MagicMock を返すよう設定し、`check_email_duplicate('dup@example.com')` を呼ぶ | 戻り値が `True` であること |
| 2 | 3.1.4.2 検索結果戻り値（存在なし） | `User.query.filter_by().first()` が `None` を返すよう設定し、`check_email_duplicate('new@example.com')` を呼ぶ | 戻り値が `False` であること |
| 3 | 3.1.1.1 検索条件指定（email_address） | `User.query.filter_by().first()` が `None` を返すよう設定し、`check_email_duplicate('test@example.com')` を呼ぶ | `filter_by` が `email_address='test@example.com', delete_flag=False` で1回呼ばれること |
| 4 | 2.2.3 論理削除済み除外 | `User.query.filter_by().first()` が `None` を返すよう設定し、`check_email_duplicate('any@example.com')` を呼ぶ | `filter_by` の引数に `delete_flag=False` が含まれること |

---

### TestGetDefaultSearchParams

`get_default_search_params` のテスト（観点: 2.1 正常系処理, 3.1.2 検索条件未指定（全件相当））

| No | テスト観点 | 操作手順 | 予想結果 |
| -- | ---------- | -------- | -------- |
| 5 | 2.1.1 正常系：必須キー全含む | `get_default_search_params()` を呼ぶ | 戻り値の dict に `page`, `per_page`, `sort_by`, `order`, `user_name`, `email_address`, `user_type_id`, `organization_id`, `region_id`, `status` が全て含まれること |
| 6 | 3.1.2.1 検索条件未指定デフォルト（空文字） | `get_default_search_params()` を呼ぶ | `user_name` と `email_address` のデフォルト値が空文字 `''` であること |
| 7 | 3.1.2.1 検索条件未指定デフォルト（None） | `get_default_search_params()` を呼ぶ | `user_type_id`, `organization_id`, `region_id`, `status` のデフォルト値が `None` であること |
| 8 | 2.1.1 正常系：デフォルトソート順 | `get_default_search_params()` を呼ぶ | `sort_by` が `'user_name'`、`order` が `'asc'` であること |
| 9 | 2.1.1 正常系：デフォルトページ番号 | `get_default_search_params()` を呼ぶ | `page` のデフォルト値が `1` であること |

---

### TestSearchUsers

`search_users` のテスト（観点: 3.1.1 検索条件指定, 3.1.2 検索条件未指定, 3.1.3 ページング, 3.1.4 戻り値ハンドリング）

| No | テスト観点 | 操作手順 | 予想結果 |
| -- | ---------- | -------- | -------- |
| 10 | 3.1.4.1 戻り値ハンドリング（正常系） | `db.session.query()` がユーザー2件・total=2 を返すモックを設定し、全条件Noneのparamsで `search_users(params, user_id=1)` を呼ぶ | 戻り値が長さ2のタプルであること |
| 11 | 3.1.4.2 戻り値ハンドリング（空結果） | `db.session.query()` が空リスト・total=0 を返すモックを設定し、`search_users(params, user_id=1)` を呼ぶ | 戻り値の users が空リスト、total が `0` であること |
| 12 | 3.1.1.1 検索条件指定（user_name） | `user_name='田中'` を含む params で `search_users(params, user_id=1)` を呼ぶ | `mock_query.filter` が呼ばれること |
| 13 | 3.1.1.2 複数条件指定（user_name + email） | `user_name='田中'`, `email_address='@example'` を含む params で `search_users(params, user_id=1)` を呼ぶ | `mock_query.filter` が2回以上呼ばれること |
| 14 | 3.1.1.3 未指定条件は除外 | 全フィルター条件がNoneのparamsで `search_users(params, user_id=1)` を呼ぶ | 追加フィルタ（`mock_query.filter`）が0回であること |
| 15 | 3.1.1.5 AND結合（OR未使用） | `user_name='田中'`, `email_address='@example'`, `user_type_id=2` の params で `search_users(params, user_id=1)` を呼ぶ | `mock_query.filter` が2回以上呼ばれること（OR結合でなくAND連鎖） |
| 16 | 3.1.1.4 スコープ制限（login_user_id） | `user_id=99` で `search_users(params, user_id=99)` を呼ぶ | `db.session.query` が `UserMasterByUser` を引数として1回呼ばれること |
| 17 | 3.1.3.1 ページングオフセット計算 | `page=3, per_page=20` の params で `search_users(params, user_id=1)` を呼ぶ | `mock_query.limit().offset` が `40` で呼ばれること |
| 18 | 3.1.3.1 per_page が limit に渡される | `per_page=10` の params で `search_users(params, user_id=1)` を呼ぶ | `mock_query.limit` が `10` で1回呼ばれること |

---

### TestGetUserByDatabricksId

`get_user_by_databricks_id` のテスト（観点: 2.2 対象データ存在チェック, 3.1.1 検索条件指定）

| No | テスト観点 | 操作手順 | 予想結果 |
| -- | ---------- | -------- | -------- |
| 19 | 2.2.1 対象IDが存在する場合 | `db.session.query().filter().first()` が MagicMock を返すよう設定し、`get_user_by_databricks_id('uid-1', login_user_id=1)` を呼ぶ | 戻り値がモックユーザーオブジェクトであること |
| 20 | 2.2.2 対象IDが存在しない場合 | `db.session.query().filter().first()` が `None` を返すよう設定し、`get_user_by_databricks_id('nonexistent', login_user_id=1)` を呼ぶ | 戻り値が `None` であること |
| 21 | 2.2.3 論理削除済み除外 | `db.session.query().filter().first()` が `None` を返すよう設定し、`get_user_by_databricks_id('uid-1', login_user_id=1)` を呼ぶ | `db.session.query().filter` が1回呼ばれること（delete_flag フィルタを含む） |
| 22 | 3.1.1.1 検索条件指定（スコープ制限） | `login_user_id=42` で `get_user_by_databricks_id('uid-1', login_user_id=42)` を呼ぶ | `db.session.query` が `UserMasterByUser` を引数として1回呼ばれること |

---

### TestGetUserFormOptions

`get_user_form_options` のテスト（観点: 2.1 正常系処理, 3.1.1 検索条件指定, 3.1.4 戻り値ハンドリング）

| No | テスト観点 | 操作手順 | 予想結果 |
| -- | ---------- | -------- | -------- |
| 23 | 2.1.1 / 3.1.4.1 正常系：4タプル返却 | `db.session.query()` が空リストを返すモックを設定し、`get_user_form_options(user_id=1, login_user_type_id=2)` を呼ぶ | 戻り値が長さ4のタプル（organizations, user_types, regions, sort_items）であること |
| 24 | 3.1.1.1 検索条件指定（下位ロールのみ） | `db.session.query()` が空リストを返すモックを設定し、`get_user_form_options(user_id=1, login_user_type_id=2)` を呼ぶ | `db.session.query().filter` が呼ばれること（UserType に対して user_type_id > 2 のフィルタ） |

---

### TestGetAllUsersForExport

`get_all_users_for_export` のテスト（観点: 3.1.1 検索条件指定, 3.1.2 検索条件未指定, 3.1.4 戻り値ハンドリング, 2.2 存在チェック）

| No | テスト観点 | 操作手順 | 予想結果 |
| -- | ---------- | -------- | -------- |
| 25 | 3.1.4.1 戻り値ハンドリング（正常系） | モックが2件のユーザーリストを返すよう設定し、全条件Noneのparamsで `get_all_users_for_export(params, user_id=1)` を呼ぶ | 戻り値がモックユーザーのリストであること |
| 26 | 3.1.4.2 戻り値ハンドリング（空結果） | モックが空リストを返すよう設定し、`get_all_users_for_export(params, user_id=1)` を呼ぶ | 戻り値が空リストであること |
| 27 | 2.2.3 論理削除済み除外 | `db.session.query().filter()` が空リストを返すよう設定し、`get_all_users_for_export(params, user_id=1)` を呼ぶ | `db.session.query().filter` が1回呼ばれること（delete_flag=False フィルタ） |
| 28 | 3.1.1.1 検索条件指定（user_name） | `user_name='田中'` を含む params で `get_all_users_for_export(params, user_id=1)` を呼ぶ | `mock_q.filter` が呼ばれること |
| 29 | 3.1.1.3 未指定条件は除外 | 全フィルター条件がNoneのparamsで `get_all_users_for_export(params, user_id=1)` を呼ぶ | 追加フィルタ（`mock_q.filter`）が0回であること |

---

### TestInsertUnityCatalogUser

`_insert_unity_catalog_user` のテスト（観点: 3.2.1 登録処理呼び出し）

| No | テスト観点 | 操作手順 | 予想結果 |
| -- | ---------- | -------- | -------- |
| 30 | 3.2.1.1 登録処理呼び出し（1回） | `UnityCatalogConnector` をモック化し、`_insert_unity_catalog_user(user_id=1, databricks_user_id='uid-1', user_data={...}, creator_id=99)` を呼ぶ | `mock_conn.execute_dml` が1回呼ばれること |
| 31 | 3.2.1.1 登録処理呼び出し（全フィールド含む） | `UnityCatalogConnector` をモック化し、`_insert_unity_catalog_user(user_id=42, databricks_user_id='uid-42', user_data={...}, creator_id=10)` を呼ぶ | `execute_dml` のパラメータに `user_id=42` と `databricks_user_id='uid-42'` が含まれること |

---

### TestRollbackCreateUser

`_rollback_create_user` のテスト（観点: 2.3 副作用チェック, 1.3 エラーハンドリング）

| No | テスト観点 | 操作手順 | 予想結果 |
| -- | ---------- | -------- | -------- |
| 32 | 2.3.2 副作用チェック（SCIM 削除実行） | `ScimClient` をモック化し、`_rollback_create_user(user_id=None, databricks_user_id='uid-1', uc_inserted=False)` を呼ぶ | `mock_scim.delete_user` が `'uid-1'` で1回呼ばれること |
| 33 | 2.3.2 副作用チェック（SCIM 削除スキップ） | `ScimClient` をモック化し、`_rollback_create_user(user_id=None, databricks_user_id=None, uc_inserted=False)` を呼ぶ | `mock_scim.delete_user` が呼ばれないこと |
| 34 | 2.3.2 副作用チェック（UC 削除実行） | `ScimClient`, `UnityCatalogConnector` をモック化し、`_rollback_create_user(user_id=5, databricks_user_id='uid-1', uc_inserted=True)` を呼ぶ | `mock_conn.execute_dml` が1回呼ばれること |
| 35 | 2.3.2 副作用チェック（UC 削除スキップ） | `ScimClient`, `UnityCatalogConnector` をモック化し、`_rollback_create_user(user_id=5, databricks_user_id='uid-1', uc_inserted=False)` を呼ぶ | `mock_conn.execute_dml` が呼ばれないこと |
| 36 | 1.3.1 エラーハンドリング（SCIM例外抑制） | `ScimClient.delete_user` が例外を投げるよう設定し、`_rollback_create_user(user_id=None, databricks_user_id='uid-1', uc_inserted=False)` を呼ぶ | 例外が re-raise されないこと（ベストエフォート） |
| 37 | 1.3.1 エラーハンドリング（UC例外抑制） | `UnityCatalogConnector.execute_dml` が例外を投げるよう設定し、`_rollback_create_user(user_id=5, databricks_user_id='uid-1', uc_inserted=True)` を呼ぶ | 例外が re-raise されないこと（ベストエフォート） |

---

### TestCreateUser

`create_user` のテスト（観点: 2.1 正常系処理, 2.3 副作用チェック, 3.2 登録機能, 1.3 エラーハンドリング）

| No | テスト観点 | 操作手順 | 予想結果 |
| -- | ---------- | -------- | -------- |
| 38 | 2.1.1 / 3.2.2.1 正常系：commit・結果dict | `db`, `User`, `ScimClient`, `_insert_unity_catalog_user` をモック化し（`create_user` が `'new-uid'` を返す）、`create_user(form_data, creator_id=1, auth_provider=...)` を呼ぶ | `db.session.commit` が1回呼ばれ、戻り値に `invite_sent`, `invite_failed` キーが含まれること |
| 39 | 3.2.1.1 登録処理呼び出し（仮登録 delete_flag=True） | `User` のコンストラクタを記録するよう設定し、`create_user(form_data, creator_id=1, auth_provider=...)` を呼ぶ | `User()` 生成時の引数に `delete_flag=True` が含まれること（仮登録状態） |
| 40 | 3.2.1.1 登録処理呼び出し（活性化 delete_flag=False） | `User` モックが `delete_flag=True` 状態で返るよう設定し、`create_user(form_data, creator_id=1, auth_provider=...)` を呼ぶ | 活性化ステップで `mock_user_obj.delete_flag` が `False` に更新されること |
| 41 | 3.2.1.1 登録処理呼び出し（SCIM email・name） | `ScimClient` をモック化し、`create_user(form_data, creator_id=1, auth_provider=...)` を呼ぶ | `mock_scim.create_user` が `email=form_data['email_address'], display_name=form_data['user_name']` で1回呼ばれること |
| 42 | 2.3.2 / 1.3.1 副作用チェック（SCIM失敗→rollback・例外伝播） | `ScimClient.create_user` が例外を投げるよう設定し、`create_user(...)` を呼ぶ | `_rollback_create_user` が1回呼ばれ、例外が伝播すること |
| 43 | 2.3.2 副作用チェック（UC INSERT失敗→uc_inserted=False） | `_insert_unity_catalog_user` が例外を投げるよう設定し、`create_user(...)` を呼ぶ | `_rollback_create_user` が `uc_inserted=False` で呼ばれること |
| 44 | 2.3.2 副作用チェック（commit失敗→uc_inserted=True） | `db.session.commit` が例外を投げるよう設定し、`create_user(...)` を呼ぶ | `_rollback_create_user` が `uc_inserted=True` で呼ばれること |
| 45 | 3.2.1.1 登録処理呼び出し（グループ追加） | `ScimClient.create_user` が `'new-uid'` を返すよう設定し、`create_user(form_data, creator_id=1, auth_provider=...)` を呼ぶ | `mock_scim.add_user_to_group` が1回呼ばれ、位置引数に `'new-uid'` が含まれること |
| 46 | 2.3.2 副作用チェック（グループ追加失敗→uc_inserted=False） | `ScimClient.add_user_to_group` が例外を投げるよう設定し、`create_user(...)` を呼ぶ | `_rollback_create_user` が1回呼ばれ、`uc_inserted=False` であること |

---

### TestUpdateOltpUser

`_update_oltp_user` のテスト（観点: 3.3.1 更新処理呼び出し, 3.3.2 更新結果）

| No | テスト観点 | 操作手順 | 予想結果 |
| -- | ---------- | -------- | -------- |
| 47 | 3.3.1.1 更新処理呼び出し（全更新可能フィールド） | `User.query.get` がモックユーザーを返すよう設定し、`_update_oltp_user(user_id=1, user_data={user_name:'更新後名前', region_id:2, status:0,...}, modifier_id=99)` を呼ぶ | モックユーザーの `user_name='更新後名前'`, `region_id=2`, `status=0` が設定されること |
| 48 | 3.3.2.2 更新結果（対象user_id） | `User.query.get` がモックユーザーを返すよう設定し、`_update_oltp_user(user_id=42, user_data={...}, modifier_id=1)` を呼ぶ | `User.query.get` が `42` で1回呼ばれること |

---

### TestUpdateUnityCatalogUser

`_update_unity_catalog_user` のテスト（観点: 3.3.1 更新処理呼び出し）

| No | テスト観点 | 操作手順 | 予想結果 |
| -- | ---------- | -------- | -------- |
| 49 | 3.3.1.1 更新処理呼び出し（execute_dml 1回） | `UnityCatalogConnector` をモック化し、`_update_unity_catalog_user(user_id=1, user_data={...}, modifier_id=99)` を呼ぶ | `mock_conn.execute_dml` が1回呼ばれること |
| 50 | 3.3.2.2 更新結果（user_id パラメータ） | `UnityCatalogConnector` をモック化し、`_update_unity_catalog_user(user_id=55, user_data={...}, modifier_id=1)` を呼ぶ | `execute_dml` のパラメータに `user_id=55` が含まれること |

---

### TestRollbackUpdateUser

`_rollback_update_user` のテスト（観点: 2.3 副作用チェック, 1.3 エラーハンドリング）

| No | テスト観点 | 操作手順 | 予想結果 |
| -- | ---------- | -------- | -------- |
| 51 | 2.3.2 副作用チェック（SCIM・UC復元） | `User.query.get` がモックユーザーを返し、`ScimClient`, `UnityCatalogConnector` をモック化して `_rollback_update_user(databricks_user_id='uid-1', user_id=1)` を呼ぶ | `mock_scim.update_user` と `mock_conn.execute_dml` がそれぞれ1回呼ばれること |
| 52 | 2.3.2 副作用チェック（元データなし→何もしない） | `User.query.get` が `None` を返すよう設定し、`_rollback_update_user(databricks_user_id='uid-1', user_id=999)` を呼ぶ | `mock_scim.update_user` が呼ばれないこと |
| 53 | 1.3.1 エラーハンドリング（ロールバック例外抑制） | `ScimClient.update_user` が例外を投げるよう設定し、`_rollback_update_user(databricks_user_id='uid-1', user_id=1)` を呼ぶ | 例外が re-raise されないこと（ベストエフォート） |

---

### TestUpdateUser

`update_user` のテスト（観点: 2.1 正常系処理, 2.3 副作用チェック, 3.3 更新機能, 1.3 エラーハンドリング）

| No | テスト観点 | 操作手順 | 予想結果 |
| -- | ---------- | -------- | -------- |
| 54 | 2.1.1 / 3.3.2.1 正常系：commit | `db`, `ScimClient`, `_update_oltp_user`, `_update_unity_catalog_user` をモック化し、`update_user(user_id=1, databricks_user_id='uid-1', user_data={...}, modifier_id=1)` を呼ぶ | `db.session.commit` が1回呼ばれること |
| 55 | 3.3.1.1 更新処理呼び出し（Saga実行順） | call_order リストを使い各ステップの呼び出し順を記録し、`update_user(...)` を呼ぶ | 呼び出し順が `['scim', 'uc', 'oltp']` であること（①SCIM update → ②UC UPDATE → ③OLTP UPDATE） |
| 56 | 2.3.2 / 1.3.1 副作用チェック（SCIM失敗→rollback・例外伝播） | `ScimClient.update_user` が例外を投げるよう設定し、`update_user(...)` を呼ぶ | `_rollback_update_user` が1回呼ばれ、例外が伝播すること |
| 57 | 2.3.2 / 1.3.1 副作用チェック（UC失敗→rollback・例外伝播） | `_update_unity_catalog_user` が例外を投げるよう設定し、`update_user(...)` を呼ぶ | `_rollback_update_user` が1回呼ばれ、例外が伝播すること |
| 58 | 2.3.2 / 1.3.1 副作用チェック（OLTP失敗→rollback・例外伝播） | `_update_oltp_user` が例外を投げるよう設定し、`update_user(...)` を呼ぶ | `_rollback_update_user` が1回呼ばれ、例外が伝播すること |

---

### TestDeleteUnityCatalogUser

`_delete_unity_catalog_user` のテスト（観点: 3.4.1 削除処理呼び出し）

| No | テスト観点 | 操作手順 | 予想結果 |
| -- | ---------- | -------- | -------- |
| 59 | 3.4.1.1 削除処理呼び出し（execute_dml 1回） | `UnityCatalogConnector` をモック化し、`_delete_unity_catalog_user(user_id=5)` を呼ぶ | `mock_conn.execute_dml` が1回呼ばれること |
| 60 | 3.4.1.1 削除処理呼び出し（user_id パラメータ） | `UnityCatalogConnector` をモック化し、`_delete_unity_catalog_user(user_id=77)` を呼ぶ | `execute_dml` のパラメータに `user_id=77` が含まれること |

---

### TestRollbackDeleteUser

`_rollback_delete_user` のテスト（観点: 2.3 副作用チェック, 1.3 エラーハンドリング）

| No | テスト観点 | 操作手順 | 予想結果 |
| -- | ---------- | -------- | -------- |
| 61 | 2.3.2 副作用チェック（UC再INSERT） | `User.query.get` がモックユーザーを返し、`UnityCatalogConnector` をモック化して `_rollback_delete_user(user_id=1)` を呼ぶ | `mock_conn.execute_dml` が1回呼ばれること |
| 62 | 2.3.2 副作用チェック（元データなし→何もしない） | `User.query.get` が `None` を返すよう設定し、`_rollback_delete_user(user_id=999)` を呼ぶ | `mock_conn.execute_dml` が呼ばれないこと |
| 63 | 1.3.1 エラーハンドリング（ロールバック例外抑制） | `UnityCatalogConnector.execute_dml` が例外を投げるよう設定し、`_rollback_delete_user(user_id=1)` を呼ぶ | 例外が re-raise されないこと（ベストエフォート） |

---

### TestDeleteUser

`delete_user` のテスト（観点: 2.1 正常系処理, 2.3 副作用チェック, 3.4 削除機能, 1.3 エラーハンドリング）

| No | テスト観点 | 操作手順 | 予想結果 |
| -- | ---------- | -------- | -------- |
| 64 | 2.1.1 / 3.4.2.1 正常系：commit | `db`, `ScimClient`, `_delete_unity_catalog_user` をモック化し、`delete_user(user=user_mock, deleter_id=99)` を呼ぶ | `db.session.commit` が1回呼ばれること |
| 65 | 3.4.1.1 削除処理呼び出し（OLTP論理削除） | `db`, `ScimClient`, `_delete_unity_catalog_user` をモック化し、`delete_user(user=user_mock, deleter_id=99)` を呼ぶ | `user.delete_flag` が `True` に設定されること |
| 66 | 3.4.1.1 削除処理呼び出し（Saga実行順） | call_order リストを使い各ステップの呼び出し順を記録し、`delete_user(user=user_mock, deleter_id=99)` を呼ぶ | 呼び出し順が `['uc', 'oltp', 'scim']` であること（①UC DELETE → ②OLTP flush → ③SCIM delete） |
| 67 | 2.3.2 副作用チェック（UC失敗→rollback不要） | `_delete_unity_catalog_user` が例外を投げるよう設定し、`delete_user(...)` を呼ぶ | `_rollback_delete_user` が呼ばれないこと（uc_deleted=False のため） |
| 68 | 2.3.2 / 1.3.1 副作用チェック（OLTP flush失敗→UCロールバック・例外伝播） | `db.session.flush` が例外を投げるよう設定し、`delete_user(...)` を呼ぶ | `_rollback_delete_user` が `user.user_id` で1回呼ばれ、例外が伝播すること |
| 69 | 2.3.2 / 1.3.1 副作用チェック（SCIM失敗→UCロールバック・例外伝播） | `ScimClient.delete_user` が例外を投げるよう設定し、`delete_user(...)` を呼ぶ | `_rollback_delete_user` が `user.user_id` で1回呼ばれ、例外が伝播すること |

---

### TestGenerateUsersCsv

`generate_users_csv` のテスト（観点: 3.5.1 CSV生成ロジック, 3.5.2 エスケープ処理, 3.5.3 エンコーディング処理）

| No | テスト観点 | 操作手順 | 予想結果 |
| -- | ---------- | -------- | -------- |
| 70 | 3.5.1.1 CSV生成（ヘッダー行） | `generate_users_csv([])` を呼び、UTF-8 BOM付きでデコードする | `'ユーザーID'`, `'ユーザー名'`, `'メールアドレス'` がヘッダーに含まれること |
| 71 | 3.5.1.3 CSV生成（0件→ヘッダーのみ） | `generate_users_csv([])` を呼び、UTF-8 BOM付きでデコードしてsplitlinesする | 空行を除いた行数が1行（ヘッダーのみ）であること |
| 72 | 3.5.1.2 CSV生成（全件データ行） | 2件のモックユーザーを渡して `generate_users_csv(users)` を呼ぶ | 空行を除いた行数が3行（ヘッダー + 2データ行）であること |
| 73 | 3.5.1.4 CSV生成（列順序） | `generate_users_csv([])` を呼び、ヘッダー行をカンマで分割する | 0列目が `'ユーザーID'`、1列目が `'ユーザー名'`、2列目が `'メールアドレス'` であること |
| 74 | 3.5.2.1 エスケープ（カンマ） | `user_name='テスト,ユーザー'` のモックユーザーで `generate_users_csv([user])` を呼ぶ | 出力に `'"テスト,ユーザー"'` が含まれること |
| 75 | 3.5.2.2 エスケープ（改行） | `user_name='テスト\nユーザー'` のモックユーザーで `generate_users_csv([user])` を呼ぶ | 出力に `'"テスト\nユーザー"'` が含まれること |
| 76 | 3.5.2.3 エスケープ（ダブルクォート） | `user_name='名前"テスト"'` のモックユーザーで `generate_users_csv([user])` を呼ぶ | 出力に `'""'` が含まれること（ダブルクォートの二重エスケープ） |
| 77 | 3.5.2.4 エスケープ不要（特殊文字なし） | `user_name='テストユーザー'` のモックユーザーで `generate_users_csv([user])` を呼ぶ | 出力に `'テストユーザー'` がそのまま含まれること |
| 78 | 3.5.3.1 エンコーディング（BOM付与） | `generate_users_csv([])` を呼ぶ | 戻り値の先頭3バイトが `b'\xef\xbb\xbf'` であること |
| 79 | 3.5.3.2 エンコーディング（日本語文字） | `user_name='山田太郎'`, `organization_name='東京営業所'` のモックユーザーで `generate_users_csv([user])` を呼ぶ | UTF-8 BOM付きデコード後の出力に `'山田太郎'` と `'東京営業所'` が含まれること |

---

## test_user_form.py

### TestUserCreateForm

`UserCreateForm` のバリデーションテスト（観点: 1.1.1 必須チェック, 1.1.2 最大文字列長チェック, 1.1.5 メールアドレス形式チェック, 2.1 正常系処理）

| No | テスト観点 | 操作手順 | 予想結果 |
| -- | ---------- | -------- | -------- |
| 80 | 2.1.1 正常系：有効な入力値 | app の test_request_context 内で有効なデータ全項目を渡して `UserCreateForm` を生成し、`form.validate()` を呼ぶ | バリデーションが通ること（`True` を返すこと） |
| 81 | 1.1.1 必須チェック（user_name 空文字） | `user_name=''` で `UserCreateForm` を生成し、`form.validate()` を呼ぶ | バリデーションが失敗し、`form.errors` に `'user_name'` が含まれること |
| 82 | 1.1.2 最大文字列長チェック（user_name 超過） | `user_name='あ'*21`（21文字）で `UserCreateForm` を生成し、`form.validate()` を呼ぶ | バリデーションが失敗し、`form.errors` に `'user_name'` が含まれること |
| 83 | 1.1.2 最大文字列長チェック（user_name 上限ちょうど） | `user_name='あ'*20`（20文字）で `UserCreateForm` を生成し、`form.validate()` を呼ぶ | バリデーションが通ること |
| 84 | 1.1.1 必須チェック（email_address 空文字） | `email_address=''` で `UserCreateForm` を生成し、`form.validate()` を呼ぶ | バリデーションが失敗し、`form.errors` に `'email_address'` が含まれること |
| 85 | 1.1.5 メールアドレス形式チェック（@なし） | `email_address='not-an-email'` で `UserCreateForm` を生成し、`form.validate()` を呼ぶ | バリデーションが失敗し、`form.errors` に `'email_address'` が含まれること |
| 86 | 1.1.2 最大文字列長チェック（email_address 超過） | ローカル部244文字で合計256文字のメールアドレスで `UserCreateForm` を生成し、`form.validate()` を呼ぶ | バリデーションが失敗し、`form.errors` に `'email_address'` が含まれること |
| 87 | 1.1.2 最大文字列長チェック（email_address 上限ちょうど） | ローカル部243文字で合計254文字のメールアドレスで `UserCreateForm` を生成し、`form.validate()` を呼ぶ | バリデーションが通ること |
| 88 | 1.1.2 最大文字列長チェック（address 超過） | `address='あ'*501`（501文字）で `UserCreateForm` を生成し、`form.validate()` を呼ぶ | バリデーションが失敗し、`form.errors` に `'address'` が含まれること |
| 89 | 1.1.2 最大文字列長チェック（address 上限ちょうど） | `address='あ'*500`（500文字）で `UserCreateForm` を生成し、`form.validate()` を呼ぶ | バリデーションが通ること |
| 90 | 1.1.2 最大文字列長チェック（address 空文字・任意項目） | `address=''` で `UserCreateForm` を生成し、`form.validate()` を呼ぶ | バリデーションが通ること（address は任意項目） |
| 91 | 1.1.1 必須チェック（organization_id 未選択） | `organization_id=None` で `UserCreateForm` を生成し、`form.validate()` を呼ぶ | バリデーションが失敗し、`form.errors` に `'organization_id'` が含まれること |
| 92 | 1.1.1 必須チェック（user_type_id 未選択） | `user_type_id=None` で `UserCreateForm` を生成し、`form.validate()` を呼ぶ | バリデーションが失敗し、`form.errors` に `'user_type_id'` が含まれること |
| 93 | 1.1.1 必須チェック（region_id 未選択） | `region_id=None` で `UserCreateForm` を生成し、`form.validate()` を呼ぶ | バリデーションが失敗し、`form.errors` に `'region_id'` が含まれること |
| 94 | 1.1.1 必須チェック（status 未選択） | `status=None` で `UserCreateForm` を生成し、`form.validate()` を呼ぶ | バリデーションが失敗し、`form.errors` に `'status'` が含まれること |

---

### TestUserUpdateForm

`UserUpdateForm` のバリデーションテスト（観点: 1.1.1 必須チェック, 1.1.2 最大文字列長チェック, 2.1 正常系処理）

| No | テスト観点 | 操作手順 | 予想結果 |
| -- | ---------- | -------- | -------- |
| 95 | 2.1.1 正常系：有効な入力値 | app の test_request_context 内で有効なデータ全項目を渡して `UserUpdateForm` を生成し、`form.validate()` を呼ぶ | バリデーションが通ること（`True` を返すこと） |
| 96 | 1.1.1 必須チェック（user_name 空文字） | `user_name=''` で `UserUpdateForm` を生成し、`form.validate()` を呼ぶ | バリデーションが失敗し、`form.errors` に `'user_name'` が含まれること |
| 97 | 1.1.2 最大文字列長チェック（user_name 超過） | `user_name='あ'*21`（21文字）で `UserUpdateForm` を生成し、`form.validate()` を呼ぶ | バリデーションが失敗し、`form.errors` に `'user_name'` が含まれること |
| 98 | 1.1.2 最大文字列長チェック（user_name 上限ちょうど） | `user_name='あ'*20`（20文字）で `UserUpdateForm` を生成し、`form.validate()` を呼ぶ | バリデーションが通ること |
| 99 | 1.1.2 最大文字列長チェック（address 超過） | `address='あ'*501`（501文字）で `UserUpdateForm` を生成し、`form.validate()` を呼ぶ | バリデーションが失敗し、`form.errors` に `'address'` が含まれること |
| 100 | 1.1.2 最大文字列長チェック（address 上限ちょうど） | `address='あ'*500`（500文字）で `UserUpdateForm` を生成し、`form.validate()` を呼ぶ | バリデーションが通ること |
| 101 | 1.1.2 最大文字列長チェック（address 空文字・任意項目） | `address=''` で `UserUpdateForm` を生成し、`form.validate()` を呼ぶ | バリデーションが通ること（address は任意項目） |
| 102 | 1.1.1 必須チェック（region_id 未選択） | `region_id=None` で `UserUpdateForm` を生成し、`form.validate()` を呼ぶ | バリデーションが失敗し、`form.errors` に `'region_id'` が含まれること |
| 103 | 1.1.1 必須チェック（status 未選択） | `status=None` で `UserUpdateForm` を生成し、`form.validate()` を呼ぶ | バリデーションが失敗し、`form.errors` に `'status'` が含まれること |

---

## test_scim_client.py

### TestScimClientCreateUser

`ScimClient.create_user` のテスト（観点: 3.2.1 登録処理呼び出し, 3.2.2 登録結果, 1.3 エラーハンドリング）

| No | テスト観点 | 操作手順 | 予想結果 |
| -- | ---------- | -------- | -------- |
| 104 | 3.2.2.1 登録結果（id返却） | `requests.post` が `{'id': 'new-scim-uid', ...}` を含むモックレスポンスを返すよう設定し、`client.create_user('test@example.com', display_name='テストユーザー')` を呼ぶ | 戻り値が `'new-scim-uid'` であること |
| 105 | 3.2.1.1 登録処理呼び出し（SCIM /Users エンドポイント） | `requests.post` のモックを設定し、`client.create_user('u@u.com', display_name='ユーザー')` を呼ぶ | `requests.post` が呼ばれ、呼び出しURLに `'Users'`（または `'users'`）が含まれること |
| 106 | 3.2.1.1 登録処理呼び出し（リクエストボディ内容） | `requests.post` のモックを設定し、`client.create_user('t@e.com', display_name='テスト名')` を呼ぶ | POSTのjsonボディに `'t@e.com'` と `'テスト名'` が含まれること |
| 107 | 1.3.1 エラーハンドリング（API 4xxエラー） | `requests.post` のレスポンスが `status_code=400`、`raise_for_status` が例外を投げるよう設定し、`client.create_user('bad@bad.com', display_name='エラー')` を呼ぶ | 例外が伝播すること |

---

### TestScimClientUpdateUser

`ScimClient.update_user` のテスト（観点: 3.3.1 更新処理呼び出し, 3.3.2 更新結果, 1.3 エラーハンドリング）

| No | テスト観点 | 操作手順 | 予想結果 |
| -- | ---------- | -------- | -------- |
| 108 | 3.3.1.1 更新処理呼び出し（SCIM /Users/{id} PATCH） | `requests.patch` のモックを設定し、`client.update_user('uid-1', display_name='更新名', status=1)` を呼ぶ | `requests.patch` が呼ばれ、呼び出しURLに `'uid-1'` が含まれること |
| 109 | 3.3.1.1 更新処理呼び出し（status=0 → active=False） | `requests.patch` のモックを設定し、`client.update_user('uid-1', display_name='名前', status=0)` を呼ぶ | PATCHのjsonボディの `Operations` 配列中 `path='active'` の操作の `value` が `False` であること |
| 110 | 1.3.1 エラーハンドリング（API 4xxエラー） | `requests.patch` のレスポンスが `status_code=404`、`raise_for_status` が例外を投げるよう設定し、`client.update_user('bad-uid', display_name='名前', status=1)` を呼ぶ | 例外が伝播すること |

---

### TestScimClientDeleteUser

`ScimClient.delete_user` のテスト（観点: 3.4.1 削除処理呼び出し, 3.4.2 削除結果, 1.3 エラーハンドリング）

| No | テスト観点 | 操作手順 | 予想結果 |
| -- | ---------- | -------- | -------- |
| 111 | 3.4.1.1 削除処理呼び出し（SCIM /Users/{id} DELETE） | `requests.delete` のモックを設定し、`client.delete_user('uid-to-delete')` を呼ぶ | `requests.delete` が呼ばれること |
| 112 | 3.4.2.2 削除結果（URLにuser_id含む） | `requests.delete` のモックを設定し、`client.delete_user('target-uid-999')` を呼ぶ | DELETEの呼び出しURLに `'target-uid-999'` が含まれること |
| 113 | 1.3.1 エラーハンドリング（API 4xxエラー） | `requests.delete` のレスポンスが `status_code=404`、`raise_for_status` が例外を投げるよう設定し、`client.delete_user('nonexistent-uid')` を呼ぶ | 例外が伝播すること |

---

### TestScimClientAddUserToGroup

`ScimClient.add_user_to_group` のテスト（観点: 3.2.1 登録処理呼び出し, 1.3 エラーハンドリング）

| No | テスト観点 | 操作手順 | 予想結果 |
| -- | ---------- | -------- | -------- |
| 114 | 3.2.1.1 登録処理呼び出し（SCIM /Groups/{id} PATCH） | `requests.patch` のモックを設定し、`client.add_user_to_group('group-gid', 'user-uid')` を呼ぶ | `requests.patch` が呼ばれ、呼び出しURLに `'Groups'`（または `'groups'`）が含まれること |
| 115 | 3.2.1.1 登録処理呼び出し（URLにgroup_id含む） | `requests.patch` のモックを設定し、`client.add_user_to_group('workspace-group-id', 'user-uid')` を呼ぶ | PATCHの呼び出しURLに `'workspace-group-id'` が含まれること |
| 116 | 3.2.1.1 登録処理呼び出し（ボディにuser_id含む） | `requests.patch` のモックを設定し、`client.add_user_to_group('group-gid', 'user-uid-123')` を呼ぶ | PATCHのjsonボディに `'user-uid-123'` が含まれること |
| 117 | 1.3.1 エラーハンドリング（API 4xxエラー） | `requests.patch` のレスポンスが `status_code=400`、`raise_for_status` が例外を投げるよう設定し、`client.add_user_to_group('group-gid', 'user-uid')` を呼ぶ | 例外が伝播すること |

---

## test_user.py

### TestUserModel

`User` モデルのテスト（観点: 2.1 正常系処理（カラム定義・制約・デフォルト値が設計書通りであること））

| No | テスト観点 | 操作手順 | 予想結果 |
| -- | ---------- | -------- | -------- |
| 118 | 2.1.1 正常系：テーブル名 | app_context 内で `User.__tablename__` を参照する | `'user_master'` であること |
| 119 | 2.1.1 正常系：主キー | app_context 内で `User.__table__.c.user_id.primary_key` を参照する | `True` であること |
| 120 | 2.1.1 正常系：オートインクリメント | app_context 内で `User.__table__.c.user_id.autoincrement` を参照する | `True` であること |
| 121 | 2.1.1 正常系：NOT NULL（user_name） | app_context 内で `User.__table__.c.user_name.nullable` を参照する | `False` であること |
| 122 | 2.1.1 正常系：NOT NULL（email_address） | app_context 内で `User.__table__.c.email_address.nullable` を参照する | `False` であること |
| 123 | 2.1.1 正常系：NOT NULL（databricks_user_id） | app_context 内で `User.__table__.c.databricks_user_id.nullable` を参照する | `False` であること |
| 124 | 2.1.1 正常系：デフォルト値（language_code） | app_context 内で `User.__table__.c.language_code.default.arg` を参照する | `'ja'` であること |
| 125 | 2.1.1 正常系：デフォルト値（status） | app_context 内で `User.__table__.c.status.default.arg` を参照する | `1`（有効）であること |
| 126 | 2.1.1 正常系：デフォルト値（alert_notification_flag） | app_context 内で `User.__table__.c.alert_notification_flag.default.arg` を参照する | `True` であること |
| 127 | 2.1.1 正常系：デフォルト値（system_notification_flag） | app_context 内で `User.__table__.c.system_notification_flag.default.arg` を参照する | `True` であること |
| 128 | 2.1.1 正常系：デフォルト値（delete_flag） | app_context 内で `User.__table__.c.delete_flag.default.arg` を参照する | `False`（論理削除なし）であること |

---

### TestUserTypeModel

`UserType` モデルのテスト（観点: 2.1 正常系処理（カラム定義・制約・デフォルト値が設計書通りであること））

| No | テスト観点 | 操作手順 | 予想結果 |
| -- | ---------- | -------- | -------- |
| 129 | 2.1.1 正常系：テーブル名 | app_context 内で `UserType.__tablename__` を参照する | `'user_type_master'` であること |
| 130 | 2.1.1 正常系：主キー | app_context 内で `UserType.__table__.c.user_type_id.primary_key` を参照する | `True` であること |
| 131 | 2.1.1 正常系：NOT NULL（user_type_name） | app_context 内で `UserType.__table__.c.user_type_name.nullable` を参照する | `False` であること |
| 132 | 2.1.1 正常系：デフォルト値（delete_flag） | app_context 内で `UserType.__table__.c.delete_flag.default.arg` を参照する | `False`（論理削除なし）であること |
