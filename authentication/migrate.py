from flask import Flask
from flask_migrate import Migrate, init, migrate, upgrade
from configuration import Configuration
from models import database, Role, User
from sqlalchemy_utils import database_exists, create_database, drop_database

application = Flask(__name__)
application.config.from_object(Configuration)

migrate_object = Migrate(application, database)

done = False

while not done:
    try:
        # if database_exists(application.config["SQLALCHEMY_DATABASE_URI"]):
        #     drop_database(application.config["SQLALCHEMY_DATABASE_URI"])

        if not database_exists(application.config["SQLALCHEMY_DATABASE_URI"]):
            create_database(application.config["SQLALCHEMY_DATABASE_URI"])

        database.init_app(application)

        with application.app_context() as context:
            init()
            migrate(message="Production migration")
            upgrade()

            admin_role = Role(name="admin")
            user_role = Role(name="zvanicnik")

            database.session.add(admin_role)
            database.session.add(user_role)
            database.session.commit()

            admin = User(jmbg="0000000000000", forename="admin", surname="admin", email="admin@admin.com", password="1", roleId=1)
            database.session.add(admin)
            database.session.commit()

            done = True

    except Exception as error:
        print(error)