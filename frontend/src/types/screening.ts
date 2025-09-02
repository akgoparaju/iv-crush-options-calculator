// Market screening type definitions for the Advanced Options Trading Calculator

export interface ScreeningCriteria {
  id: string;
  name: string;
  description: string;
  filters: ScreeningFilter[];
  sorting: ScreeningSortConfig[];
  createdAt: string;
  updatedAt: string;
  isPublic: boolean;
  createdBy?: string;
}

export interface ScreeningFilter {
  field: ScreeningField;
  operator: FilterOperator;
  value: any;
  logicalOperator?: 'AND' | 'OR';
}

export interface ScreeningSortConfig {
  field: ScreeningField;
  direction: 'asc' | 'desc';
  priority: number;
}

export type ScreeningField =
  // Basic Stock Data
  | 'symbol'
  | 'price'
  | 'marketCap'
  | 'volume'
  | 'avgVolume'
  | 'sector'
  | 'industry'
  
  // Options Data
  | 'impliedVolatility'
  | 'historicalVolatility'
  | 'ivRank'
  | 'ivPercentile'
  | 'optionsVolume'
  | 'putCallRatio'
  | 'maxPain'
  | 'skew'
  
  // Greeks
  | 'delta'
  | 'gamma'
  | 'theta'
  | 'vega'
  | 'rho'
  
  // Volatility Metrics
  | 'ivCrushPotential'
  | 'earningsDate'
  | 'daysToEarnings'
  | 'volatilityExpansion'
  | 'termStructureSlope'
  
  // Technical Indicators
  | 'rsi'
  | 'macd'
  | 'bollinger'
  | 'support'
  | 'resistance'
  | 'trend'
  
  // Fundamental Data
  | 'pe'
  | 'eps'
  | 'dividend'
  | 'yield'
  | 'beta'
  | 'shortFloat'
  
  // Strategy-Specific
  | 'calendarSpreadOpportunity'
  | 'straddleOpportunity'
  | 'ironCondorOpportunity'
  | 'coveredCallYield'
  | 'cashSecuredPutYield';

export type FilterOperator =
  | 'equals'
  | 'not_equals'
  | 'greater_than'
  | 'greater_than_or_equal'
  | 'less_than'
  | 'less_than_or_equal'
  | 'between'
  | 'in'
  | 'not_in'
  | 'contains'
  | 'starts_with'
  | 'ends_with'
  | 'is_null'
  | 'is_not_null';

export interface ScreeningResult {
  symbol: string;
  name: string;
  price: number;
  change: number;
  changePercent: number;
  volume: number;
  marketCap: number;
  sector: string;
  industry: string;
  
  // Options Data
  impliedVolatility: number;
  historicalVolatility: number;
  ivRank: number;
  ivPercentile: number;
  optionsVolume: number;
  putCallRatio: number;
  maxPain?: number;
  
  // Earnings
  earningsDate?: string;
  daysToEarnings?: number;
  ivCrushPotential: number;
  
  // Strategy Opportunities
  strategies: StrategyOpportunity[];
  
  // Technical Indicators
  technicals: {
    rsi?: number;
    macd?: number;
    trend?: 'bullish' | 'bearish' | 'neutral';
    support?: number;
    resistance?: number;
  };
  
  // Fundamental Data
  fundamentals: {
    pe?: number;
    eps?: number;
    dividend?: number;
    yield?: number;
    beta?: number;
  };
  
  // Screening Score
  score: number;
  rank: number;
  
  // Last Updated
  lastUpdated: string;
}

export interface StrategyOpportunity {
  strategy: StrategyType;
  score: number;
  confidence: 'high' | 'medium' | 'low';
  expectedReturn: number;
  maxRisk: number;
  probability: number;
  description: string;
  entry: {
    price: number;
    impliedVolatility: number;
    timeToExpiration: number;
  };
  reasoning: string[];
}

export type StrategyType = 
  | 'calendar_spread'
  | 'straddle'
  | 'strangle'
  | 'iron_condor'
  | 'iron_butterfly'
  | 'covered_call'
  | 'cash_secured_put'
  | 'bull_call_spread'
  | 'bear_put_spread'
  | 'collar'
  | 'long_call'
  | 'long_put'
  | 'short_call'
  | 'short_put';

