# app/routes/auth.py
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from app.models.user import User
from app import bcrypt # Import bcrypt from the app package

bp = Blueprint('auth', __name__)

@bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('tasks.dashboard')) # Redirect to dashboard if already logged in

    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')

        # Basic validation
        if not username or not email or not password:
            flash('All fields are required.', 'danger')
            return redirect(url_for('auth.register'))

        # Check if username or email already exists
        existing_user = User.find_by_username(username) or User.find_by_email(email)
        if existing_user:
            flash('Username or email already exists.', 'warning')
            return redirect(url_for('auth.register'))

        # Create new user
        new_user = User(username=username, email=email)
        new_user.set_password(password)
        new_user.save()

        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('login.html', is_register=True) # Reuse login template or create register.html

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('tasks.dashboard')) # Redirect to dashboard if already logged in

    if request.method == 'POST':
        identifier = request.form.get('identifier') # Can be username or email
        password = request.form.get('password')
        remember = request.form.get('remember') == 'on'

        if not identifier or not password:
            flash('Username/Email and password are required.', 'danger')
            return redirect(url_for('auth.login'))

        # Try finding user by username or email
        user = User.find_by_username(identifier) or User.find_by_email(identifier)

        if user and user.check_password(password):
            login_user(user, remember=remember)
            flash('Login successful!', 'success')
            # Redirect to the page user was trying to access, or dashboard
            next_page = request.args.get('next')
            return redirect(next_page or url_for('tasks.dashboard'))
        else:
            flash('Invalid username/email or password.', 'danger')
            return redirect(url_for('auth.login'))

    return render_template('login.html', is_register=False)

@bp.route('/logout')
@login_required # Ensure user is logged in to log out
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login')) 