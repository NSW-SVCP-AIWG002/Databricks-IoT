# テスト項目書 - device-inventory

- **対象ファイル**: `src/iot_app/models/device_inventory.py`
- **テストコード**: `/workspaces/Databricks-IoT/tests/unit/models/test_device_inventory_model.py`
- **観点表**: `docs/05-testing/unit-test/unit-test-perspectives.md`
- **ワークフロー仕様書**: `/workspaces/Databricks-IoT/docs/03-features/flask-app/device-inventory/workflow-specification.md`

---

## 対応表

テストクラスと、ワークフロー仕様書の各ワークフロー・処理フロー項目の対応を示します。

| テストクラス | テスト項目No. | 対応ワークフロー | 処理フロー項目 | エンドポイント |
|---|:---:|---|---|---|
| TestInventoryStatusMasterDefaults | 1〜3 | 初期表示・検索・絞り込み・デバイス台帳登録・デバイス台帳更新 | 在庫状況マスタ参照 | `GET /admin/device-inventory`, `POST /admin/device-inventory`, `GET /admin/device-inventory/create`, `GET /admin/device-inventory/<uuid>/edit` |
| TestDeviceTypeMasterDefaults | 4〜6 | 初期表示・検索・絞り込み・デバイス台帳登録・デバイス台帳更新 | デバイス種別マスタ参照 | `GET /admin/device-inventory`, `POST /admin/device-inventory`, `GET /admin/device-inventory/create`, `GET /admin/device-inventory/<uuid>/edit` |
| TestDeviceInventoryMasterDefaults | 7〜11 | デバイス台帳登録・デバイス台帳更新・デバイス台帳削除 | デバイス台帳マスタのデフォルト値 | `POST /admin/device-inventory/create`, `POST /admin/device-inventory/<uuid>/update`, `POST /admin/device-inventory/delete` |
| TestDeviceInventoryMasterInit | 12〜22 | デバイス台帳登録・デバイス台帳更新 | デバイス台帳マスタのフィールド設定 | `POST /admin/device-inventory/create`, `POST /admin/device-inventory/<uuid>/update` |
| TestDeviceMasterDefaults | 23〜27 | デバイス台帳登録・デバイス台帳更新 | デバイスマスタのフィールド設定 | `POST /admin/device-inventory/create`, `POST /admin/device-inventory/<uuid>/update` |

---

## ワークフロー別カバレッジ

ワークフロー仕様書の各ワークフローに対して、どのテストクラスが対応しているかを示します。

### 初期表示

| 処理フロー項目 | 対応テストクラス | テスト項目No. |
|---|---|:---:|
| 在庫状況マスタ参照 | TestInventoryStatusMasterDefaults | 1〜3 |
| デバイス種別マスタ参照 | TestDeviceTypeMasterDefaults | 4〜6 |

### 検索・絞り込み

| 処理フロー項目 | 対応テストクラス | テスト項目No. |
|---|---|:---:|
| 在庫状況マスタ参照 | TestInventoryStatusMasterDefaults | 1〜3 |
| デバイス種別マスタ参照 | TestDeviceTypeMasterDefaults | 4〜6 |

### デバイス台帳登録

| 処理フロー項目 | 対応テストクラス | テスト項目No. |
|---|---|:---:|
| 在庫状況マスタ参照 | TestInventoryStatusMasterDefaults | 1〜3 |
| デバイス種別マスタ参照 | TestDeviceTypeMasterDefaults | 4〜6 |
| デバイス台帳マスタ登録 | TestDeviceInventoryMasterDefaults | 7〜11 |
| デバイス台帳マスタ登録 | TestDeviceInventoryMasterInit | 12〜22 |
| デバイスマスタ登録 | TestDeviceMasterDefaults | 23〜27 |

### デバイス台帳更新

| 処理フロー項目 | 対応テストクラス | テスト項目No. |
|---|---|:---:|
| 在庫状況マスタ参照 | TestInventoryStatusMasterDefaults | 1〜3 |
| デバイス種別マスタ参照 | TestDeviceTypeMasterDefaults | 4〜6 |
| デバイス台帳マスタ更新 | TestDeviceInventoryMasterDefaults | 7〜11 |
| デバイス台帳マスタ更新 | TestDeviceInventoryMasterInit | 12〜22 |
| デバイスマスタ更新 | TestDeviceMasterDefaults | 23〜27 |

### デバイス台帳削除

| 処理フロー項目 | 対応テストクラス | テスト項目No. |
|---|---|:---:|
| デバイス台帳マスタ論理削除 | TestDeviceInventoryMasterDefaults | 7〜11 |

---

## テストクラス一覧

テストクラスに対して、テスト観点、操作手順、予想結果を示します。

---

### TestInventoryStatusMasterDefaults

