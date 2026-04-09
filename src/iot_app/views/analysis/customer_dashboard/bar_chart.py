import json
from datetime import datetime

from flask import Response, abort, g, jsonify, redirect, render_template, request, url_for

from iot_app.common.exceptions import NotFoundError
from iot_app.common.logger import get_logger
from iot_app.forms.customer_dashboard.bar_chart import BarChartGadgetForm
from iot_app.services.customer_dashboard.bar_chart import (
    check_device_access,
    fetch_bar_chart_data,
    format_bar_chart_data,
    generate_bar_chart_csv,
    get_accessible_org_ids,
    get_bar_chart_create_context,
    get_dashboard_by_id,
    get_dashboard_groups,
    get_dashboard_user_setting,
    get_device_name_by_id,
    get_gadget_by_uuid,
    get_measurement_item_column_name,
    get_measurement_item_legend_name,
    register_bar_chart_gadget,
    validate_chart_params,
)
from iot_app.services.customer_dashboard.common import check_gadget_access, get_organization_id_by_user

logger = get_logger(__name__)

from iot_app.views.analysis.customer_dashboard import customer_dashboard_bp  # noqa: E402


# ============================================================
# ルート定義
# ============================================================

def handle_gadget_data(gadget_uuid):
    """棒グラフガジェットデータ取得（AJAX）"""
    gadget = get_gadget_by_uuid(gadget_uuid)
    if not gadget:
        return jsonify({'error': '指定されたガジェットが見つかりません'}), 404

    accessible_org_ids = get_accessible_org_ids(get_organization_id_by_user(g.current_user.user_id))
    if check_gadget_access(gadget_uuid, accessible_org_ids) is None:
        return jsonify({'error': 'アクセス権限がありません'}), 404

    params = request.get_json() or {}
    display_unit = params.get('display_unit', 'hour')
    interval = params.get('interval', '10min')
    base_datetime_str = params.get('base_datetime')

    error = validate_chart_params(display_unit, interval, base_datetime_str)
    if error:
        return jsonify({'error': error}), 400

    try:
        base_datetime = datetime.strptime(base_datetime_str, '%Y/%m/%d %H:%M:%S')
        data_source_config = json.loads(gadget.data_source_config or '{}')
        device_id = data_source_config.get('device_id')
        if device_id is None:
            setting = get_dashboard_user_setting(g.current_user.user_id)
            device_id = setting.device_id if setting else None
        chart_config = json.loads(gadget.chart_config or '{}')
        measurement_item_id = chart_config.get('measurement_item_id', 1)
        summary_method_id = chart_config.get('summary_method_id', 1)

        column_name = None
        if display_unit == 'hour':
            column_name = get_measurement_item_column_name(measurement_item_id)
            if column_name is None:
                return jsonify({'error': '測定項目が見つかりません'}), 500

        rows = fetch_bar_chart_data(
            device_id=device_id, display_unit=display_unit,
            interval=interval, base_datetime=base_datetime,
            measurement_item_id=measurement_item_id,
            summary_method_id=summary_method_id, limit=100,
        )
        chart_data = format_bar_chart_data(rows, display_unit, interval, summary_method_id, column_name=column_name)
        return jsonify({
            'gadget_uuid': gadget_uuid,
            'chart_data': chart_data,
            'updated_at': datetime.now().strftime('%Y/%m/%d %H:%M:%S'),
        })

    except Exception as e:
        g.last_exception_type = type(e).__name__
        logger.error(f'棒グラフデータ取得エラー: gadget_uuid={gadget_uuid}, error={str(e)}')
        return jsonify({'error': 'データの取得に失敗しました'}), 500


def handle_gadget_create(gadget_type):
    """棒グラフガジェット登録モーダル表示"""
    setting = get_dashboard_user_setting(g.current_user.user_id)
    if setting is None:
        abort(404)

    accessible_org_ids = get_accessible_org_ids(get_organization_id_by_user(g.current_user.user_id))
    dashboard = get_dashboard_by_id(setting.dashboard_id, accessible_org_ids)
    if dashboard is None:
        abort(404)

    groups = get_dashboard_groups(dashboard.dashboard_id)

    try:
        context = get_bar_chart_create_context(accessible_org_ids)
    except Exception as e:
        logger.error(f'棒グラフ登録モーダル表示エラー: {str(e)}')
        abort(500)

    form = BarChartGadgetForm()
    form.device_id.choices = [(0, '選択してください')] + [
        (d.device_id, d.device_name) for d in context['devices']
    ]
    form.group_id.choices = [(0, '選択してください')] + [
        (gr.dashboard_group_id, gr.dashboard_group_name) for gr in groups
    ]
    form.summary_method_id.choices = [(0, '選択してください')] + [
        (sm.summary_method_id, sm.summary_method_name) for sm in context['summary_methods']
    ]
    form.measurement_item_id.choices = [(0, '選択してください')] + [
        (m.measurement_item_id, m.display_name) for m in context['measurement_items']
    ]
    return render_template(
        'analysis/customer_dashboard/gadgets/modals/bar_chart.html',
        form=form,
        gadget_type=gadget_type,
        groups=groups,
        **context,
    )


