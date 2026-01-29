# デバイス台帳管理 (FR-004-5)

## 📑 目次

- [概要](#概要)
- [機能一覧](#機能一覧)
- [画面一覧](#画面一覧)
- [データモデル](#データモデル)
- [Flaskルート一覧](#flaskルート一覧)
- [アクセス権限](#アクセス権限)
- [関連ドキュメント](#関連ドキュメント)
- [実装ステータス](#実装ステータス)

---

## 概要

デバイス台帳管理は、IoTデバイスの物理的な在庫を管理する機能です。デバイスの購入から廃棄までのライフサイクル全体を追跡し、在庫状況、保証期限、保管場所などの情報を一元管理します。

**機能ID:** FR-004-5

**目的:**
- IoTデバイスの物理在庫の一元管理
- 購入日・保証期限の管理による保守計画の支援
- 出荷状況の追跡
- 在庫場所の管理

**対象ユーザー:**
- システム保守者（NSW内部担当者）のみ

**備考:**
- デバイス管理（FR-004-1）とは異なり、物理的な在庫管理に特化
- Azure IoT Hubsへの連携は行わない
- 論理削除方式を採用

---

## 機能一覧

| 機能ID | 機能名 | 概要 |
|--------|--------|------|
| FR-004-5-1 | デバイス台帳一覧・検索 | 台帳情報の一覧表示、検索・絞り込み |
| FR-004-5-2 | デバイス台帳登録 | デバイス台帳情報の新規登録 |
| FR-004-5-3 | デバイス台帳更新 | 台帳情報の変更 |
| FR-004-5-4 | デバイス台帳削除 | 台帳の論理削除 |
| FR-004-5-5 | デバイス台帳参照 | 台帳の詳細情報表示 |
| FR-004-5-6 | CSVエクスポート | 台帳データのCSV出力 |

---

## 画面一覧

| 画面ID | 画面名 | スラッグ | 概要 |
|--------|--------|---------|------|
| ADM-013 | デバイス台帳一覧画面 | `/admin/device-inventory` | 一覧・検索・削除 |
| ADM-014 | デバイス台帳登録画面 | `/admin/device-inventory/register` | 登録（モーダル） |
| ADM-015 | デバイス台帳更新画面 | `/admin/device-inventory/update` | 更新（モーダル） |
| ADM-016 | デバイス台帳参照画面 | `/admin/device-inventory/detail/:id` | 詳細表示（モーダル） |

---

## データモデル

### device_inventory テーブル

| カラム名 | 論理名 | データ型 | NULL | PK | FK | 説明 |
|---------|--------|----------|------|----|----|------|
| inventory_id | 台帳ID | VARCHAR(36) | NO | ○ | - | UUID形式 |
| device_id | デバイスID | VARCHAR(50) | NO | - | - | デバイスの一意識別子 |
| device_name | デバイス名 | VARCHAR(100) | NO | - | - | デバイスの名称 |
| device_type | デバイス種別 | VARCHAR(50) | NO | - | - | センサー/ゲートウェイ/コントローラー/その他 |
| model_info | モデル情報 | VARCHAR(100) | YES | - | - | モデル番号等 |
| sim_id | SIMID | VARCHAR(50) | YES | - | - | SIMカードのID |
| mac_address | MACアドレス | VARCHAR(17) | YES | - | - | XX:XX:XX:XX:XX:XX形式 |
| stock_status | 在庫状況 | VARCHAR(20) | NO | - | - | 在庫中/出荷済み/修理中/廃棄予定/廃棄済み |
| purchase_date | 購入日 | DATE | YES | - | - | デバイス購入日 |
| scheduled_ship_date | 出荷予定日 | DATE | YES | - | - | 出荷予定の日付 |
| ship_date | 出荷日 | DATE | YES | - | - | 実際の出荷日 |
| manufacturer_warranty_end | メーカー保証終了日 | DATE | YES | - | - | メーカー保証の終了日 |
| vendor_warranty_end | ベンダー保証終了日 | DATE | YES | - | - | ベンダー保証の終了日 |
| storage_location | 在庫場所 | VARCHAR(100) | YES | - | - | 保管場所 |
| organization_id | 組織ID | VARCHAR(36) | NO | - | ○ | データスコープ制限用 |
| deleted_flag | 削除フラグ | BOOLEAN | NO | - | - | 論理削除フラグ（デフォルト: FALSE） |
| created_at | 作成日時 | DATETIME | NO | - | - | レコード作成日時 |
| created_by | 作成者 | VARCHAR(36) | NO | - | - | 作成者のユーザーID |
| updated_at | 更新日時 | DATETIME | NO | - | - | レコード更新日時 |
| updated_by | 更新者 | VARCHAR(36) | NO | - | - | 更新者のユーザーID |

### インデックス

| インデックス名 | カラム | 種別 | 用途 |
|---------------|--------|------|------|
| PRIMARY | inventory_id | PRIMARY KEY | 主キー |
| idx_device_inventory_device_id | device_id | UNIQUE | デバイスID重複チェック |
| idx_device_inventory_org_id | organization_id | INDEX | データスコープ制限 |
| idx_device_inventory_stock_status | stock_status | INDEX | 在庫状況検索 |
| idx_device_inventory_device_type | device_type | INDEX | デバイス種別検索 |

---

## Flaskルート一覧

| No | ルート名 | エンドポイント | メソッド | 用途 |
|----|---------|---------------|---------|------|
| 1 | デバイス台帳一覧表示 | `/admin/device-inventory` | GET | 一覧・検索表示 |
| 2 | デバイス台帳登録画面 | `/admin/device-inventory/create` | GET | 登録モーダル表示 |
| 3 | デバイス台帳登録実行 | `/admin/device-inventory/create` | POST | 登録処理 |
| 4 | デバイス台帳詳細表示 | `/admin/device-inventory/<inventory_id>` | GET | 詳細モーダル表示 |
| 5 | デバイス台帳更新画面 | `/admin/device-inventory/<inventory_id>/edit` | GET | 更新モーダル表示 |
| 6 | デバイス台帳更新実行 | `/admin/device-inventory/<inventory_id>/update` | POST | 更新処理 |
| 7 | デバイス台帳削除実行 | `/admin/device-inventory/delete` | POST | 削除処理（複数選択対応） |
| 8 | CSVエクスポート | `/admin/device-inventory?export=csv` | GET | CSV出力 |

---

## アクセス権限

### 機能別アクセス権限

| 機能 | システム保守者 | 管理者 | 販社ユーザ | サービス利用者 |
|------|--------------|--------|----------|--------------|
| デバイス台帳一覧 | ○ | - | - | - |
| デバイス台帳参照 | ○ | - | - | - |
| デバイス台帳登録 | ○ | - | - | - |
| デバイス台帳更新 | ○ | - | - | - |
| デバイス台帳削除 | ○ | - | - | - |
| CSVエクスポート | ○ | - | - | - |

**注:** デバイス台帳管理はシステム保守者（NSW内部）専用の機能です。

### 権限制御の実装

- **グローバルメニュー:** システム保守者以外には非表示
- **ルートレベル:** `@role_required(Role.SYSTEM_ADMIN)` デコレーター
- **データスコープ:** 組織階層ベースのフィルタリング適用

---

## 関連ドキュメント

### 機能仕様

- [UI仕様書](./ui-specification.md) - 画面レイアウト、UI要素、バリデーションルール
- [ワークフロー仕様書](./workflow-specification.md) - 処理フロー、API統合、エラーハンドリング

### 共通仕様

- [共通仕様書](../../common/common-specification.md) - HTTPステータスコード、エラーコード等
- [UI共通仕様書](../../common/ui-common-specification.md) - 共通UI仕様

### 要件定義

- [機能要件定義書](../../../../02-requirements/functional-requirements.md) - FR-004-5
- [非機能要件定義書](../../../../02-requirements/non-functional-requirements.md)
- [技術要件定義書](../../../../02-requirements/technical-requirements.md)

### 関連機能

- [デバイス管理](../devices/README.md) - FR-004-1（運用中デバイスの管理）
- [CSVインポート](../csv-import/README.md) - FR-004-8（CSVインポート機能）

### アーキテクチャ

- [バックエンド設計](../../../../01-architecture/backend.md) - Flask/LDP設計
- [データベース設計](../../../../01-architecture/database.md) - テーブル定義

---

## 実装ステータス

| フェーズ | 機能 | ステータス | 備考 |
|---------|------|----------|------|
| フェーズ2 | デバイス台帳一覧・検索 | 未着手 | - |
| フェーズ2 | デバイス台帳登録 | 未着手 | - |
| フェーズ2 | デバイス台帳更新 | 未着手 | - |
| フェーズ2 | デバイス台帳削除 | 未着手 | - |
| フェーズ2 | デバイス台帳参照 | 未着手 | - |
| フェーズ2 | CSVエクスポート | 未着手 | - |

**注:** デバイス台帳管理はフェーズ2（拡張機能）での実装予定

---

**作成日:** 2026-01-26
**最終更新日:** 2026-01-26
**作成者:** Claude
