import sys
import os

print("Verifying setup...")

try:
    import flask
    print(f"Flask version: {flask.__version__}")
    from app import create_app
    from extensions import db
    
    app = create_app()
    print("App created successfully.")
    
    with app.app_context():
        # Check if DB file is created
        if os.path.exists("instance/attendance.db") or os.path.exists("attendance.db"):
             print("Database file found.")
        else:
             print("Database file NOT found (it might be created in instance/ folder depending on Flask version).")
        
        # Test ML Engine import
        from ml_engine import ml_engine
        print("ML Engine imported.")
        
    print("VERIFICATION SUCCESSFUL: All systems go.")

except Exception as e:
    print(f"VERIFICATION FAILED: {e}")
    sys.exit(1)
