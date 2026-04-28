"""
業種別ダッシュボードサービス層 単体テスト

対象: src/iot_app/services/industry_dashboard_service.py

テスト対象関数:
  - check_device_access              タスク2-2
  - get_recent_alerts_with_count     タスク2-3
  - get_device_list_with_count       タスク2-4
  - get_latest_sensor_data           タスク2-5
  - get_device_alerts_with_count     タスク2-6
  - get_graph_data                   タスク2-7
  - export_sensor_data_csv           タスク2-8
  - get_default_date_range           タスク2-9
  - validate_date_range              タスク2-10
"""

import re
import pytest
from datetime import datetime, timedelta, timezone
from freezegun import freeze_time

# 追加: 2026-04-24
# freeze_time用 UTC固定時刻 → JST換算: 2026-04-01 12:00:00
# 62日カットオフ（JST）= 2026-01-29 12:00:00
_FROZEN_NOW_UTC = "2026-04-01 03:00:00"

_JST = timezone(timedelta(hours=9))
from unittest.mock import Mock, MagicMock, patch

from iot_app.services.industry_dashboard_service import (
    check_device_access,
    export_sensor_data_csv,
    get_default_date_range,
    get_device_alerts_with_count,
    get_device_list_with_count,
    get_graph_data,
    get_latest_sensor_data,
    get_recent_alerts_with_count,
    search_organizations_by_name,
    validate_date_range,
)


# =============================================================================
# テストヘルパー
# =============================================================================


def _mock_execute_one(mock_db, first=None, rows=None):
    """db.session.execute が1回呼ばれる関数用（check_device_access / search_organizations_by_name）"""
    result = MagicMock()
    result.first.return_value = first
    result.fetchall.return_value = rows if rows is not None else []
    mock_db.session.execute.return_value = result


def _mock_execute_two(mock_db, count=0, rows=None):
    """db.session.execute が2回呼ばれる関数用（COUNT → SELECT の2クエリ関数）"""
    count_result = MagicMock()
    count_result.__getitem__ = MagicMock(return_value=count)
    count_exec = MagicMock()
    count_exec.first.return_value = count_result
    data_exec = MagicMock()
    data_exec.fetchall.return_value = rows if rows is not None else []
    mock_db.session.execute.side_effect = [count_exec, data_exec]


def _make_mock_device(device_uuid="uuid-001", device_id=1, organization_id=1):
    """テスト用モックデバイスオブジェクトを生成"""
    device = Mock()
    device.device_uuid = device_uuid
    device.device_id = device_id
    device.device_name = "冷蔵庫1"
    device.organization_id = organization_id
    device.delete_flag = False
    return device


def _make_mock_sensor_row(**kwargs):
    """テスト用モックセンサーデータ行を生成（全カラムデフォルト値あり）"""
    return {
        "event_timestamp":                      kwargs.get("event_timestamp",                      "2026-02-27 12:00:00"),
        "external_temp":                        kwargs.get("external_temp",                        25.0),
        "set_temp_freezer_1":                   kwargs.get("set_temp_freezer_1",                   -15.0),
        "internal_sensor_temp_freezer_1":       kwargs.get("internal_sensor_temp_freezer_1",       -12.0),
        "internal_temp_freezer_1":              kwargs.get("internal_temp_freezer_1",              -11.0),
        "df_temp_freezer_1":                    kwargs.get("df_temp_freezer_1",                    -10.0),
        "condensing_temp_freezer_1":            kwargs.get("condensing_temp_freezer_1",            40.0),
        "adjusted_internal_temp_freezer_1":     kwargs.get("adjusted_internal_temp_freezer_1",     -12.5),
        "set_temp_freezer_2":                   kwargs.get("set_temp_freezer_2",                   -18.0),
        "internal_sensor_temp_freezer_2":       kwargs.get("internal_sensor_temp_freezer_2",       -17.0),
        "internal_temp_freezer_2":              kwargs.get("internal_temp_freezer_2",              -16.0),
        "df_temp_freezer_2":                    kwargs.get("df_temp_freezer_2",                    -15.0),
        "condensing_temp_freezer_2":            kwargs.get("condensing_temp_freezer_2",            42.0),
        "adjusted_internal_temp_freezer_2":     kwargs.get("adjusted_internal_temp_freezer_2",     -17.5),
        "compressor_freezer_1":                 kwargs.get("compressor_freezer_1",                 1),
        "compressor_freezer_2":                 kwargs.get("compressor_freezer_2",                 1),
        "fan_motor_1":                          kwargs.get("fan_motor_1",                          1),
        "fan_motor_2":                          kwargs.get("fan_motor_2",                          0),
        "fan_motor_3":                          kwargs.get("fan_motor_3",                          1),
        "fan_motor_4":                          kwargs.get("fan_motor_4",                          0),
        "fan_motor_5":                          kwargs.get("fan_motor_5",                          1),
        "defrost_heater_output_1":              kwargs.get("defrost_heater_output_1",              0),
        "defrost_heater_output_2":              kwargs.get("defrost_heater_output_2",              0),
    }


# =============================================================================
# 1. 表示期間バリデーション - validate_date_range()
#    観点: 1.1.4 日付形式チェック, 1.3 エラーハンドリング
# =============================================================================

