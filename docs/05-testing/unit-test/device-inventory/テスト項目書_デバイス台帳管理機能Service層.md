# テスト項目書 - デバイス台帳管理機能 Service層

**対象ファイル:** `tests/unit/services/test_device_inventory_service.py`
**対象モジュール:** `iot_app.services.device_inventory_service`
**作成日:** 2026-04-17
**テスト総数:** 86件

---

## TestGetDefaultSearchParams

`get_default_search_params()` のデフォルト値を検証するテスト群。

| No  | テスト観点                           | 操作手順                                           | 予想結果                                                               | 実施結果 | 確認日 | 確認者 | 備考 |
| --- | ------------------------------------ | -------------------------------------------------- | ---------------------------------------------------------------------- | -------- | ------ | ------ | ---- |
| 1   | 2.1.1 正常系処理（有効な入力データ） | `get_default_search_params()` を引数なしで呼び出す | 戻り値の `page` キーの値が `1` であること                              |          |        |        |      |
| 2   | 2.1.1 正常系処理（有効な入力データ） | `get_default_search_params()` を引数なしで呼び出す | 戻り値の `per_page` キーの値が `25` であること                         |          |        |        |      |
| 3   | 2.1.1 正常系処理（有効な入力データ） | `get_default_search_params()` を引数なしで呼び出す | 戻り値の `device_uuid` キーの値が `''`（空文字）であること             |          |        |        |      |
| 4   | 2.1.1 正常系処理（有効な入力データ） | `get_default_search_params()` を引数なしで呼び出す | 戻り値の `device_name` キーの値が `''`（空文字）であること             |          |        |        |      |
| 5   | 2.1.1 正常系処理（有効な入力データ） | `get_default_search_params()` を引数なしで呼び出す | 戻り値の `device_type_id` キーの値が `-1`（すべて選択）であること      |          |        |        |      |
| 6   | 2.1.1 正常系処理（有効な入力データ） | `get_default_search_params()` を引数なしで呼び出す | 戻り値の `inventory_status_id` キーの値が `-1`（すべて選択）であること |          |        |        |      |
| 7   | 2.1.1 正常系処理（有効な入力データ） | `get_default_search_params()` を引数なしで呼び出す | 戻り値の `inventory_location` キーの値が `''`（空文字）であること      |          |        |        |      |
| 8   | 2.1.1 正常系処理（有効な入力データ） | `get_default_search_params()` を引数なしで呼び出す | 戻り値の `purchase_date_from` キーの値が `None` であること             |          |        |        |      |
| 9   | 2.1.1 正常系処理（有効な入力データ） | `get_default_search_params()` を引数なしで呼び出す | 戻り値の `purchase_date_to` キーの値が `None` であること               |          |        |        |      |
| 10  | 2.1.1 正常系処理（有効な入力データ） | `get_default_search_params()` を引数なしで呼び出す | 戻り値の `sort_item_id` キーの値が `-1`（未選択）であること            |          |        |        |      |
| 11  | 2.1.1 正常系処理（有効な入力データ） | `get_default_search_params()` を引数なしで呼び出す | 戻り値の `sort_order` キーの値が `-1`（未選択）であること              |          |        |        |      |

---

## TestSearchDeviceInventories

`search_device_inventories()` の検索条件・ページング・ソート・戻り値を検証するテスト群。

