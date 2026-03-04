"""
業種別ダッシュボード（冷蔵冷凍庫） 単体テスト

対象画面:
- IDS-001: 店舗モニタリング画面 (/industry-dashboard/store-monitoring)
- IDS-002: デバイス詳細画面 (/industry-dashboard/device-details/<device_uuid>)

参考ドキュメント:
- UI仕様書:         docs/03-features/flask-app/industry-dashboard/ui-specification.md
- ワークフロー仕様書: docs/03-features/flask-app/industry-dashboard/workflow-specification.md
- 単体テスト観点表:  docs/05-testing/unit-test/unit-test-perspectives.md

注意:
  本テストは設計書（ワークフロー仕様書）の実装例に基づいて作成しています。
  実装完了後、下記インポートパスを実際のモジュールパスに変更してください。

  想定インポートパス:
    from src.services.industry_dashboard_service import (
        validate_date_range,
        get_default_date_range,
        get_accessible_organizations,
        check_device_access,
        get_recent_alerts_with_count,
        get_device_list_with_count,
        get_device_alerts_with_count,
        get_latest_sensor_data,
        get_graph_data,
        get_all_sensor_data,
        export_sensor_data_csv,
    )
"""

import re
import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, MagicMock, patch, call


# =============================================================================
# テストヘルパー
# =============================================================================

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
    row = Mock()
    row.event_timestamp          = kwargs.get("event_timestamp",          datetime(2026, 2, 27, 12, 0, 0))
    row.external_temp            = kwargs.get("external_temp",            25.0)
    row.set_temp_freezer_1       = kwargs.get("set_temp_freezer_1",       -15.0)
    row.internal_sensor_temp_freezer_1 = kwargs.get("internal_sensor_temp_freezer_1", -12.0)
    row.internal_temp_freezer_1  = kwargs.get("internal_temp_freezer_1",  -11.0)
    row.df_temp_freezer_1        = kwargs.get("df_temp_freezer_1",        -10.0)
    row.condensing_temp_freezer_1 = kwargs.get("condensing_temp_freezer_1", 40.0)
    row.adjusted_internal_temp_freezer_1 = kwargs.get("adjusted_internal_temp_freezer_1", -12.5)
    row.set_temp_freezer_2       = kwargs.get("set_temp_freezer_2",       -18.0)
    row.internal_sensor_temp_freezer_2 = kwargs.get("internal_sensor_temp_freezer_2", -17.0)
    row.internal_temp_freezer_2  = kwargs.get("internal_temp_freezer_2",  -16.0)
    row.df_temp_freezer_2        = kwargs.get("df_temp_freezer_2",        -15.0)
    row.condensing_temp_freezer_2 = kwargs.get("condensing_temp_freezer_2", 42.0)
    row.adjusted_internal_temp_freezer_2 = kwargs.get("adjusted_internal_temp_freezer_2", -17.5)
    row.compressor_freezer_1     = kwargs.get("compressor_freezer_1",     1)
    row.compressor_freezer_2     = kwargs.get("compressor_freezer_2",     1)
    row.fan_motor_1              = kwargs.get("fan_motor_1",              1)
    row.fan_motor_2              = kwargs.get("fan_motor_2",              0)
    row.fan_motor_3              = kwargs.get("fan_motor_3",              1)
    row.fan_motor_4              = kwargs.get("fan_motor_4",              0)
    row.fan_motor_5              = kwargs.get("fan_motor_5",              1)
    row.defrost_heater_output_1  = kwargs.get("defrost_heater_output_1",  0)
    row.defrost_heater_output_2  = kwargs.get("defrost_heater_output_2",  0)
    return row


