import json
from datetime import datetime

from flask import abort, g, jsonify, redirect, render_template, url_for

from iot_app import db
from iot_app.common.logger import get_logger
from iot_app.forms.customer_dashboard.circle_chart import CircleChartGadgetForm
from iot_app.services.customer_dashboard.circle_chart import (
    create_circle_chart_gadget,
    fetch_circle_chart_data,
    format_circle_chart_data,
    get_column_definition,
    get_device_name,
    get_gadget_by_uuid,
)
from iot_app.services.customer_dashboard.common import (
    check_device_access,
    check_gadget_access,
    get_accessible_organizations,
    get_all_devices_in_scope,
    get_dashboard_by_id,
    get_dashboard_groups,
    get_dashboard_user_setting,
    get_measurement_items,
    get_organization_id_by_user,
    get_organizations,
)
from iot_app.views.analysis.customer_dashboard import customer_dashboard_bp  # noqa: E402

logger = get_logger(__name__)

# chart_config のスロットキー順
_SLOT_KEYS = ['item_id_1', 'item_id_2', 'item_id_3', 'item_id_4', 'item_id_5']


# ---------------------------------------------------------------------------
# ガジェットデータ取得（AJAX）
# ---------------------------------------------------------------------------

def handle_gadget_data(gadget_uuid):
    """円グラフガジェットデータ取得（AJAX）"""
    accessible_org_ids = get_accessible_organizations(get_organization_id_by_user(g.current_user.user_id))

    gadget = get_gadget_by_uuid(gadget_uuid)
    if not gadget:
        return jsonify({'error': '指定されたガジェットが見つかりません'}), 404

    if check_gadget_access(gadget_uuid, accessible_org_ids) is None:
        return jsonify({'error': 'アクセス権限がありません'}), 404

    try:
        data_source_config = json.loads(gadget.data_source_config or '{}')
        device_id = data_source_config.get('device_id')

        if device_id is None:
            setting = get_dashboard_user_setting(g.current_user.user_id)
            device_id = setting.device_id if setting else None

        device_name = get_device_name(device_id) if device_id is not None else None

        rows = fetch_circle_chart_data(device_id) if device_id is not None else []

        all_columns = get_column_definition()
        chart_config = json.loads(gadget.chart_config or '{}')
        item_map = {col.measurement_item_id: col for col in all_columns}
        columns = [
            {'silver_data_column_name': item_map[mid].silver_data_column_name,
             'display_name': item_map[mid].display_name}
            for slot_key in _SLOT_KEYS
            if (mid := chart_config.get(slot_key)) is not None and mid in item_map
        ]

        rows_as_dicts = [row if isinstance(row, dict) else dict(row._mapping) for row in rows] if rows else []
        chart_data = format_circle_chart_data(rows_as_dicts, columns)

        return jsonify({
            'gadget_uuid': gadget_uuid,
            'device_name': device_name,
            'chart_data': chart_data,
            'updated_at': datetime.now().strftime('%Y/%m/%d %H:%M:%S'),
        })

    except Exception as e:
        g.last_exception_type = type(e).__name__
        logger.error(f'円グラフデータ取得エラー: gadget_uuid={gadget_uuid}, error={str(e)}')
        return jsonify({'error': 'データの取得に失敗しました'}), 500


# ---------------------------------------------------------------------------
# ガジェット登録モーダル表示
# ---------------------------------------------------------------------------

def handle_gadget_create(gadget_type):
    """円グラフガジェット登録モーダル表示"""
    accessible_org_ids = get_accessible_organizations(get_organization_id_by_user(g.current_user.user_id))

    setting = get_dashboard_user_setting(g.current_user.user_id)
    if setting is None:
        abort(404)

    dashboard = get_dashboard_by_id(setting.dashboard_id)
    if dashboard is None:
        abort(404)

    try:
        groups = get_dashboard_groups(dashboard.dashboard_id)
        measurement_items = get_measurement_items()
        organizations = get_organizations(accessible_org_ids)
        devices = get_all_devices_in_scope(accessible_org_ids)
    except Exception as e:
        logger.error(f'円グラフ登録モーダル表示エラー: {str(e)}')
        abort(500)

    form = CircleChartGadgetForm()
    form.measurement_item_ids.choices = [
        (item.measurement_item_id, item.display_name) for item in measurement_items
    ]
    if groups:
        form.group_id.data = groups[0].dashboard_group_id

    return render_template(
        'analysis/customer_dashboard/gadgets/modals/circle_chart.html',
        form=form,
        gadget_type=gadget_type,
        groups=groups,
        measurement_items=measurement_items,
        organizations=organizations,
        devices=devices,
    )


# ---------------------------------------------------------------------------
# ガジェット登録実行
# ---------------------------------------------------------------------------

def handle_gadget_register(gadget_type):
    """円グラフガジェット登録実行"""
    accessible_org_ids = get_accessible_organizations(get_organization_id_by_user(g.current_user.user_id))

    form = CircleChartGadgetForm()
    # measurement_item_ids はJS動的ロードのため送信値をchoicesに設定
    # 未選択時も sentinel [(-1, '')] を設定してバリデーターを必ず実行させる
    submitted_item_ids = [int(v) for v in (form.measurement_item_ids.raw_data or []) if v.isdigit()]
    form.measurement_item_ids.choices = [(mid, '') for mid in submitted_item_ids] if submitted_item_ids else [(-1, '')]

    if not form.validate_on_submit():
        measurement_items = get_measurement_items()
        setting = get_dashboard_user_setting(g.current_user.user_id)
        groups = get_dashboard_groups(setting.dashboard_id) if setting else []
        organizations = get_organizations(accessible_org_ids)
        devices = get_all_devices_in_scope(accessible_org_ids)
        return render_template(
            'analysis/customer_dashboard/gadgets/modals/circle_chart.html',
            form=form,
            gadget_type=gadget_type,
            groups=groups,
            measurement_items=measurement_items,
            organizations=organizations,
            devices=devices,
        ), 400

    device_id = None
    if form.device_mode.data == 'fixed':
        if check_device_access(form.device_id.data, accessible_org_ids) is None:
            abort(404)
        device_id = form.device_id.data

    item_ids = form.measurement_item_ids.data or []
    chart_config = {}
    for i, mid in enumerate(item_ids[:5], start=1):
        chart_config[f'item_id_{i}'] = mid

    data_source_config = {'device_id': device_id}

    try:
        create_circle_chart_gadget(
            gadget_name=form.gadget_name.data,
            dashboard_group_id=form.group_id.data,
            chart_config=chart_config,
            data_source_config=data_source_config,
            user_id=g.current_user.user_id,
        )
        return redirect(url_for('customer_dashboard.customer_dashboard', registered=1))

    except Exception as e:
        logger.error(f'円グラフガジェット登録エラー: {str(e)}')
        abort(500)
