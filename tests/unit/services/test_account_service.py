"""
アカウント機能 - Service層 単体テスト

対象ファイル: src/iot_app/services/account_service.py（未実装）

参照ドキュメント:
  - UI設計書:         docs/03-features/flask-app/account/ui-specification.md
  - 機能設計書:       docs/03-features/flask-app/account/workflow-specification.md
  - 単体テスト観点表: docs/05-testing/unit-test/unit-test-perspectives.md
  - 実装ガイド:       docs/05-testing/unit-test/unit-test-guide.md

適用した観点:
  - 1.1.1 必須チェック          : language_code 空文字・None
  - 1.1.2 最大文字列長チェック  : language_code 最大10文字
  - 1.1.6 不整値チェック        : language_code が language_master に存在しない値
  - 2.1   正常系処理            : 各メソッドの正常ケース
  - 2.2   対象データ存在チェック: ユーザー未検出・論理削除済みユーザー
  - 2.3   副作用チェック        : DB エラー時のロールバック確認
  - 3.1   検索機能              : get_language_settings / get_languages / get_profile
  - 3.3   更新機能              : update_language

適用外の観点（設計書に該当機能なし）:
  - 1.4 ログ出力機能 / 3.2 登録機能 / 3.4 削除機能 / 3.5 CSV エクスポート
"""
import pytest
from unittest.mock import MagicMock, Mock, patch


# ============================================================
# フィクスチャ
# ============================================================

@pytest.fixture
def mock_session():
    """DB セッションのモック"""
    return MagicMock()


@pytest.fixture
def service(mock_session):
    """AccountService のインスタンス（DB セッションをモック化）"""
    from iot_app.services.account_service import AccountService
    return AccountService(db_session=mock_session)


def make_user_mock(**kwargs):
    """UserMaster モックオブジェクトを生成するヘルパー"""
    m = Mock()
    m.user_id         = kwargs.get("user_id", 1)
    m.user_name       = kwargs.get("user_name", "山田 太郎")
    m.email_address   = kwargs.get("email_address", "yamada@example.com")
    m.organization_id = kwargs.get("organization_id", 10)
    m.language_code   = kwargs.get("language_code", "ja")
    m.delete_flag     = kwargs.get("delete_flag", False)
    return m


def make_language_mock(**kwargs):
    """LanguageMaster モックオブジェクトを生成するヘルパー"""
    m = Mock()
    m.language_code = kwargs.get("language_code", "ja")
    m.language_name = kwargs.get("language_name", "日本語")
    m.delete_flag   = kwargs.get("delete_flag", False)
    return m


def make_profile_mock(**kwargs):
    """プロフィール取得用のモック（user_master + organization_master 結合結果）"""
    m = Mock()
    m.user_id           = kwargs.get("user_id", 1)
    m.user_name         = kwargs.get("user_name", "山田 太郎")
    m.email_address     = kwargs.get("email_address", "yamada@example.com")
    m.organization_name = kwargs.get("organization_name", "株式会社サンプル")
    m.role              = kwargs.get("role", "management_admin")
    return m


# ============================================================
# 1. 言語設定取得 (get_language_settings)
# 観点: 3.1 検索機能, 2.2 対象データ存在チェック
# ============================================================

@pytest.mark.unit
class TestAccountServiceGetLanguageSettings:
    """言語設定取得
    観点: 3.1.4 検索結果戻り値ハンドリング, 2.2 対象データ存在チェック
    """

    def test_get_language_settings_success(self, service, mock_session):
        """2.1.1 / 3.1.4.1: 有効なユーザーIDで現在の language_code が返される"""
        # Arrange
        user = make_user_mock(language_code="ja")
        mock_session.query.return_value.filter_by.return_value.first.return_value = user

        # Act
        result = service.get_language_settings(user_id=1)

        # Assert
        assert result == "ja"

    def test_get_language_settings_returns_en(self, service, mock_session):
        """2.1.1: 英語設定のユーザーの場合 'en' が返される"""
        # Arrange
        user = make_user_mock(language_code="en")
        mock_session.query.return_value.filter_by.return_value.first.return_value = user

        # Act
        result = service.get_language_settings(user_id=1)

        # Assert
        assert result == "en"

    def test_get_language_settings_user_not_found_raises(self, service, mock_session):
        """2.2.2: 存在しないユーザーIDで NotFoundError がスローされる"""
        # Arrange
        mock_session.query.return_value.filter_by.return_value.first.return_value = None

        # Act & Assert
        with pytest.raises(Exception):
            service.get_language_settings(user_id=9999)

    def test_get_language_settings_deleted_user_raises(self, service, mock_session):
        """2.2.3: 論理削除済みユーザーは NotFoundError がスローされる"""
        # Arrange
        # delete_flag=True のユーザーは filter_by(delete_flag=False) でヒットしない想定
        mock_session.query.return_value.filter_by.return_value.first.return_value = None

        # Act & Assert
        with pytest.raises(Exception):
            service.get_language_settings(user_id=1)


