from flask import Flask
from flask_sqlalchemy import SQLAlchemy
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
            # Add is_active column with default value True
            db.session.execute('ALTER TABLE parking_lots ADD COLUMN is_active BOOLEAN DEFAULT TRUE')
            db.session.commit()
            print("Successfully added is_active column to parking_lots table")
        except Exception as e:
            db.session.rollback()
            print(f"Error adding is_active column: {str(e)}")

if __name__ == '__main__':
    upgrade() 