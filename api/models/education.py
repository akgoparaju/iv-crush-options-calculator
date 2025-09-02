"""
Education Models for Phase 5.4
Educational content management system models
"""

import logging
from datetime import datetime
from typing import List, Optional, Dict, Any
from uuid import UUID
from enum import Enum
from pydantic import BaseModel, Field, validator

logger = logging.getLogger(__name__)

# =====================================================================================
# Enums and Constants
# =====================================================================================

class ContentType(str, Enum):
    """Educational content types"""
    ARTICLE = "article"
    VIDEO = "video"
    TUTORIAL = "tutorial"
    STRATEGY_GUIDE = "strategy_guide"
    CASE_STUDY = "case_study"
    QUIZ = "quiz"
    GLOSSARY = "glossary"
    INFOGRAPHIC = "infographic"

class DifficultyLevel(str, Enum):
    """Content difficulty levels"""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate" 
    ADVANCED = "advanced"
    EXPERT = "expert"

class ContentStatus(str, Enum):
    """Content publication status"""
    DRAFT = "draft"
    UNDER_REVIEW = "under_review"
    PUBLISHED = "published"
    ARCHIVED = "archived"

class LearningPath(str, Enum):
    """Structured learning paths"""
    OPTIONS_BASICS = "options_basics"
    TRADING_STRATEGIES = "trading_strategies"
    RISK_MANAGEMENT = "risk_management"
    MARKET_ANALYSIS = "market_analysis"
    ADVANCED_CONCEPTS = "advanced_concepts"
    PORTFOLIO_MANAGEMENT = "portfolio_management"

class InteractionType(str, Enum):
    """User interaction types"""
    VIEW = "view"
    LIKE = "like"
    BOOKMARK = "bookmark"
    SHARE = "share"
    COMMENT = "comment"
    COMPLETE = "complete"

# =====================================================================================
# Request Models
# =====================================================================================

class CreateContentRequest(BaseModel):
    """Create new educational content"""
    title: str = Field(..., min_length=1, max_length=200, description="Content title")
    subtitle: Optional[str] = Field(None, max_length=300, description="Content subtitle")
    content_type: ContentType
    difficulty_level: DifficultyLevel
    learning_paths: List[LearningPath] = Field([], description="Associated learning paths")
    tags: List[str] = Field([], max_items=10, description="Content tags")
    summary: str = Field(..., min_length=10, max_length=1000, description="Content summary")
    content_body: str = Field(..., min_length=50, description="Main content body")
    estimated_read_time: int = Field(..., ge=1, le=240, description="Estimated read time in minutes")
    prerequisites: List[str] = Field([], description="Required knowledge or content")
    key_concepts: List[str] = Field([], max_items=15, description="Key concepts covered")
    is_premium: bool = Field(default=False, description="Premium content flag")
    featured: bool = Field(default=False, description="Featured content flag")

class UpdateContentRequest(BaseModel):
    """Update existing content"""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    subtitle: Optional[str] = Field(None, max_length=300)
    content_type: Optional[ContentType] = None
    difficulty_level: Optional[DifficultyLevel] = None
    learning_paths: Optional[List[LearningPath]] = Field(None, max_items=5)
    tags: Optional[List[str]] = Field(None, max_items=10)
    summary: Optional[str] = Field(None, min_length=10, max_length=1000)
    content_body: Optional[str] = Field(None, min_length=50)
    estimated_read_time: Optional[int] = Field(None, ge=1, le=240)
    prerequisites: Optional[List[str]] = None
    key_concepts: Optional[List[str]] = Field(None, max_items=15)
    status: Optional[ContentStatus] = None
    is_premium: Optional[bool] = None
    featured: Optional[bool] = None

class CreateCommentRequest(BaseModel):
    """Create comment on content"""
    content: str = Field(..., min_length=1, max_length=2000, description="Comment content")
    parent_comment_id: Optional[UUID] = Field(None, description="Parent comment ID for replies")

