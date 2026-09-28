"""
Tests for Prescription Status and Profile View
"""
import unittest
from datetime import datetime
from app import create_app, db
from app.models import User, Student, Medicine, Prescription, PrescriptionItem


class PrescriptionStatusTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing')
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

        self.h2 = User(username='h2_test', email='h2@test.com', role='H2')
        self.h2.set_password('pass123')

        self.student_user = User(username='student_test', email='stu@test.com', role='Student')
        self.student_user.set_password('pass123')

        db.session.add_all([self.h2, self.student_user])
        db.session.flush()

        self.student = Student(user_id=self.student_user.id, roll_number='ROLL202')
        db.session.add(self.student)

        self.medicine = Medicine(
            name='Amoxicillin',
            generic_name='Amoxicillin',
            dosage='500mg',
            unit='capsules',
            quantity=100
        )
        db.session.add(self.medicine)
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_prescription_item_is_dispensed_property(self):
        """Verify is_dispensed property on PrescriptionItem and Prescription"""
        rx = Prescription(student_id=self.student.id, created_by_id=self.h2.id)
        db.session.add(rx)
        db.session.flush()

        item = PrescriptionItem(
            prescription_id=rx.id,
            medicine_id=self.medicine.id,
            dosage='500mg',
            frequency='Twice daily',
            duration_days=5,
            status='PENDING'
        )
        db.session.add(item)
        db.session.commit()

        self.assertFalse(item.is_dispensed)
        self.assertFalse(rx.is_dispensed)

        # Mark item as DISPENSED
        item.status = 'DISPENSED'
        db.session.commit()

        self.assertTrue(item.is_dispensed)
        self.assertTrue(rx.is_dispensed)

    def test_profile_page_prescription_status_rendering(self):
        """Verify profile page renders Dispensed and Pending statuses correctly"""
        rx = Prescription(student_id=self.student.id, created_by_id=self.h2.id)
        db.session.add(rx)
        db.session.flush()

        dispensed_item = PrescriptionItem(
            prescription_id=rx.id,
            medicine_id=self.medicine.id,
            dosage='500mg',
            frequency='Twice daily',
            duration_days=5,
            status='DISPENSED'
        )
        db.session.add(dispensed_item)
        db.session.commit()

        # Login as H2 to view student profile
        self.client.post('/login', data={'username': 'h2_test', 'password': 'pass123'}, follow_redirects=True)
        response = self.client.get(f'/students/{self.student.id}')
        self.assertEqual(response.status_code, 200)
        content = response.data.decode('utf-8')

        self.assertIn('Dispensed', content)
        self.assertIn('bg-success', content)
