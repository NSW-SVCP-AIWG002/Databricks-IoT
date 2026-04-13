"""
顧客作成ダッシュボード 表ガジェット ビュー

参照設計書:
  - docs/03-features/flask-app/customer-dashboard/grid/workflow-specification.md
  - docs/03-features/flask-app/customer-dashboard/grid/ui-specification.md
"""

from datetime import datetime

from flask import Response, abort, g, jsonify, redirect, render_template, request, url_for

from iot_app.common.logger import get_logger
from iot_app.forms.customer_dashboard.grid import GridGadgetForm
from iot_app.services.customer_dashboard.common import (
    check_gadget_access,
    get_accessible_organizations,
    get_dashboard_by_id,
    get_dashboard_groups,
    get_dashboard_user_setting,
    get_organization_id_by_user,
)
from iot_app.services.customer_dashboard.grid import (
    PER_PAGE,
    calculate_page_offset,
    count_grid_data,
    fetch_grid_data,
    format_grid_data,
    generate_grid_csv,
    get_column_definition,
    get_grid_create_context,
    register_grid_gadget,
    validate_chart_params,
)
from iot_app.views.analysis.customer_dashboard import customer_dashboard_bp  # noqa: E402

logger = get_logger(__name__)


# ============================================================
# ガジェットデータ取得（AJAX）
# ============================================================

def handle_gadget_data(gadget_uuid):
    """表ガジェットデータ取得（AJAX）"""
    accessible_org_ids = get_accessible_organizations(get_organization_id_by_user(g.current_user.user_id))
    gadget = check_gadget_access(gadget_uuid, accessible_org_ids)
    if gadget is None:
        return jsonify({'error': '指定されたガジェットが見つかりません'}), 404

    params = request.get_json() or {}
    start_datetime_str = params.get('start_datetime')
    end_datetime_str = params.get('end_datetime')
    page = params.get('page', 1)

    if not validate_chart_params(start_datetime_str, end_datetime_str):
        return jsonify({'error': 'パラメータが不正です'}), 400

    try:
        start_datetime = datetime.strptime(start_datetime_str, '%Y/%m/%d %H:%M:%S')
        end_datetime = datetime.strptime(end_datetime_str, '%Y/%m/%d %H:%M:%S')

        user_setting = get_dashboard_user_setting(g.current_user.user_id)
        device_id = user_setting.device_id if user_setting else None

        offset = calculate_page_offset(page, per_page=PER_PAGE)

        rows = fetch_grid_data(
            device_id=device_id,
            start_datetime=start_datetime,
            end_datetime=end_datetime,
            limit=PER_PAGE,
            offset=offset,
        )

        columns = get_column_definition()
        grid_data = format_grid_data(rows, columns)

        total_count = count_grid_data(
            device_id=device_id,
            start_datetime=start_datetime,
            end_datetime=end_datetime,
        )

        return jsonify({
            'gadget_uuid': gadget_uuid,
            'columns': [
                {
                    'column_name': col.silver_data_column_name,
                    'display_name': col.display_name,
                }
                for col in columns
            ],
            'grid_data': grid_data,
            'total_count': total_count,
            'page': page,
            'per_page': PER_PAGE,
            'updated_at': datetime.now().strftime('%Y/%m/%d %H:%M:%S'),
        })

    except Exception as e:
        g.last_exception_type = type(e).__name__
        logger.error(f'表データ取得エラー: gadget_uuid={gadget_uuid}, error={str(e)}', exc_info=True)
        return jsonify({'error': 'データの取得に失敗しました'}), 500


# ============================================================
# 登録モーダル プレビューデータ取得（AJAX）
# ============================================================

def handle_gadget_preview():
    """表ガジェット登録モーダル用プレビューデータ取得（AJAX）"""
    params = request.get_json() or {}
    start_datetime_str = params.get('start_datetime')
    end_datetime_str = params.get('end_datetime')
    page = params.get('page', 1)

    if not validate_chart_params(start_datetime_str, end_datetime_str):
        return jsonify({'error': 'パラメータが不正です'}), 400

    try:
        start_datetime = datetime.strptime(start_datetime_str, '%Y/%m/%d %H:%M:%S')
        end_datetime = datetime.strptime(end_datetime_str, '%Y/%m/%d %H:%M:%S')

        user_setting = get_dashboard_user_setting(g.current_user.user_id)
        device_id = user_setting.device_id if user_setting else None

        offset = calculate_page_offset(page, per_page=PER_PAGE)

        rows = fetch_grid_data(
            device_id=device_id,
            start_datetime=start_datetime,
            end_datetime=end_datetime,
            limit=PER_PAGE,
            offset=offset,
        )

        columns = get_column_definition()
        grid_data = format_grid_data(rows, columns)

        total_count = count_grid_data(
            device_id=device_id,
            start_datetime=start_datetime,
            end_datetime=end_datetime,
        )

        return jsonify({
            'columns': [
                {
                    'column_name': col.silver_data_column_name,
                    'display_name': col.display_name,
                }
                for col in columns
            ],
            'grid_data': grid_data,
            'total_count': total_count,
            'page': page,
            'per_page': PER_PAGE,
        })

    except Exception as e:
        g.last_exception_type = type(e).__name__
        logger.error(f'表プレビューデータ取得エラー: error={str(e)}', exc_info=True)
        return jsonify({'error': 'データの取得に失敗しました'}), 500


