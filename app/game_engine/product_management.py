"""
Product Management System
Handles product creation, tagging, market positioning, saturation, and degradation
"""
from app import db
from app.models import Product, Tag
import json


def create_product(company, name, ip_invested, goods_invested, tags, current_week):
    """
    Create new product from capital

    Args:
        company: Company creating product
        name: Product name
        ip_invested: Amount of IP capital to invest
        goods_invested: Amount of Goods capital to invest (optional)
        tags: List of exactly 3 tag names
        current_week: Current game week

    Returns:
        dict: {
            'success': bool,
            'product': Product or None,
            'message': str
        }
    """
    # Validate tags
    if len(tags) != 3:
        return {
            'success': False,
            'product': None,
            'message': 'Product must have exactly 3 tags'
        }

    # Check if company has sufficient capital
    from app.game_engine.capital_generation import deduct_capital_from_company

    if not deduct_capital_from_company(company, 'IP', ip_invested):
        return {
            'success': False,
            'product': None,
            'message': f'Insufficient IP (need {ip_invested}, have {company.ip_active + company.ip_backed_up})'
        }

    if goods_invested > 0:
        if not deduct_capital_from_company(company, 'Goods', goods_invested):
            # Refund IP
            from app.game_engine.capital_generation import add_capital_to_company
            add_capital_to_company(company, 'IP', ip_invested)
            return {
                'success': False,
                'product': None,
                'message': f'Insufficient Goods (need {goods_invested}, have {company.goods_active + company.goods_backed_up})'
            }

    # Calculate base value
    base_value = ip_invested + goods_invested

    # Create product
    product = Product(
        company_id=company.id,
        name=name,
        ip_invested=ip_invested,
        goods_invested=goods_invested,
        base_value=base_value,
        current_value=base_value,
        week_created=current_week
    )
    product.set_tags(tags)

    db.session.add(product)

    return {
        'success': True,
        'product': product,
        'message': f'Created product "{name}" with value {base_value}'
    }


def get_tag_modifiers(product, game_id):
    """
    Calculate demand and margin modifiers based on product tags

    Returns:
        dict: {
            'volume_potential': float (average demand multiplier),
            'profit_margin': float (average margin multiplier),
            'tags_data': [tag objects]
        }
    """
    tag_names = product.get_tags()

    # Get tag objects from database
    tags = Tag.query.filter(
        Tag.game_id == game_id,
        Tag.name.in_(tag_names)
    ).all()

    if len(tags) != 3:
        # Default values if tags not found
        return {
            'volume_potential': 1.0,
            'profit_margin': 1.0,
            'tags_data': []
        }

    # Calculate averages
    total_demand = sum(tag.demand_multiplier for tag in tags)
    total_margin = sum(tag.profit_margin for tag in tags)

    volume_potential = total_demand / 3.0
    profit_margin = total_margin / 3.0

    return {
        'volume_potential': volume_potential,
        'profit_margin': profit_margin,
        'tags_data': tags
    }


def calculate_market_saturation(product, game_id, config):
    """
    Calculate market saturation based on competing products

    Competition Rules:
    - Share 3 tags: Full competition (1.0× weight)
    - Share 2 tags: Partial competition (0.5× weight)
    - Share 0-1 tags: No competition (0× weight)

    Returns:
        dict: {
            'saturation_penalty': float (0.0-1.0),
            'competing_products': int,
            'full_competitors': int,
            'partial_competitors': int
        }
    """
    product_tags = set(product.get_tags())

    # Find all competing products (same game, different company or same company)
    all_products = Product.query.join(Product.company).filter(
        Company.game_id == game_id
    ).all()

    full_competitors = 0
    partial_competitors = 0
    total_sales_teams = 0

    for other_product in all_products:
        if other_product.id == product.id:
            continue  # Don't compete with self

        other_tags = set(other_product.get_tags())
        shared_tags = len(product_tags.intersection(other_tags))

        # Count sales facilities linked to this product
        sales_teams = count_sales_teams_for_product(other_product)

        if shared_tags == 3:
            # Full competition
            full_competitors += 1
            total_sales_teams += sales_teams
        elif shared_tags == 2:
            # Partial competition (50% weight)
            partial_competitors += 1
            total_sales_teams += (sales_teams * 0.5)

    # Calculate saturation penalty
    # Formula: 1.0 / (1 + saturation_rate × (teams - 1))
    saturation_rate = config.MARKET_SATURATION_RATE

    if total_sales_teams <= 1:
        saturation_penalty = 1.0  # No saturation
    else:
        saturation_penalty = 1.0 / (1 + saturation_rate * (total_sales_teams - 1))

    return {
        'saturation_penalty': saturation_penalty,
        'competing_products': full_competitors + partial_competitors,
        'full_competitors': full_competitors,
        'partial_competitors': partial_competitors,
        'effective_sales_teams': total_sales_teams
    }


def count_sales_teams_for_product(product):
    """
    Count how many sales facilities are linked to this product

    Returns:
        int: Number of sales facilities
    """
    from app.models import Facility

    # Get all active facilities for this company
    facilities = Facility.query.filter_by(
        company_id=product.company_id,
        is_active=True
    ).all()

    count = 0

    for facility in facilities:
        linked_products = facility.get_linked_products()
        if product.id in linked_products:
            count += 1

    return count


def apply_product_degradation(product, config):
    """
    Apply weekly degradation to product value

    Degradation encourages product refresh/innovation
    """
    degradation_rate = config.PRODUCT_DEGRADATION_RATE / 100.0  # Convert to decimal
    product.current_value *= (1 - degradation_rate)
    product.current_value = max(0, product.current_value)


def calculate_product_revenue(product, facility, game_id, config):
    """
    Calculate revenue for selling a product through a sales facility

    Revenue = Base Generation × Product Value × Volume × Saturation × Margin × Events

    Returns:
        dict: {
            'revenue': float,
            'breakdown': {generation, value, volume, saturation, margin}
        }
    """
    from app.game_engine.dice import roll_dice

    # Step 1: Base generation from sales facility
    template = facility.template
    base_generation_dict = template.get_base_generation()

    # For sales facilities, they typically generate "Cash" or use a sales roll
    # We'll use Cash generation as the base multiplier
    base_roll = roll_dice(base_generation_dict.get('Cash', 'd10+5'))

    # Step 2: Product value
    product_value = product.current_value

    # Step 3: Tag modifiers
    tag_mods = get_tag_modifiers(product, game_id)
    volume_potential = tag_mods['volume_potential']
    profit_margin = tag_mods['profit_margin']

    # Step 4: Market saturation
    saturation_data = calculate_market_saturation(product, game_id, config)
    saturation_penalty = saturation_data['saturation_penalty']

    # Step 5: Calculate final revenue
    revenue = (
        base_roll *
        product_value *
        volume_potential *
        saturation_penalty *
        profit_margin
    )

    # TODO: Apply event modifiers (market booms, crashes, etc.)
    event_modifier = 1.0

    revenue *= event_modifier

    return {
        'revenue': revenue,
        'breakdown': {
            'base_roll': base_roll,
            'product_value': product_value,
            'volume_potential': volume_potential,
            'saturation_penalty': saturation_penalty,
            'profit_margin': profit_margin,
            'event_modifier': event_modifier
        }
    }


from app.models import Company  # Import here to avoid circular import
