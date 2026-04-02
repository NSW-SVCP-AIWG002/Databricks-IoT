# AIオーケストレータ デプロイ手順書

## 目次

- [前提条件](#前提条件)
- [STEP 1：conf/config.ini の設定](#step-1confconfigini-の設定)
- [STEP 2：Databricks Workspace へのファイルアップロード](#step-2databricks-workspace-へのファイルアップロード)
- [STEP 3：Notebook でモデル登録（log_model.py 実行）](#step-3notebook-でモデル登録log_modelpy-実行)
- [STEP 4：Model Serving Endpoint の作成](#step-4model-serving-endpoint-の作成)
- [STEP 5：動作確認](#step-5動作確認)
- [トラブルシューティング](#トラブルシューティング)

---

## 前提条件

### 必要な権限

| 対象                  | 必要な権限                                                      |
| --------------------- | --------------------------------------------------------------- |
| Databricks Workspace  | `CAN MANAGE` 以上（Notebook 作成・Workspace ファイル操作）      |
| Unity Catalog         | `CREATE TABLE` 権限（チェックポイントテーブル作成先スキーマ）   |
| MLflow Model Registry | `CAN MANAGE` 以上（モデル登録先カタログ・スキーマ）             |
| Model Serving         | `CAN MANAGE` 以上（Serving Endpoint 作成）                      |
| SQL Warehouse         | `CAN USE` 以上                                                  |
| Genie Space           | 対象スペースへのアクセス権                                      |

### 必要な情報（事前に収集）

| 情報                         | 取得場所                                                                               |
| ---------------------------- | -------------------------------------------------------------------------------------- |
| Workspace URL                | ブラウザのアドレスバー（例: `https://adb-xxxxxxxxxxxx.azuredatabricks.net`）           |
| SQL Warehouse Server Hostname| Databricks UI → SQL → SQL Warehouses → 対象 → Connection details → Server hostname    |
| SQL Warehouse HTTP Path      | 同上 → HTTP path                                                                       |
| Genie Space ID（各スペース） | Databricks UI → SQL → Genie → 対象スペース → ブラウザ URL 内の ID                     |
| LLM エンドポイント名         | Databricks UI → Machine Learning → Serving → 対象エンドポイント名                     |
| Unity Catalog カタログ名     | Databricks UI → Data → カタログ一覧で確認                                              |

---

## STEP 1：conf/config.ini の設定

`conf/config.ini` を開き、`<...>` のプレースホルダーをすべて実際の値に書き換えます。

```ini
[model]
endpoint = databricks-gemini-2-5-pro   # ← 使用する LLM エンドポイント名に変更

[filestore]
databricks_host = https://adb-xxxxxxxxxxxx.azuredatabricks.net   # ← Workspace URL（末尾スラッシュなし）
csv_file_name = tables/csv_data/{message_id}_{timestamp}.csv     # ← 変更不要

[genie]
databricks_host = https://adb-xxxxxxxxxxxx.azuredatabricks.net   # ← filestore と同じ URL
genie_start_conversation_api = /api/2.0/genie/spaces/{space_id}/start-conversation
genie_get_message_api = /api/2.0/genie/spaces/{space_id}/conversations/{conversation_id}/messages/{message_id}
genie_post_message_api = /api/2.0/genie/spaces/{space_id}/conversations/{conversation_id}/messages
statement_api = /api/2.0/sql/statements/{statement_id}           # ← 上記 4 行は変更不要

[genie_spaces.SALES]
id = 01jxxxxxxxxxxxxxxxxxxxxxx   # ← Genie Space の ID（URL から取得）
description = 売上・在庫・客数・商品・店舗・実績比較など
keywords = ["売上","在庫","客数","商品","店舗","実績","前年比","前週比"]
examples = ["2025年の売上高、在庫、客数、前週比を教えて。"]

[genie_spaces.BUDGET]
id = 01jyyyyyyyyyyyyyyyyyyyyyy   # ← Genie Space の ID
description = 予算・予算比・予算達成率・目標管理など。「予算」というキーワードが含まれる場合は必ずBUDGETを優先に選択する。
keywords = ["予算","予算比","予算達成","目標","達成率"]
examples = ["2025年の売上高、予算、客数、前年比を教えて。","今月の予算達成率を教えて。"]

[sql]
sql_server_host_name = adb-xxxxxxxxxxxx.azuredatabricks.net   # ← https:// なし
sql_http_path = /sql/1.0/warehouses/xxxxxxxxxxxxxxxx          # ← Connection details の HTTP path

[checkpoint]
table_name = iot_catalog.genie.history   # ← カタログ名.スキーマ名.テーブル名
max_turns = 15                           # ← 変更不要
max_size_bytes = 524288                  # ← 変更不要
```

### Genie Space ID の確認方法

1. Databricks UI → `SQL` → `Genie` を開く
2. 対象のスペースをクリック
3. ブラウザの URL を確認する

```
https://adb-xxxx.azuredatabricks.net/genie/spaces/01jxxxxxxxxxxxxxxxxxxxxxx/...
                                                   ^^^^^^^^^^^^^^^^^^^^^^^^^^
                                                   この部分が id
```

### sql_server_host_name の確認方法

1. Databricks UI → `SQL` → `SQL Warehouses` を開く
2. 対象の Warehouse をクリック
3. `Connection details` タブを開く
4. `Server hostname` の値をコピー（**`https://` を除いた部分のみ**使用）

---

## STEP 2：Databricks Workspace へのファイルアップロード

`ai_chat_graph_gen_src/` ディレクトリ全体を Databricks Workspace にアップロードします。

### アップロード対象（必要なもの）

```
ai_chat_graph_gen_src/
├── conf/               ← 設定ファイル（STEP 1 で編集済み）
├── db/                 ← チェックポイント DB 接続
├── model/              ← MLflow pyfunc ラッパー
├── src/                ← ビジネスロジック
├── log_model.py        ← デプロイ実行スクリプト
└── requirements.txt    ← 依存パッケージ
```

> `streamlit_app.py`・`app.yaml`・`test_run.py`・`main.py` はローカル確認用のため、アップロード不要です。

### 方法A：Databricks CLI を使用（推奨）

```bash
# 1. Databricks CLI のインストール（未インストールの場合）
pip install databricks-cli

# 2. 認証設定
databricks configure --token
# Host: https://adb-xxxxxxxxxxxx.azuredatabricks.net
# Token: <Personal Access Token>

# 3. アップロード先ディレクトリを作成
databricks workspace mkdirs /Users/yourname@example.com/ai_orchestrator

# 4. ファイルを一括アップロード
databricks workspace import_dir \
  ./ai_chat_graph_gen_src \
  /Users/yourname@example.com/ai_orchestrator \
  --overwrite
```

### 方法B：Workspace UI からアップロード

1. Databricks UI → 左メニューの `Workspace` を開く
2. アップロード先フォルダを作成（例: `/Users/yourname@example.com/ai_orchestrator/`）
3. `ai_chat_graph_gen_src/` を zip 圧縮する
4. フォルダを右クリック → `Import` → zip ファイルを選択してアップロード

---

## STEP 3：Notebook でモデル登録（log_model.py 実行）

### 3-1. チェックポイント用スキーマの事前作成

`log_model.py` を実行する前に、チェックポイントテーブルの保存先スキーマを作成します。

Databricks の SQL Editor または Notebook で以下を実行します：

```sql
-- config.ini の [checkpoint] table_name に合わせて変更
-- 例: table_name = iot_catalog.genie.history の場合
CREATE SCHEMA IF NOT EXISTS iot_catalog.genie;
```

> テーブル自体はアプリ初回実行時に自動作成されます。スキーマのみ事前作成が必要です。

### 3-2. モデル登録先スキーマの事前作成

```sql
-- log_model.py 内の registered_model_name に合わせて変更
-- 例: "iot_catalog.ai.ai_orchestrator" の場合
CREATE SCHEMA IF NOT EXISTS iot_catalog.ai;
```

### 3-3. Notebook の作成と設定

1. Databricks UI → STEP 2 でアップロードしたフォルダを開く
2. `log_model.py` を右クリック → `Clone` で Notebook として複製する（または新規 Notebook を作成して内容を貼り付ける）
3. Notebook 内の以下の行を確認し、プロジェクトの Unity Catalog カタログ名に合わせて変更する：

```python
# log_model.py 40行目（変更が必要な場合）
registered_model_name = "prd_im_dlh.genie.langgraph_agent"
#                        ↑ カタログ  ↑ スキーマ ↑ モデル名
# → 例: "iot_catalog.ai.ai_orchestrator" に変更
```

### 3-4. 作業ディレクトリの設定

Notebook の **最初のセル**（`%pip install` より前）に以下を追加します：

```python
import os
# STEP 2 でアップロードしたパスに合わせて変更
os.chdir("/Workspace/Users/yourname@example.com/ai_orchestrator")
print(os.getcwd())
print(os.listdir("."))
# 出力例: ['conf', 'db', 'log_model.py', 'model', 'requirements.txt', 'src', ...]
```

### 3-5. Notebook の実行

セルを上から順に実行します。

```
セル1（追加）: os.chdir(...)
セル2: %pip install mlflow==3.6.0       ← 実行後にカーネルが自動再起動
セル3: %pip install databricks-sdk==0.73.0
セル4: %pip install -r requirements.txt
セル5: import 〜 mlflow.pyfunc.log_model(...) 〜 mlflow.register_model(...)
```

> `%pip install` 実行後にカーネルが再起動するため、**再起動後に残りのセルを再実行**してください。

**実行成功時の出力例：**

```
Registered: iot_catalog.ai.ai_orchestrator 1
```

`Registered: <モデル名> <バージョン番号>` が表示されれば登録完了です。

---

## STEP 4：Model Serving Endpoint の作成

### 4-1. UI からの作成手順

1. Databricks UI → `Machine Learning` → `Serving` を開く
2. `Create serving endpoint` をクリック
3. 以下の設定を入力する：

| 項目          | 設定値                                                                  |
| ------------- | ----------------------------------------------------------------------- |
| Name          | 任意（例: `ai-orchestrator`）                                           |
| Entity        | STEP 3 で登録したモデル名（例: `iot_catalog.ai.ai_orchestrator`）       |
| Version       | `1`（最新バージョンを選択）                                             |
| Compute type  | `CPU`（LLM は外部 API 呼び出しのため GPU 不要）                         |
| Compute size  | `Small`（起動後に必要に応じて変更可）                                   |
| Scale to zero | 有効（コスト最適化のため推奨）                                          |

4. `Create` をクリック
5. ステータスが `Ready` になるまで待機（数分〜10分程度）

### 4-2. エンドポイント URL の確認

Endpoint が `Ready` になったら URL をメモします：

```
https://adb-xxxxxxxxxxxx.azuredatabricks.net/serving-endpoints/ai-orchestrator/invocations
```

Databricks UI → `Serving` → 対象エンドポイント → `Query endpoint` の URL で確認できます。

---

## STEP 5：動作確認

### 5-1. Serving Endpoint から直接テスト（UI）

1. Databricks UI → `Serving` → 作成したエンドポイントを開く
2. `Query endpoint` をクリック
3. 以下の JSON をリクエストボディに入力して `Send request` をクリック：

```json
{
  "dataframe_records": [
    {
      "prompt": "こんにちは",
      "access_token": "<Personal Access Token>",
      "thread_id": "test-001"
    }
  ]
}
```

**正常レスポンス例：**

```json
{
  "predictions": [
    {
      "status": "ok",
      "message": "こんにちは！何かご質問はありますか？",
      "df": null,
      "fig_data": null,
      "sql_query": ""
    }
  ]
}
```

### 5-2. HITL（グラフ作成確認）の動作確認

グラフ生成を含む質問で HITL が正しく動作するか確認します。

**1回目リクエスト（グラフ生成を含む質問）：**

```json
{
  "dataframe_records": [
    {
      "prompt": "売上のグラフを作成して",
      "access_token": "<Personal Access Token>",
      "thread_id": "test-002"
    }
  ]
}
```

**期待されるレスポンス（中断）：**

```json
{
  "predictions": [
    {
      "status": "interrupted",
      "message": "以下のデータを取得しました。グラフを作成しますか？",
      "df": [{ ... }],
      "sql_query": "SELECT ...",
      "fig_data": null
    }
  ]
}
```

**2回目リクエスト（「はい」で再開）：同一の `thread_id` を使用**

```json
{
  "dataframe_records": [
    {
      "prompt": "はい",
      "access_token": "<Personal Access Token>",
      "thread_id": "test-002"
    }
  ]
}
```

**期待されるレスポンス（グラフあり）：**

```json
{
  "predictions": [
    {
      "status": "ok",
      "message": "グラフを作成しました。...",
      "df": null,
      "fig_data": "{ \"data\": [...] }",
      "sql_query": "SELECT ..."
    }
  ]
}
```

---

## トラブルシューティング

### `ModuleNotFoundError: No module named 'conf'`

**原因：** Notebook の作業ディレクトリが正しく設定されていない。

**対処：**

```python
import os
os.chdir("/Workspace/Users/yourname@example.com/ai_orchestrator")
print(os.listdir("."))
# conf, db, model, src が表示されることを確認
```

---

### `アクセストークンが無効です (401 Unauthorized)`

**原因：** リクエストの `access_token` が無効または期限切れ。

**対処：** Databricks UI → 右上のユーザーアイコン → `User Settings` → `Developer` → `Access tokens` で新しいトークンを発行して使用する。

---

### Genie API が応答しない / `Genie conversation error`

**原因：** `config.ini` の `databricks_host` または Genie Space ID の設定が誤っている。

**対処：**

1. `[genie]` セクションの `databricks_host` が正しい Workspace URL か確認する（末尾スラッシュなし）
2. `[genie_spaces.*]` の `id` が正しいか確認する（ブラウザ URL から再取得）
3. 対象 Genie Space へのアクセス権があるか確認する

---

### SQL Warehouse に接続できない / `SQL実行エラー`

**原因：** `config.ini` の `[sql]` セクションの設定が誤っている。

**対処：**

1. `sql_server_host_name` に `https://` が含まれていないか確認する（含まれている場合は削除）
2. `sql_http_path` が `/sql/1.0/warehouses/...` の形式か確認する
3. SQL Warehouse が起動中か確認する（自動停止している場合は Warehouse を手動で起動）

---

### チェックポイントテーブルへの書き込み失敗

**原因：** `config.ini` の `[checkpoint] table_name` のスキーマが存在しない。

**対処：**

```sql
-- table_name = iot_catalog.genie.history の場合
CREATE SCHEMA IF NOT EXISTS iot_catalog.genie;
```

---

### Endpoint のステータスが `Failed` になる

**原因：** `requirements.txt` のパッケージ競合、または `code_paths` のディレクトリが見つからない。

**対処：**

1. Databricks UI → `Serving` → 対象エンドポイント → `Logs` タブでエラー内容を確認する
2. 作業ディレクトリ（`os.chdir()`）が正しく設定されているか確認する
3. `log_model.py` 内の `code_paths=["model", "src", "conf", "db"]` の各ディレクトリが作業ディレクトリ直下に存在するか確認する

---

## 変更履歴

| 日付       | 版数 | 変更内容 | 担当者       |
| ---------- | ---- | -------- | ------------ |
| 2026-04-02 | 1.0  | 初版作成 | Kei Sugiyama |
