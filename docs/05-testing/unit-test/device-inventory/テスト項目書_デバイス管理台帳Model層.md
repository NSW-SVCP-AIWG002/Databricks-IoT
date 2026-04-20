# テスト項目書 - デバイス管理台帳 Model層

- **対象テストコード**: `tests/unit/models/test_device_inventory.py`
- **対象モデル**: `iot_app.models.device_inventory`（`DeviceInventoryMaster`, `InventoryStatusMaster`）/ `iot_app.models.device`（`DeviceMaster`, `DeviceTypeMaster`）
- **作成日**: 2026-04-20

---

## TestDeviceInventoryMasterDefaults

| No  | テスト観点                               | 操作手順                                                                                                                                               | 予想結果                                            | 実施結果 | 確認日 | 確認者 | 備考 |
| --- | ---------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------ | --------------------------------------------------- | -------- | ------ | ------ | ---- |
| 1   | 2.1.1 正常系：有効な入力データで正常終了 | `make_valid_inventory_kwargs()` で最小有効引数セットを用意し（`delete_flag` は指定しない）、`DeviceInventoryMaster(**kwargs)` でインスタンスを生成する | `instance.delete_flag` が `False` であること        |          |        |        |      |
| 2   | 2.1.1 正常系：有効な入力データで正常終了 | `make_valid_inventory_kwargs(delete_flag=True)` で引数を用意し、`DeviceInventoryMaster(**kwargs)` でインスタンスを生成する                             | `instance.delete_flag` が `True` であること         |          |        |        |      |
| 3   | 2.1.1 正常系：有効な入力データで正常終了 | `make_valid_inventory_kwargs(delete_flag=False)` で引数を用意し、`DeviceInventoryMaster(**kwargs)` でインスタンスを生成する                            | `instance.delete_flag` が `False` であること        |          |        |        |      |
| 4   | 2.1.1 正常系：有効な入力データで正常終了 | `make_valid_inventory_kwargs()` で引数を用意し（`estimated_ship_date` は指定しない）、`DeviceInventoryMaster(**kwargs)` でインスタンスを生成する       | `instance.estimated_ship_date` が `None` であること |          |        |        |      |
| 5   | 2.1.1 正常系：有効な入力データで正常終了 | `make_valid_inventory_kwargs()` で引数を用意し（`ship_date` は指定しない）、`DeviceInventoryMaster(**kwargs)` でインスタンスを生成する                 | `instance.ship_date` が `None` であること           |          |        |        |      |

---

## TestDeviceInventoryMasterInit

| No  | テスト観点                               | 操作手順                                                                                                          | 予想結果                                                                            | 実施結果 | 確認日 | 確認者 | 備考 |
| --- | ---------------------------------------- | ----------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------- | -------- | ------ | ------ | ---- |
| 6   | 2.1.1 正常系：有効な入力データで正常終了 | `device_inventory_uuid='INV-UUID-TEST-001'` を指定した引数で `DeviceInventoryMaster(**kwargs)` を生成する         | `instance.device_inventory_uuid` が `'INV-UUID-TEST-001'` と一致すること            |          |        |        |      |
| 7   | 2.1.1 正常系：有効な入力データで正常終了 | `inventory_status_id=3` を指定した引数で `DeviceInventoryMaster(**kwargs)` を生成する                             | `instance.inventory_status_id` が `3` と一致すること                                |          |        |        |      |
| 8   | 2.1.1 正常系：有効な入力データで正常終了 | `device_model='MODEL-Z500'` を指定した引数で `DeviceInventoryMaster(**kwargs)` を生成する                         | `instance.device_model` が `'MODEL-Z500'` と一致すること                            |          |        |        |      |
| 9   | 2.1.1 正常系：有効な入力データで正常終了 | `mac_address='BB:CC:DD:EE:FF:00'` を指定した引数で `DeviceInventoryMaster(**kwargs)` を生成する                   | `instance.mac_address` が `'BB:CC:DD:EE:FF:00'` と一致すること                      |          |        |        |      |
| 10  | 2.1.1 正常系：有効な入力データで正常終了 | `purchase_date=date(2025, 6, 15)` を指定した引数で `DeviceInventoryMaster(**kwargs)` を生成する                   | `instance.purchase_date` が `date(2025, 6, 15)` と一致すること                      |          |        |        |      |
| 11  | 2.1.1 正常系：有効な入力データで正常終了 | `manufacturer_warranty_end_date=date(2027, 12, 31)` を指定した引数で `DeviceInventoryMaster(**kwargs)` を生成する | `instance.manufacturer_warranty_end_date` が `date(2027, 12, 31)` と一致すること    |          |        |        |      |
| 12  | 2.1.1 正常系：有効な入力データで正常終了 | `inventory_location='新倉庫B-棚3'` を指定した引数で `DeviceInventoryMaster(**kwargs)` を生成する                  | `instance.inventory_location` が `'新倉庫B-棚3'` と一致すること                     |          |        |        |      |
| 13  | 2.1.1 正常系：有効な入力データで正常終了 | `estimated_ship_date=date(2025, 3, 1)` を指定した引数で `DeviceInventoryMaster(**kwargs)` を生成する              | `instance.estimated_ship_date` が `date(2025, 3, 1)` と一致すること                 |          |        |        |      |
| 14  | 2.1.1 正常系：有効な入力データで正常終了 | `ship_date=date(2025, 4, 10)` を指定した引数で `DeviceInventoryMaster(**kwargs)` を生成する                       | `instance.ship_date` が `date(2025, 4, 10)` と一致すること                          |          |        |        |      |
| 15  | 2.1.1 正常系：有効な入力データで正常終了 | `creator=42`, `modifier=42` を指定した引数で `DeviceInventoryMaster(**kwargs)` を生成する                         | `instance.creator` が `42`、`instance.modifier` が `42` と一致すること              |          |        |        |      |
| 16  | 2.1.2 正常系：最小構成の入力で正常終了   | `make_valid_inventory_kwargs()` の必須項目のみで `DeviceInventoryMaster(**kwargs)` を生成する                     | インスタンスが `None` でないこと、かつ `instance.delete_flag` が `False` であること |          |        |        |      |

