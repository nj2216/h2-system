"""
H2 System - Health & Hostel Management System
Entry point for the Flask application
"""
import os
from app import create_app, db
from app.models import User, Student, DoctorVisit, Prescription, Medicine, Asset, MaintenanceLog, SickLeaveRequest


def create_default_admin():
    """Create default admin user if it doesn't exist"""
    admin_user = User.query.filter_by(username='admin').first()
    
    if not admin_user:
        admin_user = User(
            username='admin',
            email='admin@h2system.local',
            first_name='Admin',
            last_name='User',
            role='Director',
            is_active=True
        )
        admin_user.set_password('admin')
        
        db.session.add(admin_user)
        db.session.commit()
        
        print("✓ Default admin user created (username: admin, password: admin)")


if __name__ == '__main__':
    # Create Flask app
    app = create_app(os.environ.get('FLASK_ENV', 'development'))
    
    # Create database tables
    with app.app_context():
        db.create_all()
        create_default_admin()
    
    # Run development server
    debug = os.environ.get('FLASK_DEBUG', True)
    host = os.environ.get('FLASK_HOST', '0.0.0.0')
    port = int(os.environ.get('FLASK_PORT', 5000))
    
    print(f"\n{'='*50}")
    print("H2 System - Health & Hostel Management")
    print(f"{'='*50}")
    print(f"Starting server on http://{host}:{port}")
    print("Default Login: admin / admin")
    print(f"{'='*50}\n")
    
    app.run(host=host, port=port, debug=debug)