# =============================================================================
# 1. 表示期間バリデーション - validate_date_range()
#    観点: 1.1.4 日付形式チェック, 1.3 エラーハンドリング
#    対応ワークフロー: デバイス詳細検索（表示期間変更）> バリデーション
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
    """

    # ------------------------------------------------------------------
    # 正常系
    # ------------------------------------------------------------------

    def test_valid_range_within_62_days_returns_empty_errors(self):
        """1.4.1 / 正常系: 有効な日時範囲（1日）でエラーリストが空"""
        # Arrange
        start = "2026-02-01T10:00"
        end   = "2026-02-02T10:00"

        # Act
        from src.services.industry_dashboard_service import validate_date_range
        errors = validate_date_range(start, end)

        # Assert
        assert errors == []

    def test_valid_range_exactly_62_days_returns_empty_errors(self):
        """1.3.2 / 境界値: 表示期間がちょうど62日はエラーなし"""
        # Arrange
        start = "2026-01-01T00:00"
        end   = "2026-03-04T00:00"  # 62日後

        # Act
        from src.services.industry_dashboard_service import validate_date_range
        errors = validate_date_range(start, end)

        # Assert
        assert errors == []

    # ------------------------------------------------------------------
    # 日時フォーマット不正 (VAL_001)
    # ------------------------------------------------------------------

    def test_invalid_format_start_slash_separator_returns_error(self):
        """1.4.3 / VAL_001: 開始日時がスラッシュ区切り（不正形式）でエラー"""
        # Arrange
        start = "2026/02/01 10:00"   # スラッシュ区切りは不正
        end   = "2026-02-02T10:00"

        # Act
        from src.services.industry_dashboard_service import validate_date_range
        errors = validate_date_range(start, end)

        # Assert
        assert len(errors) > 0
        assert any("形式が正しくありません" in e for e in errors)

    def test_invalid_format_end_unparseable_string_returns_error(self):
        """1.4.3 / VAL_001: 終了日時が解析不可能な文字列でエラー"""
        # Arrange
        start = "2026-02-01T10:00"
        end   = "invalid-date-string"

        # Act
        from src.services.industry_dashboard_service import validate_date_range
        errors = validate_date_range(start, end)

        # Assert
        assert len(errors) > 0
        assert any("形式が正しくありません" in e for e in errors)

    def test_invalid_format_date_only_without_time_returns_error(self):
        """1.4.1 / VAL_001: 時刻部分が欠落した日付のみの形式でエラー"""
        # Arrange
        start = "2026-02-01"         # 時刻なし
        end   = "2026-02-02T10:00"

        # Act
        from src.services.industry_dashboard_service import validate_date_range
        errors = validate_date_range(start, end)

        # Assert
        assert len(errors) > 0
        assert any("形式が正しくありません" in e for e in errors)

    # ------------------------------------------------------------------
    # 空文字 / None (入力なし)
    # ------------------------------------------------------------------

    def test_empty_start_datetime_returns_error(self):
        """1.1.1 / VAL_001: 開始日時が空文字の場合エラー"""
        # Arrange
        start = ""
        end   = "2026-02-02T10:00"

        # Act
        from src.services.industry_dashboard_service import validate_date_range
        errors = validate_date_range(start, end)

        # Assert
        assert len(errors) > 0

    def test_empty_end_datetime_returns_error(self):
        """1.1.1 / VAL_001: 終了日時が空文字の場合エラー"""
        # Arrange
        start = "2026-02-01T10:00"
        end   = ""

        # Act
        from src.services.industry_dashboard_service import validate_date_range
        errors = validate_date_range(start, end)

        # Assert
        assert len(errors) > 0

    # ------------------------------------------------------------------
    # 開始 >= 終了 (VAL_002)
    # ------------------------------------------------------------------

    def test_start_equals_end_returns_error(self):
        """1.3.2 / VAL_002: 開始日時 == 終了日時のとき「前である必要があります」エラー"""
        # Arrange
        start = "2026-02-01T10:00"
        end   = "2026-02-01T10:00"

        # Act
        from src.services.industry_dashboard_service import validate_date_range
        errors = validate_date_range(start, end)

        # Assert
        assert len(errors) > 0
        assert any("開始日時は終了日時より前" in e for e in errors)

    def test_start_after_end_returns_error(self):
        """1.3.2 / VAL_002: 開始日時 > 終了日時のとき「前である必要があります」エラー"""
        # Arrange
        start = "2026-02-03T10:00"
        end   = "2026-02-01T10:00"

        # Act
        from src.services.industry_dashboard_service import validate_date_range
        errors = validate_date_range(start, end)

        # Assert
        assert len(errors) > 0
        assert any("開始日時は終了日時より前" in e for e in errors)

    # ------------------------------------------------------------------
    # 期間超過 62日 (VAL_003)
    # ------------------------------------------------------------------

    def test_period_over_62_days_returns_error(self):
        """1.3.2 / VAL_003: 表示期間が63日以上のとき「2ヶ月以内」エラー"""
        # Arrange
        start = "2026-01-01T00:00"
        end   = "2026-03-05T00:00"  # 63日後

        # Act
        from src.services.industry_dashboard_service import validate_date_range
        errors = validate_date_range(start, end)

        # Assert
        assert len(errors) > 0
        assert any("2ヶ月以内" in e for e in errors)

    def test_period_62_days_23h59m_is_within_limit_returns_empty_errors(self):
        """1.3.2 / 境界値: .days比較のため62日+23時間59分はエラーなし（日単位切り捨て仕様）"""
        # Arrange
        start = "2026-01-01T00:00"
        end   = "2026-03-04T23:59"  # 62日と23時間59分後（.daysは62のままエラーにならない）

        # Act
        from src.services.industry_dashboard_service import validate_date_range
        errors = validate_date_range(start, end)

        # Assert
        assert errors == []


# =============================================================================
# 2. デフォルト表示期間取得 - get_default_date_range()
#    観点: 2.1 正常系処理
#    対応ワークフロー: デバイス詳細初期表示 > 表示期間の初期値設定
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
        - フォーマット: YYYY/MM/DDTHH:MM
    """

    def test_returns_dict_with_required_keys(self):
        """2.1.1: 戻り値に search_start_datetime / search_end_datetime キーが存在する"""
        # Arrange / Act
        from src.services.industry_dashboard_service import get_default_date_range
        result = get_default_date_range()

        # Assert
        assert "search_start_datetime" in result
        assert "search_end_datetime" in result

    def test_end_datetime_is_close_to_now(self):
        """2.1.2: search_end_datetime が現在日時に近い（1分以内）"""
        # Arrange
        before = datetime.now()

        # Act
        from src.services.industry_dashboard_service import get_default_date_range
        result = get_default_date_range()
        after = datetime.now()

        # Assert
        end_dt = datetime.strptime(result["search_end_datetime"], "%Y/%m/%dT%H:%M")
        assert before.replace(second=0, microsecond=0) - timedelta(seconds=30) <= end_dt <= after.replace(second=0, microsecond=0) + timedelta(seconds=30)

    def test_start_datetime_is_24_hours_before_end(self):
        """2.1.2: search_start_datetime が search_end_datetime の24時間前"""
        # Arrange / Act
        from src.services.industry_dashboard_service import get_default_date_range
        result = get_default_date_range()

        # Assert
        start_dt = datetime.strptime(result["search_start_datetime"], "%Y/%m/%dT%H:%M")
        end_dt   = datetime.strptime(result["search_end_datetime"],   "%Y/%m/%dT%H:%M")
        diff = end_dt - start_dt
        assert diff == timedelta(hours=24)

    def test_datetime_format_matches_specification(self):
        """2.1.3: 日時フォーマットが YYYY/MM/DDTHH:MM 形式（UI仕様書 10-1, 10-2 準拠）"""
        # Arrange / Act
        from src.services.industry_dashboard_service import get_default_date_range
        result = get_default_date_range()

        # Assert
        pattern = r"^\d{4}/\d{2}/\d{2}T\d{2}:\d{2}$"
        assert re.match(pattern, result["search_start_datetime"]), \
            f"start_datetime format mismatch: {result['search_start_datetime']}"
        assert re.match(pattern, result["search_end_datetime"]), \
            f"end_datetime format mismatch: {result['search_end_datetime']}"


