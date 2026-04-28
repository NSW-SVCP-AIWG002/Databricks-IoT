# テスト項目書 - device-inventory

- **対象ファイル**: `src/iot_app/services/device_inventory_service.py`
- **テストコード**: `/workspaces/Databricks-IoT/tests/unit/services/test_device_inventory_service.py`
- **観点表**: `docs/05-testing/unit-test/unit-test-perspectives.md`
- **ワークフロー仕様書**: `/workspaces/Databricks-IoT/docs/03-features/flask-app/device-inventory/workflow-specification.md`

---

## 対応表

テストクラスと、ワークフロー仕様書の各ワークフロー・処理フロー項目の対応を示します。

| テストクラス | テスト項目No. | 対応ワークフロー | 処理フロー項目 | エンドポイント |
|---|:---:|---|---|---|
| TestGetDefaultSearchParams | 1〜11 | 初期表示 | デフォルト検索パラメータ生成 | `GET /admin/device-inventory` |
| TestGetDeviceInventoryFormOptions | 12〜18 | 初期表示・デバイス台帳登録・デバイス台帳更新 | フォーム用マスタデータ取得 | `GET /admin/device-inventory`, `GET /admin/device-inventory/create`, `GET /admin/device-inventory/<uuid>/edit` |
| TestSearchDeviceInventories | 19〜34 | 初期表示・検索・絞り込み・ソート・ページング | デバイス台帳検索 | `GET /admin/device-inventory`, `POST /admin/device-inventory` |
| TestGetOrganizationOptions | 35〜38 | デバイス台帳登録・デバイス台帳更新 | 組織選択肢取得 | `GET /admin/device-inventory/create`, `GET /admin/device-inventory/<uuid>/edit` |
| TestCreateDeviceInventory | 39〜47 | デバイス台帳登録 | 登録実行 | `POST /admin/device-inventory/create` |
| TestUpdateDeviceInventory | 48〜55 | デバイス台帳更新 | 更新実行 | `POST /admin/device-inventory/<uuid>/update` |
| TestCheckLinkedDeviceMaster | 56〜59 | デバイス台帳削除 | 削除対象デバイスマスタ確認 | `POST /admin/device-inventory/delete` |
| TestDeleteDeviceInventories | 60〜66 | デバイス台帳削除 | 削除実行 | `POST /admin/device-inventory/delete` |
| TestExportDeviceInventoriesCsv | 67〜75 | CSVエクスポート | CSVデータ生成 | `POST /admin/device-inventory/export` |

---

## ワークフロー別カバレッジ

ワークフロー仕様書の各ワークフローに対して、どのテストクラスが対応しているかを示します。

### 初期表示

| 処理フロー項目 | 対応テストクラス | テスト項目No. |
|---|---|:---:|
| デフォルト検索パラメータ生成 | TestGetDefaultSearchParams | 1〜11 |
| フォーム用マスタデータ取得 | TestGetDeviceInventoryFormOptions | 12〜18 |
| デバイス台帳検索 | TestSearchDeviceInventories | 19〜34 |

### 検索・絞り込み

| 処理フロー項目 | 対応テストクラス | テスト項目No. |
|---|---|:---:|
| デバイス台帳検索（検索条件適用） | TestSearchDeviceInventories | 19〜34 |

### ソート

| 処理フロー項目 | 対応テストクラス | テスト項目No. |
|---|---|:---:|
| デバイス台帳検索（ソート条件適用） | TestSearchDeviceInventories | 19〜34 |

### ページング

| 処理フロー項目 | 対応テストクラス | テスト項目No. |
|---|---|:---:|
| デバイス台帳検索（ページング） | TestSearchDeviceInventories | 19〜34 |

### デバイス台帳登録

| 処理フロー項目 | 対応テストクラス | テスト項目No. |
|---|---|:---:|
| フォーム用マスタデータ取得 | TestGetDeviceInventoryFormOptions | 12〜18 |
| 組織選択肢取得 | TestGetOrganizationOptions | 35〜38 |
| 登録実行 | TestCreateDeviceInventory | 39〜47 |

### デバイス台帳更新

| 処理フロー項目 | 対応テストクラス | テスト項目No. |
|---|---|:---:|
| フォーム用マスタデータ取得 | TestGetDeviceInventoryFormOptions | 12〜18 |
| 組織選択肢取得 | TestGetOrganizationOptions | 35〜38 |
| 更新実行 | TestUpdateDeviceInventory | 48〜55 |

### デバイス台帳削除

