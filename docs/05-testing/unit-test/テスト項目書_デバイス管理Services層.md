# 単体テスト項目書 - デバイス管理 Services層

対象ファイル: `tests/unit/services/test_device_service.py`
対象サービス: `src/iot_app/services/device_service.py`

---

## TestGetDefaultSearchParams

| No | テスト観点 | 操作手順 | 予想結果 |
|----|-----------|---------|---------|
| 1 | 2.1.1 正常系：デフォルト値（page） | `get_default_search_params()` を引数なしで呼び出す | 戻り値の `page` が `1` であること |
| 2 | 2.1.1 正常系：デフォルト値（per_page） | `get_default_search_params()` を引数なしで呼び出す | 戻り値の `per_page` が `25` であること |
| 3 | 2.1.1 正常系：デフォルト値（device_id） | `get_default_search_params()` を引数なしで呼び出す | 戻り値の `device_id` が空文字であること |
| 4 | 2.1.1 正常系：デフォルト値（device_name） | `get_default_search_params()` を引数なしで呼び出す | 戻り値の `device_name` が空文字であること |
| 5 | 2.1.1 正常系：デフォルト値（device_type_id） | `get_default_search_params()` を引数なしで呼び出す | 戻り値の `device_type_id` が `None` であること |
| 6 | 2.1.1 正常系：デフォルト値（location） | `get_default_search_params()` を引数なしで呼び出す | 戻り値の `location` が空文字であること |
| 7 | 2.1.1 正常系：デフォルト値（organization_id） | `get_default_search_params()` を引数なしで呼び出す | 戻り値の `organization_id` が `None` であること |
| 8 | 2.1.1 正常系：デフォルト値（certificate_expiration_date） | `get_default_search_params()` を引数なしで呼び出す | 戻り値の `certificate_expiration_date` が空文字であること |
| 9 | 2.1.1 正常系：デフォルト値（status） | `get_default_search_params()` を引数なしで呼び出す | 戻り値の `status` が `None` であること |
| 10 | 2.1.1 正常系：デフォルト値（sort_by） | `get_default_search_params()` を引数なしで呼び出す | 戻り値の `sort_by` が空文字であること |
| 11 | 2.1.1 正常系：デフォルト値（order） | `get_default_search_params()` を引数なしで呼び出す | 戻り値の `order` が空文字であること |

---

## TestSearchDevices

