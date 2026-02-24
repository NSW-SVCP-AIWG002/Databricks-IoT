from src import db


class OrganizationType(db.Model):
    __tablename__ = 'organization_type_master'

    organization_type_id = db.Column(db.Integer, primary_key=True, nullable=False)
    organization_type_name = db.Column(db.String(50), nullable=False)
    create_date = db.Column(db.DateTime, nullable=False, server_default=db.func.current_timestamp())
    creator = db.Column(db.Integer, nullable=False)
    update_date = db.Column(db.DateTime, nullable=False, server_default=db.func.current_timestamp())
    modifier = db.Column(db.Integer, nullable=False)
    delete_flag = db.Column(db.Boolean, nullable=False, default=False)


class Organization(db.Model):
    __tablename__ = 'organization_master'

    organization_id = db.Column(db.Integer, primary_key=True, nullable=False)
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
    create_date = db.Column(db.DateTime, nullable=False, server_default=db.func.current_timestamp())
    creator = db.Column(db.Integer, nullable=False)
    update_date = db.Column(db.DateTime, nullable=False, server_default=db.func.current_timestamp())
    modifier = db.Column(db.Integer, nullable=False)
    delete_flag = db.Column(db.Boolean, nullable=False, default=False)

    organization_type = db.relationship('OrganizationType', backref='organizations')
    contract_status = db.relationship('ContractStatus', backref='organizations')


class OrganizationClosure(db.Model):
    __tablename__ = 'organization_closure'

    parent_organization_id = db.Column(db.Integer, db.ForeignKey('organization_master.organization_id'), primary_key=True, nullable=False)
    subsidiary_organization_id = db.Column(db.Integer, db.ForeignKey('organization_master.organization_id'), primary_key=True, nullable=False)
    depth = db.Column(db.Integer, nullable=False, default=0)

    parent_organization = db.relationship('Organization', foreign_keys=[parent_organization_id], backref='child_closures')
    subsidiary_organization = db.relationship('Organization', foreign_keys=[subsidiary_organization_id], backref='parent_closures')
