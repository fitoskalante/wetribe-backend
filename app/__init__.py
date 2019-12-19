from flask import Flask, redirect, url_for, flash, render_template, jsonify, request
from flask_login import login_required, logout_user, current_user
from itsdangerous import URLSafeTimedSerializer, SignatureExpired
from .config import Config
from .models import db, login_manager, User, Token, Event, EventCategory, Category, Attendance, Comment, UserInterest, Interest
from .oauth import blueprint
from .cli import create_db
from flask_migrate import Migrate
from flask_cors import CORS
import googlemaps
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
                city=data['city'],
                last_name=data['lastname'],
                country=data['country'],
            )
            user.set_password(data['password'])
            user.add()
            res = {
                'success': True,
                "message": "Success",
                'user_id': user.id,
                'user_name': user.name,
            }
            return jsonify(res)
        res = {'success': False, "message": "This email is already registered"}
        return jsonify(res)


@app.route('/geteventsbylocation', methods=['POST'])
def get_events_by_location():
    if request.method == 'POST':
        data = request.get_json()
        city = data.split(', ')[0]
        evs_city = Event.query.filter_by(city=city).all()
        if len(evs_city) > 0:
            res = {
                'success': True,
                'message': 'Join these Tribes in',
                'events': [i.convert_to_obj() for i in evs_city]
            }
            return jsonify(res)
        res = {'success': False, 'message': 'No Tribes yet in'}
        return jsonify(res)


@app.route('/addaboutyou', methods=['POST'])
def add_about_you():
    if request.method == 'POST':
        data = request.get_json()
        user_id = data['user_id']['user_id']
        description = data['data']['description']
        interests = data['interests']
        user = User.query.get(user_id)

        user.description = description
        db.session.commit()

        if len(interests) > 0:
            for interest in interests:
                usin = UserInterest(user_id=user_id, interest_id=interest)
                db.session.add(usin)
                db.session.commit()
        res = {
            'success': True,
            "message": "Success",
        }
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


@app.route('/getpos', methods=['POST'])
def geocode():
    if request.method == 'POST':
        address = request.get_json()
        geocode_result = gmaps.geocode(address)
        lat = geocode_result[0]['geometry']['location']['lat']
        lng = geocode_result[0]['geometry']['location']['lng']
        addres_geocode = geocode_result[0]["address_components"]
        lng = geocode_result[0]['geometry']['location']['lng']
        res = {
            "success": True,
            "position": {
                "lat": lat,
                "lng": lng
            },
            'addres': addres_geocode
        }
        return jsonify(res)


@app.route('/getaddress', methods=['POST'])
def reverse_geocode():
    if request.method == 'POST':
        latlng = request.get_json()
        if latlng:
            reverse_geocode_result = gmaps.reverse_geocode(
                (latlng['lat'], latlng['lng']))
            res = {
                'city': reverse_geocode_result[6],
                'address': reverse_geocode_result[0]
            }
            print(res)
            if not res:
                res_two = {
                    'city': reverse_geocode_result[2],
                    'address': reverse_geocode_result[0]
                }
                if not res_two:
                    res_three = {
                        'city': reverse_geocode_result[1],
                        'address': reverse_geocode_result[0]
                    }
                    if not res_three:
                        res_final = {
                            'city': reverse_geocode_result[0],
                            'address': reverse_geocode_result[0]
                        }
                        return jsonify(res_final)
                    return jsonify(res_three)
                return jsonify(res_two)
            return jsonify(res)
        else:
            res = {'message': 'No position finded'}
            return jsonify(res)


@app.route('/joinevent', methods=['POST'])
def join_event():
    if request.method == 'POST':
        api_key = request.headers.get('Authorization')
        if api_key:
            api_key = api_key.replace('Token ', '', 1)
            token = Token.query.filter_by(uuid=api_key).first()
            if token:
                currentuser = token.user
                if currentuser:
                    ev_id = request.get_json()
                    a = Attendance(event_id=ev_id, user_id=currentuser.id)
                    db.session.add(a)
                    db.session.commit()
                    get_all_a = len(
                        Attendance.query.filter_by(event_id=ev_id).all())
                    res = {'joined': True, 'attendance': get_all_a}
                    return jsonify(res)
        res = {'notloged': True}
        return jsonify(res)


