"""
Sick leave and sick food workflow blueprint routes
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import current_user, login_required
from datetime import datetime, timedelta
from ..extensions import db
from app.models import Student, SickLeaveRequest
from app.auth.utils import role_required

sickleave_bp = Blueprint('sickleave', __name__, template_folder='../templates/sickleave')


@sickleave_bp.route('/calendar')
@role_required('H2', 'Warden', 'Office', 'Director')
def calendar_view():
    """Calendar view of sick leave/food requests"""
    year = request.args.get('year', type=int)
    month = request.args.get('month', type=int)
    
    today = datetime.now().date()
    if not year:
        year = today.year
    if not month:
        month = today.month
    
    # Get stats
    approved = SickLeaveRequest.query.filter_by(overall_status='Approved').count()
    pending = SickLeaveRequest.query.filter_by(overall_status='Pending').count()
    rejected = SickLeaveRequest.query.filter_by(overall_status='Rejected').count()
    total = SickLeaveRequest.query.count()
    
    stats = {
        'approved': approved,
        'pending': pending,
        'rejected': rejected,
        'total': total
    }
    
    # Get all sick leave requests
    requests = SickLeaveRequest.query.all()
    
    # Build events for calendar
    events = []
    for req in requests:
        current_date = req.start_date
        while current_date <= req.end_date:
            events.append({
                'date': current_date.strftime('%Y-%m-%d'),
                'request_id': req.id,
                'student': req.student.user.first_name or req.student.user.username,
                'type': req.request_type,
                'status': req.overall_status,
                'color': 'success' if req.overall_status == 'Approved' else 'warning' if req.overall_status == 'Pending' else 'danger'
            })
            current_date += timedelta(days=1)
    
    return render_template('sickleave/calendar.html', year=year, month=month, events=events, stats=stats)


@sickleave_bp.route('/calendar/data')
@role_required('H2', 'Warden', 'Office', 'Director')
def calendar_data():
    """API endpoint for calendar events"""
    year = request.args.get('year', type=int)
    month = request.args.get('month', type=int)
    
    if not year or not month:
        return jsonify([])
    
    # Get first and last day of month
    first_day = datetime(year, month, 1).date()
    if month == 12:
        last_day = datetime(year + 1, 1, 1).date() - timedelta(days=1)
    else:
        last_day = datetime(year, month + 1, 1).date() - timedelta(days=1)
    
    # Get all requests overlapping with this month
    requests = SickLeaveRequest.query.filter(
        SickLeaveRequest.start_date <= last_day,
        SickLeaveRequest.end_date >= first_day
    ).all()
    
    events = []
    for req in requests:
        current_date = max(req.start_date, first_day)
        while current_date <= min(req.end_date, last_day):
            events.append({
                'date': current_date.strftime('%Y-%m-%d'),
                'request_id': req.id,
                'student': req.student.user.first_name or req.student.user.username,
                'type': req.request_type,
                'status': req.overall_status,
                'color': 'success' if req.overall_status == 'Approved' else 'warning' if req.overall_status == 'Pending' else 'danger'
            })
            current_date += timedelta(days=1)
    
    return jsonify(events)


@sickleave_bp.route('/')
@role_required('H2', 'Warden', 'Office', 'Director')
def requests_list():
    """List sick leave/food requests"""
    page = request.args.get('page', 1, type=int)
    status = request.args.get('status', '')
    request_type = request.args.get('type', '')
    
    query = SickLeaveRequest.query
    
    if status:
        query = query.filter_by(overall_status=status)
    
    if request_type:
        query = query.filter_by(request_type=request_type)
    
    requests = query.order_by(SickLeaveRequest.created_at.desc()).paginate(page=page, per_page=20)
    
    return render_template('sickleave/list.html', requests=requests, status=status, request_type=request_type)


@sickleave_bp.route('/create', methods=['GET', 'POST'])
@role_required('H2')
def create_request():
    """Create new sick leave/food request"""
    if request.method == 'POST':
        student_id = request.form.get('student_id', type=int)
        request_type = request.form.get('request_type')  # 'Sick Leave' or 'Sick Food'
        start_date = request.form.get('start_date')
        end_date = request.form.get('end_date')
        reason = request.form.get('reason')
        medical_certificate = request.form.get('medical_certificate')
        
        # Validate required fields
        if not student_id or not request_type or not start_date or not end_date or not reason:
            flash('Please fill in all required fields.', 'danger')
            return redirect(url_for('sickleave.create_request'))
        
        student = Student.query.get_or_404(student_id)
        
        # Convert date strings to Python date objects
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        
        sick_request = SickLeaveRequest(
            student_id=student_id,
            created_by_id=current_user.id,
            request_type=request_type,
            start_date=start_date,
            end_date=end_date,
            reason=reason,
            medical_certificate=medical_certificate,
            overall_status='Pending'  # Explicitly set initial status
        )
        
        db.session.add(sick_request)
        db.session.commit()
        
        flash(f'{request_type} request created successfully.', 'success')
        return redirect(url_for('sickleave.view_request', request_id=sick_request.id))
    
    students = Student.query.all()
    
    return render_template('sickleave/create.html', students=students)


@sickleave_bp.route('/<int:request_id>')
@role_required('H2', 'Warden', 'Office', 'Director')
def view_request(request_id):
    """View sick leave/food request details"""
    sick_request = SickLeaveRequest.query.get_or_404(request_id)
    
    return render_template('sickleave/view.html', request=sick_request)


@sickleave_bp.route('/<int:request_id>/h2-approve', methods=['POST'])
@role_required('H2')
def h2_approve(request_id):
    """H2 approves/rejects request"""
    sick_request = SickLeaveRequest.query.get_or_404(request_id)
    
    action = request.form.get('action')  # approve or reject
    notes = request.form.get('notes')
    
    if action == 'approve':
        sick_request.h2_status = 'Approved'
        # Keep overall_status as Pending - it will be updated after all approvals
        message = 'Request approved by H2. Forwarding to Warden for verification.'
    else:
        sick_request.h2_status = 'Rejected'
        sick_request.overall_status = 'Rejected'
        message = 'Request rejected by H2.'
    
    sick_request.h2_notes = notes
    sick_request.h2_approved_by = current_user.id
    sick_request.h2_approved_date = datetime.utcnow()
    
    db.session.commit()
    
    flash(message, 'success')
    return redirect(url_for('sickleave.view_request', request_id=request_id))


@sickleave_bp.route('/<int:request_id>/warden-verify', methods=['POST'])
@role_required('Warden')
def warden_verify(request_id):
    """Warden verifies/rejects request"""
    sick_request = SickLeaveRequest.query.get_or_404(request_id)
    
    if sick_request.h2_status != 'Approved':
        flash('H2 approval is required before warden verification.', 'danger')
        return redirect(url_for('sickleave.view_request', request_id=request_id))
    
    action = request.form.get('action')  # approve or reject
    notes = request.form.get('notes')
    
    if action == 'approve':
        sick_request.warden_status = 'Approved'
        # Keep overall_status as Pending - it will be updated after Office approval
        message = 'Request verified by Warden. Forwarding to Office for approval.'
    else:
        sick_request.warden_status = 'Rejected'
        sick_request.overall_status = 'Rejected'
        message = 'Request rejected by Warden.'
    
    sick_request.warden_notes = notes
    sick_request.warden_verified_by = current_user.id
    sick_request.warden_verified_date = datetime.utcnow()
    
    db.session.commit()
    
    flash(message, 'success')
    return redirect(url_for('sickleave.view_request', request_id=request_id))


@sickleave_bp.route('/<int:request_id>/office-approve', methods=['POST'])
@role_required('Office')
def office_approve(request_id):
    """Office approves/rejects request"""
    sick_request = SickLeaveRequest.query.get_or_404(request_id)
    
    if sick_request.warden_status != 'Approved':
        flash('Warden verification is required before office approval.', 'danger')
        return redirect(url_for('sickleave.view_request', request_id=request_id))
    
    action = request.form.get('action')  # approve or reject
    notes = request.form.get('notes')
    
    if action == 'approve':
        sick_request.office_status = 'Approved'
        # If all three stages approved, mark as Approved
        if (sick_request.h2_status == 'Approved' and 
            sick_request.warden_status == 'Approved' and 
            sick_request.office_status == 'Approved'):
            sick_request.overall_status = 'Approved'
        message = 'Request approved by Office. All approvals complete!'
    else:
        sick_request.office_status = 'Rejected'
        sick_request.overall_status = 'Rejected'
        message = 'Request rejected by Office.'
    
    sick_request.office_notes = notes
    sick_request.office_approved_by = current_user.id
    sick_request.office_approved_date = datetime.utcnow()
    
    db.session.commit()
    
    flash(message, 'success')
    return redirect(url_for('sickleave.view_request', request_id=request_id))


@sickleave_bp.route('/<int:request_id>/director-approve', methods=['POST'])
@role_required('Director')
def director_approve(request_id):
    """Director reviews/approves request (optional)"""
    sick_request = SickLeaveRequest.query.get_or_404(request_id)
    
    action = request.form.get('action')  # approve or reject
    notes = request.form.get('notes')
    
    if action == 'approve':
        sick_request.director_status = 'Approved'
        message = 'Request approved by Director.'
    else:
        sick_request.director_status = 'Rejected'
        sick_request.overall_status = 'Rejected'
        message = 'Request rejected by Director.'
    
    sick_request.director_notes = notes
    sick_request.director_approved_by = current_user.id
    sick_request.director_approved_date = datetime.utcnow()
    
    db.session.commit()
    
    flash(message, 'success')
    return redirect(url_for('sickleave.view_request', request_id=request_id))


@sickleave_bp.route('/pending')
@role_required('H2', 'Warden', 'Office', 'Director')
def pending_requests():
    """View pending requests based on user role"""
    if current_user.role == 'H2':
        requests = SickLeaveRequest.query.filter_by(h2_status='Pending').all()
        stage = 'H2 Review'
    elif current_user.role == 'Warden':
        requests = SickLeaveRequest.query.filter_by(warden_status='Pending', h2_status='Approved').all()
        stage = 'Warden Verification'
    elif current_user.role == 'Office':
        requests = SickLeaveRequest.query.filter_by(office_status='Pending', warden_status='Approved').all()
        stage = 'Office Approval'
    elif current_user.role == 'Director':
        requests = SickLeaveRequest.query.filter_by(director_status='Pending').all()
        stage = 'Director Review'
    else:
        requests = []
        stage = ''
    
    return render_template('sickleave/pending.html', requests=requests, stage=stage)


@sickleave_bp.route('/approved')
@role_required('H2', 'Warden', 'Office', 'Director')
def approved_requests():
    """View approved requests"""
    page = request.args.get('page', 1, type=int)
    
    requests = SickLeaveRequest.query.filter_by(overall_status='Approved').paginate(page=page, per_page=20)
    
    return render_template('sickleave/approved.html', requests=requests)
