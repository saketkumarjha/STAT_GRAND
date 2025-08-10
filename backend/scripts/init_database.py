#!/usr/bin/env python3
"""
Database initialization script for NCO Semantic Search.
Creates database tables and performs initial setup.
"""

import sys
import logging
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from app.database import get_database_manager, create_tables, verify_schema, get_table_info
from app.core.config import get_settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def main():
    """Initialize the database"""
    try:
        logger.info("Starting database initialization...")
        
        # Get settings and database manager
        settings = get_settings()
        db_manager = get_database_manager()
        
        logger.info(f"Database URL: {settings.database_url}")
        
        # Check database connection
        if not db_manager.check_connection():
            logger.error("Failed to connect to database")
            return False
        
        logger.info("Database connection successful")
        
        # Get database info
        db_info = db_manager.get_database_info()
        logger.info(f"SQLite version: {db_info.get('sqlite_version', 'Unknown')}")
        logger.info(f"VSS extension available: {db_info.get('vss_available', False)}")
        
        # Create tables
        logger.info("Creating database tables...")
        if not create_tables(db_manager):
            logger.error("Failed to create database tables")
            return False
        
        logger.info("Database tables created successfully")
        
        # Verify schema
        logger.info("Verifying database schema...")
        verification = verify_schema(db_manager)
        
        if not verification["schema_valid"]:
            logger.error("Database schema verification failed")
            logger.error(f"Missing tables: {verification['missing_tables']}")
            logger.error(f"Errors: {verification['errors']}")
            return False
        
        logger.info("Database schema verification successful")
        logger.info(f"Existing tables: {verification['existing_tables']}")
        logger.info(f"VSS extension available: {verification['vss_available']}")
        
        # Get table information
        logger.info("Getting table information...")
        table_info = get_table_info(db_manager)
        
        for table in table_info:
            logger.info(f"Table '{table['name']}': {table['row_count']} rows, {len(table['columns'])} columns")
        
        logger.info("Database initialization completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)