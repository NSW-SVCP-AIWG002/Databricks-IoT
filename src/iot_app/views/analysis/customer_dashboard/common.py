from flask import abort, flash, g, jsonify, redirect, render_template, request, url_for

from iot_app import db
from iot_app.common.logger import get_logger
from iot_app.decorators.auth import require_auth
from iot_app.forms.customer_dashboard.common import DashboardForm, DashboardGroupForm, GadgetForm
from iot_app.models.customer_dashboard import DashboardGadgetMaster, DashboardGroupMaster, DashboardMaster

from iot_app.services.customer_dashboard.common import (
    check_dashboard_access,
    check_gadget_access,
    check_group_access,
    create_dashboard,
    create_dashboard_group,
    delete_dashboard_user_setting,
    delete_dashboard_with_cascade,
    delete_gadget,
    delete_group_with_cascade,
    get_accessible_organizations,
    get_dashboard_by_id,
    get_dashboard_groups,
    get_dashboard_update_date,
    get_dashboard_user_setting,
    get_dashboards,
    get_devices,
    get_devices_by_organization,
    get_fixed_gadget_device_names,
    get_first_dashboard,
    get_gadget_type,
    get_gadget_type_id_by_name,
    get_gadget_types,
    get_gadget_update_date,
    get_gadgets_by_groups,
    get_group_update_date,
    get_organization_id_by_user,
    get_organizations,
    save_layout,
    update_dashboard_title,
    update_datasource_setting,
    update_gadget_title,
    update_group_title,
    upsert_dashboard_user_setting,
)
from iot_app.views.analysis.customer_dashboard import customer_dashboard_bp

logger = get_logger(__name__)

# ============================================================
# ガジェット種別レジストリ
# ============================================================
# 新しいガジェット種別を追加する際はここにエントリを追加するだけでよい。
# 追加後、以下は自動的に反映される:
#   - ガジェット追加モーダルの URL スラグ生成
#   - 登録モーダル表示 / 登録実行 / データ取得 / CSV エクスポートのルーティング
#   - ダッシュボード画面での CSS・JS の読み込み
#   - ガジェット描画テンプレートの選択
#
# 各ガジェット JS ファイル末尾でも以下の呼び出しが必要:
#   CustomerDashboard.registerModalBinder(bind<GadgetName>GadgetRegister);
#
# NOTE: gadget_type_master に論理名カラムがないため暫定的にコードで管理
#       設計確認事項 No.14 参照（gadget_type_slug カラム追加で解消予定）
_GADGET_REGISTRY = {
    '棒グラフ': {
        'slug':     'bar-chart',
        'template': 'analysis/customer_dashboard/gadgets/bar_chart.html',
        'css':      'css/components/customer_dashboard/bar_chart.css',
        'js':       'js/components/customer_dashboard/bar_chart.js',
        'module':   'iot_app.views.analysis.customer_dashboard.bar_chart',
    },
    '時系列グラフ': {
        'slug':     'timeline',
        'template': 'analysis/customer_dashboard/gadgets/timeline.html',
        'css':      'css/components/customer_dashboard/timeline.css',
        'js':       'js/components/customer_dashboard/timeline.js',
        'module':   'iot_app.views.analysis.customer_dashboard.timeline',
    },
    '円グラフ': {
        'slug':     'circle-chart',
        'template': 'analysis/customer_dashboard/gadgets/circle_chart.html',
        'css':      'css/components/customer_dashboard/circle_chart.css',
        'js':       'js/components/customer_dashboard/circle_chart.js',
        'module':   'iot_app.views.analysis.customer_dashboard.circle_chart',
    },
    '帯グラフ': {
        'slug':     'belt-chart',
        'template': 'analysis/customer_dashboard/gadgets/belt_chart.html',
        'css':      'css/components/customer_dashboard/belt_chart.css',
        'js':       'js/components/customer_dashboard/belt_chart.js',
        'module':   'iot_app.views.analysis.customer_dashboard.belt_chart',
    },
    '表': {
        'slug':     'grid',
        'template': 'analysis/customer_dashboard/gadgets/grid.html',
        'css':      'css/components/customer_dashboard/grid.css',
        'js':       'js/components/customer_dashboard/grid.js',
        'module':   'iot_app.views.analysis.customer_dashboard.grid',
    },
}

