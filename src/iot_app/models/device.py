from iot_app import db


class Device(db.Model):
    __tablename__ = "device_master"

    device_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    device_uuid = db.Column(db.String(255), nullable=False, unique=True)
    device_name = db.Column(db.String(255), nullable=False)
    organization_id = db.Column(
        db.Integer,
        db.ForeignKey("organization_master.organization_id"),
        nullable=True,
    )
    delete_flag = db.Column(db.Boolean, default=False, nullable=False)
