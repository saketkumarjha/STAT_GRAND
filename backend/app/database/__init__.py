"""
Database package for NCO Semantic Search.
Provides database connection, schema management, and CRUD operations.
"""

from .connection import DatabaseManager, get_database_manager, reset_database_manager
from .schema import create_tables, verify_schema, get_table_info, drop_tables
from .crud import (
    OccupationCRUD, 
    SearchQueryCRUD, 
    UserSessionCRUD,
    get_occupation_crud,
    get_search_query_crud,
    get_user_session_crud
)

__all__ = [
    # Connection management
    'DatabaseManager',
    'get_database_manager',
    'reset_database_manager',
    
    # Schema management
    'create_tables',
    'verify_schema',
    'get_table_info',
    'drop_tables',
    
    # CRUD operations
    'OccupationCRUD',
    'SearchQueryCRUD',
    'UserSessionCRUD',
    'get_occupation_crud',
    'get_search_query_crud',
    'get_user_session_crud'
]