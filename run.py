"""
Business Simulation Game - Server Entry Point
"""
import os
from app import create_app, db
from config import config

# Create app
app = create_app(os.environ.get('FLASK_ENV', 'default'))

if __name__ == '__main__':
    # Create data directory if it doesn't exist
    os.makedirs('data', exist_ok=True)

    # Run development server
    print("=" * 60)
    print("Business Simulation Game Server")
    print("=" * 60)
    print(f"Environment: {os.environ.get('FLASK_ENV', 'default')}")
    print(f"Database: {app.config['SQLALCHEMY_DATABASE_URI']}")
    print("=" * 60)
    print("\nServer starting on http://localhost:5000")
    print("Press CTRL+C to quit\n")

    app.run(host='0.0.0.0', port=5000, debug=True)
