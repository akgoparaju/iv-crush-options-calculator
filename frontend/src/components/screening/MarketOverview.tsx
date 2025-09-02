import React from 'react';
import { Card } from '../ui/Card';
import { Badge } from '../ui/Badge';
import { Button } from '../ui/Button';
import { formatCurrency, formatPercentage } from '../../utils/formatters';
import { MarketOverview as MarketOverviewType } from '../../types/screening';
import { 
  TrendingUp, 
  TrendingDown, 
  Calendar,
  Activity,
  DollarSign,
  BarChart3,
  Eye
} from 'lucide-react';

interface MarketOverviewProps {
  data: MarketOverviewType;
  onSymbolSelect?: (symbol: string) => void;
}

const MarketOverview: React.FC<MarketOverviewProps> = ({ data, onSymbolSelect }) => {
  const formatTime = (timestamp: string) => {
    return new Date(timestamp).toLocaleString();
  };

  const getTimeOfDayLabel = (time: string) => {
    switch (time) {
      case 'BMO': return 'Before Market Open';
      case 'AMC': return 'After Market Close';
      default: return 'Unknown';
    }
  };

  return (
    <div className="space-y-6">
      {/* Market Indices */}
      <Card className="p-6">
        <h3 className="text-lg font-semibold text-slate-900 mb-4">Market Indices</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {data.indices.map((index) => (
            <div key={index.symbol} className="p-4 bg-slate-50 rounded-lg">
              <div className="flex items-center justify-between mb-2">
                <span className="font-medium text-slate-900">{index.symbol}</span>
                {index.change >= 0 ? (
                  <TrendingUp className="w-4 h-4 text-green-600" />
                ) : (
                  <TrendingDown className="w-4 h-4 text-red-600" />
                )}
              </div>
              <p className="text-sm text-slate-600 mb-1">{index.name}</p>
              <p className="text-lg font-bold text-slate-900">
                {formatCurrency(index.price)}
              </p>
              <div className={`flex items-center space-x-2 text-sm ${
                index.change >= 0 ? 'text-green-600' : 'text-red-600'
              }`}>
                <span>{index.change >= 0 ? '+' : ''}{formatCurrency(index.change)}</span>
                <span>({formatPercentage(index.changePercent)})</span>
              </div>
              {index.impliedVolatility && (
                <p className="text-xs text-slate-500 mt-1">
                  IV: {formatPercentage(index.impliedVolatility)}
                </p>
              )}
            </div>
          ))}
        </div>
      </Card>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Volatility Metrics */}
        <Card className="p-6">
          <h3 className="text-lg font-semibold text-slate-900 mb-4">Volatility Metrics</h3>
          <div className="space-y-4">
            <div className="flex items-center justify-between p-4 bg-slate-50 rounded-lg">
              <div className="flex items-center space-x-3">
                <div className="p-2 bg-primary-100 rounded-lg">
                  <Activity className="w-5 h-5 text-primary-600" />
                </div>
                <div>
                  <p className="font-medium text-slate-900">VIX</p>
                  <p className="text-sm text-slate-600">Fear & Greed Index</p>
                </div>
              </div>
              <div className="text-right">
                <p className="text-xl font-bold text-slate-900">
                  {data.volatilityMetrics.vix.toFixed(2)}
                </p>
                <p className={`text-sm ${
                  data.volatilityMetrics.vixChange >= 0 ? 'text-green-600' : 'text-red-600'
                }`}>
                  {data.volatilityMetrics.vixChange >= 0 ? '+' : ''}
                  {data.volatilityMetrics.vixChange.toFixed(2)}
                </p>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="p-3 bg-slate-50 rounded-lg">
                <p className="text-sm text-slate-600">Term Structure</p>
                <p className="font-medium text-slate-900">
                  Front: {data.volatilityMetrics.termStructure.front.toFixed(1)}%
                </p>
                <p className="font-medium text-slate-900">
                  Back: {data.volatilityMetrics.termStructure.back.toFixed(1)}%
                </p>
                <p className={`text-sm ${
                  data.volatilityMetrics.termStructure.slope >= 0 ? 'text-green-600' : 'text-red-600'
                }`}>
                  Slope: {data.volatilityMetrics.termStructure.slope.toFixed(3)}
                </p>
              </div>
              
              <div className="p-3 bg-slate-50 rounded-lg">
                <p className="text-sm text-slate-600">Volatility Skew</p>
                <p className="font-medium text-slate-900">
                  SPX: {data.volatilityMetrics.skew.spx.toFixed(1)}%
                </p>
                <p className="font-medium text-slate-900">
                  Individual: {data.volatilityMetrics.skew.individual.toFixed(1)}%
                </p>
              </div>
            </div>
          </div>
        </Card>

        {/* Sector Performance */}
        <Card className="p-6">
          <h3 className="text-lg font-semibold text-slate-900 mb-4">Sector Performance</h3>
          <div className="space-y-3">
            {data.sectors.slice(0, 8).map((sector) => (
              <div key={sector.sector} className="flex items-center justify-between p-2 hover:bg-slate-50 rounded">
                <div className="flex-1">
                  <div className="flex items-center justify-between">
                    <span className="font-medium text-slate-900 text-sm">{sector.sector}</span>
                    <div className="flex items-center space-x-2">
                      <Badge variant="outline" className="text-xs">
                        {sector.symbolCount} stocks
                      </Badge>
                      <span className={`text-sm font-medium ${
                        sector.change >= 0 ? 'text-green-600' : 'text-red-600'
                      }`}>
                        {formatPercentage(sector.changePercent)}
                      </span>
                    </div>
                  </div>
                  <div className="flex items-center justify-between mt-1">
                    <span className="text-xs text-slate-500">
                      Avg IV: {formatPercentage(sector.avgImpliedVolatility)}
                    </span>
                    <div className="flex items-center space-x-1">
                      {sector.topSymbols.slice(0, 3).map((symbol) => (
                        <Badge key={symbol} variant="outline" className="text-xs">
                          {symbol}
                        </Badge>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Top Gainers */}
        <Card className="p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-slate-900">Top Gainers</h3>
            <TrendingUp className="w-5 h-5 text-green-600" />
          </div>
          <div className="space-y-3">
            {data.topMovers.gainers.slice(0, 5).map((stock) => (
              <div key={stock.symbol} className="flex items-center justify-between">
                <div className="flex-1">
                  <div className="flex items-center space-x-2">
                    <span className="font-medium text-slate-900">{stock.symbol}</span>
                    <Badge variant="success" className="text-xs">
                      {formatPercentage(stock.changePercent)}
                    </Badge>
                  </div>
                  <p className="text-sm text-slate-600 truncate">{stock.name}</p>
                  <p className="text-xs text-slate-500">
                    IV: {formatPercentage(stock.impliedVolatility)} | Vol: {stock.volume.toLocaleString()}
                  </p>
                </div>
                <div className="text-right">
                  <p className="font-medium text-slate-900">{formatCurrency(stock.price)}</p>
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={() => onSymbolSelect?.(stock.symbol)}
                    className="p-1"
                  >
                    <Eye className="w-3 h-3" />
                  </Button>
                </div>
              </div>
            ))}
          </div>
        </Card>

        {/* Top Losers */}
        <Card className="p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-slate-900">Top Losers</h3>
            <TrendingDown className="w-5 h-5 text-red-600" />
          </div>
          <div className="space-y-3">
            {data.topMovers.losers.slice(0, 5).map((stock) => (
              <div key={stock.symbol} className="flex items-center justify-between">
                <div className="flex-1">
                  <div className="flex items-center space-x-2">
                    <span className="font-medium text-slate-900">{stock.symbol}</span>
                    <Badge variant="destructive" className="text-xs">
                      {formatPercentage(stock.changePercent)}
                    </Badge>
                  </div>
                  <p className="text-sm text-slate-600 truncate">{stock.name}</p>
                  <p className="text-xs text-slate-500">
                    IV: {formatPercentage(stock.impliedVolatility)} | Vol: {stock.volume.toLocaleString()}
                  </p>
                </div>
                <div className="text-right">
                  <p className="font-medium text-slate-900">{formatCurrency(stock.price)}</p>
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={() => onSymbolSelect?.(stock.symbol)}
                    className="p-1"
                  >
                    <Eye className="w-3 h-3" />
                  </Button>
                </div>
              </div>
            ))}
          </div>
        </Card>

        {/* Most Active */}
        <Card className="p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-slate-900">Most Active</h3>
            <BarChart3 className="w-5 h-5 text-blue-600" />
          </div>
          <div className="space-y-3">
            {data.topMovers.active.slice(0, 5).map((stock) => (
              <div key={stock.symbol} className="flex items-center justify-between">
                <div className="flex-1">
                  <div className="flex items-center space-x-2">
                    <span className="font-medium text-slate-900">{stock.symbol}</span>
                    <Badge 
                      variant={stock.changePercent >= 0 ? 'success' : 'destructive'} 
                      className="text-xs"
                    >
                      {formatPercentage(stock.changePercent)}
                    </Badge>
                  </div>
                  <p className="text-sm text-slate-600 truncate">{stock.name}</p>
                  <p className="text-xs text-slate-500">
                    IV: {formatPercentage(stock.impliedVolatility)} | Vol: {(stock.volume / 1000000).toFixed(1)}M
                  </p>
                </div>
                <div className="text-right">
                  <p className="font-medium text-slate-900">{formatCurrency(stock.price)}</p>
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={() => onSymbolSelect?.(stock.symbol)}
                    className="p-1"
                  >
                    <Eye className="w-3 h-3" />
                  </Button>
                </div>
              </div>
            ))}
          </div>
        </Card>
      </div>

      {/* Earnings Calendar */}
      {data.earnings && data.earnings.length > 0 && (
        <Card className="p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-slate-900">Upcoming Earnings</h3>
            <Calendar className="w-5 h-5 text-purple-600" />
          </div>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-slate-200">
              <thead>
                <tr>
                  <th className="px-4 py-2 text-left text-xs font-medium text-slate-500 uppercase">Symbol</th>
                  <th className="px-4 py-2 text-left text-xs font-medium text-slate-500 uppercase">Date</th>
                  <th className="px-4 py-2 text-left text-xs font-medium text-slate-500 uppercase">Time</th>
                  <th className="px-4 py-2 text-left text-xs font-medium text-slate-500 uppercase">Implied Move</th>
                  <th className="px-4 py-2 text-left text-xs font-medium text-slate-500 uppercase">DTE</th>
                  <th className="px-4 py-2 text-left text-xs font-medium text-slate-500 uppercase">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200">
                {data.earnings.slice(0, 10).map((earning) => (
                  <tr key={earning.symbol} className="hover:bg-slate-50">
                    <td className="px-4 py-2">
                      <div>
                        <span className="font-medium text-slate-900">{earning.symbol}</span>
                        <p className="text-sm text-slate-600 truncate">{earning.name}</p>
                      </div>
                    </td>
                    <td className="px-4 py-2 text-sm text-slate-900">
                      {new Date(earning.date).toLocaleDateString()}
                    </td>
                    <td className="px-4 py-2">
                      <Badge 
                        variant={earning.time === 'BMO' ? 'secondary' : earning.time === 'AMC' ? 'warning' : 'outline'}
                        className="text-xs"
                      >
                        {earning.time}
                      </Badge>
                    </td>
                    <td className="px-4 py-2 text-sm text-slate-900">
                      {earning.impliedMove ? formatPercentage(earning.impliedMove) : 'N/A'}
                    </td>
                    <td className="px-4 py-2 text-sm text-slate-900">
                      {earning.daysToEarnings}d
                    </td>
                    <td className="px-4 py-2">
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={() => onSymbolSelect?.(earning.symbol)}
                      >
                        <Eye className="w-4 h-4 mr-1" />
                        Analyze
                      </Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      )}

      {/* Last Updated */}
      <div className="text-center text-sm text-slate-500">
        Last updated: {formatTime(data.lastUpdated)}
      </div>
    </div>
  );
};

export default MarketOverview;