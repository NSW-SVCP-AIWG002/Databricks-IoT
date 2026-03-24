"""
auth/ 単体テストパッケージ

## テストスコープ

Azure 環境（Easy Auth）を前提とした認証モジュールの単体テスト。
AWS・オンプレミス固有の機能はスコープ外。

## 対象ファイルと除外理由

| ファイル                        | 対応テスト                    | 備考                                              |
| ------------------------------- | ----------------------------- | ------------------------------------------------- |
| auth/exceptions.py              | test_exceptions.py            | -                                                 |
| auth/factory.py                 | test_factory.py               | -                                                 |
| auth/middleware.py              | test_middleware.py            | -                              |
| auth/token_exchange.py          | test_token_exchange.py        | -                                |
| auth/providers/azure_easy_auth.py | providers/test_azure_easy_auth.py | -                                             |
| auth/services.py                | test_services.py              | `find_user_by_email()`  |
| auth/providers/base.py          | **対象外**                    | 抽象基底クラスのみ（テスト可能なロジックなし）    |
| auth/routes.py                  | **対象外**                    | Flaskルート定義 → 結合テスト対象                  |
"""
