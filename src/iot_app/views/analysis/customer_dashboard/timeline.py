"""
顧客作成ダッシュボード 時系列グラフ ビュー

参照設計書:
  - docs/03-features/flask-app/customer-dashboard/timeline/workflow-specification.md
  - docs/03-features/flask-app/customer-dashboard/timeline/ui-specification.md
"""

from datetime import datetime

from flask import Response, abort, g, jsonify, redirect, render_template, request, url_for

from iot_app import db
from iot_app.common.logger import get_logger
from iot_app.forms.customer_dashboard.timeline import TimelineGadgetForm
from iot_app.services.customer_dashboard.timeline import (
    check_device_in_scope,
    check_gadget_access,
    export_timeline_csv,
    fetch_timeline_data,
    format_timeline_data,
    get_accessible_org_ids,
    get_dashboard_user_setting,
    get_gadget_by_uuid,
    get_measurement_item,
    get_timeline_create_context,
    register_gadget,
    validate_chart_params,
)
from iot_app.services.customer_dashboard.common import get_organization_id_by_user

logger = get_logger(__name__)

_DATETIME_FORMAT = '%Y/%m/%d %H:%M:%S'


# ---------------------------------------------------------------------------
# 1. ガジェットデータ取得 (AJAX)
# POST /analysis/customer-dashboard/gadgets/<gadget_uuid>/data
# ---------------------------------------------------------------------------

def handle_gadget_data(gadget_uuid):
    """時系列グラフガジェット データ取得（AJAX）"""
    accessible_org_ids = get_accessible_org_ids(get_organization_id_by_user(g.current_user.user_id))

    # ① ガジェット設定取得
    gadget = get_gadget_by_uuid(gadget_uuid)
    if not gadget:
        return jsonify({'error': '指定されたガジェットが見つかりません'}), 404

    # データスコープ制限チェック
    if not check_gadget_access(gadget, accessible_org_ids):
        return jsonify({'error': 'アクセス権限がありません'}), 404

    params = request.get_json() or {}
    start_datetime_str = params.get('start_datetime')
    end_datetime_str   = params.get('end_datetime')

    if not validate_chart_params(start_datetime_str, end_datetime_str):
        return jsonify({'error': 'パラメータが不正です'}), 400

    try:
        start_datetime = datetime.strptime(start_datetime_str, _DATETIME_FORMAT)
        end_datetime   = datetime.strptime(end_datetime_str,   _DATETIME_FORMAT)

        # ② デバイスID決定
        import json as _json
        data_source_config = _json.loads(gadget.data_source_config or '{}')
        device_id = data_source_config.get('device_id')
        if not device_id:
            user_setting = get_dashboard_user_setting(g.current_user.user_id)
            device_id = user_setting.device_id if user_setting else None

        chart_config = _json.loads(gadget.chart_config or '{}')

        # ③ カラム名・表示情報取得
        left_item  = get_measurement_item(chart_config['left_item_id'])
        right_item = get_measurement_item(chart_config['right_item_id'])
        left_col   = left_item.silver_data_column_name
        right_col  = right_item.silver_data_column_name

        rows = fetch_timeline_data(
            device_id=device_id,
            start_datetime=start_datetime,
            end_datetime=end_datetime,
            left_item_id=chart_config['left_item_id'],
            right_item_id=chart_config['right_item_id'],
        )

        # ④ データ整形 + ラベル・単位・最小/最大値を補完 [A]
        chart_data = format_timeline_data(rows, left_col, right_col)
        chart_data.update({
            'left_label':  left_item.display_name  if left_item  else '左軸',
            'right_label': right_item.display_name if right_item else '右軸',
            'left_unit':   left_item.unit_name     if left_item  else '',
            'right_unit':  right_item.unit_name    if right_item else '',
            'left_min':    chart_config.get('left_min_value'),
            'left_max':    chart_config.get('left_max_value'),
            'right_min':   chart_config.get('right_min_value'),
            'right_max':   chart_config.get('right_max_value'),
        })

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

