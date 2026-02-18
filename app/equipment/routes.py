"""
Equipment Management Routes
"""
from datetime import datetime, timedelta
from flask import render_template, request, flash, redirect, url_for, jsonify, current_app
from flask_login import login_required, current_user
from markupsafe import Markup
from sqlalchemy import and_, or_
from app.extensions import db
from app.models import MedicalEquipment, EquipmentIssue, Student, User
from . import equipment_bp


def require_role(*roles):
    """Decorator to check user role"""
    def decorator(f):
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated or current_user.role not in roles:
                flash('Access denied. Insufficient permissions.', 'danger')
                return redirect(url_for('main.index'))
            return f(*args, **kwargs)
        decorated_function.__name__ = f.__name__
        return decorated_function
    return decorator


@equipment_bp.route('/inventory', methods=['GET'])
@login_required
def inventory():
    """View equipment inventory"""
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    
    query = MedicalEquipment.query
    
    if search:
        query = query.filter(
            or_(
                MedicalEquipment.name.ilike(f'%{search}%'),
                MedicalEquipment.equipment_code.ilike(f'%{search}%'),
                MedicalEquipment.category.ilike(f'%{search}%')
            )
        )
    
    equipments = query.paginate(page=page, per_page=20)
    
    return render_template('equipment/inventory.html', equipments=equipments, search=search)


@equipment_bp.route('/issue', methods=['GET', 'POST'])
@login_required
@require_role('H2', 'Doctor')
def issue_equipment():
    """Issue equipment to student"""
    if request.method == 'POST':
        try:
            student_id = request.form.get('student_id', type=int)
            equipment_id = request.form.get('equipment_id', type=int)
            quantity = request.form.get('quantity', 1, type=int)
            expected_return_days = request.form.get('expected_return_days', 7, type=int)
            
            # Validate inputs
            student = Student.query.get(student_id)
            equipment = MedicalEquipment.query.get(equipment_id)
            
            if not student or not equipment:
                flash('Invalid student or equipment.', 'danger')
                return redirect(url_for('equipment.issue_equipment'))
            
            if equipment.quantity_available < quantity:
                flash(f'Insufficient stock. Available: {equipment.quantity_available}', 'danger')
                return redirect(url_for('equipment.issue_equipment'))
            
            # Create issue record
            expected_return_date = datetime.utcnow() + timedelta(days=expected_return_days)
            
            issue = EquipmentIssue(
                equipment_id=equipment_id,
                student_id=student_id,
                issued_by_id=current_user.id,
                quantity=quantity,
                expected_return_date=expected_return_date
            )
            
            # Update equipment quantity
            equipment.quantity_available -= quantity
            equipment.quantity_issued += quantity
            
            db.session.add(issue)
            db.session.commit()
            
            flash(f'Equipment issued successfully. Expected return: {expected_return_date.strftime("%Y-%m-%d")}', 'success')
            return redirect(url_for('equipment.issue_list'))
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f'Equipment issue error: {str(e)}', exc_info=True)
            flash('Failed to issue equipment. Please try again or contact support.', 'danger')
    
    # Get students and equipment for dropdown
    students = Student.query.all()
    equipments = MedicalEquipment.query.filter(MedicalEquipment.quantity_available > 0).all()
    
    return render_template('equipment/issue.html', students=students, equipments=equipments)


@equipment_bp.route('/issues', methods=['GET'])
@login_required
def issue_list():
    """List equipment issues"""
    page = request.args.get('page', 1, type=int)
    status_filter = request.args.get('status', 'all')
    search = request.args.get('search', '')
    
    query = EquipmentIssue.query
    
    # Role-based filtering
    if current_user.role == 'Student':
        student = Student.query.filter_by(user_id=current_user.id).first()
        if student:
            query = query.filter_by(student_id=student.id)
        else:
            query = query.filter(False)  # No results for non-student users
    elif current_user.role in ['Warden', 'H2', 'Office']:
        # Wardens, H2, and Office can view all issues
        pass
    elif current_user.role == 'Doctor':
        # Doctor can view issues they issued
        query = query.filter_by(issued_by_id=current_user.id)
    
    # Status filter
    if status_filter != 'all':
        query = query.filter_by(status=status_filter)
    
    # Search
    if search:
        query = query.join(Student).join(MedicalEquipment).filter(
            or_(
                Student.roll_number.ilike(f'%{search}%'),
                MedicalEquipment.name.ilike(f'%{search}%')
            )
        )
    
    # Mark overdue issues
    overdue_issues = query.filter(
        and_(
            EquipmentIssue.actual_return_date == None,
            EquipmentIssue.expected_return_date < datetime.utcnow(),
            EquipmentIssue.status != 'Overdue'
        )
    ).all()
    
    for issue in overdue_issues:
        issue.mark_as_overdue()
    
    issues = query.order_by(EquipmentIssue.issued_date.desc()).paginate(page=page, per_page=20)
    
    return render_template('equipment/issue_list.html', issues=issues, status_filter=status_filter, search=search)


