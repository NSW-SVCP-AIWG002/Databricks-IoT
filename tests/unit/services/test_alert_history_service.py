"""
アラート履歴 - Service層 単体テスト（TDD）

対象ファイル: src/iot_app/services/alert_history_service.py

参照ドキュメント:
  - UI設計書:         docs/03-features/flask-app/alert-history/ui-specification.md
  - 機能設計書:       docs/03-features/flask-app/alert-history/workflow-specification.md
  - 単体テスト観点表: docs/05-testing/unit-test/unit-test-perspectives.md
  - 実装ガイド:       docs/05-testing/unit-test/unit-test-guide.md

テスト対象関数:
  - get_default_search_params       デフォルト検索条件を返す
  - search_alert_histories          アラート履歴一覧検索（v_alert_history_by_user VIEW経由）
  - get_alert_history_detail        アラート履歴詳細取得（v_alert_history_by_user VIEW経由）

データスコープ制御パターン（VIEW方式）:
  v_alert_history_by_user に user_id を渡すことでスコープ制限を自動適用。
  VIEWが内部で organization_closure を参照し、アクセス可能な組織のデータのみ返す。
  アプリ側では organization_closure への直接アクセスは不要。
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, Mock, patch

MODULE = "iot_app.services.alert_history_service"


# =============================================================================
# テストヘルパー
# =============================================================================

def _make_default_search_params(**overrides):
    """デフォルト検索パラメータを生成するヘルパー。
    UI仕様書 (2) 検索フォームの初期値に基づく。
    """
    now = datetime.now()
    params = {
        "page": 1,
        "per_page": 25,
        "sort_by": "alert_occurrence_datetime",
        "order": "desc",
        "start_datetime": (now - timedelta(days=7)).strftime("%Y/%m/%d 00:00"),
        "end_datetime": now.strftime("%Y/%m/%d 23:59"),
        "device_name": None,
        "device_location": None,
        "alert_name": None,
        "alert_level_id": None,
        "alert_status_id": None,
    }
    params.update(overrides)
    return params


def _make_mock_alert_history(**kwargs):
    """モックアラート履歴オブジェクトを生成するヘルパー。
    AlertHistoryByUser（v_alert_history_by_user VIEW）の結果を模倣する。
    """
    m = Mock()
    m.alert_history_id = kwargs.get("alert_history_id", 1)
    m.alert_history_uuid = kwargs.get("alert_history_uuid", "uuid-001")
    m.alert_occurrence_datetime = kwargs.get(
        "alert_occurrence_datetime", datetime(2026, 1, 13, 18, 45, 0)
    )
    m.alert_recovery_datetime = kwargs.get("alert_recovery_datetime", None)
    m.alert_value = kwargs.get("alert_value", 85.5)
    m.alert_status_id = kwargs.get("alert_status_id", 1)
    m.delete_flag = kwargs.get("delete_flag", False)
    m.user_id = kwargs.get("user_id", 10)
    # VIEWが結合済みのカラム
    m.device_name = kwargs.get("device_name", "テストデバイス")
    m.device_location = kwargs.get("device_location", "東京倉庫")
    m.alert_name = kwargs.get("alert_name", "温度異常")
    m.alert_level_id = kwargs.get("alert_level_id", 2)
    m.alert_level_name = kwargs.get("alert_level_name", "Warning")
    m.alert_status_name = kwargs.get("alert_status_name", "発生中")
    return m


def _setup_mock_query(mock_db, count=0, results=None):
    """db.session.query チェーンのモックをセットアップするヘルパー。"""
    if results is None:
        results = []
    mock_query = MagicMock()
    mock_db.session.query.return_value = mock_query
    mock_query.filter.return_value = mock_query
    mock_query.order_by.return_value = mock_query
    mock_query.count.return_value = count
    mock_query.limit.return_value = mock_query
    mock_query.offset.return_value = mock_query
    mock_query.all.return_value = results
    mock_query.first.return_value = results[0] if results else None
    return mock_query


# =============================================================================
# 2.1 get_default_search_params — デフォルト検索条件
# =============================================================================

@pytest.mark.unit
class TestGetDefaultSearchParams:
    """2.1 get_default_search_params — デフォルト検索条件

    ワークフロー仕様書「実装例: get_default_search_params()」に基づく。
    """

    def test_returns_dict(self):
        """2.1.1: 戻り値が dict 型であること"""
        from iot_app.services.alert_history_service import get_default_search_params
        result = get_default_search_params()
        assert isinstance(result, dict)

    def test_has_required_keys(self):
        """2.1.1: 必須キーをすべて含むこと"""
        from iot_app.services.alert_history_service import get_default_search_params
        result = get_default_search_params()
        required_keys = {
            "page", "per_page", "sort_by", "order",
            "start_datetime", "end_datetime",
            "device_name", "device_location", "alert_name",
            "alert_level_id", "alert_status_id",
        }
        assert required_keys.issubset(result.keys())

    def test_start_datetime_is_7_days_before_today(self):
        """2.1.1: start_datetime が現在日から7日前の 00:00 であること
        UI仕様書 (2-1): 初期表示は直近7日間
        """
        from iot_app.services.alert_history_service import get_default_search_params
        result = get_default_search_params()
        expected_date = (datetime.now() - timedelta(days=7)).strftime("%Y/%m/%d")
        assert result["start_datetime"].startswith(expected_date)
        assert "00:00" in result["start_datetime"]

    def test_end_datetime_is_today_2359(self):
        """2.1.1: end_datetime が現在日の 23:59 であること
        UI仕様書 (2-2): 終了日時の初期値は当日23:59
        """
        from iot_app.services.alert_history_service import get_default_search_params
        result = get_default_search_params()
        expected_date = datetime.now().strftime("%Y/%m/%d")
        assert result["end_datetime"].startswith(expected_date)
        assert "23:59" in result["end_datetime"]

    def test_sort_by_default_is_alert_occurrence_datetime(self):
        """2.1.1: sort_by のデフォルトが alert_occurrence_datetime であること
        UI仕様書 (2-8): ソート項目デフォルトは発生日時
        """
        from iot_app.services.alert_history_service import get_default_search_params
        result = get_default_search_params()
        assert result["sort_by"] == "alert_occurrence_datetime"

    def test_order_default_is_desc(self):
        """2.1.1: order のデフォルトが 'desc' であること
        UI仕様書 (2-9): ソート順デフォルトは降順（最新が上）
        """
        from iot_app.services.alert_history_service import get_default_search_params
        result = get_default_search_params()
        assert result["order"] == "desc"

    def test_alert_level_id_default_is_none(self):
        """2.1.1: alert_level_id のデフォルトが None（すべて）であること
        UI仕様書 (2-6): アラートレベルのデフォルトは「すべて」
        """
        from iot_app.services.alert_history_service import get_default_search_params
        result = get_default_search_params()
        assert result["alert_level_id"] is None

    def test_alert_status_id_default_is_none(self):
        """2.1.1: alert_status_id のデフォルトが None（すべて）であること
        UI仕様書 (2-7): ステータスのデフォルトは「すべて」
        """
        from iot_app.services.alert_history_service import get_default_search_params
        result = get_default_search_params()
        assert result["alert_status_id"] is None


# =============================================================================
# 2.1 / 3.1.1 search_alert_histories — データスコープ制御
# =============================================================================

@pytest.mark.unit
class TestSearchAlertHistoriesScope:
    """3.1.1.1 / 2.1 データスコープ制御（VIEW方式）

    ワークフロー仕様書「③ データスコープ制限の適用」:
      v_alert_history_by_user に user_id を渡すことでスコープ制限を自動適用。
      VIEWが内部で organization_closure を参照するため、
      アプリ側では user_id フィルタのみ実施する。
    """

    @patch(f"{MODULE}.AlertHistoryByUser")
    @patch(f"{MODULE}.db")
    def test_user_id_filter_applied(self, mock_db, _mock_model):
        """2.1.1: search_alert_histories でログインユーザーの user_id でフィルタされること"""
        # Arrange
        user_id = 10
        search_params = _make_default_search_params()
        mock_query = _setup_mock_query(mock_db)

        # Act
        from iot_app.services.alert_history_service import search_alert_histories
        search_alert_histories(search_params=search_params, user_id=user_id)

        # Assert: filter が呼ばれていること（user_id スコープ適用）
        mock_query.filter.assert_called()

    @patch(f"{MODULE}.AlertHistoryByUser")
    @patch(f"{MODULE}.db")
    def test_delete_flag_false_filter_applied(self, mock_db, _mock_model):
        """2.1.1: delete_flag=False のフィルタが適用されること（論理削除レコード除外）"""
        # Arrange
        user_id = 10
        search_params = _make_default_search_params()
        mock_query = _setup_mock_query(mock_db)

        # Act
        from iot_app.services.alert_history_service import search_alert_histories
        search_alert_histories(search_params=search_params, user_id=user_id)

        # Assert
        assert mock_query.filter.call_count >= 1

    @patch(f"{MODULE}.AlertHistoryByUser")
    @patch(f"{MODULE}.db")
    def test_empty_result_when_no_accessible_data(self, mock_db, _mock_model):
        """3.1.4.1: アクセス可能なデータが0件の場合、空リストと 0 を返すこと"""
        # Arrange
        user_id = 99  # スコープ外ユーザー
        search_params = _make_default_search_params()
        _setup_mock_query(mock_db, count=0, results=[])

        # Act
        from iot_app.services.alert_history_service import search_alert_histories
        result_list, total = search_alert_histories(search_params=search_params, user_id=user_id)

        # Assert
        assert result_list == []
        assert total == 0


# =============================================================================
# 3.1.1 search_alert_histories — 検索条件の適用
# =============================================================================

@pytest.mark.unit
class TestSearchAlertHistoriesWithConditions:
    """3.1.1 検索条件の適用

    ワークフロー仕様書 SQL詳細（CASE WHEN パターン）:
      各条件が NULL の場合は条件を適用しない。
      複数条件は AND で結合する。OR は使用しない。
    """

    @patch(f"{MODULE}.AlertHistoryByUser")
    @patch(f"{MODULE}.db")
    def test_start_end_datetime_between_filter(self, mock_db, _mock_model):
        """3.1.1.1/2: 期間（start_datetime, end_datetime）が指定された場合、
        BETWEEN フィルタが適用される
        UI仕様書 (2-1)(2-2): 期間検索
        """
        # Arrange
        user_id = 10
        search_params = _make_default_search_params(
            start_datetime="2026/01/01 00:00",
            end_datetime="2026/01/07 23:59",
        )
        mock_query = _setup_mock_query(mock_db, count=1, results=[_make_mock_alert_history()])

        # Act
        from iot_app.services.alert_history_service import search_alert_histories
        search_alert_histories(search_params=search_params, user_id=user_id)

        # Assert: filter が呼ばれること（BETWEEN 含む）
        assert mock_query.filter.call_count >= 1

    @patch(f"{MODULE}.AlertHistoryByUser")
    @patch(f"{MODULE}.db")
    def test_start_end_datetime_none_no_between_filter(self, mock_db, _mock_model):
        """3.1.1.1: start_datetime/end_datetime が None の場合、BETWEEN フィルタが追加されない
        CASE WHEN :start_datetime IS NULL THEN TRUE ...
        """
        # Arrange
        user_id = 10

        def _run(start, end):
            mock_query = _setup_mock_query(mock_db)
            search_params = _make_default_search_params(start_datetime=start, end_datetime=end)
            from iot_app.services.alert_history_service import search_alert_histories
            search_alert_histories(search_params=search_params, user_id=user_id)
            return mock_query.filter.call_count

        # Act
        count_with = _run("2026/01/01 00:00", "2026/01/07 23:59")
        count_without = _run(None, None)

        # Assert: 期間なしの方がフィルタ呼び出し回数が少ない
        assert count_without <= count_with

    @patch(f"{MODULE}.AlertHistoryByUser")
    @patch(f"{MODULE}.db")
    def test_device_name_partial_match(self, mock_db, _mock_model):
        """3.1.1.1: device_name を指定した場合、部分一致フィルタが適用される
        UI仕様書 (2-3): デバイス名（前方・後方・中間一致、max100文字）
        """
        # Arrange
        user_id = 10
        search_params = _make_default_search_params(device_name="センサー")
        mock_query = _setup_mock_query(mock_db)

        # Act
        from iot_app.services.alert_history_service import search_alert_histories
        search_alert_histories(search_params=search_params, user_id=user_id)

        # Assert
        mock_query.filter.assert_called()

    @patch(f"{MODULE}.AlertHistoryByUser")
    @patch(f"{MODULE}.db")
    def test_device_location_partial_match(self, mock_db, _mock_model):
        """3.1.1.1: device_location を指定した場合、部分一致フィルタが適用される
        UI仕様書 (2-4): 設置場所（前方・後方・中間一致、max100文字）
        """
        # Arrange
        user_id = 10
        search_params = _make_default_search_params(device_location="東京")
        mock_query = _setup_mock_query(mock_db)

        # Act
        from iot_app.services.alert_history_service import search_alert_histories
        search_alert_histories(search_params=search_params, user_id=user_id)

        # Assert
        mock_query.filter.assert_called()

    @patch(f"{MODULE}.AlertHistoryByUser")
    @patch(f"{MODULE}.db")
    def test_alert_name_partial_match(self, mock_db, _mock_model):
        """3.1.1.1: alert_name を指定した場合、部分一致フィルタが適用される
        UI仕様書 (2-5): アラート名（前方・後方・中間一致、max100文字）
        """
        # Arrange
        user_id = 10
        search_params = _make_default_search_params(alert_name="温度")
        mock_query = _setup_mock_query(mock_db)

        # Act
        from iot_app.services.alert_history_service import search_alert_histories
        search_alert_histories(search_params=search_params, user_id=user_id)

        # Assert
        mock_query.filter.assert_called()

    @patch(f"{MODULE}.AlertHistoryByUser")
    @patch(f"{MODULE}.db")
    def test_alert_level_id_exact_match(self, mock_db, _mock_model):
        """3.1.1.3: alert_level_id を指定した場合、完全一致フィルタが適用される
        UI仕様書 (2-6): アラートレベル（完全一致）
        """
        # Arrange
        user_id = 10
        search_params = _make_default_search_params(alert_level_id=2)
        mock_query = _setup_mock_query(mock_db)

        # Act
        from iot_app.services.alert_history_service import search_alert_histories
        search_alert_histories(search_params=search_params, user_id=user_id)

        # Assert
        mock_query.filter.assert_called()

    @patch(f"{MODULE}.AlertHistoryByUser")
    @patch(f"{MODULE}.db")
    def test_alert_status_id_exact_match(self, mock_db, _mock_model):
        """3.1.1.3: alert_status_id を指定した場合、完全一致フィルタが適用される
        UI仕様書 (2-7): ステータス（完全一致）
        """
        # Arrange
        user_id = 10
        search_params = _make_default_search_params(alert_status_id=1)
        mock_query = _setup_mock_query(mock_db)

        # Act
        from iot_app.services.alert_history_service import search_alert_histories
        search_alert_histories(search_params=search_params, user_id=user_id)

        # Assert
        mock_query.filter.assert_called()

    @patch(f"{MODULE}.AlertHistoryByUser")
    @patch(f"{MODULE}.db")
    def test_multiple_conditions_are_and(self, mock_db, _mock_model):
        """3.1.1.4: 複数条件を指定した場合、AND 結合されること（filter() が複数回呼ばれる）
        SQL: 各 CASE WHEN 条件は AND で結合される
        """
        # Arrange
        user_id = 10

        def _run(params):
            mock_query = _setup_mock_query(mock_db)
            from iot_app.services.alert_history_service import search_alert_histories
            search_alert_histories(search_params=params, user_id=user_id)
            return mock_query.filter.call_count

        # Act
        count_multi = _run(_make_default_search_params(
            device_name="センサー", alert_level_id=2, alert_status_id=1
        ))
        count_none = _run(_make_default_search_params(
            device_name=None, alert_level_id=None, alert_status_id=None
        ))

        # Assert: 複数条件の方がフィルタ呼び出し回数が多い
        assert count_multi >= count_none

    @patch(f"{MODULE}.AlertHistoryByUser")
    @patch(f"{MODULE}.db")
    def test_no_or_condition_used(self, mock_db, _mock_model):
        """3.1.1.5: OR 条件（sqlalchemy.or_）が使用されないこと
        仕様: 検索条件はすべて AND 結合。OR は禁止。
        """
        # Arrange
        user_id = 10
        search_params = _make_default_search_params(device_name="センサー", alert_name="温度")
        _setup_mock_query(mock_db)

        # Act & Assert
        with patch("sqlalchemy.or_") as mock_or:
            from iot_app.services.alert_history_service import search_alert_histories
            search_alert_histories(search_params=search_params, user_id=user_id)
            mock_or.assert_not_called()

    @patch(f"{MODULE}.AlertHistoryByUser")
    @patch(f"{MODULE}.db")
    def test_alert_level_all_selected_returns_all_levels(self, mock_db, _mock_model):
        """3.1.1.3: alert_level_id=None（すべて選択）の場合、全レベルのアラートが返される
        UI仕様書 (2-6): 「すべて」がデフォルト選択
        """
        # Arrange
        user_id = 10
        search_params = _make_default_search_params(alert_level_id=None)
        mock_histories = [
            _make_mock_alert_history(alert_history_id=1, alert_level_name="Critical"),
            _make_mock_alert_history(alert_history_id=2, alert_level_name="Warning"),
            _make_mock_alert_history(alert_history_id=3, alert_level_name="Info"),
        ]
        _setup_mock_query(mock_db, count=3, results=mock_histories)

        # Act
        from iot_app.services.alert_history_service import search_alert_histories
        result_list, total = search_alert_histories(search_params=search_params, user_id=user_id)

        # Assert: 全レベルが返される
        assert isinstance(total, int)
        assert len(result_list) == 3
        levels = {h.alert_level_name for h in result_list}
        assert {"Critical", "Warning", "Info"} == levels

    @patch(f"{MODULE}.AlertHistoryByUser")
    @patch(f"{MODULE}.db")
    def test_alert_level_all_selected_has_fewer_filters_than_specific(self, mock_db, _mock_model):
        """3.1.1.3: alert_level_id=None の場合、具体値指定より filter() 呼び出し回数が少ない
        None → レベルフィルタを追加しない（CASE WHEN IS NULL THEN TRUE）
        """
        # Arrange
        user_id = 10

        def _run(alert_level_id):
            mock_query = _setup_mock_query(mock_db)
            search_params = _make_default_search_params(alert_level_id=alert_level_id)
            from iot_app.services.alert_history_service import search_alert_histories
            search_alert_histories(search_params=search_params, user_id=user_id)
            return mock_query.filter.call_count

        # Act & Assert
        assert _run(2) > _run(None)

    @patch(f"{MODULE}.AlertHistoryByUser")
    @patch(f"{MODULE}.db")
    def test_alert_status_all_selected_returns_all_statuses(self, mock_db, _mock_model):
        """3.1.1.3: alert_status_id=None（すべて選択）の場合、全ステータスのアラートが返される
        UI仕様書 (2-7): 「すべて」がデフォルト選択
        """
        # Arrange
        user_id = 10
        search_params = _make_default_search_params(alert_status_id=None)
        mock_histories = [
            _make_mock_alert_history(alert_history_id=1, alert_status_name="発生中"),
            _make_mock_alert_history(alert_history_id=2, alert_status_name="復旧済み"),
        ]
        _setup_mock_query(mock_db, count=2, results=mock_histories)

        # Act
        from iot_app.services.alert_history_service import search_alert_histories
        result_list, total = search_alert_histories(search_params=search_params, user_id=user_id)

        # Assert: 全ステータスが返される
        assert isinstance(total, int)
        assert len(result_list) == 2
        statuses = {h.alert_status_name for h in result_list}
        assert {"発生中", "復旧済み"} == statuses

    @patch(f"{MODULE}.AlertHistoryByUser")
    @patch(f"{MODULE}.db")
    def test_alert_status_all_selected_has_fewer_filters_than_specific(self, mock_db, _mock_model):
        """3.1.1.3: alert_status_id=None の場合、具体値指定より filter() 呼び出し回数が少ない"""
        # Arrange
        user_id = 10

        def _run(alert_status_id):
            mock_query = _setup_mock_query(mock_db)
            search_params = _make_default_search_params(alert_status_id=alert_status_id)
            from iot_app.services.alert_history_service import search_alert_histories
            search_alert_histories(search_params=search_params, user_id=user_id)
            return mock_query.filter.call_count

        # Act & Assert
        assert _run(1) > _run(None)


# =============================================================================
# 3.1.1 search_alert_histories — ソート
# =============================================================================

@pytest.mark.unit
class TestSearchAlertHistoriesSorting:
    """3.1.1.1 ソート機能

    ワークフロー仕様書「全体ソート」:
      sort_by, order パラメータを使ってサーバーサイドで全体ソートを行う。
      デフォルトは alert_occurrence_datetime 降順（最新が上）。
      第二ソートキー: alert_history_id（主ソートと同方向）
    """

    @patch(f"{MODULE}.AlertHistoryByUser")
    @patch(f"{MODULE}.db")
    def test_desc_order_applies_descending_sort(self, mock_db, _mock_model):
        """3.1.1.1: order='desc' の場合、order_by が呼ばれる（降順）"""
        # Arrange
        user_id = 10
        search_params = _make_default_search_params(
            sort_by="alert_occurrence_datetime", order="desc"
        )
        mock_query = _setup_mock_query(mock_db)

        # Act
        from iot_app.services.alert_history_service import search_alert_histories
        search_alert_histories(search_params=search_params, user_id=user_id)

        # Assert
        mock_query.order_by.assert_called()

    @patch(f"{MODULE}.AlertHistoryByUser")
    @patch(f"{MODULE}.db")
    def test_asc_order_applies_ascending_sort(self, mock_db, _mock_model):
        """3.1.1.1: order='asc' の場合、order_by が呼ばれる（昇順）"""
        # Arrange
        user_id = 10
        search_params = _make_default_search_params(
            sort_by="alert_occurrence_datetime", order="asc"
        )
        mock_query = _setup_mock_query(mock_db)

        # Act
        from iot_app.services.alert_history_service import search_alert_histories
        search_alert_histories(search_params=search_params, user_id=user_id)

        # Assert
        mock_query.order_by.assert_called()

    @pytest.mark.parametrize("sort_by", [
        "device_name",
        "device_location",
        "alert_name",
        "alert_level_id",
        "alert_status_id",
    ])
    @patch(f"{MODULE}.AlertHistoryByUser")
    @patch(f"{MODULE}.db")
    def test_non_default_sort_by_applies_dynamic_sort(self, mock_db, _mock_model, sort_by):
        """3.1.1.1: sort_by にデフォルト以外のカラムを指定した場合も order_by が呼ばれる
        UI仕様書 (2-8) ソート項目: sort_item_master から動的取得。
        UI仕様書 (5) データテーブル ソート可カラム:
          device_name, device_location, alert_name, alert_level, alert_status
        """
        # Arrange
        user_id = 10
        search_params = _make_default_search_params(sort_by=sort_by, order="desc")
        mock_query = _setup_mock_query(mock_db)

        # Act
        from iot_app.services.alert_history_service import search_alert_histories
        search_alert_histories(search_params=search_params, user_id=user_id)

        # Assert
        mock_query.order_by.assert_called()

    @pytest.mark.parametrize("sort_by,order", [
        ("device_name",               "asc"),
        ("device_name",               "desc"),
        ("device_location",           "asc"),
        ("device_location",           "desc"),
        ("alert_name",                "asc"),
        ("alert_occurrence_datetime", "asc"),
        ("alert_occurrence_datetime", "desc"),
    ])
    @patch(f"{MODULE}.AlertHistoryByUser")
    @patch(f"{MODULE}.db")
    def test_sort_by_and_order_combination_applies_sort(self, mock_db, _mock_model, sort_by, order):
        """3.1.1.1: sort_by と order の組み合わせが変わっても order_by が正しく呼ばれる
        UI仕様書 (2-8)(2-9): ソート項目（動的）× ソート順（昇順/降順）の全組み合わせ。
        """
        # Arrange
        user_id = 10
        search_params = _make_default_search_params(sort_by=sort_by, order=order)
        mock_query = _setup_mock_query(mock_db)

        # Act
        from iot_app.services.alert_history_service import search_alert_histories
        result_list, total = search_alert_histories(search_params=search_params, user_id=user_id)

        # Assert
        mock_query.order_by.assert_called()
        assert isinstance(result_list, list)
        assert isinstance(total, int)

    @patch(f"{MODULE}.AlertHistoryByUser")
    @patch(f"{MODULE}.db")
    def test_second_sort_key_applied(self, mock_db, _mock_model):
        """3.1.1.1: 第二ソートキー（alert_history_id）が主ソートと同方向で適用されること
        ワークフロー仕様書 SQL:
          ORDER BY {sort_by} {order}, ah.alert_history_id {order} -- 第二ソートキー
        """
        # Arrange
        user_id = 10
        search_params = _make_default_search_params(
            sort_by="alert_occurrence_datetime", order="desc"
        )
        mock_query = _setup_mock_query(mock_db)

        # Act
        from iot_app.services.alert_history_service import search_alert_histories
        search_alert_histories(search_params=search_params, user_id=user_id)

        # Assert: order_by が主ソートキー + alert_history_id の2つ以上の引数で呼ばれること
        mock_query.order_by.assert_called()
        call_args = mock_query.order_by.call_args
        assert len(call_args.args) >= 2, (
            "order_by は主ソートキーと第二ソートキー(alert_history_id)の"
            "2つ以上の引数で呼ばれる必要があります"
        )


# =============================================================================
# 3.1.3 search_alert_histories — ページネーション
# =============================================================================

@pytest.mark.unit
class TestSearchAlertHistoriesPagination:
    """3.1.3.1 ページネーション

    ワークフロー仕様書:
      1ページ 25件固定（ITEM_PER_PAGE）
      OFFSET = (page - 1) * per_page
    """

    @patch(f"{MODULE}.AlertHistoryByUser")
    @patch(f"{MODULE}.db")
    def test_limit_is_per_page(self, mock_db, _mock_model):
        """3.1.3.1: limit に per_page（25）が渡されること"""
        # Arrange
        user_id = 10
        search_params = _make_default_search_params(page=1, per_page=25)
        mock_query = _setup_mock_query(mock_db)

        # Act
        from iot_app.services.alert_history_service import search_alert_histories
        search_alert_histories(search_params=search_params, user_id=user_id)

        # Assert
        mock_query.limit.assert_called_once_with(25)

    @patch(f"{MODULE}.AlertHistoryByUser")
    @patch(f"{MODULE}.db")
    def test_page_1_offset_is_0(self, mock_db, _mock_model):
        """3.1.3.1: page=1 の場合、offset=0 となること
        OFFSET = (1 - 1) * 25 = 0
        """
        # Arrange
        user_id = 10
        search_params = _make_default_search_params(page=1, per_page=25)
        mock_query = _setup_mock_query(mock_db)

        # Act
        from iot_app.services.alert_history_service import search_alert_histories
        search_alert_histories(search_params=search_params, user_id=user_id)

        # Assert
        mock_query.offset.assert_called_once_with(0)

    @patch(f"{MODULE}.AlertHistoryByUser")
    @patch(f"{MODULE}.db")
    def test_page_2_offset_is_per_page(self, mock_db, _mock_model):
        """3.1.3.1: page=2 の場合、offset=25 となること
        OFFSET = (2 - 1) * 25 = 25
        """
        # Arrange
        user_id = 10
        search_params = _make_default_search_params(page=2, per_page=25)
        mock_query = _setup_mock_query(mock_db, count=30)

        # Act
        from iot_app.services.alert_history_service import search_alert_histories
        search_alert_histories(search_params=search_params, user_id=user_id)

        # Assert
        mock_query.offset.assert_called_once_with(25)

    @patch(f"{MODULE}.AlertHistoryByUser")
    @patch(f"{MODULE}.db")
    def test_page_3_offset_is_50(self, mock_db, _mock_model):
        """3.1.3.1: page=3 の場合、offset=50 となること
        OFFSET = (3 - 1) * 25 = 50
        """
        # Arrange
        user_id = 10
        search_params = _make_default_search_params(page=3, per_page=25)
        mock_query = _setup_mock_query(mock_db, count=60)

        # Act
        from iot_app.services.alert_history_service import search_alert_histories
        search_alert_histories(search_params=search_params, user_id=user_id)

        # Assert
        mock_query.offset.assert_called_once_with(50)


# =============================================================================
# 2.1 / 3.1.4 search_alert_histories — 戻り値
# =============================================================================

@pytest.mark.unit
class TestSearchAlertHistoriesReturnValue:
    """2.1.2/2.1.3 / 3.1.4 戻り値の型と内容

    search_alert_histories は (list, int) のタプルを返す。
    """

    @patch(f"{MODULE}.AlertHistoryByUser")
    @patch(f"{MODULE}.db")
    def test_returns_tuple_of_list_and_int(self, mock_db, _mock_model):
        """2.1.2: 戻り値が (list, int) のタプルであること"""
        # Arrange
        user_id = 10
        search_params = _make_default_search_params()
        _setup_mock_query(
            mock_db,
            count=5,
            results=[_make_mock_alert_history(alert_history_id=i) for i in range(1, 6)],
        )

        # Act
        from iot_app.services.alert_history_service import search_alert_histories
        result = search_alert_histories(search_params=search_params, user_id=user_id)

        # Assert
        assert isinstance(result, tuple)
        assert len(result) == 2
        result_list, total = result
        assert isinstance(result_list, list)
        assert isinstance(total, int)

    @patch(f"{MODULE}.AlertHistoryByUser")
    @patch(f"{MODULE}.db")
    def test_total_reflects_count_query(self, mock_db, _mock_model):
        """2.1.3: total が count() の結果であること（全件数、ページング後の件数ではない）"""
        # Arrange
        user_id = 10
        search_params = _make_default_search_params(page=2, per_page=25)
        _setup_mock_query(mock_db, count=100, results=[_make_mock_alert_history()])

        # Act
        from iot_app.services.alert_history_service import search_alert_histories
        _, total = search_alert_histories(search_params=search_params, user_id=user_id)

        # Assert: total は全件数（count()の結果）
        assert total == 100

    @patch(f"{MODULE}.AlertHistoryByUser")
    @patch(f"{MODULE}.db")
    def test_empty_result_returns_empty_list_and_zero(self, mock_db, _mock_model):
        """3.1.4.2: 検索結果が0件の場合、([], 0) を返すこと"""
        # Arrange
        user_id = 10
        search_params = _make_default_search_params()
        _setup_mock_query(mock_db, count=0, results=[])

        # Act
        from iot_app.services.alert_history_service import search_alert_histories
        result_list, total = search_alert_histories(search_params=search_params, user_id=user_id)

        # Assert
        assert result_list == []
        assert total == 0

    @patch(f"{MODULE}.AlertHistoryByUser")
    @patch(f"{MODULE}.db")
    def test_result_list_contains_alert_history_objects(self, mock_db, _mock_model):
        """3.1.4.1: 戻り値リストが AlertHistoryByUser オブジェクトを含むこと"""
        # Arrange
        user_id = 10
        search_params = _make_default_search_params()
        mock_history = _make_mock_alert_history()
        _setup_mock_query(mock_db, count=1, results=[mock_history])

        # Act
        from iot_app.services.alert_history_service import search_alert_histories
        result_list, total = search_alert_histories(search_params=search_params, user_id=user_id)

        # Assert
        assert len(result_list) == 1
        assert result_list[0] is mock_history
        assert total == 1

    @patch(f"{MODULE}.AlertHistoryByUser")
    @patch(f"{MODULE}.db")
    def test_multiple_pages_total_reflects_all_data(self, mock_db, _mock_model):
        """3.1.4.1: 複数ページにまたがるデータがある場合、total が全件数を返すこと"""
        # Arrange
        user_id = 10
        search_params = _make_default_search_params(page=1, per_page=25)
        _setup_mock_query(
            mock_db,
            count=75,
            results=[_make_mock_alert_history(alert_history_id=i) for i in range(1, 26)],
        )

        # Act
        from iot_app.services.alert_history_service import search_alert_histories
        result_list, total = search_alert_histories(search_params=search_params, user_id=user_id)

        # Assert
        assert total == 75
        assert len(result_list) == 25


# =============================================================================
# 1.3.1 search_alert_histories — エラーハンドリング
# =============================================================================

@pytest.mark.unit
class TestSearchAlertHistoriesErrorHandling:
    """1.3.1 エラーハンドリング — 例外伝播"""

    @patch(f"{MODULE}.AlertHistoryByUser")
    @patch(f"{MODULE}.db")
    def test_propagates_db_exception(self, mock_db, _mock_model):
        """1.3.1: DB例外が発生した場合、上位へ伝播されること"""
        from sqlalchemy.exc import SQLAlchemyError

        # Arrange
        user_id = 10
        search_params = _make_default_search_params()
        mock_db.session.query.side_effect = SQLAlchemyError("DB Timeout")

        # Act & Assert
        from iot_app.services.alert_history_service import search_alert_histories
        with pytest.raises(SQLAlchemyError):
            search_alert_histories(search_params=search_params, user_id=user_id)


# =============================================================================
# 2.2 / 3.1.5 get_alert_history_detail — 詳細取得
# =============================================================================

@pytest.mark.unit
class TestGetAlertHistoryDetail:
    """2.2 / 3.1.5 get_alert_history_detail — アラート履歴詳細取得

    ワークフロー仕様書「詳細表示」:
      v_alert_history_by_user に alert_history_uuid + user_id でフィルタ。
      該当なし → None（呼び出し元が404ハンドリング）
    """

    @patch(f"{MODULE}.AlertHistoryByUser")
    @patch(f"{MODULE}.db")
    def test_returns_alert_history_by_uuid(self, mock_db, _mock_model):
        """2.2.1: alert_history_uuid に一致するアラート履歴が返されること"""
        # Arrange
        alert_history_uuid = "uuid-001"
        user_id = 10
        mock_history = _make_mock_alert_history(alert_history_uuid=alert_history_uuid)
        _setup_mock_query(mock_db, results=[mock_history])

        # Act
        from iot_app.services.alert_history_service import get_alert_history_detail
        result = get_alert_history_detail(
            alert_history_uuid=alert_history_uuid, user_id=user_id
        )

        # Assert
        assert result is mock_history

    @patch(f"{MODULE}.AlertHistoryByUser")
    @patch(f"{MODULE}.db")
    def test_user_id_scope_applied(self, mock_db, _mock_model):
        """2.2.2: user_id でスコープが適用されること（他ユーザーのデータが取得されない）"""
        # Arrange
        alert_history_uuid = "uuid-001"
        user_id = 10
        mock_query = _setup_mock_query(mock_db)

        # Act
        from iot_app.services.alert_history_service import get_alert_history_detail
        get_alert_history_detail(
            alert_history_uuid=alert_history_uuid, user_id=user_id
        )

        # Assert: filter が呼ばれていること（user_id スコープ含む）
        mock_query.filter.assert_called()

    @patch(f"{MODULE}.AlertHistoryByUser")
    @patch(f"{MODULE}.db")
    def test_delete_flag_filter_applied(self, mock_db, _mock_model):
        """2.2.2: delete_flag=False のフィルタが適用されること"""
        # Arrange
        alert_history_uuid = "uuid-001"
        user_id = 10
        mock_query = _setup_mock_query(mock_db)

        # Act
        from iot_app.services.alert_history_service import get_alert_history_detail
        get_alert_history_detail(
            alert_history_uuid=alert_history_uuid, user_id=user_id
        )

        # Assert
        assert mock_query.filter.call_count >= 1

    @patch(f"{MODULE}.AlertHistoryByUser")
    @patch(f"{MODULE}.db")
    def test_returns_none_when_not_found(self, mock_db, _mock_model):
        """2.2.3: 該当するアラート履歴が存在しない場合、None を返すこと
        ワークフロー仕様書: DB取得失敗 → 404エラー（呼び出し元でハンドリング）
        """
        # Arrange
        alert_history_uuid = "uuid-not-exist"
        user_id = 10
        _setup_mock_query(mock_db, results=[])

        # Act
        from iot_app.services.alert_history_service import get_alert_history_detail
        result = get_alert_history_detail(
            alert_history_uuid=alert_history_uuid, user_id=user_id
        )

        # Assert
        assert result is None

    @patch(f"{MODULE}.AlertHistoryByUser")
    @patch(f"{MODULE}.db")
    def test_returns_none_when_different_user(self, mock_db, _mock_model):
        """2.2.3: 異なる user_id で検索した場合、None を返すこと（スコープ外）
        VIEWが user_id スコープ外のデータを除外する
        """
        # Arrange
        alert_history_uuid = "uuid-001"
        other_user_id = 99
        _setup_mock_query(mock_db, results=[])  # VIEWがスコープ外を除外

        # Act
        from iot_app.services.alert_history_service import get_alert_history_detail
        result = get_alert_history_detail(
            alert_history_uuid=alert_history_uuid, user_id=other_user_id
        )

        # Assert
        assert result is None

    @patch(f"{MODULE}.AlertHistoryByUser")
    @patch(f"{MODULE}.db")
    def test_uuid_filter_applied(self, mock_db, _mock_model):
        """1.3.5: alert_history_uuid でフィルタされること"""
        # Arrange
        alert_history_uuid = "uuid-target"
        user_id = 10
        mock_history = _make_mock_alert_history(alert_history_uuid=alert_history_uuid)
        mock_query = _setup_mock_query(mock_db, results=[mock_history])

        # Act
        from iot_app.services.alert_history_service import get_alert_history_detail
        get_alert_history_detail(
            alert_history_uuid=alert_history_uuid, user_id=user_id
        )

        # Assert: filter が呼ばれたこと
        mock_query.filter.assert_called()

    @patch(f"{MODULE}.AlertHistoryByUser")
    @patch(f"{MODULE}.db")
    def test_propagates_db_exception(self, mock_db, _mock_model):
        """1.3.1: 詳細取得時にDBで例外が発生した場合、例外が上位へ伝播される"""
        # Arrange
        alert_history_uuid = "uuid-001"
        user_id = 10
        mock_db.session.query.side_effect = Exception("DB Timeout")

        # Act & Assert
        from iot_app.services.alert_history_service import get_alert_history_detail
        with pytest.raises(Exception, match="DB Timeout"):
            get_alert_history_detail(
                alert_history_uuid=alert_history_uuid, user_id=user_id
            )


# =============================================================================
# 1.4 ログ出力機能
# =============================================================================

@pytest.mark.unit
class TestLogging:
    """1.4 ログ出力機能

    対象観点:
      - 1.4.1.1 ERRORレベル出力（DB例外発生時）
      - 1.4.1.3 INFOレベル出力（正常処理完了時）
      - 1.4.1.4 DEBUGレベル出力（検索条件・件数等の詳細情報）

    対象外観点:
      - 1.4.1.2 WARNレベル: 400系エラーはView層（バリデーション）の責務
      - 1.4.2 必須項目出力: リクエストID/エンドポイント/HTTP情報はView層の責務
      - 1.4.3 機密情報非出力: アラート履歴データにパスワード・トークン等は含まれない
      - 1.4.4 マスキング処理: アラート履歴データにメール・電話番号・氏名は含まれない
    """

    @patch(f"{MODULE}.AlertHistoryByUser")
    @patch(f"{MODULE}.db")
    def test_search_logs_error_when_db_fails(self, mock_db, _mock_model, caplog):
        """1.4.1.1: search_alert_histories でDB例外が発生した場合、ERRORレベルでログが出力される"""
        import logging
        from sqlalchemy.exc import SQLAlchemyError

        # Arrange
        mock_db.session.query.side_effect = SQLAlchemyError("Connection timeout")
        search_params = _make_default_search_params()
        user_id = 10

        # Act & Assert
        from iot_app.services.alert_history_service import search_alert_histories
        with caplog.at_level(logging.ERROR, logger=MODULE):
            with pytest.raises(SQLAlchemyError):
                search_alert_histories(search_params=search_params, user_id=user_id)
        assert any(r.levelno == logging.ERROR for r in caplog.records)

    @patch(f"{MODULE}.AlertHistoryByUser")
    @patch(f"{MODULE}.db")
    def test_search_logs_info_on_success(self, mock_db, _mock_model, caplog):
        """1.4.1.3: search_alert_histories が正常完了した場合、INFOレベルでログが出力される"""
        import logging

        # Arrange
        _setup_mock_query(mock_db, count=0, results=[])
        search_params = _make_default_search_params()
        user_id = 10

        # Act
        from iot_app.services.alert_history_service import search_alert_histories
        with caplog.at_level(logging.INFO, logger=MODULE):
            search_alert_histories(search_params=search_params, user_id=user_id)

        # Assert
        assert any(r.levelno == logging.INFO for r in caplog.records)

    @patch(f"{MODULE}.AlertHistoryByUser")
    @patch(f"{MODULE}.db")
    def test_search_logs_debug_with_result_count(self, mock_db, _mock_model, caplog):
        """1.4.1.4: search_alert_histories が正常完了した場合、DEBUGレベルで件数情報がログ出力される"""
        import logging

        # Arrange
        _setup_mock_query(
            mock_db,
            count=3,
            results=[_make_mock_alert_history(alert_history_id=i) for i in range(1, 4)],
        )
        search_params = _make_default_search_params()
        user_id = 10

        # Act
        from iot_app.services.alert_history_service import search_alert_histories
        with caplog.at_level(logging.DEBUG, logger=MODULE):
            search_alert_histories(search_params=search_params, user_id=user_id)

        # Assert
        assert any(r.levelno == logging.DEBUG for r in caplog.records)

    @patch(f"{MODULE}.AlertHistoryByUser")
    @patch(f"{MODULE}.db")
    def test_get_detail_logs_error_when_db_fails(self, mock_db, _mock_model, caplog):
        """1.4.1.1: get_alert_history_detail でDB例外が発生した場合、ERRORレベルでログが出力される"""
        import logging

        # Arrange
        mock_db.session.query.side_effect = Exception("DB Error")
        alert_history_uuid = "uuid-001"
        user_id = 10

        # Act & Assert
        from iot_app.services.alert_history_service import get_alert_history_detail
        with caplog.at_level(logging.ERROR, logger=MODULE):
            with pytest.raises(Exception, match="DB Error"):
                get_alert_history_detail(
                    alert_history_uuid=alert_history_uuid, user_id=user_id
                )
        assert any(r.levelno == logging.ERROR for r in caplog.records)
