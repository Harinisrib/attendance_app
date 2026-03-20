from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app
from flask_login import login_required, current_user
from models import Classroom, Student, ClassSession, Attendance
from extensions import db
from auth import token_required
from datetime import datetime, timedelta
import jwt
import math

main = Blueprint('main', __name__)

def haversine_distance(lat1, lon1, lat2, lon2):
    """Calculate distance in meters between two GPS coordinates."""
    if lat1 is None or lon1 is None or lat2 is None or lon2 is None:
        return 999999 # Inf
    R = 6371000 # Earth radius in meters
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

def format_date_with_day(date_obj):
    """Format date as 'Monday, Feb 12, 2026'"""
    return date_obj.strftime('%A, %b %d, %Y')

def format_date_short(date_obj):
    """Format date as 'Mon, Feb 12'"""
    return date_obj.strftime('%a, %b %d')

def get_attendance_percentage(student, start_date=None, end_date=None, subject_id=None):
    from models import LeaveRequest
    approved_leaves = LeaveRequest.query.filter_by(student_id=student.id, status='Approved').all()
    
    def is_on_leave(date_obj):
        for leave in approved_leaves:
            if leave.start_date <= date_obj <= leave.end_date:
                return True
        return False
        
    total_relevant_sessions = 0
    present_count = 0
    
    for a in student.attendances:
        # Apply filters
        if start_date and a.date < start_date: continue
        if end_date and a.date > end_date: continue
        if subject_id is not None and a.subject_id != subject_id: continue
        
        if is_on_leave(a.date):
            continue
            
        total_relevant_sessions += 1
        if a.is_present:
            present_count += 1
            
    if total_relevant_sessions == 0: return 0
    return round((present_count / total_relevant_sessions) * 100, 1)

@main.route('/')
def index():
    if current_user.is_authenticated:
        if not current_user.is_faculty:
            return redirect(url_for('main.student_dashboard'))
        return redirect(url_for('main.dashboard'))
    return redirect(url_for('auth.login'))

@main.route('/dashboard')
@login_required
def dashboard():
    classes = Classroom.query.filter_by(faculty_id=current_user.id).all()
    
    # Calculate aggregate stats for sidebar
    total_students = 0
    total_classes = len(classes)
    for c in classes:
        total_students += len(c.students)
        
    return render_template('dashboard.html', 
                           classes=classes,
                           total_students=total_students,
                           total_classes=total_classes)

@main.route('/student/dashboard')
@login_required
def student_dashboard():
    if current_user.is_faculty:
        return redirect(url_for('main.dashboard'))
    
    student = Student.query.get(current_user.id)
    attendance_pct = get_attendance_percentage(student)
    
    # Graphs Data (last 30 days)
    from sqlalchemy import func
    from models import Attendance
    
    attendance_records = Attendance.query.filter_by(student_id=student.id).order_by(Attendance.date.desc()).limit(30).all()
    attendance_records.reverse()
    
    labels = [r.date.strftime('%b %d') for r in attendance_records]
    data = [1 if r.is_present else 0 for r in attendance_records]
    
    return render_template('student_dashboard.html', 
                           student=student, 
                           attendance_pct=attendance_pct,
                           total_sessions=len(student.attendances),
                           present_count=sum(1 for a in student.attendances if a.is_present),
                           absent_count=sum(1 for a in student.attendances if not a.is_present),
                           labels=labels,
                           data=data)

@main.route('/student/attendance')
@login_required
def student_attendance():
    if current_user.is_faculty:
        return redirect(url_for('main.dashboard'))
        
    date_query = request.args.get('date', '')
    page = request.args.get('page', 1, type=int)
    
    query = Attendance.query.filter_by(student_id=current_user.id)
    if date_query:
        try:
            date_obj = datetime.strptime(date_query, '%Y-%m-%d').date()
            query = query.filter_by(date=date_obj)
        except ValueError:
            flash('Invalid date format')

    attendances = query.order_by(Attendance.date.desc()).paginate(page=page, per_page=10, error_out=False)
    
    return render_template('student_attendance.html', attendances=attendances, date_query=date_query)

# Leave Management Routes
@main.route('/student/leave', methods=['GET', 'POST'])
@login_required
def student_leave():
    if current_user.is_faculty:
        return redirect(url_for('main.dashboard'))
    
    if request.method == 'POST':
        reason = request.form.get('reason')
        start_date_str = request.form.get('start_date')
        end_date_str = request.form.get('end_date')
        
        try:
            from models import LeaveRequest
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
            
            new_leave = LeaveRequest(
                student_id=current_user.id,
                reason=reason,
                start_date=start_date,
                end_date=end_date
            )
            db.session.add(new_leave)
            db.session.commit()
            flash('Leave request submitted successfully.')
        except ValueError:
            flash('Invalid date format.')
            
    from models import LeaveRequest
    leaves = LeaveRequest.query.filter_by(student_id=current_user.id).order_by(LeaveRequest.created_at.desc()).all()
    return render_template('student_leave.html', leaves=leaves)

@main.route('/student/leave/<int:leave_id>/delete', methods=['POST'])
@login_required
def delete_leave(leave_id):
    if current_user.is_faculty:
        return redirect(url_for('main.dashboard'))
        
    from models import LeaveRequest
    leave = LeaveRequest.query.get_or_404(leave_id)
    
    if leave.student_id != current_user.id:
        from flask import jsonify
        return jsonify({'error': 'Unauthorized'}), 401
        
    db.session.delete(leave)
    db.session.commit()
    flash('Leave request deleted successfully.')
    return redirect(url_for('main.student_leave'))

@main.route('/faculty/leaves')
@login_required
def faculty_leaves():
    if not current_user.is_faculty:
        return redirect(url_for('main.student_dashboard'))
    
    from models import LeaveRequest, Classroom, Student
    # Get all leave requests for students in classrooms managed by this faculty
    leaves = LeaveRequest.query.join(Student).join(Classroom).filter(Classroom.faculty_id == current_user.id).order_by(LeaveRequest.status, LeaveRequest.created_at.desc()).all()
    
    return render_template('faculty_leaves.html', leaves=leaves)

@main.route('/faculty/leave/<int:leave_id>/action', methods=['POST'])
@login_required
def leave_action(leave_id):
    if not current_user.is_faculty:
        return jsonify({'error': 'Unauthorized'}), 401
        
    from models import LeaveRequest
    leave = LeaveRequest.query.get_or_404(leave_id)
    action = request.form.get('action') # 'approve' or 'reject'
    
    if action == 'approve':
        leave.status = 'Approved'
        flash(f'Leave for {leave.student.name} approved.')
    elif action == 'reject':
        leave.status = 'Rejected'
        flash(f'Leave for {leave.student.name} rejected.')
        
    db.session.commit()
    return redirect(url_for('main.faculty_leaves'))

