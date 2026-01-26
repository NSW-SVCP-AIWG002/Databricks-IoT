# テスト実装ルール

## 📑 目次

- [📋 概要](#-概要)
- [📚 テストレベル別の詳細ガイド](#-テストレベル別の詳細ガイド)
- [🛠️ テスト実行コマンド一覧](#️-テスト実行コマンド一覧)
- [📋 テスト実装の基本原則](#-テスト実装の基本原則)
- [📂 テストコードの実装方針とファイル配置ルール](#-テストコードの実装方針とファイル配置ルール)

---

## 📋 概要

このドキュメントでは、バックエンド（Flask）とフロントエンド（Flask + Jinja2）におけるテスト実装の具体的なコード例、実行コマンド、ファイル配置ルールを提供します。

プロジェクトでは以下の 3 つのテストレベルを実施します：

- **単体テスト（Unit Test）**: Service 層、Model 層、Utility 関数の最小単位のテスト
- **結合テスト（Integration Test）**: API 結合テスト、複数モジュール間の連携テスト
- **E2E テスト（End-to-End Test）**: ユーザーの操作フローを再現した画面・機能の統合テスト

各テストレベルの詳細な運用ルールや実装指針については、次のセクション「テストレベル別の詳細ガイド」を参照してください。

---

## 📚 テストレベル別の詳細ガイド

各テストレベルには、より詳細な運用ルールと実装指針が別ドキュメントで定義されています。

### 🧪 単体テスト（Unit Test）

**概要**: Repository 層、UseCase 層、UI コンポーネント層の最小単位をテスト。外部依存をモック化し、ビジネスロジックのみを検証します。

**詳細ドキュメント**: **[単体テスト実装ルール](./unit-testing-rule.md)**

**主な対象**:

- Repository 層の CRUD 操作、検索、フィルタリング
- UseCase 層のビジネスロジック、バリデーション
- UI コンポーネントのレンダリング、ユーザーインタラクション

### 🔗 結合テスト（Integration Test）

**概要**: 複数のモジュールやレイヤーが連携して動作することを検証。API 結合テストでは、実際の HTTP リクエストを送信し、データベースを含む全レイヤーの動作を確認します。

**詳細ドキュメント**: **[結合テスト実装ルール](./integration-testing-rule.md)**

**主な対象**:

- API エンドポイントの HTTP リクエスト/レスポンス
- 認証・認可フロー
- データベースとの連携
- フロントエンド ↔ バックエンドの API 連携

### 🌐 E2E テスト（End-to-End Test）

**概要**: Playwright を使用して、実際のブラウザでユーザーの操作フローを再現。クリティカルユーザージャーニー（CUJ）を中心に、重要な業務フローの完走性を保証します。

**詳細ドキュメント**: **[E2E テスト運用ルール](./e2e-testing-rule.md)**

**主な対象**:

- ログイン → タスク操作 → ログアウトの一連フロー
- 契約管理の検索・絞り込み・詳細参照・登録
- 管理者向けマネジメント業務の成功パス
- クロスブラウザ/レスポンシブ対応の確認

**重要**: E2E テストは「顧客が達成したい成果」に焦点を当て、細かなバリデーションや境界値検証は単体テスト・結合テストで担保します。

---

## 🛠️ テスト実行コマンド一覧

### Flask アプリケーション

```bash
# 全てのテストを実行
pytest

# カバレッジ付きで実行
pytest --cov=app --cov-report=html

# ウォッチモードで実行（pytest-watchプラグイン使用）
ptw

# 特定のテストファイルのみ実行
pytest tests/device_service_test.py

# 特定のテストクラスのみ実行
pytest tests/device_service.py_test::TestDeviceService

# 特定のテストメソッドのみ実行
pytest tests/device_service_test.py::TestDeviceService::create_device_test

# 結合テストのみ実行（マーカー使用）
pytest -m integration

# 単体テストのみ実行（マーカー使用）
pytest -m unit

# E2Eテストを実行（Playwright使用）
pytest tests/e2e/

# 詳細な出力で実行
pytest -v

# カバレッジレポートを確認
open htmlcov/index.html
```

---

## 📋 テスト実装の基本原則

### 1. テストの独立性

- 各テストは他のテストに依存せず、独立して実行できるように設計する
- テストの実行順序に依存しない
- `@BeforeEach`/`@AfterEach`（JUnit）または`beforeEach`/`afterEach`（Jest）を使ってセットアップ・クリーンアップを行う
- グローバル変数の共有を避ける

### 2. AAA パターン（Arrange-Act-Assert）

- **Arrange（準備）**: テストに必要なデータやモックをセットアップ
- **Act（実行）**: テスト対象の関数やメソッドを実行
- **Assert（検証）**: 期待される結果を検証

### 3. テストの可読性

- テスト名は「何をテストしているか」を明確に示す
- `@DisplayName`（JUnit）を使用して日本語のテスト名を記述
- エラーメッセージは具体的で理解しやすいものにする

### 4. モック・スタブの適切な使用

- 外部依存（データベース、外部 API 等）は適切にモック化する
- Mockito の`@Mock`、`@InjectMocks`を使用（Spring Boot）
- MSW を使用して API をモック化（Next.js）
- 過度なモック化は避け、単体テストと結合テストのバランスを考慮する

### 5. エラーハンドリングのテスト

- 正常系だけでなく、異常系のテストも必ず実装する
- 境界値やエッジケースのテストを含める
- `assertThatThrownBy`（AssertJ）または`expect().toThrow()`（Jest）を使用

### 6. テストデータの管理

- テストデータはファクトリ関数やビルダーパターンを使って生成する
- `@DataJpaTest`でテスト用のデータベースを使用（Spring Boot）
- MSW でテスト用の API レスポンスを定義（Next.js）

### 7. 非同期処理の扱い

- `async/await`を適切に使用する（Next.js）
- `waitFor`を使用して非同期処理の完了を待つ（React Testing Library）
- タイムアウトやレースコンディションに注意する

### 8. テストのクリーンアップ

- 各テストの前後で適切にセットアップ・クリーンアップを行う
- データベースのトランザクションを使用してロールバック（Spring Boot）
- リソース（データベース接続、ファイルハンドル等）は適切に解放する

---

## 📂 テストコードの実装方針とファイル配置ルール

### テスト項目書とテストコードの関係

#### テスト項目書（`docs/06-testing/`配下の spec.md）の役割

- **機能単位でテスト項目を管理**する仕様書
- **目的**: テストカバレッジの把握、レビュー、進捗管理
- **例**: `docs/06-testing/unit-test/user-management-spec.md` には ビジネスロジック、ドメインルール、UI コンポーネント単位の全テスト項目を記載

#### 実際のテストコード実装の方針

テスト項目書は**機能単位**でまとめられていますが、実際のテストコード実装では以下のように**適切な粒度で分割**してください。

---

### Flask アプリケーション テストコードのファイル配置

#### 単体テスト（Unit Test）

**配置ルール**: Service/Model/Utility 単位でファイル分割

**配置場所**: 実装コードと同じディレクトリ

```
app/services/
├── device_service.py
└── device_service_test.py            # Service層の単体テスト

app/models/
├── device.py
└── device_test.py                    # Model層の単体テスト

```

**命名規則**:  `<実装ファイル名>_test.py`

#### 結合テスト（Integration Test）

**配置ルール**: エンドポイント単位または Blueprint 単位でファイル分割

**配置場所**: `tests/integration/` ディレクトリ

```
tests/integration/
├──_device_api_test.py               # デバイス管理API結合テスト
├── user_api_test.py                 # ユーザー管理API結合テスト
└── alert_api_test.py                # アラート管理API結合テスト
```

**命名規則**: `<機能名>_api_test.py`

#### E2E テスト

**配置ルール**: ユーザージャーニー（CUJ）単位でファイル分割

**配置場所**: `tests/e2e/` ディレクトリ

```
tests/e2e/
├── test_device_management_flow.py   # デバイス管理フロー
├── test_alert_configuration_flow.py # アラート設定フロー
└── test_dashboard_view_flow.py      # ダッシュボード表示フロー
```

**命名規則**: `test_<フロー名>_flow.py`

---

### テスト項目書とコードのマッピング方法

各テストコードには、対応するテスト項目書の項目番号をコメントで記載することを推奨します。

#### 単体テストの例

```python
# tests/unit/test_device_service.py
# 対応: docs/06-testing/unit-test/device-management-spec.md の「Service層」

def test_create_device():
    """B-U-001: デバイス作成が正常に動作すること"""
    # テスト実装
    service = DeviceService()
    result = service.create_device(device_data)
    assert result.success is True
```

#### E2E テストの例

```python
# tests/e2e/test_device_management_flow.py
# 対応: docs/06-testing/e2e-test/device-management-spec.md の「1. デバイス管理フロー」

def test_device_search_flow(page):
    """F-E-001: 検索ボタンクリックで検索が実行されること"""
    # テスト実装
    page.goto("https://workspace-url/apps/app-name/admin/devices")
    page.fill("#search-input", "device-001")
    page.click("#search-button")
    assert page.locator(".device-row").count() > 0
```

---

### テストファイル配置の原則

1. **単体テスト**: `tests/unit/` または実装コードと同じディレクトリに配置
2. **結合テスト**: `tests/integration/` ディレクトリに配置
3. **E2E テスト**: `tests/e2e/` ディレクトリに集約
4. **命名の一貫性**: プロジェクト全体で `test_` プレフィックスを使用
5. **テストの可読性**: ファイル名から何をテストしているか明確にわかるようにする
