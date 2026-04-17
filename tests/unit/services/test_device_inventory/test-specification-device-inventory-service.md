# テスト項目書 - デバイス台帳管理 Service層

**対象ファイル:** `tests/unit/services/test_device_inventory_service.py`
**対象モジュール:**
- `iot_app.services.device_inventory_service`（セクション 1〜10）

**作成日:** 2026-04-17

---

## 1. get_default_search_params

| No.  | テストメソッド名                                 | 観点番号 | テスト概要                                        | 実行内容                                           | 想定結果                                         | 実行結果 | 確認者名 | 備考 |
| ---- | ------------------------------------------------ | -------- | ------------------------------------------------- | -------------------------------------------------- | ------------------------------------------------ | -------- | -------- | ---- |
| 1-1  | test_returns_page_1                              | 2.1.1    | page のデフォルト値検証                           | `get_default_search_params()` を引数なしで呼び出す | `page`として1が返却されること                    |          |          |      |
| 1-2  | test_returns_per_page_25                         | 2.1.1    | per_page のデフォルト値検証                       | `get_default_search_params()` を引数なしで呼び出す | `per_page`として25が返却されること               |          |          |      |
| 1-3  | test_returns_empty_string_for_device_uuid        | 2.1.1    | device_uuid のデフォルト値検証                    | `get_default_search_params()` を引数なしで呼び出す | `device_uuid`として空文字が返却されること        |          |          |      |
| 1-4  | test_returns_empty_string_for_device_name        | 2.1.1    | device_name のデフォルト値検証                    | `get_default_search_params()` を引数なしで呼び出す | `device_name`として空文字が返却されること        |          |          |      |
| 1-5  | test_returns_all_for_device_type                 | 2.1.1    | device_type のデフォルト値検証（すべて選択）      | `get_default_search_params()` を引数なしで呼び出す | `device_type_id`として-1が返却されること         |          |          |      |
| 1-6  | test_returns_all_for_inventory_status            | 2.1.1    | inventory_status のデフォルト値検証（すべて選択） | `get_default_search_params()` を引数なしで呼び出す | `inventory_status_id`として-1が返却されること    |          |          |      |
| 1-7  | test_returns_empty_string_for_inventory_location | 2.1.1    | inventory_location のデフォルト値検証             | `get_default_search_params()` を引数なしで呼び出す | `inventory_location`として空文字が返却されること |          |          |      |
| 1-8  | test_returns_none_for_purchase_date_from         | 2.1.1    | purchase_date_from のデフォルト値検証             | `get_default_search_params()` を引数なしで呼び出す | `purchase_date_from`としてNoneが返却されること   |          |          |      |
| 1-9  | test_returns_none_for_purchase_date_to           | 2.1.1    | purchase_date_to のデフォルト値検証               | `get_default_search_params()` を引数なしで呼び出す | `purchase_date_to`としてNoneが返却されること     |          |          |      |
| 1-10 | test_returns_minus1_for_sort_item_id             | 2.1.1    | sort_item_id のデフォルト値検証（未選択）         | `get_default_search_params()` を引数なしで呼び出す | `sort_item_id`として-1が返却されること           |          |          |      |
| 1-11 | test_returns_minus1_for_sort_order               | 2.1.1    | sort_order のデフォルト値検証（未選択）           | `get_default_search_params()` を引数なしで呼び出す | `sort_order`として-1が返却されること             |          |          |      |

---

## 2. search_device_inventories

