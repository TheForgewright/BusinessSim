"""
API Routes
JSON API endpoints for AJAX calls
"""
from flask import Blueprint, jsonify, request, session
from app.models import Company, Player, Facility, Debt, Product, Tag, Game
from app.game_engine import (
    stock_market,
    debt_management,
    product_management,
    capital_generation,
    facility_management
)
from app import db
from config import config

bp = Blueprint('api', __name__)


def get_current_player():
    """Get current logged-in player"""
    if 'player_id' not in session:
        return None
    return Player.query.get(session['player_id'])


@bp.route('/company/<int:company_id>/data')
def company_data(company_id):
    """Get company data as JSON"""
    company = Company.query.get_or_404(company_id)
    return jsonify(company.to_dict())


@bp.route('/stock/buy', methods=['POST'])
def buy_stock():
    """Buy stock"""
    player = get_current_player()
    if not player:
        return jsonify({'success': False, 'message': 'Not logged in'}), 401

    data = request.get_json()
    company_id = data.get('company_id')
    shares = data.get('shares', 0)

    company = Company.query.get_or_404(company_id)
    game = company.game

    result = stock_market.execute_stock_purchase(
        player, company, shares, game.current_week
    )

    if result['success']:
        db.session.commit()

    return jsonify(result)


@bp.route('/stock/sell', methods=['POST'])
def sell_stock():
    """Sell stock"""
    player = get_current_player()
    if not player:
        return jsonify({'success': False, 'message': 'Not logged in'}), 401

    data = request.get_json()
    company_id = data.get('company_id')
    shares = data.get('shares', 0)

    company = Company.query.get_or_404(company_id)
    game = company.game

    result = stock_market.execute_stock_sale(
        player, company, shares, game.current_week
    )

    if result['success']:
        db.session.commit()

    return jsonify(result)


@bp.route('/debt/create', methods=['POST'])
def create_debt():
    """Create new debt (take out loan)"""
    player = get_current_player()
    if not player:
        return jsonify({'success': False, 'message': 'Not logged in'}), 401

    data = request.get_json()
    company_id = data.get('company_id')
    company = Company.query.get_or_404(company_id)

    if company.owner_id != player.id:
        return jsonify({'success': False, 'message': 'Not your company'}), 403

    game = company.game

    debt = debt_management.create_debt(
        company,
        game.current_week,
        name=data.get('name'),
        creditor=data.get('creditor'),
        principal=data.get('principal'),
        interest_rate=data.get('interest_rate'),
        compounding_type=data.get('compounding_type', 'not_compounding'),
        collateral=data.get('collateral'),
        due_date=data.get('due_date'),
        term_weeks=data.get('term_weeks'),
        agreed_payment_amount=data.get('agreed_payment_amount'),
        auto_pay=data.get('auto_pay', False)
    )

    db.session.commit()

    return jsonify({
        'success': True,
        'debt': debt.to_dict(),
        'message': f'Loan created: {debt.principal} Cash added to company'
    })


@bp.route('/debt/<int:debt_id>/pay', methods=['POST'])
def pay_debt():
    """Make manual payment on debt"""
    player = get_current_player()
    if not player:
        return jsonify({'success': False, 'message': 'Not logged in'}), 401

    data = request.get_json()
    payment_amount = data.get('amount', 0)

    debt = Debt.query.get_or_404(debt_id)
    company = debt.company

    if company.owner_id != player.id:
        return jsonify({'success': False, 'message': 'Not your company'}), 403

    if company.cash < payment_amount:
        return jsonify({
            'success': False,
            'message': f'Insufficient cash (need {payment_amount}, have {company.cash})'
        })

    # Make payment
    result = debt_management.make_debt_payment(debt, payment_amount)
    company.cash -= result['total_paid']

    db.session.commit()

    return jsonify({
        'success': True,
        'payment_result': result,
        'message': f'Paid {result["total_paid"]} on debt'
    })


@bp.route('/product/create', methods=['POST'])
def create_product():
    """Create new product from capital"""
    player = get_current_player()
    if not player:
        return jsonify({'success': False, 'message': 'Not logged in'}), 401

    data = request.get_json()
    company_id = data.get('company_id')
    company = Company.query.get_or_404(company_id)

    if company.owner_id != player.id:
        return jsonify({'success': False, 'message': 'Not your company'}), 403

    game = company.game

    result = product_management.create_product(
        company,
        data.get('name'),
        data.get('ip_invested', 0),
        data.get('goods_invested', 0),
        data.get('tags', []),
        game.current_week
    )

    if result['success']:
        db.session.commit()
        return jsonify({
            'success': True,
            'product': result['product'].to_dict(),
            'message': result['message']
        })
    else:
        return jsonify(result)