# レジストリから派生（直接編集不要）
GADGET_TYPE_SLUG = {name: info['slug'] for name, info in _GADGET_REGISTRY.items()}
_SLUG_TO_NAME = {info['slug']: name for name, info in _GADGET_REGISTRY.items()}


def _get_handler(gadget_name, handler_attr):
    """ガジェット種別名からハンドラ関数を遅延インポートして返す"""
    import importlib
    info = _GADGET_REGISTRY.get(gadget_name)
    if info is None:
        return None
    mod = importlib.import_module(info['module'])
    return getattr(mod, handler_attr, None)


# ---------------------------------------------------------------------------
# No.1 顧客作成ダッシュボード初期表示
# ---------------------------------------------------------------------------

@customer_dashboard_bp.route('', methods=['GET'])
@require_auth
def customer_dashboard():
    """顧客作成ダッシュボード初期表示"""
    accessible_org_ids = get_accessible_organizations(get_organization_id_by_user(g.current_user.user_id))

    user_setting = get_dashboard_user_setting(g.current_user.user_id)

    if user_setting and user_setting.dashboard_id:
        dashboard_id = user_setting.dashboard_id
    else:
        first = get_first_dashboard(accessible_org_ids)
        dashboard_id = first.dashboard_id if first else None

    dashboards = get_dashboards(accessible_org_ids)
    organizations = get_organizations(accessible_org_ids)
    gadget_static_files = list(_GADGET_REGISTRY.values())
    gadget_id_to_template = {
        get_gadget_type_id_by_name(name): info['template']
        for name, info in _GADGET_REGISTRY.items()
    }
    gadget_type_ids = {
        name: get_gadget_type_id_by_name(name)
        for name in _GADGET_REGISTRY
    }

    if not dashboard_id:
        return render_template(
            'analysis/customer_dashboard/index.html',
            dashboards=[],
            dashboard=None,
            groups=[],
            gadgets=[],
            gadget_id_to_template=gadget_id_to_template,
            gadget_type_ids=gadget_type_ids,
            gadget_static_files=gadget_static_files,
            organizations=organizations,
            devices=[],
            user_setting=user_setting,
        )

    dashboard = get_dashboard_by_id(dashboard_id)
    groups = get_dashboard_groups(dashboard_id)
    group_ids = [grp.dashboard_group_id for grp in groups]
    gadgets = get_gadgets_by_groups(group_ids)
    devices = []
    if user_setting and user_setting.organization_id is not None:
        devices = get_devices(user_setting.organization_id)

    gadget_device_names = get_fixed_gadget_device_names(gadgets)

    return render_template(
        'analysis/customer_dashboard/index.html',
        dashboards=dashboards,
        dashboard=dashboard,
        groups=groups,
        gadgets=gadgets,
        gadget_id_to_template=gadget_id_to_template,
        gadget_type_ids=gadget_type_ids,
        gadget_static_files=gadget_static_files,
        organizations=organizations,
        devices=devices,
        user_setting=user_setting,
        gadget_device_names=gadget_device_names,
    )


# ---------------------------------------------------------------------------
# No.2 ダッシュボード管理モーダル表示
# ---------------------------------------------------------------------------

@customer_dashboard_bp.route('/dashboards', methods=['GET'])
@require_auth
def dashboard_management():
    """ダッシュボード管理モーダル表示"""
    accessible_org_ids = get_accessible_organizations(get_organization_id_by_user(g.current_user.user_id))
    dashboards = get_dashboards(accessible_org_ids)

    return render_template(
        'analysis/customer_dashboard/modals/dashboard_management.html',
        dashboards=dashboards,
    )


# ---------------------------------------------------------------------------
# No.3 ダッシュボード登録モーダル表示
# ---------------------------------------------------------------------------

