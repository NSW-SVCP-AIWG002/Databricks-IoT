# メール通知送信ジョブ

## 目次

- [概要](#概要)
- [機能ID](#機能id)
- [データモデル](#データモデル)
- [使用テーブル一覧](#使用テーブル一覧)
- [処理フロー](#処理フロー)
- [障害時のTeams通知](#障害時のteams通知)
- [パフォーマンス要件](#パフォーマンス要件)
- [データ保持ポリシー](#データ保持ポリシー)
- [関連ドキュメント](#関連ドキュメント)
- [変更履歴](#変更履歴)

---

## 概要

メール通知送信ジョブは、IoTデバイスのアラート検出時にメール通知キューへ登録されたレコードを、Databricks Workflowで定期実行して送信するバッチジョブです。

シルバー層LDPパイプラインがアラートを検出するたびにメール送信キュー（`email_notification_queue`）へPENDINGステータスのレコードを登録し、本ジョブが1分間隔でそのレコードを取得してSMTP経由でメール送信を行います。LDPストリーミング処理とメール送信を非同期化することで、ストリーミング処理のレイテンシに影響を与えないアーキテクチャを実現しています。

### 主な責務

1. **メールキュー取得**: メール通知キュー（`email_notification_queue`）からPENDINGレコードを取得
2. **メール送信**: SMTP経由でアラート通知メールを送信
3. **ステータス管理**: 送信結果に応じてキューレコードのステータスを更新（SENT / PENDING / FAILED）
4. **履歴記録**: 送信完了メールの記録を`mail_history`テーブルに保存
5. **リカバリ処理**: ジョブ異常終了時にPROCESSING状態で滞留しているレコードを自動削除
6. **クリーンアップ**: 30日経過したSENT/FAILEDレコードを定期削除（別ジョブ）

---

## 機能ID

| 機能ID   | 機能名         | 説明                                             |
| -------- | -------------- | ------------------------------------------------ |
| FR-003-2 | アラート通知   | メール送信キューからのメール送信（バッチジョブ） |
| OP-002   | クリーンアップ | 送信済み・失敗レコードの定期削除                 |

---

## データモデル

### 入力データ

| データソース             | 形式             | 説明                                                             |
| ------------------------ | ---------------- | ---------------------------------------------------------------- |
| email_notification_queue | OLTP DB テーブル | シルバー層パイプラインがアラート検出時に登録するメール送信待機列 |

### メール通知キューカラム一覧

| #   | カラム物理名      | カラム論理名         | データ型      | NULL     | 説明                                         |
| --- | ----------------- | -------------------- | ------------- | -------- | -------------------------------------------- |
| 1   | queue_id          | キューID             | BIGINT        | NOT NULL | キューレコードの一意識別子（自動採番）       |
| 2   | device_id         | デバイスID           | INT           | NOT NULL | アラート発生元デバイスID                     |
| 3   | organization_id   | 組織ID               | INT           | NOT NULL | デバイス所属組織ID                           |
| 4   | alert_id          | アラートID           | INT           | NOT NULL | 発生したアラート設定ID                       |
| 5   | recipient_email   | 送信先メールアドレス | VARCHAR(2000) | NOT NULL | 通知送信先のメールアドレス                   |
| 6   | subject           | 件名                 | VARCHAR(500)  | NOT NULL | メール件名                                   |
| 7   | body              | 本文                 | VARCHAR(2000) | NOT NULL | メール本文                                   |
| 8   | alert_detail_json | アラート詳細JSON     | JSON          | NOT NULL | アラート詳細情報（測定項目・値・閾値等）     |
| 9   | status            | ステータス           | VARCHAR(20)   | NOT NULL | `PENDING` / `PROCESSING` / `SENT` / `FAILED` |
| 10  | retry_count       | リトライ回数         | INT           | NOT NULL | 送信リトライ回数（初期値: 0、最大: 3）       |
| 11  | error_message     | エラーメッセージ     | JSON          | NULL     | 送信失敗時のエラー内容                       |
| 12  | event_timestamp   | イベント発生日時     | TIMESTAMP     | NOT NULL | アラートが発生した日時                       |
| 13  | queued_time       | キュー登録日時       | TIMESTAMP     | NOT NULL | キューに登録された日時                       |
| 14  | processed_time    | 処理完了日時         | TIMESTAMP     | NULL     | メール送信処理が完了した日時                 |
| 15  | create_date       | 作成日時             | TIMESTAMP     | NOT NULL | レコード作成日時                             |
| 16  | update_date       | 更新日時             | TIMESTAMP     | NOT NULL | レコード更新日時                             |

### ステータス遷移

| ステータス | 説明                             | 遷移元     | 遷移先                  |
| ---------- | -------------------------------- | ---------- | ----------------------- |
| PENDING    | 送信待ち（初期状態）             | -          | PROCESSING              |
| PROCESSING | 送信処理中                       | PENDING    | SENT / PENDING / FAILED |
| SENT       | 送信完了                         | PROCESSING | -                       |
| FAILED     | 送信失敗（最大リトライ回数超過） | PROCESSING | -                       |

### 出力先

| 出力先                   | 形式                 | 説明                                          |
| ------------------------ | -------------------- | --------------------------------------------- |
| SendGrid API             | HTTP POSTリクエスト  | アラート通知メールの送信                      |
| email_notification_queue | OLTP DB テーブル更新 | ステータス・retry_count・processed_timeの更新 |
| mail_history             | OLTP DB テーブル登録 | 送信済みメールの履歴記録                      |

### メール送信履歴カラム一覧

| #   | カラム物理名      | カラム論理名         | データ型     | NULL     | 説明                                      |
| --- | ----------------- | -------------------- | ------------ | -------- | ----------------------------------------- |
| 1   | mail_history_id   | メール送信履歴ID     | INT          | NOT NULL | メール送信履歴の一意識別子                |
| 2   | mail_history_uuid | メール送信履歴UUID   | VARCHAR(36)  | NOT NULL | UUID（外部公開用一意識別子）              |
| 3   | mail_type         | メール種別ID         | INT          | NOT NULL | メール種別ID（mail_type_master参照）      |
| 4   | sender_email      | 送信元メールアドレス | VARCHAR(254) | NOT NULL | 送信元のメールアドレス                    |
| 5   | recipients        | 送信先メールアドレス | JSON         | NOT NULL | 送信先のメールアドレス（JSON形式）        |
| 6   | subject           | メール件名           | VARCHAR(500) | NOT NULL | メールの件名                              |
| 7   | body              | メール本文           | TEXT         | NOT NULL | メールの本文                              |
| 8   | sent_at           | 送信日時             | DATETIME     | NOT NULL | メール送信日時                            |
| 9   | user_id           | 関連ユーザーID       | INT          | NULL     | 関連するユーザーID（user_master参照）     |
| 10  | organization_id   | 関連組織ID           | INT          | NULL     | 関連する組織ID（organization_master参照） |
| 11  | create_date       | 作成日時             | DATETIME     | NOT NULL | レコード作成日時                          |
| 12  | creator           | 作成者               | INT          | NOT NULL | レコード作成者のユーザーID                |
| 13  | update_date       | 更新日時             | DATETIME     | NULL     | レコード最終更新日時                      |
| 14  | modifier          | 更新者               | INT          | NULL     | レコード更新者のユーザーID                |

---

## 使用テーブル一覧

### 読み取りテーブル（OLTP DB）

| テーブル名               | 用途                                          |
| ------------------------ | --------------------------------------------- |
| email_notification_queue | PENDINGステータスのメール送信待機レコード取得 |

### 読み取りテーブル（Deltaテーブル）

| テーブル名          | 用途                                                 |
| ------------------- | ---------------------------------------------------- |
| device_master       | メール通知時、デバイスの実在確認で利用する           |
| organization_master | メール通知時、通知先組織の実在チェックで利用する     |
| user_master         | メール通知先のユーザのメールアドレスの取得に利用する |


### 書き込みテーブル（OLTP DB）

| テーブル名               | 用途                                        |
| ------------------------ | ------------------------------------------- |
| email_notification_queue | ステータス・retry_count・processed_time更新 |
| mail_history             | 送信済みメールの履歴記録                    |

---

## 処理フロー

```mermaid
flowchart TB
    subgraph Silver["シルバー層LDPパイプライン（foreachBatch）"]
        AlertDetect[アラート検出<br>alert_triggered=TRUE]
        QueueInsert[メール送信キュー登録<br>status=PENDING]
        AlertDetect --> QueueInsert
    end

    subgraph  
        subgraph Queue["メール通知キュー（OLTP DB）"]
            PendingRecord[(email_notification_queue<br>status=PENDING)]
            QueueInsert --> PendingRecord
        end

        subgraph DLTTBL["Deltaテーブル"]
            direction LR
            OrganizationMaster[(organization_master<br>organization_id=<br>email_notification_queue.organization_id)]
            UserMaster[(user_master<br>organization_id=<br>organization_master.organization_id)]
        end
    end

    subgraph Batch["メール送信バッチジョブ（1分間隔）"]
        Recovery[PROCESSING滞留レコード削除<br>最終更新後15分経過で<br>自動削除]
        Fetch[抽出済メール送信<br>キューデータ<br>組織マスタ/ユーザマスタと結合]
        UpdateProcessing[ステータス→PROCESSING]
        SendEmail[メール送信<br>SMTP]
        Success{送信成功?}
        UpdateSent[ステータス→SENT<br>processed_time記録]
        CheckRetry{retry_count < 3?}
        UpdatePending[retry_count++<br>ステータス→PENDING]
        UpdateFailed[ステータス→FAILED]
        RecordHistory[mail_history登録]

        Recovery -->|PENDINGレコード取得<br>最大100件| Fetch
        Fetch --> UpdateProcessing
        UpdateProcessing --> SendEmail
        SendEmail --> Success
        Success -->|Yes| UpdateSent
        Success -->|No| CheckRetry
        CheckRetry -->|Yes| UpdatePending
        CheckRetry -->|No| UpdateFailed
        UpdateSent --> RecordHistory
    end

    subgraph External["外部連携"]
        SendGrid[SendGrid API]
        MailHistory[(OLTP DB<br>mail_history)]
        SendEmail --> SendGrid
        RecordHistory --> MailHistory
    end

    PendingRecord --> Recovery
    OrganizationMaster -.->|参照| Fetch
    UserMaster -.->|参照| Fetch
```

### リトライフロー

```mermaid
flowchart TB
    A(送信失敗) --> B{retry_count < 3?}
    B -->|Yes| C[retry_count++<br>status=PENDING<br>error_message記録]
    B -->|No| D[status=FAILED<br>error_message記録]
    C --> E[次回バッチ実行まで待機<br>最大1分]
    E --> F(再送信試行)
    D --> G(処理終了)
```

---

## 障害時のTeams通知

以下のエラー発生時、Teamsのシステム保守者連絡チャネルに通知を行い、運用担当者が迅速に対応できるようにする。

| エラー種別             | 通知タイミング       | 説明                                       |
| ---------------------- | -------------------- | ------------------------------------------ |
| SendGrid API接続失敗   | 最大リトライ超過後   | SendGrid APIへの接続失敗が連続した場合     |
| メール送信履歴記録失敗 | INSERT失敗時（即時） | mail_historyへのINSERT失敗時               |
| キュー取得失敗         | 例外発生時（即時）   | email_notification_queueへのアクセス失敗時 |
| FAILED件数過多         | 日次（100件超過）    | 大量のFAILEDレコード発生時                 |

詳細は[ジョブ仕様書](./job-specification.md)のエラーハンドリングセクションを参照。

---

## パフォーマンス要件

| 要件           | 値                       | 対応策                                     |
| -------------- | ------------------------ | ------------------------------------------ |
| 実行間隔       | 1分（60秒）              | Databricks Workflowの定期実行              |
| バッチ処理時間 | 1分以内                  | 1バッチあたり最大100件で次実行に干渉しない |
| メール送信     | 平均100件/分             | SendGrid APIタイムアウト30秒以内           |
| E2Eレイテンシ  | アラート検出から70秒以内 | ストリーミング処理5秒 + キュー待機60秒     |

---

## データ保持ポリシー

| テーブル                 | 保持期間 | 削除対象            | 削除方式 |
| ------------------------ | -------- | ------------------- | -------- |
| email_notification_queue | 30日間   | SENT/FAILEDレコード | DELETE   |
| mail_history             | 恒久保持 | 削除しない          | -        |

クリーンアップは `email_queue_cleanup` ジョブ（日次 03:00）で実行する。

---

## 関連ドキュメント

### 機能仕様

- [ジョブ仕様書](./job-specification.md) - 処理コード・リトライ戦略・クリーンアップジョブ詳細

### 上流パイプライン

- [シルバー層LDPパイプライン概要](../../ldp-pipeline/silver-layer/README.md) - メール送信キュー登録元
- [シルバー層LDPパイプライン仕様書](../../ldp-pipeline/silver-layer/ldp-pipeline-specification.md) - メールキュー登録処理の詳細

### データベース設計

- [アプリケーションデータベース設計書](../../common/app-database-specification.md) - email_notification_queue・mail_historyテーブル定義

### 要件定義

- [機能要件定義書](../../../02-requirements/functional-requirements.md) - FR-003-2
- [非機能要件定義書](../../../02-requirements/non-functional-requirements.md) - NFR-PERF, NFR-AVAIL

---

## 変更履歴

| 日付       | 版数 | 変更内容 | 担当者       |
| ---------- | ---- | -------- | ------------ |
| 2026-04-01 | 1.0  | 初版作成 | Kei Sugiyama |
