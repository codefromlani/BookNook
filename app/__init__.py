from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flask_mail import Mail
from config import Config

db = SQLAlchemy()
login = LoginManager()
migrate = Migrate()
jwt = JWTManager()
mail = Mail()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    app.config['JWT_JSON_KEY_FUNCTIONS'] = {
        'identity_claim_key': lambda: 'sub'
    }

    db.init_app(app)
    login.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    mail.init_app(app)

    login.login_view = 'auth.login'

    from app.auth.routes import bp as auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')

    from app.books.routes import bp as books_bp
    app.register_blueprint(books_bp, url_prefix='/books')

    return app

# from app import models 