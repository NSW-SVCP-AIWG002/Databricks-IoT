"""
メール通知履歴 - Service層 単体テスト

対象ファイル: src/iot_app/services/mail_history_service.py

参照ドキュメント:
  - UI設計書:       docs/03-features/flask-app/mail-history/ui-specification.md
  - 機能設計書:     docs/03-features/flask-app/mail-history/workflow-specification.md
  - 単体テスト観点表: docs/05-testing/unit-test/unit-test-perspectives.md
  - 実装ガイド:     docs/05-testing/unit-test/unit-test-guide.md
"""

import pytest
from datetime import date, datetime
from unittest.mock import MagicMock, Mock, patch


# ============================================================
# ヘルパー
# ============================================================

def make_mail_type_mock(mail_type_id=1, mail_type_name='アラート通知', delete_flag=False):
    m = Mock()
    m.mail_type_id = mail_type_id
    m.mail_type_name = mail_type_name
    m.delete_flag = delete_flag
    return m


def make_mail_history_mock(**kwargs):
    m = Mock()
    m.mail_history_id = kwargs.get('mail_history_id', 1)
    m.mail_history_uuid = kwargs.get('mail_history_uuid', 'test-uuid-001')
    m.mail_type = kwargs.get('mail_type', 1)
    m.sender_email = kwargs.get('sender_email', 'sender@example.com')
    m.recipients = kwargs.get('recipients', {'to': ['recipient@example.com']})
    m.subject = kwargs.get('subject', 'テスト件名')
    m.body = kwargs.get('body', 'テスト本文')
    m.sent_at = kwargs.get('sent_at', datetime(2026, 4, 10, 12, 0, 0))
    m.organization_id = kwargs.get('organization_id', 1)
    return m


def make_sort_item_mock(sort_item_name='sent_at'):
    m = Mock()
    m.sort_item_name = sort_item_name
    return m


def _make_query_chain(records, total):
    """SQLAlchemy クエリチェーンのモックを生成"""
    q = MagicMock()
    q.filter_by.return_value = q
    q.filter.return_value = q
    q.order_by.return_value = q
    q.count.return_value = total
    q.limit.return_value = q
    q.offset.return_value = q
    q.all.return_value = records
    return q


# ============================================================
# 1. get_mail_type_choices
# 観点: 2.1 正常系処理, 2.4 データフィルタリング
# ============================================================

@pytest.mark.unit
class TestGetMailTypeChoices:
    """メール種別一覧取得"""

    def test_returns_active_mail_types(self):
        """2.1.1: delete_flag=False のレコードのみ返す"""
        # Arrange
        mock_types = [
            make_mail_type_mock(1, 'アラート通知'),
            make_mail_type_mock(2, '招待メール'),
        ]
        with patch('iot_app.services.mail_history_service.MailTypeMaster') as MockModel:
            MockModel.query.filter_by.return_value.order_by.return_value.all.return_value = mock_types
            from iot_app.services.mail_history_service import get_mail_type_choices

            # Act
            result = get_mail_type_choices()

            # Assert
            assert result == mock_types
            MockModel.query.filter_by.assert_called_once_with(delete_flag=False)

    def test_returns_empty_list_when_no_types(self):
        """2.1.2: レコードが存在しない場合は空リストを返す"""
        # Arrange
        with patch('iot_app.services.mail_history_service.MailTypeMaster') as MockModel:
            MockModel.query.filter_by.return_value.order_by.return_value.all.return_value = []
            from iot_app.services.mail_history_service import get_mail_type_choices

            # Act
            result = get_mail_type_choices()

            # Assert
            assert result == []


# ============================================================
# 2. get_sort_column
# 観点: 2.1 正常系処理, 2.3 フォールバック動作
# ============================================================

