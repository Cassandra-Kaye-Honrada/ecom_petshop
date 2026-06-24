from flask import Flask, session
from flask_mysqldb import MySQL
import uuid
import os

mysql = MySQL()

def create_app():
    app = Flask(__name__) 
    
    app.config['MYSQL_HOST'] = 'localhost'
    app.config['MYSQL_USER'] = 'root'
    app.config['MYSQL_PASSWORD'] = 'your_password'
    app.config['MYSQL_DB'] = 'plantify'
    app.secret_key = 'your-secret-key'
    
    mysql.init_app(app)
    
    @app.before_request
    def ensure_session_id():
        if 'session_id' not in session:
            session['session_id'] = str(uuid.uuid4())
    
    from routes.customer import register_customer
    register_customer(app, mysql)
    
    return app