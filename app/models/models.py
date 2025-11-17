"""
Database Models for Business Simulation Game
"""
from datetime import datetime, timedelta
from app import db
import json
import secrets


class Game(db.Model):
    """Overall game state and configuration"""
    __tablename__ = 'games'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    current_week = db.Column(db.Integer, default=0)
    total_weeks = db.Column(db.Integer, default=50)
    max_turn_advancement = db.Column(db.Integer, default=3)
    is_active = db.Column(db.Boolean, default=True)

    # Analytics Settings
    allow_endgame_analytics = db.Column(db.Boolean, default=True)  # Show analytics to all players at game end
    analytics_visible_json = db.Column(db.Text, default='{}')  # JSON: {company_id: bool} - professor can toggle per player
    sales_profit_facility_multiplier = db.Column(db.Float, default=0.8)  # 80% of facility cost attributed to sales

    # Governance Settings
    governance_base_threshold = db.Column(db.Float, default=60.0)  # Base vote % required (default 60%)
    governance_difficulty_modifier = db.Column(db.Float, default=5.0)  # % reduction per difficulty point (default 5%)
    governance_influence_modifier = db.Column(db.Float, default=5.0)  # % increase per influence spent (default 5%)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    companies = db.relationship('Company', backref='game', lazy=True, cascade='all, delete-orphan')
    events = db.relationship('Event', backref='game', lazy=True, cascade='all, delete-orphan')
    tags = db.relationship('Tag', backref='game', lazy=True, cascade='all, delete-orphan')

    def get_analytics_visible(self):
        """Get dict of company_id -> visibility"""
        if not self.analytics_visible_json:
            return {}
        return json.loads(self.analytics_visible_json)

    def set_analytics_visible(self, visible_dict):
        """Set analytics visibility dict"""
        self.analytics_visible_json = json.dumps(visible_dict)

    def is_analytics_visible_for_company(self, company_id):
        """Check if analytics are visible for a specific company"""
        visible = self.get_analytics_visible()
        return visible.get(str(company_id), False)

    def toggle_analytics_visibility(self, company_id):
        """Toggle analytics visibility for a company"""
        visible = self.get_analytics_visible()
        company_key = str(company_id)
        visible[company_key] = not visible.get(company_key, False)
        self.set_analytics_visible(visible)
        return visible[company_key]

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'current_week': self.current_week,
            'total_weeks': self.total_weeks,
            'max_turn_advancement': self.max_turn_advancement,
            'is_active': self.is_active,
            'allow_endgame_analytics': self.allow_endgame_analytics,
            'sales_profit_facility_multiplier': self.sales_profit_facility_multiplier,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class Player(db.Model):
    """Student/Professor accounts"""
    __tablename__ = 'players'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=True)  # Nullable until first login
    email = db.Column(db.String(255), unique=True, nullable=False)  # Required for all users
    password_hash = db.Column(db.String(200), nullable=True)  # Nullable until password is set
    is_professor = db.Column(db.Boolean, default=False)
    personal_cash = db.Column(db.Float, default=0.0)  # Personal wealth (from dividends, stock sales)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime, nullable=True)

    # Email verification
    email_verified = db.Column(db.Boolean, default=False)
    verification_token = db.Column(db.String(100), nullable=True)
    verification_token_expiry = db.Column(db.DateTime, nullable=True)

    # Password reset
    password_reset_token = db.Column(db.String(100), nullable=True)
    password_reset_token_expiry = db.Column(db.DateTime, nullable=True)

    # First login tracking
    needs_username_setup = db.Column(db.Boolean, default=True)

    # Relationships
    companies = db.relationship('Company', backref='owner', lazy=True)
    stock_ownership = db.relationship('StockOwnership', backref='player', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'is_professor': self.is_professor,
            'personal_cash': self.personal_cash,
            'email_verified': self.email_verified,
            'needs_username_setup': self.needs_username_setup,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None
        }

    def generate_password_reset_token(self):
        """Generate a password reset token valid for 1 hour"""
        self.password_reset_token = secrets.token_urlsafe(32)
        self.password_reset_token_expiry = datetime.utcnow() + timedelta(hours=1)
        return self.password_reset_token

    def verify_password_reset_token(self, token):
        """Check if the password reset token is valid"""
        if not self.password_reset_token or not self.password_reset_token_expiry:
            return False
        if self.password_reset_token != token:
            return False
        if datetime.utcnow() > self.password_reset_token_expiry:
            return False
        return True

    def clear_password_reset_token(self):
        """Clear the password reset token after use"""
        self.password_reset_token = None
        self.password_reset_token_expiry = None

    def generate_verification_token(self):
        """Generate an email verification token valid for 24 hours"""
        self.verification_token = secrets.token_urlsafe(32)
        self.verification_token_expiry = datetime.utcnow() + timedelta(hours=24)
        return self.verification_token

    def verify_email_token(self, token):
        """Check if the email verification token is valid"""
        if not self.verification_token or not self.verification_token_expiry:
            return False
        if self.verification_token != token:
            return False
        if datetime.utcnow() > self.verification_token_expiry:
            return False
        return True

    def mark_email_verified(self):
        """Mark email as verified and clear the verification token"""
        self.email_verified = True
        self.verification_token = None
        self.verification_token_expiry = None


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
    has_ipo = db.Column(db.Boolean, default=False)  # Whether company has gone public
    ipo_week = db.Column(db.Integer)  # Week company went public
    dividend_rate = db.Column(db.Float, default=0.0)  # Dividend per share per week (set at IPO)

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
    history = db.relationship('CompanyHistory', backref='company', lazy=True, cascade='all, delete-orphan')

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


