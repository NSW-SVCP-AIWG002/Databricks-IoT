# 00-rules ディレクトリ修正作業進捗

## 作業概要
別案件（タスク管理アプリ）から流用した00-rulesファイルを、Databricks IoTシステムのアーキテクチャに合わせて修正する作業。

---

## ✅ 完了済み作業

### Phase 1: 不要ファイル削除・新規ファイル作成
- [x] `package-manager-rule.md` を削除（Python/requirements.txt管理のため不要）
- [x] `react-rule.md` を削除
- [x] `theme-rule.md` を削除
- [x] `flask-jinja2-rule.md` を新規作成（Flask + Jinja2実装ルール、簡潔版）
- [x] `css-design-token-rule.md` を新規作成（CSSデザイントークン管理ルール、簡潔版）
- [x] `README.md` を更新（プロジェクト名、技術スタック、ファイルリスト反映）

---

## ✅ Phase 2 完了済み作業

#### 1. `general-rule.md` ✅ 完了
**修正箇所**:
- [x] line 4: `rc-docs/00-rules/**/*.md` → `docs/00-rules/**/*.md`
- [x] line 10: `rc-docs/` ディレクトリ → `docs/` ディレクトリ
- [x] line 16: `app/task-api/api/` - OpenAPI定義（API仕様） → **削除**（Databricks IoTには存在しない）

#### 2. `test-rule.md` ✅ 完了
**修正箇所**:
- [x] line 15: `バックエンド（Spring Boot）とフロントエンド（Next.js）` → `バックエンド（Flask）とフロントエンド（Flask + Jinja2）`
- [x] lines 75-95: Spring Boot (`./gradlew test`) → Flask pytest (`pytest`, `pytest --cov`)
- [x] lines 97-123: Bun/Next.js テストコマンド → **削除**（Flask + Jinja2の場合不要）
- [x] lines 206-213: `app/task-api/src/repository/users/` → Databricks IoT実ディレクトリ構造（例: `app/blueprints/admin/`, `app/services/`）
- [x] lines 257-269: Next.js コンポーネントテスト → **削除**

#### 3. `unit-testing-rule.md` ✅ 完了
**修正箇所**:
- [x] lines 4-6: glob パターンを Databricks IoT のテストパスに修正（`app/**/*_test.py`）
- [x] lines 70-100: Spring Boot + JUnit → Flask + pytest の実行コマンド
- [x] lines 86-100: Bun/Next.js → **削除**
- [x] lines 104-139: Spring Boot + Mockito コード例 → Flask + pytest + unittest.mock コード例
- [x] lines 141-164: React Testing Library コード例 → **削除**

---

## 🔄 Phase 2 残作業

#### 4. `integration-testing-rule.md` ⏸️ 一時停止（部分完了）
**修正箇所**:
- [x] lines 4-5: glob パターンを Databricks IoT のテストパスに修正（`tests/integration/**/*.py`）
- [ ] lines 11: フロントエンド結合テストの記述削除
- [ ] lines 31-36: フロントエンド結合テスト対象の記述削除
- [ ] lines 40-56: ファイル配置例を Flask 構造に変更
- [ ] lines 62-86: 実行方法を pytest に変更
- [ ] lines 90-133: Spring Boot + TestRestTemplate コード例 → Flask + pytest + Flask test client コード例
- [ ] lines 136-178: MSW + React Testing Library コード例 → **削除**
- [ ] lines 184-198: フロントエンド関連ベストプラクティス → **削除**

#### 5. `e2e-testing-rule.md` 🔲 未着手
**修正箇所**:
- [ ] lines 11-12: `http://localhost:3000` (API), `http://localhost:3001` (Web) → Databricks Apps URL（`https://[workspace-url]/apps/[app-name]`）
- [ ] line 12: `demo@example.com / password123` → **削除**（Databricks User認証はリバースプロキシ経由）
- [ ] lines 15-18: タスク管理CUJ（`ログイン→タスク一覧表示→タスク操作`）→ Databricks IoT CUJ（`ログイン→ダッシュボード表示→デバイス管理`、`アラート設定→通知履歴確認`）
- [ ] lines 21-24: `app/task-api` マイグレーション → Databricks IoT のセットアップ手順
- [ ] lines 30-33: Bun コマンド (`bun run test:e2e`) → pytest + Playwright コマンド（例: `pytest tests/e2e/`）

---

## 📝 修正方針
- 実装例は最小限に圧縮（react-rule.md、flask-jinja2-rule.md と同等の簡潔さ）
- Spring Boot/JUnit/Next.js/Jest → Flask/pytest に全面書き換え
- Databricks IoT固有のディレクトリ構造、CUJ、URL構成に合わせる
- 汎用的なテストベストプラクティスはそのまま流用

---

## 🎯 再開時のアクションプラン
1. `general-rule.md` から順次修正
2. 各ファイル修正後、このTODOファイルのチェックボックスを更新
3. 全修正完了後、このTODOファイルを削除または完了マークに変更
