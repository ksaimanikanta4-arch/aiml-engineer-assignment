"""
Simple test script for the QA API
"""

import requests
import sys

BASE_URL = "http://localhost:8000"


def test_health():
    """Test health endpoint"""
    print("Testing /health endpoint...")
    response = requests.get(f"{BASE_URL}/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}\n")


def test_stats():
    """Test stats endpoint"""
    print("Testing /stats endpoint...")
    response = requests.get(f"{BASE_URL}/stats")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}\n")


def test_ask(question: str):
    """Test /ask endpoint"""
    print(f"Testing /ask endpoint with question: '{question}'")
    response = requests.get(f"{BASE_URL}/ask", params={"question": question})
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"Answer: {result.get('answer', 'No answer')}\n")
    else:
        print(f"Error: {response.text}\n")


def main():
    """Run all tests"""
    print("=" * 60)
    print("Testing Member Data QA API")
    print("=" * 60)
    print()

    try:
        test_health()
        test_stats()

        # Test example questions
        test_ask("When is Layla planning her trip to London?")
        test_ask("How many cars does Vikram Desai have?")
        test_ask("What are Amira's favorite restaurants?")

        print("=" * 60)
        print("Tests completed!")
        print("=" * 60)

    except requests.exceptions.ConnectionError:
        print(
            "Error: Could not connect to the API. Make sure the server is running on http://localhost:8000"
        )
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
