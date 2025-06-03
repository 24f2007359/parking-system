from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
import os
import sys

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from models.file1 import db

def upgrade():
    app = create_app()
    with app.app_context():
        try:
            # Add new columns to reservations table one by one
            columns = [
                ('user_name', 'VARCHAR(100)'),
                ('user_phone', 'VARCHAR(20)'),
                ('vehicle_type', 'VARCHAR(50)'),
                ('vehicle_number', 'VARCHAR(20)'),
                ('vehicle_model', 'VARCHAR(50)'),
                ('vehicle_color', 'VARCHAR(30)'),
                ('driver_name', 'VARCHAR(100)')
            ]
            
            for column_name, column_type in columns:
                try:
                    db.session.execute(text(f'ALTER TABLE reservations ADD COLUMN {column_name} {column_type}'))
                    db.session.commit()
                    print(f"Successfully added column {column_name}")
                except Exception as e:
                    if "duplicate column name" not in str(e).lower():
                        print(f"Error adding column {column_name}: {str(e)}")
                    else:
                        print(f"Column {column_name} already exists")
                    db.session.rollback()
            
            print("Migration completed")
        except Exception as e:
            db.session.rollback()
            print(f"Error in migration: {str(e)}")

if __name__ == '__main__':
    upgrade() 