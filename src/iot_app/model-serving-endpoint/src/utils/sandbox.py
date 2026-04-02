import re
import signal
from typing import Tuple


# L1: 禁止パターン一覧（コード静的解析用）
FORBIDDEN_PATTERNS = [
    r'\bimport\b',
    r'__import__',
    r'\bopen\s*\(',
    r'\beval\s*\(',
    r'\bexec\s*\(',
    r'\bcompile\s*\(',
    r'\bgetattr\s*\(',
    r'\bsetattr\s*\(',
    r'\bdelattr\s*\(',
    r'__builtins__',
    r'__globals__',
    r'__dict__',
    r'\bsubprocess\b',
    r'os\.system',
    r'os\.popen',
    r'\bsocket\b',
    r'\bpathlib\b',
]


def validate_generated_code(code: str) -> Tuple[bool, str]:
    """LLM生成コードの安全性を検証する（L1: コード静的解析）。

    Returns:
        (is_safe, violation_detail): 安全な場合は(True, "")、
        危険な場合は(False, 検出されたパターンの説明)
    """
    for pattern in FORBIDDEN_PATTERNS:
        match = re.search(pattern, code)
        if match:
            return False, f"禁止パターン検出: {match.group()}"
    return True, ""


class CodeExecutionTimeoutError(Exception):
    """コード実行タイムアウト例外（L3用）"""
    pass


def _timeout_handler(signum, frame):
    raise CodeExecutionTimeoutError("コード実行がタイムアウトしました（30秒）")


def execute_with_timeout(code: str, namespace: dict, timeout_sec: int = 30) -> None:
    """タイムアウト付きでコードを実行する（L3: 実行タイムアウト）。

    Args:
        code: 実行するPythonコード文字列
        namespace: exec()に渡す名前空間（L2: 制限付き実行名前空間を渡すこと）
        timeout_sec: タイムアウト秒数（デフォルト30秒）

    Raises:
        CodeExecutionTimeoutError: 実行がタイムアウトした場合
        Exception: コード実行中に発生した例外

    Note:
        signal.SIGALRM はLinux専用のため、Databricks Model Serving Endpoint
        （Linuxコンテナ）での実行を前提とする。
    """
    original_handler = signal.signal(signal.SIGALRM, _timeout_handler)
    signal.alarm(timeout_sec)
    try:
        exec(code, namespace)
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, original_handler)
