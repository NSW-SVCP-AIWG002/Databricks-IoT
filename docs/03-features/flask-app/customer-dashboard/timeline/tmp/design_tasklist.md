# ダッシュボードタイムライングラフ - 設計タスク管理表

## タスク一覧

| No | タスク | 説明 | ステータス | 備考 |
|----|--------|------|-----------|------|
| 0 | タスク管理表作成 | design_tasklist.md を作成し、タスク進捗を管理する | ✅ 完了 | このファイル |
| 1 | 要件分析・準備 | 要件定義書・テンプレート・既存ダッシュボード仕様の分析、ギャップ・新規セクションの特定 | ✅ 完了 | design_preparation.md |
| 2 | README.md 作成 | 機能概要書の作成（プロジェクト規約・テンプレート準拠） | ✅ 完了 | - |
| 3 | ui-specification.md 作成 | UI仕様書の作成（テンプレート準拠 + タイムライン固有セクション） | ✅ 完了 | - |
| 4 | workflow-specification.md 作成 | ワークフロー仕様書の作成（テンプレート準拠） | ✅ 完了 | - |
| 5 | 要件クロスチェック | 全出力ファイルと要件定義書の整合性確認 | ✅ 完了 | - |

## 参照ドキュメント

| ドキュメント | パス | 用途 |
|-------------|------|------|
| 機能要件定義書 | `docs/02-requirements/functional-requirements.md` | FR-006 分析機能の要件確認 |
| UI仕様書テンプレート | `docs/03-features/templates/ui-specification-template.md` | UI仕様書の構造準拠 |
| ワークフロー仕様書テンプレート | `docs/03-features/templates/workflow-specification-template.md` | ワークフロー仕様書の構造準拠 |
| 機能別実装ガイド作成ルール | `docs/03-features/feature-guide.md` | 命名規則・構成ルール準拠 |
| 棒グラフ仕様書 | `docs/03-features/flask-app/dashboard-bar-chart/` | 参照パターン（ECharts、CSV出力、ガジェット登録） |
| 円グラフ仕様書 | `docs/03-features/flask-app/dashboard-circle/` | 参照パターン（ガジェット登録、集約方法） |
| 帯グラフ仕様書 | `docs/03-features/flask-app/dashboard-belt-chart/` | 参照パターン（積み上げグラフ、複数項目） |
| 表ガジェット仕様書 | `docs/03-features/flask-app/dashboard-grid/` | 参照パターン（Silver層直接参照、日時範囲） |
| Unity Catalog DB仕様 | `docs/03-features/common/unity-catalog-database-specification.md` | silver_sensor_data テーブル定義 |
| OLTP DB仕様 | `docs/03-features/common/app-database-specification.md` | デバイスマスタ、測定項目マスタ等 |

## 更新履歴

| 日付 | 更新内容 |
|------|---------|
| 2026-02-17 | 初版作成 |
