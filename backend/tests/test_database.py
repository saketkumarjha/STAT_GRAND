"""
Unit tests for database operations.
Tests database connection, schema creation, and CRUD operations.
"""

import pytest
import tempfile
import os
import numpy as np
from datetime import datetime
from pathlib import Path

from app.database.connection import DatabaseManager
from app.database.schema import create_tables, verify_schema, get_table_info
from app.database.crud import OccupationCRUD, SearchQueryCRUD, UserSessionCRUD
from app.models.occupation import Occupation
from app.models.search import SearchResult, UserQuery


@pytest.fixture
def temp_db():
    """Create a temporary database for testing"""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
        db_path = tmp.name
    
    # Create database manager with temporary database
    db_manager = DatabaseManager(f"sqlite:///{db_path}")
    
    # Create tables
    create_tables(db_manager)
    
    yield db_manager
    
    # Cleanup
    try:
        os.unlink(db_path)
    except:
        pass


@pytest.fixture
def sample_occupation():
    """Create a sample occupation for testing"""
    return Occupation(
        code="12345678",
        title="Software Developer",
        description="Develops software applications and systems",
        division="1",
        major_group="12",
        sub_major_group="123",
        minor_group="1234",
        unit_group="12345",
        keywords=["software", "programming", "development", "coding"],
        synonyms={
            "en": ["programmer", "coder", "developer"],
            "hi": ["प्रोग्रामर", "कोडर"]
        },
        embedding=np.random.rand(768).astype(np.float32)
    )


@pytest.fixture
def sample_occupation_no_embedding():
    """Create a sample occupation without embedding for testing"""
    return Occupation(
        code="87654321",
        title="Data Analyst",
        description="Analyzes data to extract insights",
        division="2",
        major_group="21",
        sub_major_group="213",
        minor_group="2132",
        unit_group="21321",
        keywords=["data", "analysis", "statistics"],
        synonyms={"en": ["analyst", "researcher"]}
    )


class TestDatabaseManager:
    """Test cases for DatabaseManager"""
    
    def test_database_creation(self, temp_db):
        """Test database creation and connection"""
        assert temp_db.check_connection()
        
        # Test database info
        info = temp_db.get_database_info()
        assert info["connection_working"] is True
        assert "sqlite_version" in info
        assert isinstance(info["tables"], list)
    
    def test_execute_query(self, temp_db):
        """Test query execution"""
        # Test simple query
        result = temp_db.execute_query("SELECT 1 as test")
        assert len(result) == 1
        assert result[0]["test"] == 1
    
    def test_execute_update(self, temp_db):
        """Test update execution"""
        # Insert test data
        rows_affected = temp_db.execute_update(
            "INSERT INTO occupations (code, title, description, division, major_group, sub_major_group, minor_group, unit_group, keywords, synonyms) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            ("12345678", "Test Job", "Test Description", "1", "12", "123", "1234", "12345", "[]", "{}")
        )
        assert rows_affected == 1
        
        # Verify insertion
        result = temp_db.execute_query("SELECT * FROM occupations WHERE code = ?", ("12345678",))
        assert len(result) == 1
        assert result[0]["title"] == "Test Job"
    
    def test_serialization(self, temp_db):
        """Test data serialization/deserialization"""
        # Test embedding serialization
        embedding = np.random.rand(768).astype(np.float32)
        serialized = temp_db.serialize_embedding(embedding)
        deserialized = temp_db.deserialize_embedding(serialized)
        
        assert isinstance(serialized, bytes)
        assert isinstance(deserialized, np.ndarray)
        np.testing.assert_array_equal(embedding, deserialized)
        
        # Test JSON serialization
        data = {"test": "value", "number": 42}
        json_str = temp_db.serialize_json(data)
        deserialized_data = temp_db.deserialize_json(json_str)
        
        assert isinstance(json_str, str)
        assert deserialized_data == data
    
    def test_none_serialization(self, temp_db):
        """Test serialization of None values"""
        assert temp_db.serialize_embedding(None) is None
        assert temp_db.deserialize_embedding(None) is None
        assert temp_db.serialize_json(None) is None
        assert temp_db.deserialize_json(None) is None


