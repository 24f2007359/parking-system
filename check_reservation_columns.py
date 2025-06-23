import sqlite3
import sys

conn = sqlite3.connect('instance/app.db')
cursor = conn.cursor()
cursor.execute('PRAGMA table_info(reservations)')
columns = cursor.fetchall()
print('Columns in reservations table:')
sys.stdout.flush()
for col in columns:
    print(col)
    sys.stdout.flush()
conn.close() 