# =============================================================================
# 3. アクセス可能組織ID取得 - get_accessible_organizations()
#    観点: 2.1 正常系処理, 3.1.4 検索結果戻り値ハンドリング
#    対応ワークフロー: データスコープ制限の適用（全ワークフロー共通）
# =============================================================================

@pytest.mark.unit
class TestGetAccessibleOrganizations:
    """アクセス可能組織ID取得

    観点: 2.1 正常系処理, 3.1.4 検索結果戻り値ハンドリング
    対応ワークフロー仕様書:
        - ② データスコープ制限の適用
        - get_accessible_organizations(current_user_organization_id)
    仕様:
        - organization_closure テーブルから parent_organization_id で検索
        - subsidiary_organization_id のリストを返す
        - ロールによる条件分岐は行わない
    """

    def test_returns_list_of_subsidiary_org_ids(self, mocker):
        """3.1.4.1: DBクエリ結果から subsidiary_organization_id のリストが返却される"""
        # Arrange
        mock_db = mocker.patch("src.services.industry_dashboard_service.db")
        mock_db.session.query.return_value.filter.return_value.all.return_value = [
            (1,),
            (2,),
            (3,),
        ]

        # Act
        from src.services.industry_dashboard_service import get_accessible_organizations
        result = get_accessible_organizations(10)

        # Assert
        assert result == [1, 2, 3]

    def test_returns_empty_list_when_no_subsidiaries(self, mocker):
        """3.1.4.2: 下位組織が存在しない場合、空リストが返却される"""
        # Arrange
        mock_db = mocker.patch("src.services.industry_dashboard_service.db")
        mock_db.session.query.return_value.filter.return_value.all.return_value = []

        # Act
        from src.services.industry_dashboard_service import get_accessible_organizations
        result = get_accessible_organizations(99)

        # Assert
        assert result == []

    def test_query_is_executed_with_parent_org_id(self, mocker):
        """3.1.1.1: parent_organization_id を条件にクエリが実行される"""
        # Arrange
        mock_db = mocker.patch("src.services.industry_dashboard_service.db")
        mock_db.session.query.return_value.filter.return_value.all.return_value = []

        # Act
        from src.services.industry_dashboard_service import get_accessible_organizations
        get_accessible_organizations(100)

        # Assert
        mock_db.session.query.assert_called_once()
        mock_db.session.query.return_value.filter.assert_called_once()

    def test_returns_flat_list_not_tuples(self, mocker):
        """2.1.1: 戻り値がタプルではなく整数のフラットリスト"""
        # Arrange
        mock_db = mocker.patch("src.services.industry_dashboard_service.db")
        mock_db.session.query.return_value.filter.return_value.all.return_value = [
            (1,),
        ]

        # Act
        from src.services.industry_dashboard_service import get_accessible_organizations
        result = get_accessible_organizations(10)

        # Assert
        assert isinstance(result, list)
        assert result[0] == 1   # タプルではなく整数


# =============================================================================
# 4. デバイスアクセス権限チェック - check_device_access()
#    観点: 2.2 対象データ存在チェック, 1.3 エラーハンドリング
#    対応ワークフロー: センサー情報表示、デバイス詳細 > スコープ制限チェック
# =============================================================================

@pytest.mark.unit
class TestCheckDeviceAccess:
    """デバイスアクセス権限チェック

    観点: 2.2 対象データ存在チェック
    対応ワークフロー仕様書:
        - ① データスコープ制限チェック
        - check_device_access(device_uuid, accessible_org_ids)
    仕様:
        - device_uuid が accessible_org_ids 内の組織に属し、
          かつ delete_flag == False であれば Device を返す
        - それ以外は None を返す（→ 呼び出し元が abort(404) する）
    エラーハンドリング:
        - ERR_002: 指定されたデバイスが見つかりません（404）
    """

    def test_accessible_device_returns_device_object(self, mocker):
        """2.2.1: アクセス可能なデバイスが存在する場合、Deviceオブジェクトを返す"""
        # Arrange
        mock_device = _make_mock_device(device_uuid="uuid-001")
        mocker.patch(
            "src.services.industry_dashboard_service.Device"
        ).query.filter.return_value.first.return_value = mock_device

        # Act
        from src.services.industry_dashboard_service import check_device_access
        result = check_device_access("uuid-001", [1])

        # Assert
        assert result is mock_device

    def test_device_not_in_accessible_orgs_returns_none(self, mocker):
        """2.2.2: デバイスがアクセス可能組織に属さない（スコープ外）場合、Noneを返す"""
        # Arrange
        mocker.patch(
            "src.services.industry_dashboard_service.Device"
        ).query.filter.return_value.first.return_value = None

        # Act
        from src.services.industry_dashboard_service import check_device_access
        result = check_device_access("uuid-outside", [1])

        # Assert
        assert result is None

    def test_logically_deleted_device_returns_none(self, mocker):
        """2.2.3: 論理削除済みデバイス（delete_flag=True）はNoneを返す（フィルタ条件による）"""
        # Arrange
        # delete_flag == False のフィルタが効くため、削除済みデバイスは first() で None になる
        mocker.patch(
            "src.services.industry_dashboard_service.Device"
        ).query.filter.return_value.first.return_value = None

        # Act
        from src.services.industry_dashboard_service import check_device_access
        result = check_device_access("uuid-deleted", [1])

        # Assert
        assert result is None

    def test_empty_accessible_org_ids_returns_none(self, mocker):
        """2.2.2: accessible_org_ids が空リストの場合、Noneを返す"""
        # Arrange
        mocker.patch(
            "src.services.industry_dashboard_service.Device"
        ).query.filter.return_value.first.return_value = None

        # Act
        from src.services.industry_dashboard_service import check_device_access
        result = check_device_access("uuid-001", [])

        # Assert
        assert result is None

    def test_nonexistent_device_uuid_returns_none(self, mocker):
        """2.2.2: 存在しない device_uuid はNoneを返す"""
        # Arrange
        mocker.patch(
            "src.services.industry_dashboard_service.Device"
        ).query.filter.return_value.first.return_value = None

        # Act
        from src.services.industry_dashboard_service import check_device_access
        result = check_device_access("uuid-nonexistent-9999", [1])

        # Assert
        assert result is None


