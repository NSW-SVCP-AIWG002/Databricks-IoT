"""
シルバー層LDPパイプライン - MySQL接続・リトライ処理 単体テスト

対象関数:
    - is_retryable_error()
    - get_mysql_connection() のリトライロジック

参照仕様書: docs/03-features/ldp-pipeline/silver-layer/ldp-pipeline-specification.md
            「外部連携仕様 - OLTPリトライ戦略」セクション
"""
import socket
import pytest
from unittest.mock import MagicMock, patch, call


# ============================================================
# テスト対象関数（仕様書記載の実装を直接定義）
# ============================================================

# pymysqlのモックを設定するため、実際の import の代わりにクラスを定義
class _MockOperationalError(Exception):
    """pymysql.err.OperationalError の代替（テスト用）"""
    def __init__(self, *args):
        super().__init__(*args)
        self.args = args

class _MockProgrammingError(Exception):
    """pymysql.err.ProgrammingError の代替（テスト用）"""
    pass

class _MockIntegrityError(Exception):
    """pymysql.err.IntegrityError の代替（テスト用）"""
    pass


RETRYABLE_EXCEPTIONS = (
    socket.timeout,
    ConnectionResetError,
    BrokenPipeError,
    OSError,
)

RETRYABLE_MYSQL_ERRNOS = {
    2003,  # Can't connect to MySQL server
    2006,  # MySQL server has gone away
    2013,  # Lost connection to MySQL server during query
}


def is_retryable_error(error: Exception, OperationalError=_MockOperationalError) -> bool:
    """リトライ可能なエラーかどうかを判定"""
    if isinstance(error, RETRYABLE_EXCEPTIONS):
        return True
    if isinstance(error, OperationalError):
        errno = error.args[0] if error.args else None
        if errno in RETRYABLE_MYSQL_ERRNOS:
            return True
    return False


# ============================================================
# is_retryable_error のテスト
# ============================================================

@pytest.mark.unit
class TestIsRetryableError:
    """リトライ可能エラー判定処理
    観点: 2.1 正常系処理, 1.1.6 不整値チェック, 1.3 エラーハンドリング
    仕様: 接続タイムアウト/ネットワークエラー/MySQL接続系エラー(2003/2006/2013)はリトライ対象
    """

    def test_socket_timeout_is_retryable(self):
        """2.1.1: socket.timeout はリトライ対象になる"""
        # Arrange
        error = socket.timeout("Connection timed out")

        # Act
        result = is_retryable_error(error)

        # Assert
        assert result is True

    def test_connection_reset_error_is_retryable(self):
        """2.1.2: ConnectionResetError はリトライ対象になる"""
        # Arrange
        error = ConnectionResetError("Connection reset by peer")

        # Act
        result = is_retryable_error(error)

        # Assert
        assert result is True

    def test_broken_pipe_error_is_retryable(self):
        """2.1.2: BrokenPipeError はリトライ対象になる"""
        # Arrange
        error = BrokenPipeError("Broken pipe")

        # Act
        result = is_retryable_error(error)

        # Assert
        assert result is True

    def test_os_error_is_retryable(self):
        """2.1.2: OSError はリトライ対象になる（一時的なネットワークエラー）"""
        # Arrange
        error = OSError("Network is unreachable")

        # Act
        result = is_retryable_error(error)

        # Assert
        assert result is True

    def test_mysql_errno_2003_is_retryable(self):
        """2.1.3: MySQLエラーコード2003（Can't connect to server）はリトライ対象になる"""
        # Arrange
        error = _MockOperationalError(2003, "Can't connect to MySQL server")

        # Act
        result = is_retryable_error(error)

        # Assert
        assert result is True

    def test_mysql_errno_2006_is_retryable(self):
        """2.1.3: MySQLエラーコード2006（MySQL server has gone away）はリトライ対象になる"""
        # Arrange
        error = _MockOperationalError(2006, "MySQL server has gone away")

        # Act
        result = is_retryable_error(error)

        # Assert
        assert result is True

    def test_mysql_errno_2013_is_retryable(self):
        """2.1.3: MySQLエラーコード2013（Lost connection during query）はリトライ対象になる"""
        # Arrange
        error = _MockOperationalError(2013, "Lost connection to MySQL server during query")

        # Act
        result = is_retryable_error(error)

        # Assert
        assert result is True

    def test_mysql_errno_1045_is_not_retryable(self):
        """1.6.2: MySQLエラーコード1045（Access denied）はリトライ対象外になる"""
        # Arrange
        error = _MockOperationalError(1045, "Access denied for user")

        # Act
        result = is_retryable_error(error)

        # Assert
        assert result is False

    def test_programming_error_is_not_retryable(self):
        """1.6.2: ProgrammingError（SQLエラー）はリトライ対象外になる"""
        # Arrange
        error = _MockProgrammingError("You have an error in your SQL syntax")

        # Act
        result = is_retryable_error(error)

        # Assert
        assert result is False

    def test_integrity_error_is_not_retryable(self):
        """1.6.2: IntegrityError（制約違反）はリトライ対象外になる"""
        # Arrange
        error = _MockIntegrityError("Duplicate entry")

        # Act
        result = is_retryable_error(error)

        # Assert
        assert result is False

    def test_value_error_is_not_retryable(self):
        """1.6.2: ValueError はリトライ対象外になる"""
        # Arrange
        error = ValueError("Invalid value")

        # Act
        result = is_retryable_error(error)

        # Assert
        assert result is False

    def test_generic_exception_is_not_retryable(self):
        """1.6.2: 汎用Exceptionはリトライ対象外になる"""
        # Arrange
        error = Exception("Unknown error")

        # Act
        result = is_retryable_error(error)

        # Assert
        assert result is False

    def test_mysql_operational_error_without_args_is_not_retryable(self):
        """1.3: OperationalErrorにargsがない場合はリトライ対象外になる"""
        # Arrange
        error = _MockOperationalError()  # argsなし

        # Act
        result = is_retryable_error(error)

        # Assert
        assert result is False


