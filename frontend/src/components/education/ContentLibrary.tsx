import React, { useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Card } from '../ui/Card';
import { Button } from '../ui/Button';
import { Badge } from '../ui/Badge';
import { Input } from '../ui/Input';
import { LoadingSpinner } from '../ui/LoadingSpinner';
import { 
  EducationalContent, 
  ContentFilter, 
  ContentSort,
  ContentType,
  DifficultyLevel,
  ContentCategory 
} from '../../types/education';
import { educationService } from '../../services/educationService';
import { 
  Search, 
  Filter,
  Star, 
  Clock, 
  Play,
  BookOpen,
  Video,
  Users,
  Award,
  Eye,
  Heart,
  Bookmark,
  ChevronDown,
  X
} from 'lucide-react';

interface ContentLibraryProps {
  onContentSelect?: (contentId: string) => void;
  searchQuery?: string;
  featuredContent?: EducationalContent[];
  trendingContent?: EducationalContent[];
  recentContent?: EducationalContent[];
}

const ContentLibrary: React.FC<ContentLibraryProps> = ({ 
  onContentSelect, 
  searchQuery = '',
  featuredContent,
  trendingContent,
  recentContent
}) => {
  const [activeFilter, setActiveFilter] = useState<ContentFilter>({});
  const [sortBy, setSortBy] = useState<ContentSort>({ field: 'created_at', direction: 'desc' });
  const [currentPage, setCurrentPage] = useState(1);
  const [showFilters, setShowFilters] = useState(false);
  const [localSearchQuery, setLocalSearchQuery] = useState(searchQuery);

  // Update local search when prop changes
  useEffect(() => {
    setLocalSearchQuery(searchQuery);
    if (searchQuery) {
      setActiveFilter(prev => ({ ...prev, search_query: searchQuery }));
    }
  }, [searchQuery]);

  // Fetch filtered content
  const { data: contentData, isLoading, error } = useQuery({
    queryKey: ['content-library', activeFilter, sortBy, currentPage],
    queryFn: () => educationService.getContent(activeFilter, sortBy, currentPage, 12),
  });

  // Fetch categories for filters
  const { data: categories } = useQuery({
    queryKey: ['content-categories'],
    queryFn: educationService.getCategories,
  });

  const contentTypes: { value: ContentType; label: string; icon: React.ComponentType<any> }[] = [
    { value: 'article', label: 'Articles', icon: BookOpen },
    { value: 'video', label: 'Videos', icon: Video },
    { value: 'tutorial', label: 'Tutorials', icon: Play },
    { value: 'course', label: 'Courses', icon: Award },
    { value: 'webinar', label: 'Webinars', icon: Users },
  ];

  const difficultyLevels: { value: DifficultyLevel; label: string; color: string }[] = [
    { value: 'beginner', label: 'Beginner', color: 'green' },
    { value: 'intermediate', label: 'Intermediate', color: 'yellow' },
    { value: 'advanced', label: 'Advanced', color: 'orange' },
    { value: 'expert', label: 'Expert', color: 'red' },
  ];

  const handleFilterChange = (newFilter: Partial<ContentFilter>) => {
    setActiveFilter(prev => ({ ...prev, ...newFilter }));
    setCurrentPage(1);
  };

  const clearFilters = () => {
    setActiveFilter({});
    setLocalSearchQuery('');
    setCurrentPage(1);
  };

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    handleFilterChange({ search_query: localSearchQuery });
  };

  const getContentIcon = (type: ContentType) => {
    const contentType = contentTypes.find(t => t.value === type);
    return contentType?.icon || BookOpen;
  };

  const getDifficultyColor = (difficulty: DifficultyLevel) => {
    const level = difficultyLevels.find(l => l.value === difficulty);
    return level?.color || 'gray';
  };

  if (error) {
    return (
      <Card className="p-8 text-center">
        <div className="text-red-500 mb-4">
          <X className="w-12 h-12 mx-auto" />
        </div>
        <h3 className="text-lg font-medium text-slate-900 mb-2">Failed to load content</h3>
        <p className="text-slate-600 mb-4">There was an error loading the educational content.</p>
        <Button onClick={() => window.location.reload()}>Try Again</Button>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      {/* Search and Filters */}
      <div className="space-y-4">
        <div className="flex flex-col sm:flex-row gap-4">
          <form onSubmit={handleSearch} className="flex-1 flex gap-2">
            <Input
              placeholder="Search content..."
              value={localSearchQuery}
              onChange={(e) => setLocalSearchQuery(e.target.value)}
              icon={Search}
            />
            <Button type="submit" variant="outline">
              Search
            </Button>
          </form>
          <Button 
            variant="outline"
            onClick={() => setShowFilters(!showFilters)}
            className="flex items-center gap-2"
          >
            <Filter className="w-4 h-4" />
            Filters
            <ChevronDown className={`w-4 h-4 transition-transform ${showFilters ? 'rotate-180' : ''}`} />
          </Button>
        </div>

        {/* Filter Panel */}
        {showFilters && (
          <Card className="p-4">
            <div className="space-y-4">
              {/* Content Types */}
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2">Content Type</label>
                <div className="flex flex-wrap gap-2">
                  {contentTypes.map((type) => {
                    const Icon = type.icon;
                    const isSelected = activeFilter.types?.includes(type.value);
                    return (
                      <Button
                        key={type.value}
                        variant={isSelected ? 'primary' : 'outline'}
                        size="sm"
                        onClick={() => {
                          const newTypes = isSelected
                            ? activeFilter.types?.filter(t => t !== type.value) || []
                            : [...(activeFilter.types || []), type.value];
                          handleFilterChange({ types: newTypes.length ? newTypes : undefined });
                        }}
                        className="flex items-center gap-2"
                      >
                        <Icon className="w-4 h-4" />
                        {type.label}
                      </Button>
                    );
                  })}
                </div>
              </div>

              {/* Categories */}
              {categories && categories.length > 0 && (
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-2">Category</label>
                  <div className="flex flex-wrap gap-2">
                    {categories.slice(0, 8).map((category) => {
                      const isSelected = activeFilter.categories?.includes(category.id as ContentCategory);
                      return (
                        <Button
                          key={category.id}
                          variant={isSelected ? 'primary' : 'outline'}
                          size="sm"
                          onClick={() => {
                            const newCategories = isSelected
                              ? activeFilter.categories?.filter(c => c !== category.id) || []
                              : [...(activeFilter.categories || []), category.id as ContentCategory];
                            handleFilterChange({ categories: newCategories.length ? newCategories : undefined });
                          }}
                        >
                          {category.name} ({category.content_count})
                        </Button>
                      );
                    })}
                  </div>
                </div>
              )}

              {/* Difficulty */}
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2">Difficulty Level</label>
                <div className="flex flex-wrap gap-2">
                  {difficultyLevels.map((level) => {
                    const isSelected = activeFilter.difficulties?.includes(level.value);
                    return (
                      <Button
                        key={level.value}
                        variant={isSelected ? 'primary' : 'outline'}
                        size="sm"
                        onClick={() => {
                          const newDifficulties = isSelected
                            ? activeFilter.difficulties?.filter(d => d !== level.value) || []
                            : [...(activeFilter.difficulties || []), level.value];
                          handleFilterChange({ difficulties: newDifficulties.length ? newDifficulties : undefined });
                        }}
                      >
                        {level.label}
                      </Button>
                    );
                  })}
                </div>
              </div>

              {/* Additional Filters */}
              <div className="flex flex-wrap gap-4">
                <label className="flex items-center space-x-2">
                  <input
                    type="checkbox"
                    checked={activeFilter.is_featured || false}
                    onChange={(e) => handleFilterChange({ is_featured: e.target.checked || undefined })}
                    className="rounded border-slate-300"
                  />
                  <span className="text-sm text-slate-700">Featured Content</span>
                </label>
                <label className="flex items-center space-x-2">
                  <input
                    type="checkbox"
                    checked={activeFilter.is_premium || false}
                    onChange={(e) => handleFilterChange({ is_premium: e.target.checked || undefined })}
                    className="rounded border-slate-300"
                  />
                  <span className="text-sm text-slate-700">Premium Content</span>
                </label>
              </div>

              {/* Clear Filters */}
              <div className="flex justify-between items-center pt-2 border-t">
                <span className="text-sm text-slate-600">
                  {Object.keys(activeFilter).length > 0 ? `${Object.keys(activeFilter).length} filters active` : 'No filters applied'}
                </span>
                <Button variant="outline" size="sm" onClick={clearFilters}>
                  Clear All
                </Button>
              </div>
            </div>
          </Card>
        )}
      </div>

      {/* Sort Options */}
      <div className="flex items-center justify-between">
        <p className="text-sm text-slate-600">
          {contentData ? `${contentData.total_count} results found` : 'Loading...'}
        </p>
        <div className="flex items-center gap-2">
          <label className="text-sm text-slate-600">Sort by:</label>
          <select
            value={`${sortBy.field}-${sortBy.direction}`}
            onChange={(e) => {
              const [field, direction] = e.target.value.split('-');
              setSortBy({ field: field as any, direction: direction as 'asc' | 'desc' });
            }}
            className="text-sm border border-slate-300 rounded px-2 py-1"
          >
            <option value="created_at-desc">Newest First</option>
            <option value="created_at-asc">Oldest First</option>
            <option value="rating_average-desc">Highest Rated</option>
            <option value="views_count-desc">Most Popular</option>
            <option value="title-asc">Title A-Z</option>
            <option value="duration_minutes-asc">Shortest First</option>
            <option value="duration_minutes-desc">Longest First</option>
          </select>
        </div>
      </div>

      {/* Content Grid */}
      {isLoading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {[...Array(12)].map((_, i) => (
            <div key={i} className="animate-pulse">
              <div className="h-48 bg-slate-200 rounded-lg mb-4"></div>
              <div className="h-4 bg-slate-200 rounded mb-2"></div>
              <div className="h-3 bg-slate-200 rounded mb-2"></div>
              <div className="h-3 bg-slate-200 rounded w-1/2"></div>
            </div>
          ))}
        </div>
      ) : contentData && contentData.content.length > 0 ? (
        <>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {contentData.content.map((content) => {
              const ContentIcon = getContentIcon(content.type);
              return (
                <Card 
                  key={content.id} 
                  className="overflow-hidden cursor-pointer hover:shadow-lg transition-shadow"
                  onClick={() => onContentSelect?.(content.id)}
                >
                  {content.thumbnail_url ? (
                    <img
                      src={content.thumbnail_url}
                      alt={content.title}
                      className="w-full h-48 object-cover"
                    />
                  ) : (
                    <div className="w-full h-48 bg-gradient-to-br from-primary-100 to-primary-200 flex items-center justify-center">
                      <ContentIcon className="w-12 h-12 text-primary-600" />
                    </div>
                  )}
                  
                  <div className="p-4">
                    <div className="flex items-center gap-2 mb-2">
                      <Badge variant="outline" className="text-xs">
                        {content.type}
                      </Badge>
                      <Badge 
                        variant="secondary" 
                        className={`text-xs bg-${getDifficultyColor(content.difficulty)}-100 text-${getDifficultyColor(content.difficulty)}-800`}
                      >
                        {content.difficulty}
                      </Badge>
                      {content.is_premium && (
                        <Badge variant="warning" className="text-xs">Premium</Badge>
                      )}
                      {content.is_featured && (
                        <Star className="w-3 h-3 text-yellow-500 fill-current" />
                      )}
                    </div>
                    
                    <h3 className="font-semibold text-slate-900 mb-2 line-clamp-2">
                      {content.title}
                    </h3>
                    
                    <p className="text-sm text-slate-600 mb-3 line-clamp-2">
                      {content.description}
                    </p>
                    
                    <div className="flex items-center justify-between text-xs text-slate-500 mb-3">
                      <span className="flex items-center gap-1">
                        <Clock className="w-3 h-3" />
                        {content.duration_minutes || content.read_time_minutes}m
                      </span>
                      <span className="flex items-center gap-1">
                        <Star className="w-3 h-3 fill-current text-yellow-500" />
                        {content.rating_average.toFixed(1)}
                      </span>
                      <span className="flex items-center gap-1">
                        <Eye className="w-3 h-3" />
                        {content.views_count.toLocaleString()}
                      </span>
                    </div>
                    
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-slate-600">
                        by {content.author.name}
                      </span>
                      <div className="flex items-center gap-1">
                        {content.is_liked && <Heart className="w-4 h-4 text-red-500 fill-current" />}
                        {content.is_bookmarked && <Bookmark className="w-4 h-4 text-blue-500 fill-current" />}
                      </div>
                    </div>
                    
                    {content.progress_percent !== undefined && (
                      <div className="mt-3">
                        <div className="flex justify-between text-xs text-slate-600 mb-1">
                          <span>Progress</span>
                          <span>{content.progress_percent}%</span>
                        </div>
                        <div className="w-full bg-slate-200 rounded-full h-1">
                          <div 
                            className="bg-primary-600 h-1 rounded-full"
                            style={{ width: `${content.progress_percent}%` }}
                          />
                        </div>
                      </div>
                    )}
                  </div>
                </Card>
              );
            })}
          </div>

          {/* Pagination */}
          {contentData.has_more && (
            <div className="flex justify-center">
              <Button
                onClick={() => setCurrentPage(prev => prev + 1)}
                loading={isLoading}
              >
                Load More
              </Button>
            </div>
          )}
        </>
      ) : (
        <Card className="p-12 text-center">
          <div className="text-slate-400 mb-4">
            <Search className="w-12 h-12 mx-auto" />
          </div>
          <h3 className="text-lg font-medium text-slate-900 mb-2">No content found</h3>
          <p className="text-slate-600 mb-4">
            Try adjusting your search terms or filters to find what you're looking for.
          </p>
          <Button variant="outline" onClick={clearFilters}>
            Clear Filters
          </Button>
        </Card>
      )}
    </div>
  );
};

export default ContentLibrary;