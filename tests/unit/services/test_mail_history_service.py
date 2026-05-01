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

MODULE = 'iot_app.services.mail_history_service'


# ============================================================
# ヘルパー
# ============================================================

def make_mail_type_mock(mail_type_id=1, mail_type_name='アラート通知', delete_flag=False):
    """MailTypeMaster モックを生成するヘルパー"""
    m = Mock()
    m.mail_type_id = mail_type_id
    m.mail_type_name = mail_type_name
    m.delete_flag = delete_flag
    return m


def make_mail_history_mock(**kwargs):
    """MailHistory モックを生成するヘルパー"""
    m = Mock()
    m.mail_history_id = kwargs.get('mail_history_id', 1)
    m.mail_history_uuid = kwargs.get('mail_history_uuid', 'test-uuid-001')
    m.mail_type = kwargs.get('mail_type', 1)
    m.sender_email = kwargs.get('sender_email', 'sender@example.com')
    m.subject = kwargs.get('subject', 'テスト件名')
    m.body = kwargs.get('body', 'テスト本文')
    m.sent_at = kwargs.get('sent_at', datetime(2026, 4, 10, 12, 0, 0))
    m.organization_id = kwargs.get('organization_id', 1)
    return m


def make_mail_recipient_mock(**kwargs):
    """MailRecipient モックを生成するヘルパー"""
    m = Mock()
    m.mail_history_id = kwargs.get('mail_history_id', 1)
    m.user_id = kwargs.get('user_id', 10)
    m.recipient_email = kwargs.get('recipient_email', 'recipient@example.com')
    return m


def make_sort_item_mock(sort_item_name='sent_at'):
    """SortItemMaster モックを生成するヘルパー"""
    m = Mock()
    m.sort_item_name = sort_item_name
    return m


def make_mock_query(records=None, total=0):
    """SQLAlchemy クエリチェーンのモックを生成するヘルパー"""
    if records is None:
        records = []
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
    """get_mail_type_choices - メール種別一覧取得
    観点: 2.1 正常系処理, 2.4 データフィルタリング
    """

    @patch(f'{MODULE}.MailTypeMaster')
    def test_returns_active_mail_types(self, MockModel):
        """2.1.1: delete_flag=False のレコードのみ返す"""
        # Arrange: delete_flag=False の2件を返すようにモック設定
        mock_types = [
            make_mail_type_mock(1, 'アラート通知'),
            make_mail_type_mock(2, '招待メール'),
        ]
        MockModel.query.filter_by.return_value.order_by.return_value.all.return_value = mock_types
        from iot_app.services.mail_history_service import get_mail_type_choices

        # Act
        result = get_mail_type_choices()

        # Assert: 取得結果が設定したモックと一致すること
        assert result == mock_types
        # Assert: filter_by が delete_flag=False で呼ばれること
        MockModel.query.filter_by.assert_called_once_with(delete_flag=False)

    @patch(f'{MODULE}.MailTypeMaster')
    def test_returns_empty_list_when_no_types(self, MockModel):
        """2.1.2: レコードが存在しない場合は空リストを返す"""
        # Arrange: 全件削除済み（空リスト）
        MockModel.query.filter_by.return_value.order_by.return_value.all.return_value = []
        from iot_app.services.mail_history_service import get_mail_type_choices

        # Act
        result = get_mail_type_choices()

        # Assert: 空リストが返ること
        assert result == []


# ============================================================
# 2. get_mail_type_by_id
# 観点: 2.1 正常系処理, 2.2 対象データ存在チェック
# ============================================================

