# CSVインポート/エクスポート機能 - README

## 📑 目次

- [CSVインポート/エクスポート機能 - README](#csvインポートエクスポート機能---readme)
  - [📑 目次](#-目次)
  - [概要](#概要)
  - [機能一覧](#機能一覧)
  - [画面一覧](#画面一覧)
  - [データモデル](#データモデル)
    - [マスタ一覧（master\_list）](#マスタ一覧master_list)
      - [テーブル設計](#テーブル設計)
      - [インデックス](#インデックス)
  - [CSVフォーマット詳細](#csvフォーマット詳細)
    - [対象マスタ一覧](#対象マスタ一覧)
    - [共通仕様](#共通仕様)
    - [1. デバイス（device\_master, device\_type\_master, organization\_master）](#1-デバイスdevice_master-device_type_master-organization_master)
    - [2. ユーザー（user\_master, user\_type\_master, region\_master, organization\_master）](#2-ユーザーuser_master-user_type_master-region_master-organization_master)
    - [3. 組織（organization\_master, organization\_type\_master, contract\_status\_master）](#3-組織organization_master-organization_type_master-contract_status_master)
    - [4. アラート設定（alert\_setting\_master, alert\_level\_master, device\_name）](#4-アラート設定alert_setting_master-alert_level_master-device_name)
    - [5. デバイス在庫情報（device\_stock\_info\_master）](#5-デバイス在庫情報device_stock_info_master)
  - [Flaskルート一覧](#flaskルート一覧)
  - [アクセス権限](#アクセス権限)
  - [実装ステータス](#実装ステータス)
  - [関連ドキュメント](#関連ドキュメント)
    - [機能設計・仕様](#機能設計仕様)
    - [アーキテクチャ設計](#アーキテクチャ設計)
    - [共通仕様](#共通仕様-1)

---

## 概要

CSVインポート/エクスポート機能は、Databricks IoTシステムのマスタデータ（ユーザー、組織、デバイス等）を一括で登録・更新・削除・エクスポートする機能です。

**機能ID:** FR-004-8

---

## 機能一覧

| 機能ID | 機能名 | 説明 |
|--------|--------|------|
| FR-004-8-1 | CSVエクスポート | 各マスタ一覧画面からデータをエクスポート |
| FR-004-8-2 | CSVインポート | 専用画面からマスタデータを一括インポート |

---

## 画面一覧

| 画面ID | 画面名 | スラッグ | 表示方式 | 概要 |
|--------|-------|----------|---------|------|
| TRF-001 | CSVインポート画面 | `/transfer/csv-import` | モーダル | マスタデータの一括登録・更新・削除 |

---

## データモデル

### マスタ一覧（master_list）

#### テーブル設計

| カラム名 | 論理名 | データ型 | 必須 | 備考 |
|----------|-------|---------|------|------|
| master_id | マスタID | INT | ○ | マスタの一意識別子（主キー） |
| user_type_id | ユーザー種別ID | INT | ○ | アクセス可能なユーザーID（主キー） |
| master_name | マスタ名 | VARCHAR(20) | ○ | マスタの名称 |
| create_date | 作成日時 | DATETIME | ○ | レコード作成日時 |
| creator | 作成者 | INT | ○ | レコード作成者のユーザーID |
| update_date | 更新日時 | DATETIME | ○ | レコード更新日時 |
| modifier | 更新者 | VARCHAR(20) | ○ | レコード更新者のユーザーID |
| delete_flag | 削除フラグ | BOOLEAN | ○ | 論理削除フラグ（0: 有効, 1: 削除） |

#### インデックス

| インデックス名 | カラム | 種別 | 目的 |
|---------------|--------|-----|------|
| PRIMARY | master_id, user_type_id | 主キー（複合キー） | マスタの一意識別子、アクセス可能なユーザーID |

**注**: 詳細なテーブル定義は [データベース設計書](../../common/app-database-specification.md) を参照してください。

---

## CSVフォーマット詳細

### 対象マスタ一覧

本機能では以下のマスタデータを対象とします。

| No | マスタ名 | テーブル名 | 主キー | 備考 |
|----|---------|-----------|--------|------|
| 1 | デバイスマスタ | device_master | device_id | - |
| 2 | ユーザーマスタ | user_master | user_id | - |
| 3 | 組織マスタ | organization_master | organization_id | - |
| 4 | アラート設定マスタ | alert_setting_master | alert_id | - |
| 5 | デバイス在庫情報マスタ | device_stock_info_master | device_stock_id | システム保守者のみ |

**注:** データベース設計の詳細は [データベース設計書](../../common/app-database-specification.md) を参照してください。

### 共通仕様

**文字コード:**
- エクスポート: UTF-8 BOM付き
- インポート: UTF-8（BOM付き/なし）、Shift-JIS、EUC-JP（自動検出）

**区切り文字:**
- カンマ (`,`)

**ヘッダー行:**
- 必須（1行目）

**ファイルサイズ**
- 最大 10MB

**データ型フォーマット:**
- 日付型: `YYYY-MM-DD`（ISO 8601形式）
- 日時型: `YYYY-MM-DD HH:mm:ss`（ISO 8601形式）
- 真偽値: `true` / `false`（小文字）
- NULL値: 空文字（カンマのみ）

**エスケープ:**
- カンマを含む値: ダブルクォーテーションで囲む
- ダブルクォーテーションを含む値: `""` でエスケープ

### 1. デバイス（device_master, device_type_master, organization_master）

**CSVフォーマット:**

| 表示名 | データカラム名 | データ型 | 必須 | 最大長 | 備考 |
|--------|---------------|---------|-----|--------|------|
| デバイスID | device_master.device_uuid | string | ○ | 128 | デバイスの一意の識別キー |
| デバイス名 | device_master.device_name | string | ○ | 100 | - |
| デバイス種別 | device_type_master.device_type_name | string | ○ | 100 | device_type_idをキーに参照 |
| モデル情報 | device_master.device_model | string | ○ | 100 | - |
| SIMID | device_master.sim_id | string | - | 20 | - |
| MACアドレス | device_master.mac_address | string | - | 17 | - |
| 設置場所 | device_master.device_location | string | - | 100 | - |
| 所属組織 | organization_master.organization_name | string | ○ | 200 | organization_idをキーに参照 |
| 証明書期限 | device_master.certificate_expiration_date | date | - | - | - |

**CSVサンプル:**
```csv
デバイスID,デバイス名,デバイス種別,モデル情報,SIMID,MACアドレス,設置場所,所属組織,証明書期限
DEV-001,温度センサー1号機,センサー,MODEL-A100,12345678901234567890,AA:BB:CC:DD:EE:FF,本社ビル1階 サーバールーム,A株式会社,2025-12-31
DEV-002,温度センサー2号機,センサー,MODEL-A200,12345678901234567891,AA:BB:CC:DD:EE:FG,本社ビル2階 サーバールーム,A株式会社,2025-12-31
```

---

### 2. ユーザー（user_master, user_type_master, region_master, organization_master）

**CSVフォーマット:**

| 表示名 | データカラム名 | データ型 | 必須 | 最大長 | 備考 |
|--------|---------------|---------|-----|--------|------|
| ユーザーID | user_master.user_id | int | ○ | - | ユーザーの一意の識別キー |
| ユーザー名 | user_master.user_name | string | ○ | 20 | - |
| メールアドレス | user_master.email_address | string | ○ | 254 | - |
| 所属 | organization_master.organization_name | string | ○ | 200 | organization_idをキーに参照 |
| ユーザー種別 | user_type_master.user_type_name | string | ○ | 20 | user_type_idをキーに参照 |
| 地域 | region_master.region_name | string | ○ | 50 | region_idをキーに参照 |
| 住所 | user_master.address | string | - | 500 | - |
| アラート通知メール受信設定 | user_master.alert_notification_flag | boolean | ○ | - | - |
| システム通知メール受信設定 | user_master.system_notification_flag | boolean | ○ | - | - |

**CSVサンプル:**
```csv
ユーザーID,ユーザー名,メールアドレス,所属,ユーザー種別,地域,住所,アラート通知メール受信設定,システム通知メール受信設定
1,山田太郎,yamada@example.com,組織A,管理者,東京都,東京都渋谷区...,true,true
2,佐藤花子,sato@example.com,組織A,管理者,東京都,東京都渋谷区...,true,true
```

---

### 3. 組織（organization_master, organization_type_master, contract_status_master）

**CSVフォーマット:**

| 表示名 | データカラム名 | データ型 | 必須 | 最大長 | 備考 |
|--------|---------------|---------|-----|--------|------|
| 組織ID | organization_master.organization_id | int | ○ | - | - |
| 組織名 | organization_master.organization_name | string | ○ | 200 | - |
| 組織種別 | organization_type_master.organization_type_name | string | ○ | 50 | organization_type_idをキーに参照 |
| 所属組織 | organization_master.organization_name | string | ○ | 200 | organization_closureのparent_organization_idをキーに参照 |
| 住所 | organization_master.address | string | ○ | 500 | - |
| 電話番号 | organization_master.phone_number | string | ○ | 20 | - |
| FAX | organization_master.fax_number | string | - | 20 | - |
| 担当者名 | organization_master.contact_person | string | ○ | 20 | - |
| 契約状態 | contract_status_master.contract_status_name | string | ○ | 20 | contract_status_idをキーに参照 |
| 契約開始日 | organization_master.contract_start_date | date | ○ | - | - |
| 契約終了日 | organization_master.contract_end_date | date | ○ | - | - |

**CSVサンプル:**
```csv
組織ID,組織名,組織種別,所属組織,住所,電話番号,FAX,担当者名,契約状態,契約開始日,契約終了日
1,組織A,販売会社,NSW株式会社,東京都渋谷区...,03-1234-5678,03-1234-5679,山田太郎,契約中,2025-01-01,2026-12-31
2,組織B,販売会社,NSW株式会社,大阪府大阪市...,06-1234-5678,06-1234-5679,佐藤花子,契約中,2025-01-01,2026-12-31
```

---

### 4. アラート設定（alert_setting_master, alert_level_master, device_name）

**CSVフォーマット:**

| 表示名 | データカラム名 | データ型 | 必須 | 最大長 | 備考 |
|--------|---------------|---------|-----|--------|------|
| アラートID | alert_setting_master.alert_id | int | ○ | - | - |
| アラート名 | alert_setting_master.alert_name | string | ○ | 100 | - |
| デバイス名 | device_master.device_name | string | ○ | 100 | device_idをキーに参照 |
| アラート発生条件_測定項目 | alert_setting_master.alert_conditions_field | string | ○ | 100 | - |
| アラート発生条件_比較演算子 | alert_setting_master.alert_conditions_operator | string | ○ | 10 | - |
| アラート発生条件_閾値 | alert_setting_master.alert_conditions_threshold | float | ○ | - | - |
| アラート復旧条件_測定項目 | alert_setting_master.alert_recovery_field | string | ○ | 100 | - |
| アラート復旧条件_比較演算子 | alert_setting_master.alert_recovery_operator | string | ○ | 10 | - |
| アラート復旧条件_閾値 | alert_setting_master.alert_recovery_threshold | float | ○ | - | - |
| 判定時間 | alert_setting_master.judgment_time | int | ○ | - | - |
| アラートレベル | alert_level_master.alert_level_name | string | ○ | 100 | - |
| アラート通知 | alert_setting_master.alert_notification_flag | boolean | ○ | - | - |
| メール送信 | alert_setting_master.alert_email_flag | boolean | ○ | - | - |

**CSVサンプル:**
```csv
アラートID,アラート名,デバイス名,アラート発生条件_測定項目,アラート発生条件_比較演算子,アラート発生条件_閾値,アラート復旧条件_測定項目,アラート復旧条件_比較演算子,アラート復旧条件_閾値,判定時間,アラートレベル,アラート通知,メール送信
1,温度異常,DEV-001,temperature,>,30.0,temperature,<=,30.0,5,Warning,true,false
2,湿度異常,DEV-001,humidity,>,50.0,humidity,<=,50.0,5,Warning,true,false
```

---

### 5. デバイス在庫情報（device_stock_info_master）

**CSVフォーマット:**

未定

**CSVサンプル:**
```csv
```

**備考:** デバイス在庫情報はシステム保守者のみアクセス可能。

---

## Flaskルート一覧

| No | ルート名 | エンドポイント | メソッド | 用途 | レスポンス形式 |
|----|---------|---------------|---------|------|---------------|
| 1 | CSVインポート画面 | `/transfer/csv-import` | GET | CSVインポート画面表示 | HTML（モーダル） |
| 2 | CSVインポート実行 | `/transfer/csv-import` | POST | CSVファイルアップロード・インポート実行 | HTML（モーダル） |
| 3 | デバイス一覧エクスポート | `/admin/devices?export=csv` | GET | デバイス一覧CSVエクスポート | CSV (ダウンロード) |
| 4 | ユーザー一覧エクスポート | `/admin/users?export=csv` | GET | ユーザー一覧CSVエクスポート | CSV (ダウンロード) |
| 5 | 組織一覧エクスポート | `/admin/organizations?export=csv` | GET | 組織一覧CSVエクスポート | CSV (ダウンロード) |
| 6 | アラート設定一覧エクスポート | `/admin/alert-settings?export=csv` | GET | アラート設定一覧CSVエクスポート | CSV (ダウンロード) |
| 7 | デバイス在庫一覧エクスポート | `/admin/device-inventory?export=csv` | GET | デバイス在庫一覧CSVエクスポート | CSV (ダウンロード) |

---

## アクセス権限

| 機能 | システム保守者 | 管理者 | 販社ユーザ | サービス利用者 |
|------|---------------|--------|-----------|---------------|
| CSVインポート | ○ | ○ | ○ | - |
| CSVエクスポート | ○ | ○ | ○ | - |

**凡例**:
- **○**: 利用可能
- **-**: 利用不可

**データスコープ制限**:
- **すべてのユーザー**: 組織階層（organization_closure）によるデータスコープ制限
  - ユーザーの所属組織とその下位組織に属するユーザーのみアクセス可能

---

## 実装ステータス

| 機能 | UI仕様書 | ワークフロー仕様書 | 実装 | テスト | ステータス | 
|------|----------|------------------|------|-------|-----------|
| CSVインポート | 完了 | 完了 | 未着手 | 未着手 | 設計中 |
| CSVエクスポート | 完了 | 完了 | 未着手 | 未着手 | 設計中 |

---

## 関連ドキュメント

### 機能設計・仕様
- [UI仕様書](./ui-specification.md) - TRF-001 CSVインポート画面のUI仕様
- [ワークフロー仕様書](./workflow-specification.md) - インポート/エクスポート処理フローの詳細
- [機能要件定義書](../../../02-requirements/functional-requirements.md) - FR-004-8
- [技術要件定義書](../../../02-requirements/technical-requirements.md) - TR-BE-004
- [非機能要件定義書](../../../02-requirements/non-functional-requirements.md) - セキュリティ、パフォーマンス要件

### アーキテクチャ設計
- [バックエンド設計](../../../01-architecture/backend.md) - Flask/LDP設計
- [データベース設計](../../../01-architecture/database.md) - テーブル定義、インデックス設計

### 共通仕様
- [共通仕様書](../../common/common-specification.md) - HTTPステータスコード、エラーコード、トランザクション管理、セキュリティ等
- [認証仕様書](../../common/authentication-specification.md) - 認証アーキテクチャ、Token Exchange、Unity Catalog接続
- [UI共通仕様書](../../common/ui-common-specification.md) - すべての画面に共通するUI仕様

---

**最終更新日:** 2026-01-06
**作成者:** Claude (AI Assistant)