| 処理フロー項目 | 対応テストクラス | テスト項目No. |
|---|---|:---:|
| 削除対象デバイスマスタ確認 | TestCheckLinkedDeviceMaster | 56〜59 |
| 削除実行 | TestDeleteDeviceInventories | 60〜66 |

### CSVエクスポート

| 処理フロー項目 | 対応テストクラス | テスト項目No. |
|---|---|:---:|
| CSVデータ生成 | TestExportDeviceInventoriesCsv | 67〜75 |

---

## テストクラス一覧

テストクラスに対して、テスト観点、操作手順、予想結果を示します。

---

### TestGetDefaultSearchParams

| No | テスト観点 | 操作手順 | 予想結果 |
|---|---|---|---|
| 1 | 2.1.1 正常系処理：有効な入力データで正常終了 | `get_default_search_params()` を引数なしで呼び出す | 戻り値の `page` キーの値が `1` であること |
| 2 | 2.1.1 正常系処理：有効な入力データで正常終了 | `get_default_search_params()` を引数なしで呼び出す | 戻り値の `per_page` キーの値が `25` であること |
| 3 | 2.1.1 正常系処理：有効な入力データで正常終了 | `get_default_search_params()` を引数なしで呼び出す | 戻り値の `device_uuid` キーの値が空文字（`''`）であること |
| 4 | 2.1.1 正常系処理：有効な入力データで正常終了 | `get_default_search_params()` を引数なしで呼び出す | 戻り値の `device_name` キーの値が空文字（`''`）であること |
| 5 | 2.1.1 正常系処理：有効な入力データで正常終了 | `get_default_search_params()` を引数なしで呼び出す | 戻り値の `device_type_id` キーの値が `-1`（すべて選択）であること |
| 6 | 2.1.1 正常系処理：有効な入力データで正常終了 | `get_default_search_params()` を引数なしで呼び出す | 戻り値の `inventory_status_id` キーの値が `-1`（すべて選択）であること |
| 7 | 2.1.1 正常系処理：有効な入力データで正常終了 | `get_default_search_params()` を引数なしで呼び出す | 戻り値の `inventory_location` キーの値が空文字（`''`）であること |
| 8 | 2.1.1 正常系処理：有効な入力データで正常終了 | `get_default_search_params()` を引数なしで呼び出す | 戻り値の `purchase_date_from` キーの値が `None` であること |
| 9 | 2.1.1 正常系処理：有効な入力データで正常終了 | `get_default_search_params()` を引数なしで呼び出す | 戻り値の `purchase_date_to` キーの値が `None` であること |
| 10 | 2.1.1 正常系処理：有効な入力データで正常終了 | `get_default_search_params()` を引数なしで呼び出す | 戻り値の `sort_item_id` キーの値が `-1`（未選択）であること |
| 11 | 2.1.1 正常系処理：有効な入力データで正常終了 | `get_default_search_params()` を引数なしで呼び出す | 戻り値の `sort_order` キーの値が `-1`（未選択）であること |

---

### TestGetDeviceInventoryFormOptions

| No | テスト観点 | 操作手順 | 予想結果 |
|---|---|---|---|
| 12 | 3.1.4.1 正常系：Repositoryがリストを返却した場合、返却されたリストがそのまま返却される | `DeviceTypeMaster`・`InventoryStatusMaster`・`SortItemMaster` をMock化し（各 `.all()` は空リストを返す）、`get_device_inventory_form_options()` を呼び出す | 戻り値がタプルであり、要素数が3であること |
| 13 | 2.1.1 正常系処理：有効な入力データで正常終了 | `DeviceTypeMaster`・`InventoryStatusMaster`・`SortItemMaster` をMock化し（各 `.all()` は空リストを返す）、`get_device_inventory_form_options()` を呼び出す | `DeviceTypeMaster.query.filter_by(delete_flag=False)` が呼ばれること |
| 14 | 2.1.1 正常系処理：有効な入力データで正常終了 | `DeviceTypeMaster`・`InventoryStatusMaster`・`SortItemMaster` をMock化し（各 `.all()` は空リストを返す）、`get_device_inventory_form_options()` を呼び出す | `InventoryStatusMaster.query.filter_by(delete_flag=False)` が呼ばれること |
| 15 | 2.1.1 正常系処理：有効な入力データで正常終了 | `DeviceTypeMaster`・`InventoryStatusMaster`・`SortItemMaster` をMock化し（各 `.all()` は空リストを返す）、`get_device_inventory_form_options()` を呼び出す | `SortItemMaster.query.filter()` が呼ばれること（`view_id` と `delete_flag` によるフィルタ） |
| 16 | 2.1.1 正常系処理：有効な入力データで正常終了 | `DeviceTypeMaster`・`InventoryStatusMaster`・`SortItemMaster` をMock化し（各 `.all()` は空リストを返す）、`get_device_inventory_form_options()` を呼び出す | `SortItemMaster.query.filter().order_by()` が呼ばれること（`sort_order` 昇順） |
| 17 | 3.1.4.1 正常系：Repositoryがリストを返却した場合、返却されたリストがそのまま返却される | `DeviceTypeMaster`（2件）・`InventoryStatusMaster`（1件）・`SortItemMaster`（3件）の各Mockデータを設定し、`get_device_inventory_form_options()` を呼び出す | 戻り値 `(device_types, inventory_statuses, sort_items)` が各Mockデータと完全一致すること |
| 18 | 3.1.4.2 空結果：Repositoryが空リストを返却した場合、空リストが返却される | `DeviceTypeMaster`・`InventoryStatusMaster`・`SortItemMaster` をMock化し（各 `.all()` は空リストを返す）、`get_device_inventory_form_options()` を呼び出す | `device_types`・`inventory_statuses`・`sort_items` がいずれも空リストであること |

