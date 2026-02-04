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
    """Medicine prescription model - contains multiple medicines"""
    __tablename__ = 'prescriptions'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    visit_id = db.Column(db.Integer, db.ForeignKey('doctor_visits.id'))
    created_by_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    notes = db.Column(db.Text)  # General prescription notes
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    items = db.relationship('PrescriptionItem', backref='prescription', cascade='all, delete-orphan')
    
    @property
    def overall_status(self):
        """Get overall prescription status based on items"""
        if not self.items:
            return 'EMPTY'
        
        statuses = {item.status for item in self.items}
        
        if statuses == {'DISPENSED'}:
            return 'DISPENSED'
        elif 'OUT_OF_STOCK' in statuses and len(statuses) == 1:
            return 'OUT_OF_STOCK'
        elif 'PENDING' in statuses:
            return 'PENDING'
        elif 'PARTIAL' in statuses or (statuses - {'DISPENSED'}):
            return 'PARTIAL'
        else:
            return 'PENDING'
    
    def __repr__(self):
        return f'<Prescription {self.id} - Student {self.student_id} ({self.overall_status})>'


class PrescriptionItem(db.Model):
    """Individual medicine item in a prescription"""
    __tablename__ = 'prescription_items'
    
    id = db.Column(db.Integer, primary_key=True)
    prescription_id = db.Column(db.Integer, db.ForeignKey('prescriptions.id'), nullable=False)
    medicine_id = db.Column(db.Integer, db.ForeignKey('medicines.id'))  # Optional - null if using dummy medicine
    dummy_medicine_id = db.Column(db.Integer, db.ForeignKey('dummy_medicines.id'))  # For out-of-stock medicines
    dosage = db.Column(db.String(100))  # e.g., "500mg"
    frequency = db.Column(db.String(100))  # e.g., "3 times daily"
    duration_days = db.Column(db.Integer)
    quantity_prescribed = db.Column(db.Integer, default=1)
    quantity_dispensed = db.Column(db.Integer, default=0)
    instructions = db.Column(db.Text)
    status = db.Column(db.String(20), default='PENDING')  # PENDING, PARTIAL, DISPENSED, OUT_OF_STOCK
    dispensed_date = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    medicine = db.relationship('Medicine', backref='prescription_items')
    dummy_medicine = db.relationship('DummyMedicine', backref='prescription_items')
    
    def get_medicine(self):
        """Get either real or dummy medicine"""
        return self.medicine if self.medicine else self.dummy_medicine
    
    def __repr__(self):
        med = self.get_medicine()
        med_name = med.name if med else "Unknown"
        return f'<PrescriptionItem {med_name} ({self.status})>'


class DummyMedicine(db.Model):
    """Placeholder for medicines not in inventory (for prescribing out-of-stock medicines)"""
    __tablename__ = 'dummy_medicines'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False, index=True)
    generic_name = db.Column(db.String(255))
    dosage = db.Column(db.String(100))
    unit = db.Column(db.String(50))  # tablets, bottles, etc.
    supplier = db.Column(db.String(255))
    estimated_cost = db.Column(db.Float)
    notes = db.Column(db.Text)  # Prescription notes mentioning this dummy medicine
    replaced_by_id = db.Column(db.Integer, db.ForeignKey('medicines.id'))  # Links to real medicine after replacement
    is_replaced = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    replaced_by = db.relationship('Medicine', backref='replaced_dummy_medicines')
    
    def __repr__(self):
        return f'<DummyMedicine {self.name} (Replaced: {self.is_replaced})>'


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
    batches = db.relationship('MedicineBatch', backref='medicine', cascade='all, delete-orphan')
    
    @property
    def is_low_stock(self):
        """Check if medicine is below minimum stock level (non-expired batches only)"""
        return self.total_batch_quantity <= self.min_stock_level
    
    @property
    def total_batch_quantity(self):
        """Calculate total available quantity across all NON-EXPIRED batches"""
        return sum(batch.available_quantity for batch in self.batches if not batch.is_expired)
    
    def get_fefo_batch(self):
        """Get the oldest NON-EXPIRED batch with available stock (FEFO principle)"""
        # Filter batches: must have available stock AND not be expired
        available_batches = [b for b in self.batches if b.available_quantity > 0 and not b.is_expired]
        if available_batches:
            # Sort by expiry date (oldest first)
            return sorted(available_batches, key=lambda b: (b.expiry_date or datetime.max.date(), b.created_at))[0]
        return None
    
    def __repr__(self):
        return f'<Medicine {self.name}>'


class MedicineBatch(db.Model):
    """Track individual batches of medicine with shelf location and expiry"""
    __tablename__ = 'medicine_batches'
    
    id = db.Column(db.Integer, primary_key=True)
    medicine_id = db.Column(db.Integer, db.ForeignKey('medicines.id'), nullable=False, index=True)
    batch_number = db.Column(db.String(100), nullable=False, index=True)  # Manufacturer batch number
    quantity = db.Column(db.Integer, nullable=False)  # Total quantity in batch
    available_quantity = db.Column(db.Integer, nullable=False)  # Remaining available quantity
    expiry_date = db.Column(db.Date, nullable=False, index=True)
    shelf_location = db.Column(db.String(100), nullable=False)  # e.g., "Shelf A1", "Cold Storage 2"
    cost_per_unit = db.Column(db.Float)
    date_added = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    dispensings = db.relationship('BatchDispensing', backref='batch', cascade='all, delete-orphan')
    
    @property
    def is_expired(self):
        """Check if batch is expired"""
        return self.expiry_date <= datetime.now().date()
    
    @property
    def days_to_expiry(self):
        """Calculate days remaining until expiry"""
        delta = self.expiry_date - datetime.now().date()
        return delta.days
    
    def __repr__(self):
        return f'<MedicineBatch {self.batch_number} - {self.available_quantity}/{self.quantity}>'


