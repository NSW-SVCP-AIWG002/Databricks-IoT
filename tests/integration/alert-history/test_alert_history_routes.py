"""
アラート履歴 - 結合テスト

出力先: tests/integration/alert-history/test_alert_history_routes.py

対象エンドポイント:
  GET  /alert/alert-history                       初期表示・ページング
  POST /alert/alert-history                       検索実行
  GET  /alert/alert-history/<alert_history_uuid>  詳細表示（参照モーダル）

参照ドキュメント:
  - UI設計書:              docs/03-features/flask-app/alert-history/ui-specification.md
  - 機能設計書:            docs/03-features/flask-app/alert-history/workflow-specification.md
  - 結合テスト観点表:      docs/05-testing/integration-test/integration-test-perspectives.md
  - 結合テスト実装ガイド:  docs/05-testing/integration-test/integration-test-guide.md

適用観点:
  1.1  認証テスト
  1.3  データスコープフィルタテスト
  2.1  正常遷移テスト（初期表示・検索・参照）
  2.2  エラー時遷移テスト（404・500）
  4.1  一覧表示テスト
  4.2  詳細表示テスト
  5.1  検索条件テスト（部分一致・AND結合）
  5.2  ソート機能テスト
  5.3  ページネーションテスト
  8.1  正常系ログテスト
  8.2  異常系ログテスト
  9.1  SQLインジェクションテスト
  9.2  XSSテスト
  9.3  CSRF対策テスト

スコープ外:
  3.x  バリデーション（検索フォームは全任意入力のためバリデーションなし）
  4.3〜4.6  登録・更新・削除・CSV（read-only機能のため対象外）
  6.x  外部API連携（Databricks連携なし）
  7.x  トランザクション（read-only機能のため対象外）
  2.3  リダイレクトテスト（POST後は直接HTML返却のため対象外）
"""

import uuid
from datetime import timedelta

import pytest


# ---------------------------------------------------------------------------
# ヘルパー
# ---------------------------------------------------------------------------

def _add_extra_histories(alert_history_test_data, n):
    """alert_setting_acc に紐づく追加 AlertHistory を n 件 flush で挿入する。

    タイムスタンプは 4 日前から 1 時間ずつずらして投入する（既存 history_acc/sub より古い）。
    alert_history_test_data のロールバックで自動的にクリーンアップされる。

    Returns:
        list[AlertHistory]: 挿入順に並んだ履歴オブジェクトのリスト（[0] が最新、[-1] が最古）
    """
    import uuid as _uuid
    from iot_app import db
    from iot_app.models.alert import AlertHistory

    now = alert_history_test_data['now']
    alert_id = alert_history_test_data['alert_setting_acc'].alert_id
    alert_status_id = alert_history_test_data['alert_status_id']
    added = []
    for i in range(n):
        h = AlertHistory(
            alert_history_uuid=str(_uuid.uuid4()),
            alert_id=alert_id,
            alert_occurrence_datetime=now - timedelta(days=4, hours=i),
            alert_status_id=alert_status_id,
            alert_value=float(i),
            creator=1,
            modifier=1,
        )
        db.session.add(h)
        added.append(h)
    db.session.flush()
    return added  # added[0] が最新（4日前0h）、added[-1] が最古（4日前 n-1 h）


def _post_search(client, **kwargs):
    """アラート履歴検索 POST のヘルパー。

    指定しないキーはデフォルト値（空文字）で埋める。
    """
    data = {
        'start_datetime':  kwargs.get('start_datetime', ''),
        'end_datetime':    kwargs.get('end_datetime', ''),
        'device_name':     kwargs.get('device_name', ''),
        'device_location': kwargs.get('device_location', ''),
        'alert_name':      kwargs.get('alert_name', ''),
        'alert_level_id':  kwargs.get('alert_level_id', ''),
        'alert_status_id': kwargs.get('alert_status_id', ''),
        'sort_item_id':    kwargs.get('sort_item_id', '1'),
        'sort_order_id':   kwargs.get('sort_order_id', '2'),
    }
    return client.post('/alert/alert-history', data=data)


# ---------------------------------------------------------------------------
# 1. 認証・認可テスト
# ---------------------------------------------------------------------------

@pytest.mark.integration
class TestAlertHistoryAuth:
    """認証・認可テスト
    観点: 1.1 認証テスト
    """

    def test_authenticated_user_can_access_list(self, client):
        """1.1.1: 認証済みユーザーがアラート履歴一覧にアクセスできる（200）

        inject_test_user autouse fixture により g.current_user が設定済み。
        """
        # Act
        response = client.get('/alert/alert-history')

        # Assert
        assert response.status_code == 200

    def test_unauthenticated_request_returns_401(self, app, client):
        """1.1.2: 未認証リクエスト（認証ヘッダーなし）で 401 が返る

        authenticate_request ミドルウェアを before_request に再登録し、
        auth_provider が UnauthorizedError を送出するようモックすることで
        認証エラー時の 401 レスポンスを確認する。
        """
        # Arrange
        from unittest.mock import MagicMock
        import iot_app.auth.middleware as _mw
        from iot_app.auth.exceptions import UnauthorizedError
        from iot_app.auth.middleware import authenticate_request

        # inject_test_user が index=0 に挿入した _set_current_user を退避して除外
        funcs = app.before_request_funcs.setdefault(None, [])
        saved_func = funcs[0] if funcs else None
        if saved_func:
            funcs.remove(saved_func)

        # authenticate_request を先頭に挿入
        funcs.insert(0, authenticate_request)

        # auth_provider を「常に UnauthorizedError を送出」するモックに差し替え
        original_provider = _mw.auth_provider
        mock_provider = MagicMock()
        mock_provider.get_user_info.side_effect = UnauthorizedError("no auth header")
        _mw.auth_provider = mock_provider

        try:
            # Act
            response = client.get('/alert/alert-history')

            # Assert
            assert response.status_code == 401
        finally:
            _mw.auth_provider = original_provider
            if authenticate_request in funcs:
                funcs.remove(authenticate_request)
            if saved_func and saved_func not in funcs:
                funcs.insert(0, saved_func)

    def test_invalid_token_returns_401(self, app, client):
        """1.1.3: 不正な認証トークンで 401 が返る

        auth_provider が不正トークンに対して UnauthorizedError を送出する状況を再現し、
        401 レスポンスが返ることを確認する。
        """
        # Arrange
        from unittest.mock import MagicMock
        import iot_app.auth.middleware as _mw
        from iot_app.auth.exceptions import UnauthorizedError
        from iot_app.auth.middleware import authenticate_request

        funcs = app.before_request_funcs.setdefault(None, [])
        saved_func = funcs[0] if funcs else None
        if saved_func:
            funcs.remove(saved_func)

        funcs.insert(0, authenticate_request)

        original_provider = _mw.auth_provider
        mock_provider = MagicMock()
        mock_provider.get_user_info.side_effect = UnauthorizedError("invalid token")
        _mw.auth_provider = mock_provider

        try:
            # Act
            response = client.get(
                '/alert/alert-history',
                headers={'X-MS-TOKEN-AAD-ACCESS-TOKEN': 'invalid.token.value'},
            )

            # Assert
            assert response.status_code == 401
        finally:
            _mw.auth_provider = original_provider
            if authenticate_request in funcs:
                funcs.remove(authenticate_request)
            if saved_func and saved_func not in funcs:
                funcs.insert(0, saved_func)

    def test_expired_session_returns_401(self, app, client):
        """1.1.4: セッション期限切れ（期限切れトークン）で 401 が返る

        auth_provider が期限切れトークンに対して UnauthorizedError を送出する状況を再現し、
        401 レスポンスが返ることを確認する。
        """
        # Arrange
        from unittest.mock import MagicMock
        import iot_app.auth.middleware as _mw
        from iot_app.auth.exceptions import UnauthorizedError
        from iot_app.auth.middleware import authenticate_request

        funcs = app.before_request_funcs.setdefault(None, [])
        saved_func = funcs[0] if funcs else None
        if saved_func:
            funcs.remove(saved_func)

        funcs.insert(0, authenticate_request)

        original_provider = _mw.auth_provider
        mock_provider = MagicMock()
        mock_provider.get_user_info.side_effect = UnauthorizedError("token expired")
        _mw.auth_provider = mock_provider

        try:
            # Act
            response = client.get('/alert/alert-history')

            # Assert
            assert response.status_code == 401
        finally:
            _mw.auth_provider = original_provider
            if authenticate_request in funcs:
                funcs.remove(authenticate_request)
            if saved_func and saved_func not in funcs:
                funcs.insert(0, saved_func)

    def test_authenticated_user_can_execute_search(self, client):
        """1.1.1: 認証済みユーザーがアラート履歴検索を実行できる（200）"""
        # Act
        response = _post_search(client)

        # Assert
        assert response.status_code == 200

    def test_authenticated_user_can_access_detail(self, client, alert_history_test_data):
        """1.1.1: 認証済みユーザーがスコープ内のアラート履歴詳細にアクセスできる（200）"""
        # Arrange
        uuid_str = alert_history_test_data['history_uuid']

        # Act
        response = client.get(f'/alert/alert-history/{uuid_str}')

        # Assert
        assert response.status_code == 200


