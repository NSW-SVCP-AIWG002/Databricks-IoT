# TODO: 時系列グラフガジェット ルート実装（timeline ブランチから移植予定）
from flask import abort

from iot_app.views.analysis.customer_dashboard import customer_dashboard_bp  # noqa: F401


def handle_gadget_data(gadget_uuid):
    """時系列グラフガジェットデータ取得（スタブ） TODO:時系列マージ後上書き"""
    abort(501)


def handle_gadget_csv_export(gadget_uuid):
    """時系列グラフガジェット CSVエクスポート（スタブ） TODO:時系列マージ後上書き"""
    abort(501)
