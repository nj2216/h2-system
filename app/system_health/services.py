"""
System Health and Diagnostics Services for H2 System
Collects real-time runtime metrics, environment data, database health, and log buffers.
"""
import os
import sys
import time
import shutil
import platform
import resource
import logging
import threading
import io
import json
import zipfile
from datetime import datetime, timezone
from collections import deque
from logging.handlers import RotatingFileHandler
from sqlalchemy import text
from flask import current_app
from app.extensions import db


# Track server start time
SERVER_START_TIME = datetime.now(timezone.utc)

# Thread-safe in-memory log buffer
MAX_LOG_BUFFER_SIZE = 1000
_log_buffer_lock = threading.Lock()
_in_memory_log_buffer = deque(maxlen=MAX_LOG_BUFFER_SIZE)
_logging_initialized = False


class InMemoryLogHandler(logging.Handler):
    """Logging handler that retains the latest N log records in memory"""
    def emit(self, record):
        try:
            log_entry = {
                'timestamp': datetime.fromtimestamp(record.created, timezone.utc).isoformat(),
                'level': record.levelname,
                'logger': record.name,
                'message': self.format(record),
                'module': record.module,
                'line': record.lineno
            }
            with _log_buffer_lock:
                _in_memory_log_buffer.append(log_entry)
        except Exception:
            self.handleError(record)


def init_logging(app):
    """
    Initialize logging for H2 System with both rotating file and memory buffer.
    """
    global _logging_initialized
    if _logging_initialized:
        return

    # Determine log directory
    log_dir = os.path.join(app.root_path, '..', 'logs')
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, 'h2_system.log')

    formatter = logging.Formatter(
        '%(asctime)s [%(levelname)s] [%(name)s] %(message)s'
    )

    # 1. Rotating File Handler (10 MB, up to 5 backups)
    try:
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=10 * 1024 * 1024,
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setFormatter(formatter)
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        logging.getLogger().addHandler(file_handler)
    except Exception as e:
        print(f"Warning: Could not initialize rotating file logger: {e}", file=sys.stderr)

    # 2. In-memory circular buffer handler
    memory_handler = InMemoryLogHandler()
    memory_handler.setFormatter(formatter)
    memory_handler.setLevel(logging.DEBUG if app.debug else logging.INFO)
    app.logger.addHandler(memory_handler)
    logging.getLogger().addHandler(memory_handler)

    # Ensure log level is active
    app.logger.setLevel(logging.DEBUG if app.debug else logging.INFO)
    _logging_initialized = True

    app.logger.info("H2 System Health Monitor & Logging Service initialized.")


def mask_connection_uri(uri):
    """Safely mask passwords in database URIs"""
    if not uri:
        return 'N/A'
    if '://' in uri:
        try:
            proto, rest = uri.split('://', 1)
            if '@' in rest:
                creds, host = rest.split('@', 1)
                if ':' in creds:
                    user, _ = creds.split(':', 1)
                    return f"{proto}://{user}:***@{host}"
                return f"{proto}://***@{host}"
            return uri
        except Exception:
            return '***'
    return uri


def get_memory_info():
    """Extract system RAM info from /proc/meminfo or fallback to resource rusage"""
    mem_data = {
        'total_mb': None,
        'available_mb': None,
        'used_mb': None,
        'percent': None,
        'process_rss_mb': None
    }

    # Process RSS
    try:
        # On Linux ru_maxrss is in Kilobytes
        rss_kb = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        mem_data['process_rss_mb'] = round(rss_kb / 1024, 2)
    except Exception:
        pass

    # System RAM on Linux
    if os.path.exists('/proc/meminfo'):
        try:
            meminfo = {}
            with open('/proc/meminfo', 'r') as f:
                for line in f:
                    parts = line.split(':')
                    if len(parts) == 2:
                        meminfo[parts[0].strip()] = parts[1].strip()
            total_kb = int(meminfo.get('MemTotal', '0 kB').split()[0])
            available_kb = int(meminfo.get('MemAvailable', '0 kB').split()[0])
            free_kb = int(meminfo.get('MemFree', '0 kB').split()[0])

            total_mb = round(total_kb / 1024, 1)
            available_mb = round(available_kb / 1024, 1) if available_kb else round(free_kb / 1024, 1)
            used_mb = round(total_mb - available_mb, 1)
            percent = round((used_mb / total_mb) * 100, 1) if total_mb else 0

            mem_data.update({
                'total_mb': total_mb,
                'available_mb': available_mb,
                'used_mb': used_mb,
                'percent': percent
            })
        except Exception:
            pass

    return mem_data


