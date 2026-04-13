# デバイス台帳管理 (FR-004-5)

> **注記**: 本仕様書では、簡単のため「デバイス在庫情報マスタ」を「台帳マスタ」と記載する。

## 📑 目次

- [概要](#概要)
- [機能一覧](#機能一覧)
- [画面一覧](#画面一覧)
- [データモデル](#データモデル)
- [Flaskルート一覧](#flaskルート一覧)
- [アクセス権限](#アクセス権限)
- [関連ドキュメント](#関連ドキュメント)

---

## 概要

デバイス台帳管理は、NSWが保有するセンサーやゲートウェイといったIoTデバイスの、物理的な在庫を管理する機能です。デバイス購入から廃棄まで、ライフサイクル全体を追跡し、保証期限、保管場所などの情報を一元管理します。

**機能ID:** FR-004-5

**目的:**
- IoTデバイスの物理在庫の一元管理
- 購入日・保証期限の管理による、システム保守者が行う保守計画の支援
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

| 機能ID     | 機能名                 | 概要                               |
| ---------- | ---------------------- | ---------------------------------- |
| FR-004-5-1 | デバイス台帳一覧・検索 | 台帳情報の一覧表示、検索・絞り込み |
| FR-004-5-2 | デバイス台帳登録       | デバイス台帳情報の新規登録         |
| FR-004-5-3 | デバイス台帳更新       | 台帳情報の変更                     |
| FR-004-5-4 | デバイス台帳削除       | 台帳の論理削除                     |
| FR-004-5-5 | デバイス台帳参照       | 台帳の詳細情報表示                 |
| FR-004-5-6 | CSVエクスポート        | 台帳データのCSV出力                |

---

## 画面一覧

| 画面ID  | 画面名                   | 概要                     |
| ------- | ------------------------ | ------------------------ |
| ADM-013 | デバイス台帳一覧画面     | 一覧・検索・削除         |
| ADM-014 | デバイス台帳登録画面     | 登録（モーダル）         |
| ADM-015 | デバイス台帳更新画面     | 更新（モーダル）         |
| ADM-016 | デバイス台帳参照画面     | 詳細表示（モーダル）     |
| ADM-017 | デバイス台帳登録確認画面 | 登録確認（モーダル）     |
| ADM-018 | デバイス台帳更新確認画面 | 更新確認（モーダル）     |
| ADM-019 | デバイス台帳削除確認画面 | 削除確認（モーダル）     |
| ADM-020 | デバイス台帳登録完了画面 | 登録完了通知（モーダル） |
| ADM-021 | デバイス台帳更新完了画面 | 更新完了通知（モーダル） |
| ADM-022 | デバイス台帳削除完了画面 | 削除完了通知（モーダル） |

---

## データモデル

### デバイス在庫情報マスタ (device_inventory_master)

**概要**: デバイスの在庫・配備状況を管理するテーブル

| #   | カラム物理名                   | カラム論理名       | データ型     | NULL     | PK  | FK  | デフォルト値      | 説明                                                                                                                    |
| --- | ------------------------------ | ------------------ | ------------ | -------- | --- | --- | ----------------- | ----------------------------------------------------------------------------------------------------------------------- |
| 1   | device_inventory_id            | デバイス在庫ID     | INT          | NOT NULL | ○   | -   | AUTO_INCREMENT    | デバイス在庫ID（主キー、自動採番）                                                                                      |
| 2   | device_inventory_uuid          | デバイス在庫UUID   | VARCHAR(36)  | NOT NULL | -   | -   | UUID自動生成      | デバイス在庫の外部公開用識別子（URLパスパラメータとして使用）                                                           |
| 3   | inventory_status_id            | 在庫状況ID         | INT          | NOT NULL | -   | ○   | -                 | 在庫状況ID（inventory_status_master参照）                                                                               |
| 4   | device_model                   | モデル情報         | VARCHAR(100) | NOT NULL | -   | -   | -                 | デバイスのモデル名・型番（オリジナル値を履歴として保持）                                                                |
| 5   | mac_address                    | MACアドレス        | VARCHAR(17)  | NOT NULL | -   | -   | -                 | ネットワークインターフェースの物理アドレス。コロン区切り形式（AA:BB:CC:DD:EE:FF）で格納（オリジナル値を履歴として保持） |
| 6   | purchase_date                  | 購入日             | DATETIME     | NOT NULL | -   | -   | -                 | デバイス購入日                                                                                                          |
| 7   | estimated_ship_date            | 出荷予定日         | DATETIME     | NULL     | -   | -   | -                 | デバイス出荷予定日                                                                                                      |
| 8   | ship_date                      | 出荷日             | DATETIME     | NULL     | -   | -   | -                 | デバイス出荷日                                                                                                          |
| 9   | manufacturer_warranty_end_date | メーカー保証終了日 | DATETIME     | NOT NULL | -   | -   | -                 | メーカー保証の終了日                                                                                                    |
| 10  | inventory_location             | 在庫場所           | VARCHAR(100) | NOT NULL | -   | -   | -                 | 現在の在庫保管場所                                                                                                      |
| 11  | create_date                    | 作成日時           | DATETIME     | NOT NULL | -   | -   | CURRENT_TIMESTAMP | レコード作成日時                                                                                                        |
| 12  | creator                        | 作成者             | INT          | NOT NULL | -   | -   | -                 | レコード作成者のユーザID                                                                                                |
| 13  | update_date                    | 更新日時           | DATETIME     | NOT NULL | -   | -   | CURRENT_TIMESTAMP | レコード最終更新日時                                                                                                    |
| 14  | modifier                       | 更新者             | INT          | NOT NULL | -   | -   | -                 | レコード更新者のユーザID                                                                                                |
| 15  | delete_flag                    | 削除フラグ         | BOOLEAN      | NOT NULL | -   | -   | FALSE             | 論理削除状態：TRUE　その他の場合：FALSE                                                                                 |

**外部キー:**
- `inventory_status_id` → `inventory_status_master.inventory_status_id`

**ビジネスルール:**
- device_inventory_idは1デバイスにつき1レコード（1:1関係）
- inventory_status_idで在庫状態を管理
- デバイス情報（device_id, device_name等）はdevice_masterテーブルからdevice_inventory_idで参照
- device_model、mac_addressはオリジナル値を履歴として残しておくため台帳マスタに設置

---

### 在庫状況マスタ (inventory_status_master)

**概要**: デバイス在庫状況のステータスを管理するマスタテーブル

| #   | カラム物理名          | カラム論理名 | データ型     | NULL     | PK  | FK  | デフォルト値      | 説明                                    |
| --- | --------------------- | ------------ | ------------ | -------- | --- | --- | ----------------- | --------------------------------------- |
| 1   | inventory_status_id   | 在庫状況ID   | INT          | NOT NULL | ○   | -   | AUTO_INCREMENT    | 自動採番、在庫状況の一意識別子          |
| 2   | inventory_status_name | 在庫状況名   | VARCHAR(100) | NOT NULL | -   | -   | -                 | 在庫状況の表示名                        |
| 3   | create_date           | 作成日時     | DATETIME     | NOT NULL | -   | -   | CURRENT_TIMESTAMP | レコード作成日時                        |
| 4   | creator               | 作成者       | INT          | NOT NULL | -   | -   | -                 | レコード作成者のユーザID                |
| 5   | update_date           | 更新日時     | DATETIME     | NOT NULL | -   | -   | CURRENT_TIMESTAMP | レコード最終更新日時                    |
| 6   | modifier              | 更新者       | INT          | NOT NULL | -   | -   | -                 | レコード更新者のユーザID                |
| 7   | delete_flag           | 削除フラグ   | BOOLEAN      | NOT NULL | -   | -   | FALSE             | 論理削除状態：TRUE　その他の場合：FALSE |

**初期データ:**
| inventory_status_id | inventory_status_name | 説明                 |
| ------------------- | --------------------- | -------------------- |
| 1                   | 在庫中                | 倉庫に保管中         |
| 2                   | 出荷予定              | 出荷待ち             |
| 3                   | 出荷済み              | 顧客へ出荷完了       |
| 4                   | 修理中                | 修理・メンテナンス中 |
| 5                   | 返却予定              | 顧客から返却待ち     |
| 6                   | 廃棄予定              | 廃棄待ち             |
| 7                   | 廃棄済み              | 廃棄完了             |

---

### デバイスマスタ (device_master)

**概要**: IoTデバイスの基本情報を管理するテーブル。デバイス台帳登録時に、device_inventory_masterと同時にレコードが作成される。device_uuidは接続するクラウドサービス（Azure IoT Hubs、AWS IoT Core等）ごとにバリデーション方法が異なるため、クラウド連携時に各サービスの仕様に従った形式で登録する必要がある。

| #   | カラム物理名                | カラム論理名           | データ型     | NULL     | PK  | FK  | デフォルト値      | 説明                                                                                |
| --- | --------------------------- | ---------------------- | ------------ | -------- | --- | --- | ----------------- | ----------------------------------------------------------------------------------- |
| 1   | device_id                   | デバイスID             | INT          | NOT NULL | ○   | -   | AUTO_INCREMENT    | デバイスの一意識別子（主キー、自動採番）                                            |
| 2   | device_uuid                 | デバイスUUID           | VARCHAR(128) | NOT NULL | -   | -   | -                 | クラウドに登録されるデバイスID（※1）128ビットの値でなくてもよいのでUUIDとも限らない |
| 3   | device_name                 | デバイス名             | VARCHAR(100) | NOT NULL | -   | -   | -                 | デバイスの表示名                                                                    |
| 4   | device_type_id              | デバイス種別ID         | INT          | NOT NULL | -   | ○   | -                 | デバイス種別ID（device_type_master参照）                                            |
| 5   | device_model                | モデル情報             | VARCHAR(100) | NOT NULL | -   | -   | -                 | デバイスのモデル名・型番                                                            |
| 6   | device_inventory_id         | デバイス在庫ID         | INT          | NULL     | -   | ○   | -                 | デバイス在庫ID（device_inventory_master参照）                                       |
| 7   | sim_id                      | SIMID                  | VARCHAR(20)  | NULL     | -   | -   | -                 | デバイスのSIM ID                                                                    |
| 8   | mac_address                 | MACアドレス            | VARCHAR(17)  | NULL     | -   | -   | -                 | デバイスのMACアドレス。コロン区切り形式（AA:BB:CC:DD:EE:FF）で格納                  |
| 9   | organization_id             | 組織ID                 | INT          | NULL     | -   | ○   | -                 | 所属組織ID（organization_master参照）                                               |
| 10  | software_version            | ソフトウェアバージョン | VARCHAR(100) | NULL     | -   | -   | -                 | デバイスのファームウェアバージョン                                                  |
| 11  | device_location             | 設置場所               | VARCHAR(100) | NULL     | -   | -   | -                 | デバイスの設置場所                                                                  |
| 12  | certificate_expiration_date | 証明書期限             | DATETIME     | NULL     | -   | -   | -                 | SSL証明書期限                                                                       |
| 13  | delete_flag                 | 削除フラグ             | BOOLEAN      | NOT NULL | -   | -   | FALSE             | 論理削除状態：TRUE　その他の場合：FALSE                                             |
| 14  | create_date                 | 作成日時               | DATETIME     | NOT NULL | -   | -   | CURRENT_TIMESTAMP | レコード作成日時                                                                    |
| 15  | creator                     | 作成者                 | INT          | NOT NULL | -   | -   | -                 | レコード作成者のユーザID                                                            |
| 16  | update_date                 | 更新日時               | DATETIME     | NOT NULL | -   | -   | CURRENT_TIMESTAMP | レコード最終更新日時                                                                |
| 17  | modifier                    | 更新者                 | INT          | NOT NULL | -   | -   | -                 | レコード更新者のユーザID                                                            |

**※1 device_uuidのクラウド別バリデーション:**
| クラウドサービス | 形式・制約                                                                                                 |
| ---------------- | ---------------------------------------------------------------------------------------------------------- |
| Azure IoT Hubs   | 最大128文字、ASCII 7 ビット英数字の大文字と小文字が区別される文字列、(- . % _ * ? ! ( ) , : = @ $ ')使用可 |
| AWS IoT Core     | 最大128文字、[a-zA-Z0-9:_-]使用可                                                                          |

**外部キー:**
- `device_type_id` → `device_type_master.device_type_id`
- `device_inventory_id` → `device_inventory_master.device_inventory_id`
- `organization_id` → `organization_master.organization_id`

**ビジネスルール:**
- デバイス台帳登録時、device_inventory_masterと同時にdevice_masterにもレコードを作成
- device_uuidはクラウドサービス（Azure IoT Hubs、AWS IoT Core等）で登録されるデバイスIDが格納される
- 登録時、device_model、mac_addressはdevice_inventory_master（台帳マスタ）の値と同期する
- 顧客が用意したデバイスはデバイス在庫IDが空の状態でデバイス管理画面からデバイスマスタに登録（台帳管理対象外）
- device_uuidはユニーク制約（重複登録不可）

---

## Flaskルート一覧

| No  | ルート名             | エンドポイント                                           | メソッド | 用途                               |
| --- | -------------------- | -------------------------------------------------------- | -------- | ---------------------------------- |
| 1   | デバイス台帳一覧表示 | `/admin/device-inventory`                                | GET      | 一覧・検索表示                     |
| 2   | デバイス台帳登録画面 | `/admin/device-inventory/create`                         | GET      | 登録モーダル表示                   |
| 3   | デバイス台帳登録実行 | `/admin/device-inventory/create`                         | POST     | 登録処理                           |
| 4   | デバイス台帳詳細表示 | `/admin/device-inventory/<device_inventory_uuid>`        | GET      | 詳細モーダル表示                   |
| 5   | デバイス台帳更新画面 | `/admin/device-inventory/<device_inventory_uuid>/edit`   | GET      | 更新モーダル表示                   |
| 6   | デバイス台帳更新実行 | `/admin/device-inventory/<device_inventory_uuid>/update` | POST     | 更新処理                           |
| 7   | デバイス台帳削除実行 | `/admin/device-inventory/delete`                         | POST     | 削除処理（論理削除、複数選択対応） |
| 8   | CSVエクスポート      | `/admin/device-inventory`                                | POST     | CSV出力                            |

---

## アクセス権限

### 機能別アクセス権限

| 機能             | システム保守者 | 管理者 | 販社ユーザ | サービス利用者 |
| ---------------- | -------------- | ------ | ---------- | -------------- |
| デバイス台帳一覧 | ○              | -      | -          | -              |
| デバイス台帳参照 | ○              | -      | -          | -              |
| デバイス台帳登録 | ○              | -      | -          | -              |
| デバイス台帳更新 | ○              | -      | -          | -              |
| デバイス台帳削除 | ○              | -      | -          | -              |
| CSVエクスポート  | ○              | -      | -          | -              |

**注:** デバイス台帳管理はシステム保守者（NSW内部）専用の機能です。

### 権限制御の実装

- **グローバルメニュー:** システム保守者以外には非表示
- **ルートレベル:** `@require_role(Role.SYSTEM_ADMIN)` デコレーター
- **データスコープ:** なし（システム保守者は全データにアクセス可能）

---

## 関連ドキュメント

### 機能仕様

- [UI仕様書](./ui-specification.md) - 画面レイアウト、UI要素、バリデーションルール
- [ワークフロー仕様書](./workflow-specification.md) - 処理フロー、API統合、エラーハンドリング

### 共通仕様

- [共通仕様書](../../common/common-specification.md) - HTTPステータスコード、エラーコード等
- [UI共通仕様書](../../common/ui-common-specification.md) - 共通UI仕様
- [アプリケーションDB仕様書](../../common/app-database-specification.md) - テーブル定義（device_inventory_master）

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

**作成日:** 2026-01-26
**最終更新日:** 2026-01-29
**作成者:** Claude
