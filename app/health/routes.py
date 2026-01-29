"""
Health and drug management blueprint routes
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import current_user, login_required
from datetime import datetime
from ..extensions import db
from app.models import Student, DoctorVisit, Prescription, Medicine, StockMovement, User
from app.auth.utils import role_required

health_bp = Blueprint('health', __name__, template_folder='../templates/health')


@health_bp.route('/visits')
@role_required('H2', 'Warden', 'Director', 'Doctor')
def visits_list():
    """List all doctor visits"""
    page = request.args.get('page', 1, type=int)
    student_id = request.args.get('student_id', type=int)
    
    query = DoctorVisit.query
    
    if student_id:
        query = query.filter_by(student_id=student_id)
    
    visits = query.order_by(DoctorVisit.visit_date.desc()).paginate(page=page, per_page=20)
    
    return render_template('health/visits_list.html', visits=visits)


@health_bp.route('/visits/create', methods=['GET', 'POST'])
@role_required('H2', 'Doctor')
def create_visit():
    """Create a new doctor visit record"""
    if request.method == 'POST':
        student_id = request.form.get('student_id', type=int)
        doctor_id = request.form.get('doctor_id', type=int) if current_user.role == 'H2' else current_user.id
        symptoms = request.form.get('symptoms')
        diagnosis = request.form.get('diagnosis')
        treatment = request.form.get('treatment')
        notes = request.form.get('notes')
        
        student = Student.query.get_or_404(student_id)
        
        visit = DoctorVisit(
            student_id=student_id,
            doctor_id=doctor_id,
            symptoms=symptoms,
            diagnosis=diagnosis,
            treatment=treatment,
            notes=notes
        )
        
        db.session.add(visit)
        db.session.commit()
        
        flash('Doctor visit recorded successfully.', 'success')
        return redirect(url_for('health.view_visit', visit_id=visit.id))
    
    # Get list of students and doctors for form
    students = Student.query.all()
    doctors = User.query.filter_by(role='Doctor').all()
    
    return render_template('health/create_visit.html', students=students, doctors=doctors)


@health_bp.route('/visits/<int:visit_id>')
@role_required('H2', 'Warden', 'Director', 'Doctor', 'Student')
def view_visit(visit_id):
    """View doctor visit details"""
    visit = DoctorVisit.query.get_or_404(visit_id)
    
    # Check access
    if current_user.role == 'Student' and current_user.id != visit.student.user_id:
        flash('You do not have permission to view this record.', 'danger')
        return redirect(url_for('dashboards.dashboard'))
    
    prescriptions = visit.prescriptions
    
    return render_template('health/view_visit.html', visit=visit, prescriptions=prescriptions)


@health_bp.route('/visits/<int:visit_id>/edit', methods=['GET', 'POST'])
@role_required('H2', 'Doctor')
def edit_visit(visit_id):
    """Edit doctor visit record"""
    visit = DoctorVisit.query.get_or_404(visit_id)
    
    if request.method == 'POST':
        visit.symptoms = request.form.get('symptoms')
        visit.diagnosis = request.form.get('diagnosis')
        visit.treatment = request.form.get('treatment')
        visit.notes = request.form.get('notes')
        
        db.session.commit()
        flash('Doctor visit updated successfully.', 'success')
        return redirect(url_for('health.view_visit', visit_id=visit.id))
    
    return render_template('health/edit_visit.html', visit=visit)


@health_bp.route('/prescriptions')
@role_required('H2', 'Warden', 'Director', 'Doctor')
def prescriptions_list():
    """List all prescriptions"""
    page = request.args.get('page', 1, type=int)
    student_id = request.args.get('student_id', type=int)
    undispensed = request.args.get('undispensed', 'false').lower() == 'true'
    
    query = Prescription.query
    
    if student_id:
        query = query.filter_by(student_id=student_id)
    
    if undispensed:
        query = query.filter_by(is_dispensed=False)
    
    prescriptions = query.order_by(Prescription.created_at.desc()).paginate(page=page, per_page=20)
    
    return render_template('health/prescriptions_list.html', prescriptions=prescriptions)


@health_bp.route('/prescriptions/create', methods=['GET', 'POST'])
@role_required('H2', 'Doctor')
def create_prescription():
    """Create a new prescription"""
    if request.method == 'POST':
        student_id = request.form.get('student_id', type=int)
        visit_id = request.form.get('visit_id', type=int)
        medicine_id = request.form.get('medicine_id', type=int)
        dosage = request.form.get('dosage')
        frequency = request.form.get('frequency')
        duration_days = request.form.get('duration_days', type=int)
        quantity_prescribed = request.form.get('quantity_prescribed', type=int)
        instructions = request.form.get('instructions')
        
        student = Student.query.get_or_404(student_id)
        
        # Get medicine from inventory
        medicine = Medicine.query.get_or_404(medicine_id)
        
        if not quantity_prescribed or quantity_prescribed < 1:
            flash('Quantity must be calculated from frequency and duration.', 'danger')
            return redirect(url_for('health.create_prescription'))
        
        if medicine.quantity < quantity_prescribed:
            flash(f'Insufficient stock for {medicine.name}. Available: {medicine.quantity}, Required: {quantity_prescribed}', 'danger')
            return redirect(url_for('health.create_prescription'))
        
        # Map frequency value to readable text
        frequency_map = {
            '1': '1 time daily',
            '2': '2 times daily',
            '3': '3 times daily',
            '4': '4 times daily',
            '1/2': 'Every 12 hours (2 times daily)',
            '1/3': 'Every 8 hours (3 times daily)',
            '1/6': 'Every 6 hours (4 times daily)',
            '0.5': 'Once in 2 days'
        }
        frequency_text = frequency_map.get(frequency, frequency)
        
        prescription = Prescription(
            student_id=student_id,
            visit_id=visit_id if visit_id else None,
            created_by_id=current_user.id,
            medicine_name=medicine.name,
            dosage=dosage,
            frequency=frequency_text,
            duration_days=duration_days,
            quantity_prescribed=quantity_prescribed,
            instructions=instructions
        )
        
        db.session.add(prescription)
        db.session.commit()
        
        flash(f'Prescription created: {medicine.name} - {quantity_prescribed} units ({frequency_text} for {duration_days} days).', 'success')
        return redirect(url_for('health.view_prescription', prescription_id=prescription.id))
    
    students = Student.query.all()
    medicines = Medicine.query.filter(Medicine.quantity > 0).all()
    
    return render_template('health/create_prescription.html', students=students, medicines=medicines)


@health_bp.route('/prescriptions/<int:prescription_id>/dispense', methods=['POST'])
@role_required('H2')
def dispense_prescription(prescription_id):
    """Mark prescription as dispensed and reduce stock"""
    prescription = Prescription.query.get_or_404(prescription_id)
    
    if prescription.is_dispensed:
        flash('This prescription has already been dispensed.', 'warning')
        return redirect(url_for('health.view_prescription', prescription_id=prescription.id))
    
    # Find medicine and verify stock
    medicine = Medicine.query.filter_by(name=prescription.medicine_name).first()
    if not medicine:
        flash(f'Medicine "{prescription.medicine_name}" not found in inventory.', 'warning')
        return redirect(url_for('health.view_prescription', prescription_id=prescription.id))
    
    # Check stock before dispensing
    qty_to_dispense = prescription.quantity_prescribed
    if medicine.quantity < qty_to_dispense:
        flash(f'Insufficient stock to dispense. Available: {medicine.quantity}, Required: {qty_to_dispense}', 'danger')
        return redirect(url_for('health.view_prescription', prescription_id=prescription.id))
    
    # Mark as dispensed
    prescription.is_dispensed = True
    prescription.dispensed_date = datetime.utcnow()
    
    # Reduce stock by the prescribed quantity
    medicine.quantity -= qty_to_dispense
    
    # Record the stock movement
    stock_movement = StockMovement(
        medicine_id=medicine.id,
        user_id=current_user.id,
        movement_type='DISPENSE',
        quantity=qty_to_dispense,
        reason=f'Prescription dispensed to {prescription.student.roll_number} - {qty_to_dispense} units',
        reference_id=prescription.id
    )
    db.session.add(stock_movement)
    db.session.commit()
    
    flash(f'Prescription dispensed successfully. Stock reduced by {qty_to_dispense} units.', 'success')
    return redirect(url_for('health.view_prescription', prescription_id=prescription.id))


@health_bp.route('/prescriptions/<int:prescription_id>')
@role_required('H2', 'Warden', 'Director', 'Doctor', 'Student')
def view_prescription(prescription_id):
    """View prescription details"""
    prescription = Prescription.query.get_or_404(prescription_id)
    
    if current_user.role == 'Student' and current_user.id != prescription.student.user_id:
        flash('You do not have permission to view this record.', 'danger')
        return redirect(url_for('dashboards.dashboard'))
    
    return render_template('health/view_prescription.html', prescription=prescription)
