"""
Professor Routes
Professor dashboard and administrative controls
"""
from flask import Blueprint, render_template, session, redirect, url_for, flash, request, jsonify
from app.models import Game, Company, Player, Event, Tag, FacilityTemplate
from app import db
from app.game_engine import turn_processor
from config import config

bp = Blueprint('professor', __name__)


def require_professor():
    """Decorator to require professor login"""
    if 'player_id' not in session or not session.get('is_professor'):
        return redirect(url_for('main.index'))
    return None


@bp.route('/dashboard')
def dashboard():
    """Professor dashboard"""
    auth_check = require_professor()
    if auth_check:
        return auth_check

    # Get all games
    games = Game.query.all()

    return render_template('professor/dashboard.html', games=games)


@bp.route('/game/<int:game_id>')
def game_view(game_id):
    """View specific game"""
    auth_check = require_professor()
    if auth_check:
        return auth_check

    game = Game.query.get_or_404(game_id)
    companies = Company.query.filter_by(game_id=game_id).all()

    return render_template('professor/game_view.html', game=game, companies=companies)


@bp.route('/game/<int:game_id>/advance', methods=['POST'])
def advance_game(game_id):
    """Advance game by N weeks"""
    auth_check = require_professor()
    if auth_check:
        return auth_check

    game = Game.query.get_or_404(game_id)
    weeks = request.form.get('weeks', type=int, default=1)

    # Get config
    cfg = config['default']

    result = turn_processor.advance_turns(game, weeks, cfg)

    if result['success']:
        # Autosave after successful turn advancement
        from app.game_engine import save_restore
        save_result = save_restore.save_game(game_id, auto=True)

        if save_result['success']:
            flash(f"Advanced {weeks} week(s) to week {game.current_week} (Autosaved: {save_result['filename']})", 'success')
        else:
            flash(f"Advanced {weeks} week(s) to week {game.current_week} (Warning: Autosave failed)", 'warning')
    else:
        flash(f"Error: {result['message']}", 'error')

    return redirect(url_for('professor.game_view', game_id=game_id))


@bp.route('/game/create', methods=['GET', 'POST'])
def create_game():
    """Create new game"""
    auth_check = require_professor()
    if auth_check:
        return auth_check

    if request.method == 'POST':
        name = request.form.get('name')
        total_weeks = request.form.get('total_weeks', type=int, default=50)
        max_turn_advancement = request.form.get('max_turn_advancement', type=int, default=3)

        game = Game(
            name=name,
            total_weeks=total_weeks,
            max_turn_advancement=max_turn_advancement
        )
        db.session.add(game)
        db.session.commit()

        flash(f'Game "{name}" created successfully!', 'success')
        return redirect(url_for('professor.game_view', game_id=game.id))

    return render_template('professor/create_game.html')


@bp.route('/game/<int:game_id>/event/create', methods=['GET', 'POST'])
def create_event(game_id):
    """Create new event"""
    auth_check = require_professor()
    if auth_check:
        return auth_check

    game = Game.query.get_or_404(game_id)

    if request.method == 'POST':
        event = Event(
            game_id=game_id,
            name=request.form.get('name'),
            description=request.form.get('description'),
            event_type=request.form.get('event_type'),
            severity=request.form.get('severity'),
            trigger_week=request.form.get('trigger_week', type=int),
            duration_weeks=request.form.get('duration_weeks', type=int, default=1)
        )
        db.session.add(event)
        db.session.commit()

        flash(f'Event "{event.name}" created!', 'success')
        return redirect(url_for('professor.game_view', game_id=game_id))

    return render_template('professor/create_event.html', game=game)


@bp.route('/templates/facilities')
def facility_templates():
    """Manage facility templates"""
    auth_check = require_professor()
    if auth_check:
        return auth_check

    templates = FacilityTemplate.query.all()
    return render_template('professor/facility_templates.html', templates=templates)


@bp.route('/game/<int:game_id>/tags')
def manage_tags(game_id):
    """Manage product tags for game"""
    auth_check = require_professor()
    if auth_check:
        return auth_check

    game = Game.query.get_or_404(game_id)
    tags = Tag.query.filter_by(game_id=game_id).all()

    return render_template('professor/manage_tags.html', game=game, tags=tags)


@bp.route('/game/<int:game_id>/saves')
def manage_saves(game_id):
    """Manage save files for game"""
    auth_check = require_professor()
    if auth_check:
        return auth_check

    game = Game.query.get_or_404(game_id)

    from app.game_engine import save_restore
    saves = save_restore.list_saves(game_id)

    return render_template('professor/manage_saves.html', game=game, saves=saves)


@bp.route('/game/<int:game_id>/save', methods=['POST'])
def manual_save(game_id):
    """Manually save game"""
    auth_check = require_professor()
    if auth_check:
        return auth_check

    game = Game.query.get_or_404(game_id)
    save_name = request.form.get('save_name', '')

    from app.game_engine import save_restore
    result = save_restore.save_game(game_id, save_name=save_name, auto=False)

    if result['success']:
        flash(f"Game saved: {result['filename']}", 'success')
    else:
        flash(f"Save failed: {result['message']}", 'error')

    return redirect(url_for('professor.manage_saves', game_id=game_id))


@bp.route('/game/restore', methods=['POST'])
def restore_game():
    """Restore game from save file"""
    auth_check = require_professor()
    if auth_check:
        return auth_check

    filepath = request.form.get('filepath')

    if not filepath:
        flash('No save file selected', 'error')
        return redirect(url_for('professor.dashboard'))

    from app.game_engine import save_restore
    result = save_restore.restore_game(filepath)

    if result['success']:
        msg = result['message']
        if result['warnings']:
            msg += ' Warnings: ' + ', '.join(result['warnings'])
        flash(msg, 'success' if not result['warnings'] else 'warning')
        return redirect(url_for('professor.game_view', game_id=result['game_id']))
    else:
        flash(f"Restore failed: {result['message']}", 'error')
        return redirect(url_for('professor.dashboard'))


@bp.route('/game/save/delete', methods=['POST'])
def delete_save():
    """Delete a save file"""
    auth_check = require_professor()
    if auth_check:
        return auth_check

    filepath = request.form.get('filepath')
    game_id = request.form.get('game_id', type=int)

    from app.game_engine import save_restore
    result = save_restore.delete_save(filepath)

    if result['success']:
        flash('Save file deleted', 'success')
    else:
        flash(f"Delete failed: {result['message']}", 'error')

    if game_id:
        return redirect(url_for('professor.manage_saves', game_id=game_id))
    else:
        return redirect(url_for('professor.dashboard'))
