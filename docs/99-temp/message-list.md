# メッセージ一覧・共通化検討

> 作成日: 2026-04-14  
> 対象: Flaskアプリ（`src/iot_app/` ※ `model-serving-endpoint/` 除く）
> 検索方法: 日本語文字（ひらがな・カタカナ・漢字）を含む文字列リテラルを全抽出

---

## 1. 現状メッセージ一覧

### 1-1. views — 成功メッセージ（jsonify message）

| 文言 | ファイル:行 | 設計書記載 |
|---|---|---|
| ダッシュボードを登録しました | customer_dashboard/common.py:239 | あり（common/workflow-specification.md:851 / SUC_001） |
| ダッシュボードタイトルを更新しました | customer_dashboard/common.py:308 | あり（common/workflow-specification.md:1092 / SUC_002） |
| ダッシュボードを削除しました | customer_dashboard/common.py:362 | あり（common/workflow-specification.md:1287 / SUC_003） |
| ダッシュボードグループを登録しました | customer_dashboard/common.py:435 | あり（common/workflow-specification.md:1435 / SUC_004） |
| ダッシュボードグループタイトルを更新しました | customer_dashboard/common.py:504 | あり（common/workflow-specification.md:1558 / SUC_005） |
| ダッシュボードグループを削除しました | customer_dashboard/common.py:558 | あり（common/workflow-specification.md:1720 / SUC_006） |
| ガジェットタイトルを更新しました | customer_dashboard/common.py:672 | あり（common/workflow-specification.md:1940 / SUC_008） |
| ガジェットを削除しました | customer_dashboard/common.py:726 | あり（common/workflow-specification.md:2043 / SUC_009） |
| レイアウトを保存しました | customer_dashboard/common.py:777 | あり（common/workflow-specification.md:2155 / SUC_010） |
| ガジェットを登録しました | bar_chart.py:186 / belt_chart.py:212 / circle_chart.py:185 / timeline.py:208 | あり（各ガジェット種 workflow-specification.md） |

### 1-2. views — エラーメッセージ（jsonify error）

| 文言 | ファイル:行 | HTTP | 設計書記載 |
|---|---|---|---|
| 指定されたガジェットが見つかりません | bar_chart:41 / belt_chart:67 / circle_chart:47 / timeline:49 | 404 | あり（common/workflow-specification.md:1962） |
| アクセス権限がありません | bar_chart:45 / circle_chart:50 / timeline:53 | 404 | **なし** |
| 測定項目が見つかりません | bar_chart:71 | 500 | **なし** |
| データの取得に失敗しました | bar_chart:89 / belt_chart:113 / circle_chart:87 / timeline:111 | 500 | あり（common/workflow-specification.md:586 / ERR_001） |
| 追加予定のガジェットです | common.py:590 | 404 | **なし** |
| レイアウトの保存に失敗しました | common.py:782 | 500 | あり（common/workflow-specification.md:2160 / ERR_011） |
| デバイス一覧の取得に失敗しました | common.py:809 | 500 | あり（common/workflow-specification.md:2400） |
| データソース設定の保存に失敗しました | common.py:835 | 500 | あり（common/workflow-specification.md:2421） |

### 1-3. views — AIチャット エラーメッセージ

| 文言 | ファイル:行 | 種別 | 設計書記載 |
|---|---|---|---|
| 質問を入力してください | chat/views.py:131 | 入力バリデーション | あり（conversational-ai-chat/workflow-specification.md:331） |
| 質問は1000文字以内で入力してください | chat/views.py:138 | 入力バリデーション | あり（conversational-ai-chat/workflow-specification.md:338） |
| thread_idが指定されていません | chat/views.py:146 | 入力バリデーション | あり（conversational-ai-chat/workflow-specification.md:345） |
| 回答の取得がタイムアウトしました。しばらく経ってから再度お試しください。 | chat/views.py:181 | システムエラー | あり（conversational-ai-chat/workflow-specification.md:805） |
| 接続エラーが発生しました。しばらく経ってから再度お試しください。 | chat/views.py:192 | システムエラー | あり（conversational-ai-chat/workflow-specification.md:806） |
| 回答の生成に失敗しました。しばらく経ってから再度お試しください。 | chat/views.py:205 | システムエラー | あり（conversational-ai-chat/workflow-specification.md:302,374） |

### 1-4. common/error_handlers.py — HTTPエラー文言

| コード | タイトル | メッセージ | 設計書記載 |
|---|---|---|---|
| 400 | 不正なリクエストです | リクエストの内容が正しくありません。 | **なし** |
| 403 | アクセスできません | このアプリケーションへのアクセス権限がありません。\nシステム管理者にお問い合わせください。 | **なし** |
| 404 | ページが見つかりません | お探しのページは存在しないか、削除された可能性があります。 | **なし** |
| 409 | 競合が発生しました | 他の操作と競合が発生しました。再度お試しください。 | **なし** |
| （デフォルト） | エラー | エラーが発生しました。 | **なし** |

