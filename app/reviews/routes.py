from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models import Review, Book, Order, OrderItem
from sqlalchemy import and_
from app.utils.rate_limit import ip_limit, user_limit
from app.utils.cache import cached, invalidate_cache_pattern
from app.books.routes import invalidate_book_cache

bp = Blueprint('reviews', __name__)

def invalidate_review_cache(book_id=None, review_id=None):
    """Invalidate review-related caches"""
    patterns = []
    if book_id:
        patterns.extend([f'book_{book_id}_reviews*', f'book_{book_id}*'])
    if review_id:
        patterns.append(f'review_{review_id}*')
    patterns.append('user_reviews*')
    for pattern in patterns:
        invalidate_cache_pattern(pattern)

def has_purchased_book(user_id, book_id):
    """Check if user has purchased the book"""
    return OrderItem.query.join(Order).filter(
        and_(
            Order.user_id == user_id,
            OrderItem.book_id == book_id,
            Order.status == 'COMPLETED'
        )
    ).first() is not None

@bp.route('/books/<int:book_id>/reviews', methods=['GET'])
@ip_limit("30 per minute")
@cached(timeout=5 * 60)
def get_book_reviews(book_id):
    book = db.session.get(Book, book_id)
    if not book:
        return jsonify({'error': 'Book not found'}), 404
    reviews = Review.query.filter_by(book_id=book_id).all()
    return jsonify([review.to_dict() for review in reviews])

@bp.route('/books/<int:book_id>/reviews', methods=['POST'])
@jwt_required()
@user_limit("5 per day, per book")
def create_review(book_id):
    user_id = get_jwt_identity()
    data = request.get_json()

    if not all(k in data for k in ('rating', 'comment')):
        return jsonify({'error': 'Rating and comment are required'}), 400
    
    rating = int(data['rating'])
    if not 1 <= rating <= 5:
        return jsonify({'error': 'Rating must be between 1 and 5'}), 400
    
    book = Book.query.get_or_404(book_id)

    if not has_purchased_book(user_id, book_id):
        return jsonify({'error': 'You can only review books you have purchased'}), 403
    
    existing_review = Review.query.filter_by(user_id=user_id, book_id=book_id).first()
    if existing_review:
        return jsonify({'error': 'You have already reviewed this book'}), 400
    
    review = Review(
        user_id=user_id,
        book_id=book_id,
        rating=rating,
        comment=data['comment']
    )
    db.session.add(review)
    db.session.commit()

    invalidate_review_cache(book_id=book_id)
    invalidate_book_cache(book_id)

    return jsonify(review.to_dict()), 201

@bp.route('/reviews/<int:review_id>', methods=['PUT'])
@jwt_required()
@user_limit("10 per hour")
def update_review(review_id):
    user_id = get_jwt_identity()
    review = Review.query.get_or_404(review_id)

    if int(review.user_id) != int(user_id):  
        return jsonify({'error': 'You can only update your own reviews'}), 403
    
    data = request.get_json()

    if not all(k in data for k in ('rating', 'comment')):
        return jsonify({'error': 'Rating and comment are required'}), 400
    
    rating = int(data['rating'])
    if not 1 <= rating <= 5:
        return jsonify({'error': 'Rating must be between 1 and 5'}), 400
    
    review.rating = rating
    review.comment = data['comment']
    db.session.commit()

    invalidate_review_cache(book_id=review.book_id, review_id=review_id)
    invalidate_book_cache(review.book_id)

    return jsonify(review.to_dict())

@bp.route('/reviews/<int:review_id>', methods=['DELETE'])
@jwt_required()
@user_limit("10 per hour")
def delete_review(review_id):
    user_id = get_jwt_identity()
    review = Review.query.get_or_404(review_id)

    if review.user_id != user_id:
        return jsonify({'error': 'You can only delete your own reviews'}), 403
    
    book_id = review.book_id
    db.session.delete(review)
    db.session.commit()

    invalidate_review_cache(book_id=book_id, review_id=review_id)
    invalidate_book_cache(book_id)

    return jsonify({'message': 'Review deleted successfully'})

@bp.route('/users/reviews', methods=['GET'])
@jwt_required()
@user_limit("30 per minute")
@cached(timeout=5 * 60)
def get_user_reviews():
    """Get all reviews by the current user"""
    user_id = get_jwt_identity()
    reviews = Review.query.filter_by(user_id=user_id).all()
    return jsonify([review.to_dict() for review in reviews]) 