@pytest.mark.unit
class TestValidateDateRange:
    """表示期間バリデーション

    観点: 1.1.4 日付形式チェック, 1.3.2 ValidationError
    対応ワークフロー仕様書:
        - デバイス詳細検索（表示期間変更）> バリデーション
        - validate_date_range(start_datetime_str, end_datetime_str)
    エラーメッセージ定義（仕様書 VAL_001〜VAL_003）:
        - VAL_001: 日時の形式が正しくありません
        - VAL_002: 開始日時は終了日時より前である必要があります
        - VAL_003: 表示期間は2ヶ月以内で指定してください
    バリデーションルール（ワークフロー仕様書 10.3 表示期間変更ボタン）:
        - 日時形式: YYYY-MM-DDTHH:MM
        - 開始日時 < 終了日時
        - 表示期間は最大2ヶ月（62日）以内
    """

    # ------------------------------------------------------------------
    # 正常系
    # ------------------------------------------------------------------

    def test_valid_range_within_62_days_returns_empty_errors(self):
        """1.4.1 / 正常系: 有効な日時範囲（1日）でエラーリストが空
        修正: 2026-04-24 freeze_time対応（62日以内バリデーション追加に伴う修正）"""
        with freeze_time(_FROZEN_NOW_UTC):
            start = "2026-03-01T00:00"
            end   = "2026-03-02T00:00"
            errors = validate_date_range(start, end)
        assert errors == []

    def test_valid_range_exactly_62_days_returns_empty_errors(self):
        """1.3.2 / 境界値: 表示期間がちょうど62日はエラーなし
        修正: 2026-04-24 freeze_time対応（62日以内バリデーション追加に伴う修正）"""
        with freeze_time(_FROZEN_NOW_UTC):
            start = "2026-02-01T00:00"  # 固定now(JST:4/1)から59日前 → 62日以内✓
            end   = "2026-04-04T00:00"  # start + 62日
            errors = validate_date_range(start, end)
        assert errors == []

    def test_exactly_61_days_is_valid(self):
        """61日はエラーなし（上限62日の境界値: 61日 < 62日）
        修正: 2026-04-24 freeze_time対応（62日以内バリデーション追加に伴う修正）"""
        with freeze_time(_FROZEN_NOW_UTC):
            errors = validate_date_range("2026-02-01T00:00", "2026-04-03T00:00")
        assert errors == []

    # ------------------------------------------------------------------
    # 日時フォーマット不正 (VAL_001)
    # ------------------------------------------------------------------

    def test_invalid_format_start_slash_separator_returns_error(self):
        """1.4.3 / VAL_001: 開始日時がスラッシュ区切り（不正形式）でエラー"""
        start = "2026/02/01 10:00"
        end   = "2026-02-02T10:00"
        errors = validate_date_range(start, end)
        assert len(errors) > 0
        assert any("形式が正しくありません" in e for e in errors)

    def test_invalid_format_end_unparseable_string_returns_error(self):
        """1.4.3 / VAL_001: 終了日時が解析不可能な文字列でエラー"""
        start = "2026-02-01T10:00"
        end   = "invalid-date-string"
        errors = validate_date_range(start, end)
        assert len(errors) > 0
        assert any("形式が正しくありません" in e for e in errors)

    def test_invalid_format_date_only_without_time_returns_error(self):
        """1.4.1 / VAL_001: 時刻部分が欠落した日付のみの形式でエラー"""
        start = "2026-02-01"
        end   = "2026-02-02T10:00"
        errors = validate_date_range(start, end)
        assert len(errors) > 0
        assert any("形式が正しくありません" in e for e in errors)

    # ------------------------------------------------------------------
    # 空文字 / None (入力なし)
    # ------------------------------------------------------------------

    def test_empty_start_datetime_returns_error(self):
        """1.1.1 / VAL_001: 開始日時が空文字の場合エラー"""
        errors = validate_date_range("", "2026-02-02T10:00")
        assert len(errors) > 0

    def test_empty_end_datetime_returns_error(self):
        """1.1.1 / VAL_001: 終了日時が空文字の場合エラー"""
        errors = validate_date_range("2026-02-01T10:00", "")
        assert len(errors) > 0

    def test_none_value_returns_error(self):
        """None値のエラーを検出すること"""
        errors = validate_date_range(None, "2026-02-02T00:00")
        assert len(errors) >= 1

    # ------------------------------------------------------------------
    # 開始 >= 終了 (VAL_002)
    # ------------------------------------------------------------------

    def test_start_equals_end_returns_error(self):
        """1.3.2 / VAL_002: 開始日時 == 終了日時のとき「前である必要があります」エラー"""
        start = "2026-02-01T10:00"
        end   = "2026-02-01T10:00"
        errors = validate_date_range(start, end)
        assert len(errors) > 0
        assert any("開始日時は終了日時より前" in e for e in errors)

    def test_start_after_end_returns_error(self):
        """1.3.2 / VAL_002: 開始日時 > 終了日時のとき「前である必要があります」エラー"""
        start = "2026-02-03T10:00"
        end   = "2026-02-01T10:00"
        errors = validate_date_range(start, end)
        assert len(errors) > 0
        assert any("開始日時は終了日時より前" in e for e in errors)

    # ------------------------------------------------------------------
    # 期間超過 62日 (VAL_003)
    # ------------------------------------------------------------------

    def test_period_over_62_days_returns_error(self):
        """1.3.2 / VAL_003: 表示期間が63日以上のとき「2ヶ月以内」エラー"""
        start = "2026-01-01T00:00"
        end   = "2026-03-05T00:00"
        errors = validate_date_range(start, end)
        assert len(errors) > 0
        assert any("2ヶ月以内" in e for e in errors)

    def test_period_62_days_1min_over_limit_returns_error(self):
        """1.3.2 / 境界値: 62日0h1mはエラー（timedelta比較のため時間込みで62日超はNG）
        修正: 2026-04-24 freeze_time対応（62日以内バリデーション追加に伴う修正）
        修正: 2026-04-27 62日0h0min超をエラーにする仕様変更に伴う修正
              start が62日以内（cutoff=2026-01-29 12:00）であることも freeze_time で担保"""
        with freeze_time(_FROZEN_NOW_UTC):
            start = "2026-01-31T23:59"  # cutoff(2026-01-29 12:00)より後 → ルックバックエラーなし
            end   = "2026-04-04T00:00"  # start + 62日0時間1分 → timedelta(days=62) 超
            errors = validate_date_range(start, end)
        assert len(errors) > 0
        assert any("2ヶ月以内" in e for e in errors)


# =============================================================================
# 2. デフォルト表示期間取得 - get_default_date_range()
#    観点: 2.1 正常系処理
# =============================================================================

@pytest.mark.unit
class TestGetDefaultDateRange:
    """デフォルト表示期間取得

    観点: 2.1 正常系処理
    対応ワークフロー仕様書:
        - デバイス詳細初期表示 > 表示期間の初期値設定
        - get_default_date_range()
    仕様:
        - 開始: 現在日時 - 24時間
        - 終了: 現在日時
        - フォーマット: YYYY-MM-DDTHH:MM
    """

    def test_returns_dict_with_required_keys(self):
        """2.1.1: 戻り値に search_start_datetime / search_end_datetime キーが存在する"""
        result = get_default_date_range()
        assert "search_start_datetime" in result
        assert "search_end_datetime" in result

    def test_end_datetime_is_close_to_now(self):
        """2.1.2: search_end_datetime が現在日時に近い（1分以内）"""
        from datetime import timezone
        _JST = timezone(timedelta(hours=9))
        before = datetime.now(_JST).replace(tzinfo=None)
        result = get_default_date_range()
        after = datetime.now(_JST).replace(tzinfo=None)
        end_dt = datetime.strptime(result["search_end_datetime"], "%Y-%m-%dT%H:%M")
        assert (
            before.replace(second=0, microsecond=0) - timedelta(seconds=30)
            <= end_dt
            <= after.replace(second=0, microsecond=0) + timedelta(seconds=30)
        )

    def test_start_datetime_is_24_hours_before_end(self):
        """2.1.2: search_start_datetime が search_end_datetime の24時間前"""
        result = get_default_date_range()
        start_dt = datetime.strptime(result["search_start_datetime"], "%Y-%m-%dT%H:%M")
        end_dt   = datetime.strptime(result["search_end_datetime"],   "%Y-%m-%dT%H:%M")
        assert end_dt - start_dt == timedelta(hours=24)

    def test_datetime_format_matches_specification(self):
        """2.1.3: 日時フォーマットが YYYY-MM-DDTHH:MM 形式（UI仕様書 10-1, 10-2 準拠）"""
        result = get_default_date_range()
        pattern = r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}$"
        assert re.match(pattern, result["search_start_datetime"]), \
            f"start_datetime format mismatch: {result['search_start_datetime']}"
        assert re.match(pattern, result["search_end_datetime"]), \
            f"end_datetime format mismatch: {result['search_end_datetime']}"

    # 追加: 2026-04-24
    def test_uses_jst_timezone_not_utc(self):
        """UTC 15:00固定時、返却値がJST翌日00:00になることを確認（UTC時刻ではないこと）
        UTC 2026-01-01 15:00:00 → JST 2026-01-02 00:00:00
        UTCをそのまま使うと end=15:00 だが、JSTなら翌日 00:00 になるため区別可能"""
        with freeze_time("2026-01-01 15:00:00"):  # UTC固定
            result = get_default_date_range()
        end_dt = datetime.strptime(result["search_end_datetime"], "%Y-%m-%dT%H:%M")
        assert end_dt == datetime(2026, 1, 2, 0, 0), \
            f"JSTの時刻（翌日 00:00）が期待されるが実際は {end_dt}（UTCの可能性）"


# =============================================================================
# 3.5 店舗名オートコンプリート - search_organizations_by_name()
#     観点: 3.1.1 検索条件指定, 3.1.2 検索条件未指定（全件相当）,
#           3.1.4 検索結果戻り値ハンドリング
# =============================================================================