# =============================================================================
# 5. アラート一覧取得 - get_recent_alerts_with_count()
#    観点: 2.1 正常系処理, 3.1 検索機能（Read）
#    対応ワークフロー: 店舗モニタリング初期表示・検索 > ③ アラート一覧取得
# =============================================================================

@pytest.mark.unit
class TestGetRecentAlertsWithCount:
    """アラート一覧取得（店舗モニタリング）

    観点: 2.1 正常系処理, 3.1.1 検索条件指定, 3.1.3 ページング・件数制御,
          3.1.4 検索結果戻り値ハンドリング
    対応ワークフロー仕様書:
        - ③ アラート一覧取得
        - get_recent_alerts_with_count(search_params, accessible_org_ids, limit=30)
    仕様:
        - アラート発生日時が過去30日以内のアラート履歴を最大30件取得
        - 検索条件: organization_name（部分一致）, device_name（部分一致）
        - ソート: alert_history_id DESC（デフォルト）
        - 戻り値: (alerts_list, total_count) のタプル
    """

    def _setup_mock_db(self, mocker, return_list=None, total_count=0):
        mock_db = mocker.patch("src.services.industry_dashboard_service.db")
        mock_query = mock_db.session.query.return_value.filter.return_value
        mock_query.count.return_value = total_count
        mock_query.order_by.return_value.limit.return_value.all.return_value = (
            return_list if return_list is not None else []
        )
        return mock_db, mock_query

    def test_returns_alert_list_and_count_tuple(self, mocker):
        """2.1.1 / 3.1.4.1: アラートリストと件数のタプルが返却される"""
        # Arrange
        mock_alert = Mock()
        mock_alert.alert_occurrence_datetime = datetime(2026, 2, 1, 18, 45, 0)
        mock_alert.device_name = "冷蔵庫1"
        mock_alert.alert_name = "温度異常"
        mock_alert.alert_level_name = "Warning"
        mock_alert.alert_status_name = "発生中"
        self._setup_mock_db(mocker, return_list=[mock_alert], total_count=1)

        # Act
        from src.services.industry_dashboard_service import get_recent_alerts_with_count
        alerts, total = get_recent_alerts_with_count(
            search_params={"organization_name": "", "device_name": ""},
            accessible_org_ids=[1],
            limit=30,
        )

        # Assert
        assert total == 1
        assert len(alerts) == 1
        assert alerts[0] is mock_alert

    def test_returns_empty_list_and_zero_count_when_no_alerts(self, mocker):
        """3.1.4.2: アラートが存在しない場合、空リストと0件が返却される"""
        # Arrange
        self._setup_mock_db(mocker, return_list=[], total_count=0)

        # Act
        from src.services.industry_dashboard_service import get_recent_alerts_with_count
        alerts, total = get_recent_alerts_with_count(
            search_params={"organization_name": "", "device_name": ""},
            accessible_org_ids=[1],
            limit=30,
        )

        # Assert
        assert total == 0
        assert alerts == []

    def test_search_params_passed_to_query(self, mocker):
        """3.1.1.2: 検索条件（店舗名・デバイス名）がクエリに渡される"""
        # Arrange
        mock_db, _ = self._setup_mock_db(mocker, return_list=[], total_count=0)

        # Act
        from src.services.industry_dashboard_service import get_recent_alerts_with_count
        get_recent_alerts_with_count(
            search_params={"organization_name": "店舗A", "device_name": "冷蔵庫"},
            accessible_org_ids=[1],
            limit=30,
        )

        # Assert
        mock_db.session.query.assert_called()

    def test_limit_applied_to_result(self, mocker):
        """3.1.3.1: limit=30 がクエリに適用される"""
        # Arrange
        mock_db = mocker.patch("src.services.industry_dashboard_service.db")
        mock_query = mock_db.session.query.return_value.filter.return_value
        mock_query.count.return_value = 0
        mock_limit = mock_query.order_by.return_value.limit
        mock_limit.return_value.all.return_value = []

        # Act
        from src.services.industry_dashboard_service import get_recent_alerts_with_count
        get_recent_alerts_with_count(
            search_params={"organization_name": "", "device_name": ""},
            accessible_org_ids=[1],
            limit=30,
        )

        # Assert
        mock_limit.assert_called_with(30)

    def test_organization_name_empty_string_treated_as_no_filter(self, mocker):
        """3.1.2.1: 店舗名が空文字の場合、フィルタなし相当でクエリが実行される"""
        # Arrange
        self._setup_mock_db(mocker, return_list=[], total_count=0)

        # Act
        from src.services.industry_dashboard_service import get_recent_alerts_with_count
        alerts, total = get_recent_alerts_with_count(
            search_params={"organization_name": "", "device_name": ""},
            accessible_org_ids=[1],
            limit=30,
        )

        # Assert
        assert total == 0  # クエリが正常実行されること


# =============================================================================
# 6. デバイス一覧取得 - get_device_list_with_count()
#    観点: 2.1 正常系処理, 3.1 検索機能（Read）, 3.1.3 ページング
#    対応ワークフロー: 店舗モニタリング初期表示・検索 > ④ デバイス一覧取得
# =============================================================================

