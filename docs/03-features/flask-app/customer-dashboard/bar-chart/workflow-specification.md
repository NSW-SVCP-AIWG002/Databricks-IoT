# 顧客作成ダッシュボード棒グラフガジェット - ワークフロー仕様書

## 📑 目次

- [顧客作成ダッシュボード棒グラフガジェット - ワークフロー仕様書](#顧客作成ダッシュボード棒グラフガジェット---ワークフロー仕様書)
  - [📑 目次](#-目次)
  - [概要](#概要)
  - [使用するFlaskルート一覧](#使用するflaskルート一覧)
  - [ルート呼び出しマッピング](#ルート呼び出しマッピング)
    - [棒グラフガジェット](#棒グラフガジェット)
    - [棒グラフガジェット登録モーダル](#棒グラフガジェット登録モーダル)
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
    - [ガジェット登録モーダル表示](#ガジェット登録モーダル表示)
      - [処理フロー](#処理フロー-2)
      - [Flaskルート](#flaskルート-2)
      - [バリデーション](#バリデーション-2)
      - [処理詳細（サーバーサイド）](#処理詳細サーバーサイド-2)
      - [エラーハンドリング](#エラーハンドリング)
    - [ガジェット登録](#ガジェット登録)
      - [処理フロー](#処理フロー-3)
      - [Flaskルート](#flaskルート-3)
      - [バリデーション](#バリデーション-3)
      - [処理詳細（サーバーサイド）](#処理詳細サーバーサイド-3)
      - [エラーハンドリング](#エラーハンドリング-1)
    - [CSVエクスポート](#csvエクスポート)
      - [処理フロー](#処理フロー-4)
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

このドキュメントは、顧客作成ダッシュボード棒グラフ機能のユーザー操作に対する処理フロー、データベース処理、エラーハンドリングの詳細を記載します。

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
| 1 | 顧客作成ダッシュボード表示 | `/analysis/customer-dashboard` | GET | 初期表示（顧客作成ダッシュボード画面に棒グラフガジェットを埋め込み） | HTML | - |
| 2 | ガジェットデータ取得 | `/analysis/customer-dashboard/gadgets/<gadget_uuid>/data` | POST | ガジェットのグラフ表示用データ取得 | JSON (AJAX) | 非同期通信 |
| 3 | ガジェット登録画面 | `/analysis/customer-dashboard/gadgets/bar-chart/create` | GET | 棒グラフガジェット登録モーダル表示 | HTML（モーダル） | - |
| 4 | ガジェット登録実行 | `/analysis/customer-dashboard/gadgets/bar-chart/register` | POST | 棒グラフガジェット登録処理 | リダイレクト (302) | 成功時: `/analysis/customer-dashboard` |
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

### 棒グラフガジェット

| ユーザー操作 | トリガー | 呼び出すルート | パラメータ | レスポンス | エラー時の挙動 |
|-------------|---------|-------------|-----------|-----------|---------------|
| 画面初期表示 | URL直接アクセス | `GET /analysis/customer-dashboard`, `POST /analysis/customer-dashboard/gadgets/<gadget_uuid>/data` | なし | HTML（顧客作成ダッシュボード画面に棒グラフガジェットを埋め込み） | エラーページ表示 |
| 表示時間単位切替（時/日/週/月） | ボタンクリック | `POST /analysis/customer-dashboard/gadgets/<gadget_uuid>/data` | `gadget_uuid` | JSON | エラーモーダル表示 |
| 集計時間幅選択 | ドロップダウン選択 | `POST /analysis/customer-dashboard/gadgets/<gadget_uuid>/data` | `gadget_uuid` | JSON | エラーモーダル表示 |
| 時間帯選択 | デイトタイムピッカー選択 | `POST /analysis/customer-dashboard/gadgets/<gadget_uuid>/data` | `gadget_uuid` | JSON | エラーモーダル表示 |
| 更新ボタン押下 | ボタンクリック | `POST /analysis/customer-dashboard/gadgets/<gadget_uuid>/data` | `gadget_uuid` | JSON | エラーモーダル表示 |
| CSVエクスポートボタン押下 | ボタンクリック | `GET /analysis/customer-dashboard/gadgets/<gadget_uuid>?export=csv` | `gadget_uuid` | CSVダウンロード | エラーモーダル表示 |

### 棒グラフガジェット登録モーダル

| ユーザー操作 | トリガー | 呼び出すルート | パラメータ | レスポンス | エラー時の挙動 |
|-------------|---------|-------------|-----------|-----------|---------------|
| 画面初期表示 | URL直接アクセス | `GET /analysis/customer-dashboard/gadgets/bar-chart/create` | なし | HTML（モーダル） | エラーページ表示 |
| 登録ボタン押下 | ボタンクリック | `POST /analysis/customer-dashboard/gadgets/bar-chart/register` | `title, device_mode, device_id, group_id, summary_method_id, measurement_item_id, min_value, max_value, gadget_size` | リダイレクト | エラーモーダル表示 |

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
- **フィルタリングロジックは全ユーザーで共通、実質的なアクセス可能範囲に差分あり**
- システム保守者・管理者: すべてのユーザーにアクセス可能
- 販社ユーザ・サービス利用者: ログインユーザーの `organization_id` に紐づく全子組織でフィルタリング

#### 処理詳細（サーバーサイド）

[共通ワークフロー仕様書](../common/workflow-specification.md) のダッシュボード初期表示の処理詳細（①〜⑨）と同様の処理を実行します。

棒グラフガジェット固有の追加処理はありません。

---

### ガジェットデータ取得

**トリガー:** 画面初期表示時 / 表示時間単位切替時 / 集計時間幅選択時 / 時間帯選択時 / 更新ボタン押下時

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
    CheckValidate -->|OK| GetConfig[ガジェット設定取得<br>DB dashboard_gadget_master]

    GetConfig --> CheckGetConfig{DBクエリ結果}
    CheckGetConfig -->|失敗| Error500[500エラーレスポンス]
    CheckGetConfig -->|成功| CheckDeviceId[データソース設定に<br>デバイスIDが設定されているかを確認]

    CheckDeviceId --> ExistDeviceId{デバイスID設定あり?}
    ExistDeviceId -->|設定なし| GetUserSetting[ユーザー設定から選択中デバイスIDを取得]
    ExistDeviceId -->|設定あり| UnitCheck{表示単位<br>判定}

    GetUserSetting --> UnitCheck

    UnitCheck -->|時| SilverDataColumnNameQuery[シルバーデータカラム名取得<br>DB measurement_item_master]
    SilverDataColumnNameQuery --> CheckSilverDataColumnNameQuery{DBクエリ結果}
    CheckSilverDataColumnNameQuery -->|NG| Error500
    CheckSilverDataColumnNameQuery -->|OK| QuerySilver[センサーデータ取得<br>OLTP DB クエリ<br>silver_sensor_data]

    QuerySilver --> CheckQuerySilver{DBクエリ結果}
    CheckQuerySilver -->|NG| Error500
    CheckQuerySilver -->|OK| AggregateSilver[集計間隔で集約<br>1/2/3/5/10/15分]

    UnitCheck -->|日| QueryGoldDay[センサーデータ取得<br>OLTP DB クエリ<br>gold_sensor_data_hourly_summary]
    QueryGoldDay --> CheckQueryGoldDay{DBクエリ結果}
    CheckQueryGoldDay -->|NG| Error500
    CheckQueryGoldDay -->|OK| AggregateDay[1時間単位で24本取得<br>目盛り:2時間ごと]

    UnitCheck -->|週| QueryGoldWeek[センサーデータ取得<br>OLTP DB クエリ<br>gold_sensor_data_daily_summary]
    QueryGoldWeek --> CheckQueryGoldWeek{DBクエリ結果}
    CheckQueryGoldWeek -->|NG| Error500
    CheckQueryGoldWeek -->|OK| AggregateWeek[1日単位で7本取得<br>日曜〜土曜]

    UnitCheck -->|月| QueryGoldMonth[センサーデータ取得<br>OLTP DB クエリ<br>gold_sensor_data_daily_summary]
    QueryGoldMonth --> CheckQueryGoldMonth{DBクエリ結果}
    CheckQueryGoldMonth -->|NG| Error500
    CheckQueryGoldMonth -->|OK| AggregateMonth[1日単位で全日取得<br>目盛り:奇数日のみ]

    AggregateSilver --> Format[データ整形<br>labels/values配列生成]
    AggregateDay --> Format
    AggregateWeek --> Format
    AggregateMonth --> Format

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
| ガジェットデータ取得 | `POST /analysis/customer-dashboard/gadgets/<gadget_uuid>/data` | パスパラメータ: `gadget_uuid` クエリパラメータ: `display_unit, interval, base_datetime, chart_config` |

#### バリデーション

**実行タイミング:** データスコープ制限チェック完了後

**バリデーションルール:**

| 項目 | ルール | エラーメッセージ |
|------|--------|-----------------|
| 表示単位 | 許容値（hour/day/week/month） | 表示単位が不正です |
| 集計間隔（時単位のみ） | 許容値（1min, 2min, 3min, 5min, 10min, 15min） | 集計間隔が不正です |
| 基準日時 | 形式（YYYY/MM/DD HH:mm:ss） | 日付形式が不正です |

#### 処理詳細（サーバーサイド）

**① ガジェット設定取得**

**使用テーブル:** dashboard_gadget_master

**SQL詳細:**
```sql
SELECT
  gadget_id,
  gadget_uuid,
  gadget_type_id,
  chart_config,
  data_source_config
FROM
  dashboard_gadget_master
WHERE
  gadget_uuid = :gadget_uuid
  AND delete_flag = FALSE
```

**chart_config JSON スキーマ:**
```json
{
  "measurement_item_id": 1,
  "summary_method_id": 1,
  "min_value": 0.0,
  "max_value": 100.0
}
```

**data_source_config JSON スキーマ:**
```json
{
  "device_id": 12345
}
```
※ `device_id` が `null` の場合はデバイス可変モード

**サービス関数実装例:**
```python
# services/customer_dashboard/bar_chart.py
def get_gadget_by_uuid_and_user(gadget_uuid, user_id):
    """ガジェットをUUIDとユーザーIDで取得する（データスコープ制限込み）

    v_dashboard_gadget_master_by_user に user_id を渡すことで、
    ログインユーザーの所属組織に属するガジェットのみ取得できる。
    """
    return (
        db.session.query(DashboardGadgetMasterByUser)
        .filter(
            DashboardGadgetMasterByUser.gadget_uuid == gadget_uuid,
            DashboardGadgetMasterByUser.user_id == user_id,
            DashboardGadgetMasterByUser.delete_flag == False,
        )
        .first()
    )
```

---

**② デバイスID決定**

`data_source_config.device_id` を参照し、デバイスIDを決定します。

- **デバイス固定モード** (`device_id` が設定されている場合): `data_source_config.device_id` を使用
- **デバイス可変モード** (`device_id` が `null` の場合): ユーザー設定 (`dashboard_user_setting.device_id`) を使用

**SQL詳細（ユーザー設定取得）:**
```sql
SELECT
  device_id
FROM
  dashboard_user_setting
WHERE
  user_id = :current_user_id
  AND delete_flag = FALSE
```

**サービス関数実装例:**
```python
# services/customer_dashboard/bar_chart.py
def get_dashboard_user_setting(user_id):
    """ユーザーIDでダッシュボードユーザー設定を取得する"""
    if user_id is None:
        return None
    return db.session.query(DashboardUserSetting).filter_by(user_id=user_id).first()
```

---

**③ 表示単位別センサーデータ取得**

| display_unit | 参照層 | テーブル | 集計粒度 |
|-------------|-------|---------|--------|
| hour | OLTP DB | silver_sensor_data | インターバル単位（1/2/3/5/10/15分） |
| day | OLTP DB | gold_sensor_data_hourly_summary | 1時間単位（24本） |
| week | OLTP DB | gold_sensor_data_daily_summary | 1日単位（7本、日曜〜土曜） |
| month | OLTP DB | gold_sensor_data_daily_summary | 1日単位（月の全日） |

**時間範囲の決定:**

| display_unit | start | end |
|-------------|-------|-----|
| hour | base_datetime の時刻を00分00秒に切り捨て | start + 1時間 |
| day | base_datetime の日付 00:00:00 | base_datetime の日付 23:59:59 |
| week | base_datetime の週の日曜日 00:00:00 | base_datetime の週の土曜日 23:59:59 |
| month | base_datetime の月の初日 00:00:00 | base_datetime の月の最終日 23:59:59 |

**SQL詳細（display_unit=hour / OLTP DB）:**
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
  silver_sensor_data
WHERE
  device_id = :device_id
  AND event_timestamp BETWEEN :start_datetime AND :end_datetime
ORDER BY
  event_timestamp ASC
```

**SQL詳細（display_unit=hour / 測定項目マスタ）:**
```sql
SELECT
  silver_data_column_name
FROM
  measurement_item_master
WHERE
  measurement_item_id = :measurement_item_id
```

※ インターバル単位のグループ化・集計・表示項目選択はPython側で実施する（下記④参照）

**SQL詳細（display_unit=day / OLTP DB hourly）:**
```sql
SELECT
  HOUR(collection_datetime) AS collection_hour,
  summary_value
FROM
  gold_sensor_data_hourly_summary
WHERE
  device_id = :device_id
  AND summary_item = :measurement_item_id
  AND summary_method_id = :summary_method_id
  AND DATE(collection_datetime) = :target_date
ORDER BY
  collection_hour ASC
```

**SQL詳細（display_unit=week または month / OLTP DB daily）:**
```sql
SELECT
  collection_date,
  summary_value
FROM
  gold_sensor_data_daily_summary
WHERE
  device_id = :device_id
  AND summary_item = :measurement_item_id
  AND summary_method_id = :summary_method_id
  AND collection_date BETWEEN :start_date AND :end_date
ORDER BY
  collection_date ASC
```

```python
# services/customer_dashboard/bar_chart.py
def fetch_bar_chart_data(device_id, display_unit, interval, base_datetime,
                         measurement_item_id, summary_method_id, limit=100):
    """表示単位に応じたセンサーデータを取得する

    Args:
        device_id (int): デバイスID
        display_unit (str): 表示単位（hour/day/week/month）
        interval (str): 集計時間幅（display_unit=hour のみ使用）
        base_datetime (datetime): 基準日時
        measurement_item_id (int): 表示項目ID
        summary_method_id (int): 集約方法ID
        limit (int): 最大取得件数（デフォルト100）

    Returns:
        list[dict]: クエリ結果行のリスト

    Raises:
        Exception: クエリ実行失敗時
    """
    try:
        if display_unit == "hour":
            start_datetime = base_datetime.replace(minute=0, second=0, microsecond=0)
            end_datetime = start_datetime + timedelta(hours=1)
            query = text("""
                SELECT event_timestamp, external_temp, set_temp_freezer_1,
                       internal_sensor_temp_freezer_1, internal_temp_freezer_1,
                       df_temp_freezer_1, condensing_temp_freezer_1,
                       adjusted_internal_temp_freezer_1, set_temp_freezer_2,
                       internal_sensor_temp_freezer_2, internal_temp_freezer_2,
                       df_temp_freezer_2, condensing_temp_freezer_2,
                       adjusted_internal_temp_freezer_2, compressor_freezer_1,
                       compressor_freezer_2, fan_motor_1, fan_motor_2, fan_motor_3,
                       fan_motor_4, fan_motor_5, defrost_heater_output_1,
                       defrost_heater_output_2
                FROM silver_sensor_data
                WHERE device_id = :device_id
                  AND event_timestamp BETWEEN :start_datetime AND :end_datetime
                ORDER BY event_timestamp ASC
                LIMIT :limit
            """)
            result = db.session.execute(query, {
                'device_id': device_id,
                'start_datetime': start_datetime,
                'end_datetime': end_datetime,
                'limit': limit,
            })
            return [row._asdict() for row in result]

        elif display_unit == "day":
            target_date = base_datetime.date()
            query = text("""
                SELECT HOUR(collection_datetime) AS collection_hour, summary_value
                FROM gold_sensor_data_hourly_summary
                WHERE device_id = :device_id
                  AND summary_item = :measurement_item_id
                  AND summary_method_id = :summary_method_id
                  AND DATE(collection_datetime) = :target_date
                ORDER BY collection_hour ASC
                LIMIT :limit
            """)
            result = db.session.execute(query, {
                'device_id': device_id,
                'measurement_item_id': measurement_item_id,
                'summary_method_id': summary_method_id,
                'target_date': target_date,
                'limit': limit,
            })
            return [row._asdict() for row in result]

        elif display_unit == "week":
            # 当週の日曜〜土曜（weekday: 月=0, 日=6）
            weekday = base_datetime.weekday()
            days_since_sunday = (weekday + 1) % 7
            start_date = (base_datetime - timedelta(days=days_since_sunday)).date()
            end_date = start_date + timedelta(days=6)
            query = text("""
                SELECT collection_date, summary_value
                FROM gold_sensor_data_daily_summary
                WHERE device_id = :device_id
                  AND summary_item = :measurement_item_id
                  AND summary_method_id = :summary_method_id
                  AND collection_date BETWEEN :start_date AND :end_date
                ORDER BY collection_date ASC
                LIMIT :limit
            """)
            result = db.session.execute(query, {
                'device_id': device_id,
                'measurement_item_id': measurement_item_id,
                'summary_method_id': summary_method_id,
                'start_date': start_date,
                'end_date': end_date,
                'limit': limit,
            })
            return [row._asdict() for row in result]

        elif display_unit == "month":
            import calendar
            start_date = base_datetime.replace(day=1).date()
            last_day = calendar.monthrange(base_datetime.year, base_datetime.month)[1]
            end_date = base_datetime.replace(day=last_day).date()
            query = text("""
                SELECT collection_date, summary_value
                FROM gold_sensor_data_daily_summary
                WHERE device_id = :device_id
                  AND summary_item = :measurement_item_id
                  AND summary_method_id = :summary_method_id
                  AND collection_date BETWEEN :start_date AND :end_date
                ORDER BY collection_date ASC
                LIMIT :limit
            """)
            result = db.session.execute(query, {
                'device_id': device_id,
                'measurement_item_id': measurement_item_id,
                'summary_method_id': summary_method_id,
                'start_date': start_date,
                'end_date': end_date,
                'limit': limit,
            })
            return [row._asdict() for row in result]

        return []

    except Exception as e:
        logger.error(f"棒グラフデータ取得エラー: device_id={device_id}, error={str(e)}")
        raise


def get_measurement_item_column_name(measurement_item_id):
    """測定項目のシルバー層カラム名を取得する

    Returns:
        str or None: silver_data_column_name。測定項目が存在しない場合は None
    """
    item = db.session.query(MeasurementItemMaster).filter_by(
        measurement_item_id=measurement_item_id
    ).first()
    return item.silver_data_column_name if item else None
```

---

**④ データ整形**

取得データを ECharts 棒グラフ用の `labels` / `values` 配列に変換します。

| display_unit | ラベル形式 | 備考 |
|-------------|---------|------|
| hour | HH:mm | インターバル単位の開始時刻 |
| day | HH | 0〜23時（24本） |
| week | E | 日曜〜土曜（7本） |
| month | DD | 月初〜月末（目盛りはフロント側で奇数日のみ表示） |

```python
# services/customer_dashboard/bar_chart.py
INTERVAL_MINUTES = {
    '1min': 1, '2min': 2, '3min': 3,
    '5min': 5, '10min': 10, '15min': 15
}

def format_bar_chart_data(rows, display_unit, interval="10min", summary_method_id=1, column_name=None):
    if not rows:
        return {"labels": [], "values": []}

    labels, values = [], []
    if display_unit == 'hour':
        # column_name は呼び出し元で measurement_item_master から取得して引数として渡す
        interval_min = INTERVAL_MINUTES.get(interval, 10)
        groups = {}
        for row in rows:
            dt = row['event_timestamp']
            bucket = dt.replace(
                minute=(dt.minute // interval_min) * interval_min,
                second=0, microsecond=0
            )
            key = bucket.strftime('%H:%M')
            groups.setdefault(key, []).append(row[column_name])
        for key in sorted(groups):
            labels.append(key)
            values.append(aggregate_values(groups[key], summary_method_id))
    elif display_unit == 'day':
        for row in rows:
            labels.append(f"{row['collection_hour']:02d}:00")
            values.append(row['summary_value'])
    elif display_unit == 'week':
        for row in rows:
            labels.append(row['collection_date'].strftime('%a'))
            values.append(row['summary_value'])
    elif display_unit == 'month':
        for row in rows:
            labels.append(row['collection_date'].strftime('%d'))
            values.append(row['summary_value'])
    return {'labels': labels, 'values': values}
```

---

**⑤ レスポンス形式**

```json
{
  "gadget_uuid": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
  "chart_data": {
    "labels": ["00:00", "00:05", "00:10"],
    "values": [10.5, 12.3, 9.8]
  },
  "updated_at": "2026/03/05 12:00:00"
}
```

データなしの場合:
```json
{
  "gadget_uuid": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
  "chart_data": {"labels": [], "values": []},
  "updated_at": "2026/03/05 12:00:00"
}
```

---

**⑥ 実装例**

```python
# services/customer_dashboard/bar_chart.py
def validate_chart_params(display_unit, interval, base_datetime_str):
    """チャートパラメータのバリデーション

    Returns:
        str | None: エラーメッセージ（正常時は None）
    """
    if display_unit not in _VALID_DISPLAY_UNITS:
        return '表示単位が不正です'

    if interval not in INTERVAL_MINUTES:
        return '集計間隔が不正です'

    if not base_datetime_str:
        return '日付形式が不正です'

    try:
        datetime.strptime(base_datetime_str, "%Y/%m/%d %H:%M:%S")
    except (ValueError, TypeError):
        return '日付形式が不正です'

    return None


# views/analysis/customer_dashboard/bar_chart.py
def handle_gadget_data(gadget_uuid):
    """棒グラフガジェットデータ取得（AJAX）"""
    # ① ガジェット設定取得 & データスコープ制限チェック
    # v_dashboard_gadget_master_by_user に user_id と gadget_uuid を渡してスコープ制限を自動適用
    gadget = get_gadget_by_uuid_and_user(gadget_uuid, g.current_user.user_id)
    if not gadget:
        return jsonify({'error': '指定されたガジェットが見つかりません'}), 404

    # リクエストパラメータ取得・バリデーション
    params = request.get_json() or {}
    display_unit = params.get('display_unit', 'hour')
    interval = params.get('interval', '10min')
    base_datetime_str = params.get('base_datetime')

    error = validate_chart_params(display_unit, interval, base_datetime_str)
    if error:
        return jsonify({'error': error}), 400

    try:
        base_datetime = datetime.strptime(base_datetime_str, '%Y/%m/%d %H:%M:%S')

        # ② デバイスID決定
        data_source_config = json.loads(gadget.data_source_config or '{}')
        device_id = data_source_config.get('device_id')
        if device_id is None:
            setting = get_dashboard_user_setting(g.current_user.user_id)
            device_id = setting.device_id if setting else None

        chart_config = json.loads(gadget.chart_config or '{}')
        measurement_item_id = chart_config.get('measurement_item_id', 1)
        summary_method_id = chart_config.get('summary_method_id', 1)

        column_name = None
        if display_unit == 'hour':
            column_name = get_measurement_item_column_name(measurement_item_id)
            if column_name is None:
                return jsonify({'error': '測定項目が見つかりません'}), 500

        # ③ 表示単位別センサーデータ取得
        rows = fetch_bar_chart_data(
            device_id=device_id,
            display_unit=display_unit,
            interval=interval,
            base_datetime=base_datetime,
            measurement_item_id=measurement_item_id,
            summary_method_id=summary_method_id,
            limit=100,
        )

        # ④ データ整形
        chart_data = format_bar_chart_data(
            rows, display_unit, interval, summary_method_id, column_name=column_name
        )

        return jsonify({
            'gadget_uuid': gadget_uuid,
            'chart_data': chart_data,
            'updated_at': datetime.now().strftime('%Y/%m/%d %H:%M:%S'),
        })

    except Exception as e:
        g.last_exception_type = type(e).__name__
        logger.error(f'棒グラフデータ取得エラー: gadget_uuid={gadget_uuid}, error={str(e)}')
        return jsonify({'error': 'データの取得に失敗しました'}), 500
```

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
    CheckValidate -->|OK| Scope[データスコープ制限適用<br>各リソース用VIEWにuser_idを渡して<br>スコープ制限を自動適用]
    
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
    CheckGroupQuery -->|成功| DisplayItemsQuery[表示項目一覧取得<br>DB measurement_item_master]

    DisplayItemsQuery --> CheckDisplayItemsQuery{DBクエリ結果}
    CheckDisplayItemsQuery -->|失敗| Error500
    CheckDisplayItemsQuery -->|成功| OrganizationQuery[組織一覧取得<br>DB organization_master]

    OrganizationQuery --> CheckOrganizationQuery{DBクエリ結果}
    CheckOrganizationQuery -->|失敗| Error500
    CheckOrganizationQuery -->|成功| DeviceQuery[デバイス一覧取得<br>DB device_master]

    DeviceQuery --> CheckDeviceQuery{DBクエリ結果}
    CheckDeviceQuery -->|失敗| Error500
    CheckDeviceQuery -->|成功| SummaryMethodQuery[集約方法一覧取得<br>DB gold_summary_method_master]

    SummaryMethodQuery --> CheckSummaryMethodQuery{DBクエリ結果}
    CheckSummaryMethodQuery -->|失敗| Error500
    CheckSummaryMethodQuery -->|成功| Template[棒グラフガジェット登録モーダル表示]

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
| 棒グラフガジェット登録画面 | `GET /analysis/customer-dashboard/gadgets/bar-chart/create` | パラメータ: なし |

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

**サービス関数実装例:**
```python
# services/customer_dashboard/bar_chart.py
# get_dashboard_user_setting(user_id) → フロー1定義済み
```

---

**② ダッシュボード情報取得**

**使用テーブル:** dashboard_master

```sql
SELECT
  d.dashboard_id,
  d.dashboard_uuid,
  d.dashboard_name
FROM
  dashboard_master d
  INNER JOIN user_master u
    ON d.organization_id = u.organization_id
WHERE
  d.dashboard_id = :dashboard_id
  AND d.delete_flag = FALSE
  AND u.user_id = :user_id
  AND u.delete_flag = FALSE
```

**サービス関数実装例:**
```python
def get_dashboard_by_id(dashboard_id, user_id):
    """ダッシュボードをIDとユーザーIDで取得する（データスコープ制限込み）

    user_master と organization_id で JOIN し、ログインユーザーの所属組織に
    属するダッシュボードのみ取得できる。
    """
    return (
        db.session.query(DashboardMaster)
        .join(UserMaster, DashboardMaster.organization_id == UserMaster.organization_id)
        .filter(
            DashboardMaster.dashboard_id == dashboard_id,
            DashboardMaster.delete_flag == False,
            UserMaster.user_id == user_id,
            UserMaster.delete_flag == False,
        )
        .first()
    )
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

**サービス関数実装例:**
```python
def get_dashboard_groups(dashboard_id):
    """ダッシュボードIDでグループ一覧を表示順で取得する"""
    return (
        db.session.query(DashboardGroupMaster)
        .filter(
            DashboardGroupMaster.dashboard_id == dashboard_id,
            DashboardGroupMaster.delete_flag == False,
        )
        .order_by(DashboardGroupMaster.display_order.asc())
        .all()
    )
```

---

**④ 表示項目一覧取得**

**使用テーブル:** measurement_item_master

```sql
SELECT
  measurement_item_id,
  display_name,
  unit_name
FROM
  measurement_item_master
WHERE
  delete_flag = FALSE
ORDER BY
  measurement_item_id ASC
```

---

**⑤ 組織一覧取得**

**使用テーブル:** v_organization_master_by_user

```sql
SELECT
  organization_id,
  organization_name
FROM
  v_organization_master_by_user
WHERE
  user_id = :user_id
  AND delete_flag = FALSE
ORDER BY
  organization_id ASC
```

---

**⑥ デバイス一覧取得（デバイス固定モード用）**

**使用テーブル:** v_device_master_by_user

```sql
SELECT
  device_id,
  device_name,
  device_organization_id
FROM
  v_device_master_by_user
WHERE
  user_id = :user_id
  AND delete_flag = FALSE
ORDER BY
  device_id ASC
```

---

**⑦ 集約方法一覧取得**

**使用テーブル:** gold_summary_method_master

```sql
SELECT
  summary_method_id,
  summary_method_name
FROM
  gold_summary_method_master
WHERE
  delete_flag = FALSE
ORDER BY
  summary_method_id ASC
```

**サービス関数実装例:**
```python
# services/customer_dashboard/bar_chart.py
def get_bar_chart_create_context(user_id):
    """棒グラフ登録モーダル用データを取得する

    Args:
        user_id: ログインユーザーID（VIEWのスコープ制限に使用）

    Returns:
        dict: measurement_items, organizations, devices をキーに持つ dict
    """
    measurement_items = (
        db.session.query(MeasurementItemMaster)
        .filter(MeasurementItemMaster.delete_flag == False)
        .order_by(MeasurementItemMaster.measurement_item_id.asc())
        .all()
    )
    organizations = (
        db.session.query(VOrganizationMasterByUser)
        .filter(
            VOrganizationMasterByUser.user_id == user_id,
            VOrganizationMasterByUser.delete_flag == False,
        )
        .order_by(VOrganizationMasterByUser.organization_id.asc())
        .all()
    )
    devices = (
        db.session.query(VDeviceMasterByUser)
        .filter(
            VDeviceMasterByUser.user_id == user_id,
            VDeviceMasterByUser.delete_flag == False,
        )
        .order_by(VDeviceMasterByUser.device_id.asc())
        .all()
    )
    summary_methods = (
        db.session.query(GoldSummaryMethodMaster)
        .filter(GoldSummaryMethodMaster.delete_flag == False)
        .order_by(GoldSummaryMethodMaster.summary_method_id.asc())
        .all()
    )
    return {
        'measurement_items': measurement_items,
        'organizations': organizations,
        'devices': devices,
        'summary_methods': summary_methods,
    }
```

---

**⑧ 実装例**

```python
# forms/customer_dashboard/bar_chart.py
class BarChartGadgetForm(FlaskForm):
    """棒グラフガジェット登録フォーム"""

    title = StringField(
        'タイトル',
        validators=[
            DataRequired(message='タイトルを入力してください'),
            Length(max=20, message='タイトルは20文字以内で入力してください'),
        ]
    )
    device_mode = SelectField(
        '表示デバイス',
        choices=[('fixed', 'デバイス固定'), ('variable', 'デバイス可変')],
        validators=[DataRequired(message='表示デバイスを選択してください')],
    )
    device_id = SelectField('デバイス', coerce=int, validators=[Optional()])
    group_id = SelectField('グループ', coerce=int, validators=[DataRequired(message='グループを選択してください')])
    summary_method_id = SelectField('集約方法', coerce=int, validators=[DataRequired(message='集約方法を選択してください')])
    measurement_item_id = SelectField('表示項目', coerce=int, validators=[DataRequired(message='表示項目を選択してください')])
    min_value = FloatField('最小値', validators=[Optional()])
    max_value = FloatField('最大値', validators=[Optional()])

    def validate(self, extra_validators=None):
        result = super().validate(extra_validators)
        if self.device_mode.data == 'fixed' and (self.device_id.data is None or self.device_id.data == 0):
            self.device_id.errors.append('デバイスを選択してください')
            result = False
        return result

    def validate_min_value(self, field):
        from wtforms import ValidationError as WTFormsValidationError
        if field.data is not None and self.max_value.data is not None:
            if field.data >= self.max_value.data:
                raise WTFormsValidationError('最小値は最大値より小さい値を入力してください')

    def validate_max_value(self, field):
        from wtforms import ValidationError as WTFormsValidationError
        if field.data is not None and self.min_value.data is not None:
            if field.data <= self.min_value.data:
                raise WTFormsValidationError('最大値は最小値より大きい値を入力してください')

    gadget_size = SelectField(
        '部品サイズ',
        choices=[('2x2', '2x2'), ('2x4', '2x4')],
        validators=[DataRequired(message='部品サイズを選択してください')],
    )


# views/analysis/customer_dashboard/bar_chart.py
def handle_gadget_create(gadget_type):
    """棒グラフガジェット登録モーダル表示"""
    user_id = g.current_user.user_id

    # ① ユーザー設定取得
    setting = get_dashboard_user_setting(user_id)
    if setting is None:
        abort(404)

    # ② ダッシュボード情報取得（user_master JOIN でスコープ制限を適用）
    dashboard = get_dashboard_by_id(setting.dashboard_id, user_id)
    if dashboard is None:
        abort(404)

    # ③ ダッシュボードグループ一覧取得
    groups = get_dashboard_groups(dashboard.dashboard_id)

    # ④〜⑦ 表示項目・組織・デバイス・集約方法一覧取得（VIEWでスコープ制限を自動適用）
    try:
        context = get_bar_chart_create_context(user_id)
    except Exception as e:
        logger.error(f'棒グラフ登録モーダル表示エラー: {str(e)}')
        abort(500)

    form = BarChartGadgetForm()
    form.device_id.choices = [(0, '選択してください')] + [
        (d.device_id, d.device_name) for d in context['devices']
    ]
    form.group_id.choices = [(0, '選択してください')] + [
        (gr.dashboard_group_id, gr.dashboard_group_name) for gr in groups
    ]
    form.summary_method_id.choices = [(0, '選択してください')] + [
        (sm.summary_method_id, sm.summary_method_name) for sm in context['summary_methods']
    ]
    form.measurement_item_id.choices = [(0, '選択してください')] + [
        (m.measurement_item_id, m.display_name) for m in context['measurement_items']
    ]
    return render_template(
        'analysis/customer_dashboard/gadgets/modals/bar_chart.html',
        form=form,
        gadget_type=gadget_type,
        groups=groups,
        **context,
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
    CheckValidate -->|OK| ChekcDeviceMode{表示デバイス選択?}

    ChekcDeviceMode -->|デバイス固定| DeviceQuery[デバイス存在&データスコープチェック]
    ChekcDeviceMode -->|デバイス可変| NotSetDeviceId[データソース設定のデバイスIDは未設定]

    NotSetDeviceId --> Insert[ガジェット登録<br> DB dashboard_gadget_master INSERT]

    DeviceQuery --> CheckDeviceQuery{デバイス存在&データスコープOK?}
    CheckDeviceQuery -->|NG| Error404[404エラーモーダル表示]
    CheckDeviceQuery -->|OK| Insert

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
| 棒グラフガジェット登録実行 | `POST /analysis/customer-dashboard/gadgets/bar-chart/register` | フォームデータ: `title, device_mode, device_id, group_id, summary_method_id, measurement_item_id, min_value, max_value, gadget_size` |

#### バリデーション

**実行タイミング:** フォーム送信時（サーバーサイド）

| 項目 | ルール | エラーメッセージ |
|------|--------|-----------------|
| タイトル | 必須 | タイトルを入力してください |
| タイトル | 最大20文字 | タイトルは20文字以内で入力してください |
| 表示デバイス | 必須 | 表示デバイスを選択してください |
| デバイス（デバイス固定時のみ） | 必須 | デバイスを選択してください |
| グループ | 必須 | グループを選択してください |
| 集約方法 | 必須 | 集約方法を選択してください |
| 表示項目 | 必須 | 表示項目を選択してください |
| 最小値 | 数値、最大値未満 | 最小値は最大値より小さい値を入力してください |
| 最大値 | 数値、最小値超過 | 最大値は最小値より大きい値を入力してください |
| 部品サイズ | 必須 | 部品サイズを選択してください |

#### 処理詳細（サーバーサイド）

**① デバイス存在&データスコープチェック（デバイス固定モード時のみ）**

**使用テーブル:** v_device_master_by_user

```sql
SELECT
  device_id,
  device_name,
  device_organization_id
FROM
  v_device_master_by_user
WHERE
  device_id = :device_id
  AND user_id = :user_id
  AND delete_flag = FALSE
```

**サービス関数実装例:**
```python
# services/customer_dashboard/bar_chart.py
def check_device_access(device_id, user_id):
    """デバイスの存在とデータスコープをチェックする

    Args:
        device_id (int): デバイスID
        user_id (int): ログインユーザーID

    Returns:
        device object or None: デバイスが存在しアクセス可能な場合はデバイス、それ以外は None
    """
    return (
        db.session.query(VDeviceMasterByUser)
        .filter(
            VDeviceMasterByUser.device_id == device_id,
            VDeviceMasterByUser.user_id == user_id,
            VDeviceMasterByUser.delete_flag == False,
        )
        .first()
    )
```

---

**② chart_config / data_source_config JSONスキーマ**

```json
// chart_config
{
  "measurement_item_id": 1,
  "summary_method_id": 1,
  "min_value": 0.0,
  "max_value": 100.0
}

// data_source_config（デバイス固定モード）
{"device_id": 12345}

// data_source_config（デバイス可変モード）
{"device_id": null}
```

---

**③ ガジェット登録**

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

**サービス関数実装例:**
```python
# services/customer_dashboard/bar_chart.py
def register_bar_chart_gadget(params, current_user_id):
    """棒グラフガジェットを登録する

    Args:
        params (dict): 登録パラメータ
        current_user_id (int): 操作ユーザーID

    Returns:
        int: 登録されたガジェットの gadget_id

    Raises:
        ValidationError: バリデーションエラー時
        NotFoundError: ガジェット種別が見つからない場合
        Exception: DB エラー時
    """
    # バリデーション
    validate_gadget_registration(params)

    # デバイス固定モード
    device_id = None
    if params.get("device_mode") == "fixed":
        device_id = params.get("device_id")

    chart_config = json.dumps({
        "measurement_item_id": params.get("measurement_item_id"),
        "summary_method_id": params.get("summary_method_id"),
        "min_value": params.get("min_value"),
        "max_value": params.get("max_value"),
    })
    data_source_config = json.dumps({"device_id": device_id})

    max_position_y = db.session.query(
        func.max(DashboardGadgetMaster.position_y)
    ).filter(
        DashboardGadgetMaster.dashboard_group_id == params.get("group_id"),
        DashboardGadgetMaster.delete_flag == False,
    ).scalar() or 0

    max_order = db.session.query(
        func.max(DashboardGadgetMaster.display_order)
    ).filter(
        DashboardGadgetMaster.dashboard_group_id == params.get("group_id"),
        DashboardGadgetMaster.delete_flag == False,
    ).scalar() or 0

    gadget_type = db.session.query(GadgetTypeMaster).filter_by(
        gadget_type_name='棒グラフ', delete_flag=False
    ).first()
    if not gadget_type:
        raise NotFoundError("ガジェット種別が見つかりません")

    gadget = DashboardGadgetMaster(
        gadget_uuid=str(uuid.uuid4()),
        gadget_name=params.get("title"),
        gadget_type_id=gadget_type.gadget_type_id,
        dashboard_group_id=params.get("group_id"),
        chart_config=chart_config,
        data_source_config=data_source_config,
        position_x=0,
        position_y=max_position_y + 1,
        gadget_size=GADGET_SIZE_TO_INT[params.get("gadget_size")],
        display_order=max_order + 1,
        creator=current_user_id,
        modifier=current_user_id,
    )

    try:
        db.session.add(gadget)
        db.session.commit()
        return gadget.gadget_id
    except Exception as e:
        db.session.rollback()
        logger.error("棒グラフガジェット登録エラー", exc_info=True)
        raise
```

---

**④ 実装例**

```python
# views/analysis/customer_dashboard/bar_chart.py
def handle_gadget_register(gadget_type):
    """棒グラフガジェット登録実行"""
    user_id = g.current_user.user_id

    form = BarChartGadgetForm()
    # device_id / measurement_item_id / group_id / summary_method_id はJS動的ロードのため送信値をそのまま choices に設定
    submitted_device_id = request.form.get('device_id', type=int) or 0
    form.device_id.choices = [(submitted_device_id, '')]
    submitted_measurement_item_id = request.form.get('measurement_item_id', type=int) or 0
    form.measurement_item_id.choices = [(submitted_measurement_item_id, '')]
    submitted_group_id = request.form.get('group_id', type=int) or 0
    submitted_summary_method_id = request.form.get('summary_method_id', type=int) or 0
    form.group_id.choices = [(submitted_group_id, '')]
    form.summary_method_id.choices = [(submitted_summary_method_id, '')]

    if not form.validate_on_submit():
        try:
            context = get_bar_chart_create_context(user_id)
            setting = get_dashboard_user_setting(user_id)
            groups = get_dashboard_groups(setting.dashboard_id) if setting else []
        except Exception as e:
            logger.error(f'棒グラフガジェット登録コンテキスト取得エラー: {str(e)}')
            abort(500)
        return render_template(
            'analysis/customer_dashboard/gadgets/modals/bar_chart.html',
            form=form,
            gadget_type=gadget_type,
            groups=groups,
            **context,
        ), 400

    # ① デバイス固定モードの場合: デバイス存在&データスコープチェック（VIEWでスコープ制限を自動適用）
    if form.device_mode.data == 'fixed':
        if check_device_access(form.device_id.data, user_id) is None:
            abort(404)

    params = {
        'title': form.title.data,
        'device_mode': form.device_mode.data,
        'device_id': form.device_id.data,
        'group_id': form.group_id.data,
        'summary_method_id': form.summary_method_id.data,
        'measurement_item_id': form.measurement_item_id.data,
        'min_value': form.min_value.data,
        'max_value': form.max_value.data,
        'gadget_size': form.gadget_size.data,
    }

    try:
        # ②③ ガジェット登録（chart_config/data_source_config生成、DB登録）
        register_bar_chart_gadget(
            params=params,
            current_user_id=g.current_user.user_id,
        )
        return jsonify({'message': 'ガジェットを登録しました'})

    except NotFoundError:
        abort(404)
    except Exception as e:
        logger.error(f'棒グラフガジェット登録エラー: {str(e)}')
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
    CheckValidate -->|OK| GetConfig[ガジェット設定取得<br>DB dashboard_gadget_master]

    GetConfig --> CheckGetConfig{DBクエリ結果}
    CheckGetConfig -->|失敗| Error500[500エラーモーダル表示]
    CheckGetConfig -->|成功| CheckDeviceId[データソース設定に<br>デバイスIDが設定されているかを確認]

    CheckDeviceId --> ExistDeviceId{デバイスID設定あり?}
    ExistDeviceId -->|設定なし| GetUserSetting[ユーザー設定から選択中デバイスIDを取得]
    ExistDeviceId -->|設定あり| UnitCheck{表示単位<br>判定}

    GetUserSetting --> UnitCheck

    UnitCheck -->|時| QuerySilver[センサーデータ取得<br>OLTP DB クエリ<br>silver_sensor_data]
    QuerySilver --> AggregateSilver[集計間隔で集約<br>1/2/3/5/10/15分]

    UnitCheck -->|日| QueryGoldDay[センサーデータ取得<br>OLTP DB クエリ<br>gold_sensor_data_hourly_summary]
    QueryGoldDay --> AggregateDay[1時間単位で24本取得<br>目盛り:2時間ごと]

    UnitCheck -->|週| QueryGoldWeek[センサーデータ取得<br>OLTP DB クエリ<br>gold_sensor_data_daily_summary]
    QueryGoldWeek --> AggregateWeek[1日単位で7本取得<br>日曜〜土曜]

    UnitCheck -->|月| QueryGoldMonth[センサーデータ取得<br>OLTP DB クエリ<br>gold_sensor_data_daily_summary]
    QueryGoldMonth --> AggregateMonth[1日単位で全日取得<br>目盛り:奇数日のみ]

    AggregateSilver --> FormatCSV[CSVフォーマット変換]
    AggregateDay --> FormatCSV
    AggregateWeek --> FormatCSV
    AggregateMonth --> FormatCSV

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
| CSVエクスポート | `GET /analysis/customer-dashboard/gadgets/<gadget_uuid>?export=csv` | パスパラメータ: `gadget_uuid` クエリパラメータ: `display_unit, interval, base_datetime, chart_config` |

#### バリデーション

**実行タイミング:** CSVエクスポートボタン押下時（サーバーサイド）

| 項目 | ルール | エラーメッセージ |
|------|--------|-----------------|
| 表示単位 | 許容値（hour/day/week/month） | 表示単位が不正です |
| 集計間隔（時単位のみ） | 許容値（1min, 2min, 3min, 5min, 10min, 15min） | 集計間隔が不正です |
| 基準日時 | 形式（YYYY/MM/DD HH:mm:ss） | 日付形式が不正です |


#### 処理詳細（サーバーサイド）

**① ガジェット設定取得**

[ガジェットデータ取得 ①](#ガジェットデータ取得) と同様のSQL（dashboard_gadget_master）を実行します。

---

**② デバイスID決定**

[ガジェットデータ取得 ②](#ガジェットデータ取得) と同様のロジックを適用します。

---

**③ 表示単位別センサーデータ取得**

[ガジェットデータ取得 ③](#ガジェットデータ取得) と同様のSQL（Silver/Gold層）を実行します。

**グラフ表示との差異:**

| 項目 | ガジェットデータ取得 | CSVエクスポート |
|------|----------------|--------------|
| 最大取得件数 | 100件 | 100,000件 |
| レスポンス形式 | JSON | CSV |

---

**④ CSVカラム定義**

| カラム名 | 内容 | 形式 |
|---------|------|------|
| timestamp | 日時ラベル | 表示単位に応じた形式（HH:mm / HH:00 / MM/DD） |
| value | センサー値 | float（小数点2桁） |

---

**⑤ 実装例**

```python
# services/customer_dashboard/bar_chart.py
def get_device_name_by_id(device_id):
    """デバイスIDからデバイス名を取得する

    Returns:
        str: デバイス名。未登録または削除済みの場合は '--'
    """
    if device_id is None:
        return '--'
    device = db.session.query(DeviceMaster).filter_by(
        device_id=device_id,
        delete_flag=False,
    ).first()
    return device.device_name if device else '--'


def get_measurement_item_legend_name(measurement_item_id):
    """測定項目IDから凡例名（表示名＋単位）を取得する

    Returns:
        str: "表示名（単位）" 形式。未登録の場合は空文字
    """
    item = db.session.query(MeasurementItemMaster).filter_by(
        measurement_item_id=measurement_item_id,
    ).first()
    if not item:
        return ''
    return f"{item.display_name}（{item.unit_name}）"


def generate_bar_chart_csv(chart_data, display_unit, base_datetime, device_name, legend_name):
    """チャートデータから CSV 文字列を生成する

    Args:
        chart_data (dict): {"labels": [...], "values": [...]}
        display_unit (str): 表示単位（hour/day/week/month）
        base_datetime (datetime): 基準日時（日付補完に使用）
        device_name (str): デバイス名（列1）
        legend_name (str): 凡例名（列3ヘッダー、例: "外気温度（℃）"）

    Returns:
        str: CSV 文字列（BOM付き UTF-8）
    """
    output = io.StringIO()
    writer = csv.writer(output)
    time_col = _CSV_TIME_COL_HEADERS.get(display_unit, "時間")
    writer.writerow(["デバイス名", time_col, legend_name])
    for label, value in zip(chart_data["labels"], chart_data["values"]):
        ts = _csv_timestamp(label, display_unit, base_datetime)
        writer.writerow([device_name, ts, f"{value:.2f}"])
    return '\ufeff' + output.getvalue()


# views/analysis/customer_dashboard/bar_chart.py
def handle_gadget_csv_export(gadget_uuid):
    """棒グラフガジェット CSVエクスポート"""
    if request.args.get('export') != 'csv':
        abort(404)

    # ① ガジェット設定取得 & データスコープ制限チェック
    # v_dashboard_gadget_master_by_user に user_id と gadget_uuid を渡してスコープ制限を自動適用
    gadget = get_gadget_by_uuid_and_user(gadget_uuid, g.current_user.user_id)
    if not gadget:
        abort(404)

    # リクエストパラメータ取得・バリデーション
    display_unit = request.args.get('display_unit', 'hour')
    interval = request.args.get('interval', '10min')
    base_datetime_str = request.args.get('base_datetime')

    if validate_chart_params(display_unit, interval, base_datetime_str):
        abort(400)

    try:
        # ② デバイスID決定
        data_source_config = json.loads(gadget.data_source_config or '{}')
        device_id = data_source_config.get('device_id')
        if device_id is None:
            setting = get_dashboard_user_setting(g.current_user.user_id)
            device_id = setting.device_id if setting else None

        chart_config = json.loads(gadget.chart_config or '{}')
        measurement_item_id = chart_config.get('measurement_item_id', 1)
        summary_method_id = chart_config.get('summary_method_id', 1)
        base_datetime = datetime.strptime(base_datetime_str, '%Y/%m/%d %H:%M:%S')

        column_name = None
        if display_unit == 'hour':
            column_name = get_measurement_item_column_name(measurement_item_id)
            if column_name is None:
                abort(500)

        # ③ センサーデータ取得（最大10万件）
        rows = fetch_bar_chart_data(
            device_id=device_id,
            display_unit=display_unit,
            interval=interval,
            base_datetime=base_datetime,
            measurement_item_id=measurement_item_id,
            summary_method_id=summary_method_id,
            limit=100_000,
        )
        chart_data = format_bar_chart_data(
            rows, display_unit, interval, summary_method_id, column_name=column_name
        )

        # ④ CSV生成（デバイス名、時間列名、凡例名を含む3カラム形式）
        device_name = get_device_name_by_id(device_id)
        legend_name = get_measurement_item_legend_name(measurement_item_id)
        csv_content = generate_bar_chart_csv(chart_data, display_unit, base_datetime, device_name, legend_name)

        # ⑤ CSVダウンロードレスポンス
        filename = f"sensor_data_{datetime.now().strftime('%Y%m%d%H%M%S')}.csv"
        return Response(
            csv_content,
            mimetype='text/csv',
            headers={'Content-Disposition': f'attachment; filename={filename}'},
        )

    except Exception as e:
        logger.error(f'棒グラフCSVエクスポートエラー: gadget_uuid={gadget_uuid}, error={str(e)}')
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
Databricksリバースプロキシヘッダ認証（`X-Forwarded-User`）

**認可ロジック:**
組織階層に基づいて、ユーザーがアクセスできるデータを制限します。

**処理内容:**
- **全ユーザー共通**: 各リソース用VIEW（`v_dashboard_gadget_master_by_user` 等）に `user_id` を渡すことでスコープ制限を自動適用
  - VIEWが内部でユーザーの所属組織（`user_master.organization_id`）と一致するデータのみ返す
  - **ロールによる条件分岐は一切行わない**

**注**:
- システム保守者・管理者が全データにアクセスできるのは、ルート組織（すべての組織を子組織に持つ）に所属しているため
- センサーデータ（`silver_sensor_data` 等）はOLTP DBに格納されており、VIEWが存在しないため、データ取得の度にデバイスIDを条件として直接クエリする

**実装例:**
```python
# 組織一覧取得
def get_organizations():
    # v_organization_master_by_user に user_id を渡すだけでスコープ制限が自動適用される
    return (
        db.session.query(OrganizationMasterByUser)
        .filter(
            OrganizationMasterByUser.user_id == g.current_user.user_id,
            OrganizationMasterByUser.delete_flag == False,
        )
        .order_by(OrganizationMasterByUser.organization_id)
        .all()
    )

# シルバー層センサーデータ取得（OLTP DB / device_id で直接クエリ）
def get_silver_sensor_data(device_id, start_datetime, end_datetime):
    # device_id はガジェット設定またはユーザー設定から取得済みのため、直接条件に指定する
    query = text("""
        SELECT event_timestamp, external_temp, set_temp_freezer_1,
               internal_sensor_temp_freezer_1, internal_temp_freezer_1,
               df_temp_freezer_1, condensing_temp_freezer_1,
               adjusted_internal_temp_freezer_1
        FROM silver_sensor_data
        WHERE device_id = :device_id
          AND event_timestamp BETWEEN :start_datetime AND :end_datetime
        ORDER BY event_timestamp ASC
        LIMIT 100
    """)
    result = db.session.execute(query, {
        'device_id': device_id,
        'start_datetime': start_datetime,
        'end_datetime': end_datetime,
    })
    return [row._asdict() for row in result]
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

@customer_dashboard_bp.route('/analysis/customer-dashboard/dashboards/register', methods=['POST'])
@require_auth
def dashboard_register():
    logger.info(f'ダッシュボード登録開始: user_id={g.current_user.user_id}')

    try:
        # ... 処理 ...
        logger.info(f'ダッシュボード登録成功: dashboard_id={dashboard.dashboard_id}')
        return response
    except Exception as e:
        logger.error(f'ダッシュボード登録エラー: error={str(e)}')
        abort(500)
```

---

## 関連ドキュメント

- [UI仕様書](./ui-specification.md) - 画面要素・レイアウト仕様
- [README.md](./README.md) - 機能概要
- [シルバー層仕様](../../ldp-pipeline/silver-layer/README.md) - センサーデータスキーマ
- [ゴールド層仕様](../../ldp-pipeline/gold_layer/README.md) - 集計データスキーマ
- [共通仕様](../../common/common-specification.md) - 認証・セキュリティ共通仕様
