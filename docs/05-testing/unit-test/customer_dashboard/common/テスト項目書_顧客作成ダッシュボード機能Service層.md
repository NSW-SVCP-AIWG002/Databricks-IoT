# テスト項目書 - 顧客作成ダッシュボード共通機能 Service層

- **対象ファイル**: `src/iot_app/services/customer_dashboard/common.py`
- **テストコード**: `tests/unit/services/customer_dashboard/test_common.py`
- **観点表**: `docs/05-testing/unit-test/unit-test-perspectives.md`
- **ワークフロー仕様書**: `docs/03-features/flask-app/customer-dashboard/common/workflow-specification.md`

---

## 対応表

テストクラスと、ワークフロー仕様書の各ワークフロー・処理フロー項目の対応を示します。

| テストクラス | テスト項目No. | 対応ワークフロー | 処理フロー項目 | エンドポイント |
|------------|:---:|--------------|-------------|-------------|
| TestGetDashboardUserSetting | 1〜2 | ダッシュボード初期表示<br>レイアウト保存 | 初期表示 ③ ダッシュボードユーザー設定取得<br>レイアウト保存 ① ダッシュボードユーザー設定取得 | `GET /analysis/customer-dashboard`<br>`POST /analysis/customer-dashboard/layout/save` |
| TestUpsertDashboardUserSetting | 3〜4 | ダッシュボード初期表示<br>ダッシュボード登録<br>ダッシュボード表示切替<br>ダッシュボード削除 | 初期表示 ③ ユーザー設定自動登録<br>登録 ② ユーザー設定更新<br>表示切替（ユーザー設定更新）<br>削除（次ダッシュボードあり時のユーザー設定更新） | `GET /analysis/customer-dashboard`<br>`POST .../dashboards/register`<br>`POST .../dashboards/<uuid>/switch`<br>`POST .../dashboards/<uuid>/delete` |
| TestGetFirstDashboard | 5〜8 | ダッシュボード初期表示<br>ダッシュボード削除 | 初期表示 ③ 先頭ダッシュボード取得<br>削除（次ダッシュボード取得） | `GET /analysis/customer-dashboard`<br>`POST .../dashboards/<uuid>/delete` |
| TestGetDashboardById | 9〜10 | ダッシュボード初期表示<br>レイアウト保存 | 初期表示 ④ ダッシュボード情報取得（ID指定）<br>レイアウト保存 ② ダッシュボード情報取得 | `GET /analysis/customer-dashboard`<br>`POST /analysis/customer-dashboard/layout/save` |
| TestGetDashboards | 11〜13 | ダッシュボード管理モーダル表示 | 管理モーダル ① ダッシュボード一覧取得 | `GET /analysis/customer-dashboard/dashboards` |
| TestGetDashboardGroups | 14〜16 | ダッシュボード初期表示 | 初期表示 ⑤ ダッシュボードグループ一覧取得 | `GET /analysis/customer-dashboard` |
| TestGetGadgetsByGroups | 17〜18 | ダッシュボード初期表示 | 初期表示 ⑥ ガジェット一覧取得 | `GET /analysis/customer-dashboard` |
| TestGetOrganizations | 19〜21 | ダッシュボード初期表示 | 初期表示 ⑦ 組織選択肢取得 | `GET /analysis/customer-dashboard` |
| TestGetDevices | 22〜24 | ダッシュボード初期表示 | 初期表示 ⑧ デバイス選択肢取得 | `GET /analysis/customer-dashboard` |
| TestGetFixedGadgetDeviceNames | 25〜31 | ダッシュボード初期表示 | 初期表示 ⑨ ガジェット固定デバイス名取得 | `GET /analysis/customer-dashboard` |
| TestGetGadgetTypeIdBySlug | 32〜33 | ダッシュボード初期表示 | 初期表示 ⑩ gadget_type_ids 構築（slug → gadget_type_id 変換） | `GET /analysis/customer-dashboard` |
| TestCreateDashboard | 34〜37 | ダッシュボード登録 | 登録 ① ダッシュボード登録（INSERT） | `POST /analysis/customer-dashboard/dashboards/register` |
| TestGetDashboardByUuid | 38〜40 | ダッシュボード表示切替<br>ダッシュボードタイトル更新<br>ダッシュボード削除<br>ダッシュボードグループ登録 | 表示切替（スコープチェック）<br>タイトル更新 ① ダッシュボード取得（スコープチェック）<br>削除（スコープチェック）<br>グループ登録 ① ダッシュボード取得（スコープチェック） | `POST .../dashboards/<uuid>/switch`<br>`POST .../dashboards/<uuid>/update`<br>`POST .../dashboards/<uuid>/delete`<br>`POST .../groups/register` |
| TestUpdateDashboardTitle | 41〜42 | ダッシュボードタイトル更新 | タイトル更新 ④ ダッシュボードタイトル更新（UPDATE） | `POST /analysis/customer-dashboard/dashboards/<uuid>/update` |
| TestDeleteGadgetsByDashboard | 43〜45 | ダッシュボード削除 | 削除 ① 配下のガジェットを論理削除 | `POST /analysis/customer-dashboard/dashboards/<uuid>/delete` |
| TestDeleteGroupsByDashboard | 46〜48 | ダッシュボード削除 | 削除 ② 配下のグループを論理削除 | `POST /analysis/customer-dashboard/dashboards/<uuid>/delete` |
| TestDeleteDashboardWithCascade | 49〜52 | ダッシュボード削除 | 削除 ① 配下ガジェット論理削除<br>削除 ② 配下グループ論理削除<br>削除 ③ ダッシュボード論理削除<br>削除（ユーザー設定更新 or 論理削除） | `POST /analysis/customer-dashboard/dashboards/<uuid>/delete` |
| TestDeleteDashboardUserSetting | 53〜54 | ダッシュボード削除 | 削除 ③ ユーザー設定を論理削除（次ダッシュボードなし時） | `POST /analysis/customer-dashboard/dashboards/<uuid>/delete` |
| TestCreateDashboardGroup | 55〜59 | ダッシュボードグループ登録 | グループ登録 ④ ダッシュボードグループ登録（INSERT） | `POST /analysis/customer-dashboard/groups/register` |
| TestGetGroupByUuid | 60〜62 | ダッシュボードグループタイトル更新<br>ダッシュボードグループ削除 | グループタイトル更新 ① グループ取得（スコープチェック）<br>グループ削除 ①（スコープチェック） | `POST .../groups/<uuid>/update`<br>`POST .../groups/<uuid>/delete` |
| TestUpdateGroupTitle | 63〜64 | ダッシュボードグループタイトル更新 | グループタイトル更新 ④ グループタイトル更新（UPDATE） | `POST /analysis/customer-dashboard/groups/<uuid>/update` |
| TestDeleteGadgetsByGroup | 65〜67 | ダッシュボードグループ削除 | グループ削除 ① 配下のガジェットを論理削除 | `POST /analysis/customer-dashboard/groups/<uuid>/delete` |
| TestDeleteGroupWithCascade | 68〜70 | ダッシュボードグループ削除 | グループ削除 ① 配下のガジェットを論理削除<br>グループ削除 ② グループを論理削除 | `POST /analysis/customer-dashboard/groups/<uuid>/delete` |
| TestGetGadgetTypes | 71〜72 | ガジェット追加モーダル表示 | ガジェット追加 ① ガジェット種別一覧取得 | `GET /analysis/customer-dashboard/gadgets/add` |
| TestGetGadgetByUuid | 73〜75 | ガジェットタイトル更新<br>ガジェット削除 | ガジェットタイトル更新 ① ガジェット取得（スコープチェック）<br>ガジェット削除 ① ガジェット取得（スコープチェック） | `POST .../gadgets/<uuid>/update`<br>`POST .../gadgets/<uuid>/delete` |
| TestUpdateGadgetTitle | 76〜77 | ガジェットタイトル更新 | ガジェットタイトル更新 ④ ガジェットタイトル更新（UPDATE） | `POST /analysis/customer-dashboard/gadgets/<uuid>/update` |
| TestDeleteGadget | 78〜79 | ガジェット削除 | ガジェット削除 ③ ガジェットを論理削除（UPDATE） | `POST /analysis/customer-dashboard/gadgets/<uuid>/delete` |
| TestGetGadgetType | 80〜82 | ガジェットデータ取得<br>CSVエクスポート<br>自動更新 | ガジェット種別スラッグ取得（gadget_uuid → gadget_type_name） | `POST .../gadgets/<uuid>/data`<br>`GET .../gadgets/<uuid>?export=csv` |
| TestSaveLayout | 83〜86 | レイアウト保存 | レイアウト保存 ④ レイアウト情報更新（UPDATE） | `POST /analysis/customer-dashboard/layout/save` |
| TestGetDevicesByOrganization | 87〜88 | データソース選択（No.26） | データソース選択（組織選択変更時）デバイス一覧取得 | `GET /analysis/customer-dashboard/organizations/<org_id>/devices` |
| TestUpdateDatasourceSetting | 89〜92 | データソース選択（No.27） | データソース選択（デバイス選択変更時）ユーザー設定保存（organization_id / device_id 更新） | `POST /analysis/customer-dashboard/datasource/save` |

