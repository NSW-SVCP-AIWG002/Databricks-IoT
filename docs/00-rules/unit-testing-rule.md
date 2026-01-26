---
description: 単体テスト（Unit Test）の実装ルール
globs:
  - app/**/*_test.py
alwaysApply: true
---

# 単体テスト（Unit Test）概要

単体テストは、Service層、Model層、Utility関数の最小単位をテストします。外部依存をモック化し、ビジネスロジックのみを検証することで、高速で信頼性の高いテストを実現します。

## テスト方針

- **最小単位の検証**: 各モジュールを独立してテストし、他のモジュールへの依存を排除
- **外部依存のモック化**: データベース、外部API、ファイルシステムなどはモック化
- **高速実行**: 単体テストは数秒以内に完了し、開発サイクルを加速
- **AAAパターン**: Arrange（準備）、Act（実行）、Assert（検証）の3ステップで構成
- **境界値とエッジケース**: 正常系だけでなく、異常系、境界値、エッジケースも網羅

## テスト対象

### Service層
- ビジネスロジックの検証
- バリデーション
- データ操作処理
- 外部サービス連携（モック化）
- CRUD操作のロジック

### Model層
- データモデルの検証
- プロパティの正当性
- メソッドの動作確認
- データ変換処理

### Utility関数
- ヘルパー関数の検証
- データフォーマット処理
- 計算ロジック
- 文字列操作

## ファイル配置ルール

単体テストは`tests/unit/`ディレクトリ、または実装コードと同じディレクトリに配置します。

```
app/services/
├── device_service.py
└── device_service_test.py            # Service層の単体テスト

app/models/
├── device.py
└── device_test.py                    # Model層の単体テスト

app/utils/
├── date_utils.py
└── date_utils_test.py                # Utility関数の単体テスト

```

**命名規則**: `<実装ファイル名>_test.py`

## 実行方法

### Flask アプリケーション（pytest）

```bash
# 単体テストのみ実行（マーカー使用）
pytest -m unit

# 全てのテストを実行
pytest

# カバレッジ付きで実行
pytest --cov=app --cov-report=html

# ウォッチモードで実行（pytest-watchプラグイン使用）
ptw

# 特定のテストファイルのみ実行
pytest tests/unit/device_service_test.py

# 特定のテストクラスのみ実行
pytest tests/unit/device_service_test.py::TestDeviceService

# 特定のテストメソッドのみ実行
pytest tests/unit/device_service_test.py::TestDeviceService::create_device_test

# 詳細な出力で実行
pytest -v

# カバレッジレポートを確認
open htmlcov/index.html
```

## 単体テストのコード例

### Flask アプリケーション: Service層のテスト

**特徴**: 依存関係をモック化し、ビジネスロジックのみを検証

```python
# device_service_test.py
import pytest
from unittest.mock import Mock, patch
from app.services.device_service import DeviceService
from app.models.device import Device

@pytest.mark.unit
class TestDeviceService:
    """DeviceServiceの単体テスト"""

    def setup_method(self):
        """各テストメソッドの前に実行されるセットアップ"""
        self.mock_db = Mock()
        self.device_service = DeviceService(db=self.mock_db)

    def create_device_test(self):
        """デバイス作成が正常に動作する"""
        # Arrange
        device_data = {
            "device_id": "device-001",
            "device_name": "Test Device",
            "device_type": "sensor"
        }
        expected_device = Device(
            id=1,
            device_id="device-001",
            device_name="Test Device",
            device_type="sensor"
        )
        self.mock_db.save.return_value = expected_device

        # Act
        result = self.device_service.create_device(device_data)

        # Assert
        assert result.id == 1
        assert result.device_id == "device-001"
        assert result.device_name == "Test Device"
        self.mock_db.save.assert_called_once()

    def create_device_with_invalid_data_test(self):
        """無効なデータでデバイス作成が失敗する"""
        # Arrange
        invalid_data = {"device_id": ""}  # 空のdevice_id

        # Act & Assert
        with pytest.raises(ValueError, match="device_id is required"):
            self.device_service.create_device(invalid_data)
```

## 単体テストのベストプラクティス

### 1. テストの独立性

- 各テストは他のテストに依存せず、独立して実行できるように設計する
- テストの実行順序に依存しない
- `setup_method()`/`teardown_method()`（pytest）を使ってセットアップ・クリーンアップを行う
- グローバル変数の共有を避ける

### 2. AAAパターン（Arrange-Act-Assert）

- **Arrange（準備）**: テストに必要なデータやモックをセットアップ
- **Act（実行）**: テスト対象の関数やメソッドを実行
- **Assert（検証）**: 期待される結果を検証

### 3. テストの可読性

- テスト名は「何をテストしているか」を明確に示す（`create_device_test`）
- docstringを使用して日本語のテスト説明を記述（`"""デバイス作成が正常に動作する"""`）
- エラーメッセージは具体的で理解しやすいものにする

### 4. モック・スタブの適切な使用

- 外部依存（データベース、外部API等）は適切にモック化する
- `unittest.mock.Mock`, `unittest.mock.patch`を使用（Python標準ライブラリ）
- pytest の `monkeypatch` フィクスチャも活用可能
- 過度なモック化は避け、必要最小限に留める

### 5. エラーハンドリングのテスト

- 正常系だけでなく、異常系のテストも必ず実装する
- 境界値やエッジケースのテストを含める
- `assertThatThrownBy`（AssertJ）または`expect().toThrow()`（Jest）を使用

### 6. テストデータの管理

- テストデータはファクトリ関数やビルダーパターンを使って生成する
- ハードコードされた値ではなく、意味のある変数名を使用
- テストデータの再利用性を高める

### 7. 非同期処理の扱い（フロントエンド）

- `async/await`を適切に使用する
- `waitFor`を使用して非同期処理の完了を待つ（React Testing Library）
- タイムアウトやレースコンディションに注意する

### 8. カバレッジ目標

- **最低目標**: 70%以上
- **推奨目標**: 80%以上
- Line Coverage、Branch Coverage、Function Coverageを測定
- カバレッジは品質の指標の一つであり、100%を目指すことよりも、意味のあるテストを書くことを優先

## 単体テスト作成のチェックリスト

新しい単体テストを作成する際は、以下のチェックリストを確認してください。

- [ ] 正常系のテストがある
- [ ] 異常系のテストがある
- [ ] 境界値のテストがある
- [ ] エッジケースのテストがある
- [ ] テストが独立している
- [ ] AAAパターンに従っている
- [ ] テスト名が明確である（`@DisplayName`を使用）
- [ ] モックが適切に使用されている
- [ ] テストデータが適切に管理されている
- [ ] 実行速度が十分に速い（数秒以内）
- [ ] テストコードの可読性が高い
- [ ] エラーメッセージが具体的である

## 新しい単体テストを追加する際の注意点

- テストファイルは実装コードと同じディレクトリに配置する
- 命名規則（`<実装ファイル名>.test.ts`）を遵守する
- テスト対象のモジュールのみをテストし、依存関係はモック化する
- テストが失敗した場合、原因を特定しやすいように適切なアサーションとエラーメッセージを記述する
- CI/CD パイプラインで自動実行されることを意識し、環境依存の処理は避ける
- 新しいテストを追加した際は、このドキュメントと関連する開発ルールを必要に応じて更新してください

---

**単体テストは品質保証の基盤です。適切なテストを実装し、継続的に品質を維持してください。**
