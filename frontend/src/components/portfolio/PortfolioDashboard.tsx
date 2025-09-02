import React, { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Card } from '../ui/Card';
import { Button } from '../ui/Button';
import { LoadingSpinner } from '../ui/LoadingSpinner';
import { StatusIndicator } from '../ui/StatusIndicator';
import { Badge } from '../ui/Badge';
import { portfolioService } from '../../services/portfolioService';
import { formatCurrency, formatPercentage } from '../../utils/formatters';
import { PlusIcon, TrendingUpIcon, TrendingDownIcon, DollarSignIcon } from 'lucide-react';
import { PortfolioSummary, PortfolioDetail } from '../../types/portfolio';
import PortfolioCreateModal from './PortfolioCreateModal';
import PortfolioCard from './PortfolioCard';

interface PortfolioDashboardProps {
  onSelectPortfolio?: (portfolioId: string) => void;
}

const PortfolioDashboard: React.FC<PortfolioDashboardProps> = ({ onSelectPortfolio }) => {
  const [selectedPortfolioId, setSelectedPortfolioId] = useState<string | null>(null);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const queryClient = useQueryClient();

  // Fetch user portfolios
  const {
    data: portfolios,
    isLoading: portfoliosLoading,
    error: portfoliosError,
  } = useQuery({
    queryKey: ['portfolios'],
    queryFn: portfolioService.getPortfolios,
  });

  // Fetch selected portfolio details
  const {
    data: portfolioDetail,
    isLoading: detailLoading,
  } = useQuery({
    queryKey: ['portfolio-detail', selectedPortfolioId],
    queryFn: () => portfolioService.getPortfolioDetail(selectedPortfolioId!),
    enabled: !!selectedPortfolioId,
  });

  // Create portfolio mutation
  const createPortfolioMutation = useMutation({
    mutationFn: portfolioService.createPortfolio,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['portfolios'] });
      setShowCreateModal(false);
    },
  });

  const handleSelectPortfolio = (portfolioId: string) => {
    setSelectedPortfolioId(portfolioId);
    onSelectPortfolio?.(portfolioId);
  };

  const calculateTotalValue = (portfolios: PortfolioSummary[] = []) => {
    return portfolios.reduce((total, portfolio) => total + portfolio.currentValue, 0);
  };

  const calculateTotalPnL = (portfolios: PortfolioSummary[] = []) => {
    return portfolios.reduce((total, portfolio) => total + portfolio.totalPnl, 0);
  };

  if (portfoliosLoading) {
    return (
      <div className="flex justify-center items-center h-64">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  if (portfoliosError) {
    return (
      <Card className="p-6">
        <div className="text-center">
          <div className="text-red-500 mb-4">❌</div>
          <h3 className="text-lg font-semibold text-slate-900 mb-2">
            Failed to load portfolios
          </h3>
          <p className="text-slate-600 mb-4">
            There was an error loading your portfolios. Please try again.
          </p>
          <Button 
            onClick={() => queryClient.invalidateQueries({ queryKey: ['portfolios'] })}
          >
            Retry
          </Button>
        </div>
      </Card>
    );
  }

  const totalValue = calculateTotalValue(portfolios);
  const totalPnL = calculateTotalPnL(portfolios);
  const totalPnLPercentage = totalValue > 0 ? (totalPnL / (totalValue - totalPnL)) * 100 : 0;

  return (
    <div className="space-y-6">
      {/* Portfolio Overview Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Portfolio Dashboard</h1>
          <p className="text-slate-600">
            Manage your options trading portfolios and track performance
          </p>
        </div>
        <Button
          onClick={() => setShowCreateModal(true)}
          className="inline-flex items-center"
        >
          <PlusIcon className="w-4 h-4 mr-2" />
          Create Portfolio
        </Button>
      </div>

      {/* Total Portfolio Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card className="p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-slate-600">Total Value</p>
              <p className="text-2xl font-bold text-slate-900">
                {formatCurrency(totalValue)}
              </p>
            </div>
            <div className="p-3 bg-blue-100 rounded-lg">
              <DollarSignIcon className="w-6 h-6 text-blue-600" />
            </div>
          </div>
        </Card>

        <Card className="p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-slate-600">Total P&L</p>
              <p className={`text-2xl font-bold ${totalPnL >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                {formatCurrency(totalPnL)}
              </p>
              <p className={`text-sm ${totalPnL >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                {formatPercentage(totalPnLPercentage)}
              </p>
            </div>
            <div className={`p-3 ${totalPnL >= 0 ? 'bg-green-100' : 'bg-red-100'} rounded-lg`}>
              {totalPnL >= 0 ? (
                <TrendingUpIcon className="w-6 h-6 text-green-600" />
              ) : (
                <TrendingDownIcon className="w-6 h-6 text-red-600" />
              )}
            </div>
          </div>
        </Card>

        <Card className="p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-slate-600">Active Portfolios</p>
              <p className="text-2xl font-bold text-slate-900">
                {portfolios?.length || 0}
              </p>
            </div>
            <div className="p-3 bg-purple-100 rounded-lg">
              <div className="w-6 h-6 text-purple-600 font-bold">📊</div>
            </div>
          </div>
        </Card>
      </div>

      {/* Portfolio List */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="space-y-4">
          <h2 className="text-lg font-semibold text-slate-900">Your Portfolios</h2>
          {portfolios && portfolios.length > 0 ? (
            <div className="space-y-3">
              {portfolios.map((portfolio) => (
                <PortfolioCard
                  key={portfolio.id}
                  portfolio={portfolio}
                  isSelected={selectedPortfolioId === portfolio.id}
                  onSelect={() => handleSelectPortfolio(portfolio.id)}
                />
              ))}
            </div>
          ) : (
            <Card className="p-8 text-center">
              <div className="text-slate-400 mb-4">📊</div>
              <h3 className="text-lg font-semibold text-slate-900 mb-2">
                No Portfolios Yet
              </h3>
              <p className="text-slate-600 mb-4">
                Create your first portfolio to start tracking your options trades.
              </p>
              <Button onClick={() => setShowCreateModal(true)}>
                Create Portfolio
              </Button>
            </Card>
          )}
        </div>

        {/* Portfolio Detail Panel */}
        <div>
          <h2 className="text-lg font-semibold text-slate-900 mb-4">Portfolio Details</h2>
          {selectedPortfolioId ? (
            detailLoading ? (
              <Card className="p-6">
                <div className="flex justify-center">
                  <LoadingSpinner />
                </div>
              </Card>
            ) : portfolioDetail ? (
              <div className="space-y-4">
                {/* Portfolio Performance */}
                <Card className="p-4">
                  <h3 className="font-semibold text-slate-900 mb-3">{portfolioDetail.name}</h3>
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <p className="text-slate-600">Current Value</p>
                      <p className="font-semibold">{formatCurrency(portfolioDetail.currentValue)}</p>
                    </div>
                    <div>
                      <p className="text-slate-600">Available Cash</p>
                      <p className="font-semibold">{formatCurrency(portfolioDetail.availableCash)}</p>
                    </div>
                    <div>
                      <p className="text-slate-600">Total P&L</p>
                      <p className={`font-semibold ${portfolioDetail.totalPnl >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                        {formatCurrency(portfolioDetail.totalPnl)}
                      </p>
                    </div>
                    <div>
                      <p className="text-slate-600">Daily P&L</p>
                      <p className={`font-semibold ${portfolioDetail.dailyPnl >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                        {formatCurrency(portfolioDetail.dailyPnl)}
                      </p>
                    </div>
                  </div>
                </Card>

                {/* Recent Positions */}
                <Card className="p-4">
                  <h4 className="font-semibold text-slate-900 mb-3">Recent Positions</h4>
                  {portfolioDetail.positions && portfolioDetail.positions.length > 0 ? (
                    <div className="space-y-2">
                      {portfolioDetail.positions.slice(0, 3).map((position) => (
                        <div key={position.id} className="flex items-center justify-between py-2 border-b border-slate-100 last:border-b-0">
                          <div>
                            <p className="font-medium text-slate-900">{position.symbol}</p>
                            <p className="text-sm text-slate-600">{position.strategyType}</p>
                          </div>
                          <div className="text-right">
                            <Badge variant={position.status === 'open' ? 'success' : 'secondary'}>
                              {position.status}
                            </Badge>
                            <p className={`text-sm ${position.pnl >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                              {formatCurrency(position.pnl)}
                            </p>
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-slate-600 text-sm">No positions yet</p>
                  )}
                </Card>
              </div>
            ) : null
          ) : (
            <Card className="p-8 text-center">
              <div className="text-slate-400 mb-4">👆</div>
              <h3 className="text-lg font-semibold text-slate-900 mb-2">
                Select a Portfolio
              </h3>
              <p className="text-slate-600">
                Choose a portfolio from the list to view detailed information.
              </p>
            </Card>
          )}
        </div>
      </div>

      {/* Create Portfolio Modal */}
      {showCreateModal && (
        <PortfolioCreateModal
          onClose={() => setShowCreateModal(false)}
          onSubmit={createPortfolioMutation.mutate}
          isLoading={createPortfolioMutation.isPending}
        />
      )}
    </div>
  );
};

export default PortfolioDashboard;