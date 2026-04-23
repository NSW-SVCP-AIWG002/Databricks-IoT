# テストコードレビュー結果 - ユーザー管理機能 Service層

**対象テストコード:** `tests/unit/services/test_user_service.py`
**対象テスト項目書:** `docs/05-testing/unit-test/users/テスト項目書_ユーザー管理機能Service層.md`
**レビュー日:** 2026-04-23

---

## チェックリスト確認結果

| チェックID | 確認結果 | 備考 |
|-----------|---------|------|
| CL-1-1 | OK | 全DB操作・APIリクエストで全フィールドアサートあり |
| CL-1-2 | OK | No.88（search_users）/ No.89（get_all_users_for_export）で全フィルター条件を同時指定するテストを追加済み |
| CL-2-1 | OK | create_user / update_user / delete_user 各失敗パターンで例外伝播テストあり |
| CL-2-2 | OK | サービス層は例外レベルで検証（SCIM clientテストで4xx/5xxカバー済み） |
| CL-3   | OK | サービス層のため非該当 |
| CL-4-1 | OK | No.77 で全8列名を検証 |
| CL-4-2 | OK | No.90 で全8列値を一括検証するテストを追加済み |
| CL-4-3 | **指摘あり** | 下記No.5 参照（代表1件で対応予定） |
| CL-5-1 | OK | MODULE = 'iot_app.services.user_service' を使用し全パスが正しい |
| CL-5-2 | OK | 全テストメソッドのdocstringに観点番号と概要あり |
| CL-6-1 | OK | テスト項目書87件 = テストコード87メソッド |
| CL-6-2 | OK | No.1〜87 重複・欠番なし |
| CL-6-3 | OK | 現時点で変更なし |

---

## 指摘一覧

| No | 対象ファイル | 対象テスト / 行 | 指摘内容 | 対応観点 | 修正案 | 対応状況 |
|----|-------------|----------------|----------|----------|--------|--------|
| 1 | test_user_service.py | TestSearchUsers 全体 | `organization_id`, `region_id`, `status` の各フィルター条件を個別に検証するテストがない。`user_type_id` のみカバー（No.8）。 | CL-1-2 / 3.1.1 | 全フィルター条件を同時指定するテストを1件追加する | **解決済み**（No.88追加） |
| 2 | test_user_service.py | TestGetAllUsersForExport 全体 | `email_address`, `organization_id`, `region_id`, `status`, `user_type_id` のフィルター条件が個別にテストされていない。`user_name` のみカバー（No.75）。 | CL-1-2 / 3.1.1 | 全フィルター条件を同時指定するテストを1件追加する | **解決済み**（No.89追加） |
| 3 | test_user_service.py | test_none_relationship_outputs_empty_string / L1441 | `rows[1][5]` を検証しているが、列順序仕様（No.80）によると所属組織名は index 4、index 5 はユーザー種別。テストがアサートしている列が仕様と食い違っている可能性がある。 | CL-4-2 / CL-4-3 | `rows[1][4]`（所属組織名）が `''` になることを検証するよう修正する。 | **解決済み**（`rows[1][5]`→`rows[1][4]`、テスト項目書No.87も修正済み） |
| 4 | test_user_service.py | TestGenerateUsersCsv 全体 | データ行の全8列の値を一括検証するテストがない。 | CL-4-2 | 1件のユーザーを渡し、`rows[1][0]`〜`rows[1][7]` の全列値を検証するテストを追加する | **解決済み**（No.90追加） |
| 5 | test_user_service.py | TestGenerateUsersCsv 全体 | `user_type` リレーション属性が `None` のとき（No.87 は `organization=None` のみカバー）のテストがない。`user.user_type = None` の場合 `user_type_name` アクセスで AttributeError が発生する可能性がある。 | CL-4-3 | `user_type=None` のとき該当列（ユーザー種別）が空文字で出力されるテストを代表1件追加する | **保留**（後日対応） |

---

## 補足

- **No.3 は優先度高**: 実装と列インデックスがずれている場合、organization=None のテストが意図しない列を検証していることになる。実装ファイル（`user_service.py`）の CSV 生成コードで列順序を確認してから修正すること。
- **No.1・No.2 は優先度中**: 検索フィルター条件の網羅性。実装上は同じロジックを共有している可能性が高いが、個別に検証することで回帰を防げる。
- **No.4 は優先度低**: 現状のテストで機能的な問題はないが、全列値の一括検証があることでリファクタリング時の安全性が高まる。
- **No.5 は優先度中**: CSV 生成時に None リレーション属性へのアクセスが発生する場合、実行時エラーになるため確認が必要。
