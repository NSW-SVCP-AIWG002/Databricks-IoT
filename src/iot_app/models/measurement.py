from datetime import datetime

from iot_app import db


class SilverSensorData(db.Model):
    __tablename__ = "silver_sensor_data"

    device_id                        = db.Column(db.Integer, primary_key=True, nullable=False)
    organization_id                  = db.Column(db.Integer, primary_key=True, nullable=False)
    event_timestamp                  = db.Column(db.DateTime, primary_key=True, nullable=False)
    event_date                       = db.Column(db.Date, nullable=False)
    external_temp                    = db.Column(db.Float, nullable=True)
    set_temp_freezer_1               = db.Column(db.Float, nullable=True)
    internal_sensor_temp_freezer_1   = db.Column(db.Float, nullable=True)
    internal_temp_freezer_1          = db.Column(db.Float, nullable=True)
    df_temp_freezer_1                = db.Column(db.Float, nullable=True)
    condensing_temp_freezer_1        = db.Column(db.Float, nullable=True)
    adjusted_internal_temp_freezer_1 = db.Column(db.Float, nullable=True)
    set_temp_freezer_2               = db.Column(db.Float, nullable=True)
    internal_sensor_temp_freezer_2   = db.Column(db.Float, nullable=True)
    internal_temp_freezer_2          = db.Column(db.Float, nullable=True)
    df_temp_freezer_2                = db.Column(db.Float, nullable=True)
    condensing_temp_freezer_2        = db.Column(db.Float, nullable=True)
    adjusted_internal_temp_freezer_2 = db.Column(db.Float, nullable=True)
    compressor_freezer_1             = db.Column(db.Float, nullable=True)
    compressor_freezer_2             = db.Column(db.Float, nullable=True)
    fan_motor_1                      = db.Column(db.Float, nullable=True)
    fan_motor_2                      = db.Column(db.Float, nullable=True)
    fan_motor_3                      = db.Column(db.Float, nullable=True)
    fan_motor_4                      = db.Column(db.Float, nullable=True)
    fan_motor_5                      = db.Column(db.Float, nullable=True)
    defrost_heater_output_1          = db.Column(db.Float, nullable=True)
    defrost_heater_output_2          = db.Column(db.Float, nullable=True)
    create_time                      = db.Column(db.DateTime, nullable=False, server_default=db.func.now())


class MeasurementItemMaster(db.Model):
    """測定項目マスタ"""
    __tablename__ = 'measurement_item_master'

    measurement_item_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    measurement_item_name = db.Column(db.String(50), nullable=False)
    silver_data_column_name = db.Column(db.String(50), nullable=False)
    display_name = db.Column(db.String(50), nullable=False)
    unit_name = db.Column(db.String(10), nullable=False)
    create_date = db.Column(db.DateTime, nullable=False, default=datetime.now)
    creator = db.Column(db.Integer, nullable=False)
    update_date = db.Column(db.DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)
    modifier = db.Column(db.Integer, nullable=False)
    delete_flag = db.Column(db.Boolean, nullable=False, default=False)

    def __init__(self, **kwargs):
        kwargs.setdefault('delete_flag', False)
        super().__init__(**kwargs)
