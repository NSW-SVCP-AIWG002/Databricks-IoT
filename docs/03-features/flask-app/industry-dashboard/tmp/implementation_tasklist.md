# 業種別ダッシュボード機能（冷蔵冷凍庫） - 実装タスクリスト

## 概要

このドキュメントは、業種別ダッシュボード機能（FR-006）のソースファイル実装タスクを管理します。
設計書（UI仕様書・ワークフロー仕様書・共通仕様書）をもとに、実装順序・依存関係・担当ファイルを整理します。

**対象機能:**
- IDS-001: 店舗モニタリング画面
- IDS-002: デバイス詳細画面

**参照設計書:**
- [README.md](../README.md) - 機能概要・データモデル・画面一覧
- [ui-specification.md](../ui-specification.md) - 画面レイアウト・UI要素仕様
- [workflow-specification.md](../workflow-specification.md) - 処理フロー・DB連携・エラーハンドリング
- [共通仕様書](../../common/common-specification.md) - HTTPステータスコード・エラーコード等
- [UI共通仕様書](../../common/ui-common-specification.md) - 全画面共通UI仕様
- [Unity Catalog DB設計書](../../common/unity-catalog-database-specification.md) - センサーデータテーブル定義
- [OLTP DB設計書](../../common/app-database-specification.md) - マスタテーブル定義

---

## タスク一覧

### フェーズ1: 基盤層（Blueprint・設定）

| No | タスク | 担当ファイル | 依存タスク | ステータス | 完了日 | 備考 |
|----|--------|-------------|-----------|-----------|--------|------|
| 1-1 | Blueprint ディレクトリ作成 | `src/views/industry_dashboard/__init__.py` | なし | ✅ 完了 | 2026-02-19 | `industry_dashboard_bp` を定義 |
| 1-2 | Blueprint をアプリに登録 | `src/__init__.py` | 1-1 | ✅ 完了 | 2026-02-19 | `create_app()` に `register_blueprint` を追加 |

---

### フェーズ2: Service層

| No | タスク | 担当ファイル | 依存タスク | ステータス | 完了日 | 備考 |
|----|--------|-------------|-----------|-----------|--------|------|
| 2-1 | データスコープ制限関数の実装 | `src/services/industry_dashboard_service.py` | なし | ✅ 完了 | 2026-02-19 | `get_accessible_organizations(organization_id)` / `organization_closure` テーブル参照 / workflow-specification.md「②データスコープ制限の適用」 |
| 2-2 | デバイスアクセス権限チェック関数の実装 | `src/services/industry_dashboard_service.py` | 2-1 | ✅ 完了 | 2026-02-19 | `check_device_access(device_uuid, accessible_org_ids)` / `device_master` テーブル参照 / workflow-specification.md「①データスコープ制限チェック」 |
| 2-3 | アラート一覧取得関数の実装（店舗モニタリング用） | `src/services/industry_dashboard_service.py` | 2-1 | ✅ 完了 | 2026-02-19 | `get_recent_alerts_with_count(search_params, accessible_org_ids, limit)` / `alert_history`, `alert_setting_master`, `alert_level_master`, `alert_status_master`, `device_master`, `organization_master` テーブル参照 / workflow-specification.md「③アラート一覧取得」 |
| 2-4 | デバイス一覧取得関数の実装 | `src/services/industry_dashboard_service.py` | 2-1 | ✅ 完了 | 2026-02-19 | `get_device_list_with_count(search_params, accessible_org_ids, page, per_page)` / `device_master`, `organization_master`, `device_status_data` テーブル参照 / workflow-specification.md「④デバイス一覧取得」 |
| 2-5 | 最新センサーデータ取得関数の実装 | `src/services/industry_dashboard_service.py` | なし | ✅ 完了 | 2026-02-19 | `get_latest_sensor_data(device_id)` / Unity Catalog `sensor_data_view` 参照 / `db/unity_catalog_connector.py` 使用 / workflow-specification.md「②最新センサーデータ取得」 |
| 2-6 | デバイス詳細アラート取得関数の実装 | `src/services/industry_dashboard_service.py` | 2-1 | ✅ 完了 | 2026-02-19 | `get_device_alerts_with_count(device_id, search_params)` / `alert_history`, `alert_setting_master`, `alert_level_master`, `alert_status_master` テーブル参照 |
| 2-7 | グラフ用センサーデータ取得関数の実装 | `src/services/industry_dashboard_service.py` | なし | ✅ 完了 | 2026-02-19 | `get_graph_data(device_id, search_params)` / Unity Catalog `sensor_data_view` 参照 / 表示期間フィルタ適用 / workflow-specification.md「②グラフ用データ取得」 |
| 2-8 | CSVエクスポート関数の実装 | `src/services/industry_dashboard_service.py` | 2-7 | ✅ 完了 | 2026-02-19 | `export_sensor_data_csv(device, search_params)` / 全センサーデータカラムを出力 / workflow-specification.md「CSVエクスポート」 |
| 2-9 | デフォルト表示期間取得関数の実装 | `src/services/industry_dashboard_service.py` | なし | ✅ 完了 | 2026-02-19 | `get_default_date_range()` / 直近24時間を返す / workflow-specification.md「①表示期間の初期値設定」 |
| 2-10 | 表示期間バリデーション関数の実装 | `src/services/industry_dashboard_service.py` | なし | ✅ 完了 | 2026-02-19 | `validate_date_range(start_datetime_str, end_datetime_str)` / 開始<終了・最大62日 / workflow-specification.md「バリデーション」 |

