"""
Automated Comprehensive Test Suite
Validates all routes, database operations, calculations, and analytics.
"""

import time
import unittest
from app import create_app
from db import query_all, query_one, execute

class StudentAnalyticsSystemTestCase(unittest.TestCase):

    def setUp(self):
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()

    def login_admin(self):
        """Helper to establish an authenticated admin session."""
        return self.client.post('/login', data={
            'username': 'admin',
            'password': 'admin123'
        }, follow_redirects=True)

    def test_01_login_logout(self):
        """Test authentication flow."""
        # Unauthorized access redirects to login
        res = self.client.get('/')
        self.assertEqual(res.status_code, 302)
        self.assertIn('/login', res.headers['Location'])

        # Valid login
        res = self.login_admin()
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Executive Academic Dashboard', res.data)

        # Logout
        res = self.client.get('/logout', follow_redirects=True)
        self.assertIn(b'You have been securely logged out', res.data)

    def test_02_dashboard_kpis_and_chart_api(self):
        """Test dashboard rendering and chart API."""
        self.login_admin()
        res = self.client.get('/')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Total Enrolled', res.data)
        self.assertIn(b'Avg Attendance', res.data)

        # Charts JSON endpoint
        api_res = self.client.get('/api/dashboard/charts')
        self.assertEqual(api_res.status_code, 200)
        json_data = api_res.get_json()
        self.assertIn('departments', json_data)
        self.assertIn('grades', json_data)
        self.assertTrue(len(json_data['departments']['labels']) > 0)

    def test_03_student_management_crud(self):
        """Test student creation, search, duplicate check, and viewing."""
        self.login_admin()

        # List students
        res = self.client.get('/students')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Aarav Patel', res.data)

        # Search
        res = self.client.get('/students?search=Aarav')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'910023104001', res.data)

        # Add new test student with timestamped unique reg number
        uid = int(time.time() * 1000) % 1000000
        test_reg = f'9100231{uid:05d}'
        test_email = f'test.{uid}@student.edu'

        res = self.client.post('/students/add', data={
            'register_number': test_reg,
            'name': 'Test Student Quality',
            'email': test_email,
            'phone': '9898989898',
            'dept_id': 1,
            'year': 3,
            'semester': 5,
            'section': 'A',
            'gender': 'Male'
        }, follow_redirects=True)
        self.assertIn(b'added successfully', res.data)

        # Check DB
        created = query_one("SELECT * FROM students WHERE register_number = %s", (test_reg,))
        self.assertIsNotNone(created)
        s_id = created['student_id']

        # Duplicate check with exact same reg number
        dup_res = self.client.post('/students/add', data={
            'register_number': test_reg,
            'name': 'Duplicate Person',
            'email': f'another.{uid}@student.edu',
            'phone': '9898989898',
            'dept_id': 1,
            'year': 3,
            'semester': 5,
            'section': 'A',
            'gender': 'Male'
        }, follow_redirects=True)
        self.assertIn(b'Duplicate Record', dup_res.data)

        # View Profile
        profile_res = self.client.get(f'/students/view/{s_id}')
        self.assertEqual(profile_res.status_code, 200)
        self.assertIn(b'Test Student Quality', profile_res.data)

        # Delete test student
        del_res = self.client.post(f'/students/delete/{s_id}', follow_redirects=True)
        self.assertIn(b'permanently removed', del_res.data)

    def test_04_faculty_management(self):
        """Test faculty management and course assignment."""
        self.login_admin()
        res = self.client.get('/faculty')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Dr. Rajesh Sharma', res.data)

    def test_05_attendance_operations(self):
        """Test attendance sheet, batch marking, history, and ledger."""
        self.login_admin()

        # Daily attendance sheet
        res = self.client.get('/attendance?course_id=1&date=2026-08-15')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Class Attendance Register', res.data)

        # Batch mark attendance
        mark_res = self.client.post('/attendance/mark-batch', data={
            'course_id': '1',
            'attendance_date': '2026-08-15',
            'student_ids': ['1', '2'],
            'present_ids': ['1'], # student 1 present, student 2 absent
            'remarks_1': 'Punctual',
            'remarks_2': 'Absent with permission'
        }, follow_redirects=True)
        self.assertIn(b'Attendance recorded successfully', mark_res.data)

        # Verify in DB
        att1 = query_one("SELECT status FROM attendance WHERE student_id=1 AND course_id=1 AND attendance_date='2026-08-15'")
        att2 = query_one("SELECT status FROM attendance WHERE student_id=2 AND course_id=1 AND attendance_date='2026-08-15'")
        self.assertEqual(att1['status'], 'Present')
        self.assertEqual(att2['status'], 'Absent')

        # Attendance history
        hist_res = self.client.get('/attendance/view?date=2026-08-15')
        self.assertEqual(hist_res.status_code, 200)
        self.assertIn(b'Punctual', hist_res.data)

        # Attendance ledger
        ledger_res = self.client.get('/attendance/summary')
        self.assertEqual(ledger_res.status_code, 200)
        self.assertIn(b'Cumulative Attendance Records', ledger_res.data)

    def test_06_performance_management(self):
        """Test performance marks entry, grade calculation, and editing."""
        self.login_admin()
        res = self.client.get('/performance')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Academic Examination Marks', res.data)

        # Clean any prior test row for student 1, course 1, exam 3
        execute("DELETE FROM performances WHERE student_id=1 AND course_id=1 AND exam_id=3")

        # Add marks for student 1 in Exam 3 (Model Exam)
        mark_res = self.client.post('/performance/add', data={
            'student_id': '1',
            'course_id': '1',
            'exam_id': '3',
            'internal_marks': '28.0',
            'assignment_marks': '19.0',
            'exam_marks': '45.0'
        }, follow_redirects=True)
        self.assertIn(b'Marks recorded successfully', mark_res.data)

        # Check total & grade: 28 + 19 + 45 = 92 -> Grade O
        row = query_one("SELECT total_marks, grade FROM performances WHERE student_id=1 AND course_id=1 AND exam_id=3")
        self.assertEqual(row['total_marks'], 92.0)
        self.assertEqual(row['grade'], 'O')

    def test_07_analytics_engine(self):
        """Test Pandas/NumPy analytics calculations and scatter API."""
        self.login_admin()
        res = self.client.get('/analytics')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Pearson Correlation', res.data)

        # Scatter plot API
        scatter_res = self.client.get('/api/analytics/scatter')
        self.assertEqual(scatter_res.status_code, 200)
        data = scatter_res.get_json()
        self.assertIn('correlation', data)
        self.assertIn('slope', data)
        self.assertIn('scatter_points', data)
        self.assertTrue(len(data['scatter_points']) > 0)
        self.assertGreater(data['correlation'], 0.8) # High positive correlation verified

    def test_08_reports_and_transcripts(self):
        """Test report center, official student grade card, and CSV export."""
        self.login_admin()
        res = self.client.get('/reports')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Official Low Attendance Detention List', res.data)

        # Student official print card
        card_res = self.client.get('/reports/student-card/1')
        self.assertEqual(card_res.status_code, 200)
        self.assertIn(b'OFFICIAL STUDENT ACADEMIC & ATTENDANCE TRANSCRIPT', card_res.data)
        self.assertIn(b'Aarav Patel', card_res.data)

        # CSV Export
        csv_res = self.client.get('/reports/export-csv')
        self.assertEqual(csv_res.status_code, 200)
        self.assertTrue('text/csv' in csv_res.headers['Content-Type'])
        self.assertIn(b'register_number,student_name', csv_res.data)

    def test_09_dbms_concepts_showcase(self):
        """Test DBMS concepts showcase and query execution API."""
        self.login_admin()
        res = self.client.get('/dbms-showcase')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Interactive SQL Query Execution Terminal', res.data)

        # Test execute query API
        api_res = self.client.post('/api/dbms/execute', json={'concept_id': 'aggregates_groupby'})
        self.assertEqual(api_res.status_code, 200)
        data = api_res.get_json()
        self.assertTrue(data['success'])
        self.assertTrue(len(data['results']) > 0)

if __name__ == '__main__':
    unittest.main()
