"""
Game Configuration
All professor-configurable game parameters
"""
import os

class Config:
    """Base configuration"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(os.path.abspath(os.path.dirname(__file__)), 'data', 'business_sim.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Email Configuration
    MAIL_SERVER = os.environ.get('MAIL_SERVER') or 'localhost'
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 25)
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'true').lower() in ['true', 'on', '1']
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER') or 'noreply@businesssim.local'
    MAIL_MAX_EMAILS = None
    MAIL_ASCII_ATTACHMENTS = False

    # Application URLs
    APP_URL = os.environ.get('APP_URL') or 'http://localhost:5000'

    # Game Settings (Professor Configurable)
    GAME_TOTAL_WEEKS = 50
    GAME_MAX_TURN_ADVANCEMENT = 3  # Students can advance max 3 weeks at once

    # Starting Conditions (Professor Configurable)
    STARTING_CASH = 5000.0
    STARTING_GOODS = 0.0
    STARTING_IP = 0.0
    STARTING_INFLUENCE = 0.0
    STARTING_LABOR = 0.0
    STARTING_SHARES = 1000
    STARTING_OWNERSHIP_PCT = 100.0

    # Facility Settings
    BASE_DEPRECIATION_RATE = 2.0  # Percent per week for active facilities
    PERSONNEL_SHUTDOWN_MULTIPLIER = 4.0  # Personnel facilities depreciate 4x when shut down
    PHYSICAL_SHUTDOWN_MULTIPLIER = 1.0  # Physical facilities depreciate 1x when shut down

    # Maintenance Settings
    MAINTENANCE_FREQUENCY_WEEKS = 12  # How often maintenance is required
    MAINTENANCE_COST_PERCENT = 15.0  # Percent of original build cost

    # Storage Costs (Cash per unit per week)
    STORAGE_COST_ACTIVE_GOODS = 2.0
    STORAGE_COST_BACKED_UP_GOODS = 0.5
    STORAGE_COST_ACTIVE_IP = 2.0
    STORAGE_COST_BACKED_UP_IP = 0.5
    STORAGE_COST_ACTIVE_INFLUENCE = 2.0
    STORAGE_COST_BACKED_UP_INFLUENCE = 0.5
    STORAGE_COST_ACTIVE_LABOR = 2.0
    STORAGE_COST_BACKED_UP_LABOR = 0.5

    # Facility Construction - Cash Equivalent Prices
    # If player doesn't have capital, they can pay cash instead
    CASH_EQUIVALENT_GOODS = 10.0  # 1 Goods = 10 Cash
    CASH_EQUIVALENT_IP = 15.0  # 1 IP = 15 Cash
    CASH_EQUIVALENT_INFLUENCE = 12.0  # 1 Influence = 12 Cash
    CASH_EQUIVALENT_LABOR = 8.0  # 1 Labor = 8 Cash

    # Sales Revenue Settings
    BASE_GOODS_SALE_VALUE = 10.0  # Base cash value per goods sold
    INFLUENCE_SALES_MULTIPLIER = 1.0  # Spending 1 influence = 1x more goods sold

    # Market Settings
    MARKET_SATURATION_RATE = 0.3  # Saturation penalty rate
    PRODUCT_DEGRADATION_RATE = 2.0  # Percent per week

    # Stock Market Settings
    WEEKLY_TRADING_LIMIT = None  # None = unlimited, or set to number
    DIVIDEND_MODIFIER_WEIGHT = 0.05  # Impact of dividend history on stock price
    MOMENTUM_BONUS_WEIGHT = 0.1  # Impact of recent growth on stock price

    # Event Distribution (per player over entire game)
    EVENTS_MAJOR_POSITIVE = 1
    EVENTS_MAJOR_NEGATIVE = 1
    EVENTS_MODERATE_POSITIVE = 2
    EVENTS_MODERATE_NEGATIVE = 2
    EVENTS_MINOR_POSITIVE = 3
    EVENTS_MINOR_NEGATIVE = 3

    # Bankruptcy Settings
    BANKRUPTCY_ENABLED = False  # Professor can enable bankruptcy as game-over


class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True


class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False


config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
