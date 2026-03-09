"""
業種別ダッシュボード Blueprint

ルート一覧:
  GET  analysis/industry-dashboard/store-monitoring           店舗モニタリング初期表示・ページング
  POST analysis/industry-dashboard/store-monitoring           店舗モニタリング検索
  GET  analysis/industry-dashboard/store-monitoring/<uuid>    センサー情報表示
  GET  analysis/industry-dashboard/device-details/<uuid>      デバイス詳細初期表示・ページング・CSVエクスポート
  POST analysis/industry-dashboard/device-details/<uuid>      デバイス詳細検索（表示期間変更）
"""

import json

from flask import Blueprint, abort, g, make_response, render_template, request

from iot_app.services.industry_dashboard_service import (
    check_device_access,
    export_sensor_data_csv,
    get_accessible_organizations,
    get_default_date_range,
    get_device_alerts_with_count,
    get_device_list_with_count,
    get_graph_data,
    get_latest_sensor_data,
    get_recent_alerts_with_count,
    validate_date_range,
)

analysis_bp = Blueprint("analysis", __name__)

_ITEM_PER_PAGE = 10
_STORE_MONITORING_COOKIE = "store_monitoring_search_params"
_DEVICE_DETAILS_COOKIE = "device_details_search_params"
_COOKIE_MAX_AGE = 86400


def _get_store_monitoring_search_params():
    """Cookie から店舗モニタリング検索条件を取得する。存在しない場合はデフォルト値を返す。"""
    cookie_data = request.cookies.get(_STORE_MONITORING_COOKIE)
    if cookie_data:
        try:
            return json.loads(cookie_data)
        except (ValueError, TypeError):
            pass
    return {"organization_name": "", "device_name": "", "page": 1}


def _get_device_details_search_params():
    """Cookie からデバイス詳細検索条件を取得する。存在しない場合はデフォルト値を返す。"""
    cookie_data = request.cookies.get(_DEVICE_DETAILS_COOKIE)
    if cookie_data:
        try:
            return json.loads(cookie_data)
        except (ValueError, TypeError):
            pass
    return get_default_date_range()


def _set_cookie(response, name, params):
    """レスポンスに検索条件 Cookie をセットする。"""
    response.set_cookie(
        name,
        json.dumps(params),
        max_age=_COOKIE_MAX_AGE,
        httponly=True,
        samesite="Lax",
    )


# ---------------------------------------------------------------------------
# 店舗モニタリング
# ---------------------------------------------------------------------------


@analysis_bp.route("/analysis/industry-dashboard/store-monitoring", methods=["GET"])
def store_monitoring():
    """店舗モニタリング初期表示・ページング"""
    try:
        accessible_org_ids = get_accessible_organizations(
            g.current_user.organization_id
        )

        is_initial = "page" not in request.args
        if is_initial:
            search_params = {"organization_name": "", "device_name": "", "page": 1}
        else:
            search_params = _get_store_monitoring_search_params()
            search_params["page"] = request.args.get("page", 1, type=int)

        page = search_params.get("page", 1)

        alerts, alerts_total = get_recent_alerts_with_count(
            search_params, accessible_org_ids, limit=30
        )
        devices, devices_total = get_device_list_with_count(
            search_params, accessible_org_ids, page, _ITEM_PER_PAGE
        )

        response = make_response(
            render_template(
                "analysis/industry_dashboard/store_monitoring.html",
                alerts=alerts,
                alerts_total=alerts_total,
                devices=devices,
                devices_total=devices_total,
                page=page,
                per_page=_ITEM_PER_PAGE,
                search_params=search_params,
            )
        )

        _set_cookie(response, _STORE_MONITORING_COOKIE, search_params)
        return response

    except Exception as e:
        if hasattr(e, "code"):
            raise
        abort(500)


@analysis_bp.route("/analysis/industry-dashboard/store-monitoring", methods=["POST"])
def store_monitoring_search():
    """店舗モニタリング検索"""
    try:
        accessible_org_ids = get_accessible_organizations(
            g.current_user.organization_id
        )

        search_params = {
            "organization_name": request.form.get("organization_name", ""),
            "device_name": request.form.get("device_name", ""),
            "page": 1,
        }

        alerts, alerts_total = get_recent_alerts_with_count(
            search_params, accessible_org_ids, limit=30
        )
        devices, devices_total = get_device_list_with_count(
            search_params, accessible_org_ids, 1, _ITEM_PER_PAGE
        )

        response = make_response(
            render_template(
                "analysis/industry_dashboard/store_monitoring.html",
                alerts=alerts,
                alerts_total=alerts_total,
                devices=devices,
                devices_total=devices_total,
                page=1,
                per_page=_ITEM_PER_PAGE,
                search_params=search_params,
            )
        )

        _set_cookie(response, _STORE_MONITORING_COOKIE, search_params)
        return response

    except Exception as e:
        if hasattr(e, "code"):
            raise
        abort(500)


