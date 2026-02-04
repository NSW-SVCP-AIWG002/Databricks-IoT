import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from config import Config

app = Flask(__name__)
app.config.from_object(Config)

db = SQLAlchemy(app)


class Device(db.Model):
    """Device model."""
    __tablename__ = "devices"

    id = db.Column(db.Integer, primary_key=True)
    device_name = db.Column(db.String(255), nullable=False)
    device_type = db.Column(db.String(100))
    status = db.Column(db.String(50), default="active")
    created_at = db.Column(db.DateTime, server_default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, server_default=db.func.current_timestamp(),
                           onupdate=db.func.current_timestamp())

    def to_dict(self):
        return {
            "id": self.id,
            "device_name": self.device_name,
            "device_type": self.device_type,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }


@app.route("/")
def index():
    return {"message": "Hello, Databricks-IoT!"}


@app.route("/health")
def health():
    return {"status": "healthy"}


@app.route("/api/devices", methods=["GET"])
def get_devices():
    """Get all devices."""
    devices = Device.query.all()
    return jsonify([device.to_dict() for device in devices])


@app.route("/api/devices/<int:device_id>", methods=["GET"])
def get_device(device_id):
    """Get a device by ID."""
    device = Device.query.get_or_404(device_id)
    return jsonify(device.to_dict())


if __name__ == "__main__":
    app.run(host=Config.FLASK_HOST, port=Config.FLASK_PORT, debug=True)
