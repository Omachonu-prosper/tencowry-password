import os

from flask import Flask, jsonify, request
from pymongo import MongoClient
from dotenv import load_dotenv
from flask_cors import CORS
from random import randint
from flask_mail import Mail, Message
from bson import ObjectId
from datetime import datetime, timedelta
from flask_bcrypt import generate_password_hash


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
    """
    Generates a 6 digit OTP that would be sent to the user
    """
    otp = randint(100000, 999999)
    return str(otp)


@app.route('/user/password/otp/generate', strict_slashes=False, methods=['POST'])
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
    # Correct user verification based on the database structure should be done so as to fit the requirements
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
            body=f'{email} >> Your OTP to reset your password is {otp} \n The OTP will expire in 30 minutes',
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


@app.route('/user/password/otp/verify', strict_slashes=False, methods=['POST'])
def verify_otp():
    data = request.json
    otp = data.get('otp', None)
    user_id = data.get('user_id', None)
    password = data.get('password', None)
    if otp is None or user_id is None or password is None:
        return jsonify({
            'message': 'Incomplete payload - otp, password and user_id are required',
            'status': False
        }), 400
    
    user = users.find_one({'_id': ObjectId(user_id)}, {'_id': 0, 'password_otp': 1})
    if not user:
        return jsonify({
            'message': 'User not found',
            'status': False
        }), 404

    otp_details = user.get('password_otp')
    if otp_details.get('otp') == otp:
        now = datetime.now()
        if now < otp_details.get('expires'):
            # If the current time is still less than the expiry time of the otp 
            # ie the 30 minutes hasnt elapsed
            password = generate_password_hash(password)
            
            # This section should be edited to fit the database structure of users and their passwords
            users.update_one(
                {'_id': ObjectId(user_id)},
                {'$set': {'password': password, 'password_otp': None}}
            )
            ####

            return jsonify({
                'message': 'Password updated successfully',
                'status': True
            }), 200
        else:
            return jsonify({
                'message': 'expired OTP',
                'status': False
            }), 401
    else:
        return jsonify({
            'message': 'Invalid OTP',
            'status': False
        }), 400


if __name__ == '__main__':
    app.run(debug=True)