### 1-5. forms — バリデーションメッセージ

#### 共通（customer_dashboard/common.py）

| 文言 | 対象フィールド |
|---|---|
| ダッシュボードタイトルを入力してください | DashboardForm.title |
| ダッシュボードタイトルは50文字以内で入力してください | DashboardForm.title |
| ダッシュボードグループタイトルを入力してください | DashboardGroupForm.title |
| ダッシュボードグループタイトルは50文字以内で入力してください | DashboardGroupForm.title |
| ガジェットタイトルを入力してください | GadgetForm.title |
| ガジェットタイトルは20文字以内で入力してください | GadgetForm.title |

#### 棒グラフ（customer_dashboard/bar_chart.py）

| 文言 | 対象フィールド |
|---|---|
| タイトルを入力してください | title |
| タイトルは20文字以内で入力してください | title |
| 表示デバイスを選択してください | device_mode |
| グループを選択してください | group_id |
| 集約方法を選択してください | summary_method_id |
| 表示項目を選択してください | measurement_item_id |
| デバイスを選択してください | device_id（カスタムバリデーション） |
| 最小値は最大値より小さい値を入力してください | min_value |
| 最大値は最小値より大きい値を入力してください | max_value |
| 部品サイズを選択してください | gadget_size |

#### ベルトチャート（customer_dashboard/belt_chart.py）

| 文言 | 対象フィールド |
|---|---|
| タイトルを入力してください | title |
| タイトルは20文字以内で入力してください | title |
| 表示デバイスを選択してください | device_mode |
| グループを選択してください | group_id |
| 集約方法を選択してください | summary_method_id |
| 部品サイズを選択してください | gadget_size |
| 表示項目を1つ以上5つ以下で選択してください | カスタムバリデーション |
| デバイスを選択してください | device_id（カスタムバリデーション） |

#### 円グラフ（customer_dashboard/circle_chart.py）

| 文言 | 対象フィールド |
|---|---|
| タイトルを入力してください | title |
| タイトルは20文字以内で入力してください | title |
| 表示デバイスを選択してください | device_mode |
| グループを選択してください | group_id |
| 表示項目を1つ以上5つ以下で選択してください | カスタムバリデーション |
| デバイスを選択してください | device_id（カスタムバリデーション） |

#### 時系列（customer_dashboard/timeline.py）

| 文言 | 対象フィールド |
|---|---|
| タイトルを入力してください | title |
| タイトルは20文字以内で入力してください | title |
| 表示デバイス選択を選択してください | device_mode（※「表示デバイスを選択してください」と不統一） |
| グループを選択してください | group_id |
| 左表示項目を選択してください | left_measurement_item_id |
| 右表示項目を選択してください | right_measurement_item_id |
| 左表示項目の最小値は数値で入力してください | left_min_value |
| （他最大値・右側も同様） | |

### 1-6. services — バリデーションメッセージ（customer_dashboard/bar_chart.py）

| 文言 |
|---|
| 最大値は数値で入力してください |
| 最小値は最大値より小さい値を入力してください。最大値は最小値より大きい値を入力してください。 |
| 部品サイズを選択してください |
| 部品サイズが不正です |
| 表示単位が不正です |
| 集計間隔が不正です |
| 日付形式が不正です |
| タイトルを入力してください |
| タイトルは20文字以内で入力してください |

### 1-7. static/js — Toast表示メッセージ

| 文言 | ファイル:行 | 種別 | 設計書記載 |
|---|---|---|---|
| 削除するダッシュボードを選択してください | common.js:134 | error | **なし** |
| 切り替えるダッシュボードを選択してください | common.js:147 | error | **なし** |
| ダッシュボードの切り替えに失敗しました | common.js:160 | error | **なし** |
| 通信エラーが発生しました | common.js:451 | error | **なし** |
| 開始日時を入力してください | common.js:589 | error | あり（common/workflow-specification.md:2246） |
| 終了日時を入力してください | common.js:590 | error | あり（common/workflow-specification.md:2247） |
| 開始日時は終了日時より前に設定してください | common.js:592 | error | あり（common/workflow-specification.md:2248） |
| CSVのダウンロードに失敗しました | bar_chart.js:250 / timeline.js:377 | error | **なし** |

---

## 2. 共通化検討

### 2-1. パターン分類

#### Python側（views・forms・services）

