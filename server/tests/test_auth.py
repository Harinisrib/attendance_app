import pytest
from app import create_app
from extensions import db
from models import User

@pytest.fixture
def client():
    app = create_app()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['WTF_CSRF_ENABLED'] = False

    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            yield client
        with app.app_context():
            db.session.remove()
            db.drop_all()

def test_login_page_loads(client):
    response = client.get('/login')
    assert response.status_code == 200

def test_register_page_loads(client):
    response = client.get('/register')
    assert response.status_code == 200
