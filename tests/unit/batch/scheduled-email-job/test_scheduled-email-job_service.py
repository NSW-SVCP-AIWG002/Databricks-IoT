"""
メール通知送信バッチ Service層 単体テスト

対象モジュール: src/batch/email_notification_sender.py
対象関数:
  - send_emails_bulk                : SendGrid API によるバルクメール送信
  - validate_and_enrich_records     : 組織・ユーザーマスタ存在チェックと user_id 取得
  - cleanup_stale_processing_records: PROCESSING 滞留レコードの FAILED 更新
  - process_email_queue             : メール送信キューのメイン処理オーケストレーション

設計書:
  - docs/03-features/batch/scheduled-email-job/README.md
  - docs/03-features/batch/scheduled-email-job/job-specification.md

テスト観点:
  - docs/05-testing/unit-test/unit-test-perspectives.md
"""
import json
import pytest
from unittest.mock import MagicMock, patch

# テスト対象モジュールのパス（@patch デコレータで使用）
MODULE = "batch.email_notification_sender"


# =============================================================================
# ヘルパー関数
# =============================================================================

def _make_queue_record(queue_id, subject="アラート通知", body="閾値を超えました",
                       emails=None, org_id=100, retry_count=0):
    """テスト用メール通知キューレコードを生成"""
    if emails is None:
        emails = ["user@example.com"]
    return {
        "queue_id": queue_id,
        "organization_id": org_id,
        "subject": subject,
        "body": body,
        "recipient_email": json.dumps({"to": emails}),
        "retry_count": retry_count,
    }


def _make_conn_mock(fetchone_result=None):
    """DB コネクションと カーソルのモックを生成するヘルパー"""
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_conn.cursor.return_value.__exit__.return_value = False
    if fetchone_result is not None:
        mock_cursor.fetchone.return_value = fetchone_result
    return mock_conn, mock_cursor


# =============================================================================
# send_emails_bulk のテスト
# =============================================================================

