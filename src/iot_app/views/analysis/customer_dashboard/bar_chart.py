from flask import abort

from iot_app.views.analysis.customer_dashboard import customer_dashboard_bp

# 起動エラー回避用スタブ、barchartブランチマージ時に上書きすること
@customer_dashboard_bp.route('/gadgets/<string:gadget_uuid>/data', methods=['POST'])
def gadget_data(gadget_uuid):
    abort(501)

# 起動エラー回避用スタブ、barchartブランチマージ時に上書きすること
@customer_dashboard_bp.route('/gadgets/<string:gadget_uuid>', methods=['GET'])
def gadget_csv_export(gadget_uuid):
    abort(501)
