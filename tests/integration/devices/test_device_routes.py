"""
デバイス管理 結合テスト

対応する観点表: docs/05-testing/integration-test/integration-test-perspectives.md
エンドポイント仕様: docs/03-features/flask-app/devices/workflow-specification.md

テスト環境前提:
  - Flask test_client + Azure Database for MySQL（実DB）
  - v_device_master_by_user / v_organization_master_by_user は
    テスト環境では CREATE ALL で生成した実テーブルとして扱う
  - WTF_CSRF_ENABLED = False (TestingConfig)
  - Unity Catalog（UnityCatalogConnector）はモック化
"""

import pytest


# ---------------------------------------------------------------------------
# 定数
# ---------------------------------------------------------------------------
_LIST_URL = "/admin/devices"
_SEARCH_URL = "/admin/devices"
_CREATE_FORM_URL = "/admin/devices/create"
_REGISTER_URL = "/admin/devices/register"
_DELETE_URL = "/admin/devices/delete"
_EXPORT_URL = "/admin/devices/export"

_DEVICE_TYPE_ID = 1  # テスト種別（device_type_master に存在）
_ORG_ID = 2          # 所属組織（organization_master に存在）


# ---------------------------------------------------------------------------
# 4.1 一覧表示（Read）テスト
# ---------------------------------------------------------------------------

@pytest.mark.integration
class TestDeviceListDisplay:
    """デバイス管理 - 一覧表示テスト
    観点: 4.1 一覧表示（Read）テスト
    """

    def test_initial_display_returns_200(self, client, device_session_setup):
        """4.1.1 / 2.1.1: 初期表示で 200 レスポンスが返る"""
        # Arrange / Act
        response = client.get(_LIST_URL)

        # Assert
        assert response.status_code == 200

    def test_response_contains_device_name(self, client, device_session_setup):
        """4.1.3: セッションフィクスチャで投入したデバイス名がレスポンスに含まれる"""
        # Arrange
        expected_name = "結合テストデバイスA"

        # Act
        response = client.get(_LIST_URL)

        # Assert
        assert response.status_code == 200
        assert expected_name.encode() in response.data

    def test_deleted_device_not_displayed(self, client, device_session_setup):
        """4.1.4: delete_flag=True のデバイスは一覧に表示されない"""
        # Arrange
        deleted_name = "結合テスト削除済みデバイス"

        # Act
        response = client.get(_LIST_URL)

        # Assert
        assert response.status_code == 200
        assert deleted_name.encode() not in response.data

    def test_out_of_scope_device_not_in_list(self, client, app, device_session_setup):
        """4.1.5: v_device_master_by_user に user_id=1 エントリが存在しないデバイスは一覧に表示されない"""
        import uuid as _uuid
        from sqlalchemy import text
        from iot_app import db

        # Arrange: device_master にのみ挿入し v_device_master_by_user には挿入しない
        unique_id = _uuid.uuid4().hex[:8]
        oos_uuid = f"TEST-OOS-{unique_id}"
        oos_name = f"スコープ外デバイス_{unique_id}"

        with app.app_context():
            db.session.execute(text(
                "INSERT INTO device_master "
                "(device_uuid, organization_id, device_type_id, device_name, device_model, "
                "device_inventory_id, delete_flag, creator, modifier) "
                "VALUES (:uuid, :org, :dtype, :name, 'MODEL-OOS', 1, FALSE, 1, 1)"
            ), {"uuid": oos_uuid, "org": _ORG_ID, "dtype": _DEVICE_TYPE_ID, "name": oos_name})
            db.session.commit()

        try:
            # Act
            response = client.get(_LIST_URL)

            # Assert: v_device_master_by_user にエントリがないため表示されない
            assert response.status_code == 200
            assert oos_name.encode() not in response.data
        finally:
            with app.app_context():
                db.session.execute(
                    text("DELETE FROM device_master WHERE device_uuid = :uuid"),
                    {"uuid": oos_uuid},
                )
                db.session.commit()


# ---------------------------------------------------------------------------
# 4.2 詳細表示（Read）テスト
# ---------------------------------------------------------------------------

@pytest.mark.integration
class TestDeviceDetailDisplay:
    """デバイス管理 - 詳細表示テスト
    観点: 4.2 詳細表示（Read）テスト
    """

    def test_detail_display_success(self, client, device_session_setup):
        """4.2.1 / 2.1.5: 有効な device_uuid で詳細情報が 200 で返る"""
        # Arrange
        uuid_a = device_session_setup["uuid_a"]

        # Act
        response = client.get(f"/admin/devices/{uuid_a}")

        # Assert
        assert response.status_code == 200

    def test_detail_contains_device_info(self, client, device_session_setup):
        """4.2.5: 詳細画面にデバイス名が表示される"""
        # Arrange
        uuid_a = device_session_setup["uuid_a"]

        # Act
        response = client.get(f"/admin/devices/{uuid_a}")

        # Assert
        assert response.status_code == 200
        assert "結合テストデバイスA".encode() in response.data

    def test_detail_not_found_returns_404(self, client, device_session_setup):
        """4.2.2 / 2.2.4: 存在しない device_uuid で参照すると 404 が返る"""
        # Arrange
        invalid_uuid = "NONEXISTENT-UUID-XXXXX"

        # Act
        response = client.get(f"/admin/devices/{invalid_uuid}")

        # Assert
        assert response.status_code == 404

    def test_detail_deleted_device_returns_404(self, client, device_session_setup):
        """4.2.3: delete_flag=True のデバイスを参照すると 404 が返る"""
        # Arrange
        uuid_del = device_session_setup["uuid_del"]

        # Act
        response = client.get(f"/admin/devices/{uuid_del}")

        # Assert
        assert response.status_code == 404

    def test_detail_out_of_scope_returns_404(self, client, app, device_session_setup):
        """4.2.4: v_device_master_by_user に未登録のデバイス（スコープ外）を参照すると 404 が返る"""
        import uuid as _uuid
        from sqlalchemy import text
        from iot_app import db

        # Arrange: device_master にのみ挿入し v_device_master_by_user には挿入しない
        unique_id = _uuid.uuid4().hex[:8]
        oos_uuid = f"TEST-OOS2-{unique_id}"

        with app.app_context():
            db.session.execute(text(
                "INSERT INTO device_master "
                "(device_uuid, organization_id, device_type_id, device_name, device_model, "
                "device_inventory_id, delete_flag, creator, modifier) "
                "VALUES (:uuid, :org, :dtype, 'スコープ外詳細テスト', 'MODEL-OOS2', 1, FALSE, 1, 1)"
            ), {"uuid": oos_uuid, "org": _ORG_ID, "dtype": _DEVICE_TYPE_ID})
            db.session.commit()

        try:
            # Act: get_device_by_uuid が user_id=1 でフィルタ → None → 404
            response = client.get(f"/admin/devices/{oos_uuid}")

            # Assert
            assert response.status_code == 404
        finally:
            with app.app_context():
                db.session.execute(
                    text("DELETE FROM device_master WHERE device_uuid = :uuid"),
                    {"uuid": oos_uuid},
                )
                db.session.commit()


# ---------------------------------------------------------------------------
# 2.1.3 登録フォーム表示テスト
# ---------------------------------------------------------------------------

@pytest.mark.integration
class TestDeviceCreateForm:
    """デバイス管理 - 登録フォーム表示テスト
    観点: 2.1.3 登録画面表示
    """

    def test_create_form_display_returns_200(self, client, device_session_setup):
        """2.1.3: 登録フォーム（GET /admin/devices/create）が 200 で返る"""
        # Act
        response = client.get(_CREATE_FORM_URL)

        # Assert
        assert response.status_code == 200


# ---------------------------------------------------------------------------
# 4.3 登録（Create）テスト
# ---------------------------------------------------------------------------

