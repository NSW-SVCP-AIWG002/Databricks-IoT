# devices 実装タスクリスト

## タスク一覧

| #  | タスク名                        | 対象ファイル                                                                                                                    | 対応テスト                                         | 実装フロー状態 | 備考                            |
|----|---------------------------------|---------------------------------------------------------------------------------------------------------------------------------|----------------------------------------------------|----------------|---------------------------------|
| 1  | データ定義層①モデル             | src/iot_app/models/device.py                                                                                                    | tests/unit/models/test_device.py                   | 完了           | DeviceMasterByUser を追加       |
| 2  | データ定義層②設定               | src/iot_app/config.py                                                                                                           | -                                                  | 完了           | DEVICE_DATA_INTERVAL_SECONDS=60 |
| 3  | ビジネスロジック層              | src/iot_app/services/device_service.py                                                                                          | tests/unit/services/test_device_service.py         | 完了           | 全サービス関数                  |
| 4  | インターフェース層①フォーム     | src/iot_app/forms/device.py                                                                                                     | tests/integration/test_device_routes.py            | 完了           | Search/Create/UpdateForm        |
| 5  | インターフェース層②ビュー       | src/iot_app/views/admin/devices.py<br>src/iot_app/views/admin/__init__.py<br>src/iot_app/__init__.py                            | tests/integration/test_device_routes.py            | 完了           | admin_bp 登録含む               |
| 6  | インターフェース層③テンプレート | src/iot_app/templates/admin/devices/list.html<br>src/iot_app/templates/admin/devices/form.html<br>src/iot_app/templates/admin/devices/detail.html | -                             | 完了           |                                 |
| 7  | インターフェース層④静的ファイル | src/iot_app/static/js/components/device.js<br>src/iot_app/static/css/components/device.css                                     | -                                                  | 完了           | main.css への追加も実施         |

## 実装フロー状態

| 状態     | 意味                 |
|----------|----------------------|
| 未着手   | 実装未開始           |
| 実装中   | ① 実装 実施中        |
| テスト中 | ② pytest 実行中      |
| 修正中   | ③ テスト失敗・修正中 |
| 完了     | ④ 全テスト通過       |

## セルフレビュー進捗

| 観点                         | 状態   | 確認結果 |
|------------------------------|--------|----------|
| 機能: 設計書との差分         | 完了   | form.html/detail.htmlはviews.pyの渡す変数と整合。detail.htmlのdevice_type名・org名はIDで代替（view側制限） |
| 機能: テスト仕様カバレッジ   | 完了   | タスク6/7はテスト対象外（テンプレート・静的ファイル） |
| 機能: インターフェース整合性 | 完了   | url_for ルート名・テンプレート変数がviews.pyと一致 |
| 非機能: セキュリティ         | 完了   | CSRF対応(csrf_token)、XSS対応(Jinja2自動エスケープ)、権限チェック(@require_role)確認済み |
| 非機能: ログ準拠             | 完了   | テンプレート内でのログ出力なし。サーバーサイドで管理 |
| 非機能: エラーハンドリング   | 完了   | views.pyでabort(404/500)処理済み、フォームエラーはtemplate内で表示 |
