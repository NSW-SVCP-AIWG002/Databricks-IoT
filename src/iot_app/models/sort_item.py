from datetime import datetime

from iot_app import db


class SortItemMaster(db.Model):
    """ソート項目マスタ"""
    __tablename__ = 'sort_item_master'

    view_id = db.Column(db.Integer, primary_key=True, nullable=False)
    sort_item_id = db.Column(db.Integer, primary_key=True, nullable=False)
    sort_item_name = db.Column(db.String(100), nullable=False)
    sort_order = db.Column(db.Integer, nullable=False)
    delete_flag = db.Column(db.Boolean, nullable=False, default=False)
    create_date = db.Column(db.DateTime, nullable=False, default=datetime.now)
    update_date = db.Column(db.DateTime, nullable=True)
