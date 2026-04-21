from flask import abort, g, make_response, redirect, render_template, request, url_for

from iot_app import db
from iot_app.common.constants import SORT_ORDER
from iot_app.common.cookie import (
    clear_search_conditions_cookie,
    get_search_conditions_cookie,
    set_search_conditions_cookie,
)
from iot_app.common.logger import get_logger
from iot_app.decorators.auth import require_role
from iot_app.models.alert import AlertLevelMaster, AlertStatusMaster
from iot_app.models.sort_item import SortItemMaster
from iot_app.services.alert_history_service import (
    get_alert_history_detail,
    get_default_search_params,
    search_alert_histories,
)
from iot_app.views.alert import alert_bp

logger = get_logger(__name__)

_ALL_ROLES = (
    'system_admin',
    'management_admin',
    'sales_company_user',
    'service_company_user',
)

_ALERT_HISTORY_VIEW_ID = 5  # ALT-005 アラート履歴一覧


def _load_masters():
    """アラートレベル・ステータス・ソート項目マスタを取得する"""
    alert_levels = (
        db.session.query(AlertLevelMaster)
        .filter_by(delete_flag=False)
        .order_by(AlertLevelMaster.alert_level_id)
        .all()
    )
    alert_statuses = (
        db.session.query(AlertStatusMaster)
        .filter_by(delete_flag=False)
        .order_by(AlertStatusMaster.alert_status_id)
        .all()
    )
    sort_items = (
        db.session.query(SortItemMaster)
        .filter_by(view_id=_ALERT_HISTORY_VIEW_ID, delete_flag=False)
        .order_by(SortItemMaster.sort_order)
        .all()
    )
    return alert_levels, alert_statuses, sort_items


@alert_bp.route('/alert/alert-history', methods=['GET'])
@require_role(*_ALL_ROLES)
def alert_history_list():
    """アラート履歴一覧 初期表示・ページング"""
    user_id = g.current_user.user_id
    logger.info("アラート履歴一覧 処理開始 user_id=%s", user_id)

    if 'page' not in request.args:
        # 初期表示: デフォルト検索条件でCookieをリセット
        search_params = get_default_search_params()
        save_cookie = True
    else:
        # ページング: Cookieから検索条件取得 → page のみ上書き
        search_params = get_search_conditions_cookie('alert_history') or get_default_search_params()
        search_params['page'] = max(1, request.args.get('page', 1, type=int))
        save_cookie = False

    try:
        logger.info("アラート履歴一覧 DB取得開始 user_id=%s", user_id)
        alert_histories, total = search_alert_histories(search_params, user_id)
        logger.info("アラート履歴一覧 DB取得完了 user_id=%s 件数=%s", user_id, total)
    except Exception:
        abort(500)

    alert_levels, alert_statuses, sort_items = _load_masters()

    response = make_response(render_template(
        'alert/alert-history/list.html',
        alert_histories=alert_histories,
        total=total,
        search_params=search_params,
        alert_levels=alert_levels,
        alert_statuses=alert_statuses,
        sort_items=sort_items,
        sort_orders=SORT_ORDER,
    ))

    if save_cookie:
        response = clear_search_conditions_cookie(response, 'alert_history')
        response = set_search_conditions_cookie(response, 'alert_history', search_params)

    logger.info("アラート履歴一覧 処理完了 user_id=%s", user_id)
    return response


@alert_bp.route('/alert/alert-history', methods=['POST'])
@require_role(*_ALL_ROLES)
def alert_history_search():
    """アラート履歴検索実行（PRG: Cookie保存後GETへリダイレクト）"""
    user_id = g.current_user.user_id
    logger.info("アラート履歴検索 処理開始 user_id=%s", user_id)

    raw_level      = request.form.get('alert_level_id')
    raw_status     = request.form.get('alert_status_id')
    raw_sort_item  = request.form.get('sort_item_id')
    raw_sort_order = request.form.get('sort_order_id')

    search_params = {
        'page':            1,
        'per_page':        25,
        'sort_item_id':    int(raw_sort_item)  if raw_sort_item  else 1,
        'sort_order_id':   int(raw_sort_order) if raw_sort_order else 2,
        'start_datetime':  request.form.get('start_datetime', ''),
        'end_datetime':    request.form.get('end_datetime', ''),
        'device_name':     request.form.get('device_name', ''),
        'device_location': request.form.get('device_location', ''),
        'alert_name':      request.form.get('alert_name', ''),
        'alert_level_id':  int(raw_level)  if raw_level  else None,
        'alert_status_id': int(raw_status) if raw_status else None,
    }

    response = make_response(redirect(url_for('alert.alert_history_list', page=1)))
    response = clear_search_conditions_cookie(response, 'alert_history')
    response = set_search_conditions_cookie(response, 'alert_history', search_params)

    logger.info("アラート履歴検索 処理完了（PRGリダイレクト） user_id=%s", user_id)
    return response


@alert_bp.route('/alert/alert-history/<alert_history_uuid>', methods=['GET'])
@require_role(*_ALL_ROLES)
def alert_history_detail(alert_history_uuid):
    """アラート履歴詳細 参照モーダル"""
    user_id = g.current_user.user_id

    try:
        alert_history = get_alert_history_detail(alert_history_uuid, user_id)
    except Exception:
        logger.error("アラート履歴詳細 取得エラー user_id=%s uuid=%s", user_id, alert_history_uuid, exc_info=True)
        abort(404)

    if alert_history is None:
        abort(404)

    return render_template(
        'alert/alert-history/detail_modal.html',
        alert_history=alert_history,
    )
