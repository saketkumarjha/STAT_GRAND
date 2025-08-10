"""
Unit tests for data models.
Tests the Occupation, SearchResult, SearchResults, and UserQuery models.
"""

import pytest
import numpy as np
from datetime import datetime
from typing import Dict, List

from app.models.occupation import Occupation
from app.models.search import SearchResult, SearchResults, UserQuery


class TestOccupation:
    """Test cases for Occupation model"""
    
    def test_occupation_creation(self):
        """Test basic occupation creation"""
        occupation = Occupation(
            code="12345678",
            title="Software Developer",
            description="Develops software applications",
            division="1",
            major_group="12",
            sub_major_group="123",
            minor_group="1234",
            unit_group="12345",
            keywords=["software", "programming", "development"],
            synonyms={"en": ["programmer", "coder"], "hi": ["प्रोग्रामर"]}
        )
        
        assert occupation.code == "12345678"
        assert occupation.title == "Software Developer"
        assert occupation.description == "Develops software applications"
        assert occupation.division == "1"
        assert occupation.major_group == "12"
        assert occupation.sub_major_group == "123"
        assert occupation.minor_group == "1234"
        assert occupation.unit_group == "12345"
        assert occupation.keywords == ["software", "programming", "development"]
        assert occupation.synonyms == {"en": ["programmer", "coder"], "hi": ["प्रोग्रामर"]}
        assert occupation.created_at is not None
        assert occupation.updated_at is not None
    
    def test_occupation_with_embedding(self):
        """Test occupation with numpy embedding"""
        embedding = np.random.rand(768).astype(np.float32)
        
        occupation = Occupation(
            code="87654321",
            title="Data Scientist",
            description="Analyzes data using statistical methods",
            division="2",
            major_group="21",
            sub_major_group="213",
            minor_group="2132",
            unit_group="21321",
            keywords=["data", "analysis", "statistics"],
            synonyms={"en": ["analyst", "researcher"]},
            embedding=embedding
        )
        
        assert occupation.embedding is not None
        assert isinstance(occupation.embedding, np.ndarray)
        assert occupation.embedding.shape == (768,)
        assert occupation.embedding.dtype == np.float32
        np.testing.assert_array_equal(occupation.embedding, embedding)
    
    def test_get_hierarchy_level(self):
        """Test hierarchy level extraction"""
        occupation = Occupation(
            code="12345678",
            title="Test Occupation",
            description="Test description",
            division="1",
            major_group="12",
            sub_major_group="123",
            minor_group="1234",
            unit_group="12345",
            keywords=[],
            synonyms={}
        )
        
        assert occupation.get_hierarchy_level("division") == "1"
        assert occupation.get_hierarchy_level("major_group") == "12"
        assert occupation.get_hierarchy_level("sub_major_group") == "123"
        assert occupation.get_hierarchy_level("minor_group") == "1234"
        assert occupation.get_hierarchy_level("unit_group") == "12345"
        assert occupation.get_hierarchy_level("invalid") == ""
    
    def test_to_dict(self):
        """Test occupation serialization to dictionary"""
        occupation = Occupation(
            code="12345678",
            title="Software Developer",
            description="Develops software applications",
            division="1",
            major_group="12",
            sub_major_group="123",
            minor_group="1234",
            unit_group="12345",
            keywords=["software", "programming"],
            synonyms={"en": ["programmer"]}
        )
        
        result = occupation.to_dict()
        
        assert isinstance(result, dict)
        assert result["code"] == "12345678"
        assert result["title"] == "Software Developer"
        assert result["keywords"] == ["software", "programming"]
        assert result["synonyms"] == {"en": ["programmer"]}
        assert "created_at" in result
        assert "updated_at" in result
    
    def test_occupation_validation(self):
        """Test occupation field validation"""
        # Test with minimal required fields
        occupation = Occupation(
            code="12345678",
            title="Test",
            description="Test description",
            division="1",
            major_group="12",
            sub_major_group="123",
            minor_group="1234",
            unit_group="12345",
            keywords=[],
            synonyms={}
        )
        
        assert occupation.code == "12345678"
        assert occupation.keywords == []
        assert occupation.synonyms == {}


class TestSearchResult:
    """Test cases for SearchResult model"""
    
    def test_search_result_creation(self):
        """Test basic search result creation"""
        occupation = Occupation(
            code="12345678",
            title="Software Developer",
            description="Develops software applications",
            division="1",
            major_group="12",
            sub_major_group="123",
            minor_group="1234",
            unit_group="12345",
            keywords=["software"],
            synonyms={}
        )
        
        search_result = SearchResult(
            occupation=occupation,
            confidence_score=0.95,
            similarity_score=0.87,
            match_type="semantic",
            highlighted_terms=["software", "developer"],
            explanation="High semantic similarity match"
        )
        
        assert search_result.occupation == occupation
        assert search_result.confidence_score == 0.95
        assert search_result.similarity_score == 0.87
        assert search_result.match_type == "semantic"
        assert search_result.highlighted_terms == ["software", "developer"]
        assert search_result.explanation == "High semantic similarity match"
    
    def test_search_result_to_dict(self):
        """Test search result serialization"""
        occupation = Occupation(
            code="12345678",
            title="Software Developer",
            description="Test",
            division="1",
            major_group="12",
            sub_major_group="123",
            minor_group="1234",
            unit_group="12345",
            keywords=[],
            synonyms={}
        )
        
        search_result = SearchResult(
            occupation=occupation,
            confidence_score=0.95,
            similarity_score=0.87,
            match_type="semantic",
            highlighted_terms=["software"],
            explanation="Test explanation"
        )
        
        result_dict = search_result.to_dict()
        
        assert isinstance(result_dict, dict)
        assert "occupation" in result_dict
        assert result_dict["confidence_score"] == 0.95
        assert result_dict["similarity_score"] == 0.87
        assert result_dict["match_type"] == "semantic"
        assert result_dict["highlighted_terms"] == ["software"]