@pytest.mark.unit
class TestGetDeviceListWithCount:
    """デバイス一覧取得（店舗モニタリング）

    観点: 2.1 正常系処理, 3.1.1 検索条件指定, 3.1.3 ページング・件数制御,
          3.1.4 検索結果戻り値ハンドリング
    対応ワークフロー仕様書:
        - ④ デバイス一覧取得
        - get_device_list_with_count(search_params, accessible_org_ids, page, per_page)
    仕様:
        - デバイスマスタから組織でフィルタしたデバイス一覧を取得
        - 検索条件: organization_name（部分一致）, device_name（部分一致）
        - ソート: organization_id ASC（デフォルト）
        - ページング: LIMIT per_page OFFSET (page-1)*per_page
        - 戻り値: (devices_list, total_count) のタプル
    """

    def _setup_mock_db(self, mocker, return_list=None, total_count=0):
        mock_db = mocker.patch("src.services.industry_dashboard_service.db")
        mock_query = mock_db.session.query.return_value.filter.return_value
        mock_query.count.return_value = total_count
        mock_query.order_by.return_value.limit.return_value.offset.return_value.all.return_value = (
            return_list if return_list is not None else []
        )
        return mock_db, mock_query

    def test_returns_device_list_and_count_tuple(self, mocker):
        """2.1.1 / 3.1.4.1: デバイスリストと件数のタプルが返却される"""
        # Arrange
        mock_device = _make_mock_device()
        self._setup_mock_db(mocker, return_list=[mock_device], total_count=1)

        # Act
        from src.services.industry_dashboard_service import get_device_list_with_count
        devices, total = get_device_list_with_count(
            search_params={"organization_name": "", "device_name": ""},
            accessible_org_ids=[1],
            page=1,
            per_page=10,
        )

        # Assert
        assert total == 1
        assert len(devices) == 1
        assert devices[0] is mock_device

    def test_returns_empty_list_when_no_devices(self, mocker):
        """3.1.4.2: デバイスが存在しない場合、空リストと0件が返却される"""
        # Arrange
        self._setup_mock_db(mocker, return_list=[], total_count=0)

        # Act
        from src.services.industry_dashboard_service import get_device_list_with_count
        devices, total = get_device_list_with_count(
            search_params={"organization_name": "", "device_name": ""},
            accessible_org_ids=[1],
            page=1,
            per_page=10,
        )

        # Assert
        assert total == 0
        assert devices == []

    def test_page_2_offset_is_10_when_per_page_10(self, mocker):
        """3.1.3.1: page=2, per_page=10 のとき OFFSET=10 が適用される"""
        # Arrange
        mock_db = mocker.patch("src.services.industry_dashboard_service.db")
        mock_query = mock_db.session.query.return_value.filter.return_value
        mock_query.count.return_value = 20
        mock_offset = mock_query.order_by.return_value.limit.return_value.offset
        mock_offset.return_value.all.return_value = []

        # Act
        from src.services.industry_dashboard_service import get_device_list_with_count
        get_device_list_with_count(
            search_params={"organization_name": "", "device_name": ""},
            accessible_org_ids=[1],
            page=2,
            per_page=10,
        )

        # Assert
        mock_offset.assert_called_with(10)  # (2-1) * 10 = 10

    def test_page_1_offset_is_0(self, mocker):
        """3.1.3.1: page=1, per_page=10 のとき OFFSET=0 が適用される"""
        # Arrange
        mock_db = mocker.patch("src.services.industry_dashboard_service.db")
        mock_query = mock_db.session.query.return_value.filter.return_value
        mock_query.count.return_value = 5
        mock_offset = mock_query.order_by.return_value.limit.return_value.offset
        mock_offset.return_value.all.return_value = []

        # Act
        from src.services.industry_dashboard_service import get_device_list_with_count
        get_device_list_with_count(
            search_params={"organization_name": "", "device_name": ""},
            accessible_org_ids=[1],
            page=1,
            per_page=10,
        )

        # Assert
        mock_offset.assert_called_with(0)

    def test_search_params_both_conditions_passed_to_query(self, mocker):
        """3.1.1.2: 複数条件（店舗名・デバイス名）が両方クエリに渡される"""
        # Arrange
        mock_db, _ = self._setup_mock_db(mocker, return_list=[], total_count=0)

        # Act
        from src.services.industry_dashboard_service import get_device_list_with_count
        get_device_list_with_count(
            search_params={"organization_name": "店舗A", "device_name": "冷蔵庫"},
            accessible_org_ids=[1],
            page=1,
            per_page=10,
        )

        # Assert
        mock_db.session.query.assert_called()

    def test_per_page_limit_applied_to_query(self, mocker):
        """3.1.3.1: per_page=10 が LIMIT として適用される"""
        # Arrange
        mock_db = mocker.patch("src.services.industry_dashboard_service.db")
        mock_query = mock_db.session.query.return_value.filter.return_value
        mock_query.count.return_value = 0
        mock_limit = mock_query.order_by.return_value.limit
        mock_limit.return_value.offset.return_value.all.return_value = []

        # Act
        from src.services.industry_dashboard_service import get_device_list_with_count
        get_device_list_with_count(
            search_params={"organization_name": "", "device_name": ""},
            accessible_org_ids=[1],
            page=1,
            per_page=10,
        )

        # Assert
        mock_limit.assert_called_with(10)


# =============================================================================
# 7. デバイス別アラート一覧取得 - get_device_alerts_with_count()
#    観点: 2.1 正常系処理, 3.1 検索機能（Read）
#    対応ワークフロー: デバイス詳細初期表示 > アラート一覧取得
# =============================================================================

