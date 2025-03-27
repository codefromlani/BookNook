from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models import Review, Book, Order, OrderItem
from sqlalchemy import and_

bp = Blueprint('reviews', __name__)

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
def get_book_reviews(book_id):
    book = Book.query.get_or_404(book_id)
    reviews = Review.query.filter_by(book_id=book_id).all()
    return jsonify([review.to_dict() for review in reviews])

@bp.route('/books/<int:book_id>/reviews', methods=['POST'])
@jwt_required()
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

    return jsonify(review.to_dict()), 201

@bp.route('/reviews/<int:review_id>', methods=['PUT'])
@jwt_required()
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

    return jsonify(review.to_dict())

@bp.route('/reviews/<int:review_id>', methods=['DELETE'])
@jwt_required()
def delete_review(review_id):
    user_id = get_jwt_identity()
    review = Review.query.get_or_404(review_id)

    if review.user_id != user_id:
        return jsonify({'error': 'You can only delete your own reviews'}), 403
    
    db.session.delete(review)
    db.session.commit()

    return jsonify({'message': 'Review deleted successfully'})

@bp.route('/users/reviews', methods=['GET'])
@jwt_required()
def get_user_reviews():
    """Get all reviews by the current user"""
    user_id = get_jwt_identity()
    reviews = Review.query.filter_by(user_id=user_id).all()
    return jsonify([review.to_dict() for review in reviews]) 