| No.  | テストメソッド名                                       | 観点番号 | テスト概要                                       | 実行内容                                                                                      | 想定結果                                                                                                | 実行結果 | 確認者名 | 備考 |
| ---- | ------------------------------------------------------ | -------- | ------------------------------------------------ | --------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------- | -------- | -------- | ---- |
| 2-1  | test_search_with_device_uuid_applies_filter            | 3.1.1.1  | device_uuid 指定時のフィルタ適用確認（前方一致） | `device_uuid='DEV-001'` を含むパラメータで検索を実行する                                      | ・`query.filter` が1回以上呼ばれること<br>・フィルタ条件文字列に `'DEV-001%'` が含まれること（前方一致）  |          |          |      |
| 2-2  | test_search_with_device_name_applies_filter            | 3.1.1.2  | device_name 指定時のフィルタ適用確認（前方一致） | `device_name='センサー'` を含むパラメータで検索を実行する                                     | ・`query.filter` が1回以上呼ばれること<br>フィルタ条件文字列に `'センサー%'` が含まれること（前方一致） |          |          |      |
| 2-3  | test_search_with_device_type_not_minus1_applies_filter | 3.1.1.1  | device_type が -1 以外のときフィルタ適用確認     | `device_type=1, sort_item_id=1, sort_order=1` を含むパラメータで検索を実行する                | `query.filter` が1回以上呼ばれること                                                                    |          |          |      |
| 2-4  | test_search_with_purchase_date_range_applies_filter    | 3.1.1.2  | 購入日 From/To 指定時の範囲フィルタ確認          | `purchase_date_from=date(2025, 1, 1)`, `purchase_date_to=date(2025, 12, 31)` で検索を実行する | `query.filter` が1回以上呼ばれること                                                                    |          |          |      |
| 2-5  | test_search_without_conditions_returns_result          | 3.1.2.1  | 条件なし検索時の結果型確認                       | デフォルトパラメータのみで検索を実行する                                                      | `(list, int)` のタプルが返却されること                                                                  |          |          |      |
| 2-6  | test_search_per_page_minus1_uses_all_without_limit     | 3.1.3.1  | per_page=-1 時の全件取得確認                     | `per_page=-1` で検索を実行する                                                                | `query.limit` が呼ばれないこと、全件リストが返却されること                                              |          |          |      |
| 2-7  | test_search_with_per_page_uses_limit_offset            | 3.1.3.1  | per_page 正数時のページング確認                  | `page=2, per_page=25` で検索を実行する                                                        | `query.limit` と `query.offset` が呼ばれること                                                          |          |          |      |
| 2-8  | test_search_returns_tuple_of_list_and_total            | 3.1.4.1  | 戻り値の型・内容確認                             | デフォルトパラメータで検索を実行する（件数3件）                                               | `(inventories, total)` タプルが返却され `total == 3` であること                                         |          |          |      |
| 2-9  | test_search_empty_result_returns_empty_list_and_zero   | 3.1.4.2  | 0件検索時の戻り値確認                            | 検索結果0件になるようモックを設定して検索を実行する                                           | `inventories == []` かつ `total == 0` であること                                                        |          |          |      |
| 2-10 | test_search_with_device_type_minus1_skips_filter       | 3.1.2.1  | device_type=-1 時のフィルタスキップ確認          | `device_type=-1` で検索を実行する                                                             | `SortItemMaster.query.filter_by` が呼ばれないこと（sort_item_id=-1 のためソート検索もスキップ）         |          |          |      |
| 2-11 | test_search_with_inventory_status_minus1_skips_filter  | 3.1.2.1  | inventory_status=-1 時のフィルタスキップ確認     | `inventory_status=-1` で検索を実行する                                                        | `SortItemMaster.query.filter_by` が呼ばれないこと（sort_item_id=-1 のためソート検索もスキップ）         |          |          |      |
| 2-12 | test_search_with_sort_item_id_minus1_skips_sort_lookup | 3.1.1.1  | sort_item_id=-1 時のソート検索スキップ確認       | `sort_item_id=-1, sort_order=-1` で検索を実行する                                             | `SortItemMaster.query.filter_by` が呼ばれず、`query.order_by` はデフォルトソートで呼ばれること          |          |          |      |
| 2-13 | test_search_with_sort_order_1_applies_asc              | 3.1.1.1  | sort_order=1（昇順）時のソート適用確認           | `sort_item_id=9, sort_order=1` で検索を実行する                                               | `SortItemMaster` が検索され、カラムの `.asc()` が呼ばれること                                           |          |          |      |
| 2-14 | test_search_with_sort_order_2_applies_desc             | 3.1.1.1  | sort_order=2（降順）時のソート適用確認           | `sort_item_id=9, sort_order=2` で検索を実行する                                               | `SortItemMaster` が検索され、カラムの `.desc()` が呼ばれること                                          |          |          |      |

