"""
デバイス管理 結合テスト専用フィクスチャ

テスト環境では v_device_master_by_user / v_organization_master_by_user は
MySQL VIEW ではなく create_all() によって生成された実テーブルとして扱われる。
そのため、テスト用デバイスデータをフィクスチャで直接 INSERT する。

teardown:
  - session スコープ: FK 逆順で明示的 DELETE + COMMIT
  - function スコープ: 同上（MySQL READ COMMITTED のためロールバック方式は使用しない）
"""

import uuid

import pytest
from sqlalchemy import text

# テスト環境で使用する固定 ID（99_test_data.sql が保有する既存データ）
TEST_USER_ID = 1         # inject_test_user が g.current_user.user_id に設定する値
TEST_ORG_ID = 2          # 所属組織（見える） - organization_master に存在
TEST_ORG_SUB_ID = 3      # 配下組織（見える） - organization_master に存在
TEST_DEVICE_TYPE_ID = 1  # テスト種別         - device_type_master に存在


# ---------------------------------------------------------------------------
# session スコープ: 一覧・詳細・検索テスト向けの固定テストデータ
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session", autouse=True)
def device_session_setup():
    """デバイス管理結合テスト用セッションスコープセットアップ。

    device_master / v_device_master_by_user / v_organization_master_by_user に
    テスト用レコードを投入する。セッション終了時に FK 逆順で削除する。

    autouse=True のため、tests/integration/devices/ 配下の全テストで自動適用される。
    """
    import os
    os.environ.setdefault("FLASK_ENV", "testing")

    from iot_app import create_app, db

    _app = create_app()
    uid = uuid.uuid4().hex[:10]

    # セッション内で一意な UUID を生成
    uuid_a = f"TEST-SES-A-{uid}"
    uuid_b = f"TEST-SES-B-{uid}"
    uuid_del = f"TEST-SES-DEL-{uid}"
    uuid_inacc = f"TEST-SES-INACC-{uid}"

    inserted_device_ids = []

    with _app.app_context():
        # ------------------------------------------------------------------
        # device_master に挿入（CRUD 操作・重複チェック用）
        # ------------------------------------------------------------------
        _insert_dm = text(
            "INSERT INTO device_master "
            "(device_uuid, organization_id, device_type_id, device_name, device_model, "
            "device_inventory_id, delete_flag, creator, modifier) "
            "VALUES (:uuid, :org, :dtype, :name, :model, 1, :del, 0, 0)"
        )

        r_a = _app.extensions["sqlalchemy"].session.execute(_insert_dm, {
            "uuid": uuid_a, "org": TEST_ORG_ID,
            "dtype": TEST_DEVICE_TYPE_ID, "name": "結合テストデバイスA",
            "model": "MODEL-TEST-A", "del": False,
        })
        r_b = _app.extensions["sqlalchemy"].session.execute(_insert_dm, {
            "uuid": uuid_b, "org": TEST_ORG_ID,
            "dtype": TEST_DEVICE_TYPE_ID, "name": "結合テストデバイスB",
            "model": "MODEL-TEST-B", "del": False,
        })
        r_del = _app.extensions["sqlalchemy"].session.execute(_insert_dm, {
            "uuid": uuid_del, "org": TEST_ORG_ID,
            "dtype": TEST_DEVICE_TYPE_ID, "name": "結合テスト削除済みデバイス",
            "model": "MODEL-TEST-DEL", "del": True,
        })
        r_inacc = _app.extensions["sqlalchemy"].session.execute(_insert_dm, {
            "uuid": uuid_inacc, "org": TEST_ORG_SUB_ID,
            "dtype": TEST_DEVICE_TYPE_ID, "name": "結合テスト別組織デバイス",
            "model": "MODEL-TEST-INACC", "del": False,
        })

        did_a = r_a.lastrowid
        did_b = r_b.lastrowid
        did_del = r_del.lastrowid
        did_inacc = r_inacc.lastrowid
        inserted_device_ids = [did_a, did_b, did_del, did_inacc]

        # ------------------------------------------------------------------
        # v_device_master_by_user に挿入（検索・詳細表示用）
        # テスト環境では VIEW ではなく実テーブルとして create_all() で生成済み
        # ------------------------------------------------------------------
        _insert_view = text(
            "INSERT INTO v_device_master_by_user "
            "(user_id, device_id, device_uuid, organization_id, device_type_id, "
            "device_name, device_model, delete_flag) "
            "VALUES (:uid, :did, :duuid, :org, :dtype, :name, :model, :del)"
        )
        for did, duuid, dname, del_flag in [
            (did_a,    uuid_a,    "結合テストデバイスA",       False),
            (did_b,    uuid_b,    "結合テストデバイスB",       False),
            (did_del,  uuid_del,  "結合テスト削除済みデバイス", True),
            (did_inacc, uuid_inacc, "結合テスト別組織デバイス", False),
        ]:
            _app.extensions["sqlalchemy"].session.execute(_insert_view, {
                "uid": TEST_USER_ID, "did": did, "duuid": duuid,
                "org": TEST_ORG_ID if did != did_inacc else TEST_ORG_SUB_ID,
                "dtype": TEST_DEVICE_TYPE_ID,
                "name": dname, "model": "MODEL-TEST", "del": del_flag,
            })

        # ------------------------------------------------------------------
        # v_organization_master_by_user に挿入（登録・更新フォーム選択肢用）
        # ------------------------------------------------------------------
        for org_id, org_name in [
            (TEST_ORG_ID,     "所属組織（見える）"),
            (TEST_ORG_SUB_ID, "配下組織（見える）"),
        ]:
            existing = _app.extensions["sqlalchemy"].session.execute(text(
                "SELECT COUNT(*) FROM v_organization_master_by_user "
                "WHERE user_id = :uid AND organization_id = :oid"
            ), {"uid": TEST_USER_ID, "oid": org_id}).scalar()
            if existing == 0:
                _app.extensions["sqlalchemy"].session.execute(text(
                    "INSERT INTO v_organization_master_by_user "
                    "(user_id, organization_id, organization_name, delete_flag) "
                    "VALUES (:uid, :oid, :name, FALSE)"
                ), {"uid": TEST_USER_ID, "oid": org_id, "name": org_name})

        _app.extensions["sqlalchemy"].session.commit()

        yield {
            "device_id_a": did_a,
            "device_id_b": did_b,
            "device_id_del": did_del,
            "device_id_inacc": did_inacc,
            "uuid_a": uuid_a,
            "uuid_b": uuid_b,
            "uuid_del": uuid_del,
            "uuid_inacc": uuid_inacc,
        }

        # ------------------------------------------------------------------
        # クリーンアップ（FK 逆順削除）
        # ------------------------------------------------------------------
        _app.extensions["sqlalchemy"].session.execute(
            text("DELETE FROM v_device_master_by_user WHERE device_id IN :ids"),
            {"ids": tuple(inserted_device_ids)},
        )
        _app.extensions["sqlalchemy"].session.execute(
            text("DELETE FROM device_master WHERE device_id IN :ids"),
            {"ids": tuple(inserted_device_ids)},
        )
        _app.extensions["sqlalchemy"].session.execute(
            text(
                "DELETE FROM v_organization_master_by_user "
                "WHERE user_id = :uid AND organization_id IN :oids"
            ),
            {"uid": TEST_USER_ID, "oids": (TEST_ORG_ID, TEST_ORG_SUB_ID)},
        )
        _app.extensions["sqlalchemy"].session.commit()


