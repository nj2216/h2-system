"""
Routes for System Health, Environment Diagnostics, and Log Dumps
"""
import io
from datetime import datetime, timezone
from flask import (
    Blueprint, render_template, jsonify, request, send_file, Response, current_app
)
from app.system_health.services import (
    get_system_health, get_recent_logs, generate_log_dump_text,
    generate_diagnostic_archive
)

system_health_bp = Blueprint('system_health', __name__, template_folder='templates')


@system_health_bp.route('/', methods=['GET'])
@system_health_bp.route('', methods=['GET'])
def dashboard():
    """
    Main system health endpoint.
    Returns JSON if requested via API/header or query param `format=json`.
    Otherwise renders a responsive, theme-aware web dashboard.
    """
    health = get_system_health()

    # If API requested or format=json specified
    wants_json = (
        request.args.get('format') == 'json' or
        request.headers.get('Accept', '').startswith('application/json') or
        request.is_json
    )
    if wants_json:
        status_code = 200 if health['status'] != 'CRITICAL' else 503
        return jsonify(health), status_code

    # Render HTML dashboard
    recent_logs = get_recent_logs(limit=100)
    return render_template(
        'system_health/dashboard.html',
        health=health,
        logs=recent_logs
    )


@system_health_bp.route('/api', methods=['GET'])
def api_health():
    """Direct JSON API endpoint for system health metrics"""
    health = get_system_health()
    status_code = 200 if health['status'] != 'CRITICAL' else 503
    return jsonify(health), status_code


@system_health_bp.route('/ping', methods=['GET'])
@system_health_bp.route('/live', methods=['GET'])
def ping():
    """Fast liveness probe for monitoring tools"""
    health = get_system_health()
    return jsonify({
        'status': 'ok',
        'uptime_seconds': health['uptime_seconds'],
        'uptime': health['uptime_formatted'],
        'timestamp': datetime.now(timezone.utc).isoformat()
    }), 200


@system_health_bp.route('/ready', methods=['GET'])
def ready():
    """Readiness probe checking database connectivity"""
    health = get_system_health()
    is_ready = health['database']['status'] == 'CONNECTED'
    code = 200 if is_ready else 503
    return jsonify({
        'status': 'ready' if is_ready else 'not_ready',
        'database': health['database']['status'],
        'latency_ms': health['database']['latency_ms'],
        'timestamp': datetime.now(timezone.utc).isoformat()
    }), code


@system_health_bp.route('/logs/download', methods=['GET'])
def download_logs():
    """Download plain application log dump file"""
    log_content = generate_log_dump_text()
    timestamp_str = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"h2_system_logs_{timestamp_str}.log"

    return Response(
        log_content,
        mimetype='text/plain; charset=utf-8',
        headers={
            'Content-Disposition': f'attachment; filename="{filename}"'
        }
    )


@system_health_bp.route('/dump/download', methods=['GET'])
def download_diagnostic_dump():
    """Download comprehensive diagnostics ZIP package"""
    zip_buffer = generate_diagnostic_archive()
    timestamp_str = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"h2_system_diagnostics_{timestamp_str}.zip"

    return send_file(
        zip_buffer,
        mimetype='application/zip',
        as_attachment=True,
        download_name=filename
    )


@system_health_bp.route('/api/logs', methods=['GET'])
def api_logs():
    """Get recent in-memory logs in JSON format"""
    limit = request.args.get('limit', 100, type=int)
    level = request.args.get('level', None)
    logs = get_recent_logs(limit=min(limit, 1000), level=level)
    return jsonify({
        'total_returned': len(logs),
        'filter_level': level or 'ALL',
        'logs': logs
    })


@system_health_bp.route('/logs/test', methods=['POST'])
def test_log():
    """Endpoint to emit a test log message to verify logging functionality"""
    data = request.get_json(silent=True) or request.form
    level = (data.get('level') or 'INFO').upper()
    message = data.get('message') or f"Manual test log entry generated via /system-health/logs/test"

    log_fn = getattr(current_app.logger, level.lower(), current_app.logger.info)
    log_fn(f"[SYSTEM-HEALTH TEST] {message}")

    return jsonify({
        'success': True,
        'level': level,
        'message': message,
        'timestamp': datetime.now(timezone.utc).isoformat()
    })
