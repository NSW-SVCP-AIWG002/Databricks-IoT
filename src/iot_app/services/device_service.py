import csv
from datetime import datetime, timezone, timedelta
from io import StringIO

from flask import current_app
from sqlalchemy import or_

from iot_app import db
from iot_app.common.exceptions import NotFoundError
from iot_app.databricks.unity_catalog_connector import UnityCatalogConnector
from iot_app.models.device import DeviceMaster, DeviceMasterByUser, DeviceTypeMaster
from iot_app.models.device_status import DeviceStatusData
from iot_app.models.organization import OrganizationMaster, OrganizationMasterByUser
from iot_app.models.sort_item import SortItem

_ITEM_PER_PAGE = 25
_DEFAULT_DEVICE_DATA_INTERVAL_SECONDS = 60


class DuplicateDeviceIdError(Exception):
    pass


class DuplicateMacAddressError(Exception):
    pass


def get_default_search_params() -> dict:
    return {
        'page': 1,
        'per_page': _ITEM_PER_PAGE,
        'sort_by': '',
        'order': '',
        'device_id': '',
        'device_name': '',
        'device_type_id': None,
        'location': '',
        'organization_id': None,
        'certificate_expiration_date': '',
        'status': None,
    }


def search_devices(params: dict, user_id: int):
    query = DeviceMasterByUser.query.filter(
        DeviceMasterByUser.user_id == user_id,
        DeviceMasterByUser.delete_flag == False,
    )

    if params.get('device_id'):
        query = query.filter(
            DeviceMasterByUser.device_uuid.like(f"%{params['device_id']}%")
        )
    if params.get('device_name'):
        query = query.filter(
            DeviceMasterByUser.device_name.like(f"%{params['device_name']}%")
        )
    if params.get('device_type_id') is not None:
        query = query.filter(
            DeviceMasterByUser.device_type_id == params['device_type_id']
        )
    if params.get('location'):
        query = query.filter(
            DeviceMasterByUser.device_location.like(f"%{params['location']}%")
        )
    if params.get('organization_id') is not None:
        query = query.filter(
            DeviceMasterByUser.organization_id == params['organization_id']
        )
    if params.get('certificate_expiration_date'):
        query = query.filter(
            DeviceMasterByUser.certificate_expiration_date <= params['certificate_expiration_date']
        )
    if params.get('status'):
        try:
            interval = current_app.config.get(
                'DEVICE_DATA_INTERVAL_SECONDS', _DEFAULT_DEVICE_DATA_INTERVAL_SECONDS
            )
        except RuntimeError:
            interval = _DEFAULT_DEVICE_DATA_INTERVAL_SECONDS
        cutoff = datetime.now(timezone.utc) - timedelta(seconds=interval * 2)
        query = query.outerjoin(
            DeviceStatusData,
            DeviceMasterByUser.device_id == DeviceStatusData.device_id,
        )
        if params['status'] == 'connected':
            query = query.filter(DeviceStatusData.last_received_time >= cutoff)
        elif params['status'] == 'disconnected':
            query = query.filter(
                or_(
                    DeviceStatusData.last_received_time == None,
                    DeviceStatusData.last_received_time < cutoff,
                )
            )

    total = query.count()
    page = params.get('page', 1)
    per_page = params.get('per_page', _ITEM_PER_PAGE)
    offset = (page - 1) * per_page

    sort_by = params.get('sort_by')
    if sort_by:
        sort_col = getattr(DeviceMasterByUser, sort_by, None)
        if sort_col is not None:
            if params.get('order') == 'desc':
                query = query.order_by(sort_col.desc())
            else:
                query = query.order_by(sort_col.asc())
    else:
        query = query.order_by(DeviceMasterByUser.device_id)

    devices = query.limit(per_page).offset(offset).all()
    return devices, total


