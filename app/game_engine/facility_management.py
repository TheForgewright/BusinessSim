"""
Facility Management System
Handles depreciation, maintenance, and facility state management
"""
from app import db


def apply_facility_depreciation(facility, config):
    """
    Apply weekly depreciation to facility

    Depreciation rules:
    - Active facilities: Base rate (e.g., 2%/week)
    - Shutdown personnel facilities: 4× rate
    - Shutdown physical facilities: 1× rate (same as active)
    """
    if facility.condition <= 0:
        return  # Already destroyed

    template = facility.template
    base_rate = config.BASE_DEPRECIATION_RATE

    if facility.is_active:
        # Active: normal depreciation
        depreciation_rate = base_rate
    else:
        # Shutdown: depends on facility type
        if template.facility_type == 'personnel':
            depreciation_rate = base_rate * config.PERSONNEL_SHUTDOWN_MULTIPLIER
        else:  # 'physical'
            depreciation_rate = base_rate * config.PHYSICAL_SHUTDOWN_MULTIPLIER

    # Apply depreciation
    facility.condition = max(0, facility.condition - depreciation_rate)

    # Decrement maintenance counter
    if facility.weeks_until_maintenance > 0:
        facility.weeks_until_maintenance -= 1


def check_maintenance_required(facility, config):
    """
    Check if facility requires maintenance

    Returns:
        bool: True if maintenance is due
    """
    return facility.weeks_until_maintenance <= 0


def perform_maintenance(facility, company, config):
    """
    Perform maintenance on facility

    Returns:
        dict: {
            'success': bool,
            'cost': float,
            'condition_restored': float,
            'message': str
        }
    """
    template = facility.template
    build_cost = template.get_build_cost()

    # Calculate maintenance cost (percentage of build cost)
    total_build_cost = sum(build_cost.values())
    maintenance_cost = total_build_cost * (config.MAINTENANCE_COST_PERCENT / 100.0)

    if company.cash < maintenance_cost:
        return {
            'success': False,
            'cost': maintenance_cost,
            'condition_restored': 0,
            'message': f'Insufficient cash (need {maintenance_cost}, have {company.cash})'
        }

    # Deduct cost
    company.cash -= maintenance_cost

    # Restore condition (not to 100%, but significant improvement)
    condition_before = facility.condition
    facility.condition = min(100.0, facility.condition + 25.0)  # +25% condition
    condition_restored = facility.condition - condition_before

    # Reset maintenance timer
    facility.weeks_until_maintenance = config.MAINTENANCE_FREQUENCY_WEEKS

    # Facility is offline during maintenance week (handled in generation phase)

    return {
        'success': True,
        'cost': maintenance_cost,
        'condition_restored': condition_restored,
        'message': f'Maintenance completed, restored {condition_restored:.1f}% condition'
    }


def shutdown_facility(facility):
    """Shutdown facility (stop generation, reduce costs, accelerated depreciation)"""
    facility.is_active = False


def activate_facility(facility):
    """Activate facility (resume generation)"""
    if facility.condition > 0:
        facility.is_active = True
        return True
    return False  # Can't activate destroyed facility


def destroy_facility(facility):
    """Mark facility as destroyed (condition = 0)"""
    facility.condition = 0
    facility.is_active = False


def calculate_facility_operating_cost(facility):
    """
    Calculate weekly operating cost for facility

    Returns:
        float: Weekly operating cost
    """
    template = facility.template

    if facility.is_active:
        # Active: full operating cost
        return template.weekly_operating_cost
    else:
        # Shutdown: reduced costs
        if template.facility_type == 'personnel':
            # Personnel: 0 cost when shutdown (no payroll)
            return 0.0
        else:  # 'physical'
            # Physical: half cost (property tax, minimal maintenance)
            return template.weekly_operating_cost * 0.5


def deduct_facility_operating_costs(company):
    """
    Deduct all facility operating costs from company

    Returns:
        float: Total operating costs deducted
    """
    total_cost = 0

    for facility in company.facilities:
        cost = calculate_facility_operating_cost(facility)
        total_cost += cost

    # Deduct from company cash
    company.cash -= total_cost

    return total_cost
