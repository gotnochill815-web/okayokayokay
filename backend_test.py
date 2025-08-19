import requests
import sys
import json
import time
from datetime import datetime

class OrbiAPITester:
    def __init__(self, base_url="https://prodgenius-1.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.created_items = {
            'notes': [],
            'tasks': [],
            'events': []
        }

    def run_test(self, name, method, endpoint, expected_status, data=None, timeout=30):
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}" if endpoint else f"{self.api_url}/"
        headers = {'Content-Type': 'application/json'}

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=timeout)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=timeout)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers, timeout=timeout)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers, timeout=timeout)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    response_data = response.json()
                    print(f"   Response: {json.dumps(response_data, indent=2)[:200]}...")
                    return True, response_data
                except:
                    return True, {}
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"   Error: {error_data}")
                except:
                    print(f"   Error: {response.text}")
                return False, {}

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    def test_welcome_endpoint(self):
        """Test GET /api/ - welcome message"""
        return self.run_test("Welcome Endpoint", "GET", "", 200)

    def test_note_summarization(self):
        """Test POST /api/notes/summarize - AI summarization"""
        test_data = {
            "title": "Machine Learning Basics",
            "content": "Machine learning is a subset of artificial intelligence that enables computers to learn and make decisions from data without being explicitly programmed. It involves algorithms that can identify patterns in data and make predictions or classifications based on those patterns."
        }
        
        success, response = self.run_test(
            "Note Summarization", 
            "POST", 
            "notes/summarize", 
            200, 
            test_data,
            timeout=45  # AI processing might take longer
        )
        
        if success and 'summary' in response and 'keywords' in response:
            print(f"   AI Summary: {response['summary']}")
            print(f"   Keywords: {response['keywords']}")
            return True, response
        return False, {}

    def test_create_note(self):
        """Test POST /api/notes - create note with AI summary"""
        test_data = {
            "title": "Python Programming Fundamentals",
            "content": "Python is a high-level programming language known for its simplicity and readability. It supports multiple programming paradigms including procedural, object-oriented, and functional programming. Python is widely used in web development, data science, artificial intelligence, and automation."
        }
        
        success, response = self.run_test(
            "Create Note", 
            "POST", 
            "notes", 
            200, 
            test_data,
            timeout=45  # AI processing might take longer
        )
        
        if success and 'id' in response:
            self.created_items['notes'].append(response['id'])
            print(f"   Created note ID: {response['id']}")
            if 'summary' in response:
                print(f"   AI Summary: {response['summary']}")
            if 'keywords' in response:
                print(f"   Keywords: {response['keywords']}")
        return success, response

    def test_get_notes(self):
        """Test GET /api/notes - get all notes"""
        return self.run_test("Get All Notes", "GET", "notes", 200)

    def test_schedule_parsing(self):
        """Test POST /api/schedule/parse - natural language scheduling"""
        test_data = {
            "natural_language": "Schedule Math study session tomorrow at 3 PM for calculus review"
        }
        
        success, response = self.run_test(
            "Schedule Parsing", 
            "POST", 
            "schedule/parse", 
            200, 
            test_data,
            timeout=45  # AI processing might take longer
        )
        
        if success and 'id' in response:
            self.created_items['events'].append(response['id'])
            print(f"   Created event ID: {response['id']}")
            print(f"   Event: {response.get('title', 'N/A')} on {response.get('date', 'N/A')} at {response.get('time', 'N/A')}")
        return success, response

    def test_get_schedule(self):
        """Test GET /api/schedule - get scheduled events"""
        return self.run_test("Get Schedule", "GET", "schedule", 200)

    def test_task_extraction(self):
        """Test POST /api/tasks/extract - extract tasks from conversation"""
        test_data = {
            "conversation_text": "Hey, don't forget to submit the physics assignment by Friday. Also, we need to call mom this weekend and prepare for the chemistry exam next week."
        }
        
        success, response = self.run_test(
            "Task Extraction", 
            "POST", 
            "tasks/extract", 
            200, 
            test_data,
            timeout=45  # AI processing might take longer
        )
        
        if success and 'tasks' in response:
            for task in response['tasks']:
                if 'id' in task:
                    self.created_items['tasks'].append(task['id'])
            print(f"   Extracted {len(response['tasks'])} tasks")
            for i, task in enumerate(response['tasks'][:3]):  # Show first 3 tasks
                print(f"   Task {i+1}: {task.get('title', 'N/A')} (Priority: {task.get('priority', 'N/A')})")
        return success, response

    def test_get_tasks(self):
        """Test GET /api/tasks - get all tasks"""
        return self.run_test("Get All Tasks", "GET", "tasks", 200)

    def test_complete_task(self):
        """Test PUT /api/tasks/{id}/complete - mark task complete"""
        if not self.created_items['tasks']:
            print("⚠️  No tasks available to complete")
            return False, {}
        
        task_id = self.created_items['tasks'][0]
        success, response = self.run_test(
            f"Complete Task {task_id}", 
            "PUT", 
            f"tasks/{task_id}/complete", 
            200
        )
        return success, response

    def test_delete_task(self):
        """Test DELETE /api/tasks/{id} - delete task"""
        if not self.created_items['tasks']:
            print("⚠️  No tasks available to delete")
            return False, {}
        
        task_id = self.created_items['tasks'][-1]  # Delete the last created task
        success, response = self.run_test(
            f"Delete Task {task_id}", 
            "DELETE", 
            f"tasks/{task_id}", 
            200
        )
        if success:
            self.created_items['tasks'].remove(task_id)
        return success, response

    def test_delete_note(self):
        """Test DELETE /api/notes/{id} - delete note"""
        if not self.created_items['notes']:
            print("⚠️  No notes available to delete")
            return False, {}
        
        note_id = self.created_items['notes'][-1]  # Delete the last created note
        success, response = self.run_test(
            f"Delete Note {note_id}", 
            "DELETE", 
            f"notes/{note_id}", 
            200
        )
        if success:
            self.created_items['notes'].remove(note_id)
        return success, response

