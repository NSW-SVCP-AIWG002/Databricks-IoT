# テストコードレビュー結果 - 顧客作成ダッシュボード機能（共通）

- **レビュー対象**:
  - `tests/unit/services/customer_dashboard/test_common.py`
  - `tests/unit/models/test_customer_dashboard.py`
  - `tests/unit/forms/customer_dashboard/test_common.py`
- **レビュー日**: 2026-04-23
- **チェックリスト**: `docs/05-testing/unit-test/テストコードレビュー用プロンプト.md`

---

## チェックリスト確認結果

| チェック項目 | 結果 |
|------------|------|
| CL-1-1 全フィールドのアサート確認 | 指摘あり（No.1〜6） |
| CL-1-2 全フィルター条件の検証 | 指摘あり（No.7） |
| CL-2-1 例外伝播テスト | OK |
| CL-2-2 4xx/5xxエラー代表ケース | OK（Service層はDB操作のみ） |
| CL-3-1 必須チェック全ケース | OK |
| CL-3-2 最大文字列長チェック全ケース | OK |
| CL-3-3 数値範囲チェック | OK（該当フィールドなし） |
| CL-3-4 日付形式チェック | OK（該当フィールドなし） |
| CL-3-5 メールアドレス形式チェック | OK（該当フィールドなし） |
| CL-3-6 不整値チェック | OK（該当フィールドなし） |
| CL-4-1〜4-3 CSVエクスポート | OK（対象なし） |
| CL-5-1 patchパス確認 | OK |
| CL-5-2 docstring観点番号 | 指摘あり（No.8） |
| CL-6-1 テスト総数一致 | OK（修正後） |
| CL-6-2 No列重複・欠番なし | OK |
| CL-6-3 テスト項目書との整合性 | 修正後に更新が必要 |

---

## 指摘一覧

| No | 対象ファイル | 対象テスト / 行 | 指摘内容 | 対応観点 | 修正案 |
|----|-------------|----------------|----------|----------|--------|
| 1 | test_common.py (Service層) | TestCreateDashboard.test_adds_dashboard_to_session / L755 | `create_dashboard('テストダッシュボード', user_id=1)` を呼び出しているが、追加オブジェクトの `dashboard_name` をアサートしていない | CL-1-1 / 3.2.1.4 | `added_obj = mock_db.session.add.call_args[0][0]` を追加し、`assert added_obj.dashboard_name == 'テストダッシュボード'` を追加する |
| 2 | test_common.py (Service層) | TestCreateDashboardGroup.test_sets_creator_and_modifier / L1246 | `create_dashboard_group('グループA', dashboard_id=1, user_id=1)` を呼び出しているが、`dashboard_group_name` と `dashboard_id` のアサートがない | CL-1-1 / 3.2.1.4 | `assert added_obj.dashboard_group_name == 'グループA'` と `assert added_obj.dashboard_id == 1` を追加する |
| 3 | test_common.py (Service層) | TestUpsertDashboardUserSetting.test_inserts_when_no_existing_setting / L88 | `upsert_dashboard_user_setting(1, 1)` で `user_id=1` を渡しているが、追加オブジェクトの `user_id` をアサートしていない | CL-1-1 / 3.2.1.4 | `assert added_obj.user_id == 1` を追加する |
| 4 | test_common.py (Model層) | TestDashboardGadgetMaster.test_instantiate_with_required_fields / L177 | `dashboard_group_id=1, gadget_type_id=1, position_x=0, position_y=0, gadget_size=0, display_order=0` を明示的に指定して生成しているが、`gadget_uuid` と `gadget_name` しかアサートしていない | CL-1-1 / 3.2.1.4 | `assert gadget.dashboard_group_id == 1`、`assert gadget.gadget_type_id == 1`、`assert gadget.position_x == 0`、`assert gadget.position_y == 0`、`assert gadget.gadget_size == 0`、`assert gadget.display_order == 0` を追加する |
| 5 | test_common.py (Model層) | TestDashboardUserSetting.test_instantiate_with_required_fields / L312 | `organization_id=None, device_id=None` を明示的に指定（docstringに「NULL で保存」と記載）しているが、これらのアサートがない | CL-1-1 / 3.2.1.4 | `assert setting.organization_id is None` と `assert setting.device_id is None` を追加する |
| 6 | test_common.py (Model層) | TestGadgetTypeMaster.test_instantiate_with_required_fields / L260 | `gadget_image_path='static/images/bar_chart.png'` と `gadget_description='棒グラフガジェット'` を明示的に指定しているが、アサートしていない | CL-1-1 / 3.2.1.4 | `assert gadget_type.gadget_image_path == 'static/images/bar_chart.png'` と `assert gadget_type.gadget_description == '棒グラフガジェット'` を追加する |
| 7 | test_common.py (Service層) | TestGetDevices / L532 | `get_devices(organization_id)` は `DeviceMaster.organization_id` でフィルタするが、このフィルタ条件が実際に適用されることを検証するテストがない（`TestGetOrganizations.test_filters_by_user_id` に相当するテストが欠如） | CL-1-2 / 3.1.1 | `test_filters_by_organization_id` を新規追加し、`filter` の引数に `DeviceMaster.organization_id == 1` に相当する式が含まれることをアサートする |
| 8 | test_common.py (Form層) | TestDashboardGroupForm.test_valid_when_dashboard_uuid_provided / L132<br>TestDashboardGroupForm.test_valid_when_dashboard_uuid_empty / L141 | docstringに観点表の観点番号が記載されていない（他のテストメソッドは `1.1.1.3` 等の番号を付与している） | CL-5-2 | `test_valid_when_dashboard_uuid_provided` → `"""1.1.1.3 dashboard_uuid あり: HiddenField は任意値でバリデーション通過"""`、`test_valid_when_dashboard_uuid_empty` → `"""1.2.4 dashboard_uuid 空文字: HiddenField はバリデーターなしのためバリデーション通過"""` |

---

## 修正実施結果

上記 No.1〜8 の指摘を以下のファイルに反映済み：

- `tests/unit/services/customer_dashboard/test_common.py` — No.1, 2, 3, 7 対応
- `tests/unit/models/test_customer_dashboard.py` — No.4, 5, 6 対応
- `tests/unit/forms/customer_dashboard/test_common.py` — No.8 対応
- `docs/05-testing/unit-test/customer_dashboard/common/テスト項目書_顧客作成ダッシュボード機能Service層.md` — No.7 対応（No.23 追加・以降の連番更新）
- `docs/05-testing/unit-test/customer_dashboard/common/テスト項目書_顧客作成ダッシュボード機能Model層.md` — No.4, 5, 6 対応（予想結果更新）