| No | テスト観点 | 操作手順 | 予想結果 |
|----|-----------|---------|---------|
| 12 | 3.1.1.1 検索条件指定（device_id, LIKE） | `DeviceMasterByUser.query` をモック化し `device_id='DEV-001'` を指定して `search_devices(params, user_id=1)` を呼び出す | `filter()` が1回以上呼ばれ、フィルタ引数に `'DEV-001'` が含まれること |
| 13 | 3.1.1.2 検索条件指定（device_name, LIKE） | `DeviceMasterByUser.query` をモック化し `device_name='センサー'` を指定して `search_devices(params, user_id=1)` を呼び出す | `filter()` が1回以上呼ばれ、フィルタ引数に `'センサー'` が含まれること |
| 14 | 3.1.1.1 検索条件指定（device_type_id） | `DeviceMasterByUser.query` をモック化し `device_type_id=1` を指定して `search_devices(params, user_id=1)` を呼び出す | `filter()` が1回以上呼ばれること |
| 15 | 3.1.1.1 検索条件指定（location, LIKE） | `DeviceMasterByUser.query` をモック化し `location='本社'` を指定して `search_devices(params, user_id=1)` を呼び出す | `filter()` が1回以上呼ばれ、フィルタ引数に `'本社'` が含まれること |
| 16 | 3.1.1.1 検索条件指定（organization_id） | `DeviceMasterByUser.query` をモック化し `organization_id=10` を指定して `search_devices(params, user_id=1)` を呼び出す | `filter()` が1回以上呼ばれること |
| 17 | 3.1.2.1 検索条件未指定（全件相当） | 全パラメータをデフォルト（空文字/None）にして `search_devices(params, user_id=1)` を呼び出す | フィルタ引数にテキスト検索値（`'DEV'`, `'センサー'`）が含まれないこと |
| 18 | 3.1.3.1 ページング・件数制御 | `page=2, per_page=25` を指定して `search_devices(params, user_id=1)` を呼び出す | `limit()` と `offset()` がそれぞれ1回以上呼ばれること |
| 19 | 3.1.4.1 検索結果戻り値（複数件） | `q.all.return_value=[device1, device2]`, `q.count.return_value=2` として `search_devices(params, user_id=1)` を呼び出す | 戻り値がリスト2件・件数2のタプル `(devices, total)` であること |
| 20 | 3.1.4.2 検索結果戻り値（0件） | `q.all.return_value=[]`, `q.count.return_value=0` として `search_devices(params, user_id=1)` を呼び出す | 戻り値が空リスト・件数0のタプル `([], 0)` であること |
| 21 | 3.1.1.2 検索条件指定（全条件） | 全検索条件（device_id/device_name/device_type_id/location/organization_id/status='connected'）を指定して `search_devices(params, user_id=1)` を呼び出す | フィルタ引数に各検索値（`'DEV-001'`, `'センサー'`, `'本社'`）が全て含まれること |
| 22 | 3.1.1.3 検索条件指定（一部条件のみ） | `device_id='DEV-001'` のみ指定し他はデフォルトで `search_devices(params, user_id=1)` を呼び出す | フィルタ引数に `'DEV-001'` が含まれ、未指定条件のデフォルト値（空文字）がフィルタ値として含まれないこと |
| 23 | 3.1.1.4 条件結合（AND） | `device_id='DEV-001'`, `device_name='センサー'`, `location='本社'` を指定して `search_devices(params, user_id=1)` を呼び出す | `filter()` が2回以上呼ばれること（条件ごとのチェーンによるAND結合） |
| 24 | 3.1.1.5 条件結合（OR含まれない） | `device_id='DEV-001'`, `device_name='センサー'` を指定して `search_devices(params, user_id=1)` を呼び出す | フィルタ引数に `'or_'` または `' OR '` が含まれないこと |
| 25 | 1.3.1 例外伝播（DBクエリエラー） | `DeviceMasterByUser.query.filter/filter_by/join` が例外を発生させるモックを設定し、全デフォルトパラメータで `search_devices(params, user_id=1)` を呼び出す | `Exception('DB接続エラー')` が呼び出し元へ伝播すること |
| 26 | 3.1.1.1 検索条件指定（status='connected'） | `DeviceMasterByUser.query` をモック化し `status='connected'` を指定して `search_devices(params, user_id=1)` を呼び出す | `filter()` が1回以上呼ばれること |
| 27 | 3.1.1.1 検索条件指定（status='disconnected'） | `DeviceMasterByUser.query` をモック化し `status='disconnected'` を指定して `search_devices(params, user_id=1)` を呼び出す | `filter()` が1回以上呼ばれること |
| 28 | 3.1.1.1 検索条件指定（certificate_expiration_date） | `DeviceMasterByUser.query` をモック化し `certificate_expiration_date=date(2025,12,31)` を指定して `search_devices(params, user_id=1)` を呼び出す | `filter()` が1回以上呼ばれること |

---

## TestValidateDeviceDataRequired

| No | テスト観点 | 操作手順 | 予想結果 |
|----|-----------|---------|---------|
| 28 | 1.1.1 必須チェック（device_uuid, 空文字） | `device_uuid=''` を含むデータで `validate_device_data(data, is_create=True)` を呼び出す | `ValidationError` がスローされること |
| 29 | 1.1.2 必須チェック（device_uuid, None） | `device_uuid=None` を含むデータで `validate_device_data(data, is_create=True)` を呼び出す | `ValidationError` がスローされること |
| 30 | 1.1.1 必須チェック（device_name, 空文字） | `device_name=''` を含むデータで `validate_device_data(data, is_create=True)` を呼び出す | `ValidationError` がスローされること |
| 31 | 1.1.2 必須チェック（device_name, None） | `device_name=None` を含むデータで `validate_device_data(data, is_create=True)` を呼び出す | `ValidationError` がスローされること |
| 32 | 1.1.2 必須チェック（device_type_id, None） | `device_type_id=None` を含むデータで `validate_device_data(data, is_create=True)` を呼び出す | `ValidationError` がスローされること |
| 33 | 1.1.2 必須チェック（organization_id, None） | `organization_id=None` を含むデータで `validate_device_data(data, is_create=True)` を呼び出す | `ValidationError` がスローされること |
| 34 | 1.1.4 必須チェック（device_name, 空白のみ） | `device_name='   '` を含むデータで `validate_device_data(data, is_create=True)` を呼び出す | 必須チェックでは例外が発生しないこと（空白文字列は「入力あり」扱い）※要確認 |
| 35 | 1.1.1 必須チェック（device_model, 空文字） | `device_model=''` を含むデータで `validate_device_data(data, is_create=True)` を呼び出す | `ValidationError` がスローされること |
| 36 | 1.1.2 必須チェック（device_model, None） | `device_model=None` を含むデータで `validate_device_data(data, is_create=True)` を呼び出す | `ValidationError` がスローされること |