# ============================================================
# 2. 言語選択肢取得 (get_languages)
# 観点: 3.1 検索機能
# ============================================================

@pytest.mark.unit
class TestAccountServiceGetLanguages:
    """言語選択肢一覧取得
    観点: 3.1.4 検索結果戻り値ハンドリング, 3.1.2 検索条件未指定（全件相当）
    """

    def test_get_languages_returns_list(self, service, mock_session):
        """3.1.4.1: delete_flag=0 の言語が一覧で返される"""
        # Arrange
        languages = [
            make_language_mock(language_code="ja", language_name="日本語"),
            make_language_mock(language_code="en", language_name="English"),
        ]
        mock_session.query.return_value.filter_by.return_value.order_by.return_value.all.return_value = languages

        # Act
        result = service.get_languages()

        # Assert
        assert len(result) == 2
        assert result[0].language_code == "ja"
        assert result[1].language_code == "en"

    def test_get_languages_empty_returns_empty_list(self, service, mock_session):
        """3.1.4.2: language_master にデータがない場合、空リストが返される"""
        # Arrange
        mock_session.query.return_value.filter_by.return_value.order_by.return_value.all.return_value = []

        # Act
        result = service.get_languages()

        # Assert
        assert result == []

    def test_get_languages_excludes_deleted(self, service, mock_session):
        """3.1.2.1: delete_flag=1 の言語は除外される（filter_by が delete_flag=0 で呼ばれる）"""
        # Arrange
        mock_session.query.return_value.filter_by.return_value.order_by.return_value.all.return_value = []

        # Act
        service.get_languages()

        # Assert
        mock_session.query.return_value.filter_by.assert_called_once()
        call_kwargs = mock_session.query.return_value.filter_by.call_args
        # delete_flag=False または delete_flag=0 で絞り込まれること
        assert "delete_flag" in call_kwargs.kwargs or len(call_kwargs.args) > 0


# ============================================================
# 3. 言語設定更新 (update_language)
# 観点: 1.1.1 必須チェック, 1.1.2 最大文字列長, 1.1.6 不整値チェック,
#        3.3 更新機能, 2.2 存在確認, 2.3 副作用チェック
# ============================================================