@pytest.mark.unit
class TestSendEmailsBulk:
    """send_emails_bulk - SendGrid API 経由のバルクメール送信
    観点: 2.1 正常系処理, 1.3 エラーハンドリング, 3.2.1.4 フィールド網羅, CL-2 エラーハンドリング
    """

    # -------------------------------------------------------------------------
    # 正常系: API 呼び出し、レスポンス処理
    # -------------------------------------------------------------------------

    @patch(f"{MODULE}.requests.post")
    def test_single_record_success_returns_true_result(self, mock_post):
        """2.1.1: 1件のレコードを SendGrid API に送信し、成功結果 (True, None) が返される

        実行内容: recipient_email を含む1件のレコードを渡して send_emails_bulk を呼び出す
        想定結果: results[queue_id] == (True, None) かつ API が1回呼ばれる
        """
        from batch.email_notification_sender import send_emails_bulk

        # Arrange: mock_post が status_code=202 を返す設定
        mock_post.return_value.status_code = 202
        records = [_make_queue_record(queue_id=1)]

        # Act: send_emails_bulk を呼び出す
        results = send_emails_bulk(records)

        # Assert: API コールが1回実行されること
        mock_post.assert_called_once()
        # Assert: 返却されるリストの内容が (True, None) であること
        assert results[1] == (True, None)
        
    # -------------------------------------------------------------------------
    # 正常系: 受信者1人のレコードで API リクエストのペイロード内容とフィールド網羅
    # -------------------------------------------------------------------------
    
    @patch(f"{MODULE}.requests.post")
    def test_api_request_payload_contains_all_required_fields_single_record(self, mock_post):
        """3.1.1.2: API リクエストのペイロードに personalizations・from・subject・content の全フィールドが含まれる

        実行内容: 受信者1名のレコードで send_emails_bulk を呼び出す
        想定結果: personalizations[0]["to"] に全受信者、from・subject・content が正しく設定される
        """
        from batch.email_notification_sender import send_emails_bulk

        # Arrange: mock_post が status_code=202 を返す設定
        mock_post.return_value.status_code = 202
        # Arrange: 全受信者が1人のレコードを用意
        records = [
            _make_queue_record(queue_id=1, subject="件名A", body="本文A", emails=["a@example.com"])
        ]

        # Act: send_emails_bulk を呼び出す
        send_emails_bulk(records)

        # Assert: API コールが1回だけ実行されること
        assert mock_post.call_count == 1
        
        # POSTする際のペイロードを取得して検証
        payload = mock_post.call_args.kwargs.get("json") or mock_post.call_args[1]["json"]
        # Assert: personalizations[0]["to"] に全受信者が正しく設定されること
        assert payload["personalizations"][0]["to"] == [
            {"email": "a@example.com"}
        ]
        # Assert: from が正しく設定されること
        assert payload["from"]["email"] == SENDGRID_CONFIG["from_address"]
        # Assert: subject が正しく設定されること
        assert payload["subject"] == "アラート通知"
        # Assert: content[0].type が正しく設定されること
        assert payload["content"][0]["type"] == "text/plain"
        # Assert: content[0].value が正しく設定されること
        assert payload["content"][0]["value"] == "閾値を超えました"
        
    # -------------------------------------------------------------------------
    # 正常系: 複数レコードのグループ化と API 呼び出し回数
    # -------------------------------------------------------------------------

    @patch(f"{MODULE}.requests.post")
    def test_same_subject_body_grouped_into_one_api_call(self, mock_post):
        """2.1.3: 同一 subject+body の複数レコードが1グループに集約され API コールが1回になる

        実行内容: subject・body が同一のレコード2件を渡す
        想定結果: 両レコードが成功 (True, None)、mock_post.call_count == 1
        """
        from batch.email_notification_sender import send_emails_bulk

        # Arrange: mock_post が status_code=202 を返す設定
        mock_post.return_value.status_code = 202
        # Arrange: subject・body が同一のレコード（送信先は異なる）を複数用意
        records = [
            _make_queue_record(queue_id=1, subject="件名A", body="本文A", emails=["a@example.com"]),
            _make_queue_record(queue_id=2, subject="件名A", body="本文A", emails=["b@example.com"]),
        ]

        # Act: send_emails_bulk を呼び出す
        results = send_emails_bulk(records)
        
        # Assert: API コールが1回だけ実行されること（同一 subject+body でグループ化されているため）
        assert mock_post.call_count == 1
        # Assert: レコードが成功 (True, None) であること
        assert results[0] == (True, None)
        
    # -------------------------------------------------------------------------
    # 正常系: 受信者複数名のレコードで API リクエストのペイロード内容とフィールド網羅
    # -------------------------------------------------------------------------

    @patch(f"{MODULE}.requests.post")
    def test_api_request_payload_contains_all_required_fields(self, mock_post):
        """3.2.1.4: API リクエストのペイロードに personalizations・from・subject・content の全フィールドが含まれる

        実行内容: 受信者2名のレコードで send_emails_bulk を呼び出す
        想定結果: personalizations[0]["to"] に全受信者、from・subject・content が正しく設定される
        """
        from batch.email_notification_sender import send_emails_bulk, SENDGRID_CONFIG

        # Arrange:  mock_post が status_code=202 を返す設定
        mock_post.return_value.status_code = 202
        # Arrange: subject・body が同一のレコード（送信先は異なる）を複数用意
        records = [
            _make_queue_record(queue_id=1, subject="件名A", body="本文A", emails=["a@example.com"]),
            _make_queue_record(queue_id=2, subject="件名A", body="本文A", emails=["b@example.com"]),
        ]

        # Act: send_emails_bulk を呼び出す
        send_emails_bulk(records)

        # Assert: API コールが1回だけ実行されること
        mock_post.assert_called_once()
        
        # POSTする際のペイロードを取得して検証
        payload = mock_post.call_args.kwargs.get("json") or mock_post.call_args[1]["json"]
        # Assert: personalizations[0]["to"] に全受信者が正しく設定されること
        assert payload["personalizations"][0]["to"] == [
            {"email": "a@example.com"},
            {"email": "b@example.com"},
        ]
        # Assert: from が正しく設定されること
        assert payload["from"]["email"] == SENDGRID_CONFIG["from_address"]
        # Assert: subject が正しく設定されること
        assert payload["subject"] == "件名A"
        # Assert: content[0].type が正しく設定されること
        assert payload["content"][0]["type"] == "text/plain"
        # Assert: content[0].value が正しく設定されること
        assert payload["content"][0]["value"] == "本文A"
        
    # -------------------------------------------------------------------------
    # 正常系: グループ化条件（subject+body）と API 呼び出し回数の関係
    # -------------------------------------------------------------------------

    @patch(f"{MODULE}.requests.post")
    def test_different_subject_body_makes_separate_api_calls(self, mock_post):
        """3.1.1.2: subject+body が異なる複数レコードは別グループに分割され、グループ数分 API コールが実行される

        実行内容: subject・body が異なる2件のレコードを渡す
        想定結果: mock_post.call_count == 2 (2グループ→2回コール)
        """
        from batch.email_notification_sender import send_emails_bulk

        # Arrange: mock_post が status_code=202 を返す設定
        mock_post.return_value.status_code = 202
        # Arrange: subject・body が異なるレコードを複数用意
        records = [
            _make_queue_record(queue_id=1, subject="件名A", body="本文A"),
            _make_queue_record(queue_id=2, subject="件名B", body="本文B"),
        ]

        # Act: send_emails_bulk を呼び出す
        results = send_emails_bulk(records)
        
        # Assert: API コールが2回実行されること（subject+body が異なるためグループ化されない）
        assert mock_post.call_count == 2
        # Assert: 両レコードが成功 (True, None) であること
        assert results[0] == (True, None)
        assert results[1] == (True, None)
        
    # -------------------------------------------------------------------------
    # 正常系: グループ化条件（subject）と API 呼び出し回数の関係
    # -------------------------------------------------------------------------

    @patch(f"{MODULE}.requests.post")
    def test_different_subject_makes_separate_api_calls(self, mock_post):
        """3.1.1.2: subject が異なる複数レコードは別グループに分割され、グループ数分 API コールが実行される

        実行内容: subject が異なる2件のレコードを渡す
        想定結果: mock_post.call_count == 2 (2グループ→2回コール)
        """
        from batch.email_notification_sender import send_emails_bulk

        # Arrange: mock_post が status_code=202 を返す設定
        mock_post.return_value.status_code = 202
        # Arrange: subject が異なるレコードを複数用意
        records = [
            _make_queue_record(queue_id=1, subject="件名A", body="本文A"),
            _make_queue_record(queue_id=2, subject="件名B", body="本文A"),
        ]

        # Act: send_emails_bulk を呼び出す
        results = send_emails_bulk(records)
        
        # Assert: API コールが2回実行されること（subject+body が異なるためグループ化されない）
        assert mock_post.call_count == 2
        # Assert: 両レコードが成功 (True, None) であること
        assert results[0] == (True, None)
        assert results[1] == (True, None)
        
    # -------------------------------------------------------------------------
    # 正常系: グループ化条件（body）と API 呼び出し回数の関係
    # -------------------------------------------------------------------------

    @patch(f"{MODULE}.requests.post")
    def test_different_body_makes_separate_api_calls(self, mock_post):
        """3.1.1.2: body が異なる複数レコードは別グループに分割され、グループ数分 API コールが実行される

        実行内容: body が異なる2件のレコードを渡す
        想定結果: mock_post.call_count == 2 (2グループ→2回コール)
        """
        from batch.email_notification_sender import send_emails_bulk

        # Arrange: mock_post が status_code=202 を返す設定
        mock_post.return_value.status_code = 202
        # Arrange: body が異なるレコードを複数用意
        records = [
            _make_queue_record(queue_id=1, subject="件名A", body="本文A"),
            _make_queue_record(queue_id=2, subject="件名A", body="本文B"),
        ]

        # Act: send_emails_bulk を呼び出す
        results = send_emails_bulk(records)
        
        # Assert: API コールが2回実行されること（subject+body が異なるためグループ化されない）
        assert mock_post.call_count == 2
        # Assert: 両レコードが成功 (True, None) であること
        assert results[0] == (True, None)
        assert results[1] == (True, None)
        
    # -------------------------------------------------------------------------
    # 正常系: グループ化条件（subject+body）と API 呼び出し回数の関係
    # -------------------------------------------------------------------------

    @patch(f"{MODULE}.requests.post")
    def test_different_subject_body_makes_separate_api_calls(self, mock_post):
        """3.1.1.2: subject+body が異なる複数レコードは別グループに分割され、グループ数分 API コールが実行される

        実行内容: subject・body が異なるレコード、同一のレコードを渡す
        想定結果: mock_post.call_count == 2 (2グループ→2回コール)
        """
        from batch.email_notification_sender import send_emails_bulk

        # Arrange: mock_post が status_code=202 を返す設定
        mock_post.return_value.status_code = 202
        # Arrange: subject・body が異なるレコード、同一のレコードを複数用意
        records = [
            _make_queue_record(queue_id=1, subject="件名A", body="本文A", emails=["a@example.com"]),
            _make_queue_record(queue_id=2, subject="件名B", body="本文B", emails=["a@example.com"]),
            _make_queue_record(queue_id=3, subject="件名B", body="本文B", emails=["b@example.com"]),
        ]

        # Act: send_emails_bulk を呼び出す
        results = send_emails_bulk(records)

        # Assert: API コールが2回実行されること（subject+body が異なるものはグループ化されない）
        assert mock_post.call_count == 2
        # Assert: 両レコードが成功 (True, None) であること
        assert results[0] == (True, None)
        assert results[1] == (True, None)
        
    # -------------------------------------------------------------------------
    # 正常系: 空のレコードリストに対するAPI リクエストのペイロード内容とフィールド網羅
    # -------------------------------------------------------------------------

    @patch(f"{MODULE}.requests.post")
    def test_empty_records_returns_empty_dict(self, mock_post):
        """3.1.4.2: 空のレコードリストを渡した場合、空の辞書が返され API コールは実行されない

        実行内容: 空リストを渡して send_emails_bulk を呼び出す
        想定結果: 戻り値が {} であること
        """
        from batch.email_notification_sender import send_emails_bulk

        # Arrange: mock_post を用意するが、呼び出されないことを期待するため特に設定しない
        records = []

        # Act: send_emails_bulk を呼び出す
        results = send_emails_bulk(records)

        # Assert: 戻り値が空の辞書であること
        assert results == {}
        # Assert: API コールが一切実行されないこと
        mock_post.assert_not_called()

    # -------------------------------------------------------------------------
    # 異常系: API エラー発生と例外処理
    # -------------------------------------------------------------------------

    @patch(f"{MODULE}.requests.post")
    def test_api_non_202_response_returns_failure_with_status_code(self, mock_post):
        """CL-2-2: SendGrid API が HTTP 202 以外のステータスを返した場合、失敗として処理される

        実行内容: mock_post が status_code=400 を返す設定で send_emails_bulk を呼び出す
        想定結果: results[queue_id] == (False, エラーメッセージ) でステータスコード "400" を含む
        """
        from batch.email_notification_sender import send_emails_bulk

        # Arrange: mock_post が status_code=400 を返す設定
        mock_post.return_value.status_code = 400
        # Arrange: API のエラーレスポンスの内容も設定（"Bad Request"）
        mock_post.return_value.text = "Bad Request"
        records = [_make_queue_record(queue_id=1)]

        # Act: send_emails_bulk を呼び出す
        results = send_emails_bulk(records)
        success, error_msg = results[1]
        
        # Assert: 成功フラグが False であること
        assert success is False
        # Assert: エラーメッセージにステータスコード "400" が含まれること
        assert "400" in error_msg
        # Assert: エラーメッセージに API のエラーレスポンスの内容 "Bad Request" が含まれること
        assert "Bad Request" in error_msg

    # -------------------------------------------------------------------------
    # 異常系: API タイムアウト時の例外処理
    # -------------------------------------------------------------------------

    @patch(f"{MODULE}.requests.post")
    def test_api_timeout_returns_failure_with_timeout_message(self, mock_post):
        """1.3.1 / CL-2-1: SendGrid API への接続がタイムアウトした場合、"SendGrid API Timeout" が返される

        実行内容: mock_post が requests.exceptions.Timeout を発生させる設定で send_emails_bulk を呼び出す
        想定結果: results[queue_id] == (False, "SendGrid API Timeout")
        """
        import requests as _requests
        from batch.email_notification_sender import send_emails_bulk

        # Arrange:  mock_post が requests.exceptions.Timeout を発生させる設定
        mock_post.side_effect = _requests.exceptions.Timeout()
        records = [_make_queue_record(queue_id=1)]

        # Act: send_emails_bulk を呼び出す
        results = send_emails_bulk(records)
        success, error_msg = results[1]
        
        # Assert: 成功フラグが False であること
        assert success is False
        # Assert: エラーメッセージが "SendGrid API Timeout" であること
        assert error_msg == "SendGrid API Timeout"
        
    # -------------------------------------------------------------------------
    # 異常系: API 呼び出し時の予期しない例外の処理
    # -------------------------------------------------------------------------

    @patch(f"{MODULE}.requests.post")
    def test_api_unexpected_exception_returns_failure_with_error_message(self, mock_post):
        """1.3.1 / CL-2-1: 予期しない例外が発生した場合、失敗として "Unexpected Error: ..." が返される

        実行内容: mock_post が ValueError("test error") を発生させる設定で send_emails_bulk を呼び出す
        想定結果: results[queue_id] == (False, "Unexpected Error: test error")
        """
        from batch.email_notification_sender import send_emails_bulk

        # Arrange: mock_post が ValueError("test error") を発生させる設定
        mock_post.side_effect = ValueError("test error")
        records = [_make_queue_record(queue_id=1)]

        # Act: send_emails_bulk を呼び出す
        results = send_emails_bulk(records)
        success, error_msg = results[1]
        
        # Assert: 成功フラグが False であること
        assert success is False
        # Assert: エラーメッセージに "Unexpected Error: test error" が含まれること
        assert error_msg == "Unexpected Error: test error"


