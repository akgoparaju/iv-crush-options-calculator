import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Card } from '../ui/Card';
import { Button } from '../ui/Button';
import { Badge } from '../ui/Badge';
import { LoadingSpinner } from '../ui/LoadingSpinner';
import { ProgressResponse } from '../../types/education';
import { educationService } from '../../services/educationService';
import { 
  TrendingUp,
  Clock,
  CheckCircle,
  Play,
  BookOpen,
  Award,
  Calendar,
  Target,
  Brain,
  Star,
  BarChart3
} from 'lucide-react';

interface MyProgressProps {
  progressData?: ProgressResponse;
  onContentSelect?: (contentId: string) => void;
}

const MyProgress: React.FC<MyProgressProps> = ({ progressData, onContentSelect }) => {
  const [timeRange, setTimeRange] = useState<'week' | 'month' | 'all'>('month');

  // Get detailed progress if not provided
  const { data: detailedProgress, isLoading } = useQuery({
    queryKey: ['detailed-progress'],
    queryFn: () => educationService.getUserProgress(),
    enabled: !progressData,
  });

  const progress = progressData || detailedProgress;

  if (isLoading || !progress) {
    return (
      <div className="space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="animate-pulse h-24 bg-slate-200 rounded-lg"></div>
          ))}
        </div>
        <div className="animate-pulse h-64 bg-slate-200 rounded-lg"></div>
      </div>
    );
  }

  const completionPercentage = progress.completion_stats.total_content > 0 
    ? (progress.completion_stats.completed_content / progress.completion_stats.total_content) * 100 
    : 0;

  const recentProgress = progress.progress
    .filter(p => {
      const date = new Date(p.updated_at);
      const now = new Date();
      const daysAgo = (now.getTime() - date.getTime()) / (1000 * 60 * 60 * 24);
      
      switch (timeRange) {
        case 'week': return daysAgo <= 7;
        case 'month': return daysAgo <= 30;
        default: return true;
      }
    })
    .sort((a, b) => new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime());

  const completedContent = progress.progress.filter(p => p.progress_percent === 100);
  const inProgressContent = progress.progress.filter(p => p.progress_percent > 0 && p.progress_percent < 100);

  return (
    <div className="space-y-8">
      {/* Progress Overview */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card className="p-6">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-blue-100 rounded-lg">
              <BookOpen className="w-6 h-6 text-blue-600" />
            </div>
            <div>
              <p className="text-sm text-slate-600">Total Content</p>
              <p className="text-2xl font-bold text-slate-900">
                {progress.completion_stats.total_content}
              </p>
            </div>
          </div>
        </Card>
        
        <Card className="p-6">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-green-100 rounded-lg">
              <CheckCircle className="w-6 h-6 text-green-600" />
            </div>
            <div>
              <p className="text-sm text-slate-600">Completed</p>
              <p className="text-2xl font-bold text-slate-900">
                {progress.completion_stats.completed_content}
              </p>
              <p className="text-xs text-green-600">
                {completionPercentage.toFixed(1)}% complete
              </p>
            </div>
          </div>
        </Card>
        
        <Card className="p-6">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-yellow-100 rounded-lg">
              <Play className="w-6 h-6 text-yellow-600" />
            </div>
            <div>
              <p className="text-sm text-slate-600">In Progress</p>
              <p className="text-2xl font-bold text-slate-900">
                {progress.completion_stats.in_progress_content}
              </p>
            </div>
          </div>
        </Card>
        
        <Card className="p-6">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-purple-100 rounded-lg">
              <Clock className="w-6 h-6 text-purple-600" />
            </div>
            <div>
              <p className="text-sm text-slate-600">Study Time</p>
              <p className="text-2xl font-bold text-slate-900">
                {progress.completion_stats.total_time_spent_hours.toFixed(1)}h
              </p>
            </div>
          </div>
        </Card>
      </div>

      {/* Overall Progress Chart */}
      <Card className="p-6">
        <div className="flex items-center justify-between mb-6">
          <h3 className="text-lg font-semibold text-slate-900">Learning Progress</h3>
          <div className="text-right">
            <div className="text-2xl font-bold text-primary-600">{completionPercentage.toFixed(1)}%</div>
            <div className="text-sm text-slate-600">Overall Completion</div>
          </div>
        </div>
        
        <div className="space-y-4">
          <div className="w-full bg-slate-200 rounded-full h-4">
            <div 
              className="bg-gradient-to-r from-primary-500 to-primary-600 h-4 rounded-full transition-all duration-500"
              style={{ width: `${completionPercentage}%` }}
            />
          </div>
          
          <div className="flex justify-between text-sm">
            <span className="text-slate-600">
              {progress.completion_stats.completed_content} of {progress.completion_stats.total_content} completed
            </span>
            <span className="text-primary-600 font-medium">
              Keep learning!
            </span>
          </div>
        </div>
      </Card>

      {/* Recent Activity */}
      <Card className="p-6">
        <div className="flex items-center justify-between mb-6">
          <h3 className="text-lg font-semibold text-slate-900">Recent Activity</h3>
          <div className="flex items-center gap-2">
            <select
              value={timeRange}
              onChange={(e) => setTimeRange(e.target.value as 'week' | 'month' | 'all')}
              className="text-sm border border-slate-300 rounded px-3 py-1"
            >
              <option value="week">Last Week</option>
              <option value="month">Last Month</option>
              <option value="all">All Time</option>
            </select>
          </div>
        </div>

        {recentProgress.length === 0 ? (
          <div className="text-center py-8">
            <div className="text-slate-400 mb-4">
              <BarChart3 className="w-12 h-12 mx-auto" />
            </div>
            <h4 className="text-lg font-medium text-slate-900 mb-2">No recent activity</h4>
            <p className="text-slate-600">Start learning to see your progress here!</p>
          </div>
        ) : (
          <div className="space-y-4">
            {recentProgress.slice(0, 10).map((item) => (
              <div key={item.content_id} className="flex items-center justify-between p-4 bg-slate-50 rounded-lg">
                <div className="flex items-center space-x-3">
                  <div className="flex-shrink-0">
                    {item.progress_percent === 100 ? (
                      <CheckCircle className="w-6 h-6 text-green-600" />
                    ) : (
                      <div className="w-6 h-6 rounded-full border-2 border-primary-200 bg-white flex items-center justify-center">
                        <div 
                          className="w-3 h-3 rounded-full bg-primary-500"
                          style={{ 
                            transform: `scale(${item.progress_percent / 100})`,
                            opacity: Math.max(0.3, item.progress_percent / 100)
                          }}
                        />
                      </div>
                    )}
                  </div>
                  <div>
                    <p className="font-medium text-slate-900">
                      Content {item.content_id.substring(0, 8)}...
                    </p>
                    <div className="flex items-center gap-4 text-sm text-slate-600">
                      <span>{item.progress_percent}% complete</span>
                      <span>{item.time_spent_minutes}m studied</span>
                      <span>{new Date(item.updated_at).toLocaleDateString()}</span>
                    </div>
                    {item.notes && (
                      <p className="text-sm text-slate-500 italic mt-1">{item.notes}</p>
                    )}
                  </div>
                </div>
                <div className="flex items-center space-x-2">
                  {item.progress_percent === 100 && (
                    <Badge variant="success" className="text-xs">Completed</Badge>
                  )}
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => onContentSelect?.(item.content_id)}
                  >
                    {item.progress_percent === 100 ? 'Review' : 'Continue'}
                  </Button>
                </div>
              </div>
            ))}
          </div>
        )}
      </Card>

      {/* Learning Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Completed Content */}
        <Card className="p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-slate-900 flex items-center gap-2">
              <Award className="w-5 h-5 text-green-600" />
              Completed Content
            </h3>
            <Badge variant="success">{completedContent.length} items</Badge>
          </div>
          
          {completedContent.length === 0 ? (
            <div className="text-center py-6">
              <p className="text-slate-600">No completed content yet</p>
              <p className="text-sm text-slate-500">Keep learning to earn achievements!</p>
            </div>
          ) : (
            <div className="space-y-3">
              {completedContent.slice(0, 5).map((item) => (
                <div key={item.content_id} className="flex items-center justify-between p-3 bg-green-50 rounded-lg">
                  <div className="flex items-center space-x-3">
                    <CheckCircle className="w-5 h-5 text-green-600" />
                    <div>
                      <p className="font-medium text-slate-900">
                        Content {item.content_id.substring(0, 8)}...
                      </p>
                      <p className="text-sm text-slate-600">
                        Completed {item.completed_at ? new Date(item.completed_at).toLocaleDateString() : 'Recently'}
                      </p>
                    </div>
                  </div>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => onContentSelect?.(item.content_id)}
                  >
                    Review
                  </Button>
                </div>
              ))}
              {completedContent.length > 5 && (
                <div className="text-center">
                  <Button variant="outline" size="sm">
                    View All ({completedContent.length - 5} more)
                  </Button>
                </div>
              )}
            </div>
          )}
        </Card>

        {/* In Progress Content */}
        <Card className="p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-slate-900 flex items-center gap-2">
              <Play className="w-5 h-5 text-yellow-600" />
              Continue Learning
            </h3>
            <Badge variant="warning">{inProgressContent.length} items</Badge>
          </div>
          
          {inProgressContent.length === 0 ? (
            <div className="text-center py-6">
              <p className="text-slate-600">No content in progress</p>
              <p className="text-sm text-slate-500">Start learning to see your progress!</p>
            </div>
          ) : (
            <div className="space-y-3">
              {inProgressContent.slice(0, 5).map((item) => (
                <div key={item.content_id} className="flex items-center justify-between p-3 bg-yellow-50 rounded-lg">
                  <div className="flex items-center space-x-3">
                    <div className="w-5 h-5 rounded-full border-2 border-yellow-300 bg-white flex items-center justify-center">
                      <div 
                        className="w-2 h-2 rounded-full bg-yellow-500"
                        style={{ opacity: Math.max(0.5, item.progress_percent / 100) }}
                      />
                    </div>
                    <div>
                      <p className="font-medium text-slate-900">
                        Content {item.content_id.substring(0, 8)}...
                      </p>
                      <div className="flex items-center gap-2">
                        <div className="w-16 bg-slate-200 rounded-full h-1">
                          <div 
                            className="bg-yellow-500 h-1 rounded-full"
                            style={{ width: `${item.progress_percent}%` }}
                          />
                        </div>
                        <span className="text-sm text-slate-600">{item.progress_percent}%</span>
                      </div>
                    </div>
                  </div>
                  <Button
                    size="sm"
                    onClick={() => onContentSelect?.(item.content_id)}
                  >
                    Continue
                  </Button>
                </div>
              ))}
              {inProgressContent.length > 5 && (
                <div className="text-center">
                  <Button variant="outline" size="sm">
                    View All ({inProgressContent.length - 5} more)
                  </Button>
                </div>
              )}
            </div>
          )}
        </Card>
      </div>

      {/* Learning Achievements */}
      <Card className="p-6 bg-gradient-to-r from-yellow-50 to-orange-50">
        <div className="text-center">
          <div className="w-16 h-16 bg-yellow-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <Award className="w-8 h-8 text-yellow-600" />
          </div>
          <h3 className="text-lg font-semibold text-slate-900 mb-2">Learning Achievements</h3>
          <div className="flex items-center justify-center gap-6 text-sm">
            <div className="text-center">
              <div className="text-2xl font-bold text-yellow-600">{completedContent.length}</div>
              <div className="text-slate-600">Completed</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-blue-600">
                {progress.completion_stats.total_time_spent_hours.toFixed(0)}
              </div>
              <div className="text-slate-600">Hours</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-green-600">
                {Math.floor(completionPercentage / 10)}
              </div>
              <div className="text-slate-600">Milestones</div>
            </div>
          </div>
        </div>
      </Card>
    </div>
  );
};

export default MyProgress;