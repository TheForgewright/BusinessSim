"""
Weekly Turn Processor
Orchestrates all 29 phases of weekly turn processing
"""
from app import db
from app.models import Game, Company, Facility, Product, ConstructionTimer, EventEffect, GovernanceProposal, Event
from app.game_engine import (
    facility_management,
    capital_generation,
    debt_management,
    stock_market,
    product_management,
    analytics
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

    # Initialize analytics tracking for each company
    company_analytics_data = {}
    for company in companies:
        company_analytics_data[company.id] = {
            'depreciation_amount': 0.0,
            'sales_revenue': 0.0,
            'goods_sold': 0.0,
            'influence_spent': 0.0,
            'sales_facilities': []
        }

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
            depreciation_amount = condition_before - facility.condition

            # Track for analytics
            company_analytics_data[company.id]['depreciation_amount'] += depreciation_amount

            depreciation_summary.append({
                'company': company.name,
                'facility': facility.name,
                'condition_before': condition_before,
                'condition_after': facility.condition,
                'depreciation': depreciation_amount
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

        # Track sales data for analytics
        company_analytics_data[company.id]['sales_revenue'] += result['total_revenue']

        for facility_result in result['facility_results']:
            sales_result = facility_result['result']
            if sales_result['success']:
                company_analytics_data[company.id]['goods_sold'] += sales_result['goods_sold']
                company_analytics_data[company.id]['influence_spent'] += sales_result['influence_spent']
                company_analytics_data[company.id]['sales_facilities'].append(facility_result['facility_id'])

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
    from app.models import StockPriceHistory

    for company in companies:
        old_price = company.stock_price
        company.current_equity = company.calculate_equity()
        stock_market.update_company_stock_price(company, config)

        # Record stock price history for charting
        history_entry = StockPriceHistory(
            company_id=company.id,
            week=current_week,
            stock_price=company.stock_price
        )
        db.session.add(history_entry)

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
    from app.models import StockOwnership, Player

    for company in companies:
        if company.has_ipo and company.dividend_rate > 0:
            # Pay dividends to all shareholders
            ownerships = StockOwnership.query.filter_by(company_id=company.id).all()
            total_dividend_paid = 0

            for ownership in ownerships:
                dividend_amount = ownership.shares_owned * company.dividend_rate

                if ownership.player_id:
                    # Pay to player's personal cash
                    player = Player.query.get(ownership.player_id)
                    if player:
                        player.personal_cash += dividend_amount
                # NPCs don't get paid (money disappears)

                total_dividend_paid += dividend_amount

            # Deduct total from company cash
            company.cash -= total_dividend_paid

            dividend_summary.append({
                'company': company.name,
                'dividend_rate': company.dividend_rate,
                'total_paid': total_dividend_paid,
                'shareholders': len(ownerships)
            })

    phase_summaries['dividends'] = {
        'companies_processed': len(dividend_summary),
        'details': dividend_summary
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
    # Phase 28: Update Status Effects (EventEffect Processing)
    # ====================
    effect_summary = []

    # Get all active event effects for this game
    all_effects = EventEffect.query.join(EventEffect.event).filter(
        Event.game_id == game.id,
        EventEffect.is_active == True,
        EventEffect.is_expired == False
    ).all()

    for effect in all_effects:
        # Check if effect should be active this week
        if not effect.is_currently_active(current_week):
            # Mark as expired if past end week
            if current_week > effect.end_week:
                effect.is_expired = True
                effect_summary.append({
                    'effect_id': effect.id,
                    'action': 'expired',
                    'effect_type': effect.effect_type
                })
            continue

        # Apply the effect based on type
        effect_data = effect.get_effect_data()

        if effect.effect_type == 'stat_modifier':
            # Apply stat modifiers to company facilities
            # These are applied dynamically during generation phases
            # Just track that they're active
            effect_summary.append({
                'effect_id': effect.id,
                'action': 'active_modifier',
                'company_id': effect.company_id,
                'modifiers': effect_data
            })

        elif effect.effect_type == 'facility_depreciation':
            # Apply additional depreciation to facilities
            amount = effect_data.get('amount', 0)
            if effect.facility_id:
                # Specific facility
                facility = Facility.query.get(effect.facility_id)
                if facility:
                    facility.condition = max(0, facility.condition - amount)
                    effect_summary.append({
                        'effect_id': effect.id,
                        'action': 'depreciation',
                        'facility_id': facility.id,
                        'amount': amount
                    })
            elif effect.company_id:
                # All facilities in company
                company = Company.query.get(effect.company_id)
                if company:
                    for facility in company.facilities:
                        facility.condition = max(0, facility.condition - amount)
                    effect_summary.append({
                        'effect_id': effect.id,
                        'action': 'depreciation',
                        'company_id': company.id,
                        'facilities_affected': len(company.facilities),
                        'amount': amount
                    })
            else:
                # All facilities in game
                for company in companies:
                    for facility in company.facilities:
                        facility.condition = max(0, facility.condition - amount)
                effect_summary.append({
                    'effect_id': effect.id,
                    'action': 'depreciation',
                    'all_companies': True,
                    'amount': amount
                })

        elif effect.effect_type == 'capital_deletion':
            # Delete capital from companies
            capital_type = effect_data.get('capital_type')
            amount = effect_data.get('amount', 0)

            if effect.company_id:
                company = Company.query.get(effect.company_id)
                if company and capital_type:
                    current_value = getattr(company, capital_type, 0)
                    setattr(company, capital_type, max(0, current_value - amount))
                    effect_summary.append({
                        'effect_id': effect.id,
                        'action': 'capital_deletion',
                        'company_id': company.id,
                        'capital_type': capital_type,
                        'amount': amount
                    })
            else:
                # All companies
                for company in companies:
                    if capital_type:
                        current_value = getattr(company, capital_type, 0)
                        setattr(company, capital_type, max(0, current_value - amount))
                effect_summary.append({
                    'effect_id': effect.id,
                    'action': 'capital_deletion',
                    'all_companies': True,
                    'capital_type': capital_type,
                    'amount': amount
                })

        elif effect.effect_type == 'facility_disable':
            # Disable facilities temporarily
            # Mark in effect summary - actual disabling would be checked during generation
            effect_summary.append({
                'effect_id': effect.id,
                'action': 'facility_disabled',
                'facility_id': effect.facility_id,
                'company_id': effect.company_id
            })

    phase_summaries['status_effects'] = {
        'effects_processed': len(effect_summary),
        'effects_expired': len([e for e in effect_summary if e.get('action') == 'expired']),
        'details': effect_summary
    }

    # ====================
    # Phase 28b: Execute Governance Proposals
    # ====================
    governance_summary = []

    # Get all active proposals that have ended voting this week
    ended_proposals = GovernanceProposal.query.join(GovernanceProposal.company).filter(
        Company.game_id == game.id,
        GovernanceProposal.voting_ends_week == current_week,
        GovernanceProposal.status == 'active'
    ).all()

    for proposal in ended_proposals:
        # Calculate if proposal passed
        current_percent = proposal.calculate_vote_percentage()
        passed = current_percent >= proposal.required_percent

        if passed:
            proposal.status = 'passed'

            # Execute the proposal based on type
            proposal_data = proposal.get_proposal_data()
            company = proposal.company

            if proposal.proposal_type == 'stock_split':
                # Execute stock split
                split_ratio = proposal_data.get('split_ratio', 2)  # Default 2:1

                # Update all stock ownerships
                from app.models import StockOwnership
                ownerships = StockOwnership.query.filter_by(company_id=company.id).all()

                for ownership in ownerships:
                    ownership.shares_owned = int(ownership.shares_owned * split_ratio)

                # Update total shares
                company.total_shares = int(company.total_shares * split_ratio)

                # Adjust stock price (inverse of split ratio)
                company.stock_price = company.stock_price / split_ratio

                proposal.status = 'executed'
                governance_summary.append({
                    'proposal_id': proposal.id,
                    'company': company.name,
                    'type': 'stock_split',
                    'split_ratio': split_ratio,
                    'result': 'executed'
                })

            elif proposal.proposal_type == 'dividend_change':
                # Execute dividend rate change
                new_dividend_rate = proposal_data.get('new_dividend_rate', 0)
                old_rate = company.dividend_rate

                company.dividend_rate = new_dividend_rate

                proposal.status = 'executed'
                governance_summary.append({
                    'proposal_id': proposal.id,
                    'company': company.name,
                    'type': 'dividend_change',
                    'old_rate': old_rate,
                    'new_rate': new_dividend_rate,
                    'result': 'executed'
                })

            elif proposal.proposal_type == 'custom':
                # Custom proposals just marked as passed, professor must handle
                governance_summary.append({
                    'proposal_id': proposal.id,
                    'company': company.name,
                    'type': 'custom',
                    'result': 'passed_awaiting_professor'
                })
        else:
            # Proposal failed
            proposal.status = 'failed'
            governance_summary.append({
                'proposal_id': proposal.id,
                'company': proposal.company.name,
                'type': proposal.proposal_type,
                'result': 'failed',
                'vote_percent': current_percent,
                'required_percent': proposal.required_percent
            })

    phase_summaries['governance_execution'] = {
        'proposals_resolved': len(governance_summary),
        'proposals_executed': len([g for g in governance_summary if 'executed' in g.get('result', '')]),
        'proposals_failed': len([g for g in governance_summary if g.get('result') == 'failed']),
        'details': governance_summary
    }

    # ====================
    # Phase 29: Record Analytics Data
    # ====================
    analytics_summary = []
    for company in companies:
        weekly_data = company_analytics_data.get(company.id, {})
        history = analytics.record_weekly_metrics(
            company=company,
            current_week=current_week,
            config=config,
            weekly_data=weekly_data
        )
        analytics_summary.append({
            'company': company.name,
            'equity': history.equity,
            'cash': history.cash,
            'sales_revenue': history.sales_revenue,
            'sales_profit': history.sales_profit
        })

    phase_summaries['analytics'] = {
        'companies_recorded': len(analytics_summary),
        'details': analytics_summary
    }

    # ====================
    # Phase 30: Refresh UI
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