def handle_gadget_register(gadget_type):
    """棒グラフガジェット登録実行"""
    accessible_org_ids = get_accessible_org_ids(get_organization_id_by_user(g.current_user.user_id))

    form = BarChartGadgetForm()
    # device_id / measurement_item_id / group_id / summary_method_id はJS動的ロードのため送信値をそのまま choices に設定
    submitted_device_id = request.form.get('device_id', type=int) or 0
    form.device_id.choices = [(submitted_device_id, '')]
    submitted_measurement_item_id = request.form.get('measurement_item_id', type=int) or 0
    form.measurement_item_id.choices = [(submitted_measurement_item_id, '')]
    submitted_group_id = request.form.get('group_id', type=int) or 0
    submitted_summary_method_id = request.form.get('summary_method_id', type=int) or 0
    form.group_id.choices = [(submitted_group_id, '')]
    form.summary_method_id.choices = [(submitted_summary_method_id, '')]

    if not form.validate_on_submit():
        try:
            context = get_bar_chart_create_context(accessible_org_ids)
            setting = get_dashboard_user_setting(g.current_user.user_id)
            groups = get_dashboard_groups(setting.dashboard_id) if setting else []
        except Exception as e:
            logger.error(f'棒グラフガジェット登録コンテキスト取得エラー: {str(e)}')
            abort(500)
        return render_template(
            'analysis/customer_dashboard/gadgets/modals/bar_chart.html',
            form=form,
            gadget_type=gadget_type,
            groups=groups,
            **context,
        ), 400

    # デバイス固定モード時: デバイス存在&データスコープチェック
    if form.device_mode.data == 'fixed':
        if check_device_access(form.device_id.data, accessible_org_ids) is None:
            abort(404)

    params = {
        'title': form.title.data,
        'device_mode': form.device_mode.data,
        'device_id': form.device_id.data,
        'group_id': form.group_id.data,
        'summary_method_id': form.summary_method_id.data,
        'measurement_item_id': form.measurement_item_id.data,
        'min_value': form.min_value.data,
        'max_value': form.max_value.data,
        'gadget_size': form.gadget_size.data,
    }

    try:
        register_bar_chart_gadget(
            params=params,
            current_user_id=g.current_user.user_id,
        )
        return redirect(url_for('customer_dashboard.customer_dashboard', registered=1))

    except NotFoundError:
        abort(404)
    except Exception as e:
        logger.error(f'棒グラフガジェット登録エラー: {str(e)}')
        abort(500)


def handle_gadget_csv_export(gadget_uuid):
    """棒グラフガジェット CSVエクスポート"""
    if request.args.get('export') != 'csv':
        abort(404)

    accessible_org_ids = get_accessible_org_ids(get_organization_id_by_user(g.current_user.user_id))

    gadget = get_gadget_by_uuid(gadget_uuid)
    if not gadget:
        abort(404)
    if check_gadget_access(gadget_uuid, accessible_org_ids) is None:
        abort(404)

    display_unit = request.args.get('display_unit', 'hour')
    interval = request.args.get('interval', '10min')
    base_datetime_str = request.args.get('base_datetime')

    if validate_chart_params(display_unit, interval, base_datetime_str):
        abort(400)

    try:
        data_source_config = json.loads(gadget.data_source_config or '{}')
        device_id = data_source_config.get('device_id')
        if device_id is None:
            setting = get_dashboard_user_setting(g.current_user.user_id)
            device_id = setting.device_id if setting else None
        chart_config = json.loads(gadget.chart_config or '{}')
        measurement_item_id = chart_config.get('measurement_item_id', 1)
        summary_method_id = chart_config.get('summary_method_id', 1)
        base_datetime = datetime.strptime(base_datetime_str, '%Y/%m/%d %H:%M:%S')

        column_name = None
        if display_unit == 'hour':
            column_name = get_measurement_item_column_name(measurement_item_id)
            if column_name is None:
                abort(500)

        rows = fetch_bar_chart_data(
            device_id=device_id, display_unit=display_unit, interval=interval,
            base_datetime=base_datetime, measurement_item_id=measurement_item_id,
            summary_method_id=summary_method_id, limit=100_000,
        )
        chart_data = format_bar_chart_data(rows, display_unit, interval, summary_method_id, column_name=column_name)
        device_name = get_device_name_by_id(device_id)
        legend_name = get_measurement_item_legend_name(measurement_item_id)
        csv_content = generate_bar_chart_csv(chart_data, display_unit, base_datetime, device_name, legend_name)

        filename = f"sensor_data_{datetime.now().strftime('%Y%m%d%H%M%S')}.csv"
        return Response(
            csv_content,
            mimetype='text/csv',
            headers={'Content-Disposition': f'attachment; filename={filename}'},
        )

    except Exception as e:
        logger.error(f'棒グラフCSVエクスポートエラー: gadget_uuid={gadget_uuid}, error={str(e)}')
        abort(500)
