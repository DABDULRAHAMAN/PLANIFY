import razorpay
from flask import Blueprint, render_template, request, redirect, current_app, url_for, flash, jsonify
from models import db, Registration, User, Event

# Blueprint for payment-related routes
payment_bp = Blueprint('payment', __name__)

# Razorpay client setup
razorpay_key_id = "rzp_test_xoGhUNgyxCjvch"  # Replace with your test key ID
razorpay_secret_key = "s1smm98jw7OYghenqrnfEIgT"  # Replace with your secret key
client = razorpay.Client(auth=(razorpay_key_id, razorpay_secret_key))

@payment_bp.route('/payment', methods=['POST'])
def payment():
    data = request.get_json()  # Parse JSON payload
    if not data:
        return jsonify({"error": "Invalid data provided"}), 400

    # Extract details from the JSON payload
    name = data.get('name')
    email = data.get('email')
    phone = data.get('phone')
    remarks = data.get('remarks', '')
    event_id = data.get('event_id')
    amount = int(data.get('amount', 0)) * 100  # Convert to paise

    if not (name and email and phone and event_id and amount):
        return jsonify({"error": "All fields are required!"}), 400

    event = Event.query.get(event_id)
    if not event:
        return jsonify({"error": "Event not found."}), 404

    try:
        order = create_payment_order(amount, email, event.name)
        if not order:
            return jsonify({"error": "Failed to create payment order."}), 500

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

        return jsonify({"order": order}), 200
    except Exception as e:
        current_app.logger.error(f"Error during payment initiation: {e}")
        return jsonify({"error": "An internal error occurred. Please try again later."}), 500


@payment_bp.route('/success', methods=['POST'])
def payment_success():
    data = request.get_json()
    payment_id = data.get('razorpay_payment_id')
    order_id = data.get('razorpay_order_id')
    signature = data.get('razorpay_signature')

    try:
        params = {
            'razorpay_order_id': order_id,
            'razorpay_payment_id': payment_id,
            'razorpay_signature': signature
        }
        client.utility.verify_payment_signature(params)

        registration = Registration.query.filter_by(payment_order_id=order_id).first()
        if registration:
            registration.payment_status = 'completed'
            db.session.commit()

        return jsonify({"message": "Payment successful!"}), 200
    except Exception as e:
        current_app.logger.error(f"Payment verification failed: {e}")
        return jsonify({"error": "Payment verification failed."}), 400


def create_payment_order(amount, email, event_name):
    try:
        data = {
            "amount": amount,
            "currency": "INR",
            "receipt": f"order_{email}_{event_name}",
            "notes": {"event": event_name, "email": email}
        }
        return client.order.create(data)
    except Exception as e:
        current_app.logger.error(f"Error creating payment order: {e}")
        return None