@pytest.mark.unit
class TestGetMailTypeById:
    """get_mail_type_by_id - メール種別ID検索
    観点: 2.1 正常系処理, 2.2 対象データ存在チェック
    """

    @patch(f'{MODULE}.db')
    @patch(f'{MODULE}.MailTypeMaster')
    def test_returns_record_when_found(self, MockModel, mock_db):
        """2.1.1: 指定IDのレコードが存在する場合は MailTypeMaster を返す"""
        # Arrange: mail_type_id=1 に対応するレコードを設定
        mock_type = make_mail_type_mock(1, 'アラート通知')
        mock_db.session.get.return_value = mock_type
        from iot_app.services.mail_history_service import get_mail_type_by_id

        # Act
        result = get_mail_type_by_id(1)

        # Assert: 設定したモックレコードが返ること
        assert result == mock_type
        # Assert: db.session.get が正しい引数で呼ばれること
        mock_db.session.get.assert_called_once_with(MockModel, 1)

    @patch(f'{MODULE}.db')
    @patch(f'{MODULE}.MailTypeMaster')
    def test_returns_none_when_not_found(self, MockModel, mock_db):
        """2.2.2: 指定IDのレコードが存在しない場合は None を返す"""
        # Arrange: DB に該当レコードなし
        mock_db.session.get.return_value = None
        from iot_app.services.mail_history_service import get_mail_type_by_id

        # Act
        result = get_mail_type_by_id(999)

        # Assert: None が返ること
        assert result is None


# ============================================================
# 3. get_sort_column
# 観点: 2.1 正常系処理, 2.3 フォールバック動作
# ============================================================

@pytest.mark.unit
class TestGetSortColumn:
    """get_sort_column - ソートカラム取得（ホワイトリスト検証）
    観点: 2.1 正常系処理, 2.3 フォールバック動作
    """

    @patch(f'{MODULE}.SortItemMaster')
    def test_returns_db_value_when_found(self, MockModel):
        """2.1.1: sort_item_master にレコードが存在する場合、DB値を返す"""
        # Arrange: sort_item_name='sent_at' を返すモック設定
        mock_item = make_sort_item_mock('sent_at')
        MockModel.query.filter_by.return_value.first.return_value = mock_item
        from iot_app.services.mail_history_service import get_sort_column

        # Act
        result = get_sort_column(3)

        # Assert: DB から取得した sort_item_name が返ること
        assert result == 'sent_at'
        # Assert: filter_by が view_id=5, sort_item_id=3, delete_flag=False で呼ばれること
        MockModel.query.filter_by.assert_called_once_with(
            view_id=5,
            sort_item_id=3,
            delete_flag=False,
        )

    @patch(f'{MODULE}.SortItemMaster')
    def test_fallback_mail_type_when_db_miss(self, MockModel):
        """2.3.1: DB未登録の sort_id=1 はフォールバック値 'mail_type' を返す"""
        # Arrange: DB に該当レコードなし（None）
        MockModel.query.filter_by.return_value.first.return_value = None
        from iot_app.services.mail_history_service import get_sort_column

        # Act
        result = get_sort_column(1)

        # Assert: フォールバック値 'mail_type' が返ること
        assert result == 'mail_type'

    @patch(f'{MODULE}.SortItemMaster')
    def test_fallback_subject_when_db_miss(self, MockModel):
        """2.3.2: DB未登録の sort_id=2 はフォールバック値 'subject' を返す"""
        # Arrange: DB に該当レコードなし（None）
        MockModel.query.filter_by.return_value.first.return_value = None
        from iot_app.services.mail_history_service import get_sort_column

        # Act
        result = get_sort_column(2)

        # Assert: フォールバック値 'subject' が返ること
        assert result == 'subject'

    @patch(f'{MODULE}.SortItemMaster')
    def test_fallback_sent_at_when_db_miss(self, MockModel):
        """2.3.3: DB未登録の sort_id=3 はフォールバック値 'sent_at' を返す"""
        # Arrange: DB に該当レコードなし（None）
        MockModel.query.filter_by.return_value.first.return_value = None
        from iot_app.services.mail_history_service import get_sort_column

        # Act
        result = get_sort_column(3)

        # Assert: フォールバック値 'sent_at' が返ること
        assert result == 'sent_at'

    @patch(f'{MODULE}.SortItemMaster')
    def test_returns_none_for_unknown_sort_id(self, MockModel):
        """2.3.4: DB未登録かつフォールバックにも存在しない sort_id は None を返す"""
        # Arrange: DB に該当レコードなし（None）＆ フォールバック辞書にも未定義のID
        MockModel.query.filter_by.return_value.first.return_value = None
        from iot_app.services.mail_history_service import get_sort_column

        # Act
        result = get_sort_column(999)

        # Assert: None が返ること
        assert result is None