---

## ワークフロー別カバレッジ

ワークフロー仕様書の各ワークフローに対して、どのテストクラスが対応しているかを示します。

### ダッシュボード初期表示（GET /analysis/customer-dashboard）

| 処理フロー項目 | 対応テストクラス | テスト項目No. |
|-------------|--------------|:---:|
| ③ ダッシュボードユーザー設定取得 | TestGetDashboardUserSetting | 1〜2 |
| ③ ユーザー設定自動登録（未登録時） | TestUpsertDashboardUserSetting | 3〜4 |
| ③ 先頭ダッシュボード取得 | TestGetFirstDashboard | 5〜8 |
| ④ ダッシュボード情報取得（ID指定） | TestGetDashboardById | 9〜10 |
| ⑤ ダッシュボードグループ一覧取得 | TestGetDashboardGroups | 14〜16 |
| ⑥ ガジェット一覧取得 | TestGetGadgetsByGroups | 17〜18 |
| ⑦ 組織選択肢取得 | TestGetOrganizations | 19〜21 |
| ⑧ デバイス選択肢取得 | TestGetDevices | 22〜24 |
| ⑨ ガジェット固定デバイス名取得 | TestGetFixedGadgetDeviceNames | 25〜31 |
| ⑩ gadget_type_ids 構築 | TestGetGadgetTypeIdBySlug | 32〜33 |

### ダッシュボード管理モーダル表示（GET /analysis/customer-dashboard/dashboards）

| 処理フロー項目 | 対応テストクラス | テスト項目No. |
|-------------|--------------|:---:|
| ① ダッシュボード一覧取得 | TestGetDashboards | 11〜13 |

### ダッシュボード登録（POST /analysis/customer-dashboard/dashboards/register）

| 処理フロー項目 | 対応テストクラス | テスト項目No. |
|-------------|--------------|:---:|
| ① ダッシュボード登録（INSERT） | TestCreateDashboard | 34〜37 |
| ② ユーザー設定更新 | TestUpsertDashboardUserSetting | 3〜4 |

### ダッシュボード表示切替（POST /analysis/customer-dashboard/dashboards/\<uuid\>/switch）

| 処理フロー項目 | 対応テストクラス | テスト項目No. |
|-------------|--------------|:---:|
| ダッシュボード取得（スコープチェック） | TestGetDashboardByUuid | 38〜40 |
| ユーザー設定更新 | TestUpsertDashboardUserSetting | 3〜4 |

### ダッシュボードタイトル更新（POST /analysis/customer-dashboard/dashboards/\<uuid\>/update）

| 処理フロー項目 | 対応テストクラス | テスト項目No. |
|-------------|--------------|:---:|
| ① ダッシュボード取得（スコープチェック） | TestGetDashboardByUuid | 38〜40 |
| ④ ダッシュボードタイトル更新（UPDATE） | TestUpdateDashboardTitle | 41〜42 |

### ダッシュボード削除（POST /analysis/customer-dashboard/dashboards/\<uuid\>/delete）

| 処理フロー項目 | 対応テストクラス | テスト項目No. |
|-------------|--------------|:---:|
| ダッシュボード取得（スコープチェック） | TestGetDashboardByUuid | 38〜40 |
| ① 配下のガジェットを論理削除 | TestDeleteGadgetsByDashboard | 43〜45 |
| ② 配下のグループを論理削除 | TestDeleteGroupsByDashboard | 46〜48 |
| ③ ダッシュボードを論理削除 | TestDeleteDashboardWithCascade | 49〜52 |
| ③ ユーザー設定を論理削除（次ダッシュボードなし時） | TestDeleteDashboardUserSetting | 53〜54 |
| 次ダッシュボード取得 | TestGetFirstDashboard | 5〜8 |
| 次ダッシュボードあり時のユーザー設定更新 | TestUpsertDashboardUserSetting | 3〜4 |

### ダッシュボードグループ登録（POST /analysis/customer-dashboard/groups/register）