def handle_gadget_create(gadget_type):
    """時系列グラフガジェット 登録モーダル表示"""
    from iot_app.common.exceptions import NotFoundError
    accessible_org_ids = get_accessible_org_ids(get_organization_id_by_user(g.current_user.user_id))
    current_user_id = g.current_user.user_id

    try:
        context = get_timeline_create_context(accessible_org_ids, current_user_id)
    except NotFoundError:
        abort(404)
    except Exception:
        abort(500)

    form = TimelineGadgetForm()
    form.group_id.choices = [
        (grp.dashboard_group_id, grp.dashboard_group_name) for grp in context['groups']
    ]
    if context['groups']:
        form.group_id.data = context['groups'][0].dashboard_group_id

    return render_template(
        'analysis/customer_dashboard/gadgets/modals/timeline.html',
        form=form,
        gadget_type=gadget_type,
        **context,
    )


# ---------------------------------------------------------------------------
# 4. ガジェット登録実行
# POST /analysis/customer-dashboard/gadgets/timeline/register
# ---------------------------------------------------------------------------

def handle_gadget_register(gadget_type):
    """時系列グラフガジェット 登録実行"""
    form = TimelineGadgetForm()

    # group_id: 送信値の存在チェックのみ（必須選択）
    submitted_group_id = request.form.get('group_id', type=int) or 0
    form.group_id.choices = [(submitted_group_id, '')]

    if not form.validate_on_submit():
        # [D] 422時にフルコンテキストを渡す
        from iot_app.common.exceptions import NotFoundError
        accessible_org_ids = get_accessible_org_ids(get_organization_id_by_user(g.current_user.user_id))
        try:
            context = get_timeline_create_context(accessible_org_ids, g.current_user.user_id)
        except NotFoundError:
            abort(404)
        except Exception:
            abort(500)
        # グループ選択肢をフル選択肢に更新（検証用の1件だけでは再描画時に空になるため）
        form.group_id.choices = [
            (grp.dashboard_group_id, grp.dashboard_group_name) for grp in context['groups']
        ]
        return render_template(
            'analysis/customer_dashboard/gadgets/modals/timeline.html',
            form=form,
            gadget_type=gadget_type,
            **context,
        ), 422

    current_user_id = g.current_user.user_id

    # デバイス固定モード時: デバイス存在&データスコープチェック
    if form.device_mode.data == 'fixed':
        accessible_org_ids = get_accessible_org_ids(get_organization_id_by_user(g.current_user.user_id))
        if check_device_in_scope(form.device_id.data, accessible_org_ids) is None:
            abort(404)

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

def handle_gadget_csv_export(gadget_uuid):
    """時系列グラフガジェット CSVエクスポート"""
    from iot_app.common.exceptions import NotFoundError

    if request.args.get('export') != 'csv':
        abort(404)

    accessible_org_ids = get_accessible_org_ids(get_organization_id_by_user(g.current_user.user_id))
    gadget = get_gadget_by_uuid(gadget_uuid)
    if not gadget or not check_gadget_access(gadget, accessible_org_ids):
        abort(404)

    start_datetime_str = request.args.get('start_datetime')
    end_datetime_str   = request.args.get('end_datetime')

    if not validate_chart_params(start_datetime_str, end_datetime_str):
        abort(400)

    try:
        csv_content = export_timeline_csv(
            gadget_uuid=gadget_uuid,
            start_datetime=start_datetime_str,
            end_datetime=end_datetime_str,
            current_user_id=g.current_user.user_id,
        )

        filename = f"sensor_data_{datetime.now().strftime('%Y%m%d%H%M%S')}.csv"
        return Response(
            csv_content.encode('utf-8'),
            mimetype='text/csv; charset=utf-8',
            headers={'Content-Disposition': f'attachment; filename={filename}'},
        )

    except NotFoundError:
        abort(404)

    except Exception:
        logger.error(f'時系列グラフCSVエクスポートエラー: gadget_uuid={gadget_uuid}', exc_info=True)
        abort(500)