class UpdateCommentRequest(BaseModel):
    """Update comment"""
    content: str = Field(..., min_length=1, max_length=2000)

class CreateQuizRequest(BaseModel):
    """Create educational quiz"""
    title: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=10, max_length=1000)
    content_id: Optional[UUID] = Field(None, description="Associated content ID")
    difficulty_level: DifficultyLevel
    learning_paths: List[LearningPath] = Field([], max_items=3)
    questions: List[Dict[str, Any]] = Field(..., min_items=1, max_items=50, description="Quiz questions")
    passing_score: int = Field(70, ge=0, le=100, description="Passing score percentage")
    time_limit: Optional[int] = Field(None, ge=1, le=180, description="Time limit in minutes")

# =====================================================================================
# Response Models
# =====================================================================================

class ContentSummary(BaseModel):
    """Content summary for listings"""
    id: UUID
    title: str
    subtitle: Optional[str]
    content_type: ContentType
    difficulty_level: DifficultyLevel
    learning_paths: List[LearningPath]
    tags: List[str]
    summary: str
    author: str
    estimated_read_time: int
    views_count: int = 0
    likes_count: int = 0
    bookmarks_count: int = 0
    featured: bool
    is_premium: bool
    published_at: Optional[datetime]
    updated_at: datetime

    class Config:
        json_encoders = {
            datetime: lambda dt: dt.isoformat()
        }

class ContentDetailResponse(BaseModel):
    """Detailed content response"""
    id: UUID
    title: str
    subtitle: Optional[str]
    content_type: ContentType
    difficulty_level: DifficultyLevel
    learning_paths: List[LearningPath]
    tags: List[str]
    summary: str
    content_body: str
    author: str
    author_bio: Optional[str]
    estimated_read_time: int
    prerequisites: List[str]
    key_concepts: List[str]
    views_count: int = 0
    likes_count: int = 0
    bookmarks_count: int = 0
    comments_count: int = 0
    featured: bool
    is_premium: bool
    status: ContentStatus
    published_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    user_interactions: Dict[str, bool] = Field(default_factory=dict, description="Current user's interactions")

    class Config:
        json_encoders = {
            datetime: lambda dt: dt.isoformat()
        }

class CommentResponse(BaseModel):
    """Comment response"""
    id: UUID
    content_id: UUID
    user_id: UUID
    username: str
    content: str
    parent_comment_id: Optional[UUID]
    replies: List['CommentResponse'] = []
    likes_count: int = 0
    is_edited: bool = False
    created_at: datetime
    updated_at: datetime

    class Config:
        json_encoders = {
            datetime: lambda dt: dt.isoformat()
        }

# Enable forward references
CommentResponse.update_forward_refs()

class QuizResponse(BaseModel):
    """Quiz response"""
    id: UUID
    title: str
    description: str
    content_id: Optional[UUID]
    difficulty_level: DifficultyLevel
    learning_paths: List[LearningPath]
    questions_count: int
    passing_score: int
    time_limit: Optional[int]
    attempts_count: int = 0
    completion_rate: float = 0.0
    average_score: float = 0.0
    created_at: datetime
    updated_at: datetime

    class Config:
        json_encoders = {
            datetime: lambda dt: dt.isoformat()
        }

class QuizAttemptResponse(BaseModel):
    """Quiz attempt response"""
    id: UUID
    quiz_id: UUID
    user_id: UUID
    score: int
    passed: bool
    time_taken: int
    answers: Dict[str, Any]
    completed_at: datetime

    class Config:
        json_encoders = {
            datetime: lambda dt: dt.isoformat()
        }

class LearningProgressResponse(BaseModel):
    """User learning progress"""
    user_id: UUID
    learning_path: LearningPath
    progress_percentage: float
    completed_content: int
    total_content: int
    completed_quizzes: int
    total_quizzes: int
    average_quiz_score: float
    estimated_completion_time: int  # hours
    last_activity: datetime
    achievements: List[str] = []

    class Config:
        json_encoders = {
            datetime: lambda dt: dt.isoformat()
        }

