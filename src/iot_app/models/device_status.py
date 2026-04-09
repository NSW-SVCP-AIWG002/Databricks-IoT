from iot_app import db


class DeviceStatusData(db.Model):
    __tablename__ = "device_status_data"

    device_id                = db.Column(db.Integer, db.ForeignKey("device_master.device_id"), primary_key=True, nullable=False)
    latest_event_timestamp   = db.Column(db.DateTime, nullable=True)
    alert_count              = db.Column(db.Integer, nullable=True)
    last_alert_timestamp     = db.Column(db.DateTime, nullable=True)
    updated_at               = db.Column(db.DateTime, nullable=True)
