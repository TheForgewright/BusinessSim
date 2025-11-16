"""
Student Routes
Student dashboard and company management
"""
from flask import Blueprint, render_template, session, redirect, url_for, flash, request
from app.models import Company, Player, Game, StockOwnership
from app.game_engine import stock_market
from app import db

bp = Blueprint('student', __name__)


def require_student():
    """Decorator to require student login"""
    if 'player_id' not in session:
        return redirect(url_for('main.index'))
    return None


@bp.route('/dashboard')
def dashboard():
    """Student dashboard"""
    auth_check = require_student()
    if auth_check:
        return auth_check

    player = Player.query.get(session['player_id'])

    # Get player's companies
    companies = Company.query.filter_by(owner_id=player.id).all()

    # Get player's wealth
    wealth = stock_market.get_player_total_wealth(player)

    return render_template('student/dashboard.html',
                          player=player,
                          companies=companies,
                          wealth=wealth)


@bp.route('/company/<int:company_id>')
def company_view(company_id):
    """View company details"""
    auth_check = require_student()
    if auth_check:
        return auth_check

    company = Company.query.get_or_404(company_id)
    player = Player.query.get(session['player_id'])

    # Check if player owns this company
    if company.owner_id != player.id:
        flash('You do not own this company', 'error')
        return redirect(url_for('student.dashboard'))

    return render_template('student/company_view.html', company=company)


@bp.route('/company/<int:company_id>/set_focus', methods=['POST'])
def set_focus(company_id):
    """Set weekly focus for company"""
    auth_check = require_student()
    if auth_check:
        return auth_check

    company = Company.query.get_or_404(company_id)
    player = Player.query.get(session['player_id'])

    if company.owner_id != player.id:
        flash('You do not own this company', 'error')
        return redirect(url_for('student.dashboard'))

    focus = request.form.get('focus')
    valid_focuses = ['Goods', 'IP', 'Influence', 'Labor', 'Cash']

    if focus not in valid_focuses:
        flash('Invalid focus type', 'error')
        return redirect(url_for('student.company_view', company_id=company_id))

    company.weekly_focus = focus
    db.session.commit()

    flash(f'Weekly focus set to {focus}', 'success')
    return redirect(url_for('student.company_view', company_id=company_id))


@bp.route('/company/create', methods=['GET', 'POST'])
def create_company():
    """Create new company"""
    auth_check = require_student()
    if auth_check:
        return auth_check

    player = Player.query.get(session['player_id'])
    games = Game.query.filter_by(is_active=True).all()

    if request.method == 'POST':
        game_id = request.form.get('game_id', type=int)
        name = request.form.get('name')

        game = Game.query.get_or_404(game_id)

        # Create company with default starting resources
        from config import config
        cfg = config['default']

        company = Company(
            game_id=game_id,
            owner_id=player.id,
            name=name,
            cash=cfg.STARTING_CASH,
            goods_active=cfg.STARTING_GOODS,
            ip_active=cfg.STARTING_IP,
            influence_active=cfg.STARTING_INFLUENCE,
            labor_active=cfg.STARTING_LABOR,
            total_shares=cfg.STARTING_SHARES
        )
        db.session.add(company)
        db.session.commit()

        # Create initial stock ownership (player owns 100%)
        ownership = StockOwnership(
            company_id=company.id,
            player_id=player.id,
            investor_name=player.username,
            shares_owned=cfg.STARTING_SHARES,
            is_npc=False
        )
        db.session.add(ownership)
        db.session.commit()

        flash(f'Company "{name}" created successfully!', 'success')
        return redirect(url_for('student.company_view', company_id=company.id))

    return render_template('student/create_company.html', games=games)


@bp.route('/company/<int:company_id>/build')
def build_facility(company_id):
    """Build facility page"""
    auth_check = require_student()
    if auth_check:
        return auth_check

    company = Company.query.get_or_404(company_id)
    player = Player.query.get(session['player_id'])

    if company.owner_id != player.id:
        flash('You do not own this company', 'error')
        return redirect(url_for('student.dashboard'))

    return render_template('student/build_facility.html', company=company)


@bp.route('/market')
def market():
    """Stock market view"""
    auth_check = require_student()
    if auth_check:
        return auth_check

    player = Player.query.get(session['player_id'])

    # Get all companies in active games
    companies = Company.query.join(Company.game).filter(Game.is_active == True).all()

    # Get player's portfolio
    wealth = stock_market.get_player_total_wealth(player)

    return render_template('student/market.html',
                          player=player,
                          companies=companies,
                          wealth=wealth)


@bp.route('/portfolio')
def portfolio():
    """View stock portfolio"""
    auth_check = require_student()
    if auth_check:
        return auth_check

    player = Player.query.get(session['player_id'])
    wealth = stock_market.get_player_total_wealth(player)

    return render_template('student/portfolio.html',
                          player=player,
                          wealth=wealth)
