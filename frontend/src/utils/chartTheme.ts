import { ChartTheme } from '@/types/charts'

/**
 * Professional chart theme configuration matching the design system
 */
export const defaultChartTheme: ChartTheme = {
  profitColor: '#10b981',    // success-500
  lossColor: '#ef4444',      // danger-500  
  neutralColor: '#64748b',   // slate-500
  gridColor: '#e2e8f0',      // slate-200
  textColor: '#374151',      // slate-700
  backgroundColor: '#ffffff', // white
  fontFamily: 'Inter, system-ui, sans-serif',
  axisColor: '#6b7280'       // slate-500
}

export const darkChartTheme: ChartTheme = {
  profitColor: '#34d399',    // success-400
  lossColor: '#f87171',      // danger-400
  neutralColor: '#94a3b8',   // slate-400  
  gridColor: '#374151',      // slate-700
  textColor: '#f1f5f9',      // slate-100
  backgroundColor: '#1e293b', // slate-800
  fontFamily: 'Inter, system-ui, sans-serif',
  axisColor: '#9ca3af'       // slate-400
}

/**
 * Chart color palette for different data series
 */
export const chartColors = {
  primary: '#3b82f6',     // blue-500
  secondary: '#6366f1',   // indigo-500
  accent: '#8b5cf6',      // violet-500
  success: '#10b981',     // emerald-500
  warning: '#f59e0b',     // amber-500
  danger: '#ef4444',      // red-500
  info: '#06b6d4',        // cyan-500
  neutral: '#64748b'      // slate-500
}

/**
 * Greeks-specific color mapping
 */
export const greeksColors = {
  delta: chartColors.primary,    // Blue for Delta
  gamma: chartColors.accent,     // Purple for Gamma  
  theta: chartColors.danger,     // Red for Theta (decay)
  vega: chartColors.success,     // Green for Vega
  rho: chartColors.warning       // Amber for Rho
}

/**
 * Responsive breakpoints for chart sizing
 */
export const chartBreakpoints = {
  sm: 640,
  md: 768, 
  lg: 1024,
  xl: 1280,
  '2xl': 1536
}

/**
 * Default chart dimensions based on screen size
 */
export const getResponsiveChartDimensions = (containerWidth: number) => {
  if (containerWidth >= chartBreakpoints.xl) {
    return { width: 800, height: 400 }
  } else if (containerWidth >= chartBreakpoints.lg) {
    return { width: 700, height: 350 }
  } else if (containerWidth >= chartBreakpoints.md) {
    return { width: 600, height: 300 }
  } else if (containerWidth >= chartBreakpoints.sm) {
    return { width: 500, height: 250 }
  } else {
    return { width: containerWidth - 32, height: 200 } // Mobile with padding
  }
}

/**
 * Format currency values for chart display
 */
export const formatChartCurrency = (value: number): string => {
  const absValue = Math.abs(value)
  
  if (absValue >= 1000000) {
    return `$${(value / 1000000).toFixed(1)}M`
  } else if (absValue >= 1000) {
    return `$${(value / 1000).toFixed(1)}K`
  } else if (absValue >= 1) {
    return `$${value.toFixed(2)}`
  } else {
    return `$${value.toFixed(3)}`
  }
}

/**
 * Format percentage values for chart display
 */
export const formatChartPercentage = (value: number): string => {
  if (Math.abs(value) >= 100) {
    return `${value.toFixed(0)}%`
  } else if (Math.abs(value) >= 10) {
    return `${value.toFixed(1)}%`
  } else {
    return `${value.toFixed(2)}%`
  }
}

/**
 * Format Greek values for chart display
 */
export const formatGreekValue = (greek: string, value: number): string => {
  switch (greek.toLowerCase()) {
    case 'delta':
    case 'gamma':
      return value.toFixed(3)
    case 'theta':
      return `${value.toFixed(2)}/day`
    case 'vega':
      return value.toFixed(3)
    case 'rho':
      return value.toFixed(4)
    default:
      return value.toFixed(3)
  }
}

/**
 * Get color based on P&L value (profit/loss)
 */
export const getPnLColor = (value: number, theme: ChartTheme = defaultChartTheme): string => {
  if (value > 0) return theme.profitColor
  if (value < 0) return theme.lossColor
  return theme.neutralColor
}

/**
 * Generate chart gradient definitions for enhanced visuals
 */
export const generateChartGradients = (theme: ChartTheme) => ({
  profitGradient: {
    id: 'profitGradient',
    stops: [
      { offset: '0%', stopColor: theme.profitColor, stopOpacity: 0.8 },
      { offset: '100%', stopColor: theme.profitColor, stopOpacity: 0.2 }
    ]
  },
  lossGradient: {
    id: 'lossGradient', 
    stops: [
      { offset: '0%', stopColor: theme.lossColor, stopOpacity: 0.8 },
      { offset: '100%', stopColor: theme.lossColor, stopOpacity: 0.2 }
    ]
  }
})

/**
 * Chart animation configurations
 */
export const chartAnimations = {
  // Smooth entry animation
  enter: {
    duration: 800,
    easing: 'ease-out'
  },
  // Hover state animation
  hover: {
    duration: 200,
    easing: 'ease-in-out'
  },
  // Data update animation
  update: {
    duration: 500,
    easing: 'ease-in-out'
  }
}

/**
 * Mobile-specific chart configurations
 */
export const mobileChartConfig = {
  minTouchTarget: 44, // 44px minimum touch target
  tooltipOffset: 20,
  zoomSensitivity: 1.5,
  panThreshold: 10,
  maxZoom: 5,
  minZoom: 0.5
}

/**
 * Chart accessibility configurations
 */
export const chartA11yConfig = {
  // ARIA labels and descriptions
  ariaLabels: {
    pnlChart: 'Profit and Loss scenario chart',
    greeksChart: 'Options Greeks time series chart',
    exportButton: 'Export chart data'
  },
  // Keyboard navigation
  keyboardShortcuts: {
    zoomIn: 'Plus',
    zoomOut: 'Minus', 
    reset: 'R',
    export: 'E'
  },
  // Screen reader support
  screenReaderDescriptions: true,
  // High contrast mode support
  highContrastSupport: true
}