from iot_app import db


class MeasurementItemMaster(db.Model):
    """測定項目マスタ"""
    __tablename__ = "measurement_item_master"

    measurement_item_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    display_name = db.Column(db.String(100), nullable=False)
    unit_name = db.Column(db.String(20), nullable=True)
    silver_data_column_name = db.Column(db.String(100), nullable=True)
    delete_flag = db.Column(db.Boolean, nullable=False, default=False)
