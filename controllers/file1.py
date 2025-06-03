from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from models.file1 import User, ParkingLot, ParkingSpot, Reservation, db
from functools import wraps
from datetime import datetime
import re

auth = Blueprint('auth', __name__)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'error')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        role = request.form.get('role', 'user')  # Default to 'user' if not specified
        
        # Check for regular user login
        user = User.query.filter_by(email=email, role=role).first()
        if user and user.check_password(password):
            session['user_id'] = user.id
            session['username'] = user.username
            session['role'] = user.role
            flash('Login successful!', 'success')
            return redirect(url_for('main.home'))
        
        flash('Invalid email, password, or role.', 'error')
    return render_template('login.html')

@auth.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        role = request.form.get('role', 'user')  # Default to 'user' if not specified
        
        # Validate input
        if not username or not email or not password:
            flash('All fields are required.', 'error')
            return render_template('register.html')
        
        if password != confirm_password:
            flash('Passwords do not match.', 'error')
            return render_template('register.html')
        
        # Check if username or email already exists
        if User.query.filter_by(username=username).first():
            flash('Username already exists.', 'error')
            return render_template('register.html')
        
        if User.query.filter_by(email=email).first():
            flash('Email already exists.', 'error')
            return render_template('register.html')
        
        # Create new user
        try:
            new_user = User(username=username, email=email, role=role)
            new_user.set_password(password)
            db.session.add(new_user)
            db.session.commit()
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('auth.login'))
        except Exception as e:
            db.session.rollback()
            flash('An error occurred during registration.', 'error')
            return render_template('register.html')
    
    return render_template('register.html')

@auth.route('/user/dashboard/book', methods=['POST'])
@login_required
def book_spot():
    lot_id = request.form.get('lot_id')
    if not lot_id:
        flash('No lot selected.', 'error')
        return redirect(url_for('auth.user_dashboard'))
    
    try:
        # Get form data
        user_name = request.form.get('user_name')
        user_phone = request.form.get('user_phone')
        vehicle_type = request.form.get('vehicle_type')
        vehicle_number = request.form.get('vehicle_number')
        vehicle_model = request.form.get('vehicle_model')
        vehicle_color = request.form.get('vehicle_color')
        driver_name = request.form.get('driver_name')
        parking_timestamp = request.form.get('parking_timestamp')
        
        # Validate required fields
        required_fields = {
            'user_name': user_name,
            'vehicle_type': vehicle_type,
            'vehicle_number': vehicle_number,
            'vehicle_model': vehicle_model,
            'vehicle_color': vehicle_color,
            'driver_name': driver_name,
            'parking_timestamp': parking_timestamp
        }
        
        missing_fields = [field for field, value in required_fields.items() if not value]
        if missing_fields:
            flash(f'Please fill in all required fields: {", ".join(missing_fields)}', 'error')
            return redirect(url_for('auth.user_dashboard'))
        
        # Validate vehicle number format
        if not re.match(r'^[A-Z0-9]{2,3}[A-Z]{1,2}[0-9]{4}$', vehicle_number):
            flash('Please enter a valid vehicle number (e.g., KA01AB1234)', 'error')
            return redirect(url_for('auth.user_dashboard'))
        
        # Validate phone number if provided
        if user_phone and not re.match(r'^[0-9]{10}$', user_phone):
            flash('Please enter a valid 10-digit phone number', 'error')
            return redirect(url_for('auth.user_dashboard'))
        
        lot = ParkingLot.query.get_or_404(int(lot_id))
        available_spot = ParkingSpot.query.filter_by(lot_id=lot.id, status='available').first()
        
        if not available_spot:
            flash('No available spots in this lot.', 'error')
            return redirect(url_for('auth.user_dashboard'))
        
        # Check if user already has an active reservation
        active_reservation = Reservation.query.filter_by(
            user_id=session['user_id'],
            leaving_timestamp=None
        ).first()
        
        if active_reservation:
            flash('You already have an active reservation.', 'error')
            return redirect(url_for('auth.user_dashboard'))
        
        # Parse parking timestamp
        try:
            parking_time = datetime.strptime(parking_timestamp, '%Y-%m-%dT%H:%M')
        except ValueError:
            flash('Invalid parking time format.', 'error')
            return redirect(url_for('auth.user_dashboard'))
        
        # Create new reservation with all details
        reservation = Reservation(
            spot_id=available_spot.id,
            user_id=session['user_id'],
            parking_timestamp=parking_time,
            user_name=user_name,
            user_phone=user_phone,
            vehicle_type=vehicle_type,
            vehicle_number=vehicle_number,
            vehicle_model=vehicle_model,
            vehicle_color=vehicle_color,
            driver_name=driver_name
        )
        
        # Update spot status
        available_spot.status = 'occupied'
        
        db.session.add(reservation)
        db.session.commit()
        
        flash('Spot reserved successfully!', 'success')
        return redirect(url_for('auth.user_dashboard'))
    except Exception as e:
        db.session.rollback()
        flash(f'Error reserving spot: {str(e)}', 'error')
        return redirect(url_for('auth.user_dashboard'))

@auth.route('/user/reservation/<int:reservation_id>/cancel', methods=['POST'])
@login_required
def cancel_reservation(reservation_id):
    try:
        # Get the reservation
        reservation = Reservation.query.get_or_404(reservation_id)
        
        # Check if reservation belongs to user
        if reservation.user_id != session['user_id']:
            return jsonify({
                'success': False,
                'message': 'You do not have permission to cancel this reservation.'
            }), 403
        
        # Check if reservation is already completed or cancelled
        if reservation.leaving_timestamp is not None:
            return jsonify({
                'success': False,
                'message': 'This reservation is already completed or cancelled.'
            }), 400
        
        # Cancel the reservation
        reservation.leaving_timestamp = datetime.now()
        reservation.parking_cost = 0  # No charge for cancelled reservations
        reservation.spot.status = 'available'  # Free up the spot
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Reservation cancelled successfully.'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Error cancelling reservation: {str(e)}'
        }), 500 