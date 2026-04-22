# 単体テスト項目書 - デバイス管理 Model層

対象ファイル: `tests/unit/models/test_device.py`
対象モデル: `src/iot_app/models/device.py`

---

## TestDeviceMasterDefaults

| No | テスト観点 | 操作手順 | 予想結果 |
|----|-----------|---------|---------|
| 1 | 2.1.1 正常系：デフォルト値（delete_flag） | `DeviceMaster` を最小有効引数（`delete_flag` 未指定）でインスタンス化する | `instance.delete_flag` が `False` であること |
| 2 | 2.1.1 正常系：フィールド値設定（delete_flag=True） | `DeviceMaster` を `delete_flag=True` を指定してインスタンス化する | `instance.delete_flag` が `True` であること |
| 3 | 2.1.1 正常系：フィールド値設定（device_uuid） | `DeviceMaster` を `device_uuid='DEV-TEST-001'` を指定してインスタンス化する | `instance.device_uuid` が `'DEV-TEST-001'` であること |
| 4 | 2.1.1 正常系：フィールド値設定（device_name） | `DeviceMaster` を `device_name='温度センサー'` を指定してインスタンス化する | `instance.device_name` が `'温度センサー'` であること |
| 5 | 2.1.2 正常系：nullable列のデフォルト値（sim_id） | `DeviceMaster` を `sim_id` 未指定でインスタンス化する | `instance.sim_id` が `None` であること |
| 6 | 2.1.2 正常系：nullable列のデフォルト値（mac_address） | `DeviceMaster` を `mac_address` 未指定でインスタンス化する | `instance.mac_address` が `None` であること |
| 7 | 2.1.1 正常系：フィールド値設定（mac_address） | `DeviceMaster` を `mac_address='AA:BB:CC:DD:EE:FF'` を指定してインスタンス化する | `instance.mac_address` が `'AA:BB:CC:DD:EE:FF'` であること |
| 8 | 2.1.2 正常系：nullable列のデフォルト値（software_version） | `DeviceMaster` を `software_version` 未指定でインスタンス化する | `instance.software_version` が `None` であること |
| 9 | 2.1.2 正常系：nullable列のデフォルト値（device_location） | `DeviceMaster` を `device_location` 未指定でインスタンス化する | `instance.device_location` が `None` であること |
| 10 | 2.1.2 正常系：nullable列のデフォルト値（certificate_expiration_date） | `DeviceMaster` を `certificate_expiration_date` 未指定でインスタンス化する | `instance.certificate_expiration_date` が `None` であること |
| 11 | 2.1.1 正常系：フィールド値設定（certificate_expiration_date） | `DeviceMaster` を `certificate_expiration_date=datetime(2025, 12, 31, 0, 0, 0)` を指定してインスタンス化する | `instance.certificate_expiration_date` が `datetime(2025, 12, 31, 0, 0, 0)` であること |
| 12 | 2.1.1 正常系：フィールド値設定（device_type_id） | `DeviceMaster` を `device_type_id=2` を指定してインスタンス化する | `instance.device_type_id` が `2` であること |
| 13 | 2.1.1 正常系：テーブル名確認 | `DeviceMaster.__tablename__` を参照する | `'device_master'` であること |
| 14 | 2.1.1 正常系：フィールド値設定（device_model, nullable=False） | `DeviceMaster` を `device_model='MODEL-B200'` を指定してインスタンス化する | `instance.device_model` が `'MODEL-B200'` であること |
| 15 | 2.1.1 正常系：フィールド値設定（device_inventory_id, nullable=True） | `DeviceMaster` を `device_inventory_id=42` を指定してインスタンス化する | `instance.device_inventory_id` が `42` であること |
| 16 | 2.1.2 正常系：nullable列のデフォルト値（device_inventory_id） | `DeviceMaster` を `device_inventory_id` 未指定でインスタンス化する | `instance.device_inventory_id` が `None` であること |
| 17 | 2.1.1 正常系：フィールド値設定（creator / modifier, 監査証跡） | `DeviceMaster` を `creator=10, modifier=20` を指定してインスタンス化する | `instance.creator` が `10`、`instance.modifier` が `20` であること |
| 18 | 2.1.1 正常系：フィールド値設定（software_version） | `DeviceMaster` を `software_version='v1.2.3'` を指定してインスタンス化する | `instance.software_version` が `'v1.2.3'` であること |