// Predefined Screening Templates
export interface ScreeningTemplate {
  id: string;
  name: string;
  description: string;
  category: ScreeningCategory;
  criteria: ScreeningCriteria;
  popularity: number;
  isBuiltIn: boolean;
}

export type ScreeningCategory =
  | 'earnings_plays'
  | 'high_volatility'
  | 'technical_breakouts'
  | 'dividend_plays'
  | 'momentum'
  | 'value'
  | 'growth'
  | 'custom';

// Screening Request/Response Types
export interface ScreeningRequest {
  criteria: ScreeningCriteria;
  limit?: number;
  offset?: number;
  includeGreeks?: boolean;
  includeStrategies?: boolean;
  includeTechnicals?: boolean;
  includeFundamentals?: boolean;
}

export interface ScreeningResponse {
  results: ScreeningResult[];
  totalCount: number;
  page: number;
  limit: number;
  executionTime: number;
  timestamp: string;
  summary: ScreeningSummary;
}

export interface ScreeningSummary {
  totalSymbols: number;
  averageScore: number;
  topSector: string;
  mostCommonStrategy: StrategyType;
  avgImpliedVolatility: number;
  avgIvRank: number;
  upcomingEarnings: number;
}

// Watchlist Integration
export interface Watchlist {
  id: string;
  name: string;
  description?: string;
  symbols: string[];
  screeningCriteriaId?: string;
  autoUpdate: boolean;
  createdAt: string;
  updatedAt: string;
}

export interface WatchlistItem {
  symbol: string;
  addedAt: string;
  notes?: string;
  alerts: WatchlistAlert[];
  lastScreened?: string;
  screeningResult?: Partial<ScreeningResult>;
}

export interface WatchlistAlert {
  id: string;
  type: 'price' | 'volume' | 'iv' | 'earnings' | 'strategy';
  condition: AlertCondition;
  isActive: boolean;
  triggeredAt?: string;
  createdAt: string;
}

export interface AlertCondition {
  field: ScreeningField;
  operator: FilterOperator;
  value: any;
  description: string;
}

// Market Data Types
export interface MarketOverview {
  indices: MarketIndex[];
  sectors: SectorPerformance[];
  volatilityMetrics: VolatilityMetrics;
  earnings: EarningsCalendar[];
  topMovers: {
    gainers: ScreeningResult[];
    losers: ScreeningResult[];
    active: ScreeningResult[];
  };
  lastUpdated: string;
}

export interface MarketIndex {
  symbol: string;
  name: string;
  price: number;
  change: number;
  changePercent: number;
  impliedVolatility?: number;
}

export interface SectorPerformance {
  sector: string;
  change: number;
  changePercent: number;
  symbolCount: number;
  avgImpliedVolatility: number;
  topSymbols: string[];
}

export interface VolatilityMetrics {
  vix: number;
  vixChange: number;
  termStructure: {
    front: number;
    back: number;
    slope: number;
  };
  skew: {
    spx: number;
    individual: number;
  };
}

export interface EarningsCalendar {
  symbol: string;
  name: string;
  date: string;
  time: 'BMO' | 'AMC' | 'Unknown';
  estimate?: number;
  impliedMove?: number;
  daysToEarnings: number;
}

// Chart Data Types
export interface ScreeningChartData {
  timeline: Array<{
    date: string;
    totalResults: number;
    avgScore: number;
    avgIV: number;
  }>;
  distribution: {
    bySector: Array<{ sector: string; count: number; avgScore: number }>;
    byStrategy: Array<{ strategy: StrategyType; count: number; avgScore: number }>;
    byScore: Array<{ scoreRange: string; count: number }>;
  };
}

// API Request/Response Helpers
export interface SaveScreeningCriteriaRequest {
  name: string;
  description?: string;
  criteria: Omit<ScreeningCriteria, 'id' | 'createdAt' | 'updatedAt' | 'createdBy'>;
  isPublic?: boolean;
}

export interface UpdateScreeningCriteriaRequest extends Partial<SaveScreeningCriteriaRequest> {
  id: string;
}

export interface CreateWatchlistRequest {
  name: string;
  description?: string;
  symbols?: string[];
  screeningCriteriaId?: string;
  autoUpdate?: boolean;
}

export interface UpdateWatchlistRequest extends Partial<CreateWatchlistRequest> {
  id: string;
}