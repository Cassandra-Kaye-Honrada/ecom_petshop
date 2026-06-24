from flask import Flask
from flask_mysqldb import MySQL
from .routes.auth import register_auth
from .routes.admin import register_admin
from .routes.customer import register_customer

mysql = MySQL()

def create_app():
    app = Flask(__name__)
    app.config.from_object('config.Config')

    mysql.init_app(app)

    register_auth(app, mysql)
    register_admin(app, mysql)
    register_customer(app, mysql)

    return app 