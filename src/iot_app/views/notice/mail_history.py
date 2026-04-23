"""
メール通知履歴 ルート

ルート一覧:
  GET  /notice/mail-history                       一覧初期表示・ページング・ソート
  POST /notice/mail-history                       検索
  GET  /notice/mail-history/<mail_history_uuid>   詳細モーダル（パーシャル）
"""

from datetime import date

from flask import abort, g, make_response, render_template, request
from flask_wtf import FlaskForm
from wtforms import DateField, SelectMultipleField, StringField
from wtforms.validators import Length, Optional

from iot_app.common.cookie import get_search_conditions_cookie, set_search_conditions_cookie
from iot_app.common.logger import get_logger
from iot_app.services.mail_history_service import (
    DEFAULT_PER_PAGE,
    DEFAULT_SORT_ID,
    DEFAULT_SORT_ORDER,
    get_default_date_range,
    get_mail_history_detail,
    get_mail_history_list,
    get_mail_type_by_id,
    get_mail_type_choices,
    get_sort_column,
)
from iot_app.views.notice import notice_bp

logger = get_logger(__name__)

# メール種別ID → バッジCSSクラスのマッピング
_MAIL_TYPE_BADGE_CLASS: dict[int, str] = {
    1: 'danger',   # アラート通知: 赤
    2: 'info',     # 招待メール: 青
    3: 'warning',  # パスワードリセット: 黄
    4: 'success',  # システム通知: 緑
}


class MailHistorySearchForm(FlaskForm):
    mail_type_ids = SelectMultipleField(
        'メール種別',
        coerce=int,
        choices=[],
        validators=[Optional()],
    )
    keyword = StringField(
        'キーワード（件名・本文）',
        validators=[Optional(), Length(max=255)],
    )
    sent_at_start = DateField('送信日時（開始）', validators=[Optional()])
    sent_at_end = DateField('送信日時（終了）', validators=[Optional()])


def _init_params() -> dict:
    """初期表示用デフォルト検索条件を返す"""
    start, end = get_default_date_range()
    return {
        'mail_types': [],
        'keyword': '',
        'sent_at_start': start.isoformat(),
        'sent_at_end': end.isoformat(),
        'sort_id': DEFAULT_SORT_ID,
        'order': DEFAULT_SORT_ORDER,
        'page': 1,
    }


def _resolve_sort(sort_id: int, order: str) -> tuple:
    """sort_id を検証してカラム名を返す。無効な場合はデフォルト値にフォールバック。"""
    column = get_sort_column(sort_id)
    if column is None:
        column = get_sort_column(DEFAULT_SORT_ID) or 'sent_at'
    if order not in ('asc', 'desc'):
        order = DEFAULT_SORT_ORDER
    return column, order


def _build_form(mail_type_list: list) -> MailHistorySearchForm:
    form = MailHistorySearchForm()
    form.mail_type_ids.choices = [
        (mt.mail_type_id, mt.mail_type_name) for mt in mail_type_list
    ]
    return form


def _build_template_context(
    form,
    mail_type_list,
    records,
    total,
    page,
    sort_id,
    order,
    params,
) -> dict:
    """テンプレートに渡すコンテキスト辞書を構築する"""
    total_pages = (total + DEFAULT_PER_PAGE - 1) // DEFAULT_PER_PAGE
    mail_type_map = {mt.mail_type_id: mt.mail_type_name for mt in mail_type_list}
    return dict(
        form=form,
        mail_histories=records,
        mail_type_list=mail_type_list,
        mail_type_map=mail_type_map,
        mail_type_badge=_MAIL_TYPE_BADGE_CLASS,
        total=total,
        page=page,
        total_pages=total_pages,
        per_page=DEFAULT_PER_PAGE,
        sort_id=sort_id,
        order=order,
        search_params=params,
    )


@notice_bp.route('/notice/mail-history', methods=['GET'])
def mail_history_list():
    """メール通知履歴一覧（初期表示・ページング・ソート）"""
    logger.info('メール通知履歴一覧表示開始')
    organization_id = g.current_user.organization_id

    mail_type_list = get_mail_type_choices()
    form = _build_form(mail_type_list)

    has_page = 'page' in request.args
    has_sort = 'sort_id' in request.args

    if not has_page and not has_sort:
        # 初期表示: Cookie をリセットしてデフォルト値で初期化
        params = _init_params()
    elif has_sort:
        # ソート: Cookie の検索条件を保持してソート条件を更新
        params = get_search_conditions_cookie('mail_history') or _init_params()
        params['sort_id'] = request.args.get('sort_id', DEFAULT_SORT_ID, type=int)
        params['order'] = request.args.get('order', DEFAULT_SORT_ORDER)
        params['page'] = 1
    else:
        # ページング: Cookie の検索条件を保持してページを更新
        params = get_search_conditions_cookie('mail_history') or _init_params()
        params['page'] = max(1, request.args.get('page', 1, type=int))

    sort_id = params.get('sort_id', DEFAULT_SORT_ID)
    order = params.get('order', DEFAULT_SORT_ORDER)
    sort_column, order = _resolve_sort(sort_id, order)
    page = params.get('page', 1)

    sent_at_start_str = params.get('sent_at_start')
    sent_at_end_str = params.get('sent_at_end')
    start = date.fromisoformat(sent_at_start_str) if sent_at_start_str else None
    end = date.fromisoformat(sent_at_end_str) if sent_at_end_str else None

    try:
        records, total = get_mail_history_list(
            organization_id=organization_id,
            mail_types=params.get('mail_types', []),
            keyword=params.get('keyword', ''),
            sent_at_start=start,
            sent_at_end=end,
            sort_column=sort_column,
            order=order,
            page=page,
            per_page=DEFAULT_PER_PAGE,
        )
        logger.info('メール通知履歴一覧取得成功', extra={'total': total, 'page': page})
    except Exception:
        logger.error('メール通知履歴一覧取得失敗')
        abort(500)

    # フォームに検索条件をセット（表示用）
    form.mail_type_ids.data = params.get('mail_types', [])
    form.keyword.data = params.get('keyword', '')
    form.sent_at_start.data = start
    form.sent_at_end.data = end

    ctx = _build_template_context(form, mail_type_list, records, total, page, sort_id, order, params)
    response = make_response(render_template('notice/mail_history/list.html', **ctx))
    set_search_conditions_cookie(response, 'mail_history', params)
    return response