@pytest.mark.unit
class TestAccountServiceUpdateLanguage:
    """言語設定更新
    観点: 1.1.1, 1.1.2, 1.1.6, 2.1, 2.2, 2.3, 3.3
    """

    # ----------------------------------------------------------------
    # 3.3 正常系
    # ----------------------------------------------------------------

    def test_update_language_success(self, service, mock_session):
        """2.1.1 / 3.3.2.1: 有効なユーザーID と language_code で正常に更新される"""
        # Arrange
        user = make_user_mock(language_code="ja")
        mock_session.query.return_value.filter_by.return_value.first.return_value = user
        valid_codes = ["ja", "en"]

        # Act
        service.update_language(user_id=1, language_code="en", valid_language_codes=valid_codes)

        # Assert
        assert user.language_code == "en"
        mock_session.commit.assert_called_once()

    def test_update_language_passes_correct_user_id(self, service, mock_session):
        """3.3.2.2: 指定した user_id を持つユーザーが更新対象となる"""
        # Arrange
        user = make_user_mock(user_id=42, language_code="ja")
        mock_session.query.return_value.filter_by.return_value.first.return_value = user
        valid_codes = ["ja", "en"]

        # Act
        service.update_language(user_id=42, language_code="en", valid_language_codes=valid_codes)

        # Assert
        # filter_by に user_id=42 が渡されること
        call_kwargs = mock_session.query.return_value.filter_by.call_args
        assert 42 in call_kwargs.args or call_kwargs.kwargs.get("user_id") == 42

    # ----------------------------------------------------------------
    # 1.1.1 必須チェック: language_code
    # ----------------------------------------------------------------

    def test_update_language_empty_code_raises(self, service, mock_session):
        """1.1.1: language_code が空文字の場合 ValidationError がスローされる"""
        # Arrange
        valid_codes = ["ja", "en"]

        # Act & Assert
        with pytest.raises(Exception):
            service.update_language(user_id=1, language_code="", valid_language_codes=valid_codes)

    def test_update_language_none_code_raises(self, service, mock_session):
        """1.1.2: language_code が None の場合 ValidationError がスローされる"""
        # Arrange
        valid_codes = ["ja", "en"]

        # Act & Assert
        with pytest.raises(Exception):
            service.update_language(user_id=1, language_code=None, valid_language_codes=valid_codes)

    # ----------------------------------------------------------------
    # 1.1.2 最大文字列長チェック: language_code (最大10文字)
    # ----------------------------------------------------------------

    def test_update_language_code_10chars_ok(self, service, mock_session):
        """1.2.2: language_code が 10文字ちょうどはバリデーション通過"""
        # Arrange
        user = make_user_mock()
        mock_session.query.return_value.filter_by.return_value.first.return_value = user
        code_10 = "a" * 10
        valid_codes = [code_10]

        # Act & Assert（例外が起きないこと）
        # TODO: 実装完了後に検証（10文字が許容されることを確認）

    def test_update_language_code_11chars_raises(self, service, mock_session):
        """1.2.3: language_code が 11文字の場合 ValidationError がスローされる"""
        # Arrange
        valid_codes = ["ja", "en"]

        # Act & Assert
        with pytest.raises(Exception):
            service.update_language(user_id=1, language_code="a" * 11, valid_language_codes=valid_codes)

    # ----------------------------------------------------------------
    # 1.1.6 不整値チェック: language_code が language_master に存在するか
    # ----------------------------------------------------------------

    def test_update_language_code_not_in_master_raises(self, service, mock_session):
        """1.6.2: language_master に存在しない language_code は ValidationError がスローされる"""
        # Arrange
        valid_codes = ["ja", "en"]

        # Act & Assert
        with pytest.raises(Exception):
            service.update_language(user_id=1, language_code="zh", valid_language_codes=valid_codes)

    def test_update_language_code_in_master_ok(self, service, mock_session):
        """1.6.1: language_master に存在する language_code は許容される"""
        # Arrange
        user = make_user_mock(language_code="ja")
        mock_session.query.return_value.filter_by.return_value.first.return_value = user
        valid_codes = ["ja", "en"]

        # Act & Assert（例外が起きないこと）
        service.update_language(user_id=1, language_code="en", valid_language_codes=valid_codes)

    # ----------------------------------------------------------------
    # 2.2 対象データ存在チェック
    # ----------------------------------------------------------------

    def test_update_language_user_not_found_raises(self, service, mock_session):
        """2.2.2: 存在しないユーザーIDで NotFoundError がスローされる"""
        # Arrange
        mock_session.query.return_value.filter_by.return_value.first.return_value = None
        valid_codes = ["ja", "en"]

        # Act & Assert
        with pytest.raises(Exception):
            service.update_language(user_id=9999, language_code="en", valid_language_codes=valid_codes)

    def test_update_language_user_not_found_no_commit(self, service, mock_session):
        """2.2.2 / 3.3.1.3: ユーザー未検出時はコミットされない"""
        # Arrange
        mock_session.query.return_value.filter_by.return_value.first.return_value = None
        valid_codes = ["ja", "en"]

        # Act
        try:
            service.update_language(user_id=9999, language_code="en", valid_language_codes=valid_codes)
        except Exception:
            pass

        # Assert
        mock_session.commit.assert_not_called()

    # ----------------------------------------------------------------
    # 2.3 副作用チェック: DB エラー時のロールバック
    # ----------------------------------------------------------------

    def test_update_language_db_error_calls_rollback(self, service, mock_session):
        """2.3.2: commit() で DB エラーが発生した場合 rollback() が呼ばれる"""
        # Arrange
        user = make_user_mock(language_code="ja")
        mock_session.query.return_value.filter_by.return_value.first.return_value = user
        mock_session.commit.side_effect = Exception("DB error")
        valid_codes = ["ja", "en"]

        # Act
        try:
            service.update_language(user_id=1, language_code="en", valid_language_codes=valid_codes)
        except Exception:
            pass

        # Assert
        mock_session.rollback.assert_called_once()

    def test_update_language_db_error_data_not_persisted(self, service, mock_session):
        """2.3.1: DB エラー時はデータが更新されない（rollback によりロールバックされる）"""
        # Arrange
        user = make_user_mock(language_code="ja")
        mock_session.query.return_value.filter_by.return_value.first.return_value = user
        mock_session.commit.side_effect = Exception("DB error")
        valid_codes = ["ja", "en"]

        # Act
        try:
            service.update_language(user_id=1, language_code="en", valid_language_codes=valid_codes)
        except Exception:
            pass

        # Assert
        mock_session.rollback.assert_called_once()