---

## 3. create_device_inventory

| No. | テストメソッド名                                         | 観点番号        | テスト概要                              | 実行内容                                                          | 想定結果                                                                                                   | 実行結果 | 確認者名 | 備考 |
| --- | -------------------------------------------------------- | --------------- | --------------------------------------- | ----------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------- | -------- | -------- | ---- |
| 3-1 | test_create_success_adds_inventory_and_device_to_session | 2.1.1 / 3.2.1.1 | DBセッションへの追加確認                | 有効なフォームデータで登録を実行する                              | `db.session.add()` が2回以上呼ばれ、`db.session.flush()` が呼ばれること                                    |          |          |      |
| 3-2 | test_create_success_commits_on_completion                | 2.1.1 / 3.2.2.1 | 正常完了時のコミット確認                | 有効なフォームデータで登録を実行する                              | `db.session.commit()` が1回呼ばれること                                                                    |          |          |      |
| 3-3 | test_create_calls_unity_catalog_insert                   | 3.2.1.1         | Unity Catalog INSERT 呼び出し確認       | 有効なフォームデータで登録を実行する                              | `execute_dml()` が1回呼ばれ、SQL に `INSERT INTO iot_catalog.oltp_db.device_master` が含まれること         |          |          |      |
| 3-4 | test_create_db_flush_exception_calls_rollback            | 2.3.2           | flush 例外時のロールバック確認          | `db.session.flush()` が例外をスローするよう設定して登録を実行する | `db.session.rollback()` が呼ばれること、例外が上位へ伝播すること                                           |          |          |      |
| 3-5 | test_create_db_exception_propagates                      | 1.3.1           | DB例外の伝播確認                        | `db.session.flush()` が `RuntimeError` をスローするよう設定する   | `RuntimeError` が上位へ握りつぶされず伝播すること                                                          |          |          |      |
| 3-6 | test_create_uc_exception_triggers_compensating_delete    | 1.3.1           | UC INSERT失敗時の補償DELETE確認         | UC の `execute_dml()` が1回目で例外をスローするよう設定する       | `execute_dml()` が2回呼ばれ、2回目の SQL に `DELETE FROM iot_catalog.oltp_db.device_master` が含まれること |          |          |      |
| 3-7 | test_create_uc_exception_calls_oltp_rollback             | 2.3.2           | UC INSERT失敗時の OLTP ロールバック確認 | UC の `execute_dml()` が1回目で例外をスローするよう設定する       | `db.session.rollback()` が呼ばれること                                                                     |          |          |      |
| 3-8 | test_create_generates_device_inventory_uuid              | 3.2.1.1         | device_inventory_uuid の自動生成確認    | `uuid.uuid4()` をモックして登録を実行する                         | `uuid.uuid4()` が呼ばれること                                                                              |          |          |      |
| 3-9 | test_create_sets_creator_id_on_records                   | 3.2.1.1         | creator_id の設定確認                   | `creator_id=42` で登録を実行する                                  | `DeviceInventoryMaster` コンストラクタの引数 `creator` および `modifier` が `42` であること                |          |          |      |

---

## 4. update_device_inventory

