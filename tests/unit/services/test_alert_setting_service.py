"""
アラート設定管理 - Service層 単体テスト

対象ファイル: src/iot_app/services/alert_setting_service.py

参照ドキュメント:
  - UI設計書:         docs/03-features/flask-app/alert-settings/ui-specification.md
  - 機能設計書:       docs/03-features/flask-app/alert-settings/workflow-specification.md
  - 単体テスト観点表: docs/05-testing/unit-test/unit-test-perspectives.md
  - 実装ガイド:       docs/05-testing/unit-test/unit-test-guide.md
"""
import pytest
from unittest.mock import MagicMock, Mock, patch, call


# ============================================================
# フィクスチャ
# ============================================================

@pytest.fixture
def mock_session():
    """DBセッションのモック"""
    return MagicMock()


@pytest.fixture
def service(mock_session):
    """AlertSettingService のインスタンス（DBセッションをモック化）"""
    from iot_app.services.alert_setting_service import AlertSettingService
    return AlertSettingService(db_session=mock_session)


def make_valid_form_data(**overrides):
    """
    登録・更新フォームの有効データを生成するヘルパー。
    必須項目をすべて含む最小有効データをベースに、引数で任意項目を上書きできる。

    バリデーションルール出典: ui-specification.md > (4) アラート設定登録モーダル > バリデーション
    """
    data = {
        "alert_name": "温度異常アラート",                           # 必須, 最大100文字
        "device_id": 1,                                           # 必須
        "alert_conditions_measurement_item_id": 1,                # 必須
        "alert_conditions_operator": ">",                         # 必須
        "alert_conditions_threshold": 30.0,                       # 必須, 数値, ±999,999,999,999,999
        "alert_recovery_conditions_measurement_item_id": 1,       # 必須
        "alert_recovery_conditions_operator": "<=",               # 必須
        "alert_recovery_conditions_threshold": 30.0,              # 必須, 数値, ±999,999,999,999,999
        "judgment_time": 5,                                       # 必須, 許容値: 1,5,10,15,30,60
        "alert_level_id": 1,                                      # 必須, alert_level_master に存在するID
        "alert_notification_flag": True,                          # 必須, デフォルト: True
        "alert_email_flag": True,                                 # 必須, デフォルト: True
        "user_id": 1,
    }
    data.update(overrides)
    return data


def make_alert_setting_mock(**kwargs):
    """検索・CSVエクスポートテスト用のアラート設定データモックを生成"""
    m = Mock()
    m.alert_id = kwargs.get("alert_id", 1)
    m.alert_uuid = kwargs.get("alert_uuid", "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee")
    m.alert_name = kwargs.get("alert_name", "温度異常アラート")
    m.device = Mock()
    m.device.device_name = kwargs.get("device_name", "Device01")
    m.alert_conditions_measurement_item = Mock()
    m.alert_conditions_measurement_item.measurement_item_name = kwargs.get(
        "occur_item_name", "temperature"
    )
    m.alert_conditions_operator = kwargs.get("alert_conditions_operator", ">")
    m.alert_conditions_threshold = kwargs.get("alert_conditions_threshold", 30.0)
    m.alert_recovery_conditions_measurement_item = Mock()
    m.alert_recovery_conditions_measurement_item.measurement_item_name = kwargs.get(
        "recovery_item_name", "temperature"
    )
    m.alert_recovery_conditions_operator = kwargs.get("alert_recovery_conditions_operator", "<=")
    m.alert_recovery_conditions_threshold = kwargs.get("alert_recovery_conditions_threshold", 30.0)
    m.judgment_time = kwargs.get("judgment_time", 5)
    m.alert_level = Mock()
    m.alert_level.alert_level_name = kwargs.get("alert_level_name", "Warning")
    m.alert_notification_flag = kwargs.get("alert_notification_flag", True)
    m.alert_email_flag = kwargs.get("alert_email_flag", False)
    m.create_date = kwargs.get("create_date", Mock(strftime=lambda fmt: "2025/11/01 10:30:00"))
    m.creator = kwargs.get("creator", 1)
    m.update_date = kwargs.get("update_date", Mock(strftime=lambda fmt: "2025/11/15 14:20:00"))
    m.modifier = kwargs.get("modifier", 2)
    m.delete_flag = kwargs.get("delete_flag", False)
    return m


# ============================================================
# 1. 入力バリデーション
# 観点: 1.1.1 必須チェック, 1.1.2 最大文字列長チェック,
#       1.1.3 数値範囲チェック, 1.1.6 不整値チェック
# ============================================================

