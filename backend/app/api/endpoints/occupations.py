from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from pydantic import BaseModel

from app.models import Occupation
from app.core.config import get_settings

router = APIRouter()
settings = get_settings()


class OccupationResponse(BaseModel):
    """Response model for occupation data"""
    success: bool
    data: Optional[dict] = None
    message: str


@router.get("/{occupation_code}", response_model=OccupationResponse)
async def get_occupation(occupation_code: str):
    """
    Get detailed information about a specific occupation code.
    
    Returns complete occupation details including hierarchical structure,
    description, keywords, and synonyms.
    """
    try:
        if not occupation_code.strip():
            raise HTTPException(status_code=400, detail="Occupation code cannot be empty")
        
        # Validate occupation code format (should be 8 digits for NCO-2015)
        if not occupation_code.isdigit() or len(occupation_code) != 8:
            raise HTTPException(
                status_code=400, 
                detail="Invalid occupation code format. Expected 8-digit NCO code."
            )
        
        # TODO: Implement actual occupation retrieval in future tasks
        return OccupationResponse(
            success=True,
            message="Occupation retrieval endpoint ready - implementation pending",
            data={
                "occupation_code": occupation_code,
                "note": "Occupation data retrieval will be implemented in subsequent tasks."
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get occupation: {str(e)}")


@router.get("/", response_model=OccupationResponse)
async def list_occupations(
    division: Optional[str] = Query(None, description="Filter by division (1-digit)"),
    major_group: Optional[str] = Query(None, description="Filter by major group (2-digit)"),
    limit: int = Query(50, description="Maximum number of occupations to return"),
    offset: int = Query(0, description="Number of occupations to skip")
):
    """
    List occupations with optional filtering by hierarchy level.
    
    Supports pagination and filtering by division or major group.
    """
    try:
        if limit < 1 or limit > 100:
            raise HTTPException(status_code=400, detail="Limit must be between 1 and 100")
        
        if offset < 0:
            raise HTTPException(status_code=400, detail="Offset must be non-negative")
        
        # Validate division format if provided
        if division and (not division.isdigit() or len(division) != 1):
            raise HTTPException(status_code=400, detail="Division must be a single digit")
        
        # Validate major group format if provided
        if major_group and (not major_group.isdigit() or len(major_group) != 2):
            raise HTTPException(status_code=400, detail="Major group must be 2 digits")
        
        # TODO: Implement actual occupation listing in future tasks
        return OccupationResponse(
            success=True,
            message="Occupation listing endpoint ready - implementation pending",
            data={
                "filters": {
                    "division": division,
                    "major_group": major_group
                },
                "pagination": {
                    "limit": limit,
                    "offset": offset
                },
                "occupations": [],
                "note": "Occupation listing will be implemented in subsequent tasks."
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list occupations: {str(e)}")


@router.get("/hierarchy/{level}")
async def get_hierarchy_level(
    level: str,
    code: Optional[str] = Query(None, description="Parent code to filter by")
):
    """
    Get occupation hierarchy at a specific level.
    
    Returns divisions, major groups, sub-major groups, minor groups, or unit groups
    based on the specified level.
    """
    try:
        valid_levels = ["division", "major_group", "sub_major_group", "minor_group", "unit_group"]
        if level not in valid_levels:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid hierarchy level. Must be one of: {valid_levels}"
            )
        
        # TODO: Implement hierarchy retrieval in future tasks
        return OccupationResponse(
            success=True,
            message="Hierarchy endpoint ready - implementation pending",
            data={
                "level": level,
                "parent_code": code,
                "hierarchy_items": [],
                "note": "Hierarchy retrieval will be implemented in subsequent tasks."
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get hierarchy: {str(e)}")