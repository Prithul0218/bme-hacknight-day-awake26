import requests
import json

BASE_URL = "http://localhost:8000/api"

# Step 1: Upload the test file
print("[1] Uploading test file...")
with open("../test_financial_data.csv", "rb") as f:
    files = {"file": f}
    response = requests.post(f"{BASE_URL}/upload", files=files)
    
print(f"Upload status: {response.status_code}")
if response.status_code == 200:
    data = response.json()
    file_id = data["file_id"]
    print(f"File ID: {file_id}")
    
    # Step 2: Analyze the file
    print("\n[2] Analyzing document...")
    analyze_request = {
        "file_id": file_id,
        "departments": ["engineering", "sales", "marketing"]
    }
    
    response = requests.post(f"{BASE_URL}/analyze", json=analyze_request)
    print(f"Analysis status: {response.status_code}")
    print(f"Response: {response.text}")
else:
    print(f"Upload failed: {response.text}")