| No. | テストメソッド名                              | 観点番号        | テスト概要                               | 実行内容                                                                    | 想定結果                                                                                             | 実行結果 | 確認者名 | 備考 |
| --- | --------------------------------------------- | --------------- | ---------------------------------------- | --------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------- | -------- | -------- | ---- |
| 4-1 | test_update_success_updates_inventory_fields  | 2.1.1 / 3.3.1.1 | device_inventory フィールドの更新確認    | `inventory_location='新倉庫B'`, `purchase_date=2025-06-01` で更新を実行する | `mock_inventory.inventory_location == '新倉庫B'` かつ `purchase_date == date(2025, 6, 1)` であること |          |          |      |
| 4-2 | test_update_success_updates_device_fields     | 3.3.1.1         | device_master フィールドの更新確認       | `device_name='新センサーX'`, `device_type_id=2` で更新を実行する            | `mock_device.device_name == '新センサーX'` かつ `device_type_id == 2` であること                     |          |          |      |
| 4-3 | test_update_sets_modifier_id_on_both_records  | 3.3.2.2         | modifier_id の設定確認                   | `modifier_id=99` で更新を実行する                                           | `mock_inventory.modifier == 99` かつ `mock_device.modifier == 99` であること                         |          |          |      |
| 4-4 | test_update_calls_unity_catalog_update        | 3.3.1.1         | Unity Catalog UPDATE 呼び出し確認        | 有効なフォームデータで更新を実行する                                        | `execute_dml()` が1回呼ばれ、SQL に `UPDATE iot_catalog.oltp_db.device_master` が含まれること        |          |          |      |
| 4-5 | test_update_success_commits                   | 3.3.2.1         | 更新成功時のコミット確認                 | 有効なフォームデータで更新を実行する                                        | `db.session.commit()` が1回呼ばれること                                                              |          |          |      |
| 4-6 | test_update_db_flush_exception_calls_rollback | 2.3.2           | flush 例外時のロールバック確認           | `db.session.flush()` が例外をスローするよう設定して更新を実行する           | `db.session.rollback()` が呼ばれること                                                               |          |          |      |
| 4-7 | test_update_uc_exception_triggers_uc_rollback | 1.3.1           | UC UPDATE 失敗時の UC ロールバック確認   | UC の `execute_dml()` が1回目で例外をスローするよう設定する                 | `execute_dml()` が2回呼ばれること（1回目: UPDATE、2回目: 旧値へのロールバック UPDATE）               |          |          |      |
| 4-8 | test_update_uc_exception_calls_oltp_rollback  | 2.3.2           | UC UPDATE 失敗時の OLTP ロールバック確認 | UC の `execute_dml()` が1回目で例外をスローするよう設定する                 | `db.session.rollback()` が呼ばれること                                                               |          |          |      |

---

## 5. delete_device_inventories

> **変更履歴:** 削除対象は `device_inventory_master` のみ（device_master/UC の論理削除は廃止）

| No. | テストメソッド名                                       | 観点番号        | テスト概要                               | 実行内容                                                          | 想定結果                                                              | 実行結果 | 確認者名 | 備考 |
| --- | ------------------------------------------------------ | --------------- | ---------------------------------------- | ----------------------------------------------------------------- | --------------------------------------------------------------------- | -------- | -------- | ---- |
| 5-1 | test_delete_success_sets_delete_flag_true_on_inventory | 2.1.1 / 3.4.1.1 | device_inventory の delete_flag 更新確認 | 有効な UUID リストで削除を実行する                                | `mock_inventory.delete_flag is True` であること                       |          |          |      |
| 5-2 | test_delete_sets_modifier_id_on_inventory              | 3.4.1.1         | modifier_id の設定確認                   | `modifier_id=99` で削除を実行する                                 | `mock_inventory.modifier == 99` であること                            |          |          |      |
| 5-3 | test_delete_success_commits                            | 3.4.2.1         | 削除成功時のコミット確認                 | 有効な UUID リストで削除を実行する                                | `db.session.commit()` が1回呼ばれること                               |          |          |      |
| 5-4 | test_delete_no_matching_records_raises_value_error     | 2.2.2           | 存在しない UUID 指定時のエラー確認       | 存在しない UUID で削除を実行する（DBモックは空リストを返す）      | `ValueError('削除対象が見つかりません')` がスローされること           |          |          |      |
| 5-5 | test_delete_empty_uuids_list_raises_value_error        | 2.2.2           | 空の UUID リスト指定時のエラー確認       | 空リスト `[]` で削除を実行する                                    | `ValueError` がスローされること                                       |          |          |      |
| 5-6 | test_delete_db_flush_exception_calls_rollback          | 2.3.2           | flush 例外時のロールバック確認           | `db.session.flush()` が例外をスローするよう設定して削除を実行する | `db.session.rollback()` が呼ばれること                                |          |          |      |
| 5-7 | test_delete_multiple_inventories                       | 2.1.3           | 複数 UUID 指定時の全件論理削除確認       | `['uuid-001', 'uuid-002']` の2件で削除を実行する                  | `inv1.delete_flag is True` かつ `inv2.delete_flag is True` であること |          |          |      |

