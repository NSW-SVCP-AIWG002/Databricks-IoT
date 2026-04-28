# テスト項目書 - ユーザー管理機能 Service層

- **対象ファイル**: `src/iot_app/services/user_service.py`
- **テストコード**: `tests/unit/services/test_user_service.py`
- **観点表**: `docs/05-testing/unit-test/unit-test-perspectives.md`
- **ワークフロー仕様書**: `docs/03-features/flask-app/users/workflow-specification.md`

**テスト総数:** 92件

---

## 対応表

テストクラスと、ワークフロー仕様書の各ワークフロー・処理フロー項目の対応を示します。

| テストクラス | テスト項目No. | 対応ワークフロー | 処理フロー項目 | エンドポイント |
|------------|:---:|--------------|-------------|-------------|
| TestGetDefaultSearchParams | 1〜4 | 初期表示 / 検索・絞り込み / 全体ソート | デフォルト検索パラメータ生成 | `GET /admin/users` |
| TestSearchUsers | 5〜18 | 初期表示 / 検索・絞り込み / 全体ソート / ページング | ユーザー一覧検索・フィルタ・ソート・ページング | `GET /admin/users`, `POST /admin/users` |
| TestGetUserFormOptions | 19〜20 | ユーザー登録（登録ボタン押下）/ ユーザー更新（更新ボタン押下） | フォームオプション取得（組織・ユーザー種別・地域・ソート項目） | `GET /admin/users/create`, `GET /admin/users/<id>/edit` |
| TestCheckEmailDuplicate | 21〜24 | ユーザー登録（登録実行） | メールアドレス重複チェック（論理削除済み除外） | `POST /admin/users/register` |
| TestInsertUnityCatalogUser | 25〜26 | ユーザー登録（登録実行） | UC INSERT（ユーザーレコード登録） | `POST /admin/users/register` |
| TestRollbackCreateUser | 27〜29 | ユーザー登録（登録実行）Saga補償 | Phase2失敗時 SCIM削除（ベストエフォート） | `POST /admin/users/register` |
| TestRollbackCreateUserUcFailure | 30〜33 | ユーザー登録（登録実行）Saga補償 | Phase3（UC INSERT）失敗時 OLTP補償UPDATE + SCIM削除 | `POST /admin/users/register` |
| TestCreateUser | 34〜44 | ユーザー登録（登録実行） | OLTP仮登録→SCIM登録→グループ追加→活性化→UC INSERT・Saga補償 | `POST /admin/users/register` |
| TestUpdateOltpUser | 45〜46 | ユーザー更新（更新実行） | OLTP ユーザーレコード更新 | `POST /admin/users/<id>/update` |
| TestUpdateUnityCatalogUser | 47〜48 | ユーザー更新（更新実行） | UC UPDATE（ユーザーレコード更新） | `POST /admin/users/<id>/update` |
| TestRollbackUpdateUser | 49〜52 | ユーザー更新（更新実行）Saga補償 | SCIM/UC失敗時 OLTP/SCIM/UC補償（ベストエフォート） | `POST /admin/users/<id>/update` |
| TestUpdateUser | 53〜58 | ユーザー更新（更新実行） | OLTP→SCIM→UC順実行・Saga補償 | `POST /admin/users/<id>/update` |
| TestGetUserByDatabricksId | 59〜62 | ユーザー参照 / ユーザー更新（更新ボタン押下）/ ユーザー削除 | ユーザー情報取得（スコープ付き・論理削除除外） | `GET /admin/users/<id>`, `GET /admin/users/<id>/edit`, `POST /admin/users/delete` |
| TestDeleteUnityCatalogUser | 63〜64 | ユーザー削除 | UC DELETE（ユーザーレコード削除） | `POST /admin/users/delete` |
| TestRollbackDeleteUser | 65〜68 | ユーザー削除 Saga補償 | UC DELETE失敗時 UC INSERT再実行（ベストエフォート） | `POST /admin/users/delete` |
| TestDeleteUser | 69〜74 | ユーザー削除 | UC DELETE→OLTP論理削除→SCIM削除・Saga補償 | `POST /admin/users/delete` |
| TestGetAllUsersForExport | 75〜80 | CSV エクスポート | 全件取得（ページングなし）・フィルタ適用 | `POST /admin/users/export` |
| TestGenerateUsersCsv | 81〜92 | CSV エクスポート | CSV生成・エスケープ・エンコーディング | `POST /admin/users/export` |

---

## ワークフロー別カバレッジ

ワークフロー仕様書の各ワークフローに対して、どのテストクラスが対応しているかを示します。

### 初期表示

| 処理フロー項目 | 対応テストクラス | テスト項目No. |
|-------------|--------------|:---:|
| デフォルト検索パラメータ生成 | TestGetDefaultSearchParams | 1〜4 |
| ユーザー一覧検索（スコープ・delete_flag） | TestSearchUsers | 5〜18 |
| ページング（limit/offset） | TestSearchUsers | 13〜14 |

### 検索・絞り込み

| 処理フロー項目 | 対応テストクラス | テスト項目No. |
|-------------|--------------|:---:|
| ユーザー名フィルタ（LIKE） | TestSearchUsers | 7 |
| IDフィルタ完全一致（user_type_id） | TestSearchUsers | 8 |
| 複数条件同時指定（AND結合） | TestSearchUsers | 9, 11 |
| フィルタなし（空条件） | TestSearchUsers | 10 |
| 全フィルター条件同時指定 | TestSearchUsers | 18 |

### 全体ソート

| 処理フロー項目 | 対応テストクラス | テスト項目No. |
|-------------|--------------|:---:|
| ソート未指定（デフォルトソート） | TestSearchUsers | 17 |
| ソート指定・昇順 | TestSearchUsers | 15 |
| ソート指定・降順 | TestSearchUsers | 16 |

### ページング

| 処理フロー項目 | 対応テストクラス | テスト項目No. |
|-------------|--------------|:---:|
| ページングオフセット計算（page × per_page） | TestSearchUsers | 13 |
| per_page が limit に渡される | TestSearchUsers | 14 |

