from flask import Blueprint, jsonify, request
from sqlalchemy import or_, and_
from app.models import Book
from app import db

bp = Blueprint('books', __name__)

@bp.route('/list', methods=['GET'])
def list_books():
    
    category = request.args.get('category')
    min_price = request.args.get('min_price', type=float)
    max_price = request.args.get('max_price', type=float)
    min_rating = request.args.get('min_rating', type=float)
    search_query = request.args.get('q')
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)

    query = Book.query

    if category:
        query = query.filter(Book.category == category)

    if min_price is not None:
        query = query.filter(Book.price >= min_price)
    
    if max_price is not None:
        query = query.filter(Book.price <= max_price)

    if min_rating is not None:
        books_with_ratings = query.all()
        filtered_books = [book for book in books_with_ratings if book.average_rating >= min_rating]
        total = len(filtered_books)

        start = (page - 1) * per_page
        end = start + per_page
        paginated_books = filtered_books[start:end]

        return jsonify({
            'books': [book.to_dict() for book in paginated_books],
            'total': total,
            'page': page,
            'per_page': per_page,
            'total_pages': (total + per_page - 1) // per_page
        })
    
    if search_query:
        query = query.filter(
            or_(
                Book.title.ilike(f'%{search_query}%'),
                Book.author.ilike(f'%{search_query}%'),
                Book.description.ilike(f'%{search_query}%')
            )
        )
    
    pagination = query.paginate(page=page, per_page=per_page)
    
    return jsonify({
        'books': [book.to_dict() for book in pagination.items],
        'total': pagination.total,
        'page': page,
        'per_page': per_page,
        'total_pages': pagination.pages
    })

@bp.route('/<int:id>', methods=['GET'])
def get_book(id):
    book = db.session.get(Book, id)
    if not book:
        return jsonify({'error': 'Book not found'}), 404
    return jsonify(book.to_dict(include_reviews=True))

@bp.route('/search', methods=['GET'])
def search_books():
    query = request.args.get('q', '')
    category = request.args.get('category')
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)

    search_filter = or_(
        Book.title.ilike(f'%{query}%'),
        Book.author.ilike(f'%{query}%'),
        Book.description.ilike(f'%{query}%')
    )

    if category:
        search_filter = and_(search_filter, Book.category == category)

    pagination = Book.query.filter(search_filter).paginate(
        page=page, per_page=per_page
    )

    return jsonify({
        'books': [book.to_dict() for book in pagination.items],
        'total': pagination.total,
        'page': page,
        'per_page': per_page,
        'total_pages': pagination.pages
    })

@bp.route('/categories', methods=['GET'])
def get_categories():
    categories = db.session.query(Book.category).distinct().all()
    return jsonify({
        'categories': [category[0] for category in categories]
    })