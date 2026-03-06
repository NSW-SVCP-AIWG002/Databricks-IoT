"""
業種別ダッシュボードサービス

店舗モニタリング・デバイス詳細画面のビジネスロジック。
Unity Catalog (Databricks) および OLTP DB (MySQL/SQLite) へのアクセスを担当する。
"""

import csv
from datetime import datetime, timedelta
from io import StringIO

from flask import Response

from iot_app import db
from iot_app.databricks.unity_catalog_connector import get_databricks_connection
from iot_app.models.alert import (
    AlertHistory,
    AlertLevelMaster,
    AlertSettingMaster,
    AlertStatusMaster,
)
from iot_app.models.device import Device
from iot_app.models.organization import OrganizationClosure, OrganizationMaster

_ALERT_RECENT_DAYS = 30
_ITEM_PER_PAGE = 10
_SENSOR_DATA_VIEW = "iot_catalog.views.sensor_data_view"


# ---------------------------------------------------------------------------
# タスク2-10: 表示期間バリデーション
# ---------------------------------------------------------------------------


def validate_date_range(start_str, end_str):
    """表示期間のバリデーションを行い、エラーメッセージのリストを返す。

    Args:
        start_str: 開始日時文字列 (YYYY-MM-DDTHH:MM)
        end_str: 終了日時文字列 (YYYY-MM-DDTHH:MM)

    Returns:
        list[str]: エラーメッセージのリスト（エラーなしの場合は空リスト）
    """
    errors = []
    try:
        start_dt = datetime.strptime(start_str, "%Y-%m-%dT%H:%M")
        end_dt = datetime.strptime(end_str, "%Y-%m-%dT%H:%M")
    except (ValueError, TypeError):
        errors.append("日時の形式が正しくありません")
        return errors

    if start_dt >= end_dt:
        errors.append("開始日時は終了日時より前である必要があります")

    if (end_dt - start_dt).days > 62:
        errors.append("表示期間は2ヶ月以内で指定してください")

    return errors


# ---------------------------------------------------------------------------
# タスク2-9: デフォルト表示期間取得
# ---------------------------------------------------------------------------


def get_default_date_range():
    """直近24時間をデフォルト表示期間として返す。

    Returns:
        dict: search_start_datetime / search_end_datetime を含む辞書
              フォーマット: YYYY/MM/DDTHH:MM
    """
    end_dt = datetime.now()
    start_dt = end_dt - timedelta(hours=24)
    return {
        "search_start_datetime": start_dt.strftime("%Y/%m/%dT%H:%M"),
        "search_end_datetime": end_dt.strftime("%Y/%m/%dT%H:%M"),
    }


# ---------------------------------------------------------------------------
# タスク2-1: アクセス可能組織ID取得
# ---------------------------------------------------------------------------


def get_accessible_organizations(current_user_organization_id):
    """ユーザーの組織IDに基づいてアクセス可能な組織IDリストを返す。

    organization_closure テーブルから parent_organization_id で検索し、
    subsidiary_organization_id のリストを返す。

    Args:
        current_user_organization_id: ユーザーの組織ID

    Returns:
        list[int]: アクセス可能な組織IDのリスト
    """
    rows = (
        db.session.query(OrganizationClosure.subsidiary_organization_id)
        .filter(
            OrganizationClosure.parent_organization_id == current_user_organization_id
        )
        .all()
    )
    return [row[0] for row in rows]


# ---------------------------------------------------------------------------
# タスク2-2: デバイスアクセス権限チェック
# ---------------------------------------------------------------------------


def check_device_access(device_uuid, accessible_org_ids):
    """device_uuid がアクセス可能組織に属するかチェックし、Deviceを返す。

    Args:
        device_uuid: デバイスUUID
        accessible_org_ids: アクセス可能な組織IDリスト

    Returns:
        Device | None: アクセス可能な場合はDeviceオブジェクト、否の場合はNone
    """
    if not accessible_org_ids:
        return None
    return Device.query.filter(
        Device.device_uuid == device_uuid,
        Device.organization_id.in_(accessible_org_ids),
        Device.delete_flag == False,  # noqa: E712
    ).first()


# ---------------------------------------------------------------------------
# タスク2-3: アラート一覧取得（店舗モニタリング）
# ---------------------------------------------------------------------------


