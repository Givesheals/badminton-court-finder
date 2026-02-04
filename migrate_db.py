"""Database migration script to add new columns to Facility table."""
from database import init_db, get_session, Facility, Base
from sqlalchemy import inspect, text

def migrate():
    """Add new columns to Facility table if they don't exist."""
    engine = init_db()
    session = get_session(engine)
    
    try:
        # Get table info
        inspector = inspect(engine)
        columns = [col['name'] for col in inspector.get_columns('facilities')]
        
        # SQLite doesn't support all ALTER TABLE operations well
        # So we'll just recreate the table with new columns if needed
        # But first, let's try to add columns (SQLite 3.1.3+ supports ADD COLUMN)
        
        new_columns = {
            'last_scraped_at': 'DATETIME',
            'scrape_count_today': 'INTEGER DEFAULT 0',
            'last_scrape_date': 'VARCHAR',
            'scrape_errors': 'INTEGER DEFAULT 0'
        }
        
        for col_name, col_type in new_columns.items():
            if col_name not in columns:
                print(f"Adding column '{col_name}'...")
                try:
                    session.execute(text(f"ALTER TABLE facilities ADD COLUMN {col_name} {col_type}"))
                    session.commit()
                    print(f"  ✓ Added {col_name}")
                except Exception as e:
                    print(f"  ✗ Error adding {col_name}: {e}")
                    session.rollback()
            else:
                print(f"Column '{col_name}' already exists")
        
        # Verify by querying
        test_facility = session.query(Facility).first()
        if test_facility:
            # Try to access new attributes
            _ = test_facility.last_scraped_at
            _ = test_facility.scrape_count_today
            _ = test_facility.last_scrape_date
            _ = test_facility.scrape_errors
        
        print("Migration completed successfully!")
        
    except Exception as e:
        print(f"Migration error: {e}")
        import traceback
        traceback.print_exc()
        session.rollback()
    finally:
        session.close()

if __name__ == '__main__':
    migrate()
