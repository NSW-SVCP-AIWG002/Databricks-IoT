from src import db


class UserType(db.Model):
    __tablename__ = 'user_type_master'

    user_type_id = db.Column(db.Integer, primary_key=True, nullable=False)
    user_type_name = db.Column(db.String(20), nullable=False)
    create_date = db.Column(db.DateTime, nullable=False, server_default=db.func.current_timestamp())
    creator = db.Column(db.Integer, nullable=False)
    update_date = db.Column(db.DateTime, nullable=False, server_default=db.func.current_timestamp())
    modifier = db.Column(db.Integer, nullable=False)
    delete_flag = db.Column(db.Boolean, nullable=False, default=False)


class User(db.Model):
    __tablename__ = 'user_master'

    user_id = db.Column(db.Integer, primary_key=True, nullable=False)
    databricks_user_id = db.Column(db.String(36), nullable=False)
    user_name = db.Column(db.String(20), nullable=False)
    organization_id = db.Column(db.Integer, db.ForeignKey('organization_master.organization_id'), nullable=False)
    email_address = db.Column(db.String(254), nullable=False, unique=True)
    user_type_id = db.Column(db.Integer, db.ForeignKey('user_type_master.user_type_id'), nullable=False)
    language_code = db.Column(db.String(10), db.ForeignKey('language_master.language_code'), nullable=False, default='ja')
    region_id = db.Column(db.Integer, db.ForeignKey('region_master.region_id'), nullable=False)
    address = db.Column(db.String(500), nullable=False)
    status = db.Column(db.Integer, nullable=False, default=1)
    alert_notification_flag = db.Column(db.Boolean, nullable=False, default=True)
    system_notification_flag = db.Column(db.Boolean, nullable=False, default=True)
    create_date = db.Column(db.DateTime, nullable=False, server_default=db.func.current_timestamp())
    creator = db.Column(db.Integer, nullable=False)
    update_date = db.Column(db.DateTime, nullable=False, server_default=db.func.current_timestamp())
    modifier = db.Column(db.Integer, nullable=False)
    delete_flag = db.Column(db.Boolean, nullable=False, default=False)

    organization = db.relationship('Organization', backref='users')
    user_type = db.relationship('UserType', backref='users')
    language = db.relationship('Language', backref='users')
    region = db.relationship('Region', backref='users')