---

## TestDeviceTypeMasterDefaults

| No | テスト観点 | 操作手順 | 予想結果 |
|----|-----------|---------|---------|
| 19 | 2.1.1 正常系：デフォルト値（delete_flag） | `DeviceTypeMaster` を最小有効引数（`delete_flag` 未指定）でインスタンス化する | `instance.delete_flag` が `False` であること |
| 20 | 2.1.1 正常系：フィールド値設定（delete_flag=True） | `DeviceTypeMaster` を `delete_flag=True` を指定してインスタンス化する | `instance.delete_flag` が `True` であること |
| 21 | 2.1.1 正常系：フィールド値設定（device_type_name） | `DeviceTypeMaster` を `device_type_name='ゲートウェイ'` を指定してインスタンス化する | `instance.device_type_name` が `'ゲートウェイ'` であること |
| 22 | 2.1.1 正常系：テーブル名確認 | `DeviceTypeMaster.__tablename__` を参照する | `'device_type_master'` であること |
| 23 | 2.1.1 正常系：フィールド値設定（creator / modifier, 監査証跡） | `DeviceTypeMaster` を `creator=5, modifier=7` を指定してインスタンス化する | `instance.creator` が `5`、`instance.modifier` が `7` であること |

---

## TestDeviceMasterByUser

対象: `v_device_master_by_user` VIEW（ログインユーザーが参照可能なデバイス一覧）

| No | テスト観点 | 操作手順 | 予想結果 |
|----|-----------|---------|---------|
| 24 | 2.1.1 正常系：テーブル名（ビュー名）確認 | `DeviceMasterByUser.__tablename__` を参照する | `'v_device_master_by_user'` であること |
| 25 | 2.1.1 正常系：デフォルト値（delete_flag） | `DeviceMasterByUser` を最小有効引数（`delete_flag` 未指定）でインスタンス化する | `instance.delete_flag` が `False` であること |
| 26 | 2.1.1 正常系：フィールド値設定（user_id） | `DeviceMasterByUser` を `user_id=99` を指定してインスタンス化する | `instance.user_id` が `99` であること |
| 27 | 2.1.1 正常系：フィールド値設定（device_id） | `DeviceMasterByUser` を `device_id=42` を指定してインスタンス化する | `instance.device_id` が `42` であること |
| 28 | 2.1.1 正常系：フィールド値設定（device_name） | `DeviceMasterByUser` を `device_name='温度センサー'` を指定してインスタンス化する | `instance.device_name` が `'温度センサー'` であること |
| 29 | 2.1.1 正常系：フィールド値設定（device_model） | `DeviceMasterByUser` を `device_model='MODEL-X500'` を指定してインスタンス化する | `instance.device_model` が `'MODEL-X500'` であること |
| 30 | 2.1.1 正常系：フィールド値設定（depth, 組織階層深さ） | `DeviceMasterByUser` を `depth=3` を指定してインスタンス化する | `instance.depth` が `3` であること |
| 31 | 2.1.2 正常系：nullable列のデフォルト値（sim_id） | `DeviceMasterByUser` を `sim_id` 未指定でインスタンス化する | `instance.sim_id` が `None` であること |
| 32 | 2.1.2 正常系：nullable列のデフォルト値（mac_address） | `DeviceMasterByUser` を `mac_address` 未指定でインスタンス化する | `instance.mac_address` が `None` であること |
| 33 | 2.1.2 正常系：nullable列のデフォルト値（device_location） | `DeviceMasterByUser` を `device_location` 未指定でインスタンス化する | `instance.device_location` が `None` であること |
| 34 | 2.1.2 正常系：nullable列のデフォルト値（certificate_expiration_date） | `DeviceMasterByUser` を `certificate_expiration_date` 未指定でインスタンス化する | `instance.certificate_expiration_date` が `None` であること |
| 35 | 2.1.2 正常系：nullable列のデフォルト値（software_version） | `DeviceMasterByUser` を `software_version` 未指定でインスタンス化する | `instance.software_version` が `None` であること |
