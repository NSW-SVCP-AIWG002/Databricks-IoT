"""
顧客作成ダッシュボード 帯グラフガジェット サービス

参照設計書:
  - docs/03-features/flask-app/customer-dashboard/belt-chart/workflow-specification.md
  - docs/03-features/flask-app/customer-dashboard/belt-chart/ui-specification.md
"""

import csv
import io
import json
import uuid
from datetime import datetime, timedelta

from sqlalchemy import func, text

from iot_app import db
from iot_app.common.exceptions import NotFoundError
from iot_app.common.logger import get_logger
from iot_app.models.customer_dashboard import DashboardGadgetMaster, GadgetTypeMaster, GoldSummaryMethodMaster
from iot_app.services.customer_dashboard.bar_chart import aggregate_values
from iot_app.services.customer_dashboard.common import check_device_access

logger = get_logger(__name__)

# 集計時間幅（分）マッピング
INTERVAL_MINUTES = {
    '1min': 1,
    '2min': 2,
    '3min': 3,
    '5min': 5,
    '10min': 10,
    '15min': 15,
}

_VALID_DISPLAY_UNITS = {'hour', 'day', 'week', 'month'}
_CSV_TIME_COL_HEADERS = {'hour': '時間', 'day': '時間', 'week': '曜日', 'month': '日付'}
_EN_WEEKDAY_OFFSET = {'Sun': 0, 'Mon': 1, 'Tue': 2, 'Wed': 3, 'Thu': 4, 'Fri': 5, 'Sat': 6}


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
        datetime.strptime(base_datetime_str, '%Y/%m/%d %H:%M:%S')
    except (ValueError, TypeError):
        return False

    return True


# ============================================================
# データ整形
# ============================================================

