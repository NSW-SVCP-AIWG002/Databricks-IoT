"""
業種別ダッシュボード機能（冷蔵冷凍庫） サービス層

対象機能:
- IDS-001: 店舗モニタリング画面
- IDS-002: デバイス詳細画面

参照:
- workflow-specification.md
- README.md (データモデル)
"""

import csv
import logging
from datetime import datetime, timedelta
from io import StringIO

from flask import make_response
from sqlalchemy import text

from src import db
from src.models.alert import AlertHistory, AlertLevelMaster, AlertSettingMaster, AlertStatusMaster
from src.models.device import Device, DeviceTypeMaster
from src.models.device_status import DeviceStatusData
from src.models.organization import Organization, OrganizationClosure

logger = logging.getLogger(__name__)

# 1ページあたりの表示件数
ITEM_PER_PAGE = 10

# アラート一覧取得上限
ALERT_FETCH_LIMIT = 30


# ---------------------------------------------------------------------------
# タスク2-1: データスコープ制限
# ---------------------------------------------------------------------------

def get_accessible_organizations(current_user_organization_id):
    """アクセス可能な組織IDリストを取得

    organization_closure テーブルを参照し、
    ユーザーの所属組織とその下位組織の organization_id 一覧を返す。

    Args:
        current_user_organization_id (int): ログインユーザーの organization_id

    Returns:
        list[int]: アクセス可能な organization_id のリスト
    """
    logger.info(f"データスコープ制限取得開始: organization_id={current_user_organization_id}")
    rows = db.session.query(
        OrganizationClosure.subsidiary_organization_id
    ).filter(
        OrganizationClosure.parent_organization_id == current_user_organization_id
    ).all()
    org_ids = [row[0] for row in rows]
    logger.info(f"データスコープ制限取得完了: 対象組織数={len(org_ids)}")
    return org_ids


# ---------------------------------------------------------------------------
# タスク2-2: デバイスアクセス権限チェック
# ---------------------------------------------------------------------------

def check_device_access(device_uuid, accessible_org_ids):
    """デバイスへのアクセス権限をチェック

    指定された device_uuid が、アクセス可能な組織に属するか確認する。

    Args:
        device_uuid (str): チェック対象デバイスの UUID
        accessible_org_ids (list[int]): アクセス可能な organization_id リスト

    Returns:
        Device | None: アクセス可能な場合はデバイスオブジェクト、不可の場合は None
    """
    if not accessible_org_ids:
        return None
    return db.session.query(Device).filter(
        Device.device_uuid == device_uuid,
        Device.organization_id.in_(accessible_org_ids),
        Device.delete_flag == False  # noqa: E712
    ).first()


# ---------------------------------------------------------------------------
# タスク2-3: アラート一覧取得（店舗モニタリング用）
# ---------------------------------------------------------------------------

def get_recent_alerts_with_count(search_params, accessible_org_ids, limit=ALERT_FETCH_LIMIT):
    """過去30日以内のアラート一覧と件数を取得（店舗モニタリング用）

    Args:
        search_params (dict): 検索条件 {"organization_name": str, "device_name": str}
        accessible_org_ids (list[int]): アクセス可能な organization_id リスト
        limit (int): 最大取得件数

    Returns:
        tuple[list, int]: (アラートリスト, 総件数)
    """
    if not accessible_org_ids:
        return [], 0

    organization_name = search_params.get("organization_name") or None
    device_name = search_params.get("device_name") or None

    base_query = (
        db.session.query(
            AlertHistory.alert_occurrence_datetime,
            Device.device_name,
            AlertSettingMaster.alert_name,
            AlertLevelMaster.alert_level_name,
            AlertStatusMaster.alert_status_name,
        )
        .join(AlertSettingMaster, (AlertHistory.alert_id == AlertSettingMaster.alert_id)
              & (AlertSettingMaster.delete_flag == False))  # noqa: E712
        .join(Device, (AlertSettingMaster.device_id == Device.device_id)
              & (Device.delete_flag == False))  # noqa: E712
        .join(Organization, (Device.organization_id == Organization.organization_id)
              & (Organization.delete_flag == False))  # noqa: E712
        .join(AlertLevelMaster, (AlertSettingMaster.alert_level_id == AlertLevelMaster.alert_level_id)
              & (AlertLevelMaster.delete_flag == False))  # noqa: E712
        .join(AlertStatusMaster, (AlertHistory.alert_status_id == AlertStatusMaster.alert_status_id)
              & (AlertStatusMaster.delete_flag == False))  # noqa: E712
        .filter(
            AlertHistory.delete_flag == False,  # noqa: E712
            Device.organization_id.in_(accessible_org_ids),
            AlertHistory.alert_occurrence_datetime >= text("DATE_ADD(NOW(), INTERVAL -30 DAY)"),
        )
    )

    if organization_name:
        base_query = base_query.filter(
            Organization.organization_name.like(f"%{organization_name}%")
        )
    if device_name:
        base_query = base_query.filter(
            Device.device_name.like(f"%{device_name}%")
        )

    logger.info("アラート一覧件数取得開始")
    total = base_query.count()
    total = min(total, limit)
    logger.info(f"アラート一覧件数取得完了: count={total}")

    logger.info("アラート一覧取得開始")
    alerts = (
        base_query
        .order_by(AlertHistory.alert_history_id.desc())
        .limit(limit)
        .all()
    )
    logger.info(f"アラート一覧取得完了: 件数={len(alerts)}")

    return alerts, total


