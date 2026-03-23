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
