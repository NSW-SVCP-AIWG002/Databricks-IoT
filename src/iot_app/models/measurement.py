from datetime import datetime

from iot_app import db


class MeasurementItemMaster(db.Model):
    """測定項目マスタ"""
    __tablename__ = 'measurement_item_master'

    measurement_item_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    measurement_item_name = db.Column(db.String(50), nullable=False)
    silver_data_column_name = db.Column(db.String(50), nullable=False)
    display_name = db.Column(db.String(50), nullable=False)
    unit_name = db.Column(db.String(10), nullable=False)
    create_date = db.Column(db.DateTime, nullable=False, default=datetime.now)
    creator = db.Column(db.Integer, nullable=False)
    update_date = db.Column(db.DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)
    modifier = db.Column(db.Integer, nullable=False)
    delete_flag = db.Column(db.Boolean, nullable=False, default=False)

    def __init__(self, **kwargs):
        kwargs.setdefault('delete_flag', False)
        super().__init__(**kwargs)