---

### TestSearchDeviceInventories

| No | テスト観点 | 操作手順 | 予想結果 |
|---|---|---|---|
| 19 | 3.1.1.1 条件指定：検索条件を指定した場合、指定した条件がRepositoryに渡される | `DeviceInventoryMaster`（クエリチェーンMock）・`SortItemMaster`（`filter_by().first()=None`）をMock化し、`device_uuid='DEV-001'` を含む検索パラメータで `search_device_inventories(params)` を呼び出す | `filter` が1回以上呼ばれ、フィルタ文字列に `'DEV-001%'` が含まれ、`'%DEV-001%'` は含まれないこと（前方一致検索） |
| 20 | 3.1.1.2 条件指定：複数条件を指定した場合、全条件が欠落なく渡される | `DeviceInventoryMaster`・`SortItemMaster`（`filter_by().first()=None`）をMock化し、`device_name='センサー'` を含む検索パラメータで `search_device_inventories(params)` を呼び出す | `filter` が1回以上呼ばれ、フィルタ文字列に `'%センサー%'` が含まれること（部分一致検索） |
| 21 | 3.1.1.1 条件指定：検索条件を指定した場合、指定した条件がRepositoryに渡される | `DeviceInventoryMaster`・`SortItemMaster`（`filter_by().first()=None`）をMock化し、`inventory_location='倉庫A'` を含む検索パラメータで `search_device_inventories(params)` を呼び出す | `filter` が1回以上呼ばれ、フィルタ文字列に `'%倉庫A%'` が含まれること（部分一致検索） |
| 22 | 3.1.1.1 条件指定：検索条件を指定した場合、指定した条件がRepositoryに渡される | `DeviceInventoryMaster`・`SortItemMaster`（`filter_by().first()=None`）をMock化し、`device_uuid='VALID'`・`device_name='ゲート'`・`inventory_location='5階'` を含む検索パラメータで `search_device_inventories(params)` を呼び出す | `filter` が3回以上呼ばれ、フィルタ文字列に `'VALID%'` が含まれ、`'%VALID%'` は含まれないこと（device_uuidは前方一致） |
| 23 | 3.1.1.1 条件指定：検索条件を指定した場合、指定した条件がRepositoryに渡される | `DeviceInventoryMaster`・`SortItemMaster`（`filter_by().first()=None`）をMock化し、`device_type_id=1`・`sort_item_id=1`・`sort_order=1` を含む検索パラメータで `search_device_inventories(params)` を呼び出す | `filter` が1回以上呼ばれること |
| 24 | 3.1.1.2 条件指定：複数条件を指定した場合、全条件が欠落なく渡される | `DeviceInventoryMaster`・`SortItemMaster`（`filter_by().first()=None`）をMock化し、`purchase_date_from=date(2025,1,1)`・`purchase_date_to=date(2025,12,31)` を含む検索パラメータで `search_device_inventories(params)` を呼び出す | `filter` が1回以上呼ばれること |
| 25 | 3.1.2.1 条件未指定：検索条件なしの場合、condition=NoneでRepositoryが呼ばれる | `DeviceInventoryMaster`（`count()=0`・`offset().all()=[]`）・`SortItemMaster`（`filter_by().first()=None`）をMock化し、デフォルト検索パラメータで `search_device_inventories(params)` を呼び出す | 戻り値がリスト型と整数型のタプル `(list, int)` で返却されること |
| 26 | 3.1.3.1 件数制御：設定値ありの場合、設定値がRepositoryに渡される | `DeviceInventoryMaster`（`all()` が2件のMockリストを返す・`count()=2`）・`SortItemMaster`（`filter_by().first()=None`）をMock化し、`per_page=-1` を指定した検索パラメータで `search_device_inventories(params)` を呼び出す | `q.limit` が呼ばれず（全件取得）、戻り値の `inventories` がMockリストと一致すること |
| 27 | 3.1.3.1 件数制御：設定値ありの場合、設定値がRepositoryに渡される | `DeviceInventoryMaster`（`count()=1`・`offset().all()` が1件のMockリスト）・`SortItemMaster`（`filter_by().first()=None`）をMock化し、`page=2`・`per_page=25` を指定した検索パラメータで `search_device_inventories(params)` を呼び出す | `q.limit` と `q.offset` がそれぞれ呼ばれること |
| 28 | 3.1.4.1 正常系：Repositoryがリストを返却した場合、返却されたリストがそのまま返却される | `DeviceInventoryMaster`（`count()=3`・`offset().all()` が3件のMockリスト）・`SortItemMaster`（`filter_by().first()=None`）をMock化し、デフォルト検索パラメータで `search_device_inventories(params)` を呼び出す | 戻り値がタプルで要素数が2であり、`total` が `3` であること |
| 29 | 3.1.4.2 空結果：Repositoryが空リストを返却した場合、空リストが返却される | `DeviceInventoryMaster`（`count()=0`・`offset().all()=[]`）・`SortItemMaster`（`filter_by().first()=None`）をMock化し、デフォルト検索パラメータで `search_device_inventories(params)` を呼び出す | `total` が `0`、`inventories` が空リストであること |
| 30 | 3.1.2.1 条件未指定：検索条件なしの場合、condition=NoneでRepositoryが呼ばれる | `DeviceInventoryMaster`・`SortItemMaster`（`filter_by().first()=None`）をMock化し、`device_type_id=-1` を指定した検索パラメータで `search_device_inventories(params)` を呼び出す | `SortItemMaster.query.filter_by` が呼ばれないこと（`sort_item_id=-1` のためソートスキップ） |
| 31 | 3.1.2.1 条件未指定：検索条件なしの場合、condition=NoneでRepositoryが呼ばれる | `DeviceInventoryMaster`・`SortItemMaster`（`filter_by().first()=None`）をMock化し、`inventory_status_id=-1` を指定した検索パラメータで `search_device_inventories(params)` を呼び出す | `SortItemMaster.query.filter_by` が呼ばれないこと（`sort_item_id=-1` のためソートスキップ） |
| 32 | 3.1.1.1 条件指定：検索条件を指定した場合、指定した条件がRepositoryに渡される | `DeviceInventoryMaster`・`SortItemMaster`（`filter_by().first()=None`）をMock化し、`sort_item_id=-1`・`sort_order=-1` を指定した検索パラメータで `search_device_inventories(params)` を呼び出す | `SortItemMaster.query.filter_by` が呼ばれず（ソートスキップ）、`order_by` はデフォルトソートとして呼ばれること |
| 33 | 3.1.1.1 条件指定：検索条件を指定した場合、指定した条件がRepositoryに渡される | `DeviceInventoryMaster`・`SortItemMaster`（`filter_by().first()` が `sort_item_name='inventory_location'` のMockを返す）をMock化し、`sort_item_id=9`・`sort_order=1`（昇順）を指定した検索パラメータで `search_device_inventories(params)` を呼び出す | `SortItemMaster.query.filter_by` が呼ばれ、`mock_inventory_attr.asc()` が使われること（昇順ソート適用） |
| 34 | 3.1.1.1 条件指定：検索条件を指定した場合、指定した条件がRepositoryに渡される | `DeviceInventoryMaster`・`SortItemMaster`（`filter_by().first()` が `sort_item_name='inventory_location'` のMockを返す）をMock化し、`sort_item_id=9`・`sort_order=2`（降順）を指定した検索パラメータで `search_device_inventories(params)` を呼び出す | `SortItemMaster.query.filter_by` が呼ばれ、`mock_inventory_attr.desc()` が使われること（降順ソート適用） |

