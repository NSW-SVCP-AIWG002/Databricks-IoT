"""tests/unit/test_conversational-ai-chat.py

対話型AIチャット機能（CHT-001）単体テスト

テスト対象:
    - validate_generated_code()  src/utils/sandbox.py        / L1 コード静的解析
    - execute_with_timeout()     src/utils/sandbox.py        / L3 実行タイムアウト
    - clean_code() [graph]       src/apis/request_graph_api.py / 全角→半角変換
    - clean_code() [llm]         src/apis/request_llm_api.py   / Markdown ブロック抽出
    - trim_messages()            src/utils/common.py           / 往復数・サイズ制限
    - sanitize_question()        リファレンス実装              / HTML エスケープ・制御文字除去

    ※ ソースは docs/03-features/flask-app/conversational-ai-chat/ai_chat_graph_gen_src/ 配下

設計書:
    - docs/03-features/flask-app/conversational-ai-chat/ui-specification.md
    - docs/03-features/flask-app/conversational-ai-chat/workflow-specification.md

テスト観点:
    - docs/05-testing/unit-test/unit-test-perspectives.md

注意 (trim_messages):
    common.py の実装値（max_turns=5, max_size_bytes=100KB）は
    workflow-specification.md 記載の設計値（15往復, 512KB）と乖離あり。
    # TODO: 実装値・設計書値の乖離を確認・修正すること

注意 (sanitize_question):
    Flask app (src/views/chat/) に sanitize_question() は未実装のため、
    設計書記載の仕様をもとにリファレンス実装を本ファイル内に定義してテストする。
    # TODO: Flask app 実装後は src.views.chat.utils 等から import に変更すること
"""
import importlib.util
import os
import re
import sys
from unittest.mock import MagicMock

import pytest

# ============================================================
# Mock クラス定義（importlib ロード前に定義が必要）
# ============================================================

class MockHumanMessage:
    """langchain_core.messages.HumanMessage のスタブ"""

    def __init__(self, content: str = "dummy"):
        self.content = content

    def __repr__(self):
        return f"MockHumanMessage(content={self.content!r})"


class MockAIMessage:
    """langchain_core AIMessage のスタブ"""

    def __init__(self, content: str = "dummy"):
        self.content = content

    def __repr__(self):
        return f"MockAIMessage(content={self.content!r})"


# ============================================================
# sys.modules への外部依存モック登録
# （importlib によるモジュールロード前に実行）
# ============================================================

# langchain_core.messages は HumanMessage を MockHumanMessage に差し替え
_mock_lc_messages = MagicMock()
_mock_lc_messages.HumanMessage = MockHumanMessage
_mock_lc_messages.BaseMessage = object

_mock_lc = MagicMock()
_mock_lc.messages = _mock_lc_messages

# setdefault: 既にインストール済みの実パッケージを上書きしない
sys.modules.setdefault("langchain_core", _mock_lc)
sys.modules["langchain_core.messages"] = _mock_lc_messages  # HumanMessage を確実に差し替え

_EXTERNAL_MOCKS = {
    "langgraph": MagicMock(),
    "langgraph.graph": MagicMock(),
    "numpy": MagicMock(),
    "pandas": MagicMock(),
    "plotly": MagicMock(),
    "plotly.express": MagicMock(),
    "plotly.graph_objects": MagicMock(),
    "plotly.io": MagicMock(),
    "requests": MagicMock(),
    "conf": MagicMock(),
    "conf.settings": MagicMock(),
    "conf.logging_config": MagicMock(),
    "conf.prompt": MagicMock(),
    "src": MagicMock(),
    "src.utils": MagicMock(),
    "src.utils.llm": MagicMock(),
    "src.utils.sandbox": MagicMock(),
    "src.utils.dataframe": MagicMock(),
}
for _mod_name, _mock in _EXTERNAL_MOCKS.items():
    sys.modules.setdefault(_mod_name, _mock)


# ============================================================
# ai_chat_graph_gen_src モジュールロード
# ============================================================

_AI_CHAT_BASE = os.path.abspath(os.path.join(
    os.path.dirname(__file__),
    "../../docs/03-features/flask-app/conversational-ai-chat/ai_chat_graph_gen_src",
))