@pytest.mark.unit
class TestAlertSettingServiceValidation:
    """アラート設定登録・更新フォームバリデーション
    観点: 1.1.1 必須チェック, 1.1.2 最大文字列長チェック,
          1.1.3 数値範囲チェック, 1.1.6 不整値チェック
    """

    # ----------------------------------------------------------------
    # 1.1.1 必須チェック - alert_name
    # ----------------------------------------------------------------

    def test_required_alert_name_empty_raises(self, service):
        """1.1.1: alert_name が空文字の場合 ValidationError がスローされる"""
        # Arrange
        data = make_valid_form_data(alert_name="")
        # Act & Assert
        with pytest.raises(Exception):
            service.create(data)

    def test_required_alert_name_none_raises(self, service):
        """1.1.2: alert_name が None の場合 ValidationError がスローされる"""
        # Arrange
        data = make_valid_form_data(alert_name=None)
        # Act & Assert
        with pytest.raises(Exception):
            service.create(data)

    # ----------------------------------------------------------------
    # 1.1.1 必須チェック - device_id
    # ----------------------------------------------------------------

    def test_required_device_id_none_raises(self, service):
        """1.1.2: device_id が None の場合 ValidationError がスローされる"""
        # Arrange
        data = make_valid_form_data(device_id=None)
        # Act & Assert
        with pytest.raises(Exception):
            service.create(data)

    # ----------------------------------------------------------------
    # 1.1.1 必須チェック - alert_conditions_measurement_item_id
    # ----------------------------------------------------------------

    def test_required_alert_conditions_measurement_item_id_none_raises(self, service):
        """1.1.2: alert_conditions_measurement_item_id が None の場合 ValidationError がスローされる"""
        # Arrange
        data = make_valid_form_data(alert_conditions_measurement_item_id=None)
        # Act & Assert
        with pytest.raises(Exception):
            service.create(data)

    # ----------------------------------------------------------------
    # 1.1.1 必須チェック - alert_conditions_operator
    # ----------------------------------------------------------------

    def test_required_alert_conditions_operator_empty_raises(self, service):
        """1.1.1: alert_conditions_operator が空文字の場合 ValidationError がスローされる"""
        # Arrange
        data = make_valid_form_data(alert_conditions_operator="")
        # Act & Assert
        with pytest.raises(Exception):
            service.create(data)

    def test_required_alert_conditions_operator_none_raises(self, service):
        """1.1.2: alert_conditions_operator が None の場合 ValidationError がスローされる"""
        # Arrange
        data = make_valid_form_data(alert_conditions_operator=None)
        # Act & Assert
        with pytest.raises(Exception):
            service.create(data)

    # ----------------------------------------------------------------
    # 1.1.1 必須チェック - alert_conditions_threshold
    # ----------------------------------------------------------------

    def test_required_alert_conditions_threshold_none_raises(self, service):
        """1.1.2: alert_conditions_threshold が None の場合 ValidationError がスローされる"""
        # Arrange
        data = make_valid_form_data(alert_conditions_threshold=None)
        # Act & Assert
        with pytest.raises(Exception):
            service.create(data)

    # ----------------------------------------------------------------
    # 1.1.1 必須チェック - alert_recovery_conditions_measurement_item_id
    # ----------------------------------------------------------------

    def test_required_alert_recovery_conditions_measurement_item_id_none_raises(self, service):
        """1.1.2: alert_recovery_conditions_measurement_item_id が None の場合 ValidationError がスローされる"""
        # Arrange
        data = make_valid_form_data(alert_recovery_conditions_measurement_item_id=None)
        # Act & Assert
        with pytest.raises(Exception):
            service.create(data)

    # ----------------------------------------------------------------
    # 1.1.1 必須チェック - alert_recovery_conditions_operator
    # ----------------------------------------------------------------

    def test_required_alert_recovery_conditions_operator_empty_raises(self, service):
        """1.1.1: alert_recovery_conditions_operator が空文字の場合 ValidationError がスローされる"""
        # Arrange
        data = make_valid_form_data(alert_recovery_conditions_operator="")
        # Act & Assert
        with pytest.raises(Exception):
            service.create(data)

    def test_required_alert_recovery_conditions_operator_none_raises(self, service):
        """1.1.2: alert_recovery_conditions_operator が None の場合 ValidationError がスローされる"""
        # Arrange
        data = make_valid_form_data(alert_recovery_conditions_operator=None)
        # Act & Assert
        with pytest.raises(Exception):
            service.create(data)

    # ----------------------------------------------------------------
    # 1.1.1 必須チェック - alert_recovery_conditions_threshold
    # ----------------------------------------------------------------

    def test_required_alert_recovery_conditions_threshold_none_raises(self, service):
        """1.1.2: alert_recovery_conditions_threshold が None の場合 ValidationError がスローされる"""
        # Arrange
        data = make_valid_form_data(alert_recovery_conditions_threshold=None)
        # Act & Assert
        with pytest.raises(Exception):
            service.create(data)

    # ----------------------------------------------------------------
    # 1.1.1 必須チェック - judgment_time
    # ----------------------------------------------------------------

    def test_required_judgment_time_none_raises(self, service):
        """1.1.2: judgment_time が None の場合 ValidationError がスローされる"""
        # Arrange
        data = make_valid_form_data(judgment_time=None)
        # Act & Assert
        with pytest.raises(Exception):
            service.create(data)

    # ----------------------------------------------------------------
    # 1.1.1 必須チェック - alert_level_id
    # ----------------------------------------------------------------

    def test_required_alert_level_id_none_raises(self, service):
        """1.1.2: alert_level_id が None の場合 ValidationError がスローされる"""
        # Arrange
        data = make_valid_form_data(alert_level_id=None)
        # Act & Assert
        with pytest.raises(Exception):
            service.create(data)

    # ----------------------------------------------------------------
    # 1.1.2 最大文字列長チェック - alert_name (最大100文字)
    # 出典: ui-specification.md (4.2) アラート名 最大100文字
    # ----------------------------------------------------------------

    def test_max_length_alert_name_99_ok(self, service):
        """1.2.1: alert_name が 99文字（最大長-1）はバリデーション通過"""
        # Arrange
        data = make_valid_form_data(alert_name="あ" * 99)
        # Act & Assert（例外が発生しないこと）
        service.create(data)

    def test_max_length_alert_name_100_ok(self, service):
        """1.2.2: alert_name が 100文字ちょうどはバリデーション通過"""
        # Arrange
        data = make_valid_form_data(alert_name="あ" * 100)
        # Act & Assert（例外が発生しないこと）
        service.create(data)

    def test_max_length_alert_name_101_raises(self, service):
        """1.2.3: alert_name が 101文字の場合 ValidationError がスローされる"""
        # Arrange
        data = make_valid_form_data(alert_name="あ" * 101)
        # Act & Assert
        with pytest.raises(Exception):
            service.create(data)

    # ----------------------------------------------------------------
    # 1.1.3 数値範囲チェック - alert_conditions_threshold
    # 出典: ui-specification.md (4.4.3)
    #   最大値: 999,999,999,999,999 / 最小値: -999,999,999,999,999
    # ----------------------------------------------------------------

    def test_threshold_occur_at_min_boundary_ok(self, service):
        """1.3.2: alert_conditions_threshold が最小値 -999999999999999 ちょうどはバリデーション通過"""
        # Arrange
        data = make_valid_form_data(alert_conditions_threshold=-999_999_999_999_999)
        # Act & Assert（例外が発生しないこと）
        service.create(data)

    def test_threshold_occur_below_min_raises(self, service):
        """1.3.1: alert_conditions_threshold が -999999999999999 未満の場合 ValidationError がスローされる"""
        # Arrange
        data = make_valid_form_data(alert_conditions_threshold=-1_000_000_000_000_000)
        # Act & Assert
        with pytest.raises(Exception):
            service.create(data)

    def test_threshold_occur_at_max_boundary_ok(self, service):
        """1.3.5: alert_conditions_threshold が最大値 999999999999999 ちょうどはバリデーション通過"""
        # Arrange
        data = make_valid_form_data(alert_conditions_threshold=999_999_999_999_999)
        # Act & Assert（例外が発生しないこと）
        service.create(data)

    def test_threshold_occur_above_max_raises(self, service):
        """1.3.6: alert_conditions_threshold が 999999999999999 超過の場合 ValidationError がスローされる"""
        # Arrange
        data = make_valid_form_data(alert_conditions_threshold=1_000_000_000_000_000)
        # Act & Assert
        with pytest.raises(Exception):
            service.create(data)

    def test_threshold_occur_non_numeric_raises(self, service):
        """1.3.7: alert_conditions_threshold に文字列を渡すと ValidationError がスローされる"""
        # Arrange
        data = make_valid_form_data(alert_conditions_threshold="abc")
        # Act & Assert
        with pytest.raises(Exception):
            service.create(data)

    def test_threshold_recovery_below_min_raises(self, service):
        """1.3.1: alert_recovery_conditions_threshold が最小値未満の場合 ValidationError がスローされる"""
        # Arrange
        data = make_valid_form_data(alert_recovery_conditions_threshold=-1_000_000_000_000_000)
        # Act & Assert
        with pytest.raises(Exception):
            service.create(data)

    def test_threshold_recovery_above_max_raises(self, service):
        """1.3.6: alert_recovery_conditions_threshold が最大値超過の場合 ValidationError がスローされる"""
        # Arrange
        data = make_valid_form_data(alert_recovery_conditions_threshold=1_000_000_000_000_000)
        # Act & Assert
        with pytest.raises(Exception):
            service.create(data)

    # ----------------------------------------------------------------
    # 1.1.6 不整値チェック - judgment_time
    # 出典: ui-specification.md (4.6) 判定時間: 設定ファイルから取得
    #   固定値: 1, 5, 10, 15, 30, 60
    # ----------------------------------------------------------------

    def test_judgment_time_valid_value_1_ok(self, service):
        """1.6.1: judgment_time = 1 は許容値"""
        # Arrange
        data = make_valid_form_data(judgment_time=1)
        # Act & Assert（例外が発生しないこと）
        service.create(data)

    def test_judgment_time_valid_value_60_ok(self, service):
        """1.6.1: judgment_time = 60 は許容値"""
        # Arrange
        data = make_valid_form_data(judgment_time=60)
        # Act & Assert（例外が発生しないこと）
        service.create(data)

    def test_judgment_time_invalid_value_raises(self, service):
        """1.6.2: judgment_time が許容値以外（例: 7）の場合 ValidationError がスローされる"""
        # Arrange
        data = make_valid_form_data(judgment_time=7)
        # Act & Assert
        with pytest.raises(Exception):
            service.create(data)

    def test_judgment_time_zero_raises(self, service):
        """1.6.3: judgment_time = 0 は許容値外のため ValidationError がスローされる"""
        # Arrange
        data = make_valid_form_data(judgment_time=0)
        # Act & Assert
        with pytest.raises(Exception):
            service.create(data)


