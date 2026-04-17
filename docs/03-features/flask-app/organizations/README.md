# 組織管理機能

## 📑 目次

- [組織管理機能](#組織管理機能)
  - [📑 目次](#-目次)
  - [概要](#概要)
  - [機能一覧](#機能一覧)
  - [画面一覧](#画面一覧)
  - [データモデル](#データモデル)
    - [組織マスタ (organization\_master)](#組織マスタ-organization_master)
      - [テーブル設計](#テーブル設計)
      - [インデックス](#インデックス)
    - [組織閉包テーブル (organization\_closure)](#組織閉包テーブル-organization_closure)
      - [テーブル設計](#テーブル設計-1)
      - [インデックス](#インデックス-1)
    - [組織種別マスタ (organization\_type\_master)](#組織種別マスタ-organization_type_master)
      - [テーブル設計](#テーブル設計-2)
      - [インデックス](#インデックス-2)
    - [契約状態マスタ (contract\_status\_master)](#契約状態マスタ-contract_status_master)
      - [テーブル設計](#テーブル設計-3)
      - [インデックス](#インデックス-3)
  - [Flaskルート一覧](#flaskルート一覧)
  - [アクセス権限](#アクセス権限)
  - [関連ドキュメント](#関連ドキュメント)
    - [設計仕様書](#設計仕様書)
    - [要件定義書](#要件定義書)
    - [アーキテクチャ設計](#アーキテクチャ設計)
    - [共通仕様](#共通仕様)

---

## 概要

組織管理機能は、Databricks IoTシステムにおける組織マスタの管理を行う機能です。組織の一覧表示、検索、参照、登録、更新、削除、CSVエクスポートの操作を提供します。

**機能ID:** FR-004-4

---

## 機能一覧

| 機能ID | 機能名 | 概要 |
|--------|-------|------|
| FR-004-4-1 | 組織一覧・検索 | 組織情報の一覧表示と検索 |
| FR-004-4-2 | 組織登録 | 組織基本情報の新規登録 |
| FR-004-4-3 | 組織更新 | 組織基本情報の変更 |
| FR-004-4-4 | 組織参照 | 組織の詳細情報表示 |
| FR-004-4-5 | 組織削除 | 組織の論理削除 |
| FR-004-4-6 | CSVエクスポート | 組織のCSVエクスポート |

---

## 画面一覧

| 画面ID | 画面名 | スラッグ | 表示方式 | 概要 |
|--------|-------|----------|---------|------|
| ADM-009 | 組織一覧画面 | `/admin/organizations` | 画面 | 組織の一覧・検索・削除 |
| ADM-010 | 組織登録画面 | `/admin/organizations/create` | モーダル | 組織の新規登録 |
| ADM-011 | 組織更新画面 | `/admin/organizations/<organization_uuid>/edit` |  モーダル | 組織の更新 |
| ADM-012 | 組織参照画面 | `/admin/organizations/<organization_uuid>` | モーダル | 組織の詳細情報表示 |

---

## データモデル

### 組織マスタ (organization_master)

#### テーブル設計

| カラム名 | 論理名 | データ型 | 必須 | 備考 |
|----------|-------|---------|------|------|
| organization_id | 組織ID | INT | ○ | 組織の一意識別子（主キー） |
| organization_uuid | 組織UUID | VARCHAR(36) | ○ | 組織の外部公開用識別子（URLパスパラメータとして使用） |
| organization_name | 組織名 | VARCHAR(200) | ○ | 組織の名称 |
| organization_type_id | 組織種別ID | INT | ○ | 組織種別の一意識別子（外部キー） |
| address | 住所 | VARCHAR(500) | ○ | 組織の所在地 |
| phone_number | 電話番号 | VARCHAR(20) | ○ | 組織の代表電話番号 |
| fax_number | FAX | VARCHAR(20) | - | 組織のFAX番号 |
| contact_person | 担当者名 | VARCHAR(20) | ○ | 組織の担当者氏名 |
| contract_status_id | 契約状態ID | INT | ○ | 契約状態の一意識別子（外部キー） |
| contract_start_date | 契約開始日 | DATE | ○ | 契約開始日 |
| contract_end_date | 契約終了日 | DATE | - | 契約終了日 |
| create_date | 作成日時 | DATETIME | ○ | レコード作成日時 |
| creator | 作成者 | INT | ○ | レコード作成者のユーザID |
| update_date | 更新日時 | DATETIME | ○ | レコード更新日時 |
| modifier | 更新者 | INT | ○ | レコード更新者のユーザID |
| delete_flag | 削除フラグ | BOOLEAN | ○ | 論理削除フラグ（0: 有効, 1: 削除） |

#### インデックス

| インデックス名 | カラム | 種別 | 目的 |
|---------------|--------|-----|------|
| PRIMARY | organization_id | 主キー | 組織の一意識別子 |

### 組織閉包テーブル (organization_closure)

#### テーブル設計

| カラム名 | 論理名 | データ型 | 必須 | 備考 |
|----------|-------|---------|------|------|
| parent_organization_id | 親組織ID | INT | ○ | 親組織の一意識別子（主キー） |
| subsidiary_organization_id | 子組織ID | INT | ○ | 子組織の一意識別子（主キー） |
| depth | 深さ | INT | ○ | 親組織から子組織への階層の深さ |

#### インデックス

| インデックス名 | カラム | 種別 | 目的 |
|---------------|--------|-----|------|
| PRIMARY | parent_organization_id, subsidiary_organization_id | 主キー（複合キー） | 親組織、子組織の一意識別子 |
| idx_subsidiary_organization_id | subsidiary_organization_id | INDEX | 子組織の検索 |

### 組織種別マスタ (organization_type_master)

#### テーブル設計

| カラム名 | 論理名 | データ型 | 必須 | 備考 |
|----------|-------|---------|------|------|
| organization_type_id | 組織種別ID | INT | ○ | 組織種別の一意識別子（主キー） |
| organization_type_name | 組織種別名 | VARCHAR(50) | ○ | 組織の種別（管理会社、販売会社等） |
| create_date | 作成日時 | DATETIME | ○ | レコード作成日時 |
| creator | 作成者 | INT | ○ | レコード作成者のユーザID |
| update_date | 更新日時 | DATETIME | ○ | レコード更新日時 |
| modifier | 更新者 | INT | ○ | レコード更新者のユーザID |
| delete_flag | 削除フラグ | BOOLEAN | ○ | 論理削除フラグ（0: 有効, 1: 削除） |

#### インデックス

| インデックス名 | カラム | 種別 | 目的 |
|---------------|--------|-----|------|
| PRIMARY | organization_type_id | 主キー | 組織種別の一意識別子 |

### 契約状態マスタ (contract_status_master)

#### テーブル設計

| カラム名 | 論理名 | データ型 | 必須 | 備考 |
|----------|-------|---------|------|------|
| contract_status_id | 契約状態ID | INT | ○ | 契約状態の一意識別子（主キー） |
| contract_status_name | 契約状態名 | VARCHAR(20) | ○ | 契約状態（契約中, 契約終了等） |
| create_date | 作成日時 | DATETIME | ○ | レコード作成日時 |
| creator | 作成者 | INT | ○ | レコード作成者のユーザID |
| update_date | 更新日時 | DATETIME | ○ | レコード更新日時 |
| modifier | 更新者 | INT | ○ | レコード更新者のユーザID |
| delete_flag | 削除フラグ | BOOLEAN | ○ | 論理削除フラグ（0: 有効, 1: 削除） |

#### インデックス

| インデックス名 | カラム | 種別 | 目的 |
|---------------|--------|-----|------|
| PRIMARY | contract_status_id | 主キー | 契約状態の一意識別子 |

---

## Flaskルート一覧

| No | ルート名 | エンドポイント | メソッド | 用途 | レスポンス形式 |
|----|---------|---------------|---------|------|---------------|
| 1 | 組織一覧初期表示 | `/admin/organizations` | GET | 組織一覧初期表示・ページング | HTML |
| 2 | 組織一覧検索 | `/admin/organizations` | POST | 組織検索実行 | HTML |
| 3 | 組織登録画面 | `/admin/organizations/create` | GET | 組織登録フォーム表示 | HTML（モーダル） |
| 4 | 組織登録実行 | `/admin/organizations/register` | POST | 組織登録処理 | リダイレクト (302) |
| 5 | 組織参照画面 | `/admin/organizations/<organization_uuid>` | GET | 組織詳細情報表示 | HTML（モーダル） |
| 6 | 組織更新画面 | `/admin/organizations/<organization_uuid>/edit` | GET | 組織更新フォーム表示 | HTML（モーダル） |
| 7 | 組織更新実行 | `/admin/organizations/<organization_uuid>/update` | POST | 組織更新処理 | リダイレクト (302) |
| 8 | 組織削除実行 | `/admin/organizations/delete` | POST | 組織削除処理（複数件対応）| リダイレクト (302) |
| 9 | CSVエクスポート | `/admin/organizations/export` | POST | 組織一覧CSVダウンロード | CSV |

---

## アクセス権限

| 機能 | システム保守者 | 管理者 | 販社ユーザ | サービス利用者 |
|------|---------------|--------|-----------|---------------|
| 組織一覧 | ○ | ○ | ○ | - |
| 組織参照 | ○ | ○ | ○ | - |
| 組織登録 | ○ | ○ | ○ | - |
| 組織更新 | ○ | ○ | ○ | - |
| 組織削除 | ○ | ○ | ○ | - |
| CSVエクスポート | ○ | ○ | ○ | - |

**凡例**:
- **○**: 利用可能
- **-**: 利用不可

**データスコープ制限**:
- **すべてのユーザー**: 組織階層（organization_closure）によるデータスコープ制限
  - ユーザーの所属組織とその下位組織に属するユーザーのみアクセス可能

**機能制限**
- サービス利用者に対して、組織管理機能へのアクセスを禁止する

---

## 関連ドキュメント

### 設計仕様書

- [UI仕様書](./ui-specification.md) - 画面レイアウト、UI要素の詳細仕様
- [ワークフロー仕様書](./workflow-specification.md) - 処理フロー、API統合、エラーハンドリング

### 要件定義書

- [機能要件定義書](../../../02-requirements/functional-requirements.md) - FR-004-4: 組織管理
- [非機能要件定義書](../../../02-requirements/non-functional-requirements.md) - NFR-SEC-006, NFR-SEC-007
- [技術要件定義書](../../../02-requirements/technical-requirements.md) - TR-SEC-001, TR-SEC-004, TR-SEC-005

### アーキテクチャ設計

- [バックエンド設計](../../../01-architecture/backend.md) - Flask/LDP設計
- [フロントエンド設計](../../../01-architecture/frontend.md) - Flask + Jinja2設計
- [データベース設計](../../../01-architecture/database.md) - テーブル定義、インデックス設計

### 共通仕様

- [共通仕様書](../../common/common-specification.md) - HTTPステータスコード、エラーコード、トランザクション管理、セキュリティ等
- [認証仕様書](../../common/authentication-specification.md) - 認証アーキテクチャ、Token Exchange、Unity Catalog接続
- [UI共通仕様書](../../common/ui-common-specification.md) - すべての画面に共通するUI仕様
