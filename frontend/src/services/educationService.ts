// Educational content service for API integration
import { apiClient } from './api';
import {
  EducationalContent,
  ContentSeries,
  LearningPath,
  Quiz,
  QuizAttempt,
  Bookmark,
  BookmarkFolder,
  UserProgress,
  ContentFilter,
  ContentSort,
  ContentResponse,
  SeriesResponse,
  LearningPathsResponse,
  BookmarksResponse,
  ProgressResponse,
  CreateBookmarkRequest,
  CreateBookmarkFolderRequest,
  UpdateProgressRequest,
  RateContentRequest,
  ContentReview,
  ContentAnalytics,
  LearningRecommendations,
  QuizQuestion,
} from '../types/education';

export class EducationService {
  private baseUrl = '/education';

  // Content Management
  async getContent(
    filter?: ContentFilter,
    sort?: ContentSort,
    page = 1,
    limit = 20
  ): Promise<ContentResponse> {
    const params = new URLSearchParams();
    
    if (filter) {
      if (filter.categories) params.append('categories', filter.categories.join(','));
      if (filter.types) params.append('types', filter.types.join(','));
      if (filter.difficulties) params.append('difficulties', filter.difficulties.join(','));
      if (filter.tags) params.append('tags', filter.tags.join(','));
      if (filter.author_ids) params.append('author_ids', filter.author_ids.join(','));
      if (filter.is_premium !== undefined) params.append('is_premium', filter.is_premium.toString());
      if (filter.is_featured !== undefined) params.append('is_featured', filter.is_featured.toString());
      if (filter.min_duration) params.append('min_duration', filter.min_duration.toString());
      if (filter.max_duration) params.append('max_duration', filter.max_duration.toString());
      if (filter.min_rating) params.append('min_rating', filter.min_rating.toString());
      if (filter.search_query) params.append('q', filter.search_query);
    }
    
    if (sort) {
      params.append('sort_by', sort.field);
      params.append('sort_dir', sort.direction);
    }
    
    params.append('page', page.toString());
    params.append('limit', limit.toString());
    
    const response = await apiClient.get(`${this.baseUrl}/content?${params.toString()}`);
    return response.data;
  }

  async getContentById(contentId: string): Promise<EducationalContent> {
    const response = await apiClient.get(`${this.baseUrl}/content/${contentId}`);
    return response.data.content;
  }

  async getFeaturedContent(limit = 10): Promise<EducationalContent[]> {
    const response = await apiClient.get(`${this.baseUrl}/content/featured?limit=${limit}`);
    return response.data.content;
  }

  async getTrendingContent(limit = 10): Promise<EducationalContent[]> {
    const response = await apiClient.get(`${this.baseUrl}/content/trending?limit=${limit}`);
    return response.data.content;
  }

  async getRecentContent(limit = 10): Promise<EducationalContent[]> {
    const response = await apiClient.get(`${this.baseUrl}/content/recent?limit=${limit}`);
    return response.data.content;
  }

  // Content Series
  async getSeries(
    category?: string,
    page = 1,
    limit = 20
  ): Promise<SeriesResponse> {
    const params = new URLSearchParams();
    if (category) params.append('category', category);
    params.append('page', page.toString());
    params.append('limit', limit.toString());
    
    const response = await apiClient.get(`${this.baseUrl}/series?${params.toString()}`);
    return response.data;
  }

  async getSeriesById(seriesId: string): Promise<ContentSeries> {
    const response = await apiClient.get(`${this.baseUrl}/series/${seriesId}`);
    return response.data.series;
  }

  // Learning Paths
  async getLearningPaths(
    category?: string,
    difficulty?: string,
    page = 1,
    limit = 20
  ): Promise<LearningPathsResponse> {
    const params = new URLSearchParams();
    if (category) params.append('category', category);
    if (difficulty) params.append('difficulty', difficulty);
    params.append('page', page.toString());
    params.append('limit', limit.toString());
    
    const response = await apiClient.get(`${this.baseUrl}/learning-paths?${params.toString()}`);
    return response.data;
  }

