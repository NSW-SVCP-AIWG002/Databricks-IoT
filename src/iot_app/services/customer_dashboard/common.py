import uuid

from sqlalchemy import func

from iot_app import db
from iot_app.models.customer_dashboard import (
    DashboardGadgetMaster,
    DashboardGroupMaster,
    DashboardMaster,
    DashboardUserSetting,
    GadgetTypeMaster,
)
from iot_app.models.device import DeviceMaster
from iot_app.models.organization import OrganizationClosure, OrganizationMaster
from iot_app.models.user import User


# ---------------------------------------------------------------------------
# データスコープ制御
# ---------------------------------------------------------------------------

def get_organization_id_by_user(user_id):
    """ユーザーIDから所属組織IDを返す。
    NOTE: get_accessible_organizations が不要になった際は呼び出し元ごと削除する。
    """
    return (
        db.session.query(User.organization_id)
        .filter(User.user_id == user_id, User.delete_flag == False)
        .scalar()
    )


def get_accessible_organizations(parent_org_id):
    """ユーザーがアクセス可能な組織IDリストを返す"""
    rows = (
        db.session.query(OrganizationClosure.subsidiary_organization_id)
        .filter(OrganizationClosure.parent_organization_id == parent_org_id)
        .all()
    )
    return [r[0] for r in rows]


# ---------------------------------------------------------------------------
# ダッシュボードユーザー設定
# ---------------------------------------------------------------------------

def get_dashboard_user_setting(user_id):
    """ユーザーのダッシュボード設定を返す。存在しない場合はNone"""
    return (
        db.session.query(DashboardUserSetting)
        .filter(
            DashboardUserSetting.user_id == user_id,
            DashboardUserSetting.delete_flag == False,
        )
        .first()
    )


def upsert_dashboard_user_setting(user_id, dashboard_id):
    """ユーザー設定が存在しない場合はINSERT、存在する場合はdashboard_idを更新する"""
    setting = (
        db.session.query(DashboardUserSetting)
        .filter(DashboardUserSetting.user_id == user_id)
        .first()
    )
    if setting is None:
        new_setting = DashboardUserSetting(
            user_id=user_id,
            dashboard_id=dashboard_id,
            organization_id=None,
            device_id=None,
            creator=user_id,
            modifier=user_id,
        )
        db.session.add(new_setting)
    else:
        setting.dashboard_id = dashboard_id


def delete_dashboard_user_setting(user_id, modifier):
    """ユーザー設定を論理削除する"""
    setting = (
        db.session.query(DashboardUserSetting)
        .filter(DashboardUserSetting.user_id == user_id)
        .first()
    )
    if setting is not None:
        setting.delete_flag = True
        setting.modifier = modifier


def update_datasource_setting(user_id, organization_id, device_id, modifier):
    """ユーザー設定の組織ID・デバイスIDを更新する。未選択はNULLで保持する"""
    setting = (
        db.session.query(DashboardUserSetting)
        .filter(DashboardUserSetting.user_id == user_id)
        .first()
    )
    if setting is not None:
        setting.organization_id = organization_id
        setting.device_id = device_id
        setting.modifier = modifier


# ---------------------------------------------------------------------------
# ダッシュボード取得
# ---------------------------------------------------------------------------

def get_dashboard_by_id(dashboard_id):
    """dashboard_idでダッシュボードを取得する"""
    return (
        db.session.query(DashboardMaster)
        .filter(DashboardMaster.dashboard_id == dashboard_id)
        .first()
    )


def get_dashboards(accessible_org_ids):
    """アクセス可能スコープ内のダッシュボード一覧をdashboard_id昇順で返す"""
    if not accessible_org_ids:
        return []
    return (
        db.session.query(DashboardMaster)
        .filter(
            DashboardMaster.organization_id.in_(accessible_org_ids),
            DashboardMaster.delete_flag == False,
        )
        .order_by(DashboardMaster.dashboard_id)
        .all()
    )


