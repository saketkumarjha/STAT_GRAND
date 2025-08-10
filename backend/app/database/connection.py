"""
Database connection management for NCO Semantic Search.
Handles SQLite database with sqlite-vss extension for vector search capabilities.
"""

import sqlite3
import logging
import json
import numpy as np
from typing import Optional, Dict, Any, List
from contextlib import asynccontextmanager
import aiosqlite
from pathlib import Path

from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class DatabaseManager:
    """
    Manages SQLite database connections with sqlite-vss extension for vector search.
    Provides both synchronous and asynchronous database operations.
    """
    
    def __init__(self, database_url: str = None):
        """Initialize database manager with connection URL"""
        self.database_url = database_url or settings.database_url
        self.db_path = self._extract_db_path(self.database_url)
        self._ensure_db_directory()
        
    def _extract_db_path(self, database_url: str) -> str:
        """Extract database file path from SQLite URL"""
        if database_url.startswith("sqlite:///"):
            return database_url[10:]  # Remove 'sqlite:///' prefix
        elif database_url.startswith("sqlite://"):
            return database_url[9:]   # Remove 'sqlite://' prefix
        else:
            return database_url
    
    def _ensure_db_directory(self):
        """Ensure database directory exists"""
        db_path = Path(self.db_path)
        db_path.parent.mkdir(parents=True, exist_ok=True)
    
    def get_sync_connection(self) -> sqlite3.Connection:
        """
        Get synchronous SQLite connection with sqlite-vss extension loaded.
        
        Returns:
            sqlite3.Connection: Database connection with vector search capabilities
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row  # Enable dict-like access to rows
            
            # Enable foreign keys
            conn.execute("PRAGMA foreign_keys = ON")
            
            # Try to load sqlite-vss extension
            try:
                conn.enable_load_extension(True)
                conn.load_extension("vss0")
                logger.info("sqlite-vss extension loaded successfully")
            except sqlite3.OperationalError as e:
                logger.warning(f"Could not load sqlite-vss extension: {e}")
                logger.info("Vector search will use fallback implementation")
            
            return conn
            
        except sqlite3.Error as e:
            logger.error(f"Failed to connect to database: {e}")
            raise
    
    @asynccontextmanager
    async def get_async_connection(self):
        """
        Get asynchronous SQLite connection context manager.
        
        Yields:
            aiosqlite.Connection: Async database connection
        """
        try:
            async with aiosqlite.connect(self.db_path) as conn:
                # Enable dict-like access to rows
                conn.row_factory = aiosqlite.Row
                
                # Enable foreign keys
                await conn.execute("PRAGMA foreign_keys = ON")
                
                # Try to load sqlite-vss extension
                try:
                    await conn.enable_load_extension(True)
                    await conn.load_extension("vss0")
                    logger.debug("sqlite-vss extension loaded for async connection")
                except aiosqlite.OperationalError as e:
                    logger.debug(f"sqlite-vss not available for async connection: {e}")
                
                yield conn
                
        except aiosqlite.Error as e:
            logger.error(f"Failed to connect to async database: {e}")
            raise
    
    def execute_query(self, query: str, params: tuple = None) -> List[Dict[str, Any]]:
        """
        Execute a SELECT query and return results as list of dictionaries.
        
        Args:
            query: SQL query string
            params: Query parameters tuple
            
        Returns:
            List[Dict[str, Any]]: Query results
        """
        with self.get_sync_connection() as conn:
            cursor = conn.execute(query, params or ())
            return [dict(row) for row in cursor.fetchall()]
    
    def execute_update(self, query: str, params: tuple = None) -> int:
        """
        Execute an INSERT, UPDATE, or DELETE query.
        
        Args:
            query: SQL query string
            params: Query parameters tuple
            
        Returns:
            int: Number of affected rows
        """
        with self.get_sync_connection() as conn:
            cursor = conn.execute(query, params or ())
            conn.commit()
            return cursor.rowcount
    
    def execute_many(self, query: str, params_list: List[tuple]) -> int:
        """
        Execute a query multiple times with different parameters.
        
        Args:
            query: SQL query string
            params_list: List of parameter tuples
            
        Returns:
            int: Total number of affected rows
        """
        with self.get_sync_connection() as conn:
            cursor = conn.executemany(query, params_list)
            conn.commit()
            return cursor.rowcount
    
    async def execute_async_query(self, query: str, params: tuple = None) -> List[Dict[str, Any]]:
        """
        Execute an async SELECT query and return results.
        
        Args:
            query: SQL query string
            params: Query parameters tuple
            
        Returns:
            List[Dict[str, Any]]: Query results
        """
        async with self.get_async_connection() as conn:
            async with conn.execute(query, params or ()) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]
    
    async def execute_async_update(self, query: str, params: tuple = None) -> int:
        """
        Execute an async INSERT, UPDATE, or DELETE query.
        
        Args:
            query: SQL query string
            params: Query parameters tuple
            
        Returns:
            int: Number of affected rows
        """
        async with self.get_async_connection() as conn:
            cursor = await conn.execute(query, params or ())
            await conn.commit()
            return cursor.rowcount
    
    def serialize_embedding(self, embedding: np.ndarray) -> bytes:
        """
        Serialize numpy array embedding to bytes for database storage.
        
        Args:
            embedding: Numpy array embedding
            
        Returns:
            bytes: Serialized embedding
        """
        if embedding is None:
            return None
        return embedding.astype(np.float32).tobytes()
    
    def deserialize_embedding(self, embedding_bytes: bytes) -> np.ndarray:
        """
        Deserialize bytes to numpy array embedding.
        
        Args:
            embedding_bytes: Serialized embedding bytes
            
        Returns:
            np.ndarray: Deserialized embedding
        """
        if embedding_bytes is None:
            return None
        return np.frombuffer(embedding_bytes, dtype=np.float32)
    
    def serialize_json(self, data: Any) -> str:
        """
        Serialize data to JSON string for database storage.
        
        Args:
            data: Data to serialize
            
        Returns:
            str: JSON string
        """
        if data is None:
            return None
        return json.dumps(data, ensure_ascii=False)
    
    def deserialize_json(self, json_str: str) -> Any:
        """
        Deserialize JSON string to Python object.
        
        Args:
            json_str: JSON string
            
        Returns:
            Any: Deserialized data
        """
        if json_str is None:
            return None
        return json.loads(json_str)
    
    def check_connection(self) -> bool:
        """
        Check if database connection is working.
        
        Returns:
            bool: True if connection is successful
        """
        try:
            with self.get_sync_connection() as conn:
                conn.execute("SELECT 1")
                return True
        except Exception as e:
            logger.error(f"Database connection check failed: {e}")
            return False
    
    def get_database_info(self) -> Dict[str, Any]:
        """
        Get database information and statistics.
        
        Returns:
            Dict[str, Any]: Database information
        """
        try:
            with self.get_sync_connection() as conn:
                # Get SQLite version
                sqlite_version = conn.execute("SELECT sqlite_version()").fetchone()[0]
                
                # Check if sqlite-vss is available
                vss_available = False
                try:
                    conn.execute("SELECT vss_version()")
                    vss_available = True
                except sqlite3.OperationalError:
                    pass
                
                # Get table information
                tables = conn.execute("""
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name NOT LIKE 'sqlite_%'
                """).fetchall()
                
                return {
                    "database_path": self.db_path,
                    "sqlite_version": sqlite_version,
                    "vss_available": vss_available,
                    "tables": [table[0] for table in tables],
                    "connection_working": True
                }
                
        except Exception as e:
            logger.error(f"Failed to get database info: {e}")
            return {
                "database_path": self.db_path,
                "connection_working": False,
                "error": str(e)
            }


# Global database manager instance
_db_manager: Optional[DatabaseManager] = None


def get_database_manager() -> DatabaseManager:
    """
    Get global database manager instance (singleton pattern).
    
    Returns:
        DatabaseManager: Database manager instance
    """
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager()
        logger.info("Database manager initialized")
    return _db_manager


def reset_database_manager():
    """Reset global database manager (useful for testing)"""
    global _db_manager
    _db_manager = None