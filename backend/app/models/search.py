from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional
from .occupation import Occupation


@dataclass
class SearchResult:
    """
    Represents a single search result with confidence scoring and match information.
    """
    occupation: Occupation
    confidence_score: float
    similarity_score: float
    match_type: str  # "exact", "semantic", "synonym"
    highlighted_terms: List[str]
    explanation: str

    def to_dict(self) -> dict:
        """Convert search result to dictionary for JSON serialization"""
        return {
            'occupation': self.occupation.to_dict(),
            'confidence_score': self.confidence_score,
            'similarity_score': self.similarity_score,
            'match_type': self.match_type,
            'highlighted_terms': self.highlighted_terms,
            'explanation': self.explanation
        }


@dataclass
class SearchResults:
    """
    Container for multiple search results with metadata.
    """
    results: List[SearchResult]
    query: str
    language: str
    total_results: int
    processing_time: float
    timestamp: datetime

    def __post_init__(self):
        """Initialize timestamp if not provided"""
        if not hasattr(self, 'timestamp') or self.timestamp is None:
            self.timestamp = datetime.now()

    def to_dict(self) -> dict:
        """Convert search results to dictionary for JSON serialization"""
        return {
            'results': [result.to_dict() for result in self.results],
            'query': self.query,
            'language': self.language,
            'total_results': self.total_results,
            'processing_time': self.processing_time,
            'timestamp': self.timestamp.isoformat()
        }


@dataclass
class UserQuery:
    """
    Represents a user search query with processing metadata and feedback.
    """
    query_id: str
    original_text: str
    processed_text: str
    language: str
    user_id: Optional[str]
    session_id: str
    timestamp: datetime
    results: List[SearchResult]
    selected_result: Optional[str] = None
    feedback_rating: Optional[int] = None

    def __post_init__(self):
        """Initialize timestamp if not provided"""
        if not hasattr(self, 'timestamp') or self.timestamp is None:
            self.timestamp = datetime.now()

    def to_dict(self) -> dict:
        """Convert user query to dictionary for JSON serialization"""
        return {
            'query_id': self.query_id,
            'original_text': self.original_text,
            'processed_text': self.processed_text,
            'language': self.language,
            'user_id': self.user_id,
            'session_id': self.session_id,
            'timestamp': self.timestamp.isoformat(),
            'results': [result.to_dict() for result in self.results],
            'selected_result': self.selected_result,
            'feedback_rating': self.feedback_rating
        }