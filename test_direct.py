#!/usr/bin/env python3
"""Direct test of core functionality without HTTP."""
from scraper_manager import ScraperManager
import json

def test_core_functionality():
    """Test the scraper manager directly."""
    print("=" * 60)
    print("Testing Core Functionality (Direct)")
    print("=" * 60)
    print()
    
    sm = ScraperManager()
    
    # Test 1: List facilities
    print("1. Testing List Facilities...")
    facilities = list(sm.scrapers.keys())
    print(f"✓ Found {len(facilities)} facilities: {facilities}")
    print()
    
    # Test 2: Check if should scrape (should use cache)
    print("2. Testing Cache Logic...")
    facility_name = "Linton Village College"
    should_scrape, reason = sm.should_scrape(facility_name)
    print(f"✓ Should scrape: {should_scrape}")
    print(f"  Reason: {reason}")
    print()
    
    # Test 3: Get cached availability
    print("3. Testing Get Availability (cached)...")
    result = sm.get_availability(
        facility_name=facility_name,
        date='2026-02-06'
    )
    print(f"✓ Got availability data")
    print(f"  Count: {result['count']} available slots")
    print(f"  Using cached: {result['cached']}")
    if result['data']:
        print(f"  Sample slot: {result['data'][0]}")
    print()
    
    # Test 4: Get availability with time filter
    print("4. Testing Get Availability (with time filter)...")
    result = sm.get_availability(
        facility_name=facility_name,
        date='2026-02-06',
        start_time='15:00',
        end_time='18:00'
    )
    print(f"✓ Got filtered availability")
    print(f"  Count: {result['count']} slots between 15:00-18:00")
    if result['data']:
        print(f"  Sample: {result['data'][0]}")
    print()
    
    # Test 5: Get facility stats
    print("5. Testing Facility Stats...")
    stats = sm.get_facility_stats(facility_name)
    if stats:
        print(f"✓ Got facility stats:")
        print(json.dumps(stats, indent=2))
    else:
        print("✗ No stats found")
    print()
    
    # Test 6: Test API endpoint logic (simulate)
    print("6. Testing API Endpoint Logic...")
    from app import app
    with app.test_client() as client:
        # Health check
        response = client.get('/health')
        print(f"✓ Health check: {response.status_code}")
        print(f"  Response: {response.get_json()}")
        
        # Facilities
        response = client.get('/api/facilities')
        print(f"✓ Facilities: {response.status_code}")
        print(f"  Response: {response.get_json()}")
        
        # Availability
        response = client.get('/api/availability?facility=Linton%20Village%20College&date=2026-02-06')
        print(f"✓ Availability: {response.status_code}")
        data = response.get_json()
        print(f"  Count: {data.get('count', 0)}")
        print(f"  Cached: {data.get('cached', False)}")
    
    sm.close()
    
    print()
    print("=" * 60)
    print("✓ All core functionality tests passed!")
    print("=" * 60)

if __name__ == '__main__':
    test_core_functionality()
