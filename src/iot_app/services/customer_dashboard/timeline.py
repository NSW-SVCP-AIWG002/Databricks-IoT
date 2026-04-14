"""
時系列グラフガジェット サービス層

参照設計書:
  - docs/03-features/flask-app/customer-dashboard/timeline/workflow-specification.md
  - docs/03-features/flask-app/customer-dashboard/timeline/ui-specification.md
"""

import csv
import io
import json
import uuid
from datetime import datetime, timedelta

from sqlalchemy.exc import IntegrityError

from sqlalchemy import func

from iot_app import db
from iot_app.common.exceptions import NotFoundError, ValidationError
from iot_app.common.messages import (
    ERR_DATETIME_FORMAT,
    ERR_DATETIME_RANGE_24H,
    ERR_END_BEFORE_START,
    err_invalid,
    err_max_length,
    err_min_less_than_max,
    err_numeric,
    err_required,
    err_select_required,
)
from iot_app.common.logger import get_logger
from iot_app.services.customer_dashboard.common import GADGET_SIZE_TO_INT
from iot_app.models.customer_dashboard import DashboardGadgetMaster, DashboardGroupMaster, DashboardMaster, GadgetTypeMaster

logger = get_logger(__name__)

_DATETIME_FORMAT = '%Y/%m/%d %H:%M:%S'
_ALLOWED_GADGET_SIZES = {'2x2', '2x4'}


# ---------------------------------------------------------------------------
# データスコープ・ガジェット取得
# ---------------------------------------------------------------------------

def get_accessible_org_ids(org_id):
    """organization_closure からアクセス可能な組織IDリストを取得する

    Args:
        org_id: 親組織ID（current_user.organization_id）

    Returns:
        list[int]: アクセス可能な組織IDリスト
    """
    from iot_app.models.organization import OrganizationClosure
    rows = db.session.query(
        OrganizationClosure.subsidiary_organization_id
    ).filter(
        OrganizationClosure.parent_organization_id == org_id
    ).all()
    return [r[0] for r in rows]