# ---------------------------------------------------------------------------
# 2. 一覧表示テスト（初期表示・正常遷移）
# ---------------------------------------------------------------------------

@pytest.mark.integration
class TestAlertHistoryListDisplay:
    """一覧表示テスト
    観点: 4.1 一覧表示（Read）テスト、2.1.1 正常遷移テスト（初期表示）
    """

    def test_initial_display_returns_200(self, client):
        """2.1.1: 初期表示で 200 が返る（データなしでも正常）"""
        # Act
        response = client.get('/alert/alert-history')

        # Assert
        assert response.status_code == 200
        assert b'html' in response.data.lower()

    def test_accessible_histories_are_displayed(self, client, alert_history_test_data):
        """4.1.2 / 4.1.3: アクセス可能なアラート履歴（自組織・下位組織）が一覧に表示される"""
        # Arrange
        alert_name_acc = alert_history_test_data['alert_name_acc']
        alert_name_sub = alert_history_test_data['alert_name_sub']

        # Act
        response = client.get('/alert/alert-history')

        # Assert
        assert response.status_code == 200
        text = response.data.decode('utf-8')
        assert alert_name_acc in text
        assert alert_name_sub in text

    def test_single_history_displayed(self, client, alert_history_test_data):
        """4.1.2: アクセス可能なアラート履歴が1件のみのとき正常に表示される"""
        # Arrange: device_name_acc で絞り込み → history_acc の1件のみヒット
        device_name_acc = alert_history_test_data['device_name_acc']
        alert_name_acc = alert_history_test_data['alert_name_acc']

        # Act
        response = _post_search(client, device_name=device_name_acc)

        # Assert
        assert response.status_code == 200
        text = response.data.decode('utf-8')
        assert alert_name_acc in text
        assert '1件' in text

    def test_deleted_history_is_not_displayed(self, client, alert_history_test_data):
        """4.1.4: 論理削除済み（delete_flag=True）のアラート履歴は一覧に表示されない"""
        # Arrange
        deleted_uuid = alert_history_test_data['history_deleted'].alert_history_uuid

        # Act
        response = client.get('/alert/alert-history')

        # Assert
        assert response.status_code == 200
        text = response.data.decode('utf-8')
        assert deleted_uuid not in text

    def test_zero_results_shows_zero_count(self, client):
        """4.1.1: 検索結果0件のとき "0件" が表示される（データなし状態の正常レンダリング確認）

        存在しえない未来の期間を検索条件に指定することで結果を0件にし、
        テンプレートが "0件" を正しくレンダリングすることを確認する。
        """
        # Arrange: 遠い未来の期間を指定して結果を0件に強制する
        response = _post_search(
            client,
            start_datetime='2099/01/01 00:00',
            end_datetime='2099/01/02 00:00',
        )

        # Assert
        assert response.status_code == 200
        text = response.data.decode('utf-8')
        assert '0件' in text, "検索結果0件のとき '0件' が表示されるべき"

    def test_initial_display_applies_default_datetime_filter(
        self, client, alert_history_test_data
    ):
        """初期表示デフォルト日時フィルタ: 8日以上前のデータは初期表示に含まれない

        ワークフロー仕様書より、初期表示の開始日時デフォルトは「現在日時から7日前の00:00」。
        7日以上前（8日前）のアラート履歴は一覧に表示されないことを確認する。
        """
        # Arrange: 8日前のアラート履歴を追加（7日フィルタの範囲外）
        import uuid as _uuid
        from iot_app import db
        from iot_app.models.alert import AlertHistory

        now = alert_history_test_data['now']
        alert_id = alert_history_test_data['alert_setting_acc'].alert_id
        alert_status_id = alert_history_test_data['alert_status_id']
        old_uuid = str(_uuid.uuid4())

        old_history = AlertHistory(
            alert_history_uuid=old_uuid,
            alert_id=alert_id,
            alert_occurrence_datetime=now - timedelta(days=8),
            alert_status_id=alert_status_id,
            alert_value=99.0,
            creator=1,
            modifier=1,
        )
        db.session.add(old_history)
        db.session.flush()

        # Act: 初期表示（page パラメータなし）
        response = client.get('/alert/alert-history')

        # Assert: 7日より古いレコードは表示されない
        assert response.status_code == 200
        text = response.data.decode('utf-8')
        assert old_uuid not in text, "8日前のアラート履歴は初期表示に含まれるべきでない"
        # 7日以内のデータ（1日前）は引き続き表示される
        alert_name_acc = alert_history_test_data['alert_name_acc']
        assert alert_name_acc in text, "7日以内のアラート履歴は初期表示に含まれるべき"

    def test_initial_display_clears_previous_cookie(self, client, alert_history_test_data):
        """ClearCookie: 初期表示時に前回の検索Cookie条件がクリアされデフォルト条件で表示される

        POST検索で絞り込み条件（結果0件になるデバイス名）をCookieに保存した後、
        初期表示（page未指定）を行うと Cookie がクリアされデフォルト条件（全件）に戻り、
        テストデータが表示されることを確認する。
        """
        # Arrange: 存在しないデバイス名で検索し、0件条件のCookieを設定する
        alert_name_acc = alert_history_test_data['alert_name_acc']
        _post_search(client, device_name='XXXXXXXXXX存在しないデバイス')

        # Act: 初期表示（page パラメータなし → ClearCookie → デフォルト条件）
        response = client.get('/alert/alert-history')

        # Assert: CookieがクリアされデフォルトのWHERE条件（絞り込みなし）が適用される
        assert response.status_code == 200
        text = response.data.decode('utf-8')
        assert alert_name_acc in text, \
            "初期表示でCookieがクリアされデフォルト条件が適用されるべき"


# ---------------------------------------------------------------------------
# 3. エラー時遷移テスト
# ---------------------------------------------------------------------------

@pytest.mark.integration
class TestAlertHistoryErrorTransition:
    """エラー時遷移テスト
    観点: 2.2 エラー時遷移テスト
    """

    def test_nonexistent_uuid_returns_404(self, client):
        """2.2.4: 存在しない UUID で詳細アクセスすると 404 が返る"""
        # Arrange
        nonexistent_uuid = str(uuid.uuid4())

        # Act
        response = client.get(f'/alert/alert-history/{nonexistent_uuid}')

        # Assert
        assert response.status_code == 404

    def test_invalid_uuid_format_returns_404(self, client):
        """2.2.4: 不正な UUID 形式で詳細アクセスすると 404 が返る"""
        # Arrange
        invalid_uuid = 'invalid-uuid-format'

        # Act
        response = client.get(f'/alert/alert-history/{invalid_uuid}')

        # Assert
        assert response.status_code == 404

    def test_list_db_error_returns_500(self, client):
        """2.2.5: 一覧取得（GET）でサービス層が例外を送出すると 500 が返る"""
        # Arrange
        from unittest.mock import patch

        with patch(
            'iot_app.views.alert.alert_history.search_alert_histories',
            side_effect=RuntimeError("DB接続エラー（テスト）"),
        ):
            # Act
            response = client.get('/alert/alert-history')

        # Assert
        assert response.status_code == 500

    def test_search_db_error_returns_500(self, client):
        """2.2.5: 検索実行（POST）でサービス層が例外を送出すると 500 が返る"""
        # Arrange
        from unittest.mock import patch

        with patch(
            'iot_app.views.alert.alert_history.search_alert_histories',
            side_effect=RuntimeError("DB接続エラー（テスト）"),
        ):
            # Act
            response = _post_search(client)

        # Assert
        assert response.status_code == 500


# ---------------------------------------------------------------------------
# 4. 詳細表示テスト
# ---------------------------------------------------------------------------