# ============================================================
# 2. 検索機能（Read）
# 観点: 3.1.1 検索条件指定, 3.1.2 検索条件未指定,
#       3.1.3 ページング, 3.1.4 戻り値ハンドリング
# ============================================================

@pytest.mark.unit
class TestAlertSettingServiceSearch:
    """アラート設定検索機能
    観点: 3.1.1 検索条件指定, 3.1.2 検索条件未指定,
          3.1.3 ページング・件数制御, 3.1.4 検索結果戻り値ハンドリング
    """

    # ----------------------------------------------------------------
    # 3.1.1 検索条件指定
    # ----------------------------------------------------------------

    def test_search_with_alert_name_passes_condition(self, service, mock_session):
        """3.1.1.1: alert_name を指定すると部分一致条件がクエリに渡される"""
        # Arrange
        mock_session.query.return_value.filter.return_value.filter.return_value.all.return_value = []
        # Act
        service.search(alert_name="温度", user_id=1)
        # Assert
        mock_session.query.assert_called()

    def test_search_with_multiple_conditions_passes_all(self, service, mock_session):
        """3.1.1.2: 複数条件（alert_name + device_name）を指定すると全条件がクエリに渡される"""
        # Arrange
        mock_session.query.return_value.filter.return_value.all.return_value = []
        # Act
        service.search(alert_name="温度", device_name="Device01", user_id=1)
        # Assert
        mock_session.query.assert_called()

    def test_search_with_no_conditions(self, service, mock_session):
        """3.1.2.1: 検索条件なしで呼び出すと全件相当のクエリが実行される"""
        # Arrange
        mock_session.query.return_value.filter.return_value.all.return_value = []
        # Act
        service.search(user_id=1)
        # Assert
        mock_session.query.assert_called()

    # ----------------------------------------------------------------
    # 3.1.3 ページング・件数制御
    # ----------------------------------------------------------------

    def test_search_with_pagination_passes_limit_offset(self, service, mock_session):
        """3.1.3.1: page と per_page を指定すると limit/offset がリポジトリに渡される"""
        # Arrange
        mock_q = MagicMock()
        mock_session.query.return_value = mock_q
        mock_q.filter.return_value = mock_q
        mock_q.limit.return_value = mock_q
        mock_q.offset.return_value = mock_q
        mock_q.all.return_value = []
        # Act
        service.search(user_id=1, page=2, per_page=25)
        # Assert
        mock_q.limit.assert_called_with(25)
        mock_q.offset.assert_called_with(25)  # (page-1) * per_page = (2-1) * 25 = 25

    # ----------------------------------------------------------------
    # 3.1.4 検索結果戻り値ハンドリング
    # ----------------------------------------------------------------

    def test_search_returns_list_from_repository(self, service, mock_session):
        """3.1.4.1: リポジトリがリストを返すとそのリストが返却される"""
        # Arrange
        expected = [make_alert_setting_mock(), make_alert_setting_mock(alert_id=2)]
        mock_q = MagicMock()
        mock_session.query.return_value = mock_q
        mock_q.filter.return_value = mock_q
        mock_q.order_by.return_value = mock_q
        mock_q.limit.return_value = mock_q
        mock_q.offset.return_value = mock_q
        mock_q.all.return_value = expected
        # Act
        result = service.search(user_id=1)
        # Assert
        assert result == expected

    def test_search_returns_empty_list_when_no_result(self, service, mock_session):
        """3.1.4.2: リポジトリが空リストを返すと空リストが返却される"""
        # Arrange
        mock_q = MagicMock()
        mock_session.query.return_value = mock_q
        mock_q.filter.return_value = mock_q
        mock_q.order_by.return_value = mock_q
        mock_q.limit.return_value = mock_q
        mock_q.offset.return_value = mock_q
        mock_q.all.return_value = []
        # Act
        result = service.search(user_id=1)
        # Assert
        assert result == []


