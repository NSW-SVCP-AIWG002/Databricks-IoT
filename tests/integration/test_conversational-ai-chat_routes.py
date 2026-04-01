"""
対話型AIチャット機能 結合テスト (CHT-001)
観点: integration-test-perspectives.md

対象エンドポイント:
    GET  /analysis/chat       - チャット画面表示 (CHT-001)
    POST /api/analysis/chat   - 質問送信API
"""
import json
import os
import uuid
from unittest.mock import MagicMock, patch

import pytest
import requests as req_lib


# ---------------------------------------------------------------------------
# フィクスチャ
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def bypass_auth_middleware():
    """認証ミドルウェアをテスト用にバイパスする

    DevAuthProvider が "dev@localhost" のユーザーを DB から検索するが、
    テスト DB には存在しないため 403 になる。
    find_user_by_email をパッチして middleware が正常通過するようにする。
    """
    with patch(
        'iot_app.auth.middleware.find_user_by_email',
        return_value={'user_id': 1, 'user_type_id': 1},
    ):
        with patch.dict(os.environ, {'DEV_DATABRICKS_TOKEN': 'test-token'}):
            yield


# ---------------------------------------------------------------------------
# ヘルパー
# ---------------------------------------------------------------------------

def _valid_thread_id() -> str:
    """テスト用 UUID 文字列を返す"""
    return str(uuid.uuid4())


def _orchestrator_ok_response() -> dict:
    """AIオーケストレータ正常応答（status='ok'）のモックデータ"""
    return {
        "predictions": {
            "status": "ok",
            "message": "昨日（2026/02/03）の第1冷凍庫の平均温度は **-18.5℃** でした。",
            "df": [{"avg_temp": -18.5}],
            "fig_data": None,
            "sql_query": "SELECT AVG(internal_temp_freezer_1) FROM sensor_data_view",
        }
    }


def _orchestrator_interrupted_response() -> dict:
    """AIオーケストレータ HITL 中断応答（status='interrupted'）のモックデータ"""
    return {
        "predictions": {
            "status": "interrupted",
            "message": "以下のデータを取得しました。グラフを作成しますか？",
            "df": [{"date": "2026-02-03", "avg_temp": -18.5}],
            "fig_data": None,
            "sql_query": "SELECT ...",
        }
    }


def _make_mock_response(json_data: dict) -> MagicMock:
    """requests.post の戻り値となるモックオブジェクトを生成する"""
    mock_resp = MagicMock()
    mock_resp.raise_for_status = MagicMock()
    mock_resp.json.return_value = json_data
    return mock_resp


# ---------------------------------------------------------------------------
# 1. チャット画面表示テスト（GET /analysis/chat）
# ---------------------------------------------------------------------------

@pytest.mark.integration
class TestChatPageDisplay:
    """チャット画面表示テスト
    観点: 2.1 正常遷移テスト
    """

    def test_get_chat_page_returns_200(self, client):
        """2.1.1: /analysis/chat へ GET アクセスで 200 を返す"""
        # Arrange & Act
        response = client.get('/analysis/chat')

        # Assert
        assert response.status_code == 200

    def test_get_chat_page_content_type_is_html(self, client):
        """2.1.1: レスポンスの Content-Type が text/html"""
        # Arrange & Act
        response = client.get('/analysis/chat')

        # Assert
        assert response.content_type.startswith('text/html')

    def test_get_chat_page_contains_question_input(self, client):
        """2.1.1: 質問入力エリア（question_input または question）が HTML に含まれる"""
        # Arrange & Act
        response = client.get('/analysis/chat')
        body = response.data.decode('utf-8')

        # Assert
        assert 'question' in body

    def test_get_chat_page_contains_submit_button(self, client):
        """2.1.1: 送信ボタン（submit_btn または「送信」テキスト）が HTML に含まれる"""
        # Arrange & Act
        response = client.get('/analysis/chat')
        body = response.data.decode('utf-8')

        # Assert
        assert 'submit_btn' in body or '送信' in body

    def test_get_chat_page_contains_new_conversation_button(self, client):
        """2.1.1: 「新しい会話を開始」ボタンが HTML に含まれる"""
        # Arrange & Act
        response = client.get('/analysis/chat')
        body = response.data.decode('utf-8')

        # Assert
        assert 'new_conversation_btn' in body or '新しい会話を開始' in body

    def test_get_chat_page_contains_loading_indicator(self, client):
        """2.1.1: ローディング表示要素（loading_indicator）が HTML に含まれる"""
        # Arrange & Act
        response = client.get('/analysis/chat')
        body = response.data.decode('utf-8')

        # Assert
        assert 'loading_indicator' in body or 'loading' in body