@pytest.mark.unit
class TestSearchOrganizationsByName:
    """店舗名オートコンプリート

    観点: 3.1.1 検索条件指定, 3.1.2 検索条件未指定（全件相当）,
          3.1.4 検索結果戻り値ハンドリング
    対応ワークフロー仕様書:
        - 店舗モニタリング検索 > 検索条件（organization_name 部分一致）
        - search_organizations_by_name(name, user_id)
    仕様:
        - v_device_master_by_user VIEW に user_id を渡してスコープ制限
        - name が空文字の場合は全件相当（nameフィルタなし）で取得
        - 戻り値: {organization_id, organization_name} の辞書リスト
    """

    def test_returns_dict_list_with_org_id_and_name(self, mocker):
        """3.1.4.1: 戻り値が organization_id / organization_name を持つ辞書リストである"""
        mock_db = mocker.patch("iot_app.services.industry_dashboard_service.db")
        _mock_execute_one(mock_db, rows=[(1, "店舗A")])

        result = search_organizations_by_name("店舗", user_id=10)

        assert len(result) == 1
        assert result[0]["organization_id"] == 1
        assert result[0]["organization_name"] == "店舗A"

    def test_no_name_filter_when_name_is_empty(self, mocker):
        """3.1.2.1: name が空文字の場合、nameフィルタなしで全件相当クエリが実行される"""
        mock_db = mocker.patch("iot_app.services.industry_dashboard_service.db")
        _mock_execute_one(mock_db, rows=[(2, "店舗B")])

        result = search_organizations_by_name("", user_id=10)

        assert len(result) == 1
        assert result[0]["organization_name"] == "店舗B"

    def test_returns_empty_list_when_no_matching_orgs(self, mocker):
        """3.1.4.2: 条件に一致する組織が存在しない場合、空リストが返却される"""
        mock_db = mocker.patch("iot_app.services.industry_dashboard_service.db")
        _mock_execute_one(mock_db, rows=[])

        result = search_organizations_by_name("存在しない店舗", user_id=10)

        assert result == []

    def test_returns_multiple_orgs_as_list(self, mocker):
        """3.1.4.1: 複数の組織が存在する場合、全件がリストで返却される"""
        mock_db = mocker.patch("iot_app.services.industry_dashboard_service.db")
        _mock_execute_one(mock_db, rows=[(1, "店舗A"), (2, "店舗B"), (3, "店舗C")])

        result = search_organizations_by_name("店舗", user_id=10)

        assert len(result) == 3
        assert all("organization_id" in r and "organization_name" in r for r in result)

    def test_execute_called_with_user_id(self, mocker):
        """3.1.1.1: user_id が execute の params に渡される"""
        mock_db = mocker.patch("iot_app.services.industry_dashboard_service.db")
        _mock_execute_one(mock_db, rows=[])

        search_organizations_by_name("店舗", user_id=42)

        call_params = mock_db.session.execute.call_args[0][1]
        assert call_params["user_id"] == 42


# =============================================================================
# 4. デバイスアクセス権限チェック - check_device_access()
#    観点: 2.2 対象データ存在チェック, 1.3 エラーハンドリング
# =============================================================================

@pytest.mark.unit
class TestCheckDeviceAccess:
    """デバイスアクセス権限チェック

    観点: 2.2 対象データ存在チェック
    対応ワークフロー仕様書:
        - ① データスコープ制限チェック
        - check_device_access(device_uuid, user_id)
    仕様:
        - v_device_master_by_user VIEW に user_id を渡してスコープ制限
        - アクセス可能なデバイスは Row を返す、それ以外は None
    """

    def test_accessible_device_returns_device_row(self, mocker):
        """2.2.1: アクセス可能なデバイスが存在する場合、Row を返す"""
        mock_db = mocker.patch("iot_app.services.industry_dashboard_service.db")
        mock_row = Mock()
        mock_row.device_uuid = "uuid-001"
        _mock_execute_one(mock_db, first=mock_row)

        result = check_device_access("uuid-001", user_id=10)

        assert result is mock_row

    def test_device_not_accessible_returns_none(self, mocker):
        """2.2.2: アクセス範囲外のデバイスは None を返す"""
        mock_db = mocker.patch("iot_app.services.industry_dashboard_service.db")
        _mock_execute_one(mock_db, first=None)

        result = check_device_access("uuid-outside", user_id=10)

        assert result is None

    def test_nonexistent_device_uuid_returns_none(self, mocker):
        """2.2.2: 存在しない device_uuid は None を返す"""
        mock_db = mocker.patch("iot_app.services.industry_dashboard_service.db")
        _mock_execute_one(mock_db, first=None)

        result = check_device_access("uuid-nonexistent-9999", user_id=10)

        assert result is None

    def test_execute_called_with_user_id_and_device_uuid(self, mocker):
        """3.1.1.1: user_id と device_uuid が execute の params に渡される"""
        mock_db = mocker.patch("iot_app.services.industry_dashboard_service.db")
        _mock_execute_one(mock_db, first=None)

        check_device_access("uuid-001", user_id=42)

        call_params = mock_db.session.execute.call_args[0][1]
        assert call_params["user_id"] == 42
        assert call_params["device_uuid"] == "uuid-001"


# =============================================================================
# 5. アラート一覧取得 - get_recent_alerts_with_count()
#    観点: 2.1 正常系処理, 3.1 検索機能（Read）
# =============================================================================

@pytest.mark.unit
class TestGetRecentAlertsWithCount:
    """アラート一覧取得（店舗モニタリング）

    観点: 2.1 正常系処理, 3.1.1 検索条件指定, 3.1.3 ページング・件数制御,
          3.1.4 検索結果戻り値ハンドリング
    対応ワークフロー仕様書:
        - ③ アラート一覧取得
        - get_recent_alerts_with_count(search_params, user_id, page=1, per_page=10)
    仕様:
        - v_alert_history_by_user VIEW に user_id を渡してスコープ制限
        - 過去30日以内のアラート履歴を最大30件取得
        - 検索条件: organization_name（部分一致）, device_name（部分一致）
        - 戻り値: (alerts_list, total_count) のタプル
    """

    def test_returns_alert_list_and_count_tuple(self, mocker):
        """2.1.1 / 3.1.4.1: アラートリストと件数のタプルが返却される"""
        mock_alert = Mock()
        mock_alert.alert_occurrence_datetime = datetime(2026, 2, 1, 18, 45, 0)
        mock_alert.alert_name = "温度異常"
        mock_db = mocker.patch("iot_app.services.industry_dashboard_service.db")
        _mock_execute_two(mock_db, count=1, rows=[mock_alert])

        alerts, total = get_recent_alerts_with_count(
            search_params={"organization_name": "", "device_name": ""},
            user_id=10,
        )

        assert total == 1
        assert len(alerts) == 1
        assert alerts[0] is mock_alert

    def test_returns_empty_list_and_zero_count_when_no_alerts(self, mocker):
        """3.1.4.2: アラートが存在しない場合、空リストと0件が返却される"""
        mock_db = mocker.patch("iot_app.services.industry_dashboard_service.db")
        _mock_execute_two(mock_db, count=0, rows=[])

        alerts, total = get_recent_alerts_with_count(
            search_params={"organization_name": "", "device_name": ""},
            user_id=10,
        )

        assert total == 0
        assert alerts == []

    def test_max_total_30_applied(self, mocker):
        """3.1.3.1: DBに100件あっても total が30件に制限される"""
        mock_db = mocker.patch("iot_app.services.industry_dashboard_service.db")
        _mock_execute_two(mock_db, count=100, rows=[])

        _, total = get_recent_alerts_with_count(
            search_params={"organization_name": "", "device_name": ""},
            user_id=10,
        )

        assert total == 30

    def test_execute_called_with_user_id(self, mocker):
        """3.1.1.1: user_id が execute の params に渡される"""
        mock_db = mocker.patch("iot_app.services.industry_dashboard_service.db")
        _mock_execute_two(mock_db, count=0, rows=[])

        get_recent_alerts_with_count(
            search_params={"organization_name": "", "device_name": ""},
            user_id=42,
        )

        call_params = mock_db.session.execute.call_args_list[0][0][1]
        assert call_params["user_id"] == 42

    def test_order_by_alert_level_id_asc_then_alert_history_id_desc(self, mocker):
        """ソート順: al.alert_level_id ASC, v.alert_history_id DESC の順でSQLが構築される"""
        mock_db = mocker.patch("iot_app.services.industry_dashboard_service.db")
        _mock_execute_two(mock_db, count=0, rows=[])

        get_recent_alerts_with_count(
            search_params={"organization_name": "", "device_name": ""},
            user_id=10,
        )

        sql_text = str(mock_db.session.execute.call_args_list[1][0][0])
        assert "alert_level_id ASC" in sql_text
        assert "alert_history_id DESC" in sql_text
        level_pos = sql_text.find("alert_level_id ASC")
        history_pos = sql_text.find("alert_history_id DESC")
        assert level_pos < history_pos, "alert_level_id ASC が alert_history_id DESC より前に来る必要があります"

    # 追加: 2026-04-24
    def test_order_by_three_keys_status_level_history(self, mocker):
        """3キーのソート順が設計書通りであること
        第一: alert_status_id ASC（発生中が先）
        第二: alert_level_id ASC（重大が先）
        第三: alert_history_id DESC（新しい順）"""
        mock_db = mocker.patch("iot_app.services.industry_dashboard_service.db")
        _mock_execute_two(mock_db, count=0, rows=[])

        get_recent_alerts_with_count(
            search_params={"organization_name": "", "device_name": ""},
            user_id=10,
        )

        sql_text = str(mock_db.session.execute.call_args_list[1][0][0])
        assert "alert_status_id ASC" in sql_text, "alert_status_id ASC がSQLに存在しない"
        assert "alert_level_id ASC" in sql_text,  "alert_level_id ASC がSQLに存在しない"
        assert "alert_history_id DESC" in sql_text, "alert_history_id DESC がSQLに存在しない"
        status_pos  = sql_text.find("alert_status_id ASC")
        level_pos   = sql_text.find("alert_level_id ASC")
        history_pos = sql_text.find("alert_history_id DESC")
        assert status_pos < level_pos,   "第一ソート(alert_status_id ASC)が第二ソート(alert_level_id ASC)より前にない"
        assert level_pos  < history_pos, "第二ソート(alert_level_id ASC)が第三ソート(alert_history_id DESC)より前にない"


