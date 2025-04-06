from flask import Blueprint, jsonify, request
from sqlalchemy import or_, and_
from app.models import Book
from app import db
from app.utils.rate_limit import ip_limit
from app.utils.cache import invalidate_cache_pattern, cached

bp = Blueprint('books', __name__)

def invalidate_book_cache(book_id=None):
    """Invalidate book-related caches"""
    patterns = ['books_list*', 'books_search*', 'books_categories*']
    if book_id:
        patterns.append(f'book_{book_id}*')
    for pattern in patterns:
        invalidate_cache_pattern(pattern)

@bp.route('/list', methods=['GET'])
@ip_limit("60 per minute")
@cached(timeout=10 * 60)
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
    
    if search_query:
        query = query.filter(
            or_(
                Book.title.ilike(f'%{search_query}%'),
                Book.author.ilike(f'%{search_query}%'),
                Book.description.ilike(f'%{search_query}%')
            )
        )
    
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
    
    pagination = query.paginate(page=page, per_page=per_page)
    
    return jsonify({
        'books': [book.to_dict() for book in pagination.items],
        'total': pagination.total,
        'page': page,
        'per_page': per_page,
        'total_pages': pagination.pages
    })

@bp.route('/<int:id>', methods=['GET'])
@ip_limit("30 per minute")
@cached(timeout=5 * 60)
def get_book(id):
    book = db.session.get(Book, id)
    if not book:
        return jsonify({'error': 'Book not found'}), 404
    return jsonify(book.to_dict(include_reviews=True))

@bp.route('/search', methods=['GET'])
@ip_limit("30 per minute")
@cached(timeout=5 * 60)
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
@ip_limit("30 per minute")
@cached(timeout=60 * 60)
def get_categories():
    categories = db.session.query(Book.category).distinct().all()
    return jsonify({
        'categories': [category[0] for category in categories]
    })