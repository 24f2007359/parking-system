from sqlalchemy import create_engine, inspect, Boolean
from sqlalchemy.sql import text
import os

def add_is_active_column():
    """
    Add is_active column to parking_lots table if it doesn't exist.
    This function is idempotent and can be run multiple times safely.
    """
    # Get the database URL from environment variable or use default SQLite path
    database_url = os.getenv('DATABASE_URL', 'sqlite:///parking_system.db')
    engine = create_engine(database_url)
    
    # Create an inspector to check table structure
    inspector = inspect(engine)
    
    # Check if the column exists
    columns = [col['name'] for col in inspector.get_columns('parking_lots')]
    
    if 'is_active' not in columns:
        try:
            # Add the column with default value True
            with engine.connect() as conn:
                conn.execute(text("""
                    ALTER TABLE parking_lots 
                    ADD COLUMN is_active BOOLEAN DEFAULT TRUE
                """))
                conn.commit()
            print("Successfully added is_active column to parking_lots table")
        except Exception as e:
            print(f"Error adding is_active column: {str(e)}")
    else:
        print("is_active column already exists in parking_lots table")

if __name__ == '__main__':
    add_is_active_column() 