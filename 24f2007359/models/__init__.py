from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

def init_db(app):
    db.init_app(app)
    with app.app_context():
        # Import models and patch function
        from .file1 import User, create_sample_data, force_update_parking_lots_schema
        
        # Force update the schema before creating tables
        force_update_parking_lots_schema()
        
        # Create tables
        db.create_all()
        
        # Create admin user if it doesn't exist
        if not User.query.filter_by(username='admin').first():
            admin = User(username='admin', role='admin')
            admin.set_password('admin123')  # You should change this in production
            db.session.add(admin)
            db.session.commit()
            # Create sample data after admin user is created
            create_sample_data() 