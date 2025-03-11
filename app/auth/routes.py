from flask import Blueprint, request, jsonify, current_app, url_for
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash
from app import db
from app.models import User
from app.auth.email import send_password_reset_email
from app.auth.validators import validate_email, validate_password

bp = Blueprint('auth', __name__)

def generate_tokens(user):
    user_id_str = str(user.id)
    access_token = create_access_token(identity=user_id_str)
    refresh_token = create_refresh_token(identity=user_id_str)
    return access_token, refresh_token


@bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()

    if not all(k in data for k in ('email', 'username', 'password', 'first_name', 'last_name')):
        return jsonify({'error': 'Missing required fields'}), 400
    
    if not validate_email(data['email']):
        return jsonify({'error': 'Invalid email format'}), 400
    
    if not validate_password(data['password']):
        return jsonify({'error': 'Password must be at least 8 characters long and contain at least one number and one letter'}), 400 

    if User.query.filter_by(email=data['email']).first():
        return jsonify({'error': 'Email already registered'}), 400
    
    if User.query.filter_by(username=data['username']).first():
        return jsonify({'error': 'Username already taken'}), 400
    
    user = User(
        email=data['email'],
        username=data['username'],
        first_name=data['first_name'],
        last_name=data['last_name']
    )
    user.set_password(data['password'])

    db.session.add(user)
    db.session.commit()

    access_token, refresh_token = generate_tokens(user)
    
    return jsonify({
        'message': 'User registered successfully',
        'user': user.to_dict(),
        'access_token': access_token,
        'refresh_token': refresh_token
    }), 201

@bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()

    if not all(k in data for k in ('email', 'password')):
        return jsonify({'error': 'Missing email or password'}), 400
    
    user = User.query.filter_by(email=data['email']).first()

    if not user or not user.check_password(data['password']):
        return jsonify({'error': 'Invalid email or password'}), 401
    
    access_token, refresh_token = generate_tokens(user)
    
    return jsonify({
        'message': 'Login successful',
        'user': user.to_dict(),
        'access_token': access_token,
        'refresh_token': refresh_token
    }), 200

@bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    current_user_id = get_jwt_identity()
    if not isinstance(current_user_id, str):
        current_user_id = str(current_user_id)
    access_token = create_access_token(identity=current_user_id)
    return jsonify({'access_token': access_token}), 200

@bp.route('/reset-password-request', methods=['POST'])
def reset_password_request():
    data = request.get_json()

    if 'email' not in data:
        return jsonify({'error': 'Email is required'}), 400
    
    user = User.query.filter_by(email=data['email']).first()
    if user:
        send_password_reset_email(user)

    return jsonify({
        'message': 'Password reset instructions have been sent to your email'
    }), 200

@bp.route('/reset-password/<token>', methods=['POST'])
def reset_password(token):
    data = request.get_json()

    if 'password' not in data:
        return jsonify({'error': 'New password is required'}), 400
    
    user = User.verify_reset_password_token(token)
    if not user:
        return jsonify({'error': 'Invalid or expired reset token'}), 400
    
    if not validate_password(data['password']):
        return jsonify({'error': 'Password must be at least 8 characters long and contain at least one number and one letter'}), 400
    
    user.set_password(data['password'])
    db.session.commit()
    
    return jsonify({'message': 'Password has been reset successfully'}), 200

@bp.route('/me', methods=['GET'])
@jwt_required()
def get_current_user():
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    return jsonify(user.to_dict()), 200