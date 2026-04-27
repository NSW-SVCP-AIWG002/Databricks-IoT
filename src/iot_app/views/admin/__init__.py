from flask import Blueprint

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

from iot_app.views.admin import devices  # noqa: F401, E402