| パターン | 件数 | 共通化案 |
|---|---|---|
| `{対象}を登録しました` | 6 | `msg_created(subject)` |
| `{対象}を更新しました` / `{対象}タイトルを更新しました` | 3 | `msg_updated(subject)` ※後述 |
| `{対象}を削除しました` | 3 | `msg_deleted(subject)` |
| `{対象}を保存しました` | 1 | `msg_saved(subject)` |
| `指定された{対象}が見つかりません` | 4ファイル重複 | `err_not_found(subject)` |
| `{対象}の取得に失敗しました` | 5 | `err_fetch_failed(subject)` |
| `{対象}の保存に失敗しました` | 2 | `err_save_failed(subject)` |
| `{対象}を入力してください` | 多数 | `err_required(subject)` |
| `{対象}は{n}文字以内で入力してください` | 多数 | `err_max_length(subject, n)` |
| `{対象}を選択してください` | 多数 | `err_select_required(subject)` |
| `{対象}が不正です` | 複数 | `err_invalid(subject)` |

#### JS側（Toast）

JSファイルはPythonの `messages.py` で管理できないため、**JSの定数ファイル（`messages.js`）を別途作成**するか、現状維持かの判断が必要。

### 2-2. 未解消の不統一

| 問題 | 箇所 | 対応方針 |
|---|---|---|
| `表示デバイスを選択してください` と `表示デバイス選択を選択してください` が混在 | timeline.py vs 他 | `表示デバイスを選択してください` に統一（**確定**） |
| forms と services で同じ文言が重複定義（例: `タイトルを入力してください`） | bar_chart.py 等 | messages.py 導入で解消 |

> ※更新系メッセージ（`ダッシュボードタイトルを更新しました` 等）は全て「タイトル」更新のため不統一なし

### 2-3. 設計案

```python
# テンプレート関数（パターン化できるもの）
def msg_created(subject: str) -> str:  return f'{subject}を登録しました'
def msg_updated(subject: str) -> str:  return f'{subject}を更新しました'
def msg_deleted(subject: str) -> str:  return f'{subject}を削除しました'
def msg_saved(subject: str) -> str:    return f'{subject}を保存しました'

def err_required(subject: str) -> str:        return f'{subject}を入力してください'
def err_max_length(subject: str, n: int) -> str: return f'{subject}は{n}文字以内で入力してください'
def err_select_required(subject: str) -> str: return f'{subject}を選択してください'
def err_invalid(subject: str) -> str:         return f'{subject}が不正です'
def err_not_found(subject: str) -> str:       return f'指定された{subject}が見つかりません'
def err_fetch_failed(subject: str) -> str:    return f'{subject}の取得に失敗しました'
def err_save_failed(subject: str) -> str:     return f'{subject}の保存に失敗しました'

# 固定定数（パターン化不可の固有文言）
ERR_ACCESS_DENIED                  = 'アクセス権限がありません'
ERR_INVALID_PARAMETER              = 'パラメータが不正です'
ERR_GADGET_NOT_AVAILABLE           = '追加予定のガジェットです'
ERR_MEASUREMENT_NOT_FOUND          = '測定項目が見つかりません'
ERR_GADGET_ITEM_COUNT              = '表示項目を1つ以上5つ以下で選択してください'
ERR_MIN_MAX_COMBINED               = '最小値は最大値より小さい値を入力してください。最大値は最小値より大きい値を入力してください。'

# AIチャット画面 固有
ERR_CHAT_QUESTION_EMPTY            = '質問を入力してください'
ERR_CHAT_QUESTION_TOO_LONG        = '質問は1000文字以内で入力してください'
ERR_CHAT_NO_THREAD_ID              = 'thread_idが指定されていません'
ERR_CHAT_TIMEOUT                   = '回答の取得がタイムアウトしました。しばらく経ってから再度お試しください。'
ERR_CHAT_CONNECTION                = '接続エラーが発生しました。しばらく経ってから再度お試しください。'
ERR_CHAT_GENERATION                = '回答の生成に失敗しました。しばらく経ってから再度お試しください。'

# HTTPエラーハンドラー用（error_handlers.py から移管）
HTTP_4XX_CONTENT = {
    400: ('不正なリクエストです', 'リクエストの内容が正しくありません。', 'Bad Request'),
    403: ('アクセスできません', 'このアプリケーションへのアクセス権限がありません。\nシステム管理者にお問い合わせください。', 'Forbidden'),
    404: ('ページが見つかりません', 'お探しのページは存在しないか、削除された可能性があります。', 'Not Found'),
    409: ('競合が発生しました', '他の操作と競合が発生しました。再度お試しください。', 'Conflict'),
}
HTTP_4XX_DEFAULT = ('エラー', 'エラーが発生しました。', 'Error')
```

### 2-4. JS側の方針（**案A採用確定**）

- **案A採用**: `static/js/messages.js` を作成し定数管理（JSも一元化）
- `base.html` に `<script src="{{ url_for('static', filename='js/messages.js') }}">` を追加する
- 対象: common.js（6件）、bar_chart.js・timeline.js（各1件）の計8件

### 2-5. 対応ファイル一覧

