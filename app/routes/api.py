from flask import Blueprint, jsonify, session
from models.file1 import ParkingLot, ParkingSpot, Reservation, User
from datetime import datetime, timedelta
from sqlalchemy import func
from functools import wraps

api = Blueprint('api', __name__)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'Authentication required'}), 401
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'role' not in session or session['role'] != 'admin':
            return jsonify({'error': 'Admin access required'}), 403
        return f(*args, **kwargs)
    return decorated_function

@api.route('/api/parking_lots')
@login_required
def get_parking_lots():
    lots = ParkingLot.query.all()
    return jsonify({
        'lots': [{
            'id': lot.id,
            'name': lot.prime_location_name,
            'location': lot.address,
            'total_spots': lot.maximum_number_of_spots,
            'available_spots': lot.available_spots,
            'rate_per_hour': lot.price,
            'is_active': True  # You might want to add this field to your model
        } for lot in lots]
    })

@api.route('/api/user_reservations')
@login_required
def get_user_reservations():
    user_id = session['user_id']
    active_reservations = Reservation.query.filter_by(
        user_id=user_id,
        leaving_timestamp=None
    ).all()
    
    past_reservations = Reservation.query.filter(
        Reservation.user_id == user_id,
        Reservation.leaving_timestamp != None
    ).order_by(Reservation.leaving_timestamp.desc()).all()
    
    return jsonify({
        'active_reservations': [{
            'id': res.id,
            'lot_name': res.spot.lot.prime_location_name,
            'start_time': res.parking_timestamp.isoformat(),
            'duration': None,  # Will be calculated when completed
            'cost': None,      # Will be calculated when completed
            'status': 'active'
        } for res in active_reservations],
        'past_reservations': [{
            'id': res.id,
            'lot_name': res.spot.lot.prime_location_name,
            'start_time': res.parking_timestamp.isoformat(),
            'end_time': res.leaving_timestamp.isoformat(),
            'duration': res.duration,
            'cost': res.parking_cost,
            'status': 'completed'
        } for res in past_reservations]
    })

@api.route('/api/admin/dashboard_data')
@admin_required
def get_admin_dashboard_data():
    # Get occupancy data for the last 7 days
    last_week = datetime.utcnow() - timedelta(days=7)
    occupancy_data = []
    occupancy_labels = []
    
    for i in range(7):
        date = last_week + timedelta(days=i)
        total_spots = ParkingSpot.query.count()
        occupied_spots = ParkingSpot.query.filter(
            ParkingSpot.status == 'occupied',
            func.date(ParkingSpot.reservations.any().parking_timestamp) == date.date()
        ).count()
        
        occupancy_rate = (occupied_spots / total_spots * 100) if total_spots > 0 else 0
        occupancy_data.append(round(occupancy_rate, 2))
        occupancy_labels.append(date.strftime('%Y-%m-%d'))

    # Get revenue data by lot
    lots = ParkingLot.query.all()
    revenue_data = []
    revenue_labels = []
    
    for lot in lots:
        total_revenue = sum(
            res.parking_cost or 0
            for spot in lot.spots
            for res in spot.reservations
            if res.leaving_timestamp is not None
        )
        revenue_data.append(round(total_revenue, 2))
        revenue_labels.append(lot.prime_location_name)

    # Get peak hours data
    peak_hours_data = []
    peak_hours_labels = []
    
    for hour in range(24):
        occupied_spots = ParkingSpot.query.filter(
            ParkingSpot.status == 'occupied',
            func.extract('hour', ParkingSpot.reservations.any().parking_timestamp) == hour
        ).count()
        total_spots = ParkingSpot.query.count()
        occupancy_rate = (occupied_spots / total_spots * 100) if total_spots > 0 else 0
        peak_hours_data.append(round(occupancy_rate, 2))
        peak_hours_labels.append(f'{hour:02d}:00')

    # Get duration distribution
    duration_ranges = ['0-1h', '1-2h', '2-4h', '4-8h', '8h+']
    duration_data = []
    
    for i, range_str in enumerate(duration_ranges):
        if i == 0:
            count = Reservation.query.filter(
                Reservation.leaving_timestamp != None,
                Reservation.duration <= 1
            ).count()
        elif i == 1:
            count = Reservation.query.filter(
                Reservation.leaving_timestamp != None,
                Reservation.duration > 1,
                Reservation.duration <= 2
            ).count()
        elif i == 2:
            count = Reservation.query.filter(
                Reservation.leaving_timestamp != None,
                Reservation.duration > 2,
                Reservation.duration <= 4
            ).count()
        elif i == 3:
            count = Reservation.query.filter(
                Reservation.leaving_timestamp != None,
                Reservation.duration > 4,
                Reservation.duration <= 8
            ).count()
        else:
            count = Reservation.query.filter(
                Reservation.leaving_timestamp != None,
                Reservation.duration > 8
            ).count()
        
        total_reservations = Reservation.query.filter(
            Reservation.leaving_timestamp != None
        ).count()
        
        percentage = (count / total_reservations * 100) if total_reservations > 0 else 0
        duration_data.append(round(percentage, 2))

    return jsonify({
        'occupancy_labels': occupancy_labels,
        'occupancy_data': occupancy_data,
        'revenue_labels': revenue_labels,
        'revenue_data': revenue_data,
        'peak_hours_labels': peak_hours_labels,
        'peak_hours_data': peak_hours_data,
        'duration_labels': duration_ranges,
        'duration_data': duration_data
    })

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
                Reservation.duration <= 1
            ).count()
        elif i == 1:
            count = Reservation.query.filter(
                Reservation.user_id == user_id,
                Reservation.leaving_timestamp != None,
                Reservation.duration > 1,
                Reservation.duration <= 2
            ).count()
        elif i == 2:
            count = Reservation.query.filter(
                Reservation.user_id == user_id,
                Reservation.leaving_timestamp != None,
                Reservation.duration > 2,
                Reservation.duration <= 4
            ).count()
        elif i == 3:
            count = Reservation.query.filter(
                Reservation.user_id == user_id,
                Reservation.leaving_timestamp != None,
                Reservation.duration > 4,
                Reservation.duration <= 8
            ).count()
        else:
            count = Reservation.query.filter(
                Reservation.user_id == user_id,
                Reservation.leaving_timestamp != None,
                Reservation.duration > 8
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

    # Get parking frequency by day
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    frequency_data = []
    
    for i, day in enumerate(days):
        count = Reservation.query.filter(
            Reservation.user_id == user_id,
            func.extract('dow', Reservation.parking_timestamp) == i
        ).count()
        frequency_data.append(count)

    # Get preferred parking times
    preferred_times_data = []
    preferred_times_labels = []
    
    for hour in range(24):
        count = Reservation.query.filter(
            Reservation.user_id == user_id,
            func.extract('hour', Reservation.parking_timestamp) == hour
        ).count()
        preferred_times_data.append(count)
        preferred_times_labels.append(f'{hour:02d}:00')

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