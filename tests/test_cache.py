import pytest
from app import create_app, db
from app.models import Book, Review, User
from app.utils.cache import cache, clear_all_cache
from config import Config
from datetime import datetime
import json

class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    CACHE_TYPE = 'simple'  
    CACHE_ENABLED = True

@pytest.fixture
def app():
    app = create_app(TestConfig)
    with app.app_context():
        db.create_all()
        clear_all_cache()
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def sample_book():
    book = Book(
        isbn="1234567890",
        title="Test Book",
        author="Test Author",
        price=9.99,
        stock=10,
        description="Test Description",
        category="Test Category"
    )
    db.session.add(book)
    db.session.commit()
    return book

@pytest.fixture
def sample_user():
    user = User(
        email="test@example.com",
        username="testuser",
        first_name="Test",
        last_name="User"
    )
    user.set_password("password123")
    db.session.add(user)
    db.session.commit()
    return user

def test_list_books_cache(client, sample_book):
    clear_all_cache()
    response1 = client.get('/books/list')
    assert response1.status_code == 200
    data1 = json.loads(response1.data)

    sample_book.price = 19.99
    db.session.commit()

    response2 = client.get('/books/list')
    assert response2.status_code == 200
    data2 = json.loads(response2.data)

    assert data1 == data2
    assert data2['books'][0]['price'] == 9.99

def test_get_book_cache(client, sample_book):
    response1 = client.get(f'/books/{sample_book.id}')
    assert response1.status_code == 200
    data1 = json.loads(response1.data)

    sample_book.title = "Updated Title"
    db.session.commit()

    response2 = client.get(f'/books/{sample_book.id}')
    assert response2.status_code == 200
    data2 = json.loads(response2.data)

    assert data1 == data2
    assert data2['title'] == "Test Book"

def test_search_book_cache(client, sample_book):
    response1 = client.get('/books/search?q=Test')
    assert response1.status_code == 200
    data1 = json.loads(response1.data)

    sample_book.title = "Modified Book"
    db.session.commit()

    response2 = client.get('/books/search?q=Test')
    assert response2.status_code == 200
    data2 = json.loads(response2.data)

    assert data1 == data2
    assert data2['books'][0]['title'] == "Test Book"

def test_categories_cache(client, sample_book):
    response1 = client.get('/books/categories')
    assert response1.status_code == 200
    data1 = json.loads(response1.data)

    new_book = Book(
        isbn="0987654321",
        title="Another Book",
        author="Another Author",
        price=14.99,
        stock=5,
        category="New Category"
    )
    db.session.add(new_book)
    db.session.commit()

    response2 = client.get('/books/categories')
    assert response2.status_code == 200
    data2 = json.loads(response2.data)

    assert data1 == data2
    assert len(data2['categories']) == 1
    assert "New Category" not in data2['categories']

def test_book_reviews_cache(client, sample_book, sample_user):
    review = Review(
        user_id=sample_user.id,
        book_id=sample_book.id,
        rating=5,
        comment="Great book!"
    )
    db.session.add(review)
    db.session.commit()

    response1 = client.get(f'/api/books/{sample_book.id}/reviews')
    assert response1.status_code == 200
    data1 = json.loads(response1.data)

    review2 = Review(
        user_id=sample_user.id,
        book_id=sample_book.id,
        rating=5,
        comment="Great book!"
    )
    db.session.add(review)
    db.session.commit()

    response2 = client.get(f'/api/books/{sample_book.id}/reviews')
    assert response2.status_code == 200
    data2 = json.loads(response2.data)

    assert data1 == data2
    assert len(data2) == 1

def test_cache_invalidation(client, sample_book):
    response1 = client.get(f'/books/{sample_book.id}')
    assert response1.status_code == 200
    data1 = json.loads(response1.data)

    cache.clear()

    sample_book.title = "Updated Title"
    db.session.commit()
    
    response2 = client.get(f'/books/{sample_book.id}')
    assert response2.status_code == 200
    data2 = json.loads(response2.data)

    assert data1 != data2
    assert data2['title'] == "Updated Title" 