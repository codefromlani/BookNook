import os
import pytest
from app import create_app, db
from app.models import User, Book
from config import Config

class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False
    JWT_SECRET_KEY = 'test-secret-key'
    STRIPE_SECRET_KEY = os.environ.get('STRIPE_TEST_SECRET_KEY')

@pytest.fixture
def app():
    app = create_app(TestConfig)

    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def auth_headers(client):
    user_data = {
        'email': 'test@gmail.com',
        'username': 'testuser',
        'password': 'Test123!',
        'first_name': 'Test',
        'last_name': 'User'
    }

    response = client.post('/auth/register', json=user_data)
    access_token = response.json['access_token']

    return {'Authorization': f'Bearer {access_token}'}

@pytest.fixture
def admin_header(app, client):
    with app.app_context():
        admin = User(
            email='admin@gmail.com',
            username='admin',
            first_name='Admin',
            last_name='User',
            is_admin=True
        )
        admin.set_password('Admin123!')
        db.session.add(admin)
        db.session.commit()

        response = client.post('/auth/login', json={
            'email': 'admin@gmail.com',
            'password': 'Admin123!'
        })
        access_token = response.json['access_token']
        
        return {'Authorization': f'Bearer {access_token}'}
    
@pytest.fixture
def sample_book(app):
    with app.app_context():
        book = Book(
            isbn='1234567890',
            title='Test Book',
            author='Test Author',
            price=29.99,
            stock=10,
            description='A test book',
            category='Fiction'
        )
        db.session.add(book)
        db.session.commit()
        book_data = book.to_dict()
        return book_data
    
@pytest.fixture
def sample_cart(app, auth_headers, client, sample_book):
    response = client.post('/api/cart/add', 
        json={'book_id': sample_book['id'], 'quantity': 1},
        headers=auth_headers
    )
    return response.json