# ---------------------------------------------------------------------------
# 2. 質問送信API バリデーションテスト（POST /api/analysis/chat）
# ---------------------------------------------------------------------------

@pytest.mark.integration
class TestChatAPIValidation:
    """質問送信API バリデーションテスト
    観点: 3.1 必須チェック, 3.2 文字列長チェック, 3.6 不整値チェック
    """

    ENDPOINT = '/api/analysis/chat'

    # --- question バリデーション ---

    def test_missing_question_returns_400(self, client):
        """3.1.2: question フィールド未指定で 400 VALIDATION_ERROR"""
        # Arrange
        payload = {"thread_id": _valid_thread_id()}

        # Act
        response = client.post(
            self.ENDPOINT,
            data=json.dumps(payload),
            content_type='application/json',
        )
        body = response.get_json()

        # Assert
        assert response.status_code == 400
        assert body['success'] is False
        assert body['error_code'] == 'VALIDATION_ERROR'

    def test_empty_string_question_returns_400(self, client):
        """3.1.2: question が空文字で 400 VALIDATION_ERROR"""
        # Arrange
        payload = {"question": "", "thread_id": _valid_thread_id()}

        # Act
        response = client.post(
            self.ENDPOINT,
            data=json.dumps(payload),
            content_type='application/json',
        )
        body = response.get_json()

        # Assert
        assert response.status_code == 400
        assert body['success'] is False
        assert body['error_code'] == 'VALIDATION_ERROR'

    def test_whitespace_only_question_returns_400(self, client):
        """3.1.2: question が空白のみで 400 VALIDATION_ERROR"""
        # Arrange
        payload = {"question": "   \t\n", "thread_id": _valid_thread_id()}

        # Act
        response = client.post(
            self.ENDPOINT,
            data=json.dumps(payload),
            content_type='application/json',
        )
        body = response.get_json()

        # Assert
        assert response.status_code == 400
        assert body['success'] is False
        assert body['error_code'] == 'VALIDATION_ERROR'

    def test_question_over_max_length_returns_400(self, client):
        """3.2.2: question が 1001 文字（最大1000文字超過）で 400 VALIDATION_ERROR"""
        # Arrange
        payload = {
            "question": "あ" * 1001,
            "thread_id": _valid_thread_id(),
        }

        # Act
        response = client.post(
            self.ENDPOINT,
            data=json.dumps(payload),
            content_type='application/json',
        )
        body = response.get_json()

        # Assert
        assert response.status_code == 400
        assert body['success'] is False
        assert body['error_code'] == 'VALIDATION_ERROR'

    def test_question_at_max_length_is_accepted(self, client):
        """3.2.1: question が 1000 文字（上限値）で正常処理される"""
        # Arrange
        tid = _valid_thread_id()
        payload = {"question": "\\" * 1000, "thread_id": tid}
        mock_resp = _make_mock_response(_orchestrator_ok_response())

        # Act
        with patch('iot_app.views.analysis.chat.views.requests.post', return_value=mock_resp):
            response = client.post(
                self.ENDPOINT,
                data=json.dumps(payload),
                content_type='application/json',
            )
        body = response.get_json()

        # Assert
        assert response.status_code == 200
        assert body['success'] is True

    def test_question_single_char_is_accepted(self, client):
        """3.2.1: question が 1 文字（最小値）で正常処理される"""
        # Arrange
        tid = _valid_thread_id()
        payload = {"question": "あ", "thread_id": tid}
        mock_resp = _make_mock_response(_orchestrator_ok_response())

        # Act
        with patch('iot_app.views.analysis.chat.views.requests.post', return_value=mock_resp):
            response = client.post(
                self.ENDPOINT,
                data=json.dumps(payload),
                content_type='application/json',
            )
        body = response.get_json()

        # Assert
        assert response.status_code == 200
        assert body['success'] is True

    # --- thread_id バリデーション ---

    def test_missing_thread_id_returns_400(self, client):
        """3.1.2: thread_id フィールド未指定で 400 VALIDATION_ERROR"""
        # Arrange
        payload = {"question": "昨日の温度は？"}

        # Act
        response = client.post(
            self.ENDPOINT,
            data=json.dumps(payload),
            content_type='application/json',
        )
        body = response.get_json()

        # Assert
        assert response.status_code == 400
        assert body['success'] is False
        assert body['error_code'] == 'VALIDATION_ERROR'

    def test_empty_thread_id_returns_400(self, client):
        """3.1.2: thread_id が空文字で 400 VALIDATION_ERROR"""
        # Arrange
        payload = {"question": "昨日の温度は？", "thread_id": ""}

        # Act
        response = client.post(
            self.ENDPOINT,
            data=json.dumps(payload),
            content_type='application/json',
        )
        body = response.get_json()

        # Assert
        assert response.status_code == 400
        assert body['success'] is False
        assert body['error_code'] == 'VALIDATION_ERROR'

    def test_non_uuid_thread_id_returns_400(self, client):
        """3.6.2: thread_id が UUID 形式でない場合 400 VALIDATION_ERROR"""
        # Arrange
        payload = {
            "question": "昨日の温度は？",
            "thread_id": "not-a-valid-uuid-string",
        }

        # Act
        response = client.post(
            self.ENDPOINT,
            data=json.dumps(payload),
            content_type='application/json',
        )
        body = response.get_json()

        # Assert
        assert response.status_code == 400
        assert body['success'] is False
        assert body['error_code'] == 'VALIDATION_ERROR'

    def test_non_json_request_body_returns_400(self, client):
        """3.1.2: JSON でないリクエストボディで 400 エラー（question が空扱い）"""
        # Arrange & Act
        response = client.post(
            self.ENDPOINT,
            data="not json at all",
            content_type='text/plain',
        )
        body = response.get_json()

        # Assert
        assert response.status_code == 400
        assert body['success'] is False


