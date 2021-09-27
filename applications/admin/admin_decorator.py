from functools import wraps
from flask_jwt_extended import verify_jwt_in_request, get_jwt
from flask import jsonify, make_response


def role_check(role):
    def wrapper(function):
        @wraps(function)
        def decorator(*arguments, **keyword_arguments):
            verify_jwt_in_request()
            claims = get_jwt()
            if "role" in claims and role == claims["role"]:
                return function(*arguments, **keyword_arguments)
            else:
                response = "Missing Authorization Header"
                return make_response(jsonify(msg=response), 401)

        return decorator

    return wrapper