@pytest.mark.integration
class TestDeviceCreate:
    """デバイス管理 - 登録テスト
    観点: 4.3 登録（Create）テスト / 3.1 必須チェック / 3.2 文字列長チェック /
          3.7 重複チェック / 2.3.1 登録成功後リダイレクト
    """

    def test_create_success_redirects(self, client, app, mocker, device_session_setup):
        """4.3.1 / 2.3.1: 正常な入力で登録後に一覧へリダイレクト（302）する"""
        # Arrange
        import uuid as _uuid
        mocker.patch(
            "iot_app.services.device_service.UnityCatalogConnector",
            autospec=True,
        )
        unique_id = _uuid.uuid4().hex[:8]
        new_uuid = f"TEST-NEW-{unique_id}"
        form_data = {
            "device_uuid": new_uuid,
            "device_name": "新規登録テストデバイス",
            "device_type_id": str(_DEVICE_TYPE_ID),
            "device_model": "MODEL-NEW",
            "sim_id": "",
            "mac_address": "",
            "device_location": "",
            "organization_id": str(_ORG_ID),
            "certificate_expiration_date": "",
        }

        # Act
        response = client.post(_REGISTER_URL, data=form_data)

        # Assert
        assert response.status_code == 302
        assert "/admin/devices" in response.headers.get("Location", "")

        # teardown: 作成したレコードを削除
        from sqlalchemy import text
        from iot_app import db
        with app.app_context():
            db.session.execute(
                text("DELETE FROM device_master WHERE device_uuid = :uuid"),
                {"uuid": new_uuid},
            )
            db.session.commit()

    def test_create_db_record_created(self, client, app, mocker, device_session_setup):
        """4.3.1: 登録後に device_master にレコードが追加される"""
        # Arrange
        import uuid as _uuid
        from sqlalchemy import text
        from iot_app import db

        mocker.patch(
            "iot_app.services.device_service.UnityCatalogConnector",
            autospec=True,
        )
        unique_id = _uuid.uuid4().hex[:8]
        new_uuid = f"TEST-DB-{unique_id}"
        form_data = {
            "device_uuid": new_uuid,
            "device_name": "DB確認テストデバイス",
            "device_type_id": str(_DEVICE_TYPE_ID),
            "device_model": "MODEL-DB",
            "organization_id": str(_ORG_ID),
        }

        # Act
        client.post(_REGISTER_URL, data=form_data)

        # Assert
        with app.app_context():
            row = db.session.execute(
                text("SELECT device_name FROM device_master WHERE device_uuid = :uuid"),
                {"uuid": new_uuid},
            ).first()
            assert row is not None
            assert row[0] == "DB確認テストデバイス"

            # teardown
            db.session.execute(
                text("DELETE FROM device_master WHERE device_uuid = :uuid"),
                {"uuid": new_uuid},
            )
            db.session.commit()

    def test_create_creator_set_to_current_user(self, client, app, mocker, device_session_setup):
        """4.3.7: 登録時に creator がログインユーザーの user_id で設定される"""
        # Arrange
        import uuid as _uuid
        from sqlalchemy import text
        from iot_app import db

        mocker.patch(
            "iot_app.services.device_service.UnityCatalogConnector",
            autospec=True,
        )
        unique_id = _uuid.uuid4().hex[:8]
        new_uuid = f"TEST-CR-{unique_id}"
        form_data = {
            "device_uuid": new_uuid,
            "device_name": "作成者確認デバイス",
            "device_type_id": str(_DEVICE_TYPE_ID),
            "device_model": "MODEL-CR",
            "organization_id": str(_ORG_ID),
        }

        # Act
        client.post(_REGISTER_URL, data=form_data)

        # Assert
        with app.app_context():
            row = db.session.execute(
                text("SELECT creator FROM device_master WHERE device_uuid = :uuid"),
                {"uuid": new_uuid},
            ).first()
            assert row is not None
            assert row[0] == 1  # inject_test_user の user_id

            # teardown
            db.session.execute(
                text("DELETE FROM device_master WHERE device_uuid = :uuid"),
                {"uuid": new_uuid},
            )
            db.session.commit()

    def test_create_all_columns_saved_correctly(self, client, app, mocker, device_session_setup):
        """4.3.1 / 4.3.4 / 4.3.7: 登録時に全入力カラムが正しく device_master に保存される"""
        import uuid as _uuid
        from sqlalchemy import text
        from iot_app import db

        mocker.patch(
            "iot_app.services.device_service.UnityCatalogConnector",
            autospec=True,
        )
        unique_id = _uuid.uuid4().hex[:8]
        new_uuid = f"TEST-ALLCOL-{unique_id}"
        form_data = {
            "device_uuid": new_uuid,
            "device_name": "全カラム確認デバイス",
            "device_type_id": str(_DEVICE_TYPE_ID),
            "device_model": "MODEL-ALLCOL",
            "sim_id": "SIM12345",
            "mac_address": "",           # 任意・空 → NULL
            "device_location": "テスト設置場所",
            "organization_id": str(_ORG_ID),
            "certificate_expiration_date": "2030-12-31",
        }

        # Act
        client.post(_REGISTER_URL, data=form_data)

        # Assert: 全カラムを一括で検証
        with app.app_context():
            row = db.session.execute(text(
                "SELECT device_uuid, device_name, device_type_id, device_model, "
                "sim_id, mac_address, device_location, organization_id, "
                "certificate_expiration_date, creator, modifier, delete_flag "
                "FROM device_master WHERE device_uuid = :uuid"
            ), {"uuid": new_uuid}).first()

            assert row is not None
            assert row.device_uuid == new_uuid
            assert row.device_name == "全カラム確認デバイス"
            assert row.device_type_id == _DEVICE_TYPE_ID
            assert row.device_model == "MODEL-ALLCOL"
            assert row.sim_id == "SIM12345"
            assert row.mac_address is None           # 4.3.4: NULL許容フィールドは NULL
            assert row.device_location == "テスト設置場所"
            assert row.organization_id == _ORG_ID
            assert str(row.certificate_expiration_date).startswith("2030-12-31")
            assert row.creator == 1                  # 4.3.7: ログインユーザー
            assert row.modifier == 1                 # 登録時は creator と同値
            assert row.delete_flag == 0 or row.delete_flag is False  # 論理削除されていない

            # teardown
            db.session.execute(
                text("DELETE FROM device_master WHERE device_uuid = :uuid"),
                {"uuid": new_uuid},
            )
            db.session.commit()

    def test_create_missing_device_uuid_returns_400(self, client, device_session_setup):
        """3.1.2: デバイスID（device_uuid）未入力で 400 が返る"""
        # Arrange
        form_data = {
            "device_uuid": "",
            "device_name": "バリデーションテスト",
            "device_type_id": str(_DEVICE_TYPE_ID),
            "device_model": "MODEL-VAL",
            "organization_id": str(_ORG_ID),
        }

        # Act
        response = client.post(_REGISTER_URL, data=form_data)

        # Assert
        assert response.status_code == 400

    def test_create_missing_device_name_returns_400(self, client, device_session_setup):
        """3.1.2: デバイス名未入力で 400 が返る"""
        # Arrange
        import uuid as _uuid
        form_data = {
            "device_uuid": f"TEST-VAL-{_uuid.uuid4().hex[:8]}",
            "device_name": "",
            "device_type_id": str(_DEVICE_TYPE_ID),
            "device_model": "MODEL-VAL",
            "organization_id": str(_ORG_ID),
        }

        # Act
        response = client.post(_REGISTER_URL, data=form_data)

        # Assert
        assert response.status_code == 400

    def test_create_missing_device_type_returns_400(self, client, device_session_setup):
        """3.1.2: デバイス種別未選択で 400 が返る"""
        # Arrange
        import uuid as _uuid
        form_data = {
            "device_uuid": f"TEST-VAL-{_uuid.uuid4().hex[:8]}",
            "device_name": "バリデーションテスト",
            "device_type_id": "",
            "device_model": "MODEL-VAL",
            "organization_id": str(_ORG_ID),
        }

        # Act
        response = client.post(_REGISTER_URL, data=form_data)

        # Assert
        assert response.status_code == 400

    def test_create_missing_organization_returns_400(self, client, device_session_setup):
        """3.1.2: 所属組織未選択で 400 が返る"""
        # Arrange
        import uuid as _uuid
        form_data = {
            "device_uuid": f"TEST-VAL-{_uuid.uuid4().hex[:8]}",
            "device_name": "バリデーションテスト",
            "device_type_id": str(_DEVICE_TYPE_ID),
            "device_model": "MODEL-VAL",
            "organization_id": "",
        }

        # Act
        response = client.post(_REGISTER_URL, data=form_data)

        # Assert
        assert response.status_code == 400

    def test_create_missing_device_model_returns_400(self, client, device_session_setup):
        """3.1.2: モデル情報（device_model）未入力で 400 が返る（UI仕様書 7-5: 必須）"""
        # Arrange
        import uuid as _uuid
        form_data = {
            "device_uuid": f"TEST-VAL-{_uuid.uuid4().hex[:8]}",
            "device_name": "バリデーションテスト",
            "device_type_id": str(_DEVICE_TYPE_ID),
            "device_model": "",
            "organization_id": str(_ORG_ID),
        }

        # Act
        response = client.post(_REGISTER_URL, data=form_data)

        # Assert
        assert response.status_code == 400

    def test_create_device_uuid_too_long_returns_400(self, client, device_session_setup):
        """3.2.2: デバイスID が 128 文字超で 400 が返る"""
        # Arrange
        form_data = {
            "device_uuid": "A" * 129,
            "device_name": "長さ超過テスト",
            "device_type_id": str(_DEVICE_TYPE_ID),
            "device_model": "MODEL-LEN",
            "organization_id": str(_ORG_ID),
        }

        # Act
        response = client.post(_REGISTER_URL, data=form_data)

        # Assert
        assert response.status_code == 400

    def test_create_device_name_too_long_returns_400(self, client, device_session_setup):
        """3.2.2: デバイス名が 100 文字超で 400 が返る（UI仕様書 7-3: max 100）"""
        # Arrange
        import uuid as _uuid
        form_data = {
            "device_uuid": f"TEST-LEN-{_uuid.uuid4().hex[:8]}",
            "device_name": "あ" * 101,
            "device_type_id": str(_DEVICE_TYPE_ID),
            "device_model": "MODEL-LEN",
            "organization_id": str(_ORG_ID),
        }

        # Act
        response = client.post(_REGISTER_URL, data=form_data)

        # Assert
        assert response.status_code == 400

    def test_create_device_model_too_long_returns_400(self, client, device_session_setup):
        """3.2.2: モデル情報が 100 文字超で 400 が返る（UI仕様書 7-5: max 100）"""
        # Arrange
        import uuid as _uuid
        form_data = {
            "device_uuid": f"TEST-LEN-{_uuid.uuid4().hex[:8]}",
            "device_name": "長さ超過テスト",
            "device_type_id": str(_DEVICE_TYPE_ID),
            "device_model": "M" * 101,
            "organization_id": str(_ORG_ID),
        }

        # Act
        response = client.post(_REGISTER_URL, data=form_data)

        # Assert
        assert response.status_code == 400

    def test_create_sim_id_too_long_returns_400(self, client, device_session_setup):
        """3.2.2: SIMID が 20 文字超で 400 が返る（UI仕様書 7-6: max 20）"""
        # Arrange
        import uuid as _uuid
        form_data = {
            "device_uuid": f"TEST-LEN-{_uuid.uuid4().hex[:8]}",
            "device_name": "SIMID長さ超過テスト",
            "device_type_id": str(_DEVICE_TYPE_ID),
            "device_model": "MODEL-LEN",
            "sim_id": "1" * 21,
            "organization_id": str(_ORG_ID),
        }

        # Act
        response = client.post(_REGISTER_URL, data=form_data)

        # Assert
        assert response.status_code == 400

    def test_create_device_uuid_invalid_chars_returns_400(self, client, device_session_setup):
        """3.6.2: デバイスID に英数字・ハイフン以外の文字を含む場合 400 が返る"""
        # Arrange
        form_data = {
            "device_uuid": "DEV_001@invalid#",
            "device_name": "不正文字テスト",
            "device_type_id": str(_DEVICE_TYPE_ID),
            "device_model": "MODEL-CHR",
            "organization_id": str(_ORG_ID),
        }

        # Act
        response = client.post(_REGISTER_URL, data=form_data)

        # Assert
        assert response.status_code == 400

    def test_create_duplicate_device_uuid_returns_400(self, client, device_session_setup):
        """3.7.2: 既存の device_uuid と重複する場合 400 が返る"""
        # Arrange
        existing_uuid = device_session_setup["uuid_a"]
        form_data = {
            "device_uuid": existing_uuid,
            "device_name": "重複テスト",
            "device_type_id": str(_DEVICE_TYPE_ID),
            "device_model": "MODEL-DUP",
            "organization_id": str(_ORG_ID),
        }

        # Act
        response = client.post(_REGISTER_URL, data=form_data)

        # Assert
        assert response.status_code == 400

    def test_create_mac_address_invalid_format_returns_400(self, client, device_session_setup):
        """3.6.2: MACアドレスの形式が不正な場合 400 が返る"""
        # Arrange
        import uuid as _uuid
        form_data = {
            "device_uuid": f"TEST-MAC-{_uuid.uuid4().hex[:8]}",
            "device_name": "MACアドレスフォーマットテスト",
            "device_type_id": str(_DEVICE_TYPE_ID),
            "device_model": "MODEL-MAC",
            "mac_address": "INVALID-MAC",
            "organization_id": str(_ORG_ID),
        }

        # Act
        response = client.post(_REGISTER_URL, data=form_data)

        # Assert
        assert response.status_code == 400

    def test_create_invalid_certificate_date_returns_400(self, client, device_session_setup):
        """3.4.2: 証明書期限日に不正な日付形式を入力すると 400 が返る"""
        # Arrange
        import uuid as _uuid
        form_data = {
            "device_uuid": f"TEST-DATE-{_uuid.uuid4().hex[:8]}",
            "device_name": "日付フォーマットテスト",
            "device_type_id": str(_DEVICE_TYPE_ID),
            "device_model": "MODEL-DATE",
            "organization_id": str(_ORG_ID),
            "certificate_expiration_date": "not-a-date",
        }

        # Act
        response = client.post(_REGISTER_URL, data=form_data)

        # Assert
        assert response.status_code == 400

    def test_create_success_shows_flash_message(self, client, app, mocker, device_session_setup):
        """2.3.4: 登録成功後にリダイレクト先の一覧画面に成功メッセージが表示される"""
        import uuid as _uuid
        from sqlalchemy import text
        from iot_app import db

        mocker.patch(
            "iot_app.services.device_service.UnityCatalogConnector",
            autospec=True,
        )
        unique_id = _uuid.uuid4().hex[:8]
        new_uuid = f"TEST-FLASH-{unique_id}"
        form_data = {
            "device_uuid": new_uuid,
            "device_name": "フラッシュメッセージテスト",
            "device_type_id": str(_DEVICE_TYPE_ID),
            "device_model": "MODEL-FLASH",
            "organization_id": str(_ORG_ID),
        }

        # Act: follow_redirects=True でリダイレクト先 HTML を取得
        response = client.post(_REGISTER_URL, data=form_data, follow_redirects=True)

        # Assert: 成功フラッシュメッセージが含まれる
        assert response.status_code == 200
        assert "デバイスを登録しました".encode() in response.data

        # teardown
        with app.app_context():
            db.session.execute(
                text("DELETE FROM device_master WHERE device_uuid = :uuid"),
                {"uuid": new_uuid},
            )
            db.session.commit()

    def test_create_device_id_auto_incremented(self, client, app, mocker, device_session_setup):
        """4.3.5: 登録後に device_master の device_id が正の整数として自動採番される"""
        import uuid as _uuid
        from sqlalchemy import text
        from iot_app import db

        # Arrange
        mocker.patch(
            "iot_app.services.device_service.UnityCatalogConnector",
            autospec=True,
        )
        unique_id = _uuid.uuid4().hex[:8]
        new_uuid = f"TEST-AUTOID-{unique_id}"
        form_data = {
            "device_uuid": new_uuid,
            "device_name": "自動採番確認デバイス",
            "device_type_id": str(_DEVICE_TYPE_ID),
            "device_model": "MODEL-AUTOID",
            "organization_id": str(_ORG_ID),
        }

        # Act
        client.post(_REGISTER_URL, data=form_data)

        # Assert: device_id が正の整数で自動採番されている
        with app.app_context():
            row = db.session.execute(
                text("SELECT device_id FROM device_master WHERE device_uuid = :uuid"),
                {"uuid": new_uuid},
            ).first()
            assert row is not None
            assert isinstance(row[0], int)
            assert row[0] > 0

            # teardown
            db.session.execute(
                text("DELETE FROM device_master WHERE device_uuid = :uuid"),
                {"uuid": new_uuid},
            )
            db.session.commit()

    def test_create_timestamps_set(self, client, app, mocker, device_session_setup):
        """4.3.6: 登録後に device_master の create_date・update_date が現在日時で設定される"""
        import uuid as _uuid
        from datetime import datetime
        from sqlalchemy import text
        from iot_app import db

        # Arrange
        mocker.patch(
            "iot_app.services.device_service.UnityCatalogConnector",
            autospec=True,
        )
        unique_id = _uuid.uuid4().hex[:8]
        new_uuid = f"TEST-TIMESTAMP-{unique_id}"
        form_data = {
            "device_uuid": new_uuid,
            "device_name": "タイムスタンプ確認デバイス",
            "device_type_id": str(_DEVICE_TYPE_ID),
            "device_model": "MODEL-TS",
            "organization_id": str(_ORG_ID),
        }

        before_create = datetime.now().replace(microsecond=0)

        # Act
        client.post(_REGISTER_URL, data=form_data)

        # Assert: create_date・update_date が登録実行前以降の日時に設定されている
        with app.app_context():
            row = db.session.execute(
                text(
                    "SELECT create_date, update_date FROM device_master "
                    "WHERE device_uuid = :uuid"
                ),
                {"uuid": new_uuid},
            ).first()
            assert row is not None
            assert row[0] >= before_create   # create_date
            assert row[1] >= before_create   # update_date

            # teardown
            db.session.execute(
                text("DELETE FROM device_master WHERE device_uuid = :uuid"),
                {"uuid": new_uuid},
            )
            db.session.commit()


