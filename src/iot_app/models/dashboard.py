from datetime import datetime

from iot_app import db


class GadgetTypeMaster(db.Model):
    """ガジェット種別マスタ"""
    __tablename__ = "gadget_type_master"

    gadget_type_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    gadget_type_name = db.Column(db.String(100), nullable=False)
    delete_flag = db.Column(db.Boolean, nullable=False, default=False)


class DashboardGadgetMaster(db.Model):
    """ダッシュボードガジェットマスタ"""
    __tablename__ = "dashboard_gadget_master"

    gadget_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    gadget_uuid = db.Column(db.String(36), nullable=False, unique=True)
    gadget_name = db.Column(db.String(100), nullable=False)
    gadget_type_id = db.Column(db.Integer, db.ForeignKey("gadget_type_master.gadget_type_id"), nullable=False)
    dashboard_group_id = db.Column(db.Integer, nullable=False)
    chart_config = db.Column(db.Text, nullable=True)
    data_source_config = db.Column(db.Text, nullable=True)
    position_x = db.Column(db.Integer, nullable=False, default=0)
    position_y = db.Column(db.Integer, nullable=False, default=0)
    gadget_size = db.Column(db.String(10), nullable=True)
    display_order = db.Column(db.Integer, nullable=False, default=0)
    create_date = db.Column(db.DateTime, nullable=False, default=datetime.now)
    creator = db.Column(db.Integer, nullable=True)
    update_date = db.Column(db.DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)
    modifier = db.Column(db.Integer, nullable=True)
    delete_flag = db.Column(db.Boolean, nullable=False, default=False)
