"""
ダッシュボード関連モデル

テーブル:
  - dashboard_gadget_master: ガジェット定義
  - gadget_type_master:      ガジェット種別マスタ
"""

from iot_app import db


class GadgetTypeMaster(db.Model):
    """ガジェット種別マスタ"""

    __tablename__ = 'gadget_type_master'

    gadget_type_id   = db.Column(db.Integer, primary_key=True, autoincrement=True)
    gadget_type_name = db.Column(db.String(100), nullable=False)
    delete_flag      = db.Column(db.Boolean, default=False, nullable=False)

    def __init__(self, **kwargs):
        kwargs.setdefault('delete_flag', False)
        super().__init__(**kwargs)


class DashboardGadgetMaster(db.Model):
    """ダッシュボードガジェットマスタ"""

    __tablename__ = 'dashboard_gadget_master'

    gadget_id           = db.Column(db.Integer, primary_key=True, autoincrement=True)
    gadget_uuid         = db.Column(db.String(36), unique=True, nullable=False)
    gadget_name         = db.Column(db.String(100), nullable=False)
    gadget_type_id      = db.Column(db.Integer, db.ForeignKey('gadget_type_master.gadget_type_id'), nullable=False)
    dashboard_group_id  = db.Column(db.Integer, nullable=False)
    chart_config        = db.Column(db.Text, nullable=False)
    data_source_config  = db.Column(db.Text, nullable=False)
    position_x          = db.Column(db.Integer, default=0, nullable=False)
    position_y          = db.Column(db.Integer, default=0, nullable=False)
    gadget_size         = db.Column(db.String(10), nullable=False)
    display_order       = db.Column(db.Integer, default=0, nullable=False)
    create_date         = db.Column(db.DateTime, nullable=True)
    creator             = db.Column(db.Integer, nullable=False)
    update_date         = db.Column(db.DateTime, nullable=True)
    modifier            = db.Column(db.Integer, nullable=False)
    delete_flag         = db.Column(db.Boolean, default=False, nullable=False)

    def __init__(self, **kwargs):
        kwargs.setdefault('position_x', 0)
        kwargs.setdefault('position_y', 0)
        kwargs.setdefault('display_order', 0)
        kwargs.setdefault('delete_flag', False)
        super().__init__(**kwargs)
