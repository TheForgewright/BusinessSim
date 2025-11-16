"""
Database Models for Business Simulation Game
"""
from datetime import datetime
from app import db
import json


class Game(db.Model):
    """Overall game state and configuration"""
    __tablename__ = 'games'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    current_week = db.Column(db.Integer, default=0)
    total_weeks = db.Column(db.Integer, default=50)
    max_turn_advancement = db.Column(db.Integer, default=3)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    companies = db.relationship('Company', backref='game', lazy=True, cascade='all, delete-orphan')
    events = db.relationship('Event', backref='game', lazy=True, cascade='all, delete-orphan')
    tags = db.relationship('Tag', backref='game', lazy=True, cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'current_week': self.current_week,
            'total_weeks': self.total_weeks,
            'max_turn_advancement': self.max_turn_advancement,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class Player(db.Model):
    """Student/Professor accounts"""
    __tablename__ = 'players'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    is_professor = db.Column(db.Boolean, default=False)
    personal_cash = db.Column(db.Float, default=0.0)  # Personal wealth (from dividends, stock sales)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    companies = db.relationship('Company', backref='owner', lazy=True)
    stock_ownership = db.relationship('StockOwnership', backref='player', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'is_professor': self.is_professor,
            'personal_cash': self.personal_cash,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class Company(db.Model):
    """Student companies"""
    __tablename__ = 'companies'

    id = db.Column(db.Integer, primary_key=True)
    game_id = db.Column(db.Integer, db.ForeignKey('games.id'), nullable=False)
    owner_id = db.Column(db.Integer, db.ForeignKey('players.id'), nullable=False)
    name = db.Column(db.String(200), nullable=False)

    # Capital Resources
    cash = db.Column(db.Float, default=5000.0)
    goods_active = db.Column(db.Float, default=0.0)
    goods_backed_up = db.Column(db.Float, default=0.0)
    ip_active = db.Column(db.Float, default=0.0)
    ip_backed_up = db.Column(db.Float, default=0.0)
    influence_active = db.Column(db.Float, default=0.0)
    influence_backed_up = db.Column(db.Float, default=0.0)
    labor_active = db.Column(db.Float, default=0.0)
    labor_backed_up = db.Column(db.Float, default=0.0)

    # Focus System
    weekly_focus = db.Column(db.String(50))  # 'Goods', 'IP', 'Influence', 'Labor', 'Cash'

    # Stock Information
    total_shares = db.Column(db.Integer, default=1000)
    stock_price = db.Column(db.Float, default=5.0)

    # Cash Reserve (for auto-pay protection)
    cash_reserve = db.Column(db.Float, default=0.0)

    # Equity Tracking
    current_equity = db.Column(db.Float, default=5000.0)
    last_week_equity = db.Column(db.Float, default=5000.0)

    # Capital Attrition Tracking (JSON: {capital_type: weeks_since_generation})
    attrition_counters = db.Column(db.Text, default='{}')

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    facilities = db.relationship('Facility', backref='company', lazy=True, cascade='all, delete-orphan')
    debts = db.relationship('Debt', backref='company', lazy=True, cascade='all, delete-orphan')
    products = db.relationship('Product', backref='company', lazy=True, cascade='all, delete-orphan')
    stock_ownership = db.relationship('StockOwnership', backref='company', lazy=True, cascade='all, delete-orphan')
    construction_timers = db.relationship('ConstructionTimer', backref='company', lazy=True, cascade='all, delete-orphan')

    def get_attrition_counters(self):
        """Parse JSON attrition counters"""
        if not self.attrition_counters:
            return {}
        return json.loads(self.attrition_counters)

    def set_attrition_counters(self, counters):
        """Set JSON attrition counters"""
        self.attrition_counters = json.dumps(counters)

    def get_total_capital_value(self):
        """Calculate total value of all capital"""
        # This would need pricing logic - for now simple sum
        return (self.goods_active + self.goods_backed_up +
                self.ip_active + self.ip_backed_up +
                self.influence_active + self.influence_backed_up +
                self.labor_active + self.labor_backed_up)

    def get_total_debt(self):
        """Calculate total debt (principal + accrued interest)"""
        return sum(debt.principal + debt.accrued_interest
                   for debt in self.debts if not debt.resolved)

    def calculate_equity(self):
        """Calculate company equity"""
        capital_value = self.get_total_capital_value()
        total_debt = self.get_total_debt()
        return capital_value + self.cash - total_debt

    def to_dict(self):
        return {
            'id': self.id,
            'game_id': self.game_id,
            'owner_id': self.owner_id,
            'name': self.name,
            'cash': self.cash,
            'goods_active': self.goods_active,
            'goods_backed_up': self.goods_backed_up,
            'ip_active': self.ip_active,
            'ip_backed_up': self.ip_backed_up,
            'influence_active': self.influence_active,
            'influence_backed_up': self.influence_backed_up,
            'labor_active': self.labor_active,
            'labor_backed_up': self.labor_backed_up,
            'weekly_focus': self.weekly_focus,
            'total_shares': self.total_shares,
            'stock_price': self.stock_price,
            'cash_reserve': self.cash_reserve,
            'current_equity': self.current_equity,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class FacilityTemplate(db.Model):
    """Facility definitions (professor configurable)"""
    __tablename__ = 'facility_templates'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    facility_type = db.Column(db.String(50), nullable=False)  # 'physical' or 'personnel'
    description = db.Column(db.Text)

    # Build Costs (JSON: {capital_type: amount})
    build_cost_json = db.Column(db.Text, nullable=False)
    build_time_weeks = db.Column(db.Integer, default=1)

    # Operating Costs
    weekly_operating_cost = db.Column(db.Float, default=0.0)

    # Per-capital generation costs (JSON: {capital_type: cost_per_unit})
    cost_per_capital_json = db.Column(db.Text, default='{}')

    # Base Generation (JSON: {capital_type: dice_expression})
    base_generation_json = db.Column(db.Text, default='{}')

    # Focus Bonuses (JSON: {capital_type: bonus_amount})
    focus_bonuses_json = db.Column(db.Text, default='{}')

    # Link Capacity (for linking products to sales facilities)
    link_capacity = db.Column(db.Integer, default=0)

    def get_build_cost(self):
        return json.loads(self.build_cost_json) if self.build_cost_json else {}

    def set_build_cost(self, cost_dict):
        self.build_cost_json = json.dumps(cost_dict)

    def get_cost_per_capital(self):
        return json.loads(self.cost_per_capital_json) if self.cost_per_capital_json else {}

    def set_cost_per_capital(self, cost_dict):
        self.cost_per_capital_json = json.dumps(cost_dict)

    def get_base_generation(self):
        return json.loads(self.base_generation_json) if self.base_generation_json else {}

    def set_base_generation(self, gen_dict):
        self.base_generation_json = json.dumps(gen_dict)

    def get_focus_bonuses(self):
        return json.loads(self.focus_bonuses_json) if self.focus_bonuses_json else {}

    def set_focus_bonuses(self, bonus_dict):
        self.focus_bonuses_json = json.dumps(bonus_dict)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'facility_type': self.facility_type,
            'description': self.description,
            'build_cost': self.get_build_cost(),
            'build_time_weeks': self.build_time_weeks,
            'weekly_operating_cost': self.weekly_operating_cost,
            'cost_per_capital': self.get_cost_per_capital(),
            'base_generation': self.get_base_generation(),
            'focus_bonuses': self.get_focus_bonuses(),
            'link_capacity': self.link_capacity
        }


class Facility(db.Model):
    """Facilities owned by companies"""
    __tablename__ = 'facilities'

    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False)
    template_id = db.Column(db.Integer, db.ForeignKey('facility_templates.id'), nullable=False)
    name = db.Column(db.String(200), nullable=False)

    # State
    is_active = db.Column(db.Boolean, default=True)  # True = active, False = shutdown
    condition = db.Column(db.Float, default=100.0)  # 0-100%
    weeks_until_maintenance = db.Column(db.Integer, default=12)

    # Linked Products (for sales facilities) - JSON array of product IDs
    linked_products_json = db.Column(db.Text, default='[]')

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    template = db.relationship('FacilityTemplate', backref='instances')

    def get_linked_products(self):
        return json.loads(self.linked_products_json) if self.linked_products_json else []

    def set_linked_products(self, product_ids):
        self.linked_products_json = json.dumps(product_ids)

    def to_dict(self):
        return {
            'id': self.id,
            'company_id': self.company_id,
            'template_id': self.template_id,
            'name': self.name,
            'is_active': self.is_active,
            'condition': self.condition,
            'weeks_until_maintenance': self.weeks_until_maintenance,
            'linked_products': self.get_linked_products(),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'template': self.template.to_dict() if self.template else None
        }


class Debt(db.Model):
    """Company debts and loans"""
    __tablename__ = 'debts'

    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    creditor = db.Column(db.String(200))

    # Amounts
    principal = db.Column(db.Float, nullable=False)
    accrued_interest = db.Column(db.Float, default=0.0)
    interest_rate = db.Column(db.Float, nullable=False)  # Annual percentage rate

    # Compounding
    compounding_type = db.Column(db.String(50), default='not_compounding')
    # Options: not_compounding, daily, weekly, monthly, quarterly
    last_interest_week = db.Column(db.Integer, default=0)

    # Terms
    collateral = db.Column(db.Text)
    due_date = db.Column(db.Integer)  # Week number, or None
    term_weeks = db.Column(db.Integer)  # Loan duration
    agreed_payment_amount = db.Column(db.Float)  # Fixed weekly payment

    # Auto-pay
    auto_pay = db.Column(db.Boolean, default=False)
    missed_payments = db.Column(db.Integer, default=0)

    # Status
    resolved = db.Column(db.Boolean, default=False)
    week_created = db.Column(db.Integer, nullable=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def get_total_owed(self):
        """Total amount owed (principal + accrued interest)"""
        return self.principal + self.accrued_interest

    def to_dict(self):
        return {
            'id': self.id,
            'company_id': self.company_id,
            'name': self.name,
            'creditor': self.creditor,
            'principal': self.principal,
            'accrued_interest': self.accrued_interest,
            'interest_rate': self.interest_rate,
            'compounding_type': self.compounding_type,
            'last_interest_week': self.last_interest_week,
            'collateral': self.collateral,
            'due_date': self.due_date,
            'term_weeks': self.term_weeks,
            'agreed_payment_amount': self.agreed_payment_amount,
            'auto_pay': self.auto_pay,
            'missed_payments': self.missed_payments,
            'resolved': self.resolved,
            'week_created': self.week_created,
            'total_owed': self.get_total_owed()
        }


class Product(db.Model):
    """Products created from capital"""
    __tablename__ = 'products'

    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False)
    name = db.Column(db.String(200), nullable=False)

    # Capital Investment
    ip_invested = db.Column(db.Float, default=0.0)
    goods_invested = db.Column(db.Float, default=0.0)
    base_value = db.Column(db.Float, nullable=False)  # Initial product value

    # Current value (affected by degradation)
    current_value = db.Column(db.Float, nullable=False)

    # Tags (JSON array of tag names)
    tags_json = db.Column(db.Text, nullable=False)  # Must have exactly 3 tags

    # Product age tracking
    week_created = db.Column(db.Integer, nullable=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def get_tags(self):
        return json.loads(self.tags_json) if self.tags_json else []

    def set_tags(self, tag_list):
        if len(tag_list) != 3:
            raise ValueError("Product must have exactly 3 tags")
        self.tags_json = json.dumps(tag_list)

    def to_dict(self):
        return {
            'id': self.id,
            'company_id': self.company_id,
            'name': self.name,
            'ip_invested': self.ip_invested,
            'goods_invested': self.goods_invested,
            'base_value': self.base_value,
            'current_value': self.current_value,
            'tags': self.get_tags(),
            'week_created': self.week_created,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class Tag(db.Model):
    """Market positioning tags"""
    __tablename__ = 'tags'

    id = db.Column(db.Integer, primary_key=True)
    game_id = db.Column(db.Integer, db.ForeignKey('games.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    demand_multiplier = db.Column(db.Float, nullable=False)  # Volume potential
    profit_margin = db.Column(db.Float, nullable=False)  # Margin multiplier
    description = db.Column(db.Text)

    def to_dict(self):
        return {
            'id': self.id,
            'game_id': self.game_id,
            'name': self.name,
            'demand_multiplier': self.demand_multiplier,
            'profit_margin': self.profit_margin,
            'description': self.description
        }


class StockOwnership(db.Model):
    """Track who owns shares in each company"""
    __tablename__ = 'stock_ownership'

    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False)
    player_id = db.Column(db.Integer, db.ForeignKey('players.id'), nullable=True)  # None for NPCs
    investor_name = db.Column(db.String(200), nullable=False)
    shares_owned = db.Column(db.Integer, nullable=False, default=0)
    is_npc = db.Column(db.Boolean, default=False)
    freeze_trading = db.Column(db.Boolean, default=False)  # Prevent AI trading

    def to_dict(self):
        return {
            'id': self.id,
            'company_id': self.company_id,
            'player_id': self.player_id,
            'investor_name': self.investor_name,
            'shares_owned': self.shares_owned,
            'is_npc': self.is_npc,
            'freeze_trading': self.freeze_trading
        }


class StockTransaction(db.Model):
    """Stock buy/sell history"""
    __tablename__ = 'stock_transactions'

    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False)
    player_id = db.Column(db.Integer, db.ForeignKey('players.id'), nullable=True)
    transaction_type = db.Column(db.String(20), nullable=False)  # 'buy' or 'sell'
    shares = db.Column(db.Integer, nullable=False)
    price_per_share = db.Column(db.Float, nullable=False)
    total_amount = db.Column(db.Float, nullable=False)
    week = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'company_id': self.company_id,
            'player_id': self.player_id,
            'transaction_type': self.transaction_type,
            'shares': self.shares,
            'price_per_share': self.price_per_share,
            'total_amount': self.total_amount,
            'week': self.week,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class Event(db.Model):
    """Market events (scheduled or professor-triggered)"""
    __tablename__ = 'events'

    id = db.Column(db.Integer, primary_key=True)
    game_id = db.Column(db.Integer, db.ForeignKey('games.id'), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)

    # Event Type
    event_type = db.Column(db.String(50), nullable=False)
    # instant, multi_week, warning
    severity = db.Column(db.String(50))  # major_positive, major_negative, etc.

    # Timing
    trigger_week = db.Column(db.Integer, nullable=False)
    duration_weeks = db.Column(db.Integer, default=1)
    warning_weeks = db.Column(db.Integer, default=0)

    # Effects (JSON: {effect_type: value})
    effects_json = db.Column(db.Text, default='{}')

    # Targeting
    target_company_id = db.Column(db.Integer, db.ForeignKey('companies.id'))  # None = all companies
    target_tags = db.Column(db.Text)  # JSON array of tag names

    # Status
    is_active = db.Column(db.Boolean, default=False)
    is_completed = db.Column(db.Boolean, default=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def get_effects(self):
        return json.loads(self.effects_json) if self.effects_json else {}

    def set_effects(self, effects_dict):
        self.effects_json = json.dumps(effects_dict)

    def to_dict(self):
        return {
            'id': self.id,
            'game_id': self.game_id,
            'name': self.name,
            'description': self.description,
            'event_type': self.event_type,
            'severity': self.severity,
            'trigger_week': self.trigger_week,
            'duration_weeks': self.duration_weeks,
            'warning_weeks': self.warning_weeks,
            'effects': self.get_effects(),
            'target_company_id': self.target_company_id,
            'is_active': self.is_active,
            'is_completed': self.is_completed
        }


class ConstructionTimer(db.Model):
    """Track facilities under construction"""
    __tablename__ = 'construction_timers'

    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False)
    template_id = db.Column(db.Integer, db.ForeignKey('facility_templates.id'), nullable=False)
    facility_name = db.Column(db.String(200), nullable=False)

    # Construction timing
    start_week = db.Column(db.Integer, nullable=False)
    completion_week = db.Column(db.Integer, nullable=False)

    # Costs already paid
    costs_paid_json = db.Column(db.Text, default='{}')

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    template = db.relationship('FacilityTemplate')

    def get_costs_paid(self):
        return json.loads(self.costs_paid_json) if self.costs_paid_json else {}

    def set_costs_paid(self, costs_dict):
        self.costs_paid_json = json.dumps(costs_dict)

    def to_dict(self):
        return {
            'id': self.id,
            'company_id': self.company_id,
            'template_id': self.template_id,
            'facility_name': self.facility_name,
            'start_week': self.start_week,
            'completion_week': self.completion_week,
            'costs_paid': self.get_costs_paid(),
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