### ユーザー登録（登録ボタン押下）

| 処理フロー項目 | 対応テストクラス | テスト項目No. |
|-------------|--------------|:---:|
| フォームオプション取得（組織・種別・地域・ソート） | TestGetUserFormOptions | 19〜20 |

### ユーザー登録（登録実行）

| 処理フロー項目 | 対応テストクラス | テスト項目No. |
|-------------|--------------|:---:|
| メールアドレス重複チェック呼び出し | TestCreateUser | 44 |
| 重複あり（True返却） | TestCheckEmailDuplicate | 21 |
| 重複なし（False返却） | TestCheckEmailDuplicate | 22 |
| 重複チェック条件（email + delete_flag=False） | TestCheckEmailDuplicate | 23〜24 |
| OLTP仮登録（delete_flag=True）・flush・commit① | TestCreateUser | 34〜35 |
| OLTP全フィールド登録 | TestCreateUser | 36 |
| SCIM ユーザー作成（email/name） | TestCreateUser | 38 |
| SCIM グループ追加 | TestCreateUser | 43 |
| OLTP 活性化（databricks_user_id・delete_flag更新）・commit② | TestCreateUser | 37 |
| UC INSERT 呼び出し（全フィールド） | TestInsertUnityCatalogUser | 25〜26 |
| Saga実行順（flush→commit→SCIM→グループ→活性化→commit→UC） | TestCreateUser | 34 |
| SCIM失敗 → _rollback_create_user・例外伝播 | TestCreateUser | 39 |
| グループ追加失敗 → _rollback_create_user・例外伝播 | TestCreateUser | 44 (No.44) |
| Phase2 commit②失敗 → _rollback_create_user・例外伝播 | TestCreateUser | 41 |
| Phase3 UC INSERT失敗 → _rollback_create_user_uc_failure・例外伝播 | TestCreateUser | 40 |
| _rollback_create_user: SCIM削除（databricks_id あり） | TestRollbackCreateUser | 27 |
| _rollback_create_user: SCIM削除スキップ（databricks_id なし） | TestRollbackCreateUser | 28 |
| _rollback_create_user: SCIM例外抑制（ベストエフォート） | TestRollbackCreateUser | 29 |
| _rollback_create_user_uc_failure: OLTP補償UPDATE | TestRollbackCreateUserUcFailure | 30 |
| _rollback_create_user_uc_failure: SCIM削除 | TestRollbackCreateUserUcFailure | 31 |
| _rollback_create_user_uc_failure: OLTP例外抑制 | TestRollbackCreateUserUcFailure | 32 |
| _rollback_create_user_uc_failure: SCIM例外抑制 | TestRollbackCreateUserUcFailure | 33 |

### ユーザー更新（更新ボタン押下）

| 処理フロー項目 | 対応テストクラス | テスト項目No. |
|-------------|--------------|:---:|
| フォームオプション取得 | TestGetUserFormOptions | 19〜20 |
| ユーザー情報取得（スコープ付き） | TestGetUserByDatabricksId | 59〜62 |

### ユーザー更新（更新実行）

| 処理フロー項目 | 対応テストクラス | テスト項目No. |
|-------------|--------------|:---:|
| OLTP 全フィールド更新 | TestUpdateOltpUser | 45 |
| OLTP 対象user_id | TestUpdateOltpUser | 46 |
| UC UPDATE 呼び出し（全フィールド） | TestUpdateUnityCatalogUser | 47〜48 |
| Saga実行順（OLTP→SCIM→UC） | TestUpdateUser | 54 |
| commit | TestUpdateUser | 53 |
| 重複チェック非呼び出し（email更新不可） | TestUpdateUser | 58 |
| SCIM失敗 → _rollback_update_user・例外伝播 | TestUpdateUser | 55 |
| UC失敗 → _rollback_update_user・例外伝播 | TestUpdateUser | 56 |
| OLTP失敗 → rollback非呼び出し・例外伝播 | TestUpdateUser | 57 |
| _rollback_update_user: OLTP/SCIM/UC補償 | TestRollbackUpdateUser | 49 |
| _rollback_update_user: 全フィールド補償 | TestRollbackUpdateUser | 50 |
| _rollback_update_user: OLTPユーザー不在→OLTPコミットなし | TestRollbackUpdateUser | 51 |
| _rollback_update_user: 例外抑制（ベストエフォート） | TestRollbackUpdateUser | 52 |

### ユーザー参照

| 処理フロー項目 | 対応テストクラス | テスト項目No. |
|-------------|--------------|:---:|
| ユーザー情報取得（存在あり） | TestGetUserByDatabricksId | 59 |
| ユーザー情報取得（存在なし → None） | TestGetUserByDatabricksId | 60 |
| 論理削除済み除外（delete_flag=False） | TestGetUserByDatabricksId | 61 |
| スコープ制限（UserMasterByUser） | TestGetUserByDatabricksId | 62 |

### ユーザー削除

| 処理フロー項目 | 対応テストクラス | テスト項目No. |
|-------------|--------------|:---:|
| ユーザー情報取得（スコープ付き） | TestGetUserByDatabricksId | 59〜62 |
| UC DELETE 呼び出し（user_id） | TestDeleteUnityCatalogUser | 63〜64 |
| OLTP 論理削除（delete_flag=True）・flush | TestDeleteUser | 70 |
| SCIM 削除 | TestDeleteUser | 69 |
| Saga実行順（UC→OLTP→SCIM） | TestDeleteUser | 71 |
| commit | TestDeleteUser | 69 |
| UC失敗 → rollback不要（uc_deleted=False） | TestDeleteUser | 72 |
| OLTP flush失敗 → UCロールバック・例外伝播 | TestDeleteUser | 73 |
| SCIM失敗 → UCロールバック・例外伝播 | TestDeleteUser | 74 |
| _rollback_delete_user: UC再INSERT | TestRollbackDeleteUser | 65 |
| _rollback_delete_user: 全フィールド再INSERT | TestRollbackDeleteUser | 66 |
| _rollback_delete_user: 元データなし→何もしない | TestRollbackDeleteUser | 67 |
| _rollback_delete_user: 例外抑制（ベストエフォート） | TestRollbackDeleteUser | 68 |

