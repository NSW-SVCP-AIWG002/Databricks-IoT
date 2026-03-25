from flask import Blueprint

customer_dashboard_bp = Blueprint(
    'customer_dashboard',
    __name__,
    url_prefix='/analysis/customer-dashboard',
)