def get_disk_info(path=None):
    """Get disk usage for the host partition"""
    if path is None:
        path = os.getcwd()
    try:
        total, used, free = shutil.disk_usage(path)
        return {
            'path': path,
            'total_gb': round(total / (1024 ** 3), 2),
            'used_gb': round(used / (1024 ** 3), 2),
            'free_gb': round(free / (1024 ** 3), 2),
            'percent_used': round((used / total) * 100, 1) if total else 0
        }
    except Exception as e:
        return {'path': path, 'error': str(e)}


def check_database_health():
    """Check database connectivity, response time, and record stats"""
    start_time = time.perf_counter()
    db_result = {
        'status': 'UNKNOWN',
        'latency_ms': None,
        'dialect': None,
        'connection_uri': mask_connection_uri(current_app.config.get('SQLALCHEMY_DATABASE_URI', '')),
        'table_counts': {},
        'error': None
    }

    try:
        # Check dialect
        db_result['dialect'] = db.engine.dialect.name
        
        # Ping with SELECT 1
        db.session.execute(text('SELECT 1'))
        latency = (time.perf_counter() - start_time) * 1000
        db_result['latency_ms'] = round(latency, 2)
        db_result['status'] = 'CONNECTED'

        # Gather table counts
        from app.models import (
            User, Student, Medicine, DoctorVisit, Prescription,
            PrescriptionItem, MedicalEquipment, EquipmentIssue, SickLeaveRequest
        )
        
        counts = {
            'users': User.query.count(),
            'students': Student.query.count(),
            'medicines': Medicine.query.count(),
            'doctor_visits': DoctorVisit.query.count(),
            'prescriptions': Prescription.query.count(),
            'prescription_items': PrescriptionItem.query.count(),
            'equipment': MedicalEquipment.query.count(),
            'equipment_issues': EquipmentIssue.query.count(),
            'sickleave_requests': SickLeaveRequest.query.count()
        }
        db_result['table_counts'] = counts

    except Exception as e:
        db_result['status'] = 'ERROR'
        db_result['error'] = str(e)
        db_result['latency_ms'] = round((time.perf_counter() - start_time) * 1000, 2)

    return db_result


def format_uptime(seconds):
    """Format duration in seconds into human-readable string"""
    seconds = int(seconds)
    days, seconds = divmod(seconds, 86400)
    hours, seconds = divmod(seconds, 3600)
    minutes, seconds = divmod(seconds, 60)

    parts = []
    if days > 0:
        parts.append(f"{days}d")
    if hours > 0:
        parts.append(f"{hours}h")
    if minutes > 0:
        parts.append(f"{minutes}m")
    parts.append(f"{seconds}s")
    return " ".join(parts)


def get_system_health():
    """
    Collect comprehensive system health and environment diagnostics.
    """
    now_utc = datetime.now(timezone.utc)
    uptime_seconds = int((now_utc - SERVER_START_TIME).total_seconds())

    # CPU load average if available (Unix)
    load_avg = None
    if hasattr(os, 'getloadavg'):
        try:
            load_avg = [round(x, 2) for x in os.getloadavg()]
        except Exception:
            pass

    # Database
    db_health = check_database_health()

    # Memory & Disk
    mem_info = get_memory_info()
    disk_info = get_disk_info()

    # Determine overall health status
    overall_status = 'HEALTHY'
    status_reasons = []

    if db_health['status'] != 'CONNECTED':
        overall_status = 'CRITICAL'
        status_reasons.append(f"Database error: {db_health.get('error') or 'Not connected'}")
    elif db_health['latency_ms'] and db_health['latency_ms'] > 1000:
        overall_status = 'DEGRADED'
        status_reasons.append("High database query latency (> 1000ms)")

    if disk_info.get('percent_used', 0) > 92:
        overall_status = 'CRITICAL' if overall_status != 'CRITICAL' else overall_status
        status_reasons.append(f"Critical disk usage: {disk_info.get('percent_used')}%")
    elif disk_info.get('percent_used', 0) > 85:
        if overall_status == 'HEALTHY':
            overall_status = 'DEGRADED'
        status_reasons.append(f"High disk usage: {disk_info.get('percent_used')}%")

    if mem_info.get('percent') and mem_info['percent'] > 95:
        if overall_status == 'HEALTHY':
            overall_status = 'DEGRADED'
        status_reasons.append(f"High memory usage: {mem_info.get('percent')}%")

    # Registered Blueprints
    blueprints = sorted(list(current_app.blueprints.keys()))

    return {
        'status': overall_status,
        'status_reasons': status_reasons,
        'timestamp': now_utc.isoformat(),
        'timestamp_local': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'server_start_time': SERVER_START_TIME.isoformat(),
        'uptime_seconds': uptime_seconds,
        'uptime_formatted': format_uptime(uptime_seconds),
        'database': db_health,
        'environment': {
            'app_name': 'H2 System (Health & Hostel Management)',
            'env': os.environ.get('FLASK_ENV', 'development'),
            'debug': current_app.debug,
            'testing': current_app.testing,
            'python_version': platform.python_version(),
            'python_implementation': platform.python_implementation(),
            'python_executable': sys.executable,
            'platform': platform.platform(),
            'os_name': platform.system(),
            'os_release': platform.release(),
            'architecture': platform.machine(),
            'hostname': platform.node(),
            'cpu_cores': os.cpu_count(),
            'cpu_load_avg_1_5_15': load_avg,
            'active_threads': threading.active_count(),
            'process_id': os.getpid(),
            'blueprints': blueprints,
            'total_blueprints': len(blueprints)
        },
        'memory': mem_info,
        'disk': disk_info
    }