### CSV エクスポート

| 処理フロー項目 | 対応テストクラス | テスト項目No. |
|-------------|--------------|:---:|
| 全件取得（ページングなし） | TestGetAllUsersForExport | 75 |
| 検索フィルタ適用（user_name） | TestGetAllUsersForExport | 78 |
| 全フィルター条件同時適用 | TestGetAllUsersForExport | 80 |
| フィルタなし（空条件） | TestGetAllUsersForExport | 79 |
| 論理削除済み除外 | TestGetAllUsersForExport | 77 |
| 空結果 | TestGetAllUsersForExport | 76 |
| ヘッダー行（全8列） | TestGenerateUsersCsv | 81 |
| 0件→ヘッダーのみ | TestGenerateUsersCsv | 82 |
| 全件データ行 | TestGenerateUsersCsv | 83 |
| 列順序 | TestGenerateUsersCsv | 84 |
| カンマエスケープ | TestGenerateUsersCsv | 85 |
| 改行エスケープ | TestGenerateUsersCsv | 86 |
| ダブルクォートエスケープ | TestGenerateUsersCsv | 87 |
| エスケープ不要（特殊文字なし） | TestGenerateUsersCsv | 88 |
| UTF-8 BOM付与 | TestGenerateUsersCsv | 89 |
| 日本語文字 | TestGenerateUsersCsv | 90 |
| None→空欄 | TestGenerateUsersCsv | 91 |
| 全8列値 | TestGenerateUsersCsv | 92 |

---

## テストクラス一覧

テストクラスに対して、テスト観点、操作手順、予想結果を示します。

### TestGetDefaultSearchParams

`get_default_search_params()` はユーザー検索のデフォルトパラメータ（ページ番号・ソート条件・各検索条件の初期値）を返す。

| No | テスト観点 | 操作手順 | 予想結果 |
| -- | ---------- | -------- | -------- |
| 1 | 2.1.1 正常系：デフォルトページング | `get_default_search_params()` を呼ぶ | `page` が `1`、`per_page` が `ITEM_PER_PAGE` であること |
| 2 | 3.1.2.1 検索条件未指定デフォルト（空文字） | `get_default_search_params()` を呼ぶ | `user_name` と `email_address` のデフォルト値が空文字 `''` であること |
| 3 | 3.1.2.1 検索条件未指定デフォルト（None） | `get_default_search_params()` を呼ぶ | `user_type_id`, `organization_id`, `region_id`, `status` のデフォルト値が `None` であること |
| 4 | 2.1.1 正常系：デフォルトソート順 | `get_default_search_params()` を呼ぶ | `sort_by` が `'user_name'`、`order` が `'asc'` であること |

---

### TestSearchUsers

`search_users()` はスコープ制限付きでユーザーを検索し、検索条件・ページング・ソートを適用してリストと総件数を返す。

| No | テスト観点 | 操作手順 | 予想結果 |
| -- | ---------- | -------- | -------- |
| 5 | 3.1.4.1 戻り値ハンドリング（正常系） | `db.session.query()` がユーザー2件・total=2 を返すモックを設定し、全条件Noneのparamsで `search_users(params, user_id=1)` を呼ぶ | 戻り値が長さ2のタプルであること |
| 6 | 3.1.4.2 戻り値ハンドリング（空結果） | `db.session.query()` が空リスト・total=0 を返すモックを設定し、`search_users(params, user_id=1)` を呼ぶ | 戻り値の users が空リスト、total が `0` であること |
| 7 | 3.1.1.1 検索条件指定（テキスト部分一致） | `user_name='田中'` を含む params で `search_users(params, user_id=1)` を呼ぶ | `mock_query.filter` が呼ばれ、フィルタ条件文字列に `'%田中%'` が含まれること（部分一致） |
| 8 | 3.1.1.1 検索条件指定（IDフィルタ完全一致） | `user_type_id=2` を含む params で `search_users(params, user_id=1)` を呼ぶ | `mock_query.filter` が呼ばれ、フィルタ条件文字列に `'user_type_id'` と `'2'` が含まれること（完全一致） |
| 9 | 3.1.1.2 複数条件指定 | `user_name='田中'`, `email_address='@example'` を含む params で `search_users(params, user_id=1)` を呼ぶ | `mock_query.filter` が2回以上呼ばれ、フィルタ条件文字列に `'%田中%'` と `'%@example%'` が含まれること |
| 10 | 3.1.1.3 未指定条件は除外 | 全フィルター条件がNoneのparamsで `search_users(params, user_id=1)` を呼ぶ | 追加フィルタ（`mock_query.filter`）が0回であること |
| 11 | 3.1.1.5 AND結合（OR未使用） | `user_name='田中'`, `email_address='@example'`, `user_type_id=2` の params で `search_users(params, user_id=1)` を呼ぶ | `mock_query.filter` が2回以上呼ばれること（OR結合でなくAND連鎖） |
| 12 | 3.1.1.4 スコープ制限（login_user_id） | `user_id=99` で `search_users(params, user_id=99)` を呼ぶ | `db.session.query` が `UserMasterByUser` を引数として1回呼ばれること |
| 13 | 3.1.3.1 ページングオフセット計算 | `page=3, per_page=20` の params で `search_users(params, user_id=1)` を呼ぶ | `mock_query.limit().offset` が `40` で呼ばれること |
| 14 | 3.1.3.1 per_page が limit に渡される | `per_page=10` の params で `search_users(params, user_id=1)` を呼ぶ | `mock_query.limit` が `10` で1回呼ばれること |
| 15 | 3.1.1.1 検索条件指定（ソート昇順） | `sort_by='user_name', order='asc'` の params で `search_users(params, user_id=1)` を呼ぶ | `mock_query.order_by` が呼ばれ、`.asc()` が適用されること |
| 16 | 3.1.1.1 検索条件指定（ソート降順） | `sort_by='user_name', order='desc'` の params で `search_users(params, user_id=1)` を呼ぶ | `mock_query.order_by` が呼ばれ、`.desc()` が適用されること |
| 17 | 3.1.2.1 検索条件未指定（ソート未指定） | `sort_by='', order=''` の params で `search_users(params, user_id=1)` を呼ぶ | `mock_query.order_by` が呼ばれること（デフォルトソート） |
| 18 | 3.1.1.2 全フィルター条件同時指定 | `user_name='田中'`, `email_address='@example'`, `user_type_id=2`, `organization_id=1`, `region_id=2`, `status=1` を含む params で `search_users(params, user_id=1)` を呼ぶ | `mock_query.filter` が6回以上呼ばれ、フィルタ条件文字列に `'%田中%'`, `'%@example%'`, `'user_type_id'`, `'organization_id'`, `'region_id'`, `'status'` が含まれること |

