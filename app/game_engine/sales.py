"""
Sales Revenue Generation System
Handles sales facilities generating revenue from products
"""
from app.game_engine.dice import roll_dice
from app.game_engine.capital_generation import deduct_capital_from_company


def calculate_sales_revenue(facility, company, products, config, influence_to_spend=0):
    """
    Calculate revenue for a sales facility

    Sales Mechanics:
    - Base sales rate = 1 goods sold per influence generation potential
    - Influence generation = facility's influence dice roll
    - Can spend extra influence to boost sales by INFLUENCE_SALES_MULTIPLIER
    - Revenue = goods_sold × BASE_GOODS_SALE_VALUE

    Args:
        facility: Sales facility (must have link_capacity > 0)
        company: Company owning the facility
        products: List of products linked to this facility
        config: Config object
        influence_to_spend: Extra influence to spend for boosted sales

    Returns:
        dict: {
            'success': bool,
            'influence_potential': float,
            'influence_spent': float,
            'goods_sold': float,
            'revenue': float,
            'product_sales': [{product, goods_sold, revenue}],
            'message': str
        }
    """
    if not facility.is_active:
        return {
            'success': False,
            'influence_potential': 0,
            'influence_spent': 0,
            'goods_sold': 0,
            'revenue': 0,
            'product_sales': [],
            'message': 'Facility is shutdown'
        }

    if facility.condition <= 0:
        return {
            'success': False,
            'influence_potential': 0,
            'influence_spent': 0,
            'goods_sold': 0,
            'revenue': 0,
            'product_sales': [],
            'message': 'Facility is destroyed'
        }

    template = facility.template

    if template.link_capacity <= 0:
        return {
            'success': False,
            'influence_potential': 0,
            'influence_spent': 0,
            'goods_sold': 0,
            'revenue': 0,
            'product_sales': [],
            'message': 'This facility cannot link products (not a sales facility)'
        }

    if not products or len(products) == 0:
        return {
            'success': False,
            'influence_potential': 0,
            'influence_spent': 0,
            'goods_sold': 0,
            'revenue': 0,
            'product_sales': [],
            'message': 'No products linked to this facility'
        }

    # Get influence generation potential from facility
    base_generation = template.get_base_generation()
    influence_dice = base_generation.get('Influence', 'd6+2')  # Default if not specified

    # Roll for influence potential (marketing/sales capacity)
    influence_potential = roll_dice(influence_dice)

    # Add focus bonus if company focus is Influence
    if company.weekly_focus == 'Influence':
        focus_bonuses = template.get_focus_bonuses()
        influence_potential += focus_bonuses.get('Influence', 0)

    # Check if company has enough influence to spend
    from app.game_engine.capital_generation import get_company_capital
    available_influence = get_company_capital(company, 'Influence')

    if influence_to_spend > available_influence:
        influence_to_spend = available_influence

    # Calculate total sales capacity
    # Base: 1 goods per influence potential
    # Boost: influence_to_spend × INFLUENCE_SALES_MULTIPLIER
    base_sales_capacity = influence_potential
    boost_multiplier = influence_to_spend * config.INFLUENCE_SALES_MULTIPLIER
    total_sales_capacity = base_sales_capacity * (1 + boost_multiplier)

    # Deduct influence spent
    if influence_to_spend > 0:
        deduct_capital_from_company(company, 'Influence', influence_to_spend)

    # Distribute sales capacity across linked products
    # For now, split evenly
    per_product_capacity = total_sales_capacity / len(products)

    product_sales = []
    total_goods_sold = 0
    total_revenue = 0

    for product in products:
        # Check if company has goods to sell
        available_goods = get_company_capital(company, 'Goods')

        # Sell up to capacity or available goods, whichever is less
        goods_to_sell = min(per_product_capacity, available_goods)

        if goods_to_sell > 0:
            # Deduct goods from inventory
            deduct_capital_from_company(company, 'Goods', goods_to_sell)

            # Calculate revenue
            product_revenue = goods_to_sell * config.BASE_GOODS_SALE_VALUE

            # Add to company cash
            company.cash += product_revenue

            product_sales.append({
                'product_id': product.id,
                'product_name': product.name,
                'goods_sold': goods_to_sell,
                'revenue': product_revenue
            })

            total_goods_sold += goods_to_sell
            total_revenue += product_revenue

    return {
        'success': True,
        'influence_potential': influence_potential,
        'influence_spent': influence_to_spend,
        'goods_sold': total_goods_sold,
        'revenue': total_revenue,
        'product_sales': product_sales,
        'message': f'Sold {total_goods_sold:.1f} goods for ${total_revenue:.2f} revenue'
    }


def process_all_sales_facilities(company, current_week, config):
    """
    Process sales for all active sales facilities in a company

    Returns:
        dict: {
            'total_revenue': float,
            'facility_results': [results per facility]
        }
    """
    from app.models import Product

    total_revenue = 0
    facility_results = []

    # Get all active facilities with link capacity
    sales_facilities = [f for f in company.facilities
                        if f.is_active and f.template.link_capacity > 0]

    for facility in sales_facilities:
        # Get linked products
        linked_product_ids = facility.get_linked_products()

        if not linked_product_ids:
            continue

        products = Product.query.filter(
            Product.id.in_(linked_product_ids),
            Product.company_id == company.id
        ).all()

        # Calculate sales (no extra influence spending in auto-processing)
        result = calculate_sales_revenue(facility, company, products, config, influence_to_spend=0)

        if result['success']:
            total_revenue += result['revenue']

        facility_results.append({
            'facility_id': facility.id,
            'facility_name': facility.name,
            'result': result
        })

    return {
        'total_revenue': total_revenue,
        'facility_results': facility_results
    }