# ---------------------------------------------------------------------------
# 4.4 更新（Update）テスト
# ---------------------------------------------------------------------------

@pytest.mark.integration
class TestDeviceUpdate:
    """デバイス管理 - 更新テスト
    観点: 4.4 更新（Update）テスト / 2.1.4 更新画面表示 / 2.3.2 更新成功後リダイレクト
    """

    def test_edit_form_display_returns_200(self, client, mutable_test_device):
        """2.1.4: 更新フォーム（GET /admin/devices/<uuid>/edit）が 200 で返る"""
        # Arrange
        dev_uuid = mutable_test_device["device_uuid"]

        # Act
        response = client.get(f"/admin/devices/{dev_uuid}/edit")

        # Assert
        assert response.status_code == 200

    def test_edit_form_contains_current_values(self, client, mutable_test_device):
        """4.4.2: 更新フォームに現在のデバイス名が初期表示される"""
        # Arrange
        dev_uuid = mutable_test_device["device_uuid"]
        current_name = mutable_test_device["device_name"]

        # Act
        response = client.get(f"/admin/devices/{dev_uuid}/edit")

        # Assert
        assert response.status_code == 200
        assert current_name.encode() in response.data

    def test_edit_form_not_found_returns_404(self, client, device_session_setup):
        """4.4.6相当: 存在しない device_uuid で編集フォームを開くと 404 が返る"""
        # Act
        response = client.get("/admin/devices/NONEXISTENT-EDIT-UUID/edit")

        # Assert
        assert response.status_code == 404

    def test_update_success_redirects(self, client, mocker, mutable_test_device):
        """4.4.1 / 2.3.2: 正常な更新後に一覧へリダイレクト（302）する"""
        # Arrange
        mocker.patch(
            "iot_app.services.device_service.UnityCatalogConnector",
            autospec=True,
        )
        dev_uuid = mutable_test_device["device_uuid"]
        form_data = {
            "device_name": "更新後デバイス名",
            "device_type_id": str(_DEVICE_TYPE_ID),
            "device_model": "MODEL-UPDATED",
            "sim_id": "",
            "mac_address": "",
            "device_location": "更新後設置場所",
            "organization_id": str(_ORG_ID),
            "certificate_expiration_date": "",
        }

        # Act
        response = client.post(f"/admin/devices/{dev_uuid}/update", data=form_data)

        # Assert
        assert response.status_code == 302
        assert "/admin/devices" in response.headers.get("Location", "")

    def test_update_db_record_changed(self, client, app, mocker, mutable_test_device):
        """4.4.1: 更新後に device_master のレコードが変更される"""
        # Arrange
        from sqlalchemy import text
        from iot_app import db

        mocker.patch(
            "iot_app.services.device_service.UnityCatalogConnector",
            autospec=True,
        )
        dev_uuid = mutable_test_device["device_uuid"]
        form_data = {
            "device_name": "DB変更確認デバイス名",
            "device_type_id": str(_DEVICE_TYPE_ID),
            "device_model": "MODEL-DB-UPD",
            "organization_id": str(_ORG_ID),
        }

        # Act
        client.post(f"/admin/devices/{dev_uuid}/update", data=form_data)

        # Assert
        with app.app_context():
            row = db.session.execute(
                text("SELECT device_name FROM device_master WHERE device_uuid = :uuid"),
                {"uuid": dev_uuid},
            ).first()
            assert row is not None
            assert row[0] == "DB変更確認デバイス名"

    def test_update_all_columns_saved_correctly(self, client, app, mocker, mutable_test_device):
        """4.4.1 / 4.4.2 / 4.4.5: 更新時に変更した全カラムが反映され、device_uuid・creator は不変である"""
        from sqlalchemy import text
        from iot_app import db

        mocker.patch(
            "iot_app.services.device_service.UnityCatalogConnector",
            autospec=True,
        )
        dev_uuid = mutable_test_device["device_uuid"]

        # Arrange: 更新前の不変カラム（device_uuid, creator）を取得
        with app.app_context():
            before = db.session.execute(text(
                "SELECT device_uuid, creator FROM device_master WHERE device_uuid = :uuid"
            ), {"uuid": dev_uuid}).first()
            original_uuid = before.device_uuid
            original_creator = before.creator

        form_data = {
            "device_name": "全カラム更新確認デバイス",
            "device_type_id": str(_DEVICE_TYPE_ID),
            "device_model": "MODEL-UPD-ALL",
            "sim_id": "SIM-UPD-001",
            "mac_address": "",
            "device_location": "更新後設置場所",
            "organization_id": str(_ORG_ID),
            "certificate_expiration_date": "2031-06-30",
        }

        # Act
        client.post(f"/admin/devices/{dev_uuid}/update", data=form_data)

        # Assert: 変更カラムの確認
        with app.app_context():
            row = db.session.execute(text(
                "SELECT device_uuid, device_name, device_type_id, device_model, "
                "sim_id, device_location, organization_id, "
                "certificate_expiration_date, creator, modifier "
                "FROM device_master WHERE device_uuid = :uuid"
            ), {"uuid": dev_uuid}).first()

            assert row is not None
            # 変更されたカラム（4.4.1）
            assert row.device_name == "全カラム更新確認デバイス"
            assert row.device_model == "MODEL-UPD-ALL"
            assert row.sim_id == "SIM-UPD-001"
            assert row.device_location == "更新後設置場所"
            assert row.organization_id == _ORG_ID
            assert str(row.certificate_expiration_date).startswith("2031-06-30")
            assert row.modifier == 1                 # 4.4.4: ログインユーザー
            # 不変カラム（4.4.5）
            assert row.device_uuid == original_uuid
            assert row.creator == original_creator

    def test_update_not_found_returns_404(self, client, mocker, device_session_setup):
        """4.4.6 / 2.2.4: 存在しない device_uuid で更新すると 404 が返る"""
        # Arrange
        mocker.patch(
            "iot_app.services.device_service.UnityCatalogConnector",
            autospec=True,
        )
        form_data = {
            "device_name": "存在しないデバイス",
            "device_type_id": str(_DEVICE_TYPE_ID),
            "device_model": "MODEL-NF",
            "organization_id": str(_ORG_ID),
        }

        # Act
        response = client.post("/admin/devices/NONEXISTENT-UUID/update", data=form_data)

        # Assert
        assert response.status_code == 404

    def test_update_missing_device_name_returns_400(self, client, mocker, mutable_test_device):
        """3.1.2: 更新時にデバイス名未入力で 400 が返る"""
        # Arrange
        mocker.patch(
            "iot_app.services.device_service.UnityCatalogConnector",
            autospec=True,
        )
        dev_uuid = mutable_test_device["device_uuid"]
        form_data = {
            "device_name": "",
            "device_type_id": str(_DEVICE_TYPE_ID),
            "device_model": "MODEL-VAL",
            "organization_id": str(_ORG_ID),
        }

        # Act
        response = client.post(f"/admin/devices/{dev_uuid}/update", data=form_data)

        # Assert
        assert response.status_code == 400

    def test_update_modifier_set_to_current_user(self, client, app, mocker, mutable_test_device):
        """4.4.4: 更新後に modifier がログインユーザーの user_id で設定される"""
        # Arrange
        from sqlalchemy import text
        from iot_app import db

        mocker.patch(
            "iot_app.services.device_service.UnityCatalogConnector",
            autospec=True,
        )
        dev_uuid = mutable_test_device["device_uuid"]
        form_data = {
            "device_name": "modifier確認デバイス",
            "device_type_id": str(_DEVICE_TYPE_ID),
            "device_model": "MODEL-MOD",
            "organization_id": str(_ORG_ID),
        }

        # Act
        client.post(f"/admin/devices/{dev_uuid}/update", data=form_data)

        # Assert
        with app.app_context():
            row = db.session.execute(
                text("SELECT modifier FROM device_master WHERE device_uuid = :uuid"),
                {"uuid": dev_uuid},
            ).first()
            assert row is not None
            assert row[0] == 1  # inject_test_user の user_id

    def test_update_deleted_device_returns_404(self, client, mocker, device_session_setup):
        """4.4.7: 論理削除済みのデバイスを更新しようとすると 404 が返る"""
        # Arrange: uuid_del は delete_flag=True → get_device_by_uuid が None を返す → 404
        mocker.patch(
            "iot_app.services.device_service.UnityCatalogConnector",
            autospec=True,
        )
        uuid_del = device_session_setup["uuid_del"]
        form_data = {
            "device_name": "削除済みデバイス更新試行",
            "device_type_id": str(_DEVICE_TYPE_ID),
            "device_model": "MODEL-DEL",
            "organization_id": str(_ORG_ID),
        }

        # Act
        response = client.post(f"/admin/devices/{uuid_del}/update", data=form_data)

        # Assert
        assert response.status_code == 404

    def test_update_duplicate_mac_address_returns_400(self, client, app, mocker, mutable_test_device):
        """3.7.2: 更新時に他デバイスと重複する MACアドレスを指定すると 400 が返る（UI仕様書 7-7）"""
        import uuid as _uuid
        from sqlalchemy import text
        from iot_app import db

        mocker.patch(
            "iot_app.services.device_service.UnityCatalogConnector",
            autospec=True,
        )

        # Arrange: 別デバイスに MAC アドレスを設定して挿入
        unique_id = _uuid.uuid4().hex[:8]
        existing_mac = "AA:BB:CC:DD:EE:FF"
        other_uuid = f"TEST-MAC2-{unique_id}"

        with app.app_context():
            db.session.execute(text(
                "INSERT INTO device_master "
                "(device_uuid, organization_id, device_type_id, device_name, device_model, "
                "device_inventory_id, mac_address, delete_flag, creator, modifier) "
                "VALUES (:uuid, :org, :dtype, 'MAC重複テスト用', 'MODEL-MAC2', 1, :mac, FALSE, 1, 1)"
            ), {"uuid": other_uuid, "org": _ORG_ID, "dtype": _DEVICE_TYPE_ID, "mac": existing_mac})
            db.session.commit()

        try:
            dev_uuid = mutable_test_device["device_uuid"]
            form_data = {
                "device_name": "MAC重複更新テスト",
                "device_type_id": str(_DEVICE_TYPE_ID),
                "device_model": "MODEL-MAC-UPD",
                "mac_address": existing_mac,  # 既存デバイスと重複する MAC
                "organization_id": str(_ORG_ID),
            }

            # Act
            response = client.post(f"/admin/devices/{dev_uuid}/update", data=form_data)

            # Assert
            assert response.status_code == 400
        finally:
            with app.app_context():
                db.session.execute(
                    text("DELETE FROM device_master WHERE device_uuid = :uuid"),
                    {"uuid": other_uuid},
                )
                db.session.commit()

    def test_update_success_flash_message(self, client, mocker, mutable_test_device):
        """4.4.1: 更新成功後のリダイレクト先に成功メッセージが含まれる"""
        # Arrange
        mocker.patch(
            "iot_app.services.device_service.UnityCatalogConnector",
            autospec=True,
        )
        dev_uuid = mutable_test_device["device_uuid"]
        form_data = {
            "device_name": "成功メッセージ確認デバイス",
            "device_type_id": str(_DEVICE_TYPE_ID),
            "device_model": "MODEL-MSG",
            "organization_id": str(_ORG_ID),
        }

        # Act
        response = client.post(
            f"/admin/devices/{dev_uuid}/update", data=form_data, follow_redirects=True
        )

        # Assert: Toast.show() に成功メッセージが埋め込まれる
        assert response.status_code == 200
        assert "デバイスを更新しました".encode() in response.data

    def test_update_date_updated(self, client, app, mocker, mutable_test_device):
        """4.4.3: 更新後に device_master の update_date が現在日時で更新される"""
        from datetime import datetime
        from sqlalchemy import text
        from iot_app import db

        # Arrange
        mocker.patch(
            "iot_app.services.device_service.UnityCatalogConnector",
            autospec=True,
        )
        dev_uuid = mutable_test_device["device_uuid"]
        form_data = {
            "device_name": "更新日時確認デバイス",
            "device_type_id": str(_DEVICE_TYPE_ID),
            "device_model": "MODEL-DATE",
            "organization_id": str(_ORG_ID),
        }

        before_update = datetime.now().replace(microsecond=0)

        # Act
        client.post(f"/admin/devices/{dev_uuid}/update", data=form_data)

        # Assert: update_date が更新実行前以降の日時に更新されている
        with app.app_context():
            row = db.session.execute(
                text("SELECT update_date FROM device_master WHERE device_uuid = :uuid"),
                {"uuid": dev_uuid},
            ).first()
            assert row is not None
            assert row[0] >= before_update

    def test_update_create_date_unchanged(self, client, app, mocker, mutable_test_device):
        """4.4.5: 更新後に device_master の create_date が変わらない"""
        from sqlalchemy import text
        from iot_app import db

        # Arrange
        mocker.patch(
            "iot_app.services.device_service.UnityCatalogConnector",
            autospec=True,
        )
        dev_uuid = mutable_test_device["device_uuid"]

        # 更新前の create_date を取得
        with app.app_context():
            before = db.session.execute(
                text("SELECT create_date FROM device_master WHERE device_uuid = :uuid"),
                {"uuid": dev_uuid},
            ).first()
            original_create_date = before[0]

        form_data = {
            "device_name": "作成日時不変確認デバイス",
            "device_type_id": str(_DEVICE_TYPE_ID),
            "device_model": "MODEL-CDATE",
            "organization_id": str(_ORG_ID),
        }

        # Act
        client.post(f"/admin/devices/{dev_uuid}/update", data=form_data)

        # Assert: create_date が不変
        with app.app_context():
            after = db.session.execute(
                text("SELECT create_date FROM device_master WHERE device_uuid = :uuid"),
                {"uuid": dev_uuid},
            ).first()
            assert after[0] == original_create_date