@main.route('/calendar', methods=['GET', 'POST'])
@login_required
def academic_calendar():
    if not current_user.is_faculty:
        return redirect(url_for('main.student_dashboard'))
    
    if request.method == 'POST':
        name = request.form.get('name')
        date_str = request.form.get('date')
        is_holiday = request.form.get('is_holiday') == 'on'
        
        try:
            from models import AcademicEvent
            event_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            new_event = AcademicEvent(name=name, date=event_date, is_holiday=is_holiday)
            db.session.add(new_event)
            db.session.commit()
            flash('Event added to calendar.')
        except ValueError:
            flash('Invalid date.')
            
    from models import AcademicEvent
    events = AcademicEvent.query.order_by(AcademicEvent.date.desc()).all()
    return render_template('academic_calendar.html', events=events)

@main.route('/calendar/delete/<int:event_id>', methods=['POST'])
@login_required
def delete_calendar_event(event_id):
    if not current_user.is_faculty:
        return jsonify({'error': 'Unauthorized'}), 401
    
    from models import AcademicEvent
    event = AcademicEvent.query.get_or_404(event_id)
    db.session.delete(event)
    db.session.commit()
    flash('Event removed from calendar.')
    return redirect(url_for('main.academic_calendar'))

@main.route('/dashboard/analysis')
@login_required
def dashboard_analysis():
    classes = Classroom.query.filter_by(faculty_id=current_user.id).all()
    
    total_students = 0
    total_classes = len(classes)
    risk_counts = {'Low': 0, 'Medium': 0, 'High': 0}
    
    # New Metrics
    # Date Range Filters
    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')
    start_date = None
    end_date = None
    
    if start_date_str:
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        except ValueError: pass
    if end_date_str:
        try:
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        except ValueError: pass

    # Initialize counters
    total_attendance_percentage = 0
    student_count_for_avg = 0
    low_attendance_count = 0
    at_risk_students = []
    avg_attendance = 0

    # ... main iteration ...
    for c in classes:
        total_students += len(c.students)
        for s in c.students:
            # Risk Counts (Always based on overall for consistency)
            if s.risk_level in risk_counts:
                risk_counts[s.risk_level] += 1
            else:
                 risk_counts['Low'] += 1
            
            # Attendance Stats (Filtered)
            pct = get_attendance_percentage(s, start_date, end_date)
            if pct > 0:
                total_attendance_percentage += pct
                student_count_for_avg += 1
            
            if pct < 75:
                low_attendance_count += 1
            
            # Populate Alerts
            if s.risk_level in ['High', 'Medium'] or pct < 75:
                at_risk_students.append({
                    'id': s.id,
                    'name': s.name,
                    'class_name': c.name,
                    'risk_level': s.risk_level,
                    'attendance_pct': round(pct, 1)
                })

    at_risk_students.sort(key=lambda x: x['attendance_pct'])
    avg_attendance = round(total_attendance_percentage / student_count_for_avg, 1) if student_count_for_avg > 0 else 0

    # ... classes_data logic ...
    classes_data = []
    for c in classes:
        c_presents = 0
        c_totals = 0
        for s in c.students:
            # We need to filter attendance records for each student in the class
            for a in s.attendances:
                if start_date and a.date < start_date: continue
                if end_date and a.date > end_date: continue
                c_presents += 1 if a.is_present else 0
                c_totals += 1
        c_avg = (c_presents / c_totals * 100) if c_totals > 0 else 0
        classes_data.append({'name': c.name, 'attendance': round(c_avg, 1)})

    return render_template('dashboard_analysis.html',
                           classes=classes,
                           total_students=total_students,
                           total_classes=total_classes,
                           risk_counts=risk_counts,
                           avg_attendance=avg_attendance,
                           low_attendance_count=low_attendance_count,
                           at_risk_students=at_risk_students,
                           classes_data=classes_data,
                           now=datetime.now())

@main.route('/add_class', methods=['POST'])
@login_required
def add_class():
    name = request.form.get('name')
    if name:
        new_class = Classroom(name=name, faculty_id=current_user.id)
        db.session.add(new_class)
        db.session.commit()
        flash('Class created successfully.')
    return redirect(url_for('main.dashboard'))

@main.route('/class/<int:class_id>/qr')
@login_required
def show_qr(class_id):
    if not current_user.is_faculty:
        return redirect(url_for('main.student_dashboard'))
    
    classroom = Classroom.query.get_or_404(class_id)
    if classroom.faculty_id != current_user.id:
        return redirect(url_for('main.dashboard'))
        
    import random
    
    date_str = request.args.get('date', datetime.today().strftime('%Y-%m-%d'))
    # Accept multiple sessions as a list
    sessions = request.args.getlist('sessions')
    if not sessions:
        # Fallback to single session if provided (backward compatibility), else default to ['Morning']
        legacy_session = request.args.get('session')
        sessions = [legacy_session] if legacy_session else ['Morning']
        
    subject_id = request.args.get('subject_id')
    
    # Generate JWT Token (valid for 10 mins)
    payload = {
        'class_id': class_id,
        'sessions': sessions,
        'subject_id': subject_id,
        'date': date_str,
        'exp': datetime.utcnow() + timedelta(minutes=10),
        'iat': datetime.utcnow()
    }
    token = jwt.encode(payload, current_app.config['SECRET_KEY'], algorithm='HS256')
    
    # Generate deterministic/random 6-digit OTP assigned to this session payload
    pin = str(random.randint(100000, 999999))
    current_app.config['ACTIVE_OTPS'][pin] = payload
    
    return render_template('show_qr.html', 
                           classroom=classroom, 
                           token=token,
                           pin=pin,
                           sessions=sessions,
                           date=date_str,
                           subject_id=subject_id)

@main.route('/class/<int:class_id>/set_location', methods=['POST'])
@login_required
def set_classroom_location(class_id):
    if not current_user.is_faculty:
        return jsonify({'error': 'Unauthorized'}), 401
        
    classroom = Classroom.query.get_or_404(class_id)
    lat = request.form.get('lat')
    lon = request.form.get('lon')
    
    if lat and lon:
        classroom.latitude = float(lat)
        classroom.longitude = float(lon)
        db.session.commit()
        flash('Classroom location updated strictly.')
        
    return redirect(url_for('main.class_view', class_id=class_id))

@main.route('/class/<int:class_id>')
@login_required
def class_view(class_id):
    classroom = Classroom.query.get_or_404(class_id)
    if classroom.faculty_id != current_user.id:
        flash('Unauthorized access.')
        return redirect(url_for('main.dashboard'))
    
    search_query = request.args.get('search', '').strip()
    page = request.args.get('page', 1, type=int)
    
    query = Student.query.filter_by(classroom_id=class_id)
    if search_query:
        query = query.filter(
            (Student.name.ilike(f'%{search_query}%')) | 
            (Student.roll_number.ilike(f'%{search_query}%'))
        )
        
    students = query.order_by(Student.roll_number).paginate(page=page, per_page=15, error_out=False)
        
    return render_template('class_view.html', classroom=classroom, students=students, search_query=search_query)

