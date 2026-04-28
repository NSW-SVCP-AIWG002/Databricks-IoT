# テスト項目書 - 顧客作成ダッシュボード機能 Form層

- **対象ファイル**: `src/iot_app/forms/customer_dashboard/common.py`
- **テストコード**: `tests/unit/forms/customer_dashboard/test_common.py`
- **観点表**: `docs/05-testing/unit-test/unit-test-perspectives.md`
- **ワークフロー仕様書**: `docs/03-features/flask-app/customer-dashboard/common/workflow-specification.md`

---

## 対応表

テストクラスと、ワークフロー仕様書の各ワークフロー・処理フロー項目の対応を示します。

| テストクラス | テスト項目No. | 対応ワークフロー | 処理フロー項目 | エンドポイント |
|------------|:---:|--------------|-------------|-------------|
| TestDashboardForm | 1〜7 | ダッシュボード登録<br>ダッシュボードタイトル更新 | 登録 バリデーション<br>更新 ③ バリデーション | `POST /analysis/customer-dashboard/dashboards/register`<br>`POST /analysis/customer-dashboard/dashboards/<dashboard_uuid>/update` |
| TestDashboardGroupForm | 8〜16 | ダッシュボードグループ登録<br>ダッシュボードグループタイトル更新 | グループ登録 ③ バリデーション<br>グループ更新 ③ バリデーション | `POST /analysis/customer-dashboard/groups/register`<br>`POST /analysis/customer-dashboard/groups/<dashboard_group_uuid>/update` |
| TestGadgetForm | 17〜23 | ガジェット登録<br>ガジェットタイトル更新 | ガジェット登録 バリデーション<br>ガジェット更新 ③ バリデーション | `POST /analysis/customer-dashboard/gadgets/{gadget_type}/register`<br>`POST /analysis/customer-dashboard/gadgets/<gadget_uuid>/update` |

---

## ワークフロー別カバレッジ

ワークフロー仕様書の各ワークフローに対して、どのテストクラスが対応しているかを示します。

### ダッシュボード登録

| 処理フロー項目 | 対応テストクラス | テスト項目No. |
|-------------|--------------|:---:|
| バリデーション | TestDashboardForm | 1〜7 |

### ダッシュボードタイトル更新

| 処理フロー項目 | 対応テストクラス | テスト項目No. |
|-------------|--------------|:---:|
| ③ バリデーション | TestDashboardForm | 1〜7 |

### ダッシュボードグループ登録

| 処理フロー項目 | 対応テストクラス | テスト項目No. |
|-------------|--------------|:---:|
| ③ バリデーション | TestDashboardGroupForm | 8〜16 |

### ダッシュボードグループタイトル更新

| 処理フロー項目 | 対応テストクラス | テスト項目No. |
|-------------|--------------|:---:|
| ③ バリデーション | TestDashboardGroupForm | 8〜16 |

### ガジェット登録

| 処理フロー項目 | 対応テストクラス | テスト項目No. |
|-------------|--------------|:---:|
| バリデーション | TestGadgetForm | 17〜23 |

### ガジェットタイトル更新

| 処理フロー項目 | 対応テストクラス | テスト項目No. |
|-------------|--------------|:---:|
| ③ バリデーション | TestGadgetForm | 17〜23 |

---

## テストクラス一覧

テストクラスに対して、テスト観点、操作手順、予想結果を示します。

### TestDashboardForm

| No | テスト観点 | 操作手順 | 予想結果 |
|----|-----------|---------|---------|
| 1 | 1.1.1.3 入力あり: バリデーション通過 | `DashboardForm(data={'dashboard_name': 'テストダッシュボード'})` を生成し、`form.validate()` を呼ぶ | `True` が返る（バリデーション通過） |
| 2 | 1.1.1.1 空文字: バリデーションエラー | `DashboardForm(data={'dashboard_name': ''})` を生成し、`form.validate()` を呼ぶ | `False` が返り、`form.errors` に `dashboard_name` が含まれる |
| 3 | 1.1.1.2 None: バリデーションエラー | `DashboardForm(data={'dashboard_name': None})` を生成し、`form.validate()` を呼ぶ | `False` が返り、`form.errors` に `dashboard_name` が含まれる |
| 4 | 1.1.1.4 空白のみ: バリデーションエラー | `DashboardForm(data={'dashboard_name': '   '})` を生成し、`form.validate()` を呼ぶ（DataRequired が strip するため空文字扱いになる） | `False` が返り、`form.errors` に `dashboard_name` が含まれる |
| 5 | 1.2.1 最大長-1（49文字）: バリデーション通過 | `DashboardForm(data={'dashboard_name': 'a' * 49})` を生成し、`form.validate()` を呼ぶ | `True` が返る（バリデーション通過） |
| 6 | 1.2.2 最大長ちょうど（50文字）: バリデーション通過 | `DashboardForm(data={'dashboard_name': 'a' * 50})` を生成し、`form.validate()` を呼ぶ | `True` が返る（バリデーション通過） |
| 7 | 1.2.3 最大長+1（51文字）: バリデーションエラー | `DashboardForm(data={'dashboard_name': 'a' * 51})` を生成し、`form.validate()` を呼ぶ | `False` が返り、`form.errors` に `dashboard_name` が含まれる |

