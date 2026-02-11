from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from models import Classroom, Student
from extensions import db
from datetime import datetime

main = Blueprint('main', __name__)

@main.route('/')
def index():
    if current_user.is_authenticated:
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

@main.route('/dashboard/analysis')
@login_required
def dashboard_analysis():
    classes = Classroom.query.filter_by(faculty_id=current_user.id).all()
    
    total_students = 0
    total_classes = len(classes)
    risk_counts = {'Low': 0, 'Medium': 0, 'High': 0}
    
    # New Metrics
    total_attendance_percentage = 0
    student_count_for_avg = 0
    low_attendance_count = 0 # < 75%
    at_risk_students = []
    
    # Helper to calculate student attendance %
    def calculate_attendance_pct(student):
        total_sessions = len(student.attendances)
        if total_sessions == 0: return 0
        present_count = sum(1 for a in student.attendances if a.is_present)
        return (present_count / total_sessions) * 100

    for c in classes:
        total_students += len(c.students)
        for s in c.students:
            # Risk Counts
            if s.risk_level in risk_counts:
                risk_counts[s.risk_level] += 1
            else:
                 risk_counts['Low'] += 1
            
            # Attendance Stats
            pct = calculate_attendance_pct(s)
            if pct > 0:
                total_attendance_percentage += pct
                student_count_for_avg += 1
            
            if pct < 75:
                low_attendance_count += 1
            
            # Populate Alerts (High Risk or Low Attendance)
            if s.risk_level == 'High' or pct < 60:
                at_risk_students.append({
                    'name': s.name,
                    'class_name': c.name,
                    'risk_level': s.risk_level,
                    'attendance_pct': round(pct, 1)
                })

    avg_attendance = round(total_attendance_percentage / student_count_for_avg, 1) if student_count_for_avg > 0 else 0
        
    return render_template('dashboard_analysis.html',
                           classes=classes,
                           total_students=total_students,
                           total_classes=total_classes,
                           risk_counts=risk_counts,
                           avg_attendance=avg_attendance,
                           low_attendance_count=low_attendance_count,
                           at_risk_students=at_risk_students)

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

@main.route('/class/<int:class_id>')
@login_required
def class_view(class_id):
    classroom = Classroom.query.get_or_404(class_id)
    if classroom.faculty_id != current_user.id:
        flash('Unauthorized access.')
        return redirect(url_for('main.dashboard'))
    
    return render_template('class_view.html', classroom=classroom)

@main.route('/class/<int:class_id>/analysis')
@login_required
def class_analysis(class_id):
    classroom = Classroom.query.get_or_404(class_id)
    if classroom.faculty_id != current_user.id:
        flash('Unauthorized access.')
        return redirect(url_for('main.dashboard'))
    
    total_students = len(classroom.students)
    risk_counts = {'Low': 0, 'Medium': 0, 'High': 0}
    
    # Metrics
    total_attendance_percentage = 0
    student_count_for_avg = 0
    low_attendance_count = 0
    at_risk_students = []
    
    def calculate_attendance_pct(student):
        total_sessions = len(student.attendances)
        if total_sessions == 0: return 0
        present_count = sum(1 for a in student.attendances if a.is_present)
        return (present_count / total_sessions) * 100

    from models import Attendance
    # Get recent sessions (unique dates)
    # This is a bit inefficient but works for small scale. 
    # Use a set to track unique (date, session) tuples
    recent_sessions_set = set()
    for s in classroom.students:
        for a in s.attendances:
            recent_sessions_set.add((a.date, a.session))
            
    # Sort by date desc and take top 5
    recent_sessions_list = sorted(list(recent_sessions_set), key=lambda x: x[0], reverse=True)[:5]
    
    recent_sessions_data = []
    for date_obj, session_name in recent_sessions_list:
        # Calculate presence for this session across all students
        present = 0
        total = 0
        for s in classroom.students:
            att = Attendance.query.filter_by(student_id=s.id, date=date_obj, session=session_name).first()
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
            'status': status
        })

    for s in classroom.students:
        if s.risk_level in risk_counts:
            risk_counts[s.risk_level] += 1
        else:
            risk_counts['Low'] += 1
            
        pct = calculate_attendance_pct(s)
        if pct > 0:
            total_attendance_percentage += pct
            student_count_for_avg += 1
        
        if pct < 75:
            low_attendance_count += 1
            
        if s.risk_level == 'High' or pct < 60:
            at_risk_students.append({
                'name': s.name,
                'risk_level': s.risk_level,
                'attendance_pct': round(pct, 1)
            })

    avg_attendance = round(total_attendance_percentage / student_count_for_avg, 1) if student_count_for_avg > 0 else 0
            
    return render_template('class_analysis.html', 
                           classroom=classroom,
                           total_students=total_students,
                           risk_counts=risk_counts,
                           avg_attendance=avg_attendance,
                           low_attendance_count=low_attendance_count,
                           at_risk_students=at_risk_students,
                           recent_sessions=recent_sessions_data)

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
            new_student = Student(name=name, roll_number=roll_number, classroom_id=class_id)
            db.session.add(new_student)
            db.session.commit()
            flash('Student added successfully.')
            
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
            flash('Invalid date format.')
            return render_template('mark_attendance.html', classroom=classroom, today=date_str, current_session=session, attendance_map={})
            
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
            else:
                new_attendance = Attendance(
                    date=date_obj, 
                    session=session, 
                    is_present=is_present, 
                    student_id=student.id
                )
                db.session.add(new_attendance)
        
        # Update ML Risk Analysis
        for student in students:
            ml_engine.update_student_risk(student)
            
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

    from models import Attendance
    attendance_map = {}
    
    # Pre-fetch attendance for all students in this class/date/session
    # Optimization: fetch all at once instead of in loop
    attendances = Attendance.query.filter_by(
        date=date_obj, 
        session=selected_session
    ).filter(Attendance.student_id.in_([s.id for s in classroom.students])).all()
    
    for att in attendances:
        attendance_map[att.student_id] = att.is_present

    return render_template('mark_attendance.html', 
                           classroom=classroom, 
                           today=selected_date,
                           current_session=selected_session,
                           attendance_map=attendance_map)

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
            'date': date_obj.strftime('%Y-%m-%d'),
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
                           generation_date=datetime.now().strftime('%Y-%m-%d %H:%M'))

@main.route('/delete_class/<int:class_id>', methods=['POST'])
@login_required
def delete_class(class_id):
    classroom = Classroom.query.get_or_404(class_id)
    if classroom.faculty_id != current_user.id:
        flash('Unauthorized action.')
        return redirect(url_for('main.dashboard'))
    
    # Manually delete dependencies since we didn't set up cascade delete
    for student in classroom.students:
        for attendance in student.attendances:
            db.session.delete(attendance)
        db.session.delete(student)
            
    db.session.delete(classroom)
    db.session.commit()
    flash('Class deleted successfully.')
    return redirect(url_for('main.dashboard'))

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
