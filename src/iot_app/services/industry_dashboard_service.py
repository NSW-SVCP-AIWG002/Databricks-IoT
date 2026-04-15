"""
業種別ダッシュボードサービス

店舗モニタリング・デバイス詳細画面のビジネスロジック。
OLTP DB (MySQL/SQLite) へのアクセスを担当する。

データスコープ制限は v_device_master_by_user / v_alert_history_by_user VIEW に
user_id を渡すことで自動適用される。ロールによる条件分岐は一切行わない。
"""

import csv
from datetime import datetime, timedelta, timezone
from io import StringIO

from flask import Response
from sqlalchemy import text

from iot_app import db
from iot_app.models.device_status import DeviceStatusData  # noqa: F401
from iot_app.models.measurement import MeasurementItemMaster, SilverSensorData  # noqa: F401

_JST = timezone(timedelta(hours=9))
_ALERT_RECENT_DAYS = 30
_ALERT_MAX_TOTAL = 30
_ITEM_PER_PAGE = 10


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
              フォーマット: YYYY-MM-DDTHH:MM
    """
    end_dt = datetime.now(_JST).replace(tzinfo=None)
    start_dt = end_dt - timedelta(hours=24)
    return {
        "search_start_datetime": start_dt.strftime("%Y-%m-%dT%H:%M"),
        "search_end_datetime": end_dt.strftime("%Y-%m-%dT%H:%M"),
    }


# ---------------------------------------------------------------------------
# 店舗名オートコンプリート
# ---------------------------------------------------------------------------


def search_organizations_by_name(name, user_id):
    """部分一致する組織名の一覧を返す（店舗名オートコンプリート用）。

    v_device_master_by_user VIEW に user_id を渡してデータスコープ制限を適用する。

    Args:
        name: 検索文字列（部分一致）
        user_id: ログインユーザーID

    Returns:
        list[dict]: {organization_id, organization_name} の辞書リスト
    """
    params = {"user_id": user_id}
    name_filter = ""
    if name:
        params["name"] = f"%{name}%"
        name_filter = "AND om.organization_name LIKE :name"

    rows = db.session.execute(
        text(f"""
            SELECT DISTINCT om.organization_id, om.organization_name
            FROM v_device_master_by_user v
            INNER JOIN organization_master om
              ON v.device_organization_id = om.organization_id
              AND om.delete_flag = FALSE
            WHERE v.user_id = :user_id
              AND v.delete_flag = FALSE
              {name_filter}
            ORDER BY om.organization_name ASC
        """),
        params,
    ).fetchall()

    return [
        {"organization_id": row[0], "organization_name": row[1]}
        for row in rows
    ]


# ---------------------------------------------------------------------------
# タスク2-2: デバイスアクセス権限チェック
# ---------------------------------------------------------------------------


def check_device_access(device_uuid, user_id):
    """device_uuid がユーザーのアクセス範囲に属するかチェックし、デバイス情報を返す。

    v_device_master_by_user VIEW に user_id を渡してデータスコープ制限を適用する。

    Args:
        device_uuid: デバイスUUID
        user_id: ログインユーザーID

    Returns:
        Row | None: アクセス可能な場合はデバイス情報の Row、否の場合はNone
    """
    return db.session.execute(
        text("""
            SELECT
                v.device_id,
                dm.device_uuid,
                v.device_name,
                dm.device_model,
                v.device_organization_id AS organization_id,
                dtm.device_type_name,
                om.organization_name
            FROM v_device_master_by_user v
            INNER JOIN device_master dm
              ON v.device_id = dm.device_id
            LEFT JOIN device_type_master dtm
              ON dm.device_type_id = dtm.device_type_id
              AND dtm.delete_flag = FALSE
            LEFT JOIN organization_master om
              ON v.device_organization_id = om.organization_id
              AND om.delete_flag = FALSE
            WHERE v.user_id = :user_id
              AND dm.device_uuid = :device_uuid
              AND v.delete_flag = FALSE
        """),
        {"user_id": user_id, "device_uuid": device_uuid},
    ).first()


# ---------------------------------------------------------------------------
# タスク2-3: アラート一覧取得（店舗モニタリング）
# ---------------------------------------------------------------------------


def get_recent_alerts_with_count(search_params, user_id, page=1, per_page=10):
    """過去30日以内のアラート履歴を取得する（店舗モニタリング用）。

    v_alert_history_by_user VIEW に user_id を渡してデータスコープ制限を適用する。

    Args:
        search_params: 検索条件辞書 (organization_id, organization_name, device_name)
        user_id: ログインユーザーID
        page: ページ番号（1始まり）
        per_page: 1ページあたりの件数（デフォルト10）

    Returns:
        tuple[list, int]: (アラートリスト, 総件数)
    """
    organization_id = search_params.get("organization_id", "")
    organization_name = search_params.get("organization_name", "")
    device_name = search_params.get("device_name", "")

    params = {"user_id": user_id, "days": _ALERT_RECENT_DAYS}
    extra_filters = ""

    if organization_id:
        params["organization_id"] = organization_id
        extra_filters += " AND dm.organization_id = :organization_id"
    elif organization_name:
        params["organization_name"] = f"%{organization_name}%"
        extra_filters += " AND om.organization_name LIKE :organization_name"
    if device_name:
        params["device_name"] = f"%{device_name}%"
        extra_filters += " AND dm.device_name LIKE :device_name"

    base_sql = f"""
        FROM v_alert_history_by_user v
        LEFT JOIN alert_status_master asm
          ON v.alert_status_id = asm.alert_status_id
          AND asm.delete_flag = FALSE
        LEFT JOIN alert_setting_master am
          ON v.alert_id = am.alert_id
          AND am.delete_flag = FALSE
        LEFT JOIN alert_level_master al
          ON am.alert_level_id = al.alert_level_id
          AND al.delete_flag = FALSE
        LEFT JOIN device_master dm
          ON v.device_id = dm.device_id
          AND dm.delete_flag = FALSE
        LEFT JOIN organization_master om
          ON dm.organization_id = om.organization_id
          AND om.delete_flag = FALSE
        WHERE v.user_id = :user_id
          AND v.delete_flag = FALSE
          AND v.alert_occurrence_datetime >= DATE_SUB(NOW(), INTERVAL :days DAY)
          {extra_filters}
    """

    count_row = db.session.execute(
        text(f"SELECT COUNT(v.alert_history_id) AS cnt {base_sql}"),
        params,
    ).first()
    total = min(count_row[0] if count_row else 0, _ALERT_MAX_TOTAL)

    offset = (page - 1) * per_page
    effective_limit = min(per_page, max(0, _ALERT_MAX_TOTAL - offset))
    if effective_limit <= 0:
        return [], total

    params["limit"] = effective_limit
    params["offset"] = offset
    rows = db.session.execute(
        text(f"""
            SELECT
                v.alert_history_id,
                v.alert_occurrence_datetime,
                dm.device_name,
                am.alert_name,
                al.alert_level_name,
                asm.alert_status_name,
                om.organization_name
            {base_sql}
            ORDER BY al.alert_level_id ASC, v.alert_history_id DESC
            LIMIT :limit OFFSET :offset
        """),
        params,
    ).fetchall()

    return rows, total


# ---------------------------------------------------------------------------
# タスク2-4: デバイス一覧取得（店舗モニタリング）
# ---------------------------------------------------------------------------


def get_device_list_with_count(search_params, user_id, page, per_page=10):
    """デバイス一覧をページング付きで取得する（店舗モニタリング用）。

    v_device_master_by_user VIEW に user_id を渡してデータスコープ制限を適用する。

    Args:
        search_params: 検索条件辞書 (organization_id, organization_name, device_name)
        user_id: ログインユーザーID
        page: ページ番号（1始まり）
        per_page: 1ページあたりの件数（デフォルト10）

    Returns:
        tuple[list, int]: (デバイスリスト, 総件数)
    """
    organization_id = search_params.get("organization_id", "")
    organization_name = search_params.get("organization_name", "")
    device_name = search_params.get("device_name", "")

    params = {"user_id": user_id}
    extra_filters = ""

    if organization_id:
        params["organization_id"] = organization_id
        extra_filters += " AND dm.organization_id = :organization_id"
    elif organization_name:
        params["organization_name"] = f"%{organization_name}%"
        extra_filters += " AND om.organization_name LIKE :organization_name"
    if device_name:
        params["device_name"] = f"%{device_name}%"
        extra_filters += " AND v.device_name LIKE :device_name"

    base_sql = f"""
        FROM v_device_master_by_user v
        INNER JOIN device_master dm
          ON v.device_id = dm.device_id
        LEFT JOIN organization_master om
          ON v.device_organization_id = om.organization_id
          AND om.delete_flag = FALSE
        LEFT JOIN device_status_data ds
          ON v.device_id = ds.device_id
        WHERE v.user_id = :user_id
          AND v.delete_flag = FALSE
          {extra_filters}
    """

    count_row = db.session.execute(
        text(f"SELECT COUNT(v.device_id) AS cnt {base_sql}"),
        params,
    ).first()
    total = count_row[0] if count_row else 0

    offset = (page - 1) * per_page
    params["limit"] = per_page
    params["offset"] = offset
    rows = db.session.execute(
        text(f"""
            SELECT
                v.device_id,
                dm.device_uuid,
                v.device_name,
                v.device_organization_id AS organization_id,
                om.organization_name
            {base_sql}
            ORDER BY v.device_organization_id ASC, v.device_id ASC
            LIMIT :limit OFFSET :offset
        """),
        params,
    ).fetchall()

    return rows, total


# ---------------------------------------------------------------------------
# タスク2-6: デバイス別アラート一覧取得（デバイス詳細）
# ---------------------------------------------------------------------------


def get_device_alerts_with_count(device_id, search_params, user_id):
    """特定デバイスのアラート履歴をページング付きで取得する（デバイス詳細用）。

    v_alert_history_by_user VIEW に user_id を渡してデータスコープ制限を適用する。

    Args:
        device_id: デバイスID
        search_params: 検索条件辞書 (page)
        user_id: ログインユーザーID

    Returns:
        tuple[list, int]: (アラートリスト, 総件数)
    """
    page = search_params.get("page", 1)
    per_page = _ITEM_PER_PAGE
    params = {"user_id": user_id, "device_id": device_id, "days": _ALERT_RECENT_DAYS}

    base_sql = """
        FROM v_alert_history_by_user v
        LEFT JOIN alert_status_master asm
          ON v.alert_status_id = asm.alert_status_id
          AND asm.delete_flag = FALSE
        LEFT JOIN alert_setting_master am
          ON v.alert_id = am.alert_id
          AND am.delete_flag = FALSE
        LEFT JOIN alert_level_master al
          ON am.alert_level_id = al.alert_level_id
          AND al.delete_flag = FALSE
        WHERE v.user_id = :user_id
          AND v.device_id = :device_id
          AND v.delete_flag = FALSE
          AND v.alert_occurrence_datetime >= DATE_SUB(NOW(), INTERVAL :days DAY)
    """

    count_row = db.session.execute(
        text(f"SELECT COUNT(v.alert_history_id) AS cnt {base_sql}"),
        params,
    ).first()
    total = min(count_row[0] if count_row else 0, _ALERT_MAX_TOTAL)

    offset = (page - 1) * per_page
    effective_limit = min(per_page, max(0, _ALERT_MAX_TOTAL - offset))
    if effective_limit <= 0:
        return [], total

    params["limit"] = effective_limit
    params["offset"] = offset
    rows = db.session.execute(
        text(f"""
            SELECT
                v.alert_history_id,
                v.alert_occurrence_datetime,
                am.alert_name,
                al.alert_level_name,
                asm.alert_status_name
            {base_sql}
            ORDER BY al.alert_level_id ASC, v.alert_history_id DESC
            LIMIT :limit OFFSET :offset
        """),
        params,
    ).fetchall()

    return rows, total


# ---------------------------------------------------------------------------
# タスク2-5: 最新センサーデータ取得
# ---------------------------------------------------------------------------


def get_latest_sensor_data(device_id):
    """最新センサーデータを1件取得する（MySQLのみ）。

    Args:
        device_id: デバイスID

    Returns:
        row | None: 最新センサーデータ行、データなしの場合はNone
    """
    return (
        db.session.query(SilverSensorData)
        .filter(SilverSensorData.device_id == device_id)
        .order_by(SilverSensorData.event_timestamp.desc())
        .first()
    )


# ---------------------------------------------------------------------------
# タスク2-7: グラフ用センサーデータ取得
# ---------------------------------------------------------------------------


def get_graph_data(device_id, search_params):
    """表示期間内のセンサーデータを全件取得する（グラフ用、MySQLのみ）。

    Args:
        device_id: デバイスID
        search_params: 検索条件辞書 (search_start_datetime, search_end_datetime)

    Returns:
        list: センサーデータ行のリスト（MySQLにデータがない場合は空リスト）
    """
    start_str = search_params.get("search_start_datetime", "")
    end_str = search_params.get("search_end_datetime", "")

    try:
        start_dt = datetime.strptime(start_str, "%Y-%m-%dT%H:%M")
        end_dt = datetime.strptime(end_str, "%Y-%m-%dT%H:%M")
    except (ValueError, TypeError):
        return []

    return _fetch_graph_data_from_mysql(device_id, start_dt, end_dt)


def _sensor_row_to_dict(row):
    """SilverSensorData ORM オブジェクトを JSON シリアライズ可能な dict に変換する。"""
    return {
        "event_timestamp": row.event_timestamp.strftime("%Y-%m-%d %H:%M:%S") if row.event_timestamp else None,
        "external_temp": row.external_temp,
        "set_temp_freezer_1": row.set_temp_freezer_1,
        "internal_sensor_temp_freezer_1": row.internal_sensor_temp_freezer_1,
        "internal_temp_freezer_1": row.internal_temp_freezer_1,
        "df_temp_freezer_1": row.df_temp_freezer_1,
        "condensing_temp_freezer_1": row.condensing_temp_freezer_1,
        "adjusted_internal_temp_freezer_1": row.adjusted_internal_temp_freezer_1,
        "set_temp_freezer_2": row.set_temp_freezer_2,
        "internal_sensor_temp_freezer_2": row.internal_sensor_temp_freezer_2,
        "internal_temp_freezer_2": row.internal_temp_freezer_2,
        "df_temp_freezer_2": row.df_temp_freezer_2,
        "condensing_temp_freezer_2": row.condensing_temp_freezer_2,
        "adjusted_internal_temp_freezer_2": row.adjusted_internal_temp_freezer_2,
        "compressor_freezer_1": row.compressor_freezer_1,
        "compressor_freezer_2": row.compressor_freezer_2,
        "fan_motor_1": row.fan_motor_1,
        "fan_motor_2": row.fan_motor_2,
        "fan_motor_3": row.fan_motor_3,
        "fan_motor_4": row.fan_motor_4,
        "fan_motor_5": row.fan_motor_5,
        "defrost_heater_output_1": row.defrost_heater_output_1,
        "defrost_heater_output_2": row.defrost_heater_output_2,
    }


def _fetch_graph_data_from_mysql(device_id, start_dt, end_dt):
    """MySQLからグラフ用センサーデータを取得する。"""
    rows = (
        db.session.query(SilverSensorData)
        .filter(
            SilverSensorData.device_id == device_id,
            SilverSensorData.event_timestamp >= start_dt,
            SilverSensorData.event_timestamp <= end_dt,
        )
        .order_by(SilverSensorData.event_timestamp.asc())
        .all()
    )
    return [_sensor_row_to_dict(row) for row in rows]


# ---------------------------------------------------------------------------
# 内部ヘルパー: 全センサーデータ取得（CSV用）
# ---------------------------------------------------------------------------


def get_all_sensor_data(device_id, search_params):
    """表示期間内の全センサーデータを取得する（CSV出力用、MySQLのみ）。

    Args:
        device_id: デバイスID
        search_params: 検索条件辞書 (search_start_datetime, search_end_datetime)

    Returns:
        list: センサーデータ行のリスト（MySQLにデータがない場合は空リスト）
    """
    return get_graph_data(device_id, search_params)


# ---------------------------------------------------------------------------
# タスク2-8: CSVエクスポート
# ---------------------------------------------------------------------------

_CSV_HEADERS = [
    "イベント発生日時",
    "外気温度",
    "第1冷凍 設定温度",
    "第1冷凍 庫内センサー温度",
    "第1冷凍 表示温度",
    "第1冷凍 DF温度",
    "第1冷凍 凝縮温度",
    "第1冷凍 微調整後庫内温度",
    "第2冷凍 設定温度",
    "第2冷凍 庫内センサー温度",
    "第2冷凍 表示温度",
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
        device: DeviceMasterオブジェクト
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
                row["event_timestamp"] if row.get("event_timestamp") is not None else "",
                _val(row.get("external_temp")),
                _val(row.get("set_temp_freezer_1")),
                _val(row.get("internal_sensor_temp_freezer_1")),
                _val(row.get("internal_temp_freezer_1")),
                _val(row.get("df_temp_freezer_1")),
                _val(row.get("condensing_temp_freezer_1")),
                _val(row.get("adjusted_internal_temp_freezer_1")),
                _val(row.get("set_temp_freezer_2")),
                _val(row.get("internal_sensor_temp_freezer_2")),
                _val(row.get("internal_temp_freezer_2")),
                _val(row.get("df_temp_freezer_2")),
                _val(row.get("condensing_temp_freezer_2")),
                _val(row.get("adjusted_internal_temp_freezer_2")),
                _val(row.get("compressor_freezer_1")),
                _val(row.get("compressor_freezer_2")),
                _val(row.get("fan_motor_1")),
                _val(row.get("fan_motor_2")),
                _val(row.get("fan_motor_3")),
                _val(row.get("fan_motor_4")),
                _val(row.get("fan_motor_5")),
                _val(row.get("defrost_heater_output_1")),
                _val(row.get("defrost_heater_output_2")),
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