# ---------------------------------------------------------------------------
# タスク2-4: デバイス一覧取得
# ---------------------------------------------------------------------------

def get_device_list_with_count(search_params, accessible_org_ids, page, per_page=ITEM_PER_PAGE):
    """デバイス一覧と件数を取得

    Args:
        search_params (dict): 検索条件 {"organization_name": str, "device_name": str}
        accessible_org_ids (list[int]): アクセス可能な organization_id リスト
        page (int): ページ番号（1始まり）
        per_page (int): 1ページあたりの件数

    Returns:
        tuple[list, int]: (デバイスリスト, 総件数)
    """
    if not accessible_org_ids:
        return [], 0

    organization_name = search_params.get("organization_name") or None
    device_name = search_params.get("device_name") or None

    base_query = (
        db.session.query(
            Device.device_uuid,
            Organization.organization_name,
            Device.device_name,
            DeviceStatusData.status,
        )
        .join(Organization, (Device.organization_id == Organization.organization_id)
              & (Organization.delete_flag == False))  # noqa: E712
        .join(DeviceStatusData, Device.device_status_id == DeviceStatusData.device_status_id,
              isouter=True)
        .filter(
            Device.delete_flag == False,  # noqa: E712
            Device.organization_id.in_(accessible_org_ids),
        )
    )

    if organization_name:
        base_query = base_query.filter(
            Organization.organization_name.like(f"%{organization_name}%")
        )
    if device_name:
        base_query = base_query.filter(
            Device.device_name.like(f"%{device_name}%")
        )

    logger.info("デバイス一覧件数取得開始")
    total = base_query.count()
    logger.info(f"デバイス一覧件数取得完了: count={total}")

    offset = (page - 1) * per_page

    logger.info("デバイス一覧取得開始")
    devices = (
        base_query
        .order_by(Device.organization_id.asc())
        .limit(per_page)
        .offset(offset)
        .all()
    )
    logger.info(f"デバイス一覧取得完了: 件数={len(devices)}")

    return devices, total


# ---------------------------------------------------------------------------
# タスク2-5: 最新センサーデータ取得（Unity Catalog）
# ---------------------------------------------------------------------------

def get_latest_sensor_data(device_id):
    """最新センサーデータを1件取得（Unity Catalog経由）

    Args:
        device_id (int): デバイスID

    Returns:
        Row | None: 最新センサーデータの行オブジェクト、存在しない場合は None
    """
    from src.db.unity_catalog_connector import get_unity_catalog_connection

    sql = """
        SELECT *
        FROM iot_catalog.views.sensor_data_view
        WHERE device_id = :device_id
        ORDER BY event_timestamp DESC
        LIMIT 1
    """
    logger.info(f"最新センサーデータ取得開始: device_id={device_id}")
    conn = get_unity_catalog_connection()
    try:
        result = conn.execute(text(sql), {"device_id": device_id})
        row = result.fetchone()
        logger.info(f"最新センサーデータ取得完了: device_id={device_id}, found={row is not None}")
        return row
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# タスク2-6: デバイス詳細アラート取得
# ---------------------------------------------------------------------------

