# customer-dashboard/bar-chart 実装タスクリスト

## タスク一覧

| #   | タスク名                                       | 対象ファイル                                                  | 対応テスト                          | 実装フロー状態 | 備考 |
| --- | ---------------------------------------------- | ------------------------------------------------------------- | ----------------------------------- | -------------- | ---- |
| 1   | 例外クラス定義                                 | `src/iot_app/common/exceptions.py`                            | Section 6〜10 (ValidationError, NotFoundError) | 完了           |      |
| 2   | ダッシュボードモデル定義                       | `src/iot_app/models/dashboard.py`                             | Section 8, 9 (DashboardGadgetMaster, GadgetTypeMaster) | 完了           |      |
| 3   | サービス層実装（定数・バリデーション・データ整形） | `src/iot_app/services/customer_dashboard/bar_chart_service.py` | Section 1〜5 (INTERVAL_MINUTES, validate_chart_params, format_bar_chart_data, aggregate_values) | 完了           |      |
| 4   | サービス層実装（CSV生成・エクスポート）        | `src/iot_app/services/customer_dashboard/bar_chart_service.py` | Section 7 (generate_bar_chart_csv, export_bar_chart_csv) | 完了           |      |
| 5   | サービス層実装（ガジェット登録・デバイスチェック） | `src/iot_app/services/customer_dashboard/bar_chart_service.py` | Section 6, 8, 9, 10 (validate_gadget_registration, register_bar_chart_gadget, check_device_access) | 完了           |      |
| 6   | サービス層実装（データ取得 fetch/execute）     | `src/iot_app/services/customer_dashboard/bar_chart_service.py` | Section 11〜13 (fetch_bar_chart_data, execute_silver_query, execute_gold_query) | 完了           |      |
| 7   | フォーム定義                                   | `src/iot_app/forms/customer_dashboard.py`                     | BarChartGadgetForm                          | 完了           |      |
| 8   | Viewルーティング実装                           | `src/iot_app/views/analysis/customer_dashboard.py`            | 5エンドポイント（初期表示/データ取得/登録モーダル/登録実行/CSVエクスポート） | 完了           |      |
| 9   | ダッシュボード画面テンプレート                 | `src/iot_app/templates/analysis/customer_dashboard/index.html` | 共通UI・ガジェット枠 | 完了           |      |
| 10  | 棒グラフ登録モーダルテンプレート               | `src/iot_app/templates/analysis/customer_dashboard/modals/gadget_register/bar_chart.html` | 登録フォーム | 完了           |      |
| 11  | 棒グラフガジェットJS                           | `src/iot_app/static/js/components/customer_dashboard/bar_chart.js` | ECharts描画・AJAX | 完了           |      |
| 12  | 棒グラフガジェットCSS                          | `src/iot_app/static/css/components/customer_dashboard/bar_chart.css` | ガジェットスタイル | 完了           |      |

## 実装フロー状態

| 状態     | 意味                 |
| -------- | -------------------- |
| 未着手   | 実装未開始           |
| 実装中   | ① 実装 実施中        |
| テスト中 | ② pytest 実行中      |
| 修正中   | ③ テスト失敗・修正中 |
| 完了     | ④ 全テスト通過       |

## セルフレビュー進捗

| 観点                         | 状態   | 確認結果 |
| ---------------------------- | ------ | -------- |
| 機能: 設計書との差分         | 完了   | 5エンドポイント・バリデーション・エラー処理すべて設計書通り |
| 機能: テスト仕様カバレッジ   | 完了   | 149/149 通過 |
| 機能: インターフェース整合性 | 完了   | 引数・戻り値・例外型が設計書と一致 |
| 非機能: セキュリティ         | 完了   | ORM使用・センサー値のログ出力なし |
| 非機能: ログ準拠             | 完了   | get_logger使用・エラー時logger.error |
| 非機能: エラーハンドリング   | 完了   | view層でcolumn_name未渡し問題を要確認（ユーザー確認済み） |