def main():
    print("🚀 Starting Orbi Smart Productivity Assistant API Tests")
    print("=" * 60)
    
    tester = OrbiAPITester()
    
    # Test sequence
    test_functions = [
        tester.test_welcome_endpoint,
        tester.test_note_summarization,
        tester.test_create_note,
        tester.test_get_notes,
        tester.test_schedule_parsing,
        tester.test_get_schedule,
        tester.test_task_extraction,
        tester.test_get_tasks,
        tester.test_complete_task,
        tester.test_delete_task,
        tester.test_delete_note
    ]
    
    failed_tests = []
    
    for test_func in test_functions:
        try:
            success, _ = test_func()
            if not success:
                failed_tests.append(test_func.__name__)
        except Exception as e:
            print(f"❌ Test {test_func.__name__} crashed: {str(e)}")
            failed_tests.append(test_func.__name__)
        
        # Small delay between tests
        time.sleep(1)
    
    # Print final results
    print("\n" + "=" * 60)
    print("📊 FINAL TEST RESULTS")
    print("=" * 60)
    print(f"Tests Run: {tester.tests_run}")
    print(f"Tests Passed: {tester.tests_passed}")
    print(f"Tests Failed: {tester.tests_run - tester.tests_passed}")
    print(f"Success Rate: {(tester.tests_passed/tester.tests_run)*100:.1f}%")
    
    if failed_tests:
        print(f"\n❌ Failed Tests:")
        for test in failed_tests:
            print(f"   - {test}")
    else:
        print(f"\n✅ All tests passed!")
    
    print(f"\n📝 Created Items Summary:")
    print(f"   Notes: {len(tester.created_items['notes'])}")
    print(f"   Tasks: {len(tester.created_items['tasks'])}")
    print(f"   Events: {len(tester.created_items['events'])}")
    
    return 0 if tester.tests_passed == tester.tests_run else 1

if __name__ == "__main__":
    sys.exit(main())