@pytest.mark.integration
class TestAlertHistoryDetail:
    """詳細表示テスト
    観点: 4.2 詳細表示（Read）テスト
    """

    def test_accessible_detail_returns_200(self, client, alert_history_test_data):
        """4.2.1: スコープ内の有効な UUID で詳細が 200 で返る"""
        # Arrange
        uuid_str = alert_history_test_data['history_uuid']

        # Act
        response = client.get(f'/alert/alert-history/{uuid_str}')

        # Assert
        assert response.status_code == 200

    def test_detail_contains_expected_data(self, client, alert_history_test_data):
        """4.2.5: 詳細モーダルにアラート名・デバイス名が含まれる（関連データ結合確認）"""
        # Arrange
        uuid_str = alert_history_test_data['history_uuid']
        alert_name_acc = alert_history_test_data['alert_name_acc']
        device_name_acc = alert_history_test_data['device_name_acc']

        # Act
        response = client.get(f'/alert/alert-history/{uuid_str}')

        # Assert
        assert response.status_code == 200
        text = response.data.decode('utf-8')
        assert alert_name_acc in text
        assert device_name_acc in text

    def test_deleted_history_detail_returns_404(self, client, alert_history_test_data):
        """4.2.3: 論理削除済みアラート履歴の詳細アクセスは 404 が返る"""
        # Arrange
        deleted_uuid = alert_history_test_data['history_deleted'].alert_history_uuid

        # Act
        response = client.get(f'/alert/alert-history/{deleted_uuid}')

        # Assert
        assert response.status_code == 404

    def test_inaccessible_history_detail_returns_404(self, client, alert_history_test_data):
        """4.2.4: データスコープ外のアラート履歴詳細は 404 が返る"""
        # Arrange
        inacc_uuid = alert_history_test_data['history_inacc'].alert_history_uuid

        # Act
        response = client.get(f'/alert/alert-history/{inacc_uuid}')

        # Assert
        assert response.status_code == 404

    def test_nonexistent_history_returns_404(self, client):
        """4.2.2: 存在しない UUID の詳細は 404 が返る"""
        # Arrange
        nonexistent_uuid = str(uuid.uuid4())

        # Act
        response = client.get(f'/alert/alert-history/{nonexistent_uuid}')

        # Assert
        assert response.status_code == 404


# ---------------------------------------------------------------------------
# 5. 検索条件テスト
# ---------------------------------------------------------------------------

