from src import db


class Language(db.Model):
    __tablename__ = 'language_master'

    language_code = db.Column(db.String(10), primary_key=True, nullable=False)
    language_name = db.Column(db.String(50), nullable=False)
    default_flag = db.Column(db.Boolean, nullable=False)
    display_order = db.Column(db.Integer, nullable=False)
    create_date = db.Column(db.DateTime, nullable=False, server_default=db.func.current_timestamp())
    creator = db.Column(db.Integer, nullable=False)
    update_date = db.Column(db.DateTime, nullable=False, server_default=db.func.current_timestamp())
    modifier = db.Column(db.Integer, nullable=False)
    delete_flag = db.Column(db.Boolean, nullable=False, default=False)
