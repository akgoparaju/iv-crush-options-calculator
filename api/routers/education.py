"""
Education Router for Phase 5.4
Educational content management endpoints
"""

import logging
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, HTTPException, Depends, status, Query, BackgroundTasks
from fastapi.responses import JSONResponse

from api.models.education import (
    CreateContentRequest, UpdateContentRequest, CreateCommentRequest, 
    UpdateCommentRequest, CreateQuizRequest, ContentDetailResponse,
    ContentSummary, CommentResponse, QuizResponse, QuizAttemptResponse,
    LearningProgressResponse, ContentAnalytics, ContentSearchRequest,
    ContentSearchResponse, LearningPath
)
from api.models.auth import UserInDB
from api.routers.auth import get_current_active_user
from api.services.education_service import education_service

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/education", tags=["Educational Content"])

# =====================================================================================
# Content Management Endpoints
# =====================================================================================

@router.post("/content", response_model=ContentDetailResponse, status_code=status.HTTP_201_CREATED)
async def create_content(
    content_data: CreateContentRequest,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """
    Create new educational content
    
    Creates educational content like articles, tutorials, strategy guides, etc.
    """
    try:
        content = await education_service.create_content(
            author_id=current_user.id,
            content_data=content_data
        )
        
        logger.info(f"📚 Content created: {content.title} by {current_user.username}")
        return content
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Content creation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create content"
        )

@router.get("/content/search", response_model=ContentSearchResponse)
async def search_content(
    query: Optional[str] = Query(None, description="Search query"),
    content_types: Optional[str] = Query(None, description="Comma-separated content types"),
    difficulty_levels: Optional[str] = Query(None, description="Comma-separated difficulty levels"),
    learning_paths: Optional[str] = Query(None, description="Comma-separated learning paths"),
    tags: Optional[str] = Query(None, description="Comma-separated tags"),
    featured_only: bool = Query(False, description="Show only featured content"),
    premium_only: bool = Query(False, description="Show only premium content"),
    min_read_time: Optional[int] = Query(None, ge=1, description="Minimum read time in minutes"),
    max_read_time: Optional[int] = Query(None, le=240, description="Maximum read time in minutes"),
    author: Optional[str] = Query(None, description="Author username"),
    sort_by: str = Query("updated_at", description="Sort field"),
    sort_order: str = Query("desc", description="Sort order: asc or desc"),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page")
):
    """
    Search educational content
    
    Advanced search with filtering, sorting, and pagination
    """
    try:
        from api.models.education import ContentType, DifficultyLevel
        
        # Parse comma-separated values
        search_params = ContentSearchRequest(
            query=query,
            content_types=[ContentType(ct.strip()) for ct in content_types.split(',')] if content_types else None,
            difficulty_levels=[DifficultyLevel(dl.strip()) for dl in difficulty_levels.split(',')] if difficulty_levels else None,
            learning_paths=[LearningPath(lp.strip()) for lp in learning_paths.split(',')] if learning_paths else None,
            tags=tags.split(',') if tags else None,
            featured_only=featured_only,
            premium_only=premium_only,
            min_read_time=min_read_time,
            max_read_time=max_read_time,
            author=author,
            sort_by=sort_by,
            sort_order=sort_order,
            page=page,
            per_page=per_page
        )
        
        results = await education_service.search_content(search_params)
        return results
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid parameter value: {str(e)}"
        )
    except Exception as e:
        logger.error(f"❌ Error searching content: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to search content"
        )

@router.get("/content/{content_id}", response_model=ContentDetailResponse)
async def get_content(
    content_id: UUID,
    current_user: Optional[UserInDB] = Depends(get_current_active_user)
):
    """
    Get content by ID
    
    Returns detailed content information with user interaction data
    """
    try:
        user_id = current_user.id if current_user else None
        content = await education_service.get_content(content_id, user_id)
        return content
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error fetching content: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch content"
        )

