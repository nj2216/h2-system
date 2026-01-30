"""
Equipment Management Routes
"""
from datetime import datetime, timedelta
from flask import render_template, request, flash, redirect, url_for, jsonify
from flask_login import login_required, current_user
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
            flash(f'Error issuing equipment: {str(e)}', 'danger')
    
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
            
            # Process return
            issue.process_return(condition, notes)
            issue.verified_by_id = current_user.id
            
            db.session.commit()
            
            penalty_msg = ''
            if issue.penalty_amount > 0:
                penalty_msg = f' Penalty charged: ₹{issue.penalty_amount:.2f}'
            
            flash(f'Equipment return processed successfully.{penalty_msg}', 'success')
            return redirect(url_for('equipment.issue_list'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error processing return: {str(e)}', 'danger')
    
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
            flash(f'Error managing equipment: {str(e)}', 'danger')
    
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
        flash(f'Error: {str(e)}', 'danger')
    
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
    
    return render_template('equipment/student_dashboard.html', issued=issued, returned=returned, total_penalty=total_penalty)
