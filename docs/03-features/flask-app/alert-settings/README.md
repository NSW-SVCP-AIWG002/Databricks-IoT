# アラート設定管理機能

## 📑 目次

- [機能概要](#機能概要)
- [データモデル](#データモデル)
- [Flaskルート一覧](#flaskルート一覧)
- [関連ドキュメント](#関連ドキュメント)

---

## 機能概要

### 基本情報

| 項目 | 内容 |
|------|------|
| 機能ID | FR-004-3 |
| 機能名 | アラート設定管理 |
| カテゴリ | マスタ管理機能（Flaskアプリケーション） |
| Blueprint | `alert_settings_bp` |
| URL Prefix | `/alert/alert-setting` |

### 機能説明

アラート設定管理機能は、IoTデバイスから収集されるセンサーデータに対する異常検出条件を設定・管理する機能です。設定された条件に基づき、LDPパイプライン（シルバー層）でリアルタイムにアラート判定が実行されます。

### サブ機能一覧

| 機能ID | 機能名 | 画面ID | 概要 |
|--------|--------|--------|------|
| FR-004-3-1 | アラート設定一覧・検索 | ALT-001 | アラート設定の一覧表示、検索、削除 |
| FR-004-3-2 | アラート設定参照 | ALT-004 | アラート設定の詳細情報表示（モーダル） |
| FR-004-3-3 | アラート設定登録 | ALT-002 | アラート設定の新規登録（モーダル） |
| FR-004-3-4 | アラート設定編集 | ALT-003 | アラート設定の更新（モーダル） |
| FR-004-3-5 | アラート設定削除 | ALT-001 | アラート設定の論理削除（一覧画面から実行） |

### アクセス権限

| 機能 | システム保守者 | 管理者 | 販社ユーザ | サービス利用者 |
|------|---------------|--------|-----------|---------------|
| アラート設定一覧 | ◎ | ◎ | ○ | ○ |
| アラート設定参照 | ◎ | ◎ | ○ | ○ |
| アラート設定登録 | ◎ | ◎ | ○ | ○ |
| アラート設定更新 | ◎ | ◎ | ○ | ○ |
| アラート設定削除 | ◎ | ◎ | ○ | ○ |
| CSVエクスポート | ◎ | ◎ | ○ | - |

**凡例**:
- ◎: 制限なく利用可能（全データアクセス可能）
- ○: 制限下で利用可（自社もしくは傘下組織のデータにアクセス可能）
- -: 利用不可

---

## データモデル

### AlertSetting（アラート設定）

| No | 項目名（論理）             | 項目名（物理）                       | データ型     | 必須 | デフォルト値      | 説明                                                       |
|----|---------------------------|-------------------------------------|--------------|------|-------------------|-----------------------------------------------------------|
| 1  | アラートID                 | alert_id                            | INT          | ○    | AUTO_INCREMENT    | PK、自動採番                                               |
| 2  | アラートUUID               | alert_uuid                          | VARCHAR(36)  | ○    | UUID自動生成       | アラート設定の外部公開用識別子。URLパスパラメータとして使用し、詳細表示・編集・削除時にリソースを特定する。 |
| 3  | アラート名                 | alert_name                          | VARCHAR(100) | ○    | -                 | アラートの名称                                             |
| 4  | デバイスID                 | device_id                           | INT          | ○    | -                 | FK、対象デバイス                                           |
| 5  | アラート発生条件_測定項目ID   | alert_conditions_measurement_item_id  | INT        | ○    | -                 | FK、measurement_item_masterテーブルを参照。異常検出条件式の測定項目のIDを格納           |
| 6  | アラート発生条件_比較演算子 | alert_conditions_operator           | VARCHAR(10)  | ○    | -                 | 異常検出条件式の比較演算子（>、<、>=、<=、=、!=）を格納 |
| 7  | アラート発生条件_閾値       | alert_conditions_threshold          | DOUBLE        | ○    | -                 | 異常検出条件式の閾値（20、30などの数値）を格納             |
| 8  | アラート復旧条件_測定項目ID   | alert_recovery_conditions_measurement_item_id     | INT | ○    | -                 | FK、measurement_item_masterテーブルを参照。正常復帰条件式の測定項目のIDを格納           |
| 9  | アラート復旧条件_比較演算子 | alert_recovery_conditions_operator  | VARCHAR(10)  | ○    | -                 | 正常復帰条件式の比較演算子（>、<、>=、<=、=、!=）を格納 |
| 10 | アラート復旧条件_閾値       | alert_recovery_conditions_threshold | DOUBLE        | ○    | -                 | 正常復帰条件式の閾値（20、30などの数値）を格納             |
| 11 | 判定時間                   | judgment_time                       | INT          | ○    | 5                 | 判定間隔（分）                                             |
| 12 | アラートレベルID           | alert_level_id                      | INT          | ○    | -                 | FK、alert_level_masterテーブルを参照                       |
| 13 | アラート通知フラグ         | alert_notification_flag             | BOOLEAN      | ○    | TRUE              | アラート通知 有効/無効　発生したアラートをダッシュボード上に表示するかを管理する |
| 14 | メール送信フラグ           | alert_email_flag                    | BOOLEAN      | ○    | TRUE              | メール送信 有効/無効　アラートが発生した旨を通知するメールを送信するかを管理する |
| 15 | 作成日時                   | create_date                         | DATETIME     | ○    | CURRENT_TIMESTAMP | 作成日時                                                   |
| 16 | 作成者                     | creator                             | INT          | ○    | -                 | 作成者ユーザーID                                           |
| 17 | 更新日時                   | update_date                         | DATETIME     | ○    | CURRENT_TIMESTAMP | 更新日時                                                   |
| 18 | 更新者                     | modifier                            | INT          | ○    | -                 | 更新者ユーザーID                                           |
| 19 | 削除フラグ                 | delete_flag                         | BOOLEAN      | ○    | FALSE             | 論理削除用フラグ                                           |

### MeasurementItem（測定項目）

| No | 項目名（論理） | 項目名（物理）        | データ型    | 必須 | デフォルト値      | 説明                                           |
|----|----------------|----------------------|-------------|------|-------------------|------------------------------------------------|
| 1  | 測定項目ID     | measurement_item_id  | INT         | ○    | AUTO_INCREMENT    | PK、自動採番                                   |
| 2  | 測定項目名     | measurement_item_name| VARCHAR(50) | ○    | -                 | センサーで読み取る、機器に関する測定項目の名前 |
| 3  | 作成日時       | create_date          | DATETIME    | ○    | CURRENT_TIMESTAMP | 作成日時                                       |
| 4  | 作成者         | creator              | INT         | ○    | -                 | 作成者ユーザーID                               |
| 5  | 更新日時       | update_date          | DATETIME    | ○    | CURRENT_TIMESTAMP | 更新日時                                       |
| 6  | 更新者         | modifier             | INT         | ○    | -                 | 更新者ユーザーID                               |
| 7  | 削除フラグ     | delete_flag          | BOOLEAN     | ○    | FALSE             | 論理削除用フラグ                               |

測定項目マスタには以下のデータを格納する

| measurement_item_id | measurement_item_name          |
|---------------------|--------------------------------|
| 1                   | 共通外気温度[℃]                |
| 2                   | 第1冷凍設定温度[℃]            |
| 3                   | 第1冷凍庫内センサー温度[℃]    |
| 4                   | 第1冷凍表示温度[℃]            |
| 5                   | 第1冷凍DF温度[℃]              |
| 6                   | 第1冷凍凝縮温度[℃]            |
| 7                   | 第1冷凍微調整後庫内温度[℃]    |
| 8                   | 第2冷凍設定温度[℃]            |
| 9                   | 第2冷凍庫内センサー温度[℃]    |
| 10                  | 第2冷凍表示温度[℃]            |
| 11                  | 第2冷凍DF温度[℃]              |
| 12                  | 第2冷凍凝縮温度[℃]            |
| 13                  | 第2冷凍微調整後庫内温度[℃]    |
| 14                  | 第1冷凍圧縮機回転数[rpm]      |
| 15                  | 第2冷凍圧縮機回転数[rpm]      |
| 16                  | 第1ファンモータ回転数[rpm]    |
| 17                  | 第2ファンモータ回転数[rpm]    |
| 18                  | 第3ファンモータ回転数[rpm]    |
| 19                  | 第4ファンモータ回転数[rpm]    |
| 20                  | 第5ファンモータ回転数[rpm]    |
| 21                  | 防露ヒータ出力(1)[%]          |
| 22                  | 防露ヒータ出力(2)[%]          |

### AlertLevel（アラートレベル）

| No | 項目名（論理）   | 項目名（物理）   | データ型    | 必須 | デフォルト値      | 説明                       |
|----|------------------|------------------|-------------|------|-------------------|----------------------------|
| 1  | アラートレベルID | alert_level_id   | INT         | ○    | AUTO_INCREMENT    | PK、自動採番               |
| 2  | アラートレベル名 | alert_level_name | VARCHAR(100) | ○    | -                 | アラートの重要度レベル名称 |
| 3  | 作成日時         | create_date      | DATETIME    | ○    | CURRENT_TIMESTAMP | 作成日時                   |
| 4  | 作成者           | creator          | INT         | ○    | -                 | 作成者ユーザーID           |
| 5  | 更新日時         | update_date      | DATETIME    | ○    | CURRENT_TIMESTAMP | 更新日時                   |
| 6  | 更新者           | modifier         | INT         | ○    | -                 | 更新者ユーザーID           |
| 7  | 削除フラグ       | delete_flag      | BOOLEAN     | ○    | FALSE             | 論理削除用フラグ           |

アラートレベルマスタには以下のデータを格納する

| alert_level_id | alert_level_name |
|----------------|------------------|
| 1              | Critical         |
| 2              | Warning          |
| 3              | Info             |

### 比較演算子（設定ファイル定義）

比較演算子の選択肢は、以下の理由によりDBテーブルではなく設定ファイル（`config/constants.py`）で定義する。

**設定ファイルで管理する理由**:
- 比較演算子は固定値であり、運用中に変更されることがない
- DBアクセスのオーバーヘッドを回避し、パフォーマンスを向上させる
- シルバー層のアラート判定ロジックとの整合性を保つ（コード変更時に両方を同時に更新できる）

**定義内容**:

| value | label              |
|-------|--------------------|
| >     | より大きい (>)     |
| <     | より小さい (<)     |
| >=    | 以上 (>=)          |
| <=    | 以下 (<=)          |
| =     | 等しい (=)         |
| !=    | 等しくない (!=)    |

**実装例**:
```python
# config/constants.py
COMPARISON_OPERATORS = [
    {"value": ">",  "label": "より大きい (>)"},
    {"value": "<",  "label": "より小さい (<)"},
    {"value": ">=", "label": "以上 (>=)"},
    {"value": "<=", "label": "以下 (<=)"},
    {"value": "=",  "label": "等しい (=)"},
    {"value": "!=", "label": "等しくない (!=)"},
]
```

### 判定時間（設定ファイル定義）

判定時間の選択肢は、以下の理由によりDBテーブルではなく設定ファイル（`config/constants.py`）で定義する。

**設定ファイルで管理する理由**:
- 判定時間は固定値であり、運用中に変更されることがない
- DBアクセスのオーバーヘッドを回避し、パフォーマンスを向上させる
- シルバー層のアラート判定ロジックとの整合性を保つ（コード変更時に両方を同時に更新できる）

**定義内容**:

| value | label    |
|-------|----------|
| 1     | 1分      |
| 5     | 5分      |
| 10    | 10分     |
| 15    | 15分     |
| 30    | 30分     |
| 60    | 60分     |

**実装例**:
```python
# config/constants.py
JUDGMENT_TIMES = [
    {"value": 1,  "label": "1分"},
    {"value": 5,  "label": "5分"},
    {"value": 10, "label": "10分"},
    {"value": 15, "label": "15分"},
    {"value": 30, "label": "30分"},
    {"value": 60, "label": "60分"},
]
```

---

## Flaskルート一覧

### アラート設定一覧・検索

| No | ルート名 | エンドポイント | メソッド | 用途 | レスポンス形式 |
|----|---------|---------------|---------|------|---------------|
| 1 | アラート設定一覧表示 | `/alert/alert-setting` | GET | アラート設定一覧・検索 | HTML |

**クエリパラメータ**:
- `alert_name`: アラート名検索（アラート名）
- `organization_name`: 組織名
- `device_name`: デバイス名
- `alert_level_id`: アラートレベルID
- `alert_notification_flag`: アラート通知フラグ
- `alert_email_flag`: メール送信フラグ
- `page`: ページ番号（デフォルト: 1）
- `per_page`: 1ページあたりの件数（デフォルト: 25）
- `sort_by`: ソートフィールド（デフォルト: alert_id）
- `order`: ソート順（デフォルト: asc）

### アラート設定登録

| No | ルート名 | エンドポイント | メソッド | 用途 | レスポンス形式 |
|----|---------|---------------|---------|------|---------------|
| 2 | アラート設定登録フォーム表示 | `/alert/alert-setting/create` | GET | 登録フォーム表示（モーダル用データ取得） | HTML |
| 3 | アラート設定登録実行 | `/alert/alert-setting/create` | POST | アラート設定登録処理 | リダイレクト (302) |

**POST リクエストボディ**:
```json
{
  "alert_name": "温度異常アラート",
  "device_id": 1,
  "alert_conditions_measurement_item_id": 1,
  "alert_conditions_operator": ">",
  "alert_conditions_threshold": 30,
  "alert_recovery_conditions_measurement_item_id": 1,
  "alert_recovery_conditions_operator": "<=",
  "alert_recovery_conditions_threshold": 30,
  "judgment_time": 5,
  "alert_level_id": 1,
  "alert_notification_flag": true,
  "alert_email_flag": true
}
```

### アラート設定更新

| No | ルート名 | エンドポイント | メソッド | 用途 | レスポンス形式 |
|----|---------|---------------|---------|------|---------------|
| 4 | アラート設定更新フォーム表示 | `/alert/alert-setting/<alert_uuid>/edit` | GET | 更新フォーム表示（モーダル用データ取得） | HTML |
| 5 | アラート設定更新実行 | `/alert/alert-setting/<alert_uuid>/update` | POST | アラート設定更新処理 | リダイレクト (302) |

**POST リクエストボディ**: 登録と同様

### アラート設定参照

| No | ルート名 | エンドポイント | メソッド | 用途 | レスポンス形式 |
|----|---------|---------------|---------|------|---------------|
| 6 | アラート設定詳細表示 | `/alert/alert-setting/<alert_uuid>` | GET | アラート設定詳細情報表示 | HTML |

### アラート設定削除

| No | ルート名 | エンドポイント | メソッド | 用途 | レスポンス形式 |
|----|---------|---------------|---------|------|---------------|
| 7 | アラート設定削除実行 | `/alert/alert-setting/<alert_uuid>/delete` | POST | アラート設定削除処理（論理削除） | リダイレクト (302) |

**注**: HTMLフォームの制約により、DELETEメソッドではなくPOSTメソッドを使用します。

### CSVエクスポート

| No | ルート名 | エンドポイント | メソッド | 用途 | レスポンス形式 |
|----|---------|---------------|---------|------|---------------|
| 8 | CSVエクスポート | `/alert/alert-setting?export=csv` | GET | CSVエクスポート | CSV |

**レスポンス**:
- Content-Type: `text/csv; charset=utf-8-sig`
- ファイル名: `alert-settings_{YYYYMMDD_HHmmss}.csv`
- エクスポート対象: 一覧画面の絞り込み条件が適用された状態のデータ

---

## 関連ドキュメント

### 機能設計・仕様

- [UI仕様書](./ui-specification.md) - アラート設定管理画面のUI仕様
- [ワークフロー仕様書](./workflow-specification.md) - ワークフロー・処理フロー詳細
- [共通仕様書](../../03-features/common/common-specification.md) - HTTPステータスコード、エラーコード等
- [UI共通仕様書](../../03-features/common/ui-common-specification.md) - すべての画面に共通するUI仕様

### 要件定義

- [機能要件定義書](../../02-requirements/functional-requirements.md) - FR-004-3
- [非機能要件定義書](../../02-requirements/non-functional-requirements.md) - パフォーマンス、セキュリティ要件
- [技術要件定義書](../../02-requirements/technical-requirements.md) - 技術スタック、Flask設計

### アーキテクチャ設計

- [バックエンド設計](../../01-architecture/backend.md) - Flask Blueprint構成
- [データベース設計](../../01-architecture/database.md) - テーブル定義、インデックス設計
- [フロントエンド設計](../../01-architecture/frontend.md) - Flask + Jinja2設計

### 関連機能

- [デバイス管理機能](../devices/README.md) - アラート設定の対象デバイス管理
- [アラート履歴機能](../alert-history/README.md) - 発生したアラートの履歴表示
- [メール通知設定管理](../mail-settings/README.md) - メール通知の詳細設定
- [シルバー層処理](../../ldp-pipeline/silver-layer/README.md) - アラート判定実行処理

---

## 編集履歴

| 日付 | バージョン | 編集者 | 変更内容 |
|------|------------|--------|----------|
| 2025-12-10 | 1.0 | Claude | 初版作成（アラート設定管理機能の概要、データモデル、Flaskルート一覧を定義する） |

---

**このドキュメントは、実装前に必ずレビューを受けてください。**
