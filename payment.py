import razorpay
from flask import Blueprint, request, jsonify, current_app
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
        current_app.logger.error("No data received in the request")
        return jsonify({"error": "Invalid data provided"}), 400

    try:
        # Extract details from the JSON payload
        name = data.get('name')
        email = data.get('email')
        phone = data.get('phone')
        remarks = data.get('remarks', '')
        event_id = data.get('event_id')
        amount = int(data.get('amount', 0)) * 100  # Convert to paise

        current_app.logger.info(f"Received payment request: name={name}, email={email}, phone={phone}, event_id={event_id}, amount={amount}")

        # Validate required fields
        if not (name and email and phone and event_id and amount):
            current_app.logger.error("Missing required fields in the request")
            return jsonify({"error": "All fields are required!"}), 400

        # Check if the event exists
        event = Event.query.get(event_id)
        if not event:
            current_app.logger.error(f"Event not found: event_id={event_id}")
            return jsonify({"error": "Event not found."}), 404

        # Create Razorpay order
        order = create_payment_order(amount, email, event.title)  # Use event.title instead of event.name
        if not order:
            current_app.logger.error("Failed to create Razorpay order")
            return jsonify({"error": "Failed to create payment order. Please try again."}), 500

        current_app.logger.info(f"Razorpay order created: order_id={order['id']}")

        # Check if the user exists
        user = User.query.filter_by(email=email).first()
        if not user:
            current_app.logger.error(f"User not found: email={email}")
            return jsonify({"error": "User not found."}), 404

        # Save registration details
        new_registration = Registration(
            user_id=user.id,
            event_id=event_id,
            phone_no=phone,
            remarks=remarks,
            payment_order_id=order['id'],
            payment_status='pending'
        )
        db.session.add(new_registration)
        db.session.commit()

        current_app.logger.info(f"Registration saved: registration_id={new_registration.id}")

        return jsonify({"order": order}), 200
    except Exception as e:
        current_app.logger.error(f"Error during payment initiation: {str(e)}", exc_info=True)
        return jsonify({"error": "An internal error occurred. Please try again later."}), 500

@payment_bp.route('/success', methods=['POST'])
def payment_success():
    data = request.get_json()
    payment_id = data.get('razorpay_payment_id')
    order_id = data.get('razorpay_order_id')
    signature = data.get('razorpay_signature')

    try:
        current_app.logger.info(f"Received payment success callback: payment_id={payment_id}, order_id={order_id}")

        # Verify payment signature
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
            current_app.logger.info(f"Payment status updated: registration_id={registration.id}")
        else:
            current_app.logger.error(f"Registration not found: order_id={order_id}")
            return jsonify({"error": "Registration not found."}), 404

        return jsonify({"message": "Payment successful!"}), 200
    except Exception as e:
        current_app.logger.error(f"Payment verification failed: {str(e)}", exc_info=True)
        return jsonify({"error": "Payment verification failed. Please contact support."}), 400

def create_payment_order(amount, email, event_name):
    try:
        # Generate a shorter receipt ID using user email and event name
        receipt_id = f"order_{email[:10]}_{event_name[:20]}"  # Truncate email and event name
        receipt_id = receipt_id.replace(" ", "_")  # Replace spaces with underscores
        receipt_id = receipt_id[:40]  # Ensure the receipt ID is no more than 40 characters

        data = {
            "amount": amount,
            "currency": "INR",
            "receipt": receipt_id,  # Use the shortened receipt ID
            "notes": {"event": event_name, "email": email}
        }
        current_app.logger.info(f"Creating Razorpay order: amount={amount}, email={email}, event_name={event_name}")
        return client.order.create(data)
    except Exception as e:
        current_app.logger.error(f"Error creating payment order: {str(e)}", exc_info=True)
        return None