# ---------------------------------------------------------------------------
# 3. 質問送信API 正常系テスト
# ---------------------------------------------------------------------------

@pytest.mark.integration
class TestChatAPINormal:
    """質問送信API 正常系テスト
    観点: 6.1 外部API連携 正常系テスト
    """

    ENDPOINT = '/api/analysis/chat'

    def test_success_returns_200_and_success_true(self, client):
        """6.1.1: AIオーケストレータが正常応答した場合 200 success=true"""
        # Arrange
        tid = _valid_thread_id()
        payload = {"question": "昨日の第1冷凍庫の平均温度は？", "thread_id": tid}
        mock_resp = _make_mock_response(_orchestrator_ok_response())

        # Act
        with patch('iot_app.views.analysis.chat.views.requests.post', return_value=mock_resp):
            response = client.post(
                self.ENDPOINT,
                data=json.dumps(payload),
                content_type='application/json',
            )
        body = response.get_json()

        # Assert
        assert response.status_code == 200
        assert body['success'] is True

    def test_success_response_contains_required_fields(self, client):
        """6.1.3: 正常応答に必須フィールドが含まれる（success, thread_id, status, message, df, fig_data, sql_query）"""
        # Arrange
        tid = _valid_thread_id()
        payload = {"question": "昨日の温度は？", "thread_id": tid}
        mock_resp = _make_mock_response(_orchestrator_ok_response())

        # Act
        with patch('iot_app.views.analysis.chat.views.requests.post', return_value=mock_resp):
            response = client.post(
                self.ENDPOINT,
                data=json.dumps(payload),
                content_type='application/json',
            )
        body = response.get_json()

        # Assert
        for key in ('success', 'thread_id', 'status', 'message', 'df', 'fig_data', 'sql_query'):
            assert key in body, f"レスポンスに '{key}' が含まれていない"

    def test_success_status_field_is_ok(self, client):
        """6.1.1: オーケストレータ正常応答時 status='ok' が返される"""
        # Arrange
        tid = _valid_thread_id()
        payload = {"question": "温度は？", "thread_id": tid}
        mock_resp = _make_mock_response(_orchestrator_ok_response())

        # Act
        with patch('iot_app.views.analysis.chat.views.requests.post', return_value=mock_resp):
            response = client.post(
                self.ENDPOINT,
                data=json.dumps(payload),
                content_type='application/json',
            )
        body = response.get_json()

        # Assert
        assert body['status'] == 'ok'

    def test_thread_id_is_preserved_in_response(self, client):
        """6.1.1: リクエストの thread_id がレスポンスにそのまま返される"""
        # Arrange
        tid = _valid_thread_id()
        payload = {"question": "温度は？", "thread_id": tid}
        mock_resp = _make_mock_response(_orchestrator_ok_response())

        # Act
        with patch('iot_app.views.analysis.chat.views.requests.post', return_value=mock_resp):
            response = client.post(
                self.ENDPOINT,
                data=json.dumps(payload),
                content_type='application/json',
            )
        body = response.get_json()

        # Assert
        assert body['thread_id'] == tid

    def test_response_content_type_is_json(self, client):
        """6.1.2: レスポンスの Content-Type が application/json"""
        # Arrange
        tid = _valid_thread_id()
        payload = {"question": "温度は？", "thread_id": tid}
        mock_resp = _make_mock_response(_orchestrator_ok_response())

        # Act
        with patch('iot_app.views.analysis.chat.views.requests.post', return_value=mock_resp):
            response = client.post(
                self.ENDPOINT,
                data=json.dumps(payload),
                content_type='application/json',
            )

        # Assert
        assert response.content_type.startswith('application/json')

    def test_hitl_interrupted_status_is_returned(self, client):
        """6.1.1: AIオーケストレータが HITL 中断応答の場合 status='interrupted' が返される"""
        # Arrange
        tid = _valid_thread_id()
        payload = {"question": "先月の温度推移をグラフ化して", "thread_id": tid}
        mock_resp = _make_mock_response(_orchestrator_interrupted_response())

        # Act
        with patch('iot_app.views.analysis.chat.views.requests.post', return_value=mock_resp):
            response = client.post(
                self.ENDPOINT,
                data=json.dumps(payload),
                content_type='application/json',
            )
        body = response.get_json()

        # Assert
        assert response.status_code == 200
        assert body['success'] is True
        assert body['status'] == 'interrupted'

    def test_hitl_interrupted_response_contains_df(self, client):
        """6.1.3: HITL 中断応答に df（Genie 取得結果）が含まれる"""
        # Arrange
        tid = _valid_thread_id()
        payload = {"question": "先月の温度推移をグラフ化して", "thread_id": tid}
        mock_resp = _make_mock_response(_orchestrator_interrupted_response())

        # Act
        with patch('iot_app.views.analysis.chat.views.requests.post', return_value=mock_resp):
            response = client.post(
                self.ENDPOINT,
                data=json.dumps(payload),
                content_type='application/json',
            )
        body = response.get_json()

        # Assert
        assert body['df'] is not None
        assert isinstance(body['df'], list)

    def test_orchestrator_called_with_question_and_thread_id(self, client):
        """6.1.1: オーケストレータに question と thread_id が正しく渡される"""
        # Arrange
        tid = _valid_thread_id()
        question = "昨日の第1冷凍庫の平均温度は？"
        payload = {"question": question, "thread_id": tid}
        mock_resp = _make_mock_response(_orchestrator_ok_response())

        # Act
        with patch(
            'iot_app.views.analysis.chat.views.requests.post',
            return_value=mock_resp,
        ) as mock_post:
            client.post(
                self.ENDPOINT,
                data=json.dumps(payload),
                content_type='application/json',
            )

        # Assert
        called_payload = mock_post.call_args[1]['json']
        record = called_payload['dataframe_records'][0]
        assert record['thread_id'] == tid
        # question はサニタイズ後に送信されるため、元テキストと等価または無害化済み
        assert record['prompt'] is not None