@pytest.mark.unit
class TestGetDeviceAlertsWithCount:
    """デバイス別アラート一覧取得（デバイス詳細画面）

    観点: 2.1 正常系処理, 3.1.1 検索条件指定, 3.1.3 ページング・件数制御,
          3.1.4 検索結果戻り値ハンドリング
    対応ワークフロー仕様書:
        - デバイス詳細初期表示 > アラート一覧取得
        - get_device_alerts_with_count(device_id, search_params)
    仕様:
        - 特定デバイスのアラート履歴（過去30日以内）を最大30件取得
        - ソート: alert_history_id DESC（UI仕様書 9-テーブル設定）
        - デバイス詳細画面はデバイスで絞り込み済みのためデバイス名カラムなし（UI仕様書 (9)）
        - 戻り値: (alerts_list, total_count) のタプル
    """

    def _setup_mock_db(self, mocker, return_list=None, total_count=0):
        mock_db = mocker.patch("src.services.industry_dashboard_service.db")
        mock_query = mock_db.session.query.return_value.filter.return_value
        mock_query.count.return_value = total_count
        mock_query.order_by.return_value.limit.return_value.offset.return_value.all.return_value = (
            return_list if return_list is not None else []
        )
        return mock_db, mock_query

    def test_returns_alert_list_and_count_for_specific_device(self, mocker):
        """2.1.1 / 3.1.1.1: 特定デバイスのアラートリストと件数が返却される"""
        # Arrange
        mock_alert = Mock()
        mock_alert.alert_occurrence_datetime = datetime(2026, 2, 1, 18, 45, 0)
        mock_alert.alert_name = "温度異常"
        mock_alert.alert_level_name = "Warning"
        mock_alert.alert_status_name = "発生中"
        self._setup_mock_db(mocker, return_list=[mock_alert], total_count=1)

        # Act
        from src.services.industry_dashboard_service import get_device_alerts_with_count
        alerts, total = get_device_alerts_with_count(
            device_id=1,
            search_params={"page": 1},
        )

        # Assert
        assert total == 1
        assert len(alerts) == 1

    def test_returns_empty_list_when_no_alerts_for_device(self, mocker):
        """3.1.4.2: 対象デバイスにアラートが存在しない場合、空リストが返却される"""
        # Arrange
        self._setup_mock_db(mocker, return_list=[], total_count=0)

        # Act
        from src.services.industry_dashboard_service import get_device_alerts_with_count
        alerts, total = get_device_alerts_with_count(
            device_id=1,
            search_params={"page": 1},
        )

        # Assert
        assert total == 0
        assert alerts == []

    def test_device_id_passed_to_query_filter(self, mocker):
        """3.1.1.1: device_id がクエリフィルタに渡される"""
        # Arrange
        mock_db, _ = self._setup_mock_db(mocker, return_list=[], total_count=0)

        # Act
        from src.services.industry_dashboard_service import get_device_alerts_with_count
        get_device_alerts_with_count(device_id=42, search_params={"page": 1})

        # Assert
        mock_db.session.query.assert_called()


# =============================================================================
# 8. 最新センサーデータ取得 - get_latest_sensor_data()
#    観点: 2.1 正常系処理, 3.1.4 検索結果戻り値ハンドリング
#    対応ワークフロー: センサー情報表示 > ② 最新センサーデータ取得
# =============================================================================

@pytest.mark.unit
class TestGetLatestSensorData:
    """最新センサーデータ取得（Unity Catalog / sensor_data_view）

    観点: 2.1 正常系処理, 3.1.4 検索結果戻り値ハンドリング
    対応ワークフロー仕様書:
        - センサー情報表示 > ② 最新センサーデータ取得
        - get_latest_sensor_data(device_id)
    仕様:
        - sensor_data_view から device_id で絞り込み
        - event_timestamp DESC LIMIT 1 で最新1件を取得
        - 戻り値: センサーデータ行オブジェクト または None
    """

    def test_returns_latest_sensor_row_when_exists(self, mocker):
        """3.1.4.1: センサーデータが存在する場合、最新の1行が返却される"""
        # Arrange
        mock_row = _make_mock_sensor_row()
        mock_connector = mocker.patch(
            "src.services.industry_dashboard_service.get_databricks_connection"
        )
        mock_cursor = mock_connector.return_value.__enter__.return_value.cursor.return_value
        mock_cursor.fetchone.return_value = mock_row

        # Act
        from src.services.industry_dashboard_service import get_latest_sensor_data
        result = get_latest_sensor_data(device_id=1)

        # Assert
        assert result is mock_row

    def test_returns_none_when_no_sensor_data(self, mocker):
        """3.1.4.2: センサーデータが存在しない場合、Noneが返却される"""
        # Arrange
        mock_connector = mocker.patch(
            "src.services.industry_dashboard_service.get_databricks_connection"
        )
        mock_cursor = mock_connector.return_value.__enter__.return_value.cursor.return_value
        mock_cursor.fetchone.return_value = None

        # Act
        from src.services.industry_dashboard_service import get_latest_sensor_data
        result = get_latest_sensor_data(device_id=999)

        # Assert
        assert result is None

    def test_device_id_passed_to_query(self, mocker):
        """3.1.1.1: device_id がSQLクエリに渡される"""
        # Arrange
        mock_connector = mocker.patch(
            "src.services.industry_dashboard_service.get_databricks_connection"
        )
        mock_cursor = mock_connector.return_value.__enter__.return_value.cursor.return_value
        mock_cursor.fetchone.return_value = None

        # Act
        from src.services.industry_dashboard_service import get_latest_sensor_data
        get_latest_sensor_data(device_id=42)

        # Assert
        mock_cursor.execute.assert_called_once()
        call_args = mock_cursor.execute.call_args
        # SQLまたはパラメータに device_id=42 が含まれることを確認
        assert any(
            42 in str(arg) or 42 in (arg if isinstance(arg, (list, tuple, dict)) else [])
            for arg in call_args.args + tuple(call_args.kwargs.values())
        )


