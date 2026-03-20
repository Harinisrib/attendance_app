from extensions import db
from flask_login import UserMixin
from datetime import datetime

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    name = db.Column(db.String(1000), nullable=False)
    classes = db.relationship('Classroom', backref='faculty', lazy=True)

    @property
    def is_faculty(self):
        return True

class Classroom(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    faculty_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Smart Verification fields
    latitude = db.Column(db.Float, nullable=True) # Classroom GPS lat
    longitude = db.Column(db.Float, nullable=True) # Classroom GPS long
    
    students = db.relationship('Student', backref='classroom', lazy=True)
    sessions = db.relationship('ClassSession', backref='classroom', lazy=True)
    subjects = db.relationship('Subject', backref='classroom', lazy=True)

class Student(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=True) # Allow null for existing, then update
    password = db.Column(db.String(255), nullable=True)
    roll_number = db.Column(db.String(50), nullable=False)
    classroom_id = db.Column(db.Integer, db.ForeignKey('classroom.id'), nullable=False)
    attendances = db.relationship('Attendance', backref='student', lazy=True)
    risk_level = db.Column(db.String(20), default='Low') # Low, Medium, High
    
    # Associations
    leaves = db.relationship('LeaveRequest', backref='student', lazy=True)

    @property
    def is_faculty(self):
        return False

class ClassSession(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    classroom_id = db.Column(db.Integer, db.ForeignKey('classroom.id'), nullable=False)
    
    # New Scheduling Fields
    start_time = db.Column(db.Time, nullable=True) # e.g. 09:00:00
    end_time = db.Column(db.Time, nullable=True)   # e.g. 10:00:00
    day_of_week = db.Column(db.String(20), nullable=True) # e.g. 'Monday'

class Attendance(db.Model):
    __table_args__ = (
        db.Index('idx_attendance_student_date', 'student_id', 'date'),
        db.Index('idx_attendance_date_session', 'date', 'session')
    )
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False, default=datetime.utcnow)
    session = db.Column(db.String(10), nullable=False) # 'Morning', 'Afternoon'
    is_present = db.Column(db.Boolean, default=False)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    
    # Advanced metadata
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.id'), nullable=True)
    verification_type = db.Column(db.String(20), default='Manual') # Manual, QR, GPS
    verification_token = db.Column(db.String(100), nullable=True) # For QR
    gps_lat = db.Column(db.Float, nullable=True)
    gps_long = db.Column(db.Float, nullable=True)
    status_note = db.Column(db.String(200), nullable=True) # e.g. "Late", "Medical Leave"
    
    # New Status & Tracking Fields
    status = db.Column(db.String(20), default='Present') # 'Present', 'Absent', 'Late', 'Excused'
    check_in_time = db.Column(db.DateTime, nullable=True)
    photo_url = db.Column(db.String(500), nullable=True) # For Ph2 Biometric Audit

    def to_dict(self):
        return {
            'date': self.date.isoformat(),
            'session': self.session,
            'is_present': self.is_present,
            'subject': self.subject.name if self.subject else None,
            'status_note': self.status_note
        }

class Subject(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    classroom_id = db.Column(db.Integer, db.ForeignKey('classroom.id'), nullable=False)
    attendances = db.relationship('Attendance', backref='subject', lazy=True)

class LeaveRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    reason = db.Column(db.Text, nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(20), default='Pending') # Pending, Approved, Rejected
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class AcademicEvent(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    date = db.Column(db.Date, nullable=False)
    is_holiday = db.Column(db.Boolean, default=True)
    description = db.Column(db.String(500), nullable=True)