# ============================================================
# 4. get_default_date_range
# 観点: 2.1 正常系処理, 3.5 日付処理
# ============================================================

@pytest.mark.unit
class TestGetDefaultDateRange:
    """get_default_date_range - デフォルト日付範囲取得
    観点: 2.1 正常系処理, 機能固有: 日付範囲計算
    """

    def test_start_is_7_days_before_end(self):
        """機能固有: 開始日は終了日の7日前"""
        # Arrange / Act
        from iot_app.services.mail_history_service import get_default_date_range
        start, end = get_default_date_range()

        # Assert: end - start が 7 日であること
        assert (end - start).days == 7

    def test_returns_date_objects(self):
        """機能固有: 戻り値は date 型"""
        # Arrange / Act
        from iot_app.services.mail_history_service import get_default_date_range
        start, end = get_default_date_range()

        # Assert: start, end がともに date 型であること
        assert isinstance(start, date)
        assert isinstance(end, date)

    def test_start_before_end(self):
        """機能固有: 開始日は終了日より前"""
        # Arrange / Act
        from iot_app.services.mail_history_service import get_default_date_range
        start, end = get_default_date_range()

        # Assert: start < end であること
        assert start < end

    def test_concrete_date_values(self):
        """機能固有: 実行日基準の具体値検証（期待値も同じ計算式で動的に導出）"""
        from datetime import timedelta
        from iot_app.services.mail_history_service import get_default_date_range

        # Arrange: 期待値を実行日基準で動的に算出
        expected_start = date.today() - timedelta(days=7)
        expected_end = date.today()

        # Act
        start, end = get_default_date_range()

        # Assert
        assert start == expected_start
        assert end == expected_end


# ============================================================
# 5. get_mail_history_list
# 観点: 2.1 正常系処理, 2.4 データフィルタリング, 3.3 ページネーション, 3.4 ソート
# ============================================================