---

### TestDashboardGroupForm

| No | テスト観点 | 操作手順 | 予想結果 |
|----|-----------|---------|---------|
| 8 | 1.1.1.3 入力あり: バリデーション通過 | `DashboardGroupForm(data={'dashboard_group_name': 'テストグループ'})` を生成し、`form.validate()` を呼ぶ | `True` が返る（バリデーション通過） |
| 9 | 1.1.1.1 空文字: バリデーションエラー | `DashboardGroupForm(data={'dashboard_group_name': ''})` を生成し、`form.validate()` を呼ぶ | `False` が返り、`form.errors` に `dashboard_group_name` が含まれる |
| 10 | 1.1.1.2 None: バリデーションエラー | `DashboardGroupForm(data={'dashboard_group_name': None})` を生成し、`form.validate()` を呼ぶ | `False` が返り、`form.errors` に `dashboard_group_name` が含まれる |
| 11 | 1.1.1.4 空白のみ: バリデーションエラー | `DashboardGroupForm(data={'dashboard_group_name': '   '})` を生成し、`form.validate()` を呼ぶ（DataRequired が strip するため空文字扱いになる） | `False` が返り、`form.errors` に `dashboard_group_name` が含まれる |
| 12 | 1.2.1 最大長-1（49文字）: バリデーション通過 | `DashboardGroupForm(data={'dashboard_group_name': 'a' * 49})` を生成し、`form.validate()` を呼ぶ | `True` が返る（バリデーション通過） |
| 13 | 1.2.2 最大長ちょうど（50文字）: バリデーション通過 | `DashboardGroupForm(data={'dashboard_group_name': 'a' * 50})` を生成し、`form.validate()` を呼ぶ | `True` が返る（バリデーション通過） |
| 14 | 1.2.3 最大長+1（51文字）: バリデーションエラー | `DashboardGroupForm(data={'dashboard_group_name': 'a' * 51})` を生成し、`form.validate()` を呼ぶ | `False` が返り、`form.errors` に `dashboard_group_name` が含まれる |
| 15 | dashboard_uuid あり: バリデーション通過 | `DashboardGroupForm(data={'dashboard_uuid': 'test-dashboard-uuid-001', 'dashboard_group_name': 'テストグループ'})` を生成し、`form.validate()` を呼ぶ | `True` が返る（バリデーション通過） |
| 16 | dashboard_uuid 空: バリデーション通過 | `DashboardGroupForm(data={'dashboard_uuid': '', 'dashboard_group_name': 'テストグループ'})` を生成し、`form.validate()` を呼ぶ（HiddenField はバリデーターなしのため空文字でも通過する） | `True` が返る（バリデーション通過） |

---

### TestGadgetForm

| No | テスト観点 | 操作手順 | 予想結果 |
|----|-----------|---------|---------|
| 17 | 1.1.1.3 入力あり: バリデーション通過 | `GadgetForm(data={'gadget_name': 'テストガジェット'})` を生成し、`form.validate()` を呼ぶ | `True` が返る（バリデーション通過） |
| 18 | 1.1.1.1 空文字: バリデーションエラー | `GadgetForm(data={'gadget_name': ''})` を生成し、`form.validate()` を呼ぶ | `False` が返り、`form.errors` に `gadget_name` が含まれる |
| 19 | 1.1.1.2 None: バリデーションエラー | `GadgetForm(data={'gadget_name': None})` を生成し、`form.validate()` を呼ぶ | `False` が返り、`form.errors` に `gadget_name` が含まれる |
| 20 | 1.1.1.4 空白のみ: バリデーションエラー | `GadgetForm(data={'gadget_name': '   '})` を生成し、`form.validate()` を呼ぶ（DataRequired が strip するため空文字扱いになる） | `False` が返り、`form.errors` に `gadget_name` が含まれる |
| 21 | 1.2.1 最大長-1（19文字）: バリデーション通過 | `GadgetForm(data={'gadget_name': 'a' * 19})` を生成し、`form.validate()` を呼ぶ | `True` が返る（バリデーション通過） |
| 22 | 1.2.2 最大長ちょうど（20文字）: バリデーション通過 | `GadgetForm(data={'gadget_name': 'a' * 20})` を生成し、`form.validate()` を呼ぶ | `True` が返る（バリデーション通過） |
| 23 | 1.2.3 最大長+1（21文字）: バリデーションエラー | `GadgetForm(data={'gadget_name': 'a' * 21})` を生成し、`form.validate()` を呼ぶ | `False` が返り、`form.errors` に `gadget_name` が含まれる |
