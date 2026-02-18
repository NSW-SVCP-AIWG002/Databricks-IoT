# テスト実装ルール

## 📑 目次

- [📋 概要](#-概要)
- [📋 テスト実装の基本原則](#-テスト実装の基本原則)
- [🧪 単体テスト（Unit Test）ルール](#-単体テストunit-testルール)
- [🔗 結合テスト（Integration Test）ルール](#-結合テストintegration-testルール)
- [🌐 E2E テスト（End-to-End Test）ルール](#-e2e-テストend-to-end-testルール)
- [🛠️ テスト実行コマンド一覧](#️-テスト実行コマンド一覧)
- [📂 テストコードの実装方針とファイル配置ルール](#-テストコードの実装方針とファイル配置ルール)

---

## 📋 概要

このドキュメントでは、Flask + Jinja2 アプリケーションにおけるテスト実装のルール、実行コマンド、ファイル配置ルールを提供します。

プロジェクトでは以下の 3 つのテストレベルを実施します：

| テストレベル | ツール                      | 対象                            | 実行方式       |
| ------------ | --------------------------- | ------------------------------- | -------------- |
| 単体テスト   | pytest + unittest.mock      | Service層、Model層、Utility関数 | 自動（pytest） |
| 結合テスト   | pytest + Flask test_client  | APIエンドポイント、DB連携       | 自動（pytest） |
| E2Eテスト    | 手動 / Playwright（必要時） | ユーザー業務フロー（CUJ）       | 手動基本       |

これらのテストは`03-features`配下の設計書をベースにテストケースを作成して実施します。

---

## 📋 テスト実装の基本原則

### 1. テストの独立性

- 各テストは他のテストに依存せず、独立して実行できるように設計する
- テストの実行順序に依存しない
- `setup_method()` / `teardown_method()`、または pytest フィクスチャでセットアップ・クリーンアップを行う
- グローバル変数の共有を避ける

### 2. AAA パターン（Arrange-Act-Assert）

- **Arrange（準備）**: テストに必要なデータやモックをセットアップ
- **Act（実行）**: テスト対象の関数やメソッドを実行
- **Assert（検証）**: 期待される結果を検証

### 3. テストの可読性

- テスト名は「何をテストしているか」を明確に示す
- docstring を使用して日本語のテスト説明を記述
- エラーメッセージは具体的で理解しやすいものにする

### 4. モック・スタブの適切な使用

- 外部依存（データベース、外部 API 等）は適切にモック化する
- `unittest.mock.Mock`、`unittest.mock.patch` を使用
- pytest の `monkeypatch` フィクスチャも活用可能
- 過度なモック化は避け、単体テストと結合テストのバランスを考慮する

### 5. エラーハンドリングのテスト

- 正常系だけでなく、異常系のテストも必ず実装する
- 境界値やエッジケースのテストを含める
- `pytest.raises()` を使用して例外を検証する

### 6. テストデータの管理

- テストデータはファクトリ関数やフィクスチャを使って生成する
- ハードコードされた値ではなく、意味のある変数名を使用する
- テストデータの再利用性を高める

### 7. テストのクリーンアップ

- 各テストの前後で適切にセットアップ・クリーンアップを行う
- リソース（データベース接続、ファイルハンドル等）は適切に解放する

---

## 🧪 単体テスト（Unit Test）ルール

### 概要

Service層、Model層、Utility関数の最小単位をテスト。外部依存をモック化し、ビジネスロジックのみを検証します。

### テスト対象

- **Service層**: ビジネスロジック、バリデーション、CRUD操作のロジック
- **Model層**: データモデルの検証、プロパティの正当性、データ変換処理
- **Utility関数**: ヘルパー関数、データフォーマット処理、計算ロジック

### カバレッジ目標

- **最低目標**: 70%以上
- **推奨目標**: 80%以上
- Line Coverage、Branch Coverage、Function Coverage を測定
- カバレッジは品質の指標の一つであり、100%を目指すことよりも意味のあるテストを書くことを優先

### チェックリスト

- [ ] 正常系のテストがある
- [ ] 異常系のテストがある
- [ ] 境界値のテストがある
- [ ] エッジケースのテストがある
- [ ] テストが独立している
- [ ] AAA パターンに従っている
- [ ] テスト名が明確である（docstring で日本語説明）
- [ ] モックが適切に使用されている
- [ ] テストデータが適切に管理されている
- [ ] 実行速度が十分に速い（数秒以内）

---

## 🔗 結合テスト（Integration Test）ルール

### 概要

複数のモジュールやレイヤーが連携して動作することを検証。Flask test_client を使用して実際の HTTP リクエストを送信し、データベースを含む全レイヤーの動作を確認します。

### テスト対象

- API エンドポイントの HTTP リクエスト/レスポンス
- 認証・認可フロー
- データベースとの連携（CRUD操作）
- トランザクション処理
- エラーハンドリング

### テスト環境の分離

- テスト専用のデータベースを使用する
- テスト用の設定ファイル・環境変数でテスト環境を識別する
- 本番データに影響を与えないようにする

### データのクリーンアップ

- テストの前後でデータを初期化・クリーンアップする
- トランザクションを使用してロールバックする
- テスト終了後にテストデータを確実に削除する

### カバレッジ目標

- **統合ポイントカバレッジ**: 最低90%、推奨95%
- 全公開 API エンドポイント 100%カバー
- 認証・認可フローは 100%カバー

### チェックリスト

- [ ] API エンドポイントのテストがある
- [ ] 認証・認可のテストがある
- [ ] データフローのテストがある（リクエスト → 処理 → レスポンス → DB保存）
- [ ] エラーハンドリングのテストがある
- [ ] トランザクションのテストがある（該当する場合）
- [ ] データベースとの連携が正しく動作する
- [ ] テスト環境が適切に設定されている
- [ ] データのクリーンアップが実装されている
- [ ] HTTP ステータスコードが正しく返される
- [ ] レスポンスボディの内容が期待通りである
- [ ] テストが独立している（他のテストに依存しない）

---

## 🌐 E2E テスト（End-to-End Test）ルール

### 概要

原則手動で実施し、場合に応じて Playwright で自動化します。クリティカルユーザージャーニー（CUJ）を中心に、重要な業務フローの完走性を保証します。

### テスト方針

- **手動テストが基本**: ブラウザで実際の操作フローを手動で確認する
- **自動化は必要時**: 回帰テストの効率化等で必要な場合に Playwright を導入する
- **CUJ に集中**: 「顧客が達成したい成果」に焦点を当てる
- **細かな検証は他レベルで担保**: バリデーション詳細や境界値検証は単体テスト・結合テストで担保する

### テスト対象

- 一連の各種業務フロー（ログイン、検索、登録、更新、削除等）
- クロスブラウザ/レスポンシブ対応の確認

### CUJ の考え方

- ユーザーが業務上必須の操作を完遂できることを担保する
- 新たな E2E テストを追加する場合は、既存 CUJ と重複しないか確認してから実施する

### チェックリスト

- [ ] クリティカルパスのテストがある
- [ ] エラー発生時の業務継続性テストがある
- [ ] 既存 CUJ と重複していないか確認した
- [ ] 細かな検証は単体テスト・結合テストへ委ねている

---

## 🛠️ テスト実行コマンド一覧

```bash
# 全てのテストを実行
pytest

# カバレッジ付きで実行
pytest --cov=app --cov-report=html

# ウォッチモードで実行（pytest-watchプラグイン使用）
ptw

# 特定のテストファイルのみ実行
pytest tests/unit/test_device_service.py

# 特定のテストクラスのみ実行
pytest tests/unit/test_device_service.py::TestDeviceService

# 特定のテストメソッドのみ実行
pytest tests/unit/test_device_service.py::TestDeviceService::test_create_device

# 単体テストのみ実行（マーカー使用）
pytest -m unit

# 結合テストのみ実行（マーカー使用）
pytest -m integration

# E2Eテストを実行（Playwright使用時）
pytest tests/e2e/

# 詳細な出力で実行
pytest -v

# カバレッジレポートを確認
open htmlcov/index.html
```

---

## 📂 テストコードの実装方針とファイル配置ルール

### テスト観点とテストコードの関係

#### テスト観点表（`docs/05-testing/`配下の perspectives.md）の役割

- **テストレベルごとに汎用的な観点を定義**するチェックリスト
- **目的**: テストカバレッジの把握、観点の漏れ防止
- **例**: `docs/05-testing/unit-test/unit-test-perspectives.md` にはバリデーション、CRUD操作、エラーハンドリング等の観点を記載

#### テストコード実装の方針

テスト観点表から該当する機能の観点を選択し、**テストコードを直接実装**してください。テストコード内に対応する観点番号をdocstring/コメントで記載し、トレーサビリティを確保します。

---

### ファイル配置

#### 単体テスト（Unit Test）

**配置ルール**: 責務単位でファイル分割

**配置場所**: `tests/unit/` ディレクトリ

```
tests/unit/
└── device/
    ├── test_device_service.py            # Service層の単体テスト
    └── test_device_model.py              # Model層の単体テスト
```

**命名規則**: `test_<実装ファイル名>.py`

#### 結合テスト（Integration Test）

**配置ルール**: Blueprint 単位でファイル分割

**配置場所**: `tests/integration/` ディレクトリ

```
tests/integration/
├── test_device_routes.py               # デバイス管理API結合テスト
├── test_user_routes.py                 # ユーザー管理API結合テスト
└── test_alert_routes.py                # アラート管理API結合テスト
```

**命名規則**: `test_<機能名>_routes.py`

#### E2E テスト

- ※ 手動テストの場合は参照不要

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

### テスト観点とコードのマッピング方法

各テストコードには、対応するテスト観点表のセクション番号をdocstring/コメントに記載してください。

#### 単体テストの例

```python
# tests/unit/test_device_service.py
# 観点: unit-test-perspectives.md > 1.1 入力チェック, 2.1 正常系処理

@pytest.mark.unit
class TestDeviceServiceValidation:
    """デバイスサービス - 入力バリデーション
    観点: 1.1.1 必須チェック, 1.1.2 最大文字列長チェック
    """

    def test_required_field_empty(self):
        """1.1.1: 必須項目が空文字の場合、ValidationErrorがスローされる"""
        # Arrange
        data = {"device_id": "", "device_name": "Test Device"}

        # Act & Assert
        with pytest.raises(ValidationError):
            self.service.create_device(data)
```

#### 結合テストの例

```python
# tests/integration/test_device_routes.py
# 観点: integration-test-perspectives.md > 4.3 登録（Create）テスト

@pytest.mark.integration
class TestDeviceRoutesCreate:
    """デバイス管理API - 登録テスト
    観点: 4.3 登録（Create）テスト
    """

    def test_create_device_success(self):
        """4.3.1: 正常登録 - 登録成功、DBにレコード追加、一覧リダイレクト"""
        # Arrange
        data = {"device_id": "DEV-001", "device_name": "Test Device"}

        # Act
        response = self.client.post("/devices", data=data, follow_redirects=False)

        # Assert
        assert response.status_code == 302
```

---

### テストファイル配置の原則

1. **単体テスト**: `tests/unit/` ディレクトリに配置
2. **結合テスト**: `tests/integration/` ディレクトリに配置
3. **E2E テスト**: `tests/e2e/` ディレクトリに集約
4. **命名の一貫性**: プロジェクト全体で `test_` プレフィックスを使用
5. **テストの可読性**: ファイル名から何をテストしているか明確にわかるようにする