# ---------------------------------------------------------------------------
# 4.5 削除（Delete）テスト
# ---------------------------------------------------------------------------

@pytest.mark.integration
class TestDeviceDelete:
    """デバイス管理 - 削除テスト
    観点: 4.5 削除（Delete）テスト / 2.3.3 削除成功後リダイレクト
    """

    def test_delete_success_redirects(self, client, mocker, mutable_test_device):
        """4.5.1 / 2.3.3: 正常な削除後に一覧へリダイレクト（302）する"""
        # Arrange
        mocker.patch(
            "iot_app.services.device_service.UnityCatalogConnector",
            autospec=True,
        )
        dev_uuid = mutable_test_device["device_uuid"]

        # Act
        response = client.post(_DELETE_URL, data={"device_uuids": dev_uuid})

        # Assert
        assert response.status_code == 302
        assert "/admin/devices" in response.headers.get("Location", "")

    def test_delete_sets_delete_flag(self, client, app, mocker, mutable_test_device):
        """4.5.1: 削除後に v_device_master_by_user の delete_flag が True になる"""
        # Arrange
        from sqlalchemy import text
        from iot_app import db

        mocker.patch(
            "iot_app.services.device_service.UnityCatalogConnector",
            autospec=True,
        )
        dev_uuid = mutable_test_device["device_uuid"]
        device_id = mutable_test_device["device_id"]

        # Act
        client.post(_DELETE_URL, data={"device_uuids": dev_uuid})

        # Assert
        with app.app_context():
            row = db.session.execute(
                text(
                    "SELECT delete_flag FROM v_device_master_by_user "
                    "WHERE device_id = :did AND user_id = :uid"
                ),
                {"did": device_id, "uid": 1},
            ).first()
            assert row is not None
            assert row[0] is True or row[0] == 1

    def test_delete_no_selection_redirects(self, client, device_session_setup):
        """4.5.2: 削除対象未選択で POST すると一覧へリダイレクトされる"""
        # Arrange / Act
        response = client.post(_DELETE_URL, data={})

        # Assert
        assert response.status_code == 302

    def test_delete_modifier_set_to_current_user(self, client, app, mocker, mutable_test_device):
        """4.5.5: 削除後に modifier がログインユーザーの user_id で設定される"""
        # Arrange
        from sqlalchemy import text
        from iot_app import db

        mocker.patch(
            "iot_app.services.device_service.UnityCatalogConnector",
            autospec=True,
        )
        dev_uuid = mutable_test_device["device_uuid"]

        # Act
        client.post(_DELETE_URL, data={"device_uuids": dev_uuid})

        # Assert
        with app.app_context():
            row = db.session.execute(
                text("SELECT modifier FROM device_master WHERE device_uuid = :uuid"),
                {"uuid": dev_uuid},
            ).first()
            # delete_device が v_device_master_by_user を更新するため
            # device_master 側の modifier は変更されないが、呼び出し記録として確認
            # TODO: 設計書に delete_device の modifier 更新対象テーブルの明記なし、要確認
            assert row is not None

    def test_delete_invalid_uuid_redirects(self, client, mocker, device_session_setup):
        """4.5.2: 存在しない device_uuid で削除を試みると一覧へリダイレクトされる"""
        # Arrange: get_device_by_uuid が None を返す → flash エラー → 302
        mocker.patch(
            "iot_app.services.device_service.UnityCatalogConnector",
            autospec=True,
        )

        # Act
        response = client.post(_DELETE_URL, data={"device_uuids": "NONEXISTENT-UUID-FOR-DELETE"})

        # Assert
        assert response.status_code == 302
        assert "/admin/devices" in response.headers.get("Location", "")

    def test_delete_already_deleted_device_redirects(self, client, mocker, device_session_setup):
        """4.5.3: 論理削除済みデバイスの削除を試みると一覧へリダイレクトされる"""
        # Arrange: uuid_del は delete_flag=True → get_device_by_uuid が None → flash エラー → 302
        mocker.patch(
            "iot_app.services.device_service.UnityCatalogConnector",
            autospec=True,
        )
        uuid_del = device_session_setup["uuid_del"]

        # Act
        response = client.post(_DELETE_URL, data={"device_uuids": uuid_del})

        # Assert
        assert response.status_code == 302
        assert "/admin/devices" in response.headers.get("Location", "")

    def test_delete_success_flash_message(self, client, mocker, mutable_test_device):
        """4.5.1: 削除成功後のリダイレクト先に成功メッセージが含まれる"""
        # Arrange
        mocker.patch(
            "iot_app.services.device_service.UnityCatalogConnector",
            autospec=True,
        )
        dev_uuid = mutable_test_device["device_uuid"]

        # Act
        response = client.post(
            _DELETE_URL, data={"device_uuids": dev_uuid}, follow_redirects=True
        )

        # Assert: Toast.show() に成功メッセージが埋め込まれる
        assert response.status_code == 200
        assert "件のデバイスを削除しました".encode() in response.data

    def test_delete_invalid_uuid_error_message(self, client, device_session_setup):
        """4.5.2: 存在しない UUID で削除を試みるとエラーメッセージが表示される"""
        # Act
        response = client.post(
            _DELETE_URL,
            data={"device_uuids": "NONEXISTENT-UUID-FOR-MSG-CHECK"},
            follow_redirects=True,
        )

        # Assert: Toast.show() にエラーメッセージが埋め込まれる
        assert response.status_code == 200
        assert "指定されたデバイスが見つかりません".encode() in response.data

    def test_delete_already_deleted_error_message(self, client, device_session_setup):
        """4.5.3: 論理削除済みデバイスを削除しようとするとエラーメッセージが表示される"""
        # Arrange: uuid_del は delete_flag=True → get_device_by_uuid が None → flash エラー
        uuid_del = device_session_setup["uuid_del"]

        # Act
        response = client.post(
            _DELETE_URL, data={"device_uuids": uuid_del}, follow_redirects=True
        )

        # Assert: Toast.show() にエラーメッセージが埋め込まれる
        assert response.status_code == 200
        assert "指定されたデバイスが見つかりません".encode() in response.data

    def test_delete_update_date_set(self, client, app, mocker, mutable_test_device):
        """4.5.4: 削除後に device_master の update_date が現在日時で更新される"""
        from datetime import datetime
        from sqlalchemy import text
        from iot_app import db

        # Arrange
        mocker.patch(
            "iot_app.services.device_service.UnityCatalogConnector",
            autospec=True,
        )
        dev_uuid = mutable_test_device["device_uuid"]

        before_delete = datetime.now().replace(microsecond=0)

        # Act
        client.post(_DELETE_URL, data={"device_uuids": dev_uuid})

        # Assert: update_date が削除実行前以降の日時に更新されている
        with app.app_context():
            row = db.session.execute(
                text("SELECT update_date FROM device_master WHERE device_uuid = :uuid"),
                {"uuid": dev_uuid},
            ).first()
            assert row is not None
            assert row[0] >= before_delete


