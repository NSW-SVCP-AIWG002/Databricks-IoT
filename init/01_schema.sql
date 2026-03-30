-- ============================================================
-- Databricks IoTシステム スキーマ定義
-- データベース: databricks_iot
-- 文字コード: utf8mb4 / 照合順序: utf8mb4_general_ci
-- ============================================================

USE databricks_iot;

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- ============================================================
-- 種別・状態マスタ（FK参照先）
-- ============================================================

-- 2. ユーザー種別マスタ
CREATE TABLE IF NOT EXISTS user_type_master (
    user_type_id   INT          NOT NULL,
    user_type_name VARCHAR(20)  NOT NULL,
    create_date    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    creator        INT          NOT NULL,
    update_date    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    modifier       INT          NOT NULL,
    delete_flag    BOOLEAN      NOT NULL DEFAULT FALSE,
    PRIMARY KEY (user_type_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- 3. 言語マスタ
CREATE TABLE IF NOT EXISTS language_master (
    language_code VARCHAR(10)  NOT NULL,
    language_name VARCHAR(50)  NOT NULL,
    default_flag  BOOLEAN      NOT NULL,
    display_order INT          NOT NULL,
    create_date   DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    creator       INT          NOT NULL,
    update_date   DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    modifier      INT          NOT NULL,
    delete_flag   BOOLEAN      NOT NULL DEFAULT FALSE,
    PRIMARY KEY (language_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- 5. 組織種別マスタ
CREATE TABLE IF NOT EXISTS organization_type_master (
    organization_type_id   INT          NOT NULL,
    organization_type_name VARCHAR(50)  NOT NULL,
    create_date            DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    creator                INT          NOT NULL,
    update_date            DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    modifier               INT          NOT NULL,
    delete_flag            BOOLEAN      NOT NULL DEFAULT FALSE,
    PRIMARY KEY (organization_type_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- 6. 契約状態マスタ
CREATE TABLE IF NOT EXISTS contract_status_master (
    contract_status_id   INT          NOT NULL,
    contract_status_name VARCHAR(20)  NOT NULL,
    create_date          DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    creator              INT          NOT NULL,
    update_date          DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    modifier             INT          NOT NULL,
    delete_flag          BOOLEAN      NOT NULL DEFAULT FALSE,
    PRIMARY KEY (contract_status_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- 17. 地域マスタ
CREATE TABLE IF NOT EXISTS region_master (
    region_id   INT          NOT NULL,
    region_name VARCHAR(50)  NOT NULL,
    time_zone   VARCHAR(64)  NOT NULL,
    delete_flag BOOLEAN      NOT NULL DEFAULT FALSE,
    create_date DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    update_date DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (region_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- 9. デバイス種別マスタ
CREATE TABLE IF NOT EXISTS device_type_master (
    device_type_id   INT          NOT NULL,
    device_type_name VARCHAR(100) NOT NULL,
    create_date      DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    creator          INT          NOT NULL,
    update_date      DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    modifier         INT          NOT NULL,
    delete_flag      BOOLEAN      NOT NULL DEFAULT FALSE,
    PRIMARY KEY (device_type_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- 11. 在庫状況マスタ
CREATE TABLE IF NOT EXISTS inventory_status_master (
    inventory_status_id   INT          NOT NULL,
    inventory_status_name VARCHAR(100) NOT NULL,
    create_date           DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    creator               INT          NOT NULL,
    update_date           DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    modifier              INT          NOT NULL,
    delete_flag           BOOLEAN      NOT NULL DEFAULT FALSE,
    PRIMARY KEY (inventory_status_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- 13. 測定項目マスタ
CREATE TABLE IF NOT EXISTS measurement_item_master (
    measurement_item_id     INT          NOT NULL AUTO_INCREMENT,
    measurement_item_name   VARCHAR(50)  NOT NULL,
    silver_data_column_name VARCHAR(50)  NOT NULL,
    display_name            VARCHAR(50)  NOT NULL,
    unit_name               VARCHAR(10)  NOT NULL,
    create_date             DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    creator                 INT          NOT NULL,
    update_date             DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    modifier                INT          NOT NULL,
    delete_flag             BOOLEAN      NOT NULL DEFAULT FALSE,
    PRIMARY KEY (measurement_item_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- 14. アラートレベルマスタ
CREATE TABLE IF NOT EXISTS alert_level_master (
    alert_level_id   INT          NOT NULL AUTO_INCREMENT,
    alert_level_name VARCHAR(100) NOT NULL,
    create_date      DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    creator          INT          NOT NULL,
    update_date      DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    modifier         INT          NOT NULL,
    delete_flag      BOOLEAN      NOT NULL DEFAULT FALSE,
    PRIMARY KEY (alert_level_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- 21. アラートステータスマスタ
CREATE TABLE IF NOT EXISTS alert_status_master (
    alert_status_id   INT          NOT NULL AUTO_INCREMENT,
    alert_status_name VARCHAR(10)  NOT NULL,
    create_date       DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    creator           INT          NOT NULL,
    update_date       DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    modifier          INT          NOT NULL,
    delete_flag       BOOLEAN      NOT NULL DEFAULT FALSE,
    PRIMARY KEY (alert_status_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- 19. メール種別マスタ
CREATE TABLE IF NOT EXISTS mail_type_master (
    mail_type_id   INT          NOT NULL,
    mail_type_name VARCHAR(50)  NOT NULL,
    delete_flag    TINYINT      NOT NULL DEFAULT 0,
    create_date    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    update_date    DATETIME     NULL     DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (mail_type_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- ============================================================
-- 主要エンティティ
-- ============================================================

-- 4. 組織マスタ
CREATE TABLE IF NOT EXISTS organization_master (
    organization_id      INT          NOT NULL,
    organization_name    VARCHAR(200) NOT NULL,
    organization_type_id INT          NOT NULL,
    address              VARCHAR(500) NOT NULL,
    phone_number         VARCHAR(20)  NOT NULL,
    fax_number           VARCHAR(20)  NULL,
    contact_person       VARCHAR(20)  NOT NULL,
    contract_status_id   INT          NOT NULL,
    contract_start_date  DATE         NOT NULL,
    contract_end_date    DATE         NULL,
    databricks_group_id  VARCHAR(20)  NOT NULL,
    create_date          DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    creator              INT          NOT NULL,
    update_date          DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    modifier             INT          NOT NULL,
    delete_flag          BOOLEAN      NOT NULL DEFAULT FALSE,
    PRIMARY KEY (organization_id),
    CONSTRAINT FK_organization_type FOREIGN KEY (organization_type_id)
        REFERENCES organization_type_master (organization_type_id),
    CONSTRAINT FK_organization_contract_status FOREIGN KEY (contract_status_id)
        REFERENCES contract_status_master (contract_status_id),
    CONSTRAINT CK_contract_dates CHECK (contract_end_date IS NULL OR contract_end_date >= contract_start_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- 7. 組織閉包テーブル
CREATE TABLE IF NOT EXISTS organization_closure (
    parent_organization_id     INT NOT NULL,
    subsidiary_organization_id INT NOT NULL,
    depth                      INT NOT NULL DEFAULT 0,
    PRIMARY KEY (parent_organization_id, subsidiary_organization_id),
    INDEX IX_organization_closure_subsidiary_id (subsidiary_organization_id),
    CONSTRAINT FK_organization_closure_parent FOREIGN KEY (parent_organization_id)
        REFERENCES organization_master (organization_id),
    CONSTRAINT FK_organization_closure_subsidiary FOREIGN KEY (subsidiary_organization_id)
        REFERENCES organization_master (organization_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- 1. ユーザーマスタ
CREATE TABLE IF NOT EXISTS user_master (
    user_id                  INT          NOT NULL,
    databricks_user_id       VARCHAR(36)  NOT NULL,
    user_name                VARCHAR(20)  NOT NULL,
    organization_id          INT          NOT NULL,
    email_address            VARCHAR(254) NOT NULL,
    user_type_id             INT          NOT NULL,
    language_code            VARCHAR(10)  NOT NULL DEFAULT 'ja',
    region_id                INT          NOT NULL,
    address                  VARCHAR(500) NOT NULL,
    status                   INT          NOT NULL DEFAULT 1,
    alert_notification_flag  BOOLEAN      NOT NULL DEFAULT TRUE,
    system_notification_flag BOOLEAN      NOT NULL DEFAULT TRUE,
    create_date              DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    creator                  INT          NOT NULL,
    update_date              DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    modifier                 INT          NOT NULL,
    delete_flag              BOOLEAN      NOT NULL DEFAULT FALSE,
    PRIMARY KEY (user_id),
    UNIQUE INDEX UX_user_master_email (email_address),
    INDEX IX_user_master_organization_id (organization_id),
    INDEX IX_user_master_user_type_id (user_type_id),
    INDEX IX_user_master_language_code (language_code),
    CONSTRAINT FK_user_organization FOREIGN KEY (organization_id)
        REFERENCES organization_master (organization_id),
    CONSTRAINT FK_user_type FOREIGN KEY (user_type_id)
        REFERENCES user_type_master (user_type_id),
    CONSTRAINT FK_user_language FOREIGN KEY (language_code)
        REFERENCES language_master (language_code),
    CONSTRAINT FK_user_region FOREIGN KEY (region_id)
        REFERENCES region_master (region_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- 10. デバイス在庫情報マスタ
CREATE TABLE IF NOT EXISTS device_inventory_master (
    device_inventory_id             INT          NOT NULL AUTO_INCREMENT,
    device_inventory_uuid           VARCHAR(36)  NOT NULL,
    inventory_status_id             INT          NOT NULL,
    device_model                    VARCHAR(100) NOT NULL,
    mac_address                     VARCHAR(17)  NOT NULL,
    purchase_date                   DATETIME     NOT NULL,
    estimated_ship_date             DATETIME     NULL,
    ship_date                       DATETIME     NULL,
    manufacturer_warranty_end_date  DATETIME     NOT NULL,
    inventory_location              VARCHAR(100) NOT NULL,
    create_date                     DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    creator                         INT          NOT NULL,
    update_date                     DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    modifier                        INT          NOT NULL,
    delete_flag                     BOOLEAN      NOT NULL DEFAULT FALSE,
    PRIMARY KEY (device_inventory_id),
    UNIQUE INDEX UX_device_inventory_uuid (device_inventory_uuid),
    INDEX IX_device_inventory_status_id (inventory_status_id),
    CONSTRAINT FK_device_inventory_status FOREIGN KEY (inventory_status_id)
        REFERENCES inventory_status_master (inventory_status_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- 8. デバイスマスタ
CREATE TABLE IF NOT EXISTS device_master (
    device_id                   INT          NOT NULL,
    device_uuid                 VARCHAR(128) NOT NULL,
    organization_id             INT          NULL,
    device_type_id              INT          NOT NULL,
    device_name                 VARCHAR(100) NOT NULL,
    device_model                VARCHAR(100) NOT NULL,
    device_inventory_id         INT          NOT NULL,
    sim_id                      VARCHAR(100) NULL,
    mac_address                 VARCHAR(100) NULL,
    software_version            VARCHAR(100) NULL,
    device_location             VARCHAR(100) NULL,
    certificate_expiration_date DATETIME     NULL,
    create_date                 DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    creator                     INT          NOT NULL,
    update_date                 DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    modifier                    INT          NOT NULL,
    delete_flag                 BOOLEAN      NOT NULL DEFAULT FALSE,
    PRIMARY KEY (device_id),
    UNIQUE INDEX UX_device_master_mac_address (mac_address),
    INDEX IX_device_master_organization_id (organization_id),
    INDEX IX_device_master_type_id (device_type_id),
    INDEX IX_device_master_org_type (organization_id, device_type_id),
    CONSTRAINT FK_device_organization FOREIGN KEY (organization_id)
        REFERENCES organization_master (organization_id),
    CONSTRAINT FK_device_type FOREIGN KEY (device_type_id)
        REFERENCES device_type_master (device_type_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- 12. アラート設定マスタ
CREATE TABLE IF NOT EXISTS alert_setting_master (
    alert_id                                    INT          NOT NULL AUTO_INCREMENT,
    alert_uuid                                  VARCHAR(36)  NOT NULL,
    alert_name                                  VARCHAR(100) NOT NULL,
    device_id                                   INT          NOT NULL,
    alert_conditions_measurement_item_id        INT          NOT NULL,
    alert_conditions_operator                   VARCHAR(10)  NOT NULL,
    alert_conditions_threshold                  DOUBLE       NOT NULL,
    alert_recovery_conditions_measurement_item_id INT        NOT NULL,
    alert_recovery_conditions_operator          VARCHAR(10)  NOT NULL,
    alert_recovery_conditions_threshold         DOUBLE       NOT NULL,
    judgment_time                               INT          NOT NULL DEFAULT 5,
    alert_level_id                              INT          NOT NULL,
    alert_notification_flag                     BOOLEAN      NOT NULL DEFAULT TRUE,
    alert_email_flag                            BOOLEAN      NOT NULL DEFAULT TRUE,
    create_date                                 DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    creator                                     INT          NOT NULL,
    update_date                                 DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    modifier                                    INT          NOT NULL,
    delete_flag                                 BOOLEAN      NOT NULL DEFAULT FALSE,
    PRIMARY KEY (alert_id),
    INDEX IX_alert_setting_device_id (device_id),
    INDEX IX_alert_setting_conditions_item (alert_conditions_measurement_item_id),
    INDEX IX_alert_setting_recovery_item (alert_recovery_conditions_measurement_item_id),
    INDEX IX_alert_setting_level (alert_level_id),
    INDEX IX_alert_setting_device_level (device_id, alert_level_id),
    CONSTRAINT FK_alert_setting_device FOREIGN KEY (device_id)
        REFERENCES device_master (device_id),
    CONSTRAINT FK_alert_setting_conditions_item FOREIGN KEY (alert_conditions_measurement_item_id)
        REFERENCES measurement_item_master (measurement_item_id),
    CONSTRAINT FK_alert_setting_recovery_item FOREIGN KEY (alert_recovery_conditions_measurement_item_id)
        REFERENCES measurement_item_master (measurement_item_id),
    CONSTRAINT FK_alert_setting_level FOREIGN KEY (alert_level_id)
        REFERENCES alert_level_master (alert_level_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- 16. デバイスステータス
CREATE TABLE IF NOT EXISTS device_status_data (
    device_id   VARCHAR(100) NOT NULL,
    status      INT          NOT NULL DEFAULT 0,
    delete_flag BOOLEAN      NOT NULL DEFAULT FALSE,
    create_date DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    update_date DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (device_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- 15. ソート項目マスタ
CREATE TABLE IF NOT EXISTS sort_item_master (
    view_id        INT          NOT NULL,
    sort_item_id   INT          NOT NULL,
    sort_item_name VARCHAR(100) NOT NULL,
    sort_order     INT          NOT NULL,
    delete_flag    BOOLEAN      NOT NULL DEFAULT FALSE,
    create_date    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    update_date    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (view_id, sort_item_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- ============================================================
-- 履歴テーブル
-- ============================================================

-- 18. メール送信履歴
CREATE TABLE IF NOT EXISTS mail_history (
    mail_history_id   INT          NOT NULL,
    mail_history_uuid VARCHAR(32)  NOT NULL,
    mail_type         INT          NOT NULL,
    sender_email      VARCHAR(254) NOT NULL,
    recipients        JSON         NOT NULL,
    subject           VARCHAR(500) NOT NULL,
    body              TEXT         NOT NULL,
    sent_at           DATETIME     NOT NULL,
    user_id           INT          NULL,
    organization_id   INT          NULL,
    create_date       DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    creator           INT          NOT NULL,
    update_date       DATETIME     NULL     DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    modifier          INT          NULL,
    PRIMARY KEY (mail_history_id),
    UNIQUE INDEX UX_mail_history_uuid (mail_history_uuid),
    INDEX IX_mail_history_organization_id (organization_id),
    INDEX IX_mail_history_sent_at (sent_at),
    INDEX IX_mail_history_mail_type (mail_type),
    CONSTRAINT FK_mail_history_type FOREIGN KEY (mail_type)
        REFERENCES mail_type_master (mail_type_id),
    CONSTRAINT FK_mail_history_user FOREIGN KEY (user_id)
        REFERENCES user_master (user_id),
    CONSTRAINT FK_mail_history_organization FOREIGN KEY (organization_id)
        REFERENCES organization_master (organization_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- 20. アラート履歴
CREATE TABLE IF NOT EXISTS alert_history (
    alert_history_id          INT          NOT NULL AUTO_INCREMENT,
    alert_history_uuid        VARCHAR(36)  NOT NULL,
    alert_id                  INT          NOT NULL,
    alert_occurrence_datetime DATETIME     NOT NULL,
    alert_recovery_datetime   DATETIME     NULL,
    alert_status_id           INT          NOT NULL,
    alert_value               FLOAT        NULL,
    create_date               DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    creator                   INT          NOT NULL,
    update_date               DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    modifier                  INT          NOT NULL,
    delete_flag               BOOLEAN      NOT NULL DEFAULT FALSE,
    PRIMARY KEY (alert_history_id),
    CONSTRAINT FK_alert_history_alert FOREIGN KEY (alert_id)
        REFERENCES alert_setting_master (alert_id),
    CONSTRAINT FK_alert_history_status FOREIGN KEY (alert_status_id)
        REFERENCES alert_status_master (alert_status_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- 22. マスタ一覧
CREATE TABLE IF NOT EXISTS master_list (
    master_id    INT          NOT NULL,
    user_type_id INT          NOT NULL,
    master_name  VARCHAR(20)  NOT NULL,
    create_date  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    creator      INT          NOT NULL,
    update_date  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    modifier     INT          NOT NULL,
    delete_flag  BOOLEAN      NOT NULL DEFAULT FALSE,
    PRIMARY KEY (master_id),
    CONSTRAINT FK_master_list_user_type FOREIGN KEY (user_type_id)
        REFERENCES user_type_master (user_type_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- ============================================================
-- 顧客作成ダッシュボード
-- ============================================================

-- 32. ガジェット種別マスタ
CREATE TABLE IF NOT EXISTS gadget_type_master (
    gadget_type_id      INT           NOT NULL AUTO_INCREMENT,
    gadget_type_name    VARCHAR(20)   NOT NULL,
    data_source_type    INT           NOT NULL,
    gadget_image_path   VARCHAR(100)  NOT NULL,
    gadget_description  VARCHAR(500)  NOT NULL,
    display_order       INT           NOT NULL,
    create_date         DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    creator             INT           NOT NULL,
    update_date         DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    modifier            INT           NOT NULL,
    delete_flag         BOOLEAN       NOT NULL DEFAULT FALSE,
    PRIMARY KEY (gadget_type_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- 29. ダッシュボードマスタ
CREATE TABLE IF NOT EXISTS dashboard_master (
    dashboard_id    INT          NOT NULL AUTO_INCREMENT,
    dashboard_uuid  VARCHAR(36)  NOT NULL,
    dashboard_name  VARCHAR(50)  NOT NULL,
    organization_id INT          NOT NULL,
    create_date     DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    creator         INT          NOT NULL,
    update_date     DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    modifier        INT          NOT NULL,
    delete_flag     BOOLEAN      NOT NULL DEFAULT FALSE,
    PRIMARY KEY (dashboard_id),
    CONSTRAINT FK_dashboard_organization FOREIGN KEY (organization_id)
        REFERENCES organization_master (organization_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- 30. ダッシュボードグループマスタ
CREATE TABLE IF NOT EXISTS dashboard_group_master (
    dashboard_group_id   INT          NOT NULL AUTO_INCREMENT,
    dashboard_group_uuid VARCHAR(36)  NOT NULL,
    dashboard_group_name VARCHAR(50)  NOT NULL,
    dashboard_id         INT          NOT NULL,
    display_order        INT          NOT NULL,
    create_date          DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    creator              INT          NOT NULL,
    update_date          DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    modifier             INT          NOT NULL,
    delete_flag          BOOLEAN      NOT NULL DEFAULT FALSE,
    PRIMARY KEY (dashboard_group_id),
    CONSTRAINT FK_dashboard_group_dashboard FOREIGN KEY (dashboard_id)
        REFERENCES dashboard_master (dashboard_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- 31. ダッシュボードガジェットマスタ
CREATE TABLE IF NOT EXISTS dashboard_gadget_master (
    gadget_id           INT          NOT NULL AUTO_INCREMENT,
    gadget_uuid         VARCHAR(36)  NOT NULL,
    gadget_name         VARCHAR(20)  NOT NULL,
    dashboard_group_id  INT          NOT NULL,
    gadget_type_id      INT          NOT NULL,
    chart_config        JSON         NOT NULL,
    data_source_config  JSON         NOT NULL,
    position_x          INT          NOT NULL,
    position_y          INT          NOT NULL,
    gadget_size         INT          NOT NULL,
    display_order       INT          NOT NULL,
    create_date         DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    creator             INT          NOT NULL,
    update_date         DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    modifier            INT          NOT NULL,
    delete_flag         BOOLEAN      NOT NULL DEFAULT FALSE,
    PRIMARY KEY (gadget_id),
    CONSTRAINT FK_gadget_group FOREIGN KEY (dashboard_group_id)
        REFERENCES dashboard_group_master (dashboard_group_id),
    CONSTRAINT FK_gadget_type FOREIGN KEY (gadget_type_id)
        REFERENCES gadget_type_master (gadget_type_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- 33. ダッシュボードユーザー設定
CREATE TABLE IF NOT EXISTS dashboard_user_setting (
    user_id         INT      NOT NULL,
    dashboard_id    INT      NOT NULL,
    organization_id INT      NOT NULL,
    device_id       INT      NOT NULL,
    create_date     DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    creator         INT      NOT NULL,
    update_date     DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    modifier        INT      NOT NULL,
    delete_flag     BOOLEAN  NOT NULL DEFAULT FALSE,
    PRIMARY KEY (user_id),
    CONSTRAINT FK_dashboard_user_setting_user FOREIGN KEY (user_id)
        REFERENCES user_master (user_id),
    CONSTRAINT FK_dashboard_user_setting_dashboard FOREIGN KEY (dashboard_id)
        REFERENCES dashboard_master (dashboard_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- 34. サマリー計算手法マスタ
CREATE TABLE IF NOT EXISTS gold_summary_method_master (
    summary_method_id   INT          NOT NULL AUTO_INCREMENT,
    summary_method_code VARCHAR(20)  NOT NULL,
    summary_method_name VARCHAR(30)  NOT NULL,
    create_date         DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    creator             INT          NOT NULL,
    update_date         DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    modifier            INT          NOT NULL,
    delete_flag         BOOLEAN      NOT NULL DEFAULT FALSE,
    PRIMARY KEY (summary_method_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- ============================================================
-- 通知・アラート処理
-- ============================================================

-- 23. メール通知キュー
CREATE TABLE IF NOT EXISTS email_notification_queue (
    queue_id          BIGINT         NOT NULL AUTO_INCREMENT,
    device_id         INT            NOT NULL,
    organization_id   INT            NOT NULL,
    alert_id          INT            NOT NULL,
    recipient_email   VARCHAR(2000)  NOT NULL,
    subject           VARCHAR(500)   NOT NULL,
    body              VARCHAR(2000)  NOT NULL,
    alert_detail_json JSON           NOT NULL,
    status            VARCHAR(20)    NOT NULL,
    retry_count       INT            NOT NULL,
    error_message     JSON           NULL,
    event_timestamp   TIMESTAMP      NOT NULL,
    queued_time       TIMESTAMP      NOT NULL,
    processed_time    TIMESTAMP      NULL,
    create_time       TIMESTAMP      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    update_time       TIMESTAMP      NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (queue_id),
    CONSTRAINT FK_email_queue_device FOREIGN KEY (device_id)
        REFERENCES device_master (device_id),
    CONSTRAINT FK_email_queue_organization FOREIGN KEY (organization_id)
        REFERENCES organization_master (organization_id),
    CONSTRAINT FK_email_queue_alert FOREIGN KEY (alert_id)
        REFERENCES alert_setting_master (alert_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- 24. アラート異常状態
CREATE TABLE IF NOT EXISTS alert_abnomal_state (
    device_id           INT       NOT NULL,
    alert_id            INT       NOT NULL,
    abnormal_start_time TIMESTAMP NULL,
    last_event_time     TIMESTAMP NOT NULL,
    last_sensor_value   DOUBLE    NULL,
    alert_fired_time    TIMESTAMP NULL,
    alert_history_id    INT       NULL,
    create_time         TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    update_time         TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (device_id, alert_id),
    CONSTRAINT FK_alert_abnormal_device FOREIGN KEY (device_id)
        REFERENCES device_master (device_id),
    CONSTRAINT FK_alert_abnormal_alert FOREIGN KEY (alert_id)
        REFERENCES alert_setting_master (alert_id),
    CONSTRAINT FK_alert_abnormal_history FOREIGN KEY (alert_history_id)
        REFERENCES alert_history (alert_history_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

SET FOREIGN_KEY_CHECKS = 1;