---

### TestGetOrganizationOptions

| No | テスト観点 | 操作手順 | 予想結果 |
|---|---|---|---|
| 35 | 2.1.1 正常系処理：有効な入力データで正常終了 | `OrganizationMaster`（`filter_by().order_by().all()=[]`）をMock化し、`get_organization_options()` を呼び出す | `OrganizationMaster.query.filter_by(delete_flag=False)` が呼ばれること |
| 36 | 2.1.1 正常系処理：有効な入力データで正常終了 | `OrganizationMaster`（`filter_by().order_by().all()=[]`）をMock化し、`get_organization_options()` を呼び出す | `OrganizationMaster.query.filter_by().order_by()` が呼ばれること（`organization_name` 昇順） |
| 37 | 3.1.4.1 正常系：Repositoryがリストを返却した場合、返却されたリストがそのまま返却される | `OrganizationMaster`（`filter_by().order_by().all()` が2件のMockリストを返す）をMock化し、`get_organization_options()` を呼び出す | 戻り値がMockリストと完全一致すること |
| 38 | 3.1.4.2 空結果：Repositoryが空リストを返却した場合、空リストが返却される | `OrganizationMaster`（`filter_by().order_by().all()=[]`）をMock化し、`get_organization_options()` を呼び出す | 戻り値が空リストであること |