# =============================================================================
# validate_and_enrich_records のテスト
# =============================================================================

@pytest.mark.unit
class TestValidateAndEnrichRecords:
    """validate_and_enrich_records - 組織・ユーザーマスタ存在チェックと user_id 取得
    観点: 1.1.6 不整値チェック, 2.1 正常系処理, 2.2 対象データ存在チェック, 2.2.3 論理削除済みデータ
    """

    def _make_validate_conn(self, org_ids_found, email_user_map):
        """fetchall を2呼び出し用に side_effect 設定するヘルパー
        1回目: 組織 ID リスト返却
        2回目: email/user_id ペアリスト返却
        """
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_conn.cursor.return_value.__exit__.return_value = False
        mock_cursor.fetchall.side_effect = [
            [{"organization_id": oid} for oid in org_ids_found],
            [{"email": e, "user_id": uid, "organization_id": oid} for e, (uid, oid) in email_user_map.items()],
        ]
        return mock_conn

    # -------------------------------------------------------------------------
    # 正常系
    # -------------------------------------------------------------------------

    def test_all_valid_records_returned_with_user_id(self):
        """2.1.1: ユーザーがマスタに存在し、対象組織がユーザに紐づく場合、valid_records に追加され _user_id が付与される

        実行内容: organization_master・user_master に存在するレコードを渡す
        想定結果: valid_records=[レコード], invalid_records=[], valid_records[0]["_user_id"]==42
        """
        from batch.email_notification_sender import validate_and_enrich_records

        # Arrange: バリデーション対象のレコードを生成
        records = [_make_queue_record(queue_id=1, org_id=100, emails=["user@example.com"])]
        # Arrange: 組織 ID 100 が存在し、組織ID 100 に紐づく user_id 42 が user_master に存在するようにモックを設定
        conn = self._make_validate_conn(
            org_ids_found=[100],
            email_user_map={"user@example.com": (42, 100)},
        )

        # Act: validate_and_enrich_records を呼び出す
        valid_records, invalid_records = validate_and_enrich_records(conn, records)

        # Assert: valid_records に1件のレコードが存在すること
        assert len(valid_records) == 1
        # Assert: invalid_records が空であること
        assert len(invalid_records) == 0
        # Assert: valid_records[0] に _user_id フィールドが追加され、値が 42 であること
        assert valid_records[0]["_user_id"] == 42

    def test_user_id_set_from_first_recipient_email(self):
        """3.2.1.4: _user_id には recipient_email リストの先頭アドレスに対応する user_id が設定される

        実行内容: 受信者2名（先頭 user_id=10、2番目 user_id=20）のレコードを渡す
        想定結果: valid_records[0]["_user_id"] == 10 (先頭メールの user_id)
        """
        from batch.email_notification_sender import validate_and_enrich_records

        # Arrange: 組織ID 100 が存在し、組織ID 100 に紐づく user_id 10 と 20 が user_master に存在するようにモックを設定
        records = [_make_queue_record(
            queue_id=1, org_id=100, emails=["first@example.com", "second@example.com"]
        )]
        
        # Arrange: 組織 ID 100 が存在し、組織ID 100 に紐づく user_id 10 と 20 が user_master に存在するようにモックを設定
        conn = self._make_validate_conn(
            org_ids_found=[100],
            email_user_map={"first@example.com": (10, 100), "second@example.com": (20, 100)},
        )

        # Act: validate_and_enrich_records を呼び出す
        valid_records, _ = validate_and_enrich_records(conn, records)

        # Assert
        assert valid_records[0]["_user_id"] == 10

    def test_mixed_valid_invalid_correctly_separated(self):
        """2.1.1: 有効・無効レコードが混在する場合、それぞれ正しく分類される

        実行内容: 有効 (org_id=100) と無効 (org_id=999) のレコードを渡す
        想定結果: valid_records=[queue_id=1], invalid_records=[(queue_id=2, エラー)]
        """
        from batch.email_notification_sender import validate_and_enrich_records

        # Arrange: 有効なレコード (org_id=100) と無効なレコード (org_id=999) を用意
        records = [
            _make_queue_record(queue_id=1, org_id=100, emails=["valid@example.com"]),
            _make_queue_record(queue_id=2, org_id=999, emails=["other@example.com"]),
        ]
        # Arrange: 組織 ID 100 が存在し、組織ID 100 に紐づく user_id 42 が user_master に存在するようにモックを設定
        conn = self._make_validate_conn(
            org_ids_found=[100],
            email_user_map={"valid@example.com": (42, 100)},
        )

        # Act: validate_and_enrich_records を呼び出す
        valid_records, invalid_records = validate_and_enrich_records(conn, records)

        # Assert: 有効レコードに 1件 レコードが存在すること
        assert len(valid_records) == 1
        # Assert: 無効レコードに 1件 レコードが存在すること
        assert len(invalid_records) == 1
        # Assert: 有効レコードとして保持されるレコードの queue_id が 1 であること
        assert valid_records[0]["queue_id"] == 1
        # Assert: 無効レコードとして保持されるレコードの queue_id が 2 であること
        assert invalid_records[0][0]["queue_id"] == 2

    def test_empty_records_returns_empty_lists_without_db_call(self):
        """3.1.4.2: 空のレコードリストを渡した場合、DB 問い合わせを行わず ([], []) を返す

        実行内容: 空リストを渡して validate_and_enrich_records を呼び出す
        想定結果: ([], []) が返される、conn.cursor() が呼ばれない
        """
        from batch.email_notification_sender import validate_and_enrich_records

        # Arrange: DB コネクションのモックを用意
        mock_conn = MagicMock()

        # Act: 空のレコードリストを渡して validate_and_enrich_records を呼び出す
        valid_records, invalid_records = validate_and_enrich_records(mock_conn, [])

        # Assert: 有効レコードが存在しないこと
        assert valid_records == []
        # Assert: 無効レコードが存在しないこと
        assert invalid_records == []
        # Assert: DB コネクションの cursor() メソッドが呼び出されないこと
        mock_conn.cursor.assert_not_called()

    # -------------------------------------------------------------------------
    # 異常系: マスタ不整合
    # -------------------------------------------------------------------------

    def test_org_not_in_master_returns_invalid_with_error_message(self):
        """1.1.6 / 2.2.2: organization_id が organization_master に存在しない場合、invalid_records に追加される

        実行内容: 存在しない organization_id=999 のレコードを渡す
        想定結果: invalid_records=[(record, エラーメッセージ)]、エラーに "organization_id=999" と
                  "not found in organization_master" が含まれる
        """
        from batch.email_notification_sender import validate_and_enrich_records

        # Arrange
        records = [_make_queue_record(queue_id=1, org_id=999, emails=["user@example.com"])]
        conn = self._make_validate_conn(
            org_ids_found=[],
            email_user_map={"user@example.com": 42},
        )

        # Act
        valid_records, invalid_records = validate_and_enrich_records(conn, records)

        # Assert
        assert len(valid_records) == 0
        assert len(invalid_records) == 1
        _, error_msg = invalid_records[0]
        assert "organization_id=999" in error_msg
        assert "not found in organization_master" in error_msg

    def test_email_not_in_user_master_returns_invalid(self):
        """1.1.6 / 2.2.2: recipient_email が user_master に存在しない場合、invalid_records に追加される

        実行内容: user_master に存在しないメールアドレスのレコードを渡す
        想定結果: invalid_records=[(record, エラーメッセージ)]、エラーにメールアドレスと
                  "not found in user_master" が含まれる
        """
        from batch.email_notification_sender import validate_and_enrich_records

        # Arrange
        records = [_make_queue_record(queue_id=1, org_id=100, emails=["missing@example.com"])]
        conn = self._make_validate_conn(
            org_ids_found=[100],
            email_user_map={},
        )

        # Act
        valid_records, invalid_records = validate_and_enrich_records(conn, records)

        # Assert
        assert len(valid_records) == 0
        assert len(invalid_records) == 1
        _, error_msg = invalid_records[0]
        assert "missing@example.com" in error_msg
        assert "not found in user_master" in error_msg

    def test_org_delete_flag_1_treated_as_not_found(self):
        """2.2.3: delete_flag=1 の組織は WHERE 句フィルタリングにより存在チェック結果に現れず、invalid_records に追加される

        実行内容: organization_master に delete_flag=1 で登録されている組織の ID を渡す
                  （SQL の delete_flag=0 条件により空が返される想定）
        想定結果: valid_records=[], invalid_records=[(record, エラーメッセージ)]
        """
        from batch.email_notification_sender import validate_and_enrich_records

        # Arrange
        records = [_make_queue_record(queue_id=1, org_id=100, emails=["user@example.com"])]
        conn = self._make_validate_conn(
            org_ids_found=[],  # delete_flag=0 フィルタにより空
            email_user_map={"user@example.com": 42},
        )

        # Act
        valid_records, invalid_records = validate_and_enrich_records(conn, records)

        # Assert
        assert len(valid_records) == 0
        assert len(invalid_records) == 1

    def test_user_delete_flag_1_treated_as_not_found(self):
        """2.2.3: delete_flag=1 のユーザーは WHERE 句フィルタリングにより存在チェック結果に現れず、invalid_records に追加される

        実行内容: user_master に delete_flag=1 で登録されているメールアドレスのレコードを渡す
                  （SQL の delete_flag=0 条件により空が返される想定）
        想定結果: valid_records=[], invalid_records=[(record, エラーメッセージ)]
        """
        from batch.email_notification_sender import validate_and_enrich_records

        # Arrange
        records = [_make_queue_record(queue_id=1, org_id=100, emails=["deleted@example.com"])]
        conn = self._make_validate_conn(
            org_ids_found=[100],
            email_user_map={},  # delete_flag=0 フィルタにより空
        )

        # Act
        valid_records, invalid_records = validate_and_enrich_records(conn, records)

        # Assert
        assert len(valid_records) == 0
        assert len(invalid_records) == 1

    def test_partial_email_missing_in_user_master_returns_invalid(self):
        """1.1.6: recipient_emails のうち1件でも user_master に存在しない場合、invalid_records に追加される

        実行内容: 受信者2名のうち1名 (missing@example.com) が user_master に存在しない状態で渡す
        想定結果: valid_records=[], invalid_records=[(record, エラーメッセージ)]
                  エラーメッセージに "missing@example.com" が含まれる
        """
        from batch.email_notification_sender import validate_and_enrich_records

        # Arrange
        records = [_make_queue_record(
            queue_id=1, org_id=100, emails=["exists@example.com", "missing@example.com"]
        )]
        conn = self._make_validate_conn(
            org_ids_found=[100],
            email_user_map={"exists@example.com": 10},
        )

        # Act
        valid_records, invalid_records = validate_and_enrich_records(conn, records)

        # Assert
        assert len(valid_records) == 0
        assert len(invalid_records) == 1
        _, error_msg = invalid_records[0]
        assert "missing@example.com" in error_msg


