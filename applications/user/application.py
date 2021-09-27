import csv
import io

from flask import Flask, request, make_response, jsonify
from flask_jwt_extended import JWTManager, get_jwt
from redis import Redis

from admin_decorator import role_check
from configuration import Configuration

application = Flask(__name__)
application.config.from_object(Configuration)
jwt = JWTManager(application)


def validate_vote(content):
    stream = io.StringIO(content)
    reader = csv.reader(stream)

    for row in reader:
        if len(row) != 2:
            return "Incorrect number of values on line 0."
        if not row[1].isdigit():
            return "Incorrect poll number on line 0."

    return "Validation successful!"


@application.route("/vote", methods=["POST"])
@role_check(role="zvanicnik")
def vote():
    with Redis(host=Configuration.REDIS_HOST) as redis:
        if not request.files or request.files.get("file", "") == "":
            return make_response(jsonify(message="Field file is missing."), 400)

        content = request.files["file"].stream.read().decode("utf-8")
        stream = io.StringIO(content)
        reader = csv.reader(stream)

        response = validate_vote(content)
        if response != "Validation successful!":
            return make_response(jsonify(message=response), 400)

        refresh_claims = get_jwt()
        redis.rpush(Configuration.REDIS_VOTES_LIST, str("jmbg," + refresh_claims["jmbg"]))
        for row in reader:
            redis.rpush(Configuration.REDIS_VOTES_LIST, str(row[0] + "," + row[1]))

    return make_response("", 200)


if __name__ == "__main__":
    application.run(debug=True, host="0.0.0.0", port=5000)