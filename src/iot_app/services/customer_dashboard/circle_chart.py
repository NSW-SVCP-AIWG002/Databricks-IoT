"""
顧客作成ダッシュボード 円グラフガジェット - サービス層

参照設計書:
  - docs/03-features/flask-app/customer-dashboard/circle-chart/ui-specification.md
  - docs/03-features/flask-app/customer-dashboard/circle-chart/workflow-specification.md
"""

import json
import uuid

from sqlalchemy import func, text

from iot_app import db
from iot_app.models.customer_dashboard import DashboardGadgetMaster
from iot_app.models.device import DeviceMaster
from iot_app.models.measurement import MeasurementItemMaster
import iot_app.services.customer_dashboard.common as _common


# ---------------------------------------------------------------------------
# データ整形
# ---------------------------------------------------------------------------

def format_circle_chart_data(rows, columns):
    """センサーデータ行と表示項目定義からグラフ表示用データを整形する

    Args:
        rows (list[dict]): センサーデータ行リスト（最新1件を使用）
        columns (list[dict]): 表示項目定義リスト（silver_data_column_name, display_name）

    Returns:
        dict: {"labels": [...], "values": [...]}
    """
    if not rows:
        return {"labels": [], "values": []}
    row = rows[0]
    labels = []
    values = []
    for item in columns:
        column_name = item["silver_data_column_name"]
        value = row.get(column_name)
        labels.append(item["display_name"])
        values.append(value)
    return {"labels": labels, "values": values}


# ---------------------------------------------------------------------------
# ガジェット設定取得
# ---------------------------------------------------------------------------

def get_gadget_by_uuid(gadget_uuid):
    """gadget_uuid でガジェット設定を取得する

    Args:
        gadget_uuid (str): ガジェットUUID

    Returns:
        DashboardGadgetMaster or None
    """
    return (
        db.session.query(DashboardGadgetMaster)
        .filter(
            DashboardGadgetMaster.gadget_uuid == gadget_uuid,
            DashboardGadgetMaster.delete_flag == False,
        )
        .first()
    )


# ---------------------------------------------------------------------------
# センサーデータ取得
# ---------------------------------------------------------------------------

def fetch_circle_chart_data(device_id):
    """sensor_data_view から最新1件のセンサーデータを取得する

    Args:
        device_id (int): デバイスID

    Returns:
        list: クエリ結果行リスト（最大1件）
    """
    # ── 開発用モック（削除予定）────────────────────────────────────────────
    # UC接続確認後（開発環境でも Unity Catalog に疎通できる状態になったら）以下ブロックごと削除すること
    import os
    if os.getenv('FLASK_ENV') == 'development':
        col_names = [
            r.silver_data_column_name for r in db.session.query(
                MeasurementItemMaster.silver_data_column_name
            ).filter_by(delete_flag=False).all()
        ]
        row = {'device_id': device_id}
        for i, col in enumerate(col_names):
            row[col] = round(20.0 + i * 1.5, 1)
        return [row]
    # ── /開発用モック ──────────────────────────────────────────────────────

    sql = text("""
        SELECT event_timestamp, external_temp, set_temp_freezer_1,
               internal_sensor_temp_freezer_1, internal_temp_freezer_1,
               df_temp_freezer_1, condensing_temp_freezer_1,
               adjusted_internal_temp_freezer_1, set_temp_freezer_2,
               internal_sensor_temp_freezer_2, internal_temp_freezer_2,
               df_temp_freezer_2, condensing_temp_freezer_2,
               adjusted_internal_temp_freezer_2, compressor_freezer_1,
               compressor_freezer_2, fan_motor_1, fan_motor_2, fan_motor_3,
               fan_motor_4, fan_motor_5, defrost_heater_output_1,
               defrost_heater_output_2
        FROM iot_catalog.views.sensor_data_view
        WHERE device_id = :device_id
        ORDER BY event_timestamp DESC
        LIMIT 1
    """)
    return db.session.execute(sql, {"device_id": device_id}).fetchall()


# ---------------------------------------------------------------------------
# 凡例名取得
# ---------------------------------------------------------------------------

def get_column_definition():
    """measurement_item_master の全列定義を取得する

    Returns:
        list[MeasurementItemMaster]: 測定項目マスタ一覧（measurement_item_id昇順）
    """
    return (
        db.session.query(MeasurementItemMaster)
        .filter(MeasurementItemMaster.delete_flag == False)
        .order_by(MeasurementItemMaster.measurement_item_id)
        .all()
    )


# ---------------------------------------------------------------------------
# デバイス名取得
# ---------------------------------------------------------------------------

def get_device_name(device_id):
    """device_id からデバイス名を取得する

    Args:
        device_id (int or None): デバイスID

    Returns:
        str or None: デバイス名。デバイスが存在しない場合は None
    """
    device = (
        db.session.query(DeviceMaster)
        .filter(
            DeviceMaster.device_id == device_id,
            DeviceMaster.delete_flag == False,
        )
        .first()
    )
    return device.device_name if device else None


# ---------------------------------------------------------------------------
# ガジェット登録
# ---------------------------------------------------------------------------

def create_circle_chart_gadget(gadget_name, dashboard_group_id, chart_config, data_source_config, user_id):
    """円グラフガジェットを登録する

    Args:
        gadget_name (str): ガジェット名
        dashboard_group_id (int): ダッシュボードグループID
        chart_config (dict): チャート設定（{"item_id_1": 1, ...}）
        data_source_config (dict): データソース設定（{"device_id": int or None}）
        user_id (int): 操作ユーザーID

    Returns:
        DashboardGadgetMaster: 登録されたガジェットオブジェクト

    Raises:
        Exception: DB登録エラー時（rollback後に再raise）
    """
    from iot_app.models.customer_dashboard import GadgetTypeMaster

    try:
        max_position_y = (
            _common.db.session.query(func.max(DashboardGadgetMaster.position_y))
            .filter(DashboardGadgetMaster.dashboard_group_id == dashboard_group_id)
            .scalar()
        )
        max_display_order = (
            _common.db.session.query(func.max(DashboardGadgetMaster.display_order))
            .filter(DashboardGadgetMaster.dashboard_group_id == dashboard_group_id)
            .scalar()
        )
        position_y = (max_position_y or 0) + 1
        display_order = (max_display_order or 0) + 1

        gadget_type = (
            _common.db.session.query(GadgetTypeMaster)
            .filter_by(gadget_type_name='円グラフ', delete_flag=False)
            .first()
        )

        gadget = DashboardGadgetMaster(
            gadget_uuid=str(uuid.uuid4()),
            gadget_name=gadget_name,
            dashboard_group_id=dashboard_group_id,
            gadget_type_id=gadget_type.gadget_type_id,
            chart_config=json.dumps(chart_config),
            data_source_config=json.dumps(data_source_config),
            position_x=0,
            position_y=position_y,
            display_order=display_order,
            gadget_size=0,
            delete_flag=False,
            creator=user_id,
            modifier=user_id,
        )
        _common.db.session.add(gadget)
        _common.db.session.commit()
        return gadget
    except Exception:
        _common.db.session.rollback()
        raise
