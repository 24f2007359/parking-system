from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from models.file1 import User, ParkingLot, ParkingSpot, Reservation, db
from functools import wraps
from datetime import datetime

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
        username = request.form.get('username')
        password = request.form.get('password')
        is_admin = request.form.get('is_admin') == 'on'
        
        if is_admin:
            # Check for admin login
            if username == 'admin' and password == 'admin123':
                session['user_id'] = 1  # Admin user ID
                session['username'] = 'admin'
                session['role'] = 'admin'
                flash('Welcome back, Admin!', 'success')
                return redirect(url_for('main.home'))
            else:
                flash('Invalid admin credentials.', 'error')
                return render_template('login.html')
        else:
            # Check for regular user login
            user = User.query.filter_by(username=username).first()
            if user and user.check_password(password):
                session['user_id'] = user.id
                session['username'] = user.username
                session['role'] = user.role
                flash('Login successful!', 'success')
                return redirect(url_for('main.home'))
            
            flash('Invalid username or password.', 'error')
    return render_template('login.html')

@auth.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        is_admin = request.form.get('is_admin') == 'on'
        
        # Validate input
        if not username or not password:
            flash('All fields are required.', 'error')
            return render_template('register.html')
        
        if password != confirm_password:
            flash('Passwords do not match.', 'error')
            return render_template('register.html')
        
        # Check if username already exists
        if User.query.filter_by(username=username).first():
            flash('Username already exists.', 'error')
            return render_template('register.html')
        
        # Create new user
        try:
            role = 'admin' if is_admin else 'user'
            new_user = User(username=username, role=role)
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

@auth.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'success')
    return redirect(url_for('auth.login'))

@auth.route('/user/dashboard')
@login_required
def user_dashboard():
    # Get user
    user = User.query.get(session['user_id'])
    
    # Get user's active reservations
    active_reservations_list = Reservation.query.filter_by(
        user_id=user.id,
        leaving_timestamp=None
    ).all()
    
    # Get user's reservation history
    reservation_history = Reservation.query.filter(
        Reservation.user_id == user.id,
        Reservation.leaving_timestamp != None
    ).order_by(Reservation.leaving_timestamp.desc()).all()
    
    # Calculate user stats
    total_hours = sum(r.duration for r in reservation_history if r.duration)
    total_spent = sum(r.parking_cost for r in reservation_history if r.parking_cost)
    loyalty_points = user.loyalty_points if hasattr(user, 'loyalty_points') else 0
    
    # Get available lots for new reservations
    available_lots = ParkingLot.query.filter_by(is_active=True).all()
    
    return render_template('user/dashboard.html',
                         active_reservations=len(active_reservations_list),
                         active_reservations_list=active_reservations_list,
                         reservation_history=reservation_history,
                         total_hours=total_hours,
                         total_spent=total_spent,
                         loyalty_points=loyalty_points,
                         available_lots=available_lots)

@auth.route('/user/dashboard/reserve', methods=['POST'])
@login_required
def dashboard_reserve():
    spot_id = request.form.get('spot_id')
    if not spot_id:
        flash('No spot selected.', 'error')
        return redirect(url_for('auth.user_dashboard'))
    return reserve_spot(int(spot_id))

@auth.route('/user/lot/<int:lot_id>/spots')
@login_required
def get_lot_spots(lot_id):
    try:
        lot = ParkingLot.query.get_or_404(lot_id)
        spots = ParkingSpot.query.filter_by(lot_id=lot_id).all()
        
        return jsonify({
            'success': True,
            'lot_name': lot.prime_location_name,
            'price_per_hour': lot.price,
            'spots': [{
                'id': spot.id,
                'status': spot.status,
                'is_available': spot.is_available
            } for spot in spots]
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error fetching spots: {str(e)}'
        })

@auth.route('/user/reserve/<int:spot_id>', methods=['POST'])
@login_required
def reserve_spot(spot_id):
    try:
        spot = ParkingSpot.query.get_or_404(spot_id)
        
        # Check if spot is available
        if not spot.is_available:
            return jsonify({
                'success': False,
                'message': 'This spot is no longer available.'
            })
        
        # Check if user already has an active reservation
        active_reservation = Reservation.query.filter_by(
            user_id=session['user_id'],
            leaving_timestamp=None
        ).first()
        
        if active_reservation:
            return jsonify({
                'success': False,
                'message': 'You already have an active reservation.'
            })
        
        # Create new reservation
        reservation = Reservation(
            spot_id=spot_id,
            user_id=session['user_id']
        )
        
        # Update spot status
        spot.status = 'occupied'
        
        db.session.add(reservation)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Spot reserved successfully.',
            'reservation_id': reservation.id
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Error reserving spot: {str(e)}'
        })