---

### フェーズ3: Form層

| No | タスク | 担当ファイル | 依存タスク | ステータス | 完了日 | 備考 |
|----|--------|-------------|-----------|-----------|--------|------|
| 3-1 | デバイス詳細検索フォームの実装 | `src/forms/industry_dashboard.py` | なし | ✅ 完了 | 2026-02-19 | `DeviceDetailSearchForm` / `search_start_datetime`・`search_end_datetime` フィールド / CSRF保護 / workflow-specification.md「バリデーション」 |

---

### フェーズ4: View層（ルーティング）

| No | タスク | 担当ファイル | 依存タスク | ステータス | 完了日 | 備考 |
|----|--------|-------------|-----------|-----------|--------|------|
| 4-1 | 店舗モニタリング初期表示ルートの実装 | `src/views/industry_dashboard/views.py` | 1-1, 2-1, 2-3, 2-4 | ✅ 完了 | 2026-02-19 | `GET /industry-dashboard/store-monitoring` / Cookie検索条件管理・ページング対応 / workflow-specification.md「店舗モニタリング初期表示」 |
| 4-2 | 店舗モニタリング検索ルートの実装 | `src/views/industry_dashboard/views.py` | 1-1, 2-1, 2-3, 2-4 | ✅ 完了 | 2026-02-19 | `POST /industry-dashboard/store-monitoring` / フォームから検索条件取得・Cookie保存 / workflow-specification.md「店舗モニタリング検索」 |
| 4-3 | センサー情報表示ルートの実装 | `src/views/industry_dashboard/views.py` | 1-1, 2-2, 2-5 | ✅ 完了 | 2026-02-19 | `GET /industry-dashboard/store-monitoring/<device_uuid>` / デバイスアクセス権限チェック・最新センサーデータ取得 / workflow-specification.md「センサー情報表示」 |
| 4-4 | デバイス詳細初期表示ルートの実装 | `src/views/industry_dashboard/views.py` | 1-1, 2-2, 2-6, 2-7, 2-9 | ✅ 完了 | 2026-02-19 | `GET /industry-dashboard/device-details/<device_uuid>` / Cookie管理・ページング対応・CSVエクスポート分岐 / workflow-specification.md「デバイス詳細初期表示」 |
| 4-5 | デバイス詳細検索ルートの実装 | `src/views/industry_dashboard/views.py` | 1-1, 2-2, 2-6, 2-7, 2-10, 3-1 | ✅ 完了 | 2026-02-19 | `POST /industry-dashboard/device-details/<device_uuid>` / バリデーション・Cookie保存 / workflow-specification.md「デバイス詳細検索（表示期間変更）」 |
| 4-6 | CSVエクスポートルートの実装 | `src/views/industry_dashboard/views.py` | 1-1, 2-2, 2-8 | ✅ 完了 | 2026-02-19 | `GET /industry-dashboard/device-details/<device_uuid>?export=csv` / デバイスアクセス権限チェック / workflow-specification.md「CSVエクスポート」 |

---

### フェーズ5: Template層

| No | タスク | 担当ファイル | 依存タスク | ステータス | 完了日 | 備考 |
|----|--------|-------------|-----------|-----------|--------|------|
| 5-1 | 店舗モニタリング画面テンプレートの実装 | `src/templates/dashboard/store_monitoring.html` | 4-1, 4-2 | ✅ 完了 | 2026-02-19 | (1)画面タイトル・(2)検索フォーム・(3)アラート一覧・(4)デバイス一覧・(5)センサー情報欄 / base.html 継承 / ui-specification.md「IDS-001」 |
| 5-2 | デバイス詳細画面テンプレートの実装 | `src/templates/dashboard/device_details.html` | 4-4, 4-5 | ✅ 完了 | 2026-02-19 | (6)画面タイトル・(7)アクションボタン・(8)デバイス情報・(9)アラート一覧・(10)表示期間変更・(11)CSVエクスポート・(12)時系列グラフ・(13)凡例 / base.html 継承 / ui-specification.md「IDS-002」 |

---

### フェーズ6: 静的ファイル層

