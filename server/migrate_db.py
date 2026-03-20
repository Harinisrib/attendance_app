"""
Database migration script - safely adds new columns to existing tables.
Run this once: python migrate_db.py
"""
import sqlite3
import os

db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance', 'attendance.db')
print(f"Migrating database at: {db_path}")

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

def add_column_if_missing(table, column, col_type):
    cursor.execute(f"PRAGMA table_info({table})")
    existing = [row[1] for row in cursor.fetchall()]
    if column not in existing:
        print(f"  [+] Adding column: {table}.{column}")
        cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} {col_type}")
    else:
        print(f"  [=] Already exists: {table}.{column}")

add_column_if_missing('classroom', 'latitude',  'REAL')
add_column_if_missing('classroom', 'longitude', 'REAL')

# ── ClassSession: Time slots & recurrence
add_column_if_missing('class_session', 'start_time',  'TEXT')
add_column_if_missing('class_session', 'end_time',    'TEXT')
add_column_if_missing('class_session', 'day_of_week', 'TEXT')

# ── Attendance: Smart Verification metadata
add_column_if_missing('attendance', 'subject_id',          'INTEGER')
add_column_if_missing('attendance', 'verification_type',   'TEXT DEFAULT "Manual"')
add_column_if_missing('attendance', 'verification_token',  'TEXT')
add_column_if_missing('attendance', 'gps_lat',             'REAL')
add_column_if_missing('attendance', 'gps_long',            'REAL')
add_column_if_missing('attendance', 'status_note',         'TEXT')

# V2.0 Tracking
add_column_if_missing('attendance', 'status',              'TEXT DEFAULT "Present"')
add_column_if_missing('attendance', 'check_in_time',       'TEXT')
add_column_if_missing('attendance', 'photo_url',           'TEXT')

# ── Student: risk level & student-login fields
add_column_if_missing('student', 'email',      'TEXT')
add_column_if_missing('student', 'password',   'TEXT')
add_column_if_missing('student', 'risk_level', 'TEXT DEFAULT "Low"')

# ── Create new tables if they don't exist yet
cursor.execute("""
    CREATE TABLE IF NOT EXISTS subject (
        id           INTEGER PRIMARY KEY AUTOINCREMENT,
        name         TEXT NOT NULL,
        classroom_id INTEGER NOT NULL,
        FOREIGN KEY (classroom_id) REFERENCES classroom(id)
    )
""")
print("  [=] Table 'subject' ensured.")

cursor.execute("""
    CREATE TABLE IF NOT EXISTS leave_request (
        id         INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER NOT NULL,
        reason     TEXT    NOT NULL,
        start_date TEXT    NOT NULL,
        end_date   TEXT    NOT NULL,
        status     TEXT    DEFAULT 'Pending',
        created_at TEXT    DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (student_id) REFERENCES student(id)
    )
""")
print("  [=] Table 'leave_request' ensured.")

cursor.execute("""
    CREATE TABLE IF NOT EXISTS academic_event (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        name        TEXT    NOT NULL,
        date        TEXT    NOT NULL,
        is_holiday  INTEGER DEFAULT 1,
        description TEXT
    )
""")
print("  [=] Table 'academic_event' ensured.")

conn.commit()
conn.close()
print("\nMigration complete! Restart the server.")
