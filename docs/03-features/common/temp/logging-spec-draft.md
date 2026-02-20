# ログ出力仕様 検討ドラフト

> **ステータス**: レビュー待ち（確定後 `common-specification.md` に反映）
> **目的**: 既存の共通仕様書「ログ出力ポリシー」セクションに不足している実装方針を補足する

---

## 1. 既存仕様との差分サマリー

既存の `common-specification.md` にはログレベル定義・必須項目・マスキング方針は記載済み。
本ドキュメントでは以下の未定義事項を補足する。

| 項目 | 既存仕様 | 本ドラフトでの決定 |
|---|---|---|
| requestId 生成方式 | 記載なし | UUID自前発行、`before_request`で生成 |
| ログ出力形式 | 記載なし | dev=テキスト、stg/prod=JSON |
| 共通ロガー実装 | 記載なし | `LoggerAdapter`（`common/logger.py`） |
| マスキング実装方式 | 方針のみ | LoggerAdapterが自動マスキング（キー名ベース） |
| ログ出力タイミング | リクエスト・エラーのみ言及 | カテゴリ別に整理（本ドラフト7章）。500系はerror_handlers自動ログで補足するため認証カテゴリの手動ERRORログは不要 |
| 外部API呼び出しログ | 記載なし | Connectorクラスパターン（SCIM / Unity Catalog を同列に扱う） |
| MySQL クエリログ | 記載なし | 業務書き込みINFO（Service層で手動出力） |
| organizationId | 必須項目に記載あり | セッションから除外されたため出力しない |
| errorCode | `TokenExchangeError`のみ定義 | スコープ外・削除（例外クラス名で代替） |
| ipAddress | 必須項目に記載あり | 採用。`X-Forwarded-For` 優先（Azure App Service はリバースプロキシ構成のため） |
| userAgent | 必須項目に記載あり | 不採用。BtoBシステムのためブラウザ固有調査の需要が低く、ログのノイズになるため |

---

## 2. 共通ロガー実装方針

### 2.1 LoggerAdapter パターン

全モジュールで `common/logger.py` の `get_logger()` を使用する。
直接 `logging.getLogger()` を呼び出してはならない。

```python
# common/logger.py

import logging
import json
import re
import time
import uuid
from flask import g, request, has_request_context


# マスキング対象キーと処理（4章参照）
_MASKING_RULES = {
    "email": lambda v: re.sub(r"(?<=^.{2})[^@]+(?=@)", "****", v) if isinstance(v, str) else v,
    "phone": lambda v: re.sub(r"(\d{3})-(\d{4})-(\d{4})", r"\1-****-\3", v) if isinstance(v, str) else v,
}


class AppLoggerAdapter(logging.LoggerAdapter):
    """リクエストコンテキストの自動付与・マスキングを行う共通ロガー"""

    def process(self, msg, kwargs):
        extra = {}

        # リクエストコンテキストから自動付与（6章参照）
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

### 2.2 各モジュールでの使い方

```python
from common.logger import get_logger

logger = get_logger(__name__)

# 基本
logger.info("処理完了")

# 追加フィールドあり
logger.info("CSVインポート完了", extra={"count": 500})

# エラー（スタックトレース付き）
logger.error("Token Exchange失敗", exc_info=True, extra={"service": "databricks"})

# マスキング対象キーはそのまま渡す（自動マスク）
logger.warning("認証失敗", extra={"email": "yamada@example.com"})
# → email=ya****@example.com で出力される
```

---

## 3. requestId 生成方式

- `before_request` フックで UUID v4 を発行し `g.request_id` に保持する
- 上流ヘッダーからの受け取りは行わない（モノリシック構成のため不要）
- LoggerAdapter が全ログに自動付与する

```python
# __init__.py (create_app 内)
import uuid
from flask import g

@app.before_request
def set_request_id():
    g.request_id = str(uuid.uuid4())
```

---

## 4. マスキング定義

### 4.1 自動マスキング対象キー

LoggerAdapter は以下のキー名を検出して自動マスキングする。
**個人情報をログ出力する場合は必ず下記のキー名を使用すること。**

| キー名 | マスキング方式 | 入力例 | 出力例 |
|---|---|---|---|
| `email` | ローカル部の先頭2文字以外を `****` に置換 | `yamada@example.com` | `ya****@example.com` |
| `phone` | 中間4桁を `****` に置換 | `090-1234-5678` | `090-****-5678` |

### 4.2 出力禁止項目（変更なし）

既存仕様書の「出力禁止項目」を参照。Databricksトークン・セッションID・パスワード等は絶対に出力しない。

---

## 5. ログ出力形式

環境によってフォーマッターを切り替える。

| 環境 | 形式 | 理由 |
|---|---|---|
| dev | テキスト | 開発時の可読性 |
| stg / prod | JSON | Azure Log Analytics でフィールド単位のクエリが可能 |

```python
# config.py
if ENV in ("stg", "prod"):
    formatter = JsonFormatter()   # 構造化JSON
else:
    formatter = TextFormatter()   # 人間が読めるテキスト
