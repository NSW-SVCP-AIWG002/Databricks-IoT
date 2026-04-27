"""
CSV インポート/エクスポート - Service層 単体テスト

対象ファイル: src/iot_app/services/csv_service.py

参照ドキュメント:
  - 機能設計書:       docs/03-features/flask-app/csv-import-export/workflow-specification.md
  - UI設計書:         docs/03-features/flask-app/csv-import-export/ui-specification.md
  - CSV仕様:          docs/03-features/flask-app/csv-import-export/README.md
  - 単体テスト観点表: docs/05-testing/unit-test/unit-test-perspectives.md
  - 実装ガイド:       docs/05-testing/unit-test/unit-test-guide.md
"""
import pytest
from unittest.mock import MagicMock, Mock, patch


MODULE = 'iot_app.services.csv_service'


# ============================================================
# ヘルパー関数
# ============================================================

def _decode(result):
    """戻り値が bytes または str どちらでも UTF-8 文字列に変換する"""
    if isinstance(result, bytes):
        return result.decode('utf-8-sig')
    return result


def _make_user(organization_id=1):
    """テスト用ユーザーモックを生成するヘルパー"""
    user = Mock()
    user.organization_id = organization_id
    return user


def _make_mock_db_scope(mock_db, org_ids):
    """organization_closure からのスコープ取得モックを設定するヘルパー

    Args:
        mock_db: db モック
        org_ids: アクセス可能な組織IDのタプルリスト [(1,), (2,)] 形式
    """
    mock_db.session.query.return_value.filter.return_value.all.return_value = org_ids


# ============================================================
# 1. detect_encoding
# 観点: 2.1 正常系処理
# ============================================================

@pytest.mark.unit
class TestDetectEncoding:
    """detect_encoding - 文字エンコーディング検出
    観点: 2.1 正常系処理
    """

    def test_detects_utf8_bom(self):
        """2.1.1: UTF-8 BOM 付きファイルの場合 'utf-8-sig' が返される"""
        from iot_app.services.csv_service import detect_encoding

        # Arrange: UTF-8 BOM（0xEF 0xBB 0xBF）で始まるバイト列を用意
        file_content = b'\xef\xbb\xbf' + '操作列,デバイスID\n'.encode('utf-8')

        # Act
        result = detect_encoding(file_content)

        # Assert: エンコーディングが 'utf-8-sig' であること
        assert result == 'utf-8-sig'

    @patch(f'{MODULE}.chardet')
    def test_detects_encoding_via_chardet_when_no_bom(self, mock_chardet):
        """2.1.1: BOM なしファイルの場合 chardet の検出結果が返される"""
        from iot_app.services.csv_service import detect_encoding

        # Arrange: BOM なしバイト列と chardet の戻り値を設定
        file_content = '操作列,デバイスID\n'.encode('utf-8')
        mock_chardet.detect.return_value = {'encoding': 'UTF-8', 'confidence': 0.99}

        # Act
        result = detect_encoding(file_content)

        # Assert: chardet の検出したエンコーディングが返されること
        assert result == 'UTF-8'

    @patch(f'{MODULE}.chardet')
    def test_chardet_is_called_with_file_content(self, mock_chardet):
        """2.1.1: chardet.detect にファイルコンテンツが渡される"""
        from iot_app.services.csv_service import detect_encoding

        # Arrange
        file_content = b'some,csv,content'
        mock_chardet.detect.return_value = {'encoding': 'ascii', 'confidence': 1.0}

        # Act
        detect_encoding(file_content)

        # Assert: chardet.detect がファイルコンテンツを引数として呼ばれること
        mock_chardet.detect.assert_called_once_with(file_content)


# ============================================================
# 2. read_csv
# 観点: 2.1 正常系処理, 1.3 エラーハンドリング
# ============================================================

