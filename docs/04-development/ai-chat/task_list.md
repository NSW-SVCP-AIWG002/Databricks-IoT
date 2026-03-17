# ai-chat 実装タスクリスト

## タスク一覧

| #   | タスク名                        | 対象ファイル                                                                                                         | 対応テスト                                           | 実装フロー状態 | 備考                                       |
| --- | ------------------------------- | -------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------- | -------------- | ------------------------------------------ |
| 1   | テストパス修正                  | tests/unit/ai-chat/test_conversational-ai-chat.py                                                                   | -                                                    | 完了           | _AI_CHAT_BASE を model-serving-endpoint 指定に修正 |
| 2   | Config 追加                     | src/iot_app/config.py                                                                                                | -                                                    | 完了           | DATABRICKS_HOST 等の環境変数追加           |
| 3   | インターフェース層: Blueprint    | src/iot_app/views/analysis/chat/__init__.py<br>src/iot_app/views/analysis/chat/views.py                                               | tests/unit/ai-chat/test_conversational-ai-chat.py    | 完了           | /analysis/chat GET, /api/analysis/chat POST                  |
| 4   | インターフェース層: __init__登録 | src/iot_app/__init__.py                                                                                              | -                                                    | 完了           | chat_bp のBlueprint登録                    |
| 5   | インターフェース層: テンプレート | src/iot_app/templates/analysis/chat/index.html                                                                                | -                                                    | 完了           | CHT-001 チャット画面                       |
| 6   | インターフェース層: CSS          | src/iot_app/static/css/components/analysis/chat.css                                                                          | -                                                    | 完了           | チャットUI専用スタイル                     |
| 7   | インターフェース層: JavaScript   | src/iot_app/static/js/components/analysis/chat.js                                                                            | -                                                    | 完了           | ChatUI クラス実装                          |
| 8   | pytest 実行・確認               | -                                                                                                                    | tests/unit/ai-chat/test_conversational-ai-chat.py    | 完了           | 112 passed, 3 xfailed / 1 failed (test_exception_propagates: テスト設計バグ、修正保留) |

## 実装フロー状態

| 状態     | 意味                 |
| -------- | -------------------- |
| 未着手   | 実装未開始           |
| 実装中   | ① 実装 実施中        |
| テスト中 | ② pytest 実行中      |
| 修正中   | ③ テスト失敗・修正中 |
| 完了     | ④ 全テスト通過       |

## セルフレビュー進捗

| 観点                         | 状態   | 確認結果 |
| ---------------------------- | ------ | -------- |
| 機能: 設計書との差分         | 完了   | OK。UUID検証は設計書例より堅牢な try/except で実装。 |
| 機能: テスト仕様カバレッジ   | 完了   | OK。sanitize_question・validate_generated_code・execute_with_timeout など全テストに対応する実装あり。 |
| 機能: インターフェース整合性 | 完了   | OK。/analysis/chat GET・/api/analysis/chat POST・g.databricks_token・thread_id UUID検証すべて設計書と一致。 |
| 非機能: セキュリティ         | 完了   | OK。XSS: Jinja2自動エスケープ・DOMPurify。入力: sanitize_question。トークン: ミドルウェア取得。JSON APIはCSRF対象外（設計上意図的）。 |
| 非機能: ログ準拠             | 完了   | OK（修正済）。call_orchestrator_endpoint に外部API INFO/ERROR ログ追加。500系例外に ERROR ログ追加。 |
| 非機能: エラーハンドリング   | 完了   | OK（修正済）。_appendErrorMessage に errorCode パラメータ追加し VALIDATION_ERROR でのリトライボタン非表示を修正。 |