```

---

## 6. 自動付与フィールド

LoggerAdapter がリクエストコンテキストから自動付与するフィールド。

| フィールド | 取得元 | 認証前の値 |
|---|---|---|
| `requestId` | `g.request_id` | `-` |
| `method` | `request.method` | `-` |
| `endpoint` | `request.path` | `-` |
| `ipAddress` | `X-Forwarded-For` ヘッダー（なければ `request.remote_addr`） | `-` |
| `userId` | `g.current_user_id` | 出力しない |

> `organizationId` はセッション管理から除外されたため出力しない。ユーザーIDがあれば組織情報は追跡可能。
> `userAgent` は不採用。BtoBシステムのためブラウザ固有調査の需要が低く、ログのノイズになるため。

---

## 7. ログ出力タイミング パターン

### 7.1 タイミング一覧

| カテゴリ | タイミング | 実装場所 | レベル | 共通化 |
|---|---|---|---|---|
| リクエスト | 開始 | `before_request` フック | INFO | 自動 |
| リクエスト | 終了（processingTime含む） | `after_request` フック | INFO | 自動 |
| 認証 | IdP認証成功 | `authenticate_request()` | INFO | 手動 |
| 認証 | IdP認証失敗（UnauthorizedError） | `authenticate_request()` | WARN | 手動 |
| 外部API | 呼び出し前後・失敗（SCIM / Unity Catalog 等） | Connectorクラス内 | INFO / ERROR | 自動（クラス集約） |
| MySQL | 業務上重要な書き込み（INSERT/UPDATE/DELETE） | Service層 | INFO | 手動 |
| エラー | 500系例外 | `error_handlers.py` | ERROR | 自動 |
| エラー | 400系業務エラー | 各 except ブロック | WARN | 手動 |

### 7.2 リクエスト前後（自動）

```python
@app.before_request
def log_request_start():
    g.start_time = time.time()
    logger.info("リクエスト開始")

@app.after_request
def log_request_end(response):
    duration_ms = int((time.time() - g.start_time) * 1000)
    logger.info("リクエスト完了", extra={"httpStatus": response.status_code, "processingTime": duration_ms})
    return response
```

### 7.3 認証イベント（手動）

```python
# auth/middleware.py
except UnauthorizedError:
    logger.warning("IdP認証失敗", extra={"email": idp_user_info.get("email")})
    ...

logger.info("認証成功", extra={"email": idp_user_info.get("email")})
```

### 7.4 外部API Connectorクラスパターン

SCIM APIのように専用Connectorクラスを持つ外部APIは `_request()` に集約する。

```python
# 例: db/databricks_scim_client.py
def _request(self, method, endpoint, operation, **kwargs):
    logger.info("外部API呼び出し開始", extra={"service": "databricks_scim", "operation": operation})
    start = time.time()
    try:
        response = requests.request(...)
        duration_ms = int((time.time() - start) * 1000)
        if not response.ok:
            logger.error("外部API失敗", exc_info=False,
                         extra={"service": "databricks_scim", "operation": operation,
                                "status": response.status_code, "duration_ms": duration_ms})
            raise SCIMError(response.text)
        logger.info("外部API完了",
                    extra={"service": "databricks_scim", "operation": operation, "duration_ms": duration_ms})
        return response.json()
    except SCIMError:
        raise
    except Exception:
        logger.error("外部API例外", exc_info=True, extra={"service": "databricks_scim", "operation": operation})
        raise

# 公開メソッドは operation を渡すだけ
def create_user(self, email, display_name):
    return self._request("POST", "/Users", operation="ユーザー作成", json={...})

def delete_user(self, user_id):
    return self._request("DELETE", f"/Users/{user_id}", operation="ユーザー削除")
```

### 7.5 MySQL ログ方針

業務上重要な書き込み操作はService層で手動出力：

```python
# services/user_service.py
def create_user(email, ...):
    _create_databricks_user(email)      # DatabricksSCIMClient が自動ログ
    _register_unity_catalog(email)      # UnityCatalogConnector が自動ログ
    user = User(email=email, ...)
    db.session.add(user)
    db.session.commit()
    logger.info("MySQLユーザー登録完了", extra={"db": "mysql", "user_id": user.id})  # 手動
```

---

## 8. 業務イベントログのフィールド規則

カテゴリ別に必須フィールドを定義する。呼び出し側はこれに従うこと。

| カテゴリ | 必須フィールド | 例 |
|---|---|---|
| 外部API呼び出し | `service`, `operation`, `duration_ms` | `extra={"service": "databricks_scim", "operation": "ユーザー作成", "duration_ms": 95}` |
| 認証イベント | `email`（マスク自動適用） | `extra={"email": "yamada@example.com"}` |

---

## 9. 未決定事項

| 項目 | 状況 |
|---|---|
| JSON フォーマッターの具体的な実装ライブラリ（`python-json-logger` 等） | 要検討 |
| Teams通知クラスのConnectorパターン適用 | 実装時に本パターンに準拠 |
