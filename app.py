import os

from flask import Flask, jsonify, request
from pymongo import MongoClient
from dotenv import load_dotenv
from flask_cors import CORS
from random import randint
from flask_mail import Mail, Message
from bson import ObjectId
from datetime import datetime, timedelta


app = Flask(__name__)
load_dotenv()
CORS()

# Flask-Mail config
app.config['MAIL_SERVER']='smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_DEFAULT_SENDER')
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True
mail = Mail(app)

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


def generate_user_otp():
    otp = randint(100000, 999999)
    return str(otp)


@app.route('/user/password/generate-otp', strict_slashes=False, methods=['POST'])
def generate_otp():
    data = request.json
    email = data.get('email', None)
    user_id = data.get('user_id', None)
    if email is None or user_id is None:
        return jsonify({
            'message': 'Incomplete payload - email and user_id are required',
            'status': False
        }), 400
    
    otp = generate_user_otp()
    insert_otp = users.update_one(
        {'_id': ObjectId(user_id)},
        {'$set': {
            'password_otp': {
                'otp': otp,
                'expires': datetime.now() + timedelta(minutes=30)
            }
        }}
    )
    if insert_otp.matched_count:
        msg = Message(
            subject="Password reset OTP",
            body=f'{email} >> Your OTP to reset your password is {otp}',
            recipients=[email])
        mail.send(msg)
    else:
        return jsonify({
            'message': 'User not found',
            'status': False
        }), 404
    
    return jsonify({
        'message': f'Success: OTP generated and sent to mail ({email})',
        'status': True
    }), 200


@app.route('/user/password/verify-otp', strict_slashes=False, methods=['POST'])
def verify_otp():
    return 'Under construction'