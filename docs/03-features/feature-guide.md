# 機能仕様書作成ガイド

## 📑 目次

- [概要](#概要)
- [実装領域の分類](#実装領域の分類)
- [命名規則とディレクトリ構成](#命名規則とディレクトリ構成)
  - [ディレクトリ構造](#ディレクトリ構造)
  - [命名規則](#命名規則)
  - [ディレクトリ作成手順](#ディレクトリ作成手順)
  - [実際のディレクトリ構成例](#実際のディレクトリ構成例)
- [UI仕様書テンプレート](#ui仕様書テンプレート)
  - [使用方法](#使用方法)
  - [AI を使用したUI仕様書の作成](#ai-を使用したui仕様書の作成)
- [ワークフロー仕様書テンプレート](#ワークフロー仕様書テンプレート)
  - [使用方法](#使用方法-1)
  - [AI を使用したワークフロー仕様書の作成](#ai-を使用したワークフロー仕様書の作成)
- [作成時の注意事項](#作成時の注意事項)
- [関連ドキュメント](#関連ドキュメント)

---

## 概要

このドキュメントは、Databricks IoTシステムの機能仕様書を作成する際のガイドラインです。

本システムは2つの実装領域に分かれています：
1. **Flask アプリケーション**: Webアプリケーション（マスタ管理、履歴表示、ダッシュボード）
2. **LDP パイプライン**: データ処理パイプライン（シルバー層、ゴールド層）

すべての機能仕様書は、以下のルールに従って作成してください：
- 統一されたディレクトリ構成とテンプレートを使用
- 命名規則に従ったディレクトリ・ファイル名
- UIとワークフロー仕様書の責務を明確に分離

---

## 実装領域の分類

### Flask アプリケーション（`flask-app/`）

Databricks Apps（App Compute）上で動作するFlask + Jinja2 Webアプリケーション

**対象機能：**
- FR-004: マスタ管理機能（デバイス、ユーザー、組織、アラート設定など）
- FR-005: 履歴機能（アラート履歴、メール通知履歴）
- FR-006: 分析機能（ダッシュボード）

**ドキュメント構成：**
- README.md（機能概要）
- ui-specification.md（UI仕様）
- workflow-specification.md（ワークフロー仕様）

### LDP パイプライン（`ldp-pipeline/`）

Lakeflow 宣言型パイプライン（Python/SQL）によるストリーム処理

**対象機能：**
- FR-002: データ取込み機能（シルバー層、ゴールド層）

**ドキュメント構成：**
- README.md（機能概要）
- workflow-specification.md（ワークフロー仕様）
- ※UIがないため、ui-specification.mdは不要

---

## 命名規則とディレクトリ構成

### ディレクトリ構造

各機能は以下の階層構造で管理します。

**Flask アプリケーション:**
```
flask-app/{機能名}/
├── README.md                 # 機能概要（概要・データモデル・API一覧・実装ステータス）
├── ui-specification.md       # UI仕様書（画面レイアウト・UI要素・バリデーションルール定義）
└── workflow-specification.md # ワークフロー仕様書（処理フロー・API統合・状態管理）
```

**LDP パイプライン:**
```
ldp-pipeline/{処理層名}/
├── README.md                 # 機能概要（概要・データモデル・テーブル一覧・実装ステータス）
└── workflow-specification.md # ワークフロー仕様書（処理フロー・データ変換・エラーハンドリング）
```

---

### 命名規則

#### ディレクトリ名

| 項目 | 規則 | 例 |
|------|------|-----|
| **言語** | 英語 | `devices`, `silver-layer` |
| **形式** | ハイフン区切り | `silver-layer` (アンダースコア `silver_layer` は使用しない) |
| **文字種** | 小文字のみ | `silver-layer` (`SilverLayer` は使用しない) |

#### Flask app ディレクトリ名

| 機能ID | 機能名 | ディレクトリ名 |
|--------|--------|--------------|
| FR-004-1 | デバイス管理 | `devices` |
| FR-004-2 | ユーザー管理 | `users` |
| FR-004-3 | 組織管理 | `organizations` |
| FR-004-4 | アラート設定管理 | `alert-settings` |
| FR-004-5 | デバイス台帳管理 | `device-inventory` |
| FR-004-6 | メール通知設定管理 | `mail-settings` |
| FR-004-7 | アカウント管理 | `account` |
| FR-004-8 | CSVインポート | `csv-import` |
| FR-005-1 | アラート履歴 | `alert-history` |
| FR-005-2 | メール通知履歴 | `mail-history` |
| FR-006-1 | ダッシュボード | `dashboard` |

#### LDP pipeline ディレクトリ名

| 処理層 | 機能名 | ディレクトリ名 |
|--------|--------|--------------|
| シルバー層 | データ構造化・異常検出 | `silver-layer` |
| ゴールド層 | 集計・分析データ生成 | `gold-layer` |

---

### データ長規則

#### 人名

最大20文字とする

**例:** 作成者、更新者、担当者名

---

### ディレクトリ作成手順

#### 1. 実装領域を決定

機能がFlaskアプリケーションかLDPパイプラインかを決定します。

**例:** デバイス管理機能を作成する場合 → `flask-app/`

#### 2. ディレクトリ名を決定

命名規則に従ってディレクトリ名を決定します。

**例:** デバイス管理機能 → `devices`

#### 3. ディレクトリを作成

```bash
# Flask アプリケーション機能の場合
mkdir -p docs/03-features/flask-app/{機能名}

# LDP パイプライン機能の場合
mkdir -p docs/03-features/ldp-pipeline/{処理層名}
```

**例:**
```bash
# デバイス管理機能
mkdir -p docs/03-features/flask-app/devices

# シルバー層処理
mkdir -p docs/03-features/ldp-pipeline/silver-layer
```

#### 4. ファイルを作成

```bash
# Flask アプリケーション機能の場合（3ファイル）
touch docs/03-features/flask-app/{機能名}/README.md
touch docs/03-features/flask-app/{機能名}/ui-specification.md
touch docs/03-features/flask-app/{機能名}/workflow-specification.md

# LDP パイプライン機能の場合（2ファイル、UIなし）
touch docs/03-features/ldp-pipeline/{処理層名}/README.md
touch docs/03-features/ldp-pipeline/{処理層名}/workflow-specification.md
```

**例:**
```bash
# デバイス管理機能
touch docs/03-features/flask-app/devices/README.md
touch docs/03-features/flask-app/devices/ui-specification.md
touch docs/03-features/flask-app/devices/workflow-specification.md

# シルバー層処理
touch docs/03-features/ldp-pipeline/silver-layer/README.md
touch docs/03-features/ldp-pipeline/silver-layer/workflow-specification.md
```

---

### 実際のディレクトリ構成例

```
docs/03-features/
├── flask-app/
│   ├── devices/
│   │   ├── README.md
│   │   ├── ui-specification.md
│   │   └── workflow-specification.md
│   ├── users/
│   │   ├── README.md
│   │   ├── ui-specification.md
│   │   └── workflow-specification.md
│   └── dashboard/
│       ├── README.md
│       ├── ui-specification.md
│       └── workflow-specification.md
│
└── ldp-pipeline/
    ├── silver-layer/
    │   ├── README.md
    │   └── workflow-specification.md
    └── gold-layer/
        ├── README.md
        └── workflow-specification.md
```

---

## UI仕様書テンプレート

`ui-specification.md` を作成する際は、以下のテンプレートファイルを使用してください。

**テンプレートファイル:** [ui-specification-template.md](./templates/ui-specification-template.md)

**注:** LDP パイプライン機能には UI がないため、ui-specification.md は不要です。

### 使用方法

1. テンプレートファイルの内容をコピー
2. 新規作成した機能ディレクトリ（例: `flask-app/devices/`）に `ui-specification.md` として保存
3. `{プレースホルダー}` 部分を実際の値に置き換え
4. 不要なセクションは削除せず「なし」と記載

### AI を使用したUI仕様書の作成

Claude や他のAIアシスタントを使用する場合は、以下のプロンプトを使用してください：

```
@ui-specification-template.md を参照して、デバイス管理画面の ui-specification.md を作成してください。

画面名: デバイス管理画面
機能: デバイスの検索・一覧表示・登録・更新・削除
使用するAPI:
- GET /api/devices - デバイス一覧取得
- POST /api/devices - デバイス作成
- PUT /api/devices/{id} - デバイス更新
- DELETE /api/devices/{id} - デバイス削除
```

**プロンプト例の説明:**
- `@ui-specification-template.md` でテンプレートファイルを参照
- 画面名と機能の概要を簡潔に記載
- 使用するAPIを列挙
- AIがテンプレートに沿って自動的にui-specification.mdを生成

---

## ワークフロー仕様書テンプレート

`workflow-specification.md` を作成する際は、以下のテンプレートファイルを使用してください。

**テンプレートファイル:** [workflow-specification-template.md](./templates/workflow-specification-template.md)

**このファイルの役割:**
- ユーザー操作のトリガー条件（Flask appの場合）
- 処理フローの詳細（API呼び出しシーケンス、データ変換処理）
- バリデーション実行タイミング（いつチェックするか）
- エラーハンドリングフロー
- UI状態遷移（Flask appの場合）
- 複雑なAPI統合パターン（シーケンス図、状態管理、ロールバック処理）
- ストリーム処理フロー（LDP pipelineの場合）

**注:** このテンプレートには、基本的なワークフローセクションに加えて、複雑な場合のみ使用するセクション（シーケンス図、状態管理、パフォーマンス最適化）が含まれています。機能の複雑さに応じて必要なセクションのみを記載してください。

### 使用方法

1. テンプレートファイルの内容をコピー
2. 機能ディレクトリに `workflow-specification.md` として保存
3. `{プレースホルダー}` 部分を実際の値に置き換え
4. 各ワークフローの処理フローを記載

### AI を使用したワークフロー仕様書の作成

Claude や他のAIアシスタントを使用する場合は、以下のプロンプトを使用してください：

#### Flask アプリケーション機能の場合

**基本的なワークフローの場合:**

```
@workflow-specification-template.md を参照して、デバイス管理画面の workflow-specification.md を作成してください。

画面名: デバイス管理画面
主要なワークフロー:
- 初期表示: GET /api/devices でデバイス一覧を取得
- 検索: 検索条件でフィルタリング
- デバイス登録: POST /api/devices でデバイス作成、成功時に一覧を再取得

複雑度: 基本的（シーケンス図、状態管理のセクションは不要）
```

**複雑なAPI統合が必要な場合:**

```
@workflow-specification-template.md を参照して、デバイス管理画面の workflow-specification.md を作成してください。

画面名: デバイス管理画面
主要なワークフロー:
- 初期表示: GET /api/devices でデバイス一覧を取得
- デバイス登録（複数API連鎖）:
  1. POST /api/devices でデバイス作成
  2. POST /api/device-organizations で組織紐付け（失敗時はデバイス削除）
  3. POST /api/notifications で通知送信（失敗時は警告のみ）

複雑度: 高（シーケンス図、ロールバック実装例、状態管理を含む）
```

#### LDP パイプライン機能の場合

```
@workflow-specification-template.md を参照して、シルバー層処理の workflow-specification.md を作成してください。

処理名: シルバー層処理
主要なワークフロー:
- Event Hubsからストリーム取込み
- データ構造化（JSON → Delta Lake形式）
- 異常検出（閾値チェック）
- アラート生成（異常データの場合）
- OLTP DB更新（デバイスステータス更新）

複雑度: 高（ストリーム処理、エラーハンドリング、パフォーマンス最適化を含む）
```

**プロンプト例の説明:**
- `@workflow-specification-template.md` でテンプレートファイルを参照
- 画面名/処理名と主要なワークフローを簡潔に記載
- 複雑度を明記することで、AIが適切なセクションを含めて生成
- 連鎖的なAPI呼び出しやロールバック処理がある場合は、その旨を明記

---

## 作成時の注意事項

### 1. 一貫性を保つ

- テンプレートに従い、すべての機能仕様書で構成を統一してください

### 2. UIとワークフローの責務を明確に分離

- **UI仕様書 (`ui-specification.md`)**: 画面レイアウト、UI要素の詳細仕様、バリデーションルール定義（何をチェックするか）
- **ワークフロー仕様書 (`workflow-specification.md`)**: 処理フロー、バリデーション実行タイミング（いつどのようにチェックするか）、エラーハンドリング、API呼び出しシーケンス、状態管理

### 3. Flask SSRルート設計指針を理解する

本システムはFlask SSR（Server-Side Rendering）を採用しているため、REST APIではなくFlaskルートとして設計します。

**Flask SSR の特徴:**
- JSONレスポンスではなく、HTMLレスポンス（`render_template()`）またはリダイレクト（`redirect()`）を返す
- ルートは `/api/users` ではなく `/users` の形式
- クライアントサイドJavaScriptは最小限（Jinja2テンプレートでサーバーサイドレンダリング）

#### ルート設計の基本

| 操作 | HTTPメソッド | エンドポイント例 | レスポンス形式 | 用途 |
|------|-------------|----------------|---------------|------|
| 一覧表示 | GET | `/users` | HTML | ユーザー一覧画面表示 |
| 詳細表示 | GET | `/users/<user_id>` | HTML | ユーザー詳細画面表示 |
| 登録画面 | GET | `/users/create` | HTML | ユーザー登録フォーム表示 |
| 登録実行 | POST | `/users/create` | リダイレクト (302) | ユーザー登録処理、成功時一覧へリダイレクト |
| 更新画面 | GET | `/users/<user_id>/edit` | HTML | ユーザー更新フォーム表示 |
| 更新実行 | POST | `/users/<user_id>/update` | リダイレクト (302) | ユーザー更新処理、成功時詳細へリダイレクト |
| 削除実行 | POST | `/users/<user_id>/delete` | リダイレクト (302) | ユーザー削除処理、成功時一覧へリダイレクト |

**注:** 本システムではDELETEメソッドではなく、POSTメソッドで削除処理を実装します（HTMLフォームの制約のため）。

#### パスパラメータの使用

リソースを一意に識別する情報に使用します：
- リソースID（例: `/users/<user_id>`）
- 特定のリソースの詳細表示・更新・削除

**例:**
```
GET  /users/<user_id>           # ユーザ詳細表示
GET  /users/<user_id>/edit      # ユーザ更新フォーム表示
POST /users/<user_id>/update    # ユーザ更新実行
POST /users/<user_id>/delete    # ユーザ削除実行
```

#### クエリパラメータの使用

リソースの検索・絞り込み・表示制御に使用します：
- **検索・絞り込み**: `?keyword=山田&role=user`
- **ページング**: `?page=1&per_page=20`
- **並び替え**: `?sort_by=name&order=desc`
- **フィルタリング**: `?status=active&created_after=2025-01-01`

**例:**
```
GET /users?keyword=山田&role=user&page=1&per_page=20&sort_by=name&order=asc
GET /devices?status=active&organization_id=org_001&page=2
GET /alert-history?device_id=dev_001&start_date=2025-01-01&end_date=2025-01-31
```

#### パラメータ使用の判断基準

| 用途 | パラメータ種別 | 例 |
|------|---------------|-----|
| リソース識別 | パスパラメータ | `/users/<user_id>` |
| 検索条件 | クエリパラメータ | `?keyword=山田&email=yamada@example.com` |
| ページング | クエリパラメータ | `?page=1&per_page=20` |
| 並び替え | クエリパラメータ | `?sort_by=created_at&order=desc` |
| フィルタリング | クエリパラメータ | `?status=active&role=user` |

### 4. Flask app と LDP pipeline の違いを理解する

| 項目 | Flask アプリケーション | LDP パイプライン |
|------|---------------------|----------------|
| UI仕様書 | 必要 | 不要 |
| ワークフロー仕様書 | 必要 | 必要 |
| 主な内容 | ユーザー操作フロー | データ処理フロー |
| データソース | OLTP DB、Unity Catalog | Event Hubs、Unity Catalog |

### 5. セキュリティ設計の徹底

- **Flask app**: データスコープ制限をアプリケーション層で実装（WHERE句）
- **LDP pipeline**: Unity Catalogのアクセス制御を活用
- **認証・認可**: Databricks Platform側で実施（アプリケーション側では実装不要）

### 6. パフォーマンス要件の遵守

- **データ処理**: 5分以内（FR-002-2）
- **画面表示**: 3秒以内（NR-PERF-001）
- **大量データ対応**: ページネーション、インデックス設計

---

## 関連ドキュメント

### 機能設計・仕様

- [README.md](./README.md) - 機能仕様書ディレクトリの概要
- [UI共通仕様書](./common/ui-common-specification.md) - すべての画面に共通するUI仕様
- [UI仕様書テンプレート](./templates/ui-specification-template.md) - ui-specification.md のテンプレート
- [ワークフロー仕様書テンプレート](./templates/workflow-specification-template.md) - workflow-specification.md のテンプレート（API統合パターンを含む）
- [機能要件定義書](../02-requirements/functional-requirements.md)
- [技術要件定義書](../02-requirements/technical-requirements.md)
- [非機能要件定義書](../02-requirements/non-functional-requirements.md)

### アーキテクチャ設計

- [アーキテクチャ概要](../01-architecture/overview.md)
- [バックエンド設計](../01-architecture/backend.md) - Flask/LDP設計
- [フロントエンド設計](../01-architecture/frontend.md) - Flask + Jinja2設計
- [データベース設計書](../01-architecture/database.md)

### データベース

- [データベース設計書](../01-architecture/database.md) - テーブル定義、インデックス設計

**注:** 共通のHTTPステータスコード、エラーコード、トランザクション管理方針、セキュリティ方針は [common/common-specification.md](./common/common-specification.md) で管理されます

### テスト仕様

- [テスト仕様書](../06-testing/)

---

**このガイドに従って、統一された機能仕様書を作成してください。**