---

## TestInventoryStatusMasterDefaults

| No  | テスト観点                               | 操作手順                                                                                                                                                  | 予想結果                                                        | 実施結果 | 確認日 | 確認者 | 備考 |
| --- | ---------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------- | -------- | ------ | ------ | ---- |
| 17  | 2.1.1 正常系：有効な入力データで正常終了 | `inventory_status_name='在庫中'`, `creator=1`, `modifier=1` を指定し（`delete_flag` は指定しない）、`InventoryStatusMaster(...)` でインスタンスを生成する | `instance.delete_flag` が `False` であること                    |          |        |        |      |
| 18  | 2.1.1 正常系：有効な入力データで正常終了 | `inventory_status_name='出荷済み'`, `creator=1`, `modifier=1` を指定し、`InventoryStatusMaster(...)` でインスタンスを生成する                             | `instance.inventory_status_name` が `'出荷済み'` と一致すること |          |        |        |      |
| 19  | 2.1.1 正常系：有効な入力データで正常終了 | `inventory_status_name='廃棄済み'`, `creator=1`, `modifier=1`, `delete_flag=True` を指定し、`InventoryStatusMaster(...)` でインスタンスを生成する         | `instance.delete_flag` が `True` であること                     |          |        |        |      |

---

## TestDeviceMasterDefaults

| No  | テスト観点                               | 操作手順                                                                                                                                                                                                                                                                                                            | 予想結果                                                                                                                                        | 実施結果 | 確認日 | 確認者 | 備考 |
| --- | ---------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------- | -------- | ------ | ------ | ---- |
| 20  | 2.1.1 正常系：有効な入力データで正常終了 | `device_uuid='DEV-UUID-001'` など必須項目を指定し（`delete_flag` は指定しない）、`DeviceMaster(...)` でインスタンスを生成する                                                                                                                                                                                       | `instance.delete_flag` が `False` であること                                                                                                    |          |        |        |      |
| 21  | 2.1.1 正常系：有効な入力データで正常終了 | 必須項目に加えて `delete_flag=True` を指定し、`DeviceMaster(...)` でインスタンスを生成する                                                                                                                                                                                                                          | `instance.delete_flag` が `True` であること                                                                                                     |          |        |        |      |
| 22  | 2.1.2 正常系：最小構成の入力で正常終了   | 必須項目（`device_uuid`, `device_type_id`, `device_name`, `device_model`, `device_inventory_id`, `organization_id`, `mac_address`, `creator`, `modifier`）のみを指定し、`DeviceMaster(...)` でインスタンスを生成する（`sim_id`, `software_version`, `device_location`, `certificate_expiration_date` は指定しない） | `instance.sim_id`, `instance.software_version`, `instance.device_location`, `instance.certificate_expiration_date` がいずれも `None` であること |          |        |        |      |
| 23  | 2.1.1 正常系：有効な入力データで正常終了 | `device_uuid='MyDevice-UUID-12345'` を指定した引数で `DeviceMaster(...)` を生成する                                                                                                                                                                                                                                 | `instance.device_uuid` が `'MyDevice-UUID-12345'` と一致すること                                                                                |          |        |        |      |
| 24  | 2.1.1 正常系：有効な入力データで正常終了 | `device_uuid='FULL-UUID-001'`, `device_type_id=2`, `device_name='フルデバイス'`, `device_model='MODEL-FULL'`, `device_inventory_id=500`, `organization_id=10`, `mac_address='EE:FF:AA:BB:CC:DD'`, `creator=99`, `modifier=99` を指定し、`DeviceMaster(...)` でインスタンスを生成する                                | 各フィールドがそれぞれ指定値と一致し、`instance.delete_flag` が `False` であること                                                              |          |        |        |      |

---

## TestDeviceTypeMasterDefaults

| No  | テスト観点                               | 操作手順                                                                                                                                          | 予想結果                                                       | 実施結果 | 確認日 | 確認者 | 備考 |
| --- | ---------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------- | -------- | ------ | ------ | ---- |
| 25  | 2.1.1 正常系：有効な入力データで正常終了 | `device_type_name='センサー'`, `creator=1`, `modifier=1` を指定し（`delete_flag` は指定しない）、`DeviceTypeMaster(...)` でインスタンスを生成する | `instance.delete_flag` が `False` であること                   |          |        |        |      |
| 26  | 2.1.1 正常系：有効な入力データで正常終了 | `device_type_name='ゲートウェイ'`, `creator=1`, `modifier=1` を指定し、`DeviceTypeMaster(...)` でインスタンスを生成する                           | `instance.device_type_name` が `'ゲートウェイ'` と一致すること |          |        |        |      |
| 27  | 2.1.1 正常系：有効な入力データで正常終了 | `device_type_name='廃止デバイス種別'`, `creator=1`, `modifier=1`, `delete_flag=True` を指定し、`DeviceTypeMaster(...)` でインスタンスを生成する   | `instance.delete_flag` が `True` であること                    |          |        |        |      |