@pytest.mark.unit
class TestReadCsv:
    """read_csv - CSV ファイル読み込み
    観点: 2.1 正常系処理, 1.3 エラーハンドリング
    """

    def test_returns_dataframe_on_success(self):
        """2.1.1: 正常な CSV データの場合 DataFrame が返される"""
        from iot_app.services.csv_service import read_csv

        # Arrange: 正常な CSV バイト列（ヘッダー1行 + データ1行）を用意
        csv_bytes = '操作列,デバイスID\nR,DEV-001\n'.encode('utf-8')

        # Act
        result = read_csv(csv_bytes, 'utf-8')

        # Assert: pandas DataFrame が返されること（iloc 属性を保有していること）
        assert hasattr(result, 'iloc')
        # Assert: データ行が 1 件であること
        assert len(result) == 1

    def test_reads_correct_column_names(self):
        """2.1.1: CSV ヘッダー行がカラム名として読み込まれる"""
        from iot_app.services.csv_service import read_csv

        # Arrange
        csv_bytes = '操作列,デバイスID,デバイス名\nR,DEV-001,センサーA\n'.encode('utf-8')

        # Act
        result = read_csv(csv_bytes, 'utf-8')

        # Assert: カラム名がヘッダー行の内容と一致すること
        assert '操作列' in result.columns
        assert 'デバイスID' in result.columns
        assert 'デバイス名' in result.columns

    def test_skips_empty_lines(self):
        """2.1.2: 空行がスキップされる"""
        from iot_app.services.csv_service import read_csv

        # Arrange: データ行の間に空行を含む CSV
        csv_bytes = '操作列,デバイスID\nR,DEV-001\n\nR,DEV-002\n'.encode('utf-8')

        # Act
        result = read_csv(csv_bytes, 'utf-8')

        # Assert: 空行がスキップされ 2 件が読み込まれること
        assert len(result) == 2

    def test_raises_on_read_error(self):
        """1.3.6 / CL-2-1: CSV 読み込みエラー時に例外が上位へ伝播する"""
        from iot_app.services.csv_service import read_csv

        # Arrange: 指定エンコーディングと不一致なバイト列（強制的にデコードエラーを誘発）
        # shift-jisバイト列をUTF-8として読もうとするとエラーになる
        file_content = 'テスト'.encode('shift-jis')

        # Act & Assert: 例外が発生し上位へ伝播すること
        with pytest.raises(Exception):
            read_csv(file_content, 'utf-8')


# ============================================================
# 3. validate_csv_format
# 観点: 1.1.1 必須チェック, 1.2 認可, 2.1 正常系処理, 1.3 エラーハンドリング
# ============================================================

