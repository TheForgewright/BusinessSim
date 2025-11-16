"""
Main Routes
Home page and general routes
"""
from flask import Blueprint, render_template, redirect, url_for, session

bp = Blueprint('main', __name__)


@bp.route('/')
def index():
    """Home page"""
    if 'player_id' in session:
        # Redirect logged-in users to their dashboard
        if session.get('is_professor'):
            return redirect(url_for('professor.dashboard'))
        else:
            return redirect(url_for('student.dashboard'))

    return render_template('index.html')


@bp.route('/about')
def about():
    """About page"""
    return render_template('about.html')


@bp.route('/logout')
def logout():
    """Logout"""
    session.clear()
    return redirect(url_for('main.index'))
