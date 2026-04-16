from flask import Blueprint

alert_bp = Blueprint('alert', __name__)

from iot_app.views.alert import alert_history  # noqa: F401