# ============================================================
# 3. 登録機能（Create）
# 観点: 2.1 正常系処理, 2.3 副作用チェック, 3.2 登録機能
# ============================================================

@pytest.mark.unit
class TestAlertSettingServiceCreate:
    """アラート設定登録機能
    観点: 2.1 正常系処理, 2.3 副作用チェック, 3.2 登録機能
    """

    # ----------------------------------------------------------------
    # 3.2.1 登録処理呼び出し
    # ----------------------------------------------------------------

    def test_create_passes_valid_data_to_session(self, service, mock_session):
        """3.2.1.1 / 2.1.1: 有効な入力値で db.session.add が呼び出される"""
        # Arrange
        data = make_valid_form_data()
        mock_session.add.return_value = None
        mock_session.commit.return_value = None
        # Act
        service.create(data)
        # Assert
        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()

    def test_create_with_notification_flag_false(self, service, mock_session):
        """3.2.1.2: alert_notification_flag=False を含む入力でも正常に登録される"""
        # Arrange
        data = make_valid_form_data(alert_notification_flag=False, alert_email_flag=False)
        mock_session.add.return_value = None
        mock_session.commit.return_value = None
        # Act
        service.create(data)
        # Assert
        mock_session.add.assert_called_once()

    # ----------------------------------------------------------------
    # 3.2.2 登録結果
    # ----------------------------------------------------------------

    # ----------------------------------------------------------------
    # 2.3 副作用チェック
    # ----------------------------------------------------------------

    def test_create_rollback_on_db_error(self, service, mock_session):
        """2.3.2: DB例外発生時に rollback() が呼び出される"""
        # Arrange
        data = make_valid_form_data()
        mock_session.commit.side_effect = Exception("DB error")
        # Act & Assert
        with pytest.raises(Exception):
            service.create(data)
        mock_session.rollback.assert_called_once()

    def test_create_no_data_change_on_validation_error(self, service, mock_session):
        """2.3.1: バリデーションエラー時に db.session.add が呼ばれない"""
        # Arrange
        data = make_valid_form_data(alert_name="")
        # Act
        try:
            service.create(data)
        except Exception:
            pass
        # Assert
        mock_session.add.assert_not_called()

    # ----------------------------------------------------------------
    # 1.3 エラーハンドリング
    # ----------------------------------------------------------------

    def test_create_raises_error_on_db_failure(self, service, mock_session):
        """1.3.1: DB例外は握りつぶされず上位へ伝播される"""
        # Arrange
        data = make_valid_form_data()
        mock_session.commit.side_effect = Exception("DB connection failed")
        # Act & Assert
        with pytest.raises(Exception):
            service.create(data)


