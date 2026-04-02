"""
結合テスト共通フィクスチャ

全結合テストで使用する共通フィクスチャを定義する。
主な役割:
  - before_request フックで flask.g に認証済みユーザーをセットする。
  - 業種別ダッシュボード結合テスト用の実DBテストデータを投入・クリーンアップする。
"""

import uuid
from datetime import date, datetime, timedelta
from types import SimpleNamespace

import pytest


@pytest.fixture(autouse=True)
def inject_test_user(app):
    """各テストリクエストで g.current_user をセットする before_request フックを登録する。

    flask.g は LocalProxy であり、パッチでは差し替えできない。
    before_request フックで直接 g に属性をセットすることで、
    ビュー層が参照する g.current_user を正しく設定する。
    """
    from flask import g

    def _set_current_user():
        g.current_user = SimpleNamespace(
            user_id=1,
            user_type_id=1,
            organization_id=1,
            email_address="test@example.com",
        )
        g.current_user_id = 1
        g.databricks_token = ""

    # before_request_funcs の先頭に挿入（ミドルウェアより先に実行）
    app.before_request_funcs.setdefault(None, []).insert(0, _set_current_user)

    yield

    # テスト後にフックを削除してテスト間の干渉を防ぐ
    funcs = app.before_request_funcs.get(None, [])
    if _set_current_user in funcs:
        funcs.remove(_set_current_user)


