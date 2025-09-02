/**
 * Chart data types and interfaces for Phase 3 visualizations
 */

export interface PnLScenario {
  /** Price change percentage from current price */
  priceChange: number
  /** Absolute price value */
  absolutePrice: number
  /** Days to expiration array for time decay analysis */
  daysToExpiration: number[]
  /** P&L values corresponding to days array */
  pnlValues: number[]
  /** IV crush scenarios with different intensity levels */
  ivCrushScenarios: {
    high: number      // 30% IV crush
    medium: number    // 20% IV crush  
    low: number       // 10% IV crush
  }
  /** Probability of this price occurring */
  probability?: number
}

export interface PnLScenarioProps {
  /** Array of P&L scenarios across price and time */
  scenarios: PnLScenario[]
  /** Current underlying price */
  currentPrice: number
  /** Trading strategy type */
  strategy: 'calendar' | 'straddle'
  /** Strike price for the trade */
  strikePrice: number
  /** Enable interactive features */
  interactionEnabled?: boolean
  /** Chart height in pixels */
  height?: number
  /** Chart width in pixels */
  width?: number
}

export interface GreeksTimeSeries {
  /** Days to expiration */
  daysToExpiration: number
  /** Underlying stock price */
  underlyingPrice: number
  /** Delta (price sensitivity) */
  delta: number
  /** Gamma (delta sensitivity) */
  gamma: number
  /** Theta (time decay) */
  theta: number
  /** Vega (volatility sensitivity) */
  vega: number
  /** Rho (interest rate sensitivity) */
  rho?: number
}

export interface GreeksChartProps {
  /** Time series data for Greeks */
  greeksData: GreeksTimeSeries[]
  /** Selected Greeks to display */
  selectedGreeks: ('delta' | 'gamma' | 'theta' | 'vega' | 'rho')[]
  /** Time range in days */
  timeRange: number
  /** Price range for analysis [min, max] */
  priceRange?: [number, number]
  /** Current underlying price */
  currentPrice: number
  /** Strike price for reference */
  strikePrice: number
  /** Chart height in pixels */
  height?: number
  /** Enable interactive features */
  interactive?: boolean
}

export interface ChartExportOptions {
  /** Export format */
  format: 'pdf' | 'png' | 'svg' | 'json'
  /** Include chart visualizations */
  includeCharts: boolean
  /** Include analysis data */
  includeAnalysis: boolean
  /** Include risk disclaimers */
  includeDisclaimers: boolean
  /** Generate shareable link */
  shareableLink: boolean
  /** Chart quality (1-10) */
  quality?: number
  /** Page orientation for PDF */
  orientation?: 'portrait' | 'landscape'
}

export interface ChartTheme {
  /** Primary color for profit/positive values */
  profitColor: string
  /** Color for loss/negative values */
  lossColor: string
  /** Color for breakeven/neutral values */
  neutralColor: string
  /** Grid line colors */
  gridColor: string
  /** Text color */
  textColor: string
  /** Background color */
  backgroundColor: string
  /** Font family */
  fontFamily: string
  /** Axis colors */
  axisColor: string
}

export interface ChartInteraction {
  /** Zoom level (1.0 = 100%) */
  zoomLevel: number
  /** Pan offset [x, y] */
  panOffset: [number, number]
  /** Selected data point */
  selectedPoint?: {
    x: number
    y: number
    data: any
  }
  /** Hover state */
  isHovering: boolean
  /** Touch/mouse position */
  cursorPosition?: [number, number]
}

export interface MobileChartConfig {
  /** Use touch-optimized controls */
  touchOptimized: boolean
  /** Minimum touch target size */
  minTouchTarget: number
  /** Enable pinch zoom */
  pinchZoom: boolean
  /** Enable swipe pan */
  swipePan: boolean
  /** Stack charts vertically on small screens */
  stackOnMobile: boolean
  /** Simplified mobile layout */
  simplifiedLayout: boolean
}

// Chart utility types
export type ChartDataPoint = {
  x: number
  y: number
  label?: string
  metadata?: Record<string, any>
}

export type ChartSeries = {
  name: string
  data: ChartDataPoint[]
  color: string
  type?: 'line' | 'area' | 'scatter'
}

export type ChartTooltipData = {
  title: string
  values: Array<{
    label: string
    value: string | number
    color?: string
  }>
  position: [number, number]
}

// P&L Surface Plot specific types
export interface PnLSurfaceData {
  /** X-axis: Price changes */
  priceChanges: number[]
  /** Y-axis: Days to expiration */
  daysToExpiration: number[]
  /** Z-axis: P&L values (2D array) */
  pnlMatrix: number[][]
  /** Metadata for each point */
  metadata?: {
    breakeven: number[]
    maxProfit: number
    maxLoss: number
    probabilityOfProfit: number
  }
}

// Export data structure
export interface ChartExportData {
  /** Timestamp of export */
  timestamp: string
  /** Chart type identifier */
  chartType: 'pnl_scenario' | 'greeks_timeseries' | 'combined'
  /** Raw data used in charts */
  data: any
  /** Chart configuration */
  config: {
    theme: ChartTheme
    dimensions: { width: number; height: number }
    selectedMetrics: string[]
  }
  /** Analysis metadata */
  metadata: {
    symbol: string
    currentPrice: number
    strategy: string
    analysisDate: string
  }
}