import csv
import io
import json
import uuid
from datetime import datetime

from sqlalchemy import func

from iot_app import db
from iot_app.common.exceptions import ValidationError
from iot_app.common.logger import get_logger
from iot_app.models.customer_dashboard import DashboardGadgetMaster, DashboardGroupMaster, GadgetTypeMaster

logger = get_logger(__name__)

PER_PAGE = 25


# ============================================================
# バリデーション
# ============================================================

def validate_chart_params(start_datetime_str, end_datetime_str):
    """開始・終了日時パラメータをバリデーションする

    Args:
        start_datetime_str (str): 開始日時文字列（YYYY/MM/DD HH:mm:ss）
        end_datetime_str (str): 終了日時文字列（YYYY/MM/DD HH:mm:ss）

    Returns:
        bool: 両パラメータが有効な形式かつ end > start の場合 True
    """
    if not start_datetime_str or not end_datetime_str:
        return False

    fmt = '%Y/%m/%d %H:%M:%S'
    try:
        start = datetime.strptime(start_datetime_str, fmt)
        end = datetime.strptime(end_datetime_str, fmt)
    except (ValueError, TypeError):
        return False

    # 終了日時は開始日時より後（設計書: 開始日時 < 終了日時、等値は不可）
    if end <= start:
        return False

    # 日時範囲の上限は24時間以内
    from datetime import timedelta
    if (end - start) > timedelta(hours=24):
        return False

    return True


# ============================================================
# データ整形
# ============================================================

def format_grid_data(rows, columns):
    """センサーデータを行ベースのリストに変換する

    Args:
        rows (list[dict]): クエリ結果行のリスト
        columns (list): MeasurementItemMaster オブジェクトのリスト

    Returns:
        list[dict]: 整形後の行データリスト
    """
    grid_data = []
    for row in rows:
        row_data = {
            'event_timestamp': row['event_timestamp'].strftime('%Y/%m/%d %H:%M:%S'),
            'device_name': row.get('device_name', ''),
        }
        for col in columns:
            row_data[col.silver_data_column_name] = row.get(col.silver_data_column_name)
        grid_data.append(row_data)
    return grid_data


# ============================================================
# ページング計算
# ============================================================

def calculate_page_offset(page, per_page=25):
    """ページ番号からオフセットを計算する

    Args:
        page (int): ページ番号（1以上）
        per_page (int): 1ページあたりの件数（デフォルト25）

    Returns:
        int: オフセット値

    Raises:
        ValueError: page が 1 未満の場合
    """
    if page <= 0:
        raise ValueError(f'page は 1 以上の整数でなければなりません: {page}')
    return (page - 1) * per_page


# ============================================================
# Unity Catalog クエリ
# ============================================================