@customer_dashboard_bp.route('/dashboards/create', methods=['GET'])
@require_auth
def dashboard_create():
    """ダッシュボード登録モーダル表示"""
    form = DashboardForm()
    return render_template(
        'analysis/customer_dashboard/modals/dashboard_register.html',
        form=form,
    )


# ---------------------------------------------------------------------------
# No.4 ダッシュボード登録実行
# ---------------------------------------------------------------------------

@customer_dashboard_bp.route('/dashboards/register', methods=['POST'])
@require_auth
def dashboard_register():
    """ダッシュボード登録実行"""
    form = DashboardForm()

    if not form.validate_on_submit():
        return render_template(
            'analysis/customer_dashboard/modals/dashboard_register.html',
            form=form,
        ), 400

    try:
        logger.info(f'ダッシュボード登録開始: user_id={g.current_user.user_id}')
        dashboard = create_dashboard(
            name=form.dashboard_name.data,
            organization_id=get_organization_id_by_user(g.current_user.user_id),
            user_id=g.current_user.user_id,
        )
        db.session.flush()
        upsert_dashboard_user_setting(g.current_user.user_id, dashboard.dashboard_id)
        db.session.commit()
        logger.info(f'ダッシュボード登録成功: dashboard_id={dashboard.dashboard_id}')
        flash('ダッシュボードを登録しました', 'success')
        return redirect(url_for('customer_dashboard.customer_dashboard'))

    except Exception as e:
        db.session.rollback()
        abort(500)


# ---------------------------------------------------------------------------
# No.5 ダッシュボードタイトル更新モーダル表示
# ---------------------------------------------------------------------------

@customer_dashboard_bp.route('/dashboards/<string:dashboard_uuid>/edit', methods=['GET'])
@require_auth
def dashboard_edit(dashboard_uuid):
    """ダッシュボードタイトル更新モーダル表示"""
    accessible_org_ids = get_accessible_organizations(get_organization_id_by_user(g.current_user.user_id))
    dashboard = check_dashboard_access(dashboard_uuid, accessible_org_ids)
    if not dashboard:
        abort(404)

    form = DashboardForm(obj=dashboard)
    form.dashboard_name.data = dashboard.dashboard_name
    return render_template(
        'analysis/customer_dashboard/modals/dashboard_edit.html',
        form=form,
        dashboard=dashboard,
    )


# ---------------------------------------------------------------------------
# No.6 ダッシュボードタイトル更新実行
# ---------------------------------------------------------------------------

@customer_dashboard_bp.route('/dashboards/<string:dashboard_uuid>/update', methods=['POST'])
@require_auth
def dashboard_update(dashboard_uuid):
    """ダッシュボードタイトル更新実行"""
    try:
        snapshot_update_date = get_dashboard_update_date(dashboard_uuid)
    except Exception as e:
        abort(500)

    form = DashboardForm()
    if not form.validate_on_submit():
        dashboard = db.session.query(DashboardMaster).filter(
            DashboardMaster.dashboard_uuid == dashboard_uuid,
            DashboardMaster.delete_flag == False,
        ).first()
        return render_template(
            'analysis/customer_dashboard/modals/dashboard_edit.html',
            form=form,
            dashboard=dashboard,
        ), 400

    accessible_org_ids = get_accessible_organizations(get_organization_id_by_user(g.current_user.user_id))
    dashboard = check_dashboard_access(dashboard_uuid, accessible_org_ids)
    if not dashboard:
        abort(404)

    try:
        current_update_date = get_dashboard_update_date(dashboard_uuid)
    except Exception as e:
        abort(500)

    if snapshot_update_date != current_update_date:
        logger.warning(f'楽観ロック競合検出: dashboard_uuid={dashboard_uuid}, user_id={g.current_user.user_id}')
        abort(409)

    try:
        update_dashboard_title(dashboard, form.dashboard_name.data, g.current_user.user_id)
        db.session.commit()
        flash('ダッシュボードタイトルを更新しました', 'success')
        return redirect(url_for('customer_dashboard.customer_dashboard'))

    except Exception as e:
        db.session.rollback()
        abort(500)


