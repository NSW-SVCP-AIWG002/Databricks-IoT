from src import db


class AlertLevel(db.Model):
    __tablename__ = 'alert_level_master'

    alert_level_id = db.Column(db.Integer, primary_key=True, autoincrement=True, nullable=False)
    alert_level_name = db.Column(db.String(100), nullable=False)
    create_date = db.Column(db.DateTime, nullable=False, server_default=db.func.current_timestamp())
    creator = db.Column(db.Integer, nullable=False)
    update_date = db.Column(db.DateTime, nullable=False, server_default=db.func.current_timestamp())
    modifier = db.Column(db.Integer, nullable=False)
    delete_flag = db.Column(db.Boolean, nullable=False, default=False)


class AlertSetting(db.Model):
    __tablename__ = 'alert_setting_master'

    alert_id = db.Column(db.Integer, primary_key=True, autoincrement=True, nullable=False)
    alert_uuid = db.Column(db.String(36), nullable=False)
    alert_name = db.Column(db.String(100), nullable=False)
    device_id = db.Column(db.Integer, db.ForeignKey('device_master.device_id'), nullable=False)
    alert_conditions_measurement_item_id = db.Column(db.Integer, db.ForeignKey('measurement_item_master.measurement_item_id'), nullable=False)
    alert_conditions_operator = db.Column(db.String(10), nullable=False)
    alert_conditions_threshold = db.Column(db.Float(precision=53), nullable=False)
    alert_recovery_conditions_measurement_item_id = db.Column(db.Integer, db.ForeignKey('measurement_item_master.measurement_item_id'), nullable=False)
    alert_recovery_conditions_operator = db.Column(db.String(10), nullable=False)
    alert_recovery_conditions_threshold = db.Column(db.Float(precision=53), nullable=False)
    judgment_time = db.Column(db.Integer, nullable=False, default=5)
    alert_level_id = db.Column(db.Integer, db.ForeignKey('alert_level_master.alert_level_id'), nullable=False)
    alert_notification_flag = db.Column(db.Boolean, nullable=False, default=True)
    alert_email_flag = db.Column(db.Boolean, nullable=False, default=True)
    create_date = db.Column(db.DateTime, nullable=False, server_default=db.func.current_timestamp())
    creator = db.Column(db.Integer, nullable=False)
    update_date = db.Column(db.DateTime, nullable=False, server_default=db.func.current_timestamp())
    modifier = db.Column(db.Integer, nullable=False)
    delete_flag = db.Column(db.Boolean, nullable=False, default=False)

    device = db.relationship('Device', backref='alert_settings')
    alert_level = db.relationship('AlertLevel', backref='alert_settings')
    alert_conditions_measurement_item = db.relationship('MeasurementItem', foreign_keys=[alert_conditions_measurement_item_id])
    alert_recovery_conditions_measurement_item = db.relationship('MeasurementItem', foreign_keys=[alert_recovery_conditions_measurement_item_id])


class AlertStatus(db.Model):
    __tablename__ = 'alert_status_master'

    alert_status_id = db.Column(db.Integer, primary_key=True, autoincrement=True, nullable=False)
    alert_status_name = db.Column(db.String(10), nullable=False)
    create_date = db.Column(db.DateTime, nullable=False, server_default=db.func.current_timestamp())
    creator = db.Column(db.Integer, nullable=False)
    update_date = db.Column(db.DateTime, nullable=False, server_default=db.func.current_timestamp())
    modifier = db.Column(db.Integer, nullable=False)
    delete_flag = db.Column(db.Boolean, nullable=False, default=False)


class AlertHistory(db.Model):
    __tablename__ = 'alert_history'

    alert_history_id = db.Column(db.Integer, primary_key=True, autoincrement=True, nullable=False)
    alert_history_uuid = db.Column(db.String(36), nullable=False)
    alert_id = db.Column(db.Integer, db.ForeignKey('alert_setting_master.alert_id'), nullable=False)
    alert_occurrence_datetime = db.Column(db.DateTime, nullable=False)
    alert_recovery_datetime = db.Column(db.DateTime, nullable=True)
    alert_status_id = db.Column(db.Integer, db.ForeignKey('alert_status_master.alert_status_id'), nullable=False)
    alert_value = db.Column(db.Float, nullable=True)
    create_date = db.Column(db.DateTime, nullable=False, server_default=db.func.current_timestamp())
    creator = db.Column(db.Integer, nullable=False)
    update_date = db.Column(db.DateTime, nullable=False, server_default=db.func.current_timestamp())
    modifier = db.Column(db.Integer, nullable=False)
    delete_flag = db.Column(db.Boolean, nullable=False, default=False)

    alert_setting = db.relationship('AlertSetting', backref='alert_histories')
    alert_status = db.relationship('AlertStatus', backref='alert_histories')


# エイリアス（サービス層との互換性）
AlertLevelMaster = AlertLevel
AlertSettingMaster = AlertSetting
AlertStatusMaster = AlertStatus
