#!/usr/bin/env python3
"""
Performance and Functionality Testing Script for Tanse App
"""

import requests
import time
import json
from datetime import datetime

class TanseAppTester:
    def __init__(self, base_url="http://127.0.0.1:5001"):
        self.base_url = base_url
        self.session = requests.Session()
        self.results = []
        
    def measure_response_time(self, url, method='GET', data=None):
        """Measure response time for a URL"""
        start_time = time.time()
        try:
            if method == 'GET':
                response = self.session.get(url, timeout=10)
            elif method == 'POST':
                response = self.session.post(url, data=data, timeout=10)
            
            end_time = time.time()
            response_time = (end_time - start_time) * 1000  # Convert to milliseconds
            
            return {
                'url': url,
                'method': method,
                'status_code': response.status_code,
                'response_time_ms': round(response_time, 2),
                'success': response.status_code == 200,
                'content_length': len(response.content) if response.content else 0
            }
        except Exception as e:
            end_time = time.time()
            response_time = (end_time - start_time) * 1000
            return {
                'url': url,
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
        result = self.measure_response_time(f"{self.base_url}/login")
        self.results.append({'test': 'Login Page', **result})
        
        # Test login functionality
        login_data = {
            'username': 'admin',
            'password': 'admin'
        }
        
        start_time = time.time()
        try:
            response = self.session.post(f"{self.base_url}/login", data=login_data, timeout=10, allow_redirects=False)
            end_time = time.time()
            response_time = (end_time - start_time) * 1000
            
            # Check if login succeeded by redirect status
            success = response.status_code in [302, 303]
            
            # Follow redirect manually
            if success:
                redirect_response = self.session.get(f"{self.base_url}/", timeout=5)
                success = redirect_response.status_code == 200
            
            login_result = {
                'url': f"{self.base_url}/login",
                'method': 'POST',
                'status_code': response.status_code,
                'response_time_ms': round(response_time, 2),
                'success': success,
                'content_length': len(response.content) if response.content else 0
            }
        except Exception as e:
            end_time = time.time()
            response_time = (end_time - start_time) * 1000
            login_result = {
                'url': f"{self.base_url}/login",
                'method': 'POST',
                'status_code': 0,
                'response_time_ms': round(response_time, 2),
                'success': False,
                'error': str(e),
                'content_length': 0
            }
        
        self.results.append({'test': 'Login Functionality', **login_result})
        return login_result['success']
    
    def test_home_page(self):
        """Test home page (requires login)"""
        print("Testing Home Page...")
        result = self.measure_response_time(f"{self.base_url}/")
        self.results.append({'test': 'Home Page', **result})
        return result['success']
    
    def test_add_violation_page(self):
        """Test add violation page"""
        print("Testing Add Violation Page...")
        result = self.measure_response_time(f"{self.base_url}/add_violation")
        self.results.append({'test': 'Add Violation Page', **result})
        return result['success']
    
    def test_classes_page(self):
        """Test manage classes page"""
        print("Testing Classes Management Page...")
        result = self.measure_response_time(f"{self.base_url}/classes")
        self.results.append({'test': 'Classes Page', **result})
        return result['success']
    
    def test_statistics_page(self):
        """Test statistics page"""
        print("Testing Statistics Page...")
        result = self.measure_response_time(f"{self.base_url}/statistics")
        self.results.append({'test': 'Statistics Page', **result})
        return result['success']
    
    def test_static_files(self):
        """Test static file loading"""
        print("Testing Static Files...")
        
        static_files = [
            '/static/css/style.css',
            '/static/js/main.js'
        ]
        
        for file_path in static_files:
            result = self.measure_response_time(f"{self.base_url}{file_path}")
            self.results.append({'test': f'Static File: {file_path}', **result})
    
    def test_post_methods(self):
        """Test POST methods for functionality"""
        print("Testing POST Methods...")
        
        # Test adding a class
        class_data = {'class_name': f'Test Class {datetime.now().strftime("%H%M%S")}'}
        result = self.measure_response_time(
            f"{self.base_url}/classes", 
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
            f"{self.base_url}/add_violation", 
            method='POST', 
            data=violation_data
        )
        self.results.append({'test': 'Add Violation POST', **result})
    
    def run_all_tests(self):
        """Run all tests"""
        print("=" * 60)
        print("TANSE APP - PERFORMANCE & FUNCTIONALITY TESTING")
        print("=" * 60)
        print(f"Testing URL: {self.base_url}")
        print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
        
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
        
        # Save results to file
        self.save_results()
    
    def save_results(self):
        """Save test results to file"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"test_results_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        print(f"\nResults saved to: {filename}")

if __name__ == "__main__":
    tester = TanseAppTester()
    tester.run_all_tests()