# ---------------------------------------------------------------------------
# No.7 ダッシュボード削除確認モーダル表示
# ---------------------------------------------------------------------------

@customer_dashboard_bp.route('/dashboards/<string:dashboard_uuid>/delete', methods=['GET'])
@require_auth
def dashboard_delete_confirm(dashboard_uuid):
    """ダッシュボード削除確認モーダル表示"""
    accessible_org_ids = get_accessible_organizations(get_organization_id_by_user(g.current_user.user_id))
    dashboard = check_dashboard_access(dashboard_uuid, accessible_org_ids)
    if not dashboard:
        abort(404)

    return render_template(
        'analysis/customer_dashboard/modals/dashboard_delete_confirm.html',
        dashboard=dashboard,
    )


# ---------------------------------------------------------------------------
# No.8 ダッシュボード削除実行
# ---------------------------------------------------------------------------

@customer_dashboard_bp.route('/dashboards/<string:dashboard_uuid>/delete', methods=['POST'])
@require_auth
def dashboard_delete(dashboard_uuid):
    """ダッシュボード削除実行"""
    try:
        snapshot_update_date = get_dashboard_update_date(dashboard_uuid)
    except Exception as e:
        abort(500)

    accessible_org_ids = get_accessible_organizations(get_organization_id_by_user(g.current_user.user_id))
    dashboard = check_dashboard_access(dashboard_uuid, accessible_org_ids)
    if not dashboard:
        abort(404)

    try:
        current_update_date = get_dashboard_update_date(dashboard_uuid)
    except Exception as e:
        abort(500)

    if snapshot_update_date != current_update_date:
        logger.warning(f'楽観ロック競合検出: dashboard_uuid={dashboard_uuid}, user_id={g.current_user.user_id}')
        abort(409)

    try:
        delete_dashboard_with_cascade(dashboard, accessible_org_ids, g.current_user.user_id)
        db.session.commit()
        flash('ダッシュボードを削除しました', 'success')
        return redirect(url_for('customer_dashboard.customer_dashboard'))

    except Exception as e:
        db.session.rollback()
        abort(500)


# ---------------------------------------------------------------------------
# No.9 ダッシュボード表示切替
# ---------------------------------------------------------------------------

@customer_dashboard_bp.route('/dashboards/<string:dashboard_uuid>/switch', methods=['POST'])
@require_auth
def dashboard_switch(dashboard_uuid):
    """ダッシュボード表示切替"""
    accessible_org_ids = get_accessible_organizations(get_organization_id_by_user(g.current_user.user_id))
    dashboard = check_dashboard_access(dashboard_uuid, accessible_org_ids)
    if not dashboard:
        abort(404)

    try:
        upsert_dashboard_user_setting(g.current_user.user_id, dashboard.dashboard_id)
        db.session.commit()
        return redirect(url_for('customer_dashboard.customer_dashboard'))

    except Exception as e:
        db.session.rollback()
        abort(500)


# ---------------------------------------------------------------------------
# No.10 ダッシュボードグループ登録モーダル表示
# ---------------------------------------------------------------------------

@customer_dashboard_bp.route('/groups/create', methods=['GET'])
@require_auth
def group_create():
    """ダッシュボードグループ登録モーダル表示"""
    form = DashboardGroupForm()
    form.dashboard_uuid.data = request.args.get('dashboard_uuid', '')
    return render_template(
        'analysis/customer_dashboard/modals/group_register.html',
        form=form,
    )


# ---------------------------------------------------------------------------
# No.11 ダッシュボードグループ登録実行
# ---------------------------------------------------------------------------

