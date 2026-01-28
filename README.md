# H2 System - Health & Hostel Management System

A comprehensive Flask-based management system for health teams and hostel operations.

## Features

### 1. **Authentication & Role-Based Access Control (RBAC)**
- Secure login system with Flask-Login
- Multiple user roles: H2 (Health Team), Warden, Office, Director, Doctor, Student
- Role-specific dashboards and permissions

### 2. **Student Management**
- Student profile creation and management
- Emergency contact information
- Medical history tracking
- Allergies and current medications
- Role-based access to student information

### 3. **Health & Drug Management**
- Doctor visit records with symptoms, diagnosis, and treatment
- Prescription creation and tracking
- Medicine dispensing records
- Prescription status management

### 4. **Medical Stock Management**
- Medicine inventory tracking
- Low-stock alerts
- Stock movement history (ADD, DISPENSE, LOSS)
- Supplier and cost tracking
- Expiry date management

### 5. **Hostel Asset Management**
- Asset registration with unique codes
- Location and condition tracking
- Asset categorization (tables, chairs, heaters, etc.)
- Maintenance log history
- Asset condition reports

### 6. **Sick Leave & Sick Food Workflow**
- Multi-stage approval workflow:
  1. H2 (Health Team) reviews
  2. Warden verifies student presence
  3. Office approves
  4. Director review (optional)
- Request status tracking
- Support for sick leave and sick food requests

### 7. **Role-Specific Dashboards**
- **H2 Dashboard**: Student stats, medicine inventory, doctor visits
- **Warden Dashboard**: Asset inventory, maintenance logs, student management
- **Office Dashboard**: Request approvals, sick leave tracking
- **Director Dashboard**: System overview, user management, statistics
- **Student Dashboard**: Personal health history, prescriptions, requests
- **Doctor Dashboard**: Visit records, prescriptions managed

## Tech Stack

- **Backend**: Flask 3.0.0
- **Database**: SQLite with SQLAlchemy ORM
- **Frontend**: HTML5, CSS3, JavaScript with Bootstrap 5.3
- **Authentication**: Flask-Login
- **Architecture**: Blueprint-based modular design

## Project Structure

```
h2sqrr/
├── app/
│   ├── __init__.py              # App factory
│   ├── models.py                # Database models
│   ├── extensions.py            # Flask extensions
│   ├── auth/
│   │   ├── __init__.py
│   │   ├── routes.py            # Authentication routes
│   │   └── utils.py             # RBAC decorators
│   ├── students/
│   │   ├── __init__.py
│   │   └── routes.py            # Student management
│   ├── health/
│   │   ├── __init__.py
│   │   └── routes.py            # Doctor visits & prescriptions
│   ├── stock/
│   │   ├── __init__.py
│   │   └── routes.py            # Medicine inventory
│   ├── assets/
│   │   ├── __init__.py
│   │   └── routes.py            # Asset management
│   ├── sickleave/
│   │   ├── __init__.py
│   │   └── routes.py            # Sick leave workflow
│   ├── dashboards/
│   │   ├── __init__.py
│   │   └── routes.py            # Role-based dashboards
│   ├── templates/
│   │   ├── base.html            # Base template
│   │   ├── auth/                # Authentication templates
│   │   ├── students/            # Student templates
│   │   ├── health/              # Health templates
│   │   ├── stock/               # Stock templates
│   │   ├── assets/              # Asset templates
│   │   ├── sickleave/           # Sick leave templates
│   │   └── dashboards/          # Dashboard templates
│   └── static/
│       ├── css/style.css        # Custom CSS
│       └── js/script.js         # Custom JavaScript
├── config.py                    # Configuration
├── requirements.txt             # Python dependencies
└── run.py                       # Application entry point
```

## Installation & Setup

### 1. Clone the Repository
```bash
git clone https://github.com/yourusername/h2sqrr.git
cd h2sqrr
```

### 2. Create Virtual Environment
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/macOS
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Run Application
```bash
python run.py
```

The application will start on `http://localhost:5000`

## Default Credentials

- **Username**: admin
- **Password**: admin
- **Role**: Director

⚠️ **IMPORTANT**: Change these credentials immediately after first login in production!

## Database

