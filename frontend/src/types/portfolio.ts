// Portfolio type definitions for the Advanced Options Trading Calculator

export interface PortfolioSummary {
  id: string;
  name: string;
  description?: string;
  initialCapital: number;
  currentValue: number;
  availableCash: number;
  totalPnl: number;
  dailyPnl: number;
  positionCount: number;
  isDefault: boolean;
  createdAt: string;
  updatedAt: string;
}

export interface PortfolioDetail extends PortfolioSummary {
  positions: Position[];
  riskMetrics: RiskMetrics;
  performanceMetrics: PerformanceMetrics;
  analytics: PortfolioAnalytics;
}

export interface Position {
  id: string;
  portfolioId: string;
  symbol: string;
  strategyType: StrategyType;
  status: PositionStatus;
  entryDate: string;
  exitDate?: string;
  entryCost: number;
  exitValue?: number;
  pnl: number;
  pnlPercentage: number;
  maxProfit?: number;
  maxLoss?: number;
  breakevenPoints: number[];
  greeks: Greeks;
  legs: OptionLeg[];
  notes?: string;
  createdAt: string;
  updatedAt: string;
}

export interface OptionLeg {
  id: string;
  positionId: string;
  optionType: 'call' | 'put';
  strikePrice: number;
  expirationDate: string;
  action: 'buy_to_open' | 'sell_to_open' | 'buy_to_close' | 'sell_to_close';
  contracts: number;
  premium: number;
  impliedVolatility?: number;
  delta?: number;
  gamma?: number;
  theta?: number;
  vega?: number;
}

export interface Greeks {
  delta: number;
  gamma: number;
  theta: number;
  vega: number;
  rho?: number;
}

export interface RiskMetrics {
  portfolioDelta: number;
  portfolioGamma: number;
  portfolioTheta: number;
  portfolioVega: number;
  concentrationRisk: number;
  varOneDay: number;
  maxDrawdown: number;
  sharpeRatio: number;
  volatility: number;
}

export interface PerformanceMetrics {
  totalReturn: number;
  annualizedReturn: number;
  winRate: number;
  profitFactor: number;
  averageWin: number;
  averageLoss: number;
  largestWin: number;
  largestLoss: number;
  totalTrades: number;
  winningTrades: number;
  losingTrades: number;
}

export interface PortfolioAnalytics {
  pnlChart: PnLDataPoint[];
  performanceBreakdown: PerformanceBreakdown;
  strategyDistribution: StrategyDistribution[];
  symbolDistribution: SymbolDistribution[];
  monthlyReturns: MonthlyReturn[];
}

export interface PnLDataPoint {
  date: string;
  pnl: number;
  cumulativePnl: number;
  portfolioValue: number;
}

export interface PerformanceBreakdown {
  byStrategy: Record<StrategyType, number>;
  bySymbol: Record<string, number>;
  byMonth: Record<string, number>;
  byTimeframe: {
    oneWeek: number;
    oneMonth: number;
    threeMonths: number;
    sixMonths: number;
    oneYear: number;
  };
}

export interface StrategyDistribution {
  strategy: StrategyType;
  count: number;
  pnl: number;
  percentage: number;
}

export interface SymbolDistribution {
  symbol: string;
  count: number;
  pnl: number;
  percentage: number;
  currentValue: number;
}

export interface MonthlyReturn {
  month: string;
  return: number;
  trades: number;
  winRate: number;
}

// Enums and Unions
export type StrategyType = 
  | 'calendar_spread'
  | 'straddle'
  | 'strangle'
  | 'iron_condor'
  | 'iron_butterfly'
  | 'covered_call'
  | 'cash_secured_put'
  | 'long_call'
  | 'long_put'
  | 'short_call'
  | 'short_put'
  | 'bull_call_spread'
  | 'bear_put_spread'
  | 'collar';

export type PositionStatus = 'open' | 'closed' | 'expired' | 'assigned';

// Form Data Types
export interface CreatePortfolioRequest {
  name: string;
  description?: string;
  initialCapital: number;
  isDefault?: boolean;
}

export interface UpdatePortfolioRequest {
  name?: string;
  description?: string;
  isDefault?: boolean;
}

export interface AddPositionRequest {
  symbol: string;
  strategyType: StrategyType;
  entryDate: string;
  legs: CreateOptionLegRequest[];
  notes?: string;
}

export interface CreateOptionLegRequest {
  optionType: 'call' | 'put';
  strikePrice: number;
  expirationDate: string;
  action: 'buy_to_open' | 'sell_to_open' | 'buy_to_close' | 'sell_to_close';
  contracts: number;
  premium: number;
}

export interface ClosePositionRequest {
  exitDate: string;
  exitValue: number;
  exitReason?: string;
  notes?: string;
}

// API Response Types
export interface PortfolioListResponse {
  portfolios: PortfolioSummary[];
  totalCount: number;
}

export interface PortfolioDetailResponse {
  portfolio: PortfolioDetail;
}

export interface PositionResponse {
  position: Position;
}

export interface PortfolioAnalyticsResponse {
  analytics: PortfolioAnalytics;
}

// Chart Data Types
export interface ChartDataPoint {
  x: number | string | Date;
  y: number;
  label?: string;
}

export interface PnLChartData {
  data: ChartDataPoint[];
  currentValue: number;
  totalPnl: number;
  dateRange: {
    start: string;
    end: string;
  };
}

export interface GreeksChartData {
  portfolio: {
    delta: ChartDataPoint[];
    gamma: ChartDataPoint[];
    theta: ChartDataPoint[];
    vega: ChartDataPoint[];
  };
  positions: Record<string, {
    symbol: string;
    delta: ChartDataPoint[];
    gamma: ChartDataPoint[];
    theta: ChartDataPoint[];
    vega: ChartDataPoint[];
  }>;
}

// Filter and Sort Types
export interface PortfolioFilter {
  status?: PositionStatus[];
  strategies?: StrategyType[];
  symbols?: string[];
  dateRange?: {
    start: string;
    end: string;
  };
  minPnl?: number;
  maxPnl?: number;
}

export interface PortfolioSort {
  field: 'name' | 'currentValue' | 'totalPnl' | 'createdAt' | 'updatedAt';
  direction: 'asc' | 'desc';
}

export interface PositionFilter {
  status?: PositionStatus[];
  strategies?: StrategyType[];
  symbols?: string[];
  dateRange?: {
    start: string;
    end: string;
  };
  minPnl?: number;
  maxPnl?: number;
}

export interface PositionSort {
  field: 'symbol' | 'strategyType' | 'entryDate' | 'pnl' | 'status';
  direction: 'asc' | 'desc';
}