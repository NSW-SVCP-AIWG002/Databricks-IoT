from iot_app import db


class AlertStatusMaster(db.Model):
    __tablename__ = "alert_status_master"

    alert_status_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    alert_status_name = db.Column(db.String(255), nullable=False)
    delete_flag = db.Column(db.Boolean, default=False, nullable=False)


class AlertLevelMaster(db.Model):
    __tablename__ = "alert_level_master"

    alert_level_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    alert_level_name = db.Column(db.String(255), nullable=False)
    delete_flag = db.Column(db.Boolean, default=False, nullable=False)


class AlertSettingMaster(db.Model):
    __tablename__ = "alert_setting_master"

    alert_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    device_id = db.Column(
        db.Integer,
        db.ForeignKey("device_master.device_id"),
        nullable=True,
    )
    alert_level_id = db.Column(
        db.Integer,
        db.ForeignKey("alert_level_master.alert_level_id"),
        nullable=True,
    )
    alert_name = db.Column(db.String(255), nullable=False)
    delete_flag = db.Column(db.Boolean, default=False, nullable=False)


class AlertHistory(db.Model):
    __tablename__ = "alert_history"

    alert_history_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    alert_id = db.Column(
        db.Integer,
        db.ForeignKey("alert_setting_master.alert_id"),
        nullable=True,
    )
    alert_status_id = db.Column(
        db.Integer,
        db.ForeignKey("alert_status_master.alert_status_id"),
        nullable=True,
    )
    alert_occurrence_datetime = db.Column(db.DateTime, nullable=False)
    delete_flag = db.Column(db.Boolean, default=False, nullable=False)
