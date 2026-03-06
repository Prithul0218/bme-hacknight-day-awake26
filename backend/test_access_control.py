"""
Test suite for access control implementation.
Tests different user roles accessing files with different classifications.
"""

import requests
import json
from pathlib import Path

BASE_URL = "http://localhost:8000"

# Create a simple test CSV file
TEST_FILE_PATH = "test_financial_data.csv"
TEST_CSV_CONTENT = """Date,Revenue,Expenses,Department
2024-01-01,100000,75000,Engineering
2024-01-02,120000,85000,Sales
2024-01-03,95000,70000,Marketing
2024-01-04,110000,80000,Operations
2024-01-05,105000,72000,Finance
"""

def setup_test_file():
    """Create test CSV file."""
    with open(TEST_FILE_PATH, 'w') as f:
        f.write(TEST_CSV_CONTENT)
    print(f"✓ Test file created: {TEST_FILE_PATH}")

def cleanup_test_file():
    """Remove test CSV file."""
    if Path(TEST_FILE_PATH).exists():
        Path(TEST_FILE_PATH).unlink()
        print(f"✓ Test file cleaned up")

def upload_file(classification, user_role="employee"):
    """Upload a file with specified classification."""
    with open(TEST_FILE_PATH, 'rb') as f:
        files = {'file': f}
        params = {'classification': classification}
        headers = {'X-User-Role': user_role}
        
        response = requests.post(
            f"{BASE_URL}/api/upload",
            files=files,
            params=params,
            headers=headers
        )
    
    if response.status_code == 200:
        data = response.json()
        print(f"✓ Uploaded {classification} file: {data['file_id']}")
        return data['file_id']
    else:
        print(f"✗ Upload failed: {response.status_code} - {response.text}")
        return None

def test_chat_access(file_id, user_role, classification):
    """Test chat access with given user role."""
    question = "What is the total revenue?"
    headers = {
        'Content-Type': 'application/json',
        'X-User-Role': user_role
    }
    
    payload = {
        'file_id': file_id,
        'question': question,
        'departments': []
    }
    
    response = requests.post(
        f"{BASE_URL}/api/chat",
        json=payload,
        headers=headers
    )
    
    user_display = user_role.title().ljust(12)
    classification_display = classification.replace('_', ' ').title().ljust(25)
    
    if response.status_code == 200:
        print(f"  {user_display} → {classification_display} ✓ Allowed")
        return True
    elif response.status_code == 403:
        print(f"  {user_display} → {classification_display} ✗ Denied (as expected)")
        return False
    else:
        print(f"  {user_display} → {classification_display} ? Unexpected: {response.status_code}")
        return None

def test_access_matrix():
    """Test the complete access control matrix."""
    
    print("\n" + "="*70)
    print("ACCESS CONTROL MATRIX TEST")
    print("="*70)
    
    roles = ['employee', 'finance', 'management', 'admin']
    classifications = [
        'public_company',
        'finance_only',
        'management_only',
        'admin_only'
    ]
    
    # Upload files with each classification
    file_ids = {}
    print("\n1. UPLOADING FILES WITH DIFFERENT CLASSIFICATIONS:")
    print("-" * 70)
    
    for classification in classifications:
        file_id = upload_file(classification)
        if file_id:
            file_ids[classification] = file_id
    
    # Test access for each role to each file classification
    print("\n2. TESTING ACCESS CONTROL:")
    print("-" * 70)
    
    # Expected results matrix
    expected_access = {
        'employee': {
            'public_company': True,
            'finance_only': False,
            'management_only': False,
            'admin_only': False
        },
        'finance': {
            'public_company': True,
            'finance_only': True,
            'management_only': False,
            'admin_only': False
        },
        'management': {
            'public_company': True,
            'finance_only': False,
            'management_only': True,
            'admin_only': False
        },
        'admin': {
            'public_company': True,
            'finance_only': True,
            'management_only': True,
            'admin_only': True
        }
    }
    
    results = {}
    for classification in classifications:
        if classification not in file_ids:
            continue
        
        file_id = file_ids[classification]
        print(f"\nTesting {classification.replace('_', ' ').upper()} file:")
        
        for role in roles:
            access_allowed = test_chat_access(file_id, role, classification)
            
            if access_allowed is not None:
                expected = expected_access[role][classification]
                is_correct = access_allowed == expected
                status = "✓" if is_correct else "✗"
                
                key = f"{role}_{classification}"
                results[key] = {
                    'expected': expected,
                    'actual': access_allowed,
                    'correct': is_correct
                }

    # Print summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    
    all_results = list(results.values())
    passed = sum(1 for r in all_results if r['correct'])
    total = len(all_results)
    
    print(f"\nTotal Tests: {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {total - passed}")
    
    if passed == total:
        print("\n✓ ALL TESTS PASSED!")
    else:
        failed_tests = [k for k, v in results.items() if not v['correct']]
        print(f"\n✗ Failed tests: {', '.join(failed_tests)}")
    
    return passed == total

def main():
    """Run all access control tests."""
    print("\n📋 Starting Access Control Test Suite\n")
    
    try:
        setup_test_file()
        
        # Test the access matrix
        success = test_access_matrix()
        
        cleanup_test_file()
        
        print("\n" + "="*70)
        if success:
            print("✓ Access Control Implementation Successful!")
        else:
            print("✗ Some access control tests failed")
        print("="*70 + "\n")
        
        return 0 if success else 1
        
    except requests.exceptions.ConnectionError:
        print("✗ Could not connect to server. Is it running on localhost:8000?")
        cleanup_test_file()
        return 1
    except Exception as e:
        print(f"✗ Test error: {e}")
        cleanup_test_file()
        return 1

if __name__ == '__main__':
    exit(main())