def get_device_alerts_with_count(device_id, search_params):
    """特定デバイスのアラート一覧と件数を取得（デバイス詳細用）

    過去30日以内のアラート履歴を最大 ALERT_FETCH_LIMIT 件取得する。

    Args:
        device_id (int): デバイスID
        search_params (dict): 検索条件（page を含む）

    Returns:
        tuple[list, int]: (アラートリスト, 総件数)
    """
    page = search_params.get("page", 1)

    base_query = (
        db.session.query(
            AlertHistory.alert_occurrence_datetime,
            AlertSettingMaster.alert_name,
            AlertLevelMaster.alert_level_name,
            AlertStatusMaster.alert_status_name,
        )
        .join(AlertSettingMaster, (AlertHistory.alert_id == AlertSettingMaster.alert_id)
              & (AlertSettingMaster.delete_flag == False))  # noqa: E712
        .join(AlertLevelMaster, (AlertSettingMaster.alert_level_id == AlertLevelMaster.alert_level_id)
              & (AlertLevelMaster.delete_flag == False))  # noqa: E712
        .join(AlertStatusMaster, (AlertHistory.alert_status_id == AlertStatusMaster.alert_status_id)
              & (AlertStatusMaster.delete_flag == False))  # noqa: E712
        .filter(
            AlertHistory.delete_flag == False,  # noqa: E712
            AlertSettingMaster.device_id == device_id,
            AlertHistory.alert_occurrence_datetime >= text("DATE_ADD(NOW(), INTERVAL -30 DAY)"),
        )
    )

    logger.info(f"デバイス詳細アラート件数取得開始: device_id={device_id}")
    total = min(base_query.count(), ALERT_FETCH_LIMIT)
    logger.info(f"デバイス詳細アラート件数取得完了: count={total}")

    offset = (page - 1) * ITEM_PER_PAGE

    logger.info(f"デバイス詳細アラート取得開始: device_id={device_id}, page={page}")
    alerts = (
        base_query
        .order_by(AlertHistory.alert_history_id.desc())
        .limit(ITEM_PER_PAGE)
        .offset(offset)
        .all()
    )
    logger.info(f"デバイス詳細アラート取得完了: 件数={len(alerts)}")

    return alerts, total


# ---------------------------------------------------------------------------
# タスク2-7: グラフ用センサーデータ取得（Unity Catalog）
# ---------------------------------------------------------------------------

def get_graph_data(device_id, search_params):
    """時系列グラフ用センサーデータを取得（Unity Catalog経由）

    表示期間内の全センサーデータを昇順で取得する。

    Args:
        device_id (int): デバイスID
        search_params (dict): {"search_start_datetime": str, "search_end_datetime": str}

    Returns:
        list[Row]: センサーデータ行オブジェクトのリスト
    """
    from src.db.unity_catalog_connector import get_unity_catalog_connection

    start_dt = search_params.get("search_start_datetime", "")
    end_dt = search_params.get("search_end_datetime", "")

    sql = """
        SELECT *
        FROM iot_catalog.views.sensor_data_view
        WHERE device_id = :device_id
          AND event_timestamp BETWEEN :start_dt AND :end_dt
        ORDER BY event_timestamp ASC
    """
    logger.info(f"グラフ用センサーデータ取得開始: device_id={device_id}, "
                f"start={start_dt}, end={end_dt}")
    conn = get_unity_catalog_connection()
    try:
        result = conn.execute(text(sql), {
            "device_id": device_id,
            "start_dt": start_dt,
            "end_dt": end_dt,
        })
        rows = result.fetchall()
        logger.info(f"グラフ用センサーデータ取得完了: 件数={len(rows)}")
        return rows
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# タスク2-8: CSVエクスポート
# ---------------------------------------------------------------------------

