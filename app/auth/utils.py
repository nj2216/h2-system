"""
Authentication utilities and decorators
"""
from functools import wraps
from flask import abort
from flask_login import current_user


def role_required(*roles):
    """
    Decorator to require specific user roles
    
    Args:
        *roles: One or more role names (e.g., 'H2', 'Warden', 'Director')
    
    Returns:
        Decorated function
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                abort(403)
            
            if not current_user.has_role(*roles):
                abort(403)
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def admin_required(f):
    """Decorator to require Director role"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.has_role('Director'):
            abort(403)
        return f(*args, **kwargs)
    return decorated_function


def h2_required(f):
    """Decorator to require H2 role"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.has_role('H2'):
            abort(403)
        return f(*args, **kwargs)
    return decorated_function
