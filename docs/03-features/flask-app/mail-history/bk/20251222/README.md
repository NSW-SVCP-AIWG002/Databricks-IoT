# メール通知履歴 (mail-history) - 機能概要

## 📑 目次

- [基本情報](#基本情報)
- [機能概要](#機能概要)
- [データモデル](#データモデル)
- [使用テーブル一覧](#使用テーブル一覧)
- [画面一覧](#画面一覧)
- [Flaskルート一覧](#flaskルート一覧)
- [実装ステータス](#実装ステータス)
- [関連ドキュメント](#関連ドキュメント)

---

## 基本情報

| 項目 | 内容 |
|------|------|
| 機能ID | FR-005-2 |
| 機能名 | メール通知履歴 |
| カテゴリ | 履歴機能 |
| 画面ID | NTC-005（一覧画面）、NTC-006（参照画面） |
| 実装領域 | Flask アプリケーション |
| ディレクトリ | `docs/03-features/flask-app/mail-history/` |

---

## 機能概要

### 目的

システム内で送信されたメール通知の履歴を参照する機能。アラート通知メール、招待メール、パスワードリセットメールなどの送信履歴を一覧表示し、詳細を確認できる。

### 主要機能

- **メール通知履歴の一覧表示**: 送信されたメールの履歴を一覧表示
- **メール通知履歴の検索・絞り込み**: メール種別、送信先、キーワード、日時範囲で検索
- **メール通知履歴の詳細表示**: メールの件名・本文・送信日時などの詳細をモーダルで表示

### 特徴

- **参照専用機能**: 登録・更新・削除機能なし
- **データスコープ制限**: 販社ユーザとサービス利用者は自社に紐づくデータのみ閲覧可能
- **検索機能**: メール種別、送信先、キーワード、日時範囲による検索に対応
- **ページネーション**: 大量のメール履歴を効率的に表示

### アクセス権限

| ロール | 権限レベル | アクセス可能なデータ範囲 |
|--------|-----------|---------------------|
| システム保守者 | ◎ | 全データにアクセス可能 |
| 管理者 | ◎ | 全データにアクセス可能 |
| 販社ユーザ | ○ | 自社に紐づくデータのみ |
| サービス利用者 | ○ | 自社データのみ |

---

## データモデル

### エンティティ関連図（ER図）

```mermaid
erDiagram
    MAIL_HISTORY ||--o| USER_MASTER : "送信先ユーザー"
    MAIL_HISTORY ||--o| ORGANIZATION_MASTER : "関連組織"

    MAIL_HISTORY {
        VARCHAR mail_history_id PK "メール送信履歴ID（UUID）"
        VARCHAR mail_type "メール種別"
        VARCHAR sender_email "送信元メールアドレス"
        VARCHAR recipient_email "送信先メールアドレス"
        VARCHAR subject "メール件名"
        TEXT body "メール本文"
        DATETIME2 sent_at "送信日時"
        VARCHAR user_id FK "関連ユーザーID"
        VARCHAR organization_id FK "関連組織ID"
        DATETIME2 create_date "作成日時"
        VARCHAR creator "作成者"
        DATETIME2 update_date "更新日時"
        VARCHAR modifier "更新者"
    }

    USER_MASTER {
        VARCHAR user_id PK "ユーザーID"
        VARCHAR user_name "ユーザー名"
        VARCHAR email_address "メールアドレス"
        VARCHAR organization_id FK "組織ID"
    }

    ORGANIZATION_MASTER {
        VARCHAR organization_id PK "組織ID"
        VARCHAR organization_name "組織名"
    }
```

### データ項目定義

#### メール通知履歴（mail_history）

| No | カラム名 | 論理名 | データ型 | NULL | デフォルト値 | 説明 |
|----|---------|--------|---------|------|-------------|------|
| 1 | mail_history_id | メール送信履歴ID | VARCHAR(100) | NOT NULL | - | 主キー、UUID |
| 2 | mail_type | メール種別 | VARCHAR(50) | NOT NULL | - | アラート通知、招待メール、パスワードリセット、システム通知 |
| 3 | sender_email | 送信元メールアドレス | VARCHAR(255) | NOT NULL | - | 送信元のメールアドレス |
| 4 | recipient_email | 送信先メールアドレス | VARCHAR(255) | NOT NULL | - | 送信先のメールアドレス |
| 5 | subject | メール件名 | VARCHAR(500) | NOT NULL | - | メールの件名 |
| 6 | body | メール本文 | TEXT | NOT NULL | - | メールの本文（HTML可） |
| 7 | sent_at | 送信日時 | DATETIME2 | NOT NULL | - | メール送信日時 |
| 8 | user_id | 関連ユーザーID | VARCHAR(100) | NULL | - | 関連するユーザーID（外部キー、user_master.user_id参照） |
| 9 | organization_id | 関連組織ID | VARCHAR(100) | NULL | - | 関連する組織ID（外部キー、organization_master.organization_id参照、データスコープ制限用） |
| 10 | create_date | 作成日時 | DATETIME2 | NOT NULL | GETDATE() | レコード作成日時 |
| 11 | creator | 作成者 | VARCHAR(100) | NOT NULL | - | レコード作成者のユーザID |
| 12 | update_date | 更新日時 | DATETIME2 | NULL | - | レコード最終更新日時 |
| 13 | modifier | 更新者 | VARCHAR(100) | NULL | - | レコード更新者のユーザID |

**外部キー:**
- `user_id` → `user_master.user_id`
- `organization_id` → `organization_master.organization_id`

**ビジネスルール:**
- mail_history_idはUUID形式で生成
- mail_typeは固定値（alert, invitation, password_reset, system）
- メール送信履歴は作成のみで更新は行わない（update_date, modifierは通常NULL）
- データスコープ制限: organization_idでアクセス制御

---

## 使用テーブル一覧

| No | テーブル名 | 論理名 | 操作種別 | 用途 |
|----|-----------|--------|---------|------|
| 1 | mail_history | メール送信履歴 | SELECT | メール通知履歴の一覧・検索・参照 |
| 2 | user_master | ユーザーマスタ | SELECT | 関連ユーザー情報の取得 |
| 3 | organization_master | 組織マスタ | SELECT | 関連組織情報の取得 |

**注:** テーブル詳細は [アプリケーションデータベース設計書](../../common/app-database-specification.md) を参照してください。

### インデックス設計

| テーブル名 | インデックス名 | カラム | 種別 | 用途 |
|-----------|--------------|--------|------|------|
| mail_history | PRIMARY | mail_history_id | PRIMARY KEY | 主キー |
| mail_history | idx_organization_id | organization_id | INDEX | データスコープ制限用 |
| mail_history | idx_sent_at | sent_at | INDEX | 日時範囲検索用 |
| mail_history | idx_mail_type | mail_type | INDEX | メール種別検索用 |

---

## 画面一覧

| 画面ID | 画面名 | パス | 概要 |
|--------|--------|------|------|
| NTC-005 | メール通知履歴一覧画面 | `/notice/mail-history` | メール通知履歴の一覧・検索 |
| NTC-006 | メール通知履歴参照画面 | `/notice/mail-history/<mail_history_id>` | メール通知履歴の詳細表示（モーダル） |

---

## Flaskルート一覧

| No | ルート名 | エンドポイント | メソッド | 用途 | レスポンス形式 | 備考 |
|----|---------|---------------|---------|------|---------------|------|
| 1 | メール通知履歴一覧表示 | `/notice/mail-history` | GET | メール通知履歴一覧表示 | HTML | ページング・検索対応 |
| 2 | メール通知履歴参照 | `/notice/mail-history/<mail_history_id>` | GET | メール通知履歴詳細表示 | HTML（パーシャル） | モーダル表示 |

---

## 実装ステータス

### 全体進捗

| 項目 | ステータス | 備考 |
|------|-----------|------|
| 要件定義 | ✅ 完了 | functional-requirements.md に記載 |
| UI仕様書 | 🔄 作成中 | ui-specification.md |
| ワークフロー仕様書 | 🔄 作成中 | workflow-specification.md |
| データベース設計 | ✅ 完了 | mail_history テーブル |
| フロントエンド実装 | ⏳ 未着手 | - |
| バックエンド実装 | ⏳ 未着手 | - |
| テスト | ⏳ 未着手 | - |

### 画面別実装ステータス

| 画面ID | 画面名 | UI設計 | ワークフロー設計 | 実装 | テスト | 備考 |
|--------|--------|--------|---------------|------|--------|------|
| NTC-005 | メール通知履歴一覧画面 | 🔄 | 🔄 | ⏳ | ⏳ | - |
| NTC-006 | メール通知履歴参照画面 | 🔄 | 🔄 | ⏳ | ⏳ | - |

### 凡例
- ✅ 完了
- 🔄 進行中
- ⏳ 未着手

---

## 関連ドキュメント

### 機能設計・仕様

- [UI仕様書](./ui-specification.md) - 画面レイアウト、UI要素の詳細仕様
- [ワークフロー仕様書](./workflow-specification.md) - ユーザー操作の処理フローと動作詳細
- [機能要件定義書](../../../02-requirements/functional-requirements.md) - FR-005-2: メール通知履歴
- [非機能要件定義書](../../../02-requirements/non-functional-requirements.md) - パフォーマンス・セキュリティ要件
- [技術要件定義書](../../../02-requirements/technical-requirements.md) - Flask/Jinja2技術仕様

### アーキテクチャ設計

- [アーキテクチャ概要](../../../01-architecture/overview.md)
- [バックエンド設計](../../../01-architecture/backend.md) - Flask/Blueprint設計
- [フロントエンド設計](../../../01-architecture/frontend.md) - Flask + Jinja2設計
- [データベース設計](../../../01-architecture/database.md) - テーブル定義、インデックス設計

### 共通仕様

- [共通仕様書](../../common/common-specification.md) - HTTPステータスコード、エラーコード、セキュリティ等
- [UI共通仕様書](../../common/ui-common-specification.md) - すべての画面に共通するUI仕様
- [アプリケーションデータベース設計書](../../common/app-database-specification.md) - テーブル定義、インデックス設計

---

**このドキュメントは、実装前に必ずレビューを受けてください。**