@customer_dashboard_bp.route('/groups/register', methods=['POST'])
@require_auth
def group_register():
    """ダッシュボードグループ登録実行"""
    form = DashboardGroupForm()

    if not form.validate_on_submit():
        return render_template(
            'analysis/customer_dashboard/modals/group_register.html',
            form=form,
        ), 400

    accessible_org_ids = get_accessible_organizations(get_organization_id_by_user(g.current_user.user_id))
    dashboard = check_dashboard_access(form.dashboard_uuid.data, accessible_org_ids)
    if not dashboard:
        abort(404)

    try:
        logger.info(f'グループ登録開始: user_id={g.current_user.user_id}, dashboard_id={dashboard.dashboard_id}')
        create_dashboard_group(
            group_name=form.dashboard_group_name.data,
            dashboard_id=dashboard.dashboard_id,
            user_id=g.current_user.user_id,
        )
        db.session.commit()
        logger.info(f'グループ登録成功: dashboard_id={dashboard.dashboard_id}')
        flash('ダッシュボードグループを登録しました', 'success')
        return redirect(url_for('customer_dashboard.customer_dashboard'))

    except Exception as e:
        db.session.rollback()
        abort(500)


# ---------------------------------------------------------------------------
# No.12 ダッシュボードグループタイトル更新モーダル表示
# ---------------------------------------------------------------------------

@customer_dashboard_bp.route('/groups/<string:dashboard_group_uuid>/edit', methods=['GET'])
@require_auth
def group_edit(dashboard_group_uuid):
    """ダッシュボードグループタイトル更新モーダル表示"""
    accessible_org_ids = get_accessible_organizations(get_organization_id_by_user(g.current_user.user_id))
    group = check_group_access(dashboard_group_uuid, accessible_org_ids)
    if not group:
        abort(404)

    form = DashboardGroupForm()
    form.dashboard_group_name.data = group.dashboard_group_name
    return render_template(
        'analysis/customer_dashboard/modals/group_edit.html',
        form=form,
        group=group,
    )


# ---------------------------------------------------------------------------
# No.13 ダッシュボードグループタイトル更新実行
# ---------------------------------------------------------------------------

@customer_dashboard_bp.route('/groups/<string:dashboard_group_uuid>/update', methods=['POST'])
@require_auth
def group_update(dashboard_group_uuid):
    """ダッシュボードグループタイトル更新実行"""
    try:
        snapshot_update_date = get_group_update_date(dashboard_group_uuid)
    except Exception as e:
        abort(500)

    form = DashboardGroupForm()
    if not form.validate_on_submit():
        group = db.session.query(DashboardGroupMaster).filter(
            DashboardGroupMaster.dashboard_group_uuid == dashboard_group_uuid,
            DashboardGroupMaster.delete_flag == False,
        ).first()
        return render_template(
            'analysis/customer_dashboard/modals/group_edit.html',
            form=form,
            group=group,
        ), 400

    accessible_org_ids = get_accessible_organizations(get_organization_id_by_user(g.current_user.user_id))
    group = check_group_access(dashboard_group_uuid, accessible_org_ids)
    if not group:
        abort(404)

    try:
        current_update_date = get_group_update_date(dashboard_group_uuid)
    except Exception as e:
        abort(500)

    if snapshot_update_date != current_update_date:
        logger.warning(f'楽観ロック競合検出: dashboard_group_uuid={dashboard_group_uuid}, user_id={g.current_user.user_id}')
        abort(409)

    try:
        update_group_title(group, form.dashboard_group_name.data, g.current_user.user_id)
        db.session.commit()
        flash('ダッシュボードグループタイトルを更新しました', 'success')
        return redirect(url_for('customer_dashboard.customer_dashboard'))

    except Exception as e:
        db.session.rollback()
        abort(500)


# ---------------------------------------------------------------------------
# No.14 ダッシュボードグループ削除確認モーダル表示
# ---------------------------------------------------------------------------

@customer_dashboard_bp.route('/groups/<string:dashboard_group_uuid>/delete', methods=['GET'])
@require_auth
def group_delete_confirm(dashboard_group_uuid):
    """ダッシュボードグループ削除確認モーダル表示"""
    accessible_org_ids = get_accessible_organizations(get_organization_id_by_user(g.current_user.user_id))
    group = check_group_access(dashboard_group_uuid, accessible_org_ids)
    if not group:
        abort(404)

    return render_template(
        'analysis/customer_dashboard/modals/group_delete_confirm.html',
        group=group,
    )


