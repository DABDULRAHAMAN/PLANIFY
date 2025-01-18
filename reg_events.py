from flask import Blueprint, render_template, request, redirect, url_for, flash
from werkzeug.utils import secure_filename
from datetime import datetime
import os
from models import db, Event

# Create Blueprint
reg_events = Blueprint('reg_events', __name__, template_folder='templates')

# Set the upload folder path
UPLOAD_FOLDER = 'static/uploads'

@reg_events.route('/Create', methods=['GET', 'POST'])
def user_create_event():
    if request.method == 'POST':
        try:
            # Retrieve form data
            title = request.form['title']
            short_desc = request.form['short_desc']
            description = request.form['description']
            datetime_str = request.form['datetime']
            event_date = datetime.strptime(datetime_str, '%Y-%m-%dT%H:%M')  # Convert to datetime object

            # Handle file uploads
            short_photo = request.files['poster']
            long_photo = request.files['banner']

            # Save files to the /static/uploads folder
            if not os.path.exists(UPLOAD_FOLDER):
                os.makedirs(UPLOAD_FOLDER)

            short_photo_filename = None
            long_photo_filename = None

            if short_photo:
                short_photo_filename = secure_filename(short_photo.filename)
                short_photo_path = os.path.join(UPLOAD_FOLDER, short_photo_filename)
                short_photo.save(short_photo_path)

            if long_photo:
                long_photo_filename = secure_filename(long_photo.filename)
                long_photo_path = os.path.join(UPLOAD_FOLDER, long_photo_filename)
                long_photo.save(long_photo_path)

            # Create a new Event object and add to the database
            new_event = Event(
                title=title,
                short_desc=short_desc,
                description=description,
                date=event_date,
                short_photo=f'/static/uploads/{short_photo_filename}' if short_photo_filename else None,
                long_photo=f'/static/uploads/{long_photo_filename}' if long_photo_filename else None
            )

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