---

## 6. export_device_inventories_csv

| No. | テストメソッド名                                    | 観点番号 | テスト概要                                   | 実行内容                                                                         | 想定結果                                                                                                                                                               | 実行結果 | 確認者名 | 備考 |
| --- | --------------------------------------------------- | -------- | -------------------------------------------- | -------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------- | -------- | ---- |
| 6-1 | test_export_calls_search_with_per_page_minus1       | 3.1.3.1  | CSVエクスポート時の全件取得確認              | デフォルトパラメータで CSV エクスポートを実行する                                | 内部の `search_device_inventories` が `per_page=-1` で呼ばれること                                                                                                     |          |          |      |
| 6-2 | test_export_calls_search_with_page_1                | 3.1.1.1  | CSVエクスポート時のページング無効化確認      | `page=3` を含むパラメータで CSV エクスポートを実行する                           | 内部の `search_device_inventories` が `page=1` で呼ばれること                                                                                                          |          |          |      |
| 6-3 | test_export_csv_contains_required_headers           | 3.5.1.1  | CSV ヘッダー項目の存在確認                   | デフォルトパラメータで CSV エクスポートを実行する                                | 操作列、デバイス名、デバイス種別、モデル情報、SIMID、MACアドレス、在庫状況、購入日、出荷予定日、出荷日、メーカー保証終了日、在庫場所がヘッダーに含まれること           |          |          |      |
| 6-4 | test_export_empty_list_returns_headers_only         | 3.5.1.3  | データ0件時のヘッダー行のみ出力確認          | 検索結果0件の状態で CSV エクスポートを実行する                                   | CSV 出力がヘッダー行のみ（1行）であること                                                                                                                              |          |          |      |
| 6-5 | test_export_multiple_records_all_output             | 3.5.1.2  | 複数件データの全件出力確認                   | 2件のモックデータを返す状態で CSV エクスポートを実行する                         | CSV 出力がヘッダー+2行（計3行）であること                                                                                                                              |          |          |      |
| 6-6 | test_export_csv_column_order                        | 3.5.1.4  | CSV 列順の仕様適合確認                       | デフォルトパラメータで CSV エクスポートを実行する                                | CSV ヘッダーの列順が `操作列, デバイス名, デバイス種別, モデル情報, SIMID, MACアドレス, 在庫状況, 購入日, 出荷予定日, 出荷日, メーカー保証終了日, 在庫場所` であること |          |          |      |
| 6-7 | test_export_csv_encodes_with_utf8_bom               | 3.5.3.1  | UTF-8 BOM エンコーディング確認               | デフォルトパラメータで CSV エクスポートを実行する                                | バイト列の場合は先頭3バイトが `\xef\xbb\xbf`（UTF-8 BOM）であること。文字列の場合は `str` 型であること（TODO: 実装完了後に要確認）                                     |          |          |      |
| 6-8 | test_export_date_formatted_as_slash_separated       | 3.5.1.2  | 日付フォーマット確認（YYYY/MM/DD）           | `purchase_date=date(2025, 3, 15)` を持つデータで CSV エクスポートを実行する      | CSV 出力に `2025/03/15` が含まれること                                                                                                                                 |          |          |      |
| 6-9 | test_export_optional_date_none_outputs_empty_string | 3.5.1.2  | 任意日付フィールドが None 時の空文字出力確認 | `estimated_ship_date=None, ship_date=None` のデータで CSV エクスポートを実行する | CSV データ行に空フィールドが存在すること（連続カンマまたは空ダブルクォートが出現）                                                                                     |          |          |      |

