"""
Hostel asset management blueprint routes
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import current_user, login_required
from datetime import datetime
from ..extensions import db
from app.models import Asset, MaintenanceLog
from app.auth.utils import role_required

assets_bp = Blueprint('assets', __name__, template_folder='../templates/assets')


@assets_bp.route('/')
@role_required('Warden', 'H2', 'Director')
def assets_list():
    """List all assets"""
    page = request.args.get('page', 1, type=int)
    category = request.args.get('category', '')
    location = request.args.get('location', '')
    condition = request.args.get('condition', '')
    
    query = Asset.query
    
    if category:
        query = query.filter_by(category=category)
    
    if location:
        query = query.filter_by(location=location)
    
    if condition:
        query = query.filter_by(condition=condition)
    
    assets = query.order_by(Asset.asset_code).paginate(page=page, per_page=20)
    
    # Get unique values for filters
    categories = db.session.query(Asset.category).distinct().all()
    locations = db.session.query(Asset.location).distinct().all()
    conditions = db.session.query(Asset.condition).distinct().all()
    
    return render_template('assets/list.html', 
                          assets=assets,
                          categories=[c[0] for c in categories],
                          locations=[l[0] for l in locations],
                          conditions=[c[0] for c in conditions],
                          selected_category=category,
                          selected_location=location,
                          selected_condition=condition)


@assets_bp.route('/add', methods=['GET', 'POST'])
@role_required('Warden', 'Director')
def add_asset():
    """Add new asset"""
    if request.method == 'POST':
        asset_code = request.form.get('asset_code')
        name = request.form.get('name')
        category = request.form.get('category')
        description = request.form.get('description')
        location = request.form.get('location')
        quantity = request.form.get('quantity', 1, type=int)
        condition = request.form.get('condition', 'Good')
        purchase_date = request.form.get('purchase_date')
        cost = request.form.get('cost', type=float)
        warranty_expiry = request.form.get('warranty_expiry')
        
        if Asset.query.filter_by(asset_code=asset_code).first():
            flash('Asset code already exists.', 'danger')
            return redirect(url_for('assets.add_asset'))
        
        # Convert date strings to date objects if provided
        if purchase_date:
            purchase_date = datetime.strptime(purchase_date, '%Y-%m-%d').date()
        if warranty_expiry:
            warranty_expiry = datetime.strptime(warranty_expiry, '%Y-%m-%d').date()
        
        asset = Asset(
            asset_code=asset_code,
            name=name,
            category=category,
            description=description,
            location=location,
            quantity=quantity,
            condition=condition,
            purchase_date=purchase_date,
            cost=cost,
            warranty_expiry=warranty_expiry
        )
        
        db.session.add(asset)
        db.session.commit()
        
        flash(f'Asset {asset_code} added successfully.', 'success')
        return redirect(url_for('assets.view_asset', asset_id=asset.id))
    
    return render_template('assets/add.html')


@assets_bp.route('/<int:asset_id>')
@role_required('Warden', 'H2', 'Director')
def view_asset(asset_id):
    """View asset details and maintenance history"""
    asset = Asset.query.get_or_404(asset_id)
    maintenance_logs = asset.maintenance_logs
    
    return render_template('assets/view.html', asset=asset, maintenance_logs=maintenance_logs)


@assets_bp.route('/<int:asset_id>/edit', methods=['GET', 'POST'])
@role_required('Warden', 'Director')
def edit_asset(asset_id):
    """Edit asset details"""
    asset = Asset.query.get_or_404(asset_id)
    
    if request.method == 'POST':
        asset.name = request.form.get('name')
        asset.category = request.form.get('category')
        asset.description = request.form.get('description')
        asset.location = request.form.get('location')
        asset.quantity = request.form.get('quantity', type=int)
        asset.condition = request.form.get('condition')
        
        # Convert date strings to date objects if provided
        purchase_date = request.form.get('purchase_date')
        if purchase_date:
            asset.purchase_date = datetime.strptime(purchase_date, '%Y-%m-%d').date()
        
        asset.cost = request.form.get('cost', type=float)
        
        warranty_expiry = request.form.get('warranty_expiry')
        if warranty_expiry:
            asset.warranty_expiry = datetime.strptime(warranty_expiry, '%Y-%m-%d').date()
        
        db.session.commit()
        flash('Asset updated successfully.', 'success')
        return redirect(url_for('assets.view_asset', asset_id=asset.id))
    
    return render_template('assets/edit.html', asset=asset)


@assets_bp.route('/<int:asset_id>/maintenance', methods=['GET', 'POST'])
@role_required('Warden', 'Director')
def add_maintenance_log(asset_id):
    """Add maintenance log for asset"""
    asset = Asset.query.get_or_404(asset_id)
    
    if request.method == 'POST':
        issue_description = request.form.get('issue_description')
        action_taken = request.form.get('action_taken')
        cost = request.form.get('cost', type=float)
        status = request.form.get('status', 'Completed')
        
        log = MaintenanceLog(
            asset_id=asset_id,
            issue_description=issue_description,
            action_taken=action_taken,
            cost=cost,
            status=status
        )
        
        db.session.add(log)
        db.session.commit()
        
        flash('Maintenance log added successfully.', 'success')
        return redirect(url_for('assets.view_asset', asset_id=asset.id))
    
    return render_template('assets/add_maintenance.html', asset=asset)


@assets_bp.route('/<int:asset_id>/delete', methods=['POST'])
@role_required('Director')
def delete_asset(asset_id):
    """Delete asset (Director only)"""
    asset = Asset.query.get_or_404(asset_id)
    asset_code = asset.asset_code
    
    db.session.delete(asset)
    db.session.commit()
    
    flash(f'Asset {asset_code} has been deleted.', 'success')
    return redirect(url_for('assets.assets_list'))


@assets_bp.route('/condition-report')
@role_required('Warden', 'H2', 'Director')
def condition_report():
    """View assets grouped by condition"""
    assets_by_condition = {}
    conditions = ['Good', 'Fair', 'Poor', 'Damaged']
    
    for condition in conditions:
        assets_by_condition[condition] = Asset.query.filter_by(condition=condition).all()
    
    return render_template('assets/condition_report.html', assets_by_condition=assets_by_condition)


@assets_bp.route('/maintenance-logs')
@role_required('Warden', 'H2', 'Director')
def maintenance_logs():
    """View all maintenance logs"""
    page = request.args.get('page', 1, type=int)
    status = request.args.get('status', '')
    
    query = MaintenanceLog.query
    
    if status:
        query = query.filter_by(status=status)
    
    logs = query.order_by(MaintenanceLog.maintenance_date.desc()).paginate(page=page, per_page=50)
    
    return render_template('assets/maintenance_logs.html', logs=logs, status=status)
