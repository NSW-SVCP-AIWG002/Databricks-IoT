"""
結合テスト共通フィクスチャ

全結合テストで使用する共通フィクスチャを定義する。
主な役割:
  - before_request フックで flask.g に認証済みユーザーをセットする。
  - 業種別ダッシュボード結合テスト用の実DBテストデータを投入・クリーンアップする。
  - measurement_item_master が空の場合に必要なマスタデータを自動シードする。
"""

import uuid
from datetime import date, datetime, timedelta
from types import SimpleNamespace

import pytest


# ------------------------------------------------------------
# measurement_item_master シードデータ（02_master_data.sql と同一）
# ------------------------------------------------------------
_MEASUREMENT_ITEMS = [
    (1,  '共通外気温度[℃]',            'external_temp',                    '共通外気温度',            '℃'),
    (2,  '第1冷凍設定温度[℃]',         'set_temp_freezer_1',               '第1冷凍設定温度',         '℃'),
    (3,  '第1冷凍庫内センサー温度[℃]', 'internal_sensor_temp_freezer_1',   '第1冷凍庫内センサー温度', '℃'),
    (4,  '第1冷凍表示温度[℃]',         'internal_temp_freezer_1',          '第1冷凍表示温度',         '℃'),
    (5,  '第1冷凍DF温度[℃]',           'df_temp_freezer_1',                '第1冷凍DF温度',           '℃'),
    (6,  '第1冷凍凝縮温度[℃]',         'condensing_temp_freezer_1',        '第1冷凍凝縮温度',         '℃'),
    (7,  '第1冷凍微調整後庫内温度[℃]', 'adjusted_internal_temp_freezer_1', '第1冷凍微調整後庫内温度', '℃'),
    (8,  '第2冷凍設定温度[℃]',         'set_temp_freezer_2',               '第2冷凍設定温度',         '℃'),
    (9,  '第2冷凍庫内センサー温度[℃]', 'internal_sensor_temp_freezer_2',   '第2冷凍庫内センサー温度', '℃'),
    (10, '第2冷凍表示温度[℃]',         'internal_temp_freezer_2',          '第2冷凍表示温度',         '℃'),
    (11, '第2冷凍DF温度[℃]',           'df_temp_freezer_2',                '第2冷凍DF温度',           '℃'),
    (12, '第2冷凍凝縮温度[℃]',         'condensing_temp_freezer_2',        '第2冷凍凝縮温度',         '℃'),
    (13, '第2冷凍微調整後庫内温度[℃]', 'adjusted_internal_temp_freezer_2', '第2冷凍微調整後庫内温度', '℃'),
    (14, '第1冷凍圧縮機回転数[rpm]',   'compressor_freezer_1',             '第1冷凍圧縮機回転数',     'rpm'),
    (15, '第2冷凍圧縮機回転数[rpm]',   'compressor_freezer_2',             '第2冷凍圧縮機回転数',     'rpm'),
    (16, '第1ファンモータ回転数[rpm]', 'fan_motor_1',                      '第1ファンモータ回転数',   'rpm'),
    (17, '第2ファンモータ回転数[rpm]', 'fan_motor_2',                      '第2ファンモータ回転数',   'rpm'),
    (18, '第3ファンモータ回転数[rpm]', 'fan_motor_3',                      '第3ファンモータ回転数',   'rpm'),
    (19, '第4ファンモータ回転数[rpm]', 'fan_motor_4',                      '第4ファンモータ回転数',   'rpm'),
    (20, '第5ファンモータ回転数[rpm]', 'fan_motor_5',                      '第5ファンモータ回転数',   'rpm'),
    (21, '防露ヒータ出力(1)[%]',       'defrost_heater_output_1',          '防露ヒータ出力(1)',       '%'),
    (22, '防露ヒータ出力(2)[%]',       'defrost_heater_output_2',          '防露ヒータ出力(2)',       '%'),
]


