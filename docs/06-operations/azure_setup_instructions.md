# Azure デプロイ時の設定手順

## Step 1: App Service の作成

1. **Azure Portal** → `App Service` → `作成` → `Web アプリ`
2. 以下を入力：

| 項目 | 値 |
|------|----|
| リソースグループ | rg-nsw-iotbricks |
| 名前 | nswiotbricks |
| 公開 | コード |
| ランタイムスタック | Python 3.11 |
| オペレーティングシステム | Linux |
| リージョン | Japan East |
| App Service プラン | 「新規作成」→ P0v4 |

3. `確認および作成` →`作成`

---

## Step 2: Entra ID アプリ登録

1. **Azure Portal** → `Microsoft Entra ID` → `アプリの登録` → `新規登録`
2. 以下を入力：

| 項目 | 値 |
|------|----|
| 名前 | nswiotbricks |
| サポートされるアカウントの種類 | 要件に合わせて選択（検証環境：`所属する組織のみ`） |
| リダイレクトURL | `https://<既定のドメイン>/.auth/login/aad/callback` |

3. 登録後、**テナントID** と **クライアントID** をメモ

**注:** リダイレクトURLの`<既定のドメイン>`は `App Service` → `概要` からコピペ（例: `nswiotbricks-debhgub8hacwcbaw.japaneast-01.azurewebsites.net`）

---

## Step 3: Entra ID アプリ登録の追加設定

### API アクセス許可の追加
1. `APIのアクセス許可` → `アクセス許可の追加` → `自分のAPIを選択`
2. `2ff814a6-3304-4ab8-85cb-cd0e6f879c1d`（Azure Databricks）を検索
3. `user_impersonation` にチェック → `アクセス許可の追加`
4. **管理者の同意を与える** をクリック（組織の既定値で不要になっている場合は手順スキップ）

### クライアントシークレットの発行
1. `証明書とシークレット` → `新しいクライアントシークレット`
2. シークレット値をコピーしてメモ（一度しか表示されません）

---

## Step 4: App Service の Easy Auth 設定

1. **Azure Portal** → 対象の `App Service` → `認証`
2. `ID プロバイダーを追加` → `Microsoft` を選択
3. 以下を設定：

| 項目 | 値 | 備考 |
|------|----|------|
| アプリ登録の種類 | 既存のアプリ登録を提供する | |
| アプリケーション（クライアント）ID | Step 2 でメモしたクライアントID | |
| クライアントシークレット | Step 3 でメモしたシークレット値 | |
| 発行者の URL | `https://login.microsoftonline.com/<tenant-id>/v2.0` | `<tenant-id>` は Step 2 でメモしたテナントID |
| 認証されていない要求 | HTTP 302 リダイレクト（ログインページへ） |

4. `追加`をクリック
5. `リソースエクスプローラー` → `subscriptions` → `サブスクリプション名` → `resourceGroups` → `リソースグループ名` → `プロバイダー` → `Microsoft.Web` → `sites` → `App Service 名` → `config` → `authsettingsV2` を選択
6. json の `properties` → `identityProviders` → `azureActiveDirectory` → `login` 内に以下を追加：

```json
"loginParameters": [
    "scope=openid profile email offline_access 2ff814a6-3304-4ab8-85cb-cd0e6f879c1d/user_impersonation"
]
```

**重要:** 上記スコープがないと `X-MS-TOKEN-AAD-ACCESS-TOKEN` ヘッダーに Databricks 用トークンが含まれず、Token Exchange が失敗します。

**注:** `offline_access` がないとリフレッシュトークンが発行されず、アクセストークン期限切れ時に `/.auth/refresh` でのトークン更新が機能しません。

---

## Step 5: Databricks Federation Policy 設定

**Databricks Account Console** で設定します。

1. `Security` → `Authentication` → `Federation policies` → `Create policy`
2. 以下を設定：

| 項目 | 値 | 備考 |
|------|----|------|
| Issuer URL | `https://sts.windows.net/<tenant-id>/` | `<tenant-id>` は Step 2 でメモしたテナントID |
| Audiences | 2ff814a6-3304-4ab8-85cb-cd0e6f879c1d | |
| Subject claim | unique_name | |
| JWKS URI | `https://login.microsoftonline.com/<tenant-id>/discovery/v2.0/keys` | `Advanced fields` → `JWKS URI` で設定 |

3. `Create policy` をクリック

---

## Step 6: App Service の環境変数設定

1. **Azure Portal** → `App Service` → `環境変数` → `アプリ設定`
2. 以下を追加：

| 環境変数名 | 値 | 備考 |
|------------|----|-----|
| `FLASK_ENV` | `production` | |
| `AUTH_TYPE` | `azure` | |
| `SECRET_KEY` | UUID（32文字以上推奨） | |
| `DATABRICKS_HOST` | `<workspace-url>.azuredatabricks.net`（`https://` なし） | `Databricks` → `SQL Warehouses` → `Connection details` からコピペ |
| `DATABRICKS_HTTP_PATH` | `/sql/1.0/warehouses/<warehouse-id>` | `Databricks` → `SQL Warehouses` → `Connection details` からコピペ |
| `MYSQL_HOST` | 本番 MySQL のホスト名 | |
| `MYSQL_USER` | 本番 MySQL ユーザー名 | |
| `MYSQL_PASSWORD` | 本番 MySQL パスワード | |
| `MYSQL_DATABASE` | 本番 DB 名 | |
| `MYSQL_PORT` | 本番 DB ポート番号 | |
| `DATABASE_URL` | `mysql+pymysql://<MYSQL_USER>:<MYSQL_PASSWORD>@<MYSQL_HOST>:<MYSQL_PORT>/<MYSQL_DATABASE>?ssl_ca=/etc/ssl/certs/ca-certificates.crt` | |
| `SCM_DO_BUILD_DURING_DEPLOYMENT` | `true` | zipデプロイのビルド自動化設定 |

---

## Step 7: ソースコードのデプロイ

1. `Databricks-IoT\src\iot_app`, `Databricks-IoT\requirements.txt`, `Databricks-IoT\wsgi.py` をzipファイル化する

```
zipファイル構成
├── iot_app
│    └── ...
├── requirements.txt
└── wsgi.py
```

2. **Azure CLI** で以下のコマンド実行

```
az webapp deploy --resource-group <リソースグループ名> --name <App Service 名> --src-path <zipファイルパス> --type zip
```

---

## Step 8: 動作確認

1. アプリケーションのURLアクセス
2. Entra ID でログインしホーム画面にリダイレクトされたらOK