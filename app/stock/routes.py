"""
Medical stock management blueprint routes
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import current_user, login_required
from datetime import datetime
from ..extensions import db
from app.models import Medicine, StockMovement
from app.auth.utils import role_required

stock_bp = Blueprint('stock', __name__, template_folder='../templates/stock')


@stock_bp.route('/')
@role_required('H2', 'Director')
def inventory():
    """View medicine inventory"""
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    show_low = request.args.get('low_stock', 'false').lower() == 'true'
    
    query = Medicine.query
    
    if search:
        query = query.filter(Medicine.name.ilike(f'%{search}%'))
    
    if show_low:
        query = query.filter(Medicine.quantity <= Medicine.min_stock_level)
    
    medicines = query.order_by(Medicine.name).paginate(page=page, per_page=20)
    
    return render_template('stock/inventory.html', medicines=medicines, search=search, show_low=show_low)


@stock_bp.route('/add-medicine', methods=['GET', 'POST'])
@role_required('H2', 'Director')
def add_medicine():
    """Add new medicine to inventory"""
    if request.method == 'POST':
        name = request.form.get('name')
        generic_name = request.form.get('generic_name')
        dosage = request.form.get('dosage')
        quantity = request.form.get('quantity', type=int)
        min_stock_level = request.form.get('min_stock_level', type=int)
        unit = request.form.get('unit')
        expiry_date = request.form.get('expiry_date')
        supplier = request.form.get('supplier')
        cost_per_unit = request.form.get('cost_per_unit', type=float)
        location = request.form.get('location')
        
        if Medicine.query.filter_by(name=name).first():
            flash('Medicine name already exists.', 'danger')
            return redirect(url_for('stock.add_medicine'))
        
        # Convert expiry_date string to date object if provided
        if expiry_date:
            expiry_date = datetime.strptime(expiry_date, '%Y-%m-%d').date()
        
        medicine = Medicine(
            name=name,
            generic_name=generic_name,
            dosage=dosage,
            quantity=quantity,
            min_stock_level=min_stock_level,
            unit=unit,
            expiry_date=expiry_date,
            supplier=supplier,
            cost_per_unit=cost_per_unit,
            location=location
        )
        
        db.session.add(medicine)
        db.session.flush()
        
        # Record stock movement
        movement = StockMovement(
            medicine_id=medicine.id,
            user_id=current_user.id,
            movement_type='ADD',
            quantity=quantity,
            reason='Initial stock addition'
        )
        
        db.session.add(movement)
        db.session.commit()
        
        flash(f'Medicine {name} added successfully with {quantity} units.', 'success')
        return redirect(url_for('stock.view_medicine', medicine_id=medicine.id))
    
    return render_template('stock/add_medicine.html')


@stock_bp.route('/<int:medicine_id>')
@role_required('H2', 'Director')
def view_medicine(medicine_id):
    """View medicine details and stock history"""
    medicine = Medicine.query.get_or_404(medicine_id)
    movements = medicine.stock_movements
    
    return render_template('stock/view_medicine.html', medicine=medicine, movements=movements)


@stock_bp.route('/<int:medicine_id>/edit', methods=['GET', 'POST'])
@role_required('H2', 'Director')
def edit_medicine(medicine_id):
    """Edit medicine details"""
    medicine = Medicine.query.get_or_404(medicine_id)
    
    if request.method == 'POST':
        medicine.generic_name = request.form.get('generic_name')
        medicine.dosage = request.form.get('dosage')
        medicine.min_stock_level = request.form.get('min_stock_level', type=int)
        medicine.unit = request.form.get('unit')
        
        # Convert expiry_date string to date object if provided
        expiry_date = request.form.get('expiry_date')
        if expiry_date:
            medicine.expiry_date = datetime.strptime(expiry_date, '%Y-%m-%d').date()
        
        medicine.supplier = request.form.get('supplier')
        medicine.cost_per_unit = request.form.get('cost_per_unit', type=float)
        medicine.location = request.form.get('location')
        
        db.session.commit()
        flash('Medicine updated successfully.', 'success')
        return redirect(url_for('stock.view_medicine', medicine_id=medicine.id))
    
    return render_template('stock/edit_medicine.html', medicine=medicine)


@stock_bp.route('/<int:medicine_id>/adjust-stock', methods=['POST'])
@role_required('H2', 'Director')
def adjust_stock(medicine_id):
    """Adjust medicine stock"""
    medicine = Medicine.query.get_or_404(medicine_id)
    
    quantity = request.form.get('quantity', type=int)
    movement_type = request.form.get('movement_type')  # ADD, DISPENSE, LOSS
    reason = request.form.get('reason')
    
    if movement_type == 'ADD':
        medicine.quantity += quantity
    elif movement_type in ['DISPENSE', 'LOSS']:
        if medicine.quantity < quantity:
            flash('Insufficient stock available.', 'danger')
            return redirect(url_for('stock.view_medicine', medicine_id=medicine.id))
        medicine.quantity -= quantity
    
    # Record stock movement
    movement = StockMovement(
        medicine_id=medicine.id,
        user_id=current_user.id,
        movement_type=movement_type,
        quantity=quantity,
        reason=reason
    )
    
    db.session.add(movement)
    db.session.commit()
    
    flash(f'Stock adjusted: {movement_type} {quantity} units.', 'success')
    return redirect(url_for('stock.view_medicine', medicine_id=medicine.id))


@stock_bp.route('/low-stock-alerts')
@role_required('H2', 'Director')
def low_stock_alerts():
    """View low stock alerts"""
    medicines = Medicine.query.filter(Medicine.quantity <= Medicine.min_stock_level).all()
    
    return render_template('stock/low_stock_alerts.html', medicines=medicines)


@stock_bp.route('/stock-history')
@role_required('H2', 'Director')
def stock_history():
    """View stock movement history"""
    page = request.args.get('page', 1, type=int)
    medicine_id = request.args.get('medicine_id', type=int)
    movement_type = request.args.get('movement_type', '')
    
    query = StockMovement.query
    
    if medicine_id:
        query = query.filter_by(medicine_id=medicine_id)
    
    if movement_type:
        query = query.filter_by(movement_type=movement_type)
    
    movements = query.order_by(StockMovement.created_at.desc()).paginate(page=page, per_page=50)
    
    return render_template('stock/stock_history.html', movements=movements, medicine_id=medicine_id)


@stock_bp.route('/<int:medicine_id>/delete', methods=['POST'])
@role_required('Director')
def delete_medicine(medicine_id):
    """Delete medicine (Director only)"""
    medicine = Medicine.query.get_or_404(medicine_id)
    medicine_name = medicine.name
    
    db.session.delete(medicine)
    db.session.commit()
    
    flash(f'Medicine {medicine_name} has been deleted.', 'success')
    return redirect(url_for('stock.inventory'))
