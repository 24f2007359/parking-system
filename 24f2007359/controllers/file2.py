from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for, session
from models.file1 import User, ParkingLot, ParkingSpot, db, Reservation
from functools import wraps
import re
from datetime import datetime, timedelta
from sqlalchemy import func

admin = Blueprint('admin', __name__)

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'role' not in session or session['role'] != 'admin':
            flash('You do not have permission to access this page.', 'error')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

@admin.route('/dashboard')
@admin_required
def dashboard():
    # Get statistics
    total_lots = ParkingLot.query.count()
    available_spots = ParkingSpot.query.filter_by(status='available').count()
    total_revenue = db.session.query(func.sum(Reservation.parking_cost)).filter(
        Reservation.leaving_timestamp != None
    ).scalar() or 0
    active_users = User.query.filter_by(role='user').count()
    
    # Get all parking lots with their spots
    parking_lots = ParkingLot.query.all()

    # Get occupancy data for the last 7 days
    last_week = datetime.utcnow() - timedelta(days=7)
    occupancy_data = []
    occupancy_labels = []
    
    for i in range(7):
        date = last_week + timedelta(days=i)
        total_spots = ParkingSpot.query.count()
        occupied_spots = db.session.query(ParkingSpot).join(
            Reservation, ParkingSpot.id == Reservation.spot_id
        ).filter(
            ParkingSpot.status == 'occupied',
            func.date(Reservation.parking_timestamp) == date.date()
        ).count()
        
        occupancy_rate = (occupied_spots / total_spots * 100) if total_spots > 0 else 0
        occupancy_data.append(round(occupancy_rate, 2))
        occupancy_labels.append(date.strftime('%Y-%m-%d'))

    # Get revenue data by lot
    revenue_data = []
    revenue_labels = []
    
    for lot in parking_lots:
        total_revenue = db.session.query(func.sum(Reservation.parking_cost)).join(
            ParkingSpot, Reservation.spot_id == ParkingSpot.id
        ).filter(
            ParkingSpot.lot_id == lot.id,
            Reservation.leaving_timestamp != None
        ).scalar() or 0
        revenue_data.append(round(total_revenue, 2))
        revenue_labels.append(lot.prime_location_name)

    # Get peak hours data
    peak_hours_data = []
    peak_hours_labels = []
    
    for hour in range(24):
        occupied_spots = db.session.query(ParkingSpot).join(
            Reservation, ParkingSpot.id == Reservation.spot_id
        ).filter(
            ParkingSpot.status == 'occupied',
            func.extract('hour', Reservation.parking_timestamp) == hour
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
            count = db.session.query(Reservation).filter(
                Reservation.leaving_timestamp != None,
                func.extract('epoch', Reservation.leaving_timestamp - Reservation.parking_timestamp) / 3600 <= 1
            ).count()
        elif i == 1:
            count = db.session.query(Reservation).filter(
                Reservation.leaving_timestamp != None,
                func.extract('epoch', Reservation.leaving_timestamp - Reservation.parking_timestamp) / 3600 > 1,
                func.extract('epoch', Reservation.leaving_timestamp - Reservation.parking_timestamp) / 3600 <= 2
            ).count()
        elif i == 2:
            count = db.session.query(Reservation).filter(
                Reservation.leaving_timestamp != None,
                func.extract('epoch', Reservation.leaving_timestamp - Reservation.parking_timestamp) / 3600 > 2,
                func.extract('epoch', Reservation.leaving_timestamp - Reservation.parking_timestamp) / 3600 <= 4
            ).count()
        elif i == 3:
            count = db.session.query(Reservation).filter(
                Reservation.leaving_timestamp != None,
                func.extract('epoch', Reservation.leaving_timestamp - Reservation.parking_timestamp) / 3600 > 4,
                func.extract('epoch', Reservation.leaving_timestamp - Reservation.parking_timestamp) / 3600 <= 8
            ).count()
        else:
            count = db.session.query(Reservation).filter(
                Reservation.leaving_timestamp != None,
                func.extract('epoch', Reservation.leaving_timestamp - Reservation.parking_timestamp) / 3600 > 8
            ).count()
        
        total_reservations = db.session.query(Reservation).filter(
            Reservation.leaving_timestamp != None
        ).count()
        
        percentage = (count / total_reservations * 100) if total_reservations > 0 else 0
        duration_data.append(round(percentage, 2))
    
    return render_template('admin/dashboard.html',
                         total_lots=total_lots,
                         available_spots=available_spots,
                         total_revenue=total_revenue,
                         active_users=active_users,
                         parking_lots=parking_lots,
                         occupancy_labels=occupancy_labels,
                         occupancy_data=occupancy_data,
                         revenue_labels=revenue_labels,
                         revenue_data=revenue_data,
                         peak_hours_labels=peak_hours_labels,
                         peak_hours_data=peak_hours_data,
                         duration_labels=duration_ranges,
                         duration_data=duration_data)

@admin.route('/lot/<int:lot_id>')
@admin_required
def get_lot(lot_id):
    lot = ParkingLot.query.get_or_404(lot_id)
    spots = ParkingSpot.query.filter_by(lot_id=lot_id).all()
    return jsonify({
        'prime_location_name': lot.prime_location_name,
        'price': lot.price,
        'address': lot.address,
        'pin_code': lot.pin_code,
        'maximum_number_of_spots': lot.maximum_number_of_spots,
        'spots': [{
            'id': spot.id,
            'status': spot.status,
            'current_reservation': spot.current_reservation.id if spot.current_reservation else None
        } for spot in spots]
    })

@admin.route('/lot/add', methods=['POST'])
@admin_required
def add_lot():
    try:
        # Validate input
        data = request.form
        if not all(key in data for key in ['prime_location_name', 'price', 'address', 'pin_code', 'maximum_number_of_spots']):
            flash('All fields are required.', 'error')
            return redirect(url_for('admin.dashboard'))
        
        # Validate price
        try:
            price = float(data['price'])
            if price < 0:
                raise ValueError
        except ValueError:
            flash('Invalid price value.', 'error')
            return redirect(url_for('admin.dashboard'))
        
        # Validate maximum spots
        try:
            max_spots = int(data['maximum_number_of_spots'])
            if max_spots < 1:
                raise ValueError
        except ValueError:
            flash('Invalid number of spots.', 'error')
            return redirect(url_for('admin.dashboard'))
        
        # Validate PIN code format (assuming 6-digit format)
        if not re.match(r'^\d{6}$', data['pin_code']):
            flash('PIN code must be 6 digits.', 'error')
            return redirect(url_for('admin.dashboard'))
        
        # Check for duplicate location name
        if ParkingLot.query.filter_by(prime_location_name=data['prime_location_name']).first():
            flash('A parking lot with this name already exists.', 'error')
            return redirect(url_for('admin.dashboard'))
        
        # Create new parking lot
        lot = ParkingLot(
            prime_location_name=data['prime_location_name'],
            price=price,
            address=data['address'],
            pin_code=data['pin_code'],
            maximum_number_of_spots=max_spots
        )
        db.session.add(lot)
        db.session.flush()  # Get the lot ID without committing
        
        # Create parking spots with sequential numbering
        for i in range(max_spots):
            spot = ParkingSpot(
                lot_id=lot.id,
                status='available'
            )
            db.session.add(spot)
        
        db.session.commit()
        flash('Parking lot added successfully with {} spots.'.format(max_spots), 'success')
    except Exception as e:
        db.session.rollback()
        flash('An error occurred while adding the parking lot: {}'.format(str(e)), 'error')
    
    return redirect(url_for('admin.dashboard'))

@admin.route('/lot/<int:lot_id>/edit', methods=['POST'])
@admin_required
def edit_lot(lot_id):
    try:
        lot = ParkingLot.query.get_or_404(lot_id)
        data = request.form
        
        # Validate input
        if not all(key in data for key in ['prime_location_name', 'price', 'address', 'pin_code', 'maximum_number_of_spots']):
            flash('All fields are required.', 'error')
            return redirect(url_for('admin.dashboard'))
        
        # Validate price
        try:
            price = float(data['price'])
            if price < 0:
                raise ValueError
        except ValueError:
            flash('Invalid price value.', 'error')
            return redirect(url_for('admin.dashboard'))
        
        # Validate maximum spots
        try:
            max_spots = int(data['maximum_number_of_spots'])
            if max_spots < 1:
                raise ValueError
        except ValueError:
            flash('Invalid number of spots.', 'error')
            return redirect(url_for('admin.dashboard'))
        
        # Validate PIN code format
        if not re.match(r'^\d{6}$', data['pin_code']):
            flash('PIN code must be 6 digits.', 'error')
            return redirect(url_for('admin.dashboard'))
        
        # Check for duplicate location name (excluding current lot)
        existing_lot = ParkingLot.query.filter(
            ParkingLot.prime_location_name == data['prime_location_name'],
            ParkingLot.id != lot_id
        ).first()
        if existing_lot:
            flash('A parking lot with this name already exists.', 'error')
            return redirect(url_for('admin.dashboard'))
        
        # Update parking lot
        lot.prime_location_name = data['prime_location_name']
        lot.price = price
        lot.address = data['address']
        lot.pin_code = data['pin_code']
        
        # Handle spot changes
        current_spots = ParkingSpot.query.filter_by(lot_id=lot.id).count()
        occupied_spots = ParkingSpot.query.filter_by(lot_id=lot.id, status='occupied').count()
        
        if max_spots < occupied_spots:
            flash('Cannot reduce spots below the number of occupied spots.', 'error')
            return redirect(url_for('admin.dashboard'))
        
        if max_spots > current_spots:
            # Add new spots
            for _ in range(max_spots - current_spots):
                spot = ParkingSpot(lot_id=lot.id, status='available')
                db.session.add(spot)
        elif max_spots < current_spots:
            # Remove excess spots (only if they're available)
            spots_to_remove = ParkingSpot.query.filter_by(
                lot_id=lot.id,
                status='available'
            ).limit(current_spots - max_spots).all()
            for spot in spots_to_remove:
                db.session.delete(spot)
        
        lot.maximum_number_of_spots = max_spots
        db.session.commit()
        flash('Parking lot updated successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        flash('An error occurred while updating the parking lot: {}'.format(str(e)), 'error')
    
    return redirect(url_for('admin.dashboard'))

@admin.route('/lot/<int:lot_id>/delete', methods=['POST'])
@admin_required
def delete_lot(lot_id):
    try:
        lot = ParkingLot.query.get_or_404(lot_id)
        
        # Get all spots in the lot
        spots = ParkingSpot.query.filter_by(lot_id=lot.id).all()
        
        # Get active spots with their reservations
        active_spots = [spot for spot in spots if spot.status == 'occupied']
        active_reservations = []
        
        for spot in active_spots:
            if spot.current_reservation:
                active_reservations.append({
                    'spot_id': spot.id,
                    'user': spot.current_reservation.user.username,
                    'start_time': spot.current_reservation.parking_timestamp.isoformat()
                })
        
        if active_reservations:
            return jsonify({
                'success': False,
                'message': 'Cannot delete parking lot with active reservations.',
                'active_reservations': active_reservations,
                'reservation_count': len(active_reservations)
            }), 400
        
        # Get lot details for confirmation message
        lot_name = lot.prime_location_name
        spot_count = len(spots)
        
        try:
            # First, delete all historical reservations for spots in this lot
            for spot in spots:
                # Delete all historical reservations (where leaving_timestamp is not None)
                Reservation.query.filter(
                    Reservation.spot_id == spot.id,
                    Reservation.leaving_timestamp != None
                ).delete()
            
            # Now delete the lot (this will cascade delete the spots)
            db.session.delete(lot)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': f'Parking lot "{lot_name}" and its {spot_count} spots have been deleted successfully.'
            })
        except Exception as e:
            db.session.rollback()
            return jsonify({
                'success': False,
                'message': f'Error deleting parking lot: {str(e)}'
            }), 500
            
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'An unexpected error occurred: {str(e)}'
        }), 500

@admin.route('/lot/<int:lot_id>/spots')
@admin_required
def get_lot_spots(lot_id):
    try:
        lot = ParkingLot.query.get_or_404(lot_id)
        spots = ParkingSpot.query.filter_by(lot_id=lot_id).all()
        
        return jsonify({
            'success': True,
            'lot_name': lot.prime_location_name,
            'spots': [{
                'id': spot.id,
                'status': spot.status,
                'current_reservation': {
                    'id': spot.current_reservation.id,
                    'user': spot.current_reservation.user.username,
                    'start_time': spot.current_reservation.parking_timestamp.isoformat()
                } if spot.current_reservation else None
            } for spot in spots]
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error fetching spots: {str(e)}'
        }) 