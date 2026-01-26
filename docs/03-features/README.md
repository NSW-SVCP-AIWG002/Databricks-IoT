# 機能別実装ガイド

## 📑 目次

- [📁 このディレクトリについて](#-このディレクトリについて)
- [🗂️ ディレクトリ構成](#️-ディレクトリ構成)
- [📄 機能一覧](#-機能一覧)
  - [Flaskアプリケーション機能](#flaskアプリケーション機能)
  - [LDPパイプライン機能](#ldpパイプライン機能)
- [🔗 関連ドキュメント](#-関連ドキュメント)

---

## 📁 このディレクトリについて

このディレクトリには、Databricks IoTシステムの各機能の実装ガイドが格納されます。

本システムは大きく2つの実装領域に分かれています：
1. **Flaskアプリケーション**: Webアプリケーション（マスタ管理、履歴表示、ダッシュボード）
2. **LDPパイプライン**: データ処理パイプライン（シルバー層、ゴールド層）

各機能は、以下のドキュメント構成で管理されます：
- **README.md**: 機能概要・データモデル・API/テーブル一覧・実装ステータス
- **ui-specification.md**: UI仕様（画面レイアウト・UI要素・バリデーションルール定義）※Flask appのみ
- **workflow-specification.md**: ワークフロー仕様（処理フロー・API統合・エラーハンドリング・状態管理）

**注:**
- Flask SSRルート設計はflask-app配下の各機能の `workflow-specification.md` で管理されています
- LDPパイプライン設計はldp-pipeline配下の各機能の `workflow-specification.md` で管理されています
- データベース設計は `03-features/common/databases.md` で管理されています（TODO）
- **共通仕様**（HTTPステータスコード、エラーコード、トランザクション管理、セキュリティ等）は [common/common-specification.md](./common/common-specification.md) で管理されます

---

## 🗂️ ディレクトリ構成

```
03-features/
├── README.md                          # このファイル（機能一覧と概要）
├── feature-guide.md                   # 機能実装ガイド作成ルール
│
├── common/                            # 共通仕様
│   ├── common-specification.md        # HTTPステータスコード、エラーコード、トランザクション管理、セキュリティ等
│   └── ui-common-specification.md     # UI共通仕様
│
├── templates/                         # テンプレート
│   ├── ui-specification-template.md   # UI仕様書テンプレート
│   └── workflow-specification-template.md # ワークフロー仕様書テンプレート
│
├── flask-app/                         # Flaskアプリケーション機能
│   ├── devices/             # デバイス管理
│   │   ├── README.md
│   │   ├── ui-specification.md
│   │   └── workflow-specification.md
│   ├── users/               # ユーザー管理
│   │   ├── README.md
│   │   ├── ui-specification.md
│   │   └── workflow-specification.md
│   ├── organizations/       # 組織管理
│   │   ├── README.md
│   │   ├── ui-specification.md
│   │   └── workflow-specification.md
│   ├── alert-settings/                # アラート設定管理
│   │   ├── README.md
│   │   ├── ui-specification.md
│   │   └── workflow-specification.md
│   ├── device-inventory/                 # デバイス台帳管理
│   │   ├── README.md
│   │   ├── ui-specification.md
│   │   └── workflow-specification.md
│   ├── mail-settings/   # メール通知設定管理
│   │   ├── README.md
│   │   ├── ui-specification.md
│   │   └── workflow-specification.md
│   ├── account/              # アカウント管理
│   │   ├── README.md
│   │   ├── ui-specification.md
│   │   └── workflow-specification.md
│   ├── csv-import-export/             # CSVインポート/エクスポート
│   │   ├── README.md
│   │   ├── ui-specification.md
│   │   └── workflow-specification.md
│   ├── alert-history/                 # アラート履歴
│   │   ├── README.md
│   │   ├── ui-specification.md
│   │   └── workflow-specification.md
│   ├── mail-history/    # メール通知履歴
│   │   ├── README.md
│   │   ├── ui-specification.md
│   │   └── workflow-specification.md
│   └── dashboard/                     # ダッシュボード
│       ├── README.md
│       ├── ui-specification.md
│       └── workflow-specification.md
│
└── ldp-pipeline/                      # LDPパイプライン機能
    ├── silver-layer/                  # シルバー層処理
    │   ├── README.md
    │   └── workflow-specification.md  # UIなし
    └── gold-layer/                    # ゴールド層処理
        ├── README.md
        └── workflow-specification.md  # UIなし
```

---

## 📄 機能一覧

### Flaskアプリケーション機能

#### FR-004: マスタ管理機能

| 機能ID | 機能名 | ディレクトリ | 説明 |
|--------|--------|------------|------|
| FR-004-1 | デバイス管理 | `flask-app/devices/` | デバイスの一覧・検索・参照・登録・更新・削除・CSVエクスポート |
| FR-004-2 | ユーザー管理 | `flask-app/users/` | ユーザーの一覧・検索・参照・登録・更新・削除・CSVエクスポート |
| FR-004-3 | 組織管理 | `flask-app/organizations/` | 組織の一覧・検索・参照・登録・更新・削除・CSVエクスポート |
| FR-004-4 | アラート設定管理 | `flask-app/alert-settings/` | アラート設定の一覧・検索・参照・登録・更新・削除・CSVエクスポート |
| FR-004-5 | デバイス台帳管理 | `flask-app/device-inventory/` | デバイス台帳の一覧・検索・参照・登録・更新・削除・CSVエクスポート |
| FR-004-6 | メール通知設定管理 | `flask-app/mail-settings/` | メール通知設定の一覧・検索・参照・登録・更新・削除・CSVエクスポート |
| FR-004-7 | アカウント管理 | `flask-app/account/` | 言語設定の変更 |
| FR-004-8 | CSVインポート | `flask-app/csv-import/` | CSVインポート |

#### FR-005: 履歴機能

| 機能ID | 機能名 | ディレクトリ | 説明 |
|--------|--------|------------|------|
| FR-005-1 | アラート履歴 | `flask-app/alert-history/` | アラート履歴の一覧・検索・参照 |
| FR-005-2 | メール通知履歴 | `flask-app/mail-history/` | メール通知履歴の一覧・検索・参照 |

#### FR-006: 分析機能

| 機能ID | 機能名 | ディレクトリ | 説明 |
|--------|--------|------------|------|
| FR-006-1 | ダッシュボード | `flask-app/dashboard/` | リアルタイムIoTデータ表示、最新アラート表示、Databricks Dashboard埋め込み |
| FR-006-2 | 対話型AI機能 | `flask-app/dashboard/` | Databricks Dashboard内の対話型AI（Databricks標準機能） |

---

### LDPパイプライン機能

#### FR-002: データ取込み機能

| 処理層 | 機能名 | ディレクトリ | 説明 |
|--------|--------|------------|------|
| シルバー層 | データ構造化・異常検出 | `ldp-pipeline/silver-layer/` | Event Hubからのデータ取込み、構造化、異常データ検出（アラート）、OLTP DB更新 |
| ゴールド層 | 集計・分析データ生成 | `ldp-pipeline/gold-layer/` | シルバー層データの集計、ダッシュボード表示用データ生成 |

**注:**
- **ブロンズ層**: Event Hubs Captureが自動処理（LDP実装対象外）
- **シルバー層**: LDPで実装（データ構造化、アラート検出、OLTP DB更新）
- **ゴールド層**: LDPで実装（集計データ生成）

---

## 🔗 関連ドキュメント

### 機能設計・仕様

- [共通仕様書](./common/common-specification.md) - HTTPステータスコード、エラーコード、トランザクション管理、セキュリティ等
- [UI共通仕様書](./common/ui-common-specification.md) - すべての画面に共通するUI仕様
- [機能別実装ガイド作成ルール](./feature-guide.md) - 実装ガイドの作成方法
- [UI仕様書テンプレート](./templates/ui-specification-template.md) - ui-specification.md のテンプレート
- [ワークフロー仕様書テンプレート](./templates/workflow-specification-template.md) - workflow-specification.md のテンプレート
- [機能要件定義書](../02-requirements/functional-requirements.md) - 全機能の要件定義
- [技術要件定義書](../02-requirements/technical-requirements.md) - 技術仕様・セキュリティ要件
- [非機能要件定義書](../02-requirements/non-functional-requirements.md) - パフォーマンス・可用性要件

### アーキテクチャ設計

- [アーキテクチャ概要](../01-architecture/overview.md)
- [バックエンド設計](../01-architecture/backend.md) - Flask/LDP設計
- [フロントエンド設計](../01-architecture/frontend.md) - Flask + Jinja2設計
- [データベース設計](../01-architecture/database.md) - OLTP DB/Unity Catalog設計
- [インフラストラクチャ設計](../01-architecture/infrastructure.md)

### データベース

- [データベース設計書](../01-architecture/database.md) - テーブル定義、インデックス設計、データスコープ制限

### テスト仕様

- [テスト仕様書](../06-testing/) - 単体テスト・結合テスト・E2Eテスト

---

**このディレクトリ内の実装ガイドは、実装前に必ずレビューを受けてください。**
