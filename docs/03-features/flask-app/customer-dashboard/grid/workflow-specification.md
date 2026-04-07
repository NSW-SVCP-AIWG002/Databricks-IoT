# 顧客作成ダッシュボード表ガジェット - ワークフロー仕様書

## 📑 目次

- [顧客作成ダッシュボード表ガジェット - ワークフロー仕様書](#顧客作成ダッシュボード表ガジェット---ワークフロー仕様書)
  - [📑 目次](#-目次)
  - [概要](#概要)
  - [使用するFlaskルート一覧](#使用するflaskルート一覧)
  - [ルート呼び出しマッピング](#ルート呼び出しマッピング)
    - [表ガジェット](#表ガジェット)
    - [表ガジェット登録モーダル](#表ガジェット登録モーダル)
  - [ワークフロー一覧](#ワークフロー一覧)
    - [ガジェット初期表示](#ガジェット初期表示)
      - [処理フロー](#処理フロー)
      - [Flaskルート](#flaskルート)
      - [バリデーション](#バリデーション)
      - [処理詳細（サーバーサイド）](#処理詳細サーバーサイド)
    - [ガジェットデータ取得](#ガジェットデータ取得)
      - [処理フロー](#処理フロー-1)
      - [Flaskルート](#flaskルート-1)
      - [バリデーション](#バリデーション-1)
      - [処理詳細（サーバーサイド）](#処理詳細サーバーサイド-1)
    - [ページング](#ページング)
      - [処理フロー](#処理フロー-2)
      - [処理詳細](#処理詳細)
      - [UI状態](#ui状態)
    - [ガジェット登録モーダル表示](#ガジェット登録モーダル表示)
      - [処理フロー](#処理フロー-3)
      - [Flaskルート](#flaskルート-2)
      - [バリデーション](#バリデーション-2)
      - [処理詳細（サーバーサイド）](#処理詳細サーバーサイド-2)
      - [エラーハンドリング](#エラーハンドリング)
    - [ガジェット登録](#ガジェット登録)
      - [処理フロー](#処理フロー-4)
      - [Flaskルート](#flaskルート-3)
      - [バリデーション](#バリデーション-3)
      - [処理詳細（サーバーサイド）](#処理詳細サーバーサイド-3)
      - [エラーハンドリング](#エラーハンドリング-1)
    - [CSVエクスポート](#csvエクスポート)
      - [処理フロー](#処理フロー-5)
      - [Flaskルート](#flaskルート-4)
      - [バリデーション](#バリデーション-4)
      - [処理詳細（サーバーサイド）](#処理詳細サーバーサイド-4)
      - [エラーハンドリング](#エラーハンドリング-2)
  - [セキュリティ実装](#セキュリティ実装)
    - [認証・認可実装](#認証認可実装)
    - [ログ出力ルール](#ログ出力ルール)
  - [関連ドキュメント](#関連ドキュメント)

**重要:** 顧客作成ダッシュボード画面の共通仕様は [共通ワークフロー仕様書](../common/workflow-specification.md) を参照してください。

---

## 概要

このドキュメントは、顧客作成ダッシュボード表ガジェット機能のユーザー操作に対する処理フロー、データベース処理、エラーハンドリングの詳細を記載します。

**このドキュメントの役割:**
- ✅ ユーザー操作のトリガー条件
- ✅ 処理フローの詳細（Flaskルート呼び出し、フォーム送信、AJAX通信）
- ✅ エラーハンドリングフロー
- ✅ サーバーサイド処理詳細（SQL、変数、条件分岐、コード例）
- ✅ データベース利用詳細（トランザクション管理、テーブル操作）
- ✅ セキュリティ実装詳細（認証、データスコープ制限、ログ出力）
- ✅ クライアントサイド処理詳細（AJAX、ドラッグ＆ドロップ、自動更新）

**UI仕様書との役割分担:**
- **UI仕様書**: 画面レイアウト、UI要素の詳細仕様
- **ワークフロー仕様書**: 処理フロー、データベース処理、エラーハンドリング、サーバーサイド実装詳細

**注:** UI要素の詳細は [UI仕様書](./ui-specification.md) を参照してください。

---

## 使用するFlaskルート一覧

この機能で使用するすべてのFlaskルート（エンドポイント）を記載します。

| No | ルート名 | エンドポイント | メソッド | 用途 | レスポンス形式 | 備考 |
|----|---------|---------------|---------|------|---------------|------|
| 1 | 顧客作成ダッシュボード表示 | `/analysis/customer-dashboard` | GET | 初期表示（顧客作成ダッシュボード画面に表ガジェットを埋め込み） | HTML | - |
| 2 | ガジェットデータ取得 | `/analysis/customer-dashboard/gadgets/<gadget_uuid>/data` | POST | ガジェットのグラフ表示用データ取得 | JSON (AJAX) | 非同期通信 |
| 3 | ガジェット登録画面 | `/analysis/customer-dashboard/gadgets/grid/create` | GET | 表ガジェット登録モーダル表示 | HTML（モーダル） | - |
| 4 | ガジェット登録実行 | `/analysis/customer-dashboard/gadgets/grid/register` | POST | 表ガジェット登録処理 | リダイレクト (302) | 成功時: `/analysis/customer-dashboard` |
| 5 | CSVエクスポート | `/analysis/customer-dashboard/gadgets/<gadget_uuid>?export=csv` | GET | ガジェットのグラフデータをCSVファイルとしてダウンロード | CSV | - |

**注:**
- **レスポンス形式**:
  - `HTML`: Jinja2テンプレートをレンダリングして返す（`render_template()`）
  - `HTML（モーダル）`: モーダルダイアログ用のHTMLフラグメントを返す
  - `リダイレクト (302)`: 処理成功後に `/analysis/customer-dashboard` へリダイレクト
  - `JSON (AJAX)`: JavaScriptからの非同期リクエストに対してJSONレスポンスを返す
  - `CSV`: CSVファイルをダウンロードレスポンスとして返す
- **Flask Blueprint構成**: `customer_dashboard_bp` として実装

---

## ルート呼び出しマッピング

### 表ガジェット

| ユーザー操作 | トリガー | 呼び出すルート | パラメータ | レスポンス | エラー時の挙動 |
|-------------|---------|-------------|-----------|-----------|---------------|
| 画面初期表示 | URL直接アクセス | `GET /analysis/customer-dashboard`, `POST /analysis/customer-dashboard/gadgets/<gadget_uuid>/data` | なし | HTML（顧客作成ダッシュボード画面に表ガジェットを埋め込み） | エラーページ表示 |
| 開始日時・終了日時選択 | デイトタイムピッカー選択 | `POST /analysis/customer-dashboard/gadgets/<gadget_uuid>/data` | `gadget_uuid` | JSON | エラーモーダル表示 |
| 更新ボタン押下 | ボタンクリック | `POST /analysis/customer-dashboard/gadgets/<gadget_uuid>/data` | `gadget_uuid` | JSON | エラーモーダル表示 |
| ページ番号ボタン押下 | ボタンクリック | `POST /analysis/customer-dashboard/gadgets/<gadget_uuid>/data` | `gadget_uuid, page` | JSON（該当ページデータ） | エラーモーダル表示 |
| CSVエクスポートボタン押下 | ボタンクリック | `GET /analysis/customer-dashboard/gadgets/<gadget_uuid>?export=csv` | `gadget_uuid` | CSVダウンロード | エラーモーダル表示 |

### 表ガジェット登録モーダル

| ユーザー操作 | トリガー | 呼び出すルート | パラメータ | レスポンス | エラー時の挙動 |
|-------------|---------|-------------|-----------|-----------|---------------|
| 画面初期表示 | URL直接アクセス | `GET /analysis/customer-dashboard/gadgets/grid/create` | なし | HTML（モーダル） | エラーページ表示 |
| 開始日時・終了日時選択 | デイトタイムピッカー選択 | `POST /analysis/customer-dashboard/gadgets/<gadget_uuid>/data` | `gadget_uuid` | JSON | エラーモーダル表示 |
| 登録ボタン押下 | ボタンクリック | `POST /analysis/customer-dashboard/gadgets/grid/register` | `title, group_id, gadget_size` | リダイレクト | エラーモーダル表示 |

---

## ワークフロー一覧

### ガジェット初期表示

**トリガー:** 顧客作成ダッシュボード画面アクセス時

**前提条件:**
- ユーザーがログイン済み（Databricks認証完了）
- 適切な権限を持っている（システム保守者、管理者、販社ユーザ、サービス利用者）

#### 処理フロー

[共通ワークフロー仕様書](../common/workflow-specification.md) のダッシュボード初期表示と同様の処理フローに従います。

#### Flaskルート

| ルート | エンドポイント | 詳細 |
|-------|---------------|------|
| 顧客作成ダッシュボード表示 | `GET /analysis/customer-dashboard` | クエリパラメータ: なし |

#### バリデーション

**実行タイミング:** なし

**データスコープ制限:**
- **全ユーザー共通**: 組織階層（`organization_closure`）でフィルタ
  - ユーザーの `organization_id` を親組織IDとして検索
  - 下位組織リスト（`subsidiary_organization_id`）を取得
  - そのリストに該当する組織のデータのみアクセス可能
  - **ロールによる条件分岐は一切行わない**

**注**: システム保守者・管理者が全データにアクセスできるのは、ルート組織に所属しているため

#### 処理詳細（サーバーサイド）

[共通ワークフロー仕様書](../common/workflow-specification.md) のダッシュボード初期表示の処理詳細（①〜⑨）と同様の処理を実行します。

表ガジェット固有の追加処理はありません。

---

### ガジェットデータ取得

**トリガー:** 画面初期表示時 / 開始日時・終了日時選択時 / 更新ボタン押下時

**前提条件:**
- ガジェットが表示されている
- データソース設定が存在する

#### 処理フロー

```mermaid
flowchart TD
    Start([ガジェットデータ取得リクエスト<br>AJAX]) --> Auth[認証チェック]
    Auth --> CheckAuth{認証済み?}
    CheckAuth -->|未認証| Error401[401エラーレスポンス]
    CheckAuth -->|認証OK| Scope[データスコープ制限チェック<br>ガジェットがアクセス可能な組織に属するか確認]

    Scope --> CheckScope{スコープOK?}
    CheckScope -->|スコープ外| Error404[404エラーレスポンス]
    CheckScope -->|スコープOK| Validate[バリデーション<br>リクエストパラメータ]

    Validate --> CheckValidate{バリデーションOK?}
    CheckValidate -->|NG| Error400[400エラーレスポンス]
    CheckValidate -->|OK| DeviceQuery[選択中デバイス取得<br>DB dashboard_user_setting]

    DeviceQuery --> CheckDeviceQuery{DBクエリ結果}
    CheckDeviceQuery -->|失敗| Error500
    CheckDeviceQuery -->|成功| SilverQuery[センサーデータ取得<br>sensor_data_view]

    SilverQuery --> CheckSilverQuery{DBクエリ結果}
    CheckSilverQuery -->|NG| Error500
    CheckSilverQuery -->|OK| ColumnNameQuery[テーブルカラム名取得<br>DB measurement_item_master]

    ColumnNameQuery --> CheckColumnNameQuery{DBクエリ結果}
    CheckColumnNameQuery -->|NG| Error500
    CheckColumnNameQuery -->|OK| Format[データ整形]

    Format --> ReturnData[JSONデータ返却]

    Error401 --> End([処理完了])
    Error404 --> End
    Error400 --> End
    Error500 --> End
    ReturnData --> End
```

#### Flaskルート

| ルート | エンドポイント | 詳細 |
|-------|---------------|------|
| ガジェットデータ取得 | `POST /analysis/customer-dashboard/gadgets/<gadget_uuid>/data` | パスパラメータ: `gadget_uuid` リクエストボディ: `start_datetime, end_datetime, page`（pageは省略時1） |

#### バリデーション

**実行タイミング:** データスコープ制限チェック完了後

**バリデーションルール:**

| 項目 | ルール | エラーメッセージ |
|------|--------|-----------------|
| 開始日時 | 日付形式 | 正しい日付形式で入力してください（YYYY/MM/DD HH:mm:ss） |
| 終了日時 | 日付形式 | 正しい日付形式で入力してください（YYYY/MM/DD HH:mm:ss） |
| 開始日時 | 開始日時 < 終了日時 | 終了日時は開始日時以降の日時を入力してください |

#### 処理詳細（サーバーサイド）

**① 選択中デバイス取得**

**使用テーブル:** dashboard_user_setting, device_master

**SQL詳細:**
```sql
SELECT
  du.device_id,
  dm.device_name
FROM
  dashboard_user_setting du
LEFT JOIN
  device_master dm
ON
  du.device_id = dm.device_id
  AND dm.delete_flag = FALSE
WHERE
  du.user_id = :current_user_id
  AND du.delete_flag = FALSE
```

---

**② センサーデータ取得**

**使用テーブル:** sensor_data_view 

**SQL詳細:** 
```sql
SELECT
  event_timestamp 
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
FROM
  iot_catalog.views.sensor_data_view
WHERE
  device_id = :device_id
  AND event_timestamp BETWEEN :start_datetime AND :end_datetime
ORDER BY
  event_timestamp ASC
```

---

**③ テーブルカラム名取得**

**使用テーブル:** measurement_item_master

**SQL詳細:** 
```sql
SELECT
  silver_data_column_name,
  display_name
FROM
  measurement_item_master
WHERE
  delete_flag = FALSE
ORDER BY
  measurement_item_id
```

---

**④ データ整形**

取得データをテーブル表示用に変換します。

```python
def format_grid_data(rows, columns):
    """センサーデータを行ベースのリストに変換"""
    grid_data = []
    for row in rows:
        row_data = {
            'event_timestamp': row['event_timestamp'].strftime('%Y/%m/%d %H:%M:%S'),
            'device_name': row.get('device_name', '')
        }
        for col in columns:
            row_data[col.silver_data_column_name] = row.get(col.silver_data_column_name)
        grid_data.append(row_data)
    return grid_data
```

---

**⑤ レスポンス形式**

```json
{
  "gadget_uuid": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
  "columns": [
    {"column_name": "event_timestamp", "display_name": "受信日時"},
    {"column_name": "device_name",     "display_name": "デバイス名称"},
    {"column_name": "external_temp",   "display_name": "外気温度"},
    {"column_name": "set_temp_freezer_1", "display_name": "第1冷凍 設定温度"},
    ...
  ],
  "grid_data": [
    {
      "event_timestamp": "2026/02/17 00:00:00",
      "device_name": "Device-001",
      "external_temp": 25.5,
      "set_temp_freezer_1": -18.0,
      ...
    }
  ],
  "updated_at": "2026/03/05 12:00:00"
}
```

データなしの場合:
```json
{
  "gadget_uuid": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
  "columns": [
    {"column_name": "event_timestamp", "display_name": "受信日時"},
    {"column_name": "device_name",     "display_name": "デバイス名称"},
    {"column_name": "external_temp",   "display_name": "外気温度"},
    {"column_name": "set_temp_freezer_1", "display_name": "第1冷凍 設定温度"},
    ...
  ],
  "grid_data": [],
  "updated_at": "2026/03/05 12:00:00"
}
```

---

**⑥ 実装例**

```python
@customer_dashboard_bp.route('/analysis/customer-dashboard/gadgets/<string:gadget_uuid>/data', methods=['POST'])
@require_auth
def gadget_grid_data(gadget_uuid):
    """表ガジェットデータ取得（AJAX）"""
    accessible_org_ids = get_accessible_organizations(g.current_user.organization_id)

    # データスコープ制限チェック
    gadget = get_gadget_by_uuid(gadget_uuid)
    if not gadget:
        return jsonify({'error': '指定されたガジェットが見つかりません'}), 404
    if not check_gadget_access(gadget, accessible_org_ids):
        return jsonify({'error': 'アクセス権限がありません'}), 404

    # リクエストパラメータ取得・バリデーション
    params = request.get_json() or {}
    start_datetime_str = params.get('start_datetime')
    end_datetime_str = params.get('end_datetime')

    if not validate_chart_params(start_datetime_str, end_datetime_str):
        return jsonify({'error': 'パラメータが不正です'}), 400

    try:
        start_datetime = datetime.strptime(start_datetime_str, '%Y/%m/%d %H:%M:%S')
        end_datetime = datetime.strptime(end_datetime_str, '%Y/%m/%d %H:%M:%S')

        # ① 選択中デバイス取得
        user_setting = get_dashboard_user_setting(g.current_user.user_id)
        device_id = user_setting.device_id if user_setting else None
        device_name = user_setting.device_name if user_setting else None

        # ② センサーデータ取得
        rows = fetch_grid_data(
            device_id=device_id,
            start_datetime=start_datetime,
            end_datetime=end_datetime
        )

        # ③ テーブルカラム名取得
        columns = get_column_definition()

        # ④ データ整形
        grid_data = format_grid_data(rows, columns)

        return jsonify({
            'gadget_uuid': gadget_uuid,
            'columns': [
                {
                    'column_name': col.silver_data_column_name,
                    'display_name': col.display_name,
                    'unit': col.unit_name
                }
                for col in columns
            ],
            'grid_data': grid_data,
            'updated_at': datetime.now().strftime('%Y/%m/%d %H:%M:%S')
        })

    except Exception as e:
        logger.error(f'表データ取得エラー: gadget_uuid={gadget_uuid}, error={str(e)}')
        return jsonify({'error': 'データの取得に失敗しました'}), 500
```

---

### ページング

**トリガー:** (6.1) ページネーションのページ番号ボタンクリック

**前提条件:**
- ガジェットが表示されている
- ガジェットデータ取得が完了している

#### 処理フロー

```mermaid
flowchart TD
    Start([ページ番号ボタンクリック]) --> SaveCookie[CookieにページConditions保存<br>start_datetime, end_datetime, page]
    SaveCookie --> Ajax[AJAX POST<br>/analysis/customer-dashboard/gadgets/gadget_uuid/data<br>リクエストボディ: start_datetime, end_datetime, page]
    Ajax --> Auth[認証チェック]
    Auth --> CheckAuth{認証済み?}
    CheckAuth -->|未認証| Error401[401エラーレスポンス]
    CheckAuth -->|認証OK| Scope[データスコープ制限チェック]

    Scope --> CheckScope{スコープOK?}
    CheckScope -->|スコープ外| Error404[404エラーレスポンス]
    CheckScope -->|スコープOK| CalcOffset[ページング計算<br>offset = page - 1 × 25<br>limit = 25]

    CalcOffset --> DeviceQuery[選択中デバイス取得<br>DB dashboard_user_setting]
    DeviceQuery --> CheckDeviceQuery{DBクエリ結果}
    CheckDeviceQuery -->|失敗| Error500[500エラーレスポンス]
    CheckDeviceQuery -->|成功| SilverQuery[センサーデータ取得<br>sensor_data_view<br>LIMIT 25 OFFSET offset]

    SilverQuery --> CheckSilverQuery{DBクエリ結果}
    CheckSilverQuery -->|失敗| Error500
    CheckSilverQuery -->|OK| CountQuery[総件数取得<br>sensor_data_view COUNT]

    CountQuery --> CheckCountQuery{DBクエリ結果}
    CheckCountQuery -->|失敗| Error500
    CheckCountQuery -->|OK| Format[データ整形]

    Format --> ReturnData[JSONデータ返却<br>grid_data, total_count, page, per_page]
    ReturnData --> Render[テーブル再描画<br>該当ページのデータ行を表示]
    Render --> UpdatePagination[ページネーションUI更新<br>選択ページをアクティブ状態に変更]

    Error401 --> End([処理完了])
    Error404 --> End
    Error500 --> End
    UpdatePagination --> End
```

#### Flaskルート

| ルート | エンドポイント | 詳細 |
|-------|---------------|------|
| ガジェットデータ取得（ページング） | `POST /analysis/customer-dashboard/gadgets/<gadget_uuid>/data` | パスパラメータ: `gadget_uuid` リクエストボディ: `start_datetime, end_datetime, page`（pageは1以上の整数） |

#### 処理詳細

ページネーションのページ番号を選択するたびにサーバーへAJAXリクエストを送信し、該当ページのデータのみを取得して表示する。

**Cookie管理:**
- Cookieキー: `grid_gadget_search_params_{gadget_uuid}`
- 保存内容: `start_datetime`, `end_datetime`, `page`
- 保存タイミング: ページ番号ボタンクリック時（AJAXリクエスト送信前）
- `max_age`: 86400秒（24時間）

**ページング計算（サーバーサイド）:**
```python
PER_PAGE = 25
page = params.get('page', 1, type=int)
offset = (page - 1) * PER_PAGE

# センサーデータ取得（ページ分のみ）
rows = fetch_grid_data(
    device_id=device_id,
    start_datetime=start_datetime,
    end_datetime=end_datetime,
    limit=PER_PAGE,
    offset=offset
)

# 総件数取得
total_count = count_grid_data(
    device_id=device_id,
    start_datetime=start_datetime,
    end_datetime=end_datetime
)
```

**レスポンス形式（ページング時の追加フィールド）:**
```json
{
  "gadget_uuid": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
  "columns": [ ... ],
  "grid_data": [ ... ],
  "total_count": 250,
  "page": 2,
  "per_page": 25,
  "updated_at": "2026/03/05 12:00:00"
}
```

#### UI状態

- 検索条件（開始日時・終了日時）: 保持
- データテーブル: 選択ページのデータ行を表示（25件）
- ページネーション: 選択ページをアクティブ状態

---

### ガジェット登録モーダル表示

**トリガー:** ガジェット追加モーダルの登録画面ボタンクリック

**前提条件:**
- ガジェット追加モーダルが表示されている
- ガジェット種別が選択されている

**注:** ガジェット追加モーダルのUI仕様は [共通UI仕様書](../common/ui-specification.md) を参照してください。

#### 処理フロー

```mermaid
flowchart TD
    Start([登録画面ボタンクリック]) --> Auth[認証チェック]
    Auth --> CheckAuth{認証済み?}
    CheckAuth -->|未認証| LoginRedirect[ログイン画面へリダイレクト]
    CheckAuth -->|認証OK| Validate[バリデーション<br>ガジェット種別]

    Validate --> CheckValidate{バリデーションOK?}
    CheckValidate -->|NG| Error400[400エラーモーダル表示]
    CheckValidate -->|OK| Scope[データスコープ制限適用<br>organization_closureテーブルから<br>下位組織IDリスト取得]
    
    Scope --> UserSettingQuery[ダッシュボードユーザー設定取得<br>DB dashboard_user_setting]
    UserSettingQuery --> CheckUserSettingQuery{DBクエリ結果}
    CheckUserSettingQuery -->|失敗| Error500[500エラーページ表示]
    CheckUserSettingQuery -->|成功| CheckUserSetting{ユーザー設定あり?}

    CheckUserSetting -->|なし| Error404[404エラーモーダル表示]
    CheckUserSetting -->|あり| DashboardQuery[選択中ダッシュボード情報取得<br>DB dashboard_master]

    DashboardQuery --> CheckDashboardQuery{DBクエリ結果}
    CheckDashboardQuery -->|失敗| Error500
    CheckDashboardQuery -->|成功| CheckDashboard{ダッシュボードあり?}

    CheckDashboard -->|なし| Error404[404エラーモーダル表示]
    CheckDashboard -->|あり| GroupQuery[ダッシュボードグループ一覧取得<br>DB dashboard_group_master]

    GroupQuery --> CheckGroupQuery{DBクエリ結果}
    CheckGroupQuery -->|失敗| Error500
    CheckGroupQuery -->|成功| Template[表ガジェット登録モーダル表示]

    Template --> Response[HTMLレスポンス返却]

    LoginRedirect --> End([処理完了])
    Error400 --> End
    Error404 --> End
    Error500 --> End   
    Response --> End
```

#### Flaskルート

| ルート | エンドポイント | 詳細 |
|-------|---------------|------|
| 表ガジェット登録画面 | `GET /analysis/customer-dashboard/gadgets/grid/create` | パラメータ: なし |

#### バリデーション

**実行タイミング:** 登録画面ボタン押下時

**バリデーションルール:**

| 項目 | ルール | エラーメッセージ |
|------|--------|-----------------|
| ガジェット種別 | 必須 | ガジェットを選択してください |

#### 処理詳細（サーバーサイド）

**① ダッシュボードユーザー設定取得**

**使用テーブル:** dashboard_user_setting

```sql
SELECT
  dashboard_id,
  organization_id,
  device_id
FROM
  dashboard_user_setting
WHERE
  user_id = :current_user_id
  AND delete_flag = FALSE
```

---

**② ダッシュボード情報取得**

**使用テーブル:** dashboard_master

```sql
SELECT
  dashboard_id,
  dashboard_uuid,
  dashboard_name
FROM
  dashboard_master
WHERE
  dashboard_id = :dashboard_id
  AND organization_id IN (:accessible_org_ids)
  AND delete_flag = FALSE
```

---

**③ ダッシュボードグループ一覧取得**

**使用テーブル:** dashboard_group_master

```sql
SELECT
  dashboard_group_id,
  dashboard_group_uuid,
  dashboard_group_name
FROM
  dashboard_group_master
WHERE
  dashboard_id = :dashboard_id
  AND delete_flag = FALSE
ORDER BY
  display_order ASC
```

---

**④ 実装例**

```python
@customer_dashboard_bp.route('/analysis/customer-dashboard/gadgets/grid/create', methods=['GET'])
@require_auth
def gadget_grid_create():
    """表ガジェット登録モーダル表示"""
    accessible_org_ids = get_accessible_organizations(g.current_user.organization_id)

    # ① ユーザー設定取得
    user_setting = get_dashboard_user_setting(g.current_user.user_id)
    if not user_setting:
        abort(404)

    # ② ダッシュボード情報取得
    dashboard = get_dashboard_by_id(user_setting.dashboard_id, accessible_org_ids)
    if not dashboard:
        abort(404)

    # ③ ダッシュボードグループ一覧取得
    groups = get_dashboard_groups(dashboard.dashboard_id)

    form = GridGadgetForm()
    return render_template(
        'customer_dashboard/modals/gadget_register/grid.html',
        form=form,
        dashboard=dashboard,
        groups=groups
    )
```

#### エラーハンドリング

| HTTPステータス | エラー種別 | 処理内容 | 表示内容 |
|--------------|-----------|---------|---------|
| 400 | バリデーションエラー | フォーム再表示（エラーモーダル表示） | バリデーションエラーメッセージ |
| 401 | 認証エラー | ログイン画面へリダイレクト | - |
| 404 | リソース不存在 | 404エラーモーダル表示 | ダッシュボードが見つかりません |
| 500 | データベースエラー | 500エラーページ表示 | データの取得に失敗しました |

---

### ガジェット登録

**トリガー:** ガジェット登録モーダルの登録ボタンクリック

**前提条件:** ガジェット登録モーダルが表示されている

#### 処理フロー

```mermaid
flowchart TD
    Start([登録ボタンクリック]) --> Auth[認証チェック]
    Auth --> CheckAuth{認証済み?}
    CheckAuth -->|未認証| LoginRedirect[ログイン画面へリダイレクト]
    CheckAuth -->|認証OK| Validate[バリデーション]

    Validate --> CheckValidate{バリデーションOK?}
    CheckValidate -->|NG| Error400[400エラーモーダル表示]
    CheckValidate -->|OK| Insert[ガジェット登録<br> DB dashboard_gadget_master INSERT]

    Insert --> CheckInsert{DB操作結果}
    CheckInsert -->|失敗| Error500[500エラーページ表示]
    CheckInsert -->|成功| Commit[トランザクションコミット]

    Commit --> Redirect[リダイレクト<br>/analysis/customer-dashboard]
    Redirect --> 200OK[成功モーダル表示]

    LoginRedirect --> End([処理完了])
    Error400 --> End
    Error404 --> End
    Error500 --> End
    200OK --> End
```

#### Flaskルート

| ルート | エンドポイント | 詳細 |
|-------|---------------|------|
| 表ガジェット登録実行 | `POST /analysis/customer-dashboard/gadgets/grid/register` | フォームデータ: `title, group_id, gadget_size` |

#### バリデーション

**実行タイミング:** フォーム送信時（サーバーサイド）

**バリデーションルール:** [UI仕様書](./ui-specification.md) の バリデーション（登録画面） を参照

#### 処理詳細（サーバーサイド）

**① ガジェット登録**

**使用テーブル:** dashboard_gadget_master

```sql
INSERT INTO dashboard_gadget_master (
  gadget_uuid,
  gadget_name,
  dashboard_group_id,
  gadget_type_id,
  chart_config,
  data_source_config,
  position_x,
  position_y,
  gadget_size,
  display_order,
  create_date,
  creator,
  update_date,
  modifier,
  delete_flag
) VALUES (
  :gadget_uuid,
  :gadget_name,
  :dashboard_group_id,
  :gadget_type_id,
  :chart_config,
  :data_source_config,
  0,
  (
    SELECT COALESCE(MAX(position_y), 0) + 1
    FROM dashboard_gadget_master
    WHERE dashboard_group_id = :dashboard_group_id
    AND delete_flag = FALSE
  ),
  :gadget_size,
  (
    SELECT COALESCE(MAX(display_order), 0) + 1
    FROM dashboard_gadget_master
    WHERE dashboard_group_id = :dashboard_group_id
    AND delete_flag = FALSE
  ),
  NOW(),
  :current_user_id,
  NOW(),
  :current_user_id,
  FALSE
)
```

---

**② 実装例**

```python
@customer_dashboard_bp.route('/analysis/customer-dashboard/gadgets/grid/register', methods=['POST'])
@require_auth
def gadget_grid_register():
    """表ガジェット登録実行"""
    form = GridGadgetForm()
    if not form.validate_on_submit():
        return render_template(
            'customer_dashboard/modals/gadget_register/grid.html',
            form=form
        ), 400

    accessible_org_ids = get_accessible_organizations(g.current_user.organization_id)

    try:
        # ② chart_config / data_source_config 生成
        chart_config = json.dumps({})
        data_source_config = json.dumps({'device_id': ''})

        # position_y と display_order を別々に取得する
        max_position_y = db.session.query(
            func.max(DashboardGadgetMaster.position_y)
        ).filter(
            DashboardGadgetMaster.dashboard_group_id == form.group_id.data,
            DashboardGadgetMaster.delete_flag == False
        ).scalar() or 0

        max_order = db.session.query(
            func.max(DashboardGadgetMaster.display_order)
        ).filter(
            DashboardGadgetMaster.dashboard_group_id == form.group_id.data,
            DashboardGadgetMaster.delete_flag == False
        ).scalar() or 0

        # 表のgadget_type_idを事前に取得する
        gadget_type = db.session.query(GadgetTypeMaster).filter_by(
            gadget_type_name='表',
            delete_flag=False
        ).first()
        gadget_type_id = gadget_type.gadget_type_id

        # ③ ガジェット登録
        gadget = DashboardGadgetMaster(
            gadget_uuid=str(uuid.uuid4()),
            gadget_name=form.title.data,
            gadget_type_id=gadget_type_id,
            dashboard_group_id=form.group_id.data,
            chart_config=chart_config,
            data_source_config=data_source_config,
            position_x=0,
            position_y=max_position_y + 1,
            gadget_size=form.gadget_size.data,
            display_order=max_order + 1,
            creator=g.current_user.user_id,
            modifier=g.current_user.user_id
        )
        db.session.add(gadget)
        db.session.commit()
        modal('ガジェットを登録しました', 'success')
        return redirect(url_for('customer_dashboard.customer_dashboard'))

    except Exception as e:
        db.session.rollback()
        logger.error(f'表ガジェット登録エラー: {str(e)}')
        abort(500)
```

#### エラーハンドリング

| HTTPステータス | エラー種別 | 処理内容 | 表示内容 |
|--------------|-----------|---------|---------|
| 400 | バリデーションエラー | フォーム再表示（エラーモーダル表示） | バリデーションエラーメッセージ |
| 401 | 認証エラー | ログイン画面へリダイレクト | - |
| 404 | リソース不存在 | 404エラーモーダル表示 | 指定されたデバイスが見つかりません |
| 500 | データベースエラー | 500エラーページ表示 | データの取得に失敗しました |

---

### CSVエクスポート

**トリガー:** CSVエクスポートボタンクリック

**前提条件:**
- ガジェットが表示されている
- データが存在する

#### 処理フロー

```mermaid
flowchart TD
    Start([CSVエクスポートボタンクリック]) --> Auth[認証チェック]
    Auth --> CheckAuth{認証済み?}
    CheckAuth -->|未認証| LoginRedirect[ログイン画面へリダイレクト]
    CheckAuth -->|認証OK| Scope[データスコープ制限チェック<br>ガジェットがアクセス可能な組織に属するか確認]

    Scope --> CheckScope{スコープOK?}
    CheckScope -->|スコープ外| Error404[404エラーモーダル表示]
    CheckScope -->|スコープOK| Validate[バリデーション<br>リクエストパラメータ]

    Validate --> CheckValidate{バリデーションOK?}
    CheckValidate -->|NG| Error400[400エラーモーダル表示]
    CheckValidate -->|OK| DeviceQuery[選択中デバイス取得<br>DB dashboard_user_setting]

    DeviceQuery --> CheckDeviceQuery{DBクエリ結果}
    CheckDeviceQuery -->|失敗| Error500[500エラーモーダル表示]
    CheckDeviceQuery -->|成功| SilverQuery[センサーデータ取得<br>sensor_data_view]

    SilverQuery --> CheckSilverQuery{DBクエリ結果}
    CheckSilverQuery -->|NG| Error500
    CheckSilverQuery -->|OK| ColumnNameQuery[テーブルカラム名取得<br>DB measurement_item_master]

    ColumnNameQuery --> CheckColumnNameQuery{DBクエリ結果}
    CheckColumnNameQuery -->|NG| Error500
    CheckColumnNameQuery -->|OK| FormatCSV[CSVフォーマット変換]

    FormatCSV --> Response[CSVダウンロードレスポンス]

    LoginRedirect --> End([処理完了])
    Error404 --> End
    Error400 --> End
    Error500 --> End
    Response --> End
```

#### Flaskルート

| ルート | エンドポイント | 詳細 |
|-------|---------------|------|
| CSVエクスポート | `GET /analysis/customer-dashboard/gadgets/<gadget_uuid>?export=csv` | パスパラメータ: `gadget_uuid` クエリパラメータ: `start_datetime, end_datetime, chart_config` |

#### バリデーション

**実行タイミング:** CSVエクスポートボタン押下時（サーバーサイド）

| 項目 | ルール | エラーメッセージ |
|------|--------|-----------------|
| 開始日時 | 日付形式 | 正しい日付形式で入力してください（YYYY/MM/DD HH:mm:ss） |
| 終了日時 | 日付形式 | 正しい日付形式で入力してください（YYYY/MM/DD HH:mm:ss） |
| 開始日時 | 開始日時 < 終了日時 | 終了日時は開始日時以降の日時を入力してください |

#### 処理詳細（サーバーサイド）

**① 選択中デバイス取得**

[ガジェットデータ取得 ①](#ガジェットデータ取得) と同様のSQL（dashboard_user_setting, device_master）を実行します。

---

**② センサーデータ取得**

[ガジェットデータ取得 ①](#ガジェットデータ取得) と同様のSQL（sensor_data_view）を実行します。

**グラフ表示との差異:**

| 項目 | ガジェットデータ取得 | CSVエクスポート |
|------|----------------|--------------|
| 最大取得件数 | 1000件 | 100,000件 |
| レスポンス形式 | JSON | CSV |

---

**③ テーブルカラム名取得**

[ガジェットデータ取得 ①](#ガジェットデータ取得) と同様のSQL（measurement_item_master）を実行します。

---

**④ CSVカラム定義**

measurement_item_master から取得した display_name をヘッダーとし、「受信日時」「デバイス名称」を先頭に追加します。カラムの順序は measurement_item_id の昇順に従います。

---

**⑤ 実装例**

```python
@customer_dashboard_bp.route('/analysis/customer-dashboard/gadgets/<string:gadget_uuid>', methods=['GET'])
@require_auth
def gadget_csv_export(gadget_uuid):
    """表ガジェット CSVエクスポート"""
    if request.args.get('export') != 'csv':
        abort(404)

    accessible_org_ids = get_accessible_organizations(g.current_user.organization_id)

    # データスコープ制限チェック
    gadget = get_gadget_by_uuid(gadget_uuid)
    if not gadget or not check_gadget_access(gadget, accessible_org_ids):
        abort(404)

    # リクエストパラメータ取得・バリデーション
    start_datetime_str = request.args.get('start_datetime')
    end_datetime_str = request.args.get('end_datetime')

    if not validate_chart_params(start_datetime_str, end_datetime_str):
        abort(400)

    try:
        start_datetime = datetime.strptime(start_datetime_str, '%Y/%m/%d %H:%M:%S')
        end_datetime = datetime.strptime(end_datetime_str, '%Y/%m/%d %H:%M:%S')

        # ① 選択中デバイス取得
        user_setting = get_dashboard_user_setting(g.current_user.user_id)
        device_id = user_setting.device_id if user_setting else None

        # ② センサーデータ取得（最大10万件）
        rows = fetch_grid_data(
            device_id=device_id,
            start_datetime=start_datetime,
            end_datetime=end_datetime,
            limit=100000
        )

        # ③ テーブルカラム名取得
        columns = get_column_definition()

        # ④ データ整形
        grid_data = format_grid_data(rows, columns)

        # ⑤ CSV生成
        output = io.StringIO()
        writer = csv.writer(output)
        headers = ['受信日時', 'デバイス名称'] + [col.display_name for col in columns]
        writer.writerow(headers)

        for row_data in grid_data:
            row_values = [
                row_data.get('event_timestamp', ''),
                row_data.get('device_name', '')
            ] + [row_data.get(col.silver_data_column_name, '') for col in columns]
            writer.writerow(row_values)

        # ⑥ CSVダウンロードレスポンス
        output.seek(0)
        filename = f"sensor_data_{datetime.now().strftime('%Y%m%d%H%M%S')}.csv"
        return Response(
            output.getvalue(),
            mimetype='text/csv',
            headers={'Content-Disposition': f'attachment; filename={filename}'}
        )

    except Exception as e:
        logger.error(f'表ガジェットCSVエクスポートエラー: gadget_uuid={gadget_uuid}, error={str(e)}')
        abort(500)
```

#### エラーハンドリング

| HTTPステータス | エラー種別 | 処理内容 | 表示内容 |
|--------------|-----------|---------|---------|
| 400 | バリデーションエラー | フォーム再表示（エラーモーダル表示） | バリデーションエラーメッセージ |
| 401 | 認証エラー | ログイン画面へリダイレクト | - |
| 404 | リソース不存在 | 404エラーモーダル表示 | 指定されたデバイスが見つかりません |
| 500 | データベースエラー | 500エラーページ表示 | データの取得に失敗しました |

---

## セキュリティ実装

### 認証・認可実装

**認証方式:**
- Databricksリバースプロキシヘッダ認証（`X-Forwarded-User`）

**認可ロジック:**

組織階層に基づいて、ユーザーがアクセスできるデータを制限します。

**処理内容:**
- **全ユーザー共通**: 組織階層（`organization_closure`）でフィルタ
  - ユーザーの `organization_id` を親組織IDとして検索
  - 下位組織リスト（`subsidiary_organization_id`）を取得
  - そのリストに該当する組織のダッシュボード・ガジェットデータのみアクセス可能
  - **ロールによる条件分岐は一切行わない**

**注**: システム保守者・管理者が全データにアクセスできるのは、ルート組織（すべての組織を子組織に持つ）に所属しているため

**実装例:**
```python
def apply_dashboard_data_scope_filter(query, current_user):
    """組織階層に基づいたダッシュボードデータのスコープ制限を適用"""
    accessible_org_ids = db.session.query(
        OrganizationClosure.subsidiary_organization_id
    ).filter(
        OrganizationClosure.parent_organization_id == current_user.organization_id
    ).all()

    org_ids = [org_id[0] for org_id in accessible_org_ids]

    if not org_ids:
        return query.filter(DashboardMaster.organization_id.in_([]))

    return query.filter(DashboardMaster.organization_id.in_(org_ids))
```

### ログ出力ルール

**出力する情報:**
- リクエストID
- ユーザーID（操作者）
- 操作種別（ダッシュボード登録、更新、削除、ガジェット登録、レイアウト保存等）
- 対象リソースID（dashboard_id、group_id、gadget_id）
- 処理結果（成功/失敗）
- エラー種別（バリデーションエラー、DBエラー等）
- タイムスタンプ（UTC）

**出力しない情報（機密情報）:**
- 認証トークン
- センサーデータの具体値

**実装例:**
```python
import logging

logger = logging.getLogger(__name__)

@customer_dashboard_bp.route('/analysis/customer-dashboard/gadgets/grid/register', methods=['POST'])
@require_auth
def gadget_grid_register():
    logger.info(f'表ガジェット登録開始: user_id={g.current_user.user_id}')

    try:
        # ... 処理 ...
        logger.info(f'表ガジェット登録成功: gadget_id={gadget.gadget_id}')
        return response
    except Exception as e:
        logger.error(f'表ガジェット登録エラー: error={str(e)}')
        abort(500)
```

---

## 関連ドキュメント

- [UI仕様書](./ui-specification.md) - 画面要素・レイアウト仕様
- [README.md](./README.md) - 機能概要
- [シルバー層仕様](../../ldp-pipeline/silver-layer/README.md) - センサーデータスキーマ
- [ゴールド層仕様](../../ldp-pipeline/gold_layer/README.md) - 集計データスキーマ
- [共通仕様](../../common/common-specification.md) - 認証・セキュリティ共通仕様