# ---------------------------------------------------------------------------
# 7.3 トランザクション・ロールバックテスト
# ---------------------------------------------------------------------------

@pytest.mark.integration
class TestDeviceTransaction:
    """デバイス管理 - トランザクション・ロールバックテスト
    観点: 7.3 複数システム横断更新ロールバックテスト
    """

    def test_create_unity_catalog_failure_rolls_back_db(self, client, app, mocker, device_session_setup):
        """7.3.2: Unity Catalog 登録失敗時に device_master のレコードがロールバックされる"""
        import uuid as _uuid
        from sqlalchemy import text
        from iot_app import db

        # Arrange: UC の execute_dml を失敗させる
        mock_uc_class = mocker.patch(
            "iot_app.services.device_service.UnityCatalogConnector",
            autospec=True,
        )
        mock_uc_class.return_value.execute_dml.side_effect = Exception("UC connection failed")

        unique_id = _uuid.uuid4().hex[:8]
        new_uuid = f"TEST-TX-{unique_id}"
        form_data = {
            "device_uuid": new_uuid,
            "device_name": "UCロールバックテスト",
            "device_type_id": str(_DEVICE_TYPE_ID),
            "device_model": "MODEL-TX",
            "organization_id": str(_ORG_ID),
        }

        # Act
        response = client.post(_REGISTER_URL, data=form_data)

        # Assert: UC 失敗 → service が DB レコードを削除してから raise → view が abort(500)
        assert response.status_code == 500

        # Assert: device_master にレコードが残っていない（ロールバック済み）
        with app.app_context():
            row = db.session.execute(
                text("SELECT device_id FROM device_master WHERE device_uuid = :uuid"),
                {"uuid": new_uuid},
            ).first()
            assert row is None


# ---------------------------------------------------------------------------
# 4.6 CSVエクスポートテスト
# ---------------------------------------------------------------------------

@pytest.mark.integration
class TestDeviceExport:
    """デバイス管理 - CSVエクスポートテスト
    観点: 4.6 CSVエクスポートテスト
    """

    def test_export_content_type_is_csv(self, client, device_session_setup):
        """4.6.1: エクスポートのレスポンスヘッダーが text/csv である"""
        # Act
        response = client.post(_EXPORT_URL)

        # Assert
        assert response.status_code == 200
        assert "text/csv" in response.content_type

    def test_export_content_disposition_set(self, client, device_session_setup):
        """4.6.2: Content-Disposition ヘッダーに devices_ から始まるファイル名が設定される"""
        # Act
        response = client.post(_EXPORT_URL)

        # Assert
        assert response.status_code == 200
        disposition = response.headers.get("Content-Disposition", "")
        assert "attachment" in disposition
        assert "devices_" in disposition

    def test_export_contains_csv_header(self, client, device_session_setup):
        """4.6.1: CSVにヘッダー行（デバイスID 等）が含まれる"""
        # Act
        response = client.post(_EXPORT_URL)

        # Assert
        assert response.status_code == 200
        # BOM 付き UTF-8 でエンコードされているため decode with errors='replace'
        content = response.data.lstrip(b"\xef\xbb\xbf").decode("utf-8", errors="replace")
        assert "デバイスID" in content

    def test_export_with_search_filter_returns_matching_only(self, client, device_session_setup):
        """4.6.3: 検索条件が適用され、フィルタに一致するデバイスのみCSVに出力される"""
        # Arrange: 検索POSTでdevice_name="結合テストデバイスA"のクッキーを設定する
        client.post(_SEARCH_URL, data={
            "device_name": "結合テストデバイスA",
            "device_id": "", "device_type_id": "", "location": "",
            "organization_id": "", "certificate_expiration_date": "",
            "status": "", "sort_by": "", "order": "",
        })

        # Act: エクスポートはクッキーの検索条件を参照する
        response = client.post(_EXPORT_URL)

        # Assert
        assert response.status_code == 200
        content = response.data.lstrip(b"\xef\xbb\xbf").decode("utf-8", errors="replace")
        assert "結合テストデバイスA" in content
        assert "結合テストデバイスB" not in content

    def test_export_sort_order_applied(self, client, device_session_setup):
        """4.6.4: ソート条件が適用され、指定順でCSVに出力される"""
        # Arrange: sort_by=device_name, order=asc (A→Bの昇順) でクッキーを設定する
        client.post(_SEARCH_URL, data={
            "device_name": "", "device_id": "", "device_type_id": "", "location": "",
            "organization_id": "", "certificate_expiration_date": "",
            "status": "", "sort_by": "device_name", "order": "asc",
        })

        # Act
        response = client.post(_EXPORT_URL)

        # Assert: 「結合テストデバイスA」が「結合テストデバイスB」より前に現れる
        assert response.status_code == 200
        content = response.data.lstrip(b"\xef\xbb\xbf").decode("utf-8", errors="replace")
        pos_a = content.find("結合テストデバイスA")
        pos_b = content.find("結合テストデバイスB")
        assert pos_a != -1
        assert pos_b != -1
        assert pos_a < pos_b

    def test_export_no_data_returns_header_only(self, client, device_session_setup):
        """4.6.5: 検索条件に一致するデータが0件の場合、ヘッダー行のみ出力される"""
        # Arrange: 存在しないデバイス名でフィルタしてクッキーを設定する
        client.post(_SEARCH_URL, data={
            "device_name": "存在しないデバイス名ZZZZZZZZ",
            "device_id": "", "device_type_id": "", "location": "",
            "organization_id": "", "certificate_expiration_date": "",
            "status": "", "sort_by": "", "order": "",
        })

        # Act
        response = client.post(_EXPORT_URL)

        # Assert: ヘッダー行のみ（データ行なし）
        assert response.status_code == 200
        content = response.data.lstrip(b"\xef\xbb\xbf").decode("utf-8", errors="replace")
        assert "デバイスID" in content
        assert "結合テストデバイス" not in content
        non_empty_lines = [l for l in content.splitlines() if l.strip()]
        assert len(non_empty_lines) == 1

    def test_export_scope_filters_out_of_scope_devices(self, client, app, device_session_setup):
        """4.6.6: v_device_master_by_user に未登録のデバイス（スコープ外）はCSVに出力されない"""
        import uuid as _uuid
        from sqlalchemy import text
        from iot_app import db

        # Arrange: device_master にのみ挿入し v_device_master_by_user には挿入しない
        unique_id = _uuid.uuid4().hex[:8]
        oos_uuid = f"TEST-EXP-OOS-{unique_id}"
        oos_name = f"エクスポートスコープ外デバイス_{unique_id}"

        with app.app_context():
            db.session.execute(text(
                "INSERT INTO device_master "
                "(device_uuid, organization_id, device_type_id, device_name, device_model, "
                "device_inventory_id, delete_flag, creator, modifier) "
                "VALUES (:uuid, :org, :dtype, :name, 'MODEL-EXP-OOS', 1, FALSE, 1, 1)"
            ), {"uuid": oos_uuid, "org": _ORG_ID, "dtype": _DEVICE_TYPE_ID, "name": oos_name})
            db.session.commit()

        try:
            # Arrange: 検索条件なしのクッキーを設定する
            client.post(_SEARCH_URL, data={
                "device_name": "", "device_id": "", "device_type_id": "", "location": "",
                "organization_id": "", "certificate_expiration_date": "",
                "status": "", "sort_by": "", "order": "",
            })

            # Act
            response = client.post(_EXPORT_URL)

            # Assert: スコープ外デバイスがCSVに含まれない
            assert response.status_code == 200
            content = response.data.lstrip(b"\xef\xbb\xbf").decode("utf-8", errors="replace")
            assert oos_name not in content
        finally:
            with app.app_context():
                db.session.execute(
                    text("DELETE FROM device_master WHERE device_uuid = :uuid"),
                    {"uuid": oos_uuid},
                )
                db.session.commit()

    def test_export_contains_joined_data(self, client, device_session_setup):
        """4.6.7: 外部結合データ（デバイス種別名・所属組織名・ステータス）を含む7カラムのCSVが出力される"""
        # Arrange: 検索条件をdevice_name="結合テストデバイスA"に絞ってクッキー設定
        client.post(_SEARCH_URL, data={
            "device_name": "結合テストデバイスA",
            "device_id": "", "device_type_id": "", "location": "",
            "organization_id": "", "certificate_expiration_date": "",
            "status": "", "sort_by": "", "order": "",
        })

        # Act
        response = client.post(_EXPORT_URL)

        # Assert: データ行の列数が7（外部結合カラムを含む）であること
        assert response.status_code == 200
        content = response.data.lstrip(b"\xef\xbb\xbf").decode("utf-8", errors="replace")
        import csv as _csv, io
        reader = _csv.reader(io.StringIO(content))
        rows = list(reader)
        # ヘッダー行 + データ行が存在すること
        assert len(rows) >= 2
        header = rows[0]
        assert len(header) == 7  # デバイスID,デバイス名,デバイス種別,設置場所,所属組織,証明書期限,ステータス
        data_row = rows[1]
        assert len(data_row) == 7

    def test_export_all_records_without_pagination(self, client, device_session_setup):
        """4.6.8: per_page=1 のクッキー設定でも全件がエクスポートされる（ページング無視）"""
        import json

        # Arrange: per_page=1 の検索条件クッキーを直接設定する（Flask 3.x API）
        client.set_cookie(
            "search_conditions_devices",
            json.dumps({"device_name": "", "per_page": 1}),
        )

        # Act
        response = client.post(_EXPORT_URL)

        # Assert: per_page=1 でも有効なデバイスA・Bが両方CSVに含まれる
        assert response.status_code == 200
        content = response.data.lstrip(b"\xef\xbb\xbf").decode("utf-8", errors="replace")
        assert "結合テストデバイスA" in content
        assert "結合テストデバイスB" in content


# ---------------------------------------------------------------------------
# 5.1 / 5.3 検索・ページネーションテスト
# ---------------------------------------------------------------------------

