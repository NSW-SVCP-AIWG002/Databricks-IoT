from src import db


class MeasurementItem(db.Model):
    __tablename__ = 'measurement_item_master'

    measurement_item_id = db.Column(db.Integer, primary_key=True, autoincrement=True, nullable=False)
    measurement_item_name = db.Column(db.String(50), nullable=False)
    create_date = db.Column(db.DateTime, nullable=False, server_default=db.func.current_timestamp())
    creator = db.Column(db.Integer, nullable=False)
    update_date = db.Column(db.DateTime, nullable=False, server_default=db.func.current_timestamp())
    modifier = db.Column(db.Integer, nullable=False)
    delete_flag = db.Column(db.Boolean, nullable=False, default=False)
