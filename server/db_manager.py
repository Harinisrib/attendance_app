"""
Database Management Utility
Provides tools for backing up, restoring, and maintaining the attendance database
"""

from app import create_app
from extensions import db
from models import User, Classroom, Student, ClassSession, Attendance
from datetime import datetime
import shutil
import os

app = create_app()

def backup_database():
    """Create a timestamped backup of the database"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_dir = 'backups'
    
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)
    
    source = 'instance/attendance.db'
    destination = f'{backup_dir}/attendance_backup_{timestamp}.db'
    
    try:
        shutil.copy2(source, destination)
        print(f"✅ Database backed up successfully!")
        print(f"   Backup location: {destination}")
        return destination
    except Exception as e:
        print(f"❌ Backup failed: {e}")
        return None

def restore_database(backup_file):
    """Restore database from a backup file"""
    source = backup_file
    destination = 'instance/attendance.db'
    
    try:
        # Create a safety backup before restoring
        safety_backup = f'instance/attendance_before_restore_{datetime.now().strftime("%Y%m%d_%H%M%S")}.db'
        shutil.copy2(destination, safety_backup)
        print(f"📦 Safety backup created: {safety_backup}")
        
        # Restore from backup
        shutil.copy2(source, destination)
        print(f"✅ Database restored successfully from {backup_file}")
        return True
    except Exception as e:
        print(f"❌ Restore failed: {e}")
        return False

def show_database_stats():
    """Display comprehensive database statistics"""
    with app.app_context():
        print("\n" + "="*60)
        print("DATABASE STATISTICS")
        print("="*60)
        
        # Users
        users = User.query.all()
        print(f"\n👥 USERS: {len(users)}")
        for user in users:
            print(f"   - {user.name} ({user.email})")
        
        # Classes
        classes = Classroom.query.all()
        print(f"\n🏫 CLASSES: {len(classes)}")
        for classroom in classes:
            print(f"   - {classroom.name} (Faculty: {classroom.faculty.name})")
            print(f"     Students: {len(classroom.students)}, Sessions: {len(classroom.sessions)}")
        
        # Students
        total_students = Student.query.count()
        print(f"\n📚 TOTAL STUDENTS: {total_students}")
        
        # Sessions
        sessions = ClassSession.query.all()
        print(f"\n📅 SESSIONS: {len(sessions)}")
        session_names = {}
        for session in sessions:
            if session.name not in session_names:
                session_names[session.name] = 0
            session_names[session.name] += 1
        for name, count in session_names.items():
            print(f"   - {name}: {count} class(es)")
        
        # Attendance Records
        total_attendance = Attendance.query.count()
        present_count = Attendance.query.filter_by(is_present=True).count()
        absent_count = total_attendance - present_count
        
        print(f"\n✅ ATTENDANCE RECORDS: {total_attendance}")
        print(f"   Present: {present_count}")
        print(f"   Absent: {absent_count}")
        if total_attendance > 0:
            print(f"   Overall Rate: {(present_count/total_attendance*100):.1f}%")
        
        # Risk Distribution
        high_risk = Student.query.filter_by(risk_level='High').count()
        medium_risk = Student.query.filter_by(risk_level='Medium').count()
        low_risk = Student.query.filter_by(risk_level='Low').count()
        
        print(f"\n⚠️  RISK DISTRIBUTION:")
        print(f"   High Risk: {high_risk}")
        print(f"   Medium Risk: {medium_risk}")
        print(f"   Low Risk: {low_risk}")
        
        print("\n" + "="*60 + "\n")

def clean_orphaned_records():
    """Remove orphaned records (attendance without students, etc.)"""
    with app.app_context():
        print("\n🧹 CLEANING ORPHANED RECORDS...")
        
        # Find attendance records for non-existent students
        all_student_ids = [s.id for s in Student.query.all()]
        orphaned_attendance = Attendance.query.filter(
            ~Attendance.student_id.in_(all_student_ids)
        ).all()
        
        if orphaned_attendance:
            print(f"   Found {len(orphaned_attendance)} orphaned attendance records")
            for att in orphaned_attendance:
                db.session.delete(att)
            db.session.commit()
            print("   ✅ Orphaned attendance records removed")
        else:
            print("   ✅ No orphaned attendance records found")
        
        # Find sessions without classrooms
        all_class_ids = [c.id for c in Classroom.query.all()]
        orphaned_sessions = ClassSession.query.filter(
            ~ClassSession.classroom_id.in_(all_class_ids)
        ).all()
        
        if orphaned_sessions:
            print(f"   Found {len(orphaned_sessions)} orphaned sessions")
            for sess in orphaned_sessions:
                db.session.delete(sess)
            db.session.commit()
            print("   ✅ Orphaned sessions removed")
        else:
            print("   ✅ No orphaned sessions found")
        
        print("\n✅ Database cleanup completed!\n")

def verify_database_integrity():
    """Verify database integrity and relationships"""
    with app.app_context():
        print("\n🔍 VERIFYING DATABASE INTEGRITY...")
        issues = []
        
        # Check students have valid classrooms
        for student in Student.query.all():
            if not student.classroom:
                issues.append(f"Student {student.name} (ID: {student.id}) has no classroom")
        
        # Check sessions have valid classrooms
        for session in ClassSession.query.all():
            if not session.classroom:
                issues.append(f"Session {session.name} (ID: {session.id}) has no classroom")
        
        # Check attendance has valid students
        for att in Attendance.query.all():
            if not att.student:
                issues.append(f"Attendance record (ID: {att.id}) has no student")
        
        # Check classrooms have valid faculty
        for classroom in Classroom.query.all():
            if not classroom.faculty:
                issues.append(f"Classroom {classroom.name} (ID: {classroom.id}) has no faculty")
        
        if issues:
            print(f"\n⚠️  Found {len(issues)} integrity issues:")
            for issue in issues:
                print(f"   - {issue}")
        else:
            print("\n✅ Database integrity verified - no issues found!")
        
        print()

def main_menu():
    """Interactive database management menu"""
    while True:
        print("\n" + "="*60)
        print("DATABASE MANAGEMENT MENU")
        print("="*60)
        print("1. Show Database Statistics")
        print("2. Backup Database")
        print("3. Restore Database")
        print("4. Clean Orphaned Records")
        print("5. Verify Database Integrity")
        print("6. Exit")
        print("="*60)
        
        choice = input("\nEnter your choice (1-6): ").strip()
        
        if choice == '1':
            show_database_stats()
        elif choice == '2':
            backup_database()
        elif choice == '3':
            backup_file = input("Enter backup file path: ").strip()
            if os.path.exists(backup_file):
                restore_database(backup_file)
            else:
                print(f"❌ File not found: {backup_file}")
        elif choice == '4':
            confirm = input("Are you sure you want to clean orphaned records? (yes/no): ").strip().lower()
            if confirm == 'yes':
                clean_orphaned_records()
        elif choice == '5':
            verify_database_integrity()
        elif choice == '6':
            print("\n👋 Goodbye!\n")
            break
        else:
            print("❌ Invalid choice. Please try again.")

if __name__ == '__main__':
    main_menu()
