"""
Seed Database with Initial Data
Creates facility templates and sample tags
"""
from app import create_app, db
from app.models import FacilityTemplate, Tag, Player, Game
from werkzeug.security import generate_password_hash

def create_facility_templates():
    """Create sample facility templates"""

    templates = [
        # R&D Lab (Physical)
        {
            'name': 'R&D Lab',
            'facility_type': 'physical',
            'description': 'Research and development laboratory for IP generation',
            'build_cost': {'Goods': 80, 'IP': 50, 'Influence': 20, 'Labor': 70, 'Cash': 500},
            'build_time_weeks': 16,
            'weekly_operating_cost': 100.0,
            'cost_per_capital': {'Goods': 10, 'IP': 15, 'Influence': 12, 'Labor': 8},
            'base_generation': {'Goods': 'd6+2', 'IP': 'd8+3', 'Influence': 'd4+1', 'Labor': 'd6+2', 'Cash': 'd8+5'},
            'focus_bonuses': {'Goods': 2, 'IP': 5, 'Influence': 1, 'Labor': 2, 'Cash': 0},
            'link_capacity': 0
        },

        # R&D Staff (Personnel)
        {
            'name': 'R&D Staff',
            'facility_type': 'personnel',
            'description': 'Skilled research and development team',
            'build_cost': {'Labor': 100, 'Influence': 30, 'Cash': 300},
            'build_time_weeks': 8,
            'weekly_operating_cost': 150.0,
            'cost_per_capital': {'IP': 12, 'Labor': 5},
            'base_generation': {'IP': 'd8+4', 'Labor': 'd6+3', 'Cash': 'd6+2'},
            'focus_bonuses': {'IP': 6, 'Labor': 3, 'Cash': 0},
            'link_capacity': 0
        },

        # Sales Team (Personnel)
        {
            'name': 'Sales Team',
            'facility_type': 'personnel',
            'description': 'Professional sales force that sells products',
            'build_cost': {'Labor': 80, 'Influence': 50, 'Cash': 400},
            'build_time_weeks': 6,
            'weekly_operating_cost': 120.0,
            'cost_per_capital': {'Influence': 10},
            'base_generation': {'Cash': 'd10+5', 'Influence': 'd6+2'},
            'focus_bonuses': {'Cash': 8, 'Influence': 3},
            'link_capacity': 3  # Can link up to 3 products
        },

        # Warehouse (Physical)
        {
            'name': 'Warehouse',
            'facility_type': 'physical',
            'description': 'Storage facility for goods',
            'build_cost': {'Goods': 120, 'Cash': 600},
            'build_time_weeks': 12,
            'weekly_operating_cost': 80.0,
            'cost_per_capital': {'Goods': 8},
            'base_generation': {'Goods': 'd8+4', 'Cash': 'd6+2'},
            'focus_bonuses': {'Goods': 6, 'Cash': 1},
            'link_capacity': 0
        },

        # Factory Floor (Physical)
        {
            'name': 'Factory Floor',
            'facility_type': 'physical',
            'description': 'Manufacturing facility for goods production',
            'build_cost': {'Goods': 150, 'Labor': 100, 'Cash': 800},
            'build_time_weeks': 20,
            'weekly_operating_cost': 200.0,
            'cost_per_capital': {'Goods': 12, 'Labor': 8},
            'base_generation': {'Goods': 'd10+5', 'Labor': 'd6+3'},
            'focus_bonuses': {'Goods': 8, 'Labor': 4},
            'link_capacity': 0
        },

        # Marketing Department (Personnel)
        {
            'name': 'Marketing Department',
            'facility_type': 'personnel',
            'description': 'Marketing and brand management team',
            'build_cost': {'Influence': 80, 'Labor': 60, 'Cash': 500},
            'build_time_weeks': 8,
            'weekly_operating_cost': 130.0,
            'cost_per_capital': {'Influence': 15, 'Labor': 6},
            'base_generation': {'Influence': 'd8+4', 'Labor': 'd6+2', 'Cash': 'd6+3'},
            'focus_bonuses': {'Influence': 7, 'Labor': 2, 'Cash': 1},
            'link_capacity': 0
        },

        # Training Center (Physical)
        {
            'name': 'Training Center',
            'facility_type': 'physical',
            'description': 'Employee training and development facility',
            'build_cost': {'Labor': 90, 'Goods': 60, 'Cash': 450},
            'build_time_weeks': 10,
            'weekly_operating_cost': 90.0,
            'cost_per_capital': {'Labor': 10},
            'base_generation': {'Labor': 'd8+4', 'Cash': 'd6+2'},
            'focus_bonuses': {'Labor': 6, 'Cash': 1},
            'link_capacity': 0
        }
    ]

    for template_data in templates:
        # Check if template already exists
        existing = FacilityTemplate.query.filter_by(name=template_data['name']).first()
        if existing:
            print(f"  - Template '{template_data['name']}' already exists, skipping")
            continue

        template = FacilityTemplate(
            name=template_data['name'],
            facility_type=template_data['facility_type'],
            description=template_data['description'],
            build_time_weeks=template_data['build_time_weeks'],
            weekly_operating_cost=template_data['weekly_operating_cost'],
            link_capacity=template_data['link_capacity']
        )

        template.set_build_cost(template_data['build_cost'])
        template.set_cost_per_capital(template_data['cost_per_capital'])
        template.set_base_generation(template_data['base_generation'])
        template.set_focus_bonuses(template_data['focus_bonuses'])

        db.session.add(template)
        print(f"  ✓ Created facility template: {template_data['name']}")

    db.session.commit()


