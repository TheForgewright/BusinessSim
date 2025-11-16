"""
Debt Management System
Handles interest accrual, compounding, and auto-pay
"""
from app import db


def accrue_interest_on_debt(debt, current_week):
    """
    Accrue weekly interest on debt

    Weekly Interest = (Principal × Annual Rate) / 52 weeks
    """
    if debt.resolved:
        return 0

    # Calculate weekly interest rate
    weekly_rate = debt.interest_rate / 52.0 / 100.0  # Convert percentage to decimal and weekly

    # Calculate interest on current principal
    weekly_interest = debt.principal * weekly_rate

    # Add to accrued interest
    debt.accrued_interest += weekly_interest

    return weekly_interest


def check_and_compound_interest(debt, current_week):
    """
    Check if debt should compound interest and apply if needed

    Compounding frequencies:
    - not_compounding: Never compounds
    - daily: Every 1 week
    - weekly: Every 7 weeks
    - monthly: Every 4 weeks
    - quarterly: Every 13 weeks
    """
    if debt.resolved or debt.compounding_type == 'not_compounding':
        return False

    weeks_since_last = current_week - debt.last_interest_week

    should_compound = False

    if debt.compounding_type == 'daily' and weeks_since_last >= 1:
        should_compound = True
    elif debt.compounding_type == 'weekly' and weeks_since_last >= 7:
        should_compound = True
    elif debt.compounding_type == 'monthly' and weeks_since_last >= 4:
        should_compound = True
    elif debt.compounding_type == 'quarterly' and weeks_since_last >= 13:
        should_compound = True

    if should_compound:
        # Add accrued interest to principal
        debt.principal += debt.accrued_interest
        debt.accrued_interest = 0
        debt.last_interest_week = current_week
        return True

    return False


def calculate_weekly_payment(debt):
    """
    Calculate weekly payment amount for debt

    Returns:
        float: Weekly payment amount
    """
    if debt.agreed_payment_amount:
        # Fixed payment amount
        return debt.agreed_payment_amount
    elif debt.term_weeks and debt.term_weeks > 0:
        # Calculate payment based on term
        # Simple approach: (principal + estimated total interest) / term_weeks
        weeks_remaining = debt.term_weeks - (debt.last_interest_week - debt.week_created)
        if weeks_remaining <= 0:
            weeks_remaining = 1

        total_owed = debt.principal + debt.accrued_interest
        return total_owed / weeks_remaining
    else:
        # No payment schedule - return 0 (manual payment only)
        return 0


def make_debt_payment(debt, payment_amount):
    """
    Make payment on debt

    Payment priority: Accrued interest first, then principal

    Returns:
        dict: {
            'interest_paid': float,
            'principal_paid': float,
            'total_paid': float,
            'remaining_owed': float
        }
    """
    if debt.resolved:
        return {
            'interest_paid': 0,
            'principal_paid': 0,
            'total_paid': 0,
            'remaining_owed': 0
        }

    interest_paid = 0
    principal_paid = 0
    remaining_payment = payment_amount

    # Pay accrued interest first
    if debt.accrued_interest > 0:
        if remaining_payment >= debt.accrued_interest:
            interest_paid = debt.accrued_interest
            remaining_payment -= debt.accrued_interest
            debt.accrued_interest = 0
        else:
            interest_paid = remaining_payment
            debt.accrued_interest -= remaining_payment
            remaining_payment = 0

    # Pay principal with remaining
    if remaining_payment > 0 and debt.principal > 0:
        if remaining_payment >= debt.principal:
            principal_paid = debt.principal
            remaining_payment -= debt.principal
            debt.principal = 0
        else:
            principal_paid = remaining_payment
            debt.principal -= remaining_payment
            remaining_payment = 0

    # Check if debt is fully paid
    if debt.principal <= 0.01 and debt.accrued_interest <= 0.01:
        debt.principal = 0
        debt.accrued_interest = 0
        debt.resolved = True

    total_paid = interest_paid + principal_paid
    remaining_owed = debt.principal + debt.accrued_interest

    return {
        'interest_paid': interest_paid,
        'principal_paid': principal_paid,
        'total_paid': total_paid,
        'remaining_owed': remaining_owed
    }


def process_auto_pay_debts(company, current_week):
    """
    Process all auto-pay debts for company

    This happens BEFORE adding weekly earnings to treasury

    Returns:
        dict: {
            'total_paid': float,
            'payments': [payment_details],
            'available_cash_after': float
        }
    """
    # Calculate available cash (respecting reserve)
    available_cash = company.cash - company.cash_reserve
    if available_cash <= 0:
        return {
            'total_paid': 0,
            'payments': [],
            'available_cash_after': company.cash
        }

    # Get all auto-pay debts, sorted by oldest first
    auto_pay_debts = [d for d in company.debts if d.auto_pay and not d.resolved]
    auto_pay_debts.sort(key=lambda d: d.week_created)

    total_paid = 0
    payments = []

    for debt in auto_pay_debts:
        if available_cash <= 0:
            break

        # Calculate weekly payment
        weekly_payment = calculate_weekly_payment(debt)

        # Attempt to pay (up to available cash)
        payment_amount = min(weekly_payment, available_cash)

        if payment_amount > 0:
            result = make_debt_payment(debt, payment_amount)
            available_cash -= result['total_paid']
            total_paid += result['total_paid']

            payments.append({
                'debt_id': debt.id,
                'debt_name': debt.name,
                'attempted': weekly_payment,
                'actual': result['total_paid'],
                'interest_paid': result['interest_paid'],
                'principal_paid': result['principal_paid'],
                'remaining': result['remaining_owed']
            })

            # Track missed payment if couldn't pay full amount
            if result['total_paid'] < weekly_payment:
                debt.missed_payments += 1

    # Deduct total payments from company cash
    company.cash -= total_paid

    return {
        'total_paid': total_paid,
        'payments': payments,
        'available_cash_after': company.cash
    }


def check_overdue_debts(company, current_week):
    """
    Check for debts that are past due date

    Returns:
        list: Overdue debt objects
    """
    overdue = []

    for debt in company.debts:
        if not debt.resolved and debt.due_date and current_week >= debt.due_date:
            overdue.append(debt)

    return overdue


def create_debt(company, current_week, **kwargs):
    """
    Create new debt for company

    Required kwargs:
        - name: str
        - creditor: str
        - principal: float
        - interest_rate: float (annual percentage)

    Optional kwargs:
        - compounding_type: str (default 'not_compounding')
        - collateral: str
        - due_date: int (week number)
        - term_weeks: int
        - agreed_payment_amount: float
        - auto_pay: bool (default False)

    Returns:
        Debt: New debt object
    """
    from app.models import Debt

    debt = Debt(
        company_id=company.id,
        name=kwargs.get('name'),
        creditor=kwargs.get('creditor'),
        principal=kwargs.get('principal'),
        interest_rate=kwargs.get('interest_rate'),
        compounding_type=kwargs.get('compounding_type', 'not_compounding'),
        collateral=kwargs.get('collateral'),
        due_date=kwargs.get('due_date'),
        term_weeks=kwargs.get('term_weeks'),
        agreed_payment_amount=kwargs.get('agreed_payment_amount'),
        auto_pay=kwargs.get('auto_pay', False),
        week_created=current_week,
        last_interest_week=current_week
    )

    db.session.add(debt)

    # Add cash to company immediately
    company.cash += debt.principal

    return debt