  async getLearningPathById(pathId: string): Promise<LearningPath> {
    const response = await apiClient.get(`${this.baseUrl}/learning-paths/${pathId}`);
    return response.data.path;
  }

  async enrollInLearningPath(pathId: string): Promise<void> {
    await apiClient.post(`${this.baseUrl}/learning-paths/${pathId}/enroll`);
  }

  // User Progress
  async getUserProgress(contentId?: string): Promise<ProgressResponse> {
    const params = contentId ? `?content_id=${contentId}` : '';
    const response = await apiClient.get(`${this.baseUrl}/progress${params}`);
    return response.data;
  }

  async updateProgress(request: UpdateProgressRequest): Promise<UserProgress> {
    const response = await apiClient.post(`${this.baseUrl}/progress`, request);
    return response.data.progress;
  }

  async markContentComplete(contentId: string): Promise<UserProgress> {
    const response = await apiClient.post(`${this.baseUrl}/progress/${contentId}/complete`);
    return response.data.progress;
  }

  // Bookmarks
  async getBookmarks(folderId?: string, page = 1, limit = 50): Promise<BookmarksResponse> {
    const params = new URLSearchParams();
    if (folderId) params.append('folder_id', folderId);
    params.append('page', page.toString());
    params.append('limit', limit.toString());
    
    const response = await apiClient.get(`${this.baseUrl}/bookmarks?${params.toString()}`);
    return response.data;
  }

  async createBookmark(request: CreateBookmarkRequest): Promise<Bookmark> {
    const response = await apiClient.post(`${this.baseUrl}/bookmarks`, request);
    return response.data.bookmark;
  }

  async deleteBookmark(bookmarkId: string): Promise<void> {
    await apiClient.delete(`${this.baseUrl}/bookmarks/${bookmarkId}`);
  }

  async getBookmarkFolders(): Promise<BookmarkFolder[]> {
    const response = await apiClient.get(`${this.baseUrl}/bookmarks/folders`);
    return response.data.folders;
  }

  async createBookmarkFolder(request: CreateBookmarkFolderRequest): Promise<BookmarkFolder> {
    const response = await apiClient.post(`${this.baseUrl}/bookmarks/folders`, request);
    return response.data.folder;
  }

  async deleteBookmarkFolder(folderId: string): Promise<void> {
    await apiClient.delete(`${this.baseUrl}/bookmarks/folders/${folderId}`);
  }

  // Ratings and Reviews
  async rateContent(request: RateContentRequest): Promise<void> {
    await apiClient.post(`${this.baseUrl}/content/${request.content_id}/rate`, {
      rating: request.rating,
      review: request.review,
    });
  }

  async getContentReviews(contentId: string, page = 1, limit = 20): Promise<{
    reviews: ContentReview[];
    total_count: number;
    average_rating: number;
  }> {
    const response = await apiClient.get(
      `${this.baseUrl}/content/${contentId}/reviews?page=${page}&limit=${limit}`
    );
    return response.data;
  }

  // Quizzes
  async getQuizzes(contentId?: string): Promise<Quiz[]> {
    const params = contentId ? `?content_id=${contentId}` : '';
    const response = await apiClient.get(`${this.baseUrl}/quizzes${params}`);
    return response.data.quizzes;
  }

  async getQuizById(quizId: string): Promise<Quiz> {
    const response = await apiClient.get(`${this.baseUrl}/quizzes/${quizId}`);
    return response.data.quiz;
  }

  async startQuizAttempt(quizId: string): Promise<{ attempt_id: string }> {
    const response = await apiClient.post(`${this.baseUrl}/quizzes/${quizId}/attempts`);
    return response.data;
  }

  async submitQuizAnswer(
    attemptId: string,
    questionId: string,
    answer: string | string[]
  ): Promise<void> {
    await apiClient.post(`${this.baseUrl}/quiz-attempts/${attemptId}/answers`, {
      question_id: questionId,
      answer,
    });
  }

