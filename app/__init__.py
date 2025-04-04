from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flask_mail import Mail
from config import Config
from flask_swagger_ui import get_swaggerui_blueprint
from app.utils.rate_limit import limiter, handle_rate_limit_exceeded
from app.utils.cache import cache

db = SQLAlchemy()
login = LoginManager()
migrate = Migrate()
jwt = JWTManager()
mail = Mail()

@login.user_loader
def load_user(user_id):
    from app.models import User  # Import User inside the function
    return User.query.get(int(user_id))

SWAGGER_URL = '/api/docs'
API_URL = '/static/swagger.json'

swagger_ui_blueprint = get_swaggerui_blueprint(
    SWAGGER_URL,
    API_URL,
    config={
        'app_name': "BookNook API Documentation",
        'deepLinking': True,
        'supportedSubmitMethods': ['get', 'post', 'put', 'delete']
    }
)

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Redis cache configuration for caching
    app.config['CACHE_TYPE'] = 'RedisCache'
    app.config['CACHE_REDIS_URL'] = app.config.get('REDIS_URL', 'redis://localhost:6379/0')
    app.config['CACHE_DEFAULT_TIMEOUT'] = 300  # 5 minutes default

    app.config['JWT_JSON_KEY_FUNCTIONS'] = {
        'identity_claim_key': lambda: 'sub'
    }

    db.init_app(app)
    login.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    mail.init_app(app)
    limiter.init_app(app)
    cache.init_app(app) 

    login.login_view = 'auth.login'

    app.errorhandler(429)(handle_rate_limit_exceeded)

    from app.auth.routes import bp as auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')

    from app.books.routes import bp as books_bp
    app.register_blueprint(books_bp, url_prefix='/books')
    
    from app.cart.routes import bp as cart_bp
    app.register_blueprint(cart_bp, url_prefix='/api')

    from app.reviews.routes import bp as reviews_bp
    app.register_blueprint(reviews_bp, url_prefix='/api')

    from app.admin.routes import bp as admin_bp
    app.register_blueprint(admin_bp, url_prefix='/admin')

    app.register_blueprint(swagger_ui_blueprint, url_prefix=SWAGGER_URL)

    return app

# from app import models 