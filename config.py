import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:

    SECRET_KEY = "lab_lab_secret_key"
    DEBUG = True

    MYSQL_HOST = 'localhost'
    MYSQL_USER = 'root'
    MYSQL_PASSWORD = ''
    MYSQL_DB = 'python_etr_db'

    UPLOAD_PRODUCT = os.path.join(BASE_DIR,'app','static', 'uploads', 'products')
    UPLOAD_PAYMENT = os.path.join(BASE_DIR,'app','static', 'uploads', 'payments')