| No | タスク | 担当ファイル | 依存タスク | ステータス | 完了日 | 備考 |
|----|--------|-------------|-----------|-----------|--------|------|
| 6-1 | ダッシュボード用CSSの実装 | `src/static/css/components/industry_dashboard.css` | なし | ✅ 完了 | 2026-02-19 | 2カラムレイアウト・センサー情報欄・デバイス情報欄のスタイル / BEM命名規則 / variables.css のCSS変数を使用 / ui-specification.md「画面レイアウト」 |
| 6-2 | main.cssへのインポート追加 | `src/static/css/main.css` | 6-1 | ✅ 完了 | 2026-02-19 | `@import "./components/industry_dashboard.css"` を追加 |
| 6-3 | 時系列グラフ用JSの実装 | `src/static/js/components/industry_dashboard.js` | なし | ✅ 完了 | 2026-02-19 | Apache ECharts 初期化・折れ線グラフ描画・凡例チェックボックス連動・ズーム機能・ツールチップ / ui-specification.md「(12)時系列グラフ」「(13)凡例」 |
| 6-4 | 自動更新機能のJS実装 | `src/static/js/components/industry_dashboard.js` | 6-3 | ✅ 完了 | 2026-02-19 | 60秒ごとにデバイス詳細画面を再取得・自動更新チェックボックス連動 / ui-specification.md「(10.4)自動更新チェックボックス」 |
| 6-5 | 店舗名ドロップダウン検索のJS実装 | `src/static/js/components/industry_dashboard.js` | なし | ✅ 完了 | 2026-02-19 | 入力値で組織名をインクリメンタルサーチ・完全一致/部分一致切り替え / ui-specification.md「(2-1)店舗名検索」 |
| 6-6 | センサー情報欄表示切り替えのJS実装 | `src/static/js/components/industry_dashboard.js` | なし | ✅ 完了 | 2026-02-19 | センサー情報表示ボタン押下時に右欄を表示・未選択時は非表示 / ui-specification.md「(5)センサー情報表示」 |

---

### フェーズ7: テスト層

| No | タスク | 担当ファイル | 依存タスク | ステータス | 完了日 | 備考 |
|----|--------|-------------|-----------|-----------|--------|------|
| 7-1 | Service層単体テストの実装 | `tests/unit/services/test_industry_dashboard_service.py` | 2-1〜2-10 | ✅ 完了 | 2026-02-19 | 各関数の正常系・異常系テスト / `unittest.mock` でDB・Unity Catalogをモック |
| 7-2 | View層結合テストの実装 | `tests/integration/test_industry_dashboard_routes.py` | 4-1〜4-6 | ✅ 完了 | 2026-02-19 | 全エンドポイントの正常系・異常系・権限チェックテスト / Flask test_client を使用 |

---

## 実装順序

```
フェーズ1（Blueprint登録）
    ↓
フェーズ2（Service層）← Unity Catalogコネクタ確認
    ↓
フェーズ3（Form層）
    ↓
フェーズ4（View層）← フェーズ2・3に依存
    ↓
フェーズ5（Template層）← フェーズ4に依存
    ↓
フェーズ6（静的ファイル層）← フェーズ5と並行可
    ↓
フェーズ7（テスト層）← 全フェーズ完了後
```

---

## 実装上の注意事項

### 既存コードとの整合性

| 確認項目 | 参照先 | 内容 |
|---------|--------|------|
| Unity Catalog接続 | `src/db/unity_catalog_connector.py` | `g.databricks_token` を使用した接続方式を踏襲 |
| 認証デコレータ | `src/decorators/auth.py` | `@require_role` ではなく `@require_auth` を使用（全ロール許可） |
| エラーハンドラー | `src/common/error_handlers.py` | 400/403/404→モーダル、500→エラーページ |
| Cookieキー名 | workflow-specification.md | `store_monitoring_search_params`、`device_details_search_params` |
| Blueprint名 | workflow-specification.md | `dashboard_bp`（または `industry_dashboard_bp`）として実装 |
| ページあたり件数 | ui-specification.md | アラート一覧・デバイス一覧ともに10件/ページ固定 |
| アラート取得上限 | ui-specification.md | 過去30日以内のアラート履歴を30件取得 |

### Apache ECharts

| 確認項目 | 内容 |
|---------|------|
| ライブラリ取得 | CDNまたはローカル配置を確認（`base.html` に追記要否確認） |
| グラフ設定 | ui-specification.md「(12-1)時系列グラフ」記載の色・線種に従う |
| 複数Y軸 | 温度系・回転数系・ヒータ出力系の3軸対応 |
| ズーム | 横軸・縦軸の両方に対応 |

### センサーデータCSVカラム順

workflow-specification.md「CSVエクスポート」のヘッダー行定義に従う（23カラム）。

---

## ステータス凡例

| 記号 | ステータス |
|------|-----------|
| ✅ | 完了 |
| 🔄 | 進行中 |
| ⬜ | 未着手 |
| ❌ | 中断/課題あり |

---

## 更新履歴

| 日付 | 更新内容 |
|------|---------|
| 2026-02-19 | 初版作成 |
| 2026-02-19 | タスク1-1完了: `src/views/industry_dashboard/__init__.py` 作成 |
| 2026-02-19 | タスク1-2〜7-2完了: 全ソースファイル実装完了 |