@pytest.mark.unit
class TestGetMailHistoryList:
    """get_mail_history_list - メール通知履歴一覧取得
    観点: 2.1 正常系処理, 2.4 データフィルタリング, 3.3 ページネーション, 3.4 ソート
    """

    @patch(f'{MODULE}.MailHistory')
    def test_returns_records_and_total(self, MockModel):
        """2.1.1: 正常系 - レコードと総件数をタプルで返す"""
        # Arrange: モックレコード1件、総件数1を設定
        mock_records = [make_mail_history_mock()]
        q = make_mock_query(mock_records, 1)
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

        # Assert: 取得レコードと総件数がモック値と一致すること
        assert records == mock_records
        assert total == 1

    @patch(f'{MODULE}.MailHistory')
    def test_filters_by_organization_id(self, MockModel):
        """2.4.1: organization_id でデータスコープが制限される"""
        # Arrange: organization_id=42 でクエリされることを検証するための設定
        q = make_mock_query([], 0)
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

        # Assert: filter_by が organization_id=42 で呼ばれること
        MockModel.query.filter_by.assert_called_once_with(organization_id=42)

    @patch(f'{MODULE}.MailHistory')
    def test_applies_mail_type_filter_when_specified(self, MockModel):
        """2.4.2: mail_types が指定された場合、in_ フィルタが適用される"""
        # Arrange: mail_types=[1, 2] を渡してフィルタが呼ばれることを検証
        q = make_mock_query([], 0)
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

        # Assert: mail_types フィルタとして filter が1回呼ばれること
        assert q.filter.call_count == 1

    @patch(f'{MODULE}.or_')
    @patch(f'{MODULE}.MailHistory')
    def test_applies_keyword_filter_when_specified(self, MockModel, mock_or):
        """2.4.3: keyword が指定された場合、件名・本文の OR フィルタが適用される"""
        # Arrange: or_() に渡す MagicMock オペランドが SQLAlchemy で評価されないよう
        #          or_ 自体もモック化する
        q = make_mock_query([], 0)
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

        # Assert: keyword フィルタとして filter が1回呼ばれること
        assert q.filter.call_count == 1
        # Assert: or_() が呼ばれること（件名・本文の OR 結合）
        assert mock_or.called

    @patch(f'{MODULE}.MailHistory')
    def test_applies_date_range_filters_when_specified(self, MockModel):
        """2.4.4: 日付範囲が指定された場合、sent_at の開始・終了フィルタが各1回適用される"""
        # Arrange: MagicMock の比較演算子（>= / <=）が datetime と組み合わさると
        #          Python が逆側の比較メソッドにフォールバックしエラーになるため、
        #          sent_at 属性の __ge__ / __le__ を明示的に設定する
        q = make_mock_query([], 0)
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

        # Assert: 開始日・終了日フィルタで filter が2回（各1回）呼ばれること
        assert q.filter.call_count == 2

    @patch(f'{MODULE}.MailHistory')
    def test_no_filter_when_all_conditions_empty(self, MockModel):
        """2.4.5: 全条件が空の場合、追加フィルタは適用されない"""
        # Arrange: 検索条件をすべて空/None に設定
        q = make_mock_query([], 0)
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

        # Assert: 追加の filter が1回も呼ばれないこと
        q.filter.assert_not_called()

    @patch(f'{MODULE}.MailHistory')
    def test_pagination_offset_page1(self, MockModel):
        """3.3.1: page=1 の場合、offset=0 で取得する"""
        # Arrange
        q = make_mock_query([], 0)
        MockModel.query.filter_by.return_value = q
        MockModel.mail_history_id = MagicMock()
        from iot_app.services.mail_history_service import (
            get_mail_history_list,
            DEFAULT_PER_PAGE,
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
            page=1,
        )

        # Assert: offset が 0 で呼ばれること（page=1 → offset=(1-1)*per_page=0）
        q.offset.assert_called_once_with(0)
        # Assert: limit が DEFAULT_PER_PAGE(25) で呼ばれること
        q.limit.assert_called_once_with(DEFAULT_PER_PAGE)

    @patch(f'{MODULE}.MailHistory')
    def test_pagination_offset_page3(self, MockModel):
        """3.3.2: page=3 の場合、offset=(3-1)*per_page で取得する"""
        # Arrange
        q = make_mock_query([], 0)
        MockModel.query.filter_by.return_value = q
        MockModel.mail_history_id = MagicMock()
        from iot_app.services.mail_history_service import (
            get_mail_history_list,
            DEFAULT_PER_PAGE,
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

        # Assert: offset が (3-1)*DEFAULT_PER_PAGE で呼ばれること
        expected_offset = (3 - 1) * DEFAULT_PER_PAGE
        q.offset.assert_called_once_with(expected_offset)

    @patch(f'{MODULE}.MailHistory')
    def test_returns_empty_when_no_records(self, MockModel):
        """2.1.2: レコードが存在しない場合、空リストと 0 を返す"""
        # Arrange: DB に該当レコードなし
        q = make_mock_query([], 0)
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

        # Assert: 空リストと 0 が返ること
        assert records == []
        assert total == 0

    @patch(f'{MODULE}.MailHistory')
    def test_sort_order_desc_uses_desc_method(self, MockModel):
        """3.4.1: order='desc' のとき、ソートカラムの .desc() が呼ばれる"""
        # Arrange: sort_column='sent_at', order='desc' を指定
        q = make_mock_query([], 0)
        MockModel.query.filter_by.return_value = q
        mock_sent_at_col = MagicMock()
        MockModel.sent_at = mock_sent_at_col
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

        # Assert: sent_at カラムの .desc() が呼ばれること
        mock_sent_at_col.desc.assert_called_once()
        # Assert: 第2ソートキーとして mail_history_id.asc() が呼ばれること
        MockModel.mail_history_id.asc.assert_called_once()

    @patch(f'{MODULE}.MailHistory')
    def test_sort_order_asc_uses_asc_method(self, MockModel):
        """3.4.2: order='asc' のとき、ソートカラムの .asc() が呼ばれる"""
        # Arrange: sort_column='sent_at', order='asc' を指定
        q = make_mock_query([], 0)
        MockModel.query.filter_by.return_value = q
        mock_sent_at_col = MagicMock()
        MockModel.sent_at = mock_sent_at_col
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
            order='asc',
            page=1,
        )

        # Assert: sent_at カラムの .asc() が呼ばれること
        mock_sent_at_col.asc.assert_called_once()
        # Assert: 第2ソートキーとして mail_history_id.asc() が呼ばれること
        MockModel.mail_history_id.asc.assert_called_once()

    @patch(f'{MODULE}.MailHistory')
    def test_fallback_sort_column_when_invalid(self, MockModel):
        """異常系: MailHistory に存在しない sort_column は sent_at にフォールバックする"""
        # Arrange: 存在しないカラム名を None に設定し、フォールバック先 sent_at を別途設定
        #          MagicMock はデフォルトで未定義属性を自動生成するため、明示的に None を設定する
        q = make_mock_query([], 0)
        MockModel.query.filter_by.return_value = q
        MockModel.mail_history_id = MagicMock()
        mock_sent_at_col = MagicMock()
        MockModel.sent_at = mock_sent_at_col
        MockModel.nonexistent_col = None
        from iot_app.services.mail_history_service import get_mail_history_list

        # Act
        get_mail_history_list(
            organization_id=1,
            mail_types=[],
            keyword='',
            sent_at_start=None,
            sent_at_end=None,
            sort_column='nonexistent_col',
            order='desc',
            page=1,
        )

        # Assert: sent_at カラムの .desc() が呼ばれること（nonexistent_col → sent_at フォールバック確認）
        mock_sent_at_col.desc.assert_called_once()
        # Assert: 第2ソートキーとして mail_history_id.asc() が呼ばれること
        MockModel.mail_history_id.asc.assert_called_once()

    @patch(f'{MODULE}.MailHistory')
    def test_applies_only_sent_at_start_filter(self, MockModel):
        """正常系: sent_at_start のみ指定した場合、開始フィルタのみ1回適用される（sent_at_end=None は無視）"""
        # Arrange: sent_at_end=None の場合、終了日フィルタが適用されないことを検証
        q = make_mock_query([], 0)
        MockModel.query.filter_by.return_value = q
        MockModel.mail_history_id = MagicMock()
        mock_sent_at = MagicMock()
        mock_sent_at.__ge__ = Mock(return_value=MagicMock())
        MockModel.sent_at = mock_sent_at
        from iot_app.services.mail_history_service import get_mail_history_list

        # Act
        get_mail_history_list(
            organization_id=1,
            mail_types=[],
            keyword='',
            sent_at_start=date(2026, 4, 1),
            sent_at_end=None,
            sort_column='sent_at',
            order='desc',
            page=1,
        )

        # Assert: filter が1回（開始日フィルタのみ）呼ばれること
        assert q.filter.call_count == 1

    @patch(f'{MODULE}.MailHistory')
    def test_applies_only_sent_at_end_filter(self, MockModel):
        """正常系: sent_at_end のみ指定した場合、終了フィルタのみ1回適用される（sent_at_start=None は無視）"""
        # Arrange: sent_at_start=None の場合、開始日フィルタが適用されないことを検証
        q = make_mock_query([], 0)
        MockModel.query.filter_by.return_value = q
        MockModel.mail_history_id = MagicMock()
        mock_sent_at = MagicMock()
        mock_sent_at.__le__ = Mock(return_value=MagicMock())
        MockModel.sent_at = mock_sent_at
        from iot_app.services.mail_history_service import get_mail_history_list

        # Act
        get_mail_history_list(
            organization_id=1,
            mail_types=[],
            keyword='',
            sent_at_start=None,
            sent_at_end=date(2026, 4, 30),
            sort_column='sent_at',
            order='desc',
            page=1,
        )

        # Assert: filter が1回（終了日フィルタのみ）呼ばれること
        assert q.filter.call_count == 1

    @patch(f'{MODULE}.MailHistory')
    def test_sent_at_start_combined_with_time_min(self, MockModel):
        """機能固有: sent_at_start は time.min (00:00:00) を付加した datetime に変換される"""
        # Arrange: sent_at.__ge__ の呼び出し引数を検証するためモックの比較演算子を設定
        q = make_mock_query([], 0)
        MockModel.query.filter_by.return_value = q
        MockModel.mail_history_id = MagicMock()
        mock_sent_at = MagicMock()
        mock_sent_at.__ge__ = Mock(return_value=MagicMock())
        MockModel.sent_at = mock_sent_at
        from iot_app.services.mail_history_service import get_mail_history_list

        # Act
        get_mail_history_list(
            organization_id=1,
            mail_types=[],
            keyword='',
            sent_at_start=date(2026, 4, 1),
            sent_at_end=None,
            sort_column='sent_at',
            order='desc',
            page=1,
        )

        # Assert: sent_at.__ge__ が time.min (00:00:00) 付加の datetime で呼ばれること
        mock_sent_at.__ge__.assert_called_once_with(datetime(2026, 4, 1, 0, 0, 0))

    @patch(f'{MODULE}.MailHistory')
    def test_sent_at_end_combined_with_time_23_59_59(self, MockModel):
        """機能固有: sent_at_end は time(23, 59, 59) を付加した datetime に変換される"""
        # Arrange: sent_at.__le__ の呼び出し引数を検証するためモックの比較演算子を設定
        q = make_mock_query([], 0)
        MockModel.query.filter_by.return_value = q
        MockModel.mail_history_id = MagicMock()
        mock_sent_at = MagicMock()
        mock_sent_at.__le__ = Mock(return_value=MagicMock())
        MockModel.sent_at = mock_sent_at
        from iot_app.services.mail_history_service import get_mail_history_list

        # Act
        get_mail_history_list(
            organization_id=1,
            mail_types=[],
            keyword='',
            sent_at_start=None,
            sent_at_end=date(2026, 4, 30),
            sort_column='sent_at',
            order='desc',
            page=1,
        )

        # Assert: sent_at.__le__ が time(23, 59, 59) 付加の datetime で呼ばれること
        mock_sent_at.__le__.assert_called_once_with(datetime(2026, 4, 30, 23, 59, 59))

    @patch(f'{MODULE}.or_')
    @patch(f'{MODULE}.MailHistory')
    def test_applies_all_filters_combined(self, MockModel, mock_or):
        """全体確認: mail_type・keyword・sent_at_start・sent_at_end を全て指定した場合、filter が計4回適用される"""
        # Arrange: 全フィルタ条件を指定し、各フィルタが干渉せず独立して適用されることを検証
        q = make_mock_query([], 0)
        MockModel.query.filter_by.return_value = q
        MockModel.mail_history_id = MagicMock()
        mock_sent_at = MagicMock()
        mock_sent_at.__ge__ = Mock(return_value=MagicMock())
        mock_sent_at.__le__ = Mock(return_value=MagicMock())
        MockModel.sent_at = mock_sent_at
        mock_or.return_value = MagicMock()
        from iot_app.services.mail_history_service import get_mail_history_list

        # Act
        get_mail_history_list(
            organization_id=1,
            mail_types=[1, 2],
            keyword='テスト',
            sent_at_start=date(2026, 4, 1),
            sent_at_end=date(2026, 4, 30),
            sort_column='sent_at',
            order='desc',
            page=1,
        )

        # Assert: mail_type + keyword + 開始日 + 終了日 で filter が計4回呼ばれること
        assert q.filter.call_count == 4

    @patch(f'{MODULE}.MailHistory')
    def test_returned_record_has_no_missing_list_fields(self, MockModel):
        """機能固有: 一覧取得レコードのフロント表示項目が全て欠損なし"""
        # Arrange: 一覧テンプレートが参照する全フィールドを明示設定したモックレコード
        mock_record = make_mail_history_mock(
            mail_type=1,
            subject='テスト件名',
            body='テスト本文',
            sent_at=datetime(2026, 4, 10, 12, 0, 0),
            mail_history_uuid='test-uuid-001',
        )
        q = make_mock_query([mock_record], 1)
        MockModel.query.filter_by.return_value = q
        MockModel.mail_history_id = MagicMock()
        from iot_app.services.mail_history_service import get_mail_history_list

        # Act
        records, _ = get_mail_history_list(
            organization_id=1,
            mail_types=[],
            keyword='',
            sent_at_start=None,
            sent_at_end=None,
            sort_column='sent_at',
            order='desc',
            page=1,
        )

        # Assert: 一覧テンプレートが参照する全フィールドが None でないこと
        assert len(records) == 1
        record = records[0]
        assert record.mail_type is not None
        assert record.subject is not None
        assert record.body is not None
        assert record.sent_at is not None
        assert record.mail_history_uuid is not None


