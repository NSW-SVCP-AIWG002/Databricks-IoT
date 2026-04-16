from datetime import datetime

from iot_app import db


class MailTypeMaster(db.Model):
    """メール種別マスタ"""
    __tablename__ = 'mail_type_master'

    mail_type_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    mail_type_name = db.Column(db.String(50), nullable=False)
    delete_flag = db.Column(db.Boolean, nullable=False, default=False)
    create_date = db.Column(db.DateTime, nullable=False, default=datetime.now)
    creator = db.Column(db.Integer, nullable=False)
    update_date = db.Column(db.DateTime, nullable=True)
    modifier = db.Column(db.Integer, nullable=True)


class MailHistory(db.Model):
    """メール送信履歴"""
    __tablename__ = 'mail_history'

    mail_history_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    mail_history_uuid = db.Column(db.String(36), nullable=False, unique=True)
    mail_type = db.Column(
        db.Integer,
        db.ForeignKey('mail_type_master.mail_type_id'),
        nullable=False,
    )
    sender_email = db.Column(db.String(254), nullable=False)
    recipients = db.Column(db.JSON, nullable=False)
    subject = db.Column(db.String(500), nullable=False)
    body = db.Column(db.Text, nullable=False)
    sent_at = db.Column(db.DateTime, nullable=False)
    user_id = db.Column(db.Integer, nullable=True)
    organization_id = db.Column(db.Integer, nullable=True)
    create_date = db.Column(db.DateTime, nullable=False, default=datetime.now)
    creator = db.Column(db.Integer, nullable=False)
    update_date = db.Column(db.DateTime, nullable=True)
    modifier = db.Column(db.Integer, nullable=True)
