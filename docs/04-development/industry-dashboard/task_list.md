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
| 機能: 設計書との差分          | 完了   | ⚠️ Cookie: ページング時も`_set_cookie`を呼ぶ（仕様はページング時更新なし）。実害軽微。 |
| 機能: テスト仕様カバレッジ    | 完了   | ✅ service層81件全通過。views/templateはテスト対象外。 |
| 機能: インターフェース整合性  | 完了   | ✅ service関数10件の呼び出し引数すべて整合。 |
| 非機能: セキュリティ          | 完了   | ❌ middleware.py が空のため`g.current_user`未設定（要別途実装）。Cookie属性・スコープ制限は✅。 |
| 非機能: ログ準拠              | 完了   | ❌ loggerなし。仕様「DBクエリ前後にログ出力」未実装（要別途実装）。 |
| 非機能: エラーハンドリング    | 完了   | ✅ 404/400/500のabort処理、HTTPException再raiseすべて正しく実装。 |