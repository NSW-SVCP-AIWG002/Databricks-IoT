from src import db


class Region(db.Model):
    __tablename__ = 'region_master'

    region_id = db.Column(db.Integer, primary_key=True, nullable=False)
    region_name = db.Column(db.String(50), nullable=False)
    time_zone = db.Column(db.String(64), nullable=False)
    delete_flag = db.Column(db.Boolean, nullable=False, default=False)
    create_date = db.Column(db.DateTime, nullable=False, server_default=db.func.current_timestamp())
    update_date = db.Column(db.DateTime, nullable=False, server_default=db.func.current_timestamp())
