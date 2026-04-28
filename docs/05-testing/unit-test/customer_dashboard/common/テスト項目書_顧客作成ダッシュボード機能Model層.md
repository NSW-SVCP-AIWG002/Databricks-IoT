# テスト項目書 - 顧客作成ダッシュボード共通機能 Model層

- **対象ファイル**: `src/iot_app/models/customer_dashboard.py`
- **テストコード**: `tests/unit/models/test_customer_dashboard.py`
- **観点表**: `docs/05-testing/unit-test/unit-test-perspectives.md`
- **ワークフロー仕様書**: `docs/03-features/flask-app/customer-dashboard/common/workflow-specification.md`

---

## 対応表

テストクラスと、ワークフロー仕様書の各ワークフロー・処理フロー項目の対応を示します。

| テストクラス | テスト項目No. | 対応ワークフロー | 処理フロー項目 | エンドポイント |
|------------|:---:|--------------|-------------|-------------|
| TestDashboardUserSetting | 1〜2 | ダッシュボード初期表示<br>ダッシュボード登録<br>データソース選択 | 初期表示 ③ ユーザー設定取得<br>登録 ② ユーザー設定更新<br>データソース選択 設定保存 | `GET /analysis/customer-dashboard`<br>`POST /analysis/customer-dashboard/dashboards/register`<br>`POST /analysis/customer-dashboard/datasource/save` |
| TestVDashboardMasterByUser | 3 | ダッシュボード初期表示<br>ダッシュボード管理モーダル表示<br>ダッシュボードタイトル更新 | 初期表示 ④ ダッシュボード情報取得<br>管理モーダル ① ダッシュボード一覧取得<br>タイトル更新 ① ダッシュボード情報取得 | `GET /analysis/customer-dashboard`<br>`GET /analysis/customer-dashboard/dashboards`<br>`POST /analysis/customer-dashboard/dashboards/<dashboard_uuid>/update` |
| TestDashboardGroupMaster | 4〜6 | ダッシュボード初期表示<br>ダッシュボードグループ登録<br>ダッシュボードグループタイトル更新<br>ダッシュボードグループ削除 | 初期表示 ⑤ グループ一覧取得<br>グループ登録 ④ グループ登録<br>グループ更新 ④ グループタイトル更新<br>グループ削除 | `GET /analysis/customer-dashboard`<br>`POST /analysis/customer-dashboard/groups/register`<br>`POST /analysis/customer-dashboard/groups/<dashboard_group_uuid>/update`<br>`POST /analysis/customer-dashboard/groups/<dashboard_group_uuid>/delete` |
| TestDashboardGadgetMaster | 7〜9 | ダッシュボード初期表示<br>ガジェット登録<br>ガジェットタイトル更新<br>ガジェット削除 | 初期表示 ⑥ ガジェット一覧取得<br>ガジェット登録<br>ガジェット更新 ④ ガジェットタイトル更新<br>ガジェット削除 | `GET /analysis/customer-dashboard`<br>`POST /analysis/customer-dashboard/gadgets/{gadget_type}/register`<br>`POST /analysis/customer-dashboard/gadgets/<gadget_uuid>/update`<br>`POST /analysis/customer-dashboard/gadgets/<gadget_uuid>/delete` |
| TestVOrganizationMasterByUser | 10 | ダッシュボード初期表示<br>データソース選択 | 初期表示 ⑦ 組織選択肢取得<br>デバイス一覧取得 組織選択肢取得 | `GET /analysis/customer-dashboard`<br>`GET /analysis/customer-dashboard/organizations/<org_id>/devices` |
| TestDashboardMaster | 11〜13 | ダッシュボード登録<br>ダッシュボードタイトル更新<br>ダッシュボード削除 | 登録 ⑩ ダッシュボード登録<br>タイトル更新 ④ タイトル更新<br>削除 | `POST /analysis/customer-dashboard/dashboards/register`<br>`POST /analysis/customer-dashboard/dashboards/<dashboard_uuid>/update`<br>`POST /analysis/customer-dashboard/dashboards/<dashboard_uuid>/delete` |
| TestVDashboardGroupMasterByUser | 14 | ダッシュボードグループタイトル更新 | グループ更新 ① グループ情報取得 | `POST /analysis/customer-dashboard/groups/<dashboard_group_uuid>/update` |
| TestGadgetTypeMaster | 15〜16 | ガジェット追加モーダル表示 | ガジェット種別一覧取得 | `GET /analysis/customer-dashboard/gadgets/add` |
| TestVDashboardGadgetMasterByUser | 17 | ガジェットタイトル更新 | ガジェット更新 ① ガジェット情報取得 | `POST /analysis/customer-dashboard/gadgets/<gadget_uuid>/update` |

