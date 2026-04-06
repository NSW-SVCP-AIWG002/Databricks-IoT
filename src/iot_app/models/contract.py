from iot_app import db


class ContractStatusMaster(db.Model):
    __tablename__ = "contract_status_master"

    contract_status_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    contract_status_name = db.Column(db.String(20), nullable=False)
    create_date = db.Column(db.DateTime, nullable=False, server_default=db.func.now())
    creator = db.Column(db.Integer, nullable=False)
    update_date = db.Column(db.DateTime, nullable=False, server_default=db.func.now())
    modifier = db.Column(db.Integer, nullable=False)
    delete_flag = db.Column(db.Boolean, default=False, nullable=False)