---

### TestGetUserFormOptions

`get_user_form_options()` はユーザー登録・更新フォームに必要な選択肢（組織・ユーザー種別・地域・ソート項目）を取得する。ログインユーザーより下位のロールのみを選択肢として返す。

| No | テスト観点 | 操作手順 | 予想結果 |
| -- | ---------- | -------- | -------- |
| 19 | 2.1.1 / 3.1.4.1 正常系：4タプル返却 | `db.session.query()` が空リストを返すモックを設定し、`get_user_form_options(user_id=1, login_user_type_id=2)` を呼ぶ | 戻り値が長さ4のタプル（organizations, user_types, regions, sort_items）であること |
| 20 | 3.1.1.1 検索条件指定（下位ロールのみ） | `db.session.query()` が空リストを返すモックを設定し、`get_user_form_options(user_id=1, login_user_type_id=2)` を呼ぶ | `db.session.query().filter` が呼ばれること（UserType に対して user_type_id > 2 のフィルタ） |

---

### TestCheckEmailDuplicate

`check_email_duplicate()` はメールアドレスの重複を確認し、登録済みなら `True`、未登録なら `False` を返す。論理削除済みユーザーは重複対象外とする。

| No | テスト観点 | 操作手順 | 予想結果 |
| -- | ---------- | -------- | -------- |
| 21 | 3.1.4.1 検索結果戻り値（存在あり） | `User.query.filter_by().first()` が MagicMock を返すよう設定し、`check_email_duplicate('dup@example.com')` を呼ぶ | 戻り値が `True` であること |
| 22 | 3.1.4.2 検索結果戻り値（存在なし） | `User.query.filter_by().first()` が `None` を返すよう設定し、`check_email_duplicate('new@example.com')` を呼ぶ | 戻り値が `False` であること |
| 23 | 3.1.1.1 検索条件指定（email_address） | `User.query.filter_by().first()` が `None` を返すよう設定し、`check_email_duplicate('test@example.com')` を呼ぶ | `filter_by` が `email_address='test@example.com', delete_flag=False` で1回呼ばれること |
| 24 | 2.2.3 論理削除済み除外 | `User.query.filter_by().first()` が `None` を返すよう設定し、`check_email_duplicate('any@example.com')` を呼ぶ | `filter_by` の引数に `delete_flag=False` が含まれること |

---

### TestInsertUnityCatalogUser

`_insert_unity_catalog_user()` はUnity CatalogのOLTP DBテーブルへユーザーレコードをINSERTするプライベート関数。ユーザー登録Sagaの一ステップとして呼ばれる。

| No | テスト観点 | 操作手順 | 予想結果 |
| -- | ---------- | -------- | -------- |
| 25 | 3.2.1.1 登録処理呼び出し（1回） | `UnityCatalogConnector` をモック化し、`_insert_unity_catalog_user(user_id=1, databricks_user_id='uid-1', user_data={...}, creator_id=99)` を呼ぶ | `mock_conn.execute_dml` が1回呼ばれること |
| 26 | 3.2.1.1 登録処理呼び出し（全フィールド含む） | `UnityCatalogConnector` をモック化し、`_insert_unity_catalog_user(user_id=42, databricks_user_id='uid-42', user_data={...}, creator_id=10)` を呼ぶ | `execute_dml` のパラメータに全登録対象フィールド（直接引数：`user_id`, `databricks_user_id`, `creator_id`、user_data写し：`user_name`, `organization_id`, `email_address`, `user_type_id`, `region_id`, `address`, `status`, `alert_notification_flag`, `system_notification_flag`）が含まれること |

---

### TestRollbackCreateUser

`_rollback_create_user()` はPhase2失敗時の補償処理で、Databricks削除をベストエフォートで実行する。OLTP は `db.session.rollback()` で自動巻き戻し済み（Phase1コミット済みの仮登録レコードは残存）。

| No | テスト観点 | 操作手順 | 予想結果 |
| -- | ---------- | -------- | -------- |
| 27 | 2.3.2 副作用チェック（SCIM 削除実行） | `ScimClient` をモック化し、`_rollback_create_user(user_id=None, databricks_user_id='uid-1')` を呼ぶ | `mock_scim.delete_user` が `'uid-1'` で1回呼ばれること |
| 28 | 2.3.2 副作用チェック（SCIM 削除スキップ） | `ScimClient` をモック化し、`_rollback_create_user(user_id=None, databricks_user_id=None)` を呼ぶ | `mock_scim.delete_user` が呼ばれないこと |
| 29 | 1.3.1 エラーハンドリング（SCIM例外抑制） | `ScimClient.delete_user` が例外を投げるよう設定し、`_rollback_create_user(user_id=None, databricks_user_id='uid-1')` を呼ぶ | 例外が re-raise されないこと（ベストエフォート） |

---

### TestRollbackCreateUserUcFailure

`_rollback_create_user_uc_failure()` はPhase3（UC INSERT）失敗時の補償処理。OLTPは既にコミット済みのため補償UPDATEで仮登録状態に戻し、その後Databricksユーザーを削除する。