---

### TestCreateDeviceInventory

| No | テスト観点 | 操作手順 | 予想結果 |
|---|---|---|---|
| 39 | 2.1.1 / 3.2.1.1 正常系処理：有効な入力値で登録内容がRepositoryに渡される | `DeviceInventoryMaster`（`device_inventory_id=100`）・`DeviceMaster`（`device_id=200`）・`db`・`UnityCatalogConnector` をMock化し、`make_valid_form_data()` のデータで `create_device_inventory(form_data, creator_id=1)` を呼び出す | `db.session.add()` が2回以上（デバイス台帳マスタ・デバイスマスタへの登録）呼ばれ、`db.session.flush()` が呼ばれること |
| 40 | 2.1.1 / 3.2.2.1 正常系処理：Repositoryからのレスポンスを正常に受け取ること | `DeviceInventoryMaster`（`device_inventory_id=100`）・`DeviceMaster`（`device_id=200`）・`db`・`UnityCatalogConnector` をMock化し、有効なフォームデータで `create_device_inventory(form_data, creator_id=1)` を呼び出す | `db.session.commit()` が1回だけ呼ばれること |
| 41 | 3.2.1.1 登録処理呼び出し：正常な入力値で登録内容がRepositoryに渡される | `DeviceInventoryMaster`（`device_inventory_id=100`）・`DeviceMaster`（`device_id=200`）・`db`・`UnityCatalogConnector` をMock化し、有効なフォームデータで `create_device_inventory(form_data, creator_id=1)` を呼び出す | `UnityCatalogConnector().execute_dml()` が1回呼ばれ、渡されたSQLに `'INSERT INTO iot_catalog.oltp_db.device_master'` が含まれること |
| 42 | 2.3.2 副作用チェック：例外発生時にrollback()が呼び出される | `DeviceInventoryMaster`・`DeviceMaster`・`db`（`session.flush()` が `Exception` を送出）・`UnityCatalogConnector` をMock化し、有効なフォームデータで `create_device_inventory(form_data, creator_id=1)` を呼び出す | `Exception` が送出され、`db.session.rollback()` が呼ばれること |
| 43 | 1.3.1 エラーハンドリング：例外が握りつぶされず上位へ伝播される | `DeviceInventoryMaster`・`db`（`session.flush()` が `RuntimeError` を送出）・`UnityCatalogConnector` をMock化し、有効なフォームデータで `create_device_inventory(form_data, creator_id=1)` を呼び出す | `RuntimeError` が上位へ伝播されること |
| 44 | 1.3.1 エラーハンドリング：例外が握りつぶされず上位へ伝播される | `DeviceInventoryMaster`（`device_inventory_id=100`）・`DeviceMaster`（`device_id=200`）・`db`・`UnityCatalogConnector`（`execute_dml` の1回目が `Exception` を送出し2回目は成功）をMock化し、有効なフォームデータで `create_device_inventory(form_data, creator_id=1)` を呼び出す | `Exception` が送出され、`execute_dml` が2回呼ばれ、2回目のSQLに `'DELETE FROM iot_catalog.oltp_db.device_master'` が含まれること（補償DELETE実行） |
| 45 | 2.3.2 副作用チェック：例外発生時にrollback()が呼び出される | `DeviceInventoryMaster`（`device_inventory_id=100`）・`DeviceMaster`（`device_id=200`）・`db`・`UnityCatalogConnector`（`execute_dml` の1回目が `Exception` を送出し2回目は成功）をMock化し、有効なフォームデータで `create_device_inventory(form_data, creator_id=1)` を呼び出す | `Exception` が送出され、`db.session.rollback()` が呼ばれること |
| 46 | 3.2.1.1 登録処理呼び出し：正常な入力値で登録内容がRepositoryに渡される | `uuid` モジュールを `uuid4()` が `'generated-uuid'` を返すようにMock化し、`DeviceInventoryMaster`（`device_inventory_id=100`）・`DeviceMaster`（`device_id=200`）・`db`・`UnityCatalogConnector` をMock化し、有効なフォームデータで `create_device_inventory(form_data, creator_id=1)` を呼び出す | `uuid.uuid4()` が呼ばれること（UUID自動生成） |
| 47 | 3.2.1.1 登録処理呼び出し：正常な入力値で登録内容がRepositoryに渡される | `DeviceInventoryMaster`（`side_effect` でコンストラクタ引数をキャプチャ）・`DeviceMaster`（`device_id=200`）・`db`・`UnityCatalogConnector` をMock化し、`creator_id=42` を指定して `create_device_inventory(form_data, creator_id=42)` を呼び出す | `DeviceInventoryMaster` のコンストラクタに渡された `creator` と `modifier` がいずれも `42` であること |

