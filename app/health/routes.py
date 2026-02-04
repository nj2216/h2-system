"""
Health and drug management blueprint routes
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import current_user, login_required
from datetime import datetime
from ..extensions import db
from app.models import Student, DoctorVisit, Prescription, PrescriptionItem, Medicine, DummyMedicine, StockMovement, User
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


@health_bp.route('/visits/<int:visit_id>/prescribe', methods=['GET', 'POST'])
@role_required('H2', 'Doctor')
def prescribe_during_visit(visit_id):
    """Create prescription directly during a doctor visit"""
    visit = DoctorVisit.query.get_or_404(visit_id)
    
    if request.method == 'POST':
        notes = request.form.get('notes', '').strip()
        medicine_ids = request.form.getlist('medicine_id')
        
        if not medicine_ids or len(medicine_ids) == 0:
            flash('Please add at least one medicine to the prescription.', 'danger')
            return redirect(url_for('health.prescribe_during_visit', visit_id=visit_id))
        
        # Create prescription linked to visit
        prescription = Prescription(
            student_id=visit.student_id,
            visit_id=visit_id,
            created_by_id=current_user.id,
            notes=notes
        )
        db.session.add(prescription)
        db.session.flush()
        
        # Frequency mapping
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
        
        item_count = 0
        for idx, medicine_id in enumerate(medicine_ids):
            if not medicine_id:
                continue
            
            # Get medicine
            medicine = Medicine.query.get(medicine_id)
            if not medicine:
                continue
            
            # Get form data for this medicine
            dosage = request.form.getlist('dosage[]')[idx] if idx < len(request.form.getlist('dosage[]')) else ''
            frequency = request.form.getlist('frequency[]')[idx] if idx < len(request.form.getlist('frequency[]')) else ''
            duration_days = request.form.getlist('duration_days[]')[idx] if idx < len(request.form.getlist('duration_days[]')) else '0'
            quantity = request.form.getlist('quantity_prescribed[]')[idx] if idx < len(request.form.getlist('quantity_prescribed[]')) else '1'
            instructions = request.form.getlist('instructions[]')[idx] if idx < len(request.form.getlist('instructions[]')) else ''
            
            try:
                duration_days = int(duration_days) if duration_days else 0
                quantity = int(quantity) if quantity else 1
            except ValueError:
                continue
            
            frequency_text = frequency_map.get(frequency, frequency)
            
            # Check if medicine is in stock
            if medicine.quantity >= quantity:
                # Create item with real medicine
                item = PrescriptionItem(
                    prescription_id=prescription.id,
                    medicine_id=medicine_id,
                    dosage=dosage.strip() or None,
                    frequency=frequency_text.strip() or None,
                    duration_days=duration_days,
                    quantity_prescribed=quantity,
                    instructions=instructions.strip() or None,
                    status='PENDING'
                )
            else:
                # Create dummy medicine for out-of-stock
                dummy = DummyMedicine(
                    name=medicine.name,
                    generic_name=medicine.generic_name,
                    dosage=medicine.dosage,
                    unit=medicine.unit,
                    supplier=medicine.supplier,
                    estimated_cost=medicine.cost_per_unit,
                    notes=f'Prescribed during visit - out of stock (available: {medicine.quantity})'
                )
                db.session.add(dummy)
                db.session.flush()
                
                item = PrescriptionItem(
                    prescription_id=prescription.id,
                    dummy_medicine_id=dummy.id,
                    dosage=dosage.strip() or None,
                    frequency=frequency_text.strip() or None,
                    duration_days=duration_days,
                    quantity_prescribed=quantity,
                    instructions=instructions.strip() or None,
                    status='OUT_OF_STOCK'
                )
            
            db.session.add(item)
            item_count += 1
        
        if item_count == 0:
            db.session.rollback()
            flash('No valid medicines were added to the prescription.', 'danger')
            return redirect(url_for('health.prescribe_during_visit', visit_id=visit_id))
        
        db.session.commit()
        flash(f'Prescription created with {item_count} medicine(s) during this visit.', 'success')
        return redirect(url_for('health.view_visit', visit_id=visit_id))
    
    medicines = Medicine.query.all()
    return render_template('health/prescribe_during_visit.html', visit=visit, medicines=medicines)


@health_bp.route('/prescriptions')
@role_required('H2', 'Warden', 'Director', 'Doctor')
def prescriptions_list():
    """List all prescriptions"""
    page = request.args.get('page', 1, type=int)
    student_id = request.args.get('student_id', type=int)
    status = request.args.get('status', '')
    
    query = Prescription.query
    
    if student_id:
        query = query.filter_by(student_id=student_id)
    
    if status:
        query = query.filter_by(status=status)
    
    prescriptions = query.order_by(Prescription.created_at.desc()).paginate(page=page, per_page=20)
    
    return render_template('health/prescriptions_list.html', prescriptions=prescriptions)


@health_bp.route('/prescriptions/create', methods=['GET', 'POST'])
@role_required('H2', 'Doctor')
def create_prescription():
    """Create a new prescription with multiple medicines"""
    if request.method == 'POST':
        student_id = request.form.get('student_id', type=int)
        visit_id = request.form.get('visit_id', type=int)
        notes = request.form.get('notes', '').strip()
        
        student = Student.query.get_or_404(student_id)
        
        # Get medicine IDs and quantities from form
        medicine_ids = request.form.getlist('medicine_id')
        
        if not medicine_ids or len(medicine_ids) == 0:
            flash('Please add at least one medicine to the prescription.', 'danger')
            return redirect(url_for('health.create_prescription'))
        
        # Create prescription
        prescription = Prescription(
            student_id=student_id,
            visit_id=visit_id if visit_id else None,
            created_by_id=current_user.id,
            notes=notes
        )
        db.session.add(prescription)
        db.session.flush()  # Get prescription ID without committing
        
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
        
        # Add prescription items
        item_count = 0
        for idx, medicine_id in enumerate(medicine_ids):
            if not medicine_id:
                continue
            
            medicine = Medicine.query.get(medicine_id)
            if not medicine:
                continue
            
            dosage = request.form.getlist('dosage[]')[idx] if idx < len(request.form.getlist('dosage[]')) else ''
            frequency = request.form.getlist('frequency[]')[idx] if idx < len(request.form.getlist('frequency[]')) else ''
            duration_days = request.form.getlist('duration_days[]')[idx] if idx < len(request.form.getlist('duration_days[]')) else '0'
            quantity = request.form.getlist('quantity_prescribed[]')[idx] if idx < len(request.form.getlist('quantity_prescribed[]')) else '1'
            instructions = request.form.getlist('instructions[]')[idx] if idx < len(request.form.getlist('instructions[]')) else ''
            
            try:
                duration_days = int(duration_days) if duration_days else 0
                quantity = int(quantity) if quantity else 1
            except ValueError:
                flash(f'Invalid values for {medicine.name}', 'warning')
                continue
            
            frequency_text = frequency_map.get(frequency, frequency)
            
            item = PrescriptionItem(
                prescription_id=prescription.id,
                medicine_id=medicine_id,
                dosage=dosage.strip() or None,
                frequency=frequency_text.strip() or None,
                duration_days=duration_days,
                quantity_prescribed=quantity,
                instructions=instructions.strip() or None,
                status='PENDING'
            )
            db.session.add(item)
            item_count += 1
        
        if item_count == 0:
            db.session.rollback()
            flash('No valid medicines were added to the prescription.', 'danger')
            return redirect(url_for('health.create_prescription'))
        
        db.session.commit()
        flash(f'Prescription created with {item_count} medicine(s). Ready for dispensing.', 'success')
        return redirect(url_for('health.view_prescription', prescription_id=prescription.id))
    
    students = Student.query.all()
    medicines = Medicine.query.all()  # Show all medicines
    
    return render_template('health/create_prescription.html', students=students, medicines=medicines)


@health_bp.route('/prescriptions/<int:prescription_id>/dispense', methods=['POST'])
@role_required('H2')
def dispense_prescription(prescription_id):
    """Dispense prescription item with per-medicine dispensing support"""
    prescription = Prescription.query.get_or_404(prescription_id)
    
    if prescription.overall_status == 'DISPENSED':
        flash('This prescription has already been fully dispensed.', 'warning')
        return redirect(url_for('health.view_prescription', prescription_id=prescription.id))
    
    # Get item ID to dispense
    item_id = request.form.get('item_id', type=int)
    quantity_to_dispense = request.form.get('quantity_to_dispense', type=int)
    
    item = PrescriptionItem.query.get_or_404(item_id)
    
    if item.prescription_id != prescription.id:
        flash('Invalid prescription item.', 'danger')
        return redirect(url_for('health.view_prescription', prescription_id=prescription.id))
    
    if item.status == 'DISPENSED':
        flash(f'Medicine {item.medicine.name} has already been fully dispensed.', 'warning')
        return redirect(url_for('health.view_prescription', prescription_id=prescription.id))
    
    # Default to remaining quantity if not specified
    if not quantity_to_dispense or quantity_to_dispense < 1:
        quantity_to_dispense = item.quantity_prescribed - item.quantity_dispensed
    
    # Validate quantity
    if quantity_to_dispense > (item.quantity_prescribed - item.quantity_dispensed):
        flash(f'Cannot dispense more than prescribed. Remaining: {item.quantity_prescribed - item.quantity_dispensed}', 'danger')
        return redirect(url_for('health.view_prescription', prescription_id=prescription.id))
    
    medicine = item.medicine
    if not medicine:
        item.status = 'OUT_OF_STOCK'
        db.session.commit()
        flash(f'Medicine not found in inventory. Item marked as OUT_OF_STOCK.', 'warning')
        return redirect(url_for('health.view_prescription', prescription_id=prescription.id))
    
    # Check stock
    if medicine.quantity < quantity_to_dispense:
        item.status = 'OUT_OF_STOCK'
        db.session.commit()
        flash(f'Insufficient stock for {medicine.name}. Available: {medicine.quantity}, Required: {quantity_to_dispense}. Item marked as OUT_OF_STOCK.', 'warning')
        return redirect(url_for('health.view_prescription', prescription_id=prescription.id))
    
    # Dispense the medicine
    item.quantity_dispensed += quantity_to_dispense
    
    # Update item status
    if item.quantity_dispensed >= item.quantity_prescribed:
        item.status = 'DISPENSED'
    else:
        item.status = 'PARTIAL'
    
    item.dispensed_date = datetime.utcnow()
    
    # Reduce stock
    medicine.quantity -= quantity_to_dispense
    
    # Record stock movement
    stock_movement = StockMovement(
        medicine_id=medicine.id,
        user_id=current_user.id,
        movement_type='DISPENSE',
        quantity=quantity_to_dispense,
        reason=f'Prescription dispensed to {prescription.student.roll_number} - {quantity_to_dispense} units',
        reference_id=item.id
    )
    db.session.add(stock_movement)
    db.session.commit()
    
    status_text = 'fully' if item.status == 'DISPENSED' else 'partially'
    flash(f'{medicine.name} {status_text} dispensed. {quantity_to_dispense} units reduced from stock.', 'success')
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


@health_bp.route('/prescriptions/replace-dummy/<int:item_id>', methods=['GET', 'POST'])
@role_required('H2')
def replace_dummy_medicine(item_id):
    """Replace dummy medicine with real medicine before dispensing"""
    item = PrescriptionItem.query.get_or_404(item_id)
    
    if not item.dummy_medicine_id:
        flash('This is not a dummy medicine prescription item.', 'danger')
        return redirect(url_for('health.view_prescription', prescription_id=item.prescription_id))
    
    if request.method == 'POST':
        real_medicine_id = request.form.get('medicine_id', type=int)
        real_medicine = Medicine.query.get_or_404(real_medicine_id)
        
        # Verify new medicine has sufficient stock
        if real_medicine.quantity < item.quantity_prescribed:
            flash(f'Insufficient stock for {real_medicine.name}. Required: {item.quantity_prescribed}, Available: {real_medicine.quantity}', 'danger')
            return redirect(url_for('health.replace_dummy_medicine', item_id=item_id))
        
        # Update prescription item
        item.medicine_id = real_medicine_id
        item.dummy_medicine_id = None
        item.status = 'PENDING'  # Reset to PENDING
        
        # Mark dummy as replaced
        dummy = item.dummy_medicine
        dummy.is_replaced = True
        dummy.replaced_by_id = real_medicine_id
        
        db.session.commit()
        
        flash(f'Dummy medicine replaced with {real_medicine.name}.', 'success')
        return redirect(url_for('health.view_prescription', prescription_id=item.prescription_id))
    
    # Get available real medicines that could replace this dummy
    dummy = item.dummy_medicine
    similar_medicines = Medicine.query.filter(Medicine.quantity > 0).all()
    
    return render_template('health/replace_dummy_medicine.html', item=item, dummy=dummy, medicines=similar_medicines)


@health_bp.route('/prescriptions/print/<int:prescription_id>')
@role_required('H2', 'Doctor')
def print_prescription(prescription_id):
    """Print prescription (with or without dummy medicine buying details)"""
    prescription = Prescription.query.get_or_404(prescription_id)
    include_dummy_details = request.args.get('include_dummy_details', 'true').lower() == 'true'
    
    return render_template('health/print_prescription.html', 
                          prescription=prescription,
                          include_dummy_details=include_dummy_details,
                          now=datetime.now())