  async completeQuizAttempt(attemptId: string): Promise<QuizAttempt> {
    const response = await apiClient.post(`${this.baseUrl}/quiz-attempts/${attemptId}/complete`);
    return response.data.attempt;
  }

  async getQuizAttempts(quizId?: string): Promise<QuizAttempt[]> {
    const params = quizId ? `?quiz_id=${quizId}` : '';
    const response = await apiClient.get(`${this.baseUrl}/quiz-attempts${params}`);
    return response.data.attempts;
  }

  // Analytics and Recommendations
  async getContentAnalytics(contentId: string): Promise<ContentAnalytics> {
    const response = await apiClient.get(`${this.baseUrl}/content/${contentId}/analytics`);
    return response.data.analytics;
  }

  async getLearningRecommendations(limit = 10): Promise<LearningRecommendations> {
    const response = await apiClient.get(`${this.baseUrl}/recommendations?limit=${limit}`);
    return response.data;
  }

  async searchContent(query: string, filters?: ContentFilter): Promise<ContentResponse> {
    return this.getContent({ ...filters, search_query: query });
  }

  // Content Interaction
  async likeContent(contentId: string): Promise<void> {
    await apiClient.post(`${this.baseUrl}/content/${contentId}/like`);
  }

  async unlikeContent(contentId: string): Promise<void> {
    await apiClient.delete(`${this.baseUrl}/content/${contentId}/like`);
  }

  async viewContent(contentId: string): Promise<void> {
    await apiClient.post(`${this.baseUrl}/content/${contentId}/view`);
  }

  // Categories and Tags
  async getCategories(): Promise<Array<{ 
    id: string; 
    name: string; 
    description?: string; 
    content_count: number 
  }>> {
    const response = await apiClient.get(`${this.baseUrl}/categories`);
    return response.data.categories;
  }

  async getTags(query?: string): Promise<Array<{
    id: string;
    name: string;
    usage_count: number;
  }>> {
    const params = query ? `?q=${encodeURIComponent(query)}` : '';
    const response = await apiClient.get(`${this.baseUrl}/tags${params}`);
    return response.data.tags;
  }

  // Authors
  async getAuthors(page = 1, limit = 20): Promise<{
    authors: Array<{
      id: string;
      name: string;
      bio?: string;
      avatar?: string;
      credentials?: string[];
      content_count: number;
      average_rating: number;
    }>;
    total_count: number;
  }> {
    const response = await apiClient.get(`${this.baseUrl}/authors?page=${page}&limit=${limit}`);
    return response.data;
  }

  async getAuthorById(authorId: string): Promise<{
    author: {
      id: string;
      name: string;
      bio?: string;
      avatar?: string;
      credentials?: string[];
      social_links?: any;
      content_count: number;
      average_rating: number;
    };
    content: EducationalContent[];
  }> {
    const response = await apiClient.get(`${this.baseUrl}/authors/${authorId}`);
    return response.data;
  }

  // Study Notes
  async getStudyNotes(contentId?: string): Promise<Array<{
    id: string;
    content_id: string;
    notes: string;
    created_at: string;
    updated_at: string;
  }>> {
    const params = contentId ? `?content_id=${contentId}` : '';
    const response = await apiClient.get(`${this.baseUrl}/study-notes${params}`);
    return response.data.notes;
  }

  async createStudyNote(contentId: string, notes: string): Promise<{
    id: string;
    content_id: string;
    notes: string;
    created_at: string;
  }> {
    const response = await apiClient.post(`${this.baseUrl}/study-notes`, {
      content_id: contentId,
      notes,
    });
    return response.data.note;
  }

  async updateStudyNote(noteId: string, notes: string): Promise<void> {
    await apiClient.put(`${this.baseUrl}/study-notes/${noteId}`, { notes });
  }

  async deleteStudyNote(noteId: string): Promise<void> {
    await apiClient.delete(`${this.baseUrl}/study-notes/${noteId}`);
  }
}

// Export singleton instance
export const educationService = new EducationService();