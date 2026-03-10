from iot_app import db


class DeviceMaster(db.Model):
    """デバイスマスタ"""
    __tablename__ = "device_master"

    device_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    device_name = db.Column(db.String(200), nullable=False)
    organization_id = db.Column(db.Integer, nullable=False)
    delete_flag = db.Column(db.Boolean, nullable=False, default=False)