@main.route('/class/<int:class_id>/add_subject', methods=['POST'])
@login_required
def add_subject(class_id):
    classroom = Classroom.query.get_or_404(class_id)
    if classroom.faculty_id != current_user.id:
        flash('Unauthorized access.')
        return redirect(url_for('main.dashboard'))
    
    name = request.form.get('name')
    if name:
        from models import Subject
        new_subject = Subject(name=name, classroom_id=class_id)
        db.session.add(new_subject)
        db.session.commit()
        flash('Subject added successfully.')
    return redirect(url_for('main.class_view', class_id=class_id))

@main.route('/class/<int:class_id>/delete_subject/<int:subject_id>', methods=['POST'])
@login_required
def delete_subject(class_id, subject_id):
    classroom = Classroom.query.get_or_404(class_id)
    if classroom.faculty_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 401
    
    from models import Subject
    subject = Subject.query.get_or_404(subject_id)
    if subject.classroom_id != class_id:
        return jsonify({'error': 'Invalid subject'}), 400
        
    db.session.delete(subject)
    db.session.commit()
    flash('Subject removed.')
    return redirect(url_for('main.class_view', class_id=class_id))

@main.route('/class/<int:class_id>/analysis')
@login_required
def class_analysis(class_id):
    classroom = Classroom.query.get_or_404(class_id)
    if classroom.faculty_id != current_user.id:
        flash('Unauthorized access.')
        return redirect(url_for('main.dashboard'))
    
    # Date and Subject Filters
    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')
    subject_id_str = request.args.get('subject_id')
    
    start_date = None
    end_date = None
    subject_id = None
    
    if start_date_str:
        try: start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        except ValueError: pass
    if end_date_str:
        try: end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        except ValueError: pass
    if subject_id_str:
        try: subject_id = int(subject_id_str)
        except ValueError: pass

    # Get recent sessions (unique dates) filtered by subject if needed
    recent_sessions_set = set()
    for s in classroom.students:
        for a in s.attendances:
            if start_date and a.date < start_date: continue
            if end_date and a.date > end_date: continue
            if subject_id is not None and a.subject_id != subject_id: continue
            recent_sessions_set.add((a.date, a.session))
            
    # Sort by date desc and take top 5
    recent_sessions_list = sorted(list(recent_sessions_set), key=lambda x: x[0], reverse=True)[:5]
    
    recent_sessions_data = []
    for date_obj, session_name in recent_sessions_list:
        # Calculate presence for this session across all students
        present = 0
        total = 0
        for s in classroom.students:
            # Note: Attendance records are filtered by date, session, and potentially subject
            att_query = Attendance.query.filter_by(student_id=s.id, date=date_obj, session=session_name)
            if subject_id is not None:
                att_query = att_query.filter_by(subject_id=subject_id)
            
            att = att_query.first()
            if att:
                total += 1
                if att.is_present: present += 1
        
        status = 'Present' # Default logic, maybe improve based on %
        if total > 0:
            session_pct = (present / total) * 100
            if session_pct < 50: status = 'Absent' # Low attendance session
            elif session_pct < 80: status = 'Mixed'
            
        recent_sessions_data.append({
            'date': date_obj.strftime('%Y-%m-%d'),
            'session': session_name,
            'status': status,
            'rate': round((present / total * 100), 1) if total > 0 else 0
        })

    total_students = len(classroom.students)
    risk_counts = {'Low': 0, 'Medium': 0, 'High': 0}
    total_attendance_percentage = 0
    student_count_for_avg = 0
    low_attendance_count = 0
    at_risk_students = []

    for s in classroom.students:
        if s.risk_level in risk_counts:
            risk_counts[s.risk_level] += 1
        else:
            risk_counts['Low'] += 1
            
        pct = get_attendance_percentage(s, start_date, end_date, subject_id)
        if pct > 0:
            total_attendance_percentage += pct
            student_count_for_avg += 1
        
        if pct < 75:
            low_attendance_count += 1
            
        if s.risk_level in ['High', 'Medium'] or pct < 75:
            at_risk_students.append({
                'id': s.id,
                'name': s.name,
                'risk_level': s.risk_level,
                'attendance_pct': round(pct, 1)
            })

    # Sort alerts by attendance (lowest first)
    at_risk_students.sort(key=lambda x: x['attendance_pct'])
    avg_attendance = round(total_attendance_percentage / student_count_for_avg, 1) if student_count_for_avg > 0 else 0
            
    return render_template('class_analysis.html', 
                           classroom=classroom,
                           total_students=total_students,
                           risk_counts=risk_counts,
                           avg_attendance=avg_attendance,
                           low_attendance_count=low_attendance_count,
                           at_risk_students=at_risk_students,
                           recent_sessions=recent_sessions_data,
                           today=datetime.now().strftime('%Y-%m-%d'),
                           now=datetime.now())

@main.route('/class/<int:class_id>/add_student', methods=['POST'])
@login_required
def add_student(class_id):
    classroom = Classroom.query.get_or_404(class_id)
    if classroom.faculty_id != current_user.id:
        return redirect(url_for('main.dashboard'))
    
    name = request.form.get('name')
    roll_number = request.form.get('roll_number')
    
    if name and roll_number:
        # Check if roll number exists in this class
        exists = Student.query.filter_by(roll_number=roll_number, classroom_id=class_id).first()
        if exists:
            flash(f'Student with roll number {roll_number} already exists.')
        else:
            from werkzeug.security import generate_password_hash
            # Auto-generate email and default password
            email = f"{roll_number.lower().replace('-', '').replace(' ', '')}@university.edu"
            default_password = generate_password_hash('password123', method='scrypt')
            
            new_student = Student(
                name=name, 
                roll_number=roll_number, 
                email=email,
                password=default_password,
                classroom_id=class_id
            )
            db.session.add(new_student)
            db.session.commit()
            flash(f'Student added successfully. Login: {email}')
            
    return redirect(url_for('main.class_view', class_id=class_id))
            