| ファイル | 変更内容 |
|---|---|
| `src/iot_app/common/messages.py` | 新規作成 |
| `src/iot_app/common/error_handlers.py` | `_4XX_CONTENT` を messages.py から import |
| `src/iot_app/views/analysis/customer_dashboard/common.py` | 13箇所 |
| `src/iot_app/views/analysis/customer_dashboard/bar_chart.py` | 5箇所 |
| `src/iot_app/views/analysis/customer_dashboard/belt_chart.py` | 3箇所 |
| `src/iot_app/views/analysis/customer_dashboard/circle_chart.py` | 4箇所 |
| `src/iot_app/views/analysis/customer_dashboard/timeline.py` | 4箇所 |
| `src/iot_app/views/analysis/chat/views.py` | 6箇所 |
| `src/iot_app/forms/customer_dashboard/*.py` | 各フォームの validator message |
| `src/iot_app/services/customer_dashboard/bar_chart.py` | ValidationError文言 |
| `src/iot_app/static/js/messages.js` | 新規作成（JS側定数ファイル） |
| `src/iot_app/static/js/components/customer_dashboard/common.js` | 6箇所 → MESSAGES定数参照に変更 |
| `src/iot_app/static/js/components/customer_dashboard/bar_chart.js` | 1箇所 → MESSAGES定数参照に変更 |
| `src/iot_app/static/js/components/customer_dashboard/timeline.js` | 1箇所 → MESSAGES定数参照に変更 |
| `src/iot_app/templates/base.html` | messages.js の `<script>` タグ追加 |

### 2-6. メッセージ統一対応

#### 日付形式チェックメッセージ
- 日付形式チェックのメッセージが不統一
- 日付形式が不正です/正しい日付形式で入力してください（YYYY/MM/DD HH:mm:ss）
- プレースホルダーがあるため形式の指定は冗長であることから「正しい日付形式で入力してください」で統一

---

## 3. 未実装機能 メッセージ一覧（設計書より抽出）

> 対象: 未実装機能の workflow-specification.md / ui-specification.md より抽出  
> JS限定列: UI設計書にのみ記載があり、フロントエンド（JS）で処理すべきメッセージは「yes」

---

### account

| 文言 | 種別 | 表示タイミング | JS限定 |
|---|---|---|---|
| 言語設定を保存しました | 成功 | 言語設定更新成功時 | no |
| 更新に失敗しました | エラー | DB更新エラー時 | no |
| 認証が必要です | エラー | 認証ヘッダがない場合 | no |
| ユーザー情報が見つかりません | エラー | ユーザー未検出時 | no |
| 画面表示に失敗しました | エラー | DBクエリ失敗時 | no |
| 入力内容を確認してください | エラー | バリデーションエラー時 | no |

---

### alert-history

| 文言 | 種別 | 表示タイミング | JS限定 |
|---|---|---|---|
| データの取得に失敗しました | エラー | DBクエリ失敗時 | no |

---

### alert-settings

| 文言 | 種別 | 表示タイミング | JS限定 |
|---|---|---|---|
| アラート設定を登録しました | 成功 | 登録成功時 | no |
| アラート設定を更新しました | 成功 | 更新成功時 | no |
| アラート設定を削除しました | 成功 | 削除成功時 | no |
| アラート設定の登録に失敗しました | エラー | DB操作失敗時 | no |
| データの取得に失敗しました | エラー | DBクエリ失敗時（初期表示・検索時） | no |
| アラート名を入力してください | バリデーション | アラート名未入力時 | no |
| アラート名は100文字以内で入力してください | バリデーション | アラート名100文字超過時 | no |
| 対象デバイスを選択してください | バリデーション | デバイス未選択時 | no |
| アラート発生条件の測定項目名を選択してください | バリデーション | 発生条件の測定項目未選択時 | no |
| アラート発生条件の比較演算子を選択してください | バリデーション | 発生条件の比較演算子未選択時 | no |
| アラート発生条件の閾値を入力してください | バリデーション | 発生条件の閾値未入力時 | no |
| アラート復旧条件の測定項目名を選択してください | バリデーション | 復旧条件の測定項目未選択時 | no |
| アラート復旧条件の比較演算子を選択してください | バリデーション | 復旧条件の比較演算子未選択時 | no |
| アラート復旧条件の閾値を入力してください | バリデーション | 復旧条件の閾値未入力時 | no |
| 判定時間を選択してください | バリデーション | 判定時間未選択時 | no |
| アラートレベルを選択してください | バリデーション | アラートレベル未選択時 | no |

---

### csv-import-export

