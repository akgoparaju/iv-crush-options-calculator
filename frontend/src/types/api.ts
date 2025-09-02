// TypeScript types for API integration
// Matches the FastAPI Pydantic models

export interface AnalysisRequest {
  symbol: string
  include_earnings?: boolean
  include_trade_construction?: boolean
  include_position_sizing?: boolean
  include_trading_decision?: boolean
  expirations_to_check?: number
  trade_structure?: 'calendar' | 'straddle' | 'auto'
  account_size?: number
  risk_per_trade?: number
  use_demo?: boolean
}

export interface AnalysisOverview {
  symbol: string
  current_price: number
  data_source: string
  analysis_mode: string
  expirations_checked: number
  timestamp: string
}

export interface ModuleStatus {
  earnings_analysis: boolean
  trade_construction: boolean
  position_sizing: boolean
  trading_decision: boolean
}

export interface EarningsAnalysis {
  next_earnings_date?: string
  days_to_earnings?: number
  earnings_timing?: string
  entry_window?: Record<string, unknown>
  exit_window?: Record<string, unknown>
  trading_signals?: Record<string, unknown>
}

export interface TradeConstruction {
  calendar_trade?: Record<string, unknown>
  straddle_construction?: Record<string, unknown>
  quality_assessment?: Record<string, unknown>
  greeks_analysis?: Record<string, unknown>
  pnl_analysis?: Record<string, unknown>
}

export interface PositionSizing {
  recommended_position?: Record<string, unknown>
  kelly_analysis?: Record<string, unknown>
  risk_assessment?: Record<string, unknown>
  portfolio_impact?: Record<string, unknown>
}

export interface TradingDecision {
  decision?: string
  confidence?: number
  signal_strength?: string
  reasoning?: string[]
  risk_warnings?: string[]
}

export interface AnalysisResponse {
  success: boolean
  message: string
  timestamp: string
  execution_time_ms: number
  overview: AnalysisOverview
  module_status: ModuleStatus
  earnings_analysis?: EarningsAnalysis
  trade_construction?: TradeConstruction
  position_sizing?: PositionSizing
  trading_decision?: TradingDecision
  disclaimers: string[]
  data_freshness?: string
  cache_hit: boolean
}

export interface ErrorResponse {
  success: false
  error: string
  message: string
  details?: Record<string, unknown>
  timestamp: string
  request_id?: string
}

export interface HealthResponse {
  status: string
  timestamp: string
  version: string
  uptime_seconds: number
  system_info?: Record<string, unknown>
  dependencies?: Record<string, unknown>
  cache_status?: Record<string, unknown>
}

// Chart data interfaces
export interface ChartDataPoint {
  x: number
  y: number
  label?: string
}

export interface PnLScenarioData {
  price_change: number
  days_to_expiration: number
  pnl: number
  probability: number
}

export interface GreeksTimeSeries {
  date: string
  underlying_price: number
  delta: number
  gamma: number
  theta: number
  vega: number
}

// UI state interfaces
export interface LoadingState {
  isLoading: boolean
  message?: string
  progress?: number
}

export interface ErrorState {
  hasError: boolean
  message?: string
  details?: string
}

// Form interfaces
export interface AnalysisFormData {
  symbol: string
  includeEarnings: boolean
  includeTradeConstruction: boolean
  includePositionSizing: boolean
  includeTradingDecision: boolean
  expirationsToCheck: number
  tradeStructure: 'calendar' | 'straddle' | 'auto'
  accountSize: string
  riskPerTrade: string
  useDemo: boolean
}

// API client types
export type ApiResponse<T> = T | ErrorResponse
export type ApiMethod = 'GET' | 'POST' | 'PUT' | 'DELETE'

export interface ApiConfig {
  baseURL: string
  timeout: number
  retries: number
}

// WebSocket types (for future real-time updates)
export interface WebSocketMessage {
  type: 'price_update' | 'analysis_complete' | 'error'
  data: unknown
  timestamp: string
}

export interface PriceUpdate {
  symbol: string
  price: number
  change: number
  change_percent: number
  timestamp: string
}