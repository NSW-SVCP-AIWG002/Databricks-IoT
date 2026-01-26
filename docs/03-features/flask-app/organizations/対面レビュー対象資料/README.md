# 組織管理機能 (Organizations)

## 📑 目次

- [概要](#概要)
- [機能一覧](#機能一覧)
- [画面一覧](#画面一覧)
- [データモデル](#データモデル)
- [使用テーブル](#使用テーブル)
- [Flaskルート一覧](#flaskルート一覧)
- [アクセス権限](#アクセス権限)
- [外部連携](#外部連携)
- [実装ステータス](#実装ステータス)
- [関連ドキュメント](#関連ドキュメント)

---

## 概要

組織管理機能（FR-004-4）は、Databricks IoTシステムにおける組織マスタの管理を行う機能です。組織の一覧表示、検索、参照、登録、更新、削除、CSVエクスポートの操作を提供し、Databricks ワークスペースグループとの連携を行います。

**機能ID:** FR-004-4

---

## 機能一覧

| 機能ID | 機能名 | 概要 |
| ------ | ----- | ---- |
| FR-004-4-1 | 組織一覧・検索 | 組織情報の一覧表示と検索 |
| FR-004-4-2 | 組織登録 | 組織基本情報の新規登録 |
| FR-004-4-3 | 組織更新 | 組織基本情報の変更 |
| FR-004-4-4 | 組織参照 | 組織の詳細情報表示 |
| FR-004-4-5 | 組織削除 | 組織の論理削除 |

---

## 画面一覧

| 画面ID | 画面名 | スラッグ | 表示方式 | 概要 |
|--------|--------|----------|------|------|
| ADM-009 | 組織一覧画面 | `/admin/organizations` | 画面 | 組織の一覧・検索・削除 |
| ADM-010 | 組織登録画面 | `/admin/organizations/create` | モーダル | 組織の新規登録 |
| ADM-011 | 組織更新画面 | `/admin/organizations/update` |  モーダル | 組織の更新 |
| ADM-012 | 組織参照画面 | `/admin/organizations/detail/:id` | モーダル | 組織の詳細情報表示 |

---

## データモデル

### 組織マスタ (organization_master)

#### テーブル設計

| 項目名 | 物理名 | 型 | 必須 | 説明 |
|--------|--------|-----|------|------|
| 組織ID | organization_id | INT | ○ | 組織の一意識別子（主キー） |
| 組織名 | organization_name | VARCHAR(200) | ○ | 組織の名称 |
| 組織種別ID | organization_type_id | INT | ○ | 組織種別の一意識別子（外部キー） |
| 住所 | address | VARCHAR(500) | ○ | 組織の所在地 |
| 電話番号 | phone_number | VARCHAR(20) | ○ | 組織の代表電話番号 |
| FAX | fax_number | VARCHAR(20) | - | 組織のFAX番号 |
| 担当者名 | contact_person | VARCHAR(100) | ○ | 組織の担当者氏名 |
| 契約状態ID | contract_status_id | INT | ○ | 契約状態の一意識別子（外部キー） |
| 契約開始日 | contract_start_date | DATE | ○ | 契約開始日 |
| 契約終了日 | contract_end_date | DATE | - | 契約終了日 |
| DatabricksグループID | databricks_group_id | VARCHAR(20) | ○ | DatabricksワークスペースグループID |
| 作成日時 | create_date | DATETIME | ○ | レコード作成日時 |
| 作成者 | creater | VARCHAR(100) | ○ | レコード作成者 |
| 更新日時 | update_date | DATETIME | ○ | レコード更新日時 |
| 更新者 | modifier | VARCHAR(100) | ○ | レコード更新者 |
| 削除フラグ | delete_flag | BOOLEAN | ○ | 論理削除フラグ（0: 有効, 1: 削除） |

### 組織閉包テーブル (organization_closure)

#### テーブル設計

| 項目名 | 物理名 | 型 | 必須 | 説明 |
|--------|--------|-----|------|------|
| 親組織ID | parent_organization_id | INT | ○ | 親組織の一意識別子（主キー） |
| 子組織ID | subsidiary_organization_id | INT | ○ | 子組織の一意識別子（主キー） |
| 深さ | depth | INT | ○ | 親組織から子組織への階層の深さ |
| 削除フラグ | delete_flag | BOOLEAN | ○ | 論理削除フラグ（0: 有効, 1: 削除） |

### 組織種別マスタ (organization_type_master)

#### テーブル設計

| 項目名 | 物理名 | 型 | 必須 | 説明 |
|--------|--------|-----|------|------|
| 組織種別ID | organization_type_id | INT | ○ | 組織種別の一意識別子（主キー） |
| 組織種別名 | organization_type_name | VARCHAR(50) | ○ | 組織の種別（管理会社、販売会社等） |
| 作成日時 | create_date | DATETIME | ○ | レコード作成日時 |
| 作成者 | creater | VARCHAR(100) | ○ | レコード作成者 |
| 更新日時 | update_date | DATETIME | ○ | レコード更新日時 |
| 更新者 | modifier | VARCHAR(100) | ○ | レコード更新者 |
| 削除フラグ | delete_flag | BOOLEAN | ○ | 論理削除フラグ（0: 有効, 1: 削除） |

### 契約状態マスタ (contract_status_master)

#### テーブル設計

| 項目名 | 物理名 | 型 | 必須 | 説明 |
|--------|--------|-----|------|------|
| 契約状態ID | contract_status_id | INT | ○ | 契約状態の一意識別子（主キー） |
| 契約状態名 | contract_status_name | VARCHAR(20) | ○ | 契約状態（契約中, 契約終了等） |
| 作成日時 | create_date | DATETIME | ○ | レコード作成日時 |
| 作成者 | creater | VARCHAR(100) | ○ | レコード作成者 |
| 更新日時 | update_date | DATETIME | ○ | レコード更新日時 |
| 更新者 | modifier | VARCHAR(100) | ○ | レコード更新者 |
| 削除フラグ | delete_flag | BOOLEAN | ○ | 論理削除フラグ（0: 有効, 1: 削除） |

---

## 使用テーブル

### OLTP DB (MySQL互換)

| テーブル名 | 論理名 | 操作種別 | 用途 |
|-----------|--------|---------|------|
| organization_master | 組織マスタ | SELECT, INSERT, UPDATE | 組織情報の管理 |
| organization_closure | 組織閉包テーブル | SELECT, INSERT, UPDATE | 組織の階層構造の管理 |
| organization_type_master | 組織種別マスタ | SELECT, INSERT, UPDATE | 組織種別情報の管理 |
| contract_status_master | 契約状態マスタ | SELECT, INSERT, UPDATE | 契約状態情報の管理 |

---

## Flaskルート一覧

| No | ルート名 | エンドポイント | メソッド | 用途 | レスポンス形式 |
|----|---------|---------------|---------|------|---------------|
| 1 | 組織一覧表示 | `/admin/organizations` | GET | 組織検索・一覧表示（初期表示） | HTML |
| 2 | 組織一覧表示 | `/admin/organizations` | POST | 組織検索・一覧表示（検索時） | HTML |
| 3 | 組織登録画面 | `/admin/organizations/create` | GET | 組織登録画面表示 | HTML（モーダル） |
| 4 | 組織登録実行 | `/admin/organizations/create` | POST | 組織登録処理 | リダイレクト (302) |
| 5 | 組織詳細表示 | `/admin/organizations/<databricks_group_id>` | GET | 組織詳細情報表示 | HTML（モーダル） |
| 6 | 組織更新画面 | `/admin/organizations/<databricks_group_id>/edit` | GET | 組織更新画面表示 | HTML（モーダル） |
| 7 | 組織更新実行 | `/admin/organizations/<databricks_group_id>/update` | POST | 組織更新処理 | リダイレクト (302) |
| 8 | 組織削除実行 | `/admin/organizations/delete` | POST | 組織削除処理 | リダイレクト (302) |
| 9 | CSVエクスポート | `/admin/organizations?export=csv` | GET | 組織一覧CSVダウンロード | CSV |

---

## アクセス権限

### ロール別アクセス制限

| 機能 | システム保守者 | 管理者 | 販社ユーザ | サービス利用者 |
|------|---------------|--------|-----------|---------------|
| 組織一覧 | ◎ | ◎ | ○ | - |
| 組織参照 | ◎ | ◎ | ○ | - |
| 組織登録 | ◎ | ◎ | ○ | - |
| 組織更新 | ◎ | ◎ | ○ | - |
| 組織削除 | ◎ | ◎ | ○ | - |

**凡例:**
- **◎**: 制限なく利用可能（すべてのデータにアクセス可能）
- **○**: 制限下で利用可（自社に紐づく組織のみアクセス可能）
- **-**: 利用不可

### データスコープ制限

**全ユーザー:**
- 自社に紐づく組織のみアクセス可能

---

## 外部連携

### Databricks ワークスペースグループ API

#### 連携タイミング

| 操作 | 連携内容 | API |
|------|---------|-----|
| 組織登録 | ワークスペースグループ作成 | `POST /api/2.0/accounts/{account_id}/scim/v2/Groups` |
| 組織更新 | ワークスペースグループ更新 | `PUT /api/2.0/accounts/{account_id}/scim/v2/Groups/{id}` |
| 組織削除 | ワークスペースグループ削除 | `DELETE /api/2.0/accounts/{account_id}/scim/v2/Groups/{id}` |

#### 認証方式

- **サービスプリンシパル認証**: 管理者権限を持つサービスプリンシパルのトークンを使用
- **環境変数**: `DATABRICKS_SERVICE_PRINCIPAL_TOKEN`

#### グループ命名規則

- グループ名: `organization_{organization_id}`
- 例: `organization_1`

#### エラーハンドリング

**組織登録時:**
- Databricks API失敗 → OLTP DBをロールバック（組織レコードを削除）

**組織更新時:**
- Databricks API失敗 → OLTP DBをロールバック（組織レコードを元に戻す）

**組織削除時:**
- Databricks API失敗 → OLTP DBをロールバック（組織レコードを元に戻す）

---

## 実装ステータス

### 実装優先度

**フェーズ**: フェーズ1（MVP）

**優先度**: 高

### 実装チェックリスト

#### UI実装
- [ ] ADM-009: 組織一覧画面
  - [ ] 検索フォーム
  - [ ] データテーブル
  - [ ] ページネーション
  - [ ] ソート機能
- [ ] ADM-010: 組織登録モーダル
  - [ ] フォーム入力
  - [ ] バリデーション
- [ ] ADM-011: 組織更新モーダル
  - [ ] フォーム入力（初期値設定）
  - [ ] バリデーション
- [ ] ADM-012: 組織参照モーダル
  - [ ] 詳細情報表示

#### バックエンド実装
- [ ] Flaskルート実装
  - [ ] 組織一覧取得
  - [ ] 組織登録
  - [ ] 組織更新
  - [ ] 組織削除
  - [ ] 組織詳細取得
- [ ] データベース操作
  - [ ] SELECT（一覧、詳細）
  - [ ] INSERT（登録）
  - [ ] UPDATE（更新）
  - [ ] 論理削除
- [ ] Databricks連携
  - [ ] グループ作成API
  - [ ] グループ更新API
  - [ ] グループ削除API
- [ ] セキュリティ実装
  - [ ] ロールベースアクセス制御
  - [ ] データスコープ制限
  - [ ] 入力検証
- [ ] トランザクション管理
  - [ ] OLTP DB + Databricks API連携
  - [ ] ロールバック処理

#### テスト実装
- [ ] 単体テスト
  - [ ] バリデーションテスト
  - [ ] データベース操作テスト
  - [ ] Databricks API連携テスト（モック）
- [ ] 結合テスト
  - [ ] エンドツーエンドテスト
  - [ ] エラーハンドリングテスト
  - [ ] ロールバックテスト
- [ ] E2Eテスト
  - [ ] 画面操作テスト
  - [ ] 権限制御テスト

---

## 関連ドキュメント

### 機能設計・仕様

- [UI仕様書](./ui-specification.md) - 画面レイアウト、UI要素の詳細仕様
- [ワークフロー仕様書](./workflow-specification.md) - 処理フロー、API統合、エラーハンドリング
- [機能要件定義書](../../02-requirements/functional-requirements.md) - FR-004-4（組織管理）
- [技術要件定義書](../../02-requirements/technical-requirements.md) - TR-SEC-001, TR-SEC-004, TR-SEC-005
- [非機能要件定義書](../../02-requirements/non-functional-requirements.md) - NFR-SEC-006, NFR-SEC-007

### アーキテクチャ設計

- [バックエンド設計](../../01-architecture/backend.md) - Flask/LDP設計、Blueprint構成
- [データベース設計](../../01-architecture/database.md) - テーブル定義、インデックス設計
- [インフラストラクチャ設計](../../01-architecture/infrastructure.md) - Databricks環境、Private Link

### 共通仕様

- [共通仕様書](../common/common-specification.md) - HTTPステータスコード、エラーコード、トランザクション管理
- [UI共通仕様書](../common/ui-common-specification.md) - すべての画面に共通するUI仕様

### 類似機能

- [デバイス管理機能](../devices/README.md) - 同様のCRUD画面構成
- [ユーザー管理機能](../users/README.md) - 同様のDatabricks連携（ワークスペースグループ）

---

**最終更新日:** 2025-12-19
**作成者:** Claude Sonnet 4.5
