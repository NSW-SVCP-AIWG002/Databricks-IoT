import logging
from typing import Union

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

_logger = logging.getLogger(__name__)

def log_message(
    message: str,
    level: Union[int, str] = "INFO",
) -> None:
    """
    指定されたレベルでログを出力するユーティリティ。

    Parameters
    ----------
    message : str
        ログに出力したい文字列。
    level : int or str, default "INFO"
        出力レベル。``logging.INFO`` などの数値、または "INFO"/"ERROR"/"WARNING" などの文字列。
    """
    # 文字列が渡されたときは logging の定数に変換
    if isinstance(level, str):
        level_name = level.upper()
        level = getattr(logging, level_name, None)
        if level is None:
            raise ValueError(f"Unsupported log level: {level_name!r}")
    # print(level, message)

    _logger.log(level, message)