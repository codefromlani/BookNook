from app import db
from app.models import Book
from app.utils.cache import clear_all_cache

def test_list_books(client, sample_book):

    clear_all_cache()
    response = client.get('/books/list')
    assert response.status_code == 200
    assert 'books' in response.json
    assert response.json['books'][0]['title'] == 'Test Book'
    assert response.json['total'] == 1

def test_list_books_with_fliters(client, app):
    with app.app_context():
        books = [
            Book(isbn='111', title='Fiction Book', author='Author 1', 
                price=19.99, stock=5, category='Fiction'),
            Book(isbn='222', title='Science Book', author='Author 2', 
                price=29.99, stock=5, category='Science'),
            Book(isbn='333', title='Expensive Book', author='Author 3', 
                price=49.99, stock=5, category='Fiction')
        ]
        for book in books:
            db.session.add(book)
        db.session.commit()

    response = client.get('/books/list?category=Fiction')
    assert response.status_code == 200
    assert len(response.json['books']) == 2

    response = client.get('/books/list?min_price=25&max_price=45')
    assert response.status_code == 200
    assert len(response.json['books']) == 1
    assert response.json['books'][0]['title'] == 'Science Book'

def test_search_books(client, app):
    with app.app_context():
        books = [
            Book(isbn='444', title='Python Programming', author='Coder One', 
                price=29.99, stock=5, category='Programming'),
            Book(isbn='555', title='Java Basics', author='Coder Two', 
                price=24.99, stock=5, category='Programming'),
            Book(isbn='666', title='Web Development', author='Coder One', 
                price=34.99, stock=5, category='Web')
        ]
        for book in books:
            db.session.add(book)
        db.session.commit()

    response = client.get('/books/search?q=Python')
    assert response.status_code == 200
    assert len(response.json['books']) == 1
    assert response.json['books'][0]['title'] == 'Python Programming'

    response = client.get('/books/search?q=Coder One')
    assert response.status_code == 200
    assert len(response.json['books']) == 2

def test_get_book_details(client, sample_book):
    response = client.get(f'/books/{sample_book['id']}')
    assert response.status_code == 200
    assert response.json['title'] == 'Test Book'
    assert response.json['author'] == 'Test Author'
    assert response.json['price'] == 29.99
    assert 'reviews' in response.json

def test_get_categories(client, app):

    print("Available routes:")
    for rule in app.url_map.iter_rules():
        print(f"{rule.endpoint}: {rule.rule}")

    with app.app_context():
        from app.utils.cache import cache
        cache.clear()
        
        categories = ['Fiction', 'Non-Fiction', 'Science', 'Technology']
        for category in categories:
            book = Book(
                isbn=f'cat{category}',
                title=f'{category} Book',
                author='Test Author',
                price=29.99,
                stock=5,
                category=category
            )
            db.session.add(book)
        db.session.commit()
    
    response = client.get('/books/categories')
    print(response.json) 
    assert response.status_code == 200
    assert 'categories' in response.json
    assert set(response.json['categories']) == set(categories)

def test_book_not_found(client):
    response = client.get('/books/999')
    assert response.status_code == 404 