from iot_app import db


class OrganizationTypeMaster(db.Model):
    __tablename__ = "organization_type_master"

    organization_type_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    organization_type_name = db.Column(db.String(50), nullable=False)
    create_date = db.Column(db.DateTime, nullable=False, server_default=db.func.now())
    creator = db.Column(db.Integer, nullable=False)
    update_date = db.Column(db.DateTime, nullable=False, server_default=db.func.now())
    modifier = db.Column(db.Integer, nullable=False)
    delete_flag = db.Column(db.Boolean, default=False, nullable=False)


class OrganizationMaster(db.Model):
    __tablename__ = "organization_master"

    organization_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    organization_name = db.Column(db.String(200), nullable=False)
    organization_type_id = db.Column(
        db.Integer,
        db.ForeignKey("organization_type_master.organization_type_id"),
        nullable=False,
    )
    address = db.Column(db.String(500), nullable=False)
    phone_number = db.Column(db.String(20), nullable=False)
    fax_number = db.Column(db.String(20), nullable=True)
    contact_person = db.Column(db.String(20), nullable=False)
    contract_status_id = db.Column(
        db.Integer,
        db.ForeignKey("contract_status_master.contract_status_id"),
        nullable=False,
    )
    contract_start_date = db.Column(db.Date, nullable=False)
    contract_end_date = db.Column(db.Date, nullable=True)
    databricks_group_id = db.Column(db.String(20), nullable=False)
    create_date = db.Column(db.DateTime, nullable=False, server_default=db.func.now())
    creator = db.Column(db.Integer, nullable=False)
    update_date = db.Column(db.DateTime, nullable=False, server_default=db.func.now())
    modifier = db.Column(db.Integer, nullable=False)
    delete_flag = db.Column(db.Boolean, default=False, nullable=False)


class OrganizationClosure(db.Model):
    __tablename__ = "organization_closure"

    parent_organization_id = db.Column(
        db.Integer,
        db.ForeignKey("organization_master.organization_id"),
        primary_key=True,
        nullable=False,
    )
    subsidiary_organization_id = db.Column(
        db.Integer,
        db.ForeignKey("organization_master.organization_id"),
        primary_key=True,
        nullable=False,
    )
    depth = db.Column(db.Integer, nullable=False, default=0)