class ContentAnalytics(BaseModel):
    """Content performance analytics"""
    content_id: UUID
    title: str
    views: int
    unique_viewers: int
    likes: int
    bookmarks: int
    comments: int
    completion_rate: float
    average_read_time: int
    engagement_score: float
    top_referrers: List[str]
    popular_sections: List[str]
    user_feedback: Dict[str, Any]
    performance_trend: List[Dict[str, Any]]

# =====================================================================================
# Search and Filter Models
# =====================================================================================

class ContentSearchRequest(BaseModel):
    """Content search parameters"""
    query: Optional[str] = Field(None, max_length=200, description="Search query")
    content_types: Optional[List[ContentType]] = None
    difficulty_levels: Optional[List[DifficultyLevel]] = None
    learning_paths: Optional[List[LearningPath]] = None
    tags: Optional[List[str]] = None
    featured_only: bool = False
    premium_only: bool = False
    min_read_time: Optional[int] = Field(None, ge=1)
    max_read_time: Optional[int] = Field(None, le=240)
    author: Optional[str] = None
    sort_by: str = Field("updated_at", description="Sort field")
    sort_order: str = Field("desc", description="Sort order: asc or desc")
    page: int = Field(1, ge=1, description="Page number")
    per_page: int = Field(20, ge=1, le=100, description="Items per page")

    @validator('sort_by')
    def validate_sort_by(cls, v):
        valid_sorts = ['title', 'created_at', 'updated_at', 'views_count', 'likes_count', 'difficulty_level']
        if v not in valid_sorts:
            raise ValueError(f'Invalid sort field: {v}. Must be one of {valid_sorts}')
        return v

    @validator('sort_order')
    def validate_sort_order(cls, v):
        if v not in ['asc', 'desc']:
            raise ValueError('Sort order must be "asc" or "desc"')
        return v

class ContentSearchResponse(BaseModel):
    """Search results response"""
    results: List[ContentSummary]
    total_count: int
    page: int
    per_page: int
    total_pages: int
    facets: Dict[str, Dict[str, int]] = Field(default_factory=dict, description="Search facets")

# =====================================================================================
# Internal Models (Database)
# =====================================================================================

class ContentInDB(BaseModel):
    """Content as stored in database"""
    id: UUID
    title: str
    subtitle: Optional[str]
    content_type: str
    difficulty_level: str
    learning_paths: List[str]
    tags: List[str]
    summary: str
    content_body: str
    author_id: UUID
    estimated_read_time: int
    prerequisites: List[str]
    key_concepts: List[str]
    status: str
    is_premium: bool
    featured: bool
    views_count: int
    likes_count: int
    bookmarks_count: int
    comments_count: int
    published_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

class UserInteractionInDB(BaseModel):
    """User interaction as stored in database"""
    id: UUID
    user_id: UUID
    content_id: UUID
    interaction_type: str
    metadata: Optional[Dict[str, Any]]
    created_at: datetime

class CommentInDB(BaseModel):
    """Comment as stored in database"""
    id: UUID
    content_id: UUID
    user_id: UUID
    content: str
    parent_comment_id: Optional[UUID]
    likes_count: int
    is_edited: bool
    created_at: datetime
    updated_at: datetime

class QuizInDB(BaseModel):
    """Quiz as stored in database"""
    id: UUID
    title: str
    description: str
    content_id: Optional[UUID]
    author_id: UUID
    difficulty_level: str
    learning_paths: List[str]
    questions: Dict[str, Any]
    passing_score: int
    time_limit: Optional[int]
    is_active: bool
    created_at: datetime
    updated_at: datetime

class QuizAttemptInDB(BaseModel):
    """Quiz attempt as stored in database"""
    id: UUID
    quiz_id: UUID
    user_id: UUID
    score: int
    passed: bool
    time_taken: int
    answers: Dict[str, Any]
    completed_at: datetime