class TestSearchResults:
    """Test cases for SearchResults model"""
    
    def test_search_results_creation(self):
        """Test search results container creation"""
        occupation = Occupation(
            code="12345678",
            title="Software Developer",
            description="Test",
            division="1",
            major_group="12",
            sub_major_group="123",
            minor_group="1234",
            unit_group="12345",
            keywords=[],
            synonyms={}
        )
        
        search_result = SearchResult(
            occupation=occupation,
            confidence_score=0.95,
            similarity_score=0.87,
            match_type="semantic",
            highlighted_terms=["software"],
            explanation="Test"
        )
        
        search_results = SearchResults(
            results=[search_result],
            query="software developer",
            language="en",
            total_results=1,
            processing_time=0.25,
            timestamp=datetime.now()
        )
        
        assert len(search_results.results) == 1
        assert search_results.query == "software developer"
        assert search_results.language == "en"
        assert search_results.total_results == 1
        assert search_results.processing_time == 0.25
        assert search_results.timestamp is not None
    
    def test_search_results_to_dict(self):
        """Test search results serialization"""
        occupation = Occupation(
            code="12345678",
            title="Software Developer",
            description="Test",
            division="1",
            major_group="12",
            sub_major_group="123",
            minor_group="1234",
            unit_group="12345",
            keywords=[],
            synonyms={}
        )
        
        search_result = SearchResult(
            occupation=occupation,
            confidence_score=0.95,
            similarity_score=0.87,
            match_type="semantic",
            highlighted_terms=["software"],
            explanation="Test"
        )
        
        search_results = SearchResults(
            results=[search_result],
            query="software developer",
            language="en",
            total_results=1,
            processing_time=0.25,
            timestamp=datetime.now()
        )
        
        result_dict = search_results.to_dict()
        
        assert isinstance(result_dict, dict)
        assert "results" in result_dict
        assert len(result_dict["results"]) == 1
        assert result_dict["query"] == "software developer"
        assert result_dict["language"] == "en"
        assert result_dict["total_results"] == 1
        assert result_dict["processing_time"] == 0.25


class TestUserQuery:
    """Test cases for UserQuery model"""
    
    def test_user_query_creation(self):
        """Test user query creation"""
        occupation = Occupation(
            code="12345678",
            title="Software Developer",
            description="Test",
            division="1",
            major_group="12",
            sub_major_group="123",
            minor_group="1234",
            unit_group="12345",
            keywords=[],
            synonyms={}
        )
        
        search_result = SearchResult(
            occupation=occupation,
            confidence_score=0.95,
            similarity_score=0.87,
            match_type="semantic",
            highlighted_terms=["software"],
            explanation="Test"
        )
        
        user_query = UserQuery(
            query_id="test-query-123",
            original_text="software developer",
            processed_text="software developer",
            language="en",
            user_id="user-123",
            session_id="session-456",
            timestamp=datetime.now(),
            results=[search_result],
            selected_result="12345678",
            feedback_rating=5
        )
        
        assert user_query.query_id == "test-query-123"
        assert user_query.original_text == "software developer"
        assert user_query.processed_text == "software developer"
        assert user_query.language == "en"
        assert user_query.user_id == "user-123"
        assert user_query.session_id == "session-456"
        assert len(user_query.results) == 1
        assert user_query.selected_result == "12345678"
        assert user_query.feedback_rating == 5
    
    def test_user_query_to_dict(self):
        """Test user query serialization"""
        occupation = Occupation(
            code="12345678",
            title="Software Developer",
            description="Test",
            division="1",
            major_group="12",
            sub_major_group="123",
            minor_group="1234",
            unit_group="12345",
            keywords=[],
            synonyms={}
        )
        
        search_result = SearchResult(
            occupation=occupation,
            confidence_score=0.95,
            similarity_score=0.87,
            match_type="semantic",
            highlighted_terms=["software"],
            explanation="Test"
        )
        
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
        
        result_dict = user_query.to_dict()
        
        assert isinstance(result_dict, dict)
        assert result_dict["query_id"] == "test-query-123"
        assert result_dict["original_text"] == "software developer"
        assert result_dict["language"] == "en"
        assert result_dict["user_id"] == "user-123"
        assert result_dict["session_id"] == "session-456"
        assert "results" in result_dict
        assert len(result_dict["results"]) == 1