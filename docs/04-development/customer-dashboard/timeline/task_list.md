# 時系列グラフガジェット 実装タスクリスト

## タスク一覧

| #  | タスク名                          | 対象ファイル                                                                                   | 対応テスト                                                                 | 実装フロー状態 | 備考 |
|----|-----------------------------------|-----------------------------------------------------------------------------------------------|----------------------------------------------------------------------------|----------------|------|
| 1  | データ定義層: モデル実装           | `src/iot_app/models/dashboard.py`                                                             | `tests/unit/models/test_customer_dashboard/timeline.py`                    | 完了           | `DashboardGadgetMaster`, `GadgetTypeMaster` |
| 2  | ビジネスロジック層: サービス実装   | `src/iot_app/services/customer_dashboard/timeline_service.py`                                 | `tests/unit/services/test_customer_dashboard/timeline_service.py`          | 完了           | `validate_chart_params`, `validate_gadget_registration`, `format_timeline_data`, `generate_timeline_csv`, `fetch_timeline_data`, `register_gadget`, `get_accessible_org_ids`, `get_gadget_in_scope`, `get_active_gadgets_in_scope`, `get_chart_column_names`, `check_device_in_scope`, `get_timeline_create_context`（①②ステップ追加・グループ取得修正） |
| 3  | インターフェース層: フォーム実装   | `src/iot_app/forms/customer_dashboard.py`                                                     | -                                                                          | 完了           | `TimelineGadgetForm` (Flask-WTF) |
| 4  | インターフェース層: ビュー実装     | `src/iot_app/views/analysis/customer_dashboard.py`                                            | -                                                                          | 完了           | 5ルート（初期表示・データ取得・登録モーダル・登録実行・CSVエクスポート）。デバイス固定モード時スコープチェック追加、`gadget_timeline_create` NotFoundError → 404対応、未使用インポート（`generate_timeline_csv`）削除 |
| 5  | インターフェース層: テンプレート実装 | `src/iot_app/templates/analysis/customer_dashboard/index.html`<br>`src/iot_app/templates/analysis/customer_dashboard/modals/gadget_register/timeline.html` | -                                                                          | 完了           | ガジェット埋め込み・登録モーダル |
| 6  | インターフェース層: JS実装         | `src/iot_app/static/js/components/customer_dashboard/timeline.js`                             | -                                                                          | 完了           | ECharts 時系列グラフ描画・AJAX・CSV エクスポート |
| 7  | インターフェース層: CSS実装        | `src/iot_app/static/css/components/customer_dashboard/timeline.css`                           | -                                                                          | 完了           | customer-dashboard・gadget・timeline・gadget-register・timeline-register |

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

| 観点                         | 状態     | 確認結果 |
| ---------------------------- | -------- | -------- |
| 機能: 設計書との差分         | 完了     | A〜C: 前回セッション修正済み。追加修正: ①デバイス固定モードのスコープチェック欠落（`check_device_in_scope` 追加・view で `abort(404)` 対応）②`get_timeline_create_context` の①②ステップ（ユーザー設定取得・ダッシュボード取得・404チェック）追加、グループ取得を `dashboard_id` 限定に修正③未使用インポート（`generate_timeline_csv`）削除 |
| 機能: テスト仕様カバレッジ   | 完了     | 80テスト通過（services: 新関数4クラス11件追加）。全通過確認済み |
| 機能: インターフェース整合性 | 完了     | 引数・戻り値・例外が設計書と一致。`get_timeline_create_context` に `current_user_id` 引数追加 |
| 非機能: セキュリティ         | 完了     | ORM使用・Jinja2自動エスケープ・Flask-WTF CSRF保護・organization_closure によるデータスコープチェック実装済み。デバイス固定モード時のスコープチェック追加済み |
| 非機能: ログ準拠             | 完了     | 全エラーログに `exc_info=True` 追加済み（timeline_service.py・customer_dashboard.py）。logging-specification.md §7 準拠 |
| 非機能: エラーハンドリング   | 完了     | `gadget_timeline_register` に `except AppValidationError` を追加し 400 で処理。ValidationError の握りつぶし解消済み |

