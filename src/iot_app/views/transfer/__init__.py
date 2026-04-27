from flask import Blueprint

transfer_bp = Blueprint('transfer', __name__, url_prefix='/transfer')

from iot_app.views.transfer import views  # noqa: E402, F401
