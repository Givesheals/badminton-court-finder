"""Database models and setup for court availability storage."""
import os
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

Base = declarative_base()


class Facility(Base):
    """Represents a sports facility."""
    __tablename__ = 'facilities'
    
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)
    hall_name = Column(String)  # e.g., "New Gym", "Sports Hall"
    created_at = Column(DateTime, default=datetime.utcnow)
    last_scraped_at = Column(DateTime)  # Last successful scrape
    scrape_count_today = Column(Integer, default=0)  # Scrapes today
    last_scrape_date = Column(String)  # Date of last scrape (YYYY-MM-DD)
    scrape_errors = Column(Integer, default=0)  # Consecutive errors


class CourtAvailability(Base):
    """Represents available court time slots."""
    __tablename__ = 'court_availability'
    
    id = Column(Integer, primary_key=True)
    facility_id = Column(Integer, nullable=False)
    court_number = Column(String)  # e.g., "Court 1", "Court 2"
    date = Column(String, nullable=False)  # e.g., "2024-01-15"
    day_name = Column(String)  # e.g., "Wednesday"
    start_time = Column(String, nullable=False)  # e.g., "18:00"
    end_time = Column(String, nullable=False)  # e.g., "20:00"
    is_available = Column(Boolean, default=True)
    scraped_at = Column(DateTime, default=datetime.utcnow)


def init_db(db_path=None):
    """
    Initialize the database and create tables.
    - If DATABASE_URL is set (e.g. Render Postgres): use PostgreSQL.
    - Else if DB_PATH is set: use SQLite at that path.
    - Else: use SQLite at court_availability.db (local dev).
    """
    database_url = os.getenv('DATABASE_URL')
    if database_url:
        # Render and others use postgres:// but SQLAlchemy 1.4+ expects postgresql://
        if database_url.startswith('postgres://'):
            database_url = database_url.replace('postgres://', 'postgresql://', 1)
        engine = create_engine(database_url)
    else:
        path = db_path or os.getenv('DB_PATH', 'court_availability.db')
        engine = create_engine(f'sqlite:///{path}')
    Base.metadata.create_all(engine)
    return engine


def get_session(engine):
    """Get a database session."""
    Session = sessionmaker(bind=engine)
    return Session()
