"""
Tests for Equipment Penalty Override and Revert Feature
"""
import unittest
from datetime import datetime, timedelta
from app import create_app, db
from app.models import User, Student, MedicalEquipment, EquipmentIssue


class EquipmentPenaltyOverrideTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing')
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

        # Create test users with different roles
        self.director = User(username='director_test', email='dir@test.com', role='Director')
        self.director.set_password('pass123')

        self.h2 = User(username='h2_test', email='h2@test.com', role='H2')
        self.h2.set_password('pass123')

        self.office = User(username='office_test', email='office@test.com', role='Office')
        self.office.set_password('pass123')

        self.warden = User(username='warden_test', email='warden@test.com', role='Warden')
        self.warden.set_password('pass123')

        self.doctor = User(username='doctor_test', email='doc@test.com', role='Doctor')
        self.doctor.set_password('pass123')

        self.student_user = User(username='student_test', email='stu@test.com', role='Student')
        self.student_user.set_password('pass123')

        db.session.add_all([self.director, self.h2, self.office, self.warden, self.doctor, self.student_user])
        db.session.flush()

        self.student = Student(user_id=self.student_user.id, roll_number='ROLL101')
        db.session.add(self.student)

        self.equipment = MedicalEquipment(
            name='Blood Pressure Monitor',
            equipment_code='BP001',
            quantity_available=5,
            unit_cost=1500.0,
            daily_penalty=50.0
        )
        db.session.add(self.equipment)
        db.session.commit()

        # Create an overdue issue with penalty
        self.issue = EquipmentIssue(
            equipment_id=self.equipment.id,
            student_id=self.student.id,
            issued_by_id=self.h2.id,
            quantity=1,
            issued_date=datetime.now() - timedelta(days=10),
            expected_return_date=datetime.now() - timedelta(days=4),
            days_overdue=4,
            penalty_amount=200.0,
            status='Overdue'
        )
        db.session.add(self.issue)
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_model_override_penalty(self):
        """Test EquipmentIssue.override_penalty method"""
        self.issue.override_penalty(100.0, reason='50% concession for student', user_id=self.director.id)
        self.assertEqual(self.issue.penalty_amount, 100.0)
        self.assertEqual(self.issue.original_penalty_amount, 200.0)
        self.assertTrue(self.issue.penalty_overridden)
        self.assertEqual(self.issue.penalty_override_reason, '50% concession for student')
        self.assertEqual(self.issue.penalty_overridden_by_id, self.director.id)
        self.assertIsNotNone(self.issue.penalty_overridden_at)

    def test_model_revert_penalty(self):
        """Test EquipmentIssue.revert_penalty method"""
        self.issue.revert_penalty(reason='Excused due to hospitalization', user_id=self.h2.id)
        self.assertEqual(self.issue.penalty_amount, 0.0)
        self.assertEqual(self.issue.original_penalty_amount, 200.0)
        self.assertTrue(self.issue.penalty_overridden)
        self.assertEqual(self.issue.penalty_override_reason, 'Excused due to hospitalization')
        self.assertFalse(self.issue.penalty_paid)

    def test_model_restore_penalty(self):
        """Test EquipmentIssue.restore_penalty method"""
        self.issue.revert_penalty(reason='Mistake', user_id=self.h2.id)
        self.assertEqual(self.issue.penalty_amount, 0.0)
        self.assertTrue(self.issue.penalty_overridden)

        self.issue.restore_penalty()
        self.assertEqual(self.issue.penalty_amount, 200.0)
        self.assertFalse(self.issue.penalty_overridden)
        self.assertIsNone(self.issue.penalty_override_reason)

    def test_mark_as_overdue_preserves_overridden_penalty(self):
        """Test that mark_as_overdue does not overwrite an overridden penalty"""
        self.issue.revert_penalty(reason='Excused', user_id=self.h2.id)
        self.assertEqual(self.issue.penalty_amount, 0.0)

        # Trigger mark_as_overdue
        self.issue.mark_as_overdue()
        self.assertEqual(self.issue.penalty_amount, 0.0)
        self.assertTrue(self.issue.penalty_overridden)

    def test_http_revert_penalty_as_admin(self):
        """Test POST /equipment/override-penalty/<id> with action=revert as Director"""
        self.client.post('/login', data={'username': 'director_test', 'password': 'pass123'}, follow_redirects=True)

        res = self.client.post(f'/equipment/override-penalty/{self.issue.id}', data={
            'action': 'revert',
            'reason': 'Returned on time - system delay'
        }, follow_redirects=True)
        self.assertEqual(res.status_code, 200)

        db.session.expire_all()
        updated_issue = db.session.get(EquipmentIssue, self.issue.id)
        self.assertEqual(updated_issue.penalty_amount, 0.0)
        self.assertTrue(updated_issue.penalty_overridden)
        self.assertIn('reverted to ₹0.00', res.data.decode('utf-8'))
        self.assertIn('Waived', res.data.decode('utf-8'))

    def test_http_override_penalty_as_h2(self):
        """Test POST /equipment/override-penalty/<id> with action=override as H2"""
        self.client.post('/login', data={'username': 'h2_test', 'password': 'pass123'}, follow_redirects=True)

        res = self.client.post(f'/equipment/override-penalty/{self.issue.id}', data={
            'action': 'override',
            'penalty_amount': '75.00',
            'reason': 'Partial fee reduction'
        }, follow_redirects=True)
        self.assertEqual(res.status_code, 200)

        db.session.expire_all()
        updated_issue = db.session.get(EquipmentIssue, self.issue.id)
        self.assertEqual(updated_issue.penalty_amount, 75.00)
        self.assertEqual(updated_issue.original_penalty_amount, 200.0)
        self.assertTrue(updated_issue.penalty_overridden)
        self.assertIn('updated to ₹75.00', res.data.decode('utf-8'))

    def test_http_restore_penalty_as_office(self):
        """Test POST /equipment/override-penalty/<id> with action=restore as Office"""
        self.client.post('/login', data={'username': 'office_test', 'password': 'pass123'}, follow_redirects=True)

        # First override
        self.client.post(f'/equipment/override-penalty/{self.issue.id}', data={
            'action': 'revert',
            'reason': 'Waived temporarily'
        }, follow_redirects=True)

        # Then restore
        res = self.client.post(f'/equipment/override-penalty/{self.issue.id}', data={
            'action': 'restore'
        }, follow_redirects=True)
        self.assertEqual(res.status_code, 200)

        db.session.expire_all()
        updated_issue = db.session.get(EquipmentIssue, self.issue.id)
        self.assertEqual(updated_issue.penalty_amount, 200.0)
        self.assertFalse(updated_issue.penalty_overridden)
        self.assertIn('restored to ₹200.00', res.data.decode('utf-8'))

    def test_unauthorized_student_cannot_override_penalty(self):
        """Test that Student cannot call /equipment/override-penalty"""
        self.client.post('/login', data={'username': 'student_test', 'password': 'pass123'}, follow_redirects=True)

        res = self.client.post(f'/equipment/override-penalty/{self.issue.id}', data={
            'action': 'revert',
            'reason': 'Unauthorized'
        }, follow_redirects=False)
        self.assertEqual(res.status_code, 302)  # Redirected away by require_role

        db.session.expire_all()
        updated_issue = db.session.get(EquipmentIssue, self.issue.id)
        self.assertEqual(updated_issue.penalty_amount, 200.0)
        self.assertFalse(updated_issue.penalty_overridden)

    def test_unauthorized_doctor_cannot_override_penalty(self):
        """Test that Doctor cannot call /equipment/override-penalty"""
        self.client.post('/login', data={'username': 'doctor_test', 'password': 'pass123'}, follow_redirects=True)

        res = self.client.post(f'/equipment/override-penalty/{self.issue.id}', data={
            'action': 'revert',
            'reason': 'Doctor attempt'
        }, follow_redirects=False)
        self.assertEqual(res.status_code, 302)

        db.session.expire_all()
        updated_issue = db.session.get(EquipmentIssue, self.issue.id)
        self.assertEqual(updated_issue.penalty_amount, 200.0)
        self.assertFalse(updated_issue.penalty_overridden)

    def test_issue_list_template_renders_modal_and_revert_button(self):
        """Test GET /equipment/issues renders override buttons and modal for admin"""
        self.client.post('/login', data={'username': 'director_test', 'password': 'pass123'}, follow_redirects=True)

        res = self.client.get('/equipment/issues')
        self.assertEqual(res.status_code, 200)
        html = res.data.decode('utf-8')
        self.assertIn('Equipment Issues', html)
        self.assertIn(f'overridePenaltyModal{self.issue.id}', html)
        self.assertIn('Override / Revert Penalty', html)
        self.assertIn('Set to ₹0 (Waive)', html)
        self.assertIn('Revert to ₹0.00', html)
        self.assertIn('Print Issues Report', html)
        self.assertIn('Quick Print', html)

    def test_print_issues_route_as_h2(self):
        """Test GET /equipment/issues/print by H2 member"""
        self.client.post('/login', data={'username': 'h2_test', 'password': 'pass123'}, follow_redirects=True)

        res = self.client.get('/equipment/issues/print')
        self.assertEqual(res.status_code, 200)
        html = res.data.decode('utf-8')

        # Check official letterhead
        self.assertIn('SRI SATHYA SAI INSTITUTE OF HIGHER LEARNING', html)
        self.assertIn('NANDIGIRI HOSTEL', html)
        self.assertIn('HOLISTIC HEALTH (H2) TEAM', html)
        self.assertIn('Medical Equipment Issues & Penalties Audit Report', html)

        # Check summary metrics
        self.assertIn('Total Issues', html)
        self.assertIn('Total Penalty', html)
        self.assertIn('Unpaid Fine', html)

        # Check issue row
        self.assertIn('Blood Pressure Monitor', html)
        self.assertIn('ROLL101', html)
        self.assertIn('200.00', html)

        # Check H2 attestation and signature block
        self.assertIn('H2 Health Team Member Attestation', html)
        self.assertIn('h2_test', html)
        self.assertIn('H2 Member Signature', html)
        self.assertIn('Hostel Health Office Seal', html)

    def test_print_issues_unauthorized_student(self):
        """Test that Student cannot access print issues report"""
        self.client.post('/login', data={'username': 'student_test', 'password': 'pass123'}, follow_redirects=True)

        res = self.client.get('/equipment/issues/print', follow_redirects=False)
        self.assertEqual(res.status_code, 302)  # Blocked by require_role


if __name__ == '__main__':
    unittest.main()