| 処理フロー項目 | 対応テストクラス | テスト項目No. |
|-------------|--------------|:---:|
| ① ダッシュボード取得（スコープチェック） | TestGetDashboardByUuid | 38〜40 |
| ④ ダッシュボードグループ登録（INSERT） | TestCreateDashboardGroup | 55〜59 |

### ダッシュボードグループタイトル更新（POST /analysis/customer-dashboard/groups/\<uuid\>/update）

| 処理フロー項目 | 対応テストクラス | テスト項目No. |
|-------------|--------------|:---:|
| ① グループ取得（スコープチェック） | TestGetGroupByUuid | 60〜62 |
| ④ グループタイトル更新（UPDATE） | TestUpdateGroupTitle | 63〜64 |

### ダッシュボードグループ削除（POST /analysis/customer-dashboard/groups/\<uuid\>/delete）

| 処理フロー項目 | 対応テストクラス | テスト項目No. |
|-------------|--------------|:---:|
| ① グループ取得（スコープチェック） | TestGetGroupByUuid | 60〜62 |
| ① 配下のガジェットを論理削除 | TestDeleteGadgetsByGroup | 65〜67 |
| ① ② カスケード論理削除 | TestDeleteGroupWithCascade | 68〜70 |

### ガジェット追加モーダル表示（GET /analysis/customer-dashboard/gadgets/add）

| 処理フロー項目 | 対応テストクラス | テスト項目No. |
|-------------|--------------|:---:|
| ① ガジェット種別一覧取得 | TestGetGadgetTypes | 71〜72 |

### ガジェットタイトル更新（POST /analysis/customer-dashboard/gadgets/\<uuid\>/update）

| 処理フロー項目 | 対応テストクラス | テスト項目No. |
|-------------|--------------|:---:|
| ① ガジェット取得（スコープチェック） | TestGetGadgetByUuid | 73〜75 |
| ④ ガジェットタイトル更新（UPDATE） | TestUpdateGadgetTitle | 76〜77 |

### ガジェット削除（POST /analysis/customer-dashboard/gadgets/\<uuid\>/delete）

| 処理フロー項目 | 対応テストクラス | テスト項目No. |
|-------------|--------------|:---:|
| ① ガジェット取得（スコープチェック） | TestGetGadgetByUuid | 73〜75 |
| ③ ガジェットを論理削除 | TestDeleteGadget | 78〜79 |

### ガジェットデータ取得・CSVエクスポート・自動更新

| 処理フロー項目 | 対応テストクラス | テスト項目No. |
|-------------|--------------|:---:|
| ガジェット種別スラッグ取得（gadget_uuid → gadget_type_name） | TestGetGadgetType | 80〜82 |

### レイアウト保存（POST /analysis/customer-dashboard/layout/save）

| 処理フロー項目 | 対応テストクラス | テスト項目No. |
|-------------|--------------|:---:|
| ① ダッシュボードユーザー設定取得 | TestGetDashboardUserSetting | 1〜2 |
| ② ダッシュボード情報取得 | TestGetDashboardById | 9〜10 |
| ④ レイアウト情報更新（UPDATE） | TestSaveLayout | 83〜86 |

### データソース選択

| 処理フロー項目 | 対応テストクラス | テスト項目No. | エンドポイント |
|-------------|--------------|:---:|-------------|
| No.26 組織選択変更時 デバイス一覧取得 | TestGetDevicesByOrganization | 87〜88 | `GET .../organizations/<org_id>/devices` |
| No.27 デバイス選択変更時 ユーザー設定保存 | TestUpdateDatasourceSetting | 89〜92 | `POST .../datasource/save` |

---

## テストクラス一覧

テストクラスに対して、テスト観点、操作手順、予想結果を示します。

### TestGetDashboardUserSetting

| No | テスト観点 | 操作手順 | 予想結果 |
|----|-----------|---------|---------|
| 1 | 2.2.1 対象データ存在チェック（対象IDが存在する） | `mock_setting`（dashboard_id=1を持つMagicMock）を用意し、`db.session.query().filter().first()` が `mock_setting` を返すようモックする。`get_dashboard_user_setting(1)` を呼び出す。 | `result` が `mock_setting` と同一オブジェクトである。 |
| 2 | 2.2.2 対象データ存在チェック（対象IDが存在しない） | `db.session.query().filter().first()` が `None` を返すようモックする。`get_dashboard_user_setting(999)` を呼び出す。 | `result` が `None` である。 |

---

### TestUpsertDashboardUserSetting

| No | テスト観点 | 操作手順 | 予想結果 |
|----|-----------|---------|---------|
| 3 | 3.2.1.1 登録処理呼び出し（正常な入力値） | `db.session.query().filter().first()` が `None` を返すようモックする（ユーザー設定なし）。`upsert_dashboard_user_setting(1, 1)` を呼び出す。 | `db.session.add()` が1回呼ばれる。追加オブジェクトの `dashboard_id==1`、`organization_id is None`、`device_id is None`、`creator==1`、`modifier==1` である。 |
| 4 | 3.3.1.1 更新処理呼び出し（正常な入力値） | `mock_setting`（dashboard_id=1）を用意し、`db.session.query().filter().first()` が返すようモックする（ユーザー設定あり）。`upsert_dashboard_user_setting(1, 99)` を呼び出す。 | `mock_setting.dashboard_id` が `99` に更新されている。`db.session.add()` は呼ばれない。 |

---

### TestGetFirstDashboard

| No | テスト観点 | 操作手順 | 予想結果 |
|----|-----------|---------|---------|
| 5 | 3.1.4.1 検索結果戻り値ハンドリング（正常系） | `mock_dash` を用意し、`db.session.query().filter().order_by().first()` が返すようモックする。`get_first_dashboard(1)` を呼び出す。 | `result` が `mock_dash` と同一オブジェクトである。 |
| 6 | 3.1.4.2 検索結果戻り値ハンドリング（空結果） | `db.session.query().filter().order_by().first()` が `None` を返すようモックする。`get_first_dashboard(1)` を呼び出す。 | `result` が `None` である。 |
| 7 | 3.1.1.1 検索条件指定（検索条件を指定） | `mock_dash` を用意し、`db.session.query().filter().filter().order_by().first()` が返すようモックする。`get_first_dashboard(1, exclude_id=3)` を呼び出す。 | `result` が `mock_dash` と同一オブジェクトである。`db.session.query().filter().filter` が呼ばれている（exclude_id除外用の追加フィルタが適用される）。 |
| 8 | 3.1.1.1 検索条件指定（検索条件を指定） | `db.session.query().filter().order_by().first()` が `None` を返すようモックする。`VDashboardMasterByUser` をインポートする。`get_first_dashboard(1)` を呼び出す。 | `filter` の引数に `VDashboardMasterByUser.user_id == 1` に相当するフィルタ式が含まれる。 |

