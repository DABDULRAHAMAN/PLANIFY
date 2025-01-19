from flask import Blueprint, render_template, request, redirect, url_for, flash
from werkzeug.utils import secure_filename
from datetime import datetime
import os
from models import db, Event

# Create Blueprint
reg_events = Blueprint('reg_events', __name__, template_folder='templates')

# Set the upload folder path
UPLOAD_FOLDER = 'static/uploads'

# Profile Dashboard Route
@reg_events.route('/profile_dashboard')
def profile_dashboard():
    return render_template('profile/profile_dashboard.html', user={
        'name': 'John Doe',
        'email': 'john.doe@example.com',
        'joined_date': 'January 1, 2023'
    })

# Create Event Route (GET and POST)
@reg_events.route('/create_event', methods=['GET', 'POST'])
def create_event():
    return render_template('profile/create_events.html')

# Manage Event Route
@reg_events.route('/manage_event')
def manage_event():
    events = Event.query.all()  # Retrieve all events from the database
    return render_template('profile/manage_events.html', events=events)

# View Event Route
@reg_events.route('/view_event')
def view_event():
    events = Event.query.all()  # Retrieve all events from the database
    return render_template('profile/view_events.html', events=events)




@reg_events.route('/Create', methods=['GET', 'POST'])
def user_create_event():
    if request.method == 'POST':
        # Retrieve form data
        title = request.form['title']
        short_desc = request.form['short_desc']
        date_str = request.form['datetime']  # The date input from the form
        description = request.form.get('description', '')
        short_photo = request.files.get('poster')
        long_photo = request.files.get('banner')

        if short_photo and long_photo:
            # Save the photo to the upload folder
            short_filename = secure_filename(short_photo.filename)
            short_photo.save(os.path.join('static','uploads', short_filename))

            long_filename = secure_filename(long_photo.filename)
            long_photo.save(os.path.join('static','uploads', long_filename))
        else:
            short_filename = None
            long_filename = None

        try:
            # Convert the date string to a datetime object
            event_date = datetime.strptime(date_str, "%Y-%m-%dT%H:%M")  # Adjust the format if necessary
            
            # Create new event
            new_event = Event(
                title=title,
                short_desc=short_desc,
                date=event_date,
                description=description,
                short_photo=short_filename,
                long_photo=long_filename,
                is_approved=False
            )
            
            # Add and commit to the database
            db.session.add(new_event)
            db.session.commit()
            # Flash a success message and redirect
            flash('Event created successfully!', 'success')
            return redirect(url_for('reg_events.user_create_event'))

        except Exception as e:
            # Flash an error message
            flash(f'An error occurred: {str(e)}', 'danger')
            return redirect(url_for('reg_events.user_create_event'))

    # Render the form for GET request
    return render_template('users/user_create_events.html')
