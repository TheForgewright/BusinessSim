"""
Stock Market System
Handles stock pricing, trading, and dividends
"""
from app import db
from app.models import StockOwnership, StockTransaction


def calculate_stock_price(company, config):
    """
    Calculate stock price for company

    Stock Price = (Base Equity / Total Shares) × (1 + Dividend Mod + Momentum Bonus)

    Base Equity = (Capital Value + Cash - Total Debt)
    """
    # Calculate base equity
    capital_value = company.get_total_capital_value()
    total_debt = company.get_total_debt()
    base_equity = max(0.01, capital_value + company.cash - total_debt)  # Minimum 0.01

    # Calculate per-share base price
    base_price_per_share = base_equity / company.total_shares

    # Calculate dividend modifier (based on dividend history)
    dividend_modifier = 0.0  # TODO: Implement based on dividend payment history

    # Calculate momentum bonus (based on recent equity growth)
    momentum_bonus = 0.0
    if company.last_week_equity > 0:
        equity_change = (company.current_equity - company.last_week_equity) / company.last_week_equity
        momentum_bonus = min(0.5, max(-0.5, equity_change * config.MOMENTUM_BONUS_WEIGHT))

    # Final price
    final_price = base_price_per_share * (1 + dividend_modifier + momentum_bonus)

    return max(0.01, final_price)  # Minimum price 0.01


def update_company_stock_price(company, config):
    """Update company's stock price"""
    company.stock_price = calculate_stock_price(company, config)


def execute_stock_purchase(buyer_player, company, shares, current_week):
    """
    Execute stock purchase

    Args:
        buyer_player: Player object buying shares
        company: Company whose stock is being bought
        shares: Number of shares to buy
        current_week: Current game week

    Returns:
        dict: {
            'success': bool,
            'shares_bought': int,
            'total_cost': float,
            'price_per_share': float,
            'message': str
        }
    """
    if shares <= 0:
        return {
            'success': False,
            'shares_bought': 0,
            'total_cost': 0,
            'price_per_share': 0,
            'message': 'Invalid share count'
        }

    # Calculate total cost
    price_per_share = company.stock_price
    total_cost = shares * price_per_share

    # Check if buyer has enough cash
    if buyer_player.personal_cash < total_cost:
        return {
            'success': False,
            'shares_bought': 0,
            'total_cost': total_cost,
            'price_per_share': price_per_share,
            'message': f'Insufficient personal cash (need {total_cost:.2f}, have {buyer_player.personal_cash:.2f})'
        }

    # Deduct cash from buyer
    buyer_player.personal_cash -= total_cost

    # Add/update stock ownership
    ownership = StockOwnership.query.filter_by(
        company_id=company.id,
        player_id=buyer_player.id
    ).first()

    if ownership:
        ownership.shares_owned += shares
    else:
        ownership = StockOwnership(
            company_id=company.id,
            player_id=buyer_player.id,
            investor_name=buyer_player.username,
            shares_owned=shares,
            is_npc=False,
            freeze_trading=False
        )
        db.session.add(ownership)

    # Record transaction
    transaction = StockTransaction(
        company_id=company.id,
        player_id=buyer_player.id,
        transaction_type='buy',
        shares=shares,
        price_per_share=price_per_share,
        total_amount=total_cost,
        week=current_week
    )
    db.session.add(transaction)

    return {
        'success': True,
        'shares_bought': shares,
        'total_cost': total_cost,
        'price_per_share': price_per_share,
        'message': f'Purchased {shares} shares at {price_per_share:.2f} per share'
    }