def create_device(data: dict, user_id: int):
    existing = DeviceMaster.query.filter_by(device_uuid=data.get('device_uuid'), delete_flag=False).first()
    if existing:
        raise DuplicateDeviceIdError(f"device_uuid '{data.get('device_uuid')}' は既に登録されています")

    if data.get('mac_address'):
        existing_mac = DeviceMaster.query.filter_by(mac_address=data['mac_address']).first()
        if existing_mac:
            raise DuplicateMacAddressError(f"mac_address '{data['mac_address']}' は既に登録されています")

    device = DeviceMaster(
        device_uuid=data.get('device_uuid'),
        device_name=data.get('device_name'),
        device_type_id=data.get('device_type_id'),
        device_model=data.get('device_model'),
        sim_id=data.get('sim_id'),
        mac_address=data.get('mac_address'),
        device_location=data.get('device_location'),
        organization_id=data.get('organization_id'),
        certificate_expiration_date=data.get('certificate_expiration_date'),
        creator=user_id,
        modifier=user_id,
    )

    try:
        db.session.add(device)
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise

    import os
    if os.getenv('FLASK_ENV') != 'development':
        # 開発環境向けスキップ（Unity Catalog に疎通できる環境になったら削除）
        try:
            uc = UnityCatalogConnector()
            uc.execute_dml(
                f"INSERT INTO device_master VALUES ({device.device_id}, '{device.device_uuid}')",
                {}
            )
        except Exception:
            db.session.delete(device)
            db.session.commit()
            raise

    return device


def get_device_by_uuid(device_uuid: str, user_id: int):
    return db.session.query(DeviceMasterByUser).filter(
        DeviceMasterByUser.device_uuid == device_uuid,
        DeviceMasterByUser.user_id == user_id,
        DeviceMasterByUser.delete_flag == False,
    ).first()


def update_device(device_uuid: str, data: dict, user_id: int) -> None:
    device = DeviceMaster.query.filter_by(device_uuid=device_uuid, delete_flag=False).first()
    if device is None:
        raise NotFoundError(f"device_uuid '{device_uuid}' が見つかりません")

    if data.get('mac_address'):
        existing_mac = DeviceMaster.query.filter_by(mac_address=data['mac_address']).first()
        if existing_mac and existing_mac.device_uuid != device_uuid:
            raise DuplicateMacAddressError(f"mac_address '{data['mac_address']}' は既に他のデバイスで使用されています")

    original = {
        'device_name': device.device_name,
        'device_type_id': device.device_type_id,
        'device_model': device.device_model,
        'sim_id': device.sim_id,
        'mac_address': device.mac_address,
        'device_location': device.device_location,
        'organization_id': device.organization_id,
        'certificate_expiration_date': device.certificate_expiration_date,
        'modifier': device.modifier,
    }

    device.device_name = data.get('device_name', device.device_name)
    device.device_type_id = data.get('device_type_id', device.device_type_id)
    device.device_model = data.get('device_model') or device.device_model
    device.sim_id = data.get('sim_id', device.sim_id)
    device.mac_address = data.get('mac_address', device.mac_address)
    device.device_location = data.get('device_location', device.device_location)
    device.organization_id = data.get('organization_id', device.organization_id)
    device.certificate_expiration_date = data.get(
        'certificate_expiration_date', device.certificate_expiration_date
    )
    device.modifier = user_id

    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise

    import os
    if os.getenv('FLASK_ENV') != 'development':
        # 開発環境向けスキップ（Unity Catalog に疎通できる環境になったら削除）
        try:
            uc = UnityCatalogConnector()
            uc.execute_dml(
                f"UPDATE device_master SET delete_flag = false WHERE device_id = {device.device_id}",
                {}
            )
        except Exception:
            for key, value in original.items():
                setattr(device, key, value)
            db.session.commit()
            raise


def delete_device(device, deleter_id: int) -> None:
    import os
    if os.getenv('FLASK_ENV') != 'development':
        # 開発環境向けスキップ（Unity Catalog に疎通できる環境になったら削除）
        uc = UnityCatalogConnector()
        uc.execute_dml(
            f"UPDATE device_master SET delete_flag = true WHERE device_uuid = '{device.device_uuid}'",
            {}
        )

    device.delete_flag = True
    device.modifier = deleter_id

    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        if os.getenv('FLASK_ENV') != 'development':
            try:
                uc.execute_dml(
                    f"UPDATE device_master SET delete_flag = false WHERE device_uuid = '{device.device_uuid}'",
                    {}
                )
            except Exception:
                pass
        raise


