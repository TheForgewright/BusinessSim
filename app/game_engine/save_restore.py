"""
Game Save/Restore System
Handles saving and loading complete game state
"""
import json
import os
from datetime import datetime
from app import db
from app.models import (
    Game, Company, Player, Facility, Debt, Product, Tag,
    StockOwnership, StockTransaction, Event, ConstructionTimer,
    FacilityTemplate
)


def serialize_game_state(game_id):
    """
    Serialize complete game state to dictionary

    Returns:
        dict: Complete game state ready for JSON serialization
    """
    game = Game.query.get(game_id)
    if not game:
        return None

    # Get all related data
    companies = Company.query.filter_by(game_id=game_id).all()
    tags = Tag.query.filter_by(game_id=game_id).all()
    events = Event.query.filter_by(game_id=game_id).all()

    # Build complete state
    state = {
        'metadata': {
            'saved_at': datetime.utcnow().isoformat(),
            'game_id': game_id,
            'game_name': game.name,
            'current_week': game.current_week,
            'version': '1.0'
        },
        'game': {
            'id': game.id,
            'name': game.name,
            'current_week': game.current_week,
            'total_weeks': game.total_weeks,
            'max_turn_advancement': game.max_turn_advancement,
            'is_active': game.is_active,
            'created_at': game.created_at.isoformat() if game.created_at else None
        },
        'companies': [],
        'tags': [],
        'events': []
    }

    # Serialize tags
    for tag in tags:
        state['tags'].append({
            'id': tag.id,
            'name': tag.name,
            'demand_multiplier': tag.demand_multiplier,
            'profit_margin': tag.profit_margin,
            'description': tag.description
        })

    # Serialize events
    for event in events:
        state['events'].append({
            'id': event.id,
            'name': event.name,
            'description': event.description,
            'event_type': event.event_type,
            'severity': event.severity,
            'trigger_week': event.trigger_week,
            'duration_weeks': event.duration_weeks,
            'warning_weeks': event.warning_weeks,
            'effects': event.get_effects(),
            'target_company_id': event.target_company_id,
            'is_active': event.is_active,
            'is_completed': event.is_completed
        })

    # Serialize companies and all related data
    for company in companies:
        company_data = {
            'id': company.id,
            'owner_id': company.owner_id,
            'name': company.name,
            'cash': company.cash,
            'goods_active': company.goods_active,
            'goods_backed_up': company.goods_backed_up,
            'ip_active': company.ip_active,
            'ip_backed_up': company.ip_backed_up,
            'influence_active': company.influence_active,
            'influence_backed_up': company.influence_backed_up,
            'labor_active': company.labor_active,
            'labor_backed_up': company.labor_backed_up,
            'weekly_focus': company.weekly_focus,
            'total_shares': company.total_shares,
            'stock_price': company.stock_price,
            'cash_reserve': company.cash_reserve,
            'current_equity': company.current_equity,
            'last_week_equity': company.last_week_equity,
            'attrition_counters': company.attrition_counters,
            'facilities': [],
            'debts': [],
            'products': [],
            'stock_ownership': [],
            'construction_timers': []
        }

        # Serialize facilities
        for facility in company.facilities:
            company_data['facilities'].append({
                'id': facility.id,
                'template_id': facility.template_id,
                'name': facility.name,
                'is_active': facility.is_active,
                'condition': facility.condition,
                'weeks_until_maintenance': facility.weeks_until_maintenance,
                'linked_products': facility.get_linked_products()
            })

        # Serialize debts
        for debt in company.debts:
            company_data['debts'].append({
                'id': debt.id,
                'name': debt.name,
                'creditor': debt.creditor,
                'principal': debt.principal,
                'accrued_interest': debt.accrued_interest,
                'interest_rate': debt.interest_rate,
                'compounding_type': debt.compounding_type,
                'last_interest_week': debt.last_interest_week,
                'collateral': debt.collateral,
                'due_date': debt.due_date,
                'term_weeks': debt.term_weeks,
                'agreed_payment_amount': debt.agreed_payment_amount,
                'auto_pay': debt.auto_pay,
                'missed_payments': debt.missed_payments,
                'resolved': debt.resolved,
                'week_created': debt.week_created
            })

        # Serialize products
        for product in company.products:
            company_data['products'].append({
                'id': product.id,
                'name': product.name,
                'ip_invested': product.ip_invested,
                'goods_invested': product.goods_invested,
                'base_value': product.base_value,
                'current_value': product.current_value,
                'tags': product.get_tags(),
                'week_created': product.week_created
            })

        # Serialize stock ownership
        stock_owners = StockOwnership.query.filter_by(company_id=company.id).all()
        for owner in stock_owners:
            company_data['stock_ownership'].append({
                'id': owner.id,
                'player_id': owner.player_id,
                'investor_name': owner.investor_name,
                'shares_owned': owner.shares_owned,
                'is_npc': owner.is_npc,
                'freeze_trading': owner.freeze_trading
            })

        # Serialize construction timers
        for timer in company.construction_timers:
            company_data['construction_timers'].append({
                'id': timer.id,
                'template_id': timer.template_id,
                'facility_name': timer.facility_name,
                'start_week': timer.start_week,
                'completion_week': timer.completion_week,
                'costs_paid': timer.get_costs_paid()
            })

        state['companies'].append(company_data)

    return state