# =============================================================================
# 6. デバイス一覧取得 - get_device_list_with_count()
#    観点: 2.1 正常系処理, 3.1 検索機能（Read）, 3.1.3 ページング
# =============================================================================

@pytest.mark.unit
class TestGetDeviceListWithCount:
    """デバイス一覧取得（店舗モニタリング）

    観点: 2.1 正常系処理, 3.1.1 検索条件指定, 3.1.3 ページング・件数制御,
          3.1.4 検索結果戻り値ハンドリング
    対応ワークフロー仕様書:
        - ④ デバイス一覧取得
        - get_device_list_with_count(search_params, user_id, page, per_page)
    仕様:
        - v_device_master_by_user VIEW に user_id を渡してスコープ制限
        - 検索条件: organization_name（部分一致）, device_name（部分一致）
        - ページング: LIMIT per_page OFFSET (page-1)*per_page
        - 戻り値: (devices_list, total_count) のタプル
    """

    def test_returns_device_list_and_count_tuple(self, mocker):
        """2.1.1 / 3.1.4.1: デバイスリストと件数のタプルが返却される"""
        mock_device = _make_mock_device()
        mock_db = mocker.patch("iot_app.services.industry_dashboard_service.db")
        _mock_execute_two(mock_db, count=1, rows=[mock_device])

        devices, total = get_device_list_with_count(
            search_params={"organization_name": "", "device_name": ""},
            user_id=10,
            page=1,
            per_page=10,
        )

        assert total == 1
        assert len(devices) == 1
        assert devices[0] is mock_device

    def test_returns_empty_list_when_no_devices(self, mocker):
        """3.1.4.2: デバイスが存在しない場合、空リストと0件が返却される"""
        mock_db = mocker.patch("iot_app.services.industry_dashboard_service.db")
        _mock_execute_two(mock_db, count=0, rows=[])

        devices, total = get_device_list_with_count(
            search_params={"organization_name": "", "device_name": ""},
            user_id=10,
            page=1,
            per_page=10,
        )

        assert total == 0
        assert devices == []

    def test_page_2_offset_is_10_when_per_page_10(self, mocker):
        """3.1.3.1: page=2, per_page=10 のとき OFFSET=10 が params に含まれる"""
        mock_db = mocker.patch("iot_app.services.industry_dashboard_service.db")
        _mock_execute_two(mock_db, count=20, rows=[])

        get_device_list_with_count(
            search_params={"organization_name": "", "device_name": ""},
            user_id=10,
            page=2,
            per_page=10,
        )

        call_params = mock_db.session.execute.call_args_list[1][0][1]
        assert call_params["offset"] == 10

    def test_page_1_offset_is_0(self, mocker):
        """3.1.3.1: page=1, per_page=10 のとき OFFSET=0 が params に含まれる"""
        mock_db = mocker.patch("iot_app.services.industry_dashboard_service.db")
        _mock_execute_two(mock_db, count=5, rows=[])

        get_device_list_with_count(
            search_params={"organization_name": "", "device_name": ""},
            user_id=10,
            page=1,
            per_page=10,
        )

        call_params = mock_db.session.execute.call_args_list[1][0][1]
        assert call_params["offset"] == 0

    def test_per_page_limit_applied_to_query(self, mocker):
        """3.1.3.1: per_page=10 が params の limit に含まれる"""
        mock_db = mocker.patch("iot_app.services.industry_dashboard_service.db")
        _mock_execute_two(mock_db, count=0, rows=[])

        get_device_list_with_count(
            search_params={"organization_name": "", "device_name": ""},
            user_id=10,
            page=1,
            per_page=10,
        )

        call_params = mock_db.session.execute.call_args_list[1][0][1]
        assert call_params["limit"] == 10

    def test_execute_called_with_user_id(self, mocker):
        """3.1.1.1: user_id が execute の params に渡される"""
        mock_db = mocker.patch("iot_app.services.industry_dashboard_service.db")
        _mock_execute_two(mock_db, count=0, rows=[])

        get_device_list_with_count(
            search_params={"organization_name": "", "device_name": ""},
            user_id=42,
            page=1,
        )

        call_params = mock_db.session.execute.call_args_list[0][0][1]
        assert call_params["user_id"] == 42

    # 追加: 2026-04-24
    def test_device_status_data_joined_in_query(self, mocker):
        """device_status_data テーブルが JOIN されていること
        デバイスステータス（最終受信時刻）の取得元が device_status_data であることを保証"""
        mock_db = mocker.patch("iot_app.services.industry_dashboard_service.db")
        _mock_execute_two(mock_db, count=0, rows=[])

        get_device_list_with_count(
            search_params={"organization_name": "", "device_name": ""},
            user_id=10,
            page=1,
        )

        sql_text = str(mock_db.session.execute.call_args_list[0][0][0])
        assert "device_status_data" in sql_text, \
            "device_status_data テーブルがJOINされていない"

    # 追加: 2026-04-24
    def test_last_received_time_included_in_select(self, mocker):
        """SELECT に last_received_time が含まれていること
        デバイスステータス（最終受信時刻）が取得されることを保証"""
        mock_db = mocker.patch("iot_app.services.industry_dashboard_service.db")
        _mock_execute_two(mock_db, count=0, rows=[])

        get_device_list_with_count(
            search_params={"organization_name": "", "device_name": ""},
            user_id=10,
            page=1,
        )

        sql_text = str(mock_db.session.execute.call_args_list[1][0][0])
        assert "last_received_time" in sql_text, \
            "last_received_time が SELECT に含まれていない"


# =============================================================================
# 7. デバイス別アラート一覧取得 - get_device_alerts_with_count()
#    観点: 2.1 正常系処理, 3.1 検索機能（Read）
# =============================================================================