def get_recent_alerts_with_count(search_params, accessible_org_ids, limit=30):
    """過去30日以内のアラート履歴を取得する（店舗モニタリング用）。

    Args:
        search_params: 検索条件辞書 (organization_name, device_name)
        accessible_org_ids: アクセス可能な組織IDリスト
        limit: 最大取得件数（デフォルト30）

    Returns:
        tuple[list, int]: (アラートリスト, 総件数)
    """
    if not accessible_org_ids:
        return [], 0

    cutoff = datetime.now() - timedelta(days=_ALERT_RECENT_DAYS)

    q = (
        db.session.query(AlertHistory)
        .join(
            AlertStatusMaster,
            (AlertHistory.alert_status_id == AlertStatusMaster.alert_status_id)
            & (AlertStatusMaster.delete_flag == False),  # noqa: E712
            isouter=True,
        )
        .join(
            AlertSettingMaster,
            (AlertHistory.alert_id == AlertSettingMaster.alert_id)
            & (AlertSettingMaster.delete_flag == False),  # noqa: E712
            isouter=True,
        )
        .join(
            AlertLevelMaster,
            (AlertSettingMaster.alert_level_id == AlertLevelMaster.alert_level_id)
            & (AlertLevelMaster.delete_flag == False),  # noqa: E712
            isouter=True,
        )
        .join(
            Device,
            (AlertSettingMaster.device_id == Device.device_id)
            & (Device.delete_flag == False),  # noqa: E712
            isouter=True,
        )
        .join(
            OrganizationMaster,
            (Device.organization_id == OrganizationMaster.organization_id)
            & (OrganizationMaster.delete_flag == False),  # noqa: E712
            isouter=True,
        )
    )

    q = q.filter(
        AlertHistory.delete_flag == False,  # noqa: E712
        Device.organization_id.in_(accessible_org_ids),
        AlertHistory.alert_occurrence_datetime >= cutoff,
    )

    organization_name = search_params.get("organization_name", "")
    device_name = search_params.get("device_name", "")

    if organization_name:
        q = q.filter(
            OrganizationMaster.organization_name.like(f"%{organization_name}%")
        )
    if device_name:
        q = q.filter(Device.device_name.like(f"%{device_name}%"))

    total = q.count()
    results = q.order_by(AlertHistory.alert_history_id.desc()).limit(limit).all()

    return results, total


# ---------------------------------------------------------------------------
# タスク2-4: デバイス一覧取得（店舗モニタリング）
# ---------------------------------------------------------------------------


def get_device_list_with_count(search_params, accessible_org_ids, page, per_page=10):
    """デバイス一覧をページング付きで取得する（店舗モニタリング用）。

    Args:
        search_params: 検索条件辞書 (organization_name, device_name)
        accessible_org_ids: アクセス可能な組織IDリスト
        page: ページ番号（1始まり）
        per_page: 1ページあたりの件数（デフォルト10）

    Returns:
        tuple[list, int]: (デバイスリスト, 総件数)
    """
    if not accessible_org_ids:
        return [], 0

    q = db.session.query(Device).join(
        OrganizationMaster,
        (Device.organization_id == OrganizationMaster.organization_id)
        & (OrganizationMaster.delete_flag == False),  # noqa: E712
        isouter=True,
    )

    q = q.filter(
        Device.delete_flag == False,  # noqa: E712
        Device.organization_id.in_(accessible_org_ids),
    )

    organization_name = search_params.get("organization_name", "")
    device_name = search_params.get("device_name", "")

    if organization_name:
        q = q.filter(
            OrganizationMaster.organization_name.like(f"%{organization_name}%")
        )
    if device_name:
        q = q.filter(Device.device_name.like(f"%{device_name}%"))

    total = q.count()
    offset = (page - 1) * per_page
    results = (
        q.order_by(Device.organization_id.asc()).limit(per_page).offset(offset).all()
    )

    return results, total


# ---------------------------------------------------------------------------
# タスク2-6: デバイス別アラート一覧取得（デバイス詳細）
# ---------------------------------------------------------------------------


def get_device_alerts_with_count(device_id, search_params):
    """特定デバイスのアラート履歴をページング付きで取得する（デバイス詳細用）。

    Args:
        device_id: デバイスID
        search_params: 検索条件辞書 (page)

    Returns:
        tuple[list, int]: (アラートリスト, 総件数)
    """
    page = search_params.get("page", 1)
    per_page = _ITEM_PER_PAGE
    cutoff = datetime.now() - timedelta(days=_ALERT_RECENT_DAYS)

    q = (
        db.session.query(AlertHistory)
        .join(
            AlertStatusMaster,
            (AlertHistory.alert_status_id == AlertStatusMaster.alert_status_id)
            & (AlertStatusMaster.delete_flag == False),  # noqa: E712
            isouter=True,
        )
        .join(
            AlertSettingMaster,
            (AlertHistory.alert_id == AlertSettingMaster.alert_id)
            & (AlertSettingMaster.delete_flag == False),  # noqa: E712
            isouter=True,
        )
        .join(
            AlertLevelMaster,
            (AlertSettingMaster.alert_level_id == AlertLevelMaster.alert_level_id)
            & (AlertLevelMaster.delete_flag == False),  # noqa: E712
            isouter=True,
        )
    )

    q = q.filter(
        AlertHistory.delete_flag == False,  # noqa: E712
        AlertSettingMaster.device_id == device_id,
        AlertHistory.alert_occurrence_datetime >= cutoff,
    )

    total = q.count()
    offset = (page - 1) * per_page
    results = (
        q.order_by(AlertHistory.alert_history_id.desc())
        .limit(per_page)
        .offset(offset)
        .all()
    )

    return results, total