def save_game(game_id, save_name=None, auto=False):
    """
    Save game state to file

    Args:
        game_id: Game ID to save
        save_name: Custom save name (for manual saves)
        auto: If True, this is an autosave

    Returns:
        dict: {
            'success': bool,
            'filepath': str,
            'filename': str,
            'message': str
        }
    """
    # Create saves directory if it doesn't exist
    saves_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data', 'saves')
    os.makedirs(saves_dir, exist_ok=True)

    # Serialize game state
    state = serialize_game_state(game_id)
    if not state:
        return {
            'success': False,
            'filepath': None,
            'filename': None,
            'message': 'Game not found'
        }

    # Generate filename
    timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
    week = state['game']['current_week']

    if auto:
        filename = f"game_{game_id}_week_{week}_auto_{timestamp}.json"
    elif save_name:
        safe_name = "".join(c for c in save_name if c.isalnum() or c in (' ', '-', '_')).strip()
        filename = f"game_{game_id}_week_{week}_manual_{safe_name}_{timestamp}.json"
    else:
        filename = f"game_{game_id}_week_{week}_manual_{timestamp}.json"

    filepath = os.path.join(saves_dir, filename)

    # Write to file
    try:
        with open(filepath, 'w') as f:
            json.dump(state, f, indent=2)

        return {
            'success': True,
            'filepath': filepath,
            'filename': filename,
            'message': f'Game saved to {filename}'
        }
    except Exception as e:
        return {
            'success': False,
            'filepath': None,
            'filename': None,
            'message': f'Error saving game: {str(e)}'
        }


