from flask import Blueprint

customer_dashboard_bp = Blueprint(
    'customer_dashboard',
    __name__,
    url_prefix='/analysis/customer-dashboard',
)

from iot_app.views.analysis import customer_dashboard  # noqa: E402, F401