---

### TestUpdateDeviceInventory

| No | テスト観点 | 操作手順 | 予想結果 |
|---|---|---|---|
| 48 | 2.1.1 / 3.3.1.1 正常系処理：有効な入力値で更新内容がRepositoryに渡される | `DeviceInventoryMaster`（`filter_by().first_or_404()` がMockオブジェクトを返す）・`DeviceMaster`（`filter_by().first_or_404()` がMockオブジェクトを返す）・`db`・`UnityCatalogConnector` をMock化し、`inventory_location='新倉庫B'`・`purchase_date=date(2025,6,1)` を含むフォームデータで `update_device_inventory('test-uuid', form_data, modifier_id=1)` を呼び出す | `mock_inventory.inventory_location` が `'新倉庫B'`、`mock_inventory.purchase_date` が `date(2025,6,1)` に更新されること |
| 49 | 3.3.1.1 更新処理呼び出し：正常な入力値で更新内容がRepositoryに渡される | `DeviceInventoryMaster`・`DeviceMaster`・`db`・`UnityCatalogConnector` をMock化し、`device_name='新センサーX'`・`device_type_id=2` を含むフォームデータで `update_device_inventory('test-uuid', form_data, modifier_id=1)` を呼び出す | `mock_device.device_name` が `'新センサーX'`、`mock_device.device_type_id` が `2` に更新されること |
| 50 | 3.3.2.2 更新結果：指定したIDがRepositoryに渡される | `DeviceInventoryMaster`・`DeviceMaster`・`db`・`UnityCatalogConnector` をMock化し、有効なフォームデータで `update_device_inventory('test-uuid', form_data, modifier_id=99)` を呼び出す | `mock_inventory.modifier` と `mock_device.modifier` がいずれも `99` に設定されること |
| 51 | 3.3.1.1 更新処理呼び出し：正常な入力値で更新内容がRepositoryに渡される | `DeviceInventoryMaster`・`DeviceMaster`・`db`・`UnityCatalogConnector` をMock化し、有効なフォームデータで `update_device_inventory('test-uuid', form_data, modifier_id=1)` を呼び出す | `UnityCatalogConnector().execute_dml()` が1回呼ばれ、渡されたSQLに `'UPDATE iot_catalog.oltp_db.device_master'` が含まれること |
| 52 | 3.3.2.1 更新結果：更新処理が成功して例外なく処理が完了する | `DeviceInventoryMaster`・`DeviceMaster`・`db`・`UnityCatalogConnector` をMock化し、有効なフォームデータで `update_device_inventory('test-uuid', form_data, modifier_id=1)` を呼び出す | `db.session.commit()` が1回呼ばれること |
| 53 | 2.3.2 副作用チェック：例外発生時にrollback()が呼び出される | `DeviceInventoryMaster`・`DeviceMaster`・`db`（`session.flush()` が `Exception` を送出）・`UnityCatalogConnector` をMock化し、有効なフォームデータで `update_device_inventory('test-uuid', form_data, modifier_id=1)` を呼び出す | `Exception` が送出され、`db.session.rollback()` が呼ばれること |
| 54 | 1.3.1 エラーハンドリング：例外が握りつぶされず上位へ伝播される | `DeviceInventoryMaster`・`DeviceMaster`・`db`・`UnityCatalogConnector`（`execute_dml` の1回目が `Exception` を送出し2回目は成功）をMock化し、有効なフォームデータで `update_device_inventory('test-uuid', form_data, modifier_id=1)` を呼び出す | `Exception` が送出され、`execute_dml` がちょうど2回呼ばれること（UCロールバックUPDATEを含む） |
| 55 | 2.3.2 副作用チェック：例外発生時にrollback()が呼び出される | `DeviceInventoryMaster`・`DeviceMaster`・`db`・`UnityCatalogConnector`（`execute_dml` の1回目が `Exception` を送出し2回目は成功）をMock化し、有効なフォームデータで `update_device_inventory('test-uuid', form_data, modifier_id=1)` を呼び出す | `Exception` が送出され、`db.session.rollback()` が呼ばれること |

