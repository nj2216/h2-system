"""
System Health Module for H2 System
Provides endpoints for monitoring runtime health, environment specs, and log dumps.
"""
from app.system_health.routes import system_health_bp
from app.system_health.services import init_logging

__all__ = ['system_health_bp', 'init_logging']