@main.route('/class/<int:class_id>/mark_attendance', methods=['GET', 'POST'])
@login_required
def mark_attendance(class_id):
    classroom = Classroom.query.get_or_404(class_id)
    if classroom.faculty_id != current_user.id:
        flash('Unauthorized access.')
        return redirect(url_for('main.dashboard'))
    
    if request.method == 'POST':
        date_str = request.form.get('date')
        session = request.form.get('session')
        
        # Convert date string to python date object
        try:
            date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            flash('Invalid date format.')
            return render_template('mark_attendance.html', classroom=classroom, today=date_str, current_session=session, attendance_map={}, selected_subject_id=None)
            
        subject_id = request.form.get('subject_id')
        if subject_id == "": subject_id = None
            
        # Process attendance for each student
        from models import Attendance
        from ml_engine import ml_engine
        
        students = classroom.students
        
        for student in students:
            # Checkbox value will be present ('on') if checked, else None
            is_present = request.form.get(f'student_{student.id}') == 'on'
            
            # Check if attendance already exists for this slot to avoid duplicates
            existing = Attendance.query.filter_by(
                student_id=student.id,
                date=date_obj,
                session=session
            ).first()
            
            if existing:
                existing.is_present = is_present
                existing.subject_id = subject_id
            else:
                new_attendance = Attendance(
                    date=date_obj, 
                    session=session, 
                    is_present=is_present, 
                    student_id=student_id,
                    subject_id=subject_id
                )
                db.session.add(new_attendance)
        
        # Update ML Risk Analysis and Send Notifications
        for student in students:
            ml_engine.update_student_risk(student)
            
            # Real-time absence notification
            is_present = request.form.get(f'student_{student.id}') == 'on'
            if not is_present:
                ml_engine.send_absence_notification(student, date_obj, session)
            
        db.session.commit()
        flash('Attendance recorded successfully.')
        return redirect(url_for('main.class_view', class_id=class_id))
        
    # GET Request: Load layout for specific date/session if provided
    selected_date = request.args.get('date', datetime.today().strftime('%Y-%m-%d'))
    selected_session = request.args.get('session', 'Morning')
    
    try:
        date_obj = datetime.strptime(selected_date, '%Y-%m-%d').date()
    except ValueError:
        date_obj = datetime.today().date()
        selected_date = date_obj.strftime('%Y-%m-%d')

    from models import Attendance, AcademicEvent
    attendance_map = {}
    
    # Check if the selected date is a holiday
    holiday_event = AcademicEvent.query.filter_by(date=date_obj, is_holiday=True).first()
    
    # Pre-fetch attendance for all students in this class/date/session
    # Optimization: fetch all at once instead of in loop
    attendances = Attendance.query.filter_by(
        date=date_obj, 
        session=selected_session
    ).filter(Attendance.student_id.in_([s.id for s in classroom.students])).all()
    
    for att in attendances:
        attendance_map[att.student_id] = {'present': att.is_present, 'status': att.status}
    
    sessions_list = Classroom.query.get(class_id).sessions
    if not sessions_list:
        from models import ClassSession
        db.session.add(ClassSession(name='Morning', classroom_id=class_id))
        db.session.add(ClassSession(name='Afternoon', classroom_id=class_id))
        db.session.commit()
        sessions_list = Classroom.query.get(class_id).sessions

    return render_template('mark_attendance.html', 
                           classroom=classroom, 
                           today=selected_date,
                           current_session=selected_session,
                           attendance_map=attendance_map,
                           sessions=sessions_list,
                           selected_subject_id=None,
                           holiday_event=holiday_event)

@main.route('/class/<int:class_id>/daily', methods=['GET', 'POST'])
@login_required
def daily_attendance(class_id):
    classroom = Classroom.query.get_or_404(class_id)
    if classroom.faculty_id != current_user.id:
        return redirect(url_for('main.dashboard'))
    
    date_str = request.args.get('date', datetime.today().strftime('%Y-%m-%d'))
    selected_subject_id = request.args.get('subject_id', '')
    if selected_subject_id:
        try:
            selected_subject_id = int(selected_subject_id)
        except ValueError:
            selected_subject_id = None
    else:
        selected_subject_id = None

    search_query = request.args.get('search', '').strip()
    
    try:
        date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        date_obj = datetime.today().date()
        date_str = date_obj.strftime('%Y-%m-%d')
    
    # Debug print
    print(f"DEBUG: date_str={date_str}, date_obj={date_obj}, formatted={format_date_with_day(date_obj)}")

    if not classroom.sessions:
        db.session.add(ClassSession(name='Morning', classroom_id=classroom.id))
        db.session.add(ClassSession(name='Afternoon', classroom_id=classroom.id))
        db.session.commit()

    if request.method == 'POST':
        # Bulk save for the whole day
        from models import Attendance
        from ml_engine import ml_engine
        
        subject_id = request.args.get('subject_id')
        if subject_id == "": subject_id = None

        for student in classroom.students:
            for session in classroom.sessions:
                field_name = f'att_{student.id}_{session.id}'
                is_present = request.form.get(field_name) == 'on'
                
                existing = Attendance.query.filter_by(
                    student_id=student.id,
                    date=date_obj,
                    session=session.name,
                    subject_id=subject_id
                ).first()
                
                if existing:
                    existing.is_present = is_present
                else:
                    new_att = Attendance(
                        date=date_obj,
                        session=session.name,
                        is_present=is_present,
                        student_id=student.id,
                        subject_id=subject_id
                    )
                    db.session.add(new_att)
            
            ml_engine.update_student_risk(student)
            
            # Real-time absence notifications (per session)
            for session_obj in classroom.sessions:
                field_name = f'att_{student.id}_{session_obj.id}'
                is_present = request.form.get(field_name) == 'on'
                if not is_present:
                    ml_engine.send_absence_notification(student, date_obj, session_obj.name)
            
        db.session.commit()

        return redirect(url_for('main.daily_attendance', class_id=class_id, date=date_str, subject_id=subject_id or ''))

    # GET logic
    from models import Attendance, AcademicEvent
    
    # Check if the date is a holiday
    holiday_event = AcademicEvent.query.filter_by(date=date_obj, is_holiday=True).first()
    
    students_query = Student.query.filter_by(classroom_id=class_id)
    if search_query:
        students_query = students_query.filter(
            (Student.name.ilike(f'%{search_query}%')) | 
            (Student.roll_number.ilike(f'%{search_query}%'))
        )
    students = students_query.order_by(Student.roll_number).all()
    
    # Pre-fetch all attendance for this class and date and subject
    all_atts = Attendance.query.filter_by(date=date_obj, subject_id=selected_subject_id).filter(
        Attendance.student_id.in_([s.id for s in classroom.students])
    ).all()
    
    # Map: student_id -> {session_name: {'present': bool, 'status': str}}
    att_map = {s.id: {sess.name: {'present': False, 'status': None} for sess in classroom.sessions} for s in classroom.students}
    for a in all_atts:
        if a.student_id in att_map:
            att_map[a.student_id][a.session] = {'present': a.is_present, 'status': a.status}

    return render_template('daily_attendance.html', 
                           classroom=classroom, 
                           date=date_str,
                           date_formatted=format_date_with_day(date_obj),
                           students=students, 
                           att_map=att_map,
                           search_query=search_query,
                           selected_subject_id=selected_subject_id,
                           holiday_event=holiday_event)