def get_gadget_in_scope(gadget_uuid, accessible_org_ids):
    """スコープチェック込みでガジェットを取得する

    DashboardGadgetMaster → DashboardGroupMaster → DashboardMaster → organization_id の
    経路でアクセス可能な組織に属するガジェットのみ返す。

    Args:
        gadget_uuid (str): ガジェット UUID
        accessible_org_ids (list[int]): アクセス可能な組織IDリスト

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


def get_active_gadgets_in_scope(accessible_org_ids):
    """アクセス可能な組織に属するガジェット一覧を表示順で取得する

    Args:
        accessible_org_ids (list[int]): アクセス可能な組織IDリスト

    Returns:
        list[DashboardGadgetMaster]: ガジェット一覧（display_order昇順）
    """
    return db.session.query(DashboardGadgetMaster).join(
        DashboardGroupMaster,
        DashboardGadgetMaster.dashboard_group_id == DashboardGroupMaster.dashboard_group_id,
    ).join(
        DashboardMaster,
        DashboardGroupMaster.dashboard_id == DashboardMaster.dashboard_id,
    ).filter(
        DashboardGadgetMaster.delete_flag == False,
        DashboardGroupMaster.delete_flag == False,
        DashboardMaster.delete_flag == False,
        DashboardMaster.organization_id.in_(accessible_org_ids),
    ).order_by(DashboardGadgetMaster.display_order.asc()).all()


def get_chart_column_names(gadget):
    """ガジェットの chart_config から左右のシルバー層カラム名を取得する

    Args:
        gadget (DashboardGadgetMaster): ガジェットオブジェクト

    Returns:
        tuple[str, str]: (left_column_name, right_column_name)

    Raises:
        NotFoundError: 測定項目が存在しない場合
    """
    from iot_app.models.measurement import MeasurementItemMaster
    chart_config = json.loads(gadget.chart_config)
    left_item  = db.session.get(MeasurementItemMaster, chart_config['left_item_id'])
    right_item = db.session.get(MeasurementItemMaster, chart_config['right_item_id'])
    if left_item is None or right_item is None:
        raise NotFoundError('測定項目が見つかりません')
    return left_item.silver_data_column_name, right_item.silver_data_column_name


def get_gadget_by_uuid(gadget_uuid):
    """ガジェットをUUIDで取得する（スコープチェックなし）

    Args:
        gadget_uuid (str): ガジェット UUID

    Returns:
        DashboardGadgetMaster | None: ガジェット、または None（存在しない・論理削除済み）
    """
    return db.session.query(DashboardGadgetMaster).filter(
        DashboardGadgetMaster.gadget_uuid == gadget_uuid,
        DashboardGadgetMaster.delete_flag == False,
    ).first()


def check_gadget_access(gadget, accessible_org_ids):
    """ガジェットがアクセス可能な組織に属するか確認する

    Args:
        gadget (DashboardGadgetMaster): ガジェットオブジェクト
        accessible_org_ids (list[int]): アクセス可能な組織IDリスト

    Returns:
        bool: アクセス可能であれば True
    """
    return get_gadget_in_scope(gadget.gadget_uuid, accessible_org_ids) is not None


def get_measurement_item(item_id):
    """測定項目を取得する

    Args:
        item_id (int): 測定項目ID

    Returns:
        MeasurementItem | None: 測定項目、または None

    Raises:
        NotFoundError: 測定項目が存在しない場合
    """
    from iot_app.models.measurement import MeasurementItemMaster
    item = db.session.get(MeasurementItemMaster, item_id)
    if item is None:
        raise NotFoundError(f'測定項目が見つかりません: item_id={item_id}')
    return item


def check_device_in_scope(device_id, accessible_org_ids):
    """デバイスがスコープ内に存在するか確認する

    Args:
        device_id (int): デバイスID
        accessible_org_ids (list[int]): アクセス可能な組織IDリスト

    Returns:
        DeviceMaster | None: スコープ内のデバイス、または None
    """
    from iot_app.models.device import DeviceMaster
    return db.session.query(DeviceMaster).filter(
        DeviceMaster.device_id == device_id,
        DeviceMaster.organization_id.in_(accessible_org_ids),
        DeviceMaster.delete_flag == False,
    ).first()


# ---------------------------------------------------------------------------
# DBアクセス関数
# ---------------------------------------------------------------------------

def get_dashboard_user_setting(user_id):
    """ダッシュボードユーザー設定を取得する（dashboard_user_setting テーブル）"""
    from iot_app.models.customer_dashboard import DashboardUserSetting
    if user_id is None:
        return None
    return db.session.query(DashboardUserSetting).filter_by(
        user_id=user_id,
        delete_flag=False,
    ).first()


# ---------------------------------------------------------------------------
# 外部依存（テストではモック化される）
# ---------------------------------------------------------------------------

def execute_silver_query(device_id, start_datetime, end_datetime, limit=100):
    """Unity Catalog sensor_data_view からセンサーデータを取得する"""
    import os
    if os.getenv('FLASK_ENV') == 'development':
        # 開発環境向けモック（Unity Catalog に疎通できる環境になったら削除）
        from iot_app import db
        from iot_app.models.measurement import MeasurementItemMaster
        col_names = [r.silver_data_column_name for r in db.session.query(
            MeasurementItemMaster.silver_data_column_name
        ).filter_by(delete_flag=False).all()]

        rows = []
        t = start_datetime
        step = (end_datetime - start_datetime) / max(10, 1)
        for i in range(10):
            row = {
                'event_timestamp': t + step * i,
                'device_id': device_id,
                'device_name': 'モックデバイス',
            }
            for col in col_names:
                row[col] = round(20.0 + i * 0.1, 2)
            rows.append(row)
        return rows

    from iot_app.databricks.unity_catalog_connector import UnityCatalogConnector
    connector = UnityCatalogConnector()
    sql_text = """
        SELECT *
        FROM iot_catalog.views.sensor_data_view
        WHERE device_id = :device_id
          AND event_timestamp >= :start_datetime
          AND event_timestamp < :end_datetime
        ORDER BY event_timestamp
        LIMIT :limit
    """
    return connector.execute(sql_text, {
        'device_id':      device_id,
        'start_datetime': start_datetime,
        'end_datetime':   end_datetime,
        'limit':          limit,
    })


# ---------------------------------------------------------------------------
# validate_chart_params
# ---------------------------------------------------------------------------

def validate_chart_params(start_datetime_str, end_datetime_str):
    """ガジェットデータ取得パラメータのバリデーション

    Args:
        start_datetime_str: 開始日時文字列（YYYY/MM/DD HH:mm:ss）
        end_datetime_str:   終了日時文字列（YYYY/MM/DD HH:mm:ss）

    Returns:
        str | None: エラーメッセージ（正常時は None）
    """
    if not start_datetime_str or not end_datetime_str:
        return '正しい日付形式で入力してください（YYYY/MM/DD HH:mm:ss）'

    try:
        start = datetime.strptime(start_datetime_str, _DATETIME_FORMAT)
        end   = datetime.strptime(end_datetime_str,   _DATETIME_FORMAT)
    except ValueError:
        return '正しい日付形式で入力してください（YYYY/MM/DD HH:mm:ss）'

    # 1桁月などの曖昧な表記を排除（strftime で再フォーマットして一致確認）
    if start.strftime(_DATETIME_FORMAT) != start_datetime_str:
        return '正しい日付形式で入力してください（YYYY/MM/DD HH:mm:ss）'
    if end.strftime(_DATETIME_FORMAT) != end_datetime_str:
        return '正しい日付形式で入力してください（YYYY/MM/DD HH:mm:ss）'

    if start >= end:
        return '終了日時は開始日時以降の日時を入力してください'

    if (end - start) > timedelta(hours=24):
        return '取得期間は24時間以内で指定してください'

    return None


# ---------------------------------------------------------------------------
# validate_gadget_registration
# ---------------------------------------------------------------------------

def validate_gadget_registration(params):
    """ガジェット登録パラメータのバリデーション

    Args:
        params (dict): 登録パラメータ辞書

    Raises:
        ValidationError: バリデーション違反時
    """
    title           = params.get('title')
    device_mode     = params.get('device_mode')
    device_id       = params.get('device_id')
    group_id        = params.get('group_id')
    left_item_id    = params.get('left_item_id')
    right_item_id   = params.get('right_item_id')
    left_min_value  = params.get('left_min_value')
    left_max_value  = params.get('left_max_value')
    right_min_value = params.get('right_min_value')
    right_max_value = params.get('right_max_value')
    gadget_size     = params.get('gadget_size')

    # タイトル
    if title is None or title == '':
        raise ValidationError(err_required('タイトル'))
    if len(title) > 20:
        raise ValidationError(err_max_length('タイトル', 20))

    # デバイスID（デバイス固定モード時は必須）
    if device_mode == 'fixed' and device_id is None:
        raise ValidationError(err_select_required('デバイス'))

    # グループID
    if group_id is None:
        raise ValidationError(err_select_required('グループ'))

    # 表示項目
    if left_item_id is None:
        raise ValidationError(err_select_required('左表示項目'))
    if right_item_id is None:
        raise ValidationError(err_select_required('右表示項目'))

    # 最小値・最大値（数値形式チェック）
    def _to_float_or_none(value, field_label):
        if value is None or value == '':
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            raise ValidationError(err_numeric(field_label))

    left_min_f  = _to_float_or_none(left_min_value,  '左表示項目の最小値')
    left_max_f  = _to_float_or_none(left_max_value,  '左表示項目の最大値')
    right_min_f = _to_float_or_none(right_min_value, '右表示項目の最小値')
    right_max_f = _to_float_or_none(right_max_value, '右表示項目の最大値')

    # 最小値 < 最大値 チェック
    if left_min_f is not None and left_max_f is not None:
        if left_min_f >= left_max_f:
            raise ValidationError(err_min_less_than_max('左表示項目'))

    if right_min_f is not None and right_max_f is not None:
        if right_min_f >= right_max_f:
            raise ValidationError(err_min_less_than_max('右表示項目'))

    # 部品サイズ
    if gadget_size is None:
        raise ValidationError(err_select_required('部品サイズ'))
    if gadget_size not in _ALLOWED_GADGET_SIZES:
        raise ValidationError(err_invalid('部品サイズ'))


# ---------------------------------------------------------------------------
# format_timeline_data
# ---------------------------------------------------------------------------

def format_timeline_data(rows, left_column_name, right_column_name):
    """センサーデータ行を ECharts 用の labels/values 配列に変換する

    Args:
        rows: センサーデータ行のリスト（各行は dict-like）
        left_column_name:  左Y軸列名
        right_column_name: 右Y軸列名

    Returns:
        dict: {'labels': [...], 'left_values': [...], 'right_values': [...]}
    """
    labels       = []
    left_values  = []
    right_values = []

    for row in rows:
        labels.append(row['event_timestamp'].strftime(_DATETIME_FORMAT))
        left_values.append(row[left_column_name])
        right_values.append(row[right_column_name])

    return {'labels': labels, 'left_values': left_values, 'right_values': right_values}


# ---------------------------------------------------------------------------
# generate_timeline_csv
# ---------------------------------------------------------------------------

def generate_timeline_csv(rows, left_column_name, right_column_name, left_label, right_label):
    """センサーデータ行から CSV 文字列を生成する（UTF-8 BOM付き）

    Args:
        rows:              センサーデータ行のリスト
        left_column_name:  左表示項目列名
        right_column_name: 右表示項目列名
        left_label:        左表示項目ラベル（ヘッダー用）
        right_label:       右表示項目ラベル（ヘッダー用）

    Returns:
        str: BOM付き CSV 文字列
    """
    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow(['デバイス名', '時刻', left_label, right_label])

    for row in rows:
        writer.writerow([
            row['device_name'],
            row['event_timestamp'].strftime(_DATETIME_FORMAT),
            row[left_column_name],
            row[right_column_name],
        ])

    return '\ufeff' + output.getvalue()


# ---------------------------------------------------------------------------
# fetch_timeline_data
# ---------------------------------------------------------------------------

def fetch_timeline_data(device_id, start_datetime, end_datetime, left_item_id, right_item_id, limit=100):
    """センサーデータを取得する

    Args:
        device_id (int):        デバイスID
        start_datetime:         開始日時（datetime）
        end_datetime:           終了日時（datetime）
        left_item_id (int):     左軸測定項目ID
        right_item_id (int):    右軸測定項目ID
        limit (int):            最大取得件数（デフォルト 100）

    Returns:
        list: センサーデータ行のリスト

    Raises:
        Exception: センサークエリ失敗時（上位に伝播）
    """
    try:
        rows = execute_silver_query(
            device_id=device_id,
            start_datetime=start_datetime,
            end_datetime=end_datetime,
            limit=limit,
        )
        return rows
    except Exception:
        logger.error(
            f'時系列グラフデータ取得エラー: device_id={device_id}',
            exc_info=True,
        )
        raise


# ---------------------------------------------------------------------------
# register_gadget
# ---------------------------------------------------------------------------

def register_gadget(params, current_user_id=0):
    """ガジェットを登録する

    Args:
        params (dict):      登録パラメータ辞書
        current_user_id:    登録者のユーザーID

    Returns:
        int: 登録されたガジェットの gadget_id

    Raises:
        ValidationError:  バリデーション違反時
        IntegrityError:   DB 制約違反時（ロールバック後に再 raise）
    """
    validate_gadget_registration(params)

    device_id = params.get('device_id') if params.get('device_mode') == 'fixed' else None

    def _to_float_or_none(value):
        if value is None or value == '':
            return None
        return float(value)

    chart_config = json.dumps({
        'left_item_id':    params.get('left_item_id'),
        'right_item_id':   params.get('right_item_id'),
        'left_min_value':  _to_float_or_none(params.get('left_min_value')),
        'left_max_value':  _to_float_or_none(params.get('left_max_value')),
        'right_min_value': _to_float_or_none(params.get('right_min_value')),
        'right_max_value': _to_float_or_none(params.get('right_max_value')),
    })
    data_source_config = json.dumps({'device_id': device_id})

    group_id = params.get('group_id')

    max_position_y = db.session.query(
        func.max(DashboardGadgetMaster.position_y)
    ).filter(
        DashboardGadgetMaster.dashboard_group_id == group_id,
        DashboardGadgetMaster.delete_flag == False,
    ).scalar() or 0

    max_display_order = db.session.query(
        func.max(DashboardGadgetMaster.display_order)
    ).filter(
        DashboardGadgetMaster.dashboard_group_id == group_id,
        DashboardGadgetMaster.delete_flag == False,
    ).scalar() or 0

    gadget_type = db.session.query(GadgetTypeMaster).filter_by(
        gadget_type_name='時系列グラフ',
        delete_flag=False,
    ).first()
    if not gadget_type:
        raise NotFoundError('ガジェット種別が見つかりません')

    now = datetime.now()
    gadget = DashboardGadgetMaster(
        gadget_uuid=str(uuid.uuid4()),
        gadget_name=params.get('title'),
        gadget_type_id=gadget_type.gadget_type_id,
        dashboard_group_id=group_id,
        chart_config=chart_config,
        data_source_config=data_source_config,
        position_x=0,
        position_y=max_position_y + 1,
        gadget_size=GADGET_SIZE_TO_INT[params.get('gadget_size')],
        display_order=max_display_order + 1,
        create_date=now,
        update_date=now,
        creator=current_user_id,
        modifier=current_user_id,
    )

    try:
        db.session.add(gadget)
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        raise

    return gadget.gadget_id


# ---------------------------------------------------------------------------
# get_timeline_create_context
# ---------------------------------------------------------------------------

def get_timeline_create_context(accessible_org_ids, current_user_id):
    """時系列グラフガジェット登録モーダル用データを取得する

    Args:
        accessible_org_ids (list): アクセス可能な組織IDリスト
        current_user_id (int): 現在のユーザーID

    Returns:
        dict: measurement_items, organizations, devices, groups をキーに持つ dict

    Raises:
        NotFoundError: ユーザー設定またはダッシュボードが存在しない場合
    """
    from iot_app.models.measurement import MeasurementItemMaster
    from iot_app.models.organization import OrganizationMaster
    from iot_app.models.device import DeviceMaster
    from iot_app.models.customer_dashboard import DashboardUserSetting

    # ① ダッシュボードユーザー設定取得
    user_setting = db.session.query(DashboardUserSetting).filter_by(
        user_id=current_user_id,
        delete_flag=False,
    ).first()
    if user_setting is None:
        raise NotFoundError('ダッシュボードユーザー設定が見つかりません')
    dashboard_id = user_setting.dashboard_id

    # ② ダッシュボード情報取得（スコープ確認）
    dashboard = db.session.query(DashboardMaster).filter(
        DashboardMaster.dashboard_id == dashboard_id,
        DashboardMaster.organization_id.in_(accessible_org_ids),
        DashboardMaster.delete_flag == False,
    ).first()
    if dashboard is None:
        raise NotFoundError('ダッシュボードが見つかりません')

    # ③ 表示項目一覧取得
    measurement_items = db.session.query(MeasurementItemMaster).filter_by(
        delete_flag=False
    ).order_by(MeasurementItemMaster.measurement_item_id.asc()).all()

    # ④ 組織一覧取得
    organizations = db.session.query(OrganizationMaster).filter(
        OrganizationMaster.organization_id.in_(accessible_org_ids),
        OrganizationMaster.delete_flag == False,
    ).order_by(OrganizationMaster.organization_id.asc()).all()

    # ⑤ デバイス一覧取得
    devices = db.session.query(DeviceMaster).filter(
        DeviceMaster.organization_id.in_(accessible_org_ids),
        DeviceMaster.delete_flag == False,
    ).order_by(DeviceMaster.device_id.asc()).all()

    # ⑥ ダッシュボードグループ一覧取得（ユーザーのダッシュボードのみ）
    groups = db.session.query(DashboardGroupMaster).filter(
        DashboardGroupMaster.dashboard_id == dashboard_id,
        DashboardGroupMaster.delete_flag == False,
    ).order_by(DashboardGroupMaster.display_order.asc()).all()

    return {
        'measurement_items': measurement_items,
        'organizations': organizations,
        'devices': devices,
        'groups': groups,
    }


# ---------------------------------------------------------------------------
# export_timeline_csv
# ---------------------------------------------------------------------------

def export_timeline_csv(gadget_uuid, start_datetime, end_datetime, current_user_id=None):
    """時系列グラフガジェットの CSV エクスポート

    Args:
        gadget_uuid (str):      ガジェット UUID
        start_datetime:         開始日時（datetime または YYYY/MM/DD HH:mm:ss 文字列）
        end_datetime:           終了日時（datetime または YYYY/MM/DD HH:mm:ss 文字列）
        current_user_id (int):  現在のユーザーID（デバイス可変モード時に使用）

    Returns:
        str: UTF-8 BOM付き CSV 文字列

    Raises:
        ValidationError: パラメータ不正時
        NotFoundError:   ガジェット未検出時
        Exception:       データ取得失敗時
    """
    # start_datetime の正規化
    if isinstance(start_datetime, str):
        start_datetime_str = start_datetime
    elif start_datetime is None:
        start_datetime_str = None
    else:
        start_datetime_str = start_datetime.strftime(_DATETIME_FORMAT)

    # end_datetime の正規化
    if isinstance(end_datetime, str):
        end_datetime_str = end_datetime
    elif end_datetime is None:
        end_datetime_str = None
    else:
        end_datetime_str = end_datetime.strftime(_DATETIME_FORMAT)

    # 開始日時バリデーション
    if not end_datetime_str or not start_datetime_str:
        raise ValidationError(ERR_DATETIME_FORMAT)
    try:
        start_dt = datetime.strptime(start_datetime_str, _DATETIME_FORMAT)
        if start_dt.strftime(_DATETIME_FORMAT) != start_datetime_str:
            raise ValueError
    except (ValueError, TypeError):
        raise ValidationError(ERR_DATETIME_FORMAT)

    # 終了日時バリデーション
    try:
        end_dt = datetime.strptime(end_datetime_str, _DATETIME_FORMAT)
        if end_dt.strftime(_DATETIME_FORMAT) != end_datetime_str:
            raise ValueError
    except (ValueError, TypeError):
        raise ValidationError(ERR_DATETIME_FORMAT)

    # 開始 < 終了チェック
    if start_dt >= end_dt:
        raise ValidationError(ERR_END_BEFORE_START)

    # 24時間以内チェック
    if (end_dt - start_dt) > timedelta(hours=24):
        raise ValidationError(ERR_DATETIME_RANGE_24H)

    try:
        gadget = get_gadget_by_uuid(gadget_uuid)
        if gadget is None:
            raise NotFoundError(f'ガジェットが見つかりません: gadget_uuid={gadget_uuid}')

        data_source_config = json.loads(gadget.data_source_config or '{}')
        device_id = data_source_config.get('device_id')
        if not device_id:
            user_setting = get_dashboard_user_setting(current_user_id)
            device_id = user_setting.device_id if user_setting else None

        chart_config = json.loads(gadget.chart_config or '{}')
        left_item  = get_measurement_item(chart_config['left_item_id'])
        right_item = get_measurement_item(chart_config['right_item_id'])

        rows = fetch_timeline_data(
            device_id=device_id,
            start_datetime=start_dt,
            end_datetime=end_dt,
            left_item_id=chart_config['left_item_id'],
            right_item_id=chart_config['right_item_id'],
            limit=100000,
        )

        # [E] device_id → device_name マッピングを構築して各行に付加
        from iot_app.models.device import DeviceMaster
        device_ids = {row['device_id'] for row in rows}
        devices = db.session.query(DeviceMaster).filter(
            DeviceMaster.device_id.in_(device_ids)
        ).all()
        device_name_map = {d.device_id: d.device_name for d in devices}
        for row in rows:
            row['device_name'] = device_name_map.get(row['device_id'], '')

        return generate_timeline_csv(
            rows,
            left_column_name=left_item.silver_data_column_name,
            right_column_name=right_item.silver_data_column_name,
            left_label=left_item.display_name,
            right_label=right_item.display_name,
        )

    except ValidationError:
        raise
    except NotFoundError:
        raise
    except Exception:
        logger.error(
            f'時系列グラフCSVエクスポートエラー: gadget_uuid={gadget_uuid}',
            exc_info=True,
        )
        raise
