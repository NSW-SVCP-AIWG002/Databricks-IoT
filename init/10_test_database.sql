-- ============================================================
-- テスト用データベース作成
-- databricks_iot の構造をコピーし、マスタデータのみ投入する
-- ============================================================

CREATE DATABASE IF NOT EXISTS databricks_iot_test
    CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;

GRANT ALL PRIVILEGES ON databricks_iot_test.* TO 'user'@'%';
FLUSH PRIVILEGES;

USE databricks_iot_test;

SET FOREIGN_KEY_CHECKS = 0;

-- ============================================================
-- テーブル構造コピー（FK参照先から順に）
-- ============================================================

CREATE TABLE IF NOT EXISTS databricks_iot_test.user_type_master        LIKE databricks_iot.user_type_master;
CREATE TABLE IF NOT EXISTS databricks_iot_test.language_master          LIKE databricks_iot.language_master;
CREATE TABLE IF NOT EXISTS databricks_iot_test.organization_type_master LIKE databricks_iot.organization_type_master;
CREATE TABLE IF NOT EXISTS databricks_iot_test.contract_status_master   LIKE databricks_iot.contract_status_master;
CREATE TABLE IF NOT EXISTS databricks_iot_test.region_master            LIKE databricks_iot.region_master;
CREATE TABLE IF NOT EXISTS databricks_iot_test.device_type_master       LIKE databricks_iot.device_type_master;
CREATE TABLE IF NOT EXISTS databricks_iot_test.inventory_status_master  LIKE databricks_iot.inventory_status_master;
CREATE TABLE IF NOT EXISTS databricks_iot_test.measurement_item_master  LIKE databricks_iot.measurement_item_master;
CREATE TABLE IF NOT EXISTS databricks_iot_test.alert_level_master       LIKE databricks_iot.alert_level_master;
CREATE TABLE IF NOT EXISTS databricks_iot_test.alert_status_master      LIKE databricks_iot.alert_status_master;
CREATE TABLE IF NOT EXISTS databricks_iot_test.mail_type_master         LIKE databricks_iot.mail_type_master;
CREATE TABLE IF NOT EXISTS databricks_iot_test.master_list              LIKE databricks_iot.master_list;
CREATE TABLE IF NOT EXISTS databricks_iot_test.sort_item_master         LIKE databricks_iot.sort_item_master;
CREATE TABLE IF NOT EXISTS databricks_iot_test.gadget_type_master       LIKE databricks_iot.gadget_type_master;
CREATE TABLE IF NOT EXISTS databricks_iot_test.gold_summary_method_master LIKE databricks_iot.gold_summary_method_master;
CREATE TABLE IF NOT EXISTS databricks_iot_test.organization_master      LIKE databricks_iot.organization_master;
CREATE TABLE IF NOT EXISTS databricks_iot_test.organization_closure     LIKE databricks_iot.organization_closure;
CREATE TABLE IF NOT EXISTS databricks_iot_test.user_master              LIKE databricks_iot.user_master;
CREATE TABLE IF NOT EXISTS databricks_iot_test.device_inventory_master  LIKE databricks_iot.device_inventory_master;
CREATE TABLE IF NOT EXISTS databricks_iot_test.device_master            LIKE databricks_iot.device_master;
CREATE TABLE IF NOT EXISTS databricks_iot_test.alert_setting_master     LIKE databricks_iot.alert_setting_master;
CREATE TABLE IF NOT EXISTS databricks_iot_test.device_status_data       LIKE databricks_iot.device_status_data;
CREATE TABLE IF NOT EXISTS databricks_iot_test.mail_history             LIKE databricks_iot.mail_history;
CREATE TABLE IF NOT EXISTS databricks_iot_test.alert_history            LIKE databricks_iot.alert_history;
CREATE TABLE IF NOT EXISTS databricks_iot_test.silver_sensor_data       LIKE databricks_iot.silver_sensor_data;
CREATE TABLE IF NOT EXISTS databricks_iot_test.dashboard_master         LIKE databricks_iot.dashboard_master;
CREATE TABLE IF NOT EXISTS databricks_iot_test.dashboard_group_master   LIKE databricks_iot.dashboard_group_master;
CREATE TABLE IF NOT EXISTS databricks_iot_test.dashboard_gadget_master  LIKE databricks_iot.dashboard_gadget_master;
CREATE TABLE IF NOT EXISTS databricks_iot_test.dashboard_user_setting   LIKE databricks_iot.dashboard_user_setting;
CREATE TABLE IF NOT EXISTS databricks_iot_test.email_notification_queue LIKE databricks_iot.email_notification_queue;
CREATE TABLE IF NOT EXISTS databricks_iot_test.alert_abnomal_state      LIKE databricks_iot.alert_abnomal_state;

-- ============================================================
-- マスタデータコピー（テスト実行に必要なマスタのみ）
-- ============================================================

INSERT INTO databricks_iot_test.region_master            SELECT * FROM databricks_iot.region_master;
INSERT INTO databricks_iot_test.organization_type_master SELECT * FROM databricks_iot.organization_type_master;
INSERT INTO databricks_iot_test.contract_status_master   SELECT * FROM databricks_iot.contract_status_master;
INSERT INTO databricks_iot_test.inventory_status_master  SELECT * FROM databricks_iot.inventory_status_master;
INSERT INTO databricks_iot_test.user_type_master         SELECT * FROM databricks_iot.user_type_master;
INSERT INTO databricks_iot_test.language_master          SELECT * FROM databricks_iot.language_master;
INSERT INTO databricks_iot_test.alert_level_master       SELECT * FROM databricks_iot.alert_level_master;
INSERT INTO databricks_iot_test.alert_status_master      SELECT * FROM databricks_iot.alert_status_master;
INSERT INTO databricks_iot_test.mail_type_master         SELECT * FROM databricks_iot.mail_type_master;
INSERT INTO databricks_iot_test.measurement_item_master  SELECT * FROM databricks_iot.measurement_item_master;
INSERT INTO databricks_iot_test.master_list              SELECT * FROM databricks_iot.master_list;
INSERT INTO databricks_iot_test.sort_item_master         SELECT * FROM databricks_iot.sort_item_master;
INSERT INTO databricks_iot_test.device_type_master       SELECT * FROM databricks_iot.device_type_master;

SET FOREIGN_KEY_CHECKS = 1;

-- ============================================================
-- VIEW定義（databricks_iot_test 用）
-- 03_views.sql と同内容・USE databricks_iot_test 配下で作成
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

CREATE OR REPLACE VIEW v_device_inventory_master_by_user AS
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