@main.route('/class/<int:class_id>/add_session', methods=['POST'])
@login_required
def add_session(class_id):
    classroom = Classroom.query.get_or_404(class_id)
    if classroom.faculty_id != current_user.id: return redirect(url_for('main.dashboard'))
    
    name = request.form.get('session_name')
    start_time_str = request.form.get('start_time')
    end_time_str = request.form.get('end_time')
    
    if name:
        from datetime import datetime
        start_time = datetime.strptime(start_time_str, '%H:%M').time() if start_time_str else None
        end_time = datetime.strptime(end_time_str, '%H:%M').time() if end_time_str else None
        
        new_sess = ClassSession(name=name, classroom_id=class_id, start_time=start_time, end_time=end_time)
        db.session.add(new_sess)
        db.session.commit()
    return redirect(request.referrer or url_for('main.daily_attendance', class_id=class_id))

@main.route('/class/<int:class_id>/rename_session/<int:session_id>', methods=['POST'])
@login_required
def rename_session(class_id, session_id):
    classroom = Classroom.query.get_or_404(class_id)
    if classroom.faculty_id != current_user.id: return redirect(url_for('main.dashboard'))
    
    session = ClassSession.query.get_or_404(session_id)
    new_name = request.form.get('session_name')
    start_time_str = request.form.get('start_time')
    end_time_str = request.form.get('end_time')
    
    if new_name and session.classroom_id == class_id:
        from datetime import datetime
        old_name = session.name
        session.name = new_name
        
        if start_time_str:
            session.start_time = datetime.strptime(start_time_str, '%H:%M').time()
        if end_time_str:
            session.end_time = datetime.strptime(end_time_str, '%H:%M').time()
        
        # Update existing attendance records
        from models import Attendance
        Attendance.query.filter_by(session=old_name).filter(
            Attendance.student_id.in_([s.id for s in classroom.students])
        ).update({Attendance.session: new_name}, synchronize_session=False)
        
        db.session.commit()
    return redirect(request.referrer or url_for('main.daily_attendance', class_id=class_id))

@main.route('/class/<int:class_id>/delete_session/<int:session_id>', methods=['POST'])
@login_required
def delete_session(class_id, session_id):
    classroom = Classroom.query.get_or_404(class_id)
    if classroom.faculty_id != current_user.id: return redirect(url_for('main.dashboard'))
    
    session = ClassSession.query.get_or_404(session_id)
    if session.classroom_id == class_id:
        # Note: We might want to delete attendance too or keep it? 
        # Usually deleting a session implies its data is gone.
        from models import Attendance
        Attendance.query.filter_by(session=session.name).filter(
            Attendance.student_id.in_([s.id for s in classroom.students])
        ).delete(synchronize_session=False)
        
        db.session.delete(session)
        db.session.commit()
        flash (f'Session "{session.name}" deleted.')
    return redirect(request.referrer or url_for('main.daily_attendance', class_id=class_id))

@main.route('/class/<int:class_id>/report')
@login_required
def class_report(class_id):
    classroom = Classroom.query.get_or_404(class_id)
    if classroom.faculty_id != current_user.id:
        flash('Unauthorized access.')
        return redirect(url_for('main.dashboard'))
    
    from models import Attendance
    
    # 1. Calculate Student Stats
    students_data = []
    total_sessions_query = db.session.query(Attendance.date, Attendance.session).filter(
        Attendance.student_id.in_([s.id for s in classroom.students])
    ).distinct().all()
    
    total_sessions = len(total_sessions_query)
    
    for s in classroom.students:
        present_count = sum(1 for a in s.attendances if a.is_present)
        pct = round((present_count / total_sessions * 100), 1) if total_sessions > 0 else 0
        
        students_data.append({
            'name': s.name,
            'roll_number': s.roll_number,
            'present_count': present_count,
            'percentage': pct,
            'risk': s.risk_level
        })
        
    # 2. Calculate Session Stats
    sessions_data = []
    # Sort sessions by date desc
    sorted_sessions = sorted(total_sessions_query, key=lambda x: x[0], reverse=True)
    
    total_students = len(classroom.students)
    
    for date_obj, session_name in sorted_sessions:
        present_in_session = 0
        for s in classroom.students:
            att = Attendance.query.filter_by(student_id=s.id, date=date_obj, session=session_name).first()
            if att and att.is_present:
                present_in_session += 1
                
        rate = round((present_in_session / total_students * 100), 1) if total_students > 0 else 0
        
        sessions_data.append({
            'date': format_date_short(date_obj),
            'name': session_name,
            'present_count': present_in_session,
            'rate': rate
        })
        
    # Calculate class average attendance
    total_pct = sum(s['percentage'] for s in students_data)
    avg_attendance = round(total_pct / len(students_data), 1) if len(students_data) > 0 else 0
        
    return render_template('report.html',
                           classroom=classroom,
                           students_data=students_data,
                           sessions_data=sessions_data,
                           total_students=total_students,
                           total_sessions=total_sessions,
                           avg_attendance=avg_attendance,
                           generation_date=format_date_with_day(datetime.now()))

@main.route('/delete_class/<int:class_id>', methods=['POST'])
@login_required
def delete_class(class_id):
    classroom = Classroom.query.get_or_404(class_id)
    if classroom.faculty_id != current_user.id:
        flash('Unauthorized action.')
        return redirect(url_for('main.dashboard'))
    
    # Manually delete dependencies since we didn't set up cascade delete
    # Delete sessions first
    for session in classroom.sessions:
        db.session.delete(session)
    
    # Delete students and their attendance
    for student in classroom.students:
        for attendance in student.attendances:
            db.session.delete(attendance)
        db.session.delete(student)
            
    db.session.delete(classroom)
    db.session.commit()
    flash('Class deleted successfully.')
    return redirect(url_for('main.dashboard'))

@main.route('/student/<int:student_id>/analysis')
@login_required
def student_analysis(student_id):
    student = Student.query.get_or_404(student_id)
    if student.classroom.faculty_id != current_user.id:
        flash('Unauthorized access.')
        return redirect(url_for('main.dashboard'))
        
    from ml_engine import ml_engine
    metrics = ml_engine.get_student_metrics(student)
    
    return render_template('student_analysis.html', student=student, metrics=metrics)

@main.route('/class/<int:class_id>/delete_student/<int:student_id>', methods=['POST'])
@login_required
def delete_student(class_id, student_id):
    classroom = Classroom.query.get_or_404(class_id)
    if classroom.faculty_id != current_user.id:
        return redirect(url_for('main.dashboard'))
        
    student = Student.query.get_or_404(student_id)
    if student.classroom_id != class_id:
        flash('Student not found in this class.')
        return redirect(url_for('main.class_view', class_id=class_id))
        
    for attendance in student.attendances:
        db.session.delete(attendance)
        
    db.session.delete(student)
    db.session.commit()
    flash('Student removed successfully.')
    return redirect(url_for('main.class_view', class_id=class_id))

@main.route('/api/stats')
@token_required
def api_stats(current_user):
    return jsonify({
        'user': {
            'name': current_user.name,
            'type': 'faculty' if hasattr(current_user, 'classes') else 'student'
        },
        'status': 'success'
    })

