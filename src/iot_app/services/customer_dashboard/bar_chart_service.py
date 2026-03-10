import csv
import io
import json
import statistics
import uuid
from datetime import datetime, timedelta

from sqlalchemy import func

from iot_app import db
from iot_app.common.exceptions import NotFoundError, ValidationError
from iot_app.common.logger import get_logger
from iot_app.models.dashboard import DashboardGadgetMaster

logger = get_logger(__name__)

# 集計時間幅（分）マッピング
INTERVAL_MINUTES = {
    "1min": 1,
    "2min": 2,
    "3min": 3,
    "5min": 5,
    "10min": 10,
    "15min": 15,
}

_VALID_DISPLAY_UNITS = {"hour", "day", "week", "month"}
_VALID_GADGET_SIZES = {"2x2", "2x4"}


# ============================================================
# バリデーション
# ============================================================

def validate_chart_params(display_unit, interval, base_datetime_str):
    """チャートパラメータのバリデーション

    Returns:
        bool: 全パラメータが有効な場合 True、それ以外 False
    """
    if display_unit not in _VALID_DISPLAY_UNITS:
        return False

    if interval not in INTERVAL_MINUTES:
        return False

    if not base_datetime_str:
        return False

    try:
        datetime.strptime(base_datetime_str, "%Y/%m/%d %H:%M:%S")
    except (ValueError, TypeError):
        return False

    return True


def validate_gadget_registration(params):
    """ガジェット登録パラメータのバリデーション

    Args:
        params (dict): 登録パラメータ

    Raises:
        ValidationError: バリデーションエラー時
    """
    title = params.get("title")
    if not title and title != " ":
        if title is None or title == "":
            raise ValidationError("タイトルを入力してください")

    if title is not None and len(str(title)) > 20:
        raise ValidationError("タイトルは20文字以内で入力してください")

    device_mode = params.get("device_mode")
    if device_mode == "fixed":
        device_id = params.get("device_id")
        if device_id is None:
            raise ValidationError("デバイスを選択してください")

    if params.get("group_id") is None:
        raise ValidationError("グループを選択してください")

    if params.get("summary_method_id") is None:
        raise ValidationError("集約方法を選択してください")

    if params.get("measurement_item_id") is None:
        raise ValidationError("表示項目を選択してください")

    gadget_size = params.get("gadget_size")
    if gadget_size is None:
        raise ValidationError("部品サイズを選択してください")
    if gadget_size not in _VALID_GADGET_SIZES:
        raise ValidationError("部品サイズが不正です")

    min_value = params.get("min_value")
    max_value = params.get("max_value")

    if min_value is not None:
        try:
            min_value = float(min_value)
        except (TypeError, ValueError):
            raise ValidationError("最小値は数値で入力してください")

    if max_value is not None:
        try:
            max_value = float(max_value)
        except (TypeError, ValueError):
            raise ValidationError("最大値は数値で入力してください")

    if min_value is not None and max_value is not None:
        if min_value >= max_value:
            raise ValidationError(
                "最小値は最大値より小さい値を入力してください。最大値は最小値より大きい値を入力してください"
            )


# ============================================================
# データ集約
# ============================================================

def aggregate_values(values, summary_method_id):
    """値リストを集約方法IDに従って集約する

    Args:
        values (list): 集約対象の数値リスト
        summary_method_id (int): 集約方法ID

    Returns:
        float: 集約結果
    """
    if not values:
        return None

    numeric = [v for v in values if v is not None]
    if not numeric:
        return None

    if summary_method_id == 1:   # AVG
        return sum(numeric) / len(numeric)
    elif summary_method_id == 2:  # MAX
        return max(numeric)
    elif summary_method_id == 3:  # MIN
        return min(numeric)
    elif summary_method_id == 4:  # P25
        return statistics.quantiles(numeric, n=4)[0]
    elif summary_method_id == 5:  # MEDIAN
        return statistics.median(numeric)
    elif summary_method_id == 6:  # P75
        return statistics.quantiles(numeric, n=4)[2]
    elif summary_method_id == 7:  # STDDEV
        return statistics.stdev(numeric) if len(numeric) > 1 else 0.0
    elif summary_method_id == 8:  # P95
        return statistics.quantiles(numeric, n=20)[18]
    else:
        return sum(numeric) / len(numeric)


