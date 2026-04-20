# 顧客作成ダッシュボード機能

## 📑 目次

- [顧客作成ダッシュボード機能](#顧客作成ダッシュボード機能)
  - [📑 目次](#-目次)
  - [概要](#概要)
  - [機能一覧](#機能一覧)
  - [画面一覧](#画面一覧)
  - [データモデル](#データモデル)
    - [テーブル定義](#テーブル定義)
      - [dashboard\_master（ダッシュボードマスタ）](#dashboard_masterダッシュボードマスタ)
      - [インデックス](#インデックス)
      - [dashboard\_group\_master（ダッシュボードグループマスタ）](#dashboard_group_masterダッシュボードグループマスタ)
      - [インデックス](#インデックス-1)
      - [dashboard\_gadget\_master（ダッシュボードガジェットマスタ）](#dashboard_gadget_masterダッシュボードガジェットマスタ)
      - [インデックス](#インデックス-2)
      - [gadget\_type\_master（ガジェット種別マスタ）](#gadget_type_masterガジェット種別マスタ)
      - [インデックス](#インデックス-3)
      - [dashboard\_user\_setting（ダッシュボードユーザー設定）](#dashboard_user_settingダッシュボードユーザー設定)
      - [インデックス](#インデックス-4)
      - [gold\_summary\_method\_master（サマリー計算手法マスタ）](#gold_summary_method_masterサマリー計算手法マスタ)
      - [インデックス](#インデックス-5)
  - [Flaskルート一覧](#flaskルート一覧)
  - [アクセス権限](#アクセス権限)
  - [ダッシュボード編集権限](#ダッシュボード編集権限)
  - [関連ドキュメント](#関連ドキュメント)
    - [仕様書](#仕様書)
    - [共通仕様](#共通仕様)
    - [ガジェット仕様](#ガジェット仕様)
    - [要件定義](#要件定義)

---

## 概要

顧客作成ダッシュボード画面は、Databricks IoTシステムにおけるIoTデータの可視化と分析を提供する機能です。ユーザーがダッシュボード・ダッシュボードグループ・ガジェット（各種グラフ）を作成し、ダッシュボード上に自由に配置可能です。

**機能ID:** FR-006

**特徴:**
- **カスタムダッシュボード**: ユーザーがダッシュボード・ダッシュボードグループ・ガジェットを作成し自由に配置
- **多様なガジェット種別**: 数値表示、メーター、棒グラフ、円グラフ、時系列グラフ、表、地図など22種類のガジェットに対応
- **2パターン固定サイズ**: ガジェットサイズは2×2（480×480px）と2×4（960×480px）の2パターン固定（リサイズ不可、登録時のみ選択）
- **ドラッグ＆ドロップ配置**: ガジェットをドラッグ＆ドロップで自由に配置可能（リサイズ操作なし）
- **自動更新**: 60秒間隔でのガジェット自動更新に対応
- **CSVエクスポート**: ガジェットのグラフデータをCSVファイルとしてダウンロード可能
- **データスコープ制限**: すべてのユーザーに所属組織配下のデータのみアクセス可能なフィルタが適用される

**グラフ描画ライブラリ**
- Apache ECharts 5.x系を使用して描画（クライアントサイドでJavaScriptによるレンダリング）

---

## 機能一覧

| 機能ID | 機能名 | 概要 |
|--------|--------|------|
| FR-006-1 | 顧客作成ダッシュボード表示 | ユーザーが作成したダッシュボード/ダッシュボードグループ/ガジェットを表示 |
| FR-006-2 | ダッシュボード管理 | ダッシュボードの登録/表示切替/タイトル更新/削除を管理 |
| FR-006-3 | ダッシュボードグループ管理 | ダッシュボードグループの登録/タイトル更新/削除を管理 |
| FR-006-4 | ガジェット管理 | ガジェットの追加/タイトル更新/削除を管理 |
| FR-006-5 | レイアウト管理 | ガジェットのドラッグ＆ドロップによる配置管理 |
| FR-006-6 | データソース選択 | 組織・デバイスによるガジェットデータソースの選択 |
| FR-006-7 | CSVエクスポート | ガジェットのグラフデータをCSVファイルとしてエクスポート |

---

## 画面一覧

| 画面ID | 画面名 | スラッグ | 表示方式 | 概要 |
|--------|--------|---------|---------|------|
| CDS-001 | 顧客作成ダッシュボード表示画面 | `/analysis/customer-dashboard` | 画面 | ダッシュボード/ダッシュボードグループ/ガジェットを表示 |
| CDS-002 | ダッシュボード管理モーダル | `/analysis/customer-dashboard/dashboards` | モーダル | ダッシュボードの登録/表示切替/削除を選択 |
| CDS-003 | ガジェット追加モーダル | `/analysis/customer-dashboard/gadgets/add` | モーダル | 追加するガジェットの種別を選択 |
| CDS-004 | 登録・更新モーダル | `/analysis/customer-dashboard/dashboards/create`, `/analysis/customer-dashboard/dashboards/<dashboard_uuid>/edit`, `/analysis/customer-dashboard/groups/create`, `/analysis/customer-dashboard/groups/<dashboard_group_uuid>/edit`, `/analysis/customer-dashboard/gadgets/<gadget_uuid>/edit` | モーダル | ダッシュボード登録/ダッシュボードタイトル更新/ダッシュボードグループ登録/ダッシュボードグループタイトル更新/ガジェットタイトル更新 |
| CDS-005 | 削除確認モーダル | `/analysis/customer-dashboard/dashboards/<dashboard_uuid>/delete`, `/analysis/customer-dashboard/groups/<dashboard_group_uuid>/delete`, `/analysis/customer-dashboard/gadgets/<gadget_uuid>/delete` | モーダル | ダッシュボード削除/ダッシュボードグループ削除/ガジェット削除の確認 |

---

## データモデル

### テーブル定義

#### dashboard_master（ダッシュボードマスタ）

| カラム名 | 論理名 | データ型 | 必須 | 備考 |
|----------|-------|---------|------|------|
| dashboard_id | ダッシュボードID | INT | ○ | ダッシュボードの一意識別子（主キー、AutoIncrement） |
| dashboard_uuid | ダッシュボードUUID | VARCHAR(36) | ○ | ダッシュボードのUUID（URLパラメータ用） |
| dashboard_name | ダッシュボード名 | VARCHAR(50) | ○ | ダッシュボード名 |
| organization_id | 組織ID | INT | ○ | 組織の一意識別子（外部キー） |
| create_date | 作成日時 | DATETIME | ○ | レコード作成日時 |
| creator | 作成者 | INT | ○ | レコード作成者のユーザーID |
| update_date | 更新日時 | DATETIME | ○ | レコード更新日時 |
| modifier | 更新者 | INT | ○ | レコード更新者のユーザーID |
| delete_flag | 削除フラグ | BOOLEAN | ○ | 論理削除状態（デフォルト: FALSE） |

#### インデックス

| インデックス名 | カラム | 種別 | 目的 |
|---------------|--------|-----|------|
| PRIMARY | dashboard_id | 主キー | ダッシュボードの一意識別子 |

#### dashboard_group_master（ダッシュボードグループマスタ）

| カラム名 | 論理名 | データ型 | 必須 | 備考 |
|----------|-------|---------|------|------|
| dashboard_group_id | ダッシュボードグループID | INT | ○ | ダッシュボードグループの一意識別子（主キー、AutoIncrement） |
| dashboard_group_uuid | ダッシュボードグループUUID | VARCHAR(36) | ○ | ダッシュボードグループのUUID（URLパラメータ用） |
| dashboard_group_name | ダッシュボードグループ名 | VARCHAR(50) | ○ | ダッシュボードグループ名 |
| dashboard_id | ダッシュボードID | INT | ○ | ダッシュボードの一意識別子（外部キー） |
| display_order | 表示順 | INT | ○ | ダッシュボードグループの表示順 |
| create_date | 作成日時 | DATETIME | ○ | レコード作成日時 |
| creator | 作成者 | INT | ○ | レコード作成者のユーザーID |
| update_date | 更新日時 | DATETIME | ○ | レコード更新日時 |
| modifier | 更新者 | INT | ○ | レコード更新者のユーザーID |
| delete_flag | 削除フラグ | BOOLEAN | ○ | 論理削除状態（デフォルト: FALSE） |

#### インデックス

| インデックス名 | カラム | 種別 | 目的 |
|---------------|--------|-----|------|
| PRIMARY | dashboard_group_id | 主キー | ダッシュボードグループの一意識別子 |

#### dashboard_gadget_master（ダッシュボードガジェットマスタ）

| カラム名 | 論理名 | データ型 | 必須 | 備考 |
|----------|-------|---------|------|------|
| gadget_id | ガジェットID | INT | ○ | ガジェットの一意識別子（主キー、AutoIncrement） |
| gadget_uuid | ガジェットUUID | VARCHAR(36) | ○ | ガジェットのUUID（URLパラメータ用） |
| gadget_name | ガジェット名 | VARCHAR(20) | ○ | ガジェット名 |
| dashboard_group_id | ダッシュボードグループID | INT | ○ | ダッシュボードグループの一意識別子（外部キー） |
| gadget_type_id | ガジェット種別ID | INT | ○ | ガジェット種別の一意識別子（外部キー） |
| chart_config | チャート設定 | JSON | ○ | 抽象化されたアプリケーション設定（EChartsオプションへの変換はレンダリング時に実行） |
| data_source_config | データソース設定 | JSON | ○ | ガジェットが参照するデータの種別・表示設定（デフォルト設定） |
| position_x | X座標 | INT | ○ | グリッド位置 |
| position_y | Y座標 | INT | ○ | グリッド位置 |
| gadget_size | ガジェットサイズ | INT | ○ | 0: 2x2（480×480px）、1: 2×4（960×480px） |
| display_order | 表示順 | INT | ○ | ガジェットの表示順 |
| create_date | 作成日時 | DATETIME | ○ | レコード作成日時 |
| creator | 作成者 | INT | ○ | レコード作成者のユーザーID |
| update_date | 更新日時 | DATETIME | ○ | レコード更新日時 |
| modifier | 更新者 | INT | ○ | レコード更新者のユーザーID |
| delete_flag | 削除フラグ | BOOLEAN | ○ | 論理削除状態（デフォルト: FALSE） |

#### インデックス

| インデックス名 | カラム | 種別 | 目的 |
|---------------|--------|-----|------|
| PRIMARY | gadget_id | 主キー | ガジェットの一意識別子 |

#### gadget_type_master（ガジェット種別マスタ）

| カラム名 | 論理名 | データ型 | 必須 | 備考 |
|----------|-------|---------|------|------|
| gadget_type_id | ガジェット種別ID | INT | ○ | ガジェット種別の一意識別子（主キー、AutoIncrement） |
| gadget_type_name | ガジェット種別名 | VARCHAR(20) | ○ | ガジェット種別名 |
| data_source_type | データソース種別 | INT | ○ | 0: 組織、1: デバイス |
| gadget_image_path | ガジェットイメージパス | VARCHAR(100) | ○ | 画像パス（例: static\images\xxxxx.png） |
| gadget_description | ガジェット説明 | VARCHAR(500) | ○ | ガジェットの説明文 |
| display_order | 表示順 | INT | ○ | ガジェット種別の表示順 |
| create_date | 作成日時 | DATETIME | ○ | レコード作成日時 |
| creator | 作成者 | INT | ○ | レコード作成者のユーザーID |
| update_date | 更新日時 | DATETIME | ○ | レコード更新日時 |
| modifier | 更新者 | INT | ○ | レコード更新者のユーザーID |
| delete_flag | 削除フラグ | BOOLEAN | ○ | 論理削除状態（デフォルト: FALSE） |

#### インデックス

| インデックス名 | カラム | 種別 | 目的 |
|---------------|--------|-----|------|
| PRIMARY | gadget_type_id | 主キー | ガジェット種別の一意識別子 |

#### dashboard_user_setting（ダッシュボードユーザー設定）

| カラム名 | 論理名 | データ型 | 必須 | 備考 |
|----------|-------|---------|------|------|
| user_id | ユーザーID | INT | ○ | ユーザーの一意識別子（主キー、外部キー） |
| dashboard_id | ダッシュボードID | INT | ○ | 選択中のダッシュボードID（外部キー） |
| organization_id | 組織ID | INT | ○ | 選択中の組織ID（外部キー）、未選択の場合は0を登録 |
| device_id | デバイスID | INT | ○ | 選択中のデバイスID（外部キー） 、未選択の場合は0を登録 |
| create_date | 作成日時 | DATETIME | ○ | レコード作成日時 |
| creator | 作成者 | INT | ○ | レコード作成者のユーザーID |
| update_date | 更新日時 | DATETIME | ○ | レコード更新日時 |
| modifier | 更新者 | INT | ○ | レコード更新者のユーザーID |
| delete_flag | 削除フラグ | BOOLEAN | ○ | 論理削除状態（デフォルト: FALSE） |

#### インデックス

| インデックス名 | カラム | 種別 | 目的 |
|---------------|--------|-----|------|
| PRIMARY | user_id | 主キー | ユーザーの一意識別子 |

#### gold_summary_method_master（サマリー計算手法マスタ）

| カラム名 | 論理名 | データ型 | 必須 | 備考 |
|----------|-------|---------|------|------|
| summary_method_id | 集計方法ID | INT | ○ | 集約方法の一意識別子（主キー、AutoIncrement） |
| summary_method_code | 集計方法コード | VARCHAR(20) | ○ | 集約方法コード |
| summary_method_name | 集計方法名 | VARCHAR(30) | ○ | 集約方法名 |
| create_date | 作成日時 | DATETIME | ○ | レコード作成日時 |
| creator | 作成者 | INT | ○ | レコード作成者のユーザーID |
| update_date | 更新日時 | DATETIME | ○ | レコード更新日時 |
| modifier | 更新者 | INT | ○ | レコード更新者のユーザーID |
| delete_flag | 削除フラグ | BOOLEAN | ○ | 論理削除状態（デフォルト: FALSE） |

#### インデックス

| インデックス名 | カラム | 種別 | 目的 |
|---------------|--------|-----|------|
| PRIMARY | summary_method_id | 集約方法ID | 集約方法の一意識別子 |

---

## Flaskルート一覧

| No | ルート名 | エンドポイント | メソッド | 用途 | レスポンス形式 |
|----|---------|---------------|---------|------|---------------|
| 1 | 顧客作成ダッシュボード表示 | `/analysis/customer-dashboard` | GET | 顧客作成ダッシュボード画面の初期表示 | HTML |
| 2 | ダッシュボード管理画面 | `/analysis/customer-dashboard/dashboards` | GET | ダッシュボード管理画面表示 | HTML（モーダル） |
| 3 | ダッシュボード登録画面 | `/analysis/customer-dashboard/dashboards/create` | GET | ダッシュボード登録画面表示 | HTML（モーダル） |
| 4 | ダッシュボード登録実行 | `/analysis/customer-dashboard/dashboards/register` | POST | ダッシュボード登録処理 | リダイレクト (302) |
| 5 | ダッシュボードタイトル更新画面 | `/analysis/customer-dashboard/dashboards/<dashboard_uuid>/edit` | GET | ダッシュボードタイトル更新画面表示 | HTML（モーダル） |
| 6 | ダッシュボードタイトル更新実行 | `/analysis/customer-dashboard/dashboards/<dashboard_uuid>/update` | POST | ダッシュボードタイトル更新処理 | リダイレクト (302) |
| 7 | ダッシュボード削除確認画面 | `/analysis/customer-dashboard/dashboards/<dashboard_uuid>/delete` | GET | ダッシュボード削除確認画面表示 | HTML（モーダル） |
| 8 | ダッシュボード削除実行 | `/analysis/customer-dashboard/dashboards/<dashboard_uuid>/delete` | POST | ダッシュボード削除処理 | リダイレクト (302) |
| 9 | ダッシュボード表示切替 | `/analysis/customer-dashboard/dashboards/<dashboard_uuid>/switch` | POST | 表示するダッシュボードの切替 | リダイレクト (302) |
| 10 | ダッシュボードグループ登録画面 | `/analysis/customer-dashboard/groups/create` | GET | ダッシュボードグループ登録画面表示 | HTML（モーダル） |
| 11 | ダッシュボードグループ登録実行 | `/analysis/customer-dashboard/groups/register` | POST | ダッシュボードグループ登録処理 | リダイレクト (302) |
| 12 | ダッシュボードグループタイトル更新画面 | `/analysis/customer-dashboard/groups/<dashboard_group_uuid>/edit` | GET | ダッシュボードグループタイトル更新画面表示 | HTML（モーダル） |
| 13 | ダッシュボードグループタイトル更新実行 | `/analysis/customer-dashboard/groups/<dashboard_group_uuid>/update` | POST | ダッシュボードグループタイトル更新処理 | リダイレクト (302) |
| 14 | ダッシュボードグループ削除確認画面 | `/analysis/customer-dashboard/groups/<dashboard_group_uuid>/delete` | GET | ダッシュボードグループ削除確認画面表示 | HTML（モーダル） |
| 15 | ダッシュボードグループ削除実行 | `/analysis/customer-dashboard/groups/<dashboard_group_uuid>/delete` | POST | ダッシュボードグループ削除処理 | リダイレクト (302) |
| 16 | ガジェット追加画面 | `/analysis/customer-dashboard/gadgets/add` | GET | ガジェット追加画面表示 | HTML（モーダル） |
| 17 | ガジェット登録画面 | `/analysis/customer-dashboard/gadgets/{gadget_type}/create` | GET | ガジェット登録画面表示、ガジェット毎にFlaskルートが異なる | HTML（モーダル） |
| 18 | ガジェット登録実行 | `/analysis/customer-dashboard/gadgets/{gadget_type}/register` | POST | ガジェット登録処理、ガジェット毎にFlaskルートが異なる | リダイレクト (302) |
| 19 | ガジェットタイトル更新画面 | `/analysis/customer-dashboard/gadgets/<gadget_uuid>/edit` | GET | ガジェットタイトル更新画面表示 | HTML（モーダル） |
| 20 | ガジェットタイトル更新実行 | `/analysis/customer-dashboard/gadgets/<gadget_uuid>/update` | POST | ガジェットタイトル更新処理 | リダイレクト (302) |
| 21 | ガジェット削除確認画面 | `/analysis/customer-dashboard/gadgets/<gadget_uuid>/delete` | GET | ガジェット削除確認画面表示 | HTML（モーダル） |
| 22 | ガジェット削除実行 | `/analysis/customer-dashboard/gadgets/<gadget_uuid>/delete` | POST | ガジェット削除処理 | リダイレクト (302) |
| 23 | ガジェットデータ取得 | `/analysis/customer-dashboard/gadgets/<gadget_uuid>/data` | POST | ガジェットのグラフ表示用データ取得 | JSON (AJAX) |
| 24 | レイアウト保存 | `/analysis/customer-dashboard/layout/save` | POST | ガジェットのレイアウト設定保存 | JSON (AJAX) |
| 25 | CSVエクスポート | `/analysis/customer-dashboard/gadgets/<gadget_uuid>?export=csv` | GET | ガジェットのグラフデータをCSVファイルとしてダウンロード | CSV |

---

## アクセス権限

| 機能 | システム保守者 | 管理者 | 販社ユーザ | サービス利用者 |
|------|---------------|--------|-----------|---------------|
| ダッシュボード表示 | ○ | ○ | ○ | ○ |
| ダッシュボード管理 | ○ | ○ | ○ | ○ |
| ダッシュボードグループ管理 | ○ | ○ | ○ | ○ |
| ガジェット管理 | ○ | ○ | ○ | ○ |
| レイアウト管理 | ○ | ○ | ○ | ○ |
| CSVエクスポート | ○ | ○ | ○ | ○ |

**凡例**:
- **○**: 利用可能
- **-**: 利用不可

**データスコープ制限**:
- **すべてのユーザー**: 組織階層（organization_closure）によるデータスコープ制限
  - ユーザーの所属組織とその下位組織に属するデータのみアクセス可能

**ダッシュボードアクセス制限**:
- **すべてのユーザー**: 
  - ユーザーの所属組織に属するダッシュボードのみアクセス可能
  - 下位組織であっても他組織のダッシュボードはアクセス不可

---

## ダッシュボード編集権限

作成されたダッシュボードに予期しない変更が加わることを防ぐため、各機能の利用ユーザーを限定する。
処理の開始時に`creator`と`ログインユーザー`が一致することを確認し、一致しない場合は403エラー（権限エラー）とする。

| 機能 | 利用可能ユーザー | 備考 |
|------|-----------------|-----|
| ダッシュボードタイトル更新 | ダッシュボード作成者 |  |
| ダッシュボード削除 | ダッシュボード作成者 | |
| ダッシュボードグループ登録 | ダッシュボード作成者 | |
| ダッシュボードグループタイトル更新 | ダッシュボードグループ作成者 | ダッシュボードグループ作成者=ダッシュボード作成者 |
| ダッシュボードグループ削除 | ダッシュボードグループ作成者 | 同上 |
| ガジェット登録 | ダッシュボードグループ作成者 | 同上 |
| ガジェットタイトル更新 | ガジェット作成者 | ガジェット作成者=ダッシュボードグループ作成者=ダッシュボード作成者 |
| ガジェット削除 | ガジェット作成者 | 同上 |
| レイアウト保存 | ダッシュボード作成者 | |

**重要:** ダッシュボード作成者がシステムから削除された場合、新規でオブジェクトを作り直す運用とする

---

## 関連ドキュメント

### 仕様書

- [UI仕様書](./ui-specification.md) - 画面レイアウト・UI要素・バリデーション
- [ワークフロー仕様書](./workflow-specification.md) - 処理フロー・API統合・エラーハンドリング

### 共通仕様

- [UI共通仕様書](../../../common/ui-common-specification.md) - すべての画面に共通するUI仕様
- [共通仕様書](../../../common/common-specification.md) - HTTPステータスコード、エラーコード等

### ガジェット仕様

- [業種別ダッシュボード](../industry-dashboard/) - 業種別ダッシュボード機能
- [デバイス管理](../devices/) - デバイス情報の管理
- [組織管理](../organizations/) - 組織情報の管理

### 要件定義

- [機能要件定義書](../../../02-requirements/functional-requirements.md) - FR-006
- [非機能要件定義書](../../../02-requirements/non-functional-requirements.md) - パフォーマンス、セキュリティ要件
- [技術要件定義書](../../../02-requirements/technical-requirements.md) - 技術スタック、実装方針

---
