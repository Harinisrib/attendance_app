# Trigger Reload v2.2.0 - Compact UI
import os
from dotenv import load_dotenv
from flask import Flask
from flask_cors import CORS

from extensions import db, login_manager, mail

def create_app():
    loaded = load_dotenv()
    print(f"DEBUG: load_dotenv() -> {loaded}")
    print(f"DEBUG: CWD -> {os.getcwd()}")
    app = Flask(__name__)
    CORS(app)
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-prod')
    app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', app.config['SECRET_KEY'])
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance', 'attendance.db')
    # Use consistent forward slashes for SQLite on Windows
    clean_path = db_path.replace("\\", "/")
    if clean_path.lower().startswith("c:"):
        clean_path = clean_path[2:]
    db_uri = os.getenv('DATABASE_URI', f'sqlite:///{clean_path}')
    app.config['SQLALCHEMY_DATABASE_URI'] = db_uri
    app.config['ACTIVE_OTPS'] = {}

    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Mail Configuration
    app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
    app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT', 587))
    app.config['MAIL_USE_TLS'] = os.getenv('MAIL_USE_TLS', 'True').lower() in ['true', '1', 't']
    app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME', 'mock_email@university.edu')
    app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD', 'mock_password')
    app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_DEFAULT_SENDER', 'noreply@university.edu')

    db.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)
    login_manager.login_view = 'auth.login'

    from models import User, Student
    from flask import session
    
    @login_manager.user_loader
    def load_user(user_id):
        user_type = session.get('user_type')
        if user_type == 'student':
            return Student.query.get(int(user_id))
        return User.query.get(int(user_id))

    # Register Blueprints
    from auth import auth as auth_blueprint
    app.register_blueprint(auth_blueprint)

    from main import main as main_blueprint
    app.register_blueprint(main_blueprint)

    with app.app_context():
        db.create_all()

    return app

if __name__ == '__main__':
    app = create_app()
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=True, use_reloader=True, host='0.0.0.0', port=port)