---

### TestGetDashboardById

| No | テスト観点 | 操作手順 | 予想結果 |
|----|-----------|---------|---------|
| 9 | 2.2.1 対象データ存在チェック（対象IDが存在する） | `mock_dashboard`（dashboard_id=1を持つMagicMock）を用意し、`db.session.query().filter().first()` が `mock_dashboard` を返すようモックする。`get_dashboard_by_id(1)` を呼び出す。 | `result` が `mock_dashboard` と同一オブジェクトである。 |
| 10 | 2.2.2 対象データ存在チェック（対象IDが存在しない） | `db.session.query().filter().first()` が `None` を返すようモックする。`get_dashboard_by_id(999)` を呼び出す。 | `result` が `None` である。 |

---

### TestGetDashboards

| No | テスト観点 | 操作手順 | 予想結果 |
|----|-----------|---------|---------|
| 11 | 3.1.4.1 検索結果戻り値ハンドリング（正常系） | `mock_dash1`, `mock_dash2` を用意し、`db.session.query().filter().order_by().all()` が `[mock_dash1, mock_dash2]` を返すようモックする。`get_dashboards(1)` を呼び出す。 | `result == [mock_dash1, mock_dash2]` である。 |
| 12 | 3.1.4.2 検索結果戻り値ハンドリング（空結果） | `db.session.query().filter().order_by().all()` が `[]` を返すようモックする。`get_dashboards(1)` を呼び出す。 | `result == []` である。 |
| 13 | 3.1.1.1 検索条件指定（検索条件を指定） | `db.session.query().filter().order_by().all()` が `[]` を返すようモックする。`VDashboardMasterByUser` をインポートする。`get_dashboards(1)` を呼び出す。 | `db.session.query` が `VDashboardMasterByUser` を引数として1回呼ばれる。`filter` の引数に `VDashboardMasterByUser.user_id == 1` に相当するフィルタ式が含まれる。 |

---

### TestGetDashboardGroups

| No | テスト観点 | 操作手順 | 予想結果 |
|----|-----------|---------|---------|
| 14 | 3.1.1.1 検索条件指定（検索条件を指定） | `DashboardGroupMaster` をインポートする。`db.session.query().filter().order_by().all()` が `[]` を返すようモックする。`get_dashboard_groups(dashboard_id=1)` を呼び出す。 | `db.session.query` が `DashboardGroupMaster` を引数として1回呼ばれる。`db.session.query().filter` が1回呼ばれる。 |
| 15 | 3.1.4.1 検索結果戻り値ハンドリング（正常系） | `mock_group1`, `mock_group2` を用意し、`db.session.query().filter().order_by().all()` が `[mock_group1, mock_group2]` を返すようモックする。`get_dashboard_groups(dashboard_id=1)` を呼び出す。 | `result == [mock_group1, mock_group2]` である。 |
| 16 | 3.1.4.2 検索結果戻り値ハンドリング（空結果） | `db.session.query().filter().order_by().all()` が `[]` を返すようモックする。`get_dashboard_groups(dashboard_id=1)` を呼び出す。 | `result == []` である。 |

---

### TestGetGadgetsByGroups

| No | テスト観点 | 操作手順 | 予想結果 |
|----|-----------|---------|---------|
| 17 | 3.1.4.1 検索結果戻り値ハンドリング（正常系） | `mock_gadget1` を用意し、`db.session.query().filter().order_by().all()` が `[mock_gadget1]` を返すようモックする。`get_gadgets_by_groups([10, 20])` を呼び出す。 | `result == [mock_gadget1]` である。 |
| 18 | 3.1.2.1 検索条件未指定（全件相当） | `get_gadgets_by_groups([])` を呼び出す（`_get_devices_by_ids` のモックは不要）。 | `result == []` である。`db.session.query` は呼ばれない。 |

---

### TestGetOrganizations

| No | テスト観点 | 操作手順 | 予想結果 |
|----|-----------|---------|---------|
| 19 | 3.1.4.1 検索結果戻り値ハンドリング（正常系） | `g.current_user.user_id = 1` をモックする。`mock_org1`, `mock_org2` を用意し、`db.session.query().filter().order_by().all()` が `[mock_org1, mock_org2]` を返すようモックする。`get_organizations()` を呼び出す。 | `result == [mock_org1, mock_org2]` である。 |
| 20 | 2.2.2 対象データ存在チェック（対象IDが存在しない） | `g.current_user.user_id = 1` をモックする。`db.session.query().filter().order_by().all()` が `[]` を返すようモックする。`get_organizations()` を呼び出す。 | `result == []` である。 |
| 21 | 3.1.1.1 検索条件指定（検索条件を指定） | `g.current_user.user_id = 1` をモックする。`db.session.query().filter().order_by().all()` が `[]` を返すようモックする。`VOrganizationMasterByUser` をインポートする。`get_organizations()` を呼び出す。 | `filter` の引数に `VOrganizationMasterByUser.user_id == 1` に相当するフィルタ式が含まれる。 |

---

### TestGetDevices

| No | テスト観点 | 操作手順 | 予想結果 |
|----|-----------|---------|---------|
| 22 | 3.1.4.1 検索結果戻り値ハンドリング（正常系） | `mock_device1`, `mock_device2` を用意し、`db.session.query().filter().order_by().all()` が `[mock_device1, mock_device2]` を返すようモックする。`get_devices(1)` を呼び出す。 | `result == [mock_device1, mock_device2]` である。 |
| 23 | 2.2.2 対象データ存在チェック（対象IDが存在しない） | `db.session.query().filter().order_by().all()` が `[]` を返すようモックする。`get_devices(999)` を呼び出す。 | `result == []` である。 |
| 24 | 3.1.1.1 検索条件指定（検索条件を指定） | `db.session.query().filter().order_by().all()` が `[]` を返すようモックする。`DeviceMaster` をインポートする。`get_devices(1)` を呼び出す。 | `filter` の引数に `DeviceMaster.organization_id == 1` に相当するフィルタ式が含まれる。 |

---

### TestGetFixedGadgetDeviceNames

