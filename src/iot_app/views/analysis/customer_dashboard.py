"""
顧客作成ダッシュボード ビュー

参照設計書:
  - docs/03-features/flask-app/customer-dashboard/timeline/workflow-specification.md
  - docs/03-features/flask-app/customer-dashboard/timeline/ui-specification.md
"""

import io
import json
from datetime import datetime

from flask import Blueprint, Response, abort, g, jsonify, redirect, render_template, request, url_for

from iot_app import db
from iot_app.common.logger import get_logger
from iot_app.forms.customer_dashboard import TimelineGadgetForm
from iot_app.models.dashboard import DashboardGadgetMaster, DashboardGroupMaster, DashboardMaster, GadgetTypeMaster
from iot_app.services.customer_dashboard.timeline_service import (
    export_timeline_csv,
    fetch_timeline_data,
    format_timeline_data,
    generate_timeline_csv,
    register_gadget,
    validate_chart_params,
)

logger = get_logger(__name__)

customer_dashboard_bp = Blueprint(
    'customer_dashboard',
    __name__,
    url_prefix='/analysis',
)

_DATETIME_FORMAT = '%Y/%m/%d %H:%M:%S'


# ---------------------------------------------------------------------------
# ヘルパー
# ---------------------------------------------------------------------------

def _get_accessible_org_ids():
    """アクセス可能な組織IDリストを返す（organization_closure 経由）"""
    from iot_app.models.organization import OrganizationClosure
    rows = db.session.query(
        OrganizationClosure.subsidiary_organization_id
    ).filter(
        OrganizationClosure.parent_organization_id == g.current_user.organization_id
    ).all()
    return [r[0] for r in rows]


def _check_gadget_access(gadget_uuid, accessible_org_ids):
    """ガジェットがアクセス可能な組織に属するか確認する

    DashboardGadgetMaster → DashboardGroupMaster → DashboardMaster → organization_id の
    経路でスコープチェックを行う。

    Returns:
        DashboardGadgetMaster | None: アクセス可能なガジェット、または None
    """
    return db.session.query(DashboardGadgetMaster).join(
        DashboardGroupMaster,
        DashboardGadgetMaster.dashboard_group_id == DashboardGroupMaster.dashboard_group_id,
    ).join(
        DashboardMaster,
        DashboardGroupMaster.dashboard_id == DashboardMaster.dashboard_id,
    ).filter(
        DashboardGadgetMaster.gadget_uuid == gadget_uuid,
        DashboardGadgetMaster.delete_flag == False,
        DashboardGroupMaster.delete_flag == False,
        DashboardMaster.delete_flag == False,
        DashboardMaster.organization_id.in_(accessible_org_ids),
    ).first()


# ---------------------------------------------------------------------------
# 1. 顧客作成ダッシュボード初期表示
# GET /analysis/customer-dashboard
# ---------------------------------------------------------------------------

@customer_dashboard_bp.route('/customer-dashboard', methods=['GET'])
def customer_dashboard():
    """顧客作成ダッシュボード画面 初期表示"""
    gadgets = db.session.query(DashboardGadgetMaster).filter_by(
        delete_flag=False
    ).order_by(DashboardGadgetMaster.display_order.asc()).all()

    return render_template(
        'analysis/customer_dashboard/index.html',
        gadgets=gadgets,
    )


# ---------------------------------------------------------------------------
# 2. ガジェットデータ取得 (AJAX)
# POST /analysis/customer-dashboard/gadgets/<gadget_uuid>/data
# ---------------------------------------------------------------------------

@customer_dashboard_bp.route(
    '/customer-dashboard/gadgets/<string:gadget_uuid>/data',
    methods=['POST'],
)
def gadget_timeline_data(gadget_uuid):
    """時系列グラフガジェット データ取得（AJAX）"""
    accessible_org_ids = _get_accessible_org_ids()
    gadget = _check_gadget_access(gadget_uuid, accessible_org_ids)
    if gadget is None:
        return jsonify({'error': '指定されたガジェットが見つかりません'}), 404

    params = request.get_json() or {}
    start_datetime_str = params.get('start_datetime')
    end_datetime_str   = params.get('end_datetime')

    if not validate_chart_params(start_datetime_str, end_datetime_str):
        return jsonify({'error': 'パラメータが不正です'}), 400

    try:
        start_datetime = datetime.strptime(start_datetime_str, _DATETIME_FORMAT)
        end_datetime   = datetime.strptime(end_datetime_str,   _DATETIME_FORMAT)
        current_user_id = getattr(getattr(g, 'current_user', None), 'user_id', None)
        rows = fetch_timeline_data(
            gadget_uuid=gadget_uuid,
            start_datetime=start_datetime,
            end_datetime=end_datetime,
            current_user_id=current_user_id,
        )
        chart_config = json.loads(gadget.chart_config)
        from iot_app.models.measurement import MeasurementItem
        left_item  = db.session.get(MeasurementItem, chart_config['left_item_id'])
        right_item = db.session.get(MeasurementItem, chart_config['right_item_id'])
        chart_data = format_timeline_data(
            rows,
            left_item.silver_data_column_name,
            right_item.silver_data_column_name,
        )
        return jsonify({
            'gadget_uuid': gadget_uuid,
            'chart_data':  chart_data,
            'updated_at':  datetime.now().strftime(_DATETIME_FORMAT),
        })
    except Exception as e:
        logger.error(f'時系列グラフデータ取得エラー: gadget_uuid={gadget_uuid}', exc_info=True)
        return jsonify({'error': 'データの取得に失敗しました'}), 500


