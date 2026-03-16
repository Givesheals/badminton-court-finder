"""Scraper manager with rate limiting and budget controls.

All facilities use agent (LLM) scrapers for extraction; base scrapers provide
navigation only. Requires OPENAI_API_KEY for scraping.
"""
import os
from datetime import datetime, timedelta
from database import init_db, get_session, Facility, CourtAvailability
from scrapers.cherry_hinton_agent_scraper import CherryHintonAgentScraper
from scrapers.linton_agent_scraper import LintonAgentScraper
from scrapers.hill_roads_agent_scraper import HillRoadsAgentScraper
from scrapers.one_leisure_agent_scraper import (
    OneLeisureStIvesAgentScraper,
    OneLeisureStNeotsAgentScraper,
    OneLeisureHuntingdonAgentScraper,
    OneLeisureRamseyAgentScraper,
    OneLeisureSawtryAgentScraper,
)
from scrapers.trumpington_agent_scraper import TrumpingtonAgentScraper
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

    def __init__(self, engine=None):
        """Create manager. If engine is provided (e.g. app-scoped), use it; else create own (e.g. background scrapes)."""
        if engine is not None:
            self.db_engine = engine
            self.session = get_session(engine)
        else:
            self.db_engine = init_db()
            self.session = get_session(self.db_engine)
        self.scrapers = {
            'Cherry Hinton Leisure Centre': CherryHintonAgentScraper,
            'Linton Village College': LintonAgentScraper,
            'Hill Roads Sport and Tennis Centre': HillRoadsAgentScraper,
            'One Leisure St Ives': OneLeisureStIvesAgentScraper,
            'One Leisure St Neots': OneLeisureStNeotsAgentScraper,
            'One Leisure Huntingdon': OneLeisureHuntingdonAgentScraper,
            'One Leisure Ramsey': OneLeisureRamseyAgentScraper,
            'One Leisure Sawtry': OneLeisureSawtryAgentScraper,
            'Trumpington Sport': TrumpingtonAgentScraper,
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
        facility = None
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
            self._purge_past_availability()
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
            logger.exception("Error scraping %s: %s", facility_name, e)
            # Roll back so the session is usable for the next request (avoids "Can't reconnect until invalid transaction is rolled back")
            try:
                self.session.rollback()
            except Exception:
                pass
            # Update error count (may fail if DB connection is dead; that's OK)
            if facility:
                try:
                    facility.scrape_errors = (facility.scrape_errors or 0) + 1
                    self.session.commit()
                except Exception:
                    self.session.rollback()
            # Return cached data if available
            try:
                cached_data = self._get_cached_data(facility_name)
            except Exception:
                cached_data = []
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
    
    def _purge_past_availability(self):
        """Delete CourtAvailability rows where date is more than 24 hours in the past (keeps DB size down)."""
        cutoff_date = (datetime.utcnow().date() - timedelta(days=1)).isoformat()
        deleted = self.session.query(CourtAvailability).filter(CourtAvailability.date < cutoff_date).delete()
        if deleted:
            logger.info(f"Purged {deleted} past availability record(s) (date < {cutoff_date})")
    
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

    def scrape_one_leisure_sequence(self):
        """Helper to scrape all One Leisure facilities sequentially.

        Respects per-facility rate limits and returns a mapping of facility name
        to the scrape result dictionary.
        """
        one_leisure_names = [
            "One Leisure St Ives",
            "One Leisure St Neots",
            "One Leisure Huntingdon",
            "One Leisure Ramsey",
            "One Leisure Sawtry",
        ]
        results = {}
        for name in one_leisure_names:
            results[name] = self.scrape_facility(name)
        return results

    def get_facilities_last_updated(self):
        """Get last_scraped_at for all known facilities (for display). Single query instead of N+1."""
        names = self.get_facilities_list()
        # One query for all facilities that exist in DB; build name -> last_scraped_at
        facilities = self.session.query(Facility).filter(Facility.name.in_(names)).all()
        by_name = {f.name: f.last_scraped_at for f in facilities}
        return {
            n: (by_name[n].isoformat() if by_name.get(n) and by_name[n] else None)
            for n in names
        }

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

    def reset_circuit_breaker(self, facility_name):
        """Reset scrape_errors for a facility so the next scrape is not blocked by the circuit breaker."""
        facility = self.session.query(Facility).filter_by(name=facility_name).first()
        if not facility:
            return False, "Facility not found"
        facility.scrape_errors = 0
        self.session.commit()
        logger.info("Reset circuit breaker for %s", facility_name)
        return True, "Circuit breaker reset"
    
    def close(self):
        """Close database session."""
        self.session.close()
