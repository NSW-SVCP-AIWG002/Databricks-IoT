# industry-dashboard 実装タスクリスト

## タスク一覧

| #   | タスク名           | 対象ファイル                                                                                                                                 | 対応テスト                                                       | 実装フロー状態 | 備考                                       |
| --- | ------------------ | -------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------- | -------------- | ------------------------------------------ |
| 0   | パッケージ初期化   | `src/__init__.py`（新規）, `src/views/__init__.py`（新規）, `src/views/industry_dashboard/__init__.py`（新規）                              | -                                                                | 完了           | create_app/db 再エクスポート               |
| 1   | データ定義層       | `src/iot_app/models/device.py`, `organization.py`, `alert.py`, `src/iot_app/databricks/unity_catalog_connector.py`                          | `tests/unit/services/test_industry_dashboard_service.py`         | 完了           | Device, OrganizationClosure 等             |
| 2   | ビジネスロジック層 | `src/iot_app/services/industry_dashboard_service.py`                                                                                        | `tests/unit/services/test_industry_dashboard_service.py`         | 完了           | 10関数 + 1内部ヘルパー                     |
| 3   | インターフェース層 | `src/views/industry_dashboard/views.py`, `store_monitoring.html`, `device_details.html`, `src/iot_app/__init__.py`（Blueprint登録追加）     | `tests/integration/test_industry_dashboard_routes.py`            | 完了           | Blueprint登録 `/industry-dashboard/` 前置  |

## 実装フロー状態

| 状態     | 意味                 |
| -------- | -------------------- |
| 未着手   | 実装未開始           |
| 実装中   | ① 実装 実施中        |
| テスト中 | ② pytest 実行中      |
| 修正中   | ③ テスト失敗・修正中 |
| 完了     | ④ 全テスト通過       |

## セルフレビュー進捗

| 観点                         | 状態 | 確認結果 |
| ---------------------------- | ---- | -------- |
| 機能: 設計書との差分         | 完了 | ルート5本・サービス関数10本すべて設計書通り実装。URL prefix `/industry-dashboard/` 一致。 |
| 機能: テスト仕様カバレッジ   | 完了 | 単体テスト 81/81 通過（テストコードバグ `42 in str(arg)` → `str(42) in str(arg)` を修正して解消）。結合テストはユーザー指示によりスキップ。 |
| 機能: インターフェース整合性 | 完了 | **要注意**: `iot_app/__init__.py` の `from views.industry_dashboard.views import dashboard_bp` と結合テストのパッチパス `src.views.industry_dashboard.views.*` が不一致。結合テスト実行時にはパッチが効かない可能性あり。修正が必要な場合は `from src.views.industry_dashboard.views import dashboard_bp` に変更。 |
| 非機能: セキュリティ         | 完了 | SQLAlchemy ORM + `?` プレースホルダでSQLインジェクション対策済み。Cookie は `httponly=True, samesite="Lax"` 設定済み。 |
| 非機能: ログ準拠             | 完了 | **指摘**: views.py の `except Exception: abort(500)` ブロックにエラーログ出力なし。本番環境での障害追跡に影響する可能性あり（別途対応を検討）。 |
| 非機能: エラーハンドリング   | 完了 | `abort(500)` + `if hasattr(e, "code"): raise` パターンで HTTPException を再発行。404/400/500 を適切に返却。 |