class BatchDispensing(db.Model):
    """Record of batch used during medicine dispensing for traceability"""
    __tablename__ = 'batch_dispensings'
    
    id = db.Column(db.Integer, primary_key=True)
    prescription_item_id = db.Column(db.Integer, db.ForeignKey('prescription_items.id'), nullable=False, index=True)
    batch_id = db.Column(db.Integer, db.ForeignKey('medicine_batches.id'), nullable=False, index=True)
    quantity_dispensed = db.Column(db.Integer, nullable=False)
    dispensed_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    dispensed_at = db.Column(db.DateTime, default=datetime.utcnow)
    notes = db.Column(db.Text)
    
    # Relationships
    prescription_item = db.relationship('PrescriptionItem', backref='batch_dispensings')
    dispensed_by = db.relationship('User', backref='batch_dispensings')
    
    def __repr__(self):
        return f'<BatchDispensing Batch#{self.batch_id} - {self.quantity_dispensed} units>'


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


class MedicalEquipment(db.Model):
    """Medical equipment inventory (non-consumable items)"""
    __tablename__ = 'medical_equipments'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)  # Crepe Band, Hot Pack, Ice Pack, etc.
    equipment_code = db.Column(db.String(50), unique=True, nullable=False, index=True)
    category = db.Column(db.String(100))  # Support, Thermal, Device, etc.
    description = db.Column(db.Text)
    quantity_available = db.Column(db.Integer, default=0)
    quantity_issued = db.Column(db.Integer, default=0)
    quantity_damaged = db.Column(db.Integer, default=0)
    quantity_lost = db.Column(db.Integer, default=0)
    unit_cost = db.Column(db.Float)
    location = db.Column(db.String(100))  # Storage location
    daily_penalty = db.Column(db.Float, default=0.0)  # Penalty per day if not returned on time
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    issues = db.relationship('EquipmentIssue', backref='equipment', cascade='all, delete-orphan')
    
    @property
    def total_quantity(self):
        """Total equipment quantity"""
        return self.quantity_available + self.quantity_issued + self.quantity_damaged + self.quantity_lost
    
    def __repr__(self):
        return f'<MedicalEquipment {self.equipment_code} - {self.name}>'


class EquipmentIssue(db.Model):
    """Equipment issue/rental record"""
    __tablename__ = 'equipment_issues'
    
    id = db.Column(db.Integer, primary_key=True)
    equipment_id = db.Column(db.Integer, db.ForeignKey('medical_equipments.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    issued_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)  # H2 or Doctor
    verified_by_id = db.Column(db.Integer, db.ForeignKey('users.id'))  # H2 who verified return
    
    # Issue details
    quantity = db.Column(db.Integer, default=1, nullable=False)
    issued_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    expected_return_date = db.Column(db.DateTime, nullable=False)
    
    # Return details
    actual_return_date = db.Column(db.DateTime)
    return_condition = db.Column(db.String(50))  # 'normal', 'damaged', 'lost'
    return_notes = db.Column(db.Text)
    
    # Penalty tracking
    is_overdue = db.Column(db.Boolean, default=False)
    days_overdue = db.Column(db.Integer, default=0)
    penalty_amount = db.Column(db.Float, default=0.0)
    penalty_paid = db.Column(db.Boolean, default=False)
    penalty_paid_date = db.Column(db.DateTime)
    
    status = db.Column(db.String(50), default='Issued')  # Issued, Overdue, Returned, Defaulted
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    student = db.relationship('Student', backref='equipment_issues')
    issued_by = db.relationship('User', foreign_keys=[issued_by_id], backref='equipment_issues_issued')
    verified_by = db.relationship('User', foreign_keys=[verified_by_id], backref='equipment_issues_verified')
    
    def mark_as_overdue(self):
        """Mark issue as overdue and calculate penalty"""
        from datetime import datetime, timedelta
        
        if not self.actual_return_date and self.expected_return_date < datetime.utcnow():
            self.is_overdue = True
            self.status = 'Overdue'
            
            days_over = (datetime.utcnow() - self.expected_return_date).days
            self.days_overdue = max(1, days_over)  # At least 1 day
            
            equipment = MedicalEquipment.query.get(self.equipment_id)
            self.penalty_amount = self.days_overdue * equipment.daily_penalty * self.quantity
            
            db.session.commit()
    
    def process_return(self, condition, notes=''):
        """Process equipment return"""
        from datetime import datetime
        
        self.actual_return_date = datetime.utcnow()
        self.return_condition = condition
        self.return_notes = notes
        
        equipment = MedicalEquipment.query.get(self.equipment_id)
        
        # Update equipment quantities
        equipment.quantity_issued -= self.quantity
        
        if condition == 'normal':
            equipment.quantity_available += self.quantity
            self.status = 'Returned'
        elif condition == 'damaged':
            equipment.quantity_damaged += self.quantity
            self.status = 'Returned'
            self.penalty_amount = equipment.unit_cost * self.quantity * 0.5  # 50% penalty for damage
        elif condition == 'lost':
            equipment.quantity_lost += self.quantity
            self.status = 'Returned'
            self.penalty_amount = equipment.unit_cost * self.quantity  # Full replacement cost
        
        # Calculate overdue penalty
        if self.actual_return_date > self.expected_return_date:
            days_over = (self.actual_return_date - self.expected_return_date).days
            days_over = max(1, days_over)
            self.penalty_amount += days_over * equipment.daily_penalty * self.quantity
        
        self.is_overdue = False
        db.session.commit()
    
    def __repr__(self):
        return f'<EquipmentIssue {self.id} - Student {self.student_id}>'
