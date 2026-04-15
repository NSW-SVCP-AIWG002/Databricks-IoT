# メールデフォルト内容マスタ テーブル定義書

## 📑 目次

- [メールデフォルト内容マスタ テーブル定義書](#メールデフォルト内容マスタ-テーブル定義書)
  - [📑 目次](#-目次)
  - [概要](#概要)
  - [テーブル定義](#テーブル定義)
    - [メールデフォルト内容マスタ (mail\_default\_content\_master)](#メールデフォルト内容マスタ-mail_default_content_master)
  - [インデックス設計](#インデックス設計)
  - [制約・ルール](#制約ルール)
    - [外部キー制約](#外部キー制約)
    - [ビジネスルール](#ビジネスルール)
  - [初期データ例](#初期データ例)
  - [関連ドキュメント](#関連ドキュメント)

---

## 概要

本テーブルは、システムから送信されるメールのデフォルト内容（件名・本文）を管理するマスタテーブルです。メール種別ごと、言語ごとにデフォルトのメールテンプレートを保持し、メール送信時のテンプレートとして使用されます。

**主な用途:**
- メール送信時のデフォルト件名・本文の提供
- 多言語対応（言語マスタと連携）
- メールテンプレートの一元管理

**関連テーブル:**
- `mail_type_master` - メール種別マスタ
- `language_master` - 言語マスタ
- `mail_history` - メール送信履歴

---

## テーブル定義

### メールデフォルト内容マスタ (mail_default_content_master)

**概要**: メール種別ごと、言語ごとのデフォルトメール内容を管理するマスタテーブル

| #   | カラム物理名       | カラム論理名           | データ型     | NULL     | PK  | FK  | デフォルト値      | 説明                                            |
| --- | ------------------ | ---------------------- | ------------ | -------- | --- | --- | ----------------- | ----------------------------------------------- |
| 1   | mail_template_id   | メールテンプレートID   | INT          | NOT NULL | ○   | -   | -                 | メールテンプレートの一意識別子（自動採番）      |
| 2   | mail_type_id       | メール種別ID           | INT          | NOT NULL | -   | ○   | -                 | メール種別ID（mail_type_master参照）            |
| 3   | language_id        | 言語ID                 | INT          | NOT NULL | -   | ○   | 1                 | 対象言語ID（language_master参照）               |
| 4   | default_subject    | デフォルト件名         | VARCHAR(500) | NOT NULL | -   | -   | -                 | メールのデフォルト件名                          |
| 5   | default_body       | デフォルト本文         | TEXT         | NOT NULL | -   | -   | -                 | メールのデフォルト本文                          |
| 6   | template_variables | テンプレート変数       | JSON         | NULL     | -   | -   | -                 | 利用可能な変数の説明（JSON形式）                |
| 7   | description        | 説明                   | VARCHAR(500) | NULL     | -   | -   | -                 | テンプレートの用途説明                          |
| 8   | is_active          | 有効フラグ             | BOOLEAN      | NOT NULL | -   | -   | TRUE              | テンプレートの有効状態（TRUE:有効、FALSE:無効） |
| 9   | create_date        | 作成日時               | DATETIME     | NOT NULL | -   | -   | CURRENT_TIMESTAMP | レコード作成日時                                |
| 10  | creator            | 作成者                 | INT | NOT NULL | -   | -   | -                          | レコード作成者のユーザーID                      |
| 11  | update_date        | 更新日時               | DATETIME     | NOT NULL | -   | -   | CURRENT_TIMESTAMP | レコード最終更新日時                            |
| 12  | modifier           | 更新者                 | INT | NOT NULL | -   | -   | -                          | レコード更新者のユーザーID                      |
| 13  | delete_flag        | 削除フラグ             | BOOLEAN      | NOT NULL | -   | -   | -               |        |

**外部キー:**
- `mail_type_id` → `mail_type_master.mail_type_id`
- `language_id` → `language_master.language_id`

**インデックス:**
- PRIMARY KEY: `mail_template_id`
- UNIQUE INDEX: `mail_type_id, language_id` （メール種別と言語の組み合わせは一意）
- INDEX: `mail_type_id`
- INDEX: `language_id`
- INDEX: `is_active`

---

## インデックス設計

```sql
-- 主キー
CREATE INDEX PK_mail_default_content_master ON mail_default_content_master(mail_template_id);

-- メール種別と言語の組み合わせは一意（1つのメール種別に対して1言語1レコード）
CREATE UNIQUE INDEX UX_mail_default_content_type_lang ON mail_default_content_master(mail_type_id, language_id)
WHERE delete_flag = FALSE;

-- メール種別での検索用
CREATE INDEX IX_mail_default_content_type ON mail_default_content_master(mail_type_id);

-- 言語での検索用
CREATE INDEX IX_mail_default_content_language ON mail_default_content_master(language_id);

-- 有効なテンプレートの検索用
CREATE INDEX IX_mail_default_content_active ON mail_default_content_master(is_active);
```

---

## 制約・ルール

### 外部キー制約

```sql
-- メール種別マスタへの外部キー
ALTER TABLE mail_default_content_master
ADD CONSTRAINT FK_mail_default_content_mail_type FOREIGN KEY (mail_type_id)
REFERENCES mail_type_master(mail_type_id);

-- 言語マスタへの外部キー
ALTER TABLE mail_default_content_master
ADD CONSTRAINT FK_mail_default_content_language FOREIGN KEY (language_id)
REFERENCES language_master(language_id);
```

### ビジネスルール

1. **テンプレート変数の形式**
   - テンプレート本文・件名内で使用する変数は `{{variable_name}}` 形式で記載
   - 例: `{{user_name}}様、{{alert_message}}が発生しました。`

2. **多言語対応**
   - 同一のmail_type_idに対して、複数の言語のテンプレートを登録可能
   - mail_type_idとlanguage_idの組み合わせは一意制約（削除フラグがFALSEの場合）
   - 未登録の言語の場合は、デフォルト言語（language_id = 1: 日本語）のテンプレートを使用

3. **テンプレート変数の管理**
   - `template_variables` カラムにJSON形式で利用可能な変数を記載
   - 例: `{"user_name": "ユーザー名", "alert_message": "アラートメッセージ", "device_name": "デバイス名"}`
   - アプリケーション側でテンプレート変数を実際の値に置換してメール送信

4. **有効フラグの管理**
   - `is_active = TRUE` のテンプレートのみが使用される
   - テンプレート更新時は、新規レコードを作成し、旧レコードは `is_active = FALSE` に更新
   - バージョン管理のような運用も可能

5. **デフォルト値**
   - 新規メール種別追加時は、最低限日本語（language_id = 1）のテンプレートを登録必須

---

## 想定されるメール種別選択肢

以下は、システムで使用されるメール種別の選択肢です。

1. **発生アラート通知** - デバイスやシステムでアラートが発生した際の通知メール
2. **完了アラート通知** - デバイスやシステムでアラートが完了した際の通知メール
3. **ユーザー招待** - 新規ユーザーをシステムに招待する際のメール
4. **パスワードリセット** - パスワード再設定のリクエスト時のメール
5. **システム通知** - 一般的なシステムからの各種お知らせメール

---

## 関連ドキュメント

**参照元:**
- [アプリケーションデータベース設計書](../docs/03-features/common/app-database-specification.md)
  - メール送信履歴（mail_history）- 88行目
  - メール種別マスタ（mail_type_master）- 593行目

**関連テーブル:**
- `mail_type_master` - メール種別マスタ（発生アラート通知、完了アラート通知、招待メール、パスワードリセット、システム通知）
- `language_master` - 言語マスタ（日本語、英語など）
- `mail_history` - メール送信履歴（実際に送信されたメール内容を記録）

**設計思想:**
- メールテンプレートを一元管理し、メンテナンス性を向上
- 多言語対応により、ユーザーの言語設定に応じたメール送信が可能
- テンプレート変数により、動的なメール内容の生成をサポート

---

**このテーブル定義は、実装前に必ずレビューを受けてください。**