| No | テスト観点 | 操作手順 | 予想結果 |
| -- | ---------- | -------- | -------- |
| 30 | 2.3.2 副作用チェック（OLTP補償UPDATE） | `db`, `User`, `ScimClient` をモック化し、`_rollback_create_user_uc_failure(user_id=5, databricks_user_id='uid-1')` を呼ぶ | `mock_user_obj.delete_flag` が `True` に、`mock_user_obj.databricks_user_id` が `''` に設定され、`db.session.commit` が1回呼ばれること |
| 31 | 2.3.2 副作用チェック（SCIM 削除実行） | `db`, `User`, `ScimClient` をモック化し、`_rollback_create_user_uc_failure(user_id=5, databricks_user_id='uid-1')` を呼ぶ | `mock_scim.delete_user` が `'uid-1'` で1回呼ばれること |
| 32 | 1.3.1 エラーハンドリング（OLTP例外抑制） | `db.session.commit` が例外を投げるよう設定し、`_rollback_create_user_uc_failure(user_id=5, databricks_user_id='uid-1')` を呼ぶ | 例外が re-raise されないこと（ベストエフォート） |
| 33 | 1.3.1 エラーハンドリング（SCIM例外抑制） | `ScimClient.delete_user` が例外を投げるよう設定し、`_rollback_create_user_uc_failure(user_id=5, databricks_user_id='uid-1')` を呼ぶ | 例外が re-raise されないこと（ベストエフォート） |

---

### TestCreateUser

`create_user()` は3フェーズのSagaオーケストレーター。Phase1: OLTP仮登録→commit①、Phase2: Databricks登録→OLTP本登録→commit②、Phase3: UC INSERT。各フェーズの失敗時に対応する補償処理を実行し例外を伝播する。

| No | テスト観点 | 操作手順 | 予想結果 |
| -- | ---------- | -------- | -------- |
| 34 | 3.2.1.1 / 2.1.1 登録処理呼び出し（Saga実行順） | call_order リストで各ステップの呼び出し順を記録し、`create_user(form_data, creator_id=1, auth_provider=...)` を呼ぶ | 呼び出し順が `['flush', 'commit', 'scim_create', 'add_to_group', 'flush', 'commit', 'uc']` であること（①OLTP flush → commit① → ②SCIM create → ③グループ追加 → ④活性化 flush → commit② → ⑤UC INSERT） |
| 35 | 3.2.1.1 登録処理呼び出し（仮登録ステップ） | `User` のコンストラクタを記録するよう設定し、`create_user(form_data, creator_id=1, auth_provider=...)` を呼ぶ | `User()` 生成時の引数に `delete_flag=True` が含まれること（仮登録状態）かつ `db.session.add` が1回呼ばれること |
| 36 | 3.2.1.1 登録処理呼び出し（User コンストラクタ引数・全件） | `User` のコンストラクタを記録するよう設定し、`create_user(form_data, creator_id=1, auth_provider=...)` を呼ぶ | `User()` 生成時に全登録対象項目（固定値・user_data写し・creator_id写し）がコンストラクタ引数に含まれること（delete_flag は No.35 でカバー） |
| 37 | 3.2.1.1 登録処理呼び出し（活性化 databricks_user_id・delete_flag更新） | `User` モックが `delete_flag=True` 状態で返るよう設定し、`create_user(form_data, creator_id=1, auth_provider=...)` を呼ぶ | 活性化ステップで `mock_user_obj.databricks_user_id` が `'new-uid'` に、`mock_user_obj.delete_flag` が `False` に更新されること |
| 38 | 3.2.1.1 登録処理呼び出し（SCIM email・name） | `ScimClient` をモック化し、`create_user(form_data, creator_id=1, auth_provider=...)` を呼ぶ | `mock_scim.create_user` が `email=form_data['email_address'], display_name=form_data['user_name']` で1回呼ばれること |
| 39 | 2.3.2 / 1.3.1 副作用チェック（SCIM失敗→rollback・例外伝播） | `ScimClient.create_user` が例外を投げるよう設定し、`create_user(...)` を呼ぶ | `_rollback_create_user` が1回呼ばれ、例外が伝播すること |
| 40 | 2.3.2 / 1.3.1 副作用チェック（Phase3 UC INSERT失敗→rollback_uc_failure・例外伝播） | `_insert_unity_catalog_user` が例外を投げるよう設定し、`create_user(...)` を呼ぶ | `_rollback_create_user_uc_failure` が1回呼ばれ、例外が伝播すること |
| 41 | 2.3.2 / 1.3.1 副作用チェック（Phase2 commit②失敗→rollback・例外伝播） | `db.session.commit` が2回目の呼び出し時のみ例外を投げるよう設定し、`create_user(...)` を呼ぶ | `_rollback_create_user` が1回呼ばれ、例外が伝播すること |
| 42 | 3.2.1.1 登録処理呼び出し（グループ追加） | `ScimClient.create_user` が `'new-uid'` を返すよう設定し、`create_user(form_data, creator_id=1, auth_provider=...)` を呼ぶ | `mock_scim.add_user_to_group` が1回呼ばれ、位置引数に `'new-uid'` が含まれること |
| 43 | 2.3.2 / 1.3.1 副作用チェック（グループ追加失敗→rollback・例外伝播） | `ScimClient.add_user_to_group` が例外を投げるよう設定し、`create_user(...)` を呼ぶ | `_rollback_create_user` が1回呼ばれ、例外が伝播すること |
| 44 | 3.2.1.1 登録処理呼び出し（重複チェック呼び出し） | `check_email_duplicate` をモック化して `False` を返すよう設定し、`create_user(form_data, creator_id=1, auth_provider=...)` を呼ぶ | `check_email_duplicate` が `form_data['email_address']` を引数として1回呼ばれること |

---

### TestUpdateOltpUser

`_update_oltp_user()` はOLTP DB（MySQL）のユーザーレコードを更新するプライベート関数。ユーザー更新Sagaの一ステップとして呼ばれる。

| No | テスト観点 | 操作手順 | 予想結果 |
| -- | ---------- | -------- | -------- |
| 45 | 3.3.1.1 更新処理呼び出し（全更新可能フィールド） | `User.query.get` がモックユーザーを返すよう設定し、`_update_oltp_user(user_id=1, user_data={...}, modifier_id=99)` を呼ぶ | モックユーザーの全更新対象フィールドが正しく設定されること（`user_name`, `region_id`, `address`, `status`, `alert_notification_flag`, `system_notification_flag`, `modifier`） |
| 46 | 3.3.2.2 更新結果（対象user_id） | `User.query.get` がモックユーザーを返すよう設定し、`_update_oltp_user(user_id=42, user_data={...}, modifier_id=1)` を呼ぶ | `User.query.get` が `42` で1回呼ばれること |

