import React, { useState, useMemo } from 'react'
import { 
  TrendingUp, 
  Calendar, 
  DollarSign, 
  Target, 
  ChevronDown, 
  ChevronRight,
  Copy,
  Download,
  Share2,
  Clock,
  AlertCircle,
  CheckCircle,
  XCircle,
  Info
} from 'lucide-react'
import { Card } from '../ui/Card'
import { Button } from '../ui/Button'
import { Badge } from '../ui/Badge'
import { Tooltip } from '../ui/Tooltip'
import { LoadingSpinner, ProgressBar, Skeleton } from '../ui/LoadingSpinner'
import { NetworkError, ServerError, ValidationError, TimeoutError, LoadingWithTimeout } from '../ui/ErrorStates'
import ErrorBoundary from '../ui/ErrorBoundary'
import { AnalysisResponse } from '@/types/api'

interface AnalysisResultsProps {
  data: AnalysisResponse | null
  isLoading: boolean
  error?: string | null
  errorType?: 'network' | 'server' | 'validation' | 'timeout' | 'security' | 'unknown'
  progress?: number
  loadingMessage?: string
  onRetry?: () => void
  onCancel?: () => void
}

interface ResultSectionProps {
  title: string
  icon: React.ReactNode
  status?: 'success' | 'warning' | 'error' | 'info'
  badge?: React.ReactNode
  children: React.ReactNode
  collapsible?: boolean
  defaultExpanded?: boolean
  actions?: React.ReactNode
}

const ResultSection: React.FC<ResultSectionProps> = ({
  title,
  icon,
  status,
  badge,
  children,
  collapsible = false,
  defaultExpanded = true,
  actions
}) => {
  const [expanded, setExpanded] = useState(defaultExpanded)
  
  const statusIcons = {
    success: <CheckCircle className="h-4 w-4 text-success-600" />,
    warning: <AlertCircle className="h-4 w-4 text-warning-600" />,
    error: <XCircle className="h-4 w-4 text-danger-600" />,
    info: <Info className="h-4 w-4 text-primary-600" />
  }

  return (
    <Card className="overflow-hidden">
      <div className="px-3 sm:px-4 lg:px-6 py-3 sm:py-4 border-b border-slate-200 bg-slate-50">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between space-y-2 sm:space-y-0">
          <div className="flex items-center space-x-2 sm:space-x-3">
            {icon}
            <h3 className="text-base sm:text-lg font-semibold text-slate-900 truncate">{title}</h3>
            {status && statusIcons[status]}
            {badge && <div className="hidden sm:block">{badge}</div>}
          </div>
          
          <div className="flex items-center justify-between sm:justify-end space-x-2">
            {badge && <div className="block sm:hidden">{badge}</div>}
            {actions && <div className="flex items-center space-x-2">{actions}</div>}
            {collapsible && (
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setExpanded(!expanded)}
                className="ml-auto touch-manipulation"
              >
                {expanded ? <ChevronDown className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
              </Button>
            )}
          </div>
        </div>
      </div>
      
      {expanded && (
        <div className="px-3 sm:px-4 lg:px-6 py-3 sm:py-4">
          {children}
        </div>
      )}
    </Card>
  )
}

const DataTable: React.FC<{
  data: Array<{ label: string; value: React.ReactNode; tooltip?: string }>
  columns?: 2 | 3 | 4
}> = ({ data, columns = 2 }) => {
  const gridCols = {
    2: 'grid-cols-1 sm:grid-cols-2',
    3: 'grid-cols-1 sm:grid-cols-2 lg:grid-cols-3', 
    4: 'grid-cols-1 sm:grid-cols-2 lg:grid-cols-4'
  }

  return (
    <div className={`grid ${gridCols[columns]} gap-3 sm:gap-4`}>
      {data.map((item, index) => (
        <div key={index} className="bg-white p-3 sm:p-4 rounded-lg border border-slate-200 hover:shadow-sm transition-shadow">
          <div className="flex items-center justify-between">
            <dt className="text-sm font-medium text-slate-600 flex items-center">
              <span className="truncate">{item.label}</span>
              {item.tooltip && (
                <Tooltip content={item.tooltip}>
                  <Info className="h-3 w-3 ml-1 flex-shrink-0 text-slate-400" />
                </Tooltip>
              )}
            </dt>
          </div>
          <dd className="mt-1 text-base sm:text-lg font-semibold text-slate-900 break-words">
            {item.value}
          </dd>
        </div>
      ))}
    </div>
  )
}

