"""
Flask application factory for H2 System
"""
import os
from flask import Flask, redirect
from config import config
from .extensions import db, login_manager
from flask import redirect, url_for


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
    
    # Initialize application logging and in-memory log buffer
    from app.system_health.services import init_logging
    init_logging(app)
    
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
    
    # Ensure database schema is up-to-date
    with app.app_context():
        db.create_all()
        try:
            from sqlalchemy import inspect, text
            inspector = inspect(db.engine)
            if 'equipment_issues' in inspector.get_table_names():
                existing_cols = {col['name'] for col in inspector.get_columns('equipment_issues')}
                new_cols = [
                    ('penalty_overridden', 'BOOLEAN DEFAULT 0'),
                    ('original_penalty_amount', 'FLOAT DEFAULT 0.0'),
                    ('penalty_override_reason', 'TEXT'),
                    ('penalty_overridden_by_id', 'INTEGER REFERENCES users(id)'),
                    ('penalty_overridden_at', 'DATETIME')
                ]
                for col_name, col_type in new_cols:
                    if col_name not in existing_cols:
                        db.session.execute(text(f'ALTER TABLE equipment_issues ADD COLUMN {col_name} {col_type}'))
                db.session.commit()
        except Exception:
            db.session.rollback()
    
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
    from app.main.routes import main_bp
    from app.equipment import equipment_bp
    from app.system_health.routes import system_health_bp
    
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(students_bp, url_prefix='/students')
    app.register_blueprint(health_bp, url_prefix='/health')
    app.register_blueprint(stock_bp, url_prefix='/stock')
    app.register_blueprint(assets_bp, url_prefix='/assets')
    app.register_blueprint(sickleave_bp, url_prefix='/sickleave')
    app.register_blueprint(dashboards_bp, url_prefix='/dashboard')
    app.register_blueprint(equipment_bp)
    app.register_blueprint(system_health_bp, url_prefix='/system-health')


def register_error_handlers(app):
    """Register error handlers"""
    from flask import render_template
    
    @app.errorhandler(403)
    def forbidden(e):
        return redirect(url_for('auth.login'))
    
    @app.errorhandler(404)
    def not_found(e):
        return render_template('404.html'), 404
    
    @app.errorhandler(500)
    def internal_error(e):
        db.session.rollback()
        return {'error': 'Internal Server Error', 'message': 'An unexpected error occurred'}, 500


if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
