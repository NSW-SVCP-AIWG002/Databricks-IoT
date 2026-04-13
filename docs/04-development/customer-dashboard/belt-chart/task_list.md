# belt-chart 実装タスクリスト

## タスク一覧

| #   | タスク名               | 対象ファイル                                                                                    | 対応テスト                                                         | 実装フロー状態 | 備考 |
| --- | ---------------------- | ----------------------------------------------------------------------------------------------- | ------------------------------------------------------------------ | -------------- | ---- |
| 1   | フォーム               | `src/iot_app/forms/customer_dashboard/belt_chart.py`                                            | `tests/unit/services/test_customer_dashboard/belt_chart.py`（TestBeltChartGadgetForm*） | 完了           | 新規作成 |
| 2   | サービス               | `src/iot_app/services/customer_dashboard/belt_chart.py`                                         | `tests/unit/services/test_customer_dashboard/belt_chart.py`（全クラス） | 完了           | 新規作成 |
| 3   | ビュー                 | `src/iot_app/views/analysis/customer_dashboard/belt_chart.py`                                   | -                                                                  | 完了           | 新規作成 |
| 4   | ガジェットHTML         | `src/iot_app/templates/analysis/customer_dashboard/gadgets/belt_chart.html`                     | -                                                                  | 完了           | 新規作成 |
| 5   | モーダルHTML           | `src/iot_app/templates/analysis/customer_dashboard/gadgets/modals/belt_chart.html`              | -                                                                  | 完了           | 新規作成 |
| 6   | CSS                    | `src/iot_app/static/css/components/customer_dashboard/belt_chart.css`                           | -                                                                  | 完了           | 新規作成 |
| 7   | JS                     | `src/iot_app/static/js/components/customer_dashboard/belt_chart.js`                             | -                                                                  | 完了           | 新規作成 |

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
| 機能: 設計書との差分         | 完了 | device_name追加返却あり（実害なし）。その他差分はテストコード優先として記録済み |
| 機能: テスト仕様カバレッジ   | 完了 | 全サービス・フォームテスト対象関数を実装済み |
| 機能: インターフェース整合性 | 完了 | 引数・戻り値・例外すべて一致 |
| 非機能: セキュリティ         | 完了 | 問題なし |
| 非機能: ログ準拠             | 完了 | logger.error に exc_info=True を追加して修正済み |
| 非機能: エラーハンドリング   | 完了 | 問題なし |

## 設計書・テストコード矛盾点（テストコード優先）

| # | 項目 | 設計書 | テストコード（採用） |
|---|------|-------|-------------------|
| 1 | フォームフィールド名（タイトル） | `form.title.data` | `gadget_name` フィールド |
| 2 | `format_belt_chart_data` week ラベル | `d.strftime('%m/%d')` | `E`（例: `Sun`） |
| 3 | `format_belt_chart_data` month ラベル | `d.strftime('%m/%d')` | `DD`（例: `15`） |
| 4 | CSV ヘッダー | `['timestamp'] + sensor_names` | `['デバイス名', 時間名, series名...]` |
| 5 | CSV 関数 | View 層で直接 writer.writerow | `generate_belt_chart_csv(chart_data, display_unit, base_datetime, device_name)` |
