from iot_app import db


class DeviceTypeMaster(db.Model):
    __tablename__ = "device_type_master"

    device_type_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    device_type_name = db.Column(db.String(100), nullable=False)
    create_date = db.Column(db.DateTime, nullable=False, server_default=db.func.now())
    creator = db.Column(db.Integer, nullable=False)
    update_date = db.Column(db.DateTime, nullable=False, server_default=db.func.now())
    modifier = db.Column(db.Integer, nullable=False)
    delete_flag = db.Column(db.Boolean, default=False, nullable=False)


class Device(db.Model):
    __tablename__ = "device_master"

    device_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    device_uuid = db.Column(db.String(128), nullable=False, unique=True)
    organization_id = db.Column(
        db.Integer,
        db.ForeignKey("organization_master.organization_id"),
        nullable=True,
    )
    device_type_id = db.Column(
        db.Integer,
        db.ForeignKey("device_type_master.device_type_id"),
        nullable=True,
    )
    device_name = db.Column(db.String(100), nullable=False)
    device_model = db.Column(db.String(100), nullable=False)
    device_inventory_id = db.Column(db.Integer, nullable=True)
    sim_id = db.Column(db.String(100), nullable=True)
    mac_address = db.Column(db.String(100), nullable=True, unique=True)
    software_version = db.Column(db.String(100), nullable=True)
    device_location = db.Column(db.String(100), nullable=True)
    certificate_expiration_date = db.Column(db.DateTime, nullable=True)
    create_date = db.Column(db.DateTime, nullable=False, server_default=db.func.now())
    creator = db.Column(db.Integer, nullable=False)
    update_date = db.Column(db.DateTime, nullable=False, server_default=db.func.now())
    modifier = db.Column(db.Integer, nullable=False)
    delete_flag = db.Column(db.Boolean, default=False, nullable=False)