def execute_silver_query(device_id, start_datetime, end_datetime, limit=1000, offset=0):
    """センサーデータを Silver 層 sensor_data_view から取得する

    Args:
        device_id (int): デバイスID
        start_datetime (datetime): 開始日時
        end_datetime (datetime): 終了日時
        limit (int): 最大取得件数（デフォルト1000、CSV時は100000）
        offset (int): オフセット（ページング用）

    Returns:
        list[dict]: クエリ結果行のリスト
    """
    # ── 開発用モック（削除予定）────────────────────────────────────────────
    # UC接続確認後（開発環境でも Unity Catalog に疎通できる状態になったら）以下ブロックごと削除すること
    import os
    if os.environ.get('FLASK_ENV') == 'development':
        from datetime import timedelta
        from iot_app import db
        from iot_app.models.device import DeviceMaster
        _device = db.session.query(DeviceMaster).filter_by(device_id=device_id, delete_flag=False).first()
        _MOCK_DEVICE_NAME = _device.device_name if _device else '--'
        from datetime import timedelta
        _TOTAL = 51
        _INTERVAL = timedelta(minutes=10)
        # end_datetime から遡る形で生成し昇順に並べ替える
        all_rows = []
        for i in range(_TOTAL):
            ts = end_datetime - _INTERVAL * (_TOTAL - 1 - i)
            all_rows.append({
                'event_timestamp':              ts,
                'device_name':                  _MOCK_DEVICE_NAME,
                'external_temp':                round(25.0 + i * 0.1, 1),
                'set_temp_freezer_1':           -18.0,
                'internal_sensor_temp_freezer_1': round(-17.8 + i * 0.05, 1),
                'internal_temp_freezer_1':      round(-18.2 - i * 0.02, 1),
                'df_temp_freezer_1':            round(-20.0 + i * 0.1, 1),
                'condensing_temp_freezer_1':    round(30.0 + i * 0.2, 1),
                'adjusted_internal_temp_freezer_1': round(-18.0 + i * 0.03, 1),
                'set_temp_freezer_2':           -15.0,
                'internal_sensor_temp_freezer_2': round(-14.8 + i * 0.05, 1),
                'internal_temp_freezer_2':      round(-15.2 - i * 0.02, 1),
                'df_temp_freezer_2':            round(-17.0 + i * 0.1, 1),
                'condensing_temp_freezer_2':    round(28.0 + i * 0.2, 1),
                'adjusted_internal_temp_freezer_2': round(-15.0 + i * 0.03, 1),
                'compressor_freezer_1':         1 if i % 3 != 2 else 0,
                'compressor_freezer_2':         1 if i % 4 != 3 else 0,
                'fan_motor_1':                  round(1200.0 + i * 5, 0),
                'fan_motor_2':                  round(1100.0 + i * 4, 0),
                'fan_motor_3':                  round(1050.0 + i * 3, 0),
                'fan_motor_4':                  round(980.0 + i * 2, 0),
                'fan_motor_5':                  round(950.0 + i * 1, 0),
                'defrost_heater_output_1':      round(45.0 + i * 0.5, 1),
                'defrost_heater_output_2':      round(42.0 + i * 0.4, 1),
            })
        # OFFSET と LIMIT を適用
        return all_rows[offset: offset + limit]
    # ── /開発用モック ──────────────────────────────────────────────────────

    from iot_app.databricks.unity_catalog_connector import UnityCatalogConnector
    connector = UnityCatalogConnector()
    sql = """
        SELECT
            event_timestamp,
            device_name,
            external_temp,
            set_temp_freezer_1,
            internal_sensor_temp_freezer_1,
            internal_temp_freezer_1,
            df_temp_freezer_1,
            condensing_temp_freezer_1,
            adjusted_internal_temp_freezer_1,
            set_temp_freezer_2,
            internal_sensor_temp_freezer_2,
            internal_temp_freezer_2,
            df_temp_freezer_2,
            condensing_temp_freezer_2,
            adjusted_internal_temp_freezer_2,
            compressor_freezer_1,
            compressor_freezer_2,
            fan_motor_1,
            fan_motor_2,
            fan_motor_3,
            fan_motor_4,
            fan_motor_5,
            defrost_heater_output_1,
            defrost_heater_output_2
        FROM iot_catalog.views.sensor_data_view
        WHERE device_id = :device_id
          AND event_timestamp BETWEEN :start_datetime AND :end_datetime
        ORDER BY event_timestamp ASC
        LIMIT :limit
        OFFSET :offset
    """
    return connector.execute(sql, {
        'device_id': device_id,
        'start_datetime': start_datetime,
        'end_datetime': end_datetime,
        'limit': limit,
        'offset': offset,
    }, operation='Silver層クエリ実行')


# ============================================================
# データ件数取得
# ============================================================

def count_grid_data(device_id, start_datetime, end_datetime):
    """センサーデータの総件数を取得する

    Args:
        device_id (int): デバイスID
        start_datetime (datetime): 開始日時
        end_datetime (datetime): 終了日時

    Returns:
        int: 総件数
    """
    # ── 開発用モック（削除予定）────────────────────────────────────────────
    # UC接続確認後（開発環境でも Unity Catalog に疎通できる状態になったら）以下ブロックごと削除すること
    import os
    if os.environ.get('FLASK_ENV') == 'development':
        return 51
    # ── /開発用モック ──────────────────────────────────────────────────────

    from iot_app.databricks.unity_catalog_connector import UnityCatalogConnector
    connector = UnityCatalogConnector()
    sql = """
        SELECT COUNT(*) AS cnt
        FROM iot_catalog.views.sensor_data_view
        WHERE device_id = :device_id
          AND event_timestamp BETWEEN :start_datetime AND :end_datetime
    """
    rows = connector.execute(sql, {
        'device_id': device_id,
        'start_datetime': start_datetime,
        'end_datetime': end_datetime,
    }, operation='Silver層件数クエリ実行')
    return rows[0]['cnt'] if rows else 0


# ============================================================
# データ取得
# ============================================================