# ============================================================
# データ整形
# ============================================================

def format_bar_chart_data(rows, display_unit, interval="10min", summary_method_id=1, column_name=None):
    """取得データを ECharts 棒グラフ用 labels/values 配列に変換する

    Args:
        rows (list): クエリ結果行のリスト
        display_unit (str): 表示単位（hour/day/week/month）
        interval (str): 集計時間幅（display_unit=hour のみ使用）
        summary_method_id (int): 集約方法ID（display_unit=hour のみ使用）
        column_name (str): シルバー層カラム名（display_unit=hour のみ使用）

    Returns:
        dict: {"labels": [...], "values": [...]}
    """
    if not rows:
        return {"labels": [], "values": []}

    labels, values = [], []

    if display_unit == "hour":
        interval_min = INTERVAL_MINUTES.get(interval, 10)
        groups = {}
        for row in rows:
            dt = row["event_timestamp"]
            bucket = dt.replace(
                minute=(dt.minute // interval_min) * interval_min,
                second=0,
                microsecond=0,
            )
            key = bucket.strftime("%H:%M")
            groups.setdefault(key, []).append(row[column_name])
        for key in sorted(groups):
            labels.append(key)
            values.append(aggregate_values(groups[key], summary_method_id))

    elif display_unit == "day":
        for row in rows:
            labels.append(f"{row['collection_hour']:02d}:00")
            values.append(row["summary_value"])

    elif display_unit == "week":
        for row in rows:
            labels.append(row["collection_date"].strftime("%a"))
            values.append(row["summary_value"])

    elif display_unit == "month":
        for row in rows:
            labels.append(row["collection_date"].strftime("%d"))
            values.append(row["summary_value"])

    return {"labels": labels, "values": values}


# ============================================================
# CSV 生成
# ============================================================

def generate_bar_chart_csv(chart_data):
    """チャートデータから CSV 文字列を生成する

    Args:
        chart_data (dict): {"labels": [...], "values": [...]}

    Returns:
        str: CSV 文字列
    """
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["timestamp", "value"])
    for label, value in zip(chart_data["labels"], chart_data["values"]):
        writer.writerow([label, value])
    return output.getvalue()


# ============================================================
# Unity Catalog クエリ（スタブ：テストでモック差替え）
# ============================================================

def execute_silver_query(device_id, start_datetime, end_datetime):
    """シルバー層 sensor_data_view クエリ実行（Unity Catalog）

    Returns:
        list[dict]: クエリ結果行のリスト
    """
    from iot_app.databricks.unity_catalog_connector import UnityCatalogConnector
    connector = UnityCatalogConnector()
    sql = """
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
          AND event_timestamp BETWEEN :start_datetime AND :end_datetime
        ORDER BY event_timestamp ASC
    """
    return connector.execute(sql, {
        "device_id": device_id,
        "start_datetime": start_datetime,
        "end_datetime": end_datetime,
    })


def execute_gold_query(device_id, display_unit, measurement_item_id, summary_method_id,
                       start_date=None, end_date=None, target_date=None):
    """ゴールド層クエリ実行（Unity Catalog）

    Returns:
        list[dict]: クエリ結果行のリスト
    """
    from iot_app.databricks.unity_catalog_connector import UnityCatalogConnector
    connector = UnityCatalogConnector()

    if display_unit == "day":
        sql = """
            SELECT collection_hour, summary_value
            FROM iot_catalog.gold.gold_sensor_data_hourly_summary
            WHERE device_id = :device_id
              AND summary_item = :measurement_item_id
              AND summary_method_id = :summary_method_id
              AND collection_date = :target_date
            ORDER BY collection_hour ASC
        """
        return connector.execute(sql, {
            "device_id": device_id,
            "measurement_item_id": measurement_item_id,
            "summary_method_id": summary_method_id,
            "target_date": target_date,
        })
    else:
        sql = """
            SELECT collection_date, summary_value
            FROM iot_catalog.gold.gold_sensor_data_daily_summary
            WHERE device_id = :device_id
              AND summary_item = :measurement_item_id
              AND summary_method_id = :summary_method_id
              AND collection_date BETWEEN :start_date AND :end_date
            ORDER BY collection_date ASC
        """
        return connector.execute(sql, {
            "device_id": device_id,
            "measurement_item_id": measurement_item_id,
            "summary_method_id": summary_method_id,
            "start_date": start_date,
            "end_date": end_date,
        })