@auth.route('/user/reservation/<int:reservation_id>/complete', methods=['POST'])
@login_required
def complete_reservation(reservation_id):
    try:
        # First check if reservation exists
        reservation = Reservation.query.get(reservation_id)
        if not reservation:
            return jsonify({
                'success': False,
                'message': 'Reservation not found. It may have been deleted.'
            }), 404

        # Check if reservation belongs to user
        if reservation.user_id != session['user_id']:
            return jsonify({
                'success': False,
                'message': 'You do not have permission to complete this reservation.'
            }), 403

        # Check if reservation is already completed
        if not reservation.is_active:
            return jsonify({
                'success': False,
                'message': 'This reservation is already completed.'
            }), 400

        # Verify spot and lot still exist
        if not reservation.spot:
            return jsonify({
                'success': False,
                'message': 'The parking spot for this reservation no longer exists.'
            }), 400

        if not reservation.spot.lot:
            return jsonify({
                'success': False,
                'message': 'The parking lot for this reservation no longer exists.'
            }), 400

        # Verify lot is still active
        if not reservation.spot.lot.is_active:
            return jsonify({
                'success': False,
                'message': 'The parking lot for this reservation is no longer active.'
            }), 400

        try:
            # Complete the reservation
            reservation.complete_reservation()
            db.session.commit()
            return jsonify({
                'success': True,
                'message': 'Reservation completed successfully.',
                'cost': reservation.parking_cost,
                'duration': reservation.duration
            })
        except Exception as e:
            db.session.rollback()
            return jsonify({
                'success': False,
                'message': f'Error completing reservation: {str(e)}'
            }), 500

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'An unexpected error occurred: {str(e)}'
        }), 500

@auth.route('/user/dashboard/book', methods=['POST'])
@login_required
def book_spot():
    lot_id = request.form.get('lot_id')
    if not lot_id:
        flash('No lot selected.', 'error')
        return redirect(url_for('auth.user_dashboard'))
    
    try:
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
        
        # Create new reservation with check-in timestamp
        reservation = Reservation(
            spot_id=available_spot.id,
            user_id=session['user_id'],
            parking_timestamp=datetime.now(),
            vehicle_type=request.form.get('vehicle_type'),
            vehicle_number=request.form.get('vehicle_number'),
            driver_name=request.form.get('driver_name')
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

@auth.route('/reservation/<int:reservation_id>')
@login_required
def get_reservation(reservation_id):
    try:
        reservation = Reservation.query.get_or_404(reservation_id)
        
        # Check if reservation belongs to user
        if reservation.user_id != session['user_id'] and not session.get('role') == 'admin':
            return jsonify({'error': 'You do not have permission to view this reservation'}), 403
            
        # Calculate estimated cost if reservation is still active
        estimated_cost = None
        duration = None
        if reservation.is_active:
            # Get current time
            current_time = datetime.now()
            # Calculate duration in hours
            duration_seconds = (current_time - reservation.parking_timestamp).total_seconds()
            duration = round(duration_seconds / 3600, 2)
            # Calculate estimated cost
            estimated_cost = round(duration * reservation.spot.lot.price, 2)
        
        return jsonify({
            'id': reservation.id,
            'parking_timestamp': reservation.parking_timestamp.isoformat(),
            'leaving_timestamp': reservation.leaving_timestamp.isoformat() if reservation.leaving_timestamp else None,
            'duration': reservation.duration if reservation.leaving_timestamp else duration,
            'parking_cost': reservation.parking_cost if reservation.leaving_timestamp else estimated_cost,
            'is_active': reservation.is_active,
            'spot': {
                'id': reservation.spot.id,
                'status': reservation.spot.status,
                'lot': {
                    'id': reservation.spot.lot.id,
                    'prime_location_name': reservation.spot.lot.prime_location_name,
                    'price': reservation.spot.lot.price
                }
            }
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

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