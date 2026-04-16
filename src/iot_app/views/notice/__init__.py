from flask import Blueprint

notice_bp = Blueprint('notice', __name__)

from iot_app.views.notice import mail_history  # noqa: F401, E402
