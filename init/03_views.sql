-- ============================================================
-- Databricks IoTシステム VIEW定義
-- データベース: databricks_iot
-- 文字コード: utf8mb4 / 照合順序: utf8mb4_general_ci
-- ============================================================
-- 目的: 組織階層（organization_closure）に基づくデータスコープ制御
--       ログインユーザーが参照可能な組織配下のデータのみを取得する
-- ============================================================

USE databricks_iot;

SET NAMES utf8mb4;

-- ============================================================
-- 1. デバイス一覧用VIEW
-- ============================================================
-- ログインユーザーの所属組織とその配下の全組織に紐づくデバイスを返す
-- 論理削除ユーザー（u.delete_flag = TRUE）はVIEW側で除外
-- 論理削除デバイス（delete_flag = TRUE）はアプリケーション側でフィルタリング
-- ============================================================

CREATE OR REPLACE VIEW v_device_master_by_user AS
SELECT
    u.user_id,
    u.user_name,
    u.organization_id AS user_organization_id,
    d.device_id,
    d.device_uuid,
    d.organization_id AS device_organization_id,
    d.device_type_id,
    d.device_name,
    d.device_model,
    d.device_inventory_id,
    d.sim_id,
    d.mac_address,
    d.software_version,
    d.device_location,
    d.certificate_expiration_date,
    d.create_date,
    d.creator,
    d.update_date,
    d.modifier,
    d.delete_flag,
    oc.depth
FROM
    user_master u
    INNER JOIN organization_closure oc
        ON u.organization_id = oc.parent_organization_id
    INNER JOIN device_master d
        ON oc.subsidiary_organization_id = d.organization_id
WHERE
    u.delete_flag = FALSE;

-- ============================================================
-- 2. ユーザー一覧用VIEW
-- ============================================================
-- ログインユーザーの所属組織とその配下の全組織に所属するユーザーを返す
-- ログインユーザー自身も結果に含まれる（depth=0の自己参照）
-- 論理削除ユーザー（delete_flag = TRUE）はアプリケーション側でフィルタリング
-- ============================================================

CREATE OR REPLACE VIEW v_user_master_by_user AS
SELECT
    u.user_id AS login_user_id,
    u.user_name AS login_user_name,
    u.organization_id AS login_user_organization_id,
    target.user_id,
    target.databricks_user_id,
    target.user_name,
    target.organization_id,
    target.email_address,
    target.user_type_id,
    target.language_code,
    target.region_id,
    target.address,
    target.status,
    target.alert_notification_flag,
    target.system_notification_flag,
    target.create_date,
    target.creator,
    target.update_date,
    target.modifier,
    target.delete_flag,
    oc.depth
FROM
    user_master u
    INNER JOIN organization_closure oc
        ON u.organization_id = oc.parent_organization_id
    INNER JOIN user_master target
        ON oc.subsidiary_organization_id = target.organization_id;

-- ============================================================
-- 3. 組織一覧用VIEW
-- ============================================================
-- ログインユーザーの所属組織とその配下の全組織を返す
-- ユーザーの所属組織自身も結果に含まれる（depth=0の自己参照）
-- 論理削除組織（delete_flag = TRUE）はアプリケーション側でフィルタリング
-- ============================================================

CREATE OR REPLACE VIEW v_organization_master_by_user AS
SELECT
    u.user_id,
    u.user_name,
    u.organization_id AS user_organization_id,
    o.organization_id,
    o.organization_name,
    o.organization_type_id,
    o.address,
    o.phone_number,
    o.fax_number,
    o.contact_person,
    o.contract_status_id,
    o.contract_start_date,
    o.contract_end_date,
    o.databricks_group_id,
    o.create_date,
    o.creator,
    o.update_date,
    o.modifier,
    o.delete_flag,
    oc.depth
FROM
    user_master u
    INNER JOIN organization_closure oc
        ON u.organization_id = oc.parent_organization_id
    INNER JOIN organization_master o
        ON oc.subsidiary_organization_id = o.organization_id;

-- ============================================================
-- 4. デバイス在庫情報一覧用VIEW
-- ============================================================
-- ログインユーザーの所属組織とその配下の全組織に紐づくデバイスの在庫情報を返す
-- device_inventory_masterは組織IDを持たないため、device_masterを経由してアクセス制御を実現
-- 論理削除デバイス在庫情報（delete_flag = TRUE）はアプリケーション側でフィルタリング
-- ============================================================

