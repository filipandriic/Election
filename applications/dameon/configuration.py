import os

database_url = os.environ["DATABASE_URL"]
redis_host = os.environ["REDIS_URI"]


class Configuration:
    SQLALCHEMY_DATABASE_URI = f"mysql+pymysql://root:root@{database_url}/project"
    REDIS_HOST = redis_host
    REDIS_VOTES_LIST = "votes"
    JWT_SECRET_KEY = "JWT_SECRET_KEY"
