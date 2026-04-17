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
