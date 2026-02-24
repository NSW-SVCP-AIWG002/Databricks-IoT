from src import db


class DeviceType(db.Model):
    __tablename__ = 'device_type_master'

    device_type_id = db.Column(db.Integer, primary_key=True, nullable=False)
    device_type_name = db.Column(db.String(100), nullable=False)
    create_date = db.Column(db.DateTime, nullable=False, server_default=db.func.current_timestamp())
    creator = db.Column(db.Integer, nullable=False)
    update_date = db.Column(db.DateTime, nullable=False, server_default=db.func.current_timestamp())
    modifier = db.Column(db.Integer, nullable=False)
    delete_flag = db.Column(db.Boolean, nullable=False, default=False)


class Device(db.Model):
    __tablename__ = 'device_master'

    device_id = db.Column(db.Integer, primary_key=True, nullable=False)
    device_uuid = db.Column(db.String(128), nullable=False, unique=True)
    organization_id = db.Column(db.Integer, db.ForeignKey('organization_master.organization_id'), nullable=True)
    device_type_id = db.Column(db.Integer, db.ForeignKey('device_type_master.device_type_id'), nullable=False)
    device_name = db.Column(db.String(100), nullable=False)
    device_model = db.Column(db.String(100), nullable=False)
    device_stock_id = db.Column(db.Integer, db.ForeignKey('device_stock_info_master.device_stock_id'), nullable=False)
    sim_id = db.Column(db.String(100), nullable=True)
    mac_address = db.Column(db.String(100), nullable=True, unique=True)
    software_version = db.Column(db.String(100), nullable=True)
    device_location = db.Column(db.String(100), nullable=True)
    certificate_expiration_date = db.Column(db.DateTime, nullable=True)
    create_date = db.Column(db.DateTime, nullable=False, server_default=db.func.current_timestamp())
    creator = db.Column(db.Integer, nullable=False)
    update_date = db.Column(db.DateTime, nullable=False, server_default=db.func.current_timestamp())
    modifier = db.Column(db.Integer, nullable=False)
    delete_flag = db.Column(db.Boolean, nullable=False, default=False)

    organization = db.relationship('Organization', backref='devices')
    device_type = db.relationship('DeviceType', backref='devices')
    device_stock = db.relationship('DeviceStockInfo', backref='device')


# エイリアス（サービス層との互換性）
DeviceTypeMaster = DeviceType
