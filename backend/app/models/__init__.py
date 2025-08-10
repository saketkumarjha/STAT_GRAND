# Data models for NCO semantic search

from .occupation import Occupation
from .search import SearchResult, SearchResults, UserQuery

__all__ = [
    'Occupation',
    'SearchResult', 
    'SearchResults',
    'UserQuery'
]