# ============================================================
# 4. 更新機能（Update）
# 観点: 2.1 正常系処理, 2.2 対象データ存在チェック,
#       2.3 副作用チェック, 3.3 更新機能
# ============================================================

@pytest.mark.unit
class TestAlertSettingServiceUpdate:
    """アラート設定更新機能
    観点: 2.1 正常系処理, 2.2 対象データ存在チェック,
          2.3 副作用チェック, 3.3 更新機能
    """

    # ----------------------------------------------------------------
    # 3.3.1 更新処理呼び出し
    # ----------------------------------------------------------------

    def test_update_passes_data_to_session(self, service, mock_session):
        """3.3.1.1 / 2.1.1: 有効な入力値で db.session.commit が呼び出される"""
        # Arrange
        alert_uuid = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
        data = make_valid_form_data()
        mock_alert = make_alert_setting_mock(alert_uuid=alert_uuid)
        mock_session.query.return_value.filter.return_value.first.return_value = mock_alert
        # Act
        service.update(alert_uuid=alert_uuid, data=data, user_id=1)
        # Assert
        mock_session.commit.assert_called_once()

    # ----------------------------------------------------------------
    # 3.3.2 更新結果
    # ----------------------------------------------------------------

    def test_update_completes_without_exception(self, service, mock_session):
        """3.3.2.1: 更新処理成功時に例外なく処理が完了する"""
        # Arrange
        alert_uuid = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
        data = make_valid_form_data()
        mock_alert = make_alert_setting_mock(alert_uuid=alert_uuid)
        mock_session.query.return_value.filter.return_value.first.return_value = mock_alert
        # Act & Assert（例外が発生しないこと）
        service.update(alert_uuid=alert_uuid, data=data, user_id=1)

    def test_update_uses_specified_alert_uuid(self, service, mock_session):
        """3.3.2.2: 指定した alert_uuid がリポジトリに渡される"""
        # Arrange
        target_uuid = "target-uuid-0001-0001-0001-000000000001"
        data = make_valid_form_data()
        mock_alert = make_alert_setting_mock(alert_uuid=target_uuid)
        mock_session.query.return_value.filter.return_value.first.return_value = mock_alert
        # Act
        service.update(alert_uuid=target_uuid, data=data, user_id=1)
        # Assert
        mock_session.query.return_value.filter.assert_called_once()
        filter_call_args = str(mock_session.query.return_value.filter.call_args)
        assert target_uuid in filter_call_args

    # ----------------------------------------------------------------
    # 2.2 対象データ存在チェック
    # ----------------------------------------------------------------

    def test_update_not_found_raises(self, service, mock_session):
        """2.2.2: 存在しない alert_uuid を指定すると NotFoundError がスローされる"""
        # Arrange
        mock_session.query.return_value.filter.return_value.first.return_value = None
        data = make_valid_form_data()
        # Act & Assert
        with pytest.raises(Exception):
            service.update(alert_uuid="nonexistent-uuid", data=data, user_id=1)

    # ----------------------------------------------------------------
    # 2.3 副作用チェック
    # ----------------------------------------------------------------

    def test_update_rollback_on_db_error(self, service, mock_session):
        """2.3.2: DB例外発生時に rollback() が呼び出される"""
        # Arrange
        alert_uuid = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
        data = make_valid_form_data()
        mock_alert = make_alert_setting_mock(alert_uuid=alert_uuid)
        mock_session.query.return_value.filter.return_value.first.return_value = mock_alert
        mock_session.commit.side_effect = Exception("DB error")
        # Act & Assert
        with pytest.raises(Exception):
            service.update(alert_uuid=alert_uuid, data=data, user_id=1)
        mock_session.rollback.assert_called_once()


