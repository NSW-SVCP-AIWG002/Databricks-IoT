"""
auth/services.py の単体テスト

観点: unit-test-perspectives.md
  - 2.1 正常系処理
  - 2.2 対象データ存在チェック
  - 1.3 エラーハンドリング

検証内容:
  - emailが一致するアクティブユーザーが存在する場合、user_id と user_type_id を返す
  - emailが一致するユーザーが存在しない場合、UnauthorizedError を送出する
  - クエリに delete_flag=False が含まれること（論理削除済みユーザーを除外）
  - DB例外は握りつぶさず上位へ伝播する
"""
import pytest
from unittest.mock import patch, MagicMock

from auth.services import find_user_by_email
from auth.exceptions import UnauthorizedError


# ---------------------------------------------------------------------------
# find_user_by_email()
# ---------------------------------------------------------------------------

@pytest.mark.unit
class TestFindUserByEmail:
    """find_user_by_email() のテスト
    観点: 2.1 正常系処理, 2.2 対象データ存在チェック, 1.3 エラーハンドリング
    """

    def test_success_returns_user_id_and_user_type_id(self):
        """2.1.1: emailが一致するアクティブユーザーが存在する場合、user_id と user_type_id を返す"""
        mock_user = MagicMock()
        mock_user.user_id = 42
        mock_user.user_type_id = 2

        with patch('auth.services.User') as mock_user_class:
            mock_user_class.query.filter_by.return_value.first.return_value = mock_user

            result = find_user_by_email('yamada@example.com')

        assert result['user_id'] == 42
        assert result['user_type_id'] == 2

    def test_not_found_raises_unauthorized(self):
        """2.2.1: emailが一致するユーザーが存在しない場合、UnauthorizedError を送出する"""
        with patch('auth.services.User') as mock_user_class:
            mock_user_class.query.filter_by.return_value.first.return_value = None

            with pytest.raises(UnauthorizedError):
                find_user_by_email('notfound@example.com')

    def test_deleted_user_is_excluded_from_query(self):
        """2.2.3: 論理削除済みユーザー（delete_flag=True）は検索対象から除外される
        （クエリに delete_flag=False が指定されていることで保証）
        """
        mock_user = MagicMock()
        mock_user.user_id = 99
        mock_user.user_type_id = 1

        with patch('auth.services.User') as mock_user_class:
            mock_user_class.query.filter_by.return_value.first.return_value = mock_user

            find_user_by_email('test@example.com')

            mock_user_class.query.filter_by.assert_called_with(
                email_address='test@example.com', delete_flag=False
            )

    def test_db_exception_propagates(self):
        """1.3.1: DB例外は握りつぶさず上位へ伝播する"""
        with patch('auth.services.User') as mock_user_class:
            mock_user_class.query.filter_by.side_effect = Exception("DB connection failed")

            with pytest.raises(Exception):
                find_user_by_email('yamada@example.com')
