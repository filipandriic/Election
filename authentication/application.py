from flask import Flask, request, jsonify, make_response
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, create_refresh_token, get_jwt, \
    get_jwt_identity
from configuration import Configuration
from models import database, User, Role
from sqlalchemy import and_
from admin_decorator import role_check
import re

application = Flask(__name__)
application.config.from_object(Configuration)
jwt = JWTManager(application)


def validate_email(email):
    regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    if re.fullmatch(regex, email):
        return True

    return False


def validate_control_number_from_jmbg(jmbg):
    # DDMMYYYRRBBBK = abcdefghijklm
    a = int(jmbg[0])
    b = int(jmbg[1])
    c = int(jmbg[2])
    d = int(jmbg[3])
    e = int(jmbg[4])
    f = int(jmbg[5])
    g = int(jmbg[6])
    h = int(jmbg[7])
    i = int(jmbg[8])
    j = int(jmbg[9])
    k = int(jmbg[10])
    l = int(jmbg[11])
    m = int(jmbg[12])

    control_number = 11 - ((7 * (a + g) + 6 * (b + h) + 5 * (c + i) + 4 * (d + j) + 3 * (e + k) + 2 * (f + l)) % 11)
    if control_number > 9:
        control_number = 0

    if control_number != m:
        return False

    return True


def validate_registration(jmbg, forename, surname, email, password):
    # all
    if len(jmbg) == 0:
        return "Field jmbg is missing."
    if len(forename) == 0:
        return "Field forename is missing."
    if len(surname) == 0:
        return "Field surname is missing."
    if len(email) == 0:
        return "Field email is missing."
    if len(password) == 0:
        return "Field password is missing."


    # jmbg
    jmbg_pattern = '^(0[1-9]|[1-2][0-9]|3[0-1])(0[1-9]|1[0-2])[0-9]{3}[7-9][0-9]{5}'
    if len(jmbg) != 13 or not re.search(jmbg_pattern, jmbg) or validate_control_number_from_jmbg(jmbg) is False:
        return "Invalid jmbg."

    # email
    if validate_email(email) is False:
        return "Invalid email."

    # password
    capital_letter = '[A-Z]'
    lower_letter = '[a-z]'
    digit = '[1-9]'
    if len(password) < 8 or not re.search(capital_letter, password) \
            or not re.search(lower_letter, password) or not re.search(digit, password):
        return "Invalid password."

    if User.query.filter(User.email == email).first():
        return "Email already exists."

    return "Validation successful!"


def validate_login(email, password):
    # all
    if len(email) == 0:
        return "Field email is missing."
    if len(password) == 0:
        return "Field password is missing."


    # email
    if validate_email(email) is False:
        return "Invalid email."

    return "Validation successful!"


def validate_delete(email):
    if len(email) == 0:
        return "Field email is missing."

    if validate_email(email) is False:
        return "Invalid email."

    return "Validation successful!"


@application.route("/users", methods=["GET"])
def show_users():
    return str(User.query.all())


@application.route("/roles", methods=["GET"])
def show_roles():
    return str(Role.query.all())


@application.route("/register", methods=["POST"])
def register_user():
    jmbg = request.json.get("jmbg", "")
    forename = request.json.get("forename", "")
    surname = request.json.get("surname", "")
    email = request.json.get("email", "")
    password = request.json.get("password", "")

    response = validate_registration(jmbg, forename, surname, email, password)
    if response != "Validation successful!":
        return make_response(jsonify(message=response), 400)

    user = User(jmbg=jmbg, forename=forename, surname=surname, email=email, password=password, roleId=2)
    database.session.add(user)
    database.session.commit()

    return make_response("", 200)


@application.route("/login", methods=["POST"])
def user_login():
    email = request.json.get("email", "")
    password = request.json.get("password", "")

    response = validate_login(email, password)
    if response != "Validation successful!":
        return make_response(jsonify(message=response), 400)

    user = User.query.filter(and_(User.email == email, User.password == password)).first()
    if not user:
        response = "Invalid credentials."
        return make_response(jsonify(message=response), 400)

    additional_claims = {
        "jmbg": user.jmbg,
        "forename": user.forename,
        "surname": user.surname,
        "role": str(user.role)
    }

    access_token = create_access_token(identity=user.email, additional_claims=additional_claims)
    refresh_token = create_refresh_token(identity=user.email, additional_claims=additional_claims)

    return make_response(jsonify(accessToken=access_token, refreshToken=refresh_token), 200)


@application.route("/refresh", methods=["POST"])
@jwt_required(refresh=True)
def refresh_token():
    identity = get_jwt_identity()
    refresh_claims = get_jwt()

    additional_claims = {
        "jmbg": refresh_claims["jmbg"],
        "forename": refresh_claims["forename"],
        "surname": refresh_claims["surname"],
        "role": refresh_claims["role"]
    }

    return make_response(
        jsonify(accessToken=create_access_token(identity=identity, additional_claims=additional_claims)), 200)


@application.route("/check", methods=["POST"])
@jwt_required()
def check():
    return "Token is valid."


@application.route("/delete", methods=["POST"])
@role_check(role="admin")
def delete_user():
    email = request.json.get("email", "")
    response = validate_delete(email)
    if response != "Validation successful!":
        return make_response(jsonify(message=response), 400)

    user = User.query.filter(User.email == email).first()
    if not user:
        response = "Unknown user."
        return make_response(jsonify(message=response), 400)

    database.session.delete(user)
    database.session.commit()

    return make_response("", 200)


@application.route("/", methods=["GET"])
def index():
    return "Hello"


if __name__ == "__main__":
    database.init_app(application)
    application.run(debug=True, host="0.0.0.0", port=5002)
