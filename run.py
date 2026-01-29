"""
H2 System - Health & Hostel Management System
Entry point for the Flask application
"""
import os
from app import create_app, db
from config import Config
from app.models import User, Student, DoctorVisit, Prescription, Medicine, Asset, MaintenanceLog, SickLeaveRequest


def create_default_users():
    """Create default users for all roles if they don't exist"""
    # Define default users for all roles
    default_users = [
        {
            'username': 'admin',
            'email': 'admin@h2system.local',
            'first_name': 'Admin',
            'last_name': 'User',
            'role': 'Director',
            'password': 'admin'
        },
        {
            'username': 'h2',
            'email': 'h2@h2system.local',
            'first_name': 'H2',
            'last_name': 'Officer',
            'role': 'H2',
            'password': 'h2'
        },
        {
            'username': 'warden',
            'email': 'warden@h2system.local',
            'first_name': 'Warden',
            'last_name': 'User',
            'role': 'Warden',
            'password': 'warden'
        },
        {
            'username': 'office',
            'email': 'office@h2system.local',
            'first_name': 'Office',
            'last_name': 'Staff',
            'role': 'Office',
            'password': 'office'
        },
        {
            'username': 'director',
            'email': 'director@h2system.local',
            'first_name': 'Director',
            'last_name': 'User',
            'role': 'Director',
            'password': 'director'
        },
        {
            'username': 'doctor',
            'email': 'doctor@h2system.local',
            'first_name': 'Doctor',
            'last_name': 'User',
            'role': 'Doctor',
            'password': 'doctor'
        }
    ]
    
    created_count = 0
    for user_data in default_users:
        user = User.query.filter_by(username=user_data['username']).first()
        
        if not user:
            user = User(
                username=user_data['username'],
                email=user_data['email'],
                first_name=user_data['first_name'],
                last_name=user_data['last_name'],
                role=user_data['role'],
                is_active=True
            )
            user.set_password(user_data['password'])
            db.session.add(user)
            created_count += 1
    
    if created_count > 0:
        db.session.commit()
        print(f"✓ Created {created_count} default user(s)")
        print("\nDefault Login Credentials:")
        print("  admin / admin (Director)")
        print("  h2 / h2 (H2 Officer)")
        print("  warden / warden (Warden)")
        print("  office / office (Office Staff)")
        print("  director / director (Director)")
        print("  doctor / doctor (Doctor)")


if __name__ == '__main__':
    # Create Flask app
    app = create_app(os.environ.get('FLASK_ENV', 'development'))
    
    # Create database tables
    with app.app_context():
        db.create_all()
        create_default_users()
    
    # Run development server
    debug = os.environ.get('FLASK_DEBUG', True)
    host = os.environ.get('FLASK_HOST', '0.0.0.0')
    port = int(os.environ.get('FLASK_PORT', 5000))
    
    print(f"\n{'='*50}")
    print("H2 System - Health & Hostel Management")
    print(f"{'='*50}")
    print(f"Starting server on http://{host}:{port}")
    print(f"{'='*50}\n")
    print(os.environ.get('FLASK_ENV', 'development'))
    
    app.run(host=host, port=port, debug=debug)