def fetch_grid_data(device_id, start_datetime, end_datetime, limit=1000, offset=0):
    """センサーデータを取得する

    Args:
        device_id (int): デバイスID
        start_datetime (datetime): 開始日時
        end_datetime (datetime): 終了日時
        limit (int): 最大取得件数（デフォルト1000、CSV時は100000）
        offset (int): オフセット（ページング用、デフォルト0）

    Returns:
        list[dict]: クエリ結果行のリスト
    """
    return execute_silver_query(
        device_id=device_id,
        start_datetime=start_datetime,
        end_datetime=end_datetime,
        limit=limit,
        offset=offset,
    )


# ============================================================
# カラム定義取得
# ============================================================

def get_column_definition():
    """テーブル表示用カラム定義を measurement_item_master から取得する

    Returns:
        list[MeasurementItemMaster]: measurement_item_id 昇順のカラム定義リスト
    """
    from iot_app.models.measurement import MeasurementItemMaster
    return (
        db.session.query(MeasurementItemMaster)
        .filter(MeasurementItemMaster.delete_flag == False)
        .order_by(MeasurementItemMaster.measurement_item_id.asc())
        .all()
    )


# ============================================================
# ガジェット登録
# ============================================================

def register_grid_gadget(params, current_user_id):
    """表ガジェットを登録する

    Args:
        params (dict): 登録パラメータ（title, group_id, gadget_size）
        current_user_id (int): 操作ユーザーID

    Returns:
        DashboardGadgetMaster: 登録されたガジェットオブジェクト

    Raises:
        ValidationError: バリデーションエラー時
        Exception: DB エラー時
    """
    title = params.get('title')
    if not title:
        raise ValidationError('タイトルを入力してください')

    group_id = params.get('group_id')
    gadget_size = params.get('gadget_size')

    chart_config = json.dumps({})
    data_source_config = json.dumps({'device_id': None})

    max_position_y = db.session.query(
        func.max(DashboardGadgetMaster.position_y)
    ).filter(
        DashboardGadgetMaster.dashboard_group_id == group_id,
        DashboardGadgetMaster.delete_flag == False,
    ).scalar() or 0

    max_order = db.session.query(
        func.max(DashboardGadgetMaster.display_order)
    ).filter(
        DashboardGadgetMaster.dashboard_group_id == group_id,
        DashboardGadgetMaster.delete_flag == False,
    ).scalar() or 0

    gadget_type = db.session.query(GadgetTypeMaster).filter_by(
        gadget_type_name='表',
        delete_flag=False,
    ).first()
    gadget_type_id = gadget_type.gadget_type_id if gadget_type else None

    gadget = DashboardGadgetMaster(
        gadget_uuid=str(uuid.uuid4()),
        gadget_name=title,
        gadget_type_id=gadget_type_id,
        dashboard_group_id=group_id,
        chart_config=chart_config,
        data_source_config=data_source_config,
        position_x=0,
        position_y=max_position_y + 1,
        gadget_size=int(gadget_size) if gadget_size is not None else 0,
        display_order=max_order + 1,
        creator=current_user_id,
        modifier=current_user_id,
        delete_flag=False,
    )

    try:
        db.session.add(gadget)
        db.session.commit()
        return gadget
    except Exception:
        db.session.rollback()
        logger.error('表ガジェット登録エラー', exc_info=True)
        raise


# ============================================================
# 登録モーダル用コンテキスト取得
# ============================================================

def get_grid_create_context(dashboard_id):
    """表ガジェット登録モーダル用のデータを取得する

    Args:
        dashboard_id (int): ダッシュボードID

    Returns:
        dict: {'groups': [...]}
    """
    groups = (
        db.session.query(DashboardGroupMaster)
        .filter(
            DashboardGroupMaster.dashboard_id == dashboard_id,
            DashboardGroupMaster.delete_flag == False,
        )
        .order_by(DashboardGroupMaster.display_order.asc())
        .all()
    )
    return {'groups': groups}


# ============================================================
# CSV 生成
# ============================================================

def generate_grid_csv(grid_data, columns):
    """センサーデータから CSV 文字列を生成する（UTF-8 BOM付き）

    Args:
        grid_data (list[dict]): format_grid_data() で整形済みのデータリスト
        columns (list): MeasurementItemMaster オブジェクトのリスト

    Returns:
        str: BOM付き UTF-8 CSV 文字列
    """
    output = io.StringIO()
    writer = csv.writer(output)

    headers = ['受信日時', 'デバイス名称'] + [col.display_name for col in columns]
    writer.writerow(headers)

    for row_data in grid_data:
        row_values = [
            row_data.get('event_timestamp', ''),
            row_data.get('device_name', ''),
        ] + [row_data.get(col.silver_data_column_name, '') for col in columns]
        writer.writerow(row_values)

    return '\ufeff' + output.getvalue()
