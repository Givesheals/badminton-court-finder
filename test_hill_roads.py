#!/usr/bin/env python3
"""Test the Hill Roads scraper locally to inspect page structure"""
from scrapers.hill_roads import HillRoadsScraper

def test_scraper():
    """Test the scraper in non-headless mode to see what's happening."""
    print("=" * 60)
    print("TESTING HILL ROADS SCRAPER (non-headless for debugging)")
    print("=" * 60)
    
    # Initialize scraper in non-headless mode so we can see what's happening
    scraper = HillRoadsScraper(headless=False)
    
    try:
        print("\nStarting scrape...")
        scraper.scrape()
        print("\n✓ Scrape completed successfully!")
    except Exception as e:
        print(f"\n✗ Error during scrape: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_scraper()
