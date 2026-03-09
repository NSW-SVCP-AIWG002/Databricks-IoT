# 業種別ダッシュボード機能（冷蔵冷凍庫）

## 📑 目次

- [業種別ダッシュボード機能（冷蔵冷凍庫）](#業種別ダッシュボード機能冷蔵冷凍庫)
  - [📑 目次](#-目次)
  - [概要](#概要)
  - [機能一覧](#機能一覧)
  - [画面一覧](#画面一覧)
  - [データモデル](#データモデル)
    - [センサーデータ (silver\_sensor\_data)](#センサーデータ-silver_sensor_data)
    - [センサーデータビュー（sensor\_data\_view）](#センサーデータビューsensor_data_view)
  - [Flaskルート一覧](#flaskルート一覧)
  - [アクセス権限](#アクセス権限)
  - [実装ステータス](#実装ステータス)
  - [関連ドキュメント](#関連ドキュメント)
    - [仕様書](#仕様書)
    - [共通仕様](#共通仕様)
    - [関連機能](#関連機能)
    - [要件定義](#要件定義)

---

## 概要

業種別ダッシュボード画面は、Databricks IoTシステムにおけるIoTデータの可視化と分析を提供する機能です。ログイン後のホーム画面として機能し、業種に特化したUI・UXを構築します。

**機能ID:** FR-006

**特徴**:
- **リアルタイムデータ表示**: センサーデータ、デバイスステータス一覧の表示
- **履歴データ分析**: 時系列グラフ、期間指定による絞り込み
- **最新アラート情報**: 直近のアラート通知を表示
- **データスコープ制限**: すべてのユーザーに所属組織配下のデータのみアクセス可能なフィルタが適用される

**グラフ描画ライブラリ**
- 時系列グラフはApache EChartsを使用して描画

---

## 機能一覧

| 機能ID | 機能名 | 概要 |
|--------|--------|------|
| FR-006-1 | 店舗モニタリング表示 | アラート一覧・デバイス一覧・センサー情報表示 |
| FR-006-2 | デバイス詳細表示 | デバイス情報表示・アラート一覧・時系列グラフ |

---

## 画面一覧

| 画面ID | 画面名 | スラッグ | 表示方式 | 概要 |
|--------|--------|---------|---------|------|
| IDS-001 | 店舗モニタリング画面 | `analysis/industry-dashboard/store-monitoring` | 画面 | ログイン後の初期画面（グローバルメニューからも遷移可能）、店舗のデバイス一覧やアラート一覧を表示 |
| IDS-002 | デバイス詳細画面 | `analysis/industry-dashboard/device-details/<device_uuid>` | 画面 | 店舗モニタリング画面から遷移、デバイスのセンサーデータやアラート履歴を表示 |

---

## データモデル

### センサーデータ (silver_sensor_data)

| カラム名 | 論理名 | データ型 | 必須 | 備考 |
|----------|-------|---------|------|------|
| device_id | デバイスID | INT | ○ | システム内でのIoTデバイスの一意識別子 |
| organization_id | 組織ID | INT | ○ | 所属組織ID |
| event_timestamp | イベント発生日時 | TIMESTAMP | ○ | センサーがデータを取得した日時（ダッシュボード内グラフ横軸表示項目） |
| event_date | イベント発生日 | DATE | ○ | センサーがデータを取得した日（クラスタリングキー） |
| external_temp | 外気温度 | DOUBLE | - | 冷蔵冷凍庫の外気温度[℃]（ダッシュボード内グラフ縦軸表示項目） |
| set_temp_freezer_1 | 第1冷凍 設定温度 | DOUBLE | - | 第1冷凍庫の設定温度[℃]（ダッシュボード内グラフ縦軸表示項目） |
| internal_sensor_temp_freezer_1 | 第1冷凍 庫内センサー温度 | DOUBLE | - | 第1冷凍庫の庫内センサー温度[℃]（ダッシュボード内グラフ縦軸表示項目） |
| internal_temp_freezer_1 | 第1冷凍 庫内温度 | DOUBLE | - | 第1冷凍庫の庫内温度[℃]（ダッシュボード内グラフ縦軸表示項目） |
| df_temp_freezer_1  | 第1冷凍 DF温度 | DOUBLE | - | 第1冷凍庫のDF温度[℃]（ダッシュボード内グラフ縦軸表示項目） |
| condensing_temp_freezer_1 | 第1冷凍 凝縮温度 | DOUBLE | - | 第1冷凍庫の凝縮温度[℃]（ダッシュボード内グラフ縦軸表示項目） |
| adjusted_internal_temp_freezer_1 | 第1冷凍 微調整後庫内温度 | DOUBLE | - | 第1冷凍庫の微調整後庫内温度[℃]（ダッシュボード内グラフ縦軸表示項目） |
| set_temp_freezer_2 | 第2冷凍 設定温度 | DOUBLE | - | 第2冷凍庫の設定温度[℃]（ダッシュボード内グラフ縦軸表示項目） |
| internal_sensor_temp_freezer_2 | 第2冷凍 庫内センサー温度 | DOUBLE | - | 第2冷凍庫の庫内センサー温度[℃]（ダッシュボード内グラフ縦軸表示項目） |
| internal_temp_freezer_2 | 第2冷凍 庫内温度 | DOUBLE | - | 第2冷凍庫の庫内温度[℃]（ダッシュボード内グラフ縦軸表示項目） |
| df_temp_freezer_2 | 第2冷凍 DF温度 | DOUBLE | - | 第2冷凍庫のDF温度[℃]（ダッシュボード内グラフ縦軸表示項目） |
| condensing_temp_freezer_2 | 第2冷凍 凝縮温度 | DOUBLE | - | 第2冷凍庫の凝縮温度[℃]（ダッシュボード内グラフ縦軸表示項目） |
| adjusted_internal_temp_freezer_2 | 第2冷凍 微調整後庫内温度 | DOUBLE | - | 第2冷凍庫の微調整後庫内温度[℃]（ダッシュボード内グラフ縦軸表示項目） |
| compressor_freezer_1 | 第1冷凍 圧縮機 | DOUBLE | - | 第1冷凍庫の圧縮機の回転数[rpm]（ダッシュボード内グラフ縦軸表示項目） |
| compressor_freezer_2 | 第2冷凍 圧縮機 | DOUBLE | - | 第2冷凍庫の圧縮機の回転数[rpm]（ダッシュボード内グラフ縦軸表示項目） |
| fan_motor_1 | 第1ファンモータ | DOUBLE | - | 第1ファンモータの回転数[rpm]（ダッシュボード内グラフ縦軸表示項目）|
| fan_motor_2 | 第2ファンモータ | DOUBLE | - | 第2ファンモータの回転数[rpm]（ダッシュボード内グラフ縦軸表示項目）|
| fan_motor_3 | 第3ファンモータ | DOUBLE | - | 第3ファンモータの回転数[rpm]（ダッシュボード内グラフ縦軸表示項目）|
| fan_motor_4 | 第4ファンモータ | DOUBLE | - | 第4ファンモータの回転数[rpm]（ダッシュボード内グラフ縦軸表示項目）|
| fan_motor_5 | 第5ファンモータ | DOUBLE | - | 第5ファンモータの回転数[rpm]（ダッシュボード内グラフ縦軸表示項目）|
| defrost_heater_output_1 | 防露ヒータ出力(1) | DOUBLE | - | 防露ヒータ(1)の出力[％]（ダッシュボード内グラフ縦軸表示項目）|
| defrost_heater_output_2 | 防露ヒータ出力(2) | DOUBLE | - | 防露ヒータ(2)の出力[％]（ダッシュボード内グラフ縦軸表示項目）|
| sensor_data_json | センサーデータ本体 | VARIANT | ○ | 構造化以前のJSON形式のセンサーデータ |
| create_time | 作成日時 | TIMESTAMP | ○ | レコード作成日時 |

**クラスタリングキー**: `event_date`, `device_id`

### センサーデータビュー（sensor_data_view）

```sql
CREATE OR REPLACE VIEW iot_catalog.views.sensor_data_view AS
SELECT
    device_id
    , organization_id
    , event_timestamp 
    , event_date
    , external_temp
    , set_temp_freezer_1
    , internal_sensor_temp_freezer_1
    , internal_temp_freezer_1
    , df_temp_freezer_1
    , condensing_temp_freezer_1 
    , adjusted_internal_temp_freezer_1
    , set_temp_freezer_2
    , internal_sensor_temp_freezer_2
    , internal_temp_freezer_2
    , df_temp_freezer_2
    , condensing_temp_freezer_2
    , adjusted_internal_temp_freezer_2
    , compressor_freezer_1
    , compressor_freezer_2
    , fan_motor_1
    , fan_motor_2
    , fan_motor_3
    , fan_motor_4
    , fan_motor_5
    , defrost_heater_output_1
    , defrost_heater_output_2
FROM iot_catalog.silver.silver_sensor_data sl
;
```
**シルバー層のセンサーデータテーブルからの除外カラム**:
- `sensor_data_json`: 構造化済みカラムで十分なため除外
- `create_time`: ダッシュボード表示に不要なため除外

**注**: 詳細なテーブル定義は [Unity Catalog データベース設計書](../../common/unity-catalog-database-specification.md) を参照してください。

---

## Flaskルート一覧

| No | ルート名 | エンドポイント | メソッド | 用途 | レスポンス形式 |
|----|---------|---------------|---------|------|---------------|
| 1 | 店舗モニタリング初期表示 | `analysis/industry-dashboard/store-monitoring` | GET | 店舗モニタリングの初期表示 | HTML |
| 2 | 店舗モニタリング検索 | `analysis/industry-dashboard/store-monitoring` | POST | 店舗モニタリングの検索 | HTML |
| 3 | センサー情報表示 | `analysis/industry-dashboard/store-monitoring/<device_uuid>` | GET | センサー情報表示 | HTML |
| 4 | デバイス詳細初期表示 | `analysis/industry-dashboard/device-details/<device_uuid>` | GET | デバイス詳細の初期表示 | HTML |
| 5 | デバイス詳細検索 | `analysis/industry-dashboard/device-details/<device_uuid>` | POST | デバイス詳細の検索 | HTML | |
| 6 | CSVエクスポート | `analysis/industry-dashboard/device-details/<device_uuid>?export=csv` | GET | センサー情報CSVダウンロード | CSV |

---

## アクセス権限

| 機能 | システム保守者 | 管理者 | 販社ユーザ | サービス利用者 |
|------|---------------|--------|-----------|---------------|
| 店舗モニタリング | ○ | ○ | ○ | ○ |
| センサー情報表示 | ○ | ○ | ○ | ○ |
| デバイス詳細 | ○ | ○ | ○ | ○ |
| CSVエクスポート | ○ | ○ | ○ | ○ |

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
| 店舗モニタリング表示 | 完了 | 完了 | 未着手 | 未着手 | 設計中 |
| センサー情報表示 | 完了 | 完了 | 未着手 | 未着手 | 設計中 |
| デバイス詳細 | 完了 | 完了 | 未着手 | 未着手 | 設計中 |
| CSVエクスポート | 完了 | 完了 | 未着手 | 未着手 | 設計中 |

---

## 関連ドキュメント

### 仕様書

- [UI仕様書](./ui-specification.md) - 画面レイアウト・UI要素・iframe仕様
- [ワークフロー仕様書](./workflow-specification.md) - 処理フロー・Databricks連携・エラーハンドリング

### 共通仕様

- [UI共通仕様書](../../common/ui-common-specification.md) - すべての画面に共通するUI仕様
- [共通仕様書](../../common/common-specification.md) - HTTPステータスコード、エラーコード等

### 関連機能

- [アラート設定管理](../alert-settings/) - アラート設定のCRUD機能
- [アラート履歴](../alert-history/) - アラート発生履歴の参照
- [デバイス管理](../devices/) - デバイス情報の管理

### 要件定義

- [機能要件定義書](../../../02-requirements/functional-requirements.md) - FR-006
- [非機能要件定義書](../../../02-requirements/non-functional-requirements.md) - NFR-PERF-003, NFR-SEC-007
- [技術要件定義書](../../../02-requirements/technical-requirements.md) - TR-DB-001

---

**このREADMEは、ダッシュボード機能の全体像を示す概要ドキュメントです。詳細な仕様は各仕様書を参照してください。**
