from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models import Book, Order, User, OrderItem
from app.admin.utils import admin_required
from sqlalchemy import func
from datetime import datetime, timedelta

bp = Blueprint('admin', __name__)

# Book Management
@bp.route('/books', methods=['POST'])
@jwt_required()
@admin_required
def create_book():
    data = request.get_json()
    required_fields = ['isbn', 'title', 'author', 'price', 'stock', 'category']

    if not all(field in data for field in required_fields):
        return jsonify({'error': 'Missing required fields'}), 400
    
    if Book.query.filter_by(isbn=data['isbn']).first():
        return jsonify({'error': 'ISBN already exists'}), 400
    
    book = Book(
        isbn=data['isbn'],
        title=data['title'],
        author=data['author'],
        price=data['price'],
        stock=data['stock'],
        description=data.get('description'),
        publisher=data.get('publisher'),
        publication_date=datetime.strptime(data['publication_date'], '%Y-%m-%d').date() if 'publication_date' in data else None,
        category=data['category']
    )

    db.session.add(book)
    db.session.commit()

    return jsonify(book.to_dict()), 201

@bp.route('/books/<int:book_id>', methods=['PUT'])
@jwt_required()
@admin_required
def update_book(book_id):
    book = Book.query.get_or_404(book_id)
    data = request.get_json()

    if 'title' in data:
        book.title = data['title']
    if 'author' in data:
        book.author = data['author']
    if 'price' in data:
        book.price = data['price']
    if 'stock' in data:
        book.stock = data['stock']
    if 'description' in data:
        book.description = data['description']
    if 'publisher' in data:
        book.publisher = data['publisher']
    if 'publication_date' in data:
        book.publication_date = datetime.strptime(data['publication_date'], '%Y-%m-%d').date()
    if 'category' in data:
        book.category = data['category']

    db.session.commit()
    return jsonify(book.to_dict())

@bp.route('/books<int:book_id>', methods=['DELETE'])
@jwt_required()
@admin_required
def delete_book(book_id):
    book = Book.query.get_or_404(book_id)
    db.session.delete(book)
    db.session.commit()
    return jsonify({'message': 'Book deleted successfully'})

# Order Management
@bp.route('/orders', methods=['GET'])
@jwt_required()
@admin_required
def get_all_orders():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    status = request.args.get('status')

    query = Order.query
    if status:
        query = query.filter(Order.status == status)

    orders = query.paginate(page=page, per_page=per_page)

    return jsonify({
        'orders': [{
            'id': order.id,
            'user_id': order.user_id,
            'total_amount': float(order.total_amount),
            'status': order.status.value,
            'order_date': order.order_date.isoformat(),
            'customer': {
                'id': order.customer.id,
                'email': order.customer.email,
                'username': order.customer.username
            }
        } for order in orders.items],
        'total': orders.total,
        'pages': orders.pages,
        'current_page': page
    })

@bp.route('/orders<int:order_id>', methods=['GET'])
@jwt_required()
@admin_required
def get_order_details(order_id):
    order = Order.query.get_or_404(order_id)
    return jsonify({
        'id': order.id,
        'user_id': order.user_id,
        'total_amount': float(order.total_amount),
        'status': order.status.value,
        'order_date': order.order_date.isoformat(),
        'shipping_address': order.shipping_address,
        'customer': {
            'id': order.customer.id,
            'email': order.customer.email,
            'username': order.customer.username
        },
        'items': [{
            'id': item.id,
            'book_id': item.book_id,
            'quantity': item.quantity,
            'price_at_time': float(item.price_at_time),
            'book': item.book.to_dict()
        } for item in order.items]
    })

@bp.route('/orders<int:order_id>', methods=['PUT'])
@jwt_required()
@admin_required
def update_order_status(order_id):
    order = Order.query.get_or_404(order_id)
    data = request.get_json()

    if 'status' not in data:
        return jsonify({'error': 'Status is required'}), 400
    
    try:
        order.status = data['status']
        db.session.commit()
        return jsonify({'message': 'Order status updated successfully'})
    except ValueError:
        return jsonify({'error': 'Invalid status value'}), 400
    
# User Management
@bp.route('/users', methods=['GET'])
@jwt_required()
@admin_required
def get_all_users():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)

    users = User.query.paginate(page=page, per_page=per_page)

    return jsonify({
        'users': [user.to_dict() for user in users.items],
        'total': users.total,
        'pages': users.pages,
        'current_page': page
    })