| No | テスト観点 | 操作手順 | 予想結果 |
|---|---|---|---|
| 1 | 2.1.1 正常系処理：有効な入力データで正常終了 | `InventoryStatusMaster(inventory_status_name='在庫中', creator=1, modifier=1)` を呼び出す（`delete_flag` を指定しない） | `instance.delete_flag` が `False` であること（デフォルト値） |
| 2 | 2.1.1 正常系処理：有効な入力データで正常終了 | `inventory_status_name='出荷済み'` を指定して `InventoryStatusMaster(inventory_status_name='出荷済み', creator=1, modifier=1)` を呼び出す | `instance.inventory_status_name` が `'出荷済み'` と一致すること |
| 3 | 2.1.1 正常系処理：有効な入力データで正常終了 | `delete_flag=True` を指定して `InventoryStatusMaster(inventory_status_name='廃棄済み', creator=1, modifier=1, delete_flag=True)` を呼び出す | `instance.delete_flag` が `True` であること |

---

### TestDeviceTypeMasterDefaults

| No | テスト観点 | 操作手順 | 予想結果 |
|---|---|---|---|
| 4 | 2.1.1 正常系処理：有効な入力データで正常終了 | `DeviceTypeMaster(device_type_name='センサー', creator=1, modifier=1)` を呼び出す（`delete_flag` を指定しない） | `instance.delete_flag` が `False` であること（デフォルト値） |
| 5 | 2.1.1 正常系処理：有効な入力データで正常終了 | `device_type_name='ゲートウェイ'` を指定して `DeviceTypeMaster(device_type_name='ゲートウェイ', creator=1, modifier=1)` を呼び出す | `instance.device_type_name` が `'ゲートウェイ'` と一致すること |
| 6 | 2.1.1 正常系処理：有効な入力データで正常終了 | `delete_flag=True` を指定して `DeviceTypeMaster(device_type_name='廃止デバイス種別', creator=1, modifier=1, delete_flag=True)` を呼び出す | `instance.delete_flag` が `True` であること |

---

### TestDeviceInventoryMasterDefaults

| No | テスト観点 | 操作手順 | 予想結果 |
|---|---|---|---|
| 7 | 2.1.1 正常系処理：有効な入力データで正常終了 | `make_valid_inventory_kwargs()` から `delete_flag` を除いた引数で `DeviceInventoryMaster(**kwargs)` を呼び出す | `instance.delete_flag` が `False` であること（デフォルト値） |
| 8 | 2.1.1 正常系処理：有効な入力データで正常終了 | `delete_flag=True` を加えた `make_valid_inventory_kwargs()` の引数で `DeviceInventoryMaster(**kwargs)` を呼び出す | `instance.delete_flag` が `True` であること |
| 9 | 2.1.1 正常系処理：有効な入力データで正常終了 | `delete_flag=False` を明示指定した `make_valid_inventory_kwargs()` の引数で `DeviceInventoryMaster(**kwargs)` を呼び出す | `instance.delete_flag` が `False` であること |
| 10 | 2.1.1 正常系処理：有効な入力データで正常終了 | `make_valid_inventory_kwargs()` の引数（`estimated_ship_date` を指定しない）で `DeviceInventoryMaster(**kwargs)` を呼び出す | `instance.estimated_ship_date` が `None` であること（デフォルト値） |
| 11 | 2.1.1 正常系処理：有効な入力データで正常終了 | `make_valid_inventory_kwargs()` の引数（`ship_date` を指定しない）で `DeviceInventoryMaster(**kwargs)` を呼び出す | `instance.ship_date` が `None` であること（デフォルト値） |

---

### TestDeviceInventoryMasterInit

