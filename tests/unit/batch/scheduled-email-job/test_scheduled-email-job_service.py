"""
メール通知送信バッチ Service層 単体テスト

対象モジュール: batch.email_notification_sender
対象クラス/関数: cleanup_stale_processing_records, TeamsNotifier, notify_error
"""
import logging
import pytest
import requests
from unittest.mock import MagicMock, patch



# ---------------------------------------------------------------------------
# TestCleanupStaleProcessingRecords
# ---------------------------------------------------------------------------

@pytest.mark.unit
class TestCleanupStaleProcessingRecords:
    """cleanup_stale_processing_records 関数 - PROCESSING ステータスで15分以上滞留しているレコード
    のステータスをFAILEDに更新する関数の単体テスト

    観点: 2.1.1 正常系処理, 1.3.1 例外伝播, 1.4.1 ログレベル, 2.3.2 副作用チェック
    """
    
    # ------------------------------------------------------------------------------------
    # 正常系: 関数実行 → 更新対象件数を取得するクエリが実行される
    # ------------------------------------------------------------------------------------

    @patch("batch.email_notification_sender.pymysql.connect")
    def test_cleanup_stale_processing_records_check_count_query(
        self, mock_connect
    ):
        """2.1.1: PROCESSING ステータスで15分以上滞留しているレコードの件数を取得するクエリが実行される

        実行内容: mock を用いて15分以上前の PROCESSING レコードを用意し、関数を実行
        想定結果: 対象レコードの件数を取得するクエリが実行される
        """
        
        from batch.email_notification_sender import cleanup_stale_processing_records
        
        # Arrange
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_connection
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor

        # Act: cleanup_stale_processing_records を呼び出す
        cleanup_stale_processing_records(mock_connection)

        # Assert: .execute が呼び出されること
        mock_cursor.execute.assert_called_once()
        executed_query = mock_cursor.execute.call_args[0][0]
        # Assert: クエリに SELECT文 が含まれること
        assert """
            SELECT COUNT(*) as cnt
            FROM email_notification_queue
            WHERE status = 'PROCESSING'
              AND update_date < DATE_SUB(NOW(), INTERVAL 15 MINUTE)
            """ in executed_query

    # ------------------------------------------------------------------------------------
    # 正常系: 更新対象データあり → 対象レコードのステータスを FAILED に更新するクエリが実行される
    # ------------------------------------------------------------------------------------

    @patch("batch.email_notification_sender.pymysql.connect")
    def test_cleanup_stale_processing_records_check_query(
        self, mock_connect, capfd
    ):
        """2.1.1: PROCESSING ステータスで15分以上滞留しているレコードが存在する場合、ステータスが FAILED に更新される

        実行内容: mock を用いて15分以上前の PROCESSING レコードを用意し、関数を実行
        想定結果: 対象レコードのステータスを FAILED に更新するクエリが実行される
        """
        
        from batch.email_notification_sender import cleanup_stale_processing_records
        
        # Arrange
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_connection
        mock_cursor.fetchone.return_value = (1,)  # 更新対象レコードが1件存在する想定
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor

        # Act: cleanup_stale_processing_records を呼び出す
        cleanup_stale_processing_records(mock_connection)
        # Act: 標準出力をキャプチャ
        captured = capfd.readouterr()

        # Assert: 標準出力が存在すること
        assert "PROCESSING状態で" in captured.out or "経過したレコード:" in captured.out
        # Assert: .execute が呼び出されること
        mock_cursor.execute.assert_called_once()
        
        executed_query = mock_cursor.execute.call_args[0][0]
        # Assert: クエリに UPDATE文 が含まれること
        assert """UPDATE email_notification_queue
                SET status = 'FAILED',
                    processed_time = NOW(),
                    update_date = NOW()
                WHERE status = 'PROCESSING'
                  AND update_date < DATE_SUB(NOW(), INTERVAL 15 MINUTE)
                  """ in executed_query
                  
    # ------------------------------------------------------------------------------------
    # 正常系: 更新対象データあり → 対象レコードのステータスを FAILED に更新するクエリが実行、コミットされる
    # ------------------------------------------------------------------------------------
    
    @patch("batch.email_notification_sender.pymysql.connect")
    def test_cleanup_stale_processing_records_check_call_commit(
        self, mock_connect, capfd
    ):
        """2.1.1: PROCESSING ステータスで15分以上滞留しているレコードが存在する場合、ステータスが FAILED に更新される

        実行内容: mock を用いて15分以上前の PROCESSING レコードを用意し、関数を実行
        想定結果: 対象レコードのステータスを FAILED に更新するクエリが実行され、コミットされる
        """
        
        from batch.email_notification_sender import cleanup_stale_processing_records
        
        # Arrange
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_connection
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor

        # Act: cleanup_stale_processing_records を呼び出す
        cleanup_stale_processing_records(mock_connection)
        
        captured = capfd.readouterr()

        # Assert: .commit が呼び出されること
        mock_connection.commit.assert_called_once()
        # Assert: コミットは1回だけ呼び出されること
        assert mock_connection.commit.call_count == 1
        # Assert: 標準出力が存在すること
        assert "FAILED更新完了:" in captured.out
        
    # ------------------------------------------------------------------------------------
    # 正常系: 更新対象データあり → 対象レコードのステータスを FAILED に更新するクエリが実行される
    # ------------------------------------------------------------------------------------
        
    @patch("batch.email_notification_sender.pymysql.connect")
    def test_cleanup_stale_processing_records_no_stale_records(
        self, mock_connect
    ):
        """2.1.1: PROCESSING ステータスで15分以上滞留しているレコードが存在しない場合、クエリは実行されない

        実行内容: mock を用いて15分以上前の PROCESSING レコードが存在しない状態を用意し、関数を実行
        想定結果: 対象レコードのステータスを FAILED に更新するクエリは実行されない
        """
        
        from batch.email_notification_sender import cleanup_stale_processing_records
        
        # Arrange
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_connection
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor

        # Act: cleanup_stale_processing_records を呼び出す
        cleanup_stale_processing_records(mock_connection)

        # Assert: .execute が呼び出されないこと
        mock_cursor.execute.assert_not_called()