# =============================================================================
# cleanup_stale_processing_records のテスト
# =============================================================================

@pytest.mark.unit
class TestCleanupStaleProcessingRecords:
    """cleanup_stale_processing_records - PROCESSING 滞留レコードの FAILED 更新
    観点: 2.1 正常系処理, 3.3 更新機能, 3.1.4.2 空結果ハンドリング, CL-1-1 フィールド網羅
    """

    # -------------------------------------------------------------------------
    # 正常系: 滞留レコードあり
    # -------------------------------------------------------------------------

    def test_stale_records_exist_triggers_update_and_commit(self):
        """2.1.1 / 3.3.1.1: 15分以上滞留した PROCESSING レコードが存在する場合、FAILED への UPDATE と commit が実行される

        実行内容: fetchone() が {"cnt": 3} を返す設定で cleanup_stale_processing_records を呼び出す
        想定結果: cursor.execute が2回呼ばれ (SELECT COUNT + UPDATE)、conn.commit が1回呼ばれる
        """
        from batch.email_notification_sender import cleanup_stale_processing_records

        # Arrange
        mock_conn, mock_cursor = _make_conn_mock(fetchone_result={"cnt": 3})

        # Act
        cleanup_stale_processing_records(mock_conn)

        # Assert
        assert mock_cursor.execute.call_count == 2
        mock_conn.commit.assert_called_once()

    def test_stale_records_update_sets_correct_status_and_fields(self):
        """3.3.1.4 / CL-1-1: UPDATE の SQL が status='FAILED', processed_time=NOW(), update_date=NOW() を含む（フィールド網羅）

        実行内容: fetchone() が {"cnt": 1} を返す設定で cleanup_stale_processing_records を呼び出す
        想定結果: 2回目の execute 呼び出しの SQL に "status = 'FAILED'"、
                  "processed_time = NOW()"、"update_date = NOW()" が含まれる
        """
        from batch.email_notification_sender import cleanup_stale_processing_records

        # Arrange
        mock_conn, mock_cursor = _make_conn_mock(fetchone_result={"cnt": 1})

        # Act
        cleanup_stale_processing_records(mock_conn)

        # Assert
        update_sql = mock_cursor.execute.call_args_list[1][0][0]
        assert "status = 'FAILED'" in update_sql
        assert "processed_time = NOW()" in update_sql
        assert "update_date = NOW()" in update_sql
        assert "status = 'PROCESSING'" in update_sql

    def test_stale_threshold_is_15_minutes(self):
        """3.3.1.4: 滞留判定の閾値として INTERVAL %s MINUTE のパラメータに 15 が渡される

        実行内容: fetchone() が {"cnt": 1} を返す設定で cleanup_stale_processing_records を呼び出す
        想定結果: SELECT COUNT・UPDATE の両クエリのパラメータとして (15,) が渡される
        """
        from batch.email_notification_sender import cleanup_stale_processing_records

        # Arrange
        mock_conn, mock_cursor = _make_conn_mock(fetchone_result={"cnt": 1})

        # Act
        cleanup_stale_processing_records(mock_conn)

        # Assert
        select_params = mock_cursor.execute.call_args_list[0][0][1]
        assert select_params == (15,)
        update_params = mock_cursor.execute.call_args_list[1][0][1]
        assert update_params == (15,)

    # -------------------------------------------------------------------------
    # 正常系: 滞留レコードなし
    # -------------------------------------------------------------------------

    def test_no_stale_records_skips_update_and_commit(self):
        """3.1.4.2: 滞留レコードが0件の場合、UPDATE は実行されず commit も呼ばれない

        実行内容: fetchone() が {"cnt": 0} を返す設定で cleanup_stale_processing_records を呼び出す
        想定結果: cursor.execute が1回のみ呼ばれ (SELECT COUNT のみ)、conn.commit は呼ばれない
        """
        from batch.email_notification_sender import cleanup_stale_processing_records

        # Arrange
        mock_conn, mock_cursor = _make_conn_mock(fetchone_result={"cnt": 0})

        # Act
        cleanup_stale_processing_records(mock_conn)

        # Assert
        assert mock_cursor.execute.call_count == 1
        mock_conn.commit.assert_not_called()