@pytest.mark.unit
class TestGetSortColumn:
    """ソートカラム取得（ホワイトリスト検証）"""

    def test_returns_db_value_when_found(self):
        """2.1.1: sort_item_master にレコードが存在する場合、DB値を返す"""
        # Arrange
        mock_item = make_sort_item_mock('sent_at')
        with patch('iot_app.services.mail_history_service.SortItemMaster') as MockModel:
            MockModel.query.filter_by.return_value.first.return_value = mock_item
            from iot_app.services.mail_history_service import get_sort_column

            # Act
            result = get_sort_column(3)

            # Assert
            assert result == 'sent_at'

    def test_fallback_mail_type_when_db_miss(self):
        """2.3.1: DB未登録のsort_id=1はフォールバック値 'mail_type' を返す"""
        # Arrange
        with patch('iot_app.services.mail_history_service.SortItemMaster') as MockModel:
            MockModel.query.filter_by.return_value.first.return_value = None
            from iot_app.services.mail_history_service import get_sort_column

            # Act
            result = get_sort_column(1)

            # Assert
            assert result == 'mail_type'

    def test_fallback_subject_when_db_miss(self):
        """2.3.2: DB未登録のsort_id=2はフォールバック値 'subject' を返す"""
        with patch('iot_app.services.mail_history_service.SortItemMaster') as MockModel:
            MockModel.query.filter_by.return_value.first.return_value = None
            from iot_app.services.mail_history_service import get_sort_column

            result = get_sort_column(2)

            assert result == 'subject'

    def test_fallback_sent_at_when_db_miss(self):
        """2.3.3: DB未登録のsort_id=3はフォールバック値 'sent_at' を返す"""
        with patch('iot_app.services.mail_history_service.SortItemMaster') as MockModel:
            MockModel.query.filter_by.return_value.first.return_value = None
            from iot_app.services.mail_history_service import get_sort_column

            result = get_sort_column(3)

            assert result == 'sent_at'

    def test_returns_none_for_unknown_sort_id(self):
        """2.3.4: DB未登録かつフォールバックにも存在しないsort_idはNoneを返す"""
        # Arrange
        with patch('iot_app.services.mail_history_service.SortItemMaster') as MockModel:
            MockModel.query.filter_by.return_value.first.return_value = None
            from iot_app.services.mail_history_service import get_sort_column

            # Act
            result = get_sort_column(999)

            # Assert
            assert result is None


# ============================================================
# 3. get_default_date_range
# 観点: 2.1 正常系処理, 3.5 日付処理
# ============================================================

@pytest.mark.unit
class TestGetDefaultDateRange:
    """デフォルト日付範囲取得"""

    def test_start_is_7_days_before_end(self):
        """3.5.1: 開始日は終了日の7日前"""
        # Arrange / Act
        from iot_app.services.mail_history_service import get_default_date_range
        start, end = get_default_date_range()

        # Assert
        assert (end - start).days == 7

    def test_returns_date_objects(self):
        """3.5.2: 戻り値は date 型"""
        from iot_app.services.mail_history_service import get_default_date_range
        start, end = get_default_date_range()

        assert isinstance(start, date)
        assert isinstance(end, date)

    def test_start_before_end(self):
        """3.5.3: 開始日は終了日より前"""
        from iot_app.services.mail_history_service import get_default_date_range
        start, end = get_default_date_range()

        assert start < end


# ============================================================
# 4. get_mail_history_list
# 観点: 2.1 正常系処理, 2.4 データフィルタリング, 3.3 ページネーション
# ============================================================