def get_first_dashboard(accessible_org_ids, exclude_id=None):
    """アクセス可能スコープ内の先頭ダッシュボードを返す。exclude_id指定時は除外する"""
    query = (
        db.session.query(DashboardMaster)
        .filter(
            DashboardMaster.organization_id.in_(accessible_org_ids),
            DashboardMaster.delete_flag == False,
        )
    )
    if exclude_id is not None:
        query = query.filter(DashboardMaster.dashboard_id != exclude_id)
    return query.order_by(DashboardMaster.dashboard_id).first()


def get_active_dashboard(user_setting, accessible_org_ids):
    """アクティブなダッシュボードIDを返す。ユーザー設定あり→設定値、なし→先頭、どちらもなし→None"""
    if user_setting is not None:
        return user_setting.dashboard_id
    first = get_first_dashboard(accessible_org_ids)
    if first is None:
        return None
    return first.dashboard_id


def check_dashboard_access(dashboard_uuid, accessible_org_ids):
    """ダッシュボードがアクセス可能スコープ内に存在するか確認する"""
    return (
        db.session.query(DashboardMaster)
        .filter(
            DashboardMaster.dashboard_uuid == dashboard_uuid,
            DashboardMaster.organization_id.in_(accessible_org_ids),
            DashboardMaster.delete_flag == False,
        )
        .first()
    )


def get_dashboard_update_date(dashboard_uuid):
    """楽観ロック用: ダッシュボードの update_date を返す。存在しない場合は None"""
    return (
        db.session.query(DashboardMaster.update_date)
        .filter(
            DashboardMaster.dashboard_uuid == dashboard_uuid,
            DashboardMaster.delete_flag == False,
        )
        .scalar()
    )


# ---------------------------------------------------------------------------
# ダッシュボード操作
# ---------------------------------------------------------------------------

def create_dashboard(name, organization_id, user_id):
    """ダッシュボードを新規作成してsessionに追加する"""
    dashboard = DashboardMaster(
        dashboard_uuid=str(uuid.uuid4()),
        dashboard_name=name,
        organization_id=organization_id,
        creator=user_id,
        modifier=user_id,
    )
    db.session.add(dashboard)
    return dashboard


def update_dashboard_title(dashboard, name, modifier):
    """ダッシュボード名とmodifierを更新する"""
    dashboard.dashboard_name = name
    dashboard.modifier = modifier


def delete_dashboard_with_cascade(dashboard, accessible_org_ids, user_id):
    """ダッシュボードをカスケード論理削除する。次のダッシュボードがあればユーザー設定を更新する"""
    dashboard_id = dashboard.dashboard_id

    delete_gadgets_by_dashboard(dashboard_id=dashboard_id, modifier=user_id)
    delete_groups_by_dashboard(dashboard_id=dashboard_id, modifier=user_id)

    dashboard.delete_flag = True
    dashboard.modifier = user_id

    next_dashboard = get_first_dashboard(accessible_org_ids, exclude_id=dashboard_id)
    if next_dashboard is not None:
        upsert_dashboard_user_setting(user_id, next_dashboard.dashboard_id)
    else:
        delete_dashboard_user_setting(user_id=user_id, modifier=user_id)


# ---------------------------------------------------------------------------
# グループ取得
# ---------------------------------------------------------------------------

def get_dashboard_groups(dashboard_id):
    """ダッシュボードに紐づくグループをdisplay_order昇順で返す"""
    return (
        db.session.query(DashboardGroupMaster)
        .filter(
            DashboardGroupMaster.dashboard_id == dashboard_id,
            DashboardGroupMaster.delete_flag == False,
        )
        .order_by(DashboardGroupMaster.display_order)
        .all()
    )


