from iot_app import db


class DeviceStatusData(db.Model):
    __tablename__ = "device_status_data"

    device_id           = db.Column(db.Integer, db.ForeignKey("device_master.device_id"), primary_key=True, nullable=False)
    last_received_time  = db.Column(db.DateTime, nullable=True)
    delete_flag         = db.Column(db.Boolean, nullable=False, default=False)
    create_date         = db.Column(db.DateTime, nullable=False)
    update_date         = db.Column(db.DateTime, nullable=False)