| No | テスト観点 | 操作手順 | 予想結果 |
|----|-----------|---------|---------|
| 25 | 1.1 ガジェット0件: 空dictを返す | `_get_devices_by_ids` をモックする。`get_fixed_gadget_device_names([])` を呼び出す。 | `result == {}` である。`_get_devices_by_ids` は呼ばれない。 |
| 26 | 1.2 全ガジェットが可変モード（device_id=null）: 空dictを返す | `_get_devices_by_ids` をモックする。`gadget_uuid='uuid-1'`・`data_source_config='{"device_id": null}'` と `gadget_uuid='uuid-2'`・`data_source_config='{"device_id": null}'` の2ガジェットMockを用意し、`get_fixed_gadget_device_names(gadgets)` を呼び出す。 | `result == {}` である。`_get_devices_by_ids` は呼ばれない。 |
| 27 | 1.3 固定モードのガジェット: device_nameを返す | `device.device_id=10`, `device.device_name='デバイスA'` を用意し `_get_devices_by_ids` が `[device]` を返すようモックする。`gadget_uuid='uuid-fixed'`・`data_source_config='{"device_id": 10}'` のガジェットMockを用意し、`get_fixed_gadget_device_names(gadgets)` を呼び出す。 | `result == {'uuid-fixed': 'デバイスA'}` である。 |
| 28 | 1.4 固定・可変モード混在: 固定モードのみ含む | `device.device_id=10`, `device.device_name='デバイスA'` を用意し `_get_devices_by_ids` が `[device]` を返すようモックする。固定モード（device_id=10）の `uuid-fixed` と可変モード（device_id=null）の `uuid-variable` の2ガジェットMockを用意し、`get_fixed_gadget_device_names(gadgets)` を呼び出す。 | `'uuid-fixed' in result` であり、`'uuid-variable' not in result` である。 |
| 29 | 1.5 固定モードだがデバイスがDB未存在（論理削除等）: '--'を返す | `_get_devices_by_ids` が `[]` を返すようモックする（デバイス未存在）。`gadget_uuid='uuid-1'`・`data_source_config='{"device_id": 99}'` のガジェットMockを用意し、`get_fixed_gadget_device_names(gadgets)` を呼び出す。 | `result == {'uuid-1': '--'}` である。 |
| 30 | 1.6 data_source_configがNone: そのガジェットをスキップする | `_get_devices_by_ids` をモックする。`gadget_uuid='uuid-1'`・`data_source_config=None` のガジェットMockを用意し、`get_fixed_gadget_device_names(gadgets)` を呼び出す。 | `result == {}` である。`_get_devices_by_ids` は呼ばれない。 |
| 31 | 1.7 data_source_configが不正JSON: そのガジェットをスキップする | `_get_devices_by_ids` をモックする。`gadget_uuid='uuid-1'`・`data_source_config='invalid-json'` のガジェットMockを用意し、`get_fixed_gadget_device_names(gadgets)` を呼び出す。 | `result == {}` である。`_get_devices_by_ids` は呼ばれない。 |

---

### TestGetGadgetTypeIdBySlug

| No | テスト観点 | 操作手順 | 予想結果 |
|----|-----------|---------|---------|
| 32 | 2.2.1 対象データ存在チェック（対象IDが存在する） | `mock_result.gadget_type_id = 6` を用意し、`db.session.query().filter_by().first()` が返すようモックする。`get_gadget_type_id_by_slug('bar-chart')` を呼び出す。 | `result == 6` である。 |
| 33 | 2.2.2 対象データ存在チェック（対象IDが存在しない） | `db.session.query().filter_by().first()` が `None` を返すようモックする。`get_gadget_type_id_by_slug('no-such-slug')` を呼び出す。 | `result is None` である。 |

---

### TestCreateDashboard

| No | テスト観点 | 操作手順 | 予想結果 |
|----|-----------|---------|---------|
| 34 | 3.2.1.1 登録処理呼び出し（正常な入力値） | `db.session.query().filter().scalar()` が `1` を返すようモックする（ユーザーのorganization_id取得用）。`create_dashboard('テストダッシュボード', user_id=1)` を呼び出す。 | `db.session.add()` が1回呼ばれる。 |
| 35 | 3.2.2.1 登録結果（ID返却） | `db.session.query().filter().scalar()` が `1` を返すようモックする。`create_dashboard('テストダッシュボード', user_id=1)` を呼び出し、`db.session.add.call_args[0][0]` で追加オブジェクトを取得する。 | 追加オブジェクトの `dashboard_uuid` が `None` でなく、`str()` に変換した長さが36文字（UUID形式）である。 |
| 36 | 3.2.2.1 登録結果（ID返却） | `db.session.query().filter().scalar()` が `1` を返すようモックする。`create_dashboard('テストダッシュボード', user_id=1)` を呼び出し、追加オブジェクトを取得する。 | 追加オブジェクトの `creator == 1`、`modifier == 1` である。 |
| 37 | 3.2.2.1 登録結果（ID返却） | `db.session.query().filter().scalar()` が `5` を返すようモックする（ユーザーの組織ID=5）。`create_dashboard('テストダッシュボード', user_id=1)` を呼び出し、追加オブジェクトを取得する。 | 追加オブジェクトの `organization_id == 5` である。 |

---

### TestGetDashboardByUuid

| No | テスト観点 | 操作手順 | 予想結果 |
|----|-----------|---------|---------|
| 38 | 2.2.1 対象データ存在チェック（対象IDが存在する） | `mock_dash` を用意し、`db.session.query().filter().first()` が返すようモックする。`get_dashboard_by_uuid('dash-uuid-001', 1)` を呼び出す。 | `result` が `mock_dash` と同一オブジェクトである。 |
| 39 | 2.2.2 対象データ存在チェック（対象IDが存在しない） | `db.session.query().filter().first()` が `None` を返すようモックする。`get_dashboard_by_uuid('no-such-uuid', 1)` を呼び出す。 | `result` が `None` である。 |
| 40 | 3.1.1.1 検索条件指定（検索条件を指定） | `db.session.query().filter().first()` が `None` を返すようモックする。`VDashboardMasterByUser` をインポートする。`get_dashboard_by_uuid('dash-uuid-001', 1)` を呼び出す。 | `filter` の引数に `VDashboardMasterByUser.user_id == 1` に相当するフィルタ式が含まれる。 |

---

### TestUpdateDashboardTitle

| No | テスト観点 | 操作手順 | 予想結果 |
|----|-----------|---------|---------|
| 41 | 3.3.1.1 更新処理呼び出し（正常な入力値） | `mock_dashboard = MagicMock()` を用意する。`update_dashboard_title(mock_dashboard, name='新しいタイトル', modifier=1)` を呼び出す。 | `mock_dashboard.dashboard_name == '新しいタイトル'` である。 |
| 42 | 3.3.2.1 更新結果（処理完了） | `mock_dashboard = MagicMock()` を用意する。`update_dashboard_title(mock_dashboard, name='タイトル', modifier=1)` を呼び出す。 | `mock_dashboard.modifier == 1` である。 |

---

### TestDeleteGadgetsByDashboard