# ---------------------------------------------------------------------------
# No.15 ダッシュボードグループ削除実行
# ---------------------------------------------------------------------------

@customer_dashboard_bp.route('/groups/<string:dashboard_group_uuid>/delete', methods=['POST'])
@require_auth
def group_delete(dashboard_group_uuid):
    """ダッシュボードグループ削除実行"""
    try:
        snapshot_update_date = get_group_update_date(dashboard_group_uuid)
    except Exception as e:
        abort(500)

    accessible_org_ids = get_accessible_organizations(get_organization_id_by_user(g.current_user.user_id))
    group = check_group_access(dashboard_group_uuid, accessible_org_ids)
    if not group:
        abort(404)

    try:
        current_update_date = get_group_update_date(dashboard_group_uuid)
    except Exception as e:
        abort(500)

    if snapshot_update_date != current_update_date:
        logger.warning(f'楽観ロック競合検出: dashboard_group_uuid={dashboard_group_uuid}, user_id={g.current_user.user_id}')
        abort(409)

    try:
        delete_group_with_cascade(group, g.current_user.user_id)
        db.session.commit()
        flash('ダッシュボードグループを削除しました', 'success')
        return redirect(url_for('customer_dashboard.customer_dashboard'))

    except Exception as e:
        db.session.rollback()
        abort(500)


# ---------------------------------------------------------------------------
# No.16 ガジェット追加モーダル表示
# ---------------------------------------------------------------------------

@customer_dashboard_bp.route('/gadgets/add', methods=['GET'])
@require_auth
def gadget_add():
    """ガジェット追加モーダル表示"""
    gadget_types = get_gadget_types()
    return render_template(
        'analysis/customer_dashboard/modals/gadget_add.html',
        gadget_types=gadget_types,
        gadget_type_slug_map=GADGET_TYPE_SLUG,
    )


# ---------------------------------------------------------------------------
# No.17 ガジェット登録モーダル表示（ガジェット種別個別仕様に委譲）
# ---------------------------------------------------------------------------

@customer_dashboard_bp.route('/gadgets/<string:gadget_type>/create', methods=['GET'])
@require_auth
def gadget_create(gadget_type):
    """ガジェット登録モーダル表示（ガジェット種別ごとのハンドラーにディスパッチ）"""
    gadget_name = _SLUG_TO_NAME.get(gadget_type)
    if gadget_name is None:
        logger.error(f'未対応のガジェット種別: gadget_type={gadget_type}')
        abort(500)
    handler = _get_handler(gadget_name, 'handle_gadget_create')
    return handler(gadget_type)


# ---------------------------------------------------------------------------
# No.18 ガジェット登録実行（ガジェット種別個別仕様に委譲）
# ---------------------------------------------------------------------------

@customer_dashboard_bp.route('/gadgets/<string:gadget_type>/register', methods=['POST'])
@require_auth
def gadget_register(gadget_type):
    """ガジェット登録実行（ガジェット種別ごとのハンドラーにディスパッチ）"""
    gadget_name = _SLUG_TO_NAME.get(gadget_type)
    if gadget_name is None:
        logger.error(f'未対応のガジェット種別: gadget_type={gadget_type}')
        abort(500)
    handler = _get_handler(gadget_name, 'handle_gadget_register')
    return handler(gadget_type)


# ---------------------------------------------------------------------------
# No.19 ガジェットタイトル更新モーダル表示
# ---------------------------------------------------------------------------

@customer_dashboard_bp.route('/gadgets/<string:gadget_uuid>/edit', methods=['GET'])
@require_auth
def gadget_edit(gadget_uuid):
    """ガジェットタイトル更新モーダル表示"""
    accessible_org_ids = get_accessible_organizations(get_organization_id_by_user(g.current_user.user_id))
    gadget = check_gadget_access(gadget_uuid, accessible_org_ids)
    if not gadget:
        abort(404)

    form = GadgetForm()
    form.gadget_name.data = gadget.gadget_name
    return render_template(
        'analysis/customer_dashboard/modals/gadget_edit.html',
        form=form,
        gadget=gadget,
    )


