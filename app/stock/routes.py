"""
Medical stock management blueprint routes
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import current_user, login_required
from datetime import datetime
from ..extensions import db
from app.models import Medicine, StockMovement
from app.auth.utils import role_required
import csv
import io

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


@stock_bp.route('/bulk-upload', methods=['GET', 'POST'])
@role_required('H2', 'Director')
def bulk_upload_medicines():
    """Bulk upload medicines from CSV file for new stock arrivals"""
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file part in the request.', 'danger')
            return redirect(url_for('stock.bulk_upload_medicines'))
        
        file = request.files['file']
        
        if file.filename == '':
            flash('No selected file.', 'danger')
            return redirect(url_for('stock.bulk_upload_medicines'))
        
        if not file.filename.endswith(('.csv', '.txt')):
            flash('Please upload a CSV or TXT file.', 'danger')
            return redirect(url_for('stock.bulk_upload_medicines'))
        
        try:
            # Read file
            stream = io.StringIO(file.read().decode('UTF-8'), newline=None)
            csv_reader = csv.DictReader(stream)
            
            if not csv_reader.fieldnames:
                flash('CSV file is empty.', 'danger')
                return redirect(url_for('stock.bulk_upload_medicines'))
            
            # Expected columns: name, generic_name, dosage, quantity, min_stock_level, unit,
            # expiry_date, supplier, cost_per_unit, location
            required_fields = ['name', 'quantity']
            missing_fields = [field for field in required_fields if field not in csv_reader.fieldnames]
            
            if missing_fields:
                flash(f'Missing required columns: {", ".join(missing_fields)}', 'danger')
                return redirect(url_for('stock.bulk_upload_medicines'))
            
            created = 0
            updated = 0
            errors = []
            
            for row_num, row in enumerate(csv_reader, start=2):  # Start at 2 (after header)
                try:
                    name = row.get('name', '').strip()
                    quantity = row.get('quantity', '').strip()
                    
                    if not name or not quantity:
                        errors.append(f'Row {row_num}: Missing name or quantity')
                        continue
                    
                    try:
                        quantity = int(quantity)
                    except ValueError:
                        errors.append(f'Row {row_num}: Quantity must be a number')
                        continue
                    
                    if quantity <= 0:
                        errors.append(f'Row {row_num}: Quantity must be greater than 0')
                        continue
                    
                    # Check if medicine exists
                    medicine = Medicine.query.filter_by(name=name).first()
                    
                    if medicine:
                        # Update existing medicine
                        old_quantity = medicine.quantity
                        medicine.quantity += quantity
                        
                        # Update optional fields if provided
                        if row.get('generic_name', '').strip():
                            medicine.generic_name = row.get('generic_name').strip()
                        if row.get('dosage', '').strip():
                            medicine.dosage = row.get('dosage').strip()
                        if row.get('min_stock_level', '').strip():
                            try:
                                medicine.min_stock_level = int(row.get('min_stock_level').strip())
                            except ValueError:
                                pass
                        if row.get('unit', '').strip():
                            medicine.unit = row.get('unit').strip()
                        if row.get('supplier', '').strip():
                            medicine.supplier = row.get('supplier').strip()
                        if row.get('cost_per_unit', '').strip():
                            try:
                                medicine.cost_per_unit = float(row.get('cost_per_unit').strip())
                            except ValueError:
                                pass
                        if row.get('location', '').strip():
                            medicine.location = row.get('location').strip()
                        
                        # Parse expiry date if provided
                        if row.get('expiry_date', '').strip():
                            try:
                                medicine.expiry_date = datetime.strptime(row.get('expiry_date'), '%Y-%m-%d').date()
                            except ValueError:
                                errors.append(f'Row {row_num}: Invalid date format for expiry_date')
                                continue
                        
                        db.session.flush()
                        updated += 1
                        
                    else:
                        # Create new medicine
                        medicine = Medicine(
                            name=name,
                            generic_name=row.get('generic_name', '').strip(),
                            dosage=row.get('dosage', '').strip(),
                            quantity=quantity,
                            min_stock_level=int(row.get('min_stock_level', 10)) if row.get('min_stock_level', '').strip() else 10,
                            unit=row.get('unit', '').strip() or 'units',
                            supplier=row.get('supplier', '').strip(),
                            cost_per_unit=float(row.get('cost_per_unit', 0)) if row.get('cost_per_unit', '').strip() else None,
                            location=row.get('location', '').strip()
                        )
                        
                        # Parse expiry date if provided
                        if row.get('expiry_date', '').strip():
                            try:
                                medicine.expiry_date = datetime.strptime(row.get('expiry_date'), '%Y-%m-%d').date()
                            except ValueError:
                                errors.append(f'Row {row_num}: Invalid date format for expiry_date')
                                continue
                        
                        db.session.add(medicine)
                        db.session.flush()
                        created += 1
                    
                    # Record stock movement for new arrivals
                    movement = StockMovement(
                        medicine_id=medicine.id,
                        user_id=current_user.id,
                        movement_type='ADD',
                        quantity=quantity,
                        reason='Bulk stock arrival'
                    )
                    db.session.add(movement)
                
                except Exception as e:
                    errors.append(f'Row {row_num}: {str(e)}')
            
            # Commit all successful entries
            if created > 0 or updated > 0:
                db.session.commit()
                flash(f'Successfully created {created} new medicine(s) and updated {updated} existing medicine(s).', 'success')
            
            if errors:
                error_msg = '<br>'.join(errors[:10])  # Show first 10 errors
                if len(errors) > 10:
                    error_msg += f'<br>... and {len(errors) - 10} more errors'
                flash(f'Encountered {len(errors)} error(s):<br>{error_msg}', 'warning')
            
            return redirect(url_for('stock.inventory'))
        
        except Exception as e:
            flash(f'Error processing file: {str(e)}', 'danger')
            return redirect(url_for('stock.bulk_upload_medicines'))
    
    return render_template('stock/bulk_upload.html')
