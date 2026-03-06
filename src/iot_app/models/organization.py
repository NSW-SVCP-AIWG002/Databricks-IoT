from iot_app import db


class OrganizationMaster(db.Model):
    __tablename__ = "organization_master"

    organization_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    organization_name = db.Column(db.String(255), nullable=False)
    delete_flag = db.Column(db.Boolean, default=False, nullable=False)


class OrganizationClosure(db.Model):
    __tablename__ = "organization_closure"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    parent_organization_id = db.Column(
        db.Integer,
        db.ForeignKey("organization_master.organization_id"),
        nullable=False,
    )
    subsidiary_organization_id = db.Column(
        db.Integer,
        db.ForeignKey("organization_master.organization_id"),
        nullable=False,
    )