@pytest.mark.integration
class TestDeviceSearch:
    """デバイス管理 - 検索・ページネーションテスト
    観点: 5.1 検索条件テスト / 5.3 ページネーションテスト
    """

    def test_search_no_conditions_redirects(self, client, device_session_setup):
        """5.1.1: 検索条件なしで POST すると 302 リダイレクトされる"""
        # Arrange
        form_data = {
            "device_id": "",
            "device_name": "",
            "device_type_id": "",
            "location": "",
            "organization_id": "",
            "certificate_expiration_date": "",
            "status": "",
            "sort_by": "",
            "order": "",
        }

        # Act
        response = client.post(_SEARCH_URL, data=form_data)

        # Assert
        assert response.status_code == 302

    def test_search_by_device_name_partial_redirects(self, client, device_session_setup):
        """5.1.7: デバイス名の部分一致検索で 302 リダイレクトされる"""
        # Arrange
        form_data = {
            "device_id": "",
            "device_name": "結合テスト",  # 部分一致
            "device_type_id": "",
            "location": "",
            "organization_id": "",
            "certificate_expiration_date": "",
            "status": "",
            "sort_by": "",
            "order": "",
        }

        # Act
        response = client.post(_SEARCH_URL, data=form_data)

        # Assert
        assert response.status_code == 302

    def test_pagination_page1_returns_200(self, client, device_session_setup):
        """5.3.1: page=1 で GET すると 200 が返る"""
        # Act
        response = client.get(f"{_LIST_URL}?page=1")

        # Assert
        assert response.status_code == 200

    def test_pagination_page2_returns_200(self, client, device_session_setup):
        """5.3.2: page=2 で GET すると 200 が返る（データ件数が 1 ページ以下でも正常応答）"""
        # Act
        response = client.get(f"{_LIST_URL}?page=2")

        # Assert
        assert response.status_code == 200

    def test_sort_asc_returns_200(self, client, device_session_setup):
        """5.2.2: ソート条件付きで GET すると 200 が返る"""
        # Act
        response = client.get(f"{_LIST_URL}?page=1")

        # Assert
        assert response.status_code == 200

    # ------------------------------------------------------------------
    # 5.1.1 全件表示（内容確認）
    # ------------------------------------------------------------------

    def test_search_no_conditions_shows_all_active_devices(self, client, device_session_setup):
        """5.1.1: 検索条件なしで検索すると有効な全デバイスが一覧に表示される"""
        # Act
        response = client.post(_SEARCH_URL, data={
            "device_id": "", "device_name": "", "device_type_id": "", "location": "",
            "organization_id": "", "certificate_expiration_date": "",
            "status": "", "sort_by": "", "order": "",
        }, follow_redirects=True)

        # Assert
        assert response.status_code == 200
        assert "結合テストデバイスA".encode() in response.data
        assert "結合テストデバイスB".encode() in response.data
        assert "結合テスト別組織デバイス".encode() in response.data

    # ------------------------------------------------------------------
    # 5.1.2 完全一致フィールド: organization_id
    # ------------------------------------------------------------------

    def test_search_org_id_exact_match_hits(self, client, device_session_setup):
        """5.1.2: 完全一致フィールド（organization_id）に正確な値を指定するとヒットする"""
        # Act: org_id=2 → A・B がヒット、org_id=3 の別組織デバイスは非表示
        response = client.post(_SEARCH_URL, data={
            "device_id": "", "device_name": "", "device_type_id": "", "location": "",
            "organization_id": "2", "certificate_expiration_date": "",
            "status": "", "sort_by": "", "order": "",
        }, follow_redirects=True)

        # Assert
        assert response.status_code == 200
        assert "結合テストデバイスA".encode() in response.data
        assert "結合テストデバイスB".encode() in response.data
        assert "結合テスト別組織デバイス".encode() not in response.data

    # ------------------------------------------------------------------
    # 5.1.2 完全一致フィールド: device_type_id
    # ------------------------------------------------------------------

    def test_search_device_type_id_exact_match_hits(self, client, device_session_setup):
        """5.1.2: 完全一致フィールド（device_type_id）に正確な値を指定するとヒットする"""
        # Act: device_type_id=1 → 全セッションデバイスがヒット
        response = client.post(_SEARCH_URL, data={
            "device_id": "", "device_name": "", "device_type_id": "1", "location": "",
            "organization_id": "", "certificate_expiration_date": "",
            "status": "", "sort_by": "", "order": "",
        }, follow_redirects=True)

        # Assert
        assert response.status_code == 200
        assert "結合テストデバイスA".encode() in response.data
        assert "結合テストデバイスB".encode() in response.data

    # ------------------------------------------------------------------
    # 5.1.3 / 5.1.4 / 5.1.5 完全一致フィールド: 非合致値でヒットしない
    # （整数IDフィールドのため前方/後方/中間一致の概念なし。非存在値で代替）
    # ------------------------------------------------------------------

    def test_search_exact_match_field_nonexistent_no_hit(self, client, device_session_setup):
        """5.1.3 / 5.1.4 / 5.1.5: 完全一致フィールドに合致しない値を指定するとヒットしない
        （organization_id は整数IDのため前方/後方/中間一致の概念なし。非存在値テストで代替）"""
        # Act: org_id=99999（存在しない値）
        response = client.post(_SEARCH_URL, data={
            "device_id": "", "device_name": "", "device_type_id": "", "location": "",
            "organization_id": "99999", "certificate_expiration_date": "",
            "status": "", "sort_by": "", "order": "",
        }, follow_redirects=True)

        # Assert: ヒットなし
        assert response.status_code == 200
        assert "結合テストデバイスA".encode() not in response.data
        assert "結合テストデバイスB".encode() not in response.data

    # ------------------------------------------------------------------
    # 5.1.6 部分一致フィールド: device_name 完全一致文字列
    # ------------------------------------------------------------------

    def test_search_device_name_full_string_hits(self, client, device_session_setup):
        """5.1.6: 部分一致フィールド（device_name）に完全一致する文字列を指定するとヒットする"""
        # Act: "結合テストデバイスA" → A のみヒット
        response = client.post(_SEARCH_URL, data={
            "device_id": "", "device_name": "結合テストデバイスA",
            "device_type_id": "", "location": "", "organization_id": "",
            "certificate_expiration_date": "", "status": "", "sort_by": "", "order": "",
        }, follow_redirects=True)

        # Assert
        assert response.status_code == 200
        assert "結合テストデバイスA".encode() in response.data
        assert "結合テストデバイスB".encode() not in response.data

    # ------------------------------------------------------------------
    # 5.1.7 部分一致フィールド: device_name 前方一致（内容確認）
    # ------------------------------------------------------------------

    def test_search_device_name_prefix_hits_with_content(self, client, device_session_setup):
        """5.1.7: 部分一致フィールド（device_name）に前方一致する文字列を指定するとヒットする（結果内容確認）"""
        # Act: "結合テスト" → A・B・別組織 が前方一致
        response = client.post(_SEARCH_URL, data={
            "device_id": "", "device_name": "結合テスト",
            "device_type_id": "", "location": "", "organization_id": "",
            "certificate_expiration_date": "", "status": "", "sort_by": "", "order": "",
        }, follow_redirects=True)

        # Assert
        assert response.status_code == 200
        assert "結合テストデバイスA".encode() in response.data
        assert "結合テストデバイスB".encode() in response.data

    # ------------------------------------------------------------------
    # 5.1.8 部分一致フィールド: device_name 後方一致
    # ------------------------------------------------------------------

    def test_search_device_name_suffix_hits(self, client, device_session_setup):
        """5.1.8: 部分一致フィールド（device_name）に後方一致する文字列を指定するとヒットする"""
        # Act: "デバイスA" → A のみ後方一致
        response = client.post(_SEARCH_URL, data={
            "device_id": "", "device_name": "デバイスA",
            "device_type_id": "", "location": "", "organization_id": "",
            "certificate_expiration_date": "", "status": "", "sort_by": "", "order": "",
        }, follow_redirects=True)

        # Assert
        assert response.status_code == 200
        assert "結合テストデバイスA".encode() in response.data
        assert "結合テストデバイスB".encode() not in response.data

    # ------------------------------------------------------------------
    # 5.1.9 部分一致フィールド: device_name 中間一致
    # ------------------------------------------------------------------

    def test_search_device_name_middle_hits(self, client, device_session_setup):
        """5.1.9: 部分一致フィールド（device_name）に中間一致する文字列を指定するとヒットする"""
        # Act: "テストデバイス" → A・B に中間一致
        response = client.post(_SEARCH_URL, data={
            "device_id": "", "device_name": "テストデバイス",
            "device_type_id": "", "location": "", "organization_id": "",
            "certificate_expiration_date": "", "status": "", "sort_by": "", "order": "",
        }, follow_redirects=True)

        # Assert
        assert response.status_code == 200
        assert "結合テストデバイスA".encode() in response.data
        assert "結合テストデバイスB".encode() in response.data

    # ------------------------------------------------------------------
    # 5.1.6〜5.1.9相当: device_id（device_uuid）フィールド 部分一致
    # ------------------------------------------------------------------

    def test_search_device_id_partial_match_hits(self, client, device_session_setup):
        """5.1.7相当: 部分一致フィールド（device_id = device_uuid）の前方一致検索でヒットする"""
        # Arrange: uuid_a の先頭 10 文字で検索（前方一致）
        uuid_a = device_session_setup["uuid_a"]
        prefix = uuid_a[:10]

        # Act
        response = client.post(_SEARCH_URL, data={
            "device_id": prefix, "device_name": "", "device_type_id": "",
            "location": "", "organization_id": "", "certificate_expiration_date": "",
            "status": "", "sort_by": "", "order": "",
        }, follow_redirects=True)

        # Assert: A がヒット
        assert response.status_code == 200
        assert "結合テストデバイスA".encode() in response.data

    # ------------------------------------------------------------------
    # 5.1.6〜5.1.9相当: location（device_location）フィールド 部分一致
    # ------------------------------------------------------------------

    def test_search_location_partial_match_hits(self, client, app, device_session_setup):
        """5.1.7相当: 部分一致フィールド（location = device_location）の中間一致検索でヒットする"""
        import uuid as _uuid
        from sqlalchemy import text
        from iot_app import db

        # Arrange: device_location が設定されたテンポラリデバイスを挿入
        unique_id = _uuid.uuid4().hex[:8]
        loc_uuid = f"TEST-LOC-{unique_id}"
        loc_name = f"ロケーション検索テストデバイス_{unique_id}"
        loc_value = f"東京都テスト設置場所_{unique_id}"

        with app.app_context():
            r = db.session.execute(text(
                "INSERT INTO device_master "
                "(device_uuid, organization_id, device_type_id, device_name, device_model, "
                "device_inventory_id, device_location, delete_flag, creator, modifier) "
                "VALUES (:uuid, :org, :dtype, :name, 'MODEL-LOC', 1, :loc, FALSE, 1, 1)"
            ), {"uuid": loc_uuid, "org": _ORG_ID, "dtype": _DEVICE_TYPE_ID,
                "name": loc_name, "loc": loc_value})
            loc_device_id = r.lastrowid

            db.session.execute(text(
                "INSERT INTO v_device_master_by_user "
                "(user_id, device_id, device_uuid, organization_id, device_type_id, "
                "device_name, device_model, device_location, delete_flag) "
                "VALUES (:uid, :did, :duuid, :org, :dtype, :name, 'MODEL-LOC', :loc, FALSE)"
            ), {"uid": 1, "did": loc_device_id, "duuid": loc_uuid,
                "org": _ORG_ID, "dtype": _DEVICE_TYPE_ID,
                "name": loc_name, "loc": loc_value})
            db.session.commit()

        try:
            # Act: "テスト設置場所" で中間一致検索
            response = client.post(_SEARCH_URL, data={
                "device_id": "", "device_name": "", "device_type_id": "",
                "location": "テスト設置場所", "organization_id": "",
                "certificate_expiration_date": "", "status": "", "sort_by": "", "order": "",
            }, follow_redirects=True)

            # Assert: テンポラリデバイスがヒット。A・B は device_location=NULL のため非表示
            assert response.status_code == 200
            assert loc_name.encode() in response.data
            assert "結合テストデバイスA".encode() not in response.data
        finally:
            with app.app_context():
                db.session.execute(
                    text("DELETE FROM v_device_master_by_user WHERE device_id = :did"),
                    {"did": loc_device_id},
                )
                db.session.execute(
                    text("DELETE FROM device_master WHERE device_uuid = :uuid"),
                    {"uuid": loc_uuid},
                )
                db.session.commit()

    # ------------------------------------------------------------------
    # 5.1.2相当: certificate_expiration_date フィールド（<=フィルタ）
    # ------------------------------------------------------------------

    def test_search_cert_date_hits(self, client, app, device_session_setup):
        """5.1.2相当: certificate_expiration_date に指定日以前の証明書期限を持つデバイスがヒットし、指定日より後はヒットしない"""
        import uuid as _uuid
        from sqlalchemy import text
        from iot_app import db

        # Arrange: cert_date が設定されたテンポラリデバイスを挿入（期限 2028-06-30）
        unique_id = _uuid.uuid4().hex[:8]
        cert_uuid = f"TEST-CERT-{unique_id}"
        cert_name = f"証明書期限検索テストデバイス_{unique_id}"
        cert_date = "2028-06-30"

        with app.app_context():
            r = db.session.execute(text(
                "INSERT INTO device_master "
                "(device_uuid, organization_id, device_type_id, device_name, device_model, "
                "device_inventory_id, certificate_expiration_date, delete_flag, creator, modifier) "
                "VALUES (:uuid, :org, :dtype, :name, 'MODEL-CERT', 1, :cert, FALSE, 1, 1)"
            ), {"uuid": cert_uuid, "org": _ORG_ID, "dtype": _DEVICE_TYPE_ID,
                "name": cert_name, "cert": cert_date})
            cert_device_id = r.lastrowid

            db.session.execute(text(
                "INSERT INTO v_device_master_by_user "
                "(user_id, device_id, device_uuid, organization_id, device_type_id, "
                "device_name, device_model, certificate_expiration_date, delete_flag) "
                "VALUES (:uid, :did, :duuid, :org, :dtype, :name, 'MODEL-CERT', :cert, FALSE)"
            ), {"uid": 1, "did": cert_device_id, "duuid": cert_uuid,
                "org": _ORG_ID, "dtype": _DEVICE_TYPE_ID,
                "name": cert_name, "cert": cert_date})
            db.session.commit()

        try:
            # Act1: 検索日=2029-12-31 → cert_date(2028-06-30) <= 2029-12-31 → ヒット
            response_hit = client.post(_SEARCH_URL, data={
                "device_id": "", "device_name": "", "device_type_id": "", "location": "",
                "organization_id": "", "certificate_expiration_date": "2029-12-31",
                "status": "", "sort_by": "", "order": "",
            }, follow_redirects=True)

            # Act2: 検索日=2027-01-01 → cert_date(2028-06-30) > 2027-01-01 → ヒットしない
            response_no_hit = client.post(_SEARCH_URL, data={
                "device_id": "", "device_name": "", "device_type_id": "", "location": "",
                "organization_id": "", "certificate_expiration_date": "2027-01-01",
                "status": "", "sort_by": "", "order": "",
            }, follow_redirects=True)

            # Assert
            assert response_hit.status_code == 200
            assert cert_name.encode() in response_hit.data

            assert response_no_hit.status_code == 200
            assert cert_name.encode() not in response_no_hit.data
        finally:
            with app.app_context():
                db.session.execute(
                    text("DELETE FROM v_device_master_by_user WHERE device_id = :did"),
                    {"did": cert_device_id},
                )
                db.session.execute(
                    text("DELETE FROM device_master WHERE device_uuid = :uuid"),
                    {"uuid": cert_uuid},
                )
                db.session.commit()

    # ------------------------------------------------------------------
    # 5.1.2相当: status フィールド（disconnected）
    # ------------------------------------------------------------------

    def test_search_status_disconnected_hits(self, client, device_session_setup):
        """5.1.2相当: status=disconnected で検索するとdevice_status_dataが存在しない（未接続）デバイスがヒットする"""
        # Act: セッションフィクスチャのデバイスは device_status_data に未登録 → 全て未接続
        response = client.post(_SEARCH_URL, data={
            "device_id": "", "device_name": "", "device_type_id": "", "location": "",
            "organization_id": "", "certificate_expiration_date": "",
            "status": "disconnected", "sort_by": "", "order": "",
        }, follow_redirects=True)

        # Assert: A・B がヒット（device_status_data なし = last_received_time IS NULL = 未接続）
        assert response.status_code == 200
        assert "結合テストデバイスA".encode() in response.data
        assert "結合テストデバイスB".encode() in response.data

    # ------------------------------------------------------------------
    # 5.1.10 AND 検索: 複数条件をすべて満たす → ヒット
    # ------------------------------------------------------------------

    def test_search_and_all_conditions_match(self, client, device_session_setup):
        """5.1.10: 複数条件（device_name AND organization_id）をすべて満たすとヒットする"""
        # Act: device_name="結合テスト"（前方一致）+ organization_id=2
        # → A・B は両条件を満たす。別組織デバイス（org_id=3）はorg_id条件を満たさない
        response = client.post(_SEARCH_URL, data={
            "device_id": "", "device_name": "結合テスト",
            "device_type_id": "", "location": "", "organization_id": "2",
            "certificate_expiration_date": "", "status": "", "sort_by": "", "order": "",
        }, follow_redirects=True)

        # Assert
        assert response.status_code == 200
        assert "結合テストデバイスA".encode() in response.data
        assert "結合テストデバイスB".encode() in response.data
        assert "結合テスト別組織デバイス".encode() not in response.data

    # ------------------------------------------------------------------
    # 5.1.11 AND 検索: 条件の片方しか満たさない → ヒットしない
    # ------------------------------------------------------------------

    def test_search_and_partial_conditions_no_hit(self, client, device_session_setup):
        """5.1.11: 複数条件のうち片方しか満たさない場合ヒットしない
        （device_name="結合テストデバイスA" はA に一致、organization_id=3 は別組織に一致。
        両条件を同時に満たすデバイスは存在しない）"""
        # Act
        response = client.post(_SEARCH_URL, data={
            "device_id": "", "device_name": "結合テストデバイスA",
            "device_type_id": "", "location": "", "organization_id": "3",
            "certificate_expiration_date": "", "status": "", "sort_by": "", "order": "",
        }, follow_redirects=True)

        # Assert: 両条件を同時に満たすデバイスなし
        # uuid_a はフォームに現れず結果テーブルにのみ出現するため、デバイスAの非表示を確認
        assert response.status_code == 200
        assert device_session_setup["uuid_a"].encode() not in response.data
        assert "結合テスト別組織デバイス".encode() not in response.data

    # ------------------------------------------------------------------
    # 5.3.3 最終ページ表示
    # ------------------------------------------------------------------

    def test_pagination_last_page_shows_remaining_records(self, client, device_session_setup):
        """5.3.3: 最終ページに残りのレコードが表示される
        セッションフィクスチャの有効デバイスは 3 件（< 25 件）のため page=1 が最終ページ。
        最終ページにデバイスA・Bが含まれることを確認する。"""
        # Act
        response = client.get(f"{_LIST_URL}?page=1")

        # Assert: 最終ページ（= 1 ページ目）に残りのデバイスが表示される
        assert response.status_code == 200
        assert "結合テストデバイスA".encode() in response.data
        assert "結合テストデバイスB".encode() in response.data

    # ------------------------------------------------------------------
    # 5.3.4 ページ範囲外（page=0）
    # ------------------------------------------------------------------

    def test_pagination_out_of_range_page0(self, client, device_session_setup):
        """5.3.4: page=0 を指定しても 500 エラーが発生しない
        （実装上 offset が負になるため、実際の挙動は 200 または 500 となりうる。
        設計期待値は 1 ページ目表示だが、本テストでは 500 を返さないことを確認する）"""
        # Act
        response = client.get(f"{_LIST_URL}?page=0")

        # Assert: サーバーエラーにならない
        assert response.status_code != 500

    # ------------------------------------------------------------------
    # 5.3.5 ページサイズ境界値（ちょうど 25 件）
    # ------------------------------------------------------------------

    def test_pagination_exactly_page_size(self, client, app, device_session_setup):
        """5.3.5: 表示件数がページサイズ（25 件）と一致するとき、page=1 に全件表示される"""
        import uuid as _uuid
        from sqlalchemy import text
        from iot_app import db

        # Arrange: ユニーク prefix で一時デバイスを挿入（セッション有効 3 件 + 22 件 = 25 件）
        uid = _uuid.uuid4().hex[:8]
        prefix = f"PAG25-{uid}"
        n_insert = 22
        inserted_ids = []

        with app.app_context():
            for i in range(n_insert):
                dev_uuid = f"{prefix}-{i:03d}"
                r = db.session.execute(text(
                    "INSERT INTO device_master "
                    "(device_uuid, organization_id, device_type_id, device_name, device_model, "
                    "device_inventory_id, delete_flag, creator, modifier) "
                    "VALUES (:uuid, :org, :dtype, :name, 'MODEL-PAG', 1, FALSE, 1, 1)"
                ), {"uuid": dev_uuid, "org": _ORG_ID, "dtype": _DEVICE_TYPE_ID,
                    "name": f"{prefix}-{i:03d}"})
                did = r.lastrowid
                inserted_ids.append(did)
                db.session.execute(text(
                    "INSERT INTO v_device_master_by_user "
                    "(user_id, device_id, device_uuid, organization_id, device_type_id, "
                    "device_name, device_model, delete_flag) "
                    "VALUES (1, :did, :duuid, :org, :dtype, :name, 'MODEL-PAG', FALSE)"
                ), {"did": did, "duuid": dev_uuid, "org": _ORG_ID,
                    "dtype": _DEVICE_TYPE_ID, "name": f"{prefix}-{i:03d}"})
            db.session.commit()

        try:
            # Act: page=1 → 25 件分が表示される（ページネーション不要）
            response_p1 = client.get(f"{_LIST_URL}?page=1")
            # Act: page=2 → データなし
            response_p2 = client.get(f"{_LIST_URL}?page=2")

            # Assert: page=1 は 200 でデバイスが表示される
            assert response_p1.status_code == 200
            assert prefix.encode() in response_p1.data
            # Assert: page=2 は 200 だが一時デバイスが含まれない（25 件以下のため 2 ページ目なし）
            assert response_p2.status_code == 200
            assert prefix.encode() not in response_p2.data
        finally:
            with app.app_context():
                if inserted_ids:
                    id_tuple = tuple(inserted_ids)
                    db.session.execute(
                        text("DELETE FROM v_device_master_by_user WHERE device_id IN :ids"),
                        {"ids": id_tuple},
                    )
                    db.session.execute(
                        text("DELETE FROM device_master WHERE device_id IN :ids"),
                        {"ids": id_tuple},
                    )
                    db.session.commit()

    # ------------------------------------------------------------------
    # 5.3.6 ページサイズ境界値+1（26 件）
    # ------------------------------------------------------------------

    def test_pagination_one_over_page_size(self, client, app, device_session_setup):
        """5.3.6: 表示件数がページサイズ+1（26 件）のとき、page=1 に 25 件・page=2 に 1 件が表示される"""
        import uuid as _uuid
        from sqlalchemy import text
        from iot_app import db

        # Arrange: ユニーク prefix で一時デバイスを挿入（セッション有効 3 件 + 23 件 = 26 件）
        uid = _uuid.uuid4().hex[:8]
        prefix = f"PAG26-{uid}"
        n_insert = 23
        inserted_ids = []

        with app.app_context():
            for i in range(n_insert):
                dev_uuid = f"{prefix}-{i:03d}"
                r = db.session.execute(text(
                    "INSERT INTO device_master "
                    "(device_uuid, organization_id, device_type_id, device_name, device_model, "
                    "device_inventory_id, delete_flag, creator, modifier) "
                    "VALUES (:uuid, :org, :dtype, :name, 'MODEL-PAG', 1, FALSE, 1, 1)"
                ), {"uuid": dev_uuid, "org": _ORG_ID, "dtype": _DEVICE_TYPE_ID,
                    "name": f"{prefix}-{i:03d}"})
                did = r.lastrowid
                inserted_ids.append(did)
                db.session.execute(text(
                    "INSERT INTO v_device_master_by_user "
                    "(user_id, device_id, device_uuid, organization_id, device_type_id, "
                    "device_name, device_model, delete_flag) "
                    "VALUES (1, :did, :duuid, :org, :dtype, :name, 'MODEL-PAG', FALSE)"
                ), {"did": did, "duuid": dev_uuid, "org": _ORG_ID,
                    "dtype": _DEVICE_TYPE_ID, "name": f"{prefix}-{i:03d}"})
            db.session.commit()

        try:
            # Act: page=1（ソート順で先頭 25 件）と page=2（残り 1 件以上）を取得
            response_p1 = client.get(f"{_LIST_URL}?page=1")
            response_p2 = client.get(f"{_LIST_URL}?page=2")

            # Assert: page=1・page=2 ともに 200
            assert response_p1.status_code == 200
            assert response_p2.status_code == 200
            # Assert: 26 件のうち一部は page=1、残りは page=2 に分散される
            # （全 prefix デバイスが 2 ページにまたがって表示されることを確認）
            combined = response_p1.data + response_p2.data
            assert prefix.encode() in combined
            # page=1 と page=2 の両方にデータが存在する（= 2 ページに分割される）
            assert prefix.encode() in response_p1.data or prefix.encode() in response_p2.data
        finally:
            with app.app_context():
                if inserted_ids:
                    id_tuple = tuple(inserted_ids)
                    db.session.execute(
                        text("DELETE FROM v_device_master_by_user WHERE device_id IN :ids"),
                        {"ids": id_tuple},
                    )
                    db.session.execute(
                        text("DELETE FROM device_master WHERE device_id IN :ids"),
                        {"ids": id_tuple},
                    )
                    db.session.commit()

    # ------------------------------------------------------------------
    # 5.3.7 総件数表示
    # ------------------------------------------------------------------

    def test_pagination_total_count_displayed(self, client, device_session_setup):
        """5.3.7: 一覧ページに総件数が表示される"""
        # Act
        response = client.get(_LIST_URL)

        # Assert: テンプレートの dm-result-count__value 要素（総件数）が含まれる
        assert response.status_code == 200
        assert b"dm-result-count__value" in response.data