class CompanyHistory(db.Model):
    """Historical metrics for analytics"""
    __tablename__ = 'company_history'

    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False)
    week = db.Column(db.Integer, nullable=False)

    # Financial Metrics
    equity = db.Column(db.Float, default=0.0)
    cash = db.Column(db.Float, default=0.0)
    total_debt = db.Column(db.Float, default=0.0)

    # Operations Metrics
    weekly_depreciation = db.Column(db.Float, default=0.0)  # Total depreciation this week
    sales_revenue = db.Column(db.Float, default=0.0)  # Revenue from goods sold
    sales_profit = db.Column(db.Float, default=0.0)  # Net profit after all costs

    # Sales Cost Components (for profit calculation)
    goods_cost = db.Column(db.Float, default=0.0)  # Cost to produce goods sold
    influence_cost = db.Column(db.Float, default=0.0)  # Cost of influence spent on sales
    facility_cost = db.Column(db.Float, default=0.0)  # Allocated cost of sales facilities

    recorded_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'company_id': self.company_id,
            'week': self.week,
            'equity': self.equity,
            'cash': self.cash,
            'total_debt': self.total_debt,
            'weekly_depreciation': self.weekly_depreciation,
            'sales_revenue': self.sales_revenue,
            'sales_profit': self.sales_profit,
            'goods_cost': self.goods_cost,
            'influence_cost': self.influence_cost,
            'facility_cost': self.facility_cost,
            'recorded_at': self.recorded_at.isoformat() if self.recorded_at else None
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


class StockPriceHistory(db.Model):
    """Track stock prices over time for charts"""
    __tablename__ = 'stock_price_history'

    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False)
    week = db.Column(db.Integer, nullable=False)
    stock_price = db.Column(db.Float, nullable=False)
    recorded_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'company_id': self.company_id,
            'week': self.week,
            'stock_price': self.stock_price,
            'recorded_at': self.recorded_at.isoformat() if self.recorded_at else None
        }


