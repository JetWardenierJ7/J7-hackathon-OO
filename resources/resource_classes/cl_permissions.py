from functools import wraps
from flask_jwt_extended import get_jwt, verify_jwt_in_request
from flask import jsonify


def global_administrator_required():
    """Checks if the user is a global administrator"""

    def wrapper(fn):
        @wraps(fn)
        def decorator(*args, **kwargs):
            verify_jwt_in_request()
            claims = get_jwt()
            if claims["is_global_admin"]:
                return fn(*args, **kwargs)
            else:
                return (
                    jsonify(msg="You don't have permission to perform this action."),
                    403,
                )

        return decorator

    return wrapper


def is_global_admin(user):
    """Checks if the user is a global admin"""
    if user.role == "Global administrator":
        return True

    return False
