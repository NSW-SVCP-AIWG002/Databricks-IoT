from src import db


class SortItem(db.Model):
    __tablename__ = 'sort_item_master'

    view_id = db.Column(db.Integer, primary_key=True, nullable=False)
    sort_item_id = db.Column(db.Integer, primary_key=True, nullable=False)
    sort_item_name = db.Column(db.String(100), nullable=False)
    sort_order = db.Column(db.Integer, nullable=False)
    delete_flag = db.Column(db.Boolean, nullable=False, default=False)
    create_date = db.Column(db.DateTime, nullable=False, server_default=db.func.current_timestamp())
    update_date = db.Column(db.DateTime, nullable=False, server_default=db.func.current_timestamp())
