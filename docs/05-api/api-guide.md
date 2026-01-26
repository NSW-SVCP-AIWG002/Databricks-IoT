# APIガイド（API仕様書・処理設計書作成ガイド）

## 📑 目次

1. [概要](#1-概要)
2. [命名規則とディレクトリ構成](#2-命名規則とディレクトリ構成)
   - 2.1 [ディレクトリ構造](#21-ディレクトリ構造)
   - 2.2 [機能カテゴリの命名規則](#22-機能カテゴリの命名規則)
   - 2.3 [操作名の標準化](#23-操作名の標準化)
   - 2.4 [ディレクトリ作成手順](#24-ディレクトリ作成手順)
   - 2.5 [命名例](#25-命名例)
   - 2.6 [実際のディレクトリ構成例](#26-実際のディレクトリ構成例)
3. [API仕様書テンプレート](#3-api仕様書テンプレート)
   - 3.1 [使用方法](#31-使用方法)
4. [処理設計書テンプレート](#4-処理設計書テンプレート)
   - 4.1 [使用方法](#41-使用方法)
5. [作成時の注意事項](#5-作成時の注意事項)
   - 5.1 [一貫性を保つ](#51-一貫性を保つ)
   - 5.2 [REST API設計指針に従う](#52-rest-api設計指針に従う)
   - 5.3 [具体例を記載](#53-具体例を記載)
   - 5.4 [バリデーション要件を明記](#54-バリデーション要件を明記)
   - 5.5 [エラーケースを網羅](#55-エラーケースを網羅)
6. [関連ドキュメント](#6-関連ドキュメント)

---

## 1. 概要

このドキュメントは、API仕様書および処理設計書を作成する際のガイドラインです。

**⚠️ 重要**: API仕様書を作成する前に、必ず[API共通仕様書](./common-specification.md)を確認してください。共通仕様書には、ベースURL、認証・認可、共通レスポンスフォーマット、エラーハンドリングなど、すべてのAPIに適用される共通ルールが記載されています。

すべてのAPI仕様書・処理設計書は、以下のルールに従って作成してください：
- **[API共通仕様書](./common-specification.md)の内容を理解する**（最優先）
- 統一されたディレクトリ構成とテンプレートを使用
- 命名規則に従ったディレクトリ・ファイル名
- REST API設計指針に準拠

---

## 2. 命名規則とディレクトリ構成

### 2.1 ディレクトリ構造

各APIは **機能カテゴリ > 操作名** の階層構造で管理します。

```
{機能カテゴリ}/{操作名}/
├── specification.md    # API仕様書（入力・出力・エラー仕様）
└── processing.md       # 処理設計書（処理フロー・ロジック詳細）
```

### 2.2 機能カテゴリの命名規則

| 項目 | 規則 | 例 |
|------|------|-----|
| **言語** | 英語 | `users`, `groups` |
| **形式** | 複数形 | `users` (単数形 `user` は使用しない) |
| **文字種** | 小文字のみ | `users` (`Users` は使用しない) |
| **区切り** | ハイフン使用可 | `user-groups` |

**主要な機能カテゴリ:**
- `users` - ユーザ管理
- `groups` - グループ管理
- `contracts` - 契約管理
- `documents` - ドキュメント管理
- `notifications` - 通知管理
- `settings` - 設定管理

### 2.3 操作名の標準化

| 操作名 | 意味 | HTTPメソッド | エンドポイント例 |
|--------|------|-------------|----------------|
| `list` | 一覧取得 | GET | `GET /users` |
| `get` | 詳細取得 | GET | `GET /users/{userId}` |
| `create` | 作成 | POST | `POST /users` |
| `update` | 更新 | PUT/PATCH | `PUT /users/{userId}` |
| `delete` | 削除 | DELETE | `DELETE /users/{userId}` |
| `search` | 検索 | GET | `GET /users/search?q=keyword` |
| `upload` | アップロード | POST | `POST /documents/upload` |
| `download` | ダウンロード | GET | `GET /documents/{documentId}/download` |

**注:** その他の操作が必要な場合は、適切な動詞を使用してください（例: `activate`, `deactivate`, `export`, `import`）

### 2.4 ディレクトリ作成手順

#### 1. 機能カテゴリを決定

機能の種類に応じて、適切なカテゴリを選択または新規作成します。

**例:** ユーザ管理のAPIを作成する場合 → `users/`

#### 2. 操作名を決定

標準化された操作名から選択します。

**例:** ユーザ一覧取得APIを作成する場合 → `list`

#### 3. ディレクトリを作成

```bash
mkdir -p docs/05-api/{機能カテゴリ}/{操作名}
```

**例:**
```bash
mkdir -p docs/05-api/users/list
mkdir -p docs/05-api/users/create
mkdir -p docs/05-api/groups/delete
```

#### 4. ファイルを作成

各ディレクトリに `specification.md` と `processing.md` を作成します。

```bash
# specification.md の作成
touch docs/05-api/users/list/specification.md

# processing.md の作成
touch docs/05-api/users/list/processing.md
```

### 2.5 命名例

| 機能 | 操作 | ディレクトリパス | ファイル |
|------|------|----------------|---------|
| ユーザ管理 | 一覧取得 | `users/list/` | `specification.md`, `processing.md` |
| ユーザ管理 | 詳細取得 | `users/get/` | `specification.md`, `processing.md` |
| ユーザ管理 | 作成 | `users/create/` | `specification.md`, `processing.md` |
| ユーザ管理 | 更新 | `users/update/` | `specification.md`, `processing.md` |
| ユーザ管理 | 削除 | `users/delete/` | `specification.md`, `processing.md` |
| グループ管理 | 一覧取得 | `groups/list/` | `specification.md`, `processing.md` |
| グループ管理 | 作成 | `groups/create/` | `specification.md`, `processing.md` |
| 契約管理 | 一覧取得 | `contracts/list/` | `specification.md`, `processing.md` |
| ドキュメント管理 | アップロード | `documents/upload/` | `specification.md`, `processing.md` |

### 2.6 実際のディレクトリ構成例

```
docs/05-api/
├── users/
│   ├── list/
│   │   ├── specification.md
│   │   └── processing.md
│   ├── get/
│   │   ├── specification.md
│   │   └── processing.md
│   ├── create/
│   │   ├── specification.md
│   │   └── processing.md
│   └── update/
│       ├── specification.md
│       └── processing.md
│
└── documents/
    ├── upload/
    |   ├── specification.md
    |   └── processing.md
    └── delete/
        ├── specification.md
        └── processing.md
```

---

## 3. API仕様書テンプレート

`specification.md` を作成する際は、以下のテンプレートファイルを使用してください。

**テンプレートファイル:** [specification-template.md](./specification-template.md)

### 3.1 使用方法

1. テンプレートファイルの内容をコピー
2. 新規作成したAPIディレクトリ（例: `users/list/`）に `specification.md` として保存
3. `{プレースホルダー}` 部分を実際の値に置き換え
4. 不要なセクションは削除せず「なし」と記載

---

## 4. 処理設計書テンプレート

`processing.md` を作成する際は、以下のテンプレートファイルを使用してください。

**テンプレートファイル:** [processing-template.md](./processing-template.md)

### 4.1 使用方法

1. テンプレートファイルの内容をコピー
2. 新規作成したAPIディレクトリ（例: `users/list/`）に `processing.md` として保存
3. `{プレースホルダー}` 部分を実際の値に置き換え
4. 処理フロー図やシーケンス図を追加

---

## 5. 作成時の注意事項

### 5.1 一貫性を保つ

- テンプレートに従い、すべてのAPI仕様書で構成を統一してください

### 5.2 REST API設計指針に従う

- **パスパラメータ**と**クエリパラメータ**は以下の指針に従って使い分けてください

#### パスパラメータの使用

リソースを一意に識別する情報に使用します：
- リソースID（例: `/api/users/{userId}`）
- 特定のリソースの詳細取得・更新・削除
- 階層的なリソース構造（例: `/api/contracts/{contractId}/users/{userId}`）

**例:**
```
GET /api/users/{userId}           # ユーザ詳細取得
PUT /api/groups/{groupId}         # グループ更新
DELETE /api/documents/{documentId} # ドキュメント削除
```

#### クエリパラメータの使用

リソースの検索・絞り込み・表示制御に使用します：
- **検索・絞り込み**: `?name=山田&role=user`
- **ページング**: `?page=1&per_page=20`
- **並び替え**: `?sort=createdAt&order=desc`
- **フィルタリング**: `?status=active&startDate=2025-01-01`
- **フィールド選択**: `?fields=id,name,email`

**例:**
```
GET /api/users?role=user&page=1&per_page=20&sort=name
GET /api/documents?status=indexed&tag=重要&createdAfter=2025-01-01
GET /api/contracts?status=active&sort=endDate&order=asc
```

#### パラメータ使用の判断基準

| 用途 | パラメータ種別 | 例 |
|------|---------------|-----|
| リソース識別 | パスパラメータ | `/api/users/{userId}` |
| リソース階層 | パスパラメータ | `/api/contracts/{contractId}/documents` |
| 検索条件 | クエリパラメータ | `?name=山田&email=yamada@example.com` |
| ページング | クエリパラメータ | `?page=1&per_page=20` |
| 並び替え | クエリパラメータ | `?sort=createdAt&order=desc` |
| フィルタリング | クエリパラメータ | `?status=active&role=user` |
| 部分取得 | クエリパラメータ | `?fields=id,name,email` |

### 5.3 具体例を記載

- 入力サンプル、リクエスト例、レスポンス例は必ず実際のJSON/curlコマンドを記載してください
- プロジェクトの標準レスポンス形式（`success`, `data`, `error`, `timestamp`）に従ってください

### 5.4 バリデーション要件を明記

- 入力パラメータ詳細の表で、各フィールドのバリデーションルール（最小桁、最大桁、必須など）を明確に記載してください
- 備考欄には、形式制約（UUID形式、メールアドレス形式など）を記載してください

### 5.5 エラーケースを網羅

- レスポンス詳細の表で、想定されるエラー条件とそのレスポンスを記載してください
- レスポンス例で、代表的なエラーケース（400, 401, 500など）のJSON例を記載してください

---

## 6. 関連ドキュメント

- [API共通仕様書](./common-specification.md) - すべてのAPIに共通する仕様
- [API実装ベストプラクティス](./implementation-best-practices.md) - 実装例とコードサンプル
- [README.md](./README.md) - API仕様書ディレクトリの概要
- [データベース設計書](../01-architecture/database.md)
- [機能仕様書](../03-features/)
- [テスト仕様書](../06-testing/)

---

**このガイドに従って、統一されたAPI仕様書を作成してください。**
