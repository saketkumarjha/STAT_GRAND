from dataclasses import dataclass
from datetime import datetime
from typing import List, Dict, Optional
import numpy as np


@dataclass
class Occupation:
    """
    Core data model for NCO occupation codes and descriptions.
    Represents the hierarchical structure of National Classification of Occupation (NCO-2015).
    """
    code: str  # 8-digit NCO code
    title: str
    description: str
    division: str  # 1-digit
    major_group: str  # 2-digit
    sub_major_group: str  # 3-digit
    minor_group: str  # 4-digit
    unit_group: str  # 5-digit
    keywords: List[str]
    synonyms: Dict[str, List[str]]  # language -> synonyms
    embedding: Optional[np.ndarray] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def __post_init__(self):
        """Initialize timestamps if not provided"""
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = datetime.now()

    def get_hierarchy_level(self, level: str) -> str:
        """Get specific hierarchy level from the occupation code"""
        hierarchy_map = {
            'division': self.division,
            'major_group': self.major_group,
            'sub_major_group': self.sub_major_group,
            'minor_group': self.minor_group,
            'unit_group': self.unit_group
        }
        return hierarchy_map.get(level, '')

    def to_dict(self) -> dict:
        """Convert occupation to dictionary for JSON serialization"""
        return {
            'code': self.code,
            'title': self.title,
            'description': self.description,
            'division': self.division,
            'major_group': self.major_group,
            'sub_major_group': self.sub_major_group,
            'minor_group': self.minor_group,
            'unit_group': self.unit_group,
            'keywords': self.keywords,
            'synonyms': self.synonyms,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }