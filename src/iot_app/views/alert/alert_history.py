from flask import abort, g, make_response, render_template, request

from iot_app import db
from iot_app.common.cookie import (
    clear_search_conditions_cookie,
    get_search_conditions_cookie,
    set_search_conditions_cookie,
)
from iot_app.decorators.auth import require_role
from iot_app.models.alert import AlertLevelMaster, AlertStatusMaster
from iot_app.services.alert_history_service import (
    get_alert_history_detail,
    get_default_search_params,
    search_alert_histories,
)
from iot_app.views.alert import alert_bp

# sort_item_master が未実装のため静的リストで代替
_SORT_ITEMS = [
    {'value': 'alert_occurrence_datetime', 'label': 'アラート発生日時'},
    {'value': 'device_name',               'label': 'デバイス名'},
    {'value': 'device_location',           'label': '設置場所'},
    {'value': 'alert_name',                'label': 'アラート名'},
    {'value': 'alert_level_id',            'label': 'アラートレベル'},
    {'value': 'alert_status_id',           'label': 'ステータス'},
]

_ALL_ROLES = (
    'system_admin',
    'management_admin',
    'sales_company_user',
    'service_company_user',
)


def _load_masters():
    """アラートレベル・ステータスマスタを取得する"""
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
    return alert_levels, alert_statuses


@alert_bp.route('/alert/alert-history', methods=['GET'])
@require_role(*_ALL_ROLES)
def alert_history_list():
    """アラート履歴一覧 初期表示・ページング"""
    user_id = g.current_user.user_id

    if 'page' not in request.args:
        # 初期表示: デフォルト検索条件でCookieをリセット
        search_params = get_default_search_params()
        save_cookie = True
    else:
        # ページング: Cookieから検索条件取得 → page のみ上書き
        search_params = get_search_conditions_cookie('alert_history') or get_default_search_params()
        search_params['page'] = request.args.get('page', 1, type=int)
        save_cookie = False

    try:
        alert_histories, total = search_alert_histories(search_params, user_id)
    except Exception:
        abort(500)

    alert_levels, alert_statuses = _load_masters()

    response = make_response(render_template(
        'analysis/alert_history/index.html',
        alert_histories=alert_histories,
        total=total,
        search_params=search_params,
        alert_levels=alert_levels,
        alert_statuses=alert_statuses,
        sort_items=_SORT_ITEMS,
    ))

    if save_cookie:
        response = clear_search_conditions_cookie(response, 'alert_history')
        response = set_search_conditions_cookie(response, 'alert_history', search_params)

    return response


@alert_bp.route('/alert/alert-history', methods=['POST'])
@require_role(*_ALL_ROLES)
def alert_history_search():
    """アラート履歴検索実行"""
    user_id = g.current_user.user_id

    raw_level  = request.form.get('alert_level_id')
    raw_status = request.form.get('alert_status_id')

    search_params = {
        'page':            1,
        'per_page':        25,
        'sort_by':         request.form.get('sort_by', 'alert_occurrence_datetime'),
        'order':           request.form.get('order', 'desc'),
        'start_datetime':  request.form.get('start_datetime', ''),
        'end_datetime':    request.form.get('end_datetime', ''),
        'device_name':     request.form.get('device_name', ''),
        'device_location': request.form.get('device_location', ''),
        'alert_name':      request.form.get('alert_name', ''),
        'alert_level_id':  int(raw_level)  if raw_level  else None,
        'alert_status_id': int(raw_status) if raw_status else None,
    }

    try:
        alert_histories, total = search_alert_histories(search_params, user_id)
    except Exception:
        abort(500)

    alert_levels, alert_statuses = _load_masters()

    response = make_response(render_template(
        'analysis/alert_history/index.html',
        alert_histories=alert_histories,
        total=total,
        search_params=search_params,
        alert_levels=alert_levels,
        alert_statuses=alert_statuses,
        sort_items=_SORT_ITEMS,
    ))

    response = clear_search_conditions_cookie(response, 'alert_history')
    response = set_search_conditions_cookie(response, 'alert_history', search_params)

    return response


@alert_bp.route('/alert/alert-history/<alert_history_uuid>', methods=['GET'])
@require_role(*_ALL_ROLES)
def alert_history_detail(alert_history_uuid):
    """アラート履歴詳細 参照モーダル"""
    user_id = g.current_user.user_id

    try:
        alert_history = get_alert_history_detail(alert_history_uuid, user_id)
    except Exception:
        abort(404)

    if alert_history is None:
        abort(404)

    return render_template(
        'analysis/alert_history/modals/alert_history_reference.html',
        alert_history=alert_history,
    )
