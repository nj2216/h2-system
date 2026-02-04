"""
Medical stock management blueprint routes
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import current_user, login_required
from datetime import datetime
from ..extensions import db
from app.models import Medicine, StockMovement, MedicineBatch
from app.auth.utils import role_required
import csv
import io

stock_bp = Blueprint('stock', __name__, template_folder='../templates/stock')


@stock_bp.route('/')
@role_required('H2', 'Director')
def inventory():
    """View medicine inventory (based on non-expired batches only)"""
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    show_low = request.args.get('low_stock', 'false').lower() == 'true'
    
    query = Medicine.query
    
    if search:
        query = query.filter(Medicine.name.ilike(f'%{search}%'))
    
    medicines = query.order_by(Medicine.name).all()
    
    # Filter by low stock using property (excludes expired batches)
    if show_low:
        medicines = [m for m in medicines if m.is_low_stock]
    
    # Manual pagination since we're filtering in Python
    total = len(medicines)
    per_page = 20
    start = (page - 1) * per_page
    end = start + per_page
    medicines_page = medicines[start:end]
    
    # Create a simple pagination object
    class SimplePage:
        def __init__(self, items, page, per_page, total):
            self.items = items
            self.pages = (total + per_page - 1) // per_page
            self.prev_num = page - 1 if page > 1 else None
            self.next_num = page + 1 if page < self.pages else None
            self.has_prev = page > 1
            self.has_next = page < self.pages
    
    medicines = SimplePage(medicines_page, page, per_page, total)
    
    return render_template('stock/inventory.html', medicines=medicines, search=search, show_low=show_low)


@stock_bp.route('/add-medicine', methods=['GET', 'POST'])
@role_required('H2', 'Director')
def add_medicine():
    """Add new medicine to inventory with batch tracking"""
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
        batch_number = request.form.get('batch_number')
        shelf_location = request.form.get('shelf_location')
        
        if Medicine.query.filter_by(name=name).first():
            flash('Medicine name already exists.', 'danger')
            return redirect(url_for('stock.add_medicine'))
        
        # Validate batch information
        if not batch_number or not shelf_location or not expiry_date:
            flash('Batch number, shelf location, and expiry date are required.', 'danger')
            return redirect(url_for('stock.add_medicine'))
        
        # Convert expiry_date string to date object
        try:
            expiry_date_obj = datetime.strptime(expiry_date, '%Y-%m-%d').date()
        except ValueError:
            flash('Invalid expiry date format. Use YYYY-MM-DD.', 'danger')
            return redirect(url_for('stock.add_medicine'))
        
        # Create medicine
        medicine = Medicine(
            name=name,
            generic_name=generic_name,
            dosage=dosage,
            quantity=0,  # Will be tracked via batches
            min_stock_level=min_stock_level,
            unit=unit,
            supplier=supplier,
            cost_per_unit=cost_per_unit
        )
        
        db.session.add(medicine)
        db.session.flush()
        
        # Create initial batch
        batch = MedicineBatch(
            medicine_id=medicine.id,
            batch_number=batch_number,
            quantity=quantity,
            available_quantity=quantity,
            expiry_date=expiry_date_obj,
            shelf_location=shelf_location,
            cost_per_unit=cost_per_unit
        )
        
        db.session.add(batch)
        db.session.flush()
        
        # Update medicine quantity
        medicine.quantity = quantity
        
        # Record stock movement
        movement = StockMovement(
            medicine_id=medicine.id,
            user_id=current_user.id,
            movement_type='ADD',
            quantity=quantity,
            reason=f'Initial batch addition - Batch: {batch_number} (Shelf: {shelf_location})'
        )
        
        db.session.add(movement)
        db.session.commit()
        
        flash(f'Medicine {name} added successfully with batch {batch_number} ({quantity} units).', 'success')
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
    """View low stock alerts (based on non-expired batches only)"""
    # Get all medicines and filter by low stock using property (excludes expired batches)
    all_medicines = Medicine.query.all()
    medicines = [m for m in all_medicines if m.is_low_stock]
    
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
            
            # Expected columns: name, quantity, batch_number, shelf_location, expiry_date (required)
            # Optional: generic_name, dosage, min_stock_level, unit, supplier, cost_per_unit
            required_fields = ['name', 'quantity', 'batch_number', 'shelf_location', 'expiry_date']
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
                    batch_number = row.get('batch_number', '').strip()
                    shelf_location = row.get('shelf_location', '').strip()
                    expiry_date_str = row.get('expiry_date', '').strip()
                    
                    if not name or not quantity or not batch_number or not shelf_location or not expiry_date_str:
                        errors.append(f'Row {row_num}: Missing required fields (name, quantity, batch_number, shelf_location, expiry_date)')
                        continue
                    
                    try:
                        quantity = int(quantity)
                    except ValueError:
                        errors.append(f'Row {row_num}: Quantity must be a number')
                        continue
                    
                    if quantity <= 0:
                        errors.append(f'Row {row_num}: Quantity must be greater than 0')
                        continue
                    
                    # Parse expiry date first
                    try:
                        expiry_date = datetime.strptime(expiry_date_str, '%Y-%m-%d').date()
                    except ValueError:
                        errors.append(f'Row {row_num}: Invalid expiry_date format (use YYYY-MM-DD)')
                        continue
                    
                    # Check if medicine exists
                    medicine = Medicine.query.filter_by(name=name).first()
                    
                    if not medicine:
                        # Create new medicine if it doesn't exist
                        medicine = Medicine(
                            name=name,
                            generic_name=row.get('generic_name', '').strip(),
                            dosage=row.get('dosage', '').strip(),
                            quantity=0,  # Will be tracked via batches
                            min_stock_level=int(row.get('min_stock_level', 10)) if row.get('min_stock_level', '').strip() else 10,
                            unit=row.get('unit', '').strip() or 'units',
                            supplier=row.get('supplier', '').strip(),
                            cost_per_unit=float(row.get('cost_per_unit', 0)) if row.get('cost_per_unit', '').strip() else None
                        )
                        db.session.add(medicine)
                        db.session.flush()
                        created += 1
                    else:
                        # Update optional fields if provided (only if not already set)
                        if row.get('generic_name', '').strip() and not medicine.generic_name:
                            medicine.generic_name = row.get('generic_name').strip()
                        if row.get('dosage', '').strip() and not medicine.dosage:
                            medicine.dosage = row.get('dosage').strip()
                        if row.get('min_stock_level', '').strip():
                            try:
                                medicine.min_stock_level = int(row.get('min_stock_level').strip())
                            except ValueError:
                                pass
                        if row.get('unit', '').strip() and not medicine.unit:
                            medicine.unit = row.get('unit').strip()
                        if row.get('supplier', '').strip() and not medicine.supplier:
                            medicine.supplier = row.get('supplier').strip()
                        if row.get('cost_per_unit', '').strip():
                            try:
                                medicine.cost_per_unit = float(row.get('cost_per_unit').strip())
                            except ValueError:
                                pass
                        db.session.flush()
                        updated += 1
                    
                    # Check if batch already exists
                    existing_batch = MedicineBatch.query.filter_by(
                        medicine_id=medicine.id,
                        batch_number=batch_number
                    ).first()
                    
                    if existing_batch:
                        # Update existing batch
                        old_qty = existing_batch.available_quantity
                        existing_batch.quantity += quantity
                        existing_batch.available_quantity += quantity
                        existing_batch.expiry_date = expiry_date
                        existing_batch.shelf_location = shelf_location
                        if row.get('cost_per_unit', '').strip():
                            try:
                                existing_batch.cost_per_unit = float(row.get('cost_per_unit').strip())
                            except ValueError:
                                pass
                        db.session.flush()
                    else:
                        # Create new batch
                        batch = MedicineBatch(
                            medicine_id=medicine.id,
                            batch_number=batch_number,
                            quantity=quantity,
                            available_quantity=quantity,
                            expiry_date=expiry_date,
                            shelf_location=shelf_location,
                            cost_per_unit=float(row.get('cost_per_unit', 0)) if row.get('cost_per_unit', '').strip() else None
                        )
                        db.session.add(batch)
                        db.session.flush()
                    
                    # Update medicine's aggregate quantity (for backward compatibility)
                    medicine.quantity = sum(b.available_quantity for b in medicine.batches)
                    
                    # Record stock movement for batch addition
                    movement = StockMovement(
                        medicine_id=medicine.id,
                        user_id=current_user.id,
                        movement_type='ADD',
                        quantity=quantity,
                        reason=f'Bulk stock arrival - Batch: {batch_number} (Shelf: {shelf_location})'
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