@main.route('/migrate_students')
@login_required
def migrate_students():
    if not current_user.is_faculty:
        return redirect(url_for('main.student_dashboard'))
    
    from werkzeug.security import generate_password_hash
    students = Student.query.all()
    updated_count = 0
    
    for student in students:
        needs_update = False
        if not student.email:
            student.email = f"{student.roll_number.lower().replace('-', '').replace(' ', '')}@university.edu"
            needs_update = True
        if not student.password:
            student.password = generate_password_hash('password123', method='scrypt')
            needs_update = True
        
        if needs_update:
            updated_count += 1
            
    if updated_count > 0:
        db.session.commit()
        flash(f'Provisioned accounts for {updated_count} existing students.')
    else:
        flash('All students already have accounts.')
        
    return redirect(url_for('main.dashboard'))

@main.route('/api/classes/<int:class_id>/export', methods=['GET'])
@token_required
def export_class_csv(current_user, class_id):
    if not current_user.is_faculty:
        return jsonify({'error': 'Unauthorized'}), 403
    classroom = Classroom.query.get_or_404(class_id)
    if classroom.faculty_id != current_user.id:
        return jsonify({'error': 'Unauthorized access'}), 403
    
    import csv
    import io
    from flask import Response
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Header
    writer.writerow(['Student Name', 'Roll Number', 'Email', 'Total Sessions', 'Present Count', 'Attendance %', 'Risk Level'])
    
    def calculate_stats(student):
        total = len(student.attendances)
        present = sum(1 for a in student.attendances if a.is_present)
        pct = round((present / total * 100), 1) if total > 0 else 0
        return total, present, pct

    for student in classroom.students:
        total, present, pct = calculate_stats(student)
        writer.writerow([
            student.name,
            student.roll_number,
            student.email or 'N/A',
            total,
            present,
            f"{pct}%",
            student.risk_level
        ])
    
    output.seek(0)
    
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-disposition": f"attachment; filename={classroom.name.replace(' ', '_')}_Attendance.csv"}
    )


@main.route('/api/student/dashboard', methods=['GET'])
@token_required
def api_student_dashboard(current_user):
    if current_user.is_faculty:
        return jsonify({'error': 'Unauthorized'}), 403
    
    from ml_engine import ml_engine
    metrics = ml_engine.get_student_metrics(current_user)
    
    return jsonify({
        'name': current_user.name,
        'roll_number': current_user.roll_number,
        'risk_level': current_user.risk_level,
        'metrics': metrics
    })

@main.route('/api/student/attendance', methods=['GET'])
@token_required
def api_student_attendance(current_user):
    if current_user.is_faculty:
        return jsonify({'error': 'Unauthorized'}), 403
        
    history = sorted(current_user.attendances, key=lambda x: (x.date, x.session), reverse=True)
    
    return jsonify([{
        'date': a.date.strftime('%Y-%m-%d'),
        'session': a.session,
        'status': 'Present' if a.is_present else 'Absent'
    } for a in history])

# --- NEW API ENDPOINTS FOR PHASE 2 FRONTEND ---

@main.route('/api/classes', methods=['GET', 'POST'])
@token_required
def api_classes(current_user):
    if not current_user.is_faculty:
        return jsonify({'error': 'Unauthorized'}), 403
        
    if request.method == 'POST':
        data = request.get_json()
        if not data or not data.get('name'):
            return jsonify({'error': 'Missing class name'}), 400
        
        new_class = Classroom(name=data['name'], faculty_id=current_user.id)
        db.session.add(new_class)
        db.session.commit()
        return jsonify({'id': new_class.id, 'name': new_class.name, 'student_count': 0}), 201
    
    classes = Classroom.query.filter_by(faculty_id=current_user.id).all()
    return jsonify([{
        'id': c.id, 
        'name': c.name, 
        'student_count': len(c.students)
    } for c in classes])

@main.route('/api/classes/<int:class_id>', methods=['GET', 'DELETE'])
@token_required
def api_class_detail(current_user, class_id):
    classroom = Classroom.query.get_or_404(class_id)
    if classroom.faculty_id != current_user.id:
        return jsonify({'error': 'Unauthorized access'}), 403
        
    if request.method == 'DELETE':
        # Reuse existing delete logic structure or just simplify for API
        for session in classroom.sessions: db.session.delete(session)
        for student in classroom.students:
            for att in student.attendances: db.session.delete(att)
            db.session.delete(student)
        db.session.delete(classroom)
        db.session.commit()
        return jsonify({'message': 'Class deleted successfully'})

    return jsonify({
        'id': classroom.id,
        'name': classroom.name,
        'students': [{
            'id': s.id,
            'name': s.name,
            'roll_number': s.roll_number,
            'risk_level': s.risk_level or 'Low'
        } for s in classroom.students]
    })

@main.route('/api/classes/<int:class_id>/students', methods=['POST'])
@token_required
def api_add_student(current_user, class_id):
    classroom = Classroom.query.get_or_404(class_id)
    if classroom.faculty_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
        
    data = request.get_json()
    if not data or not data.get('name') or not data.get('roll_number'):
        return jsonify({'error': 'Missing student details'}), 400
        
    # Check duplicate
    exists = Student.query.filter_by(roll_number=data['roll_number'], classroom_id=class_id).first()
    if exists:
        return jsonify({'error': f"Student {data['roll_number']} already exists"}), 400
        
    from werkzeug.security import generate_password_hash
    email = f"{data['roll_number'].lower().replace('-', '').replace(' ', '')}@university.edu"
    default_pw = generate_password_hash('password123', method='scrypt')
    
    new_student = Student(
        name=data['name'], 
        roll_number=data['roll_number'], 
        email=email,
        password=default_pw,
        classroom_id=class_id
    )
    db.session.add(new_student)
    db.session.commit()
    return jsonify({'id': new_student.id, 'name': new_student.name, 'roll_number': new_student.roll_number}), 201

@main.route('/api/classes/<int:class_id>/students/<int:student_id>', methods=['DELETE'])
@token_required
def api_delete_student(current_user, class_id, student_id):
    classroom = Classroom.query.get_or_404(class_id)
    if classroom.faculty_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
        
    student = Student.query.get_or_404(student_id)
    if student.classroom_id != class_id:
        return jsonify({'error': 'Student not in this class'}), 404
        
    for att in student.attendances: db.session.delete(att)
    db.session.delete(student)
    db.session.commit()
    return jsonify({'message': 'Student removed'})

