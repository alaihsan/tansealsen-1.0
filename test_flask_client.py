#!/usr/bin/env python3
"""
Flask Test Client Performance Testing for Tanse App
"""

import sys
import os
import time
from datetime import datetime

# Add my_app to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'my_app'))

from my_app.app import create_app
from my_app.extensions import db
from my_app.models import User
from my_app.extensions import bcrypt

class FlaskTanseAppTester:
    def __init__(self):
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()
        self.results = []
        
    def setup_database(self):
        """Setup database for testing"""
        with self.app.app_context():
            db.create_all()
            
            # Create admin user if not exists
            user = User.query.filter_by(username='admin').first()
            if not user:
                hashed_password = bcrypt.generate_password_hash('admin').decode('utf-8')
                admin_user = User(username='admin', password=hashed_password)
                db.session.add(admin_user)
                db.session.commit()
                print("Admin user created for testing")
    
    def measure_response_time(self, path, method='GET', data=None):
        """Measure response time using Flask test client"""
        start_time = time.time()
        try:
            if method == 'GET':
                response = self.client.get(path, follow_redirects=False)
            elif method == 'POST':
                response = self.client.post(path, data=data, follow_redirects=False)
            
            end_time = time.time()
            response_time = (end_time - start_time) * 1000  # Convert to milliseconds
            
            return {
                'url': path,
                'method': method,
                'status_code': response.status_code,
                'response_time_ms': round(response_time, 2),
                'success': response.status_code in [200, 302],
                'content_length': len(response.data) if response.data else 0
            }
        except Exception as e:
            end_time = time.time()
            response_time = (end_time - start_time) * 1000
            return {
                'url': path,
                'method': method,
                'status_code': 0,
                'response_time_ms': round(response_time, 2),
                'success': False,
                'error': str(e),
                'content_length': 0
            }
    
    def test_login_page(self):
        """Test login page"""
        print("Testing Login Page...")
        result = self.measure_response_time('/login')
        self.results.append({'test': 'Login Page', **result})
        
        # Test login functionality
        login_data = {
            'username': 'admin',
            'password': 'admin'
        }
        login_result = self.measure_response_time(
            '/login', 
            method='POST', 
            data=login_data
        )
        self.results.append({'test': 'Login Functionality', **login_result})
        return login_result['success'] and login_result['status_code'] == 302
    
    def test_home_page(self):
        """Test home page (requires login)"""
        print("Testing Home Page...")
        # Login first to get session
        self.client.post('/login', data={
            'username': 'admin',
            'password': 'admin'
        })
        
        result = self.measure_response_time('/')
        self.results.append({'test': 'Home Page', **result})
        return result['success']
    
    def test_add_violation_page(self):
        """Test add violation page"""
        print("Testing Add Violation Page...")
        result = self.measure_response_time('/add_violation')
        self.results.append({'test': 'Add Violation Page', **result})
        return result['success']
    
    def test_classes_page(self):
        """Test manage classes page"""
        print("Testing Classes Management Page...")
        result = self.measure_response_time('/classes')
        self.results.append({'test': 'Classes Page', **result})
        return result['success']
    
    def test_statistics_page(self):
        """Test statistics page"""
        print("Testing Statistics Page...")
        result = self.measure_response_time('/statistics')
        self.results.append({'test': 'Statistics Page', **result})
        return result['success']
    
    def test_static_files(self):
        """Test static file loading"""
        print("Testing Static Files...")
        
        static_files = [
            '/static/css/style.css',
        ]
        
        for file_path in static_files:
            result = self.measure_response_time(file_path)
            self.results.append({'test': f'Static File: {file_path}', **result})
    
    def test_post_methods(self):
        """Test POST methods for functionality"""
        print("Testing POST Methods...")
        
        # Test adding a class
        class_data = {'class_name': f'Test Class {datetime.now().strftime("%H%M%S")}'}
        result = self.measure_response_time(
            '/classes', 
            method='POST', 
            data=class_data
        )
        self.results.append({'test': 'Add Class POST', **result})
        
        # Test adding violation (might fail if no students exist, but that's ok for testing)
        violation_data = {
            'student_id': '1',
            'description': 'Test violation for performance testing',
            'points': '5'
        }
        result = self.measure_response_time(
            '/add_violation', 
            method='POST', 
            data=violation_data
        )
        self.results.append({'test': 'Add Violation POST', **result})
    
    def run_all_tests(self):
        """Run all tests"""
        print("=" * 60)
        print("TANSE APP - FLASK TEST CLIENT PERFORMANCE TESTING")
        print("=" * 60)
        print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
        
        # Setup database
        self.setup_database()
        
        # Test login first
        login_success = self.test_login_page()
        
        if login_success:
            # Test authenticated pages
            self.test_home_page()
            self.test_add_violation_page()
            self.test_classes_page()
            self.test_statistics_page()
            self.test_static_files()
            self.test_post_methods()
        else:
            print("X Login failed. Skipping authenticated page tests.")
        
        # Generate report
        self.generate_report()
    
    def generate_report(self):
        """Generate test report"""
        print("\n" + "=" * 60)
        print("TEST RESULTS SUMMARY")
        print("=" * 60)
        
        successful_tests = [r for r in self.results if r['success']]
        failed_tests = [r for r in self.results if not r['success']]
        
        print(f"Total Tests: {len(self.results)}")
        print(f"Successful: {len(successful_tests)} [OK]")
        print(f"Failed: {len(failed_tests)} [FAIL]")
        
        if successful_tests:
            avg_response_time = sum(r['response_time_ms'] for r in successful_tests) / len(successful_tests)
            print(f"Average Response Time: {avg_response_time:.2f}ms")
        
        print("\nDetailed Results:")
        print("-" * 60)
        
        for result in self.results:
            status = "[OK]" if result['success'] else "[FAIL]"
            print(f"{status} {result['test']}: {result['response_time_ms']}ms")
            
            if not result['success'] and 'error' in result:
                print(f"   Error: {result['error']}")
        
        # Performance Analysis
        print("\n" + "=" * 60)
        print("PERFORMANCE ANALYSIS")
        print("=" * 60)
        
        if successful_tests:
            sorted_by_time = sorted(successful_tests, key=lambda x: x['response_time_ms'])
            
            print("Fastest Pages:")
            for i, result in enumerate(sorted_by_time[:3]):
                print(f"  {i+1}. {result['test']}: {result['response_time_ms']}ms")
            
            print("\nSlowest Pages:")
            for i, result in enumerate(sorted_by_time[-3:], 1):
                print(f"  {i}. {result['test']}: {result['response_time_ms']}ms")
        
        # Recommendations
        print("\n" + "=" * 60)
        print("PERFORMANCE RECOMMENDATIONS")
        print("=" * 60)
        
        if successful_tests:
            slow_pages = [r for r in successful_tests if r['response_time_ms'] > 100]
            if slow_pages:
                print("Pages that need optimization (response time > 100ms):")
                for page in slow_pages:
                    print(f"  - {page['test']}: {page['response_time_ms']}ms")
            else:
                print("All pages are performing well (< 100ms response time)")
        
        if failed_tests:
            print("\nFailed tests that need fixing:")
            for test in failed_tests:
                print(f"  - {test['test']}: {test.get('error', 'Unknown error')}")

if __name__ == "__main__":
    tester = FlaskTanseAppTester()
    tester.run_all_tests()