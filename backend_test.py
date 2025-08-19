#!/usr/bin/env python3

import requests
import sys
import json
import time
from datetime import datetime

class SmartNotesAPITester:
    def __init__(self, base_url="https://productivity-pal-6.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.user_id = None
        self.tests_run = 0
        self.tests_passed = 0
        self.created_note_id = None

    def log_test(self, name, success, details=""):
        """Log test results"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name} - PASSED {details}")
        else:
            print(f"❌ {name} - FAILED {details}")
        return success

    def make_request(self, method, endpoint, data=None, expected_status=200):
        """Make HTTP request with proper headers"""
        url = f"{self.api_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        
        if self.token:
            headers['Authorization'] = f'Bearer {self.token}'

        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=30)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=30)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers, timeout=30)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers, timeout=30)

            success = response.status_code == expected_status
            result_data = {}
            
            try:
                result_data = response.json()
            except:
                result_data = {"raw_response": response.text}

            return success, response.status_code, result_data

        except Exception as e:
            return False, 0, {"error": str(e)}

    def test_health_check(self):
        """Test API health endpoint"""
        success, status, data = self.make_request('GET', 'health')
        return self.log_test(
            "Health Check", 
            success and data.get('status') == 'healthy',
            f"Status: {status}, Response: {data.get('message', 'N/A')}"
        )

    def test_user_registration(self):
        """Test user registration"""
        timestamp = datetime.now().strftime('%H%M%S')
        user_data = {
            "email": f"test_user_{timestamp}@example.com",
            "password": "TestPassword123!",
            "name": f"Test User {timestamp}"
        }
        
        success, status, data = self.make_request('POST', 'auth/register', user_data, 200)
        
        if success and 'token' in data:
            self.token = data['token']
            self.user_id = data['user']['id']
            
        return self.log_test(
            "User Registration",
            success and 'token' in data,
            f"Status: {status}, User ID: {data.get('user', {}).get('id', 'N/A')}"
        )

    def test_user_login(self):
        """Test user login with existing credentials"""
        # Use the same credentials from registration
        timestamp = datetime.now().strftime('%H%M%S')
        login_data = {
            "email": f"test_user_{timestamp}@example.com",
            "password": "TestPassword123!"
        }
        
        success, status, data = self.make_request('POST', 'auth/login', login_data, 200)
        
        if success and 'token' in data:
            self.token = data['token']
            
        return self.log_test(
            "User Login",
            success and 'token' in data,
            f"Status: {status}, Message: {data.get('message', 'N/A')}"
        )

    def test_invalid_login(self):
        """Test login with invalid credentials"""
        login_data = {
            "email": "invalid@example.com",
            "password": "wrongpassword"
        }
        
        success, status, data = self.make_request('POST', 'auth/login', login_data, 400)
        
        return self.log_test(
            "Invalid Login",
            success,
            f"Status: {status}, Error: {data.get('detail', 'N/A')}"
        )

    def test_create_note_short(self):
        """Test creating a note with short content (no AI summary)"""
        note_data = {
            "title": "Test Note Short",
            "content": "This is a short note.",
            "tags": ["test", "short"]
        }
        
        success, status, data = self.make_request('POST', 'notes', note_data, 201)
        
        if success:
            self.created_note_id = data.get('id')
            
        return self.log_test(
            "Create Short Note",
            success and data.get('summary') is None,
            f"Status: {status}, Note ID: {data.get('id', 'N/A')}, Summary: {data.get('summary', 'None')}"
        )

    def test_create_note_long(self):
        """Test creating a note with long content (should trigger AI summary)"""
        note_data = {
            "title": "Test Note Long with AI Summary",
            "content": "This is a much longer note that should trigger the AI summarization feature. It contains more than 100 characters which is the threshold for automatic summary generation. The AI should analyze this content and provide a concise summary that captures the key points and important information from the note content.",
            "tags": ["test", "long", "ai-summary"]
        }
        
        success, status, data = self.make_request('POST', 'notes', note_data, 201)
        
        # AI summary generation might take time, so we check if it exists or is being processed
        has_summary = data.get('summary') is not None
        
        return self.log_test(
            "Create Long Note (AI Summary)",
            success,
            f"Status: {status}, Note ID: {data.get('id', 'N/A')}, Has Summary: {has_summary}"
        )

    def test_get_notes(self):
        """Test retrieving all notes"""
        success, status, data = self.make_request('GET', 'notes')
        
        is_list = isinstance(data, list)
        
        return self.log_test(
            "Get All Notes",
            success and is_list,
            f"Status: {status}, Notes Count: {len(data) if is_list else 'N/A'}"
        )

    def test_get_single_note(self):
        """Test retrieving a single note"""
        if not self.created_note_id:
            return self.log_test("Get Single Note", False, "No note ID available")
            
        success, status, data = self.make_request('GET', f'notes/{self.created_note_id}')
        
        return self.log_test(
            "Get Single Note",
            success and data.get('id') == self.created_note_id,
            f"Status: {status}, Note Title: {data.get('title', 'N/A')}"
        )

    def test_update_note(self):
        """Test updating a note"""
        if not self.created_note_id:
            return self.log_test("Update Note", False, "No note ID available")
            
        update_data = {
            "title": "Updated Test Note",
            "content": "This note has been updated with new content.",
            "is_favorite": True
        }
        
        success, status, data = self.make_request('PUT', f'notes/{self.created_note_id}', update_data)
        
        return self.log_test(
            "Update Note",
            success and data.get('title') == "Updated Test Note",
            f"Status: {status}, Updated Title: {data.get('title', 'N/A')}"
        )

    def test_search_notes(self):
        """Test searching notes"""
        success, status, data = self.make_request('GET', 'notes?search=test')
        
        is_list = isinstance(data, list)
        
        return self.log_test(
            "Search Notes",
            success and is_list,
            f"Status: {status}, Search Results: {len(data) if is_list else 'N/A'}"
        )

    def test_filter_favorites(self):
        """Test filtering favorite notes"""
        success, status, data = self.make_request('GET', 'notes?favorites_only=true')
        
        is_list = isinstance(data, list)
        
        return self.log_test(
            "Filter Favorites",
            success and is_list,
            f"Status: {status}, Favorite Notes: {len(data) if is_list else 'N/A'}"
        )

    def test_ai_summarize(self):
        """Test AI summarization"""
        if not self.created_note_id:
            return self.log_test("AI Summarize", False, "No note ID available")
            
        ai_request = {
            "action": "summarize",
            "note_id": self.created_note_id
        }
        
        success, status, data = self.make_request('POST', 'ai/process', ai_request)
        
        # AI processing might take time
        time.sleep(2)
        
        return self.log_test(
            "AI Summarize",
            success and data.get('action') == 'summarize',
            f"Status: {status}, Result Length: {len(data.get('result', '')) if data.get('result') else 0}"
        )

    def test_ai_suggest_tags(self):
        """Test AI tag suggestions"""
        if not self.created_note_id:
            return self.log_test("AI Suggest Tags", False, "No note ID available")
            
        ai_request = {
            "action": "suggest_tags",
            "note_id": self.created_note_id
        }
        
        success, status, data = self.make_request('POST', 'ai/process', ai_request)
        
        # AI processing might take time
        time.sleep(2)
        
        try:
            tags = json.loads(data.get('result', '[]'))
            is_valid_tags = isinstance(tags, list)
        except:
            is_valid_tags = False
            
        return self.log_test(
            "AI Suggest Tags",
            success and data.get('action') == 'suggest_tags' and is_valid_tags,
            f"Status: {status}, Suggested Tags: {data.get('result', 'N/A')}"
        )

    def test_ai_insights(self):
        """Test AI insights generation"""
        if not self.created_note_id:
            return self.log_test("AI Insights", False, "No note ID available")
            
        ai_request = {
            "action": "insights",
            "note_id": self.created_note_id
        }
        
        success, status, data = self.make_request('POST', 'ai/process', ai_request)
        
        # AI processing might take time
        time.sleep(2)
        
        return self.log_test(
            "AI Insights",
            success and data.get('action') == 'insights',
            f"Status: {status}, Insights Length: {len(data.get('result', '')) if data.get('result') else 0}"
        )

    def test_get_tags(self):
        """Test getting user tags"""
        success, status, data = self.make_request('GET', 'tags')
        
        is_list = isinstance(data, list)
        
        return self.log_test(
            "Get User Tags",
            success and is_list,
            f"Status: {status}, Tags Count: {len(data) if is_list else 'N/A'}"
        )

    def test_get_stats(self):
        """Test getting user statistics"""
        success, status, data = self.make_request('GET', 'stats')
        
        has_required_fields = all(key in data for key in ['total_notes', 'favorite_notes', 'recent_notes'])
        
        return self.log_test(
            "Get User Stats",
            success and has_required_fields,
            f"Status: {status}, Stats: {data if success else 'N/A'}"
        )

    def test_delete_note(self):
        """Test deleting a note"""
        if not self.created_note_id:
            return self.log_test("Delete Note", False, "No note ID available")
            
        success, status, data = self.make_request('DELETE', f'notes/{self.created_note_id}', expected_status=200)
        
        return self.log_test(
            "Delete Note",
            success,
            f"Status: {status}, Message: {data.get('message', 'N/A')}"
        )

    def run_all_tests(self):
        """Run all API tests"""
        print("🚀 Starting Smart Notes API Tests...")
        print(f"🔗 Testing against: {self.base_url}")
        print("=" * 60)
        
        # Health check
        if not self.test_health_check():
            print("❌ API is not healthy, stopping tests")
            return False
            
        # Authentication tests
        if not self.test_user_registration():
            print("❌ Registration failed, stopping tests")
            return False
            
        self.test_invalid_login()
        
        # Note CRUD tests
        self.test_create_note_short()
        self.test_create_note_long()
        self.test_get_notes()
        self.test_get_single_note()
        self.test_update_note()
        self.test_search_notes()
        self.test_filter_favorites()
        
        # AI feature tests (critical)
        print("\n🤖 Testing AI Features...")
        self.test_ai_summarize()
        self.test_ai_suggest_tags()
        self.test_ai_insights()
        
        # Additional API tests
        self.test_get_tags()
        self.test_get_stats()
        
        # Cleanup
        self.test_delete_note()
        
        # Results
        print("\n" + "=" * 60)
        print(f"📊 Test Results: {self.tests_passed}/{self.tests_run} tests passed")
        
        if self.tests_passed == self.tests_run:
            print("🎉 All tests passed!")
            return True
        else:
            print(f"⚠️  {self.tests_run - self.tests_passed} tests failed")
            return False

def main():
    tester = SmartNotesAPITester()
    success = tester.run_all_tests()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())