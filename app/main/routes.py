"""
Main blueprint routes for landing page and public pages
"""
from flask import Blueprint, render_template
from flask_login import login_required

main_bp = Blueprint('main', __name__, template_folder='../templates')


@main_bp.route('/')
def index():
    """Home page / Landing page"""
    return render_template('index.html')


@main_bp.route('/about')
def about():
    """About page (same as index for now)"""
    return render_template('index.html')
