from src import db


class MailType(db.Model):
    __tablename__ = 'mail_type_master'

    mail_type_id = db.Column(db.Integer, primary_key=True, nullable=False)
    mail_type_name = db.Column(db.String(50), nullable=False)
    delete_flag = db.Column(db.SmallInteger, nullable=False, default=0)
    create_date = db.Column(db.DateTime, nullable=False, server_default=db.func.current_timestamp())
    update_date = db.Column(db.DateTime, nullable=True, server_default=db.func.current_timestamp())


class MailHistory(db.Model):
    __tablename__ = 'mail_history'

    mail_history_id = db.Column(db.Integer, primary_key=True, nullable=False)
    mail_history_uuid = db.Column(db.String(32), nullable=False, unique=True)
    mail_type = db.Column(db.Integer, db.ForeignKey('mail_type_master.mail_type_id'), nullable=False)
    sender_email = db.Column(db.String(254), nullable=False)
    recipients = db.Column(db.JSON, nullable=False)
    subject = db.Column(db.String(500), nullable=False)
    body = db.Column(db.Text, nullable=False)
    sent_at = db.Column(db.DateTime, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user_master.user_id'), nullable=True)
    organization_id = db.Column(db.Integer, db.ForeignKey('organization_master.organization_id'), nullable=True)
    create_date = db.Column(db.DateTime, nullable=False, server_default=db.func.current_timestamp())
    creator = db.Column(db.Integer, nullable=False)
    update_date = db.Column(db.DateTime, nullable=True, server_default=db.func.current_timestamp())
    modifier = db.Column(db.Integer, nullable=True)

    mail_type_rel = db.relationship('MailType', backref='mail_histories')
    user = db.relationship('User', backref='mail_histories')
    organization = db.relationship('Organization', backref='mail_histories')