---

## 実装メモ

### タスク #1: モデル実装

**`DashboardGadgetMaster`** カラム定義:

| カラム名 | 型 | 制約 |
|---|---|---|
| gadget_id | INT | PK, AUTO |
| gadget_uuid | VARCHAR(36) | UNIQUE, NOT NULL |
| gadget_name | VARCHAR(100) | NOT NULL |
| gadget_type_id | INT | FK → gadget_type_master |
| dashboard_group_id | INT | NOT NULL |
| chart_config | TEXT | NOT NULL |
| data_source_config | TEXT | NOT NULL |
| position_x | INT | default=0 |
| position_y | INT | default=0 |
| gadget_size | VARCHAR(10) | NOT NULL |
| display_order | INT | default=0 |
| create_date | DATETIME | NOT NULL |
| creator | INT | NOT NULL |
| update_date | DATETIME | NOT NULL |
| modifier | INT | NOT NULL |
| delete_flag | BOOLEAN | default=False |

**`GadgetTypeMaster`** カラム定義:

| カラム名 | 型 | 制約 |
|---|---|---|
| gadget_type_id | INT | PK, AUTO |
| gadget_type_name | VARCHAR(100) | NOT NULL |
| delete_flag | BOOLEAN | default=False |

---

### タスク #2: サービス実装

**実装対象関数:**

| 関数名 | 概要 |
|---|---|
| `validate_chart_params(start_datetime, end_datetime)` | 日時パラメータのバリデーション（形式・必須・24時間制約）。True/False を返す |
| `validate_gadget_registration(params)` | ガジェット登録パラメータのバリデーション。失敗時は `ValidationError` を raise |
| `format_timeline_data(rows, left_column_name, right_column_name)` | DBの行データを ECharts 用 labels/left_values/right_values に変換 |
| `generate_timeline_csv(rows, left_label, right_label, left_column_name, right_column_name)` | センサーデータ行からCSV文字列を生成（UTF-8 BOM付き） |
| `fetch_timeline_data(gadget_uuid, start_datetime, end_datetime, limit=100)` | gadget_uuidでガジェット設定取得→デバイスID決定→センサーデータ取得 |
| `register_gadget(params, current_user_id)` | バリデーション→`DashboardGadgetMaster` INSERT→コミット。失敗時はロールバック |

**依存する例外クラス:**
- `iot_app.common.exceptions.ValidationError`
- `iot_app.common.exceptions.NotFoundError`
- `sqlalchemy.exc.IntegrityError`

---

### タスク #3: フォーム実装

**`TimelineGadgetForm`** フィールド:

| フィールド名 | 型 | バリデーション |
|---|---|---|
| title | StringField | DataRequired, Length(max=20) |
| device_mode | RadioField | DataRequired, choices=['fixed','variable'] |
| device_id | IntegerField | Optional（device_mode='fixed'時は必須） |
| group_id | IntegerField | DataRequired |
| left_item_id | IntegerField | DataRequired |
| right_item_id | IntegerField | DataRequired |
| left_min_value | FloatField | Optional |
| left_max_value | FloatField | Optional |
| right_min_value | FloatField | Optional |
| right_max_value | FloatField | Optional |
| gadget_size | SelectField | DataRequired, choices=['2x2','2x4'] |

---

### タスク #4: ビュー実装

**実装対象ルート:**

| ルート | メソッド | 関数名 |
|---|---|---|
| `/analysis/customer-dashboard` | GET | `customer_dashboard` |
| `/analysis/customer-dashboard/gadgets/<gadget_uuid>/data` | POST | `gadget_timeline_data` |
| `/analysis/customer-dashboard/gadgets/timeline/create` | GET | `gadget_timeline_create` |
| `/analysis/customer-dashboard/gadgets/timeline/register` | POST | `gadget_timeline_register` |
| `/analysis/customer-dashboard/gadgets/<gadget_uuid>` | GET | `gadget_csv_export` |
