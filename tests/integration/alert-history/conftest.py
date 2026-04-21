"""
アラート履歴結合テスト - 共通フィクスチャ

autouse フィクスチャは親の tests/integration/conftest.py（inject_test_user 等）に依存する。
このファイルにはアラート履歴機能固有のフィクスチャのみを定義する。

teardown 方針:
  MySQL READ COMMITTED のためロールバック方式は使用しない。
  function スコープフィクスチャ: yield 後に明示的 DELETE + commit でデータを削除する。
"""

import uuid
from datetime import datetime, timedelta

import pytest
from flask import g
from sqlalchemy import text

from iot_app import db
from iot_app.models.alert import (
    AlertHistory,
    AlertLevelMaster,
    AlertSettingMaster,
    AlertStatusMaster,
)
from iot_app.models.contract import ContractStatusMaster
from iot_app.models.measurement import MeasurementItemMaster
from iot_app.models.organization import (
    OrganizationClosure,
    OrganizationMaster,
    OrganizationTypeMaster,
)


@pytest.fixture()
def alert_history_test_data(app):
    """アラート履歴結合テスト用データフィクスチャ。

    テスト用組織・デバイス・アラート設定・アラート履歴を commit で挿入し、
    テスト完了後に明示的 DELETE + commit でクリーンアップする。

    投入データ:
      org_accessible   : テスト対象ユーザー(user_id=1)がアクセス可能な組織
      org_sub          : org_accessible の下位組織
      org_inaccessible : closure 未登録のアクセス不可組織
      device_acc       : org_accessible 配下デバイス（アクセス可能）
      device_sub       : org_sub 配下デバイス（アクセス可能・下位組織）
      device_inacc     : org_inaccessible 配下デバイス（アクセス不可）
      history_acc      : device_acc のアラート履歴（論理削除なし・アクセス可能）
      history_sub      : device_sub のアラート履歴（論理削除なし・アクセス可能）
      history_deleted  : device_acc のアラート履歴（delete_flag=True・論理削除済み）
      history_inacc    : device_inacc のアラート履歴（スコープ外）

    organization_closure の設計:
      user_id=1 が user_master で持つ organization_id から
      org_accessible・org_sub へのパスを登録する。
      org_inaccessible へのパスは登録しないことでスコープ外テストを実現する。
    """
    # ------------------------------------------------------------------ #
    # マスタデータ取得
    # ------------------------------------------------------------------ #
    org_type = (
        db.session.query(OrganizationTypeMaster).filter_by(delete_flag=False).first()
    )
    contract_status = db.session.query(ContractStatusMaster).first()
    measurement_item = (
        db.session.query(MeasurementItemMaster).filter_by(delete_flag=False).first()
    )
    alert_level = db.session.query(AlertLevelMaster).filter_by(delete_flag=False).first()
    alert_status = db.session.query(AlertStatusMaster).filter_by(delete_flag=False).first()

    assert org_type is not None, "organization_type_master にレコードがありません"
    assert contract_status is not None, "contract_status_master にレコードがありません"
    assert alert_level is not None, "alert_level_master にレコードがありません"
    assert alert_status is not None, "alert_status_master にレコードがありません"

    # measurement_item_master が空の場合は最小レコードを自作
    _created_measurement_item = False
    if measurement_item is None:
        measurement_item = MeasurementItemMaster(
            measurement_item_id=996,
            measurement_item_name="テスト計測項目AH[℃]",
            silver_data_column_name="test_ah_conf_item",
            display_name="テスト計測項目AH",
            unit_name="℃",
            creator=0,
            modifier=0,
        )
        db.session.add(measurement_item)
        db.session.flush()
        _created_measurement_item = True

    # ------------------------------------------------------------------ #
    # テストデータ準備
    # ------------------------------------------------------------------ #
    now = datetime.now()
    today = now.date()
    uid = uuid.uuid4().hex[:12]
    _C = 1

    # 組織
    org_accessible = OrganizationMaster(
        organization_name=f"テストアクセス可組織_AH_{uid}",
        organization_type_id=org_type.organization_type_id,
        address="テスト住所AH1",
        phone_number="000-0000-2001",
        contact_person="テスト担当AH1",
        contract_status_id=contract_status.contract_status_id,
        contract_start_date=today,
        databricks_group_id=f"ahc1_{uid[:8]}",
        creator=_C,
        modifier=_C,
    )
    org_sub = OrganizationMaster(
        organization_name=f"テストサブ組織_AH_{uid}",
        organization_type_id=org_type.organization_type_id,
        address="テスト住所AH2",
        phone_number="000-0000-2002",
        contact_person="テスト担当AH2",
        contract_status_id=contract_status.contract_status_id,
        contract_start_date=today,
        databricks_group_id=f"ahc2_{uid[:8]}",
        creator=_C,
        modifier=_C,
    )
    org_inaccessible = OrganizationMaster(
        organization_name=f"テストアクセス不可組織_AH_{uid}",
        organization_type_id=org_type.organization_type_id,
        address="テスト住所AH3",
        phone_number="000-0000-2003",
        contact_person="テスト担当AH3",
        contract_status_id=contract_status.contract_status_id,
        contract_start_date=today,
        databricks_group_id=f"ahc3_{uid[:8]}",
        creator=_C,
        modifier=_C,
    )
    db.session.add_all([org_accessible, org_sub, org_inaccessible])
    db.session.flush()

    # user_id=1 の organization_id を取得（VIEW がスコープ解決に使用）
    user1_org_id = db.session.execute(
        text("SELECT organization_id FROM user_master WHERE user_id = 1 LIMIT 1")
    ).scalar()

    # organization_closure 登録
    # org_accessible / org_sub へのパスを登録。org_inaccessible は意図的に登録しない。
    closures = [
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
        OrganizationClosure(
            parent_organization_id=org_sub.organization_id,
            subsidiary_organization_id=org_sub.organization_id,
            depth=0,
        ),
    ]
    if user1_org_id and user1_org_id != org_accessible.organization_id:
        closures += [
            OrganizationClosure(
                parent_organization_id=user1_org_id,
                subsidiary_organization_id=org_accessible.organization_id,
                depth=1,
            ),
            OrganizationClosure(
                parent_organization_id=user1_org_id,
                subsidiary_organization_id=org_sub.organization_id,
                depth=2,
            ),
        ]
    db.session.add_all(closures)

    # デバイス（raw SQL: ORM モデルと DB 制約が乖離しているため）
    _dtype_row = db.session.execute(
        text("SELECT device_type_id FROM device_type_master WHERE delete_flag=0 LIMIT 1")
    ).first()
    _inv_row = db.session.execute(
        text("SELECT device_inventory_id FROM device_inventory_master LIMIT 1")
    ).first()
    assert _dtype_row, "device_type_master にレコードがありません"
    assert _inv_row, "device_inventory_master にレコードがありません"
    _dtype_id = _dtype_row[0]
    _inv_id = _inv_row[0]

    _insert_dev = text(
        "INSERT INTO device_master "
        "(device_uuid, organization_id, device_type_id, device_name, device_location,"
        " device_model, device_inventory_id, creator, modifier) "
        "VALUES (:uuid, :org, :dtype, :name, :loc, :model, :inv, :c, :m)"
    )
    acc_uuid = f"ahc-acc-{uid}"
    sub_uuid = f"ahc-sub-{uid}"
    inacc_uuid = f"ahc-inacc-{uid}"

    r_acc = db.session.execute(_insert_dev, {
        "uuid": acc_uuid, "org": org_accessible.organization_id,
        "dtype": _dtype_id, "name": "テストデバイスAH_アクセス可",
        "loc": "テスト設置場所AH", "model": "AHC-MODEL-001",
        "inv": _inv_id, "c": _C, "m": _C,
    })
    r_sub = db.session.execute(_insert_dev, {
        "uuid": sub_uuid, "org": org_sub.organization_id,
        "dtype": _dtype_id, "name": "テストデバイスAH_サブ",
        "loc": "テスト設置場所AHサブ", "model": "AHC-MODEL-002",
        "inv": _inv_id, "c": _C, "m": _C,
    })
    r_inacc = db.session.execute(_insert_dev, {
        "uuid": inacc_uuid, "org": org_inaccessible.organization_id,
        "dtype": _dtype_id, "name": "テストデバイスAH_アクセス不可",
        "loc": "テスト設置場所AHアクセス不可", "model": "AHC-MODEL-003",
        "inv": _inv_id, "c": _C, "m": _C,
    })
    device_acc_id = r_acc.lastrowid
    device_sub_id = r_sub.lastrowid
    device_inacc_id = r_inacc.lastrowid

    # アラート設定
    _mid = measurement_item.measurement_item_id
    alert_setting_acc = AlertSettingMaster(
        alert_uuid=str(uuid.uuid4()),
        alert_name="テストアラートAH_アクセス可",
        device_id=device_acc_id,
        alert_conditions_measurement_item_id=_mid,
        alert_conditions_operator=">=",
        alert_conditions_threshold=80.0,
        alert_recovery_conditions_measurement_item_id=_mid,
        alert_recovery_conditions_operator="<",
        alert_recovery_conditions_threshold=75.0,
        judgment_time=5,
        alert_level_id=alert_level.alert_level_id,
        creator=_C,
        modifier=_C,
    )
    alert_setting_sub = AlertSettingMaster(
        alert_uuid=str(uuid.uuid4()),
        alert_name="テストアラートAH_サブ",
        device_id=device_sub_id,
        alert_conditions_measurement_item_id=_mid,
        alert_conditions_operator=">=",
        alert_conditions_threshold=80.0,
        alert_recovery_conditions_measurement_item_id=_mid,
        alert_recovery_conditions_operator="<",
        alert_recovery_conditions_threshold=75.0,
        judgment_time=5,
        alert_level_id=alert_level.alert_level_id,
        creator=_C,
        modifier=_C,
    )
    alert_setting_inacc = AlertSettingMaster(
        alert_uuid=str(uuid.uuid4()),
        alert_name="テストアラートAH_アクセス不可",
        device_id=device_inacc_id,
        alert_conditions_measurement_item_id=_mid,
        alert_conditions_operator=">=",
        alert_conditions_threshold=80.0,
        alert_recovery_conditions_measurement_item_id=_mid,
        alert_recovery_conditions_operator="<",
        alert_recovery_conditions_threshold=75.0,
        judgment_time=5,
        alert_level_id=alert_level.alert_level_id,
        creator=_C,
        modifier=_C,
    )
    db.session.add_all([alert_setting_acc, alert_setting_sub, alert_setting_inacc])
    db.session.flush()

    # アラート履歴
    history_uuid = str(uuid.uuid4())
    history_acc = AlertHistory(
        alert_history_uuid=history_uuid,
        alert_id=alert_setting_acc.alert_id,
        alert_occurrence_datetime=now - timedelta(days=1),
        alert_status_id=alert_status.alert_status_id,
        alert_value=85.5,
        creator=_C,
        modifier=_C,
    )
    history_sub = AlertHistory(
        alert_history_uuid=str(uuid.uuid4()),
        alert_id=alert_setting_sub.alert_id,
        alert_occurrence_datetime=now - timedelta(days=2),
        alert_status_id=alert_status.alert_status_id,
        alert_value=82.0,
        creator=_C,
        modifier=_C,
    )
    history_deleted = AlertHistory(
        alert_history_uuid=str(uuid.uuid4()),
        alert_id=alert_setting_acc.alert_id,
        alert_occurrence_datetime=now - timedelta(days=3),
        alert_status_id=alert_status.alert_status_id,
        alert_value=83.0,
        delete_flag=True,
        creator=_C,
        modifier=_C,
    )
    history_inacc = AlertHistory(
        alert_history_uuid=str(uuid.uuid4()),
        alert_id=alert_setting_inacc.alert_id,
        alert_occurrence_datetime=now - timedelta(days=1),
        alert_status_id=alert_status.alert_status_id,
        alert_value=90.0,
        creator=_C,
        modifier=_C,
    )
    db.session.add_all([history_acc, history_sub, history_deleted, history_inacc])
    db.session.commit()

    # inject_test_user の organization_id を org_accessible に override
    accessible_org_id = org_accessible.organization_id

    def _override_org():
        if hasattr(g, "current_user"):
            g.current_user.organization_id = accessible_org_id

    app.before_request_funcs.setdefault(None, []).append(_override_org)

    # ------------------------------------------------------------------ #
    # yield（テストへデータを提供）
    # ------------------------------------------------------------------ #
    yield {
        "org_accessible_id": org_accessible.organization_id,
        "org_sub_id": org_sub.organization_id,
        "org_inaccessible_id": org_inaccessible.organization_id,
        "device_acc_id": device_acc_id,
        "device_sub_id": device_sub_id,
        "device_inacc_id": device_inacc_id,
        "alert_setting_acc": alert_setting_acc,
        "alert_setting_sub": alert_setting_sub,
        "alert_setting_inacc": alert_setting_inacc,
        "history_uuid": history_uuid,
        "history_acc": history_acc,
        "history_sub": history_sub,
        "history_deleted": history_deleted,
        "history_inacc": history_inacc,
        "device_name_acc": "テストデバイスAH_アクセス可",
        "device_name_sub": "テストデバイスAH_サブ",
        "device_name_inacc": "テストデバイスAH_アクセス不可",
        "device_location_acc": "テスト設置場所AH",
        "device_location_sub": "テスト設置場所AHサブ",
        "alert_name_acc": "テストアラートAH_アクセス可",
        "alert_name_sub": "テストアラートAH_サブ",
        "alert_name_inacc": "テストアラートAH_アクセス不可",
        "alert_level_id": alert_level.alert_level_id,
        "alert_status_id": alert_status.alert_status_id,
        "now": now,
    }

    # ------------------------------------------------------------------ #
    # teardown: 明示的 DELETE + commit でテストデータを削除する
    # MySQL READ COMMITTED のためロールバック方式は使用しない
    # ------------------------------------------------------------------ #
    funcs = app.before_request_funcs.get(None, [])
    if _override_org in funcs:
        funcs.remove(_override_org)

    alert_ids = [
        alert_setting_acc.alert_id,
        alert_setting_sub.alert_id,
        alert_setting_inacc.alert_id,
    ]
    device_ids = [device_acc_id, device_sub_id, device_inacc_id]
    org_ids = [
        org_accessible.organization_id,
        org_sub.organization_id,
        org_inaccessible.organization_id,
    ]

    db.session.query(AlertHistory).filter(
        AlertHistory.alert_id.in_(alert_ids)
    ).delete(synchronize_session=False)

    db.session.query(AlertSettingMaster).filter(
        AlertSettingMaster.alert_id.in_(alert_ids)
    ).delete(synchronize_session=False)

    db.session.execute(
        text("DELETE FROM device_master WHERE device_id IN :ids"),
        {"ids": tuple(device_ids)},
    )

    db.session.query(OrganizationClosure).filter(
        OrganizationClosure.subsidiary_organization_id.in_(org_ids)
    ).delete(synchronize_session=False)

    db.session.query(OrganizationMaster).filter(
        OrganizationMaster.organization_id.in_(org_ids)
    ).delete(synchronize_session=False)

    if _created_measurement_item:
        db.session.query(MeasurementItemMaster).filter(
            MeasurementItemMaster.measurement_item_id == measurement_item.measurement_item_id
        ).delete(synchronize_session=False)

    db.session.commit()