# ---------------------------------------------------------------------------
# function スコープ: 更新・削除テスト向けの可変テストデバイス
# ---------------------------------------------------------------------------

@pytest.fixture()
def mutable_test_device(app):
    """更新・削除テストに使用する function スコープのデバイスフィクスチャ。

    テストごとに一意な device_uuid を生成し、device_master と
    v_device_master_by_user の両方に INSERT して yield する。
    teardown では DELETE + COMMIT で後片付けをおこなう。
    """
    from iot_app import db

    uid = uuid.uuid4().hex[:10]
    dev_uuid = f"TEST-MUT-{uid}"

    # device_master に挿入
    r = db.session.execute(text(
        "INSERT INTO device_master "
        "(device_uuid, organization_id, device_type_id, device_name, device_model, "
        "device_inventory_id, delete_flag, creator, modifier) "
        "VALUES (:uuid, :org, :dtype, :name, :model, 1, FALSE, 1, 1)"
    ), {
        "uuid": dev_uuid, "org": TEST_ORG_ID,
        "dtype": TEST_DEVICE_TYPE_ID,
        "name": f"更新削除テスト用デバイス_{uid}",
        "model": "MODEL-MUT",
    })
    device_id = r.lastrowid

    # v_device_master_by_user に挿入（get_device_by_uuid が参照）
    db.session.execute(text(
        "INSERT INTO v_device_master_by_user "
        "(user_id, device_id, device_uuid, organization_id, device_type_id, "
        "device_name, device_model, delete_flag) "
        "VALUES (:uid, :did, :duuid, :org, :dtype, :name, :model, FALSE)"
    ), {
        "uid": TEST_USER_ID, "did": device_id, "duuid": dev_uuid,
        "org": TEST_ORG_ID, "dtype": TEST_DEVICE_TYPE_ID,
        "name": f"更新削除テスト用デバイス_{uid}", "model": "MODEL-MUT",
    })

    db.session.commit()

    yield {
        "device_id": device_id,
        "device_uuid": dev_uuid,
        "device_name": f"更新削除テスト用デバイス_{uid}",
    }

    # teardown: 明示的 DELETE + COMMIT
    db.session.execute(
        text("DELETE FROM v_device_master_by_user WHERE device_id = :did"),
        {"did": device_id},
    )
    db.session.execute(
        text("DELETE FROM device_master WHERE device_id = :did"),
        {"did": device_id},
    )
    db.session.commit()