| 文言 | 種別 | 表示タイミング | JS限定 |
|---|---|---|---|
| CSVファイルのインポートが完了しました。 | 成功 | インポート完了時 | no |
| CSVファイルをインポートします。よろしいですか？ | 確認 | インポート確認モーダル表示時 | no |
| CSVファイルを選択してください | バリデーション | インポートボタン押下時 | no |
| ファイルサイズは10MB以下にしてください | バリデーション | ファイル選択時 | no |
| CSVファイルの形式が正しくありません | バリデーション | ファイル選択時 | no |
| CSVファイルにデータがありません | バリデーション | ファイル選択時 | no |
| 対象マスタを選択してください | バリデーション | インポートボタン押下時 | no |
| CSVファイルの読み込みに失敗しました | エラー | 読込処理失敗時 | no |
| CSVインポートに失敗しました | エラー | インポート処理失敗時 | no |
| CSVファイルのインポートが失敗しました。 | エラー | エラーモーダル表示時 | no |
| ファイルを解析しています。しばらくお待ちください。 | 情報 | 処理中モーダル表示時 | yes |
| ※ブラウザを閉じないでください | 警告 | 処理中モーダル表示時 | yes |

---

### device-inventory

| 文言 | 種別 | 表示タイミング | JS限定 |
|---|---|---|---|
| デバイスの登録が完了しました。 | 成功 | 登録完了時 | no |
| デバイスの更新が完了しました。 | 成功 | 更新完了時 | no |
| デバイスの削除が完了しました。 | 成功 | 削除完了時 | no |
| デバイスを削除します。削除してもよろしいですか？ | 確認 | 削除確認モーダル表示時 | no |
| この操作は取り消すことができません。 | 警告 | 削除確認モーダル表示時 | no |
| クラウドに登録するデバイスIDを入力してください | バリデーション | 登録モーダル送信時 | no |
| クラウド登録するデバイスIDは128文字以内で入力してください | バリデーション | フォーム送信時 | no |
| デバイス名を入力してください | バリデーション | 登録モーダル送信時 | no |
| デバイス名は100文字以内で入力してください | バリデーション | フォーム送信時 | no |
| デバイス種別を選択してください | バリデーション | 登録モーダル送信時 | no |
| モデル情報を入力してください | バリデーション | 登録モーダル送信時 | no |
| モデル情報は100文字以下で入力してください | バリデーション | フォーム送信時 | no |
| SIMIDは20文字以下で入力してください | バリデーション | フォーム送信時 | no |
| MACアドレスを入力してください | バリデーション | 登録モーダル送信時 | no |
| MACアドレスはXX:XX:XX:XX:XX:XX形式で入力してください | バリデーション | フォーム送信時 | no |
| 組織を選択してください | バリデーション | 登録モーダル送信時 | no |
| ソフトウェアバージョンは100文字以下で入力してください | バリデーション | フォーム送信時 | no |
| 設置場所は100文字以下で入力してください | バリデーション | フォーム送信時 | no |
| 在庫場所を入力してください | バリデーション | 登録モーダル送信時 | no |
| 在庫場所は100文字以下で入力してください | バリデーション | フォーム送信時 | no |
| 在庫状況を選択してください | バリデーション | 登録モーダル送信時 | no |
| 購入日を入力してください | バリデーション | 登録モーダル送信時 | no |
| 出荷予定日は購入日以降を指定してください | バリデーション | フォーム送信時 | no |
| 出荷日は購入日以降を指定してください | バリデーション | フォーム送信時 | no |
| メーカー保証終了日を入力してください | バリデーション | 登録モーダル送信時 | no |
| メーカー保証終了日は購入日以降を指定してください | バリデーション | フォーム送信時 | no |
| 開始日は終了日以前を指定してください | バリデーション | 検索フォーム送信時 | no |
| ⚠ 期限間近 | 警告 | 証明書期限が30日以内の場合 | yes |
| ⚠ 期限切れ | 警告 | 証明書期限切れの場合 | yes |

---

### devices

| 文言 | 種別 | 表示タイミング | JS限定 |
|---|---|---|---|
| デバイスを登録しました | 成功 | 登録成功時 | no |
| デバイスを更新しました | 成功 | 更新成功時 | no |
| デバイスを削除しました | 成功 | 削除成功時 | no |
| 選択したデバイス（{n}件）を削除しますか？ | 確認 | 削除確認モーダル表示時 | no |
| この操作は取り消すことができません。 | 警告 | 削除確認モーダル表示時 | no |
| デバイスIDを入力してください | バリデーション | 登録/更新モーダル送信時 | no |
| デバイスIDは128文字以内で入力してください | バリデーション | フォーム送信時 | no |
| デバイスIDは英数字とハイフンのみ使用できます | バリデーション | フォーム送信時 | no |
| このデバイスIDは既に登録されています | バリデーション | 登録時重複チェック | no |
| デバイス名を入力してください | バリデーション | フォーム送信時 | no |
| デバイス名は100文字以内で入力してください | バリデーション | フォーム送信時 | no |
| デバイス種別を選択してください | バリデーション | フォーム送信時 | no |
| モデル情報は100文字以内で入力してください | バリデーション | フォーム送信時 | no |
| SIMIDは20文字以内で入力してください | バリデーション | フォーム送信時 | no |
| MACアドレスの形式が正しくありません（例: AA:BB:CC:DD:EE:FF） | バリデーション | フォーム送信時 | no |
| 指定されたMACアドレスは既に登録されています | バリデーション | 登録/更新時重複チェック | no |
| 設置場所は100文字以内で入力してください | バリデーション | フォーム送信時 | no |
| 所属組織を選択してください | バリデーション | フォーム送信時 | no |