@analysis_bp.route(
    "/analysis/industry-dashboard/store-monitoring/<device_uuid>", methods=["GET"]
)
def show_sensor_info(device_uuid):
    """センサー情報表示"""
    try:
        accessible_org_ids = get_accessible_organizations(
            g.current_user.organization_id
        )

        device = check_device_access(device_uuid, accessible_org_ids)
        if not device:
            abort(404)

        search_params = _get_store_monitoring_search_params()
        page = search_params.get("page", 1)

        alerts, alerts_total = get_recent_alerts_with_count(
            search_params, accessible_org_ids, limit=30
        )
        devices, devices_total = get_device_list_with_count(
            search_params, accessible_org_ids, page, _ITEM_PER_PAGE
        )
        sensor_data = get_latest_sensor_data(device.device_id)

        return render_template(
            "analysis/industry_dashboard/store_monitoring.html",
            alerts=alerts,
            alerts_total=alerts_total,
            devices=devices,
            devices_total=devices_total,
            page=page,
            per_page=_ITEM_PER_PAGE,
            search_params=search_params,
            selected_device=device,
            sensor_data=sensor_data,
            show_sensor_info=True,
        )

    except Exception as e:
        if hasattr(e, "code"):
            raise
        abort(500)


# ---------------------------------------------------------------------------
# デバイス詳細
# ---------------------------------------------------------------------------


@analysis_bp.route(
    "/analysis/industry-dashboard/device-details/<device_uuid>", methods=["GET"]
)
def device_details(device_uuid):
    """デバイス詳細初期表示・ページング・CSVエクスポート"""
    try:
        accessible_org_ids = get_accessible_organizations(
            g.current_user.organization_id
        )

        device = check_device_access(device_uuid, accessible_org_ids)
        if not device:
            abort(404)

        is_initial = "page" not in request.args
        if is_initial:
            search_params = get_default_date_range()
            search_params["page"] = 1
        else:
            search_params = _get_device_details_search_params()
            search_params["page"] = request.args.get("page", 1, type=int)

        # CSVエクスポート
        if request.args.get("export") == "csv":
            csv_search_params = _get_device_details_search_params()
            return export_sensor_data_csv(device, csv_search_params)

        page = search_params.get("page", 1)

        alerts, alerts_total = get_device_alerts_with_count(
            device.device_id, search_params
        )
        graph_data = get_graph_data(device.device_id, search_params)

        response = make_response(
            render_template(
                "analysis/industry_dashboard/device_details.html",
                device=device,
                alerts=alerts,
                alerts_total=alerts_total,
                graph_data=graph_data,
                page=page,
                per_page=_ITEM_PER_PAGE,
                search_params=search_params,
            )
        )

        if is_initial:
            _set_cookie(response, _DEVICE_DETAILS_COOKIE, search_params)
        return response

    except Exception as e:
        if hasattr(e, "code"):
            raise
        abort(500)


@analysis_bp.route(
    "/analysis/industry-dashboard/device-details/<device_uuid>", methods=["POST"]
)
def device_details_search(device_uuid):
    """デバイス詳細検索（表示期間変更）"""
    try:
        accessible_org_ids = get_accessible_organizations(
            g.current_user.organization_id
        )

        device = check_device_access(device_uuid, accessible_org_ids)
        if not device:
            abort(404)

        start_str = request.form.get("search_start_datetime", "")
        end_str = request.form.get("search_end_datetime", "")

        errors = validate_date_range(start_str, end_str)
        if errors:
            abort(400)

        search_params = {
            "search_start_datetime": start_str,
            "search_end_datetime": end_str,
            "page": 1,
        }

        alerts, alerts_total = get_device_alerts_with_count(
            device.device_id, search_params
        )
        graph_data = get_graph_data(device.device_id, search_params)

        response = make_response(
            render_template(
                "analysis/industry_dashboard/device_details.html",
                device=device,
                alerts=alerts,
                alerts_total=alerts_total,
                graph_data=graph_data,
                page=1,
                per_page=_ITEM_PER_PAGE,
                search_params=search_params,
            )
        )

        _set_cookie(response, _DEVICE_DETAILS_COOKIE, search_params)
        return response

    except Exception as e:
        if hasattr(e, "code"):
            raise
        abort(500)