# ---------------------------------------------------------------------------
# 3. ガジェット登録モーダル表示
# GET /analysis/customer-dashboard/gadgets/timeline/create
# ---------------------------------------------------------------------------

@customer_dashboard_bp.route(
    '/customer-dashboard/gadgets/timeline/create',
    methods=['GET'],
)
def gadget_timeline_create():
    """時系列グラフガジェット 登録モーダル表示"""
    from iot_app.models.measurement import MeasurementItem
    from iot_app.models.organization import OrganizationMaster
    from iot_app.models.device import DeviceMaster
    accessible_org_ids = _get_accessible_org_ids()
    measurement_items = db.session.query(MeasurementItem).filter_by(
        delete_flag=False
    ).order_by(MeasurementItem.measurement_item_id.asc()).all()
    organizations = db.session.query(OrganizationMaster).filter(
        OrganizationMaster.organization_id.in_(accessible_org_ids),
        OrganizationMaster.delete_flag == False,
    ).order_by(OrganizationMaster.organization_id.asc()).all()
    devices = db.session.query(DeviceMaster).filter(
        DeviceMaster.organization_id.in_(accessible_org_ids),
        DeviceMaster.delete_flag == False,
    ).order_by(DeviceMaster.device_id.asc()).all()
    groups = db.session.query(DashboardGroupMaster).join(
        DashboardMaster,
        DashboardGroupMaster.dashboard_id == DashboardMaster.dashboard_id,
    ).filter(
        DashboardGroupMaster.delete_flag == False,
        DashboardMaster.delete_flag == False,
        DashboardMaster.organization_id.in_(accessible_org_ids),
    ).order_by(DashboardGroupMaster.display_order.asc()).all()

    form = TimelineGadgetForm()
    return render_template(
        'analysis/customer_dashboard/modals/gadget_register/timeline.html',
        form=form,
        measurement_items=measurement_items,
        organizations=organizations,
        devices=devices,
        groups=groups,
    )


# ---------------------------------------------------------------------------
# 4. ガジェット登録実行
# POST /analysis/customer-dashboard/gadgets/timeline/register
# ---------------------------------------------------------------------------

@customer_dashboard_bp.route(
    '/customer-dashboard/gadgets/timeline/register',
    methods=['POST'],
)
def gadget_timeline_register():
    """時系列グラフガジェット 登録実行"""
    form = TimelineGadgetForm()

    if not form.validate_on_submit():
        return render_template(
            'analysis/customer_dashboard/modals/gadget_register/timeline.html',
            form=form,
        ), 400

    current_user_id = getattr(getattr(g, 'current_user', None), 'user_id', 0)

    params = {
        'title':           form.title.data,
        'device_mode':     form.device_mode.data,
        'device_id':       form.device_id.data,
        'group_id':        form.group_id.data,
        'left_item_id':    form.left_item_id.data,
        'right_item_id':   form.right_item_id.data,
        'left_min_value':  form.left_min_value.data,
        'left_max_value':  form.left_max_value.data,
        'right_min_value': form.right_min_value.data,
        'right_max_value': form.right_max_value.data,
        'gadget_size':     form.gadget_size.data,
    }

    from iot_app.common.exceptions import ValidationError as AppValidationError

    try:
        register_gadget(params, current_user_id=current_user_id)
        logger.info(f'時系列グラフガジェット登録成功: user_id={current_user_id}')
        return redirect(url_for('customer_dashboard.customer_dashboard'))

    except AppValidationError as e:
        db.session.rollback()
        logger.warning(f'時系列グラフガジェット登録バリデーションエラー: {str(e)}')
        abort(400)

    except Exception as e:
        db.session.rollback()
        logger.error(f'時系列グラフガジェット登録エラー: {str(e)}', exc_info=True)
        abort(500)


# ---------------------------------------------------------------------------
# 5. CSVエクスポート
# GET /analysis/customer-dashboard/gadgets/<gadget_uuid>?export=csv
# ---------------------------------------------------------------------------

@customer_dashboard_bp.route(
    '/customer-dashboard/gadgets/<string:gadget_uuid>',
    methods=['GET'],
)
def gadget_csv_export(gadget_uuid):
    """時系列グラフガジェット CSVエクスポート"""
    from iot_app.common.exceptions import ValidationError, NotFoundError

    if request.args.get('export') != 'csv':
        abort(404)

    accessible_org_ids = _get_accessible_org_ids()
    if _check_gadget_access(gadget_uuid, accessible_org_ids) is None:
        abort(404)

    start_datetime_str = request.args.get('start_datetime')
    end_datetime_str   = request.args.get('end_datetime')
    current_user_id    = getattr(getattr(g, 'current_user', None), 'user_id', None)

    try:
        csv_content = export_timeline_csv(
            gadget_uuid=gadget_uuid,
            start_datetime=start_datetime_str,
            end_datetime=end_datetime_str,
            current_user_id=current_user_id,
        )

        filename = f"sensor_data_{datetime.now().strftime('%Y%m%d%H%M%S')}.csv"
        return Response(
            csv_content.encode('utf-8'),
            mimetype='text/csv; charset=utf-8',
            headers={'Content-Disposition': f'attachment; filename={filename}'},
        )

    except ValidationError as e:
        logger.warning(f'時系列グラフCSVエクスポート バリデーションエラー: {str(e)}')
        abort(400)

    except NotFoundError:
        abort(404)

    except Exception:
        logger.error(f'時系列グラフCSVエクスポートエラー: gadget_uuid={gadget_uuid}', exc_info=True)
        abort(500)