@pytest.mark.integration
class TestAlertHistorySearch:
    """検索条件テスト
    観点: 5.1 検索条件テスト、2.1.2 正常遷移テスト（検索後表示）
    """

    def test_search_no_conditions_returns_200(self, client, alert_history_test_data):
        """5.1.1: 全条件未入力で検索すると 200 が返る"""
        # Act
        response = _post_search(client)

        # Assert
        assert response.status_code == 200

    def test_search_no_conditions_shows_accessible_data(self, client, alert_history_test_data):
        """5.1.1: 条件なし検索でアクセス可能なデータが表示される"""
        # Arrange
        alert_name_acc = alert_history_test_data['alert_name_acc']
        alert_name_sub = alert_history_test_data['alert_name_sub']

        # Act
        response = _post_search(client)

        # Assert
        assert response.status_code == 200
        text = response.data.decode('utf-8')
        assert alert_name_acc in text
        assert alert_name_sub in text

    def test_search_by_device_name_partial_forward(self, client, alert_history_test_data):
        """5.1.7: デバイス名の前方一致検索でヒットする"""
        # Arrange: デバイス名の先頭5文字を検索語にする
        device_name_acc = alert_history_test_data['device_name_acc']
        partial = device_name_acc[:5]

        # Act
        response = _post_search(client, device_name=partial)

        # Assert
        assert response.status_code == 200
        text = response.data.decode('utf-8')
        assert device_name_acc in text

    def test_search_by_device_name_partial_middle(self, client, alert_history_test_data):
        """5.1.9: デバイス名の中間一致検索でヒットする"""
        # Arrange: デバイス名の中間部分を検索語にする
        device_name_acc = alert_history_test_data['device_name_acc']
        # "テストデバイスAH_アクセス可" → "デバイスAH" を検索
        partial = 'デバイスAH'

        # Act
        response = _post_search(client, device_name=partial)

        # Assert
        assert response.status_code == 200
        text = response.data.decode('utf-8')
        assert device_name_acc in text

    def test_search_by_device_name_no_match(self, client, alert_history_test_data):
        """5.1.6〜5.1.9: 一致しないデバイス名で検索するとヒットしない"""
        # Arrange
        device_name_acc = alert_history_test_data['device_name_acc']
        device_name_sub = alert_history_test_data['device_name_sub']

        # Act
        response = _post_search(client, device_name='XXXXXXXXXX存在しないデバイス')

        # Assert
        assert response.status_code == 200
        text = response.data.decode('utf-8')
        assert device_name_acc not in text
        assert device_name_sub not in text

    def test_search_by_alert_name_partial_match(self, client, alert_history_test_data):
        """5.1.9: アラート名の部分一致検索でヒットする"""
        # Arrange
        alert_name_acc = alert_history_test_data['alert_name_acc']
        # "テストアラートAH_アクセス可" → "テストアラートAH" を検索
        partial = 'テストアラートAH'

        # Act
        response = _post_search(client, alert_name=partial)

        # Assert
        assert response.status_code == 200
        text = response.data.decode('utf-8')
        assert alert_name_acc in text

    def test_search_by_alert_name_exact_full_match(self, client, alert_history_test_data):
        """5.1.6: 部分一致フィールド（アラート名）にフル名称を入力した場合もヒットする"""
        # Arrange: アラート名を完全入力で検索
        alert_name_acc = alert_history_test_data['alert_name_acc']

        # Act
        response = _post_search(client, alert_name=alert_name_acc)

        # Assert: LIKE '%完全一致%' でもヒットすること
        assert response.status_code == 200
        text = response.data.decode('utf-8')
        assert alert_name_acc in text

    def test_search_by_alert_name_partial_forward(self, client, alert_history_test_data):
        """5.1.7: アラート名の前方一致検索でヒットする"""
        # Arrange: アラート名の先頭部分（"テストアラート"）を検索語にする
        alert_name_acc = alert_history_test_data['alert_name_acc']
        partial = alert_name_acc[:6]  # "テストアラート"

        # Act
        response = _post_search(client, alert_name=partial)

        # Assert
        assert response.status_code == 200
        text = response.data.decode('utf-8')
        assert alert_name_acc in text

    def test_search_by_alert_name_partial_backward(self, client, alert_history_test_data):
        """5.1.8: アラート名の後方一致検索でヒットする"""
        # Arrange: アラート名の末尾部分（"AH_アクセス可"）を検索語にする
        alert_name_acc = alert_history_test_data['alert_name_acc']
        suffix = 'AH_アクセス可'

        # Act
        response = _post_search(client, alert_name=suffix)

        # Assert
        assert response.status_code == 200
        text = response.data.decode('utf-8')
        assert alert_name_acc in text

    def test_search_by_alert_level_id(self, client, alert_history_test_data):
        """5.1.2: アラートレベル ID の完全一致検索でヒットする"""
        # Arrange
        alert_level_id = alert_history_test_data['alert_level_id']
        alert_name_acc = alert_history_test_data['alert_name_acc']

        # Act
        response = _post_search(client, alert_level_id=str(alert_level_id))

        # Assert
        assert response.status_code == 200
        text = response.data.decode('utf-8')
        assert alert_name_acc in text

    def test_search_by_alert_status_id(self, client, alert_history_test_data):
        """5.1.2: アラートステータス ID の完全一致検索でヒットする"""
        # Arrange
        alert_status_id = alert_history_test_data['alert_status_id']
        alert_name_acc = alert_history_test_data['alert_name_acc']

        # Act
        response = _post_search(client, alert_status_id=str(alert_status_id))

        # Assert
        assert response.status_code == 200
        text = response.data.decode('utf-8')
        assert alert_name_acc in text

    def test_search_and_conditions_both_match(self, client, alert_history_test_data):
        """5.1.10: デバイス名・アラート名 AND 条件で両方一致するとヒットする"""
        # Arrange
        device_name_acc = alert_history_test_data['device_name_acc']
        alert_name_acc = alert_history_test_data['alert_name_acc']

        # Act
        response = _post_search(client, device_name=device_name_acc, alert_name=alert_name_acc)

        # Assert
        assert response.status_code == 200
        text = response.data.decode('utf-8')
        assert device_name_acc in text

    def test_search_and_conditions_one_mismatch(self, client, alert_history_test_data):
        """5.1.11: デバイス名・アラート名 AND 条件で片方が一致しないとヒットしない"""
        # Arrange
        device_name_acc = alert_history_test_data['device_name_acc']
        nonexistent_alert = 'XXXXXXXXXX存在しないアラート'

        # Act
        response = _post_search(
            client,
            device_name=device_name_acc,
            alert_name=nonexistent_alert,
        )

        # Assert
        assert response.status_code == 200
        text = response.data.decode('utf-8')
        assert device_name_acc not in text

    def test_search_with_datetime_range_hits(self, client, alert_history_test_data):
        """5.1.1: 開始・終了日時を指定して BETWEEN フィルタが適用され、範囲内のデータがヒットする"""
        # Arrange: テストデータの発生日時を含む期間を指定
        now = alert_history_test_data['now']
        start = (now - timedelta(days=5)).strftime('%Y/%m/%d %H:%M')
        end = now.strftime('%Y/%m/%d %H:%M')
        alert_name_acc = alert_history_test_data['alert_name_acc']

        # Act
        response = _post_search(client, start_datetime=start, end_datetime=end)

        # Assert
        assert response.status_code == 200
        text = response.data.decode('utf-8')
        assert alert_name_acc in text

    def test_search_with_datetime_range_excludes_old_data(self, client, alert_history_test_data):
        """5.1.1: 開始・終了日時の範囲外のデータは表示されない（BETWEEN 除外）"""
        # Arrange: テストデータの発生日時より未来の期間を指定（過去データが範囲外）
        now = alert_history_test_data['now']
        start = (now + timedelta(days=1)).strftime('%Y/%m/%d %H:%M')
        end = (now + timedelta(days=2)).strftime('%Y/%m/%d %H:%M')
        alert_name_acc = alert_history_test_data['alert_name_acc']
        alert_name_sub = alert_history_test_data['alert_name_sub']

        # Act
        response = _post_search(client, start_datetime=start, end_datetime=end)

        # Assert
        assert response.status_code == 200
        text = response.data.decode('utf-8')
        assert alert_name_acc not in text
        assert alert_name_sub not in text

    def test_search_by_device_location_partial_forward(self, client, alert_history_test_data):
        """5.1.7: 設置場所の前方一致検索でヒットする"""
        # Arrange: 設置場所の先頭部分（"テスト設置場所"）を検索語にする
        alert_name_acc = alert_history_test_data['alert_name_acc']
        partial = alert_history_test_data['device_location_acc'][:7]  # "テスト設置場所"

        # Act
        response = _post_search(client, device_location=partial)

        # Assert
        assert response.status_code == 200
        text = response.data.decode('utf-8')
        assert alert_name_acc in text

    def test_search_by_device_location_partial_middle(self, client, alert_history_test_data):
        """5.1.9: 設置場所の中間一致検索でヒットする"""
        # Arrange: 設置場所の中間部分（"設置場所AH"）を検索語にする
        alert_name_acc = alert_history_test_data['alert_name_acc']
        partial = '設置場所AH'

        # Act
        response = _post_search(client, device_location=partial)

        # Assert
        assert response.status_code == 200
        text = response.data.decode('utf-8')
        assert alert_name_acc in text

    def test_search_by_device_location_exact_full_match(self, client, alert_history_test_data):
        """5.1.6: 部分一致フィールド（設置場所）にフル名称を入力した場合もヒットする"""
        # Arrange: 設置場所を完全入力で検索
        alert_name_acc = alert_history_test_data['alert_name_acc']
        device_location_acc = alert_history_test_data['device_location_acc']

        # Act
        response = _post_search(client, device_location=device_location_acc)

        # Assert: LIKE '%完全一致%' でもヒットすること
        assert response.status_code == 200
        text = response.data.decode('utf-8')
        assert alert_name_acc in text

    def test_search_by_device_location_partial_backward(self, client, alert_history_test_data):
        """5.1.8: 設置場所の後方一致検索でヒットする"""
        # Arrange: 設置場所の末尾部分（"場所AH"）を検索語にする
        alert_name_acc = alert_history_test_data['alert_name_acc']
        suffix = '場所AH'

        # Act
        response = _post_search(client, device_location=suffix)

        # Assert
        assert response.status_code == 200
        text = response.data.decode('utf-8')
        assert alert_name_acc in text

    def test_search_by_device_location_no_match(self, client, alert_history_test_data):
        """5.1.6〜5.1.9: 一致しない設置場所で検索するとヒットしない"""
        # Arrange
        alert_name_acc = alert_history_test_data['alert_name_acc']
        alert_name_sub = alert_history_test_data['alert_name_sub']

        # Act
        response = _post_search(client, device_location='XXXXXXXXXX存在しない設置場所')

        # Assert
        assert response.status_code == 200
        text = response.data.decode('utf-8')
        assert alert_name_acc not in text
        assert alert_name_sub not in text

    def test_search_by_alert_status_id_no_match(self, client, alert_history_test_data):
        """5.1.2: 存在しないアラートステータス ID で検索するとヒットしない"""
        # Arrange: DB に存在しない ID を指定
        alert_name_acc = alert_history_test_data['alert_name_acc']
        alert_name_sub = alert_history_test_data['alert_name_sub']

        # Act
        response = _post_search(client, alert_status_id='99999')

        # Assert
        assert response.status_code == 200
        text = response.data.decode('utf-8')
        assert alert_name_acc not in text
        assert alert_name_sub not in text

    def test_search_by_device_name_exact_full_match(self, client, alert_history_test_data):
        """5.1.6: 部分一致フィールド（デバイス名）にフル名称を入力した場合もヒットする"""
        # Arrange: デバイス名を完全一致（フル入力）で検索
        device_name_acc = alert_history_test_data['device_name_acc']
        alert_name_acc = alert_history_test_data['alert_name_acc']

        # Act
        response = _post_search(client, device_name=device_name_acc)

        # Assert: LIKE '%完全一致%' でもヒットすること
        assert response.status_code == 200
        text = response.data.decode('utf-8')
        assert alert_name_acc in text

    def test_search_by_device_name_partial_backward(self, client, alert_history_test_data):
        """5.1.8: デバイス名の後方一致検索でヒットする"""
        # Arrange: デバイス名の末尾部分（"アクセス可"）を検索語にする
        # "テストデバイスAH_アクセス可" の末尾
        alert_name_acc = alert_history_test_data['alert_name_acc']
        suffix = 'AH_アクセス可'

        # Act
        response = _post_search(client, device_name=suffix)

        # Assert
        assert response.status_code == 200
        text = response.data.decode('utf-8')
        assert alert_name_acc in text

    def test_search_all_conditions_match(self, client, alert_history_test_data):
        """5.1.10: 全検索条件（期間・デバイス名・設置場所・アラート名・レベルID・ステータスID）を
        設定し、すべてが history_acc に一致する場合にヒットする"""
        # Arrange: history_acc の各属性に合わせた条件を設定
        now = alert_history_test_data['now']
        alert_name_acc = alert_history_test_data['alert_name_acc']

        # Act
        response = _post_search(
            client,
            start_datetime=(now - timedelta(days=5)).strftime('%Y/%m/%d %H:%M'),
            end_datetime=now.strftime('%Y/%m/%d %H:%M'),
            device_name=alert_history_test_data['device_name_acc'],
            device_location=alert_history_test_data['device_location_acc'],
            alert_name=alert_history_test_data['alert_name_acc'],
            alert_level_id=str(alert_history_test_data['alert_level_id']),
            alert_status_id=str(alert_history_test_data['alert_status_id']),
        )

        # Assert
        assert response.status_code == 200
        text = response.data.decode('utf-8')
        assert alert_name_acc in text

    def test_search_all_conditions_one_mismatch(self, client, alert_history_test_data):
        """5.1.11: 全検索条件設定で設置場所のみ不一致にするとヒットしない（AND 結合の確認）"""
        # Arrange: device_location だけ存在しない値にする
        now = alert_history_test_data['now']
        alert_name_acc = alert_history_test_data['alert_name_acc']

        # Act
        response = _post_search(
            client,
            start_datetime=(now - timedelta(days=5)).strftime('%Y/%m/%d %H:%M'),
            end_datetime=now.strftime('%Y/%m/%d %H:%M'),
            device_name=alert_history_test_data['device_name_acc'],
            device_location='XXXXXXXXXX存在しない設置場所',
            alert_name=alert_history_test_data['alert_name_acc'],
            alert_level_id=str(alert_history_test_data['alert_level_id']),
            alert_status_id=str(alert_history_test_data['alert_status_id']),
        )

        # Assert
        assert response.status_code == 200
        text = response.data.decode('utf-8')
        assert alert_name_acc not in text


# ---------------------------------------------------------------------------
# 6. ソート機能テスト
# ---------------------------------------------------------------------------

