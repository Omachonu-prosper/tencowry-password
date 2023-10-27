import os

from flask import Flask
from pymongo import MongoClient
from dotenv import load_dotenv
from flask_cors import CORS
from flask_mail import Mail


app = Flask(__name__)
load_dotenv()
CORS()

try:
    # If we are working in a production environment (deployed state)
    # the database to be used will be the mongodb atlas database
    # else the local mongodb instance will be used
    app_status = os.environ.get('APP_STATUS')
    if app_status == 'production':
        db_username = os.environ['DATABASE_USER']
        db_passwd = os.environ['DATABASE_PASSWORD']
        db_url = os.environ['DATABASE_URL']
        uri = f"mongodb+srv://{db_username}:{db_passwd}@{db_url}"
    else:
        uri = "mongodb://127.0.0.1:27017"
except Exception as e:
    print(f'Error in connection to Database: {e}')

client = MongoClient(uri)
db = client['test']
users = db['users']


@app.route('/user/password/generate-otp', strict_slashes=False)
def generate_otp():
    return 'Under construction'


@app.route('/user/password/verify-otp', strict_slashes=False, methods=['POST'])
def verify_otp():
    return 'Under construction'