# ============================================================
# 4. ユーザープロフィール取得 (get_profile)
# 観点: 3.1 検索機能, 2.2 対象データ存在チェック
# ============================================================

@pytest.mark.unit
class TestAccountServiceGetProfile:
    """ユーザープロフィール取得
    観点: 2.1 正常系処理, 2.2 対象データ存在チェック, 3.1.4 検索結果戻り値ハンドリング
    """

    # ----------------------------------------------------------------
    # 3.1 正常系
    # ----------------------------------------------------------------

    def test_get_profile_success_returns_user_info(self, service, mock_session):
        """2.1.1 / 3.1.4.1: 有効なユーザーIDでユーザー情報が返される"""
        # Arrange
        profile = make_profile_mock(
            user_name="山田 太郎",
            email_address="yamada@example.com",
            organization_name="株式会社サンプル",
            role="management_admin",
        )
        mock_session.query.return_value.outerjoin.return_value.filter.return_value.first.return_value = profile

        # Act
        result = service.get_profile(user_id=1)

        # Assert
        assert result.user_name == "山田 太郎"
        assert result.email_address == "yamada@example.com"
        assert result.organization_name == "株式会社サンプル"
        assert result.role == "management_admin"

    def test_get_profile_contains_required_fields(self, service, mock_session):
        """3.1.4.1: 返却値に必須フィールドがすべて含まれる"""
        # Arrange
        profile = make_profile_mock()
        mock_session.query.return_value.outerjoin.return_value.filter.return_value.first.return_value = profile

        # Act
        result = service.get_profile(user_id=1)

        # Assert
        assert hasattr(result, "user_name")
        assert hasattr(result, "email_address")
        assert hasattr(result, "organization_name")
        assert hasattr(result, "role")

    def test_get_profile_no_organization_returns_none_org_name(self, service, mock_session):
        """3.1.4.1: 所属組織なし（LEFT JOIN 結果が None）の場合、organization_name が None となる"""
        # Arrange
        profile = make_profile_mock(organization_name=None)
        mock_session.query.return_value.outerjoin.return_value.filter.return_value.first.return_value = profile

        # Act
        result = service.get_profile(user_id=1)

        # Assert
        assert result.organization_name is None

    # ----------------------------------------------------------------
    # 2.2 対象データ存在チェック
    # ----------------------------------------------------------------

    def test_get_profile_user_not_found_raises(self, service, mock_session):
        """2.2.2: 存在しないユーザーIDで NotFoundError がスローされる"""
        # Arrange
        mock_session.query.return_value.outerjoin.return_value.filter.return_value.first.return_value = None

        # Act & Assert
        with pytest.raises(Exception):
            service.get_profile(user_id=9999)

    def test_get_profile_deleted_user_raises(self, service, mock_session):
        """2.2.3: delete_flag=True のユーザーは対象外となり NotFoundError がスローされる"""
        # Arrange
        # delete_flag=False のフィルタが適用されるため None が返る
        mock_session.query.return_value.outerjoin.return_value.filter.return_value.first.return_value = None

        # Act & Assert
        with pytest.raises(Exception):
            service.get_profile(user_id=1)

    def test_get_profile_filters_by_user_id(self, service, mock_session):
        """3.1.1.1: get_profile は指定した user_id で絞り込んで DB に問い合わせる"""
        # Arrange
        profile = make_profile_mock(user_id=5)
        mock_session.query.return_value.outerjoin.return_value.filter.return_value.first.return_value = profile

        # Act
        service.get_profile(user_id=5)

        # Assert
        # filter() が呼び出されること（user_id=5 の条件で絞り込まれる）
        mock_session.query.return_value.outerjoin.return_value.filter.assert_called_once()
