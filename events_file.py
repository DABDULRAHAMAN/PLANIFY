from flask import Blueprint, render_template, request, session, redirect, url_for, flash
from models import db, User, Event, Registration
from payment import create_payment_order  # Import payment order creation function

# Create Blueprint
events_file = Blueprint('events_file', __name__, template_folder='templates')

# Route: Display all events
@events_file.route('/explore-events')
def explore_events():
    # Fetch only approved events
    events_list = Event.query.filter_by(is_approved=True).all()

    # Fetch the logged-in user
    if 'email' in session:
        user = User.query.filter_by(email=session['email']).first()
    else:
        user = None

    return render_template('users/events.html', events=events_list, user=user)

# Route: About Us page
@events_file.route('/about-us')
def about_us():
    # Fetch the logged-in user
    if 'email' in session:
        user = User.query.filter_by(email=session['email']).first()
    else:
        user = None
    return render_template('users/contact_us.html', user=user)

# Route: Display event details
@events_file.route('/events_details/<int:event_id>', methods=['GET'])
def event_details(event_id):
    event = Event.query.get_or_404(event_id)  # Automatically handles event not found
    return render_template('users/event_details.html', event=event)

# Route: Event registration page
@events_file.route('/event_registration/<int:event_id>')
def event_registration_page(event_id):
    event = Event.query.get(event_id)
    if not event:
        flash('Event not found!', 'error')
        return redirect(url_for('events_file.explore_events'))
    return render_template('users/events_registration.html', event=event)

# Route: Register for an event
@events_file.route('/register_event', methods=['POST'])
def register_event_user():
    # Extract form data
    email = request.form.get('email')
    event_id = request.form.get('event_id')
    phone = request.form.get('phone')
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

    # Create a Razorpay order
    amount = int(event.fee * 100)  # Convert to paise
    payment_order = create_payment_order({'amount': amount, 'currency': 'INR', 'receipt': f'receipt_{user.id}_{event_id}'})

    # Store the registration and payment order ID in the database
    new_registration = Registration(
        user_id=user.id,
        event_id=event_id,
        phone_no=phone,
        remarks=remarks,
        payment_order_id=payment_order['id'],
        payment_status='pending'
    )
    db.session.add(new_registration)
    db.session.commit()

    # Redirect to payment page
    return render_template('payment_page.html', payment_order=payment_order, event=event)

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