---

## 7. get_device_inventory_form_options

| No. | テストメソッド名                                       | 観点番号 | テスト概要                                              | 実行内容                                                                          | 想定結果                                                                        | 実行結果 | 確認者名 | 備考 |
| --- | ------------------------------------------------------ | -------- | ------------------------------------------------------- | --------------------------------------------------------------------------------- | ------------------------------------------------------------------------------- | -------- | -------- | ---- |
| 7-1 | test_returns_tuple_of_three_elements                   | 3.1.4.1  | 戻り値が3要素タプルであることを確認                     | `get_device_inventory_form_options()` を呼び出す                                  | 返却値が`tuple` 型かつ長さ3であること                                           |          |          |      |
| 7-2 | test_device_types_queries_with_delete_flag_false       | 2.1.1    | DeviceTypeMaster の delete_flag=False フィルタ確認      | `get_device_inventory_form_options()` を呼び出す                                  | `DeviceTypeMaster.query.filter_by(delete_flag=False)` が呼ばれること            |          |          |      |
| 7-3 | test_inventory_statuses_queries_with_delete_flag_false | 2.1.1    | InventoryStatusMaster の delete_flag=False フィルタ確認 | `get_device_inventory_form_options()` を呼び出す                                  | `InventoryStatusMaster.query.filter_by(delete_flag=False)` が呼ばれること       |          |          |      |
| 7-4 | test_sort_items_queries_with_view_id_filter            | 2.1.1    | SortItemMaster の view_id/delete_flag フィルタ確認      | `get_device_inventory_form_options()` を呼び出す                                  | `SortItemMaster.query.filter()` が呼ばれること                                  |          |          |      |
| 7-5 | test_sort_items_ordered_by_sort_order                  | 2.1.1    | SortItemMaster の sort_order 昇順取得確認               | `get_device_inventory_form_options()` を呼び出す                                  | `filter()` の後に `order_by()` が呼ばれること                                   |          |          |      |
| 7-6 | test_returns_master_data_as_fetched                    | 3.1.4.1  | DBから取得したデータがそのまま返却されることを確認      | 各マスタに複数件モックを設定して `get_device_inventory_form_options()` を呼び出す | `device_types`, `inventory_statuses`, `sort_items` がモックデータと一致すること |          |          |      |
| 7-7 | test_returns_empty_lists_when_masters_are_empty        | 3.1.4.2  | 各マスタ0件時の空リスト返却を確認                       | 各マスタが0件のモックで `get_device_inventory_form_options()` を呼び出す          | `device_types == []`, `inventory_statuses == []`, `sort_items == []` であること |          |          |      |

---

## 8. get_organization_options

| No. | テストメソッド名                              | 観点番号 | テスト概要                                           | 実行内容                                                                | 想定結果                                                               | 実行結果 | 確認者名 | 備考 |
| --- | --------------------------------------------- | -------- | ---------------------------------------------------- | ----------------------------------------------------------------------- | ---------------------------------------------------------------------- | -------- | -------- | ---- |
| 8-1 | test_queries_with_delete_flag_false           | 2.1.1    | OrganizationMaster の delete_flag=False フィルタ確認 | `get_organization_options()` を呼び出す                                 | `OrganizationMaster.query.filter_by(delete_flag=False)` が呼ばれること |          |          |      |
| 8-2 | test_ordered_by_organization_name             | 2.1.1    | organization_name 昇順取得確認                       | `get_organization_options()` を呼び出す                                 | `filter_by()` の後に `order_by()` が呼ばれること                       |          |          |      |
| 8-3 | test_returns_master_data_as_fetched           | 3.1.4.1  | DBから取得したデータがそのまま返却されることを確認   | 組織マスタに2件モックを設定して `get_organization_options()` を呼び出す | 戻り値がモックデータと一致すること                                     |          |          |      |
| 8-4 | test_returns_empty_list_when_no_organizations | 3.1.4.2  | 組織マスタ0件時の空リスト返却確認                    | 組織マスタが0件のモックで `get_organization_options()` を呼び出す       | 空リストが返却されること                                               |          |          |      |

