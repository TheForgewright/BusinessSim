"""
Flask Application Factory
"""
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from config import config

# Initialize extensions
db = SQLAlchemy()


def create_app(config_name='default'):
    """Create and configure Flask application"""
    app = Flask(__name__)
    app.config.from_object(config[config_name])

    # Initialize extensions
    db.init_app(app)
    CORS(app)

    # Register blueprints
    from app.routes import main, professor, student, api, auth
    app.register_blueprint(main.bp)
    app.register_blueprint(professor.bp, url_prefix='/professor')
    app.register_blueprint(student.bp, url_prefix='/student')
    app.register_blueprint(api.bp, url_prefix='/api')
    app.register_blueprint(auth.bp)

    # Create database tables
    with app.app_context():
        db.create_all()

    return app