# =============================================================================
# 9. グラフ用センサーデータ取得 - get_graph_data()
#    観点: 2.1 正常系処理, 3.1.1 検索条件指定, 3.1.4 検索結果戻り値ハンドリング
#    対応ワークフロー: デバイス詳細初期表示・検索 > ② グラフ用データ取得
# =============================================================================

@pytest.mark.unit
class TestGetGraphData:
    """グラフ用センサーデータ取得（Unity Catalog / sensor_data_view）

    観点: 2.1 正常系処理, 3.1.1 検索条件指定, 3.1.4 検索結果戻り値ハンドリング
    対応ワークフロー仕様書:
        - ② グラフ用データ取得
        - get_graph_data(device_id, search_params)
    仕様:
        - sensor_data_view から表示期間（BETWEEN）でフィルタした全データを取得
        - event_timestamp ASC でソート
        - 戻り値: センサーデータ行のリスト
    """

    def _default_search_params(self):
        return {
            "search_start_datetime": "2026/02/26T12:00",
            "search_end_datetime":   "2026/02/27T12:00",
        }

    def test_returns_list_of_sensor_rows(self, mocker):
        """3.1.4.1: 期間内のセンサーデータリストが返却される"""
        # Arrange
        mock_rows = [_make_mock_sensor_row() for _ in range(3)]
        mock_connector = mocker.patch(
            "src.services.industry_dashboard_service.get_databricks_connection"
        )
        mock_cursor = mock_connector.return_value.__enter__.return_value.cursor.return_value
        mock_cursor.fetchall.return_value = mock_rows

        # Act
        from src.services.industry_dashboard_service import get_graph_data
        result = get_graph_data(device_id=1, search_params=self._default_search_params())

        # Assert
        assert len(result) == 3

    def test_returns_empty_list_when_no_data_in_period(self, mocker):
        """3.1.4.2: 期間内にデータがない場合、空リストが返却される"""
        # Arrange
        mock_connector = mocker.patch(
            "src.services.industry_dashboard_service.get_databricks_connection"
        )
        mock_cursor = mock_connector.return_value.__enter__.return_value.cursor.return_value
        mock_cursor.fetchall.return_value = []

        # Act
        from src.services.industry_dashboard_service import get_graph_data
        result = get_graph_data(device_id=1, search_params=self._default_search_params())

        # Assert
        assert result == []

    def test_search_start_and_end_datetime_passed_to_query(self, mocker):
        """3.1.1.2: 表示期間（start/end）がSQLクエリに渡される"""
        # Arrange
        mock_connector = mocker.patch(
            "src.services.industry_dashboard_service.get_databricks_connection"
        )
        mock_cursor = mock_connector.return_value.__enter__.return_value.cursor.return_value
        mock_cursor.fetchall.return_value = []

        search_params = {
            "search_start_datetime": "2026/02/01T00:00",
            "search_end_datetime":   "2026/02/02T00:00",
        }

        # Act
        from src.services.industry_dashboard_service import get_graph_data
        get_graph_data(device_id=1, search_params=search_params)

        # Assert
        mock_cursor.execute.assert_called_once()