| No  | テスト観点                                   | 操作手順                                                                                                                                                                                                        | 予想結果                                                                                                  | 実施結果 | 確認日 | 確認者 | 備考 |
| --- | -------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------- | -------- | ------ | ------ | ---- |
| 12  | 3.1.1.1 検索条件指定（条件指定）             | `DeviceInventoryMaster.query` および `SortItemMaster.query` をモック化し、`device_uuid='DEV-001'` を含むパラメータで `search_device_inventories()` を呼び出す                                                   | `query.filter` が1回以上呼ばれ、フィルタ条件文字列に `'DEV-001%'` が含まれること（前方一致検索）          |          |        |        |      |
| 13  | 3.1.1.1 検索条件指定（条件指定）             | `DeviceInventoryMaster.query` および `SortItemMaster.query` をモック化し、`device_name='センサー'` を含むパラメータで `search_device_inventories()` を呼び出す                                                  | `query.filter` が1回以上呼ばれ、フィルタ条件文字列に `'%センサー%'` が含まれること（部分一致検索）        |          |        |        |      |
| 14  | 3.1.1.1 検索条件指定（条件指定）             | `DeviceInventoryMaster.query` および `SortItemMaster.query` をモック化し、`inventory_location='倉庫A'` を含むパラメータで `search_device_inventories()` を呼び出す                                              | `query.filter` が1回以上呼ばれ、フィルタ条件文字列に `'%倉庫A%'` が含まれること（部分一致検索）           |          |        |        |      |
| 15  | 3.1.1.2 検索条件指定（複数条件）             | `DeviceInventoryMaster.query` および `SortItemMaster.query` をモック化し、`device_uuid='VALID'`、`device_name='ゲート'`、`inventory_location='5階'` を含むパラメータで `search_device_inventories()` を呼び出す | `query.filter` が3回以上呼ばれ、複数の検索条件が指定可能であること                                        |          |        |        |      |
| 16  | 3.1.1.1 検索条件指定（条件指定）             | 各モデルをモック化し、`device_type_id=1, sort_item_id=1, sort_order=1` を含むパラメータで `search_device_inventories()` を呼び出す                                                                              | `query.filter` が1回以上呼ばれること（デバイス種別フィルタが適用される）                                  |          |        |        |      |
| 17  | 3.1.1.2 検索条件指定（複数条件）             | 各モデルをモック化し、`purchase_date_from=date(2025,1,1)`, `purchase_date_to=date(2025,12,31)` を含むパラメータで `search_device_inventories()` を呼び出す                                                      | `query.filter` が1回以上呼ばれること（購入日範囲フィルタが適用される）                                    |          |        |        |      |
| 18  | 3.1.2.1 検索条件未指定（全件相当）           | `query.count` を0, `query.offset().all()` を空リストに設定し、デフォルトパラメータで `search_device_inventories()` を呼び出す                                                                                   | 戻り値がリスト型と整数型のタプルであること                                                                |          |        |        |      |
| 19  | 3.1.3.1 ページング・件数制御（件数制御）     | `query.all` にモックレコード2件を設定し、`per_page=-1` で `search_device_inventories()` を呼び出す                                                                                                              | `query.limit` が呼ばれないこと、戻り値のリストがモックレコードと一致すること                              |          |        |        |      |
| 20  | 3.1.3.1 ページング・件数制御（件数制御）     | `query.count` を1、`query.offset().all()` をモックレコード1件に設定し、`page=2, per_page=25` で `search_device_inventories()` を呼び出す                                                                        | `query.limit` および `query.offset` が呼ばれること                                                        |          |        |        |      |
| 21  | 3.1.4.1 検索結果戻り値ハンドリング（正常系） | モックレコード3件と `query.count` を3に設定し、デフォルトパラメータで `search_device_inventories()` を呼び出す                                                                                                  | 戻り値が長さ2のタプルであり、`total`(検索結果件数) が `3` であること                                      |          |        |        |      |
| 22  | 3.1.4.2 検索結果戻り値ハンドリング（空結果） | `query.count` を0, `query.offset().all()` を空リストに設定し、デフォルトパラメータで `search_device_inventories()` を呼び出す                                                                                   | `inventories`(検索結果一覧リスト) が `[]`、`total`(検索結果件数) が `0` であること                        |          |        |        |      |
| 23  | 3.1.2.1 検索条件未指定（全件相当）           | 各モデルをモック化し、`device_type_id=-1` を含むパラメータで `search_device_inventories()` を呼び出す                                                                                                           | `SortItemMaster.query.filter_by` が呼ばれないこと（デバイス種別フィルタおよびソート検索がスキップされる） |          |        |        |      |
| 24  | 3.1.2.1 検索条件未指定（全件相当）           | 各モデルをモック化し、`inventory_status_id=-1` を含むパラメータで `search_device_inventories()` を呼び出す                                                                                                      | `SortItemMaster.query.filter_by` が呼ばれないこと（在庫状況フィルタおよびソート検索がスキップされる）     |          |        |        |      |
| 25  | 3.1.1.1 検索条件指定（条件指定）             | 各モデルをモック化し、`sort_item_id=-1, sort_order=-1` で `search_device_inventories()` を呼び出す                                                                                                              | `SortItemMaster.query.filter_by` が呼ばれないこと、`query.order_by` はデフォルトソートで呼ばれること      |          |        |        |      |
| 26  | 3.1.1.1 検索条件指定（条件指定）             | `SortItemMaster` が `sort_item_name='inventory_location'` を返すよう設定し、`sort_item_id=9, sort_order=1` で `search_device_inventories()` を呼び出す                                                          | `SortItemMaster.query.filter_by` が呼ばれ、カラムの `.asc()` が呼ばれること                               |          |        |        |      |
| 27  | 3.1.1.1 検索条件指定（条件指定）             | `SortItemMaster` が `sort_item_name='inventory_location'` を返すよう設定し、`sort_item_id=9, sort_order=2` で `search_device_inventories()` を呼び出す                                                          | `SortItemMaster.query.filter_by` が呼ばれ、カラムの `.desc()` が呼ばれること                              |          |        |        |      |