@router.put("/content/{content_id}", response_model=ContentDetailResponse)
async def update_content(
    content_id: UUID,
    update_data: UpdateContentRequest,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """
    Update content
    
    Updates content owned by the authenticated user
    """
    try:
        content = await education_service.update_content(
            content_id=content_id,
            author_id=current_user.id,
            updates=update_data
        )
        
        return content
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error updating content: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update content"
        )

@router.delete("/content/{content_id}")
async def delete_content(
    content_id: UUID,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """
    Delete content
    
    Soft deletes content by archiving it
    """
    try:
        success = await education_service.delete_content(content_id, current_user.id)
        
        if success:
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={
                    "success": True,
                    "message": "Content deleted successfully"
                }
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Content not found or access denied"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error deleting content: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete content"
        )

# =====================================================================================
# User Interaction Endpoints
# =====================================================================================

@router.post("/content/{content_id}/like")
async def toggle_content_like(
    content_id: UUID,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """
    Toggle like on content
    
    Adds or removes a like from the content
    """
    try:
        is_liked = await education_service.toggle_like(current_user.id, content_id)
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "success": True,
                "liked": is_liked,
                "message": "Content liked" if is_liked else "Like removed"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error toggling like: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to toggle like"
        )

@router.post("/content/{content_id}/bookmark")
async def toggle_content_bookmark(
    content_id: UUID,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """
    Toggle bookmark on content
    
    Adds or removes a bookmark from the content
    """
    try:
        is_bookmarked = await education_service.toggle_bookmark(current_user.id, content_id)
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "success": True,
                "bookmarked": is_bookmarked,
                "message": "Content bookmarked" if is_bookmarked else "Bookmark removed"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error toggling bookmark: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to toggle bookmark"
        )

# =====================================================================================
# Learning Progress Endpoints
# =====================================================================================

@router.get("/progress/{learning_path}", response_model=LearningProgressResponse)
async def get_learning_progress(
    learning_path: LearningPath,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """
    Get learning progress for a path
    
    Returns detailed progress metrics and achievements
    """
    try:
        progress = await education_service.get_learning_progress(
            user_id=current_user.id,
            learning_path=learning_path
        )
        
        return progress
        
    except Exception as e:
        logger.error(f"❌ Error fetching learning progress: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch learning progress"
        )

@router.get("/learning-paths")
async def get_learning_paths():
    """
    Get available learning paths
    
    Returns structured learning paths with descriptions
    """
    try:
        learning_paths = {
            "options_basics": {
                "name": "Options Trading Basics",
                "description": "Fundamental concepts of options trading",
                "estimated_hours": 20,
                "difficulty": "beginner"
            },
            "trading_strategies": {
                "name": "Trading Strategies",
                "description": "Common options trading strategies",
                "estimated_hours": 30,
                "difficulty": "intermediate"
            },
            "risk_management": {
                "name": "Risk Management",
                "description": "Managing risk in options trading",
                "estimated_hours": 25,
                "difficulty": "intermediate"
            },
            "market_analysis": {
                "name": "Market Analysis",
                "description": "Technical and fundamental analysis",
                "estimated_hours": 35,
                "difficulty": "intermediate"
            },
            "advanced_concepts": {
                "name": "Advanced Concepts",
                "description": "Advanced options strategies and concepts",
                "estimated_hours": 40,
                "difficulty": "advanced"
            },
            "portfolio_management": {
                "name": "Portfolio Management",
                "description": "Managing an options trading portfolio",
                "estimated_hours": 30,
                "difficulty": "advanced"
            }
        }
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "success": True,
                "learning_paths": learning_paths
            }
        )
        
    except Exception as e:
        logger.error(f"❌ Error fetching learning paths: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch learning paths"
        )

# =====================================================================================
# Content Discovery Endpoints
# =====================================================================================