def execute_stock_sale(seller_player, company, shares, current_week):
    """
    Execute stock sale

    Returns:
        dict: Similar to execute_stock_purchase
    """
    if shares <= 0:
        return {
            'success': False,
            'shares_sold': 0,
            'total_revenue': 0,
            'price_per_share': 0,
            'message': 'Invalid share count'
        }

    # Check if seller owns enough shares
    ownership = StockOwnership.query.filter_by(
        company_id=company.id,
        player_id=seller_player.id
    ).first()

    if not ownership or ownership.shares_owned < shares:
        owned = ownership.shares_owned if ownership else 0
        return {
            'success': False,
            'shares_sold': 0,
            'total_revenue': 0,
            'price_per_share': 0,
            'message': f'Insufficient shares (trying to sell {shares}, own {owned})'
        }

    # Calculate total revenue
    price_per_share = company.stock_price
    total_revenue = shares * price_per_share

    # Deduct shares from seller
    ownership.shares_owned -= shares

    # Add cash to seller's personal account
    seller_player.personal_cash += total_revenue

    # Record transaction
    transaction = StockTransaction(
        company_id=company.id,
        player_id=seller_player.id,
        transaction_type='sell',
        shares=shares,
        price_per_share=price_per_share,
        total_amount=total_revenue,
        week=current_week
    )
    db.session.add(transaction)

    return {
        'success': True,
        'shares_sold': shares,
        'total_revenue': total_revenue,
        'price_per_share': price_per_share,
        'message': f'Sold {shares} shares at {price_per_share:.2f} per share'
    }


def issue_new_shares(company, shares_to_issue):
    """
    Issue new shares (dilutes existing ownership)

    New shares go to company owner's personal account
    Cash goes to company treasury
    """
    # Calculate how much cash to raise
    cash_raised = shares_to_issue * company.stock_price

    # Increase total shares
    company.total_shares += shares_to_issue

    # Add cash to company
    company.cash += cash_raised

    # Add shares to owner's personal ownership
    owner_ownership = StockOwnership.query.filter_by(
        company_id=company.id,
        player_id=company.owner_id
    ).first()

    if owner_ownership:
        owner_ownership.shares_owned += shares_to_issue
    else:
        owner_ownership = StockOwnership(
            company_id=company.id,
            player_id=company.owner_id,
            investor_name=company.owner.username,
            shares_owned=shares_to_issue,
            is_npc=False
        )
        db.session.add(owner_ownership)

    return cash_raised


def pay_dividends(company, dividend_amount_total, current_week):
    """
    Pay dividends to all shareholders

    Args:
        company: Company paying dividends
        dividend_amount_total: Total dividend pool
        current_week: Current game week

    Returns:
        dict: {
            'total_paid': float,
            'payments': [{investor, shares, amount}]
        }
    """
    # Get all shareholders
    shareholders = StockOwnership.query.filter_by(company_id=company.id).all()

    if not shareholders or company.total_shares == 0:
        return {
            'total_paid': 0,
            'payments': []
        }

    # Calculate per-share dividend
    per_share_dividend = dividend_amount_total / company.total_shares

    payments = []

    for shareholder in shareholders:
        if shareholder.shares_owned <= 0:
            continue

        # Calculate dividend for this shareholder
        dividend = shareholder.shares_owned * per_share_dividend

        # Pay to player's personal account if player
        if shareholder.player_id and shareholder.player:
            shareholder.player.personal_cash += dividend

        payments.append({
            'investor_name': shareholder.investor_name,
            'shares': shareholder.shares_owned,
            'amount': dividend,
            'is_player': shareholder.player_id is not None
        })

    # Deduct total from company cash
    company.cash -= dividend_amount_total

    return {
        'total_paid': dividend_amount_total,
        'payments': payments
    }


def get_player_portfolio_value(player):
    """
    Calculate total value of player's stock portfolio

    Returns:
        dict: {
            'total_value': float,
            'holdings': [{company_name, shares, value}]
        }
    """
    holdings = StockOwnership.query.filter_by(player_id=player.id).all()

    total_value = 0
    portfolio = []

    for holding in holdings:
        if holding.shares_owned <= 0:
            continue

        company = holding.company
        value = holding.shares_owned * company.stock_price

        total_value += value

        portfolio.append({
            'company_name': company.name,
            'company_id': company.id,
            'shares': holding.shares_owned,
            'price_per_share': company.stock_price,
            'total_value': value
        })

    return {
        'total_value': total_value,
        'holdings': portfolio
    }


def get_player_total_wealth(player):
    """
    Calculate player's total wealth (personal cash + stock portfolio value)

    This is the final score metric!
    """
    portfolio = get_player_portfolio_value(player)
    total_wealth = player.personal_cash + portfolio['total_value']

    return {
        'personal_cash': player.personal_cash,
        'portfolio_value': portfolio['total_value'],
        'total_wealth': total_wealth,
        'holdings': portfolio['holdings']
    }
