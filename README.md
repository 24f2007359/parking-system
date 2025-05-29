# Parking Management System

A Flask-based web application for managing parking lots, spots, and reservations. This system provides separate interfaces for administrators and users to manage parking operations efficiently.

## Features

### Admin Features
- **Dashboard Overview**
  - Total parking lots and available spots
  - Total revenue and active users
  - Occupancy rate charts (last 7 days)
  - Revenue distribution by lot
  - Peak hours analysis
  - Duration distribution of parking sessions

- **Parking Lot Management**
  - Add new parking lots with customizable spots
  - Edit existing lot details (name, price, address, spots)
  - Delete parking lots (with safety checks for active reservations)
  - View lot status and occupancy
  - Monitor active reservations

### User Features
- **Dashboard**
  - View active reservations
  - Access reservation history
  - Track total parking hours and spending
  - Loyalty points system
  - Book new parking spots

- **Reservation Management**
  - Book available spots
  - Complete parking sessions
  - View parking costs and duration
  - Access detailed reservation information

## Technical Stack

- **Backend**: Python 3.12 with Flask
- **Database**: SQLite with SQLAlchemy ORM
- **Frontend**: HTML, CSS, JavaScript
- **UI Framework**: Bootstrap 5
- **Charts**: Chart.js
- **Tables**: DataTables

## Database Models

### ParkingLot
- `id`: Primary key
- `prime_location_name`: Unique name for the lot
- `address`: Physical location
- `price`: Rate per hour
- `is_active`: Lot status
- `pin_code`: 6-digit location code
- `maximum_number_of_spots`: Total capacity
- Relationship with ParkingSpot (one-to-many)

### ParkingSpot
- `id`: Primary key
- `lot_id`: Foreign key to ParkingLot
- `status`: Available/Occupied/Reserved
- Relationship with Reservation (one-to-many)

### Reservation
- `id`: Primary key
- `spot_id`: Foreign key to ParkingSpot
- `user_id`: Foreign key to User
- `parking_timestamp`: Start time
- `leaving_timestamp`: End time
- `parking_cost`: Total cost
- `duration`: Parking duration

### User
- `id`: Primary key
- `username`: Unique username
- `role`: Admin/User
- `loyalty_points`: User's loyalty points

## Setup Instructions

1. **Clone the Repository**
   ```bash
   git clone <repository-url>
   cd <repository-name>
   ```

2. **Create Virtual Environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Initialize Database**
   ```bash
   flask db init
   flask db migrate
   flask db upgrade
   ```

5. **Run the Application**
   ```bash
   python app.py
   ```

The application will be available at `http://127.0.0.1:5000`

## Usage Guide

### Admin Access
1. Login with admin credentials
2. Access the admin dashboard at `/admin/dashboard`
3. Manage parking lots, view statistics, and monitor operations

### User Access
1. Register/Login with user credentials
2. Access the user dashboard at `/auth/user/dashboard`
3. Book spots and manage reservations

## Security Features

- Role-based access control (Admin/User)
- Session management
- CSRF protection
- Password hashing
- Input validation and sanitization

## Error Handling

The system includes comprehensive error handling for:
- Invalid inputs
- Database constraints
- Active reservation conflicts
- Authentication/Authorization
- Session management

## API Endpoints

### Admin Routes
- `GET /admin/dashboard`: Admin dashboard
- `GET /admin/lot/<id>`: Get lot details
- `POST /admin/lot/add`: Add new lot
- `POST /admin/lot/<id>/edit`: Edit lot
- `POST /admin/lot/<id>/delete`: Delete lot
- `GET /admin/lot/<id>/spots`: Get lot spots

### User Routes
- `GET /auth/user/dashboard`: User dashboard
- `POST /auth/user/dashboard/book`: Book spot
- `GET /auth/reservation/<id>`: View reservation
- `POST /auth/user/reservation/<id>/complete`: Complete reservation

### API Routes
- `GET /api/user/dashboard_data`: User dashboard data
- `GET /api/parking_lots`: List all parking lots

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support, please open an issue in the repository or contact the development team. 