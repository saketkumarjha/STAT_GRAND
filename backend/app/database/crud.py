"""
CRUD operations for NCO Semantic Search database.
Provides Create, Read, Update, Delete operations for all data models.
"""

import logging
import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any
import numpy as np

from app.models.occupation import Occupation
from app.models.search import SearchResult, SearchResults, UserQuery
from .connection import DatabaseManager, get_database_manager

logger = logging.getLogger(__name__)


class OccupationCRUD:
    """
    CRUD operations for Occupation model.
    Handles database operations for NCO occupation codes and descriptions.
    """
    
    def __init__(self, db_manager: DatabaseManager = None):
        """Initialize with database manager"""
        self.db_manager = db_manager or get_database_manager()
    
    def create(self, occupation: Occupation) -> bool:
        """
        Create a new occupation record in the database.
        
        Args:
            occupation: Occupation instance to create
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Serialize complex fields
            keywords_json = self.db_manager.serialize_json(occupation.keywords)
            synonyms_json = self.db_manager.serialize_json(occupation.synonyms)
            embedding_bytes = self.db_manager.serialize_embedding(occupation.embedding)
            
            query = """
                INSERT INTO occupations (
                    code, title, description, division, major_group, 
                    sub_major_group, minor_group, unit_group, keywords, 
                    synonyms, embedding, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            params = (
                occupation.code,
                occupation.title,
                occupation.description,
                occupation.division,
                occupation.major_group,
                occupation.sub_major_group,
                occupation.minor_group,
                occupation.unit_group,
                keywords_json,
                synonyms_json,
                embedding_bytes,
                occupation.created_at,
                occupation.updated_at
            )
            
            rows_affected = self.db_manager.execute_update(query, params)
            
            # Insert into vector table if available
            if embedding_bytes:
                if self._is_vss_available():
                    self._insert_vector(occupation.code, occupation.embedding)
                elif self._is_fallback_vector_available():
                    self._insert_fallback_vector(occupation.code, occupation.embedding)
            
            logger.debug(f"Created occupation: {occupation.code}")
            return rows_affected > 0
            
        except Exception as e:
            logger.error(f"Failed to create occupation {occupation.code}: {e}")
            return False
    
    def get_by_code(self, code: str) -> Optional[Occupation]:
        """
        Retrieve occupation by NCO code.
        
        Args:
            code: NCO occupation code
            
        Returns:
            Optional[Occupation]: Occupation instance or None if not found
        """
        try:
            query = "SELECT * FROM occupations WHERE code = ?"
            results = self.db_manager.execute_query(query, (code,))
            
            if not results:
                return None
            
            return self._row_to_occupation(results[0])
            
        except Exception as e:
            logger.error(f"Failed to get occupation {code}: {e}")
            return None
    
    def get_by_hierarchy(self, level: str, value: str) -> List[Occupation]:
        """
        Get occupations by hierarchy level (division, major_group, etc.).
        
        Args:
            level: Hierarchy level (division, major_group, sub_major_group, minor_group, unit_group)
            value: Value to search for
            
        Returns:
            List[Occupation]: List of matching occupations
        """
        try:
            valid_levels = ['division', 'major_group', 'sub_major_group', 'minor_group', 'unit_group']
            if level not in valid_levels:
                raise ValueError(f"Invalid hierarchy level: {level}")
            
            query = f"SELECT * FROM occupations WHERE {level} = ? ORDER BY code"
            results = self.db_manager.execute_query(query, (value,))
            
            return [self._row_to_occupation(row) for row in results]
            
        except Exception as e:
            logger.error(f"Failed to get occupations by {level}={value}: {e}")
            return []
    
    def search_by_title(self, title_pattern: str, limit: int = 10) -> List[Occupation]:
        """
        Search occupations by title pattern.
        
        Args:
            title_pattern: Title search pattern (supports SQL LIKE syntax)
            limit: Maximum number of results
            
        Returns:
            List[Occupation]: List of matching occupations
        """
        try:
            query = """
                SELECT * FROM occupations 
                WHERE title LIKE ? OR description LIKE ?
                ORDER BY 
                    CASE 
                        WHEN title LIKE ? THEN 1 
                        ELSE 2 
                    END,
                    code
                LIMIT ?
            """
            
            pattern = f"%{title_pattern}%"
            exact_pattern = f"{title_pattern}%"
            
            results = self.db_manager.execute_query(
                query, (pattern, pattern, exact_pattern, limit)
            )
            
            return [self._row_to_occupation(row) for row in results]
            
        except Exception as e:
            logger.error(f"Failed to search occupations by title '{title_pattern}': {e}")
            return []
    
    def update(self, occupation: Occupation) -> bool:
        """
        Update an existing occupation record.
        
        Args:
            occupation: Occupation instance with updated data
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Update timestamp
            occupation.updated_at = datetime.now()
            
            # Serialize complex fields
            keywords_json = self.db_manager.serialize_json(occupation.keywords)
            synonyms_json = self.db_manager.serialize_json(occupation.synonyms)
            embedding_bytes = self.db_manager.serialize_embedding(occupation.embedding)
            
            query = """
                UPDATE occupations SET
                    title = ?, description = ?, division = ?, major_group = ?,
                    sub_major_group = ?, minor_group = ?, unit_group = ?,
                    keywords = ?, synonyms = ?, embedding = ?, updated_at = ?
                WHERE code = ?
            """
            
            params = (
                occupation.title,
                occupation.description,
                occupation.division,
                occupation.major_group,
                occupation.sub_major_group,
                occupation.minor_group,
                occupation.unit_group,
                keywords_json,
                synonyms_json,
                embedding_bytes,
                occupation.updated_at,
                occupation.code
            )
            
            rows_affected = self.db_manager.execute_update(query, params)
            
            # Update vector table if available
            if embedding_bytes:
                if self._is_vss_available():
                    self._update_vector(occupation.code, occupation.embedding)
                elif self._is_fallback_vector_available():
                    self._update_fallback_vector(occupation.code, occupation.embedding)
            
            logger.debug(f"Updated occupation: {occupation.code}")
            return rows_affected > 0
            
        except Exception as e:
            logger.error(f"Failed to update occupation {occupation.code}: {e}")
            return False
    
    def delete(self, code: str) -> bool:
        """
        Delete an occupation record.
        
        Args:
            code: NCO occupation code
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Delete from vector table first if available
            if self._is_vss_available():
                self._delete_vector(code)
            elif self._is_fallback_vector_available():
                self._delete_fallback_vector(code)
            
            query = "DELETE FROM occupations WHERE code = ?"
            rows_affected = self.db_manager.execute_update(query, (code,))
            
            logger.debug(f"Deleted occupation: {code}")
            return rows_affected > 0
            
        except Exception as e:
            logger.error(f"Failed to delete occupation {code}: {e}")
            return False
    
    def get_all(self, limit: int = None, offset: int = 0) -> List[Occupation]:
        """
        Get all occupations with optional pagination.
        
        Args:
            limit: Maximum number of results (None for all)
            offset: Number of records to skip
            
        Returns:
            List[Occupation]: List of occupations
        """
        try:
            query = "SELECT * FROM occupations ORDER BY code"
            
            if limit is not None:
                query += f" LIMIT {limit} OFFSET {offset}"
            
            results = self.db_manager.execute_query(query)
            return [self._row_to_occupation(row) for row in results]
            
        except Exception as e:
            logger.error(f"Failed to get all occupations: {e}")
            return []
    
    def count(self) -> int:
        """
        Get total count of occupations.
        
        Returns:
            int: Total number of occupations
        """
        try:
            query = "SELECT COUNT(*) as count FROM occupations"
            result = self.db_manager.execute_query(query)
            return result[0]['count'] if result else 0
            
        except Exception as e:
            logger.error(f"Failed to count occupations: {e}")
            return 0
    
    def bulk_create(self, occupations: List[Occupation]) -> int:
        """
        Create multiple occupation records in a single transaction.
        
        Args:
            occupations: List of Occupation instances
            
        Returns:
            int: Number of successfully created records
        """
        try:
            query = """
                INSERT INTO occupations (
                    code, title, description, division, major_group, 
                    sub_major_group, minor_group, unit_group, keywords, 
                    synonyms, embedding, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            params_list = []
            vector_data = []
            
            for occupation in occupations:
                keywords_json = self.db_manager.serialize_json(occupation.keywords)
                synonyms_json = self.db_manager.serialize_json(occupation.synonyms)
                embedding_bytes = self.db_manager.serialize_embedding(occupation.embedding)
                
                params_list.append((
                    occupation.code,
                    occupation.title,
                    occupation.description,
                    occupation.division,
                    occupation.major_group,
                    occupation.sub_major_group,
                    occupation.minor_group,
                    occupation.unit_group,
                    keywords_json,
                    synonyms_json,
                    embedding_bytes,
                    occupation.created_at,
                    occupation.updated_at
                ))
                
                if occupation.embedding is not None:
                    vector_data.append((occupation.code, occupation.embedding))
            
            rows_affected = self.db_manager.execute_many(query, params_list)
            
            # Bulk insert vectors if available
            if vector_data:
                if self._is_vss_available():
                    self._bulk_insert_vectors(vector_data)
                elif self._is_fallback_vector_available():
                    self._bulk_insert_fallback_vectors(vector_data)
            
            logger.info(f"Bulk created {rows_affected} occupations")
            return rows_affected
            
        except Exception as e:
            logger.error(f"Failed to bulk create occupations: {e}")
            return 0
    
    def _row_to_occupation(self, row: Dict[str, Any]) -> Occupation:
        """
        Convert database row to Occupation instance.
        
        Args:
            row: Database row as dictionary
            
        Returns:
            Occupation: Occupation instance
        """
        return Occupation(
            code=row['code'],
            title=row['title'],
            description=row['description'],
            division=row['division'],
            major_group=row['major_group'],
            sub_major_group=row['sub_major_group'],
            minor_group=row['minor_group'],
            unit_group=row['unit_group'],
            keywords=self.db_manager.deserialize_json(row['keywords']) or [],
            synonyms=self.db_manager.deserialize_json(row['synonyms']) or {},
            embedding=self.db_manager.deserialize_embedding(row['embedding']),
            created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else None,
            updated_at=datetime.fromisoformat(row['updated_at']) if row['updated_at'] else None
        )
    
    def _is_vss_available(self) -> bool:
        """Check if sqlite-vss extension is available"""
        try:
            result = self.db_manager.execute_query("SELECT name FROM sqlite_master WHERE name='occupation_vectors'")
            return len(result) > 0
        except:
            return False
    
    def _is_fallback_vector_available(self) -> bool:
        """Check if fallback vector table is available"""
        try:
            result = self.db_manager.execute_query("SELECT name FROM sqlite_master WHERE name='occupation_vectors_fallback'")
            return len(result) > 0
        except:
            return False
    
    def _insert_vector(self, code: str, embedding: np.ndarray):
        """Insert vector into sqlite-vss table"""
        try:
            # Convert numpy array to list for sqlite-vss
            vector_list = embedding.tolist()
            query = "INSERT INTO occupation_vectors(rowid, embedding) VALUES (?, ?)"
            # Use hash of code as rowid for consistency
            rowid = hash(code) % (2**31)  # Ensure positive 32-bit integer
            self.db_manager.execute_update(query, (rowid, str(vector_list)))
        except Exception as e:
            logger.warning(f"Failed to insert vector for {code}: {e}")
    
    def _update_vector(self, code: str, embedding: np.ndarray):
        """Update vector in sqlite-vss table"""
        try:
            self._delete_vector(code)
            self._insert_vector(code, embedding)
        except Exception as e:
            logger.warning(f"Failed to update vector for {code}: {e}")
    
    def _delete_vector(self, code: str):
        """Delete vector from sqlite-vss table"""
        try:
            rowid = hash(code) % (2**31)
            query = "DELETE FROM occupation_vectors WHERE rowid = ?"
            self.db_manager.execute_update(query, (rowid,))
        except Exception as e:
            logger.warning(f"Failed to delete vector for {code}: {e}")
    
    def _bulk_insert_vectors(self, vector_data: List[tuple]):
        """Bulk insert vectors into sqlite-vss table"""
        try:
            query = "INSERT INTO occupation_vectors(rowid, embedding) VALUES (?, ?)"
            params_list = []
            
            for code, embedding in vector_data:
                rowid = hash(code) % (2**31)
                vector_list = embedding.tolist()
                params_list.append((rowid, str(vector_list)))
            
            self.db_manager.execute_many(query, params_list)
        except Exception as e:
            logger.warning(f"Failed to bulk insert vectors: {e}")
    
    def _insert_fallback_vector(self, code: str, embedding: np.ndarray):
        """Insert vector into fallback table"""
        try:
            embedding_bytes = self.db_manager.serialize_embedding(embedding)
            query = "INSERT OR REPLACE INTO occupation_vectors_fallback(occupation_code, embedding) VALUES (?, ?)"
            self.db_manager.execute_update(query, (code, embedding_bytes))
        except Exception as e:
            logger.warning(f"Failed to insert fallback vector for {code}: {e}")
    
    def _update_fallback_vector(self, code: str, embedding: np.ndarray):
        """Update vector in fallback table"""
        try:
            embedding_bytes = self.db_manager.serialize_embedding(embedding)
            query = "UPDATE occupation_vectors_fallback SET embedding = ? WHERE occupation_code = ?"
            self.db_manager.execute_update(query, (embedding_bytes, code))
        except Exception as e:
            logger.warning(f"Failed to update fallback vector for {code}: {e}")
    
    def _delete_fallback_vector(self, code: str):
        """Delete vector from fallback table"""
        try:
            query = "DELETE FROM occupation_vectors_fallback WHERE occupation_code = ?"
            self.db_manager.execute_update(query, (code,))
        except Exception as e:
            logger.warning(f"Failed to delete fallback vector for {code}: {e}")
    
    def _bulk_insert_fallback_vectors(self, vector_data: List[tuple]):
        """Bulk insert vectors into fallback table"""
        try:
            query = "INSERT OR REPLACE INTO occupation_vectors_fallback(occupation_code, embedding) VALUES (?, ?)"
            params_list = []
            
            for code, embedding in vector_data:
                embedding_bytes = self.db_manager.serialize_embedding(embedding)
                params_list.append((code, embedding_bytes))
            
            self.db_manager.execute_many(query, params_list)
        except Exception as e:
            logger.warning(f"Failed to bulk insert fallback vectors: {e}")


class SearchQueryCRUD:
    """
    CRUD operations for search queries and analytics.
    """
    
    def __init__(self, db_manager: DatabaseManager = None):
        """Initialize with database manager"""
        self.db_manager = db_manager or get_database_manager()
    
    def create_query(self, user_query: UserQuery) -> bool:
        """
        Create a new search query record.
        
        Args:
            user_query: UserQuery instance to create
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            results_json = self.db_manager.serialize_json([
                result.to_dict() for result in user_query.results
            ])
            
            query = """
                INSERT INTO search_queries (
                    query_id, original_text, processed_text, language,
                    user_id, session_id, timestamp, results,
                    selected_result, feedback_rating
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            params = (
                user_query.query_id,
                user_query.original_text,
                user_query.processed_text,
                user_query.language,
                user_query.user_id,
                user_query.session_id,
                user_query.timestamp,
                results_json,
                user_query.selected_result,
                user_query.feedback_rating
            )
            
            rows_affected = self.db_manager.execute_update(query, params)
            logger.debug(f"Created search query: {user_query.query_id}")
            return rows_affected > 0
            
        except Exception as e:
            logger.error(f"Failed to create search query {user_query.query_id}: {e}")
            return False
    
    def update_feedback(self, query_id: str, selected_result: str = None, 
                       feedback_rating: int = None) -> bool:
        """
        Update search query with user feedback.
        
        Args:
            query_id: Query ID to update
            selected_result: Selected occupation code
            feedback_rating: User rating (1-5)
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            updates = []
            params = []
            
            if selected_result is not None:
                updates.append("selected_result = ?")
                params.append(selected_result)
            
            if feedback_rating is not None:
                updates.append("feedback_rating = ?")
                params.append(feedback_rating)
            
            if not updates:
                return True  # Nothing to update
            
            query = f"UPDATE search_queries SET {', '.join(updates)} WHERE query_id = ?"
            params.append(query_id)
            
            rows_affected = self.db_manager.execute_update(query, tuple(params))
            logger.debug(f"Updated feedback for query: {query_id}")
            return rows_affected > 0
            
        except Exception as e:
            logger.error(f"Failed to update feedback for query {query_id}: {e}")
            return False
    
    def get_by_session(self, session_id: str, limit: int = 50) -> List[UserQuery]:
        """
        Get search queries by session ID.
        
        Args:
            session_id: Session ID
            limit: Maximum number of results
            
        Returns:
            List[UserQuery]: List of user queries
        """
        try:
            query = """
                SELECT * FROM search_queries 
                WHERE session_id = ? 
                ORDER BY timestamp DESC 
                LIMIT ?
            """
            
            results = self.db_manager.execute_query(query, (session_id, limit))
            return [self._row_to_user_query(row) for row in results]
            
        except Exception as e:
            logger.error(f"Failed to get queries for session {session_id}: {e}")
            return []
    
    def get_analytics(self, start_date: datetime = None, end_date: datetime = None) -> Dict[str, Any]:
        """
        Get search analytics for a date range.
        
        Args:
            start_date: Start date for analytics
            end_date: End date for analytics
            
        Returns:
            Dict[str, Any]: Analytics data
        """
        try:
            conditions = []
            params = []
            
            if start_date:
                conditions.append("timestamp >= ?")
                params.append(start_date)
            
            if end_date:
                conditions.append("timestamp <= ?")
                params.append(end_date)
            
            where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
            
            # Total queries
            total_query = f"SELECT COUNT(*) as count FROM search_queries {where_clause}"
            total_result = self.db_manager.execute_query(total_query, tuple(params))
            total_queries = total_result[0]['count'] if total_result else 0
            
            # Queries by language
            lang_query = f"""
                SELECT language, COUNT(*) as count 
                FROM search_queries {where_clause}
                GROUP BY language 
                ORDER BY count DESC
            """
            lang_results = self.db_manager.execute_query(lang_query, tuple(params))
            
            # Average feedback rating
            rating_query = f"""
                SELECT AVG(feedback_rating) as avg_rating, COUNT(feedback_rating) as rated_count
                FROM search_queries 
                {where_clause} AND feedback_rating IS NOT NULL
            """
            rating_result = self.db_manager.execute_query(rating_query, tuple(params))
            
            return {
                'total_queries': total_queries,
                'queries_by_language': {row['language']: row['count'] for row in lang_results},
                'average_rating': rating_result[0]['avg_rating'] if rating_result and rating_result[0]['avg_rating'] else 0,
                'rated_queries': rating_result[0]['rated_count'] if rating_result else 0,
                'date_range': {
                    'start': start_date.isoformat() if start_date else None,
                    'end': end_date.isoformat() if end_date else None
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to get analytics: {e}")
            return {}
    
    def _row_to_user_query(self, row: Dict[str, Any]) -> UserQuery:
        """Convert database row to UserQuery instance"""
        results_data = self.db_manager.deserialize_json(row['results']) or []
        
        # Note: This is a simplified conversion since we don't have full SearchResult reconstruction
        # In a real implementation, you'd need to reconstruct SearchResult objects
        results = []  # Simplified for now
        
        return UserQuery(
            query_id=row['query_id'],
            original_text=row['original_text'],
            processed_text=row['processed_text'],
            language=row['language'],
            user_id=row['user_id'],
            session_id=row['session_id'],
            timestamp=datetime.fromisoformat(row['timestamp']) if row['timestamp'] else datetime.now(),
            results=results,
            selected_result=row['selected_result'],
            feedback_rating=row['feedback_rating']
        )


class UserSessionCRUD:
    """
    CRUD operations for user sessions.
    """
    
    def __init__(self, db_manager: DatabaseManager = None):
        """Initialize with database manager"""
        self.db_manager = db_manager or get_database_manager()
    
    def create_session(self, session_id: str, user_id: str = None, 
                      language_preference: str = "en",
                      accessibility_settings: Dict[str, Any] = None) -> bool:
        """
        Create a new user session.
        
        Args:
            session_id: Unique session identifier
            user_id: Optional user identifier
            language_preference: Preferred language code
            accessibility_settings: Accessibility preferences
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            settings_json = self.db_manager.serialize_json(accessibility_settings or {})
            
            query = """
                INSERT INTO user_sessions (
                    session_id, user_id, language_preference, accessibility_settings
                ) VALUES (?, ?, ?, ?)
            """
            
            params = (session_id, user_id, language_preference, settings_json)
            rows_affected = self.db_manager.execute_update(query, params)
            
            logger.debug(f"Created user session: {session_id}")
            return rows_affected > 0
            
        except Exception as e:
            logger.error(f"Failed to create session {session_id}: {e}")
            return False
    
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get session information.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Optional[Dict[str, Any]]: Session data or None if not found
        """
        try:
            query = "SELECT * FROM user_sessions WHERE session_id = ?"
            results = self.db_manager.execute_query(query, (session_id,))
            
            if not results:
                return None
            
            row = results[0]
            return {
                'session_id': row['session_id'],
                'user_id': row['user_id'],
                'language_preference': row['language_preference'],
                'accessibility_settings': self.db_manager.deserialize_json(row['accessibility_settings']) or {},
                'created_at': row['created_at'],
                'last_activity': row['last_activity']
            }
            
        except Exception as e:
            logger.error(f"Failed to get session {session_id}: {e}")
            return None
    
    def update_activity(self, session_id: str) -> bool:
        """
        Update session last activity timestamp.
        
        Args:
            session_id: Session identifier
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            query = "UPDATE user_sessions SET last_activity = CURRENT_TIMESTAMP WHERE session_id = ?"
            rows_affected = self.db_manager.execute_update(query, (session_id,))
            return rows_affected > 0
            
        except Exception as e:
            logger.error(f"Failed to update activity for session {session_id}: {e}")
            return False


# Convenience functions for getting CRUD instances
def get_occupation_crud(db_manager: DatabaseManager = None) -> OccupationCRUD:
    """Get OccupationCRUD instance"""
    return OccupationCRUD(db_manager)


def get_search_query_crud(db_manager: DatabaseManager = None) -> SearchQueryCRUD:
    """Get SearchQueryCRUD instance"""
    return SearchQueryCRUD(db_manager)


def get_user_session_crud(db_manager: DatabaseManager = None) -> UserSessionCRUD:
    """Get UserSessionCRUD instance"""
    return UserSessionCRUD(db_manager)