# ============================================================
# 6. get_mail_history_detail
# 観点: 2.1 正常系処理, 2.2 対象データ存在チェック, 2.4 データフィルタリング
# ============================================================

@pytest.mark.unit
class TestGetMailHistoryDetail:
    """get_mail_history_detail - メール通知履歴詳細取得
    観点: 2.1 正常系処理, 2.2 対象データ存在チェック, 2.4 データフィルタリング
    """

    @patch(f'{MODULE}.MailHistory')
    def test_returns_record_when_found(self, MockModel):
        """2.1.1: 正常系 - 一致する UUID と組織 ID のレコードを返す"""
        # Arrange: UUID='abc-123', organization_id=1 に一致するレコードを設定
        mock_history = make_mail_history_mock(mail_history_uuid='abc-123', organization_id=1)
        MockModel.query.filter_by.return_value.first.return_value = mock_history
        from iot_app.services.mail_history_service import get_mail_history_detail

        # Act
        result = get_mail_history_detail('abc-123', organization_id=1)

        # Assert: 設定したモックレコードが返ること
        assert result == mock_history
        # Assert: filter_by が UUID と organization_id の両方で呼ばれること
        MockModel.query.filter_by.assert_called_once_with(
            mail_history_uuid='abc-123',
            organization_id=1,
        )

    @patch(f'{MODULE}.MailHistory')
    def test_returns_none_when_uuid_not_found(self, MockModel):
        """2.2.2: UUID が存在しない場合は None を返す"""
        # Arrange: DB に該当レコードなし
        MockModel.query.filter_by.return_value.first.return_value = None
        from iot_app.services.mail_history_service import get_mail_history_detail

        # Act
        result = get_mail_history_detail('no-such-uuid', organization_id=1)

        # Assert: None が返ること
        assert result is None

    @patch(f'{MODULE}.MailHistory')
    def test_returns_none_when_wrong_organization(self, MockModel):
        """2.4.1: organization_id が一致しない場合は None を返す（データスコープ制限）"""
        # Arrange: 異なる organization_id では該当レコードなし
        MockModel.query.filter_by.return_value.first.return_value = None
        from iot_app.services.mail_history_service import get_mail_history_detail

        # Act
        result = get_mail_history_detail('abc-123', organization_id=999)

        # Assert: None が返ること
        assert result is None
        # Assert: filter_by が organization_id=999 で呼ばれること（スコープ制限確認）
        MockModel.query.filter_by.assert_called_once_with(
            mail_history_uuid='abc-123',
            organization_id=999,
        )

    @patch(f'{MODULE}.MailHistory')
    def test_returned_record_has_no_missing_detail_fields(self, MockModel):
        """機能固有: 詳細取得レコードのフロント表示項目が全て欠損なし"""
        # Arrange: 詳細モーダル・view が参照する全フィールドを明示設定したモックレコード
        # 宛先(recipient_email)は mail_recipient テーブルから別途取得するため本テストの対象外
        mock_history = make_mail_history_mock(
            mail_history_id=1,
            mail_type=1,
            sender_email='sender@example.com',
            sent_at=datetime(2026, 4, 10, 12, 0, 0),
            subject='テスト件名',
            body='テスト本文',
            mail_history_uuid='test-uuid-001',
        )
        MockModel.query.filter_by.return_value.first.return_value = mock_history
        from iot_app.services.mail_history_service import get_mail_history_detail

        # Act
        result = get_mail_history_detail('test-uuid-001', organization_id=1)

        # Assert: 詳細テンプレート・view が参照する全フィールドが None でないこと
        assert result.mail_history_id is not None
        assert result.mail_type is not None
        assert result.sender_email is not None
        assert result.sent_at is not None
        assert result.subject is not None
        assert result.body is not None