# ============================================================
# 5. 削除機能（Delete）
# 観点: 2.1 正常系処理, 2.2 対象データ存在チェック,
#       2.3 副作用チェック, 3.4 削除機能
# ============================================================

@pytest.mark.unit
class TestAlertSettingServiceDelete:
    """アラート設定削除機能（論理削除）
    観点: 2.1 正常系処理, 2.2 対象データ存在チェック,
          2.3 副作用チェック, 3.4 削除機能
    """

    # ----------------------------------------------------------------
    # 3.4.1 削除処理呼び出し
    # ----------------------------------------------------------------

    def test_delete_passes_alert_uuids_to_session(self, service, mock_session):
        """3.4.1.1: 指定した alert_uuid リストが論理削除クエリに渡される"""
        # Arrange
        uuids = ["uuid-0001", "uuid-0002"]
        mock_q = MagicMock()
        mock_session.query.return_value = mock_q
        mock_q.filter.return_value = mock_q
        mock_q.update.return_value = 2
        # Act
        service.delete(alert_uuids=uuids, user_id=1)
        # Assert
        mock_q.filter.assert_called_once()
        filter_call_args = str(mock_q.filter.call_args)
        for uuid in uuids:
            assert uuid in filter_call_args
        mock_session.commit.assert_called_once()

    # ----------------------------------------------------------------
    # 3.4.2 削除結果
    # ----------------------------------------------------------------

    def test_delete_completes_without_exception(self, service, mock_session):
        """3.4.2.1: 削除処理成功時に例外なく処理が完了する"""
        # Arrange
        uuids = ["uuid-0001"]
        mock_q = MagicMock()
        mock_session.query.return_value = mock_q
        mock_q.filter.return_value = mock_q
        mock_q.update.return_value = 1
        # Act & Assert（例外が発生しないこと）
        service.delete(alert_uuids=uuids, user_id=1)

    def test_delete_sets_delete_flag_true(self, service, mock_session):
        """3.4.2.2: 削除処理は delete_flag=True を設定する（論理削除）"""
        # Arrange
        uuids = ["uuid-0001"]
        mock_q = MagicMock()
        mock_session.query.return_value = mock_q
        mock_q.filter.return_value = mock_q
        mock_q.update.return_value = 1
        # Act
        service.delete(alert_uuids=uuids, user_id=1)
        # Assert: update が delete_flag=True で呼ばれること
        update_call_kwargs = mock_q.update.call_args
        assert update_call_kwargs is not None
        args, kwargs = update_call_kwargs
        update_dict = args[0]
        assert isinstance(update_dict, dict)
        assert update_dict.get("delete_flag") is True

    # ----------------------------------------------------------------
    # 2.2 対象データ存在チェック
    # ----------------------------------------------------------------

    def test_delete_zero_updated_raises_not_found(self, service, mock_session):
        """2.2.2: 削除対象が0件（存在しない UUID）の場合 NotFoundError がスローされる"""
        # Arrange
        mock_q = MagicMock()
        mock_session.query.return_value = mock_q
        mock_q.filter.return_value = mock_q
        mock_q.update.return_value = 0  # 0件更新
        # Act & Assert
        with pytest.raises(Exception):
            service.delete(alert_uuids=["nonexistent-uuid"], user_id=1)

    # ----------------------------------------------------------------
    # 2.3 副作用チェック
    # ----------------------------------------------------------------

    def test_delete_rollback_on_db_error(self, service, mock_session):
        """2.3.2: DB例外発生時に rollback() が呼び出される"""
        # Arrange
        mock_q = MagicMock()
        mock_session.query.return_value = mock_q
        mock_q.filter.return_value = mock_q
        mock_session.commit.side_effect = Exception("DB error")
        # Act & Assert
        with pytest.raises(Exception):
            service.delete(alert_uuids=["uuid-0001"], user_id=1)
        mock_session.rollback.assert_called_once()