---

## TestCreateDeviceInventory

`create_device_inventory()` のDB登録・UC連携・エラーハンドリングを検証するテスト群。

| No  | テスト観点                                    | 操作手順                                                                                                                                                                  | 予想結果                                                                                                  | 実施結果 | 確認日 | 確認者 | 備考 |
| --- | --------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------- | -------- | ------ | ------ | ---- |
| 28  | 2.1.1 / 3.2.1.1 正常系処理 / 登録処理呼び出し | `DeviceInventoryMaster`, `DeviceMaster`, `db`, `UnityCatalogConnector` をモック化し、有効なフォームデータで `create_device_inventory(form_data, creator_id=1)` を呼び出す | `db.session.add()` が2回以上呼ばれ、`db.session.flush()` が呼ばれること                                   |          |        |        |      |
| 29  | 2.1.1 / 3.2.2.1 正常系処理 / 登録結果         | 同上のモック設定で `create_device_inventory(form_data, creator_id=1)` を呼び出す                                                                                          | `db.session.commit()` が1回呼ばれること                                                                   |          |        |        |      |
| 30  | 3.2.1.1 登録処理呼び出し                      | 同上のモック設定で `create_device_inventory(form_data, creator_id=1)` を呼び出す                                                                                          | `execute_dml()` が1回呼ばれ、渡されたSQLに `INSERT INTO iot_catalog.oltp_db.device_master` が含まれること |          |        |        |      |
| 31  | 2.3.2 副作用チェック（例外発生時）            | `db.session.flush` が `Exception` を送出するよう設定し、`create_device_inventory()` を呼び出す                                                                            | `db.session.rollback()` が呼ばれること、`Exception` が上位へ伝播すること                                  |          |        |        |      |
| 32  | 1.3.1 エラーハンドリング（例外伝播）          | `db.session.flush` が `RuntimeError` を送出するよう設定し、`create_device_inventory()` を呼び出す                                                                         | `RuntimeError` が握りつぶされず上位へ伝播すること                                                         |          |        |        |      |
| 33  | 1.3.1 エラーハンドリング（例外伝播）          | `execute_dml()` の1回目が `Exception` を送出するよう設定し、2回目は正常終了するよう設定して `create_device_inventory()` を呼び出す                                        | `execute_dml()` が2回呼ばれ、2回目のSQLに `DELETE FROM iot_catalog.oltp_db.device_master` が含まれること  |          |        |        |      |
| 34  | 2.3.2 副作用チェック（例外発生時）            | `execute_dml()` の1回目が `Exception` を送出するよう設定し、`create_device_inventory()` を呼び出す                                                                        | `db.session.rollback()` が呼ばれること                                                                    |          |        |        |      |
| 35  | 3.2.1.1 登録処理呼び出し                      | `uuid` モジュールをモック化して `create_device_inventory(form_data, creator_id=1)` を呼び出す                                                                             | `uuid.uuid4()` が呼ばれること                                                                             |          |        |        |      |
| 36  | 3.2.1.1 登録処理呼び出し                      | `DeviceInventoryMaster` のコンストラクタ引数をキャプチャするサイドエフェクトを設定し、`create_device_inventory(form_data, creator_id=42)` を呼び出す                      | `DeviceInventoryMaster` コンストラクタの `creator` および `modifier` キーワード引数が `42` であること     |          |        |        |      |

