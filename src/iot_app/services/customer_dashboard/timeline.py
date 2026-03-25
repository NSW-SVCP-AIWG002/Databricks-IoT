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
from iot_app.common.logger import get_logger
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
    from iot_app.models.measurement import MeasurementItem
    chart_config = json.loads(gadget.chart_config)
    left_item  = db.session.get(MeasurementItem, chart_config['left_item_id'])
    right_item = db.session.get(MeasurementItem, chart_config['right_item_id'])
    if left_item is None or right_item is None:
        raise NotFoundError('測定項目が見つかりません')
    return left_item.silver_data_column_name, right_item.silver_data_column_name


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
    from iot_app.databricks.unity_catalog_connector import UnityCatalogConnector
    connector = UnityCatalogConnector()
    return connector.execute_query(
        device_id=device_id,
        start_datetime=start_datetime,
        end_datetime=end_datetime,
        limit=limit,
    )


# ---------------------------------------------------------------------------
# validate_chart_params
# ---------------------------------------------------------------------------

def validate_chart_params(start_datetime_str, end_datetime_str):
    """ガジェットデータ取得パラメータのバリデーション

    Args:
        start_datetime_str: 開始日時文字列（YYYY/MM/DD HH:mm:ss）
        end_datetime_str:   終了日時文字列（YYYY/MM/DD HH:mm:ss）

    Returns:
        bool: True = 正常、False = バリデーションエラー
    """
    if not start_datetime_str or not end_datetime_str:
        return False

    try:
        start = datetime.strptime(start_datetime_str, _DATETIME_FORMAT)
        end   = datetime.strptime(end_datetime_str,   _DATETIME_FORMAT)
    except ValueError:
        return False

    # 1桁月などの曖昧な表記を排除（strftime で再フォーマットして一致確認）
    if start.strftime(_DATETIME_FORMAT) != start_datetime_str:
        return False
    if end.strftime(_DATETIME_FORMAT) != end_datetime_str:
        return False

    if start >= end:
        return False

    if (end - start) > timedelta(hours=24):
        return False

    return True


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
        raise ValidationError('タイトルを入力してください')
    if len(title) > 20:
        raise ValidationError('タイトルは20文字以内で入力してください')

    # デバイスID（デバイス固定モード時は必須）
    if device_mode == 'fixed' and device_id is None:
        raise ValidationError('デバイスを選択してください')

    # グループID
    if group_id is None:
        raise ValidationError('グループを選択してください')

    # 表示項目
    if left_item_id is None:
        raise ValidationError('左表示項目を選択してください')
    if right_item_id is None:
        raise ValidationError('右表示項目を選択してください')

    # 最小値・最大値（数値形式チェック）
    def _to_float_or_none(value, field_label):
        if value is None or value == '':
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            raise ValidationError(f'{field_label}は数値で入力してください')

    left_min_f  = _to_float_or_none(left_min_value,  '左表示項目の最小値')
    left_max_f  = _to_float_or_none(left_max_value,  '左表示項目の最大値')
    right_min_f = _to_float_or_none(right_min_value, '右表示項目の最小値')
    right_max_f = _to_float_or_none(right_max_value, '右表示項目の最大値')

    # 最小値 < 最大値 チェック
    if left_min_f is not None and left_max_f is not None:
        if left_min_f >= left_max_f:
            raise ValidationError('左表示項目の最小値は最大値より小さい値を入力してください')

    if right_min_f is not None and right_max_f is not None:
        if right_min_f >= right_max_f:
            raise ValidationError('右表示項目の最小値は最大値より小さい値を入力してください')

    # 部品サイズ
    if gadget_size is None:
        raise ValidationError('部品サイズを選択してください')
    if gadget_size not in _ALLOWED_GADGET_SIZES:
        raise ValidationError('部品サイズが不正です')


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

    writer.writerow(['受信日時', 'デバイス名', left_label, right_label])

    for row in rows:
        writer.writerow([
            row['event_timestamp'].strftime(_DATETIME_FORMAT),
            row['device_name'],
            row[left_column_name],
            row[right_column_name],
        ])

    return '\ufeff' + output.getvalue()


# ---------------------------------------------------------------------------
# fetch_timeline_data
# ---------------------------------------------------------------------------

def fetch_timeline_data(gadget_uuid, start_datetime, end_datetime, limit=100, current_user_id=None):
    """ガジェット設定を取得し、センサーデータを返す

    Args:
        gadget_uuid:      ガジェット UUID
        start_datetime:   開始日時（datetime）
        end_datetime:     終了日時（datetime）
        limit:            最大取得件数（デフォルト 100）
        current_user_id:  現在のユーザーID（デバイス可変モード時に使用）

    Returns:
        list: センサーデータ行のリスト

    Raises:
        NotFoundError:  ガジェットが存在しない、または論理削除済みの場合
        Exception:      センサークエリ失敗時（上位に伝播）
    """
    gadget = db.session.query(DashboardGadgetMaster).filter_by(gadget_uuid=gadget_uuid).first()

    if gadget is None or gadget.delete_flag:
        raise NotFoundError(f'ガジェットが見つかりません: gadget_uuid={gadget_uuid}')

    data_source_config = json.loads(gadget.data_source_config)
    device_id = data_source_config.get('device_id')

    if device_id is None:
        user_setting = get_dashboard_user_setting(current_user_id)
        device_id = user_setting.device_id if user_setting else None

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
            f'時系列グラフデータ取得エラー: gadget_uuid={gadget_uuid}',
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
        gadget_size=params.get('gadget_size'),
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
    from iot_app.models.measurement import MeasurementItem
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
    measurement_items = db.session.query(MeasurementItem).filter_by(
        delete_flag=False
    ).order_by(MeasurementItem.measurement_item_id.asc()).all()

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
        raise ValidationError('正しい日付形式で入力してください（YYYY/MM/DD HH:mm:ss）')
    try:
        start_dt = datetime.strptime(start_datetime_str, _DATETIME_FORMAT)
        if start_dt.strftime(_DATETIME_FORMAT) != start_datetime_str:
            raise ValueError
    except (ValueError, TypeError):
        raise ValidationError('正しい日付形式で入力してください（YYYY/MM/DD HH:mm:ss）')

    # 終了日時バリデーション
    try:
        end_dt = datetime.strptime(end_datetime_str, _DATETIME_FORMAT)
        if end_dt.strftime(_DATETIME_FORMAT) != end_datetime_str:
            raise ValueError
    except (ValueError, TypeError):
        raise ValidationError('正しい日付形式で入力してください（YYYY/MM/DD HH:mm:ss）')

    # 開始 < 終了チェック
    if start_dt >= end_dt:
        raise ValidationError('終了日時は開始日時以降の日時を入力してください')

    # 24時間以内チェック
    if (end_dt - start_dt) > timedelta(hours=24):
        raise ValidationError('取得期間は24時間以内で指定してください')

    try:
        rows = fetch_timeline_data(
            gadget_uuid=gadget_uuid,
            start_datetime=start_dt,
            end_datetime=end_dt,
            limit=100000,
            current_user_id=current_user_id,
        )

        gadget = db.session.query(DashboardGadgetMaster).filter(
            DashboardGadgetMaster.gadget_uuid == gadget_uuid,
            DashboardGadgetMaster.delete_flag == False,
        ).first()
        chart_config = json.loads(gadget.chart_config)

        from iot_app.models.measurement import MeasurementItem
        left_item  = db.session.get(MeasurementItem, chart_config['left_item_id'])
        right_item = db.session.get(MeasurementItem, chart_config['right_item_id'])

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
