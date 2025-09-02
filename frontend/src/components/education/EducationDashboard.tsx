import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Card } from '../ui/Card';
import { Button } from '../ui/Button';
import { Badge } from '../ui/Badge';
import { Input } from '../ui/Input';
import { LoadingSpinner } from '../ui/LoadingSpinner';
import { educationService } from '../../services/educationService';
import ContentLibrary from './ContentLibrary';
import LearningPaths from './LearningPaths';
import MyProgress from './MyProgress';
import Bookmarks from './Bookmarks';
import { 
  BookOpen, 
  TrendingUp, 
  Clock, 
  Star,
  Search,
  Filter,
  Play,
  Users,
  Award,
  Brain
} from 'lucide-react';

interface EducationDashboardProps {
  onContentSelect?: (contentId: string) => void;
}

type TabType = 'library' | 'paths' | 'progress' | 'bookmarks';

const EducationDashboard: React.FC<EducationDashboardProps> = ({ onContentSelect }) => {
  const [activeTab, setActiveTab] = useState<TabType>('library');
  const [searchQuery, setSearchQuery] = useState('');

  // Fetch dashboard data
  const { data: featuredContent, isLoading: featuredLoading } = useQuery({
    queryKey: ['featured-content'],
    queryFn: () => educationService.getFeaturedContent(8),
  });

  const { data: trendingContent, isLoading: trendingLoading } = useQuery({
    queryKey: ['trending-content'],
    queryFn: () => educationService.getTrendingContent(6),
  });

  const { data: recentContent, isLoading: recentLoading } = useQuery({
    queryKey: ['recent-content'],
    queryFn: () => educationService.getRecentContent(6),
  });

  const { data: progressData, isLoading: progressLoading } = useQuery({
    queryKey: ['user-progress'],
    queryFn: () => educationService.getUserProgress(),
  });

  const { data: recommendations, isLoading: recommendationsLoading } = useQuery({
    queryKey: ['learning-recommendations'],
    queryFn: () => educationService.getLearningRecommendations(6),
  });

  const tabs = [
    { 
      id: 'library' as TabType, 
      name: 'Content Library', 
      icon: BookOpen,
      description: 'Browse all educational content'
    },
    { 
      id: 'paths' as TabType, 
      name: 'Learning Paths', 
      icon: Brain,
      description: 'Structured learning journeys'
    },
    { 
      id: 'progress' as TabType, 
      name: 'My Progress', 
      icon: TrendingUp,
      description: 'Track your learning journey'
    },
    { 
      id: 'bookmarks' as TabType, 
      name: 'Bookmarks', 
      icon: Star,
      description: 'Saved content and favorites'
    },
  ];

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    // Search functionality will be handled by the ContentLibrary component
    if (activeTab !== 'library') {
      setActiveTab('library');
    }
  };

  const isLoading = featuredLoading || trendingLoading || recentLoading || progressLoading || recommendationsLoading;

  return (
    <div className="space-y-8">
      {/* Header with Search */}
      <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-slate-900">Education Center</h1>
          <p className="text-slate-600 mt-2">
            Master options trading with comprehensive courses, tutorials, and expert insights
          </p>
        </div>
        
        <form onSubmit={handleSearch} className="flex gap-2 max-w-md">
          <Input
            placeholder="Search courses, articles, videos..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            icon={Search}
            className="min-w-64"
          />
          <Button type="submit" variant="outline">
            <Filter className="w-4 h-4" />
          </Button>
        </form>
      </div>

      {/* Quick Stats */}
      {progressData && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card className="p-4">
            <div className="flex items-center space-x-3">
              <div className="p-2 bg-blue-100 rounded-lg">
                <BookOpen className="w-6 h-6 text-blue-600" />
              </div>
              <div>
                <p className="text-sm text-slate-600">Total Content</p>
                <p className="text-xl font-bold text-slate-900">
                  {progressData.completion_stats.total_content}
                </p>
              </div>
            </div>
          </Card>
          
          <Card className="p-4">
            <div className="flex items-center space-x-3">
              <div className="p-2 bg-green-100 rounded-lg">
                <Award className="w-6 h-6 text-green-600" />
              </div>
              <div>
                <p className="text-sm text-slate-600">Completed</p>
                <p className="text-xl font-bold text-slate-900">
                  {progressData.completion_stats.completed_content}
                </p>
              </div>
            </div>
          </Card>
          
          <Card className="p-4">
            <div className="flex items-center space-x-3">
              <div className="p-2 bg-yellow-100 rounded-lg">
                <Play className="w-6 h-6 text-yellow-600" />
              </div>
              <div>
                <p className="text-sm text-slate-600">In Progress</p>
                <p className="text-xl font-bold text-slate-900">
                  {progressData.completion_stats.in_progress_content}
                </p>
              </div>
            </div>
          </Card>
          
          <Card className="p-4">
            <div className="flex items-center space-x-3">
              <div className="p-2 bg-purple-100 rounded-lg">
                <Clock className="w-6 h-6 text-purple-600" />
              </div>
              <div>
                <p className="text-sm text-slate-600">Hours Studied</p>
                <p className="text-xl font-bold text-slate-900">
                  {progressData.completion_stats.total_time_spent_hours.toFixed(1)}
                </p>
              </div>
            </div>
          </Card>
        </div>
      )}

      {/* Featured Content */}
      {featuredContent && featuredContent.length > 0 && (
        <div>
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-xl font-semibold text-slate-900">Featured Content</h2>
            <Button variant="outline" size="sm">View All</Button>
          </div>
          
          {featuredLoading ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              {[...Array(4)].map((_, i) => (
                <div key={i} className="animate-pulse">
                  <div className="h-48 bg-slate-200 rounded-lg mb-3"></div>
                  <div className="h-4 bg-slate-200 rounded mb-2"></div>
                  <div className="h-3 bg-slate-200 rounded"></div>
                </div>
              ))}
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              {featuredContent.slice(0, 4).map((content) => (
                <Card 
                  key={content.id} 
                  className="p-4 cursor-pointer hover:shadow-lg transition-shadow"
                  onClick={() => onContentSelect?.(content.id)}
                >
                  {content.thumbnail_url && (
                    <img
                      src={content.thumbnail_url}
                      alt={content.title}
                      className="w-full h-32 object-cover rounded-lg mb-3"
                    />
                  )}
                  <div className="space-y-2">
                    <div className="flex items-center gap-2">
                      <Badge variant="outline" className="text-xs">
                        {content.type}
                      </Badge>
                      <Badge variant="secondary" className="text-xs">
                        {content.difficulty}
                      </Badge>
                    </div>
                    <h3 className="font-medium text-slate-900 line-clamp-2">
                      {content.title}
                    </h3>
                    <p className="text-sm text-slate-600 line-clamp-2">
                      {content.description}
                    </p>
                    <div className="flex items-center justify-between text-xs text-slate-500">
                      <span>{content.duration_minutes}m</span>
                      <div className="flex items-center gap-1">
                        <Star className="w-3 h-3 fill-current text-yellow-500" />
                        <span>{content.rating_average.toFixed(1)}</span>
                      </div>
                    </div>
                  </div>
                </Card>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Main Navigation Tabs */}
      <div className="border-b border-slate-200">
        <nav className="flex space-x-8">
          {tabs.map((tab) => {
            const Icon = tab.icon;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center space-x-2 py-4 border-b-2 transition-colors ${
                  activeTab === tab.id
                    ? 'border-primary-500 text-primary-600'
                    : 'border-transparent text-slate-500 hover:text-slate-700 hover:border-slate-300'
                }`}
              >
                <Icon className="w-5 h-5" />
                <span className="font-medium">{tab.name}</span>
              </button>
            );
          })}
        </nav>
      </div>

      {/* Tab Content */}
      <div className="min-h-96">
        {isLoading && (
          <div className="flex justify-center items-center h-64">
            <LoadingSpinner size="lg" />
          </div>
        )}
        
        {!isLoading && (
          <>
            {activeTab === 'library' && (
              <ContentLibrary 
                onContentSelect={onContentSelect}
                searchQuery={searchQuery}
                featuredContent={featuredContent}
                trendingContent={trendingContent}
                recentContent={recentContent}
              />
            )}
            
            {activeTab === 'paths' && (
              <LearningPaths onPathSelect={(pathId) => console.log('Selected path:', pathId)} />
            )}
            
            {activeTab === 'progress' && (
              <MyProgress 
                progressData={progressData}
                onContentSelect={onContentSelect}
              />
            )}
            
            {activeTab === 'bookmarks' && (
              <Bookmarks onContentSelect={onContentSelect} />
            )}
          </>
        )}
      </div>

      {/* Recommendations Section */}
      {recommendations && (
        <Card className="p-6">
          <h3 className="text-lg font-semibold text-slate-900 mb-4">Recommended for You</h3>
          
          {recommendationsLoading ? (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {[...Array(3)].map((_, i) => (
                <div key={i} className="animate-pulse h-24 bg-slate-200 rounded-lg"></div>
              ))}
            </div>
          ) : (
            <div className="space-y-6">
              {recommendations.based_on_progress && recommendations.based_on_progress.length > 0 && (
                <div>
                  <h4 className="font-medium text-slate-900 mb-3">Continue Your Learning Journey</h4>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    {recommendations.based_on_progress.slice(0, 3).map((content) => (
                      <div
                        key={content.id}
                        className="flex items-center space-x-3 p-3 bg-slate-50 rounded-lg cursor-pointer hover:bg-slate-100"
                        onClick={() => onContentSelect?.(content.id)}
                      >
                        <div className="flex-shrink-0">
                          <div className="w-12 h-12 bg-primary-100 rounded-lg flex items-center justify-center">
                            <BookOpen className="w-6 h-6 text-primary-600" />
                          </div>
                        </div>
                        <div className="min-w-0">
                          <p className="font-medium text-slate-900 truncate">{content.title}</p>
                          <p className="text-sm text-slate-600">{content.type} • {content.duration_minutes}m</p>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </Card>
      )}
    </div>
  );
};

export default EducationDashboard;