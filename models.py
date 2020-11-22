from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from random import choices
from flask import Flask
import string
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin
from flask_dance.consumer.storage.sqla import OAuthConsumerMixin

app = Flask(__name__)
db = SQLAlchemy()


class Links(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    original_url = db.Column(db.String(512))
    short_url = db.Column(db.String(50), unique=True)
    visits = db.Column(db.Integer, default=0)
    date_created = db.Column(db.DateTime, default=datetime.now)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.short_url = self.generate_short_link()

    def generate_short_link(self):
        characters = string.digits + string.ascii_letters
        short_url = ''.join(choices(characters, k=5))

        link = self.query.filter_by(short_url=short_url).first()

        if link:
            return self.generate_short_link()

        return short_url


class IpAddresses(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ipAddress = db.Column(db.String(30))
    count = db.Column(db.Integer, default=0)

    def __init__(self, ipAddress):
        self.ipAddress = ipAddress


class Register(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    user_name = db.Column(db.String(256), unique=True)
    email = db.Column(db.String(256), unique=True)
    password = db.Column(db.String(256))

    def __init__(self, user_name, email, password):
        self.user_name = user_name
        self.email = email
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)


class Users(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    unique_id = db.Column(db.String(8), unique=True)
    email = db.Column(db.String(256), unique=True)
    google_email = db.Column(db.String(256), unique=True)
    google_name = db.Column(db.String(256))
    twitter_user_name = db.Column(db.String(256), unique=True)
    twitter_name = db.Column(db.String(256))
    facebook_user_name = db.Column(db.String(256), unique=True)
    facebook_name = db.Column(db.String(256))
    github_username = db.Column(db.String(256), unique=True)
    github_name = db.Column(db.String(256))
    onboard_option = db.Column(db.String(256))
    first_name = db.Column(db.String(256))
    last_name = db.Column(db.String(256))
    options = db.Column(db.String(512))
    organization = db.Column(db.String(256))
    title = db.Column(db.String(256))
    department = db.Column(db.String(256))
    organization_size = db.Column(db.Integer)


class OAuth(OAuthConsumerMixin, db.Model):
    provider_user_id = db.Column(db.String(256), unique=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey(Users.id), nullable=False)
    user = db.relationship(Users)


class UserDashboard(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    unique_id = db.Column(db.String(8))
    original_url = db.Column(db.String(512))
    short_url = db.Column(db.String(50), unique=True)
    visits = db.Column(db.Integer, default=0)
    date_created = db.Column(db.DateTime, default=datetime.now)
    title = db.Column(db.String(256))
    country = db.Column(db.String(256))
    max_country_visit = db.Column(db.Integer, default=0)
    max_country_visit_name = db.Column(db.String(256))
    ip_address = db.Column(db.String(30))


login_manager = LoginManager()
login_manager.login_view = 'signup'


@login_manager.user_loader
def load_user(user_id):
    return Users.query.get(int(user_id))
