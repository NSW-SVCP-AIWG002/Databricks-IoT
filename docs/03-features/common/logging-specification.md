# ログ設計書

## 目次

1. [概要・設計方針](#1-概要設計方針)
2. [ロガー実装](#2-ロガー実装)
   - 2.1 [共通ロガー（LoggerAdapter）](#21-共通ロガーloggeradapter)
   - 2.2 [各モジュールでの使い方](#22-各モジュールでの使い方)
   - 2.3 [requestId 管理](#23-requestid-管理)
3. [ログ出力形式・出力先](#3-ログ出力形式出力先)
4. [自動付与フィールド](#4-自動付与フィールド)
5. [マスキング](#5-マスキング)
   - 5.1 [自動マスキング](#51-自動マスキング)
   - 5.2 [認証失敗時の非マスク出力](#52-認証失敗時の非マスク出力)
   - 5.3 [出力禁止項目](#53-出力禁止項目)
6. [ログ出力タイミングと実装パターン](#6-ログ出力タイミングと実装パターン)
   - 6.1 [タイミング一覧](#61-タイミング一覧)
   - 6.2 [リクエスト前後（自動）](#62-リクエスト前後自動)
   - 6.3 [認証イベント](#63-認証イベント)
   - 6.4 [外部API Connectorパターン](#64-外部api-connectorパターン)
   - 6.5 [Token Exchangeパターン](#65-token-exchangeパターン)
   - 6.6 [MySQL（SQLAlchemyイベントリスナー）](#66-mysqlsqlalchemyイベントリスナー)
   - 6.7 [エラーハンドリング（400系・500系）](#67-エラーハンドリング400系500系)
7. [業務イベント別フィールド規則](#7-業務イベント別フィールド規則)
8. [未決定事項](#8-未決定事項)

---

## 1. 概要・設計方針

### 目的

アプリケーション内のログ出力を統一し、障害調査・セキュリティ監査・性能分析を効率化する。

### 基本方針

| 方針 | 内容 |
|---|---|
| 共通ロガー統一 | 全モジュールで `common/logger.py` の `get_logger()` を使用する。直接 `logging.getLogger()` を呼び出してはならない |
| コンテキスト自動付与 | `LoggerAdapter` がリクエスト情報（requestId・endpoint・userId 等）を自動付与する |
| ログ出力の自動化 | リクエスト前後・SQL実行・エラーハンドリングは自動出力。手動出力は認証成功・業務上の意図的なイベントのみ |
| マスキング自動適用 | 特定のキー名（`email` 等）を使用すると LoggerAdapter が自動マスキングする |

### 関連ドキュメント

- [共通仕様書 - ログ出力ポリシー](./common-specification.md#ログ出力ポリシー) — ログレベル定義・出力禁止項目・マスキング方針・ローテーション方針

---

## 2. ロガー実装

### 2.1 共通ロガー（LoggerAdapter）

`src/common/logger.py` に実装する。リクエストコンテキストの自動付与とマスキングを担う。

```python
# common/logger.py

import logging
import re
from flask import g, request, has_request_context

# マスキング対象キーと処理（5章参照）
_MASKING_RULES = {
    "email": lambda v: re.sub(r"(?<=^.{2})[^@]+(?=@)", "****", v) if isinstance(v, str) else v,
    "phone": lambda v: re.sub(r"(\d{3})-(\d{4})-(\d{4})", r"\1-****-\3", v) if isinstance(v, str) else v,
}


class AppLoggerAdapter(logging.LoggerAdapter):
    """リクエストコンテキストの自動付与・マスキングを行う共通ロガー"""

    def process(self, msg, kwargs):
        extra = {}

        # リクエストコンテキストから自動付与（4章参照）
        if has_request_context():
            extra["requestId"] = getattr(g, "request_id", "-")
            extra["method"] = request.method
            extra["endpoint"] = request.path
            extra["ipAddress"] = request.headers.get("X-Forwarded-For", request.remote_addr)
            user_id = getattr(g, "current_user_id", None)
            if user_id is not None:
                extra["userId"] = user_id

        # kwargs から extra を取り出してマスキング適用
        kw_extra = kwargs.pop("extra", {})
        for key, value in kw_extra.items():
            extra[key] = _MASKING_RULES[key](value) if key in _MASKING_RULES else value

        if extra:
            kwargs["extra"] = extra

        return msg, kwargs


def get_logger(name: str) -> AppLoggerAdapter:
    """モジュール共通ロガーを取得する"""
    return AppLoggerAdapter(logging.getLogger(name), {})
```

> **実装注意**: `get_logger()` はモジュールレベルで一度だけ呼ぶ。`process()` がログ呼び出し時に Flask の `g` から遅延読み出しするため、各リクエストで情報は自動的に切り替わる。`before_request` での再初期化は不要・不正。

### 2.2 各モジュールでの使い方

```python
from common.logger import get_logger

logger = get_logger(__name__)  # モジュールレベルで一度だけ宣言する

# 基本
logger.info("処理完了")

# 追加フィールドあり（外部API完了時の例）
logger.info("外部API完了", extra={
    "service": "databricks_scim",
    "operation": "ユーザー作成",
    "duration_ms": 95,
})

# エラー時（スタックトレース自動付与 + 例外クラス名）
logger.error("Internal Server Error", exc_info=True, extra={"error_type": type(e).__name__})

# マスキングあり（認証成功 → email キーで自動マスク）
logger.info("認証成功", extra={"email": "yamada@example.com"})
# → email=ya****@example.com で出力される

# マスキングなし（認証失敗 → raw_email キーでマスクなし。5.2章参照）
logger.warning("認証失敗", extra={"raw_email": "unknown@external.com"})
# → raw_email=unknown@external.com そのままで出力される
```

> リクエスト前後・SQL・エラーのログはフレームワーク側で自動出力されるため、各モジュールで個別に書く必要はない。

### 2.3 requestId 管理

`before_request` フックで UUID v4 を発行し `g.request_id` に保持する。上流ヘッダーからの受け取りは行わない（モノリシック構成のため不要）。LoggerAdapter が全ログに自動付与する。

```python
# src/__init__.py (create_app 内)
import uuid
from flask import g

@app.before_request
def set_request_id():
    g.request_id = str(uuid.uuid4())
```

---

## 3. ログ出力形式・出力先

全環境で標準出力（stdout）に JSON を出力する。Azure App Service は標準出力を収集するため、この形式で統一する。開発環境のみ、追加でテキスト形式のログファイルを出力する。

| 環境 | 出力先 | 形式 |
|---|---|---|
| 全環境 | stdout | JSON（構造化） |
| dev のみ | `app.log` | テキスト（可読性確保） |

```python
# src/__init__.py (create_app 内)
import logging

# 全環境: stdout に JSON 出力
json_handler = logging.StreamHandler()
json_handler.setFormatter(JsonFormatter())  # ライブラリは未決定（8章参照）
app.logger.addHandler(json_handler)

# dev のみ: テキストファイルに追加出力
if ENV == "dev":
    file_handler = logging.FileHandler("app.log")
    file_handler.setFormatter(TextFormatter())
    app.logger.addHandler(file_handler)
```

---

## 4. 自動付与フィールド

LoggerAdapter がリクエストコンテキストから自動付与するフィールド。

| フィールド | 取得元 | 認証前の値 | 備考 |
|---|---|---|---|
| `requestId` | `g.request_id` | `-` | UUID v4（before_request で生成） |
| `method` | `request.method` | `-` | |
| `endpoint` | `request.path` | `-` | |
| `ipAddress` | `X-Forwarded-For` ヘッダー（なければ `request.remote_addr`） | `-` | Azure App Service はリバースプロキシ構成のため優先 |
| `userId` | `g.current_user_id` | 出力しない | 認証後に設定される |

> `organizationId` はセッション管理から除外されたため出力しない。userId があれば組織情報は追跡可能。
> `userAgent` は不採用。BtoB システムのためブラウザ固有調査の需要が低く、ノイズになるため。

---

## 5. マスキング

### 5.1 自動マスキング

LoggerAdapter は以下のキー名を検出して自動マスキングする。**個人情報をログ出力する場合は必ず下記のキー名を使用すること。**

| キー名 | マスキング方式 | 入力例 | 出力例 |
|---|---|---|---|
| `email` | ローカル部の先頭2文字以外を `****` に置換 | `yamada@example.com` | `ya****@example.com` |
| `phone` | 中間4桁を `****` に置換 | `090-1234-5678` | `090-****-5678` |

### 5.2 認証失敗時の非マスク出力

認証失敗ログでは `raw_email` キーを使用する。管理外（未登録）のメールアドレスはマスキング対象外とし、調査に備えて素のアドレスを記録する。`raw_email` はマスキングルールに登録しない。

```python
# 認証失敗時（raw_email を使用してマスキングなしで出力）
logger.warning("認証失敗", extra={"raw_email": "unknown@external.com"})
```

> **理由**: Azure 認証失敗はシステム管理外のメールアドレスが入力されたケース。マスキングすると調査不能になる上、管理外情報のためマスキングの必要性もない。

### 5.3 出力禁止項目

共通仕様書「[出力禁止項目](./common-specification.md#出力禁止項目機密情報)」を参照。Databricks トークン・セッション ID・パスワード等は絶対に出力しない。

---

## 6. ログ出力タイミングと実装パターン

### 6.1 タイミング一覧

| カテゴリ | タイミング | 実装場所 | レベル |
|---|---|---|---|
| リクエスト | 開始 | `before_request` フック | INFO |
| リクエスト | 終了（processingTime 含む） | `after_request` フック | INFO |
| 認証 | IdP 認証成功 | `authenticate_request()` | INFO |
| 外部API（Connector） | 呼び出し前後・失敗（SCIM / Unity Catalog 等） | Connector クラス内 | INFO / ERROR |
| 外部API（Token Exchange） | 呼び出し前後・失敗 | `auth/token_exchange.py` | INFO / ERROR |
| MySQL | 書き込み（INSERT / UPDATE / DELETE） | `src/__init__.py`（SQLAlchemy イベント） | INFO |
| MySQL | SELECT | `src/__init__.py`（SQLAlchemy イベント） | DEBUG |
| エラー | 500 系例外 | `error_handlers.py` | ERROR |
| エラー | 400 系例外（abort(4xx)） | `error_handlers.py` | WARN |

### 6.2 リクエスト前後（自動）

`src/__init__.py` の `create_app()` 内に登録する。

```python
import time
from flask import g

@app.before_request
def log_request_start():
    g.start_time = time.time()
    logger.info("リクエスト開始")

@app.after_request
def log_request_end(response):
    duration_ms = int((time.time() - g.start_time) * 1000)
    logger.info("リクエスト完了", extra={
        "httpStatus": response.status_code,
        "processingTime": duration_ms,
    })
    return response
```

### 6.3 認証イベント

認証成功は `authenticate_request()` で手動出力する。認証失敗は `abort(401)` 後に `error_handlers.py` が自動 WARN 出力する。

```python
# auth/middleware.py

# 認証成功（手動・INFO）
logger.info("認証成功", extra={"email": idp_user_info.get("email")})

# 認証失敗（g に保存 → abort → error_handlers が WARN 出力）
g.failed_email = idp_user_info.get("email")
abort(401)
```

```python
# common/error_handlers.py（401 ハンドラー）
@app.errorhandler(401)
def handle_401(e):
    raw_email = getattr(g, "failed_email", None)
    if raw_email:
        logger.warning("認証失敗", extra={"raw_email": raw_email})
    else:
        logger.warning("認証失敗")
    session.clear()
    return redirect(url_for("auth.login"))
```

### 6.4 外部API Connectorパターン

SCIM / Unity Catalog など専用 Connector クラスを持つ外部 API は `_request()` に集約する。公開メソッドは `operation` を渡すだけでログは自動出力される。

```python
# databricks/scim_client.py
def _request(self, method, endpoint, operation, **kwargs):
    logger.info("外部API呼び出し開始", extra={
        "service": "databricks_scim",
        "operation": operation,
    })
    start = time.time()
    try:
        response = requests.request(...)
        duration_ms = int((time.time() - start) * 1000)
        if not response.ok:
            failure_reason = response.json().get("message", response.text[:200])
            logger.error("外部API失敗", exc_info=False, extra={
                "service": "databricks_scim",
                "operation": operation,
                "status": response.status_code,
                "duration_ms": duration_ms,
                "failure_reason": failure_reason,
            })
            raise SCIMError(response.text)
        logger.info("外部API完了", extra={
            "service": "databricks_scim",
            "operation": operation,
            "duration_ms": duration_ms,
        })
        return response.json()
    except SCIMError:
        raise
    except Exception:
        logger.error("外部API例外", exc_info=True, extra={
            "service": "databricks_scim",
            "operation": operation,
        })
        raise

# 公開メソッドは operation を渡すだけ
def create_user(self, email, display_name):
    return self._request("POST", "/Users", operation="ユーザー作成", json={...})

def delete_user(self, user_id):
    return self._request("DELETE", f"/Users/{user_id}", operation="ユーザー削除")
```

> **注意**: `failure_reason` の抽出方法は API のレスポンス構造によって異なる。各 Connector で適切に実装すること（例: SCIM は `message` フィールド、Unity Catalog は独自構造）。

### 6.5 Token Exchangeパターン

Token Exchange は Connector クラスの `_request()` 抽象化を持たないため、`exchange_token()` メソッド内で直接ログを出力する。フィールド構造は Connector パターンと同じ（`service`, `operation`, `duration_ms` 等）。

```python
# auth/token_exchange.py
def exchange_token(self, idp_jwt: str) -> dict:
    logger.info("外部API呼び出し開始", extra={
        "service": "databricks_token_exchange",
        "operation": "Token Exchange",
    })
    start = time.time()
    response = requests.post(self.token_endpoint, data=payload)
    duration_ms = int((time.time() - start) * 1000)

    if response.status_code != 200:
        logger.error("外部API失敗", exc_info=False, extra={
            "service": "databricks_token_exchange",
            "operation": "Token Exchange",
            "status": response.status_code,
            "duration_ms": duration_ms,
            "failure_reason": response.text[:200],
        })
        raise TokenExchangeError(f"Token Exchange failed: {response.text}")

    logger.info("外部API完了", extra={
        "service": "databricks_token_exchange",
        "operation": "Token Exchange",
        "duration_ms": duration_ms,
    })
    ...
```

### 6.6 MySQL（SQLAlchemyイベントリスナー）

Service 層での手動ログ出力は行わない。`create_app()` 内で SQLAlchemy イベントリスナーを登録し、全 SQL 実行を自動でログ出力する。

```python
# src/__init__.py (create_app 内、db.init_app(app) の直後)
from sqlalchemy import event
from sqlalchemy.engine import Engine
import logging
import time

@event.listens_for(Engine, "before_cursor_execute")
def _before_sql(conn, cursor, statement, parameters, context, executemany):
    conn.info.setdefault("_sql_start", []).append(time.time())

@event.listens_for(Engine, "after_cursor_execute")
def _after_sql(conn, cursor, statement, parameters, context, executemany):
    duration_ms = int((time.time() - conn.info["_sql_start"].pop()) * 1000)
    is_select = statement.strip().upper().startswith("SELECT")
    level = logging.DEBUG if is_select else logging.INFO
    logger.log(level, "SQL実行", extra={"query": statement, "duration_ms": duration_ms})
```

Service 層の実装例（ログ出力コードは不要）：

```python
# services/user_service.py
def create_user(email, ...):
    _create_databricks_user(email)   # DatabricksSCIMClient が自動ログ
    _register_unity_catalog(email)   # UnityCatalogConnector が自動ログ
    user = User(email=email, ...)
    db.session.add(user)
    db.session.commit()
    # ← SQLAlchemy イベントリスナーが INSERT ログを自動出力するため手動出力不要
```

### 6.7 エラーハンドリング（400系・500系）

`error_handlers.py` がすべての HTTP エラーを一元的にログ出力する。

```python
# common/error_handlers.py

@app.errorhandler(Exception)
def handle_500(e):
    logger.error(
        "Internal Server Error",
        exc_info=True,                              # スタックトレース自動付与
        extra={"error_type": type(e).__name__},     # 例外クラス名
    )
    return render_template("errors/500.html"), 500

# 400系は一律 WARN（401 は 6.3 参照）
@app.errorhandler(400)
@app.errorhandler(403)
@app.errorhandler(404)
def handle_4xx(e):
    logger.warning("Client Error", extra={"httpStatus": e.code})
    # 400系はモーダル表示（共通仕様書参照）
    ...
```

---

## 7. 業務イベント別フィールド規則

カテゴリ別に必須フィールドを定義する。呼び出し側はこれに従うこと。

| カテゴリ | 必須フィールド | 例 |
|---|---|---|
| 認証成功 | `email`（マスク自動適用） | `extra={"email": "yamada@example.com"}` |
| 認証失敗 | `raw_email`（マスクなし） | `extra={"raw_email": "unknown@external.com"}` |
| 外部API呼び出し | `service`, `operation`, `duration_ms` | `extra={"service": "databricks_scim", "operation": "ユーザー作成", "duration_ms": 95}` |
| 外部API失敗 | 上記 + `status`, `failure_reason` | `extra={..., "status": 400, "failure_reason": "user already exists"}` ※ API ごとに抽出方法が異なる |
| DB操作（MySQL） | `query`, `duration_ms` | SQLAlchemy イベントリスナーが自動付与 |
| 400系エラー | `httpStatus` | `extra={"httpStatus": e.code}` |
| 500エラー | 例外クラス名・スタックトレース（自動） | `exc_info=True` で自動付与。任意で `extra={"error_type": type(e).__name__}` |

---

## 8. 未決定事項

| 項目 | 状況 |
|---|---|
| JSON フォーマッターの実装ライブラリ（`python-json-logger` 等） | 要検討 |