---

## ワークフロー別カバレッジ

ワークフロー仕様書の各ワークフローに対して、どのテストクラスが対応しているかを示します。

### ダッシュボード初期表示

| 処理フロー項目 | 対応テストクラス | テスト項目No. |
|-------------|--------------|:---:|
| ③ ダッシュボードユーザー設定取得 | TestDashboardUserSetting | 1〜2 |
| ④ ダッシュボード情報取得 | TestVDashboardMasterByUser | 3 |
| ⑤ ダッシュボードグループ一覧取得 | TestDashboardGroupMaster | 4〜6 |
| ⑥ ガジェット一覧取得 | TestDashboardGadgetMaster | 7〜9 |
| ⑦ 組織選択肢取得 | TestVOrganizationMasterByUser | 10 |

### ダッシュボード管理モーダル表示

| 処理フロー項目 | 対応テストクラス | テスト項目No. |
|-------------|--------------|:---:|
| ① ダッシュボード一覧取得 | TestVDashboardMasterByUser | 3 |

### ダッシュボード登録

| 処理フロー項目 | 対応テストクラス | テスト項目No. |
|-------------|--------------|:---:|
| ② ユーザー設定更新 | TestDashboardUserSetting | 1〜2 |
| ⑩ ダッシュボード登録 | TestDashboardMaster | 11〜13 |

### ダッシュボードタイトル更新

| 処理フロー項目 | 対応テストクラス | テスト項目No. |
|-------------|--------------|:---:|
| ① ダッシュボード情報取得 | TestVDashboardMasterByUser | 3 |
| ④ ダッシュボードタイトル更新 | TestDashboardMaster | 11〜13 |

### ダッシュボード削除

| 処理フロー項目 | 対応テストクラス | テスト項目No. |
|-------------|--------------|:---:|
| 削除処理 | TestDashboardMaster | 11〜13 |

### ダッシュボードグループ登録

| 処理フロー項目 | 対応テストクラス | テスト項目No. |
|-------------|--------------|:---:|
| ④ グループ登録 | TestDashboardGroupMaster | 4〜6 |

### ダッシュボードグループタイトル更新

| 処理フロー項目 | 対応テストクラス | テスト項目No. |
|-------------|--------------|:---:|
| ① グループ情報取得 | TestVDashboardGroupMasterByUser | 14 |
| ④ グループタイトル更新 | TestDashboardGroupMaster | 4〜6 |

### ダッシュボードグループ削除

| 処理フロー項目 | 対応テストクラス | テスト項目No. |
|-------------|--------------|:---:|
| 削除処理 | TestDashboardGroupMaster | 4〜6 |

### ガジェット追加モーダル表示

| 処理フロー項目 | 対応テストクラス | テスト項目No. |
|-------------|--------------|:---:|
| ガジェット種別一覧取得 | TestGadgetTypeMaster | 15〜16 |

### ガジェット登録

| 処理フロー項目 | 対応テストクラス | テスト項目No. |
|-------------|--------------|:---:|
| ガジェット登録 | TestDashboardGadgetMaster | 7〜9 |

### ガジェットタイトル更新

