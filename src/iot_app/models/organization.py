from datetime import datetime

from iot_app import db


class OrganizationTypeMaster(db.Model):
    """組織種別マスタ"""
    __tablename__ = 'organization_type_master'

    organization_type_id = db.Column(db.Integer, primary_key=True)
    organization_type_name = db.Column(db.String(50), nullable=False)
    create_date = db.Column(db.DateTime, nullable=False, default=datetime.now)
    creator = db.Column(db.Integer, nullable=False)
    update_date = db.Column(db.DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)
    modifier = db.Column(db.Integer, nullable=False)
    delete_flag = db.Column(db.Boolean, nullable=False, default=False)


class OrganizationMaster(db.Model):
    """組織マスタ"""
    __tablename__ = 'organization_master'

    organization_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    organization_name = db.Column(db.String(200), nullable=False)
    organization_type_id = db.Column(db.Integer, db.ForeignKey('organization_type_master.organization_type_id'), nullable=False)
    address = db.Column(db.String(500), nullable=False)
    phone_number = db.Column(db.String(20), nullable=False)
    fax_number = db.Column(db.String(20), nullable=True)
    contact_person = db.Column(db.String(20), nullable=False)
    contract_status_id = db.Column(db.Integer, db.ForeignKey('contract_status_master.contract_status_id'), nullable=False)
    contract_start_date = db.Column(db.Date, nullable=False)
    contract_end_date = db.Column(db.Date, nullable=True)
    databricks_group_id = db.Column(db.String(20), nullable=False)
    create_date = db.Column(db.DateTime, nullable=False, default=datetime.now)
    creator = db.Column(db.Integer, nullable=False)
    update_date = db.Column(db.DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)
    modifier = db.Column(db.Integer, nullable=False)
    delete_flag = db.Column(db.Boolean, nullable=False, default=False)

    def __init__(self, **kwargs):
        kwargs.setdefault('delete_flag', False)
        super().__init__(**kwargs)


class OrganizationClosure(db.Model):
    """組織閉包テーブル"""
    __tablename__ = 'organization_closure'

    parent_organization_id = db.Column(db.Integer, db.ForeignKey('organization_master.organization_id'), primary_key=True, nullable=False)
    subsidiary_organization_id = db.Column(db.Integer, db.ForeignKey('organization_master.organization_id'), primary_key=True, nullable=False)
    depth = db.Column(db.Integer, nullable=False, default=0)


class OrganizationMasterByUser(db.Model):
    """組織マスタ（ユーザースコープ制限ビュー）"""
    __tablename__ = 'v_organization_master_by_user'

    user_id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.Integer, primary_key=True)
    organization_name = db.Column(db.String(200), nullable=False)
    delete_flag = db.Column(db.Boolean, nullable=False, default=False)

    def __init__(self, **kwargs):
        kwargs.setdefault('delete_flag', False)
        super().__init__(**kwargs)
