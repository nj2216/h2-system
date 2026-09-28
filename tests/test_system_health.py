"""
Tests for System Health Endpoint, Environment Diagnostics, and Log Dumps
"""
import io
import json
import zipfile
import unittest
from app import create_app, db
from app.models import User, Student
from app.system_health.services import get_system_health, format_uptime, mask_connection_uri


class SystemHealthTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing')
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

        self.user = User(username='admin_health', email='health@test.com', role='Director')
        self.user.set_password('pass123')
        db.session.add(self.user)
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_services_get_system_health(self):
        """Test services get_system_health structure and values"""
        health = get_system_health()
        self.assertIn(health['status'], ['HEALTHY', 'DEGRADED', 'CRITICAL'])
        self.assertIn('uptime_seconds', health)
        self.assertIn('database', health)
        self.assertEqual(health['database']['status'], 'CONNECTED')
        self.assertIn('environment', health)
        self.assertIn('python_version', health['environment'])
        self.assertIn('disk', health)
        self.assertIn('memory', health)

    def test_services_mask_connection_uri(self):
        """Test database credentials masking"""
        uri = "postgresql://myuser:supersecretpass@db.internal:5432/h2_db"
        masked = mask_connection_uri(uri)
        self.assertNotIn("supersecretpass", masked)
        self.assertIn("myuser:***", masked)

        sqlite_uri = "sqlite:///h2_system.db"
        self.assertEqual(mask_connection_uri(sqlite_uri), sqlite_uri)

    def test_format_uptime(self):
        """Test uptime formatting"""
        self.assertEqual(format_uptime(45), "45s")
        self.assertEqual(format_uptime(125), "2m 5s")
        self.assertEqual(format_uptime(3665), "1h 1m 5s")
        self.assertEqual(format_uptime(90065), "1d 1h 1m 5s")

    def test_html_dashboard_endpoint(self):
        """Test GET /system-health returns HTML dashboard"""
        response = self.client.get('/system-health')
        self.assertEqual(response.status_code, 200)
        content = response.data.decode('utf-8')
        self.assertIn('System Health', content)
        self.assertIn('Database', content)
        self.assertIn('Environment & Platform Details', content)
        self.assertIn('Application Logs', content)

    def test_json_api_endpoints(self):
        """Test GET /system-health?format=json and GET /system-health/api"""
        # Format=json
        res1 = self.client.get('/system-health?format=json')
        self.assertEqual(res1.status_code, 200)
        data1 = json.loads(res1.data)
        self.assertIn('status', data1)
        self.assertEqual(data1['database']['status'], 'CONNECTED')

        # Direct /api
        res2 = self.client.get('/system-health/api')
        self.assertEqual(res2.status_code, 200)
        data2 = json.loads(res2.data)
        self.assertIn('environment', data2)
        self.assertEqual(data2['environment']['app_name'], 'H2 System (Health & Hostel Management)')

    def test_ping_and_ready_probes(self):
        """Test lightweight liveness and readiness probe endpoints"""
        ping_res = self.client.get('/system-health/ping')
        self.assertEqual(ping_res.status_code, 200)
        ping_data = json.loads(ping_res.data)
        self.assertEqual(ping_data['status'], 'ok')

        ready_res = self.client.get('/system-health/ready')
        self.assertEqual(ready_res.status_code, 200)
        ready_data = json.loads(ready_res.data)
        self.assertEqual(ready_data['status'], 'ready')
        self.assertEqual(ready_data['database'], 'CONNECTED')

    def test_download_logs(self):
        """Test GET /system-health/logs/download returns .log attachment"""
        response = self.client.get('/system-health/logs/download')
        self.assertEqual(response.status_code, 200)
        self.assertIn('attachment;', response.headers.get('Content-Disposition', ''))
        self.assertIn('.log', response.headers.get('Content-Disposition', ''))
        self.assertTrue(len(response.data) > 0)

    def test_download_diagnostic_dump_zip(self):
        """Test GET /system-health/dump/download returns valid ZIP archive"""
        response = self.client.get('/system-health/dump/download')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, 'application/zip')
        self.assertIn('.zip', response.headers.get('Content-Disposition', ''))

        # Verify ZIP archive contents
        zip_buf = io.BytesIO(response.data)
        with zipfile.ZipFile(zip_buf, 'r') as zf:
            namelist = zf.namelist()
            self.assertIn('system_health_report.json', namelist)
            self.assertIn('h2_system.log', namelist)
            self.assertIn('environment_summary.txt', namelist)

            # Check json content inside zip
            report_raw = zf.read('system_health_report.json').decode('utf-8')
            report_data = json.loads(report_raw)
            self.assertIn('status', report_data)

    def test_log_test_emission_and_api_logs(self):
        """Test POST /system-health/logs/test and GET /system-health/api/logs"""
        test_msg = "Custom diagnostic test entry for automated test"
        post_res = self.client.post(
            '/system-health/logs/test',
            json={'level': 'INFO', 'message': test_msg}
        )
        self.assertEqual(post_res.status_code, 200)
        post_data = json.loads(post_res.data)
        self.assertTrue(post_data['success'])

        # Check in api/logs
        get_res = self.client.get('/system-health/api/logs?limit=50')
        self.assertEqual(get_res.status_code, 200)
        logs_data = json.loads(get_res.data)
        messages = [log['message'] for log in logs_data['logs']]
        self.assertTrue(any(test_msg in m for m in messages))