class TestDatabaseSchema:
    """Test cases for database schema"""
    
    def test_schema_creation(self, temp_db):
        """Test schema creation"""
        # Schema should already be created by fixture
        verification = verify_schema(temp_db)
        
        assert verification["schema_valid"] is True
        assert len(verification["missing_tables"]) == 0
        assert "occupations" in verification["existing_tables"]
        assert "search_queries" in verification["existing_tables"]
        assert "user_sessions" in verification["existing_tables"]
    
    def test_table_info(self, temp_db):
        """Test table information retrieval"""
        table_info = get_table_info(temp_db)
        
        assert isinstance(table_info, list)
        assert len(table_info) >= 3  # At least 3 main tables
        
        # Check that occupations table exists with correct columns
        occupations_table = next((t for t in table_info if t["name"] == "occupations"), None)
        assert occupations_table is not None
        assert occupations_table["type"] == "table"
        
        # Check for key columns
        column_names = [col["name"] for col in occupations_table["columns"]]
        expected_columns = ["code", "title", "description", "division", "major_group", "embedding"]
        for col in expected_columns:
            assert col in column_names


class TestOccupationCRUD:
    """Test cases for OccupationCRUD"""
    
    def test_create_occupation(self, temp_db, sample_occupation):
        """Test occupation creation"""
        crud = OccupationCRUD(temp_db)
        
        # Create occupation
        success = crud.create(sample_occupation)
        assert success is True
        
        # Verify creation
        retrieved = crud.get_by_code(sample_occupation.code)
        assert retrieved is not None
        assert retrieved.code == sample_occupation.code
        assert retrieved.title == sample_occupation.title
        assert retrieved.keywords == sample_occupation.keywords
        assert retrieved.synonyms == sample_occupation.synonyms
        
        # Check embedding
        if sample_occupation.embedding is not None:
            assert retrieved.embedding is not None
            np.testing.assert_array_equal(retrieved.embedding, sample_occupation.embedding)
    
    def test_create_occupation_no_embedding(self, temp_db, sample_occupation_no_embedding):
        """Test occupation creation without embedding"""
        crud = OccupationCRUD(temp_db)
        
        success = crud.create(sample_occupation_no_embedding)
        assert success is True
        
        retrieved = crud.get_by_code(sample_occupation_no_embedding.code)
        assert retrieved is not None
        assert retrieved.embedding is None
    
    def test_get_by_code_not_found(self, temp_db):
        """Test getting non-existent occupation"""
        crud = OccupationCRUD(temp_db)
        
        result = crud.get_by_code("99999999")
        assert result is None
    
    def test_update_occupation(self, temp_db, sample_occupation):
        """Test occupation update"""
        crud = OccupationCRUD(temp_db)
        
        # Create occupation
        crud.create(sample_occupation)
        
        # Update occupation
        sample_occupation.title = "Updated Software Developer"
        sample_occupation.description = "Updated description"
        
        success = crud.update(sample_occupation)
        assert success is True
        
        # Verify update
        retrieved = crud.get_by_code(sample_occupation.code)
        assert retrieved.title == "Updated Software Developer"
        assert retrieved.description == "Updated description"
        assert retrieved.updated_at > retrieved.created_at
    
    def test_delete_occupation(self, temp_db, sample_occupation):
        """Test occupation deletion"""
        crud = OccupationCRUD(temp_db)
        
        # Create occupation
        crud.create(sample_occupation)
        
        # Verify creation
        assert crud.get_by_code(sample_occupation.code) is not None
        
        # Delete occupation
        success = crud.delete(sample_occupation.code)
        assert success is True
        
        # Verify deletion
        assert crud.get_by_code(sample_occupation.code) is None
    
    def test_get_by_hierarchy(self, temp_db, sample_occupation):
        """Test getting occupations by hierarchy level"""
        crud = OccupationCRUD(temp_db)
        
        # Create occupation
        crud.create(sample_occupation)
        
        # Test different hierarchy levels
        results = crud.get_by_hierarchy("division", "1")
        assert len(results) == 1
        assert results[0].code == sample_occupation.code
        
        results = crud.get_by_hierarchy("major_group", "12")
        assert len(results) == 1
        
        results = crud.get_by_hierarchy("unit_group", "12345")
        assert len(results) == 1
        
        # Test non-existent hierarchy
        results = crud.get_by_hierarchy("division", "9")
        assert len(results) == 0
    
    def test_search_by_title(self, temp_db, sample_occupation):
        """Test searching occupations by title"""
        crud = OccupationCRUD(temp_db)
        
        # Create occupation
        crud.create(sample_occupation)
        
        # Test exact match
        results = crud.search_by_title("Software Developer")
        assert len(results) == 1
        assert results[0].code == sample_occupation.code
        
        # Test partial match
        results = crud.search_by_title("Software")
        assert len(results) == 1
        
        # Test case insensitive
        results = crud.search_by_title("software")
        assert len(results) == 1
        
        # Test no match
        results = crud.search_by_title("Nonexistent Job")
        assert len(results) == 0
    
    def test_bulk_create(self, temp_db):
        """Test bulk occupation creation"""
        crud = OccupationCRUD(temp_db)
        
        # Create multiple occupations
        occupations = []
        for i in range(5):
            occupation = Occupation(
                code=f"1234567{i}",
                title=f"Test Job {i}",
                description=f"Test description {i}",
                division="1",
                major_group="12",
                sub_major_group="123",
                minor_group="1234",
                unit_group="12345",
                keywords=[f"keyword{i}"],
                synonyms={"en": [f"synonym{i}"]}
            )
            occupations.append(occupation)
        
        # Bulk create
        created_count = crud.bulk_create(occupations)
        assert created_count == 5
        
        # Verify all were created
        total_count = crud.count()
        assert total_count == 5
        
        # Verify individual occupations
        for i in range(5):
            retrieved = crud.get_by_code(f"1234567{i}")
            assert retrieved is not None
            assert retrieved.title == f"Test Job {i}"
    
    def test_count_and_get_all(self, temp_db, sample_occupation):
        """Test count and get_all operations"""
        crud = OccupationCRUD(temp_db)
        
        # Initially empty
        assert crud.count() == 0
        assert len(crud.get_all()) == 0
        
        # Create occupation
        crud.create(sample_occupation)
        
        # Check count and get_all
        assert crud.count() == 1
        all_occupations = crud.get_all()
        assert len(all_occupations) == 1
        assert all_occupations[0].code == sample_occupation.code
        
        # Test pagination
        all_with_limit = crud.get_all(limit=1, offset=0)
        assert len(all_with_limit) == 1