---

### mail-history

| 文言 | 種別 | 表示タイミング | JS限定 |
|---|---|---|---|
| データの取得に失敗しました | エラー | DBクエリ失敗時 | no |
| この操作を実行する権限がありません | エラー | 権限不足時 | no |

---

### organizations

| 文言 | 種別 | 表示タイミング | JS限定 |
|---|---|---|---|
| 組織情報を登録しました | 成功 | 組織登録成功時 | no |
| 組織情報を更新しました | 成功 | 組織更新成功時 | no |
| 組織を削除しました | 成功 | 削除成功時 | no |
| 組織の登録に失敗しました | エラー | API呼び出し失敗時、DB操作失敗時 | no |
| 組織の更新に失敗しました | エラー | API呼び出し失敗時、DB操作失敗時 | no |
| 組織の削除に失敗しました | エラー | Databricks API失敗時、DB操作失敗時 | no |
| 指定された所属組織が見つかりません | エラー | リソース不在時 | no |
| 指定された組織が見つかりません | エラー | リソース不在時 | no |
| 傘下の組織が存在するため削除できません | エラー | 傘下組織存在チェック時 | no |
| 傘下のユーザーが存在するため削除できません | エラー | 傘下ユーザー存在チェック時 | no |
| 傘下のデバイスが存在するため削除できません | エラー | 傘下デバイス存在チェック時 | no |
| 削除する組織を選択してください | エラー | 削除対象未選択時 | no |
| この操作を実行する権限がありません | エラー | 権限不足時 | no |
| データの取得に失敗しました | エラー | DBクエリ失敗時 | no |
| 組織名を入力してください | バリデーション | フォーム送信時 | no |
| 組織名は200文字以内で入力してください | バリデーション | フォーム送信時 | no |
| 組織種別を選択してください | バリデーション | フォーム送信時 | no |
| 所属組織を選択してください | バリデーション | フォーム送信時 | no |
| 住所を入力してください | バリデーション | フォーム送信時 | no |
| 住所は500文字以内で入力してください | バリデーション | フォーム送信時 | no |
| 電話番号を入力してください | バリデーション | フォーム送信時 | no |
| 正しい電話番号形式で入力してください（例: 03-xxxx-xxxx） | バリデーション | フォーム送信時 | no |
| 電話番号は20文字以内で入力してください | バリデーション | フォーム送信時 | no |
| 正しいFAX番号形式で入力してください（例: 03-xxxx-xxxx） | バリデーション | フォーム送信時 | no |
| FAX番号は20文字以内で入力してください | バリデーション | フォーム送信時 | no |
| 担当者名を入力してください | バリデーション | フォーム送信時 | no |
| 担当者名は20文字以内で入力してください | バリデーション | フォーム送信時 | no |
| 契約状態を選択してください | バリデーション | フォーム送信時 | no |
| 契約開始日を入力してください | バリデーション | フォーム送信時 | no |
| 正しい日付形式で入力してください | バリデーション | フォーム送信時 | no |
| 契約終了日は契約開始日以降の日付を入力してください | バリデーション | フォーム送信時 | no |

---

### users

| 文言 | 種別 | 表示タイミング | JS限定 |
|---|---|---|---|
| ユーザーを登録しました | 成功 | 登録成功時（Azure/AWS環境） | no |
| ユーザーを登録し、招待メールを送信しました | 成功 | 登録成功時（オンプレミス環境） | no |
| ユーザーを登録しましたが、招待メール送信に失敗しました | 警告 | 招待メール送信失敗時 | no |
| ユーザー情報を更新しました | 成功 | 更新成功時 | no |
| ユーザーを削除しました | 成功 | 削除成功時 | no |
| ユーザーの登録に失敗しました | エラー | DB操作失敗時 | no |
| ユーザーの更新に失敗しました | エラー | UC/DB操作失敗時 | no |
| ユーザーの削除に失敗しました | エラー | UC/DB/Databricks操作失敗時 | no |
| 指定されたユーザーが見つかりません | エラー | リソース不在時 | no |
| 自分自身のユーザーは削除できません | エラー | 自己削除チェック時 | no |
| 削除するユーザーを選択してください | エラー | 削除対象未選択時 | no |
| この操作を実行する権限がありません | エラー | 権限不足時 | no |
| データの取得に失敗しました | エラー | DBクエリ失敗時 | no |
| ユーザー名を入力してください | バリデーション | フォーム送信時 | no |
| ユーザー名は20文字以内で入力してください | バリデーション | フォーム送信時 | no |
| メールアドレスを入力してください | バリデーション | フォーム送信時 | no |
| 有効なメールアドレスを入力してください | バリデーション | フォーム送信時 | no |
| メールアドレスは254文字以内で入力してください | バリデーション | フォーム送信時 | no |
| このメールアドレスは既に使用されています | バリデーション | メールアドレス重複チェック時（登録時のみ） | no |
| ユーザー種別を選択してください | バリデーション | フォーム送信時 | no |
| 所属を選択してください | バリデーション | フォーム送信時 | no |
| 地域を選択してください | バリデーション | フォーム送信時 | no |
| 住所は500文字以内で入力してください | バリデーション | フォーム送信時 | no |
| ステータスを選択してください | バリデーション | フォーム送信時 | no |
---

