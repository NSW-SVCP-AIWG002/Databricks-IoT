# デバイス台帳管理 (FR-004-5)

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
| ADM-014 | デバイス台帳登録画面 | `/admin/device-inventory/create` | 登録（モーダル） |
| ADM-015 | デバイス台帳更新画面 | `/admin/device-inventory/<device_stock_uuid>/edit` | 更新（モーダル） |
| ADM-016 | デバイス台帳参照画面 | `/admin/device-inventory/<device_stock_uuid>` | 詳細表示（モーダル） |
| ADM-017 | デバイス台帳登録確認画面 | - | 登録確認（モーダル） |
| ADM-018 | デバイス台帳更新確認画面 | - | 更新確認（モーダル） |
| ADM-019 | デバイス台帳削除確認画面 | - | 削除確認（モーダル） |
| ADM-020 | デバイス台帳登録完了画面 | - | 登録完了通知（モーダル） |
| ADM-021 | デバイス台帳更新完了画面 | - | 更新完了通知（モーダル） |
| ADM-022 | デバイス台帳削除完了画面 | - | 削除完了通知（モーダル） |

---

## データモデル

### デバイス在庫情報マスタ (device_stock_info_master)

**概要**: デバイスの在庫・配備状況を管理するテーブル

| #   | カラム物理名                   | カラム論理名       | データ型     | NULL     | PK  | FK  | デフォルト値      | 説明                                                          |
| --- | ------------------------------ | ------------------ | ------------ | -------- | --- | --- | ----------------- | ------------------------------------------------------------- |
| 1   | device_stock_id                | デバイス在庫ID     | INT          | NOT NULL | ○   | -   | AUTO_INCREMENT    | デバイス在庫ID（主キー、自動採番）                            |
| 2   | device_stock_uuid              | デバイス在庫UUID   | VARCHAR(36)  | NOT NULL | -   | -   | UUID自動生成      | デバイス在庫の外部公開用識別子（URLパスパラメータとして使用） |
| 3   | stock_status_id                | 在庫状況ID         | INT          | NOT NULL | -   | ○   | -                 | 在庫状況ID（stock_status_master参照）                         |
| 4   | purchase_date                  | 購入日             | DATETIME     | NOT NULL | -   | -   | -                 | デバイス購入日                                                |
| 5   | estimated_ship_date            | 出荷予定日         | DATETIME     | NULL     | -   | -   | -                 | デバイス出荷予定日                                            |
| 6   | ship_date                      | 出荷日             | DATETIME     | NULL     | -   | -   | -                 | デバイス出荷日                                                |
| 7   | manufacturer_warranty_end_date | メーカー保証終了日 | DATETIME     | NOT NULL | -   | -   | -                 | メーカー保証の終了日                                          |
| 8   | vendor_warranty_end_date       | ベンダー保証終了日 | DATETIME     | NOT NULL | -   | -   | -                 | ベンダー保証の終了日                                          |
| 9   | stock_location                 | 在庫場所           | VARCHAR(100) | NOT NULL | -   | -   | -                 | 現在の在庫保管場所                                            |
| 10  | create_date                    | 作成日時           | DATETIME     | NOT NULL | -   | -   | CURRENT_TIMESTAMP | レコード作成日時                                              |
| 11  | creator                        | 作成者             | INT          | NOT NULL | -   | -   | -                 | レコード作成者のユーザID                                      |
| 12  | update_date                    | 更新日時           | DATETIME     | NOT NULL | -   | -   | CURRENT_TIMESTAMP | レコード最終更新日時                                          |
| 13  | modifier                       | 更新者             | INT          | NOT NULL | -   | -   | -                 | レコード更新者のユーザID                                      |
| 14  | delete_flag                    | 削除フラグ         | BOOLEAN      | NOT NULL | -   | -   | FALSE             | 論理削除状態：TRUE　その他の場合：FALSE                       |

**外部キー:**
- `stock_status_id` → `stock_status_master.stock_status_id`

**ビジネスルール:**
- device_stock_idは1デバイスにつき1レコード（1:1関係）
- stock_status_idで在庫状態を管理
- デバイス情報（device_id, device_name等）はdevice_masterテーブルからdevice_stock_idで参照

---

### 在庫状況マスタ (stock_status_master)

**概要**: デバイス在庫状況のステータスを管理するマスタテーブル

| #   | カラム物理名      | カラム論理名 | データ型     | NULL     | PK  | FK  | デフォルト値      | 説明                                    |
| --- | ----------------- | ------------ | ------------ | -------- | --- | --- | ----------------- | --------------------------------------- |
| 1   | stock_status_id   | 在庫状況ID   | INT          | NOT NULL | ○   | -   | AUTO_INCREMENT    | 自動採番、在庫状況の一意識別子          |
| 2   | stock_status_name | 在庫状況名   | VARCHAR(100) | NOT NULL | -   | -   | -                 | 在庫状況の表示名                        |
| 3   | create_date       | 作成日時     | DATETIME     | NOT NULL | -   | -   | CURRENT_TIMESTAMP | レコード作成日時                        |
| 4   | creator           | 作成者       | INT          | NOT NULL | -   | -   | -                 | レコード作成者のユーザID                |
| 5   | update_date       | 更新日時     | DATETIME     | NOT NULL | -   | -   | CURRENT_TIMESTAMP | レコード最終更新日時                    |
| 6   | modifier          | 更新者       | INT          | NOT NULL | -   | -   | -                 | レコード更新者のユーザID                |
| 7   | delete_flag       | 削除フラグ   | BOOLEAN      | NOT NULL | -   | -   | FALSE             | 論理削除状態：TRUE　その他の場合：FALSE |

**初期データ:**
| stock_status_id | stock_status_name | 説明 |
| --------------- | ----------------- | ---- |
| 1               | 在庫中            | 倉庫に保管中 |
| 2               | 出荷済み          | 顧客へ出荷完了 |
| 3               | 修理中            | 修理・メンテナンス中 |
| 4               | 廃棄予定          | 廃棄待ち |
| 5               | 廃棄済み          | 廃棄完了 |

---

## Flaskルート一覧

| No | ルート名 | エンドポイント | メソッド | 用途 |
|----|---------|---------------|---------|------|
| 1 | デバイス台帳一覧表示 | `/admin/device-inventory` | GET | 一覧・検索表示 |
| 2 | デバイス台帳登録画面 | `/admin/device-inventory/create` | GET | 登録モーダル表示 |
| 3 | デバイス台帳登録実行 | `/admin/device-inventory/create` | POST | 登録処理 |
| 4 | デバイス台帳詳細表示 | `/admin/device-inventory/<device_stock_uuid>` | GET | 詳細モーダル表示 |
| 5 | デバイス台帳更新画面 | `/admin/device-inventory/<device_stock_uuid>/edit` | GET | 更新モーダル表示 |
| 6 | デバイス台帳更新実行 | `/admin/device-inventory/<device_stock_uuid>/update` | POST | 更新処理 |
| 7 | デバイス台帳削除実行 | `/admin/device-inventory/delete` | POST | 削除処理（論理削除、複数選択対応） |
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
- [アプリケーションDB仕様書](../../common/app-database-specification.md) - テーブル定義（device_stock_info_master）

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