def check_group_access(dashboard_group_uuid, accessible_org_ids):
    """グループがアクセス可能スコープ内に存在するか確認する（JOINでダッシュボード経由）"""
    return (
        db.session.query(DashboardGroupMaster)
        .join(DashboardMaster)
        .filter(
            DashboardGroupMaster.dashboard_group_uuid == dashboard_group_uuid,
            DashboardMaster.organization_id.in_(accessible_org_ids),
            DashboardGroupMaster.delete_flag == False,
        )
        .first()
    )


def get_group_update_date(dashboard_group_uuid):
    """楽観ロック用: グループの update_date を返す。存在しない場合は None"""
    return (
        db.session.query(DashboardGroupMaster.update_date)
        .filter(
            DashboardGroupMaster.dashboard_group_uuid == dashboard_group_uuid,
            DashboardGroupMaster.delete_flag == False,
        )
        .scalar()
    )


# ---------------------------------------------------------------------------
# グループ操作
# ---------------------------------------------------------------------------

def create_dashboard_group(group_name, dashboard_id, user_id):
    """グループを新規作成する。display_orderは既存最大値+1を設定する"""
    max_order = (
        db.session.query(func.max(DashboardGroupMaster.display_order))
        .filter(DashboardGroupMaster.dashboard_id == dashboard_id)
        .scalar()
    )
    display_order = (max_order or 0) + 1

    group = DashboardGroupMaster(
        dashboard_group_uuid=str(uuid.uuid4()),
        dashboard_group_name=group_name,
        dashboard_id=dashboard_id,
        display_order=display_order,
        creator=user_id,
        modifier=user_id,
    )
    db.session.add(group)
    return group


def update_group_title(group, name, modifier):
    """グループ名とmodifierを更新する"""
    group.dashboard_group_name = name
    group.modifier = modifier


def delete_group_with_cascade(group, user_id):
    """グループをカスケード論理削除する"""
    delete_gadgets_by_group(group_id=group.dashboard_group_id, modifier=user_id)
    group.delete_flag = True
    group.modifier = user_id


# ---------------------------------------------------------------------------
# ガジェット取得
# ---------------------------------------------------------------------------

def get_gadgets_by_groups(group_ids):
    """指定グループIDに紐づくガジェット一覧を返す。group_idsが空の場合はDBアクセスしない"""
    if not group_ids:
        return []
    return (
        db.session.query(DashboardGadgetMaster)
        .filter(
            DashboardGadgetMaster.dashboard_group_id.in_(group_ids),
            DashboardGadgetMaster.delete_flag == False,
        )
        .order_by(DashboardGadgetMaster.display_order)
        .all()
    )


def get_gadget_type_id_by_name(gadget_type_name):
    """ガジェット種別名から gadget_type_id を返す。該当なしの場合は None"""
    result = (
        db.session.query(GadgetTypeMaster.gadget_type_id)
        .filter_by(gadget_type_name=gadget_type_name, delete_flag=False)
        .first()
    )
    return result.gadget_type_id if result else None


def get_gadget_types():
    """全ガジェット種別をdisplay_order昇順で返す"""
    return (
        db.session.query(GadgetTypeMaster)
        .filter(GadgetTypeMaster.delete_flag == False)
        .order_by(GadgetTypeMaster.display_order)
        .all()
    )


def check_gadget_access(gadget_uuid, accessible_org_ids):
    """ガジェットがアクセス可能スコープ内に存在するか確認する（2段JOINでダッシュボード経由）"""
    return (
        db.session.query(DashboardGadgetMaster)
        .join(DashboardGroupMaster)
        .join(DashboardMaster)
        .filter(
            DashboardGadgetMaster.gadget_uuid == gadget_uuid,
            DashboardMaster.organization_id.in_(accessible_org_ids),
            DashboardGadgetMaster.delete_flag == False,
        )
        .first()
    )


def get_gadget_update_date(gadget_uuid):
    """楽観ロック用: ガジェットの update_date を返す。存在しない場合は None"""
    return (
        db.session.query(DashboardGadgetMaster.update_date)
        .filter(
            DashboardGadgetMaster.gadget_uuid == gadget_uuid,
            DashboardGadgetMaster.delete_flag == False,
        )
        .scalar()
    )


