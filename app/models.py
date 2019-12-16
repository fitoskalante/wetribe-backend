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
    last_name = db.Column(db.String)
    description = db.Column(db.Text)
    email = db.Column(db.String)
    city = db.Column(db.String)
    country = db.Column(db.String)
    password = db.Column(db.String)
    events = db.relationship('Event', backref='user_events', lazy=True)
    comments = db.relationship('Comment', backref='user_comments', lazy=True)
    interests = db.relationship('Interest',
                                backref='user_interests',
                                lazy=True,
                                secondary='userinterests')
    attendances = db.relationship('Event',
                                  backref='user_attendances',
                                  lazy=True,
                                  secondary='attendances')

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)

    def check_user(self):
        return User.query.filter_by(email=self.email).first()

    def add(self):
        db.session.add(self)
        db.session.commit()

    def convert_to_obj(self):
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "interests": [i.convert_to_obj() for i in self.interests],
            "events": [i.event_info() for i in self.events],
            "attendances": [i.event_info() for i in self.attendances],
            "comments": [i.my_comments_info() for i in self.comments],
            "country": self.country,
            "city": self.city,
        }


class Event(db.Model):
    __tablename__ = 'events'
    id = db.Column(db.Integer, primary_key=True)
    creator_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    title = db.Column(db.String, nullable=False)
    description = db.Column(db.Text)
    image_url = db.Column(db.String)
    address = db.Column(db.String)
    city = db.Column(db.String)
    country = db.Column(db.String)
    time = db.Column(db.DateTime)
    date = db.Column(db.DateTime)
    date = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    lat = db.Column(db.Float)
    lng = db.Column(db.Float)
    categs = db.relationship('Category',
                             backref='event_categories',
                             lazy=True,
                             secondary='eventcategories')
    attendants = db.relationship('User',
                                 backref='event_attendants',
                                 lazy=True,
                                 secondary="attendances")
    comments = db.relationship('Comment', backref='event_comments', lazy=True)

    def add(self):
        db.session.add(self)
        db.session.commit()

    def event_info(self):
        return {
            "id": self.id,
            "creator_id": self.creator_id,
            "title": self.title,
            "city": self.city,
            "country": self.country,
            "date": self.date,
            "image_url": self.image_url,
        }

    def convert_to_obj(self):
        c = Comment.query.filter_by(event_id=self.id).all()
        return {
            "id":
            self.id,
            "title":
            self.title,
            'description':
            self.description,
            'image_url':
            self.image_url,
            'address':
            self.address,
            'city':
            self.city,
            'country':
            self.country,
            'time':
            self.time,
            'date':
            self.date,
            'created_at':
            self.created_at,
            'position': {
                'lat': self.lat,
                'lng': self.lng
            },
            'lat':
            self.lat,
            'lng':
            self.lng,
            "categories": [i.convert_to_obj() for i in self.categs],
            "creator":
            User.query.filter_by(id=self.creator_id).first().convert_to_obj(),
            "attendants":
            len(self.attendants),
            "attendants_details":
            [i.convert_to_obj() for i in self.attendants],
            "comments": [i.convert_to_obj() for i in c],
        }


class Category(db.Model):
    __tablename__ = 'categories'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)

    def convert_to_obj(self):
        return {"id": self.id, "name": self.name}


class Interest(db.Model):
    __tablename__ = 'interests'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)

    def convert_to_obj(self):
        return {"id": self.id, "name": self.name}


class UserInterest(db.Model):
    __tablename__ = 'userinterests'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    interest_id = db.Column(db.Integer, db.ForeignKey('interests.id'))


class Attendance(db.Model):
    __tablename__ = 'attendances'
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('events.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))

    def add(self):
        db.session.add(self)
        db.session.commit()


class EventCategory(db.Model):
    __tablename__ = 'eventcategories'
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('events.id'))
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'))


class Comment(db.Model):
    __tablename__ = 'comments'
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.Text, nullable=False)
    event_id = db.Column(db.Integer, db.ForeignKey('events.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime,
                           server_default=db.func.now(),
                           server_onupdate=db.func.now())

    def add(self):
        db.session.add(self)
        db.session.commit()

    def my_comments_info(self):
        return {
            "id": self.id,
            "body": self.body,
            'event_id': self.event_id,
            'created_at': self.created_at,
        }

    def convert_to_obj(self):
        return {
            "id": self.id,
            "body": self.body,
            'event_id': self.event_id,
            'user':
            User.query.filter_by(id=self.user_id).first().convert_to_obj(),
            'created_at': self.created_at,
        }


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