def _load_module(module_name: str, relative_path: str):
    """ai_chat_graph_gen_src 配下のファイルを直接ロードする"""
    path = os.path.join(_AI_CHAT_BASE, relative_path)
    spec = importlib.util.spec_from_file_location(module_name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# sandbox.py は stdlib のみ使用のため追加モック不要
_sandbox = _load_module("ai_chat_sandbox", "src/utils/sandbox.py")
validate_generated_code = _sandbox.validate_generated_code
execute_with_timeout = _sandbox.execute_with_timeout
CodeExecutionTimeoutError = _sandbox.CodeExecutionTimeoutError

_graph_api = _load_module("ai_chat_graph_api", "src/apis/request_graph_api.py")
graph_clean_code = _graph_api.clean_code  # 全角→半角変換

_llm_api = _load_module("ai_chat_llm_api", "src/apis/request_llm_api.py")
llm_clean_code = _llm_api.clean_code  # Markdown コードブロック抽出

_common = _load_module("ai_chat_common", "src/utils/common.py")
trim_messages = _common.trim_messages


# ============================================================
# sanitize_question リファレンス実装
# （workflow-specification.md § 入力サニタイズ に基づく）
# ============================================================

try:
    from markupsafe import escape as _markup_escape
except ImportError:
    # markupsafe 未インストール環境向けフォールバック
    # TODO: Flask 本番環境では markupsafe が利用可能なため、このフォールバックは不要
    import html as _html

    def _markup_escape(s):
        return _html.escape(str(s), quote=True)


def sanitize_question(question: str) -> str:
    """質問テキストをサニタイズ（workflow-specification.md § 入力サニタイズ 参照）

    処理内容:
        1. HTML エスケープ（markupsafe.escape）
        2. 制御文字除去（\\x00-\\x1f, \\x7f-\\x9f）
        3. 前後の空白を strip()
    """
    question = str(_markup_escape(question))
    question = re.sub(r"[\x00-\x1f\x7f-\x9f]", "", question)
    return question.strip()


# ============================================================
# ヘルパー
# ============================================================

def _make_turn(q: str = "question", a: str = "answer"):
    """trim_messages テスト用: 1往復分（HumanMessage + AIMessage）を返す"""
    return [MockHumanMessage(q), MockAIMessage(a)]


# ============================================================
# 1. validate_generated_code — L1 コード静的解析
# ============================================================

@pytest.mark.unit
class TestValidateGeneratedCode:
    """validate_generated_code() のテスト

    観点: 2.1 正常系処理, 1.3 エラーハンドリング
    セキュリティ: L1 コード静的解析（禁止パターン検出）
    """

    # --- 正常系 ---

    def test_safe_code_returns_true(self):
        """2.1.1: 安全なコードは (True, "") を返す"""
        # Arrange
        code = "fig = px.bar(df, x='date', y='value')"
        # Act
        is_safe, detail = validate_generated_code(code)
        # Assert
        assert is_safe is True
        assert detail == ""

    def test_empty_string_returns_true(self):
        """2.1.1: 空文字列は禁止パターンなしとして (True, "") を返す"""
        # Arrange
        code = ""
        # Act
        is_safe, detail = validate_generated_code(code)
        # Assert
        assert is_safe is True
        assert detail == ""

    def test_multiline_safe_code_returns_true(self):
        """2.1.1: 複数行の安全なコードは (True, "") を返す"""
        # Arrange
        code = (
            "fig = px.line(df, x='date', y='value')\n"
            "fig.update_layout(title='Temperature')\n"
        )
        # Act
        is_safe, detail = validate_generated_code(code)
        # Assert
        assert is_safe is True
        assert detail == ""

    def test_plotly_realistic_code_is_safe(self):
        """2.1.1: 実際の Plotly コード例が安全と判定される"""
        # Arrange
        code = (
            "fig = px.scatter(df, x='x_col', y='y_col', title='Scatter')\n"
            "fig.update_layout(xaxis_title='X', yaxis_title='Y')\n"
        )
        # Act
        is_safe, detail = validate_generated_code(code)
        # Assert
        assert is_safe is True

    # --- 禁止パターン検出 ---

    def test_import_statement_detected(self):
        """2.1: import 文を検出して (False, ...) を返す"""
        # Arrange
        code = "import os"
        # Act
        is_safe, detail = validate_generated_code(code)
        # Assert
        assert is_safe is False
        assert "禁止パターン検出" in detail

    def test_dunder_import_detected(self):
        """2.1: __import__() を検出して (False, ...) を返す"""
        # Arrange
        code = "__import__('os')"
        # Act
        is_safe, detail = validate_generated_code(code)
        # Assert
        assert is_safe is False
        assert "禁止パターン検出" in detail

    def test_open_function_detected(self):
        """2.1: open() を検出して (False, ...) を返す"""
        # Arrange
        code = "f = open('file.txt')"
        # Act
        is_safe, detail = validate_generated_code(code)
        # Assert
        assert is_safe is False

    def test_eval_function_detected(self):
        """2.1: eval() を検出して (False, ...) を返す"""
        # Arrange
        code = "result = eval('1+1')"
        # Act
        is_safe, detail = validate_generated_code(code)
        # Assert
        assert is_safe is False

    def test_exec_function_detected(self):
        """2.1: exec() を検出して (False, ...) を返す"""
        # Arrange
        code = "exec('print(1)')"
        # Act
        is_safe, detail = validate_generated_code(code)
        # Assert
        assert is_safe is False

    def test_compile_function_detected(self):
        """2.1: compile() を検出して (False, ...) を返す"""
        # Arrange
        code = "compile('x=1', '', 'exec')"
        # Act
        is_safe, detail = validate_generated_code(code)
        # Assert
        assert is_safe is False

    def test_getattr_function_detected(self):
        """2.1: getattr() を検出して (False, ...) を返す"""
        # Arrange
        code = "getattr(obj, '__class__')"
        # Act
        is_safe, detail = validate_generated_code(code)
        # Assert
        assert is_safe is False

    def test_setattr_function_detected(self):
        """2.1: setattr() を検出して (False, ...) を返す"""
        # Arrange
        code = "setattr(obj, 'x', 1)"
        # Act
        is_safe, detail = validate_generated_code(code)
        # Assert
        assert is_safe is False

    def test_delattr_function_detected(self):
        """2.1: delattr() を検出して (False, ...) を返す"""
        # Arrange
        code = "delattr(obj, 'x')"
        # Act
        is_safe, detail = validate_generated_code(code)
        # Assert
        assert is_safe is False

    def test_dunder_builtins_detected(self):
        """2.1: __builtins__ を検出して (False, ...) を返す"""
        # Arrange
        code = "__builtins__['open']"
        # Act
        is_safe, detail = validate_generated_code(code)
        # Assert
        assert is_safe is False

    def test_dunder_globals_detected(self):
        """2.1: __globals__ を検出して (False, ...) を返す"""
        # Arrange
        code = "func.__globals__['os']"
        # Act
        is_safe, detail = validate_generated_code(code)
        # Assert
        assert is_safe is False

    def test_dunder_dict_detected(self):
        """2.1: __dict__ を検出して (False, ...) を返す"""
        # Arrange
        code = "obj.__dict__"
        # Act
        is_safe, detail = validate_generated_code(code)
        # Assert
        assert is_safe is False

    def test_subprocess_detected(self):
        """2.1: subprocess を検出して (False, ...) を返す"""
        # Arrange
        code = "subprocess.run(['ls'])"
        # Act
        is_safe, detail = validate_generated_code(code)
        # Assert
        assert is_safe is False

    def test_os_system_detected(self):
        """2.1: os.system を検出して (False, ...) を返す"""
        # Arrange
        code = "os.system('whoami')"
        # Act
        is_safe, detail = validate_generated_code(code)
        # Assert
        assert is_safe is False

    def test_os_popen_detected(self):
        """2.1: os.popen を検出して (False, ...) を返す"""
        # Arrange
        code = "os.popen('ls')"
        # Act
        is_safe, detail = validate_generated_code(code)
        # Assert
        assert is_safe is False

    def test_socket_detected(self):
        """2.1: socket を検出して (False, ...) を返す"""
        # Arrange
        code = "socket.connect(('example.com', 80))"
        # Act
        is_safe, detail = validate_generated_code(code)
        # Assert
        assert is_safe is False

    def test_pathlib_detected(self):
        """2.1: pathlib を検出して (False, ...) を返す"""
        # Arrange
        code = "pathlib.Path('/etc/passwd').read_text()"
        # Act
        is_safe, detail = validate_generated_code(code)
        # Assert
        assert is_safe is False

    # --- 違反詳細 ---

    def test_violation_detail_contains_detected_keyword(self):
        """1.3: 違反時は検出パターンを含む説明文字列が返る"""
        # Arrange
        code = "import os"
        # Act
        is_safe, detail = validate_generated_code(code)
        # Assert
        assert is_safe is False
        assert "import" in detail

    def test_first_forbidden_pattern_stops_check(self):
        """2.1: 複数の禁止パターンが存在する場合、最初の検出で返却される"""
        # Arrange
        code = "import os; eval('1')"
        # Act
        is_safe, detail = validate_generated_code(code)
        # Assert
        assert is_safe is False
        assert "import" in detail


# ============================================================
# 2. execute_with_timeout — L3 実行タイムアウト
# ============================================================

@pytest.mark.unit
class TestExecuteWithTimeout:
    """execute_with_timeout() のテスト

    観点: 2.1 正常系処理, 1.3 エラーハンドリング, 2.3 副作用チェック
    セキュリティ: L3 実行タイムアウト（SIGALRM、Linux 専用）
    """

    def test_normal_execution_succeeds(self):
        """2.1.1: 通常のコードが正常実行される"""
        # Arrange
        namespace = {"__builtins__": {}, "result": None}
        code = "result = 1 + 2"
        # Act
        execute_with_timeout(code, namespace)
        # Assert
        assert namespace["result"] == 3

    def test_namespace_mutation_preserved(self):
        """2.1.1: 実行結果が名前空間に反映される"""
        # Arrange
        import pandas as pd  # noqa: PLC0415 (実パッケージを直接使用)
        df = pd.DataFrame({"x": [1, 2, 3]})
        namespace = {"df": df, "pd": pd, "__builtins__": {}, "output": None}
        code = "output = df['x'].sum()"
        # Act
        execute_with_timeout(code, namespace)
        # Assert
        assert namespace["output"] == 6

    def test_exception_propagates(self):
        """1.3.1: コード実行中の例外が上位に伝播する"""
        # Arrange
        namespace = {"__builtins__": {}}
        code = "raise ValueError('test error')"
        # Act & Assert
        with pytest.raises(ValueError, match="test error"):
            execute_with_timeout(code, namespace)

    def test_syntax_error_propagates(self):
        """1.3.1: 構文エラーが上位に伝播する"""
        # Arrange
        namespace = {"__builtins__": {}}
        code = "def broken(:"
        # Act & Assert
        with pytest.raises(SyntaxError):
            execute_with_timeout(code, namespace)

    def test_timeout_raises_code_execution_timeout_error(self):
        """1.3: タイムアウト時に CodeExecutionTimeoutError が発生する"""
        # Arrange
        namespace = {"__builtins__": {}}
        code = "while True: pass"
        # Act & Assert
        with pytest.raises(CodeExecutionTimeoutError):
            execute_with_timeout(code, namespace, timeout_sec=1)

    def test_alarm_is_cleared_after_normal_execution(self):
        """2.3.1: 正常実行後にアラームがクリアされる（後続の SIGALRM に影響しない）"""
        import signal
        # Arrange
        namespace = {"__builtins__": {}, "result": None}
        code = "result = 42"
        # Act
        execute_with_timeout(code, namespace, timeout_sec=5)
        # Assert: signal.alarm(0) で残り秒数が 0 であることを確認
        remaining = signal.alarm(0)
        assert remaining == 0

    def test_custom_timeout_sec_parameter(self):
        """2.1.1: timeout_sec パラメータが正常に受け付けられる"""
        # Arrange
        namespace = {"__builtins__": {}, "result": None}
        code = "result = 'done'"
        # Act
        execute_with_timeout(code, namespace, timeout_sec=5)
        # Assert
        assert namespace["result"] == "done"


# ============================================================
# 3. request_graph_api.clean_code — 全角→半角変換
# ============================================================

@pytest.mark.unit
class TestGraphApiCleanCode:
    """request_graph_api.clean_code() のテスト（全角記号・全角スペースを半角に変換）

    観点: 2.1 正常系処理
    """

    def test_japanese_comma_converted(self):
        """2.1.1: 読点（、）がカンマ（,）に変換される"""
        # Arrange
        code = "x = 1、y = 2"
        # Act
        result = graph_clean_code(code)
        # Assert
        assert "、" not in result
        assert "," in result

    def test_japanese_period_converted(self):
        """2.1.1: 句点（。）がピリオド（.）に変換される"""
        # Arrange
        code = "x = 1。y = 2"
        # Act
        result = graph_clean_code(code)
        # Assert
        assert "。" not in result
        assert "." in result

    def test_fullwidth_colon_converted(self):
        """2.1.1: 全角コロン（：）が半角コロン（:）に変換される"""
        # Arrange
        code = "dict = {'key'：'value'}"
        # Act
        result = graph_clean_code(code)
        # Assert
        assert "：" not in result
        assert ":" in result

    def test_fullwidth_open_paren_converted(self):
        """2.1.1: 全角開き括弧（（）が半角（(）に変換される"""
        # Arrange
        code = "func（arg）"
        # Act
        result = graph_clean_code(code)
        # Assert
        assert "（" not in result
        assert "(" in result

    def test_fullwidth_close_paren_converted(self):
        """2.1.1: 全角閉じ括弧（）が半角）に変換される"""
        # Arrange
        code = "func（arg）"
        # Act
        result = graph_clean_code(code)
        # Assert
        assert "）" not in result
        assert ")" in result

    def test_fullwidth_space_converted(self):
        """2.1.1: 全角スペース（U+3000）が半角スペースに変換される"""
        # Arrange
        code = "x\u3000=\u30001"
        # Act
        result = graph_clean_code(code)
        # Assert
        assert "\u3000" not in result
        assert " " in result

    def test_all_fullwidth_chars_converted_simultaneously(self):
        """2.1.1: 複数の全角文字が同時に変換される"""
        # Arrange
        code = "func（x、y）：\u3000result"
        # Act
        result = graph_clean_code(code)
        # Assert
        assert "（" not in result
        assert "）" not in result
        assert "、" not in result
        assert "：" not in result
        assert "\u3000" not in result

    def test_halfwidth_code_unchanged(self):
        """2.1.1: 全角文字を含まないコードはそのまま返る"""
        # Arrange
        code = "fig = px.bar(df, x='date', y='value')"
        # Act
        result = graph_clean_code(code)
        # Assert
        assert result == code

    def test_empty_string_returns_empty(self):
        """1.1.1: 空文字列は空文字列のまま返る"""
        # Arrange
        code = ""
        # Act
        result = graph_clean_code(code)
        # Assert
        assert result == ""

    def test_no_strip_applied(self):
        """2.1: strip() は行わない（前後の空白が保持される）"""
        # Arrange
        code = "  fig = px.bar(df)  "
        # Act
        result = graph_clean_code(code)
        # Assert
        assert result.startswith("  ")
        assert result.endswith("  ")


# ============================================================
# 4. request_llm_api.clean_code — Markdown コードブロック抽出
# ============================================================

@pytest.mark.unit
class TestLlmApiCleanCode:
    """request_llm_api.clean_code() のテスト（Markdown コードブロック抽出 + strip）

    観点: 2.1 正常系処理
    """

    def test_python_code_block_extracted(self):
        """2.1.1: ```python ... ``` ブロックからコードが抽出される"""
        # Arrange
        code = "```python\nprint('hello')\n```"
        # Act
        result = llm_clean_code(code)
        # Assert
        assert result == "print('hello')"

    def test_plain_code_block_extracted(self):
        """2.1.1: ``` ... ``` ブロック（言語指定なし）からコードが抽出される"""
        # Arrange
        code = "```\nx = 1 + 2\n```"
        # Act
        result = llm_clean_code(code)
        # Assert
        assert result == "x = 1 + 2"

    def test_no_code_block_returns_stripped(self):
        """2.1.1: コードブロックがない場合は strip() した文字列を返す"""
        # Arrange
        code = "  result = df['x'].sum()  "
        # Act
        result = llm_clean_code(code)
        # Assert
        assert result == "result = df['x'].sum()"

    def test_multiline_code_block_extracted(self):
        """2.1.1: 複数行のコードブロックが正しく抽出される"""
        # Arrange
        code = (
            "```python\n"
            "df_filtered = df[df['x'] > 0]\n"
            "print(df_filtered.sum())\n"
            "```"
        )
        # Act
        result = llm_clean_code(code)
        # Assert
        assert "df_filtered" in result
        assert "print" in result
        assert "```" not in result

    def test_surrounding_text_removed(self):
        """2.1.1: コードブロック前後の説明文が除去される"""
        # Arrange
        code = "以下のコードを実行してください。\n```python\nx = 1\n```\n以上です。"
        # Act
        result = llm_clean_code(code)
        # Assert
        assert "以下" not in result
        assert "以上" not in result
        assert result.strip() == "x = 1"

    def test_empty_code_block_returns_empty(self):
        """1.1.1: 空のコードブロックは空文字列を返す"""
        # Arrange
        code = "```python\n```"
        # Act
        result = llm_clean_code(code)
        # Assert
        assert result == ""

    def test_empty_string_returns_empty(self):
        """1.1.1: 空文字列は空文字列を返す"""
        # Arrange
        code = ""
        # Act
        result = llm_clean_code(code)
        # Assert
        assert result == ""

    def test_strip_applied_to_extracted_code(self):
        """2.1.1: コードブロック抽出後に strip() が適用される"""
        # Arrange
        code = "```python\n\n  x = 1  \n\n```"
        # Act
        result = llm_clean_code(code)
        # Assert
        assert not result.startswith("\n")
        assert not result.endswith("\n")


# ============================================================
# 5. trim_messages — 空入力
# ============================================================

@pytest.mark.unit
class TestTrimMessagesEmptyInput:
    """trim_messages() — 空入力のテスト

    観点: 1.1.1 必須チェック
    """

    def test_empty_list_returns_empty(self):
        """1.1.1: 空リストを渡すと空リストが返る"""
        # Arrange
        messages = []
        # Act
        result = trim_messages(messages)
        # Assert
        assert result == []

    def test_single_human_message_within_limit_not_trimmed(self):
        """2.1.1: 1件の HumanMessage は制限以内のためそのまま返る"""
        # Arrange
        messages = [MockHumanMessage("質問")]
        # Act
        result = trim_messages(messages, max_turns=5, max_size_bytes=100 * 1024)
        # Assert
        assert len(result) == 1


# ============================================================
# 6. trim_messages — 往復数制限
# ============================================================

@pytest.mark.unit
class TestTrimMessagesByTurns:
    """trim_messages() — 往復数制限のテスト

    観点: 2.1 正常系処理
    """

    def test_within_max_turns_not_trimmed(self):
        """2.1.1: max_turns 以内の往復数は削除されない"""
        # Arrange
        messages = _make_turn("q1") + _make_turn("q2")  # 2往復
        # Act
        result = trim_messages(messages, max_turns=5, max_size_bytes=10 * 1024 * 1024)
        # Assert
        assert len(result) == 4

    def test_exactly_max_turns_not_trimmed(self):
        """2.1.2: max_turns ちょうどの往復数は削除されない"""
        # Arrange
        messages = sum([_make_turn(f"q{i}") for i in range(5)], [])  # 5往復
        # Act
        result = trim_messages(messages, max_turns=5, max_size_bytes=10 * 1024 * 1024)
        # Assert
        assert len(result) == 10

    def test_exceeds_max_turns_oldest_removed(self):
        """2.1: max_turns を超えると古いメッセージが削除される"""
        # Arrange
        messages = sum([_make_turn(f"q{i}") for i in range(6)], [])  # 6往復
        # Act
        result = trim_messages(messages, max_turns=5, max_size_bytes=10 * 1024 * 1024)
        # Assert
        human_count = sum(1 for m in result if isinstance(m, MockHumanMessage))
        assert human_count == 5

    def test_max_turns_1_keeps_only_last_turn(self):
        """2.1: max_turns=1 のとき最後の1往復のみ残る"""
        # Arrange
        messages = sum([_make_turn(f"q{i}") for i in range(3)], [])  # 3往復
        # Act
        result = trim_messages(messages, max_turns=1, max_size_bytes=10 * 1024 * 1024)
        # Assert
        human_count = sum(1 for m in result if isinstance(m, MockHumanMessage))
        assert human_count == 1
        assert result[-2].content == "q2"  # 最後の HumanMessage が残る

    def test_ai_message_only_not_counted_as_turn(self):
        """2.1: AIMessage のみのリストは HumanMessage=0 往復とみなし削除なし"""
        # Arrange
        messages = [MockAIMessage("a1"), MockAIMessage("a2")]
        # Act
        result = trim_messages(messages, max_turns=1, max_size_bytes=10 * 1024 * 1024)
        # Assert
        assert len(result) == 2

    def test_cut_keeps_latest_messages(self):
        """2.1: 削除後のメッセージリストが最新のものであることを確認"""
        # Arrange
        messages = (
            _make_turn("oldest") +
            _make_turn("middle") +
            _make_turn("newest")
        )  # 3往復
        # Act
        result = trim_messages(messages, max_turns=2, max_size_bytes=10 * 1024 * 1024)
        # Assert: 最新2往復が残る
        contents = [m.content for m in result]
        assert "oldest" not in contents
        assert "middle" in contents
        assert "newest" in contents


# ============================================================
# 7. trim_messages — サイズ制限
# ============================================================

@pytest.mark.unit
class TestTrimMessagesBySize:
    """trim_messages() — サイズ制限のテスト

    観点: 2.1 正常系処理
    """

    def test_within_max_size_not_trimmed(self):
        """2.1.1: max_size_bytes 以内のリストは削除されない"""
        # Arrange
        messages = [MockHumanMessage("短い質問"), MockAIMessage("短い回答")]
        # Act
        result = trim_messages(messages, max_turns=100, max_size_bytes=1024 * 1024)
        # Assert
        assert len(result) == 2

    def test_exceeds_max_size_oldest_removed(self):
        """2.1: max_size_bytes を超えると古いメッセージが削除される"""
        # Arrange: 各 1000 バイトのメッセージ 5件
        large_content = "x" * 1000
        messages = [MockAIMessage(large_content) for _ in range(5)]
        # Act
        result = trim_messages(messages, max_turns=100, max_size_bytes=2000)
        # Assert
        total_size = sum(len(str(m.content).encode("utf-8")) for m in result)
        assert total_size <= 2000

    def test_single_large_message_exceeds_size_returns_empty(self):
        """2.1: 単一の超大容量メッセージはサイズ超過で空リストになる

        実装詳細: size_cut_index = i + 1 = 1 → messages[1:] = [] となる。
        # TODO: 単一メッセージがサイズ超過時の挙動について設計書に記載なし、要確認
        """
        # Arrange: 200KB > max_size_bytes(100KB)
        messages = [MockAIMessage("x" * 200 * 1024)]
        # Act
        result = trim_messages(messages, max_turns=100, max_size_bytes=100 * 1024)
        # Assert
        assert result == []

    def test_size_check_uses_utf8_encoding(self):
        """2.1: サイズ計算は UTF-8 バイト数で行われる"""
        # Arrange: 日本語1文字 = 3バイト（UTF-8）、100文字 = 300バイト
        japanese = "あ" * 100  # 300 bytes
        messages = [MockAIMessage(japanese)]
        # Act
        result = trim_messages(messages, max_turns=100, max_size_bytes=400)
        # Assert: 300 bytes < 400 bytes のため削除なし
        assert len(result) == 1

    def test_max_size_bytes_zero_returns_empty(self):
        """2.1: max_size_bytes=0 のとき全メッセージが削除される"""
        # Arrange
        messages = [MockHumanMessage("質問"), MockAIMessage("回答")]
        # Act
        result = trim_messages(messages, max_turns=100, max_size_bytes=0)
        # Assert
        assert result == []


# ============================================================
# 8. trim_messages — 往復数・サイズ両方の制限
# ============================================================

@pytest.mark.unit
class TestTrimMessagesCombined:
    """trim_messages() — 往復数制限・サイズ制限の組み合わせテスト

    観点: 2.1 正常系処理
    """

    def test_turns_applied_before_size(self):
        """2.1.1: 往復数制限 → サイズ制限の順で適用される"""
        # Arrange: 3往復、各メッセージ 500バイト（1往復 = 1000バイト）
        content = "x" * 500
        messages = sum(
            [[MockHumanMessage(content), MockAIMessage(content)] for _ in range(3)],
            [],
        )
        # Act: max_turns=2（削減後 4件 = 2000bytes）、max_size_bytes=1500（さらに削減）
        result = trim_messages(messages, max_turns=2, max_size_bytes=1500)
        # Assert: サイズ制限まで適用された結果のサイズが 1500 以下
        total_size = sum(len(str(m.content).encode("utf-8")) for m in result)
        assert total_size <= 1500


# ============================================================
# 9. sanitize_question — 空入力
# ============================================================

@pytest.mark.unit
class TestSanitizeQuestionEmptyInput:
    """sanitize_question() — 空入力のテスト

    観点: 1.1.1 必須チェック
    """

    def test_empty_string_returns_empty(self):
        """1.1.1: 空文字列を渡すと空文字列が返る"""
        # Arrange
        question = ""
        # Act
        result = sanitize_question(question)
        # Assert
        assert result == ""

    def test_whitespace_only_returns_empty(self):
        """1.1.1: 空白のみの文字列は strip() により空文字列になる"""
        # Arrange
        question = "   "
        # Act
        result = sanitize_question(question)
        # Assert
        assert result == ""

    def test_newline_only_returns_empty(self):
        """1.1.1: 改行のみの文字列は制御文字除去 + strip() により空文字列になる"""
        # Arrange
        question = "\n\r"
        # Act
        result = sanitize_question(question)
        # Assert
        assert result == ""


# ============================================================
# 10. sanitize_question — 長さ関連
# ============================================================

@pytest.mark.unit
class TestSanitizeQuestionLength:
    """sanitize_question() — 長さ関連のテスト

    観点: 1.1.2 最大文字列長チェック
    注: sanitize_question() 自体は最大文字数チェックを行わない
        （Flask view / バリデーション層で実施）
    """

    def test_normal_question_processed_correctly(self):
        """2.1.1: 通常の質問テキストは HTML エスケープされて返る"""
        # Arrange
        question = "昨日の第1冷凍庫の平均温度は？"
        # Act
        result = sanitize_question(question)
        # Assert
        assert "冷凍庫" in result
        assert "温度" in result

    def test_1000_char_input_processed(self):
        """1.2.2: UI 仕様の最大値（1000文字）の入力が処理される"""
        # Arrange
        question = "あ" * 1000
        # Act
        result = sanitize_question(question)
        # Assert
        assert len(result) > 0

    def test_strip_applied_to_leading_trailing_whitespace(self):
        """2.1.1: 前後の空白が除去される"""
        # Arrange
        question = "  質問テキスト  "
        # Act
        result = sanitize_question(question)
        # Assert
        assert result == "質問テキスト"


# ============================================================
# 11. sanitize_question — HTML エスケープ（XSS 対策）
# ============================================================

@pytest.mark.unit
class TestSanitizeQuestionHtmlEscape:
    """sanitize_question() — HTML エスケープのテスト

    観点: セキュリティ（XSS 対策）
    """

    def test_less_than_escaped(self):
        """セキュリティ: < が &lt; にエスケープされる"""
        # Arrange
        question = "<script>alert(1)</script>"
        # Act
        result = sanitize_question(question)
        # Assert
        assert "<script>" not in result
        assert "&lt;" in result

    def test_greater_than_escaped(self):
        """セキュリティ: > が &gt; にエスケープされる"""
        # Arrange
        question = "x > 0"
        # Act
        result = sanitize_question(question)
        # Assert
        assert ">" not in result
        assert "&gt;" in result

    def test_ampersand_escaped(self):
        """セキュリティ: & が &amp; にエスケープされる"""
        # Arrange
        question = "A & B"
        # Act
        result = sanitize_question(question)
        # Assert
        assert "&amp;" in result

    def test_double_quote_escaped(self):
        """セキュリティ: " がエスケープされる（&#34; または &quot;）"""
        # Arrange
        question = 'He said "hello"'
        # Act
        result = sanitize_question(question)
        # Assert
        assert '"hello"' not in result

    def test_single_quote_behavior(self):
        """セキュリティ: ' の扱いは markupsafe 実装依存（最低限 str が返ること）

        # TODO: markupsafe は ' をエスケープしない仕様のため、要確認
        """
        # Arrange
        question = "It's a question"
        # Act
        result = sanitize_question(question)
        # Assert
        assert isinstance(result, str)

    def test_normal_text_not_escaped(self):
        """2.1.1: HTML タグを含まない通常テキストはそのまま返る"""
        # Arrange
        question = "冷凍庫の温度を教えてください"
        # Act
        result = sanitize_question(question)
        # Assert
        assert result == "冷凍庫の温度を教えてください"


# ============================================================
# 12. sanitize_question — 制御文字除去（インジェクション対策）
# ============================================================

@pytest.mark.unit
class TestSanitizeQuestionControlCharacters:
    """sanitize_question() — 制御文字除去のテスト

    観点: セキュリティ（インジェクション対策）
    """

    def test_null_byte_removed(self):
        """セキュリティ: NULL 文字（\\x00）が除去される"""
        # Arrange
        question = "質問\x00テキスト"
        # Act
        result = sanitize_question(question)
        # Assert
        assert "\x00" not in result
        assert "質問" in result

    def test_tab_removed(self):
        """セキュリティ: タブ文字（\\x09）が除去される"""
        # Arrange
        question = "質問\x09テキスト"
        # Act
        result = sanitize_question(question)
        # Assert
        assert "\x09" not in result

    def test_newline_removed(self):
        """セキュリティ: 改行文字（\\x0a）が除去される"""
        # Arrange
        question = "質問\nテキスト"
        # Act
        result = sanitize_question(question)
        # Assert
        assert "\n" not in result

    def test_carriage_return_removed(self):
        """セキュリティ: キャリッジリターン（\\x0d）が除去される"""
        # Arrange
        question = "質問\rテキスト"
        # Act
        result = sanitize_question(question)
        # Assert
        assert "\r" not in result

    def test_del_character_removed(self):
        """セキュリティ: DEL 文字（\\x7f）が除去される"""
        # Arrange
        question = "質問\x7fテキスト"
        # Act
        result = sanitize_question(question)
        # Assert
        assert "\x7f" not in result

    def test_c1_control_characters_removed(self):
        """セキュリティ: C1 制御文字（\\x80-\\x9f）が除去される"""
        # Arrange
        question = "質問\x80\x9fテキスト"
        # Act
        result = sanitize_question(question)
        # Assert
        assert "\x80" not in result
        assert "\x9f" not in result

    def test_normal_text_preserved_after_control_char_removal(self):
        """2.1.1: 制御文字除去後も通常テキストが保持される"""
        # Arrange
        question = "昨日\x00の\n温度\rは？"
        # Act
        result = sanitize_question(question)
        # Assert
        assert "昨日" in result
        assert "温度" in result
        assert "は" in result
