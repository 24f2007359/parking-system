from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from . import db

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    role = db.Column(db.String(20), nullable=False, default='user')
    
    # Relationship with Reservation
    reservations = db.relationship('Reservation', backref='user', lazy=True)
    
    def __init__(self, username, role='user'):
        self.username = username
        self.role = role
    
    def set_password(self, password):
        """Hash and set the user's password."""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check if the provided password matches the hash."""
        return check_password_hash(self.password_hash, password)
    
    def is_admin(self):
        """Check if the user has admin role."""
        return self.role == 'admin'
    
    def __repr__(self):
        return f'<User {self.username}>'

class ParkingLot(db.Model):
    __tablename__ = 'parking_lots'
    
    id = db.Column(db.Integer, primary_key=True)
    prime_location_name = db.Column(db.String(100), nullable=False)
    address = db.Column(db.String(200), nullable=False)
    price = db.Column(db.Float, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    pin_code = db.Column(db.String(10), nullable=False)
    maximum_number_of_spots = db.Column(db.Integer, nullable=False)
    
    # Relationship with ParkingSpot
    spots = db.relationship('ParkingSpot', backref='lot', lazy=True, cascade='all, delete-orphan')
    
    def __init__(self, prime_location_name, price, address, pin_code, maximum_number_of_spots):
        self.prime_location_name = prime_location_name
        self.price = price
        self.address = address
        self.pin_code = pin_code
        self.maximum_number_of_spots = maximum_number_of_spots
    
    def __repr__(self):
        return f'<ParkingLot {self.prime_location_name}>'
    
    @property
    def available_spots(self):
        """Return the number of available spots in the lot."""
        return len([spot for spot in self.spots if spot.status == 'available'])
    
    @property
    def occupied_spots(self):
        """Return the number of occupied spots in the lot."""
        return len([spot for spot in self.spots if spot.status == 'occupied'])

class ParkingSpot(db.Model):
    __tablename__ = 'parking_spots'
    
    id = db.Column(db.Integer, primary_key=True)
    lot_id = db.Column(db.Integer, db.ForeignKey('parking_lots.id', ondelete='CASCADE'), nullable=False)
    status = db.Column(db.String(20), nullable=False, default='available')  # available, occupied, reserved
    
    # Relationship with Reservation
    reservations = db.relationship('Reservation', backref='spot', lazy=True)
    
    def __init__(self, lot_id, status='available'):
        self.lot_id = lot_id
        self.status = status
    
    def __repr__(self):
        return f'<ParkingSpot {self.id} in Lot {self.lot_id}>'
    
    @property
    def is_available(self):
        """Check if the spot is available."""
        return self.status == 'available'
    
    @property
    def current_reservation(self):
        """Get the current active reservation for this spot."""
        return Reservation.query.filter_by(
            spot_id=self.id,
            leaving_timestamp=None
        ).first()

class Reservation(db.Model):
    __tablename__ = 'reservations'
    
    id = db.Column(db.Integer, primary_key=True)
    spot_id = db.Column(db.Integer, db.ForeignKey('parking_spots.id', ondelete='CASCADE'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    parking_timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    leaving_timestamp = db.Column(db.DateTime, nullable=True)
    parking_cost = db.Column(db.Float, nullable=True)
    
    # User details
    user_name = db.Column(db.String(100), nullable=False)
    user_phone = db.Column(db.String(20), nullable=True)
    
    # Vehicle details
    vehicle_type = db.Column(db.String(50), nullable=True)
    vehicle_number = db.Column(db.String(20), nullable=True)
    vehicle_model = db.Column(db.String(50), nullable=True)
    vehicle_color = db.Column(db.String(30), nullable=True)
    driver_name = db.Column(db.String(100), nullable=True)
    
    def __init__(self, spot_id, user_id, parking_timestamp=None, user_name=None, user_phone=None,
                 vehicle_type=None, vehicle_number=None, vehicle_model=None, vehicle_color=None, driver_name=None):
        self.spot_id = spot_id
        self.user_id = user_id
        self.parking_timestamp = parking_timestamp or datetime.utcnow()
        self.leaving_timestamp = None
        self.parking_cost = None
        self.user_name = user_name
        self.user_phone = user_phone
        self.vehicle_type = vehicle_type
        self.vehicle_number = vehicle_number
        self.vehicle_model = vehicle_model
        self.vehicle_color = vehicle_color
        self.driver_name = driver_name
    
    def complete_reservation(self, leaving_timestamp=None):
        """Complete the reservation and calculate the cost."""
        self.leaving_timestamp = leaving_timestamp or datetime.utcnow()
        # Calculate parking duration in hours
        duration = (self.leaving_timestamp - self.parking_timestamp).total_seconds() / 3600
        # Get the parking lot's price per hour
        hourly_rate = self.spot.lot.price
        # Calculate total cost
        self.parking_cost = round(duration * hourly_rate, 2)
        # Update spot status
        self.spot.status = 'available'
    
    @property
    def is_active(self):
        """Check if the reservation is still active."""
        return self.leaving_timestamp is None
    
    @property
    def duration(self):
        """Get the duration of the parking in hours."""
        if not self.leaving_timestamp:
            return None
        return round((self.leaving_timestamp - self.parking_timestamp).total_seconds() / 3600, 2)
    
    def __repr__(self):
        return f'<Reservation {self.id} for User {self.user_id} at Spot {self.spot_id}>'

def create_sample_data():
    """Create sample data for testing."""
    try:
        # Create a sample parking lot
        lot = ParkingLot(
            prime_location_name="Downtown Parking",
            price=10.50,
            address="123 Main Street",
            pin_code="12345",
            maximum_number_of_spots=50
        )
        db.session.add(lot)
        
        # Create some sample parking spots
        for i in range(5):
            spot = ParkingSpot(lot_id=lot.id)
            db.session.add(spot)
        
        db.session.commit()
        print("Sample data created successfully.")
    except Exception as e:
        db.session.rollback()
        print(f"Error creating sample data: {str(e)}")

def force_update_parking_lots_schema():
    """
    Force update the parking_lots table schema to ensure is_active column exists.
    This is a more aggressive approach that will work even if the table exists.
    """
    try:
        # Get the database connection
        conn = db.engine.raw_connection()
        cursor = conn.cursor()
        
        # Check if table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='parking_lots'")
        if cursor.fetchone():
            # Check if is_active column exists
            cursor.execute("PRAGMA table_info(parking_lots)")
            columns = [col[1] for col in cursor.fetchall()]
            
            if 'is_active' not in columns:
                # Add the column
                cursor.execute("ALTER TABLE parking_lots ADD COLUMN is_active BOOLEAN DEFAULT 1")
                # Update existing rows to have is_active = 1
                cursor.execute("UPDATE parking_lots SET is_active = 1 WHERE is_active IS NULL")
                conn.commit()
                print("Successfully added and initialized is_active column")
            else:
                print("is_active column already exists")
        else:
            print("parking_lots table doesn't exist - will be created by db.create_all()")
        
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Error in force_update_parking_lots_schema: {str(e)}")
        if 'conn' in locals():
            conn.rollback()
            conn.close()

def patch_parking_lots_schema():
    """
    One-time function to add is_active column to parking_lots table if it doesn't exist.
    This should be called before db.create_all() or during database initialization.
    """
    try:
        # First check if the table exists
        result = db.session.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='parking_lots'
        """).fetchone()
        
        if result:
            # Table exists, check if is_active column exists
            result = db.session.execute('PRAGMA table_info(parking_lots)').fetchall()
            columns = [col[1] for col in result]  # Column names are in the second position
            
            if 'is_active' not in columns:
                # Add the column if it doesn't exist
                db.session.execute('ALTER TABLE parking_lots ADD COLUMN is_active BOOLEAN DEFAULT 1')
                # Update existing rows
                db.session.execute('UPDATE parking_lots SET is_active = 1 WHERE is_active IS NULL')
                db.session.commit()
                print("Successfully added is_active column to parking_lots table")
            else:
                print("is_active column already exists in parking_lots table")
        else:
            print("parking_lots table doesn't exist yet - will be created by db.create_all()")
    except Exception as e:
        db.session.rollback()
        print(f"Error patching parking_lots schema: {str(e)}")
        # If the normal patch fails, try the force update
        force_update_parking_lots_schema() 