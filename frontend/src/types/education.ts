// Educational content types for the options trading calculator

export type ContentType = 'article' | 'video' | 'tutorial' | 'guide' | 'case_study' | 'webinar' | 'course';
export type DifficultyLevel = 'beginner' | 'intermediate' | 'advanced' | 'expert';
export type ContentCategory = 
  | 'options_basics' 
  | 'strategies' 
  | 'risk_management' 
  | 'technical_analysis' 
  | 'market_psychology' 
  | 'portfolio_management'
  | 'earnings_trades'
  | 'volatility'
  | 'greeks'
  | 'tax_implications';

export interface ContentAuthor {
  id: string;
  name: string;
  bio?: string;
  avatar?: string;
  credentials?: string[];
  social_links?: {
    twitter?: string;
    linkedin?: string;
    website?: string;
  };
}

export interface ContentTag {
  id: string;
  name: string;
  color?: string;
}

export interface EducationalContent {
  id: string;
  title: string;
  description: string;
  content: string; // Full content (HTML or markdown)
  excerpt?: string;
  type: ContentType;
  category: ContentCategory;
  difficulty: DifficultyLevel;
  duration_minutes?: number;
  read_time_minutes?: number;
  
  // Media
  thumbnail_url?: string;
  video_url?: string;
  audio_url?: string;
  
  // Organization
  tags: ContentTag[];
  author: ContentAuthor;
  
  // Engagement
  views_count: number;
  likes_count: number;
  bookmarks_count: number;
  rating_average: number;
  rating_count: number;
  
  // User interactions
  is_liked?: boolean;
  is_bookmarked?: boolean;
  user_rating?: number;
  progress_percent?: number; // For courses/tutorials
  
  // Metadata
  published_at: string;
  updated_at: string;
  is_premium: boolean;
  is_featured: boolean;
  
  // Learning path
  prerequisites?: string[]; // Content IDs
  next_content?: string[]; // Suggested next content IDs
  series_id?: string;
  series_order?: number;
}

export interface ContentSeries {
  id: string;
  title: string;
  description: string;
  thumbnail_url?: string;
  author: ContentAuthor;
  category: ContentCategory;
  difficulty: DifficultyLevel;
  content_count: number;
  total_duration_minutes: number;
  completion_rate?: number; // User's completion percentage
  created_at: string;
  updated_at: string;
  is_premium: boolean;
  content_items: EducationalContent[];
}

export interface LearningPath {
  id: string;
  title: string;
  description: string;
  thumbnail_url?: string;
  category: ContentCategory;
  difficulty: DifficultyLevel;
  estimated_hours: number;
  completion_rate?: number;
  content_items: {
    content_id: string;
    order: number;
    is_required: boolean;
    is_completed?: boolean;
  }[];
  created_at: string;
  updated_at: string;
  is_premium: boolean;
}

export interface UserProgress {
  user_id: string;
  content_id: string;
  progress_percent: number;
  completed_at?: string;
  time_spent_minutes: number;
  notes?: string;
  created_at: string;
  updated_at: string;
}

export interface ContentFilter {
  categories?: ContentCategory[];
  types?: ContentType[];
  difficulties?: DifficultyLevel[];
  tags?: string[];
  author_ids?: string[];
  is_premium?: boolean;
  is_featured?: boolean;
  min_duration?: number;
  max_duration?: number;
  min_rating?: number;
  search_query?: string;
}

export interface ContentSort {
  field: 'created_at' | 'updated_at' | 'views_count' | 'rating_average' | 'title' | 'duration_minutes';
  direction: 'asc' | 'desc';
}

export interface ContentResponse {
  content: EducationalContent[];
  total_count: number;
  page: number;
  limit: number;
  has_more: boolean;
}

export interface QuizQuestion {
  id: string;
  question: string;
  type: 'multiple_choice' | 'true_false' | 'fill_in_blank' | 'matching';
  options?: string[]; // For multiple choice
  correct_answer: string | string[];
  explanation?: string;
  difficulty: DifficultyLevel;
  points: number;
}

export interface Quiz {
  id: string;
  title: string;
  description?: string;
  content_id?: string; // Associated content
  category: ContentCategory;
  difficulty: DifficultyLevel;
  questions: QuizQuestion[];
  time_limit_minutes?: number;
  passing_score: number;
  attempts_allowed: number;
  created_at: string;
  updated_at: string;
}

export interface QuizAttempt {
  id: string;
  quiz_id: string;
  user_id: string;
  score: number;
  max_score: number;
  percentage: number;
  time_taken_minutes: number;
  passed: boolean;
  answers: {
    question_id: string;
    answer: string | string[];
    is_correct: boolean;
    points_earned: number;
  }[];
  completed_at: string;
}

export interface BookmarkFolder {
  id: string;
  name: string;
  description?: string;
  user_id: string;
  bookmark_count: number;
  created_at: string;
  updated_at: string;
}

export interface Bookmark {
  id: string;
  user_id: string;
  content_id: string;
  folder_id?: string;
  notes?: string;
  created_at: string;
}

// Request types
export interface CreateBookmarkRequest {
  content_id: string;
  folder_id?: string;
  notes?: string;
}

export interface CreateBookmarkFolderRequest {
  name: string;
  description?: string;
}

export interface UpdateProgressRequest {
  content_id: string;
  progress_percent: number;
  time_spent_minutes?: number;
  notes?: string;
}

export interface RateContentRequest {
  content_id: string;
  rating: number; // 1-5
  review?: string;
}

export interface ContentReview {
  id: string;
  user_id: string;
  content_id: string;
  rating: number;
  review?: string;
  is_verified_purchase?: boolean;
  helpful_count: number;
  created_at: string;
  updated_at: string;
  user: {
    name: string;
    avatar?: string;
  };
}

// API Response types
export interface SeriesResponse {
  series: ContentSeries[];
  total_count: number;
  page: number;
  limit: number;
}

export interface LearningPathsResponse {
  paths: LearningPath[];
  total_count: number;
  page: number;
  limit: number;
}

export interface BookmarksResponse {
  bookmarks: (Bookmark & { content: EducationalContent })[];
  folders: BookmarkFolder[];
  total_count: number;
  page: number;
  limit: number;
}

export interface ProgressResponse {
  progress: UserProgress[];
  total_count: number;
  completion_stats: {
    total_content: number;
    completed_content: number;
    in_progress_content: number;
    total_time_spent_hours: number;
  };
}

export interface ContentAnalytics {
  content_id: string;
  views_today: number;
  views_week: number;
  views_month: number;
  completion_rate: number;
  average_time_spent: number;
  rating_breakdown: {
    [key: number]: number; // rating -> count
  };
}

export interface LearningRecommendations {
  based_on_progress: EducationalContent[];
  trending: EducationalContent[];
  similar_users: EducationalContent[];
  continue_learning: EducationalContent[];
}