---

## TestUpdateDeviceInventory

`update_device_inventory()` のフィールド更新・UC連携・エラーハンドリングを検証するテスト群。

| No  | テスト観点                                    | 操作手順                                                                                                                                                                                                                                                              | 予想結果                                                                                                          | 実施結果 | 確認日 | 確認者 | 備考 |
| --- | --------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------- | -------- | ------ | ------ | ---- |
| 37  | 2.1.1 / 3.3.1.1 正常系処理 / 更新処理呼び出し | `DeviceInventoryMaster.query.filter_by().first_or_404()` と `DeviceMaster.query.filter_by().first_or_404()` をモック化し、`inventory_location='新倉庫B', purchase_date=date(2025,6,1)` で `update_device_inventory('test-uuid', form_data, modifier_id=1)` を呼び出す | `mock_inventory.inventory_location` が `'新倉庫B'`、`mock_inventory.purchase_date` が `date(2025,6,1)` であること |          |        |        |      |
| 38  | 3.3.1.1 更新処理呼び出し                      | 同上のモック設定で `device_name='新センサーX', device_type_id=2` を含むフォームデータで `update_device_inventory()` を呼び出す                                                                                                                                        | `mock_device.device_name` が `'新センサーX'`、`mock_device.device_type_id` が `2` であること                      |          |        |        |      |
| 39  | 3.3.2.2 更新結果（ID指定）                    | 同上のモック設定で `update_device_inventory('test-uuid', form_data, modifier_id=99)` を呼び出す                                                                                                                                                                       | `mock_inventory.modifier` が `99`、`mock_device.modifier` が `99` であること                                      |          |        |        |      |
| 40  | 3.3.1.1 更新処理呼び出し                      | 同上のモック設定で `update_device_inventory()` を呼び出す                                                                                                                                                                                                             | `execute_dml()` が1回呼ばれ、渡されたSQLに `UPDATE iot_catalog.oltp_db.device_master` が含まれること              |          |        |        |      |
| 41  | 3.3.2.1 更新結果（処理完了）                  | 同上のモック設定で `update_device_inventory()` を呼び出す                                                                                                                                                                                                             | `db.session.commit()` が1回呼ばれること                                                                           |          |        |        |      |
| 42  | 2.3.2 副作用チェック（例外発生時）            | `db.session.flush` が `Exception` を送出するよう設定し、`update_device_inventory()` を呼び出す                                                                                                                                                                        | `db.session.rollback()` が呼ばれること、`Exception` が上位へ伝播すること                                          |          |        |        |      |
| 43  | 1.3.1 エラーハンドリング（例外伝播）          | `execute_dml()` の1回目が `Exception` を送出し、2回目は正常終了するよう設定して `update_device_inventory()` を呼び出す                                                                                                                                                | `execute_dml()` が2回呼ばれること（1回目: UPDATE、2回目: 旧値への UC ロールバック UPDATE）                        |          |        |        |      |
| 44  | 2.3.2 副作用チェック（例外発生時）            | `execute_dml()` の1回目が `Exception` を送出するよう設定し、`update_device_inventory()` を呼び出す                                                                                                                                                                    | `db.session.rollback()` が呼ばれること                                                                            |          |        |        |      |

---

## TestDeleteDeviceInventories

`delete_device_inventories()` の論理削除・存在チェック・エラーハンドリングを検証するテスト群。

