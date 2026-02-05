"""Quick script to verify DB contents: list facilities and availability counts."""
import os
import sys

# Run from project root so we use the same DB path as the app
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from database import init_db, get_session, Facility, CourtAvailability
from datetime import datetime, timedelta

def main():
    db_path = os.getenv("DB_PATH", "court_availability.db")
    engine = init_db(db_path)
    session = get_session(engine)

    print(f"Database: {db_path}")
    print("-" * 50)
    facilities = session.query(Facility).all()
    if not facilities:
        print("No facilities in database.")
        session.close()
        return

    cutoff = (datetime.utcnow() - timedelta(days=14)).date().isoformat()
    for f in facilities:
        total = session.query(CourtAvailability).filter_by(facility_id=f.id).count()
        available = session.query(CourtAvailability).filter_by(
            facility_id=f.id, is_available=True
        ).filter(CourtAvailability.date >= cutoff).count()
        print(f"  {f.name!r}")
        print(f"    id={f.id}, total slots={total}, available (last 14d)={available}")
    print("-" * 50)
    session.close()

if __name__ == "__main__":
    main()