---

### TestCheckLinkedDeviceMaster

| No | テスト観点 | 操作手順 | 予想結果 |
|---|---|---|---|
| 56 | 2.1.1 正常系処理：有効な入力データで正常終了 | `DeviceInventoryMaster`（`filter().all()` が1件のMockオブジェクト `device_inventory_id=100` を返す）・`DeviceMaster`（`filter().count()=1`）をMock化し、`check_linked_device_master(['uuid-001'])` を呼び出す | `True` が返ること（紐づくデバイスマスタが存在する） |
| 57 | 2.1.1 正常系処理：有効な入力データで正常終了 | `DeviceInventoryMaster`（`filter().all()` が1件のMockオブジェクト `device_inventory_id=100` を返す）・`DeviceMaster`（`filter().count()=0`）をMock化し、`check_linked_device_master(['uuid-001'])` を呼び出す | `False` が返ること（紐づくデバイスマスタが存在しない） |
| 58 | 2.2.2 対象データ存在チェック：対象IDが存在しない | `DeviceInventoryMaster`（`filter().all()=[]`）・`DeviceMaster`（`filter().count()=0`）をMock化し、`check_linked_device_master(['nonexistent-uuid'])` を呼び出す | `False` が返ること（台帳レコードが存在しないため） |
| 59 | 2.1.3 正常系処理：最大件数内の入力で正常終了 | `DeviceInventoryMaster`（`filter().all()` が `device_inventory_id=100,200` の2件のMockオブジェクトを返す）・`DeviceMaster`（`filter().count()=1`）をMock化し、`check_linked_device_master(['uuid-001', 'uuid-002'])` を呼び出す | `True` が返ること（複数UUID指定時でも1件以上デバイスマスタが存在する） |

---

### TestDeleteDeviceInventories

| No | テスト観点 | 操作手順 | 予想結果 |
|---|---|---|---|
| 60 | 2.1.1 / 3.4.1.1 正常系処理：有効なIDで削除処理が呼び出される | `DeviceInventoryMaster`（`filter().all()` が `delete_flag=False`・`device_inventory_id=100` のMockを返す）・`db` をMock化し、`delete_device_inventories(['uuid-001'], modifier_id=1)` を呼び出す | `mock_inventory.delete_flag` が `True` に更新されること（論理削除） |
| 61 | 3.4.1.1 削除処理呼び出し：正常なIDで指定したIDがRepositoryに渡される | `DeviceInventoryMaster`（`filter().all()` が `device_inventory_id=100` のMockを返す）・`db` をMock化し、`delete_device_inventories(['uuid-001'], modifier_id=99)` を呼び出す | `mock_inventory.modifier` が `99` に設定されること |
| 62 | 3.4.2.1 削除結果：削除処理が成功して例外なく処理が完了する | `DeviceInventoryMaster`（`filter().all()` が `device_inventory_id=100` のMockを返す）・`db` をMock化し、`delete_device_inventories(['uuid-001'], modifier_id=1)` を呼び出す | `db.session.commit()` が1回呼ばれること |
| 63 | 2.2.2 対象データ存在チェック：対象IDが存在しない場合、NotFoundErrorがスローされる | `DeviceInventoryMaster`（`filter().all()=[]`）をMock化し、`delete_device_inventories(['nonexistent-uuid'], modifier_id=1)` を呼び出す | `ValueError` が送出され、エラーメッセージに `'削除対象が見つかりません'` が含まれること |
| 64 | 2.2.2 対象データ存在チェック：対象IDが存在しない場合、NotFoundErrorがスローされる | `DeviceInventoryMaster`（`filter().all()=[]`）をMock化し、空リストを指定して `delete_device_inventories([], modifier_id=1)` を呼び出す | `ValueError` が送出されること |
| 65 | 2.3.2 副作用チェック：例外発生時にrollback()が呼び出される | `DeviceInventoryMaster`（`filter().all()` が `device_inventory_id=100` のMockを返す）・`db`（`session.flush()` が `Exception` を送出）をMock化し、`delete_device_inventories(['uuid-001'], modifier_id=1)` を呼び出す | `Exception` が送出され、`db.session.rollback()` が呼ばれること |
| 66 | 2.1.3 正常系処理：最大件数内の入力で正常終了 | `DeviceInventoryMaster`（`filter().all()` が `delete_flag=False` の2件のMockオブジェクトを返す）・`db` をMock化し、`delete_device_inventories(['uuid-001', 'uuid-002'], modifier_id=1)` を呼び出す | `inv1.delete_flag` と `inv2.delete_flag` がいずれも `True` に更新されること |