| No  | テスト観点                                         | 操作手順                                                                                                                                                                                                 | 予想結果                                                                 | 実施結果 | 確認日 | 確認者 | 備考 |
| --- | -------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------ | -------- | ------ | ------ | ---- |
| 45  | 2.1.1 / 3.4.1.1 正常系処理 / 削除処理呼び出し      | `DeviceInventoryMaster.query.filter().all()` が `delete_flag=False` のモック台帳1件を返すよう設定し、`delete_device_inventories(['uuid-001'], modifier_id=1)` を呼び出す                                 | `mock_inventory.delete_flag` が `True` であること                        |          |        |        |      |
| 46  | 3.4.1.1 削除処理呼び出し                           | 同上のモック設定で `delete_device_inventories(['uuid-001'], modifier_id=99)` を呼び出す                                                                                                                  | `mock_inventory.modifier` が `99` であること                             |          |        |        |      |
| 47  | 3.4.2.1 削除結果（処理完了）                       | 同上のモック設定で `delete_device_inventories(['uuid-001'], modifier_id=1)` を呼び出す                                                                                                                   | `db.session.commit()` が1回呼ばれること                                  |          |        |        |      |
| 48  | 2.2.2 対象データ存在チェック（対象IDが存在しない） | `DeviceInventoryMaster.query.filter().all()` が空リストを返すよう設定し、`delete_device_inventories(['nonexistent-uuid'], modifier_id=1)` を呼び出す                                                     | `ValueError('削除対象が見つかりません')` が送出されること                |          |        |        |      |
| 49  | 2.2.2 対象データ存在チェック（対象IDが存在しない） | `DeviceInventoryMaster.query.filter().all()` が空リストを返すよう設定し、`delete_device_inventories([], modifier_id=1)` を呼び出す                                                                       | `ValueError` が送出されること                                            |          |        |        |      |
| 50  | 2.3.2 副作用チェック（例外発生時）                 | モック台帳1件を返す設定で `db.session.flush` が `Exception` を送出するよう設定し、`delete_device_inventories()` を呼び出す                                                                               | `db.session.rollback()` が呼ばれること、`Exception` が上位へ伝播すること |          |        |        |      |
| 51  | 2.1.3 正常系処理（最大件数内の入力）               | `DeviceInventoryMaster.query.filter().all()` がモック台帳2件（`inv1`, `inv2`、両方 `delete_flag=False`）を返すよう設定し、`delete_device_inventories(['uuid-001','uuid-002'], modifier_id=1)` を呼び出す | `inv1.delete_flag` が `True`、`inv2.delete_flag` が `True` であること    |          |        |        |      |

---

## TestExportDeviceInventoriesCsv

`export_device_inventories_csv()` のCSV生成・形式・エンコーディングを検証するテスト群。

| No  | テスト観点                                    | 操作手順                                                                                                                                                                    | 予想結果                                                                                                                                                                              | 実施結果 | 確認日 | 確認者 | 備考 |
| --- | --------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------- | ------ | ------ | ---- |
| 52  | 3.1.3.1 ページング・件数制御（件数制御）      | `search_device_inventories` をモック化して `([], 0)` を返すよう設定し、デフォルトパラメータで `export_device_inventories_csv()` を呼び出す                                  | 内部の `search_device_inventories` が `per_page=-1` で呼ばれること                                                                                                                    |          |        |        |      |
| 53  | 3.1.1.1 検索条件指定（条件指定）              | `search_device_inventories` をモック化して `([], 0)` を返すよう設定し、`page=3` を含むパラメータで `export_device_inventories_csv()` を呼び出す                             | 内部の `search_device_inventories` が `page=1` で呼ばれること                                                                                                                         |          |        |        |      |
| 54  | 3.5.1.1 CSV生成ロジック（ヘッダー行出力）     | `search_device_inventories` が `([], 0)` を返すよう設定し、`export_device_inventories_csv()` を呼び出してUTF-8-sig デコードする                                             | `操作列`, `デバイス名`, `デバイス種別`, `モデル情報`, `SIMID`, `MACアドレス`, `在庫状況`, `購入日`, `出荷予定日`, `出荷日`, `メーカー保証終了日`, `在庫場所` がヘッダーに含まれること |          |        |        |      |
| 55  | 3.5.1.3 CSV生成ロジック（0件出力）            | `search_device_inventories` が `([], 0)` を返すよう設定し、`export_device_inventories_csv()` を呼び出してデコードして行数を確認する                                         | 空行を除く行数が1行（ヘッダーのみ）であること                                                                                                                                         |          |        |        |      |
| 56  | 3.5.1.2 CSV生成ロジック（データ行出力）       | `search_device_inventories` がモック台帳2件（`センサーA`, `センサーB`）を返すよう設定し、`export_device_inventories_csv()` を呼び出してデコードして行数を確認する           | 空行を除く行数が3行（ヘッダー + 2件）であること                                                                                                                                       |          |        |        |      |
| 57  | 3.5.1.4 CSV生成ロジック（列順序）             | `search_device_inventories` が `([], 0)` を返すよう設定し、`export_device_inventories_csv()` を呼び出してヘッダー列を解析する                                               | CSV列順が `操作列, デバイス名, デバイス種別, モデル情報, SIMID, MACアドレス, 在庫状況, 購入日, 出荷予定日, 出荷日, メーカー保証終了日, 在庫場所` であること                           |          |        |        |      |
| 58  | 3.5.3.1 エンコーディング処理（UTF-8 BOM付き） | `search_device_inventories` が `([], 0)` を返すよう設定し、`export_device_inventories_csv()` を呼び出す                                                                     | 戻り値がバイト列の場合は先頭3バイトが `\xef\xbb\xbf`（UTF-8 BOM）、文字列の場合は `str` 型であること ※要確認                                                                          |          |        |        |      |
| 59  | 3.5.1.2 CSV生成ロジック（データ行出力）       | `search_device_inventories` が `purchase_date=date(2025,3,15)` のモック台帳1件を返すよう設定し、`export_device_inventories_csv()` を呼び出してデコードする                  | CSV出力に `'2025/03/15'` が含まれること（スラッシュ区切りのYYYY/MM/DD形式）                                                                                                           |          |        |        |      |
| 60  | 3.5.1.2 CSV生成ロジック（データ行出力）       | `search_device_inventories` が `estimated_ship_date=None, ship_date=None` のモック台帳1件を返すよう設定し、`export_device_inventories_csv()` を呼び出してデータ行を取得する | データ行に連続カンマ（`,,`）またはダブルクォートで囲まれた空フィールド（`,"","`）が存在すること                                                                                       |          |        |        |      |

