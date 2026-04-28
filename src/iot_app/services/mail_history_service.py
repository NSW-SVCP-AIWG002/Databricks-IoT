"""メール通知履歴サービス

担当する処理:
- メール通知履歴一覧取得（検索・ソート・ページネーション）
- メール通知履歴詳細取得
- ソートカラム検証（sort_item_master経由のホワイトリスト）
- メール種別マスタ取得
"""

from __future__ import annotations

from datetime import date, datetime, time, timedelta
from typing import Optional

import pytz
from sqlalchemy import or_

from iot_app import db
from iot_app.common.logger import get_logger
from iot_app.models.notification import MailHistory, MailTypeMaster
from iot_app.models.sort_item import SortItemMaster

logger = get_logger(__name__)

_VIEW_ID_MAIL_HISTORY = 5
DEFAULT_SORT_ID = 3        # sent_at
DEFAULT_SORT_ORDER = 'desc'
DEFAULT_PER_PAGE = 25

# sort_item_master 未登録時のフォールバック（view_id=5 の初期データ）
_SORT_COLUMN_FALLBACK: dict[int, str] = {
    1: 'mail_type',
    2: 'subject',
    3: 'sent_at',
}


def get_mail_type_choices() -> list:
    """mail_type_master から有効なメール種別一覧を取得する"""
    return (
        MailTypeMaster.query
        .filter_by(delete_flag=False)
        .order_by(MailTypeMaster.mail_type_id)
        .all()
    )


def get_mail_type_by_id(mail_type_id: int) -> Optional[MailTypeMaster]:
    """メール種別IDからメール種別マスタレコードを取得する"""
    return db.session.get(MailTypeMaster, mail_type_id)


def get_sort_column(
    sort_id: int,
    view_id: int = _VIEW_ID_MAIL_HISTORY,
) -> Optional[str]:
    """sort_item_master からソートカラム名を取得する（ホワイトリスト検証）

    DBに該当レコードが存在しない場合は _SORT_COLUMN_FALLBACK で補完する。
    それも存在しない場合は None を返す。
    """
    item = SortItemMaster.query.filter_by(
        view_id=view_id,
        sort_item_id=sort_id,
        delete_flag=False,
    ).first()
    if item:
        return item.sort_item_name
    return _SORT_COLUMN_FALLBACK.get(sort_id)


def get_default_date_range() -> tuple[date, date]:
    """初期表示用デフォルト日付範囲を返す（JST基準）

    Returns:
        (sent_at_start, sent_at_end): 7日前〜当日 の date オブジェクト
    """
    jst = pytz.timezone('Asia/Tokyo')
    now_jst = datetime.now(jst)
    start = (now_jst - timedelta(days=7)).date()
    end = now_jst.date()
    return start, end


def get_mail_history_list(
    organization_id: int,
    mail_types: list,
    keyword: str,
    sent_at_start: Optional[date],
    sent_at_end: Optional[date],
    sort_column: str,
    order: str,
    page: int,
    per_page: int = DEFAULT_PER_PAGE,
) -> tuple[list, int]:
    """メール送信履歴一覧を取得する

    データスコープ制限（organization_id）・検索フィルタ・ソート・ページネーションを適用する。

    Args:
        organization_id: データスコープ制限用の組織ID
        mail_types: メール種別IDリスト（空リストの場合は絞り込みなし）
        keyword: 件名または本文の部分一致検索ワード（空文字の場合は絞り込みなし）
        sent_at_start: 送信日時の開始日（Noneの場合は絞り込みなし）
        sent_at_end: 送信日時の終了日（Noneの場合は絞り込みなし）
        sort_column: ソート対象カラム名（sort_item_master で検証済みの値）
        order: ソート順（'asc' or 'desc'）
        page: ページ番号（1始まり）
        per_page: 1ページあたりの件数

    Returns:
        (records, total): レコードリストと総件数
    """
    query = MailHistory.query.filter_by(organization_id=organization_id)

    if mail_types:
        query = query.filter(MailHistory.mail_type.in_(mail_types))

    if keyword:
        query = query.filter(
            or_(
                MailHistory.subject.like(f'%{keyword}%'),
                MailHistory.body.like(f'%{keyword}%'),
            )
        )

    if sent_at_start:
        start_dt = datetime.combine(sent_at_start, time.min)
        query = query.filter(MailHistory.sent_at >= start_dt)

    if sent_at_end:
        end_dt = datetime.combine(sent_at_end, time(23, 59, 59))
        query = query.filter(MailHistory.sent_at <= end_dt)

    col = getattr(MailHistory, sort_column, None)
    if col is None:
        col = getattr(MailHistory, 'sent_at')
    sort_expr = col.desc() if order == 'desc' else col.asc()
    # 第2ソートキーとして mail_history_id ASC を使用（ページング時の並び順を一定に保つ）
    query = query.order_by(sort_expr, MailHistory.mail_history_id.asc())

    total = query.count()
    offset = (page - 1) * per_page
    records = query.limit(per_page).offset(offset).all()

    return records, total


def get_mail_history_detail(
    mail_history_uuid: str,
    organization_id: int,
) -> Optional[MailHistory]:
    """UUIDで指定されたメール送信履歴を取得する（データスコープ制限あり）

    Args:
        mail_history_uuid: メール送信履歴UUID
        organization_id: データスコープ制限用の組織ID

    Returns:
        MailHistory レコード、または None（存在しない・アクセス不可）
    """
    return MailHistory.query.filter_by(
        mail_history_uuid=mail_history_uuid,
        organization_id=organization_id,
    ).first()