---

### TestExportDeviceInventoriesCsv

| No | テスト観点 | 操作手順 | 予想結果 |
|---|---|---|---|
| 67 | 3.1.3.1 件数制御：設定値ありの場合、設定値がRepositoryに渡される | `search_device_inventories` を `([], 0)` を返すようにMock化し、デフォルト検索パラメータで `export_device_inventories_csv(params)` を呼び出す | `search_device_inventories` に渡された `per_page` が `-1` であること（全件取得） |
| 68 | 3.1.1.1 条件指定：検索条件を指定した場合、指定した条件がRepositoryに渡される | `search_device_inventories` を `([], 0)` を返すようにMock化し、`page=3` を含む検索パラメータで `export_device_inventories_csv(params)` を呼び出す | `search_device_inventories` に渡された `page` が `1` であること（ページングを無効化） |
| 69 | 3.5.1.1 ヘッダー行出力：定義された列名がヘッダー行に出力される | `search_device_inventories` を `([], 0)` を返すようにMock化し、デフォルト検索パラメータで `export_device_inventories_csv(params)` を呼び出し、UTF-8 BOM付きでデコードする | デコードした文字列に `'操作列'`・`'在庫状況'`・`'モデル情報'`・`'デバイス名'`・`'デバイス種別'`・`'SIMID'`・`'MACアドレス'`・`'購入日'`・`'出荷予定日'`・`'出荷日'`・`'メーカー保証終了日'`・`'在庫場所'` がすべて含まれること |
| 70 | 3.5.1.3 0件出力：空リストを渡した場合、ヘッダー行のみ出力される | `search_device_inventories` を `([], 0)` を返すようにMock化し、デフォルト検索パラメータで `export_device_inventories_csv(params)` を呼び出し、UTF-8 BOM付きでデコードする | 出力行が1行（ヘッダー行のみ）であること |
| 71 | 3.5.1.2 データ行出力：複数件のデータリストを渡した場合、全件がCSV行として出力される | `search_device_inventories` を `([inv1, inv2], 2)` を返すようにMock化（`inv1.device.device_name='センサーA'`・`inv2.device.device_name='センサーB'`）し、デフォルト検索パラメータで `export_device_inventories_csv(params)` を呼び出す | 出力行が3行（ヘッダー行 + 2件分のデータ行）であること |
| 72 | 3.5.1.4 列順序：定義された列順序で出力される | `search_device_inventories` を `([], 0)` を返すようにMock化し、デフォルト検索パラメータで `export_device_inventories_csv(params)` を呼び出し、CSVヘッダー行のカラム名リストを取得する | カラム順序が `['操作列', 'デバイス名', 'デバイス種別', 'モデル情報', 'SIMID', 'MACアドレス', '在庫状況', '購入日', '出荷予定日', '出荷日', 'メーカー保証終了日', '在庫場所']` と完全一致すること |
| 73 | 3.5.3.1 UTF-8 BOM付き：CSV生成実行後、先頭にBOMが付与される | `search_device_inventories` を `([], 0)` を返すようにMock化し、デフォルト検索パラメータで `export_device_inventories_csv(params)` を呼び出す | 戻り値がバイト列の場合は先頭3バイトが `b'\xef\xbb\xbf'`（UTF-8 BOM）であること ※要確認（実装によって戻り値の型が変わる可能性あり） |
| 74 | 3.5.1.2 データ行出力：複数件のデータリストを渡した場合、全件がCSV行として出力される | `search_device_inventories` を `([inv], 1)` を返すようにMock化（`inv.purchase_date=date(2025,3,15)`）し、デフォルト検索パラメータで `export_device_inventories_csv(params)` を呼び出す | デコードした文字列に `'2025/03/15'` が含まれること（スラッシュ区切りの日付形式） |
| 75 | 3.5.1.2 データ行出力：複数件のデータリストを渡した場合、全件がCSV行として出力される | `search_device_inventories` を `([inv], 1)` を返すようにMock化（`inv.estimated_ship_date=None`・`inv.ship_date=None`）し、デフォルト検索パラメータで `export_device_inventories_csv(params)` を呼び出し、データ行を取得する | データ行に空フィールド（連続カンマまたは空ダブルクォート）が存在すること（出荷予定日・出荷日が空文字で出力） |