@main.route('/api/classes/<int:class_id>/students/import', methods=['POST'])
@token_required
def api_import_students(current_user, class_id):
    classroom = Classroom.query.get_or_404(class_id)
    if classroom.faculty_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
        
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
        
    file = request.files['file']
    if not file.filename.endswith('.csv'):
        return jsonify({'error': 'File must be a CSV'}), 400
        
    import csv
    import io
    from werkzeug.security import generate_password_hash
    
    stream = io.StringIO(file.stream.read().decode("UTF8"), newline=None)
    csv_input = csv.DictReader(stream)
    
    # Try to handle common variations of headers
    added = 0
    errors = []
    
    for row in csv_input:
        name = row.get('Name') or row.get('name') or row.get('Student Name')
        roll = row.get('RollNumber') or row.get('roll_number') or row.get('Roll No')
        
        if not name or not roll: continue
        
        exists = Student.query.filter_by(roll_number=roll, classroom_id=class_id).first()
        if not exists:
            email = f"{roll.lower().replace('-', '').replace(' ', '')}@university.edu"
            new_student = Student(
                name=name, roll_number=roll, email=email,
                password=generate_password_hash('password123', method='scrypt'),
                classroom_id=class_id
            )
            db.session.add(new_student)
            added += 1
            
    db.session.commit()
    return jsonify({'message': f"Successfully imported {added} students", 'count': added})

@main.route('/api/classes/<int:class_id>/sessions', methods=['GET'])
@token_required
def api_sessions(current_user, class_id):
    classroom = Classroom.query.get_or_404(class_id)
    if classroom.faculty_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
        
    # Return custom sessions or defaults if none exist
    if not classroom.sessions:
        return jsonify([{'id': 1, 'name': 'Morning'}, {'id': 2, 'name': 'Afternoon'}])
        
    return jsonify([{'id': s.id, 'name': s.name} for s in classroom.sessions])

@main.route('/api/classes/<int:class_id>/attendance', methods=['GET'])
@token_required
def api_get_attendance(current_user, class_id):
    classroom = Classroom.query.get_or_404(class_id)
    if classroom.faculty_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
        
    date_str = request.args.get('date', datetime.today().strftime('%Y-%m-%d'))
    try:
        date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
    except:
        return jsonify({'error': 'Invalid date format'}), 400
        
    from models import Attendance
    atts = Attendance.query.filter_by(date=date_obj).filter(
        Attendance.student_id.in_([s.id for s in classroom.students])
    ).all()
    
    # Map: student_id -> {session_name: is_present}
    res = {}
    for a in atts:
        if a.student_id not in res: res[a.student_id] = {}
        res[a.student_id][a.session] = a.is_present
        
    return jsonify({'attendance': res})

@main.route('/api/classes/<int:class_id>/attendance/daily', methods=['POST'])
@token_required
def api_save_attendance(current_user, class_id):
    classroom = Classroom.query.get_or_404(class_id)
    if classroom.faculty_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
        
    data = request.get_json()
    if not data or not data.get('date') or not data.get('attendance'):
        return jsonify({'error': 'Missing data'}), 400
        
    date_str = data['date']
    try:
        date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
    except:
        return jsonify({'error': 'Invalid date format'}), 400
        
    from models import Attendance
    from ml_engine import ml_engine
    
    # attendance map: { studentId: { sessionName: boolean } }
    att_map = data['attendance']
    for student_id_str, sessions in att_map.items():
        sid = int(student_id_str)
        student = Student.query.get(sid)
        if not student or student.classroom_id != class_id: continue
        
        for sess_name, is_present in sessions.items():
            existing = Attendance.query.filter_by(student_id=sid, date=date_obj, session=sess_name).first()
            if existing:
                existing.is_present = is_present
            else:
                db.session.add(Attendance(student_id=sid, date=date_obj, session=sess_name, is_present=is_present))
                
        # Risk update
        ml_engine.update_student_risk(student)
        
    db.session.commit()
    return jsonify({'message': 'Attendance saved'})

@main.route('/api/dashboard/analysis', methods=['GET'])
@token_required
def api_dashboard_analysis(current_user):
    if not current_user.is_faculty:
        return jsonify({'error': 'Unauthorized'}), 403
        
    classes = Classroom.query.filter_by(faculty_id=current_user.id).all()
    
    total_students = 0
    risk_counts = {'Low': 0, 'Medium': 0, 'High': 0}
    total_attendance_percentage = 0
    student_count_for_avg = 0
    low_attendance_count = 0
    at_risk_students = []
    classes_data = []

    def calc_pct(student):
        total = len(student.attendances)
        if total == 0: return 0
        return (sum(1 for a in student.attendances if a.is_present) / total) * 100

    for c in classes:
        c_presents = 0
        c_totals = 0
        total_students += len(c.students)
        
        for s in c.students:
            risk = s.risk_level or 'Low'
            risk_counts[risk] = risk_counts.get(risk, 0) + 1
            
            pct = calc_pct(s)
            if len(s.attendances) > 0:
                total_attendance_percentage += pct
                student_count_for_avg += 1
            if pct < 75 and len(s.attendances) > 0:
                low_attendance_count += 1
            
            if risk in ['High', 'Medium'] or (pct < 75 and len(s.attendances) > 0):
                at_risk_students.append({
                    'name': s.name,
                    'class_name': c.name,
                    'attendance_pct': round(pct, 1),
                    'risk_level': risk
                })
            
            c_presents += sum(1 for a in s.attendances if a.is_present)
            c_totals += len(s.attendances)
            
        c_avg = (c_presents / c_totals * 100) if c_totals > 0 else 0
        classes_data.append({'name': c.name, 'attendance': round(c_avg, 1)})

    avg_attendance = round(total_attendance_percentage / student_count_for_avg, 1) if student_count_for_avg > 0 else 0
    at_risk_students.sort(key=lambda x: x['attendance_pct'])

    return jsonify({
        'total_students': total_students,
        'avg_attendance': avg_attendance,
        'low_attendance_count': low_attendance_count,
        'risk_counts': risk_counts,
        'at_risk_students': at_risk_students,
        'classes_data': classes_data
    })

@main.route('/api/classes/<int:class_id>/analysis', methods=['GET'])
@token_required
def api_class_analysis(current_user, class_id):
    classroom = Classroom.query.get_or_404(class_id)
    if classroom.faculty_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
        
    total_students = len(classroom.students)
    if total_students == 0:
        return jsonify({
            'name': classroom.name,
            'avg_attendance': 0,
            'risk_counts': {'Low': 0, 'Medium': 0, 'High': 0},
            'trend': []
        })

    # Calculations
    presents = 0
    totals = 0
    risk_counts = {'Low': 0, 'Medium': 0, 'High': 0}
    
    for s in classroom.students:
        risk = s.risk_level or 'Low'
        risk_counts[risk] = risk_counts.get(risk, 0) + 1
        presents += sum(1 for a in s.attendances if a.is_present)
        totals += len(s.attendances)
        
    avg_attendance = round((presents / totals * 100), 1) if totals > 0 else 0
    
    # Recent sessions trend
    # Get last 10 unique dates/sessions
    from models import Attendance
    recent_atts = Attendance.query.filter(
        Attendance.student_id.in_([s.id for s in classroom.students])
    ).order_by(Attendance.date.desc(), Attendance.session.desc()).limit(10 * total_students).all()
    
    # Group by date/session
    sessions_data = {}
    for a in recent_atts:
        key = (a.date.isoformat(), a.session)
        if key not in sessions_data: sessions_data[key] = {'presents': 0, 'total': 0}
        if a.is_present: sessions_data[key]['presents'] += 1
        sessions_data[key]['total'] += 1
        
    trend = []
    for (date, sess), vals in sorted(sessions_data.items(), reverse=True)[:10]:
        trend.append({
            'date': date,
            'session': sess,
            'rate': round((vals['presents'] / vals['total'] * 100), 1) if vals['total'] > 0 else 0
        })

    return jsonify({
        'name': classroom.name,
        'avg_attendance': avg_attendance,
        'total_students': total_students,
        'risk_counts': risk_counts,
        'trend': trend[::-1] # chronological
    })

