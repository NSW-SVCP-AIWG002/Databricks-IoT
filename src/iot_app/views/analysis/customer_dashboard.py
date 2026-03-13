import json
from datetime import datetime

from flask import Blueprint, Response, abort, g, jsonify, redirect, render_template, request, url_for

from iot_app.common.exceptions import NotFoundError, ValidationError
from iot_app.common.logger import get_logger
from iot_app.forms.customer_dashboard import BarChartGadgetForm
from iot_app.services.customer_dashboard.bar_chart_service import (
    check_device_access,
    fetch_bar_chart_data,
    format_bar_chart_data,
    generate_bar_chart_csv,
    get_accessible_org_ids,
    get_all_active_gadgets,
    get_bar_chart_create_context,
    get_gadget_by_uuid,
    get_measurement_item_column_name,
    register_bar_chart_gadget,
    validate_chart_params,
)

logger = get_logger(__name__)

customer_dashboard_bp = Blueprint(
    'customer_dashboard',
    __name__,
    url_prefix='/analysis/customer-dashboard',
)


# ============================================================
# ルート定義
# ============================================================

@customer_dashboard_bp.route('', methods=['GET'])
def customer_dashboard():
    """顧客作成ダッシュボード初期表示"""
    gadgets = get_all_active_gadgets()
    return render_template(
        'analysis/customer_dashboard/index.html',
        gadgets=gadgets,
    )


@customer_dashboard_bp.route('/gadgets/<string:gadget_uuid>/data', methods=['POST'])
def gadget_bar_chart_data(gadget_uuid):
    """棒グラフガジェットデータ取得（AJAX）"""
    gadget = get_gadget_by_uuid(gadget_uuid)
    if not gadget:
        return jsonify({'error': '指定されたガジェットが見つかりません'}), 404

    params = request.get_json() or {}
    display_unit = params.get('display_unit', 'hour')
    interval = params.get('interval', '10min')
    base_datetime_str = params.get('base_datetime')

    if not validate_chart_params(display_unit, interval, base_datetime_str):
        return jsonify({'error': 'パラメータが不正です'}), 400

    try:
        base_datetime = datetime.strptime(base_datetime_str, '%Y/%m/%d %H:%M:%S')
        data_source_config = json.loads(gadget.data_source_config or '{}')
        device_id = data_source_config.get('device_id')

        chart_config = json.loads(gadget.chart_config or '{}')
        measurement_item_id = chart_config.get('measurement_item_id', 1)
        summary_method_id = chart_config.get('summary_method_id', 1)

        # display_unit=hour の場合はシルバー層カラム名を事前取得
        column_name = None
        if display_unit == 'hour':
            column_name = get_measurement_item_column_name(measurement_item_id)
            if column_name is None:
                return jsonify({'error': '測定項目が見つかりません'}), 500

        rows = fetch_bar_chart_data(
            device_id=device_id,
            display_unit=display_unit,
            interval=interval,
            base_datetime=base_datetime,
            measurement_item_id=measurement_item_id,
            summary_method_id=summary_method_id,
            limit=100,
        )
        chart_data = format_bar_chart_data(
            rows, display_unit, interval, summary_method_id, column_name=column_name
        )
        return jsonify({
            'gadget_uuid': gadget_uuid,
            'chart_data': chart_data,
            'updated_at': datetime.now().strftime('%Y/%m/%d %H:%M:%S'),
        })

    except Exception as e:
        logger.error(f'棒グラフデータ取得エラー: gadget_uuid={gadget_uuid}, error={str(e)}')
        return jsonify({'error': 'データの取得に失敗しました'}), 500


@customer_dashboard_bp.route('/gadgets/bar-chart/create', methods=['GET'])
def gadget_bar_chart_create():
    """棒グラフガジェット登録モーダル表示"""
    try:
        context = get_bar_chart_create_context()
    except Exception as e:
        logger.error(f'棒グラフ登録モーダル表示エラー: {str(e)}')
        abort(500)

    form = BarChartGadgetForm()
    form.device_id.choices = [(0, '選択してください')] + [
        (d.device_id, d.device_name) for d in context['devices']
    ]
    form.group_id.choices = [(0, '選択してください')]
    form.summary_method_id.choices = [(0, '選択してください')]
    form.measurement_item_id.choices = [(0, '選択してください')] + [
        (m.measurement_item_id, m.display_name) for m in context['measurement_items']
    ]

    return render_template(
        'analysis/customer_dashboard/modals/gadget_register/bar_chart.html',
        form=form,
        **context,
    )