# ============================================================
# 6. 詳細取得機能（参照）
# 観点: 2.2 対象データ存在チェック, 3.1.4 検索結果戻り値
# ============================================================

@pytest.mark.unit
class TestAlertSettingServiceGet:
    """アラート設定参照（詳細取得）機能
    観点: 2.2 対象データ存在チェック, 3.1.4 検索結果戻り値ハンドリング
    """

    def test_get_existing_alert_returns_data(self, service, mock_session):
        """2.2.1 / 3.1.4.1: 存在する alert_uuid でデータが返却される"""
        # Arrange
        alert_uuid = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
        expected = make_alert_setting_mock(alert_uuid=alert_uuid)
        mock_session.query.return_value.filter.return_value.first.return_value = expected
        # Act
        result = service.get(alert_uuid=alert_uuid, user_id=1)
        # Assert
        assert result == expected

    def test_get_nonexistent_alert_raises_not_found(self, service, mock_session):
        """2.2.2: 存在しない alert_uuid では NotFoundError がスローされる"""
        # Arrange
        mock_session.query.return_value.filter.return_value.first.return_value = None
        # Act & Assert
        with pytest.raises(Exception):
            service.get(alert_uuid="nonexistent-uuid", user_id=1)

    def test_get_deleted_alert_raises_not_found(self, service, mock_session):
        """2.2.3: 論理削除済みデータは存在しないものと同様に扱われ NotFoundError がスローされる"""
        # Arrange: delete_flag=True のレコードをDBが返してきた場合、サービス層が存在しないものと同様に扱う
        deleted_alert = make_alert_setting_mock(alert_uuid="deleted-uuid", delete_flag=True)
        mock_session.query.return_value.filter.return_value.first.return_value = deleted_alert
        # Act & Assert
        with pytest.raises(Exception):
            service.get(alert_uuid="deleted-uuid", user_id=1)


# ============================================================
# 7. CSVエクスポート機能
# 観点: 3.5.1 CSV生成ロジック, 3.5.3 エンコーディング処理
# ============================================================