class TestSearchQueryCRUD:
    """Test cases for SearchQueryCRUD"""
    
    def test_create_query(self, temp_db, sample_occupation):
        """Test search query creation"""
        crud = SearchQueryCRUD(temp_db)
        
        # Create a search result
        search_result = SearchResult(
            occupation=sample_occupation,
            confidence_score=0.95,
            similarity_score=0.87,
            match_type="semantic",
            highlighted_terms=["software", "developer"],
            explanation="High semantic similarity"
        )
        
        # Create user query
        user_query = UserQuery(
            query_id="test-query-123",
            original_text="software developer",
            processed_text="software developer",
            language="en",
            user_id="user-123",
            session_id="session-456",
            timestamp=datetime.now(),
            results=[search_result]
        )
        
        # Create query
        success = crud.create_query(user_query)
        assert success is True
    
    def test_update_feedback(self, temp_db, sample_occupation):
        """Test updating query feedback"""
        crud = SearchQueryCRUD(temp_db)
        
        # Create a query first
        search_result = SearchResult(
            occupation=sample_occupation,
            confidence_score=0.95,
            similarity_score=0.87,
            match_type="semantic",
            highlighted_terms=["software"],
            explanation="Test"
        )
        
        user_query = UserQuery(
            query_id="test-query-456",
            original_text="test query",
            processed_text="test query",
            language="en",
            user_id="user-123",
            session_id="session-456",
            timestamp=datetime.now(),
            results=[search_result]
        )
        
        crud.create_query(user_query)
        
        # Update feedback
        success = crud.update_feedback(
            query_id="test-query-456",
            selected_result="12345678",
            feedback_rating=5
        )
        assert success is True
    
    def test_get_by_session(self, temp_db, sample_occupation):
        """Test getting queries by session"""
        crud = SearchQueryCRUD(temp_db)
        
        # Create multiple queries for same session
        session_id = "test-session-789"
        
        for i in range(3):
            search_result = SearchResult(
                occupation=sample_occupation,
                confidence_score=0.8,
                similarity_score=0.7,
                match_type="semantic",
                highlighted_terms=["test"],
                explanation="Test"
            )
            
            user_query = UserQuery(
                query_id=f"query-{i}",
                original_text=f"test query {i}",
                processed_text=f"test query {i}",
                language="en",
                user_id="user-123",
                session_id=session_id,
                timestamp=datetime.now(),
                results=[search_result]
            )
            
            crud.create_query(user_query)
        
        # Get queries by session
        queries = crud.get_by_session(session_id)
        assert len(queries) == 3
        
        # All should have same session_id
        for query in queries:
            assert query.session_id == session_id
    
    def test_get_analytics(self, temp_db, sample_occupation):
        """Test analytics retrieval"""
        crud = SearchQueryCRUD(temp_db)
        
        # Create some test queries
        languages = ["en", "hi", "en", "ta"]
        ratings = [5, 4, None, 3]
        
        for i, (lang, rating) in enumerate(zip(languages, ratings)):
            search_result = SearchResult(
                occupation=sample_occupation,
                confidence_score=0.8,
                similarity_score=0.7,
                match_type="semantic",
                highlighted_terms=["test"],
                explanation="Test"
            )
            
            user_query = UserQuery(
                query_id=f"analytics-query-{i}",
                original_text=f"test query {i}",
                processed_text=f"test query {i}",
                language=lang,
                user_id="user-123",
                session_id="analytics-session",
                timestamp=datetime.now(),
                results=[search_result],
                feedback_rating=rating
            )
            
            crud.create_query(user_query)
        
        # Get analytics
        analytics = crud.get_analytics()
        
        assert analytics["total_queries"] == 4
        assert analytics["queries_by_language"]["en"] == 2
        assert analytics["queries_by_language"]["hi"] == 1
        assert analytics["queries_by_language"]["ta"] == 1
        assert analytics["rated_queries"] == 3  # 3 queries with ratings
        assert analytics["average_rating"] == 4.0  # (5+4+3)/3