@notice_bp.route('/notice/mail-history', methods=['POST'])
def mail_history_search():
    """メール通知履歴検索"""
    logger.info('メール通知履歴検索開始')
    organization_id = g.current_user.organization_id

    mail_type_list = get_mail_type_choices()
    form = _build_form(mail_type_list)

    if not form.validate_on_submit():
        logger.warning('フォームバリデーションエラー')
        ctx = _build_template_context(
            form, mail_type_list, [], 0, 1, DEFAULT_SORT_ID, DEFAULT_SORT_ORDER, {}
        )
        return make_response(
            render_template('notice/mail_history/list.html', **ctx), 422
        )

    # 検証済みのメール種別IDのみ許可（ホワイトリスト方式）
    valid_ids = {mt.mail_type_id for mt in mail_type_list}
    filtered_ids = [i for i in (form.mail_type_ids.data or []) if i in valid_ids]
    sent_at_start = form.sent_at_start.data
    sent_at_end = form.sent_at_end.data
    keyword = form.keyword.data or ''

    params = {
        'mail_types': filtered_ids,
        'keyword': keyword,
        'sent_at_start': sent_at_start.isoformat() if sent_at_start else None,
        'sent_at_end': sent_at_end.isoformat() if sent_at_end else None,
        'sort_id': DEFAULT_SORT_ID,
        'order': DEFAULT_SORT_ORDER,
        'page': 1,
    }

    sort_column, order = _resolve_sort(DEFAULT_SORT_ID, DEFAULT_SORT_ORDER)

    try:
        records, total = get_mail_history_list(
            organization_id=organization_id,
            mail_types=filtered_ids,
            keyword=keyword,
            sent_at_start=sent_at_start,
            sent_at_end=sent_at_end,
            sort_column=sort_column,
            order=order,
            page=1,
            per_page=DEFAULT_PER_PAGE,
        )
        logger.info('メール通知履歴検索成功', extra={'total': total})
    except Exception:
        logger.error('メール通知履歴検索失敗')
        abort(500)

    ctx = _build_template_context(
        form, mail_type_list, records, total, 1, DEFAULT_SORT_ID, order, params
    )
    response = make_response(render_template('notice/mail_history/list.html', **ctx))
    set_search_conditions_cookie(response, 'mail_history', params)
    return response


@notice_bp.route('/notice/mail-history/<mail_history_uuid>', methods=['GET'])
def mail_history_detail(mail_history_uuid: str):
    """メール通知履歴詳細（モーダルパーシャル）"""
    logger.info('メール通知履歴詳細表示開始', extra={'mail_history_uuid': mail_history_uuid})
    organization_id = g.current_user.organization_id

    try:
        mail_history = get_mail_history_detail(mail_history_uuid, organization_id)
    except Exception:
        logger.error('メール通知履歴詳細取得失敗', extra={'mail_history_uuid': mail_history_uuid})
        abort(500)

    if mail_history is None:
        logger.warning('メール通知履歴が見つかりません', extra={'mail_history_uuid': mail_history_uuid})
        abort(404)

    logger.info('メール通知履歴詳細取得成功', extra={'mail_history_id': mail_history.mail_history_id})

    # メール種別名を取得
    mail_type_record = get_mail_type_by_id(mail_history.mail_type)
    mail_type_name = mail_type_record.mail_type_name if mail_type_record else str(mail_history.mail_type)
    mail_type_badge_class = _MAIL_TYPE_BADGE_CLASS.get(mail_history.mail_type, 'info')

    # recipients JSON → カンマ区切り文字列に変換
    recipients_data = mail_history.recipients or {}
    if isinstance(recipients_data, dict):
        recipients_list = recipients_data.get('to', [])
    elif isinstance(recipients_data, list):
        recipients_list = recipients_data
    else:
        recipients_list = []
    recipients_str = ', '.join(str(r) for r in recipients_list)

    return render_template(
        'notice/mail_history/detail_modal.html',
        mail_history=mail_history,
        mail_type_name=mail_type_name,
        mail_type_badge_class=mail_type_badge_class,
        recipients_str=recipients_str,
    )
