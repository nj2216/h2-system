"""
Student management blueprint routes
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import current_user, login_required
from datetime import datetime
from ..extensions import db
from app.models import Student, User
from app.auth.utils import role_required

students_bp = Blueprint('students', __name__, template_folder='../templates/students')


@students_bp.route('/')
@role_required('H2', 'Warden', 'Director')
def students_list():
    """List all students"""
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    
    query = Student.query
    
    if search:
        query = query.filter(
            (Student.roll_number.ilike(f'%{search}%')) |
            (User.first_name.ilike(f'%{search}%')) |
            (User.last_name.ilike(f'%{search}%'))
        ).join(User)
    
    students = query.paginate(page=page, per_page=20)
    
    return render_template('students/list.html', students=students, search=search)


@students_bp.route('/register', methods=['GET', 'POST'])
@role_required('H2', 'Director')
def register_student():
    """Register a new student"""
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        roll_number = request.form.get('roll_number')
        date_of_birth = request.form.get('date_of_birth')
        gender = request.form.get('gender')
        blood_group = request.form.get('blood_group')
        hostel_room = request.form.get('hostel_room')
        phone_number = request.form.get('phone_number')
        emergency_contact_name = request.form.get('emergency_contact_name')
        emergency_contact_phone = request.form.get('emergency_contact_phone')
        emergency_contact_relation = request.form.get('emergency_contact_relation')
        
        # Validation
        if not username or not email or not password or not roll_number:
            flash('Username, email, password, and roll number are required.', 'danger')
            return redirect(url_for('students.register_student'))
        
        if User.query.filter_by(username=username).first():
            flash('Username already exists.', 'danger')
            return redirect(url_for('students.register_student'))
        
        if User.query.filter_by(email=email).first():
            flash('Email already exists.', 'danger')
            return redirect(url_for('students.register_student'))
        
        if Student.query.filter_by(roll_number=roll_number).first():
            flash('Roll number already exists.', 'danger')
            return redirect(url_for('students.register_student'))
        
        # Convert date_of_birth string to date object
        dob = None
        if date_of_birth:
            try:
                dob = datetime.strptime(date_of_birth, '%Y-%m-%d').date()
            except ValueError:
                flash('Invalid date format for date of birth.', 'danger')
                return redirect(url_for('students.register_student'))
        
        # Create user
        user = User(
            username=username,
            email=email,
            first_name=first_name,
            last_name=last_name,
            role='Student'
        )
        user.set_password(password)
        db.session.add(user)
        db.session.flush()
        
        # Create student profile
        student = Student(
            user_id=user.id,
            roll_number=roll_number,
            date_of_birth=dob,
            gender=gender,
            blood_group=blood_group,
            hostel_room=hostel_room,
            phone_number=phone_number,
            emergency_contact_name=emergency_contact_name,
            emergency_contact_phone=emergency_contact_phone,
            emergency_contact_relation=emergency_contact_relation
        )
        
        db.session.add(student)
        db.session.commit()
        
        flash(f'Student {roll_number} registered successfully.', 'success')
        return redirect(url_for('students.view_student', student_id=student.id))
    
    return render_template('students/student_register.html')


@students_bp.route('/<int:student_id>')
@role_required('H2', 'Warden', 'Director', 'Doctor', 'Student')
def view_student(student_id):
    """View student profile and health history"""
    student = Student.query.get_or_404(student_id)
    
    # Check access: students can only view their own profile
    if current_user.role == 'Student' and current_user.id != student.user_id:
        flash('You do not have permission to view this profile.', 'danger')
        return redirect(url_for('dashboards.dashboard'))
    
    doctor_visits = student.doctor_visits
    prescriptions = student.prescriptions
    
    return render_template('students/profile.html', 
                          student=student, 
                          doctor_visits=doctor_visits,
                          prescriptions=prescriptions)


@students_bp.route('/<int:student_id>/edit', methods=['GET', 'POST'])
@role_required('H2', 'Director')
def edit_student(student_id):
    """Edit student profile"""
    student = Student.query.get_or_404(student_id)
    
    if request.method == 'POST':
        # Handle date parsing
        date_of_birth = request.form.get('date_of_birth')
        if date_of_birth:
            try:
                student.date_of_birth = datetime.strptime(date_of_birth, '%Y-%m-%d').date()
            except ValueError:
                flash('Invalid date format for date of birth.', 'danger')
                return redirect(url_for('students.edit_student', student_id=student.id))
        else:
            student.date_of_birth = None
        
        student.gender = request.form.get('gender')
        student.blood_group = request.form.get('blood_group')
        student.hostel_room = request.form.get('hostel_room')
        student.phone_number = request.form.get('phone_number')
        student.allergies = request.form.get('allergies')
        student.medical_conditions = request.form.get('medical_conditions')
        student.current_medications = request.form.get('current_medications')
        student.emergency_contact_name = request.form.get('emergency_contact_name')
        student.emergency_contact_phone = request.form.get('emergency_contact_phone')
        student.emergency_contact_relation = request.form.get('emergency_contact_relation')
        
        db.session.commit()
        flash('Student profile updated successfully.', 'success')
        return redirect(url_for('students.view_student', student_id=student.id))
    
    return render_template('students/edit.html', student=student)


@students_bp.route('/<int:student_id>/health-history')
@role_required('H2', 'Warden', 'Director', 'Doctor', 'Student')
def health_history(student_id):
    """View student health history"""
    student = Student.query.get_or_404(student_id)
    
    # Check access
    if current_user.role == 'Student' and current_user.id != student.user_id:
        flash('You do not have permission to view this profile.', 'danger')
        return redirect(url_for('dashboards.dashboard'))
    
    doctor_visits = student.doctor_visits
    prescriptions = student.prescriptions
    
    return render_template('students/health_history.html',
                          student=student,
                          doctor_visits=doctor_visits,
                          prescriptions=prescriptions)