@bp.route('/users/<int:user_id>/block', methods=['PUT'])
@jwt_required()
@admin_required
def toggle_user_block(user_id):
    user = User.query.get_or_404(user_id)
    data = request.get_json()

    if 'is_blocked' not in data:
        return jsonify({'error': 'is_blocked field is required'}), 400
    
    user.is_blocked = data['is_blocked']
    db.session.commit()
    
    return jsonify({'message': f'User {"blocked" if data["is_blocked"] else "unblocked"} successfully'})

@bp.route('/users/<int:user_id>/orders', methods=['GET'])
@jwt_required()
@admin_required
def get_user_order_history(user_id):
    user = User.query.get_or_404(user_id)
    orders = Order.query.filter_by(user_id=user_id).all()

    return jsonify([{
        'id': order.id,
        'total_amount': float(order.total_amount),
        'status': order.status.value,
        'order_date': order.order_date.isoformat(),
        'items': [{
            'book': item.book.to_dict(),
            'quantity': item.quantity,
            'price_at_time': float(item.price_at_time)
        } for item in order.items]
    } for order in orders])

# Report Generation 
@bp.route('/reports/sales', methods=['GET'])
@jwt_required()
@admin_required
def get_sales_report():
    period = request.args.get('period', 'month')  # week, month, year
    end_date = datetime.utcnow()

    if period == 'week':
        start_date = end_date - timedelta(days=7)
    elif period == 'month':
        start_date = end_date - timedelta(days=30)
    else:  # year
        start_date = end_date - timedelta(days=365)
    
    sales = db.session.query(
        func.date(Order.order_date).label('date'),
        func.sum(Order.total_amount).label('total_sales'),
        func.count(Order.id).label('num_orders')
    ).filter(
        Order.order_date.between(start_date, end_date),
        Order.status == 'COMPLETED'
    ).group_by(
        func.date(Order.order_date)
    ).all()

    return jsonify([{
        'date': str(sale.date),
        'total_sales': float(sale.total_sales),
        'num_orders': sale.num_orders
    } for sale in sales])

@bp.route('/reports/popular-books', methods=['GET'])
@jwt_required()
@admin_required
def get_popular_books_report():
    period = request.args.get('period', 'month')
    limit = request.args.get('limit', 10, type=int)
    
    end_date = datetime.utcnow()
    if period == 'week':
        start_date = end_date - timedelta(days=7)
    elif period == 'month':
        start_date = end_date - timedelta(days=30)
    else:  # year
        start_date = end_date - timedelta(days=365)
    
    popular_books = db.session.query(
        Book,
        func.sum(OrderItem.quantity).label('total_quantity'),
        func.sum(OrderItem.quantity * OrderItem.price_at_time).label('total_revenue')
    ).join(
        OrderItem
    ).join(
        Order
    ).filter(
        Order.order_date.between(start_date, end_date),
        Order.status == 'COMPLETED'
    ).group_by(
        Book.id
    ).order_by(
        func.sum(OrderItem.quantity).desc()
    ).limit(limit).all()
    
    return jsonify([{
        'book': book.to_dict(),
        'total_quantity_sold': int(total_quantity),
        'total_revenue': float(total_revenue)
    } for book, total_quantity, total_revenue in popular_books])

@bp.route('/reports/customer-activity', methods=['GET'])
@jwt_required()
@admin_required
def get_customer_activity_report():
    period = request.args.get('period', 'month')
    limit = request.args.get('limit', 10, type=int)
    
    end_date = datetime.utcnow()
    if period == 'week':
        start_date = end_date - timedelta(days=7)
    elif period == 'month':
        start_date = end_date - timedelta(days=30)
    else:  # year
        start_date = end_date - timedelta(days=365)
    
    active_customers = db.session.query(
        User,
        func.count(Order.id).label('total_orders'),
        func.sum(Order.total_amount).label('total_spent')
    ).join(
        Order
    ).filter(
        Order.order_date.between(start_date, end_date),
        Order.status == 'completed'
    ).group_by(
        User.id
    ).order_by(
        func.count(Order.id).desc()
    ).limit(limit).all()
    
    return jsonify([{
        'user': user.to_dict(),
        'total_orders': int(total_orders),
        'total_spent': float(total_spent)
    } for user, total_orders, total_spent in active_customers]) 