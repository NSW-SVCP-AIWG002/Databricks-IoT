# 円グラフガジェット 実装タスクリスト

## タスク一覧

| #  | タスク名               | 対象ファイル                                                                                                                                                                                                                                                                | 対応テスト                                                                               | 実装フロー状態 | 備考                                                                                              |
|----|------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------|----------------|---------------------------------------------------------------------------------------------------|
| 1  | フォーム実装           | src/iot_app/forms/customer_dashboard/circle_chart.py                                                                                                                                                                                                                       | tests/unit/services/test_customer_dashboard/circle_chart.py §1〜4, 14                  | 完了           | CircleChartGadgetForm（gadget_name / measurement_item_ids / device_mode / device_id / group_id） |
| 2  | サービス層実装         | src/iot_app/services/customer_dashboard/circle_chart.py                                                                                                                                                                                                                    | tests/unit/services/test_customer_dashboard/circle_chart.py §5, 14, 16, 17             | 完了           | format_circle_chart_data / fetch_circle_chart_data / create_circle_chart_gadget / get_gadget_by_uuid |
| 3  | インターフェース層実装 | src/iot_app/views/analysis/customer_dashboard/circle_chart.py, src/iot_app/templates/analysis/customer_dashboard/gadgets/circle_chart.html, src/iot_app/templates/analysis/customer_dashboard/gadgets/modals/circle_chart.html, src/iot_app/static/js/components/customer_dashboard/circle_chart.js, src/iot_app/static/css/components/customer_dashboard/circle_chart.css | tests/unit/services/test_customer_dashboard/circle_chart.py（全129件通過）              | 完了           | handle_gadget_data / handle_gadget_create / handle_gadget_register / テンプレート / JS / CSS     |

## 実装フロー状態

| 状態     | 意味                 |
|----------|----------------------|
| 未着手   | 実装未開始           |
| 実装中   | ① 実装 実施中        |
| テスト中 | ② pytest 実行中      |
| 修正中   | ③ テスト失敗・修正中 |
| 完了     | ④ 全テスト通過       |

## セルフレビュー進捗

| 観点                         | 状態   | 確認結果 |
|------------------------------|--------|----------|
| 機能: 設計書との差分         | 完了   | 差分なし ✓（handle_gadget_create の try/except 追加済み） |
| 機能: テスト仕様カバレッジ   | 完了   | 129 passed / 0 failed ✓ |
| 機能: インターフェース整合性 | 完了   | 全関数の引数・戻り値・例外が設計書と一致 ✓ |
| 非機能: セキュリティ         | 完了   | ORM/バインドパラメータ・CSRF・スコープチェック・機密情報ログ禁止・XSS対策 全OK ✓ |
| 非機能: ログ準拠             | 完了   | リクエスト前後(自動)・エラーERROR出力準拠 ✓ |
| 非機能: エラーハンドリング   | 完了   | 致命的な握りつぶしなし ✓。全ハンドラーに適切な try/except 実装済み |