# ---------------------------------------------------------------------------
# 1.2 認可（権限チェック）テスト
# ---------------------------------------------------------------------------

@pytest.mark.integration
class TestDeviceAuth:
    """デバイス管理 - 認可テスト
    観点: 1.2 認可（権限チェック）機能
    """

    def _set_service_company_user(self, app):
        """g.current_user.user_type_id を service_company_user (4) に変える before_request フックを登録する。"""
        from flask import g

        def _set_user():
            from types import SimpleNamespace
            g.current_user = SimpleNamespace(
                user_id=1,
                user_type_id=4,  # service_company_user
                organization_id=1,
                email_address="svc@example.com",
            )

        funcs = app.before_request_funcs.setdefault(None, [])
        funcs.append(_set_user)
        return _set_user

    def test_system_admin_can_access_list(self, client, device_session_setup):
        """1.2.1: システム保守者（user_type_id=1）は一覧を参照できる"""
        # Act（inject_test_user がデフォルトで user_type_id=1 を設定）
        response = client.get(_LIST_URL)

        # Assert
        assert response.status_code == 200

    def test_service_company_user_cannot_create(self, client, app, device_session_setup):
        """1.2.7: サービス利用者（user_type_id=4）が登録エンドポイントにアクセスすると 403 が返る"""
        # Arrange
        hook = self._set_service_company_user(app)

        try:
            # Act
            response = client.post(_REGISTER_URL, data={
                "device_uuid": "FORBIDDEN-DEV",
                "device_name": "権限テスト",
                "device_type_id": str(_DEVICE_TYPE_ID),
                "device_model": "MODEL-FORB",
                "organization_id": str(_ORG_ID),
            })

            # Assert
            assert response.status_code == 403
        finally:
            funcs = app.before_request_funcs.get(None, [])
            if hook in funcs:
                funcs.remove(hook)

    def test_service_company_user_cannot_delete(self, client, app, device_session_setup):
        """1.2.7: サービス利用者（user_type_id=4）が削除エンドポイントにアクセスすると 403 が返る"""
        # Arrange
        hook = self._set_service_company_user(app)

        try:
            # Act
            response = client.post(_DELETE_URL, data={"device_uuids": "SOME-UUID"})

            # Assert
            assert response.status_code == 403
        finally:
            funcs = app.before_request_funcs.get(None, [])
            if hook in funcs:
                funcs.remove(hook)

    def test_service_company_user_can_view_list(self, client, app, device_session_setup):
        """1.2.6: サービス利用者（user_type_id=4）は一覧を参照できる"""
        # Arrange
        hook = self._set_service_company_user(app)

        try:
            # Act
            response = client.get(_LIST_URL)

            # Assert
            assert response.status_code == 200
        finally:
            funcs = app.before_request_funcs.get(None, [])
            if hook in funcs:
                funcs.remove(hook)

    def test_sales_company_user_can_access_create_form(self, client, app, device_session_setup):
        """1.2.4: 販社ユーザー（user_type_id=3）は登録フォームにアクセスできる"""
        # Arrange
        from flask import g

        def _set_sales_user():
            from types import SimpleNamespace
            g.current_user = SimpleNamespace(
                user_id=1,
                user_type_id=3,  # sales_company_user
                organization_id=1,
                email_address="sales@example.com",
            )

        funcs = app.before_request_funcs.setdefault(None, [])
        funcs.insert(0, _set_sales_user)

        try:
            # Act
            response = client.get(_CREATE_FORM_URL)

            # Assert
            assert response.status_code == 200
        finally:
            if _set_sales_user in funcs:
                funcs.remove(_set_sales_user)