# ---------------------------------------------------------------------------
# タスク2-5: 最新センサーデータ取得
# ---------------------------------------------------------------------------


def get_latest_sensor_data(device_id):
    """Unity Catalog から最新センサーデータを1件取得する。

    Args:
        device_id: デバイスID

    Returns:
        row | None: 最新センサーデータ行、データなしの場合はNone
    """
    with get_databricks_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            f"SELECT * FROM {_SENSOR_DATA_VIEW}"
            " WHERE device_id = ?"
            " ORDER BY event_timestamp DESC"
            " LIMIT 1",
            [device_id],
        )
        return cursor.fetchone()


# ---------------------------------------------------------------------------
# タスク2-7: グラフ用センサーデータ取得
# ---------------------------------------------------------------------------


def get_graph_data(device_id, search_params):
    """Unity Catalog から表示期間内のセンサーデータを全件取得する（グラフ用）。

    Args:
        device_id: デバイスID
        search_params: 検索条件辞書 (search_start_datetime, search_end_datetime)

    Returns:
        list: センサーデータ行のリスト
    """
    start_str = search_params.get("search_start_datetime", "")
    end_str = search_params.get("search_end_datetime", "")

    with get_databricks_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            f"SELECT * FROM {_SENSOR_DATA_VIEW}"
            " WHERE device_id = ?"
            " AND event_timestamp BETWEEN ? AND ?"
            " ORDER BY event_timestamp ASC",
            [device_id, start_str, end_str],
        )
        return cursor.fetchall()


# ---------------------------------------------------------------------------
# 内部ヘルパー: 全センサーデータ取得（CSV用）
# ---------------------------------------------------------------------------


def get_all_sensor_data(device_id, search_params):
    """Unity Catalog から表示期間内の全センサーデータを取得する（CSV出力用）。

    Args:
        device_id: デバイスID
        search_params: 検索条件辞書 (search_start_datetime, search_end_datetime)

    Returns:
        list: センサーデータ行のリスト
    """
    start_str = search_params.get("search_start_datetime", "")
    end_str = search_params.get("search_end_datetime", "")

    with get_databricks_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            f"SELECT * FROM {_SENSOR_DATA_VIEW}"
            " WHERE device_id = ?"
            " AND event_timestamp BETWEEN ? AND ?"
            " ORDER BY event_timestamp ASC",
            [device_id, start_str, end_str],
        )
        return cursor.fetchall()


# ---------------------------------------------------------------------------
# タスク2-8: CSVエクスポート
# ---------------------------------------------------------------------------

_CSV_HEADERS = [
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
]


def _val(v):
    """None を空文字に変換する。0 など falsy な値はそのまま保持する。"""
    return "" if v is None else v


def export_sensor_data_csv(device, search_params):
    """センサーデータをUTF-8 BOM付きCSVとしてエクスポートする。

    Args:
        device: Deviceオブジェクト
        search_params: 検索条件辞書 (search_start_datetime, search_end_datetime)

    Returns:
        flask.Response: CSV レスポンス
    """
    sensor_data_list = get_all_sensor_data(device.device_id, search_params)

    si = StringIO()
    writer = csv.writer(si)
    writer.writerow(_CSV_HEADERS)

    for row in sensor_data_list:
        writer.writerow(
            [
                row.event_timestamp.strftime("%Y-%m-%d %H:%M:%S")
                if row.event_timestamp is not None
                else "",
                _val(row.external_temp),
                _val(row.set_temp_freezer_1),
                _val(row.internal_sensor_temp_freezer_1),
                _val(row.internal_temp_freezer_1),
                _val(row.df_temp_freezer_1),
                _val(row.condensing_temp_freezer_1),
                _val(row.adjusted_internal_temp_freezer_1),
                _val(row.set_temp_freezer_2),
                _val(row.internal_sensor_temp_freezer_2),
                _val(row.internal_temp_freezer_2),
                _val(row.df_temp_freezer_2),
                _val(row.condensing_temp_freezer_2),
                _val(row.adjusted_internal_temp_freezer_2),
                _val(row.compressor_freezer_1),
                _val(row.compressor_freezer_2),
                _val(row.fan_motor_1),
                _val(row.fan_motor_2),
                _val(row.fan_motor_3),
                _val(row.fan_motor_4),
                _val(row.fan_motor_5),
                _val(row.defrost_heater_output_1),
                _val(row.defrost_heater_output_2),
            ]
        )

    csv_data = si.getvalue().encode("utf-8-sig")
    filename = (
        f"sensor_data_{device.device_uuid}"
        f"_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    )

    return Response(
        csv_data,
        headers={
            "Content-Disposition": f"attachment; filename={filename}",
            "Content-type": "text/csv; charset=utf-8-sig",
        },
    )
