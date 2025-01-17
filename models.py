from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import uuid

db = SQLAlchemy()  # Initialize the database object


# User Table
class User(db.Model):
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(80), nullable=False)
    # phone_no = db.Column(db.Integer, nullable=False)  # Ensure this field exists
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(256), nullable=False)
    registrations = db.relationship('Registration', backref='user', lazy=True)

# Event Table
class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    short_desc=db.Column(db.String(100),nullable=False)
    description = db.Column(db.Text, nullable=True)  
    date = db.Column(db.DateTime, nullable=False)
    photo = db.Column(db.String(200), nullable=True)
    registrations = db.relationship('Registration', backref='event', lazy=True)


# Registration Table
class Registration(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(36), db.ForeignKey('user.id'), nullable=False)
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'), nullable=False)
    registration_date = db.Column(db.DateTime, default=datetime.utcnow)
    remarks = db.Column(db.Text, nullable=True)
    __table_args__ = (db.UniqueConstraint('user_id', 'event_id', name='unique_registration'),)

