"""Flask API for badminton court availability."""
import logging
import os
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from flask import Flask, jsonify, request
from flask_cors import CORS
from database import init_db
from scraper_manager import ScraperManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Facilities to skip in scheduled scrape-all. Comma-separated. Default: Linton (bot protection returns 403).
EXCLUDE_SCRAPE_FACILITIES = [
    name.strip() for name in
    os.getenv('EXCLUDE_SCRAPE_FACILITIES', 'Linton Village College').split(',')
    if name.strip()
]

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend

# One engine per process for read paths (find courts); avoids per-request engine/connection creation.
db_engine = init_db()


def _run_scheduled_scrapes():
    """Background thread: scrape all facilities except EXCLUDE_SCRAPE_FACILITIES. Uses its own ScraperManager."""
    excluded = set(
        name.strip() for name in
        os.getenv('EXCLUDE_SCRAPE_FACILITIES', 'Linton Village College').split(',')
        if name.strip()
    )
    delay_sec = int(os.getenv('SCRAPE_DELAY_BETWEEN_FACILITIES_SECONDS', '1'))
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


def _run_scheduled_scrapes_concurrent():
    """Background: scrape all facilities concurrently (one thread per facility, each with its own ScraperManager)."""
    excluded = set(
        name.strip() for name in
        os.getenv('EXCLUDE_SCRAPE_FACILITIES', 'Linton Village College').split(',')
        if name.strip()
    )
    sm = ScraperManager()
    try:
        facilities = [f for f in sm.get_facilities_list() if f not in excluded]
        sm.close()
    except Exception:
        if sm:
            sm.close()
        raise
    if not facilities:
        logger.info("No facilities to scrape (all excluded or none configured).")
        return
    logger.info(f"Concurrent scrape started for: {facilities}")

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
                logger.info(f"Concurrent scrape {name}: success={result.get('success')}")
            except Exception as e:
                logger.error(f"Concurrent scrape {name} failed: {e}")
    logger.info("Concurrent scrape run finished.")


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
        sm = ScraperManager(engine=db_engine)
        try:
            result = sm.get_availability(
                facility_name=facility_name,
                date=date,
                start_time=start_time,
                end_time=end_time
            )
            return jsonify(result), 200
        finally:
            sm.close()
    except Exception as e:
        logger.exception("Error getting availability")
        return jsonify({'error': str(e)}), 500


@app.route('/api/facilities', methods=['GET'])
def get_facilities():
    """Get list of available facilities (from scrapers + DB) and last scraped time per facility."""
    try:
        sm = ScraperManager(engine=db_engine)
        try:
            facilities = sm.get_facilities_list()
            last_updated = sm.get_facilities_last_updated()
            return jsonify({
                'facilities': facilities,
                'last_updated': last_updated
            }), 200
        finally:
            sm.close()
    except Exception as e:
        logger.exception("Error getting facilities")
        return jsonify({'error': str(e)}), 500


@app.route('/api/scrape-all', methods=['POST'])
def trigger_scrape_all():
    """Trigger scrapes for all facilities except EXCLUDE_SCRAPE_FACILITIES (e.g. broken scrapers). Runs in background; returns 202.
    Use ?concurrent=1 or JSON body {"concurrent": true} to run all scrapers concurrently instead of sequentially with delay."""
    excluded = set(EXCLUDE_SCRAPE_FACILITIES)
    try:
        sm = ScraperManager(engine=db_engine)
        try:
            facilities = [f for f in sm.get_facilities_list() if f not in excluded]
        finally:
            sm.close()
    except Exception as e:
        logger.exception("Error getting facilities list for scrape-all")
        return jsonify({'error': str(e)}), 500
    if not facilities:
        return jsonify({
            'status': 'no_facilities',
            'message': 'No facilities to scrape (all excluded or none configured)',
            'excluded': list(excluded)
        }), 200
    data = request.get_json(silent=True) or {}
    concurrent = (
        request.args.get('concurrent', '').lower() in ('1', 'true', 'yes')
        or data.get('concurrent') is True
        or (isinstance(data.get('concurrent'), str) and data.get('concurrent', '').lower() in ('true', 'yes', '1'))
    )
    target = _run_scheduled_scrapes_concurrent if concurrent else _run_scheduled_scrapes
    thread = threading.Thread(target=target, daemon=True)
    thread.start()
    return jsonify({
        'status': 'accepted',
        'message': 'Scrapes started in background (concurrent)' if concurrent else 'Scrapes started in background',
        'facilities': facilities,
        'excluded': list(excluded),
        'concurrent': concurrent
    }), 202


@app.route('/api/scrape', methods=['POST'])
def trigger_scrape():
    """Manually trigger a scrape for a facility. Set reset_errors=true to clear circuit breaker first."""
    data = request.get_json() or {}
    facility_name = data.get('facility') or request.args.get('facility')
    reset_errors = (
        data.get('reset_errors') is True
        or request.args.get('reset_errors', '').lower() in ('1', 'true', 'yes')
    )

    if not facility_name:
        return jsonify({
            'error': 'facility parameter is required'
        }), 400

    try:
        sm = ScraperManager(engine=db_engine)
        try:
            if reset_errors:
                ok, _ = sm.reset_circuit_breaker(facility_name)
                if ok:
                    logger.info("Circuit breaker reset for %s before scrape", facility_name)
            result = sm.scrape_facility(facility_name)
            return jsonify(result), 200 if result['success'] else 500
        finally:
            sm.close()
    except Exception as e:
        logger.exception("Error triggering scrape: %s", e)
        return jsonify({'error': str(e)}), 500


@app.route('/api/facility/<path:facility_name>/stats', methods=['GET'])
def get_facility_stats(facility_name):
    """Get scraping statistics for a facility."""
    try:
        sm = ScraperManager(engine=db_engine)
        try:
            stats = sm.get_facility_stats(facility_name)
            if not stats:
                return jsonify({'error': 'Facility not found'}), 404
            return jsonify(stats), 200
        finally:
            sm.close()
    except Exception as e:
        logger.exception("Error getting facility stats: %s", e)
        return jsonify({'error': str(e)}), 500


@app.route('/api/facility/<path:facility_name>/reset-circuit-breaker', methods=['POST'])
def reset_circuit_breaker(facility_name):
    """Reset circuit breaker (scrape_errors) for a facility so the next scrape is not blocked."""
    try:
        sm = ScraperManager(engine=db_engine)
        try:
            ok, message = sm.reset_circuit_breaker(facility_name)
            if not ok:
                return jsonify({'error': message}), 404
            return jsonify({'status': 'ok', 'message': message}), 200
        finally:
            sm.close()
    except Exception as e:
        logger.exception("Error resetting circuit breaker: %s", e)
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    app.run(host='0.0.0.0', port=port, debug=debug)