## 4. messages.py / messages.js 追加検討（Section 3 分析）

> Section 3（未実装機能設計書より抽出）をもとに、既存パターンとの差分を整理する。

---

### 4-1. 新規パターン関数候補（messages.py）

既存の `suc_created / suc_updated / suc_deleted / err_not_found` に倣い、以下を追加する。

| 関数名 | テンプレート文言 | 対象機能 |
|---|---|---|
| `err_create_failed(entity)` | `{entity}の登録に失敗しました` | users, organizations, devices, device-inventory, alert-settings, mail-settings |
| `err_update_failed(entity)` | `{entity}の更新に失敗しました` | users, organizations, devices, device-inventory, alert-settings, mail-settings |
| `err_delete_failed(entity)` | `{entity}の削除に失敗しました` | users, organizations, devices, device-inventory, alert-settings, mail-settings |
| `err_select_to_delete(entity)` | `削除する{entity}を選択してください` | users, organizations, devices, device-inventory |
| `err_has_children(entity)` | `{entity}に紐づくデータが存在します` | organizations（配下組織/デバイスあり時）|
| `err_date_order(start_label, end_label)` | `{end_label}は{start_label}以降の日付を入力してください` | organizations（契約終了日）, alert-settings（有効期間）|
| `err_already_registered(field)` | `この{field}は既に使用されています` | users（メールアドレス）, organizations（組織コード）|

---

### 4-2. 新規個別定数候補（messages.py）

パターン化に馴染まない固有メッセージ。

| 定数名 | 文言 | 対象機能 |
|---|---|---|
| `ERR_NO_PERMISSION` | `この操作を実行する権限がありません` | users, organizations（権限不足時）|
| `ERR_SELF_DELETE` | `自分自身のユーザーは削除できません` | users |
| `SUC_INVITE_SENT` | `ユーザーを登録し、招待メールを送信しました` | users（オンプレ環境）|
| `WARN_INVITE_FAILED` | `ユーザーを登録しましたが、招待メール送信に失敗しました` | users（招待メール失敗時）|
| `ERR_FILE_REQUIRED` | `ファイルを選択してください` | csv-import-export |
| `ERR_FILE_FORMAT` | `ファイル形式が正しくありません（.csvファイルを選択してください）` | csv-import-export |
| `ERR_IMPORT_FAILED` | `CSVの取り込みに失敗しました` | csv-import-export |
| `SUC_IMPORT` | `{n}件のデータを取り込みました`（n は件数変数） | csv-import-export |

---

### 4-3. 新規個別定数候補（messages.js）

JS 専用（フロントエンドのみで使用するもの）。

| 定数名 | 文言 | 対象機能 | 備考 |
|---|---|---|---|
| `MSG_PROCESSING` | `処理中...` | csv-import-export（処理中モーダル）| インポート実行中スピナー表示 |
| `BADGE_CERT_EXPIRED` | `証明書有効期限切れ` | device-inventory | JS でバッジ生成 |
| `BADGE_CERT_EXPIRING_SOON` | `証明書有効期限間近` | device-inventory | JS でバッジ生成 |

---

### 4-4. 既存実装との不整合（統一要）

実装と設計書の間、または機能間で文言が揺れている箇所。

#### Section 3 追加分析より（Section 1〜3 横断）

| # | 項目 | 揺れの内容 | 推奨方針 |
|---|---|---|---|
| 1 | 成功メッセージの文体 | `{対象}を{操作}しました`（users/devices/alert-settings/organizations）vs `{対象}の{操作}が完了しました。`（device-inventory・句点あり）| 既存実装パターン `{対象}を{操作}しました` に統一。device-inventory 実装時に合わせる |
| 2 | organizations 成功メッセージ内部 | `組織情報を登録しました` / `組織情報を更新しました` vs `組織を削除しました`（同一機能内で主語が不統一）| `組織を{操作}しました` に統一（削除に合わせる）|
| 3 | account エラーの主語なし | `更新に失敗しました`（主語なし）vs `ユーザーの更新に失敗しました` 等（他機能は主語あり）| `言語設定の更新に失敗しました` など主語を補う |
| 4 | CSV インポートエラー 3 種 | `CSVファイルの読み込みに失敗しました` / `CSVインポートに失敗しました` / `CSVファイルのインポートが失敗しました。` が混在 | タイミングが異なる場合は残してよいが文言を整理。句点の有無も統一要 |
| 5 | `指定された{対象}が見つかりません` vs `{対象}が見つかりません` | users/organizations は「指定された」付き、account は「ユーザー情報が見つかりません」（なし）| `err_not_found` パターンで統一。account も「指定された」形式に揃えるか別定数にするか決定要 |
| 6 | 組織選択バリデーション | `所属組織を選択してください`（devices/organizations）vs `組織を選択してください`（device-inventory）| 同じ組織選択なら `所属組織` に統一。device-inventory のコンテキスト上「所属組織」が不自然であれば別定数で可 |