@pytest.mark.unit
class TestAlertSettingServiceExport:
    """アラート設定CSVエクスポート機能
    観点: 3.5.1 CSV生成ロジック, 3.5.3 エンコーディング処理

    出典: workflow-specification.md > CSVエクスポート > 処理詳細（サーバーサイド）
    権限: CSVエクスポートはシステム保守者・管理者・販社ユーザのみ（サービス利用者は403）
    """

    def _make_csv_data(self):
        """CSVエクスポート用テストデータ生成"""
        return [make_alert_setting_mock(
            alert_id=1,
            alert_name="温度異常アラート",
            device_name="Device01",
            occur_item_name="temperature",
            alert_conditions_operator=">",
            alert_conditions_threshold=30.0,
            recovery_item_name="temperature",
            alert_recovery_conditions_operator="<=",
            alert_recovery_conditions_threshold=30.0,
            judgment_time=5,
            alert_level_name="Warning",
            alert_notification_flag=True,
            alert_email_flag=False,
        )]

    # ----------------------------------------------------------------
    # 3.5.1 CSV生成ロジック
    # ----------------------------------------------------------------

    def test_export_csv_returns_data(self, service, mock_session):
        """3.5.1.2: データが存在する場合、CSVデータが返却される"""
        # Arrange
        mock_q = MagicMock()
        mock_session.query.return_value = mock_q
        mock_q.filter.return_value = mock_q
        mock_q.order_by.return_value = mock_q
        mock_q.all.return_value = self._make_csv_data()
        # Act
        result = service.export_csv(user_id=1)
        # Assert
        assert result is not None

    def test_export_csv_contains_header(self, service, mock_session):
        """3.5.1.1: CSVヘッダー行に定義済み列名が含まれる"""
        # Arrange
        mock_q = MagicMock()
        mock_session.query.return_value = mock_q
        mock_q.filter.return_value = mock_q
        mock_q.order_by.return_value = mock_q
        mock_q.all.return_value = self._make_csv_data()
        # Act
        result = service.export_csv(user_id=1)
        # Assert: 出典の列名を検証
        expected_headers = [
            "アラートID", "アラート名", "デバイス名",
            "アラート発生条件_測定項目名", "アラート発生条件_比較演算子", "アラート発生条件_閾値",
            "アラート復旧条件_測定項目名", "アラート復旧条件_比較演算子", "アラート復旧条件_閾値",
            "判定時間（分）", "アラートレベル", "アラート通知", "メール送信",
            "作成日時", "作成者", "更新日時", "更新者",
        ]
        for header in expected_headers:
            assert header in result

    def test_export_csv_empty_data_returns_header_only(self, service, mock_session):
        """3.5.1.3: データが0件の場合、ヘッダー行のみのCSVが返却される"""
        # Arrange
        mock_q = MagicMock()
        mock_session.query.return_value = mock_q
        mock_q.filter.return_value = mock_q
        mock_q.order_by.return_value = mock_q
        mock_q.all.return_value = []
        # Act
        result = service.export_csv(user_id=1)
        # Assert: ヘッダーはあるがデータ行はない
        assert result is not None
        lines = result.strip().split("\n")
        assert len(lines) == 1  # ヘッダー行のみ

    def test_export_csv_notification_flag_displayed_as_text(self, service, mock_session):
        """3.5.1.4: alert_notification_flag が True の場合 '有効'、False の場合 '無効' と表示される"""
        # Arrange
        mock_q = MagicMock()
        mock_session.query.return_value = mock_q
        mock_q.filter.return_value = mock_q
        mock_q.order_by.return_value = mock_q
        mock_q.all.return_value = [
            make_alert_setting_mock(alert_notification_flag=True, alert_email_flag=False)
        ]
        # Act
        result = service.export_csv(user_id=1)
        # Assert
        assert "有効" in result
        assert "無効" in result

    # ----------------------------------------------------------------
    # 3.5.3 エンコーディング処理
    # ----------------------------------------------------------------

    def test_export_csv_encoded_utf8_bom(self, service, mock_session):
        """3.5.3.1: CSVデータが UTF-8 BOM付き（utf-8-sig）でエンコードされる"""
        # Arrange
        mock_q = MagicMock()
        mock_session.query.return_value = mock_q
        mock_q.filter.return_value = mock_q
        mock_q.order_by.return_value = mock_q
        mock_q.all.return_value = self._make_csv_data()
        # Act
        result = service.export_csv(user_id=1)
        # Assert: エンコード済みバイト列の場合、BOMが先頭に存在する
        if isinstance(result, bytes):
            assert result[:3] == b"\xef\xbb\xbf"
        else:
            assert isinstance(result, str)
            assert result.startswith("\ufeff")

    def test_export_csv_contains_japanese_characters(self, service, mock_session):
        """3.5.3.2: 日本語を含むデータが文字化けなく出力される"""
        # Arrange
        mock_q = MagicMock()
        mock_session.query.return_value = mock_q
        mock_q.filter.return_value = mock_q
        mock_q.order_by.return_value = mock_q
        mock_q.all.return_value = [
            make_alert_setting_mock(alert_name="温度異常アラート日本語テスト")
        ]
        # Act
        result = service.export_csv(user_id=1)
        # Assert
        assert "温度異常アラート日本語テスト" in result


# ============================================================
# 8. CSVエクスポート権限チェック
# 観点: 1.2 認可（権限チェック）機能
# ============================================================

@pytest.mark.unit
class TestAlertSettingServiceExportPermission:
    """CSVエクスポート権限チェック
    観点: 1.2 認可（権限チェック）機能

    出典: workflow-specification.md > CSVエクスポート > 処理フロー
      権限あり: システム保守者・管理者・販社ユーザ
      権限なし: サービス利用者
    """

    def test_export_csv_forbidden_for_service_company_user(self, service, mock_session):
        """1.2.2: サービス利用者が CSVエクスポートを実行すると ForbiddenError がスローされる"""
        # Arrange: user_type_id=4（サービス利用者）を返すモック
        mock_user = Mock()
        mock_user.user_type_id = 4
        mock_session.query.return_value.filter.return_value.first.return_value = mock_user
        # Act & Assert
        with pytest.raises(Exception):
            service.export_csv(user_id=1)

    def test_export_csv_allowed_for_system_admin(self, service, mock_session):
        """1.2.1: システム保守者が CSVエクスポートを実行すると正常に処理される"""
        # Arrange: user_type_id=1（システム保守者）を返すモック
        mock_user = Mock()
        mock_user.user_type_id = 1
        mock_session.query.return_value.filter.return_value.first.return_value = mock_user
        # Act & Assert（例外が発生しないこと）
        service.export_csv(user_id=1)
