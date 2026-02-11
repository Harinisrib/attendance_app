import numpy as np
import pandas as pd
from extensions import db

class MLEngine:
    def update_student_risk(self, student):
        """
        Analyzes a student's attendance history and updates their risk level in the DB.
        """
        history = student.attendances
        
        if not history:
            student.risk_level = 'Low' # Default to Low if no data
            return
        
        total_sessions = len(history)
        present_sessions = sum(1 for a in history if a.is_present)
        
        if total_sessions == 0:
            attendance_percentage = 100
        else:
            attendance_percentage = (present_sessions / total_sessions) * 100
        
        # Rule-based classification
        if attendance_percentage < 60:
            student.risk_level = 'High'
        elif attendance_percentage < 75:
            student.risk_level = 'Medium'
        else:
            student.risk_level = 'Low'
            
        # Note: commit should be handled by caller or here if standalone
        # db.session.add(student) # Already in session

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
        
        if not history:
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
        # Iterate backwards
        for att in reversed(history):
            if att.is_present:
                streak += 1
            else:
                break
                
        # 2. Key Stats
        total_sessions = len(history)
        present_sessions = sum(1 for a in history if a.is_present)
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
            if all(statuses):
                final_heatmap[d] = 'Present'
            elif not any(statuses):
                final_heatmap[d] = 'Absent'
            else:
                final_heatmap[d] = 'Mixed'
                
        return {
            'streak': streak,
            'consistency': round(consistency, 1),
            'attendance_pct': round(pct, 1),
            'total_sessions': total_sessions,
            'present_sessions': present_sessions,
            'heatmap': final_heatmap
        }

ml_engine = MLEngine()
