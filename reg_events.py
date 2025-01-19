from flask import Blueprint, render_template, request, redirect, url_for, flash,session
from werkzeug.utils import secure_filename
from datetime import datetime
import os
from models import db, Event, User  # Ensure User model is imported

# Create Blueprint
reg_events = Blueprint('reg_events', __name__, template_folder='templates')

# Set the upload folder path
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# Helper function to check allowed file extensions
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@reg_events.route('/profile_dashboard')
def profile_dashboard():
    user_id = session.get('id')  # Get the logged-in user's ID from the session

    if not user_id:
        flash('You must log in first.', 'danger')
        return redirect(url_for('auth.login'))

    # Retrieve the user from the database using their ID
    user = User.query.get(user_id)

    if not user:
        flash('User not found.', 'danger')
        return redirect(url_for('auth.login'))

    # Retrieve the events the user is registered for and created
    registered_events = user.registrations  # List of events the user is registered for
    created_events = user.events_created  # List of events the user created

    # Get the count of registered and created events
    num_registered_events = len(registered_events)
    num_created_events = len(created_events)

    # Pass data to the template
    return render_template(
        'profile/profile_dashboard.html',
        user=user,
        registered_events=registered_events,
        created_events=created_events,
        num_registered_events=num_registered_events,
        num_created_events=num_created_events
    )

@reg_events.route('/edit_dashboard')
def edit_dashboard():
    user_id = session.get('id')  # Get the user ID from the session

    if not user_id:
        flash('You must log in first.', 'danger')
        return redirect(url_for('login'))

    # Retrieve the user from the database
    user = User.query.get(user_id)

    if not user:
        flash('User not found.', 'danger')
        return redirect(url_for('login'))

    # Pass the user object (or relevant data) to the template
    return render_template('profile/edit_profile.html', user=user)

# Profile Update Route
@reg_events.route('/update_profile', methods=['POST'])
def update_profile():
    try:
        # Replace with logic to retrieve the logged-in user
        user = User.query.get(1)  # Example: Fetch user with ID 1

        # Handle profile photo upload
        if 'profile_photo' in request.files:
            profile_photo = request.files['profile_photo']
            if profile_photo and allowed_file(profile_photo.filename):
                filename = secure_filename(profile_photo.filename)
                photo_path = os.path.join(UPLOAD_FOLDER, 'profile_photos', filename)
                profile_photo.save(photo_path)
                user.photo = filename  # Update photo path in the database

        # Update name and email
        user.name = request.form.get('name')
        user.email = request.form.get('email')

        # Update password if provided
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        if password:
            if password == confirm_password:
                user.set_password(password)  # Ensure your User model has a set_password method
            else:
                flash('Passwords do not match.', 'danger')
                return redirect(url_for('reg_events.profile_dashboard'))

        # Commit changes
        db.session.commit()
        flash('Profile updated successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'An error occurred while updating the profile: {str(e)}', 'danger')

    return redirect(url_for('reg_events.profile_dashboard'))

# Manage Event Route
@reg_events.route('/manage_event')
def user_manage_event():
    events = Event.query.all()
    return render_template('profile/manage_events.html', events=events)

# View Event Route
@reg_events.route('/view_event')
def user_view_event():
    events = Event.query.all()
    return render_template('profile/view_events.html', events=events)

# User Create Event Route
@reg_events.route('/Create', methods=['GET', 'POST'])
def user_create_event():
    if request.method == 'POST':
        try:
            # Retrieve form data
            title = request.form['title']
            short_desc = request.form['short_desc']
            date_str = request.form['datetime']
            description = request.form.get('description', '')
            short_photo = request.files.get('poster')
            long_photo = request.files.get('banner')

            # Save uploaded photos
            short_filename = secure_filename(short_photo.filename) if short_photo and allowed_file(short_photo.filename) else None
            long_filename = secure_filename(long_photo.filename) if long_photo and allowed_file(long_photo.filename) else None

            if short_filename:
                short_photo.save(os.path.join(UPLOAD_FOLDER, short_filename))
            if long_filename:
                long_photo.save(os.path.join(UPLOAD_FOLDER, long_filename))

            # Convert the date string to a datetime object
            event_date = datetime.strptime(date_str, "%Y-%m-%dT%H:%M")

            # Create new event
            new_event = Event(
                title=title,
                short_desc=short_desc,
                date=event_date,
                description=description,
                short_photo=short_filename,
                long_photo=long_filename,
                is_approved=False,
                creator_id=session['id']  # Set the creator ID to the current user's ID
            )

            # Add and commit to the database
            db.session.add(new_event)
            db.session.commit()
            flash('Event created successfully!', 'success')
            return redirect(url_for('reg_events.user_create_event'))
        except Exception as e:
            db.session.rollback()
            flash(f'An error occurred: {str(e)}', 'danger')

    return render_template('users/user_create_events.html')