def create_sample_tags(game_id):
    """Create sample product tags for a game"""

    tags = [
        {'name': 'Consumer', 'demand': 2.0, 'margin': 0.6, 'description': 'Mass market products - high volume, low margins'},
        {'name': 'Enterprise', 'demand': 0.8, 'margin': 1.8, 'description': 'B2B - lower volume, high margins'},
        {'name': 'Luxury', 'demand': 0.4, 'margin': 2.5, 'description': 'Premium - very limited market, exceptional margins'},
        {'name': 'Budget', 'demand': 2.5, 'margin': 0.4, 'description': 'Low-cost - massive volume, razor-thin margins'},
        {'name': 'Technology', 'demand': 1.2, 'margin': 1.0, 'description': 'Tech sector - moderate volume and margins'},
        {'name': 'Healthcare', 'demand': 0.9, 'margin': 1.6, 'description': 'Medical - regulated, stable demand, good margins'},
        {'name': 'Mobile', 'demand': 1.5, 'margin': 0.8, 'description': 'Mobile devices - high volume, competitive margins'},
        {'name': 'Cloud', 'demand': 1.1, 'margin': 1.3, 'description': 'Cloud services - growing demand, SaaS margins'},
        {'name': 'AI', 'demand': 0.7, 'margin': 2.0, 'description': 'Cutting edge - limited market, premium pricing'},
        {'name': 'Industrial', 'demand': 0.6, 'margin': 1.4, 'description': 'B2B equipment - niche, steady margins'},
        {'name': 'Premium', 'demand': 0.5, 'margin': 2.2, 'description': 'High-end positioning - limited customers, high margins'},
        {'name': 'Standard', 'demand': 1.3, 'margin': 1.0, 'description': 'Mid-market - balanced volume and margins'},
        {'name': 'Software', 'demand': 1.4, 'margin': 1.1, 'description': 'Software products - scalable, good margins'},
        {'name': 'Hardware', 'demand': 1.1, 'margin': 0.9, 'description': 'Physical devices - manufacturing costs'},
        {'name': 'Service', 'demand': 1.0, 'margin': 1.3, 'description': 'Service offerings - labor intensive'},
    ]

    for tag_data in tags:
        # Check if tag already exists for this game
        existing = Tag.query.filter_by(game_id=game_id, name=tag_data['name']).first()
        if existing:
            print(f"  - Tag '{tag_data['name']}' already exists, skipping")
            continue

        tag = Tag(
            game_id=game_id,
            name=tag_data['name'],
            demand_multiplier=tag_data['demand'],
            profit_margin=tag_data['margin'],
            description=tag_data['description']
        )

        db.session.add(tag)
        print(f"  ✓ Created tag: {tag_data['name']}")

    db.session.commit()


def create_demo_data():
    """Create demo professor, game, and student"""

    # Create demo professor
    professor = Player.query.filter_by(username='professor').first()
    if not professor:
        professor = Player(
            username='professor',
            password_hash=generate_password_hash('password'),
            is_professor=True
        )
        db.session.add(professor)
        print("  ✓ Created demo professor (username: professor, password: password)")
    else:
        print("  - Professor account already exists")

    # Create demo student
    student = Player.query.filter_by(username='student').first()
    if not student:
        student = Player(
            username='student',
            password_hash=generate_password_hash('password'),
            is_professor=False,
            personal_cash=1000.0
        )
        db.session.add(student)
        print("  ✓ Created demo student (username: student, password: password)")
    else:
        print("  - Student account already exists")

    db.session.commit()

    # Create demo game
    game = Game.query.filter_by(name='Demo Game').first()
    if not game:
        game = Game(
            name='Demo Game',
            current_week=0,
            total_weeks=50,
            max_turn_advancement=3,
            is_active=True
        )
        db.session.add(game)
        db.session.commit()
        print(f"  ✓ Created demo game (ID: {game.id})")

        # Create tags for demo game
        print("\nCreating tags for demo game...")
        create_sample_tags(game.id)
    else:
        print("  - Demo game already exists")


def main():
    """Main seed function"""
    print("=" * 60)
    print("Business Simulation Game - Database Seeding")
    print("=" * 60)

    app = create_app()

    with app.app_context():
        print("\n1. Creating facility templates...")
        create_facility_templates()

        print("\n2. Creating demo data (professor, student, game)...")
        create_demo_data()

        print("\n" + "=" * 60)
        print("Database seeding complete!")
        print("=" * 60)
        print("\nDemo Accounts:")
        print("  Professor - username: professor, password: password")
        print("  Student   - username: student, password: password")
        print("\nYou can now run the server with: python run.py")
        print("=" * 60)


if __name__ == '__main__':
    main()
