"""
Dashboard blueprint routes with role-based views
"""
from flask import Blueprint, render_template
from flask_login import current_user, login_required
from sqlalchemy import func
from ..extensions import db
from app.models import (Student, DoctorVisit, Prescription, Medicine, Asset, 
                        SickLeaveRequest, User, StockMovement, MaintenanceLog)

dashboards_bp = Blueprint('dashboards', __name__, template_folder='../templates/dashboards')


@dashboards_bp.route('/')
@login_required
def dashboard():
    """Main dashboard with role-based view"""
    if current_user.role == 'Student':
        return student_dashboard()
    elif current_user.role == 'H2':
        return h2_dashboard()
    elif current_user.role == 'Warden':
        return warden_dashboard()
    elif current_user.role == 'Office':
        return office_dashboard()
    elif current_user.role == 'Director':
        return director_dashboard()
    elif current_user.role == 'Doctor':
        return doctor_dashboard()
    else:
        return render_template('dashboards/dashboard.html')


def student_dashboard():
    """Student view dashboard"""
    student = Student.query.filter_by(user_id=current_user.id).first()
    
    if not student:
        return render_template('dashboards/student_dashboard.html', student=None)
    
    # Get student's recent doctor visits
    recent_visits = student.doctor_visits[-5:] if student.doctor_visits else []
    
    # Get student's pending/partial prescriptions (not fully dispensed)
    all_prescriptions = Prescription.query.filter_by(student_id=student.id).all()
    pending_prescriptions = [p for p in all_prescriptions if p.overall_status != 'DISPENSED']
    
    # Get student's sick leave requests
    sick_requests = student.sickleave_requests[-3:] if student.sickleave_requests else []
    
    stats = {
        'total_visits': len(student.doctor_visits),
        'pending_prescriptions': len(pending_prescriptions),
        'total_requests': len(student.sickleave_requests)
    }
    
    return render_template('dashboards/student_dashboard.html',
                          student=student,
                          recent_visits=recent_visits,
                          pending_prescriptions=pending_prescriptions,
                          sick_requests=sick_requests,
                          stats=stats)


def h2_dashboard():
    """Health Team view dashboard"""
    total_students = Student.query.count()
    total_visits = DoctorVisit.query.count()
    total_medicines = Medicine.query.count()
    # Count medicines with low stock, considering only non-expired batches
    all_medicines = Medicine.query.all()
    low_stock_medicines = sum(1 for medicine in all_medicines if medicine.is_low_stock)
    
    # Pending requests
    pending_h2_requests = SickLeaveRequest.query.filter_by(h2_status='Pending').count()
    
    # Recent doctor visits
    recent_visits = DoctorVisit.query.order_by(DoctorVisit.visit_date.desc()).limit(10).all()
    
    # Undispensed prescriptions (not all items dispensed)
    all_prescriptions = Prescription.query.all()
    undispensed = sum(1 for p in all_prescriptions if p.overall_status != 'DISPENSED')
    
    stats = {
        'total_students': total_students,
        'total_visits': total_visits,
        'total_medicines': total_medicines,
        'low_stock': low_stock_medicines,
        'pending_requests': pending_h2_requests,
        'undispensed_prescriptions': undispensed
    }
    
    return render_template('dashboards/h2_dashboard.html',
                          stats=stats,
                          recent_visits=recent_visits)


def warden_dashboard():
    """Warden view dashboard"""
    total_students = Student.query.count()
    total_assets = Asset.query.count()
    damaged_assets = Asset.query.filter_by(condition='Damaged').count()
    poor_assets = Asset.query.filter_by(condition='Poor').count()
    
    # Pending requests for warden
    pending_requests = SickLeaveRequest.query.filter(
        SickLeaveRequest.warden_status == 'Pending',
        SickLeaveRequest.h2_status == 'Approved'
    ).count()
    
    # Maintenance logs
    recent_maintenance = MaintenanceLog.query.order_by(
        MaintenanceLog.maintenance_date.desc()
    ).limit(5).all()
    
    stats = {
        'total_students': total_students,
        'total_assets': total_assets,
        'damaged_assets': damaged_assets,
        'poor_condition_assets': poor_assets,
        'pending_approvals': pending_requests
    }
    
    return render_template('dashboards/warden_dashboard.html',
                          stats=stats,
                          recent_maintenance=recent_maintenance)