# ============================================================
# ガジェット登録モーダル表示
# ============================================================

def handle_gadget_create(gadget_type):
    """表ガジェット登録モーダル表示"""
    setting = get_dashboard_user_setting(g.current_user.user_id)
    if setting is None:
        abort(404)

    dashboard = get_dashboard_by_id(setting.dashboard_id)
    if dashboard is None:
        abort(404)

    try:
        context = get_grid_create_context(dashboard.dashboard_id)
    except Exception as e:
        g.last_exception_type = type(e).__name__
        logger.error(f'表ガジェット登録モーダル表示エラー: {str(e)}')
        abort(500)

    form = GridGadgetForm()
    form.group_id.choices = [(0, '選択してください')] + [
        (gr.dashboard_group_id, gr.dashboard_group_name) for gr in context['groups']
    ]
    form.gadget_name.data = '表'

    return render_template(
        'analysis/customer_dashboard/gadgets/modals/grid.html',
        form=form,
        gadget_type=gadget_type,
        **context,
    )


# ============================================================
# ガジェット登録実行
# ============================================================

def handle_gadget_register(gadget_type):
    """表ガジェット登録実行"""
    logger.info(f'表ガジェット登録開始: user_id={g.current_user.user_id}')
    form = GridGadgetForm()

    submitted_group_id = request.form.get('group_id', type=int) or 0
    form.group_id.choices = [(submitted_group_id, '')]

    if not form.validate_on_submit():
        try:
            setting = get_dashboard_user_setting(g.current_user.user_id)
            dashboard = get_dashboard_by_id(setting.dashboard_id) if setting else None
            context = get_grid_create_context(dashboard.dashboard_id) if dashboard else {'groups': []}
        except Exception as e:
            g.last_exception_type = type(e).__name__
            logger.error(f'表ガジェット登録コンテキスト取得エラー: {str(e)}')
            abort(500)
        return render_template(
            'analysis/customer_dashboard/gadgets/modals/grid.html',
            form=form,
            gadget_type=gadget_type,
            **context,
        ), 400

    params = {
        'title': form.gadget_name.data,
        'group_id': form.group_id.data,
        'gadget_size': form.gadget_size.data,
    }

    try:
        register_grid_gadget(params=params, current_user_id=g.current_user.user_id)
        logger.info(f'表ガジェット登録成功: user_id={g.current_user.user_id}')
        return redirect(url_for('customer_dashboard.customer_dashboard', registered=1))
    except Exception as e:
        g.last_exception_type = type(e).__name__
        logger.error(f'表ガジェット登録エラー: {str(e)}', exc_info=True)
        abort(500)


# ============================================================
# CSVエクスポート
# ============================================================

def handle_gadget_csv_export(gadget_uuid):
    """表ガジェット CSVエクスポート"""
    if request.args.get('export') != 'csv':
        abort(404)

    accessible_org_ids = get_accessible_organizations(get_organization_id_by_user(g.current_user.user_id))
    gadget = check_gadget_access(gadget_uuid, accessible_org_ids)
    if gadget is None:
        abort(404)

    start_datetime_str = request.args.get('start_datetime')
    end_datetime_str = request.args.get('end_datetime')

    if not validate_chart_params(start_datetime_str, end_datetime_str):
        abort(400)

    try:
        start_datetime = datetime.strptime(start_datetime_str, '%Y/%m/%d %H:%M:%S')
        end_datetime = datetime.strptime(end_datetime_str, '%Y/%m/%d %H:%M:%S')

        user_setting = get_dashboard_user_setting(g.current_user.user_id)
        device_id = user_setting.device_id if user_setting else None

        rows = fetch_grid_data(
            device_id=device_id,
            start_datetime=start_datetime,
            end_datetime=end_datetime,
            limit=100_000,
            offset=0,
        )

        columns = get_column_definition()
        grid_data = format_grid_data(rows, columns)
        csv_content = generate_grid_csv(grid_data, columns)

        filename = f"sensor_data_{datetime.now().strftime('%Y%m%d%H%M%S')}.csv"
        return Response(
            csv_content,
            mimetype='text/csv',
            headers={'Content-Disposition': f'attachment; filename={filename}'},
        )

    except Exception as e:
        g.last_exception_type = type(e).__name__
        logger.error(f'表CSVエクスポートエラー: gadget_uuid={gadget_uuid}, error={str(e)}', exc_info=True)
        abort(500)