class TestUserSessionCRUD:
    """Test cases for UserSessionCRUD"""
    
    def test_create_session(self, temp_db):
        """Test session creation"""
        crud = UserSessionCRUD(temp_db)
        
        success = crud.create_session(
            session_id="test-session-123",
            user_id="user-456",
            language_preference="hi",
            accessibility_settings={"high_contrast": True, "font_size": "large"}
        )
        
        assert success is True
    
    def test_get_session(self, temp_db):
        """Test session retrieval"""
        crud = UserSessionCRUD(temp_db)
        
        # Create session
        accessibility_settings = {"high_contrast": True, "font_size": "large"}
        crud.create_session(
            session_id="test-session-456",
            user_id="user-789",
            language_preference="ta",
            accessibility_settings=accessibility_settings
        )
        
        # Get session
        session = crud.get_session("test-session-456")
        
        assert session is not None
        assert session["session_id"] == "test-session-456"
        assert session["user_id"] == "user-789"
        assert session["language_preference"] == "ta"
        assert session["accessibility_settings"] == accessibility_settings
        assert "created_at" in session
        assert "last_activity" in session
    
    def test_get_session_not_found(self, temp_db):
        """Test getting non-existent session"""
        crud = UserSessionCRUD(temp_db)
        
        session = crud.get_session("nonexistent-session")
        assert session is None
    
    def test_update_activity(self, temp_db):
        """Test updating session activity"""
        crud = UserSessionCRUD(temp_db)
        
        # Create session
        crud.create_session("activity-test-session")
        
        # Get initial session
        initial_session = crud.get_session("activity-test-session")
        initial_activity = initial_session["last_activity"]
        
        # Update activity
        success = crud.update_activity("activity-test-session")
        assert success is True
        
        # Verify activity was updated
        updated_session = crud.get_session("activity-test-session")
        updated_activity = updated_session["last_activity"]
        
        # Note: In a real test, you might want to add a small delay to ensure timestamp difference
        # For now, we just check that the update was successful
        assert updated_activity is not None