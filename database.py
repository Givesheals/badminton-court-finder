"""Database models and setup for court availability storage."""
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


def init_db(db_path='court_availability.db'):
    """Initialize the database and create tables."""
    engine = create_engine(f'sqlite:///{db_path}')
    Base.metadata.create_all(engine)
    return engine


def get_session(engine):
    """Get a database session."""
    Session = sessionmaker(bind=engine)
    return Session()