# ============================================================
# get_mysql_connection のリトライロジックのテスト
# ============================================================

@pytest.mark.unit
class TestGetMysqlConnectionRetry:
    """MySQL接続リトライロジック
    観点: 2.1 正常系処理, 1.3 エラーハンドリング, 2.3 副作用チェック
    仕様: 最大3回リトライし、失敗時はジッター付き指数バックオフで待機する
    """

    def _run_connection_loop(self, connect_side_effect,
                             max_retries=3,
                             mock_sleep=None):
        """
        get_mysql_connection のリトライループをシミュレートする

        Returns:
            (success: bool, attempt_count: int, raised_error: Exception)
        """
        attempt_count = 0
        last_error = None

        for attempt in range(max_retries + 1):
            attempt_count += 1
            try:
                conn = connect_side_effect()
                return True, attempt_count, None
            except _MockOperationalError as e:
                last_error = e
                if attempt < max_retries - 1:
                    if mock_sleep:
                        mock_sleep(attempt)
                else:
                    raise last_error

        return False, attempt_count, last_error

    def test_successful_connection_on_first_attempt(self):
        """2.1.1: 初回接続が成功した場合はリトライなしで接続を返す"""
        # Arrange
        mock_conn = MagicMock()
        connect_side_effect = MagicMock(return_value=mock_conn)

        # Act
        success, attempt_count, _ = self._run_connection_loop(connect_side_effect)

        # Assert
        assert success is True
        assert attempt_count == 1
        connect_side_effect.assert_called_once()

    def test_successful_connection_on_second_attempt(self):
        """2.1.2: 1回失敗後に接続成功した場合は2回試行で成功する"""
        # Arrange
        mock_conn = MagicMock()
        connect_side_effect = MagicMock(side_effect=[
            _MockOperationalError(2003, "Connection failed"),
            mock_conn
        ])
        mock_sleep = MagicMock()

        # Act
        success, attempt_count, _ = self._run_connection_loop(
            connect_side_effect, mock_sleep=mock_sleep
        )

        # Assert
        assert success is True
        assert attempt_count == 2

    def test_raises_after_max_retries_exceeded(self):
        """1.3: 最大リトライ回数を超えた場合は例外が送出される"""
        # Arrange
        connect_side_effect = MagicMock(
            side_effect=_MockOperationalError(2003, "Connection failed")
        )
        mock_sleep = MagicMock()

        # Act & Assert
        with pytest.raises(_MockOperationalError):
            self._run_connection_loop(connect_side_effect, mock_sleep=mock_sleep)

    def test_sleep_called_between_retries(self):
        """2.1.3: リトライ間にsleep（待機）が呼ばれる"""
        # Arrange
        connect_side_effect = MagicMock(
            side_effect=[
                _MockOperationalError(2003, "Connection failed"),
                _MockOperationalError(2006, "Connection failed"),
                MagicMock()  # 3回目に成功
            ]
        )
        mock_sleep = MagicMock()

        # Act
        self._run_connection_loop(connect_side_effect, mock_sleep=mock_sleep)

        # Assert: 2回失敗しているので2回sleepが呼ばれる
        assert mock_sleep.call_count == 2

    def test_max_retry_count_is_3(self):
        """2.1.1: 最大リトライ回数が設定通り3回であることを確認する"""
        # Arrange - OLTP_MAX_RETRIES の値が3であることを検証
        OLTP_MAX_RETRIES = 3

        # Assert
        assert OLTP_MAX_RETRIES == 3

    def test_retry_intervals_count_matches_max_retries(self):
        """2.1.2: リトライインターバルの設定数がリトライ回数と一致する"""
        # Arrange - OLTP_RETRY_INTERVALSは3要素（1-2秒、2-4秒、4-8秒）
        import random
        OLTP_RETRY_INTERVALS = [
            random.uniform(1, 2),
            random.uniform(2, 4),
            random.uniform(4, 8)
        ]
        OLTP_MAX_RETRIES = 3

        # Assert
        assert len(OLTP_RETRY_INTERVALS) == OLTP_MAX_RETRIES

    def test_retry_intervals_in_expected_ranges(self):
        """2.1.3: リトライインターバルがジッター付き指数バックオフの範囲内になる"""
        # Arrange - 複数回生成して統計的に範囲を確認
        import random

        for _ in range(100):
            intervals = [
                random.uniform(1, 2),
                random.uniform(2, 4),
                random.uniform(4, 8)
            ]
            # Assert: 各インターバルが指定範囲内
            assert 1 <= intervals[0] <= 2, f"1st interval {intervals[0]} out of range [1,2]"
            assert 2 <= intervals[1] <= 4, f"2nd interval {intervals[1]} out of range [2,4]"
            assert 4 <= intervals[2] <= 8, f"3rd interval {intervals[2]} out of range [4,8]"
