from flask import Flask, redirect, url_for, flash, render_template, jsonify, request
from flask_login import login_required, logout_user, current_user
from .config import Config
from .models import db, login_manager, User, Token
from .oauth import blueprint
from .cli import create_db
from flask_migrate import Migrate
from flask_cors import CORS
import uuid

app = Flask(__name__)
app.config.from_object(Config)
app.register_blueprint(blueprint, url_prefix="/login")
app.cli.add_command(create_db)
db.init_app(app)
login_manager.init_app(app)
migrate = Migrate(app, db)
CORS(app)


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


@app.route('/login', methods=['GET', 'POST'])
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
