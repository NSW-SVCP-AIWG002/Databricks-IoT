/**
 * アプリケーション共通メッセージ定数（JS側）
 *
 * Python側の messages.py と対応するJS専用定数ファイル。
 * base.html で全ページ読み込み済みのため、どのJSからも MESSAGES.XXX で参照可能。
 */
const MESSAGES = {
  // ダッシュボード操作
  ERR_SELECT_DASHBOARD_TO_DELETE: '削除するダッシュボードを選択してください',
  ERR_SELECT_DASHBOARD_TO_SWITCH: '切り替えるダッシュボードを選択してください',
  ERR_DASHBOARD_SWITCH_FAILED:    'ダッシュボードの切り替えに失敗しました',

  // 通信エラー
  ERR_NETWORK: '通信エラーが発生しました',

  // 日時バリデーション
  ERR_START_DATETIME_REQUIRED: '開始日時を入力してください',
  ERR_END_DATETIME_REQUIRED:   '終了日時を入力してください',
  ERR_START_BEFORE_END:        '開始日時は終了日時より前に設定してください',

  // CSVエクスポート
  ERR_CSV_DOWNLOAD_FAILED: 'CSVのダウンロードに失敗しました',

  // CSVインポート
  MSG_PROCESSING: 'ファイルを解析しています。しばらくお待ちください。',

  // デバイス台帳バッジ
  BADGE_CERT_EXPIRED:       '⚠ 期限切れ',
  BADGE_CERT_EXPIRING_SOON: '⚠ 期限間近',
};
