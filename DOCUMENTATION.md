# H2 System - Complete Documentation

## Table of Contents

1. [Project Overview](#project-overview)
2. [Features](#features)
3. [Technology Stack](#technology-stack)
4. [Project Structure](#project-structure)
5. [Installation & Setup](#installation--setup)
6. [Configuration](#configuration)
7. [Database Models](#database-models)
8. [User Roles & Permissions](#user-roles--permissions)
9. [Modules & Routes](#modules--routes)
10. [Getting Started](#getting-started)
11. [Development Guide](#development-guide)
12. [Deployment](#deployment)
13. [API Reference](#api-reference)
14. [Troubleshooting](#troubleshooting)

---

## Project Overview

**H2 System** is a comprehensive Flask-based Health & Hostel Management System designed for educational institutions. It provides integrated solutions for managing health services, student records, medical inventory, hostel assets, and sick leave/food requests with multi-stage approval workflows.

The system implements role-based access control (RBAC) with distinct user roles and provides specialized dashboards tailored to each role's responsibilities.

**Version:** 1.0.0  
**Last Updated:** February 2026

---

## Features

### 1. Authentication & Role-Based Access Control (RBAC)
- Secure login system with Flask-Login
- Six distinct user roles with specific permissions:
  - **H2 (Health Team)**: Health staff managing medical operations
  - **Warden**: Hostel management and student monitoring
  - **Office**: Administrative staff handling approvals
  - **Director**: System management and oversight
  - **Doctor**: Medical staff handling visits and prescriptions
  - **Student**: Access to personal health and equipment records
- Role-specific dashboards and permission decorators
- Session management with secure cookies

### 2. Student Management
- Student profile creation and management
- Emergency contact information tracking
- Medical history records
- Allergies and current medications tracking
- Contact information and admission details
- Role-based access to student information

### 3. Health & Drug Management
- Doctor visit records with symptoms, diagnosis, and treatment
- Prescription creation, printing, and status management
- Medicine dispensing records with batch tracking
- Prescription status workflow (Prescribed → Dispensed → Completed)
- Medicine batch management with expiry tracking
- Batch dispensing history and records

### 4. Medical Stock Management
- Medicine inventory tracking with quantities
- Stock movement history logging (ADD, DISPENSE, LOSS)
- Low-stock alerts and notifications
- Supplier and cost tracking
- Expiry date management
- Stock level monitoring and reporting

### 5. Hostel Asset Management
- Asset registration with unique identification codes
- Location and condition tracking
- Asset categorization (tables, chairs, heaters, equipment, etc.)
- Maintenance log history with costs and dates
- Asset condition reports
- Maintenance request workflow

### 6. Sick Leave & Sick Food Management
- Multi-stage approval workflow:
  1. **H2 Review**: Initial health assessment
  2. **Warden Verification**: Student presence verification
  3. **Office Approval**: Administrative approval
  4. **Director Review**: Optional final review
- Request status tracking (Pending → Approved → Rejected)
- Support for both sick leave and sick food requests
- Calendar view of approved sick leave
- Student request history

### 7. Medical Equipment Issue & Rental Management
- Equipment inventory tracking (non-consumable items)
- Issue equipment to students with expected return dates
- Track equipment issuance status (Issued, Overdue, Returned)
- Equipment return processing with condition verification
- Automatic penalty calculation:
  - Overdue equipment (daily penalty rate)
  - Damaged equipment (50% of cost)
  - Lost equipment (full replacement cost)
- Penalty reports and payment tracking
- Role-based workflows for H2, Doctor, Warden, Office
- Student dashboard showing personal equipment issues

### 8. Role-Specific Dashboards
- **H2 Dashboard**: Student statistics, medicine inventory, doctor visits, equipment management overview
- **Warden Dashboard**: Asset inventory, maintenance logs, student management, equipment issues
- **Office Dashboard**: Request approvals, sick leave tracking, penalty reports, statistics
- **Director Dashboard**: System overview, user management, comprehensive statistics
- **Student Dashboard**: Personal health history, prescriptions, requests, equipment tracking
- **Doctor Dashboard**: Visit records, prescriptions managed, equipment issuance overview

---

## Technology Stack

| Component | Technology | Version |
|-----------|-----------|---------|
| Backend Framework | Flask | 3.0.0 |
| Database ORM | SQLAlchemy | 2.0.23 |
| Database | SQLite | Latest |
| Authentication | Flask-Login | 0.6.3 |
| Web Server | Werkzeug | 3.0.1 |
| Frontend Framework | Bootstrap | 5.3 |
| Frontend Languages | HTML5, CSS3, JavaScript | Latest |
| Environment Variables | python-dotenv | 1.0.0 |
| Python Version | Python | 3.8+ |

---

## Project Structure

```
h2sqrr/
├── DOCUMENTATION.md              # This file
├── README.md                      # Quick reference guide
├── PROJECT_SUMMARY.md            # Technical summary
├── QUICKSTART.md                 # Quick start guide
├── DEPLOYMENT.md                 # Deployment instructions
├── requirements.txt              # Python dependencies
├── config.py                     # Configuration classes
├── run.py                        # Application entry point
├── cli.py                        # CLI commands
│
├── app/
│   ├── __init__.py              # Flask app factory
│   ├── models.py                # Database models (10 models)
│   ├── extensions.py            # Flask extensions initialization
│   │
│   ├── auth/                    # Authentication module
│   │   ├── __init__.py
│   │   ├── routes.py            # 6 routes for login, register, user management
│   │   └── utils.py             # RBAC decorators and utilities
│   │
│   ├── students/                # Student management module
│   │   ├── __init__.py
│   │   └── routes.py            # 5 routes for student CRUD operations
│   │
│   ├── health/                  # Health & drug management module
│   │   ├── __init__.py
│   │   └── routes.py            # 7 routes for visits, prescriptions, medicines
│   │
│   ├── stock/                   # Medical stock management module
│   │   ├── __init__.py
│   │   └── routes.py            # 8 routes for inventory management
│   │
│   ├── assets/                  # Hostel asset management module
│   │   ├── __init__.py
│   │   └── routes.py            # 7 routes for asset CRUD and maintenance
│   │
│   ├── sickleave/              # Sick leave workflow module
│   │   ├── __init__.py
│   │   └── routes.py            # 8 routes for request workflow
│   │
│   ├── equipment/              # Medical equipment module
│   │   ├── __init__.py
│   │   └── routes.py            # Equipment issuance and returns
│   │
│   ├── dashboards/             # Role-based dashboards module
│   │   ├── __init__.py
│   │   └── routes.py            # 7 dashboard functions
│   │
│   ├── main/                    # Main application module
│   │   └── routes.py            # Home page and global routes
│   │
│   ├── templates/              # HTML templates
│   │   ├── base.html            # Master template
│   │   ├── index.html           # Home page
│   │   ├── 404.html             # Error page
│   │   ├── auth/                # Authentication templates
│   │   ├── students/            # Student management templates
│   │   ├── health/              # Health module templates
│   │   ├── stock/               # Stock management templates
│   │   ├── assets/              # Asset management templates
│   │   ├── sickleave/           # Sick leave templates
│   │   ├── equipment/           # Equipment management templates
│   │   └── dashboards/          # Dashboard templates (7 variants)
│   │
│   └── static/                 # Static files
│       ├── css/
│       │   └── style.css        # Custom styling
│       ├── images/
│       │   └── team/            # Team images
│       ├── js/
│       │   ├── script.js        # Utility functions
│       │   └── theme.js         # Theme switching
│       └── lib/                 # Third-party libraries
│           ├── bootstrap/
│           └── bootstrap-icons/
│
├── instance/                    # Instance-specific files (created at runtime)
│   └── h2_system.db            # SQLite database
│
├── AUDIT/                       # Audit and deployment documentation
│   ├── AUDIT_INDEX.md
│   ├── AUDIT_REPORT.md
│   ├── AUDIT_RESULTS.md
│   ├── AUDIT_SUMMARY.md
│   ├── DEPLOYMENT_READY.md
│   ├── FEATURE_CHECKLIST.md
│   └── FINAL_AUDIT_REPORT.md
│
└── __pycache__/                # Python cache (auto-generated)
```

---

## Installation & Setup

### Prerequisites
- Python 3.8 or higher
- pip (Python package manager)
- Git
- Virtual environment (recommended)

### Step 1: Clone the Repository
```bash
git clone https://github.com/nj2216/h2-system.git
cd h2sqrr
```

### Step 2: Create Virtual Environment
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Configure Environment
```bash
# Copy the environment template
cp .env.example .env

# Edit .env with your configuration
# (See Configuration section below)
```

### Step 5: Initialize Database
```bash
python run.py
```

This will:
- Create the database file (`instance/h2_system.db`)
- Create all tables
- Populate default users

---

## Configuration

### Configuration Classes (config.py)

```python
# Base Configuration
SQLALCHEMY_DATABASE_URI = 'sqlite:///h2_system.db'
SECRET_KEY = 'dev-secret-key-change-in-production'
DEBUG = False

# Session Settings
PERMANENT_SESSION_LIFETIME = 24 hours
REMEMBER_COOKIE_DURATION = 7 days
```

### Environment Variables (.env)
```env
FLASK_ENV=development          # development, testing, production
FLASK_APP=run.py
SECRET_KEY=your-secret-key-here
DATABASE_URL=sqlite:///h2_system.db
```

### Configuration Profiles

- **Development**: Full debugging, auto-reload enabled
- **Testing**: In-memory database, CSRF disabled
- **Production**: Debug disabled, secure cookies enabled

---

## Database Models

### 1. **User** Model
```
Fields: id, username, email, password_hash, first_name, last_name, role, created_at
Roles: H2, Warden, Office, Director, Doctor, Student
```

### 2. **Student** Model
```
Fields: id, admission_no, first_name, last_name, email, phone, date_of_birth, 
        gender, allergies, current_medications, department, year, room_number, 
        emergency_contact_name, emergency_contact_phone, created_at
```

### 3. **DoctorVisit** Model
```
Fields: id, student_id, doctor_id, visit_date, symptoms, diagnosis, treatment, 
        notes, created_at
```

### 4. **Prescription** Model
```
Fields: id, visit_id, medicine_id, dosage, duration, status, created_at, updated_at
Status: Prescribed, Dispensed, Completed
```

### 5. **Medicine** Model
```
Fields: id, name, description, supplier, quantity, unit_price, expiry_date, 
        created_at, updated_at
```

### 6. **MedicineBatch** Model
```
Fields: id, medicine_id, batch_number, quantity, expiry_date, created_at
```

### 7. **BatchDispensing** Model
```
Fields: id, batch_id, quantity_dispensed, dispensed_at, notes
```

### 8. **Asset** Model
```
Fields: id, code, name, category, location, condition, purchase_date, 
        purchase_cost, notes, created_at
```

### 9. **MaintenanceLog** Model
```
Fields: id, asset_id, maintenance_date, description, cost, notes, created_at
```

### 10. **SickLeaveRequest** Model
```
Fields: id, student_id, request_type, start_date, end_date, reason, 
        h2_status, warden_status, office_status, director_status, created_at
Status: Pending, Approved, Rejected
```

### 11. **MedicalEquipment** Model
```
Fields: id, name, description, quantity, unit_cost, location, created_at
```

### 12. **EquipmentIssue** Model
```
Fields: id, equipment_id, student_id, issue_date, expected_return_date, 
        actual_return_date, status, condition_on_return, penalty_amount
```

---

## User Roles & Permissions

### Role Hierarchy & Permissions

| Role | Create | Read | Update | Delete | Approve | View All |
|------|--------|------|--------|--------|---------|----------|
| **Student** | Own data | Own data | Own data | - | - | - |
| **H2** | Students | All | Students | - | Sickleave | All |
| **Doctor** | Visits | All | Visits | - | - | All |
| **Warden** | Assets | All | Assets | - | Sickleave | All |
| **Office** | - | All | - | - | All | All |
| **Director** | Users | All | Users | Users | All | All |

### Access Decorators (auth/utils.py)

```python
@h2_required          # Restrict to H2 role
@student_required     # Restrict to Student role
@doctor_required      # Restrict to Doctor role
@admin_required       # Restrict to Director role
@warden_required      # Restrict to Warden role
@office_required      # Restrict to Office role
```

---

## Modules & Routes

### 1. Authentication Module (auth/)
**Routes:**
- `POST /auth/login` - User login
- `POST /auth/logout` - User logout
- `GET /auth/register` - Registration page
- `POST /auth/register` - Create new user
- `GET /auth/users` - List all users (Director only)
- `GET /auth/users/<id>/edit` - Edit user (Director only)

### 2. Student Management Module (students/)
**Routes:**
- `GET /students/` - List all students
- `GET /students/register` - Student registration form
- `POST /students/register` - Create new student
- `GET /students/<id>/profile` - View student profile
- `GET /students/<id>/edit` - Edit student
- `POST /students/<id>/edit` - Update student
- `GET /students/<id>/health_history` - View medical history

### 3. Health Module (health/)
**Routes:**
- `GET /health/visits` - List doctor visits
- `GET /health/visits/create` - Create visit form
- `POST /health/visits/create` - Create doctor visit
- `GET /health/visits/<id>` - View visit details
- `GET /health/prescriptions` - List prescriptions
- `GET /health/prescriptions/<id>/print` - Print prescription
- `POST /health/prescriptions/<id>/dispense` - Dispense medicine

### 4. Stock Management Module (stock/)
**Routes:**
- `GET /stock/inventory` - View medicine inventory
- `GET /stock/add` - Add medicine form
- `POST /stock/add` - Add new medicine
- `GET /stock/<id>/edit` - Edit medicine
- `POST /stock/<id>/edit` - Update medicine
- `GET /stock/<id>/dispense` - Dispense medicine form
- `POST /stock/<id>/dispense` - Record medicine dispensing
- `GET /stock/batches` - View medicine batches

### 5. Asset Management Module (assets/)
**Routes:**
- `GET /assets/` - List assets
- `GET /assets/add` - Add asset form
- `POST /assets/add` - Create asset
- `GET /assets/<id>/edit` - Edit asset
- `POST /assets/<id>/edit` - Update asset
- `GET /assets/<id>/maintenance` - Log maintenance
- `POST /assets/<id>/maintenance` - Record maintenance
- `GET /assets/<id>/condition_report` - Asset condition report

### 6. Sick Leave Module (sickleave/)
**Routes:**
- `GET /sickleave/` - List requests
- `GET /sickleave/create` - Create request form
- `POST /sickleave/create` - Submit request
- `GET /sickleave/<id>` - View request
- `POST /sickleave/<id>/approve` - Approve request (by authorized role)
- `POST /sickleave/<id>/reject` - Reject request
- `GET /sickleave/calendar` - Calendar view
- `GET /sickleave/pending` - View pending requests

### 7. Equipment Module (equipment/)
**Routes:**
- `GET /equipment/` - Equipment inventory
- `GET /equipment/issue` - Issue equipment form
- `POST /equipment/issue` - Issue equipment to student
- `GET /equipment/<id>/return` - Return equipment form
- `POST /equipment/<id>/return` - Process equipment return
- `GET /equipment/penalties` - Penalty report
- `GET /equipment/student_dashboard` - Student equipment view

### 8. Dashboard Module (dashboards/)
**Routes:**
- `GET /dashboard/` - Role-based dashboard redirect
- `GET /dashboard/h2` - H2 dashboard
- `GET /dashboard/student` - Student dashboard
- `GET /dashboard/warden` - Warden dashboard
- `GET /dashboard/office` - Office dashboard
- `GET /dashboard/director` - Director dashboard
- `GET /dashboard/doctor` - Doctor dashboard

---

## Getting Started

### Step 1: Start the Application
```bash
python run.py
```

The application will be available at `http://localhost:5000`

### Step 2: Login with Default Credentials

| Username | Email | Role | Password |
|----------|-------|------|----------|
| admin | admin@h2system.local | Director | admin |
| h2 | h2@h2system.local | H2 | h2 |
| warden | warden@h2system.local | Warden | warden |
| office | office@h2system.local | Office | office |
| doctor | doctor@h2system.local | Doctor | doctor |
| student | student@h2system.local | Student | student |

### Step 3: Navigate to Your Role Dashboard
- Each user is automatically redirected to their role-specific dashboard upon login
- From the dashboard, you can access all relevant features and data

### Step 4: Create Test Data
- Use the dashboard to register new students
- Create doctor visits and prescriptions
- Add medicines and assets
- Submit sick leave requests

---

## Development Guide

### Adding a New Module

1. **Create module directory** under `app/`
   ```bash
   mkdir app/mymodule
   touch app/mymodule/__init__.py
   ```

2. **Create routes file** (`app/mymodule/routes.py`)
   ```python
   from flask import Blueprint, render_template
   from app.auth.utils import h2_required
   
   mymodule_bp = Blueprint('mymodule', __name__, url_prefix='/mymodule')
   
   @mymodule_bp.route('/')
   @h2_required
   def index():
       return render_template('mymodule/index.html')
   ```

3. **Register blueprint** in `app/__init__.py`
   ```python
   from app.mymodule import mymodule_bp
   app.register_blueprint(mymodule_bp)
   ```

4. **Create templates** in `app/templates/mymodule/`

### Adding Database Models

1. **Define model** in `app/models.py`
   ```python
   class MyModel(db.Model):
       id = db.Column(db.Integer, primary_key=True)
       name = db.Column(db.String(100), nullable=False)
   ```

2. **Create database migration** (if using Alembic)
   ```bash
   flask db migrate -m "Add MyModel"
   flask db upgrade
   ```

3. **Use in routes**
   ```python
   from app.models import MyModel
   items = MyModel.query.all()
   ```

### Common Development Tasks

**Run in Debug Mode:**
```bash
set FLASK_ENV=development  # Windows
FLASK_ENV=development      # macOS/Linux
python run.py
```

**Create New User:**
```python
from app import create_app, db
from app.models import User

app = create_app()
with app.app_context():
    user = User('username', 'email@example.com', 'password', 'H2')
    db.session.add(user)
    db.session.commit()
```

**Query Database:**
```python
from app import create_app
from app.models import Student

app = create_app()
with app.app_context():
    students = Student.query.filter_by(department='CSE').all()
```

---

## Deployment

### For detailed deployment instructions, see [DEPLOYMENT.md](DEPLOYMENT.md)

### Quick Deployment Steps

1. **Use Production Config**
   ```bash
   set FLASK_ENV=production
   set SECRET_KEY=your-strong-secret-key
   ```

2. **Use Production Server** (Gunicorn recommended)
   ```bash
   pip install gunicorn
   gunicorn -w 4 -b 0.0.0.0:5000 run:app
   ```

3. **Enable HTTPS** via reverse proxy (Nginx/Apache)

4. **Database Backup**
   ```bash
   cp instance/h2_system.db instance/h2_system.db.backup
   ```

5. **Environment Variables** in production should include:
   - `SECRET_KEY`: Strong random key (minimum 32 characters)
   - `DATABASE_URL`: Production database connection string
   - Any API keys or secrets

---

## API Reference

### Authentication

**Login**
```http
POST /auth/login
Content-Type: application/x-www-form-urlencoded

username=user&password=pass
```

**Response:**
- Success: Redirect to dashboard
- Failure: Redirect to login with error

### Students API

**List Students**
```http
GET /students/
Authorization: Required
```

**Get Student Profile**
```http
GET /students/<student_id>/profile
Authorization: Required
```

**Create Student**
```http
POST /students/register
Content-Type: application/x-www-form-urlencoded

admission_no=SR001&first_name=John&last_name=Doe...
Authorization: H2/Doctor/Admin
```

### Health API

**Create Doctor Visit**
```http
POST /health/visits/create
Content-Type: application/x-www-form-urlencoded

student_id=1&symptoms=Fever&diagnosis=Flu...
Authorization: Doctor
```

**Create Prescription**
```http
POST /health/prescriptions/create
Content-Type: application/x-www-form-urlencoded

visit_id=1&medicine_id=1&dosage=2 tablets...
Authorization: Doctor
```

### Stock API

**Add Medicine**
```http
POST /stock/add
Content-Type: application/x-www-form-urlencoded

name=Aspirin&supplier=Company&quantity=100...
Authorization: H2/Admin
```

**View Inventory**
```http
GET /stock/inventory
Authorization: Required
```

### Sick Leave API

**Submit Request**
```http
POST /sickleave/create
Content-Type: application/x-www-form-urlencoded

student_id=1&start_date=2026-02-06&reason=...
Authorization: Student
```

**Approve Request**
```http
POST /sickleave/<request_id>/approve
Content-Type: application/x-www-form-urlencoded

status=approved
Authorization: H2/Warden/Office/Director
```

---

## Troubleshooting

### Common Issues

**1. Database Error: "No such table"**
- **Cause**: Database not initialized
- **Solution**: Run `python run.py` to create tables

**2. Login fails for default users**
- **Cause**: Password may have been changed
- **Solution**: Reset by running `python run.py` again

**3. Module import errors**
- **Cause**: Missing dependencies
- **Solution**: Run `pip install -r requirements.txt`

**4. Port already in use (Port 5000)**
- **Solution**: Specify different port: `python run.py --port 5001`

**5. Static files not loading**
- **Cause**: Debug mode disabled
- **Solution**: Use development config or manually serve static files

**6. Session expires too quickly**
- **Adjust**: `PERMANENT_SESSION_LIFETIME` in config.py

**7. Database locked error**
- **Cause**: Multiple processes accessing database
- **Solution**: Use production database (PostgreSQL) instead of SQLite

### Debug Mode

Enable detailed error messages:
```bash
set FLASK_ENV=development
set FLASK_DEBUG=1
python run.py
```

### Checking Logs

Flask logs are printed to console. To save to file:
```python
import logging
logging.basicConfig(filename='app.log', level=logging.DEBUG)
```

### Database Issues

**Backup Database:**
```bash
copy instance\h2_system.db instance\h2_system.db.backup
```

**Reset Database:**
```bash
del instance\h2_system.db
python run.py
```

---

## Support & Contribution

For issues or questions:
1. Check this documentation
2. Review project files and comments
3. Check error logs
4. Create an issue with detailed information

---

## License

This project is provided as-is for educational and institutional use.

---

**Last Updated:** February 2026  
**Status:** Production Ready
