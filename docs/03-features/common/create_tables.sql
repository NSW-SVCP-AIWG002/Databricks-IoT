-- ============================================================
-- Databricks IoT アプリケーションDB テーブル作成スクリプト
-- DBMS  : Azure Database for MySQL 8.0
-- 文字コード: utf8mb4 / utf8mb4_general_ci
-- 生成元 : app-database-specification.md
-- 作成順 : FK依存関係を考慮した順（親テーブル → 子テーブル）
-- ============================================================

-- ============================================================
-- マスタテーブル（FK依存なし）
-- ============================================================

-- 1. 言語マスタ
CREATE TABLE language_master (
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
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci
  COMMENT='言語マスタ';


-- 2. ユーザー種別マスタ
CREATE TABLE user_type_master (
    user_type_id   INT          NOT NULL AUTO_INCREMENT,
    user_type_name VARCHAR(20)  NOT NULL,
    create_date    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    creator        INT          NOT NULL,
    update_date    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    modifier       INT          NOT NULL,
    delete_flag    BOOLEAN      NOT NULL DEFAULT FALSE,
    PRIMARY KEY (user_type_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci
  COMMENT='ユーザー種別マスタ';


-- 3. 組織種別マスタ
CREATE TABLE organization_type_master (
    organization_type_id   INT          NOT NULL AUTO_INCREMENT,
    organization_type_name VARCHAR(50)  NOT NULL,
    create_date            DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    creator                INT          NOT NULL,
    update_date            DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    modifier               INT          NOT NULL,
    delete_flag            BOOLEAN      NOT NULL DEFAULT FALSE,
    PRIMARY KEY (organization_type_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci
  COMMENT='組織種別マスタ';


-- 4. 契約状態マスタ
CREATE TABLE contract_status_master (
    contract_status_id   INT          NOT NULL AUTO_INCREMENT,
    contract_status_name VARCHAR(20)  NOT NULL,
    create_date          DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    creator              INT          NOT NULL,
    update_date          DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    modifier             INT          NOT NULL,
    delete_flag          BOOLEAN      NOT NULL DEFAULT FALSE,
    PRIMARY KEY (contract_status_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci
  COMMENT='契約状態マスタ';


-- 5. 地域マスタ
CREATE TABLE region_master (
    region_id   INT          NOT NULL AUTO_INCREMENT,
    region_name VARCHAR(50)  NOT NULL,
    time_zone   VARCHAR(64)  NOT NULL,
    delete_flag BOOLEAN      NOT NULL DEFAULT FALSE,
    create_date DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    update_date DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (region_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci
  COMMENT='地域マスタ';


-- 6. デバイス種別マスタ
CREATE TABLE device_type_master (
    device_type_id   INT           NOT NULL AUTO_INCREMENT,
    device_type_name VARCHAR(100)  NOT NULL,
    create_date      DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    creator          INT           NOT NULL,
    update_date      DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    modifier         INT           NOT NULL,
    delete_flag      BOOLEAN       NOT NULL DEFAULT FALSE,
    PRIMARY KEY (device_type_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci
  COMMENT='デバイス種別マスタ';


-- 7. 在庫状況マスタ
CREATE TABLE stock_status_master (
    stock_status_id   INT           NOT NULL AUTO_INCREMENT,
    stock_status_name VARCHAR(100)  NOT NULL,
    create_date       DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    creator           INT           NOT NULL,
    update_date       DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    modifier          INT           NOT NULL,
    delete_flag       BOOLEAN       NOT NULL DEFAULT FALSE,
    PRIMARY KEY (stock_status_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci
  COMMENT='在庫状況マスタ';


-- 8. アラートレベルマスタ
CREATE TABLE alert_level_master (
    alert_level_id   INT           NOT NULL AUTO_INCREMENT,
    alert_level_name VARCHAR(100)  NOT NULL,
    create_date      DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    creator          INT           NOT NULL,
    update_date      DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    modifier         INT           NOT NULL,
    delete_flag      BOOLEAN       NOT NULL DEFAULT FALSE,
    PRIMARY KEY (alert_level_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci
  COMMENT='アラートレベルマスタ';


-- 9. 測定項目マスタ
CREATE TABLE measurement_item_master (
    measurement_item_id   INT          NOT NULL AUTO_INCREMENT,
    measurement_item_name VARCHAR(50)  NOT NULL,
    create_date           DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    creator               INT          NOT NULL,
    update_date           DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    modifier              INT          NOT NULL,
    delete_flag           BOOLEAN      NOT NULL DEFAULT FALSE,
    PRIMARY KEY (measurement_item_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci
  COMMENT='測定項目マスタ';


-- 10. メール種別マスタ
CREATE TABLE mail_type_master (
    mail_type_id   INT          NOT NULL AUTO_INCREMENT,
    mail_type_name VARCHAR(50)  NOT NULL,
    delete_flag    TINYINT      NOT NULL DEFAULT 0,
    create_date    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    update_date    DATETIME     NULL     DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (mail_type_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci
  COMMENT='メール種別マスタ';


-- 11. アラートステータスマスタ
CREATE TABLE alert_status_master (
    alert_status_id   INT          NOT NULL AUTO_INCREMENT,
    alert_status_name VARCHAR(10)  NOT NULL,
    create_date       DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    creator           INT          NOT NULL,
    update_date       DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    modifier          INT          NOT NULL,
    delete_flag       BOOLEAN      NOT NULL DEFAULT FALSE,
    PRIMARY KEY (alert_status_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci
  COMMENT='アラートステータスマスタ';


-- 12. ソート項目マスタ（複合PK）
CREATE TABLE sort_item_master (
    view_id        INT           NOT NULL,
    sort_item_id   INT           NOT NULL,
    sort_item_name VARCHAR(100)  NOT NULL,
    sort_order     INT           NOT NULL,
    delete_flag    BOOLEAN       NOT NULL DEFAULT FALSE,
    create_date    DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    update_date    DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (view_id, sort_item_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci
  COMMENT='ソート項目マスタ';


-- ============================================================
-- 依存テーブル（FK参照あり）
-- ============================================================

-- 13. 組織マスタ
CREATE TABLE organization_master (
    organization_id      INT           NOT NULL AUTO_INCREMENT,
    organization_name    VARCHAR(200)  NOT NULL,
    organization_type_id INT           NOT NULL,
    address              VARCHAR(500)  NOT NULL,
    phone_number         VARCHAR(20)   NOT NULL,
    fax_number           VARCHAR(20)   NULL,
    contact_person       VARCHAR(20)   NOT NULL,
    contract_status_id   INT           NOT NULL,
    contract_start_date  DATE          NOT NULL,
    contract_end_date    DATE          NULL,
    databricks_group_id  VARCHAR(20)   NOT NULL,
    create_date          DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    creator              INT           NOT NULL,
    update_date          DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    modifier             INT           NOT NULL,
    delete_flag          BOOLEAN       NOT NULL DEFAULT FALSE,
    PRIMARY KEY (organization_id),
    CONSTRAINT FK_organization_type
        FOREIGN KEY (organization_type_id) REFERENCES organization_type_master(organization_type_id),
    CONSTRAINT FK_organization_contract_status
        FOREIGN KEY (contract_status_id) REFERENCES contract_status_master(contract_status_id),
    CONSTRAINT CK_contract_dates
        CHECK (contract_end_date IS NULL OR contract_end_date >= contract_start_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci
  COMMENT='組織マスタ';


-- 14. 組織閉方テーブル（複合PK・閉包テーブルパターン）
CREATE TABLE organization_closure (
    parent_organization_id     INT  NOT NULL,
    subsidiary_organization_id INT  NOT NULL,
    depth                      INT  NOT NULL DEFAULT 0,
    PRIMARY KEY (parent_organization_id, subsidiary_organization_id),
    INDEX IX_organization_closure_subsidiary_id (subsidiary_organization_id),
    CONSTRAINT FK_organization_closure_parent
        FOREIGN KEY (parent_organization_id) REFERENCES organization_master(organization_id),
    CONSTRAINT FK_organization_closure_subsidiary
        FOREIGN KEY (subsidiary_organization_id) REFERENCES organization_master(organization_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci
  COMMENT='組織閉方テーブル（閉包テーブルパターン）';


-- 15. デバイス在庫情報マスタ
CREATE TABLE device_stock_info_master (
    device_stock_id                INT           NOT NULL AUTO_INCREMENT,
    stock_status_id                INT           NOT NULL,
    purchase_date                  DATETIME      NOT NULL,
    estimated_ship_date            DATETIME      NULL,
    ship_date                      DATETIME      NULL,
    manufacturer_warranty_end_date DATETIME      NOT NULL,
    vendor_warranty_end_date       DATETIME      NOT NULL,
    stock_location                 VARCHAR(100)  NOT NULL,
    create_date                    DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    creator                        INT           NOT NULL,
    update_date                    DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    modifier                       INT           NOT NULL,
    delete_flag                    BOOLEAN       NOT NULL DEFAULT FALSE,
    PRIMARY KEY (device_stock_id),
    INDEX IX_device_stock_status_id (stock_status_id),
    CONSTRAINT FK_device_stock_status
        FOREIGN KEY (stock_status_id) REFERENCES stock_status_master(stock_status_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci
  COMMENT='デバイス在庫情報マスタ';


-- 16. ユーザーマスタ
CREATE TABLE user_master (
    user_id                  INT           NOT NULL AUTO_INCREMENT,
    databricks_user_id       VARCHAR(36)   NOT NULL,
    user_name                VARCHAR(20)   NOT NULL,
    organization_id          INT           NOT NULL,
    email_address            VARCHAR(254)  NOT NULL,
    user_type_id             INT           NOT NULL,
    language_code            VARCHAR(10)   NOT NULL DEFAULT 'ja',
    region_id                INT           NOT NULL,
    address                  VARCHAR(500)  NOT NULL,
    status                   INT           NOT NULL DEFAULT 1,
    alert_notification_flag  BOOLEAN       NOT NULL DEFAULT TRUE,
    system_notification_flag BOOLEAN       NOT NULL DEFAULT TRUE,
    create_date              DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    creator                  INT           NOT NULL,
    update_date              DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    modifier                 INT           NOT NULL,
    delete_flag              BOOLEAN       NOT NULL DEFAULT FALSE,
    PRIMARY KEY (user_id),
    UNIQUE KEY UX_user_master_email (email_address),
    INDEX IX_user_master_organization_id (organization_id),
    INDEX IX_user_master_user_type_id (user_type_id),
    INDEX IX_user_master_language_code (language_code),
    CONSTRAINT FK_user_organization
        FOREIGN KEY (organization_id) REFERENCES organization_master(organization_id),
    CONSTRAINT FK_user_type
        FOREIGN KEY (user_type_id) REFERENCES user_type_master(user_type_id),
    CONSTRAINT FK_user_language
        FOREIGN KEY (language_code) REFERENCES language_master(language_code),
    CONSTRAINT FK_user_region
        FOREIGN KEY (region_id) REFERENCES region_master(region_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci
  COMMENT='ユーザーマスタ';


-- 17. デバイスマスタ
CREATE TABLE device_master (
    device_id                   INT           NOT NULL AUTO_INCREMENT,
    device_uuid                 VARCHAR(128)  NOT NULL,
    organization_id             INT           NULL,
    device_type_id              INT           NOT NULL,
    device_name                 VARCHAR(100)  NOT NULL,
    device_model                VARCHAR(100)  NOT NULL,
    device_stock_id             INT           NOT NULL,
    sim_id                      VARCHAR(100)  NULL,
    mac_address                 VARCHAR(100)  NULL,
    software_version            VARCHAR(100)  NULL,
    device_location             VARCHAR(100)  NULL,
    certificate_expiration_date DATETIME      NULL,
    create_date                 DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    creator                     INT           NOT NULL,
    update_date                 DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    modifier                    INT           NOT NULL,
    delete_flag                 BOOLEAN       NOT NULL DEFAULT FALSE,
    PRIMARY KEY (device_id),
    UNIQUE KEY UX_device_master_uuid (device_uuid),
    UNIQUE KEY UX_device_master_mac_address (mac_address),
    INDEX IX_device_master_organization_id (organization_id),
    INDEX IX_device_master_type_id (device_type_id),
    INDEX IX_device_master_org_type (organization_id, device_type_id),
    CONSTRAINT FK_device_organization
        FOREIGN KEY (organization_id) REFERENCES organization_master(organization_id),
    CONSTRAINT FK_device_type
        FOREIGN KEY (device_type_id) REFERENCES device_type_master(device_type_id),
    CONSTRAINT FK_device_stock
        FOREIGN KEY (device_stock_id) REFERENCES device_stock_info_master(device_stock_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci
  COMMENT='デバイスマスタ';


-- 18. デバイスステータス
CREATE TABLE device_status_data (
    device_id          INT        NOT NULL,
    last_received_time TIMESTAMP  NULL,
    delete_flag        BOOLEAN    NOT NULL DEFAULT FALSE,
    create_date        DATETIME   NOT NULL DEFAULT CURRENT_TIMESTAMP,
    update_date        DATETIME   NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (device_id),
    CONSTRAINT FK_device_status_device
        FOREIGN KEY (device_id) REFERENCES device_master(device_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci
  COMMENT='デバイスステータス';


-- 19. アラート設定マスタ
CREATE TABLE alert_setting_master (
    alert_id                                      INT           NOT NULL AUTO_INCREMENT,
    alert_uuid                                    VARCHAR(36)   NOT NULL,
    alert_name                                    VARCHAR(100)  NOT NULL,
    device_id                                     INT           NOT NULL,
    alert_conditions_measurement_item_id          INT           NOT NULL,
    alert_conditions_operator                     VARCHAR(10)   NOT NULL,
    alert_conditions_threshold                    DOUBLE        NOT NULL,
    alert_recovery_conditions_measurement_item_id INT           NOT NULL,
    alert_recovery_conditions_operator            VARCHAR(10)   NOT NULL,
    alert_recovery_conditions_threshold           DOUBLE        NOT NULL,
    judgment_time                                 INT           NOT NULL DEFAULT 5,
    alert_level_id                                INT           NOT NULL,
    alert_notification_flag                       BOOLEAN       NOT NULL DEFAULT TRUE,
    alert_email_flag                              BOOLEAN       NOT NULL DEFAULT TRUE,
    create_date                                   DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    creator                                       INT           NOT NULL,
    update_date                                   DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    modifier                                      INT           NOT NULL,
    delete_flag                                   BOOLEAN       NOT NULL DEFAULT FALSE,
    PRIMARY KEY (alert_id),
    UNIQUE KEY UX_alert_setting_uuid (alert_uuid),
    INDEX IX_alert_setting_device_id (device_id),
    INDEX IX_alert_setting_measurement_item_id (alert_conditions_measurement_item_id),
    INDEX IX_alert_setting_recovery_item_id (alert_recovery_conditions_measurement_item_id),
    INDEX IX_alert_setting_level (alert_level_id),
    INDEX IX_alert_setting_device_level (device_id, alert_level_id),
    CONSTRAINT FK_alert_device
        FOREIGN KEY (device_id) REFERENCES device_master(device_id),
    CONSTRAINT FK_alert_measurement_item
        FOREIGN KEY (alert_conditions_measurement_item_id) REFERENCES measurement_item_master(measurement_item_id),
    CONSTRAINT FK_alert_recovery_measurement_item
        FOREIGN KEY (alert_recovery_conditions_measurement_item_id) REFERENCES measurement_item_master(measurement_item_id),
    CONSTRAINT FK_alert_level
        FOREIGN KEY (alert_level_id) REFERENCES alert_level_master(alert_level_id),
    CONSTRAINT CK_alert_notification_flag
        CHECK (alert_notification_flag IN (0, 1)),
    CONSTRAINT CK_alert_email_flag
        CHECK (alert_email_flag IN (0, 1))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci
  COMMENT='アラート設定マスタ';


-- 20. メール送信履歴
CREATE TABLE mail_history (
    mail_history_id   INT           NOT NULL AUTO_INCREMENT,
    mail_history_uuid VARCHAR(32)   NOT NULL,
    mail_type         INT           NOT NULL,
    sender_email      VARCHAR(254)  NOT NULL,
    recipients        JSON          NOT NULL,
    subject           VARCHAR(500)  NOT NULL,
    body              TEXT          NOT NULL,
    sent_at           DATETIME      NOT NULL,
    user_id           INT           NULL,
    organization_id   INT           NULL,
    create_date       DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    creator           INT           NOT NULL,
    update_date       DATETIME      NULL     DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    modifier          INT           NULL,
    PRIMARY KEY (mail_history_id),
    UNIQUE KEY UX_mail_history_uuid (mail_history_uuid),
    INDEX IX_mail_history_organization_id (organization_id),
    INDEX IX_mail_history_sent_at (sent_at),
    INDEX IX_mail_history_mail_type (mail_type),
    CONSTRAINT FK_mail_history_type
        FOREIGN KEY (mail_type) REFERENCES mail_type_master(mail_type_id),
    CONSTRAINT FK_mail_history_user
        FOREIGN KEY (user_id) REFERENCES user_master(user_id),
    CONSTRAINT FK_mail_history_organization
        FOREIGN KEY (organization_id) REFERENCES organization_master(organization_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci
  COMMENT='メール送信履歴';


-- 21. アラート履歴
CREATE TABLE alert_history (
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
    UNIQUE KEY UX_alert_history_uuid (alert_history_uuid),
    INDEX IX_alert_history_alert_id (alert_id),
    INDEX IX_alert_history_status_id (alert_status_id),
    CONSTRAINT FK_alert_history_alert
        FOREIGN KEY (alert_id) REFERENCES alert_setting_master(alert_id),
    CONSTRAINT FK_alert_history_status
        FOREIGN KEY (alert_status_id) REFERENCES alert_status_master(alert_status_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci
  COMMENT='アラート履歴';


-- 22. マスタ一覧
CREATE TABLE master_list (
    master_id    INT          NOT NULL AUTO_INCREMENT,
    user_type_id INT          NOT NULL,
    master_name  VARCHAR(20)  NOT NULL,
    create_date  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    creator      INT          NOT NULL,
    update_date  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    modifier     INT          NOT NULL,
    delete_flag  BOOLEAN      NOT NULL DEFAULT FALSE,
    PRIMARY KEY (master_id),
    CONSTRAINT FK_master_list_user_type
        FOREIGN KEY (user_type_id) REFERENCES user_type_master(user_type_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci
  COMMENT='マスタ一覧';


-- 23. メール通知キュー
CREATE TABLE email_notification_queue (
    queue_id          BIGINT         NOT NULL AUTO_INCREMENT,
    device_id         INT            NOT NULL,
    organization_id   INT            NOT NULL,
    alert_id          INT            NOT NULL,
    recipient_email   VARCHAR(2000)  NOT NULL,
    subject           VARCHAR(500)   NOT NULL,
    body              VARCHAR(2000)  NOT NULL,
    alert_detail_json JSON           NOT NULL,
    status            VARCHAR(20)    NOT NULL,
    retry_count       INT            NOT NULL DEFAULT 0,
    error_message     JSON           NULL,
    event_timestamp   TIMESTAMP      NOT NULL,
    queued_time       TIMESTAMP      NOT NULL,
    processed_time    TIMESTAMP      NULL,
    create_time       TIMESTAMP      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    update_time       TIMESTAMP      NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (queue_id),
    INDEX IX_email_queue_status (status),
    INDEX IX_email_queue_device_id (device_id),
    CONSTRAINT FK_email_queue_device
        FOREIGN KEY (device_id) REFERENCES device_master(device_id),
    CONSTRAINT FK_email_queue_organization
        FOREIGN KEY (organization_id) REFERENCES organization_master(organization_id),
    CONSTRAINT FK_email_queue_alert
        FOREIGN KEY (alert_id) REFERENCES alert_setting_master(alert_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci
  COMMENT='メール通知キュー';


-- 24. アラート異常状態（複合PK）
CREATE TABLE alert_abnomal_state (
    device_id           INT        NOT NULL,
    alert_id            INT        NOT NULL,
    abnormal_start_time TIMESTAMP  NULL,
    last_event_time     TIMESTAMP  NOT NULL,
    last_sensor_value   DOUBLE     NULL,
    alert_fired_time    TIMESTAMP  NULL,
    alert_history_id    INT        NULL,
    create_time         TIMESTAMP  NOT NULL DEFAULT CURRENT_TIMESTAMP,
    update_time         TIMESTAMP  NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (device_id, alert_id),
    CONSTRAINT FK_alert_abnormal_device
        FOREIGN KEY (device_id) REFERENCES device_master(device_id),
    CONSTRAINT FK_alert_abnormal_alert
        FOREIGN KEY (alert_id) REFERENCES alert_setting_master(alert_id),
    CONSTRAINT FK_alert_abnormal_history
        FOREIGN KEY (alert_history_id) REFERENCES alert_history(alert_history_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci
  COMMENT='アラート異常状態';


-- ============================================================
-- オンプレミス環境専用テーブル
-- ※ Azure Easy Auth 環境ではテーブルは作成するがデータは格納しない
-- ============================================================

-- 25. ユーザーパスワード
CREATE TABLE user_password (
    user_id               INT          NOT NULL,
    password_hash         VARCHAR(60)  NULL,
    password_update_date  DATETIME     NULL,
    password_expires_date DATETIME     NULL,
    create_date           DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    update_date           DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id),
    CONSTRAINT FK_user_password_user
        FOREIGN KEY (user_id) REFERENCES user_master(user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci
  COMMENT='ユーザーパスワード（オンプレミス環境専用）';


-- 26. パスワードリセットトークン
CREATE TABLE password_reset_token (
    token_hash   VARCHAR(64)  NOT NULL,
    user_id      INT          NOT NULL,
    token_type   TINYINT      NOT NULL COMMENT '1:INVITE / 2:RESET',
    expires_date DATETIME     NOT NULL,
    create_date  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    update_date  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (token_hash),
    INDEX IX_password_reset_token_user_id (user_id),
    INDEX IX_password_reset_token_expires (expires_date),
    CONSTRAINT FK_password_reset_token_user
        FOREIGN KEY (user_id) REFERENCES user_master(user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci
  COMMENT='パスワードリセットトークン（オンプレミス環境専用）';


-- 27. ログイン履歴
CREATE TABLE login_history (
    login_history_id INT           NOT NULL AUTO_INCREMENT,
    user_id          INT           NULL,
    email            VARCHAR(254)  NOT NULL,
    login_date       DATETIME      NOT NULL,
    ip_address       VARCHAR(45)   NOT NULL,
    user_agent       TEXT          NOT NULL,
    success          BOOLEAN       NOT NULL,
    failure_reason   VARCHAR(100)  NULL,
    create_date      DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    update_date      DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (login_history_id),
    INDEX IX_login_history_user_id (user_id),
    INDEX IX_login_history_email (email),
    INDEX IX_login_history_login_date (login_date),
    CONSTRAINT FK_login_history_user
        FOREIGN KEY (user_id) REFERENCES user_master(user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci
  COMMENT='ログイン履歴（オンプレミス環境専用）';


-- 28. アカウントロック管理
CREATE TABLE account_lock (
    user_id           INT       NOT NULL,
    failed_attempts   INT       NOT NULL DEFAULT 0,
    last_failed_date  DATETIME  NOT NULL,
    locked_date       DATETIME  NULL,
    lock_expires_date DATETIME  NULL,
    PRIMARY KEY (user_id),
    CONSTRAINT FK_account_lock_user
        FOREIGN KEY (user_id) REFERENCES user_master(user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci
  COMMENT='アカウントロック管理（オンプレミス環境専用）';