# ============================================================
# データ取得
# ============================================================

def fetch_bar_chart_data(device_id, display_unit, interval, base_datetime,
                         measurement_item_id, summary_method_id):
    """表示単位に応じたセンサーデータを取得する

    Args:
        device_id (int): デバイスID
        display_unit (str): 表示単位（hour/day/week/month）
        interval (str): 集計時間幅（display_unit=hour のみ使用）
        base_datetime (datetime): 基準日時
        measurement_item_id (int): 表示項目ID
        summary_method_id (int): 集約方法ID

    Returns:
        list[dict]: クエリ結果行のリスト

    Raises:
        Exception: クエリ実行失敗時
    """
    try:
        if display_unit == "hour":
            start_datetime = base_datetime.replace(minute=0, second=0, microsecond=0)
            end_datetime = start_datetime + timedelta(hours=1)
            return execute_silver_query(device_id, start_datetime, end_datetime)

        elif display_unit == "day":
            target_date = base_datetime.date()
            return execute_gold_query(
                device_id=device_id,
                display_unit="day",
                measurement_item_id=measurement_item_id,
                summary_method_id=summary_method_id,
                target_date=target_date,
            )

        elif display_unit == "week":
            # 当週の日曜〜土曜（weekday: 月=0, 日=6）
            weekday = base_datetime.weekday()
            days_since_sunday = (weekday + 1) % 7
            start_date = (base_datetime - timedelta(days=days_since_sunday)).date()
            end_date = start_date + timedelta(days=6)
            return execute_gold_query(
                device_id=device_id,
                display_unit="week",
                measurement_item_id=measurement_item_id,
                summary_method_id=summary_method_id,
                start_date=start_date,
                end_date=end_date,
            )

        elif display_unit == "month":
            import calendar
            start_date = base_datetime.replace(day=1).date()
            last_day = calendar.monthrange(base_datetime.year, base_datetime.month)[1]
            end_date = base_datetime.replace(day=last_day).date()
            return execute_gold_query(
                device_id=device_id,
                display_unit="month",
                measurement_item_id=measurement_item_id,
                summary_method_id=summary_method_id,
                start_date=start_date,
                end_date=end_date,
            )

        return []

    except Exception as e:
        logger.error(f"棒グラフデータ取得エラー: device_id={device_id}, error={str(e)}")
        raise


# ============================================================
# CSV エクスポート
# ============================================================

def export_bar_chart_csv(gadget_uuid, device_id, display_unit, interval,
                         base_datetime, measurement_item_id, summary_method_id):
    """棒グラフガジェットの CSV エクスポート

    Args:
        gadget_uuid (str): ガジェット UUID
        device_id (int): デバイスID
        display_unit (str): 表示単位
        interval (str): 集計時間幅
        base_datetime: 基準日時（datetime または YYYY/MM/DD HH:mm:ss 文字列）
        measurement_item_id (int): 表示項目ID
        summary_method_id (int): 集約方法ID

    Returns:
        str: CSV 文字列

    Raises:
        ValidationError: パラメータ不正時
        Exception: データ取得失敗時
    """
    # base_datetime が文字列の場合は文字列としてバリデーション
    if isinstance(base_datetime, str):
        base_datetime_str = base_datetime
    elif base_datetime is None:
        base_datetime_str = None
    else:
        base_datetime_str = base_datetime.strftime("%Y/%m/%d %H:%M:%S")

    # display_unit バリデーション
    if display_unit not in _VALID_DISPLAY_UNITS:
        raise ValidationError("表示単位が不正です")

    # interval バリデーション
    if interval not in INTERVAL_MINUTES:
        raise ValidationError("集計間隔が不正です")

    # base_datetime バリデーション
    if not base_datetime_str:
        raise ValidationError("日付形式が不正です")
    try:
        if isinstance(base_datetime, str):
            base_datetime = datetime.strptime(base_datetime_str, "%Y/%m/%d %H:%M:%S")
    except (ValueError, TypeError):
        raise ValidationError("日付形式が不正です")

    try:
        rows = fetch_bar_chart_data(
            device_id=device_id,
            display_unit=display_unit,
            interval=interval,
            base_datetime=base_datetime,
            measurement_item_id=measurement_item_id,
            summary_method_id=summary_method_id,
        )
        chart_data = format_bar_chart_data(
            rows, display_unit, interval, summary_method_id
        )
        return generate_bar_chart_csv(chart_data)

    except ValidationError:
        raise
    except Exception as e:
        logger.error(f"棒グラフCSVエクスポートエラー: gadget_uuid={gadget_uuid}, error={str(e)}")
        raise