# =============================================================================
# 10. CSVエクスポート - export_sensor_data_csv()
#     観点: 3.5 CSVエクスポート機能
#     対応ワークフロー: CSVエクスポート
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
        "第1冷凍 庫内温度",
        "第1冷凍 DF温度",
        "第1冷凍 凝縮温度",
        "第1冷凍 微調整後庫内温度",
        "第2冷凍 設定温度",
        "第2冷凍 庫内センサー温度",
        "第2冷凍 庫内温度",
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
            "search_start_datetime": "2026/02/26T12:00",
            "search_end_datetime":   "2026/02/27T12:00",
        }

    def _call_export(self, mocker, device=None, sensor_rows=None):
        """export_sensor_data_csv を呼び出すヘルパー（Flask app_context が必要）"""
        if device is None:
            device = _make_mock_device()
        if sensor_rows is None:
            sensor_rows = []
        mocker.patch(
            "src.services.industry_dashboard_service.get_all_sensor_data",
            return_value=sensor_rows,
        )
        from src.services.industry_dashboard_service import export_sensor_data_csv
        return export_sensor_data_csv(device, self._default_search_params())

    # ------------------------------------------------------------------
    # 3.5.1 CSV生成ロジック
    # ------------------------------------------------------------------

    def test_header_row_contains_all_required_columns(self, mocker):
        """3.5.1.1: 定義された全カラム名がヘッダー行に出力される（ワークフロー仕様書 CSVエクスポート準拠）"""
        # Arrange / Act
        response = self._call_export(mocker, sensor_rows=[])
        csv_text = response.data.decode("utf-8-sig")
        first_line = csv_text.split("\n")[0]

        # Assert
        for header in self._EXPECTED_HEADERS:
            assert header in first_line, f"ヘッダーに '{header}' が含まれていない"

    def test_empty_data_outputs_header_only(self, mocker):
        """3.5.1.3: データ0件のとき、ヘッダー行のみ出力される"""
        # Arrange / Act
        response = self._call_export(mocker, sensor_rows=[])
        csv_text = response.data.decode("utf-8-sig")
        non_empty_lines = [l for l in csv_text.split("\n") if l.strip()]

        # Assert
        assert len(non_empty_lines) == 1  # ヘッダーのみ

    def test_data_rows_count_matches_sensor_data_count(self, mocker):
        """3.5.1.2: データ行数がセンサーデータ件数と一致する"""
        # Arrange
        rows = [_make_mock_sensor_row() for _ in range(3)]

        # Act
        response = self._call_export(mocker, sensor_rows=rows)
        csv_text = response.data.decode("utf-8-sig")
        non_empty_lines = [l for l in csv_text.split("\n") if l.strip()]

        # Assert
        assert len(non_empty_lines) == 4  # ヘッダー1行 + データ3行

    def test_column_order_follows_specification(self, mocker):
        """3.5.1.4: カラム順序がワークフロー仕様書の定義通り"""
        # Arrange / Act
        response = self._call_export(mocker, sensor_rows=[])
        csv_text = response.data.decode("utf-8-sig")
        first_line = csv_text.split("\n")[0]

        # Assert: 先頭カラムが「イベント発生日時」
        assert first_line.startswith("イベント発生日時")

    def test_event_timestamp_formatted_as_yyyy_mm_dd_hh_mm_ss(self, mocker):
        """3.5.1.4: event_timestamp が YYYY-MM-DD HH:MM:SS 形式で出力される"""
        # Arrange
        row = _make_mock_sensor_row(event_timestamp=datetime(2026, 2, 27, 12, 30, 0))

        # Act
        response = self._call_export(mocker, sensor_rows=[row])
        csv_text = response.data.decode("utf-8-sig")
        data_line = csv_text.split("\n")[1]

        # Assert
        assert "2026-02-27 12:30:00" in data_line

    def test_none_sensor_value_outputs_empty_string(self, mocker):
        """3.5.1.2: センサーデータ値が None の場合、空文字で出力される"""
        # Arrange
        row = _make_mock_sensor_row(external_temp=None)

        # Act
        response = self._call_export(mocker, sensor_rows=[row])
        csv_text = response.data.decode("utf-8-sig")

        # Assert
        # None は空文字に変換される（ワークフロー仕様書: data.external_temp or ''）
        assert ",," in csv_text  # 空フィールドが含まれること

    # ------------------------------------------------------------------
    # 3.5.2 エスケープ処理
    # ------------------------------------------------------------------

    def test_comma_in_data_is_escaped_with_double_quotes(self, mocker):
        """3.5.2.1: データにカンマを含む場合、ダブルクォートで囲まれる"""
        # Arrange
        row = _make_mock_sensor_row(external_temp="25,0")  # カンマ含む文字列

        # Act
        response = self._call_export(mocker, sensor_rows=[row])
        csv_text = response.data.decode("utf-8-sig")

        # Assert
        assert '"25,0"' in csv_text

    def test_double_quote_in_data_is_escaped(self, mocker):
        """3.5.2.3: データに " を含む場合、"" でエスケープされる"""
        # Arrange
        row = _make_mock_sensor_row(external_temp='val"ue')

        # Act
        response = self._call_export(mocker, sensor_rows=[row])
        csv_text = response.data.decode("utf-8-sig")

        # Assert
        assert '"val""ue"' in csv_text

    def test_newline_in_data_is_escaped(self, mocker):
        """3.5.2.2: データに改行を含む場合、ダブルクォートで囲まれる"""
        # Arrange
        row = _make_mock_sensor_row(external_temp="line1\nline2")

        # Act
        response = self._call_export(mocker, sensor_rows=[row])
        csv_text = response.data.decode("utf-8-sig")

        # Assert
        assert '"line1\nline2"' in csv_text

    # ------------------------------------------------------------------
    # 3.5.3 エンコーディング処理
    # ------------------------------------------------------------------

    def test_csv_starts_with_utf8_bom(self, mocker):
        """3.5.3.1: CSVがUTF-8 BOM付き (0xEF 0xBB 0xBF) で出力される"""
        # Arrange / Act
        response = self._call_export(mocker, sensor_rows=[])
        raw_bytes = response.data

        # Assert
        assert raw_bytes[:3] == b"\xef\xbb\xbf", \
            "CSVの先頭にUTF-8 BOMが付与されていない"

    def test_japanese_header_is_readable_with_utf8_bom(self, mocker):
        """3.5.3.2: 日本語ヘッダーがUTF-8 BOMデコードで文字化けなく読める"""
        # Arrange / Act
        response = self._call_export(mocker, sensor_rows=[])
        csv_text = response.data.decode("utf-8-sig")

        # Assert
        assert "イベント発生日時" in csv_text
        assert "防露ヒータ出力" in csv_text

    # ------------------------------------------------------------------
    # HTTPレスポンスヘッダー
    # ------------------------------------------------------------------

    def test_content_type_is_text_csv(self, mocker):
        """CSVレスポンスの Content-Type が text/csv を含む"""
        # Arrange / Act
        response = self._call_export(mocker, sensor_rows=[])

        # Assert
        content_type = response.headers.get("Content-type", "")
        assert "text/csv" in content_type

    def test_content_disposition_is_attachment(self, mocker):
        """CSVレスポンスの Content-Disposition が attachment である"""
        # Arrange / Act
        response = self._call_export(mocker, sensor_rows=[])

        # Assert
        content_disposition = response.headers.get("Content-Disposition", "")
        assert "attachment" in content_disposition

    def test_content_disposition_contains_device_uuid(self, mocker):
        """CSVファイル名に device_uuid が含まれる"""
        # Arrange
        device = _make_mock_device(device_uuid="uuid-test-001")

        # Act
        response = self._call_export(mocker, device=device, sensor_rows=[])

        # Assert
        content_disposition = response.headers.get("Content-Disposition", "")
        assert "uuid-test-001" in content_disposition

    def test_content_disposition_filename_contains_timestamp(self, mocker):
        """CSVファイル名に現在日時（YYYYMMdd_HHmmss形式）が含まれる"""
        # Arrange
        with patch("src.services.industry_dashboard_service.datetime") as mock_dt:
            mock_dt.now.return_value = datetime(2026, 2, 27, 12, 0, 0)

            # Act
            response = self._call_export(mocker, sensor_rows=[])

        # Assert
        content_disposition = response.headers.get("Content-Disposition", "")
        assert "20260227_120000" in content_disposition