| 処理フロー項目 | 対応テストクラス | テスト項目No. |
|-------------|--------------|:---:|
| ① ガジェット情報取得 | TestVDashboardGadgetMasterByUser | 17 |
| ④ ガジェットタイトル更新 | TestDashboardGadgetMaster | 7〜9 |

### ガジェット削除

| 処理フロー項目 | 対応テストクラス | テスト項目No. |
|-------------|--------------|:---:|
| 削除処理 | TestDashboardGadgetMaster | 7〜9 |

### データソース選択

| 処理フロー項目 | 対応テストクラス | テスト項目No. |
|-------------|--------------|:---:|
| 組織選択肢取得 | TestVOrganizationMasterByUser | 10 |
| 設定保存 | TestDashboardUserSetting | 1〜2 |

---

## テストクラス一覧

テストクラスに対して、テスト観点、操作手順、予想結果を示します。

### TestDashboardUserSetting

| No | テスト観点 | 操作手順 | 予想結果 |
|----|-----------|---------|---------|
| 1 | 必須フィールドを指定してインスタンスを生成できる | `DashboardUserSetting(user_id=1, dashboard_id=1, organization_id=None, device_id=None, creator=1, modifier=1)` でインスタンスを生成する | `setting.user_id == 1`、`setting.dashboard_id == 1`、`setting.organization_id is None`、`setting.device_id is None` である |
| 2 | delete_flag のデフォルト値は False | `DashboardUserSetting(user_id=1, dashboard_id=1, organization_id=None, device_id=None, creator=1, modifier=1)` でインスタンスを生成する | `setting.delete_flag is False` である |

---

### TestVDashboardMasterByUser

| No | テスト観点 | 操作手順 | 予想結果 |
|----|-----------|---------|---------|
| 3 | VIEWモデルに必要なカラム属性が定義されている | `VDashboardMasterByUser` クラスに対して `hasattr()` で各カラム属性の存在を確認する | `user_id`、`dashboard_id`、`dashboard_uuid`、`dashboard_name`、`creator`、`delete_flag` の各属性が存在する |

---

### TestDashboardGroupMaster

| No | テスト観点 | 操作手順 | 予想結果 |
|----|-----------|---------|---------|
| 4 | 必須フィールドを指定してインスタンスを生成できる | `DashboardGroupMaster(dashboard_group_uuid='group-uuid-001', dashboard_group_name='グループA', dashboard_id=1, display_order=0, creator=1, modifier=1)` でインスタンスを生成する | `group.dashboard_group_uuid == 'group-uuid-001'`、`group.dashboard_group_name == 'グループA'`、`group.dashboard_id == 1`、`group.display_order == 0` である |
| 5 | delete_flag のデフォルト値は False | `DashboardGroupMaster(dashboard_group_uuid='group-uuid-001', dashboard_group_name='グループA', dashboard_id=1, display_order=0, creator=1, modifier=1)` でインスタンスを生成する | `group.delete_flag is False` である |
| 6 | dashboard_group_name は最大50文字を受け付ける | `dashboard_group_name='あ' * 50` を含む必須パラメータで `DashboardGroupMaster` インスタンスを生成する | `len(group.dashboard_group_name) == 50` である |

---

### TestDashboardGadgetMaster

| No | テスト観点 | 操作手順 | 予想結果 |
|----|-----------|---------|---------|
| 7 | 必須フィールドを指定してインスタンスを生成できる | `DashboardGadgetMaster(gadget_uuid='gadget-uuid-001', gadget_name='テストガジェット', dashboard_group_id=1, gadget_type_id=1, chart_config={}, data_source_config={}, position_x=0, position_y=0, gadget_size=0, display_order=0, creator=1, modifier=1)` でインスタンスを生成する | `gadget.gadget_uuid == 'gadget-uuid-001'`、`gadget.gadget_name == 'テストガジェット'`、`gadget.dashboard_group_id == 1`、`gadget.gadget_type_id == 1`、`gadget.position_x == 0`、`gadget.position_y == 0`、`gadget.gadget_size == 0`、`gadget.display_order == 0` である |
| 8 | delete_flag のデフォルト値は False | 上記と同一パラメータで `DashboardGadgetMaster` インスタンスを生成する | `gadget.delete_flag is False` である |
| 9 | gadget_name は最大20文字を受け付ける | `gadget_name='あ' * 20` を含む必須パラメータで `DashboardGadgetMaster` インスタンスを生成する | `len(gadget.gadget_name) == 20` である |

