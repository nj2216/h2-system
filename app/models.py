"""
Database models for H2 System
"""
from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from .extensions import db, login_manager


class User(UserMixin, db.Model):
    """User model with role-based access control"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(120), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    first_name = db.Column(db.String(120))
    last_name = db.Column(db.String(120))
    role = db.Column(db.String(50), nullable=False)  # H2, Warden, Office, Director, Doctor
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    student = db.relationship('Student', uselist=False, backref='user', cascade='all, delete-orphan')
    doctor_visits = db.relationship('DoctorVisit', backref='doctor', foreign_keys='DoctorVisit.doctor_id')
    prescriptions = db.relationship('Prescription', backref='created_by_user', foreign_keys='Prescription.created_by_id')
    sickleave_requests = db.relationship('SickLeaveRequest', backref='creator', foreign_keys='SickLeaveRequest.created_by_id')
    stock_movements = db.relationship('StockMovement', backref='user')
    
    def set_password(self, password):
        """Hash and set password"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Verify password"""
        return check_password_hash(self.password_hash, password)
    
    def has_role(self, *roles):
        """Check if user has any of the given roles"""
        return self.role in roles
    
    def __repr__(self):
        return f'<User {self.username}>'


class Student(db.Model):
    """Student profile model"""
    __tablename__ = 'students'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True)
    roll_number = db.Column(db.String(50), unique=True, nullable=False, index=True)
    date_of_birth = db.Column(db.Date)
    gender = db.Column(db.String(10))
    blood_group = db.Column(db.String(10))
    hostel_room = db.Column(db.String(20))
    phone_number = db.Column(db.String(20))
    
    # Emergency contact
    emergency_contact_name = db.Column(db.String(120))
    emergency_contact_phone = db.Column(db.String(20))
    emergency_contact_relation = db.Column(db.String(50))
    
    # Medical history
    allergies = db.Column(db.Text)
    medical_conditions = db.Column(db.Text)
    current_medications = db.Column(db.Text)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    doctor_visits = db.relationship('DoctorVisit', backref='student', cascade='all, delete-orphan')
    prescriptions = db.relationship('Prescription', backref='student', cascade='all, delete-orphan')
    sickleave_requests = db.relationship('SickLeaveRequest', backref='student', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Student {self.roll_number}>'


class DoctorVisit(db.Model):
    """Doctor visit records"""
    __tablename__ = 'doctor_visits'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    visit_date = db.Column(db.DateTime, default=datetime.utcnow)
    symptoms = db.Column(db.Text)
    diagnosis = db.Column(db.Text)
    treatment = db.Column(db.Text)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    prescriptions = db.relationship('Prescription', backref='visit', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<DoctorVisit {self.id} - {self.visit_date}>'


class Prescription(db.Model):
    """Medicine prescription model"""
    __tablename__ = 'prescriptions'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    visit_id = db.Column(db.Integer, db.ForeignKey('doctor_visits.id'))
    created_by_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    medicine_name = db.Column(db.String(255), nullable=False)
    dosage = db.Column(db.String(100))  # e.g., "500mg"
    frequency = db.Column(db.String(100))  # e.g., "3 times daily"
    duration_days = db.Column(db.Integer)
    quantity_prescribed = db.Column(db.Integer, default=1)  # Number of units prescribed
    instructions = db.Column(db.Text)
    is_dispensed = db.Column(db.Boolean, default=False)
    dispensed_date = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Prescription {self.medicine_name} - {self.student_id}>'


class Medicine(db.Model):
    """Medicine inventory model"""
    __tablename__ = 'medicines'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), unique=True, nullable=False, index=True)
    generic_name = db.Column(db.String(255))
    dosage = db.Column(db.String(100))
    quantity = db.Column(db.Integer, default=0)
    min_stock_level = db.Column(db.Integer, default=10)
    unit = db.Column(db.String(50))  # tablets, bottles, etc.
    expiry_date = db.Column(db.Date)
    supplier = db.Column(db.String(255))
    cost_per_unit = db.Column(db.Float)
    location = db.Column(db.String(100))  # Storage location
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    stock_movements = db.relationship('StockMovement', backref='medicine', cascade='all, delete-orphan')
    
    @property
    def is_low_stock(self):
        """Check if medicine is below minimum stock level"""
        return self.quantity <= self.min_stock_level
    
    def __repr__(self):
        return f'<Medicine {self.name}>'


