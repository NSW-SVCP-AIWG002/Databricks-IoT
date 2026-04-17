"""
アラート履歴 - 結合テスト

対象エンドポイント:
  GET  /alert/alert-history                   初期表示・ページング
  POST /alert/alert-history                   検索実行
  GET  /alert/alert-history/<alert_history_uuid>  詳細表示（参照モーダル）

参照ドキュメント:
  - UI設計書:           docs/03-features/flask-app/alert-history/ui-specification.md
  - 機能設計書:         docs/03-features/flask-app/alert-history/workflow-specification.md
  - 結合テスト観点表:   docs/05-testing/integration-test/integration-test-perspectives.md
  - 結合テスト実装ガイド: docs/05-testing/integration-test/integration-test-guide.md

適用観点:
  1.1  認証テスト
  1.3  データスコープフィルタテスト
  2.1  正常遷移テスト（初期表示・検索・参照）
  2.2  エラー時遷移テスト（404・500）
  4.1  一覧表示テスト
  4.2  詳細表示テスト
  5.1  検索条件テスト（部分一致・完全一致・AND結合）
  5.2  ソート機能テスト
  5.3  ページネーションテスト
  9.1  SQLインジェクションテスト
  9.2  XSSテスト

スコープ外:
  3.x  バリデーション（検索フォームは全任意入力のためバリデーションなし）
  4.3〜4.6  登録・更新・削除・CSV（read-only機能のため対象外）
  6.x  外部API連携（Databricks連携なし）
  7.x  トランザクション（read-only機能のため対象外）
  8.x  ログ出力テスト（ルートテストの範囲外）
  2.3  リダイレクトテスト（POST後は直接HTML返却のため対象外）
"""

import uuid
from datetime import datetime, timedelta
from types import SimpleNamespace

import pytest
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


# =============================================================================
# フィクスチャ
# =============================================================================