# ---------------------------------------------------------------------------
# No.20 ガジェットタイトル更新実行
# ---------------------------------------------------------------------------

@customer_dashboard_bp.route('/gadgets/<string:gadget_uuid>/update', methods=['POST'])
@require_auth
def gadget_update(gadget_uuid):
    """ガジェットタイトル更新実行"""
    try:
        snapshot_update_date = get_gadget_update_date(gadget_uuid)
    except Exception as e:
        abort(500)

    form = GadgetForm()
    if not form.validate_on_submit():
        gadget = db.session.query(DashboardGadgetMaster).filter(
            DashboardGadgetMaster.gadget_uuid == gadget_uuid,
            DashboardGadgetMaster.delete_flag == False,
        ).first()
        return render_template(
            'analysis/customer_dashboard/modals/gadget_edit.html',
            form=form,
            gadget=gadget,
        ), 400

    accessible_org_ids = get_accessible_organizations(get_organization_id_by_user(g.current_user.user_id))
    gadget = check_gadget_access(gadget_uuid, accessible_org_ids)
    if not gadget:
        abort(404)

    try:
        current_update_date = get_gadget_update_date(gadget_uuid)
    except Exception as e:
        abort(500)

    if snapshot_update_date != current_update_date:
        logger.warning(f'楽観ロック競合検出: gadget_uuid={gadget_uuid}, user_id={g.current_user.user_id}')
        abort(409)

    try:
        update_gadget_title(gadget, form.gadget_name.data, g.current_user.user_id)
        db.session.commit()
        flash('ガジェットタイトルを更新しました', 'success')
        return redirect(url_for('customer_dashboard.customer_dashboard'))

    except Exception as e:
        db.session.rollback()
        abort(500)


# ---------------------------------------------------------------------------
# No.21 ガジェット削除確認モーダル表示
# ---------------------------------------------------------------------------

@customer_dashboard_bp.route('/gadgets/<string:gadget_uuid>/delete', methods=['GET'])
@require_auth
def gadget_delete_confirm(gadget_uuid):
    """ガジェット削除確認モーダル表示"""
    accessible_org_ids = get_accessible_organizations(get_organization_id_by_user(g.current_user.user_id))
    gadget = check_gadget_access(gadget_uuid, accessible_org_ids)
    if not gadget:
        abort(404)

    return render_template(
        'analysis/customer_dashboard/modals/gadget_delete_confirm.html',
        gadget=gadget,
    )


# ---------------------------------------------------------------------------
# No.22 ガジェット削除実行
# ---------------------------------------------------------------------------

@customer_dashboard_bp.route('/gadgets/<string:gadget_uuid>/delete', methods=['POST'])
@require_auth
def gadget_delete(gadget_uuid):
    """ガジェット削除実行"""
    try:
        snapshot_update_date = get_gadget_update_date(gadget_uuid)
    except Exception as e:
        abort(500)

    accessible_org_ids = get_accessible_organizations(get_organization_id_by_user(g.current_user.user_id))
    gadget = check_gadget_access(gadget_uuid, accessible_org_ids)
    if not gadget:
        abort(404)

    try:
        current_update_date = get_gadget_update_date(gadget_uuid)
    except Exception as e:
        abort(500)

    if snapshot_update_date != current_update_date:
        logger.warning(f'楽観ロック競合検出: gadget_uuid={gadget_uuid}, user_id={g.current_user.user_id}')
        abort(409)

    try:
        delete_gadget(gadget, g.current_user.user_id)
        db.session.commit()
        flash('ガジェットを削除しました', 'success')
        return redirect(url_for('customer_dashboard.customer_dashboard'))

    except Exception as e:
        db.session.rollback()
        abort(500)


# ---------------------------------------------------------------------------
# No.23 ガジェットデータ取得 / CSVエクスポート（ガジェット種別ごとのハンドラーにディスパッチ）
# ---------------------------------------------------------------------------

@customer_dashboard_bp.route('/gadgets/preview/grid/data', methods=['POST'])
@require_auth
def gadget_preview_grid_data():
    """表ガジェット登録モーダル用プレビューデータ取得"""
    from iot_app.views.analysis.customer_dashboard.grid import handle_gadget_preview
    return handle_gadget_preview()