@pytest.fixture(scope="session", autouse=True)
def seed_measurement_items():
    """measurement_item_master が空の場合にマスタデータを自動シードする。

    結合テストセッション開始時に一度だけ実行し、テーブルが空であれば
    02_master_data.sql と同一のデータを投入する。
    セッション終了後、自身が挿入したレコードのみ削除する（既存データは保護）。

    session スコープのため app フィクスチャに依存せず独立したアプリコンテキストを使用する。
    """
    import os
    os.environ.setdefault("FLASK_ENV", "testing")

    from iot_app import create_app, db
    from iot_app.models.measurement import MeasurementItemMaster

    _app = create_app()
    seeded = False

    with _app.app_context():
        existing = db.session.query(MeasurementItemMaster).count()
        if existing == 0:
            for (mid, name, col, disp, unit) in _MEASUREMENT_ITEMS:
                db.session.add(MeasurementItemMaster(
                    measurement_item_id=mid,
                    measurement_item_name=name,
                    silver_data_column_name=col,
                    display_name=disp,
                    unit_name=unit,
                    creator=0,
                    modifier=0,
                ))
            db.session.commit()
            seeded = True

        yield

        if seeded:
            seeded_ids = [row[0] for row in _MEASUREMENT_ITEMS]
            db.session.query(MeasurementItemMaster).filter(
                MeasurementItemMaster.measurement_item_id.in_(seeded_ids)
            ).delete(synchronize_session=False)
            db.session.commit()


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

    # authenticate_request を一時的に除外（テスト中はDB認証をスキップ）
    from iot_app.auth.middleware import authenticate_request
    funcs = app.before_request_funcs.setdefault(None, [])
    auth_was_present = authenticate_request in funcs
    if auth_was_present:
        funcs.remove(authenticate_request)

    # before_request_funcs の先頭に挿入（ミドルウェアより先に実行）
    funcs.insert(0, _set_current_user)

    yield

    # テスト後にフックを削除してテスト間の干渉を防ぐ
    funcs = app.before_request_funcs.get(None, [])
    if _set_current_user in funcs:
        funcs.remove(_set_current_user)

    # authenticate_request を復元
    if auth_was_present and authenticate_request not in funcs:
        funcs.append(authenticate_request)


@pytest.fixture()
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
    from iot_app.models.device import DeviceMaster
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
    assert alert_level is not None, "alert_level_master にレコードがありません"
    assert alert_status is not None, "alert_status_master にレコードがありません"

    # measurement_item_master が空の場合（他テストの clean_db で削除された場合を含む）
    # フィクスチャ内で最小限のレコードを自己作成し、テスト後にクリーンアップする
    _created_measurement_item = False
    if measurement_item is None:
        measurement_item = MeasurementItemMaster(
            measurement_item_id=1,
            measurement_item_name='共通外気温度[℃]',
            silver_data_column_name='external_temp',
            display_name='共通外気温度',
            unit_name='℃',
            creator=0,
            modifier=0,
        )
        db.session.add(measurement_item)
        db.session.flush()
        _created_measurement_item = True

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
    # 実DB制約: device_type_id NOT NULL, device_inventory_id NOT NULL
    from sqlalchemy import text as _text

    test_uuid = f"test-acc-{uid}"
    test_sub_uuid = f"test-sub-{uid}"
    test_inacc_uuid = f"test-inacc-{uid}"

    # 既存の device_type_id / device_inventory_id を動的に取得
    _dtype_row = db.session.execute(
        _text("SELECT device_type_id FROM device_type_master WHERE delete_flag=0 LIMIT 1")
    ).first()
    _inv_row = db.session.execute(
        _text("SELECT device_inventory_id FROM device_inventory_master LIMIT 1")
    ).first()
    assert _dtype_row, "device_type_master にレコードがありません"
    assert _inv_row, "device_inventory_master にレコードがありません"
    _dtype_id = _dtype_row[0]
    _inv_id = _inv_row[0]

    _insert_device_sql = _text(
        "INSERT INTO device_master "
        "(device_uuid, organization_id, device_type_id, device_name, device_model, "
        "device_inventory_id, creator, modifier) "
        "VALUES (:uuid, :org, :dtype, :name, :model, :inv, :c, :m)"
    )
    r1 = db.session.execute(_insert_device_sql, {
        "uuid": test_uuid, "org": org_accessible.organization_id,
        "dtype": _dtype_id, "name": "テストデバイス_結合テスト用",
        "model": "TEST-MODEL-001", "inv": _inv_id, "c": _C, "m": _C,
    })
    r2 = db.session.execute(_insert_device_sql, {
        "uuid": test_sub_uuid, "org": org_sub.organization_id,
        "dtype": _dtype_id, "name": "テストサブデバイス_結合テスト用",
        "model": "TEST-MODEL-002", "inv": _inv_id, "c": _C, "m": _C,
    })
    r3 = db.session.execute(_insert_device_sql, {
        "uuid": test_inacc_uuid, "org": org_inaccessible.organization_id,
        "dtype": _dtype_id, "name": "テストアクセス不可デバイス_結合テスト用",
        "model": "TEST-MODEL-003", "inv": _inv_id, "c": _C, "m": _C,
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

    if _created_measurement_item:
        db.session.query(MeasurementItemMaster).filter_by(measurement_item_id=1).delete()

    db.session.commit()
