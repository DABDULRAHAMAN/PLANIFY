from flask import Blueprint, render_template, request, session, redirect, url_for, flash
from models import db, User, Event, Registration
from functools import wraps
from datetime import datetime
from werkzeug.utils import secure_filename
import os

# Initialize admin blueprint
admin_blueprint = Blueprint('admin', __name__, template_folder='templates/admin')

# Utility: Admin Login Required Decorator
def admin_login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('admin_logged_in'):
            flash('Admin login required!', 'warning')
            return redirect(url_for('admin.admin_login'))
        return f(*args, **kwargs)
    return decorated_function

# Admin Login Route
@admin_blueprint.route('/admin-login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        admin_id = request.form.get('admin_id')
        password = request.form.get('admin_password')
        # Hardcoded credentials (replace with a secure mechanism in production)
        if admin_id == 'admin' and password == 'admin':
            session['admin_logged_in'] = True
            # flash('Admin login successful!', 'success')
            return redirect(url_for('admin.admin_dashboard'))
        flash('Invalid credentials. Please try again.', 'danger')
    return render_template('admin/admin_login.html')

# Admin Dashboard Route
@admin_blueprint.route('/admin-dashboard')
@admin_login_required
def admin_dashboard():
    # Calculate statistics
    users_count = User.query.count()
    events_count = Event.query.count()
    registrations_count = Registration.query.count()

    # Pass statistics to the template
    return render_template(
        'admin/admin_dashboard.html',
        users_count=users_count,
        events_count=events_count,
        registrations_count=registrations_count
    )

#admin create event route
@admin_blueprint.route('/create-events', methods=['GET', 'POST'])
@admin_login_required
def create_events():
    if request.method == 'POST':
        # Retrieve form data
        title = request.form['title']
        short_desc = request.form['short_desc']
        date_str = request.form['date']  # The date input from the form
        description = request.form.get('description', '')
        short_photo = request.files.get('short_photo')
        long_photo = request.files.get('long_photo')

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
            flash('Event created successfully!', 'success')
            return redirect(url_for('admin.manage_events'))  # Redirect to manage events page
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating event: {str(e)}', 'danger')

    # If it's a GET request, render the event creation form
    return render_template('admin/create_events.html')


@admin_blueprint.route('/manage-events', methods=['GET'])
@admin_login_required
def manage_events():
    # Fetch only approved events for display
    events = Event.query.filter_by(is_approved=True).order_by(Event.date.asc()).all()
    return render_template('admin/manage_events.html', events=events)

@admin_blueprint.route('/edit-event/<int:event_id>', methods=['GET', 'POST'])
@admin_login_required
def edit_event(event_id):
    event = Event.query.get_or_404(event_id)  # Fetch the event by ID

    if request.method == 'POST':
        # Update event fields
        event.title = request.form['title']
        event.short_desc = request.form['short_desc']
        event.description = request.form.get('description', event.description)
        date_str = request.form['date']
        event.date = datetime.strptime(date_str, "%Y-%m-%dT%H:%M")  # Convert date

        # Update photo if provided
        short_photo = request.files.get('short_photo')
        long_photo = request.files.get('long_photo')

        if short_photo:
            short_filename = secure_filename(short_photo.short_filename)
            short_photo.save(os.path.join('static', 'uploads', short_filename))
            event.short_photo = short_filename

        if long_photo:
            long_filename = secure_filename(long_photo.long_filename)
            long_photo.save(os.path.join('static', 'uploads', long_filename))
            event.long_photo = long_filename

        try:
            db.session.commit()
            flash('Event updated successfully!', 'success')
            return redirect(url_for('admin.manage_events'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating event: {str(e)}', 'danger')

    return render_template('admin/edit_event.html', event=event)

import os

@admin_blueprint.route('/delete-event/<int:event_id>', methods=['POST'])
@admin_login_required
def delete_event(event_id):
    # Fetch the event by ID
    event = Event.query.get_or_404(event_id)

    try:
        # Delete associated photo files if they exist
        if event.short_photo:
            short_photo_path = os.path.join('static', 'uploads', event.short_photo)
            if os.path.exists(short_photo_path):
                os.remove(short_photo_path)

        if event.long_photo:
            long_photo_path = os.path.join('static', 'uploads', event.long_photo)
            if os.path.exists(long_photo_path):
                os.remove(long_photo_path)

        # Delete the event record from the database
        db.session.delete(event)
        db.session.commit()
        flash('Event deleted successfully!', 'success')

    except Exception as e:
        db.session.rollback()  # Rollback the transaction in case of error
        flash(f'Error deleting event: {str(e)}', 'danger')

    # Redirect to the event management page
    return redirect(url_for('admin.manage_events'))


@admin_blueprint.route('/edit_registration/<int:registration_id>', methods=['GET', 'POST'])
def edit_registration(registration_id):
    registration = Registration.query.get_or_404(registration_id)
    if request.method == 'POST':
        registration.remarks = request.form.get('remarks')  # Example edit
        db.session.commit()
        flash('Registration updated successfully!', 'success')
        return redirect(url_for('events_file.view_registrations'))
    return render_template('edit_registration.html', registration=registration)

@admin_blueprint.route('/delete_registration/<int:registration_id>', methods=['POST'])
@admin_login_required  # Ensure only admins can access this route
def delete_registration(registration_id):
    try:
        # Fetch the registration or return 404 if it doesn't exist
        registration = Registration.query.get_or_404(registration_id)
        
        # Delete the registration
        db.session.delete(registration)
        db.session.commit()

        # Flash a success message
        flash(f'Registration for "{registration.event.title}" deleted successfully!', 'success')
    except Exception as e:
        # Handle unexpected errors
        flash(f'An error occurred while deleting the registration: {str(e)}', 'danger')

    # Redirect to the registrations view page
    return redirect(url_for('events_file.view_registrations'))

@admin_blueprint.route('/admin/review_event')
@admin_login_required
def review_event():
    pending_events = Event.query.filter_by(is_approved=False).all()
    return render_template('admin/review_event.html', events=pending_events)

@admin_blueprint.route('/approve-event/<int:event_id>', methods=['POST'])
@admin_login_required
def approve_event(event_id):
    # Fetch the event by ID
    event = Event.query.get_or_404(event_id)
    # Update the is_approved field to True
    event.is_approved = True
    db.session.commit()
    flash('Event approved successfully!', 'success')
    return redirect(url_for('admin.manage_events'))

@admin_blueprint.route('/reject-event/<int:event_id>', methods=['POST'])
@admin_login_required
def reject_event(event_id):
    # Fetch the event by ID
    event = Event.query.get_or_404(event_id)
    # Optionally delete the event or mark it as rejected (custom logic)
    db.session.delete(event)  # Deletes the event from the database
    db.session.commit()
    flash('Event rejected successfully!', 'danger')
    return redirect(url_for('admin.manage_events'))

# Admin Logout Route
@admin_blueprint.route('/admin-logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    flash('You have been logged out as admin.', 'info')
    return redirect(url_for('admin.admin_login'))