@pytest.mark.integration
class TestAlertHistorySort:
    """ソート機能テスト
    観点: 5.2 ソート機能テスト
    """

    def test_sort_descending_returns_200(self, client, alert_history_test_data):
        """5.2.3: 降順ソート（sort_order_id=2）で検索して 200 が返る"""
        # Act
        response = _post_search(client, sort_item_id='1', sort_order_id='2')

        # Assert
        assert response.status_code == 200

    def test_sort_ascending_returns_200(self, client, alert_history_test_data):
        """5.2.2: 昇順ソート（sort_order_id=1）で検索して 200 が返る"""
        # Act
        response = _post_search(client, sort_item_id='1', sort_order_id='1')

        # Assert
        assert response.status_code == 200

    def test_sort_not_specified_returns_200(self, client, alert_history_test_data):
        """5.2.1: ソート指定なし（sort_order_id=-1）で検索して 200 が返る"""
        # Act
        response = _post_search(client, sort_item_id='1', sort_order_id='-1')

        # Assert
        assert response.status_code == 200

    def test_descending_order_newest_first(self, client, alert_history_test_data):
        """5.2.3: 降順ソートで新しい履歴（1日前）が古い履歴（2日前）より先に表示される"""
        # Arrange
        alert_name_acc = alert_history_test_data['alert_name_acc']   # 1日前
        alert_name_sub = alert_history_test_data['alert_name_sub']   # 2日前

        # Act: 降順（新しい順）で検索
        response = _post_search(client, sort_item_id='1', sort_order_id='2')

        # Assert
        assert response.status_code == 200
        text = response.data.decode('utf-8')
        pos_acc = text.find(alert_name_acc)
        pos_sub = text.find(alert_name_sub)
        assert pos_acc != -1, f"{alert_name_acc} が応答に含まれていない"
        assert pos_sub != -1, f"{alert_name_sub} が応答に含まれていない"
        # 降順では新しい（1日前=acc）が先に表示される
        assert pos_acc < pos_sub, "降順では新しいアラートが先に表示されるべき"

    def test_ascending_order_oldest_first(self, client, alert_history_test_data):
        """5.2.2: 昇順ソートで古い履歴（2日前）が新しい履歴（1日前）より先に表示される"""
        # Arrange
        alert_name_acc = alert_history_test_data['alert_name_acc']   # 1日前
        alert_name_sub = alert_history_test_data['alert_name_sub']   # 2日前

        # Act: 昇順（古い順）で検索
        response = _post_search(client, sort_item_id='1', sort_order_id='1')

        # Assert
        assert response.status_code == 200
        text = response.data.decode('utf-8')
        pos_acc = text.find(alert_name_acc)
        pos_sub = text.find(alert_name_sub)
        assert pos_acc != -1, f"{alert_name_acc} が応答に含まれていない"
        assert pos_sub != -1, f"{alert_name_sub} が応答に含まれていない"
        # 昇順では古い（2日前=sub）が先に表示される
        assert pos_sub < pos_acc, "昇順では古いアラートが先に表示されるべき"

    # ---- sort_item_id=2〜6: 200チェック（parametrize）----

    @pytest.mark.parametrize("sort_item_id,label", [
        (2, "デバイス名"),
        (3, "設置場所"),
        (4, "アラート名"),
        (5, "アラートレベル"),
        (6, "アラートステータス"),
    ])
    def test_sort_each_item_descending_returns_200(
        self, client, alert_history_test_data, sort_item_id, label
    ):
        """5.2.3: 各ソート項目（sort_item_id=2〜6）で降順ソートして 200 が返る"""
        # Act
        response = _post_search(client, sort_item_id=str(sort_item_id), sort_order_id='2')

        # Assert
        assert response.status_code == 200

    @pytest.mark.parametrize("sort_item_id,label", [
        (2, "デバイス名"),
        (3, "設置場所"),
        (4, "アラート名"),
        (5, "アラートレベル"),
        (6, "アラートステータス"),
    ])
    def test_sort_each_item_ascending_returns_200(
        self, client, alert_history_test_data, sort_item_id, label
    ):
        """5.2.2: 各ソート項目（sort_item_id=2〜6）で昇順ソートして 200 が返る"""
        # Act
        response = _post_search(client, sort_item_id=str(sort_item_id), sort_order_id='1')

        # Assert
        assert response.status_code == 200

    # ---- sort_item_id=2 (デバイス名) 順序検証 ----

    def test_sort_by_device_name_ascending(self, client, alert_history_test_data):
        """5.2.2: デバイス名昇順（sort_item_id=2）で "アクセス可"（ア）が "サブ"（サ）より先に表示される"""
        # Arrange
        alert_name_acc = alert_history_test_data['alert_name_acc']
        alert_name_sub = alert_history_test_data['alert_name_sub']

        # Act
        response = _post_search(client, sort_item_id='2', sort_order_id='1')

        # Assert
        assert response.status_code == 200
        text = response.data.decode('utf-8')
        pos_acc = text.find(alert_name_acc)
        pos_sub = text.find(alert_name_sub)
        assert pos_acc != -1, f"{alert_name_acc} が応答に含まれていない"
        assert pos_sub != -1, f"{alert_name_sub} が応答に含まれていない"
        # ASC: "テストデバイスAH_アクセス可"（ア, U+30A2）< "テストデバイスAH_サブ"（サ, U+30B5）
        assert pos_acc < pos_sub, "デバイス名昇順では アクセス可 が サブ より先"

    def test_sort_by_device_name_descending(self, client, alert_history_test_data):
        """5.2.3: デバイス名降順（sort_item_id=2）で "サブ"（サ）が "アクセス可"（ア）より先に表示される"""
        # Arrange
        alert_name_acc = alert_history_test_data['alert_name_acc']
        alert_name_sub = alert_history_test_data['alert_name_sub']

        # Act
        response = _post_search(client, sort_item_id='2', sort_order_id='2')

        # Assert
        assert response.status_code == 200
        text = response.data.decode('utf-8')
        pos_acc = text.find(alert_name_acc)
        pos_sub = text.find(alert_name_sub)
        assert pos_acc != -1, f"{alert_name_acc} が応答に含まれていない"
        assert pos_sub != -1, f"{alert_name_sub} が応答に含まれていない"
        # DESC: "テストデバイスAH_サブ"（サ）> "テストデバイスAH_アクセス可"（ア）
        assert pos_sub < pos_acc, "デバイス名降順では サブ が アクセス可 より先"

    # ---- sort_item_id=3 (設置場所) 順序検証 ----

    def test_sort_by_device_location_ascending(self, client, alert_history_test_data):
        """5.2.2: 設置場所昇順（sort_item_id=3）で "テスト設置場所AH" が "テスト設置場所AHサブ" より先に表示される"""
        # Arrange
        alert_name_acc = alert_history_test_data['alert_name_acc']
        alert_name_sub = alert_history_test_data['alert_name_sub']

        # Act
        response = _post_search(client, sort_item_id='3', sort_order_id='1')

        # Assert
        assert response.status_code == 200
        text = response.data.decode('utf-8')
        pos_acc = text.find(alert_name_acc)
        pos_sub = text.find(alert_name_sub)
        assert pos_acc != -1, f"{alert_name_acc} が応答に含まれていない"
        assert pos_sub != -1, f"{alert_name_sub} が応答に含まれていない"
        # ASC: "テスト設置場所AH" < "テスト設置場所AHサブ"（前方一致・短い方が先）
        assert pos_acc < pos_sub, "設置場所昇順では AH が AHサブ より先"

    def test_sort_by_device_location_descending(self, client, alert_history_test_data):
        """5.2.3: 設置場所降順（sort_item_id=3）で "テスト設置場所AHサブ" が "テスト設置場所AH" より先に表示される"""
        # Arrange
        alert_name_acc = alert_history_test_data['alert_name_acc']
        alert_name_sub = alert_history_test_data['alert_name_sub']

        # Act
        response = _post_search(client, sort_item_id='3', sort_order_id='2')

        # Assert
        assert response.status_code == 200
        text = response.data.decode('utf-8')
        pos_acc = text.find(alert_name_acc)
        pos_sub = text.find(alert_name_sub)
        assert pos_acc != -1, f"{alert_name_acc} が応答に含まれていない"
        assert pos_sub != -1, f"{alert_name_sub} が応答に含まれていない"
        # DESC: "テスト設置場所AHサブ" > "テスト設置場所AH"
        assert pos_sub < pos_acc, "設置場所降順では AHサブ が AH より先"

    # ---- sort_item_id=4 (アラート名) 順序検証 ----

    def test_sort_by_alert_name_ascending(self, client, alert_history_test_data):
        """5.2.2: アラート名昇順（sort_item_id=4）で "アクセス可"（ア）が "サブ"（サ）より先に表示される"""
        # Arrange
        alert_name_acc = alert_history_test_data['alert_name_acc']
        alert_name_sub = alert_history_test_data['alert_name_sub']

        # Act
        response = _post_search(client, sort_item_id='4', sort_order_id='1')

        # Assert
        assert response.status_code == 200
        text = response.data.decode('utf-8')
        pos_acc = text.find(alert_name_acc)
        pos_sub = text.find(alert_name_sub)
        assert pos_acc != -1, f"{alert_name_acc} が応答に含まれていない"
        assert pos_sub != -1, f"{alert_name_sub} が応答に含まれていない"
        # ASC: "テストアラートAH_アクセス可"（ア, U+30A2）< "テストアラートAH_サブ"（サ, U+30B5）
        assert pos_acc < pos_sub, "アラート名昇順では アクセス可 が サブ より先"

    def test_sort_by_alert_name_descending(self, client, alert_history_test_data):
        """5.2.3: アラート名降順（sort_item_id=4）で "サブ"（サ）が "アクセス可"（ア）より先に表示される"""
        # Arrange
        alert_name_acc = alert_history_test_data['alert_name_acc']
        alert_name_sub = alert_history_test_data['alert_name_sub']

        # Act
        response = _post_search(client, sort_item_id='4', sort_order_id='2')

        # Assert
        assert response.status_code == 200
        text = response.data.decode('utf-8')
        pos_acc = text.find(alert_name_acc)
        pos_sub = text.find(alert_name_sub)
        assert pos_acc != -1, f"{alert_name_acc} が応答に含まれていない"
        assert pos_sub != -1, f"{alert_name_sub} が応答に含まれていない"
        # DESC: "テストアラートAH_サブ"（サ）> "テストアラートAH_アクセス可"（ア）
        assert pos_sub < pos_acc, "アラート名降順では サブ が アクセス可 より先"