# ============================================================
# デバイスアクセスチェック
# ============================================================

def check_device_access(device_id, accessible_org_ids):
    """デバイスの存在とデータスコープをチェックする

    Args:
        device_id (int): デバイスID
        accessible_org_ids (list): アクセス可能な組織IDリスト

    Returns:
        device object or None: デバイスが存在しアクセス可能な場合はデバイス、それ以外は None
    """
    from iot_app.models.device import DeviceMaster
    return (
        db.session.query(DeviceMaster)
        .filter(
            DeviceMaster.device_id == device_id,
            DeviceMaster.organization_id.in_(accessible_org_ids),
            DeviceMaster.delete_flag == False,
        )
        .first()
    )


# ============================================================
# ガジェット登録
# ============================================================

def register_bar_chart_gadget(params, current_user_id, accessible_org_ids=None):
    """棒グラフガジェットを登録する

    Args:
        params (dict): 登録パラメータ
        current_user_id (int): 操作ユーザーID
        accessible_org_ids (list): アクセス可能な組織IDリスト

    Returns:
        int: 登録されたガジェットの gadget_id

    Raises:
        ValidationError: バリデーションエラー時
        NotFoundError: デバイスが見つからない場合
        Exception: DB エラー時
    """
    if accessible_org_ids is None:
        accessible_org_ids = []

    # バリデーション
    validate_gadget_registration(params)

    # デバイス固定モードのデバイス存在チェック
    device_id = None
    if params.get("device_mode") == "fixed":
        device = check_device_access(params.get("device_id"), accessible_org_ids)
        if not device:
            raise NotFoundError("指定されたデバイスが見つかりません")
        device_id = params.get("device_id")

    chart_config = json.dumps({
        "measurement_item_id": params.get("measurement_item_id"),
        "summary_method_id": params.get("summary_method_id"),
        "min_value": params.get("min_value"),
        "max_value": params.get("max_value"),
    })
    data_source_config = json.dumps({"device_id": device_id})

    max_position_y = db.session.query(
        func.max(DashboardGadgetMaster.position_y)
    ).filter(
        DashboardGadgetMaster.dashboard_group_id == params.get("group_id"),
        DashboardGadgetMaster.delete_flag == False,
    ).scalar() or 0

    max_order = db.session.query(
        func.max(DashboardGadgetMaster.display_order)
    ).filter(
        DashboardGadgetMaster.dashboard_group_id == params.get("group_id"),
        DashboardGadgetMaster.delete_flag == False,
    ).scalar() or 0

    gadget = DashboardGadgetMaster(
        gadget_uuid=str(uuid.uuid4()),
        gadget_name=params.get("title"),
        gadget_type_id=1,
        dashboard_group_id=params.get("group_id"),
        chart_config=chart_config,
        data_source_config=data_source_config,
        position_x=0,
        position_y=max_position_y + 1,
        gadget_size=params.get("gadget_size"),
        display_order=max_order + 1,
        creator=current_user_id,
        modifier=current_user_id,
    )

    try:
        db.session.add(gadget)
        db.session.commit()
        return gadget.gadget_id
    except Exception as e:
        db.session.rollback()
        logger.error("棒グラフガジェット登録エラー", exc_info=True)
        raise