| No | テスト観点 | 操作手順 | 予想結果 |
|----|-----------|---------|---------|
| 43 | 3.4.1.1 削除処理呼び出し（正常なIDを指定） | `mock_gadget1`, `mock_gadget2` を用意し、`db.session.query().join().filter().all()` が `[mock_gadget1, mock_gadget2]` を返すようモックする。`delete_gadgets_by_dashboard(dashboard_id=1, modifier=1)` を呼び出す。 | `mock_gadget1.delete_flag is True`、`mock_gadget2.delete_flag is True` である。 |
| 44 | 3.4.2.1 削除結果（処理完了） | `mock_gadget` を用意し、`db.session.query().join().filter().all()` が `[mock_gadget]` を返すようモックする。`delete_gadgets_by_dashboard(dashboard_id=1, modifier=1)` を呼び出す。 | `mock_gadget.modifier == 1` である。 |
| 45 | 3.1.4.2 検索結果戻り値ハンドリング（空結果） | `db.session.query().join().filter().all()` が `[]` を返すようモックする。`delete_gadgets_by_dashboard(dashboard_id=1, modifier=1)` を呼び出す。 | 例外が発生しない。 |

---

### TestDeleteGroupsByDashboard

| No | テスト観点 | 操作手順 | 予想結果 |
|----|-----------|---------|---------|
| 46 | 3.4.1.1 削除処理呼び出し（正常なIDを指定） | `mock_group1`, `mock_group2` を用意し、`db.session.query().filter().all()` が `[mock_group1, mock_group2]` を返すようモックする。`delete_groups_by_dashboard(dashboard_id=1, modifier=1)` を呼び出す。 | `mock_group1.delete_flag is True`、`mock_group2.delete_flag is True` である。 |
| 47 | 3.4.2.1 削除結果（処理完了） | `mock_group` を用意し、`db.session.query().filter().all()` が `[mock_group]` を返すようモックする。`delete_groups_by_dashboard(dashboard_id=1, modifier=1)` を呼び出す。 | `mock_group.modifier == 1` である。 |
| 48 | 3.1.4.2 検索結果戻り値ハンドリング（空結果） | `db.session.query().filter().all()` が `[]` を返すようモックする。`delete_groups_by_dashboard(dashboard_id=1, modifier=1)` を呼び出す。 | 例外が発生しない。 |

---

### TestDeleteDashboardWithCascade

| No | テスト観点 | 操作手順 | 予想結果 |
|----|-----------|---------|---------|
| 49 | 3.4.1.1 削除処理呼び出し（正常なIDを指定） | `delete_gadgets_by_dashboard`, `delete_groups_by_dashboard`, `get_first_dashboard`, `upsert_dashboard_user_setting`, `delete_dashboard_user_setting` をモックする。`get_first_dashboard` は `dashboard_id=2` を持つオブジェクトを返す。`mock_dashboard.dashboard_id=1` を用意し、`delete_dashboard_with_cascade(mock_dashboard, user_id=1)` を呼び出す。 | `delete_gadgets_by_dashboard(dashboard_id=1, modifier=1)` が1回呼ばれる。`delete_groups_by_dashboard(dashboard_id=1, modifier=1)` が1回呼ばれる。`get_first_dashboard(1, exclude_id=1)` が1回呼ばれる。 |
| 50 | 3.4.1.1 削除処理呼び出し（正常なIDを指定） | 上記5関数をモックする。`get_first_dashboard` が `None` を返すようモックする（次ダッシュボードなし）。`mock_dashboard.dashboard_id=1` を用意し、`delete_dashboard_with_cascade(mock_dashboard, user_id=1)` を呼び出す。 | `mock_dashboard.delete_flag is True`、`mock_dashboard.modifier == 1` である。`get_first_dashboard(1, exclude_id=1)` が1回呼ばれる。 |
| 51 | 3.4.4 次ダッシュボードへの切替（次ダッシュボードがある場合） | 上記5関数をモックする。`mock_next.dashboard_id=2` を持つオブジェクトを用意し、`get_first_dashboard` が返すようモックする。`mock_dashboard.dashboard_id=1` を用意し、`delete_dashboard_with_cascade(mock_dashboard, user_id=1)` を呼び出す。 | `get_first_dashboard(1, exclude_id=1)` が1回呼ばれる。`upsert_dashboard_user_setting(1, 2)` が1回呼ばれる。`delete_dashboard_user_setting` は呼ばれない。 |
| 52 | 3.4.4 次ダッシュボードへの切替（次ダッシュボードがない場合） | 上記5関数をモックする。`get_first_dashboard` が `None` を返すようモックする（次ダッシュボードなし）。`mock_dashboard.dashboard_id=1` を用意し、`delete_dashboard_with_cascade(mock_dashboard, user_id=1)` を呼び出す。 | `get_first_dashboard(1, exclude_id=1)` が1回呼ばれる。`delete_dashboard_user_setting(user_id=1, modifier=1)` が1回呼ばれる。`upsert_dashboard_user_setting` は呼ばれない。 |

---

### TestDeleteDashboardUserSetting

| No | テスト観点 | 操作手順 | 予想結果 |
|----|-----------|---------|---------|
| 53 | 3.4.1.1 削除処理呼び出し（正常なIDを指定） | `mock_setting = MagicMock()` を用意し、`db.session.query().filter().first()` が返すようモックする。`delete_dashboard_user_setting(user_id=1, modifier=1)` を呼び出す。 | `mock_setting.delete_flag is True` である。 |
| 54 | 3.4.2.1 削除結果（処理完了） | `mock_setting = MagicMock()` を用意し、`db.session.query().filter().first()` が返すようモックする。`delete_dashboard_user_setting(user_id=1, modifier=1)` を呼び出す。 | `mock_setting.modifier == 1` である。 |

---

### TestCreateDashboardGroup

| No | テスト観点 | 操作手順 | 予想結果 |
|----|-----------|---------|---------|
| 55 | 3.2.1.1 登録処理呼び出し（正常な入力値） | `create_dashboard_group(group_name='グループA', dashboard_id=1, user_id=1)` を呼び出す。 | `db.session.add()` が1回呼ばれる。 |
| 56 | 3.2.2.1 登録結果（ID返却） | `create_dashboard_group('グループA', dashboard_id=1, user_id=1)` を呼び出し、`db.session.add.call_args[0][0]` で追加オブジェクトを取得する。 | 追加オブジェクトの `creator == 1`、`modifier == 1` である。 |
| 57 | 3.2.2.1 登録結果（ID返却） | `create_dashboard_group('グループA', dashboard_id=1, user_id=1)` を呼び出し、追加オブジェクトを取得する。 | 追加オブジェクトの `dashboard_group_uuid` が `None` でなく、`str()` に変換した長さが36文字（UUID形式）である。 |
| 58 | 3.2.2.1 登録結果（ID返却） | `db.session.query().filter().scalar()` が `2` を返すようモックする（既存最大display_order=2）。`create_dashboard_group('グループA', dashboard_id=1, user_id=1)` を呼び出し、追加オブジェクトを取得する。 | 追加オブジェクトの `display_order == 3`（最大値2 + 1）である。 |
| 59 | 3.2.2.1 登録結果（ID返却） | `db.session.query().filter().scalar()` が `None` を返すようモックする（グループなし）。`create_dashboard_group('グループA', dashboard_id=1, user_id=1)` を呼び出し、追加オブジェクトを取得する。 | 追加オブジェクトの `display_order == 1` である。 |