@pytest.mark.unit
class TestGetDeviceAlertsWithCount:
    """デバイス別アラート一覧取得（デバイス詳細画面）

    観点: 2.1 正常系処理, 3.1.1 検索条件指定, 3.1.3 ページング・件数制御,
          3.1.4 検索結果戻り値ハンドリング
    対応ワークフロー仕様書:
        - デバイス詳細初期表示 > アラート一覧取得
        - get_device_alerts_with_count(device_id, search_params, user_id)
    仕様:
        - v_alert_history_by_user VIEW に user_id を渡してスコープ制限
        - 特定デバイスのアラート履歴（過去30日以内）を最大30件取得
        - 戻り値: (alerts_list, total_count) のタプル
    """

    def test_returns_alert_list_and_count_for_specific_device(self, mocker):
        """2.1.1 / 3.1.1.1: 特定デバイスのアラートリストと件数が返却される"""
        mock_alert = Mock()
        mock_alert.alert_occurrence_datetime = datetime(2026, 2, 1, 18, 45, 0)
        mock_alert.alert_name = "温度異常"
        mock_db = mocker.patch("iot_app.services.industry_dashboard_service.db")
        _mock_execute_two(mock_db, count=1, rows=[mock_alert])

        alerts, total = get_device_alerts_with_count(
            device_id=1,
            search_params={"page": 1},
            user_id=10,
        )

        assert total == 1
        assert len(alerts) == 1

    def test_returns_empty_list_when_no_alerts_for_device(self, mocker):
        """3.1.4.2: 対象デバイスにアラートが存在しない場合、空リストが返却される"""
        mock_db = mocker.patch("iot_app.services.industry_dashboard_service.db")
        _mock_execute_two(mock_db, count=0, rows=[])

        alerts, total = get_device_alerts_with_count(
            device_id=1,
            search_params={"page": 1},
            user_id=10,
        )

        assert total == 0
        assert alerts == []

    def test_page_3_offset_is_20(self, mocker):
        """3.1.3.1: page=3, per_page=10 のとき OFFSET=20 が params に含まれる"""
        mock_db = mocker.patch("iot_app.services.industry_dashboard_service.db")
        _mock_execute_two(mock_db, count=5, rows=[])

        get_device_alerts_with_count(device_id=1, search_params={"page": 3}, user_id=10)

        call_params = mock_db.session.execute.call_args_list[1][0][1]
        assert call_params["offset"] == 20

    def test_default_page_is_1(self, mocker):
        """page パラメータがない場合に page=1（OFFSET=0）として動作すること"""
        mock_db = mocker.patch("iot_app.services.industry_dashboard_service.db")
        _mock_execute_two(mock_db, count=0, rows=[])

        get_device_alerts_with_count(device_id=1, search_params={}, user_id=10)

        call_params = mock_db.session.execute.call_args_list[1][0][1]
        assert call_params["offset"] == 0

    def test_execute_called_with_device_id_and_user_id(self, mocker):
        """3.1.1.1: device_id と user_id が execute の params に渡される"""
        mock_db = mocker.patch("iot_app.services.industry_dashboard_service.db")
        _mock_execute_two(mock_db, count=0, rows=[])

        get_device_alerts_with_count(device_id=42, search_params={"page": 1}, user_id=99)

        call_params = mock_db.session.execute.call_args_list[0][0][1]
        assert call_params["device_id"] == 42
        assert call_params["user_id"] == 99

    def test_order_by_alert_level_id_asc_then_alert_history_id_desc(self, mocker):
        """ソート順: al.alert_level_id ASC, v.alert_history_id DESC の順でSQLが構築される"""
        mock_db = mocker.patch("iot_app.services.industry_dashboard_service.db")
        _mock_execute_two(mock_db, count=0, rows=[])

        get_device_alerts_with_count(device_id=1, search_params={"page": 1}, user_id=10)

        sql_text = str(mock_db.session.execute.call_args_list[1][0][0])
        assert "alert_level_id ASC" in sql_text
        assert "alert_history_id DESC" in sql_text
        level_pos = sql_text.find("alert_level_id ASC")
        history_pos = sql_text.find("alert_history_id DESC")
        assert level_pos < history_pos, "alert_level_id ASC が alert_history_id DESC より前に来る必要があります"

    # 追加: 2026-04-24
    def test_order_by_three_keys_status_level_history(self, mocker):
        """3キーのソート順が設計書通りであること
        第一: alert_status_id ASC（発生中が先）
        第二: alert_level_id ASC（重大が先）
        第三: alert_history_id DESC（新しい順）"""
        mock_db = mocker.patch("iot_app.services.industry_dashboard_service.db")
        _mock_execute_two(mock_db, count=0, rows=[])

        get_device_alerts_with_count(device_id=1, search_params={"page": 1}, user_id=10)

        sql_text = str(mock_db.session.execute.call_args_list[1][0][0])
        assert "alert_status_id ASC" in sql_text,  "alert_status_id ASC がSQLに存在しない"
        assert "alert_level_id ASC" in sql_text,   "alert_level_id ASC がSQLに存在しない"
        assert "alert_history_id DESC" in sql_text, "alert_history_id DESC がSQLに存在しない"
        status_pos  = sql_text.find("alert_status_id ASC")
        level_pos   = sql_text.find("alert_level_id ASC")
        history_pos = sql_text.find("alert_history_id DESC")
        assert status_pos < level_pos,   "第一ソート(alert_status_id ASC)が第二ソート(alert_level_id ASC)より前にない"
        assert level_pos  < history_pos, "第二ソート(alert_level_id ASC)が第三ソート(alert_history_id DESC)より前にない"


# =============================================================================
# 8. 最新センサーデータ取得 - get_latest_sensor_data()
#    観点: 2.1 正常系処理, 3.1.4 検索結果戻り値ハンドリング
# =============================================================================

@pytest.mark.unit
class TestGetLatestSensorData:
    """最新センサーデータ取得（MySQL / silver_sensor_data）

    観点: 2.1 正常系処理, 3.1.4 検索結果戻り値ハンドリング
    対応ワークフロー仕様書:
        - センサー情報表示 > ② 最新センサーデータ取得
        - get_latest_sensor_data(device_id)
    仕様:
        - silver_sensor_data から device_id で絞り込み
        - event_timestamp DESC LIMIT 1 で最新1件を取得
        - 戻り値: センサーデータ行オブジェクト または None
    """

    def _setup_mock_db(self, mocker, first_return=None):
        """db.session.query(SilverSensorData) チェーンのモックを構築するヘルパー"""
        mock_db = mocker.patch("iot_app.services.industry_dashboard_service.db")
        mock_db.session.query.return_value.filter.return_value.order_by.return_value.first.return_value = first_return
        return mock_db

    def test_returns_latest_sensor_row_when_exists(self, mocker):
        """3.1.4.1: センサーデータが存在する場合、最新の1行が返却される"""
        mock_row = MagicMock()
        self._setup_mock_db(mocker, first_return=mock_row)
        result = get_latest_sensor_data(device_id=1)
        assert result is mock_row

    def test_returns_none_when_no_sensor_data(self, mocker):
        """3.1.4.2: センサーデータが存在しない場合、Noneが返却される（MySQLのみ参照）"""
        # ワークフロー仕様書「センサーデータ取得仕様」: MySQLにデータが存在しない場合はNoneを返す
        self._setup_mock_db(mocker, first_return=None)
        result = get_latest_sensor_data(device_id=999)
        assert result is None

    def test_device_id_passed_to_query(self, mocker):
        """3.1.1.1: device_id がMySQLクエリに渡される"""
        # ワークフロー仕様書「センサーデータ取得仕様」: silver_sensor_data テーブルを参照
        mock_db = self._setup_mock_db(mocker, first_return=None)
        get_latest_sensor_data(device_id=42)
        mock_db.session.query.assert_called_once()

    def test_returns_row_when_found(self):
        """センサーデータが存在する場合にRowオブジェクトを返すこと"""
        mock_row = MagicMock()
        with patch("iot_app.services.industry_dashboard_service.db") as mock_db:
            mock_db.session.query.return_value.filter.return_value.order_by.return_value.first.return_value = mock_row
            result = get_latest_sensor_data(device_id=1)
        assert result == mock_row

    def test_returns_none_when_not_found(self):
        """センサーデータが存在しない場合に None を返すこと（MySQLのみ参照）"""
        # ワークフロー仕様書「センサーデータ取得仕様」: MySQLにデータが存在しない場合はNoneを返す
        with patch("iot_app.services.industry_dashboard_service.db") as mock_db:
            mock_db.session.query.return_value.filter.return_value.order_by.return_value.first.return_value = None
            result = get_latest_sensor_data(device_id=99)
        assert result is None


# =============================================================================
# 9. グラフ用センサーデータ取得 - get_graph_data()
#    観点: 2.1 正常系処理, 3.1.1 検索条件指定, 3.1.4 検索結果戻り値ハンドリング
# =============================================================================

