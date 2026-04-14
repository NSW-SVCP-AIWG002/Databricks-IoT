"""
顧客作成ダッシュボード 帯グラフガジェット ビュー

参照設計書:
  - docs/03-features/flask-app/customer-dashboard/belt-chart/workflow-specification.md
  - docs/03-features/flask-app/customer-dashboard/belt-chart/ui-specification.md
"""

import json
from datetime import datetime

from flask import Response, abort, g, jsonify, redirect, render_template, request, url_for

from iot_app.common.exceptions import NotFoundError
from iot_app.common.logger import get_logger
from iot_app.forms.customer_dashboard.belt_chart import BeltChartGadgetForm
from iot_app.services.customer_dashboard.bar_chart import get_device_name_by_id
from iot_app.services.customer_dashboard.belt_chart import (
    fetch_belt_chart_data,
    format_belt_chart_data,
    generate_belt_chart_csv,
    get_aggregation_methods,
    register_belt_chart_gadget,
    validate_chart_params,
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
from iot_app.common.messages import ERR_INVALID_PARAMETER, err_fetch_failed, err_not_found, msg_created
from iot_app.views.analysis.customer_dashboard import customer_dashboard_bp  # noqa: E402

logger = get_logger(__name__)


def _build_measurement_items_for_data(measurement_item_ids):
    """measurement_item_ids からデータ整形用の項目リストを構築する"""
    all_items = get_measurement_items()
    id_to_item = {item.measurement_item_id: item for item in all_items}
    return [
        {
            'measurement_item_id': mid,
            'silver_data_column_name': id_to_item[mid].silver_data_column_name,
            'display_name': id_to_item[mid].display_name,
        }
        for mid in measurement_item_ids
        if mid in id_to_item
    ]


# ============================================================
# ガジェットデータ取得（AJAX）
# ============================================================

def handle_gadget_data(gadget_uuid):
    """帯グラフガジェットデータ取得（AJAX）"""
    accessible_org_ids = get_accessible_organizations(get_organization_id_by_user(g.current_user.user_id))
    gadget = check_gadget_access(gadget_uuid, accessible_org_ids)
    if gadget is None:
        return jsonify({'error': err_not_found('ガジェット')}), 404

    params = request.get_json() or {}
    display_unit = params.get('display_unit', 'hour')
    interval = params.get('interval', '10min')
    base_datetime_str = params.get('base_datetime')

    if not validate_chart_params(display_unit, interval, base_datetime_str):
        return jsonify({'error': ERR_INVALID_PARAMETER}), 400

    try:
        base_datetime = datetime.strptime(base_datetime_str, '%Y/%m/%d %H:%M:%S')
        data_source_config = json.loads(gadget.data_source_config or '{}')
        device_id = data_source_config.get('device_id')
        if device_id is None:
            setting = get_dashboard_user_setting(g.current_user.user_id)
            device_id = setting.device_id if setting else None

        chart_config = json.loads(gadget.chart_config or '{}')
        measurement_item_ids = chart_config.get('measurement_item_ids') or []
        summary_method_id = chart_config.get('summary_method_id', 1)

        measurement_items = _build_measurement_items_for_data(measurement_item_ids)

        rows = fetch_belt_chart_data(
            device_id=device_id,
            display_unit=display_unit,
            interval=interval,
            base_datetime=base_datetime,
            measurement_item_ids=measurement_item_ids,
            summary_method_id=summary_method_id,
            limit=100,
        )
        chart_data = format_belt_chart_data(rows, display_unit, measurement_items, interval, summary_method_id)
        device_name = get_device_name_by_id(device_id)

        return jsonify({
            'gadget_uuid': gadget_uuid,
            'device_name': device_name,
            'chart_data': chart_data,
            'updated_at': datetime.now().strftime('%Y/%m/%d %H:%M:%S'),
        })

    except Exception as e:
        g.last_exception_type = type(e).__name__
        logger.error(f'帯グラフデータ取得エラー: gadget_uuid={gadget_uuid}, error={str(e)}', exc_info=True)
        return jsonify({'error': err_fetch_failed('データ')}), 500


# ============================================================
# ガジェット登録モーダル表示
# ============================================================

def handle_gadget_create(gadget_type):
    """帯グラフガジェット登録モーダル表示"""
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
        summary_methods = get_aggregation_methods()
    except Exception as e:
        logger.error(f'帯グラフ登録モーダル表示エラー: {str(e)}')
        abort(500)

    form = BeltChartGadgetForm()
    form.measurement_item_ids.choices = [
        (item.measurement_item_id, item.display_name) for item in measurement_items
    ]
    form.gadget_name.data = '帯グラフ'
    if groups:
        form.group_id.data = groups[0].dashboard_group_id
    if summary_methods:
        form.summary_method_id.data = summary_methods[0].summary_method_id

    return render_template(
        'analysis/customer_dashboard/gadgets/modals/belt_chart.html',
        form=form,
        gadget_type=gadget_type,
        groups=groups,
        measurement_items=measurement_items,
        organizations=organizations,
        devices=devices,
        summary_methods=summary_methods,
    )


# ============================================================
# ガジェット登録実行
# ============================================================

def handle_gadget_register(gadget_type):
    """帯グラフガジェット登録実行"""
    accessible_org_ids = get_accessible_organizations(get_organization_id_by_user(g.current_user.user_id))

    form = BeltChartGadgetForm()
    # measurement_item_ids はJS動的ロードのため送信値をchoicesに設定
    # 未選択時も sentinel [(-1, '')] を設定してバリデーターを必ず実行させる
    submitted_item_ids = [int(v) for v in (form.measurement_item_ids.raw_data or []) if v.isdigit()]
    form.measurement_item_ids.choices = [(mid, '') for mid in submitted_item_ids] if submitted_item_ids else [(-1, '')]

    if not form.validate_on_submit():
        measurement_items = get_measurement_items()
        summary_methods = get_aggregation_methods()
        setting = get_dashboard_user_setting(g.current_user.user_id)
        groups = get_dashboard_groups(setting.dashboard_id) if setting else []
        organizations = get_organizations(accessible_org_ids)
        devices = get_all_devices_in_scope(accessible_org_ids)
        return render_template(
            'analysis/customer_dashboard/gadgets/modals/belt_chart.html',
            form=form,
            gadget_type=gadget_type,
            groups=groups,
            measurement_items=measurement_items,
            organizations=organizations,
            devices=devices,
            summary_methods=summary_methods,
        ), 400

    if form.device_mode.data == 'fixed':
        if check_device_access(form.device_id.data, accessible_org_ids) is None:
            abort(404)

    form_data = {
        'title': form.gadget_name.data,
        'device_mode': form.device_mode.data,
        'device_id': form.device_id.data,
        'group_id': form.group_id.data,
        'summary_method_id': form.summary_method_id.data,
        'measurement_item_ids': form.measurement_item_ids.data,
        'gadget_size': form.gadget_size.data,
    }

    try:
        register_belt_chart_gadget(form_data, g.current_user.user_id, accessible_org_ids)
        return jsonify({'message': msg_created('ガジェット')})
    except NotFoundError:
        abort(404)
    except Exception as e:
        logger.error(f'帯グラフガジェット登録エラー: {str(e)}', exc_info=True)
        abort(500)


# ============================================================
# CSVエクスポート
# ============================================================

def handle_gadget_csv_export(gadget_uuid):
    """帯グラフガジェット CSVエクスポート"""
    if request.args.get('export') != 'csv':
        abort(404)

    accessible_org_ids = get_accessible_organizations(get_organization_id_by_user(g.current_user.user_id))
    gadget = check_gadget_access(gadget_uuid, accessible_org_ids)
    if gadget is None:
        abort(404)

    display_unit = request.args.get('display_unit', 'hour')
    interval = request.args.get('interval', '10min')
    base_datetime_str = request.args.get('base_datetime')

    if not validate_chart_params(display_unit, interval, base_datetime_str):
        abort(400)

    try:
        data_source_config = json.loads(gadget.data_source_config or '{}')
        device_id = data_source_config.get('device_id')
        if device_id is None:
            setting = get_dashboard_user_setting(g.current_user.user_id)
            device_id = setting.device_id if setting else None

        chart_config = json.loads(gadget.chart_config or '{}')
        measurement_item_ids = chart_config.get('measurement_item_ids') or []
        summary_method_id = chart_config.get('summary_method_id', 1)
        base_datetime = datetime.strptime(base_datetime_str, '%Y/%m/%d %H:%M:%S')

        measurement_items = _build_measurement_items_for_data(measurement_item_ids)

        rows = fetch_belt_chart_data(
            device_id=device_id,
            display_unit=display_unit,
            interval=interval,
            base_datetime=base_datetime,
            measurement_item_ids=measurement_item_ids,
            summary_method_id=summary_method_id,
            limit=100_000,
        )
        chart_data = format_belt_chart_data(rows, display_unit, measurement_items, interval, summary_method_id)
        device_name = get_device_name_by_id(device_id)

        csv_content = generate_belt_chart_csv(
            chart_data, display_unit, base_datetime.isoformat(), device_name or ''
        )

        filename = f"sensor_data_{datetime.now().strftime('%Y%m%d%H%M%S')}.csv"
        return Response(
            csv_content,
            mimetype='text/csv',
            headers={'Content-Disposition': f'attachment; filename={filename}'},
        )

    except Exception as e:
        logger.error(f'帯グラフCSVエクスポートエラー: gadget_uuid={gadget_uuid}, error={str(e)}', exc_info=True)
        abort(500)