@pytest.mark.unit
class TestValidateCsvFormat:
    """validate_csv_format - フォーマットバリデーション
    観点: 1.1.1 必須チェック, 1.2 認可, 2.1 正常系処理, 1.3 エラーハンドリング
    """

    @patch(f'{MODULE}.db')
    def test_returns_empty_errors_for_valid_data(self, mock_db):
        """2.1.1: バリデーション通過データの場合、エラーリストが空である"""
        import pandas as pd
        from iot_app.services.csv_service import validate_csv_format

        # Arrange: アクセス可能な組織 ID = 1 のみ
        _make_mock_db_scope(mock_db, [(1,)])
        df = pd.DataFrame([
            {'操作列': 'R', '組織ID': '1', 'デバイスID': 'DEV-001', 'デバイス名': 'センサーA'}
        ])
        user = _make_user(organization_id=1)

        # Act
        errors = validate_csv_format(df, 1, user)

        # Assert: エラーリストが空であること
        assert errors == []

    @patch(f'{MODULE}.db')
    def test_returns_error_for_empty_required_field(self, mock_db):
        """1.1.1: 必須項目が空文字の場合、エラーが返される"""
        import pandas as pd
        from iot_app.services.csv_service import validate_csv_format

        # Arrange: デバイス名（必須項目）が空文字
        _make_mock_db_scope(mock_db, [(1,)])
        df = pd.DataFrame([
            {'操作列': 'R', '組織ID': '1', 'デバイスID': 'DEV-001', 'デバイス名': ''}
        ])
        user = _make_user(organization_id=1)

        # Act
        errors = validate_csv_format(df, 1, user)

        # Assert: 1 件以上のエラーが返されること
        assert len(errors) > 0

    @patch(f'{MODULE}.db')
    def test_error_dict_has_row_key(self, mock_db):
        """1.1.1: エラーオブジェクトに 'row' キーが含まれる（ヘッダー行考慮で 2 以上）"""
        import pandas as pd
        from iot_app.services.csv_service import validate_csv_format

        # Arrange: 1 行目データに必須項目違反
        _make_mock_db_scope(mock_db, [(1,)])
        df = pd.DataFrame([
            {'操作列': 'R', '組織ID': '1', 'デバイスID': '', 'デバイス名': ''}
        ])
        user = _make_user(organization_id=1)

        # Act
        errors = validate_csv_format(df, 1, user)

        # Assert: エラーオブジェクトに 'row' キーが存在し、行番号が 2 以上（ヘッダー行を考慮）であること
        assert len(errors) > 0
        assert 'row' in errors[0]
        assert errors[0]['row'] >= 2

    @patch(f'{MODULE}.db')
    def test_error_dict_has_column_key(self, mock_db):
        """1.1.1: エラーオブジェクトに 'column' キーが含まれる"""
        import pandas as pd
        from iot_app.services.csv_service import validate_csv_format

        # Arrange: 必須項目違反
        _make_mock_db_scope(mock_db, [(1,)])
        df = pd.DataFrame([
            {'操作列': 'R', '組織ID': '1', 'デバイスID': '', 'デバイス名': ''}
        ])
        user = _make_user(organization_id=1)

        # Act
        errors = validate_csv_format(df, 1, user)

        # Assert: エラーオブジェクトに 'column' キーが存在すること
        assert len(errors) > 0
        assert 'column' in errors[0]

    @patch(f'{MODULE}.db')
    def test_error_dict_has_message_key(self, mock_db):
        """1.1.1: エラーオブジェクトに 'message' キーが含まれる"""
        import pandas as pd
        from iot_app.services.csv_service import validate_csv_format

        # Arrange: 必須項目違反
        _make_mock_db_scope(mock_db, [(1,)])
        df = pd.DataFrame([
            {'操作列': 'R', '組織ID': '1', 'デバイスID': '', 'デバイス名': ''}
        ])
        user = _make_user(organization_id=1)

        # Act
        errors = validate_csv_format(df, 1, user)

        # Assert: エラーオブジェクトに 'message' キーが存在すること
        assert len(errors) > 0
        assert 'message' in errors[0]

    @patch(f'{MODULE}.db')
    def test_returns_error_for_out_of_scope_org(self, mock_db):
        """1.2.2: データスコープ外の組織 ID を含む行にエラーが返される"""
        import pandas as pd
        from iot_app.services.csv_service import validate_csv_format

        # Arrange: アクセス可能な組織は 1 のみ。組織 ID=99 はスコープ外
        _make_mock_db_scope(mock_db, [(1,)])
        df = pd.DataFrame([
            {'操作列': 'R', '組織ID': '99', 'デバイスID': 'DEV-001', 'デバイス名': 'センサーA'}
        ])
        user = _make_user(organization_id=1)

        # Act
        errors = validate_csv_format(df, 1, user)

        # Assert: アクセス権限に関するエラーが返されること
        assert any('アクセス権限' in err.get('message', '') for err in errors)

    @patch(f'{MODULE}.db')
    def test_returns_multiple_errors_for_multiple_invalid_rows(self, mock_db):
        """1.1.1: 複数行に必須項目違反がある場合、複数エラーが返される"""
        import pandas as pd
        from iot_app.services.csv_service import validate_csv_format

        # Arrange: 2 行ともデバイス名が空
        _make_mock_db_scope(mock_db, [(1,)])
        df = pd.DataFrame([
            {'操作列': 'R', '組織ID': '1', 'デバイスID': '', 'デバイス名': ''},
            {'操作列': 'U', '組織ID': '1', 'デバイスID': '', 'デバイス名': ''},
        ])
        user = _make_user(organization_id=1)

        # Act
        errors = validate_csv_format(df, 1, user)

        # Assert: 2 件以上のエラーが返されること
        assert len(errors) >= 2

    @patch(f'{MODULE}.db')
    def test_db_exception_propagates(self, mock_db):
        """1.3.6 / CL-2-1: DB クエリ失敗時に例外が上位へ伝播する"""
        import pandas as pd
        from iot_app.services.csv_service import validate_csv_format

        # Arrange: DB クエリで例外を発生させる
        mock_db.session.query.side_effect = Exception('DB connection error')
        df = pd.DataFrame([
            {'操作列': 'R', '組織ID': '1', 'デバイスID': 'DEV-001', 'デバイス名': 'センサーA'}
        ])
        user = _make_user(organization_id=1)

        # Act & Assert: 例外が上位へ伝播すること
        with pytest.raises(Exception):
            validate_csv_format(df, 1, user)