---

## TestGetDeviceInventoryFormOptions

`get_device_inventory_form_options()` のマスタデータ取得を検証するテスト群。

| No  | テスト観点                                   | 操作手順                                                                                                                                    | 予想結果                                                                                         | 実施結果 | 確認日 | 確認者 | 備考 |
| --- | -------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------ | -------- | ------ | ------ | ---- |
| 61  | 3.1.4.1 検索結果戻り値ハンドリング（正常系） | `DeviceTypeMaster`, `InventoryStatusMaster`, `SortItemMaster` を空リスト返却でモック化し、`get_device_inventory_form_options()` を呼び出す  | 戻り値が `tuple` 型で長さ3であること                                                             |          |        |        |      |
| 62  | 2.1.1 正常系処理（有効な入力データ）         | 同上のモック設定で `get_device_inventory_form_options()` を呼び出す                                                                         | `DeviceTypeMaster.query.filter_by(delete_flag=False)` が呼ばれること                             |          |        |        |      |
| 63  | 2.1.1 正常系処理（有効な入力データ）         | 同上のモック設定で `get_device_inventory_form_options()` を呼び出す                                                                         | `InventoryStatusMaster.query.filter_by(delete_flag=False)` が呼ばれること                        |          |        |        |      |
| 64  | 2.1.1 正常系処理（有効な入力データ）         | 同上のモック設定で `get_device_inventory_form_options()` を呼び出す                                                                         | `SortItemMaster.query.filter()` が呼ばれること                                                   |          |        |        |      |
| 65  | 2.1.1 正常系処理（有効な入力データ）         | 同上のモック設定で `get_device_inventory_form_options()` を呼び出す                                                                         | `SortItemMaster.query.filter().order_by()` が呼ばれること                                        |          |        |        |      |
| 66  | 3.1.4.1 検索結果戻り値ハンドリング（正常系） | 各マスタのモックに `device_types` 2件・`inventory_statuses` 1件・`sort_items` 3件を設定し、`get_device_inventory_form_options()` を呼び出す | 戻り値の `device_types`, `inventory_statuses`, `sort_items` がそれぞれモックデータと一致すること |          |        |        |      |
| 67  | 3.1.4.2 検索結果戻り値ハンドリング（空結果） | 各マスタのモックに空リストを設定し、`get_device_inventory_form_options()` を呼び出す                                                        | `device_types`, `inventory_statuses`, `sort_items` がすべて空リストであること                    |          |        |        |      |

---

## TestGetOrganizationOptions

`get_organization_options()` の組織マスタ取得を検証するテスト群。

