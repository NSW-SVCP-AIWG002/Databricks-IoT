# 結合テスト実装ガイド

## 📑 目次

- [📋 概要](#-概要)
- [📖 このドキュメントの使い方](#-このドキュメントの使い方)
- [🎯 結合テストの目的とスコープ](#-結合テストの目的とスコープ)
- [📊 テストコード実装例](#-テストコード実装例)
- [🔗 関連ドキュメント](#-関連ドキュメント)

---

## 📋 概要

このドキュメントは、Flask + Jinja2 アプリケーションの結合テスト（Integration Test）コードを実装する際のガイドラインです。

`docs/03-features/flask-app/xxxx/`配下の各機能の設計書と[結合テスト観点](./integration-test-perspectives.md)を参照し、テストコードを直接実装します。

---

## 📖 このドキュメントの使い方

このガイドは**テストコード実装のリファレンス**として活用してください。

### 利用フロー

```
各機能の設計書（振る舞い定義）
       ↓ 参照
integration-test-perspectives.md (汎用的な観点チェックリスト)
       ↓ 参照・選択
integration-test-guide.md (テストコード実装例)
       ↓ 実装
tests/integration/test_<機能名>_routes.py (テストコード)
```

### 具体的な使い方

1. **機能設計書確認**: `docs/03-features/flask-app/xxxx/`配下のUI設計書(ui-specification.md)、機能設計書(workflow-specification.md)を読み、機能の振る舞い（APIエンドポイント、DB操作、画面遷移等）を確認
2. **観点確認**: [結合テスト観点](./integration-test-perspectives.md) を開き、関連する観点を確認
3. **項目選択**: チェックリストから該当する機能に必要な項目をピックアップ
4. **コード例確認**: このガイドの「テストコード実装例」を参照し、観点の参照方法・コードの書き方を確認
5. **テスト実装**: テストコード（`test_<機能名>_routes.py`）を作成。観点表のどの項目に対応するかをdocstring/コメントに記載する

### 注意点

- [結合テスト観点](./integration-test-perspectives.md) は**汎用的な観点**を網羅的に記載
- このガイドは**テストコードの実装例**を提供（観点の参照方法、コードパターン）
- **テストコードの実装ルール**は [テスト実装ルール](../../00-rules/test-rule.md) を参照

---

## 🎯 結合テストの目的とスコープ

### 目的

- 複数のモジュール・レイヤー間の連携が正しく動作することを保証
- インターフェースの整合性確認
- データフローの妥当性検証
- システム全体の動作確認（E2Eの一歩手前）

### スコープ

- **対象**: 複数のレイヤーを跨ぐ処理（Handler → UseCase → Repository → DB）
- **外部依存**: 一部をモック化（外部APIなど）
- **カバレッジ目標**: 最低90%、推奨95%以上

### 単体テストとの違い

| 項目         | 単体テスト             | 結合テスト                 |
| ------------ | ---------------------- | -------------------------- |
| テスト範囲   | 単一の関数・モジュール | 複数のレイヤー・モジュール |
| データベース | モック化               | 実DBまたはテスト用DB       |
| 外部API      | モック化               | モック化（一部は実接続）   |
| 目的         | 個別機能の正確性       | 連携の正確性               |

---

## 📊 テストコード実装例

このセクションでは、[結合テスト観点](./integration-test-perspectives.md) の項目を、テストコードでどのように実装するかの例を示します。

### 観点の参照方法

テストコードには、対応する観点表のセクション番号をdocstringまたはコメントに記載します。

### 1. CRUD操作のテスト例

```python
# tests/integration/test_device_routes.py
# 観点: integration-test-perspectives.md > 4. CRUD操作テスト

import pytest
from app import create_app

@pytest.mark.integration
class TestDeviceRoutesCreate:
    """デバイス管理API - 登録テスト
    観点: 4.3 登録（Create）テスト
    """

    def setup_method(self):
        self.app = create_app("testing")
        self.client = self.app.test_client()

    def test_create_device_success(self):
        """4.3.1: 正常登録 - 登録成功、DBにレコード追加、一覧リダイレクト"""
        # Arrange
        data = {"device_id": "DEV-001", "device_name": "Test Device", "device_type": "sensor"}

        # Act
        response = self.client.post("/devices", data=data, follow_redirects=False)

        # Assert
        assert response.status_code == 302  # リダイレクト
        # DB にレコードが追加されていることを確認

    def test_create_device_auto_fields(self):
        """4.3.6 / 4.3.7: 作成日時・作成者が自動設定される"""
        # Arrange
        data = {"device_id": "DEV-002", "device_name": "Test Device 2"}

        # Act
        self.client.post("/devices", data=data)

        # Assert
        # DB から取得して create_date, creator を確認
```

### 2. 認証・認可のテスト例

```python
# tests/integration/test_device_routes.py
# 観点: integration-test-perspectives.md > 1. 認証・認可テスト

@pytest.mark.integration
class TestDeviceRoutesAuth:
    """デバイス管理API - 認証認可テスト
    観点: 1.1 認証テスト, 1.2 認可テスト, 1.3 データスコープフィルタテスト
    """

    def test_unauthenticated_access(self):
        """1.1.2: 未認証ユーザーのアクセスで401エラー、ログイン画面へリダイレクト"""
        # Act
        response = self.client.get("/devices")

        # Assert
        assert response.status_code == 401

    def test_forbidden_role(self):
        """1.2.5: 権限のないロールで操作実行時、403エラー"""
        # Arrange - 権限のないユーザーでログイン

        # Act
        response = self.client.post("/devices", data={...})

        # Assert
        assert response.status_code == 403
```

**※ 上記は実装例です。実際のテストでは、[結合テスト観点](./integration-test-perspectives.md) から該当する機能の観点を選択し、同様のパターンでテストコードを実装してください。**

---

## 🔗 関連ドキュメント

### 必読ドキュメント

- **[結合テスト観点](./integration-test-perspectives.md)** - テスト実装時に参照する汎用的な観点リスト
- **[テスト実装ルール](../../00-rules/test-rule.md)** - テストコードの書き方、ベストプラクティスはこちらを参照

---

**このガイドに従って結合テストを実装し、レイヤー間の連携が正しく動作することを保証してください。**