@bp.route('/facility/<int:facility_id>/shutdown', methods=['POST'])
def shutdown_facility(facility_id):
    """Shutdown facility"""
    player = get_current_player()
    if not player:
        return jsonify({'success': False, 'message': 'Not logged in'}), 401

    facility = Facility.query.get_or_404(facility_id)
    company = facility.company

    if company.owner_id != player.id:
        return jsonify({'success': False, 'message': 'Not your company'}), 403

    facility_management.shutdown_facility(facility)
    db.session.commit()

    return jsonify({
        'success': True,
        'message': f'Facility "{facility.name}" shut down'
    })


@bp.route('/facility/<int:facility_id>/activate', methods=['POST'])
def activate_facility(facility_id):
    """Activate facility"""
    player = get_current_player()
    if not player:
        return jsonify({'success': False, 'message': 'Not logged in'}), 401

    facility = Facility.query.get_or_404(facility_id)
    company = facility.company

    if company.owner_id != player.id:
        return jsonify({'success': False, 'message': 'Not your company'}), 403

    success = facility_management.activate_facility(facility)

    if success:
        db.session.commit()
        return jsonify({
            'success': True,
            'message': f'Facility "{facility.name}" activated'
        })
    else:
        return jsonify({
            'success': False,
            'message': 'Cannot activate destroyed facility (0% condition)'
        })


@bp.route('/company/<int:company_id>/capital/transfer', methods=['POST'])
def transfer_capital(company_id):
    """Transfer capital between active and backed-up"""
    player = get_current_player()
    if not player:
        return jsonify({'success': False, 'message': 'Not logged in'}), 401

    company = Company.query.get_or_404(company_id)

    if company.owner_id != player.id:
        return jsonify({'success': False, 'message': 'Not your company'}), 403

    data = request.get_json()
    capital_type = data.get('capital_type').lower()
    amount = data.get('amount', 0)
    direction = data.get('direction')  # 'to_backup' or 'to_active'

    if capital_type not in ['goods', 'ip', 'influence', 'labor']:
        return jsonify({'success': False, 'message': 'Invalid capital type'})

    # Perform transfer
    if direction == 'to_backup':
        # Move from active to backed-up
        if capital_type == 'goods':
            if company.goods_active >= amount:
                company.goods_active -= amount
                company.goods_backed_up += amount
            else:
                return jsonify({'success': False, 'message': 'Insufficient active capital'})
        elif capital_type == 'ip':
            if company.ip_active >= amount:
                company.ip_active -= amount
                company.ip_backed_up += amount
            else:
                return jsonify({'success': False, 'message': 'Insufficient active capital'})
        elif capital_type == 'influence':
            if company.influence_active >= amount:
                company.influence_active -= amount
                company.influence_backed_up += amount
            else:
                return jsonify({'success': False, 'message': 'Insufficient active capital'})
        elif capital_type == 'labor':
            if company.labor_active >= amount:
                company.labor_active -= amount
                company.labor_backed_up += amount
            else:
                return jsonify({'success': False, 'message': 'Insufficient active capital'})

    elif direction == 'to_active':
        # Move from backed-up to active
        if capital_type == 'goods':
            if company.goods_backed_up >= amount:
                company.goods_backed_up -= amount
                company.goods_active += amount
            else:
                return jsonify({'success': False, 'message': 'Insufficient backed-up capital'})
        elif capital_type == 'ip':
            if company.ip_backed_up >= amount:
                company.ip_backed_up -= amount
                company.ip_active += amount
            else:
                return jsonify({'success': False, 'message': 'Insufficient backed-up capital'})
        elif capital_type == 'influence':
            if company.influence_backed_up >= amount:
                company.influence_backed_up -= amount
                company.influence_active += amount
            else:
                return jsonify({'success': False, 'message': 'Insufficient backed-up capital'})
        elif capital_type == 'labor':
            if company.labor_backed_up >= amount:
                company.labor_backed_up -= amount
                company.labor_active += amount
            else:
                return jsonify({'success': False, 'message': 'Insufficient backed-up capital'})
    else:
        return jsonify({'success': False, 'message': 'Invalid direction'})

    db.session.commit()

    return jsonify({
        'success': True,
        'message': f'Transferred {amount} {capital_type} to {"backup" if direction == "to_backup" else "active"}'
    })


@bp.route('/game/<int:game_id>/tags')
def get_game_tags(game_id):
    """Get all tags for a game"""
    tags = Tag.query.filter_by(game_id=game_id).all()
    return jsonify({
        'tags': [tag.to_dict() for tag in tags]
    })


@bp.route('/player/wealth')
def player_wealth():
    """Get current player's total wealth"""
    player = get_current_player()
    if not player:
        return jsonify({'success': False, 'message': 'Not logged in'}), 401

    wealth = stock_market.get_player_total_wealth(player)
    return jsonify(wealth)


