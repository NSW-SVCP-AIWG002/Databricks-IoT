# 単体テスト実装ガイド

## 📑 目次

- [📋 概要](#-概要)
- [📖 このドキュメントの使い方](#-このドキュメントの使い方)
- [🎯 単体テストの目的](#-単体テストの目的)
- [📊 テストコード実装例](#-テストコード実装例)
- [🔗 関連ドキュメント](#-関連ドキュメント)

---

## 📋 概要

このドキュメントは、Flask + Jinja2 アプリケーションの単体テスト（Unit Test）コードを実装する際のガイドラインです。

`docs/03-features/flask-app/xxxx/`配下の各機能の設計書と[単体テスト観点](./unit-test-perspectives.md)を参照し、テストコードを直接実装します。

---

## 📖 このドキュメントの使い方

このガイドは**テストコード実装のリファレンス**として活用してください。

### 利用フロー

```
各機能の設計書（振る舞い定義）
       ↓ 参照
unit-test-perspectives.md (汎用的な観点チェックリスト)
       ↓ 参照・選択
unit-test-guide.md (テストコード実装例)
       ↓ 実装
tests/unit/test_<機能名>.py (テストコード)
```

### 具体的な使い方

1. **機能設計書確認**: `docs/03-features/flask-app/xxxx/`配下のUI設計書(ui-specification.md)、機能設計書(workflow-specification.md)を読み、機能の振る舞いを確認
2. **観点確認**: [単体テスト観点](./unit-test-perspectives.md) を開き、関連する観点を確認
3. **項目選択**: チェックリストから該当する機能に必要な項目をピックアップ
4. **コード例確認**: このガイドの「テストコード実装例」を参照し、観点の参照方法・コードの書き方を確認
5. **テスト実装**: テストコード（`test_<機能名>.py`）を作成。観点表のどの項目に対応するかをdocstring/コメントに記載する

### 注意点

- [単体テスト観点](./unit-test-perspectives.md) は**汎用的な観点**を網羅的に記載
- このガイドは**テストコードの実装例**を提供（観点の参照方法、コードパターン）
- **テストコードの実装ルール**は [テスト実装ルール](../../00-rules/test-rule.md) を参照

---

## 🎯 単体テストの目的

- 個別の関数・モジュール・コンポーネントが仕様通りに動作することを保証
- バグの早期発見と修正
- リファクタリング時の安全性確保
- コードの品質向上

---

## 📊 テストコード実装例

このセクションでは、[単体テスト観点](./unit-test-perspectives.md) の項目を、テストコードでどのように実装するかの例を示します。

### 観点の参照方法

テストコードには、対応する観点表のセクション番号をdocstringまたはコメントに記載します。

### 1. 入力バリデーションのテスト例

```python
# tests/unit/test_device_service.py
# 観点: unit-test-perspectives.md > 1.1 入力チェック

import pytest
from unittest.mock import Mock
from app.services.device_service import DeviceService

@pytest.mark.unit
class TestDeviceServiceValidation:
    """デバイスサービス - 入力バリデーション
    観点: 1.1.1 必須チェック, 1.1.2 最大文字列長チェック
    """

    def setup_method(self):
        self.mock_repo = Mock()
        self.service = DeviceService(repo=self.mock_repo)

    def test_required_field_empty(self):
        """1.1.1: 必須項目が空文字の場合、ValidationErrorがスローされる"""
        # Arrange
        data = {"device_id": "", "device_name": "Test Device"}

        # Act & Assert
        with pytest.raises(ValidationError):
            self.service.create_device(data)

    def test_required_field_none(self):
        """1.1.2: 必須項目がNoneの場合、ValidationErrorがスローされる"""
        # Arrange
        data = {"device_id": None, "device_name": "Test Device"}

        # Act & Assert
        with pytest.raises(ValidationError):
            self.service.create_device(data)

    def test_max_length_exceeded(self):
        """1.2.3: 最大文字数を超過した場合、ValidationErrorがスローされる"""
        # Arrange
        data = {"device_id": "a" * 256, "device_name": "Test Device"}

        # Act & Assert
        with pytest.raises(ValidationError):
            self.service.create_device(data)
```

### 2. CRUD操作のテスト例

```python
# tests/unit/test_device_service.py
# 観点: unit-test-perspectives.md > 2. データ操作テスト, 3.2 登録機能

@pytest.mark.unit
class TestDeviceServiceCrud:
    """デバイスサービス - CRUD操作
    観点: 2.1 正常系処理, 2.2 対象データ存在チェック, 3.2 登録機能
    """

    def setup_method(self):
        self.mock_repo = Mock()
        self.service = DeviceService(repo=self.mock_repo)

    def test_create_device_success(self):
        """2.1.1 / 3.2.1.1: 有効な入力で登録内容がRepositoryに渡される"""
        # Arrange
        data = {"device_id": "DEV-001", "device_name": "Test Device"}
        self.mock_repo.save.return_value = Mock(id=1)

        # Act
        result = self.service.create_device(data)

        # Assert
        assert result.id == 1
        self.mock_repo.save.assert_called_once()

    def test_get_device_not_found(self):
        """2.2.2: 存在しないIDでNotFoundErrorがスローされる"""
        # Arrange
        self.mock_repo.find_by_id.return_value = None

        # Act & Assert
        with pytest.raises(NotFoundError):
            self.service.get_device(999)
```

**※ 上記は実装例です。実際のテストでは、[単体テスト観点](./unit-test-perspectives.md) から該当する機能の観点を選択し、同様のパターンでテストコードを実装してください。**

---

## 🔗 関連ドキュメント

### 必読ドキュメント

- **[単体テスト観点](./unit-test-perspectives.md)** - テスト実装時に参照する汎用的な観点リスト
- **[テスト実装ルール](../../00-rules/test-rule.md)** - テストコードの書き方、ベストプラクティスはこちらを参照

---

**このガイドに従って単体テストを実装し、品質の高いテストコードを作成してください。**