---

### TestGetGroupByUuid

| No | テスト観点 | 操作手順 | 予想結果 |
|----|-----------|---------|---------|
| 60 | 2.2.1 対象データ存在チェック（対象IDが存在する） | `mock_group` を用意し、`db.session.query().filter().first()` が返すようモックする。`get_group_by_uuid('group-uuid-001', 1)` を呼び出す。 | `result` が `mock_group` と同一オブジェクトである。 |
| 61 | 2.2.2 対象データ存在チェック（対象IDが存在しない） | `db.session.query().filter().first()` が `None` を返すようモックする。`get_group_by_uuid('no-such-uuid', 1)` を呼び出す。 | `result` が `None` である。 |
| 62 | 3.1.1.1 検索条件指定（検索条件を指定） | `db.session.query().filter().first()` が `None` を返すようモックする。`VDashboardGroupMasterByUser` をインポートする。`get_group_by_uuid('group-uuid-001', 1)` を呼び出す。 | `filter` の引数に `VDashboardGroupMasterByUser.user_id == 1` に相当するフィルタ式が含まれる。 |

---

### TestUpdateGroupTitle

| No | テスト観点 | 操作手順 | 予想結果 |
|----|-----------|---------|---------|
| 63 | 3.3.1.1 更新処理呼び出し（正常な入力値） | `mock_group = MagicMock()` を用意する。`update_group_title(mock_group, name='新グループ名', modifier=1)` を呼び出す。 | `mock_group.dashboard_group_name == '新グループ名'` である。 |
| 64 | 3.3.2.1 更新結果（処理完了） | `mock_group = MagicMock()` を用意する。`update_group_title(mock_group, name='グループ名', modifier=1)` を呼び出す。 | `mock_group.modifier == 1` である。 |

---

### TestDeleteGadgetsByGroup

| No | テスト観点 | 操作手順 | 予想結果 |
|----|-----------|---------|---------|
| 65 | 3.4.1.1 削除処理呼び出し（正常なIDを指定） | `mock_gadget1`, `mock_gadget2` を用意し、`db.session.query().filter().all()` が `[mock_gadget1, mock_gadget2]` を返すようモックする。`delete_gadgets_by_group(group_id=10, modifier=1)` を呼び出す。 | `mock_gadget1.delete_flag is True`、`mock_gadget2.delete_flag is True` である。 |
| 66 | 3.4.2.1 削除結果（処理完了） | `mock_gadget` を用意し、`db.session.query().filter().all()` が `[mock_gadget]` を返すようモックする。`delete_gadgets_by_group(group_id=10, modifier=1)` を呼び出す。 | `mock_gadget.modifier == 1` である。 |
| 67 | 3.1.4.2 検索結果戻り値ハンドリング（空結果） | `db.session.query().filter().all()` が `[]` を返すようモックする。`delete_gadgets_by_group(group_id=10, modifier=1)` を呼び出す。 | 例外が発生しない。 |

---

### TestDeleteGroupWithCascade

| No | テスト観点 | 操作手順 | 予想結果 |
|----|-----------|---------|---------|
| 68 | 3.4.1.1 削除処理呼び出し（正常なIDを指定） | `delete_gadgets_by_group` をモックする。`mock_group.dashboard_group_id=10` を用意し、`delete_group_with_cascade(mock_group, user_id=1)` を呼び出す。 | `delete_gadgets_by_group(group_id=10, modifier=1)` が1回呼ばれる。 |
| 69 | 3.4.1.1 削除処理呼び出し（正常なIDを指定） | `delete_gadgets_by_group` をモックする。`mock_group.dashboard_group_id=10` を用意し、`delete_group_with_cascade(mock_group, user_id=1)` を呼び出す。 | `mock_group.delete_flag is True` である。 |
| 70 | 3.4.2.1 削除結果（処理完了） | `delete_gadgets_by_group` をモックする。`mock_group.dashboard_group_id=10` を用意し、`delete_group_with_cascade(mock_group, user_id=1)` を呼び出す。 | `mock_group.modifier == 1` である。 |

---

### TestGetGadgetTypes

| No | テスト観点 | 操作手順 | 予想結果 |
|----|-----------|---------|---------|
| 71 | 3.1.4.1 検索結果戻り値ハンドリング（正常系） | MagicMock 22個のリストを用意し、`db.session.query().filter().order_by().all()` が返すようモックする。`get_gadget_types()` を呼び出す。 | `len(result) == 22` である。 |
| 72 | 3.1.4.2 検索結果戻り値ハンドリング（空結果） | `db.session.query().filter().order_by().all()` が `[]` を返すようモックする。`get_gadget_types()` を呼び出す。 | `result == []` である。 |

---

### TestGetGadgetByUuid

| No | テスト観点 | 操作手順 | 予想結果 |
|----|-----------|---------|---------|
| 73 | 2.2.1 対象データ存在チェック（対象IDが存在する） | `mock_gadget` を用意し、`db.session.query().filter().first()` が返すようモックする。`get_gadget_by_uuid('gadget-uuid-001', 1)` を呼び出す。 | `result` が `mock_gadget` と同一オブジェクトである。 |
| 74 | 2.2.2 対象データ存在チェック（対象IDが存在しない） | `db.session.query().filter().first()` が `None` を返すようモックする。`get_gadget_by_uuid('no-such-uuid', 1)` を呼び出す。 | `result` が `None` である。 |
| 75 | 3.1.1.1 検索条件指定（検索条件を指定） | `db.session.query().filter().first()` が `None` を返すようモックする。`VDashboardGadgetMasterByUser` をインポートする。`get_gadget_by_uuid('gadget-uuid-001', 1)` を呼び出す。 | `filter` の引数に `VDashboardGadgetMasterByUser.user_id == 1` に相当するフィルタ式が含まれる。 |

---

### TestUpdateGadgetTitle