# ============================================================
# 7. get_mail_recipients
# 観点: 2.1 正常系処理, 3.1.1 検索条件指定, 3.1.4 検索結果戻り値ハンドリング
# ============================================================

@pytest.mark.unit
class TestGetMailRecipients:
    """get_mail_recipients - メール宛先一覧取得
    観点: 2.1 正常系処理, 3.1.1 検索条件指定, 3.1.4 検索結果戻り値ハンドリング
    """

    @patch(f'{MODULE}.MailRecipient')
    def test_returns_recipients_when_found(self, MockModel):
        """2.1.1: 正常系 - 宛先レコードのリストを返す"""
        # Arrange: 宛先2件を返すようにモック設定
        mock_recipients = [
            make_mail_recipient_mock(user_id=10, recipient_email='a@example.com'),
            make_mail_recipient_mock(user_id=11, recipient_email='b@example.com'),
        ]
        MockModel.query.filter_by.return_value.order_by.return_value.all.return_value = mock_recipients
        from iot_app.services.mail_history_service import get_mail_recipients

        # Act
        result = get_mail_recipients(1)

        # Assert: 設定したモックレコードのリストが返ること
        assert result == mock_recipients

    @patch(f'{MODULE}.MailRecipient')
    def test_returns_empty_when_no_recipients(self, MockModel):
        """3.1.4.2: 宛先が存在しない場合は空リストを返す"""
        # Arrange: DB に該当レコードなし
        MockModel.query.filter_by.return_value.order_by.return_value.all.return_value = []
        from iot_app.services.mail_history_service import get_mail_recipients

        # Act
        result = get_mail_recipients(999)

        # Assert: 空リストが返ること
        assert result == []

    @patch(f'{MODULE}.MailRecipient')
    def test_filters_by_mail_history_id(self, MockModel):
        """3.1.1.1: mail_history_id で宛先を絞り込む"""
        # Arrange
        MockModel.query.filter_by.return_value.order_by.return_value.all.return_value = []
        from iot_app.services.mail_history_service import get_mail_recipients

        # Act
        get_mail_recipients(42)

        # Assert: filter_by が mail_history_id=42 で呼ばれること
        MockModel.query.filter_by.assert_called_once_with(mail_history_id=42)

    @patch(f'{MODULE}.MailRecipient')
    def test_orders_by_user_id_asc(self, MockModel):
        """機能固有: user_id ASC でソートされる"""
        # Arrange: user_id カラムの .asc() が呼ばれることを検証
        mock_user_id_col = MagicMock()
        MockModel.user_id = mock_user_id_col
        MockModel.query.filter_by.return_value.order_by.return_value.all.return_value = []
        from iot_app.services.mail_history_service import get_mail_recipients

        # Act
        get_mail_recipients(1)

        # Assert: user_id カラムの .asc() が呼ばれること
        mock_user_id_col.asc.assert_called_once()
