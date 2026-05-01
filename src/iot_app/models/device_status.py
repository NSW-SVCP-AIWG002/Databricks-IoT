from iot_app import db


class DeviceStatusData(db.Model):
    __tablename__ = "device_status_data"

    device_id   = db.Column(db.String(100), primary_key=True, nullable=False)
    status      = db.Column(db.Integer, nullable=False, default=0)
    delete_flag = db.Column(db.Boolean, nullable=False, default=False)
    create_date = db.Column(db.DateTime, nullable=False)
    update_date = db.Column(db.DateTime, nullable=False)
