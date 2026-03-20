from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify, current_app
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, logout_user, login_required
from models import User, Student
from flask import session
from extensions import db
import jwt
import datetime

auth = Blueprint('auth', __name__)

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        user = User.query.filter_by(email=email).first()

        if not user:
            # Check student table
            user = Student.query.filter_by(email=email).first()
            utype = 'student'
        else:
            utype = 'faculty'

        if user and check_password_hash(user.password, password):
            session['user_type'] = utype
            login_user(user, remember=True)
            if utype == 'student':
                return redirect(url_for('main.student_dashboard'))
            return redirect(url_for('main.dashboard'))
        else:
            flash('Login failed. Check your email and password.')

    return render_template('auth.html', mode='login')

@auth.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        email = request.form.get('email')
        name = request.form.get('name')
        password = request.form.get('password')

        user = User.query.filter_by(email=email).first()

        if user:
            flash('Email already exists.')
            return redirect(url_for('auth.signup'))

        new_user = User(email=email, name=name, password=generate_password_hash(password, method='scrypt'))
        db.session.add(new_user)
        db.session.commit()

        session['user_type'] = 'faculty'
        login_user(new_user, remember=True)
        return redirect(url_for('main.dashboard'))

    return render_template('auth.html', mode='signup')

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))

@auth.route('/change_password', methods=['GET', 'POST'])
@login_required
def change_password():
    if request.method == 'POST':
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')

        if not check_password_hash(current_user.password, current_password):
            flash('Current password is incorrect.')
            return redirect(url_for('auth.change_password'))

        if new_password != confirm_password:
            flash('New passwords do not match.')
            return redirect(url_for('auth.change_password'))

        current_user.password = generate_password_hash(new_password, method='scrypt')
        db.session.commit()
        flash('Password updated successfully.')
        
        if session.get('user_type') == 'student':
            return redirect(url_for('main.student_dashboard'))
        return redirect(url_for('main.dashboard'))

    return render_template('change_password.html')

@auth.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email')
        verification_val = request.form.get('verification_value') # Roll number or Name
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')

        if new_password != confirm_password:
            flash('Passwords do not match.')
            return redirect(url_for('auth.forgot_password'))

        # Search for faculty first
        user = User.query.filter_by(email=email).first()
        if user:
            # For faculty, verify by name (case-insensitive)
            if user.name.lower() == verification_val.lower():
                user.password = generate_password_hash(new_password, method='scrypt')
                db.session.commit()
                flash('Password reset successful. Please login.')
                return redirect(url_for('auth.login'))
        else:
            # Search for student
            user = Student.query.filter_by(email=email).first()
            if user:
                # For student, verify by roll number
                if user.roll_number.lower() == verification_val.lower():
                    user.password = generate_password_hash(new_password, method='scrypt')
                    db.session.commit()
                    flash('Password reset successful. Please login.')
                    return redirect(url_for('auth.login'))
        
        flash('Identity verification failed. Please check your details.')
    
    return render_template('forgot_password.html')

# API Endpoints for Phase 2
@auth.route('/api/login', methods=['POST'])
def api_login():
    data = request.get_json()
    if not data or not data.get('email') or not data.get('password'):
        return jsonify({'error': 'Missing email or password'}), 400

    email = data.get('email')
    password = data.get('password')

    user = User.query.filter_by(email=email).first()
    utype = 'faculty'
    
    if not user:
        user = Student.query.filter_by(email=email).first()
        utype = 'student'

    if user and check_password_hash(user.password, password):
        token = jwt.encode({
            'user_id': user.id,
            'user_type': utype,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24)
        }, current_app.config['JWT_SECRET_KEY'], algorithm='HS256')

        return jsonify({
            'token': token,
            'user': {
                'id': user.id,
                'name': user.name,
                'email': user.email,
                'type': utype
            }
        })
    
    return jsonify({'error': 'Invalid credentials'}), 401

def token_required(f):
    from functools import wraps
    from flask_login import current_user as login_user_obj
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            if auth_header.startswith('Bearer '):
                token = auth_header.split(' ')[1]
        
        if token:
            try:
                data = jwt.decode(token, current_app.config['JWT_SECRET_KEY'], algorithms=['HS256'])
                if data['user_type'] == 'student':
                    user = Student.query.get(data['user_id'])
                else:
                    user = User.query.get(data['user_id'])
                
                if not user:
                    return jsonify({'error': 'User not found'}), 401
                return f(user, *args, **kwargs)
            except Exception as e:
                return jsonify({'error': 'Token is invalid'}), 401
        
        # Fallback to session-based auth (flask-login) for legacy templates
        if login_user_obj.is_authenticated:
            return f(login_user_obj, *args, **kwargs)
            
        return jsonify({'error': 'Authentication required'}), 401
    return decorated