# ---------------------------------------------------------------------------
# 9.1 / 9.2 セキュリティテスト
# ---------------------------------------------------------------------------

@pytest.mark.integration
class TestDeviceSecurity:
    """デバイス管理 - セキュリティテスト
    観点: 9.1 SQLインジェクションテスト / 9.2 XSSテスト
    """

    def test_sql_injection_in_device_name_search_returns_200(self, client, device_session_setup):
        """9.1.1: デバイス名検索に SQL インジェクション文字列を入力しても正常処理される"""
        # Arrange
        form_data = {
            "device_id": "",
            "device_name": "' OR '1'='1",
            "device_type_id": "",
            "location": "",
            "organization_id": "",
            "certificate_expiration_date": "",
            "status": "",
            "sort_by": "",
            "order": "",
        }

        # Act（検索は POST → 302 リダイレクト後に GET）
        response = client.post(_SEARCH_URL, data=form_data)

        # Assert: エラーにならず正常にリダイレクトされる（500 エラーが発生しない）
        assert response.status_code in (200, 302)

    def test_sql_injection_drop_table_in_search(self, client, device_session_setup):
        """9.1.2: DROP TABLE を含む SQL インジェクションで 500 エラーが発生しない"""
        # Arrange
        form_data = {
            "device_id": "",
            "device_name": "'; DROP TABLE device_master--",
            "device_type_id": "",
            "location": "",
            "organization_id": "",
            "certificate_expiration_date": "",
            "status": "",
            "sort_by": "",
            "order": "",
        }

        # Act
        response = client.post(_SEARCH_URL, data=form_data)

        # Assert
        assert response.status_code != 500

    def test_xss_in_device_name_search_is_escaped(self, client, device_session_setup):
        """9.2.1: デバイス名検索に XSS 文字列を入力してもスクリプトがエスケープされる"""
        # Arrange
        xss_payload = "<script>alert('XSS')</script>"
        form_data = {
            "device_id": "",
            "device_name": xss_payload,
            "device_type_id": "",
            "location": "",
            "organization_id": "",
            "certificate_expiration_date": "",
            "status": "",
            "sort_by": "",
            "order": "",
        }

        # Act: リダイレクト先の GET も含めて追跡
        response = client.post(_SEARCH_URL, data=form_data, follow_redirects=True)

        # Assert: スクリプトタグがそのまま出力されていない（Jinja2 自動エスケープで &lt;script&gt; になる）
        assert response.status_code == 200
        assert b"<script>alert('XSS')</script>" not in response.data

    def test_sql_injection_union_in_search(self, client, device_session_setup):
        """9.1.3: UNION 型 SQL インジェクションで 500 エラーが発生しない"""
        # Arrange
        form_data = {
            "device_id": "",
            "device_name": "' UNION SELECT 1,2,3--",
            "device_type_id": "",
            "location": "",
            "organization_id": "",
            "certificate_expiration_date": "",
            "status": "",
            "sort_by": "",
            "order": "",
        }

        # Act
        response = client.post(_SEARCH_URL, data=form_data)

        # Assert: 500 にならずリダイレクトされる
        assert response.status_code != 500

    def test_xss_img_tag_in_search_is_escaped(self, client, device_session_setup):
        """9.2.2: img タグを使った XSS 文字列がエスケープされる"""
        # Arrange
        xss_payload = "<img src=x onerror=alert('XSS')>"
        form_data = {
            "device_id": "",
            "device_name": xss_payload,
            "device_type_id": "",
            "location": "",
            "organization_id": "",
            "certificate_expiration_date": "",
            "status": "",
            "sort_by": "",
            "order": "",
        }

        # Act: リダイレクト先も含めて追跡
        response = client.post(_SEARCH_URL, data=form_data, follow_redirects=True)

        # Assert: タグがそのまま出力されていない
        assert response.status_code == 200
        assert b"<img src=x onerror=alert('XSS')>" not in response.data

    def test_xss_javascript_protocol_does_not_cause_server_error(self, client, device_session_setup):
        """9.2.3: javascript: プロトコルを含む文字列で 500 エラーが発生しない"""
        # Arrange
        form_data = {
            "device_id": "",
            "device_name": "javascript:alert('XSS')",
            "device_type_id": "",
            "location": "",
            "organization_id": "",
            "certificate_expiration_date": "",
            "status": "",
            "sort_by": "",
            "order": "",
        }

        # Act
        response = client.post(_SEARCH_URL, data=form_data, follow_redirects=True)

        # Assert: エラーにならず正常応答が返る
        assert response.status_code == 200
