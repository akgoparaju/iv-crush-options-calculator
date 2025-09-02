import React from 'react';
import { Card } from '../ui/Card';
import { Badge } from '../ui/Badge';
import { Button } from '../ui/Button';
import { formatCurrency, formatPercentage } from '../../utils/formatters';
import { PortfolioSummary } from '../../types/portfolio';
import { TrendingUpIcon, TrendingDownIcon, EyeIcon } from 'lucide-react';

interface PortfolioCardProps {
  portfolio: PortfolioSummary;
  isSelected?: boolean;
  onSelect: () => void;
  onEdit?: () => void;
  onDelete?: () => void;
}

const PortfolioCard: React.FC<PortfolioCardProps> = ({
  portfolio,
  isSelected = false,
  onSelect,
  onEdit,
  onDelete,
}) => {
  const pnlPercentage = portfolio.initialCapital > 0 
    ? (portfolio.totalPnl / portfolio.initialCapital) * 100 
    : 0;

  const utilizationPercentage = portfolio.currentValue > 0
    ? ((portfolio.currentValue - portfolio.availableCash) / portfolio.currentValue) * 100
    : 0;

  return (
    <Card 
      className={`p-4 cursor-pointer transition-all hover:shadow-md ${
        isSelected ? 'ring-2 ring-blue-500 bg-blue-50' : ''
      }`}
      onClick={onSelect}
    >
      <div className="flex items-start justify-between mb-3">
        <div className="flex-1">
          <h3 className="font-semibold text-slate-900 mb-1">
            {portfolio.name}
          </h3>
          {portfolio.description && (
            <p className="text-sm text-slate-600 mb-2">
              {portfolio.description}
            </p>
          )}
          <div className="flex items-center space-x-2">
            <Badge variant={portfolio.isDefault ? 'success' : 'secondary'}>
              {portfolio.isDefault ? 'Default' : 'Portfolio'}
            </Badge>
            <Badge variant="outline">
              {portfolio.positionCount || 0} positions
            </Badge>
          </div>
        </div>
        
        <div className="text-right">
          <Button
            variant="ghost"
            size="sm"
            onClick={(e) => {
              e.stopPropagation();
              onSelect();
            }}
          >
            <EyeIcon className="w-4 h-4" />
          </Button>
        </div>
      </div>

      {/* Portfolio Metrics */}
      <div className="grid grid-cols-2 gap-4 text-sm">
        <div>
          <p className="text-slate-600">Current Value</p>
          <p className="font-semibold text-slate-900">
            {formatCurrency(portfolio.currentValue)}
          </p>
        </div>
        <div>
          <p className="text-slate-600">Available Cash</p>
          <p className="font-semibold text-slate-900">
            {formatCurrency(portfolio.availableCash)}
          </p>
        </div>
      </div>

      {/* P&L Section */}
      <div className="mt-3 pt-3 border-t border-slate-200">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <div className={`p-1 rounded ${portfolio.totalPnl >= 0 ? 'bg-green-100' : 'bg-red-100'}`}>
              {portfolio.totalPnl >= 0 ? (
                <TrendingUpIcon className="w-3 h-3 text-green-600" />
              ) : (
                <TrendingDownIcon className="w-3 h-3 text-red-600" />
              )}
            </div>
            <div>
              <p className="text-xs text-slate-600">Total P&L</p>
              <p className={`font-semibold text-sm ${portfolio.totalPnl >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                {formatCurrency(portfolio.totalPnl)}
              </p>
            </div>
          </div>
          
          <div className="text-right">
            <p className="text-xs text-slate-600">Return</p>
            <p className={`font-semibold text-sm ${portfolio.totalPnl >= 0 ? 'text-green-600' : 'text-red-600'}`}>
              {formatPercentage(pnlPercentage)}
            </p>
          </div>
        </div>
      </div>

      {/* Daily P&L if available */}
      {portfolio.dailyPnl !== undefined && (
        <div className="mt-2">
          <div className="flex items-center justify-between text-xs">
            <span className="text-slate-600">Today:</span>
            <span className={`font-medium ${portfolio.dailyPnl >= 0 ? 'text-green-600' : 'text-red-600'}`}>
              {formatCurrency(portfolio.dailyPnl)}
            </span>
          </div>
        </div>
      )}

      {/* Utilization Bar */}
      <div className="mt-3">
        <div className="flex items-center justify-between text-xs mb-1">
          <span className="text-slate-600">Capital Utilization</span>
          <span className="text-slate-600">{formatPercentage(utilizationPercentage)}</span>
        </div>
        <div className="w-full bg-slate-200 rounded-full h-1.5">
          <div 
            className={`h-1.5 rounded-full transition-all ${
              utilizationPercentage > 80 ? 'bg-red-500' :
              utilizationPercentage > 60 ? 'bg-yellow-500' : 'bg-green-500'
            }`}
            style={{ width: `${Math.min(utilizationPercentage, 100)}%` }}
          />
        </div>
      </div>

      {/* Created Date */}
      <div className="mt-2 text-xs text-slate-500">
        Created {new Date(portfolio.createdAt).toLocaleDateString()}
      </div>
    </Card>
  );
};

export default PortfolioCard;