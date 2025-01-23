from flask import Blueprint, render_template, request, redirect, url_for, flash,session
from werkzeug.utils import secure_filename
from datetime import datetime
import os
import bcrypt
from models import db, Event, User  # Ensure User model is imported
from werkzeug.security import check_password_hash, generate_password_hash
from flask import current_app

# Create Blueprint
reg_events = Blueprint('reg_events', __name__, template_folder='templates')

# Upload folder configuration
UPLOAD_FOLDER = 'static/uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

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

@reg_events.route('/update_profile', methods=['POST'])
def update_profile():
    user_id = request.form.get('user_id')  # Assuming user_id is passed in the form
    user = User.query.get(user_id)

    if not user:
        flash("User not found.", "error")
        return redirect(url_for('reg_events.profile_dashboard'))

    # Handle profile photo update
    if 'profile_photo' in request.files:
        profile_photo = request.files['profile_photo']
        if profile_photo and allowed_file(profile_photo.filename):
            # Rename the file to the user's ID and save it securely
            filename = f"{user_id}.{profile_photo.filename.rsplit('.', 1)[1].lower()}"  # Rename as user_id.extension
            filepath = os.path.join(UPLOAD_FOLDER, filename)
            profile_photo.save(filepath)

            # Update the user's photo path in the database
            user.photo = f'uploads/{filename}'

    # Handle name update
    new_name = request.form.get('name')
    if new_name:
        user.name = new_name

    db.session.commit()
    flash("Profile updated successfully.", "success")
    return redirect(url_for('reg_events.profile_dashboard'))



# Route to update password
@reg_events.route('/update_password', methods=['POST'])
def update_password():
    user_id = session.get('id')  # Retrieve the user ID from the session
    if not user_id:
        flash("You must log in first.", "danger")
        return redirect(url_for('auth.login'))

    # Fetch the user from the database
    user = User.query.get(user_id)
    if not user:
        flash("User not found.", "danger")
        return redirect(url_for('reg_events.profile_dashboard'))

    # Get form data
    current_password = request.form.get('current_password')
    new_password = request.form.get('new_password')
    confirm_password = request.form.get('confirm_password')

    # Validate current password
    if not bcrypt.checkpw(current_password.encode('utf-8'), user.password.encode('utf-8')):
        flash("Current password is incorrect.", "danger")
        return redirect(url_for('reg_events.profile_dashboard'))

    # Validate new password and confirm password match
    if new_password != confirm_password:
        flash("New passwords do not match.", "danger")
        return redirect(url_for('reg_events.profile_dashboard'))

    # Hash and update the new password
    hashed_password = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    user.password = hashed_password

    # Commit the change
    try:
        db.session.commit()
        flash("Password updated successfully.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"An error occurred: {str(e)}", "danger")

    return redirect(url_for('reg_events.profile_dashboard'))



# Manage Event Route
@reg_events.route('/manage_events')
def manage_events():
    # Check if the user is logged in
    if 'id' not in session:
        flash('Please log in to access this page.', 'warning')
        return redirect(url_for('login'))  # Redirect to login if not logged in

    # Fetch events created by the logged-in user
    user_id = session['id']  # Get the logged-in user's ID
    user_events = Event.query.filter_by(creator_id=user_id, is_approved=True).all()
    
    return render_template('profile/manage_events.html', events=user_events)

@reg_events.route('/edit_event/<int:event_id>', methods=['GET', 'POST'])
def edit_event(event_id):
    # Fetch the event by ID
    event = Event.query.get_or_404(event_id)
    
    if request.method == 'POST':
        # Get data from the form
        event.title = request.form['title']
        event.short_desc = request.form['short_desc']
        event.description = request.form['description']
        event.date = datetime.strptime(request.form['date'], '%Y-%m-%dT%H:%M')

        # Handle file uploads for poster and banner
        poster = request.files.get('poster')
        banner = request.files.get('banner')

        if poster:
            event.short_photo = poster.filename  # Save file or handle upload
            poster.save(f'./static/uploads/{poster.filename}')

        if banner:
            event.long_photo = banner.filename  # Save file or handle upload
            banner.save(f'./static/uploads/{banner.filename}')

        # Mark as pending approval
        event.is_pending = True
        event.is_approved = False

        # Commit changes to the database but do not approve yet
        db.session.commit()

        flash('Event update submitted for approval!', 'success')
        return redirect(url_for('reg_events.manage_events'))

    return render_template('profile/update_event.html', event=event)



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