@pytest.mark.unit
class TestGetMailHistoryList:
    """メール通知履歴一覧取得"""

    def test_returns_records_and_total(self):
        """2.1.1: 正常系 - レコードと総件数をタプルで返す"""
        # Arrange
        mock_records = [make_mail_history_mock()]
        with patch('iot_app.services.mail_history_service.MailHistory') as MockModel:
            q = _make_query_chain(mock_records, 1)
            MockModel.query.filter_by.return_value = q
            MockModel.mail_history_id = MagicMock()
            from iot_app.services.mail_history_service import get_mail_history_list

            # Act
            records, total = get_mail_history_list(
                organization_id=1,
                mail_types=[],
                keyword='',
                sent_at_start=None,
                sent_at_end=None,
                sort_column='sent_at',
                order='desc',
                page=1,
            )

            # Assert
            assert records == mock_records
            assert total == 1

    def test_filters_by_organization_id(self):
        """2.4.1: organization_id でデータスコープが制限される"""
        # Arrange
        with patch('iot_app.services.mail_history_service.MailHistory') as MockModel:
            q = _make_query_chain([], 0)
            MockModel.query.filter_by.return_value = q
            MockModel.mail_history_id = MagicMock()
            from iot_app.services.mail_history_service import get_mail_history_list

            # Act
            get_mail_history_list(
                organization_id=42,
                mail_types=[],
                keyword='',
                sent_at_start=None,
                sent_at_end=None,
                sort_column='sent_at',
                order='desc',
                page=1,
            )

            # Assert
            MockModel.query.filter_by.assert_called_once_with(organization_id=42)

    def test_applies_mail_type_filter_when_specified(self):
        """2.4.2: mail_types が指定された場合、in_ フィルタが適用される"""
        # Arrange
        with patch('iot_app.services.mail_history_service.MailHistory') as MockModel:
            q = _make_query_chain([], 0)
            MockModel.query.filter_by.return_value = q
            MockModel.mail_history_id = MagicMock()
            from iot_app.services.mail_history_service import get_mail_history_list

            # Act
            get_mail_history_list(
                organization_id=1,
                mail_types=[1, 2],
                keyword='',
                sent_at_start=None,
                sent_at_end=None,
                sort_column='sent_at',
                order='desc',
                page=1,
            )

            # Assert: mail_types フィルタとして filter が1回呼ばれる
            assert q.filter.call_count == 1

    def test_applies_keyword_filter_when_specified(self):
        """2.4.3: keyword が指定された場合、件名・本文の OR フィルタが適用される"""
        # Arrange
        # or_() に渡すオペランドが MagicMock のため、sqlalchemy.or_ もモック化する
        with patch('iot_app.services.mail_history_service.MailHistory') as MockModel, \
             patch('iot_app.services.mail_history_service.or_') as mock_or:
            q = _make_query_chain([], 0)
            MockModel.query.filter_by.return_value = q
            MockModel.mail_history_id = MagicMock()
            mock_or.return_value = MagicMock()
            from iot_app.services.mail_history_service import get_mail_history_list

            # Act
            get_mail_history_list(
                organization_id=1,
                mail_types=[],
                keyword='テスト',
                sent_at_start=None,
                sent_at_end=None,
                sort_column='sent_at',
                order='desc',
                page=1,
            )

            # Assert: keyword フィルタとして filter が1回呼ばれ、or_ も呼ばれる
            assert q.filter.call_count == 1
            assert mock_or.called

    def test_applies_date_range_filters_when_specified(self):
        """2.4.4: 日付範囲が指定された場合、sent_at の開始・終了フィルタが各1回適用される"""
        # Arrange
        # MagicMock の比較演算子（>= / <=）が datetime と組み合わさるとエラーになるため
        # sent_at 属性の __ge__ / __le__ を明示的に設定する
        with patch('iot_app.services.mail_history_service.MailHistory') as MockModel:
            q = _make_query_chain([], 0)
            MockModel.query.filter_by.return_value = q
            MockModel.mail_history_id = MagicMock()
            mock_sent_at = MagicMock()
            mock_sent_at.__ge__ = Mock(return_value=MagicMock())
            mock_sent_at.__le__ = Mock(return_value=MagicMock())
            MockModel.sent_at = mock_sent_at
            from iot_app.services.mail_history_service import get_mail_history_list

            # Act
            get_mail_history_list(
                organization_id=1,
                mail_types=[],
                keyword='',
                sent_at_start=date(2026, 4, 1),
                sent_at_end=date(2026, 4, 10),
                sort_column='sent_at',
                order='desc',
                page=1,
            )

            # Assert: 開始日・終了日フィルタで filter が2回呼ばれる
            assert q.filter.call_count == 2

    def test_no_filter_when_all_conditions_empty(self):
        """2.4.5: 全条件が空の場合、追加フィルタは適用されない"""
        # Arrange
        with patch('iot_app.services.mail_history_service.MailHistory') as MockModel:
            q = _make_query_chain([], 0)
            MockModel.query.filter_by.return_value = q
            MockModel.mail_history_id = MagicMock()
            from iot_app.services.mail_history_service import get_mail_history_list

            # Act
            get_mail_history_list(
                organization_id=1,
                mail_types=[],
                keyword='',
                sent_at_start=None,
                sent_at_end=None,
                sort_column='sent_at',
                order='desc',
                page=1,
            )

            # Assert
            q.filter.assert_not_called()

    def test_pagination_offset_page1(self):
        """3.3.1: page=1 の場合、offset=0 で取得する"""
        # Arrange
        with patch('iot_app.services.mail_history_service.MailHistory') as MockModel:
            q = _make_query_chain([], 0)
            MockModel.query.filter_by.return_value = q
            MockModel.mail_history_id = MagicMock()
            from iot_app.services.mail_history_service import get_mail_history_list

            # Act
            get_mail_history_list(
                organization_id=1,
                mail_types=[],
                keyword='',
                sent_at_start=None,
                sent_at_end=None,
                sort_column='sent_at',
                order='desc',
                page=1,
            )

            # Assert
            q.offset.assert_called_once_with(0)

    def test_pagination_offset_page3(self):
        """3.3.2: page=3 の場合、offset=(3-1)*per_page で取得する"""
        # Arrange
        with patch('iot_app.services.mail_history_service.MailHistory') as MockModel:
            q = _make_query_chain([], 0)
            MockModel.query.filter_by.return_value = q
            MockModel.mail_history_id = MagicMock()
            from iot_app.services.mail_history_service import (
                get_mail_history_list,
                _DEFAULT_PER_PAGE,
            )

            # Act
            get_mail_history_list(
                organization_id=1,
                mail_types=[],
                keyword='',
                sent_at_start=None,
                sent_at_end=None,
                sort_column='sent_at',
                order='desc',
                page=3,
            )

            # Assert
            expected_offset = (3 - 1) * _DEFAULT_PER_PAGE
            q.offset.assert_called_once_with(expected_offset)

    def test_returns_empty_when_no_records(self):
        """2.1.2: レコードが存在しない場合、空リストと0を返す"""
        # Arrange
        with patch('iot_app.services.mail_history_service.MailHistory') as MockModel:
            q = _make_query_chain([], 0)
            MockModel.query.filter_by.return_value = q
            MockModel.mail_history_id = MagicMock()
            from iot_app.services.mail_history_service import get_mail_history_list

            # Act
            records, total = get_mail_history_list(
                organization_id=1,
                mail_types=[],
                keyword='',
                sent_at_start=None,
                sent_at_end=None,
                sort_column='sent_at',
                order='desc',
                page=1,
            )

            # Assert
            assert records == []
            assert total == 0


