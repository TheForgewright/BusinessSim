"""
Facility Construction System
Handles facility building, construction timers, and cash-for-capital conversion
"""
from app import db
from app.models import ConstructionTimer, Facility
from app.game_engine.capital_generation import deduct_capital_from_company


def start_facility_construction(company, template, facility_name, current_week, config):
    """
    Start construction of a new facility

    Handles:
    - Checking if company has required capital
    - Converting missing capital to cash cost
    - Creating construction timer
    - Deducting costs

    Args:
        company: Company building the facility
        template: FacilityTemplate to build from
        facility_name: Custom name for the facility
        current_week: Current game week
        config: Config object

    Returns:
        dict: {
            'success': bool,
            'timer': ConstructionTimer or None,
            'costs_paid': dict,
            'cash_substituted': dict,
            'total_cash_cost': float,
            'completion_week': int,
            'message': str
        }
    """
    build_cost = template.get_build_cost()

    # Track what we're using/paying
    capital_used = {}
    cash_substituted = {}
    total_cash_cost = build_cost.get('Cash', 0)

    # Cash equivalent rates
    cash_rates = {
        'Goods': config.CASH_EQUIVALENT_GOODS,
        'IP': config.CASH_EQUIVALENT_IP,
        'Influence': config.CASH_EQUIVALENT_INFLUENCE,
        'Labor': config.CASH_EQUIVALENT_LABOR
    }

    # Check each capital requirement
    for capital_type, amount_needed in build_cost.items():
        if capital_type == 'Cash':
            continue

        # Check if company has this capital
        from app.game_engine.capital_generation import get_company_capital
        available = get_company_capital(company, capital_type)

        if available >= amount_needed:
            # Use capital
            capital_used[capital_type] = amount_needed
        else:
            # Use what we have, pay cash for the rest
            capital_used[capital_type] = available
            shortage = amount_needed - available
            cash_equivalent = shortage * cash_rates.get(capital_type, 10.0)
            cash_substituted[capital_type] = {
                'capital_shortage': shortage,
                'cash_cost': cash_equivalent
            }
            total_cash_cost += cash_equivalent

    # Check if company can afford total cash cost
    if company.cash < total_cash_cost:
        return {
            'success': False,
            'timer': None,
            'costs_paid': {},
            'cash_substituted': cash_substituted,
            'total_cash_cost': total_cash_cost,
            'completion_week': 0,
            'message': f'Insufficient cash (need {total_cash_cost:.2f}, have {company.cash:.2f})'
        }

    # Deduct capital costs
    for capital_type, amount in capital_used.items():
        if amount > 0:
            deduct_capital_from_company(company, capital_type, amount)

    # Deduct cash cost
    company.cash -= total_cash_cost

    # Create construction timer
    completion_week = current_week + template.build_time_weeks

    timer = ConstructionTimer(
        company_id=company.id,
        template_id=template.id,
        facility_name=facility_name,
        start_week=current_week,
        completion_week=completion_week
    )
    timer.set_costs_paid({
        'capital_used': capital_used,
        'cash_substituted': cash_substituted,
        'total_cash_cost': total_cash_cost
    })

    db.session.add(timer)

    return {
        'success': True,
        'timer': timer,
        'costs_paid': {
            'capital_used': capital_used,
            'cash_substituted': cash_substituted,
            'total_cash_cost': total_cash_cost
        },
        'cash_substituted': cash_substituted,
        'total_cash_cost': total_cash_cost,
        'completion_week': completion_week,
        'message': f'Construction started! Will complete on week {completion_week}'
    }


def complete_construction_timer(timer, config):
    """
    Complete a construction timer and create the facility

    Returns:
        Facility: The newly created facility
    """
    company = timer.company
    template = timer.template

    # Create facility
    facility = Facility(
        company_id=company.id,
        template_id=template.id,
        name=timer.facility_name,
        is_active=True,
        condition=100.0,
        weeks_until_maintenance=config.MAINTENANCE_FREQUENCY_WEEKS
    )

    db.session.add(facility)
    db.session.delete(timer)

    return facility


def get_construction_cost_breakdown(company, template, config):
    """
    Calculate what it would cost to build this facility
    (for UI preview before committing)

    Returns:
        dict: {
            'capital_available': {type: amount},
            'capital_needed': {type: amount},
            'capital_shortage': {type: amount},
            'cash_substitution': {type: cash_cost},
            'total_cash_cost': float,
            'can_afford': bool
        }
    """
    from app.game_engine.capital_generation import get_company_capital

    build_cost = template.get_build_cost()

    cash_rates = {
        'Goods': config.CASH_EQUIVALENT_GOODS,
        'IP': config.CASH_EQUIVALENT_IP,
        'Influence': config.CASH_EQUIVALENT_INFLUENCE,
        'Labor': config.CASH_EQUIVALENT_LABOR
    }

    capital_available = {}
    capital_needed = {}
    capital_shortage = {}
    cash_substitution = {}
    total_cash_cost = build_cost.get('Cash', 0)

    for capital_type, amount_needed in build_cost.items():
        if capital_type == 'Cash':
            continue

        available = get_company_capital(company, capital_type)
        capital_available[capital_type] = available
        capital_needed[capital_type] = amount_needed

        if available < amount_needed:
            shortage = amount_needed - available
            capital_shortage[capital_type] = shortage
            cash_cost = shortage * cash_rates.get(capital_type, 10.0)
            cash_substitution[capital_type] = cash_cost
            total_cash_cost += cash_cost

    can_afford = company.cash >= total_cash_cost

    return {
        'capital_available': capital_available,
        'capital_needed': capital_needed,
        'capital_shortage': capital_shortage,
        'cash_substitution': cash_substitution,
        'total_cash_cost': total_cash_cost,
        'can_afford': can_afford
    }
