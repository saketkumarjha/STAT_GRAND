"""
Database schema definition for NCO Semantic Search.
Creates SQLite tables with sqlite-vss extension support for vector search.
"""

import logging
from typing import List

from .connection import DatabaseManager, get_database_manager

logger = logging.getLogger(__name__)


# SQL schema definitions
OCCUPATIONS_TABLE = """
CREATE TABLE IF NOT EXISTS occupations (
    code TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    description TEXT,
    division TEXT NOT NULL,
    major_group TEXT NOT NULL,
    sub_major_group TEXT NOT NULL,
    minor_group TEXT NOT NULL,
    unit_group TEXT NOT NULL,
    keywords TEXT,  -- JSON string
    synonyms TEXT,  -- JSON string
    embedding BLOB,  -- Serialized vector
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

OCCUPATIONS_INDEXES = [
    "CREATE INDEX IF NOT EXISTS idx_occupations_division ON occupations(division);",
    "CREATE INDEX IF NOT EXISTS idx_occupations_major_group ON occupations(major_group);",
    "CREATE INDEX IF NOT EXISTS idx_occupations_sub_major_group ON occupations(sub_major_group);",
    "CREATE INDEX IF NOT EXISTS idx_occupations_minor_group ON occupations(minor_group);",
    "CREATE INDEX IF NOT EXISTS idx_occupations_unit_group ON occupations(unit_group);",
    "CREATE INDEX IF NOT EXISTS idx_occupations_title ON occupations(title);",
    "CREATE INDEX IF NOT EXISTS idx_occupations_updated_at ON occupations(updated_at);"
]

# Vector search table using sqlite-vss (if available)
# Note: This will be created only if sqlite-vss extension is available
OCCUPATION_VECTORS_TABLE = """
CREATE VIRTUAL TABLE IF NOT EXISTS occupation_vectors USING vss0(
    embedding(768)  -- 768-dimensional vectors for sentence-transformers
);
"""

# Fallback vector search table for when sqlite-vss is not available
OCCUPATION_VECTORS_FALLBACK_TABLE = """
CREATE TABLE IF NOT EXISTS occupation_vectors_fallback (
    occupation_code TEXT PRIMARY KEY,
    embedding BLOB NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (occupation_code) REFERENCES occupations(code) ON DELETE CASCADE
);
"""

SEARCH_QUERIES_TABLE = """
CREATE TABLE IF NOT EXISTS search_queries (
    query_id TEXT PRIMARY KEY,
    original_text TEXT NOT NULL,
    processed_text TEXT,
    language TEXT NOT NULL,
    user_id TEXT,
    session_id TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    results TEXT,  -- JSON string
    selected_result TEXT,
    feedback_rating INTEGER CHECK (feedback_rating BETWEEN 1 AND 5),
    processing_time REAL
);
"""

SEARCH_QUERIES_INDEXES = [
    "CREATE INDEX IF NOT EXISTS idx_search_queries_session_id ON search_queries(session_id);",
    "CREATE INDEX IF NOT EXISTS idx_search_queries_user_id ON search_queries(user_id);",
    "CREATE INDEX IF NOT EXISTS idx_search_queries_language ON search_queries(language);",
    "CREATE INDEX IF NOT EXISTS idx_search_queries_timestamp ON search_queries(timestamp);",
    "CREATE INDEX IF NOT EXISTS idx_search_queries_feedback_rating ON search_queries(feedback_rating);"
]

USER_SESSIONS_TABLE = """
CREATE TABLE IF NOT EXISTS user_sessions (
    session_id TEXT PRIMARY KEY,
    user_id TEXT,
    language_preference TEXT DEFAULT 'en',
    accessibility_settings TEXT,  -- JSON string
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

USER_SESSIONS_INDEXES = [
    "CREATE INDEX IF NOT EXISTS idx_user_sessions_user_id ON user_sessions(user_id);",
    "CREATE INDEX IF NOT EXISTS idx_user_sessions_last_activity ON user_sessions(last_activity);"
]

# Trigger to update updated_at timestamp
UPDATE_TIMESTAMP_TRIGGER = """
CREATE TRIGGER IF NOT EXISTS update_occupations_timestamp 
AFTER UPDATE ON occupations
BEGIN
    UPDATE occupations SET updated_at = CURRENT_TIMESTAMP WHERE code = NEW.code;
END;
"""

UPDATE_SESSION_ACTIVITY_TRIGGER = """
CREATE TRIGGER IF NOT EXISTS update_session_activity 
AFTER UPDATE ON user_sessions
BEGIN
    UPDATE user_sessions SET last_activity = CURRENT_TIMESTAMP WHERE session_id = NEW.session_id;
END;
"""

# All table creation statements
ALL_TABLES = [
    OCCUPATIONS_TABLE,
    SEARCH_QUERIES_TABLE,
    USER_SESSIONS_TABLE
]

# All index creation statements
ALL_INDEXES = (
    OCCUPATIONS_INDEXES + 
    SEARCH_QUERIES_INDEXES + 
    USER_SESSIONS_INDEXES
)

# All trigger creation statements
ALL_TRIGGERS = [
    UPDATE_TIMESTAMP_TRIGGER,
    UPDATE_SESSION_ACTIVITY_TRIGGER
]


def create_tables(db_manager: DatabaseManager = None) -> bool:
    """
    Create all database tables, indexes, and triggers.
    
    Args:
        db_manager: Database manager instance (optional)
        
    Returns:
        bool: True if successful, False otherwise
    """
    if db_manager is None:
        db_manager = get_database_manager()
    
    try:
        logger.info("Creating database tables...")
        
        # Create main tables
        for table_sql in ALL_TABLES:
            db_manager.execute_update(table_sql)
            logger.debug(f"Created table: {table_sql.split()[5]}")  # Extract table name
        
        # Try to create vector search table (requires sqlite-vss)
        try:
            db_manager.execute_update(OCCUPATION_VECTORS_TABLE)
            logger.info("Created vector search table with sqlite-vss")
        except Exception as e:
            logger.warning(f"Could not create sqlite-vss vector table: {e}")
            # Create fallback vector table
            try:
                db_manager.execute_update(OCCUPATION_VECTORS_FALLBACK_TABLE)
                logger.info("Created fallback vector search table")
            except Exception as fallback_error:
                logger.error(f"Could not create fallback vector table: {fallback_error}")
                logger.info("Vector search will be disabled")
        
        # Create indexes
        for index_sql in ALL_INDEXES:
            db_manager.execute_update(index_sql)
        logger.info(f"Created {len(ALL_INDEXES)} database indexes")
        
        # Create triggers
        for trigger_sql in ALL_TRIGGERS:
            db_manager.execute_update(trigger_sql)
        logger.info(f"Created {len(ALL_TRIGGERS)} database triggers")
        
        logger.info("Database schema created successfully")
        return True
        
    except Exception as e:
        logger.error(f"Failed to create database schema: {e}")
        return False


def drop_tables(db_manager: DatabaseManager = None, confirm: bool = False) -> bool:
    """
    Drop all database tables (use with caution).
    
    Args:
        db_manager: Database manager instance (optional)
        confirm: Must be True to actually drop tables
        
    Returns:
        bool: True if successful, False otherwise
    """
    if not confirm:
        logger.warning("drop_tables called without confirmation - no action taken")
        return False
    
    if db_manager is None:
        db_manager = get_database_manager()
    
    try:
        logger.warning("Dropping all database tables...")
        
        # Drop tables in reverse order to handle dependencies
        drop_statements = [
            "DROP TABLE IF EXISTS user_sessions;",
            "DROP TABLE IF EXISTS search_queries;",
            "DROP TABLE IF EXISTS occupation_vectors;",
            "DROP TABLE IF EXISTS occupation_vectors_fallback;",
            "DROP TABLE IF EXISTS occupations;"
        ]
        
        for drop_sql in drop_statements:
            db_manager.execute_update(drop_sql)
        
        logger.warning("All database tables dropped")
        return True
        
    except Exception as e:
        logger.error(f"Failed to drop database tables: {e}")
        return False


def get_table_info(db_manager: DatabaseManager = None) -> List[dict]:
    """
    Get information about all tables in the database.
    
    Args:
        db_manager: Database manager instance (optional)
        
    Returns:
        List[dict]: Table information
    """
    if db_manager is None:
        db_manager = get_database_manager()
    
    try:
        # Get table names
        tables = db_manager.execute_query("""
            SELECT name, type FROM sqlite_master 
            WHERE type IN ('table', 'view') 
            AND name NOT LIKE 'sqlite_%'
            ORDER BY name
        """)
        
        table_info = []
        for table in tables:
            # Get column information for each table
            columns = db_manager.execute_query(f"PRAGMA table_info({table['name']})")
            
            # Get row count
            try:
                count_result = db_manager.execute_query(f"SELECT COUNT(*) as count FROM {table['name']}")
                row_count = count_result[0]['count'] if count_result else 0
            except:
                row_count = 0
            
            table_info.append({
                'name': table['name'],
                'type': table['type'],
                'columns': columns,
                'row_count': row_count
            })
        
        return table_info
        
    except Exception as e:
        logger.error(f"Failed to get table info: {e}")
        return []


def verify_schema(db_manager: DatabaseManager = None) -> dict:
    """
    Verify that the database schema is correctly set up.
    
    Args:
        db_manager: Database manager instance (optional)
        
    Returns:
        dict: Schema verification results
    """
    if db_manager is None:
        db_manager = get_database_manager()
    
    expected_tables = ['occupations', 'search_queries', 'user_sessions']
    results = {
        'schema_valid': True,
        'missing_tables': [],
        'existing_tables': [],
        'vss_available': False,
        'errors': []
    }
    
    try:
        # Check existing tables
        existing_tables = db_manager.execute_query("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name NOT LIKE 'sqlite_%'
        """)
        existing_table_names = [table['name'] for table in existing_tables]
        results['existing_tables'] = existing_table_names
        
        # Check for missing tables
        for table in expected_tables:
            if table not in existing_table_names:
                results['missing_tables'].append(table)
                results['schema_valid'] = False
        
        # Check if sqlite-vss is available
        try:
            db_manager.execute_query("SELECT name FROM sqlite_master WHERE name='occupation_vectors'")
            results['vss_available'] = 'occupation_vectors' in existing_table_names
        except:
            results['vss_available'] = False
        
        # Test basic operations on each table
        for table in existing_table_names:
            if table in expected_tables:
                try:
                    db_manager.execute_query(f"SELECT COUNT(*) FROM {table}")
                except Exception as e:
                    results['errors'].append(f"Error accessing table {table}: {e}")
                    results['schema_valid'] = False
        
    except Exception as e:
        results['schema_valid'] = False
        results['errors'].append(f"Schema verification failed: {e}")
    
    return results