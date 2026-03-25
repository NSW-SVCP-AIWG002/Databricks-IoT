import logging
import re

from flask import g, has_request_context, request

_MASKING_RULES = {
    "email": lambda v: re.sub(r"(?<=^.{2})[^@]+(?=@)", "****", v) if isinstance(v, str) else v,
    "phone": lambda v: re.sub(r"(\d{3})-(\d{4})-(\d{4})", r"\1-****-\3", v) if isinstance(v, str) else v,
}


class AppLoggerAdapter(logging.LoggerAdapter):
    """リクエストコンテキストの自動付与・マスキングを行う共通ロガー"""

    def process(self, msg, kwargs):
        extra = {}

        if has_request_context():
            extra["requestId"] = getattr(g, "request_id", "-")
            extra["method"] = request.method
            extra["endpoint"] = request.path
            extra["ipAddress"] = request.headers.get("X-Forwarded-For", request.remote_addr)
            user_id = getattr(g, "current_user_id", None)
            if user_id is not None:
                extra["userId"] = user_id

        kw_extra = kwargs.pop("extra", {})
        caller_extra = {}
        for key, value in kw_extra.items():
            masked_value = _MASKING_RULES[key](value) if key in _MASKING_RULES else value
            extra[key] = masked_value
            caller_extra[key] = masked_value

        if extra:
            kwargs["extra"] = extra

        # 呼び出し元が渡した extra フィールド（マスキング適用済み）をメッセージに付与する
        # これにより caplog.text 等のフォーマット済みログに値が現れる
        if caller_extra:
            extra_str = " ".join(f"{k}={v}" for k, v in caller_extra.items())
            msg = f"{msg} | {extra_str}"

        return msg, kwargs


def get_logger(name: str) -> AppLoggerAdapter:
    """モジュール共通ロガーを取得する"""
    return AppLoggerAdapter(logging.getLogger(name), {})
