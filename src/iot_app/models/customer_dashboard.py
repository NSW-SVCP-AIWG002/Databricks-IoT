from datetime import datetime

from iot_app import db


class DashboardMaster(db.Model):
    """ダッシュボードマスタ"""
    __tablename__ = 'dashboard_master'

    dashboard_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    dashboard_uuid = db.Column(db.String(36), nullable=False)
    dashboard_name = db.Column(db.String(50), nullable=False)
    organization_id = db.Column(db.Integer, nullable=False)
    create_date = db.Column(db.DateTime, nullable=False, default=datetime.now)
    creator = db.Column(db.Integer, nullable=False)
    update_date = db.Column(db.DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)
    modifier = db.Column(db.Integer, nullable=False)
    delete_flag = db.Column(db.Boolean, nullable=False, default=False)

    def __init__(self, **kwargs):
        kwargs.setdefault('delete_flag', False)
        super().__init__(**kwargs)


class DashboardGroupMaster(db.Model):
    """ダッシュボードグループマスタ"""
    __tablename__ = 'dashboard_group_master'

    dashboard_group_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    dashboard_group_uuid = db.Column(db.String(36), nullable=False)
    dashboard_group_name = db.Column(db.String(50), nullable=False)
    dashboard_id = db.Column(db.Integer, db.ForeignKey('dashboard_master.dashboard_id'), nullable=False)
    display_order = db.Column(db.Integer, nullable=False)
    create_date = db.Column(db.DateTime, nullable=False, default=datetime.now)
    creator = db.Column(db.Integer, nullable=False)
    update_date = db.Column(db.DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)
    modifier = db.Column(db.Integer, nullable=False)
    delete_flag = db.Column(db.Boolean, nullable=False, default=False)

    def __init__(self, **kwargs):
        kwargs.setdefault('delete_flag', False)
        super().__init__(**kwargs)


class DashboardGadgetMaster(db.Model):
    """ダッシュボードガジェットマスタ"""
    __tablename__ = 'dashboard_gadget_master'

    gadget_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    gadget_uuid = db.Column(db.String(36), nullable=False)
    gadget_name = db.Column(db.String(20), nullable=False)
    dashboard_group_id = db.Column(db.Integer, db.ForeignKey('dashboard_group_master.dashboard_group_id'), nullable=False)
    gadget_type_id = db.Column(db.Integer, db.ForeignKey('gadget_type_master.gadget_type_id'), nullable=False)
    chart_config = db.Column(db.JSON, nullable=False)
    data_source_config = db.Column(db.JSON, nullable=False)
    position_x = db.Column(db.Integer, nullable=False)
    position_y = db.Column(db.Integer, nullable=False)
    gadget_size = db.Column(db.Integer, nullable=False)
    display_order = db.Column(db.Integer, nullable=False)
    create_date = db.Column(db.DateTime, nullable=False, default=datetime.now)
    creator = db.Column(db.Integer, nullable=False)
    update_date = db.Column(db.DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)
    modifier = db.Column(db.Integer, nullable=False)
    delete_flag = db.Column(db.Boolean, nullable=False, default=False)

    def __init__(self, **kwargs):
        kwargs.setdefault('delete_flag', False)
        super().__init__(**kwargs)


class GadgetTypeMaster(db.Model):
    """ガジェット種別マスタ"""
    __tablename__ = 'gadget_type_master'

    gadget_type_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    gadget_type_name = db.Column(db.String(20), nullable=False)
    data_source_type = db.Column(db.Integer, nullable=False)
    gadget_image_path = db.Column(db.String(100), nullable=False)
    gadget_description = db.Column(db.String(500), nullable=False)
    display_order = db.Column(db.Integer, nullable=False)
    create_date = db.Column(db.DateTime, nullable=False, default=datetime.now)
    creator = db.Column(db.Integer, nullable=False)
    update_date = db.Column(db.DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)
    modifier = db.Column(db.Integer, nullable=False)
    delete_flag = db.Column(db.Boolean, nullable=False, default=False)

    def __init__(self, **kwargs):
        kwargs.setdefault('delete_flag', False)
        super().__init__(**kwargs)


class DashboardUserSetting(db.Model):
    """ダッシュボードユーザー設定"""
    __tablename__ = 'dashboard_user_setting'

    user_id = db.Column(db.Integer, primary_key=True)
    dashboard_id = db.Column(db.Integer, db.ForeignKey('dashboard_master.dashboard_id'), nullable=False)
    organization_id = db.Column(db.Integer, nullable=False)
    device_id = db.Column(db.Integer, nullable=False)
    create_date = db.Column(db.DateTime, nullable=False, default=datetime.now)
    creator = db.Column(db.Integer, nullable=False)
    update_date = db.Column(db.DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)
    modifier = db.Column(db.Integer, nullable=False)
    delete_flag = db.Column(db.Boolean, nullable=False, default=False)

    def __init__(self, **kwargs):
        kwargs.setdefault('delete_flag', False)
        super().__init__(**kwargs)