@pytest.mark.unit
class TestGetGraphData:
    """グラフ用センサーデータ取得（MySQL / silver_sensor_data）

    観点: 2.1 正常系処理, 3.1.1 検索条件指定, 3.1.4 検索結果戻り値ハンドリング
    対応ワークフロー仕様書:
        - ② グラフ用データ取得
        - get_graph_data(device_id, search_params)
    仕様:
        - silver_sensor_data から表示期間（BETWEEN）でフィルタした全データを取得
        - event_timestamp ASC でソート
        - 戻り値: センサーデータ行のリスト
    """

    def _default_search_params(self):
        return {
            "search_start_datetime": "2026-02-26T12:00",
            "search_end_datetime":   "2026-02-27T12:00",
        }

    def test_returns_list_of_sensor_rows(self, mocker):
        """3.1.4.1: 期間内のセンサーデータリストが返却される"""
        mock_rows = [_make_mock_sensor_row() for _ in range(3)]
        mocker.patch(
            "iot_app.services.industry_dashboard_service._fetch_graph_data_from_mysql",
            return_value=mock_rows,
        )
        result = get_graph_data(device_id=1, search_params=self._default_search_params())
        assert len(result) == 3

    def test_returns_empty_list_when_no_data_in_period(self, mocker):
        """3.1.4.2: 期間内にデータがない場合、空リストが返却される"""
        mocker.patch(
            "iot_app.services.industry_dashboard_service._fetch_graph_data_from_mysql",
            return_value=[],
        )
        result = get_graph_data(device_id=1, search_params=self._default_search_params())
        assert result == []

    def test_search_start_and_end_datetime_passed_to_query(self, mocker):
        """3.1.1.2: 表示期間（start/end）が _fetch_graph_data_from_mysql に渡される"""
        mock_fetch = mocker.patch(
            "iot_app.services.industry_dashboard_service._fetch_graph_data_from_mysql",
            return_value=[],
        )
        get_graph_data(device_id=1, search_params={
            "search_start_datetime": "2026-02-01T00:00",
            "search_end_datetime":   "2026-02-02T00:00",
        })
        mock_fetch.assert_called_once()

    # ------------------------------------------------------------------
    # データソース（MySQLのみ）
    # ワークフロー仕様書「センサーデータ取得仕様」:
    #   センサーデータは MySQL の silver_sensor_data テーブルのみを参照する
    # ------------------------------------------------------------------

    def test_mysql_always_called_for_valid_params(self, mocker):
        """2.1.1: 有効な検索条件のとき _fetch_graph_data_from_mysql が呼ばれる"""
        mock_mysql = mocker.patch(
            "iot_app.services.industry_dashboard_service._fetch_graph_data_from_mysql",
            return_value=[_make_mock_sensor_row()],
        )

        result = get_graph_data(device_id=1, search_params=self._default_search_params())

        mock_mysql.assert_called_once()
        assert len(result) == 1

    # Unity Catalog参照は現行仕様の対象外（ワークフロー仕様書「センサーデータ取得仕様」でMySQLのみに統一）。
    # UC参照が必要になった場合は改めてテストを追加すること。

    def test_invalid_date_format_returns_empty_list(self):
        """1.4.3 / VAL_001: 日時フォーマット不正の場合、空リストが返却される"""
        # Act
        result = get_graph_data(device_id=1, search_params={
            "search_start_datetime": "2026/02/01 00:00",
            "search_end_datetime":   "invalid-date",
        })

        # Assert
        assert result == []

    def test_missing_search_params_returns_empty_list(self):
        """3.1.1.3: search_params が空辞書の場合、空リストが返却される"""
        # Act
        result = get_graph_data(device_id=1, search_params={})

        # Assert
        assert result == []


# =============================================================================
# 10. CSVエクスポート - export_sensor_data_csv()
#     観点: 3.5 CSVエクスポート機能
# =============================================================================

@pytest.mark.unit
class TestExportSensorDataCsv:
    """センサーデータCSVエクスポート

    観点: 3.5.1 CSV生成ロジック, 3.5.2 エスケープ処理, 3.5.3 エンコーディング処理
    対応ワークフロー仕様書:
        - CSVエクスポート > 処理詳細
        - export_sensor_data_csv(device, search_params)
    仕様:
        - ヘッダー: イベント発生日時, 外気温度, 第1冷凍 設定温度 ... 防露ヒータ出力(2)
        - エンコーディング: UTF-8 BOM付き (charset=utf-8-sig)
        - Content-Type: text/csv; charset=utf-8-sig
        - Content-Disposition: attachment; filename=sensor_data_{device_uuid}_{timestamp}.csv
    """

    _EXPECTED_HEADERS = [
        "イベント発生日時",
        "外気温度",
        "第1冷凍 設定温度",
        "第1冷凍 庫内センサー温度",
        "第1冷凍 表示温度",
        "第1冷凍 DF温度",
        "第1冷凍 凝縮温度",
        "第1冷凍 微調整後庫内温度",
        "第2冷凍 設定温度",
        "第2冷凍 庫内センサー温度",
        "第2冷凍 表示温度",
        "第2冷凍 DF温度",
        "第2冷凍 凝縮温度",
        "第2冷凍 微調整後庫内温度",
        "第1冷凍 圧縮機",
        "第2冷凍 圧縮機",
        "第1ファンモータ",
        "第2ファンモータ",
        "第3ファンモータ",
        "第4ファンモータ",
        "第5ファンモータ",
        "防露ヒータ出力(1)",
        "防露ヒータ出力(2)",
    ]

    def _default_search_params(self):
        return {
            "search_start_datetime": "2026-02-26T12:00",
            "search_end_datetime":   "2026-02-27T12:00",
        }

    def _call_export(self, mocker, device=None, sensor_rows=None):
        """export_sensor_data_csv を呼び出すヘルパー"""
        if device is None:
            device = _make_mock_device()
        if sensor_rows is None:
            sensor_rows = []
        mocker.patch(
            "iot_app.services.industry_dashboard_service.get_all_sensor_data",
            return_value=sensor_rows,
        )
        return export_sensor_data_csv(device, self._default_search_params())

    # ------------------------------------------------------------------
    # 3.5.1 CSV生成ロジック
    # ------------------------------------------------------------------

    def test_header_row_contains_all_required_columns(self, mocker):
        """3.5.1.1: 定義された全カラム名がヘッダー行に出力される"""
        response = self._call_export(mocker, sensor_rows=[])
        csv_text = response.data.decode("utf-8-sig")
        first_line = csv_text.split("\n")[0]
        for header in self._EXPECTED_HEADERS:
            assert header in first_line, f"ヘッダーに '{header}' が含まれていない"

    def test_empty_data_outputs_header_only(self, mocker):
        """3.5.1.3: データ0件のとき、ヘッダー行のみ出力される"""
        response = self._call_export(mocker, sensor_rows=[])
        csv_text = response.data.decode("utf-8-sig")
        non_empty_lines = [l for l in csv_text.split("\n") if l.strip()]
        assert len(non_empty_lines) == 1

    def test_data_rows_count_matches_sensor_data_count(self, mocker):
        """3.5.1.2: データ行数がセンサーデータ件数と一致する"""
        rows = [_make_mock_sensor_row() for _ in range(3)]
        response = self._call_export(mocker, sensor_rows=rows)
        csv_text = response.data.decode("utf-8-sig")
        non_empty_lines = [l for l in csv_text.split("\n") if l.strip()]
        assert len(non_empty_lines) == 4  # ヘッダー1行 + データ3行

    def test_column_order_follows_specification(self, mocker):
        """3.5.1.4: 先頭カラムが「イベント発生日時」"""
        response = self._call_export(mocker, sensor_rows=[])
        csv_text = response.data.decode("utf-8-sig")
        first_line = csv_text.split("\n")[0]
        assert first_line.startswith("イベント発生日時")

    def test_event_timestamp_formatted_as_yyyy_mm_dd_hh_mm_ss(self, mocker):
        """3.5.1.4: event_timestamp が YYYY-MM-DD HH:MM:SS 形式で出力される"""
        row = _make_mock_sensor_row(event_timestamp="2026-02-27 12:30:00")
        response = self._call_export(mocker, sensor_rows=[row])
        csv_text = response.data.decode("utf-8-sig")
        data_line = csv_text.split("\n")[1]
        assert "2026-02-27 12:30:00" in data_line

    def test_none_sensor_value_outputs_empty_string(self, mocker):
        """3.5.1.2: センサーデータ値が None の場合、空文字で出力される"""
        row = _make_mock_sensor_row(external_temp=None)
        response = self._call_export(mocker, sensor_rows=[row])
        csv_text = response.data.decode("utf-8-sig")
        assert ",," in csv_text

    # ------------------------------------------------------------------
    # 3.5.2 エスケープ処理
    # ------------------------------------------------------------------

    def test_comma_in_data_is_escaped_with_double_quotes(self, mocker):
        """3.5.2.1: データにカンマを含む場合、ダブルクォートで囲まれる"""
        row = _make_mock_sensor_row(external_temp="25,0")
        response = self._call_export(mocker, sensor_rows=[row])
        csv_text = response.data.decode("utf-8-sig")
        assert '"25,0"' in csv_text

    def test_double_quote_in_data_is_escaped(self, mocker):
        """3.5.2.3: データに " を含む場合、"" でエスケープされる"""
        row = _make_mock_sensor_row(external_temp='val"ue')
        response = self._call_export(mocker, sensor_rows=[row])
        csv_text = response.data.decode("utf-8-sig")
        assert '"val""ue"' in csv_text

    def test_newline_in_data_is_escaped(self, mocker):
        """3.5.2.2: データに改行を含む場合、ダブルクォートで囲まれる"""
        row = _make_mock_sensor_row(external_temp="line1\nline2")
        response = self._call_export(mocker, sensor_rows=[row])
        csv_text = response.data.decode("utf-8-sig")
        assert '"line1\nline2"' in csv_text

    # ------------------------------------------------------------------
    # 3.5.3 エンコーディング処理
    # ------------------------------------------------------------------

    def test_csv_starts_with_utf8_bom(self, mocker):
        """3.5.3.1: CSVがUTF-8 BOM付き (0xEF 0xBB 0xBF) で出力される"""
        response = self._call_export(mocker, sensor_rows=[])
        assert response.data[:3] == b"\xef\xbb\xbf", \
            "CSVの先頭にUTF-8 BOMが付与されていない"

    def test_japanese_header_is_readable_with_utf8_bom(self, mocker):
        """3.5.3.2: 日本語ヘッダーがUTF-8 BOMデコードで文字化けなく読める"""
        response = self._call_export(mocker, sensor_rows=[])
        csv_text = response.data.decode("utf-8-sig")
        assert "イベント発生日時" in csv_text
        assert "防露ヒータ出力" in csv_text

    # ------------------------------------------------------------------
    # HTTPレスポンスヘッダー
    # ------------------------------------------------------------------

    def test_content_type_is_text_csv(self, mocker):
        """CSVレスポンスの Content-Type が text/csv を含む"""
        response = self._call_export(mocker, sensor_rows=[])
        assert "text/csv" in response.headers.get("Content-type", "")

    def test_content_disposition_is_attachment(self, mocker):
        """CSVレスポンスの Content-Disposition が attachment である"""
        response = self._call_export(mocker, sensor_rows=[])
        assert "attachment" in response.headers.get("Content-Disposition", "")

    def test_content_disposition_contains_device_uuid(self, mocker):
        """CSVファイル名に device_uuid が含まれる"""
        device = _make_mock_device(device_uuid="uuid-test-001")
        response = self._call_export(mocker, device=device, sensor_rows=[])
        assert "uuid-test-001" in response.headers.get("Content-Disposition", "")

    def test_content_disposition_filename_contains_timestamp(self, mocker):
        """CSVファイル名に現在日時（YYYYMMdd_HHmmss形式）が含まれる"""
        with patch("iot_app.services.industry_dashboard_service.datetime") as mock_dt:
            mock_dt.now.return_value = datetime(2026, 2, 27, 12, 0, 0)
            response = self._call_export(mocker, sensor_rows=[])
        assert "20260227_120000" in response.headers.get("Content-Disposition", "")


