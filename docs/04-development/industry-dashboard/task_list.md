# industry-dashboard 実装タスクリスト

## タスク一覧

| #  | タスク名                    | 対象ファイル                                                                                          | 対応テスト                                                              | 実装フロー状態 | 備考 |
|----|-----------------------------|------------------------------------------------------------------------------------------------------|------------------------------------------------------------------------|--------------|------|
| 1  | ビジネスロジック層            | `src/iot_app/services/industry_dashboard_service.py`                                                | `tests/unit/services/test_industry_dashboard_service.py`               | 完了         | 既存実装済み（10関数 + 1内部ヘルパー） |
| 2  | インターフェース層 - views    | `src/iot_app/views/analysis/industry_dashboard.py`                                                  | なし（単体テスト対象外）                                                 | 完了         | analysis_bp を実装。workflow-specification.md に従う |
| 3  | インターフェース層 - templates | `src/iot_app/templates/analysis/industry_dashboard/store_monitoring.html` `device_details.html`   | なし（単体テスト対象外）                                                 | 完了         | ui-specification.md のワイヤーフレーム・要素詳細に従う |
| 4  | アプリファクトリ更新           | `src/iot_app/__init__.py`                                                                           | なし                                                                    | 完了         | Blueprint登録を正しいパスに修正。`src/__init__.py` も作成 |

---

## タスク詳細

### タスク2: インターフェース層 - views

**実装内容:**
- Blueprint名: `analysis_bp`（Flask登録名: `analysis`）
- ルート一覧（url_prefix なし）:
  - `GET  analysis/industry-dashboard/store-monitoring` → `store_monitoring()`
  - `POST analysis/industry-dashboard/store-monitoring` → `store_monitoring_search()`
  - `GET  analysis/industry-dashboard/store-monitoring/<device_uuid>` → `show_sensor_info(device_uuid)`
  - `GET  analysis/industry-dashboard/device-details/<device_uuid>` → `device_details(device_uuid)`
  - `POST analysis/industry-dashboard/device-details/<device_uuid>` → `device_details_search(device_uuid)`
- CSVエクスポートは `device_details()` 内の `?export=csv` 分岐で処理

### タスク4: アプリファクトリ更新

**変更内容（影響範囲: `create_app()` 内のBlueprint登録1箇所）:**

現在（誤ったパス）:
```python
from views.industry_dashboard.views import dashboard_bp
app.register_blueprint(dashboard_bp)
```

変更後（正しいパス）:
```python
from iot_app.views.analysis.industry_dashboard import analysis_bp
app.register_blueprint(analysis_bp)
```

**影響範囲:** `create_app()` のBlueprint登録1箇所のみ。`/health` ルートおよび `dev_bp` には影響なし。

---

## 実装フロー状態

| 状態     | 意味                 |
|---------|---------------------|
| 未着手   | 実装未開始           |
| 実装中   | ① 実装 実施中        |
| テスト中 | ② pytest 実行中      |
| 修正中   | ③ テスト失敗・修正中 |
| 完了     | ④ 全テスト通過       |

---

## セルフレビュー進捗

| 観点                         | 状態   | 確認結果 |
|-----------------------------|--------|---------|
| 機能: 設計書との差分          | 完了   | ✅ `store_monitoring()`の`_set_cookie`を初期表示時のみ呼ぶよう修正済み（`if is_initial:`）。差分1件: バリデーションエラーを設計書の`redirect`ではなく`abort(400)`で返す（テスト・実装は一致）。 |
| 機能: テスト仕様カバレッジ    | 完了   | ✅ 単体テスト81件通過。結合テスト55件通過（3件は`@pytest.mark.databricks`、実Databricksトークン必要のため環境要因で失敗・除外）。観点1.3/2.1/2.2/3.1/3.4/3.8/4.1/4.2/4.6/5.1/5.3/6.3/9.1/9.2をすべてカバー。SQLインジェクション防御（9.1）・部分一致AND検索（5.1.7/5.1.9/5.1.10）は結合テスト `TestSecurity`・`TestStoreMonitoringPost` で検証済み。 |
| 機能: インターフェース整合性  | 完了   | ✅ service関数9件（`get_accessible_organizations`〜`validate_date_range`）の呼び出し引数すべて仕様書と整合。 |
| 非機能: セキュリティ          | 完了   | ⚠️ middleware.pyのbefore_requestフックで認証を代替（`@require_auth`デコレータなし）。XSSはJinja2自動エスケープ・テスト確認済み✅。データスコープ制限は全5ルートで適用✅。SQLインジェクション防御はORM使用・結合テスト `TestSecurity`（9.1.1〜9.1.3）で確認済み✅。 |
| 非機能: ログ準拠              | 完了   | ✅ 全5ルートに開始・DBクエリ前後・成功・エラーログ実装済み。user_id/device_uuidのコンテキスト付与済み。認証トークン・センサーデータ値のログ出力なし✅。 |
| 非機能: エラーハンドリング    | 完了   | ✅ 404/400/500のabort処理、`hasattr(e, "code")`によるHTTPException再raiseすべて正しく実装。UCエラーも500に変換済み。 |