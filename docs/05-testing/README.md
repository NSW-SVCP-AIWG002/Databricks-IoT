# テストドキュメント

## 📋 概要

このディレクトリには、Flask + Jinja2 アプリケーションのテスト戦略、テスト実装ガイド、テスト観点表など、テストに関する全てのドキュメントを集約しています。

---

## 📂 ディレクトリ構成

```
docs/05-testing/
├── README.md                                    # 本ドキュメント
├── test-strategy.md                             # テスト戦略・方針
├── test-quality-metrics.md                      # テストカバレッジ戦略・品質メトリクス
│
├── unit-test/                                   # 単体テスト
│   ├── unit-test-perspectives.md               # 単体テスト観点表
│   ├── unit-test-guide.md                      # 単体テスト実装ガイド
│   └── テストコード作成用プロンプト.md          # AI向けプロンプト
│
├── integration-test/                            # 結合テスト
│   ├── integration-test-perspectives.md        # 結合テスト観点表
│   ├── integration-test-guide.md               # 結合テスト実装ガイド
│   └── テストコード作成用プロンプト.md          # AI向けプロンプト
│
└── e2e-test/                                    # E2Eテスト
    ├── e2e-test-perspectives.md                # E2Eテスト観点表
    ├── e2e-test-guide.md                       # E2Eテスト実装ガイド
    └── テストコード作成用プロンプト.md          # AI向けプロンプト
```

---

## 📄 各ファイルの用途

### ルートレベル

| ファイル名                  | 用途                                                                     |
| --------------------------- | ------------------------------------------------------------------------ |
| **test-strategy.md**        | テスト戦略・方針、テストピラミッド、テスト階層ごとの戦略 |
| **test-quality-metrics.md** | テストカバレッジ戦略、カバレッジ目標値、品質メトリクス・KPI    |

### テストレベル別ディレクトリ（共通構成）

各ディレクトリには以下の3ファイルが配置されています：

| ファイル | 用途 |
|---|---|
| **perspectives.md** | 汎用的なテスト観点チェックリスト。テストコード実装時に参照し、該当する観点を選択する |
| **guide.md** | テストコード実装のガイドライン。利用フロー、コード実装例を提供する |
| **テストコード作成用プロンプト.md** | AI（Claude Code等）にテストコード作成を指示する際のプロンプトテンプレート |

---

## 🚀 クイックスタート

### テスト実装前の必読ドキュメント

**テストコードを実装する前に、必ず以下を一読してください：**

- **[テスト実装ルール](../00-rules/test-rule.md)** - 基本原則、チェックリスト、ファイル配置ルール、コマンド一覧

### テスト実装の流れ

```
設計書（docs/03-features/）を確認
       ↓
観点表（perspectives.md）から該当する観点を選択
       ↓
実装ガイド（guide.md）でコードパターンを確認
       ↓
テストコードを直接実装
```

### テスト実行コマンド

```bash
# 単体テストのみ実行
pytest -m unit

# 結合テストのみ実行
pytest -m integration

# カバレッジ付きで実行
pytest --cov=app --cov-report=html
```

詳細は [テスト実装ルール](../00-rules/test-rule.md#️-テスト実行コマンド一覧) を参照してください。

---

## 📚 ドキュメントの使い方

### 1. テスト戦略を理解する

- **[test-strategy.md](./test-strategy.md)** - テストピラミッド、テストレベル別の方針
- **[test-quality-metrics.md](./test-quality-metrics.md)** - カバレッジ目標値、品質メトリクス

### 2. テスト種別ごとのガイドを参照する

- **単体テストを実装する**: [unit-test/unit-test-guide.md](./unit-test/unit-test-guide.md)
- **結合テストを実装する**: [integration-test/integration-test-guide.md](./integration-test/integration-test-guide.md)
- **E2Eテストを実施する**: [e2e-test/e2e-test-guide.md](./e2e-test/e2e-test-guide.md)

---

## 🔗 関連ドキュメント

- [テスト実装ルール](../00-rules/test-rule.md) - テストコーディング時の必読ドキュメント
- [機能設計書](../03-features/) - テスト対象の設計書

---

**テストは品質保証の要です。各ドキュメントを参照しながら、適切なテストを実装してください。**