# =============================================================================
# 追加テスト: get_latest_sensor_data() - MySQL専用動作の確認
# =============================================================================

@pytest.mark.unit
class TestGetLatestSensorDataMysqlOnly:
    """最新センサーデータ取得 - MySQL専用動作

    観点: 3.1.4.1 正常系戻り値, 3.1.4.2 空結果, 3.1.1.1 検索条件指定
    対応ワークフロー仕様書:
        - センサーデータ取得仕様: silver_sensor_data テーブル（MySQL）のみ参照
        - MySQLにデータが存在しない場合はNoneを返す（フォールバックなし）
    仕様:
        - silver_sensor_data から device_id で絞り込み
        - event_timestamp DESC LIMIT 1 で最新1件を取得
        - データなし → None を返す（Unity Catalog への参照は行わない）
    """

    def test_mysql_returns_row_when_data_exists(self, mocker):
        """3.1.4.1: MySQLにデータあり → センサーデータ行を返す"""
        # Arrange
        mock_db = mocker.patch("iot_app.services.industry_dashboard_service.db")
        expected_row = MagicMock()
        mock_db.session.query.return_value.filter.return_value.order_by.return_value.first.return_value = expected_row

        # Act
        result = get_latest_sensor_data(device_id=1)

        # Assert: MySQLクエリの結果がそのまま返る
        assert result is expected_row

    def test_mysql_returns_none_when_no_data(self, mocker):
        """3.1.4.2: MySQLにデータなし → None を返す（フォールバックなし）"""
        # Arrange
        mock_db = mocker.patch("iot_app.services.industry_dashboard_service.db")
        mock_db.session.query.return_value.filter.return_value.order_by.return_value.first.return_value = None

        # Act
        result = get_latest_sensor_data(device_id=999)

        # Assert: None が返り、他のデータソースへの参照は行わない
        assert result is None

    def test_query_called_with_device_id(self, mocker):
        """3.1.1.1: device_id でMySQLクエリが実行される"""
        # Arrange
        mock_db = mocker.patch("iot_app.services.industry_dashboard_service.db")
        mock_db.session.query.return_value.filter.return_value.order_by.return_value.first.return_value = None

        # Act
        get_latest_sensor_data(device_id=42)

        # Assert: session.query が呼ばれる（MySQLへのクエリ発行）
        mock_db.session.query.assert_called_once()


# =============================================================================
# 追加テスト: get_recent_alerts_with_count() - organization_id 優先フィルタ
# =============================================================================

@pytest.mark.unit
class TestGetRecentAlertsOrganizationIdPriority:
    """アラート一覧取得 - organization_id / organization_name 優先度

    観点: 3.1.1.4 条件結合（organization_id が organization_name より優先）
    対応ワークフロー仕様書:
        - 店舗モニタリング検索 > 検索条件
        - organization_id が指定された場合は organization_name フィルタは使用しない
    仕様:
        - organization_id が非空 → organization_id で絞り込み（organization_name は無視）
        - organization_id が空 かつ organization_name が非空 → organization_name で部分一致
    """

    def test_organization_id_takes_priority_over_organization_name(self):
        """3.1.1.4: organization_id と organization_name が両方指定された場合、
        organization_id フィルタのみが適用される（OR条件にならない）"""
        with patch("iot_app.services.industry_dashboard_service.db") as mock_db:
            _mock_execute_two(mock_db, count=0, rows=[])

            get_recent_alerts_with_count(
                search_params={"organization_id": "1", "organization_name": "店舗A"},
                user_id=10,
            )

        sql_text = str(mock_db.session.execute.call_args_list[0][0][0])
        assert "organization_id" in sql_text

    def test_organization_name_used_when_organization_id_is_empty(self):
        """3.1.1.3: organization_id が空文字のとき organization_name フィルタが使われる"""
        with patch("iot_app.services.industry_dashboard_service.db") as mock_db:
            _mock_execute_two(mock_db, count=0, rows=[])

            get_recent_alerts_with_count(
                search_params={"organization_id": "", "organization_name": "店舗A"},
                user_id=10,
            )

        call_params = mock_db.session.execute.call_args_list[0][0][1]
        assert "organization_name" in call_params


# =============================================================================
# 追加テスト: get_device_list_with_count() - organization_id 優先フィルタ
# =============================================================================

@pytest.mark.unit
class TestGetDeviceListOrganizationIdPriority:
    """デバイス一覧取得 - organization_id / organization_name 優先度

    観点: 3.1.1.4 条件結合（organization_id が organization_name より優先）
    対応ワークフロー仕様書:
        - 店舗モニタリング検索 > 検索条件
        - organization_id が指定された場合は organization_name フィルタは使用しない
    """

    def test_organization_id_takes_priority_over_organization_name(self):
        """3.1.1.4: organization_id と organization_name が両方指定された場合、
        organization_id フィルタのみが適用される（OR条件にならない）"""
        with patch("iot_app.services.industry_dashboard_service.db") as mock_db:
            _mock_execute_two(mock_db, count=0, rows=[])

            get_device_list_with_count(
                search_params={"organization_id": "1", "organization_name": "店舗A"},
                user_id=10,
                page=1,
            )

        sql_text = str(mock_db.session.execute.call_args_list[0][0][0])
        assert "organization_id" in sql_text

    def test_organization_name_used_when_organization_id_is_empty(self):
        """3.1.1.3: organization_id が空文字のとき organization_name フィルタが使われる"""
        with patch("iot_app.services.industry_dashboard_service.db") as mock_db:
            _mock_execute_two(mock_db, count=0, rows=[])

            get_device_list_with_count(
                search_params={"organization_id": "", "organization_name": "店舗A"},
                user_id=10,
                page=1,
            )

        call_params = mock_db.session.execute.call_args_list[0][0][1]
        assert "organization_name" in call_params


