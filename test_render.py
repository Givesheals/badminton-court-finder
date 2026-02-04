#!/usr/bin/env python3
"""Test the deployed Render API"""
import requests
import json
from datetime import datetime

BASE_URL = "https://badminton-court-finder.onrender.com"

def test_health():
    """Test health endpoint"""
    print("\n1. Testing /health endpoint...")
    response = requests.get(f"{BASE_URL}/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    return response.status_code == 200

def test_facilities():
    """Test facilities endpoint"""
    print("\n2. Testing /api/facilities endpoint...")
    response = requests.get(f"{BASE_URL}/api/facilities")
    print(f"Status: {response.status_code}")
    data = response.json()
    print(f"Response: {json.dumps(data, indent=2)}")
    return response.status_code == 200

def test_availability():
    """Test availability endpoint - this will trigger a scrape"""
    print("\n3. Testing /api/availability endpoint (will scrape)...")
    print("This may take 30-60 seconds as it's scraping the website...")
    params = {"facility": "Linton Village College"}
    response = requests.get(f"{BASE_URL}/api/availability", params=params, timeout=120)
    print(f"Status: {response.status_code}")
    data = response.json()
    
    if response.status_code == 200:
        if isinstance(data, list):
            print(f"Found {len(data)} availability entries")
            if data:
                print(f"Sample entry: {json.dumps(data[0], indent=2)}")
        else:
            print(f"Response: {json.dumps(data, indent=2)}")
    else:
        print(f"Response: {json.dumps(data, indent=2)}")
    
    return response.status_code == 200

def test_facility_stats():
    """Test facility stats endpoint"""
    print("\n4. Testing /api/facility/<name>/stats endpoint...")
    response = requests.get(f"{BASE_URL}/api/facility/Linton Village College/stats")
    print(f"Status: {response.status_code}")
    data = response.json()
    print(f"Response: {json.dumps(data, indent=2)}")
    return response.status_code == 200

if __name__ == "__main__":
    print("=" * 60)
    print("TESTING RENDER DEPLOYMENT")
    print(f"Base URL: {BASE_URL}")
    print("=" * 60)
    
    results = []
    results.append(("Health Check", test_health()))
    results.append(("Facilities List", test_facilities()))
    results.append(("Availability (Scrape)", test_availability()))
    results.append(("Facility Stats", test_facility_stats()))
    
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    for name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status} - {name}")
    
    all_passed = all(result[1] for result in results)
    if all_passed:
        print("\n🎉 ALL TESTS PASSED! Your API is live and working!")
    else:
        print("\n⚠️  Some tests failed - check the output above")