# ---------------------------------------------------------------------------
# ガジェット操作
# ---------------------------------------------------------------------------

def update_gadget_title(gadget, name, modifier):
    """ガジェット名とmodifierを更新する"""
    gadget.gadget_name = name
    gadget.modifier = modifier


def delete_gadget(gadget, modifier):
    """ガジェットを論理削除する"""
    gadget.delete_flag = True
    gadget.modifier = modifier


def save_layout(layout_data, modifier):
    """レイアウトデータに基づき各ガジェットのposition/display_orderを更新する"""
    try:
        for item in layout_data:
            gadget = (
                db.session.query(DashboardGadgetMaster)
                .filter(DashboardGadgetMaster.gadget_uuid == item['gadget_uuid'])
                .first()
            )
            if gadget is None:
                continue
            gadget.position_x = item['position_x']
            gadget.position_y = item['position_y']
            gadget.display_order = item['display_order']
            gadget.modifier = modifier
    except Exception:
        db.session.rollback()
        raise


# ---------------------------------------------------------------------------
# カスケード削除ヘルパー
# ---------------------------------------------------------------------------

def delete_gadgets_by_dashboard(dashboard_id, modifier):
    """ダッシュボード配下の全ガジェットを論理削除する"""
    gadgets = (
        db.session.query(DashboardGadgetMaster)
        .join(DashboardGroupMaster)
        .filter(
            DashboardGroupMaster.dashboard_id == dashboard_id,
            DashboardGadgetMaster.delete_flag == False,
        )
        .all()
    )
    for gadget in gadgets:
        gadget.delete_flag = True
        gadget.modifier = modifier
    db.session.commit()


def delete_groups_by_dashboard(dashboard_id, modifier):
    """ダッシュボード配下の全グループを論理削除する"""
    groups = (
        db.session.query(DashboardGroupMaster)
        .filter(
            DashboardGroupMaster.dashboard_id == dashboard_id,
            DashboardGroupMaster.delete_flag == False,
        )
        .all()
    )
    for group in groups:
        group.delete_flag = True
        group.modifier = modifier
    db.session.commit()


def delete_gadgets_by_group(group_id, modifier):
    """グループ配下の全ガジェットを論理削除する"""
    gadgets = (
        db.session.query(DashboardGadgetMaster)
        .filter(
            DashboardGadgetMaster.dashboard_group_id == group_id,
            DashboardGadgetMaster.delete_flag == False,
        )
        .all()
    )
    for gadget in gadgets:
        gadget.delete_flag = True
        gadget.modifier = modifier
    db.session.commit()


# ---------------------------------------------------------------------------
# 組織・デバイス取得
# ---------------------------------------------------------------------------

def get_organizations(accessible_org_ids):
    """アクセス可能スコープ内の組織一覧をorganization_id昇順で返す"""
    return (
        db.session.query(OrganizationMaster)
        .filter(
            OrganizationMaster.organization_id.in_(accessible_org_ids),
            OrganizationMaster.delete_flag == False,
        )
        .order_by(OrganizationMaster.organization_id)
        .all()
    )


def get_devices(organization_id):
    """組織に紐づくデバイス一覧をdevice_id昇順で返す"""
    return (
        db.session.query(DeviceMaster)
        .filter(
            DeviceMaster.organization_id == organization_id,
            DeviceMaster.delete_flag == False,
        )
        .order_by(DeviceMaster.device_id)
        .all()
    )


def get_devices_by_organization(org_id):
    """組織に紐づくデバイス一覧をdevice_id昇順で返す（AJAXエンドポイント用）"""
    return (
        db.session.query(DeviceMaster)
        .filter(
            DeviceMaster.organization_id == org_id,
            DeviceMaster.delete_flag == False,
        )
        .order_by(DeviceMaster.device_id)
        .all()
    )