const StatusIndicator: React.FC<{ status: boolean; label: string }> = ({ status, label }) => (
  <div className="flex items-center space-x-2">
    {status ? (
      <CheckCircle className="h-4 w-4 flex-shrink-0 text-success-600" />
    ) : (
      <XCircle className="h-4 w-4 flex-shrink-0 text-danger-600" />
    )}
    <span className={`text-sm break-words ${status ? 'text-success-700' : 'text-danger-700'}`}>
      {label}
    </span>
  </div>
)

export const AnalysisResults: React.FC<AnalysisResultsProps> = ({
  data,
  isLoading,
  error,
  errorType = 'unknown',
  progress,
  loadingMessage = 'Running Analysis',
  onRetry,
  onCancel
}) => {
  const [copiedData, setCopiedData] = useState<string | null>(null)

  const copyToClipboard = async (text: string, label: string) => {
    try {
      await navigator.clipboard.writeText(text)
      setCopiedData(label)
      setTimeout(() => setCopiedData(null), 2000)
    } catch (err) {
      console.error('Failed to copy:', err)
    }
  }

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2
    }).format(value)
  }

  const formatPercentage = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'percent',
      minimumFractionDigits: 1,
      maximumFractionDigits: 1
    }).format(value / 100)
  }

  if (isLoading) {
    return (
      <LoadingWithTimeout
        message={loadingMessage}
        timeout={60000} // 60 seconds
        onTimeout={() => onCancel?.()}
      >
        <Card className="p-6 sm:p-8">
          <div className="flex flex-col items-center justify-center space-y-6">
            <LoadingSpinner size="lg" message={loadingMessage} />
            
            {progress !== undefined && (
              <div className="w-full max-w-xs">
                <ProgressBar 
                  progress={progress} 
                  message="Analyzing scenarios..." 
                />
              </div>
            )}
            
            <div className="text-center max-w-md">
              <p className="text-slate-600 text-sm">
                Processing options data, calculating Greeks, and running scenario analysis...
              </p>
              
              {onCancel && (
                <Button
                  onClick={onCancel}
                  variant="ghost"
                  size="sm"
                  className="mt-4"
                >
                  Cancel Analysis
                </Button>
              )}
            </div>

            {/* Loading skeleton for preview */}
            <div className="w-full max-w-2xl mt-8">
              <div className="space-y-4">
                <Skeleton rows={2} />
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <Skeleton rows={1} />
                  <Skeleton rows={1} />
                </div>
              </div>
            </div>
          </div>
        </Card>
      </LoadingWithTimeout>
    )
  }

  if (error) {
    // Render specific error components based on error type
    switch (errorType) {
      case 'network':
        return <NetworkError onRetry={onRetry} />
      
      case 'server':
        return (
          <ServerError 
            onRetry={onRetry} 
            errorCode={error?.match(/\d{3}/)?.[0]} // Extract error code if present
          />
        )
      
      case 'validation':
        return (
          <ValidationError 
            title="Invalid Parameters"
            message={error}
            onFix={onRetry}
          />
        )
      
      case 'timeout':
        return (
          <TimeoutError 
            onRetry={onRetry}
            onCancel={onCancel}
          />
        )
      
      default:
        return (
          <Card className="p-6 sm:p-8">
            <div className="text-center">
              <XCircle className="h-12 w-12 text-danger-500 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-slate-900 mb-2">
                Analysis Failed
              </h3>
              <p className="text-slate-600 mb-4 max-w-md mx-auto">
                {error || 'An unexpected error occurred during analysis. Please try again.'}
              </p>
              <div className="flex flex-col sm:flex-row gap-3 justify-center">
                {onRetry && (
                  <Button onClick={onRetry} variant="primary">
                    Retry Analysis
                  </Button>
                )}
                {onCancel && (
                  <Button onClick={onCancel} variant="outline">
                    Cancel
                  </Button>
                )}
              </div>
            </div>
          </Card>
        )
    }
  }

  if (!data) {
    return (
      <Card className="p-8">
        <div className="text-center text-slate-500">
          <TrendingUp className="h-12 w-12 opacity-50 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-slate-700 mb-2">
            Ready for Analysis
          </h3>
          <p className="text-slate-600">
            Configure your parameters and run an analysis to see results here.
          </p>
        </div>
      </Card>
    )
  }

  return (
    <ErrorBoundary
      onError={(error, errorInfo) => {
        console.error('AnalysisResults error:', error, errorInfo)
        // In production, send to error reporting service
      }}
    >
      <div className="space-y-6">
      {/* Analysis Overview */}
      <ResultSection
        title="Analysis Overview"
        icon={<TrendingUp className="h-5 w-5 text-primary-600" />}
        status={data.success ? 'success' : 'error'}
        badge={
          <Badge variant="info" size="sm">
            {data.data_source}
          </Badge>
        }
        actions={
          <div className="flex space-x-2">
            <Tooltip content="Copy analysis summary">
              <Button
                variant="ghost"
                size="sm"
                onClick={() => copyToClipboard(JSON.stringify(data, null, 2), 'summary')}
              >
                <Copy className="h-4 w-4" />
              </Button>
            </Tooltip>
            <Tooltip content="Download full report">
              <Button variant="ghost" size="sm">
                <Download className="h-4 w-4" />
              </Button>
            </Tooltip>
            <Tooltip content="Share results">
              <Button variant="ghost" size="sm">
                <Share2 className="h-4 w-4" />
              </Button>
            </Tooltip>
          </div>
        }
      >
        <DataTable
          data={[
            { 
              label: 'Symbol', 
              value: <span className="font-mono">{data.symbol}</span> 
            },
            { 
              label: 'Current Price', 
              value: formatCurrency(data.current_price || 0),
              tooltip: 'Current market price of the underlying stock'
            },
            { 
              label: 'Analysis Time', 
              value: <span className="flex items-center">
                <Clock className="h-4 w-4 mr-1 text-slate-400" />
                {new Date(data.timestamp).toLocaleString()}
              </span>
            },
            { 
              label: 'Data Quality', 
              value: data.success ? (
                <Badge variant="success" size="sm">Excellent</Badge>
              ) : (
                <Badge variant="warning" size="sm">Partial</Badge>
              )
            }
          ]}
          columns={4}
        />
      </ResultSection>

      {/* Module Status Indicators */}
      <ResultSection
        title="Analysis Modules Status"
        icon={<CheckCircle className="h-5 w-5 text-success-600" />}
        collapsible
        defaultExpanded={false}
      >
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <StatusIndicator 
            status={!!data.earnings_calendar} 
            label="Earnings Calendar"
          />
          <StatusIndicator 
            status={!!data.trade_construction} 
            label="Trade Construction"
          />
          <StatusIndicator 
            status={!!data.position_sizing} 
            label="Position Sizing"
          />
          <StatusIndicator 
            status={!!data.trading_decision} 
            label="Trading Decision"
          />
        </div>
      </ResultSection>

      {/* Earnings Calendar Analysis */}
      {data.earnings_calendar && (
        <ResultSection
          title="Earnings Calendar Analysis"
          icon={<Calendar className="h-5 w-5 text-warning-600" />}
          status="success"
          badge={<Badge variant="warning" size="sm">BMO/AMC</Badge>}
        >
          <div className="space-y-4">
            <DataTable
              data={[
                { 
                  label: 'Next Earnings', 
                  value: data.earnings_calendar.next_earnings_date || 'Not Available',
                  tooltip: 'Next scheduled earnings announcement date'
                },
                { 
                  label: 'Timing', 
                  value: data.earnings_calendar.timing || 'Unknown',
                  tooltip: 'Before Market Open (BMO) or After Market Close (AMC)'
                },
                { 
                  label: 'Entry Window', 
                  value: 'Market Close - 15min',
                  tooltip: 'Optimal entry timing for earnings play'
                },
                { 
                  label: 'Exit Window', 
                  value: 'Market Open + 15min',
                  tooltip: 'Recommended exit timing after earnings'
                }
              ]}
            />
          </div>
        </ResultSection>
      )}

      {/* Trade Construction */}
      {data.trade_construction && (
        <ResultSection
          title="Trade Construction & P&L Analysis"
          icon={<DollarSign className="h-5 w-5 text-success-600" />}
          status="success"
          badge={<Badge variant="info" size="sm">Calendar Spread</Badge>}
        >
          <div className="space-y-6">
            {/* Trade Details */}
            <div>
              <h4 className="font-medium text-slate-900 mb-3">Trade Structure</h4>
              <DataTable
                data={[
                  { 
                    label: 'Strategy', 
                    value: data.trade_construction.recommended_strategy || 'Calendar Spread' 
                  },
                  { 
                    label: 'Strike Price', 
                    value: formatCurrency(data.trade_construction.strike || 0) 
                  },
                  { 
                    label: 'Net Debit', 
                    value: formatCurrency(data.trade_construction.net_debit || 0),
                    tooltip: 'Total cost to enter the trade'
                  },
                  { 
                    label: 'Max Loss', 
                    value: formatCurrency(data.trade_construction.max_loss || 0),
                    tooltip: 'Maximum potential loss (limited to net debit)'
                  },
                  { 
                    label: 'Max Profit', 
                    value: formatCurrency(data.trade_construction.max_profit || 0),
                    tooltip: 'Maximum potential profit if stock stays near strike'
                  },
                  { 
                    label: 'Breakeven Range', 
                    value: `${formatCurrency(data.trade_construction.breakeven_lower || 0)} - ${formatCurrency(data.trade_construction.breakeven_upper || 0)}`,
                    tooltip: 'Stock price range where trade is profitable'
                  }
                ]}
                columns={3}
              />
            </div>

            {/* P&L Analysis */}
            {data.trade_construction.pnl_analysis && (
              <div>
                <h4 className="font-medium text-slate-900 mb-3">P&L Scenarios</h4>
                <DataTable
                  data={[
                    { 
                      label: 'Win Rate', 
                      value: formatPercentage(data.trade_construction.pnl_analysis.win_rate || 0),
                      tooltip: 'Percentage of scenarios showing profit'
                    },
                    { 
                      label: 'Avg Profit', 
                      value: formatCurrency(data.trade_construction.pnl_analysis.avg_profit || 0),
                      tooltip: 'Average profit across all winning scenarios'
                    },
                    { 
                      label: 'Avg Loss', 
                      value: formatCurrency(data.trade_construction.pnl_analysis.avg_loss || 0),
                      tooltip: 'Average loss across all losing scenarios'
                    },
                    { 
                      label: 'Risk/Reward', 
                      value: `${(data.trade_construction.pnl_analysis.risk_reward_ratio || 0).toFixed(2)}:1`,
                      tooltip: 'Risk to reward ratio for this trade'
                    }
                  ]}
                />
              </div>
            )}

            {/* Greeks */}
            {data.trade_construction.greeks && (
              <div>
                <h4 className="font-medium text-slate-900 mb-3">Greeks Analysis</h4>
                <DataTable
                  data={[
                    { 
                      label: 'Net Delta', 
                      value: data.trade_construction.greeks.delta?.toFixed(3) || '0.000',
                      tooltip: 'Price sensitivity to underlying movement'
                    },
                    { 
                      label: 'Net Gamma', 
                      value: data.trade_construction.greeks.gamma?.toFixed(3) || '0.000',
                      tooltip: 'Rate of change of delta'
                    },
                    { 
                      label: 'Net Theta', 
                      value: `${data.trade_construction.greeks.theta?.toFixed(2) || '0.00'}/day`,
                      tooltip: 'Time decay (profit/loss per day)'
                    },
                    { 
                      label: 'Net Vega', 
                      value: data.trade_construction.greeks.vega?.toFixed(3) || '0.000',
                      tooltip: 'Sensitivity to volatility changes'
                    }
                  ]}
                />
              </div>
            )}
          </div>
        </ResultSection>
      )}

      {/* Position Sizing */}
      {data.position_sizing && (
        <ResultSection
          title="Position Sizing & Risk Management"
          icon={<Target className="h-5 w-5 text-primary-600" />}
          status="success"
          badge={<Badge variant="conservative" size="sm">Kelly Criterion</Badge>}
        >
          <div className="space-y-4">
            <DataTable
              data={[
                { 
                  label: 'Recommended Contracts', 
                  value: data.position_sizing.recommended_contracts || 0,
                  tooltip: 'Optimal number of contracts based on Kelly criterion'
                },
                { 
                  label: 'Capital Required', 
                  value: formatCurrency(data.position_sizing.capital_required || 0),
                  tooltip: 'Total capital needed for recommended position'
                },
                { 
                  label: 'Portfolio Risk', 
                  value: formatPercentage(data.position_sizing.portfolio_risk || 0),
                  tooltip: 'Percentage of portfolio at risk'
                },
                { 
                  label: 'Kelly Fraction', 
                  value: `${((data.position_sizing.kelly_fraction || 0) * 100).toFixed(1)}%`,
                  tooltip: 'Kelly criterion recommended bet size'
                }
              ]}
            />
          </div>
        </ResultSection>
      )}

      {/* Trading Decision */}
      {data.trading_decision && (
        <ResultSection
          title="Trading Decision Summary"
          icon={<Target className="h-5 w-5 text-success-600" />}
          status={data.trading_decision.recommendation === 'RECOMMENDED' ? 'success' : 
                  data.trading_decision.recommendation === 'CONSIDER' ? 'warning' : 'error'}
          badge={
            <Badge 
              variant={data.trading_decision.recommendation === 'RECOMMENDED' ? 'success' : 
                      data.trading_decision.recommendation === 'CONSIDER' ? 'warning' : 'danger'}
              size="md"
            >
              {data.trading_decision.recommendation}
            </Badge>
          }
        >
          <div className="space-y-4">
            <div className="p-4 bg-slate-50 rounded-lg">
              <h4 className="font-medium text-slate-900 mb-2">Decision Reasoning</h4>
              <p className="text-slate-700">
                {data.trading_decision.reasoning || 'Analysis completed successfully with standard parameters.'}
              </p>
            </div>
            
            <DataTable
              data={[
                { 
                  label: 'Signal Strength', 
                  value: `${data.trading_decision.signal_strength || 0}/3`,
                  tooltip: 'Number of positive signals detected'
                },
                { 
                  label: 'Confidence Level', 
                  value: formatPercentage(data.trading_decision.confidence || 0),
                  tooltip: 'Confidence in the trading decision'
                },
                { 
                  label: 'Risk Assessment', 
                  value: data.trading_decision.risk_level || 'Moderate',
                  tooltip: 'Overall risk level for this trade'
                },
                { 
                  label: 'Time Horizon', 
                  value: data.trading_decision.time_horizon || 'Short-term',
                  tooltip: 'Recommended holding period'
                }
              ]}
            />
          </div>
        </ResultSection>
      )}

      {/* Copy Notification */}
      {copiedData && (
        <div className="fixed bottom-4 right-4 bg-success-600 text-white px-4 py-2 rounded-lg shadow-lg">
          <div className="flex items-center space-x-2">
            <CheckCircle className="h-4 w-4" />
            <span className="text-sm">Copied {copiedData} to clipboard</span>
          </div>
        </div>
      )}
      </div>
    </ErrorBoundary>
  )
}

export default AnalysisResults