def office_dashboard():
    """Office view dashboard"""
    total_students = Student.query.count()
    
    # Pending requests for office
    pending_requests = SickLeaveRequest.query.filter(
        SickLeaveRequest.office_status == 'Pending',
        SickLeaveRequest.warden_status == 'Approved'
    ).count()
    
    # Approved requests (last month)
    approved_requests = SickLeaveRequest.query.filter_by(overall_status='Approved').count()
    
    # Sick leave requests grouped by type
    sick_leave_count = SickLeaveRequest.query.filter_by(request_type='sick_leave').count()
    sick_food_count = SickLeaveRequest.query.filter_by(request_type='sick_food').count()
    
    stats = {
        'total_students': total_students,
        'pending_approvals': pending_requests,
        'approved_requests': approved_requests,
        'sick_leave_requests': sick_leave_count,
        'sick_food_requests': sick_food_count
    }
    
    return render_template('dashboards/office_dashboard.html', stats=stats)


def director_dashboard():
    """Director view dashboard - system overview"""
    total_users = User.query.count()
    total_students = Student.query.count()
    total_visits = DoctorVisit.query.count()
    total_medicines = Medicine.query.count()
    total_assets = Asset.query.count()
    
    # Pending requests at director level
    pending_director_requests = SickLeaveRequest.query.filter_by(director_status='Pending').count()
    
    # Rejected requests
    rejected_requests = SickLeaveRequest.query.filter_by(overall_status='Rejected').count()
    
    # Low stock medicines
    low_stock = Medicine.query.filter(
        Medicine.quantity <= Medicine.min_stock_level
    ).count()
    
    # Assets needing maintenance
    poor_assets = Asset.query.filter(
        Asset.condition.in_(['Poor', 'Damaged'])
    ).count()
    
    # User stats by role
    role_stats = db.session.query(
        User.role, 
        func.count(User.id)
    ).group_by(User.role).all()
    
    stats = {
        'total_users': total_users,
        'total_students': total_students,
        'total_visits': total_visits,
        'total_medicines': total_medicines,
        'total_assets': total_assets,
        'low_stock_medicines': low_stock,
        'poor_assets': poor_assets,
        'pending_director_requests': pending_director_requests,
        'rejected_requests': rejected_requests,
        'role_stats': dict(role_stats)
    }
    
    return render_template('dashboards/director_dashboard.html', stats=stats)


def doctor_dashboard():
    """Doctor view dashboard"""
    # Doctor's visits
    my_visits = DoctorVisit.query.filter_by(doctor_id=current_user.id).count()
    
    # My prescriptions
    my_prescriptions = Prescription.query.filter_by(created_by_id=current_user.id).count()
    
    # Undispensed prescriptions created by this doctor
    doctor_prescriptions = Prescription.query.filter_by(created_by_id=current_user.id).all()
    undispensed = sum(1 for p in doctor_prescriptions if p.overall_status != 'DISPENSED')
    
    # Recent visits by this doctor
    recent_visits = DoctorVisit.query.filter_by(
        doctor_id=current_user.id
    ).order_by(DoctorVisit.visit_date.desc()).limit(10).all()
    
    stats = {
        'total_visits': my_visits,
        'total_prescriptions': my_prescriptions,
        'undispensed_prescriptions': undispensed
    }
    
    return render_template('dashboards/doctor_dashboard.html',
                          stats=stats,
                          recent_visits=recent_visits)