def format_belt_chart_data(rows, display_unit, measurement_items, interval='10min', summary_method_id=1):
    """取得データを ECharts 帯グラフ用 labels/series 配列に変換する

    Args:
        rows (list): クエリ結果行のリスト
        display_unit (str): 表示単位（hour/day/week/month）
        measurement_items (list): 表示項目リスト（dict のリスト）
        interval (str): 集計時間幅（display_unit=hour のみ使用）
        summary_method_id (int): 集約方法ID（display_unit=hour のみ使用）

    Returns:
        dict: {"labels": [...], "series": [{"name": ..., "values": [...]}, ...]}
    """
    if not rows:
        return {'labels': [], 'series': []}

    labels = []
    series = []

    if display_unit == 'hour':
        interval_min = INTERVAL_MINUTES.get(interval, 10)
        groups = {}
        for row in rows:
            dt = row['event_timestamp']
            bucket = dt.replace(
                minute=(dt.minute // interval_min) * interval_min,
                second=0,
                microsecond=0,
            )
            key = bucket.strftime('%H:%M')
            if key not in groups:
                groups[key] = {item['silver_data_column_name']: [] for item in measurement_items}
            for item in measurement_items:
                col = item['silver_data_column_name']
                groups[key][col].append(row.get(col))

        sorted_keys = sorted(groups.keys())
        labels = sorted_keys
        for item in measurement_items:
            col = item['silver_data_column_name']
            values = [aggregate_values(groups[k][col], summary_method_id) for k in sorted_keys]
            series.append({'name': item['display_name'], 'values': values})

    elif display_unit == 'day':
        hour_set = sorted({row['collection_hour'] for row in rows})
        labels = [f'{h:02d}' for h in hour_set]
        for item in measurement_items:
            item_id = item['measurement_item_id']
            hour_data = {h: None for h in hour_set}
            for row in rows:
                if row['summary_item'] == item_id:
                    hour_data[row['collection_hour']] = row['summary_value']
            values = [hour_data[h] for h in hour_set]
            series.append({'name': item['display_name'], 'values': values})

    elif display_unit in ('week', 'month'):
        date_set = sorted({row['collection_date'] for row in rows})
        if display_unit == 'week':
            labels = [d.strftime('%a') for d in date_set]
        else:
            labels = [d.strftime('%d') for d in date_set]
        for item in measurement_items:
            item_id = item['measurement_item_id']
            date_data = {d: None for d in date_set}
            for row in rows:
                if row['summary_item'] == item_id:
                    date_data[row['collection_date']] = row['summary_value']
            values = [date_data[d] for d in date_set]
            series.append({'name': item['display_name'], 'values': values})

    return {'labels': labels, 'series': series}


# ============================================================
# データ取得
# ============================================================

def fetch_belt_chart_data(device_id, display_unit, interval=None, base_datetime=None,
                           measurement_item_ids=None, summary_method_id=None, limit=100):
    """表示単位に応じたセンサーデータを取得する

    Args:
        device_id (int): デバイスID
        display_unit (str): 表示単位（hour/day/week/month）
        interval (str): 集計時間幅（display_unit=hour のみ使用）
        base_datetime (datetime): 基準日時
        measurement_item_ids (list): 表示項目IDリスト
        summary_method_id (int): 集約方法ID
        limit (int): 最大取得件数（デフォルト100）

    Returns:
        list[dict]: クエリ結果行のリスト
    """
    # ── 開発用モック（削除予定）────────────────────────────────────────────
    # UC接続確認後（開発環境でも Unity Catalog に疎通できる状態になったら）以下ブロックごと削除すること
    import os
    if os.environ.get('FLASK_ENV') == 'development':
        import calendar as _cal
        _ids = measurement_item_ids or []
        if display_unit == 'hour':
            _SILVER_COLS = [
                'external_temp', 'set_temp_freezer_1', 'internal_sensor_temp_freezer_1',
                'internal_temp_freezer_1', 'df_temp_freezer_1', 'condensing_temp_freezer_1',
                'adjusted_internal_temp_freezer_1', 'set_temp_freezer_2',
                'internal_sensor_temp_freezer_2', 'internal_temp_freezer_2',
                'df_temp_freezer_2', 'condensing_temp_freezer_2',
                'adjusted_internal_temp_freezer_2', 'compressor_freezer_1',
                'compressor_freezer_2', 'fan_motor_1', 'fan_motor_2', 'fan_motor_3',
                'fan_motor_4', 'fan_motor_5', 'defrost_heater_output_1',
                'defrost_heater_output_2',
            ]
            start = base_datetime.replace(minute=0, second=0, microsecond=0)
            rows = []
            for i in range(6):
                row = {'event_timestamp': start + timedelta(minutes=i * 10)}
                for j, col in enumerate(_SILVER_COLS):
                    row[col] = round(10.0 + j * 2.0 + i * 0.5, 1)
                rows.append(row)
            return rows
        elif display_unit == 'day':
            rows = []
            for item_id in _ids:
                for h in range(24):
                    rows.append({
                        'summary_item': item_id,
                        'collection_hour': h,
                        'summary_value': round(20.0 + h * 0.3 + item_id * 0.5, 1),
                    })
            return rows
        elif display_unit == 'week':
            days_since_sunday = (base_datetime.weekday() + 1) % 7
            start_date = (base_datetime - timedelta(days=days_since_sunday)).date()
            rows = []
            for item_id in _ids:
                for d in range(7):
                    rows.append({
                        'summary_item': item_id,
                        'collection_date': start_date + timedelta(days=d),
                        'summary_value': round(15.0 + d * 2.0 + item_id * 0.5, 1),
                    })
            return rows
        elif display_unit == 'month':
            start_date = base_datetime.replace(day=1).date()
            last_day = _cal.monthrange(base_datetime.year, base_datetime.month)[1]
            rows = []
            for item_id in _ids:
                for d in range(last_day):
                    rows.append({
                        'summary_item': item_id,
                        'collection_date': start_date.replace(day=d + 1),
                        'summary_value': round(10.0 + d * 0.8 + item_id * 0.5, 1),
                    })
            return rows
        return []
    # ── /開発用モック ──────────────────────────────────────────────────────

    if display_unit == 'hour':
        start_datetime = base_datetime.replace(minute=0, second=0, microsecond=0)
        end_datetime = start_datetime + timedelta(hours=1)
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
              AND event_timestamp BETWEEN :start_datetime AND :end_datetime
            ORDER BY event_timestamp ASC
            LIMIT :limit
        """)
        params = {
            'device_id': device_id,
            'start_datetime': start_datetime,
            'end_datetime': end_datetime,
            'limit': limit,
        }

    elif display_unit == 'day':
        target_date = base_datetime.date()
        ids_str = ','.join(str(i) for i in measurement_item_ids)
        sql = text(f"""
            SELECT summary_item, collection_hour, summary_value
            FROM iot_catalog.gold.gold_sensor_data_hourly_summary
            WHERE device_id = :device_id
              AND summary_item IN ({ids_str})
              AND summary_method_id = :summary_method_id
              AND collection_date = :target_date
            ORDER BY summary_item ASC, collection_hour ASC
            LIMIT :limit
        """)
        params = {
            'device_id': device_id,
            'summary_method_id': summary_method_id,
            'target_date': target_date,
            'limit': limit,
        }

    elif display_unit == 'week':
        weekday = base_datetime.weekday()
        days_since_sunday = (weekday + 1) % 7
        start_date = (base_datetime - timedelta(days=days_since_sunday)).date()
        end_date = start_date + timedelta(days=6)
        ids_str = ','.join(str(i) for i in measurement_item_ids)
        sql = text(f"""
            SELECT summary_item, collection_date, summary_value
            FROM iot_catalog.gold.gold_sensor_data_daily_summary
            WHERE device_id = :device_id
              AND summary_item IN ({ids_str})
              AND summary_method_id = :summary_method_id
              AND collection_date BETWEEN :start_date AND :end_date
            ORDER BY summary_item ASC, collection_date ASC
            LIMIT :limit
        """)
        params = {
            'device_id': device_id,
            'summary_method_id': summary_method_id,
            'start_date': start_date,
            'end_date': end_date,
            'limit': limit,
        }

    else:  # month
        import calendar
        start_date = base_datetime.replace(day=1).date()
        last_day = calendar.monthrange(base_datetime.year, base_datetime.month)[1]
        end_date = base_datetime.replace(day=last_day).date()
        ids_str = ','.join(str(i) for i in measurement_item_ids)
        sql = text(f"""
            SELECT summary_item, collection_date, summary_value
            FROM iot_catalog.gold.gold_sensor_data_daily_summary
            WHERE device_id = :device_id
              AND summary_item IN ({ids_str})
              AND summary_method_id = :summary_method_id
              AND collection_date BETWEEN :start_date AND :end_date
            ORDER BY summary_item ASC, collection_date ASC
            LIMIT :limit
        """)
        params = {
            'device_id': device_id,
            'summary_method_id': summary_method_id,
            'start_date': start_date,
            'end_date': end_date,
            'limit': limit,
        }

    rows = db.session.execute(sql, params).fetchall()
    return [dict(row) for row in rows]


# ============================================================
# CSV 生成
# ============================================================

def _csv_timestamp(label, display_unit, base_datetime):
    """chart_data のラベルを CSV 用フルタイムスタンプ文字列に変換する"""
    date_prefix = base_datetime.strftime('%Y/%m/%d')
    if display_unit == 'hour':
        return f'{date_prefix} {label}'
    elif display_unit == 'day':
        return f'{date_prefix} {label}:00'
    elif display_unit == 'week':
        days_since_sunday = (base_datetime.weekday() + 1) % 7
        start_date = (base_datetime - timedelta(days=days_since_sunday)).date()
        offset = _EN_WEEKDAY_OFFSET.get(label, 0)
        d = start_date + timedelta(days=offset)
        return d.strftime('%Y/%m/%d') + f'({label})'
    elif display_unit == 'month':
        return f"{base_datetime.strftime('%Y/%m/')}{label}"
    return label


def generate_belt_chart_csv(chart_data, display_unit, base_datetime, device_name):
    """チャートデータから CSV 文字列を生成する

    Args:
        chart_data (dict): {"labels": [...], "series": [{"name": ..., "values": [...]}, ...]}
        display_unit (str): 表示単位（hour/day/week/month）
        base_datetime (str): 基準日時（ISO 形式: YYYY-MM-DDTHH:mm:ss）
        device_name (str): デバイス名（列1）

    Returns:
        str: CSV 文字列（BOM付き UTF-8）
    """
    base_dt = datetime.fromisoformat(base_datetime)
    time_col = _CSV_TIME_COL_HEADERS.get(display_unit, '時間')
    series_names = [s['name'] for s in chart_data['series']]

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['デバイス名', time_col] + series_names)

    for i, label in enumerate(chart_data['labels']):
        ts = _csv_timestamp(label, display_unit, base_dt)
        row_values = []
        for s in chart_data['series']:
            v = s['values'][i]
            row_values.append('' if v is None else f'{v:.2f}')
        writer.writerow([device_name, ts] + row_values)

    return '\ufeff' + output.getvalue()


# ============================================================
# ガジェット登録
# ============================================================

def register_belt_chart_gadget(form_data, current_user_id, accessible_org_ids=None):
    """帯グラフガジェットを登録する

    Args:
        form_data (dict): 登録パラメータ
        current_user_id (int): 操作ユーザーID
        accessible_org_ids (list): アクセス可能組織IDリスト（device_mode=fixed 時に使用）

    Returns:
        str: 登録されたガジェットの gadget_uuid

    Raises:
        NotFoundError: デバイスまたはガジェット種別が見つからない場合
        Exception: DB エラー時
    """
    device_id = form_data.get('device_id')
    if form_data.get('device_mode') == 'fixed':
        device = check_device_access(device_id, accessible_org_ids)
        if device is None:
            raise NotFoundError('デバイスが見つかりません')

    group_id = form_data.get('group_id')

    chart_config = json.dumps({
        'measurement_item_ids': form_data.get('measurement_item_ids'),
        'summary_method_id': form_data.get('summary_method_id'),
    })
    data_source_config = json.dumps({'device_id': device_id})

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
        gadget_type_name='帯グラフ',
    ).first()
    if gadget_type is None:
        raise NotFoundError('ガジェット種別が見つかりません')

    gadget_uuid = str(uuid.uuid4())
    gadget = DashboardGadgetMaster(
        gadget_uuid=gadget_uuid,
        gadget_name=form_data.get('title'),
        gadget_type_id=gadget_type.gadget_type_id,
        dashboard_group_id=group_id,
        chart_config=chart_config,
        data_source_config=data_source_config,
        position_x=0,
        position_y=max_position_y + 1,
        gadget_size=form_data.get('gadget_size'),
        display_order=max_order + 1,
        creator=current_user_id,
        modifier=current_user_id,
        delete_flag=False,
    )

    try:
        db.session.add(gadget)
        db.session.commit()
        return gadget_uuid
    except Exception as e:
        db.session.rollback()
        logger.error('帯グラフガジェット登録エラー', exc_info=True)
        raise


# ============================================================
# マスタデータ取得
# ============================================================

def get_aggregation_methods():
    """集約方法一覧を取得する

    Returns:
        list[GoldSummaryMethodMaster]: 集約方法マスタのリスト
    """
    return db.session.query(GoldSummaryMethodMaster).filter(
        GoldSummaryMethodMaster.delete_flag == False,
    ).order_by(GoldSummaryMethodMaster.summary_method_id.asc()).all()