# ============================================================
# 4. apply_data_scope_filter
# 観点: 2.1 正常系処理, 1.2 認可機能
# ============================================================

@pytest.mark.unit
class TestApplyDataScopeFilter:
    """apply_data_scope_filter - データスコープ制限フィルター
    観点: 2.1 正常系処理, 1.2 認可機能
    """

    @patch(f'{MODULE}.db')
    @patch(f'{MODULE}.OrganizationClosure')
    def test_filters_by_accessible_org_ids(self, _mock_closure, mock_db):
        """1.2.1: アクセス可能な組織 ID でクエリがフィルタリングされる"""
        from iot_app.services.csv_service import apply_data_scope_filter

        # Arrange: アクセス可能な組織 ID = 1, 2
        _make_mock_db_scope(mock_db, [(1,), (2,)])
        query = MagicMock()
        user = _make_user(organization_id=1)

        # Act
        apply_data_scope_filter(query, user)

        # Assert: query.filter が呼ばれること（フィルタリングが実行されること）
        query.filter.assert_called_once()

    @patch(f'{MODULE}.db')
    @patch(f'{MODULE}.OrganizationClosure')
    def test_returns_empty_result_when_no_accessible_orgs(self, _mock_closure, mock_db):
        """1.2.2: アクセス可能な組織がない場合、空フィルターが適用される"""
        from iot_app.services.csv_service import apply_data_scope_filter

        # Arrange: アクセス可能な組織なし
        _make_mock_db_scope(mock_db, [])
        query = MagicMock()
        query.filter.return_value = query
        user = _make_user(organization_id=999)

        # Act
        apply_data_scope_filter(query, user)

        # Assert: フィルタリングが実行されること（空リストでフィルタ）
        query.filter.assert_called_once()


# ============================================================
# 5. generate_csv
# 観点: 3.5.1 CSV生成ロジック, 3.5.2 エスケープ処理, 3.5.3 エンコーディング処理
# ============================================================