---

### TestUpdateUnityCatalogUser

`_update_unity_catalog_user()` はUnity CatalogのOLTP DBテーブルのユーザーレコードをUPDATEするプライベート関数。ユーザー更新Sagaの一ステップとして呼ばれる。

| No | テスト観点 | 操作手順 | 予想結果 |
| -- | ---------- | -------- | -------- |
| 47 | 3.3.1.1 更新処理呼び出し（execute_dml 1回） | `UnityCatalogConnector` をモック化し、`_update_unity_catalog_user(user_id=1, user_data={...}, modifier_id=99)` を呼ぶ | `mock_conn.execute_dml` が1回呼ばれること |
| 48 | 3.3.2.2 更新結果（全フィールド含む） | `UnityCatalogConnector` をモック化し、`_update_unity_catalog_user(user_id=55, user_data={...}, modifier_id=1)` を呼ぶ | `execute_dml` のパラメータに全更新対象フィールド（`user_id`, `user_name`, `region_id`, `address`, `status`, `alert_notification_flag`, `system_notification_flag`, `modifier_id`）が含まれること |

---

### TestRollbackUpdateUser

`_rollback_update_user()` はユーザー更新Sagaの補償処理。`original_data` を受け取り、OLTP補償コミット・SCIM復元・UC復元を独立した3ステップでベストエフォート実行する。

| No | テスト観点 | 操作手順 | 予想結果 |
| -- | ---------- | -------- | -------- |
| 49 | 2.3.2 副作用チェック（OLTP/SCIM/UC補償） | `User.query.get` がモックユーザーを返し、`db`, `ScimClient`, `UnityCatalogConnector` をモック化して `_rollback_update_user(databricks_user_id='uid-1', user_id=1, original_data={...})` を呼ぶ | `db.session.commit`・`mock_scim.update_user`・`mock_conn.execute_dml` がそれぞれ1回呼ばれること |
| 50 | 2.3.2 副作用チェック（全フィールド補償） | `original_data` に具体値をセットし、`_rollback_update_user(databricks_user_id='uid-1', user_id=10, original_data=original_data)` を呼ぶ | OLTP の各フィールドが `original_data` の値にセットされ、SCIM `update_user` が `('uid-1', '元の名前', 0)` で呼ばれ、UC execute_dml の params に全補償対象フィールド（`user_id`, `user_name`, `region_id`, `address`, `status`, `alert_notification_flag`, `system_notification_flag`, `modifier`）が含まれること |
| 51 | 2.3.2 副作用チェック（OLTPユーザー不在→OLTPコミットなし・SCIM/UCは補償） | `User.query.get` が `None` を返すよう設定し、`_rollback_update_user(databricks_user_id='uid-1', user_id=999, original_data={...})` を呼ぶ | `db.session.commit` が呼ばれず、`mock_scim.update_user` が1回呼ばれること |
| 52 | 1.3.1 エラーハンドリング（ロールバック例外抑制） | `db.session.commit` が例外を投げるよう設定し、`_rollback_update_user(databricks_user_id='uid-1', user_id=1, original_data={...})` を呼ぶ | 例外が re-raise されないこと（ベストエフォート） |

---

### TestUpdateUser

`update_user()` はOLTP更新・SCIM更新・UC更新の順に実行するSagaオーケストレーター。OLTP失敗時はdb.session.rollbackのみで例外を伝播（SCIM/UCは未実行）、SCIM/UC失敗時は `_rollback_update_user(original_data)` でOLTP/SCIM/UCを補償し例外を伝播する。メールアドレスは更新不可項目のため重複チェックは行わない。

| No | テスト観点 | 操作手順 | 予想結果 |
| -- | ---------- | -------- | -------- |
| 53 | 2.1.1 / 3.3.2.1 正常系：commit | `db`, `User`, `ScimClient`, `_update_oltp_user`, `_update_unity_catalog_user` をモック化し、`update_user(user_id=1, databricks_user_id='uid-1', user_data={...}, modifier_id=1)` を呼ぶ | `db.session.commit` が1回呼ばれること |
| 54 | 3.3.1.1 更新処理呼び出し（Saga実行順） | call_order リストを使い各ステップの呼び出し順を記録し、`update_user(...)` を呼ぶ | 呼び出し順が `['oltp', 'scim', 'uc']` であること（①OLTP UPDATE → ②SCIM update → ③UC UPDATE） |
| 55 | 2.3.2 / 1.3.1 副作用チェック（SCIM失敗→rollback・例外伝播） | `User`, `_update_oltp_user` をモック化し、`ScimClient.update_user` が例外を投げるよう設定して `update_user(...)` を呼ぶ | `_rollback_update_user` が1回呼ばれ、例外が伝播すること |
| 56 | 2.3.2 / 1.3.1 副作用チェック（UC失敗→rollback・例外伝播） | `User`, `_update_oltp_user` をモック化し、`_update_unity_catalog_user` が例外を投げるよう設定して `update_user(...)` を呼ぶ | `_rollback_update_user` が1回呼ばれ、例外が伝播すること |
| 57 | 2.3.2 / 1.3.1 副作用チェック（OLTP失敗→rollback非呼び出し・例外伝播） | `User`, `_update_unity_catalog_user` をモック化し、`_update_oltp_user` が例外を投げるよう設定して `update_user(...)` を呼ぶ | `_rollback_update_user` が呼ばれず、例外が伝播すること（SCIM/UCは未実行のため補償不要） |
| 58 | 2.3.2 副作用チェック（重複チェック非呼び出し） | `check_email_duplicate` をモック化し、`update_user(user_id=1, databricks_user_id='uid-1', user_data={...}, modifier_id=1)` を呼ぶ | `check_email_duplicate` が呼ばれないこと（email は更新不可項目のため） |

