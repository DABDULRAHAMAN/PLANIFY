from flask import Flask, render_template, request, redirect, session, url_for, flash
from events_file import events_file  # Import events blueprint
from admin import admin_blueprint  # Import admin blueprint
from models import db, User, Event, Registration
import bcrypt
from functools import wraps

# Initialize Flask app
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'secret_key'

# Initialize SQLAlchemy
db.init_app(app)

# Register Blueprints
app.register_blueprint(events_file, url_prefix="/users")
app.register_blueprint(admin_blueprint, url_prefix="/admin")

# Create database tables
with app.app_context():
    db.create_all()


# Utility: Login Required Decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'email' not in session:
            flash('You need to log in first!', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


# Routes
@app.route('/')
def index():
    return render_template('index.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']

        # Check if email already exists
        if User.query.filter_by(email=email).first():
            flash('Email already exists. Please use a different email.', 'danger')
            return redirect(url_for('register'))

        # Create new user
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        new_user = User(name=name, email=email, password=hashed_password)

        try:
            db.session.add(new_user)
            db.session.commit()
            flash('Registration successful! You can now log in.', 'success')
            print("data added")
            return redirect(url_for('login'))
        except Exception:
            db.session.rollback()
            flash('Registration failed. Please try again.', 'danger')
            print("Fail")
            return redirect(url_for('register'))

    return render_template('index.html')  # Use a dedicated registration template


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        user = User.query.filter_by(email=email).first()
        if user and bcrypt.checkpw(password.encode('utf-8'), user.password.encode('utf-8')):
            session['email'] = user.email
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid email or password. Please try again.', 'danger')
            return redirect(url_for('login'))

    return render_template('index.html')  # Use a dedicated login template


@app.route('/users/dashboard')
@login_required
def dashboard():
    user = User.query.filter_by(email=session['email']).first()
    return render_template('users/dashboard.html', user=user)


@app.route('/logout')
def logout():
    session.pop('email', None)
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

# Main entry point
if __name__ == "__main__":
    app.run(debug=True)
