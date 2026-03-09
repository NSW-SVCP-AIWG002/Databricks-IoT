import os
from dataclasses import dataclass

from flask import g


@dataclass
class _MockUser:
    organization_id: int


def setup_middleware(app):
    """アプリケーションに before_request フックを登録する。"""

    @app.before_request
    def set_current_user():
        if os.getenv("FLASK_ENV") == "development":
            g.current_user = _MockUser(organization_id=1)
