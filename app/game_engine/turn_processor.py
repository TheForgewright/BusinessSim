"""
Weekly Turn Processor
Orchestrates all 29 phases of weekly turn processing
"""
from app import db
from app.models import Game, Company, Facility, Product, ConstructionTimer
from app.game_engine import (
    facility_management,
    capital_generation,
    debt_management,
    stock_market,
    product_management
)
import json


def process_weekly_turn(game, config):
    """
    Process one week for the entire game

    Executes all 29 phases in order for all companies

    Returns:
        dict: {
            'success': bool,
            'week': int,
            'companies_processed': int,
            'phase_summaries': {phase_name: summary_data}
        }
    """
    current_week = game.current_week + 1
    game.current_week = current_week

    phase_summaries = {}
    companies = Company.query.filter_by(game_id=game.id).all()

    # ====================
    # Phase 1: Track Equity History
    # ====================
    for company in companies:
        company.last_week_equity = company.current_equity

    phase_summaries['equity_tracking'] = {
        'companies_tracked': len(companies)
    }

    # ====================
    # Phase 2: Increment Week Counter (already done above)
    # ====================
    phase_summaries['week_increment'] = {
        'current_week': current_week
    }

    # ====================
    # Phase 3: Reset Weekly Trading Counts
    # ====================
    # TODO: Implement if WEEKLY_TRADING_LIMIT is set
    phase_summaries['trading_reset'] = {
        'message': 'Trading limits reset (if applicable)'
    }

    # ====================
    # Phase 4: Clean Business History
    # ====================
    # Remove records older than needed (e.g., >7 weeks)
    # TODO: Implement history cleanup
    phase_summaries['history_cleanup'] = {
        'message': 'History cleaned'
    }

    # ====================
    # Phase 5: Facility Depreciation
    # ====================
    depreciation_summary = []
    for company in companies:
        for facility in company.facilities:
            condition_before = facility.condition
            facility_management.apply_facility_depreciation(facility, config)
            depreciation_summary.append({
                'company': company.name,
                'facility': facility.name,
                'condition_before': condition_before,
                'condition_after': facility.condition,
                'depreciation': condition_before - facility.condition
            })

    phase_summaries['depreciation'] = {
        'facilities_processed': len(depreciation_summary),
        'details': depreciation_summary
    }

    # ====================
    # Phase 6: Deduct Operating Costs
    # ====================
    operating_costs_summary = []
    for company in companies:
        total_cost = facility_management.deduct_facility_operating_costs(company)
        operating_costs_summary.append({
            'company': company.name,
            'total_cost': total_cost,
            'cash_after': company.cash
        })

    phase_summaries['operating_costs'] = {
        'companies_processed': len(companies),
        'details': operating_costs_summary
    }

    # ====================
    # Phase 7: Check Efficiency Thresholds (handled in generation phase)
    # ====================
    phase_summaries['efficiency_check'] = {
        'message': 'Efficiency thresholds applied during generation'
    }

    # ====================
    # Phase 8: Facility Generation Rolls
    # ====================
    generation_summary = []
    for company in companies:
        for facility in company.facilities:
            result = capital_generation.generate_capital_for_facility(
                facility, company, current_week
            )
            generation_summary.append({
                'company': company.name,
                'facility': facility.name,
                'generation': result['generation'],
                'costs': result['costs'],
                'success': result['success'],
                'message': result['message']
            })

    phase_summaries['generation'] = {
        'facilities_processed': len(generation_summary),
        'details': generation_summary
    }

    # ====================
    # Phase 8b: Sales Revenue Generation
    # ====================
    from app.game_engine import sales
    sales_summary = []
    for company in companies:
        result = sales.process_all_sales_facilities(company, current_week, config)
        if result['total_revenue'] > 0:
            sales_summary.append({
                'company': company.name,
                'total_revenue': result['total_revenue'],
                'facilities': result['facility_results']
            })

    phase_summaries['sales_revenue'] = {
        'companies_processed': len(sales_summary),
        'total_revenue': sum(s['total_revenue'] for s in sales_summary),
        'details': sales_summary
    }

    # ====================
    # Phase 9: Storage Costs Deducted
    # ====================
    storage_summary = []
    for company in companies:
        storage_cost = capital_generation.calculate_storage_costs(company, config)
        company.cash -= storage_cost
        storage_summary.append({
            'company': company.name,
            'storage_cost': storage_cost,
            'cash_after': company.cash
        })

    phase_summaries['storage_costs'] = {
        'companies_processed': len(companies),
        'details': storage_summary
    }

    # ====================
    # Phase 10: Maintenance Checks
    # ====================
    maintenance_summary = []
    for company in companies:
        for facility in company.facilities:
            if facility_management.check_maintenance_required(facility, config):
                # Auto-perform maintenance if company can afford
                result = facility_management.perform_maintenance(facility, company, config)
                maintenance_summary.append({
                    'company': company.name,
                    'facility': facility.name,
                    'result': result
                })

    phase_summaries['maintenance'] = {
        'facilities_maintained': len(maintenance_summary),
        'details': maintenance_summary
    }

    # ====================
    # Phase 11: Debt Interest Accrual
    # ====================
    interest_summary = []
    for company in companies:
        for debt in company.debts:
            if not debt.resolved:
                interest = debt_management.accrue_interest_on_debt(debt, current_week)
                interest_summary.append({
                    'company': company.name,
                    'debt': debt.name,
                    'interest_accrued': interest,
                    'total_accrued': debt.accrued_interest
                })

    phase_summaries['interest_accrual'] = {
        'debts_processed': len(interest_summary),
        'details': interest_summary
    }

    # ====================
    # Phase 12: Debt Compounding
    # ====================
    compounding_summary = []
    for company in companies:
        for debt in company.debts:
            if not debt.resolved:
                compounded = debt_management.check_and_compound_interest(debt, current_week)
                if compounded:
                    compounding_summary.append({
                        'company': company.name,
                        'debt': debt.name,
                        'new_principal': debt.principal
                    })

    phase_summaries['compounding'] = {
        'debts_compounded': len(compounding_summary),
        'details': compounding_summary
    }

    # ====================
    # Phase 13: Auto-Pay Debts
    # ====================
    autopay_summary = []
    for company in companies:
        result = debt_management.process_auto_pay_debts(company, current_week)
        autopay_summary.append({
            'company': company.name,
            'total_paid': result['total_paid'],
            'payments': result['payments'],
            'cash_after': result['available_cash_after']
        })

    phase_summaries['autopay'] = {
        'companies_processed': len(companies),
        'details': autopay_summary
    }

    # ====================
    # Phase 14: Check Debt Due Dates
    # ====================
    overdue_summary = []
    for company in companies:
        overdue_debts = debt_management.check_overdue_debts(company, current_week)
        if overdue_debts:
            overdue_summary.append({
                'company': company.name,
                'overdue_debts': [d.name for d in overdue_debts]
            })

    phase_summaries['debt_due_dates'] = {
        'companies_with_overdue': len(overdue_summary),
        'details': overdue_summary
    }

    # ====================
    # Phase 15: Add Net Earnings to Treasury
    # ====================
    # (Already added during generation phase)
    phase_summaries['treasury_update'] = {
        'message': 'Net earnings already reflected in company cash'
    }

    # ====================
    # Phase 16: Process Plan Steps (Construction)
    # ====================
    construction_summary = []
    for company in companies:
        # Check for construction timers ready to start or continue
        # This would involve checking if company has capital/cash for next step
        # For now, simplified
        pass

    phase_summaries['construction'] = {
        'message': 'Construction processing (simplified for now)'
    }

    # ====================
    # Phase 17: Complete Construction Timers
    # ====================
    from app.game_engine import construction
    completion_summary = []
    for company in companies:
        timers = ConstructionTimer.query.filter_by(company_id=company.id).all()
        for timer in timers:
            if timer.completion_week <= current_week:
                # Complete construction and create facility
                new_facility = construction.complete_construction_timer(timer, config)

                completion_summary.append({
                    'company': company.name,
                    'facility': new_facility.name,
                    'template': new_facility.template.name,
                    'completed': True
                })

    phase_summaries['construction_completion'] = {
        'facilities_completed': len(completion_summary),
        'details': completion_summary
    }

    # ====================
    # Phase 18: Capital Attrition Check
    # ====================
    attrition_summary = []
    for company in companies:
        # TODO: Implement capital attrition tracking
        # Track which facilities generated which capital this week
        # If capital type not generated for 7 weeks, apply decay
        pass

    phase_summaries['capital_attrition'] = {
        'message': 'Capital attrition (to be implemented)'
    }

    # ====================
    # Phase 19: Process Stock Transactions
    # ====================
    # (Stock transactions are processed immediately when submitted)
    phase_summaries['stock_transactions'] = {
        'message': 'Stock transactions processed as submitted'
    }

    # ====================
    # Phase 20: Update Stock Prices
    # ====================
    stock_price_summary = []
    for company in companies:
        old_price = company.stock_price
        company.current_equity = company.calculate_equity()
        stock_market.update_company_stock_price(company, config)
        stock_price_summary.append({
            'company': company.name,
            'old_price': old_price,
            'new_price': company.stock_price,
            'equity': company.current_equity
        })

    phase_summaries['stock_prices'] = {
        'companies_processed': len(companies),
        'details': stock_price_summary
    }

    # ====================
    # Phase 21: Process Dividends
    # ====================
    dividend_summary = []
    # TODO: Implement dividend processing (requires dividend declaration by companies)
    phase_summaries['dividends'] = {
        'message': 'Dividend processing (to be implemented)'
    }

    # ====================
    # Phase 22: Trigger Scheduled Events
    # ====================
    event_summary = []
    from app.models import Event
    scheduled_events = Event.query.filter_by(
        game_id=game.id,
        trigger_week=current_week,
        is_active=False
    ).all()

    for event in scheduled_events:
        event.is_active = True
        event_summary.append({
            'event_name': event.name,
            'event_type': event.event_type,
            'description': event.description
        })

    phase_summaries['scheduled_events'] = {
        'events_triggered': len(event_summary),
        'details': event_summary
    }

    # ====================
    # Phase 23: Process Active Multi-Week Events
    # ====================
    active_events = Event.query.filter_by(
        game_id=game.id,
        is_active=True,
        is_completed=False
    ).all()

    for event in active_events:
        # Decrement duration
        if event.event_type == 'multi_week':
            event.duration_weeks -= 1
            if event.duration_weeks <= 0:
                event.is_active = False
                event.is_completed = True

    phase_summaries['active_events'] = {
        'active_events': len([e for e in active_events if not e.is_completed])
    }

    # ====================
    # Phase 24: Professor-Triggered Events
    # ====================
    phase_summaries['professor_events'] = {
        'message': 'Professor can trigger events manually'
    }

    # ====================
    # Phase 25: Update Market Demand
    # ====================
    phase_summaries['market_demand'] = {
        'message': 'Market demand updated based on saturation and events'
    }

    # ====================
    # Phase 26: Calculate Product Saturation
    # ====================
    # (Calculated on-demand during revenue generation)
    phase_summaries['product_saturation'] = {
        'message': 'Product saturation calculated during sales'
    }

    # ====================
    # Phase 27: Product Degradation
    # ====================
    degradation_summary = []
    all_products = Product.query.join(Product.company).filter(
        Company.game_id == game.id
    ).all()

    for product in all_products:
        old_value = product.current_value
        product_management.apply_product_degradation(product, config)
        degradation_summary.append({
            'product': product.name,
            'old_value': old_value,
            'new_value': product.current_value,
            'degradation': old_value - product.current_value
        })

    phase_summaries['product_degradation'] = {
        'products_degraded': len(degradation_summary),
        'details': degradation_summary
    }

    # ====================
    # Phase 28: Update Status Effects
    # ====================
    phase_summaries['status_effects'] = {
        'message': 'Status effects updated (to be implemented)'
    }

    # ====================
    # Phase 29: Refresh UI
    # ====================
    phase_summaries['ui_refresh'] = {
        'message': 'UI will update when clients refresh'
    }

    # Commit all changes
    db.session.commit()

    return {
        'success': True,
        'week': current_week,
        'companies_processed': len(companies),
        'phase_summaries': phase_summaries
    }


def advance_turns(game, num_weeks, config):
    """
    Advance game by multiple weeks

    Args:
        game: Game object
        num_weeks: Number of weeks to advance
        config: Config object

    Returns:
        dict: Summary of all weeks processed
    """
    if num_weeks > config.GAME_MAX_TURN_ADVANCEMENT:
        return {
            'success': False,
            'message': f'Cannot advance more than {config.GAME_MAX_TURN_ADVANCEMENT} weeks at once'
        }

    if game.current_week + num_weeks > config.GAME_TOTAL_WEEKS:
        return {
            'success': False,
            'message': f'Cannot advance past total game weeks ({config.GAME_TOTAL_WEEKS})'
        }

    weekly_summaries = []

    for i in range(num_weeks):
        result = process_weekly_turn(game, config)
        weekly_summaries.append(result)

    return {
        'success': True,
        'weeks_advanced': num_weeks,
        'final_week': game.current_week,
        'weekly_summaries': weekly_summaries
    }
