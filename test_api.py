#!/usr/bin/env python3
"""Test script for the API endpoints."""
import requests
import json
import time
import sys

BASE_URL = 'http://localhost:5000'

def test_endpoint(name, method, url, **kwargs):
    """Test an API endpoint."""
    try:
        if method == 'GET':
            response = requests.get(url, timeout=10, **kwargs)
        elif method == 'POST':
            response = requests.post(url, timeout=10, **kwargs)
        else:
            print(f"✗ {name}: Unknown method {method}")
            return False
        
        if response.status_code == 200:
            print(f"✓ {name}: {response.status_code}")
            try:
                data = response.json()
                if isinstance(data, dict) and len(str(data)) < 500:
                    print(f"  Response: {json.dumps(data, indent=2)}")
                elif isinstance(data, list):
                    print(f"  Response: {len(data)} items")
                    if data:
                        print(f"  Sample: {json.dumps(data[0], indent=2)}")
                else:
                    print(f"  Response: {data}")
            except:
                print(f"  Response: {response.text[:200]}")
            return True
        else:
            print(f"✗ {name}: {response.status_code}")
            print(f"  Error: {response.text[:200]}")
            return False
    except requests.exceptions.ConnectionError:
        print(f"✗ {name}: Could not connect to server. Is it running?")
        print(f"  Start server with: python3 app.py")
        return False
    except Exception as e:
        print(f"✗ {name}: {e}")
        return False

def main():
    print("=" * 60)
    print("Testing Badminton Court Finder API")
    print("=" * 60)
    print()
    
    # Wait a moment for server to be ready
    print("Waiting for server to be ready...")
    time.sleep(2)
    
    results = []
    
    # Test 1: Health check
    print("\n1. Testing Health Check...")
    results.append(test_endpoint("Health Check", "GET", f"{BASE_URL}/health"))
    
    # Test 2: List facilities
    print("\n2. Testing List Facilities...")
    results.append(test_endpoint("List Facilities", "GET", f"{BASE_URL}/api/facilities"))
    
    # Test 3: Get availability (should use cache)
    print("\n3. Testing Get Availability (cached)...")
    results.append(test_endpoint(
        "Get Availability",
        "GET",
        f"{BASE_URL}/api/availability",
        params={
            'facility': 'Linton Village College',
            'date': '2026-02-06'
        }
    ))
    
    # Test 4: Get availability with time filter
    print("\n4. Testing Get Availability (with time filter)...")
    results.append(test_endpoint(
        "Get Availability (15:00-18:00)",
        "GET",
        f"{BASE_URL}/api/availability",
        params={
            'facility': 'Linton Village College',
            'date': '2026-02-06',
            'start_time': '15:00',
            'end_time': '18:00'
        }
    ))
    
    # Test 5: Facility stats
    print("\n5. Testing Facility Stats...")
    results.append(test_endpoint(
        "Facility Stats",
        "GET",
        f"{BASE_URL}/api/facility/Linton Village College/stats"
    ))
    
    # Summary
    print("\n" + "=" * 60)
    passed = sum(results)
    total = len(results)
    print(f"Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("✓ All tests passed!")
        return 0
    else:
        print("✗ Some tests failed")
        return 1

if __name__ == '__main__':
    sys.exit(main())