# =============================================================================
# process_email_queue のテスト
# =============================================================================

@pytest.mark.unit
class TestProcessEmailQueue:
    """process_email_queue - メール送信キューのメイン処理オーケストレーション
    観点: 2.1 正常系処理, 3.1.3 件数制御, 3.1.4.2 空結果ハンドリング,
          3.3 更新機能, 3.2 登録機能, CL-1-1 フィールド網羅

    # TODO: 設計書フローチャートに「当日の FAILED 件数が100件超過時の Teams 通知」が記載されているが、
    #       job-specification.md の実装コードには当該ロジックが含まれていない。要確認。
    """

    def _setup_conn_mock(self, mock_connect, pending_records):
        """pymysql.connect のモックと cursor モックをセットアップするヘルパー"""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.__enter__ = MagicMock(return_value=mock_conn)
        mock_conn.__exit__ = MagicMock(return_value=False)
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_conn.cursor.return_value.__exit__.return_value = False
        mock_cursor.fetchall.return_value = pending_records
        mock_connect.return_value = mock_conn
        return mock_conn, mock_cursor

    # -------------------------------------------------------------------------
    # 早期終了パターン
    # -------------------------------------------------------------------------

    @patch("pymysql.connect")
    @patch(f"{MODULE}.cleanup_stale_processing_records")
    def test_no_pending_records_exits_early_without_bulk_send(
        self, mock_cleanup, mock_connect
    ):
        """3.1.4.2: PENDING レコードが0件の場合、バルク送信が実行されず早期終了する

        実行内容: fetchall() が空リストを返す設定で process_email_queue を呼び出す
        想定結果: send_emails_bulk は呼ばれない
        """
        from batch.email_notification_sender import process_email_queue

        # Arrange
        self._setup_conn_mock(mock_connect, pending_records=[])

        # Act
        with patch(f"{MODULE}.send_emails_bulk") as mock_bulk:
            process_email_queue()

        # Assert
        mock_bulk.assert_not_called()

    @patch("pymysql.connect")
    @patch(f"{MODULE}.cleanup_stale_processing_records")
    @patch(f"{MODULE}.validate_and_enrich_records")
    def test_all_invalid_records_exits_after_failed_update(
        self, mock_validate, mock_cleanup, mock_connect
    ):
        """2.2.2: 全レコードが無効の場合、FAILED 更新後にバルク送信を行わず終了する

        実行内容: validate_and_enrich_records が ([], [(record, エラー)]) を返す設定で呼び出す
        想定結果: send_emails_bulk は呼ばれない
        """
        from batch.email_notification_sender import process_email_queue

        # Arrange
        pending = [_make_queue_record(queue_id=1)]
        mock_conn, mock_cursor = self._setup_conn_mock(mock_connect, pending)
        mock_validate.return_value = ([], [(pending[0], "org not found")])

        # Act
        with patch(f"{MODULE}.send_emails_bulk") as mock_bulk:
            process_email_queue()

        # Assert
        mock_bulk.assert_not_called()

    # -------------------------------------------------------------------------
    # フィールド網羅: 無効レコード FAILED 更新
    # -------------------------------------------------------------------------

    @patch("pymysql.connect")
    @patch(f"{MODULE}.cleanup_stale_processing_records")
    @patch(f"{MODULE}.validate_and_enrich_records")
    def test_invalid_records_update_sets_failed_with_all_fields(
        self, mock_validate, mock_cleanup, mock_connect
    ):
        """3.3.1.4 / CL-1-1: 無効レコードの UPDATE が status='FAILED', error_message, processed_time, update_date を含む

        実行内容: 1件の無効レコードを渡す
        想定結果: FAILED UPDATE の SQL に error_message=%s, processed_time=NOW(), update_date=NOW() が含まれる
        """
        from batch.email_notification_sender import process_email_queue

        # Arrange
        pending = [_make_queue_record(queue_id=1)]
        mock_conn, mock_cursor = self._setup_conn_mock(mock_connect, pending)
        mock_validate.return_value = ([], [(pending[0], "organization_id=999 not found in organization_master")])

        # Act
        with patch(f"{MODULE}.send_emails_bulk"):
            process_email_queue()

        # Assert
        execute_calls = mock_cursor.execute.call_args_list
        failed_updates = [c for c in execute_calls
                          if "status = 'FAILED'" in str(c[0][0] if c[0] else "")
                          and "error_message" in str(c[0][0] if c[0] else "")]
        assert len(failed_updates) >= 1
        update_sql = failed_updates[0][0][0]
        assert "error_message = %s" in update_sql
        assert "processed_time = NOW()" in update_sql
        assert "update_date = NOW()" in update_sql

    # -------------------------------------------------------------------------
    # PROCESSING 更新
    # -------------------------------------------------------------------------

    @patch("pymysql.connect")
    @patch(f"{MODULE}.cleanup_stale_processing_records")
    @patch(f"{MODULE}.validate_and_enrich_records")
    @patch(f"{MODULE}.send_emails_bulk")
    def test_valid_records_updated_to_processing_before_send(
        self, mock_bulk, mock_validate, mock_cleanup, mock_connect
    ):
        """3.3.1.1: 有効レコードのステータスがバルク送信前に PROCESSING へ更新される

        実行内容: 有効レコード1件で process_email_queue を呼び出す
        想定結果: status='PROCESSING' の UPDATE が実行される（update_date=NOW() 含む）
        """
        from batch.email_notification_sender import process_email_queue

        # Arrange
        pending = [_make_queue_record(queue_id=1)]
        pending[0]["_user_id"] = 42
        mock_conn, mock_cursor = self._setup_conn_mock(mock_connect, pending)
        mock_validate.return_value = (pending, [])
        mock_bulk.return_value = {1: (True, None)}

        # Act
        process_email_queue()

        # Assert
        execute_calls = mock_cursor.execute.call_args_list
        processing_calls = [c for c in execute_calls
                            if "status = 'PROCESSING'" in str(c[0][0] if c[0] else "")]
        assert len(processing_calls) == 1
        assert "update_date = NOW()" in processing_calls[0][0][0]

    # -------------------------------------------------------------------------
    # 送信成功パス
    # -------------------------------------------------------------------------

    @patch("pymysql.connect")
    @patch(f"{MODULE}.cleanup_stale_processing_records")
    @patch(f"{MODULE}.validate_and_enrich_records")
    @patch(f"{MODULE}.send_emails_bulk")
    def test_success_updates_status_to_sent_with_correct_fields(
        self, mock_bulk, mock_validate, mock_cleanup, mock_connect
    ):
        """3.3.1.4 / CL-1-1: 送信成功時の UPDATE が status='SENT', processed_time=NOW(), update_date=NOW() を含む

        実行内容: send_emails_bulk が (True, None) を返す設定で process_email_queue を呼び出す
        想定結果: SENT への UPDATE SQL に processed_time=NOW(), update_date=NOW() が含まれる
        """
        from batch.email_notification_sender import process_email_queue

        # Arrange
        pending = [_make_queue_record(queue_id=1)]
        pending[0]["_user_id"] = 42
        mock_conn, mock_cursor = self._setup_conn_mock(mock_connect, pending)
        mock_validate.return_value = (pending, [])
        mock_bulk.return_value = {1: (True, None)}

        # Act
        process_email_queue()

        # Assert
        execute_calls = mock_cursor.execute.call_args_list
        sent_calls = [c for c in execute_calls
                      if "status = 'SENT'" in str(c[0][0] if c[0] else "")]
        assert len(sent_calls) == 1
        sent_sql = sent_calls[0][0][0]
        assert "processed_time = NOW()" in sent_sql
        assert "update_date = NOW()" in sent_sql

    @patch("pymysql.connect")
    @patch(f"{MODULE}.cleanup_stale_processing_records")
    @patch(f"{MODULE}.validate_and_enrich_records")
    @patch(f"{MODULE}.send_emails_bulk")
    def test_success_inserts_mail_history_with_all_required_fields(
        self, mock_bulk, mock_validate, mock_cleanup, mock_connect
    ):
        """3.2.1.4 / CL-1-1: 送信成功時に mail_history へ INSERT が実行され、全必須フィールドが含まれる（フィールド網羅）

        実行内容: send_emails_bulk が (True, None) を返す設定で process_email_queue を呼び出す
        想定結果: INSERT INTO mail_history に mail_history_uuid, mail_type, sender_email,
                  recipients, subject, body, user_id, organization_id, creator が含まれる
        """
        from batch.email_notification_sender import (
            process_email_queue, ALERT_MAIL_TYPE_ID, SYSTEM_USER_ID, SENDGRID_CONFIG
        )

        # Arrange
        pending = [_make_queue_record(queue_id=1, org_id=100)]
        pending[0]["_user_id"] = 42
        mock_conn, mock_cursor = self._setup_conn_mock(mock_connect, pending)
        mock_validate.return_value = (pending, [])
        mock_bulk.return_value = {1: (True, None)}

        # Act
        process_email_queue()

        # Assert
        execute_calls = mock_cursor.execute.call_args_list
        insert_calls = [c for c in execute_calls
                        if "INSERT INTO mail_history" in str(c[0][0] if c[0] else "")]
        assert len(insert_calls) == 1
        insert_sql = insert_calls[0][0][0]
        insert_params = insert_calls[0][0][1]

        # SQL フィールド網羅
        for field in ["mail_history_uuid", "mail_type", "sender_email", "recipients",
                      "subject", "body", "user_id", "organization_id", "creator"]:
            assert field in insert_sql, f"フィールド '{field}' が INSERT SQL に含まれていない"

        # パラメータ値の確認
        assert ALERT_MAIL_TYPE_ID in insert_params
        assert SENDGRID_CONFIG["from_address"] in insert_params
        assert SYSTEM_USER_ID in insert_params
        assert 42 in insert_params       # _user_id
        assert 100 in insert_params      # organization_id

    # -------------------------------------------------------------------------
    # 送信失敗パス（リトライ・FAILED）
    # -------------------------------------------------------------------------

    @patch("pymysql.connect")
    @patch(f"{MODULE}.cleanup_stale_processing_records")
    @patch(f"{MODULE}.validate_and_enrich_records")
    @patch(f"{MODULE}.send_emails_bulk")
    def test_send_failure_retry_available_sets_pending_with_incremented_count(
        self, mock_bulk, mock_validate, mock_cleanup, mock_connect
    ):
        """3.3.1.4: 送信失敗かつ new_retry_count < MAX_RETRY_COUNT の場合、
        status=PENDING, retry_count++, error_message, processed_time, update_date が更新される

        実行内容: retry_count=0 のレコードで送信失敗 (False) が返る設定で呼び出す
        想定結果: PENDING への UPDATE に retry_count=1, error_message, processed_time, update_date が含まれる
        """
        from batch.email_notification_sender import process_email_queue

        # Arrange
        pending = [_make_queue_record(queue_id=1, retry_count=0)]
        pending[0]["_user_id"] = 42
        mock_conn, mock_cursor = self._setup_conn_mock(mock_connect, pending)
        mock_validate.return_value = (pending, [])
        mock_bulk.return_value = {1: (False, "connection error")}

        # Act
        process_email_queue()

        # Assert
        execute_calls = mock_cursor.execute.call_args_list
        retry_calls = [c for c in execute_calls
                       if "status = 'PENDING'" in str(c[0][0] if c[0] else "")
                       and "retry_count" in str(c[0][0] if c[0] else "")]
        assert len(retry_calls) == 1
        retry_sql = retry_calls[0][0][0]
        retry_params = retry_calls[0][0][1]
        assert "retry_count = %s" in retry_sql
        assert "error_message = %s" in retry_sql
        assert "processed_time = NOW()" in retry_sql
        assert "update_date = NOW()" in retry_sql
        assert retry_params[0] == 1  # new_retry_count (0+1)

    @patch("pymysql.connect")
    @patch(f"{MODULE}.cleanup_stale_processing_records")
    @patch(f"{MODULE}.validate_and_enrich_records")
    @patch(f"{MODULE}.send_emails_bulk")
    def test_send_failure_max_retry_exceeded_sets_failed_status(
        self, mock_bulk, mock_validate, mock_cleanup, mock_connect
    ):
        """3.3.1.4: 送信失敗かつ new_retry_count >= MAX_RETRY_COUNT の場合、status=FAILED に更新される

        実行内容: retry_count=2 (MAX_RETRY_COUNT-1) のレコードで送信失敗が返る設定で呼び出す
        想定結果: FAILED への UPDATE が実行される (retry_count=3, error_message 含む)
        """
        from batch.email_notification_sender import process_email_queue, MAX_RETRY_COUNT

        # Arrange
        pending = [_make_queue_record(queue_id=1, retry_count=MAX_RETRY_COUNT - 1)]
        pending[0]["_user_id"] = 42
        mock_conn, mock_cursor = self._setup_conn_mock(mock_connect, pending)
        mock_validate.return_value = (pending, [])
        mock_bulk.return_value = {1: (False, "connection error")}

        # Act
        process_email_queue()

        # Assert
        execute_calls = mock_cursor.execute.call_args_list
        failed_calls = [c for c in execute_calls
                        if "status = 'FAILED'" in str(c[0][0] if c[0] else "")
                        and "retry_count" in str(c[0][0] if c[0] else "")]
        assert len(failed_calls) == 1
        assert failed_calls[0][0][1][0] == MAX_RETRY_COUNT  # new_retry_count

    # -------------------------------------------------------------------------
    # 件数制御・実行順序
    # -------------------------------------------------------------------------

    @patch("pymysql.connect")
    @patch(f"{MODULE}.cleanup_stale_processing_records")
    def test_batch_size_limit_100_applied_to_pending_query(
        self, mock_cleanup, mock_connect
    ):
        """3.1.3.1: PENDING レコード取得時に MAX_BATCH_SIZE=100 の LIMIT が適用される

        実行内容: fetchall() が空リストを返す設定で process_email_queue を呼び出す
        想定結果: SELECT 文のパラメータとして MAX_BATCH_SIZE (100) が渡される
        """
        from batch.email_notification_sender import process_email_queue, MAX_BATCH_SIZE

        # Arrange
        mock_conn, mock_cursor = self._setup_conn_mock(mock_connect, pending_records=[])

        # Act
        process_email_queue()

        # Assert
        select_calls = [c for c in mock_cursor.execute.call_args_list
                        if "LIMIT" in str(c[0][0] if c[0] else "")]
        assert len(select_calls) >= 1
        limit_params = select_calls[0][0][1]
        assert MAX_BATCH_SIZE in limit_params

    @patch("pymysql.connect")
    @patch(f"{MODULE}.cleanup_stale_processing_records")
    def test_cleanup_called_before_pending_fetch(
        self, mock_cleanup, mock_connect
    ):
        """2.1.1: ジョブ開始時にリカバリ処理 (cleanup_stale_processing_records) が
        PENDING レコード取得より先に実行される

        実行内容: call_order で実行順を記録して process_email_queue を呼び出す
        想定結果: mock_cleanup が cursor.fetchall() より先に呼ばれる
        """
        from batch.email_notification_sender import process_email_queue

        # Arrange
        call_order = []
        mock_conn, mock_cursor = self._setup_conn_mock(mock_connect, pending_records=[])
        mock_cleanup.side_effect = lambda conn: call_order.append("cleanup")
        mock_cursor.fetchall.side_effect = lambda: call_order.append("fetch") or []

        # Act
        process_email_queue()

        # Assert
        assert "cleanup" in call_order
        assert "fetch" in call_order
        assert call_order.index("cleanup") < call_order.index("fetch")