@customer_dashboard_bp.route('/gadgets/bar-chart/register', methods=['POST'])
def gadget_bar_chart_register():
    """棒グラフガジェット登録実行"""
    try:
        context = get_bar_chart_create_context()
    except Exception as e:
        logger.error(f'棒グラフガジェット登録コンテキスト取得エラー: {str(e)}')
        abort(500)

    form = BarChartGadgetForm()
    form.device_id.choices = [(0, '選択してください')] + [
        (d.device_id, d.device_name) for d in context['devices']
    ]
    form.measurement_item_id.choices = [(0, '選択してください')] + [
        (m.measurement_item_id, m.display_name) for m in context['measurement_items']
    ]
    # group_id / summary_method_id はJS動的ロードのため送信値をそのまま choices に設定
    submitted_group_id = request.form.get('group_id', type=int) or 0
    submitted_summary_method_id = request.form.get('summary_method_id', type=int) or 0
    form.group_id.choices = [(submitted_group_id, '')]
    form.summary_method_id.choices = [(submitted_summary_method_id, '')]

    if not form.validate_on_submit():
        return render_template(
            'analysis/customer_dashboard/modals/gadget_register/bar_chart.html',
            form=form,
            **context,
        ), 422

    accessible_org_ids = get_accessible_org_ids(getattr(g, 'current_user_organization_id', None))

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
            current_user_id=getattr(g, 'current_user_id', None),
            accessible_org_ids=accessible_org_ids,
        )
        return redirect(url_for('customer_dashboard.customer_dashboard'))

    except ValidationError as e:
        return jsonify({'error': str(e)}), 400
    except NotFoundError as e:
        return jsonify({'error': str(e)}), 404
    except Exception as e:
        logger.error(f'棒グラフガジェット登録エラー: {str(e)}')
        abort(500)


@customer_dashboard_bp.route('/gadgets/<string:gadget_uuid>', methods=['GET'])
def gadget_csv_export(gadget_uuid):
    """棒グラフガジェット CSVエクスポート"""
    if request.args.get('export') != 'csv':
        abort(404)

    gadget = get_gadget_by_uuid(gadget_uuid)
    if not gadget:
        abort(404)

    display_unit = request.args.get('display_unit', 'hour')
    interval = request.args.get('interval', '10min')
    base_datetime_str = request.args.get('base_datetime')

    if not validate_chart_params(display_unit, interval, base_datetime_str):
        abort(400)

    try:
        data_source_config = json.loads(gadget.data_source_config or '{}')
        device_id = data_source_config.get('device_id')
        chart_config = json.loads(gadget.chart_config or '{}')
        measurement_item_id = chart_config.get('measurement_item_id', 1)
        summary_method_id = chart_config.get('summary_method_id', 1)

        base_datetime = datetime.strptime(base_datetime_str, '%Y/%m/%d %H:%M:%S')

        # display_unit=hour の場合はシルバー層カラム名を事前取得
        column_name = None
        if display_unit == 'hour':
            column_name = get_measurement_item_column_name(measurement_item_id)
            if column_name is None:
                abort(500)

        rows = fetch_bar_chart_data(
            device_id=device_id,
            display_unit=display_unit,
            interval=interval,
            base_datetime=base_datetime,
            measurement_item_id=measurement_item_id,
            summary_method_id=summary_method_id,
            limit=100_000,
        )
        chart_data = format_bar_chart_data(
            rows, display_unit, interval, summary_method_id, column_name=column_name
        )
        csv_content = generate_bar_chart_csv(chart_data)

        filename = f"sensor_data_{datetime.now().strftime('%Y%m%d%H%M%S')}.csv"
        return Response(
            csv_content,
            mimetype='text/csv',
            headers={'Content-Disposition': f'attachment; filename={filename}'},
        )

    except ValidationError:
        abort(400)
    except Exception as e:
        logger.error(f'棒グラフCSVエクスポートエラー: gadget_uuid={gadget_uuid}, error={str(e)}')
        abort(500)