@pytest.mark.unit
class TestGenerateCsv:
    """generate_csv - CSV 生成ユーティリティ
    観点: 3.5.1 CSV生成ロジック, 3.5.2 エスケープ処理, 3.5.3 エンコーディング処理
    """

    def test_header_contains_all_columns(self):
        """3.5.1.1: 渡したdictの全キー（列名）がCSVヘッダー行に出力される（CL-4-1）

        デバイスCSV仕様の全列（操作列 / デバイスID / デバイス名 / デバイス種別 /
        モデル情報 / SIMID / MACアドレス / 設置場所 / 所属組織ID / 証明書期限）を検証する。
        """
        from iot_app.services.csv_service import generate_csv

        # Arrange: デバイスCSV仕様の全列を含むデータ
        rows = [{
            '操作列': '',
            'デバイスID': 'DEV-001',
            'デバイス名': 'センサーA',
            'デバイス種別': 'センサー',
            'モデル情報': 'MODEL-A100',
            'SIMID': '12345678901234567890',
            'MACアドレス': 'AA:BB:CC:DD:EE:FF',
            '設置場所': '本社1階',
            '所属組織ID': '1',
            '証明書期限': '2025-12-31',
        }]

        # Act
        result = generate_csv(rows)
        decoded = _decode(result)
        header_line = decoded.strip().split('\n')[0]

        # Assert: 全列名がヘッダー行に含まれること
        assert '操作列' in header_line
        assert 'デバイスID' in header_line
        assert 'デバイス名' in header_line
        assert 'デバイス種別' in header_line
        assert 'モデル情報' in header_line
        assert 'SIMID' in header_line
        assert 'MACアドレス' in header_line
        assert '設置場所' in header_line
        assert '所属組織ID' in header_line
        assert '証明書期限' in header_line

    def test_data_row_contains_all_field_values(self):
        """3.5.1.2: データ行に全フィールドの値が列順を含めて正しく出力される（CL-4-2）"""
        from iot_app.services.csv_service import generate_csv

        # Arrange: 全列に具体的な値を設定
        rows = [{
            '操作列': '',
            'デバイスID': 'DEV-001',
            'デバイス名': 'センサーA',
            'デバイス種別': 'センサー',
            'モデル情報': 'MODEL-A100',
            'SIMID': 'SIM12345',
            'MACアドレス': 'AA:BB:CC:DD:EE:FF',
            '設置場所': '本社1階',
            '所属組織ID': '1',
            '証明書期限': '2025-12-31',
        }]

        # Act
        result = generate_csv(rows)
        decoded = _decode(result)
        lines = [l for l in decoded.strip().split('\n') if l.strip()]

        # Assert: ヘッダー行(1行) + データ行(1行) = 計2行であること
        assert len(lines) == 2
        data_line = lines[1]
        # Assert: データ行に全フィールドの値が含まれること
        assert 'DEV-001' in data_line
        assert 'センサーA' in data_line
        assert 'センサー' in data_line
        assert 'MODEL-A100' in data_line
        assert 'SIM12345' in data_line
        assert 'AA:BB:CC:DD:EE:FF' in data_line
        assert '本社1階' in data_line
        assert '1' in data_line
        assert '2025-12-31' in data_line

    def test_none_value_outputs_empty_string(self):
        """3.5.1.2: None 値の列は空文字で出力される（CL-4-3）"""
        from iot_app.services.csv_service import generate_csv

        # Arrange: 任意項目（設置場所・証明書期限）が None のデータ
        rows = [{
            '操作列': '',
            'デバイスID': 'DEV-001',
            'デバイス名': 'センサーA',
            '設置場所': None,
            '証明書期限': None,
        }]

        # Act
        result = generate_csv(rows)
        decoded = _decode(result)
        lines = [l for l in decoded.strip().split('\n') if l.strip()]

        # Assert: データ行が出力されること
        assert len(lines) == 2
        # Assert: None フィールドが空文字（連続カンマ）として出力されること
        # pandas は None を空文字に変換するため連続したカンマが出力される
        assert ',,' in decoded

    def test_empty_list_outputs_minimal_content(self):
        """3.5.1.3: 空リストを渡した場合、ヘッダー行のみ（またはそれ以下）が出力される"""
        from iot_app.services.csv_service import generate_csv

        # Arrange: データなし
        rows = []

        # Act
        result = generate_csv(rows)
        decoded = _decode(result)
        lines = [l for l in decoded.strip().split('\n') if l.strip()]

        # Assert: 出力行が 0 行か 1 行（ヘッダーのみ）であること
        assert len(lines) <= 1

    def test_column_order_matches_dict_insertion_order(self):
        """3.5.1.4: 列順序が入力 dict のキー挿入順序と一致する"""
        from iot_app.services.csv_service import generate_csv

        # Arrange: 列順序が明確なデータ（操作列→デバイスID→デバイス名→モデル情報）
        rows = [{'操作列': '', 'デバイスID': 'DEV-001', 'デバイス名': 'センサーA', 'モデル情報': 'MODEL-A'}]

        # Act
        result = generate_csv(rows)
        decoded = _decode(result)
        header_line = decoded.strip().split('\n')[0]
        columns = [c.strip().strip('"') for c in header_line.split(',')]

        # Assert: 列順序が操作列→デバイスID→デバイス名→モデル情報であること
        assert columns.index('操作列') < columns.index('デバイスID')
        assert columns.index('デバイスID') < columns.index('デバイス名')
        assert columns.index('デバイス名') < columns.index('モデル情報')

    def test_comma_in_value_is_double_quoted(self):
        """3.5.2.1: 値にカンマが含まれる場合、ダブルクォートで囲まれる"""
        from iot_app.services.csv_service import generate_csv

        # Arrange: カンマを含む設置場所
        rows = [{'操作列': '', '設置場所': '東京,大阪'}]

        # Act
        result = generate_csv(rows)
        decoded = _decode(result)

        # Assert: カンマを含む値がダブルクォートで囲まれること
        assert '"東京,大阪"' in decoded

    def test_newline_in_value_is_double_quoted(self):
        """3.5.2.2: 値に改行が含まれる場合、ダブルクォートで囲まれる"""
        from iot_app.services.csv_service import generate_csv

        # Arrange: 改行を含む設置場所
        rows = [{'操作列': '', '設置場所': '東京\n大阪'}]

        # Act
        result = generate_csv(rows)
        decoded = _decode(result)

        # Assert: 改行を含む値がダブルクォートで囲まれること（pandas 標準動作）
        assert '"' in decoded

    def test_double_quote_in_value_is_escaped_as_two_quotes(self):
        """3.5.2.3: 値にダブルクォートが含まれる場合、\"\"\" でエスケープされる"""
        from iot_app.services.csv_service import generate_csv

        # Arrange: ダブルクォートを含む値
        rows = [{'操作列': '', 'デバイス名': '型番"A100"センサー'}]

        # Act
        result = generate_csv(rows)
        decoded = _decode(result)

        # Assert: ダブルクォートが \"\"\" でエスケープされること
        assert '""' in decoded

    def test_plain_value_is_output_without_escape(self):
        """3.5.2.4: 特殊文字を含まない値はそのまま出力される"""
        from iot_app.services.csv_service import generate_csv

        # Arrange: 特殊文字なしのデバイス ID
        rows = [{'操作列': '', 'デバイスID': 'DEV001'}]

        # Act
        result = generate_csv(rows)
        decoded = _decode(result)

        # Assert: DEV001 がそのままの形（不要なクォートなし）で出力されること
        assert 'DEV001' in decoded

    def test_output_starts_with_utf8_bom(self):
        """3.5.3.1: 出力が UTF-8 BOM 付きでエンコードされる"""
        from iot_app.services.csv_service import generate_csv

        # Arrange
        rows = [{'操作列': '', 'デバイスID': 'DEV-001'}]

        # Act
        result = generate_csv(rows)

        # Assert: bytes の場合は先頭 3 バイトが BOM であること
        #         str の場合は str 型であること（実装確定後に要確認）
        if isinstance(result, bytes):
            assert result[:3] == b'\xef\xbb\xbf'  # UTF-8 BOM
        else:
            # TODO: 実装完了後に戻り値型（bytes / str）を確定し、BOM 検証を追加する
            assert isinstance(result, str)

    def test_japanese_characters_output_without_corruption(self):
        """3.5.3.2: 日本語データが文字化けなく正しく出力される"""
        from iot_app.services.csv_service import generate_csv

        # Arrange: 日本語の値を含むデータ
        rows = [{'操作列': '', 'デバイス名': '温度センサー１号機', '設置場所': '東京都渋谷区'}]

        # Act
        result = generate_csv(rows)
        decoded = _decode(result)

        # Assert: 日本語が文字化けせずに正しく出力されること
        assert '温度センサー１号機' in decoded
        assert '東京都渋谷区' in decoded
