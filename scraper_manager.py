"""Scraper manager with rate limiting and budget controls."""
import os
from datetime import datetime, timedelta
from database import init_db, get_session, Facility, CourtAvailability
from scrapers.linton_village_college import LintonVillageCollegeScraper
from scrapers.hill_roads import HillRoadsScraper
from scrapers.one_leisure_st_ives import OneLeisureStIvesScraper
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ScraperManager:
    """Manages scraping with rate limiting and budget controls."""
    
    # Budget and rate limiting settings
    MAX_SCRAPES_PER_DAY = int(os.getenv('MAX_SCRAPES_PER_DAY', '3'))
    MAX_SCRAPES_PER_HOUR = int(os.getenv('MAX_SCRAPES_PER_HOUR', '1'))
    MIN_CACHE_AGE_SECONDS = int(os.getenv('MIN_CACHE_AGE_SECONDS', '3600'))  # 1 hour
    MAX_CONSECUTIVE_ERRORS = 3  # Circuit breaker threshold
    
    def __init__(self):
        self.db_engine = init_db()
        self.session = get_session(self.db_engine)
        self.scrapers = {
            'Linton Village College': LintonVillageCollegeScraper,
            'Hill Roads Sport and Tennis Centre': HillRoadsScraper,
            'One Leisure St Ives': OneLeisureStIvesScraper,
        }
    
    def should_scrape(self, facility_name):
        """Check if we should scrape based on cache age and rate limits."""
        facility = self.session.query(Facility).filter_by(name=facility_name).first()
        
        if not facility:
            logger.info(f"Facility {facility_name} not found, will scrape")
            return True, "Facility not found"
        
        # Circuit breaker: too many consecutive errors
        if facility.scrape_errors and facility.scrape_errors >= self.MAX_CONSECUTIVE_ERRORS:
            logger.warning(f"Circuit breaker active for {facility_name}: {facility.scrape_errors} consecutive errors")
            return False, f"Circuit breaker: {facility.scrape_errors} consecutive errors"
        
        # Check cache age
        if facility.last_scraped_at:
            age = (datetime.utcnow() - facility.last_scraped_at).total_seconds()
            if age < self.MIN_CACHE_AGE_SECONDS:
                logger.info(f"Cache fresh for {facility_name}: {age:.0f}s old")
                return False, f"Cache fresh: {age:.0f}s old"
        
        # Check daily limit
        today = datetime.utcnow().date().isoformat()
        if facility.last_scrape_date == today:
            if facility.scrape_count_today >= self.MAX_SCRAPES_PER_DAY:
                logger.warning(f"Daily limit reached for {facility_name}: {facility.scrape_count_today} scrapes")
                return False, f"Daily limit reached: {facility.scrape_count_today}/{self.MAX_SCRAPES_PER_DAY}"
        else:
            # New day, reset counter
            facility.scrape_count_today = 0
            facility.last_scrape_date = today
            self.session.commit()
        
        # Check hourly limit (simplified: if scraped in last hour)
        if facility.last_scraped_at:
            hours_since = (datetime.utcnow() - facility.last_scraped_at).total_seconds() / 3600
            if hours_since < 1 and facility.scrape_count_today >= self.MAX_SCRAPES_PER_HOUR:
                logger.warning(f"Hourly limit reached for {facility_name}")
                return False, "Hourly limit reached"
        
        logger.info(f"Scraping approved for {facility_name}")
        return True, "Cache stale or missing"
    
    def scrape_facility(self, facility_name):
        """Scrape a facility with error handling and rate limiting."""
        should_scrape, reason = self.should_scrape(facility_name)
        
        if not should_scrape:
            return {
                'success': False,
                'cached': True,
                'reason': reason,
                'data': self._get_cached_data(facility_name)
            }
        
        facility = self.session.query(Facility).filter_by(name=facility_name).first()
        if not facility:
            # Create facility
            facility = Facility(name=facility_name)
            self.session.add(facility)
            self.session.commit()
        
        # Get scraper class
        scraper_class = self.scrapers.get(facility_name)
        if not scraper_class:
            return {
                'success': False,
                'error': f'No scraper found for {facility_name}'
            }
        
        try:
            logger.info(f"Starting scrape for {facility_name}")
            scraper = scraper_class(headless=True)
            scraper.scrape()
            
            # Update facility metadata
            facility.last_scraped_at = datetime.utcnow()
            today = datetime.utcnow().date().isoformat()
            if facility.last_scrape_date != today:
                facility.scrape_count_today = 1
                facility.last_scrape_date = today
            else:
                facility.scrape_count_today += 1
            facility.scrape_errors = 0  # Reset error count on success
            self.session.commit()
            
            logger.info(f"Successfully scraped {facility_name}")
            return {
                'success': True,
                'cached': False,
                'facility': facility_name,
                'scraped_at': facility.last_scraped_at.isoformat(),
                'data': self._get_cached_data(facility_name)
            }
            
        except Exception as e:
            logger.error(f"Error scraping {facility_name}: {e}")
            
            # Update error count
            if facility:
                facility.scrape_errors = (facility.scrape_errors or 0) + 1
                self.session.commit()
            
            # Return cached data if available
            cached_data = self._get_cached_data(facility_name)
            return {
                'success': False,
                'error': str(e),
                'cached': len(cached_data) > 0 if cached_data else False,
                'data': cached_data
            }
    
    def _get_cached_data(self, facility_name):
        """Get cached availability data for a facility."""
        facility = self.session.query(Facility).filter_by(name=facility_name).first()
        if not facility:
            return []
        
        # Get recent availability (last 14 days)
        cutoff_date = (datetime.utcnow() - timedelta(days=14)).date().isoformat()
        records = self.session.query(CourtAvailability).filter_by(
            facility_id=facility.id,
            is_available=True
        ).filter(
            CourtAvailability.date >= cutoff_date
        ).order_by(
            CourtAvailability.date,
            CourtAvailability.start_time
        ).all()
        
        return [{
            'date': r.date,
            'day_name': r.day_name,
            'start_time': r.start_time,
            'end_time': r.end_time,
            'court_number': r.court_number,
            'scraped_at': r.scraped_at.isoformat() if r.scraped_at else None
        } for r in records]
    
    def get_availability(self, facility_name, date=None, start_time=None, end_time=None):
        """Get availability for a facility from the database only (no scrape on request)."""
        # Always return cached/DB data. Scraping is triggered separately via /api/scrape or scheduled jobs.
        data = self._get_cached_data(facility_name)
        
        # Apply filters
        if date:
            data = [d for d in data if d['date'] == date]
        
        if start_time:
            data = [d for d in data if d['start_time'] >= start_time]
        
        if end_time:
            data = [d for d in data if d['end_time'] <= end_time]
        
        return {
            'facility': facility_name,
            'count': len(data),
            'data': data,
            'cached': True
        }
    
    def get_facilities_list(self):
        """Return facility names from scrapers and DB so all known facilities appear (e.g. after new scraper added)."""
        from_scrapers = set(self.scrapers.keys())
        from_db = {f.name for f in self.session.query(Facility).all()}
        return sorted(from_scrapers | from_db)

    def get_facilities_last_updated(self):
        """Get last_scraped_at for all known facilities (for display)."""
        names = self.get_facilities_list()
        result = {}
        for name in names:
            facility = self.session.query(Facility).filter_by(name=name).first()
            if facility and facility.last_scraped_at:
                result[name] = facility.last_scraped_at.isoformat()
            else:
                result[name] = None
        return result

    def get_facility_stats(self, facility_name):
        """Get statistics about a facility's scraping."""
        facility = self.session.query(Facility).filter_by(name=facility_name).first()
        if not facility:
            return None

        # Get data freshness
        cached_data = self._get_cached_data(facility_name)
        latest_scrape = facility.last_scraped_at

        return {
            'facility': facility_name,
            'last_scraped_at': latest_scrape.isoformat() if latest_scrape else None,
            'scrape_count_today': facility.scrape_count_today or 0,
            'scrape_errors': facility.scrape_errors or 0,
            'cached_slots': len(cached_data),
            'circuit_breaker_active': (facility.scrape_errors or 0) >= self.MAX_CONSECUTIVE_ERRORS
        }
    
    def close(self):
        """Close database session."""
        self.session.close()
