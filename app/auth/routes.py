from flask import Blueprint, request, jsonify, current_app, url_for
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash
from app import db
from app.models import User
from app.auth.email import send_password_reset_email
from app.auth.validators import validate_email, validate_password