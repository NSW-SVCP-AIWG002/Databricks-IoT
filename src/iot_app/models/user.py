from iot_app import db


class User(db.Model):
    __tablename__ = 'user_master'

    user_id                 = db.Column(db.Integer,      primary_key=True)
    databricks_user_id      = db.Column(db.String(36),   nullable=False)
    user_name               = db.Column(db.String(20),   nullable=False)
    organization_id         = db.Column(db.Integer,      nullable=False)
    email_address           = db.Column(db.String(254),  nullable=False)
    user_type_id            = db.Column(db.Integer,      nullable=False)
    language_code           = db.Column(db.String(10),   nullable=False, default='ja')
    region_id               = db.Column(db.Integer,      nullable=False)
    address                 = db.Column(db.String(500),  nullable=False)
    status                  = db.Column(db.Integer,      nullable=False, default=1)
    alert_notification_flag = db.Column(db.Boolean,      nullable=False, default=True)
    system_notification_flag= db.Column(db.Boolean,      nullable=False, default=True)
    create_date             = db.Column(db.DateTime,     nullable=False)
    creator                 = db.Column(db.Integer,      nullable=False)
    update_date             = db.Column(db.DateTime,     nullable=False)
    modifier                = db.Column(db.Integer,      nullable=False)
    delete_flag             = db.Column(db.Boolean,      nullable=False, default=False)
