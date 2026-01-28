"""
CLI Commands for H2 System Database Management
Usage: python cli.py <command>
"""

import click
from app import create_app, db
from app.models import User, Student, Medicine


app = create_app()


@click.group()
def cli():
    """H2 System CLI Commands"""
    pass


@cli.command()
def init_db():
    """Initialize the database"""
    with app.app_context():
        db.create_all()
        click.echo("✓ Database initialized successfully!")


@cli.command()
def reset_db():
    """Reset the database (WARNING: Deletes all data)"""
    if click.confirm('This will delete all data. Are you sure?'):
        with app.app_context():
            db.drop_all()
            db.create_all()
            click.echo("✓ Database reset successfully!")
    else:
        click.echo("✗ Database reset cancelled.")


@cli.command()
def seed_db():
    """Seed database with sample data"""
    with app.app_context():
        # Check if admin exists
        admin = User.query.filter_by(username='admin').first()
        if admin:
            click.echo("✗ Admin user already exists!")
            return
        
        # Create admin user
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
        
        # Create sample medicines
        medicines = [
            Medicine(
                name='Paracetamol',
                generic_name='Acetaminophen',
                dosage='500mg',
                quantity=100,
                min_stock_level=10,
                unit='tablets',
                supplier='PharmaCorp',
                cost_per_unit=0.50
            ),
            Medicine(
                name='Aspirin',
                generic_name='Acetylsalicylic Acid',
                dosage='325mg',
                quantity=80,
                min_stock_level=15,
                unit='tablets',
                supplier='MediChem',
                cost_per_unit=0.30
            ),
            Medicine(
                name='Vitamin C',
                generic_name='Ascorbic Acid',
                dosage='500mg',
                quantity=50,
                min_stock_level=20,
                unit='tablets',
                supplier='HealthPlus',
                cost_per_unit=0.20
            ),
        ]
        
        for medicine in medicines:
            db.session.add(medicine)
        
        db.session.commit()
        
        click.echo("✓ Database seeded successfully!")
        click.echo(f"  - Admin user: admin / admin")
        click.echo(f"  - Sample medicines: 3 added")


@cli.command()
def create_admin():
    """Create admin user"""
    with app.app_context():
        admin = User.query.filter_by(username='admin').first()
        if admin:
            click.echo("✗ Admin user already exists!")
            return
        
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
        
        click.echo("✓ Admin user created!")
        click.echo("  Username: admin")
        click.echo("  Password: admin")


@cli.command()
@click.option('--username', prompt='Username', help='Username for the user')
@click.option('--password', prompt='Password', hide_input=True, help='Password for the user')
@click.option('--email', prompt='Email', help='Email address')
@click.option('--first-name', prompt='First Name', default='', help='First name')
@click.option('--last-name', prompt='Last Name', default='', help='Last name')
@click.option('--role', type=click.Choice(['H2', 'Warden', 'Office', 'Director', 'Doctor', 'Student']), 
              prompt='Role', help='User role')
def create_user(username, password, email, first_name, last_name, role):
    """Create a new user"""
    with app.app_context():
        if User.query.filter_by(username=username).first():
            click.echo(f"✗ User '{username}' already exists!")
            return
        
        user = User(
            username=username,
            email=email,
            first_name=first_name,
            last_name=last_name,
            role=role,
            is_active=True
        )
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        
        click.echo(f"✓ User '{username}' created successfully!")


@cli.command()
def list_users():
    """List all users"""
    with app.app_context():
        users = User.query.all()
        
        if not users:
            click.echo("No users found.")
            return
        
        click.echo("\nRegistered Users:")
        click.echo("=" * 70)
        for user in users:
            status = "✓" if user.is_active else "✗"
            click.echo(f"{status} {user.username:20} | {user.email:25} | {user.role:10}")
        click.echo("=" * 70)


@cli.command()
@click.argument('username')
def delete_user(username):
    """Delete a user"""
    with app.app_context():
        user = User.query.filter_by(username=username).first()
        
        if not user:
            click.echo(f"✗ User '{username}' not found!")
            return
        
        if click.confirm(f"Delete user '{username}'?"):
            db.session.delete(user)
            db.session.commit()
            click.echo(f"✓ User '{username}' deleted!")
        else:
            click.echo("✗ Delete cancelled.")


@cli.command()
def db_stats():
    """Show database statistics"""
    with app.app_context():
        from app.models import Student, DoctorVisit, Prescription, Asset, SickLeaveRequest
        
        click.echo("\n📊 Database Statistics:")
        click.echo("=" * 40)
        click.echo(f"Users:             {User.query.count()}")
        click.echo(f"Students:          {Student.query.count()}")
        click.echo(f"Doctor Visits:     {DoctorVisit.query.count()}")
        click.echo(f"Prescriptions:     {Prescription.query.count()}")
        click.echo(f"Medicines:         {Medicine.query.count()}")
        click.echo(f"Assets:            {Asset.query.count()}")
        click.echo(f"Sick Requests:     {SickLeaveRequest.query.count()}")
        click.echo("=" * 40)


if __name__ == '__main__':
    cli()