| No | テスト観点 | 操作手順 | 予想結果 |
|---|---|---|---|
| 12 | 2.1.1 正常系処理：有効な入力データで正常終了 | `device_inventory_uuid='INV-UUID-TEST-001'` を指定した `make_valid_inventory_kwargs()` の引数で `DeviceInventoryMaster(**kwargs)` を呼び出す | `instance.device_inventory_uuid` が `'INV-UUID-TEST-001'` と一致すること |
| 13 | 2.1.1 正常系処理：有効な入力データで正常終了 | `inventory_status_id=3` を指定した `make_valid_inventory_kwargs()` の引数で `DeviceInventoryMaster(**kwargs)` を呼び出す | `instance.inventory_status_id` が `3` と一致すること |
| 14 | 2.1.1 正常系処理：有効な入力データで正常終了 | `device_model='MODEL-Z500'` を指定した `make_valid_inventory_kwargs()` の引数で `DeviceInventoryMaster(**kwargs)` を呼び出す | `instance.device_model` が `'MODEL-Z500'` と一致すること |
| 15 | 2.1.1 正常系処理：有効な入力データで正常終了 | `mac_address='BB:CC:DD:EE:FF:00'` を指定した `make_valid_inventory_kwargs()` の引数で `DeviceInventoryMaster(**kwargs)` を呼び出す | `instance.mac_address` が `'BB:CC:DD:EE:FF:00'` と一致すること |
| 16 | 2.1.1 正常系処理：有効な入力データで正常終了 | `purchase_date=date(2025,6,15)` を指定した `make_valid_inventory_kwargs()` の引数で `DeviceInventoryMaster(**kwargs)` を呼び出す | `instance.purchase_date` が `date(2025,6,15)` と一致すること |
| 17 | 2.1.1 正常系処理：有効な入力データで正常終了 | `manufacturer_warranty_end_date=date(2027,12,31)` を指定した `make_valid_inventory_kwargs()` の引数で `DeviceInventoryMaster(**kwargs)` を呼び出す | `instance.manufacturer_warranty_end_date` が `date(2027,12,31)` と一致すること |
| 18 | 2.1.1 正常系処理：有効な入力データで正常終了 | `inventory_location='新倉庫B-棚3'` を指定した `make_valid_inventory_kwargs()` の引数で `DeviceInventoryMaster(**kwargs)` を呼び出す | `instance.inventory_location` が `'新倉庫B-棚3'` と一致すること |
| 19 | 2.1.1 正常系処理：有効な入力データで正常終了 | `estimated_ship_date=date(2025,3,1)` を指定した `make_valid_inventory_kwargs()` の引数で `DeviceInventoryMaster(**kwargs)` を呼び出す | `instance.estimated_ship_date` が `date(2025,3,1)` と一致すること |
| 20 | 2.1.1 正常系処理：有効な入力データで正常終了 | `ship_date=date(2025,4,10)` を指定した `make_valid_inventory_kwargs()` の引数で `DeviceInventoryMaster(**kwargs)` を呼び出す | `instance.ship_date` が `date(2025,4,10)` と一致すること |
| 21 | 2.1.1 正常系処理：有効な入力データで正常終了 | `creator=42`・`modifier=42` を指定した `make_valid_inventory_kwargs()` の引数で `DeviceInventoryMaster(**kwargs)` を呼び出す | `instance.creator` と `instance.modifier` がいずれも `42` と一致すること |
| 22 | 2.1.2 正常系処理：最小構成の入力で正常終了 | `make_valid_inventory_kwargs()` の引数（必須項目のみ）で `DeviceInventoryMaster(**kwargs)` を呼び出す | `instance` が `None` でなく生成され、`instance.delete_flag` が `False` であること |

---

### TestDeviceMasterDefaults

| No | テスト観点 | 操作手順 | 予想結果 |
|---|---|---|---|
| 23 | 2.1.1 正常系処理：有効な入力データで正常終了 | `device_uuid='DEV-UUID-001'`・`organization_id=1`・`device_type_id=1`・`device_name='センサーA'`・`device_model='MODEL-X100'`・`device_inventory_id=100`・`creator=1`・`modifier=1` を引数として `DeviceMaster(**kwargs)` を呼び出す（`delete_flag` を指定しない） | `instance.delete_flag` が `False` であること（デフォルト値） |
| 24 | 2.1.1 正常系処理：有効な入力データで正常終了 | `delete_flag=True` を加えた引数で `DeviceMaster(**kwargs)` を呼び出す | `instance.delete_flag` が `True` であること |
| 25 | 2.1.2 正常系処理：最小構成の入力で正常終了 | `device_uuid='DEV-UUID-003'`・`organization_id=1`・`device_type_id=1`・`device_name='センサーC'`・`device_model='MODEL-X300'`・`device_inventory_id=300`・`creator=1`・`modifier=1` を引数として `DeviceMaster(**kwargs)` を呼び出す（任意フィールドを指定しない） | `instance.sim_id`・`instance.mac_address`・`instance.software_version`・`instance.device_location`・`instance.certificate_expiration_date` がいずれも `None` であること |
| 26 | 2.1.1 正常系処理：有効な入力データで正常終了 | `device_uuid='MyDevice-UUID-12345'` を指定した引数で `DeviceMaster(**kwargs)` を呼び出す | `instance.device_uuid` が `'MyDevice-UUID-12345'` と一致すること |
| 27 | 2.1.1 正常系処理：有効な入力データで正常終了 | `device_uuid='FULL-UUID-001'`・`organization_id=10`・`device_type_id=2`・`device_name='フルデバイス'`・`device_model='MODEL-FULL'`・`device_inventory_id=500`・`creator=99`・`modifier=99` を引数として `DeviceMaster(**kwargs)` を呼び出す | `instance` の各フィールド（`device_uuid`・`organization_id`・`device_type_id`・`device_name`・`device_model`・`device_inventory_id`・`creator`・`modifier`・`delete_flag`）がすべて期待値と一致すること |
