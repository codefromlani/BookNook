from flask_caching import Cache
from functools import wraps
from flask import request, current_app
import hashlib
import json

cache = Cache()

def generate_cache_key(*args, **kwargs):
    """Generate a cache key based on the function arguments and query parameters"""
    # Include query parameters in the cache key
    query_params = dict(request.args)
    # Sort to ensure consistent ordering
    key_parts = {
        'args': args,
        'kwargs': kwargs,
        'query': sorted(query_params.items())
    }
    # Convert to string and hash
    key_str = json.dumps(key_parts, sort_keys=True)
    return hashlib.md5(key_str.encode()).hexdigest()

def cached(timeout=5 * 60):# Default 5 minutes
    """Custom caching decorator that includes query parameters in the cache key"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_app.config.get('CACHE_ENABLED', True):
                return f(*args, **kwargs)
            
            cache_key = generate_cache_key(*args, **kwargs)
            rv = cache.get(cache_key)
            if rv is not None:
                return rv
            rv = f(*args, **kwargs)
            cache.set(cache_key, rv, timeout=timeout)
            return rv
        return decorated_function
    return decorator

def invalidate_cache_pattern(pattern):
     """Invalidate all cache keys matching the given pattern"""
     if hasattr(cache, '_client'): # For Redis
        for key in cache._client.scan_iter(pattern):
            cache.delete(key)

def clear_all_cache():
    """Clear all cache entries"""
    cache.clear() 