The application uses SQLite database (`h2_system.db`) which is automatically created on first run. The database includes tables for:

- Users (with roles)
- Students
- Doctor Visits
- Prescriptions
- Medicines
- Stock Movements
- Assets
- Maintenance Logs
- Sick Leave Requests

## API Endpoints

### Authentication
- `GET/POST /auth/login` - User login
- `GET /auth/logout` - User logout
- `GET/POST /auth/register` - Register new user (Director only)

### Students
- `GET /students/` - List all students
- `GET/POST /students/register` - Register new student
- `GET /students/<id>` - View student profile
- `GET/POST /students/<id>/edit` - Edit student

### Health & Drug Management
- `GET /health/visits` - List doctor visits
- `GET/POST /health/visits/create` - Create new visit
- `GET /health/prescriptions` - List prescriptions
- `GET/POST /health/prescriptions/create` - Create prescription
- `POST /health/prescriptions/<id>/dispense` - Dispense prescription

### Stock Management
- `GET /stock/` - View medicine inventory
- `GET/POST /stock/add-medicine` - Add new medicine
- `GET /stock/low-stock-alerts` - View low stock items
- `GET /stock/stock-history` - View stock movements

### Asset Management
- `GET /assets/` - List all assets
- `GET/POST /assets/add` - Add new asset
- `GET /assets/<id>` - View asset details
- `GET /assets/maintenance-logs` - View maintenance history

### Sick Leave Workflow
- `GET /sickleave/` - List requests
- `GET/POST /sickleave/create` - Create new request
- `POST /sickleave/<id>/h2-approve` - H2 approval
- `POST /sickleave/<id>/warden-verify` - Warden verification
- `POST /sickleave/<id>/office-approve` - Office approval

### Dashboards
- `GET /dashboard/` - Main dashboard (role-based)

## Security Features

✓ Password hashing with Werkzeug security  
✓ Role-based access control (RBAC)  
✓ CSRF protection (via Flask-Login)  
✓ Session management  
✓ Secure cookie settings  
✓ Login required decorators  

## Configuration

Edit `config.py` to customize:
- Database URI
- Secret key
- Session settings
- Debug mode

### Environment Variables
```bash
FLASK_ENV=development          # development, testing, production
FLASK_DEBUG=True               # Enable debug mode
SECRET_KEY=your-secret-key     # Secret key for sessions
DATABASE_URL=sqlite:///h2.db   # Database URL
```

## Development

### Create an __init__.py for each blueprint directory
Each blueprint module needs an `__init__.py` file (empty or importing the blueprint).

### Adding New Features

1. Create a new blueprint module in `app/`
2. Create routes in `module/routes.py`
3. Add templates in `app/templates/module/`
4. Register blueprint in `app/__init__.py`

### Common Patterns

**RBAC Decorator:**
```python
from app.auth.utils import role_required

@app.route('/admin')
@role_required('Director', 'H2')
def admin_page():
    return render_template('admin.html')
```

**Database Query:**
```python
from app.models import Student
from extensions import db

student = Student.query.get(1)
db.session.add(student)
db.session.commit()
```

## Troubleshooting

### ImportError: No module named 'app'
- Ensure you're running from the project root directory
- Verify virtual environment is activated

### Database locked error
- Close other connections to the database
- Delete `.db-journal` file if exists

### Template not found
- Check template path matches the blueprint folder structure
- Verify template filename matches the render_template() call

## Performance Tips

1. Use database indexes for frequently queried fields
2. Implement pagination for large result sets (already done)
3. Cache frequently accessed data
4. Use database query optimization techniques
5. Monitor slow queries in development

## Future Enhancements

- [ ] Email notifications
- [ ] SMS alerts for low stock
- [ ] Report generation (PDF/Excel)
- [ ] Advanced analytics
- [ ] API documentation (Swagger/OpenAPI)
- [ ] User activity logging
- [ ] Backup & restore functionality
- [ ] Mobile app
- [ ] Two-factor authentication
- [ ] Audit trail

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit changes
4. Push to branch
5. Submit pull request

## License

This project is licensed under the MIT License - see LICENSE file for details.

## Support & Contact

For support, email: support@h2system.local

---

**Version**: 1.0.0  
**Last Updated**: January 2026  
**Status**: Production Ready