class StockMovement(db.Model):
    """Track medicine stock movements (addition/removal)"""
    __tablename__ = 'stock_movements'
    
    id = db.Column(db.Integer, primary_key=True)
    medicine_id = db.Column(db.Integer, db.ForeignKey('medicines.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    movement_type = db.Column(db.String(20), nullable=False)  # 'ADD', 'DISPENSE', 'LOSS'
    quantity = db.Column(db.Integer, nullable=False)
    reason = db.Column(db.Text)
    reference_id = db.Column(db.Integer)  # prescription_id or purchase_order_id
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<StockMovement {self.movement_type} - {self.medicine_id}>'


class Asset(db.Model):
    """Hostel asset tracking"""
    __tablename__ = 'assets'
    
    id = db.Column(db.Integer, primary_key=True)
    asset_code = db.Column(db.String(50), unique=True, nullable=False, index=True)
    name = db.Column(db.String(255), nullable=False)
    category = db.Column(db.String(100))  # Table, Chair, Heater, Bed, etc.
    description = db.Column(db.Text)
    location = db.Column(db.String(255))  # Room number or area
    quantity = db.Column(db.Integer, default=1)
    condition = db.Column(db.String(50), default='Good')  # Good, Fair, Poor, Damaged
    purchase_date = db.Column(db.Date)
    cost = db.Column(db.Float)
    warranty_expiry = db.Column(db.Date)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    maintenance_logs = db.relationship('MaintenanceLog', backref='asset', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Asset {self.asset_code} - {self.name}>'


class MaintenanceLog(db.Model):
    """Asset maintenance history"""
    __tablename__ = 'maintenance_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    asset_id = db.Column(db.Integer, db.ForeignKey('assets.id'), nullable=False)
    maintenance_date = db.Column(db.DateTime, default=datetime.utcnow)
    issue_description = db.Column(db.Text)
    action_taken = db.Column(db.Text)
    cost = db.Column(db.Float)
    status = db.Column(db.String(50))  # Pending, Completed, In Progress
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<MaintenanceLog {self.asset_id} - {self.maintenance_date}>'


class SickLeaveRequest(db.Model):
    """Sick leave and sick food request workflow"""
    __tablename__ = 'sickleave_requests'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    created_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Request details
    request_type = db.Column(db.String(50), nullable=False)  # 'sick_leave', 'sick_food'
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    reason = db.Column(db.Text)
    medical_certificate = db.Column(db.String(255))  # File path
    
    # Workflow status
    h2_status = db.Column(db.String(50), default='Pending')  # Pending, Approved, Rejected
    h2_notes = db.Column(db.Text)
    h2_approved_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    h2_approved_date = db.Column(db.DateTime)
    
    warden_status = db.Column(db.String(50), default='Pending')  # Pending, Approved, Rejected
    warden_notes = db.Column(db.Text)
    warden_verified_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    warden_verified_date = db.Column(db.DateTime)
    
    office_status = db.Column(db.String(50), default='Pending')  # Pending, Approved, Rejected
    office_notes = db.Column(db.Text)
    office_approved_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    office_approved_date = db.Column(db.DateTime)
    
    director_status = db.Column(db.String(50), default='Pending')  # Pending, Approved, Rejected, N/A
    director_notes = db.Column(db.Text)
    director_approved_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    director_approved_date = db.Column(db.DateTime)
    
    overall_status = db.Column(db.String(50), default='Pending')  # Pending, Approved, Rejected
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Foreign keys for approvers
    __table_args__ = (
        db.ForeignKeyConstraint(['h2_approved_by'], ['users.id']),
        db.ForeignKeyConstraint(['warden_verified_by'], ['users.id']),
        db.ForeignKeyConstraint(['office_approved_by'], ['users.id']),
        db.ForeignKeyConstraint(['director_approved_by'], ['users.id']),
    )
    
    def get_overall_status(self):
        """Calculate overall approval status"""
        if self.h2_status == 'Rejected' or self.warden_status == 'Rejected' or self.office_status == 'Rejected':
            return 'Rejected'
        
        if (self.h2_status == 'Approved' and 
            self.warden_status == 'Approved' and 
            self.office_status == 'Approved'):
            return 'Approved'
        
        return 'Pending'
    
    def __repr__(self):
        return f'<SickLeaveRequest {self.id} - {self.request_type}>'
