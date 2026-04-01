"""
common/logger.py の単体テスト

観点: unit-test-perspectives.md
  - 1.4.2 必須項目出力
  - 1.4.4 マスキング処理

検証内容:
  - リクエストコンテキストから requestId / method / endpoint / ipAddress / userId が自動付与される
  - requestId は g.request_id 未設定時に "-" になる
  - ipAddress は X-Forwarded-For 優先、なければ remote_addr を使用する
  - userId は g.current.user_user_id 未設定時は出力しない（ログ設計書 4章）
  - リクエストコンテキスト外ではコンテキストフィールドを付与しない
  - email キーは自動マスキングされる（ローカル部先頭2文字以外を ****）
  - phone キーは自動マスキングされる（中間4桁を ****）
  - raw_email キーはマスキングされない（ログ設計書 5.2章：認証失敗調査用）
  - マスキング対象外のキーはそのまま素通りする
"""
import logging
import pytest

from iot_app.common.logger import AppLoggerAdapter, get_logger


@pytest.mark.unit
class TestAppLoggerAdapterProcess:
    """AppLoggerAdapter.process() のテスト"""

    def _make_adapter(self):
        return AppLoggerAdapter(logging.getLogger("test"), {})

    # -----------------------------------------------------------------------
    # 1.4.2 必須項目出力
    # -----------------------------------------------------------------------

    def test_adds_request_id_from_g(self, app):
        """1.4.2.1: g.request_id が設定されていれば requestId として付与される"""
        from flask import g
        adapter = self._make_adapter()

        with app.test_request_context("/test"):
            g.request_id = "test-request-id-001"
            _, kwargs = adapter.process("msg", {})

        assert kwargs["extra"]["requestId"] == "test-request-id-001"

    def test_request_id_defaults_to_dash_when_not_set(self, app):
        """1.4.2.1: g.request_id 未設定時は requestId が "-" になる"""
        adapter = self._make_adapter()

        with app.test_request_context("/test"):
            _, kwargs = adapter.process("msg", {})

        assert kwargs["extra"]["requestId"] == "-"

    def test_adds_method_and_endpoint(self, app):
        """1.4.2.3/4: method と endpoint がリクエストから付与される"""
        adapter = self._make_adapter()

        with app.test_request_context("/admin/users", method="POST"):
            _, kwargs = adapter.process("msg", {})

        assert kwargs["extra"]["method"] == "POST"
        assert kwargs["extra"]["endpoint"] == "/admin/users"

    def test_ip_address_uses_x_forwarded_for(self, app):
        """1.4.2: X-Forwarded-For ヘッダーがある場合はそちらを ipAddress に使用する"""
        adapter = self._make_adapter()

        with app.test_request_context(
            "/test", headers={"X-Forwarded-For": "203.0.113.10"}
        ):
            _, kwargs = adapter.process("msg", {})

        assert kwargs["extra"]["ipAddress"] == "203.0.113.10"

    def test_ip_address_falls_back_to_remote_addr(self, app):
        """1.4.2: X-Forwarded-For なし時は remote_addr を ipAddress に使用する"""
        adapter = self._make_adapter()

        with app.test_request_context("/test", environ_base={"REMOTE_ADDR": "127.0.0.1"}):
            _, kwargs = adapter.process("msg", {})

        assert kwargs["extra"]["ipAddress"] == "127.0.0.1"

    def test_adds_user_id_when_authenticated(self, app):
        """1.4.2.5: g.current_user.user_id が設定されていれば userId が付与される"""
        from flask import g
        adapter = self._make_adapter()

        from types import SimpleNamespace
        with app.test_request_context("/test"):
            g.current_user = SimpleNamespace(user_id=42)
            _, kwargs = adapter.process("msg", {})

        assert kwargs["extra"]["userId"] == 42

    def test_omits_user_id_when_not_authenticated(self, app):
        """1.4.2.5: g.current_user.user_id 未設定時は userId を出力しない（ログ設計書 4章）"""
        adapter = self._make_adapter()

        with app.test_request_context("/test"):
            _, kwargs = adapter.process("msg", {})

        assert "userId" not in kwargs["extra"]

    def test_no_context_fields_outside_request(self, app):
        """1.4.2: リクエストコンテキスト外ではコンテキストフィールドが付与されない"""
        adapter = self._make_adapter()

        with app.app_context():
            _, kwargs = adapter.process("msg", {})

        assert "extra" not in kwargs

    # -----------------------------------------------------------------------
    # 1.4.4 マスキング処理
    # -----------------------------------------------------------------------

    def test_email_is_masked(self, app):
        """1.4.4.1: email キーはローカル部先頭2文字以外が **** に置換される"""
        adapter = self._make_adapter()

        with app.test_request_context("/test"):
            _, kwargs = adapter.process("msg", {"extra": {"email": "yamada@example.com"}})

        assert kwargs["extra"]["email"] == "ya****@example.com"

    def test_phone_is_masked(self, app):
        """1.4.4.2: phone キーは中間4桁が **** に置換される"""
        adapter = self._make_adapter()

        with app.test_request_context("/test"):
            _, kwargs = adapter.process("msg", {"extra": {"phone": "090-1234-5678"}})

        assert kwargs["extra"]["phone"] == "090-****-5678"

    def test_raw_email_is_not_masked(self, app):
        """5.2章: raw_email キーはマスキングされない（認証失敗調査用）"""
        adapter = self._make_adapter()

        with app.test_request_context("/test"):
            _, kwargs = adapter.process(
                "msg", {"extra": {"raw_email": "unknown@external.com"}}
            )

        assert kwargs["extra"]["raw_email"] == "unknown@external.com"

    def test_non_masking_key_passes_through(self, app):
        """マスキング対象外のキーはそのまま extra に含まれる"""
        adapter = self._make_adapter()

        with app.test_request_context("/test"):
            _, kwargs = adapter.process(
                "msg", {"extra": {"service": "databricks", "duration_ms": 95}}
            )

        assert kwargs["extra"]["service"] == "databricks"
        assert kwargs["extra"]["duration_ms"] == 95