@app.route('/leaveevent', methods=['POST'])
@login_required
def leave_event():
    if request.method == 'POST':
        ev_id = request.get_json()
        a = Attendance.query.filter_by(event_id=ev_id,
                                       user_id=current_user.id).first()
        print('isjcisudnciwdsjcniwsc', a, current_user.id)
        db.session.delete(a)
        db.session.commit()
        res = {'joined': False}
        return jsonify(res)


@app.route('/comment', methods=['POST'])
@login_required
def comment():
    if request.method == 'POST':
        response = request.get_json()
        c = Comment(body=response['comment'],
                    user_id=current_user.id,
                    event_id=response['id'])
        c.add()
        comment = Comment.query.filter_by(id=c.id).first()
        print(comment)
        if comment:
            res = {'success': True}
            return jsonify(res)
        res = {'success': False}
        return jsonify(res)


@app.route('/geteventlist')
def get_event_list():
    event_list = Event.query.all()
    res = [i.convert_to_obj() for i in event_list]
    return jsonify(res)


@app.route('/geteventinfo/<id>')
def get_event_info(id):
    e = Event.query.filter_by(id=id).first()
    api_key = request.headers.get('Authorization')
    if api_key:
        api_key = api_key.replace('Token ', '', 1)
        token = Token.query.filter_by(uuid=api_key).first()
        if token:
            currentuser = token.user
            if currentuser:
                check_attending = Attendance.query.filter_by(
                    event_id=id, user_id=currentuser.id).first()
                print(check_attending)
                if check_attending:
                    if e.creator_id == currentuser.id:
                        res = {
                            'event': e.convert_to_obj(),
                            'attending': True,
                            'user_loged': True,
                            'my_event': True,
                        }
                        return jsonify(res)
                    res = {
                        'event': e.convert_to_obj(),
                        'attending': True,
                        'user_loged': True,
                        'my_event': False,
                    }
                    return jsonify(res)
                res = {
                    'event': e.convert_to_obj(),
                    'attending': False,
                    'user_loged': True,
                    'my_event': False,
                }
                return jsonify(res)
    res = {
        'event': e.convert_to_obj(),
        'attending': False,
        'user_loged': False,
        'my_event': False,
    }
    return jsonify(res)


@app.route('/create-event', methods=['POST'])
@login_required
def create_event():
    if request.method == 'POST':
        ev_info = request.get_json()
        print(ev_info)
        e = Event(
            title=ev_info['title'],
            creator_id=current_user.id,
            description=ev_info['description'],
            image_url=ev_info['image'],
            address=ev_info['address'],
            city=ev_info['city'],
            country=ev_info['country'],
            time=ev_info['startTime'],
            date=ev_info['startDate'],
            lat=ev_info['pos']['lat'],
            lng=ev_info['pos']['lng'],
        )
        e.add()
        a = Attendance(event_id=e.id, user_id=current_user.id)
        a.add()
        categories = ev_info['categories']
        if len(categories) > 0:
            for category in categories:
                evcat = EventCategory(event_id=e.id, category_id=category)
                db.session.add(evcat)
                db.session.commit()
        res = {"success": True, "event_id": e.id}
        return jsonify(res)


@app.route('/edit-event', methods=['POST'])
@login_required
def edit_event():
    if request.method == 'POST':
        ev_info = request.get_json()

        old_categs = EventCategory.query.filter_by(
            event_id=ev_info['id']).all()
        for c in old_categs:
            db.session.delete(c)
            db.session.commit()
        e = Event.query.get(ev_info['id'])
        e.title = ev_info['title'],
        e.creator_id = current_user.id,
        e.description = ev_info['description'],
        e.image_url = ev_info['image'],
        e.address = ev_info['address'],
        e.city = ev_info['city'],
        e.country = ev_info['country'],
        e.time = ev_info['startTime'],
        e.date = ev_info['startDate'],
        e.lat = ev_info['pos']['lat'],
        e.lng = ev_info['pos']['lng'],

        db.session.commit()

        categories = ev_info['categories']
        if len(categories) > 0:
            for category in categories:
                evcat = EventCategory(event_id=e.id, category_id=category)
                db.session.add(evcat)
                db.session.commit()
        res = {"success": True, "event_id": e.id}
        return jsonify(res)
