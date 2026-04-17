"""
アプリケーション共通メッセージ定義

パターン化できるメッセージはテンプレート関数、固有文言は定数で管理する。
"""


# ============================================================
# テンプレート関数（パターン化できるもの）
# ============================================================

# SUC_001
def msg_created(subject: str) -> str:
    return f'{subject}を登録しました'

# SUC_002
def msg_updated(subject: str) -> str:
    return f'{subject}を更新しました'

# SUC_003
def msg_deleted(subject: str) -> str:
    return f'{subject}を削除しました'

# SUC_004
def msg_saved(subject: str) -> str:
    return f'{subject}を保存しました'

# ERR_001
def err_required(subject: str) -> str:
    return f'{subject}を入力してください'

# ERR_002
def err_max_length(subject: str, n: int) -> str:
    return f'{subject}は{n}文字以内で入力してください'

# ERR_003
def err_select_required(subject: str) -> str:
    return f'{subject}を選択してください'

# ERR_004
def err_numeric(subject: str) -> str:
    return f'{subject}は数値で入力してください'

# ERR_005
def err_invalid(subject: str) -> str:
    return f'{subject}が不正です'

# ERR_006
def err_not_found(subject: str) -> str:
    return f'指定された{subject}が見つかりません'

# ERR_007
def err_fetch_failed(subject: str) -> str:
    return f'{subject}の取得に失敗しました'

# ERR_008
def err_save_failed(subject: str) -> str:
    return f'{subject}の保存に失敗しました'

# ERR_009
def err_min_less_than_max(subject: str) -> str:
    return f'{subject}の最小値は最大値より小さい値を入力してください'

# ERR_010
def err_max_greater_than_min(subject: str) -> str:
    return f'{subject}の最大値は最小値より大きい値を入力してください'


# ============================================================
# 固定定数（パターン化不可の固有文言）
# ============================================================

ERR_ACCESS_DENIED       = 'アクセス権限がありません'
ERR_GADGET_NOT_AVAILABLE = '追加予定のガジェットです'
ERR_MEASUREMENT_NOT_FOUND = '測定項目が見つかりません'
ERR_GADGET_ITEM_COUNT   = '表示項目を1つ以上5つ以下で選択してください'
ERR_MIN_VALUE_LESS_THAN_MAX    = '最小値は最大値より小さい値を入力してください'
ERR_MAX_VALUE_GREATER_THAN_MIN = '最大値は最小値より大きい値を入力してください'
# 日時バリデーション（timeline サービス）
ERR_DATETIME_FORMAT   = '正しい日付形式で入力してください'
ERR_END_BEFORE_START  = '終了日時は開始日時以降の日時を入力してください'
ERR_DATETIME_RANGE_24H = '取得期間は24時間以内で指定してください'

# チャット固有
ERR_CHAT_QUESTION_EMPTY   = '質問を入力してください'
ERR_CHAT_QUESTION_TOO_LONG = '質問は1000文字以内で入力してください'
ERR_CHAT_NO_THREAD_ID       = 'thread_idが指定されていません'
ERR_CHAT_INVALID_THREAD_ID  = '無効なthread_idが指定されました'
ERR_CHAT_TIMEOUT    = '回答の取得がタイムアウトしました。しばらく経ってから再度お試しください。'
ERR_CHAT_CONNECTION = '接続エラーが発生しました。しばらく経ってから再度お試しください。'
ERR_CHAT_GENERATION = '回答の生成に失敗しました。しばらく経ってから再度お試しください。'

# HTTPエラーハンドラー用（error_handlers.py からインポートして使用）
HTTP_4XX_CONTENT = {
    400: ('不正なリクエストです',
          'リクエストの内容が正しくありません。',
          'Bad Request'),
    403: ('アクセスできません',
          'このアプリケーションへのアクセス権限がありません。\nシステム管理者にお問い合わせください。',
          'Forbidden'),
    404: ('ページが見つかりません',
          'お探しのページは存在しないか、削除された可能性があります。',
          'Not Found'),
    409: ('競合が発生しました',
          '他の操作と競合が発生しました。再度お試しください。',
          'Conflict'),
}
HTTP_4XX_DEFAULT = ('エラー', 'エラーが発生しました。', 'Error')
