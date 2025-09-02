import React, { useState } from 'react';
import { Card } from '../ui/Card';
import { Badge } from '../ui/Badge';
import { Button } from '../ui/Button';
import { formatCurrency, formatPercentage } from '../../utils/formatters';
import { ScreeningResponse } from '../../types/screening';
import { Eye, TrendingUp, TrendingDown, Target, BarChart3, Download } from 'lucide-react';

interface ScreeningResultsProps {
  results: ScreeningResponse;
  onSymbolSelect?: (symbol: string) => void;
}

const ScreeningResults: React.FC<ScreeningResultsProps> = ({ results, onSymbolSelect }) => {
  const [sortBy, setSortBy] = useState<'score' | 'price' | 'volume' | 'iv'>('score');
  const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>('desc');

  const sortedResults = [...results.results].sort((a, b) => {
    const multiplier = sortDirection === 'desc' ? -1 : 1;
    switch (sortBy) {
      case 'score':
        return (a.score - b.score) * multiplier;
      case 'price':
        return (a.price - b.price) * multiplier;
      case 'volume':
        return (a.volume - b.volume) * multiplier;
      case 'iv':
        return (a.impliedVolatility - b.impliedVolatility) * multiplier;
      default:
        return 0;
    }
  });

  const handleSort = (field: typeof sortBy) => {
    if (sortBy === field) {
      setSortDirection(sortDirection === 'desc' ? 'asc' : 'desc');
    } else {
      setSortBy(field);
      setSortDirection('desc');
    }
  };

  const getScoreColor = (score: number) => {
    if (score >= 80) return 'text-green-600 bg-green-50';
    if (score >= 60) return 'text-yellow-600 bg-yellow-50';
    return 'text-red-600 bg-red-50';
  };

  return (
    <div className="space-y-6">
      {/* Results Summary */}
      <Card className="p-6">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h3 className="text-lg font-semibold text-slate-900">Screening Results</h3>
            <p className="text-sm text-slate-600">
              {results.totalCount} symbols found • Executed in {results.executionTime.toFixed(2)}ms
            </p>
          </div>
          <div className="flex items-center space-x-3">
            <Button variant="outline" size="sm">
              <Download className="w-4 h-4 mr-2" />
              Export
            </Button>
            <Badge variant="secondary">
              Page {results.page} of {Math.ceil(results.totalCount / results.limit)}
            </Badge>
          </div>
        </div>

        {/* Summary Stats */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="p-3 bg-slate-50 rounded-lg">
            <p className="text-sm text-slate-600">Avg Score</p>
            <p className="text-lg font-semibold text-slate-900">
              {results.summary.averageScore.toFixed(1)}
            </p>
          </div>
          <div className="p-3 bg-slate-50 rounded-lg">
            <p className="text-sm text-slate-600">Top Sector</p>
            <p className="text-lg font-semibold text-slate-900">
              {results.summary.topSector}
            </p>
          </div>
          <div className="p-3 bg-slate-50 rounded-lg">
            <p className="text-sm text-slate-600">Avg IV</p>
            <p className="text-lg font-semibold text-slate-900">
              {formatPercentage(results.summary.avgImpliedVolatility)}
            </p>
          </div>
          <div className="p-3 bg-slate-50 rounded-lg">
            <p className="text-sm text-slate-600">Earnings Soon</p>
            <p className="text-lg font-semibold text-slate-900">
              {results.summary.upcomingEarnings}
            </p>
          </div>
        </div>
      </Card>

      {/* Results Table */}
      <Card className="overflow-hidden">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-slate-200">
            <thead className="bg-slate-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">
                  Symbol
                </th>
                <th 
                  className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider cursor-pointer hover:text-slate-700"
                  onClick={() => handleSort('score')}
                >
                  Score {sortBy === 'score' && (sortDirection === 'desc' ? '↓' : '↑')}
                </th>
                <th 
                  className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider cursor-pointer hover:text-slate-700"
                  onClick={() => handleSort('price')}
                >
                  Price {sortBy === 'price' && (sortDirection === 'desc' ? '↓' : '↑')}
                </th>
                <th 
                  className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider cursor-pointer hover:text-slate-700"
                  onClick={() => handleSort('iv')}
                >
                  IV {sortBy === 'iv' && (sortDirection === 'desc' ? '↓' : '↑')}
                </th>
                <th 
                  className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider cursor-pointer hover:text-slate-700"
                  onClick={() => handleSort('volume')}
                >
                  Volume {sortBy === 'volume' && (sortDirection === 'desc' ? '↓' : '↑')}
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">
                  Top Strategy
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-slate-200">
              {sortedResults.map((result) => (
                <tr key={result.symbol} className="hover:bg-slate-50">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div>
                      <div className="flex items-center space-x-2">
                        <span className="text-sm font-medium text-slate-900">{result.symbol}</span>
                        {result.changePercent >= 0 ? (
                          <TrendingUp className="w-3 h-3 text-green-500" />
                        ) : (
                          <TrendingDown className="w-3 h-3 text-red-500" />
                        )}
                      </div>
                      <div className="text-sm text-slate-500 truncate max-w-32">{result.name}</div>
                      <div className="flex items-center space-x-1 mt-1">
                        <Badge variant="outline" className="text-xs">
                          {result.sector}
                        </Badge>
                        {result.daysToEarnings !== undefined && result.daysToEarnings <= 7 && (
                          <Badge variant="warning" className="text-xs">
                            Earnings {result.daysToEarnings}d
                          </Badge>
                        )}
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getScoreColor(result.score)}`}>
                      {result.score.toFixed(1)}
                    </div>
                    <div className="text-xs text-slate-500 mt-1">
                      Rank #{result.rank}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm font-medium text-slate-900">
                      {formatCurrency(result.price)}
                    </div>
                    <div className={`text-xs ${result.changePercent >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                      {result.changePercent >= 0 ? '+' : ''}{formatPercentage(result.changePercent)}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm text-slate-900">
                      {formatPercentage(result.impliedVolatility)}
                    </div>
                    <div className="text-xs text-slate-500">
                      Rank: {result.ivRank.toFixed(0)}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm text-slate-900">
                      {(result.volume / 1000000).toFixed(1)}M
                    </div>
                    <div className="text-xs text-slate-500">
                      Options: {(result.optionsVolume / 1000).toFixed(0)}K
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    {result.strategies && result.strategies.length > 0 ? (
                      <div>
                        <Badge 
                          variant={
                            result.strategies[0].confidence === 'high' ? 'success' :
                            result.strategies[0].confidence === 'medium' ? 'warning' : 'secondary'
                          }
                          className="text-xs"
                        >
                          {result.strategies[0].strategy.replace('_', ' ')}
                        </Badge>
                        <div className="text-xs text-slate-500 mt-1">
                          Score: {result.strategies[0].score.toFixed(1)}
                        </div>
                      </div>
                    ) : (
                      <span className="text-xs text-slate-400">No strategies</span>
                    )}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                    <div className="flex items-center space-x-2">
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={() => onSymbolSelect?.(result.symbol)}
                        className="p-1"
                      >
                        <Eye className="w-4 h-4" />
                      </Button>
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => onSymbolSelect?.(result.symbol)}
                      >
                        Analyze
                      </Button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        {results.totalCount > results.limit && (
          <div className="bg-white px-4 py-3 border-t border-slate-200 sm:px-6">
            <div className="flex items-center justify-between">
              <div className="text-sm text-slate-700">
                Showing <span className="font-medium">{((results.page - 1) * results.limit) + 1}</span> to{' '}
                <span className="font-medium">
                  {Math.min(results.page * results.limit, results.totalCount)}
                </span>{' '}
                of <span className="font-medium">{results.totalCount}</span> results
              </div>
              <div className="flex items-center space-x-2">
                <Button 
                  variant="outline" 
                  size="sm" 
                  disabled={results.page === 1}
                >
                  Previous
                </Button>
                <Button 
                  variant="outline" 
                  size="sm" 
                  disabled={results.page >= Math.ceil(results.totalCount / results.limit)}
                >
                  Next
                </Button>
              </div>
            </div>
          </div>
        )}
      </Card>
    </div>
  );
};

export default ScreeningResults;