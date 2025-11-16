"""
Analytics System - Historical Data Tracking and Metrics
Tracks company performance metrics over time for charting
"""
from app.models import CompanyHistory
from app import db


def record_weekly_metrics(company, current_week, config, weekly_data=None):
    """
    Record historical metrics for a company at the end of a week

    Args:
        company: Company model instance
        current_week: Current game week number
        config: Config object
        weekly_data: Optional dict with pre-calculated metrics:
            - depreciation_amount: Total depreciation this week
            - sales_revenue: Revenue from sales this week
            - goods_sold: Amount of goods sold
            - influence_spent: Influence spent on sales
            - sales_facilities: List of facility IDs used for sales

    Returns:
        CompanyHistory instance
    """
    if weekly_data is None:
        weekly_data = {}

    # Calculate equity and debt
    equity = company.calculate_equity()
    total_debt = company.get_total_debt()

    # Get depreciation amount
    depreciation = weekly_data.get('depreciation_amount', 0.0)

    # Get sales revenue
    sales_revenue = weekly_data.get('sales_revenue', 0.0)

    # Calculate sales profit with all costs
    sales_profit = calculate_sales_profit(
        company=company,
        sales_revenue=sales_revenue,
        goods_sold=weekly_data.get('goods_sold', 0.0),
        influence_spent=weekly_data.get('influence_spent', 0.0),
        sales_facilities=weekly_data.get('sales_facilities', []),
        config=config
    )

    # Calculate cost components
    goods_cost = weekly_data.get('goods_sold', 0.0) * config.CASH_EQUIVALENT_GOODS
    influence_cost = weekly_data.get('influence_spent', 0.0) * config.CASH_EQUIVALENT_INFLUENCE
    facility_cost = calculate_facility_cost(
        company=company,
        sales_facilities=weekly_data.get('sales_facilities', []),
        config=config
    )

    # Create history record
    history = CompanyHistory(
        company_id=company.id,
        week=current_week,
        equity=equity,
        cash=company.cash,
        total_debt=total_debt,
        weekly_depreciation=depreciation,
        sales_revenue=sales_revenue,
        sales_profit=sales_profit,
        goods_cost=goods_cost,
        influence_cost=influence_cost,
        facility_cost=facility_cost
    )

    db.session.add(history)
    db.session.commit()

    return history


def calculate_sales_profit(company, sales_revenue, goods_sold, influence_spent, sales_facilities, config):
    """
    Calculate net profit from sales after all costs

    Costs include:
    - Cost of goods sold (goods_sold × CASH_EQUIVALENT_GOODS)
    - Cost of influence spent (influence_spent × CASH_EQUIVALENT_INFLUENCE)
    - Allocated cost of sales facilities (operating cost × multiplier)

    Args:
        company: Company model
        sales_revenue: Total revenue from sales
        goods_sold: Amount of goods sold
        influence_spent: Influence spent on boosting sales
        sales_facilities: List of facility IDs used for sales
        config: Config object

    Returns:
        float: Net profit from sales
    """
    # Cost of goods sold
    goods_cost = goods_sold * config.CASH_EQUIVALENT_GOODS

    # Cost of influence spent
    influence_cost = influence_spent * config.CASH_EQUIVALENT_INFLUENCE

    # Allocated cost of sales facilities
    facility_cost = calculate_facility_cost(company, sales_facilities, config)

    # Net profit
    profit = sales_revenue - goods_cost - influence_cost - facility_cost

    return profit


def calculate_facility_cost(company, sales_facilities, config):
    """
    Calculate allocated cost of facilities used for sales

    Uses the sales_profit_facility_multiplier (default 80%) to account for
    facilities having other benefits beyond just sales

    Args:
        company: Company model
        sales_facilities: List of facility IDs used for sales
        config: Config object

    Returns:
        float: Allocated facility cost
    """
    if not sales_facilities:
        return 0.0

    from app.models import Facility

    # Get multiplier from game settings
    multiplier = company.game.sales_profit_facility_multiplier

    total_cost = 0.0
    for facility_id in sales_facilities:
        facility = Facility.query.get(facility_id)
        if facility and facility.company_id == company.id:
            # Use weekly operating cost
            total_cost += facility.template.weekly_operating_cost

    # Apply multiplier (default 80%)
    return total_cost * multiplier


def get_company_analytics(company_id, start_week=None, end_week=None):
    """
    Get historical analytics data for a company

    Args:
        company_id: Company ID
        start_week: Optional starting week (inclusive)
        end_week: Optional ending week (inclusive)

    Returns:
        dict: {
            'weeks': [week numbers],
            'equity': [values],
            'cash': [values],
            'debt': [values],
            'depreciation': [values],
            'sales_revenue': [values],
            'sales_profit': [values]
        }
    """
    query = CompanyHistory.query.filter_by(company_id=company_id)

    if start_week is not None:
        query = query.filter(CompanyHistory.week >= start_week)
    if end_week is not None:
        query = query.filter(CompanyHistory.week <= end_week)

    history = query.order_by(CompanyHistory.week).all()

    return {
        'weeks': [h.week for h in history],
        'equity': [h.equity for h in history],
        'cash': [h.cash for h in history],
        'debt': [h.total_debt for h in history],
        'depreciation': [h.weekly_depreciation for h in history],
        'sales_revenue': [h.sales_revenue for h in history],
        'sales_profit': [h.sales_profit for h in history]
    }


def get_all_companies_analytics(game_id, start_week=None, end_week=None):
    """
    Get analytics for all companies in a game

    Returns:
        dict: {company_id: analytics_data}
    """
    from app.models import Company

    companies = Company.query.filter_by(game_id=game_id).all()

    analytics = {}
    for company in companies:
        analytics[company.id] = {
            'company_name': company.name,
            'data': get_company_analytics(company.id, start_week, end_week)
        }

    return analytics
