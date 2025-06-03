from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Reservation(db.Model):
    __tablename__ = 'reservations'
    
    id = db.Column(db.Integer, primary_key=True)
    spot_id = db.Column(db.Integer, db.ForeignKey('parking_spots.id', ondelete='CASCADE'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    parking_timestamp = db.Column(db.DateTime, nullable=False, default=datetime.now)
    leaving_timestamp = db.Column(db.DateTime, nullable=True)
    duration = db.Column(db.Float, nullable=True)
    parking_cost = db.Column(db.Float, nullable=True)
    vehicle_type = db.Column(db.String(50), nullable=True)
    vehicle_number = db.Column(db.String(20), nullable=True)
    driver_name = db.Column(db.String(100), nullable=True)
    
    # User details
    user_name = db.Column(db.String(100), nullable=False)
    user_phone = db.Column(db.String(20), nullable=True)
    
    # Vehicle details
    vehicle_model = db.Column(db.String(50), nullable=False)
    vehicle_color = db.Column(db.String(30), nullable=False)
    
    def __init__(self, spot_id, user_id, parking_timestamp=None, user_name=None, user_phone=None,
                 vehicle_type=None, vehicle_number=None, vehicle_model=None, vehicle_color=None, driver_name=None):
        self.spot_id = spot_id
        self.user_id = user_id
        self.parking_timestamp = parking_timestamp or datetime.now()
        self.leaving_timestamp = None
        self.duration = None
        self.parking_cost = None
        self.vehicle_type = vehicle_type
        self.vehicle_number = vehicle_number
        self.vehicle_model = vehicle_model
        self.vehicle_color = vehicle_color
        self.driver_name = driver_name
        self.user_name = user_name
        self.user_phone = user_phone 