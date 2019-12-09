from flask import Flask, redirect, url_for, flash, render_template, jsonify, request
from flask_login import login_required, logout_user, current_user
from itsdangerous import URLSafeTimedSerializer, SignatureExpired
from .config import Config
from .models import db, login_manager, User, Token
from .oauth import blueprint
from .cli import create_db
from flask_migrate import Migrate
from flask_cors import CORS
import googlemaps
from googlemaps import convert
import uuid, os
from dotenv import load_dotenv
from prettyprinter import pprint
import requests

load_dotenv()

app = Flask(__name__)
app.config.from_object(Config)
app.register_blueprint(blueprint, url_prefix="/login")
app.cli.add_command(create_db)
db.init_app(app)
login_manager.init_app(app)
migrate = Migrate(app, db)
CORS(app)
gmaps = googlemaps.Client(key=os.environ.get('GOOGLE_KEY'))


def send_email(token, email, name):
    url = 'https://api.mailgun.net/v3/sandboxd25ec24b7b1d4277aaeac6b2622859f5.mailgun.org/messages'
    try:
        response = requests.post(
            url,
            auth=("api", app.config['EMAIL_API']),
            data={
                "from":
                'Ricardo <fitoskalante@gmail.com>',
                "to": [email],
                "subject":
                "Reset Password",
                "text":
                f"To reset your password click on this link https://localhost:3000/set-new-pw/{token}."
            })
        response.raise_for_status()
    except Exception as err:
        print(f'Other error occurred: {err}')
    else:
        res = {"success": False, "message": "This email is not registered"}
        return jsonify(res)


@app.route('/recover', methods=['GET', 'POST'])
def recover_password():
    if request.method == 'POST':
        email = request.get_json()
        user = User.query.filter_by(email=email['email']).first()
        if not user:
            res = {"success": False, "message": "This email is not registered"}
            return jsonify(res)
        s = URLSafeTimedSerializer(app.secret_key)
        token = s.dumps(user.email, salt='RESET_PASSWORD')
        send_email(token, user.email, user.name)
        res = {
            "success": True,
            "message": "Great! Now check your email for a password reset link"
        }
        return jsonify(res)


@app.route('/set-new-pw/<token>', methods=['GET', 'POST'])
def set_new_pw(token):
    if request.method == 'POST':
        try:
            password = request.get_json()
            s = URLSafeTimedSerializer(app.secret_key)
            email = s.loads(token, salt='RESET_PASSWORD', max_age=500)
            user = User(email=email).check_user()
            if not user:
                res = {"success": False, "message": "Invalid Token"}
                return jsonify(res)
            user.set_password(password['password'])
            db.session.commit()
            res = {
                "success": True,
                "message": "You have successfully updated you password!"
            }
            return jsonify(res)
        except SignatureExpired:
            res = {"success": False, "message": "Your link has expired"}
            return jsonify(res)


@app.route("/logout", methods=['GET'])
@login_required
def logout():
    token = Token.query.filter_by(user_id=current_user.id).first()
    if token:
        db.session.delete(token)
        db.session.commit()
    logout_user()
    res = {'success': True, 'message': 'success'}
    return jsonify(res)


@app.route("/")
def index():
    return render_template("home.html")


@app.route('/getuser')
@login_required
def getuser():
    return jsonify({
        'id': current_user.id,
        'name': current_user.name,
        'email': current_user.email,
        'token': current_user.token[0].uuid
    })


@app.route('/register', methods=['POST'])
def register():
    if request.method == 'POST':
        data = request.get_json()
        user = User.query.filter_by(email=data['email']).first()
        if not user:
            user = User(
                name=data['name'],
                email=data['email'],
            )
            user.set_password(data['password'])
            user.add()
            res = {'success': True, "message": "Success"}
            return jsonify(res)
        res = {'success': False, "message": "This email is already registered"}
        return jsonify(res)


@app.route('/login', methods=['POST'])
def login():
    if request.method == 'POST':
        data = request.get_json()
        user = User.query.filter_by(email=data['email']).first()
        if not user:
            res = {"success": False, "message": "This email is not registered"}
            return jsonify(res)
        if not user.check_password(data['password']):
            res = {
                "success": False,
                "message": "Wrong Password, please try again"
            }
            return jsonify(res)
        token = Token.query.filter_by(user_id=user.id).first()
        if not token:
            token = Token(uuid=str(uuid.uuid4().hex), user_id=user.id)
            token.add()
        res = {
            "success": True,
            "user": {
                "name": user.name,
                'email': user.email
            },
            "token": token.uuid
        }
        return jsonify(res)


@app.route('/getaddress', methods=['POST'])
def reverse_geocode():
    if request.method == 'POST':
        latlng = request.get_json()
        reverse_geocode_result = gmaps.reverse_geocode(
            (latlng['lat'], latlng['lng']))
        return jsonify(reverse_geocode_result[0])


@app.route('/create-event', methods=['POST'])
@login_required
def create_event():
    if request.method == 'POST':
        ev_info = request.get_json()
        e = Event(
            title=ev_info['title'],
            creator=current_user.id,
            description=ev_info['description'],
            image_url=ev_info['image_url'],
            address=ev_info['address'],
            city=ev_info['city'],
            country=ev_info['country'],
            time=ev_info['startTime'],
            date=ev_info['startDate'],
            lat=ev_info['pos']['lat'],
            lng=ev_info['pos']['lng'],
        )
        e.add()
        pprint(e)
        res = {
            "success": True,
            "event": {
                "creator": e.creator,
                "title": e.title,
                "description": e.description,
                "image_url": e.image_url,
                "address": e.address,
                "city": e.city,
                "country": e.country,
                "time": e.time,
                "date": e.date,
                "created_at": e.created_at,
                "lat": e.lat,
                "lng": e.lng
            }
        }
        return jsonify(res)
