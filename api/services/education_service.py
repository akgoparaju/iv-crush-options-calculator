"""
Education Service for Phase 5.4
Educational content management business logic
"""

import logging
import json
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Tuple
from uuid import UUID, uuid4
from math import ceil

from api.models.education import (
    ContentInDB, UserInteractionInDB, CommentInDB, QuizInDB, QuizAttemptInDB,
    ContentSummary, ContentDetailResponse, CommentResponse, QuizResponse, 
    QuizAttemptResponse, LearningProgressResponse, ContentAnalytics, 
    ContentSearchResponse, CreateContentRequest, UpdateContentRequest,
    CreateCommentRequest, UpdateCommentRequest, CreateQuizRequest,
    ContentSearchRequest, ContentType, DifficultyLevel, ContentStatus,
    LearningPath, InteractionType
)
from api.services.database_service import database_service
from api.core.exceptions import EducationServiceError, ValidationError
from fastapi import HTTPException, status

logger = logging.getLogger(__name__)

class EducationService:
    """Service for educational content management"""
    
    def __init__(self):
        self.db = database_service
        self._content_cache = {}
        self._cache_ttl = 1800  # 30 minutes
        logger.info("📚 Education service initialized")
    
    # =====================================================================================
    # Content Management
    # =====================================================================================
    
    async def create_content(self, author_id: UUID, content_data: CreateContentRequest) -> ContentDetailResponse:
        """Create new educational content"""
        try:
            content_id = uuid4()
            
            query = """
                INSERT INTO educational_content (
                    id, title, subtitle, content_type, difficulty_level, learning_paths,
                    tags, summary, content_body, author_id, estimated_read_time,
                    prerequisites, key_concepts, status, is_premium, featured,
                    created_at, updated_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, NOW(), NOW())
                RETURNING *
            """
            
            async with self.db.get_connection() as conn:
                row = await conn.fetchrow(
                    query, content_id, content_data.title, content_data.subtitle,
                    content_data.content_type.value, content_data.difficulty_level.value,
                    [path.value for path in content_data.learning_paths],
                    content_data.tags, content_data.summary, content_data.content_body,
                    author_id, content_data.estimated_read_time, content_data.prerequisites,
                    content_data.key_concepts, ContentStatus.DRAFT.value,
                    content_data.is_premium, content_data.featured
                )
                
                if not row:
                    raise EducationServiceError("Failed to create content")
                
                return await self._row_to_content_detail(row, author_id)
                
        except Exception as e:
            logger.error(f"❌ Error creating content: {str(e)}")
            if isinstance(e, (ValidationError, EducationServiceError)):
                raise
            raise EducationServiceError(f"Failed to create content: {str(e)}")
    
    async def get_content(self, content_id: UUID, user_id: Optional[UUID] = None) -> ContentDetailResponse:
        """Get content by ID"""
        try:
            # Check cache first
            cache_key = f"content_{content_id}_{user_id}"
            if self._is_cache_valid(cache_key):
                return self._content_cache[cache_key]['data']
            
            query = """
                SELECT c.*, u.username as author_name, u.email as author_email,
                       up.bio as author_bio
                FROM educational_content c
                JOIN users u ON c.author_id = u.id
                LEFT JOIN user_profiles up ON c.author_id = up.user_id
                WHERE c.id = $1 AND c.status = 'published'
            """
            
            async with self.db.get_connection() as conn:
                async with conn.transaction():
                    row = await conn.fetchrow(query, content_id)
                    
                    if not row:
                        raise HTTPException(
                            status_code=status.HTTP_404_NOT_FOUND,
                            detail="Content not found"
                        )
                    
                    # Increment view count
                    await conn.execute(
                        "UPDATE educational_content SET views_count = views_count + 1 WHERE id = $1",
                        content_id
                    )
                    
                    # Track user interaction
                    if user_id:
                        await self._track_interaction(user_id, content_id, InteractionType.VIEW, conn)
                    
                    content = await self._row_to_content_detail(row, user_id)
                    
                    # Cache result
                    self._content_cache[cache_key] = {
                        'data': content,
                        'timestamp': datetime.utcnow()
                    }
                    
                    return content
                    
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"❌ Error fetching content: {str(e)}")
            raise EducationServiceError(f"Failed to fetch content: {str(e)}")
    
    async def update_content(self, content_id: UUID, author_id: UUID, 
                           updates: UpdateContentRequest) -> ContentDetailResponse:
        """Update existing content"""
        try:
            # Build dynamic update query
            set_clauses = []
            values = []
            param_count = 1
            
            update_fields = {
                'title': updates.title,
                'subtitle': updates.subtitle,
                'content_type': updates.content_type.value if updates.content_type else None,
                'difficulty_level': updates.difficulty_level.value if updates.difficulty_level else None,
                'learning_paths': [path.value for path in updates.learning_paths] if updates.learning_paths else None,
                'tags': updates.tags,
                'summary': updates.summary,
                'content_body': updates.content_body,
                'estimated_read_time': updates.estimated_read_time,
                'prerequisites': updates.prerequisites,
                'key_concepts': updates.key_concepts,
                'status': updates.status.value if updates.status else None,
                'is_premium': updates.is_premium,
                'featured': updates.featured
            }
            
            for field, value in update_fields.items():
                if value is not None:
                    set_clauses.append(f"{field} = ${param_count}")
                    values.append(value)
                    param_count += 1
            
            if not set_clauses:
                return await self.get_content(content_id)
            
            set_clauses.append("updated_at = NOW()")
            
            # Add published_at if status is being changed to published
            if updates.status == ContentStatus.PUBLISHED:
                set_clauses.append("published_at = NOW()")
            
            query = f"""
                UPDATE educational_content 
                SET {', '.join(set_clauses)}
                WHERE id = ${param_count} AND author_id = ${param_count + 1}
                RETURNING *
            """
            values.extend([content_id, author_id])
            
            async with self.db.get_connection() as conn:
                row = await conn.fetchrow(query, *values)
                
                if not row:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="Content not found or access denied"
                    )
                
                # Clear cache
                self._clear_content_cache(content_id)
                
                return await self._row_to_content_detail(row, author_id)
                
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"❌ Error updating content: {str(e)}")
            raise EducationServiceError(f"Failed to update content: {str(e)}")
    
    async def delete_content(self, content_id: UUID, author_id: UUID) -> bool:
        """Delete content (soft delete by archiving)"""
        try:
            query = """
                UPDATE educational_content 
                SET status = 'archived', updated_at = NOW()
                WHERE id = $1 AND author_id = $2
                RETURNING id
            """
            
            async with self.db.get_connection() as conn:
                row = await conn.fetchrow(query, content_id, author_id)
                
                if row:
                    self._clear_content_cache(content_id)
                    return True
                return False
                
        except Exception as e:
            logger.error(f"❌ Error deleting content: {str(e)}")
            raise EducationServiceError(f"Failed to delete content: {str(e)}")
    
    async def search_content(self, search_params: ContentSearchRequest) -> ContentSearchResponse:
        """Search educational content"""
        try:
            # Build search query
            where_conditions = ["c.status = 'published'"]
            join_conditions = ["JOIN users u ON c.author_id = u.id"]
            values = []
            param_count = 1
            
            # Text search
            if search_params.query:
                where_conditions.append(f"""
                    (c.title ILIKE ${param_count} OR c.summary ILIKE ${param_count} 
                     OR c.content_body ILIKE ${param_count} OR array_to_string(c.tags, ' ') ILIKE ${param_count})
                """)
                values.append(f"%{search_params.query}%")
                param_count += 1
            
            # Content type filter
            if search_params.content_types:
                placeholders = [f"${param_count + i}" for i in range(len(search_params.content_types))]
                where_conditions.append(f"c.content_type = ANY(ARRAY[{','.join(placeholders)}])")
                values.extend([ct.value for ct in search_params.content_types])
                param_count += len(search_params.content_types)
            
            # Difficulty filter
            if search_params.difficulty_levels:
                placeholders = [f"${param_count + i}" for i in range(len(search_params.difficulty_levels))]
                where_conditions.append(f"c.difficulty_level = ANY(ARRAY[{','.join(placeholders)}])")
                values.extend([dl.value for dl in search_params.difficulty_levels])
                param_count += len(search_params.difficulty_levels)
            
            # Learning paths filter
            if search_params.learning_paths:
                where_conditions.append(f"c.learning_paths && ${param_count}")
                values.append([lp.value for lp in search_params.learning_paths])
                param_count += 1
            
            # Tags filter
            if search_params.tags:
                where_conditions.append(f"c.tags && ${param_count}")
                values.append(search_params.tags)
                param_count += 1
            
            # Featured filter
            if search_params.featured_only:
                where_conditions.append("c.featured = true")
            
            # Premium filter
            if search_params.premium_only:
                where_conditions.append("c.is_premium = true")
            
            # Read time filters
            if search_params.min_read_time:
                where_conditions.append(f"c.estimated_read_time >= ${param_count}")
                values.append(search_params.min_read_time)
                param_count += 1
                
            if search_params.max_read_time:
                where_conditions.append(f"c.estimated_read_time <= ${param_count}")
                values.append(search_params.max_read_time)
                param_count += 1
            
            # Author filter
            if search_params.author:
                where_conditions.append(f"u.username ILIKE ${param_count}")
                values.append(f"%{search_params.author}%")
                param_count += 1
            
            # Build ORDER BY clause
            sort_mapping = {
                'title': 'c.title',
                'created_at': 'c.created_at',
                'updated_at': 'c.updated_at',
                'views_count': 'c.views_count',
                'likes_count': 'c.likes_count',
                'difficulty_level': 'c.difficulty_level'
            }
            order_clause = f"ORDER BY {sort_mapping[search_params.sort_by]} {search_params.sort_order.upper()}"
            
            # Count query
            count_query = f"""
                SELECT COUNT(*)
                FROM educational_content c
                {' '.join(join_conditions)}
                WHERE {' AND '.join(where_conditions)}
            """
            
            # Main query with pagination
            offset = (search_params.page - 1) * search_params.per_page
            main_query = f"""
                SELECT c.id, c.title, c.subtitle, c.content_type, c.difficulty_level,
                       c.learning_paths, c.tags, c.summary, c.estimated_read_time,
                       c.views_count, c.likes_count, c.bookmarks_count, c.featured,
                       c.is_premium, c.published_at, c.updated_at, u.username as author
                FROM educational_content c
                {' '.join(join_conditions)}
                WHERE {' AND '.join(where_conditions)}
                {order_clause}
                LIMIT ${param_count} OFFSET ${param_count + 1}
            """
            values.extend([search_params.per_page, offset])
            
            async with self.db.get_connection() as conn:
                # Get total count
                total_count = await conn.fetchval(count_query, *values[:-2])
                
                # Get results
                rows = await conn.fetch(main_query, *values)
                
                # Convert to response models
                results = []
                for row in rows:
                    results.append(ContentSummary(
                        id=row['id'],
                        title=row['title'],
                        subtitle=row['subtitle'],
                        content_type=ContentType(row['content_type']),
                        difficulty_level=DifficultyLevel(row['difficulty_level']),
                        learning_paths=[LearningPath(lp) for lp in row['learning_paths']],
                        tags=row['tags'],
                        summary=row['summary'],
                        author=row['author'],
                        estimated_read_time=row['estimated_read_time'],
                        views_count=row['views_count'],
                        likes_count=row['likes_count'],
                        bookmarks_count=row['bookmarks_count'],
                        featured=row['featured'],
                        is_premium=row['is_premium'],
                        published_at=row['published_at'],
                        updated_at=row['updated_at']
                    ))
                
                total_pages = ceil(total_count / search_params.per_page)
                
                return ContentSearchResponse(
                    results=results,
                    total_count=total_count,
                    page=search_params.page,
                    per_page=search_params.per_page,
                    total_pages=total_pages,
                    facets=await self._build_search_facets(search_params, where_conditions, values[:-2])
                )
                
        except Exception as e:
            logger.error(f"❌ Error searching content: {str(e)}")
            raise EducationServiceError(f"Failed to search content: {str(e)}")
    
    # =====================================================================================
    # User Interactions
    # =====================================================================================
    
    async def toggle_like(self, user_id: UUID, content_id: UUID) -> bool:
        """Toggle like on content"""
        try:
            async with self.db.get_connection() as conn:
                async with conn.transaction():
                    # Check if already liked
                    existing = await conn.fetchrow(
                        """SELECT id FROM user_interactions 
                           WHERE user_id = $1 AND content_id = $2 AND interaction_type = 'like'""",
                        user_id, content_id
                    )
                    
                    if existing:
                        # Unlike
                        await conn.execute(
                            "DELETE FROM user_interactions WHERE id = $1",
                            existing['id']
                        )
                        await conn.execute(
                            "UPDATE educational_content SET likes_count = likes_count - 1 WHERE id = $1",
                            content_id
                        )
                        return False
                    else:
                        # Like
                        await self._track_interaction(user_id, content_id, InteractionType.LIKE, conn)
                        await conn.execute(
                            "UPDATE educational_content SET likes_count = likes_count + 1 WHERE id = $1",
                            content_id
                        )
                        return True
                        
        except Exception as e:
            logger.error(f"❌ Error toggling like: {str(e)}")
            raise EducationServiceError(f"Failed to toggle like: {str(e)}")
    
    async def toggle_bookmark(self, user_id: UUID, content_id: UUID) -> bool:
        """Toggle bookmark on content"""
        try:
            async with self.db.get_connection() as conn:
                async with conn.transaction():
                    # Check if already bookmarked
                    existing = await conn.fetchrow(
                        """SELECT id FROM user_interactions 
                           WHERE user_id = $1 AND content_id = $2 AND interaction_type = 'bookmark'""",
                        user_id, content_id
                    )
                    
                    if existing:
                        # Remove bookmark
                        await conn.execute(
                            "DELETE FROM user_interactions WHERE id = $1",
                            existing['id']
                        )
                        await conn.execute(
                            "UPDATE educational_content SET bookmarks_count = bookmarks_count - 1 WHERE id = $1",
                            content_id
                        )
                        return False
                    else:
                        # Add bookmark
                        await self._track_interaction(user_id, content_id, InteractionType.BOOKMARK, conn)
                        await conn.execute(
                            "UPDATE educational_content SET bookmarks_count = bookmarks_count + 1 WHERE id = $1",
                            content_id
                        )
                        return True
                        
        except Exception as e:
            logger.error(f"❌ Error toggling bookmark: {str(e)}")
            raise EducationServiceError(f"Failed to toggle bookmark: {str(e)}")
    
    # =====================================================================================
    # Learning Progress
    # =====================================================================================
    
    async def get_learning_progress(self, user_id: UUID, 
                                  learning_path: LearningPath) -> LearningProgressResponse:
        """Get user's learning progress for a path"""
        try:
            query = """
                WITH path_content AS (
                    SELECT id FROM educational_content 
                    WHERE $1 = ANY(learning_paths) AND status = 'published'
                ),
                path_quizzes AS (
                    SELECT id FROM educational_quizzes 
                    WHERE $1 = ANY(learning_paths) AND is_active = true
                ),
                completed_content AS (
                    SELECT COUNT(*) FROM user_interactions ui
                    JOIN path_content pc ON ui.content_id = pc.id
                    WHERE ui.user_id = $2 AND ui.interaction_type = 'complete'
                ),
                completed_quizzes AS (
                    SELECT COUNT(*), AVG(score) FROM quiz_attempts qa
                    JOIN path_quizzes pq ON qa.quiz_id = pq.id
                    WHERE qa.user_id = $2 AND qa.passed = true
                ),
                last_activity AS (
                    SELECT MAX(created_at) FROM user_interactions
                    WHERE user_id = $2
                )
                SELECT 
                    (SELECT count FROM completed_content) as completed_content_count,
                    (SELECT count FROM path_content) as total_content_count,
                    (SELECT count FROM completed_quizzes) as completed_quizzes_count,
                    (SELECT count FROM path_quizzes) as total_quizzes_count,
                    (SELECT avg FROM completed_quizzes) as average_quiz_score,
                    (SELECT max FROM last_activity) as last_activity
            """
            
            async with self.db.get_connection() as conn:
                row = await conn.fetchrow(query, learning_path.value, user_id)
                
                completed_content = row['completed_content_count'] or 0
                total_content = row['total_content_count'] or 1
                completed_quizzes = row['completed_quizzes_count'] or 0
                total_quizzes = row['total_quizzes_count'] or 0
                
                progress_percentage = (completed_content + completed_quizzes) / (total_content + total_quizzes) * 100
                estimated_hours = max(1, (total_content - completed_content) * 2)  # 2 hours per content
                
                return LearningProgressResponse(
                    user_id=user_id,
                    learning_path=learning_path,
                    progress_percentage=min(100, progress_percentage),
                    completed_content=completed_content,
                    total_content=total_content,
                    completed_quizzes=completed_quizzes,
                    total_quizzes=total_quizzes,
                    average_quiz_score=float(row['average_quiz_score'] or 0),
                    estimated_completion_time=estimated_hours,
                    last_activity=row['last_activity'] or datetime.utcnow(),
                    achievements=await self._get_user_achievements(user_id, learning_path)
                )
                
        except Exception as e:
            logger.error(f"❌ Error getting learning progress: {str(e)}")
            raise EducationServiceError(f"Failed to get learning progress: {str(e)}")
    
    # =====================================================================================
    # Private Methods
    # =====================================================================================
    
    async def _row_to_content_detail(self, row: Dict[str, Any], user_id: Optional[UUID] = None) -> ContentDetailResponse:
        """Convert database row to ContentDetailResponse"""
        user_interactions = {}
        
        if user_id:
            # Get user interactions
            async with self.db.get_connection() as conn:
                interactions = await conn.fetch(
                    "SELECT interaction_type FROM user_interactions WHERE user_id = $1 AND content_id = $2",
                    user_id, row['id']
                )
                user_interactions = {i['interaction_type']: True for i in interactions}
        
        return ContentDetailResponse(
            id=row['id'],
            title=row['title'],
            subtitle=row['subtitle'],
            content_type=ContentType(row['content_type']),
            difficulty_level=DifficultyLevel(row['difficulty_level']),
            learning_paths=[LearningPath(lp) for lp in row['learning_paths']],
            tags=row['tags'],
            summary=row['summary'],
            content_body=row['content_body'],
            author=row.get('author_name', 'Unknown'),
            author_bio=row.get('author_bio'),
            estimated_read_time=row['estimated_read_time'],
            prerequisites=row['prerequisites'],
            key_concepts=row['key_concepts'],
            views_count=row['views_count'],
            likes_count=row['likes_count'],
            bookmarks_count=row['bookmarks_count'],
            comments_count=row.get('comments_count', 0),
            featured=row['featured'],
            is_premium=row['is_premium'],
            status=ContentStatus(row['status']),
            published_at=row['published_at'],
            created_at=row['created_at'],
            updated_at=row['updated_at'],
            user_interactions=user_interactions
        )
    
    async def _track_interaction(self, user_id: UUID, content_id: UUID, 
                               interaction_type: InteractionType, conn) -> None:
        """Track user interaction"""
        try:
            await conn.execute(
                """INSERT INTO user_interactions (id, user_id, content_id, interaction_type, created_at)
                   VALUES ($1, $2, $3, $4, NOW())""",
                uuid4(), user_id, content_id, interaction_type.value
            )
        except Exception as e:
            logger.warning(f"⚠️ Failed to track interaction: {str(e)}")
    
    async def _build_search_facets(self, search_params: ContentSearchRequest,
                                 where_conditions: List[str], values: List[Any]) -> Dict[str, Dict[str, int]]:
        """Build search facets for filtering"""
        try:
            # This would build facets like content_type counts, difficulty counts, etc.
            # For now, return empty facets
            return {
                "content_types": {},
                "difficulty_levels": {},
                "learning_paths": {}
            }
        except Exception:
            return {}
    
    async def _get_user_achievements(self, user_id: UUID, learning_path: LearningPath) -> List[str]:
        """Get user achievements for learning path"""
        # This would return achievements like "First Article Read", "Quiz Master", etc.
        return ["Getting Started", "Active Learner"]
    
    def _is_cache_valid(self, cache_key: str) -> bool:
        """Check if cache entry is still valid"""
        if cache_key not in self._content_cache:
            return False
        
        cached_time = self._content_cache[cache_key]['timestamp']
        age = (datetime.utcnow() - cached_time).total_seconds()
        
        return age < self._cache_ttl
    
    def _clear_content_cache(self, content_id: UUID) -> None:
        """Clear cache entries for content"""
        keys_to_remove = [k for k in self._content_cache.keys() if str(content_id) in k]
        for key in keys_to_remove:
            self._content_cache.pop(key, None)

# Global education service instance
education_service = EducationService()