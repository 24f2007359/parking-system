from flask import Blueprint, jsonify, session
from functools import wraps
from datetime import datetime
from sqlalchemy import func
from models.file1 import User, Reservation, ParkingLot, ParkingSpot

# Create blueprint
api = Blueprint('api', __name__)

# Login required decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'Unauthorized'}), 401
        return f(*args, **kwargs)
    return decorated_function

@api.route('/api/user/dashboard_data')
@login_required
def get_user_dashboard_data():
    user_id = session['user_id']
    
    # Get duration distribution
    duration_ranges = ['0-1h', '1-2h', '2-4h', '4-8h', '8h+']
    duration_data = []
    
    for i, range_str in enumerate(duration_ranges):
        if i == 0:
            count = Reservation.query.filter(
                Reservation.user_id == user_id,
                Reservation.leaving_timestamp != None,
                func.extract('epoch', Reservation.leaving_timestamp - Reservation.parking_timestamp) / 3600 <= 1
            ).count()
        elif i == 1:
            count = Reservation.query.filter(
                Reservation.user_id == user_id,
                Reservation.leaving_timestamp != None,
                func.extract('epoch', Reservation.leaving_timestamp - Reservation.parking_timestamp) / 3600 > 1,
                func.extract('epoch', Reservation.leaving_timestamp - Reservation.parking_timestamp) / 3600 <= 2
            ).count()
        elif i == 2:
            count = Reservation.query.filter(
                Reservation.user_id == user_id,
                Reservation.leaving_timestamp != None,
                func.extract('epoch', Reservation.leaving_timestamp - Reservation.parking_timestamp) / 3600 > 2,
                func.extract('epoch', Reservation.leaving_timestamp - Reservation.parking_timestamp) / 3600 <= 4
            ).count()
        elif i == 3:
            count = Reservation.query.filter(
                Reservation.user_id == user_id,
                Reservation.leaving_timestamp != None,
                func.extract('epoch', Reservation.leaving_timestamp - Reservation.parking_timestamp) / 3600 > 4,
                func.extract('epoch', Reservation.leaving_timestamp - Reservation.parking_timestamp) / 3600 <= 8
            ).count()
        else:
            count = Reservation.query.filter(
                Reservation.user_id == user_id,
                Reservation.leaving_timestamp != None,
                func.extract('epoch', Reservation.leaving_timestamp - Reservation.parking_timestamp) / 3600 > 8
            ).count()
        
        total_reservations = Reservation.query.filter(
            Reservation.user_id == user_id,
            Reservation.leaving_timestamp != None
        ).count()
        
        percentage = (count / total_reservations * 100) if total_reservations > 0 else 0
        duration_data.append(round(percentage, 2))

    # Get monthly expenses
    last_6_months = []
    expenses_data = []
    expenses_labels = []
    
    for i in range(6):
        month = datetime.utcnow().month - i
        year = datetime.utcnow().year
        if month <= 0:
            month += 12
            year -= 1
            
        total_expense = sum(
            res.parking_cost or 0
            for res in Reservation.query.filter(
                Reservation.user_id == user_id,
                Reservation.leaving_timestamp != None,
                func.extract('month', Reservation.leaving_timestamp) == month,
                func.extract('year', Reservation.leaving_timestamp) == year
            ).all()
        )
        
        expenses_data.append(round(total_expense, 2))
        expenses_labels.append(f'{year}-{month:02d}')

    # Get parking frequency by day - using SQLite compatible approach
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    frequency_data = [0, 0, 0, 0, 0, 0, 0]  # Initialize with zeros
    
    # Get all reservations for this user
    user_reservations = Reservation.query.filter_by(user_id=user_id).all()
    
    # Count frequency for each day
    for reservation in user_reservations:
        day_index = reservation.parking_timestamp.weekday()
        frequency_data[day_index] += 1

    # Get preferred parking times - using more compatible approach
    preferred_times_data = [0] * 24  # Initialize with zeros
    preferred_times_labels = [f'{hour:02d}:00' for hour in range(24)]
    
    # Count frequency for each hour
    for reservation in user_reservations:
        hour = reservation.parking_timestamp.hour
        preferred_times_data[hour] += 1

    return jsonify({
        'duration_labels': duration_ranges,
        'duration_data': duration_data,
        'expenses_labels': expenses_labels,
        'expenses_data': expenses_data,
        'frequency_labels': days,
        'frequency_data': frequency_data,
        'preferred_times_labels': preferred_times_labels,
        'preferred_times_data': preferred_times_data
    }) 