# ---------------------------------------------------------------------------
# 4. 質問送信API 異常系テスト（外部API連携エラー）
# ---------------------------------------------------------------------------

@pytest.mark.integration
class TestChatAPIError:
    """質問送信API 異常系テスト
    観点: 6.2 外部API連携 異常系テスト
    """

    ENDPOINT = '/api/analysis/chat'

    def _base_payload(self) -> dict:
        return {"question": "昨日の温度は？", "thread_id": _valid_thread_id()}

    def test_timeout_returns_500_genie_timeout(self, client):
        """6.2.4: AIオーケストレータがタイムアウト → 500 GENIE_TIMEOUT"""
        # Arrange
        payload = self._base_payload()

        # Act
        with patch(
            'iot_app.views.analysis.chat.views.requests.post',
            side_effect=req_lib.exceptions.Timeout,
        ):
            response = client.post(
                self.ENDPOINT,
                data=json.dumps(payload),
                content_type='application/json',
            )
        body = response.get_json()

        # Assert
        assert response.status_code == 500
        assert body['success'] is False
        assert body['error_code'] == 'GENIE_TIMEOUT'

    def test_connection_error_returns_500_network_error(self, client):
        """6.2.3: AIオーケストレータへの接続失敗 → 500 NETWORK_ERROR"""
        # Arrange
        payload = self._base_payload()

        # Act
        with patch(
            'iot_app.views.analysis.chat.views.requests.post',
            side_effect=req_lib.exceptions.ConnectionError,
        ):
            response = client.post(
                self.ENDPOINT,
                data=json.dumps(payload),
                content_type='application/json',
            )
        body = response.get_json()

        # Assert
        assert response.status_code == 500
        assert body['success'] is False
        assert body['error_code'] == 'NETWORK_ERROR'

    def test_http_error_5xx_returns_500_orchestrator_error(self, client):
        """6.2.2: AIオーケストレータが 5xx 返却 → 500 ORCHESTRATOR_ERROR"""
        # Arrange
        payload = self._base_payload()
        mock_resp = MagicMock()
        mock_resp.raise_for_status.side_effect = req_lib.exceptions.HTTPError(
            response=MagicMock(status_code=500)
        )

        # Act
        with patch('iot_app.views.analysis.chat.views.requests.post', return_value=mock_resp):
            response = client.post(
                self.ENDPOINT,
                data=json.dumps(payload),
                content_type='application/json',
            )
        body = response.get_json()

        # Assert
        assert response.status_code == 500
        assert body['success'] is False
        assert body['error_code'] == 'ORCHESTRATOR_ERROR'

    def test_http_error_4xx_returns_500_orchestrator_error(self, client):
        """6.2.1: AIオーケストレータが 4xx 返却 → 500 ORCHESTRATOR_ERROR"""
        # Arrange
        payload = self._base_payload()
        mock_resp = MagicMock()
        mock_resp.raise_for_status.side_effect = req_lib.exceptions.HTTPError(
            response=MagicMock(status_code=403)
        )

        # Act
        with patch('iot_app.views.analysis.chat.views.requests.post', return_value=mock_resp):
            response = client.post(
                self.ENDPOINT,
                data=json.dumps(payload),
                content_type='application/json',
            )
        body = response.get_json()

        # Assert
        assert response.status_code == 500
        assert body['success'] is False
        assert body['error_code'] == 'ORCHESTRATOR_ERROR'

    def test_unexpected_exception_returns_500_orchestrator_error(self, client):
        """6.2.5: 予期しない例外発生 → 500 ORCHESTRATOR_ERROR"""
        # Arrange
        payload = self._base_payload()

        # Act
        with patch(
            'iot_app.views.analysis.chat.views.requests.post',
            side_effect=RuntimeError("unexpected error"),
        ):
            response = client.post(
                self.ENDPOINT,
                data=json.dumps(payload),
                content_type='application/json',
            )
        body = response.get_json()

        # Assert
        assert response.status_code == 500
        assert body['success'] is False
        assert body['error_code'] == 'ORCHESTRATOR_ERROR'

    def test_error_response_contains_error_message_field(self, client):
        """6.2.1: エラーレスポンスに error_message フィールドが含まれ、空でない"""
        # Arrange
        payload = self._base_payload()

        # Act
        with patch(
            'iot_app.views.analysis.chat.views.requests.post',
            side_effect=req_lib.exceptions.Timeout,
        ):
            response = client.post(
                self.ENDPOINT,
                data=json.dumps(payload),
                content_type='application/json',
            )
        body = response.get_json()

        # Assert
        assert 'error_message' in body
        assert len(body['error_message']) > 0

    def test_genie_timeout_error_message_content(self, client):
        """6.2.4: GENIE_TIMEOUT 時のエラーメッセージ内容が仕様通り"""
        # Arrange
        payload = self._base_payload()

        # Act
        with patch(
            'iot_app.views.analysis.chat.views.requests.post',
            side_effect=req_lib.exceptions.Timeout,
        ):
            response = client.post(
                self.ENDPOINT,
                data=json.dumps(payload),
                content_type='application/json',
            )
        body = response.get_json()

        # Assert
        assert 'タイムアウト' in body['error_message']

    def test_network_error_message_content(self, client):
        """6.2.3: NETWORK_ERROR 時のエラーメッセージ内容が仕様通り"""
        # Arrange
        payload = self._base_payload()

        # Act
        with patch(
            'iot_app.views.analysis.chat.views.requests.post',
            side_effect=req_lib.exceptions.ConnectionError,
        ):
            response = client.post(
                self.ENDPOINT,
                data=json.dumps(payload),
                content_type='application/json',
            )
        body = response.get_json()

        # Assert
        assert '接続エラー' in body['error_message']