---

### TestGetUserByDatabricksId

`get_user_by_databricks_id()` はDatabricksユーザーIDでユーザーを取得する。スコープ制限・論理削除除外が適用される。

| No | テスト観点 | 操作手順 | 予想結果 |
| -- | ---------- | -------- | -------- |
| 59 | 2.2.1 対象IDが存在する場合 | `db.session.query().filter().first()` が MagicMock を返すよう設定し、`get_user_by_databricks_id('uid-1', login_user_id=1)` を呼ぶ | 戻り値がモックユーザーオブジェクトであること |
| 60 | 2.2.2 対象IDが存在しない場合 | `db.session.query().filter().first()` が `None` を返すよう設定し、`get_user_by_databricks_id('nonexistent', login_user_id=1)` を呼ぶ | 戻り値が `None` であること |
| 61 | 2.2.3 論理削除済み除外 | `db.session.query().filter().first()` が `None` を返すよう設定し、`get_user_by_databricks_id('uid-1', login_user_id=1)` を呼ぶ | `db.session.query().filter` が1回呼ばれること（delete_flag フィルタを含む） |
| 62 | 3.1.1.1 検索条件指定（スコープ制限） | `login_user_id=42` で `get_user_by_databricks_id('uid-1', login_user_id=42)` を呼ぶ | `db.session.query` が `UserMasterByUser` を引数として1回呼ばれること |

---

### TestDeleteUnityCatalogUser

`_delete_unity_catalog_user()` はUnity CatalogのOLTP DBテーブルからユーザーレコードをDELETEするプライベート関数。ユーザー削除Sagaの一ステップとして呼ばれる。

| No | テスト観点 | 操作手順 | 予想結果 |
| -- | ---------- | -------- | -------- |
| 63 | 3.4.1.1 削除処理呼び出し（execute_dml 1回） | `UnityCatalogConnector` をモック化し、`_delete_unity_catalog_user(user_id=5)` を呼ぶ | `mock_conn.execute_dml` が1回呼ばれること |
| 64 | 3.4.1.1 削除処理呼び出し（user_id パラメータ） | `UnityCatalogConnector` をモック化し、`_delete_unity_catalog_user(user_id=77)` を呼ぶ | `execute_dml` のパラメータに `user_id=77` が含まれること |

---

### TestRollbackDeleteUser

`_rollback_delete_user()` はユーザー削除Sagaの補償処理で、UCへのINSERT再実行をベストエフォートで行う。例外が発生しても握りつぶして続行する。

| No | テスト観点 | 操作手順 | 予想結果 |
| -- | ---------- | -------- | -------- |
| 65 | 2.3.2 副作用チェック（UC再INSERT） | `User.query.get` がモックユーザーを返し、`UnityCatalogConnector` をモック化して `_rollback_delete_user(user_id=1)` を呼ぶ | `mock_conn.execute_dml` が1回呼ばれること |
| 66 | 2.3.2 副作用チェック（全フィールド含む） | `mock_original` に全フィールドの具体値をセットし、`_rollback_delete_user(user_id=1)` を呼ぶ | `execute_dml` のパラメータに全復元対象フィールド（`user_id`, `databricks_user_id`, `user_name`, `organization_id`, `email_address`, `user_type_id`, `language_code`, `region_id`, `address`, `status`, `alert_notification_flag`, `system_notification_flag`, `create_date`, `creator`, `modifier`）が含まれること |
| 67 | 2.3.2 副作用チェック（元データなし→何もしない） | `User.query.get` が `None` を返すよう設定し、`_rollback_delete_user(user_id=999)` を呼ぶ | `mock_conn.execute_dml` が呼ばれないこと |
| 68 | 1.3.1 エラーハンドリング（ロールバック例外抑制） | `UnityCatalogConnector.execute_dml` が例外を投げるよう設定し、`_rollback_delete_user(user_id=1)` を呼ぶ | 例外が re-raise されないこと（ベストエフォート） |

---

### TestDeleteUser

`delete_user()` はUC削除・OLTP論理削除・SCIM削除の順に実行するSagaオーケストレーター。OLTP flush失敗またはSCIM削除失敗時にUCロールバックを実行し、例外を伝播する。

| No | テスト観点 | 操作手順 | 予想結果 |
| -- | ---------- | -------- | -------- |
| 69 | 2.1.1 / 3.4.2.1 正常系：commit | `db`, `ScimClient`, `_delete_unity_catalog_user` をモック化し、`delete_user(user=user_mock, deleter_id=99)` を呼ぶ | `db.session.commit` が1回呼ばれること |
| 70 | 3.4.1.1 削除処理呼び出し（OLTP論理削除） | `db`, `ScimClient`, `_delete_unity_catalog_user` をモック化し、`delete_user(user=user_mock, deleter_id=99)` を呼ぶ | `user.delete_flag` が `True` に設定されること |
| 71 | 3.4.1.1 削除処理呼び出し（Saga実行順） | call_order リストを使い各ステップの呼び出し順を記録し、`delete_user(user=user_mock, deleter_id=99)` を呼ぶ | 呼び出し順が `['uc', 'oltp', 'scim']` であること（①UC DELETE → ②OLTP flush → ③SCIM delete） |
| 72 | 2.3.2 副作用チェック（UC失敗→rollback不要） | `_delete_unity_catalog_user` が例外を投げるよう設定し、`delete_user(...)` を呼ぶ | `_rollback_delete_user` が呼ばれないこと（uc_deleted=False のため） |
| 73 | 2.3.2 / 1.3.1 副作用チェック（OLTP flush失敗→UCロールバック・例外伝播） | `db.session.flush` が例外を投げるよう設定し、`delete_user(...)` を呼ぶ | `_rollback_delete_user` が `user.user_id` で1回呼ばれ、例外が伝播すること |
| 74 | 2.3.2 / 1.3.1 副作用チェック（SCIM失敗→UCロールバック・例外伝播） | `ScimClient.delete_user` が例外を投げるよう設定し、`delete_user(...)` を呼ぶ | `_rollback_delete_user` が `user.user_id` で1回呼ばれ、例外が伝播すること |

