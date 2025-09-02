import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Card } from '../ui/Card';
import { Button } from '../ui/Button';
import { Badge } from '../ui/Badge';
import { Input } from '../ui/Input';
import { LoadingSpinner } from '../ui/LoadingSpinner';
import { LearningPath, DifficultyLevel, ContentCategory } from '../../types/education';
import { educationService } from '../../services/educationService';
import { 
  Brain,
  Search,
  Clock,
  Users,
  Play,
  CheckCircle,
  Circle,
  Award,
  TrendingUp,
  BookOpen,
  Target,
  ChevronRight,
  Star
} from 'lucide-react';

interface LearningPathsProps {
  onPathSelect?: (pathId: string) => void;
}

const LearningPaths: React.FC<LearningPathsProps> = ({ onPathSelect }) => {
  const [selectedCategory, setSelectedCategory] = useState<ContentCategory | 'all'>('all');
  const [selectedDifficulty, setSelectedDifficulty] = useState<DifficultyLevel | 'all'>('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [expandedPath, setExpandedPath] = useState<string | null>(null);

  const queryClient = useQueryClient();

  // Fetch learning paths
  const { data: pathsData, isLoading } = useQuery({
    queryKey: ['learning-paths', selectedCategory, selectedDifficulty],
    queryFn: () => educationService.getLearningPaths(
      selectedCategory === 'all' ? undefined : selectedCategory,
      selectedDifficulty === 'all' ? undefined : selectedDifficulty
    ),
  });

  // Enroll in path mutation
  const enrollMutation = useMutation({
    mutationFn: (pathId: string) => educationService.enrollInLearningPath(pathId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['learning-paths'] });
    },
  });

  const categories: Array<{ id: ContentCategory | 'all'; name: string }> = [
    { id: 'all', name: 'All Categories' },
    { id: 'options_basics', name: 'Options Basics' },
    { id: 'strategies', name: 'Trading Strategies' },
    { id: 'risk_management', name: 'Risk Management' },
    { id: 'technical_analysis', name: 'Technical Analysis' },
    { id: 'portfolio_management', name: 'Portfolio Management' },
    { id: 'earnings_trades', name: 'Earnings Trades' },
  ];

  const difficulties: Array<{ id: DifficultyLevel | 'all'; name: string; color: string }> = [
    { id: 'all', name: 'All Levels', color: 'gray' },
    { id: 'beginner', name: 'Beginner', color: 'green' },
    { id: 'intermediate', name: 'Intermediate', color: 'yellow' },
    { id: 'advanced', name: 'Advanced', color: 'orange' },
    { id: 'expert', name: 'Expert', color: 'red' },
  ];

  const filteredPaths = pathsData?.paths.filter(path =>
    path.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
    path.description.toLowerCase().includes(searchQuery.toLowerCase())
  ) || [];

  const getDifficultyColor = (difficulty: DifficultyLevel) => {
    const level = difficulties.find(d => d.id === difficulty);
    return level?.color || 'gray';
  };

  const getProgressPercentage = (path: LearningPath): number => {
    return path.completion_rate || 0;
  };

  if (isLoading) {
    return (
      <div className="space-y-4">
        {[...Array(6)].map((_, i) => (
          <div key={i} className="animate-pulse">
            <div className="h-32 bg-slate-200 rounded-lg"></div>
          </div>
        ))}
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="text-center">
        <div className="flex items-center justify-center gap-3 mb-4">
          <div className="p-3 bg-primary-100 rounded-lg">
            <Brain className="w-8 h-8 text-primary-600" />
          </div>
          <div>
            <h2 className="text-2xl font-bold text-slate-900">Learning Paths</h2>
            <p className="text-slate-600">Structured journeys to master options trading</p>
          </div>
        </div>
      </div>

      {/* Filters */}
      <div className="space-y-4">
        <div className="flex flex-col sm:flex-row gap-4">
          <div className="flex-1">
            <Input
              placeholder="Search learning paths..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              icon={Search}
            />
          </div>
        </div>

        <div className="flex flex-wrap gap-4">
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-2">Category</label>
            <select
              value={selectedCategory}
              onChange={(e) => setSelectedCategory(e.target.value as ContentCategory | 'all')}
              className="border border-slate-300 rounded px-3 py-2 text-sm"
            >
              {categories.map(category => (
                <option key={category.id} value={category.id}>
                  {category.name}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-700 mb-2">Difficulty</label>
            <select
              value={selectedDifficulty}
              onChange={(e) => setSelectedDifficulty(e.target.value as DifficultyLevel | 'all')}
              className="border border-slate-300 rounded px-3 py-2 text-sm"
            >
              {difficulties.map(difficulty => (
                <option key={difficulty.id} value={difficulty.id}>
                  {difficulty.name}
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* Learning Paths Grid */}
      {filteredPaths.length === 0 ? (
        <Card className="p-12 text-center">
          <div className="text-slate-400 mb-4">
            <Brain className="w-12 h-12 mx-auto" />
          </div>
          <h3 className="text-lg font-medium text-slate-900 mb-2">No learning paths found</h3>
          <p className="text-slate-600">
            Try adjusting your search or filter criteria.
          </p>
        </Card>
      ) : (
        <div className="space-y-6">
          {filteredPaths.map((path) => {
            const isExpanded = expandedPath === path.id;
            const progressPercentage = getProgressPercentage(path);
            const isEnrolled = progressPercentage > 0;

            return (
              <Card key={path.id} className="overflow-hidden">
                <div className="p-6">
                  {/* Path Header */}
                  <div className="flex flex-col lg:flex-row lg:items-start gap-4">
                    {path.thumbnail_url ? (
                      <img
                        src={path.thumbnail_url}
                        alt={path.title}
                        className="w-full lg:w-48 h-32 object-cover rounded-lg"
                      />
                    ) : (
                      <div className="w-full lg:w-48 h-32 bg-gradient-to-br from-primary-100 to-primary-200 rounded-lg flex items-center justify-center">
                        <Brain className="w-12 h-12 text-primary-600" />
                      </div>
                    )}

                    <div className="flex-1">
                      <div className="flex items-start justify-between mb-3">
                        <div>
                          <div className="flex items-center gap-2 mb-2">
                            <Badge 
                              variant="outline" 
                              className={`bg-${getDifficultyColor(path.difficulty)}-100 text-${getDifficultyColor(path.difficulty)}-800`}
                            >
                              {path.difficulty}
                            </Badge>
                            <Badge variant="secondary" className="text-xs">
                              {path.category.replace('_', ' ')}
                            </Badge>
                          </div>
                          <h3 className="text-xl font-bold text-slate-900 mb-2">{path.title}</h3>
                          <p className="text-slate-600 mb-3">{path.description}</p>
                        </div>
                        
                        {isEnrolled && (
                          <div className="text-right">
                            <div className="text-sm text-slate-600 mb-1">Progress</div>
                            <div className="text-2xl font-bold text-primary-600">
                              {progressPercentage}%
                            </div>
                          </div>
                        )}
                      </div>

                      <div className="flex flex-wrap items-center gap-4 mb-4 text-sm text-slate-600">
                        <div className="flex items-center gap-1">
                          <BookOpen className="w-4 h-4" />
                          {path.content_count} lessons
                        </div>
                        <div className="flex items-center gap-1">
                          <Clock className="w-4 h-4" />
                          {path.estimated_hours}h total
                        </div>
                        <div className="flex items-center gap-1">
                          <Target className="w-4 h-4" />
                          Structured learning
                        </div>
                      </div>

                      {isEnrolled && progressPercentage > 0 && (
                        <div className="mb-4">
                          <div className="w-full bg-slate-200 rounded-full h-2">
                            <div 
                              className="bg-primary-600 h-2 rounded-full transition-all duration-300"
                              style={{ width: `${progressPercentage}%` }}
                            />
                          </div>
                        </div>
                      )}

                      <div className="flex items-center gap-3">
                        {isEnrolled ? (
                          <Button
                            onClick={() => onPathSelect?.(path.id)}
                            className="flex items-center gap-2"
                          >
                            <Play className="w-4 h-4" />
                            Continue Learning
                          </Button>
                        ) : (
                          <Button
                            onClick={() => enrollMutation.mutate(path.id)}
                            loading={enrollMutation.isPending}
                            className="flex items-center gap-2"
                          >
                            <Play className="w-4 h-4" />
                            Start Learning
                          </Button>
                        )}
                        
                        <Button
                          variant="outline"
                          onClick={() => setExpandedPath(isExpanded ? null : path.id)}
                          className="flex items-center gap-2"
                        >
                          View Curriculum
                          <ChevronRight className={`w-4 h-4 transition-transform ${isExpanded ? 'rotate-90' : ''}`} />
                        </Button>
                      </div>
                    </div>
                  </div>

                  {/* Curriculum (Expanded) */}
                  {isExpanded && (
                    <div className="mt-6 pt-6 border-t border-slate-200">
                      <h4 className="font-semibold text-slate-900 mb-4">Learning Path Curriculum</h4>
                      <div className="space-y-3">
                        {path.content_items.map((item, index) => (
                          <div key={item.content_id} className="flex items-center space-x-3 p-3 bg-slate-50 rounded-lg">
                            <div className="flex-shrink-0">
                              {item.is_completed ? (
                                <CheckCircle className="w-5 h-5 text-green-600" />
                              ) : (
                                <Circle className="w-5 h-5 text-slate-400" />
                              )}
                            </div>
                            <div className="flex-1">
                              <div className="flex items-center gap-2">
                                <span className="text-sm font-medium text-slate-900">
                                  Step {item.order}: Content Item {item.content_id.substring(0, 8)}
                                </span>
                                {item.is_required && (
                                  <Badge variant="warning" className="text-xs">Required</Badge>
                                )}
                              </div>
                            </div>
                            <div className="text-xs text-slate-500">
                              ~15 min
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </Card>
            );
          })}
        </div>
      )}

      {/* Stats Summary */}
      <Card className="p-6 bg-gradient-to-r from-primary-50 to-blue-50">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="text-center">
            <div className="w-12 h-12 bg-primary-100 rounded-lg flex items-center justify-center mx-auto mb-3">
              <Brain className="w-6 h-6 text-primary-600" />
            </div>
            <div className="text-2xl font-bold text-slate-900">
              {pathsData?.total_count || 0}
            </div>
            <div className="text-sm text-slate-600">Learning Paths</div>
          </div>
          
          <div className="text-center">
            <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center mx-auto mb-3">
              <Award className="w-6 h-6 text-green-600" />
            </div>
            <div className="text-2xl font-bold text-slate-900">
              {filteredPaths.filter(p => getProgressPercentage(p) === 100).length}
            </div>
            <div className="text-sm text-slate-600">Completed</div>
          </div>
          
          <div className="text-center">
            <div className="w-12 h-12 bg-yellow-100 rounded-lg flex items-center justify-center mx-auto mb-3">
              <TrendingUp className="w-6 h-6 text-yellow-600" />
            </div>
            <div className="text-2xl font-bold text-slate-900">
              {filteredPaths.filter(p => getProgressPercentage(p) > 0 && getProgressPercentage(p) < 100).length}
            </div>
            <div className="text-sm text-slate-600">In Progress</div>
          </div>
        </div>
      </Card>
    </div>
  );
};

export default LearningPaths;