@router.get("/featured", response_model=List[ContentSummary])
async def get_featured_content(
    limit: int = Query(10, ge=1, le=50, description="Number of featured items to return")
):
    """
    Get featured educational content
    
    Returns curated featured content for homepage
    """
    try:
        from api.models.education import ContentSearchRequest
        
        search_params = ContentSearchRequest(
            featured_only=True,
            sort_by="updated_at",
            sort_order="desc",
            page=1,
            per_page=limit
        )
        
        results = await education_service.search_content(search_params)
        return results.results
        
    except Exception as e:
        logger.error(f"❌ Error fetching featured content: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch featured content"
        )

@router.get("/recent", response_model=List[ContentSummary])
async def get_recent_content(
    limit: int = Query(10, ge=1, le=50, description="Number of recent items to return")
):
    """
    Get recently published content
    
    Returns most recently published educational content
    """
    try:
        from api.models.education import ContentSearchRequest
        
        search_params = ContentSearchRequest(
            sort_by="published_at",
            sort_order="desc",
            page=1,
            per_page=limit
        )
        
        results = await education_service.search_content(search_params)
        return results.results
        
    except Exception as e:
        logger.error(f"❌ Error fetching recent content: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch recent content"
        )

@router.get("/popular", response_model=List[ContentSummary])
async def get_popular_content(
    limit: int = Query(10, ge=1, le=50, description="Number of popular items to return")
):
    """
    Get popular educational content
    
    Returns most viewed and liked educational content
    """
    try:
        from api.models.education import ContentSearchRequest
        
        search_params = ContentSearchRequest(
            sort_by="views_count",
            sort_order="desc",
            page=1,
            per_page=limit
        )
        
        results = await education_service.search_content(search_params)
        return results.results
        
    except Exception as e:
        logger.error(f"❌ Error fetching popular content: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch popular content"
        )

# =====================================================================================
# User Content Endpoints
# =====================================================================================

@router.get("/my-content", response_model=List[ContentSummary])
async def get_user_content(
    current_user: UserInDB = Depends(get_current_active_user),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page")
):
    """
    Get user's created content
    
    Returns content created by the authenticated user
    """
    try:
        from api.models.education import ContentSearchRequest
        
        search_params = ContentSearchRequest(
            author=current_user.username,
            sort_by="updated_at",
            sort_order="desc",
            page=page,
            per_page=per_page
        )
        
        results = await education_service.search_content(search_params)
        return results.results
        
    except Exception as e:
        logger.error(f"❌ Error fetching user content: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch user content"
        )

@router.get("/bookmarks", response_model=List[ContentSummary])
async def get_bookmarked_content(
    current_user: UserInDB = Depends(get_current_active_user),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page")
):
    """
    Get user's bookmarked content
    
    Returns content bookmarked by the authenticated user
    """
    try:
        # This would be implemented with a join to user_interactions
        # For now, return empty list with placeholder
        return []
        
    except Exception as e:
        logger.error(f"❌ Error fetching bookmarked content: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch bookmarked content"
        )

# =====================================================================================
# Content Templates and Examples
# =====================================================================================

@router.get("/templates")
async def get_content_templates():
    """
    Get content creation templates
    
    Returns templates for different content types
    """
    try:
        templates = {
            "article": {
                "name": "Educational Article",
                "structure": ["Introduction", "Main Concepts", "Examples", "Key Takeaways"],
                "example_tags": ["options", "basics", "strategy"],
                "estimated_read_time": 15
            },
            "strategy_guide": {
                "name": "Strategy Guide",
                "structure": ["Overview", "Setup", "Risk/Reward", "When to Use", "Example Trade"],
                "example_tags": ["strategy", "guide", "tutorial"],
                "estimated_read_time": 20
            },
            "tutorial": {
                "name": "Step-by-Step Tutorial",
                "structure": ["Prerequisites", "Step 1", "Step 2", "Step N", "Summary"],
                "example_tags": ["tutorial", "howto", "guide"],
                "estimated_read_time": 30
            }
        }
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "success": True,
                "templates": templates
            }
        )
        
    except Exception as e:
        logger.error(f"❌ Error fetching content templates: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch content templates"
        )