# =============================================================================
# 追加テスト: get_graph_data() - MySQL専用ソート確認
# =============================================================================

@pytest.mark.unit
class TestGetGraphDataAdditional:
    """グラフ用センサーデータ取得 - 追加テスト

    観点: 2.1.1 正常系処理（ソート確認）, 3.1.4 検索結果戻り値ハンドリング
    対応ワークフロー仕様書:
        - センサーデータ取得仕様: MySQL の silver_sensor_data のみを参照
        - event_timestamp ASC でソートして返す
    """

    def test_mysql_data_is_sorted_by_event_timestamp_asc(self, mocker):
        """2.1.1: MySQLから取得したデータが event_timestamp ASC でソートされている
        （_fetch_graph_data_from_mysql が ASC ORDER BY で取得するため）"""
        # Arrange: 複数行を昇順でモック
        row_old = _make_mock_sensor_row(event_timestamp="2026-02-10 06:00:00")
        row_new = _make_mock_sensor_row(event_timestamp="2026-02-20 12:00:00")
        mocker.patch(
            "iot_app.services.industry_dashboard_service._fetch_graph_data_from_mysql",
            return_value=[row_old, row_new],
        )

        # Act
        result = get_graph_data(device_id=1, search_params={
            "search_start_datetime": "2026-02-01T00:00",
            "search_end_datetime":   "2026-02-27T00:00",
        })

        # Assert: 古い行が先、新しい行が後（ASCソート）
        assert len(result) == 2
        ts0 = str(result[0].get("event_timestamp") or "")
        ts1 = str(result[1].get("event_timestamp") or "")
        assert ts0 <= ts1, f"ソート順が正しくない: {ts0} > {ts1}"

    # Unity CatalogエラーハンドリングテストはMySQLのみの現行仕様では対象外。
    # UC参照が再導入された場合に追加すること。


# =============================================================================
# 追加テスト: get_device_alerts_with_count() - effective_limit 境界値
# =============================================================================

@pytest.mark.unit
class TestGetDeviceAlertsEffectiveLimit:
    """デバイス別アラート一覧取得 - effective_limit 境界値

    観点: 3.1.3.1 ページング・件数制御
    対応ワークフロー仕様書:
        - デバイス詳細画面 > アラート一覧取得
        - 最大30件制限: OFFSET が 30 以上になるページでは空リストを返す
    仕様:
        - _ALERT_MAX_TOTAL = 30
        - effective_limit = min(per_page, max(0, _ALERT_MAX_TOTAL - offset))
        - offset >= 30 → effective_limit = 0 → DBクエリを発行せず [] を返す
    """

    def test_page_4_with_per_page_10_returns_empty_list(self):
        """3.1.3.1: page=4, per_page=10 のとき offset=30 で effective_limit=0 → 空リスト"""
        with patch("iot_app.services.industry_dashboard_service.db") as mock_db:
            _mock_execute_two(mock_db, count=30, rows=[])

            alerts, total = get_device_alerts_with_count(
                device_id=1, search_params={"page": 4}, user_id=10
            )

        assert alerts == []
        assert total == 30

    def test_page_3_with_per_page_10_returns_last_page_data(self):
        """3.1.3.1: page=3, per_page=10 のとき offset=20 → effective_limit=10 → データ取得"""
        mock_alert = MagicMock()
        with patch("iot_app.services.industry_dashboard_service.db") as mock_db:
            _mock_execute_two(mock_db, count=30, rows=[mock_alert])

            alerts, total = get_device_alerts_with_count(
                device_id=1, search_params={"page": 3}, user_id=10
            )

        assert total == 30
        assert alerts == [mock_alert]


# =============================================================================
# 追加テスト: get_all_sensor_data() - get_graph_data への委譲確認
# =============================================================================

@pytest.mark.unit
class TestGetAllSensorData:
    """全センサーデータ取得（CSV用）- get_graph_data への委譲

    観点: 2.1.1 正常系処理
    対応ワークフロー仕様書:
        - CSVエクスポート > 処理詳細（サーバーサイド）
        - get_all_sensor_data は get_graph_data と同じデータソース切り替えロジックを適用
    仕様:
        - get_all_sensor_data(device_id, search_params) は get_graph_data に委譲する
    """

    def test_delegates_to_get_graph_data(self, mocker):
        """2.1.1: get_all_sensor_data が get_graph_data へ処理を委譲する"""
        from iot_app.services.industry_dashboard_service import get_all_sensor_data

        mock_graph_data = mocker.patch(
            "iot_app.services.industry_dashboard_service.get_graph_data",
            return_value=[_make_mock_sensor_row()],
        )
        search_params = {
            "search_start_datetime": "2026-02-26T12:00",
            "search_end_datetime":   "2026-02-27T12:00",
        }

        result = get_all_sensor_data(device_id=1, search_params=search_params)

        mock_graph_data.assert_called_once_with(1, search_params)
        assert len(result) == 1

    def test_returns_empty_list_when_no_data(self, mocker):
        """3.1.4.2: データなし時に空リストが返る"""
        from iot_app.services.industry_dashboard_service import get_all_sensor_data

        mocker.patch(
            "iot_app.services.industry_dashboard_service.get_graph_data",
            return_value=[],
        )

        result = get_all_sensor_data(device_id=1, search_params={
            "search_start_datetime": "2026-02-26T12:00",
            "search_end_datetime":   "2026-02-27T12:00",
        })

        assert result == []


# =============================================================================
# 追加: 2026-04-24
# 62日以内バリデーション — validate_date_range() 新規テスト
# 観点: 1.1.4 日付形式チェック（開始日時が現在から62日以内であること）
# =============================================================================

@pytest.mark.unit
class TestValidateDateRangeStartDateCutoff:
    """開始日時 62日以内チェック

    観点: 1.1.3 数値範囲チェック（日付範囲）, 1.3.2 ValidationError
    対応ワークフロー仕様書:
        - validate_date_range(start_datetime_str, end_datetime_str)
        - start_dt < now(JST) - 62日 → エラー
    バリデーションルール:
        - 開始日時は現在時刻（JST）から62日以内であること
        - 境界: start == cutoff はエラーなし（< であり == ではない）
    freeze_time基点: _FROZEN_NOW_UTC → JST 2026-04-01 12:00:00
        カットオフ = 2026-01-29 12:00:00（JST）
    """

    def test_start_datetime_older_than_62_days_returns_error(self):
        """1.3.1 / VAL_NEW: 開始日時が63日前の場合エラー"""
        with freeze_time(_FROZEN_NOW_UTC):
            # 固定now(JST)=2026-04-01 12:00, カットオフ=2026-01-29 12:00
            # 2026-01-28 は カットオフより1日前 → エラー
            errors = validate_date_range("2026-01-28T00:00", "2026-01-29T00:00")
        assert len(errors) > 0
        assert any("62日以内" in e for e in errors)

    def test_start_datetime_exactly_at_62day_cutoff_is_valid(self):
        """1.3.2 / VAL_NEW / 境界値: 開始日時がちょうどカットオフ（62日前）はエラーなし"""
        with freeze_time(_FROZEN_NOW_UTC):
            # カットオフ = 2026-01-29 12:00（JST）
            # start_dt < cutoff は False → エラーなし
            errors = validate_date_range("2026-01-29T12:00", "2026-01-30T12:00")
        assert errors == []

    def test_start_datetime_1min_before_cutoff_returns_error(self):
        """1.3.1 / VAL_NEW / 境界値: カットオフより1分前はエラー"""
        with freeze_time(_FROZEN_NOW_UTC):
            # 2026-01-29 11:59 < 2026-01-29 12:00（カットオフ）→ エラー
            errors = validate_date_range("2026-01-29T11:59", "2026-01-30T11:59")
        assert len(errors) > 0
        assert any("62日以内" in e for e in errors)
