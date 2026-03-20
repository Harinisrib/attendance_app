import numpy as np
import pandas as pd
from flask import current_app
from flask_mail import Message
from extensions import db, mail
import threading

class MLEngine:
    def update_student_risk(self, student):
        """
        Analyzes a student's attendance history and updates their risk level in the DB.
        """
        history = student.attendances
        
        from models import LeaveRequest
        approved_leaves = LeaveRequest.query.filter_by(student_id=student.id, status='Approved').all()
        
        def is_on_leave(date_obj):
            for leave in approved_leaves:
                if leave.start_date <= date_obj <= leave.end_date:
                    return True
            return False

        relevant_history = [a for a in history if not is_on_leave(a.date)]
        
        if not relevant_history:
            student.risk_level = 'Low'
            return
        
        total_sessions = len(relevant_history)
        present_sessions = sum(1 for a in relevant_history if a.is_present)
        late_sessions = sum(1 for a in relevant_history if a.is_present and a.status == 'Late')
        
        # Heuristic: 3 Lates count as 1 Absent for risk calculation
        adjusted_present = present_sessions - (late_sessions // 3)
        attendance_percentage = (adjusted_present / total_sessions) * 100
        
        # Rule-based classification
        new_risk = 'Low'
        if attendance_percentage < 60:
            new_risk = 'High'
        elif attendance_percentage < 75:
            new_risk = 'Medium'
            
        old_risk = student.risk_level
        student.risk_level = new_risk

        if new_risk == 'High' and old_risk != 'High':
            self.send_risk_alert_email(student, attendance_percentage)
            
        # Note: commit should be handled by caller or here if standalone
        # db.session.add(student) # Already in session

    def send_async_email(self, app, msg):
        with app.app_context():
            try:
                mail.send(msg)
                print(f"Async email sent to {msg.recipients[0]}")
            except Exception as e:
                print(f"Failed to send email to {msg.recipients[0]}: {e}")

    def send_risk_alert_email(self, student, attendance_percentage):
        if not student.email: return
        
        app = current_app._get_current_object()
        msg = Message(
            subject=f"URGENT: High Risk Attendance Alert for {student.name}",
            recipients=[student.email]
        )
        msg.body = f"""Dear {student.name},

You are receiving this automated alert because your attendance has dropped to {attendance_percentage:.1f}%.
This places you in the HIGH RISK category for this class. 

Please contact your faculty instructor immediately to discuss your attendance standing.

Regards,
Attendance Tracking System
"""
        thr = threading.Thread(target=self.send_async_email, args=[app, msg])
        thr.start()

    def send_absence_notification(self, student, date_obj, session_name):
        if not student.email: return
        
        app = current_app._get_current_object()
        msg = Message(
            subject=f"Update: Absence Recorded - {date_obj.strftime('%b %d')}",
            recipients=[student.email]
        )
        msg.body = f"""Dear {student.name},

This is an automated notification to inform you that you have been marked ABSENT for the {session_name} session on {date_obj.strftime('%A, %b %d, %Y')}.

If you believe this is an error, please contact your faculty instructor.

Regards,
Attendance Tracking System
"""
        thr = threading.Thread(target=self.send_async_email, args=[app, msg])
        thr.start()

    def get_class_analytics(self, classroom):
        """
        Returns stats for dashboard visualization.
        """
        students = classroom.students
        if not students:
            return {'avg_attendance': 0, 'risk_counts': {'Low':0, 'Medium':0, 'High':0}}
            
        total_present = 0
        total_sessions = 0
        risk_counts = {'Low': 0, 'Medium': 0, 'High': 0}
        
        for s in students:
            risk_counts[s.risk_level] += 1
            s_history = s.attendances
            if s_history:
                total_present += sum(1 for a in s_history if a.is_present)
                total_sessions += len(s_history)
                
        avg_attendance = (total_present / total_sessions * 100) if total_sessions > 0 else 0
        
        return {
            'avg_attendance': round(avg_attendance, 1),
            'risk_counts': risk_counts
        }

    def get_student_metrics(self, student):
        """
        Calculates advanced metrics for a single student:
        - Current Streak (consecutive present sessions)
        - Consistency Score (0-100 based on recent attendance patterns)
        - Heatmap Data (Date -> Status mapping)
        """
        history = sorted(student.attendances, key=lambda x: (x.date, x.session))
        
        from models import LeaveRequest
        approved_leaves = LeaveRequest.query.filter_by(student_id=student.id, status='Approved').all()
        
        def is_on_leave(date_obj):
            for leave in approved_leaves:
                if leave.start_date <= date_obj <= leave.end_date:
                    return True
            return False

        relevant_history = [a for a in history if not is_on_leave(a.date)]
        
        if not relevant_history:
            return {
                'streak': 0,
                'consistency': 0,
                'attendance_pct': 0,
                'total_sessions': 0,
                'present_sessions': 0,
                'heatmap': {}
            }
            
        # 1. Calculate Streak
        streak = 0
        # Iterate backwards through relevant history
        for att in reversed(relevant_history):
            if att.is_present:
                streak += 1
            else:
                break
                
        # 2. Key Stats
        total_sessions = len(history)
        present_sessions = sum(1 for a in history if a.is_present)
        late_sessions = sum(1 for a in history if a.is_present and a.status == 'Late')
        
        # Pct based on raw presence
        pct = (present_sessions / total_sessions * 100) if total_sessions > 0 else 0
        
        # 3. Consistency Score (Simple heuristic: higher % + recent streak bonus)
        # Base score is the percentage
        consistency = pct
        # Bonus for streak (capped at 10 points)
        streak_bonus = min(streak * 2, 10)
        consistency = min(100, consistency + streak_bonus)
        
        # 4. Heatmap Data
        # Format: {'YYYY-MM-DD': 'Present'/'Absent'}
        heatmap = {}
        for att in history:
            date_str = att.date.strftime('%Y-%m-%d')
            # If multiple sessions in a day, present takes precedence or show mixed?
            # For simplicity, if any session is Absent, mark day as Red, unless all are Present?
            # Let's map (date, session) actually for granular heatmap if UI supports it.
            # For this heatmap grid, let's use Date as key.
            # Logic: If all sessions present -> Green. If mixed -> Orange. If all absent -> Red.
            
            if date_str not in heatmap:
                heatmap[date_str] = []
            heatmap[date_str].append(att.is_present)
            
        final_heatmap = {}
        for d, statuses in heatmap.items():
            # statuses is a list of bools. We need status too.
            # Let's adjust this to use the actual status if multiple sessions.
            # For simplicity: any Absent -> Absent. Any Late (with no Absent) -> Late. Else Present.
            day_atts = [a for a in history if a.date.strftime('%Y-%m-%d') == d]
            if any(not a.is_present for a in day_atts):
                final_heatmap[d] = 'Absent'
            elif any(a.status == 'Late' for a in day_atts):
                final_heatmap[d] = 'Late'
            else:
                final_heatmap[d] = 'Present'
                
        return {
            'streak': streak,
            'consistency': round(consistency, 1),
            'attendance_pct': round(pct, 1),
            'total_sessions': total_sessions,
            'present_sessions': present_sessions,
            'late_sessions': late_sessions,
            'heatmap': final_heatmap
        }

ml_engine = MLEngine()