def get_recent_logs(limit=200, level=None):
    """
    Get recent logs from in-memory buffer.
    Optional filter by log level (INFO, WARNING, ERROR, DEBUG).
    """
    with _log_buffer_lock:
        logs = list(_in_memory_log_buffer)

    if level:
        level_upper = level.upper()
        logs = [entry for entry in logs if entry['level'] == level_upper]

    return logs[-limit:]


def get_log_file_path():
    """Return path to active log file"""
    log_dir = os.path.join(current_app.root_path, '..', 'logs')
    return os.path.join(log_dir, 'h2_system.log')


def generate_log_dump_text():
    """
    Generate unified log text from disk file and in-memory buffer.
    """
    log_lines = []
    log_path = get_log_file_path()

    # Read from file if exists
    if os.path.exists(log_path):
        try:
            with open(log_path, 'r', encoding='utf-8', errors='replace') as f:
                # Read up to the last 20,000 lines
                lines = f.readlines()
                log_lines.extend(lines[-20000:])
        except Exception as e:
            log_lines.append(f"--- Error reading log file: {e} ---\n")

    # If log file is empty or small, supplement with in-memory buffer
    if len(log_lines) < 5:
        with _log_buffer_lock:
            for entry in _in_memory_log_buffer:
                log_lines.append(f"{entry['timestamp']} [{entry['level']}] [{entry['logger']}] {entry['message']}\n")

    if not log_lines:
        log_lines = [f"{datetime.now(timezone.utc).isoformat()} [INFO] [h2.system] Log buffer initialized. No prior logs recorded.\n"]

    return "".join(log_lines)


def generate_diagnostic_archive():
    """
    Create in-memory ZIP package containing health JSON, application logs, and environment summary.
    """
    health_data = get_system_health()
    log_text = generate_log_dump_text()

    env_summary = (
        f"H2 SYSTEM DIAGNOSTIC DUMP\n"
        f"Generated At: {datetime.now(timezone.utc).isoformat()}\n"
        f"Status: {health_data['status']}\n"
        f"Uptime: {health_data['uptime_formatted']}\n"
        f"Python: {health_data['environment']['python_version']} ({health_data['environment']['python_implementation']})\n"
        f"Platform: {health_data['environment']['platform']}\n"
        f"CPU Cores: {health_data['environment']['cpu_cores']}\n"
        f"Memory Usage: {health_data['memory'].get('used_mb')}MB / {health_data['memory'].get('total_mb')}MB ({health_data['memory'].get('percent')}%)\n"
        f"Disk Usage: {health_data['disk'].get('used_gb')}GB / {health_data['disk'].get('total_gb')}GB ({health_data['disk'].get('percent_used')}%)\n"
        f"Database Dialect: {health_data['database'].get('dialect')} (Status: {health_data['database'].get('status')})\n"
        f"Registered Blueprints: {', '.join(health_data['environment']['blueprints'])}\n"
    )

    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        zip_file.writestr('system_health_report.json', json.dumps(health_data, indent=2))
        zip_file.writestr('h2_system.log', log_text)
        zip_file.writestr('environment_summary.txt', env_summary)

    zip_buffer.seek(0)
    return zip_buffer