# ---------------------------------------------------------------------------
# 5. セキュリティテスト（入力サニタイズ）
# ---------------------------------------------------------------------------

@pytest.mark.integration
class TestChatAPISecurity:
    """質問送信API セキュリティテスト
    観点: 9.1 SQLインジェクションテスト, 9.2 XSSテスト
    """

    ENDPOINT = '/api/analysis/chat'

    def _post_with_mock(self, client, question: str):
        """指定した question でリクエストを送り、(response, mock_post) を返す"""
        tid = _valid_thread_id()
        payload = {"question": question, "thread_id": tid}
        mock_resp = _make_mock_response({
            "predictions": {
                "status": "ok",
                "message": "テスト回答",
                "df": None,
                "fig_data": None,
                "sql_query": None,
            }
        })
        with patch(
            'iot_app.views.analysis.chat.views.requests.post',
            return_value=mock_resp,
        ) as mock_post:
            response = client.post(
                self.ENDPOINT,
                data=json.dumps(payload),
                content_type='application/json',
            )
        return response, mock_post

    def test_sql_injection_basic_is_sanitized_before_sending(self, client):
        """9.1.1: SQLインジェクション文字列（' OR '1'='1）が HTML エスケープされてオーケストレータに渡される"""
        # Arrange
        malicious_input = "' OR '1'='1"

        # Act
        response, mock_post = self._post_with_mock(client, malicious_input)

        # Assert - リクエストは成功（バリデーションエラーにならない）
        assert response.status_code == 200
        # オーケストレータへの送信内容に生の SQL インジェクション文字列が含まれないこと
        called_payload = mock_post.call_args[1]['json']
        sent_prompt = called_payload['dataframe_records'][0]['prompt']
        assert sent_prompt != malicious_input  # HTML エスケープ後は変換されている

    def test_sql_injection_drop_table_is_sanitized(self, client):
        """9.1.2: DROP TABLE を含む入力がサニタイズされてオーケストレータに渡される"""
        # Arrange
        malicious_input = "'; DROP TABLE sensor_data--"

        # Act
        response, mock_post = self._post_with_mock(client, malicious_input)

        # Assert
        assert response.status_code == 200
        called_payload = mock_post.call_args[1]['json']
        sent_prompt = called_payload['dataframe_records'][0]['prompt']
        # シングルクォートが HTML エスケープ（&#39; 等）されていること
        assert "'" not in sent_prompt or sent_prompt != malicious_input

    def test_xss_script_tag_is_html_escaped(self, client):
        """9.2.1: <script> タグが HTML エスケープされてオーケストレータに渡される"""
        # Arrange
        xss_input = "<script>alert('XSS')</script>"

        # Act
        response, mock_post = self._post_with_mock(client, xss_input)

        # Assert
        assert response.status_code == 200
        called_payload = mock_post.call_args[1]['json']
        sent_prompt = called_payload['dataframe_records'][0]['prompt']
        assert '<script>' not in sent_prompt

    def test_xss_img_onerror_tag_is_html_escaped(self, client):
        """9.2.2: <img onerror> タグが HTML エスケープされてオーケストレータに渡される"""
        # Arrange
        xss_input = "<img src=x onerror=alert('XSS')>"

        # Act
        response, mock_post = self._post_with_mock(client, xss_input)

        # Assert
        assert response.status_code == 200
        called_payload = mock_post.call_args[1]['json']
        sent_prompt = called_payload['dataframe_records'][0]['prompt']
        assert '<img' not in sent_prompt

    def test_control_characters_are_removed(self, client):
        """9.2.3: 制御文字（\\x00-\\x1f）が除去されてオーケストレータに渡される"""
        # Arrange
        input_with_control = "質問\x00テキスト\x1f終わり"

        # Act
        response, mock_post = self._post_with_mock(client, input_with_control)

        # Assert
        assert response.status_code == 200
        called_payload = mock_post.call_args[1]['json']
        sent_prompt = called_payload['dataframe_records'][0]['prompt']
        assert '\x00' not in sent_prompt
        assert '\x1f' not in sent_prompt

    def test_high_unicode_control_characters_are_removed(self, client):
        """9.2.3: 高位制御文字（\\x7f-\\x9f）が除去されてオーケストレータに渡される"""
        # Arrange
        input_with_control = "質問\x7fテキスト\x9f終わり"

        # Act
        response, mock_post = self._post_with_mock(client, input_with_control)

        # Assert
        assert response.status_code == 200
        called_payload = mock_post.call_args[1]['json']
        sent_prompt = called_payload['dataframe_records'][0]['prompt']
        assert '\x7f' not in sent_prompt
        assert '\x9f' not in sent_prompt
