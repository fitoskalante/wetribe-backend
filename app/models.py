from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin
from flask_dance.consumer.storage.sqla import OAuthConsumerMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import uuid

db = SQLAlchemy()


class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    email = db.Column(db.String)
    password = db.Column(db.String)

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)

    def check_user(self):
        return User.query.filter_by(email=self.email).first()

    def add(self):
        db.session.add(self)
        db.session.commit()


class Event(db.Model):
    __tablename__ = 'events'
    id = db.Column(db.Integer, primary_key=True)
    creator = db.Column(db.Integer, db.ForeignKey('users.id'))
    title = db.Column(db.String, nullable=False)
    description = db.Column(db.Text)
    image_url = db.Column(db.String)
    address = db.Column(db.String)
    city = db.Column(db.String)
    country = db.Column(db.String)
    time = db.Column(db.DateTime)
    date = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    lat = db.Column(db.Float)
    lng = db.Column(db.Float)
    categs = db.relationship('Category',
                             backref='event',
                             lazy=True,
                             secondary='eventcategories')

    def add(self):
        db.session.add(self)
        db.session.commit()


class Category(db.Model):
    __tablename__ = 'categories'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)


class EventCategory(db.Model):
    __tablename__ = 'eventcategories'
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('events.id'))
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'))


class OAuth(OAuthConsumerMixin, db.Model):
    provider_user_id = db.Column(db.String(256), unique=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey(User.id), nullable=False)
    user = db.relationship(User)


class Token(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String, unique=True)
    user_id = db.Column(db.Integer, db.ForeignKey(User.id), nullable=False)
    user = db.relationship(User, backref='token', lazy=True)

    def add(self):
        db.session.add(self)
        db.session.commit()


# setup login manager
login_manager = LoginManager()
login_manager.login_view = "facebook.login"

login_manager = LoginManager()


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@login_manager.request_loader
def load_user_from_request(request):
    api_key = request.headers.get('Authorization')
    if api_key:
        api_key = api_key.replace('Token ', '', 1)
        token = Token.query.filter_by(uuid=api_key).first()
        if token:
            return token.user
    return None