| No  | テスト観点                                   | 操作手順                                                                                                                         | 予想結果                                                               | 実施結果 | 確認日 | 確認者 | 備考 |
| --- | -------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------- | -------- | ------ | ------ | ---- |
| 68  | 2.1.1 正常系処理（有効な入力データ）         | `OrganizationMaster.query.filter_by().order_by().all()` が空リストを返すよう設定し、`get_organization_options()` を呼び出す      | `OrganizationMaster.query.filter_by(delete_flag=False)` が呼ばれること |          |        |        |      |
| 69  | 2.1.1 正常系処理（有効な入力データ）         | 同上のモック設定で `get_organization_options()` を呼び出す                                                                       | `filter_by()` の後に `order_by()` が呼ばれること                       |          |        |        |      |
| 70  | 3.1.4.1 検索結果戻り値ハンドリング（正常系） | `OrganizationMaster.query.filter_by().order_by().all()` がモック組織2件を返すよう設定し、`get_organization_options()` を呼び出す | 戻り値がモックデータと一致すること                                     |          |        |        |      |
| 71  | 3.1.4.2 検索結果戻り値ハンドリング（空結果） | `OrganizationMaster.query.filter_by().order_by().all()` が空リストを返すよう設定し、`get_organization_options()` を呼び出す      | 戻り値が空リストであること                                             |          |        |        |      |

---

## TestCheckLinkedDeviceMaster

`check_linked_device_master()` の紐づきデバイスマスタ存在確認を検証するテスト群。

| No  | テスト観点                                         | 操作手順                                                                                                                                                                                       | 予想結果                                                               | 実施結果 | 確認日 | 確認者 | 備考 |
| --- | -------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------- | -------- | ------ | ------ | ---- |
| 72  | 2.1.1 正常系処理（有効な入力データ）               | `DeviceInventoryMaster.query.filter().all()` がモック台帳1件、`DeviceMaster.query.filter().count()` が `1` を返すよう設定し、`check_linked_device_master(['uuid-001'])` を呼び出す             | `True` が返ること（紐づくデバイスマスタが存在する）                    |          |        |        |      |
| 73  | 2.1.1 正常系処理（有効な入力データ）               | `DeviceInventoryMaster.query.filter().all()` がモック台帳1件、`DeviceMaster.query.filter().count()` が `0` を返すよう設定し、`check_linked_device_master(['uuid-001'])` を呼び出す             | `False` が返ること（紐づくデバイスマスタが存在しない）                 |          |        |        |      |
| 74  | 2.2.2 対象データ存在チェック（対象IDが存在しない） | `DeviceInventoryMaster.query.filter().all()` が空リスト、`DeviceMaster.query.filter().count()` が `0` を返すよう設定し、`check_linked_device_master(['nonexistent-uuid'])` を呼び出す          | `False` が返ること（指定UUIDに対応する台帳レコードが存在しない）       |          |        |        |      |
| 75  | 2.1.3 正常系処理（最大件数内の入力）               | `DeviceInventoryMaster.query.filter().all()` がモック台帳2件、`DeviceMaster.query.filter().count()` が `1` を返すよう設定し、`check_linked_device_master(['uuid-001', 'uuid-002'])` を呼び出す | `True` が返ること（複数UUID指定時でもデバイスマスタが1件以上存在する） |          |        |        |      |

---

**合計: 86件**

| クラス名                          | 関数名                            | 件数     |
| --------------------------------- | --------------------------------- | -------- |
| TestGetDefaultSearchParams        | get_default_search_params         | 11件     |
| TestSearchDeviceInventories       | search_device_inventories         | 16件     |
| TestCreateDeviceInventory         | create_device_inventory           | 9件      |
| TestUpdateDeviceInventory         | update_device_inventory           | 8件      |
| TestDeleteDeviceInventories       | delete_device_inventories         | 7件      |
| TestExportDeviceInventoriesCsv    | export_device_inventories_csv     | 9件      |
| TestGetDeviceInventoryFormOptions | get_device_inventory_form_options | 7件      |
| TestGetOrganizationOptions        | get_organization_options          | 4件      |
| TestCheckLinkedDeviceMaster       | check_linked_device_master        | 4件      |
| **合計**                          |                                   | **75件** |
