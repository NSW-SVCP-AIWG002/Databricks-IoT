# API仕様書ディレクトリ

## 📑 目次

1. [このディレクトリについて](#1-このディレクトリについて)
2. [ディレクトリ構成](#2-ディレクトリ構成)
3. [ディレクトリとファイルの構成](#3-ディレクトリとファイルの構成)
   - 3.1 [管理用ファイル](#31-管理用ファイル)
   - 3.2 [API別ディレクトリ](#32-api別ディレクトリ)
4. [AIを使用したAPI仕様書・処理設計書の作成](#4-aiを使用したapi仕様書処理設計書の作成)
   - 4.1 [基本的な使い方](#41-基本的な使い方)
   - 4.2 [プロンプトの構成要素](#42-プロンプトの構成要素)
   - 4.3 [プロンプト例](#43-プロンプト例)
   - 4.4 [AIが自動的に行うこと](#44-aiが自動的に行うこと)
   - 4.5 [注意事項](#45-注意事項)
5. [関連ドキュメント](#5-関連ドキュメント)
   - 5.1 [API設計・仕様](#51-api設計仕様)
   - 5.2 [その他](#52-その他)

---

## 1. このディレクトリについて

このディレクトリには、各APIエンドポイント毎のAPI仕様書および処理設計書が格納されます。

各APIエンドポイントは、**機能カテゴリ > 操作単位でディレクトリ化**され、以下のドキュメントで構成されます：
- **specification.md**: API仕様（入力・出力・エラー仕様）
- **processing.md**: 処理設計（処理フロー・ロジック詳細）

---

## 2. ディレクトリ構成

```
05-api/
├── README.md                          # このファイル（ディレクトリ構成と概要）
├── common-specification.md            # API共通仕様書
├── api-guide.md                       # API仕様書・処理設計書作成ガイド
├── specification-template.md          # API仕様書テンプレート
├── processing-template.md             # 処理設計書テンプレート
├── implementation-best-practices.md   # API実装ベストプラクティス
│
├── users/                             # ユーザ管理API
│   ├── list/
│   │   ├── specification.md           # ユーザ一覧取得API仕様
│   │   └── processing.md              # ユーザ一覧取得API処理設計
│   ├── get/
│   │   ├── specification.md           # ユーザ詳細取得API仕様
│   │   └── processing.md              # ユーザ詳細取得API処理設計
│   ├── create/
│   │   ├── specification.md           # ユーザ作成API仕様
│   │   └── processing.md              # ユーザ作成API処理設計
│   └── ...
│
├── groups/                            # グループ管理API
│   ├── delete/
│   │   ├── specification.md
│   │   └── processing.md
│   └── ...
│
└── documents/                         # ドキュメント管理API
    ├── upload/
    │   ├── specification.md
    │   └── processing.md
    └── ...
```

**注:** 詳細な命名規則やディレクトリ作成手順は [APIガイド](./api-guide.md) を参照してください。

---

## 3. ディレクトリとファイルの構成

### 3.1 管理用ファイル

| ファイル名 | 用途 |
|-----------|------|
| **README.md** | このファイル。ディレクトリの概要と各ファイルの説明 |
| **common-specification.md** | API共通仕様（ベースURL、認証、レスポンス形式、エラーコード、キャッシュ戦略等） |
| **api-guide.md** | API仕様書・処理設計書作成ガイド（命名規則、作成手順、注意事項） |
| **specification-template.md** | API仕様書のテンプレート（specification.md作成時に使用） |
| **processing-template.md** | 処理設計書のテンプレート（processing.md作成時に使用） |
| **implementation-best-practices.md** | API実装ベストプラクティス（実装例、コードサンプル、パフォーマンス最適化） |

### 3.2 API別ディレクトリ

各APIは **機能カテゴリ/操作名** の階層構造で管理されます。

**ディレクトリ構成:**
```
{機能カテゴリ}/{操作名}/
├── specification.md    # API仕様書（入力・出力・エラー仕様）
└── processing.md       # 処理設計書（処理フロー・ロジック詳細）
```

**例:**
- `users/list/` - ユーザ一覧取得API
- `users/create/` - ユーザ作成API
- `groups/list/` - グループ一覧取得API
- `documents/upload/` - ドキュメントアップロードAPI

**命名規則:**
- **機能カテゴリ**: 複数形の英小文字（例: `users`, `groups`, `contracts`）
- **操作名**: 動詞の英小文字（例: `list`, `get`, `create`, `update`, `delete`）

詳細な作成手順は [APIガイド](./api-guide.md) を参照してください。

---

## 4. AIを使用したAPI仕様書・処理設計書の作成

Claude や他のAIアシスタントを使用することで、ディレクトリ構成やファイル名を意識せずに、API仕様書と処理設計書を自動作成できます。

### 4.1 基本的な使い方

以下のプロンプトをAIに投げるだけで、必要なディレクトリとファイルが自動的に作成されます：

```
@docs/05-api/README.md @docs/05-api/api-guide.md @docs/05-api/common-specification.md @docs/05-api/specification-template.md @docs/05-api/processing-template.md @docs/02-requirements/functional-requirements.md @docs/01-architecture/database.md を参照して、以下のAPIの仕様書と処理設計書を作成してください。

機能: ユーザー一覧取得
エンドポイント: GET /users
概要: ユーザー一覧を取得する
処理概要: データベースからユーザー情報を取得し、クライアントに返却する
```

### 4.2 プロンプトの構成要素

プロンプトには以下の情報を含めてください：

| 要素 | 説明 | 例 |
|------|------|-----|
| **機能** | APIの機能名 | `ユーザー一覧取得`、`契約情報作成` |
| **エンドポイント** | HTTPメソッドとパス | `GET /users`, `POST /contracts` |
| **概要** | APIの簡潔な説明 | `ユーザー一覧を取得する` |
| **処理概要** | 処理の流れ | `データベースからユーザー情報を取得し、クライアントに返却する` |

### 4.3 プロンプト例

#### 例1: ユーザー詳細取得API

```
@docs/05-api/README.md @docs/05-api/api-guide.md @docs/05-api/common-specification.md @docs/05-api/specification-template.md @docs/05-api/processing-template.md @docs/02-requirements/functional-requirements.md @docs/01-architecture/database.md を参照して、以下のAPIの仕様書と処理設計書を作成してください。

機能: ユーザー詳細取得
エンドポイント: GET /users/{userId}
概要: 指定されたユーザーIDのユーザー詳細情報を取得する
処理概要: パスパラメータからuserIdを取得し、データベースから該当ユーザー情報を取得して返却する
```

#### 例2: 契約情報作成API

```
@docs/05-api/README.md @docs/05-api/api-guide.md @docs/05-api/common-specification.md @docs/05-api/specification-template.md @docs/05-api/processing-template.md @docs/02-requirements/functional-requirements.md @docs/01-architecture/database.md を参照して、以下のAPIの仕様書と処理設計書を作成してください。

機能: 契約情報作成
エンドポイント: POST /contracts
概要: 新規契約情報を作成する
処理概要: リクエストボディから契約情報を受け取り、バリデーション後にデータベースに登録し、登録結果を返却する
```

#### 例3: ドキュメントアップロードAPI

```
@docs/05-api/README.md @docs/05-api/api-guide.md @docs/05-api/common-specification.md @docs/05-api/specification-template.md @docs/05-api/processing-template.md @docs/02-requirements/functional-requirements.md @docs/01-architecture/database.md を参照して、以下のAPIの仕様書と処理設計書を作成してください。

機能: ドキュメントアップロード
エンドポイント: POST /documents/upload
概要: ドキュメントファイルをアップロードする
処理概要: multipart/form-dataでファイルを受け取り、ストレージに保存後、ドキュメント情報をデータベースに登録する
```

### 4.4 AIが自動的に行うこと

上記のプロンプトを投げると、AIは以下を自動的に実行します：

1. ✅ **ディレクトリ作成** - 機能カテゴリと操作名に基づいた適切なディレクトリを作成（例: `users/list/`）
2. ✅ **specification.md作成** - API仕様書テンプレートに基づいた仕様書を生成
3. ✅ **processing.md作成** - 処理設計書テンプレートに基づいた処理設計書を生成
4. ✅ **命名規則の遵守** - APIガイドの命名規則に従ったディレクトリ・ファイル名を使用
5. ✅ **共通仕様の適用** - API共通仕様書の内容を反映（認証、エラーハンドリング等）

### 4.5 注意事項

- プロンプトには必ず以下のファイルを参照させてください：
  - `@docs/05-api/` 配下の関連ファイル（README.md, api-guide.md, common-specification.md, テンプレート等）
  - `@docs/02-requirements/functional-requirements.md` - 機能要件定義
  - `@docs/01-architecture/database.md` - データベース設計
- 機能名は日本語で記載してもOKです（AIが適切な英語のディレクトリ名に変換します）
- 複雑なAPIの場合は、処理概要をより詳細に記載すると精度が向上します

---

## 5. 関連ドキュメント

### 5.1 API設計・仕様

- [API共通仕様書](./common-specification.md) - すべてのAPIに共通する仕様
- [APIガイド](./api-guide.md) - API仕様書・処理設計書の作成方法
- [API仕様書テンプレート](./specification-template.md) - specification.md のテンプレート
- [処理設計書テンプレート](./processing-template.md) - processing.md のテンプレート
- [API実装ベストプラクティス](./implementation-best-practices.md) - 実装例とコードサンプル

### 5.2 その他

- [データベース設計書](../01-architecture/database.md)
- [機能仕様書](../03-features/)
- [テスト仕様書](../06-testing/)

---

**このディレクトリ内のAPI仕様書は、実装前に必ずレビューを受けてください。**