---

## TestValidateDeviceDataMaxLength

| No | テスト観点 | 操作手順 | 予想結果 |
|----|-----------|---------|---------|
| 37 | 1.2.1 最大長-1（device_uuid, 127文字） | `device_uuid='A'*127` で `validate_device_data(data, is_create=True)` を呼び出す | 例外が発生しないこと |
| 38 | 1.2.2 最大長（device_uuid, 128文字） | `device_uuid='A'*128` で `validate_device_data(data, is_create=True)` を呼び出す | 例外が発生しないこと |
| 39 | 1.2.3 最大長+1（device_uuid, 129文字） | `device_uuid='A'*129` で `validate_device_data(data, is_create=True)` を呼び出す | `ValidationError` がスローされること |
| 40 | 1.2.1 最大長-1（device_name, 99文字） | `device_name='あ'*99` で `validate_device_data(data, is_create=True)` を呼び出す | 例外が発生しないこと |
| 41 | 1.2.2 最大長（device_name, 100文字） | `device_name='あ'*100` で `validate_device_data(data, is_create=True)` を呼び出す | 例外が発生しないこと |
| 42 | 1.2.3 最大長+1（device_name, 101文字） | `device_name='あ'*101` で `validate_device_data(data, is_create=True)` を呼び出す | `ValidationError` がスローされること |
| 43 | 1.2.1 最大長-1（device_model, 99文字） | `device_model='M'*99` で `validate_device_data(data, is_create=True)` を呼び出す | 例外が発生しないこと |
| 44 | 1.2.2 最大長（device_model, 100文字） | `device_model='M'*100` で `validate_device_data(data, is_create=True)` を呼び出す | 例外が発生しないこと |
| 45 | 1.2.3 最大長+1（device_model, 101文字） | `device_model='M'*101` で `validate_device_data(data, is_create=True)` を呼び出す | `ValidationError` がスローされること |
| 46 | 1.2.1 最大長-1（sim_id, 19文字） | `sim_id='1'*19` で `validate_device_data(data, is_create=True)` を呼び出す | 例外が発生しないこと |
| 47 | 1.2.2 最大長（sim_id, 20文字） | `sim_id='1'*20` で `validate_device_data(data, is_create=True)` を呼び出す | 例外が発生しないこと |
| 48 | 1.2.3 最大長+1（sim_id, 21文字） | `sim_id='1'*21` で `validate_device_data(data, is_create=True)` を呼び出す | `ValidationError` がスローされること |
| 49 | 1.2.1 最大長-1（device_location, 99文字） | `device_location='あ'*99` で `validate_device_data(data, is_create=True)` を呼び出す | 例外が発生しないこと |
| 50 | 1.2.2 最大長（device_location, 100文字） | `device_location='あ'*100` で `validate_device_data(data, is_create=True)` を呼び出す | 例外が発生しないこと |
| 51 | 1.2.3 最大長+1（device_location, 101文字） | `device_location='あ'*101` で `validate_device_data(data, is_create=True)` を呼び出す | `ValidationError` がスローされること |
| 52 | 1.2.4 空文字（device_model） | `device_model=''` で `validate_device_data(data, is_create=True)` を呼び出す | 例外が発生しないこと（任意項目、空文字は文字列長0で最大値以下） |
| 53 | 1.2.4 空文字（sim_id） | `sim_id=''` で `validate_device_data(data, is_create=True)` を呼び出す | 例外が発生しないこと（任意項目、空文字は文字列長0で最大値以下） |
| 54 | 1.2.4 空文字（device_location） | `device_location=''` で `validate_device_data(data, is_create=True)` を呼び出す | 例外が発生しないこと（任意項目、空文字は文字列長0で最大値以下） |

---

## TestValidateDeviceDataFormat

| No | テスト観点 | 操作手順 | 予想結果 |
|----|-----------|---------|---------|
| 55 | 1.6.1 不整値チェック（device_uuid, 英数字+ハイフン） | `device_uuid='ABC-123-def'` で `validate_device_data(data, is_create=True)` を呼び出す | 例外が発生しないこと |
| 56 | 1.6.2 不整値チェック（device_uuid, アンダースコア含む） | `device_uuid='DEV_001'` で `validate_device_data(data, is_create=True)` を呼び出す | `ValidationError` がスローされること |
| 57 | 1.6.2 不整値チェック（device_uuid, ドット含む） | `device_uuid='DEV.001'` で `validate_device_data(data, is_create=True)` を呼び出す | `ValidationError` がスローされること |
| 58 | 1.6.2 不整値チェック（device_uuid, スペース含む） | `device_uuid='DEV 001'` で `validate_device_data(data, is_create=True)` を呼び出す | `ValidationError` がスローされること |
| 59 | 1.6.1 不整値チェック（mac_address, 正常形式） | `mac_address='AA:BB:CC:DD:EE:FF'` で `validate_device_data(data, is_create=True)` を呼び出す | 例外が発生しないこと |
| 60 | 1.6.1 不整値チェック（mac_address, 小文字） | `mac_address='aa:bb:cc:dd:ee:ff'` で `validate_device_data(data, is_create=True)` を呼び出す | 例外が発生しないこと |
| 61 | 1.6.2 不整値チェック（mac_address, ハイフン区切り） | `mac_address='AA-BB-CC-DD-EE-FF'` で `validate_device_data(data, is_create=True)` を呼び出す | `ValidationError` がスローされること |
| 62 | 1.6.2 不整値チェック（mac_address, 16進数以外の文字） | `mac_address='GG:HH:II:JJ:KK:LL'` で `validate_device_data(data, is_create=True)` を呼び出す | `ValidationError` がスローされること |
| 63 | 1.6.2 不整値チェック（mac_address, セグメント5つ） | `mac_address='AA:BB:CC:DD:EE'` で `validate_device_data(data, is_create=True)` を呼び出す | `ValidationError` がスローされること |
| 64 | 1.6.3 不整値チェック（mac_address, 空文字） | `mac_address=''` で `validate_device_data(data, is_create=True)` を呼び出す | `ValidationError` がスローされること（空文字は形式不適合） |
| 65 | 1.1.4 不整値チェック（mac_address, None） | `mac_address=None` で `validate_device_data(data, is_create=True)` を呼び出す | 例外が発生しないこと（mac_address は任意項目） |
| 66 | 1.1.3 正常系：全項目有効 | 全項目が有効な値のデータで `validate_device_data(data, is_create=True)` を呼び出す | 例外が発生しないこと |

---

## TestCreateDevice

| No | テスト観点 | 操作手順 | 予想結果 |
|----|-----------|---------|---------|
| 67 | 3.2.1.3 登録呼び出し制御（device_uuid重複） | `filter_by().first()` が既存デバイスを返すモックを設定し `create_device(data, user_id=1)` を呼び出す | `DuplicateDeviceIdError` がスローされ、`session.add` が呼ばれないこと |
| 68 | 3.2.1.3 登録呼び出し制御（mac_address重複） | device_uuid重複なし・mac_address重複ありとなるよう `filter_by` のside_effectを設定し `create_device(data, user_id=1)` を呼び出す | `DuplicateMacAddressError` がスローされ、`session.add` が呼ばれないこと |
| 69 | 3.2.1.1 / 3.2.2.1 正常系（DB登録） | 重複なしのモックを設定し有効なデータで `create_device(data, user_id=1)` を呼び出す | `session.add()` と `session.commit()` が各1回呼ばれること |
| 70 | 2.3.2 副作用チェック（DBエラー時rollback） | `session.commit` が例外を発生させるモックを設定し `create_device(data, user_id=1)` を呼び出す | 例外が伝播し `session.rollback()` が1回呼ばれること |
| 71 | 3.2.1.2 登録呼び出し（任意項目None） | 任意項目（sim_id/mac_address/device_location/certificate_expiration_date）をNoneにして `create_device(data, user_id=1)` を呼び出す | `session.add()` と `session.commit()` が各1回呼ばれること |
| 72 | 3.2.2.1 登録結果（デバイスオブジェクト返却） | `DeviceMaster()` が `device_uuid='DEV-001'` のインスタンスを返すモックを設定し `create_device(data, user_id=1)` を呼び出す | 戻り値が `None` でなく、`result.device_uuid` が `'DEV-001'` であること |
| 73 | 1.3.1 例外伝播（device_uuid重複チェックDBエラー） | `filter_by` が例外を発生させるモックを設定し `create_device(data, user_id=1)` を呼び出す | `Exception('DB接続エラー')` が伝播し `session.add` が呼ばれないこと |
| 74 | 1.3.1 例外伝播（mac_address重複チェックDBエラー） | device_uuid重複チェック後のmac_addressチェックで例外を発生させるside_effectを設定し `create_device(data, user_id=1)` を呼び出す | `Exception('mac_address DB クエリエラー')` が伝播し `session.add` が呼ばれないこと |
| 75 | 3.2.1.1 DB→UC登録順序（Sagaパターン） | `session.add/flush` と `UnityCatalogConnector.execute_dml` の呼び出し順を記録するside_effectを設定し `create_device(data, user_id=1)` を呼び出す | `'db'` のインデックスが `'unity_catalog'` のインデックスより小さいこと（DB flush→commit→UC の順） |
| 76 | 2.3.2 副作用チェック（UnityCatalogエラー時rollback） | `UnityCatalogConnector.execute_dml` が例外を発生させるモックを設定し `create_device(data, user_id=1)` を呼び出す | 例外が伝播し `session.add` が呼ばれ、`session.rollback()` が1回呼ばれること |
| 77 | 2.3.2 副作用チェック（DBコミット失敗時UCは呼ばれない） | `session.commit` が例外を発生させるモックを設定し `create_device(data, user_id=1)` を呼び出す | 例外が伝播し `UnityCatalogConnector.execute_dml` が呼ばれないこと |

---

## TestGetDeviceByUuid

| No | テスト観点 | 操作手順 | 予想結果 |
|----|-----------|---------|---------|
| 78 | 2.2.1 存在確認（存在するデバイス） | `db.session.query(...).filter(...).first()` がデバイスオブジェクトを返すモックを設定し `get_device_by_uuid('DEV-001', user_id=1)` を呼び出す | デバイスオブジェクトが返されること |
| 79 | 2.2.2 存在確認（存在しないID） | `q.first()` が `None` を返すモックを設定し `get_device_by_uuid('NONEXISTENT-001', user_id=1)` を呼び出す | `None` が返されること |
| 80 | 2.2.3 存在確認（論理削除済み） | `q.first()` が `None` を返すモックを設定し `get_device_by_uuid('DELETED-001', user_id=1)` を呼び出す | `None` が返されること（論理削除済みはフィルタで除外） |
| 81 | 1.3.1 例外伝播（DBエラー） | `db.session.query` が例外を発生させるモックを設定し `get_device_by_uuid('DEV-001', user_id=1)` を呼び出す | `Exception('DB接続エラー')` が伝播すること |
| 82 | データスコープ（組織外アクセス） | `q.first()` が `None` を返すモックを設定し `get_device_by_uuid('DEV-OTHER-ORG-001', user_id=1)` を呼び出す | `None` が返されること（スコープ外はNone返却、Viewがabort(404)） |
| 83 | 3.3.2.2相当 更新モーダル初期値（全フィールド） | 全フィールドが設定されたデバイスモックを返すよう設定し `get_device_by_uuid('DEV-001', user_id=1)` を呼び出す | `device_uuid/device_name/device_type_id/device_model/sim_id/mac_address/device_location/organization_id` の全フィールドが正しい値で返されること |

---

## TestUpdateDevice

| No | テスト観点 | 操作手順 | 予想結果 |
|----|-----------|---------|---------|
| 84 | 3.3.2.1 更新成功 | 既存デバイスを返すモックを設定し有効なデータで `update_device('DEV-001', data, user_id=1)` を呼び出す | `session.commit()` が1回呼ばれること |
| 85 | 3.3.1.3 更新呼び出し制御（mac_address重複） | 1回目は既存デバイス・2回目は別デバイスを返すside_effectを設定し `update_device('DEV-001', data, user_id=1)` を呼び出す | `ValidationError` がスローされ `session.commit` が呼ばれないこと |
| 86 | 2.2.2 存在確認（存在しないID） | `filter_by().first()` が `None` を返すモックを設定し `update_device('NONEXISTENT-001', data, user_id=1)` を呼び出す | `NotFoundError` がスローされること |
| 87 | 2.1.2 正常系：最小構成（任意項目全てNone） | 任意項目（device_model/sim_id/mac_address/device_location/certificate_expiration_date）を全てNoneにして `update_device('DEV-001', data, user_id=1)` を呼び出す | `session.commit()` が1回呼ばれること |
| 88 | 2.2.3 存在確認（論理削除済み） | `filter_by().first()` が `None` を返すモックを設定し `update_device('DELETED-001', data, user_id=1)` を呼び出す | `NotFoundError` がスローされること |
| 89 | 2.3.2 副作用チェック（DBエラー時rollback） | `session.commit` が例外を発生させるモックを設定し `update_device('DEV-001', data, user_id=1)` を呼び出す | 例外が伝播し `session.rollback()` が1回呼ばれること |
| 90 | 3.3.2.2 更新対象IDがRepositoryに渡される | 既存デバイスを返すモックを設定し `update_device('DEV-TARGET-001', data, user_id=1)` を呼び出す | `filter_by(device_uuid='DEV-TARGET-001')` が呼ばれること |
| 91 | 3.3.1.3 更新呼び出し制御（バリデーションエラー） | 既存デバイスを返すモックを設定し `device_name=''` のデータで `update_device('DEV-001', data, user_id=1)` を呼び出す | `ValidationError` がスローされ `session.commit` が呼ばれないこと |

---

## TestDeleteDevice

| No | テスト観点 | 操作手順 | 予想結果 |
|----|-----------|---------|---------|
| 92 | 3.4.1.1 / 3.4.2.1 削除成功 | `make_device_mock(delete_flag=False)` でデバイスオブジェクトを生成し `delete_device(device, deleter_id=1)` を呼び出す | `session.commit()` が1回呼ばれること |
| 93 | 2.3.2 副作用チェック（DBエラー時rollback） | `session.commit` が例外を発生させるモックを設定し `delete_device(device, deleter_id=1)` を呼び出す | 例外が伝播し `session.rollback()` が1回呼ばれること |
| 94 | 3.4.1.1 論理削除の実装確認（delete_flag=True） | `make_device_mock(delete_flag=False)` でデバイスオブジェクトを生成し `delete_device(device, deleter_id=1)` を呼び出す | デバイスの `delete_flag` が `True` に設定されること |
| 95 | 3.4.2.1 UnityCatalog削除順序（DB→UC） | DB commit と UC execute_dml の呼び出し順を記録するside_effectを設定し `delete_device(device, deleter_id=1)` を呼び出す | `'db_commit'` のインデックスが `'unity_catalog'` のインデックスより小さいこと |
| 96 | 2.3.2 副作用チェック（UnityCatalogエラー時rollback） | `UnityCatalogConnector.execute_dml` が例外を発生させるモックを設定し `delete_device(device, deleter_id=1)` を呼び出す | 例外が伝播し `session.rollback()` が1回呼ばれること |

---

## TestGenerateDevicesCsv

| No | テスト観点 | 操作手順 | 予想結果 |
|----|-----------|---------|---------|
| 97 | 3.5.3.1 UTF-8 BOM付き | `make_device_row()` で1件のタプルを生成し `generate_devices_csv([row])` を呼び出す | 戻り値バイト列の先頭3バイトが `b'\xef\xbb\xbf'` であること |
| 98 | 3.5.1.1 ヘッダー行出力（主要カラム） | `make_device_row()` で1件のタプルを生成し `generate_devices_csv([row])` を呼び出す | `utf-8-sig` でデコードした文字列に `'デバイスID'`, `'デバイス名'`, `'所属組織'` が含まれること |
| 99 | 3.5.1.4 列順序（先頭カラム） | `make_device_row()` で1件のタプルを生成し `generate_devices_csv([row])` を呼び出す | ヘッダー行の先頭カラムが `'デバイスID'` であること |
| 100 | 3.5.1.2 データ行出力（複数件） | `make_device_row()` で2件のタプルを生成し `generate_devices_csv([row1, row2])` を呼び出す | 空行除外後の行数がヘッダー1行＋データ2行＝計3行であること |
| 101 | 3.5.1.3 0件出力（ヘッダーのみ） | 空リストで `generate_devices_csv([])` を呼び出す | 空行除外後の行数が1行のみで、その行に `'デバイスID'` が含まれること |
| 102 | 3.5.2.1 カンマエスケープ | `make_device_row(device_name='センサー,1号機')` で `generate_devices_csv([row])` を呼び出す | CSV文字列に `'"センサー,1号機"'` が含まれること |
| 103 | 3.5.2.2 改行エスケープ | `make_device_row(device_name='センサー\n1号機')` で `generate_devices_csv([row])` を呼び出す | CSV文字列に `'"センサー\n1号機"'` が含まれること |
| 104 | 3.5.2.3 ダブルクォートエスケープ | `make_device_row(device_name='センサー"A"')` で `generate_devices_csv([row])` を呼び出す | CSV文字列に `'""'` が含まれること |
| 105 | 3.5.2.4 エスケープ不要 | `make_device_row(device_uuid='DEV-001', device_name='センサー1')` で `generate_devices_csv([row])` を呼び出す | CSV文字列に `'DEV-001'` と `'センサー1'` がそのまま含まれること |
| 106 | 3.5.3.2 日本語文字 | `make_device_row(device_name='温度センサー1号機')` で `generate_devices_csv([row])` を呼び出す | `utf-8-sig` デコード後に `'温度センサー1号機'` が文字化けなく含まれること |
| 107 | 3.5.3.3 特殊文字（絵文字） | `make_device_row(device_name='🌡️温度センサー', device_location='🏢本社ビル')` で `generate_devices_csv([row])` を呼び出す | `utf-8-sig` デコード後に絵文字が文字化けなく含まれること |
| 108 | 3.5.1.1 ヘッダー行出力（全7列） | `make_device_row()` で1件のタプルを生成し `generate_devices_csv([row])` を呼び出す | ヘッダー行に全7列（デバイスID・デバイス名・デバイス種別・設置場所・所属組織・証明書期限・ステータス）のカラム名が含まれること |
| 109 | 3.5.1.4 列順序（全7列） | `make_device_row()` で1件のタプルを生成し `generate_devices_csv([row])` を呼び出す | ヘッダー行のカラムが仕様通りの順序（デバイスID, デバイス名, デバイス種別, 設置場所, 所属組織, 証明書期限, ステータス）で並ぶこと |
| 110 | 3.5.1.2 データ行出力（Noneフィールドの空文字変換） | `make_device_row(device_location=None, organization_name=None, device_type_name=None)` で `generate_devices_csv([row])` を呼び出す | データ行に文字列 `'None'` が含まれないこと |

---

## TestGetDeviceFormOptions

| No | テスト観点 | 操作手順 | 予想結果 |
|----|-----------|---------|---------|
| 111 | 2.1.1 正常系（デバイス種別+組織+ソート項目返却） | DeviceTypeMaster・OrganizationMasterByUser・SortItemのDBクエリが各1件返すよう `db.session.query` をモック化し `get_device_form_options(user_id=1)` を呼び出す | 戻り値が `(device_types, orgs, sort_items)` の3要素タプルで各リストが正しく返されること |
| 112 | 3.1.1.1 OrganizationMasterByUser VIEW経由スコープ取得 | `db.session.query` の `side_effect` に `[q_dt, q_org, q_sort]` を設定し `get_device_form_options(user_id=5)` を呼び出す | 戻り値の `orgs` が VIEW 経由で取得したスコープ済み組織リスト（`[mock_scoped_org]`）であること |
| 113 | 2.1.1 正常系（SortItem取得） | SortItemのDBクエリが2件返すよう `db.session.query` をモック化し `get_device_form_options(user_id=1)` を呼び出す | 戻り値の `sort_items` が `[mock_sort1, mock_sort2]` であること |
| 114 | 1.3.1 例外伝播（DBエラー・先頭クエリ） | `db.session.query` が例外を発生させるモックを設定し `get_device_form_options(user_id=1)` を呼び出す | `Exception('DB接続エラー')` が呼び出し元に伝播すること |
| 115 | 1.3.1 例外伝播（デバイス種別マスタDBエラー） | 先頭クエリは成功・2番目のクエリで例外が発生するモックを設定し `get_device_form_options(user_id=1)` を呼び出す | `Exception('デバイス種別DB取得エラー')` が呼び出し元に伝播すること |
| 116 | 3.1.4.2 検索結果（0件） | デバイス種別・組織・ソート項目ともに `all()` が空リストを返すモックを設定し `get_device_form_options(user_id=1)` を呼び出す | 戻り値が `([], [], [])` であること |

---

## TestGetAllDevicesForExport

| No | テスト観点 | 操作手順 | 予想結果 |
|----|-----------|---------|---------|
| 117 | 3.1.6.1 全件取得（フィルタなし） | デフォルトの検索パラメータで `get_all_devices_for_export(params, user_id=1)` を呼び出す | `q.all()` の戻り値（全デバイスリスト）がそのまま返されること |
| 118 | 3.1.6.1 検索条件指定（device_id, LIKE） | `device_id='DEV-001'` を指定して `get_all_devices_for_export(params, user_id=1)` を呼び出す | `filter()` が呼ばれること |
| 119 | 3.1.6.1 検索条件指定（device_name, LIKE） | `device_name='センサー'` を指定して `get_all_devices_for_export(params, user_id=1)` を呼び出す | `filter()` が呼ばれること |
| 120 | 3.1.6.1 検索条件指定（device_type_id） | `device_type_id=2` を指定して `get_all_devices_for_export(params, user_id=1)` を呼び出す | `filter()` が呼ばれること |
| 121 | 3.1.6.1 検索条件指定（location, LIKE） | `location='東京'` を指定して `get_all_devices_for_export(params, user_id=1)` を呼び出す | `filter()` が呼ばれること |
| 122 | 3.1.6.1 検索条件指定（organization_id） | `organization_id=3` を指定して `get_all_devices_for_export(params, user_id=1)` を呼び出す | `filter()` が呼ばれること |
| 123 | 3.1.6.1 検索条件指定（certificate_expiration_date） | `certificate_expiration_date='2025-12-31'` を指定して `get_all_devices_for_export(params, user_id=1)` を呼び出す | `filter()` が呼ばれること |
| 124 | 3.1.6.1 検索条件指定（status='connected'） | `status='connected'` と `current_app.config['DEVICE_DATA_INTERVAL_SECONDS']=300` を設定して `get_all_devices_for_export(params, user_id=1)` を呼び出す | `filter()` が呼ばれること |
| 125 | 3.1.6.1 検索条件指定（status='disconnected'） | `status='disconnected'` と `current_app.config['DEVICE_DATA_INTERVAL_SECONDS']=300` を設定して `get_all_devices_for_export(params, user_id=1)` を呼び出す | `filter()` が呼ばれること |
| 126 | 3.1.4.2 0件返却 | `q.all.return_value=[]` として `get_all_devices_for_export(params, user_id=1)` を呼び出す | 空リストが返されること |
| 127 | 1.3.1 例外伝播（DBエラー） | `db.session.query` が例外を発生させるモックを設定し `get_all_devices_for_export(params, user_id=1)` を呼び出す | `Exception('DB接続エラー')` が伝播すること |

---

## TestGetDeviceStatusLabel

| No | テスト観点 | 操作手順 | 予想結果 |
|----|-----------|---------|---------|
| 128 | 3.1.7.1 last_received_time が None | `_get_device_status_label(None)` を呼び出す | `'未接続'` が返されること |
| 129 | 3.1.7.1 elapsed <= threshold * 2 | `now - last_received_time = 300秒`、`threshold=300` として `_get_device_status_label(last_received_time)` を呼び出す | `'接続済み'` が返されること（elapsed=300 <= 600） |
| 130 | 3.1.7.2 elapsed > threshold * 2 | `now - last_received_time = 700秒`、`threshold=300` として `_get_device_status_label(last_received_time)` を呼び出す | `'未接続'` が返されること（elapsed=700 > 600） |
| 131 | 3.1.7.3 境界値（elapsed = threshold * 2） | `now - last_received_time = 600秒`、`threshold=300` として `_get_device_status_label(last_received_time)` を呼び出す | `'接続済み'` が返されること（elapsed=600 == 600、境界値は接続済み） |
| 132 | 3.1.7.4 境界値（elapsed = threshold * 2 + 1） | `now - last_received_time = 601秒`、`threshold=300` として `_get_device_status_label(last_received_time)` を呼び出す | `'未接続'` が返されること（elapsed=601 > 600） |
