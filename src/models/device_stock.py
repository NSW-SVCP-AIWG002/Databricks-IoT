from src import db


class StockStatus(db.Model):
    __tablename__ = 'stock_status_master'

    stock_status_id = db.Column(db.Integer, primary_key=True, nullable=False)
    stock_status_name = db.Column(db.String(100), nullable=False)
    create_date = db.Column(db.DateTime, nullable=False, server_default=db.func.current_timestamp())
    creator = db.Column(db.Integer, nullable=False)
    update_date = db.Column(db.DateTime, nullable=False, server_default=db.func.current_timestamp())
    modifier = db.Column(db.Integer, nullable=False)
    delete_flag = db.Column(db.Boolean, nullable=False, default=False)


class DeviceStockInfo(db.Model):
    __tablename__ = 'device_stock_info_master'

    device_stock_id = db.Column(db.Integer, primary_key=True, nullable=False)
    stock_status_id = db.Column(db.Integer, db.ForeignKey('stock_status_master.stock_status_id'), nullable=False)
    purchase_date = db.Column(db.DateTime, nullable=False)
    estimated_ship_date = db.Column(db.DateTime, nullable=True)
    ship_date = db.Column(db.DateTime, nullable=True)
    manufacturer_warranty_end_date = db.Column(db.DateTime, nullable=False)
    vendor_warranty_end_date = db.Column(db.DateTime, nullable=False)
    stock_location = db.Column(db.String(100), nullable=False)
    create_date = db.Column(db.DateTime, nullable=False, server_default=db.func.current_timestamp())
    creator = db.Column(db.Integer, nullable=False)
    update_date = db.Column(db.DateTime, nullable=False, server_default=db.func.current_timestamp())
    modifier = db.Column(db.Integer, nullable=False)
    delete_flag = db.Column(db.Boolean, nullable=False, default=False)

    stock_status = db.relationship('StockStatus', backref='device_stocks')