# ---------------------------------------------------------------------------
# 7. ページネーションテスト
# ---------------------------------------------------------------------------

@pytest.mark.integration
class TestAlertHistoryPagination:
    """ページネーションテスト
    観点: 5.3 ページネーションテスト
    """

    def test_initial_display_is_page_1(self, client, alert_history_test_data):
        """5.3.1: 初期表示（?page なし）は 1 ページ目のデータが返る（200）"""
        # Act
        response = client.get('/alert/alert-history')

        # Assert
        assert response.status_code == 200

    def test_paging_page_1_returns_200(self, client, alert_history_test_data):
        """5.3.1: ?page=1 のページングリクエストが 200 を返す"""
        # Arrange: 初期表示でCookieを設定してから
        client.get('/alert/alert-history')

        # Act
        response = client.get('/alert/alert-history?page=1')

        # Assert
        assert response.status_code == 200

    def test_paging_page_2_returns_200(self, client, alert_history_test_data):
        """5.3.2: ?page=2 のページングリクエストが 200 を返す（データ不足でも正常）"""
        # Arrange: 初期表示でCookieを設定してから
        client.get('/alert/alert-history')

        # Act
        response = client.get('/alert/alert-history?page=2')

        # Assert
        assert response.status_code == 200

    def test_paging_uses_cookie_search_params(self, client, alert_history_test_data):
        """5.3.2: ページング時はCookieの検索条件を引き継ぐ（検索結果が維持される）"""
        # Arrange: デバイス名フィルタ付きで検索してCookieに条件を保存
        device_name_acc = alert_history_test_data['device_name_acc']
        _post_search(client, device_name=device_name_acc)

        # Act: page=1 でページング（Cookieの条件が適用されるはず）
        response = client.get('/alert/alert-history?page=1')

        # Assert: 検索条件が引き継がれ、デバイス名で絞り込まれたデータが返る
        assert response.status_code == 200
        text = response.data.decode('utf-8')
        # デバイス名フィルタが適用されているため acc はヒット
        assert device_name_acc in text

    def test_page_out_of_range_shows_page_1(self, client, alert_history_test_data):
        """5.3.4: ?page=0 でも 200 が返る（ページ範囲外は 1 ページ目相当）

        NOTE: page <= 0 を明示的にガードしていない実装では offset が負数になり
        500 を返す可能性がある。このテストが失敗した場合は実装側の修正が必要。
        """
        # Arrange: Cookie を設定してからページ範囲外を要求
        _post_search(client)

        # Act
        response = client.get('/alert/alert-history?page=0')

        # Assert
        assert response.status_code == 200

    def test_total_count_displayed_correctly(self, client, alert_history_test_data):
        """5.3.7: スコープ内の非削除履歴の総件数が "{n}件" として HTML に表示される"""
        # Arrange: スコープ内非削除履歴は history_acc / history_sub の 2 件
        #          条件なし検索（日時フィルタなし）で全件取得

        # Act
        response = _post_search(client)

        # Assert
        assert response.status_code == 200
        text = response.data.decode('utf-8')
        assert '2件' in text

    def test_exactly_one_page_when_data_equals_page_size(self, client, alert_history_test_data):
        """5.3.5: データ件数 = ページサイズ（25件）のとき、次ページリンクが生成されない"""
        # Arrange: 既存 2 件 + 追加 23 件 = 合計 25 件
        _add_extra_histories(alert_history_test_data, 23)

        # Act: 条件なし検索（全件対象）
        response = _post_search(client)

        # Assert: 合計 25 件・page=2 リンクなし（1 ページに収まる）
        assert response.status_code == 200
        text = response.data.decode('utf-8')
        assert '25件' in text
        assert 'page=2' not in text

    def test_two_pages_when_data_exceeds_page_size(self, client, alert_history_test_data):
        """5.3.6: データ件数 = ページサイズ + 1（26件）のとき、page=2 リンクが生成される"""
        # Arrange: 既存 2 件 + 追加 24 件 = 合計 26 件
        _add_extra_histories(alert_history_test_data, 24)

        # Act: 条件なし検索（全件対象）
        response = _post_search(client)

        # Assert: 合計 26 件・page=2 リンクあり（2 ページに分割）
        assert response.status_code == 200
        text = response.data.decode('utf-8')
        assert '26件' in text
        assert 'page=2' in text

    def test_last_page_shows_remaining_items(self, client, alert_history_test_data):
        """5.3.3: 26 件のとき最終ページ（page=2）に残り 1 件のみ表示される"""
        # Arrange: 既存 2 件 + 追加 24 件 = 合計 26 件
        #          降順ソートで最古レコード（extras[-1]）が page=2 に来る
        extras = _add_extra_histories(alert_history_test_data, 24)
        oldest_uuid = extras[-1].alert_history_uuid

        # Act: POST 検索で Cookie を設定し、page=2 を取得
        _post_search(client)
        response = client.get('/alert/alert-history?page=2')

        # Assert: page=2 に最古レコードの UUID が含まれる
        assert response.status_code == 200
        text = response.data.decode('utf-8')
        assert oldest_uuid in text

    def test_page_2_does_not_show_page_1_items(self, client, alert_history_test_data):
        """5.3.2: 2 ページ目に 1 ページ目専用レコードが含まれない（ページ境界の確認）"""
        # Arrange: 26 件、降順ソートで history_acc（最新 1 日前）が page=1 の先頭
        #          extras[-1]（最古 4 日前 23h）が page=2 の唯一のレコード
        extras = _add_extra_histories(alert_history_test_data, 24)
        newest_uuid = alert_history_test_data['history_acc'].alert_history_uuid
        oldest_uuid = extras[-1].alert_history_uuid

        # Act
        _post_search(client)
        page1_text = client.get('/alert/alert-history?page=1').data.decode('utf-8')
        page2_text = client.get('/alert/alert-history?page=2').data.decode('utf-8')

        # Assert
        assert newest_uuid in page1_text,     "最新レコードは page=1 に存在すべき"
        assert newest_uuid not in page2_text,  "最新レコードは page=2 に存在しないべき"
        assert oldest_uuid not in page1_text,  "最古レコードは page=1 に存在しないべき"
        assert oldest_uuid in page2_text,      "最古レコードは page=2 に存在すべき"

    def test_get_initial_display_cookie_used_in_paging(self, client, alert_history_test_data):
        """SaveCookie→GetCookie: GET初期表示後のページングでCookieの検索条件が引き継がれる

        POST検索を経由せずに、GET初期表示（page未指定）→ GET page=2 の流れで
        初期表示時に保存されたCookieがページングに利用されることを確認する。
        既存の test_paging_uses_cookie_search_params は POST→GETの流れのみ検証している。
        """
        # Arrange: 26件以上のデータを用意してページ分割を発生させる
        #          降順ソートで extras[-1]（最古）が page=2 に来る
        extras = _add_extra_histories(alert_history_test_data, 24)
        oldest_uuid = extras[-1].alert_history_uuid

        # Act1: GET初期表示（SaveCookie: デフォルト検索条件をCookieに保存）
        init_response = client.get('/alert/alert-history')
        assert init_response.status_code == 200

        # Act2: POSTを経由せず直接 page=2 をリクエスト（GetCookie: 初期表示のCookieを利用）
        page2_response = client.get('/alert/alert-history?page=2')

        # Assert: page=2 が正常に返り、2ページ目のレコードが含まれる
        assert page2_response.status_code == 200
        page2_text = page2_response.data.decode('utf-8')
        assert oldest_uuid in page2_text, \
            "GET初期表示後のページング(page=2)に最古レコードが含まれるべき"

    def test_search_replaces_previous_cookie(self, client, alert_history_test_data):
        """ClearCookie: POST検索を2回実行すると2回目の条件が1回目の条件を上書きする

        1回目のPOST検索（device_acc で絞り込み）後に
        2回目のPOST検索（device_sub で絞り込み）を実行し、
        以降のページングで2回目の条件のみが適用されることを確認する。
        """
        # Arrange
        device_name_acc = alert_history_test_data['device_name_acc']
        device_name_sub = alert_history_test_data['device_name_sub']
        alert_name_acc = alert_history_test_data['alert_name_acc']
        alert_name_sub = alert_history_test_data['alert_name_sub']

        # Act1: 1回目の検索（device_acc のみヒット）
        _post_search(client, device_name=device_name_acc)

        # Act2: 2回目の検索（device_sub のみヒット）→ Cookie が上書きされる
        _post_search(client, device_name=device_name_sub)

        # Act3: ページング（2回目の Cookie が使われるはず）
        response = client.get('/alert/alert-history?page=1')

        # Assert: 2回目の条件（device_sub）が適用され、device_acc はヒットしない
        assert response.status_code == 200
        text = response.data.decode('utf-8')
        assert alert_name_sub in text, \
            "2回目の検索条件（device_sub）が Cookie に保存されているべき"
        assert alert_name_acc not in text, \
            "1回目の検索条件（device_acc）は Cookie から上書きされているべき"

    def test_search_resets_page_to_1(self, client, alert_history_test_data):
        """page: 1 リセット: POST検索後のレスポンスは常にpage=1（最新レコード）から始まる

        26件のデータがある状態でpage=2を参照後にPOST検索を実行すると、
        検索レスポンスがpage=1の内容（最新レコード）を含み、
        page=2のレコードを含まないことを確認する。
        """
        # Arrange: 26件（既存2件 + 追加24件）でページ分割を発生させる
        extras = _add_extra_histories(alert_history_test_data, 24)
        newest_uuid = alert_history_test_data['history_acc'].alert_history_uuid
        oldest_uuid = extras[-1].alert_history_uuid

        # 一度 POST 検索してから page=2 へ移動しておく
        _post_search(client)
        client.get('/alert/alert-history?page=2')

        # Act: 再度 POST 検索（page が 1 にリセットされるはず）
        response = _post_search(client)

        # Assert: POST レスポンスが page=1 の内容（最新レコード）を含む
        assert response.status_code == 200
        text = response.data.decode('utf-8')
        assert newest_uuid in text, \
            "POST検索後のレスポンスはpage=1（最新レコード）を含むべき"
        assert oldest_uuid not in text, \
            "POST検索後のレスポンスにpage=2のレコードは含まれないべき"


