# test_endpoints.py
import os
import requests
from dotenv import load_dotenv

def test_endpoint(url, headers, description):
    print(f"\nTesting {description}...")
    response = requests.get(url, headers=headers)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")
    return response.status_code == 200

def main():
    print("Loading credentials...")
    load_dotenv()
    bearer_token = os.getenv("TWITTER_BEARER_TOKEN")
    
    headers = {
        "Authorization": f"Bearer {bearer_token}",
        "Content-Type": "application/json",
    }

    # Test endpoints one by one
    endpoints = [
        {
            "url": "https://api.twitter.com/2/users/me",
            "description": "Get own user info"
        },
        {
            "url": "https://api.twitter.com/2/tweets/search/recent?query=from:twitter",
            "description": "Search tweets"
        },
        {
            "url": "https://api.twitter.com/2/tweets?ids=1234567890",
            "description": "Get tweet by ID"
        }
    ]

    results = []
    for endpoint in endpoints:
        success = test_endpoint(endpoint["url"], headers, endpoint["description"])
        results.append({
            "endpoint": endpoint["description"],
            "success": success
        })

    print("\nSummary:")
    for result in results:
        status = "✅" if result["success"] else "❌"
        print(f"{status} {result['endpoint']}")

if __name__ == "__main__":
    main()