@bp.route('/facility/templates')
def facility_templates():
    """Get all facility templates"""
    from app.models import FacilityTemplate
    templates = FacilityTemplate.query.all()
    return jsonify({
        'templates': [template.to_dict() for template in templates]
    })


@bp.route('/facility/build', methods=['POST'])
def build_facility():
    """Start construction of a facility"""
    player = get_current_player()
    if not player:
        return jsonify({'success': False, 'message': 'Not logged in'}), 401

    data = request.get_json()
    company_id = data.get('company_id')
    template_id = data.get('template_id')
    facility_name = data.get('facility_name')

    company = Company.query.get_or_404(company_id)

    if company.owner_id != player.id:
        return jsonify({'success': False, 'message': 'Not your company'}), 403

    from app.models import FacilityTemplate
    template = FacilityTemplate.query.get_or_404(template_id)

    game = company.game
    cfg = config['default']

    from app.game_engine import construction
    result = construction.start_facility_construction(
        company, template, facility_name, game.current_week, cfg
    )

    if result['success']:
        db.session.commit()

    return jsonify(result)


@bp.route('/facility/build/preview', methods=['POST'])
def preview_facility_cost():
    """Preview what it would cost to build a facility"""
    player = get_current_player()
    if not player:
        return jsonify({'success': False, 'message': 'Not logged in'}), 401

    data = request.get_json()
    company_id = data.get('company_id')
    template_id = data.get('template_id')

    company = Company.query.get_or_404(company_id)

    if company.owner_id != player.id:
        return jsonify({'success': False, 'message': 'Not your company'}), 403

    from app.models import FacilityTemplate
    template = FacilityTemplate.query.get_or_404(template_id)

    cfg = config['default']

    from app.game_engine import construction
    breakdown = construction.get_construction_cost_breakdown(company, template, cfg)

    return jsonify(breakdown)


@bp.route('/facility/<int:facility_id>/link_product', methods=['POST'])
def link_product_to_facility(facility_id):
    """Link a product to a sales facility"""
    player = get_current_player()
    if not player:
        return jsonify({'success': False, 'message': 'Not logged in'}), 401

    data = request.get_json()
    product_id = data.get('product_id')

    facility = Facility.query.get_or_404(facility_id)
    company = facility.company

    if company.owner_id != player.id:
        return jsonify({'success': False, 'message': 'Not your company'}), 403

    product = Product.query.get_or_404(product_id)

    if product.company_id != company.id:
        return jsonify({'success': False, 'message': 'Product not owned by this company'}), 403

    # Check if facility can link products
    if facility.template.link_capacity <= 0:
        return jsonify({'success': False, 'message': 'This facility cannot link products'}), 400

    # Check current linked products
    linked_products = facility.get_linked_products()

    if product_id in linked_products:
        return jsonify({'success': False, 'message': 'Product already linked to this facility'}), 400

    if len(linked_products) >= facility.template.link_capacity:
        return jsonify({'success': False, 'message': f'Facility link capacity full ({facility.template.link_capacity})'}), 400

    # Add product to linked list
    linked_products.append(product_id)
    facility.set_linked_products(linked_products)

    db.session.commit()

    return jsonify({
        'success': True,
        'message': f'Product "{product.name}" linked to facility "{facility.name}"',
        'linked_products': linked_products
    })


@bp.route('/facility/<int:facility_id>/unlink_product', methods=['POST'])
def unlink_product_from_facility(facility_id):
    """Unlink a product from a sales facility"""
    player = get_current_player()
    if not player:
        return jsonify({'success': False, 'message': 'Not logged in'}), 401

    data = request.get_json()
    product_id = data.get('product_id')

    facility = Facility.query.get_or_404(facility_id)
    company = facility.company

    if company.owner_id != player.id:
        return jsonify({'success': False, 'message': 'Not your company'}), 403

    # Remove product from linked list
    linked_products = facility.get_linked_products()

    if product_id not in linked_products:
        return jsonify({'success': False, 'message': 'Product not linked to this facility'}), 400

    linked_products.remove(product_id)
    facility.set_linked_products(linked_products)

    db.session.commit()

    return jsonify({
        'success': True,
        'message': 'Product unlinked from facility',
        'linked_products': linked_products
    })


@bp.route('/company/<int:company_id>/construction_timers')
def get_construction_timers(company_id):
    """Get all active construction timers for a company"""
    player = get_current_player()
    if not player:
        return jsonify({'success': False, 'message': 'Not logged in'}), 401

    company = Company.query.get_or_404(company_id)

    if company.owner_id != player.id:
        return jsonify({'success': False, 'message': 'Not your company'}), 403

    timers = company.construction_timers

    return jsonify({
        'timers': [timer.to_dict() for timer in timers]
    })
