#!/usr/bin/env python3
"""Test the scraper locally in headless mode (matches production environment)"""
from scrapers.linton_village_college import LintonVillageCollegeScraper
from database import init_db, get_session, CourtAvailability
import os

def test_headless_scraper():
    """Test the scraper in headless mode locally."""
    print("=" * 60)
    print("TESTING SCRAPER IN HEADLESS MODE (matches production)")
    print("=" * 60)
    
    # Initialize scraper in headless mode (like production)
    print("\nInitializing scraper in headless=True mode...")
    scraper = LintonVillageCollegeScraper(headless=True)
    
    try:
        print("\nStarting scrape...")
        scraper.scrape()
        print("\n✓ Scrape completed successfully!")
        
        # Check what was scraped
        print("\nChecking database for scraped data...")
        db_engine = init_db()
        session = get_session(db_engine)
        
        availability = session.query(CourtAvailability).all()
        print(f"\nFound {len(availability)} availability records in database")
        
        if availability:
            print("\nSample records:")
            for record in availability[:5]:
                print(f"  - {record.date} {record.start_time}-{record.end_time}: {'Available' if record.is_available else 'Not available'}")
        else:
            print("\n⚠️  WARNING: No availability records found!")
        
        session.close()
        return True
        
    except Exception as e:
        print(f"\n✗ Error during scrape: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_headless_scraper()
    exit(0 if success else 1)
