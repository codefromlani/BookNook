from flask import Blueprint, jsonify, request, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
import stripe
from app import db
from app.models import Cart, CartItem, Book, Order, OrderItem, OrderStatusEnum
from sqlalchemy.orm.exc import NoResultFound

bp = Blueprint('cart', __name__)

@bp.route('/cart', methods=['GET'])
@jwt_required()
def get_cart():
    user_id = get_jwt_identity()
    cart = Cart.query.filter_by(user_id=user_id).first()

    if not cart:
        cart = Cart(user_id=user_id)
        db.session.add(cart)
        db.session.commit()

    return jsonify(cart.to_dict())

@bp.route('/cart/add', methods=['POST'])
@jwt_required()
def add_to_cart():
    user_id = get_jwt_identity()
    data = request.get_json()

    if not all(k in data for k in ('book_id', 'quantity')):
        return jsonify({'error': 'Missing required fields'}), 400
    
    try:
        book = db.session.get(Book, data['book_id'])
        if book.stock < data['quantity']:
            return jsonify({'error': 'Not enough stock available'}), 400
        
        cart = Cart.query.filter_by(user_id=user_id).first()
        if not cart:
            cart = Cart(user_id=user_id)
            db.session.add(cart)
            db.session.commit()

        cart_item = CartItem.query.filter_by(cart_id=cart.id, book_id=data['book_id']).first()
        if cart_item:
            cart_item.quantity += data['quantity']
        else:
            cart_item = CartItem(cart_id=cart.id, book_id=data['book_id'], quantity=data['quantity'])
            db.session.add(cart_item)

        db.session.commit()
        return jsonify({
            'total_item': CartItem.query.filter_by(cart_id=cart.id).count(),
            'items': [{'book': book.to_dict(), 'quantity': cart_item.quantity} for cart_item in CartItem.query.filter_by(cart_id=cart.id).all()]
        }), 200
    except Exception as e:
        db.session.rollback()  
        return jsonify({'error': str(e)}), 500
    except NoResultFound:
        return jsonify({'error': 'Book not found'}), 404
    
@bp.route('/cart/update/<int:item_id>', methods=['PUT'])
@jwt_required()
def update_cart_item(item_id):
    user_id = get_jwt_identity()
    data = request.get_json()

    if 'quantity' not in data:
        return jsonify({'error': 'Quantity is required'}), 400
    
    cart = Cart.query.filter_by(user_id=user_id).first()
    if not cart:
        return jsonify({'error': 'Cart not found'}), 404
    
    cart_item = CartItem.query.filter_by(id=item_id, cart_id=cart.id).first()
    if not cart_item:
        return jsonify({'error': 'Item not found in cart'}), 404
    
    if data['quantity'] <= 0:
        db.session.delete(cart_item)
    else:
        if cart_item.book.stock < data['quantity']:
            return jsonify({'error': 'Not enough stock available'}), 400
        cart_item.quantity = data['quantity']
    
    db.session.commit()
    return jsonify(cart.to_dict())

@bp.route('/cart/remove/<int:item_id>', methods=['DELETE'])
@jwt_required()
def remove_from_cart(item_id):
    user_id = get_jwt_identity()
    cart = Cart.query.filter_by(user_id=user_id).first()

    if not cart:
        return jsonify({'error': 'Cart not found'}), 404
    
    cart_item = CartItem.query.filter_by(id=item_id, cart_id=cart.id).first()
    if not cart_item:
        return jsonify({'error': 'Item not found in cart'}), 404
    
    db.session.delete(cart_item)
    db.session.commit()

    return jsonify(cart.to_dict())

@bp.route('/cart/clear', methods=['POST'])
@jwt_required()
def clear_cart():
    user_id = get_jwt_identity()
    cart = Cart.query.filter_by(user_id=user_id).first()

    if cart:
        CartItem.query.filter_by(cart_id=cart.id).delete()
        db.session.commit()

    return jsonify({'message': 'Cart cleared successfully'})

@bp.route('/checkout/create-payment-intent', methods=['POST'])
@jwt_required()
def create_payment_intent():
    user_id = get_jwt_identity()
    cart = Cart.query.filter_by(user_id=user_id).first()

    if not cart or cart.total_items == 0:
        return jsonify({'error': 'Cart is empty'}), 400
    
    data = request.get_json()
    if 'shipping_address' not in data:
        return jsonify({'error': 'Shipping address is required'}), 400
    
    stripe.api_key = current_app.config['STRIPE_SECRET_KEY']

    try:
        intent = stripe.PaymentIntent.create(
        amount=int(cart.total_amount * 100),
        currency='usd',
        metadata={
            'user_id': user_id,
            'cart_id': cart.id
        },
        automatic_payment_methods={
            'enabled': True,
            'allow_redirects': 'never'  
        }
    )

        return jsonify({
            'clientSecret': intent.client_secret,
            'paymentIntentId': intent.id
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 400
    
@bp.route('/checkout/complete', methods=['POST'])
@jwt_required()
def complete_checkout():
    user_id = get_jwt_identity()
    data = request.get_json()

    if not all(k in data for k in ('payment_intent_id', 'shipping_address')):
        return jsonify({'error': 'Missing required fields'}), 400
    
    cart = Cart.query.filter_by(user_id=user_id).first()
    if not cart or cart.total_items == 0:
        return jsonify({'error': 'Cart is empty'}), 400
    
    stripe.api_key = current_app.config['STRIPE_SECRET_KEY']

    try:
        intent = stripe.PaymentIntent.retrieve(data['payment_intent_id'])
         # Simulate manual payment confirmation (for testing)
        if intent.status == 'requires_payment_method':
            
            payment_method_id = 'pm_card_visa'  # Use a test card ID from Stripe (e.g., pm_card_visa)

            # Confirm the payment intent with the test card
            intent = stripe.PaymentIntent.confirm(
                data['payment_intent_id'],
                payment_method=payment_method_id
            )

        if intent.status != 'succeeded':
            return jsonify({'error': 'Payment not successful'}), 400
        
        order = Order(
            user_id=user_id,
            total_amount=cart.total_amount,
            status=OrderStatusEnum.PENDING,
            shipping_address=data['shipping_address']
        )
        db.session.add(order)

        for cart_item in cart.items:
            if cart_item.book.stock < cart_item.quantity:
                db.session.rollback()
                return jsonify({'error': f'Not enough stock for {cart_item.book.title}'}), 400
            
            order_item = OrderItem(
                order_id=order.id,
                book_id=cart_item.book_id,
                quantity=cart_item.quantity,
                price_at_time=cart_item.book.price
            )
            cart_item.book.stock -= cart_item.quantity
            db.session.add(order_item)

        CartItem.query.filter_by(cart_id=cart.id).delete()
        
        db.session.commit()

        return jsonify({
            'message': 'Order placed successfully',
            'order': {
                'id': order.id,
                'total_amount': float(order.total_amount),
                'status': order.status.value
            }
        })
    
    except stripe.error.StripeError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400 