---

### TestVOrganizationMasterByUser

| No | テスト観点 | 操作手順 | 予想結果 |
|----|-----------|---------|---------|
| 10 | VIEWモデルに必要なカラム属性が定義されている | `VOrganizationMasterByUser` クラスに対して `hasattr()` で各カラム属性の存在を確認する | `user_id`、`organization_id`、`organization_name` の各属性が存在する |

---

### TestDashboardMaster

| No | テスト観点 | 操作手順 | 予想結果 |
|----|-----------|---------|---------|
| 11 | 必須フィールドを指定してインスタンスを生成できる | `DashboardMaster(dashboard_uuid='test-uuid-001', dashboard_name='テストダッシュボード', organization_id=1, creator=1, modifier=1)` でインスタンスを生成する | `dashboard.dashboard_uuid == 'test-uuid-001'`、`dashboard.dashboard_name == 'テストダッシュボード'`、`dashboard.organization_id == 1` である |
| 12 | delete_flag のデフォルト値は False | `DashboardMaster(dashboard_uuid='test-uuid-001', dashboard_name='テストダッシュボード', organization_id=1, creator=1, modifier=1)` でインスタンスを生成する | `dashboard.delete_flag is False` である |
| 13 | dashboard_name は最大50文字を受け付ける | `dashboard_name='あ' * 50` を含む必須パラメータで `DashboardMaster` インスタンスを生成する | `len(dashboard.dashboard_name) == 50` である |

---

### TestVDashboardGroupMasterByUser

| No | テスト観点 | 操作手順 | 予想結果 |
|----|-----------|---------|---------|
| 14 | VIEWモデルに必要なカラム属性が定義されている | `VDashboardGroupMasterByUser` クラスに対して `hasattr()` で各カラム属性の存在を確認する | `user_id`、`dashboard_group_id`、`dashboard_group_uuid`、`dashboard_group_name`、`dashboard_id`、`display_order`、`creator`、`delete_flag` の各属性が存在する |

---

### TestGadgetTypeMaster

| No | テスト観点 | 操作手順 | 予想結果 |
|----|-----------|---------|---------|
| 15 | 必須フィールドを指定してインスタンスを生成できる | `GadgetTypeMaster(gadget_type_name='棒グラフ', gadget_type_slug='bar-chart', data_source_type=0, gadget_image_path='static/images/bar_chart.png', gadget_description='棒グラフガジェット', display_order=1, creator=1, modifier=1)` でインスタンスを生成する | `gadget_type.gadget_type_name == '棒グラフ'`、`gadget_type.gadget_type_slug == 'bar-chart'`、`gadget_type.data_source_type == 0`、`gadget_type.gadget_image_path == 'static/images/bar_chart.png'`、`gadget_type.gadget_description == '棒グラフガジェット'`、`gadget_type.display_order == 1` である |
| 16 | delete_flag のデフォルト値は False | 上記と同一パラメータで `GadgetTypeMaster` インスタンスを生成する | `gadget_type.delete_flag is False` である |

---

### TestVDashboardGadgetMasterByUser

| No | テスト観点 | 操作手順 | 予想結果 |
|----|-----------|---------|---------|
| 17 | VIEWモデルに必要なカラム属性が定義されている | `VDashboardGadgetMasterByUser` クラスに対して `hasattr()` で各カラム属性の存在を確認する | `user_id`、`gadget_id`、`gadget_uuid`、`gadget_name`、`dashboard_group_id`、`gadget_type_id`、`chart_config`、`data_source_config`、`position_x`、`position_y`、`gadget_size`、`display_order`、`creator`、`delete_flag` の各属性が存在する |
