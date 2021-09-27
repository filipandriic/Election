import os

redis_host = os.environ["REDIS_URI"]


class Configuration:
    REDIS_HOST = redis_host
    REDIS_VOTES_LIST = "votes"
    JWT_SECRET_KEY = "JWT_SECRET_KEY"
