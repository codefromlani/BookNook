from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from redis import Redis
import os
from dotenv import load_dotenv

load_dotenv()


redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
redis = Redis.from_url(redis_url)

limiter = Limiter(
    key_func=get_remote_address,
    storage_uri=redis_url,
    default_limits=["200 per day", "50 per hour"]
)

def ip_limit(limit_string):
    return limiter.limit(limit_string)

def user_limit(limit_string):
    def get_user_id():
        from flask_jwt_extended import get_jwt_identity
        try:
            return str(get_jwt_identity()) or get_remote_address()
        except:
            return get_remote_address()
        
    return limiter.limit(limit_string, key_func=get_user_id)

def handle_rate_limit_exceeded(e):
    return {
        "error": "Rate limit exceeded",
        "description": str(e.description),
        "retry_after": e.retry_after
    }, 429