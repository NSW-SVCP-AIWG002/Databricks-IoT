# Deltaテーブル最適化ジョブ仕様書

## 目次

- [Deltaテーブル最適化ジョブ仕様書](#deltaテーブル最適化ジョブ仕様書)
  - [目次](#目次)
  - [概要](#概要)
    - [このドキュメントの役割](#このドキュメントの役割)
    - [対象機能](#対象機能)
    - [ジョブ一覧](#ジョブ一覧)
  - [キュークリーンアップジョブ仕様](#キュークリーンアップジョブ仕様)
    - [ジョブ概要](#ジョブ概要)
    - [処理フロー](#処理フロー)
    - [処理コード](#処理コード)
    - [クリーンアップ設定](#クリーンアップ設定)
  - [Delta Lakeメンテナンスジョブ仕様](#delta-lakeメンテナンスジョブ仕様)
    - [日次OPTIMIZEジョブ](#日次optimizeジョブ)
      - [ジョブ概要](#ジョブ概要-1)
      - [処理フロー](#処理フロー-1)
      - [処理コード](#処理コード-1)
      - [OPTIMIZE設定](#optimize設定)
    - [週次VACUUMジョブ](#週次vacuumジョブ)
      - [ジョブ概要](#ジョブ概要-2)
      - [処理フロー](#処理フロー-2)
      - [処理コード](#処理コード-2)
      - [VACUUM設定](#vacuum設定)
    - [チェックポイントクリーンアップジョブ](#チェックポイントクリーンアップジョブ)
      - [ジョブ概要](#ジョブ概要-3)
      - [処理フロー](#処理フロー-3)
      - [処理コード](#処理コード-3)
      - [クリーンアップ設定](#クリーンアップ設定-1)
  - [関連ドキュメント](#関連ドキュメント)
  - [変更履歴](#変更履歴)

---

## 概要

このドキュメントは、Databricks Workflowとして実装するDeltaテーブル最適化ジョブ機能の詳細を記載します。

### このドキュメントの役割

- Delta Lakeメンテナンス処理（OPTIMIZE、VACUUM、チェックポイントクリーンアップ）

### 対象機能

| 機能ID | 機能名             | 処理内容                           |
| ------ | ------------------ | ---------------------------------- |
| OP-001 | データメンテナンス | Delta Lakeテーブルの最適化・圧縮   |
| OP-002 | クリーンアップ     | 古いデータ・チェックポイントの削除 |

### ジョブ一覧

| ジョブ名              | 実行間隔      | 説明                               |
| --------------------- | ------------- | ---------------------------------- |
| silver_table_optimize | 日次（02:00） | Silver層テーブルのOPTIMIZE実行     |
| silver_table_vacuum   | 日次（04:00） | Silver層テーブルのVACUUM実行       |
| gold_table_optimize   | 日次（02:00） | Gold層テーブルのOPTIMIZE実行       |
| gold_table_vacuum     | 日次（04:00） | Gold層テーブルのVACUUM実行         |
| checkpoint_cleanup    | 日次（05:00） | 古いチェックポイントファイルの削除 |

---

## キュークリーンアップジョブ仕様

### ジョブ概要

| 項目             | 設定値                              |
| ---------------- | ----------------------------------- |
| ジョブ名         | email_queue_cleanup                 |
| 実行方式         | Databricks Workflow                 |
| 実行間隔         | 日次（cron: `0 3 * * *`）毎日 03:00 |
| クラスタ         | Jobs Compute（サーバーレス推奨）    |
| タイムアウト     | 30分                                |
| リトライポリシー | 失敗時リトライなし                  |

### 処理フロー

```mermaid
flowchart TD
    Start([ジョブ開始]) --> Count[削除対象件数をカウント<br>30日経過したSENT/FAILEDレコード]
    Count --> Check{レコード<br>あり?}
    Check -->|なし| End([ジョブ終了])
    Check -->|あり| Delete[対象レコードを削除]
    Delete --> Log[削除件数を出力]
    Log --> End
```

### 処理コード

送信完了または失敗したレコードを定期的に削除する。

```python
def cleanup_email_queue():
    """30日経過したSENT/FAILEDレコードを削除"""
    import pymysql
    import pymysql.cursors

    db_config = {
        "host": dbutils.secrets.get("scope", "mysql-host"),
        "port": int(dbutils.secrets.get("scope", "mysql-port")),
        "user": dbutils.secrets.get("scope", "mysql-user"),
        "password": dbutils.secrets.get("scope", "mysql-password"),
        "database": dbutils.secrets.get("scope", "mysql-database"),
        "cursorclass": pymysql.cursors.DictCursor,
        "charset": "utf8mb4",
    }

    with pymysql.connect(**db_config) as conn:
        with conn.cursor() as cursor:
            # 削除対象件数を確認
            cursor.execute("""
                SELECT COUNT(*) as cnt
                FROM email_notification_queue
                WHERE status IN ('SENT', 'FAILED')
                  AND processed_time < DATE_SUB(NOW(), INTERVAL 30 DAY)
            """)
            count_before = cursor.fetchone()["cnt"]

        print(f"削除対象レコード数: {count_before}")

        if count_before == 0:
            print("削除対象レコードなし")
            return

        with conn.cursor() as cursor:
            cursor.execute("""
                DELETE FROM email_notification_queue
                WHERE status IN ('SENT', 'FAILED')
                  AND processed_time < DATE_SUB(NOW(), INTERVAL 30 DAY)
            """)
        conn.commit()
        print(f"削除完了: {count_before}件")


# ジョブ実行
cleanup_email_queue()
```

### クリーンアップ設定

| 項目     | 設定値                | 説明                                   |
| -------- | --------------------- | -------------------------------------- |
| 保持期間 | 30日                  | 処理完了から30日経過したレコードを削除 |
| 対象     | SENT/FAILEDステータス | 処理済みレコードのみ削除               |

---

## Delta Lakeメンテナンスジョブ仕様

Delta Lakeテーブルのパフォーマンスを維持するための定期メンテナンスジョブ。

### 日次OPTIMIZEジョブ

小ファイルを最適なサイズに統合し、クエリパフォーマンスを向上させる。

#### ジョブ概要

| 項目             | 設定値                         |
| ---------------- | ------------------------------ |
| ジョブ名         | silver_table_optimize          |
| 実行方式         | Databricks Workflow            |
| 実行間隔         | 日次（cron: `0 2 * * *`）02:00 |
| クラスタ         | Jobs Compute                   |
| タイムアウト     | 2時間                          |
| リトライポリシー | 失敗時1回リトライ              |

#### 処理フロー

```mermaid
flowchart TD
    Start([ジョブ開始]) --> GetTables[対象テーブル一覧を取得]
    GetTables --> Loop[各テーブルを処理]

    Loop --> Optimize[OPTIMIZE実行]
    Optimize --> Result{成功?}

    Result -->|成功| Metrics[メトリクス出力<br>統合/削除ファイル数]
    Result -->|失敗| Error[エラー出力]

    Metrics --> Next{次の<br>テーブル?}
    Error --> Next

    Next -->|あり| Loop
    Next -->|なし| End([ジョブ終了])
```

#### 処理コード

```python
def optimize_silver_tables():
    """Silver層テーブルのOPTIMIZE実行"""

    # 対象テーブル一覧
    tables = [
        "iot_catalog.silver.silver_sensor_data"
    ]

    for table in tables:
        print(f"OPTIMIZE開始: {table}")
        try:
            result = spark.sql(f"OPTIMIZE {table}")
            metrics = result.first()
            print(f"  - 統合ファイル数: {metrics['numFilesAdded']}")
            print(f"  - 削除ファイル数: {metrics['numFilesRemoved']}")
            print(f"OPTIMIZE完了: {table}")
        except Exception as e:
            print(f"OPTIMIZEエラー: {table} - {str(e)}")

    print("全テーブルのOPTIMIZE完了")


# ジョブ実行
optimize_silver_tables()
```

#### OPTIMIZE設定

| 項目               | 設定値                     | 説明                             |
| ------------------ | -------------------------- | -------------------------------- |
| 対象テーブル       | Silver層全テーブル         | センサーデータ、状態             |
| 実行タイミング     | 毎日 02:00（低負荷時間帯） | ストリーミング処理への影響を軽減 |
| 自動コンパクション | 有効（テーブル設定）       | 日次に加えて自動実行も併用       |

### 週次VACUUMジョブ

削除済みファイルを物理的に削除し、ストレージ使用量を削減する。

#### ジョブ概要

| 項目             | 設定値                             |
| ---------------- | ---------------------------------- |
| ジョブ名         | silver_table_vacuum                |
| 実行方式         | Databricks Workflow                |
| 実行間隔         | 週次（cron: `0 4 * * 0`）日曜04:00 |
| クラスタ         | Jobs Compute                       |
| タイムアウト     | 4時間                              |
| リトライポリシー | 失敗時1回リトライ                  |

#### 処理フロー

```mermaid
flowchart TD
    Start([ジョブ開始]) --> GetTables[対象テーブル一覧を取得]
    GetTables --> Loop[各テーブルを処理]

    Loop --> Before[VACUUM前のファイル数を取得]
    Before --> Vacuum[VACUUM実行<br>保持期間: 168時間]
    Vacuum --> Result{成功?}

    Result -->|成功| After[VACUUM後のファイル数を取得]
    After --> Metrics[メトリクス出力<br>削除前後のファイル数]
    Result -->|失敗| Error[エラー出力]

    Metrics --> Next{次の<br>テーブル?}
    Error --> Next

    Next -->|あり| Loop
    Next -->|なし| End([ジョブ終了])
```

#### 処理コード

```python
def vacuum_silver_tables():
    """Silver層テーブルのVACUUM実行"""

    # 保持期間（時間）
    RETAIN_HOURS = 168  # 7日

    # 対象テーブル一覧
    tables = [
        "iot_catalog.silver.silver_sensor_data"
    ]

    for table in tables:
        print(f"VACUUM開始: {table}")
        try:
            # VACUUM実行前のファイル数を取得
            before_files = spark.sql(f"DESCRIBE DETAIL {table}").first()["numFiles"]

            # VACUUM実行
            spark.sql(f"VACUUM {table} RETAIN {RETAIN_HOURS} HOURS")

            # VACUUM実行後のファイル数を取得
            after_files = spark.sql(f"DESCRIBE DETAIL {table}").first()["numFiles"]

            print(f"  - 削除前ファイル数: {before_files}")
            print(f"  - 削除後ファイル数: {after_files}")
            print(f"VACUUM完了: {table}")
        except Exception as e:
            print(f"VACUUMエラー: {table} - {str(e)}")

    print("全テーブルのVACUUM完了")


# ジョブ実行
vacuum_silver_tables()
```

#### VACUUM設定

| 項目           | 設定値             | 説明                                 |
| -------------- | ------------------ | ------------------------------------ |
| 保持期間       | 168時間（7日）     | Time Travel用に7日分のファイルを保持 |
| 対象テーブル   | Silver層全テーブル | センサーデータ、状態                 |
| 実行タイミング | 日曜 04:00         | 週末の低負荷時間帯に実行             |

**注意事項:**
- VACUUMを実行すると、保持期間より古いバージョンへのTime Travelができなくなる
- 保持期間はテーブルプロパティ `delta.deletedFileRetentionDuration` と一致させる

### チェックポイントクリーンアップジョブ

ストリーミングパイプラインのチェックポイントファイルを定期的にクリーンアップする。

#### ジョブ概要

| 項目             | 設定値                             |
| ---------------- | ---------------------------------- |
| ジョブ名         | checkpoint_cleanup                 |
| 実行方式         | Databricks Workflow                |
| 実行間隔         | 週次（cron: `0 5 * * 0`）日曜05:00 |
| クラスタ         | Jobs Compute                       |
| タイムアウト     | 1時間                              |
| リトライポリシー | 失敗時リトライなし                 |

#### 処理フロー

```mermaid
flowchart TD
    Start([ジョブ開始]) --> Cutoff[カットオフ日時を計算<br>現在 - 7日]
    Cutoff --> DirLoop[各チェックポイント<br>ディレクトリを処理]

    DirLoop --> ListFiles[ディレクトリ内の<br>ファイル一覧を取得]
    ListFiles --> ListResult{取得<br>成功?}

    ListResult -->|失敗| DirError[エラー出力]
    ListResult -->|成功| FileLoop[各ファイルを処理]

    FileLoop --> CheckDate{更新日時が<br>カットオフ日<br>より前?}
    CheckDate -->|はい| Delete[ファイル/ディレクトリ削除]
    CheckDate -->|いいえ| Skip[スキップ]

    Delete --> NextFile{次の<br>ファイル?}
    Skip --> NextFile

    NextFile -->|あり| FileLoop
    NextFile -->|なし| Log[削除件数を出力]

    DirError --> NextDir{次の<br>ディレクトリ?}
    Log --> NextDir

    NextDir -->|あり| DirLoop
    NextDir -->|なし| End([ジョブ終了])
```

#### 処理コード

```python
from datetime import datetime, timedelta

def cleanup_old_checkpoints():
    """7日以上経過したチェックポイントファイルを削除"""

    # チェックポイント保存先
    CHECKPOINT_BASE_PATH = "abfss://checkpoints@{storage_account}.dfs.core.windows.net/"

    # 保持期間（日）
    RETAIN_DAYS = 7

    # 対象パイプラインのチェックポイントディレクトリ
    checkpoint_dirs = [
        f"{CHECKPOINT_BASE_PATH}silver_pipeline/",
    ]

    cutoff_date = datetime.now() - timedelta(days=RETAIN_DAYS)

    for checkpoint_dir in checkpoint_dirs:
        print(f"チェックポイントクリーンアップ開始: {checkpoint_dir}")
        try:
            # ディレクトリ内のファイル一覧を取得
            files = dbutils.fs.ls(checkpoint_dir)

            deleted_count = 0
            for file_info in files:
                # ファイルの更新日時を確認
                if hasattr(file_info, 'modificationTime'):
                    file_time = datetime.fromtimestamp(file_info.modificationTime / 1000)
                    if file_time < cutoff_date:
                        dbutils.fs.rm(file_info.path, recurse=True)
                        deleted_count += 1

            print(f"  - 削除ファイル/ディレクトリ数: {deleted_count}")
            print(f"クリーンアップ完了: {checkpoint_dir}")
        except Exception as e:
            print(f"クリーンアップエラー: {checkpoint_dir} - {str(e)}")

    print("全チェックポイントのクリーンアップ完了")


# ジョブ実行
cleanup_old_checkpoints()
```

#### クリーンアップ設定

| 項目           | 設定値                       | 説明                                         |
| -------------- | ---------------------------- | -------------------------------------------- |
| 保持期間       | 7日                          | 障害復旧に必要な期間を確保                   |
| 対象           | チェックポイントディレクトリ | ストリーミングパイプラインのチェックポイント |
| 実行タイミング | 日曜 05:00                   | VACUUM後に実行                               |

---

## 関連ドキュメント

- [README.md](./README.md) - メール送信ジョブ概要
- [シルバー層LDPパイプライン仕様書](../../ldp-pipeline/silver-layer/ldp-pipeline-specification.md) - メールキュー登録処理の詳細
- [アプリケーションデータベース設計書](../../common/app-database-specification.md) - email_notification_queue・mail_historyテーブル定義

---

## 変更履歴

| 日付       | 版数 | 変更内容 | 担当者       |
| ---------- | ---- | -------- | ------------ |
| 2026-01-19 | 1.0  | 初版作成 | Kei Sugiyama |