# ---------------------------------------------------------------------------
# 8. データスコープフィルタテスト
# ---------------------------------------------------------------------------

@pytest.mark.integration
class TestAlertHistoryDataScope:
    """データスコープフィルタテスト
    観点: 1.3 データスコープフィルタテスト
    """

    def test_own_org_data_is_displayed(self, client, alert_history_test_data):
        """1.3.1: 自組織配下デバイスのアラート履歴が一覧に表示される"""
        # Arrange
        alert_name_acc = alert_history_test_data['alert_name_acc']

        # Act
        response = client.get('/alert/alert-history')

        # Assert
        assert response.status_code == 200
        text = response.data.decode('utf-8')
        assert alert_name_acc in text

    def test_sub_org_data_is_displayed(self, client, alert_history_test_data):
        """1.3.2: 下位組織配下デバイスのアラート履歴が一覧に表示される"""
        # Arrange
        alert_name_sub = alert_history_test_data['alert_name_sub']

        # Act
        response = client.get('/alert/alert-history')

        # Assert
        assert response.status_code == 200
        text = response.data.decode('utf-8')
        assert alert_name_sub in text

    def test_inaccessible_org_data_is_not_displayed(self, client, alert_history_test_data):
        """1.3.4: アクセス不可組織（organization_closure 未登録）のアラート履歴は表示されない"""
        # Arrange
        alert_name_inacc = alert_history_test_data['alert_name_inacc']

        # Act
        response = client.get('/alert/alert-history')

        # Assert
        assert response.status_code == 200
        text = response.data.decode('utf-8')
        assert alert_name_inacc not in text

    def test_inaccessible_org_history_detail_is_blocked(self, client, alert_history_test_data):
        """1.3.4: データスコープ外のアラート履歴詳細へのアクセスは 404 が返る"""
        # Arrange
        inacc_uuid = alert_history_test_data['history_inacc'].alert_history_uuid

        # Act
        response = client.get(f'/alert/alert-history/{inacc_uuid}')

        # Assert
        assert response.status_code == 404

    def test_search_also_applies_data_scope(self, client, alert_history_test_data):
        """1.3.4: POST 検索でもデータスコープが適用され、スコープ外データがヒットしない"""
        # Arrange
        alert_name_inacc = alert_history_test_data['alert_name_inacc']

        # Act: 条件なしで全件取得を試みる
        response = _post_search(client)

        # Assert
        assert response.status_code == 200
        text = response.data.decode('utf-8')
        assert alert_name_inacc not in text

    def test_parent_org_data_is_not_displayed(self, client, alert_history_test_data):
        """1.3.3: 上位組織配下デバイスのアラート履歴は一覧に表示されない

        conftest で user_id=1 の organization_id を org_accessible に override している。
        org_accessible の上位に相当する組織（organization_closure に親→子として登録されていない）
        のデータはスコープ外となる。
        ここでは org_inaccessible をユーザーの「上位組織」として位置づけ、
        そのデータが表示されないことで 1.3.3 の観点を検証する。

        NOTE: v_alert_history_by_user は organization_closure の
              subsidiary_organization_id でフィルタするため、
              closure 未登録の組織は上位・無関係を問わずすべてスコープ外となる。
        """
        # Arrange: org_inaccessible（上位組織相当）のアラート履歴が存在する
        alert_name_inacc = alert_history_test_data['alert_name_inacc']

        # Act: 条件なし検索（全件対象）
        response = _post_search(client)

        # Assert: 上位組織相当のデータは表示されない
        assert response.status_code == 200
        text_body = response.data.decode('utf-8')
        assert alert_name_inacc not in text_body, (
            "上位組織（closure 未登録）のアラート履歴は表示されるべきでない"
        )


# ---------------------------------------------------------------------------
# 9. セキュリティテスト
# ---------------------------------------------------------------------------

