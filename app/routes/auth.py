"""
Authentication Routes
Simple login/register system (for development/demo)
"""
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from app.models import Player
from app import db
from werkzeug.security import generate_password_hash, check_password_hash

bp = Blueprint('auth', __name__, url_prefix='/auth')


@bp.route('/login', methods=['GET', 'POST'])
def login():
    """Login page"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        player = Player.query.filter_by(username=username).first()

        if player and check_password_hash(player.password_hash, password):
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
            flash('Invalid username or password', 'error')

    return render_template('auth/login.html')


@bp.route('/register', methods=['GET', 'POST'])
def register():
    """Registration page"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        is_professor = request.form.get('is_professor') == 'on'

        # Validate
        if not username or not password:
            flash('Username and password required', 'error')
            return render_template('auth/register.html')

        if password != confirm_password:
            flash('Passwords do not match', 'error')
            return render_template('auth/register.html')

        # Check if username exists
        existing = Player.query.filter_by(username=username).first()
        if existing:
            flash('Username already taken', 'error')
            return render_template('auth/register.html')

        # Create new player
        player = Player(
            username=username,
            password_hash=generate_password_hash(password),
            is_professor=is_professor
        )
        db.session.add(player)
        db.session.commit()

        flash(f'Account created successfully! Please login.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/register.html')


@bp.route('/logout')
def logout():
    """Logout"""
    session.clear()
    flash('Logged out successfully', 'info')
    return redirect(url_for('main.index'))
