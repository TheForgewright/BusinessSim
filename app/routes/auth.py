"""
Authentication Routes
Email-based authentication with invitation system
"""
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from app.models import Player
from app import db
from app.utils.email import send_invitation_email, send_password_reset_email, send_welcome_email
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

bp = Blueprint('auth', __name__, url_prefix='/auth')


@bp.route('/login', methods=['GET', 'POST'])
def login():
    """Login page - supports both email and username"""
    if request.method == 'POST':
        login_identifier = request.form.get('login_identifier')  # Can be email or username
        password = request.form.get('password')

        # Try to find player by email first, then username
        player = Player.query.filter_by(email=login_identifier).first()
        if not player:
            player = Player.query.filter_by(username=login_identifier).first()

        if player and player.password_hash and check_password_hash(player.password_hash, password):
            # Check if user needs to set username
            if player.needs_username_setup:
                session['temp_player_id'] = player.id
                flash('Please set your username to complete your account setup.', 'info')
                return redirect(url_for('auth.setup_username'))

            # Update last login
            player.last_login = datetime.utcnow()
            db.session.commit()

            # Login successful
            session['player_id'] = player.id
            session['username'] = player.username
            session['is_professor'] = player.is_professor

            flash(f'Welcome back, {player.username}!', 'success')

            if player.is_professor:
                return redirect(url_for('professor.dashboard'))
            else:
                return redirect(url_for('student.dashboard'))
        else:
            flash('Invalid credentials', 'error')

    return render_template('auth/login.html')


@bp.route('/register', methods=['GET', 'POST'])
def register():
    """Registration page - ONLY for professors"""
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        # Validate
        if not username or not email or not password:
            flash('All fields are required', 'error')
            return render_template('auth/register.html')

        if password != confirm_password:
            flash('Passwords do not match', 'error')
            return render_template('auth/register.html')

        # Check if email exists
        existing = Player.query.filter_by(email=email).first()
        if existing:
            flash('Email already registered', 'error')
            return render_template('auth/register.html')

        # Check if username exists
        existing = Player.query.filter_by(username=username).first()
        if existing:
            flash('Username already taken', 'error')
            return render_template('auth/register.html')

        # Create new professor account
        player = Player(
            username=username,
            email=email,
            password_hash=generate_password_hash(password),
            is_professor=True,  # Only professors can self-register
            email_verified=True,  # Auto-verify professors
            needs_username_setup=False  # They already set username
        )
        db.session.add(player)
        db.session.commit()

        flash(f'Professor account created successfully! Please login.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/register.html')


@bp.route('/set-password/<token>', methods=['GET', 'POST'])
def set_password(token):
    """Set password from invitation email"""
    # Find player by verification token
    player = Player.query.filter_by(verification_token=token).first()

    if not player:
        flash('Invalid or expired invitation link', 'error')
        return redirect(url_for('auth.login'))

    # Verify token is still valid
    if not player.verify_email_token(token):
        flash('This invitation link has expired. Please contact your professor.', 'error')
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        if not password or len(password) < 6:
            flash('Password must be at least 6 characters', 'error')
            return render_template('auth/set_password.html', token=token)

        if password != confirm_password:
            flash('Passwords do not match', 'error')
            return render_template('auth/set_password.html', token=token)

        # Set password and mark email as verified
        player.password_hash = generate_password_hash(password)
        player.mark_email_verified()
        db.session.commit()

        flash('Password set successfully! Please login and set your username.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/set_password.html', token=token, email=player.email)


@bp.route('/setup-username', methods=['GET', 'POST'])
def setup_username():
    """First-time login username setup"""
    # Check if user is in temporary session
    temp_player_id = session.get('temp_player_id')
    if not temp_player_id:
        flash('Please login first', 'error')
        return redirect(url_for('auth.login'))

    player = Player.query.get(temp_player_id)
    if not player:
        flash('Invalid session', 'error')
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
        username = request.form.get('username')

        if not username or len(username) < 3:
            flash('Username must be at least 3 characters', 'error')
            return render_template('auth/setup_username.html')

        # Check if username is taken
        existing = Player.query.filter_by(username=username).first()
        if existing:
            flash('Username already taken. Please choose another.', 'error')
            return render_template('auth/setup_username.html')

        # Set username and mark setup complete
        player.username = username
        player.needs_username_setup = False
        player.last_login = datetime.utcnow()
        db.session.commit()

        # Complete login
        session.pop('temp_player_id', None)
        session['player_id'] = player.id
        session['username'] = player.username
        session['is_professor'] = player.is_professor

        # Send welcome email
        send_welcome_email(player)

        flash(f'Welcome, {username}! Your account is now set up.', 'success')

        if player.is_professor:
            return redirect(url_for('professor.dashboard'))
        else:
            return redirect(url_for('student.dashboard'))

    return render_template('auth/setup_username.html', email=player.email)


@bp.route('/request-reset', methods=['GET', 'POST'])
def request_reset():
    """Request password reset"""
    if request.method == 'POST':
        email = request.form.get('email')

        player = Player.query.filter_by(email=email).first()

        # Always show success message to prevent email enumeration
        flash('If that email is registered, you will receive password reset instructions.', 'info')

        if player:
            # Generate reset token
            token = player.generate_password_reset_token()
            db.session.commit()

            # Send reset email
            send_password_reset_email(player, token)

        return redirect(url_for('auth.login'))

    return render_template('auth/request_reset.html')


@bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    """Reset password with token"""
    # Find player by reset token
    player = Player.query.filter_by(password_reset_token=token).first()

    if not player:
        flash('Invalid or expired reset link', 'error')
        return redirect(url_for('auth.login'))

    # Verify token is still valid
    if not player.verify_password_reset_token(token):
        flash('This reset link has expired. Please request a new one.', 'error')
        return redirect(url_for('auth.request_reset'))

    if request.method == 'POST':
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        if not password or len(password) < 6:
            flash('Password must be at least 6 characters', 'error')
            return render_template('auth/reset_password.html', token=token)

        if password != confirm_password:
            flash('Passwords do not match', 'error')
            return render_template('auth/reset_password.html', token=token)

        # Reset password and clear token
        player.password_hash = generate_password_hash(password)
        player.clear_password_reset_token()
        db.session.commit()

        flash('Password reset successfully! Please login.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/reset_password.html', token=token)


@bp.route('/logout')
def logout():
    """Logout"""
    session.clear()
    flash('Logged out successfully', 'info')
    return redirect(url_for('main.index'))
