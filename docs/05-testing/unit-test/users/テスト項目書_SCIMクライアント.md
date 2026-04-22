# テスト項目書 - SCIMクライアント

**対象ファイル:** `tests/unit/databricks/test_scim_client.py`
**対象モジュール:** `iot_app.databricks.scim_client`
**テスト総数:** 21件

---

## TestScimClientCreateUser

`ScimClient.create_user()` はDatabricks SCIM API の `/Users` エンドポイントにPOSTしてユーザーを作成し、採番されたDatabricksUUIDを返す。

| No | テスト観点 | 操作手順 | 予想結果 |
| -- | ---------- | -------- | -------- |
| 1 | 3.2.2.1 登録結果（id返却） | `requests.post` が `{'id': 'new-scim-uid', ...}` を含むモックレスポンスを返すよう設定し、`client.create_user('test@example.com', display_name='テストユーザー')` を呼ぶ | 戻り値が `'new-scim-uid'` であること |
| 2 | 3.2.1.1 登録処理呼び出し（SCIM /Users エンドポイント） | `requests.post` のモックを設定し、`client.create_user('u@u.com', display_name='ユーザー')` を呼ぶ | `requests.post` が呼ばれ、呼び出しURLが `'{self.host}/api/2.0/preview/scim/v2/Users'` と一致すること |
| 3 | 3.2.1.1 登録処理呼び出し（リクエストボディ内容） | `requests.post` のモックを設定し、`client.create_user('t@e.com', display_name='テスト名')` を呼ぶ | POSTのjsonボディが `{'schemas': ['urn:ietf:params:scim:schemas:core:2.0:User'], 'userName': 't@e.com', 'displayName': 'テスト名'}` と完全一致すること |
| 4 | 1.3.1 エラーハンドリング（API 4xxエラー） | `requests.post` のレスポンスが `status_code=400`、`raise_for_status` が例外を投げるよう設定し、`client.create_user('bad@bad.com', display_name='エラー')` を呼ぶ | 例外が伝播すること |
| 5 | 1.3.1 エラーハンドリング（API 5xxエラー） | `requests.post` のレスポンスが `status_code=500`、`raise_for_status` が例外を投げるよう設定し、`client.create_user('test@example.com', display_name='テスト')` を呼ぶ | 例外が伝播すること |
| 6 | 3.2.2.1 登録結果（id キー欠如） | `requests.post` が `status_code=201`、`json()` が `{'userName': 'test@example.com'}`（id なし）を返すよう設定し、`client.create_user('test@example.com', display_name='テスト')` を呼ぶ | 例外が発生すること |
| 7 | 3.2.1.1 登録処理呼び出し（認証ヘッダ） | `requests.post` のモックを設定し、`client.create_user('a@a.com', display_name='A')` を呼ぶ | `requests.post` 呼び出し時の `headers` 引数が `client.headers` と一致すること |

---

## TestScimClientUpdateUser

`ScimClient.update_user()` はDatabricks SCIM API の `/Users/{id}` エンドポイントにPATCHして表示名・有効状態を更新する。

| No | テスト観点 | 操作手順 | 予想結果 |
| -- | ---------- | -------- | -------- |
| 8 | 3.3.1.1 更新処理呼び出し（SCIM /Users/{id} PATCH） | `requests.patch` のモックを設定し、`client.update_user('uid-1', display_name='更新名', status=1)` を呼ぶ | `requests.patch` が呼ばれ、呼び出しURLに `'uid-1'` が含まれること |
| 9 | 3.3.1.1 更新処理呼び出し（status=0 → active=False） | `requests.patch` のモックを設定し、`client.update_user('uid-1', display_name='名前', status=0)` を呼ぶ | PATCHのjsonボディの `Operations` 配列中 `path='active'` の操作の `value` が `False` であること |
| 10 | 3.3.1.1 更新処理呼び出し（status=1 → active=True） | `requests.patch` のモックを設定し、`client.update_user('uid-1', display_name='名前', status=1)` を呼ぶ | PATCHのjsonボディの `Operations` 配列中 `path='active'` の操作の `value` が `True` であること |
| 11 | 1.3.1 エラーハンドリング（API 4xxエラー） | `requests.patch` のレスポンスが `status_code=404`、`raise_for_status` が例外を投げるよう設定し、`client.update_user('bad-uid', display_name='名前', status=1)` を呼ぶ | 例外が伝播すること |
| 12 | 3.3.1.1 更新処理呼び出し（認証ヘッダ） | `requests.patch` のモックを設定し、`client.update_user('uid-1', display_name='名前', status=1)` を呼ぶ | `requests.patch` 呼び出し時の `headers` 引数が `client.headers` と一致すること |

---

## TestScimClientDeleteUser

`ScimClient.delete_user()` はDatabricks SCIM API の `/Users/{id}` エンドポイントにDELETEしてユーザーを削除する。

| No | テスト観点 | 操作手順 | 予想結果 |
| -- | ---------- | -------- | -------- |
| 13 | 3.4.1.1 削除処理呼び出し（SCIM /Users/{id} DELETE） | `requests.delete` のモックを設定し、`client.delete_user('uid-to-delete')` を呼ぶ | `requests.delete` が呼ばれること |
| 14 | 3.4.2.2 削除結果（URLにuser_id含む） | `requests.delete` のモックを設定し、`client.delete_user('target-uid-999')` を呼ぶ | DELETEの呼び出しURLに `'target-uid-999'` が含まれること |
| 15 | 1.3.1 エラーハンドリング（API 4xxエラー） | `requests.delete` のレスポンスが `status_code=404`、`raise_for_status` が例外を投げるよう設定し、`client.delete_user('nonexistent-uid')` を呼ぶ | 例外が伝播すること |
| 16 | 3.4.1.1 削除処理呼び出し（認証ヘッダ） | `requests.delete` のモックを設定し、`client.delete_user('uid-to-delete')` を呼ぶ | `requests.delete` 呼び出し時の `headers` 引数が `client.headers` と一致すること |

---

## TestScimClientAddUserToGroup

`ScimClient.add_user_to_group()` はDatabricks SCIM API の `/Groups/{id}` エンドポイントにPATCHしてユーザーをグループに追加する。

| No | テスト観点 | 操作手順 | 予想結果 |
| -- | ---------- | -------- | -------- |
| 17 | 3.2.1.1 登録処理呼び出し（SCIM /Groups/{id} PATCH） | `requests.patch` のモックを設定し、`client.add_user_to_group('group-gid', 'user-uid')` を呼ぶ | `requests.patch` が呼ばれ、呼び出しURLが `'/scim/v2/Groups/group-gid'` で終わること |
| 18 | 3.2.1.1 登録処理呼び出し（URLにgroup_id含む） | `requests.patch` のモックを設定し、`client.add_user_to_group('workspace-group-id', 'user-uid')` を呼ぶ | PATCHの呼び出しURLに `'workspace-group-id'` が含まれること |
| 19 | 3.2.1.1 登録処理呼び出し（リクエストボディ内容） | `requests.patch` のモックを設定し、`client.add_user_to_group('group-gid', 'user-uid-123')` を呼ぶ | PATCHのjsonボディが `{'schemas': ['urn:ietf:params:scim:api:messages:2.0:PatchOp'], 'Operations': [{'op': 'add', 'value': {'members': [{'value': 'user-uid-123'}]}}]}` と完全一致すること |
| 20 | 1.3.1 エラーハンドリング（API 4xxエラー） | `requests.patch` のレスポンスが `status_code=400`、`raise_for_status` が例外を投げるよう設定し、`client.add_user_to_group('group-gid', 'user-uid')` を呼ぶ | 例外が伝播すること |
| 21 | 3.2.1.1 登録処理呼び出し（認証ヘッダ） | `requests.patch` のモックを設定し、`client.add_user_to_group('group-gid', 'user-uid')` を呼ぶ | `requests.patch` 呼び出し時の `headers` 引数が `client.headers` と一致すること |