---

## 9. get_device_uuid_validator

観点: `1.1.6 不整値チェック`、`2.1 正常系処理`

| No. | テストメソッド名                                     | 観点番号 | テスト概要                             | 実行内容                                                           | 想定結果                                                           | 実行結果 | 確認者名 | 備考 |
| --- | ---------------------------------------------------- | -------- | -------------------------------------- | ------------------------------------------------------------------ | ------------------------------------------------------------------ | -------- | -------- | ---- |
| 9-1 | test_returns_azure_validator_when_auth_type_is_azure | 2.1.1    | AUTH_TYPE=azure 時のバリデータ返却確認 | AUTH_TYPE=azure で `get_device_uuid_validator()` を呼ぶ            | max_length=128、pattern・description キーを持つ辞書が返る          |          |          |      |
| 9-2 | test_returns_aws_validator_when_auth_type_is_aws     | 2.1.1    | AUTH_TYPE=aws 時のバリデータ返却確認   | AUTH_TYPE=aws で `get_device_uuid_validator()` を呼ぶ              | aws 用パターン（英数字・ハイフン・アンダースコアのみ）の辞書が返る |          |          |      |
| 9-3 | test_returns_same_as_azure_when_auth_type_is_local   | 2.1.1    | AUTH_TYPE=local 時のバリデータ返却確認 | AUTH_TYPE=local で `get_device_uuid_validator()` を呼ぶ            | azure バリデータと同じ pattern・max_length が返る                  |          |          |      |
| 9-4 | test_defaults_to_azure_when_auth_type_not_set        | 2.1.1    | AUTH_TYPE 未設定時のデフォルト値確認   | AUTH_TYPE 未設定で `get_device_uuid_validator()` を呼ぶ            | デフォルト値 'azure' が使われ max_length=128 が返る                |          |          |      |
| 9-5 | test_raises_value_error_when_auth_type_is_unknown    | 1.1.6.1  | 未知の AUTH_TYPE 指定時のエラー確認    | AUTH_TYPE=unknown_provider で `get_device_uuid_validator()` を呼ぶ | `ValueError: Unknown AUTH_TYPE: unknown_provider` が送出される     |          |          |      |

---

## 10. validate_device_uuid

観点: `1.1.2 最大文字列長チェック`、`1.1.6 不整値チェック`、`2.1 正常系処理`