@customer_dashboard_bp.route('/gadgets/<string:gadget_uuid>/data', methods=['POST'])
@require_auth
def gadget_data(gadget_uuid):
    """ガジェットデータ取得（AJAX）"""
    gadget_type = get_gadget_type(gadget_uuid)
    if gadget_type is None:
        abort(404)
    handler = _get_handler(gadget_type, 'handle_gadget_data')
    if handler is None:
        logger.error(f'未対応のガジェット種別: gadget_type={gadget_type}, gadget_uuid={gadget_uuid}')
        abort(500)
    return handler(gadget_uuid)


@customer_dashboard_bp.route('/gadgets/<string:gadget_uuid>', methods=['GET'])
@require_auth
def gadget_csv_export(gadget_uuid):
    """ガジェット CSVエクスポート"""
    gadget_type = get_gadget_type(gadget_uuid)
    if gadget_type is None:
        abort(404)
    handler = _get_handler(gadget_type, 'handle_gadget_csv_export')
    if handler is None:
        logger.error(f'未対応のガジェット種別: gadget_type={gadget_type}, gadget_uuid={gadget_uuid}')
        abort(500)
    return handler(gadget_uuid)


# ---------------------------------------------------------------------------
# No.24 レイアウト保存
# ---------------------------------------------------------------------------

@customer_dashboard_bp.route('/layout/save', methods=['POST'])
@require_auth
def layout_save():
    """レイアウト保存（AJAX）"""
    try:
        data = request.get_json()
        gadgets = data.get('gadgets', []) if data else []
        logger.info(f'レイアウト保存開始: user_id={g.current_user.user_id}, gadget_count={len(gadgets)}')
        save_layout(gadgets, g.current_user.user_id)
        db.session.commit()
        logger.info(f'レイアウト保存成功: user_id={g.current_user.user_id}')
        return jsonify({'message': 'レイアウトを保存しました'}), 200

    except Exception as e:
        db.session.rollback()
        logger.error(f'レイアウト保存エラー: {str(e)}')
        return jsonify({'error': 'レイアウトの保存に失敗しました'}), 500


# ---------------------------------------------------------------------------
# No.25 CSVエクスポート（各ガジェット種別モジュールに委譲）
# ---------------------------------------------------------------------------
# bar_chart.py 等、各ガジェット種別モジュールが /gadgets/<gadget_uuid> を実装する


# ---------------------------------------------------------------------------
# No.26 デバイス一覧取得（AJAX）
# ---------------------------------------------------------------------------

@customer_dashboard_bp.route('/organizations/<int:org_id>/devices', methods=['GET'])
@require_auth
def organization_devices(org_id):
    """デバイス一覧取得（AJAX）"""
    try:
        devices = get_devices_by_organization(org_id)
        return jsonify({
            'devices': [
                {'device_id': d.device_id, 'device_name': d.device_name}
                for d in devices
            ]
        })

    except Exception as e:
        logger.error(f'デバイス一覧取得エラー: {str(e)}')
        return jsonify({'error': 'デバイス一覧の取得に失敗しました'}), 500


# ---------------------------------------------------------------------------
# No.27 データソース設定保存（AJAX）
# ---------------------------------------------------------------------------

@customer_dashboard_bp.route('/datasource/save', methods=['POST'])
@require_auth
def datasource_save():
    """データソース設定保存（AJAX）"""
    try:
        data = request.get_json()
        organization_id = data.get('organization_id') if data else None
        device_id = data.get('device_id') if data else None
        update_datasource_setting(
            user_id=g.current_user.user_id,
            organization_id=organization_id,
            device_id=device_id,
            modifier=g.current_user.user_id,
        )
        db.session.commit()
        return jsonify({'status': 'ok'})

    except Exception as e:
        db.session.rollback()
        logger.error(f'データソース設定保存エラー: {str(e)}')
        return jsonify({'error': 'データソース設定の保存に失敗しました'}), 500