def _get_device_status_label(last_received_time) -> str:
    if last_received_time is None:
        return '未接続'
    try:
        interval = current_app.config.get(
            'DEVICE_DATA_INTERVAL_SECONDS', _DEFAULT_DEVICE_DATA_INTERVAL_SECONDS
        )
    except RuntimeError:
        interval = _DEFAULT_DEVICE_DATA_INTERVAL_SECONDS
    now = datetime.now(timezone.utc)
    elapsed = (now - last_received_time).total_seconds()
    if elapsed <= interval * 2:
        return '接続済み'
    return '未接続'


def generate_devices_csv(devices: list) -> bytes:
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow([
        'デバイスID', 'デバイス名', 'デバイス種別', '設置場所', '所属組織', '証明書期限', 'ステータス',
    ])
    for device, org_name, type_name, last_received_time in devices:
        cert = device.certificate_expiration_date
        writer.writerow([
            device.device_uuid or '',
            device.device_name or '',
            type_name or '',
            device.device_location or '',
            org_name or '',
            cert.strftime('%Y-%m-%d') if cert else '',
            _get_device_status_label(last_received_time),
        ])
    return b'\xef\xbb\xbf' + output.getvalue().encode('utf-8')


def get_device_status_map(device_ids: list) -> dict:
    if not device_ids:
        return {}
    rows = db.session.query(
        DeviceStatusData.device_id,
        DeviceStatusData.last_received_time,
    ).filter(DeviceStatusData.device_id.in_(device_ids)).all()
    return {device_id: _get_device_status_label(ts) for device_id, ts in rows}


def get_device_form_options(user_id: int):
    device_types = db.session.query(DeviceTypeMaster).filter_by(delete_flag=False).all()
    orgs = db.session.query(OrganizationMasterByUser).filter_by(user_id=user_id, delete_flag=False).all()
    sort_items = db.session.query(SortItem).filter_by(delete_flag=False).all()
    return device_types, orgs, sort_items


def get_all_devices_for_export(params: dict, user_id: int) -> list:
    query = db.session.query(
        DeviceMasterByUser,
        OrganizationMaster.organization_name,
        DeviceTypeMaster.device_type_name,
        DeviceStatusData.last_received_time,
    ).outerjoin(
        OrganizationMaster,
        DeviceMasterByUser.organization_id == OrganizationMaster.organization_id,
    ).outerjoin(
        DeviceTypeMaster,
        DeviceMasterByUser.device_type_id == DeviceTypeMaster.device_type_id,
    ).outerjoin(
        DeviceStatusData,
        DeviceMasterByUser.device_id == DeviceStatusData.device_id,
    ).filter(
        DeviceMasterByUser.user_id == user_id,
        DeviceMasterByUser.delete_flag == False,
    )

    if params.get('device_id'):
        query = query.filter(
            DeviceMasterByUser.device_uuid.like(f"%{params['device_id']}%")
        )
    if params.get('device_name'):
        query = query.filter(
            DeviceMasterByUser.device_name.like(f"%{params['device_name']}%")
        )
    if params.get('device_type_id') is not None:
        query = query.filter(
            DeviceMasterByUser.device_type_id == params['device_type_id']
        )
    if params.get('location'):
        query = query.filter(
            DeviceMasterByUser.device_location.like(f"%{params['location']}%")
        )
    if params.get('organization_id') is not None:
        query = query.filter(
            DeviceMasterByUser.organization_id == params['organization_id']
        )
    if params.get('certificate_expiration_date'):
        query = query.filter(
            DeviceMasterByUser.certificate_expiration_date <= params['certificate_expiration_date']
        )
    if params.get('status'):
        try:
            interval = current_app.config.get(
                'DEVICE_DATA_INTERVAL_SECONDS', _DEFAULT_DEVICE_DATA_INTERVAL_SECONDS
            )
        except RuntimeError:
            interval = _DEFAULT_DEVICE_DATA_INTERVAL_SECONDS
        cutoff = datetime.now(timezone.utc) - timedelta(seconds=interval * 2)
        if params['status'] == 'connected':
            query = query.filter(DeviceStatusData.last_received_time >= cutoff)
        elif params['status'] == 'disconnected':
            query = query.filter(
                or_(
                    DeviceStatusData.last_received_time == None,
                    DeviceStatusData.last_received_time < cutoff,
                )
            )

    return query.all()
