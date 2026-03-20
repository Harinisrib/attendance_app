import pytest
from app import create_app
from extensions import db

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

def test_index_redirects_to_login(client):
    response = client.get('/')
    assert response.status_code == 302
    assert '/login' in response.headers.get('Location', '')

def test_dashboard_unauthenticated(client):
    response = client.get('/dashboard')
    assert response.status_code == 302
    assert '/login' in response.headers.get('Location', '')