@equipment_bp.route('/return/<int:issue_id>', methods=['GET', 'POST'])
@login_required
@require_role('H2', 'Doctor')
def return_equipment(issue_id):
    """Process equipment return"""
    issue = EquipmentIssue.query.get_or_404(issue_id)
    
    # Check authorization
    if issue.issued_by_id != current_user.id and current_user.role != 'H2':
        flash('You can only verify returns for equipment you issued.', 'danger')
        return redirect(url_for('equipment.issue_list'))
    
    if request.method == 'POST':
        try:
            condition = request.form.get('condition')  # normal, damaged, lost
            notes = request.form.get('notes', '')
            
            if not condition:
                flash('Please select equipment condition.', 'danger')
                return redirect(url_for('equipment.return_equipment', issue_id=issue_id))
            
            # Store penalty details before processing for alert message
            equipment = issue.equipment
            penalty_details = []
            
            # Check overdue penalty
            if issue.actual_return_date is None:
                current_time = datetime.utcnow()
                if current_time > issue.expected_return_date:
                    days_over = max(0, (current_time - issue.expected_return_date).days)
                    if days_over > 0:
                        overdue_penalty = days_over * equipment.daily_penalty * issue.quantity
                        penalty_details.append(f"Overdue ({days_over} days × ₹{equipment.daily_penalty} × {issue.quantity}): ₹{overdue_penalty:.2f}")
            
            # Check condition penalty
            if condition == 'damaged':
                damage_penalty = equipment.unit_cost * issue.quantity * 0.5
                penalty_details.append(f"Damage (50% of ₹{equipment.unit_cost} × {issue.quantity}): ₹{damage_penalty:.2f}")
            elif condition == 'lost':
                loss_penalty = equipment.unit_cost * issue.quantity
                penalty_details.append(f"Replacement cost (100% of ₹{equipment.unit_cost} × {issue.quantity}): ₹{loss_penalty:.2f}")
            
            # Process return
            issue.process_return(condition, notes)
            issue.verified_by_id = current_user.id
            
            db.session.commit()
            
            # Create detailed alert message
            if issue.penalty_amount > 0:
                alert_msg = f'Equipment return processed. <strong>Penalty: ₹{issue.penalty_amount:.2f}</strong><ul class="mb-0 mt-2">'
                for detail in penalty_details:
                    alert_msg += f'<li>{detail}</li>'
                alert_msg += '</ul>'
                flash(Markup(alert_msg), 'warning')
            else:
                flash('Equipment return processed successfully. No penalty.', 'success')
            
            return redirect(url_for('equipment.issue_list'))
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f'Equipment return error: {str(e)}', exc_info=True)
            flash('Failed to process equipment return. Please try again or contact support.', 'danger')
    
    return render_template('equipment/return.html', issue=issue)


@equipment_bp.route('/manage', methods=['GET', 'POST'])
@login_required
@require_role('H2')
def manage_equipment():
    """Manage equipment inventory (add/edit/delete)"""
    if request.method == 'POST':
        try:
            action = request.form.get('action')
            
            if action == 'add':
                equipment = MedicalEquipment(
                    name=request.form.get('name'),
                    equipment_code=request.form.get('equipment_code'),
                    category=request.form.get('category'),
                    description=request.form.get('description'),
                    quantity_available=request.form.get('quantity_available', 0, type=int),
                    unit_cost=request.form.get('unit_cost', 0, type=float),
                    location=request.form.get('location'),
                    daily_penalty=request.form.get('daily_penalty', 0, type=float)
                )
                db.session.add(equipment)
                db.session.commit()
                flash('Equipment added successfully.', 'success')
            
            elif action == 'edit':
                equipment_id = request.form.get('equipment_id', type=int)
                equipment = MedicalEquipment.query.get_or_404(equipment_id)
                
                equipment.name = request.form.get('name')
                equipment.category = request.form.get('category')
                equipment.description = request.form.get('description')
                equipment.unit_cost = request.form.get('unit_cost', type=float)
                equipment.location = request.form.get('location')
                equipment.daily_penalty = request.form.get('daily_penalty', type=float)
                
                db.session.commit()
                flash('Equipment updated successfully.', 'success')
            
            elif action == 'delete':
                equipment_id = request.form.get('equipment_id', type=int)
                equipment = MedicalEquipment.query.get_or_404(equipment_id)
                
                # Check if equipment has active issues
                active_issues = EquipmentIssue.query.filter(
                    and_(
                        EquipmentIssue.equipment_id == equipment_id,
                        EquipmentIssue.actual_return_date == None
                    )
                ).count()
                
                if active_issues > 0:
                    flash('Cannot delete equipment with active issues.', 'danger')
                    return redirect(url_for('equipment.manage_equipment'))
                
                db.session.delete(equipment)
                db.session.commit()
                flash('Equipment deleted successfully.', 'success')
            
            return redirect(url_for('equipment.manage_equipment'))
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f'Equipment management error: {str(e)}', exc_info=True)
            flash('Operation failed. Please try again or contact support.', 'danger')
    
    page = request.args.get('page', 1, type=int)
    equipments = MedicalEquipment.query.paginate(page=page, per_page=20)
    
    return render_template('equipment/manage.html', equipments=equipments)


