# Smart Parking Management System

A modern web-based parking management system that helps manage parking lots, reservations, and provides real-time analytics for administrators.

## Features

### For Users
- **Easy Parking Spot Reservation**
  - View available parking spots in real-time
  - Make instant reservations
  - View parking history
  - Manage vehicle information
  - Get parking duration estimates

### For Administrators
- **Comprehensive Dashboard**
  - Real-time occupancy monitoring
  - Revenue tracking and analytics
  - Peak hours analysis
  - Parking duration distribution
  - Active user tracking

- **Parking Lot Management**
  - Add/Edit/Delete parking lots
  - Set pricing per hour
  - Manage parking spots
  - View active reservations
  - Monitor lot status

- **Advanced Analytics**
  - Occupancy rate over time
  - Revenue by lot
  - Peak hours analysis
  - Parking duration distribution
  - User activity tracking

## Technology Stack

- **Backend**
  - Python 3.x
  - Flask (Web Framework)
  - SQLAlchemy (ORM)
  - SQLite (Database)

- **Frontend**
  - HTML5/CSS3
  - JavaScript
  - Bootstrap 5
  - Chart.js (Analytics)
  - DataTables (Table Management)
  - Font Awesome (Icons)

## Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd parking-management-system
   ```

2. **Create and activate virtual environment**
   ```bash
   # Windows
   python -m venv venv
   .\venv\Scripts\activate

   # Linux/Mac
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Initialize the database**
   ```bash
   flask db upgrade
   ```

5. **Run the application**
   ```bash
   flask run
   ```

## Project Structure

```
parking-management-system/
├── 24f2007359/
│   ├── controllers/         # Route handlers and business logic
│   ├── models/             # Database models
│   ├── migrations/         # Database migrations
│   ├── templates/          # HTML templates
│   │   ├── admin/         # Admin dashboard templates
│   │   └── user/          # User interface templates
│   └── static/            # Static files (CSS, JS, images)
├── requirements.txt        # Project dependencies
└── README.md              # Project documentation
```

## Database Schema

### Key Tables
- **users**: User account information
- **parking_lots**: Parking lot details
- **parking_spots**: Individual parking spots
- **reservations**: Parking spot reservations
- **vehicles**: User vehicle information

## Usage

### Admin Access
1. Navigate to `/admin/login`
2. Use admin credentials to access the dashboard
3. Manage parking lots, view analytics, and monitor reservations

### User Access
1. Register/Login at the homepage
2. Browse available parking lots
3. Make reservations
4. View parking history

## Features in Detail

### Admin Dashboard
- **Real-time Analytics**
  - Occupancy rate tracking
  - Revenue monitoring
  - User activity analysis
  - Peak hours visualization

- **Parking Lot Management**
  - Add new parking lots
  - Edit lot details
  - Set pricing
  - Manage spots
  - View active reservations

- **User Management**
  - View user activity
  - Monitor reservations
  - Track vehicle information

### User Interface
- **Reservation System**
  - Real-time spot availability
  - Instant booking
  - Reservation history
  - Vehicle management

- **Parking Information**
  - Lot locations
  - Pricing details
  - Spot availability
  - Duration estimates

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

## Acknowledgments

- Bootstrap for the frontend framework
- Chart.js for analytics visualization
- Font Awesome for icons
- SQLAlchemy for database management 