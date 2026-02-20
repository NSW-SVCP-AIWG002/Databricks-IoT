"""
業種別ダッシュボード機能（冷蔵冷凍庫） ビュー層

ルート一覧:
  GET  /industry-dashboard/store-monitoring            店舗モニタリング初期表示・ページング
  POST /industry-dashboard/store-monitoring            店舗モニタリング検索
  GET  /industry-dashboard/store-monitoring/<uuid>     センサー情報表示
  GET  /industry-dashboard/device-details/<uuid>       デバイス詳細初期表示・ページング・CSVエクスポート
  POST /industry-dashboard/device-details/<uuid>       デバイス詳細検索（表示期間変更）

参照:
- workflow-specification.md
- ui-specification.md
"""

import json
import logging

from flask import abort, g, make_response, render_template, request

from src.services.industry_dashboard_service import (
    ITEM_PER_PAGE,
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
from src.views.industry_dashboard import industry_dashboard_bp

logger = logging.getLogger(__name__)

# Cookie キー名
_COOKIE_STORE_MONITORING = "store_monitoring_search_params"
_COOKIE_DEVICE_DETAILS = "device_details_search_params"
_COOKIE_MAX_AGE = 86400  # 24時間


def _get_default_store_search_params():
    """店舗モニタリングのデフォルト検索条件を返す"""
    return {"organization_name": "", "device_name": "", "page": 1}


# ---------------------------------------------------------------------------
# タスク4-1: 店舗モニタリング初期表示・ページング (GET)
# ---------------------------------------------------------------------------

@industry_dashboard_bp.route("/store-monitoring", methods=["GET"])
def store_monitoring():
    """店舗モニタリング初期表示・ページング

    pageパラメータなし → 初期表示（Cookie検索条件クリア）
    pageパラメータあり → ページング（Cookieから検索条件取得）
    """
    logger.info(f"店舗モニタリング表示開始: user_id={getattr(g, 'current_user_id', None)}")

    try:
        if "page" not in request.args:
            # 初期表示: 検索条件を初期化
            search_params = _get_default_store_search_params()
            save_cookie = True
        else:
            # ページング: Cookieから検索条件取得
            cookie_data = request.cookies.get(_COOKIE_STORE_MONITORING)
            if cookie_data:
                search_params = json.loads(cookie_data)
            else:
                search_params = _get_default_store_search_params()
            search_params["page"] = request.args.get("page", 1, type=int)
            save_cookie = False

        page = search_params.get("page", 1)
        accessible_org_ids = get_accessible_organizations(
            g.current_user.organization_id
        )

        alerts, alerts_total = get_recent_alerts_with_count(
            search_params, accessible_org_ids
        )
        devices, devices_total = get_device_list_with_count(
            search_params, accessible_org_ids, page
        )

        response = make_response(render_template(
            "dashboard/store_monitoring.html",
            alerts=alerts,
            alerts_total=alerts_total,
            devices=devices,
            devices_total=devices_total,
            page=page,
            per_page=ITEM_PER_PAGE,
            search_params=search_params,
            selected_device=None,
            sensor_data=None,
            show_sensor_info=False,
        ))

        if save_cookie:
            response.set_cookie(
                _COOKIE_STORE_MONITORING,
                json.dumps(search_params),
                max_age=_COOKIE_MAX_AGE,
                httponly=True,
                samesite="Lax",
            )

        logger.info("店舗モニタリング表示完了")
        return response

    except Exception as e:
        logger.error(f"店舗モニタリング表示エラー: {e}")
        abort(500)


# ---------------------------------------------------------------------------
# タスク4-2: 店舗モニタリング検索 (POST)
# ---------------------------------------------------------------------------

@industry_dashboard_bp.route("/store-monitoring", methods=["POST"])
def store_monitoring_search():
    """店舗モニタリング検索

    フォームから検索条件を取得し、アラート一覧・デバイス一覧を絞り込む。
    """
    logger.info(f"店舗モニタリング検索開始: user_id={getattr(g, 'current_user_id', None)}")

    try:
        search_params = {
            "organization_name": request.form.get("organization_name", ""),
            "device_name": request.form.get("device_name", ""),
            "page": 1,
        }

        accessible_org_ids = get_accessible_organizations(
            g.current_user.organization_id
        )

        alerts, alerts_total = get_recent_alerts_with_count(
            search_params, accessible_org_ids
        )
        devices, devices_total = get_device_list_with_count(
            search_params, accessible_org_ids, 1
        )

        response = make_response(render_template(
            "dashboard/store_monitoring.html",
            alerts=alerts,
            alerts_total=alerts_total,
            devices=devices,
            devices_total=devices_total,
            page=1,
            per_page=ITEM_PER_PAGE,
            search_params=search_params,
            selected_device=None,
            sensor_data=None,
            show_sensor_info=False,
        ))

        response.set_cookie(
            _COOKIE_STORE_MONITORING,
            json.dumps(search_params),
            max_age=_COOKIE_MAX_AGE,
            httponly=True,
            samesite="Lax",
        )

        logger.info("店舗モニタリング検索完了")
        return response

    except Exception as e:
        logger.error(f"店舗モニタリング検索エラー: {e}")
        abort(500)


# ---------------------------------------------------------------------------
# タスク4-3: センサー情報表示 (GET)
# ---------------------------------------------------------------------------

@industry_dashboard_bp.route("/store-monitoring/<device_uuid>", methods=["GET"])
def show_sensor_info(device_uuid):
    """センサー情報表示

    デバイス一覧の「センサー情報表示」ボタン押下時に呼ばれる。
    店舗モニタリング画面のセンサー情報欄に最新センサーデータを表示する。
    """
    logger.info(
        f"センサー情報表示開始: user_id={getattr(g, 'current_user_id', None)}, "
        f"device_uuid={device_uuid}"
    )

    try:
        accessible_org_ids = get_accessible_organizations(
            g.current_user.organization_id
        )

        device = check_device_access(device_uuid, accessible_org_ids)
        if not device:
            logger.warning(f"デバイスアクセス拒否: device_uuid={device_uuid}")
            abort(404)

        cookie_data = request.cookies.get(_COOKIE_STORE_MONITORING)
        if cookie_data:
            search_params = json.loads(cookie_data)
        else:
            search_params = _get_default_store_search_params()

        page = search_params.get("page", 1)

        alerts, alerts_total = get_recent_alerts_with_count(
            search_params, accessible_org_ids
        )
        devices, devices_total = get_device_list_with_count(
            search_params, accessible_org_ids, page
        )

        sensor_data = get_latest_sensor_data(device.device_id)

        logger.info(f"センサー情報表示完了: device_uuid={device_uuid}")
        return render_template(
            "dashboard/store_monitoring.html",
            alerts=alerts,
            alerts_total=alerts_total,
            devices=devices,
            devices_total=devices_total,
            page=page,
            per_page=ITEM_PER_PAGE,
            search_params=search_params,
            selected_device=device,
            sensor_data=sensor_data,
            show_sensor_info=True,
        )

    except Exception as e:
        logger.error(f"センサー情報表示エラー: device_uuid={device_uuid}, error={e}")
        abort(500)


# ---------------------------------------------------------------------------
# タスク4-4 / タスク4-6: デバイス詳細初期表示・ページング・CSVエクスポート (GET)
# ---------------------------------------------------------------------------

@industry_dashboard_bp.route("/device-details/<device_uuid>", methods=["GET"])
def device_details(device_uuid):
    """デバイス詳細初期表示・ページング・CSVエクスポート

    pageパラメータなし → 初期表示（Cookie検索条件クリア、表示期間=直近24時間）
    pageパラメータあり → ページング（Cookieから検索条件取得）
    export=csv       → CSVエクスポート
    """
    logger.info(
        f"デバイス詳細表示開始: user_id={getattr(g, 'current_user_id', None)}, "
        f"device_uuid={device_uuid}"
    )

    try:
        accessible_org_ids = get_accessible_organizations(
            g.current_user.organization_id
        )

        device = check_device_access(device_uuid, accessible_org_ids)
        if not device:
            logger.warning(f"デバイスアクセス拒否: device_uuid={device_uuid}")
            abort(404)

        # CSVエクスポート分岐
        if request.args.get("export") == "csv":
            cookie_data = request.cookies.get(_COOKIE_DEVICE_DETAILS)
            if cookie_data:
                search_params = json.loads(cookie_data)
            else:
                search_params = get_default_date_range()
            logger.info(f"CSVエクスポート開始: device_uuid={device_uuid}")
            return export_sensor_data_csv(device, search_params)

        if "page" not in request.args:
            # 初期表示
            search_params = get_default_date_range()
            search_params["page"] = 1
            save_cookie = True
        else:
            # ページング
            cookie_data = request.cookies.get(_COOKIE_DEVICE_DETAILS)
            if cookie_data:
                search_params = json.loads(cookie_data)
            else:
                search_params = get_default_date_range()
            search_params["page"] = request.args.get("page", 1, type=int)
            save_cookie = False

        page = search_params["page"]

        alerts, alerts_total = get_device_alerts_with_count(
            device.device_id, search_params
        )
        graph_data = get_graph_data(device.device_id, search_params)

        response = make_response(render_template(
            "dashboard/device_details.html",
            device=device,
            alerts=alerts,
            alerts_total=alerts_total,
            graph_data=graph_data,
            page=page,
            per_page=ITEM_PER_PAGE,
            search_params=search_params,
        ))

        if save_cookie:
            response.set_cookie(
                _COOKIE_DEVICE_DETAILS,
                json.dumps(search_params),
                max_age=_COOKIE_MAX_AGE,
                httponly=True,
                samesite="Lax",
            )

        logger.info(f"デバイス詳細表示完了: device_uuid={device_uuid}")
        return response

    except Exception as e:
        logger.error(f"デバイス詳細表示エラー: device_uuid={device_uuid}, error={e}")
        abort(500)


# ---------------------------------------------------------------------------
# タスク4-5: デバイス詳細検索（表示期間変更）(POST)
# ---------------------------------------------------------------------------

@industry_dashboard_bp.route("/device-details/<device_uuid>", methods=["POST"])
def device_details_search(device_uuid):
    """デバイス詳細検索（表示期間変更）

    フォームから表示期間を取得し、グラフデータを再取得する。
    """
    logger.info(
        f"デバイス詳細検索開始: user_id={getattr(g, 'current_user_id', None)}, "
        f"device_uuid={device_uuid}"
    )

    try:
        accessible_org_ids = get_accessible_organizations(
            g.current_user.organization_id
        )

        device = check_device_access(device_uuid, accessible_org_ids)
        if not device:
            logger.warning(f"デバイスアクセス拒否: device_uuid={device_uuid}")
            abort(404)

        start_dt = request.form.get("search_start_datetime", "")
        end_dt = request.form.get("search_end_datetime", "")

        errors = validate_date_range(start_dt, end_dt)
        if errors:
            logger.warning(f"デバイス詳細検索バリデーションエラー: {errors}")
            abort(400)

        search_params = {
            "search_start_datetime": start_dt,
            "search_end_datetime": end_dt,
            "page": 1,
        }

        alerts, alerts_total = get_device_alerts_with_count(
            device.device_id, search_params
        )
        graph_data = get_graph_data(device.device_id, search_params)

        response = make_response(render_template(
            "dashboard/device_details.html",
            device=device,
            alerts=alerts,
            alerts_total=alerts_total,
            graph_data=graph_data,
            page=1,
            per_page=ITEM_PER_PAGE,
            search_params=search_params,
        ))

        response.set_cookie(
            _COOKIE_DEVICE_DETAILS,
            json.dumps(search_params),
            max_age=_COOKIE_MAX_AGE,
            httponly=True,
            samesite="Lax",
        )

        logger.info(f"デバイス詳細検索完了: device_uuid={device_uuid}")
        return response

    except Exception as e:
        logger.error(f"デバイス詳細検索エラー: device_uuid={device_uuid}, error={e}")
        abort(500)
