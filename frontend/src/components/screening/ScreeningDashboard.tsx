import React, { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Card } from '../ui/Card';
import { Button } from '../ui/Button';
import { LoadingSpinner } from '../ui/LoadingSpinner';
import { Badge } from '../ui/Badge';
import { screeningService } from '../../services/screeningService';
import { formatCurrency, formatPercentage } from '../../utils/formatters';
import {
  Search,
  Filter,
  TrendingUp,
  TrendingDown,
  Activity,
  Calendar,
  Eye,
  Plus,
  BarChart3,
  Zap,
  Target,
  AlertTriangle
} from 'lucide-react';

import MarketOverview from './MarketOverview';
import ScreeningFilters from './ScreeningFilters';
import ScreeningResults from './ScreeningResults';
import ScreeningTemplates from './ScreeningTemplates';
import WatchlistPanel from './WatchlistPanel';

interface ScreeningDashboardProps {
  onSymbolSelect?: (symbol: string) => void;
}

const ScreeningDashboard: React.FC<ScreeningDashboardProps> = ({ onSymbolSelect }) => {
  const [activeTab, setActiveTab] = useState<'screening' | 'market' | 'watchlist' | 'insights'>('screening');
  const [showFilters, setShowFilters] = useState(false);
  const [selectedTemplate, setSelectedTemplate] = useState<string | null>(null);
  const [screeningResults, setScreeningResults] = useState<any>(null);
  const [isRunningScreening, setIsRunningScreening] = useState(false);

  const queryClient = useQueryClient();

  // Fetch market overview
  const {
    data: marketOverview,
    isLoading: marketLoading,
    error: marketError,
  } = useQuery({
    queryKey: ['market-overview'],
    queryFn: screeningService.getMarketOverview,
    refetchInterval: 60000, // Refetch every minute
  });

  // Fetch popular screening templates
  const {
    data: popularTemplates,
    isLoading: templatesLoading,
  } = useQuery({
    queryKey: ['popular-templates'],
    queryFn: () => screeningService.getPopularScreenings(6),
  });

  // Fetch user watchlists
  const {
    data: watchlists,
    isLoading: watchlistsLoading,
  } = useQuery({
    queryKey: ['watchlists'],
    queryFn: screeningService.getWatchlists,
  });

  // Fetch screening insights
  const {
    data: insights,
    isLoading: insightsLoading,
  } = useQuery({
    queryKey: ['screening-insights'],
    queryFn: () => screeningService.getScreeningInsights('7D'),
    refetchInterval: 5 * 60 * 1000, // Refetch every 5 minutes
  });

  const handleRunScreening = async (criteria: any) => {
    setIsRunningScreening(true);
    try {
      const results = await screeningService.runScreening({
        criteria,
        limit: 100,
        includeGreeks: true,
        includeStrategies: true,
        includeTechnicals: true,
        includeFundamentals: true,
      });
      setScreeningResults(results);
    } catch (error) {
      console.error('Error running screening:', error);
    } finally {
      setIsRunningScreening(false);
    }
  };

  const tabs = [
    { 
      id: 'screening', 
      name: 'Stock Screening', 
      icon: Search, 
      description: 'Find trading opportunities' 
    },
    { 
      id: 'market', 
      name: 'Market Overview', 
      icon: BarChart3, 
      description: 'Market insights & trends' 
    },
    { 
      id: 'watchlist', 
      name: 'Watchlists', 
      icon: Eye, 
      description: 'Track favorite stocks' 
    },
    { 
      id: 'insights', 
      name: 'AI Insights', 
      icon: Zap, 
      description: 'Trading recommendations' 
    },
  ] as const;

  const quickStats = marketOverview ? [
    {
      label: 'VIX',
      value: marketOverview.volatilityMetrics.vix.toFixed(2),
      change: marketOverview.volatilityMetrics.vixChange,
      icon: Activity,
    },
    {
      label: 'Market Gainers',
      value: marketOverview.topMovers.gainers.length.toString(),
      change: 0,
      icon: TrendingUp,
    },
    {
      label: 'Earnings Today',
      value: marketOverview.earnings.filter(e => 
        new Date(e.date).toDateString() === new Date().toDateString()
      ).length.toString(),
      change: 0,
      icon: Calendar,
    },
    {
      label: 'High IV Stocks',
      value: marketOverview.topMovers.active.filter(s => s.ivRank > 75).length.toString(),
      change: 0,
      icon: Target,
    },
  ] : [];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Market Screening</h1>
          <p className="text-slate-600">
            Discover trading opportunities with advanced screening tools
          </p>
        </div>
        <div className="flex items-center space-x-3">
          <Button
            variant="outline"
            onClick={() => setShowFilters(true)}
            className="inline-flex items-center"
          >
            <Filter className="w-4 h-4 mr-2" />
            Create Screen
          </Button>
          <Button
            onClick={() => setActiveTab('screening')}
            className="inline-flex items-center"
          >
            <Plus className="w-4 h-4 mr-2" />
            New Screening
          </Button>
        </div>
      </div>

      {/* Quick Stats */}
      {quickStats.length > 0 && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {quickStats.map((stat, index) => {
            const Icon = stat.icon;
            return (
              <Card key={index} className="p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-slate-600">{stat.label}</p>
                    <p className="text-2xl font-bold text-slate-900">{stat.value}</p>
                    {stat.change !== 0 && (
                      <div className={`flex items-center text-sm ${
                        stat.change > 0 ? 'text-green-600' : 'text-red-600'
                      }`}>
                        {stat.change > 0 ? (
                          <TrendingUp className="w-3 h-3 mr-1" />
                        ) : (
                          <TrendingDown className="w-3 h-3 mr-1" />
                        )}
                        {formatPercentage(Math.abs(stat.change))}
                      </div>
                    )}
                  </div>
                  <div className="p-3 bg-primary-100 rounded-lg">
                    <Icon className="w-5 h-5 text-primary-600" />
                  </div>
                </div>
              </Card>
            );
          })}
        </div>
      )}

      {/* Tab Navigation */}
      <div className="border-b border-slate-200">
        <nav className="-mb-px flex space-x-8">
          {tabs.map((tab) => {
            const Icon = tab.icon;
            const isActive = activeTab === tab.id;
            
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`group py-4 px-1 border-b-2 font-medium text-sm inline-flex items-center ${
                  isActive
                    ? 'border-primary-500 text-primary-600'
                    : 'border-transparent text-slate-500 hover:text-slate-700 hover:border-slate-300'
                }`}
              >
                <Icon className="w-5 h-5 mr-3" />
                <div className="text-left">
                  <div>{tab.name}</div>
                  <div className="text-xs text-slate-400 group-hover:text-slate-500">
                    {tab.description}
                  </div>
                </div>
              </button>
            );
          })}
        </nav>
      </div>

      {/* Tab Content */}
      {activeTab === 'screening' && (
        <div className="grid grid-cols-1 xl:grid-cols-4 gap-6">
          {/* Screening Templates */}
          <div className="xl:col-span-1">
            <Card className="p-6">
              <h3 className="text-lg font-semibold text-slate-900 mb-4">Popular Screens</h3>
              {templatesLoading ? (
                <div className="flex justify-center py-8">
                  <LoadingSpinner />
                </div>
              ) : popularTemplates && popularTemplates.length > 0 ? (
                <div className="space-y-3">
                  {popularTemplates.map((template) => (
                    <div
                      key={template.id}
                      className={`p-3 rounded-lg border cursor-pointer transition-colors ${
                        selectedTemplate === template.id
                          ? 'border-primary-300 bg-primary-50'
                          : 'border-slate-200 hover:border-slate-300 hover:bg-slate-50'
                      }`}
                      onClick={() => setSelectedTemplate(template.id)}
                    >
                      <div className="flex items-center justify-between mb-2">
                        <h4 className="font-medium text-slate-900 text-sm">{template.name}</h4>
                        <Badge variant="outline" className="text-xs">
                          {template.category.replace('_', ' ')}
                        </Badge>
                      </div>
                      <p className="text-xs text-slate-600 mb-2">{template.description}</p>
                      <div className="flex items-center justify-between">
                        <span className="text-xs text-slate-500">
                          {template.popularity} users
                        </span>
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={(e) => {
                            e.stopPropagation();
                            handleRunScreening(template.criteria);
                          }}
                          disabled={isRunningScreening}
                        >
                          Run
                        </Button>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-slate-600 text-sm">No templates available</p>
              )}

              <div className="mt-4 pt-4 border-t border-slate-200">
                <Button
                  variant="outline"
                  onClick={() => setShowFilters(true)}
                  className="w-full"
                >
                  <Plus className="w-4 h-4 mr-2" />
                  Create Custom Screen
                </Button>
              </div>
            </Card>
          </div>

          {/* Screening Results */}
          <div className="xl:col-span-3">
            {isRunningScreening ? (
              <Card className="p-8">
                <div className="flex flex-col items-center justify-center space-y-4">
                  <LoadingSpinner size="lg" />
                  <p className="text-slate-600">Running screening analysis...</p>
                </div>
              </Card>
            ) : screeningResults ? (
              <ScreeningResults
                results={screeningResults}
                onSymbolSelect={onSymbolSelect}
              />
            ) : (
              <Card className="p-8">
                <div className="text-center">
                  <Search className="w-12 h-12 text-slate-400 mx-auto mb-4" />
                  <h3 className="text-lg font-semibold text-slate-900 mb-2">
                    Ready to Find Trading Opportunities?
                  </h3>
                  <p className="text-slate-600 mb-6">
                    Select a popular screening template or create your own custom screen to discover potential trades.
                  </p>
                  <div className="flex justify-center space-x-3">
                    <Button
                      variant="outline"
                      onClick={() => setShowFilters(true)}
                    >
                      Create Custom Screen
                    </Button>
                    {popularTemplates && popularTemplates.length > 0 && (
                      <Button
                        onClick={() => handleRunScreening(popularTemplates[0].criteria)}
                      >
                        Try Popular Screen
                      </Button>
                    )}
                  </div>
                </div>
              </Card>
            )}
          </div>
        </div>
      )}

      {activeTab === 'market' && (
        <div>
          {marketLoading ? (
            <div className="flex justify-center items-center h-64">
              <LoadingSpinner size="lg" />
            </div>
          ) : marketError ? (
            <Card className="p-6">
              <div className="text-center">
                <div className="text-red-500 mb-4">❌</div>
                <h3 className="text-lg font-semibold text-slate-900 mb-2">
                  Failed to load market data
                </h3>
                <p className="text-slate-600">
                  There was an error loading market information. Please try again.
                </p>
              </div>
            </Card>
          ) : marketOverview ? (
            <MarketOverview data={marketOverview} onSymbolSelect={onSymbolSelect} />
          ) : null}
        </div>
      )}

      {activeTab === 'watchlist' && (
        <div>
          {watchlistsLoading ? (
            <div className="flex justify-center items-center h-64">
              <LoadingSpinner size="lg" />
            </div>
          ) : (
            <WatchlistPanel 
              watchlists={watchlists || []} 
              onSymbolSelect={onSymbolSelect}
            />
          )}
        </div>
      )}

      {activeTab === 'insights' && (
        <div>
          {insightsLoading ? (
            <div className="flex justify-center items-center h-64">
              <LoadingSpinner size="lg" />
            </div>
          ) : insights ? (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Market Insights */}
              <Card className="p-6">
                <h3 className="text-lg font-semibold text-slate-900 mb-4">Market Insights</h3>
                <div className="space-y-4">
                  {insights.insights.map((insight, index) => (
                    <div key={index} className="flex items-start space-x-3">
                      <div className={`flex-shrink-0 p-2 rounded-lg ${
                        insight.type === 'opportunity' ? 'bg-green-100' :
                        insight.type === 'warning' ? 'bg-red-100' :
                        insight.type === 'trend' ? 'bg-blue-100' : 'bg-yellow-100'
                      }`}>
                        {insight.type === 'opportunity' ? (
                          <Target className="w-4 h-4 text-green-600" />
                        ) : insight.type === 'warning' ? (
                          <AlertTriangle className="w-4 h-4 text-red-600" />
                        ) : insight.type === 'trend' ? (
                          <TrendingUp className="w-4 h-4 text-blue-600" />
                        ) : (
                          <Zap className="w-4 h-4 text-yellow-600" />
                        )}
                      </div>
                      <div className="flex-1">
                        <h4 className="font-medium text-slate-900 mb-1">{insight.title}</h4>
                        <p className="text-sm text-slate-600 mb-2">{insight.description}</p>
                        <div className="flex items-center justify-between">
                          <Badge 
                            variant={insight.confidence > 80 ? 'success' : insight.confidence > 60 ? 'warning' : 'secondary'}
                            className="text-xs"
                          >
                            {insight.confidence}% confidence
                          </Badge>
                          {insight.symbols && insight.symbols.length > 0 && (
                            <div className="flex items-center space-x-1">
                              {insight.symbols.slice(0, 3).map((symbol) => (
                                <Badge key={symbol} variant="outline" className="text-xs">
                                  {symbol}
                                </Badge>
                              ))}
                              {insight.symbols.length > 3 && (
                                <Badge variant="outline" className="text-xs">
                                  +{insight.symbols.length - 3}
                                </Badge>
                              )}
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </Card>

              {/* Trading Recommendations */}
              <Card className="p-6">
                <h3 className="text-lg font-semibold text-slate-900 mb-4">Trading Recommendations</h3>
                <div className="space-y-4">
                  {insights.recommendations.map((rec, index) => (
                    <div key={index} className="border border-slate-200 rounded-lg p-4">
                      <div className="flex items-center justify-between mb-2">
                        <div className="flex items-center space-x-2">
                          <Badge 
                            variant={rec.action === 'trade' ? 'success' : rec.action === 'watch' ? 'warning' : 'secondary'}
                          >
                            {rec.action.toUpperCase()}
                          </Badge>
                          <span className="font-medium text-slate-900">{rec.symbol}</span>
                          {rec.strategy && (
                            <Badge variant="outline" className="text-xs">
                              {rec.strategy}
                            </Badge>
                          )}
                        </div>
                        <Badge variant={
                          rec.priority === 'high' ? 'destructive' :
                          rec.priority === 'medium' ? 'warning' : 'secondary'
                        } className="text-xs">
                          {rec.priority} priority
                        </Badge>
                      </div>
                      <p className="text-sm text-slate-600">{rec.reasoning}</p>
                      <div className="mt-3 flex space-x-2">
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => onSymbolSelect?.(rec.symbol)}
                        >
                          Analyze
                        </Button>
                        <Button size="sm" variant="outline">
                          Add to Watchlist
                        </Button>
                      </div>
                    </div>
                  ))}
                </div>
              </Card>
            </div>
          ) : (
            <Card className="p-8">
              <div className="text-center">
                <Zap className="w-12 h-12 text-slate-400 mx-auto mb-4" />
                <h3 className="text-lg font-semibold text-slate-900 mb-2">
                  No insights available
                </h3>
                <p className="text-slate-600">
                  AI insights will appear here when market conditions provide actionable opportunities.
                </p>
              </div>
            </Card>
          )}
        </div>
      )}

      {/* Screening Filters Modal */}
      {showFilters && (
        <ScreeningFilters
          onClose={() => setShowFilters(false)}
          onRunScreening={handleRunScreening}
          isRunning={isRunningScreening}
        />
      )}
    </div>
  );
};

export default ScreeningDashboard;