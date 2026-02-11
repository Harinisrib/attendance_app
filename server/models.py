from extensions import db
from flask_login import UserMixin
from datetime import datetime

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    name = db.Column(db.String(1000), nullable=False)
    classes = db.relationship('Classroom', backref='faculty', lazy=True)

class Classroom(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    faculty_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    students = db.relationship('Student', backref='classroom', lazy=True)

class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    roll_number = db.Column(db.String(50), nullable=False)
    classroom_id = db.Column(db.Integer, db.ForeignKey('classroom.id'), nullable=False)
    attendances = db.relationship('Attendance', backref='student', lazy=True)
    risk_level = db.Column(db.String(20), default='Low') # Low, Medium, High

class Attendance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False, default=datetime.utcnow)
    session = db.Column(db.String(10), nullable=False) # 'Morning', 'Afternoon'
    is_present = db.Column(db.Boolean, default=False)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)

    def to_dict(self):
        return {
            'date': self.date.isoformat(),
            'session': self.session,
            'is_present': self.is_present
        }