@pytest.fixture(scope="class")
def industry_test_data(app):
    """業種別ダッシュボード結合テスト用実DBフィクスチャ。

    テスト用組織・デバイス・アラート・センサーデータを MySQL に投入し、
    テスト完了後に DELETE + COMMIT でクリーンアップする。
    （MySQL READ COMMITTED のためロールバック方式は使用しない）

    投入データ:
      - org_accessible  : アクセス可能組織（テスト対象ユーザーの組織）
      - org_sub         : org_accessible の下位組織
      - org_inaccessible: アクセス不可組織（closure 未登録）
      - device_accessible  : org_accessible 配下のデバイス（センサーデータあり）
      - device_sub         : org_sub 配下のデバイス（センサーデータなし）
      - device_inaccessible: org_inaccessible 配下のデバイス
      - アラート設定・履歴（device_accessible に紐づく）
      - silver_sensor_data（device_accessible の過去1時間分）

    fixture yield 後にテスト終了まで inject_test_user の organization_id を
    org_accessible.organization_id に override する before_request hook を登録する。
    """
    from flask import g

    from iot_app import db
    from iot_app.models.alert import (
        AlertHistory,
        AlertLevelMaster,
        AlertSettingMaster,
        AlertStatusMaster,
    )
    from iot_app.models.contract import ContractStatusMaster
    from iot_app.models.device import Device
    from iot_app.models.measurement import MeasurementItemMaster, SilverSensorData
    from iot_app.models.organization import (
        OrganizationClosure,
        OrganizationMaster,
        OrganizationTypeMaster,
    )

    # ------------------------------------------------------------------ #
    # 既存マスタデータの取得（FK に使用）
    # ------------------------------------------------------------------ #
    org_type = (
        db.session.query(OrganizationTypeMaster).filter_by(delete_flag=False).first()
    )
    contract_status = db.session.query(ContractStatusMaster).first()
    measurement_item = (
        db.session.query(MeasurementItemMaster).filter_by(delete_flag=False).first()
    )
    alert_level = (
        db.session.query(AlertLevelMaster).filter_by(delete_flag=False).first()
    )
    alert_status = (
        db.session.query(AlertStatusMaster).filter_by(delete_flag=False).first()
    )

    assert org_type is not None, "organization_type_master にレコードがありません"
    assert contract_status is not None, "contract_status_master にレコードがありません"
    assert measurement_item is not None, "measurement_item_master にレコードがありません"
    assert alert_level is not None, "alert_level_master にレコードがありません"
    assert alert_status is not None, "alert_status_master にレコードがありません"

    # ------------------------------------------------------------------ #
    # テストデータ投入
    # ------------------------------------------------------------------ #
    _C = 1  # creator / modifier
    now = datetime.now()
    today = date.today()
    uid = uuid.uuid4().hex[:12]

    # 組織
    org_accessible = OrganizationMaster(
        organization_name="テスト販社_結合テスト用",
        organization_type_id=org_type.organization_type_id,
        address="テスト住所_結合1",
        phone_number="000-0000-0001",
        contact_person="テスト担当者1",
        contract_status_id=contract_status.contract_status_id,
        contract_start_date=today,
        databricks_group_id=f"ti1_{uid[:8]}",
        creator=_C,
        modifier=_C,
    )
    org_sub = OrganizationMaster(
        organization_name="テストサブ組織_結合テスト用",
        organization_type_id=org_type.organization_type_id,
        address="テスト住所_結合2",
        phone_number="000-0000-0002",
        contact_person="テスト担当者2",
        contract_status_id=contract_status.contract_status_id,
        contract_start_date=today,
        databricks_group_id=f"ti2_{uid[:8]}",
        creator=_C,
        modifier=_C,
    )
    org_inaccessible = OrganizationMaster(
        organization_name="テストアクセス不可組織_結合テスト用",
        organization_type_id=org_type.organization_type_id,
        address="テスト住所_結合3",
        phone_number="000-0000-0003",
        contact_person="テスト担当者3",
        contract_status_id=contract_status.contract_status_id,
        contract_start_date=today,
        databricks_group_id=f"ti3_{uid[:8]}",
        creator=_C,
        modifier=_C,
    )
    db.session.add_all([org_accessible, org_sub, org_inaccessible])
    db.session.flush()

    # 組織クロージャ（org_accessible を親とする閉包）
    db.session.add_all([
        OrganizationClosure(
            parent_organization_id=org_accessible.organization_id,
            subsidiary_organization_id=org_accessible.organization_id,
            depth=0,
        ),
        OrganizationClosure(
            parent_organization_id=org_accessible.organization_id,
            subsidiary_organization_id=org_sub.organization_id,
            depth=1,
        ),
    ])

    # デバイス
    # device_master の実スキーマは ORM モデルと乖離があるため raw SQL で INSERT する。
    # 実DB制約: device_type_id NOT NULL, device_stock_id NOT NULL
    from sqlalchemy import text as _text

    test_uuid = f"test-acc-{uid}"
    test_sub_uuid = f"test-sub-{uid}"
    test_inacc_uuid = f"test-inacc-{uid}"

    # 既存の device_type_id / device_stock_id を動的に取得
    _dtype_row = db.session.execute(
        _text("SELECT device_type_id FROM device_type_master WHERE delete_flag=0 LIMIT 1")
    ).first()
    _stock_row = db.session.execute(
        _text("SELECT device_stock_id FROM device_stock_info_master LIMIT 1")
    ).first()
    assert _dtype_row, "device_type_master にレコードがありません"
    assert _stock_row, "device_stock_info_master にレコードがありません"
    _dtype_id = _dtype_row[0]
    _stock_id = _stock_row[0]

    _insert_device_sql = _text(
        "INSERT INTO device_master "
        "(device_uuid, organization_id, device_type_id, device_name, device_model, "
        "device_stock_id, creator, modifier) "
        "VALUES (:uuid, :org, :dtype, :name, :model, :stock, :c, :m)"
    )
    r1 = db.session.execute(_insert_device_sql, {
        "uuid": test_uuid, "org": org_accessible.organization_id,
        "dtype": _dtype_id, "name": "テストデバイス_結合テスト用",
        "model": "TEST-MODEL-001", "stock": _stock_id, "c": _C, "m": _C,
    })
    r2 = db.session.execute(_insert_device_sql, {
        "uuid": test_sub_uuid, "org": org_sub.organization_id,
        "dtype": _dtype_id, "name": "テストサブデバイス_結合テスト用",
        "model": "TEST-MODEL-002", "stock": _stock_id, "c": _C, "m": _C,
    })
    r3 = db.session.execute(_insert_device_sql, {
        "uuid": test_inacc_uuid, "org": org_inaccessible.organization_id,
        "dtype": _dtype_id, "name": "テストアクセス不可デバイス_結合テスト用",
        "model": "TEST-MODEL-003", "stock": _stock_id, "c": _C, "m": _C,
    })
    device_acc_id = r1.lastrowid
    device_sub_id = r2.lastrowid
    device_inacc_id = r3.lastrowid

    # アラート設定（device_acc_id に紐づく）
    _mid = measurement_item.measurement_item_id
    alert_setting = AlertSettingMaster(
        alert_uuid=str(uuid.uuid4()),
        alert_name="テストアラート_結合テスト用",
        device_id=device_acc_id,
        alert_conditions_measurement_item_id=_mid,
        alert_conditions_operator=">=",
        alert_conditions_threshold=10.0,
        alert_recovery_conditions_measurement_item_id=_mid,
        alert_recovery_conditions_operator="<",
        alert_recovery_conditions_threshold=5.0,
        alert_level_id=alert_level.alert_level_id,
        creator=_C,
        modifier=_C,
    )
    db.session.add(alert_setting)
    db.session.flush()

    # アラート履歴（過去1時間以内 → 30日以内フィルタに引っかかる）
    db.session.add(AlertHistory(
        alert_history_uuid=str(uuid.uuid4()),
        alert_id=alert_setting.alert_id,
        alert_occurrence_datetime=now - timedelta(hours=1),
        alert_status_id=alert_status.alert_status_id,
        alert_value=15.0,
        creator=_C,
        modifier=_C,
    ))

    # センサーデータ（device_acc_id の過去1時間分）
    # 実DB: create_time はデフォルト値なし → 明示的に指定する
    db.session.add(SilverSensorData(
        device_id=device_acc_id,
        organization_id=org_accessible.organization_id,
        event_timestamp=now - timedelta(hours=1),
        event_date=today,
        external_temp=-18.5,
        create_time=now,
    ))

    db.session.commit()

    # ------------------------------------------------------------------ #
    # inject_test_user の organization_id を org_accessible に override
    # ------------------------------------------------------------------ #
    accessible_org_id = org_accessible.organization_id

    def _override_org():
        if hasattr(g, "current_user"):
            g.current_user.organization_id = accessible_org_id

    # inject_test_user が index=0 に挿入するため、append で後続実行させる
    app.before_request_funcs.setdefault(None, []).append(_override_org)

    # ------------------------------------------------------------------ #
    # yield（テストへデータを提供）
    # ------------------------------------------------------------------ #
    yield {
        "org_accessible_id": org_accessible.organization_id,
        "org_sub_id": org_sub.organization_id,
        "org_inaccessible_id": org_inaccessible.organization_id,
        "device_uuid": test_uuid,
        "device_id": device_acc_id,
        "device_name": "テストデバイス_結合テスト用",
        "device_sub_uuid": test_sub_uuid,
        "device_sub_name": "テストサブデバイス_結合テスト用",
        "device_inaccessible_uuid": test_inacc_uuid,
        "org_accessible_name": "テスト販社_結合テスト用",
        "org_sub_name": "テストサブ組織_結合テスト用",
        "alert_name": "テストアラート_結合テスト用",
        "sensor_timestamp": now - timedelta(hours=1),
    }

    # ------------------------------------------------------------------ #
    # クリーンアップ（FK 逆順削除）
    # ------------------------------------------------------------------ #
    funcs = app.before_request_funcs.get(None, [])
    if _override_org in funcs:
        funcs.remove(_override_org)

    all_device_ids = [device_acc_id, device_sub_id, device_inacc_id]

    db.session.query(SilverSensorData).filter(
        SilverSensorData.device_id.in_(all_device_ids)
    ).delete(synchronize_session=False)

    db.session.query(AlertHistory).filter(
        AlertHistory.alert_id == alert_setting.alert_id
    ).delete(synchronize_session=False)

    db.session.query(AlertSettingMaster).filter(
        AlertSettingMaster.device_id.in_(all_device_ids)
    ).delete(synchronize_session=False)

    db.session.execute(
        _text("DELETE FROM device_master WHERE device_uuid IN :uuids"),
        {"uuids": (test_uuid, test_sub_uuid, test_inacc_uuid)},
    )

    db.session.query(OrganizationClosure).filter(
        OrganizationClosure.parent_organization_id == org_accessible.organization_id
    ).delete(synchronize_session=False)

    db.session.query(OrganizationMaster).filter(
        OrganizationMaster.organization_id.in_([
            org_accessible.organization_id,
            org_sub.organization_id,
            org_inaccessible.organization_id,
        ])
    ).delete(synchronize_session=False)

    db.session.commit()