def export_sensor_data_csv(device, search_params):
    """センサーデータをCSV形式でエクスポートする

    表示期間内の全センサーデータを取得し、CSV ファイルとして返す。

    Args:
        device (Device): エクスポート対象のデバイスオブジェクト
        search_params (dict): 検索条件（表示期間を含む）

    Returns:
        Response: CSV ダウンロードレスポンス
    """
    rows = get_graph_data(device.device_id, search_params)

    si = StringIO()
    writer = csv.writer(si)

    # ヘッダー行（workflow-specification.md「CSVエクスポート」記載の23カラム）
    writer.writerow([
        "イベント発生日時",
        "外気温度",
        "第1冷凍 設定温度",
        "第1冷凍 庫内センサー温度",
        "第1冷凍 庫内温度",
        "第1冷凍 DF温度",
        "第1冷凍 凝縮温度",
        "第1冷凍 微調整後庫内温度",
        "第2冷凍 設定温度",
        "第2冷凍 庫内センサー温度",
        "第2冷凍 庫内温度",
        "第2冷凍 DF温度",
        "第2冷凍 凝縮温度",
        "第2冷凍 微調整後庫内温度",
        "第1冷凍 圧縮機",
        "第2冷凍 圧縮機",
        "第1ファンモータ",
        "第2ファンモータ",
        "第3ファンモータ",
        "第4ファンモータ",
        "第5ファンモータ",
        "防露ヒータ出力(1)",
        "防露ヒータ出力(2)",
    ])

    # データ行
    for row in rows:
        writer.writerow([
            row.event_timestamp.strftime("%Y-%m-%d %H:%M:%S") if row.event_timestamp else "",
            row.external_temp if row.external_temp is not None else "",
            row.set_temp_freezer_1 if row.set_temp_freezer_1 is not None else "",
            row.internal_sensor_temp_freezer_1 if row.internal_sensor_temp_freezer_1 is not None else "",
            row.internal_temp_freezer_1 if row.internal_temp_freezer_1 is not None else "",
            row.df_temp_freezer_1 if row.df_temp_freezer_1 is not None else "",
            row.condensing_temp_freezer_1 if row.condensing_temp_freezer_1 is not None else "",
            row.adjusted_internal_temp_freezer_1 if row.adjusted_internal_temp_freezer_1 is not None else "",
            row.set_temp_freezer_2 if row.set_temp_freezer_2 is not None else "",
            row.internal_sensor_temp_freezer_2 if row.internal_sensor_temp_freezer_2 is not None else "",
            row.internal_temp_freezer_2 if row.internal_temp_freezer_2 is not None else "",
            row.df_temp_freezer_2 if row.df_temp_freezer_2 is not None else "",
            row.condensing_temp_freezer_2 if row.condensing_temp_freezer_2 is not None else "",
            row.adjusted_internal_temp_freezer_2 if row.adjusted_internal_temp_freezer_2 is not None else "",
            row.compressor_freezer_1 if row.compressor_freezer_1 is not None else "",
            row.compressor_freezer_2 if row.compressor_freezer_2 is not None else "",
            row.fan_motor_1 if row.fan_motor_1 is not None else "",
            row.fan_motor_2 if row.fan_motor_2 is not None else "",
            row.fan_motor_3 if row.fan_motor_3 is not None else "",
            row.fan_motor_4 if row.fan_motor_4 is not None else "",
            row.fan_motor_5 if row.fan_motor_5 is not None else "",
            row.defrost_heater_output_1 if row.defrost_heater_output_1 is not None else "",
            row.defrost_heater_output_2 if row.defrost_heater_output_2 is not None else "",
        ])

    output = make_response(si.getvalue())
    filename = (
        f"sensor_data_{device.device_uuid}_"
        f"{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    )
    output.headers["Content-Disposition"] = f"attachment; filename={filename}"
    output.headers["Content-type"] = "text/csv; charset=utf-8-sig"
    return output


# ---------------------------------------------------------------------------
# タスク2-9: デフォルト表示期間取得
# ---------------------------------------------------------------------------

def get_default_date_range():
    """デフォルトの表示期間を取得（直近24時間）

    Returns:
        dict: {"search_start_datetime": str, "search_end_datetime": str}
              フォーマット: YYYY-MM-DDTHH:MM
    """
    end_dt = datetime.now()
    start_dt = end_dt - timedelta(hours=24)
    return {
        "search_start_datetime": start_dt.strftime("%Y-%m-%dT%H:%M"),
        "search_end_datetime": end_dt.strftime("%Y-%m-%dT%H:%M"),
    }


# ---------------------------------------------------------------------------
# タスク2-10: 表示期間バリデーション
# ---------------------------------------------------------------------------

def validate_date_range(start_datetime_str, end_datetime_str):
    """表示期間のバリデーション

    Args:
        start_datetime_str (str): 開始日時文字列（YYYY-MM-DDTHH:MM）
        end_datetime_str (str): 終了日時文字列（YYYY-MM-DDTHH:MM）

    Returns:
        list[str]: エラーメッセージのリスト。空リストの場合はバリデーション成功。
    """
    errors = []

    try:
        start_dt = datetime.strptime(start_datetime_str, "%Y-%m-%dT%H:%M")
        end_dt = datetime.strptime(end_datetime_str, "%Y-%m-%dT%H:%M")
    except (ValueError, TypeError):
        errors.append("日時の形式が正しくありません")
        return errors

    if start_dt >= end_dt:
        errors.append("開始日時は終了日時より前である必要があります")

    if (end_dt - start_dt).days > 62:
        errors.append("表示期間は2ヶ月以内で指定してください")

    return errors