CREATE OR REPLACE VIEW v_device_stock_info_master_by_user AS
SELECT
    u.user_id,
    u.user_name,
    u.organization_id AS user_organization_id,
    dsi.device_inventory_id,
    dsi.device_inventory_uuid,
    dsi.inventory_status_id,
    dsi.device_model,
    dsi.mac_address,
    dsi.purchase_date,
    dsi.estimated_ship_date,
    dsi.ship_date,
    dsi.manufacturer_warranty_end_date,
    dsi.inventory_location,
    dsi.create_date,
    dsi.creator,
    dsi.update_date,
    dsi.modifier,
    dsi.delete_flag,
    d.device_id,
    d.organization_id AS device_organization_id,
    oc.depth
FROM
    user_master u
    INNER JOIN organization_closure oc
        ON u.organization_id = oc.parent_organization_id
    INNER JOIN device_master d
        ON oc.subsidiary_organization_id = d.organization_id
    INNER JOIN device_inventory_master dsi
        ON d.device_inventory_id = dsi.device_inventory_id;

-- ============================================================
-- 5. アラート設定一覧用VIEW
-- ============================================================
-- ログインユーザーの所属組織とその配下の全組織に紐づくデバイスのアラート設定を返す
-- alert_setting_masterは組織IDを持たないため、device_masterを経由してアクセス制御を実現
-- 論理削除デバイス（d.delete_flag = TRUE）はVIEW側で除外
-- 論理削除アラート設定（delete_flag = TRUE）はアプリケーション側でフィルタリング
-- ============================================================

CREATE OR REPLACE VIEW v_alert_setting_master_by_user AS
SELECT
    u.user_id,
    u.user_name,
    u.organization_id AS user_organization_id,
    a.alert_id,
    a.alert_uuid,
    a.alert_name,
    a.device_id,
    a.alert_conditions_measurement_item_id,
    a.alert_conditions_operator,
    a.alert_conditions_threshold,
    a.alert_recovery_conditions_measurement_item_id,
    a.alert_recovery_conditions_operator,
    a.alert_recovery_conditions_threshold,
    a.judgment_time,
    a.alert_level_id,
    a.alert_notification_flag,
    a.alert_email_flag,
    a.create_date,
    a.creator,
    a.update_date,
    a.modifier,
    a.delete_flag,
    d.organization_id AS device_organization_id,
    oc.depth
FROM
    user_master u
    INNER JOIN organization_closure oc
        ON u.organization_id = oc.parent_organization_id
    INNER JOIN device_master d
        ON oc.subsidiary_organization_id = d.organization_id
        AND d.delete_flag = FALSE
    INNER JOIN alert_setting_master a
        ON d.device_id = a.device_id;

-- ============================================================
-- 6. アラート履歴一覧用VIEW
-- ============================================================
-- ログインユーザーの所属組織とその配下の全組織に紐づくデバイスのアラート履歴を返す
-- alert_historyは組織IDを持たないため、alert_setting_master → device_masterを経由してアクセス制御を実現
-- 論理削除デバイス（d.delete_flag = TRUE）およびアラート設定（a.delete_flag = TRUE）はVIEW側で除外
-- 論理削除アラート履歴（delete_flag = TRUE）はアプリケーション側でフィルタリング
-- ============================================================

CREATE OR REPLACE VIEW v_alert_history_by_user AS
SELECT
    u.user_id,
    u.user_name,
    u.organization_id AS user_organization_id,
    ah.alert_history_id,
    ah.alert_history_uuid,
    ah.alert_id,
    ah.alert_occurrence_datetime,
    ah.alert_recovery_datetime,
    ah.alert_status_id,
    ah.alert_value,
    ah.create_date,
    ah.creator,
    ah.update_date,
    ah.modifier,
    ah.delete_flag,
    a.device_id,
    d.organization_id AS device_organization_id,
    oc.depth
FROM
    user_master u
    INNER JOIN organization_closure oc
        ON u.organization_id = oc.parent_organization_id
    INNER JOIN device_master d
        ON oc.subsidiary_organization_id = d.organization_id
    INNER JOIN alert_setting_master a
        ON d.device_id = a.device_id
    INNER JOIN alert_history ah
        ON a.alert_id = ah.alert_id
WHERE
    d.delete_flag = FALSE
    AND a.delete_flag = FALSE;
