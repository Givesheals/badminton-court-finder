#!/usr/bin/env python3
"""Run all scrapers concurrently (one thread per facility). Use this to trigger a full concurrent scrape from the command line."""
import os
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed

# Add project root for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from scraper_manager import ScraperManager


def main():
    excluded = set(
        name.strip() for name in
        os.getenv('EXCLUDE_SCRAPE_FACILITIES', 'Linton Village College').split(',')
        if name.strip()
    )
    sm = ScraperManager()
    try:
        facilities = [f for f in sm.get_facilities_list() if f not in excluded]
    finally:
        sm.close()
    if not facilities:
        print("No facilities to scrape (all excluded or none configured).")
        return
    print(f"Running {len(facilities)} scrapers concurrently: {facilities}")

    def scrape_one(name):
        sm_one = ScraperManager()
        try:
            result = sm_one.scrape_facility(name)
            return name, result
        finally:
            sm_one.close()

    with ThreadPoolExecutor(max_workers=len(facilities)) as executor:
        futures = {executor.submit(scrape_one, name): name for name in facilities}
        for future in as_completed(futures):
            name = futures[future]
            try:
                _, result = future.result()
                status = "OK" if result.get('success') else "failed/cached"
                print(f"  {name}: {status}")
            except Exception as e:
                print(f"  {name}: error - {e}")
    print("Done.")


if __name__ == '__main__':
    main()
