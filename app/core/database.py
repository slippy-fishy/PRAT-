"""
Database configuration and connection setup
"""
import logging
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from contextlib import contextmanager

from app.config import settings

logger = logging.getLogger(__name__)

# Database engine
engine = None
SessionLocal = None

def init_database():
    """Initialize database connection"""
    global engine, SessionLocal
    
    try:
        if settings.database_url:
            # Use PostgreSQL if configured
            engine = create_engine(
                settings.database_url,
                pool_pre_ping=True,
                pool_recycle=300,
                echo=settings.debug
            )
            logger.info("Connected to PostgreSQL database")
        else:
            # Fallback to SQLite for development
            engine = create_engine(
                "sqlite:///./prat.db",
                connect_args={"check_same_thread": False},
                poolclass=StaticPool,
                echo=settings.debug
            )
            logger.info("Connected to SQLite database (development mode)")
        
        # Create session factory
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        
        # Create tables only if they don't exist
        create_tables()
        
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise

def create_tables():
    """Create all database tables only if they don't exist"""
    try:
        from app.models.database_models import Base
        
        # Check if tables already exist
        inspector = inspect(engine)
        existing_tables = inspector.get_table_names()
        required_tables = ['purchase_orders', 'po_line_items', 'invoices', 'invoice_line_items', 'processing_history']
        
        if all(table in existing_tables for table in required_tables):
            logger.info("All required tables already exist, skipping table creation")
            return
        
        # Create tables only if they don't exist
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Failed to create tables: {e}")
        raise

def get_db() -> Session:
    """Get database session"""
    if not SessionLocal:
        init_database()
    
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@contextmanager
def get_db_context():
    """Context manager for database sessions"""
    if not SessionLocal:
        init_database()
    
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

def close_database():
    """Close database connection"""
    global engine
    if engine:
        engine.dispose()
        logger.info("Database connection closed")
