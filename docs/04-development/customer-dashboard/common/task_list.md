# 顧客作成ダッシュボード（共通） 実装タスクリスト

## タスク一覧

| #  | タスク名                        | 対象ファイル                                                                                                                                                | 対応テスト                                                              | 実装フロー状態 | 備考                                                  |
| -- | ------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------- | -------------- | ----------------------------------------------------- |
| 1  | Model: customer_dashboard       | `src/iot_app/models/customer_dashboard.py`                                                                                                                  | `tests/unit/models/test_customer_dashboard.py`                          | 完了           | 5クラス: DashboardMaster, DashboardGroupMaster, DashboardGadgetMaster, GadgetTypeMaster, DashboardUserSetting |
| 2  | Model: organization             | `src/iot_app/models/organization.py`                                                                                                                        | -                                                                       | 完了           | OrganizationClosure・OrganizationMaster。DB設計書準拠 |
| 3  | Model: device                   | `src/iot_app/models/device.py`                                                                                                                              | -                                                                       | 完了           | DeviceMaster。DB設計書準拠                            |
| 4  | Service: common                 | `src/iot_app/services/customer_dashboard/common.py`                                                                                                         | `tests/unit/services/customer_dashboard/test_common.py`                 | 完了           | 約30関数（高位関数含む）                              |
| 5  | Form: common                    | `src/iot_app/forms/customer_dashboard/common.py`                                                                                                            | -                                                                       | 完了           | DashboardForm, DashboardGroupForm, GadgetForm 実装済み |
| 6  | エラーハンドラー（409追加）     | `src/iot_app/common/error_handlers.py`                                                                                                                      | -                                                                       | 完了           | 実装時注意事項 No.6。@app.errorhandler(409) 追加      |
| 7  | Blueprint定義 + app登録         | `src/iot_app/views/analysis/__init__.py`<br>`src/iot_app/__init__.py`（追記）                                                                              | -                                                                       | 完了           | customer_dashboard_bp の Blueprint定義・登録           |
| 8  | View/Routes                     | `src/iot_app/views/analysis/customer_dashboard.py`                                                                                                          | -                                                                       | 完了           | 27ルート（No.1〜27）。No.17/18/23/25はstub（501）。`decorators/auth.py`にrequire_authスタブ追加 |
| 9  | Template: メイン画面            | `src/iot_app/templates/analysis/customer_dashboard/index.html`                                                                                              | -                                                                       | 完了           | CDS-001                                               |
| 10 | Template: モーダル群 + JavaScript | `src/iot_app/templates/analysis/customer_dashboard/modals/`（10ファイル）<br>`src/iot_app/static/js/components/customer_dashboard.js`<br>`src/iot_app/static/css/components/customer_dashboard.css` | -                                                                       | 完了           | CDS-002〜005 モーダル全種 + AJAX・D&D・自動更新JS + BEM CSS |

**実装順序:** 1 → 2 → 3 → 4 → 6 → 7 → 8 → 9 → 10（タスク5は完了済みスキップ）

---

## 実装フロー状態

| 状態     | 意味                 |
| -------- | -------------------- |
| 未着手   | 実装未開始           |
| 実装中   | ① 実装 実施中        |
| テスト中 | ② pytest 実行中      |
| 修正中   | ③ テスト失敗・修正中 |
| 完了     | ④ 全テスト通過       |

---

## セルフレビュー進捗

| 観点                         | 状態   | 確認結果 |
| ---------------------------- | ------ | -------- |
| 機能: 設計書との差分         | 完了   | OK: 27ルート全て実装。No.17/18/23/25は501でガジェット個別仕様に委譲（設計規定通り） |
| 機能: テスト仕様カバレッジ   | 完了   | OK: 104件全テスト通過。テストが要求する全主要関数が実装済み |
| 機能: インターフェース整合性 | 完了   | OK: form→views→servicesの引数・戻り値が一貫性あり |
| 非機能: セキュリティ         | 完了   | OK: SQLAlchemy ORM使用、accessible_org_ids権限チェック全ルート実施、バリデーション完備 |
| 非機能: ログ準拠             | 完了   | OK: エラーログは error_handlers.py の handle_500 が exc_info=True で一元出力。abort(500) 直前の二重 logger.error（21箇所）を削除済み。jsonify 返却の3箇所は error_handlers 経由しないため個別ログを保持 |
| 非機能: エラーハンドリング   | 完了   | OK: 400/404/409/500が設計書に準拠。ロールバック完備。楽観ロック・スコープ外一貫性あり |
