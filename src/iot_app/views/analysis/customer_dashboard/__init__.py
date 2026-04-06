from flask import Blueprint

customer_dashboard_bp = Blueprint(
    'customer_dashboard',
    __name__,
    url_prefix='/analysis/customer-dashboard',
)

from iot_app.views.analysis.customer_dashboard import common  # noqa: E402, F401
from iot_app.views.analysis.customer_dashboard import bar_chart  # noqa: E402, F401
from iot_app.views.analysis.customer_dashboard import timeline  # noqa: E402, F401
<<<<<<< HEAD
=======
from iot_app.views.analysis.customer_dashboard import circle_chart  # noqa: E402, F401
>>>>>>> origin/main