def restore_game(filepath):
    """
    Restore game state from file

    Args:
        filepath: Path to save file

    Returns:
        dict: {
            'success': bool,
            'game_id': int,
            'message': str,
            'warnings': [str]
        }
    """
    warnings = []

    # Load save file
    try:
        with open(filepath, 'r') as f:
            state = json.load(f)
    except Exception as e:
        return {
            'success': False,
            'game_id': None,
            'message': f'Error reading save file: {str(e)}',
            'warnings': []
        }

    game_id = state['metadata']['game_id']

    # Check if game exists
    existing_game = Game.query.get(game_id)
    if existing_game:
        # Clear existing game data
        warnings.append(f'Overwriting existing game "{existing_game.name}" (ID: {game_id})')

        # Delete all related data
        Company.query.filter_by(game_id=game_id).delete()
        Tag.query.filter_by(game_id=game_id).delete()
        Event.query.filter_by(game_id=game_id).delete()
        db.session.delete(existing_game)
        db.session.commit()

    # Restore game
    game_data = state['game']
    game = Game(
        id=game_data['id'],
        name=game_data['name'],
        current_week=game_data['current_week'],
        total_weeks=game_data['total_weeks'],
        max_turn_advancement=game_data['max_turn_advancement'],
        is_active=game_data['is_active']
    )
    db.session.add(game)
    db.session.flush()

    # Restore tags
    for tag_data in state['tags']:
        tag = Tag(
            id=tag_data['id'],
            game_id=game_id,
            name=tag_data['name'],
            demand_multiplier=tag_data['demand_multiplier'],
            profit_margin=tag_data['profit_margin'],
            description=tag_data['description']
        )
        db.session.add(tag)

    # Restore events
    for event_data in state['events']:
        event = Event(
            id=event_data['id'],
            game_id=game_id,
            name=event_data['name'],
            description=event_data['description'],
            event_type=event_data['event_type'],
            severity=event_data['severity'],
            trigger_week=event_data['trigger_week'],
            duration_weeks=event_data['duration_weeks'],
            warning_weeks=event_data['warning_weeks'],
            target_company_id=event_data['target_company_id'],
            is_active=event_data['is_active'],
            is_completed=event_data['is_completed']
        )
        event.set_effects(event_data['effects'])
        db.session.add(event)

    # Restore companies and all related data
    for company_data in state['companies']:
        # Check if owner player exists
        owner = Player.query.get(company_data['owner_id'])
        if not owner:
            warnings.append(f"Player ID {company_data['owner_id']} not found for company '{company_data['name']}'. Skipping company.")
            continue

        company = Company(
            id=company_data['id'],
            game_id=game_id,
            owner_id=company_data['owner_id'],
            name=company_data['name'],
            cash=company_data['cash'],
            goods_active=company_data['goods_active'],
            goods_backed_up=company_data['goods_backed_up'],
            ip_active=company_data['ip_active'],
            ip_backed_up=company_data['ip_backed_up'],
            influence_active=company_data['influence_active'],
            influence_backed_up=company_data['influence_backed_up'],
            labor_active=company_data['labor_active'],
            labor_backed_up=company_data['labor_backed_up'],
            weekly_focus=company_data['weekly_focus'],
            total_shares=company_data['total_shares'],
            stock_price=company_data['stock_price'],
            cash_reserve=company_data['cash_reserve'],
            current_equity=company_data['current_equity'],
            last_week_equity=company_data['last_week_equity'],
            attrition_counters=company_data['attrition_counters']
        )
        db.session.add(company)
        db.session.flush()

        # Restore facilities
        for facility_data in company_data['facilities']:
            facility = Facility(
                id=facility_data['id'],
                company_id=company.id,
                template_id=facility_data['template_id'],
                name=facility_data['name'],
                is_active=facility_data['is_active'],
                condition=facility_data['condition'],
                weeks_until_maintenance=facility_data['weeks_until_maintenance']
            )
            facility.set_linked_products(facility_data['linked_products'])
            db.session.add(facility)

        # Restore debts
        for debt_data in company_data['debts']:
            debt = Debt(
                id=debt_data['id'],
                company_id=company.id,
                name=debt_data['name'],
                creditor=debt_data['creditor'],
                principal=debt_data['principal'],
                accrued_interest=debt_data['accrued_interest'],
                interest_rate=debt_data['interest_rate'],
                compounding_type=debt_data['compounding_type'],
                last_interest_week=debt_data['last_interest_week'],
                collateral=debt_data['collateral'],
                due_date=debt_data['due_date'],
                term_weeks=debt_data['term_weeks'],
                agreed_payment_amount=debt_data['agreed_payment_amount'],
                auto_pay=debt_data['auto_pay'],
                missed_payments=debt_data['missed_payments'],
                resolved=debt_data['resolved'],
                week_created=debt_data['week_created']
            )
            db.session.add(debt)

        # Restore products
        for product_data in company_data['products']:
            product = Product(
                id=product_data['id'],
                company_id=company.id,
                name=product_data['name'],
                ip_invested=product_data['ip_invested'],
                goods_invested=product_data['goods_invested'],
                base_value=product_data['base_value'],
                current_value=product_data['current_value'],
                week_created=product_data['week_created']
            )
            product.set_tags(product_data['tags'])
            db.session.add(product)

        # Restore stock ownership
        for owner_data in company_data['stock_ownership']:
            owner = StockOwnership(
                id=owner_data['id'],
                company_id=company.id,
                player_id=owner_data['player_id'],
                investor_name=owner_data['investor_name'],
                shares_owned=owner_data['shares_owned'],
                is_npc=owner_data['is_npc'],
                freeze_trading=owner_data['freeze_trading']
            )
            db.session.add(owner)

        # Restore construction timers
        for timer_data in company_data['construction_timers']:
            timer = ConstructionTimer(
                id=timer_data['id'],
                company_id=company.id,
                template_id=timer_data['template_id'],
                facility_name=timer_data['facility_name'],
                start_week=timer_data['start_week'],
                completion_week=timer_data['completion_week']
            )
            timer.set_costs_paid(timer_data['costs_paid'])
            db.session.add(timer)

    # Commit all changes
    try:
        db.session.commit()
        return {
            'success': True,
            'game_id': game_id,
            'message': f'Game restored successfully to week {game.current_week}',
            'warnings': warnings
        }
    except Exception as e:
        db.session.rollback()
        return {
            'success': False,
            'game_id': None,
            'message': f'Error restoring game: {str(e)}',
            'warnings': warnings
        }


def list_saves(game_id=None):
    """
    List all available save files

    Args:
        game_id: If provided, only list saves for this game

    Returns:
        list: [{filename, filepath, metadata}]
    """
    saves_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data', 'saves')

    if not os.path.exists(saves_dir):
        return []

    saves = []

    for filename in os.listdir(saves_dir):
        if not filename.endswith('.json'):
            continue

        # Filter by game_id if provided
        if game_id and not filename.startswith(f'game_{game_id}_'):
            continue

        filepath = os.path.join(saves_dir, filename)

        # Load metadata
        try:
            with open(filepath, 'r') as f:
                state = json.load(f)
                metadata = state.get('metadata', {})
        except:
            metadata = {}

        # Parse filename for info
        is_auto = '_auto_' in filename
        save_type = 'Auto' if is_auto else 'Manual'

        saves.append({
            'filename': filename,
            'filepath': filepath,
            'save_type': save_type,
            'metadata': metadata,
            'file_size': os.path.getsize(filepath),
            'modified_time': datetime.fromtimestamp(os.path.getmtime(filepath)).isoformat()
        })

    # Sort by modified time (newest first)
    saves.sort(key=lambda x: x['modified_time'], reverse=True)

    return saves


def delete_save(filepath):
    """
    Delete a save file

    Returns:
        dict: {'success': bool, 'message': str}
    """
    try:
        if os.path.exists(filepath):
            os.remove(filepath)
            return {
                'success': True,
                'message': 'Save file deleted'
            }
        else:
            return {
                'success': False,
                'message': 'Save file not found'
            }
    except Exception as e:
        return {
            'success': False,
            'message': f'Error deleting save: {str(e)}'
        }