@pytest.mark.integration
class TestAlertHistorySecurity:
    """セキュリティテスト
    観点: 9.1 SQLインジェクションテスト、9.2 XSSテスト
    """

    def test_sql_injection_basic_does_not_crash(self, client):
        """9.1.1: デバイス名への基本 SQLインジェクション試行がエラーにならない"""
        # Arrange
        injection_payload = "' OR '1'='1"

        # Act
        response = _post_search(client, device_name=injection_payload)

        # Assert: アプリがクラッシュせず正常応答が返ること
        assert response.status_code == 200

    def test_sql_injection_comment_does_not_crash(self, client):
        """9.1.2: コメントを使った SQLインジェクション試行がエラーにならない"""
        # Arrange
        injection_payload = "'; DROP TABLE alert_history--"

        # Act
        response = _post_search(client, device_name=injection_payload)

        # Assert
        assert response.status_code == 200

    def test_sql_injection_union_does_not_crash(self, client):
        """9.1.3: UNION を使った SQLインジェクション試行がエラーにならない"""
        # Arrange
        injection_payload = "' UNION SELECT 1,2,3--"

        # Act
        response = _post_search(client, alert_name=injection_payload)

        # Assert
        assert response.status_code == 200

    def test_xss_script_tag_is_escaped_in_list(self, client):
        """9.2.1: scriptタグを含む検索値が HTML エスケープされて表示される（XSS 対策確認）"""
        # Arrange
        xss_payload = "<script>alert('XSS')</script>"

        # Act
        response = _post_search(client, device_name=xss_payload)

        # Assert: Jinja2 の自動エスケープによりスクリプトタグが生のまま出力されない
        assert response.status_code == 200
        text = response.data.decode('utf-8')
        assert xss_payload not in text

    def test_xss_img_tag_is_escaped_in_list(self, client):
        """9.2.2: imgタグ XSS を含む検索値が HTML エスケープされて表示される"""
        # Arrange
        xss_payload = "<img src=x onerror=alert('XSS')>"

        # Act
        response = _post_search(client, device_name=xss_payload)

        # Assert
        assert response.status_code == 200
        text = response.data.decode('utf-8')
        assert xss_payload not in text

    def test_xss_javascript_protocol_is_escaped_in_list(self, client):
        """9.2.3: JavaScriptプロトコル XSS を含む検索値が HTML エスケープされて表示される"""
        # Arrange
        xss_payload = "javascript:alert('XSS')"

        # Act
        response = _post_search(client, device_name=xss_payload)

        # Assert
        assert response.status_code == 200
        text = response.data.decode('utf-8')
        assert xss_payload not in text

    def test_csrf_token_absent_is_rejected(self, app, client):
        """9.3.1: CSRFトークンなし POST は拒否される（400 または 403）

        TestingConfig では WTF_CSRF_ENABLED=False だが、このテストでは
        True に上書きして CSRF 保護を有効化し、トークンなし POST が
        Flask-WTF の CSRFProtect により拒否されることを確認する。
        """
        # Arrange: CSRF を有効化
        app.config['WTF_CSRF_ENABLED'] = True
        try:
            # Act: CSRF トークンなしで POST
            response = _post_search(client)

            # Assert: CSRF バリデーション失敗 → 400 または 403
            assert response.status_code in (400, 403)
        finally:
            # 他のテストに影響しないよう CSRF を無効化に戻す
            app.config['WTF_CSRF_ENABLED'] = False

    def test_csrf_invalid_token_is_rejected(self, app, client):
        """9.3.2: 不正な CSRF トークン付き POST は拒否される（400 または 403）"""
        # Arrange: CSRF を有効化
        app.config['WTF_CSRF_ENABLED'] = True
        try:
            # Act: 不正な CSRF トークンで POST
            response = client.post('/alert/alert-history', data={
                'csrf_token':      'invalid-csrf-token-string',
                'start_datetime':  '',
                'end_datetime':    '',
                'device_name':     '',
                'device_location': '',
                'alert_name':      '',
                'alert_level_id':  '',
                'alert_status_id': '',
                'sort_item_id':    '1',
                'sort_order_id':   '2',
            })

            # Assert: CSRF バリデーション失敗 → 400 または 403
            assert response.status_code in (400, 403)
        finally:
            app.config['WTF_CSRF_ENABLED'] = False

    def test_csrf_disabled_allows_post_without_token(self, client):
        """9.3.3: テスト環境では WTF_CSRF_ENABLED=False により CSRF が無効化され、
        トークンなし POST が成功する（テスト基盤の CSRF 無効化設定の確認）

        NOTE: 本番環境では Flask-WTF の CSRFProtect が有効であり、
              有効なトークンなしの POST は拒否される（9.3.1/9.3.2 で確認済み）。
        """
        # Arrange: CSRF は TestingConfig により無効化済み（WTF_CSRF_ENABLED=False）

        # Act: トークンなしで POST
        response = _post_search(client)

        # Assert: CSRF 無効のため正常処理
        assert response.status_code == 200


# ---------------------------------------------------------------------------
# 10. ログ出力テスト
# ---------------------------------------------------------------------------

@pytest.mark.integration
class TestAlertHistoryLog:
    """ログ出力テスト
    観点: 8.1 正常系ログテスト（8.1.1〜8.1.3, 8.1.5）、8.2 異常系ログテスト（8.2.1）、
          8.3 機密情報マスキングテスト（8.3.1, 8.3.2）

    スコープ外:
      8.2.2 警告ログ（仕様書にWARNINGログの記載なし）

    NOTE: alert_history.py に logger 実装が追加されるまで本クラスは失敗する。
          実装追加後にテストがパスすることを確認すること。
    """

    def test_error_log_on_detail_service_failure(self, client, caplog):
        """8.2.1: サービス層で予期外例外が発生した際、ERROR ログが出力される"""
        # Arrange
        import logging
        from unittest.mock import patch

        nonexistent_uuid = str(uuid.uuid4())

        # Act: サービス関数が予期外例外を送出する状況を再現
        with caplog.at_level(logging.ERROR):
            with patch(
                'iot_app.views.alert.alert_history.get_alert_history_detail',
                side_effect=RuntimeError("DB接続エラー（テスト）"),
            ):
                response = client.get(f'/alert/alert-history/{nonexistent_uuid}')

        # Assert
        assert response.status_code == 404
        error_records = [r for r in caplog.records if r.levelno == logging.ERROR]
        assert len(error_records) > 0, "ERROR ログが出力されていない"
        assert any('アラート履歴' in r.message for r in error_records), \
            "ERROR ログに 'アラート履歴' が含まれていない"

    def test_user_operation_log_on_search(self, client, caplog):
        """8.1.5: 検索実行時に user_id を含む INFO ログが出力される"""
        # Arrange
        import logging

        # Act
        with caplog.at_level(logging.INFO):
            response = _post_search(client)

        # Assert
        assert response.status_code == 200
        info_records = [r for r in caplog.records if r.levelno == logging.INFO]
        assert len(info_records) > 0, "INFO ログが出力されていない"
        assert any('user_id' in r.message for r in info_records), \
            "INFO ログに 'user_id' が含まれていない"

    def test_processing_start_log_on_list(self, client, caplog):
        """8.1.1: 一覧表示リクエスト処理開始時に INFO ログが出力される"""
        # Arrange
        import logging

        # Act
        with caplog.at_level(logging.INFO):
            response = client.get('/alert/alert-history')

        # Assert
        assert response.status_code == 200
        info_records = [r for r in caplog.records if r.levelno == logging.INFO]
        assert len(info_records) > 0, "INFO ログが出力されていない"

    def test_processing_complete_log_on_list(self, client, caplog):
        """8.1.2: 一覧表示処理完了時に INFO ログが出力される"""
        # Arrange
        import logging

        # Act
        with caplog.at_level(logging.INFO):
            response = client.get('/alert/alert-history')

        # Assert
        assert response.status_code == 200
        info_records = [r for r in caplog.records if r.levelno == logging.INFO]
        assert len(info_records) > 0, "INFO ログが出力されていない"
        assert any('完了' in r.message for r in info_records), \
            "INFO ログに '完了' が含まれていない"

    def test_db_query_log_on_list(self, client, caplog):
        """8.1.3: 一覧取得時に DB クエリ前後の INFO ログが出力される"""
        # Arrange
        import logging

        # Act
        with caplog.at_level(logging.INFO):
            response = client.get('/alert/alert-history')

        # Assert
        assert response.status_code == 200
        info_records = [r for r in caplog.records if r.levelno == logging.INFO]
        messages = ' '.join(r.message for r in info_records)
        assert '取得開始' in messages, "DBクエリ開始ログ（'取得開始'）が出力されていない"
        assert '取得完了' in messages, "DBクエリ完了ログ（'取得完了'）が出力されていない"

    def test_email_not_logged_in_plain_text(self, client, caplog):
        """8.3.1: ユーザーのメールアドレスがログに平文で出力されない

        inject_test_user が設定する email_address（test@example.com）が
        ログに平文で記録されないことを確認する。
        """
        # Arrange
        import logging

        plain_email = "test@example.com"  # inject_test_user の email_address

        # Act
        with caplog.at_level(logging.DEBUG):
            response = client.get('/alert/alert-history')

        # Assert
        assert response.status_code == 200
        all_log_text = ' '.join(r.getMessage() for r in caplog.records)
        assert plain_email not in all_log_text, \
            "メールアドレスが平文でログに出力されている"

    def test_email_masking_format_via_adapter(self, app, caplog):
        """8.3.2: AppLoggerAdapter によるメールアドレスのマスキング形式が正しい

        先頭2文字 + **** + @ドメイン の形式でマスキングされることを確認する。
        例: test@example.com → te****@example.com
        """
        # Arrange
        import logging
        from iot_app.common.logger import get_logger

        test_logger = get_logger('test.alert_history_masking')
        raw_email = 'test@example.com'
        expected_masked = 'te****@example.com'

        # Act: リクエストコンテキスト内でマスキング対象ログを出力
        with app.test_request_context('/alert/alert-history'):
            with caplog.at_level(logging.INFO, logger='test.alert_history_masking'):
                test_logger.info("マスキングテスト", extra={'email': raw_email})

        # Assert
        email_records = [r for r in caplog.records if hasattr(r, 'email')]
        assert len(email_records) > 0, "email フィールドを持つログレコードが出力されていない"
        assert email_records[0].email == expected_masked, \
            f"マスキング形式が正しくない: {email_records[0].email}"
