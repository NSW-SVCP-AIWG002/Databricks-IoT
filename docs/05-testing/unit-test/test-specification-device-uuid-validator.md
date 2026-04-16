# 単体テスト仕様書 - device_uuidバリデータ

## 対象ファイル

| 対象 | パス |
| ---- | ---- |
| テスト対象実装 | `src/iot_app/validators/device_uuid_validator.py` |
| テストコード | `tests/unit/validators/test_device_uuid_validator.py` |

## 参照ドキュメント

| 種別 | パス |
| ---- | ---- |
| 機能設計書 | `docs/03-features/flask-app/device-inventory/workflow-specification.md` |
| 単体テスト観点表 | `docs/05-testing/unit-test/unit-test-perspectives.md` |
| 実装ガイド | `docs/05-testing/unit-test/unit-test-guide.md` |

---

## テスト対象関数

| 関数名 | 概要 |
| ------ | ---- |
| `get_device_uuid_validator()` | AUTH_TYPE 環境変数に基づきバリデータ辞書を返す |
| `validate_device_uuid(device_uuid)` | device_uuid の文字数・パターン検証を実行し `(bool, str)` を返す |

---

## テストケース一覧

### 1. TestGetDeviceUuidValidator

観点: `1.1.6 不整値チェック`、`2.1 正常系処理`

| No | テストメソッド | 観点 | 実行内容 | 想定結果 |
| -- | -------------- | ---- | -------- | -------- |
| 1 | `test_returns_azure_validator_when_auth_type_is_azure` | 2.1.1 | AUTH_TYPE=azure で `get_device_uuid_validator()` を呼ぶ | max_length=128、pattern・description キーを持つ辞書が返る |
| 2 | `test_returns_aws_validator_when_auth_type_is_aws` | 2.1.1 | AUTH_TYPE=aws で `get_device_uuid_validator()` を呼ぶ | aws 用パターン（英数字・ハイフン・アンダースコアのみ）の辞書が返る |
| 3 | `test_returns_same_as_azure_when_auth_type_is_local` | 2.1.1 | AUTH_TYPE=local で呼ぶ | azure バリデータと同じ pattern・max_length が返る |
| 4 | `test_defaults_to_azure_when_auth_type_not_set` | 2.1.1 | AUTH_TYPE 未設定で呼ぶ | デフォルト値 'azure' が使われ max_length=128 が返る |
| 5 | `test_raises_value_error_when_auth_type_is_unknown` | 1.1.6.1 | AUTH_TYPE=unknown_provider で呼ぶ | `ValueError: Unknown AUTH_TYPE: unknown_provider` が送出される |

---

### 2. TestValidateDeviceUuid

観点: `1.1.2 最大文字列長チェック`、`1.1.6 不整値チェック`、`2.1 正常系処理`

| No | テストメソッド | 観点 | 実行内容 | 想定結果 |
| -- | -------------- | ---- | -------- | -------- |
| 6 | `test_valid_azure_uuid_returns_true_and_empty_message` | 2.1.1 | AUTH_TYPE=azure で有効な UUID を渡す | `(True, '')` が返る |
| 7 | `test_valid_aws_uuid_returns_true_and_empty_message` | 2.1.1 | AUTH_TYPE=aws で有効な UUID を渡す | `(True, '')` が返る |
| 8 | `test_uuid_at_max_length_returns_true` | 1.1.2.1 | ちょうど 128 文字の UUID を渡す | `(True, '')` が返る（境界値: 有効） |
| 9 | `test_uuid_over_max_length_returns_false_with_message` | 1.1.2.2 | 129 文字の UUID を渡す | `(False, 'device_uuidは128文字以内で入力してください')` が返る（境界値: 無効） |
| 10 | `test_invalid_chars_for_azure_returns_false_with_message` | 1.1.6.1 | AUTH_TYPE=azure でスペースを含む UUID を渡す | `(False, 'device_uuidの形式が不正です...')` が返る |
| 11 | `test_invalid_chars_for_aws_returns_false_with_message` | 1.1.6.1 | AUTH_TYPE=aws でドットを含む UUID を渡す | `(False, 'device_uuidの形式が不正です...')` が返る |
| 12 | `test_length_error_message_includes_max_length` | 1.1.2.2 | 200 文字の UUID を渡す | エラーメッセージに '128' が含まれる |
| 13 | `test_pattern_error_message_includes_description` | 1.1.6.1 | AUTH_TYPE=azure でパターン不一致の UUID を渡す | エラーメッセージに azure の description 文言が含まれる |

---

## テストケース合計

| クラス | テスト数 |
| ------ | -------- |
| TestGetDeviceUuidValidator | 5 |
| TestValidateDeviceUuid | 8 |
| **合計** | **13** |

---

## 変更履歴

| 日付 | 版数 | 変更内容 | 担当者 |
| ---- | ---- | -------- | ------ |
| 2026-04-15 | 1.0 | 初版作成 | Kei Sugiyama |