class GovernanceProposal(db.Model):
    """Company governance proposals (splits, major decisions)"""
    __tablename__ = 'governance_proposals'

    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False)
    proposed_by = db.Column(db.Integer, db.ForeignKey('players.id'), nullable=False)

    proposal_type = db.Column(db.String(50), nullable=False)  # 'stock_split', 'dividend_change', 'custom'
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)

    # Voting parameters
    difficulty = db.Column(db.Integer, nullable=False, default=5)  # 1-10
    influence_spent = db.Column(db.Float, default=0.0)  # Influence spent by proposer

    # Voting status
    required_percent = db.Column(db.Float, nullable=False)  # Calculated based on difficulty
    votes_for = db.Column(db.Integer, default=0)
    votes_against = db.Column(db.Integer, default=0)
    total_eligible_shares = db.Column(db.Integer, nullable=False)  # Shares that can vote (non-owner)

    # Timing
    created_week = db.Column(db.Integer, nullable=False)
    voting_ends_week = db.Column(db.Integer, nullable=False)

    # Status
    status = db.Column(db.String(20), default='active')  # 'active', 'passed', 'failed', 'executed'

    # Proposal data (JSON for type-specific fields)
    proposal_data_json = db.Column(db.Text, default='{}')

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    company = db.relationship('Company')
    proposer = db.relationship('Player')
    votes = db.relationship('GovernanceVote', backref='proposal', lazy=True, cascade='all, delete-orphan')

    def get_proposal_data(self):
        return json.loads(self.proposal_data_json) if self.proposal_data_json else {}

    def set_proposal_data(self, data_dict):
        self.proposal_data_json = json.dumps(data_dict)

    def calculate_vote_percentage(self):
        """Calculate percentage of eligible shares voting for"""
        if self.total_eligible_shares == 0:
            return 0.0
        return (self.votes_for / self.total_eligible_shares) * 100

    def to_dict(self):
        return {
            'id': self.id,
            'company_id': self.company_id,
            'proposed_by': self.proposed_by,
            'proposal_type': self.proposal_type,
            'title': self.title,
            'description': self.description,
            'difficulty': self.difficulty,
            'influence_spent': self.influence_spent,
            'required_percent': self.required_percent,
            'votes_for': self.votes_for,
            'votes_against': self.votes_against,
            'total_eligible_shares': self.total_eligible_shares,
            'current_percent': self.calculate_vote_percentage(),
            'created_week': self.created_week,
            'voting_ends_week': self.voting_ends_week,
            'status': self.status,
            'proposal_data': self.get_proposal_data(),
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class GovernanceVote(db.Model):
    """Individual votes on governance proposals"""
    __tablename__ = 'governance_votes'

    id = db.Column(db.Integer, primary_key=True)
    proposal_id = db.Column(db.Integer, db.ForeignKey('governance_proposals.id'), nullable=False)
    player_id = db.Column(db.Integer, db.ForeignKey('players.id'), nullable=True)  # None for NPCs
    investor_name = db.Column(db.String(200), nullable=False)

    shares_voted = db.Column(db.Integer, nullable=False)
    vote_direction = db.Column(db.String(10), nullable=False)  # 'for', 'against', 'abstain'

    voted_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'proposal_id': self.proposal_id,
            'player_id': self.player_id,
            'investor_name': self.investor_name,
            'shares_voted': self.shares_voted,
            'vote_direction': self.vote_direction,
            'voted_at': self.voted_at.isoformat() if self.voted_at else None
        }


class EventEffect(db.Model):
    """Active effects from events applied to companies/facilities"""
    __tablename__ = 'event_effects'

    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('events.id'), nullable=False)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=True)  # None = all companies
    facility_id = db.Column(db.Integer, db.ForeignKey('facilities.id'), nullable=True)  # Specific facility target

    # Effect Type
    effect_type = db.Column(db.String(50), nullable=False)
    # Types: stat_modifier, facility_depreciation, capital_deletion, facility_disable

    # Effect Details (JSON)
    effect_data_json = db.Column(db.Text, default='{}')
    # For stat_modifier: {stat_name: modifier_value} e.g. {"goods_generation_rate": 1.5}
    # For facility_depreciation: {amount: 10.0}
    # For capital_deletion: {capital_type: "goods", amount: 100}
    # For facility_disable: {duration_weeks: 3}

    # Duration
    start_week = db.Column(db.Integer, nullable=False)
    duration_weeks = db.Column(db.Integer, nullable=False)
    end_week = db.Column(db.Integer, nullable=False)  # Calculated: start_week + duration_weeks

    # Status
    is_active = db.Column(db.Boolean, default=True)
    is_expired = db.Column(db.Boolean, default=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    event = db.relationship('Event', backref=db.backref('effects', lazy='dynamic'))
    company = db.relationship('Company', backref=db.backref('active_effects', lazy='dynamic'))
    facility = db.relationship('Facility', backref=db.backref('active_effects', lazy='dynamic'))

    def get_effect_data(self):
        """Parse effect data from JSON"""
        import json
        if self.effect_data_json:
            return json.loads(self.effect_data_json)
        return {}

    def set_effect_data(self, data):
        """Set effect data as JSON"""
        import json
        self.effect_data_json = json.dumps(data)

    def is_currently_active(self, current_week):
        """Check if effect should be active for the given week"""
        return (self.is_active and
                not self.is_expired and
                self.start_week <= current_week <= self.end_week)

    def to_dict(self):
        return {
            'id': self.id,
            'event_id': self.event_id,
            'company_id': self.company_id,
            'facility_id': self.facility_id,
            'effect_type': self.effect_type,
            'effect_data': self.get_effect_data(),
            'start_week': self.start_week,
            'duration_weeks': self.duration_weeks,
            'end_week': self.end_week,
            'is_active': self.is_active,
            'is_expired': self.is_expired,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
