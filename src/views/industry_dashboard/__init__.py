from flask import Blueprint

industry_dashboard_bp = Blueprint(
    "industry_dashboard",
    __name__,
    url_prefix="/industry-dashboard"
)

from src.views.industry_dashboard import views  # noqa: E402, F401