---

### TestGetAllUsersForExport

`get_all_users_for_export()` はCSVエクスポート用に全対象ユーザーをスコープ制限・検索条件付きで取得する。ページングなしで全件返す。

| No | テスト観点 | 操作手順 | 予想結果 |
| -- | ---------- | -------- | -------- |
| 75 | 3.1.4.1 戻り値ハンドリング（正常系） | モックが2件のユーザーリストを返すよう設定し、全条件Noneのparamsで `get_all_users_for_export(params, user_id=1)` を呼ぶ | 戻り値がモックユーザーのリストであること |
| 76 | 3.1.4.2 戻り値ハンドリング（空結果） | モックが空リストを返すよう設定し、`get_all_users_for_export(params, user_id=1)` を呼ぶ | 戻り値が空リストであること |
| 77 | 2.2.3 論理削除済み除外 | `db.session.query().filter()` が空リストを返すよう設定し、`get_all_users_for_export(params, user_id=1)` を呼ぶ | `db.session.query().filter` が1回呼ばれること（delete_flag=False フィルタ） |
| 78 | 3.1.1.1 検索条件指定（user_name） | `user_name='田中'` を含む params で `get_all_users_for_export(params, user_id=1)` を呼ぶ | `mock_q.filter` が呼ばれること |
| 79 | 3.1.1.3 未指定条件は除外 | 全フィルター条件がNoneのparamsで `get_all_users_for_export(params, user_id=1)` を呼ぶ | 追加フィルタ（`mock_q.filter`）が0回であること |
| 80 | 3.1.1.2 全フィルター条件同時指定 | `user_name='田中'`, `email_address='@example'`, `user_type_id=2`, `organization_id=1`, `region_id=2`, `status=1` を含む params で `get_all_users_for_export(params, user_id=1)` を呼ぶ | `mock_q.filter` が6回以上呼ばれ、フィルタ条件文字列に `'%田中%'`, `'%@example%'`, `'user_type_id'`, `'organization_id'`, `'region_id'`, `'status'` が含まれること |

---

### TestGenerateUsersCsv

`generate_users_csv()` はユーザーリストからCSV形式のバイト列（UTF-8 BOM付き）を生成する。カンマ・改行・ダブルクォートのエスケープ処理を含む。

| No | テスト観点 | 操作手順 | 予想結果 |
| -- | ---------- | -------- | -------- |
| 81 | 3.5.1.1 CSV生成（ヘッダー行） | `generate_users_csv([])` を呼び、UTF-8 BOM付きでデコードする | 全8列（`'ユーザーID', 'ユーザー名', 'メールアドレス', '所属組織ID', '所属組織名', 'ユーザー種別', '地域', '住所'`）がヘッダーに含まれること |
| 82 | 3.5.1.3 CSV生成（0件→ヘッダーのみ） | `generate_users_csv([])` を呼び、UTF-8 BOM付きでデコードしてsplitlinesする | 空行を除いた行数が1行（ヘッダーのみ）であること |
| 83 | 3.5.1.2 CSV生成（全件データ行） | 2件のモックユーザーを渡して `generate_users_csv(users)` を呼ぶ | 空行を除いた行数が3行（ヘッダー + 2データ行）であること |
| 84 | 3.5.1.4 CSV生成（列順序） | `generate_users_csv([])` を呼び、ヘッダー行をカンマで分割する | 0列目が `'ユーザーID'`、1列目が `'ユーザー名'`、2列目が `'メールアドレス'`、3列目が `'所属組織ID'`、4列目が `'所属組織名'`、5列目が `'ユーザー種別'`、6列目が `'地域'`、7列目が `'住所'` であること |
| 85 | 3.5.2.1 エスケープ（カンマ） | `user_name='テスト,ユーザー'` のモックユーザーで `generate_users_csv([user])` を呼ぶ | 出力に `'"テスト,ユーザー"'` が含まれること |
| 86 | 3.5.2.2 エスケープ（改行） | `user_name='テスト\nユーザー'` のモックユーザーで `generate_users_csv([user])` を呼ぶ | 出力に `'"テスト\nユーザー"'` が含まれること |
| 87 | 3.5.2.3 エスケープ（ダブルクォート） | `user_name='名前"テスト"'` のモックユーザーで `generate_users_csv([user])` を呼ぶ | 出力に `'""'` が含まれること（ダブルクォートの二重エスケープ） |
| 88 | 3.5.2.4 エスケープ不要（特殊文字なし） | `user_name='テストユーザー'` のモックユーザーで `generate_users_csv([user])` を呼ぶ | 出力に `'テストユーザー'` がそのまま含まれること |
| 89 | 3.5.3.1 エンコーディング（BOM付与） | `generate_users_csv([])` を呼ぶ | 戻り値の先頭3バイトが `b'\xef\xbb\xbf'` であること |
| 90 | 3.5.3.2 エンコーディング（日本語文字） | `user_name='山田太郎'`, `organization_name='東京営業所'` のモックユーザーで `generate_users_csv([user])` を呼ぶ | UTF-8 BOM付きデコード後の出力に `'山田太郎'` と `'東京営業所'` が含まれること |
| 91 | 3.5.1.5 CSV生成（None→空欄） | `_make_user()` で生成したユーザーの `organization` を `None` にセットして `generate_users_csv([user])` を呼ぶ | CSVデータ行の4列目（0-indexed）（所属組織名）が空文字であること |
| 92 | 3.5.1.7 CSV生成（全8列値） | `user_id=10`, `user_name='山田太郎'`, `email='yamada@example.com'`, `user_type_name='販社ユーザー'`, `org_id=5`, `org_name='東京営業所'`, `region_name='関東'`, `address='東京都渋谷区1-2-3'` のユーザーで `generate_users_csv([user])` を呼ぶ | `rows[1][0]`〜`rows[1][7]` が `'10'`, `'山田太郎'`, `'yamada@example.com'`, `'5'`, `'東京営業所'`, `'販社ユーザー'`, `'関東'`, `'東京都渋谷区1-2-3'` であること |
