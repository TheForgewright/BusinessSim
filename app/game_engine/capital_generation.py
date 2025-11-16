"""
Capital Generation System
Handles weekly facility generation of capital and cash
"""
from app.game_engine.dice import roll_dice
from app import db


def generate_capital_for_facility(facility, company, current_week):
    """
    Generate capital for a single facility

    Returns:
        dict: {
            'generation': {capital_type: amount},
            'costs': {
                'fixed': amount,
                'variable': {capital_type: amount},
                'total': amount
            },
            'success': bool,
            'message': str
        }
    """
    if not facility.is_active:
        return {
            'generation': {},
            'costs': {'fixed': 0, 'variable': {}, 'total': 0},
            'success': False,
            'message': 'Facility is shutdown'
        }

    if facility.condition <= 0:
        return {
            'generation': {},
            'costs': {'fixed': 0, 'variable': {}, 'total': 0},
            'success': False,
            'message': 'Facility is destroyed (0% condition)'
        }

    template = facility.template
    if not template:
        return {
            'generation': {},
            'costs': {'fixed': 0, 'variable': {}, 'total': 0},
            'success': False,
            'message': 'No template found'
        }

    # Get generation data from template
    base_generation = template.get_base_generation()
    focus_bonuses = template.get_focus_bonuses()
    cost_per_capital = template.get_cost_per_capital()

    # Calculate generation with efficiency penalty
    efficiency_multiplier = get_efficiency_multiplier(facility.condition)

    generation = {}
    variable_costs = {}

    for capital_type, dice_expr in base_generation.items():
        # Roll base generation
        base_amount = roll_dice(dice_expr)

        # Add focus bonus if company focus matches
        focus_bonus = 0
        if company.weekly_focus == capital_type:
            focus_bonus = focus_bonuses.get(capital_type, 0)

        # Apply efficiency penalty
        total_amount = int((base_amount + focus_bonus) * efficiency_multiplier)

        if total_amount > 0:
            generation[capital_type] = total_amount

            # Calculate variable cost for this capital type
            cost_per_unit = cost_per_capital.get(capital_type, 0)
            variable_costs[capital_type] = total_amount * cost_per_unit

    # Calculate total costs
    fixed_cost = template.weekly_operating_cost
    total_variable_cost = sum(variable_costs.values())
    total_cost = fixed_cost + total_variable_cost

    # Check if company can afford
    if company.cash < total_cost:
        return {
            'generation': {},
            'costs': {
                'fixed': fixed_cost,
                'variable': variable_costs,
                'total': total_cost
            },
            'success': False,
            'message': f'Insufficient cash (need {total_cost}, have {company.cash})'
        }

    # Deduct costs
    company.cash -= total_cost

    # Add generated capital
    for capital_type, amount in generation.items():
        add_capital_to_company(company, capital_type, amount)

    return {
        'generation': generation,
        'costs': {
            'fixed': fixed_cost,
            'variable': variable_costs,
            'total': total_cost
        },
        'success': True,
        'message': f'Generated successfully'
    }


def get_efficiency_multiplier(condition):
    """
    Get efficiency multiplier based on facility condition

    100-75%: 1.0 (full efficiency)
    74-50%: 0.75 (reduced efficiency)
    49-1%: 0.0 (broken)
    0%: 0.0 (destroyed)
    """
    if condition >= 75:
        return 1.0
    elif condition >= 50:
        return 0.75
    else:
        return 0.0


def add_capital_to_company(company, capital_type, amount):
    """Add capital to company's active inventory"""
    capital_type = capital_type.lower()

    if capital_type == 'cash':
        company.cash += amount
    elif capital_type == 'goods':
        company.goods_active += amount
    elif capital_type == 'ip':
        company.ip_active += amount
    elif capital_type == 'influence':
        company.influence_active += amount
    elif capital_type == 'labor':
        company.labor_active += amount


def deduct_capital_from_company(company, capital_type, amount):
    """Deduct capital from company (tries active first, then backed up)"""
    capital_type = capital_type.lower()

    if capital_type == 'cash':
        if company.cash >= amount:
            company.cash -= amount
            return True
        return False

    elif capital_type == 'goods':
        # Try active first
        if company.goods_active >= amount:
            company.goods_active -= amount
            return True
        # Then try backed up
        elif company.goods_active + company.goods_backed_up >= amount:
            remaining = amount - company.goods_active
            company.goods_active = 0
            company.goods_backed_up -= remaining
            return True
        return False

    elif capital_type == 'ip':
        if company.ip_active >= amount:
            company.ip_active -= amount
            return True
        elif company.ip_active + company.ip_backed_up >= amount:
            remaining = amount - company.ip_active
            company.ip_active = 0
            company.ip_backed_up -= remaining
            return True
        return False

    elif capital_type == 'influence':
        if company.influence_active >= amount:
            company.influence_active -= amount
            return True
        elif company.influence_active + company.influence_backed_up >= amount:
            remaining = amount - company.influence_active
            company.influence_active = 0
            company.influence_backed_up -= remaining
            return True
        return False

    elif capital_type == 'labor':
        if company.labor_active >= amount:
            company.labor_active -= amount
            return True
        elif company.labor_active + company.labor_backed_up >= amount:
            remaining = amount - company.labor_active
            company.labor_active = 0
            company.labor_backed_up -= remaining
            return True
        return False

    return False


def get_company_capital(company, capital_type):
    """Get total capital (active + backed up) for a given type"""
    capital_type = capital_type.lower()

    if capital_type == 'cash':
        return company.cash
    elif capital_type == 'goods':
        return company.goods_active + company.goods_backed_up
    elif capital_type == 'ip':
        return company.ip_active + company.ip_backed_up
    elif capital_type == 'influence':
        return company.influence_active + company.influence_backed_up
    elif capital_type == 'labor':
        return company.labor_active + company.labor_backed_up

    return 0


def calculate_storage_costs(company, config):
    """
    Calculate weekly storage costs for all capital

    Returns:
        float: Total storage cost
    """
    total_cost = 0

    # Goods
    total_cost += company.goods_active * config.STORAGE_COST_ACTIVE_GOODS
    total_cost += company.goods_backed_up * config.STORAGE_COST_BACKED_UP_GOODS

    # IP
    total_cost += company.ip_active * config.STORAGE_COST_ACTIVE_IP
    total_cost += company.ip_backed_up * config.STORAGE_COST_BACKED_UP_IP

    # Influence
    total_cost += company.influence_active * config.STORAGE_COST_ACTIVE_INFLUENCE
    total_cost += company.influence_backed_up * config.STORAGE_COST_BACKED_UP_INFLUENCE

    # Labor
    total_cost += company.labor_active * config.STORAGE_COST_ACTIVE_LABOR
    total_cost += company.labor_backed_up * config.STORAGE_COST_BACKED_UP_LABOR

    return total_cost