| No.  | テストメソッド名                                        | 観点番号 | テスト概要                                 | 実行内容                                                           | 想定結果                                                                                         | 実行結果 | 確認者名 | 備考 |
| ---- | ------------------------------------------------------- | -------- | ------------------------------------------ | ------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------ | -------- | -------- | ---- |
| 10-1 | test_valid_azure_uuid_returns_true_and_empty_message    | 2.1.1    | 有効な Azure UUID の正常系確認             | AUTH_TYPE=azure で有効な UUID を渡す                               | `(True, '')` が返る                                                                              |          |          |      |
| 10-2 | test_valid_aws_uuid_returns_true_and_empty_message      | 2.1.1    | 有効な AWS UUID の正常系確認               | AUTH_TYPE=aws で有効な UUID を渡す                                 | `(True, '')` が返る                                                                              |          |          |      |
| 10-3 | test_uuid_at_max_length_returns_true                    | 1.1.2.1  | 最大文字数ちょうどの境界値確認（有効）     | ちょうど 128 文字の UUID を渡す                                    | `(True, '')` が返る（境界値: 有効）                                                              |          |          |      |
| 10-4 | test_uuid_over_max_length_returns_false_with_message    | 1.1.2.2  | 最大文字数超過の境界値確認（無効）         | 129 文字の UUID を渡す                                             | `(False, 'device_uuidは128文字以内で入力してください')` が返る（境界値: 無効）                   |          |          |      |
| 10-5 | test_invalid_chars_for_azure_returns_false_with_message | 1.1.6.1  | Azure パターン不一致の確認                 | AUTH_TYPE=azure でスペースを含む UUID を渡す                       | `(False, 'device_uuidの形式が不正です...')` が返る                                               |          |          |      |
| 10-6 | test_invalid_chars_for_aws_returns_false_with_message   | 1.1.6.1  | AWS パターン不一致の確認                   | AUTH_TYPE=aws でドットを含む UUID を渡す                           | `(False, 'device_uuidの形式が不正です...')` が返る                                               |          |          |      |
| 10-7 | test_length_error_message_includes_max_length           | 1.1.2.2  | エラーメッセージへの最大文字数埋め込み確認 | 200 文字の UUID を渡す                                             | エラーメッセージに '128' が含まれる                                                              |          |          |      |
| 10-8 | test_pattern_error_message_includes_description         | 1.1.6.1  | エラーメッセージへの説明文埋め込み確認     | AUTH_TYPE=azure でパターン不一致の UUID（`'invalid uuid!'`）を渡す | エラーメッセージに `'ASCII 7ビット英数字'` または `'device_uuidの形式が不正です'` が含まれること |          |          |      |

---

## 11. check_linked_device_master

観点: `2.1 正常系処理`、`2.2 対象データ存在チェック`

| No.  | テストメソッド名                            | 観点番号 | テスト概要                                             | 実行内容                                                                           | 想定結果           | 実行結果 | 確認者名 | 備考 |
| ---- | ------------------------------------------- | -------- | ------------------------------------------------------ | ---------------------------------------------------------------------------------- | ------------------ | -------- | -------- | ---- |
| 11-1 | test_returns_true_when_linked_device_exists | 2.1.1    | 紐づくデバイスマスタが存在する場合 True を返す         | 台帳レコード1件・デバイスマスタ1件のモックで `check_linked_device_master()` を呼ぶ | `True` が返ること  |          |          |      |
| 11-2 | test_returns_false_when_no_linked_device    | 2.1.1    | 紐づくデバイスマスタが存在しない場合 False を返す      | 台帳レコード1件・デバイスマスタ0件のモックで `check_linked_device_master()` を呼ぶ | `False` が返ること |          |          |      |
| 11-3 | test_returns_false_when_inventory_not_found | 2.2.2    | 指定UUIDの台帳レコードが存在しない場合 False を返す    | 台帳レコード0件のモックで `check_linked_device_master()` を呼ぶ                    | `False` が返ること |          |          |      |
| 11-4 | test_checks_multiple_inventory_uuids        | 2.1.3    | 複数UUID指定時にデバイスマスタが1件でも存在すれば True | 台帳レコード2件・デバイスマスタ1件のモックで `check_linked_device_master()` を呼ぶ | `True` が返ること  |          |          |      |

---

**合計: 86 テストケース**

| セクション | 関数名                            | 件数     |
| ---------- | --------------------------------- | -------- |
| 1          | get_default_search_params         | 11件     |
| 2          | search_device_inventories         | 14件     |
| 3          | create_device_inventory           | 9件      |
| 4          | update_device_inventory           | 8件      |
| 5          | delete_device_inventories         | 7件      |
| 6          | export_device_inventories_csv     | 9件      |
| 7          | get_device_inventory_form_options | 7件      |
| 8          | get_organization_options          | 4件      |
| 9          | get_device_uuid_validator         | 5件      |
| 10         | validate_device_uuid              | 8件      |
| 11         | check_linked_device_master        | 4件      |
| **合計**   |                                   | **86件** |
