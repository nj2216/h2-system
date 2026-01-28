"""
Flask application factory for H2 System
"""
import os
from flask import Flask
from config import config
from .extensions import db, login_manager


def create_app(config_name=None):
    """
    Application factory function
    
    Args:
        config_name: Configuration name (development, testing, production)
    
    Returns:
        Flask application instance
    """
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')
    
    # Create Flask app
    app = Flask(__name__, instance_relative_config=False)
    
    # Load configuration
    app.config.from_object(config[config_name])
    
    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    
    # Register user loader for Flask-Login
    from app.models import User
    
    @login_manager.user_loader
    def load_user(user_id):
        """Load user by ID for Flask-Login"""
        return User.query.get(int(user_id))
    
    # Register error handlers
    register_error_handlers(app)
    
    # Register blueprints
    register_blueprints(app)
    
    # Create database tables
    with app.app_context():
        db.create_all()
    
    return app


def register_blueprints(app):
    """Register all application blueprints"""
    from app.auth.routes import auth_bp
    from app.students.routes import students_bp
    from app.health.routes import health_bp
    from app.stock.routes import stock_bp
    from app.assets.routes import assets_bp
    from app.sickleave.routes import sickleave_bp
    from app.dashboards.routes import dashboards_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(students_bp, url_prefix='/students')
    app.register_blueprint(health_bp, url_prefix='/health')
    app.register_blueprint(stock_bp, url_prefix='/stock')
    app.register_blueprint(assets_bp, url_prefix='/assets')
    app.register_blueprint(sickleave_bp, url_prefix='/sickleave')
    app.register_blueprint(dashboards_bp, url_prefix='/dashboard')


def register_error_handlers(app):
    """Register error handlers"""
    
    @app.errorhandler(403)
    def forbidden(e):
        return {'error': 'Forbidden', 'message': 'You do not have permission to access this resource'}, 403
    
    @app.errorhandler(404)
    def not_found(e):
        return {'error': 'Not Found', 'message': 'The requested resource was not found'}, 404
    
    @app.errorhandler(500)
    def internal_error(e):
        db.session.rollback()
        return {'error': 'Internal Server Error', 'message': 'An unexpected error occurred'}, 500


if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