| No | テスト観点 | 操作手順 | 予想結果 |
|----|-----------|---------|---------|
| 76 | 3.3.1.1 更新処理呼び出し（正常な入力値） | `mock_gadget = MagicMock()` を用意する。`update_gadget_title(mock_gadget, name='新ガジェット名', modifier=1)` を呼び出す。 | `mock_gadget.gadget_name == '新ガジェット名'` である。 |
| 77 | 3.3.2.1 更新結果（処理完了） | `mock_gadget = MagicMock()` を用意する。`update_gadget_title(mock_gadget, name='ガジェット名', modifier=1)` を呼び出す。 | `mock_gadget.modifier == 1` である。 |

---

### TestDeleteGadget

| No | テスト観点 | 操作手順 | 予想結果 |
|----|-----------|---------|---------|
| 78 | 3.4.1.1 削除処理呼び出し（正常なIDを指定） | `mock_gadget = MagicMock()` を用意する。`delete_gadget(mock_gadget, modifier=1)` を呼び出す。 | `mock_gadget.delete_flag is True` である。 |
| 79 | 3.4.2.1 削除結果（処理完了） | `mock_gadget = MagicMock()` を用意する。`delete_gadget(mock_gadget, modifier=1)` を呼び出す。 | `mock_gadget.modifier == 1` である。 |

---

### TestGetGadgetType

| No | テスト観点 | 操作手順 | 予想結果 |
|----|-----------|---------|---------|
| 80 | 2.3.1 gadget_uuid が存在する場合: gadget_type_name を返す | `mock_row.gadget_type_name = 'timeline'` を用意し、`db.session.query().join().filter().first()` が返すようモックする。`get_gadget_type('test-uuid-1234')` を呼び出す。 | `result == 'timeline'` である。 |
| 81 | 2.3.2 gadget_uuid が存在しない場合: None を返す | `db.session.query().join().filter().first()` が `None` を返すようモックする。`get_gadget_type('non-existent-uuid')` を呼び出す。 | `result is None` である。 |
| 82 | 2.3.3 delete_flag=True のガジェットのみ存在する場合: None を返す | `db.session.query().join().filter().first()` が `None` を返すようモックする（delete_flag=False フィルタにより論理削除済みレコードはヒットしない想定）。`get_gadget_type('deleted-uuid-5678')` を呼び出す。 | `result is None` である。 |

---

### TestSaveLayout

| No | テスト観点 | 操作手順 | 予想結果 |
|----|-----------|---------|---------|
| 83 | 3.3.1.1 更新処理呼び出し（正常な入力値） | `mock_gadget` を用意し、`db.session.query().filter().first()` が返すようモックする。`layout_data = [{'gadget_uuid': 'g-001', 'position_x': 0, 'position_y': 1, 'display_order': 0}]` を用意する。`save_layout(layout_data, modifier=1)` を呼び出す。 | `mock_gadget.position_x == 0`、`mock_gadget.position_y == 1`、`mock_gadget.display_order == 0`、`mock_gadget.modifier == 1` である。 |
| 84 | 3.3.1.1 更新処理呼び出し（正常な入力値） | `mock_gadget.gadget_size = 0` を設定し、`db.session.query().filter().first()` が返すようモックする。`layout_data = [{'gadget_uuid': 'g-001', 'position_x': 1, 'position_y': 2, 'display_order': 1}]` を用意する。`save_layout(layout_data, modifier=1)` を呼び出す。 | `mock_gadget.gadget_size == 0`（変更されていない）である。 |
| 85 | 2.2.2 対象データ存在チェック（対象IDが存在しない） | `db.session.query().filter().first()` が `None` を返すようモックする（ガジェット未存在）。`layout_data = [{'gadget_uuid': 'no-such-uuid', 'position_x': 0, 'position_y': 0, 'display_order': 0}]` を用意する。`save_layout(layout_data, modifier=1)` を呼び出す。 | 例外が発生しない（ガジェット未存在の場合は更新をスキップする）。 |
| 86 | 2.3.2 副作用チェック（例外発生時） | `db.session.query.side_effect = Exception('DB error')` を設定する。`layout_data = [{'gadget_uuid': 'g-001', 'position_x': 0, 'position_y': 0, 'display_order': 0}]` を用意する。`save_layout(layout_data, modifier=1)` を `pytest.raises(Exception)` コンテキスト内で呼び出す。 | `Exception` が発生する。`db.session.rollback()` が1回呼ばれる。 |

---

### TestGetDevicesByOrganization

| No | テスト観点 | 操作手順 | 予想結果 |
|----|-----------|---------|---------|
| 87 | 3.1.4.1 検索結果戻り値ハンドリング（正常系） | `mock_device1`, `mock_device2` を用意し、`db.session.query().filter().order_by().all()` が `[mock_device1, mock_device2]` を返すようモックする。`get_devices_by_organization(org_id=1)` を呼び出す。 | `result == [mock_device1, mock_device2]` である。 |
| 88 | 3.1.4.2 検索結果戻り値ハンドリング（空結果） | `db.session.query().filter().order_by().all()` が `[]` を返すようモックする。`get_devices_by_organization(org_id=999)` を呼び出す。 | `result == []` である。 |

---

### TestUpdateDatasourceSetting

| No | テスト観点 | 操作手順 | 予想結果 |
|----|-----------|---------|---------|
| 89 | 3.3.1.1 更新処理呼び出し（正常な入力値） | `mock_setting` を用意し、`db.session.query().filter().first()` が返すようモックする。`update_datasource_setting(user_id=1, organization_id=5, device_id=10, modifier=1)` を呼び出す。 | `mock_setting.organization_id == 5`、`mock_setting.device_id == 10` である。 |
| 90 | 3.1.2 検索条件未指定（organization_id が None の場合は None のまま設定する） | `mock_setting` を用意し、`db.session.query().filter().first()` が返すようモックする。`update_datasource_setting(user_id=1, organization_id=None, device_id=10, modifier=1)` を呼び出す。 | `mock_setting.organization_id is None` である。 |
| 91 | 3.1.2 検索条件未指定（device_id が None の場合は None のまま設定する） | `mock_setting` を用意し、`db.session.query().filter().first()` が返すようモックする。`update_datasource_setting(user_id=1, organization_id=5, device_id=None, modifier=1)` を呼び出す。 | `mock_setting.device_id is None` である。 |
| 92 | 3.3.2.1 更新結果（処理完了） | `mock_setting` を用意し、`db.session.query().filter().first()` が返すようモックする。`update_datasource_setting(user_id=1, organization_id=5, device_id=10, modifier=1)` を呼び出す。 | `mock_setting.modifier == 1` である。 |

---
