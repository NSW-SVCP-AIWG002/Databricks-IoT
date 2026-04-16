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