from flask import Blueprint

customer_dashboard_bp = Blueprint(
    'customer_dashboard',
    __name__,
    url_prefix='/analysis/customer-dashboard',
)

from iot_app.views.analysis.customer_dashboard import common  # noqa: E402, F401