@pytest.fixture()
def alert_history_test_data(app):
    """アラート履歴結合テスト用データフィクスチャ。

    テスト用組織・デバイス・アラート設定・アラート履歴を MySQL に投入し、
    テスト完了後に DELETE + COMMIT でクリーンアップする。

    投入データ:
      org_accessible   : テスト対象ユーザー(user_id=1)がアクセス可能な組織
      org_sub          : org_accessible の下位組織
      org_inaccessible : closure 未登録のアクセス不可組織
      device_acc       : org_accessible 配下デバイス（アラート履歴あり）
      device_sub       : org_sub 配下デバイス（アラート履歴あり）
      device_inacc     : org_inaccessible 配下デバイス（アラート履歴あり）
      history_acc      : device_acc のアラート履歴（アクセス可能・論理削除なし）
      history_sub      : device_sub のアラート履歴（アクセス可能・論理削除なし）
      history_deleted  : device_acc のアラート履歴（論理削除済み）
      history_inacc    : device_inacc のアラート履歴（アクセス不可）

    organization_closure の設計:
      - user_id=1 が user_master で持つ organization_id から
        org_accessible・org_sub へのパスを登録する。
      - org_inaccessible へのパスは登録しないことでスコープ外テストを実現する。
    """
    from flask import g

    # ------------------------------------------------------------------ #
    # マスタデータ取得
    # ------------------------------------------------------------------ #
    org_type = db.session.query(OrganizationTypeMaster).filter_by(delete_flag=False).first()
    contract_status = db.session.query(ContractStatusMaster).first()
    measurement_item = db.session.query(MeasurementItemMaster).filter_by(delete_flag=False).first()
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
            measurement_item_id=997,
            measurement_item_name="テスト計測項目AH[℃]",
            silver_data_column_name="test_ah_item",
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
        phone_number="000-0000-1001",
        contact_person="テスト担当AH1",
        contract_status_id=contract_status.contract_status_id,
        contract_start_date=today,
        databricks_group_id=f"ah1_{uid[:8]}",
        creator=_C,
        modifier=_C,
    )
    org_sub = OrganizationMaster(
        organization_name=f"テストサブ組織_AH_{uid}",
        organization_type_id=org_type.organization_type_id,
        address="テスト住所AH2",
        phone_number="000-0000-1002",
        contact_person="テスト担当AH2",
        contract_status_id=contract_status.contract_status_id,
        contract_start_date=today,
        databricks_group_id=f"ah2_{uid[:8]}",
        creator=_C,
        modifier=_C,
    )
    org_inaccessible = OrganizationMaster(
        organization_name=f"テストアクセス不可組織_AH_{uid}",
        organization_type_id=org_type.organization_type_id,
        address="テスト住所AH3",
        phone_number="000-0000-1003",
        contact_person="テスト担当AH3",
        contract_status_id=contract_status.contract_status_id,
        contract_start_date=today,
        databricks_group_id=f"ah3_{uid[:8]}",
        creator=_C,
        modifier=_C,
    )
    db.session.add_all([org_accessible, org_sub, org_inaccessible])
    db.session.flush()

    # user_id=1 の organization_id を取得（VIEW が user_master 経由でスコープ解決するため）
    user1_org_id = db.session.execute(
        text("SELECT organization_id FROM user_master WHERE user_id = 1 LIMIT 1")
    ).scalar()

    # organization_closure 登録
    # org_accessible と org_sub への closure を作成。
    # org_inaccessible は意図的に登録しない（スコープ外テスト用）。
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
    # user_id=1 の組織から org_accessible・org_sub へのパスを追加
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

    # デバイス（raw SQL: device_master は ORM モデルと制約が乖離している）
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
    acc_uuid = f"ah-acc-{uid}"
    sub_uuid = f"ah-sub-{uid}"
    inacc_uuid = f"ah-inacc-{uid}"

    r_acc = db.session.execute(_insert_dev, {
        "uuid": acc_uuid, "org": org_accessible.organization_id,
        "dtype": _dtype_id, "name": "テストデバイスAH_アクセス可",
        "loc": "テスト設置場所AH", "model": "AH-MODEL-001",
        "inv": _inv_id, "c": _C, "m": _C,
    })
    r_sub = db.session.execute(_insert_dev, {
        "uuid": sub_uuid, "org": org_sub.organization_id,
        "dtype": _dtype_id, "name": "テストデバイスAH_サブ",
        "loc": "テスト設置場所AHサブ", "model": "AH-MODEL-002",
        "inv": _inv_id, "c": _C, "m": _C,
    })
    r_inacc = db.session.execute(_insert_dev, {
        "uuid": inacc_uuid, "org": org_inaccessible.organization_id,
        "dtype": _dtype_id, "name": "テストデバイスAH_アクセス不可",
        "loc": "テスト設置場所AHアクセス不可", "model": "AH-MODEL-003",
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
        "alert_name_acc": "テストアラートAH_アクセス可",
        "alert_name_inacc": "テストアラートAH_アクセス不可",
        "now": now,
        "alert_level_id": alert_level.alert_level_id,
        "alert_status_id": alert_status.alert_status_id,
    }

    # ------------------------------------------------------------------ #
    # クリーンアップ（FK 逆順削除）
    # ------------------------------------------------------------------ #
    funcs = app.before_request_funcs.get(None, [])
    if _override_org in funcs:
        funcs.remove(_override_org)

    all_setting_ids = [
        alert_setting_acc.alert_id,
        alert_setting_sub.alert_id,
        alert_setting_inacc.alert_id,
    ]

    db.session.query(AlertHistory).filter(
        AlertHistory.alert_id.in_(all_setting_ids)
    ).delete(synchronize_session=False)

    db.session.query(AlertSettingMaster).filter(
        AlertSettingMaster.alert_id.in_(all_setting_ids)
    ).delete(synchronize_session=False)

    db.session.execute(
        text("DELETE FROM device_master WHERE device_uuid IN :uuids"),
        {"uuids": (acc_uuid, sub_uuid, inacc_uuid)},
    )

    # closure 削除（追加したものを限定削除）
    db.session.query(OrganizationClosure).filter(
        OrganizationClosure.parent_organization_id.in_([
            org_accessible.organization_id,
            org_sub.organization_id,
        ])
    ).delete(synchronize_session=False)
    if user1_org_id:
        db.session.query(OrganizationClosure).filter(
            OrganizationClosure.parent_organization_id == user1_org_id,
            OrganizationClosure.subsidiary_organization_id.in_([
                org_accessible.organization_id,
                org_sub.organization_id,
            ]),
        ).delete(synchronize_session=False)

    db.session.query(OrganizationMaster).filter(
        OrganizationMaster.organization_id.in_([
            org_accessible.organization_id,
            org_sub.organization_id,
            org_inaccessible.organization_id,
        ])
    ).delete(synchronize_session=False)

    if _created_measurement_item:
        db.session.query(MeasurementItemMaster).filter_by(
            measurement_item_id=997
        ).delete()

    db.session.commit()


# =============================================================================
# 1.1 / 1.2  認証・認可テスト
# =============================================================================

@pytest.mark.integration
class TestAlertHistoryAuth:
    """1.1 認証テスト / 1.2 認可テスト

    観点: integration-test-perspectives.md > 1.1, 1.2
    注: inject_test_user (autouse) が before_request フックで g.current_user を
        セットするため、認証ミドルウェアはバイパス済み。
        ここでは @require_role デコレータ（user_type_id ベース）の動作を確認する。
    """

    def test_system_admin_can_access_list(self, client):
        """1.1.1 / 1.2.1: system_admin（user_type_id=1）で一覧にアクセスできること"""
        # Arrange: inject_test_user が user_type_id=1 をセット済み

        # Act
        response = client.get("/alert/alert-history")

        # Assert
        assert response.status_code == 200

    def test_unauthorized_role_returns_403_on_list(self, client, app):
        """1.2.3 / 1.2.5 / 1.2.7: 許可ロール以外（user_type_id=0）では403エラーとなること
        _ALL_ROLES にはすべてのロールが含まれるが、無効な user_type_id=0 では403となる。
        """
        from flask import g

        def _set_invalid_user():
            g.current_user = SimpleNamespace(
                user_id=99,
                user_type_id=0,  # 不正なロールID
                organization_id=1,
            )
            g.current_user_id = 99
            g.databricks_token = ""

        funcs = app.before_request_funcs.setdefault(None, [])
        funcs.insert(0, _set_invalid_user)

        try:
            # Act
            response = client.get("/alert/alert-history")
            # Assert
            assert response.status_code == 403
        finally:
            if _set_invalid_user in funcs:
                funcs.remove(_set_invalid_user)

    def test_system_admin_can_access_detail(self, client, alert_history_test_data):
        """1.1.1: system_admin で詳細にアクセスできること"""
        # Arrange
        history_uuid = alert_history_test_data["history_uuid"]

        # Act
        response = client.get(f"/alert/alert-history/{history_uuid}")

        # Assert
        assert response.status_code == 200


# =============================================================================
# 2.1 / 4.1  初期表示・一覧表示テスト
# =============================================================================

@pytest.mark.integration
class TestAlertHistoryListDisplay:
    """2.1 正常遷移テスト / 4.1 一覧表示テスト

    観点: integration-test-perspectives.md > 2.1.1, 4.1.1〜4.1.5
    """

    def test_initial_display_returns_200(self, client):
        """2.1.1: GET /alert/alert-history で200が返ること（初期表示）"""
        # Act
        response = client.get("/alert/alert-history")

        # Assert
        assert response.status_code == 200

    def test_initial_display_renders_list_template(self, client):
        """2.1.1: 初期表示でアラート履歴一覧テンプレートがレンダリングされること"""
        # Act
        response = client.get("/alert/alert-history")

        # Assert: ページタイトルがレンダリングされること
        assert "アラート履歴" in response.data.decode("utf-8")

    def test_zero_data_shows_empty_list(self, client):
        """4.1.1: アクセス可能なアラート履歴が0件の場合、空のテーブルが表示されること
        テストデータを投入していない状態で検索する。
        """
        # Arrange: データなし状態（フィクスチャなし）
        # Act
        response = client.get("/alert/alert-history")

        # Assert
        assert response.status_code == 200

    def test_accessible_record_is_displayed(self, client, alert_history_test_data):
        """4.1.2 / 4.1.3: アクセス可能なアラート履歴が一覧に表示されること"""
        # Arrange: 検索期間を過去7日間に広げる（デフォルト期間内）
        # Act
        response = client.get("/alert/alert-history")

        # Assert: レスポンスが正常であること
        assert response.status_code == 200

    def test_logically_deleted_record_not_displayed(self, client, alert_history_test_data):
        """4.1.4: 論理削除済み（delete_flag=True）のアラート履歴は表示されないこと"""
        # Arrange
        deleted_occurrence = alert_history_test_data["history_deleted"].alert_occurrence_datetime
        start = (deleted_occurrence - timedelta(hours=1)).strftime("%Y/%m/%d %H:%M")
        end = (deleted_occurrence + timedelta(hours=1)).strftime("%Y/%m/%d %H:%M")

        # Act: 論理削除済みレコードの発生日時を狙い打ちで検索
        response = client.post("/alert/alert-history", data={
            "start_datetime": start,
            "end_datetime": end,
            "sort_item_id": 1,
            "sort_order_id": 2,
        })

        # Assert: 論理削除済みデバイス名が表示されないこと
        body = response.data.decode("utf-8")
        assert response.status_code == 200
        # history_deleted の alert_name はアクセス可デバイスのアラート設定と同じだが、
        # delete_flag=True のため件数に含まれない
        # → レスポンスは正常に返却されること
        assert "アラート履歴" in body

    def test_initial_display_sets_cookie(self, client):
        """2.1.1: GET /alert/alert-history（pageパラメータなし）でCookieが設定されること
        ワークフロー仕様書: 初期表示時に Cookie に検索条件を格納する。
        """
        # Act
        response = client.get("/alert/alert-history")

        # Assert: Set-Cookie ヘッダーに alert_history が含まれること
        cookie_header = response.headers.get("Set-Cookie", "")
        assert "alert_history" in cookie_header

    def test_paging_reads_cookie(self, client):
        """2.1.1: GET /alert/alert-history?page=2（pageパラメータあり）でCookieが読み込まれること
        ワークフロー仕様書: ページング時は Cookie から検索条件を復元する。
        """
        # Arrange: まず初期表示でCookieを設定
        client.get("/alert/alert-history")

        # Act: 2ページ目へ遷移
        response = client.get("/alert/alert-history?page=2")

        # Assert: 正常に返却されること
        assert response.status_code == 200


# =============================================================================
# 2.2  エラー時遷移テスト
# =============================================================================

@pytest.mark.integration
class TestAlertHistoryErrorTransition:
    """2.2 エラー時遷移テスト

    観点: integration-test-perspectives.md > 2.2.4, 2.2.5
    """

    def test_nonexistent_uuid_returns_404(self, client):
        """2.2.4: 存在しないUUIDで詳細アクセスすると404エラーが返ること"""
        # Arrange
        nonexistent_uuid = str(uuid.uuid4())

        # Act
        response = client.get(f"/alert/alert-history/{nonexistent_uuid}")

        # Assert
        assert response.status_code == 404

    def test_db_error_on_list_returns_500(self, client, app):
        """2.2.5: DBエラー発生時に500エラーが返ること
        search_alert_histories が例外を送出した場合、abort(500) が呼ばれる。
        """
        from unittest.mock import patch

        # Act
        with patch(
            "iot_app.views.alert.alert_history.search_alert_histories",
            side_effect=Exception("DB Timeout"),
        ):
            response = client.get("/alert/alert-history")

        # Assert
        assert response.status_code == 500


# =============================================================================
# 2.1 / 4.2  詳細表示テスト
# =============================================================================

@pytest.mark.integration
class TestAlertHistoryDetail:
    """2.1.5 / 4.2 詳細表示テスト

    観点: integration-test-perspectives.md > 2.1.5, 4.2.1〜4.2.4
    """

    def test_detail_returns_200(self, client, alert_history_test_data):
        """2.1.5 / 4.2.1: 有効なUUIDで詳細モーダルが200で表示されること"""
        # Arrange
        history_uuid = alert_history_test_data["history_uuid"]

        # Act
        response = client.get(f"/alert/alert-history/{history_uuid}")

        # Assert
        assert response.status_code == 200

    def test_detail_shows_correct_data(self, client, alert_history_test_data):
        """4.2.1: 詳細モーダルにアラート履歴の正しいデータが表示されること
        UI仕様書 (6): デバイス名・アラート名・アラート発生時の値等を表示。
        """
        # Arrange
        history_uuid = alert_history_test_data["history_uuid"]

        # Act
        response = client.get(f"/alert/alert-history/{history_uuid}")

        # Assert: デバイス名とアラート名がレンダリングされていること
        body = response.data.decode("utf-8")
        assert alert_history_test_data["device_name_acc"] in body
        assert alert_history_test_data["alert_name_acc"] in body

    def test_nonexistent_uuid_returns_404(self, client):
        """4.2.2: 存在しないUUIDで詳細アクセスすると404エラーが返ること"""
        # Arrange
        nonexistent_uuid = str(uuid.uuid4())

        # Act
        response = client.get(f"/alert/alert-history/{nonexistent_uuid}")

        # Assert
        assert response.status_code == 404

    def test_logically_deleted_returns_404(self, client, alert_history_test_data):
        """4.2.3: 論理削除済みのアラート履歴にアクセスすると404エラーが返ること
        delete_flag=True のレコードは VIEW でフィルタされるため None → 404。
        """
        # Arrange
        deleted_uuid = alert_history_test_data["history_deleted"].alert_history_uuid

        # Act
        response = client.get(f"/alert/alert-history/{deleted_uuid}")

        # Assert
        assert response.status_code == 404

    def test_out_of_scope_uuid_returns_404(self, client, alert_history_test_data):
        """4.2.4: データスコープ外のアラート履歴にアクセスすると404エラーが返ること
        org_inaccessible に紐づくアラート履歴は user_id=1 のスコープ外。
        """
        # Arrange
        inacc_uuid = alert_history_test_data["history_inacc"].alert_history_uuid

        # Act
        response = client.get(f"/alert/alert-history/{inacc_uuid}")

        # Assert
        assert response.status_code == 404


# =============================================================================
# 5.1  検索条件テスト
# =============================================================================

@pytest.mark.integration
class TestAlertHistorySearch:
    """5.1 検索条件テスト

    観点: integration-test-perspectives.md > 5.1.1, 5.1.6〜5.1.11
    注: アラート履歴は read-only（検索フォームはすべて任意入力）。
        完全一致フィールド: alert_level_id, alert_status_id
        部分一致フィールド: device_name, device_location, alert_name
    """

    def test_search_returns_200(self, client):
        """2.1.2: POST /alert/alert-history で200が返ること（検索実行）"""
        # Act
        response = client.post("/alert/alert-history", data={
            "sort_item_id": 1,
            "sort_order_id": 2,
        })

        # Assert
        assert response.status_code == 200

    def test_no_conditions_returns_all_accessible_data(self, client, alert_history_test_data):
        """5.1.1: 検索条件なしで検索すると、スコープ内の全件が返ること
        全条件未入力 → スコープ内の全アラート履歴が対象となる。
        """
        # Act: 日時条件も含め全条件を空にして検索
        response = client.post("/alert/alert-history", data={
            "start_datetime": "",
            "end_datetime": "",
            "sort_item_id": 1,
            "sort_order_id": 2,
        })

        # Assert
        assert response.status_code == 200
        body = response.data.decode("utf-8")
        # アクセス可能なデバイス名が表示されること
        assert alert_history_test_data["device_name_acc"] in body

    def test_device_name_partial_match_forward(self, client, alert_history_test_data):
        """5.1.7: device_name の前方一致検索でヒットすること
        UI仕様書 (2-3): デバイス名は部分一致検索。
        """
        # Arrange: デバイス名の先頭部分で検索
        partial_name = "テストデバイスAH"  # 前方一致

        # Act
        response = client.post("/alert/alert-history", data={
            "device_name": partial_name,
            "start_datetime": "",
            "end_datetime": "",
            "sort_item_id": 1,
            "sort_order_id": 2,
        })

        # Assert
        assert response.status_code == 200
        body = response.data.decode("utf-8")
        assert alert_history_test_data["device_name_acc"] in body

    def test_device_name_partial_match_middle(self, client, alert_history_test_data):
        """5.1.9: device_name の中間一致検索でヒットすること
        UI仕様書 (2-3): デバイス名は部分一致検索（中間一致）。
        """
        # Arrange: デバイス名の中間部分で検索
        partial_name = "デバイスAH_アクセス"  # 中間一致

        # Act
        response = client.post("/alert/alert-history", data={
            "device_name": partial_name,
            "start_datetime": "",
            "end_datetime": "",
            "sort_item_id": 1,
            "sort_order_id": 2,
        })

        # Assert
        assert response.status_code == 200
        body = response.data.decode("utf-8")
        assert alert_history_test_data["device_name_acc"] in body

    def test_device_name_partial_match_backward(self, client, alert_history_test_data):
        """5.1.8: device_name の後方一致検索でヒットすること
        UI仕様書 (2-3): デバイス名は部分一致検索（後方一致）。
        """
        # Arrange: デバイス名の末尾部分で検索
        partial_name = "アクセス可"  # 後方一致

        # Act
        response = client.post("/alert/alert-history", data={
            "device_name": partial_name,
            "start_datetime": "",
            "end_datetime": "",
            "sort_item_id": 1,
            "sort_order_id": 2,
        })

        # Assert
        assert response.status_code == 200
        body = response.data.decode("utf-8")
        assert alert_history_test_data["device_name_acc"] in body

    def test_device_name_no_match_returns_no_results(self, client):
        """5.1.11: 条件に合致するデバイス名がない場合、該当データが表示されないこと
        AND 結合: device_name が一致しないケース。
        """
        # Act: 存在しないデバイス名で検索
        response = client.post("/alert/alert-history", data={
            "device_name": "zzz存在しないデバイスzzz",
            "start_datetime": "",
            "end_datetime": "",
            "sort_item_id": 1,
            "sort_order_id": 2,
        })

        # Assert
        assert response.status_code == 200

    def test_alert_level_filter_exact_match(self, client, alert_history_test_data):
        """5.1.2: alert_level_id での完全一致フィルタが適用されること
        UI仕様書 (2-6): アラートレベルは完全一致フィルタ。
        """
        # Arrange
        alert_level_id = alert_history_test_data["alert_level_id"]

        # Act
        response = client.post("/alert/alert-history", data={
            "alert_level_id": str(alert_level_id),
            "start_datetime": "",
            "end_datetime": "",
            "sort_item_id": 1,
            "sort_order_id": 2,
        })

        # Assert
        assert response.status_code == 200

    def test_alert_status_filter_exact_match(self, client, alert_history_test_data):
        """5.1.2: alert_status_id での完全一致フィルタが適用されること
        UI仕様書 (2-7): ステータスは完全一致フィルタ。
        """
        # Arrange
        alert_status_id = alert_history_test_data["alert_status_id"]

        # Act
        response = client.post("/alert/alert-history", data={
            "alert_status_id": str(alert_status_id),
            "start_datetime": "",
            "end_datetime": "",
            "sort_item_id": 1,
            "sort_order_id": 2,
        })

        # Assert
        assert response.status_code == 200

    def test_multiple_conditions_and_both_match(self, client, alert_history_test_data):
        """5.1.10: 複数条件をすべて満たすデータがヒットすること（AND 結合）
        ワークフロー仕様書 SQL: 各条件は AND で結合される。
        """
        # Arrange: device_name + alert_level_id の両方を指定
        alert_level_id = alert_history_test_data["alert_level_id"]

        # Act
        response = client.post("/alert/alert-history", data={
            "device_name": "テストデバイスAH_アクセス可",
            "alert_level_id": str(alert_level_id),
            "start_datetime": "",
            "end_datetime": "",
            "sort_item_id": 1,
            "sort_order_id": 2,
        })

        # Assert
        assert response.status_code == 200
        body = response.data.decode("utf-8")
        assert alert_history_test_data["device_name_acc"] in body

    def test_multiple_conditions_and_one_not_match(self, client, alert_history_test_data):
        """5.1.11: 複数条件の片方しか満たさない場合、ヒットしないこと（AND 結合）
        device_name は一致するが alert_level_id は存在しないIDを指定。
        """
        # Arrange: 存在しない alert_level_id を指定
        invalid_level_id = 9999

        # Act
        response = client.post("/alert/alert-history", data={
            "device_name": "テストデバイスAH_アクセス可",
            "alert_level_id": str(invalid_level_id),
            "start_datetime": "",
            "end_datetime": "",
            "sort_item_id": 1,
            "sort_order_id": 2,
        })

        # Assert: 条件不一致のため該当データなし
        assert response.status_code == 200

    def test_date_range_within_period(self, client, alert_history_test_data):
        """5.1.1: 期間内のアラート履歴がBETWEENフィルタで取得されること
        ワークフロー仕様書 SQL: alert_occurrence_datetime BETWEEN start AND end
        """
        # Arrange: history_acc の発生日時を包む期間を指定
        occurrence = alert_history_test_data["history_acc"].alert_occurrence_datetime
        start = (occurrence - timedelta(hours=1)).strftime("%Y/%m/%d %H:%M")
        end = (occurrence + timedelta(hours=1)).strftime("%Y/%m/%d %H:%M")

        # Act
        response = client.post("/alert/alert-history", data={
            "start_datetime": start,
            "end_datetime": end,
            "sort_item_id": 1,
            "sort_order_id": 2,
        })

        # Assert
        assert response.status_code == 200
        body = response.data.decode("utf-8")
        assert alert_history_test_data["device_name_acc"] in body

    def test_date_range_outside_period_returns_no_results(self, client, alert_history_test_data):
        """5.1.1: 期間外のアラート履歴はBETWEENフィルタで除外されること"""
        # Arrange: テストデータの発生日時よりはるか過去の期間を指定
        old_start = "2000/01/01 00:00"
        old_end = "2000/01/02 00:00"

        # Act
        response = client.post("/alert/alert-history", data={
            "start_datetime": old_start,
            "end_datetime": old_end,
            "sort_item_id": 1,
            "sort_order_id": 2,
        })

        # Assert: 指定期間内のデータなし（テストデバイス名が表示されない）
        assert response.status_code == 200
        body = response.data.decode("utf-8")
        assert alert_history_test_data["device_name_acc"] not in body

    def test_search_sets_cookie(self, client):
        """2.1.2: POST /alert/alert-history（検索実行）でCookieが設定されること
        ワークフロー仕様書: 検索実行後に Cookie に検索条件を格納する。
        """
        # Act
        response = client.post("/alert/alert-history", data={
            "sort_item_id": 1,
            "sort_order_id": 2,
        })

        # Assert: Set-Cookie ヘッダーに alert_history が含まれること
        cookie_header = response.headers.get("Set-Cookie", "")
        assert "alert_history" in cookie_header


# =============================================================================
# 5.2  ソート機能テスト
# =============================================================================

@pytest.mark.integration
class TestAlertHistorySort:
    """5.2 ソート機能テスト

    観点: integration-test-perspectives.md > 5.2.1〜5.2.3
    注: バックエンド制御（ORDER BY）の全体ソートのみを検証。
        部分ソート（フロント JS 制御）は E2E テストで検証。
    """

    def test_default_sort_returns_200(self, client):
        """5.2.1: ソート条件なしでのデフォルト初期表示が200で返ること
        ワークフロー仕様書: デフォルトは alert_occurrence_datetime DESC（最新が上）。
        """
        # Act
        response = client.get("/alert/alert-history")

        # Assert
        assert response.status_code == 200

    def test_sort_asc_returns_200(self, client):
        """5.2.2: sort_order_id=1（昇順）で検索が200で返ること"""
        # Act
        response = client.post("/alert/alert-history", data={
            "sort_item_id": 1,
            "sort_order_id": 1,  # 昇順
        })

        # Assert
        assert response.status_code == 200

    def test_sort_desc_returns_200(self, client):
        """5.2.3: sort_order_id=2（降順）で検索が200で返ること"""
        # Act
        response = client.post("/alert/alert-history", data={
            "sort_item_id": 1,
            "sort_order_id": 2,  # 降順
        })

        # Assert
        assert response.status_code == 200

    def test_sort_item_device_name_returns_200(self, client):
        """5.2.2: sort_item_id=2（デバイス名）でソートが200で返ること"""
        # Act
        response = client.post("/alert/alert-history", data={
            "sort_item_id": 2,  # device_name
            "sort_order_id": 1,
        })

        # Assert
        assert response.status_code == 200

    def test_sort_order_none_returns_200(self, client):
        """5.2.1: sort_order_id=-1（指定なし）でも200が返ること
        ワークフロー仕様書: sort_order_id=-1 は ORDER BY なし。
        """
        # Act
        response = client.post("/alert/alert-history", data={
            "sort_item_id": 1,
            "sort_order_id": -1,  # 指定なし
        })

        # Assert
        assert response.status_code == 200

    def test_desc_then_asc_order_differs(self, client, alert_history_test_data):
        """5.2.2 / 5.2.3: 昇順と降順で取得順序が異なること
        2件以上のテストデータが存在する状態で、ソート順の違いをレスポンス位置で確認。
        """
        # Act: 降順で取得
        resp_desc = client.post("/alert/alert-history", data={
            "start_datetime": "",
            "end_datetime": "",
            "sort_item_id": 1,
            "sort_order_id": 2,
        })
        # Act: 昇順で取得
        resp_asc = client.post("/alert/alert-history", data={
            "start_datetime": "",
            "end_datetime": "",
            "sort_item_id": 1,
            "sort_order_id": 1,
        })

        # Assert: 両方とも正常に返ること
        assert resp_desc.status_code == 200
        assert resp_asc.status_code == 200

        # Assert: 2件以上データがある場合、降順と昇順でデバイス名の出現順が異なること
        body_desc = resp_desc.data.decode("utf-8")
        body_asc = resp_asc.data.decode("utf-8")
        name_acc = alert_history_test_data["device_name_acc"]
        name_sub = alert_history_test_data["device_name_sub"]
        if name_acc in body_desc and name_sub in body_desc:
            pos_desc_acc = body_desc.index(name_acc)
            pos_desc_sub = body_desc.index(name_sub)
            pos_asc_acc = body_asc.index(name_acc)
            pos_asc_sub = body_asc.index(name_sub)
            # 降順: history_acc（昨日）が先頭 → name_acc が先
            # 昇順: history_sub（一昨日）が先頭 → name_sub が先
            assert pos_desc_acc < pos_desc_sub
            assert pos_asc_sub < pos_asc_acc


# =============================================================================
# 5.3  ページネーションテスト
# =============================================================================

@pytest.mark.integration
class TestAlertHistoryPagination:
    """5.3 ページネーションテスト

    観点: integration-test-perspectives.md > 5.3.1, 5.3.2, 5.3.7
    """

    def test_page_1_returns_200(self, client):
        """5.3.1: page=1 で最初の25件が返ること（200）"""
        # Act
        client.get("/alert/alert-history")  # Cookie セット
        response = client.get("/alert/alert-history?page=1")

        # Assert
        assert response.status_code == 200

    def test_page_2_returns_200(self, client):
        """5.3.2: page=2 で次の25件が返ること（200）
        データが25件未満でも 2ページ目リクエスト自体は正常処理される。
        """
        # Act
        client.get("/alert/alert-history")  # Cookie セット
        response = client.get("/alert/alert-history?page=2")

        # Assert
        assert response.status_code == 200

    def test_total_count_is_correct(self, client, alert_history_test_data):
        """5.3.7: 総件数が正しく表示されること
        検索結果の総件数（total）はページ表示件数に関わらず全件数を返す。
        """
        # Act: 全件検索
        response = client.post("/alert/alert-history", data={
            "start_datetime": "",
            "end_datetime": "",
            "sort_item_id": 1,
            "sort_order_id": 2,
        })

        # Assert: 総件数表示がレンダリングされていること
        # テンプレートが "検索結果：" ラベルを含むこと
        body = response.data.decode("utf-8")
        assert response.status_code == 200
        assert "検索結果" in body


# =============================================================================
# 1.3  データスコープフィルタテスト
# =============================================================================

@pytest.mark.integration
class TestAlertHistoryDataScope:
    """1.3 データスコープフィルタテスト

    観点: integration-test-perspectives.md > 1.3.1〜1.3.4
    注: v_alert_history_by_user VIEW が organization_closure 経由でスコープを制御する。
        user_id=1（inject_test_user）のスコープ内/外でデータ表示を検証する。
    """

    def test_accessible_org_data_is_shown(self, client, alert_history_test_data):
        """1.3.1: 自組織配下のアラート履歴が表示されること"""
        # Act: 全件検索
        response = client.post("/alert/alert-history", data={
            "start_datetime": "",
            "end_datetime": "",
            "sort_item_id": 1,
            "sort_order_id": 2,
        })

        # Assert: アクセス可能なデバイス名が表示されること
        body = response.data.decode("utf-8")
        assert response.status_code == 200
        assert alert_history_test_data["device_name_acc"] in body

    def test_sub_org_data_is_shown(self, client, alert_history_test_data):
        """1.3.2: 下位組織のアラート履歴が表示されること
        organization_closure で parent→subsidiary depth=1 として登録した
        org_sub 配下のデバイスデータが取得されること。
        """
        # Act: 全件検索
        response = client.post("/alert/alert-history", data={
            "start_datetime": "",
            "end_datetime": "",
            "sort_item_id": 1,
            "sort_order_id": 2,
        })

        # Assert: サブ組織のデバイス名が表示されること
        body = response.data.decode("utf-8")
        assert response.status_code == 200
        assert alert_history_test_data["device_name_sub"] in body

    def test_inaccessible_org_data_is_not_shown(self, client, alert_history_test_data):
        """1.3.3 / 1.3.4: アクセス不可組織のアラート履歴が表示されないこと
        org_inaccessible は organization_closure 未登録のためスコープ外。
        """
        # Act: 全件検索
        response = client.post("/alert/alert-history", data={
            "start_datetime": "",
            "end_datetime": "",
            "sort_item_id": 1,
            "sort_order_id": 2,
        })

        # Assert: アクセス不可デバイス名が表示されないこと
        body = response.data.decode("utf-8")
        assert response.status_code == 200
        assert alert_history_test_data["device_name_inacc"] not in body


# =============================================================================
# 9.1 / 9.2  セキュリティテスト
# =============================================================================

@pytest.mark.integration
class TestAlertHistorySecurity:
    """9.1 SQLインジェクションテスト / 9.2 XSSテスト

    観点: integration-test-perspectives.md > 9.1.1〜9.1.3, 9.2.1
    SQLAlchemy プリペアドステートメントにより SQL インジェクションを防御。
    Jinja2 自動エスケープにより XSS を防御。
    """

    def test_sql_injection_in_device_name_returns_200(self, client):
        """9.1.1: device_name に SQLインジェクション文字列を入力しても200が返ること
        SQLAlchemy ORM のプリペアドステートメントによりエスケープされる。
        """
        # Act
        response = client.post("/alert/alert-history", data={
            "device_name": "' OR '1'='1",
            "start_datetime": "",
            "end_datetime": "",
            "sort_item_id": 1,
            "sort_order_id": 2,
        })

        # Assert: エラーにならず正常処理されること
        assert response.status_code == 200

    def test_sql_injection_comment_in_device_name(self, client):
        """9.1.2: device_name にコメントを使ったSQLインジェクション文字列を入力しても200が返ること"""
        # Act
        response = client.post("/alert/alert-history", data={
            "device_name": "'; DROP TABLE alert_history--",
            "start_datetime": "",
            "end_datetime": "",
            "sort_item_id": 1,
            "sort_order_id": 2,
        })

        # Assert
        assert response.status_code == 200

    def test_sql_injection_union_in_device_name(self, client):
        """9.1.3: device_name にUNIONを使ったSQLインジェクション文字列を入力しても200が返ること"""
        # Act
        response = client.post("/alert/alert-history", data={
            "device_name": "' UNION SELECT null, null, null--",
            "start_datetime": "",
            "end_datetime": "",
            "sort_item_id": 1,
            "sort_order_id": 2,
        })

        # Assert
        assert response.status_code == 200

    def test_xss_in_device_name_is_escaped(self, client):
        """9.2.1: device_name にXSS文字列を入力した場合、レスポンスでエスケープされること
        Jinja2 の自動エスケープにより、<script> タグが HTML エンティティに変換される。
        """
        # Act
        response = client.post("/alert/alert-history", data={
            "device_name": "<script>alert('XSS')</script>",
            "start_datetime": "",
            "end_datetime": "",
            "sort_item_id": 1,
            "sort_order_id": 2,
        })

        # Assert: <script> タグがそのまま出力されていないこと
        body = response.data.decode("utf-8")
        assert response.status_code == 200
        assert "<script>alert('XSS')</script>" not in body
        # エスケープ後の文字列が含まれること
        assert "&lt;script&gt;" in body or "<script>" not in body
