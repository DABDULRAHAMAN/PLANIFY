import razorpay
from flask import Blueprint, render_template, request, redirect, current_app, url_for, flash
from models import db, Registration, User, Event

# Blueprint for payment-related routes
payment_bp = Blueprint('payment', __name__)

# Razorpay client setup
razorpay_key_id = "rzp_test_xoGhUNgyxCjvch"  # Replace with your test key ID
razorpay_secret_key = "s1smm98jw7OYghenqrnfEIgT"  # Replace with your secret key
client = razorpay.Client(auth=(razorpay_key_id, razorpay_secret_key))

@payment_bp.route('/payment', methods=['POST'])
def payment():
    """
    Route to initiate payment after registration form submission.
    """
    # Get form data
    name = request.form.get('name')
    email = request.form.get('email')
    phone = request.form.get('phone')
    remarks = request.form.get('remarks', '')
    event_id = request.form.get('event_id')
    amount = int(request.form.get('amount')) * 100  # Convert to paise

    # Fetch event details from the database
    event = Event.query.get(event_id)
    if not event:
        flash("Event not found.", "error")
        return redirect(url_for('events_file.explore_events'))

    # Create Razorpay order
    try:
        order = create_payment_order(amount, email, event.name)

        if order is None:
            flash("Failed to create payment order.", "error")
            return redirect(url_for('events_file.explore_events'))

        # Save order details in the database
        new_registration = Registration(
            user_id=User.query.filter_by(email=email).first().id,
            event_id=event_id,
            phone_no=phone,
            remarks=remarks,
            payment_order_id=order['id'],
            payment_status='pending'
        )
        db.session.add(new_registration)
        db.session.commit()

        # Pass order details to the template
        return render_template(
            'users/payment.html',
            order=order,
            amount=amount,
            key=razorpay_key_id,
            event=event
        )
    except Exception as e:
        flash(f"An error occurred while creating the payment order: {e}", "error")
        return redirect(url_for('events_file.explore_events'))


@payment_bp.route('/success', methods=['POST'])
def payment_success():
    """
    Route to handle successful payments after Razorpay verification.
    """
    # Extract Razorpay payment details
    payment_id = request.form.get('razorpay_payment_id')
    order_id = request.form.get('razorpay_order_id')
    signature = request.form.get('razorpay_signature')

    try:
        # Verify the payment signature
        params = {
            'razorpay_order_id': order_id,
            'razorpay_payment_id': payment_id,
            'razorpay_signature': signature
        }
        client.utility.verify_payment_signature(params)

        # Update payment status in the database
        registration = Registration.query.filter_by(payment_order_id=order_id).first()
        if registration:
            registration.payment_status = 'completed'
            db.session.commit()

        flash('Payment successful! You are registered for the event.', 'success')
        return redirect(url_for('events_file.event_details', event_id=registration.event_id))
    except Exception as e:
        flash(f'Payment verification failed: {e}', 'error')
        return redirect(url_for('events_file.explore_events'))


def create_payment_order(amount, email, event_name):
    """
    Creates a Razorpay payment order.
    """
    try:
        data = {
            "amount": int(amount),  # Amount in paise
            "currency": "INR",
            "receipt": f"order_{email}_{event_name}",
            "notes": {
                "event": event_name,
                "email": email
            }
        }

        # Create the payment order via Razorpay API
        payment_order = client.order.create(data)
        payment_url = f"https://checkout.razorpay.com/v1/checkout.js?order_id={payment_order['id']}"

        # Return the payment order ID and URL
        return {
            'id': payment_order['id'],
            'url': payment_url
        }
    except Exception as e:
        current_app.logger.error(f"Payment order creation failed: {e}")
        return None
