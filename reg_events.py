from flask import Blueprint, render_template, request, session, redirect, url_for, flash
from models import db, User, Event, Registration

# Create Blueprint
reg_events = Blueprint('reg_events', __name__, template_folder='templates')

@reg_events.route('/Create')
def user_create_event():
    return render_template('users/user_create_events.html')  