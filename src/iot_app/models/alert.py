from iot_app import db


class AlertStatusMaster(db.Model):
    __tablename__ = "alert_status_master"

    alert_status_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    alert_status_name = db.Column(db.String(10), nullable=False)
    create_date = db.Column(db.DateTime, nullable=False, server_default=db.func.now())
    creator = db.Column(db.Integer, nullable=False)
    update_date = db.Column(db.DateTime, nullable=False, server_default=db.func.now())
    modifier = db.Column(db.Integer, nullable=False)
    delete_flag = db.Column(db.Boolean, default=False, nullable=False)


class AlertLevelMaster(db.Model):
    __tablename__ = "alert_level_master"

    alert_level_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    alert_level_name = db.Column(db.String(100), nullable=False)
    create_date = db.Column(db.DateTime, nullable=False, server_default=db.func.now())
    creator = db.Column(db.Integer, nullable=False)
    update_date = db.Column(db.DateTime, nullable=False, server_default=db.func.now())
    modifier = db.Column(db.Integer, nullable=False)
    delete_flag = db.Column(db.Boolean, default=False, nullable=False)


class AlertSettingMaster(db.Model):
    __tablename__ = "alert_setting_master"

    alert_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    alert_uuid = db.Column(db.String(36), nullable=False)
    alert_name = db.Column(db.String(100), nullable=False)
    device_id = db.Column(
        db.Integer,
        db.ForeignKey("device_master.device_id"),
        nullable=False,
    )
    alert_conditions_measurement_item_id = db.Column(
        db.Integer,
        db.ForeignKey("measurement_item_master.measurement_item_id"),
        nullable=False,
    )
    alert_conditions_operator = db.Column(db.String(10), nullable=False)
    alert_conditions_threshold = db.Column(db.Float(precision=53), nullable=False)
    alert_recovery_conditions_measurement_item_id = db.Column(
        db.Integer,
        db.ForeignKey("measurement_item_master.measurement_item_id"),
        nullable=False,
    )
    alert_recovery_conditions_operator = db.Column(db.String(10), nullable=False)
    alert_recovery_conditions_threshold = db.Column(db.Float(precision=53), nullable=False)
    judgment_time = db.Column(db.Integer, nullable=False, default=5)
    alert_level_id = db.Column(
        db.Integer,
        db.ForeignKey("alert_level_master.alert_level_id"),
        nullable=False,
    )
    alert_notification_flag = db.Column(db.Boolean, nullable=False, default=True)
    alert_email_flag = db.Column(db.Boolean, nullable=False, default=True)
    create_date = db.Column(db.DateTime, nullable=False, server_default=db.func.now())
    creator = db.Column(db.Integer, nullable=False)
    update_date = db.Column(db.DateTime, nullable=False, server_default=db.func.now())
    modifier = db.Column(db.Integer, nullable=False)
    delete_flag = db.Column(db.Boolean, default=False, nullable=False)


class AlertHistoryByUser(db.Model):
    """v_alert_history_by_user VIEW のマッピングモデル

    ユーザーIDに基づいてアクセス可能なアラート履歴を返す。
    VIEW内部で organization_closure を参照してデータスコープを制限するため、
    アプリ側では user_id フィルタのみ実施すればよい。
    """
    __tablename__ = "v_alert_history_by_user"

    alert_history_id = db.Column(db.Integer, primary_key=True)
    alert_history_uuid = db.Column(db.String(36), nullable=False)
    alert_occurrence_datetime = db.Column(db.DateTime, nullable=False)
    alert_recovery_datetime = db.Column(db.DateTime, nullable=True)
    alert_value = db.Column(db.Float, nullable=True)
    alert_status_id = db.Column(db.Integer, nullable=False)
    delete_flag = db.Column(db.Boolean, nullable=False)
    user_id = db.Column(db.Integer, nullable=False)
    # VIEW結合済みカラム（device_master / alert_setting_master / alert_level_master / alert_status_master）
    device_name = db.Column(db.String(100), nullable=True)
    device_location = db.Column(db.String(100), nullable=True)
    alert_name = db.Column(db.String(100), nullable=True)
    alert_level_id = db.Column(db.Integer, nullable=True)
    alert_level_name = db.Column(db.String(100), nullable=True)
    alert_status_name = db.Column(db.String(10), nullable=True)
    # アラート発生条件（仕様 6.7）
    alert_conditions_field = db.Column(db.String(50), nullable=True)
    alert_conditions_operator = db.Column(db.String(10), nullable=True)
    alert_conditions_threshold = db.Column(db.Float, nullable=True)
    # アラート復旧条件（仕様 6.8）
    alert_recovery_field = db.Column(db.String(50), nullable=True)
    alert_recovery_operator = db.Column(db.String(10), nullable=True)
    alert_recovery_threshold = db.Column(db.Float, nullable=True)
    # 判定時間（仕様 6.9）
    judgment_time = db.Column(db.Integer, nullable=True)


class AlertHistory(db.Model):
    __tablename__ = "alert_history"

    alert_history_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    alert_history_uuid = db.Column(db.String(36), nullable=False)
    alert_id = db.Column(
        db.Integer,
        db.ForeignKey("alert_setting_master.alert_id"),
        nullable=False,
    )
    alert_occurrence_datetime = db.Column(db.DateTime, nullable=False)
    alert_recovery_datetime = db.Column(db.DateTime, nullable=True)
    alert_status_id = db.Column(
        db.Integer,
        db.ForeignKey("alert_status_master.alert_status_id"),
        nullable=False,
    )
    alert_value = db.Column(db.Float, nullable=True)
    create_date = db.Column(db.DateTime, nullable=False, server_default=db.func.now())
    creator = db.Column(db.Integer, nullable=False)
    update_date = db.Column(db.DateTime, nullable=False, server_default=db.func.now())
    modifier = db.Column(db.Integer, nullable=False)
    delete_flag = db.Column(db.Boolean, default=False, nullable=False)
