from flask import Blueprint, render_template, request, session, redirect, url_for, flash
from models import db, User, Event, Registration

# Create Blueprint
events_file = Blueprint('events_file', __name__, template_folder='templates')

# Route: Display all events
@events_file.route('/explore-events')
def explore_events():
    events_list = Event.query.all()  # Fetch events from the database
    return render_template('users/events.html', events=events_list)

# Define the route for the About Us page
@events_file.route('/about-us')
def about_us():
    return render_template('users/contact_us.html')

# Route: Display event details
@events_file.route('/events_details/<int:event_id>', methods=['GET'])
def event_details(event_id):
    event = Event.query.get_or_404(event_id)  # Automatically handles event not found
    return render_template('users/event_details.html', event=event)

@events_file.route('/event_registration/<int:event_id>')
def event_registration_page(event_id):
    event = Event.query.get(event_id)
    if not event:
        flash('Event not found!', 'error')
        return redirect(url_for('events_file.explore_events'))
    return render_template('users/events_registration.html', event=event)

@events_file.route('/register_event', methods=['POST'])
def register_event_user():
    # Extract form data
    email = request.form.get('email')  # Use email to find the user
    event_id = request.form.get('event_id')
    remarks = request.form.get('remarks', '')

    # Validate required fields
    if not (email and event_id):
        flash('Email and event are required!', 'error')
        return redirect(url_for('events_file.explore_events'))

    # Check if user exists
    user = User.query.filter_by(email=email).first()
    if not user:
        flash('User with the provided email does not exist!', 'error')
        return redirect(url_for('events_file.explore_events'))

    # Check if event exists
    event = Event.query.get(event_id)
    if not event:
        flash('Invalid event!', 'error')
        return redirect(url_for('events_file.explore_events'))

    # Check if the user is already registered for the event
    existing_registration = Registration.query.filter_by(user_id=user.id, event_id=event_id).first()
    if existing_registration:
        flash('You are already registered for this event.', 'info')
        return redirect(url_for('events_file.explore_events'))

    # Register the user for the event
    new_registration = Registration(user_id=user.id, event_id=event_id, remarks=remarks)
    db.session.add(new_registration)
    db.session.commit()

    flash('Successfully registered for the event!', 'success')
    return redirect(url_for('events_file.explore_events'))

# Route: Display all registrations
@events_file.route('/registrations', methods=['GET'])
def view_registrations():
    registrations = (
        db.session.query(Registration, User.name, User.email, Event.title)
        .join(User, Registration.user_id == User.id)
        .join(Event, Registration.event_id == Event.id)
        .all()
    )
    return render_template('view_registration.html', registrations=registrations)

