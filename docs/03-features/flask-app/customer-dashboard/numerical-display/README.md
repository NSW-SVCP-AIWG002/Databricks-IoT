# 顧客作成ダッシュボード数値表示ガジェット

## 📑 目次

- [顧客作成ダッシュボード数値表示ガジェット](#顧客作成ダッシュボード数値表示ガジェット)
  - [📑 目次](#-目次)
  - [概要](#概要)
  - [機能一覧](#機能一覧)
  - [画面一覧](#画面一覧)
  - [データソース](#データソース)
    - [シルバー層（最新値表示）](#シルバー層最新値表示)
  - [対象センサー項目](#対象センサー項目)
  - [Flaskルート一覧](#flaskルート一覧)
  - [アクセス権限](#アクセス権限)
  - [関連ドキュメント](#関連ドキュメント)
    - [仕様書](#仕様書)
    - [共通仕様](#共通仕様)
    - [顧客作成ダッシュボード画面共通仕様](#顧客作成ダッシュボード画面共通仕様)
    - [データベース](#データベース)

**重要:** 顧客作成ダッシュボード画面の共通仕様は [共通README](../common/README.md) を参照してください。

---

## 概要

IoTデバイスから収集したセンサーデータの最新値を最大2項目の数値ラベルとして表示するガジェットです。顧客作成ダッシュボード画面に埋め込んで使用します。

---

## 機能一覧

| 機能ID | 機能名 | 概要 |
|--------|--------|------|
| FR-006-8 | ガジェット表示 | 選択したデバイス・測定項目の最新値を数値ラベルで表示 |
| FR-006-9 | ガジェット登録 | 数値表示ガジェットの新規登録 |

---

## 画面一覧

| 画面ID | 画面名 | スラッグ | 表示方式 | 概要 |
|--------|--------|---------|---------|------|
| CDS-001 | 顧客作成ダッシュボード表示画面 | `/analysis/customer-dashboard` | 画面 | 顧客作成ダッシュボード画面に数値表示ガジェットを埋め込んで表示 |
| CDS-011 | 数値表示ガジェット登録モーダル | `/analysis/customer-dashboard/gadgets/numerical-display/create` | モーダル | 数値表示ガジェットを登録 |

---

## データソース

### シルバー層（最新値表示）

- **テーブル**: `silver_sensor_data`
- **用途**: 指定デバイス・測定項目の最新値取得
- **取得方法**: `event_timestamp` 降順で `LIMIT 1`
- **データスコープ**: `organization_closure` による組織階層フィルタリングを適用

---

## 対象センサー項目

`measurement_item_master` で管理される項目を選択可能。

| measurement_item_id | 表示名 | 単位 | silver_sensor_data カラム名 |
|---------------------|--------|------|----------------------------|
| 1 | 外気温度 | ℃ | `external_temp` |
| 2 | 第1冷凍 設定温度 | ℃ | `set_temp_freezer_1` |
| 3 | 第1冷凍 庫内センサー温度 | ℃ | `internal_sensor_temp_freezer_1` |
| 4 | 第1冷凍 表示温度 | ℃ | `internal_temp_freezer_1` |
| 5 | 第1冷凍 DF温度 | ℃ | `df_temp_freezer_1` |
| 6 | 第1冷凍 凝縮温度 | ℃ | `condensing_temp_freezer_1` |
| 7 | 第1冷凍 微調整後庫内温度 | ℃ | `adjusted_internal_temp_freezer_1` |
| 8 | 第2冷凍 設定温度 | ℃ | `set_temp_freezer_2` |
| 9 | 第2冷凍 庫内センサー温度 | ℃ | `internal_sensor_temp_freezer_2` |
| 10 | 第2冷凍 表示温度 | ℃ | `internal_temp_freezer_2` |
| 11 | 第2冷凍 DF温度 | ℃ | `df_temp_freezer_2` |
| 12 | 第2冷凍 凝縮温度 | ℃ | `condensing_temp_freezer_2` |
| 13 | 第2冷凍 微調整後庫内温度 | ℃ | `adjusted_internal_temp_freezer_2` |
| 14 | 第1冷凍 圧縮機 | rpm | `compressor_freezer_1` |
| 15 | 第2冷凍 圧縮機 | rpm | `compressor_freezer_2` |
| 16 | 第1ファンモータ回転数 | rpm | `fan_motor_1` |
| 17 | 第2ファンモータ回転数 | rpm | `fan_motor_2` |
| 18 | 第3ファンモータ回転数 | rpm | `fan_motor_3` |
| 19 | 第4ファンモータ回転数 | rpm | `fan_motor_4` |
| 20 | 第5ファンモータ回転数 | rpm | `fan_motor_5` |
| 21 | 防露ヒータ出力(1) | ％ | `defrost_heater_output_1` |
| 22 | 防露ヒータ出力(2) | ％ | `defrost_heater_output_2` |

---

## Flaskルート一覧

| No | ルート名 | エンドポイント | メソッド | 用途 | レスポンス形式 |
|----|---------|---------------|---------|------|---------------|
| 1 | 顧客作成ダッシュボード表示 | `/analysis/customer-dashboard` | GET | 初期表示（数値表示ガジェットを埋め込み） | HTML |
| 2 | ガジェットデータ取得 | `/analysis/customer-dashboard/gadgets/<gadget_uuid>/data` | POST | 最新センサー値取得（共通エンドポイント） | JSON (AJAX) |
| 3 | ガジェット登録画面 | `/analysis/customer-dashboard/gadgets/numerical-display/create` | GET | 数値表示ガジェット登録モーダル表示 | HTML（モーダル） |
| 4 | ガジェット登録実行 | `/analysis/customer-dashboard/gadgets/numerical-display/register` | POST | 数値表示ガジェット登録処理 | JSON (AJAX) |

---

## アクセス権限

| 機能 | システム保守者 | 管理者 | 販社ユーザ | サービス利用者 |
|------|---------------|--------|-----------|---------------|
| ガジェット表示 | ○ | ○ | ○ | ○ |
| ガジェット登録 | ○ | ○ | ○ | ○ |

**凡例**:
- **○**: 利用可能
- **-**: 利用不可

**データスコープ制限**:
- すべてのユーザー: `organization_closure` による組織階層ベースのフィルタリングを適用
- ロールによるデータ制限は行わない（UI動線制御のみに使用）

---

## 関連ドキュメント

### 仕様書

- [UI仕様書](./ui-specification.md) - 画面レイアウト・UI要素・数値フォーマット仕様
- [ワークフロー仕様書](./workflow-specification.md) - 処理フロー・DB処理・エラーハンドリング

### 共通仕様

- [UI共通仕様書](../../../common/ui-common-specification.md) - すべての画面に共通するUI仕様
- [共通仕様書](../../../common/common-specification.md) - HTTPステータスコード、エラーコード等

### 顧客作成ダッシュボード画面共通仕様

- [README](../common/README.md) - 親画面となる顧客作成ダッシュボード画面のREADME
- [UI仕様書](../common/ui-specification.md) - 親画面となる顧客作成ダッシュボード画面のUI仕様書
- [ワークフロー仕様書](../common/workflow-specification.md) - 親画面となる顧客作成ダッシュボード画面のワークフロー仕様書

### データベース

- [アプリケーションDB設計書](../../../common/app-database-specification.md) - テーブル定義（silver_sensor_data, measurement_item_master, dashboard_gadget_master 等）