@main.route('/api/students/<int:student_id>/analysis', methods=['GET'])
@token_required
def api_student_analysis(current_user, student_id):
    student = Student.query.get_or_404(student_id)
    # Faculty can see their own students
    if current_user.is_faculty:
        if student.classroom.faculty_id != current_user.id:
            return jsonify({'error': 'Unauthorized'}), 403
    else:
        # Student can only see themselves
        if student.id != current_user.id:
            return jsonify({'error': 'Unauthorized'}), 403
            
    total = len(student.attendances)
    present = sum(1 for a in student.attendances if a.is_present)
    pct = round((present / total * 100), 1) if total > 0 else 0
    
    history = [{
        'date': a.date.isoformat(),
        'session': a.session,
        'is_present': a.is_present
    } for a in sorted(student.attendances, key=lambda x: (x.date, x.session), reverse=True)]
    
    return jsonify({
        'id': student.id,
        'name': student.name,
        'roll_number': student.roll_number,
        'class_name': student.classroom.name,
        'attendance_pct': pct,
        'risk_level': student.risk_level or 'Low',
        'history': history[:20] # Last 20
    })

@main.route('/api/classes/<int:class_id>/export', methods=['GET'])
@token_required
def api_export_class(current_user, class_id):
    classroom = Classroom.query.get_or_404(class_id)
    if classroom.faculty_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
        
    import io
    import csv
    from flask import Response
    
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Roll Number', 'Name', 'Attendance %', 'Risk Level'])
    
    for s in classroom.students:
        total = len(s.attendances)
        present = sum(1 for a in s.attendances if a.is_present)
        pct = round((present / total * 100), 1) if total > 0 else 0
        writer.writerow([s.roll_number, s.name, f"{pct}%", s.risk_level or 'Low'])
        
    res = Response(output.getvalue(), mimetype="text/csv")
    res.headers["Content-Disposition"] = f"attachment; filename={classroom.name}_report.csv"
    return res

@main.route('/api/verify_check_in', methods=['POST'])
@login_required
def verify_check_in():
    if current_user.is_faculty:
        return jsonify({'error': 'Faculty cannot check-in'}), 403
        
    data = request.json
    token = data.get('token')
    pin = data.get('pin')
    lat = data.get('lat')
    lon = data.get('lon')
    
    if not token and not pin:
        return jsonify({'error': 'No QR token or PIN provided'}), 400
        
    try:
        # 1. Decode payload from token OR lookup via PIN
        if token:
            payload = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=['HS256'])
        else:
            payload = current_app.config.get('ACTIVE_OTPS', {}).get(pin)
            if not payload:
                return jsonify({'error': 'Invalid or expired PIN'}), 401
            # Check expiration locally since JWT handles it implicitly
            if datetime.utcnow() > payload['exp']:
                return jsonify({'error': 'PIN code has expired'}), 401
                
        class_id = payload['class_id']
        # Handle new format (sessions list) and legacy format (session string)
        sessions_to_mark = payload.get('sessions', [])
        if not sessions_to_mark and 'session' in payload:
            sessions_to_mark = [payload['session']]
            
        subject_id = payload.get('subject_id')
        date_str = payload['date']
        date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
        
        classroom = Classroom.query.get(class_id)
        
        # 2. GPS Verification (if classroom has location set)
        if classroom.latitude and classroom.longitude:
            if not lat or not lon:
                return jsonify({'error': 'GPS coordinates required for this class'}), 400
            
            dist = haversine_distance(float(lat), float(lon), classroom.latitude, classroom.longitude)
            if dist > 50: # 50 meters
                return jsonify({'error': f'You are too far from the classroom ({round(dist)}m)'}), 403
        
        from models import Attendance
        marked_sessions = []
        already_marked_sessions = []
        
        for session_name in sessions_to_mark:
            # 3. Check for replay/duplicate per session
            existing = Attendance.query.filter_by(
                student_id=current_user.id,
                date=date_obj,
                session=session_name,
                subject_id=subject_id
            ).first()
            
            if existing and existing.is_present:
                already_marked_sessions.append(session_name)
                continue
                
            # 4. Late Detection
            now = datetime.now()
            status = 'Present'
            
            from models import ClassSession
            session_obj = ClassSession.query.filter_by(classroom_id=classroom.id, name=session_name).first()
            if session_obj and session_obj.start_time:
                # threshold is 15 mins after start time
                threshold_dt = datetime.combine(date_obj, session_obj.start_time) + timedelta(minutes=15)
                if now > threshold_dt:
                    status = 'Late'

            # 5. Mark Attendance
            if existing:
                existing.is_present = True
                existing.status = status
                existing.check_in_time = now
                existing.verification_type = 'QR+GPS' if lat else 'QR'
                existing.gps_lat = lat
                existing.gps_long = lon
            else:
                new_att = Attendance(
                    student_id=current_user.id,
                    date=date_obj,
                    session=session_name,
                    is_present=True,
                    status=status,
                    check_in_time=now,
                    subject_id=subject_id,
                    verification_type='QR+GPS' if lat else 'QR',
                    gps_lat=lat,
                    gps_long=lon
                )
                db.session.add(new_att)
            marked_sessions.append(f"{session_name} ({status})")
            
        db.session.commit()
        
        # Update risk level via ML Engine
        from ml_engine import ml_engine
        # Re-fetch student to ensure session is active
        from models import Student
        student = Student.query.get(current_user.id)
        ml_engine.update_student_risk(student)
        db.session.commit()
        
        if not marked_sessions:
            return jsonify({'message': f'Attendance already marked for {", ".join(already_marked_sessions)}.'}), 200
            
        msg = f"Attendance marked for {', '.join(marked_sessions)}."
        if already_marked_sessions:
            msg += f" (Already marked for {', '.join(already_marked_sessions)})."
            
        return jsonify({'message': msg, 'status': 'success'}), 200
        
    except jwt.ExpiredSignatureError:
        return jsonify({'error': 'QR code has expired'}), 401
    except jwt.InvalidTokenError:
        return jsonify({'error': 'Invalid QR code'}), 401
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@main.route('/student/check_in')
@login_required
def student_check_in():
    if current_user.is_faculty:
        return redirect(url_for('main.dashboard'))
    return render_template('student_check_in.html')
