import requests
import json

# Test the retrieval system
url = "http://127.0.0.1:8000/chat/non-streaming"
data = {
    "session_id": 1,
    "message": "tell me about the contract",
    "language": "english"
}

try:
    response = requests.post(url, json=data)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
except Exception as e:
    print(f"Error: {e}")