@equipment_bp.route('/penalty-report', methods=['GET'])
@login_required
@require_role('Office', 'H2')
def penalty_report():
    """View penalty report for overdue/damaged/lost equipment"""
    page = request.args.get('page', 1, type=int)
    filter_type = request.args.get('filter', 'all')  # all, unpaid, paid
    
    query = EquipmentIssue.query.filter(EquipmentIssue.penalty_amount > 0)
    
    if filter_type == 'unpaid':
        query = query.filter_by(penalty_paid=False)
    elif filter_type == 'paid':
        query = query.filter_by(penalty_paid=True)
    
    issues = query.order_by(EquipmentIssue.updated_at.desc()).paginate(page=page, per_page=20)
    
    total_penalty = db.session.query(db.func.sum(EquipmentIssue.penalty_amount)).filter(
        EquipmentIssue.penalty_paid == False
    ).scalar() or 0.0
    
    return render_template('equipment/penalty_report.html', issues=issues, filter_type=filter_type, total_penalty=total_penalty)


@equipment_bp.route('/mark-penalty-paid/<int:issue_id>', methods=['POST'])
@login_required
@require_role('Office', 'H2')
def mark_penalty_paid(issue_id):
    """Mark penalty as paid"""
    issue = EquipmentIssue.query.get_or_404(issue_id)
    
    try:
        issue.penalty_paid = True
        issue.penalty_paid_date = datetime.utcnow()
        db.session.commit()
        
        flash('Penalty marked as paid.', 'success')
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Penalty payment error: {str(e)}', exc_info=True)
        flash('Failed to process penalty payment. Please try again or contact support.', 'danger')
    
    return redirect(url_for('equipment.penalty_report'))


@equipment_bp.route('/student-dashboard', methods=['GET'])
@login_required
def student_dashboard():
    """Student view of issued equipment"""
    student = Student.query.filter_by(user_id=current_user.id).first_or_404()
    
    issued = EquipmentIssue.query.filter(
        and_(
            EquipmentIssue.student_id == student.id,
            EquipmentIssue.status == 'Issued'
        )
    ).all()
    
    # Separate overdue and due soon from regular issued
    overdue = []
    due_soon = []
    regular = []
    
    for issue in issued:
        days_until_due = (issue.expected_return_date - datetime.utcnow()).days
        
        if days_until_due < 0:  # Overdue
            overdue.append(issue)
        elif days_until_due <= 2 and days_until_due >= 0:  # Due within 2 days
            due_soon.append(issue)
        else:  # More than 2 days left
            regular.append(issue)
    
    returned = EquipmentIssue.query.filter(
        and_(
            EquipmentIssue.student_id == student.id,
            EquipmentIssue.status == 'Returned'
        )
    ).all()
    
    total_penalty = db.session.query(db.func.sum(EquipmentIssue.penalty_amount)).filter(
        and_(
            EquipmentIssue.student_id == student.id,
            EquipmentIssue.penalty_paid == False
        )
    ).scalar() or 0.0
    
    return render_template('equipment/student_dashboard.html', 
                          overdue=overdue, 
                          due_soon=due_soon, 
                          regular=regular,
                          issued=issued,
                          returned=returned, 
                          total_penalty=total_penalty,
                          now=datetime.utcnow())


