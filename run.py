"""
H2 System - Health & Hostel Management System
Entry point for the Flask application
"""
import os
from app import create_app, db
from config import Config
from app.models import User, Student, DoctorVisit, Prescription, Medicine, Asset, MaintenanceLog, SickLeaveRequest, MedicalEquipment, MedicineBatch, BatchDispensing


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


def create_sample_equipment():
    """Create sample medical equipment"""
    sample_equipment = [
        {
            'name': 'Crepe Bandage (5cm)',
            'equipment_code': 'CB-5CM',
            'category': 'Support',
            'quantity_available': 20,
            'unit_cost': 50.00,
            'daily_penalty': 5.00,
            'location': 'H2 Storage A'
        },
        {
            'name': 'Crepe Bandage (10cm)',
            'equipment_code': 'CB-10CM',
            'category': 'Support',
            'quantity_available': 15,
            'unit_cost': 75.00,
            'daily_penalty': 7.50,
            'location': 'H2 Storage A'
        },
        {
            'name': 'Hot Pack (Electric)',
            'equipment_code': 'HP-ELEC',
            'category': 'Thermal',
            'quantity_available': 10,
            'unit_cost': 500.00,
            'daily_penalty': 25.00,
            'location': 'H2 Storage B'
        },
        {
            'name': 'Ice Pack Gel',
            'equipment_code': 'IP-GEL',
            'category': 'Thermal',
            'quantity_available': 12,
            'unit_cost': 150.00,
            'daily_penalty': 10.00,
            'location': 'H2 Storage B'
        },
        {
            'name': 'Knee Support Brace',
            'equipment_code': 'KSB-UNI',
            'category': 'Support',
            'quantity_available': 8,
            'unit_cost': 300.00,
            'daily_penalty': 20.00,
            'location': 'H2 Storage C'
        },
        {
            'name': 'Elbow Support Brace',
            'equipment_code': 'ESB-UNI',
            'category': 'Support',
            'quantity_available': 8,
            'unit_cost': 250.00,
            'daily_penalty': 15.00,
            'location': 'H2 Storage C'
        },
        {
            'name': 'Ankle Support Wrap',
            'equipment_code': 'ASW-UNI',
            'category': 'Support',
            'quantity_available': 15,
            'unit_cost': 200.00,
            'daily_penalty': 12.00,
            'location': 'H2 Storage C'
        },
        {
            'name': 'Back Support Belt',
            'equipment_code': 'BSB-MED',
            'category': 'Support',
            'quantity_available': 6,
            'unit_cost': 400.00,
            'daily_penalty': 20.00,
            'location': 'H2 Storage C'
        },
        {
            'name': 'Neck Collar',
            'equipment_code': 'NC-SOFT',
            'category': 'Support',
            'quantity_available': 10,
            'unit_cost': 350.00,
            'daily_penalty': 15.00,
            'location': 'H2 Storage D'
        },
        {
            'name': 'TENS Machine',
            'equipment_code': 'TENS-001',
            'category': 'Device',
            'quantity_available': 3,
            'unit_cost': 2000.00,
            'daily_penalty': 100.00,
            'location': 'H2 Storage D'
        },
        {
            'name': 'Digital Thermometer',
            'equipment_code': 'THERM-DIG',
            'category': 'Device',
            'quantity_available': 5,
            'unit_cost': 300.00,
            'daily_penalty': 15.00,
            'location': 'H2 Storage D'
        },
        {
            'name': 'Blood Pressure Monitor',
            'equipment_code': 'BPM-AUTO',
            'category': 'Device',
            'quantity_available': 2,
            'unit_cost': 1500.00,
            'daily_penalty': 75.00,
            'location': 'H2 Storage D'
        }
    ]
    
    created_count = 0
    for equipment_data in sample_equipment:
        equipment = MedicalEquipment.query.filter_by(equipment_code=equipment_data['equipment_code']).first()
        
        if not equipment:
            equipment = MedicalEquipment(**equipment_data)
            db.session.add(equipment)
            created_count += 1
    
    if created_count > 0:
        db.session.commit()
        print(f"✓ Created {created_count} sample medical equipment items")


if __name__ == '__main__':
    # Create Flask app
    app = create_app(os.environ.get('FLASK_ENV', 'development'))
    
    # Create database tables
    with app.app_context():
        db.create_all()
        create_default_users()
        create_sample_equipment()
    
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