#### Section 4-4 初期記載分

| 項目 | 既存実装 | 設計書（未実装側） | 推奨 |
|---|---|---|---|
| MAC アドレス形式エラー | `MACアドレスはXX:XX:XX:XX:XX:XX形式で入力してください`（devices 設計書）| `正しいMACアドレス形式で入力してください（例: xx:xx:xx:xx:xx:xx）`（device-inventory 設計書）| 実装時に統一。例示形式（小文字 `xx:`）の方が自然 |
| 権限エラー文言 | `アクセス権限がありません`（customer_dashboard 既存実装 / views/analysis/）| `この操作を実行する権限がありません`（users/organizations 設計書）| `ERR_NO_PERMISSION` として一本化する際にどちらに統一するか決定要 |

---

## 5. 設計書修正対応表

> 対応済み列: ✅ = 修正完了 / ❌ = 未対応（判断待ち）/ — = 対象外

| # | カテゴリ | 対象ファイル | 修正内容 | 対応済み |
|---|---|---|---|---|
| B-1 | 権限エラー文言 + 表示方式 | organizations/workflow-specification.md（L453, L581） | `この操作を実行する権限がありません` → `アクセス権限がありません`、`403エラーページ表示` → `toast表示` | ✅ |
| B-2 | 権限エラー文言 + 表示方式 | device-inventory/workflow-specification.md（L337） | `この操作を実行する権限がありません` → `アクセス権限がありません`、`403エラーモーダル表示` → `toast表示` | ✅ |
| B-3 | 権限エラー文言 + 表示方式 | mail-history/書面レビュー対象/workflow-specification.md（L295, L890） | `この操作を実行する権限がありません` → `アクセス権限がありません`、`403エラーページ表示` → `toast表示` | ✅ |
| B-4 | 主語なしエラー文言 | account/書面レビュー対象資料/workflow-specification.md（L429, L443, L815, L831） | `更新に失敗しました` → `言語設定の更新に失敗しました` | ✅ |
| B-5 | account `ユーザー情報が見つかりません` | account/書面レビュー対象資料/workflow-specification.md | ログイン中ユーザー自身を指すコンテキストのため **現行維持**（「指定された」は不自然） | — |
| B-6 | エラー処理方針 | common/common-specification.md（L82-85, L99-101, L109-146, L157-164, L601-603） | 400 → フォーム項目下表示（フォームなければtoast）、403/404 → toast表示 に更新 | ✅ |
| C-1 | messages.py 新規作成 | src/iot_app/common/messages.py | テンプレート関数14件 + 固定定数 | ✅ |
| D-1 | error_handlers.py 更新 | src/iot_app/common/error_handlers.py | HTTP_4XX_CONTENT を messages.py から import | ✅ |
| D-2 | customer_dashboard 実装 更新 | common.py / bar_chart.py / belt_chart.py / circle_chart.py / timeline.py | messages.py 参照に変更（計29箇所）、timeline `表示デバイス選択を選択してください` 修正含む | ✅ |
| D-3 | chat 実装 更新 | views/analysis/chat/views.py | messages.py 参照に変更（6箇所） | ✅ |
| D-4 | forms 更新 | forms/customer_dashboard/*.py | バリデーションメッセージを messages.py 参照に変更 | ✅ |
| D-5 | services 更新 | services/customer_dashboard/bar_chart.py | ValidationError 文言を messages.py 参照に変更 | ✅ |
| E-1 | messages.js 新規作成 | src/iot_app/static/js/messages.js | JS定数8件 | ✅ |
| E-2 | JS 実装 更新 | common.js / bar_chart.js / timeline.js | MESSAGES定数参照に変更（8箇所） | ✅ |
| E-3 | base.html 更新 | src/iot_app/templates/base.html | messages.js の script タグ追加 | ✅ |
| ❌-1 | CSV インポートエラー 3種統一 | csv-import-export/workflow-specification.md | 役割確認・文言整理（未判断）| ❌ |
| ❌-2 | MAC アドレス形式統一 | devices/workflow-specification.md, device-inventory/workflow-specification.md | どちらの形式にするか未決定 | ❌ |