@equipment_bp.route('/bulk-upload', methods=['GET', 'POST'])
@login_required
@require_role('H2')
def bulk_upload_equipment():
    """Bulk upload equipment from CSV file"""
    import csv
    import io
    
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file part in the request.', 'danger')
            return redirect(url_for('equipment.bulk_upload_equipment'))
        
        file = request.files['file']
        
        if file.filename == '':
            flash('No selected file.', 'danger')
            return redirect(url_for('equipment.bulk_upload_equipment'))
        
        if not file.filename.endswith(('.csv', '.txt')):
            flash('Please upload a CSV or TXT file.', 'danger')
            return redirect(url_for('equipment.bulk_upload_equipment'))
        
        try:
            # Read file
            stream = io.StringIO(file.read().decode('UTF-8'), newline=None)
            csv_reader = csv.DictReader(stream)
            
            if not csv_reader.fieldnames:
                flash('CSV file is empty.', 'danger')
                return redirect(url_for('equipment.bulk_upload_equipment'))
            
            # Expected columns: name, equipment_code, category, quantity_available, unit_cost, daily_penalty, location, description
            required_fields = ['name', 'equipment_code']
            missing_fields = [field for field in required_fields if field not in csv_reader.fieldnames]
            
            if missing_fields:
                flash(f'Missing required columns: {", ".join(missing_fields)}', 'danger')
                return redirect(url_for('equipment.bulk_upload_equipment'))
            
            created = 0
            errors = []
            
            for row_num, row in enumerate(csv_reader, start=2):  # Start at 2 (after header)
                try:
                    name = row.get('name', '').strip()
                    equipment_code = row.get('equipment_code', '').strip()
                    
                    if not name or not equipment_code:
                        errors.append(f'Row {row_num}: Missing name or equipment code')
                        continue
                    
                    # Parse quantity
                    quantity_available = 0
                    if row.get('quantity_available', '').strip():
                        try:
                            quantity_available = int(row.get('quantity_available').strip())
                        except ValueError:
                            errors.append(f'Row {row_num}: Quantity must be a number')
                            continue
                    
                    if quantity_available < 0:
                        errors.append(f'Row {row_num}: Quantity cannot be negative')
                        continue
                    
                    # Parse costs
                    unit_cost = 0.0
                    if row.get('unit_cost', '').strip():
                        try:
                            unit_cost = float(row.get('unit_cost').strip())
                        except ValueError:
                            errors.append(f'Row {row_num}: Unit cost must be a number')
                            continue
                    
                    daily_penalty = 0.0
                    if row.get('daily_penalty', '').strip():
                        try:
                            daily_penalty = float(row.get('daily_penalty').strip())
                        except ValueError:
                            errors.append(f'Row {row_num}: Daily penalty must be a number')
                            continue
                    
                    # Check if equipment code already exists
                    existing_equipment = MedicalEquipment.query.filter_by(equipment_code=equipment_code).first()
                    
                    if existing_equipment:
                        # Add to existing stock
                        existing_equipment.quantity_available += quantity_available
                        # Update other fields if provided
                        if row.get('unit_cost', '').strip():
                            existing_equipment.unit_cost = unit_cost
                        if row.get('daily_penalty', '').strip():
                            existing_equipment.daily_penalty = daily_penalty
                        if row.get('location', '').strip():
                            existing_equipment.location = row.get('location', '').strip()
                    else:
                        # Create new equipment
                        equipment = MedicalEquipment(
                            name=name,
                            equipment_code=equipment_code,
                            category=row.get('category', '').strip() or None,
                            description=row.get('description', '').strip() or None,
                            quantity_available=quantity_available,
                            unit_cost=unit_cost,
                            location=row.get('location', '').strip() or None,
                            daily_penalty=daily_penalty
                        )
                        db.session.add(equipment)
                    
                    created += 1
                
                except Exception as e:
                    errors.append(f'Row {row_num}: {str(e)}')
            
            # Commit all successful entries
            if created > 0:
                db.session.commit()
                flash(f'Successfully created {created} equipment item(s).', 'success')
            
            if errors:
                error_msg = '<br>'.join(errors[:10])  # Show first 10 errors
                if len(errors) > 10:
                    error_msg += f'<br>... and {len(errors) - 10} more errors'
                flash(Markup(f'Encountered {len(errors)} error(s):<br>{error_msg}'), 'warning')
            
            return redirect(url_for('equipment.manage_equipment'))
        
        except Exception as e:
            current_app.logger.error(f'Equipment bulk upload error: {str(e)}', exc_info=True)
            flash('Failed to process file. Please check your file format and try again.', 'danger')
            return redirect(url_for('equipment.bulk_upload_equipment'))
    
    return render_template('equipment/bulk_upload.html')
