"""Flask API for badminton court availability."""
import logging
import os
import threading
import time
from flask import Flask, jsonify, request
from flask_cors import CORS
from scraper_manager import ScraperManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Facilities to skip in scheduled scrape-all (e.g. broken scrapers). Comma-separated.
EXCLUDE_SCRAPE_FACILITIES = [
    name.strip() for name in
    os.getenv('EXCLUDE_SCRAPE_FACILITIES', 'Linton Village College').split(',')
    if name.strip()
]

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend

# Initialize scraper manager
scraper_manager = ScraperManager()


def _run_scheduled_scrapes():
    """Background thread: scrape all facilities except EXCLUDE_SCRAPE_FACILITIES. Uses its own ScraperManager."""
    excluded = set(
        name.strip() for name in
        os.getenv('EXCLUDE_SCRAPE_FACILITIES', 'Linton Village College').split(',')
        if name.strip()
    )
    delay_sec = int(os.getenv('SCRAPE_DELAY_BETWEEN_FACILITIES_SECONDS', '120'))
    sm = ScraperManager()
    try:
        facilities = [f for f in sm.get_facilities_list() if f not in excluded]
        logger.info(f"Scheduled scrape started for: {facilities} (delay between facilities: {delay_sec}s)")
        for i, name in enumerate(facilities):
            if i > 0 and delay_sec > 0:
                logger.info(f"Waiting {delay_sec}s before next facility (avoid over-hitting sites)...")
                time.sleep(delay_sec)
            try:
                result = sm.scrape_facility(name)
                logger.info(f"Scheduled scrape {name}: success={result.get('success')}")
            except Exception as e:
                logger.error(f"Scheduled scrape {name} failed: {e}")
    finally:
        sm.close()
    logger.info("Scheduled scrape run finished.")


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint."""
    return jsonify({'status': 'healthy'}), 200


@app.route('/api/availability', methods=['GET'])
def get_availability():
    """Get court availability for a facility."""
    facility_name = request.args.get('facility')
    date = request.args.get('date')
    start_time = request.args.get('start_time')
    end_time = request.args.get('end_time')
    
    if not facility_name:
        return jsonify({
            'error': 'facility parameter is required'
        }), 400
    
    try:
        result = scraper_manager.get_availability(
            facility_name=facility_name,
            date=date,
            start_time=start_time,
            end_time=end_time
        )
        
        return jsonify(result), 200
        
    except Exception as e:
        logger.error(f"Error getting availability: {e}")
        return jsonify({
            'error': str(e)
        }), 500


@app.route('/api/facilities', methods=['GET'])
def get_facilities():
    """Get list of available facilities (from scrapers + DB) and last scraped time per facility."""
    facilities = scraper_manager.get_facilities_list()
    last_updated = scraper_manager.get_facilities_last_updated()
    return jsonify({
        'facilities': facilities,
        'last_updated': last_updated
    }), 200


@app.route('/api/scrape-all', methods=['POST'])
def trigger_scrape_all():
    """Trigger scrapes for all facilities except EXCLUDE_SCRAPE_FACILITIES (e.g. broken scrapers). Runs in background; returns 202."""
    excluded = set(EXCLUDE_SCRAPE_FACILITIES)
    facilities = [f for f in scraper_manager.get_facilities_list() if f not in excluded]
    if not facilities:
        return jsonify({
            'status': 'no_facilities',
            'message': 'No facilities to scrape (all excluded or none configured)',
            'excluded': list(excluded)
        }), 200
    thread = threading.Thread(target=_run_scheduled_scrapes, daemon=True)
    thread.start()
    return jsonify({
        'status': 'accepted',
        'message': 'Scrapes started in background',
        'facilities': facilities,
        'excluded': list(excluded)
    }), 202


@app.route('/api/scrape', methods=['POST'])
def trigger_scrape():
    """Manually trigger a scrape for a facility."""
    data = request.get_json() or {}
    facility_name = data.get('facility') or request.args.get('facility')
    
    if not facility_name:
        return jsonify({
            'error': 'facility parameter is required'
        }), 400
    
    try:
        result = scraper_manager.scrape_facility(facility_name)
        return jsonify(result), 200 if result['success'] else 500
        
    except Exception as e:
        logger.error(f"Error triggering scrape: {e}")
        try:
            scraper_manager.session.rollback()
        except Exception:
            pass
        return jsonify({
            'error': str(e)
        }), 500


@app.route('/api/facility/<facility_name>/stats', methods=['GET'])
def get_facility_stats(facility_name):
    """Get scraping statistics for a facility."""
    try:
        stats = scraper_manager.get_facility_stats(facility_name)
        if not stats:
            return jsonify({
                'error': 'Facility not found'
            }), 404
        return jsonify(stats), 200
    except Exception as e:
        logger.error(f"Error getting facility stats: {e}")
        return jsonify({
            'error': str(e)
        }), 500


if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    app.run(host='0.0.0.0', port=port, debug=debug)
