# デバイス管理機能

## 📑 目次

- [デバイス管理機能](#デバイス管理機能)
  - [📑 目次](#-目次)
  - [概要](#概要)
  - [機能一覧](#機能一覧)
  - [画面一覧](#画面一覧)
  - [データモデル](#データモデル)
    - [デバイスマスタ (device\_master)](#デバイスマスタ-device_master)
      - [テーブル設計](#テーブル設計)
      - [インデックス](#インデックス)
    - [デバイスステータス（device\_status\_data）](#デバイスステータスdevice_status_data)
      - [テーブル設計](#テーブル設計-1)
    - [ソート項目マスタ（sort\_item\_master）](#ソート項目マスタsort_item_master)
      - [テーブル設計](#テーブル設計-2)
  - [Flaskルート一覧](#flaskルート一覧)
  - [アクセス権限](#アクセス権限)
  - [実装ステータス](#実装ステータス)
  - [関連ドキュメント](#関連ドキュメント)
    - [機能仕様](#機能仕様)
    - [共通仕様](#共通仕様)
    - [要件定義](#要件定義)
    - [アーキテクチャ](#アーキテクチャ)

---

## 概要

デバイス管理機能は、IoTデバイスの基本情報を管理するためのWebアプリケーション機能です。事前にAzure IoT Hubsに登録済みのデバイス情報を本システムに登録し、デバイスの一覧表示、検索、登録、更新、削除、CSVエクスポートの操作を提供します。

**重要:** 本機能はWebアプリケーション側からAzure IoT Hubsへの連携は行いません。デバイスのIoT Hubs登録は別途Azure管理画面から事前に実施する前提です。

**機能ID:** FR-004-1

---

## 機能一覧

| 機能ID     | 機能名             | 概要                         |
| ---------- | ------------------ | ---------------------------- |
| FR-004-1-1 | デバイス一覧・検索 | デバイス情報の一覧表示と検索 |
| FR-004-1-2 | デバイス登録       | デバイス基本情報の新規登録   |
| FR-004-1-3 | デバイス更新       | デバイス基本情報の変更       |
| FR-004-1-4 | デバイス参照       | デバイスの詳細情報表示       |
| FR-004-1-5 | デバイス削除       | デバイスの論理削除           |

---

## 画面一覧

| 画面ID  | 画面名           | スラッグ                        | 表示方式 | 概要                       |
| ------- | ---------------- | ------------------------------- | -------- | -------------------------- |
| ADM-001 | デバイス一覧画面 | /admin/devices                  | 画面     | デバイスの一覧・検索・削除 |
| ADM-002 | デバイス登録画面 | /admin/devices/create           | モーダル | デバイスの新規登録         |
| ADM-003 | デバイス更新画面 | /admin/devices/<device_id>/edit | モーダル | デバイスの更新             |
| ADM-004 | デバイス参照画面 | /admin/devices/<device_id>      | モーダル | デバイスの詳細情報表示     |

---

## データモデル

### デバイスマスタ (device_master)
#### テーブル設計

| カラム名                    | 論理名                 | データ型     | 必須 | 備考                                                |
| --------------------------- | ---------------------- | ------------ | ---- | --------------------------------------------------- |
| device_id                   | デバイスID             | VARCHAR(128) | ○    | 主キー、Azure IoT Hubsと同じID                      |
| device_name                 | デバイス名             | VARCHAR(100) | ○    |                                                     |
| device_type_id              | デバイス種別ID         | INT          | ○    | 外部キー： device_type_master.device_type_id        |
| device_model                | モデル情報             | VARCHAR(100) | ○    |                                                     |
| device_stock_id             | デバイス在庫ID         | INT          | ○    | 外部キー： device_stock_info_master.device_stock_id |
| sim_id                      | SIMID                  | VARCHAR(100) |      |                                                     |
| mac_address                 | MACアドレス            | VARCHAR(100) |      |                                                     |
| organization_id             | 組織ID                 | VARCHAR(100) | ○    | 外部キー: organization_master.organization_id       |
| software_version            | ソフトウェアバージョン | VARCHAR(100) |      |                                                     |
| device_location             | 設置場所               | VARCHAR(100) |      |                                                     |
| certificate_expiration_date | 証明書期限             | DATETIME     |      |                                                     |
| delete_flag                 | 削除フラグ             | BOOLEAN      | ○    |                                                     |
| create_date                 | 作成日時               | DATETIME     | ○    |                                                     |
| creator                     | 作成者                 | VARCHAR(100) | ○    |                                                     |
| update_date                 | 更新日時               | DATETIME     |      |                                                     |
| modifier                    | 更新者                 | VARCHAR(100) |      |                                                     |

#### インデックス

| インデックス名             | カラム          | 種別   | 目的               |
| -------------------------- | --------------- | ------ | ------------------ |
| PRIMARY                    | device_id       | 主キー | デバイス一意識別   |
| idx_devices_organization   | organization_id | INDEX  | データスコープ制限 |
| idx_devices_device_type_id | device_type_id  | INDEX  | 種別検索           |
| idx_devices_name           | device_name     | INDEX  | 名前検索           |


### デバイスステータス（device_status_data）
#### テーブル設計

| カラム名    | 論理名     | データ型     | 必須 | 備考                                        |
| ----------- | ---------- | ------------ | ---- | ------------------------------------------- |
| device_id   | デバイスID | VARCHAR(128) | ○    | 主キーかつ外部キー: device_master.device_id |
| status      | ステータス | INT          | ○    | 0：未接続、1：接続済み                      |
| delete_flag | 削除フラグ | BOOLEAN      | ○    | True：論理削除済、False：その他             |
| create_date | 作成日時   | DATETIME     | ○    |                                             |
| update_date | 更新日時   | DATETIME     | ○    |                                             |

### ソート項目マスタ（sort_item_master）
#### テーブル設計

| カラム名       | 論理名       | データ型     | 必須 | 備考                            |
| -------------- | ------------ | ------------ | ---- | ------------------------------- |
| view_id        | 画面ID       | INT          | ○    | 画面（機能）固有のID            |
| sort_item_id   | ソート項目ID | INT          | ○    | ソート項目固有のID              |
| sort_item_name | ソート項目名 | VARCHAR(100) | ○    | ソート項目の内容                |
| sort_order     | 表示順序     | INT          | ○    | ソート項目リストでの表示順序    |
| delete_flag    | 削除フラグ   | BOOLEAN      | ○    | True：論理削除済、False：その他 |
| create_date    | 作成日時     | DATETIME     | ○    |                                 |
| update_date    | 更新日時     | DATETIME     | ○    |                                 |



---

## Flaskルート一覧

| No  | ルート名             | エンドポイント                      | メソッド | 用途                        | レスポンス形式     |
| --- | -------------------- | ----------------------------------- | -------- | --------------------------- | ------------------ |
| 1   | デバイス一覧初期表示 | `/admin/devices`                    | GET      | デバイス一覧の初期表示      | HTML               |
| 2   | デバイス一覧検索     | `/admin/devices`                    | POST     | デバイス検索・一覧表示      | HTML               |
| 3   | デバイス登録画面     | `/admin/devices/create`             | GET      | デバイス登録画面表示        | HTML（モーダル）   |
| 4   | デバイス登録実行     | `/admin/devices/register`           | POST     | デバイス登録処理            | リダイレクト (302) |
| 5   | デバイス参照画面     | `/admin/devices/<device_id>`        | GET      | デバイス詳細情報表示        | HTML（モーダル）   |
| 6   | デバイス更新画面     | `/admin/devices/<device_id>/edit`   | GET      | デバイス更新画面表示        | HTML（モーダル）   |
| 7   | デバイス更新実行     | `/admin/devices/<device_id>/update` | POST     | デバイス更新処理            | リダイレクト (302) |
| 8   | デバイス削除実行     | `/admin/devices/<device_id>/delete` | POST     | デバイス削除処理            | リダイレクト (302) |
| 9   | CSVエクスポート      | `/admin/devices?export=csv`         | GET      | デバイス一覧CSVダウンロード | CSV                |

---

## アクセス権限

| 機能         | システム保守者 | 管理者 | 販社ユーザ | サービス利用者 |
| ------------ | -------------- | ------ | ---------- | -------------- |
| デバイス一覧 | ◎              | ◎      | ○          | ○              |
| デバイス参照 | ◎              | ◎      | ○          | ○              |
| デバイス登録 | ◎              | ◎      | ○          | -              |
| デバイス更新 | ◎              | ◎      | ○          | -              |
| デバイス削除 | ◎              | ◎      | ○          | -              |

**凡例:**
- ◎ 制限なく利用可能（全データにアクセス可能）
- ○ 制限下で利用可（自社に紐づくデータのみアクセス可能）
- - 利用不可

**データスコープ制限:**
- 全ユーザ：自身の組織、自身の組織に紐づく傘下組織の`organization_id`を持つもののみ表示可能

---

## 実装ステータス

| 機能               | ステータス | 備考 |
| ------------------ | ---------- | ---- |
| デバイス一覧・検索 | 完了       |      |
| デバイス登録       | 完了       |      |
| デバイス編集       | 完了       |      |
| デバイス参照       | 完了       |      |
| デバイス削除       | 完了       |      |
| CSVエクスポート    | 完了       |      |

---

## 関連ドキュメント

### 機能仕様
- [UI仕様書](./ui-specification.md) - 画面レイアウト、UI要素、バリデーションルール
- [ワークフロー仕様書](./workflow-specification.md) - 処理フロー、API統合、エラーハンドリング

### 共通仕様
- [UI共通仕様書](../../common/ui-common-specification.md) - すべての画面に共通するUI仕様
- [共通仕様書](../../common/common-specification.md) - HTTPステータスコード、エラーコード、トランザクション管理

### 要件定義
- [機能要件定義書](../../../../02-requirements/functional-requirements.md) - FR-004-1 デバイス管理
- [技術要件定義書](../../../../02-requirements/technical-requirements.md) - 技術スタック、セキュリティ実装
- [非機能要件定義書](../../../../02-requirements/non-functional-requirements.md) - パフォーマンス、アクセス制御

### アーキテクチャ
- [データベース設計書](../../../../01-architecture/database.md) - テーブル定義
- [バックエンド設計書](../../../../01-architecture/backend.md) - Flask Blueprint構成

---

**この機能の実装仕様書は、実装前に必ずレビューを受けてください。**
