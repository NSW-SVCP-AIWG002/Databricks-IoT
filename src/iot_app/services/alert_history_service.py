from datetime import datetime, timedelta

from iot_app import db
from iot_app.models.alert import AlertHistoryByUser

ITEM_PER_PAGE = 25
INIT_START_DATETIME = 7  # days

# sort_item_id → AlertHistoryByUser カラムのマッピング（ALT-005固定）
_SORT_COLUMN_MAP = {
    1: AlertHistoryByUser.alert_occurrence_datetime,
    2: AlertHistoryByUser.device_name,
    3: AlertHistoryByUser.device_location,
    4: AlertHistoryByUser.alert_name,
    5: AlertHistoryByUser.alert_level_id,
    6: AlertHistoryByUser.alert_status_id,
}


def get_default_search_params() -> dict:
    """アラート履歴一覧検索のデフォルトパラメータを返す"""
    now = datetime.now()
    return {
        'page': 1,
        'per_page': ITEM_PER_PAGE,
        'sort_item_id': 1,   # アラート発生日時
        'sort_order_id': 2,  # 降順
        'start_datetime': (now - timedelta(days=INIT_START_DATETIME)).replace(
            hour=0, minute=0, second=0, microsecond=0
        ).strftime('%Y/%m/%d %H:%M'),
        'end_datetime': now.replace(
            hour=23, minute=59, second=59, microsecond=0
        ).strftime('%Y/%m/%d %H:%M'),
        'device_name': '',
        'device_location': '',
        'alert_name': '',
        'alert_level_id': None,
        'alert_status_id': None,
    }


def search_alert_histories(search_params: dict, user_id: int) -> tuple[list, int]:
    """アラート履歴一覧をスコープ制限付きで検索する

    Args:
        search_params: 検索条件（page, per_page, sort_item_id, sort_order_id, 各検索項目）
        user_id: ログインユーザーID（v_alert_history_by_user のスコープ制限に使用）

    Returns:
        (alert_histories, total): アラート履歴リストと総件数のタプル
    """
    page = search_params['page']
    per_page = search_params['per_page']
    sort_item_id = search_params.get('sort_item_id', 1)
    sort_order_id = search_params.get('sort_order_id', 2)
    offset = (page - 1) * per_page

    query = db.session.query(AlertHistoryByUser).filter(
        AlertHistoryByUser.user_id == user_id,
        AlertHistoryByUser.delete_flag == False,
    )

    if search_params.get('start_datetime') and search_params.get('end_datetime'):
        query = query.filter(
            AlertHistoryByUser.alert_occurrence_datetime.between(
                search_params['start_datetime'], search_params['end_datetime']
            )
        )
    if search_params.get('device_name'):
        query = query.filter(
            AlertHistoryByUser.device_name.like(f"%{search_params['device_name']}%")
        )
    if search_params.get('device_location'):
        query = query.filter(
            AlertHistoryByUser.device_location.like(f"%{search_params['device_location']}%")
        )
    if search_params.get('alert_name'):
        query = query.filter(
            AlertHistoryByUser.alert_name.like(f"%{search_params['alert_name']}%")
        )
    if search_params.get('alert_level_id') is not None:
        query = query.filter(
            AlertHistoryByUser.alert_level_id == search_params['alert_level_id']
        )
    if search_params.get('alert_status_id') is not None:
        query = query.filter(
            AlertHistoryByUser.alert_status_id == search_params['alert_status_id']
        )

    sort_col = _SORT_COLUMN_MAP.get(sort_item_id, AlertHistoryByUser.alert_occurrence_datetime)
    second_sort_col = AlertHistoryByUser.alert_history_id

    if sort_order_id == 1:
        sort_order = 'ASC'
    elif sort_order_id == 2:
        sort_order = 'DESC'
    else:
        sort_order = None

    if sort_order == 'ASC':
        query = query.order_by(sort_col.asc(), second_sort_col.asc())
    elif sort_order == 'DESC':
        query = query.order_by(sort_col.desc(), second_sort_col.desc())

    total = query.count()
    alert_histories = query.limit(per_page).offset(offset).all()
    return alert_histories, total


def get_alert_history_detail(alert_history_uuid: str, user_id: int):
    """アラート履歴詳細をUUIDとユーザーIDで取得する

    Args:
        alert_history_uuid: アラート履歴UUID
        user_id: ログインユーザーID（スコープ制限に使用）

    Returns:
        AlertHistoryByUser オブジェクト。該当なし・スコープ外・論理削除済みの場合は None
    """
    return db.session.query(AlertHistoryByUser).filter(
        AlertHistoryByUser.alert_history_uuid == alert_history_uuid,
        AlertHistoryByUser.user_id == user_id,
        AlertHistoryByUser.delete_flag == False,
    ).first()
