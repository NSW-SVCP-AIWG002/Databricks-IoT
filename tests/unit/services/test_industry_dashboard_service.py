"""
業種別ダッシュボードサービス層 単体テスト

対象: src/services/industry_dashboard_service.py
"""

from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from src.services.industry_dashboard_service import (
    check_device_access,
    get_accessible_organizations,
    get_default_date_range,
    validate_date_range,
)


# ============================================================
# タスク2-1: get_accessible_organizations
# ============================================================

class TestGetAccessibleOrganizations:
    """get_accessible_organizations のテスト"""

    def test_returns_org_id_list(self):
        """組織IDリストが正しく返されること"""
        mock_rows = [(1,), (2,), (3,)]
        with patch("src.services.industry_dashboard_service.db") as mock_db:
            mock_db.session.query.return_value.filter.return_value.all.return_value = mock_rows
            result = get_accessible_organizations(10)
        assert result == [1, 2, 3]

    def test_returns_empty_list_when_no_rows(self):
        """該当行なし時に空リストを返すこと"""
        with patch("src.services.industry_dashboard_service.db") as mock_db:
            mock_db.session.query.return_value.filter.return_value.all.return_value = []
            result = get_accessible_organizations(10)
        assert result == []


# ============================================================
# タスク2-2: check_device_access
# ============================================================

class TestCheckDeviceAccess:
    """check_device_access のテスト"""

    def test_returns_device_when_accessible(self):
        """アクセス可能デバイスのオブジェクトを返すこと"""
        mock_device = MagicMock()
        with patch("src.services.industry_dashboard_service.db") as mock_db:
            mock_db.session.query.return_value.filter.return_value.first.return_value = mock_device
            result = check_device_access("test-uuid", [1, 2, 3])
        assert result == mock_device

    def test_returns_none_when_not_accessible(self):
        """アクセス不可の場合に None を返すこと"""
        with patch("src.services.industry_dashboard_service.db") as mock_db:
            mock_db.session.query.return_value.filter.return_value.first.return_value = None
            result = check_device_access("test-uuid", [1, 2, 3])
        assert result is None

    def test_returns_none_when_empty_org_ids(self):
        """org_ids が空リストの場合に None を返すこと"""
        result = check_device_access("test-uuid", [])
        assert result is None


# ============================================================
# タスク2-9: get_default_date_range
# ============================================================

class TestGetDefaultDateRange:
    """get_default_date_range のテスト"""

    def test_returns_dict_with_required_keys(self):
        """必須キーを含む辞書が返されること"""
        result = get_default_date_range()
        assert "search_start_datetime" in result
        assert "search_end_datetime" in result

    def test_start_is_before_end(self):
        """開始日時が終了日時より前であること"""
        result = get_default_date_range()
        start = datetime.strptime(result["search_start_datetime"], "%Y-%m-%dT%H:%M")
        end = datetime.strptime(result["search_end_datetime"], "%Y-%m-%dT%H:%M")
        assert start < end

    def test_range_is_24_hours(self):
        """差が24時間以内であること"""
        result = get_default_date_range()
        start = datetime.strptime(result["search_start_datetime"], "%Y-%m-%dT%H:%M")
        end = datetime.strptime(result["search_end_datetime"], "%Y-%m-%dT%H:%M")
        diff = (end - start).total_seconds()
        assert 23 * 3600 <= diff <= 24 * 3600 + 60


# ============================================================
# タスク2-10: validate_date_range
# ============================================================

class TestValidateDateRange:
    """validate_date_range のテスト"""

    def test_valid_range_returns_empty_errors(self):
        """正常な期間の場合にエラーなし"""
        errors = validate_date_range("2026-02-01T00:00", "2026-02-02T00:00")
        assert errors == []

    def test_invalid_format_returns_error(self):
        """不正な日時フォーマットのエラーを検出すること"""
        errors = validate_date_range("2026/02/01 00:00", "2026-02-02T00:00")
        assert len(errors) == 1
        assert "形式" in errors[0]

    def test_start_equal_to_end_returns_error(self):
        """開始 == 終了のエラーを検出すること"""
        errors = validate_date_range("2026-02-01T00:00", "2026-02-01T00:00")
        assert len(errors) == 1
        assert "開始日時" in errors[0]

    def test_start_after_end_returns_error(self):
        """開始 > 終了のエラーを検出すること"""
        errors = validate_date_range("2026-02-03T00:00", "2026-02-01T00:00")
        assert len(errors) == 1
        assert "開始日時" in errors[0]

    def test_range_over_62_days_returns_error(self):
        """62日超過のエラーを検出すること"""
        errors = validate_date_range("2026-01-01T00:00", "2026-03-10T00:00")
        assert len(errors) == 1
        assert "2ヶ月" in errors[0]

    def test_exactly_62_days_is_valid(self):
        """ちょうど62日はエラーなし"""
        errors = validate_date_range("2026-01-01T00:00", "2026-03-04T00:00")
        assert errors == []

    def test_empty_string_returns_error(self):
        """空文字列のエラーを検出すること"""
        errors = validate_date_range("", "2026-02-02T00:00")
        assert len(errors) >= 1

    def test_none_value_returns_error(self):
        """None値のエラーを検出すること"""
        errors = validate_date_range(None, "2026-02-02T00:00")
        assert len(errors) >= 1