# ============================================================
# 5. get_mail_history_detail
# 観点: 2.1 正常系処理, 2.2 対象データ存在チェック, 2.4 データフィルタリング
# ============================================================

@pytest.mark.unit
class TestGetMailHistoryDetail:
    """メール通知履歴詳細取得"""

    def test_returns_record_when_found(self):
        """2.1.1: 正常系 - 一致するUUIDと組織IDのレコードを返す"""
        # Arrange
        mock_history = make_mail_history_mock(mail_history_uuid='abc-123', organization_id=1)
        with patch('iot_app.services.mail_history_service.MailHistory') as MockModel:
            MockModel.query.filter_by.return_value.first.return_value = mock_history
            from iot_app.services.mail_history_service import get_mail_history_detail

            # Act
            result = get_mail_history_detail('abc-123', organization_id=1)

            # Assert
            assert result == mock_history
            MockModel.query.filter_by.assert_called_once_with(
                mail_history_uuid='abc-123',
                organization_id=1,
            )

    def test_returns_none_when_uuid_not_found(self):
        """2.2.2: UUIDが存在しない場合はNoneを返す"""
        # Arrange
        with patch('iot_app.services.mail_history_service.MailHistory') as MockModel:
            MockModel.query.filter_by.return_value.first.return_value = None
            from iot_app.services.mail_history_service import get_mail_history_detail

            # Act
            result = get_mail_history_detail('no-such-uuid', organization_id=1)

            # Assert
            assert result is None

    def test_returns_none_when_wrong_organization(self):
        """2.4.1: organization_id が一致しない場合はNoneを返す（データスコープ制限）"""
        # Arrange
        with patch('iot_app.services.mail_history_service.MailHistory') as MockModel:
            MockModel.query.filter_by.return_value.first.return_value = None
            from iot_app.services.mail_history_service import get_mail_history_detail

            # Act
            result = get_mail_history_detail('abc-123', organization_id=999)

            # Assert
            assert result is None
            MockModel.query.filter_by.assert_called_once_with(
                mail_history_uuid='abc-123',
                organization_id=999,
            )
